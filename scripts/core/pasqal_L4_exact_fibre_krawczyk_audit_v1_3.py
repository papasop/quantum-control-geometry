#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASQAL two-atom exact matched-fibre Krawczyk audit.

Purpose
-------
Close the missing step between a numerically matched implementation fibre and
the existing formal finite-error ordering certificate.

For each frozen two-atom phase schedule this program:

1. works in the exchange-symmetric three-state subspace;
2. represents the nominal state by two complex projective coordinates;
3. represents each of the three exact first-error derivatives by the
   derivative of those two projective coordinates;
4. obtains a 16-real-component analytic constraint map;
5. selects 16 transverse control directions from the numerical SVD;
6. evaluates the constraint Jacobian on a phase box with outward-rounded
   Arb/ACB arithmetic; and
7. tests the Krawczyk inclusion K(X) subset int(X).

The error derivatives are Frechet derivatives of the segment matrix
exponentials, not finite differences.  The phase Jacobian is also enclosed
analytically, including mixed phase/error derivatives.

Claim boundary
--------------
PASS proves existence and local uniqueness of a zero of the declared
16-dimensional projective state-and-response constraint map in the reported
transverse box, with the eight numerical fibre coordinates fixed.

It does not prove:
* PASQAL hardware behaviour;
* global uniqueness of a control;
* an exact eight-dimensional fibre without an additional parameter-family
  argument;
* finite-error ordering after phase uncertainty is propagated through the
  order-30 certificate.

Required companion modules
--------------------------
    pasqal_two_atom_matched_fibre_test.py
    pasqal_two_atom_q2_prospective_ranking.py

Use the generated standalone Colab edition when companion files are
inconvenient.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import expm, expm_frechet, svd
from scipy.optimize import least_squares

try:
    import pasqal_two_atom_matched_fibre_test as base
    import pasqal_two_atom_q2_prospective_ranking as engine
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Missing companion modules. Use the standalone Colab edition."
    ) from exc


VERSION = "1.3"
VALIDATION_SEED = 20260807
N_PATHS = 12
MAX_GENERATION_ATTEMPTS = 50
TRANSVERSE_DIMENSION = 16
NUMERICAL_JACOBIAN_STEP = 2.0e-6
NUMERICAL_RANK_CUTOFF = 1.0e-7
ARB_PRECISION_BITS = 192
DEFAULT_BOX_RADIUS = 3.0e-12
DEFAULT_COHORT = Path("pasqal_L4_exact_fibre_cohort_v1_3.json")
OUTDIR = Path("pasqal_L4_exact_fibre_krawczyk_v1_3_results")


@dataclass(frozen=True)
class NumericalChart:
    name: str
    phases: np.ndarray
    source_phase_correction_inf_norm: float
    correction_optimizer_success: bool
    transverse_basis: np.ndarray
    jacobian: np.ndarray
    inverse: np.ndarray
    singular_values: np.ndarray
    residual: np.ndarray


def canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def initialize_engine() -> None:
    engine.VALIDATION_SEED = VALIDATION_SEED
    engine.N_VALIDATION_PATHS = N_PATHS
    engine.MAX_GENERATION_ATTEMPTS = MAX_GENERATION_ATTEMPTS
    engine.OUTCOMES_UNLOCKED = False
    engine.ERROR_AUDIT.start("exact_fibre_constraints_only")
    engine.REFERENCE_STATE, engine.REFERENCE_TANGENTS = (
        engine.local_state_and_tangents(engine.REFERENCE_PHASES)
    )
    vector = np.concatenate(
        [engine.REFERENCE_STATE, *engine.REFERENCE_TANGENTS]
    )
    engine.REFERENCE_FEATURE = np.r_[vector.real, vector.imag]


def numeric_generators(phase: float) -> tuple[np.ndarray, list[np.ndarray],
                                               np.ndarray, list[np.ndarray]]:
    """Return A, error directions E_a, phase direction P, and mixed Q_a."""

    c, s = math.cos(phase), math.sin(phase)
    drive_axis = c * base.GLOBAL_X + s * base.GLOBAL_Y
    phase_axis = -s * base.GLOBAL_X + c * base.GLOBAL_Y
    h0 = (
        0.5 * base.OMEGA_RAD_PER_US * drive_axis
        + base.NOMINAL_INTERACTION_RAD_PER_US * base.DOUBLE_RYDBERG
    )
    h_error = [
        0.5 * base.OMEGA_RAD_PER_US * drive_axis,
        -base.OMEGA_RAD_PER_US * base.TOTAL_NUMBER,
        base.NOMINAL_INTERACTION_RAD_PER_US * base.DOUBLE_RYDBERG,
    ]
    h_phase = 0.5 * base.OMEGA_RAD_PER_US * phase_axis
    h_mixed = [
        0.5 * base.OMEGA_RAD_PER_US * phase_axis,
        np.zeros((4, 4), dtype=complex),
        np.zeros((4, 4), dtype=complex),
    ]
    scale = -1.0j * base.SEGMENT_DURATION_US
    return (
        scale * h0,
        [scale * value for value in h_error],
        scale * h_phase,
        [scale * value for value in h_mixed],
    )


