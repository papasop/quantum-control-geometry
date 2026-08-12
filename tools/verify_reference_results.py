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


def verify_g4_threshold_claim(g4: dict[str, Any]) -> None:
    assert g4["claim_level"] == "threshold"
    threshold = float(g4["predeclared_mean_spearman_minimum"])
    assert threshold == 0.95
    assert bool(g4["reference_environment_sample"])
    assert not bool(g4["cross_architecture_exact_value_invariant"])
    assert not bool(g4["cross_architecture_top_path_invariant"])
    assert float(g4["validation"]["mean_spearman"]) >= threshold
    assert bool(g4["gates"]["primary_spearman_gate"])
    for sample in g4.get("cross_architecture_observations", {}).get(
        "samples", []
    ):
        assert float(sample["mean_spearman"]) >= threshold
        assert bool(sample["primary_spearman_gate_pass"])


def verify() -> list[str]:
    messages: list[str] = []

    g4 = load_json("results/g4_prospective/report.json")
    g4_provenance = load_json("results/g4_prospective/provenance.json")
    assert field(g4, "scientific_status") == (
        "PASQAL_TWO_ATOM_ZERO_POINT_G4_RANKING_SUPPORTED"
    )
    verify_g4_threshold_claim(g4)
    assert bool(g4["validation"]["top1_pass"])
    assert g4_provenance["legacy_manuscript_sample_status"] == (
        "legacy manuscript sample corrected in v1.2.1 textual revision"
    )
    original_colab = g4_provenance["original_colab_sample"]
    assert float(original_colab["mean_spearman"]) == 0.996992
    assert not bool(original_colab["cross_platform_reproducible"])
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
    p0 = load_json("results/audit_closure/p0_preconditioner_certificate.json")
    p0_frozen_inverse = load_json(
        "tests/audit_closure/data/p0_frozen_inverse_hex.json"
    )
    cohort_path = ROOT / "results/exact_fibre_krawczyk/cohort.json"
    p0_inverse_path = ROOT / "tests/audit_closure/data/p0_frozen_inverse_hex.json"
    preconditioner_payload = [
        {
            "path": row["path"],
            "point_preconditioner_decimal": row[
                "point_preconditioner_decimal"
            ],
        }
        for row in cohort["paths"]
    ]
    expected_paths = [f"pv{index:02d}" for index in range(1, 13)]

    assert p0_frozen_inverse["schema"] == "p0_frozen_inverse_hex"
    assert int(p0_frozen_inverse["schema_version"]) == 1
    assert p0_frozen_inverse["source_cohort_sha256"] == hashlib.sha256(
        cohort_path.read_bytes()
    ).hexdigest()
    assert p0_frozen_inverse[
        "production_preconditioner_payload_sha256"
    ] == sha256_json(preconditioner_payload)
    assert p0_frozen_inverse["matrix_shape"] == [16, 16]
    assert p0_frozen_inverse["paths"] == expected_paths
    assert set(p0_frozen_inverse["matrices"]) == set(expected_paths)
    for path in expected_paths:
        matrix = p0_frozen_inverse["matrices"][path]
        assert len(matrix) == 16
        assert all(len(row) == 16 for row in matrix)
        for row in matrix:
            for value in row:
                assert float.fromhex(value).hex() == value

    assert p0["schema"] == "p0_preconditioner_certificate"
    assert int(p0["schema_version"]) == 2
    assert p0["method"] == "Rump-Neumann regularity certificate"
    assert p0["production_preconditioner_conversion"] == (
        "arb(repr(float(decimal)))"
    )
    assert p0["source_cohort_sha256"] == hashlib.sha256(
        cohort_path.read_bytes()
    ).hexdigest()
    assert p0["production_preconditioner_payload_sha256"] == sha256_json(
        preconditioner_payload
    )
    assert p0["frozen_inverse_data_sha256"] == hashlib.sha256(
        p0_inverse_path.read_bytes()
    ).hexdigest()
    assert p0["frozen_inverse_schema"] == "p0_frozen_inverse_hex@1"
    assert p0["matrix_shape"] == [16, 16]
    assert p0["paths"] == expected_paths
    assert int(p0["prec_bits"]) == 256
    assert bool(p0["all_nonsingular"])
    assert len(p0["results"]) == 12
    assert [row["path"] for row in p0["results"]] == expected_paths
    assert all(
        bool(row["nonsingular"])
        and 0.0 <= float(row["rho_upper"]) < 1.0
        and float(row["inverse_error_bound_upper"]) >= 0.0
        for row in p0["results"]
    )
    messages.append("P0 production-preconditioner regularity: PASS")
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

    reveal = load_json(
        "results/external/open_system/"
        "dissipative_susceptibility_reveal_v1_1_2_summary.json"
    )
    assert reveal["schema"] == "dissipative_susceptibility_reveal_summary"
    assert reveal["schema_version"] == "1.1.2"
    assert reveal["scientific_status"] == (
        "PROSPECTIVE_DISSIPATIVE_SUSCEPTIBILITY_SUPPORTED"
    )
    assert reveal["workflow_run"]["conclusion"] == "success"
    assert reveal["protocol"]["canonical_sha256"] == (
        "0c220213ba9485fd06268c56b726848c33b684da10c9d715c96690e9e7ae8476"
    )
    assert int(reveal["protocol"]["holdout_conditions"]) == 26
    assert int(reveal["protocol"]["pair_condition_denominator"]) == 1716
    assert int(reveal["execution"]["propagations"]) == 2232
    assert bool(reveal["execution"]["all_values_finite"])
    reveal_results = reveal["results"]
    assert reveal_results["lambda_zero_preserved_pairs"] == "66/66"
    assert int(reveal_results["classification"]["correct"]) == 1715
    assert int(reveal_results["classification"]["denominator"]) == 1716
    assert bool(reveal_results["classification"]["passed"])
    assert int(reveal_results["pooled_harrell_c_index"]["comparable_count"]) == 1217
    assert float(reveal_results["pooled_harrell_c_index"]["value"]) == 1.0
    assert bool(reveal_results["pooled_harrell_c_index"]["passed"])
    assert int(reveal_results["pooled_factor_of_two"]["success_count"]) == 19
    assert int(reveal_results["pooled_factor_of_two"]["eligible_count"]) == 20
    assert bool(reveal_results["pooled_factor_of_two"]["passed"])
    assert bool(reveal_results["all_gates_pass"])
    assert reveal_results["failures"] == []
    assert reveal["full_report"]["sha256"] == (
        "73ca097b726e152035f20097c4e98acff01de26772abeb22370fd4bba863a65b"
    )
    messages.append("Dissipative-susceptibility reveal summary gates: PASS")

    return messages


def main() -> None:
    for message in verify():
        print(message)
    print("All bundled reference-artifact gates and hashes: PASS")


if __name__ == "__main__":
    main()
