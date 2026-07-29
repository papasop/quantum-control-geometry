#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Formal finite-error ordering on Krawczyk-certified exact matched controls.

This audit tests two logically distinct chains.

Primary finite-radius theorem:

    unique exact state-and-first-response matched root
    + direct outward-rounded propagation of its phase box
    -> finite-error path ordering.

Secondary mechanism certificate:

    exact matched-root phase box
    + order-30 zero-error jet and analytic tail
    -> a local-jet explanation/certificate for some or all ordered pairs.

Inputs
------
1. The Krawczyk certificate emitted by
   pasqal_L4_exact_fibre_krawczyk_standalone_colab_v1_2.py.
2. The earlier pre-outcome formal order-30 certificate.  Its 66 oriented
   pairs are treated as the frozen predicted ordering.

For every path the program reconstructs the phase enclosure

    phi = phi_center + N [-r,r]^16

from the Krawczyk centre, transverse basis, and accepted radius.  It then
computes two independent outward-rounded enclosures:

* a 64-point Cauchy extraction of the zero-error jet through order 30,
  enlarged by the analytic order-32 tail;
* direct Arb propagation at the six declared finite-error points.

The primary PASS requires:
* a valid 12-path Krawczyk certificate;
* path identity agreement with the frozen ordering certificate;
* 66/66 disjoint direct finite-error phase-box intervals;
* the direct interval ordering equals the frozen pre-outcome ordering.

The order-30 result is reported separately.  Its alias, tail, coverage,
orientation, and direct-overlap checks do not veto the primary theorem:
direct interval propagation already encloses the exact root at the declared
finite-error points without a Taylor truncation.

This remains conditional on the declared finite-dimensional Hamiltonian.
It is not PASQAL hardware evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

try:
    from flint import acb, acb_mat, arb, ctx
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "python-flint==0.8.0 is required. Use the standalone Colab edition, "
        "which installs it automatically."
    ) from exc

try:
    import pasqal_two_atom_matched_fibre_test as base
    import pasqal_two_atom_q2_prospective_ranking as engine
    import pasqal_L4_arb_formal_audit as previous_formal
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Missing companion modules. Use the standalone Colab edition."
    ) from exc


VERSION = "1.3"
ARB_PRECISION_BITS = 192
JET_ORDER = 30
CAUCHY_POINTS = 64
ALIAS_ENCLOSURE = "1e-40"
TAIL_ENCLOSURE = "2e-11"
N_PATHS = 12
POSSIBLE_PAIRS = N_PATHS * (N_PATHS - 1) // 2
MAX_COHORT_PHASE_MISMATCH = 1.0e-5

DEFAULT_KRAWCZYK_CERTIFICATE = Path(
    "pasqal_L4_exact_fibre_krawczyk_v1_3_results/"
    "krawczyk_certificate.json"
)
DEFAULT_ORDERING_CERTIFICATE = Path(
    "pasqal_L4_arb_formal_results/formal_certificate.json"
)
OUTDIR = Path("pasqal_L4_exact_root_ordering_v1_3_results")


def canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Required certificate not found: {path}. "
            "Run the preceding audit in the same Colab runtime or pass the "
            "correct path explicitly."
        )
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def A(value: int | float | str) -> arb:
    return arb(str(value))


def C(value: complex | int | float) -> acb:
    value = complex(value)
    return acb(A(repr(value.real)), A(repr(value.imag)))


def zero_acb_ball(radius: str) -> acb:
    interval = arb(f"0 +/- {radius}")
    return acb(interval, interval)


def zero_arb_ball(radius: str | Any) -> arb:
    return arb(0, radius)


def pair_key(better: str, worse: str) -> tuple[str, str]:
    return better, worse


def wrapped_phase_distance(first: np.ndarray, second: np.ndarray) -> float:
    return float(
        np.max(
            np.abs(
                np.angle(np.exp(1.0j * (first - second)))
            )
        )
    )


