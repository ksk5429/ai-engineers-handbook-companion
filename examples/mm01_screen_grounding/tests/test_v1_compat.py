"""T1 (rescoring oracle) and v1 reproducibility: the robustness fixes (review M2, M3) leave every
v1 and v1.1 count on the stored R1 replies unchanged."""

from __future__ import annotations

import json
import unittest
from collections import defaultdict

import helpers
from bundle import AGENT_PROMPT, agent_prompt
from rescore import oracle_check, pipeline_pass, r1_counts_v2
from trials import evaluate, labels_v1_1, load, read_spec

R1 = json.loads(helpers.R1_TRIALS.read_text("utf-8"))
_, V1 = load()
V11 = labels_v1_1(V1)


class Oracle(unittest.TestCase):
    def test_t1_per_trial_counts(self) -> None:
        want = read_spec()["dev_labels_v2"]["rescoring_oracle_v1_replies"]["expected_passed_per_trial"]
        got = {k: sum(v) for k, v in r1_counts_v2(R1).items()}
        self.assertEqual(got, want)
        self.assertEqual(sum(got.values()), 16)
        self.assertTrue(oracle_check(R1)[0])


class V1Reproducible(unittest.TestCase):
    def test_v1_totals(self) -> None:
        tot = defaultdict(int)
        for row in R1["rows"]:
            parsed, tid = row["reply"].get("parsed"), row["task_id"]
            tot["v1"] += evaluate(parsed, V1[tid])["passed"]
            tot["v1.1"] += evaluate(parsed, V11[tid])["passed"]
            tot["pipe"] += pipeline_pass(row, V11[tid])
            self.assertEqual(evaluate(parsed, V1[tid]), row["score"], f"{tid} seed {row['seed']}")
        self.assertEqual(dict(tot), {"v1": 13, "v1.1": 22, "pipe": 28})

    def test_v1_prompt_unchanged(self) -> None:
        stored = json.loads((helpers.R1_TRIALS.parent / "PREFLIGHT.json").read_text("utf-8"))
        bundles = {b.task_id: b for b in load()[0]}
        for row in stored["rows"]:
            self.assertEqual(agent_prompt(bundles[row["task_id"]]), row["prompt"], row["task_id"])
        self.assertIn("or missing, ask for a new screenshot", AGENT_PROMPT)


class EvaluateV1Robust(unittest.TestCase):
    label = V1["M4_screenshot_typed"]

    def test_non_dict_target_does_not_crash(self) -> None:
        for target in ("totals.py line 12", ["totals.py", 12], 12):
            s = evaluate({"decision": "answer", "target": target}, self.label)
            self.assertFalse(s["target_ok"])
            self.assertFalse(s["passed"])

    def test_non_dict_reply(self) -> None:
        self.assertFalse(evaluate(["answer"], self.label)["passed"])

    def test_exact_file_name(self) -> None:
        for name, ok in (("subtotals.py", False), ("report_totals.py", False), ("totals.py", True),
                         ("C:\\work\\expenses\\totals.py", True), ("src/Totals.py", True)):
            s = evaluate({"decision": "answer", "target": {"file": name, "line": 12}}, self.label)
            self.assertEqual(s["target_ok"], ok, name)


if __name__ == "__main__":
    unittest.main()
