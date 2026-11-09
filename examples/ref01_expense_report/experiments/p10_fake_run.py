"""P10 dry-run stand-in for `python run.py --ollama ...` (used only by p10_trials.py --dry-run).

Same command line and the same run records as run.py, but the model is SCRIPTED here and
no network call is made. The scripted turns are CONSTRUCTED to exercise the driver's
scoring paths; they say nothing about how a real model behaves.

Scripted behaviour (attempt = env P10_FAKE_ATTEMPT, default 1):
  v1, seeds 1-2   item 0 cites the rule NUMBER as the line         -> C3 (rule_as_line)
  v2, seed 1      item 0 cites the rule's LINE as the rule number  -> C3
  any, seed 3     decision 'approved' for a reduced total          -> C6
  v1, seed 5      text reply instead of submit_answer              -> text_reply
  v2, seed 4, first claim of a phase, attempt 1: model service error -> blocked, retried
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

EXAMPLE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXAMPLE))

import run  # noqa: E402
from docassist.models import ModelError, OllamaModel, Turn  # noqa: E402

LABELS = json.loads((EXAMPLE / "experiments" / "P10_labels.json").read_text("utf-8"))["labels"]
POLICY = (EXAMPLE / "data" / "policy.md").read_text("utf-8").splitlines()
RULES = {int(line.split(". ", 1)[0]): line.split(". ", 1)[1] for line in POLICY if line[:1].isdigit()}
RULE_LINE = {n: i for i, line in enumerate(POLICY, start=1) for n in RULES if line.startswith(f"{n}. ")}


def script(claim: str, seed: int, interface: str, attempt: int) -> list[Turn] | None:
    if interface == "v2" and seed == 4 and claim in ("claim_normal.json", "claim_heldout_1.json") \
            and attempt == 1:
        return None
    label = LABELS[claim]
    items = []
    for k, (index, allowed) in enumerate(label["items"].items()):
        rule = label["expected_rules"][index]
        wrong = k == 0 and ((interface == "v1" and seed in (1, 2)) or (interface == "v2" and seed == 1))
        ref = ({"rule_line": rule if wrong else RULE_LINE[rule]} if interface == "v1"
               else {"rule_number": RULE_LINE[rule] if wrong else rule})
        items.append({"index": int(index), "allowed": allowed, **ref, "rule_quote": RULES[rule],
                      "reason": "scripted dry-run answer"})
    claim_id = json.loads((EXAMPLE / "data" / claim).read_text("utf-8"))["claim_id"]
    answer = {"claim_id": claim_id, "decision": "approved" if seed == 3 else label["decision"],
              "items": items, "total_allowed": label["total_allowed"]}
    final = (Turn(kind="text", text="(scripted text reply)") if interface == "v1" and seed == 5
             else Turn(kind="tool", name="submit_answer", input=answer))
    return [Turn(kind="tool", name="read_document", input={"name": "policy.md"}),
            Turn(kind="tool", name="calculate", input={"expression": " + ".join(label["items"].values())}),
            final]


class ScriptedOllama(OllamaModel):
    """OllamaModel with the HTTP call replaced: options (seed, temperature, main_gpu) are real."""

    def __init__(self, claim: str, interface: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.turns = script(claim, self.options.get("seed", 0), interface,
                            int(os.environ.get("P10_FAKE_ATTEMPT", "1")))
        self.position = 0

    def describe(self) -> dict[str, Any]:
        return {**super().describe(), "route": "fake (P10 dry run; no Ollama call)"}

    def _call(self) -> Turn:
        if self.turns is None:
            raise ModelError("scripted model service error (P10 dry run)")
        turn = self.turns[min(self.position, len(self.turns) - 1)]
        self.position += 1
        usage = {"prompt_eval_count": 1000 * self.position, "eval_count": 100}
        return Turn(kind=turn.kind, name=turn.name, input=turn.input, text=turn.text,
                    id=f"fake-{self.position}", usage=usage)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    for flag in ("--claim", "--interface"):
        parser.add_argument(flag)
    known, _ = parser.parse_known_args(argv)
    run._live_model = lambda args: ScriptedOllama(known.claim, known.interface or "v1",
                                                  model=args.ollama, seed=args.seed,
                                                  temperature=args.temperature)
    return run.main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