def validate_certificates(
    krawczyk: dict[str, Any],
    ordering: dict[str, Any],
) -> tuple[list[str], dict[str, float], set[tuple[str, str]]]:
    kraw_rows = krawczyk.get("paths", [])
    if len(kraw_rows) != N_PATHS:
        raise RuntimeError(
            f"Krawczyk certificate has {len(kraw_rows)}/{N_PATHS} paths."
        )
    if not all(
        bool(row.get("krawczyk_inclusion_pass"))
        and row.get("accepted_radius") is not None
        for row in kraw_rows
    ):
        raise RuntimeError(
            "The Krawczyk certificate does not contain 12 strict inclusions."
        )

    centers = krawczyk.get("candidate_phases_decimal", {})
    bases = krawczyk.get("transverse_bases_decimal", {})
    names = [str(row["path"]) for row in kraw_rows]
    if set(centers) != set(names) or set(bases) != set(names):
        raise RuntimeError(
            "Krawczyk phase centres/bases do not match its path rows."
        )
    for name in names:
        center = np.asarray(centers[name], dtype=float)
        basis = np.asarray(bases[name], dtype=float)
        if center.shape != (base.N_SEGMENTS,):
            raise RuntimeError(f"{name}: expected 24 phase-centre values.")
        if basis.shape != (base.N_SEGMENTS, 16):
            raise RuntimeError(f"{name}: expected a 24x16 transverse basis.")

    old_centers = ordering.get("candidate_phases_decimal")
    if old_centers is None:
        old_centers = ordering.get("candidate_phases")
    if old_centers is None or set(old_centers) != set(names):
        raise RuntimeError(
            "Frozen ordering certificate does not contain the same path names."
        )
    mismatches = {
        name: wrapped_phase_distance(
            np.asarray(centers[name], dtype=float),
            np.asarray(old_centers[name], dtype=float),
        )
        for name in names
    }
    if max(mismatches.values()) > MAX_COHORT_PHASE_MISMATCH:
        raise RuntimeError(
            "Krawczyk and frozen-order cohorts differ by more than the "
            f"declared {MAX_COHORT_PHASE_MISMATCH:.1e} phase tolerance."
        )

    frozen_rows = ordering.get("order30_certified_pairs", [])
    frozen_pairs = {
        pair_key(str(row["better"]), str(row["worse"]))
        for row in frozen_rows
    }
    if len(frozen_pairs) != POSSIBLE_PAIRS:
        raise RuntimeError(
            "Frozen ordering certificate does not certify all 66 pairs."
        )
    return names, mismatches, frozen_pairs


def phase_boxes(
    name: str,
    krawczyk: dict[str, Any],
) -> list[arb]:
    centers = krawczyk["candidate_phases_decimal"][name]
    basis = krawczyk["transverse_bases_decimal"][name]
    row = next(item for item in krawczyk["paths"] if item["path"] == name)
    radius = A(repr(float(row["accepted_radius"])))
    coordinates = [arb(0, radius) for _ in range(16)]
    phases = []
    for phase_index in range(base.N_SEGMENTS):
        value = A(str(centers[phase_index]))
        for coordinate in range(16):
            value += A(str(basis[phase_index][coordinate])) * coordinates[
                coordinate
            ]
        phases.append(value)
    return phases


def hamiltonian_pair(
    phase: arb,
    axis: int,
) -> tuple[acb_mat, acb_mat]:
    dimension = 4
    pi = arb.pi()
    omega = 2 * pi
    interaction = 4 * omega
    cosine, sine = phase.cos(), phase.sin()
    h0 = acb_mat(dimension, dimension)
    h1 = acb_mat(dimension, dimension)
    amplitude_scale = A(3) / A(50)
    detuning_scale = A(1) / A(25)
    interaction_scale = A(1) / A(20)

    for row in range(dimension):
        for column in range(dimension):
            drive_axis = (
                cosine * C(previous_formal.GX[row][column])
                + sine * C(previous_formal.GY[row][column])
            )
            h0[row, column] = omega * drive_axis / 2
            h0[row, column] += (
                interaction * C(previous_formal.DOUBLE[row][column])
            )
            if axis == 0:
                h1[row, column] = (
                    omega * amplitude_scale * drive_axis / 2
                )
            elif axis == 1:
                h1[row, column] = (
                    -omega
                    * detuning_scale
                    * C(previous_formal.TOTAL_NUMBER[row][column])
                )
            else:
                h1[row, column] = (
                    interaction
                    * interaction_scale
                    * C(previous_formal.DOUBLE[row][column])
                )
    return h0, h1


