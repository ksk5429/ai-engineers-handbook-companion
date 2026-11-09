"""Interface v2 (P10 candidate): the model cites policy rules by rule number.

The evaluator (checks.py) is frozen and reads rule_line. This module derives the
v1 view that the checks read, using ONLY the rule number and the policy text the
harness loaded, never the model's quote or reason, so it cannot repair a wrong
citation.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

RULE_LINE = re.compile(r"^(\d+)\.\s+(.*\S)\s*$")      # "3. Hotel nights ..." -> (3, "Hotel nights ...")


def split_rules(lines: list[list[Any]]) -> dict[str, list[Any]]:
    """Model-facing view: rules keyed by rule number, other non-blank lines as text. No line numbers."""
    rules, other = [], []
    for _, line in lines:
        match = RULE_LINE.match(line)
        if match:
            rules.append({"rule_number": int(match.group(1)), "text": match.group(2)})
        elif line.strip():
            other.append(line)
    return {"text": other, "rules": rules}


def rule_index(source_lines: dict[int, str]) -> dict[int, int]:
    """Rule number -> line number of the line that starts with 'N. '. First occurrence wins."""
    index: dict[int, int] = {}
    for line_no in sorted(source_lines):
        match = RULE_LINE.match(source_lines[line_no])
        if match:
            index.setdefault(int(match.group(1)), line_no)
    return index


def harness_lines(data_dir: Path, result: dict[str, Any]) -> dict[int, str] | None:
    """The harness reads the file the model was shown; None if its bytes differ from what the tool hashed."""
    raw = (data_dir / result["name"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != result["sha256"]:
        return None
    return {i: line for i, line in enumerate(raw.decode("utf-8").splitlines(), start=1)}


def to_v1_view(answer: dict[str, Any], index: dict[int, int]) -> dict[str, Any]:
    """A NEW answer dict with rule_line derived from rule_number (0 = no such rule). Input is not modified."""
    items = [{"index": i["index"], "allowed": i["allowed"],
              "rule_line": index.get(i["rule_number"], 0),
              "rule_quote": i["rule_quote"], "reason": i["reason"]} for i in answer["items"]]
    return {**{k: v for k, v in answer.items() if k != "items"}, "items": items}
