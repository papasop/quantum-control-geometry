#!/usr/bin/env python3
"""Compare committed and recomputed Pulser translation reports."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


EXPECTED_STATUS = "ORDERING_ROBUST_UNDER_PULSER_QUANTIZATION"
LOSS_ABS_TOL = 5.0e-9
LOSS_REL_TOL = 5.0e-8
MEAN_ABS_TOL = 5.0e-9
MEAN_REL_TOL = 5.0e-8


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def assert_close(label: str, reference: float, candidate: float, *, abs_tol: float, rel_tol: float) -> None:
    if not math.isclose(reference, candidate, abs_tol=abs_tol, rel_tol=rel_tol):
        raise AssertionError(
            f"{label}: {candidate:.17g} differs from reference "
            f"{reference:.17g} beyond abs={abs_tol:g}, rel={rel_tol:g}"
        )


def keyed(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {tuple(row[key] for key in keys): row for row in rows}


def compare_reports(reference: dict[str, Any], candidate: dict[str, Any]) -> None:
    for report_name, report in (("reference", reference), ("candidate", candidate)):
        metrics = report["metrics"]
        if metrics["finite_numeric_values"] != 72:
            raise AssertionError(f"{report_name}: expected 72 finite numeric values")
        if metrics["complete_ordering_identical"] is not True:
            raise AssertionError(f"{report_name}: complete ordering changed")
        if metrics["certified_pair_directions"] != 66:
            raise AssertionError(f"{report_name}: expected 66/66 pair directions")
        if metrics["means_inside_original_arb_intervals"] != 0:
            raise AssertionError(f"{report_name}: expected 0/12 Arb interval memberships")
        if metrics["exact_translation_pass"] is not False:
            raise AssertionError(f"{report_name}: exact translation must remain false")
        if metrics["ordering_robustness_pass"] is not True:
            raise AssertionError(f"{report_name}: ordering robustness must pass")
        if report["scientific_status"] != EXPECTED_STATUS:
            raise AssertionError(f"{report_name}: unexpected scientific status")

    if candidate["path_order"] != reference["path_order"]:
        raise AssertionError("candidate path order differs from reference")

    reference_cells = keyed(reference["cell_results"], ("path", "error_label"))
    candidate_cells = keyed(candidate["cell_results"], ("path", "error_label"))
    if set(candidate_cells) != set(reference_cells):
        raise AssertionError("candidate cell set differs from reference")
    for key, row in reference_cells.items():
        assert_close(
            f"loss {key[0]} {key[1]}",
            float(row["loss"]),
            float(candidate_cells[key]["loss"]),
            abs_tol=LOSS_ABS_TOL,
            rel_tol=LOSS_REL_TOL,
        )

    reference_paths = keyed(reference["path_results"], ("path",))
    candidate_paths = keyed(candidate["path_results"], ("path",))
    if set(candidate_paths) != set(reference_paths):
        raise AssertionError("candidate path set differs from reference")
    for key, row in reference_paths.items():
        assert_close(
            f"mean {key[0]}",
            float(row["mean_loss"]),
            float(candidate_paths[key]["mean_loss"]),
            abs_tol=MEAN_ABS_TOL,
            rel_tol=MEAN_REL_TOL,
        )
        if (
            bool(row["mean_inside_original_arb_interval"])
            != bool(candidate_paths[key]["mean_inside_original_arb_interval"])
        ):
            raise AssertionError(f"{key[0]}: Arb interval membership changed")

    if candidate["pair_directions"] != reference["pair_directions"]:
        raise AssertionError("candidate pair directions differ from reference")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args(argv)
    reference = load_json(Path(args.reference))
    candidate = load_json(Path(args.candidate))
    compare_reports(reference, candidate)
    print("Pulser translation reports match within declared tolerances.")
    print(f"loss tolerance: abs={LOSS_ABS_TOL:g}, rel={LOSS_REL_TOL:g}")
    print(f"mean tolerance: abs={MEAN_ABS_TOL:g}, rel={MEAN_REL_TOL:g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
