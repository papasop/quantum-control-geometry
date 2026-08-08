"""Regression checks for the Pulser external translation report."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT / "tools/validate_pulser_translation_report.py"
SPEC = importlib.util.spec_from_file_location("pulser_translation", DIAGNOSTIC)
assert SPEC is not None and SPEC.loader is not None
PULSER_TRANSLATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PULSER_TRANSLATION)


class PulserTranslationReportTests(unittest.TestCase):
    def test_report_conclusion(self) -> None:
        report = PULSER_TRANSLATION.load_report()
        PULSER_TRANSLATION.validate_report(report)
        self.assertEqual(
            report["scientific_status"],
            "ORDERING_ROBUST_UNDER_PULSER_QUANTIZATION",
        )


if __name__ == "__main__":
    unittest.main()
