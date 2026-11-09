"""I5: the Section 2 decision rules and the Section 11 tables, on constructed rows (no model)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers
import rescore
import run_trials as rt
from trials import read_spec

SPEC = read_spec()
H = {"HA1": "HA1_sheet_select_error", "HA2": "HA2_sheet_select_distractor", "HA3": "HA3_sheet_typed_only",
     "HB1": "HB1_chart_select_point", "HB2": "HB2_chart_no_selection", "HC1": "HC1_term_voice_ko",
     "HC2": "HC2_term_typed_only", "HC3": "HC3_term_stale", "HC4": "HC4_term_wrong_window",
     "HC5": "HC5_term_voice_only"}


def rows_for(short: str, arm: str, values: list[dict], blocked: bool = False) -> list[dict]:
    return [{"block": "H", "arm": arm, "task_id": H[short], "status": "ok", "seed": i + 1,
             "preflight": {"proceed": not blocked}, "score": {"decision": None, "target_ok": None, **v}}
            for i, v in enumerate(values)]


def verdicts(rows: list[dict]) -> dict[str, str]:
    table = rescore.hypothesis_table(rows, SPEC, 3)[2:]
    return {line.split("|")[1].strip(): line.split("|")[4].strip() for line in table}


ANS, CLR, NEW = {"decision": "answer"}, {"decision": "clarify"}, {"decision": "new_observation"}
HIT, MISS = {"decision": "answer", "target_ok": True}, {"decision": "answer", "target_ok": False}


class Verdicts(unittest.TestCase):
    def base(self) -> list[dict]:
        return (rows_for("HA3", "P2", [ANS] * 3) + rows_for("HC2", "P2", [ANS] * 3)
                + rows_for("HA3", "P1", [ANS, CLR, CLR]) + rows_for("HC2", "P1", [NEW, CLR, ANS])
                + rows_for("HC5", "P2", [CLR] * 3)
                + rows_for("HA1", "P2", [HIT] * 3) + rows_for("HC1", "P2", [HIT, MISS, MISS])
                + rows_for("HA2", "P2", [HIT] * 3) + rows_for("HB1", "P2", [HIT] * 3)
                + rows_for("HC3", "P2", [NEW] * 3, blocked=True) + rows_for("HC4", "P2", [NEW] * 3, blocked=True)
                + rows_for("HB2", "P2", [ANS, CLR, ANS]))

    def test_rules(self) -> None:
        v = verdicts(self.base())
        self.assertEqual(v, {"H1": "support", "H2": "support", "H3": "inconclusive", "H4": "no support",
                             "H5": "no support", "X1": "report only (exploratory)"})

    def test_h1_no_support_when_v1_answers_as_often(self) -> None:
        rows = [r for r in self.base() if r["arm"] != "P1"] + rows_for("HA3", "P1", [ANS] * 3) + rows_for("HC2", "P1", [ANS] * 3)
        self.assertEqual(verdicts(rows)["H1"], "no support")

    def test_h2_guessing(self) -> None:
        rows = [r for r in self.base() if r["task_id"] != H["HC5"]] + rows_for("HC5", "P2", [ANS, ANS, CLR])
        self.assertEqual(verdicts(rows)["H2"], "no support")

    def test_h4_support_and_h5_support(self) -> None:
        rows = [r for r in self.base() if r["task_id"] not in (H["HB1"], H["HC4"])]
        rows += rows_for("HB1", "P2", [MISS, MISS, HIT]) + rows_for("HC4", "P2", [NEW, CLR, NEW], blocked=True)
        v = verdicts(rows)
        self.assertEqual((v["H4"], v["H5"]), ("support", "support"))

    def test_h5_stops_if_preflight_misses(self) -> None:
        rows = [r for r in self.base() if r["task_id"] != H["HC4"]] + rows_for("HC4", "P2", [NEW] * 3)
        self.assertTrue(verdicts(rows)["H5"].startswith("STOP"))

    def test_error_rows_make_it_undetermined(self) -> None:
        rows = self.base()
        rows[0] = {**rows[0], "status": "error", "score": None}
        self.assertEqual(verdicts(rows)["H1"], "undetermined (n below plan)")


class Report(unittest.TestCase):
    def test_comparison_from_a_mocked_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), \
             mock.patch.dict(os.environ, {"HANDBOOK_HOLD_FLAG": str(Path(tmp) / "none"), "HANDBOOK_MAIN_GPU": "1"}), \
             mock.patch.object(rt, "run_cmd", side_effect=helpers.FakeMachine(preloaded=False)) as cmd, \
             mock.patch.object(rt, "call_ollama", side_effect=lambda *a: (cmd.side_effect.call_made(), {
                 "raw": "{}", "parsed": {"decision": "clarify"}, "thinking": "", "thinking_chars": 0, "wall_s": 0})[1]):
            held = helpers.placeholder_heldout(Path(tmp) / "held")
            out = Path(tmp) / "out"
            self.assertEqual(rt.main(["--protocol", "v2", "--seeds", "1", "--out", str(out), "--heldout-dir", str(held)]), 0)
            r1 = json.loads(helpers.R1_TRIALS.read_text("utf-8"))
            text, ok = rescore.comparison_v2(rescore.read_run(out / "TRIALS_v2.json"), rescore.SPEC_V2, r1)
            self.assertTrue(ok)
            self.assertIn("Oracle check (labels v2 on R1): PASS; total 16/36", text)
            self.assertIn("| HB2_chart_no_selection | screenshot+typed | clarify | clarify 1 |", text)
            self.assertIn("| M1_typed_short | typed | 0/3 | 3/3 | 0/3 | 1/1 | 1/1 |", text)
            self.assertIn("undetermined (n below plan)", text)
            jsonl_text, _ = rescore.comparison_v2(rescore.read_run(out / "TRIALS_v2.jsonl"), rescore.SPEC_V2, None)
            self.assertIn("## Hypotheses", jsonl_text)


if __name__ == "__main__":
    unittest.main()
