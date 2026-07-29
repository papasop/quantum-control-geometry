#!/usr/bin/env python3
"""Validate the scientific gates and hashes in bundled reference artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def field(report: dict[str, Any], name: str) -> Any:
    if name in report:
        return report[name]
    gates = report.get("gates", {})
    if name in gates:
        return gates[name]
    raise KeyError(f"missing field {name!r}")


def assert_no_runtime_fields(value: Any) -> None:
    if isinstance(value, dict):
        forbidden = {"elapsed_seconds", "created_unix_time", "platform"}
        overlap = forbidden.intersection(value)
        assert not overlap, f"runtime fields inside hashed certificate: {overlap}"
        for child in value.values():
            assert_no_runtime_fields(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_runtime_fields(child)


def verify() -> list[str]:
    messages: list[str] = []

    g4 = load_json("results/g4_prospective/report.json")
    assert field(g4, "scientific_status") == (
        "PASQAL_TWO_ATOM_ZERO_POINT_G4_RANKING_SUPPORTED"
    )
    assert float(g4["validation"]["mean_spearman"]) >= 0.95
    assert bool(g4["validation"]["top1_pass"])
    messages.append("G4 prospective gates: PASS")

    l3 = load_json("results/l3_covariance/report.json")
    assert bool(l3["L3"]["supported"])
    assert all(bool(value) for value in l3["L3"]["gates"].values())
    assert float(l3["L3"]["direct_covariance_relative_error"]) < 1.0e-12
    assert float(l3["L3"]["maximum_contraction_relative_error"]) < 1.0e-12
    messages.append("L3 covariance gates: PASS")

    order30 = load_json("results/l4_order30/report.json")
    assert int(order30["order30_local_jet"]["certified_pairs"]) == 66
    assert bool(order30["order30_local_jet"]["all_certified_pairs_correct"])
    messages.append("L4 floating order-30 gates: PASS")

    formal_protocol = load_json("results/l4_formal/protocol.json")
    formal_certificate = load_json("results/l4_formal/formal_certificate.json")
    formal = load_json("results/l4_formal/report.json")
    assert sha256_json(formal_protocol) == formal["protocol_sha256"]
    assert sha256_json(formal_certificate) == formal[
        "formal_certificate_sha256"
    ]
    assert field(formal, "scientific_status") == (
        "L4_FORMAL_ARB_ORDER30_CERTIFICATE_SUPPORTED"
    )
    assert bool(formal["gates"]["formal_interval_arithmetic"])
    assert bool(formal["gates"]["formal_alias_bound"])
    assert bool(formal["gates"]["formal_order32_tail_bound"])
    assert int(field(formal, "order30_certified_pairs")) == 66
    assert float(field(formal, "order30_pair_coverage")) == 1.0
    assert bool(formal["gates"]["order30_certified_pairs_correct"])
    assert bool(formal["gates"]["ordinary_outcomes_inside_formal_intervals"])
    assert int(field(formal, "G4_certified_pairs")) == 34
    assert int(field(formal, "possible_pairs")) == 66
    assert float(field(formal, "G4_pair_coverage")) == 34 / 66
    messages.append("L4 formal Arb gates and hashes: PASS")

    cohort = load_json("results/exact_fibre_krawczyk/cohort.json")
    kraw_protocol = load_json(
        "results/exact_fibre_krawczyk/protocol.json"
    )
    kraw_certificate = load_json(
        "results/exact_fibre_krawczyk/krawczyk_certificate.json"
    )
    krawczyk = load_json("results/exact_fibre_krawczyk/report.json")
    assert sha256_json(cohort) == kraw_protocol["frozen_cohort_sha256"]
    assert sha256_json(cohort) == kraw_certificate["frozen_cohort_sha256"]
    assert sha256_json(kraw_protocol) == krawczyk["protocol_sha256"]
    assert sha256_json(kraw_protocol) == kraw_certificate["protocol_sha256"]
    assert sha256_json(kraw_certificate) == krawczyk[
        "krawczyk_certificate_sha256"
    ]
    assert field(krawczyk, "scientific_status") == (
        "L4_EXACT_RESPONSE_FIBRE_KRAWCZYK_SUPPORTED"
    )
    assert bool(krawczyk["formal_interval_arithmetic"])
    assert int(krawczyk["evaluated_paths"]) == 12
    assert len(kraw_certificate["paths"]) == 12
    assert all(
        bool(row["krawczyk_inclusion_pass"])
        and float(row["accepted_radius"]) == 3.0e-12
        for row in kraw_certificate["paths"]
    )
    assert bool(krawczyk["all_evaluated_krawczyk_inclusions_pass"])
    assert bool(krawczyk["full_declared_cohort"])
    assert_no_runtime_fields(kraw_certificate)
    messages.append("Exact-fibre reproducible Krawczyk gates and hashes: PASS")

    exact_protocol = load_json("results/exact_root_ordering/protocol.json")
    exact_certificate = load_json(
        "results/exact_root_ordering/exact_root_ordering_certificate.json"
    )
    exact_root = load_json("results/exact_root_ordering/report.json")
    assert sha256_json(exact_protocol) == exact_root["protocol_sha256"]
    assert sha256_json(exact_protocol) == exact_certificate["protocol_sha256"]
    assert sha256_json(exact_certificate) == exact_root[
        "exact_root_ordering_certificate_sha256"
    ]
    assert exact_protocol["krawczyk_certificate_sha256"] == sha256_json(
        kraw_certificate
    )
    assert exact_protocol["frozen_ordering_certificate_sha256"] == (
        sha256_json(formal_certificate)
    )
    assert field(exact_root, "scientific_status") == (
        "L4_EXACT_ROOT_DIRECT_FINITE_ERROR_ORDERING_SUPPORTED"
    )
    assert bool(exact_root["formal_interval_arithmetic"])
    assert int(exact_root["n_exact_root_boxes"]) == 12
    assert int(exact_root["direct_certified_pairs"]) == 66
    assert float(exact_root["direct_pair_coverage"]) == 1.0
    assert bool(exact_root["gates"]["direct_matches_frozen_order"])
    assert int(exact_root["order30_certified_pairs"]) == 52
    assert int(exact_root["order30_incorrect_certified_pairs"]) == 0
    assert bool(
        exact_root["gates"][
            "order30_all_certified_pairs_match_frozen_order"
        ]
    )
    assert_no_runtime_fields(exact_certificate)
    messages.append("Exact-root direct ordering gates and hashes: PASS")

    reproducibility = load_json("results/reproducibility_summary.json")
    assert reproducibility["scientific_status"] == (
        "L4_REPRODUCIBLE_CERTIFICATE_SUPPORTED"
    )
    assert bool(reproducibility["two_run_proof_files_byte_identical"])
    assert all(
        bool(value)
        for value in reproducibility["proof_file_comparisons"].values()
    )
    assert reproducibility["frozen_cohort_sha256"] == sha256_json(cohort)
    assert reproducibility["krawczyk_protocol_sha256"] == sha256_json(
        kraw_protocol
    )
    assert reproducibility["krawczyk_certificate_sha256"] == sha256_json(
        kraw_certificate
    )
    assert reproducibility["ordering_protocol_sha256"] == sha256_json(
        exact_protocol
    )
    assert reproducibility["ordering_certificate_sha256"] == sha256_json(
        exact_certificate
    )
    messages.append("Two-run deterministic certificate identity: PASS")

    return messages


def main() -> None:
    for message in verify():
        print(message)
    print("All bundled reference-artifact gates and hashes: PASS")


if __name__ == "__main__":
    main()
