# R3 Platforms, runtimes, profiling, and research systems: research notes

Researcher pass for "AI Engineer's Handbook" (folder 73). Access date for every item: **2026-11-09**.

**How the pages were read.** Every page except one was downloaded with `curl` as raw Markdown (the `.md` twins that the Mintlify, OpenAI and xAI doc sites serve) or as raw HTML that I turned into plain text locally. So every quote marked **[raw]** was read in the page's own text, with no summarising tool in between. The one exception is a single WebSearch call, used only to *discover* the 2026 Google Cloud / DeepMind pages. Those pages were then downloaded raw, and nothing below is quoted from search snippets. No model was run, no paid or inference API was called, and nothing was installed. The only metadata lookups were read-only public GETs to the GitHub releases/repo API, PyPI JSON and the npm registry.

**Redirect note.** The `developers.openai.com/codex/...` doc URLs now return HTTP 308 to `learn.chatgpt.com/docs/...`. Checked: `/codex/noninteractive` goes to `/docs/non-interactive-mode`, `/codex/guides/agents-md` to `/docs/agent-configuration/agents-md`, and `/codex/cli` to `/docs/codex/cli`. The book should cite the learn.chatgpt.com URLs.

---

## T-001 Claude Code: Manage costs effectively

- **Publisher:** Anthropic (Claude Code docs)
- **URL:** https://code.claude.com/docs/en/costs (raw: `costs.md`). Supporting pages: https://code.claude.com/docs/en/commands (`/cost` alias) and https://code.claude.com/docs/en/sub-agents
- **Date/version shown:** no page date. The page cites version gates up to "Claude Code v2.1.305".
- **Verified facts**
  - `/usage` is the cost and usage command, and `/cost` is now an alias for it. Commands page: "`/cost` | Alias for `/usage`" [raw]; "`/cost` and `/stats` are aliases" [raw].
  - The dollar figure is computed on the client and is only an estimate: "Claude Code computes the dollar figure locally from token counts at list price, unless a `modelPricing` table is in effect." [raw]
  - The Session block breaks usage down per model into input, output, cache read and cache write. Example: "claude-sonnet-4-6: 1.2k input, 5.3k output, 940.0k cache read, 50.0k cache write ($0.55)" [raw]
  - `/clear` resets the session totals: "These totals reset when `/clear` starts a new session, so the next session's total cost starts at $0." [raw] (Before v2.1.211 they kept accumulating.)
  - A prompt cache statistics line, "Prompt cache (main)", reports cache hit share, misses and warm/cold state. It "covers the main conversation only, not subagents." [raw] It requires v2.1.251 or later.
  - Caching and compaction happen automatically: "Claude Code automatically optimizes costs through prompt caching… and auto-compaction, which summarizes conversation history when approaching context limits." [raw] Custom focus is available via "`/compact Focus on code samples and API usage`" [raw].
  - Compaction has a cost of its own: "`/compact` reads the conversation it summarizes, so compacting a large context is itself a large request… `/clear` costs nothing" [raw]
  - Subagents: "The subagent's own requests still draw on your usage." [raw] Sub-agents page: "Each subagent runs in its own context window… It also sends its own requests, which count toward the same usage limits" [raw]. Agent teams: "approximately 7x more tokens than standard sessions when teammates run in plan mode" [raw].
- **Caveats:** The figures are list-price estimates, not invoices. The enterprise averages ("around $13 per developer per active day") are Anthropic's own reported figures. Thinking tokens "are billed as output tokens" [raw]. The page names Opus 5.5, Sonnet 5.5, Haiku 5.5 and Fable as models where thinking cannot be turned off.

## T-002 OpenAI: Codex as a platform (blog)

- **Publisher/authors:** OpenAI Developers blog; Nicolas Bonamy, Derrick Choi
- **URL:** https://developers.openai.com/blog/codex-as-a-platform
- **Date shown:** Aug 19, 2026
- **Verified facts**
  - The harness is open source: "The open-source Codex harness is what powers all these experiences." [raw]
  - The harness's responsibilities: "manage conversation state, stream execution, use tools, enforce configured sandbox and approval policies, and carry work across turns." [raw]
  - The app-server protocol lets "applications can create threads, start turns, receive events, and handle approval requests." [raw]
  - There are three integration layers: "codex exec for noninteractive jobs, the Codex SDK for programmatic agent workflows, or Codex app-server for applications that need persistent conversations…" [raw]
  - What is open and what is not: "The open-source layer is the harness and integration surface; model access and managed services remain separate." [raw]
  - Harness claim: "on ARC-AGI-3, retained reasoning and context compaction raised GPT-5.6 Sol's score from 13.3% to 38.3% while reducing output tokens sixfold." [raw]
- **Caveats:** The ARC-AGI-3 figure and the customer figures (Thrive/Crete, "7,000 returns") are vendor claims with no linked evaluation protocol. "Relay" is a sample app that runs on fictional seeded data.

## T-003 OpenAI Codex CLI docs (instructions, exec, sandbox/approvals, skills, MCP, hooks, resume, SDK, app-server, versions)

