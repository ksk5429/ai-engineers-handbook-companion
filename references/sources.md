# Source register and bibliography {#bibliography}

Canonical register, edited only by the managing editor. Researchers' verified notes, with quotations and caveats, are in `references/research_notes/` (R1: agents, tools, MCP, MHS; R2: platforms, security, publishing; R3: providers, runtimes, research systems; R4: multimodal interfaces; R5: sources and extra quotations for the core chapters B1 and O1). Every source below was fetched on the access date by a researcher subagent working from the live page; quotes marked [raw] in the notes were read in raw page text.

**Fact types used in the book:** *documented fact* (cites an ID below), *observed result* (cites an evidence record in `reviews/evidence/`), *recommendation* (labelled, with reasons), *illustration* (labelled constructed), *assumption* (listed in `curriculum/knowledge_gaps.md`).

**Quotation style:** quotations are verbatim. A capital letter changed at the start of a quotation is marked with square brackets ("[t]he Claude API ..."); omitted words are marked with an ellipsis. Straight or curly apostrophes and the style of nested quotation marks follow the book's style and are not marked; link markup in the source page is dropped.

| ID | Title | Publisher / author | URL or DOI | Date / version | Accessed | Supports |
|---|---|---|---|---|---|---|
| S-001 | Building effective agents | Anthropic ("Written by Erik S. and Barry Zhang") | https://www.anthropic.com/engineering/building-effective-agents | 19 Dec 2024 | 2026-11-09 | E1: workflow vs agent definitions; "start simple"; tool design |
| S-002 | Subagents | Anthropic, Claude Code docs | https://code.claude.com/docs/en/sub-agents | undated | 2026-11-09 | PROJECT.md roles; planned F-series |
| S-003 | Hooks reference; Automate actions with hooks | Anthropic, Claude Code docs | https://code.claude.com/docs/en/hooks | undated | 2026-11-09 | planned E/I-series: text vs enforcement; O1: hook kinds, best-effort `if` filter |
| S-004 | Configure permissions | Anthropic, Claude Code docs | https://code.claude.com/docs/en/permissions | undated | 2026-11-09 | O1: permission rules are enforced by the harness |
| S-005 | Settings | Anthropic, Claude Code docs | https://code.claude.com/docs/en/settings | undated | 2026-11-09 | O1: committed rules in a cloned repository |
| S-006 | Memory (CLAUDE.md) | Anthropic, Claude Code docs | https://code.claude.com/docs/en/memory | undated | 2026-11-09 | B1, O1: instructions are context, not enforced configuration; B1: auto memory, 200-line/25KB load limit (extra quotes in R5) |
| S-007 | Tool use with Claude; Define tools; Handle tool calls | Anthropic, Claude API docs | https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview | undated; samples use `anthropic-version: 2026-10-21` | 2026-11-09 | E1, B1, O1: tool definitions, tool_use/tool_result, client vs server tools, untrusted tool content |
| S-008 | Structured outputs; Strict tool use | Anthropic, Claude API docs | https://platform.claude.com/docs/en/build-with-claude/structured-outputs | undated; status stable | 2026-11-09 | E1: provider-side schema enforcement |
| S-009 | What is the Model Context Protocol (MCP)? | MCP project | https://modelcontextprotocol.io/docs/getting-started/intro | undated | 2026-11-09 | planned I-series; O1: MCP definition |
| S-010 | MCP Specification, revision 2026-07-28 | MCP project | https://modelcontextprotocol.io/specification/2026-07-28 | 2026-07-28 (current) | 2026-11-09 | planned I-series: roles, primitives, transports; O1: consent principles not enforced by the protocol |
| S-011 | MCP Authorization (2026-07-28) | MCP project | https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization | 2026-07-28 | 2026-11-09 | planned I/O-series |
| S-012 | MCP joins the Agentic AI Foundation | MCP blog | https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/ | 9 Dec 2025 | 2026-11-09 | planned: governance |
| S-013 | Model Hardware Standard | Model Hardware Standard site | https://www.modelhardwarestandard.com/ | undated; no version stated | 2026-11-09 | planned P-series: MHS status |
| S-014 | Previewing the Model Hardware Standard | Anthropic | https://www.anthropic.com/news/model-hardware-standard-research-preview | 27 Aug 2026 | 2026-11-09 | planned P-series: research preview, access by application |
| S-015 | Glossary | Anthropic, Claude API docs | https://platform.claude.com/docs/en/about-claude/glossary | undated | 2026-11-09 | B1: pretraining, fine-tuning, RLHF, no fine-tuning in the Claude API, temperature and non-determinism, tokens, RAG |
| S-016 | Context windows | Anthropic, Claude API docs | https://platform.claude.com/docs/en/build-with-claude/context-windows | undated; compaction in beta for Claude 4.6 and later models | 2026-11-09 | B1: context window, accumulation of turns, context rot, "prompt is too long", rolling first-in-first-out, compaction |
| S-017 | Models overview | Anthropic, Claude API docs | https://platform.claude.com/docs/en/about-claude/models/overview (page metadata: https://platform.claude.com/docs/en/models/overview) | undated | 2026-11-09 | B1: reliable knowledge cutoff vs training data cutoff |
| S-018 | Embeddings | Anthropic, Claude API docs | https://platform.claude.com/docs/en/build-with-claude/embeddings | undated | 2026-11-09 | B1: text embeddings, semantic search, no Anthropic embedding model |
| R-001 | AI RMF: Generative AI Profile (NIST AI 600-1) | NIST | doi:10.6028/NIST.AI.600-1 | 26 Jul 2024 | 2026-11-09 | O1: 12 risk categories (five named) |
| R-002 | OWASP Top 10 for LLM Applications 2025 | OWASP GenAI Security Project | https://genai.owasp.org/llm-top-10/ | released 17 Nov 2024 | 2026-11-09 | E1, O1: LLM01 prompt injection (direct and indirect; extra quote in R5), LLM02, LLM06 excessive agency |
| R-003 | JSON Schema 2020-12 (Core, Validation); RFC 8259 | JSON Schema org; IETF (T. Bray, ed.) | https://json-schema.org/specification ; RFC 8259 | 2020-12; Dec 2017 (STD 90) | 2026-11-09 | E1: schemas constrain structure |
| R-004 | Firebase: test Security Rules with the emulator; Emulator Suite; pricing; Admin SDK | Google | https://firebase.google.com/docs/firestore/security/test-rules-emulator | undated; @firebase/rules-unit-testing 6.0.0 | 2026-11-09 | planned N-series web app |
| R-005 | Google Play Books Partner Center help: Book file guidelines; EPUB files; ISBNs; Quickstart; Upload & update files; Content policies | Google | https://support.google.com/books/partner/answer/3424254 (and 3316879, 3431108, 9261664, 14173419, 1067634) | undated | 2026-11-09 | `guides/G-01_publishing_google_play_books.md` |
| R-006 | EPUBCheck; EPUB 3.3 | W3C / DAISY | https://github.com/w3c/epubcheck ; https://www.w3.org/TR/epub-33/ | EPUBCheck v5.4.0 (15 Sep 2026); EPUB 3.3 REC (republished 13 Jan 2026) | 2026-11-09 | G-01; release gate |
| R-007 | Pandoc User's Guide (EPUB) | John MacFarlane | https://pandoc.org/MANUAL.html | latest release 3.13; local 3.10 used | 2026-11-09 | build: EPUB 3 output, metadata |
| R-008 | Python 3.12 docs: unittest; hashlib | Python Software Foundation | https://docs.python.org/3.12/library/unittest.html | 3.12.16 docs; 3.12 security-only | 2026-11-09 | E1 tooling |

