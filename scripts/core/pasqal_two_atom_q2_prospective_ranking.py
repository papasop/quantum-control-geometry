#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASQAL two-atom Q2/J1 prospective ranking audit v1.0
====================================================

Required companion file:
    pasqal_two_atom_matched_fibre_test.py

Question
--------
Can a zero-noise local geometric quantity rank finite-error robustness inside
the two-atom, endpoint- and first-order-matched implementation fibre?

Discovery/validation separation
-------------------------------
1. The already-observed quartet
       reference, fibre_A, fibre_B, fibre_C
   is used only to freeze the orientation:
       larger Q2/J1 predicts better robustness.
   Its correlation is RETROSPECTIVE and is not the primary result.

2. Twelve new validation paths are generated using only:
       * endpoint-state matching;
       * first-order amplitude-state matching;
       * first-order detuning-state matching;
       * first-order interaction-state matching.
   No held-out finite-error outcome is evaluated during path generation.

3. Q2/J1 is computed at the zero-noise point. A ranking certificate containing
   the candidate paths, geometric scores, and predicted ordering is written
   and SHA-256 hashed.

4. Only after the certificate exists is the held-out six-error outcome
   evaluator unlocked.

Primary predeclared gate
------------------------
    Spearman(geometry score, -mean held-out infidelity) >= 0.95

With 12 validation paths this is a real ranking test. With only four paths,
rho >= 0.95 would require exact ordering and has weak resolution.

Geometry
--------
Let |psi(e)> be the phase-fixed output state for dimensionless physical error
coordinates e = (epsilon_Omega, Delta/Omega, epsilon_V). At e=0,

    J_i = P_perp partial_i |psi>,
    H_ij = P_perp partial_i partial_j |psi>.

For the predeclared six-axis physical error design E,

    J1 = mean_e ||J e||^2,
    Q2 = mean_e ||(1/2) H[e,e]||^2,
    score = Q2 / J1.

The horizontal projector P_perp removes global phase. The physical error
coordinates and their scales are part of the frozen protocol.

Important boundary
------------------
This is a local-state geometry test, not a full-unitary curvature theorem.
Failure of the rho gate rejects this particular Q2/J1 ranking rule on this
validation set; it does not logically reject every possible geometric
predictor.

Colab
-----
Upload both Python files, then run:

    %run /content/pasqal_two_atom_q2_prospective_ranking.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from scipy.linalg import svd
from scipy.optimize import least_squares
from scipy.stats import spearmanr

try:
    import pasqal_two_atom_matched_fibre_test as base
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing pasqal_two_atom_matched_fibre_test.py. "
        "Upload it beside this file and rerun."
    ) from exc


VERSION = "1.0"
VALIDATION_SEED = 20260731
N_VALIDATION_PATHS = 12
MAX_GENERATION_ATTEMPTS = 30

CONSTRAINT_JACOBIAN_STEP = 2.0e-5
CONSTRAINT_RANK_CUTOFF = 1.0e-6
CONSTRAINT_RESIDUAL_TOL = 2.0e-7
MIN_REFERENCE_PHASE_DISTANCE = 0.30
MIN_PAIR_PHASE_DISTANCE = 0.20

Q2_FD_STEP = 5.0e-4
GEOMETRY_MAX_ERROR_COMPONENT = 1.0e-3
HELD_OUT_MIN_NONZERO_COMPONENT = min(
    abs(float(error[key]))
    for error in base.HELD_OUT_ERRORS
    for key in ("amplitude", "detuning", "interaction")
    if float(error[key]) != 0.0
)

SPEARMAN_GATE = 0.95
TOP1_REQUIRED = True
J1_RELATIVE_SPREAD_TOL = 2.0e-5
HESSIAN_SYMMETRY_TOL = 2.0e-5

PREDICTION_ORIENTATION = "larger_Q2_over_J1_predicts_lower_mean_infidelity"
OUTDIR = Path("pasqal_two_atom_q2_prospective_results")

