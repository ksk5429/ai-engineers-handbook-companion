"""P10 driver: rule-number citation interface (v2) against the current one (v1).

Specification: experiments/P10_PREREGISTRATION.md v1.0, sections 5.9, 8, 9, 10, 11.

  python experiments/p10_trials.py --init-freeze                    record experiments/p10_freeze.json once
  python experiments/p10_trials.py --phase dev [--candidate-tag v2|v2.1] [--main-gpu 1] [--cap-min 60]
  python experiments/p10_trials.py --freeze-candidate v2            freeze F6 (after the dev gate)
  python experiments/p10_trials.py --phase heldout
  python experiments/p10_trials.py --analyse                        decision by code (section 10)
  python experiments/p10_trials.py --dry-run                        whole sequence, scripted model,
                                                                    no Ollama, output in a temp folder

Outputs go to reviews/evidence/p10/ only. Each invocation works in p10.new (a copy of p10, or
the leftover of an interrupted invocation, which is resumed) and swaps it in at the end.
The freeze manifest experiments/p10_freeze.json is written only by --init-freeze; --phase,
--freeze-candidate and --analyse refuse without it or when a frozen hash differs (addendum 1.1).
Exit: 0 done, 4 stopped early (hold flag, time cap, GPU temperature unreadable or >= 87 C),
64 preflight or usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXAMPLE = HERE.parent
REPO = EXAMPLE.parent.parent
sys.path.insert(0, str(EXAMPLE))

from docassist import checks, interface_v2, runner, workflow  # noqa: E402
from docassist.runlog import sha256_tree  # noqa: E402
from docassist.tools import ToolBox  # noqa: E402

FINAL = REPO / "reviews" / "evidence" / "p10"
FREEZE = HERE / "p10_freeze.json"
DRY_MARK = "DRY_RUN_ONLY.txt"
BENCH_FLAG = Path(os.environ.get("HANDBOOK_HOLD_FLAG", r"C:\ProgramData\paperkit-locks\bench_hold.flag"))
PY = sys.executable
MODEL, DIGEST, TEMPERATURE, NUM_CTX = "qwen2.5:7b", "845dbda0ea48", 0.7, 8192
SEEDS = (1, 2, 3, 4, 5)
CLAIMS = {"dev": ("claim_normal.json", "claim_injection.json"),
          "heldout": ("claim_heldout_1.json", "claim_heldout_2.json", "claim_heldout_3.json")}
FIXTURE_LABELS = {"claim_normal.json": "normal", "claim_injection.json": "injection_resisted"}
NORMAL_EXITS = {0, 1, 2, 5}
RETRIES_PER_CELL, RETRIES_TOTAL, MAX_BLOCKED_CELLS, GPU_STOP_C, MAX_CAP_MIN = 2, 6, 2, 87, 60.0
GOLDENS = {  # section 3.1, recorded 2026-11-09 from the v1 code
    "tool_definitions": "4e5ea06e93776faee744f3ed2e3faa9bb3cd8e695487db49a119e5b9b1e84517",
    "system_prompt": "e33b955890d432a663aa6a5e5f778baeb3cbb5991b799baf332612069d730633",
    "read_document_policy": "4b812fdb90bd9e639bc8e0d366b1d922b3c011481fa5504f707696d71761c6e8",
    "evaluate_source": "c9e6f6889eb7aa162f41d8d2d524b400bd7d0d854c2a32e166b7378a326b0f96",
}
FROZEN = ["docassist/checks.py", "checker.py", "docassist/schema.py", "schemas/answer.schema.json",
          "task_contract.json", "data/policy.md", "fixtures/make_cases.py", "tests/test_docassist.py",
          "experiments/P10_labels.json", "experiments/P10_PREREGISTRATION.md", "experiments/p10_trials.py",
          "experiments/P10_PROTOCOL_ADDENDUM_1_1.md", "experiments/p10_fake_run.py", "run.py",
          *(f"data/{c}" for phase in CLAIMS.values() for c in phase)]


def utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sh(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, cwd=EXAMPLE, capture_output=True, text=True, encoding="utf-8",
                              env=env)
    except FileNotFoundError as exc:                       # e.g. ollama or nvidia-smi not on PATH
        return subprocess.CompletedProcess(args, 127, "", str(exc))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(l) for l in path.read_text("utf-8").splitlines() if l.strip()] if path.is_file() else []


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------- freeze and preflight
def frozen_hashes() -> dict[str, str]:
    paths = FROZEN + sorted(p.relative_to(EXAMPLE).as_posix() for p in (EXAMPLE / "fixtures" / "cases").glob("*.json"))
    return {rel: hashlib.sha256((EXAMPLE / rel).read_bytes()).hexdigest() for rel in sorted(paths)}


def goldens_now() -> dict[str, str]:
    def h(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    read = ToolBox(EXAMPLE / "data")._read_document({"name": "policy.md"})
    return {"tool_definitions": h(json.dumps(workflow.tool_definitions(), sort_keys=True)),
            "system_prompt": h(workflow.SYSTEM_PROMPT),
            "read_document_policy": h(json.dumps(read, sort_keys=True)),
            "evaluate_source": h(inspect.getsource(workflow.evaluate))}


def load_freeze(path: Path) -> dict[str, Any] | None:
    """Read the manifest; None if it was never initialised (it is never created implicitly)."""
    if not path.is_file():
        print(f"ERROR: no freeze manifest at {path}; run --init-freeze first", file=sys.stderr)
        return None
    return json.loads(path.read_text("utf-8"))


def init_freeze(path: Path) -> int:
    """--init-freeze: record the frozen files, the addendum, the driver and the v1 goldens, once."""
    if path.exists():
        print(f"ERROR: {path} already exists; a freeze is never overwritten", file=sys.stderr)
        return 64
    if goldens_now() != GOLDENS:
        print("ERROR: the v1 goldens differ from section 3.1; nothing frozen", file=sys.stderr)
        return 64
    files = frozen_hashes()
    record = {"protocol": "experiments/P10_PREREGISTRATION.md v1.0 + P10_PROTOCOL_ADDENDUM_1_1.md",
              "recorded_utc": utc(), "files": files, "goldens": goldens_now(),
              "addendum_sha256": files["experiments/P10_PROTOCOL_ADDENDUM_1_1.md"],
              "driver_sha256": files["experiments/p10_trials.py"],
              "code_sha256_at_freeze": sha256_tree(runner.code_files()), "candidate": None}
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"freeze manifest recorded: {path} ({len(files)} files)")
    return 0


def frozen_changes(freeze: dict[str, Any]) -> list[str]:
    now = frozen_hashes()
    changed = [rel for rel, digest in now.items() if freeze["files"].get(rel) != digest]
    return changed + [rel for rel in freeze["files"] if rel not in now or not (EXAMPLE / rel).is_file()]


def code_problems(dev: list[dict[str, Any]], arms_to_run: set[str], tree: str) -> list[str]:
    """M2: one code hash per DEV arm; arms about to run must match it; v2.1 must differ from v2."""
    by_arm: dict[str, set[str]] = {}
    for r in dev:
        if r["code_sha256"]:
            by_arm.setdefault(r["arm"], set()).add(r["code_sha256"])
    problems = [f"{a}: {len(h)} different code hashes" for a, h in sorted(by_arm.items()) if len(h) > 1]
    problems += [f"{a}: current code differs from its existing DEV rows"
                 for a in sorted(arms_to_run) if a in by_arm and tree not in by_arm[a]]
    if "v2.1" in arms_to_run and tree in by_arm.get("v2", set()):
        problems.append("v2.1: current code equals v2's code (no revision)")
    if by_arm.get("v2.1", set()) & by_arm.get("v2", set()):
        problems.append("v2.1 rows share code with v2 rows")
    return problems


def labels() -> dict[str, dict[str, Any]]:
    return json.loads((HERE / "P10_labels.json").read_text("utf-8"))["labels"]


def preflight(phase: str, tag: str, freeze: dict[str, Any], out: Path, dry: bool) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append({"check": name, "ok": bool(ok), "detail": detail})

    check("bench_hold.flag absent", not BENCH_FLAG.exists(), str(BENCH_FLAG))
    changed = frozen_changes(freeze)
    check("frozen hashes equal p10_freeze.json", not changed, ", ".join(changed) or "all equal")
    now = goldens_now()
    check("v1 goldens equal section 3.1", now == GOLDENS and freeze["goldens"] == GOLDENS,
          ", ".join(k for k in GOLDENS if now.get(k) != GOLDENS[k]) or "all equal")
    lab = labels()
    differ = []
    for claim, case in FIXTURE_LABELS.items():
        fixture = json.loads((EXAMPLE / "fixtures" / "cases" / f"{case}.json").read_text("utf-8"))["label"]
        if {k: lab[claim][k] for k in ("decision", "total_allowed", "items")} != fixture:
            differ.append(claim)
    check("DEV labels equal fixture labels", not differ, ", ".join(differ) or "equal")
    if phase == "heldout":
        cand = freeze.get("candidate") or {}
        tree = sha256_tree(runner.code_files())
        check("candidate block bound to current code", cand.get("code_sha256") == tree and cand.get("tag") == tag,
              f"candidate {cand.get('tag')} {str(cand.get('code_sha256'))[:12]}, tree {tree[:12]}, tag {tag}")
    work = out.with_name(out.name + ".new")
    source = work if work.exists() else out
    if phase == "dev":
        arms = {"v2.1"} if tag == "v2.1" else {"v1", tag}
        problems = code_problems(score_phase(source, "dev"), arms, sha256_tree(runner.code_files()))
        check("DEV rows bound to one code hash per arm", not problems, "; ".join(problems) or "ok")
    if phase == "dev" and tag == "v2.1":
        gate = decide(score_phase(source, "dev"), None, None)
        check("revision v2.1 allowed (v2 failed the dev gate)", gate.get("revision_allowed", False),
              gate["notes"][-1] if gate["notes"] else "")
    if dry:
        check("ollama digest", True, "skipped: dry run, scripted model, no Ollama call")
    else:
        shown = sh(["ollama", "show", MODEL]).stdout + "\n".join(
            l for l in sh(["ollama", "list"]).stdout.splitlines() if l.startswith(MODEL))
        check(f"ollama reports {MODEL} digest {DIGEST}", DIGEST in shown, "ollama show / ollama list")
    tests = sh([PY, "-m", "unittest", "discover", "-s", "tests"])
    check("unit tests pass", tests.returncode == 0, (tests.stderr.strip().splitlines() or [""])[-1])
    return results


# ---------------------------------------------------------------- running cells
def cell_plan(phase: str, tag: str) -> list[tuple[int, str, str, int]]:
    """Section 8 order: seeds 1..5, claims in listed order; even k v1 first, odd k v2 first."""
    plan = []
    for k, (seed, claim) in enumerate((s, c) for s in SEEDS for c in CLAIMS[phase]):
        arms = [tag] if tag == "v2.1" and phase == "dev" else (["v1", tag] if k % 2 == 0 else [tag, "v1"])
        plan += [(k, arm, claim, seed) for arm in arms]
    return plan


def run_dirs(cell: Path) -> tuple[list[Path], list[Path]]:
    dirs = sorted(p for p in cell.iterdir() if p.is_dir()) if cell.is_dir() else []
    ended = [d for d in dirs if any(e["type"] == "run_end" for e in read_jsonl(d / "events.jsonl"))]
    return ended, [d for d in dirs if d not in ended]


def model_error(run_dir: Path) -> bool:
    verdicts = [e for e in read_jsonl(run_dir / "events.jsonl") if e["type"] == "verdict"]
    return bool(verdicts) and verdicts[-1]["status"] == "blocked" and not any(
        "policy document was not loaded" in r for r in verdicts[-1]["reasons"])


def launch(cell: Path, arm: str, claim: str, seed: int, main_gpu: int, dry: bool,
           attempt: int) -> tuple[Path | None, int, float, str]:
    script = [str(HERE / "p10_fake_run.py")] if dry else ["run.py"]
    args = [PY, *script, "--ollama", MODEL, "--claim", claim, "--seed", str(seed),
            "--temperature", str(TEMPERATURE), "--interface", "v1" if arm == "v1" else "v2",
            "--runs-dir", str(cell)]
    env = {**os.environ, "HANDBOOK_MAIN_GPU": str(main_gpu), "P10_FAKE_ATTEMPT": str(attempt)}
    cell.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in cell.iterdir()}
    started = time.perf_counter()
    proc = sh(args, env)
    wall = round(time.perf_counter() - started, 3)
    new = [p for p in sorted(cell.iterdir()) if p.is_dir() and p.name not in before]
    return (new[0] if new else None), proc.returncode, wall, (proc.stdout[-300:] + proc.stderr[-300:])


def run_cell(out: Path, phase: str, k: int, arm: str, claim: str, seed: int, ctx: dict[str, Any]) -> dict[str, Any]:
    cell = out / phase / arm / Path(claim).stem / f"seed{seed}"
    ended, incomplete = run_dirs(cell)              # incomplete = left by an interrupted window: kept, listed
    attempts, exit_status, wall, tail = list(ended), None, None, ""
    harness, final = False, (attempts[-1] if attempts else None)
    while not attempts or model_error(attempts[-1]):  # blocked by the model service: retry, same seed
        if attempts and (len(attempts) > RETRIES_PER_CELL or ctx["retries_used"] >= RETRIES_TOTAL):
            break
        if attempts:
            ctx["retries_used"] += 1
        run_dir, exit_status, wall, tail = launch(cell, arm, claim, seed, ctx["main_gpu"], ctx["dry"],
                                                  len(attempts) + 1)
        if run_dir is None:
            harness, final = True, None
            break
        ended_ok = run_dir in run_dirs(cell)[0]
        (attempts if ended_ok else incomplete).append(run_dir)
        final = run_dir
        if exit_status not in NORMAL_EXITS or not ended_ok:
            harness = True
            break
    checked: dict[str, Any] | None = None
    if final is not None and not harness:
        proc = sh([PY, "checker.py", str(final)])
        try:
            outcome = json.loads(proc.stdout)
            checked = {"decision": outcome["decision"], "accepted": outcome["accepted"]}
        except (json.JSONDecodeError, KeyError):
            checked = {"decision": "checker error", "accepted": False}
    rel = lambda p: p.relative_to(out).as_posix()  # noqa: E731
    events = read_jsonl(final / "events.jsonl") if final else []
    options = events[0].get("model", {}).get("options") if events else None
    expected = {"num_ctx": NUM_CTX, "temperature": TEMPERATURE, "seed": seed, "main_gpu": ctx["main_gpu"]}
    return {"phase": phase, "k": k, "arm": arm, "interface": "v1" if arm == "v1" else "v2",
            "options": options, "options_ok": options == expected,
            "claim": claim, "seed": seed, "run_dir": rel(final) if final else None,
            "attempts": [rel(a) for a in attempts], "retries": max(len(attempts) - 1, 0),
            "incomplete_runs": [rel(d) for d in incomplete], "exit_status": exit_status,
            "driver_wall_s": wall, "checker": checked, "main_gpu": ctx["main_gpu"],
            "harness_exception": harness, "tail": tail if harness else "",
            "blocked_after_retry": bool(final) and not harness and model_error(final),
            "window": ctx["window"], "dry_run": ctx["dry"]}


def gpu_status() -> list[dict[str, int]] | None:
    """Temperature and memory of EVERY GPU; None if nvidia-smi is missing or unreadable."""
    proc = sh(["nvidia-smi", "--query-gpu=index,temperature.gpu,memory.used", "--format=csv,noheader,nounits"])
    try:
        rows = [[int(x) for x in line.split(",")] for line in proc.stdout.strip().splitlines()]
    except ValueError:
        return None
    if proc.returncode != 0 or not rows or any(len(r) != 3 for r in rows):
        return None
    return [{"index": i, "temp_c": c, "mem_mib": m} for i, c, m in rows]


def placement(before: list[dict[str, int]] | None, after: list[dict[str, int]] | None,
              main_gpu: int) -> dict[str, Any]:
    """Where the model's memory appeared during the first cell (Ollama may ignore main_gpu)."""
    if not before or not after:
        return {"gpu": None, "note": "undetermined: no GPU reading"}
    delta = {a["index"]: a["mem_mib"] - b["mem_mib"] for a, b in zip(after, before)}
    top = max(delta, key=delta.get)
    if delta[top] < 500:
        return {"gpu": None, "delta_mib": delta, "note": "undetermined: model may already have been resident"}
    note = "as requested" if top == main_gpu else f"DEVIATION: model memory on GPU {top}, main_gpu {main_gpu}"
    return {"gpu": top, "delta_mib": delta, "note": note}


