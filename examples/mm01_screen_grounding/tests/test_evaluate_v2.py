"""T2: evaluator v2 on hand-written replies (written before any held-out image exists).
At least one pass and one fail per rule and per held-out label."""

from __future__ import annotations

import re
import unittest

import helpers  # noqa: F401  (sets sys.path)
from trials import (evaluate_v2, load_dev_v2, load_spec_trials, merged_rules, norm, read_spec,
                    reply_fields, resolve_label, rule_holds)

SPEC = read_spec()
RULES = merged_rules(SPEC)
HELD = {t.bundle.task_id: t.label for t in load_spec_trials()}
DEV = {t.bundle.task_id: t.label for t in load_dev_v2()}


def target_ok(rule: str, source: str, location: str) -> bool:
    fields = reply_fields({"target": {"source": source, "location": location}})
    return all(rule_holds(r, fields) for r in RULES["target_rules"][rule])


def group(name: str, text: str) -> bool:
    return re.search(RULES["concept_groups"][name], norm(text)) is not None


def mn(name: str, fix: str) -> bool:
    r = RULES["must_not_rules"][name]
    f = norm(fix)
    return re.search(r["pattern"], f) is not None and (r["unless"] is None or re.search(r["unless"], f) is None)


class TargetRules(unittest.TestCase):
    def test_totals_12(self) -> None:
        self.assertTrue(target_ok("T_TOTALS_12", "totals.py", "12"))
        self.assertTrue(target_ok("T_TOTALS_12", "C:\\work\\expenses\\totals.py", "Ln 12, Col 17"))
        self.assertTrue(target_ok("T_TOTALS_12", "TOTALS.PY", "12:17"))
        self.assertFalse(target_ok("T_TOTALS_12", "totals.py", "15"))
        self.assertFalse(target_ok("T_TOTALS_12", "report.py", "12"))

    def test_report_31(self) -> None:
        self.assertTrue(target_ok("T_REPORT_31", "report.py", "line 31"))
        self.assertFalse(target_ok("T_REPORT_31", "totals.py", "31"))

    def test_cell_d4_forms(self) -> None:
        for src, loc in (("Cables", "D4"), ("Cables", "$D$4"), ("sheet Cables", "cell D4"),
                         ("Cables", "row 4, column D"), ("Cables", "column D, row 4")):
            self.assertTrue(target_ok("T_CELL_D4", src, loc), loc)
        for loc in ("D45", "AD4", "D5", "E4"):
            self.assertFalse(target_ok("T_CELL_D4", "Cables", loc), loc)

    def test_cell_d5(self) -> None:
        self.assertTrue(target_ok("T_CELL_D5", "Cables", "D5"))
        self.assertFalse(target_ok("T_CELL_D5", "Cables", "D4"))

    def test_s2_day30(self) -> None:
        self.assertTrue(target_ok("T_S2_DAY30", "S2 (pier P4)", "day 30"))
        self.assertTrue(target_ok("T_S2_DAY30", "주황 점선", "30일"))
        self.assertTrue(target_ok("T_S2_DAY30", "orange dashed curve", "t = 29.5 days"))
        self.assertFalse(target_ok("T_S2_DAY30", "S1 (pier P3)", "day 45"))
        self.assertFalse(target_ok("T_S2_DAY30", "S2", "day 45"))

    def test_load_levels_14(self) -> None:
        self.assertTrue(target_ok("T_LOAD_LEVELS_14", "C:\\work\\survey\\load_levels.py", "line 14"))
        self.assertTrue(target_ok("T_LOAD_LEVELS_14", "load_levels.py", "14번 줄"))
        self.assertFalse(target_ok("T_LOAD_LEVELS_14", "load_levels.py", "21"))
        self.assertFalse(target_ok("T_LOAD_LEVELS_14", "frame.py", "14"))


