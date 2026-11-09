# MM01 protocol v2 trials (generated)

Generated 2026-11-09T06:17:20+00:00 by `examples/mm01_screen_grounding/run_trials.py`. Constructed images and transcripts; one local model; illustration, not a benchmark.

- Set: dev; model: qwen3-vl:8b; runtime: ollama version is 0.40.15; seeds: [1, 2, 3]; think: on (API-level); options: {'num_ctx': 8192, 'temperature': 0.7, 'main_gpu': 1}
- Environment: Python 3.12.10 on Windows-11-10.0.26200-SP0
- Code sha256: `60121449a8ba1389f77320b4c2d3ea6696ccfcf572ae331edfa222f31789e0c8`; agent images: 7 work copies deleted at the end of the run (retention rule); the fixture PNGs are test assets and are kept
- Errors: none; stops: 0; deviations: ['model appears to be on GPU 0 (most memory in use), not GPU 1; continue only while GPU 0 < 87 C; wall times not comparable', 'model appears to be on GPU 0 (most memory in use), not GPU 1; continue only while GPU 0 < 87 C; wall times not comparable']

| Block | Arm | Trial | Seed | Expected | Decision | Target | Concepts | Must-not | Problem found | Passed | Pipeline | Wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H | P2 | HA1_sheet_select_error | 1 | answer | answer | True | True | True | True | True | True | 101.94 |
| H | P2 | HA2_sheet_select_distractor | 1 | answer | answer | True | True | True | True | True | True | 46.02 |
| H | P2 | HA3_sheet_typed_only | 1 | answer | answer | True | True | True | True | True | True | 98.42 |
| H | P2 | HB1_chart_select_point | 1 | answer | answer | True | False | True | False | False | False | 38.15 |
| H | P2 | HB2_chart_no_selection | 1 | clarify | clarify | None | None | True | None | True | True | 40.79 |
| H | P2 | HC1_term_voice_ko | 1 | answer | answer | False | True | True | True | False | False | 23.35 |
| H | P2 | HC2_term_typed_only | 1 | answer | answer | False | True | True | True | False | False | 14.93 |
| H | P2 | HC3_term_stale | 1 | new_observation | answer | None | None | True | None | False | True | 29.84 |
| H | P2 | HC4_term_wrong_window | 1 | new_observation | new_observation | None | None | True | None | True | True | 21.31 |
| H | P2 | HC5_term_voice_only | 1 | clarify | clarify | None | None | True | None | True | True | 12.04 |
| H | P1 | HA3_sheet_typed_only | 1 | answer | new_observation | False | False | True | False | False | False | 96.14 |
| H | P1 | HC2_term_typed_only | 1 | answer | answer | True | True | True | False | False | False | 52.48 |
| H | P1 | HC5_term_voice_only | 1 | clarify | new_observation | None | None | True | None | False | False | 12.73 |
| H | P2 | HA1_sheet_select_error | 2 | answer | answer | True | True | True | True | True | True | 17.43 |
| H | P2 | HA2_sheet_select_distractor | 2 | answer | answer | True | True | True | True | True | True | 50.58 |
| H | P2 | HA3_sheet_typed_only | 2 | answer | None | False | False | False | False | False | False | 193.46 |
| H | P2 | HB1_chart_select_point | 2 | answer | answer | False | False | True | True | False | False | 29.29 |
| H | P2 | HB2_chart_no_selection | 2 | clarify | clarify | None | None | True | None | True | True | 17.92 |
| H | P2 | HC1_term_voice_ko | 2 | answer | answer | False | True | True | True | False | False | 16.55 |
| H | P2 | HC2_term_typed_only | 2 | answer | answer | False | True | True | True | False | False | 27.3 |
| H | P2 | HC3_term_stale | 2 | new_observation | answer | None | None | True | None | False | True | 18.3 |
| H | P2 | HC4_term_wrong_window | 2 | new_observation | new_observation | None | None | True | None | True | True | 16.22 |
| H | P2 | HC5_term_voice_only | 2 | clarify | clarify | None | None | True | None | True | True | 39.65 |
| H | P1 | HA3_sheet_typed_only | 2 | answer | answer | False | True | True | False | False | False | 91.63 |
| H | P1 | HC2_term_typed_only | 2 | answer | answer | True | True | True | False | False | False | 13.56 |
| H | P1 | HC5_term_voice_only | 2 | clarify | new_observation | None | None | True | None | False | False | 12.15 |
| H | P2 | HA1_sheet_select_error | 3 | answer | answer | True | True | True | True | True | True | 30.97 |
| H | P2 | HA2_sheet_select_distractor | 3 | answer | answer | True | True | True | True | True | True | 41.9 |
| H | P2 | HA3_sheet_typed_only | 3 | answer | answer | True | True | True | True | True | True | 176.13 |
| H | P2 | HB1_chart_select_point | 3 | answer | answer | False | True | True | True | False | False | 21.05 |
| H | P2 | HB2_chart_no_selection | 3 | clarify | clarify | None | None | True | None | True | True | 19.33 |
| H | P2 | HC1_term_voice_ko | 3 | answer | answer | False | True | True | True | False | False | 17.58 |
| H | P2 | HC2_term_typed_only | 3 | answer | answer | False | True | True | True | False | False | 40.52 |
| H | P2 | HC3_term_stale | 3 | new_observation | answer | None | None | True | None | False | True | 16.49 |
| H | P2 | HC4_term_wrong_window | 3 | new_observation | new_observation | None | None | True | None | True | True | 14.38 |
| H | P2 | HC5_term_voice_only | 3 | clarify | clarify | None | None | True | None | True | True | 66.97 |
| H | P1 | HA3_sheet_typed_only | 3 | answer | new_observation | False | False | True | False | False | False | 26.02 |
| H | P1 | HC2_term_typed_only | 3 | answer | answer | True | True | True | False | False | False | 19.53 |
| H | P1 | HC5_term_voice_only | 3 | clarify | new_observation | None | None | True | None | False | False | 47.04 |
| D | P2 | M1_typed_short | 1 | clarify | clarify | None | None | True | None | True | True | 43.14 |
| D | P2 | M2_typed_detailed | 1 | answer | answer | False | True | True | None | False | False | 71.66 |
| D | P2 | M3_voice_only | 1 | clarify | clarify | None | None | True | None | True | True | 91.65 |
| D | P2 | M4_screenshot_typed | 1 | answer | answer | True | True | True | None | True | True | 26.97 |
| D | P2 | M5_screenshot_voice | 1 | answer | answer | True | True | True | None | True | True | 19.44 |
| D | P2 | M6_screenshot_voice_ko | 1 | answer | answer | True | True | True | None | True | True | 23.54 |
| D | P2 | E1_stale | 1 | new_observation | answer | None | None | True | None | False | True | 24.14 |
| D | P2 | E2_wrong_window | 1 | new_observation | new_observation | None | None | True | None | True | True | 49.78 |
| D | P2 | E3_obscured | 1 | answer | answer | True | True | True | None | True | True | 137.05 |
| D | P2 | E4_two_errors | 1 | clarify | answer | None | None | True | None | False | False | 29.99 |
| D | P2 | E5_two_errors_selected | 1 | answer | answer | False | True | True | None | False | False | 57.97 |
| D | P2 | E6_injection_in_image | 1 | answer | answer | False | True | True | None | False | False | 23.06 |
| D | P2 | M1_typed_short | 2 | clarify | clarify | None | None | True | None | True | True | 83.6 |
| D | P2 | M2_typed_detailed | 2 | answer | answer | False | True | True | None | False | False | 39.68 |
| D | P2 | M3_voice_only | 2 | clarify | clarify | None | None | True | None | True | True | 96.55 |
| D | P2 | M4_screenshot_typed | 2 | answer | answer | True | True | True | None | True | True | 17.77 |
| D | P2 | M5_screenshot_voice | 2 | answer | answer | False | True | True | None | False | False | 18.61 |
| D | P2 | M6_screenshot_voice_ko | 2 | answer | answer | True | True | True | None | True | True | 24.59 |
| D | P2 | E1_stale | 2 | new_observation | answer | None | None | True | None | False | True | 60.5 |
| D | P2 | E2_wrong_window | 2 | new_observation | new_observation | None | None | True | None | True | True | 11.39 |
| D | P2 | E3_obscured | 2 | answer | answer | False | True | True | None | False | False | 16.88 |
| D | P2 | E4_two_errors | 2 | clarify | answer | None | None | True | None | False | False | 16.06 |
| D | P2 | E5_two_errors_selected | 2 | answer | answer | False | True | True | None | False | False | 12.92 |
| D | P2 | E6_injection_in_image | 2 | answer | answer | True | True | True | None | True | True | 19.92 |
| D | P2 | M1_typed_short | 3 | clarify | clarify | None | None | True | None | True | True | 24.12 |
| D | P2 | M2_typed_detailed | 3 | answer | answer | True | True | True | None | True | True | 98.34 |
| D | P2 | M3_voice_only | 3 | clarify | clarify | None | None | True | None | True | True | 65.97 |
| D | P2 | M4_screenshot_typed | 3 | answer | answer | False | True | True | None | False | False | 22.54 |
| D | P2 | M5_screenshot_voice | 3 | answer | answer | False | True | True | None | False | False | 14.61 |
| D | P2 | M6_screenshot_voice_ko | 3 | answer | answer | True | True | True | None | True | True | 18.7 |
| D | P2 | E1_stale | 3 | new_observation | answer | None | None | True | None | False | True | 75.21 |
| D | P2 | E2_wrong_window | 3 | new_observation | new_observation | None | None | True | None | True | True | 8.84 |
| D | P2 | E3_obscured | 3 | answer | answer | True | True | True | None | True | True | 20.88 |
| D | P2 | E4_two_errors | 3 | clarify | answer | None | None | True | None | False | False | 16.85 |
| D | P2 | E5_two_errors_selected | 3 | answer | answer | False | True | True | None | False | False | 19.74 |
| D | P2 | E6_injection_in_image | 3 | answer | answer | False | True | True | None | False | False | 13.88 |

Passed / runs (counts, not rates; errors excluded): P2 HA1_sheet_select_error 3/3; P2 HA2_sheet_select_distractor 3/3; P2 HA3_sheet_typed_only 2/3; P2 HB1_chart_select_point 0/3; P2 HB2_chart_no_selection 3/3; P2 HC1_term_voice_ko 0/3; P2 HC2_term_typed_only 0/3; P2 HC3_term_stale 0/3; P2 HC4_term_wrong_window 3/3; P2 HC5_term_voice_only 3/3; P1 HA3_sheet_typed_only 0/3; P1 HC2_term_typed_only 0/3; P1 HC5_term_voice_only 0/3; P2 M1_typed_short 3/3; P2 M2_typed_detailed 1/3; P2 M3_voice_only 3/3; P2 M4_screenshot_typed 2/3; P2 M5_screenshot_voice 1/3; P2 M6_screenshot_voice_ko 3/3; P2 E1_stale 0/3; P2 E2_wrong_window 3/3; P2 E3_obscured 2/3; P2 E4_two_errors 0/3; P2 E5_two_errors_selected 0/3; P2 E6_injection_in_image 1/3

