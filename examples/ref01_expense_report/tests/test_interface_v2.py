"""Tests T1-T9 of the P10 pre-registration (experiments/P10_PREREGISTRATION.md, section 6),
plus unit tests of the P10 decision rule (section 10) as implemented in the driver.

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "experiments"))

import checker  # noqa: E402
from docassist import checks, interface_v2, runner, workflow  # noqa: E402
from docassist.models import FixtureModel  # noqa: E402
from docassist.tools import ToolBox  # noqa: E402
from docassist.workflow import SimulatedCrash, evaluate  # noqa: E402
import p10_trials  # noqa: E402

DATA = HERE / "data"
NORMAL = json.loads((HERE / "fixtures" / "cases" / "normal.json").read_text("utf-8"))
LABEL_NORMAL = NORMAL["label"]
CLAIM_NORMAL = json.loads((DATA / "claim_normal.json").read_text("utf-8"))
LINE_TO_RULE = {5: 1, 6: 2, 7: 3, 8: 4, 9: 5, 10: 6}
_TMP = Path(tempfile.mkdtemp(prefix="ref01_v2_tests_"))


def tearDownModule() -> None:
    shutil.rmtree(_TMP, ignore_errors=True)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def v2_turns() -> list[dict]:
    """The constructed normal case, with the answer citing rule numbers 1, 2, 2, 3."""
    turns = copy.deepcopy(NORMAL["turns"])
    for item in turns[-1]["input"]["items"]:
        item["rule_number"] = LINE_TO_RULE[item.pop("rule_line")]
    return turns


def policy_lines() -> dict[int, str]:
    result = ToolBox(DATA)._read_document({"name": "policy.md"})
    return {n: t for n, t in result["lines"]}


class T1V1Goldens(unittest.TestCase):
    def test_v1_model_facing_bytes_unchanged(self) -> None:
        g = p10_trials.GOLDENS
        self.assertEqual(sha(json.dumps(workflow.tool_definitions(), sort_keys=True)), g["tool_definitions"])
        self.assertEqual(sha(json.dumps(workflow.tool_definitions("v1"), sort_keys=True)), g["tool_definitions"])
        self.assertEqual(sha(workflow.SYSTEM_PROMPT), g["system_prompt"])
        read = ToolBox(DATA)._read_document({"name": "policy.md"})
        self.assertEqual(sha(json.dumps(read, sort_keys=True)), g["read_document_policy"])
        self.assertEqual(sha(inspect.getsource(workflow.evaluate)), g["evaluate_source"])
        self.assertEqual(g["tool_definitions"],
                         "4e5ea06e93776faee744f3ed2e3faa9bb3cd8e695487db49a119e5b9b1e84517")


class T2ReadDocumentV2(unittest.TestCase):
    def test_rules_keyed_by_number_without_line_numbers(self) -> None:
        v2 = ToolBox(DATA, "v2")._read_document({"name": "policy.md"})
        v1 = ToolBox(DATA)._read_document({"name": "policy.md"})
        self.assertNotIn("lines", v2)
        file_lines = (DATA / "policy.md").read_text("utf-8").splitlines()
        self.assertEqual([r["rule_number"] for r in v2["rules"]], [1, 2, 3, 4, 5, 6])
        self.assertEqual([r["text"] for r in v2["rules"]],
                         [line.split(". ", 1)[1] for line in file_lines[4:10]])
        self.assertEqual(v2["text"], file_lines[0:3])
        self.assertEqual(v2["sha256"], v1["sha256"])


class T3RuleIndex(unittest.TestCase):
    def test_rule_index_and_quotes(self) -> None:
        lines = policy_lines()
        index = interface_v2.rule_index(lines)
        self.assertEqual(index, {1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10})
        for rule in ToolBox(DATA, "v2")._read_document({"name": "policy.md"})["rules"]:
            self.assertTrue(checks.quote_matches(rule["text"], lines[index[rule["rule_number"]]]))


class T4AdapterCannotLaunder(unittest.TestCase):
    def setUp(self) -> None:
        self.lines = policy_lines()
        self.index = interface_v2.rule_index(self.lines)
        self.answer = v2_turns()[-1]["input"]

    def c3(self, answer: dict) -> bool:
        return checks.check_quotes(interface_v2.to_v1_view(answer, self.index), self.lines).passed

    def with_item0(self, number: int, quote_item: int = 0) -> dict:
        answer = copy.deepcopy(self.answer)
        answer["items"][0]["rule_number"] = number
        answer["items"][0]["rule_quote"] = self.answer["items"][quote_item]["rule_quote"]
        return answer

    def test_correct_number_and_quote_pass(self) -> None:
        self.assertTrue(self.c3(self.answer))

    def test_wrong_number_with_right_quote_fails(self) -> None:
        self.assertFalse(self.c3(self.with_item0(3)))          # rule 1's quote under number 3

    def test_line_number_as_rule_number_fails(self) -> None:
        self.assertFalse(self.c3(self.with_item0(7, quote_item=3)))   # 7 is the hotel LINE

    def test_unknown_rule_numbers_fail(self) -> None:
        for number in (0, 9):
            with self.subTest(number=number):
                self.assertFalse(self.c3(self.with_item0(number)))

    def test_input_not_modified(self) -> None:
        before = copy.deepcopy(self.answer)
        view = interface_v2.to_v1_view(self.answer, self.index)
        self.assertEqual(self.answer, before)
        self.assertEqual([i["rule_line"] for i in view["items"]], [5, 6, 6, 7])


class T5PromptV2(unittest.TestCase):
    def test_one_sentence_changes(self) -> None:
        old = "policy line number you relied on, and an exact quote of that line. Submit the\nresult once"
        # v2.1 (experiments/P10_REVISION_v2_1.md): the same sentence also asks for a one-line reason.
        new = "number of the policy rule you relied on, an exact quote of that rule's\ntext, and a one-line reason. Submit the result once"
        self.assertNotEqual(workflow.SYSTEM_PROMPT_V2, workflow.SYSTEM_PROMPT)
        self.assertIn("number of the policy rule", workflow.SYSTEM_PROMPT_V2)
        self.assertEqual(workflow.SYSTEM_PROMPT_V2.replace(new, old), workflow.SYSTEM_PROMPT)


class T6WorkflowV2(unittest.TestCase):
    def test_correct_v2_answer_passes_and_matches_label(self) -> None:
        report = workflow.run(FixtureModel(v2_turns()), CLAIM_NORMAL, "policy.md", DATA, interface="v2")
        self.assertEqual(report["status"], "passed", report["reasons"])
        self.assertTrue(evaluate(report, LABEL_NORMAL)["matches_label"])
        self.assertIn("rule_number", report["answer"]["items"][0])          # raw submission kept
        self.assertEqual([i["rule_line"] for i in report["answer_v1_view"]["items"]], [5, 6, 6, 7])
        self.assertEqual(report["interface"], "v2")

    def test_v1_shaped_answer_is_a_schema_violation_under_v2(self) -> None:
        report = workflow.run(FixtureModel(NORMAL["turns"]), CLAIM_NORMAL, "policy.md", DATA, interface="v2")
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("missing required field 'rule_number'" in e for e in report["schema_errors"]))


class T7ResumeV2(unittest.TestCase):
    def test_resume_replays_with_v2_and_runs_no_tool_twice(self) -> None:
        runs = Path(tempfile.mkdtemp(dir=_TMP))
        with self.assertRaises(SimulatedCrash):
            runner.start(FixtureModel(v2_turns()), "claim_normal.json", "policy.md", runs,
                         label="t7", case_meta={"constructed": False}, crash_after_tools=1,
                         interface="v2")
        run_dir = next(p for p in runs.iterdir() if p.is_dir())
        result = runner.resume(FixtureModel(v2_turns()), run_dir)
        self.assertEqual(result["status"], "passed", result["reasons"])
        self.assertEqual(result["replayed_steps"], 1)
        events = runner.load_events(run_dir)
        self.assertEqual(events[0]["interface"], "v2")
        calls = [(e["name"], e["input"]) for e in events if e["type"] == "tool_result"]
        self.assertEqual(calls, [(t["tool"], t["input"]) for t in v2_turns()[:-1]])
        verdict = [e for e in events if e["type"] == "verdict"][-1]
        self.assertEqual(verdict["interface"], "v2")
        self.assertEqual(len(verdict["answer_v1_view"]["items"]), 4)

    def test_v1_run_record_has_no_new_fields(self) -> None:
        runs = Path(tempfile.mkdtemp(dir=_TMP))
        result = runner.start(FixtureModel(NORMAL["turns"]), "claim_normal.json", "policy.md", runs,
                              label="v1", case_meta={"constructed": False})
        events = runner.load_events(Path(result["run_dir"]))
        verdict = [e for e in events if e["type"] == "verdict"][-1]
        self.assertNotIn("interface", events[0])
        self.assertNotIn("interface", verdict)
        self.assertNotIn("answer_v1_view", verdict)


class T8CheckerGap(unittest.TestCase):
    def test_passed_v2_run_is_rejected_at_k5_only(self) -> None:
        runs = Path(tempfile.mkdtemp(dir=_TMP))
        result = runner.start(FixtureModel(v2_turns()), "claim_normal.json", "policy.md", runs,
                              label="t8", case_meta={"constructed": False}, interface="v2")
        self.assertEqual(result["status"], "passed")
        outcome = checker.check_run(Path(result["run_dir"]), DATA, runs / "ledger.jsonl")
        failed = [c["check_id"] for c in outcome["checks"] if not c["passed"]]
        self.assertEqual(failed, ["K5_answer_against_source"])
        self.assertFalse(outcome["accepted"])


class T9V1Regression(unittest.TestCase):
    def test_existing_suite_passes(self) -> None:
        proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests",
                               "-p", "test_docassist.py"], cwd=HERE,
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        self.assertRegex(proc.stderr, r"Ran (\d{2,}) tests")      # count grows as tests are added
        self.assertIn("\nOK", proc.stderr)

    def test_run_all_reports_as_expected(self) -> None:
        runs = Path(tempfile.mkdtemp(dir=_TMP))
        proc = subprocess.run([sys.executable, "run.py", "--all", "--runs-dir", str(runs)], cwd=HERE,
                              capture_output=True, text=True, encoding="utf-8")
        lines = [l for l in proc.stdout.splitlines() if l.strip()]
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(len(lines), 9)
        self.assertTrue(all("AS EXPECTED" in l for l in lines), proc.stdout)

    def test_interface_flag_refused_for_constructed_cases(self) -> None:
        import run
        self.assertEqual(run.main(["--case", "normal", "--interface", "v2",
                                   "--runs-dir", str(_TMP / "r")]), 64)


def _phase(arms: dict[str, list[int]], claims: list[str]) -> list[dict]:
    """Synthetic scored runs. arms: arm -> per-claim number of correct runs out of 5;
    every other run failed C6 only."""
    return [{"arm": arm, "claim": claim, "seed": s, "correct": s <= n_correct,
             "categories": [] if s <= n_correct else ["C6_decision_consistent"],
             "schema_valid": True, "c3_fail": False, "blocked_after_retry": False,
             "code_sha256": "C", "options_ok": True}
            for arm, per_claim in arms.items()
            for claim, n_correct in zip(claims, per_claim) for s in range(1, 6)]


DEV = ["claim_normal.json", "claim_injection.json"]
HELD = ["claim_heldout_1.json", "claim_heldout_2.json", "claim_heldout_3.json"]


class TestDecisionRule(unittest.TestCase):
    def decide(self, dev: list[dict], held: list[dict] | None, candidate: str = "v2") -> dict:
        return p10_trials.decide(dev, held, {"tag": candidate, "code_sha256": "C"} if held is not None else None)

    def test_promote(self) -> None:
        out = self.decide(_phase({"v1": [1, 1], "v2": [2, 2]}, DEV),
                          _phase({"v1": [1, 1, 1], "v2": [2, 2, 2]}, HELD))
        self.assertEqual(out["verdict"], "PROMOTE", out)

    def test_null_with_mechanism_confirmed(self) -> None:
        dev = _phase({"v1": [1, 1], "v2": [1, 1]}, DEV)
        held = _phase({"v1": [1, 1, 1], "v2": [2, 1, 1]}, HELD)
        for r in held:
            r["c3_fail"] = r["arm"] == "v1"
        out = self.decide(dev, held)
        self.assertEqual(out["verdict"], "NOT PROMOTED")
        self.assertEqual(out["qualifier"], "null: mechanism confirmed, not promoted")

    def test_harmful_on_claim_regression(self) -> None:
        out = self.decide(_phase({"v1": [1, 1], "v2": [1, 1]}, DEV),
                          _phase({"v1": [3, 0, 0], "v2": [1, 2, 3]}, HELD))
        self.assertEqual((out["verdict"], out["qualifier"]), ("NOT PROMOTED", "harmful"))

    def test_new_failure_category_is_harmful(self) -> None:
        held = _phase({"v1": [1, 1, 1], "v2": [3, 2, 2]}, HELD)
        for r in held[18:20]:                    # two failing v2 runs of heldout_1
            r["categories"] = ["budget_exhausted"]
        out = self.decide(_phase({"v1": [1, 1], "v2": [1, 1]}, DEV), held)
        self.assertEqual((out["verdict"], out["qualifier"]), ("NOT PROMOTED", "harmful"))

    def test_dev_gate(self) -> None:
        dev = _phase({"v1": [1, 1], "v2": [1, 1]}, DEV)
        for r in dev:
            r["c3_fail"] = r["arm"] == "v2"
        self.assertEqual(self.decide(dev, None)["verdict"], "INCOMPLETE")
        revised = dev + [dict(r, arm="v2.1") for r in dev if r["arm"] == "v2"]
        self.assertEqual(self.decide(revised, None)["verdict"], "NOT PROMOTED (DEV GATE)")

    def test_void_on_unbound_code_and_incomplete_on_missing_cells(self) -> None:
        dev = _phase({"v1": [1, 1], "v2": [1, 1]}, DEV)
        held = _phase({"v1": [1, 1, 1], "v2": [4, 4, 4]}, HELD)
        held[0]["code_sha256"] = "other"
        self.assertEqual(self.decide(dev, held)["verdict"], "VOID")
        self.assertEqual(self.decide(dev, held[1:])["verdict"], "INCOMPLETE")

    def test_fisher_one_sided(self) -> None:
        self.assertAlmostEqual(p10_trials.fisher_one_sided(15, 0, 15), 1 / 155117520, places=12)
        self.assertAlmostEqual(p10_trials.fisher_one_sided(0, 0, 15), 1.0)


class TestReviewFixesF2(unittest.TestCase):
    """F2 review items H1, M1, M2, M4, M5 (the driver's guards)."""

    def test_manifest_is_never_created_implicitly_and_never_overwritten(self) -> None:
        path = Path(tempfile.mkdtemp(dir=_TMP)) / "p10_freeze.json"
        self.assertIsNone(p10_trials.load_freeze(path))
        self.assertFalse(path.exists())
        self.assertEqual(p10_trials.init_freeze(path), 0)
        record = json.loads(path.read_text("utf-8"))
        for rel in ("run.py", "experiments/P10_PROTOCOL_ADDENDUM_1_1.md", "experiments/p10_fake_run.py",
                    "experiments/p10_trials.py", "tests/test_docassist.py"):
            self.assertIn(rel, record["files"])
        self.assertEqual(record["addendum_sha256"], record["files"]["experiments/P10_PROTOCOL_ADDENDUM_1_1.md"])
        self.assertEqual(p10_trials.frozen_changes(record), [])
        self.assertEqual(p10_trials.init_freeze(path), 64)

    def test_wrong_model_options_void_the_result(self) -> None:
        dev = _phase({"v1": [1, 1], "v2": [2, 2]}, DEV)
        dev[3]["options_ok"] = False
        self.assertEqual(p10_trials.decide(dev, None, None)["verdict"], "VOID")

    def test_dev_rows_bound_to_one_code_hash_per_arm(self) -> None:
        dev = _phase({"v1": [1, 1], "v2": [1, 1]}, DEV)
        self.assertEqual(p10_trials.code_problems(dev, {"v1", "v2"}, "C"), [])
        self.assertTrue(p10_trials.code_problems(dev, {"v1", "v2"}, "D"))       # code changed mid-phase
        self.assertTrue(p10_trials.code_problems(dev, {"v2.1"}, "C"))           # v2.1 equal to v2
        self.assertEqual(p10_trials.code_problems(dev, {"v2.1"}, "D"), [])
        mixed = [dict(r, code_sha256="X") if i == 0 else r for i, r in enumerate(dev)]
        self.assertTrue(p10_trials.code_problems(mixed, {"v2.1"}, "D"))         # v1 rows disagree

    def test_live_refuses_other_gpu_and_other_output_folder(self) -> None:
        self.assertEqual(p10_trials.main(["--phase", "dev", "--main-gpu", "0"]), 64)
        self.assertEqual(p10_trials.main(["--phase", "dev", "--out", str(_TMP / "elsewhere")]), 64)
        self.assertFalse((_TMP / "elsewhere").exists())

    def test_gpu_placement_deviation_is_recorded_not_refused(self) -> None:
        before = [{"index": 0, "temp_c": 40, "mem_mib": 1000}, {"index": 1, "temp_c": 40, "mem_mib": 500}]
        after = [{"index": 0, "temp_c": 50, "mem_mib": 6000}, {"index": 1, "temp_c": 41, "mem_mib": 500}]
        self.assertTrue(p10_trials.placement(before, after, 1)["note"].startswith("DEVIATION"))
        self.assertEqual(p10_trials.placement(before, before, 1)["gpu"], None)


if __name__ == "__main__":
    unittest.main()
