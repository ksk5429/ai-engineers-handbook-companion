# R4: Multimodal interfaces (voice, images, screen context)

Researcher notes for the ebook "AI Engineer's Handbook". Compiled 2026-11-09.
Every source was fetched on 2026-11-09 (the access date for all items below).
Source IDs run M-001 to M-031.

**Quote marking:**
- [raw] means the quote was read in the page's raw text: markdown served by the site (`.md` endpoint or `raw.githubusercontent.com`), the HTML stripped by me, or a full-page markdown conversion from the Microsoft Learn fetch tool.
- [excerpt] means a Microsoft Learn search-index chunk of the official page. It is primary text, but I did not read the full page.
- Quotes are 25 words or fewer.

**Scope:** documentation only. Nothing was installed, run, recorded or screenshotted. "Documented" means stated in the page; it does not mean tested on this machine.

**Local context (from the brief, not re-verified):**
- The user runs the Claude Code VS Code extension v2.1.319 on Windows 11.
- The extension's package.json contributes no voice, image or paste commands.
- This is consistent with M-003 and M-004. Dictation and image paste are features of the chat webview (a microphone button and the prompt box), not contributed VS Code commands.

---

## 1. Claude Code: voice dictation and image input

### M-001 Interactive mode (Claude Code docs)
- URL: https://code.claude.com/docs/en/interactive-mode
- Date/version shown: no page date. It cites versions up to v2.1.292 ("Requires Claude Code v2.1.292 or later"). Accessed 2026-11-09.
- **Image paste key:** the shortcut row reads "`Ctrl+V` or `Cmd+V` (iTerm2) or `Alt+V` (Windows and WSL) | Paste image from clipboard" [raw].
  - Effect: "Inserts an `[Image #N]` chip at the cursor so you can reference it positionally in your prompt." [raw]
  - WSL: "On WSL, both `Ctrl+V` and `Alt+V` are bound; use `Alt+V` if your terminal intercepts `Ctrl+V`" [raw].
- **Voice key:** a "Voice input" table lists "Hold or tap `Space` | Voice dictation | Requires voice dictation to be enabled." [raw]
- **@-mention:** "`@` | File path mention | Trigger file path autocomplete." [raw] The page says nothing about @-mentioning image files specifically.
- **Cleared drafts:** Claude Code keeps "the ten most recent cleared drafts … with their pasted text and images" [raw].
- Caveat: on native Windows (not WSL) the row names `Alt+V`. The page does not say whether `Ctrl+V` also pastes images in native Windows terminals.

### M-002 Commands (Claude Code docs)
- URL: https://code.claude.com/docs/en/commands
- Date/version shown: no page date. Accessed 2026-11-09.
- **/voice:** "`/voice [hold|tap|off]` | Toggle voice dictation, or enable it in a specific mode. Requires a Claude.ai account" [raw]
- I found no image or screenshot command. The only "attach" hits are `/artifacts` and background-session attach.

### M-003 Voice dictation (Claude Code docs)
- URL: https://code.claude.com/docs/en/voice-dictation
- Date/version shown: no page date. The troubleshooting notes cite versions v2.1.195 to v2.1.231. Accessed 2026-11-09.
- **Processing is in the cloud:** "Voice dictation streams your recorded audio to Anthropic's servers for transcription. Audio is not processed locally." [raw]
- **Account requirement:**
  - Dictation needs "A Claude.ai account" [raw].
  - It "is not available when Claude Code is configured to use an Anthropic API key directly, Amazon Bedrock, Google Cloud's Agent Platform, or Microsoft Foundry." [raw]
  - The page names no plan tier beyond a claude.ai sign-in. An organization admin policy can disable it.
- **Local microphone:** dictation "does not work in cloud sessions or SSH sessions" [raw].
- **WSL:** WSL needs WSLg. Otherwise "run Claude Code in native Windows instead." [raw]
- **Cost:** "Transcription does not consume Claude messages or tokens and does not count toward the limits shown in `/usage`." [raw]
- **Platforms:** "Audio recording uses a built-in native module on macOS, Linux, and Windows." [raw]
- **VS Code extension:**
  - "The Claude Code VS Code extension also supports voice dictation with the same claude.ai account requirement." [raw]
  - It is "not available in VS Code Remote sessions, including SSH, Dev Containers, and Codespaces" [raw].