OUTCOMES_UNLOCKED = False


@dataclass(frozen=True)
class Candidate:
    name: str
    phases: np.ndarray


class ErrorPhaseAudit:
    def __init__(self) -> None:
        self.phase = "uninitialized"
        self.vectors: list[tuple[float, float, float]] = []

    def start(self, phase: str) -> None:
        self.phase = phase
        self.vectors = []

    def record(self, values: Iterable[float]) -> None:
        vector = tuple(float(value) for value in values)
        if len(vector) != 3:
            raise ValueError("Expected a three-component error vector.")
        self.vectors.append(vector)

    def summary(self) -> dict[str, Any]:
        maximum = max(
            (max(abs(value) for value in vector) for vector in self.vectors),
            default=0.0,
        )
        nonzero = [
            abs(value)
            for vector in self.vectors
            for value in vector
            if value != 0.0
        ]
        return {
            "phase": self.phase,
            "evaluations": len(self.vectors),
            "distinct_vectors": len(set(self.vectors)),
            "maximum_absolute_component": maximum,
            "minimum_nonzero_absolute_component": (
                min(nonzero) if nonzero else 0.0
            ),
        }


ERROR_AUDIT = ErrorPhaseAudit()


def canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audited_state(phases: Iterable[float], error: Iterable[float]) -> np.ndarray:
    error_tuple = tuple(float(value) for value in error)
    ERROR_AUDIT.record(error_tuple)
    return base.analytic_state(phases, *error_tuple)


def phase_aligned(anchor: np.ndarray, state: np.ndarray) -> np.ndarray:
    return state * base.phase_factor(anchor, state)


def horizontal(base_state: np.ndarray, vector: np.ndarray) -> np.ndarray:
    return vector - base_state * np.vdot(base_state, vector)


