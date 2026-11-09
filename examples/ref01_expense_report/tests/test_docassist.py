"""Tests for the chapter E1 example.  Run from the example folder:

    python -m unittest discover -s tests -v

The case tests check that the workflow reaches the expected verdict for each
constructed behaviour. The unit tests check the parts that guard against those
behaviours: the validator, the tool allowlist and path restriction, the
calculator, and each independent check.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from docassist import checks  # noqa: E402
from docassist.models import FixtureModel  # noqa: E402
from docassist.schema import validate  # noqa: E402
from docassist.tools import ToolBox  # noqa: E402
from docassist.workflow import load_answer_schema, run  # noqa: E402
import checker  # noqa: E402
from docassist import runner  # noqa: E402
from docassist.workflow import SimulatedCrash  # noqa: E402
from run import load_case, run_case as _run_case  # noqa: E402

DATA = HERE / "data"
CASES = sorted((HERE / "fixtures" / "cases").glob("*.json"))
_TMP = Path(tempfile.mkdtemp(prefix="ref01_tests_"))


def run_case(case: dict) -> dict:
    return _run_case(case, _TMP / "runs")


def tearDownModule() -> None:
    shutil.rmtree(_TMP, ignore_errors=True)


class TestCases(unittest.TestCase):
    def test_case_files_exist(self) -> None:
        self.assertGreaterEqual(len(CASES), 9, "run python fixtures/make_cases.py first")

    def test_each_case_reaches_expected_status_and_checks(self) -> None:
        for path in CASES:
            case = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(case=case["case_id"]):
                self.assertTrue(case["constructed"])
                report = run_case(case)
                self.assertEqual(report["status"], case["expected"]["status"], report["reasons"])
                failed = sorted(c["check_id"] for c in report["checks"] if not c["passed"])
                self.assertEqual(failed, sorted(case["expected"]["failed_checks"]))

    def test_passing_cases_also_match_their_labels(self) -> None:
        for path in CASES:
            case = json.loads(path.read_text(encoding="utf-8"))
            report = run_case(case)
            if report["status"] == "passed":
                with self.subTest(case=case["case_id"]):
                    self.assertTrue(report["evaluation"]["matches_label"],
                                    report["evaluation"]["differences"])

    def test_injection_followed_passes_checks_but_fails_label(self) -> None:
        """The invariant checks alone do not catch a wrong rule application."""
        case = json.loads((HERE / "fixtures/cases/injection_followed.json").read_text("utf-8"))
        report = run_case(case)
        self.assertTrue(all(c["passed"] for c in report["checks"]))
        self.assertEqual(report["security_events"], ["refused tool request: send_payment"])
        self.assertFalse(report["evaluation"]["matches_label"])


class TestValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = load_answer_schema()
        case = json.loads((HERE / "fixtures/cases/normal.json").read_text("utf-8"))
        self.good = case["turns"][-1]["input"]

    def test_good_answer_is_valid(self) -> None:
        self.assertEqual(validate(self.good, self.schema), [])

    def test_float_money_rejected(self) -> None:
        bad = dict(self.good, total_allowed=187.0)
        self.assertIn("$.total_allowed: expected string, got float", validate(bad, self.schema))

    def test_extra_field_rejected(self) -> None:
        bad = dict(self.good, confidence="high")
        self.assertIn("$: unexpected field 'confidence'", validate(bad, self.schema))

    def test_bool_is_not_integer(self) -> None:
        self.assertTrue(validate(True, {"type": "integer"}))

    def test_unknown_keyword_is_an_error_not_a_pass(self) -> None:
        self.assertTrue(validate("x", {"type": "string", "maxLength": 3}))


class TestTools(unittest.TestCase):
    def setUp(self) -> None:
        self.box = ToolBox(DATA)

    def test_read_document_numbers_lines(self) -> None:
        result = self.box.call("read_document", {"name": "policy.md"})
        self.assertTrue(result["ok"])
        self.assertTrue(result["lines"][4][1].startswith("1. Mileage"))
        self.assertEqual(result["lines"][4][0], 5)

    def test_path_traversal_refused(self) -> None:
        for name in ("../run.py", "..", "data/../run.py"):
            with self.subTest(name=name):
                self.assertFalse(self.box.call("read_document", {"name": name})["ok"])

    def test_missing_file(self) -> None:
        self.assertEqual(self.box.call("read_document", {"name": "nope.md"})["error"], "not_found")

    def test_unlisted_tool_refused(self) -> None:
        self.assertEqual(self.box.call("send_payment", {"amount": "1.00"})["error"],
                         "unauthorized_tool")

    def test_submit_answer_is_not_executable_as_a_tool(self) -> None:
        self.assertEqual(self.box.call("submit_answer", {})["error"], "unauthorized_tool")

    def test_calculator_is_exact(self) -> None:
        self.assertEqual(self.box.call("calculate", {"expression": "0.1 + 0.2"})["result"], "0.3")

    def test_calculator_rejects_code(self) -> None:
        for expression in ("__import__('os')", "2 ** 100000", "1/0"):
            with self.subTest(expression=expression):
                self.assertFalse(self.box.call("calculate", {"expression": expression})["ok"])

    def test_every_call_is_recorded(self) -> None:
        self.box.call("calculate", {"expression": "1+1"})
        self.box.call("send_payment", {})
        self.assertEqual([c["tool"] for c in self.box.calls], ["calculate", "send_payment"])


class TestChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.claim = json.loads((DATA / "claim_normal.json").read_text("utf-8"))
        case = json.loads((HERE / "fixtures/cases/normal.json").read_text("utf-8"))
        self.answer = case["turns"][-1]["input"]
        box = ToolBox(DATA)
        self.lines = {n: t for n, t in box.call("read_document", {"name": "policy.md"})["lines"]}

    def test_all_pass_on_correct_answer(self) -> None:
        self.assertTrue(all(c.passed for c in checks.run_all(self.answer, self.claim, self.lines)))

    def test_quote_on_wrong_line_fails(self) -> None:
        moved = json.loads(json.dumps(self.answer))
        moved["items"][0]["rule_line"] = 6
        self.assertFalse(checks.check_quotes(moved, self.lines).passed)

    def test_missing_item_fails_coverage(self) -> None:
        short = dict(self.answer, items=self.answer["items"][:3])
        self.assertFalse(checks.check_coverage(short, self.claim).passed)

    def test_allowed_above_claimed_fails(self) -> None:
        greedy = json.loads(json.dumps(self.answer))
        greedy["items"][3]["allowed"] = "110.00"
        self.assertFalse(checks.check_not_above_claimed(greedy, self.claim).passed)


class TestRecovery(unittest.TestCase):
    """Crash, resume, idempotent publish and stale-input refusal."""

    def setUp(self) -> None:
        self.runs = Path(tempfile.mkdtemp(dir=_TMP))

    def _crash(self, **crash: object) -> Path:
        with self.assertRaises(SimulatedCrash):
            _run_case(load_case("normal"), self.runs, **crash)
        return next(p for p in self.runs.iterdir() if p.is_dir())

    def test_resume_after_crash_does_not_rerun_tools(self) -> None:
        run_dir = self._crash(crash_after_tools=2)
        self.assertFalse((run_dir / "run.json").exists())
        result = runner.resume(FixtureModel(load_case("normal")["turns"]), run_dir)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["replayed_steps"], 2)
        tool_events = [e for e in runner.load_events(run_dir) if e["type"] == "tool_result"]
        calls = [(e["name"], e["input"]) for e in tool_events]
        expected = [(t["tool"], t["input"]) for t in load_case("normal")["turns"][:-1]]
        self.assertEqual(calls, expected, "each tool ran exactly once across crash and resume")

    def test_crash_after_publish_does_not_duplicate_ledger_entry(self) -> None:
        run_dir = self._crash(crash_at_publish=True)
        result = runner.resume(FixtureModel(load_case("normal")["turns"]), run_dir)
        self.assertEqual(result["publish"]["action"], "duplicate_suppressed")
        ledger = (self.runs / "ledger.jsonl").read_text("utf-8").splitlines()
        self.assertEqual(len(ledger), 1)

    def test_finished_run_cannot_be_resumed(self) -> None:
        result = _run_case(load_case("normal"), self.runs)
        with self.assertRaises(runner.StaleRunError):
            runner.resume(FixtureModel([]), Path(result["run_dir"]))

    def test_resume_refused_when_inputs_changed(self) -> None:
        run_dir = self._crash(crash_after_tools=1)
        events = (run_dir / "events.jsonl").read_text("utf-8").splitlines()
        start = json.loads(events[0])
        start["inputs"]["policy"]["sha256"] = "0" * 64      # as if the policy changed since
        (run_dir / "events.jsonl").write_text("\n".join([json.dumps(start)] + events[1:]) + "\n",
                                              encoding="utf-8")
        with self.assertRaises(runner.StaleRunError):
            runner.resume(FixtureModel(load_case("normal")["turns"]), run_dir)


class TestChecker(unittest.TestCase):
    def setUp(self) -> None:
        self.runs = Path(tempfile.mkdtemp(dir=_TMP))
        self.passed = Path(_run_case(load_case("normal"), self.runs)["run_dir"])
        self.ledger = self.runs / "ledger.jsonl"

    def _check(self, run_dir: Path, data: Path = DATA) -> dict:
        return checker.check_run(run_dir, data, self.ledger)

    def test_accepts_genuine_passed_run(self) -> None:
        self.assertTrue(self._check(self.passed)["accepted"])

    def test_failed_run_has_valid_record_but_is_not_accepted(self) -> None:
        failed = Path(_run_case(load_case("wrong_arithmetic"), self.runs)["run_dir"])
        outcome = self._check(failed)
        self.assertTrue(outcome["record_valid"])
        self.assertFalse(outcome["accepted"])

    def test_rejects_missing_report(self) -> None:
        (self.passed / "report.md").unlink()
        self.assertIn("K1_artifacts_present", self._check(self.passed)["decision"])

    def test_rejects_edited_report(self) -> None:
        report = self.passed / "report.md"
        report.write_text(report.read_text("utf-8").replace("187.00", "197.00"), encoding="utf-8")
        self.assertIn("K2_record_integrity", self._check(self.passed)["decision"])

    def test_rejects_stale_inputs(self) -> None:
        data = Path(tempfile.mkdtemp(dir=_TMP))
        for f in DATA.iterdir():
            shutil.copy(f, data / f.name)
        policy = data / "policy.md"
        policy.write_text(policy.read_text("utf-8").replace("25.00", "30.00"), encoding="utf-8")
        self.assertIn("K3_bound_to_current_inputs", self._check(self.passed, data)["decision"])


class TestBudget(unittest.TestCase):
    def test_loop_stops_at_budget(self) -> None:
        claim = json.loads((DATA / "claim_normal.json").read_text("utf-8"))
        turns = [{"tool": "calculate", "input": {"expression": "1+1"}}] * 50
        model = FixtureModel(turns)
        report = run(model, claim, "policy.md", DATA, max_turns=3)
        self.assertEqual(report["turns_used"], 3)
        self.assertIn(report["status"], ("failed", "blocked"))
        # Regression (defect D-01, found in live trials): never request a turn beyond the budget.
        self.assertEqual(model._next, 3, "the model was asked for more turns than the budget")


class TestReviewFixes(unittest.TestCase):
    """Regression tests for technical review cycle 1 (T-01, T-04, T-05, T-07, T-08, T-10)."""

    def test_calculator_keeps_scale_and_digits(self) -> None:
        box = ToolBox(DATA)
        self.assertEqual(box.call("calculate", {"expression": "72.00 + 25.00"})["result"], "97.00")
        self.assertEqual(box.call("calculate", {"expression": "12345678901234567.89 + 0"})["result"],
                         "12345678901234567.89")

    def test_calculator_survives_deep_input(self) -> None:
        self.assertFalse(ToolBox(DATA).call("calculate", {"expression": "-" * 5000 + "1"})["ok"])

    def test_quote_fragment_is_not_a_quote(self) -> None:
        self.assertFalse(checks.quote_matches("reimbursed", "1. Mileage for a private car is reimbursed"))
        self.assertTrue(checks.quote_matches("Mileage for a  private car", "1. Mileage for a private car"))

    def test_non_object_arguments_do_not_crash(self) -> None:
        claim = json.loads((DATA / "claim_normal.json").read_text("utf-8"))
        model = FixtureModel([{"tool": "read_document", "input": ["policy.md"]}])
        report = run(model, claim, "policy.md", DATA)
        self.assertIn(report["status"], ("failed", "blocked"))

    def test_second_tool_call_in_a_turn_is_a_security_event(self) -> None:
        from docassist.models import Turn
        from docassist.workflow import _Driver  # noqa: F401  (imported to show the path exists)
        claim = json.loads((DATA / "claim_normal.json").read_text("utf-8"))

        class TwoCalls(FixtureModel):
            def start(self, system, task, tools):  # type: ignore[override]
                return Turn(kind="tool", name="read_document", input={"name": "policy.md"},
                            id="t1", extra_calls=("send_payment",))
        report = run(TwoCalls([]), claim, "policy.md", DATA, max_turns=2)
        self.assertIn("ignored additional tool request in one turn: send_payment",
                      report["security_events"])

    def test_checker_rejects_verdict_that_differs_from_submission(self) -> None:
        runs = Path(tempfile.mkdtemp(dir=_TMP))
        run_dir = Path(_run_case(load_case("normal"), runs)["run_dir"])
        path = run_dir / "events.jsonl"
        events = [json.loads(l) for l in path.read_text("utf-8").splitlines()]
        for e in events:
            if e["type"] == "verdict":
                e["answer"]["total_allowed"] = "202.00"
        path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
        summary = json.loads((run_dir / "run.json").read_text("utf-8"))
        summary["events_sha256"] = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
        (run_dir / "run.json").write_text(json.dumps(summary), encoding="utf-8")
        outcome = checker.check_run(run_dir, DATA, runs / "ledger.jsonl")
        self.assertIn("K4_status_supported_by_log", outcome["decision"])

    def test_hosted_token_cap_counts_usage_and_stops(self) -> None:
        """Regression: the spend guard once checked a counter that was never incremented."""
        import os
        from unittest import mock
        from docassist import models
        fake = {"content": [{"type": "text", "text": "hi"}],
                "usage": {"input_tokens": 600, "output_tokens": 500, "cache_read_input_tokens": 0}}
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-not-a-key",
                                          "HANDBOOK_MAX_TOTAL_TOKENS": "1000"}), \
                mock.patch.object(models, "_post_json", return_value=fake) as post:
            model = models.AnthropicModel()
            model.start("s", "t", [])
            self.assertEqual(model.used_tokens, 1100)
            with self.assertRaises(models.ModelError):
                model.reply("x", {"ok": True})
            self.assertEqual(post.call_count, 1, "no request may be sent once the cap is reached")

    def test_reworded_reason_is_not_a_new_decision(self) -> None:
        answer = load_case("normal")["turns"][-1]["input"]
        reworded = json.loads(json.dumps(answer))
        reworded["items"][0]["reason"] = "different words"
        self.assertEqual(runner.decision_fingerprint(answer), runner.decision_fingerprint(reworded))


class TestTriageFixes(unittest.TestCase):
    """Regression tests for triage cycle 2 (T-13, T-23, T-24, T-25, T-26)."""

    def test_pattern_must_match_whole_string(self) -> None:
        self.assertTrue(validate("90.00\n", {"type": "string", "pattern": "^[0-9]+\\.[0-9]{2}$"}))

    def test_case_variant_name_is_not_found(self) -> None:
        self.assertEqual(ToolBox(DATA).call("read_document", {"name": "POLICY.MD"})["error"], "not_found")

    def test_checker_handles_unreadable_log(self) -> None:
        runs = Path(tempfile.mkdtemp(dir=_TMP))
        run_dir = Path(_run_case(load_case("normal"), runs)["run_dir"])
        (run_dir / "events.jsonl").write_text("{not json\n", encoding="utf-8")
        self.assertIn("K2_record_integrity", checker.check_run(run_dir, DATA, runs / "ledger.jsonl")["decision"])

    def test_checker_rejects_wrong_claim_id(self) -> None:
        answer = json.loads(json.dumps(load_case("normal")["turns"][-1]["input"]))
        answer["claim_id"] = "RCL-1999-001"
        start = {"inputs": {"policy": {"name": "policy.md"}, "claim": {"name": "claim_normal.json"}}}
        result = checker._check_answer(answer, DATA, start, True)
        self.assertFalse(result["passed"])
        self.assertIn("claim id", result["detail"])

    def test_usage_errors_exit_64(self) -> None:
        import subprocess
        for script in ("run.py", "checker.py"):
            proc = subprocess.run([sys.executable, script, "--no-such-flag"], cwd=HERE,
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 64, script)


if __name__ == "__main__":
    unittest.main()
