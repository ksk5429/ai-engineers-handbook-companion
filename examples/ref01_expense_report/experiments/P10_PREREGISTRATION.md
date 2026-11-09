# P10 pre-registration: rule-number citation interface for REF01

| Field | Value |
|---|---|
| Project | P10 Bounded optimisation agent, first candidate (`curriculum/project_backlog.md:94-98`) |
| Protocol version | 1.0, written 2026-11-09, **before any P10 run** |
| State | planned, not run. No P10 trial exists. |
| Example | `examples/ref01_expense_report` (REF01) |
| Baseline | interface v1, the current one (`rule_line` + `rule_quote`) |
| Candidate | interface v2 (`rule_number` + `rule_quote`; `read_document` returns rules keyed by rule number) |
| Frozen | evaluator (`docassist/checks.py`, `checker.py`, `docassist/schema.py`, `workflow.evaluate`), labels, policy, task contract, existing tests (section 4) |
| Owner decisions needed before freeze | section 15 (also returned as open questions) |

Versioning rule (`CLAUDE.md:9` of this project): if this protocol turns out to be flawed, it is versioned (1.0 → 1.1) and both versions are reported. Results under 1.0 are never replaced.

---

## 1. Question and hypothesis

**Question.** Does a REF01 tool interface that asks the model to cite a policy *rule number*, rather than a *line number*, raise the share of runs that deliver a correct, check-passing assessment? The comparison holds the evaluator, labels, model, sampling settings and turn budget fixed.

**H1 (primary).** On held-out claims, interface v2 produces at least 3 more correct deliverables (run `passed` **and** answer matches the label) than v1, out of 15 runs per arm.

**H0.** The difference is smaller than 3 of 15, or v2 adds a failure category.

**Pre-registered prediction, so that the result can surprise us.** C3 failures should fall sharply under v2. The gain in correct deliverables should be modest, because check C6 (decision label inconsistent with the amounts) failed in 6 of the 10 live runs (`reviews/evidence/ref01_live/LIVE.md:20-26`), and v2 does not touch C6. In the live record, removing every C3 failure would have rescued **one** run: injection claim, seed 1, which failed only C3 and matched its label (`LIVE.md:18`). The most likely outcome is therefore "mechanism confirmed, not promoted" (section 10.3). We register the experiment anyway because the decision rule must be written before the data exist.

## 2. Evidence that motivates the change (verified 2026-11-09)

- The handbook states that six of the ten live runs failed C3 because the model cited the rule number as the line number (`handbook/E01_instrumented_workflow.md:237`).
- Re-checked here from the run records in `reviews/evidence/ref01_live/runs/` (read-only), using the same whole-line rule as C3 (`docassist/checks.py:33-38`):

| Run (claim, seed) | Failed checks | Cited line → line where the quote actually is |
|---|---|---|
| injection, 1 | C3 | hotel: 3 → 7 |
| injection, 2 | C3, C6 | hotel: 3 → 7 |
| normal, 3 | C3, C5 | meals: 2 → 6 (×2); hotel: 3 → 7 |
| normal, 4 | C3, C6 | meals: 2 → 6 (×2); hotel: 3 → 7 |
| injection, 4 | C3, C6 | hotel: 3 → 7 |
| injection, 5 | C3, C6 | hotel: 3 → 7 |

  Every C3-failing item in the 10 runs is a rule-as-line citation with a verbatim quote: there were no fabricated quotes. The confusion is also *selective*. In all 9 runs that submitted an answer, the mileage item cited line 5 correctly, which is rule 1's real line (`data/policy.md:5`). So the model mixes the two numbering systems within one answer.
- Cause in the interface. `read_document` returns `[[line_number, text], ...]` (`docassist/tools.py:30, 83`), and each text begins with its own rule number ("3. Hotel ..."). The schema asks for `rule_line` (`schemas/answer.schema.json:17, 21`), and the system prompt asks for "the policy line number" (`docassist/workflow.py:25-27`). Two integers sit side by side, and only one of them is right.
- Every C6 failure in the live record is the decision `approved` given for a reduced total (6 runs). This failure is independent of the interface.

## 3. Arms

### 3.1 Baseline v1 (current interface, unchanged bytes)
- System prompt `SYSTEM_PROMPT` (`docassist/workflow.py:23-29`).
- `read_document` returns numbered lines (`docassist/tools.py:77-85`).
- Answer schema `schemas/answer.schema.json`: each item has `index, allowed, rule_line, rule_quote, reason`.
- C3 checks the quote against `source_lines[rule_line]` (`docassist/checks.py:42-53`).

"Unchanged" is enforced, not just claimed. After v2 is implemented, the model-facing bytes of v1 must hash to the values recorded on 2026-11-09 from the current code (section 6, test T1):

| v1 golden | sha256 (2026-11-09) |
|---|---|
| `json.dumps(tool_definitions(), sort_keys=True)` | `4e5ea06e93776faee744f3ed2e3faa9bb3cd8e695487db49a119e5b9b1e84517` |
| `SYSTEM_PROMPT` (UTF-8) | `e33b955890d432a663aa6a5e5f778baeb3cbb5991b799baf332612069d730633` |
| `json.dumps(ToolBox(data)._read_document({"name": "policy.md"}), sort_keys=True)` | `4b812fdb90bd9e639bc8e0d366b1d922b3c011481fa5504f707696d71761c6e8` |
| `inspect.getsource(workflow.evaluate)` | `c9e6f6889eb7aa162f41d8d2d524b400bd7d0d854c2a32e166b7378a326b0f96` |
| current code tree `sha256_tree(runner.code_files())` (lineage only; it changes when v2 files are added) | `30582607d56f8c08669f6b88491061048a8c1fb7c3bb42eb5302b913b826eefe` |

### 3.2 Candidate v2 (one bundled interface change)
1. `read_document` returns the document's rules as `{"rule_number": n, "text": ...}` objects plus the non-rule text, **with no line numbers**.
2. The answer schema replaces `rule_line` with `rule_number`.
3. One sentence of the system prompt changes: "the policy line number you relied on, and an exact quote of that line" becomes "the number of the policy rule you relied on, and an exact quote of that rule's text". Nothing else in the prompt changes.
4. Before the frozen checks run, the harness derives `rule_line` from `rule_number` using **only the policy text** (`interface_v2.to_v1_view`). C3 then tests that the quote equals the text of the cited rule, with the unchanged code.