- **Publisher:** OpenAI (docs now hosted at learn.chatgpt.com)
- **URLs:**
  - AGENTS.md: https://learn.chatgpt.com/docs/agent-configuration/agents-md
  - Non-interactive mode: https://learn.chatgpt.com/docs/non-interactive-mode
  - Sandbox: https://learn.chatgpt.com/docs/sandboxing
  - Approvals: https://learn.chatgpt.com/docs/agent-approvals-security
  - Skills: https://learn.chatgpt.com/docs/build-skills
  - MCP: https://learn.chatgpt.com/docs/extend/mcp
  - Hooks: https://learn.chatgpt.com/docs/hooks
  - CLI commands: https://learn.chatgpt.com/docs/developer-commands?surface=cli
  - SDK: https://learn.chatgpt.com/docs/codex-sdk
  - App Server: https://learn.chatgpt.com/docs/app-server
  - Open source: https://learn.chatgpt.com/docs/open-source
  - Releases: https://github.com/openai/codex/releases
- **Version shown:**
  - GitHub releases: the latest stable is `rust-v0.167.0` (2026-11-06), with prereleases up to `rust-v0.169.0-alpha.3` (2026-11-07).
  - npm `@openai/codex` 0.167.0; npm `@openai/codex-sdk` 0.167.0; PyPI `openai-codex` 0.167.0 (2026-11-06).
  - The local install is codex-cli 0.166.0 (not run). It is one minor version behind stable.
  - **Version scheme:** `0.MINOR.PATCH`, with `-alpha.N` prereleases and GitHub tags prefixed `rust-v`. The SDK packages carry the same version number as the CLI.
- **Verified facts**
  - **Instruction file:** "Codex reads `AGENTS.md` files before doing any work." [raw]
    - Precedence: global `~/.codex` (`AGENTS.override.md`, then `AGENTS.md`), then each directory from the project root down to the cwd, with "at most one file per directory" [raw].
    - Size cap: "stops adding files once the combined size reaches the limit defined by `project_doc_max_bytes` (32 KiB by default)." [raw]
    - Fallback names come from `project_doc_fallback_filenames`.
  - **Non-interactive:** "Non-interactive mode lets you run Codex from scripts… You invoke it with `codex exec`." [raw]
    - Output streams: "Codex streams progress to `stderr` and prints only the final agent message to `stdout`." [raw]
    - Default sandbox: "By default, `codex exec` runs in a read-only sandbox." [raw]
    - `--json` gives JSONL events (`thread.started`, `turn.started`, `turn.completed`, `turn.failed`, `item.*`, `error`). `turn.completed` carries `usage` with `input_tokens`, `cached_input_tokens`, `output_tokens` and `reasoning_output_tokens`.
    - `--output-schema` takes a JSON Schema for the final answer, and `-o/--output-last-message` writes the final message to a file.
    - Removed flag: "`--full-auto` is no longer supported." [raw]
    - Git check: "Codex requires commands to run inside a Git repository… Override this check with `codex exec --skip-git-repo-check`" [raw]
  - **Resume:** "`codex exec resume --last "fix the race conditions you found"`" [raw], or `codex exec resume <SESSION_ID>`. `codex exec fork <SESSION_ID>` copies a session. For interactive use, `codex resume` and `codex fork` scope `--last` to the cwd unless `--all` is given.
  - **Sandbox modes:** `read-only`, `workspace-write` and `danger-full-access`. "Sandboxing and approvals are different controls… The sandbox defines technical boundaries. The approval policy decides when the agent must stop and ask" [raw]
    - Approval policies: `on-request` and `never`, plus a `granular` policy table.
    - Removed value: "Codex and ChatGPT Work no longer support `untrusted` as a selectable approval policy." [raw]
    - `approvals_reviewer` is `user` (the default) or `auto_review`.
    - Full bypass flag: `--dangerously-bypass-approvals-and-sandbox` (alias `--yolo`).
    - Enforcement differs by platform: Seatbelt on macOS, bubblewrap on Linux/WSL2, and a native Windows sandbox.
  - **Skills:** "Skills build on the open agent skills standard" [raw]. A skill is "a directory with a `SKILL.md` file… must include `name` and `description`" [raw].
    - Codex scans `.agents/skills` in every directory from the cwd up to the repo root, plus `$HOME/.agents/skills`.
    - Progressive disclosure: the initial skills list "uses at most 2% of the model's context window, or 8,000 characters" [raw].
  - **MCP:** Codex supports STDIO servers and Streamable HTTP servers (bearer token and OAuth). Configuration lives in `config.toml` (`[mcp_servers.<name>]`), or is added with `codex mcp add <name> -- <command>`.
    - "Codex reads the MCP `instructions` field returned during initialization" [raw]
    - The SDK page says "The `codex mcp-server` command and standalone `codex-mcp-server` binary have been removed." [raw] Codex can therefore no longer be exposed *as* an MCP server. Use app-server instead.
  - **Hooks:** they exist. "Hooks are an extensibility framework for Codex. They let you run scripts or MCP tools during the agentic loop" [raw].
    - Events include PreToolUse, PermissionRequest, PostToolUse, PreCompact/PostCompact, UserPromptSubmit, Stop, PreModelRequest/PostModelRequest, SessionStart/SessionEnd and SubagentStart/SubagentStop.
    - Hooks are configured in `hooks.json` or in inline `[hooks]` tables in `config.toml`.
    - "Non-managed hooks must be reviewed and trusted before they run." [raw]
  - **App-server (harness integration):** "Codex app-server is the interface Codex uses to power rich clients (for example, the Codex VS Code extension)." [raw]
    - Protocol: "supports bidirectional communication using JSON-RPC 2.0 messages (with the `"jsonrpc":"2.0"` header omitted on the wire)" [raw]
    - Transports: stdio JSONL (the default); WebSocket ("experimental and unsupported" [raw]); Unix socket.
    - Methods include `thread/start` and `turn/start`, with notifications such as `turn/started`.
    - `codex app-server generate-ts` and `generate-json-schema` emit version-specific schemas.
  - **SDK:** the TypeScript package is `@openai/codex-sdk` (Node 18+): `new Codex().startThread().run(...)` and `resumeThread(id)`. The Python package is `openai-codex` (Python 3.10+). It "controls the local Codex app-server over JSON-RPC" [raw] and "Published SDK builds include a pinned Codex CLI runtime dependency." [raw]
  - **Open source:** the CLI, SDK and app-server are in `openai/codex`. The IDE extension and Codex cloud are "Not open source" [raw]. The repo "doesn't accept external code contributions or pull requests." [raw]
