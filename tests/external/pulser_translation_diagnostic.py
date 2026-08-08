#!/usr/bin/env python3
"""Validate the bundled Pulser external ordering-robustness report.

This diagnostic is intentionally separate from the Arb/Krawczyk certificate.
It checks the committed Pulser 1.9 numerical translation report and enforces
the declared external-validation scope:

- all 72 numerical cells are finite;
- the complete twelve-path ordering is unchanged;
- all 66 certified pair directions agree;
- no Pulser mean is inside the original Arb interval;
- exact translation is false;
- ordering robustness is true.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
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


def load_report(path: Path = REPORT) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_report(report: dict[str, Any]) -> None:
    metrics = report["metrics"]
    gates = report["gates"]
    path_results = report["path_results"]

    assert report["schema"] == "pulser_translation_report"
    assert int(report["schema_version"]) == 1
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

    non_claims = " ".join(report["non_claims"])
    forbidden = (
        "PASQAL hardware " + "validated",
        "exactly " + "reproduced",
        "QPU " + "verified",
    )
    for phrase in forbidden:
        assert phrase not in non_claims


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

    metrics = report["metrics"]
    print(f"Pulser external translation status: {report['scientific_status']}")
    print(
        "finite values:"
        f" {metrics['finite_numeric_values']}/{metrics['expected_numeric_values']}"
    )
    print(f"complete ordering identical: {metrics['complete_ordering_identical']}")
    print(
        "certified pair directions:"
        f" {metrics['certified_pair_directions']}/{metrics['certified_pair_expected']}"
    )
    print(
        "means inside original Arb intervals:"
        f" {metrics['means_inside_original_arb_intervals']}/"
        f"{metrics['means_inside_original_arb_expected']}"
    )
    print(f"exact translation pass: {metrics['exact_translation_pass']}")
    print(f"ordering robustness pass: {metrics['ordering_robustness_pass']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
