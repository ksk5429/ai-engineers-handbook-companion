r"""Live trials of REF01 through the hosted Anthropic API, with a cumulative token cap.

Run by the OWNER in their own terminal (the key must never pass through the
authoring session):  pwsh ..\..\scripts\run_hosted_trials.ps1

  python hosted_trials.py --trials 2 --max-total-tokens 400000

Each run is a separate `run.py --anthropic` process (which has its own per-run
cap). This script adds up every token category the API reports across runs and
stops before starting a run once the cumulative total reaches the cap. It never
reads, prints or stores the key. Results: reviews/evidence/ref01_hosted/.
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
FINAL = REPO / "reviews" / "evidence" / "ref01_hosted"
OUT = FINAL.with_name("ref01_hosted.new")
PY = sys.executable
CLAIMS = ["claim_normal.json", "claim_injection.json",
          "claim_heldout_1.json", "claim_heldout_2.json", "claim_heldout_3.json"]


def labels() -> dict[str, dict[str, Any]]:
    data = json.loads((HERE / "experiments" / "P10_labels.json").read_text("utf-8"))["labels"]
    return {k: v for k, v in data.items()}


def run_tokens(run_dir: Path) -> int:
    events = [json.loads(l) for l in (run_dir / "events.jsonl").read_text("utf-8").splitlines() if l.strip()]
    total = 0
    for e in events:
        usage = e.get("usage") if e.get("type") == "model_turn" else None
        if isinstance(usage, dict):
            total += sum(v for k, v in usage.items() if k.endswith("_tokens") and isinstance(v, int))
    return total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=2)
    parser.add_argument("--max-total-tokens", type=int, default=400_000)
    args = parser.parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set in this process: nothing was sent.", file=sys.stderr)
        return 2
    sys.path.insert(0, str(HERE))
    from docassist.workflow import evaluate

    if OUT.exists():
        shutil.rmtree(OUT)
    runs = OUT / "runs"
    runs.mkdir(parents=True)
    lab = labels()
    rows: list[dict[str, Any]] = []
    spent = 0
    stopped = None
    for trial in range(1, args.trials + 1):
        for claim in CLAIMS:
            if spent >= args.max_total_tokens:
                stopped = f"token cap reached before trial {trial}, {claim} ({spent} >= {args.max_total_tokens})"
                break
            before = {p.name for p in runs.iterdir()}
            env = {**os.environ, "HANDBOOK_MAX_TOTAL_TOKENS": str(max(1, args.max_total_tokens - spent))}
            proc = subprocess.run([PY, "run.py", "--anthropic", "--claim", claim, "--runs-dir", str(runs)],
                                  cwd=HERE, capture_output=True, text=True, encoding="utf-8", env=env)
            new = [p for p in sorted(runs.iterdir()) if p.is_dir() and p.name not in before]
            row: dict[str, Any] = {"claim": claim, "trial": trial, "exit_status": proc.returncode}
            if not new:
                row.update(status="blocked", reasons=[(proc.stdout + proc.stderr)[-400:]])
                rows.append(row)
                print(f"trial {trial} {claim:<22} blocked: {row['reasons'][0][-160:]}")
                continue
            run_dir = new[0]
            events = [json.loads(l) for l in (run_dir / "events.jsonl").read_text("utf-8").splitlines() if l.strip()]
            verdict = [e for e in events if e["type"] == "verdict"]
            verdict = verdict[-1] if verdict else {"status": "blocked", "reasons": ["no verdict"]}
            tokens = run_tokens(run_dir)
            spent += tokens
            label = lab.get(claim)
            row.update(run_dir=run_dir.name, status=verdict["status"], reasons=verdict.get("reasons", []),
                       tokens=tokens, cumulative_tokens=spent,
                       model=events[0].get("model", {}).get("model"),
                       label=evaluate(verdict, label) if label else None)
            rows.append(row)
            print(f"trial {trial} {claim:<22} {row['status']:<8} label_match="
                  f"{(row['label'] or {}).get('matches_label')} tokens={tokens} cumulative={spent}")
        if stopped:
            break
    record = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "generator": "examples/ref01_expense_report/hosted_trials.py", "route": "anthropic (hosted)",
              "max_total_tokens": args.max_total_tokens, "tokens_spent_reported": spent,
              "stopped": stopped, "environment": {"python": platform.python_version(), "os": platform.platform()},
              "note": "Owner-run hosted trials; token counts are the API's own usage fields; money cost is "
                      "not computed here (see the provider's billing page).", "rows": rows}
    (OUT / "HOSTED.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    lines = ["# REF01 hosted trials (generated)", "", f"{record['note']}", "",
             f"- Route: {record['route']}; cap {args.max_total_tokens} tokens; reported tokens {spent}; "
             f"stopped: {stopped or 'no'}", "",
             "| Claim | Trial | Status | Matches label | Tokens | Reasons |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['claim']} | {r['trial']} | {r['status']} | {(r.get('label') or {}).get('matches_label', 'n/a')} "
                     f"| {r.get('tokens', '-')} | {'; '.join(r.get('reasons', []))[:160]} |")
    (OUT / "HOSTED.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if FINAL.exists():
        shutil.rmtree(FINAL)
    OUT.rename(FINAL)
    print(f"\nwrote {FINAL}\\HOSTED.md; tokens reported: {spent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
