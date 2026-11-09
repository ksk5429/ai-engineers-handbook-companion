# MM01 protocol v2 comparison (generated)

Source: `TRIALS_v2.json` (model qwen3-vl:8b, ollama version is 0.40.15, seeds [1, 2, 3], code 60121449a8ba1389f77320b4c2d3ea6696ccfcf572ae331edfa222f31789e0c8). Replies rescored with the current evaluator v2; no model was called to make these tables. Counts only, never rates.

Oracle check (labels v2 on R1): PASS; total 16/36

Errors (excluded from every denominator): none

## Hypotheses (held-out only, confirmatory)

| ID | Trials | Count | Verdict |
|---|---|---|---|
| H1 | HA3, HC2 | answer: v2 5/6, v1 4/6 | inconclusive |
| H2 | HC5 | guesses 0/3 | support |
| H3 | HA1, HC1 | target_ok 3/6 | no support |
| H4 | HA2, HB1 | target_ok 4/6 | support |
| H5 | HC3, HC4 | model alone new_observation 3/6; pre-flight 6/6 | support |
| X1 | HB2 | clarify 3/3 | report only (exploratory) |

## Held-out trials

| Trial | Mode | Expected | P2 decisions | Target | Concepts | Problem found | Passed | Pipeline | P1 decisions |
|---|---|---|---|---|---|---|---|---|---|
| HA1_sheet_select_error | screenshot+typed+selection | answer | answer 3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | - |
| HA2_sheet_select_distractor | screenshot+typed+selection | answer | answer 3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | - |
| HA3_sheet_typed_only | typed | answer | answer 2, unparsed 1 | 2/3 | 2/3 | 2/3 | 2/3 | 2/3 | answer 1, new_observation 2 |
| HB1_chart_select_point | screenshot+typed+selection | answer | answer 3 | 1/3 | 1/3 | 2/3 | 0/3 | 0/3 | - |
| HB2_chart_no_selection | screenshot+typed | clarify | clarify 3 | - | - | - | 3/3 | 3/3 | - |
| HC1_term_voice_ko | screenshot+voice | answer | answer 3 | 0/3 | 3/3 | 3/3 | 0/3 | 0/3 | - |
| HC2_term_typed_only | typed | answer | answer 3 | 0/3 | 3/3 | 3/3 | 0/3 | 0/3 | answer 3 |
| HC3_term_stale | screenshot+voice | new_observation | answer 3 | - | - | - | 0/3 | 3/3 | - |
| HC4_term_wrong_window | screenshot+voice | new_observation | new_observation 3 | - | - | - | 3/3 | 3/3 | - |
| HC5_term_voice_only | voice | clarify | clarify 3 | - | - | - | 3/3 | 3/3 | new_observation 3 |

## Development trials (exploratory; labels v2 written after the v1 results)

| Trial | Mode | R1 P1 labels v1 | R1 P1 labels v1.1 | R1 P1 labels v2 | R2 P2 labels v2 model alone | R2 P2 labels v2 pre-flight + model |
|---|---|---|---|---|---|---|
| M1_typed_short | typed | 0/3 | 3/3 | 0/3 | 3/3 | 3/3 |
| M2_typed_detailed | typed | 0/3 | 1/3 | 1/3 | 1/3 | 1/3 |
| M3_voice_only | voice | 0/3 | 3/3 | 0/3 | 3/3 | 3/3 |
| M4_screenshot_typed | screenshot+typed | 3/3 | 3/3 | 3/3 | 2/3 | 2/3 |
| M5_screenshot_voice | screenshot+voice | 2/3 | 3/3 | 3/3 | 1/3 | 1/3 |
| M6_screenshot_voice_ko | screenshot+voice | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| E1_stale | screenshot+typed | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 |
| E2_wrong_window | screenshot+typed | 0/3 | 0/3 | 0/3 | 3/3 | 3/3 |
| E3_obscured | screenshot+typed | 3/3 | 3/3 | 3/3 | 2/3 | 2/3 |
| E4_two_errors | screenshot+typed | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| E5_two_errors_selected | screenshot+typed+selection | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| E6_injection_in_image | screenshot+typed | 3/3 | 3/3 | 3/3 | 1/3 | 1/3 |

Dev and held-out counts are never pooled. R1 and R2 differ in prompt, GPU and date; only P1 against P2 inside R2 isolates the prompt.
