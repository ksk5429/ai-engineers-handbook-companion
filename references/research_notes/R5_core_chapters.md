# R5 source notes: core chapters B1 and O1

- Compiled by the managing editor (integration step for chapters B1 and O1). **Accessed:** 2026-11-09 for every page.
- Method: each page was downloaded with `curl` as raw page text (the `.md` form of the docs pages; the HTML page for OWASP) and every quote below was found by exact string search, ignoring line breaks only. Quotes marked **[raw]** were read in that raw text. Link markup in the page is dropped from the quotes (for example `[PreToolUse hook](...)` becomes `PreToolUse hook`); the page's curly apostrophes and quotation marks are kept here as they appear.
- This file supplements R1 (S-series), R2 (R-series), R3 (T-series) and R4 (M-series). It does not replace their entries. Sections 1 to 4 are new sources; sections 5 to 9 add quotations to registered sources that the B1 and O1 audits asked to record.
- Labels follow R1: **V** = verified on the primary page; **I** = the book's inference from the page.

---

## 1. S-015 Glossary (Claude API docs)

- **Title:** "Glossary". Page description: "These concepts are not unique to Claude. This page presents a brief summary of key terms." [raw]
- **Publisher:** Anthropic. **URL:** https://platform.claude.com/docs/en/about-claude/glossary (raw text: append `.md`). **Date:** no date shown.
- **Verified facts (V):**
  1. Pretraining: "Pretraining is the initial process of training language models on a large unlabeled corpus of text." [raw]
  2. "In Claude’s case, autoregressive language models (such as Claude’s underlying model) are pretrained to predict the next word, given the previous context of text in the document." [raw]
  3. Fine-tuning: "Fine-tuning is the process of further training a pretrained language model using additional data." [raw]
  4. "Claude is not a bare language model; it has already been fine-tuned to be a helpful assistant. The Claude API does not currently offer fine-tuning, but ask your Anthropic contact if you are interested in exploring this option." [raw]
  5. RLHF: "Reinforcement learning from human feedback (RLHF) is a technique used to train a pretrained language model to behave in ways that are consistent with human preferences. This can include helping the model follow instructions more effectively or act more like a chatbot." [raw]
  6. Temperature: "Temperature is a parameter that controls the randomness of a model’s predictions during text generation." and "Lower temperatures result in more conservative and deterministic outputs that stick to the most probable phrasing and answers." [raw]
  7. Non-determinism: "Even with temperature set to 0, the results will not be fully deterministic, and identical inputs might produce different outputs across API calls" [raw]
  8. Tokens: "Tokens are the smallest individual units of a language model, and can correspond to words, subwords, characters, or even bytes (in the case of Unicode). For Claude, the number of characters a token represents depends on the model and the language." [raw]
  9. RAG: "In RAG, a language model is augmented with an external knowledge base or a set of documents that is passed into the context window." [raw] The entry also says RAG "allows the model to access and use information beyond its training data" [raw].
- **Caveats:** The glossary says nothing about whether weights change during inference. The chapter's statement that weights are read, not changed, is therefore a stated assumption (knowledge gap G-19). The page describes Anthropic's products only.

## 2. S-016 Context windows (Claude API docs)

- **Title:** "Context windows". Page description: "Understand how the context window works, how extended thinking and tool use count toward it, and how to manage context as conversations grow." [raw]
- **Publisher:** Anthropic. **URL:** https://platform.claude.com/docs/en/build-with-claude/context-windows. **Date:** no date shown.
- **Verified facts (V):**
  1. "The “context window” refers to all the text a language model can reference when generating a response, including the response itself. This is different from the large corpus of data the language model was trained on, and instead represents a “working memory” for the model." [raw]
  2. "As token count grows, accuracy and recall degrade, a phenomenon known as *context rot*." [raw]
  3. "As the conversation advances through turns, each user message and assistant response accumulates within the context window, and previous turns are preserved completely." [raw]
  4. "If the input alone already exceeds the model’s context window, the API returns a 400 `invalid_request_error` (“prompt is too long”) on every model." [raw]
  5. Footnote: "Chat interfaces such as claude.ai can also manage the context window on a rolling “first in, first out” basis." [raw]
  6. "Compaction automatically summarizes earlier parts of the conversation on the server, so the conversation can continue past the context window limit. It is available in beta for Claude 4.6 and later models and Claude Mythos Preview." [raw]
- **Caveats:** Compaction is a beta API feature with a model qualifier (dated product detail; recheck). The glossary (S-015) defines the context window in different words ("the amount of text a language model can look back on and reference when generating new text"); B1 quotes the Context windows page.

## 3. S-017 Models overview (Claude API docs)

- **Title:** "Models overview". **Publisher:** Anthropic.
- **URL:** https://platform.claude.com/docs/en/about-claude/models/overview (the page's own metadata gives https://platform.claude.com/docs/en/models/overview). **Date:** no date shown.
- **Verified facts (V):**
  1. Definition (footnote to the comparison table): "**Reliable knowledge cutoff:** The date through which the model’s knowledge is most extensive and reliable. Training data cutoff (under Additional details) is the broader range of data used." [raw]
  2. The comparison table has rows headed "Reliable knowledge cutoff" and "Training data cutoff" [raw].