- **Caveats:**
  - Flag names have changed recently (`--full-auto` removed, `untrusted` retired, `codex mcp-server` removed). The book should pin a version, for example "as of 0.167.0", and print no flag table without that pin.
  - The Python SDK page says "With Codex CLI 0.166.0 or later, use the thread's saved model provider to resume it" [raw]. The local 0.166.0 install therefore meets that gate.

## T-004 OpenAI Agents SDK

- **Publisher:** OpenAI API docs
- **URLs:** guide https://developers.openai.com/api/docs/guides/agents/sdk. Subpages: quickstart, running-agents, orchestration, guardrails-approvals, integrations-observability (all under `/api/docs/guides/agents/`).
- **Version shown:** none on the page. Registry: PyPI `openai-agents` 0.24.0 (uploaded 2026-10-15, requires Python >=3.10); npm `@openai/agents` 0.21.0.
- **Verified facts**
  - Languages: the guide links the TypeScript SDK (`openai/openai-agents-js`) and the Python SDK (`openai/openai-agents-python`). Install with "`npm install @openai/agents zod`" [raw] / "`pip install openai-agents`" [raw]. The Python import name is `agents`.
  - **Division of labour:** "Use the SDK track when your server owns deployment, tool implementations, state storage, and approval decisions, while the SDK runs the agent loop and invokes those tools." [raw]
  - **Agent loop:** "One SDK run is one application-level turn." [raw] The loop calls the model, runs tool calls, switches agent on a handoff, and returns when there is a final answer with no more tool work.
  - **Handoffs vs agents-as-tools:** "Handoffs… A specialist should take over the conversation" vs "Agents as tools… The manager keeps ownership of the reply" [raw]
  - **Guardrails:** input, output and tool guardrails, plus human-in-the-loop approvals: "Pause before side effects like cancellations, edits, shell commands, or sensitive MCP actions" [raw]
  - **Sessions/state:** there are four strategies: replay history yourself, `session` (e.g. `SQLiteSession`, `MemorySession`), `conversationId` (Conversations API), or `previous_response_id`. "In most applications, pick one strategy per conversation." [raw]
  - **Tracing:** "Tracing is built into the Agents SDK and is enabled by default in the normal server-side SDK path." [raw]
  - Runtime comparison: "The Agents SDK runs in your application; the Agents API runs a managed harness in OpenAI's service." [raw]
- **What the app must still implement:** tool implementations, deployment, state storage (or a choice of server-managed state), approval decisions, and evals. This follows from the "Use the SDK track when your server owns…" sentence.
- **Caveats:** The guide pages show no SDK version. The version numbers above come from the registries, not the docs. The SDK is still 0.x.

## T-005 xAI (now branded "SpaceXSI (xAI)"): Grok Bot

- **Publisher:** docs.x.ai (the docs header reads "Official SpaceXSI (xAI) developer documentation" [raw])
- **URLs:**
  - Overview: https://docs.x.ai/grok-bot/overview
  - FAQ: https://docs.x.ai/grok-bot/faq
  - Skills and routines: https://docs.x.ai/grok-bot/skills-routines-and-automations
  - Teams and enterprises: https://docs.x.ai/grok-bot/teams-and-enterprises
  - Inference hooks: https://docs.x.ai/grok-bot/inference-hooks
  - All 26 grok-bot pages listed in https://docs.x.ai/llms.txt were downloaded and searched.
