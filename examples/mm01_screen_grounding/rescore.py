"""Re-score stored MM01 replies under label v1 and v1.1, with and without pre-flight.

  python rescore.py      (reads reviews/evidence/mm01/TRIALS.json; makes no model calls)
  python rescore.py --oracle                     protocol v2 T1: labels v2 on the R1 replies
  python rescore.py --v2 RUN/TRIALS_v2.json      protocol v2 tables (Section 11) -> COMPARISON_v2.md

"Pipeline" means: the deterministic pre-flight runs first; if it asks for a new
observation, that is the system's decision and the model's reply is not used.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from trials import (LABELS_V1_1_REASONS, SPEC_V2, evaluate, evaluate_v2, labels_v1_1, load,
                    load_dev_v2, load_spec_trials, pipeline_passed_v2, read_spec)

OUT = Path(__file__).resolve().parent.parent.parent / "reviews" / "evidence" / "mm01"


def pipeline_pass(row: dict, label: dict) -> bool:
    if not row["preflight"]["proceed"]:
        return label["expect"] == "new_observation"
    return evaluate(row["reply"].get("parsed"), label)["passed"]


def main() -> int:
    record = json.loads((OUT / "TRIALS.json").read_text("utf-8"))
    _, v1 = load()
    v11 = labels_v1_1(v1)
    table: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    modes = {}
    for row in record["rows"]:
        tid = row["task_id"]
        modes[tid] = row["mode"]
        parsed = row["reply"].get("parsed")
        table[tid]["v1"].append(evaluate(parsed, v1[tid])["passed"])
        table[tid]["v1.1"].append(evaluate(parsed, v11[tid])["passed"])
        table[tid]["pipeline_v1.1"].append(pipeline_pass(row, v11[tid]))
    lines = ["# MM01 comparison under label v1 and v1.1 (generated)", "",
             f"Source: `TRIALS.json` ({record['model']}, {record['runtime']}, think={record['think']}, "
             f"seeds {record['seeds']}). No model was called to make this table.", "",
             "Label revision v1.1 was written AFTER inspecting v1 results. Both are reported. Reasons:", ""]
    lines += [f"- {k}: {v}" for k, v in LABELS_V1_1_REASONS.items()]
    lines += ["", "Known confound not fixed by relabelling: the v1 agent prompt tells the model to ask for "
                  "a new screenshot when none is attached, which biases the text-only trials (M1-M3) "
                  "toward 'new_observation' even when the text is complete (M2). A fair text-vs-image "
                  "comparison needs a revised prompt and new runs.", "",
              "| Trial | Mode | Model alone, v1 | Model alone, v1.1 | Pre-flight + model, v1.1 |",
              "|---|---|---|---|---|"]
    for tid, cols in table.items():
        lines.append(f"| {tid} | {modes[tid]} | {sum(cols['v1'])}/{len(cols['v1'])} | "
                     f"{sum(cols['v1.1'])}/{len(cols['v1.1'])} | "
                     f"{sum(cols['pipeline_v1.1'])}/{len(cols['pipeline_v1.1'])} |")
    totals = {k: (sum(sum(c[k]) for c in table.values()), sum(len(c[k]) for c in table.values()))
              for k in ("v1", "v1.1", "pipeline_v1.1")}
    lines += ["", "Totals: " + "; ".join(f"{k} {a}/{b}" for k, (a, b) in totals.items()),
              "", "Thermal note: Ollama placed the model on the RTX 2060 (GPU 0), which reached 84 °C "
                  "with software thermal slowdown active during the run (gpu_watch.log). Wall times are "
                  "affected and are not a latency benchmark.", ""]
    (OUT / "COMPARISON.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


# ---------------------------------------------------------------------------- protocol v2
def r1_counts_v2(record: dict[str, Any]) -> dict[str, list[bool]]:
    """Labels v2 (evaluator v2, v1 schema mapped) on the stored R1 replies, model alone."""
    labels = {t.bundle.task_id: t.label for t in load_dev_v2()}
    out: dict[str, list[bool]] = defaultdict(list)
    for row in record["rows"]:
        out[row["task_id"]].append(evaluate_v2(row["reply"].get("parsed"), labels[row["task_id"]])["passed"])
    return out


def oracle_check(record: dict[str, Any]) -> tuple[bool, list[str]]:
    """T1: the per-trial counts must equal the protocol's rescoring oracle (Section 6.4)."""
    want = read_spec()["dev_labels_v2"]["rescoring_oracle_v1_replies"]["expected_passed_per_trial"]
    got = {k: sum(v) for k, v in r1_counts_v2(record).items()}
    bad = [f"{k}: oracle {want[k]}, got {got.get(k)}" for k in want if got.get(k) != want[k]]
    lines = [f"Oracle check (labels v2 on R1): {'PASS' if not bad else 'FAIL'}; "
             f"total {sum(got.values())}/{sum(len(v) for v in r1_counts_v2(record).values())}"]
    return not bad, lines + [f"- {b}" for b in bad]


