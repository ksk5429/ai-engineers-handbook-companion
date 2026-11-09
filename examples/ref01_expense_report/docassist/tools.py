"""Tools the model may call, with explicit contracts.

Each contract states the input schema, the output shape, the possible errors and
the side effects. None of these tools has a side effect outside the process:
they read files from one directory and do arithmetic. A tool that is not in
TOOL_CONTRACTS cannot be called, whatever the model asks for.
"""

from __future__ import annotations

import ast
import hashlib
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

from .interface_v2 import split_rules
from .schema import validate

ANSWER_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "answer.schema.json"
ANSWER_SCHEMA_V2_PATH = ANSWER_SCHEMA_PATH.with_name("answer_v2.schema.json")
INTERFACES = ("v1", "v2")

# --8<-- [start:contracts]
TOOL_CONTRACTS: dict[str, dict[str, Any]] = {
    "read_document": {
        "description": "Return the numbered lines of one document from the data folder.",
        "input_schema": {
            "type": "object", "additionalProperties": False, "required": ["name"],
            "properties": {"name": {"type": "string", "pattern": "^[A-Za-z0-9_.-]+$"}},
        },
        "output": "{ok: true, name, sha256, lines: [[number, text], ...]} or {ok: false, error}",
        "errors": ["not_found", "invalid_input"],
        "side_effects": "none (read-only, one folder)",
    },
    "calculate": {
        "description": "Evaluate + - * / on decimal numbers and return the exact result.",
        "input_schema": {
            "type": "object", "additionalProperties": False, "required": ["expression"],
            "properties": {"expression": {"type": "string", "pattern": "^[0-9+*/(). -]+$"}},
        },
        "output": "{ok: true, result: '<decimal string>'} or {ok: false, error}",
        "errors": ["invalid_expression", "division_by_zero", "invalid_input"],
        "side_effects": "none",
    },
    "submit_answer": {
        "description": "Submit the final structured assessment. Ends the workflow.",
        "input_schema": "schemas/answer.schema.json",
        "output": "ends the loop; the answer goes to validation and checks",
        "errors": ["schema_violation"],
        "side_effects": "none (the workflow, not the tool, decides what happens next)",
    },
}
# --8<-- [end:contracts]

# --8<-- [start:contracts_v2]
TOOL_CONTRACTS_V2: dict[str, dict[str, Any]] = {
    **TOOL_CONTRACTS,
    "read_document": {
        **TOOL_CONTRACTS["read_document"],
        "description": "Return one document from the data folder as its numbered rules "
                       "(each with its rule_number and text) and its other text.",
        "output": "{ok: true, name, sha256, text: [line, ...], rules: [{rule_number, text}, ...]} "
                  "or {ok: false, error}",
    },
    "submit_answer": {**TOOL_CONTRACTS["submit_answer"],
                      "input_schema": "schemas/answer_v2.schema.json"},
}
# --8<-- [end:contracts_v2]


def contracts(interface: str) -> dict[str, dict[str, Any]]:
    if interface not in INTERFACES:
        raise ValueError(f"unknown interface {interface!r}")
    return TOOL_CONTRACTS if interface == "v1" else TOOL_CONTRACTS_V2


class ToolBox:
    """Executes allowed tools against one data directory and records every call."""

    def __init__(self, data_dir: Path, interface: str = "v1") -> None:
        self.data_dir = data_dir.resolve()
        self.interface = interface
        self.contracts = contracts(interface)
        self.calls: list[dict[str, Any]] = []

    def call(self, name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        if name not in self.contracts or name == "submit_answer":
            result = {"ok": False, "error": "unauthorized_tool",
                      "detail": f"'{name}' is not an allowed tool"}
        else:
            problems = validate(tool_input, self.contracts[name]["input_schema"])
            if problems:
                result = {"ok": False, "error": "invalid_input", "detail": problems}
            else:
                handler: Callable[[dict[str, Any]], dict[str, Any]] = getattr(self, f"_{name}")
                result = handler(tool_input)
        self.calls.append({"tool": name, "input": tool_input, "ok": result["ok"],
                           "error": result.get("error")})
        return result

    def _read_document(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        path = (self.data_dir / tool_input["name"]).resolve()
        if path.parent != self.data_dir or path.name != tool_input["name"] or not path.is_file():
            return {"ok": False, "error": "not_found", "detail": tool_input["name"]}
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        lines = [[i, line] for i, line in enumerate(text.splitlines(), start=1)]
        if self.interface == "v2":
            return {"ok": True, "name": path.name,
                    "sha256": hashlib.sha256(raw).hexdigest(), **split_rules(lines)}
        return {"ok": True, "name": path.name,
                "sha256": hashlib.sha256(raw).hexdigest(), "lines": lines}

    def _calculate(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        if len(tool_input["expression"]) > 200:
            return {"ok": False, "error": "invalid_expression", "detail": "longer than 200 characters"}
        try:
            value = _eval_decimal(tool_input["expression"])
        except ZeroDivisionError:
            return {"ok": False, "error": "division_by_zero"}
        except (ValueError, SyntaxError, InvalidOperation, RecursionError):
            return {"ok": False, "error": "invalid_expression"}
        return {"ok": True, "result": str(value)}


_NUMBER = re.compile(r"^[0-9]+(\.[0-9]+)?$")


def _eval_decimal(expression: str) -> Decimal:
    """Evaluate arithmetic without eval(): walk the parsed tree, allow 4 operators.

    Each number is built from its SOURCE TEXT (not from Python's float), so "72.00" keeps
    its two decimals and long numbers keep every digit (technical review T-07).
    """
    def walk(node: ast.AST) -> Decimal:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            text = ast.get_source_segment(expression, node) or ""
            if _NUMBER.match(text):
                return Decimal(text)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -walk(node.operand)
        if isinstance(node, ast.BinOp):
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError
                return left / right
        raise ValueError("unsupported expression")
    return walk(ast.parse(expression, mode="eval"))