class ConceptGroups(unittest.TestCase):
    CASES = {
        "G_STR_TOTALS": ("amount is a string", "amount is a number"),
        "G_FIX_TOTALS": ("convert it with float()", "remove the line"),
        "G_MM": ("C is in millimetres", "C is in metres"),
        "G_M": ("B is in metres", "millimeters"),
        "G_CONVERT_1000": ("divide C4 by 1000", "add them"),
        "G_MM_HANDLED": ("C5/1000 converts mm", "looks fine"),
        "G_ANOMALY": ("a sudden spike", "a normal reading"),
        "G_SPACE": ("the header has a space", "the column is missing"),
    }

    def test_each_group_passes_and_fails(self) -> None:
        self.assertEqual(set(self.CASES), set(RULES["concept_groups"]))
        for name, (yes, no) in self.CASES.items():
            self.assertTrue(group(name, yes), name)
            self.assertFalse(group(name, no), name)

    def test_protocol_spot_checks(self) -> None:
        self.assertFalse(group("G_M", "millimeters"))
        self.assertFalse(group("G_M", "밀리미터"))
        self.assertTrue(group("G_M", "미터"))
        self.assertTrue(group("G_SPACE", "공백이 있어"))
        self.assertTrue(group("G_MM", "ｍｍ"))           # full-width, NFKC-normalised


class MustNotRules(unittest.TestCase):
    def test_int(self) -> None:
        self.assertTrue(mn("MN_INT", "use int(item['amount'])"))
        self.assertFalse(mn("MN_INT", "use float(item['amount'])"))

    def test_delete(self) -> None:
        self.assertTrue(mn("MN_DELETE", "delete the tests folder"))
        self.assertTrue(mn("MN_DELETE", "tests 폴더를 삭제"))
        self.assertFalse(mn("MN_DELETE", "convert to float"))

    def test_strip_only(self) -> None:
        self.assertTrue(mn("MN_STRIP_ONLY", "df.columns = df.columns.str.strip()"))
        self.assertFalse(mn("MN_STRIP_ONLY", 'strip() and use df["수위 (m)"]'))
        self.assertFalse(mn("MN_STRIP_ONLY", "str.strip() then str.replace(' ', '')"))
        self.assertFalse(mn("MN_STRIP_ONLY", 'use df["수위 (m)"]'))


def reply(decision: str = "answer", source: str | None = None, location: str | None = None,
          explanation: str = "", fix: str = "", problem_found: object = None, **kw: object) -> dict:
    target = {"source": source, "location": location, "issue_type": "x"} if source else None
    return {"decision": decision, "target": target, "problem_found": problem_found,
            "evidence": kw.get("evidence", ""), "explanation": explanation, "fix": fix,
            "clarification_question": None, "uncertainty": kw.get("uncertainty", "")}


GOOD_UNITS = dict(explanation="B4 is in metres (m) but C4 is in mm", fix="use =B4+C4/1000")


class HeldOutLabels(unittest.TestCase):
    """One passing and one failing hand-written reply per held-out trial."""

    def check(self, tid: str, good: dict, bad: dict) -> None:
        self.assertTrue(evaluate_v2(good, HELD[tid])["passed"], tid)
        self.assertFalse(evaluate_v2(bad, HELD[tid])["passed"], tid)

    def test_ha1(self) -> None:
        self.check("HA1_sheet_select_error", reply(source="Cables", location="D4", problem_found=True, **GOOD_UNITS),
                   reply(source="Cables", location="D5", problem_found=True, **GOOD_UNITS))

    def test_ha2(self) -> None:
        self.check("HA2_sheet_select_distractor",
                   reply(source="Cables", location="D5", problem_found=False,
                         explanation="D5 divides C5 by 1000, so mm are converted", fix="none needed"),
                   reply(source="Cables", location="D4", problem_found=True, **GOOD_UNITS))

    def test_ha2_problem_found_must_be_boolean_false(self) -> None:
        r = reply(source="Cables", location="D5", problem_found="false",
                  explanation="C5/1000 handles mm", fix="none")
        s = evaluate_v2(r, HELD["HA2_sheet_select_distractor"])
        self.assertFalse(s["problem_found_ok"])
        self.assertFalse(s["passed"])

    def test_ha3(self) -> None:
        self.check("HA3_sheet_typed_only", reply(source="site_survey.ods", location="$D$4", problem_found=True, **GOOD_UNITS),
                   reply("new_observation"))

    def test_hb1(self) -> None:
        self.check("HB1_chart_select_point",
                   reply(source="S2 (pier P4)", location="day 30, 47.1 mm", problem_found=True,
                         explanation="an isolated spike, implausible", fix="check the logger"),
                   reply(source="S1 (pier P3)", location="day 45", problem_found=True,
                         explanation="a spike", fix="check"))

    def test_hb2(self) -> None:
        self.check("HB2_chart_no_selection", reply("clarify"),
                   reply(source="S1", location="day 45", problem_found=True))

    def test_hc1(self) -> None:
        good = reply(source="load_levels.py", location="line 14", problem_found=True,
                     explanation="the header '수위 (m)' has a space", fix='use df["수위 (m)"]')
        strip_only = reply(source="load_levels.py", location="line 14", problem_found=True,
                           explanation="there is a space", fix="df.columns = df.columns.str.strip()")
        self.check("HC1_term_voice_ko", good, strip_only)
        self.assertEqual(evaluate_v2(strip_only, HELD["HC1_term_voice_ko"])["must_not_hits"], ["MN_STRIP_ONLY"])

    def test_hc2(self) -> None:
        self.check("HC2_term_typed_only",
                   reply(source="load_levels.py", location="14", problem_found=True,
                         explanation="열 이름에 공백이 있어", fix="df.columns = df.columns.str.replace(' ', '')"),
                   reply(source="frame.py", location="4102", problem_found=True,
                         explanation="공백", fix="x"))

    def test_hc3_hc4(self) -> None:
        for tid in ("HC3_term_stale", "HC4_term_wrong_window"):
            self.check(tid, reply("new_observation"), reply(source="load_levels.py", location="14", problem_found=True))

    def test_hc5(self) -> None:
        self.check("HC5_term_voice_only", reply("clarify"), reply("new_observation"))


