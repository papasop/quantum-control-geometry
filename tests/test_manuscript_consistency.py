"""Consistency checks between the manuscript and frozen artifacts."""

from __future__ import annotations

import importlib.util
import copy
import re
import shutil
import subprocess
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_ROOT = ROOT / "paper" / "main.tex"
MANUSCRIPT_PARTS = (
    ROOT / "paper" / "main.tex",
    ROOT / "paper" / "sec_front.tex",
    ROOT / "paper" / "sec_mid.tex",
    ROOT / "paper" / "sec_back.tex",
)
VERIFY_PATH = ROOT / "tools" / "verify_reference_results.py"
SPEC = importlib.util.spec_from_file_location("verify_reference_results", VERIFY_PATH)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


EXPECTED_TITLE = (
    "Exact-Root Certification of Finite-Error Ordering\\\\ "
    "in Quantum Control"
)
REPOSITORY_URL = "https://github.com/papasop/quantum-control-geometry"
FROZEN_COMMIT = "284974c9f6b952f4e114c8c5bdc9c2c299c4065c"
PHASE_ALIGNMENT_FRAGMENTS = (
    "projective output state",
    "first projective response",
)
REQUIRED_BOUNDARY_FRAGMENTS = (
    "response to the declared global error coordinates",
    "pairwise disjoint and totally ordered",
    "pre-outcome ordering frozen for the independent twelve-path",
    "global fibre structure remains open",
)
FORBIDDEN_G4_EXACT_SAMPLE = "0.996992"


