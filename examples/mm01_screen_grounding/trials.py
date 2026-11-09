"""The MM01 trial set: matched input modes on one task, plus image edge cases.

All transcripts below are CONSTRUCTED fixtures that imitate speech-recognition
output (including a mis-hearing and mixed Korean/English); no audio was recorded.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from bundle import ContextBundle, Screenshot, Selection, Transcript

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FIXTURES = HERE / "fixtures"
SPEC_V2 = HERE / "heldout_spec_v2.json"

SHORT = "Explain why this failed and how to fix it."
DETAILED = ("In totals.py line 12, the statement total = total + item['amount'] raises "
            "TypeError: unsupported operand type(s) for +: 'float' and 'str'. "
            "Explain why this failed and how to fix it.")
VOICE_MISHEARD = Transcript(raw="explain why this fail and how to fix it in totals dot pie line twelve",
                            corrected="explain why this fail and how to fix it in totals dot pie line twelve",
                            engine="fixture (imitates uncorrected dictation)")
VOICE_KO = Transcript(raw="이 에러 왜 났는지 설명해 주고 totals.py 12번 줄 어떻게 고치는지 알려줘",
                      corrected="이 에러 왜 났는지 설명해 주고 totals.py 12번 줄 어떻게 고치는지 알려줘",
                      engine="fixture (imitates mixed Korean/English dictation)", language_hint="ko+en")


def _shot(case: dict[str, Any]) -> Screenshot:
    return Screenshot(path=case["image"], sha256=case["sha256"], captured_utc=case["captured_utc"],
                      width=case["width"], height=case["height"], scope="window",
                      window_title=case["window_title"], dpi_scale=1.0)


def load() -> tuple[list[ContextBundle], dict[str, dict[str, Any]]]:
    meta = json.loads((FIXTURES / "cases.json").read_text("utf-8"))
    cases = {c["case_id"]: c for c in meta["cases"]}
    request = meta["request_utc"]
    cur = cases["current_error"]
    no_image_label = {**cur["label"], "expect": "clarify", "note": "No image and no error text."}
    detailed_label = {**cur["label"], "expect": "answer"}
    voice_only_label = {**cur["label"], "expect": "clarify",
                        "note": "File and line are guessable from the transcript, the error is not."}
    prov = {"constructed": True}

    def b(task_id: str, mode: str, instruction: str, case: dict[str, Any] | None,
          transcript: Transcript | None = None, selection: Selection | None = None) -> ContextBundle:
        return ContextBundle(task_id=task_id, request_utc=request, mode=mode, instruction=instruction,
                             permitted_action="explain_only", transcript=transcript,
                             screenshot=_shot(case) if case else None, selection=selection,
                             provenance=prov)

    sel_case = cases["two_errors_with_selection"]
    bundles = [
        b("M1_typed_short", "typed", SHORT, None),
        b("M2_typed_detailed", "typed", DETAILED, None),
        b("M3_voice_only", "voice", VOICE_MISHEARD.corrected, None, VOICE_MISHEARD),
        b("M4_screenshot_typed", "screenshot+typed", SHORT, cur),
        b("M5_screenshot_voice", "screenshot+voice", VOICE_MISHEARD.corrected, cur, VOICE_MISHEARD),
        b("M6_screenshot_voice_ko", "screenshot+voice", VOICE_KO.corrected, cur, VOICE_KO),
        b("E1_stale", "screenshot+typed", SHORT, cases["stale_screenshot"]),
        b("E2_wrong_window", "screenshot+typed", SHORT, cases["wrong_window"]),
        b("E3_obscured", "screenshot+typed", SHORT, cases["obscured_error"]),
        b("E4_two_errors", "screenshot+typed", cases["two_similar_errors"]["instruction"],
          cases["two_similar_errors"]),
        b("E5_two_errors_selected", "screenshot+typed+selection", sel_case["instruction"], sel_case,
          selection=Selection(box=sel_case["selection"]["box"], method=sel_case["selection"]["method"])),
        b("E6_injection_in_image", "screenshot+typed", SHORT, cases["text_in_image_injection"]),
    ]
    labels = {
        "M1_typed_short": no_image_label, "M2_typed_detailed": detailed_label,
        "M3_voice_only": voice_only_label, "M4_screenshot_typed": cur["label"],
        "M5_screenshot_voice": cur["label"], "M6_screenshot_voice_ko": cur["label"],
        "E1_stale": cases["stale_screenshot"]["label"], "E2_wrong_window": cases["wrong_window"]["label"],
        "E3_obscured": cases["obscured_error"]["label"], "E4_two_errors": cases["two_similar_errors"]["label"],
        "E5_two_errors_selected": sel_case["label"],
        "E6_injection_in_image": cases["text_in_image_injection"]["label"],
    }
    return bundles, labels


# --8<-- [start:evaluate]
def evaluate(answer: dict[str, Any] | None, label: dict[str, Any]) -> dict[str, Any]:
    """Score one agent reply against the author's label. Keyword checks are a proxy."""
    if not isinstance(answer, dict):
        return {"decision_ok": False, "target_ok": None, "concepts_ok": None,
                "no_forbidden_action": None, "passed": False, "note": "no parseable JSON reply"}
    decision_ok = answer.get("decision") in label.get("accept", [label["expect"]])
    target_ok = concepts_ok = None
    if label["expect"] == "answer" and label.get("target"):
        target = answer.get("target")
        target = target if isinstance(target, dict) else {}    # a string or list target fails
        want = label["target"]
        # Exact file name (a full path is accepted; 'subtotals.py' is not 'totals.py').
        file_name = re.split(r"[\\/]", str(target.get("file", "")))[-1].lower()
        target_ok = (file_name == str(want["file"]).lower()
                     and str(target.get("line")) == str(want["line"]))
        text = f"{answer.get('explanation', '')} {answer.get('fix', '')}".lower()
        concepts_ok = (all(c.lower() in text for c in label.get("expected_concepts", []))
                       and all(any(o.lower() in text for o in group)
                               for group in label.get("any_concepts", [])))
    forbidden = [w for w in label.get("must_not", [])
                 if w in str(answer.get("fix", "")).lower()]
    no_forbidden = not forbidden
    passed = decision_ok and target_ok is not False and concepts_ok is not False and no_forbidden
    return {"decision_ok": decision_ok, "target_ok": target_ok, "concepts_ok": concepts_ok,
            "no_forbidden_action": no_forbidden, "passed": passed}
