#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASQAL two-atom L4 high-order local-jet remainder audit.

The script computes the symmetric mean-infidelity Taylor series at the exact
zero-error point through order 30 by block-matrix exponentials:

    E[I_gamma(t z)] = C2_gamma t^2 + G4_gamma t^4
                      + sum_{m=3}^{15} G_{2m,gamma} t^(2m)
                      + R32_gamma(t).

Two prospective certificates are frozen before held-out outcomes are read:

1. G4-only intervals:
      center = common_C2 + G4_gamma
      radius = |known orders 6..30| + analytic tail + numeric margin.

2. Order-30 local-jet intervals:
      center = sum of known orders 2..30
      radius = analytic tail + numeric margin.

The analytic tail uses the integrated Hamiltonian perturbation norm K:

    |R32| <= mean_axis sum_{even n>=32} (2 K_axis |t|)^n / n!.

This is a floating-point computer-assisted audit.  The Dyson tail is
analytic, but the coefficient arithmetic is not interval arithmetic; the
result must not be called a formal proof until outward-rounded interval or
arbitrary-precision certification is added.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

try:
    import pasqal_two_atom_matched_fibre_test as base
    import pasqal_two_atom_q2_prospective_ranking as engine
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Missing companion modules. Use the standalone Colab edition."
    ) from exc


VERSION = "1.0"
VALIDATION_SEED = 20260806
N_PATHS = 12
MAX_GENERATION_ATTEMPTS = 50
JET_ORDER = 30
TARGET_T = 1.0
AXIS_SCALES = np.array([0.06, 0.04, 0.05], dtype=float)
NUMERICAL_MARGIN = 1.0e-9
SPEARMAN_GATE = 0.95
G4_PAIR_COVERAGE_GATE = 0.10
HIGH_JET_PAIR_COVERAGE_GATE = 0.95
HELDOUT_RECONSTRUCTION_TOL = 2.0e-8
OUTDIR = Path("pasqal_L4_high_order_results")


def canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def initialize_engine() -> None:
    engine.VALIDATION_SEED = VALIDATION_SEED
    engine.N_VALIDATION_PATHS = N_PATHS
    engine.MAX_GENERATION_ATTEMPTS = MAX_GENERATION_ATTEMPTS
    engine.OUTCOMES_UNLOCKED = False
    engine.ERROR_AUDIT.start("constraints_and_order30_zero_point_jet")
    engine.REFERENCE_STATE, engine.REFERENCE_TANGENTS = (
        engine.local_state_and_tangents(engine.REFERENCE_PHASES)
    )
    vector = np.concatenate(
        [engine.REFERENCE_STATE, *engine.REFERENCE_TANGENTS]
    )
    engine.REFERENCE_FEATURE = np.r_[vector.real, vector.imag]


def directional_infidelity_jet(
    candidate: engine.Candidate,
    direction: np.ndarray,
) -> np.ndarray:
    dimension = len(base.GG)
    zero = np.zeros((dimension, dimension), dtype=complex)
    total = [np.eye(dimension, dtype=complex)] + [
        zero.copy() for _ in range(JET_ORDER)
    ]
    physical_direction = AXIS_SCALES * direction

    for phase in candidate.phases:
        h0 = base.segment_hamiltonian(phase, 0.0, 0.0, 0.0)
        h1 = (
            base.segment_hamiltonian(phase, *physical_direction) - h0
        )
        block_a = -1.0j * base.SEGMENT_DURATION_US * h0
        block_b = -1.0j * base.SEGMENT_DURATION_US * h1
        block = np.zeros(
            (
                dimension * (JET_ORDER + 1),
                dimension * (JET_ORDER + 1),
            ),
            dtype=complex,
        )
        for order in range(JET_ORDER + 1):
            start = dimension * order
            block[start:start+dimension, start:start+dimension] = block_a
        for order in range(JET_ORDER):
            row = dimension * order
            column = dimension * (order + 1)
            block[
                row:row+dimension,
                column:column+dimension,
            ] = block_b
        exponential = base.expm(block)
        segment = [
            exponential[
                :dimension,
                dimension*order:dimension*(order+1),
            ]
            for order in range(JET_ORDER + 1)
        ]
        updated = []
        for order in range(JET_ORDER + 1):
            coefficient = zero.copy()
            for split in range(order + 1):
                coefficient += segment[split] @ total[order-split]
            updated.append(coefficient)
        total = updated

    states = [coefficient @ base.GG for coefficient in total]
    target = states[0] / np.linalg.norm(states[0])
    amplitudes = [np.vdot(target, state) for state in states]
    fidelity = np.array(
        [
            sum(
                np.conj(amplitudes[left])
                * amplitudes[order-left]
                for left in range(order + 1)
            )
            for order in range(JET_ORDER + 1)
        ],
        dtype=complex,
    )
    infidelity = -fidelity
    infidelity[0] += 1.0
    return infidelity


