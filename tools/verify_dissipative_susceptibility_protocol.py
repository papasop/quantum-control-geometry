#!/usr/bin/env python3
"""Verify the frozen v1.1 dissipative-susceptibility prediction protocol."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = (
    ROOT
    / "results/external/open_system_v1_1/"
    / "dissipative_susceptibility_protocol.json"
)

EXPECTED_CANONICAL_SHA256 = (
    "d749b48c9153a32c4a7baec79400d092dcba71b459acacccaa300b7e40afe7a5"
)
SOURCE_COMMIT = "2fb0c4a3e339bfb899ef3963bc92ea1fc6a74d45"
SOURCE_ASSET_SHA256 = (
    "cb5c5b6e0634f98c306c8d13d39e94da263d7f1808d67cd13ab7113603691453"
)
V1_0_TRAINING_POINTS = {0.0, 1.0e-4, 3.0e-4}


def load_protocol() -> dict[str, Any]:
    with PROTOCOL_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_protocol_sha256(protocol: dict[str, Any]) -> str:
    clone = dict(protocol)
    clone.pop("canonical_protocol_sha256", None)
    payload = json.dumps(
        clone, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify() -> list[str]:
    protocol = load_protocol()
    messages: list[str] = []

    assert protocol["schema"] == (
        "differential_dissipative_susceptibility_prediction_protocol"
    )
    assert protocol["schema_version"] == "1.1"
    assert protocol["source_release"] == "v0.5.0"
    assert protocol["source_commit"] == SOURCE_COMMIT
    assert (
        protocol["source_assets"]["open_system_v1_0_zip_sha256"]
        == SOURCE_ASSET_SHA256
    )
    assert (
        protocol["source_assets"]["open_system_v1_0_canonical_protocol_sha256"]
        == "0ba13647e72a9215072ca70577d3e4d9f0ddf5c95f5796bee5b671e9a08ad888"
    )
    messages.append("source release and asset hashes: PASS")

    assert protocol["status"] == {
        "protocol_only": True,
        "holdout_computed": False,
        "outcomes_unlocked": False,
        "results_file_expected_in_this_pr": False,
    }
    assert protocol["training_data_policy"]["no_holdout_access_before_freeze"] is True
    assert protocol["training_data_policy"]["single_channel_training_lambdas"] == [
        0.0,
        0.0001,
        0.0003,
    ]
    messages.append("protocol-only freeze flags: PASS")

    holdout = protocol["holdout_grid"]
    single = holdout["single_channel_holdout_lambdas"]
    joint = holdout["joint_holdout_lambdas"]
    assert single == [
        0.0005,
        0.00075,
        0.0015,
        0.002,
        0.004,
        0.006,
        0.008,
        0.015,
        0.02,
        0.025,
    ]
    assert joint == [
        {"decay": 0.0005, "dephasing": 0.0005},
        {"decay": 0.0015, "dephasing": 0.0015},
        {"decay": 0.002, "dephasing": 0.002},
        {"decay": 0.006, "dephasing": 0.006},
        {"decay": 0.015, "dephasing": 0.015},
        {"decay": 0.025, "dephasing": 0.025},
    ]
    assert not (set(single) & V1_0_TRAINING_POINTS)
    assert all(row["decay"] == row["dephasing"] for row in joint)
    assert not ({row["decay"] for row in joint} & V1_0_TRAINING_POINTS)
    messages.append("holdout grid excludes v1.0 training points: PASS")

    gates = protocol["primary_gates"]
    assert gates["all_propagation_values_finite"] is True
    assert gates["lambda_zero_reconstructs_pair_directions"] == "66/66"
    assert gates["holdout_pair_direction_classification_accuracy_at_least"] == 0.90
    assert gates["harrell_concordance_index_at_least"] == 0.75
    assert (
        gates["factor_of_two_accuracy_for_actual_flips_with_positive_predictions_at_least"]
        == 0.70
    )
    assert gates["report_all_failures"] is True
    assert gates["no_success_pair_selection"] is True
    assert gates["diagnostic_pairs_decide_pass_fail"] is False
    messages.append("primary falsification gates: PASS")

    text = json.dumps(protocol, sort_keys=True)
    forbidden_result_keys = (
        "holdout_results",
        "observed_holdout",
        "actual_holdout",
        "pass_fail_result",
        "scientific_status",
    )
    for key in forbidden_result_keys:
        assert key not in text
    assert protocol["solver_environment"]["solver_options"] == {
        "method": "adams",
        "atol": 1.0e-11,
        "rtol": 1.0e-11,
        "nsteps": 100000,
        "max_step": 0.005,
        "progress_bar": "",
    }
    messages.append("no holdout result payload: PASS")

    digest = canonical_protocol_sha256(protocol)
    assert digest == EXPECTED_CANONICAL_SHA256
    assert protocol["canonical_protocol_sha256"] == EXPECTED_CANONICAL_SHA256
    messages.append(f"canonical protocol SHA-256: {digest}")

    return messages


def main() -> int:
    for message in verify():
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
