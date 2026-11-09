"""Model adapters with one small interface.

  start(system, task, tools) -> Turn     first model turn
  reply(tool_use_id, result) -> Turn     send a tool result, get the next turn
  prime(system, task, tools)             rebuild state without calling the model (resume)
  record_turn(turn)                      append a replayed model turn (resume)
  record_result(result)                  append a replayed tool result (resume)
  describe() -> dict                     model, runtime and capability facts for the run record

FixtureModel replays a scripted list of turns from a case file. Those turns were
WRITTEN BY THE HANDBOOK AUTHOR to imitate specific behaviours. They are constructed
examples, not recorded model output. A fixture run tests the workflow and its
checks; it says nothing about how often a real model makes each mistake.

OllamaModel calls a local Ollama server's /api/chat endpoint with tools.
AnthropicModel calls the Anthropic Messages API (needs ANTHROPIC_API_KEY).
Verification state of each route is recorded in reviews/evidence/, not here.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Turn:
    """One model turn: a tool request or plain text, plus provider-reported usage."""
    kind: str                      # "tool" or "text"
    name: str = ""
    input: dict[str, Any] = field(default_factory=dict)
    id: str = ""
    text: str = ""
    usage: dict[str, Any] | None = None   # None = the provider reported nothing
    extra_calls: tuple[str, ...] = ()     # names of further tool calls in the same turn (ignored)


def as_object(arguments: Any) -> dict[str, Any]:
    """Tool arguments must be a JSON object; anything else is kept for the record, not executed."""
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            return parsed
    return {"_invalid_arguments": arguments}


class ModelError(RuntimeError):
    """The model service could not be reached or returned an unusable response."""


def _post_json(url: str, body: dict[str, Any], headers: dict[str, str],
               timeout_s: float) -> dict[str, Any]:
    request = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={"content-type": "application/json", **headers})
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise ModelError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise ModelError(f"model call to {url} failed: {exc}") from exc


class FixtureModel:
    def __init__(self, turns: list[dict[str, Any]]) -> None:
        self._turns = list(turns)
        self._next = 0

    def describe(self) -> dict[str, Any]:
        return {"route": "fixture", "model": "none (constructed turns)",
                "usage_reporting": "unavailable"}

    def _pop(self) -> Turn:
        if self._next >= len(self._turns):
            return Turn(kind="text", text="(fixture exhausted)")
        raw = self._turns[self._next]
        self._next += 1
        if "tool" in raw:
            return Turn(kind="tool", name=raw["tool"], input=as_object(raw.get("input", {})),
                        id=f"fixture-{self._next}")
        return Turn(kind="text", text=raw.get("text", ""))

    def start(self, system: str, task: str, tools: list[dict[str, Any]]) -> Turn:
        return self._pop()

    def reply(self, tool_use_id: str, result: dict[str, Any]) -> Turn:
        return self._pop()

    def prime(self, system: str, task: str, tools: list[dict[str, Any]]) -> None:
        pass

    def record_turn(self, turn: Turn) -> None:
        self._next += 1            # that scripted turn was already consumed before the crash

    def record_result(self, result: dict[str, Any]) -> None:
        pass


# --8<-- [start:ollama]
class OllamaModel:
    """Local model through Ollama's native /api/chat endpoint (non-streaming)."""

    def __init__(self, model: str = "qwen2.5:7b", host: str | None = None,
                 num_ctx: int = 8192, temperature: float = 0.0, seed: int | None = None,
                 timeout_s: float = 300.0) -> None:
        self.model = model
        self.host = (host or os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
        if not self.host.startswith("http"):
            self.host = "http://" + self.host
        self.options: dict[str, Any] = {"num_ctx": num_ctx, "temperature": temperature}
        if seed is not None:
            self.options["seed"] = seed
        main_gpu = os.environ.get("HANDBOOK_MAIN_GPU")              # e.g. "1" = second card
        if main_gpu is not None:
            self.options["main_gpu"] = int(main_gpu)
        self.timeout_s = timeout_s
        self.messages: list[dict[str, Any]] = []
        self.tools: list[dict[str, Any]] = []

    def describe(self) -> dict[str, Any]:
        return {"route": "ollama", "model": self.model, "host": self.host,
                "options": self.options, "usage_reporting": "prompt_eval_count, eval_count"}

    def _call(self) -> Turn:
        data = _post_json(f"{self.host}/api/chat",
                          {"model": self.model, "messages": self.messages, "tools": self.tools,
                           "stream": False, "options": self.options}, {}, self.timeout_s)
        message = data.get("message", {})
        self.messages.append(message)
        usage = {k: data[k] for k in ("prompt_eval_count", "eval_count", "total_duration",
                                      "load_duration", "prompt_eval_duration", "eval_duration")
                 if k in data}
        calls = message.get("tool_calls") or []
        if calls:
            function = calls[0].get("function", {})
            return Turn(kind="tool", name=function.get("name", ""),
                        input=as_object(function.get("arguments", {})),
                        id=f"ollama-{len(self.messages)}", usage=usage,
                        extra_calls=tuple(c.get("function", {}).get("name", "") for c in calls[1:]))
        return Turn(kind="text", text=message.get("content", ""), usage=usage)

    def start(self, system: str, task: str, tools: list[dict[str, Any]]) -> Turn:
        self.prime(system, task, tools)
        return self._call()

    def reply(self, tool_use_id: str, result: dict[str, Any]) -> Turn:
        self.messages.append({"role": "tool", "content": json.dumps(result)})
        return self._call()

    def prime(self, system: str, task: str, tools: list[dict[str, Any]]) -> None:
        self.tools = [{"type": "function", "function": t} for t in _openai_style(tools)]
        self.messages = [{"role": "system", "content": system},
                         {"role": "user", "content": task}]

    def record_turn(self, turn: Turn) -> None:
        self.messages.append({"role": "assistant", "content": "", "tool_calls": [
            {"function": {"name": turn.name, "arguments": turn.input}}]})

    def record_result(self, result: dict[str, Any]) -> None:
        self.messages.append({"role": "tool", "content": json.dumps(result)})
# --8<-- [end:ollama]


def _openai_style(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Anthropic-style {name, description, input_schema} -> {name, description, parameters}."""
    return [{"name": t["name"], "description": t["description"],
             "parameters": t["input_schema"]} for t in tools]


class AnthropicModel:  # pragma: no cover - live service; cycle 1 state: not run (no key)
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, model: str | None = None, timeout_s: float = 120.0) -> None:
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ModelError("ANTHROPIC_API_KEY is not set: live model is unavailable")
        self.model = model or os.environ.get("HANDBOOK_MODEL", "claude-sonnet-5-5")
        self.timeout_s = timeout_s
        # Hard spend guard in tokens (owner decision D-19: cap about USD 5). Converting the cap to
        # money needs the provider's current price list, so the guard is expressed in tokens and
        # the live script stops when the cumulative total would pass it.
        self.max_total_tokens = int(os.environ.get("HANDBOOK_MAX_TOTAL_TOKENS", "300000"))
        self.used_tokens = 0
        self.messages: list[dict[str, Any]] = []
        self.system = ""
        self.tools: list[dict[str, Any]] = []

    def describe(self) -> dict[str, Any]:
        return {"route": "anthropic", "model": self.model,
                "usage_reporting": "input_tokens, output_tokens, cache fields"}

    def _call(self) -> Turn:
        if self.used_tokens >= self.max_total_tokens:
            raise ModelError(f"token cap reached ({self.used_tokens} >= {self.max_total_tokens})")
        data = _post_json(self.URL, {"model": self.model, "max_tokens": 2000,
                                     "system": self.system, "tools": self.tools,
                                     "messages": self.messages},
                          {"x-api-key": self.api_key,
                           # version string used by the current tool-use docs [S-007]; recheck when they change
                           "anthropic-version": os.environ.get("HANDBOOK_ANTHROPIC_VERSION", "2026-10-21")},
                          self.timeout_s)
        content = data.get("content", [])
        self.messages.append({"role": "assistant", "content": content})
        usage = data.get("usage")
        if isinstance(usage, dict):                 # count every reported token category
            self.used_tokens += sum(v for k, v in usage.items()
                                    if k.endswith("_tokens") and isinstance(v, int))
        uses = [b for b in content if b.get("type") == "tool_use"]
        if uses:
            self._extra_ids = [b["id"] for b in uses[1:]]   # must still be answered (with an error)
            return Turn(kind="tool", name=uses[0]["name"], input=as_object(uses[0].get("input", {})),
                        id=uses[0]["id"], usage=usage, extra_calls=tuple(b["name"] for b in uses[1:]))
        text = " ".join(b.get("text", "") for b in content if b.get("type") == "text")
        return Turn(kind="text", text=text, usage=usage)

    def start(self, system: str, task: str, tools: list[dict[str, Any]]) -> Turn:
        self.prime(system, task, tools)
        return self._call()

    def reply(self, tool_use_id: str, result: dict[str, Any]) -> Turn:
        blocks = [{"type": "tool_result", "tool_use_id": tool_use_id,
                   "content": json.dumps(result), "is_error": not result.get("ok", True)}]
        blocks += [{"type": "tool_result", "tool_use_id": extra, "is_error": True,
                    "content": "refused: one tool call per turn"} for extra in getattr(self, "_extra_ids", [])]
        self._extra_ids = []
        self.messages.append({"role": "user", "content": blocks})
        return self._call()

    def prime(self, system: str, task: str, tools: list[dict[str, Any]]) -> None:
        self.system, self.tools = system, tools
        self.messages = [{"role": "user", "content": task}]

    def record_turn(self, turn: Turn) -> None:
        self.messages.append({"role": "assistant", "content": [
            {"type": "tool_use", "id": turn.id, "name": turn.name, "input": turn.input}]})
        self._last_id = turn.id

    def record_result(self, result: dict[str, Any]) -> None:
        self.messages.append({"role": "user", "content": [{
            "type": "tool_result", "tool_use_id": self._last_id, "content": json.dumps(result)}]})
