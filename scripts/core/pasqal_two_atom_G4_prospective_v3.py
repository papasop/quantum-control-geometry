#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASQAL two-atom zero-point G4 prospective ranking audit v3.0
=============================================================

Required companion files:
  pasqal_two_atom_matched_fibre_test.py
  pasqal_two_atom_q2_prospective_ranking.py

For each physical error axis k, define the symmetric infidelity response

  S_{gamma,k}(t) =
    [I_gamma(+t e_k) + I_gamma(-t e_k)] / 2
    = a2_{gamma,k} t^2 + a4_{gamma,k} t^4
      + a6_{gamma,k} t^6 + O(t^8).

The frozen prospective invariant is

  G4(gamma) = mean_k a4_{gamma,k},

with smaller G4 predicting lower mean held-out infidelity.

The prior twelve paths are formula-training data only.  On them, -G4 reached
Spearman 0.9930069930; adding a6 did not improve the rank correlation.
This script therefore freezes the minimal sufficient fourth-order rule before
creating twenty new paths with seed 20260802.  It writes and hashes the
predicted ranking before unlocking held-out outcomes.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

try:
    import pasqal_two_atom_matched_fibre_test as base
    import pasqal_two_atom_q2_prospective_ranking as engine
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Place this file beside pasqal_two_atom_matched_fibre_test.py and "
        "pasqal_two_atom_q2_prospective_ranking.py, then rerun."
    ) from exc


VERSION = "3.0"
VALIDATION_SEED = 20260802
N_VALIDATION_PATHS = 20
MAX_GENERATION_ATTEMPTS = 70
SPEARMAN_GATE = 0.95
TOP1_REQUIRED = True
OUTDIR = Path("pasqal_two_atom_G4_v3_results")

# Fixed before the new validation outcomes are evaluated.
FIT_RADII = np.array(
    [1 / 32, 1 / 24, 1 / 20, 1 / 16, 1 / 14, 1 / 12, 1 / 10, 1 / 8],
    dtype=float,
)
PRIMARY_TMAX = 1 / 8
STABILITY_TMAX = 1 / 10
FIT_MAX_ORDER = 6
A2_RELATIVE_SPREAD_TOL = 2.0e-5
G4_RANK_STABILITY_GATE = 0.95

TRAINING_SEED = 20260731
TRAINING_PATHS = 12
TRAINING_G4_SPEARMAN = 0.9930069930069931
TRAINING_G4_PLUS_G6_SPEARMAN = 0.9930069930069931
FORMULA_SELECTION_RULE = (
    "choose the lowest even order reaching training Spearman >= 0.95; "
    "G4 selected because adding G6 did not improve Spearman"
)

AXIS_MAGNITUDES = np.array([0.06, 0.04, 0.05], dtype=float)
AXIS_NAMES = ("amplitude", "detuning", "interaction")
LOCAL_MAX_ERROR_COMPONENT = PRIMARY_TMAX * float(
    np.max(AXIS_MAGNITUDES)
)
HELD_OUT_MIN_NONZERO_COMPONENT = min(
    abs(float(error[key]))
    for error in base.HELD_OUT_ERRORS
    for key in AXIS_NAMES
    if float(error[key]) != 0.0
)


def initialize_engine() -> None:
    engine.VALIDATION_SEED = VALIDATION_SEED
    engine.N_VALIDATION_PATHS = N_VALIDATION_PATHS
    engine.MAX_GENERATION_ATTEMPTS = MAX_GENERATION_ATTEMPTS
    engine.OUTCOMES_UNLOCKED = False
    engine.ERROR_AUDIT.start("constraint_and_G4_only")
    engine.REFERENCE_STATE, engine.REFERENCE_TANGENTS = (
        engine.local_state_and_tangents(engine.REFERENCE_PHASES)
    )
    values = [engine.REFERENCE_STATE, *engine.REFERENCE_TANGENTS]
    vector = np.concatenate(values)
    engine.REFERENCE_FEATURE = np.r_[vector.real, vector.imag]


def symmetric_axis_response(
    candidate: engine.Candidate,
    axis: int,
    radius: float,
    state0: np.ndarray,
) -> float:
    pair = []
    for sign in (-1.0, +1.0):
        error = np.zeros(3)
        error[axis] = sign * AXIS_MAGNITUDES[axis] * radius
        state = engine.audited_state(candidate.phases, error)
        pair.append(base.state_infidelity(state0, state))
    return float(np.mean(pair))


