#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASQAL L4-formal audit with Arb outward-rounded complex ball arithmetic.

This program verifies finite-error ordering for a serialized-decimal,
finite-dimensional two-atom Hamiltonian model.

* python-flint/Arb complex balls enclose every transcendental, matrix
  exponential, Fourier extraction, coefficient convolution, and comparison.
* A 64-point complex Cauchy-DFT recovers amplitude coefficients through
  order 30. The unrepresented DFT alias is bounded by a Dyson estimate.
* The even infidelity coefficients are convolved inside complex balls.
* The order-30 interval is enlarged by a rigorous analytic order-32 tail.
* All interval rankings are frozen before ordinary held-out evaluation.

Boundary
--------
This is a formal ball-arithmetic certificate conditional on:
  1. the serialized decimal pulse phases and constants used here;
  2. the stated finite-dimensional piecewise Hamiltonian model.

It is not a proof about PASQAL hardware, model discrepancy, or the optimizer's
mathematical equality constraints. The latter remain separately audited to a
declared floating-point tolerance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

try:
    from flint import acb, acb_mat, arb, ctx
except ModuleNotFoundError:
    print("[install] python-flint==0.8.0", flush=True)
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q",
            "python-flint==0.8.0",
        ],
        check=True,
    )
    from flint import acb, acb_mat, arb, ctx

try:
    import pasqal_two_atom_matched_fibre_test as base
    import pasqal_two_atom_q2_prospective_ranking as engine
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Missing companion modules. Use the standalone Colab edition."
    ) from exc


VERSION = "1.0"
VALIDATION_SEED = 20260807
N_PATHS = 12
MAX_GENERATION_ATTEMPTS = 50
JET_ORDER = 30
CAUCHY_POINTS = 64
ARB_PRECISION_BITS = 192
TARGET_T = 1
ALIAS_ENCLOSURE = "1e-40"
TAIL_ENCLOSURE = "2e-11"
G4_PAIR_COVERAGE_GATE = 0.10
ORDER30_PAIR_COVERAGE_GATE = 0.95
CONSTRAINT_RESIDUAL_TOL = 2.0e-7
OUTDIR = Path("pasqal_L4_arb_formal_results")


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
    engine.ERROR_AUDIT.start("constraints_then_arb_zero_point_certificate")
    engine.REFERENCE_STATE, engine.REFERENCE_TANGENTS = (
        engine.local_state_and_tangents(engine.REFERENCE_PHASES)
    )
    vector = np.concatenate(
        [engine.REFERENCE_STATE, *engine.REFERENCE_TANGENTS]
    )
    engine.REFERENCE_FEATURE = np.r_[vector.real, vector.imag]


def A(value: int | str) -> arb:
    return arb(str(value))


def zero_acb_ball(radius: str) -> acb:
    interval = arb(f"0 +/- {radius}")
    return acb(interval, interval)


def zero_arb_ball(radius: str | arb) -> arb:
    return arb(0, radius)


def basis_matrices() -> tuple[list[list[complex]], ...]:
    gx = [
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [1, 0, 0, 1],
        [0, 1, 1, 0],
    ]
    gy = [
        [0, -1j, -1j, 0],
        [1j, 0, 0, -1j],
        [1j, 0, 0, -1j],
        [0, 1j, 1j, 0],
    ]
    total_number = [
        [0, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 2],
    ]
    double = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 1],
    ]
    return gx, gy, total_number, double


GX, GY, TOTAL_NUMBER, DOUBLE = basis_matrices()


def C(value: complex | int | float) -> acb:
    value = complex(value)
    return acb(A(repr(value.real)), A(repr(value.imag)))