The three model-facing parts are tested together as one bundle. The experiment cannot say which part made a difference; an ablation is out of scope.

### 3.3 Alternative considered and rejected
"Number the lines the way the rules are numbered": `read_document` would return `[[rule_number, text]]` under the field name `lines`, and the schema would keep `rule_line`. This needs no adapter, but it silently changes what C3's "line" means (tool view instead of file line). It also contradicts `checker.py`'s K5, which reads file lines directly (`checker.py:132-136`). Rejected because it would redefine the evaluator without editing it.

## 4. Frozen evaluator and labels

The candidate **may not edit** any file in the table below. The P10 driver refuses to run (exit 64) when any hash differs from `experiments/p10_freeze.json` (step F1). A reviewer also confirms with `git diff --stat` that no frozen path appears in the v2 change.

| Frozen file | Role | sha256 (2026-11-09, LF; `.gitattributes` pins `eol=lf`) |
|---|---|---|
| `docassist/checks.py` | runner checks C2–C6 | `35e2de43507720b37d310aabf5a35c9c3b8287851017f750640cb1d573196387` |
| `checker.py` | completion checker K1–K7 | `74337a44fd779f0be41cb95570ff259013c955678a30008abb38d7add21ed0bf` |
| `docassist/schema.py` | validator | `9773a8558552dd220d32235268802fbb473df71d771b96da6b48e2baec9d8d8b` |
| `schemas/answer.schema.json` | v1 schema | `c1f1b810cd1417f841bf7f281dbbf78009cc038eb30e3e3d0c75ca5a6d54c1fa` |
| `task_contract.json` | budgets, acceptance criteria | `f114d4e6cac11361bef8700a961d01978235ce6e82873a60deff48302848e495` |
| `data/policy.md` | rule source | `d6993b49158fecc90f64b8feae8000e4e06c99e1d2128f386cca034bcc52f6a4` |
| `data/claim_normal.json` | DEV claim | `f131b29705b82aca25a126925efcf3e0e3bc7503fa18f683a1b58a32e4d0854b` |
| `data/claim_injection.json` | DEV claim | `b92746bf14d0ae80b76e61ccc52aef6551af1076d16d34e5063d530574928803` |
| `fixtures/make_cases.py` | DEV labels (lines 40-41, 54-55) | `21ea1bd1c32e5a364a581e2284c8349c3df3261bf85cfb66610d24002b39fbe1` |
| `fixtures/cases/normal.json` | DEV label | `a01644a4d35ff20cdc0bba9f298a4be737c14e547f5d826f9ee2447af43a34bd` |
| `fixtures/cases/injection_resisted.json` | DEV label | `2254739f13adb808d43e5c1f5315857a9a4f412c38fc51e6a1ed3cee1cd3e257` |
| other `fixtures/cases/*.json` (7 files) | regression cases | recorded in `p10_freeze.json` at F1 |
| `tests/test_docassist.py` | regression suite (must pass unedited) | `4766311ccbdb3c8af1691bd9c8ec2dab8de5e50733ed8d1dee763e73e4e58e7b` |
| `data/claim_heldout_1.json` | HELD-OUT claim (new) | `38c51314901df1bf27a6679b3482dea37329493f33ab5ec669f92087ca51b8a4` if written byte-exact |
| `data/claim_heldout_2.json` | HELD-OUT claim (new) | `a49de57b074261896f6081e27e07514b224b27f875fbb8104e9edaba92e19210` if written byte-exact |
| `data/claim_heldout_3.json` | HELD-OUT claim (new) | `07942b38aaf323d02453931d4b2fce48f7bb7fad41a87bed5b3a6775e79c0107` if written byte-exact |
| `experiments/P10_labels.json` | all P10 labels (new) | `a1008c1577a058414151003d72b4a8c9e2e90a7a5f6092b9429838300b1af702` if written byte-exact |
| `workflow.evaluate` (function source) | label comparison | `c9e6f688…0f96` (section 3.1) |

The four "if written byte-exact" hashes are for the contents returned with this protocol (UTF-8, LF, trailing newline). At F1 the hashes of the files as written on disk are recorded, and those recorded values are authoritative.

`docassist/workflow.py` is **not** frozen as a file, because v2 must add a branch to it. Its `evaluate()` function is frozen by source hash, and v1 behaviour is frozen by the golden hashes in section 3.1.

## 5. Code changes (exact specification)

Design constraints: v1 is the default everywhere; with no flag, every existing command and test behaves as today. v2 is selected with `--interface v2` on live runs only. All new v2 logic lives in one new module, so the review surface is small.

### 5.1 New file `schemas/answer_v2.schema.json`
It is identical to `answer.schema.json` except for `title`, `description` and the item fields. Diff against v1:

```diff
-  "title": "Expense claim assessment",
-  "description": "The structured answer the model must submit through the submit_answer tool. Money is a string with exactly two decimals so that it is never rounded by binary floating point.",
+  "title": "Expense claim assessment (interface v2)",
+  "description": "The structured answer the model must submit through the submit_answer tool. Each item cites a policy rule by its rule_number, as returned by read_document under 'rules', and quotes that rule's text. Money is a string with exactly two decimals so that it is never rounded by binary floating point.",
 ...
-        "required": ["index", "allowed", "rule_line", "rule_quote", "reason"],
+        "required": ["index", "allowed", "rule_number", "rule_quote", "reason"],
         "properties": {
           "index": {"type": "integer", "minimum": 0},
           "allowed": {"type": "string", "pattern": "^[0-9]+\\.[0-9]{2}$"},
-          "rule_line": {"type": "integer", "minimum": 1},
+          "rule_number": {"type": "integer", "minimum": 1},
           "rule_quote": {"type": "string", "minLength": 10},
           "reason": {"type": "string", "minLength": 1}
```
It uses only keywords the frozen validator supports (`docassist/schema.py:16-20`). This was verified in memory on 2026-11-09: a correct v2 answer validates, and a v1-shaped answer is rejected with "missing required field 'rule_number'" and "unexpected field 'rule_line'".