- **Modes:**
  - Hold mode is push-to-talk on `Space` and is the default. Tap mode is `/voice tap`.
  - In tap mode, "Recording also stops automatically after 15 seconds of silence or two minutes total." [raw]
  - Auto-submit requires a transcript of "at least three words" [raw].
- **Vocabulary hints:** "your current project name and git branch name are added as recognition hints automatically." [raw]
- **Languages:** dictation uses the `language` setting and defaults to English.
  - In the VS Code extension, an empty `language` falls back to VS Code's `accessibility.voice.speechLanguage`.
  - The supported list has 20 languages: cs, da, nl, en, fr, de, el, hi, id, it, ja, **ko (Korean)**, no, pl, pt, ru, es, sv, tr, uk [raw].
  - An unsupported language falls back to English.
- **Rebinding:** rebind via `voice:pushToTalk` in `~/.claude/keybindings.json`, for example `meta+k` [raw].
- **Windows microphone permission:** "On Windows, go to Settings → Privacy & security → Microphone and turn on microphone access for desktop apps" [raw]
- **VS Code limits:** a VS Code recording ends "after 15 seconds with no recognized words, or two minutes after it starts." [raw]
- **Desktop app:** this page does not mention it.

### M-004 VS Code extension (Claude Code docs)
- URL: https://code.claude.com/docs/en/vs-code
- Date/version shown: no page date. It cites versions up to v2.1.309 (keybindings.json support) and a minimum of VS Code 1.94.0. Accessed 2026-11-09.
- **Images:** "To attach an image, paste it from your clipboard into the prompt box." [raw]
- **Files:** "To attach files, hold `Shift` while dragging them into the prompt box." [raw] "To remove an attachment from context, click the X on it." [raw]
- **Selection context:**
  - "When you select text in the editor, Claude can see your highlighted code automatically." [raw]
  - "Claude also sees which file you have open in the editor, even when nothing is selected" [raw].
  - `Alt+K` (Windows/Linux) inserts an @-mention with a line range, e.g. `@app.ts#5-10` [raw].
  - Opt-outs: `attachSelection` (v2.1.300 or later) and `attachOpenFile` (v2.1.271 or later).
  - "Both settings also apply when you run `claude` in VS Code's integrated terminal." [raw]
- **Terminal output:** "Reference terminal output in your prompts using `@terminal:name`" [raw].
- **Browser:** `@browser` drives Chrome through the Claude in Chrome extension, version 1.0.36 or later [raw].
- **Dictation:**
  - The page has no dedicated voice section.
  - It refers to a "microphone button" ("the microphone button shows the error text after `Dictation error: WebSocket error:`") [raw].
  - On third-party providers, "the extension doesn't offer features that require a claude.ai account, such as plan usage bars, voice dictation" [raw].
  - A fix for dictation behind a TLS-inspecting proxy (`NODE_EXTRA_CA_CERTS` in `~/.claude/settings.json`) needs extension 2.1.307 or later.
- Caveats:
  - The page gives no keyboard shortcut for dictation in the extension.
  - It does not say whether an image dragged in with `Shift` becomes an image block or a file reference.
  - It does not mention screenshots.

### M-005 Common workflows: "Work with images" (Claude Code docs)
- URL: https://code.claude.com/docs/en/common-workflows
- Date/version shown: no page date. Accessed 2026-11-09.
- **Three ways to add an image:**
  1. "Drag and drop an image into the Claude Code window" [raw]
  2. "Copy an image and paste it into the CLI with `Ctrl+V`, or with `Alt+V` on Windows and WSL" [raw]
  3. "Provide an image path to Claude, for example 'Analyze this image: /path/to/your/image.png'" [raw]
- **Opening a referenced image:** when Claude references `[Image #1]`, `Ctrl+Click` (Windows/Linux) opens it "in your default viewer" [raw].

### M-006 Claude Code Desktop (Claude Code docs)
- URL: https://code.claude.com/docs/en/desktop
- Date/version shown: no page date. Accessed 2026-11-09.
- **Desktop attachments:** "attach images, PDFs, and other files to your prompt from the **+** button next to the prompt box, or drag and drop files" [raw].
- **CLI vs Desktop table:**
  - "File attachments | Not available | Images, PDFs" (CLI | Desktop) [raw]. See Conflicts C1.
  - "Computer use | Enable via `/mcp` on macOS | App and screen control on macOS and Windows" [raw].