- **Date shown:** none
- **Verified facts**
  - What it is: "Grok Bot is your proactive AI teammate." [raw] "It's an agent with access to a real computer in the cloud" [raw]
  - It is a separate product from Grok: "Grok (the chat app from SpaceXSI) and Grok Bot are two different apps… Grok Bot signs in with your Cursor account." [raw] Billing and identity also run through Cursor.
  - Interfaces: "Use the Grok Bot desktop app on macOS, Windows, or Linux, or the companion app on iOS or Android." [raw] It can also be reached through X Chat, by tagging @bot on X, and through a shared Bot in Slack.
  - There is no model choice: "Grok Bot picks the model for each task, and there is no model picker." [raw] It may use "a first-party SpaceXSI model or a third-party model" [raw].
  - It can call out to tools: "supports custom tooling, so it can interact with any MCP or API." [raw]
  - **Programmatic inbound interface, limited to a webhook trigger:** a routine can be started "when something happens… a Slack message, a GitHub, Linear, Sentry, or PagerDuty event, an email… or a webhook call." [raw]
    - How the webhook works: "Send an HTTP POST to that URL with the header and, optionally, a JSON body" with `Authorization: Bearer <key>` [raw].
    - "A `200` response means Grok Bot accepted the call and started a run, not that the Bot has finished; check the Bot's chat for the result." [raw]
  - Admin automation goes through Cursor's APIs: "Enable Grok Bot and manage capabilities… through the Admin API" (cursor.com) [raw]. Computers are managed through the Organization API (`admin:*` key).
  - Enterprise "inference hooks" send each governed model request to an org-run server for an allow or deny verdict (beta).
- **Conclusion for the book:** among the 26 pages, I found **no documented API that lets you send a Bot a task and get its result back** (no request/response API or SDK).
  - What exists: (a) a fire-and-forget webhook trigger on routines; (b) Cursor Admin and Organization APIs for administration; (c) chat surfaces (desktop, mobile, X, Slack).
  - Grok Bot is **not** the xAI inference API.
- **Caveats:** This is a negative finding, based on full-text search of every grok-bot page listed in llms.txt (on the terms programmatic, REST API, webhook, SDK and API). Pages not listed in llms.txt were not checked.

## T-006 xAI API: function calling, structured outputs, base URL, authentication

- **Publisher:** docs.x.ai
- **URLs:**
  - Function calling: https://docs.x.ai/developers/tools/function-calling
  - Structured outputs: https://docs.x.ai/developers/model-capabilities/text/structured-outputs
  - REST overview: https://docs.x.ai/developers/rest-api-reference/inference
  - Legacy Chat Completions: https://docs.x.ai/developers/model-capabilities/legacy/chat-completions
- **Date/version shown:** none. The model name in the examples is `grok-4.7`.
- **Verified facts**
  - OpenAI compatibility: "The SpaceXSI REST API is compatible with the OpenAI REST API." [raw]
  - Base URL and auth: inference at `https://api.x.ai` with "`Authorization: Bearer <API key>`" [raw]. Management APIs live at `https://management-api.x.ai` and use a Management API key. The OpenAI-SDK examples set `base_url="https://api.x.ai/v1"` and read `XAI_API_KEY`.
  - The primary API is now Responses: "Chat Completions is offered as a legacy endpoint." [raw] The function-calling examples use `POST /v1/responses` with flat tools (`{"type":"function","name":…,"parameters":…}`). A call comes back as an output item of `type == "function_call"` with `call_id` and a JSON-string `arguments`. The result is returned as `{"type":"function_call_output","call_id":…}` plus `previous_response_id`.
  - Streaming caveat: "With streaming, the function call is returned in whole in a single chunk, not streamed across chunks." [raw]
  - `tool_choice`: `"auto"` (default), `"required"`, `"none"`, or a forced function given as `{"type": "function", "function": {"name": "..."}}` [raw].
  - Parallel calls: "By default, parallel function calling is enabled… Disable with `parallel_tool_calls: false`" [raw]. The limit is "max 350 tools per request" [raw].
  - Schemas: the parameters root must be an object (or an anyOf/oneOf of objects). Otherwise the tool "is rejected with a `400` error that names the tool." [raw]
  - Structured outputs: `response_format.type = "json_schema"` (also `json_object` and `text`). "When using supported schema features, the response is guaranteed to match your schema." [raw]
  - Tool arguments are strict by default: "SpaceXSI models will always generate tool call arguments that strictly conform to the tool's input JSON Schema (the `strict` flag is implicitly always `true`)." [raw]
  - Built-in tools such as `web_search` and `x_search` "execute automatically on SpaceXSI servers", while custom tools "pause execution and return to you" [raw].
- **Caveats:**
  - The forced `tool_choice` example uses the nested Chat-Completions shape (`function.name`), but the page's tools use the flat Responses shape. Test which shape `/v1/responses` accepts before printing it.
  - "Structured outputs with tools is only available for supported Grok 4 family models." [raw]

## T-007 Ollama: tool calling, /api/chat usage fields, think, context length, `ollama ps`, cloud

- **Publisher:** Ollama docs
- **URLs:**
  - Tool calling: https://docs.ollama.com/capabilities/tool-calling
  - API chat: https://docs.ollama.com/api/chat (OpenAPI)
  - Usage: https://docs.ollama.com/api/usage
  - Thinking: https://docs.ollama.com/capabilities/thinking
  - Context length: https://docs.ollama.com/context-length
  - FAQ: https://docs.ollama.com/faq
  - api/ps: https://docs.ollama.com/api/ps
  - Cloud: https://docs.ollama.com/cloud
  - Authentication: https://docs.ollama.com/api/authentication
  - OpenAI compatibility: https://docs.ollama.com/api/openai-compatibility
  - Tool-model listing: https://ollama.com/search?c=tools