def run_phase(out: Path, freeze_path: Path, phase: str, tag: str, main_gpu: int, cap_min: float,
              dry: bool) -> int:
    freeze = load_freeze(freeze_path)
    if freeze is None:
        return 64
    if phase == "heldout" and not tag:
        tag = (freeze.get("candidate") or {}).get("tag", "")
    checks_done = preflight(phase, tag or "v2", freeze, out, dry)
    for c in checks_done:
        print(f"  preflight {'ok  ' if c['ok'] else 'FAIL'} {c['check']}: {c['detail']}")
    if not all(c["ok"] for c in checks_done):
        print("PREFLIGHT FAILED: nothing was run", file=sys.stderr)
        return 64
    tag = tag or "v2"
    work = open_work(out)
    windows = read_jsonl(work / "windows.jsonl")
    rows_path = work / phase / "rows.jsonl"
    done = {(r["arm"], r["claim"], r["seed"]) for r in read_jsonl(rows_path)}
    ctx = {"main_gpu": main_gpu, "dry": dry, "window": len(windows) + 1,
           "retries_used": sum(r["retries"] for p in CLAIMS for r in read_jsonl(work / p / "rows.jsonl"))}
    prior_s = sum(w["wall_s"] for w in windows)
    started, stop, ran = time.perf_counter(), "completed", 0
    ps = "" if dry else sh(["ollama", "ps"]).stdout
    gpu_place: dict[str, Any] = {"note": "not measured (dry run)"} if dry else {}
    for k, arm, claim, seed in cell_plan(phase, tag):
        if (arm, claim, seed) in done:
            continue
        gpus = None if dry else gpu_status()
        hot = [g for g in gpus or [] if g["temp_c"] >= GPU_STOP_C]
        if BENCH_FLAG.exists():
            stop = "bench_hold"
        elif prior_s + time.perf_counter() - started >= cap_min * 60:
            stop = "cap"
        elif not dry and gpus is None:
            stop = "GPU temperature unreadable (nvidia-smi)"
        elif hot:
            stop = "thermal (" + ", ".join(f"GPU {g['index']} at {g['temp_c']} C" for g in hot) + ")"
        if stop != "completed":
            break
        row = run_cell(work, phase, k, arm, claim, seed, ctx)
        row["gpus_before"] = gpus
        if not gpu_place:
            gpu_place = placement(gpus, gpu_status(), main_gpu)
            if gpu_place["note"].startswith("DEVIATION"):
                print(f"WARNING: {gpu_place['note']} (recorded; the run continues)", file=sys.stderr)
        append_jsonl(rows_path, row)
        ran += 1
        status = "HARNESS EXCEPTION" if row["harness_exception"] else score_run(work, row)["status"]
        print(f"  {phase} k={k} {arm:<4} {claim:<22} seed {seed}: {status}"
              f"{' (retries ' + str(row['retries']) + ')' if row['retries'] else ''}")
    if not dry:
        sh(["ollama", "stop", MODEL])
    append_jsonl(work / "windows.jsonl", {
        "window": ctx["window"], "phase": phase, "tag": tag, "dry_run": dry, "main_gpu": main_gpu,
        "cap_min": cap_min, "gpu_placement": gpu_place,
        "deviations": [gpu_place["note"]] if gpu_place.get("note", "").startswith("DEVIATION") else [],
        "ended_utc": utc(), "wall_s": round(time.perf_counter() - started, 3), "stop_reason": stop,
        "cells_run": ran, "cells_skipped": len(done), "preflight": checks_done, "ollama_ps": ps})
    close_work(out, work)
    print(f"window {ctx['window']} ({phase}): {ran} cells run, {len(done)} skipped, stop: {stop}")
    return 0 if stop == "completed" else 4