### 5.2 New file `docassist/interface_v2.py`
```python
"""Interface v2 (P10 candidate): the model cites policy rules by rule number.

The evaluator (checks.py) is frozen and reads rule_line. This module derives the
v1 view that the checks read, using ONLY the rule number and the policy text the
harness loaded, never the model's quote or reason, so it cannot repair a wrong
citation.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

RULE_LINE = re.compile(r"^(\d+)\.\s+(.*\S)\s*$")      # "3. Hotel nights ..." -> (3, "Hotel nights ...")


def split_rules(lines: list[list[Any]]) -> dict[str, list[Any]]:
    """Model-facing view: rules keyed by rule number, other non-blank lines as text. No line numbers."""
    rules, other = [], []
    for _, line in lines:
        match = RULE_LINE.match(line)
        if match:
            rules.append({"rule_number": int(match.group(1)), "text": match.group(2)})
        elif line.strip():
            other.append(line)
    return {"text": other, "rules": rules}


def rule_index(source_lines: dict[int, str]) -> dict[int, int]:
    """Rule number -> line number of the line that starts with 'N. '. First occurrence wins."""
    index: dict[int, int] = {}
    for line_no in sorted(source_lines):
        match = RULE_LINE.match(source_lines[line_no])
        if match:
            index.setdefault(int(match.group(1)), line_no)
    return index


def harness_lines(data_dir: Path, result: dict[str, Any]) -> dict[int, str] | None:
    """The harness reads the file the model was shown; None if its bytes differ from what the tool hashed."""
    raw = (data_dir / result["name"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != result["sha256"]:
        return None
    return {i: line for i, line in enumerate(raw.decode("utf-8").splitlines(), start=1)}


def to_v1_view(answer: dict[str, Any], index: dict[int, int]) -> dict[str, Any]:
    """A NEW answer dict with rule_line derived from rule_number (0 = no such rule). Input is not modified."""
    items = [{"index": i["index"], "allowed": i["allowed"],
              "rule_line": index.get(i["rule_number"], 0),
              "rule_quote": i["rule_quote"], "reason": i["reason"]} for i in answer["items"]]
    return {**{k: v for k, v in answer.items() if k != "items"}, "items": items}
```
On `policy.md`, `rule_index` gives `{1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10}` (probed read-only 2026-11-09). `to_v1_view` is called only on a schema-valid v2 answer, so its keys exist. Line numbering in `harness_lines` matches `tools.py:83` exactly.

### 5.3 `docassist/tools.py`
```diff
 ANSWER_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "answer.schema.json"
+ANSWER_SCHEMA_V2_PATH = ANSWER_SCHEMA_PATH.with_name("answer_v2.schema.json")
+INTERFACES = ("v1", "v2")
 # TOOL_CONTRACTS: unchanged (lines 22-52)
+# --8<-- [start:contracts_v2]
+TOOL_CONTRACTS_V2: dict[str, dict[str, Any]] = {
+    **TOOL_CONTRACTS,
+    "read_document": {
+        **TOOL_CONTRACTS["read_document"],
+        "description": "Return one document from the data folder as its numbered rules "
+                       "(each with its rule_number and text) and its other text.",
+        "output": "{ok: true, name, sha256, text: [line, ...], rules: [{rule_number, text}, ...]} "
+                  "or {ok: false, error}",
+    },
+    "submit_answer": {**TOOL_CONTRACTS["submit_answer"],
+                      "input_schema": "schemas/answer_v2.schema.json"},
+}
+# --8<-- [end:contracts_v2]
+
+
+def contracts(interface: str) -> dict[str, dict[str, Any]]:
+    if interface not in INTERFACES:
+        raise ValueError(f"unknown interface {interface!r}")
+    return TOOL_CONTRACTS if interface == "v1" else TOOL_CONTRACTS_V2

 class ToolBox:
-    def __init__(self, data_dir: Path) -> None:
+    def __init__(self, data_dir: Path, interface: str = "v1") -> None:
         self.data_dir = data_dir.resolve()
+        self.interface = interface
+        self.contracts = contracts(interface)
         self.calls: list[dict[str, Any]] = []

     def call(self, name, tool_input):
-        if name not in TOOL_CONTRACTS or name == "submit_answer":
+        if name not in self.contracts or name == "submit_answer":
 ...
-            problems = validate(tool_input, TOOL_CONTRACTS[name]["input_schema"])
+            problems = validate(tool_input, self.contracts[name]["input_schema"])

     def _read_document(self, tool_input):
         ...
         lines = [[i, line] for i, line in enumerate(text.splitlines(), start=1)]
+        if self.interface == "v2":
+            return {"ok": True, "name": path.name,
+                    "sha256": hashlib.sha256(raw).hexdigest(), **split_rules(lines)}
         return {"ok": True, "name": path.name,
                 "sha256": hashlib.sha256(raw).hexdigest(), "lines": lines}
```
plus `from .interface_v2 import split_rules`. Both tables have the same tool names and the same `read_document` and `calculate` input schemas, so the allowlist and its security behaviour are identical across arms.