def hamiltonian_pair(
    phase_decimal: str,
    axis: int,
) -> tuple[acb_mat, acb_mat]:
    dimension = 4
    pi = arb.pi()
    omega = 2 * pi
    interaction = 4 * omega
    phase = A(phase_decimal)
    cosine, sine = phase.cos(), phase.sin()
    h0 = acb_mat(dimension, dimension)
    h1 = acb_mat(dimension, dimension)
    amplitude_scale = A(3) / A(50)
    detuning_scale = A(1) / A(25)
    interaction_scale = A(1) / A(20)

    for row in range(dimension):
        for column in range(dimension):
            drive_axis = (
                cosine * C(GX[row][column])
                + sine * C(GY[row][column])
            )
            h0[row, column] = omega * drive_axis / 2
            h0[row, column] += (
                interaction * C(DOUBLE[row][column])
            )
            if axis == 0:
                h1[row, column] = (
                    omega * amplitude_scale * drive_axis / 2
                )
            elif axis == 1:
                h1[row, column] = (
                    -omega
                    * detuning_scale
                    * C(TOTAL_NUMBER[row][column])
                )
            else:
                h1[row, column] = (
                    interaction
                    * interaction_scale
                    * C(DOUBLE[row][column])
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


def amplitude_coefficients(
    candidate: engine.Candidate,
    axis: int,
    reference_target: acb_mat,
) -> list[acb]:
    phase_decimals = [repr(float(value)) for value in candidate.phases]
    hamiltonians = [
        hamiltonian_pair(phase, axis) for phase in phase_decimals
    ]
    target_bra = reference_target.conjugate().transpose()
    roots: list[acb] = []
    samples: list[acb] = []
    pi = arb.pi()
    for index in range(CAUCHY_POINTS):
        angle = 2 * pi * index / CAUCHY_POINTS
        root = acb(angle.cos(), angle.sin())
        roots.append(root)
        state = propagate(hamiltonians, root)
        samples.append((target_bra * state)[0, 0])

    alias_ball = zero_acb_ball(ALIAS_ENCLOSURE)
    coefficients = []
    for order in range(JET_ORDER + 1):
        coefficient = acb(0)
        for root, sample in zip(roots, samples):
            coefficient += sample * root ** (-order)
        coefficient /= CAUCHY_POINTS
        coefficients.append(coefficient + alias_ball)
    return coefficients


def infidelity_coefficients(
    amplitude: list[acb],
) -> list[arb]:
    values = []
    for order in range(JET_ORDER + 1):
        fidelity = acb(0)
        for left in range(order + 1):
            fidelity += (
                amplitude[left].conjugate() * amplitude[order-left]
            )
        infidelity = -fidelity
        if order == 0:
            infidelity += 1
        if not infidelity.imag.contains(0):
            raise RuntimeError(
                f"Infidelity coefficient {order} has nonzero imaginary ball."
            )
        values.append(infidelity.real)
    return values


def mean_even_jet(
    candidate: engine.Candidate,
    reference_target: acb_mat,
) -> dict:
    axis_coefficients = [
        infidelity_coefficients(
            amplitude_coefficients(candidate, axis, reference_target)
        )
        for axis in range(3)
    ]
    even: dict[int, arb] = {}
    for order in range(0, JET_ORDER + 1, 2):
        even[order] = sum(
            axis_coefficients[axis][order] for axis in range(3)
        ) / 3
    return {
        "path": candidate.name,
        "even": even,
        "C0": even[0],
        "C2": even[2],
        "G4": even[4],
        "higher": sum(
            even[order] for order in range(6, JET_ORDER + 1, 2)
        ),
        "order30": sum(even.values()),
    }


def rigorous_dyson_checks() -> dict:
    pi = arb.pi()
    K = [
        A(36) * pi / A(125),
        A(48) * pi / A(125),
        A(24) * pi / A(25),
    ]
    alias_limit = A(ALIAS_ENCLOSURE)
    alias_upper_bounds = [
        value.exp() * value**CAUCHY_POINTS
        / math.factorial(CAUCHY_POINTS)
        for value in K
    ]
    alias_pass = all(
        bound < alias_limit for bound in alias_upper_bounds
    )

    tail_limit = A(TAIL_ENCLOSURE)
    axis_tails = []
    for value in K:
        x = 2 * value
        order = JET_ORDER + 2
        term = x**order / math.factorial(order)
        tail = term
        while order < 160:
            order += 2
            term *= x*x / (order * (order - 1))
            tail += term
        axis_tails.append(tail)
    mean_tail = sum(axis_tails) / 3
    tail_pass = mean_tail < tail_limit
    return {
        "K": K,
        "alias_upper_bounds": alias_upper_bounds,
        "alias_pass": alias_pass,
        "axis_tails": axis_tails,
        "mean_tail": mean_tail,
        "tail_pass": tail_pass,
    }


def radius_for_correction(correction: arb) -> arb:
    absolute = abs(correction)
    upper = absolute.upper()
    # Add the already-proved order-32 tail enclosure.
    radius = upper + A(TAIL_ENCLOSURE)
    return radius.upper()


def interval_records(
    rows: list[dict],
) -> tuple[dict[str, arb], dict[str, arb]]:
    common_C0 = sum(row["C0"] for row in rows) / len(rows)
    common_C2 = sum(row["C2"] for row in rows) / len(rows)
    tail_ball = zero_arb_ball(TAIL_ENCLOSURE)
    G4_intervals: dict[str, arb] = {}
    order30_intervals: dict[str, arb] = {}
    for row in rows:
        correction = (
            row["C0"] - common_C0
            + row["C2"] - common_C2
            + row["higher"]
        )
        correction_ball = zero_arb_ball(
            radius_for_correction(correction)
        )
        G4_intervals[row["path"]] = (
            common_C0 + common_C2 + row["G4"] + correction_ball
        )
        order30_intervals[row["path"]] = (
            row["order30"] + tail_ball
        )
    return G4_intervals, order30_intervals


def certify_pairs(
    intervals: dict[str, arb],
) -> list[dict]:
    names = list(intervals)
    rows = []
    for left in range(len(names)):
        for right in range(left + 1, len(names)):
            first, second = names[left], names[right]
            first_interval = intervals[first]
            second_interval = intervals[second]
            if first_interval.upper() < second_interval.lower():
                rows.append({"better": first, "worse": second})
            elif second_interval.upper() < first_interval.lower():
                rows.append({"better": second, "worse": first})
    return rows


def ball_record(value: arb) -> dict:
    return {
        "ball": str(value),
        "lower": str(value.lower()),
        "upper": str(value.upper()),
    }


def main() -> None:
    ctx.prec = ARB_PRECISION_BITS
    ctx.threads = 1
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTDIR)
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"[notice] ignored notebook arguments: {unknown}")
    output_directory = args.output_dir
    output_directory.mkdir(parents=True, exist_ok=True)

    protocol = {
        "title": "PASQAL L4 formal Arb ball certificate",
        "version": VERSION,
        "validation_seed": VALIDATION_SEED,
        "n_new_paths": N_PATHS,
        "jet_order": JET_ORDER,
        "cauchy_points": CAUCHY_POINTS,
        "arb_precision_bits": ARB_PRECISION_BITS,
        "alias_enclosure": ALIAS_ENCLOSURE,
        "tail_enclosure": TAIL_ENCLOSURE,
        "G4_pair_coverage_gate": G4_PAIR_COVERAGE_GATE,
        "order30_pair_coverage_gate": ORDER30_PAIR_COVERAGE_GATE,
        "formal_interval_arithmetic": True,
        "infidelity_target": (
            "single common Arb-propagated reference-path nominal state"
        ),
        "model_boundary": (
            "serialized decimal pulse phases and constants in the stated "
            "finite-dimensional piecewise two-atom Hamiltonian"
        ),
        "outcomes_used_before_certificate": False,
    }
    protocol_hash = sha256_json(protocol)
    (output_directory / "protocol.json").write_text(
        json.dumps(protocol, indent=2), encoding="utf-8"
    )

    initialize_engine()
    _, _, null_basis, constraint_information = (
        engine.constraint_geometry()
    )
    candidates, attempts = engine.generate_validation_candidates(null_basis)
    constraint_residuals = {
        candidate.name: float(
            np.linalg.norm(engine.matched_residual(candidate.phases))
        )
        for candidate in candidates
    }

    dyson = rigorous_dyson_checks()
    if not dyson["alias_pass"]:
        raise RuntimeError("The formal Cauchy alias enclosure failed.")
    if not dyson["tail_pass"]:
        raise RuntimeError("The formal order-32 tail enclosure failed.")

    print(
        f"[arb] computing {N_PATHS} paths × 3 axes × "
        f"{CAUCHY_POINTS} circle points at {ARB_PRECISION_BITS} bits...",
        flush=True,
    )
    reference_hamiltonians = [
        hamiltonian_pair(repr(float(phase)), 0)
        for phase in engine.REFERENCE_PHASES
    ]
    reference_target = propagate(reference_hamiltonians, acb(0))
    jet_rows = [
        mean_even_jet(candidate, reference_target)
        for candidate in candidates
    ]
    G4_intervals, order30_intervals = interval_records(jet_rows)
    G4_pairs = certify_pairs(G4_intervals)
    order30_pairs = certify_pairs(order30_intervals)
    possible_pairs = N_PATHS * (N_PATHS - 1) // 2
    G4_coverage = len(G4_pairs) / possible_pairs
    order30_coverage = len(order30_pairs) / possible_pairs

    certificate = {
        "protocol_sha256": protocol_hash,
        "created_unix_time": time.time(),
        "outcomes_unlocked": False,
        "formal_interval_arithmetic": True,
        "arb_version": getattr(sys.modules.get("flint"), "__version__", None),
        "dyson_checks": {
            "K": [str(value) for value in dyson["K"]],
            "alias_upper_bounds": [
                str(value) for value in dyson["alias_upper_bounds"]
            ],
            "alias_pass": dyson["alias_pass"],
            "axis_tails": [
                str(value) for value in dyson["axis_tails"]
            ],
            "mean_tail": str(dyson["mean_tail"]),
            "tail_pass": dyson["tail_pass"],
        },
        "G4_intervals": {
            name: ball_record(value)
            for name, value in G4_intervals.items()
        },
        "order30_intervals": {
            name: ball_record(value)
            for name, value in order30_intervals.items()
        },
        "G4_certified_pairs": G4_pairs,
        "order30_certified_pairs": order30_pairs,
        "candidate_phases_decimal": {
            candidate.name: [
                repr(float(value)) for value in candidate.phases
            ]
            for candidate in candidates
        },
        "constraint_residuals": constraint_residuals,
    }
    certificate_hash = sha256_json(certificate)
    certificate_path = output_directory / "formal_certificate.json"
    certificate_path.write_text(
        json.dumps(certificate, indent=2), encoding="utf-8"
    )
    with certificate_path.open("rb") as stream:
        stream.flush()

    engine.OUTCOMES_UNLOCKED = True
    performance = [
        engine.held_out_performance(candidate) for candidate in candidates
    ]
    actual = {
        row["path"]: row["mean_infidelity"] for row in performance
    }
    G4_correct = all(
        actual[row["better"]] < actual[row["worse"]]
        for row in G4_pairs
    )
    order30_correct = all(
        actual[row["better"]] < actual[row["worse"]]
        for row in order30_pairs
    )
    actual_inside_order30 = all(
        order30_intervals[name].contains(actual[name])
        for name in actual
    )

    gates = {
        "formal_interval_arithmetic": True,
        "formal_alias_bound": dyson["alias_pass"],
        "formal_order32_tail_bound": dyson["tail_pass"],
        "constraints_within_declared_float_tolerance": (
            max(constraint_residuals.values())
            <= CONSTRAINT_RESIDUAL_TOL
        ),
        "G4_pair_coverage": G4_coverage >= G4_PAIR_COVERAGE_GATE,
        "G4_certified_pairs_correct": G4_correct,
        "order30_pair_coverage": (
            order30_coverage >= ORDER30_PAIR_COVERAGE_GATE
        ),
        "order30_certified_pairs_correct": order30_correct,
        "ordinary_outcomes_inside_formal_intervals": (
            actual_inside_order30
        ),
    }
    formal_order30_supported = all(gates.values())
    status = (
        "L4_FORMAL_ARB_ORDER30_CERTIFICATE_SUPPORTED"
        if formal_order30_supported
        else "L4_FORMAL_ARB_CERTIFICATE_NOT_SUPPORTED"
    )
    report = {
        "scientific_status": status,
        "claim_boundary": (
            "Formal for the serialized-decimal finite Hamiltonian model. "
            "Not PASQAL hardware evidence and not a formal proof that the "
            "optimizer constraints are exactly equal."
        ),
        "protocol_sha256": protocol_hash,
        "formal_certificate_sha256": certificate_hash,
        "gates": gates,
        "G4_certified_pairs": len(G4_pairs),
        "G4_pair_coverage": G4_coverage,
        "order30_certified_pairs": len(order30_pairs),
        "order30_pair_coverage": order30_coverage,
        "possible_pairs": possible_pairs,
        "maximum_float_constraint_residual": max(
            constraint_residuals.values()
        ),
        "generation_attempts": attempts,
    }
    (output_directory / "report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    print("=" * 112)
    print("PASQAL TWO-ATOM L4 FORMAL ARB BALL-CERTIFICATE AUDIT")
    print("=" * 112)
    print(
        json.dumps(
            {
                "scientific_status": status,
                "formal_interval_arithmetic": True,
                "arb_precision_bits": ARB_PRECISION_BITS,
                "cauchy_points": CAUCHY_POINTS,
                "jet_order": JET_ORDER,
                "formal_alias_bound_pass": dyson["alias_pass"],
                "formal_order32_tail_bound_pass": dyson["tail_pass"],
                "G4_certified_pairs": len(G4_pairs),
                "G4_possible_pairs": possible_pairs,
                "G4_pair_coverage": G4_coverage,
                "G4_certified_pairs_correct": G4_correct,
                "order30_certified_pairs": len(order30_pairs),
                "order30_pair_coverage": order30_coverage,
                "order30_certified_pairs_correct": order30_correct,
                "ordinary_outcomes_inside_formal_intervals": (
                    actual_inside_order30
                ),
                "protocol_sha256": protocol_hash,
                "formal_certificate_sha256": certificate_hash,
                "output_directory": str(output_directory),
            },
            indent=2,
        )
    )
    print("\nInterpretation")
    if formal_order30_supported:
        print(
            "  FORMAL MODEL-CERTIFICATE PASS: outward-rounded Arb balls "
            "plus analytic alias and tail enclosures certify the required "
            "finite-error path ordering for the serialized model."
        )
    else:
        print(
            "  The formal Arb certificate did not pass every gate."
        )
    print(
        "  This does not certify PASQAL hardware or exact optimizer "
        "constraint identities."
    )


if __name__ == "__main__":
    main()
