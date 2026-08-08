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
# GitHub-hosted runner run 31234420564 observed maximum loss drift
# 1.43549e-8. The 2e-8 tolerance is about 0.019% of the minimum
# committed path-mean ordering gap, approximately 1.05078e-4.
LOSS_ABS_TOL = 2.0e-8
LOSS_REL_TOL = 5.0e-8
MEAN_ABS_TOL = 5.0e-9
MEAN_REL_TOL = 5.0e-8


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def keyed(
    rows: list[dict[str, Any]],
    keys: tuple[str, ...],
) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {tuple(row[key] for key in keys): row for row in rows}


def relative_difference(reference: float, candidate: float) -> float:
    difference = abs(candidate - reference)
    scale = abs(reference)
    if scale == 0.0:
        return 0.0 if difference == 0.0 else math.inf
    return difference / scale


def numeric_record(
    *,
    kind: str,
    label: dict[str, str],
    reference: float,
    candidate: float,
    abs_tol: float,
    rel_tol: float,
) -> dict[str, Any]:
    abs_diff = abs(candidate - reference)
    rel_diff = relative_difference(reference, candidate)
    allowed_abs_diff = max(abs_tol, rel_tol * abs(reference))
    exceeded = abs_diff > allowed_abs_diff
    return {
        "kind": kind,
        "label": label,
        "reference": reference,
        "candidate": candidate,
        "absolute_difference": abs_diff,
        "relative_difference": rel_diff,
        "absolute_tolerance": abs_tol,
        "relative_tolerance": rel_tol,
        "allowed_absolute_difference": allowed_abs_diff,
        "exceeded": exceeded,
    }


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "count": 0,
            "exceeded_count": 0,
            "max_absolute_difference": None,
            "max_relative_difference": None,
            "exceedances": [],
        }
    max_abs = max(records, key=lambda row: row["absolute_difference"])
    max_rel = max(records, key=lambda row: row["relative_difference"])
    exceedances = [row for row in records if row["exceeded"]]
    return {
        "count": len(records),
        "exceeded_count": len(exceedances),
        "max_absolute_difference": max_abs,
        "max_relative_difference": max_rel,
        "exceedances": exceedances,
    }


