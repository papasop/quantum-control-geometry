"""Semantic checks for the exact-root Figure 2 data pipeline."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "paper" / "scripts" / "generate_fig2_exact_root.py"
SPEC = importlib.util.spec_from_file_location("generate_fig2_exact_root", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATOR
SPEC.loader.exec_module(GENERATOR)


class ExactRootFigureDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = GENERATOR.compute_figure_data()

    def test_twelve_paths_and_frozen_order(self) -> None:
        self.assertEqual(len(self.data["order"]), 12)
        self.assertEqual(len(set(self.data["order"])), 12)
        self.assertEqual(self.data["order"], GENERATOR.EXPECTED_ORDER)

    def test_all_pairs_are_strictly_disjoint(self) -> None:
        self.assertEqual(self.data["disjoint_pairs"], 66)
        intervals = self.data["intervals"]
        for index, left in enumerate(intervals):
            for right in intervals[index + 1 :]:
                self.assertLess(left.upper, right.lower)

    def test_minimum_gap_pair_and_display_value(self) -> None:
        self.assertEqual(self.data["minimum_gap_pair"], ("pv08", "pv11"))
        self.assertEqual(self.data["display_gap"], "2.50e-5")
        self.assertGreater(self.data["minimum_gap"], 0)

    def test_generator_does_not_read_g4_prospective_results(self) -> None:
        text = GENERATOR_PATH.read_text(encoding="utf-8")
        self.assertNotIn("results/g4_prospective", text)
        self.assertNotIn("g4_prospective", text)

    def test_generated_png_has_opaque_or_rgb_background(self) -> None:
        output = ROOT / "paper" / "fig2_exact_root.png"
        GENERATOR.plot_figure(self.data, output)
        try:
            from PIL import Image
        except ModuleNotFoundError:
            self.skipTest("Pillow is unavailable")

        with Image.open(output) as image:
            self.assertIn(image.mode, {"RGB", "RGBA"})
            if image.mode == "RGBA":
                alpha = image.getchannel("A")
                self.assertEqual(alpha.getextrema(), (255, 255))
            self.assertEqual(image.getpixel((0, 0))[:3], (255, 255, 255))


if __name__ == "__main__":
    unittest.main()