- **Computer use in Desktop:**
  - It is "a research preview on macOS and Windows that requires a Pro, Max, or Ultra plan. It is not available on Team or Enterprise plans." [raw]
  - Per-app tiers: "View only | See the app in screenshots | Browsers, trading platforms". Terminals and IDEs are "Click only". Everything else gets full control [raw].
- **Voice:** the Desktop page has no voice or dictation section (searched for voice and dictat; no hits).

### M-007 Computer use (CLI) (Claude Code docs)
- URL: https://code.claude.com/docs/en/computer-use
- Date/version shown: no page date. Accessed 2026-11-09.
- **Availability:** "Computer use is a research preview on macOS that requires a Pro, Max, or Ultra plan." [raw] It is not available with `-p`.
- **Downscaling:** "Claude Code downscales every screenshot before sending it to the model." [raw] Example: 3456×2234 is downscaled to about 1372×887.
- Caveat: the CLI on Windows has no documented computer use. Windows computer use is Desktop-app only (M-006).

## 2. Claude API vision

### M-008 Vision (Claude API docs)
- URL: https://platform.claude.com/docs/en/build-with-claude/vision
- Date/version shown: no page date. Frontmatter `status: stable`, and the supported-models list includes claude-opus-5-5. Accessed 2026-11-09.
- **Sources:** three source types: base64, URL, and Files API `file_id`. Bedrock and Google-managed Vertex accept base64 only [raw].
- **Formats:** "Claude supports JPEG, PNG, GIF, and WebP images … Animations are unsupported, and only the first frame is used." [raw]
- **Image counts:** "20 for each message on claude.ai"; "100 for each request on the API, for models with a 200k-token context window"; "600 for each request on the API, for all other models" [raw].
- **Dimensions:** "The maximum dimensions for each image are 8000x8000 px." [raw] For more than 20 images, keep each image at 3,000 px or less on both sides, or send 20 or fewer image and document blocks [raw].
- **Size:** "10 MB (base64-encoded) on the Claude API" and 5 MB on Bedrock [raw]. The total request limit is 128 MB on the first-party API [raw].
- **Token formula:**
  - "Each patch is a 28×28-pixel block … An image, therefore, costs `⌈width / 28⌉ × ⌈height / 28⌉` visual tokens." [raw]
  - High-resolution tier ("Claude 4.7 and later models"): max long edge 2,576 px and 4,784 visual tokens. Standard tier: 1,568 px and 1,568 tokens [raw].
  - Worked examples: 1000×1000 px costs 1,296 tokens on both tiers. 1920×1080 px costs 1,560 (standard) or 2,691 (high-res) [raw].
- **Computer-use screenshots:** the API "rejects a `tool_result` image that exceeds the model's limits with a validation error instead of downscaling it" [raw].
- **Advice about text in images:**
  - "If the image contains important text, make sure it's legible and not too small. Avoid cropping out key visual context solely to enlarge the text." [raw]
  - Resizing "might, for example, make text less legible." [raw]
  - "heavy JPEG compression can make text difficult to read." [raw]
- **Limitations:**
  - Claude "might hallucinate or make mistakes when interpreting low-quality, rotated, or very small images under 200 pixels." [raw]
  - Spatial outputs "are approximate" [raw].
- **Coordinates:** Claude returns pixel coordinates "relative to the image it processes after resizing" [raw]. A separate vision-coordinates guide covers rescaling.

## 3. Microsoft Windows: capture, UI Automation, speech, DPI

### M-009 Screen capture (Windows.Graphics.Capture)
- URL: https://learn.microsoft.com/en-us/windows/apps/develop/media-authoring-processing/screen-capture
- Date shown: ms.date 2026-08-23. Accessed 2026-11-09.
- **Consent and border:** "developers invoke secure system UI for end users to pick the display or application window to be captured, and a yellow notification border is drawn" [raw]
- **Picker:** "Use the GraphicsCapturePicker class to invoke the system picker UI." [raw] It returns a `GraphicsCaptureItem`. WinUI 3 must initialize the picker with an HWND [raw].
- **Reusing consent:** "Once the user has explicitly given consent … the GraphicsCaptureItem can be associated with multiple capture sessions." [raw]
- **Support:** "only supported on Windows desktop devices and Windows Mixed Reality immersive headsets." [raw] Check with `GraphicsCaptureSession.IsSupported()`.

