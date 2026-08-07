"""Regression tests for bundled scientific reference artifacts."""

from __future__ import annotations

import hashlib
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_PDF_SHA256 = (
    "378c0c5d92fc18e49d409ddfcc3dba649eb9e78098fdf27dc3c99c0480875a76"
)
VERIFY_PATH = ROOT / "tools" / "verify_reference_results.py"
SPEC = importlib.util.spec_from_file_location("verify_reference_results", VERIFY_PATH)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class ReferenceArtifactTests(unittest.TestCase):
    def test_declared_scientific_gates(self) -> None:
        messages = VERIFY.verify()
        self.assertEqual(len(messages), 7)

    def test_standalone_entry_points_exist(self) -> None:
        expected = (
            "external_reproduce_v0_3_1.py",
            "pasqal_two_atom_G4_standalone_colab.py",
            "pasqal_L3_L4_standalone_colab.py",
            "pasqal_L4_order30_standalone_colab.py",
            "pasqal_L4_formal_arb_standalone_colab.py",
            "pasqal_L4_exact_fibre_krawczyk_standalone_colab_v1_2.py",
            "pasqal_L4_exact_root_ordering_standalone_colab.py",
            "pasqal_L4_reproducible_certificate_v1_3_colab.py",
        )
        for name in expected:
            self.assertTrue((ROOT / "scripts" / "standalone" / name).is_file())

    def test_manuscript_exists(self) -> None:
        self.assertTrue((ROOT / "paper" / "main.tex").is_file())
        self.assertTrue((ROOT / "paper" / "manuscript.pdf").is_file())

    def test_manuscript_pdf_hash_matches_submission_version(self) -> None:
        digest = hashlib.sha256(
            (ROOT / "paper" / "manuscript.pdf").read_bytes()
        ).hexdigest()
        self.assertEqual(digest, MANUSCRIPT_PDF_SHA256)

    def test_clean_environment_notebook_exists(self) -> None:
        self.assertTrue((ROOT / "notebooks" / "reproduce_v0_3_1.ipynb").is_file())

    def test_readme_quartic_counts_match_formal_report(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        formal = VERIFY.load_json("results/l4_formal/report.json")
        certified = int(VERIFY.field(formal, "G4_certified_pairs"))
        possible = int(VERIFY.field(formal, "possible_pairs"))
        coverage = 100.0 * float(VERIFY.field(formal, "G4_pair_coverage"))
        public_count = f"{certified}/{possible}"
        public_coverage = f"{coverage:.2f}%"

        self.assertEqual(public_count, "34/66")
        self.assertIn(
            "| Quartic-only serialized-control audit | "
            f"{public_count} ({public_coverage}) |",
            readme,
        )
        self.assertIn(f"The {public_count} quartic result", readme)
        self.assertIn(
            f"Partial pairwise certification: {public_count} ({public_coverage})",
            readme,
        )
        self.assertNotIn("35/66", readme)


if __name__ == "__main__":
    unittest.main()