def validate_hard_gates(
    reference: dict[str, Any],
    candidate: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for report_name, report in (("reference", reference), ("candidate", candidate)):
        metrics = report["metrics"]
        if metrics["finite_numeric_values"] != 72:
            errors.append(f"{report_name}: expected 72 finite numeric values")
        if metrics["complete_ordering_identical"] is not True:
            errors.append(f"{report_name}: complete ordering changed")
        if metrics["certified_pair_directions"] != 66:
            errors.append(f"{report_name}: expected 66/66 pair directions")
        if metrics["means_inside_original_arb_intervals"] != 0:
            errors.append(f"{report_name}: expected 0/12 Arb interval memberships")
        if metrics["exact_translation_pass"] is not False:
            errors.append(f"{report_name}: exact translation must remain false")
        if metrics["ordering_robustness_pass"] is not True:
            errors.append(f"{report_name}: ordering robustness must pass")
        if report["scientific_status"] != EXPECTED_STATUS:
            errors.append(f"{report_name}: unexpected scientific status")

    if candidate["path_order"] != reference["path_order"]:
        errors.append("candidate path order differs from reference")

    reference_cells = keyed(reference["cell_results"], ("path", "error_label"))
    candidate_cells = keyed(candidate["cell_results"], ("path", "error_label"))
    if set(candidate_cells) != set(reference_cells):
        errors.append("candidate cell set differs from reference")

    reference_paths = keyed(reference["path_results"], ("path",))
    candidate_paths = keyed(candidate["path_results"], ("path",))
    if set(candidate_paths) != set(reference_paths):
        errors.append("candidate path set differs from reference")

    for key in sorted(set(candidate_paths) & set(reference_paths)):
        reference_membership = bool(
            reference_paths[key]["mean_inside_original_arb_interval"]
        )
        candidate_membership = bool(
            candidate_paths[key]["mean_inside_original_arb_interval"]
        )
        if reference_membership != candidate_membership:
            errors.append(f"{key[0]}: Arb interval membership changed")

    if candidate["pair_directions"] != reference["pair_directions"]:
        errors.append("candidate pair directions differ from reference")

    return errors


def audit_reports(
    reference: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    hard_gate_errors = validate_hard_gates(reference, candidate)
    loss_records: list[dict[str, Any]] = []
    mean_records: list[dict[str, Any]] = []

    reference_cells = keyed(reference.get("cell_results", []), ("path", "error_label"))
    candidate_cells = keyed(candidate.get("cell_results", []), ("path", "error_label"))
    for key in sorted(set(reference_cells) & set(candidate_cells)):
        path, error_label = key
        loss_records.append(
            numeric_record(
                kind="loss",
                label={"path": str(path), "error_label": str(error_label)},
                reference=float(reference_cells[key]["loss"]),
                candidate=float(candidate_cells[key]["loss"]),
                abs_tol=LOSS_ABS_TOL,
                rel_tol=LOSS_REL_TOL,
            )
        )

    reference_paths = keyed(reference.get("path_results", []), ("path",))
    candidate_paths = keyed(candidate.get("path_results", []), ("path",))
    for key in sorted(set(reference_paths) & set(candidate_paths)):
        path = key[0]
        mean_records.append(
            numeric_record(
                kind="mean",
                label={"path": str(path)},
                reference=float(reference_paths[key]["mean_loss"]),
                candidate=float(candidate_paths[key]["mean_loss"]),
                abs_tol=MEAN_ABS_TOL,
                rel_tol=MEAN_REL_TOL,
            )
        )

    loss_summary = summarize_records(loss_records)
    mean_summary = summarize_records(mean_records)
    passed = (
        not hard_gate_errors
        and loss_summary["exceeded_count"] == 0
        and mean_summary["exceeded_count"] == 0
    )
    return {
        "schema": "pulser_translation_comparison_summary",
        "schema_version": 1,
        "passed": passed,
        "hard_gate_errors": hard_gate_errors,
        "tolerances": {
            "loss_abs_tol": LOSS_ABS_TOL,
            "loss_rel_tol": LOSS_REL_TOL,
            "mean_abs_tol": MEAN_ABS_TOL,
            "mean_rel_tol": MEAN_REL_TOL,
        },
        "loss": loss_summary,
        "mean": mean_summary,
    }


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=False)
        handle.write("\n")


def format_label(record: dict[str, Any]) -> str:
    label = record["label"]
    if record["kind"] == "loss":
        return f"{label['path']} {label['error_label']}"
    return str(label["path"])


def print_numeric_summary(name: str, summary: dict[str, Any]) -> None:
    print(f"{name} compared: {summary['count']}")
    print(f"{name} exceedances: {summary['exceeded_count']}")
    max_abs = summary["max_absolute_difference"]
    max_rel = summary["max_relative_difference"]
    if max_abs is not None:
        print(
            f"{name} max absolute difference: "
            f"{max_abs['absolute_difference']:.17g} at {format_label(max_abs)}"
        )
    if max_rel is not None:
        print(
            f"{name} max relative difference: "
            f"{max_rel['relative_difference']:.17g} at {format_label(max_rel)}"
        )
    for row in summary["exceedances"]:
        print(
            f"{name} exceedance {format_label(row)}: "
            f"reference={row['reference']:.17g}, "
            f"candidate={row['candidate']:.17g}, "
            f"abs_diff={row['absolute_difference']:.17g}, "
            f"rel_diff={row['relative_difference']:.17g}, "
            f"allowed_abs_diff={row['allowed_absolute_difference']:.17g}, "
            f"abs_tol={row['absolute_tolerance']:.17g}, "
            f"rel_tol={row['relative_tolerance']:.17g}"
        )


def print_summary(summary: dict[str, Any]) -> None:
    print(f"hard gate errors: {len(summary['hard_gate_errors'])}")
    for error in summary["hard_gate_errors"]:
        print(f"hard gate error: {error}")
    print_numeric_summary("loss", summary["loss"])
    print_numeric_summary("mean", summary["mean"])
    if summary["passed"]:
        print("Pulser translation reports match within declared tolerances.")
    else:
        print("Pulser translation reports differ or hard gates failed.")
    tolerances = summary["tolerances"]
    print(
        "loss tolerance: "
        f"abs={tolerances['loss_abs_tol']:g}, rel={tolerances['loss_rel_tol']:g}"
    )
    print(
        "mean tolerance: "
        f"abs={tolerances['mean_abs_tol']:g}, rel={tolerances['mean_rel_tol']:g}"
    )


def compare_reports(
    reference: dict[str, Any],
    candidate: dict[str, Any],
    *,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    summary = audit_reports(reference, candidate)
    if summary_path is not None:
        write_summary(summary_path, summary)
    if not summary["passed"]:
        raise AssertionError("Pulser translation reports differ or hard gates failed.")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--summary", help="Optional JSON comparison summary output.")
    args = parser.parse_args(argv)
    reference = load_json(Path(args.reference))
    candidate = load_json(Path(args.candidate))
    summary = audit_reports(reference, candidate)
    if args.summary:
        write_summary(Path(args.summary), summary)
    print_summary(summary)
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
