#!/usr/bin/env python3
"""Validate the scientific gates in the bundled reference JSON artifacts."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_report(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def file_sha256(relative: str) -> str:
    path = ROOT / relative
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(report: dict[str, Any], name: str) -> Any:
    if name in report:
        return report[name]
    gates = report.get("gates", {})
    if name in gates:
        return gates[name]
    raise KeyError(f"missing field {name!r}")


def verify() -> list[str]:
    messages: list[str] = []

    g4 = load_report("results/g4_prospective/report.json")
    assert field(g4, "scientific_status") == (
        "PASQAL_TWO_ATOM_ZERO_POINT_G4_RANKING_SUPPORTED"
    )
    assert float(g4["validation"]["mean_spearman"]) >= 0.95
    assert bool(g4["validation"]["top1_pass"])
    messages.append("G4 prospective gates: PASS")

    l3 = load_report("results/l3_covariance/report.json")
    assert bool(l3["L3"]["supported"])
    assert all(bool(value) for value in l3["L3"]["gates"].values())
    assert float(l3["L3"]["direct_covariance_relative_error"]) < 1.0e-12
    assert float(l3["L3"]["maximum_contraction_relative_error"]) < 1.0e-12
    messages.append("L3 covariance gates: PASS")

    order30 = load_report("results/l4_order30/report.json")
    assert int(order30["order30_local_jet"]["certified_pairs"]) == 66
    assert bool(order30["order30_local_jet"]["all_certified_pairs_correct"])
    messages.append("L4 floating order-30 gates: PASS")

    formal = load_report("results/l4_formal/report.json")
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
    assert int(field(formal, "G4_certified_pairs")) < 66
    messages.append("L4 formal Arb gates: PASS")

    krawczyk = load_report("results/exact_fibre_krawczyk/report.json")
    assert field(krawczyk, "scientific_status") == (
        "L4_EXACT_RESPONSE_FIBRE_KRAWCZYK_SUPPORTED"
    )
    assert bool(krawczyk["formal_interval_arithmetic"])
    assert int(krawczyk["evaluated_paths"]) == 12
    assert int(krawczyk["declared_paths"]) == 12
    assert len(krawczyk["paths"]) == 12
    assert bool(krawczyk["all_evaluated_krawczyk_inclusions_pass"])
    assert bool(krawczyk["full_declared_cohort"])
    assert krawczyk["krawczyk_certificate_sha256"] == file_sha256(
        "results/exact_fibre_krawczyk/krawczyk_certificate.json"
    )
    assert krawczyk["protocol_sha256"] == file_sha256(
        "results/exact_fibre_krawczyk/protocol.json"
    )
    messages.append("Exact-fibre Krawczyk gates: PASS")

    exact_root = load_report("results/exact_root_ordering/report.json")
    assert field(exact_root, "scientific_status") == (
        "L4_EXACT_ROOT_DIRECT_FINITE_ERROR_ORDERING_SUPPORTED"
    )
    assert bool(exact_root["formal_interval_arithmetic"])
    assert int(exact_root["n_exact_root_boxes"]) == 12
    assert int(exact_root["direct_certified_pairs"]) == 66
    assert float(exact_root["direct_pair_coverage"]) == 1.0
    assert bool(field(exact_root, "direct_matches_frozen_order"))
    assert int(exact_root["order30_certified_pairs"]) == 52
    assert int(exact_root["order30_incorrect_certified_pairs"]) == 0
    assert bool(
        field(exact_root, "order30_all_certified_pairs_match_frozen_order")
    )
    assert exact_root["exact_root_ordering_certificate_sha256"] == file_sha256(
        "results/exact_root_ordering/exact_root_ordering_certificate.json"
    )
    assert exact_root["protocol_sha256"] == file_sha256(
        "results/exact_root_ordering/protocol.json"
    )
    messages.append("Exact-root direct ordering gates: PASS")

    return messages


def main() -> None:
    for message in verify():
        print(message)
    print("All bundled reference-artifact gates: PASS")


if __name__ == "__main__":
    main()