def propagate(
    hamiltonians: list[tuple[acb_mat, acb_mat]],
    parameter: acb,
) -> acb_mat:
    tau = A(1) / A(10)
    minus_i_tau = -acb(0, 1) * tau
    state = acb_mat([[1], [0], [0], [0]])
    for h0, h1 in hamiltonians:
        state = (minus_i_tau * (h0 + parameter * h1)).exp() * state
    return state


def reference_target() -> acb_mat:
    phases = [A(repr(float(value))) for value in engine.REFERENCE_PHASES]
    hamiltonians = [hamiltonian_pair(phase, 0) for phase in phases]
    return propagate(hamiltonians, acb(0))


def amplitude_coefficients(
    phases: list[arb],
    axis: int,
    target: acb_mat,
) -> list[acb]:
    hamiltonians = [hamiltonian_pair(phase, axis) for phase in phases]
    target_bra = target.conjugate().transpose()
    roots: list[acb] = []
    samples: list[acb] = []
    pi = arb.pi()
    for index in range(CAUCHY_POINTS):
        angle = 2 * pi * index / CAUCHY_POINTS
        root = acb(angle.cos(), angle.sin())
        roots.append(root)
        samples.append((target_bra * propagate(hamiltonians, root))[0, 0])

    alias = zero_acb_ball(ALIAS_ENCLOSURE)
    coefficients = []
    for order in range(JET_ORDER + 1):
        coefficient = acb(0)
        for root, sample in zip(roots, samples):
            coefficient += sample * root ** (-order)
        coefficient /= CAUCHY_POINTS
        coefficients.append(coefficient + alias)
    return coefficients


def infidelity_coefficients(amplitude: list[acb]) -> list[arb]:
    values = []
    for order in range(JET_ORDER + 1):
        fidelity = acb(0)
        for left in range(order + 1):
            fidelity += (
                amplitude[left].conjugate()
                * amplitude[order - left]
            )
        infidelity = -fidelity
        if order == 0:
            infidelity += 1
        if not infidelity.imag.contains(0):
            raise RuntimeError(
                f"Infidelity coefficient {order} excludes a real value."
            )
        values.append(infidelity.real)
    return values


def order30_interval(
    phases: list[arb],
    target: acb_mat,
) -> tuple[arb, dict[int, arb]]:
    axes = [
        infidelity_coefficients(
            amplitude_coefficients(phases, axis, target)
        )
        for axis in range(3)
    ]
    even = {
        order: sum(axes[axis][order] for axis in range(3)) / 3
        for order in range(0, JET_ORDER + 1, 2)
    }
    centre = sum(even.values())
    return centre + zero_arb_ball(TAIL_ENCLOSURE), even


def direct_mean_interval(
    phases: list[arb],
    target: acb_mat,
) -> tuple[arb, list[arb]]:
    target_bra = target.conjugate().transpose()
    losses = []
    for axis in range(3):
        hamiltonians = [hamiltonian_pair(phase, axis) for phase in phases]
        for sign in (-1, 1):
            state = propagate(hamiltonians, acb(sign))
            amplitude = (target_bra * state)[0, 0]
            loss = 1 - amplitude.conjugate() * amplitude
            if not loss.imag.contains(0):
                raise RuntimeError(
                    "Direct finite-error infidelity excludes a real value."
                )
            losses.append(loss.real)
    return sum(losses) / 6, losses


def certify_pairs(intervals: dict[str, arb]) -> set[tuple[str, str]]:
    names = list(intervals)
    result: set[tuple[str, str]] = set()
    for left in range(len(names)):
        for right in range(left + 1, len(names)):
            first, second = names[left], names[right]
            if intervals[first].upper() < intervals[second].lower():
                result.add(pair_key(first, second))
            elif intervals[second].upper() < intervals[first].lower():
                result.add(pair_key(second, first))
    return result


def ball_record(value: arb) -> dict[str, str]:
    return {
        "ball": str(value),
        "lower": str(value.lower()),
        "upper": str(value.upper()),
    }


