"""Pre-flight fails closed (review M4) and matches preflight_expect on all 25 bundles (T3 logic,
on placeholder held-out images; the real T3 is the dry run after the images are drawn)."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import helpers
from bundle import Selection, preflight
from trials import FIXTURES, load, load_dev_v2, load_spec_trials


def m4():
    return next(b for b in load()[0] if b.task_id == "M4_screenshot_typed")


def m1():
    return next(b for b in load()[0] if b.task_id == "M1_typed_short")


class FailClosed(unittest.TestCase):
    def test_baseline_passes(self) -> None:
        self.assertTrue(preflight(m4(), FIXTURES)["proceed"])

    def test_unknown_window_title_blocks(self) -> None:
        b = m4()
        r = preflight(replace(b, screenshot=replace(b.screenshot, window_title=None)), FIXTURES)
        self.assertFalse(r["proceed"])
        self.assertIn("window title unknown", r["findings"][0])

    def test_unknown_capture_time_blocks(self) -> None:
        b = m4()
        for value in ("", None):
            r = preflight(replace(b, screenshot=replace(b.screenshot, captured_utc=value)), FIXTURES)
            self.assertFalse(r["proceed"])
            self.assertTrue(any("capture time unknown" in f for f in r["findings"]))

    def test_naive_timestamp_is_a_finding_not_a_crash(self) -> None:
        b = m4()
        r = preflight(replace(b, screenshot=replace(b.screenshot, captured_utc="2026-11-09T01:59:52")), FIXTURES)
        self.assertFalse(r["proceed"])
        self.assertTrue(any("no time zone" in f for f in r["findings"]))
        r = preflight(replace(b, request_utc="2026-11-09T02:00:00"), FIXTURES)
        self.assertFalse(r["proceed"])

    def test_bad_timestamp_is_a_finding(self) -> None:
        b = m4()
        r = preflight(replace(b, screenshot=replace(b.screenshot, captured_utc="yesterday")), FIXTURES)
        self.assertTrue(any("not an ISO 8601" in f for f in r["findings"]))

    def test_selection_without_screenshot_blocks(self) -> None:
        r = preflight(replace(m1(), selection=Selection(box=[-5, -5, 99999, 99999], method="x")), FIXTURES)
        self.assertFalse(r["proceed"])
        self.assertIn("no screenshot", r["findings"][0])

    def test_malformed_box_is_a_finding(self) -> None:
        for box in ([1, 2, 3], [1, 2, 3, "4"], [0, 0, 10.5, 10], "0,0,10,10"):
            r = preflight(replace(m4(), selection=Selection(box=box, method="x")), FIXTURES)
            self.assertFalse(r["proceed"], box)
            self.assertIn("not four integers", r["findings"][0])

    def test_box_outside_image(self) -> None:
        r = preflight(replace(m4(), selection=Selection(box=[0, 0, 2000, 10], method="x")), FIXTURES)
        self.assertEqual(r["findings"], ["selection lies outside the image"])

    def test_missing_hash_blocks(self) -> None:
        b = m4()
        r = preflight(replace(b, screenshot=replace(b.screenshot, sha256=None)), FIXTURES)
        self.assertIn("hash not recorded", r["findings"][0])


class ExpectedActions(unittest.TestCase):
    def test_dev_set_unchanged(self) -> None:
        for t in load_dev_v2():
            self.assertEqual(preflight(t.bundle, t.image_dir)["action"], t.preflight_expect, t.bundle.task_id)

    def test_heldout_on_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = helpers.placeholder_heldout(Path(tmp))
            held = load_spec_trials(image_dir=folder)
            self.assertEqual(len(held), 10)
            for t in held:
                self.assertEqual(preflight(t.bundle, t.image_dir)["action"], t.preflight_expect, t.bundle.task_id)
            reasons = {t.bundle.task_id: preflight(t.bundle, t.image_dir)["findings"] for t in held}
            self.assertIn("1500 s older", reasons["HC3_term_stale"][0])
            self.assertIn("is not PowerShell", reasons["HC4_term_wrong_window"][0])

    def test_heldout_without_images_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for t in load_spec_trials(image_dir=Path(tmp)):
                if t.bundle.screenshot is not None:
                    self.assertFalse(preflight(t.bundle, t.image_dir)["proceed"], t.bundle.task_id)


if __name__ == "__main__":
    unittest.main()