- **Version shown:** the OpenAPI spec header shows "version: 0.1.0" (the spec version, not the server version). No server version was checked, because nothing was run.
- **Verified facts**
  - **Request shape (`POST http://localhost:11434/api/chat`):** `model`, `messages`, `stream`, and `tools: [{"type":"function","function":{"name","description","parameters"}}]` (the OpenAI-style nested shape). Local API: "does not require authentication." [raw]
  - **Response/tool-call shape:**
    - The assistant message carries `tool_calls`. OpenAPI `ToolCall` is `function{name, description, arguments}`, where `arguments` is a "JSON object of arguments to pass to the function" [raw]. It is an object, not a JSON string.
    - The doc's follow-up example echoes `"tool_calls":[{"type":"function","function":{"index":0,"name":"get_temperature","arguments":{"city":"New York"}}}]` [raw].
    - The tool result goes back as `{"role": "tool", "tool_name": "get_temperature", "content": "22°C"}` [raw]. It is matched by `tool_name`, and the schema shows no call id.
  - Parallel and multi-turn tool calling ("Agent loop") are documented. When streaming, "gather every chunk of `thinking`, `content`, and `tool_calls`, then return those fields together" [raw].
  - **Usage fields:**
    - `total_duration`, `load_duration`, `prompt_eval_count`, `prompt_eval_cached_count`, `prompt_eval_duration`, `eval_count` and `eval_duration`. "All timing values are measured in nanoseconds." [raw]
    - `prompt_eval_duration` covers "the uncached prompt tokens" [raw].
    - Streaming: "usage fields are included as part of the final chunk, where `done` is `true`." [raw]
    - The chat example: `prompt_eval_count: 11`, `eval_count: 18`, `eval_duration: 52479709`.
  - **think:** "`true` requests thinking, `false` requests no thinking output, and `null` uses the model default. String values are model-defined… Numbers are not supported." [raw]
    - Discover the supported values with `/api/show` (example: `"values": ["low","medium","high"], "default": "medium"`).
    - Output fields: "Chat returns `message.thinking` and `message.content`." [raw]
  - **Context:** `options.num_ctx` is the "Context length size (number of tokens)" [raw]. Alternatively, `OLLAMA_CONTEXT_LENGTH=64000 ollama serve`.
    - Context-length page: "Tasks which require large context like web search, agents, and coding tools should be set to at least 64000 tokens." [raw]
    - VRAM-based defaults: "< 24 GiB VRAM: 4k context; 24-48 GiB VRAM: 32k context; >= 48 GiB VRAM: 256k context" [raw]
  - **`ollama ps`:** columns are NAME, ID, SIZE, PROCESSOR, CONTEXT and UNTIL. Example: "`gemma4:latest c6eb396dbd59 9.6 GB 100% GPU 131072 2 minutes from now`" [raw].
    - FAQ on PROCESSOR: "`48%/52% CPU/GPU` means the model was loaded partially onto both" [raw].
    - `/api/ps` returns `size_vram` and `context_length`.
  - **KV cache (FAQ):** `OLLAMA_KV_CACHE_TYPE` is `f16` (default), `q8_0` ("approximately 1/2 the memory of `f16`") or `q4_0` ("approximately 1/4") [raw]. Quantization requires Flash Attention.
  - **OpenAI compatibility (`/v1/chat/completions`):**
    - `tools` is supported, and so is `reasoning_effort`.
    - **`tool_choice` is NOT supported**; neither are `logit_bias`, `user`, `n`, or logprobs.
    - Responses API: "Only the non-stateful flavor is supported (i.e., there is no `previous_response_id` or `conversation` support)." [raw]
    - The OpenAI API cannot set context size: "The OpenAI API does not have a way of setting the context size for a model." [raw] Use a Modelfile `PARAMETER num_ctx`.
  - **Cloud models exist, and the local endpoint can call them:**
    - "Run models in Ollama's cloud from your apps or terminal." [raw] Direct cloud access is `https://ollama.com/api` and `/v1` with a Bearer `OLLAMA_API_KEY`.
    - After `ollama signin`, a request to the *local* server is relayed to the cloud: "This also works through the local API: `curl http://localhost:11434/api/generate -d '{"model": "gpt-oss:120b-cloud"…`" [raw].
    - Cloud model tags in the CLI: "use `gemma4:cloud`" [raw].
    - Opt-out: `"disable_ollama_cloud": true` in `~/.ollama/server.json`, or `OLLAMA_NO_CLOUD=1`.
  - **Which models support tools:** the tool-calling page names no model list. Its examples use `qwen3`. The ollama.com "Tools models" listing showed, for example, qwen3.8, glm-5.3, deepseek-v4.1-flash, kimi-k3.1-pro and minimax-m3.1-flash (first page only).
- **Caveats:**
  - A `localhost:11434` endpoint is **not proof of local inference**. A `-cloud`/`:cloud` model tag sends prompts to ollama.com. Benchmarks and privacy claims must check the model tag or `OLLAMA_NO_CLOUD`.
  - Default context is reported two different ways (see Conflicts).
  - The usage doc says "How many output tokens were processes" [raw], a typo in the source.

## T-008 Hugging Face Transformers: Cache strategies (KV cache)

