"""Regression tests for bundled scientific reference artifacts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_PDF_SHA256 = (
    "b26aba45169c1ebe6a167c864a52774eaa5e185a71a34afa40360bf663a086e5"
)
VERIFY_PATH = ROOT / "tools" / "verify_reference_results.py"
SPEC = importlib.util.spec_from_file_location("verify_reference_results", VERIFY_PATH)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class ReferenceArtifactTests(unittest.TestCase):
    def test_declared_scientific_gates(self) -> None:
        messages = VERIFY.verify()
        self.assertEqual(len(messages), 9)
        self.assertIn("P0 production-preconditioner regularity: PASS", messages)
        self.assertIn(
            "Dissipative-susceptibility reveal summary gates: PASS",
            messages,
        )

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

    def test_short_title_is_synchronized(self) -> None:
        expected = "Exact-Root Certification of Finite-Error Ordering in Quantum Control"
        obsolete = "Geometric Prediction and Exact-Root Certification"
        for relative in ("README.md", "CITATION.cff", "REVIEWER_GUIDE.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(expected, " ".join(text.split()))
            self.assertNotIn(obsolete, text)

    def test_published_doi_is_synchronized(self) -> None:
        doi = "10.5281/zenodo.21831180"
        for relative in ("README.md", "CITATION.cff", "REVIEWER_GUIDE.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(doi, text)

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

    def test_reviewer_navigation_paths_exist(self) -> None:
        expected = (
            "docs/pulser_translation_scope.md",
            "docs/blind_pulser_response_fibre_scope.md",
            "docs/open_system_ordering_survival_scope.md",
            "results/external/pulser_translation_report.json",
            "results/external/pasqal_blind_response_fibre_v1_0_summary.json",
            "results/external/open_system/pasqal_open_system_ordering_survival_v1_0_protocol.json",
            "results/external/open_system/pasqal_open_system_ordering_survival_v1_0_summary.json",
            "tests/external/recompute_pulser_translation.py",
            "tests/external/pasqal_blind_response_fibre_v1_0.py",
            "tests/external/pasqal_open_system_ordering_survival_v1_0.py",
            "tools/validate_pulser_translation_report.py",
            "tools/compare_pulser_translation_reports.py",
            "tools/verify_blind_pulser_summary.py",
            "tools/verify_open_system_ordering_survival_v1_0.py",
            ".github/workflows/pulser_translation_diagnostic.yml",
            ".github/workflows/blind_pulser_response_fibre.yml",
            ".github/workflows/open_system_ordering_survival.yml",
        )
        for relative in expected:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_pulser_navigation_values_match_frozen_json(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        guide = (ROOT / "REVIEWER_GUIDE.md").read_text(encoding="utf-8")
        pulser = json.loads(
            (ROOT / "results/external/pulser_translation_report.json").read_text(
                encoding="utf-8"
            )
        )
        blind = json.loads(
            (
                ROOT
                / "results/external/pasqal_blind_response_fibre_v1_0_summary.json"
            ).read_text(encoding="utf-8")
        )

        metrics = pulser["metrics"]
        self.assertEqual(metrics["finite_numeric_values"], 72)
        self.assertEqual(metrics["certified_pair_directions"], 66)
        self.assertIn("12 paths x 6 error points = 72 propagations", readme)
        self.assertIn("66/66 unordered path pairs", readme)
        self.assertIn("exact_translation_pass = false", readme)
        self.assertIn("ordering_robustness_pass = true", readme)

        blind_metrics = blind["metrics"]
        self.assertEqual(blind_metrics["propagations"], 120)
        self.assertIn("20 paths x 6 error points = 120 propagations", readme)
        self.assertIn(str(blind_metrics["spearman_prediction_vs_pulser"]), readme)
        self.assertIn(str(blind_metrics["one_sided_permutation_p"]), readme)
        self.assertIn(str(blind_metrics["best_vs_worst_mean_loss_advantage"]), readme)
        self.assertIn(blind["source_protocol_sha256"], readme)
        self.assertIn(blind["prediction_freeze_sha256"], readme)
        self.assertIn("Pulser is not Arb", guide)
        self.assertIn("Pulser is not PASQAL Cloud", guide)

    def test_open_system_navigation_values_match_frozen_summary(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        guide = (ROOT / "REVIEWER_GUIDE.md").read_text(encoding="utf-8")
        scope = (ROOT / "docs/open_system_ordering_survival_scope.md").read_text(
            encoding="utf-8"
        )
        summary = json.loads(
            (
                ROOT
                / "results/external/open_system/"
                / "pasqal_open_system_ordering_survival_v1_0_summary.json"
            ).read_text(encoding="utf-8")
        )

        normalized_readme = " ".join(readme.split())
        normalized_scope = " ".join(scope.split())
        coverage = summary["coverage"]
        self.assertEqual(coverage["planned_propagations"], 2088)
        self.assertEqual(coverage["completed_propagations"], 2088)
        self.assertTrue(coverage["all_finite"])
        self.assertEqual(summary["unitary_reconstruction"]["pair_directions_preserved"], 66)
        self.assertEqual(summary["pairs"]["never_flipped_on_declared_grid"], 55)
        self.assertEqual(summary["minimum_margin_pair"], "pv08>pv11")
        self.assertEqual(summary["scientific_status"], "OPEN_SYSTEM_STRESS_AUDIT_COMPLETE")

        self.assertIn("2088 propagations", normalized_readme)
        self.assertIn("55/66 path pairs never flip", normalized_readme)
        self.assertIn(
            "scientific_status = OPEN_SYSTEM_STRESS_AUDIT_COMPLETE",
            normalized_readme,
        )
        self.assertIn("not an interval proof", normalized_readme)
        self.assertIn("not a Pulser execution", normalized_readme)
        self.assertIn("not a PASQAL Cloud run", normalized_readme)
        self.assertIn("not a physical QPU", normalized_readme)
        self.assertIn("2088-propagation open-system stress workflow", guide)
        self.assertIn(summary["protocol_sha256"], scope)
        self.assertIn(
            "not independently hash-frozen before outcome reveal",
            normalized_scope,
        )

    def test_pulser_workflows_use_current_artifact_action(self) -> None:
        for relative in (
            ".github/workflows/pulser_translation_diagnostic.yml",
            ".github/workflows/blind_pulser_response_fibre.yml",
            ".github/workflows/open_system_ordering_survival.yml",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("actions/upload-artifact@v7", text)
            self.assertNotIn("actions/upload-artifact@v5", text)
            self.assertIn("workflow_dispatch", text)

    def test_pulser_docs_do_not_overclaim_hardware(self) -> None:
        for relative in (
            "README.md",
            "REVIEWER_GUIDE.md",
            "docs/pulser_translation_scope.md",
            "docs/blind_pulser_response_fibre_scope.md",
            "docs/open_system_ordering_survival_scope.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("PASQAL hardware validated", text)
            self.assertNotIn("QPU verified", text)
            self.assertNotIn("FRESNEL validation", text)


if __name__ == "__main__":
    unittest.main()
