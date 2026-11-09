"""make_fixtures.py --heldout without drawing the held-out fixtures.

T5 (Hangul glyph check) and the font rule run on the real fonts. T4's precondition (dev hashes
match cases.json) is checked here; T4 itself runs inside `--heldout` (before and after drawing).
The drawing code is exercised on a DECOY spec: every text and every data value of the held-out
spec is replaced, so the real held-out images are never rendered before the freeze. Decoy images
go to a temporary folder, are never shown to any model, and are deleted after the test.
"""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import helpers
import make_fixtures as mf
from PIL import Image

SPEC = json.loads((helpers.HERE / "heldout_spec_v2.json").read_text("utf-8"))


def decoy_spec() -> dict:
    """Same geometry and rule paths, different content."""
    spec = copy.deepcopy(SPEC)
    a, b, c = spec["heldout"]["fixtures"]
    for n, ref in enumerate(sorted(a["cells"])):
        a["cells"][ref] = f"{n}.25" if n % 2 else f"cell {n}"
    for bar in ("title_bar", "menu_bar", "status_bar"):
        a["chrome"][bar]["text"] = "decoy"
    a["chrome"]["formula_bar"]["content"] = "decoy"
    rate = {"S1": 0.5, "S2": 0.4}
    for s in b["series"]:
        s["s_mm"] = [round(rate[s["name"][:2]] * t, 1) for t in s["t"]]
    ax = b["axes"]
    py = lambda v: 680 - v * 580 / 60  # noqa: E731
    b["points_px"] = {"S2_day30": [650.0, round(py(12.0), 1)], "S1_day45": [915.0, round(py(22.5), 1)]}
    cy = round(py(12.0))
    b["boxes"] = {"S2_day30": [636, cy - 14, 664, cy + 14], "S1_day45": [901, 0, 929, 10]}
    ax["title"], b["legend"]["entries"] = "decoy", ["S1 decoy", "S2 decoy"]
    for line in c["lines"]:
        line["text"] = f"decoy {line['n']} 가나 °" if line["n"] % 3 == 0 else f"decoy line {line['n']}"
    c["lines"][6]["text"] = "decoy line 14"
    c["lines"][12]["text"] = "KeyError: decoy"
    return spec


class Fonts(unittest.TestCase):
    def test_t5_hangul_check(self) -> None:
        self.assertTrue(mf.hangul_ok(mf.load_font("malgun.ttf", 15)))
        self.assertFalse(mf.hangul_ok(mf.load_font("consola.ttf", 15)))   # .notdef boxes
        self.assertFalse(mf.hangul_ok(mf.load_font("arial.ttf", 14)))

    def test_missing_font_aborts(self) -> None:
        with self.assertRaises(mf.FixtureError):
            mf.load_font("no_such_font.ttf", 13)

    def test_hangul_lines_use_malgun(self) -> None:
        f = mf.Fonts()
        self.assertTrue(f.get("consola.ttf 15", "KeyError: '수위(m)'").path.lower().endswith("malgun.ttf"))
        self.assertTrue(f.get("consola.ttf 15", "수온 (°C)").path.lower().endswith("malgun.ttf"))
        self.assertTrue(f.get("consola.ttf 15", "30 °").path.lower().endswith("malgun.ttf"))
        self.assertTrue(f.get("consola.ttf 15", "plain ascii").path.lower().endswith("consola.ttf"))

    def test_mark_fallback_only(self) -> None:
        self.assertTrue(mf.Fonts().mark("no_such.ttf 13 (fallback arial.ttf 13)").path.lower().endswith("arial.ttf"))
        with self.assertRaises(mf.FixtureError):
            mf.Fonts().get("no_such.ttf 13")


class DevFixtures(unittest.TestCase):
    def test_dev_hashes_match_cases_json(self) -> None:
        self.assertEqual(mf.dev_hashes_ok(), [])


class DecoyDrawing(unittest.TestCase):
    def test_draws_three_canvases_into_given_folder_only(self) -> None:
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in mf.OUT.glob("*")if p.is_file()}
        with tempfile.TemporaryDirectory() as tmp:
            rec = mf.draw_heldout(decoy_spec(), Path(tmp))
            files = sorted(p.name for p in Path(tmp).iterdir())
            self.assertEqual(files, ["ho_a.png", "ho_b.png", "ho_c.png"])
            for f in rec["fixtures"]:
                with Image.open(Path(tmp) / f["image"]) as img:
                    self.assertEqual((img.size, img.mode), ((1280, 800), "RGB"))
            self.assertIn("malgun.ttf", rec["fonts"])
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in mf.OUT.glob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((mf.OUT / "heldout" / "ho_a.png").exists())

    def test_geometry_mismatch_aborts(self) -> None:
        spec = decoy_spec()
        spec["heldout"]["fixtures"][0]["boxes"]["D4"] = [0, 0, 1, 1]
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(mf.FixtureError):
            mf.draw_heldout(spec, Path(tmp))

    def test_text_off_canvas_aborts(self) -> None:
        spec = decoy_spec()
        spec["heldout"]["fixtures"][2]["lines"][0]["text"] = "x" * 400
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(mf.FixtureError):
            mf.draw_heldout(spec, Path(tmp))

    def test_real_spec_geometry_is_consistent(self) -> None:
        """Checks the frozen spec's own numbers (boxes, point pixels) without drawing it."""
        a, b, c = SPEC["heldout"]["fixtures"]
        xs, rh = a["grid"]["column_x_edges"], a["grid"]["row_height"]
        self.assertEqual(a["boxes"]["D4"], [xs[3], 122 + rh * 3, xs[4], 122 + rh * 4])
        s2 = b["series"][1]
        self.assertAlmostEqual(680 - s2["s_mm"][s2["t"].index(30)] * 580 / 60, b["points_px"]["S2_day30"][1], delta=0.06)
        self.assertEqual(c["boxes"]["user_frame_line_14"][1], 44 + 22 * 6 - 2)


if __name__ == "__main__":
    unittest.main()