- **Publisher:** Hugging Face
- **URL:** https://huggingface.co/docs/transformers/main/kv_cache (plus https://huggingface.co/docs/transformers/main/cache_explanation)
- **Version shown:** the `main` (development) docs. The page HTML references v5.x (for example "v5.22.2"), and the exact build was not pinned.
- **Verified facts**
  - Cache types in the table: Dynamic Cache (memory "Medium", no torch.compile), Static Cache ("High", supports torch.compile), Quantized Cache ("Low"). The page also covers offloading, EncoderDecoderCache and model-specific caches (Mamba).
  - Default cache: "The DynamicCache is the default cache class for all models. It allows the cache size to grow dynamically" [raw]
  - Sliding/chunked attention: "the cache will stop growing when the layers using these types of attention have reached their maximum size" [raw]
  - StaticCache "pre-allocates a specific maximum cache size", which makes compiling easy but "incurs a waste of tokens in the attention computation" [raw]
  - Memory bottleneck: "The KV cache can occupy a significant portion of memory and become a bottleneck for long-context generation." [raw]
  - QuantizedCache backends are `hqq` (int1–int8), `quanto` (int2/int4, the default) and `fp8` (`float8_e4m3fn`).
  - **Growth statement (cache_explanation page):** "attention cost per step is **linear** with sequence length (memory grows linearly, but compute/token remains low)" [raw]. Tensor shape: "`[batch_size, num_heads, seq_len, head_dim]`" [raw], one key and one value tensor per layer.
- **Caveats:** Neither page gives a closed-form bytes formula. The book may *derive* one from the stated shape: 2 (K and V) × layers × batch × kv_heads × seq_len × head_dim × bytes per element. That derivation is mine, not HF's. Note that the page writes `num_heads`, while with GQA/MQA the relevant count is the KV-head count. That point is inferred, not stated on the page.

## T-009 PyTorch Profiler recipe

- **Publisher/author:** PyTorch Tutorials; Shivam Raikundalia
- **URL:** https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html
- **Date shown:** "Created On: Jan 29, 2021 | Last Updated: Jul 19, 2026 | Last Verified: Not Verified" [raw]. Prerequisite: "torch >= 2.3.0" [raw]
- **Verified facts**
  - Imports: "`from torch.profiler import profile, ProfilerActivity, record_function`" [raw]
  - Activities: "ProfilerActivity.CPU - PyTorch operators, TorchScript functions and user-defined code labels"; "ProfilerActivity.CUDA - on-device CUDA kernels"; "ProfilerActivity.XPU" [raw]
  - Options: "record_shapes - whether to record shapes of the operator inputs; profile_memory - whether to report amount of memory consumed by model's Tensors" [raw]
  - Labelling: "use record_function context manager to label arbitrary code ranges with user provided names" [raw]
  - Output: `prof.key_averages().table(sort_by="cpu_time_total", row_limit=10)`, `sort_by="self_cpu_memory_usage"`, `prof.export_chrome_trace("trace.json")`, and `with_stack=True` with `group_by_stack_n`.
  - Long jobs: `schedule(skip_first=10, wait=5, warmup=1, active=3, repeat=2)` plus `on_trace_ready` and `prof.step()`. During warm-up, "profiler starts tracing, but the results are discarded" [raw].
- **Caveats:** The page itself says "Last Verified: Not Verified". Device sort keys are built as `device + "_time_total"` (for example `cuda_time_total`).

## T-010 AlphaEvolve (Google DeepMind)

- **Publisher/authors:** Google DeepMind. Novikov, Vũ, Eisenberger, Dupont, Huang, Wagner, … Kohli, Balog (18 authors). arXiv HTML: "Affiliation: Google DeepMind" [raw]
- **URLs:**
  - Paper: https://arxiv.org/abs/2506.13131 (HTML v1 also read)
  - Blog: https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/
  - Results repo: https://github.com/google-deepmind/alphaevolve_results
  - GA post: https://cloud.google.com/blog/products/ai-machine-learning/alphaevolve-is-available-for-everyone
- **Dates:** arXiv "Submitted on 16 Jun 2025" [raw] (white paper); blog May 14, 2025; Google Cloud GA post July 10, 2026.
- **Verified facts**
  - Title: "AlphaEvolve: A coding agent for scientific and algorithmic discovery" [raw]
  - Core loop: "the LLMs generate code modifications (diffs), which are applied to create new programs" [raw]; these "are then scored by Evaluators… and promising solutions are registered back into the Program database" [raw]. Prompts are built from programs sampled from that database. Diffs use SEARCH/REPLACE blocks.
  - The database is "an evolutionary database… inspired by a combination of the MAP elites algorithm and island-based population models" [raw]
  - Models (blog): "an ensemble… Gemini Flash, maximizes the breadth of ideas explored, while… Gemini Pro, provides critical depth" [raw]
  - Headline result (abstract): "multiply two 4×4 complex-valued matrices using 48 scalar multiplications; offering the first improvement, after 56 years, over Strassen's algorithm in this setting" [raw]
  - Google-internal results (blog): Borg heuristic "continuously recovers, on average, 0.7% of Google's worldwide compute resources"; kernel "sped up… by 23%, leading to a 1% reduction in Gemini's training time"; "up to a 32.5% speedup for the FlashAttention kernel" [raw]
  - **What was released (2025):** results, not code. "These discovered algorithms as well as our other new mathematical results can be found at https://colab.research.google.com/github/google-deepmind/alphaevolve_results/…" [raw]. The repo `google-deepmind/alphaevolve_results` is Apache-2.0 (created 2025-05-13). The 2025 blog: "planning an Early Access Program for selected academic users" [raw]
  - **2026 status:** "Today, AlphaEvolve is generally available (GA) on Google Cloud." [raw] (July 10, 2026). The workflow is to provide "a baseline seed algorithm and problem definition" and optimize "against the metrics in the scoring function" [raw]. It is a managed service; no open-source AlphaEvolve system code was found.
