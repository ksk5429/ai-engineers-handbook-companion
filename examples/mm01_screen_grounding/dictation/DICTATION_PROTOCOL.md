# Live dictation test (D1–D5): protocol, written before any dictation

**Written:** 9 Nov 2026, about 16:40 KST (committed as 2629358 at 16:40:57; an earlier draft of this line said 16:45), before the owner dictated anything. **Owner decision:** D-18.
**Microphone:** MATA STUDIO C300 (Windows capture endpoint state 1 = active at 16:37).
**Route under test:** Claude Code VS Code extension 2.1.319, microphone button in the prompt box [M-003, M-004]. The audio is processed on Anthropic's servers, not locally [M-003].
**Optional second route:** Windows voice typing (Win+H) [M-014], same sentences.

## Procedure

1. Press the microphone button in the Claude Code prompt box (or Win+H) and read **one** sentence below aloud, exactly as written, at a normal pace.
2. **Do not correct the transcript.** Send it as it is: the raw transcript is the data.
3. Start each message with nothing extra; send the sentences in order D1 to D5, one message each.
4. The managing editor records each message verbatim in `transcripts_live.json` and scores it with `score_dictation.py` against the key terms below. The scoring rules are fixed now.

## Sentences and key terms (pre-registered)

| ID | Read aloud exactly | Key terms that must appear (any listed form counts) |
|---|---|---|
| D1 | "Explain why totals dot py failed on line twelve." | `totals.py` (also "totals dot py", "totals.pi"); `12` or "twelve" |
| D2 | "Check whether cell D7 adds kilometres and miles without converting them." | `D7` (also "D 7", "d7"); "kilometres"/"kilometers"/"km"; "miles" |
| D3 | "load underscore levels dot py 14번째 줄에서 KeyError가 왜 났는지 설명해 줘." | `load_levels.py` (also "load levels dot py", "load_levels"); `14`; "KeyError" (also "key error") |
| D4 | "The hotel is capped at ninety euros per night, so allow ninety, not one hundred and five." | `90` or "ninety"; `105` or "one hundred and five"; "euro"/"euros" |
| D5 | "Summarize the options shown here and compare them, but do not change any files." | "compare"; "not change"/"don't change"; "files" |

**Scoring:** for each sentence, the share of key terms present (case-insensitive, matching any listed form). A sentence is *usable without correction* if every key term is present. Results are reported per sentence (n = 5, one speaker, one microphone, one session): an illustration, not an accuracy rate. Speaker, accent and room are not controlled.