def numeric_segment_jets(
    phase: float,
) -> tuple[np.ndarray, list[np.ndarray], np.ndarray, list[np.ndarray]]:
    """Segment propagator, error derivatives, phase derivative, mixed terms."""

    a, errors, phase_direction, mixed_directions = numeric_generators(phase)
    unitary = expm(a)
    phase_derivative = expm_frechet(
        a, phase_direction, compute_expm=False
    )
    error_derivatives = [
        expm_frechet(a, direction, compute_expm=False)
        for direction in errors
    ]

    mixed = []
    for error_direction, direct_mixed in zip(errors, mixed_directions):
        first = np.zeros((12, 12), dtype=complex)
        second = np.zeros((12, 12), dtype=complex)
        for block in range(3):
            sl = slice(4 * block, 4 * (block + 1))
            first[sl, sl] = a
            second[sl, sl] = a
        first[0:4, 4:8] = phase_direction
        first[4:8, 8:12] = error_direction
        first[0:4, 8:12] = direct_mixed
        second[0:4, 4:8] = error_direction
        second[4:8, 8:12] = phase_direction
        first_exp = expm(first)
        second_exp = expm(second)
        mixed.append(first_exp[0:4, 8:12] + second_exp[0:4, 8:12])
    return unitary, error_derivatives, phase_derivative, mixed


def numeric_state_jets(
    phases: np.ndarray,
    need_phase_jacobian: bool,
) -> tuple[np.ndarray, list[np.ndarray], list[np.ndarray] | None,
           list[list[np.ndarray]] | None]:
    """Propagate the state, exact error derivatives, and optional phase jets."""

    state = base.GG.copy()
    error_states = [np.zeros(4, dtype=complex) for _ in range(3)]
    phase_states = (
        [np.zeros(4, dtype=complex) for _ in range(base.N_SEGMENTS)]
        if need_phase_jacobian else None
    )
    mixed_states = (
        [
            [np.zeros(4, dtype=complex) for _ in range(base.N_SEGMENTS)]
            for _ in range(3)
        ]
        if need_phase_jacobian else None
    )

    for segment, phase in enumerate(phases):
        unitary, error_u, phase_u, mixed_u = numeric_segment_jets(float(phase))
        old_state = state
        old_error = [value.copy() for value in error_states]
        old_phase = (
            [value.copy() for value in phase_states]
            if phase_states is not None else None
        )
        old_mixed = (
            [[value.copy() for value in row] for row in mixed_states]
            if mixed_states is not None else None
        )

        state = unitary @ old_state
        for axis in range(3):
            error_states[axis] = (
                unitary @ old_error[axis] + error_u[axis] @ old_state
            )

        if phase_states is not None and mixed_states is not None:
            for index in range(segment):
                phase_states[index] = unitary @ old_phase[index]
                for axis in range(3):
                    mixed_states[axis][index] = (
                        unitary @ old_mixed[axis][index]
                        + error_u[axis] @ old_phase[index]
                    )
            phase_states[segment] = phase_u @ old_state
            for axis in range(3):
                mixed_states[axis][segment] = (
                    phase_u @ old_error[axis] + mixed_u[axis] @ old_state
                )

    return state, error_states, phase_states, mixed_states


def symmetric_components_numeric(vector: np.ndarray) -> np.ndarray:
    return np.array(
        [vector[0], (vector[1] + vector[2]) / math.sqrt(2.0), vector[3]],
        dtype=complex,
    )