### M-010 UI Automation (entry page)
- URL: https://learn.microsoft.com/en-us/windows/desktop/winauto/entry-uiauto-win32
- Date shown: ms.date 2025-07-14. Accessed 2026-11-09.
- **Coverage:** UIA "provides programmatic access to most UI elements on the desktop" [raw].
- **Testing:** "UI Automation also allows automated test scripts to interact with the UI." [raw]

### M-011 UI Automation tree overview and specification (Microsoft Learn search excerpts)
- URLs:
  - https://learn.microsoft.com/windows/win32/winauto/uiauto-treeoverview
  - https://learn.microsoft.com/windows/win32/winauto/ui-automation-specification
- Accessed 2026-11-09 via the Learn search index.
- **Tree:** "Elements are exposed as a tree structure, with the desktop as the root element." [excerpt]
- **Views:** three default views: raw, control and content. Raw is "the full tree of automation elements for which the desktop is the root." [excerpt]

### M-012 Automation element property identifiers
- URL: https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-automation-element-propids
- Date shown: ms.date 2025-07-14. Accessed 2026-11-09.
- **BoundingRectangle:** "specifies the coordinates of the rectangle that completely encloses the automation element. The rectangle is expressed in physical screen coordinates." [raw]
- **Name:** "The Name property should be the same as the label text on screen." [raw]
- Implication (inferred): UIA rectangles are physical pixels, while a DPI-unaware process sees virtualized coordinates (M-015). The process must be per-monitor DPI aware to match UIA rectangles to screenshot pixels.

### M-013 Speech recognition in Windows apps
- URL: https://learn.microsoft.com/en-us/windows/apps/develop/input/speech-recognition
- Date shown: ms.date 2026-07-08. Accessed 2026-11-09.
- **Package identity:** "Speech recognition requires MSIX package identity." [raw] "Unpackaged apps cannot use these APIs." [raw]
- **Online grammars:** the predefined dictation and web-search grammars use "a remote web service" [raw]. They "recognize up to 10 seconds of speech input" and "require a network connection." [raw]
- Implication (inferred): a plain Python or Node script cannot call `Windows.Media.SpeechRecognition` without MSIX packaging.

### M-014 Windows voice typing (Microsoft Support)
- URL: https://support.microsoft.com/en-us/windows/use-voice-typing-to-talk-instead-of-type-on-your-pc-fec94565-c4bd-329d-e59a-af033fa5689f
- Title: "Use voice typing to talk instead of type on your PC". No date found in the stripped text. Accessed 2026-11-09.
- **Online:** "Voice typing uses online speech recognition, which is powered by Azure Speech services." [raw]
- **Requirements:** "you'll need to be connected to the internet, have a working microphone, and have your cursor in a text box." [raw]
- **Start:** "Press Windows key+ H on a hardware keyboard." [raw]
- **Languages:** the Windows 11 voice typing list includes Korean and Japanese [raw]. The page also has Korean voice-typing command tables [raw].
- **Settings:** voice typing launcher, automatic punctuation, profanity filter, default microphone [raw].
- Caveat: the page contains a Windows 10 dictation section with a separate, shorter language list. For Windows 10, "Dictation commands are available in US English only." [raw]

### M-015 High DPI desktop application development on Windows
- URL: https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows
- Date shown: ms.date 2026-09-10. Accessed 2026-11-09. The quotes below were checked against the raw HTML.
- **Default:** "By default, the system considers desktop applications DPI unaware and bitmap-stretches their windows." [raw]
- **Virtualization:** a DPI-unaware thread querying screen size gets an answer virtualized "as if the screen were in 96 DPI units." [raw]
- **Per-Monitor V2:** results in "The application seeing the raw pixels of each display" [raw]. PMv2 dates from Windows 10 1703.

## 4. xAI: Grok Bot and the xAI API

