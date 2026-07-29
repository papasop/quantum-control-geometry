"""Regression tests for bundled scientific reference artifacts."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / "tools" / "verify_reference_results.py"
SPEC = importlib.util.spec_from_file_location("verify_reference_results", VERIFY_PATH)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class ReferenceArtifactTests(unittest.TestCase):
    def test_declared_scientific_gates(self) -> None:
        messages = VERIFY.verify()
        self.assertEqual(len(messages), 4)

    def test_standalone_entry_points_exist(self) -> None:
        expected = (
            "pasqal_two_atom_G4_standalone_colab.py",
            "pasqal_L3_L4_standalone_colab.py",
            "pasqal_L4_order30_standalone_colab.py",
            "pasqal_L4_formal_arb_standalone_colab.py",
        )
        for name in expected:
            self.assertTrue((ROOT / "scripts" / "standalone" / name).is_file())

    def test_manuscript_exists(self) -> None:
        self.assertTrue((ROOT / "paper" / "manuscript.tex").is_file())


if __name__ == "__main__":
    unittest.main()
