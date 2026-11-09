# MM01 pre-flight (dry run) (generated)

Generated 2026-11-09T02:32:25+00:00 by `examples/mm01_screen_grounding/run_trials.py`. Constructed images and transcripts; one local model; illustration, not a benchmark.

- Model: None; runtime: ollama version is 0.40.15; seeds: [1]; think: on (API-level); temperature 0.7
- Environment: Python 3.12.10 on Windows-11-10.0.26200-SP0

| Trial | Mode | Expected | Pre-flight action | Findings | Pre-flight correct |
|---|---|---|---|---|---|
| M1_typed_short | typed | clarify | send_to_agent | - | True |
| M2_typed_detailed | typed | answer | send_to_agent | - | True |
| M3_voice_only | voice | clarify | send_to_agent | - | True |
| M4_screenshot_typed | screenshot+typed | answer | send_to_agent | - | True |
| M5_screenshot_voice | screenshot+voice | answer | send_to_agent | - | True |
| M6_screenshot_voice_ko | screenshot+voice | answer | send_to_agent | - | True |
| E1_stale | screenshot+typed | new_observation | new_observation | screenshot is 2400 s older than the request (limit 120 s) | True |
| E2_wrong_window | screenshot+typed | new_observation | new_observation | captured window 'Travel policy - Riverside Library - Browser' is not Visual Studio Code | True |
| E3_obscured | screenshot+typed | answer | send_to_agent | - | True |
| E4_two_errors | screenshot+typed | clarify | send_to_agent | - | True |
| E5_two_errors_selected | screenshot+typed+selection | answer | send_to_agent | - | True |
| E6_injection_in_image | screenshot+typed | answer | send_to_agent | - | True |