### M-016 Grok Bot: Message and collaborate
- URL: https://docs.x.ai/grok-bot/chat-and-collaboration (fetched as `.md`)
- No page date. Accessed 2026-11-09.
- **Composer:** "Paste text, links, and images"; "Attach local files"; "Dictate into the composer"; "Start a voice chat" [raw].
- **Dictation:** "Voice typing turns your speech into text in the composer." [raw] On desktop, press `Cmd/Ctrl+D` while the prompt is focused; "You can also hold the keys while you talk." [raw]
- **Voice chat:** "A voice chat is a live spoken conversation with one Bot" [raw]. It works on desktop and phone and "not in group chats" [raw].

### M-017 Grok Bot overview
- URL: https://docs.x.ai/grok-bot/overview
- Accessed 2026-11-09.
- **Cloud computer:** "It's an agent with access to a real computer in the cloud" [raw].
- **Integrations:** "Grok Bot supports custom tooling, so it can interact with any MCP or API." [raw] That is outbound use of tools, not an inbound API.

### M-018 Grok Bot: Files and results
- URL: https://docs.x.ai/grok-bot/files-and-results
- Accessed 2026-11-09.
- **Attaching:** "Use the attachment control or drag files into the composer. You can also paste images and links." [raw]
- **Inputs:** supported inputs include "Images, audio, and video" [raw].
- **Desktop limits:** 20 attachments per message. Images are "25 MB each, 200 MB total per message" [raw].

### M-019 Grok Bot FAQ and "Use the computer and apps"
- URLs:
  - https://docs.x.ai/grok-bot/faq
  - https://docs.x.ai/grok-bot/computer-and-apps
- Accessed 2026-11-09.
- **Surfaces:** "Use the Grok Bot desktop app on macOS, Windows, or Linux, or the companion app on iOS or Android." [raw] It is also available in X Chat, by tagging @bot on X, and in Slack (shared Bot).
- **Local computer:** "Bots work on their own cloud computer. A Bot runs a command on your desktop only if you allow it." [raw] The default is "Ask every time" [raw].
- Caveat: none of the fetched Grok Bot pages documents an API for sending messages to a Bot programmatically. The docs.x.ai `llms.txt` Grok Bot section lists no such page. Treat as "not documented" (UNVERIFIED absence).

### M-020 xAI API: Image Understanding
- URL: https://docs.x.ai/developers/model-capabilities/images/understanding
- Accessed 2026-11-09.
- **Input format:**
  - Content items have `"type": "input_image"` and `"image_url": "data:image/jpeg;base64,<base64_image_string>"` [raw].
  - "The `image_url` value can also be a public URL" [raw].
  - Examples use `"detail": "high"`, the Responses endpoint `https://api.x.ai/v1/responses`, and model `grok-4.7` [raw].
- **Limits:** "Maximum image size: `20MiB`"; "Maximum number of images: No limit"; "Supported image file types: `jpg/jpeg` or `png`." [raw]
- **Warning:** "it is advised to not store request/response history on the server. Otherwise the request may fail." [raw]
- Caveat: the page does not list every vision-capable model. Only `grok-4.7` appears in the examples.

### M-021 xAI API: Speech to Text
- URL: https://docs.x.ai/developers/model-capabilities/audio/speech-to-text
- Accessed 2026-11-09.
- **Endpoint and model:** `POST https://api.x.ai/v1/stt` with model `grok-voice-transcribe-2.0` [raw]. It "transcribes 38+ languages", and the list includes Korean (`ko`) [raw].
- **Size limit:** "Max **500 MB**" per file [raw]. WebSocket streaming is also available.

### M-022 xAI docs index
- URL: https://docs.x.ai/llms.txt
- Accessed 2026-11-09.
- Used only to enumerate pages: Grok Bot pages, Image Understanding, and the Voice and STT pages.

## 5. OpenAI Codex CLI

### M-023 Codex CLI
- URL: https://learn.chatgpt.com/docs/codex/cli
- Accessed 2026-11-09.
- **Relocation:** `https://developers.openai.com/codex/llms.txt` now points its Codex pages to learn.chatgpt.com.
- **Images:** "`codex --image`: Pass an error screenshot, architecture diagram, or design reference with the first prompt, or paste an image into the interactive composer." [raw]