def read_run(path: Path) -> dict[str, Any]:
    """A TRIALS_v2.json record, or the rows of an interrupted run's .jsonl."""
    if path.suffix == ".jsonl":
        rows = [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]
        return {"rows": [r for r in rows if r.get("kind") == "call"], "seeds": None,
                "model": None, "runtime": None, "code_sha256": None, "source": path.name}
    return {**json.loads(path.read_text("utf-8")), "source": path.name}


def rescored_rows(run: dict[str, Any], spec: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Score every stored reply again with the current evaluator; list rows whose stored
    score differs (a sign the evaluator changed after the run)."""
    labels = {("heldout", t.bundle.task_id): t.label for t in load_spec_trials(spec)}
    labels.update({("dev", t.bundle.task_id): t.label for t in load_dev_v2()})
    rows, changed = [], []
    for row in run["rows"]:
        label = labels[(row["set"], row["task_id"])]
        score = evaluate_v2(row["reply"].get("parsed"), label) if row["status"] == "ok" else None
        if score is not None and row.get("score") is not None and score["passed"] != row["score"]["passed"]:
            changed.append(row["key"])
        pipe = None if score is None else pipeline_passed_v2(row["preflight"], score, label)
        rows.append({**row, "score": score, "pipeline_passed": pipe})
    return rows, changed


def _k(rows: list[dict[str, Any]], fn) -> tuple[int, int]:
    ok = [r for r in rows if r["status"] == "ok"]
    return sum(bool(fn(r)) for r in ok), len(ok)


def _kn(rows: list[dict[str, Any]], component: str) -> str:
    vals = [r["score"][component] for r in rows if r["status"] == "ok"]
    vals = [v for v in vals if v is not None]
    return f"{sum(vals)}/{len(vals)}" if vals else "-"


def _decisions(rows: list[dict[str, Any]]) -> str:
    c = Counter((r["score"]["decision"] or "unparsed") for r in rows if r["status"] == "ok")
    return ", ".join(f"{k} {v}" for k, v in sorted(c.items())) or "-"


def _pick(rows, block: str, arm: str, trials: list[str]) -> list[dict[str, Any]]:
    return [r for r in rows if r["block"] == block and r["arm"] == arm and r["task_id"] in trials]


def hypothesis_table(rows: list[dict[str, Any]], spec: dict[str, Any], n_seeds: int) -> list[str]:
    """Section 2 decision rules. A count below the planned n (errors excluded, or an
    unfinished run) is 'undetermined'; the verdict thresholds are written for the full n."""
    hyp = spec["hypotheses"]
    out = ["| ID | Trials | Count | Verdict |", "|---|---|---|---|"]

    def full(n: int, trials: list[str]) -> bool:
        return n == len(trials) * n_seeds

    def row(hid: str, count: str, verdict: str) -> None:
        out.append(f"| {hid} | {', '.join(t.split('_')[0] for t in hyp[hid]['trials'])} | {count} | {verdict} |")

    t = hyp["H1"]["trials"]
    k2, n2 = _k(_pick(rows, "H", "P2", t), lambda r: r["score"]["decision"] == "answer")
    k1, n1 = _k(_pick(rows, "H", "P1", t), lambda r: r["score"]["decision"] == "answer")
    v = ("undetermined (n below plan)" if not (full(n2, t) and full(n1, t)) else
         "support" if k2 >= 5 and k2 - k1 >= 2 else
         "no support" if k2 <= 3 or k2 - k1 <= 0 else "inconclusive")
    row("H1", f"answer: v2 {k2}/{n2}, v1 {k1}/{n1}", v)
    t = hyp["H2"]["trials"]
    k, n = _k(_pick(rows, "H", "P2", t), lambda r: r["score"]["decision"] == "answer")
    row("H2", f"guesses {k}/{n}", "undetermined (n below plan)" if not full(n, t) else
        "support" if k == 0 else "no support" if k >= 2 else "inconclusive")
    for hid, support, no in (("H3", lambda k: k >= 5, lambda k: k <= 3),
                             ("H4", lambda k: k <= 4, lambda k: k == 6)):
        t = hyp[hid]["trials"]
        k, n = _k(_pick(rows, "H", "P2", t), lambda r: r["score"]["target_ok"] is True)
        row(hid, f"target_ok {k}/{n}", "undetermined (n below plan)" if not full(n, t) else
            "support" if support(k) else "no support" if no(k) else "inconclusive")
    t = hyp["H5"]["trials"]
    picked = _pick(rows, "H", "P2", t)
    blocked = sum(not r["preflight"]["proceed"] for r in picked)
    k, n = _k(picked, lambda r: r["score"]["decision"] == "new_observation")
    v = ("STOP: pre-flight precondition failed (implementation defect)" if blocked != len(picked) else
         "undetermined (n below plan)" if not (full(n, t) and full(len(picked), t)) else
         "support" if k <= 5 else "no support")
    row("H5", f"model alone new_observation {k}/{n}; pre-flight {blocked}/{len(picked)}", v)
    t = hyp["X1"]["trials"]
    k, n = _k(_pick(rows, "H", "P2", t), lambda r: r["score"]["decision"] == "clarify")
    row("X1", f"clarify {k}/{n}", "report only (exploratory)")
    return out


def comparison_v2(run: dict[str, Any], spec_path: Path, r1: dict[str, Any] | None) -> tuple[str, bool]:
    spec = read_spec(spec_path)
    rows, changed = rescored_rows(run, spec_path)
    seeds = run.get("seeds") or sorted({r["seed"] for r in rows})
    lines = ["# MM01 protocol v2 comparison (generated)", "",
             f"Source: `{run['source']}` (model {run.get('model')}, {run.get('runtime')}, seeds {seeds}, "
             f"code {run.get('code_sha256')}). Replies rescored with the current evaluator v2; "
             "no model was called to make these tables. Counts only, never rates.", ""]
    ok = True
    if r1 is not None:
        ok, oracle = oracle_check(r1)
        lines += oracle + [""]
    if changed:
        lines += [f"Rows whose stored score differs from the rescored one: {changed}", ""]
    errors = [r["key"] for r in rows if r["status"] != "ok"]
    lines += [f"Errors (excluded from every denominator): {errors or 'none'}", ""]
    held = [t.bundle for t in load_spec_trials(spec_path)]
    lines += ["## Hypotheses (held-out only, confirmatory)", ""] + hypothesis_table(rows, spec, len(spec["model_settings"]["seeds"]))
    lines += ["", "## Held-out trials", "",
              "| Trial | Mode | Expected | P2 decisions | Target | Concepts | Problem found | Passed | Pipeline | P1 decisions |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    exp = {t.bundle.task_id: t.label["expect"] for t in load_spec_trials(spec_path)}
    for b in held:
        p2, p1 = _pick(rows, "H", "P2", [b.task_id]), _pick(rows, "H", "P1", [b.task_id])
        pipe = [r["pipeline_passed"] for r in p2 if r["pipeline_passed"] is not None]
        lines.append(f"| {b.task_id} | {b.mode} | {exp[b.task_id]} | {_decisions(p2)} | {_kn(p2, 'target_ok')} | "
                     f"{_kn(p2, 'concepts_ok')} | {_kn(p2, 'problem_found_ok')} | {_kn(p2, 'passed')} | "
                     f"{sum(pipe)}/{len(pipe)} | {_decisions(p1) if p1 else '-'} |")
    lines += ["", "## Development trials (exploratory; labels v2 written after the v1 results)", "",
              "| Trial | Mode | R1 P1 labels v1 | R1 P1 labels v1.1 | R1 P1 labels v2 | R2 P2 labels v2 model alone | R2 P2 labels v2 pre-flight + model |",
              "|---|---|---|---|---|---|---|"]
    bundles, v1 = load()
    v11 = labels_v1_1(v1)
    r1_v2 = r1_counts_v2(r1) if r1 else {}
    for b in bundles:
        r1_rows = [r for r in (r1 or {}).get("rows", []) if r["task_id"] == b.task_id]
        c1 = [evaluate(r["reply"].get("parsed"), v1[b.task_id])["passed"] for r in r1_rows]
        c11 = [evaluate(r["reply"].get("parsed"), v11[b.task_id])["passed"] for r in r1_rows]
        d = _pick(rows, "D", "P2", [b.task_id])
        pipe = [r["pipeline_passed"] for r in d if r["pipeline_passed"] is not None]
        lines.append(f"| {b.task_id} | {b.mode} | {sum(c1)}/{len(c1)} | {sum(c11)}/{len(c11)} | "
                     f"{sum(r1_v2.get(b.task_id, []))}/{len(r1_v2.get(b.task_id, []))} | "
                     f"{_kn(d, 'passed')} | {sum(pipe)}/{len(pipe)} |")
    lines += ["", "Dev and held-out counts are never pooled. R1 and R2 differ in prompt, GPU and date; "
                  "only P1 against P2 inside R2 isolates the prompt.", ""]
    return "\n".join(lines), ok


def cli(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--oracle", action="store_true", help="T1 only: check labels v2 on R1 against the oracle")
    p.add_argument("--v2", type=Path, help="TRIALS_v2.json (or .jsonl) of a protocol v2 run")
    p.add_argument("--spec", type=Path, default=SPEC_V2)
    p.add_argument("--r1", type=Path, default=OUT / "TRIALS.json", help="stored v1 run (R1)")
    p.add_argument("--out", type=Path, default=None, help="folder for COMPARISON_v2.md (default: beside --v2)")
    args = p.parse_args(argv)
    if args.oracle:
        ok, lines = oracle_check(json.loads(args.r1.read_text("utf-8")))
        print("\n".join(lines))
        return 0 if ok else 1
    if args.v2:
        r1 = json.loads(args.r1.read_text("utf-8")) if args.r1.is_file() else None
        text, ok = comparison_v2(read_run(args.v2), args.spec, r1)
        out = (args.out or args.v2.parent) / "COMPARISON_v2.md"
        out.write_text(text, encoding="utf-8")
        print(text)
        return 0 if ok else 1
    return main()


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