def extract_pdf_text_forbidden_scan(path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if pdftotext is not None:
        result = subprocess.run(
            [pdftotext, str(path), "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    # Dependency-light fallback for CI jobs without poppler: inspect raw
    # and FlateDecode streams for ASCII text fragments such as stale numbers.
    data = path.read_bytes()
    chunks = [data]
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        stream = match.group(1)
        chunks.append(stream)
        try:
            chunks.append(zlib.decompress(stream))
        except zlib.error:
            pass
    return "\n".join(
        chunk.decode("latin-1", errors="ignore") for chunk in chunks
    )


class ManuscriptConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        manuscript = "\n".join(
            path.read_text(encoding="utf-8") for path in MANUSCRIPT_PARTS
        )
        cls.manuscript_source = manuscript
        cls.manuscript = " ".join(manuscript.split())
        cls.manuscript_pdf_text = extract_pdf_text_forbidden_scan(
            ROOT / "paper" / "manuscript.pdf"
        )
        cls.g4 = VERIFY.load_json("results/g4_prospective/report.json")
        cls.formal = VERIFY.load_json("results/l4_formal/report.json")
        cls.krawczyk = VERIFY.load_json("results/exact_fibre_krawczyk/report.json")
        cls.exact_root = VERIFY.load_json("results/exact_root_ordering/report.json")

    def assert_g4_threshold_claim_consistent(self, g4: dict) -> None:
        self.assertEqual(g4["claim_level"], "threshold")
        threshold = float(g4["predeclared_mean_spearman_minimum"])
        self.assertEqual(threshold, 0.95)
        self.assertGreaterEqual(
            float(g4["validation"]["mean_spearman"]), threshold
        )
        self.assertTrue(g4["gates"]["primary_spearman_gate"])
        self.assertFalse(g4["cross_architecture_exact_value_invariant"])
        self.assertFalse(g4["cross_architecture_top_path_invariant"])

        for sample in g4.get("cross_architecture_observations", {}).get(
            "samples", []
        ):
            with self.subTest(architecture_sample=sample["label"]):
                self.assertGreaterEqual(
                    float(sample["mean_spearman"]), threshold
                )
                self.assertTrue(sample["primary_spearman_gate_pass"])

        threshold_fragments = (
            r"\rho_{\mathrm{Spearman}}\ge 0.95",
            "predeclared gate",
        )
        for fragment in threshold_fragments:
            with self.subTest(g4_threshold_fragment=fragment):
                self.assertIn(fragment, self.manuscript)

    def test_manuscript_contains_artifact_values(self) -> None:
        quartic_pairs = int(VERIFY.field(self.formal, "G4_certified_pairs"))
        possible_pairs = int(VERIFY.field(self.formal, "possible_pairs"))
        quartic_coverage = 100.0 * float(
            VERIFY.field(self.formal, "G4_pair_coverage")
        )
        krawczyk_paths = int(self.krawczyk["evaluated_paths"])
        order30_pairs = int(self.exact_root["order30_certified_pairs"])
        direct_pairs = int(self.exact_root["direct_certified_pairs"])

        expected_fragments = (
            f"{quartic_pairs}/{possible_pairs}",
            f"{quartic_coverage:.2f}\\%",
            f"{krawczyk_paths}/{krawczyk_paths}",
            f"{order30_pairs}/{possible_pairs}",
            f"{direct_pairs}/{possible_pairs}",
            "twenty-path cohort",
            "twelve-path formal cohort",
            EXPECTED_TITLE,
            *PHASE_ALIGNMENT_FRAGMENTS,
            *REQUIRED_BOUNDARY_FRAGMENTS,
            REPOSITORY_URL,
            FROZEN_COMMIT,
        )
        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.manuscript)
        self.assert_g4_threshold_claim_consistent(self.g4)

    def test_g4_threshold_accepts_alternate_passing_platform_sample(self) -> None:
        g4 = copy.deepcopy(self.g4)
        g4["validation"]["mean_spearman"] = 0.9894736842
        g4["gates"]["primary_spearman_gate"] = True
        g4["validation"]["predicted_order_best_to_worst"][0] = "pv02"
        g4["validation"]["actual_mean_order_best_to_worst"][0] = "pv02"
        self.assert_g4_threshold_claim_consistent(g4)

    def test_g4_threshold_rejects_subthreshold_report(self) -> None:
        g4 = copy.deepcopy(self.g4)
        g4["validation"]["mean_spearman"] = 0.949
        g4["gates"]["primary_spearman_gate"] = False
        with self.assertRaises(AssertionError):
            self.assert_g4_threshold_claim_consistent(g4)

    def test_g4_threshold_requires_predeclared_threshold(self) -> None:
        g4 = copy.deepcopy(self.g4)
        del g4["predeclared_mean_spearman_minimum"]
        with self.assertRaises(KeyError):
            self.assert_g4_threshold_claim_consistent(g4)

    def test_g4_threshold_does_not_depend_on_platform_top_path(self) -> None:
        g4 = copy.deepcopy(self.g4)
        g4["validation"]["predicted_order_best_to_worst"][0] = "pv02"
        g4["validation"]["actual_mean_order_best_to_worst"][0] = "pv02"
        g4["validation"]["top1_pass"] = True
        g4["gates"]["top1_gate"] = True
        self.assert_g4_threshold_claim_consistent(g4)

    def test_formal_l4_values_remain_exact_value_consistent(self) -> None:
        possible_pairs = int(VERIFY.field(self.formal, "possible_pairs"))
        exact_fragments = (
            f"{int(VERIFY.field(self.formal, 'G4_certified_pairs'))}/{possible_pairs}",
            f"{100.0 * float(VERIFY.field(self.formal, 'G4_pair_coverage')):.2f}\\%",
            f"{int(self.krawczyk['evaluated_paths'])}/{int(self.krawczyk['evaluated_paths'])}",
            f"{int(self.exact_root['order30_certified_pairs'])}/{possible_pairs}",
            f"{int(self.exact_root['direct_certified_pairs'])}/{possible_pairs}",
        )
        for fragment in exact_fragments:
            with self.subTest(formal_fragment=fragment):
                self.assertIn(fragment, self.manuscript)

    def test_manuscript_rejects_stale_values(self) -> None:
        stale_fragments = (
            FORBIDDEN_G4_EXACT_SAMPLE,
            r"\eta_{F}",
            r"\II_{\gamma}(0)",
            r"\braket{\psi_{\mathrm{ref}}}{\psi_{\gamma}(0)}",
            "0.998496",
            "35/66",
            "53.03\\%",
            "Finite-Error Robustness in Quantum Control",
            "response to calibrated errors",
            "twelve pairwise ordered performance intervals",
            "the minimal interacting setting",
            "Geometric Prediction and Exact-Root Certification",
            "computed independently of the direct theorem",
            "computationally independent mechanism certificate",
        )
        for fragment in stale_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, self.manuscript_source)

    def test_mathematical_corrections_are_present(self) -> None:
        required_source_fragments = (
            r"c_{\gamma}=\frac{\braket{\psi_{\gamma}(0)}{\psi_{\mathrm{ref}}}}",
            r"\Iref_{\gamma}(0)\le\eta",
            "separate mechanism certificates, not used in the direct theorem",
            "computationally distinct mechanism certificate",
            "Rump--Neumann",
            "p0_preconditioner_certificate.json",
            r"\lVert I-R_{k}C_{k}\rVert_{\infty}<1",
            "12/12",
            "not a second full interval ordering proof",
        )
        for fragment in required_source_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.manuscript_source)

    def test_pdf_rejects_legacy_g4_exact_sample(self) -> None:
        self.assertNotIn(
            FORBIDDEN_G4_EXACT_SAMPLE,
            self.manuscript_pdf_text,
        )

    def test_main_tex_is_canonical_entry_point(self) -> None:
        self.assertTrue(MANUSCRIPT_ROOT.is_file())
        self.assertFalse((ROOT / "paper" / "manuscript.tex").exists())
        self.assertIn("\\input{sec_front}", MANUSCRIPT_ROOT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