def open_work(out: Path) -> Path:
    work = out.with_name(out.name + ".new")
    if work.exists():
        print(f"resuming the interrupted work folder {work}")
    elif out.exists():
        shutil.copytree(out, work)
    else:
        work.mkdir(parents=True)
    return work


def close_work(out: Path, work: Path) -> None:
    old = out.with_name(out.name + ".old")
    if old.exists():
        shutil.rmtree(old)
    if out.exists():
        out.rename(old)
    work.rename(out)
    if old.exists():
        shutil.rmtree(old)


def freeze_candidate(out: Path, freeze_path: Path, tag: str) -> int:
    freeze = load_freeze(freeze_path)
    if freeze is None:
        return 64
    if frozen_changes(freeze):
        print(f"ERROR: frozen files changed: {frozen_changes(freeze)}", file=sys.stderr)
        return 64
    if freeze.get("candidate"):
        print(f"ERROR: candidate already frozen: {freeze['candidate']}", file=sys.stderr)
        return 64
    if out.with_name(out.name + ".new").exists():
        print("ERROR: an interrupted window left p10.new; resume that phase first", file=sys.stderr)
        return 64
    gate = decide(score_phase(out, "dev"), None, None)
    if gate["verdict"] != "INCOMPLETE" or gate.get("final_candidate") != tag:
        print(f"ERROR: the dev gate does not admit {tag!r}: {gate['notes']}", file=sys.stderr)
        return 64
    freeze["candidate"] = {"tag": tag, "code_sha256": sha256_tree(runner.code_files()), "utc": utc()}
    freeze_path.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(f"candidate frozen: {freeze['candidate']}")
    return 0


