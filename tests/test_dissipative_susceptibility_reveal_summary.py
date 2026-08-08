from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.verify_dissipative_susceptibility_reveal_summary import verify


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results/external/open_system/dissipative_susceptibility_reveal_v1_1_2_summary.json"


class DissipativeSusceptibilityRevealSummaryTests(unittest.TestCase):
    def test_frozen_summary(self) -> None:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        messages = verify(summary)
        self.assertEqual(len(messages), 5)

    def test_scope_excludes_hardware_claim(self) -> None:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        boundary = summary["claim_boundary"]
        self.assertIn("not an Arb proof", boundary)
        self.assertIn("QPU", boundary)


if __name__ == "__main__":
    unittest.main()
