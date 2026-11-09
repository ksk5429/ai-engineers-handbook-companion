"""Repeated live trials of REF01 through a local Ollama model, then the checker.

  python live_trials.py --model qwen2.5:7b --trials 5 --temperature 0.7

For each claim and each seed: one run (separate process), then the completion
checker, then a label comparison. Writes reviews/evidence/ref01_live/LIVE.json/.md.

This is an illustration on a small sample with one local model. It is not a
benchmark, and its rates must not be read as the model's general reliability.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FINAL = REPO / "reviews" / "evidence" / "ref01_live"
OUT = FINAL.with_name("ref01_live.new")      # swapped in only after all trials finish
PY = sys.executable
CLAIMS = {"claim_normal.json": "normal", "claim_injection.json": "injection_resisted"}
BENCH_FLAG = Path(os.environ.get("HANDBOOK_HOLD_FLAG", r"C:\ProgramData\paperkit-locks\bench_hold.flag"))


def sh(args: list[str], cwd: Path = HERE) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    except FileNotFoundError as exc:                 # e.g. ollama not on PATH
        return subprocess.CompletedProcess(args, 127, "", str(exc))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.7)
    args = parser.parse_args()
    sys.path.insert(0, str(HERE))
    from docassist.workflow import evaluate

    if OUT.exists():
        shutil.rmtree(OUT)
    runs = OUT / "runs"
    runs.mkdir(parents=True)
    labels = {claim: json.loads((HERE / "fixtures" / "cases" / f"{case}.json").read_text("utf-8"))["label"]
              for claim, case in CLAIMS.items()}
    version = sh(["ollama", "--version"]).stdout.strip()
    rows: list[dict[str, Any]] = []
    ps_snapshot = ""
    for seed in range(1, args.trials + 1):
        for claim in CLAIMS:
            if BENCH_FLAG.exists():
                print("bench_hold.flag appeared: stopping", file=sys.stderr)
                return 4
            before = {p.name for p in runs.iterdir()}
            proc = sh([PY, "run.py", "--ollama", args.model, "--claim", claim, "--seed", str(seed),
                       "--temperature", str(args.temperature), "--runs-dir", str(runs)])
            new = [p for p in sorted(runs.iterdir()) if p.is_dir() and p.name not in before]
            if not ps_snapshot:
                ps_snapshot = sh(["ollama", "ps"]).stdout
            row: dict[str, Any] = {"claim": claim, "seed": seed, "exit_status": proc.returncode}
            if not new:
                row.update(status="blocked", reasons=[proc.stdout[-300:] + proc.stderr[-300:]])
                rows.append(row)
                continue
            run_dir = new[0]
            events = [json.loads(l) for l in (run_dir / "events.jsonl").read_text("utf-8").splitlines()]
            verdict = [e for e in events if e["type"] == "verdict"][-1]
            end = events[-1]
            checked = json.loads(sh([PY, "checker.py", str(run_dir)]).stdout)
            row.update(run_dir=run_dir.name, status=verdict["status"], reasons=verdict["reasons"],
                       tools=[(e["name"], e.get("ok")) for e in events if e["type"] == "tool_result"],
                       model_calls=end.get("usage", {}).get("model_calls"),
                       usage=end.get("usage", {}).get("totals"),
                       wall_s=end.get("resources", {}).get("wall_s"),
                       checker=checked["decision"],
                       label=evaluate(verdict, labels[claim]))
            rows.append(row)
            print(f"seed {seed} {claim:<22} {row['status']:<8} label_match="
                  f"{row['label']['matches_label']}  {'; '.join(row['reasons'])[:120]}")
    record = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "generator": "examples/ref01_expense_report/live_trials.py",
              "route": "ollama (local)", "model": args.model, "runtime": version,
              "temperature": args.temperature, "seeds": list(range(1, args.trials + 1)),
              "environment": {"python": platform.python_version(), "os": platform.platform()},
              "ollama_ps_during_run": ps_snapshot, "rows": rows,
              "note": "Illustration on a small sample, one local model; not a benchmark."}
    (OUT / "LIVE.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (OUT / "LIVE.md").write_text(render(record), encoding="utf-8")
    print(render(record))
    if FINAL.exists():
        shutil.rmtree(FINAL)
    OUT.rename(FINAL)
    return 0


def render(r: dict[str, Any]) -> str:
    out = [f"# REF01 live trials (generated): {r['model']} via {r['route']}", "",
           f"Generated {r['generated_utc']} by `{r['generator']}`. {r['note']}", "",
           f"- Runtime: {r['runtime']}; temperature {r['temperature']}; seeds {r['seeds']}",
           f"- Environment: Python {r['environment']['python']} on {r['environment']['os']}", "",
           "`ollama ps` during the first trial:", "", "```", r["ollama_ps_during_run"].strip(), "```", "",
           "| Claim | Seed | Status | Matches label | Checker | Calls | Prompt tok | Output tok | Wall s | Reasons |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for row in r["rows"]:
        usage = row.get("usage") if isinstance(row.get("usage"), dict) else {}
        out.append(f"| {row['claim']} | {row['seed']} | {row['status']} | "
                   f"{row.get('label', {}).get('matches_label', 'n/a')} | {row.get('checker', 'n/a')} | "
                   f"{row.get('model_calls', 'n/a')} | {usage.get('prompt_eval_count', 'n/a')} | "
                   f"{usage.get('eval_count', 'n/a')} | {row.get('wall_s', 'n/a')} | "
                   f"{'; '.join(row.get('reasons', []))[:160]} |")
    total = len(r["rows"])
    passed = sum(1 for x in r["rows"] if x["status"] == "passed")
    correct = sum(1 for x in r["rows"] if x.get("label", {}).get("matches_label"))
    accepted_wrong = sum(1 for x in r["rows"] if x["status"] == "passed"
                         and not x.get("label", {}).get("matches_label"))
    out += ["", f"Runs: {total}. Passed the runner's checks: {passed}. Matched the human label: "
                f"{correct}. Passed the checks but did NOT match the label: {accepted_wrong}.", ""]
    return "\n".join(out)


if __name__ == "__main__":
    sys.exit(main())
