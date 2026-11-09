# Live dictation: managing editor's analysis (not scorer output)

Source: `transcripts_live.json` (verbatim), scored in `DICTATION_RESULTS.md` under the rules committed before dictation (2629358, 16:40:57). This file interprets the transcript; it does not change any score.

**Pre-registered result:** 3 of 5 sentences usable without correction (D2, D4, D5).

| ID | Said | Heard | What went wrong | Consequence for an agent |
|---|---|---|---|---|
| D1 | totals dot py … line twelve | total dot py … line 12 | file name lost its final "s" | the agent would look for `total.py`, which does not exist, or guess |
| D2 | cell D7 … kilometres and miles | cell D7 … kilometers and miles | nothing material (US spelling) | none |
| D3 | load underscore levels dot py 14번째 … KeyError | Load underscore levels dot by14번째 … key error | "py" heard as "by"; the number fused onto the Korean ordinal | file name wrong; "14" present but attached to "번째" |
| D4 | The hotel is capped at ninety euros … ninety, not one hundred and five | 또 호텔 is capped at 90 euros … 90, not 105 | the recogniser switched to Korean for the first two words ("또 호텔", "also, hotel") | meaning slightly shifted; all numbers and units exact |
| D5 | Summarize … do not change any files | identical | none | none |

**Scorer flaw found (disclosed, not rescored):** the D3 rule for "14" required a word boundary (`\b14\b`). In Korean the ordinal suffix attaches directly to the number ("14번째"), so the rule missed a "14" that is present. A corrected rule would give D3 2/3, still not usable because of the file name. Like the MM01 label revisions, a fix belongs in a new protocol version applied to new dictations, not to these.

**What this shows (one speaker, one session, n = 5):** numbers and units came through as digits and correct words, which is what technical requests most need. File names did not: two of the two spoken file names were wrong. The practical rule for chapter Q1 holds: read the transcript and fix file names before sending, or type them.

**Deviation:** the five sentences were sent in one message, not five; the editor split them at sentence boundaries without changing any word. Route: the Claude Code microphone button (confirmed by the owner). Windows voice typing was not tested.
