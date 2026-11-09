"""I1 and T6: prompt v2 is the frozen text, metadata v2 follows Section 4.2, and every v2 render
works; text-only renders carry no instruction to request a screenshot."""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

import helpers
from bundle import AGENT_PROMPT_V2, MAX_IMAGE_AGE_S, agent_prompt, agent_prompt_v2
from trials import load_v2, read_spec


def meta_keys(prompt: str) -> list[str]:
    block = prompt.split("not from the user):\n", 1)[1].split("\n\nUser's request", 1)[0]
    return [line.strip().split(":", 1)[0] for line in block.splitlines()]


class FrozenText(unittest.TestCase):
    def test_equals_spec_and_protocol(self) -> None:
        self.assertEqual(AGENT_PROMPT_V2, "\n".join(read_spec()["agent_prompt_v2_template"]))
        protocol = (helpers.HERE / "PROTOCOL_v2.md").read_text("utf-8")
        block = re.search(r"### 4\.1.*?```text\n(.*?)\n```", protocol, re.S).group(1)
        self.assertEqual(AGENT_PROMPT_V2, block)


class Renders(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.trials = {t.bundle.task_id: t for t in load_v2(heldout_dir=helpers.placeholder_heldout(Path(self.tmp.name)))}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_t6_all_bundles_render(self) -> None:
        arm = [t for t in self.trials.values() if t.also_v1]
        self.assertEqual(len(self.trials) + len(arm), 25)
        for t in self.trials.values():
            p = agent_prompt_v2(t.bundle)
            self.assertNotIn("{", p.split("Reply with JSON only:")[0].replace("{metadata}", ""))
            if t.bundle.screenshot is None:
                self.assertIn("A screenshot is not required.", p)
                self.assertNotIn("or missing, ask for a new screenshot", p)
                self.assertIn("screenshot: none attached", p)
        for t in arm:
            self.assertIn("or missing, ask for a new screenshot", agent_prompt(t.bundle))

    def test_metadata_order_with_screenshot(self) -> None:
        p = agent_prompt_v2(self.trials["HA1_sheet_select_error"].bundle)
        self.assertEqual(meta_keys(p), ["request_utc", "permitted_action", "captured_utc", "window_title",
                                        "image_size", "expected_app", "max_image_age_s", "selection"])
        self.assertIn("  expected_app: LibreOffice Calc", p)
        self.assertIn(f"  max_image_age_s: {MAX_IMAGE_AGE_S}", p)
        self.assertIn("  captured_utc: 2026-11-09T04:59:54+00:00", p)

    def test_metadata_voice_and_no_screenshot(self) -> None:
        p = agent_prompt_v2(self.trials["HC5_term_voice_only"].bundle)
        self.assertEqual(meta_keys(p), ["request_utc", "permitted_action", "screenshot", "speech_engine"])

    def test_nothing_leaks(self) -> None:
        for tid, t in self.trials.items():
            p = agent_prompt_v2(t.bundle)
            self.assertNotIn(tid, p)
            self.assertNotIn(".png", p)
            self.assertNotRegex(p, r"\b1500\b")      # the computed age is never given


if __name__ == "__main__":
    unittest.main()