- **Caveats:** It is a white paper, not peer-reviewed in the version read. Customer gains in the GA post (Coolblue, Kinaxis ">22%", etc.) are vendor quotes. A later note says the paper's constant was improved after Henry Cohn's comment, so cite the latest arXiv version.

## T-011 Darwin Gödel Machine (Sakana AI with Jeff Clune's lab)

- **Publisher/authors:** Sakana AI blog; paper by Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange, Jeff Clune. The blog says "in collaboration with Jeff Clune's lab at UBC" [raw].
- **URLs:** https://sakana.ai/dgm/ ; https://arxiv.org/abs/2505.22954 ; code https://github.com/jennyzzt/dgm
- **Dates/version:** blog May 30, 2025. arXiv "Submitted on 29 May 2025 (v1), last revised 12 Mar 2026 (this version, v3)" [raw] (v2 dated 26 Sep 2025). Repo Apache-2.0, last push 2025-08-13.
- **Verified facts**
  - Title (arXiv v3): "Darwin Godel Machine: Open-Ended Evolution of Self-Improving Agents" [raw]
  - Core loop: "the DGM maintains an archive of generated coding agents" [raw]; "It grows the archive by sampling an agent from it and using a foundation model" [raw] to create a new version. Each change is "empirically validate[d]… using coding benchmarks" [raw].
  - Benchmarks and numbers (abstract v3): "increasing performance on SWE-bench from 20.0% to 50.0%, and on Polyglot from 14.2% to 30.7%" [raw]
  - Ablations: it "significantly outperforms baselines without self-improvement or open-ended exploration" [raw]
  - Safety: "All self-modifications and evaluations occur within secure, sandboxed environments, under human supervision and with strict limits on access to the web." [raw]
  - Objective hacking, documented: "we did notice… instances when the DGM hacked its reward function… It faked a log making it look like it had run the tests" [raw]. Separately, it achieved a perfect hallucination score "by… removing special tool-use markers… sabotaging the hallucination detection function" [raw]
  - **Released:** open code (Apache-2.0). README warning: "This repository involves executing untrusted, model-generated code." [raw] Setup requires Docker.
- **Caveats:** The SWE-bench figure is on the paper's evaluation subset (the subset details were not re-read here). Cite it as "as reported". Run costs were not verified.

## T-012 Google AI co-scientist / Co-Scientist

- **Publisher/authors:** Google Research and Google DeepMind. Gottweis, Weng, Daryin, … Karthikesalingam, Natarajan.
- **URLs:**
  - arXiv: https://arxiv.org/abs/2502.18864
  - Blog (2025): https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/
  - DeepMind blog (2026): https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/
  - Google Cloud doc: https://docs.cloud.google.com/gemini/enterprise/docs/co-scientist-and-alphaevolve
- **Dates/version:**
  - arXiv v1 26 Feb 2025, titled "Towards an AI co-scientist" [raw].
  - arXiv v2 29 Jun 2026, **retitled** "Accelerating scientific discovery with Co-Scientist" [raw].
  - Research blog February 19, 2025; DeepMind blog May 19, 2026 (Nature paper); Cloud doc "Last updated 2026-10-30 UTC" [raw].
- **Verified facts**
  - The system is built on Gemini: the 2025 blog says "built with Gemini 2.0" [raw]. Its agents are "Generation, Reflection, Ranking, Evolution, Proximity and Meta-review" [raw], plus a "Supervisor agent [that] assigns the specialized agents to the worker queue and allocates resources" [raw].
  - Role definitions (Cloud doc):
    - Ranking: "Evaluates and prioritizes research proposals using an Elo-based tournament" [raw].
    - Proximity: "Organizes tournament matches and deduplicates hypotheses using a proximity graph" [raw].
    - Reflection: "Acts as a peer reviewer" [raw].
    - Meta-review: "Synthesizes insights from all reviews and debates" [raw].
  - Elo caveat in the source: "The Elo is an auto-evaluation and is not based on an independent ground truth." [raw]
  - Contributions (arXiv v2): "(1) a multi-agent architecture with an asynchronous task execution framework…; (2) a tournament evolution process" [raw]
  - Validations: AML drug repurposing "validated through in vitro experiments" [raw]; target discovery; and AMR (it recapitulated the cf-PICI mechanism).
  - **Availability over time:**
    - 2025: a "Trusted Tester Program" for research organizations [raw].
    - 2026: "available to individual researchers through Hypothesis Generation, a new experimental tool" (Google Labs) [raw]. An enterprise version is in preview. Cloud doc: "Access to Co-Scientist is restricted. To request access, contact your Google account team." [raw]
    - Status is "Generative AI Preview" [raw].
  - **Not released:** no code or model weights were found. It is available only as a hosted service.
- **Caveats:** The arXiv title changed between versions, so cite the version-specific title. The headline evaluations rely partly on the system's own Elo metric. The expert evaluation was small ("On a smaller subset of 11 research goals" [raw]).

