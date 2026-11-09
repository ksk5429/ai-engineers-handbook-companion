"""Produce the evidence record for REF01 by actually running things.

  python evidence.py            (writes reviews/evidence/ref01/EVIDENCE.json and .md)

Every result below comes from a subprocess exit status or a file the runner wrote.
Nothing is typed in by hand. Seeded defects are artificial edits made by this script
to test the checker; they are labelled "seeded" and are not observed model failures.
"""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FINAL = REPO / "reviews" / "evidence" / "ref01"
OUT = FINAL.with_name("ref01.new")          # built here, swapped in only on success
RUNS = OUT / "runs"
PY = sys.executable


def sh(args: list[str], cwd: Path = HERE) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    except FileNotFoundError as exc:                 # e.g. git not installed
        return {"command": " ".join(args), "exit_status": None, "stdout": "", "stderr": str(exc)}
    return {"command": " ".join(Path(a).name if a == PY else a for a in args),
            "exit_status": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def newest_run(before: set[str], runs: Path) -> Path:
    return next(p for p in sorted(runs.iterdir()) if p.is_dir() and p.name not in before)


def run_cli(*args: str, runs: Path = RUNS) -> tuple[dict[str, Any], Path]:
    runs.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in runs.iterdir()}
    result = sh([PY, "run.py", *args, "--runs-dir", str(runs)])
    return result, newest_run(before, runs)


def check(run_dir: Path, data: Path | None = None) -> dict[str, Any]:
    args = [PY, "checker.py", str(run_dir), "--ledger", str(RUNS / "ledger.jsonl")]
    if data:
        args += ["--data-dir", str(data)]
    result = sh(args)
    return {"exit_status": result["exit_status"], **json.loads(result["stdout"])}


