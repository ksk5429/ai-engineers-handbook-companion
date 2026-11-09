# MM01 trials through Claude Code subagents (generated)

Generated 2026-11-09T01:49:58+00:00 by `examples/mm01_screen_grounding/score_replies.py`.
Route: Claude Code 2.1.319 (VS Code extension), Agent tool, model alias `haiku`, one fresh subagent per trial, Read tool on the PNG. n=1 per trial.

| Trial | Expected | Decision | Target ok | Concepts ok | Passed | Reply sha256 |
|---|---|---|---|---|---|---|
| E1_stale | new_observation | new_observation | None | None | True | `0222ffd9151e` |
| E4_two_errors | clarify | clarify | None | None | True | `ecf119a247c8` |
| M4_screenshot_typed | answer | answer | True | True | True | `c1a68a2b810d` |

Contamination note: the stale-image trial's reply says the file name marks the image as stale. The fixture file names (e.g. stale_screenshot.png) leaked the label to this route. That trial does not count as evidence that the model judged freshness from the metadata. Fixture images are renamed to neutral names for later runs.