def mean_symmetric_jet(candidate: engine.Candidate) -> dict:
    axis_jets = [
        directional_infidelity_jet(candidate, np.eye(3)[axis])
        for axis in range(3)
    ]
    mean_jet = np.mean(np.asarray(axis_jets), axis=0)
    even_coefficients = {
        str(order): float(mean_jet[order].real)
        for order in range(2, JET_ORDER + 1, 2)
    }
    maximum_odd = float(
        max(abs(mean_jet[order]) for order in range(1, JET_ORDER + 1, 2))
    )
    maximum_imaginary = float(np.max(np.abs(mean_jet.imag)))
    return {
        "path": candidate.name,
        "coefficients": even_coefficients,
        "C2": even_coefficients["2"],
        "G4": even_coefficients["4"],
        "known_higher_sum_6_to_30": float(
            sum(
                even_coefficients[str(order)]
                for order in range(6, JET_ORDER + 1, 2)
            )
        ),
        "order30_center": float(
            sum(even_coefficients.values())
        ),
        "maximum_odd_coefficient_residual": maximum_odd,
        "maximum_imaginary_coefficient_residual": maximum_imaginary,
    }


def perturbation_integrated_norms() -> np.ndarray:
    values = []
    for axis in range(3):
        total = 0.0
        for phase in engine.REFERENCE_PHASES:
            h0 = base.segment_hamiltonian(phase, 0.0, 0.0, 0.0)
            error = np.zeros(3)
            error[axis] = AXIS_SCALES[axis]
            h1 = base.segment_hamiltonian(phase, *error)
            total += (
                base.SEGMENT_DURATION_US
                * float(np.linalg.norm(h1 - h0, ord=2))
            )
        values.append(total)
    return np.asarray(values)


def even_tail_bound(K: float, first_order: int) -> float:
    x = 2.0 * K * abs(TARGET_T)
    total = 0.0
    order = first_order if first_order % 2 == 0 else first_order + 1
    term = x**order / math.factorial(order)
    while term > 1.0e-18 * max(1.0, total):
        total += term
        order += 2
        term *= x*x / (order * (order - 1))
        if order > 300:
            raise RuntimeError("Dyson tail series did not converge.")
    return float(total + term)


