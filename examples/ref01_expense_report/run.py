"""Command-line entry point for the reference workflow (REF01).

  python run.py --case normal                      replay one constructed case (no network)
  python run.py --all                              replay every constructed case
  python run.py --case normal --crash-after 2      simulate a crash after 2 tool calls
  python run.py --resume runs/<run_id>             resume a crashed run without re-running tools
  python run.py --ollama qwen2.5:7b --claim claim_normal.json   live local model via Ollama
  python run.py --anthropic --claim claim_normal.json            live hosted model (needs a key)

Every run writes runs/<run_id>/events.jsonl, report.md and run.json.
Check a run with:  python checker.py runs/<run_id>
Exit status: 0 passed, 1 failed, 2 blocked, 3 interrupted (simulated), 5 publish conflict
(passed, but the ledger already holds a different decision for this claim), 64 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from docassist import runner
from docassist.models import AnthropicModel, FixtureModel, ModelError, OllamaModel
from docassist.workflow import SimulatedCrash, evaluate

HERE = Path(__file__).resolve().parent
CASES = HERE / "fixtures" / "cases"
EXIT = {"passed": 0, "failed": 1, "blocked": 2}


def load_case(case_id: str) -> dict[str, Any]:
    path = CASES / f"{case_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"no case file {path.name}; run: python fixtures/make_cases.py")
    return json.loads(path.read_text(encoding="utf-8"))


def run_case(case: dict[str, Any], runs_dir: Path, **crash: Any) -> dict[str, Any]:
    meta = {"case_id": case["case_id"], "constructed": case["constructed"]}
    result = runner.start(FixtureModel(case["turns"]), case["claim"], case["policy"], runs_dir,
                          label=case["case_id"], case_meta=meta, **crash)
    if "label" in case:
        result["evaluation"] = evaluate(result, case["label"])
    return result


def _summary_line(case: dict[str, Any], result: dict[str, Any]) -> str:
    ok = result["status"] == case["expected"]["status"]
    return (f"{case['case_id']:<20} status={result['status']:<8} "
            f"expected={case['expected']['status']:<8} {'AS EXPECTED' if ok else 'UNEXPECTED'}"
            f"  {'; '.join(result['reasons'])}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="REF01 reference workflow")

    def _usage_error(message: str) -> None:            # documented exit status 64, not argparse's 2
        parser.print_usage(sys.stderr)
        print(f"error: {message}", file=sys.stderr)
        raise SystemExit(64)
    parser.error = _usage_error  # type: ignore[method-assign]
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--case", help="constructed case id in fixtures/cases")
    group.add_argument("--all", action="store_true", help="run every constructed case")
    group.add_argument("--resume", type=Path, help="run directory to resume")
    group.add_argument("--ollama", metavar="MODEL", help="live local model served by Ollama")
    group.add_argument("--anthropic", action="store_true", help="live Anthropic model")
    parser.add_argument("--claim", default="claim_normal.json")
    parser.add_argument("--policy", default="policy.md")
    parser.add_argument("--runs-dir", type=Path, default=HERE / "runs")
    parser.add_argument("--crash-after", type=int, default=None, help="simulate a crash")
    parser.add_argument("--crash-at-publish", action="store_true")
    parser.add_argument("--seed", type=int, default=None, help="Ollama sampling seed")
    parser.add_argument("--temperature", type=float, default=0.0, help="Ollama temperature")
    parser.add_argument("--interface", choices=["v1", "v2"], default="v1",
                        help="model-facing interface for live runs (P10); constructed cases are v1")
    args = parser.parse_args(argv)
    if args.interface != "v1" and (args.case or args.all or args.resume):
        print("ERROR: --interface applies to live runs; a resume reads it from the run record",
              file=sys.stderr)
        return 64
    crash = {"crash_after_tools": args.crash_after, "crash_at_publish": args.crash_at_publish}

    try:
        if args.all:
            worst = 0
            for path in sorted(CASES.glob("*.json")):
                case = json.loads(path.read_text(encoding="utf-8"))
                result = run_case(case, args.runs_dir)
                print(_summary_line(case, result))
                worst = max(worst, 0 if result["status"] == case["expected"]["status"] else 1)
            return worst
        if args.case:
            result = run_case(load_case(args.case), args.runs_dir, **crash)
        elif args.resume:
            first = json.loads((args.resume / "events.jsonl").read_text("utf-8").splitlines()[0])
            case_meta, described = first["case"], first["model"]
            if case_meta.get("constructed"):
                model: Any = FixtureModel(load_case(case_meta["case_id"])["turns"])
            elif described["route"] == "ollama":
                opts = described["options"]
                model = OllamaModel(model=described["model"], host=described.get("host"),
                                    num_ctx=opts.get("num_ctx", 8192), seed=opts.get("seed"),
                                    temperature=opts.get("temperature", 0.0),
                                    timeout_s=float(json.loads((HERE / "task_contract.json")
                                                    .read_text("utf-8"))["budgets"]["model_call_timeout_s"]))
            else:
                model = AnthropicModel(model=described["model"])
            result = runner.resume(model, args.resume)
        else:
            result = runner.start(_live_model(args), args.claim, args.policy, args.runs_dir,
                                  label="live" if args.interface == "v1" else "live-v2",
                                  case_meta={"constructed": False}, interface=args.interface, **crash)
    except SimulatedCrash as exc:
        print(f"INTERRUPTED: {exc}. Resume with: python run.py --resume <run_dir>",
              file=sys.stderr)
        return 3
    except (FileNotFoundError, runner.StaleRunError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 64
    except ModelError as exc:
        print(json.dumps({"status": "blocked", "reasons": [str(exc)]}, indent=2))
        return EXIT["blocked"]
    print(json.dumps(result, indent=2))
    if result.get("publish", {}).get("action") == "conflict":
        print("WARNING: publish conflict; a person must decide which decision stands", file=sys.stderr)
        return 5
    return EXIT[result["status"]]


def _live_model(args: argparse.Namespace) -> Any:
    if args.anthropic:
        return AnthropicModel()
    timeout = float(json.loads((HERE / "task_contract.json").read_text("utf-8"))["budgets"]["model_call_timeout_s"])
    return OllamaModel(model=args.ollama or "qwen2.5:7b", seed=args.seed,
                       temperature=args.temperature, timeout_s=timeout)


if __name__ == "__main__":
    sys.exit(main())
