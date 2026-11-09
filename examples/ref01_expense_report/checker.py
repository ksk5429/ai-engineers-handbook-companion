"""Completion checker: decides whether a run directory is acceptable evidence that
the task was completed. It is separate from the runner and re-implements what it
needs (hashing, quote lookup, sums) instead of importing the runner's checks, so a
bug in one is less likely to be repeated in the other. It trusts no narrative: only
the event log, the artifacts and the current input files count.

  python checker.py runs/<run_id> [--data-dir data] [--ledger runs/ledger.jsonl]

Exit status: 0 accepted, 1 rejected, 64 usage error. Output: JSON with each check.

Limits: the checker cannot tell whether the event log itself was produced by the
runner or forged by someone who also recomputed every hash. Keeping the run.json
hash somewhere the editor cannot write (for example a separate system) closes that
gap; this local example does not.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CODE_GLOBS = [("docassist", "*.py"), ("schemas", "*.json")]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_sha(paths: list[Path]) -> str:          # same definition as the runner, own code
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.as_posix()):
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def _code_sha(root: Path) -> str:
    files = [p for folder, pattern in CODE_GLOBS for p in sorted((root / folder).glob(pattern))]
    return _tree_sha(files + [root / "task_contract.json"])


def _result(check_id: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check_id": check_id, "passed": passed, "detail": detail}


# --8<-- [start:checker]
def check_run(run_dir: Path, data_dir: Path, ledger: Path, code_root: Path = HERE) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    needed = ["events.jsonl", "report.md", "run.json"]
    missing = [n for n in needed if not (run_dir / n).is_file()]
    results.append(_result("K1_artifacts_present", not missing,
                           f"missing: {missing}" if missing else "all present"))
    if missing:
        return _decide(results, None)

    try:
        events = [json.loads(l) for l in (run_dir / "events.jsonl").read_text("utf-8").splitlines()
                  if l.strip()]
        summary = json.loads((run_dir / "run.json").read_text("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        results.append(_result("K2_record_integrity", False, f"unreadable record: {exc}"))
        return _decide(results, None)
    problems = []
    if [e.get("seq") for e in events] != list(range(1, len(events) + 1)):
        problems.append("event sequence numbers are not 1..n")
    if not events or events[0].get("type") != "run_start" or events[-1].get("type") != "run_end":
        problems.append("log does not start with run_start and end with run_end")
    if not any(e.get("type") == "verdict" for e in events):
        problems.append("no verdict event")
    if summary.get("events_sha256") != _sha(run_dir / "events.jsonl"):
        problems.append("events.jsonl does not match the hash in run.json")
    if summary.get("report_sha256") != _sha(run_dir / "report.md"):
        problems.append("report.md does not match the hash in run.json")
    results.append(_result("K2_record_integrity", not problems, "; ".join(problems) or "ok"))
    if problems:
        return _decide(results, None)

    start, end = events[0], events[-1]
    verdict = [e for e in events if e["type"] == "verdict"][-1]
    stale = []
    for role in ("claim", "policy"):
        recorded = start["inputs"][role]
        path = data_dir / recorded["name"]
        current = _sha(path) if path.is_file() else None
        if current != recorded["sha256"]:
            stale.append(f"{role} {recorded['name']} changed or missing since the run")
    if _code_sha(code_root) != start["code_sha256"]:
        stale.append("code or contract changed since the run")
    results.append(_result("K3_bound_to_current_inputs", not stale, "; ".join(stale) or "ok"))

    status = verdict["status"]
    claims_pass = status == "passed"
    inconsistent = []
    if not (summary.get("status") == end.get("status") == status):
        inconsistent.append(f"status differs: run.json {summary.get('status')}, "
                            f"run_end {end.get('status')}, verdict {status}")
    if claims_pass:
        if verdict["schema_errors"] or verdict["security_events"]:
            inconsistent.append("passed despite schema errors or security events")
        if not verdict["checks"] or not all(c["passed"] for c in verdict["checks"]):
            inconsistent.append("passed although a recorded check failed or none ran")
        reads = [e for e in events if e["type"] == "tool_result" and e["name"] == "read_document"
                 and e["ok"] and e["result"].get("sha256") == start["inputs"]["policy"]["sha256"]]
        if not reads:
            inconsistent.append("no successful read of the recorded policy in the log")
    submits = [e for e in events if e["type"] == "model_turn" and e.get("name") == "submit_answer"]
    if verdict.get("answer") is not None and (not submits or submits[-1].get("input") != verdict["answer"]):
        inconsistent.append("verdict answer differs from the answer the model submitted")
    results.append(_result("K4_status_supported_by_log", not inconsistent,
                           "; ".join(inconsistent) or "ok"))

    results.append(_check_answer(verdict.get("answer"), data_dir, start, claims_pass))
    results.append(_check_report(run_dir / "report.md", status, verdict.get("answer")))
    results.append(_check_ledger(ledger, start, verdict, claims_pass))
    return _decide(results, status)
# --8<-- [end:checker]


def _check_answer(answer: Any, data_dir: Path, start: dict[str, Any], claims_pass: bool) -> dict[str, Any]:
    if not claims_pass:
        return _result("K5_answer_against_source", True, "not applicable: run did not claim to pass")
    policy = data_dir / start["inputs"]["policy"]["name"]
    claim_path = data_dir / start["inputs"]["claim"]["name"]
    if not policy.is_file() or not claim_path.is_file():
        return _result("K5_answer_against_source", False, "input file missing")
    lines = policy.read_text("utf-8").splitlines()
    claim = json.loads(claim_path.read_text("utf-8"))
    problems = []
    try:
        total = sum(Decimal(i["allowed"]) for i in answer["items"])
        if total != Decimal(answer["total_allowed"]):
            problems.append(f"total {answer['total_allowed']} != item sum {total}")
        for item in answer["items"]:
            n = item["rule_line"]
            line = lines[n - 1] if 1 <= n <= len(lines) else ""
            q, l = " ".join(item["rule_quote"].split()), " ".join(line.split())
            if not q or (q != l and q != re.sub(r"^\d+\.\s*", "", l)):
                problems.append(f"item {item['index']}: quote not on line {n}")
        if sorted(i["index"] for i in answer["items"]) != sorted(i["index"] for i in claim["items"]):
            problems.append("items do not match the claim")
        if answer.get("claim_id") != claim.get("claim_id"):
            problems.append(f"claim id {answer.get('claim_id')!r} differs from the claim {claim.get('claim_id')!r}")
    except (KeyError, TypeError, AttributeError, InvalidOperation) as exc:
        problems.append(f"answer unreadable: {exc!r}")
    return _result("K5_answer_against_source", not problems, "; ".join(problems) or "ok")


def _check_report(report: Path, status: str, answer: Any) -> dict[str, Any]:
    text = report.read_text("utf-8")
    problems = []
    match = re.search(r"Run status: \*\*(\w+)\*\*", text)
    if not match or match.group(1) != status:
        problems.append(f"report states status {match.group(1) if match else 'none'}, log says {status}")
    if status == "passed" and isinstance(answer, dict):
        if f"Total allowed: {answer['total_allowed']} EUR" not in text:
            problems.append("report total differs from the recorded answer")
    return _result("K6_report_matches_record", not problems, "; ".join(problems) or "ok")


def _check_ledger(ledger: Path, start: dict[str, Any], verdict: dict[str, Any],
                  claims_pass: bool) -> dict[str, Any]:
    if not claims_pass:
        return _result("K7_published_once", True, "not applicable: nothing should be published")
    entries = [json.loads(l) for l in ledger.read_text("utf-8").splitlines() if l.strip()] \
        if ledger.is_file() else []
    a = verdict["answer"]
    core = {"claim_id": a["claim_id"], "decision": a["decision"], "total_allowed": a["total_allowed"],
            "items": sorted([i["index"], i["allowed"]] for i in a["items"])}
    answer_sha = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()
    claim_id = verdict["answer"]["claim_id"]
    mine = [e for e in entries if e["key"] == claim_id]
    ok = len(mine) == 1 and mine[0]["answer_sha256"] == answer_sha
    return _result("K7_published_once", ok,
                   f"{len(mine)} ledger entr{'y' if len(mine) == 1 else 'ies'} for {claim_id}")


def _decide(results: list[dict[str, Any]], status: str | None) -> dict[str, Any]:
    record_valid = all(r["passed"] for r in results) and len(results) == 7
    accepted = record_valid and status == "passed"
    if accepted:
        decision = "accepted"
    elif record_valid:
        decision = f"rejected: the record is valid but the run status is {status}"
    else:
        decision = "rejected: " + "; ".join(r["check_id"] for r in results if not r["passed"])
    return {"decision": decision, "accepted": accepted, "record_valid": record_valid,
            "run_status": status, "checks": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Completion checker for one run directory")

    def _usage_error(message: str) -> None:            # documented exit status 64, not argparse's 2
        parser.print_usage(sys.stderr)
        print(f"error: {message}", file=sys.stderr)
        raise SystemExit(64)
    parser.error = _usage_error  # type: ignore[method-assign]
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--data-dir", type=Path, default=HERE / "data")
    parser.add_argument("--ledger", type=Path, default=None)
    args = parser.parse_args(argv)
    if not args.run_dir.is_dir():
        print(f"not a directory: {args.run_dir}", file=sys.stderr)
        return 64
    ledger = args.ledger or args.run_dir.parent / "ledger.jsonl"
    outcome = check_run(args.run_dir, args.data_dir, ledger)
    print(json.dumps(outcome, indent=2))
    return 0 if outcome["accepted"] else 1


if __name__ == "__main__":
    sys.exit(main())