# ---------------------------------------------------------------- scoring (run records only)
POLICY_LINES = {i: l for i, l in enumerate((EXAMPLE / "data" / "policy.md").read_text("utf-8").splitlines(), 1)}
RULE_AT = interface_v2.rule_index(POLICY_LINES)
RULE_OF_LINE = {line: rule for rule, line in RULE_AT.items()}


def c3_subcategory(interface: str, cited: int, quote: str) -> str:
    found = {n for n, line in POLICY_LINES.items() if checks.quote_matches(quote, line)}
    if not found:
        return "quote_not_in_policy"
    if interface == "v1" and cited in RULE_AT and RULE_AT[cited] in found:
        return "rule_as_line"
    if interface == "v2" and cited not in RULE_AT:
        return "line_as_rule" if cited in found else "unknown_rule_number"
    return "wrong_rule"


def score_run(out: Path, row: dict[str, Any]) -> dict[str, Any]:
    base = {k: row[k] for k in ("phase", "arm", "claim", "seed")}
    base.update(blocked_after_retry=row["blocked_after_retry"], driver_wall_s=row["driver_wall_s"],
                checker=(row["checker"] or {}).get("decision"), retries=row["retries"])
    events = read_jsonl(out / row["run_dir"] / "events.jsonl") if row["run_dir"] else []
    verdicts = [e for e in events if e["type"] == "verdict"]
    if row["harness_exception"] or not verdicts or events[-1]["type"] != "run_end":
        return {**base, "status": "harness_exception", "categories": ["harness_exception"], "correct": False,
                "schema_valid": False, "c3_fail": False, "code_sha256": None, "c3_items": [],
                "citations": [0, 0], "options_ok": False, "tokens": {}, "wall_s": None, "model_calls": None,
                "matches_label": False, "failed_checks": []}
    start, verdict, end = events[0], verdicts[-1], events[-1]
    interface, answer = start.get("interface", "v1"), verdict["answer"]
    label = labels()[row["claim"]]
    failed = [c["check_id"] for c in verdict["checks"] if not c["passed"]]
    reasons = verdict["reasons"]
    cats = list(failed)
    blocked = verdict["status"] == "blocked"
    source_missing = any("policy document was not loaded" in r for r in reasons)
    for name, hit in (("schema_violation", bool(verdict["schema_errors"])),
                      ("budget_exhausted", any("step budget of" in r for r in reasons)),
                      ("text_reply", any("replied with text" in r for r in reasons)),
                      ("no_answer", answer is None and not blocked),
                      ("security_event", bool(verdict["security_events"])),
                      ("source_not_loaded", blocked and source_missing),
                      ("model_error", blocked and not source_missing)):
        if hit:
            cats.append(name)
    schema_valid = answer is not None and not verdict["schema_errors"]
    c3_items, cited_ok, cited_n = [], 0, 0
    if schema_valid:
        for item in answer["items"]:
            ref = item["rule_line"] if interface == "v1" else item["rule_number"]
            line = ref if interface == "v1" else RULE_AT.get(ref, 0)
            rule = RULE_OF_LINE.get(ref) if interface == "v1" else ref
            expected = label["expected_rules"].get(str(item["index"]))
            cited_n += expected is not None
            cited_ok += expected is not None and rule == expected
            if "C3_quotes_in_source" in failed and not checks.quote_matches(item["rule_quote"], POLICY_LINES.get(line, "")):
                c3_items.append(c3_subcategory(interface, ref, item["rule_quote"]))
    options = start["model"].get("options", {})
    matches = workflow.evaluate(verdict, label)["matches_label"]
    totals = end.get("usage", {}).get("totals")
    return {**base, "status": verdict["status"], "categories": cats, "matches_label": matches,
            "correct": verdict["status"] == "passed" and matches, "schema_valid": schema_valid,
            "c3_fail": "C3_quotes_in_source" in failed, "c3_items": c3_items, "failed_checks": failed,
            "citations": [cited_ok, cited_n], "code_sha256": start["code_sha256"],
            "options_ok": options == {"num_ctx": NUM_CTX, "temperature": TEMPERATURE,
                                      "seed": row["seed"], "main_gpu": row["main_gpu"]},
            "tokens": totals if isinstance(totals, dict) else {},
            "wall_s": end.get("resources", {}).get("wall_s"),
            "model_calls": end.get("usage", {}).get("model_calls")}