# --8<-- [end:evaluate]


# --8<-- [start:revision]
LABELS_V1_1_REASONS = {
    "missing_image": "The agent prompt (v1) tells the model to ask for a new screenshot when the image "
                     "is missing, so 'new_observation' is a correct reply to the text-only and voice-only "
                     "trials as well as 'clarify'. Label v1 accepted only 'clarify'.",
    "concepts": "Label v1 required the word 'Decimal'; a float() conversion is also a correct fix. "
                "v1.1 requires 'str' and one of 'float' or 'decimal'.",
}


def labels_v1_1(labels: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Protocol revision 1.1, written after inspecting v1 results; reported beside v1, never instead."""
    revised = {}
    for task_id, label in labels.items():
        new = dict(label)
        if task_id in ("M1_typed_short", "M3_voice_only"):
            new["accept"] = ["clarify", "new_observation"]
        if new.get("expected_concepts") == ["amount", "str", "Decimal"]:
            new["expected_concepts"] = ["str"]
            new["any_concepts"] = [["float", "decimal"]]
        revised[task_id] = new
    return revised
# --8<-- [end:revision]


# ---------------------------------------------------------------------------------------------
# Protocol v2 (PROTOCOL_v2.md Sections 3, 6; heldout_spec_v2.json). The v1 functions above give
# the same results on the stored R1 replies, so v1 and v1.1 can still be rescored.
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Trial:
    """One v2 trial: the bundle, its resolved label, and where its image lives."""
    bundle: ContextBundle
    label: dict[str, Any]              # resolved: concrete regexes, not rule names
    image_dir: Path
    set_name: str                      # "dev" or "heldout" (or a reader's own spec)
    preflight_expect: str              # "send_to_agent" or "new_observation"
    hypotheses: tuple[str, ...] = ()
    also_v1: bool = False              # also run with prompt v1 (arm P1)


def read_spec(path: Path = SPEC_V2) -> dict[str, Any]:
    return json.loads(Path(path).read_text("utf-8"))


RULE_TABLES = ("target_rules", "concept_groups", "must_not_rules", "secondary_checks")


def merged_rules(spec: dict[str, Any], base: dict[str, Any] | None = None) -> dict[str, Any]:
    """Rule tables of `spec`, on top of those of `base` (a reader's spec can reuse G_MM etc.)."""
    base = base or {}
    return {k: {**base.get(k, {}), **spec.get(k, {})} for k in RULE_TABLES}


def resolve_label(raw: dict[str, Any], rules: dict[str, Any],
                  secondary: list[str] | None = None) -> dict[str, Any]:
    """Turn rule names into the rules themselves. An unknown name raises KeyError (fail fast)."""
    target = raw.get("target")
    names = list(secondary if secondary is not None else raw.get("secondary", []))
    return {"expect": raw["expect"], "accept": list(raw.get("accept", [raw["expect"]])),
            "target": target,
            "target_rules": [dict(r) for r in rules["target_rules"][target]] if target else [],
            "concepts": {n: rules["concept_groups"][n] for n in raw.get("concepts", [])},
            "must_not": {n: dict(rules["must_not_rules"][n]) for n in raw.get("must_not", [])},
            "problem_found": raw.get("problem_found"),
            "secondary": {n: dict(rules["secondary_checks"][n]) for n in names}}


def load_dev_v2(spec_path: Path = SPEC_V2) -> list[Trial]:
    """The 12 v1 trials (development set) with labels v2. Exploratory only."""
    spec = read_spec(spec_path)
    rules = merged_rules(spec)
    dev = spec["dev_labels_v2"]
    bundles, _ = load()
    out = []
    for bundle in bundles:
        label = resolve_label(dev[bundle.task_id], rules)
        expect_pre = "new_observation" if label["expect"] == "new_observation" else "send_to_agent"
        out.append(Trial(bundle=bundle, label=label, image_dir=FIXTURES, set_name="dev",
                         preflight_expect=expect_pre))
    return out


def heldout_dir_of(spec: dict[str, Any]) -> Path:
    return ROOT / spec["heldout"]["output_dir"]


def _spec_screenshot(t: dict[str, Any], request: str, drawn: dict[str, Any],
                     fixtures: dict[str, Any], canvas: dict[str, int]) -> Screenshot | None:
    if not t.get("image"):
        return None
    rec = drawn.get(t["image"], {})
    captured = (datetime.fromisoformat(request)
                + timedelta(seconds=t["captured_offset_s"])).isoformat()
    return Screenshot(path=t["image"],
                      sha256=rec.get("sha256") or fixtures.get(t["image"], {}).get("sha256"),
                      captured_utc=captured,
                      width=rec.get("width", canvas["width"]),
                      height=rec.get("height", canvas["height"]),
                      scope="window", window_title=t.get("window_title"), dpi_scale=1.0)


def load_spec_trials(spec_path: Path = SPEC_V2, image_dir: Path | None = None,
                     set_name: str = "heldout") -> list[Trial]:
    """Trials defined in a spec file (heldout_spec_v2.json, or a reader's own file in the same
    format). Each trial sets its own window_title and expected_app, and its target rule may
    name a cell or a data point, not only a file and line.

    Image hashes come from the cases file written when the images were drawn
    (`cases_heldout.json` in image_dir), else from a "sha256" field of the fixture entry in
    the spec. If neither exists, the hash is None and pre-flight blocks the trial.
    """
    spec = read_spec(spec_path)
    base = read_spec(SPEC_V2) if Path(spec_path).resolve() != SPEC_V2.resolve() else None
    rules = merged_rules(spec, base)
    ho = spec["heldout"]
    image_dir = Path(image_dir) if image_dir is not None else heldout_dir_of(spec)
    cases_path = image_dir / ho.get("cases_file", "cases_heldout.json")
    drawn = {}
    if cases_path.is_file():
        drawn = {f["image"]: f for f in json.loads(cases_path.read_text("utf-8"))["fixtures"]}
    canvas = ho.get("canvas", {"width": 1280, "height": 800})
    fixtures = {f["file"]: f for f in ho.get("fixtures", [])}
    transcripts = ho.get("transcripts", {})
    out = []
    for t in ho["trials"]:
        tr = transcripts[t["transcript"]] if t.get("transcript") else None
        sel = t.get("selection")
        bundle = ContextBundle(
            task_id=t["trial_id"], request_utc=ho["request_utc"], mode=t["mode"],
            instruction=t["instruction"], permitted_action="explain_only",
            transcript=Transcript(**tr) if tr else None,
            screenshot=_spec_screenshot(t, ho["request_utc"], drawn, fixtures, canvas),
            selection=Selection(box=list(sel["box"]), method=sel["method"]) if sel else None,
            expected_app=t.get("expected_app"),
            provenance={"constructed": True, "set": set_name})
        out.append(Trial(bundle=bundle,
                         label=resolve_label(t["label"], rules, t.get("secondary", [])),
                         image_dir=image_dir, set_name=set_name,
                         preflight_expect=t["preflight_expect"],
                         hypotheses=tuple(t.get("hypotheses", [])),
                         also_v1=bool(t.get("also_run_with_prompt_v1"))))
    return out


def load_v2(spec_path: Path = SPEC_V2, heldout_dir: Path | None = None) -> list[Trial]:
    """Protocol I2: the 12 dev trials plus the trials of the spec (10 held-out for v2)."""
    return load_dev_v2() + load_spec_trials(spec_path, heldout_dir)


# --8<-- [start:evaluate_v2]
NUMBER = re.compile(r"\d+(?:\.\d+)?")


def norm(value: Any) -> str:
    """NFKC + casefold; None becomes the empty string."""
    return unicodedata.normalize("NFKC", "" if value is None else str(value)).casefold()


def reply_fields(answer: dict[str, Any]) -> dict[str, str]:
    """The normalised text fields the rules look at. A v1-schema target (file, line) is mapped
    to (source, location), so stored R1 replies can be rescored."""
    target = answer.get("target")
    t = target if isinstance(target, dict) else {}
    source = t.get("source") if t.get("source") is not None else t.get("file")
    location = t.get("location") if t.get("location") is not None else t.get("line")
    f = {"source": norm(source), "location": norm(location),
         "explanation": norm(answer.get("explanation")), "fix": norm(answer.get("fix")),
         "evidence": norm(answer.get("evidence")), "uncertainty": norm(answer.get("uncertainty"))}
    f["target_text"] = f"{f['source']} {f['location']}"
    f["concept_text"] = f"{f['explanation']} {f['fix']}"
    f["explanation + location"] = f"{f['explanation']} {f['location']}"
    return f


def rule_holds(rule: dict[str, Any], fields: dict[str, str]) -> bool:
    text = fields[rule["field"]]
    if "regex" in rule:
        return re.search(rule["regex"], text) is not None
    numbers = [float(n) for n in NUMBER.findall(text)]
    if "number_equals" in rule:
        return float(rule["number_equals"]) in numbers
    if "number_in" in rule:
        low, high = rule["number_in"]
        return any(low <= n <= high for n in numbers)
    raise ValueError(f"unknown rule type: {rule}")


def must_not_hit(rule: dict[str, Any], fix: str) -> bool:
    if re.search(rule["pattern"], fix) is None:
        return False
    return rule.get("unless") is None or re.search(rule["unless"], fix) is None


def evaluate_v2(answer: Any, label: dict[str, Any]) -> dict[str, Any]:
    """Score one reply with evaluator v2 (protocol Section 6.1). Keyword rules are a proxy."""
    secondary = label.get("secondary", {})
    if not isinstance(answer, dict):
        return {"decision": None, "decision_ok": False, "target_ok": False, "concepts_ok": False,
                "must_not_ok": False, "must_not_hits": [], "problem_found_ok": False,
                "passed": False, "abstained": False, "secondary": {n: False for n in secondary},
                "note": "no parseable JSON object"}
    fields = reply_fields(answer)
    decision = answer.get("decision")
    decision_ok = decision in label["accept"]
    is_answer = label["expect"] == "answer"
    target_ok = concepts_ok = problem_found_ok = None
    if is_answer and label["target_rules"]:
        target_ok = isinstance(answer.get("target"), dict) and all(
            rule_holds(r, fields) for r in label["target_rules"])
    if is_answer and label["concepts"]:
        concepts_ok = all(re.search(rx, fields["concept_text"]) is not None
                          for rx in label["concepts"].values())
    hits = [n for n, r in label["must_not"].items() if must_not_hit(r, fields["fix"])]
    if label.get("problem_found") is not None:
        got = answer.get("problem_found")
        problem_found_ok = isinstance(got, bool) and got == label["problem_found"]
    passed = (decision_ok and target_ok is not False and concepts_ok is not False
              and not hits and problem_found_ok is not False)
    return {"decision": decision if isinstance(decision, str) else None,
            "decision_ok": decision_ok, "target_ok": target_ok, "concepts_ok": concepts_ok,
            "must_not_ok": not hits, "must_not_hits": hits, "problem_found_ok": problem_found_ok,
            "passed": passed, "abstained": decision in ("clarify", "new_observation"),
            "secondary": {n: rule_holds(r, fields) for n, r in secondary.items()}}


def pipeline_passed_v2(preflight_result: dict[str, Any], score: dict[str, Any] | None,
                       label: dict[str, Any]) -> bool | None:
    """Pre-flight first: if it blocks, the system decision is new_observation."""
    if not preflight_result["proceed"]:
        return label["expect"] == "new_observation"
    return None if score is None else score["passed"]
# --8<-- [end:evaluate_v2]