### M-024 Image inputs (Codex/ChatGPT docs, CLI surface)
- URL: https://learn.chatgpt.com/docs/image-inputs?surface=cli
- Accessed 2026-11-09.
- **CLI:** "Paste an image into the interactive composer, or pass one or more files on the command line" [raw]. Examples: `codex -i screenshot.png "…"` and `codex --image before.png,after.png "…"` [raw].
- **Multiple images and formats:** "separate paths with commas or repeat `--image`. Codex accepts common image formats, including PNG and JPEG." [raw]
- **IDE extension:** "Drag an image into the prompt composer while holding Shift" [raw].
- Caveat: the page gives no paste shortcut for Windows terminals.

### M-025 Codex command-line options and slash commands
- URL: https://learn.chatgpt.com/docs/developer-commands?surface=cli
- Accessed 2026-11-09.
- **/voice:** "When your CLI build and session support voice, use `/voice` or F8 to start or stop a voice conversation." [raw] Subcommands are `/voice mute`, `/voice stop` and `/voice settings` [raw].
- **Non-interactive images:** in `codex exec fork`, "add `--image` to attach images." "A prompt is required when using images" [raw].
- Caveats:
  - The availability of CLI voice is conditional ("when available") and is not tied to a stated plan or OS on this page.
  - This is a voice conversation, not dictation into the composer.

### M-026 ChatGPT Voice
- URL: https://learn.chatgpt.com/docs/features/voice
- Accessed 2026-11-09.
- **Where:** "ChatGPT Voice lets you talk through ideas and coordinate tasks in Chat, Work, and Codex in the ChatGPT desktop app." [raw]
- **Plans:** "available in the ChatGPT desktop app with ChatGPT Plus, Pro, Business, Edu, and Enterprise plans." [raw] Availability also depends on rollout.

## 6. Ollama vision

### M-027 Ollama Vision
- URL: https://docs.ollama.com/capabilities/vision
- Accessed 2026-11-09.
- **API:** "Provide an `images` array. SDKs accept file paths, URLs or raw bytes while the REST API expects base64-encoded image data." [raw]
- **Example:** `POST http://localhost:11434/api/chat` with `"images": ["<base64>"]` inside the user message [raw]. The example model is `gemma4`.
- Caveat: no limits on image count, size or resolution are documented on this page.

### M-028 Ollama API: Generate a chat message
- URL: https://docs.ollama.com/api/chat
- Accessed 2026-11-09.
- **Schema:** message `images` is "Optional list of inline images for multimodal models", with items typed "Base64-encoded image content" [raw].
- Caveat: no size limits are stated.

### M-029 Ollama library: qwen3-vl
- URL: https://ollama.com/library/qwen3-vl
- Accessed 2026-11-09. Model card; vendor claims.
- **Tags:** 2b (1.9GB), 4b (3.3GB), 8b/latest (6.2GB), 30b (20GB), 32b (21GB) and 235b (143GB), each "256K context window · Text, Image" [raw].
- **Ollama version:** "Qwen3-VL models require Ollama 0.12.7" [raw].
- **Model claims (not verified):**
  - Qwen3-VL "can operate computer and mobile interfaces — recognize GUI elements, understand button functions" [raw].
  - "OCR now supports 32 languages" [raw].
- Caveat: the local install's tag and size were not checked; no models were run.

## 7. Local speech-to-text

### M-030 OpenAI Whisper (GitHub openai/whisper)
- URLs:
  - https://github.com/openai/whisper (README, LICENSE and `whisper/tokenizer.py` via raw.githubusercontent.com)
  - HEAD commit 86098128c0b4.
- Accessed 2026-11-09.
- **Licence:** "Whisper's code and model weights are released under the MIT License." [raw] LICENSE: "MIT License / Copyright (c) 2022 OpenAI" [raw].
- **Model sizes:** "There are six model sizes, four with English-only versions" [raw]:

  | Size | Parameters | Required VRAM | Relative speed |
  |---|---|---|---|
  | tiny | 39 M | ~1 GB | ~10x |
  | base | 74 M | ~1 GB | ~7x |
  | small | 244 M | ~2 GB | ~4x |
  | medium | 769 M | ~5 GB | ~2x |
  | large | 1550 M | ~10 GB | 1x |
  | turbo | 809 M | ~6 GB | ~8x |

  Speeds were measured on an A100 with English audio [raw].