def score_phase(out: Path, phase: str) -> list[dict[str, Any]]:
    return [score_run(out, row) for row in read_jsonl(out / phase / "rows.jsonl")]


# ---------------------------------------------------------------- decision rule (section 10)
def _n(runs: list[dict[str, Any]], arm: str, key: str = "correct") -> int:
    return sum(1 for r in runs if r["arm"] == arm and r[key])


def _complete(runs: list[dict[str, Any]], arms: list[str], claims: tuple[str, ...]) -> bool:
    cells = Counter((r["arm"], r["claim"]) for r in runs)
    return all(cells[(a, c)] == len(SEEDS) for a in arms for c in claims)


def dev_gate(dev: list[dict[str, Any]], arm: str) -> dict[str, bool]:
    return {"G1": not any("harness_exception" in r["categories"] for r in dev if r["arm"] == arm),
            "G2": _n(dev, arm, "schema_valid") >= _n(dev, "v1", "schema_valid") - 1,
            "G3": _n(dev, arm, "c3_fail") <= _n(dev, "v1", "c3_fail")}


def decide(dev: list[dict[str, Any]], held: list[dict[str, Any]] | None,
           candidate: dict[str, Any] | None) -> dict[str, Any]:
    out: dict[str, Any] = {"verdict": "INCOMPLETE", "qualifier": None, "notes": [], "dev_gate": {}}

    def finish(verdict: str, note: str, qualifier: str | None = None) -> dict[str, Any]:
        out.update(verdict=verdict, qualifier=qualifier)
        out["notes"].append(note)
        return out

    if not _complete(dev, ["v1", "v2"], CLAIMS["dev"]):
        return finish("INCOMPLETE", "DEV phase has cells without a recorded outcome")
    bad_options = [f"{r['arm']} {r['claim']} seed {r['seed']}" for r in dev + (held or [])
                   if not r.get("options_ok", True)]
    if bad_options:
        return finish("VOID", f"model options differ from section 8 in: {', '.join(bad_options)}")
    blocked = {a: sum(r["blocked_after_retry"] for r in dev + (held or []) if r["arm"] == a)
               for a in {r["arm"] for r in dev + (held or [])}}
    out["dev_gate"]["v2"] = dev_gate(dev, "v2")
    revised = any(r["arm"] == "v2.1" for r in dev)
    if all(out["dev_gate"]["v2"].values()):
        if revised:
            return finish("VOID", "a revision v2.1 was run although v2 passed the dev gate")
        final = "v2"
    elif not _complete(dev, ["v2.1"], CLAIMS["dev"]):
        out["revision_allowed"] = not revised
        return finish("INCOMPLETE", "v2 failed the dev gate; one revision v2.1 (10 DEV runs) is allowed")
    else:
        out["dev_gate"]["v2.1"] = dev_gate(dev, "v2.1")
        if not all(out["dev_gate"]["v2.1"].values()):
            return finish("NOT PROMOTED (DEV GATE)", "v2 and its revision v2.1 both failed the dev gate")
        final = "v2.1"
    out["final_candidate"] = final
    if any(n > MAX_BLOCKED_CELLS for n in blocked.values()):
        return finish("VOID", f"more than {MAX_BLOCKED_CELLS} blocked-after-retry cells in one arm: {blocked}")
    if held is None or candidate is None:
        return finish("INCOMPLETE", f"dev gate passed by {final}; held-out phase not run")
    if candidate["tag"] != final:
        return finish("VOID", f"frozen candidate {candidate['tag']} is not the dev-gate candidate {final}")
    if not _complete(held, ["v1", final], CLAIMS["heldout"]):
        return finish("INCOMPLETE", "held-out phase has cells without a recorded outcome")
    if any(r["code_sha256"] != candidate["code_sha256"] for r in held):
        return finish("VOID", "a held-out run is not bound to the frozen candidate code_sha256")
    p1, p2 = _n(held, "v1"), _n(held, final)
    per_claim = {c: {a: sum(r["correct"] for r in held if r["arm"] == a and r["claim"] == c)
                     for a in ("v1", final)} for c in CLAIMS["heldout"]}
    cand_runs = [r for r in dev + held if r["arm"] == final]
    v1_runs = [r for r in dev + held if r["arm"] == "v1"]
    cand_cats = Counter(c for r in cand_runs for c in set(r["categories"]))
    v1_cats = Counter(c for r in v1_runs for c in set(r["categories"]))
    new_cats = sorted(c for c, n in cand_cats.items() if n >= 2 and v1_cats[c] == 0)
    rules = {"R1": p2 - p1 >= 3,
             "R2": all(d[final] >= d["v1"] - 1 for d in per_claim.values()),
             "R3": not new_cats and not cand_cats["security_event"] and not cand_cats["harness_exception"],
             "R4": True}
    c3 = {"v1": _n(held, "v1", "c3_fail"), final: _n(held, final, "c3_fail")}
    out.update(P={"v1": p1, final: p2}, per_claim=per_claim, rules=rules, new_categories=new_cats,
               heldout_c3_runs=c3, fisher_one_sided_p=fisher_one_sided(p2, p1, 3 * len(SEEDS)))
    if all(rules.values()):
        return finish("PROMOTE", f"P({final}) - P(v1) = {p2 - p1} >= 3 and R2-R4 hold")
    if p2 < p1 - 2 or not rules["R2"] or not rules["R3"]:
        return finish("NOT PROMOTED", "P(v2) < P(v1) - 2, or R2 or R3 failed", "harmful")
    mechanism = c3[final] <= c3["v1"] - 5 and c3["v1"] >= 5
    return finish("NOT PROMOTED", f"R1 failed: P({final}) - P(v1) = {p2 - p1} < 3",
                  "null: mechanism confirmed, not promoted" if mechanism else "null")