### 5.4 `docassist/workflow.py`
```diff
-from .tools import ANSWER_SCHEMA_PATH, TOOL_CONTRACTS, ToolBox
+from . import interface_v2
+from .tools import ANSWER_SCHEMA_PATH, ANSWER_SCHEMA_V2_PATH, TOOL_CONTRACTS, ToolBox, contracts
 SYSTEM_PROMPT = """..."""            # unchanged, lines 23-29
+SYSTEM_PROMPT_V2 = SYSTEM_PROMPT.replace(
+    "policy line number you relied on, and an exact quote of that line. Submit the\nresult once",
+    "number of the policy rule you relied on, and an exact quote of that rule's\ntext. Submit the result once")
+PROMPTS = {"v1": SYSTEM_PROMPT, "v2": SYSTEM_PROMPT_V2}

-def load_answer_schema() -> dict[str, Any]:
-    return json.loads(ANSWER_SCHEMA_PATH.read_text(encoding="utf-8"))
+def load_answer_schema(interface: str = "v1") -> dict[str, Any]:
+    path = ANSWER_SCHEMA_PATH if interface == "v1" else ANSWER_SCHEMA_V2_PATH
+    return json.loads(path.read_text(encoding="utf-8"))

-def tool_definitions() -> list[dict[str, Any]]:
+def tool_definitions(interface: str = "v1") -> list[dict[str, Any]]:
-    for name, contract in TOOL_CONTRACTS.items():
-        schema = load_answer_schema() if name == "submit_answer" else contract["input_schema"]
+    for name, contract in contracts(interface).items():
+        schema = load_answer_schema(interface) if name == "submit_answer" else contract["input_schema"]

 def run(model, claim, policy_name, data_dir, max_turns=MAX_TURNS, recorder=None,
-        crash_after_tools=None, replay_events=None):
+        crash_after_tools=None, replay_events=None, interface: str = "v1"):
-    toolbox = ToolBox(data_dir)
+    toolbox = ToolBox(data_dir, interface)
-        turn = driver.first(SYSTEM_PROMPT, build_task(claim, policy_name), tool_definitions())
+        turn = driver.first(PROMPTS[interface], build_task(claim, policy_name), tool_definitions(interface))
 ...                                                    # lines 156-161
             if turn.name == "read_document" and turn.input.get("name") == policy_name:
                 if result["ok"]:
-                    source_lines = {n: text for n, text in result["lines"]}
-                    report["source"] = {"name": result["name"], "sha256": result["sha256"]}
+                    source_lines = ({n: text for n, text in result["lines"]} if interface == "v1"
+                                    else interface_v2.harness_lines(toolbox.data_dir, result))
+                    if source_lines is None:
+                        report["reasons"].append("policy file differs from the document the model read")
+                    else:
+                        report["source"] = {"name": result["name"], "sha256": result["sha256"]}
 ...
-    return _verdict(report, claim, source_lines)
+    if interface != "v1":
+        report["interface"] = interface
+    return _verdict(report, claim, source_lines, interface)

-def _verdict(report, claim, source_lines):
+def _verdict(report, claim, source_lines, interface: str = "v1"):
 ...
-        report["schema_errors"] = validate(answer, load_answer_schema())
+        report["schema_errors"] = validate(answer, load_answer_schema(interface))
         if not report["schema_errors"]:
-            report["checks"] = [c.__dict__ for c in checks.run_all(answer, claim, source_lines)]
+            checked = answer
+            if interface == "v2":    # frozen checks read rule_line: derive it from rule_number only
+                checked = interface_v2.to_v1_view(answer, interface_v2.rule_index(source_lines or {}))
+                report["answer_v1_view"] = checked
+            report["checks"] = [c.__dict__ for c in checks.run_all(checked, claim, source_lines)]
 # evaluate(): byte-for-byte unchanged (frozen, section 4)
```
`report["answer"]` stays the model's raw submission in both arms. `evaluate()` reads only `decision`, `total_allowed` and `items[].index/allowed` (`workflow.py:211-221`), which both schemas share, so labels are compared identically in both arms (verified in memory: a correct v2 answer matches the `normal` label).

### 5.5 `docassist/runner.py`
```diff
 def start(model, claim_name, policy_name, runs_dir, *, label, case_meta=None,
-          crash_after_tools=None, crash_at_publish=False):
+          crash_after_tools=None, crash_at_publish=False, interface: str = "v1"):
     recorder.emit("run_start", ..., environment=environment(),
+                  **({"interface": interface} if interface != "v1" else {}))
-    return _execute(..., crash_after_tools, crash_at_publish, replay=None)
+    return _execute(..., crash_after_tools, crash_at_publish, replay=None, interface=interface)

 def resume(model, run_dir):
-    return _execute(..., None, False, replay=events)
+    return _execute(..., None, False, replay=events, interface=start_event.get("interface", "v1"))

-def _execute(..., crash_at_publish, replay):
+def _execute(..., crash_at_publish, replay, interface: str = "v1"):
-    verdict = workflow.run(..., replay_events=replay)
+    verdict = workflow.run(..., replay_events=replay, interface=interface)
     recorder.emit("verdict", ..., replayed_steps=verdict["replayed_steps"],
+                  **({"interface": interface, "answer_v1_view": verdict.get("answer_v1_view")}
+                     if interface != "v1" else {}))
```
v1 run records keep exactly the fields they have today. `_publish` and `decision_fingerprint` (`runner.py:116-146`) read only fields that both schemas share, so they are unchanged.

### 5.6 `docassist/report.py` (one line)
```diff
-    answer = verdict.get("answer") if not verdict.get("schema_errors") else None
+    answer = (verdict.get("answer_v1_view") or verdict.get("answer")) if not verdict.get("schema_errors") else None
```
For v2, the "Policy line" column shows the line the harness derived (`report.py:34`). The total line that the checker's K6 matches (`report.py:35`) is the same in both arms.

### 5.7 `run.py`
```diff
     parser.add_argument("--temperature", type=float, default=0.0, help="Ollama temperature")
+    parser.add_argument("--interface", choices=["v1", "v2"], default="v1",
+                        help="model-facing interface for live runs (P10); constructed cases are v1")
     args = parser.parse_args(argv)
+    if args.interface != "v1" and (args.case or args.all or args.resume):
+        print("ERROR: --interface applies to live runs; a resume reads it from the run record",
+              file=sys.stderr)
+        return 64
 ...
             result = runner.start(_live_model(args), args.claim, args.policy, args.runs_dir,
-                                  label="live", case_meta={"constructed": False}, **crash)
+                                  label="live" if args.interface == "v1" else "live-v2",
+                                  case_meta={"constructed": False}, interface=args.interface, **crash)
```

### 5.8 Not changed
`checker.py`, `docassist/checks.py`, `docassist/schema.py`, `docassist/models.py`, `docassist/runlog.py`, `task_contract.json`, `fixtures/make_cases.py`, `fixtures/cases/*`, `live_trials.py`, `evidence.py`, `tests/test_docassist.py`.

**Known, accepted consequence.** The frozen checker cannot accept a *passed* v2 run. Its K5 reads `item["rule_line"]` from the recorded answer (`checker.py:134`). A raw v2 answer has no such field, so K5 reports "answer unreadable" (`checker.py:141`) and the run is rejected. Recording the derived view as the answer instead would trip K4, which requires the verdict answer to equal the submission (`checker.py:106-108`). In P10, checker decisions are therefore *descriptive only*. If v2 is promoted, follow-up F-1 (a v2-aware K5 with its own tests and review) is a precondition for making v2 the default (section 10.4).

