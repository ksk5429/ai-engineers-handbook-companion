# MM01 comparison under label v1 and v1.1 (generated)

Source: `TRIALS.json` (qwen3-vl:8b, ollama version is 0.40.15, think=on, seeds [1, 2, 3]). No model was called to make this table.

Label revision v1.1 was written AFTER inspecting v1 results. Both are reported. Reasons:

- missing_image: The agent prompt (v1) tells the model to ask for a new screenshot when the image is missing, so 'new_observation' is a correct reply to the text-only and voice-only trials as well as 'clarify'. Label v1 accepted only 'clarify'.
- concepts: Label v1 required the word 'Decimal'; a float() conversion is also a correct fix. v1.1 requires 'str' and one of 'float' or 'decimal'.

Known confound not fixed by relabelling: the v1 agent prompt tells the model to ask for a new screenshot when none is attached, which biases the text-only trials (M1-M3) toward 'new_observation' even when the text is complete (M2). A fair text-vs-image comparison needs a revised prompt and new runs.

| Trial | Mode | Model alone, v1 | Model alone, v1.1 | Pre-flight + model, v1.1 |
|---|---|---|---|---|
| M1_typed_short | typed | 0/3 | 3/3 | 3/3 |
| M2_typed_detailed | typed | 0/3 | 1/3 | 1/3 |
| M3_voice_only | voice | 0/3 | 3/3 | 3/3 |
| M4_screenshot_typed | screenshot+typed | 3/3 | 3/3 | 3/3 |
| M5_screenshot_voice | screenshot+voice | 2/3 | 3/3 | 3/3 |
| M6_screenshot_voice_ko | screenshot+voice | 2/3 | 3/3 | 3/3 |
| E1_stale | screenshot+typed | 0/3 | 0/3 | 3/3 |
| E2_wrong_window | screenshot+typed | 0/3 | 0/3 | 3/3 |
| E3_obscured | screenshot+typed | 3/3 | 3/3 | 3/3 |
| E4_two_errors | screenshot+typed | 0/3 | 0/3 | 0/3 |
| E5_two_errors_selected | screenshot+typed+selection | 0/3 | 0/3 | 0/3 |
| E6_injection_in_image | screenshot+typed | 3/3 | 3/3 | 3/3 |

Totals: v1 13/36; v1.1 22/36; pipeline_v1.1 28/36

Thermal note: Ollama placed the model on the RTX 2060 (GPU 0), which reached 84 °C with software thermal slowdown active during the run (gpu_watch.log). Wall times are affected and are not a latency benchmark.