def projective_feature_numeric(
    phases: np.ndarray,
    need_jacobian: bool = False,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Return 16 real projective constraints and their 16x24 phase Jacobian."""

    state, errors, phase_states, mixed_states = numeric_state_jets(
        phases, need_jacobian
    )
    psi = symmetric_components_numeric(state)
    error_vectors = [symmetric_components_numeric(value) for value in errors]
    denominator = psi[0]
    if abs(denominator) < 0.25:
        raise RuntimeError("Projective chart denominator is too small.")

    complex_feature: list[complex] = [psi[1] / denominator, psi[2] / denominator]
    numerators: list[list[complex]] = []
    for error in error_vectors:
        row = []
        for component in (1, 2):
            numerator = (
                error[component] * denominator
                - psi[component] * error[0]
            )
            row.append(numerator)
            complex_feature.append(numerator / denominator**2)
        numerators.append(row)

    feature = np.empty(16, dtype=float)
    for index, value in enumerate(complex_feature):
        feature[2 * index] = float(value.real)
        feature[2 * index + 1] = float(value.imag)

    if not need_jacobian:
        return feature, None

    assert phase_states is not None and mixed_states is not None
    jacobian = np.zeros((16, base.N_SEGMENTS), dtype=float)
    for phase_index in range(base.N_SEGMENTS):
        phase_vector = symmetric_components_numeric(phase_states[phase_index])
        mixed_vectors = [
            symmetric_components_numeric(mixed_states[axis][phase_index])
            for axis in range(3)
        ]
        derivative_values: list[complex] = []
        for component in (1, 2):
            derivative_values.append(
                (
                    phase_vector[component] * denominator
                    - psi[component] * phase_vector[0]
                )
                / denominator**2
            )
        for axis, (error, mixed_vector) in enumerate(
            zip(error_vectors, mixed_vectors)
        ):
            for local_component, component in enumerate((1, 2)):
                numerator = numerators[axis][local_component]
                numerator_derivative = (
                    mixed_vector[component] * denominator
                    + error[component] * phase_vector[0]
                    - phase_vector[component] * error[0]
                    - psi[component] * mixed_vector[0]
                )
                derivative_values.append(
                    numerator_derivative / denominator**2
                    - 2.0
                    * numerator
                    * phase_vector[0]
                    / denominator**3
                )
        for value_index, value in enumerate(derivative_values):
            jacobian[2 * value_index, phase_index] = float(value.real)
            jacobian[2 * value_index + 1, phase_index] = float(value.imag)
    return feature, jacobian


def numerical_chart(
    name: str,
    phases: np.ndarray,
    reference_feature: np.ndarray,
) -> NumericalChart:
    feature, full_jacobian = projective_feature_numeric(
        phases, need_jacobian=True
    )
    assert full_jacobian is not None
    _, singular_values, vh = svd(full_jacobian, full_matrices=True)
    rank = int(np.sum(singular_values > NUMERICAL_RANK_CUTOFF))
    if rank != TRANSVERSE_DIMENSION:
        raise RuntimeError(
            f"{name}: numerical exact-response Jacobian rank {rank}, "
            f"expected {TRANSVERSE_DIMENSION}."
        )
    initial_transverse = vh[:TRANSVERSE_DIMENSION].T

    def reduced_residual(coordinates: np.ndarray) -> np.ndarray:
        trial = phases + initial_transverse @ coordinates
        value, _ = projective_feature_numeric(trial, need_jacobian=False)
        return value - reference_feature

    def reduced_jacobian(coordinates: np.ndarray) -> np.ndarray:
        trial = phases + initial_transverse @ coordinates
        _, value = projective_feature_numeric(trial, need_jacobian=True)
        assert value is not None
        return value @ initial_transverse

    correction = least_squares(
        reduced_residual,
        np.zeros(TRANSVERSE_DIMENSION),
        jac=reduced_jacobian,
        method="lm",
        max_nfev=100,
        ftol=1.0e-14,
        xtol=1.0e-14,
        gtol=1.0e-14,
    )
    corrected_phases = phases + initial_transverse @ correction.x
    corrected_feature, corrected_full_jacobian = projective_feature_numeric(
        corrected_phases, need_jacobian=True
    )
    assert corrected_full_jacobian is not None
    _, corrected_singular_values, corrected_vh = svd(
        corrected_full_jacobian, full_matrices=True
    )
    corrected_rank = int(
        np.sum(corrected_singular_values > NUMERICAL_RANK_CUTOFF)
    )
    if corrected_rank != TRANSVERSE_DIMENSION:
        raise RuntimeError(
            f"{name}: corrected exact-response Jacobian rank "
            f"{corrected_rank}, expected {TRANSVERSE_DIMENSION}."
        )
    transverse = corrected_vh[:TRANSVERSE_DIMENSION].T
    square_jacobian = corrected_full_jacobian @ transverse
    inverse = np.linalg.inv(square_jacobian)
    return NumericalChart(
        name=name,
        phases=corrected_phases,
        source_phase_correction_inf_norm=float(
            np.max(np.abs(initial_transverse @ correction.x))
        ),
        correction_optimizer_success=bool(correction.success),
        transverse_basis=transverse,
        jacobian=square_jacobian,
        inverse=inverse,
        singular_values=corrected_singular_values,
        residual=corrected_feature - reference_feature,
    )


def frozen_chart(
    entry: dict[str, Any],
    reference_feature: np.ndarray,
) -> NumericalChart:
    """Reconstruct a chart from proof inputs without running an optimizer.

    The phases, transverse basis, and point preconditioner are serialized as
    decimal strings in the frozen cohort. Numerical recomputation below is
    diagnostic only; the formal Krawczyk map uses the frozen proof inputs.
    """

    name = str(entry["path"])
    phases = np.asarray(entry["phases_decimal"], dtype=float)
    transverse = np.asarray(entry["transverse_basis_decimal"], dtype=float)
    inverse = np.asarray(entry["point_preconditioner_decimal"], dtype=float)
    if phases.shape != (base.N_SEGMENTS,):
        raise RuntimeError(f"{name}: frozen phase vector must have length 24.")
    if transverse.shape != (base.N_SEGMENTS, TRANSVERSE_DIMENSION):
        raise RuntimeError(f"{name}: frozen transverse basis must be 24x16.")
    if inverse.shape != (TRANSVERSE_DIMENSION, TRANSVERSE_DIMENSION):
        raise RuntimeError(f"{name}: frozen point preconditioner must be 16x16.")

    feature, full_jacobian = projective_feature_numeric(
        phases, need_jacobian=True
    )
    assert full_jacobian is not None
    singular_values = svd(full_jacobian, compute_uv=False)
    rank = int(np.sum(singular_values > NUMERICAL_RANK_CUTOFF))
    if rank != TRANSVERSE_DIMENSION:
        raise RuntimeError(
            f"{name}: frozen chart numerical rank {rank}, "
            f"expected {TRANSVERSE_DIMENSION}."
        )
    square_jacobian = full_jacobian @ transverse
    return NumericalChart(
        name=name,
        phases=phases,
        source_phase_correction_inf_norm=0.0,
        correction_optimizer_success=True,
        transverse_basis=transverse,
        jacobian=square_jacobian,
        inverse=inverse,
        singular_values=singular_values,
        residual=feature - reference_feature,
    )


def require_flint() -> tuple[Any, Any, Any, Any]:
    try:
        from flint import acb, acb_mat, arb, ctx
    except ModuleNotFoundError:
        print("[install] python-flint==0.8.0", flush=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "python-flint==0.8.0",
            ],
            check=True,
        )
        from flint import acb, acb_mat, arb, ctx
    return acb, acb_mat, arb, ctx


ACB: Any = None
ACB_MAT: Any = None
ARB: Any = None


def ar(value: float | int | str) -> Any:
    return ARB(str(value))


def ac(value: complex | float | int) -> Any:
    value = complex(value)
    return ACB(ar(repr(value.real)), ar(repr(value.imag)))


def acb_zero_matrix(rows: int, columns: int) -> Any:
    return ACB_MAT(rows, columns)


def acb_eye(size: int) -> Any:
    result = acb_zero_matrix(size, size)
    for index in range(size):
        result[index, index] = 1
    return result


def acb_block(matrix: Any, row_block: int, column_block: int) -> Any:
    result = acb_zero_matrix(4, 4)
    for row in range(4):
        for column in range(4):
            result[row, column] = matrix[
                4 * row_block + row, 4 * column_block + column
            ]
    return result


def set_acb_block(matrix: Any, row_block: int, column_block: int, value: Any) -> None:
    for row in range(4):
        for column in range(4):
            matrix[
                4 * row_block + row, 4 * column_block + column
            ] = value[row, column]


def formal_generators(phase: Any) -> tuple[Any, list[Any], Any, list[Any]]:
    """Ball enclosures of A, E_a, P, and Q_a for one segment."""

    gx = base.GLOBAL_X
    gy = base.GLOBAL_Y
    total_number = base.TOTAL_NUMBER
    double = base.DOUBLE_RYDBERG
    pi = ARB.pi()
    omega = 2 * pi
    interaction = 4 * omega
    cosine, sine = phase.cos(), phase.sin()
    tau = ar("0.1")
    minus_i_tau = -ACB(0, 1) * tau

    h0 = acb_zero_matrix(4, 4)
    h_errors = [acb_zero_matrix(4, 4) for _ in range(3)]
    h_phase = acb_zero_matrix(4, 4)
    h_mixed = [acb_zero_matrix(4, 4) for _ in range(3)]

    for row in range(4):
        for column in range(4):
            x = ac(gx[row, column])
            y = ac(gy[row, column])
            n = ac(total_number[row, column])
            rr = ac(double[row, column])
            drive = cosine * x + sine * y
            phase_drive = -sine * x + cosine * y
            h0[row, column] = omega * drive / 2 + interaction * rr
            h_errors[0][row, column] = omega * drive / 2
            h_errors[1][row, column] = -omega * n
            h_errors[2][row, column] = interaction * rr
            h_phase[row, column] = omega * phase_drive / 2
            h_mixed[0][row, column] = omega * phase_drive / 2

    return (
        minus_i_tau * h0,
        [minus_i_tau * value for value in h_errors],
        minus_i_tau * h_phase,
        [minus_i_tau * value for value in h_mixed],
    )


def formal_frechet(a: Any, direction: Any) -> Any:
    block = acb_zero_matrix(8, 8)
    set_acb_block(block, 0, 0, a)
    set_acb_block(block, 1, 1, a)
    set_acb_block(block, 0, 1, direction)
    return acb_block(block.exp(), 0, 1)


def formal_ordered_second(
    a: Any,
    first_direction: Any,
    second_direction: Any,
    direct_mixed: Any,
) -> Any:
    block = acb_zero_matrix(12, 12)
    for index in range(3):
        set_acb_block(block, index, index, a)
    set_acb_block(block, 0, 1, first_direction)
    set_acb_block(block, 1, 2, second_direction)
    set_acb_block(block, 0, 2, direct_mixed)
    return acb_block(block.exp(), 0, 2)


def formal_segment_jets(
    phase: Any,
) -> tuple[Any, list[Any], Any, list[Any]]:
    a, errors, phase_direction, mixed_directions = formal_generators(phase)
    unitary = a.exp()
    phase_derivative = formal_frechet(a, phase_direction)
    error_derivatives = [formal_frechet(a, value) for value in errors]
    zero = acb_zero_matrix(4, 4)
    mixed = []
    for error_direction, direct_mixed in zip(errors, mixed_directions):
        mixed.append(
            formal_ordered_second(
                a, phase_direction, error_direction, direct_mixed
            )
            + formal_ordered_second(
                a, error_direction, phase_direction, zero
            )
        )
    return unitary, error_derivatives, phase_derivative, mixed


def zero_state() -> Any:
    return ACB_MAT([[0], [0], [0], [0]])


def formal_state_jets(
    phases: list[Any],
) -> tuple[Any, list[Any], list[Any], list[list[Any]]]:
    state = ACB_MAT([[1], [0], [0], [0]])
    error_states = [zero_state() for _ in range(3)]
    phase_states = [zero_state() for _ in range(base.N_SEGMENTS)]
    mixed_states = [
        [zero_state() for _ in range(base.N_SEGMENTS)] for _ in range(3)
    ]

    for segment, phase in enumerate(phases):
        unitary, error_u, phase_u, mixed_u = formal_segment_jets(phase)
        old_state = state
        old_error = list(error_states)
        old_phase = list(phase_states)
        old_mixed = [list(row) for row in mixed_states]

        state = unitary * old_state
        for axis in range(3):
            error_states[axis] = (
                unitary * old_error[axis] + error_u[axis] * old_state
            )
        for index in range(segment):
            phase_states[index] = unitary * old_phase[index]
            for axis in range(3):
                mixed_states[axis][index] = (
                    unitary * old_mixed[axis][index]
                    + error_u[axis] * old_phase[index]
                )
        phase_states[segment] = phase_u * old_state
        for axis in range(3):
            mixed_states[axis][segment] = (
                phase_u * old_error[axis] + mixed_u[axis] * old_state
            )
    return state, error_states, phase_states, mixed_states


def symmetric_components_formal(vector: Any) -> list[Any]:
    root_two = ARB(2).sqrt()
    return [
        vector[0, 0],
        (vector[1, 0] + vector[2, 0]) / root_two,
        vector[3, 0],
    ]


def projective_feature_formal(
    phases: list[Any],
) -> tuple[list[Any], list[list[Any]]]:
    """Return 16 Arb constraints and an Arb 16x24 phase Jacobian."""

    state, errors, phase_states, mixed_states = formal_state_jets(phases)
    psi = symmetric_components_formal(state)
    error_vectors = [symmetric_components_formal(value) for value in errors]
    denominator = psi[0]
    if not (abs(denominator).lower() > 0):
        raise RuntimeError(
            "Projective denominator ball contains zero after interval "
            f"propagation: denominator={denominator}, "
            f"abs_lower={abs(denominator).lower()}. "
            "This is an interval-wrapping failure, not a physical zero."
        )

    complex_feature = [psi[1] / denominator, psi[2] / denominator]
    numerators: list[list[Any]] = []
    for error in error_vectors:
        row = []
        for component in (1, 2):
            numerator = (
                error[component] * denominator
                - psi[component] * error[0]
            )
            row.append(numerator)
            complex_feature.append(numerator / denominator**2)
        numerators.append(row)

    feature: list[Any] = []
    for value in complex_feature:
        feature.extend([value.real, value.imag])

    jacobian = [
        [ARB(0) for _ in range(base.N_SEGMENTS)] for _ in range(16)
    ]
    for phase_index in range(base.N_SEGMENTS):
        phase_vector = symmetric_components_formal(phase_states[phase_index])
        mixed_vectors = [
            symmetric_components_formal(mixed_states[axis][phase_index])
            for axis in range(3)
        ]
        derivative_values = []
        for component in (1, 2):
            derivative_values.append(
                (
                    phase_vector[component] * denominator
                    - psi[component] * phase_vector[0]
                )
                / denominator**2
            )
        for axis, (error, mixed_vector) in enumerate(
            zip(error_vectors, mixed_vectors)
        ):
            for local_component, component in enumerate((1, 2)):
                numerator = numerators[axis][local_component]
                numerator_derivative = (
                    mixed_vector[component] * denominator
                    + error[component] * phase_vector[0]
                    - phase_vector[component] * error[0]
                    - psi[component] * mixed_vector[0]
                )
                derivative_values.append(
                    numerator_derivative / denominator**2
                    - 2
                    * numerator
                    * phase_vector[0]
                    / denominator**3
                )
        for value_index, value in enumerate(derivative_values):
            jacobian[2 * value_index][phase_index] = value.real
            jacobian[2 * value_index + 1][phase_index] = value.imag
    return feature, jacobian


def exact_phase_balls(phases: np.ndarray) -> list[Any]:
    return [ar(repr(float(value))) for value in phases]


def box_phase_balls(chart: NumericalChart, radius: float) -> list[Any]:
    x_box = [ARB(0, ar(repr(radius))) for _ in range(TRANSVERSE_DIMENSION)]
    phases = []
    for phase_index, center in enumerate(chart.phases):
        value = ar(repr(float(center)))
        for coordinate in range(TRANSVERSE_DIMENSION):
            value += (
                ar(repr(float(chart.transverse_basis[phase_index, coordinate])))
                * x_box[coordinate]
            )
        phases.append(value)
    return phases


def real_matrix_product(
    left: list[list[Any]], right: np.ndarray
) -> list[list[Any]]:
    rows = len(left)
    shared = len(left[0])
    columns = right.shape[1]
    result = [[ARB(0) for _ in range(columns)] for _ in range(rows)]
    for row in range(rows):
        for column in range(columns):
            value = ARB(0)
            for index in range(shared):
                value += left[row][index] * ar(
                    repr(float(right[index, column]))
                )
            result[row][column] = value
    return result


def formal_reference_feature(reference_phases: np.ndarray) -> list[Any]:
    feature, _ = projective_feature_formal(
        exact_phase_balls(reference_phases)
    )
    return feature


def krawczyk_path(
    chart: NumericalChart,
    reference_feature: list[Any],
    radius: float,
) -> dict[str, Any]:
    start = time.perf_counter()
    center_feature, _ = projective_feature_formal(
        exact_phase_balls(chart.phases)
    )
    _, phase_jacobian_box = projective_feature_formal(
        box_phase_balls(chart, radius)
    )
    square_box = real_matrix_product(
        phase_jacobian_box, chart.transverse_basis
    )
    residual = [
        center_feature[index] - reference_feature[index]
        for index in range(TRANSVERSE_DIMENSION)
    ]

    correction = []
    for row in range(TRANSVERSE_DIMENSION):
        value = ARB(0)
        for column in range(TRANSVERSE_DIMENSION):
            value -= ar(repr(float(chart.inverse[row, column]))) * residual[column]
        correction.append(value)

    defect = [
        [ARB(0) for _ in range(TRANSVERSE_DIMENSION)]
        for _ in range(TRANSVERSE_DIMENSION)
    ]
    for row in range(TRANSVERSE_DIMENSION):
        for column in range(TRANSVERSE_DIMENSION):
            value = ARB(1 if row == column else 0)
            for index in range(TRANSVERSE_DIMENSION):
                value -= (
                    ar(repr(float(chart.inverse[row, index])))
                    * square_box[index][column]
                )
            defect[row][column] = value

    x_interval = ARB(0, ar(repr(radius)))
    krawczyk = []
    strict = []
    for row in range(TRANSVERSE_DIMENSION):
        value = correction[row]
        for column in range(TRANSVERSE_DIMENSION):
            value += defect[row][column] * x_interval
        krawczyk.append(value)
        strict.append(
            bool(value.lower() > ar(repr(-radius)))
            and bool(value.upper() < ar(repr(radius)))
        )

    return {
        "path": chart.name,
        "box_radius": radius,
        "numerical_exact_feature_residual_norm": float(
            np.linalg.norm(chart.residual)
        ),
        "transverse_jacobian_condition_number": float(
            np.linalg.cond(chart.jacobian)
        ),
        "minimum_retained_singular_value": float(
            chart.singular_values[TRANSVERSE_DIMENSION - 1]
        ),
        "maximum_discarded_singular_value": float(
            chart.singular_values[TRANSVERSE_DIMENSION]
            if len(chart.singular_values) > TRANSVERSE_DIMENSION
            else 0.0
        ),
        "krawczyk_intervals": [
            {
                "ball": str(value),
                "lower": str(value.lower()),
                "upper": str(value.upper()),
                "strictly_inside": passed,
            }
            for value, passed in zip(krawczyk, strict)
        ],
        "krawczyk_inclusion_pass": bool(all(strict)),
        "elapsed_seconds": time.perf_counter() - start,
    }


def main() -> None:
    global ACB, ACB_MAT, ARB

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTDIR)
    parser.add_argument("--cohort", type=Path, default=DEFAULT_COHORT)
    parser.add_argument("--box-radius", type=float, default=DEFAULT_BOX_RADIUS)
    parser.add_argument(
        "--max-paths",
        type=int,
        default=N_PATHS,
        help="Use 1 for a screening run or 12 for the declared full audit.",
    )
    parser.add_argument(
        "--numeric-only",
        action="store_true",
        help="Build and diagnose square charts without claiming a proof.",
    )
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"[notice] ignored notebook arguments: {unknown}")
    if not (1 <= args.max_paths <= N_PATHS):
        raise ValueError("--max-paths must be between 1 and 12.")
    if args.box_radius <= 0:
        raise ValueError("--box-radius must be positive.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cohort = load_json(args.cohort)
    cohort_paths = cohort.get("paths", [])
    if len(cohort_paths) != N_PATHS:
        raise RuntimeError(
            f"Frozen cohort contains {len(cohort_paths)}/{N_PATHS} paths."
        )
    cohort_hash = sha256_json(cohort)
    protocol = {
        "title": "PASQAL exact response-fibre Krawczyk audit",
        "version": VERSION,
        "frozen_cohort_sha256": cohort_hash,
        "declared_paths": N_PATHS,
        "evaluated_paths": args.max_paths,
        "constraint_dimension": TRANSVERSE_DIMENSION,
        "control_dimension": base.N_SEGMENTS,
        "fixed_fibre_dimension": base.N_SEGMENTS - TRANSVERSE_DIMENSION,
        "box_radius": args.box_radius,
        "fixed_radius_mode": True,
        "adaptive_radius_schedule": [],
        "arb_precision_bits": ARB_PRECISION_BITS,
        "proof_engine": "python-flint",
        "proof_engine_version_required": "0.8.0",
        "numeric_preconditioner_source": (
            "frozen decimal point preconditioners in the cohort"
        ),
        "constraint_map": (
            "two complex symmetric-subspace projective endpoint coordinates "
            "plus their exact first derivatives in amplitude, detuning, and "
            "interaction directions"
        ),
        "formal_interval_arithmetic": not args.numeric_only,
        "hardware_evidence": False,
    }
    protocol_hash = sha256_json(protocol)
    (args.output_dir / "protocol.json").write_text(
        json.dumps(protocol, indent=2), encoding="utf-8"
    )

    print(
        "[start] exact-response square-chart construction; "
        f"paths={args.max_paths}, formal={not args.numeric_only}",
        flush=True,
    )
    initialize_engine()

    reference_feature, reference_jacobian = projective_feature_numeric(
        engine.REFERENCE_PHASES, need_jacobian=True
    )
    assert reference_jacobian is not None
    reference_singular_values = svd(
        reference_jacobian, compute_uv=False
    )
    reference_rank = int(
        np.sum(reference_singular_values > NUMERICAL_RANK_CUTOFF)
    )
    charts = [
        frozen_chart(entry, reference_feature)
        for entry in cohort_paths[: args.max_paths]
    ]

    numerical_rows = [
        {
            "path": chart.name,
            "exact_feature_residual_norm": float(
                np.linalg.norm(chart.residual)
            ),
            "source_phase_correction_inf_norm": (
                chart.source_phase_correction_inf_norm
            ),
            "correction_optimizer_success": (
                chart.correction_optimizer_success
            ),
            "newton_correction_inf_norm": float(
                np.max(np.abs(chart.inverse @ chart.residual))
            ),
            "transverse_condition_number": float(
                np.linalg.cond(chart.jacobian)
            ),
            "minimum_retained_singular_value": float(
                chart.singular_values[TRANSVERSE_DIMENSION - 1]
            ),
        }
        for chart in charts
    ]
    maximum_newton_correction = max(
        row["newton_correction_inf_norm"] for row in numerical_rows
    )
    if (
        not args.numeric_only
        and args.box_radius <= maximum_newton_correction
    ):
        raise RuntimeError(
            "The smallest declared box radius is no larger than the "
            "numerical Newton "
            f"correction ({maximum_newton_correction:.6e}). Increase "
            "the radius schedule as a pre-outcome conditioning choice."
        )

    if args.numeric_only:
        report = {
            "scientific_status": "NUMERICAL_TRANSVERSE_CHART_SUPPORTED",
            "claim_boundary": (
                "Numerical chart diagnostic only; no interval existence "
                "or uniqueness theorem is claimed."
            ),
            "protocol_sha256": protocol_hash,
            "frozen_cohort_sha256": cohort_hash,
            "reference_exact_response_rank": reference_rank,
            "reference_singular_values": reference_singular_values.tolist(),
            "paths": numerical_rows,
        }
        (args.output_dir / "report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print("=" * 112)
        print("PASQAL TWO-ATOM EXACT-FIBRE NUMERICAL PRECONDITION AUDIT")
        print("=" * 112)
        print(json.dumps({
            "scientific_status": report["scientific_status"],
            "reference_exact_response_rank": reference_rank,
            "n_paths": len(charts),
            "maximum_exact_feature_residual_norm": max(
                row["exact_feature_residual_norm"] for row in numerical_rows
            ),
            "maximum_transverse_condition_number": max(
                row["transverse_condition_number"] for row in numerical_rows
            ),
            "maximum_newton_correction_inf_norm": max(
                row["newton_correction_inf_norm"] for row in numerical_rows
            ),
            "maximum_source_phase_correction_inf_norm": max(
                row["source_phase_correction_inf_norm"]
                for row in numerical_rows
            ),
            "output_directory": str(args.output_dir),
        }, indent=2))
        print("\nInterpretation")
        print(
            "  This run only establishes a well-conditioned numerical "
            "16x16 transverse formulation."
        )
        print("  Rerun without --numeric-only for the Arb Krawczyk audit.")
        return

    ACB, ACB_MAT, ARB, context = require_flint()
    context.prec = ARB_PRECISION_BITS
    context.threads = 1
    print(
        "[arb] computing the exact reference feature and interval "
        "phase/error Jacobians; this can take several minutes...",
        flush=True,
    )
    reference_feature_ball = formal_reference_feature(
        engine.REFERENCE_PHASES
    )
    formal_rows = []
    formal_runtime_rows = []
    for index, chart in enumerate(charts, start=1):
        print(
            f"[arb] path {index}/{len(charts)}: {chart.name}",
            flush=True,
        )
        radius = args.box_radius
        print(f"[arb]   fixed_radius={radius:.1e}", flush=True)
        try:
            raw_row = krawczyk_path(
                chart, reference_feature_ball, radius
            )
        except RuntimeError as exc:
            raw_row = {
                "path": chart.name,
                "box_radius": radius,
                "krawczyk_intervals": [],
                "krawczyk_inclusion_pass": False,
                "elapsed_seconds": 0.0,
                "diagnostic": str(exc),
            }
        proof_row = {
            "path": chart.name,
            "box_radius": radius,
            "accepted_radius": (
                radius if raw_row["krawczyk_inclusion_pass"] else None
            ),
            "krawczyk_intervals": raw_row["krawczyk_intervals"],
            "krawczyk_inclusion_pass": bool(
                raw_row["krawczyk_inclusion_pass"]
            ),
        }
        formal_rows.append(proof_row)
        formal_runtime_rows.append({
            key: value
            for key, value in raw_row.items()
            if key not in {"krawczyk_intervals"}
        })

    all_inclusions = all(
        row["krawczyk_inclusion_pass"] for row in formal_rows
    )
    full_declared_cohort = len(formal_rows) == N_PATHS
    supported = bool(all_inclusions and full_declared_cohort)
    status = (
        "L4_EXACT_RESPONSE_FIBRE_KRAWCZYK_SUPPORTED"
        if supported
        else (
            "PARTIAL_PATH_KRAWCZYK_SCREEN_SUPPORTED"
            if all_inclusions
            else "EXACT_RESPONSE_FIBRE_KRAWCZYK_INCONCLUSIVE"
        )
    )
    certificate = {
        "protocol_sha256": protocol_hash,
        "frozen_cohort_sha256": cohort_hash,
        "candidate_phases_decimal": {
            chart.name: [repr(float(value)) for value in chart.phases]
            for chart in charts
        },
        "transverse_bases_decimal": {
            chart.name: [
                [repr(float(value)) for value in row]
                for row in chart.transverse_basis
            ]
            for chart in charts
        },
        "paths": formal_rows,
    }
    certificate_hash = sha256_json(certificate)
    (args.output_dir / "krawczyk_certificate.json").write_text(
        json.dumps(certificate, indent=2), encoding="utf-8"
    )
    report = {
        "scientific_status": status,
        "claim_boundary": (
            "Formal existence and local uniqueness apply to the declared "
            "16-dimensional projective state-and-exact-response map with "
            "the eight chart fibre coordinates fixed. No hardware or "
            "finite-error ordering claim is added by this audit alone."
        ),
        "protocol_sha256": protocol_hash,
        "krawczyk_certificate_sha256": certificate_hash,
        "formal_interval_arithmetic": True,
        "arb_precision_bits": ARB_PRECISION_BITS,
        "frozen_cohort_sha256": cohort_hash,
        "reference_exact_response_rank": reference_rank,
        "evaluated_paths": len(formal_rows),
        "declared_paths": N_PATHS,
        "all_evaluated_krawczyk_inclusions_pass": all_inclusions,
        "full_declared_cohort": full_declared_cohort,
        "paths": formal_rows,
    }
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    run_metadata = {
        "certificate_sha256": certificate_hash,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": package_version("numpy"),
        "scipy": package_version("scipy"),
        "python_flint": package_version("python-flint"),
        "numerical_diagnostics": numerical_rows,
        "formal_runtime_diagnostics": formal_runtime_rows,
    }
    (args.output_dir / "run_metadata.json").write_text(
        json.dumps(run_metadata, indent=2), encoding="utf-8"
    )

    print("=" * 112)
    print("PASQAL TWO-ATOM EXACT RESPONSE-FIBRE KRAWCZYK AUDIT")
    print("=" * 112)
    print(json.dumps({
        "scientific_status": status,
        "formal_interval_arithmetic": True,
        "arb_precision_bits": ARB_PRECISION_BITS,
        "constraint_dimension": TRANSVERSE_DIMENSION,
        "fixed_fibre_dimension": (
            base.N_SEGMENTS - TRANSVERSE_DIMENSION
        ),
        "box_radius": args.box_radius,
        "fixed_radius_mode": True,
        "radius_schedule": [args.box_radius],
        "evaluated_paths": len(formal_rows),
        "declared_paths": N_PATHS,
        "krawczyk_inclusions": sum(
            row["krawczyk_inclusion_pass"] for row in formal_rows
        ),
        "accepted_radii": {
            row["path"]: row["accepted_radius"]
            for row in formal_rows
        },
        "all_evaluated_krawczyk_inclusions_pass": all_inclusions,
        "full_declared_cohort": full_declared_cohort,
        "protocol_sha256": protocol_hash,
        "krawczyk_certificate_sha256": certificate_hash,
        "output_directory": str(args.output_dir),
    }, indent=2))
    print("\nInterpretation")
    if supported:
        print(
            "  PASS: every declared path has a unique exact "
            "state-and-first-response-matched solution inside its "
            "transverse interval box."
        )
        print(
            "  The remaining step is to propagate these certified phase "
            "boxes through the formal order-30 ordering calculation."
        )
    elif all_inclusions:
        print(
            "  SCREEN PASS: every evaluated path passed, but fewer than "
            "the declared 12 paths were run."
        )
    else:
        print(
            "  INCONCLUSIVE: at least one path failed every predeclared "
            "radius. Do not shrink further post hoc; the next method is a "
            "centred mean-value/Taylor Jacobian enclosure."
        )


if __name__ == "__main__":
    main()