**Side effect on older evidence.** Adding `interface_v2.py` and `answer_v2.schema.json` changes the code-tree hash (`runner.py:29-31`, `checker.py:29`). Re-checking older run records would now report K3 "code or contract changed", as already happens after the loop fix (`E01_instrumented_workflow.md:239`). Regenerating `reviews/evidence/ref01/` is a separate step after P10, not part of it.

### 5.9 New experiment tooling (outside the hashed code tree)
- `experiments/p10_trials.py`, the driver. `live_trials.py` is not used: it would overwrite `reviews/evidence/ref01_live/` (`live_trials.py:100-102`), and it hard-codes the DEV claims (`live_trials.py:30`).
  - `--phase dev|heldout [--candidate-tag v2|v2.1]` runs the cells of section 8 in the fixed order. Each cell runs in its own runs directory, `experiments/P10_runs/<phase>/<arm>/<claim-stem>/seed<s>/`, so that ledgers never interact. For each cell the driver runs `python run.py --ollama qwen2.5:7b --claim <c> --seed <s> --temperature 0.7 --interface <arm> --runs-dir <dir>` with `HANDBOOK_MAIN_GPU=1`, then `python checker.py <run_dir>`, then `evaluate(verdict, label)` against `P10_labels.json`. It appends one row to `experiments/P10_runs/<phase>/rows.jsonl`.
  - Resumable: a cell whose directory already holds a run with a `run_end` event is skipped. An interrupted cell is restarted in a new run directory, and the incomplete one is kept and listed.
  - Preflight, which ends the run with exit 64 on any failure:
    - frozen hashes equal `p10_freeze.json`;
    - v1 goldens equal section 3.1;
    - `python -m unittest discover -s tests` passes;
    - the DEV labels in `P10_labels.json` equal the fixture labels;
    - `bench_hold.flag` is absent (as in `live_trials.py:31, 61-63`);
    - `ollama show` reports the qwen2.5:7b digest prefix `845dbda0ea48` (`LIVE.md:12`);
    - for `heldout` only: `p10_freeze.json` holds a `candidate` block whose `code_sha256` equals the current `sha256_tree(runner.code_files())`.
  - Per-run assertion, recorded in the row: `run_start.model.options` has `temperature 0.7`, `seed s`, `num_ctx 8192` and `main_gpu 1` (`docassist/models.py:114, 120-125, 131-132`).
  - `--analyse` computes every metric in section 9 and applies the decision rule in section 10 **by code**. It writes `experiments/P10_RESULTS.json` and `.md` and prints PROMOTE, NOT PROMOTED, NOT PROMOTED (DEV GATE), VOID or INCOMPLETE.
- `experiments/p10_freeze.json`: hashes of the frozen files, the held-out claims, the labels, this protocol and the driver, plus the v1 goldens. A `candidate` block (tag, code_sha256, UTC time) is added at freeze F6.

## 6. Tests required before any live run (`tests/test_interface_v2.py`, new)

| ID | Test |
|---|---|
| T1 | The v1 goldens equal section 3.1: tool definitions, `SYSTEM_PROMPT`, `read_document` output and `evaluate` source. |
| T2 | `ToolBox(data, "v2")._read_document("policy.md")` has no `lines` key. Its `rules` are numbered 1..6 with the texts of `policy.md:5-10` minus the "N. " prefix. `text` holds the 3 header lines. `sha256` equals the v1 hash. |
| T3 | `rule_index` on `policy.md` gives `{1:5, 2:6, 3:7, 4:8, 5:9, 6:10}`. For every rule, `checks.quote_matches(rule.text, line)` is true. |
| T4 | The adapter cannot launder errors. Correct number and correct quote pass C3. Number 3 with rule 1's quote fails C3. Number 7 (rule 3's *line* number) with the hotel quote fails C3. Number 0 or 9 fails C3. `to_v1_view` does not modify its input. |
| T5 | `SYSTEM_PROMPT_V2` differs from `SYSTEM_PROMPT` and contains "number of the policy rule". With that sentence swapped back, it equals v1. |
| T6 | A constructed v2 fixture (correct normal answer with rule numbers 1, 2, 2, 3) run through `workflow.run(..., interface="v2")` reaches `passed` and matches `LABEL_NORMAL`. A v2 run submitting a v1-shaped answer fails with a schema violation. |
| T7 | `runner.start(..., interface="v2")` with a crash after 1 tool call, then `resume`, replays with the v2 interface (read from `run_start`) and executes no tool twice. |
| T8 | Characterisation of the known gap: a passed v2 run is rejected by the frozen checker at K5 and nowhere else. If this test ever fails, the protocol is re-read before any run. |
| T9 | The existing `tests/test_docassist.py` passes unedited, and `python run.py --all` reports AS EXPECTED for all 9 cases. |

A reviewer agent reviews the v2 diff and the driver before F4. A BLOCK verdict stops the experiment until it is resolved.

## 7. Claims and labels

### 7.1 DEV claims (used for development and the dev gate only)
- `data/claim_normal.json` (RCL-2026-014) and `data/claim_injection.json` (RCL-2026-015), with their frozen fixture labels (`fixtures/make_cases.py:40-41, 54-55`).
- These are the claims on which the failure was discovered. Any result on them is development evidence, not a held-out result.

### 7.2 HELD-OUT claims (new, written 2026-11-09 before any P10 run)
No model is run on these claims before freeze F6. Together they cover every policy rule, three of the four decision values, a late submission under rule 4, a rule 6 referral and the "exceeds 6 hours" boundary.

| File | Claim | Rules exercised | Decision | Claimed | Allowed |
|---|---|---|---|---|---|
| `claim_heldout_1.json` | RCL-2026-021 | 1 (exact rate), 2 (under cap, over cap, exactly 6 h), 3 (2 nights under cap), 4 (met, 12 days), 5 (wine) | partially_approved | 309.10 | 279.20 |
| `claim_heldout_2.json` | RCL-2026-022 | 1 (claimed at 0.35/km), 2 (under cap), 3 (no receipt; over cap), 4 (met, 10 days), 6 (rail ticket) | refer_to_treasurer | 259.25 | 128.95 |
| `claim_heldout_3.json` | RCL-2026-023 | 4 (late: 41 days) over items that would otherwise be allowed under 1, 2 and 3 | rejected | 154.00 | 0.00 |