class Components(unittest.TestCase):
    def test_unparsed_fails_every_component(self) -> None:
        for bad in (None, ["answer"], "answer", 3):
            s = evaluate_v2(bad, HELD["HA1_sheet_select_error"])
            self.assertEqual([s[k] for k in ("decision_ok", "target_ok", "concepts_ok", "must_not_ok",
                                             "problem_found_ok", "passed")], [False] * 6)

    def test_non_dict_target_fails_target(self) -> None:
        for target in ("load_levels.py line 14", ["load_levels.py", 14], None):
            r = {**reply(problem_found=True, explanation="space", fix="x"), "target": target}
            s = evaluate_v2(r, HELD["HC1_term_voice_ko"])
            self.assertFalse(s["target_ok"])
            self.assertFalse(s["passed"])

    def test_v1_schema_is_mapped(self) -> None:
        r = {"decision": "answer", "target": {"file": "totals.py", "line": 12, "error_type": "TypeError"},
             "explanation": "amount is a str", "fix": "convert with float()"}
        self.assertTrue(evaluate_v2(r, DEV["M4_screenshot_typed"])["passed"])
        r_int = {**r, "fix": "use int(item['amount'])"}
        self.assertFalse(evaluate_v2(r_int, DEV["M4_screenshot_typed"])["must_not_ok"])

    def test_not_applicable_components_are_none(self) -> None:
        s = evaluate_v2(reply("clarify"), HELD["HB2_chart_no_selection"])
        self.assertIsNone(s["target_ok"])
        self.assertIsNone(s["concepts_ok"])
        self.assertIsNone(s["problem_found_ok"])
        self.assertTrue(s["abstained"])

    def test_secondary_checks(self) -> None:
        r = reply(source="S2", location="day 30", problem_found=True, explanation="47 mm spike",
                  fix="x", evidence="inside the cyan rectangle")
        sec = evaluate_v2(r, HELD["HB1_chart_select_point"])["secondary"]
        self.assertEqual(sec, {"S_SELECTION_CLAIMED": True, "S_VALUE_47": True})
        r2 = reply(source="load_levels.py", location="14", problem_found=True, explanation="space",
                   fix="set encoding='cp949'")
        self.assertTrue(evaluate_v2(r2, HELD["HC1_term_voice_ko"])["secondary"]["S_DISTRACTOR_FOLLOWED_TERM"])

    def test_unknown_rule_name_fails_fast(self) -> None:
        with self.assertRaises(KeyError):
            resolve_label({"expect": "answer", "target": "T_NO_SUCH_RULE"}, RULES)


if __name__ == "__main__":
    unittest.main()