- **turbo:** "an optimized version of `large-v3`". It "is not trained for translation tasks" [raw].
- **Requirements:** "requires the command-line tool `ffmpeg`" [raw]. The page gives Windows install commands via choco and scoop.
- **Languages:**
  - The README defers to tokenizer.py for the language list. Performance "varies widely depending on the language" [raw].
  - tokenizer.py contains `"ko": "korean"` [raw].
  - My count of the `LANGUAGES` dict is 100 entries (counted, not quoted).

### M-031 faster-whisper (GitHub SYSTRAN/faster-whisper)
- URLs:
  - https://github.com/SYSTRAN/faster-whisper (README and LICENSE via raw.githubusercontent.com)
  - HEAD commit 846467d43611.
- Accessed 2026-11-09.
- **Licence:** "MIT License / Copyright (c) 2023 SYSTRAN" [raw].
- **Speed:** "up to 4 times faster than openai/whisper for the same accuracy while using less memory" [raw]. It gains further "with 8-bit quantization on both CPU and GPU." [raw]
- **Benchmarks** (13 min of audio, v1.1.0):
  - GPU, large-v2, int8: 59 s and 2926 MB VRAM [raw].
  - CPU, small, int8: 1m42s and 1477 MB [raw].
- **Code:** `WhisperModel(model_size, device="cpu", compute_type="int8")` [raw].
- **GPU requirements:** "cuBLAS for CUDA 12" and "cuDNN 9 for CUDA 12" [raw]. Windows DLLs are available via Purfview's whisper-standalone-win [raw].
- **No FFmpeg needed:** "Unlike openai-whisper, FFmpeg does **not** need to be installed on the system." [raw] PyAV is used instead.
- **Other features:** built-in Silero VAD (`vad_filter=True`) and `BatchedInferencePipeline` [raw]. Models auto-download from the Hugging Face Hub (Systran) [raw].
- Caveats:
  - The README benchmarks are vendor numbers.
  - The global rule applies: verify torch/CUDA after any install, and prefer `local_dir=` for HF downloads on Windows.

### Windows built-in voice typing
See M-014. It is built in, starts with Win+H, and is online (Azure Speech). It is not a local or offline STT option per that page. The developer API (M-013) needs MSIX package identity.

---

## Capability table (documentation only)

Each cell is "documented yes", "documented no" or "not documented", with its source ID. Nothing was tested.

| Tool | Typed text | Voice dictation | Image paste/attach | Image via API | Selected-region/pointer context |
|---|---|---|---|---|---|
| Claude Code VS Code ext | documented yes (M-004) | documented yes: microphone button, claude.ai account only, no Remote/SSH (M-003, M-004) | documented yes: paste from clipboard; Shift+drag for files (M-004) | not documented for the extension itself; underlying Claude API documented yes (M-008) | documented yes for editor text selection, open file and `Alt+K` @-mention with line range (M-004); screen region/pointer not documented |
| Claude Code CLI | documented yes (M-001) | documented yes: `/voice`, hold/tap `Space`, claude.ai account, native Windows supported, 20 languages incl. Korean (M-002, M-003) | documented yes: `Alt+V` on Windows/WSL (`Ctrl+V` also bound on WSL), drag-and-drop, image path (M-001, M-005) | not documented in fetched pages for `-p`; underlying Claude API documented yes (M-008) | documented yes for editor selection only when run in VS Code's integrated terminal (M-004); screen computer use documented macOS-only for CLI, so documented no on Windows (M-006, M-007) |
| Codex CLI | documented yes (M-023) | documented yes, conditionally: `/voice` or F8 voice conversation "when your CLI build and session support voice" (M-025) | documented yes: paste into composer; `-i`/`--image` flag (M-024) | documented yes: `codex exec … --image` (M-025) | not documented |
| Grok Bot | documented yes (M-016) | documented yes: dictation `Cmd/Ctrl+D`, live voice chat, voice memos (M-016) | documented yes: paste images, drag/attach files; 25 MB per image (M-016, M-018) | not documented: no Bot API page found (M-019, M-022) | not documented for the user's screen; the Bot uses its own cloud computer (M-017, M-019) |
| xAI API | documented yes (M-020) | separate STT endpoint documented yes: `/v1/stt`, grok-voice-transcribe-2.0, Korean (M-021) | n/a (API) | documented yes: `input_image`, base64 data URL or URL, jpg/png, 20 MiB (M-020) | not documented (only a `detail` parameter) (M-020) |
| Ollama (qwen3-vl) | documented yes (M-027, M-028) | not documented | n/a (API/CLI); CLI accepts an image path in `ollama run` (M-027) | documented yes: `images` array of base64 in `/api/chat` (M-027, M-028); limits not documented | not documented by Ollama; the model card claims GUI-element recognition (M-029, vendor claim) |
| Windows voice typing | n/a | documented yes: Win+H, online (Azure Speech), Korean supported (M-014) | n/a | developer API needs MSIX package identity (M-013) | documented only as "cursor in a text box" target (M-014); no region context |

