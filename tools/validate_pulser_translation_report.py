#!/usr/bin/env python3
"""Validate a Pulser external ordering-robustness report."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "results/external/pulser_translation_report.json"
EXPECTED_STATUS = "ORDERING_ROBUST_UNDER_PULSER_QUANTIZATION"
EXPECTED_ORDER = [
    "pv07",
    "pv01",
    "pv10",
    "pv05",
    "pv04",
    "pv02",
    "pv08",
    "pv11",
    "pv09",
    "pv03",
    "pv12",
    "pv06",
]
EXPECTED_ERRORS = [
    "amp_minus",
    "amp_plus",
    "det_minus",
    "det_plus",
    "int_minus",
    "int_plus",
]


def load_report(path: Path = REPORT) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_report(report: dict[str, Any]) -> None:
    metrics = report["metrics"]
    gates = report["gates"]
    path_results = report["path_results"]
    cell_results = report.get("cell_results", [])
    pair_directions = report.get("pair_directions", [])

    assert report["schema"] == "pulser_translation_report"
    assert int(report["schema_version"]) == 2
    assert report["toolchain"]["pulser"] == "1.9.0"
    assert report["scientific_status"] == EXPECTED_STATUS
    assert report["path_order"] == EXPECTED_ORDER

    assert metrics["finite_numeric_values"] == 72
    assert metrics["expected_numeric_values"] == 72
    assert metrics["complete_ordering_identical"] is True
    assert metrics["path_ordering_matches"] == 12
    assert metrics["path_ordering_expected"] == 12
    assert metrics["certified_pair_directions"] == 66
    assert metrics["certified_pair_expected"] == 66
    assert metrics["means_inside_original_arb_intervals"] == 0
    assert metrics["means_inside_original_arb_expected"] == 12
    assert metrics["exact_translation_pass"] is False
    assert metrics["ordering_robustness_pass"] is True

    assert gates["finite_numeric_values_72_of_72"] is True
    assert gates["complete_ordering_identical"] is True
    assert gates["certified_pair_directions_66_of_66"] is True
    assert gates["original_arb_interval_membership_0_of_12"] is True
    assert gates["exact_translation_pass"] is False
    assert gates["ordering_robustness_pass"] is True

    assert len(path_results) == 12
    assert {row["path"] for row in path_results} == {
        f"pv{index:02d}" for index in range(1, 13)
    }
    assert sum(int(row["finite_values"]) for row in path_results) == 72
    assert not any(
        bool(row["mean_inside_original_arb_interval"]) for row in path_results
    )
    for row in path_results:
        assert math.isfinite(float(row["mean_loss"]))
        assert len(row["losses"]) == 6
        assert [cell["error_label"] for cell in row["losses"]] == EXPECTED_ERRORS
        assert all(math.isfinite(float(cell["loss"])) for cell in row["losses"])

    assert len(cell_results) == 72
    assert all(math.isfinite(float(row["loss"])) for row in cell_results)
    assert {
        (row["path"], row["error_label"]) for row in cell_results
    } == {
        (f"pv{path_index:02d}", error)
        for path_index in range(1, 13)
        for error in EXPECTED_ERRORS
    }

    assert len(pair_directions) == 66
    assert all(row["agrees_with_frozen_order"] is True for row in pair_directions)

    non_claims = " ".join(report["non_claims"])
    forbidden = (
        "PASQAL hardware " + "validated",
        "exactly " + "reproduced",
        "QPU " + "verified",
    )
    for phrase in forbidden:
        assert phrase not in non_claims


def summarize(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    return "\n".join(
        [
            f"Pulser external translation status: {report['scientific_status']}",
            (
                "finite values:"
                f" {metrics['finite_numeric_values']}/"
                f"{metrics['expected_numeric_values']}"
            ),
            f"complete ordering identical: {metrics['complete_ordering_identical']}",
            (
                "certified pair directions:"
                f" {metrics['certified_pair_directions']}/"
                f"{metrics['certified_pair_expected']}"
            ),
            (
                "means inside original Arb intervals:"
                f" {metrics['means_inside_original_arb_intervals']}/"
                f"{metrics['means_inside_original_arb_expected']}"
            ),
            f"exact translation pass: {metrics['exact_translation_pass']}",
            f"ordering robustness pass: {metrics['ordering_robustness_pass']}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report",
        default=str(REPORT),
        help="Path to the Pulser translation report JSON.",
    )
    args = parser.parse_args(argv)
    report = load_report(Path(args.report))
    validate_report(report)
    print(summarize(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
