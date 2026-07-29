#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASQAL two-atom L3+L4 audit: covariant quartic tensor and remainder bound.

L3
--
Recover the full symmetric quartic response tensor A4 from

    S_gamma(t, v) = [I_gamma(+t D v) + I_gamma(-t D v)] / 2
                  = q2(v)t^2 + q4(v)t^4 + q6(v)t^6 + ...

where D=diag(0.06, 0.04, 0.05) maps normalized error coordinates to the
physical amplitude, detuning, and interaction errors. Taylor coefficients
through order six are computed directly at t=0 using block-matrix
exponentials, rather than inferred from a nonzero-radius polynomial fit.
A4 is defined by

    q4(v) = A4_ijkl v_i v_j v_k v_l.

The script verifies, both algebraically and by a direct refit, that under
z = R y,

    A4_y = R^{tensor 4} A4_z,
    M4_y = R^{-tensor 4} M4_z,
    A4_z : M4_z = A4_y : M4_y.

L4
--
For the six-axis symmetric noise law, evaluate

    E[I_gamma(t z)] = C2 t^2 + G4_gamma t^4 + R6_gamma(t).

A path-independent analytic Dyson bound is derived from the integrated
spectral norms K_k of the three Hamiltonian perturbations:

    |R6_gamma(t)| <= mean_k sum_{m>=3} (2 K_k |t|)^(2m)/(2m)!.

The bound is rigorous for the finite-dimensional piecewise Hamiltonian model
but may be conservative.  A pairwise ordering is theorem-certified only when
the quartic prediction intervals do not overlap.  If the bound certifies no
pairs, the script reports L4_BOUND_INCONCLUSIVE rather than claiming a
theorem.

This is local SciPy emulator evidence, not PASQAL Cloud or QPU evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import time
from pathlib import Path
from typing import Iterable

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
VALIDATION_SEED = 20260803
TENSOR_DIRECTION_SEED = 20260804
COORDINATE_SEED = 20260805
N_PATHS = 12
MAX_GENERATION_ATTEMPTS = 50
N_TENSOR_DIRECTIONS = 36
JET_ORDER = 6
TARGET_T = 1.0
AXIS_SCALES = np.array([0.06, 0.04, 0.05], dtype=float)
AXIS_NAMES = ("amplitude", "detuning", "interaction")
SPEARMAN_GATE = 0.95
TENSOR_FIT_RESIDUAL_TOL = 2.0e-3
DIRECT_COVARIANCE_RELATIVE_TOL = 5.0e-3
CONTRACTION_RELATIVE_TOL = 5.0e-10
G2_RELATIVE_SPREAD_TOL = 2.0e-5
JET_IMAGINARY_RESIDUAL_TOL = 1.0e-10
OUTDIR = Path("pasqal_two_atom_L3_L4_results")


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
    engine.ERROR_AUDIT.start("constraints_and_local_tensor")
    engine.REFERENCE_STATE, engine.REFERENCE_TANGENTS = (
        engine.local_state_and_tangents(engine.REFERENCE_PHASES)
    )
    vector = np.concatenate(
        [engine.REFERENCE_STATE, *engine.REFERENCE_TANGENTS]
    )
    engine.REFERENCE_FEATURE = np.r_[vector.real, vector.imag]


def degree_multiindices(degree: int) -> list[tuple[int, int, int]]:
    return [
        (a, b, degree - a - b)
        for a in range(degree + 1)
        for b in range(degree + 1 - a)
    ]


MULTI4 = degree_multiindices(4)


def monomial_row(
    vector: np.ndarray,
    multiindices: Iterable[tuple[int, int, int]],
) -> np.ndarray:
    return np.array(
        [
            float(np.prod(vector ** np.asarray(alpha)))
            for alpha in multiindices
        ]
    )


def direction_design() -> np.ndarray:
    rng = np.random.default_rng(TENSOR_DIRECTION_SEED)
    rows = [np.eye(3)[index] for index in range(3)]
    while len(rows) < N_TENSOR_DIRECTIONS:
        vector = rng.normal(size=3)
        vector /= np.linalg.norm(vector)
        rows.append(vector)
    directions = np.asarray(rows)
    design = np.vstack(
        [monomial_row(vector, MULTI4) for vector in directions]
    )
    if np.linalg.matrix_rank(design) != len(MULTI4):
        raise RuntimeError("Quartic directional design is rank deficient.")
    return directions


