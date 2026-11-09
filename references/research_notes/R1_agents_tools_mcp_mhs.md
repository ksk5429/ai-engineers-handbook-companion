# R1 source register (draft): agents, Claude Code harness, tool use, MCP, MHS

- Researcher: R1. Access date for every source: **2026-11-09**.
- Method: each page was fetched live with WebFetch. Quotes are verbatim and at most 25 words. Some quotes reached me through the fetch tool's extraction layer. Where it returned a summary rather than raw page text, the item says so and marks it **[paraphrase]**.
- Labels: **V** = verified on the primary page. **I** = inference from the page. **UNVERIFIED** = not established, with the reason.
- Date convention: when a page shows no date, the entry says "no date shown". Docs pages on code.claude.com and platform.claude.com carry no visible last-updated date.

---

## S-001 Building effective agents (Anthropic Engineering)

- **Title:** "Building effective agents"
- **Publisher / authors:** Anthropic. "Written by Erik S. and Barry Zhang."
- **URL:** https://www.anthropic.com/engineering/building-effective-agents
- **Published:** Dec 19, 2024. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. Workflows are defined as: "systems where LLMs and tools are orchestrated through predefined code paths."
  2. Agents are defined as: "systems where LLMs dynamically direct their own processes and tool usage"
  3. Building block: "an LLM enhanced with augmentations such as retrieval, tools, and memory." The post calls this the augmented LLM.
  4. The five named workflow patterns:
     - Prompt chaining: "decomposes a task into a sequence of steps, where each LLM call processes the output of the previous one."
     - Routing: "classifies an input and directs it to a specialized followup task."
     - Parallelization: "LLMs can sometimes work simultaneously on a task and have their outputs aggregated programmatically."
     - Orchestrator-workers: "a central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results."
     - Evaluator-optimizer: "one LLM call generates a response while another provides evaluation and feedback in a loop."
  5. Start simple: "we recommend finding the simplest solution possible, and only increasing complexity when needed." Also: "optimizing single LLM calls with retrieval and in-context examples is usually enough."
  6. When agents fit, and their cost: agents suit "open-ended problems where it's difficult or impossible to predict the required number of steps". But: "The autonomous nature of agents means higher costs, and the potential for compounding errors."
  7. Frameworks: "We suggest that developers start by using LLM APIs directly". Frameworks "make it tempting to add complexity when a simpler setup would suffice."
  8. Tool design and the agent-computer interface (ACI):
     - "Tool definitions and specifications should be given just as much prompt engineering attention as your overall prompts."
     - "Poka-yoke your tools. Change the arguments so that it is harder to make mistakes."
     - Example: the tool was changed "to always require absolute filepaths".
     - Closing principle: "Carefully craft your agent-computer interface (ACI) through thorough tool documentation and testing."
- **Caveats/conflicts:**
  - The page now opens with an editor's note: "Much of the tooling landscape described in this post has changed since December 2024." It points readers to Claude Managed Agents for Anthropic's current approach.
  - The handbook should cite the five patterns as a 2024 framing and say that the post itself flags its tooling as dated.

## S-002 Claude Code docs: Subagents

- **Title:** Subagents ("Create custom subagents"), Claude Code documentation
- **Publisher:** Anthropic
- **URL:** https://code.claude.com/docs/en/sub-agents
- **Date:** no date shown. The page cites CLI version numbers. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. Definition: "Subagents are specialized AI assistants that handle specific types of tasks."
  2. Separate context: "Each subagent runs in its own context window with a custom system prompt, specific tool access, and independent permissions."
  3. Fresh start: a subagent "doesn't see your conversation history, the skills you've already invoked, or the files Claude has already read."
  4. Format and locations: Markdown files with YAML frontmatter. Priority, highest first:
     1. managed settings
     2. the `--agents` CLI flag
     3. `.claude/agents/` (project)
     4. `~/.claude/agents/` (user)
     5. a plugin's `agents/` directory

     On a name clash, "Claude Code uses the one from the higher-priority location."
  5. Frontmatter: "Only `name` and `description` are required."
     - Optional fields include `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort` and `isolation`, among others.
  6. Tool restriction: `tools` "Inherits every tool available to subagents if omitted."
     - "If both are set, `disallowedTools` is applied first, then `tools` is resolved against the remaining pool."
  7. Model: accepts `sonnet`, `opus`, `haiku`, `fable`, a full model ID, or `inherit`.
  8. Nesting: "By default, a subagent can spawn subagents of its own, up to three layers below the main conversation."
