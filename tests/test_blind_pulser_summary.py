"""Regression gate for the committed blind-Pulser summary."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results/external/pasqal_blind_response_fibre_v1_0_summary.json"


class BlindPulserSummaryTests(unittest.TestCase):
    def test_predeclared_gates(self) -> None:
        report = json.loads(SUMMARY.read_text(encoding="utf-8"))
        self.assertFalse(report["source_outcomes_unlocked"])
        self.assertEqual(report["metrics"]["propagations"], 120)
        self.assertGreaterEqual(
            report["metrics"]["spearman_prediction_vs_pulser"], 0.80
        )
        self.assertLess(report["metrics"]["one_sided_permutation_p"], 0.05)
        self.assertGreater(
            report["metrics"]["best_vs_worst_bootstrap_ci95"][0], 0.0
        )
        self.assertEqual(
            report["scientific_status"],
            "BLIND_PULSER_RESPONSE_FIBRE_PREDICTION_SUPPORTED",
        )


if __name__ == "__main__":
    unittest.main()