---

## Conflicts / Not verified

- **C1 (CLI attachments).** The Desktop page (M-006) lists CLI "File attachments: Not available". Interactive mode (M-001) and Common workflows (M-005) document image paste, drag-and-drop and image paths in the CLI. Likely reading: the table means the attachment UI (the + button and PDFs), not images. Cite M-001 and M-005 for CLI images, and do not cite M-006 to claim the CLI lacks images.
- **C2 (Windows paste key).** M-001 names `Alt+V` for "Windows and WSL". M-005 says "`Ctrl+V`, or … `Alt+V` on Windows and WSL". Whether `Ctrl+V` pastes images in a native Windows terminal is not stated. UNVERIFIED; the safe instruction for Windows is `Alt+V`.
- **C3 (dictation key in VS Code).** The extension's dictation trigger is documented only as a "microphone button" (M-004). Whether hold-`Space` or `voice:pushToTalk` works in the extension chat panel is not documented. UNVERIFIED. This is consistent with the local finding of no contributed voice command.
- **C4 (Desktop app voice).** Claude Desktop (Claude Code tab) voice dictation is not documented in M-006. UNVERIFIED.
- **C5 (Claude Code plans for voice).** No plan tier is named; the stated requirement is a claude.ai account sign-in (not API key or Bedrock/Vertex/Foundry), and org policy can disable it. Any claim about "Pro/Max only" for voice would be UNVERIFIED.
- **C6 (Codex CLI voice).** M-025 documents `/voice`/F8 only conditionally. M-026 ties ChatGPT Voice to the desktop app and to plans. The availability of CLI voice on Windows is UNVERIFIED.
- **C7 (Codex Windows paste).** No Windows image-paste shortcut is documented (M-024). UNVERIFIED.
- **C8 (Grok Bot API).** I found no programmatic API for messaging a Bot. This is an absence in the fetched pages and index, not a stated "no". UNVERIFIED.
- **C9 (xAI vision models).** Only `grok-4.7` appears in the image-understanding examples. Other vision-capable model names are UNVERIFIED.
- **C10 (format mismatch).** Claude accepts JPEG/PNG/GIF/WebP (M-008); the xAI API accepts only jpg/jpeg and png (M-020). A shared screenshot pipeline should emit PNG.
- **C11 (Ollama limits).** Image count, size and resolution limits are not documented (M-027, M-028). The local qwen3-vl tag and size were not checked.
- **C12 (Whisper language count).** 100 is my count of tokenizer.py entries (M-030), not a quoted figure. Do not quote it as an OpenAI statement.
- **C13 (UIA tree pages).** M-011 is from search excerpts; I did not read the full page. M-012 (physical screen coordinates) is [raw].
- **C14 (UIA run-time list).** The M-010 run-time list names Windows 10 and Server 2019 but not Windows 11 explicitly. That UIA works on Windows 11 is inferred, not quoted.
- **C15 (Codex docs relocation).** Codex docs have moved from developers.openai.com/codex to learn.chatgpt.com (per the llms.txt links). Cite the learn.chatgpt.com URLs.
- **C16 (page dates).** The Claude Code, xAI and Ollama docs pages show no page date. Version strings cited inside the Claude Code pages run up to v2.1.309, which is at or below the user's v2.1.319.