def fit_even_coefficients(
    candidate: engine.Candidate,
    tmax: float,
) -> dict:
    """Fit a2, a4, a6 with a scaled design matrix for conditioning."""
    radii = FIT_RADII[FIT_RADII <= tmax + 1.0e-15]
    if len(radii) < 4:
        raise RuntimeError("At least four radii are required.")
    state0 = engine.audited_state(
        candidate.phases, (0.0, 0.0, 0.0)
    )
    x = (radii / tmax) ** 2
    design = np.column_stack((x, x**2, x**3))
    axis_rows = []
    for axis, name in enumerate(AXIS_NAMES):
        response = np.array(
            [
                symmetric_axis_response(
                    candidate, axis, radius, state0
                )
                for radius in radii
            ]
        )
        scaled, residuals, _, _ = np.linalg.lstsq(
            design, response, rcond=None
        )
        fitted = design @ scaled
        denom = max(float(np.linalg.norm(response)), 1.0e-30)
        axis_rows.append(
            {
                "axis": name,
                "a2": float(scaled[0] / tmax**2),
                "a4": float(scaled[1] / tmax**4),
                "a6": float(scaled[2] / tmax**6),
                "relative_fit_residual": float(
                    np.linalg.norm(response - fitted) / denom
                ),
                "raw_responses": response.tolist(),
                "fit_residual_sum_squares": (
                    float(residuals[0]) if len(residuals) else 0.0
                ),
            }
        )
    return {
        "path": candidate.name,
        "tmax": tmax,
        "radii": radii.tolist(),
        "G2": float(np.mean([row["a2"] for row in axis_rows])),
        "G4": float(np.mean([row["a4"] for row in axis_rows])),
        "G6": float(np.mean([row["a6"] for row in axis_rows])),
        "maximum_relative_fit_residual": float(
            max(row["relative_fit_residual"] for row in axis_rows)
        ),
        "axes": axis_rows,
    }


