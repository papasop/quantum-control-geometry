#!/usr/bin/env python3
"""Verify the committed blind-Pulser result summary and claim boundary."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


EXPECTED_STATUS = "BLIND_PULSER_RESPONSE_FIBRE_PREDICTION_SUPPORTED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary",
        default="results/external/pasqal_blind_response_fibre_v1_0_summary.json",
    )
    args = parser.parse_args()
    report = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    metrics = report["metrics"]
    gates = report["gates"]
    assert report["source_outcomes_unlocked"] is False
    assert report["scientific_status"] == EXPECTED_STATUS
    assert metrics["propagations"] == 120
    assert math.isclose(metrics["spearman_prediction_vs_pulser"], 0.998496)
    assert metrics["one_sided_permutation_p"] < 0.05
    assert metrics["best_vs_worst_bootstrap_ci95"][0] > 0.0
    assert len(report["predicted_order_best_to_worst"]) == 20
    assert len(report["observed_order_best_to_worst"]) == 20
    assert all(gates.values())
    scope = report["scope"].lower()
    assert "not arb proof" in scope
    assert "qpu" in scope
    print(EXPECTED_STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

