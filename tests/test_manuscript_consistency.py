"""Consistency checks between the manuscript and frozen artifacts."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "paper" / "manuscript.tex"
VERIFY_PATH = ROOT / "tools" / "verify_reference_results.py"
SPEC = importlib.util.spec_from_file_location("verify_reference_results", VERIFY_PATH)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


EXPECTED_TITLE = (
    "Geometric Prediction and Exact-Root Certification of\\\\\n"
    "Finite-Error Ordering in Quantum Control"
)
REPOSITORY_URL = "https://github.com/papasop/quantum-control-geometry"
FROZEN_COMMIT = "284974c9f6b952f4e114c8c5bdc9c2c299c4065c"
PHASE_FACTOR = (
    "c_\\gamma=\n"
    "\\frac{\\overline{\\langle\\psi_{\\mathrm{ref}}|\\psi_\\gamma(\\mathbf 0)\\rangle}}\n"
    "{|\\langle\\psi_{\\mathrm{ref}}|\\psi_\\gamma(\\mathbf 0)\\rangle|}."
)


class ManuscriptConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manuscript = MANUSCRIPT.read_text(encoding="utf-8")
        cls.g4 = VERIFY.load_json("results/g4_prospective/report.json")
        cls.formal = VERIFY.load_json("results/l4_formal/report.json")
        cls.krawczyk = VERIFY.load_json("results/exact_fibre_krawczyk/report.json")
        cls.exact_root = VERIFY.load_json("results/exact_root_ordering/report.json")

    def test_manuscript_contains_artifact_values(self) -> None:
        spearman = float(self.g4["validation"]["mean_spearman"])
        quartic_pairs = int(VERIFY.field(self.formal, "G4_certified_pairs"))
        possible_pairs = int(VERIFY.field(self.formal, "possible_pairs"))
        quartic_coverage = 100.0 * float(
            VERIFY.field(self.formal, "G4_pair_coverage")
        )
        krawczyk_paths = int(self.krawczyk["evaluated_paths"])
        order30_pairs = int(self.exact_root["order30_certified_pairs"])
        direct_pairs = int(self.exact_root["direct_certified_pairs"])

        expected_fragments = (
            f"{spearman:.6f}",
            f"{quartic_pairs}/{possible_pairs}",
            f"{quartic_coverage:.2f}\\%",
            f"{krawczyk_paths}/{krawczyk_paths}",
            f"{order30_pairs}/{possible_pairs}",
            f"{direct_pairs}/{possible_pairs}",
            "twenty-path cohort",
            "twelve-path formal cohort",
            EXPECTED_TITLE,
            PHASE_FACTOR,
            REPOSITORY_URL,
            FROZEN_COMMIT,
        )
        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.manuscript)

    def test_manuscript_rejects_stale_values(self) -> None:
        stale_fragments = (
            "0.998496",
            "35/66",
            "53.03\\%",
            "Finite-Error Robustness in Quantum Control",
        )
        for fragment in stale_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, self.manuscript)


if __name__ == "__main__":
    unittest.main()