def directional_even_coefficients(
    candidate: engine.Candidate,
    direction: np.ndarray,
) -> tuple[float, float, float, float]:
    """Return exact zero-point series coefficients via block exponentials.

    For one segment exp(A+tB), block (0,n) of the exponential of the
    upper-bidiagonal block matrix with A on its diagonal and B on its first
    superdiagonal is the coefficient of t**n. Segment series are multiplied
    and truncated at JET_ORDER.
    """
    dimension = len(base.GG)
    identity = np.eye(dimension, dtype=complex)
    zero = np.zeros((dimension, dimension), dtype=complex)
    total = [identity] + [zero.copy() for _ in range(JET_ORDER)]
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
                0:dimension,
                dimension*order:dimension*(order+1),
            ]
            for order in range(JET_ORDER + 1)
        ]
        updated = []
        for order in range(JET_ORDER + 1):
            coefficient = zero.copy()
            for split in range(order + 1):
                coefficient += segment[split] @ total[order - split]
            updated.append(coefficient)
        total = updated

    state_coefficients = [
        coefficient @ base.GG for coefficient in total
    ]
    target = state_coefficients[0] / np.linalg.norm(
        state_coefficients[0]
    )
    amplitude = [
        np.vdot(target, coefficient)
        for coefficient in state_coefficients
    ]
    fidelity = [
        sum(
            np.conj(amplitude[left]) * amplitude[order-left]
            for left in range(order + 1)
        )
        for order in range(JET_ORDER + 1)
    ]
    infidelity = np.array(
        [1.0 - fidelity[0], *[-value for value in fidelity[1:]]],
        dtype=complex,
    )
    imaginary_residual = float(np.max(np.abs(infidelity.imag)))
    return (
        float(infidelity[2].real),
        float(infidelity[4].real),
        float(infidelity[6].real),
        imaginary_residual,
    )


def polynomial_to_symmetric_tensor(
    coefficients: np.ndarray,
) -> np.ndarray:
    tensor = np.zeros((3, 3, 3, 3), dtype=float)
    for alpha, coefficient in zip(MULTI4, coefficients):
        indices = (
            [0] * alpha[0] + [1] * alpha[1] + [2] * alpha[2]
        )
        permutations = sorted(set(itertools.permutations(indices)))
        value = float(coefficient) / len(permutations)
        for permutation in permutations:
            tensor[permutation] = value
    return tensor


def recover_tensor(
    candidate: engine.Candidate,
    directions: np.ndarray,
) -> dict:
    directional = [
        directional_even_coefficients(candidate, direction)
        for direction in directions
    ]
    q2 = np.array([row[0] for row in directional])
    q4 = np.array([row[1] for row in directional])
    q6 = np.array([row[2] for row in directional])
    design4 = np.vstack(
        [monomial_row(direction, MULTI4) for direction in directions]
    )
    coefficients4 = np.linalg.lstsq(design4, q4, rcond=None)[0]
    fitted4 = design4 @ coefficients4
    relative_residual = float(
        np.linalg.norm(q4 - fitted4)
        / max(np.linalg.norm(q4), 1.0e-30)
    )
    tensor4 = polynomial_to_symmetric_tensor(coefficients4)
    return {
        "path": candidate.name,
        "A4": tensor4,
        "quartic_polynomial_coefficients": coefficients4,
        "tensor_fit_relative_residual": relative_residual,
        "maximum_directional_jet_imaginary_residual": float(
            max(row[3] for row in directional)
        ),
        "mean_q2_on_design": float(np.mean(q2)),
        "mean_q6_on_design": float(np.mean(q6)),
    }


def noise_fourth_moment() -> np.ndarray:
    moment = np.zeros((3, 3, 3, 3), dtype=float)
    for axis in range(3):
        moment[axis, axis, axis, axis] = 1.0 / 3.0
    return moment


def contract4(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.einsum("ijkl,ijkl->", first, second))


def coordinate_map() -> np.ndarray:
    rng = np.random.default_rng(COORDINATE_SEED)
    left, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    right, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    return left @ np.diag([0.55, 0.75, 1.0]) @ right


