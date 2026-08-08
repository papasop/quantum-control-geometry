"""Regression checks for the Pulser external translation report."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT / "tools/validate_pulser_translation_report.py"
COMPARATOR = ROOT / "tools/compare_pulser_translation_reports.py"
WORKFLOW = ROOT / ".github/workflows/pulser_translation_diagnostic.yml"
SPEC = importlib.util.spec_from_file_location("pulser_translation", DIAGNOSTIC)
assert SPEC is not None and SPEC.loader is not None
PULSER_TRANSLATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PULSER_TRANSLATION)
COMPARE_SPEC = importlib.util.spec_from_file_location(
    "pulser_translation_compare", COMPARATOR
)
assert COMPARE_SPEC is not None and COMPARE_SPEC.loader is not None
PULSER_COMPARE = importlib.util.module_from_spec(COMPARE_SPEC)
COMPARE_SPEC.loader.exec_module(PULSER_COMPARE)


def cell(report: dict, path: str, error_label: str) -> dict:
    for row in report["cell_results"]:
        if row["path"] == path and row["error_label"] == error_label:
            return row
    raise AssertionError(f"Missing cell {path} {error_label}")


def path_row(report: dict, path: str) -> dict:
    for row in report["path_results"]:
        if row["path"] == path:
            return row
    raise AssertionError(f"Missing path {path}")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


class PulserTranslationReportTests(unittest.TestCase):
    def test_report_conclusion(self) -> None:
        report = PULSER_TRANSLATION.load_report()
        PULSER_TRANSLATION.validate_report(report)
        self.assertEqual(
            report["scientific_status"],
            "ORDERING_ROBUST_UNDER_PULSER_QUANTIZATION",
        )

    def test_compare_collects_all_numeric_exceedances(self) -> None:
        reference = PULSER_TRANSLATION.load_report()
        candidate = copy.deepcopy(reference)
        cell(candidate, "pv01", "amp_plus")["loss"] += 7.0e-9
        cell(candidate, "pv02", "int_minus")["loss"] += 2.0e-8
        summary = PULSER_COMPARE.audit_reports(reference, candidate)
        self.assertEqual(summary["loss"]["exceeded_count"], 2)
        labels = {
            (
                row["label"]["path"],
                row["label"]["error_label"],
            )
            for row in summary["loss"]["exceedances"]
        }
        self.assertEqual(
            labels,
            {("pv01", "amp_plus"), ("pv02", "int_minus")},
        )

    def test_compare_reports_max_difference_locations(self) -> None:
        reference = PULSER_TRANSLATION.load_report()
        candidate = copy.deepcopy(reference)
        cell(candidate, "pv01", "amp_plus")["loss"] += 7.0e-9
        cell(candidate, "pv02", "int_minus")["loss"] += 2.0e-8
        path_row(candidate, "pv07")["mean_loss"] += 2.0e-8
        path_row(candidate, "pv06")["mean_loss"] += 2.1e-8
        summary = PULSER_COMPARE.audit_reports(reference, candidate)

        self.assertEqual(
            summary["loss"]["max_absolute_difference"]["label"],
            {"path": "pv02", "error_label": "int_minus"},
        )
        self.assertEqual(
            summary["loss"]["max_relative_difference"]["label"],
            {"path": "pv01", "error_label": "amp_plus"},
        )
        self.assertEqual(
            summary["mean"]["max_absolute_difference"]["label"],
            {"path": "pv06"},
        )
        self.assertEqual(
            summary["mean"]["max_relative_difference"]["label"],
            {"path": "pv07"},
        )

    def test_compare_main_returns_one_on_numeric_exceedance(self) -> None:
        reference = PULSER_TRANSLATION.load_report()
        candidate = copy.deepcopy(reference)
        cell(candidate, "pv01", "amp_plus")["loss"] += 7.0e-9
        with tempfile.TemporaryDirectory() as tmp:
            reference_path = Path(tmp) / "reference.json"
            candidate_path = Path(tmp) / "candidate.json"
            summary_path = Path(tmp) / "summary.json"
            write_json(reference_path, reference)
            write_json(candidate_path, candidate)
            result = PULSER_COMPARE.main(
                [
                    "--reference",
                    str(reference_path),
                    "--candidate",
                    str(candidate_path),
                    "--summary",
                    str(summary_path),
                ]
            )
            self.assertEqual(result, 1)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["loss"]["exceeded_count"], 1)

    def test_compare_main_returns_zero_within_tolerance(self) -> None:
        reference = PULSER_TRANSLATION.load_report()
        candidate = copy.deepcopy(reference)
        cell(candidate, "pv01", "amp_plus")["loss"] += 1.0e-10
        with tempfile.TemporaryDirectory() as tmp:
            reference_path = Path(tmp) / "reference.json"
            candidate_path = Path(tmp) / "candidate.json"
            write_json(reference_path, reference)
            write_json(candidate_path, candidate)
            result = PULSER_COMPARE.main(
                [
                    "--reference",
                    str(reference_path),
                    "--candidate",
                    str(candidate_path),
                ]
            )
            self.assertEqual(result, 0)

    def test_compare_still_fails_on_hard_gate_change(self) -> None:
        reference = PULSER_TRANSLATION.load_report()
        candidate = copy.deepcopy(reference)
        candidate["metrics"]["complete_ordering_identical"] = False
        summary = PULSER_COMPARE.audit_reports(reference, candidate)
        self.assertFalse(summary["passed"])
        self.assertTrue(
            any("complete ordering changed" in item for item in summary["hard_gate_errors"])
        )

    def test_workflow_uploads_artifacts_even_after_failure(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("set -o pipefail", workflow)
        self.assertIn("tee /tmp/pulser_compare.log", workflow)
        self.assertIn("--summary /tmp/pulser_comparison_summary.json", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn("/tmp/pulser_compare.log", workflow)
        self.assertIn("/tmp/pulser_comparison_summary.json", workflow)


if __name__ == "__main__":
    unittest.main()