- **Caveats/conflicts:**
  - Older tutorials say subagents cannot spawn subagents. The current docs say they can, by default to three levels, adjustable with `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`. Use the current wording.
  - Omitting `tools` does not mean literally all tools: a fixed set (e.g. `AskUserQuestion`, plan-mode tools) is always removed **[paraphrase of the fetch summary]**.
  - The page is about 117k characters. Its last 17k characters were not read.

## S-003 Claude Code docs: Hooks (reference and guide)

- **Titles:** "Hooks reference" (https://code.claude.com/docs/en/hooks) and "Automate actions with hooks" (https://code.claude.com/docs/en/hooks-guide)
- **Publisher:** Anthropic
- **Date:** no date shown. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. From the guide: "Claude Code runs them at specific points in its lifecycle, which gives you deterministic control". Certain actions then always happen "rather than relying on the LLM to choose to run them."
  2. Reference definition: "Hooks are user-defined shell commands, HTTP endpoints, MCP tool calls, LLM prompts, or subagents that execute automatically at specific points in Claude Code's lifecycle."
  3. Events include `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `SubagentStop`, `Stop`, `PreCompact` and `SessionEnd`, among about 30 others.
     - For `PreToolUse`: "Before a tool call executes. Can block it."
  4. Blocking works in two ways:
     - Exit code: "Exit with code 2 to block the action."
     - JSON output: `hookSpecificOutput.permissionDecision`, which takes "allow/deny/ask/defer".
  5. Location: "Hooks are defined in JSON settings files". These are `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed policy, plugin `hooks/hooks.json`, and skill or subagent frontmatter.
  6. Limits on hooks as gates:
     - "use the permission system rather than a hook to enforce a hard allow or deny." This refers to the best-effort `if` filter.
     - "The hook can deny the call, but staying silent doesn't approve it."
- **Caveats/conflicts:**
  - "Deterministic" applies to command hooks. The same docs also offer prompt-based and agent-based hooks, which use a model and so are not deterministic.
  - The reference page was only partly read: about 100k of its 290k characters.

## S-004 Claude Code docs: Configure permissions

- **Title:** "Configure permissions"
- **Publisher:** Anthropic
- **URL:** https://code.claude.com/docs/en/permissions
- **Date:** no date shown. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. Order: "Rules are evaluated in order: deny, then ask, then allow. The first match in that order determines the outcome".
  2. Enforcement locus: "Permission rules are enforced by Claude Code, not by the model." Also: "Instructions in your prompt or `CLAUDE.md` shape what Claude tries to do, but they don't change what Claude Code allows."
  3. Hooks cannot override deny: "PreToolUse hook decisions don't bypass permission rules." Also: "a matching deny rule blocks the call".
  4. Modes listed include `acceptEdits`, `plan`, `auto`, `dontAsk` and `bypassPermissions`. Use `bypassPermissions` "only ... in isolated environments like containers or VMs".
  5. Limits of Bash rules: a deny or ask rule "covers the invocation Claude usually produces and isn't a security boundary around the program." For enforcement that does not depend on the command text, the page points to sandboxing.
  6. Rule syntax examples, from the settings page S-005: `Bash(npm run test *)` and `Read(./.env)`.
- **Caveats/conflicts:** Important nuance for the handbook: permission rules match command text, not program behaviour. The docs themselves send hard isolation to the sandbox.

## S-005 Claude Code docs: Settings files and precedence

- **Title:** "Settings files and precedence"
- **Publisher:** Anthropic
- **URL:** https://code.claude.com/docs/en/settings
- **Date:** no date shown. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. Files: user `~/.claude/settings.json`, shared project `.claude/settings.json`, project local `.claude/settings.local.json`, and managed settings.
  2. Precedence, highest first: managed, command line (`--settings`), project local, shared project, user.
  3. Managed settings: "Nothing in your own settings files or `--settings` overrides a managed key".
  4. Lists merge: "Claude Code combines the lists instead of picking one". This applies to keys such as `permissions.allow`.
  5. Trust: in a cloned repo, "`deny` and `ask` rules apply right away". Committed `allow` rules wait until each user trusts the folder.
  6. Instructions are separate from settings: "To give Claude standing instructions, use CLAUDE.md files or the `--append-system-prompt` flag."
- **Caveats/conflicts:** A few security keys honour a stricter lower-scope value over managed settings. Do not over-simplify "managed always wins".

## S-006 Claude Code docs: Memory (CLAUDE.md)

- **Title:** "How Claude remembers your project"
- **Publisher:** Anthropic
- **URL:** https://code.claude.com/docs/en/memory
- **Date:** no date shown. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. Two systems: CLAUDE.md files ("instructions you write to give Claude persistent context") and auto memory ("notes Claude writes itself").
  2. Not enforced: "Claude treats them as context, not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook".
  3. Locations:
     - managed policy (Windows: `C:\Program Files\ClaudeCode\CLAUDE.md`)
     - user `~/.claude/CLAUDE.md`
     - project `./CLAUDE.md` or `./.claude/CLAUDE.md`
     - local `./CLAUDE.local.md`
  4. Loading: files in the working directory and every directory above it are loaded. "All discovered files are concatenated into context rather than overriding each other."
  5. Imports: "CLAUDE.md files can import additional files using `@path/to/import` syntax."
  6. Size: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."
  7. AGENTS.md: by default it is read only when no CLAUDE.md or CLAUDE.local.md exists in the working directory or above it.
- **Caveats/conflicts:** None. S-004, S-005 and S-006 agree on the main point: CLAUDE.md is context, and settings, permissions and hooks are what the harness enforces.

## S-007 Claude API docs: Tool use (overview, define tools, handle tool calls)

- **Titles and URLs:**
  - "Tool use with Claude": https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
  - "Define tools": https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
  - "Handle tool calls": https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls
- **Publisher:** Anthropic
- **Date:** no date shown. Code samples use `anthropic-version: 2026-10-21`. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. Definition: "Tool use (also called function calling) lets Claude call functions that you define or that Anthropic provides."
  2. Definition fields:
     - `name`: "Must match the regex `^[a-zA-Z0-9_-]{1,128}$`."
     - `description`: "A detailed plain text description of what the tool does".
     - `input_schema`: "A JSON Schema object defining the expected parameters for the tool."
     - Optional: `input_examples`, `cache_control`, `strict`, `defer_loading` and `allowed_callers`.
  3. Stop reason: "Claude responds with `stop_reason: "tool_use"` and one or more `tool_use` blocks. Your code runs the operation and sends back a `tool_result`."
  4. A `tool_use` block has `id`, `name` and `input`. A `tool_result` block has `tool_use_id`, optional `content`, and optional `is_error` ("Set to `true` if the tool execution resulted in an error.").
  5. Ordering rule: "In the user message containing tool results, the `tool_result` blocks must come FIRST in the content array."
  6. Client tools vs server tools: client tools run in your application. Server tools such as `web_search`, `web_fetch` and `code_execution` "run on Anthropic's infrastructure".
  7. Description advice: "Provide extremely detailed descriptions. This is by far the most important factor in tool performance." Also: "Aim for at least 3–4 sentences".
  8. Prompt-injection warning: "Treat that content as untrusted". Keep untrusted content inside `tool_result` blocks.
- **Caveats/conflicts:** Forced tool use (`tool_choice` of `any` or `tool`) "return[s] a 400 error" on Claude Opus 5.5, Sonnet 5.5, Fable 5.1 and Mythos 5.1. The docs recommend `auto` plus strict tool use instead. Older tutorials that force `tool_choice` for JSON extraction are outdated for these models.

## S-008 Claude API docs: Structured outputs and Strict tool use

- **Titles and URLs:**
  - "Structured outputs": https://platform.claude.com/docs/en/build-with-claude/structured-outputs
  - "Strict tool use": https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
- **Publisher:** Anthropic
- **Date:** no date shown. **Accessed:** 2026-11-09.
- **Status:** both pages carry page metadata `status: stable`, so the features are **GA, not beta**. On every listed platform the status is `stable`: Claude API, Claude Platform on AWS, Amazon Bedrock, Claude Models on Google Cloud, and Microsoft Foundry.
- **Verified facts (V):**
  1. Two features under one name: **JSON outputs** (`output_config.format`) and **strict tool use** (`strict: true`). Structured outputs "constrain Claude's responses to follow a specific schema".
  2. Mechanism: `strict: true` "guarantees Claude's tool inputs match your JSON Schema by constraining the model's token sampling to schema-valid outputs". The page calls this technique grammar-constrained sampling.
  3. Guarantees: "Tool `input` strictly follows the `input_schema`" and "Tool `name` is always valid".
  4. Migration: "The `output_format` parameter has moved to `output_config.format`, and beta headers are no longer required." The old form needs the `structured-outputs-2025-11-13` beta header.
  5. Schema subset:
     - `additionalProperties` must be `false`.
     - Not supported: recursive schemas, `minimum`, `maximum`, `minLength` and `maxLength`.
     - Unsupported features return a 400 error.
  6. Availability: "Strict tool use is available on every model". The supported list runs from claude-sonnet-4-5-20250929 up to claude-opus-5-5.
  7. Data handling: only the JSON schema is cached, "for up to 24 hours since last use". PHI must not appear in schemas.
- **Caveats/conflicts:**
  - Exact feature names: "Structured outputs" is the umbrella. "JSON outputs" and "Strict tool use" are its two parts.
  - The beta-era parameter `output_format` and header `structured-outputs-2025-11-13` are deprecated.
  - The Structured outputs page was partly paraphrased by the fetch tool. Its last 6k characters were not read.

## S-009 Model Context Protocol: introduction

- **Title:** "What is the Model Context Protocol (MCP)?"
- **Publisher:** MCP project (modelcontextprotocol.io)
- **URL:** https://modelcontextprotocol.io/docs/getting-started/intro
- **Date:** no date shown. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. "MCP (Model Context Protocol) is an open-source standard for connecting AI applications to external systems."
  2. Analogy: "Think of MCP like a USB-C port for AI applications."
  3. Examples it lists: data sources ("local files, databases"), tools ("search engines, calculators") and workflows ("specialized prompts").
  4. Ecosystem: the page names Claude, ChatGPT, VS Code and Cursor as supporting MCP.
- **Caveats/conflicts:** The intro page says nothing about governance. For that, see S-012.

## S-010 MCP specification, revision 2026-07-28 (current)

- **Titles and URLs:**
  - "Specification": https://modelcontextprotocol.io/specification/latest, which resolves to revision 2026-07-28
  - "Versioning": https://modelcontextprotocol.io/specification/versioning
  - "Key Changes": https://modelcontextprotocol.io/specification/2026-07-28/changelog
  - "Transports overview": https://modelcontextprotocol.io/specification/2026-07-28/basic/transports
- **Publisher:** MCP project
- **Revision:** **2026-07-28**. The Versioning page states: "The **current** protocol version is **2026-07-28**." The previous revision was **2025-11-25**, per the changelog. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. Base protocol: "The protocol uses JSON-RPC 2.0 messages to establish communication between" three roles:
     - Hosts ("LLM applications that initiate connections")
     - Clients ("Connectors within the host application")
     - Servers ("Services that provide context and capabilities")
  2. Server features:
     - "Resources: Context and data, for the user or the AI model to use"
     - "Prompts: Templated messages and workflows for users"
     - "Tools: Functions for the AI model to execute"
  3. Client features: the 2026-07-28 overview lists **only** "Elicitation: Server-initiated requests for additional information from users".
     - The changelog: "Deprecate the Roots, Sampling, and Logging features". New implementations "should not add support for them".
  4. Stateless redesign: "Make MCP stateless: remove the `initialize`/`notifications/initialized` handshake."
     - Every request carries its protocol version and capabilities in `_meta`.
     - A new mandatory `server/discover` RPC.
     - Server-initiated requests are replaced by the "Multi Round-Trip Requests (MRTR)" pattern.
  5. Transports:
     - "stdio: newline-delimited messages over the standard streams of a client-launched subprocess"
     - "Streamable HTTP: each message is an HTTP POST to a single MCP endpoint"
     - The old HTTP+SSE transport is Deprecated.
     - Protocol-level sessions (`Mcp-Session-Id`) were removed.
  6. Security principles, from "Security and Trust & Safety":
     - "Users must explicitly consent to and understand all data access and operations"
     - "Hosts must obtain explicit user consent before invoking any tool"
     - "Tools represent arbitrary code execution and must be treated with appropriate caution."
     - Annotations "should be considered untrusted, unless obtained from a trusted server."
  7. Enforcement: "MCP itself cannot enforce these security principles at the protocol level". Implementors SHOULD build consent and authorization flows.
  8. Extensions: optional and opt-in, for example Tasks (moved out of core into an official extension) and MCP Apps.
- **Caveats/conflicts:**
  - Many tutorials, and the handbook brief's own example ("2025-06-18"), predate two later revisions: 2025-11-25 and 2026-07-28.
  - Teaching that clients offer "sampling, roots, elicitation" is now outdated. Sampling and roots still work during a deprecation window of at least 12 months, but are Deprecated.
  - Teaching the `initialize` handshake as current is also outdated. The handshake belongs to revisions 2025-11-25 and earlier, which are backward-compatibility territory.

## S-011 MCP specification 2026-07-28: Authorization

- **Title:** "Authorization"
- **Publisher:** MCP project
- **URL:** https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization
- **Revision:** 2026-07-28. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. "Authorization is **OPTIONAL** for MCP implementations."
  2. Scope: HTTP-based transports "SHOULD conform". Implementations using STDIO "SHOULD NOT follow this specification, and instead retrieve credentials from the environment."
  3. Basis: "OAuth 2.1 IETF DRAFT (draft-ietf-oauth-v2-1-13)", plus RFC 8414, RFC 8707, RFC 9728, RFC 9207, and Client ID Metadata Documents.
  4. Roles: "A protected MCP server acts as an OAuth 2.1 resource server". "An MCP client acts as an OAuth 2.1 client".
  5. "MCP servers MUST implement OAuth 2.0 Protected Resource Metadata (RFC9728)."
  6. Resource indicators: clients "MUST implement Resource Indicators for OAuth 2.0 as defined in RFC 8707".
  7. No token passthrough: "MCP servers MUST NOT accept or transit any other tokens."
  8. Dynamic Client Registration (RFC 7591) "is deprecated". Client ID Metadata Documents are preferred.
- **Caveats/conflicts:** OAuth 2.1 is still an IETF draft. Write "based on the OAuth 2.1 draft", not "OAuth 2.1 standard".

## S-012 MCP governance: "MCP joins the Agentic AI Foundation"

- **Title:** "MCP joins the Agentic AI Foundation"
- **Publisher / author:** MCP blog. David Soria Parra, Lead Core Maintainer.
- **URL:** https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/
- **Published:** Dec 9, 2025. **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. "Anthropic is donating MCP to the newly formed Agentic AI Foundation under the Linux Foundation"
  2. The foundation was "co-founded by Anthropic, Block and OpenAI."
  3. "For MCP little changes."
  4. "The governance model we introduced earlier this year continues as is."
  5. [paraphrase] Technical decisions stay with the MCP maintainers through the SEP process. The Linux Foundation supplies neutral infrastructure.
- **Caveats/conflicts:**
  - Anthropic's own announcement (anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation) appeared in search results but **was not fetched**.
  - The other AAIF founding projects (goose, AGENTS.md) and the supporting companies come from search snippets only: **UNVERIFIED** at primary level.
  - One secondary site gives a conflicting date of May 2026. It is not trusted.

## S-013 Model Hardware Standard website

- **Title:** "Model Hardware Standard"
- **Publisher:** not stated on the page. No footer, copyright line or date. The text names Anthropic and HHMI Janelia as the project's origin.
- **URL:** https://www.modelhardwarestandard.com/
- **Date:** no date shown. **Accessed:** 2026-11-09. **Version:** none stated.
- **Verified facts (V):**
  1. Full name: "Model Hardware Standard" (abbreviated MHS).
  2. Purpose: "A new standard for AI agents to safely operate physical equipment in scientific research and advanced manufacturing."
  3. Origin: "MHS started as a project between Anthropic and HHMI Janelia Research Campus to enable AI to accelerate scientific research."
  4. Maturity: "MHS is starting as a limited research preview." Also: "Access is by application during the preview."
  5. Not yet open: stakeholders are invited to test it "before we open-source it". Partners are developing it "ahead of it becoming open source."
  6. Links: "Apply for access" (a Google Form) and "Read the announcement", which links to S-014. No spec document, SDK, GitHub or schema link is on the page.
- **Caveats/conflicts:** The page does not mention MCP.

## S-014 Anthropic news: "Previewing the Model Hardware Standard"

- **Title:** "Previewing the Model Hardware Standard"
- **Publisher:** Anthropic
- **URL:** https://www.anthropic.com/news/model-hardware-standard-research-preview
- **Published:** "Published Aug 27, 2026". **Accessed:** 2026-11-09.
- **Verified facts (V):**
  1. "We're opening a research preview of the Model Hardware Standard (MHS)"
  2. Definition: "a shared specification for AI agents to safely operate physical devices."
  3. Driver: "software that translates between a computer's operating system and a hardware device". It has basic "read" and "write" commands.
  4. Reference file: the driver generates a reference file covering "what it can measure, what can be adjusted, and what safety limits will be enforced".
  5. MCP relation: "For MHS, there are three such mechanisms: MCP, the command line interface, and code files (APIs)." Also: "It is also model-agnostic".
  6. Open source: development continues "ahead of making the standard open source". No timeline is given.
  7. [paraphrase] Named partners include Genentech, Carnegie Mellon University, QuEra, AWS, Danaher, Doosan Robotics, QIAGEN, Tecan and Universal Robots. Hugging Face and Raspberry Pi are named as early adopters. Partner names come from the fetch tool's summary, not a raw-text check.
- **Caveats/conflicts:**
  - **Relation to MCP:** MCP is one of three *access mechanisms* to MHS. The post does **not** say MHS builds on or extends MCP. Reading MHS as a device and driver layer that agents reach through MCP, a CLI or APIs is **I** (inference).
  - **Prior project finding:** `F:\RESEARCH\72_MHS\AUDIT_MHS_2026-11-08.md`, lines 34-40, reached the same reading and quotes the same three-mechanism sentence. Its further claims are not used here:
    - a firsthand CMU preview report of manifests and a private Python SDK
    - "MCP sits on top"

    They do not come from these primary pages.

---

## Conflicts and open questions

1. **MCP revision drift.** The brief suggested "2025-06-18 or later". The current revision is **2026-07-28**, the previous one 2025-11-25.
   - The core model has changed: stateless requests, no `initialize` handshake, `server/discover`, the MRTR pattern, and no protocol sessions.
   - The client features Roots and Sampling are Deprecated, along with Logging.
   - Any chapter text drafted from 2025-era tutorials needs revision.
2. **Client features list.** The 2026-07-28 overview lists only Elicitation. Sampling and roots still function during the deprecation window.
   - Recommendation: present them as "deprecated (2026-07-28), still functional for at least 12 months".
3. **Subagent nesting.** Folk knowledge says subagents cannot spawn subagents. The current docs say they can, up to three levels by default.
4. **Forced `tool_choice`.** It is rejected (400) on Opus 5.5, Sonnet 5.5, Fable 5.1 and Mythos 5.1. Use `auto` with strict tool use or JSON outputs.
5. **"Hooks are deterministic."** True for command hooks. Prompt-based and agent-based hooks use a model.
   - The docs also say permission rules, not hooks, are the hard allow/deny gate. Hooks cannot override a deny rule.
6. **Permission rules are not a security boundary around a program.** The docs say Bash rules match command text. Sandboxing gives OS-level enforcement.
7. **MHS and MCP.** "MHS is built on MCP" is **not supported**. "MHS can be accessed via MCP" **is** supported.
8. **OAuth 2.1.** MCP authorization is based on an IETF *draft* (draft-ietf-oauth-v2-1-13), not a published RFC.
9. **"Building effective agents" (2024)** carries the publisher's own "tooling has changed" note. Cite it as foundational, not current.

## Not verified

- **MHS spec version, schema, field names, transport and SDK:** not public on either MHS page. There is no version number, no download, no GitHub link and no SDK link. **UNVERIFIED (not published)**.
- **MHS maturity label beyond "limited research preview":** the pages use no draft, preview or stable vocabulary.
- **MHS maintainer of record:** the site names its origin (Anthropic and HHMI Janelia) but gives no maintainer, publisher line or legal entity. **UNVERIFIED**.
- **MHS open-source date:** none given.
- **Full partner list in S-014:** taken from the fetch tool's summary, not verbatim-checked.
- **AAIF founding projects and supporters:** goose, AGENTS.md, Google, Microsoft, AWS, Cloudflare and Bloomberg. Search snippets only. The Anthropic donation post was not fetched.
- **Last-updated dates** for all code.claude.com and platform.claude.com pages: none shown.
- **Partly read pages:** the tail sections of very long pages were not read:
  - Hooks reference: about 190k characters unread.
  - Sub-agents: about 17k unread.
  - Structured outputs: about 6k unread.

  The facts above come from the parts that were read.