def local_state_and_tangents(
    phases: Iterable[float],
) -> tuple[np.ndarray, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    phases = tuple(phases)
    state0 = audited_state(phases, (0.0, 0.0, 0.0))
    tangents: list[np.ndarray] = []
    for axis in range(3):
        plus = np.zeros(3)
        minus = np.zeros(3)
        plus[axis] = base.FD_STEP
        minus[axis] = -base.FD_STEP
        state_plus = phase_aligned(state0, audited_state(phases, plus))
        state_minus = phase_aligned(state0, audited_state(phases, minus))
        tangent = (state_plus - state_minus) / (2.0 * base.FD_STEP)
        tangents.append(horizontal(state0, tangent))
    return state0, (tangents[0], tangents[1], tangents[2])


REFERENCE_PHASES = np.asarray(base.PATHS[0].phases, dtype=float)
REFERENCE_STATE: np.ndarray
REFERENCE_TANGENTS: tuple[np.ndarray, np.ndarray, np.ndarray]
REFERENCE_FEATURE: np.ndarray


def matched_feature(phases: Iterable[float]) -> np.ndarray:
    state, tangents = local_state_and_tangents(phases)
    common_phase = base.phase_factor(REFERENCE_STATE, state)
    values = [state * common_phase]
    values.extend(tangent * common_phase for tangent in tangents)
    vector = np.concatenate(values)
    return np.r_[vector.real, vector.imag]


def matched_residual(phases: Iterable[float]) -> np.ndarray:
    return matched_feature(phases) - REFERENCE_FEATURE


def wrapped_phase_distance(first: np.ndarray, second: np.ndarray) -> float:
    return float(
        np.linalg.norm(np.angle(np.exp(1.0j * (first - second))))
    )


def constraint_geometry() -> tuple[np.ndarray, int, np.ndarray, dict]:
    eye = np.eye(base.N_SEGMENTS)
    columns = []
    for index in range(base.N_SEGMENTS):
        plus = REFERENCE_PHASES + CONSTRAINT_JACOBIAN_STEP * eye[index]
        minus = REFERENCE_PHASES - CONSTRAINT_JACOBIAN_STEP * eye[index]
        columns.append(
            (matched_residual(plus) - matched_residual(minus))
            / (2.0 * CONSTRAINT_JACOBIAN_STEP)
        )
    jacobian = np.column_stack(columns)
    _, singular_values, vh = svd(jacobian, full_matrices=True)
    rank = int(np.sum(singular_values > CONSTRAINT_RANK_CUTOFF))
    null_basis = vh[rank:]
    return jacobian, rank, null_basis, {
        "rank": rank,
        "nullity": int(null_basis.shape[0]),
        "singular_values": singular_values.tolist(),
        "rank_cutoff": CONSTRAINT_RANK_CUTOFF,
    }


def generate_validation_candidates(
    null_basis: np.ndarray,
) -> tuple[list[Candidate], list[dict]]:
    rng = np.random.default_rng(VALIDATION_SEED)
    accepted: list[Candidate] = []
    attempts: list[dict] = []

    for attempt_index in range(MAX_GENERATION_ATTEMPTS):
        if len(accepted) >= N_VALIDATION_PATHS:
            break
        coefficients = rng.normal(size=null_basis.shape[0])
        direction = coefficients @ null_basis
        direction /= max(float(np.max(np.abs(direction))), 1.0e-15)
        scale = float(rng.uniform(0.5, 1.5))
        initial = REFERENCE_PHASES + scale * direction
        fit = least_squares(
            matched_residual,
            initial,
            method="trf",
            max_nfev=180,
            ftol=2.0e-11,
            xtol=2.0e-11,
            gtol=2.0e-11,
        )
        phases = np.mod(fit.x, 2.0 * math.pi)
        residual_norm = float(np.linalg.norm(matched_residual(phases)))
        reference_distance = wrapped_phase_distance(
            phases, REFERENCE_PHASES
        )
        minimum_pair_distance = min(
            (
                wrapped_phase_distance(phases, candidate.phases)
                for candidate in accepted
            ),
            default=float("inf"),
        )
        valid = bool(
            residual_norm <= CONSTRAINT_RESIDUAL_TOL
            and reference_distance >= MIN_REFERENCE_PHASE_DISTANCE
            and minimum_pair_distance >= MIN_PAIR_PHASE_DISTANCE
        )
        attempt = {
            "attempt_index": attempt_index,
            "optimizer_success": bool(fit.success),
            "optimizer_nfev": int(fit.nfev),
            "initial_null_scale": scale,
            "constraint_residual_norm": residual_norm,
            "reference_phase_distance": reference_distance,
            "minimum_previous_pair_distance": minimum_pair_distance,
            "accepted": valid,
        }
        attempts.append(attempt)
        if valid:
            accepted.append(
                Candidate(f"pv{len(accepted) + 1:02d}", phases.copy())
            )

    if len(accepted) != N_VALIDATION_PATHS:
        raise RuntimeError(
            f"Generated {len(accepted)}/{N_VALIDATION_PATHS} candidates."
        )
    return accepted, attempts


def local_jacobian_and_hessian(
    phases: Iterable[float],
) -> tuple[np.ndarray, np.ndarray, dict]:
    phases = tuple(phases)
    state0, tangents = local_state_and_tangents(phases)
    jacobian = np.column_stack(tangents)
    hessian = np.zeros((4, 3, 3), dtype=complex)

    for first in range(3):
        plus = np.zeros(3)
        minus = np.zeros(3)
        plus[first] = Q2_FD_STEP
        minus[first] = -Q2_FD_STEP
        state_plus = phase_aligned(
            state0, audited_state(phases, plus)
        )
        state_minus = phase_aligned(
            state0, audited_state(phases, minus)
        )
        hessian[:, first, first] = (
            state_plus - 2.0 * state0 + state_minus
        ) / (Q2_FD_STEP**2)

        for second in range(first):
            pp = np.zeros(3)
            pm = np.zeros(3)
            mp = np.zeros(3)
            mm = np.zeros(3)
            pp[first], pp[second] = +Q2_FD_STEP, +Q2_FD_STEP
            pm[first], pm[second] = +Q2_FD_STEP, -Q2_FD_STEP
            mp[first], mp[second] = -Q2_FD_STEP, +Q2_FD_STEP
            mm[first], mm[second] = -Q2_FD_STEP, -Q2_FD_STEP
            mixed = (
                phase_aligned(state0, audited_state(phases, pp))
                - phase_aligned(state0, audited_state(phases, pm))
                - phase_aligned(state0, audited_state(phases, mp))
                + phase_aligned(state0, audited_state(phases, mm))
            ) / (4.0 * Q2_FD_STEP**2)
            hessian[:, first, second] = mixed
            hessian[:, second, first] = mixed

    for first in range(3):
        for second in range(3):
            hessian[:, first, second] = horizontal(
                state0, hessian[:, first, second]
            )

    symmetry_error = float(
        np.linalg.norm(hessian - np.swapaxes(hessian, 1, 2))
    )
    return jacobian, hessian, {
        "hessian_symmetry_error": symmetry_error,
        "jacobian_frobenius_norm": float(np.linalg.norm(jacobian)),
        "hessian_frobenius_norm": float(np.linalg.norm(hessian)),
    }


def geometry_score(candidate: Candidate) -> dict:
    jacobian, hessian, diagnostics = local_jacobian_and_hessian(
        candidate.phases
    )
    j1_terms: list[float] = []
    q2_terms: list[float] = []
    for error in base.HELD_OUT_ERRORS:
        vector = np.array(
            [
                error["amplitude"],
                error["detuning"],
                error["interaction"],
            ],
            dtype=float,
        )
        first = jacobian @ vector
        second = 0.5 * np.einsum(
            "aij,i,j->a", hessian, vector, vector
        )
        j1_terms.append(float(np.vdot(first, first).real))
        q2_terms.append(float(np.vdot(second, second).real))
    j1 = float(np.mean(j1_terms))
    q2 = float(np.mean(q2_terms))
    return {
        "path": candidate.name,
        "J1": j1,
        "Q2": q2,
        "Q2_over_J1": q2 / max(j1, 1.0e-30),
        **diagnostics,
    }


def held_out_performance(candidate: Candidate) -> dict:
    if not OUTCOMES_UNLOCKED:
        raise RuntimeError(
            "Held-out outcome evaluator called before ranking certificate."
        )
    infidelities: list[float] = []
    rows: list[dict] = []
    for error in base.HELD_OUT_ERRORS:
        vector = (
            error["amplitude"],
            error["detuning"],
            error["interaction"],
        )
        state = audited_state(candidate.phases, vector)
        infidelity = base.state_infidelity(REFERENCE_STATE, state)
        infidelities.append(infidelity)
        rows.append(
            {
                "error_label": error["label"],
                "infidelity": infidelity,
            }
        )
    return {
        "path": candidate.name,
        "mean_infidelity": float(np.mean(infidelities)),
        "worst_infidelity": float(np.max(infidelities)),
        "rows": rows,
    }


def exact_rank(values: list[float], descending: bool) -> list[int]:
    return sorted(
        range(len(values)),
        key=lambda index: values[index],
        reverse=descending,
    )


def discovery_calibration() -> dict:
    geometry_rows = [
        geometry_score(
            Candidate(path.name, np.asarray(path.phases, dtype=float))
        )
        for path in base.PATHS
    ]
    # These are already-observed outcomes. They calibrate direction only and
    # are explicitly excluded from the primary prospective gate.
    known = base.finite_error_audit(REFERENCE_STATE)[1]["by_path"]
    scores = [row["Q2_over_J1"] for row in geometry_rows]
    performance = [
        -float(known[path.name]["mean_infidelity"]) for path in base.PATHS
    ]
    rho = float(spearmanr(scores, performance).statistic)
    return {
        "status": "RETROSPECTIVE_DIRECTION_CALIBRATION_ONLY",
        "orientation": PREDICTION_ORIENTATION,
        "spearman": rho,
        "geometry": geometry_rows,
        "known_mean_infidelity": {
            path.name: float(known[path.name]["mean_infidelity"])
            for path in base.PATHS
        },
    }


def main() -> None:
    global REFERENCE_STATE
    global REFERENCE_TANGENTS
    global REFERENCE_FEATURE
    global OUTCOMES_UNLOCKED

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTDIR)
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"[notice] ignored notebook arguments: {unknown}")
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    protocol = {
        "title": "PASQAL two-atom Q2/J1 prospective ranking audit",
        "version": VERSION,
        "validation_seed": VALIDATION_SEED,
        "n_validation_paths": N_VALIDATION_PATHS,
        "candidate_generation_uses_held_out_outcomes": False,
        "geometry_uses_held_out_outcomes": False,
        "prediction_orientation": PREDICTION_ORIENTATION,
        "primary_endpoint": "mean held-out state infidelity",
        "primary_gate": {"spearman_minimum": SPEARMAN_GATE},
        "secondary_endpoint": "worst held-out state infidelity",
        "top1_required": TOP1_REQUIRED,
        "q2_fd_step": Q2_FD_STEP,
        "constraint_fd_step": base.FD_STEP,
        "geometry_max_error_component": GEOMETRY_MAX_ERROR_COMPONENT,
        "held_out_min_nonzero_component": HELD_OUT_MIN_NONZERO_COMPONENT,
        "held_out_errors": base.HELD_OUT_ERRORS,
        "geometry_definition": {
            "J1": "mean_e ||J e||^2",
            "Q2": "mean_e ||0.5 H[e,e]||^2",
            "score": "Q2/J1",
            "horizontal_global_phase_projection": True,
        },
    }
    protocol_text = canonical_json(protocol)
    protocol_hash = sha256_text(protocol_text)
    (output_dir / "protocol.json").write_text(
        json.dumps(protocol, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    ERROR_AUDIT.start("constraint_and_geometry_only")
    REFERENCE_STATE, REFERENCE_TANGENTS = local_state_and_tangents(
        REFERENCE_PHASES
    )
    reference_values = [REFERENCE_STATE]
    reference_values.extend(REFERENCE_TANGENTS)
    reference_complex = np.concatenate(reference_values)
    REFERENCE_FEATURE = np.r_[reference_complex.real, reference_complex.imag]

    discovery = discovery_calibration()
    _, constraint_rank, null_basis, constraint_info = constraint_geometry()
    candidates, generation_attempts = generate_validation_candidates(null_basis)

    geometry_rows = [geometry_score(candidate) for candidate in candidates]
    geometry_scores = [row["Q2_over_J1"] for row in geometry_rows]
    predicted_indices = exact_rank(geometry_scores, descending=True)
    predicted_order = [candidates[index].name for index in predicted_indices]

    j1_values = np.array([row["J1"] for row in geometry_rows])
    j1_relative_spread = float(np.ptp(j1_values) / np.mean(j1_values))
    maximum_hessian_symmetry_error = float(
        max(row["hessian_symmetry_error"] for row in geometry_rows)
    )
    pre_outcome_audit = ERROR_AUDIT.summary()

    certificate = {
        "protocol_sha256": protocol_hash,
        "created_unix_time": time.time(),
        "outcomes_unlocked": False,
        "prediction_orientation": PREDICTION_ORIENTATION,
        "predicted_order_best_to_worst": predicted_order,
        "geometry_rows": geometry_rows,
        "candidate_phases": {
            candidate.name: candidate.phases.tolist()
            for candidate in candidates
        },
        "constraint_geometry": constraint_info,
        "pre_outcome_error_audit": pre_outcome_audit,
    }
    certificate_text = canonical_json(certificate)
    certificate_hash = sha256_text(certificate_text)
    certificate_path = output_dir / "ranking_certificate.json"
    certificate_path.write_text(
        json.dumps(certificate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    with certificate_path.open("rb") as stream:
        os.fsync(stream.fileno())

    # Outcome phase is deliberately below certificate creation and hashing.
    OUTCOMES_UNLOCKED = True
    ERROR_AUDIT.start("held_out_outcomes")
    performance_rows = [
        held_out_performance(candidate) for candidate in candidates
    ]
    held_out_audit = ERROR_AUDIT.summary()

    mean_infidelities = [
        row["mean_infidelity"] for row in performance_rows
    ]
    worst_infidelities = [
        row["worst_infidelity"] for row in performance_rows
    ]
    mean_rho_result = spearmanr(
        geometry_scores, [-value for value in mean_infidelities]
    )
    worst_rho_result = spearmanr(
        geometry_scores, [-value for value in worst_infidelities]
    )
    mean_rho = float(mean_rho_result.statistic)
    worst_rho = float(worst_rho_result.statistic)
    actual_mean_indices = exact_rank(mean_infidelities, descending=False)
    actual_worst_indices = exact_rank(worst_infidelities, descending=False)
    actual_mean_order = [
        candidates[index].name for index in actual_mean_indices
    ]
    actual_worst_order = [
        candidates[index].name for index in actual_worst_indices
    ]
    top1_pass = predicted_order[0] == actual_mean_order[0]

    constraint_residuals = [
        float(np.linalg.norm(matched_residual(candidate.phases)))
        for candidate in candidates
    ]
    gates = {
        "protocol_frozen": bool(protocol_hash),
        "ranking_certificate_written_before_outcomes": bool(certificate_hash),
        "validation_sample_size": len(candidates) == N_VALIDATION_PATHS,
        "constraint_rank_has_fibre": (
            constraint_rank < base.N_SEGMENTS
            and null_basis.shape[0] > 0
        ),
        "all_validation_constraints_pass": (
            max(constraint_residuals) <= CONSTRAINT_RESIDUAL_TOL
        ),
        "geometry_phase_did_not_touch_held_out_scale": (
            pre_outcome_audit["maximum_absolute_component"]
            <= GEOMETRY_MAX_ERROR_COMPONENT
            and pre_outcome_audit["maximum_absolute_component"]
            < HELD_OUT_MIN_NONZERO_COMPONENT
        ),
        "held_out_phase_reached_predeclared_scale": (
            held_out_audit["minimum_nonzero_absolute_component"]
            >= HELD_OUT_MIN_NONZERO_COMPONENT
        ),
        "J1_matching_preserved": (
            j1_relative_spread <= J1_RELATIVE_SPREAD_TOL
        ),
        "hessian_numerically_symmetric": (
            maximum_hessian_symmetry_error <= HESSIAN_SYMMETRY_TOL
        ),
        "primary_spearman_gate": mean_rho >= SPEARMAN_GATE,
        "top1_gate": (top1_pass if TOP1_REQUIRED else True),
    }
    all_integrity_gates = all(
        value
        for key, value in gates.items()
        if key not in {"primary_spearman_gate", "top1_gate"}
    )
    supported = bool(all(gates.values()))
    status = (
        "PASQAL_TWO_ATOM_Q2_PROSPECTIVE_RANKING_SUPPORTED"
        if supported
        else (
            "Q2_RANKING_NOT_SUPPORTED"
            if all_integrity_gates
            else "NUMERICAL_OR_PROTOCOL_INVALID"
        )
    )

    combined_rows = []
    geometry_by_name = {row["path"]: row for row in geometry_rows}
    performance_by_name = {row["path"]: row for row in performance_rows}
    for candidate in candidates:
        combined_rows.append(
            {
                **geometry_by_name[candidate.name],
                "mean_infidelity": performance_by_name[candidate.name][
                    "mean_infidelity"
                ],
                "worst_infidelity": performance_by_name[candidate.name][
                    "worst_infidelity"
                ],
                "predicted_rank": predicted_order.index(candidate.name) + 1,
                "actual_mean_rank": actual_mean_order.index(candidate.name) + 1,
                "actual_worst_rank": (
                    actual_worst_order.index(candidate.name) + 1
                ),
            }
        )

    script_path = Path(__file__) if "__file__" in globals() else None
    report = {
        "scientific_status": status,
        "claim_boundary": (
            "Primary support requires prospective Q2/J1 ranking on newly "
            "generated matched paths. Failure rejects this Q2/J1 rule on "
            "this validation set, not every possible geometric predictor."
        ),
        "protocol_sha256": protocol_hash,
        "ranking_certificate_sha256": certificate_hash,
        "script_sha256": (
            sha256_file(script_path)
            if script_path is not None and script_path.is_file()
            else None
        ),
        "discovery_calibration": discovery,
        "validation": {
            "n_paths": len(candidates),
            "mean_spearman": mean_rho,
            "mean_spearman_pvalue": float(mean_rho_result.pvalue),
            "worst_spearman_secondary": worst_rho,
            "worst_spearman_pvalue": float(worst_rho_result.pvalue),
            "predeclared_spearman_gate": SPEARMAN_GATE,
            "predicted_order_best_to_worst": predicted_order,
            "actual_mean_order_best_to_worst": actual_mean_order,
            "actual_worst_order_best_to_worst": actual_worst_order,
            "top1_pass": top1_pass,
            "combined_rows": combined_rows,
        },
        "constraint_geometry": constraint_info,
        "generation_attempts": generation_attempts,
        "maximum_constraint_residual": max(constraint_residuals),
        "j1_relative_spread": j1_relative_spread,
        "maximum_hessian_symmetry_error": maximum_hessian_symmetry_error,
        "pre_outcome_error_audit": pre_outcome_audit,
        "held_out_error_audit": held_out_audit,
        "gates": gates,
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 104)
    print("PASQAL TWO-ATOM Q2/J1 PROSPECTIVE RANKING AUDIT")
    print("=" * 104)
    print(
        json.dumps(
            {
                "scientific_status": status,
                "protocol_sha256": protocol_hash,
                "ranking_certificate_sha256": certificate_hash,
                "discovery_quartet_spearman_retrospective": discovery[
                    "spearman"
                ],
                "n_prospective_validation_paths": len(candidates),
                "prospective_mean_spearman": mean_rho,
                "prospective_mean_spearman_pvalue": float(
                    mean_rho_result.pvalue
                ),
                "predeclared_spearman_gate": SPEARMAN_GATE,
                "prospective_worst_spearman_secondary": worst_rho,
                "predicted_top_path": predicted_order[0],
                "actual_best_mean_path": actual_mean_order[0],
                "top1_pass": top1_pass,
                "all_integrity_gates_pass": all_integrity_gates,
                "primary_spearman_gate_pass": gates[
                    "primary_spearman_gate"
                ],
                "output_directory": str(output_dir),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print("\nPredicted order (best -> worst)")
    print("  " + " > ".join(predicted_order))
    print("Actual mean-performance order (best -> worst)")
    print("  " + " > ".join(actual_mean_order))
    print("\nInterpretation")
    if supported:
        print(
            "  The frozen zero-noise Q2/J1 score prospectively ranked "
            "held-out finite-error performance."
        )
    elif all_integrity_gates:
        print(
            "  The experiment is numerically valid, but the predeclared "
            "Q2/J1 ranking rule did not reach rho >= 0.95."
        )
        print(
            "  Do not call the current Q2/J1 rule a validated mechanism or "
            "use it for hardware selection."
        )
    else:
        print(
            "  Protocol/numerical integrity failed; no scientific "
            "interpretation is allowed."
        )


if __name__ == "__main__":
    main()