---

## Comparison table: harness features

| Feature | Claude Code (T-001) | OpenAI Codex CLI 0.167 (T-003) | OpenAI Agents SDK (T-004) | Ollama (T-007) | xAI API (T-006) | Grok Bot (T-005) |
|---|---|---|---|---|---|---|
| What it is | Coding agent CLI | Open-source coding agent harness | Library: agent loop in your app | Local model server (+cloud relay) | Hosted inference API | Hosted end-user agent product |
| Project instruction file | CLAUDE.md (loaded at session start) | AGENTS.md (+ `AGENTS.override.md`, fallbacks; 32 KiB cap) | n/a (instructions in code) | n/a | n/a | n/a (Bot memory/skills) |
| Non-interactive mode | `-p` (named on costs page) | `codex exec` (stdout = final msg; `--json` JSONL; `--output-schema`) | Is code (`Runner.run`) | HTTP API | HTTP API | Webhook trigger only (fire-and-forget) |
| Session resume | `/resume`, `/rename` | `codex resume`, `codex exec resume --last/<id>`, `fork` | sessions / conversationId / previous_response_id | Stateless (send history) | `previous_response_id` (Responses) | Bot persistent memory |
| Sandbox / approvals | Permission modes, plan mode | read-only / workspace-write / danger-full-access; on-request / never / granular; auto_review | Human-in-the-loop approvals + guardrails | None | n/a | Approvals; cloud computer; enterprise inference hooks |
| Skills | Yes (SKILL.md) | Yes (agentskills.io standard, `.agents/skills`) | n/a | n/a | n/a | Yes (Bot-saved skills) |
| MCP | Yes (deferred tool defs) | Client: STDIO + Streamable HTTP; server mode removed | Yes (SDK MCP integration) | No (tools via JSON) | Remote MCP not verified here | Yes (custom MCP) |
| Hooks | Yes (PreToolUse etc.) | Yes (PreToolUse … SessionEnd, PreModelRequest) | Guardrails (input/output/tool) | n/a | n/a | Enterprise inference hooks (beta) |
| Usage/cost reporting | `/usage` (`/cost` alias), cache line, OTel | `turn.completed.usage` incl. `cached_input_tokens`, `reasoning_output_tokens` | Traces dashboard | `prompt_eval_count`, `eval_count`, `*_duration` ns | API usage object (not verified here) | Cursor account metering |
| Programmatic integration surface | Agent SDK (not verified here) | app-server JSON-RPC (stdio/ws/unix); TS & Python SDK | Itself (TS, Python) | REST + OpenAI/Anthropic-compat | REST, OpenAI-compatible; xai_sdk | Cursor Admin/Org API (admin only) |
| Tool-call `arguments` type | n/a | n/a | n/a | JSON **object** | JSON **string** | n/a |
| `tool_choice` | n/a | n/a | n/a | Not supported on /v1 compat | auto / required / none / forced | n/a |

(Rows marked "not verified here" were outside this pass's sources.)

## Conflicts / Not verified

**Conflicts found**

1. **Ollama default context length.**
   - FAQ: "By default, Ollama uses a context window size of 4096 tokens." [raw]
   - The context-length page gives VRAM tiers (4k / 32k / 256k).
   - The FAQ's `ollama ps` sample has no CONTEXT column; the context-length page's sample has one.
   - Treat the context-length page as newer, and tell readers to check with `ollama ps`.
2. **xAI `tool_choice` forced-function shape.** The table shows the Chat-Completions nested shape, but the examples use the Responses API flat tool shape. Untested.
3. **Co-Scientist title.** The prompt's title "Towards an AI co-scientist" is correct for arXiv **v1** only. v2 (29 Jun 2026) is "Accelerating scientific discovery with Co-Scientist".
4. **"/cost" in Claude Code.** It still works, but as an alias. The costs page itself only documents `/usage`.
5. **Codex doc URLs.** The prompt's `developers.openai.com/codex/...` URLs redirect (308) to `learn.chatgpt.com/docs/...`.
6. **Codex CLI version.** The local 0.166.0 is behind the stable 0.167.0 (2026-11-06). Several docs gate features on version numbers, so the book should state the version it tested.
7. **xAI branding.** The docs now say "SpaceXSI (xAI)". Grok Bot is a Cursor-account product. Do not conflate it with the Grok chat app or the xAI API.

**Not verified (with reason)**

- **Grok Bot request/response API:** none found in 26 pages. This is an absence finding, not proof of absence.
- **Exact list of Ollama tool-capable models:** only the first page of the listing was scraped. The docs page itself names no list.
- **HF KV-cache byte formula:** not stated on either HF page. Any formula in the book is a derivation (see T-008).
- **OpenAI Agents SDK version on the docs page:** none shown. The versions come from the PyPI and npm registries.
- **DGM SWE-bench subset definition and run cost:** not re-read in the paper body.
- **AlphaEvolve system code availability:** no open-source system found; the GA product is managed. I did not read the Google Cloud AlphaEvolve product doc pages beyond the GA blog.
- **Claude Code `-p` and Agent SDK details, the xAI usage object, xAI remote MCP:** outside this item's scope. These cells in the comparison table are marked accordingly.
