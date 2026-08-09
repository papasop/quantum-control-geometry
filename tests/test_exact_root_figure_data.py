"""Semantic checks for the exact-root Figure 2 data pipeline."""

from __future__ import annotations

import importlib.util
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "paper" / "scripts" / "generate_fig2_exact_root.py"
SPEC = importlib.util.spec_from_file_location("generate_fig2_exact_root", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATOR
SPEC.loader.exec_module(GENERATOR)


def read_png_ihdr_and_pixels(path: Path) -> tuple[int, int, int, bytes]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError("invalid PNG signature")

    offset = 8
    width = height = color_type = None
    idat_parts = []
    while offset < len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filtering, interlace = (
                struct.unpack(">IIBBBBB", chunk_data)
            )
            if bit_depth != 8 or compression != 0 or filtering != 0 or interlace != 0:
                raise AssertionError("unsupported PNG IHDR for dependency-free check")
        elif chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    if width is None or height is None or color_type is None:
        raise AssertionError("missing PNG IHDR")
    if width <= 0 or height <= 0:
        raise AssertionError("non-positive PNG dimensions")

    channels = {2: 3, 6: 4}.get(color_type)
    if channels is None:
        raise AssertionError(f"unexpected PNG color type: {color_type}")
    row_size = width * channels
    raw = zlib.decompress(b"".join(idat_parts))
    rows = []
    previous = bytearray(row_size)
    cursor = 0
    for _ in range(height):
        filter_type = raw[cursor]
        cursor += 1
        current = bytearray(raw[cursor : cursor + row_size])
        cursor += row_size
        for idx, value in enumerate(current):
            left = current[idx - channels] if idx >= channels else 0
            up = previous[idx]
            upper_left = previous[idx - channels] if idx >= channels else 0
            if filter_type == 1:
                current[idx] = (value + left) & 0xFF
            elif filter_type == 2:
                current[idx] = (value + up) & 0xFF
            elif filter_type == 3:
                current[idx] = (value + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                predictor = left + up - upper_left
                pa = abs(predictor - left)
                pb = abs(predictor - up)
                pc = abs(predictor - upper_left)
                predicted = left if pa <= pb and pa <= pc else up if pb <= pc else upper_left
                current[idx] = (value + predicted) & 0xFF
            elif filter_type != 0:
                raise AssertionError(f"unsupported PNG filter type: {filter_type}")
        rows.append(bytes(current))
        previous = current
    return width, height, color_type, b"".join(rows)


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

    def test_committed_png_signature_dimensions_and_opacity(self) -> None:
        width, height, color_type, pixels = read_png_ihdr_and_pixels(
            ROOT / "paper" / "fig2_exact_root.png"
        )
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)
        self.assertIn(color_type, {2, 6})
        if color_type == 6:
            self.assertTrue(all(alpha == 255 for alpha in pixels[3::4]))

    def test_generator_saves_with_white_opaque_background(self) -> None:
        text = GENERATOR_PATH.read_text(encoding="utf-8")
        self.assertIn('facecolor="white"', text)
        self.assertIn("transparent=False", text)

    def test_generated_png_has_opaque_or_rgb_background(self) -> None:
        if importlib.util.find_spec("matplotlib") is None:
            self.skipTest("plot regeneration requires optional matplotlib/Pillow dependencies")
        if importlib.util.find_spec("PIL") is None:
            self.skipTest("plot regeneration requires optional matplotlib/Pillow dependencies")

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "fig2_exact_root.png"
            GENERATOR.plot_figure(self.data, output)

            from PIL import Image

            with Image.open(output) as image:
                self.assertIn(image.mode, {"RGB", "RGBA"})
                if image.mode == "RGBA":
                    alpha = image.getchannel("A")
                    self.assertEqual(alpha.getextrema(), (255, 255))
                self.assertEqual(image.getpixel((0, 0))[:3], (255, 255, 255))


if __name__ == "__main__":
    unittest.main()
