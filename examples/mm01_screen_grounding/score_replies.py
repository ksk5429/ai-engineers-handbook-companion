"""Score agent replies saved as files (the Claude Code route) with the same evaluator.

  python score_replies.py reviews/evidence/mm01/claude_code

Each <task_id>.reply.json was written by a fresh Claude Code subagent that was
given only its bundle prompt and the image path. The subagent wrote its own reply
file; this script does not alter it. Writes SCORES.md next to the replies.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from trials import evaluate, load


def main(folder: str) -> int:
    reply_dir = Path(folder)
    _, labels = load()
    rows = ["# MM01 trials through Claude Code subagents (generated)", "",
            f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} by "
            "`examples/mm01_screen_grounding/score_replies.py`.",
            "Route: Claude Code 2.1.319 (VS Code extension), Agent tool, model alias `haiku`, "
            "one fresh subagent per trial, Read tool on the PNG. n=1 per trial.", "",
            "| Trial | Expected | Decision | Target ok | Concepts ok | Passed | Reply sha256 |",
            "|---|---|---|---|---|---|---|"]
    for path in sorted(reply_dir.glob("*.reply.json")):
        task_id = path.name.removesuffix(".reply.json")
        raw = path.read_bytes()
        try:
            reply = json.loads(raw)
        except json.JSONDecodeError:
            reply = None
        score = evaluate(reply if reply else None, labels[task_id])
        rows.append(f"| {task_id} | {labels[task_id]['expect']} | "
                    f"{(reply or {}).get('decision', 'unparsed')} | {score['target_ok']} | "
                    f"{score['concepts_ok']} | {score['passed']} | `{hashlib.sha256(raw).hexdigest()[:12]}` |")
    rows += ["", "Contamination note: the stale-image trial's reply says the file name marks the "
                 "image as stale. The fixture file names (e.g. stale_screenshot.png) leaked the label "
                 "to this route. That trial does not count as evidence that the model judged "
                 "freshness from the metadata. Fixture images are renamed to neutral names for later runs.", ""]
    (reply_dir / "SCORES.md").write_text("\n".join(rows), encoding="utf-8")
    print("\n".join(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "../../reviews/evidence/mm01/claude_code"))