def transform_A4(A4: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    return np.einsum(
        "ijkl,ia,jb,kc,ld->abcd",
        A4, matrix, matrix, matrix, matrix,
    )


def transform_M4(
    M4: np.ndarray,
    inverse: np.ndarray,
) -> np.ndarray:
    return np.einsum(
        "ijkl,ai,bj,ck,dl->abcd",
        M4, inverse, inverse, inverse, inverse,
    )


def direct_refit_in_y(
    candidate: engine.Candidate,
    y_directions: np.ndarray,
    matrix: np.ndarray,
) -> np.ndarray:
    q4 = np.array(
        [
            directional_even_coefficients(
                candidate, matrix @ direction
            )[1]
            for direction in y_directions
        ]
    )
    design = np.vstack(
        [monomial_row(direction, MULTI4) for direction in y_directions]
    )
    coefficients = np.linalg.lstsq(design, q4, rcond=None)[0]
    return polynomial_to_symmetric_tensor(coefficients)


def axis_G2(candidate: engine.Candidate) -> float:
    return float(
        np.mean(
            [
                directional_even_coefficients(
                    candidate, np.eye(3)[axis]
                )[0]
                for axis in range(3)
            ]
        )
    )


def perturbation_integrated_norms() -> np.ndarray:
    values = []
    for axis in range(3):
        total = 0.0
        for phase in engine.REFERENCE_PHASES:
            zero = base.segment_hamiltonian(phase, 0.0, 0.0, 0.0)
            error = np.zeros(3)
            error[axis] = AXIS_SCALES[axis]
            shifted = base.segment_hamiltonian(phase, *error)
            total += (
                base.SEGMENT_DURATION_US
                * float(np.linalg.norm(shifted - zero, ord=2))
            )
        values.append(total)
    return np.asarray(values)


def even_dyson_tail(K: float, target_t: float) -> float:
    value = 2.0 * K * abs(target_t)
    return float(
        math.cosh(value)
        - 1.0
        - value**2 / math.factorial(2)
        - value**4 / math.factorial(4)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTDIR)
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"[notice] ignored notebook arguments: {unknown}")
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    protocol = {
        "title": "PASQAL two-atom L3 covariant tensor + L4 bound audit",
        "version": VERSION,
        "validation_seed": VALIDATION_SEED,
        "tensor_direction_seed": TENSOR_DIRECTION_SEED,
        "coordinate_seed": COORDINATE_SEED,
        "n_new_paths": N_PATHS,
        "n_tensor_directions": N_TENSOR_DIRECTIONS,
        "zero_point_jet_method": (
            "order-6 block-matrix exponential coefficients at t=0"
        ),
        "jet_order": JET_ORDER,
        "target_t": TARGET_T,
        "axis_scales": AXIS_SCALES.tolist(),
        "A4_definition": "q4(v)=A4_ijkl v_i v_j v_k v_l",
        "G4_definition": "A4:M4",
        "coordinate_rule": "z=R y",
        "remainder_bound": (
            "mean_k sum_{m>=3}(2*K_k*|t|)^(2m)/(2m)!"
        ),
        "primary_ranking_gate": SPEARMAN_GATE,
        "claim_boundary": (
            "L3 is a numerical tensor-covariance audit. L4 uses an "
            "analytic finite-dimensional Dyson norm bound and only "
            "certifies pairs with disjoint prediction intervals."
        ),
    }
    protocol_hash = sha256_json(protocol)
    (output_dir / "protocol.json").write_text(
        json.dumps(protocol, indent=2), encoding="utf-8"
    )

    initialize_engine()
    _, constraint_rank, null_basis, constraint_info = (
        engine.constraint_geometry()
    )
    candidates, attempts = engine.generate_validation_candidates(null_basis)
    directions = direction_design()
    tensor_rows = [
        recover_tensor(candidate, directions) for candidate in candidates
    ]
    M4_z = noise_fourth_moment()
    G4_values = [
        contract4(row["A4"], M4_z) for row in tensor_rows
    ]
    predicted_order = [
        candidate.name
        for _, candidate in sorted(
            zip(G4_values, candidates), key=lambda item: item[0]
        )
    ]

    matrix = coordinate_map()
    inverse = np.linalg.inv(matrix)
    M4_y = transform_M4(M4_z, inverse)
    covariance_rows = []
    for row in tensor_rows:
        A4_y = transform_A4(row["A4"], matrix)
        z_contraction = contract4(row["A4"], M4_z)
        y_contraction = contract4(A4_y, M4_y)
        covariance_rows.append(
            {
                "path": row["path"],
                "z_contraction": z_contraction,
                "y_contraction": y_contraction,
                "absolute_contraction_error": abs(
                    z_contraction - y_contraction
                ),
                "relative_contraction_error": abs(
                    z_contraction - y_contraction
                ) / max(abs(z_contraction), 1e-30),
            }
        )

    direct_y = direct_refit_in_y(candidates[0], directions, matrix)
    algebraic_y = transform_A4(tensor_rows[0]["A4"], matrix)
    direct_covariance_relative_error = float(
        np.linalg.norm(direct_y - algebraic_y)
        / max(np.linalg.norm(algebraic_y), 1e-30)
    )
    g2_values = np.array([axis_G2(candidate) for candidate in candidates])
    g2_relative_spread = float(
        np.ptp(g2_values) / max(abs(float(np.mean(g2_values))), 1e-30)
    )
    maximum_tensor_fit_residual = float(
        max(row["tensor_fit_relative_residual"] for row in tensor_rows)
    )
    maximum_jet_imaginary_residual = float(
        max(
            row["maximum_directional_jet_imaginary_residual"]
            for row in tensor_rows
        )
    )
    maximum_contraction_relative_error = float(
        max(row["relative_contraction_error"] for row in covariance_rows)
    )
    constraint_residuals = [
        float(np.linalg.norm(engine.matched_residual(candidate.phases)))
        for candidate in candidates
    ]
    pre_outcome_audit = engine.ERROR_AUDIT.summary()

    K_axes = perturbation_integrated_norms()
    axis_bounds = [
        even_dyson_tail(K, TARGET_T) for K in K_axes
    ]
    common_remainder_bound = float(np.mean(axis_bounds))
    common_G2 = float(np.mean(g2_values))
    predicted_intervals = {
        candidate.name: {
            "center": (
                common_G2 * TARGET_T**2
                + G4 * TARGET_T**4
            ),
            "lower": (
                common_G2 * TARGET_T**2
                + G4 * TARGET_T**4
                - common_remainder_bound
            ),
            "upper": (
                common_G2 * TARGET_T**2
                + G4 * TARGET_T**4
                + common_remainder_bound
            ),
        }
        for candidate, G4 in zip(candidates, G4_values)
    }
    certified_pairs = []
    for first in candidates:
        for second in candidates:
            if first.name == second.name:
                continue
            if (
                predicted_intervals[first.name]["upper"]
                < predicted_intervals[second.name]["lower"]
            ):
                certified_pairs.append(
                    {"better": first.name, "worse": second.name}
                )

    certificate = {
        "protocol_sha256": protocol_hash,
        "created_unix_time": time.time(),
        "outcomes_unlocked": False,
        "predicted_order_best_to_worst": predicted_order,
        "G4_by_path": {
            candidate.name: G4
            for candidate, G4 in zip(candidates, G4_values)
        },
        "coordinate_matrix_R_for_z_equals_Ry": matrix.tolist(),
        "integrated_perturbation_norms_K": K_axes.tolist(),
        "axis_remainder_bounds": axis_bounds,
        "common_remainder_bound": common_remainder_bound,
        "predicted_intervals": predicted_intervals,
        "theorem_certified_pairs": certified_pairs,
        "candidate_phases": {
            candidate.name: candidate.phases.tolist()
            for candidate in candidates
        },
        "pre_outcome_error_audit": pre_outcome_audit,
    }
    certificate_hash = sha256_json(certificate)
    certificate_path = output_dir / "ranking_certificate.json"
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
    mean_infidelities = [row["mean_infidelity"] for row in performance]
    ranking_result = spearmanr(
        [-value for value in G4_values],
        [-value for value in mean_infidelities],
    )
    ranking_rho = float(ranking_result.statistic)
    actual_order = [
        candidate.name
        for _, candidate in sorted(
            zip(mean_infidelities, candidates), key=lambda item: item[0]
        )
    ]
    actual_map = {
        row["path"]: row["mean_infidelity"] for row in performance
    }
    certified_pairs_correct = all(
        actual_map[row["better"]] < actual_map[row["worse"]]
        for row in certified_pairs
    )

    l3_gates = {
        "tensor_design_full_rank": True,
        "tensor_fit_residual": (
            maximum_tensor_fit_residual <= TENSOR_FIT_RESIDUAL_TOL
        ),
        "zero_point_jet_real": (
            maximum_jet_imaginary_residual
            <= JET_IMAGINARY_RESIDUAL_TOL
        ),
        "direct_coordinate_refit": (
            direct_covariance_relative_error
            <= DIRECT_COVARIANCE_RELATIVE_TOL
        ),
        "invariant_contraction": (
            maximum_contraction_relative_error
            <= CONTRACTION_RELATIVE_TOL
        ),
        "G2_matching": (
            g2_relative_spread <= G2_RELATIVE_SPREAD_TOL
        ),
        "prospective_ranking": ranking_rho >= SPEARMAN_GATE,
    }
    l3_supported = all(l3_gates.values())
    l4_gates = {
        "analytic_bound_computed_before_outcomes": True,
        "zero_point_coefficients_from_block_exponential": True,
        "at_least_one_pair_certified": len(certified_pairs) > 0,
        "all_certified_pairs_correct": certified_pairs_correct,
    }
    l4_supported = all(l4_gates.values())
    if l3_supported and l4_supported:
        status = "L3_COVARIANT_G4_AND_L4_ORDERING_BOUND_SUPPORTED"
    elif l3_supported:
        status = "L3_COVARIANT_G4_SUPPORTED_L4_BOUND_INCONCLUSIVE"
    else:
        status = "L3_OR_PROTOCOL_NOT_SUPPORTED"

    report = {
        "scientific_status": status,
        "protocol_sha256": protocol_hash,
        "ranking_certificate_sha256": certificate_hash,
        "L3": {
            "supported": l3_supported,
            "gates": l3_gates,
            "coordinate_matrix_condition_number": float(
                np.linalg.cond(matrix)
            ),
            "maximum_tensor_fit_relative_residual": (
                maximum_tensor_fit_residual
            ),
            "maximum_jet_imaginary_residual": (
                maximum_jet_imaginary_residual
            ),
            "direct_covariance_relative_error": (
                direct_covariance_relative_error
            ),
            "maximum_contraction_relative_error": (
                maximum_contraction_relative_error
            ),
            "G2_relative_spread": g2_relative_spread,
            "prospective_mean_spearman": ranking_rho,
            "prospective_mean_spearman_pvalue": float(
                ranking_result.pvalue
            ),
            "predicted_order": predicted_order,
            "actual_order": actual_order,
            "covariance_rows": covariance_rows,
        },
        "L4": {
            "supported": l4_supported,
            "gates": l4_gates,
            "target_t": TARGET_T,
            "integrated_perturbation_norms_K": K_axes.tolist(),
            "axis_remainder_bounds": axis_bounds,
            "common_remainder_bound": common_remainder_bound,
            "n_certified_ordered_pairs": len(certified_pairs),
            "n_possible_unordered_pairs": (
                N_PATHS * (N_PATHS - 1) // 2
            ),
            "certified_pairs": certified_pairs,
            "interpretation": (
                "The analytic bound is valid but may be too conservative. "
                "No theorem claim is made unless at least one pair has "
                "disjoint prediction intervals."
            ),
        },
        "constraint_rank": constraint_rank,
        "constraint_info": constraint_info,
        "maximum_constraint_residual": max(constraint_residuals),
        "generation_attempts": attempts,
        "pre_outcome_error_audit": pre_outcome_audit,
        "held_out_error_audit": held_out_audit,
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    print("=" * 112)
    print("PASQAL TWO-ATOM L3 COVARIANT G4 + L4 REMAINDER-BOUND AUDIT")
    print("=" * 112)
    print(
        json.dumps(
            {
                "scientific_status": status,
                "n_new_paths": N_PATHS,
                "L3_supported": l3_supported,
                "tensor_components_symmetric_3D_order4": len(MULTI4),
                "maximum_tensor_fit_relative_residual": (
                    maximum_tensor_fit_residual
                ),
                "direct_covariance_relative_error": (
                    direct_covariance_relative_error
                ),
                "maximum_invariant_contraction_relative_error": (
                    maximum_contraction_relative_error
                ),
                "G2_relative_spread": g2_relative_spread,
                "prospective_mean_spearman": ranking_rho,
                "prospective_mean_spearman_pvalue": float(
                    ranking_result.pvalue
                ),
                "L4_supported": l4_supported,
                "target_t": TARGET_T,
                "common_analytic_remainder_bound": (
                    common_remainder_bound
                ),
                "theorem_certified_pairs": len(certified_pairs),
                "all_certified_pairs_correct": certified_pairs_correct,
                "protocol_sha256": protocol_hash,
                "ranking_certificate_sha256": certificate_hash,
                "output_directory": str(output_dir),
            },
            indent=2,
        )
    )
    print("\nInterpretation")
    if l3_supported:
        print(
            "  L3 PASS: G4 is represented by a coordinate-covariant "
            "quartic response tensor and its noise-moment contraction is "
            "coordinate invariant."
        )
    else:
        print("  L3 did not pass every predeclared gate.")
    if l4_supported:
        print(
            "  L4 PASS: the analytic remainder bound theorem-certifies "
            "at least one finite-error ordering."
        )
    else:
        print(
            "  L4 INCONCLUSIVE: the analytic Dyson bound is valid but too "
            "wide to certify a finite-error ordering at the target scale."
        )
        print(
            "  Do not call the current result a rigorous finite-radius "
            "ordering theorem."
        )


if __name__ == "__main__":
    main()
