#!/usr/bin/env python3
"""Verify and score v1.1.2 dissipative-susceptibility reveal reports.

The scoring functions in this module are intentionally independent of QuTiP.
PR checks exercise them only on synthetic fixtures; the real holdout workflow
calls the same functions after manual `workflow_dispatch` execution.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from tools.verify_dissipative_susceptibility_protocol import (
    EXPECTED_CANONICAL_SHA256,
    SOURCE_COMMIT,
    canonical_protocol_sha256,
    load_protocol,
)


MERGED_PROTOCOL_COMMIT = "03055196b5b58d022a5cfcea46b007cb752cea44"
EXPECTED_PROTOCOL_SHA256 = EXPECTED_CANONICAL_SHA256
PAIR_COUNT = 66
HOLDOUT_CONDITION_COUNT = 26
CLASSIFICATION_DENOMINATOR = PAIR_COUNT * HOLDOUT_CONDITION_COUNT
FAMILIES = ("decay", "dephasing", "joint")


def holdout_conditions(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    grid = protocol["holdout_grid"]
    single = [float(x) for x in grid["single_channel_holdout_lambdas"]]
    conditions = [
        {"family": "decay", "decay": lam, "dephasing": 0.0, "lambda": lam}
        for lam in single
    ]
    conditions += [
        {"family": "dephasing", "decay": 0.0, "dephasing": lam, "lambda": lam}
        for lam in single
    ]
    conditions += [
        {
            "family": "joint",
            "decay": float(row["decay"]),
            "dephasing": float(row["dephasing"]),
            "lambda": float(row["decay"]),
        }
        for row in grid["joint_holdout_lambdas"]
    ]
    assert len(conditions) == HOLDOUT_CONDITION_COUNT
    return conditions


def d_value(means: dict[str, float], better: str, worse: str) -> float:
    return float(means[worse]) - float(means[better])


def fit_slope_fixed_intercept(
    delta: float, observations: list[tuple[float, float]]
) -> float:
    numerator = sum(lam * (value - delta) for lam, value in observations)
    denominator = sum(lam * lam for lam, _ in observations)
    if denominator <= 0.0:
        raise ValueError("slope fit requires at least one positive lambda")
    return float(numerator / denominator)


def predicted_difference(
    delta: float,
    chi_decay: float,
    chi_dephasing: float,
    condition: dict[str, Any],
) -> float:
    family = condition["family"]
    if family == "decay":
        return float(delta + chi_decay * float(condition["decay"]))
    if family == "dephasing":
        return float(delta + chi_dephasing * float(condition["dephasing"]))
    if family == "joint":
        return float(
            delta
            + chi_decay * float(condition["decay"])
            + chi_dephasing * float(condition["dephasing"])
        )
    raise ValueError(f"unknown family {family!r}")


def predicted_scale(delta: float, chi_decay: float, chi_dephasing: float, family: str) -> float | None:
    if family == "decay":
        denom = -chi_decay
    elif family == "dephasing":
        denom = -chi_dephasing
    elif family == "joint":
        denom = -(chi_decay + chi_dephasing)
    else:
        raise ValueError(f"unknown family {family!r}")
    if denom <= 0.0:
        return None
    value = delta / denom
    if not math.isfinite(value) or value <= 0.0:
        return None
    return float(value)


def first_actual_flip(
    pair_observations: list[dict[str, Any]], family: str
) -> float | None:
    rows = sorted(
        [row for row in pair_observations if row["family"] == family],
        key=lambda row: (float(row["lambda"]), float(row["decay"]), float(row["dephasing"])),
    )
    for row in rows:
        if not bool(row["actual_preserved"]):
            return float(row["lambda"])
    return None


def family_c_index(items: list[dict[str, Any]]) -> dict[str, Any]:
    comparable = 0
    credit = 0.0
    for i, left in enumerate(items):
        for right in items[i + 1 :]:
            left_actual = left["actual_first_flip"]
            right_actual = right["actual_first_flip"]
            if left_actual is None and right_actual is None:
                continue
            if left_actual is not None and right_actual is not None:
                if float(left_actual) == float(right_actual):
                    continue
                left_earlier = float(left_actual) < float(right_actual)
            else:
                left_earlier = left_actual is not None
            comparable += 1
            left_score = (
                float(left["predicted_first_flip"])
                if left["predicted_first_flip"] is not None
                else math.inf
            )
            right_score = (
                float(right["predicted_first_flip"])
                if right["predicted_first_flip"] is not None
                else math.inf
            )
            if left_score == right_score:
                credit += 0.5
            elif (left_score < right_score) == left_earlier:
                credit += 1.0
    return {
        "comparable_count": comparable,
        "concordance_credit": credit,
        "c_index": None if comparable == 0 else credit / comparable,
    }


def factor_of_two_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [
        row
        for row in items
        if row["actual_first_flip"] is not None
        and row["predicted_first_flip"] is not None
    ]
    successes = [
        row
        for row in eligible
        if 0.5 * float(row["actual_first_flip"])
        <= float(row["predicted_first_flip"])
        <= 2.0 * float(row["actual_first_flip"])
    ]
    return {
        "eligible_count": len(eligible),
        "success_count": len(successes),
        "fraction": None if not eligible else len(successes) / len(eligible),
    }


def score_reveal_payload(
    *,
    protocol: dict[str, Any],
    pairs: list[dict[str, str]],
    training_means: dict[str, dict[str, float]],
    holdout_means: list[dict[str, Any]],
) -> dict[str, Any]:
    conditions = holdout_conditions(protocol)
    condition_keys = {
        (row["family"], float(row["decay"]), float(row["dephasing"]))
        for row in conditions
    }
    observed_keys = {
        (row["family"], float(row["decay"]), float(row["dephasing"]))
        for row in holdout_means
    }
    if condition_keys != observed_keys:
        raise AssertionError("holdout conditions do not match frozen protocol")

    unitary = training_means["unitary"]
    pair_predictions: list[dict[str, Any]] = []
    pair_condition_rows: list[dict[str, Any]] = []
    correct = 0
    finite_values = True
    lambda_zero_preserved = 0

    holdout_by_key = {
        (row["family"], float(row["decay"]), float(row["dephasing"])): row["means"]
        for row in holdout_means
    }

    for pair in pairs:
        better = pair["better"]
        worse = pair["worse"]
        delta = d_value(unitary, better, worse)
        if delta > 0:
            lambda_zero_preserved += 1
        decay_obs = [
            (0.0, d_value(training_means["unitary"], better, worse)),
            (0.0001, d_value(training_means["decay:0.0001"], better, worse)),
            (0.0003, d_value(training_means["decay:0.0003"], better, worse)),
        ]
        dephasing_obs = [
            (0.0, d_value(training_means["unitary"], better, worse)),
            (0.0001, d_value(training_means["dephasing:0.0001"], better, worse)),
            (0.0003, d_value(training_means["dephasing:0.0003"], better, worse)),
        ]
        chi_decay = fit_slope_fixed_intercept(delta, decay_obs)
        chi_dephasing = fit_slope_fixed_intercept(delta, dephasing_obs)
        family_items: dict[str, list[dict[str, Any]]] = {family: [] for family in FAMILIES}
        for condition in conditions:
            means = holdout_by_key[
                (condition["family"], float(condition["decay"]), float(condition["dephasing"]))
            ]
            actual_d = d_value(means, better, worse)
            predicted_d = predicted_difference(
                delta, chi_decay, chi_dephasing, condition
            )
            actual_preserved = actual_d > 0.0
            predicted_preserved = predicted_d > 0.0
            if actual_preserved == predicted_preserved:
                correct += 1
            if not math.isfinite(actual_d):
                finite_values = False
            row = {
                "pair": f"{better}>{worse}",
                "better": better,
                "worse": worse,
                **condition,
                "delta": delta,
                "chi_decay": chi_decay,
                "chi_dephasing": chi_dephasing,
                "actual_difference": actual_d,
                "predicted_difference": predicted_d,
                "actual_preserved": actual_preserved,
                "predicted_preserved": predicted_preserved,
            }
            pair_condition_rows.append(row)
            family_items[condition["family"]].append(row)
        for family in FAMILIES:
            actual = first_actual_flip(family_items[family], family)
            pred = predicted_scale(delta, chi_decay, chi_dephasing, family)
            pair_predictions.append({
                "pair": f"{better}>{worse}",
                "family": family,
                "delta": delta,
                "chi_decay": chi_decay,
                "chi_dephasing": chi_dephasing,
                "actual_first_flip": actual,
                "predicted_first_flip": pred,
                "prediction_label": (
                    "positive-crossing"
                    if pred is not None
                    else "no-crossing-on-positive-axis"
                ),
            })

    assert len(pair_condition_rows) == CLASSIFICATION_DENOMINATOR
    family_c = {
        family: family_c_index(
            [row for row in pair_predictions if row["family"] == family]
        )
        for family in FAMILIES
    }
    total_comparable = sum(row["comparable_count"] for row in family_c.values())
    total_credit = sum(row["concordance_credit"] for row in family_c.values())
    pooled_c = None if total_comparable == 0 else total_credit / total_comparable

    family_factor = {
        family: factor_of_two_summary(
            [row for row in pair_predictions if row["family"] == family]
        )
        for family in FAMILIES
    }
    total_eligible = sum(row["eligible_count"] for row in family_factor.values())
    total_success = sum(row["success_count"] for row in family_factor.values())
    pooled_factor = None if total_eligible == 0 else total_success / total_eligible

    accuracy = correct / CLASSIFICATION_DENOMINATOR
    gates = protocol["primary_gates"]
    gate_results = {
        "all_propagation_values_finite": finite_values,
        "lambda_zero_reconstructs_66_of_66": lambda_zero_preserved == PAIR_COUNT,
        "classification_accuracy": accuracy
        >= gates["holdout_pair_direction_classification_accuracy_at_least"],
        "harrell_c_index": pooled_c is not None
        and pooled_c >= gates["harrell_concordance_index_at_least"],
        "factor_of_two": pooled_factor is not None
        and pooled_factor
        >= gates[
            "factor_of_two_accuracy_for_actual_flips_with_positive_predictions_at_least"
        ],
    }
    failures = [name for name, passed in gate_results.items() if not passed]
    return {
        "protocol_sha256": canonical_protocol_sha256(protocol),
        "classification": {
            "correct": correct,
            "denominator": CLASSIFICATION_DENOMINATOR,
            "accuracy": accuracy,
        },
        "lambda_zero_preserved_pairs": lambda_zero_preserved,
        "family_c_index": family_c,
        "pooled_c_index": {
            "comparable_count": total_comparable,
            "concordance_credit": total_credit,
            "c_index": pooled_c,
        },
        "family_factor_of_two": family_factor,
        "pooled_factor_of_two": {
            "eligible_count": total_eligible,
            "success_count": total_success,
            "fraction": pooled_factor,
        },
        "gate_results": gate_results,
        "failures": failures,
        "all_gates_pass": not failures,
        "pair_predictions": pair_predictions,
        "pair_condition_rows": pair_condition_rows,
    }


def verify_report(report: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    assert report["schema"] == "dissipative_susceptibility_reveal_report"
    assert report["schema_version"] == "1.1.2"
    assert report["merged_protocol_commit"] == MERGED_PROTOCOL_COMMIT
    assert report["protocol_sha256"] == EXPECTED_PROTOCOL_SHA256
    assert report["protocol_sha256"] == canonical_protocol_sha256(report["protocol"])
    assert report["source_commit"] == SOURCE_COMMIT
    messages.append("protocol binding: PASS")

    classification = report["metrics"]["classification"]
    assert classification["denominator"] == CLASSIFICATION_DENOMINATOR
    assert 0 <= classification["correct"] <= CLASSIFICATION_DENOMINATOR
    assert math.isclose(
        classification["accuracy"],
        classification["correct"] / CLASSIFICATION_DENOMINATOR,
    )
    assert set(report["metrics"]["family_c_index"]) == set(FAMILIES)
    assert set(report["metrics"]["family_factor_of_two"]) == set(FAMILIES)
    messages.append("scoring denominators: PASS")

    assert len(report["metrics"]["pair_condition_rows"]) == CLASSIFICATION_DENOMINATOR
    assert len(report["metrics"]["pair_predictions"]) == PAIR_COUNT * len(FAMILIES)
    assert isinstance(report["metrics"]["failures"], list)
    messages.append("complete pair reporting: PASS")
    return messages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    for message in verify_report(report):
        print(message)
    print(f"all gates pass: {report['metrics']['all_gates_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
