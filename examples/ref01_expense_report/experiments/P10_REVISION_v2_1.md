# P10 candidate revision v2.1 (9 Nov 2026, about 15:36 KST)

**Why:** the dev gate failed on G2 only (schema-valid answers: v2 6 of 10, v1 8 of 10; the gate needs v2 ≥ v1 − 1). G1 (no harness exception) and G3 (C3 failures: v2 0 runs vs v1 6 runs) passed. All four v2 schema violations were the same: items missing the required `reason` field (`reviews/evidence/p10/dev/v2/.../events.jsonl`, verdict `schema_errors`).

**Change (the one revision allowed by section 10.1):** the single v2 prompt sentence now also asks for "a one-line reason":

- v2: "...the number of the policy rule you relied on, and an exact quote of that rule's text. Submit the result once"
- v2.1: "...the number of the policy rule you relied on, an exact quote of that rule's text, and a one-line reason. Submit the result once"

Only `SYSTEM_PROMPT_V2` in `docassist/workflow.py` changed. No frozen file, no v1 path, no evaluator, label or claim changed. The v1 goldens (including the v1 system prompt) are checked by the driver's preflight.

**Known confound:** the v1 prompt does not mention a reason either; v2.1 therefore differs from v1 by the citation interface *and* this extra phrase. The comparison measures the v2.1 bundle against v1, and cannot attribute an effect to either part alone.

**Review (F5):** an independent `code-reviewer` subagent reviewed the revision at about 15:55 and returned **GO**, with LOW findings only. It recomputed all 28 frozen-file hashes (all match), confirmed the v1 goldens equal the recorded ones, confirmed that all four v2 schema violations were "missing required field 'reason'", and ran the suite (73 tests, OK). It agreed that the confound is disclosed accurately. A first draft of this note had planned a self-review, because of a 16:30 deadline that was then lifted. The search budget for revisions (1) is now used up.
