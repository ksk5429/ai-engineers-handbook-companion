"""The runner: owns the run directory, binds the run to its inputs and code, writes
the report, publishes the decision once, and supports resuming after a crash.

Files in runs/<run_id>/:
  events.jsonl   append-only event log (authoritative history)
  report.md      the deliverable, rendered by code
  run.json       summary written last, bound to the event log by its hash
Shared:
  runs/ledger.jsonl   decisions recorded at most once per claim (idempotent publish)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import workflow
from .report import render
from .runlog import RunRecorder, environment, load_events, sha256_file, sha256_tree

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTRACT_PATH = ROOT / "task_contract.json"


def code_files() -> list[Path]:
    return sorted((ROOT / "docassist").glob("*.py")) + sorted((ROOT / "schemas").glob("*.json")) \
        + [CONTRACT_PATH]


def input_fingerprint(claim_name: str, policy_name: str) -> dict[str, Any]:
    def entry(name: str) -> dict[str, Any]:
        path = DATA / name
        return {"name": name, "sha256": sha256_file(path) if path.is_file() else None}
    return {"claim": entry(claim_name), "policy": entry(policy_name)}


def new_run_id(label: str) -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + label


class StaleRunError(RuntimeError):
    """A resume was refused because inputs or code changed since the run started."""


def start(model: Any, claim_name: str, policy_name: str, runs_dir: Path, *, label: str,
          case_meta: dict[str, Any] | None = None, crash_after_tools: int | None = None,
          crash_at_publish: bool = False, interface: str = "v1") -> dict[str, Any]:
    run_id = new_run_id(label)
    recorder = RunRecorder(runs_dir / run_id)
    contract_text = CONTRACT_PATH.read_bytes()
    recorder.emit("run_start", run_id=run_id, case=case_meta or {},
                  contract=json.loads(contract_text),
                  contract_sha256=hashlib.sha256(contract_text).hexdigest(),
                  inputs=input_fingerprint(claim_name, policy_name),
                  code_sha256=sha256_tree(code_files()), model=model.describe(),
                  environment=environment(),
                  **({"interface": interface} if interface != "v1" else {}))
    return _execute(model, recorder, claim_name, policy_name, runs_dir, run_id,
                    crash_after_tools, crash_at_publish, replay=None, interface=interface)


# --8<-- [start:resume]
def resume(model: Any, run_dir: Path) -> dict[str, Any]:
    events = load_events(run_dir)
    if not events or events[0]["type"] != "run_start":
        raise StaleRunError(f"{run_dir.name}: no run_start event; cannot resume")
    if any(e["type"] == "run_end" for e in events):
        raise StaleRunError(f"{run_dir.name}: run already ended; start a new run instead")
    start_event = events[0]
    names = start_event["inputs"]
    now = input_fingerprint(names["claim"]["name"], names["policy"]["name"])
    if now != start_event["inputs"] or sha256_tree(code_files()) != start_event["code_sha256"]:
        raise StaleRunError(f"{run_dir.name}: inputs or code changed since the run started")
    recorder = RunRecorder(run_dir)
    recorder.emit("resume", replayable_events=len(events))
    return _execute(model, recorder, names["claim"]["name"], names["policy"]["name"],
                    run_dir.parent, start_event["run_id"], None, False, replay=events,
                    interface=start_event.get("interface", "v1"))
# --8<-- [end:resume]


def _execute(model: Any, recorder: RunRecorder, claim_name: str, policy_name: str,
             runs_dir: Path, run_id: str, crash_after_tools: int | None,
             crash_at_publish: bool, replay: list[dict[str, Any]] | None,
             interface: str = "v1") -> dict[str, Any]:
    claim = json.loads((DATA / claim_name).read_text(encoding="utf-8"))
    max_turns = int(json.loads(CONTRACT_PATH.read_text("utf-8"))["budgets"]["max_turns"])
    verdict = workflow.run(model, claim, policy_name, DATA, max_turns=max_turns, recorder=recorder,
                           crash_after_tools=crash_after_tools, replay_events=replay,
                           interface=interface)
    recorder.emit("verdict", status=verdict["status"], reasons=verdict["reasons"],
                  schema_errors=verdict["schema_errors"], checks=verdict["checks"],
                  security_events=verdict["security_events"], answer=verdict["answer"],
                  source=verdict["source"], replayed_steps=verdict["replayed_steps"],
                  **({"interface": interface, "answer_v1_view": verdict.get("answer_v1_view")}
                     if interface != "v1" else {}))
    report_path = recorder.run_dir / "report.md"
    report_path.write_text(render(run_id, claim, verdict, verdict["source"]), encoding="utf-8")
    recorder.emit("artifact", path="report.md", sha256=sha256_file(report_path))
    publish = _publish(runs_dir / "ledger.jsonl", run_id, claim, verdict, recorder)
    if crash_at_publish:
        recorder.emit("interruption", reason="simulated crash after publish")
        raise workflow.SimulatedCrash("simulated crash after the ledger write")
    usage = _usage_totals(load_events(recorder.run_dir))
    recorder.emit("run_end", status=verdict["status"], resources=recorder.resources(),
                  usage=usage)
    summary = {"run_id": run_id, "status": verdict["status"], "reasons": verdict["reasons"],
               "publish": publish, "usage": usage,
               "events_sha256": sha256_file(recorder.run_dir / "events.jsonl"),
               "report_sha256": sha256_file(report_path)}
    (recorder.run_dir / "run.json").write_text(json.dumps(summary, indent=2) + "\n",
                                               encoding="utf-8")
    return {**verdict, "run_id": run_id, "run_dir": str(recorder.run_dir), "publish": publish,
            "usage": usage}


# --8<-- [start:publish]
def _publish(ledger: Path, run_id: str, claim: dict[str, Any], verdict: dict[str, Any],
             recorder: RunRecorder) -> dict[str, Any]:
    """Record a passed decision at most once per claim (idempotency key = claim id)."""
    if verdict["status"] != "passed":
        recorder.emit("publish", action="skipped", reason=f"status {verdict['status']}")
        return {"action": "skipped"}
    key = claim["claim_id"]
    answer_sha = decision_fingerprint(verdict["answer"])
    existing = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines()
                if l.strip()] if ledger.exists() else []
    match = [e for e in existing if e["key"] == key]
    if match and match[0]["answer_sha256"] == answer_sha:
        outcome = {"action": "duplicate_suppressed", "key": key}
    elif match:
        outcome = {"action": "conflict", "key": key, "existing_run": match[0]["run_id"]}
    else:
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"key": key, "run_id": run_id, "answer_sha256": answer_sha,
                                     "total_allowed": verdict["answer"]["total_allowed"]}) + "\n")
        outcome = {"action": "recorded", "key": key}
    recorder.emit("publish", **outcome)
    return outcome
# --8<-- [end:publish]


def decision_fingerprint(answer: dict[str, Any]) -> str:
    """Hash of the fields that decide a payment; rewording a reason is not a new decision."""
    core = {"claim_id": answer["claim_id"], "decision": answer["decision"],
            "total_allowed": answer["total_allowed"],
            "items": sorted([i["index"], i["allowed"]] for i in answer["items"])}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def _usage_totals(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum provider-reported numeric usage fields; never estimate missing ones."""
    totals: dict[str, int] = {}
    calls = reported = 0
    for event in events:
        if event["type"] != "model_turn":
            continue
        calls += 1
        usage = event.get("usage")
        if not usage:
            continue
        reported += 1
        for key, value in usage.items():
            if isinstance(value, int):
                totals[key] = totals.get(key, 0) + value
    return {"model_calls": calls, "calls_with_usage": reported,
            "totals": totals if reported else "unavailable"}
