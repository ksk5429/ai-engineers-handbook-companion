# G-02 Running the companion examples with a local model through Ollama

**Guide date:** 9 Nov 2026. **Tested on:** Windows 11 Pro (build 26200), Ollama 0.40.15, models `qwen2.5:7b` (tool calling, REF01) and `qwen3-vl:8b` (images, MM01). The PC has an RTX 2060 (GPU 0) and an RTX 4070 (GPU 1), 12 GB each; the qwen3-vl run of 9 Nov landed on GPU 0 (the 2060), and the REF01 run's card was not recorded. Requesting `main_gpu` per call is untested. **Recheck when:** Ollama changes its `/api/chat` format or a model is updated.

## Terms

Ollama is an **inference runtime**: it loads model files and serves them over a local HTTP API (default `http://127.0.0.1:11434`). It is not a model. Each run record names both the runtime version and the model. Open-source runtime software, open-weight models, free access and total operating cost are four different things: the runtime and these models cost nothing to download, but electricity, hardware and your time are real costs that this project did not measure.

## What was observed on the test machine

| Item | Observation | Evidence |
|---|---|---|
| `ollama --version` | 0.40.15 | `reviews/evidence/ref01_live/LIVE.md` |
| `qwen2.5:7b` placement | `ollama ps`: 4.9 GB, 100% GPU, context 8192 | same |
| Tool calling via `/api/chat` with `tools` | worked: the model returned `message.tool_calls` with `function.name` and `function.arguments` (a JSON object) | REF01 live runs |
| Usage fields | `prompt_eval_count` and `eval_count` present on every call; durations in nanoseconds | `events.jsonl` in each live run |
| `qwen3-vl:8b` with `images` (base64) and `"think": true` | see MM01 results | `reviews/evidence/mm01/TRIALS.md` |

The request shape used by `docassist/models.py` (non-streaming):

```json
{"model": "qwen2.5:7b", "stream": false,
 "messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}],
 "tools": [{"type": "function", "function": {"name": "...", "description": "...", "parameters": {"type": "object"}}}],
 "options": {"num_ctx": 8192, "temperature": 0.0}}
```

Tool results go back as `{"role": "tool", "content": "<JSON text>"}`. The adapter handles arguments returned as a JSON string as well as an object; only objects were observed.

## Steps

1. Install Ollama from its official site and start it.
2. `ollama list` shows installed models. Check a model's size and licence (`ollama show <model> --license`) **before** pulling a new one; the examples need about 5–7 GB of VRAM or RAM.
3. Before a run: `ollama ps`. If another job's model is loaded, wait. Never run two heavy consumers on one Ollama at the same time.
4. Run the example (`python run.py --ollama qwen2.5:7b`), then check `ollama ps` again: the PROCESSOR column should say `100% GPU`. A CPU/GPU split means the model did not fit in VRAM and will be much slower.
5. Unload afterwards: `ollama stop <model>`.

**Data boundary.** With a local model, the prompt and documents stay on the machine. But Ollama documents cloud models: after `ollama signin`, a request sent to `localhost:11434` for a cloud model (a `:cloud` tag such as `gpt-oss:120b-cloud`) is relayed to and run on ollama.com [T-007]. **A localhost address therefore does not prove local inference.** Check the model name and `ollama ps` before sending anything private. Ollama documents `OLLAMA_NO_CLOUD=1` to disable cloud use [T-007] (not tested here).

**Documented details checked against R3's notes [T-007].** Tool results may carry a `tool_name` field (`{"role": "tool", "tool_name": "...", "content": "..."}`); the companion adapter omits it, and the tested model still worked. Ollama returns tool-call `arguments` as a JSON object (OpenAI-compatible providers return a string). `prompt_eval_duration` counts only uncached prompt tokens, and a `prompt_eval_cached_count` field may appear. The OpenAI-compatible `/v1` endpoint does not support `tool_choice`. The default context length is documented inconsistently (4096 tokens on one page, set by available VRAM on another), so always set `num_ctx` explicitly, as the examples do.

**Thinking models.** Some models (`qwen3-vl`, `qwen3.5`) can "think" before answering. Control it with `"think": true/false` in the request body; a `/no_think` text switch in the prompt was found to be ignored on this machine in earlier projects. Record the setting with the results.

## Troubleshooting

| Symptom | Likely cause | Check |
|---|---|---|
| `model call ... failed: connection refused` (run status `blocked`) | Ollama not running | Start Ollama; `ollama ps` |
| Very slow first call | model loading (cold start) | `load_duration` in the event's usage; the second call is faster |
| Model answers in prose instead of calling `submit_answer` | weak tool-calling behaviour | run is recorded as `failed` with reason "model replied with text" |
| Quotes cite the rule number as the line number | interface ambiguity, observed in 6 of 10 REF01 live runs | see chapter E1 "Results"; project P10 |
