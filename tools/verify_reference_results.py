#!/usr/bin/env python3
"""Validate the scientific gates in the bundled reference JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_report(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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

    return messages


def main() -> None:
    for message in verify():
        print(message)
    print("All bundled reference-artifact gates: PASS")


if __name__ == "__main__":
    main()