def rank_names(
    candidates: list[engine.Candidate],
    values: list[float],
    descending: bool,
) -> list[str]:
    indices = sorted(
        range(len(values)),
        key=lambda index: values[index],
        reverse=descending,
    )
    return [candidates[index].name for index in indices]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTDIR)
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"[notice] ignored notebook arguments: {unknown}")
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    protocol = {
        "title": "PASQAL two-atom zero-point G4 prospective audit",
        "version": VERSION,
        "training_role": "formula_selection_only_not_confirmation",
        "training_seed": TRAINING_SEED,
        "training_paths": TRAINING_PATHS,
        "training_G4_spearman": TRAINING_G4_SPEARMAN,
        "training_G4_plus_G6_spearman": (
            TRAINING_G4_PLUS_G6_SPEARMAN
        ),
        "formula_selection_rule": FORMULA_SELECTION_RULE,
        "validation_seed": VALIDATION_SEED,
        "n_new_validation_paths": N_VALIDATION_PATHS,
        "candidate_generation_uses_validation_outcomes": False,
        "coefficient_fit_uses_validation_outcomes": False,
        "fit_radii": FIT_RADII.tolist(),
        "primary_tmax": PRIMARY_TMAX,
        "stability_tmax": STABILITY_TMAX,
        "formula": "G4 = mean_axis a4_axis",
        "score": "-G4",
        "prediction": "smaller_G4_predicts_lower_mean_infidelity",
        "primary_endpoint": "mean held-out state infidelity",
        "primary_gate": {"spearman_minimum": SPEARMAN_GATE},
        "top1_required": TOP1_REQUIRED,
        "coefficient_rank_stability_gate": G4_RANK_STABILITY_GATE,
        "a2_relative_spread_tolerance": A2_RELATIVE_SPREAD_TOL,
        "local_max_error_component": LOCAL_MAX_ERROR_COMPONENT,
        "held_out_min_nonzero_component": (
            HELD_OUT_MIN_NONZERO_COMPONENT
        ),
        "held_out_errors": base.HELD_OUT_ERRORS,
        "claim_boundary": (
            "G4 is extracted as a fourth-order coefficient from near-zero "
            "symmetric infidelity responses; this is local emulator "
            "evidence, not PASQAL Cloud or QPU evidence"
        ),
    }
    protocol_hash = engine.sha256_text(
        engine.canonical_json(protocol)
    )
    (output_dir / "protocol.json").write_text(
        json.dumps(protocol, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    initialize_engine()
    _, constraint_rank, null_basis, constraint_info = (
        engine.constraint_geometry()
    )
    candidates, generation_attempts = (
        engine.generate_validation_candidates(null_basis)
    )

    primary_rows = [
        fit_even_coefficients(candidate, PRIMARY_TMAX)
        for candidate in candidates
    ]
    stability_rows = [
        fit_even_coefficients(candidate, STABILITY_TMAX)
        for candidate in candidates
    ]
    g4_primary = [row["G4"] for row in primary_rows]
    g4_stability = [row["G4"] for row in stability_rows]
    scores = [-value for value in g4_primary]
    predicted_order = rank_names(
        candidates, g4_primary, descending=False
    )
    g4_stability_rho = float(
        spearmanr(g4_primary, g4_stability).statistic
    )
    g2_values = np.array([row["G2"] for row in primary_rows])
    g2_relative_spread = float(
        np.ptp(g2_values) / max(abs(float(np.mean(g2_values))), 1e-30)
    )
    max_fit_residual = float(
        max(
            row["maximum_relative_fit_residual"]
            for row in primary_rows + stability_rows
        )
    )
    constraint_residuals = [
        float(np.linalg.norm(engine.matched_residual(candidate.phases)))
        for candidate in candidates
    ]
    pre_outcome_audit = engine.ERROR_AUDIT.summary()

    certificate = {
        "protocol_sha256": protocol_hash,
        "outcomes_unlocked": False,
        "formula": "G4 = mean_axis a4_axis",
        "predicted_order_best_to_worst": predicted_order,
        "primary_G4_rows": primary_rows,
        "stability_G4_rows": stability_rows,
        "G4_fit_window_rank_stability_spearman": g4_stability_rho,
        "candidate_phases": {
            candidate.name: candidate.phases.tolist()
            for candidate in candidates
        },
        "constraint_geometry": constraint_info,
        "pre_outcome_error_audit": pre_outcome_audit,
    }
    certificate_hash = engine.sha256_text(
        engine.canonical_json(certificate)
    )
    certificate_path = output_dir / "ranking_certificate.json"
    certificate_path.write_text(
        json.dumps(certificate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    with certificate_path.open("rb") as stream:
        os.fsync(stream.fileno())

    # Outcomes are inaccessible until the frozen ranking is on disk.
    engine.OUTCOMES_UNLOCKED = True
    engine.ERROR_AUDIT.start("held_out_outcomes")
    performance_rows = [
        engine.held_out_performance(candidate) for candidate in candidates
    ]
    held_out_audit = engine.ERROR_AUDIT.summary()
    mean_infidelities = [
        row["mean_infidelity"] for row in performance_rows
    ]
    worst_infidelities = [
        row["worst_infidelity"] for row in performance_rows
    ]
    mean_result = spearmanr(
        scores, [-value for value in mean_infidelities]
    )
    worst_result = spearmanr(
        scores, [-value for value in worst_infidelities]
    )
    mean_rho = float(mean_result.statistic)
    worst_rho = float(worst_result.statistic)
    actual_mean_order = rank_names(
        candidates, mean_infidelities, descending=False
    )
    actual_worst_order = rank_names(
        candidates, worst_infidelities, descending=False
    )
    top1_pass = predicted_order[0] == actual_mean_order[0]

    gates = {
        "protocol_frozen": bool(protocol_hash),
        "ranking_certificate_written_before_outcomes": bool(
            certificate_hash
        ),
        "new_validation_sample_size": (
            len(candidates) == N_VALIDATION_PATHS
        ),
        "constraint_rank_has_fibre": (
            constraint_rank < base.N_SEGMENTS and null_basis.shape[0] > 0
        ),
        "all_validation_constraints_pass": (
            max(constraint_residuals) <= engine.CONSTRAINT_RESIDUAL_TOL
        ),
        "local_fit_below_held_out_scale": (
            pre_outcome_audit["maximum_absolute_component"]
            <= LOCAL_MAX_ERROR_COMPONENT + 1e-15
            and LOCAL_MAX_ERROR_COMPONENT
            < HELD_OUT_MIN_NONZERO_COMPONENT
        ),
        "held_out_phase_reached_predeclared_scale": (
            held_out_audit["minimum_nonzero_absolute_component"]
            >= HELD_OUT_MIN_NONZERO_COMPONENT
        ),
        "G2_matching_preserved": (
            g2_relative_spread <= A2_RELATIVE_SPREAD_TOL
        ),
        "G4_fit_window_rank_stable": (
            g4_stability_rho >= G4_RANK_STABILITY_GATE
        ),
        "primary_spearman_gate": mean_rho >= SPEARMAN_GATE,
        "top1_gate": top1_pass if TOP1_REQUIRED else True,
    }
    integrity_keys = set(gates) - {
        "primary_spearman_gate", "top1_gate"
    }
    all_integrity_gates = all(gates[key] for key in integrity_keys)
    supported = bool(all(gates.values()))
    status = (
        "PASQAL_TWO_ATOM_ZERO_POINT_G4_RANKING_SUPPORTED"
        if supported
        else (
            "ZERO_POINT_G4_RANKING_NOT_SUPPORTED"
            if all_integrity_gates
            else "NUMERICAL_OR_PROTOCOL_INVALID"
        )
    )

    primary_by_name = {row["path"]: row for row in primary_rows}
    performance_by_name = {
        row["path"]: row for row in performance_rows
    }
    combined_rows = []
    for candidate in candidates:
        name = candidate.name
        combined_rows.append(
            {
                "path": name,
                "G2": primary_by_name[name]["G2"],
                "G4": primary_by_name[name]["G4"],
                "G6": primary_by_name[name]["G6"],
                "mean_infidelity": performance_by_name[name][
                    "mean_infidelity"
                ],
                "worst_infidelity": performance_by_name[name][
                    "worst_infidelity"
                ],
                "predicted_rank": predicted_order.index(name) + 1,
                "actual_mean_rank": actual_mean_order.index(name) + 1,
                "actual_worst_rank": actual_worst_order.index(name) + 1,
            }
        )

    script_path = Path(__file__) if "__file__" in globals() else None
    report = {
        "scientific_status": status,
        "claim_boundary": (
            "Success supports an extracted fourth-order zero-point "
            "symmetric-response coefficient as a prospective predictor "
            "inside this matched two-atom fibre. It is not a theorem over "
            "all controls and is not PASQAL Cloud or QPU evidence."
        ),
        "protocol_sha256": protocol_hash,
        "ranking_certificate_sha256": certificate_hash,
        "created_unix_time": time.time(),
        "script_sha256": (
            engine.sha256_file(script_path)
            if script_path is not None and script_path.is_file()
            else None
        ),
        "training_evidence": {
            "role": "FORMULA_SELECTION_ONLY",
            "n_paths": TRAINING_PATHS,
            "G4_spearman": TRAINING_G4_SPEARMAN,
            "G4_plus_G6_spearman": TRAINING_G4_PLUS_G6_SPEARMAN,
            "selection_rule": FORMULA_SELECTION_RULE,
        },
        "validation": {
            "role": "NEW_PROSPECTIVE_CONFIRMATION",
            "n_paths": len(candidates),
            "mean_spearman": mean_rho,
            "mean_spearman_pvalue": float(mean_result.pvalue),
            "worst_spearman_secondary": worst_rho,
            "worst_spearman_pvalue": float(worst_result.pvalue),
            "predicted_order_best_to_worst": predicted_order,
            "actual_mean_order_best_to_worst": actual_mean_order,
            "actual_worst_order_best_to_worst": actual_worst_order,
            "top1_pass": top1_pass,
            "combined_rows": combined_rows,
        },
        "G2_relative_spread": g2_relative_spread,
        "G4_fit_window_rank_stability_spearman": g4_stability_rho,
        "maximum_relative_fit_residual": max_fit_residual,
        "maximum_constraint_residual": max(constraint_residuals),
        "constraint_geometry": constraint_info,
        "generation_attempts": generation_attempts,
        "pre_outcome_error_audit": pre_outcome_audit,
        "held_out_error_audit": held_out_audit,
        "gates": gates,
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 108)
    print("PASQAL TWO-ATOM ZERO-POINT G4 PROSPECTIVE AUDIT")
    print("=" * 108)
    print(
        json.dumps(
            {
                "scientific_status": status,
                "formula": "G4 = mean_axis a4_axis; smaller predicts better",
                "training_paths": TRAINING_PATHS,
                "n_new_prospective_paths": len(candidates),
                "G2_relative_spread": g2_relative_spread,
                "G4_fit_window_rank_stability_spearman": (
                    g4_stability_rho
                ),
                "maximum_relative_fit_residual": max_fit_residual,
                "local_max_error_component": (
                    LOCAL_MAX_ERROR_COMPONENT
                ),
                "held_out_min_nonzero_component": (
                    HELD_OUT_MIN_NONZERO_COMPONENT
                ),
                "prospective_mean_spearman": mean_rho,
                "prospective_mean_spearman_pvalue": float(
                    mean_result.pvalue
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
                "protocol_sha256": protocol_hash,
                "ranking_certificate_sha256": certificate_hash,
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
            "  PASS: the frozen fourth-order zero-point coefficient G4 "
            "prospectively predicts mean finite-error ranking."
        )
    elif all_integrity_gates:
        print(
            "  VALID NEGATIVE RESULT: G4 did not satisfy every "
            "predeclared predictive gate."
        )
    else:
        print(
            "  Protocol/numerical integrity failed; no scientific "
            "interpretation is allowed."
        )


if __name__ == "__main__":
    main()