def rehash(run_dir: Path) -> None:
    """What a careful forger would do: make run.json hashes match the edited files."""
    summary = json.loads((run_dir / "run.json").read_text("utf-8"))
    for key, name in (("events_sha256", "events.jsonl"), ("report_sha256", "report.md")):
        summary[key] = hashlib.sha256((run_dir / name).read_bytes()).hexdigest()
    (run_dir / "run.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def copy_run(src: Path, name: str) -> Path:
    dst = RUNS / f"seeded-{name}"
    shutil.copytree(src, dst)
    return dst


def edit_events(run_dir: Path, edit: Any) -> None:
    path = run_dir / "events.jsonl"
    events = [json.loads(l) for l in path.read_text("utf-8").splitlines() if l.strip()]
    events = edit(events)
    for i, event in enumerate(events, start=1):
        event["seq"] = i
    path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    RUNS.mkdir(parents=True)
    record: dict[str, Any] = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generator": "examples/ref01_expense_report/evidence.py",
        "environment": {"python": platform.python_version(), "os": platform.platform()},
        "git_head": (lambda g: g["stdout"].strip() if g["exit_status"] == 0 else "no commit yet")(
            sh(["git", "rev-parse", "HEAD"], REPO)),
        "git_dirty": bool(sh(["git", "status", "--porcelain", "examples"], REPO)["stdout"].strip()),
    }
    sys.path.insert(0, str(HERE))
    from docassist.runner import code_files, decision_fingerprint
    from docassist.runlog import sha256_tree
    record["code_sha256"] = sha256_tree(code_files())

    tests = sh([PY, "-m", "unittest", "discover", "-s", "tests"])
    record["unit_tests"] = {"command": tests["command"], "exit_status": tests["exit_status"],
                            "summary": tests["stderr"].strip().splitlines()[-3:]}

    # 1. Every constructed case, each in its own process.
    cases = []
    case_dirs: dict[str, Path] = {}
    for path in sorted((HERE / "fixtures" / "cases").glob("*.json")):
        case = json.loads(path.read_text("utf-8"))
        result, run_dir = run_cli("--case", case["case_id"])
        case_dirs[case["case_id"]] = run_dir
        events = [json.loads(l) for l in (run_dir / "events.jsonl").read_text("utf-8").splitlines()]
        end = events[-1]
        verdict = [e for e in events if e["type"] == "verdict"][-1]
        cases.append({"case_id": case["case_id"], "constructed": True,
                      "expected_status": case["expected"]["status"],
                      "observed_status": verdict["status"], "exit_status": result["exit_status"],
                      "as_expected": verdict["status"] == case["expected"]["status"],
                      "failed_checks": [c["check_id"] for c in verdict["checks"] if not c["passed"]],
                      "reasons": verdict["reasons"], "run_dir": run_dir.name,
                      "resources": end.get("resources"), "usage": end.get("usage")})
    record["cases"] = cases

    # 2. Crash and resume, as separate processes.
    crash, crash_dir = run_cli("--case", "normal", "--crash-after", "2")
    resume = sh([PY, "run.py", "--resume", str(crash_dir), "--runs-dir", str(RUNS)])
    tool_runs = [json.loads(l) for l in (crash_dir / "events.jsonl").read_text("utf-8").splitlines()]
    record["recovery"] = {
        "crash": {"exit_status": crash["exit_status"], "stderr": crash["stderr"].strip()},
        "resume": {"exit_status": resume["exit_status"]},
        "tool_executions": [(e["name"], e["input"]) for e in tool_runs if e["type"] == "tool_result"],
        "event_types": [e["type"] for e in tool_runs], "run_dir": crash_dir.name}
    pub_runs = OUT / "publish_demo_runs"
    pub_crash, pub_dir = run_cli("--case", "injection_resisted", "--crash-at-publish", runs=pub_runs)
    pub_resume = sh([PY, "run.py", "--resume", str(pub_dir), "--runs-dir", str(pub_runs)])
    record["recovery"]["publish_crash"] = {
        "crash_exit": pub_crash["exit_status"], "resume_exit": pub_resume["exit_status"],
        "publish_events": [e for e in (json.loads(l) for l in (pub_dir / "events.jsonl")
                           .read_text("utf-8").splitlines()) if e["type"] == "publish"],
        "ledger_lines": len((pub_runs / "ledger.jsonl").read_text("utf-8").splitlines())}
    interrupted, interrupted_dir = run_cli("--case", "normal", "--crash-after", "1")

    # 3. Checker evaluation on labelled submissions.
    stale_data = OUT / "stale_data"
    shutil.copytree(HERE / "data", stale_data)
    policy = stale_data / "policy.md"
    policy.write_text(policy.read_text("utf-8").replace("90.00 EUR per night", "80.00 EUR per night"),
                      encoding="utf-8")

    d_missing = copy_run(case_dirs["normal"], "missing_report")
    (d_missing / "report.md").unlink()
    d_forged = copy_run(case_dirs["wrong_arithmetic"], "forged_pass")
    report = d_forged / "report.md"
    report.write_text(report.read_text("utf-8").replace("**failed**", "**passed**"), encoding="utf-8")
    summary = json.loads((d_forged / "run.json").read_text("utf-8"))
    summary["status"] = "passed"
    (d_forged / "run.json").write_text(json.dumps(summary), encoding="utf-8")
    rehash(d_forged)
    d_edit = copy_run(case_dirs["normal"], "edited_total")
    report = d_edit / "report.md"
    report.write_text(report.read_text("utf-8").replace("Total allowed: 187.00", "Total allowed: 197.00"),
                      encoding="utf-8")
    d_noread = copy_run(case_dirs["normal"], "log_without_source_read")
    edit_events(d_noread, lambda ev: [e for e in ev if not (e["type"] == "tool_result"
                                                            and e["name"] == "read_document")])
    rehash(d_noread)
    d_narr = copy_run(case_dirs["wrong_arithmetic"], "narrative_claim")
    (d_narr / "COMPLETION_CLAIM.md").write_text("All acceptance criteria met. Task complete.\n",
                                                encoding="utf-8")
    d_consistent = copy_run(case_dirs["normal"], "partial_forgery")

    def overpay(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for e in events:
            if e["type"] == "verdict":
                e["answer"]["items"][3]["allowed"] = "105.00"
                e["answer"]["total_allowed"] = "202.00"
        return events
    edit_events(d_consistent, overpay)
    report = d_consistent / "report.md"
    report.write_text(report.read_text("utf-8").replace("| 105.00 | 90.00 |", "| 105.00 | 105.00 |")
                      .replace("Total allowed: 187.00", "Total allowed: 202.00"), encoding="utf-8")
    rehash(d_consistent)
    ledger = RUNS / "ledger.jsonl"
    forged_answer = [json.loads(l) for l in (d_consistent / "events.jsonl").read_text("utf-8")
                     .splitlines() if json.loads(l)["type"] == "verdict"][-1]["answer"]
    lines = [json.loads(l) for l in ledger.read_text("utf-8").splitlines()]
    for entry in lines:
        if entry["key"] == "RCL-2026-014":
            entry["answer_sha256"] = decision_fingerprint(forged_answer)
    # Thorough forgery: also rewrite the model's submitted answer, the calculator call that summed
    # the items, the recorded check details and the report's Checks table, then rehash.
    d_thorough = copy_run(case_dirs["normal"], "thorough_forgery")

    def overpay_everywhere(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for e in events:
            answers = [e.get("answer")] if e["type"] == "verdict" else []
            if e["type"] == "model_turn" and e.get("name") == "submit_answer":
                answers.append(e["input"])
            for a in answers:
                a["items"][3]["allowed"] = "105.00"
                a["total_allowed"] = "202.00"
            if e["type"] == "model_turn" and e.get("name") == "calculate" and "90.00" in e["input"]["expression"]:
                e["input"]["expression"] = e["input"]["expression"].replace("90.00", "105.00")
            if e["type"] == "tool_result" and e["name"] == "calculate" and "90.00" in e["input"]["expression"]:
                e["input"]["expression"] = e["input"]["expression"].replace("90.00", "105.00")
                e["result"]["result"] = "202.00"
            if e["type"] == "verdict":
                for c in e["checks"]:
                    c["detail"] = c["detail"].replace("187.00", "202.00")
        return events
    edit_events(d_thorough, overpay_everywhere)
    report = d_thorough / "report.md"
    report.write_text(report.read_text("utf-8").replace("| 105.00 | 90.00 |", "| 105.00 | 105.00 |")
                      .replace("187.00", "202.00"), encoding="utf-8")
    events = [json.loads(l) for l in (d_thorough / "events.jsonl").read_text("utf-8").splitlines()]
    art = [e for e in events if e["type"] == "artifact"][-1]
    art["sha256"] = hashlib.sha256(report.read_bytes()).hexdigest()
    (d_thorough / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    rehash(d_thorough)
    forged_ledger = OUT / "forged_ledger.jsonl"
    forged_ledger.write_text("".join(json.dumps(e) + "\n" for e in lines), encoding="utf-8")

    submissions = [
        ("genuine_normal", case_dirs["normal"], None, True, "genuine"),
        ("genuine_injection_resisted", case_dirs["injection_resisted"], None, True, "genuine"),
        ("genuine_resumed_after_crash", crash_dir, None, True, "genuine"),
        ("genuine_failed_run", case_dirs["wrong_arithmetic"], None, False, "genuine"),
        ("interrupted_never_resumed", interrupted_dir, None, False, "genuine"),
        ("stale_policy", case_dirs["normal"], stale_data, False, "seeded"),
        ("missing_report", d_missing, None, False, "seeded"),
        ("forged_pass_on_failed_run", d_forged, None, False, "seeded"),
        ("edited_total", d_edit, None, False, "seeded"),
        ("log_without_source_read", d_noread, None, False, "seeded"),
        ("narrative_claim", d_narr, None, False, "seeded"),
        ("partial_forgery", d_consistent, None, False, "seeded"),
        ("thorough_forgery", d_thorough, None, False, "seeded"),
    ]
    rows = []
    for name, run_dir, data, should_accept, origin in submissions:
        args = [PY, "checker.py", str(run_dir),
                "--ledger", str(forged_ledger if name.endswith("_forgery") else ledger)]
        if data:
            args += ["--data-dir", str(data)]
        out = sh(args)
        outcome = json.loads(out["stdout"])
        accepted = outcome["accepted"]
        rows.append({"submission": name, "origin": origin, "label_should_accept": should_accept,
                     "checker_accepted": accepted, "exit_status": out["exit_status"],
                     "decision": outcome["decision"],
                     "error": None if accepted == should_accept else
                     ("false_acceptance" if accepted else "false_rejection")})
    record["checker_evaluation"] = {
        "submissions": rows,
        "false_acceptances": [r["submission"] for r in rows if r["error"] == "false_acceptance"],
        "false_rejections": [r["submission"] for r in rows if r["error"] == "false_rejection"],
        "n": len(rows),
        "note": "Labels were written by the author before running. Seeded submissions are "
                "artificial edits, not observed failures. n=13 is a demonstration, not a rate."}

    (OUT / "EVIDENCE.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (OUT / "EVIDENCE.md").write_text(render_md(record), encoding="utf-8")
    print(render_md(record))
    for path in OUT.rglob("*"):                         # make paths in records refer to FINAL
        if path.suffix in (".json", ".md") and path.is_file():
            path.write_text(path.read_text("utf-8").replace("ref01.new", "ref01"), encoding="utf-8")
    if FINAL.exists():
        shutil.rmtree(FINAL)
    OUT.rename(FINAL)
    ok = (tests["exit_status"] == 0 and all(c["as_expected"] for c in cases)
          and crash["exit_status"] == 3 and resume["exit_status"] == 0)
    return 0 if ok else 1


def render_md(r: dict[str, Any]) -> str:
    out = ["# REF01 evidence record (generated)", "",
           f"Generated {r['generated_utc']} by `{r['generator']}`. Do not edit by hand.", "",
           f"- Environment: Python {r['environment']['python']} on {r['environment']['os']}",
           f"- Git HEAD: `{r['git_head']}` (examples dirty: {r['git_dirty']})",
           f"- Code hash: `{r['code_sha256']}`",
           f"- Unit tests: exit {r['unit_tests']['exit_status']}: "
           + " ".join(s for s in r["unit_tests"]["summary"] if s), "",
           "## Constructed cases (fixture model; not live model behaviour)", "",
           "| Case | Expected | Observed | Exit | Failed checks | Wall s | Peak RSS MB |",
           "|---|---|---|---|---|---|---|"]
    for c in r["cases"]:
        res = c["resources"] or {}
        rss = res.get("process_peak_rss_bytes")
        out.append(f"| {c['case_id']} | {c['expected_status']} | {c['observed_status']} | "
                   f"{c['exit_status']} | {', '.join(c['failed_checks']) or '-'} | "
                   f"{res.get('wall_s', 'n/a')} | {round(rss / 2**20, 1) if rss else 'unavailable'} |")
    rec = r["recovery"]
    out += ["", "## Recovery", "",
            f"- Simulated crash after 2 tool calls: exit {rec['crash']['exit_status']}; "
            f"resume: exit {rec['resume']['exit_status']}.",
            f"- Tool executions across crash and resume: {len(rec['tool_executions'])} "
            f"({', '.join(n for n, _ in rec['tool_executions'])}).",
            f"- Crash after publish, then resume: publish actions "
            f"{[e['action'] for e in rec['publish_crash']['publish_events']]}; "
            f"ledger lines {rec['publish_crash']['ledger_lines']}.", "",
            "## Checker evaluation (labelled submissions)", "",
            "| Submission | Origin | Should accept | Accepted | Error | Decision |",
            "|---|---|---|---|---|---|"]
    for s in r["checker_evaluation"]["submissions"]:
        out.append(f"| {s['submission']} | {s['origin']} | {s['label_should_accept']} | "
                   f"{s['checker_accepted']} | {s['error'] or '-'} | {s['decision']} |")
    ce = r["checker_evaluation"]
    out += ["", f"False acceptances: {ce['false_acceptances'] or 'none'}. "
                f"False rejections: {ce['false_rejections'] or 'none'}. {ce['note']}", ""]
    return "\n".join(out)


if __name__ == "__main__":
    sys.exit(main())