**Providers, runtimes and research systems** (researcher R3, quotes read in raw page text):

| ID | Title | Publisher / author | URL or DOI | Date / version | Accessed | Supports |
|---|---|---|---|---|---|---|
| T-001 | Manage costs effectively | Anthropic, Claude Code docs | https://code.claude.com/docs/en/costs | undated | 2026-11-09 | planned C1: `/cost` alias of `/usage`, local estimate, subagent usage; B1: auto-compaction |
| T-002 | Codex as a platform | OpenAI (blog) | https://developers.openai.com/blog/codex-as-a-platform | per R3 notes | 2026-11-09 | planned E2 |
| T-003 | Codex CLI documentation (AGENTS.md, exec, sandbox, skills, MCP, hooks, resume, SDK, app-server) | OpenAI | docs now redirect to https://learn.chatgpt.com/docs/ (HTTP 308) | stable 0.167.0 (6 Nov 2026); local 0.166.0 | 2026-11-09 | planned E2, G1, Q1 |
| T-004 | OpenAI Agents SDK | OpenAI | https://developers.openai.com/api/docs/guides/agents/sdk | `openai-agents` 0.24.0; `@openai/agents` 0.21.0 | 2026-11-09 | planned F2 |
| T-005 | Grok Bot documentation | xAI ("SpaceXSI (xAI)") | https://docs.x.ai/grok-bot/overview | undated | 2026-11-09 | planned E2, Q1: end-user product; no task-and-result API found |
| T-006 | xAI API: function calling, structured outputs | xAI | https://docs.x.ai/developers/tools/function-calling | undated | 2026-11-09 | planned G1 |
| T-007 | Ollama docs: tool calling, API usage fields, think, context length, `ollama ps`, cloud models | Ollama | https://docs.ollama.com/capabilities/tool-calling ; also https://docs.ollama.com/api/chat (`num_ctx`, `top_k`, `seed`), https://docs.ollama.com/api/authentication, https://docs.ollama.com/cloud, https://docs.ollama.com/faq (pages listed in R3 and R5) | undated; local runtime 0.40.15 | 2026-11-09 | G-02; E1 live route; B1: `num_ctx`, context defaults, `top_k` and `seed`; O1: cloud models via the local API, cloud tags, cloud opt-out |
| T-008 | Cache strategies (KV cache) | Hugging Face Transformers docs | https://huggingface.co/docs/transformers/main/kv_cache | main branch | 2026-11-09 | planned D3 |
| T-009 | PyTorch Profiler recipe | PyTorch | https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html | undated | 2026-11-09 | planned D2 |
| T-010 | AlphaEvolve | Google DeepMind | arXiv:2506.13131 | 16 Jun 2025 | 2026-11-09 | planned K1, L1 |
| T-011 | Darwin Gödel Machine | Sakana AI and J. Clune's lab (UBC) | arXiv:2505.22954; https://sakana.ai/dgm/ | v3 12 Mar 2026 | 2026-11-09 | planned K1: objective hacking documented |
| T-012 | Towards an AI co-scientist (v2: Accelerating scientific discovery with Co-Scientist) | Google | arXiv:2502.18864 | v2 29 Jun 2026 | 2026-11-09 | planned L1 |