### 7.3 Label conventions (`P10_labels.json` → `conventions`)
- C-1 Mileage: min(claimed, km × 0.30).
- C-2 Meals: min(claimed, 25.00) if travel_hours > 6, else 0.00. Exactly 6 h does not exceed 6.
- C-3 Hotel: min(claimed, 90.00 × nights) if a receipt is attached, else 0.00. This is the same reading as the frozen dev label for the 5-hour meal (`make_cases.py:33-34`).
- C-4 Late claim (more than 30 days after `trip_last_day`): every item 0.00, decision `rejected`. Rule 4 takes precedence over the item rules.
- C-5 Alcohol: 0.00.
- C-6 Referral: an item that fits none of rules 1–5 gets 0.00 and the claim decision is `refer_to_treasurer`. The other items are assessed normally. Basis: `A01_goal_to_verifiable_result.md:85, 182` and `E01_instrumented_workflow.md:103`.
- C-7 Without a referral: approved / rejected / partially_approved by the same rule as C6 (`checks.py:84-95`).

C-4 and C-6 are interpretations that the policy text does not fully settle. They are flagged for the owner (section 15, Q2–Q3) and must be confirmed before F1, never after a run.

### 7.4 Hand working (identical to `P10_labels.json`)

**claim_heldout_1.json** (submitted 2026-10-26; last trip day 2026-10-14; 12 days, so rule 4 is met)

| Item | Claimed | Working | Allowed | Rule |
|---|---|---|---|---|
| 0 mileage 186 km | 55.80 | 186 × 0.30 = 55.80; min(55.80, 55.80) | 55.80 | 1 |
| 1 meal, 7.5 h | 22.40 | 7.5 > 6; min(22.40, 25.00) | 22.40 | 2 |
| 2 meal, 10 h | 29.90 | 10 > 6; min(29.90, 25.00) | 25.00 | 2 |
| 3 meal, 6 h | 14.00 | 6 does not exceed 6 | 0.00 | 2 |
| 4 hotel, 2 nights, receipt | 176.00 | cap 2 × 90.00 = 180.00; min(176.00, 180.00) | 176.00 | 3 |
| 5 wine | 11.00 | alcohol | 0.00 | 5 |

Total allowed 55.80 + 22.40 + 25.00 + 0.00 + 176.00 + 0.00 = **279.20** of 309.10 claimed. The decision is **partially_approved**.

**claim_heldout_2.json** (submitted 2026-11-02; last trip day 2026-10-23; 10 days, so rule 4 is met)

| Item | Claimed | Working | Allowed | Rule |
|---|---|---|---|---|
| 0 mileage 64 km | 22.40 (= 64 × 0.35) | 64 × 0.30 = 19.20; min(22.40, 19.20) | 19.20 | 1 |
| 1 rail ticket | 38.60 | fits none of rules 1–5; referred | 0.00 | 6 |
| 2 hotel, 1 night, no receipt | 82.00 | no receipt attached | 0.00 | 3 |
| 3 hotel, 1 night, receipt | 96.50 | cap 90.00; min(96.50, 90.00) | 90.00 | 3 |
| 4 meal, 11 h | 19.75 | 11 > 6; min(19.75, 25.00) | 19.75 | 2 |

Total allowed 19.20 + 0.00 + 0.00 + 90.00 + 19.75 = **128.95** of 259.25 claimed. The decision is **refer_to_treasurer** (item 1).

**claim_heldout_3.json** (submitted 2026-10-19; last trip day 2026-09-08; 41 days, more than 30, so rule 4 is not met)

| Item | Claimed | If on time | Allowed | Rule |
|---|---|---|---|---|
| 0 mileage 150 km | 45.00 | 150 × 0.30 = 45.00 | 0.00 | 4 |
| 1 meal, 8 h | 21.00 | 21.00 | 0.00 | 4 |
| 2 hotel, 1 night, receipt | 88.00 | 88.00 | 0.00 | 4 |

Total allowed **0.00** of 154.00 claimed. The decision is **rejected**. A model that ignores rule 4 would approve 154.00, which makes this claim a clean discriminator.

**Independent verification (2026-11-09, in memory, nothing written).** A rule engine of about 20 lines, written separately from these tables, reproduced every per-item amount, total and decision, and every day count (12, 10, 41). For each claim, a label-shaped v1 answer passed all five frozen checks C2–C6 and matched its label under `evaluate()`, so every label is attainable under the frozen evaluator.

## 8. Trial plan

| Setting | Value | Source |
|---|---|---|
| Model | qwen2.5:7b via Ollama, digest prefix `845dbda0ea48` | `LIVE.md:12` |
| Temperature | 0.7 | `LIVE.md:5` |
| Seeds | 1, 2, 3, 4, 5 (same seeds in both arms) | |
| Context | `num_ctx` 8192 (adapter default) | `models.py:114` |
| GPU | `HANDBOOK_MAIN_GPU=1` → `options.main_gpu = 1` | `models.py:123-125`; `DECISIONS.md` D-10 |
| Turn budget | 8; model call timeout 300 s (contract, frozen) | `task_contract.json:16` |
| Arms | v1, v2 (`--interface`) | section 5.7 |

**Cells.**
- DEV phase: 2 claims × 5 seeds × 2 arms = 20 runs.
- Optional revision (only if the dev gate fails, at most once): v2.1 × 2 claims × 5 seeds = 10 runs. v1 is not rerun.
- HELD-OUT phase: 3 claims × 5 seeds × 2 arms = 30 runs.
- Maximum: 60 scored runs.

**Order (fixed now, to spread drift and thermal effects across arms).** Iterate seed 1→5, and within each seed the claims in the order listed (DEV: normal, injection; HELD-OUT: heldout_1, _2, _3). Number the (seed, claim) pairs k = 0, 1, 2, ... in that order. For even k run v1 then v2; for odd k run v2 then v1.
- DEV begins: (s1, normal) v1, v2; (s1, injection) v2, v1; (s2, normal) v1, v2.
- HELD-OUT begins: (s1, H1) v1, v2; (s1, H2) v2, v1; (s1, H3) v1, v2; (s2, H1) v2, v1.

**Blocked runs.** A run with status `blocked` from a model-service error (`ModelError`, `workflow.py:166-168`) is an infrastructure error, not an outcome. It is retried with the same seed up to 2 times, with a global cap of 6 retries. If a cell is still blocked after its retries, it is reported as blocked and counted as **not** a correct deliverable for its arm. More than 2 such cells in one arm makes the phase VOID (section 10).