def fisher_one_sided(a: int, b: int, n: int) -> float:
    """P(v2 successes >= a) under the hypergeometric null, a of n (v2) against b of n (v1)."""
    k = a + b
    return sum(math.comb(k, x) * math.comb(2 * n - k, n - x)
               for x in range(a, min(k, n) + 1)) / math.comb(2 * n, n)


# ---------------------------------------------------------------- analysis and report
def _stat(values: list[Any]) -> dict[str, Any]:
    vals = [v for v in values if isinstance(v, (int, float))]
    return {"n": len(vals), "median": statistics.median(vals) if vals else None,
            "total": round(sum(vals), 3) if vals else None}


def summarise(runs: list[dict[str, Any]]) -> dict[str, Any]:
    return {"runs": len(runs), "P_correct_deliverables": sum(r["correct"] for r in runs),
            "S1_label_match": sum(r["matches_label"] for r in runs),
            "S2_passed": sum(r["status"] == "passed" for r in runs),
            "schema_valid": sum(r["schema_valid"] for r in runs),
            "S3_c3": {"runs": sum(r["c3_fail"] for r in runs), "items": sum(len(r["c3_items"]) for r in runs),
                      "subcategories": dict(Counter(c for r in runs for c in r["c3_items"]))},
            "S4_failed_checks": dict(Counter(c for r in runs for c in r["failed_checks"])),
            "categories": dict(Counter(c for r in runs for c in set(r["categories"]))),
            "S5_tokens": {k: _stat([r["tokens"].get(k) for r in runs]) for k in ("prompt_eval_count", "eval_count")},
            "S6_wall_s": {"run": _stat([r["wall_s"] for r in runs]),
                          "driver_process": _stat([r["driver_wall_s"] for r in runs])},
            "S7_model_calls": _stat([r["model_calls"] for r in runs]),
            "S8_citation_accuracy": [sum(r["citations"][0] for r in runs), sum(r["citations"][1] for r in runs)],
            "S9_checker": dict(Counter((r["checker"] or "none").split(":")[0] for r in runs)),
            "blocked_after_retry": sum(r["blocked_after_retry"] for r in runs),
            "retries": sum(r["retries"] for r in runs),
            "options_assertion_failed": sum(not r["options_ok"] for r in runs)}


