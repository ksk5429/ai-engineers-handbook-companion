# G-03 Multimodal input on Windows 11: screenshots, dictation and the MM01 checks

**Guide date:** 9 Nov 2026. **Test machine:** Windows 11 Pro 26200, VS Code with the Claude Code extension 2.1.319, Ollama 0.40.15 with `qwen3-vl:8b`, no active microphone. **Recheck when:** Claude Code, Codex or Ollama changes its image or voice features (sources M-001–M-031 in `references/sources.md`).

Each step below carries its state: **tested** (run on the test machine, with an evidence path), **documented only** (from the sources; not run here), or **blocked** (could not run, with the reason).

## Route 1: screenshot + text in the Claude Code VS Code extension

| Step | Instruction | State |
|---|---|---|
| 1 | Capture the window or region you mean, using any screenshot tool; crop out private content | documented only (capture tools were not exercised; the test fixtures are drawn by code) |
| 2 | Paste the image into the Claude Code prompt box, or Shift+drag the image file into it [M-004, M-005] | documented only |
| 3 | Type a short instruction that names the outcome and the permitted action: "Explain why this failed. Start by stating the file, line and error you are looking at. Do not change files." | tested in an equivalent form: a Claude Code subagent given the image path and the bundle prompt (`reviews/evidence/mm01/claude_code/`) |
| 4 | Check the stated target before reading the explanation (chapter Q1, "Checking what the agent understood") | tested in the equivalent route: 3 of 3 decisions correct, one of them contaminated by a revealing file name (see SCORES.md) |

## Route 2: dictation

| Step | Instruction | State |
|---|---|---|
| 1 | Connect and enable a microphone (Settings → System → Sound → Input) | **blocked** on the test PC: all 9 capture endpoints report "not present" |
| 2a | Claude Code VS Code extension: click the microphone button in the prompt box. Requires a claude.ai sign-in; audio is processed on Anthropic's servers; not available with API-key, Bedrock, Vertex, Foundry or remote sessions [M-003, M-004] | documented only |
| 2b | Any text box: Windows voice typing, Win+H. Online service; supports Korean [M-014] | documented only |
| 3 | Read the transcript and correct file names, numbers and units before sending | — |
| 4 | Record: what you said, raw transcript, corrections, whether the agent named the right target | template in chapter Q1, "Voice" |

## Route 3: the MM01 experiment (engineering)

```text
cd examples\mm01_screen_grounding
python make_fixtures.py                    # 7 synthetic screenshots + labels       (tested)
python run_trials.py --dry-run             # pre-flight on 12 trials, no model     (tested: 12/12 correct)
python run_trials.py --model qwen3-vl:8b --seeds 1 2 3 --think on   # 36 calls  (tested; announced GPU window)
python rescore.py                          # v1 and v1.1 tables from stored replies (tested)
python score_replies.py ..\..\reviews\evidence\mm01\claude_code    # Claude Code route (tested)
```

Expected vs observed: `run_trials.py --dry-run` should report `new_observation` for the stale and wrong-window trials and `send_to_agent` for the other ten; observed exactly that (`reviews/evidence/mm01/PREFLIGHT.md`). Model results are in `TRIALS.md` and `COMPARISON.md`.

**Before a GPU run on a shared PC:** `ollama ps` must be empty; pass `"options": {"main_gpu": 1}` if you need a specific card (this run landed on the RTX 2060 and reached 84 °C with thermal slowdown); watch `nvidia-smi` and stop at your limit; `ollama stop qwen3-vl:8b` afterwards.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| The agent describes the wrong window | the screenshot was taken with another window focused | capture the window, not the screen; pre-flight checks the window title when the capture tool provides it |
| The agent explains an error you already fixed | stale screenshot | take a new one; pre-flight rejects images older than 120 s (configurable in `bundle.py`) |
| The agent ignores your rectangle | observed in 3 of 3 runs with `qwen3-vl:8b` | name the target in words as well as outlining it |
| Dictation mangles `totals.py` | speech recognisers treat code names as words | spell it, or correct the transcript before sending |
| An image-reading agent "knows" the answer from the file name | descriptive file names leak labels | the companion code passes images under hash-based names |

## Retention and privacy

Screenshots and recordings can contain more than the task needs. The context bundle states a retention rule (`delete capture files when the task closes`). The trial images in `reviews/evidence/mm01/agent_images/` are synthetic, and they are excluded from version control. Claude Code dictation sends audio to Anthropic [M-003]; Windows voice typing uses an online service [M-014]. Neither is a local-only route.
