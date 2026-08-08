#!/usr/bin/env python3
"""Verify the compact v1.1.2 prospective reveal summary."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = ROOT / "results/external/open_system/dissipative_susceptibility_reveal_v1_1_2_summary.json"
EXPECTED_PROTOCOL_SHA256 = "0c220213ba9485fd06268c56b726848c33b684da10c9d715c96690e9e7ae8476"
EXPECTED_REPORT_SHA256 = "73ca097b726e152035f20097c4e98acff01de26772abeb22370fd4bba863a65b"


def verify(summary: dict) -> list[str]:
    assert summary["schema"] == "dissipative_susceptibility_reveal_summary"
    assert summary["schema_version"] == "1.1.2"
    assert summary["scientific_status"] == "PROSPECTIVE_DISSIPATIVE_SUSCEPTIBILITY_SUPPORTED"
    assert summary["protocol"]["canonical_sha256"] == EXPECTED_PROTOCOL_SHA256
    assert summary["protocol"]["pair_condition_denominator"] == 1716
    assert summary["execution"]["propagations"] == 2232
    assert summary["execution"]["all_values_finite"] is True

    results = summary["results"]
    classification = results["classification"]
    assert classification["correct"] == 1715
    assert classification["denominator"] == 1716
    assert math.isclose(classification["accuracy"], 1715 / 1716)
    assert classification["accuracy"] >= classification["gate"]

    c_index = results["pooled_harrell_c_index"]
    assert c_index["comparable_count"] == 1217
    assert c_index["value"] == 1.0
    assert c_index["value"] >= c_index["gate"]

    factor = results["pooled_factor_of_two"]
    assert factor["success_count"] == 19
    assert factor["eligible_count"] == 20
    assert math.isclose(factor["fraction"], 19 / 20)
    assert factor["fraction"] >= factor["gate"]
    assert results["all_gates_pass"] is True
    assert results["failures"] == []
    assert summary["full_report"]["sha256"] == EXPECTED_REPORT_SHA256
    return [
        "protocol and provenance: PASS",
        "classification result: PASS",
        "concordance result: PASS",
        "factor-of-two result: PASS",
        "claim boundary: PASS",
    ]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--full-report", type=Path)
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    for message in verify(summary):
        print(message)
    if args.full_report is not None:
        actual = sha256_file(args.full_report)
        if actual != EXPECTED_REPORT_SHA256:
            raise AssertionError(f"full report SHA-256 mismatch: {actual}")
        print("full report SHA-256: PASS")
    print("all frozen prospective reveal gates: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