def intervals_overlap(first: arb, second: arb) -> bool:
    return not (
        first.upper() < second.lower()
        or second.upper() < first.lower()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--krawczyk-certificate",
        type=Path,
        default=DEFAULT_KRAWCZYK_CERTIFICATE,
    )
    parser.add_argument(
        "--ordering-certificate",
        type=Path,
        default=DEFAULT_ORDERING_CERTIFICATE,
    )
    parser.add_argument("--output-dir", type=Path, default=OUTDIR)
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Validate both certificates and cohort identity, then stop.",
    )
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"[notice] ignored notebook arguments: {unknown}")

    ctx.prec = ARB_PRECISION_BITS
    ctx.threads = 1
    args.output_dir.mkdir(parents=True, exist_ok=True)

    krawczyk = load_json(args.krawczyk_certificate)
    ordering = load_json(args.ordering_certificate)
    names, cohort_mismatches, frozen_pairs = validate_certificates(
        krawczyk, ordering
    )

    if args.preflight_only:
        print("=" * 116)
        print("PASQAL L4 EXACT-ROOT ORDERING CERTIFICATE PREFLIGHT")
        print("=" * 116)
        print(json.dumps({
            "status": "PREFLIGHT_PASS",
            "krawczyk_paths": len(names),
            "strict_krawczyk_inclusions": sum(
                bool(row["krawczyk_inclusion_pass"])
                for row in krawczyk["paths"]
            ),
            "frozen_ordered_pairs": len(frozen_pairs),
            "maximum_cohort_phase_mismatch": max(
                cohort_mismatches.values()
            ),
            "phase_mismatch_gate": MAX_COHORT_PHASE_MISMATCH,
        }, indent=2))
        print(
            "\nPreflight only: no phase-box performance propagation "
            "was performed."
        )
        return

    protocol = {
        "title": (
            "Exact-root direct finite-error ordering theorem with "
            "secondary order-30 jet audit"
        ),
        "version": VERSION,
        "arb_precision_bits": ARB_PRECISION_BITS,
        "jet_order": JET_ORDER,
        "cauchy_points": CAUCHY_POINTS,
        "alias_enclosure": ALIAS_ENCLOSURE,
        "tail_enclosure": TAIL_ENCLOSURE,
        "proof_engine": "python-flint",
        "proof_engine_version_required": "0.8.0",
        "n_paths": N_PATHS,
        "possible_pairs": POSSIBLE_PAIRS,
        "krawczyk_protocol_sha256": krawczyk.get("protocol_sha256"),
        "krawczyk_certificate_sha256": sha256_json(krawczyk),
        "frozen_ordering_protocol_sha256": ordering.get("protocol_sha256"),
        "frozen_ordering_certificate_sha256": sha256_json(ordering),
        "finite_error_outcomes_used_to_choose_order": False,
        "formal_interval_arithmetic": True,
    }
    protocol_hash = sha256_json(protocol)
    (args.output_dir / "protocol.json").write_text(
        json.dumps(protocol, indent=2), encoding="utf-8"
    )

    dyson = previous_formal.rigorous_dyson_checks()
    if not dyson["alias_pass"]:
        print(
            "[warning] formal Cauchy alias gate failed; the secondary "
            "order-30 mechanism certificate will be inconclusive.",
            flush=True,
        )
    if not dyson["tail_pass"]:
        print(
            "[warning] formal order-32 tail gate failed; the secondary "
            "order-30 mechanism certificate will be inconclusive.",
            flush=True,
        )

    print(
        "[arb] propagating 12 certified phase boxes through the order-30 "
        "jet and six direct finite-error points...",
        flush=True,
    )
    target = reference_target()
    order30_intervals: dict[str, arb] = {}
    direct_intervals: dict[str, arb] = {}
    path_rows = []
    runtime_rows = []

    for index, name in enumerate(names, start=1):
        print(f"[arb] path {index}/{N_PATHS}: {name}", flush=True)
        start = time.perf_counter()
        phases = phase_boxes(name, krawczyk)
        order30, coefficients = order30_interval(phases, target)
        direct, cells = direct_mean_interval(phases, target)
        order30_intervals[name] = order30
        direct_intervals[name] = direct
        path_rows.append({
            "path": name,
            "accepted_krawczyk_radius": next(
                row["accepted_radius"]
                for row in krawczyk["paths"]
                if row["path"] == name
            ),
            "order30_interval": ball_record(order30),
            "direct_mean_interval": ball_record(direct),
            "order30_direct_overlap": intervals_overlap(order30, direct),
            "even_coefficient_intervals": {
                str(order): ball_record(value)
                for order, value in coefficients.items()
            },
            "direct_cell_intervals": [
                ball_record(value) for value in cells
            ],
        })
        runtime_rows.append({
            "path": name,
            "elapsed_seconds": time.perf_counter() - start,
        })

    order30_pairs = certify_pairs(order30_intervals)
    direct_pairs = certify_pairs(direct_intervals)
    overlap_pass = all(
        row["order30_direct_overlap"] for row in path_rows
    )
    order30_correct_pairs = order30_pairs & frozen_pairs
    order30_incorrect_pairs = order30_pairs - frozen_pairs
    gates = {
        "valid_full_krawczyk_certificate": True,
        "cohort_identity_match": (
            max(cohort_mismatches.values())
            <= MAX_COHORT_PHASE_MISMATCH
        ),
        "formal_alias_bound": bool(dyson["alias_pass"]),
        "formal_order32_tail_bound": bool(dyson["tail_pass"]),
        "order30_pair_coverage": len(order30_pairs) == POSSIBLE_PAIRS,
        "direct_pair_coverage": len(direct_pairs) == POSSIBLE_PAIRS,
        "order30_all_certified_pairs_match_frozen_order": (
            order30_pairs <= frozen_pairs
        ),
        "order30_full_order_matches_frozen_order": (
            order30_pairs == frozen_pairs
        ),
        "direct_matches_frozen_order": direct_pairs == frozen_pairs,
        "order30_direct_interval_overlap": overlap_pass,
    }
    primary_gate_names = (
        "valid_full_krawczyk_certificate",
        "cohort_identity_match",
        "direct_pair_coverage",
        "direct_matches_frozen_order",
    )
    primary_supported = all(gates[name] for name in primary_gate_names)
    order30_full_supported = all((
        gates["formal_alias_bound"],
        gates["formal_order32_tail_bound"],
        gates["order30_pair_coverage"],
        gates["order30_full_order_matches_frozen_order"],
        gates["order30_direct_interval_overlap"],
    ))
    order30_partial_supported = all((
        gates["formal_alias_bound"],
        gates["formal_order32_tail_bound"],
        bool(order30_pairs),
        gates["order30_all_certified_pairs_match_frozen_order"],
        gates["order30_direct_interval_overlap"],
    ))
    status = (
        "L4_EXACT_ROOT_DIRECT_FINITE_ERROR_ORDERING_SUPPORTED"
        if primary_supported
        else "EXACT_ROOT_DIRECT_ORDERING_CERTIFICATE_INCONCLUSIVE"
    )
    order30_status = (
        "ORDER30_FULL_ORDER_SUPPORTED"
        if order30_full_supported
        else (
            "ORDER30_PARTIAL_ORDER_SUPPORTED"
            if order30_partial_supported
            else "ORDER30_MECHANISM_INCONCLUSIVE"
        )
    )

    certificate = {
        "protocol_sha256": protocol_hash,
        "formal_interval_arithmetic": True,
        "dyson_checks": {
            "alias_pass": dyson["alias_pass"],
            "tail_pass": dyson["tail_pass"],
            "alias_upper_bounds": [
                str(value) for value in dyson["alias_upper_bounds"]
            ],
            "axis_tails": [
                str(value) for value in dyson["axis_tails"]
            ],
            "mean_tail": str(dyson["mean_tail"]),
        },
        "cohort_phase_mismatches": cohort_mismatches,
        "path_rows": path_rows,
        "order30_certified_pairs": [
            {"better": better, "worse": worse}
            for better, worse in sorted(order30_pairs)
        ],
        "direct_certified_pairs": [
            {"better": better, "worse": worse}
            for better, worse in sorted(direct_pairs)
        ],
        "frozen_pairs": [
            {"better": better, "worse": worse}
            for better, worse in sorted(frozen_pairs)
        ],
        "primary_gate_names": list(primary_gate_names),
        "primary_supported": primary_supported,
        "order30_status": order30_status,
        "order30_correct_certified_pairs": [
            {"better": better, "worse": worse}
            for better, worse in sorted(order30_correct_pairs)
        ],
        "order30_incorrect_certified_pairs": [
            {"better": better, "worse": worse}
            for better, worse in sorted(order30_incorrect_pairs)
        ],
        "gates": gates,
    }
    certificate_hash = sha256_json(certificate)
    (args.output_dir / "exact_root_ordering_certificate.json").write_text(
        json.dumps(certificate, indent=2), encoding="utf-8"
    )
    report = {
        "scientific_status": status,
        "claim_boundary": (
            "Formal for exact roots enclosed by the supplied Krawczyk "
            "phase boxes in the serialized finite-dimensional model. "
            "Not hardware, model-discrepancy, or many-body evidence."
        ),
        "protocol_sha256": protocol_hash,
        "exact_root_ordering_certificate_sha256": certificate_hash,
        "formal_interval_arithmetic": True,
        "arb_precision_bits": ARB_PRECISION_BITS,
        "n_exact_root_boxes": len(names),
        "order30_certified_pairs": len(order30_pairs),
        "order30_correct_certified_pairs": len(order30_correct_pairs),
        "order30_incorrect_certified_pairs": len(order30_incorrect_pairs),
        "order30_pair_coverage": len(order30_pairs) / POSSIBLE_PAIRS,
        "order30_status": order30_status,
        "direct_certified_pairs": len(direct_pairs),
        "direct_pair_coverage": len(direct_pairs) / POSSIBLE_PAIRS,
        "possible_pairs": POSSIBLE_PAIRS,
        "primary_supported": primary_supported,
        "primary_gate_names": list(primary_gate_names),
        "maximum_cohort_phase_mismatch": max(
            cohort_mismatches.values()
        ),
        "gates": gates,
    }
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    run_metadata = {
        "certificate_sha256": certificate_hash,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": package_version("numpy"),
        "python_flint": package_version("python-flint"),
        "path_runtime_diagnostics": runtime_rows,
    }
    (args.output_dir / "run_metadata.json").write_text(
        json.dumps(run_metadata, indent=2), encoding="utf-8"
    )

    print("=" * 116)
    print("PASQAL L4 EXACT-ROOT DIRECT ORDERING + ORDER-30 MECHANISM AUDIT")
    print("=" * 116)
    print(json.dumps({
        "scientific_status": status,
        "formal_interval_arithmetic": True,
        "arb_precision_bits": ARB_PRECISION_BITS,
        "n_exact_root_boxes": len(names),
        "order30_certified_pairs": len(order30_pairs),
        "order30_correct_certified_pairs": len(order30_correct_pairs),
        "order30_incorrect_certified_pairs": len(order30_incorrect_pairs),
        "order30_pair_coverage": len(order30_pairs) / POSSIBLE_PAIRS,
        "order30_status": order30_status,
        "direct_certified_pairs": len(direct_pairs),
        "direct_pair_coverage": len(direct_pairs) / POSSIBLE_PAIRS,
        "possible_pairs": POSSIBLE_PAIRS,
        "order30_all_certified_pairs_match_frozen_order": gates[
            "order30_all_certified_pairs_match_frozen_order"
        ],
        "order30_full_order_matches_frozen_order": gates[
            "order30_full_order_matches_frozen_order"
        ],
        "direct_matches_frozen_order": gates[
            "direct_matches_frozen_order"
        ],
        "order30_direct_interval_overlap": overlap_pass,
        "protocol_sha256": protocol_hash,
        "exact_root_ordering_certificate_sha256": certificate_hash,
        "output_directory": str(args.output_dir),
    }, indent=2))
    print("\nInterpretation")
    if primary_supported:
        print(
            "  PRIMARY L4 PASS: unique exact response-matched roots lie "
            "inside the Krawczyk boxes, and direct outward-rounded Arb "
            "finite-error propagation certifies the frozen 66/66 order."
        )
    else:
        print(
            "  PRIMARY INCONCLUSIVE: the exact-root direct finite-error "
            "ordering theorem did not pass every primary gate."
        )
    if order30_full_supported:
        print(
            "  ORDER-30 FULL PASS: the local jet plus analytic tail also "
            "certifies the complete frozen order."
        )
    elif order30_partial_supported:
        print(
            "  ORDER-30 PARTIAL PASS: every pair certified by the local "
            "jet agrees with the frozen order, but interval widening leaves "
            f"{POSSIBLE_PAIRS - len(order30_pairs)} pairs unresolved."
        )
    else:
        print(
            "  ORDER-30 INCONCLUSIVE: do not use the local-jet calculation "
            "as an ordering certificate."
        )
    print(
        "  The primary result is a theorem for the serialized model, not "
        "PASQAL hardware or model discrepancy."
    )


if __name__ == "__main__":
    main()
