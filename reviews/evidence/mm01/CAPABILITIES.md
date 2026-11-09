#### Multimodal input capabilities: documented, installed, tested (9 Nov 2026)

Compiled by the managing editor. *Documented* cites researcher R4's notes (M-xxx, pages fetched 9 Nov 2026). *Installed* comes from local checks on the Windows 11 test PC. *Tested* comes from run records in this folder. A blank in *Tested* means **not run**. This table was assembled by hand from those sources; it is not a runner output.

| Route | Capability | Documented | Installed on the test PC | Tested |
|---|---|---|---|---|
| Claude Code, VS Code extension | Typed prompt | yes [M-004] | extension 2.1.319 | used throughout this project |
| | Voice dictation | microphone button in the extension; requires a claude.ai sign-in; audio is processed on Anthropic's servers, not locally; no tokens used; 20 languages including Korean; not available with an API key, Bedrock, Vertex, Foundry, SSH or remote sessions [M-003, M-004] | the extension's manifest contributes no voice command, consistent with a button-only control; no active microphone (all 9 capture endpoints "not present") | **tested once** on 9 Nov 2026 (the owner, microphone button): 3 of 5 sentences usable without correction, both file names mis-heard; `examples/mm01_screen_grounding/dictation/` |
| | Paste or attach an image | paste into the prompt box; Shift+drag to add files [M-004, M-005] | — | not run in the chat box; an equivalent route (a subagent reading the PNG with the Read tool) was run 3 times: `claude_code/SCORES.md` |
| | Editor selection as context | selected text and the open file are sent automatically; Alt+K inserts an @-mention of a line range [M-004] | Alt+K keybinding present in the extension's manifest | not run |
| | Screen control (computer use) | CLI: macOS only; on Windows only in the Desktop app, on some plans [M-006, M-007] | — | not run (out of scope: no actuation) |
| Claude Code CLI | Voice dictation | `/voice`, hold or tap Space; works on native Windows [M-002, M-003] | `claude` not on PATH on this PC | not run |
| | Image paste | Alt+V on Windows; drag-and-drop; image file paths [M-001, M-005]. One Desktop comparison table says "File attachments: Not available" for the CLI, which conflicts with the other pages [M-006] | not installed as a CLI | not run |
| Claude API | Images | JPEG, PNG, GIF, WebP; up to 8000 × 8000 px and 10 MB; token cost grows with image area (formula in M-008) [M-008] | no API key provisioned | not run |
| OpenAI Codex CLI | Image input | `-i/--image` flag; paste into the composer [M-024, M-025] | codex-cli 0.166.0 | not run |
| | Voice | `/voice` or F8, "when your CLI build and session support voice" [M-025, M-026] | — | not run |
| Grok Bot | Images, files, dictation | paste images, attach files, dictate with Cmd/Ctrl+D, live voice chat [M-016–M-019] | not installed; no account checked | not run |
| | Programmatic task interface | none found that sends a task and returns the result [T-005, M-016–M-019] | — | — |
| xAI API | Images; speech to text | `input_image` (base64 or URL; jpg/png; ≤ 20 MiB); `/v1/stt` endpoint, covers Korean [M-020, M-021] | no API key provisioned | not run |
| Ollama + qwen3-vl:8b | Images via `/api/chat` | `images` array of base64 strings [M-027, M-028]; qwen3-vl requires Ollama ≥ 0.12.7 [M-029] | Ollama 0.40.15; qwen3-vl:8b (6.1 GB) installed | **run**: 36 calls, `TRIALS.md`, `COMPARISON.md` |
| Windows 11 voice typing (Win+H) | Dictation into any text box | online (uses Microsoft's cloud speech service); supports Korean [M-014] | Windows 11 Pro 26200 | not run (a microphone is now available; only the Claude Code button was tested) |
| Windows speech-recognition API | Dictation inside an app | needs a packaged (MSIX) app; dictation runs online [M-013] | — | not run |
| Windows.Graphics.Capture | Window or region capture with user consent | a system picker asks the user and draws a yellow border around what is captured [M-009] | — | not run; fixtures were drawn, not captured |
| UI Automation | Element names and rectangles | a tree rooted at the desktop; rectangles in physical screen coordinates, so the process must be per-monitor DPI aware [M-010–M-012, M-015] | — | not run |
| OpenAI Whisper (local speech to text) | Transcription | MIT licence (code and weights); 6 sizes, tiny to large; Korean; needs ffmpeg [M-030] | openai-whisper 20250625 installed (Python 3.12); ffmpeg on PATH; model weights not checked | not run |
| faster-whisper | Transcription | MIT; int8 on CPU and GPU [M-031] | not installed | not run |
