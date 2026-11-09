"""Independent checks on a schema-valid answer.

These checks do not ask the model anything and do not trust its reasons. They use
only the source document, the claim and arithmetic. Each returns a CheckResult;
a run passes only if every check passes.

What they establish: the answer is internally consistent, covers every claim item,
quotes the policy verbatim at the cited line, and never allows more than was
claimed. What they do NOT establish: that the model chose the *right* rule or the
right amount. That needs labelled test cases (see evaluate() in workflow.py) or a
human reviewer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    passed: bool
    detail: str


def _norm(text: str) -> str:
    return " ".join(text.split())


def quote_matches(quote: str, line: str) -> bool:
    """Whole-line match: the quote equals the line, with or without its "N. " rule prefix.

    (v0.1 accepted any fragment of 10+ characters; technical review T-08.)"""
    q, l = _norm(quote), _norm(line)
    return bool(q) and (q == l or q == re.sub(r"^\d+\.\s*", "", l))


# --8<-- [start:quote_check]
def check_quotes(answer: dict[str, Any], source_lines: dict[int, str] | None) -> CheckResult:
    """Every rule_quote must be its cited line, word for word (up to whitespace)."""
    if source_lines is None:
        return CheckResult("C3_quotes_in_source", False,
                           "source document was never loaded, so no quote can be checked")
    bad = []
    for item in answer["items"]:
        line_text = source_lines.get(item["rule_line"], "")
        if not quote_matches(item["rule_quote"], line_text):
            bad.append(f"item {item['index']}: quote not found on line {item['rule_line']}")
    return CheckResult("C3_quotes_in_source", not bad, "; ".join(bad) or "all quotes found")
# --8<-- [end:quote_check]


def check_coverage(answer: dict[str, Any], claim: dict[str, Any]) -> CheckResult:
    """Each claim item is assessed exactly once, and no invented items appear."""
    expected = sorted(item["index"] for item in claim["items"])
    got = sorted(item["index"] for item in answer["items"])
    ok = expected == got and answer["claim_id"] == claim["claim_id"]
    return CheckResult("C2_coverage", ok,
                       "ok" if ok else f"claim {claim['claim_id']} items {expected}; "
                                       f"answer {answer['claim_id']} items {got}")


def check_not_above_claimed(answer: dict[str, Any], claim: dict[str, Any]) -> CheckResult:
    claimed = {item["index"]: Decimal(item["amount"]) for item in claim["items"]}
    bad = [f"item {i['index']}: allowed {i['allowed']} > claimed {claimed[i['index']]}"
           for i in answer["items"]
           if i["index"] in claimed and Decimal(i["allowed"]) > claimed[i["index"]]]
    return CheckResult("C4_not_above_claimed", not bad, "; ".join(bad) or "ok")


# --8<-- [start:arithmetic_check]
def check_total(answer: dict[str, Any]) -> CheckResult:
    """The stated total must equal the sum of the item amounts, to the cent."""
    total = sum((Decimal(i["allowed"]) for i in answer["items"]), Decimal("0.00"))
    stated = Decimal(answer["total_allowed"])
    return CheckResult("C5_total_is_sum", total == stated,
                       f"sum of items {total:.2f}, stated total {stated:.2f}")
# --8<-- [end:arithmetic_check]


def check_decision(answer: dict[str, Any], claim: dict[str, Any]) -> CheckResult:
    """The decision label must agree with the numbers."""
    claimed = sum((Decimal(i["amount"]) for i in claim["items"]), Decimal("0.00"))
    allowed = Decimal(answer["total_allowed"])
    decision = answer["decision"]
    if decision == "refer_to_treasurer":
        return CheckResult("C6_decision_consistent", True, "referred; no numeric constraint")
    expected = ("approved" if allowed == claimed else
                "rejected" if allowed == 0 else "partially_approved")
    return CheckResult("C6_decision_consistent", decision == expected,
                       f"claimed {claimed:.2f}, allowed {allowed:.2f}: "
                       f"expected '{expected}', got '{decision}'")


def run_all(answer: dict[str, Any], claim: dict[str, Any],
            source_lines: dict[int, str] | None) -> list[CheckResult]:
    return [
        check_coverage(answer, claim),
        check_quotes(answer, source_lines),
        check_not_above_claimed(answer, claim),
        check_total(answer),
        check_decision(answer, claim),
    ]
