# P10 protocol addendum 1.1: hash update after pre-run triage fixes

| Field | Value |
|---|---|
| Addendum to | `experiments/P10_PREREGISTRATION.md` version 1.0 (unchanged; this file does not replace it) |
| Date | 2026-11-09 |
| State | **No P10 run has happened.** No live trial, DEV or held-out, exists under any interface. The only P10 executions so far are dry runs with a scripted model, written to temporary folders outside the project. |
| Reason | The F2 code review (verdict GO-WITH-FIXES) found that the section 4 hashes no longer match the files on disk. The managing editor applied triage fixes to the evaluator and harness before any run. |

## 1. Changed files

"Old" is the section 4 value. For the two files that section 4 does not list, "old" is the hash at commit `8b9159c`, which is the parent named in section 13 (F1). "New" is the sha256 of the file on disk on 2026-11-09, as LF bytes.

| File | In section 4 | Old sha256 | New sha256 | Reason for the change |
|---|---|---|---|---|
| `checker.py` | yes | `74337a44fd779f0be41cb95570ff259013c955678a30008abb38d7add21ed0bf` | `5f31e451b903fdd270bbe14491914eb2289936a4a818f364fc0ff0fb7c2b4903` | Robust JSON parse (an unreadable record is K2, not a crash); "no verdict event" is a K2 problem; K5 checks that the answer's claim id equals the claim's; a usage error exits 64 |
| `docassist/schema.py` | yes | `9773a8558552dd220d32235268802fbb473df71d771b96da6b48e2baec9d8d8b` | `36a686aa92508ab52e3e7efbe07e4244b5eea1201943ce2aef23cd5dab0b1807` | `pattern` is now matched with `re.fullmatch` instead of `re.search` |
| `task_contract.json` | yes | `f114d4e6cac11361bef8700a961d01978235ce6e82873a60deff48302848e495` | `7978d2752dd669b5979ab423b13955e64471e7b406b1f5cd1cb940b7830e0e09` | AC5 `checked_by` corrected from K4 to K5; budgets are unchanged (8 turns, 300 s) |
| `tests/test_docassist.py` | yes | `4766311ccbdb3c8af1691bd9c8ec2dab8de5e50733ed8d1dee763e73e4e58e7b` | `473815b9c090dd959ec2333b14e675765bc521a5c2058c141c6b74d8fb363afb` | New regression tests (hosted token cap, and tests for the triage fixes). The suite now has 44 tests, and they still must pass unedited |
| `docassist/tools.py` | no (v2 edits it, section 5.3) | `8572f7583baba10a48e4d60533018c7ce85259d2b12469469a98d98992d0f308` | `5b1e39448938dbdc544d2bed59a56f7a6c22072bb5276586bfd1754b56804a52` | `read_document` refuses a case-variant file name (for example `POLICY.md`), plus the section 5.3 v2 edits |
| `run.py` | no | `18f974400dc02c1c6c3658838e1132b65ca4b2ef821de53802bcf459b49d29f2` | `8fb7abf3aba6d9d11ea37bc404d72c725ed34da4b509ab1db266dbfb6d70cda6` | Resume passes the host, `num_ctx` and the contract timeout; a usage error exits 64; plus the section 5.7 `--interface` flag. Now added to the P10 freeze (review item H2) |

`docassist/__init__.py` also changed (a docstring now says chapter E1 instead of chapter 21). It is not in section 4. It changes only the code-tree lineage hash.

## 2. Effect on the comparison

- **Both arms are affected equally.** Every change listed above is in code that the v1 and v2 arms share: the evaluator, the validator, the contract, the tool sandbox and the command line. No change touches anything model-facing in one arm only.
- **The v1 goldens still hold.** The section 3.1 values for tool definitions, `SYSTEM_PROMPT`, the `read_document` output and the `evaluate` source were re-checked after the fixes (test T1 and the driver preflight).
- **The labels, the policy and the claims are unchanged.** So are `docassist/checks.py` (runner checks C2–C6), `fixtures/` and the decision rule of section 10.
- **The code-tree lineage hash changes.** It was `30582607…` in section 3.1. It is lineage only and was never a gate.

## 3. Which hashes are authoritative

The hashes recorded on disk by `python experiments/p10_trials.py --init-freeze` in `experiments/p10_freeze.json` are authoritative. The tables in section 4 and in this addendum are not. That manifest covers the frozen files of section 4, plus `run.py`, this addendum, the driver `experiments/p10_trials.py` and the dry-run stand-in `experiments/p10_fake_run.py`.

Every `--phase` and `--analyse` invocation refuses to run if the manifest is missing or if any recorded hash differs. Results under version 1.0 do not exist, so none are replaced.