**Windows (`CLAUDE.md:10` of this project; `DECISIONS.md` D-10).** Each window is announced to orchestrator session 69 with START and END lines, starts with `ollama ps`, uses one consumer, stops if GPU 0 reaches 87 °C or more, and ends with `ollama stop qwen2.5:7b`.
- Window 1: DEV, about 20 minutes.
- Window 2: the v2.1 dev re-run if needed, then HELD-OUT, about 35 minutes.

If a thermal stop or the time cap interrupts a phase, the remaining cells run in a later window with identical settings, and the split is reported.

## 9. Metrics

All metrics are computed by `p10_trials.py --analyse` from the run records alone (`events.jsonl`, `run.json`), never from narrative.

**Primary (decides H1).** **P** = held-out correct deliverables per arm: the number of the 15 held-out runs with verdict status `passed` **and** `evaluate(...).matches_label == true`. A failed run's answer is never published (`runner.py:119-121`), so a label match on a failed run is not a deliverable. The raw label match is reported as S1. This sharpens the "label match rate" of the P10 card; it is confirmed by the owner as Q1 before F1.

**Secondary (reported, not decisive except where section 10 names them).**

| ID | Metric |
|---|---|
| S1 | Raw label match: runs with `matches_label` true regardless of status (what `live_trials.py:86` reports) |
| S2 | Runner pass rate: runs with status `passed` |
| S3 | C3 failures: runs with at least one C3 failure; items failing C3; and items by sub-category (below) |
| S4 | C6 failures (decision inconsistent with amounts) and the other check ids C2, C4, C5 |
| S5 | Tokens: per-run sums of `prompt_eval_count` and `eval_count` from `run_end.usage.totals` (`runner.py:149-165`); median and total per arm and phase; never estimated when unreported |
| S6 | Wall time: `run_end.resources.wall_s` per run (median, total) and driver-measured process wall including start-up; total window time |
| S7 | Model calls per run (`run_end.usage.model_calls`) |
| S8 | Rule-citation accuracy per item, against `expected_rules`. Cited rule for v1 = the rule whose line is `rule_line` (none if that line holds no rule); for v2 = `rule_number`. Over items of schema-valid answers. |
| S9 | Checker decision per run, descriptive only (section 5.8) |
| S10 | All of the above on DEV, labelled development evidence |

**Failure categories (per run, from the verdict record).**
- `schema_violation`: `schema_errors` is non-empty.
- `C2_coverage`, `C3_quotes_in_source`, `C4_not_above_claimed`, `C5_total_is_sum`, `C6_decision_consistent`: failed check ids.
- `budget_exhausted`: the reason contains "step budget of".
- `text_reply`: the model replied with text instead of submit_answer.
- `no_answer`: no answer was submitted.
- `security_event`: `security_events` is non-empty.
- `source_not_loaded`: blocked, policy not loaded.
- `model_error`: blocked by `ModelError`.
- `harness_exception`: no run directory, or a `run.py` exit status outside {0, 1, 2, 5}.

**C3 sub-categories (diagnostic).** For each C3-failing item, let F be the set of policy lines on which `checks.quote_matches(quote, line)` holds; the frozen function is used read-only.
- `quote_not_in_policy`: F is empty.
- v1, `rule_as_line`: the cited `rule_line` is a rule number n, and rule n's line is in F.
- v2, `line_as_rule`: the cited `rule_number` is not a rule, and it equals a line number in F (for example 7 for the hotel).
- v2, `unknown_rule_number`: the cited number is not a rule and not explained by `line_as_rule`.
- `wrong_rule`: any other case.

**Information only.** A one-sided Fisher exact p for P (2 × 2, 15 vs 15) is reported, plus a per-claim table with 5 runs per arm. With n = 15 per arm, and runs clustered by claim, neither is a significance claim. Seeds do not pair runs across arms, because different prompts change the sampling path.

## 10. Decision rule (written before any run; applied by code)

### 10.1 Dev gate (after DEV, before any held-out run)
- G1: zero `harness_exception` in v2.
- G2: v2 runs with a schema-valid answer ≥ v1's minus 1 (of 10).
- G3: v2 runs with at least one C3 failure ≤ v1's.

If any gate fails, **one** revision (v2.1) is allowed. It may touch only the v2 files and the v2 branches of section 5, never the frozen files or the v1 path, and the reason is recorded. v2.1 is then rerun on DEV (10 runs). If the gate still fails, the outcome is **NOT PROMOTED (DEV GATE)**, and the held-out claims stay unused and clean for a later candidate. A revision is not allowed when the gate passes. The candidate taken to held-out is the latest revision; no candidate is chosen by score.

### 10.2 Promotion (held-out)
Let P(v1) and P(v2) be the primary counts out of 15, and d_arm(c) the count for held-out claim c out of 5. **PROMOTE if and only if all four hold:**
- R1 (superiority): P(v2) − P(v1) ≥ **3**.
- R2 (no claim regression): for every held-out claim c, d_v2(c) ≥ d_v1(c) − 1.
- R3 (no new failure category):
  - no category occurs in 2 or more runs of the final v2 candidate (DEV runs of that candidate plus held-out) while occurring in zero v1 runs (DEV plus held-out);
  - zero `security_event` in v2;
  - zero `harness_exception` in v2.
- R4 (integrity):
  - every phase passed preflight;
  - every held-out run is bound to the frozen candidate `code_sha256`;
  - every planned cell has a recorded outcome;
  - no more than 2 blocked-after-retry cells per arm.

### 10.3 Other outcomes
- **NOT PROMOTED (null).** R1 fails while R2–R4 hold. If, in addition, held-out runs with a C3 failure satisfy v2 ≤ v1 − 5 and v1 ≥ 5, the result is reported as **mechanism confirmed, not promoted**: the interface removes the rule/line confusion, but that is not enough to change deliverables, most likely because of C6.
- **NOT PROMOTED (harmful).** P(v2) < P(v1) − 2, or R2 or R3 fails.
- **VOID.** R4 fails. No conclusion is drawn. A hash mismatch discards the phase; it is rerun after the frozen files are restored, and the discarded results are reported but not used. Missing or blocked cells are rerun in a new window with identical settings.
- **INCOMPLETE.** The budget cap stopped the run; the remaining cells finish in the next window.

