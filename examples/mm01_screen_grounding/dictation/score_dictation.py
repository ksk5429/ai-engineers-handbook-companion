"""Score live dictation transcripts against the pre-registered key terms (DICTATION_PROTOCOL.md).

  python score_dictation.py transcripts_live.json      writes DICTATION_RESULTS.md next to it
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KEYS = {  # sentence -> list of key terms; each term is a list of accepted forms (regex, case-insensitive)
    "D1": [[r"totals\s*\.\s*py", r"totals\s+dot\s+py", r"totals\s*\.\s*pi"], [r"\b12\b", r"twelve"]],
    "D2": [[r"\bd\s*-?\s*7\b"], [r"kilomet(?:re|er)s?", r"\bkm\b"], [r"\bmiles?\b"]],
    "D3": [[r"load[_\s]*(?:underscore\s*)?levels?\s*(?:\.|dot)\s*py", r"load_levels"], [r"\b14\b", r"십사"],
           [r"key\s*error"]],
    "D4": [[r"\b90\b", r"ninety"], [r"\b105\b", r"one\s+hundred\s+(?:and\s+)?five"], [r"euros?"]],
    "D5": [[r"compar"], [r"(?:do\s+not|don'?t)\s+change"], [r"\bfiles?\b"]],
}


def score(text: str, terms: list[list[str]]) -> tuple[int, list[bool]]:
    hits = [any(re.search(p, text, flags=re.I) for p in forms) for forms in terms]
    return sum(hits), hits


def main(path: str) -> int:
    src = Path(path)
    data = json.loads(src.read_text("utf-8"))
    rows = ["# Live dictation results (generated)", "",
            f"Source: `{src.name}` ({data.get('route', 'route not recorded')}; recorded {data.get('recorded', '?')}). "
            "Protocol: `DICTATION_PROTOCOL.md` (written before dictation). n = 5 sentences, one speaker: an "
            "illustration, not an accuracy rate.", "",
            "| ID | Raw transcript (verbatim) | Key terms found | Usable without correction |", "|---|---|---|---|"]
    usable = 0
    for sid, terms in KEYS.items():
        text = data["transcripts"].get(sid)
        if text is None:
            rows.append(f"| {sid} | (not dictated) | - | - |")
            continue
        k, _ = score(text, terms)
        ok = k == len(terms)
        usable += ok
        rows.append(f"| {sid} | {text.replace('|', '/')} | {k}/{len(terms)} | {'yes' if ok else 'no'} |")
    rows += ["", f"Usable without correction: {usable} of {len(data['transcripts'])} dictated sentences.", ""]
    (src.parent / "DICTATION_RESULTS.md").write_text("\n".join(rows), encoding="utf-8")
    print("\n".join(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "transcripts_live.json"))