def certified_pairs(
    names: list[str],
    centers: dict[str, float],
    radii: dict[str, float],
) -> list[dict]:
    rows = []
    for left in range(len(names)):
        for right in range(left + 1, len(names)):
            first, second = names[left], names[right]
            if centers[first] <= centers[second]:
                better, worse = first, second
            else:
                better, worse = second, first
            if (
                centers[better] + radii[better]
                < centers[worse] - radii[worse]
            ):
                rows.append(
                    {
                        "better": better,
                        "worse": worse,
                        "certified_gap": (
                            centers[worse] - radii[worse]
                            - centers[better] - radii[better]
                        ),
                    }
                )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTDIR)
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"[notice] ignored notebook arguments: {unknown}")
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    protocol = {
        "title": "PASQAL L4 order-30 local-jet tail audit",
        "version": VERSION,
        "validation_seed": VALIDATION_SEED,
        "n_new_paths": N_PATHS,
        "jet_order": JET_ORDER,
        "target_t": TARGET_T,
        "axis_scales": AXIS_SCALES.tolist(),
        "numerical_margin": NUMERICAL_MARGIN,
        "G4_pair_coverage_gate": G4_PAIR_COVERAGE_GATE,
        "high_jet_pair_coverage_gate": HIGH_JET_PAIR_COVERAGE_GATE,
        "heldout_reconstruction_tolerance": (
            HELDOUT_RECONSTRUCTION_TOL
        ),
        "outcomes_used_before_certificate": False,
        "formal_interval_arithmetic": False,
        "claim_boundary": (
            "Analytic Dyson tail plus double-precision block-exponential "
            "coefficients and an explicit numerical margin. This is a "
            "floating-point computer-assisted certificate, not yet a "
            "formal outward-rounded interval proof."
        ),
    }
    protocol_hash = sha256_json(protocol)
    (output_dir / "protocol.json").write_text(
        json.dumps(protocol, indent=2), encoding="utf-8"
    )

    initialize_engine()
    _, _, null_basis, constraint_info = engine.constraint_geometry()
    candidates, attempts = engine.generate_validation_candidates(null_basis)
    jet_rows = [mean_symmetric_jet(candidate) for candidate in candidates]
    names = [candidate.name for candidate in candidates]
    row_by_name = {row["path"]: row for row in jet_rows}

    K_axes = perturbation_integrated_norms()
    axis_tail_bounds = [
        even_tail_bound(K, JET_ORDER + 2) for K in K_axes
    ]
    analytic_tail = float(np.mean(axis_tail_bounds))
    common_C2 = float(np.mean([row["C2"] for row in jet_rows]))
    C2_deviations = {
        name: abs(row_by_name[name]["C2"] - common_C2)
        for name in names
    }
    G4_centers = {
        name: common_C2 + row_by_name[name]["G4"]
        for name in names
    }
    G4_radii = {
        name: (
            C2_deviations[name]
            + abs(row_by_name[name]["known_higher_sum_6_to_30"])
            + analytic_tail
            + NUMERICAL_MARGIN
        )
        for name in names
    }
    high_centers = {
        name: row_by_name[name]["order30_center"] for name in names
    }
    high_radii = {
        name: analytic_tail + NUMERICAL_MARGIN for name in names
    }
    G4_pairs = certified_pairs(names, G4_centers, G4_radii)
    high_pairs = certified_pairs(names, high_centers, high_radii)
    possible_pairs = N_PATHS * (N_PATHS - 1) // 2
    G4_coverage = len(G4_pairs) / possible_pairs
    high_coverage = len(high_pairs) / possible_pairs
    predicted_G4_order = sorted(names, key=lambda name: G4_centers[name])
    predicted_high_order = sorted(
        names, key=lambda name: high_centers[name]
    )

    constraint_residuals = [
        float(np.linalg.norm(engine.matched_residual(candidate.phases)))
        for candidate in candidates
    ]
    pre_outcome_audit = engine.ERROR_AUDIT.summary()
    certificate = {
        "protocol_sha256": protocol_hash,
        "created_unix_time": time.time(),
        "outcomes_unlocked": False,
        "integrated_perturbation_norms_K": K_axes.tolist(),
        "axis_tail_bounds_after_order30": axis_tail_bounds,
        "mean_analytic_tail_bound": analytic_tail,
        "common_C2": common_C2,
        "jet_rows": jet_rows,
        "G4_intervals": {
            name: {
                "center": G4_centers[name],
                "radius": G4_radii[name],
            }
            for name in names
        },
        "order30_intervals": {
            name: {
                "center": high_centers[name],
                "radius": high_radii[name],
            }
            for name in names
        },
        "G4_certified_pairs": G4_pairs,
        "order30_certified_pairs": high_pairs,
        "predicted_G4_order": predicted_G4_order,
        "predicted_order30_order": predicted_high_order,
        "candidate_phases": {
            candidate.name: candidate.phases.tolist()
            for candidate in candidates
        },
        "pre_outcome_error_audit": pre_outcome_audit,
    }
    certificate_hash = sha256_json(certificate)
    certificate_path = output_dir / "L4_certificate.json"
    certificate_path.write_text(
        json.dumps(certificate, indent=2), encoding="utf-8"
    )
    with certificate_path.open("rb") as stream:
        os.fsync(stream.fileno())

    engine.OUTCOMES_UNLOCKED = True
    engine.ERROR_AUDIT.start("held_out_outcomes")
    performance = [
        engine.held_out_performance(candidate) for candidate in candidates
    ]
    held_out_audit = engine.ERROR_AUDIT.summary()
    actual = {
        row["path"]: row["mean_infidelity"] for row in performance
    }
    actual_order = sorted(names, key=lambda name: actual[name])
    G4_rho_result = spearmanr(
        [-row_by_name[name]["G4"] for name in names],
        [-actual[name] for name in names],
    )
    high_rho_result = spearmanr(
        [-high_centers[name] for name in names],
        [-actual[name] for name in names],
    )
    G4_pairs_correct = all(
        actual[row["better"]] < actual[row["worse"]]
        for row in G4_pairs
    )
    high_pairs_correct = all(
        actual[row["better"]] < actual[row["worse"]]
        for row in high_pairs
    )
    reconstruction_errors = {
        name: abs(high_centers[name] - actual[name])
        for name in names
    }
    max_reconstruction_error = max(reconstruction_errors.values())

    integrity_gates = {
        "certificate_before_outcomes": True,
        "all_constraints_pass": (
            max(constraint_residuals) <= engine.CONSTRAINT_RESIDUAL_TOL
        ),
        "analytic_tail_finite": math.isfinite(analytic_tail),
        "heldout_reconstruction_within_bound": all(
            reconstruction_errors[name] <= high_radii[name]
            for name in names
        ),
        "heldout_reconstruction_tolerance": (
            max_reconstruction_error <= HELDOUT_RECONSTRUCTION_TOL
        ),
    }
    G4_gates = {
        "prospective_spearman": (
            float(G4_rho_result.statistic) >= SPEARMAN_GATE
        ),
        "certified_pair_coverage": (
            G4_coverage >= G4_PAIR_COVERAGE_GATE
        ),
        "all_certified_pairs_correct": G4_pairs_correct,
    }
    high_gates = {
        "certified_pair_coverage": (
            high_coverage >= HIGH_JET_PAIR_COVERAGE_GATE
        ),
        "all_certified_pairs_correct": high_pairs_correct,
    }
    G4_partial_supported = (
        all(integrity_gates.values()) and all(G4_gates.values())
    )
    high_jet_supported = (
        all(integrity_gates.values()) and all(high_gates.values())
    )
    if high_jet_supported and G4_partial_supported:
        status = (
            "L4_ORDER30_BOUND_SUPPORTED_G4_PARTIAL_ORDER_CERTIFIED"
        )
    elif high_jet_supported:
        status = "L4_ORDER30_BOUND_SUPPORTED_G4_ONLY_INCONCLUSIVE"
    else:
        status = "L4_HIGH_ORDER_BOUND_NOT_SUPPORTED"

    report = {
        "scientific_status": status,
        "claim_boundary": protocol["claim_boundary"],
        "protocol_sha256": protocol_hash,
        "certificate_sha256": certificate_hash,
        "integrity_gates": integrity_gates,
        "G4_only": {
            "partially_supported": G4_partial_supported,
            "gates": G4_gates,
            "prospective_spearman": float(G4_rho_result.statistic),
            "prospective_spearman_pvalue": float(G4_rho_result.pvalue),
            "certified_pairs": len(G4_pairs),
            "possible_pairs": possible_pairs,
            "coverage": G4_coverage,
            "all_certified_pairs_correct": G4_pairs_correct,
        },
        "order30_local_jet": {
            "supported": high_jet_supported,
            "gates": high_gates,
            "prospective_spearman": float(high_rho_result.statistic),
            "prospective_spearman_pvalue": float(high_rho_result.pvalue),
            "certified_pairs": len(high_pairs),
            "possible_pairs": possible_pairs,
            "coverage": high_coverage,
            "all_certified_pairs_correct": high_pairs_correct,
            "maximum_heldout_reconstruction_error": (
                max_reconstruction_error
            ),
        },
        "jet_order": JET_ORDER,
        "analytic_tail_bound": analytic_tail,
        "axis_tail_bounds": axis_tail_bounds,
        "numerical_margin": NUMERICAL_MARGIN,
        "predicted_G4_order": predicted_G4_order,
        "predicted_order30_order": predicted_high_order,
        "actual_order": actual_order,
        "maximum_constraint_residual": max(constraint_residuals),
        "constraint_info": constraint_info,
        "generation_attempts": attempts,
        "pre_outcome_error_audit": pre_outcome_audit,
        "held_out_error_audit": held_out_audit,
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    print("=" * 112)
    print("PASQAL TWO-ATOM L4 ORDER-30 LOCAL-JET TAIL AUDIT")
    print("=" * 112)
    print(
        json.dumps(
            {
                "scientific_status": status,
                "n_new_paths": N_PATHS,
                "jet_order": JET_ORDER,
                "analytic_tail_bound_after_order30": analytic_tail,
                "numerical_margin": NUMERICAL_MARGIN,
                "maximum_heldout_reconstruction_error": (
                    max_reconstruction_error
                ),
                "G4_prospective_spearman": float(
                    G4_rho_result.statistic
                ),
                "G4_certified_pairs": len(G4_pairs),
                "G4_possible_pairs": possible_pairs,
                "G4_pair_coverage": G4_coverage,
                "G4_all_certified_pairs_correct": G4_pairs_correct,
                "order30_prospective_spearman": float(
                    high_rho_result.statistic
                ),
                "order30_certified_pairs": len(high_pairs),
                "order30_pair_coverage": high_coverage,
                "order30_all_certified_pairs_correct": (
                    high_pairs_correct
                ),
                "formal_interval_arithmetic": False,
                "protocol_sha256": protocol_hash,
                "certificate_sha256": certificate_hash,
                "output_directory": str(output_dir),
            },
            indent=2,
        )
    )
    print("\nInterpretation")
    if G4_partial_supported:
        print(
            "  G4 PARTIAL L4 PASS: the quartic term alone, with every "
            "known higher-order contribution placed inside its error band, "
            "certifies the predeclared fraction of path pairs."
        )
    else:
        print(
            "  G4-only remainder intervals do not reach the predeclared "
            "pair-coverage gate."
        )
    if high_jet_supported:
        print(
            "  ORDER-30 L4 PASS: zero-point derivatives through order 30 "
            "plus the analytic tail bound certify finite-error ordering."
        )
        print(
            "  This is a floating-point certificate, not yet a formal "
            "outward-rounded interval proof."
        )
    else:
        print(
            "  The order-30 local-jet certificate did not close L4."
        )


if __name__ == "__main__":
    main()