**Multimodal interfaces** (researcher R4):

| ID | Title | URL | Accessed | Supports |
|---|---|---|---|---|
| M-001 | Interactive mode (Claude Code docs) | https://code.claude.com/docs/en/interactive-mode | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-002 | Commands (Claude Code docs) | https://code.claude.com/docs/en/commands | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-003 | Voice dictation (Claude Code docs) | https://code.claude.com/docs/en/voice-dictation | 2026-11-09 | Q1; O1; mm01 CAPABILITIES |
| M-004 | VS Code extension (Claude Code docs) | https://code.claude.com/docs/en/vs-code | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-005 | Common workflows: "Work with images" (Claude Code docs) | https://code.claude.com/docs/en/common-workflows | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-006 | Claude Code Desktop (Claude Code docs) | https://code.claude.com/docs/en/desktop | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-007 | Computer use (CLI) (Claude Code docs) | https://code.claude.com/docs/en/computer-use | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-008 | Vision (Claude API docs) | https://platform.claude.com/docs/en/build-with-claude/vision | 2026-11-09 | Q1; B1 (visual-token sentence in R5); mm01 CAPABILITIES |
| M-009 | Screen capture (Windows.Graphics.Capture) | https://learn.microsoft.com/en-us/windows/apps/develop/media-authoring-processing/screen-capture | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-010 | UI Automation (entry page) | https://learn.microsoft.com/en-us/windows/desktop/winauto/entry-uiauto-win32 | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-011 | UI Automation tree overview and specification (Microsoft Learn search excerpts) | https://learn.microsoft.com/windows/win32/winauto/uiauto-treeoverview | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-012 | Automation element property identifiers | https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-automation-element-propids | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-013 | Speech recognition in Windows apps | https://learn.microsoft.com/en-us/windows/apps/develop/input/speech-recognition | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-014 | Windows voice typing (Microsoft Support) | https://support.microsoft.com/en-us/windows/use-voice-typing-to-talk-instead-of-type-on-your-pc-fec94565-c4bd-329d-e59a-af033fa5689f | 2026-11-09 | Q1; O1; mm01 CAPABILITIES |
| M-015 | High DPI desktop application development on Windows | https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-016 | Grok Bot: Message and collaborate | https://docs.x.ai/grok-bot/chat-and-collaboration | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-017 | Grok Bot overview | https://docs.x.ai/grok-bot/overview | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-018 | Grok Bot: Files and results | https://docs.x.ai/grok-bot/files-and-results | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-019 | Grok Bot FAQ and "Use the computer and apps" | https://docs.x.ai/grok-bot/faq | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-020 | xAI API: Image Understanding | https://docs.x.ai/developers/model-capabilities/images/understanding | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-021 | xAI API: Speech to Text | https://docs.x.ai/developers/model-capabilities/audio/speech-to-text | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-022 | xAI docs index | https://docs.x.ai/llms.txt | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-023 | Codex CLI | https://learn.chatgpt.com/docs/codex/cli | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-024 | Image inputs (Codex/ChatGPT docs, CLI surface) | https://learn.chatgpt.com/docs/image-inputs?surface=cli | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-025 | Codex command-line options and slash commands | https://learn.chatgpt.com/docs/developer-commands?surface=cli | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-026 | ChatGPT Voice | https://learn.chatgpt.com/docs/features/voice | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-027 | Ollama Vision | https://docs.ollama.com/capabilities/vision | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-028 | Ollama API: Generate a chat message | https://docs.ollama.com/api/chat | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-029 | Ollama library: qwen3-vl | https://ollama.com/library/qwen3-vl | 2026-11-09 | Q1; mm01 CAPABILITIES |
| M-030 | OpenAI Whisper (GitHub openai/whisper) | https://github.com/openai/whisper | 2026-11-09 | Q1; O1 (licence statement only); mm01 CAPABILITIES |
| M-032 | Moving from Mac (Unix) to Windows: keyboard shortcuts ("Capture a region or window: Windows key+Shift+S") | https://learn.microsoft.com/windows/dev-environment/mac-to-windows#keyboard-shortcuts | 2026-11-09 | Q1 everyday capture step (found by the managing editor via the Microsoft Learn search tool) |
| M-031 | faster-whisper (GitHub SYSTRAN/faster-whisper) | https://github.com/SYSTRAN/faster-whisper | 2026-11-09 | Q1; mm01 CAPABILITIES |

## Conflicts and open questions carried from the notes

- Google Play Books: one help page says the EPUB "must be validated by EpubCheck", another says "should". This project treats a clean EPUBCheck run as a release gate (R-005, R-006).
- Google Play Books: no policy on disclosing AI-generated content was found for books (R-005f). Check Partner Center before publishing (knowledge gap G-13).
- The MHS site publishes no specification version, schema or SDK; it is a limited research preview (S-013, S-014). The book must not say MHS builds on MCP; MCP is one of its three access mechanisms (S-014).
- The local pandoc is 3.10; the latest release is 3.13 (R-007). Builds record the version used.