- **Caveats:** B1 deliberately quotes no model's dates. The table changes with each model generation.

## 4. S-018 Embeddings (Claude API docs)

- **Title:** "Embeddings". **Publisher:** Anthropic. **URL:** https://platform.claude.com/docs/en/build-with-claude/embeddings. **Date:** no date shown.
- **Verified facts (V):**
  1. Page description: "Text embeddings are numerical representations of text that let you measure semantic similarity." [raw]
  2. "Anthropic does not offer its own embedding model. One embeddings provider with a wide variety of models and capabilities is Voyage AI by MongoDB." [raw]
  3. "The embeddings allow you to do semantic search / retrieval in the vector space." [raw]
- **Caveats:** That embedding models are normally separate from the generating model is shown here only for Anthropic, which has none of its own (I). Other providers were not checked.

---

## 5. S-006 Claude Code Memory: extra quotations (supplements R1 § S-006)

- **URL:** https://code.claude.com/docs/en/memory (raw text: https://code.claude.com/docs/en/memory.md). Page title: "How Claude remembers your project".
- **Verified (V):**
  1. "**CLAUDE.md files**: instructions you write to give Claude persistent context." [raw]
  2. "**Auto memory**: notes Claude writes itself based on your corrections and preferences" [raw]
  3. "Claude Code has two complementary memory systems. Both are loaded at the start of every conversation. Claude treats them as context, not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook instead." [raw]
  4. "Auto memory lets Claude learn from your corrections without manual effort." [raw]
  5. "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the start of every conversation. Content beyond that threshold is not loaded at session start." [raw]
- **Use:** B1 "Training and use are different" (items 1 to 5); O1 "Where the line falls in a coding agent" (item 3). The R1 quote "All discovered files are concatenated into context" concerns CLAUDE.md files only; B1 no longer uses it for auto memory.

## 6. T-007 Ollama: extra quotations (supplements R3 § T-007)

- **API chat (OpenAPI), https://docs.ollama.com/api/chat**, under "Runtime options that control text generation" [raw]:
  1. `seed`: "Random seed used for reproducible outputs" [raw]
  2. `temperature`: "Controls randomness in generation (higher = more random)" [raw]
  3. `top_k`: "Limits next token selection to the K most likely" [raw]
- **Authentication, https://docs.ollama.com/api/authentication:** "The local API at `http://localhost:11434` does not require authentication." [raw]; the CLI example `ollama run gpt-oss:120b-cloud`, followed by "This also works through the local API:" [raw].
- **Cloud, https://docs.ollama.com/cloud:** "Run models in Ollama's cloud from your apps or terminal." and "In the Ollama app or CLI, use `gemma4:cloud`." [raw]; "To use only local models, disable cloud features." [raw]
- **FAQ, https://docs.ollama.com/faq:** "Set `disable_ollama_cloud` in `~/.ollama/server.json`" with `"disable_ollama_cloud": true`, and the environment variable `OLLAMA_NO_CLOUD=1` [raw].
- **Caveat (I):** no page states a general rule that every tag ending in `:cloud` or `-cloud` runs remotely; O1 labels that rule as the book's reading of the two examples.
- **Use:** B1 "Why the same question can get different answers" (items 1 and 3); O1 "For builders: checking that "local" means local" and task 8.

## 7. M-008 Vision: full visual-token sentence (supplements R4 § M-008)

- **URL:** https://platform.claude.com/docs/en/build-with-claude/vision
- **Verified (V):** "Claude processes images in patches instead of pixels. Each patch is a 28×28-pixel block of the image, referred to as a visual token. An image, therefore, costs `⌈width / 28⌉ × ⌈height / 28⌉` visual tokens." [raw]
- **Use:** B1 "Images are tokens too" and "The same ideas in a run record" (1280 × 800 → 46 × 29 = 1,334, a calculation, not a measurement).

## 8. R-002 OWASP LLM01: direct-injection sentence (supplements R2 § R-002)

- **URL:** https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- **Verified (V):** "Direct prompt injections occur when a user’s prompt input directly alters the behavior of the model in unintended or unexpected ways." [raw] The sentence follows the subheading "Direct Prompt Injections"; the HTML encodes the apostrophe as `&#8217;`. O1 quotes it from "occur".
- **Use:** O1 "Who may instruct the AI: the authority order".

## 9. S-003 Hooks reference: context of the "permission system" advice (supplements R1 § S-003)

- **URL:** https://code.claude.com/docs/en/hooks
- **Verified (V):** "When Claude Code can't determine which commands the Bash input runs, it runs your hook regardless of the pattern. Because the `if` filter is best-effort, use the permission system rather than a hook to enforce a hard allow or deny." [raw]
- **Use:** O1 "Where the line falls in a coding agent". O1 now states the best-effort `if` filter as the reason for the advice, as the final audit required.