def analyse(out: Path, freeze_path: Path, dry: bool) -> int:
    if out.with_name(out.name + ".new").exists():
        print("ERROR: an interrupted window left p10.new; resume that phase first", file=sys.stderr)
        return 64
    if not out.exists():
        print(f"ERROR: no P10 output at {out}", file=sys.stderr)
        return 64
    freeze = load_freeze(freeze_path)
    if freeze is None:
        return 64
    dev, held = score_phase(out, "dev"), score_phase(out, "heldout")
    decision = decide(dev, held or None, freeze.get("candidate"))
    changed = frozen_changes(freeze) + (["v1 goldens"] if goldens_now() != GOLDENS else [])
    if changed:
        decision.update(verdict="VOID", qualifier=None)
        decision["notes"].append(f"frozen files changed since the freeze: {', '.join(changed)}")
    windows = read_jsonl(out / "windows.jsonl")
    metrics = {phase: {arm: summarise([r for r in runs if r["arm"] == arm])
                       for arm in sorted({r["arm"] for r in runs})}
               for phase, runs in (("dev (S10, development evidence)", dev), ("heldout", held))}
    result = {"generated_utc": utc(), "generator": "examples/ref01_expense_report/experiments/p10_trials.py",
              "protocol": "P10_PREREGISTRATION.md v1.0", "dry_run": dry, **decision,
              "candidate": freeze.get("candidate"), "metrics": metrics,
              "windows": [{k: w[k] for k in ("window", "phase", "tag", "wall_s", "stop_reason", "cells_run",
                                              "main_gpu", "dry_run")} for w in windows],
              "total_window_s": round(sum(w["wall_s"] for w in windows), 3),
              "note": "One model, synthetic claims, 15 held-out runs per arm; Fisher p and the per-claim "
                      "table are information only, not significance claims. Checker results are descriptive."}
    work = open_work(out)
    (work / "P10_RESULTS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (work / "P10_RESULTS.md").write_text(render(result), encoding="utf-8")
    close_work(out, work)
    print(render(result))
    return 0


def render(r: dict[str, Any]) -> str:
    lines = [f"# P10 results (generated){' - DRY RUN, scripted model, not evidence' if r['dry_run'] else ''}", "",
             f"Generated {r['generated_utc']} by `{r['generator']}` under {r['protocol']}.", "",
             f"**Decision: {r['verdict']}**" + (f" ({r['qualifier']})" if r["qualifier"] else ""), "",
             *[f"- {n}" for n in r["notes"]],
             f"- Dev gate: {json.dumps(r['dev_gate'])}"]
    if "rules" in r:
        lines += [f"- Rules: {json.dumps(r['rules'])}; new failure categories: {r['new_categories']}",
                  f"- P (held-out correct deliverables of 15): {json.dumps(r['P'])}; "
                  f"held-out runs with a C3 failure: {json.dumps(r['heldout_c3_runs'])}",
                  f"- One-sided Fisher p (information only): {r['fisher_one_sided_p']:.4f}", "",
                  "| Held-out claim | " + " | ".join(next(iter(r["per_claim"].values()))) + " |",
                  "|---|" + "---|" * len(next(iter(r["per_claim"].values())))]
        lines += [f"| {c} | " + " | ".join(str(v) for v in d.values()) + " |" for c, d in r["per_claim"].items()]
    lines += ["", f"Windows: {len(r['windows'])}, total {r['total_window_s']} s "
                  f"({'; '.join(f'{w['phase']} {w['wall_s']} s {w['stop_reason']}' for w in r['windows'])}).", ""]
    for phase, arms in r["metrics"].items():
        lines += [f"## {phase}", "", "| Metric | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
        for key in next(iter(arms.values()), {}):
            lines.append(f"| {key} | " + " | ".join(f"`{json.dumps(s[key])}`" for s in arms.values()) + " |")
        lines.append("")
    lines.append(r["note"])
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- entry point
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P10 driver (see the module docstring)")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--phase", choices=["dev", "heldout"])
    action.add_argument("--freeze-candidate", metavar="TAG", choices=["v2", "v2.1"])
    action.add_argument("--analyse", action="store_true")
    action.add_argument("--init-freeze", action="store_true", help="write the freeze manifest (once)")
    parser.add_argument("--candidate-tag", choices=["v2", "v2.1"], default=None)
    parser.add_argument("--main-gpu", type=int, default=1, help="HANDBOOK_MAIN_GPU for every run (protocol: 1)")
    parser.add_argument("--cap-min", type=float, default=60.0, help="wall-time cap over all windows, minutes")
    parser.add_argument("--dry-run", action="store_true", help="scripted model, no Ollama, temp output")
    parser.add_argument("--out", type=Path, default=None, help="output folder (default reviews/evidence/p10)")
    args = parser.parse_args(argv)
    if not args.dry_run and args.main_gpu != 1:
        print(f"ERROR: --main-gpu {args.main_gpu}: live runs use the protocol value 1", file=sys.stderr)
        return 64
    if not args.dry_run and args.out is not None and args.out.resolve() != FINAL.resolve():
        print(f"ERROR: live output goes only to {FINAL}", file=sys.stderr)
        return 64
    if args.cap_min > MAX_CAP_MIN:
        print(f"WARNING: --cap-min {args.cap_min} capped at {MAX_CAP_MIN} (section 11)", file=sys.stderr)
        args.cap_min = MAX_CAP_MIN
    out = args.out or (Path(tempfile.gettempdir()) / "p10_dryrun" / "p10" if args.dry_run else FINAL)
    out = out.resolve()
    marker = out.parent / DRY_MARK
    if args.dry_run and out == FINAL.resolve():
        print("ERROR: a dry run never writes to reviews/evidence/p10", file=sys.stderr)
        return 64
    if not args.dry_run and marker.exists():
        print(f"ERROR: {out.parent} holds dry-run output; live runs need their own folder", file=sys.stderr)
        return 64
    freeze_path = out.parent / "p10_freeze.json" if args.dry_run else FREEZE
    if args.dry_run and not (args.phase or args.freeze_candidate or args.analyse or args.init_freeze):
        if out.parent.exists() and not marker.exists():
            print(f"ERROR: {out.parent} exists and is not a dry-run folder", file=sys.stderr)
            return 64
        shutil.rmtree(out.parent, ignore_errors=True)
        out.parent.mkdir(parents=True)
        marker.write_text("P10 dry-run output: scripted model, not evidence.\n", encoding="utf-8")
        steps = [lambda: init_freeze(freeze_path),
                 lambda: run_phase(out, freeze_path, "dev", "v2", args.main_gpu, args.cap_min, True),
                 lambda: freeze_candidate(out, freeze_path, "v2"),
                 lambda: run_phase(out, freeze_path, "heldout", "v2", args.main_gpu, args.cap_min, True),
                 lambda: analyse(out, freeze_path, True)]
        for step in steps:
            code = step()
            if code:
                return code
        print(f"dry-run output: {out}")
        return 0
    if args.dry_run:
        out.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("P10 dry-run output: scripted model, not evidence.\n", encoding="utf-8")
    if args.init_freeze:
        return init_freeze(freeze_path)
    if args.phase:
        tag = args.candidate_tag or ("v2" if args.phase == "dev" else "")
        return run_phase(out, freeze_path, args.phase, tag, args.main_gpu, args.cap_min, args.dry_run)
    if args.freeze_candidate:
        return freeze_candidate(out, freeze_path, args.freeze_candidate)
    if args.analyse:
        return analyse(out, freeze_path, args.dry_run)
    parser.print_help()
    return 64


if __name__ == "__main__":
    sys.exit(main())