### 10.4 What "PROMOTE" means
PROMOTE approves v2 for adoption. Making it the default (`--interface` default `v2`, E1 text and contract update) requires follow-up **F-1**, a v2-aware K5 in `checker.py` with tests and review, because the frozen checker cannot accept passed v2 runs (section 5.8). F-1 is a separate, reviewed change after P10.

## 11. Budget

| Resource | Cap | Expected |
|---|---|---|
| Scored live runs | 60 (20 dev + 10 revision + 30 held-out) | 50 |
| Blocked-run retries | 6 in total, 2 per cell | 0 |
| GPU wall time (all windows) | **60 min** (default budget, `project_backlog.md:3`); the driver stops at the cap and reports INCOMPLETE | about 35–45 min, from 7.4–22.7 s per live run (`LIVE.md:17-26`) plus process start-up and checker; held-out claims have more items |
| Tokens | none (local); all reported | 4,000–15,000 prompt tokens per run (`LIVE.md:17-26`: 4,037–11,472) |
| Paid spend | 0: no hosted route in P10 | 0 |
| Search budget (candidate revisions) | 1 (section 10.1) | 0 |
| Electricity and hardware cost | not measured, reported as not measured | |

## 12. Threats to validity and limitations
- One model, one runtime, one synthetic policy, five synthetic claims, 15 held-out runs per arm. Results describe qwen2.5:7b on these claims, not model reliability in general (`live_trials.py:8-9`).
- The bundle confound: tool output, schema field and prompt sentence change together (section 3.2).
- The same author wrote the held-out claims, the labels and the v2 specification, after seeing the v1 failures. Mitigations: the labels were written and machine-checked before any P10 run, with conventions declared; the rule-as-line error can affect every rule (rule n sits on line n + 4, `policy.md:5-10`), so the claims are not tilted toward particular rules.
- The labels depend on conventions C-4 and C-6. A treasurer could read rule 4 or rule 6 differently, so an absolute match rate on heldout_2 and heldout_3 carries that interpretation. The comparison between arms is fair because neither prompt states the conventions.
- No held-out claim has the label `approved`. The live model's C6 bias was toward `approved` (6 of 6 C6 failures), which lowers P for both arms alike.
- Held-out claims have 3–6 items, so the frozen 8-turn budget may run out more often than on DEV, in both arms.
- Sampling at temperature 0.7 with seeds is not guaranteed to be deterministic across GPUs. `main_gpu` changes from the earlier live run (which recorded no GPU index), so the v1 arm is re-measured inside P10 and never compared with `LIVE.md`.
- The checker's independence is limited (`E01_instrumented_workflow.md:273`), and in P10 it is descriptive only.

## 13. Procedure and lineage

| Step | Action | Evidence |
|---|---|---|
| F0 | The owner answers section 15; answers are recorded in `DECISIONS.md` | decision IDs |
| F1 | Freeze 1: write the 3 held-out claims, `P10_labels.json` and this protocol; record hashes in `experiments/p10_freeze.json`; git commit "P10 pre-registration" (parent `8b9159c`) | commit hash, freeze manifest |
| F2 | Implement section 5 and the driver; tests T1–T9 pass; `git diff --stat` touches no frozen path; reviewer agent review, BLOCK honoured | test log, review file |
| F3 | Commit "P10 v2 interface"; record the code-tree hash | commit hash |
| F4 | Window 1: DEV phase (20 cells) | `P10_runs/dev/rows.jsonl` |
| F5 | Dev gate; if it fails, one revision v2.1 (commit, review) and a DEV re-run of v2.1 (10 cells) | gate output, revision note |
| F6 | Freeze 2: add the `candidate` block (tag, code_sha256, UTC time) to `p10_freeze.json`; commit | commit hash |
| F7 | Window 2: HELD-OUT phase (30 cells) | `P10_runs/heldout/rows.jsonl` |
| F8 | `p10_trials.py --analyse` produces the decision by code | `P10_RESULTS.json/.md` |
| F9 | Report: E1 paragraph and the P10 card updated with the outcome and lineage (v1 tree hash, candidate tree hash, revisions, costs); STATUS entry | chapter diff |

Deviations from this protocol are allowed only as a new protocol version (1.1) written before the affected runs, with reasons. Both versions are reported.

## 14. Next candidate, if the prediction holds
C6 is the larger failure (6 of 10 live runs). Under the frozen C6 rule (`checks.py:84-95`), the decision label is fully determined by the amounts unless an item is referred. A P10b candidate could therefore ask the model only for "any item referred under rule 6: yes/no" and let code derive the label. That would be the same poka-yoke idea applied to C6. It would need its own pre-registration and **fresh** held-out claims: once P10 has been analysed, its held-out claims become development data.

## 15. Questions for the owner (answer before F1; each has a recommendation)
1. **Primary metric.** Count only `passed` and label-matching runs (P), and report raw label match as S1? *Recommendation: yes.* A failed run is never published, and the interface change acts through C3, which raw label match cannot see.
2. **Rule 6 label convention C-6.** A referred item gets 0.00 and the decision `refer_to_treasurer`. *Recommendation: keep.* The alternative (the referred amount allowed while pending) would let the assistant approve money that the policy reserves for the treasurer.
3. **Rule 4 label convention C-4.** A late claim is `rejected`, with every item 0.00. *Recommendation: keep.* A late claim fits rule 4, so it is not a rule 6 case.
4. **Checker gap.** Accept that the frozen checker rejects passed v2 runs (K5), so checker results are descriptive in P10 and follow-up F-1 is required before v2 becomes the default? *Recommendation: accept.* Editing the checker inside P10 would break the frozen-evaluator rule.
5. **Promotion threshold.** Keep R1 at +3 of 15, with no promotion on "mechanism confirmed" alone? *Recommendation: keep strict R1.* It guards against adopting a change on the strength of a mechanism story.
6. **STATUS item 1** (re-run of the REF01 live trials). Keep it separate from the P10 v1 arm? *Recommendation: separate.* P10 must not write to `reviews/evidence/ref01_live/`, and `LIVE.md` is generated by its own script.
7. **GPU windows.** Request two windows from session 69 (about 20 and about 35 minutes, `main_gpu: 1`). *Recommendation: yes, booked after F3.*
