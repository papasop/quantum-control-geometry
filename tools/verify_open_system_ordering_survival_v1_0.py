#!/usr/bin/env python3
"""Verify the committed open-system v1.0 protocol/summary and optional report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/external/open_system"
PROTOCOL = BASE / "pasqal_open_system_ordering_survival_v1_0_protocol.json"
SUMMARY = BASE / "pasqal_open_system_ordering_survival_v1_0_summary.json"
EXPECTED_PROTOCOL_SHA = "0ba13647e72a9215072ca70577d3e4d9f0ddf5c95f5796bee5b671e9a08ad888"


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_sha(obj: Any) -> str:
    payload = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def scientific_projection(report: dict[str, Any]) -> dict[str, Any]:
    conditions = []
    for row in report["condition_results"]:
        conditions.append(
            {
                key: row[key]
                for key in (
                    "family",
                    "decay",
                    "dephasing",
                    "spearman_rho",
                    "pair_directions_preserved",
                    "full_order_preserved",
                    "frozen_best_rank_zero_based",
                    "frozen_worst_rank_zero_based",
                )
            }
        )
    flipped = [
        row
        for row in report["pair_flip_summary"]
        if any(value is not None for value in row["first_observed_flip"].values())
    ]
    min_pair = next(
        row
        for row in report["pair_flip_summary"]
        if row["better"] == "pv08" and row["worse"] == "pv11"
    )
    first = next(row for row in report["condition_results"] if row["reversed_pairs"])
    return {
        "coverage": {
            "conditions": len(report["condition_results"]),
            "paths": len(report["frozen_order"]),
            "error_points": len(report["protocol"]["error_points"]),
            "planned_propagations": report["summary"]["planned_propagations"],
            "completed_propagations": report["summary"]["completed_propagations"],
            "all_finite": report["summary"]["all_finite"],
        },
        "unitary_reconstruction": report["summary"]["unitary_reconstruction"],
        "evaluation_gates": report["summary"]["evaluation_gates"],
        "all_empirical_evaluation_gates_pass": report["summary"][
            "all_empirical_evaluation_gates_pass"
        ],
        "minimum_certificate_margin": report["summary"][
            "minimum_certificate_margin"
        ],
        "minimum_margin_pair": report["summary"]["minimum_margin_pair"],
        "minimum_margin_pair_first_observed_flip": min_pair["first_observed_flip"],
        "pairs": {
            "total": 66,
            "flipped_at_least_once": len(flipped),
            "never_flipped_on_declared_grid": 66 - len(flipped),
        },
        "first_observed_reversal": {
            "family": first["family"],
            "integrated_decay": first["decay"],
            "integrated_dephasing": first["dephasing"],
            "reversed_pairs": first["reversed_pairs"],
        },
        "margin_flip_association_exploratory": report["summary"][
            "margin_flip_association"
        ],
        "condition_summary": conditions,
        "flipped_pair_thresholds": flipped,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    protocol = load(PROTOCOL)
    summary = load(SUMMARY)
    assert canonical_sha(protocol) == EXPECTED_PROTOCOL_SHA
    assert summary["protocol_sha256"] == EXPECTED_PROTOCOL_SHA
    assert summary["scientific_status"] == "OPEN_SYSTEM_STRESS_AUDIT_COMPLETE"
    assert summary["coverage"] == {
        "conditions": 29,
        "paths": 12,
        "error_points": 6,
        "planned_propagations": 2088,
        "completed_propagations": 2088,
        "all_finite": True,
    }
    assert summary["unitary_reconstruction"] == {
        "spearman_rho": 1.0,
        "pair_directions_preserved": 66,
        "full_order_preserved": True,
    }
    assert summary["pairs"] == {
        "total": 66,
        "flipped_at_least_once": 11,
        "never_flipped_on_declared_grid": 55,
    }
    assert summary["minimum_margin_pair"] == "pv08>pv11"
    assert all(
        value is None
        for value in summary["minimum_margin_pair_first_observed_flip"].values()
    )
    assert summary["all_empirical_evaluation_gates_pass"] is True
    assert summary["original_run_provenance"][
        "prospective_freeze_verified_by_expected_hash"
    ] is False

    if args.report is not None:
        report = load(args.report)
        assert report["protocol_sha256"] == EXPECTED_PROTOCOL_SHA
        assert canonical_sha(report["protocol"]) == EXPECTED_PROTOCOL_SHA
        projected = scientific_projection(report)
        for key, value in projected.items():
            assert summary[key] == value, f"report mismatch in {key}"
        print("generated report scientific projection: PASS")

    print("open-system v1.0 protocol and summary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
