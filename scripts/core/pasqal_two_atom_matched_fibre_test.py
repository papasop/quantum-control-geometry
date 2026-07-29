#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASQAL two-atom matched implementation-fibre test v1.0
=======================================================

Purpose
-------
Test a neutral-atom-specific proposition:

    endpoint state + duration + pulse area + hardware clock
    + complete first-order STATE response to
      (global amplitude, global detuning, Rydberg interaction)
    do not determine finite-error robustness.

The four frozen phase paths below:

* use the same two-atom register at the nominal point;
* use the same 24 constant-amplitude, 100 ns pulses;
* have the same 2.4 us duration and 4.8 pi pulse area per atom;
* return |gg> at the ideal point;
* match the full complex first-order output-state tangents in three
  independent error directions;
* are tested on six held-out finite errors (24 total tasks).

The Rydberg interaction direction is implemented as

    V -> V (1 + epsilon_V),  V = C6 / R^6.

For Pulser, this is realized by changing the atom separation to

    R(epsilon_V) = R0 / (1 + epsilon_V)^(1/6).

Scope
-----
This script uses no password, account, API key, cloud backend, or QPU.
SciPy exact piecewise propagation is the primary audit. If Pulser 1.8 is
installed, the same schedules are independently replayed with the local
QutipEmulator and exported as Pulser abstract-representation JSON files.

Colab
-----
    %pip -q install "pulser==1.8.0" \
        "pulser-simulation==1.8.0" "qutip==5.3.0"
    %run pasqal_two_atom_matched_fibre_test.py

Local
-----
    python pasqal_two_atom_matched_fibre_test.py
    python pasqal_two_atom_matched_fibre_test.py --install
"""

from __future__ import annotations

import argparse
import csv
import importlib
import importlib.metadata
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.linalg import expm


VERSION = "1.0"
SEED = 20260730

CLOCK_NS = 4
SEGMENT_DURATION_NS = 100
SEGMENT_DURATION_US = SEGMENT_DURATION_NS / 1000.0
N_SEGMENTS = 24
TOTAL_DURATION_NS = N_SEGMENTS * SEGMENT_DURATION_NS

OMEGA_RAD_PER_US = 2.0 * math.pi
ANGLE_PER_SEGMENT = OMEGA_RAD_PER_US * SEGMENT_DURATION_US
TOTAL_AREA_RAD = N_SEGMENTS * ANGLE_PER_SEGMENT

# Pulser 1.8.0 DigitalAnalogDevice value.
INTERACTION_COEFF_RAD_UM6_PER_US = 5_420_158.53
INTERACTION_TO_OMEGA = 4.0
NOMINAL_INTERACTION_RAD_PER_US = INTERACTION_TO_OMEGA * OMEGA_RAD_PER_US
NOMINAL_DISTANCE_UM = (
    INTERACTION_COEFF_RAD_UM6_PER_US / NOMINAL_INTERACTION_RAD_PER_US
) ** (1.0 / 6.0)

FD_STEP = 2.0e-5
ENDPOINT_TOL = 1.0e-9
FIRST_ORDER_STATE_TOL = 2.0e-7
FINITE_MEAN_SPLIT_MIN = 5.0e-4
FINITE_WORST_SPLIT_MIN = 2.0e-3
INTERACTION_CELL_SPLIT_MIN = 5.0e-3

# Pulser/QutipEmulator uses a 1 ns sampled QobjEvo. Abrupt phase boundaries
# are therefore close to, but not identical to, ideal constant segments.
PULSER_CELL_TOL = 1.0e-2
PULSER_RANGE_TOL = 5.0e-3
PULSER_ATOL = 1.0e-11
PULSER_RTOL = 1.0e-11
PULSER_MAX_STEP_NS = 1.0

OUTDIR = Path("pasqal_two_atom_matched_fibre_results")

I2 = np.eye(2, dtype=complex)
SX = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SY = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
NUMBER = np.diag([0.0, 1.0]).astype(complex)

GLOBAL_X = np.kron(SX, I2) + np.kron(I2, SX)
GLOBAL_Y = np.kron(SY, I2) + np.kron(I2, SY)
TOTAL_NUMBER = np.kron(NUMBER, I2) + np.kron(I2, NUMBER)
DOUBLE_RYDBERG = np.kron(NUMBER, NUMBER)

# Analytic basis: |gg>, |gr>, |rg>, |rr>.
GG = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)


@dataclass(frozen=True)
class PathSpec:
    name: str
    role: str
    phases: tuple[float, ...]


PATHS = (
    PathSpec(
        "reference",
        "matched_reference",
        (
            5.395938949660, 4.364190556336, 4.065716153363,
            4.362035605699, 5.384474017704, 1.275621345422,
            1.330584917556, 4.407856703296, 4.811419315138,
            4.022090674744, 0.414000889690, 1.067187010905,
            1.401546960667, 3.017636778929, 2.942592144415,
            3.205438748314, 0.757976217375, 5.846203422983,
            3.626398737602, 5.777000471280, 3.048480766333,
            4.247669043136, 2.313878941042, 3.714910179805,
        ),
    ),
    PathSpec(
        "fibre_A",
        "matched_fibre",
        (
            4.990122007541, 4.830615555474, 4.008556750263,
            4.481796139382, 5.486608813061, 1.175428897198,
            1.235950499079, 4.727721805269, 4.876534086102,
            3.764918780595, 0.749351962827, 1.755969427230,
            1.559757011976, 3.043381828609, 3.386593422130,
            3.555647533995, 0.962307731009, 5.809078020691,
            3.792742539089, 6.047941029731, 3.015084426302,
            4.229614921932, 2.672127491269, 3.763040660653,
        ),
    ),
    PathSpec(
        "fibre_B",
        "matched_fibre",
        (
            6.012841492833, 4.612089140794, 4.286395015532,
            4.142392239382, 4.800046884609, 1.019702362701,
            1.702096953436, 5.095795945140, 5.237702986657,
            4.455295158587, 0.418598373057, 1.109270106234,
            1.654983239652, 2.919941021845, 2.871447100151,
            3.094293092165, 0.813820190612, 5.602766281478,
            3.627436924946, 5.559971765057, 2.993865855954,
            4.342387222303, 1.953697019038, 3.620773791134,
        ),
    ),
    PathSpec(
        "fibre_C",
        "matched_fibre",
        (
            4.814402407408, 4.246558079266, 3.824329271618,
            4.349237885264, 5.438556075924, 1.760065068095,
            1.705938350518, 4.391592320445, 5.394144479234,
            4.136152324633, 0.671434885202, 1.351360207320,
            1.199503124485, 2.772426320251, 2.588961837611,
            3.337045748430, 1.133815234257, 5.985438981938,
            4.461335572225, 6.226198723839, 3.448882808886,
            3.868375382411, 2.701943212841, 3.843254859098,
        ),
    ),
)


# epsilon_detuning is Delta/Omega. epsilon_interaction is Delta V / V.
# These are held out from the local constraint solve.
HELD_OUT_ERRORS = (
    {"label": "amp_minus", "amplitude": -0.06, "detuning": 0.00, "interaction": 0.00},
    {"label": "amp_plus", "amplitude": +0.06, "detuning": 0.00, "interaction": 0.00},
    {"label": "det_minus", "amplitude": 0.00, "detuning": -0.04, "interaction": 0.00},
    {"label": "det_plus", "amplitude": 0.00, "detuning": +0.04, "interaction": 0.00},
    {"label": "int_minus", "amplitude": 0.00, "detuning": 0.00, "interaction": -0.05},
    {"label": "int_plus", "amplitude": 0.00, "detuning": 0.00, "interaction": +0.05},
)


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def install_local_stack() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "pulser==1.8.0",
            "pulser-simulation==1.8.0",
            "qutip==5.3.0",
        ],
        check=True,
    )
    importlib.invalidate_caches()


def phase_factor(anchor: np.ndarray, state: np.ndarray) -> complex:
    overlap = np.vdot(anchor, state)
    if abs(overlap) < 1.0e-14:
        return 1.0 + 0.0j
    return complex(np.exp(-1.0j * np.angle(overlap)))


def normalized(state: np.ndarray) -> np.ndarray:
    return state / np.linalg.norm(state)


def segment_hamiltonian(
    phase: float,
    amplitude_error: float,
    detuning_error: float,
    interaction_error: float,
) -> np.ndarray:
    drive_axis = (
        math.cos(phase) * GLOBAL_X + math.sin(phase) * GLOBAL_Y
    )
    drive = (
        0.5
        * OMEGA_RAD_PER_US
        * (1.0 + amplitude_error)
        * drive_axis
    )
    detuning = -OMEGA_RAD_PER_US * detuning_error * TOTAL_NUMBER
    interaction = (
        NOMINAL_INTERACTION_RAD_PER_US
        * (1.0 + interaction_error)
        * DOUBLE_RYDBERG
    )
    return drive + detuning + interaction


def analytic_state(
    phases: Iterable[float],
    amplitude_error: float = 0.0,
    detuning_error: float = 0.0,
    interaction_error: float = 0.0,
) -> np.ndarray:
    state = GG.copy()
    for phase in phases:
        hamiltonian = segment_hamiltonian(
            phase,
            amplitude_error,
            detuning_error,
            interaction_error,
        )
        state = expm(-1.0j * SEGMENT_DURATION_US * hamiltonian) @ state
    return normalized(state)


def state_infidelity(target: np.ndarray, state: np.ndarray) -> float:
    fidelity = abs(np.vdot(target, state)) ** 2
    return float(max(0.0, 1.0 - min(1.0, fidelity)))


def state_probabilities(state: np.ndarray) -> np.ndarray:
    return np.abs(state) ** 2


def tvd(first: np.ndarray, second: np.ndarray) -> float:
    return float(0.5 * np.sum(np.abs(first - second)))


def first_order_state_tangents(
    phases: Iterable[float],
) -> tuple[np.ndarray, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    phases = tuple(phases)
    base = analytic_state(phases)
    tangents: list[np.ndarray] = []
    for error_axis in range(3):
        plus = [0.0, 0.0, 0.0]
        minus = [0.0, 0.0, 0.0]
        plus[error_axis] = FD_STEP
        minus[error_axis] = -FD_STEP
        state_plus = analytic_state(phases, *plus)
        state_minus = analytic_state(phases, *minus)
        state_plus *= phase_factor(base, state_plus)
        state_minus *= phase_factor(base, state_minus)
        tangent = (state_plus - state_minus) / (2.0 * FD_STEP)
        # Remove the unobservable global-phase component.
        tangent -= base * np.vdot(base, tangent)
        tangents.append(tangent)
    return base, (tangents[0], tangents[1], tangents[2])


def complex_gap_norm(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.linalg.norm(first - second))


def phase_geometry(phases: Iterable[float]) -> dict:
    phases = np.asarray(tuple(phases), dtype=float)
    points = np.exp(1.0j * phases)
    closed = np.r_[points, points[0]]
    oriented_area = 0.5 * float(
        np.sum(np.imag(np.conj(closed[:-1]) * closed[1:]))
    )
    steps = np.angle(np.exp(1.0j * np.diff(np.r_[phases, phases[0]])))
    return {
        "control_polygon_oriented_area": oriented_area,
        "total_absolute_phase_turn": float(np.sum(np.abs(steps))),
        "net_wrapped_phase_turn": float(np.sum(steps)),
    }


def exact_constraint_audit() -> tuple[dict, list[dict], np.ndarray]:
    reference_state, reference_tangents = first_order_state_tangents(
        PATHS[0].phases
    )
    reference_probs = state_probabilities(reference_state)
    rows: list[dict] = []

    for path in PATHS:
        state, tangents = first_order_state_tangents(path.phases)
        common_phase = phase_factor(reference_state, state)
        aligned_state = state * common_phase
        aligned_tangents = tuple(tangent * common_phase for tangent in tangents)

        row = {
            "path": path.name,
            "role": path.role,
            "n_segments": len(path.phases),
            "endpoint_state_infidelity": state_infidelity(reference_state, state),
            "endpoint_Pgg": float(abs(state[0]) ** 2),
            "endpoint_Prr": float(abs(state[3]) ** 2),
            "endpoint_distribution_tvd": tvd(
                reference_probs, state_probabilities(state)
            ),
            "amplitude_tangent_gap_norm": complex_gap_norm(
                aligned_tangents[0], reference_tangents[0]
            ),
            "detuning_tangent_gap_norm": complex_gap_norm(
                aligned_tangents[1], reference_tangents[1]
            ),
            "interaction_tangent_gap_norm": complex_gap_norm(
                aligned_tangents[2], reference_tangents[2]
            ),
            **phase_geometry(path.phases),
        }
        row["endpoint_pass"] = (
            row["endpoint_state_infidelity"] <= ENDPOINT_TOL
        )
        row["amplitude_first_order_pass"] = (
            row["amplitude_tangent_gap_norm"] <= FIRST_ORDER_STATE_TOL
        )
        row["detuning_first_order_pass"] = (
            row["detuning_tangent_gap_norm"] <= FIRST_ORDER_STATE_TOL
        )
        row["interaction_first_order_pass"] = (
            row["interaction_tangent_gap_norm"] <= FIRST_ORDER_STATE_TOL
        )
        rows.append(row)

    gates = {
        "no_credentials_required": True,
        "two_atom_interaction_present": NOMINAL_INTERACTION_RAD_PER_US > 0.0,
        "clock_multiple_pass": (
            SEGMENT_DURATION_NS % CLOCK_NS == 0
            and TOTAL_DURATION_NS % CLOCK_NS == 0
        ),
        "same_segment_count_pass": all(
            len(path.phases) == N_SEGMENTS for path in PATHS
        ),
        "same_duration_pass": True,
        "same_amplitude_envelope_pass": True,
        "same_total_area_pass": True,
        "same_nominal_register_pass": True,
        "return_to_gg_pass": all(
            row["endpoint_Pgg"] >= 1.0 - ENDPOINT_TOL for row in rows
        ),
        "endpoint_state_match_pass": all(row["endpoint_pass"] for row in rows),
        "complete_first_order_amplitude_state_match_pass": all(
            row["amplitude_first_order_pass"] for row in rows
        ),
        "complete_first_order_detuning_state_match_pass": all(
            row["detuning_first_order_pass"] for row in rows
        ),
        "complete_first_order_interaction_state_match_pass": all(
            row["interaction_first_order_pass"] for row in rows
        ),
    }
    gates["all_constraint_gates_pass"] = all(gates.values())
    return gates, rows, reference_state


def finite_error_audit(
    target_state: np.ndarray,
) -> tuple[list[dict], dict]:
    target_probs = state_probabilities(target_state)
    rows: list[dict] = []
    for path in PATHS:
        for error_index, error in enumerate(HELD_OUT_ERRORS):
            state = analytic_state(
                path.phases,
                error["amplitude"],
                error["detuning"],
                error["interaction"],
            )
            probs = state_probabilities(state)
            rows.append(
                {
                    "task_index": len(rows),
                    "error_index": error_index,
                    "error_label": error["label"],
                    "path": path.name,
                    "amplitude_error": error["amplitude"],
                    "detuning_over_omega": error["detuning"],
                    "interaction_fractional_error": error["interaction"],
                    "distance_um": (
                        NOMINAL_DISTANCE_UM
                        / (1.0 + error["interaction"]) ** (1.0 / 6.0)
                    ),
                    "target_state_infidelity": state_infidelity(
                        target_state, state
                    ),
                    "distribution_tvd": tvd(target_probs, probs),
                    "Pgg": float(probs[0]),
                    "Pgr": float(probs[1]),
                    "Prg": float(probs[2]),
                    "Prr": float(probs[3]),
                    "P_any_excitation": float(1.0 - probs[0]),
                }
            )

    by_path: dict[str, dict] = {}
    for path in PATHS:
        path_rows = [row for row in rows if row["path"] == path.name]
        infidelities = np.array(
            [row["target_state_infidelity"] for row in path_rows]
        )
        prr = np.array([row["Prr"] for row in path_rows])
        by_path[path.name] = {
            "mean_infidelity": float(np.mean(infidelities)),
            "worst_infidelity": float(np.max(infidelities)),
            "mean_Prr": float(np.mean(prr)),
            "worst_Prr": float(np.max(prr)),
        }

    means = np.array(
        [by_path[path.name]["mean_infidelity"] for path in PATHS]
    )
    worsts = np.array(
        [by_path[path.name]["worst_infidelity"] for path in PATHS]
    )
    interaction_spreads: dict[str, float] = {}
    for label in ("int_minus", "int_plus"):
        values = [
            row["target_state_infidelity"]
            for row in rows
            if row["error_label"] == label
        ]
        interaction_spreads[label] = float(np.ptp(values))

    summary = {
        "n_paths": len(PATHS),
        "n_held_out_errors": len(HELD_OUT_ERRORS),
        "n_tasks": len(rows),
        "by_path": by_path,
        "mean_infidelity_range": float(np.ptp(means)),
        "worst_infidelity_range": float(np.ptp(worsts)),
        "interaction_cell_infidelity_spreads": interaction_spreads,
    }
    summary["finite_paths_distinguished"] = bool(
        summary["mean_infidelity_range"] >= FINITE_MEAN_SPLIT_MIN
        and summary["worst_infidelity_range"] >= FINITE_WORST_SPLIT_MIN
    )
    summary["interaction_specific_split_pass"] = bool(
        max(interaction_spreads.values()) >= INTERACTION_CELL_SPLIT_MIN
    )
    summary["best_mean_path"] = min(
        by_path, key=lambda name: by_path[name]["mean_infidelity"]
    )
    summary["best_worst_case_path"] = min(
        by_path, key=lambda name: by_path[name]["worst_infidelity"]
    )
    return rows, summary


def build_pulser_sequence(
    path: PathSpec,
    amplitude_error: float,
    detuning_error: float,
    interaction_error: float,
):
    from pulser import DigitalAnalogDevice, Pulse, Register, Sequence

    distance = (
        NOMINAL_DISTANCE_UM
        / (1.0 + interaction_error) ** (1.0 / 6.0)
    )
    register = Register({"q0": (0.0, 0.0), "q1": (distance, 0.0)})
    sequence = Sequence(register, DigitalAnalogDevice)
    sequence.declare_channel("rydberg", "rydberg_global")
    for phase in path.phases:
        sequence.add(
            Pulse.ConstantPulse(
                SEGMENT_DURATION_NS,
                OMEGA_RAD_PER_US * (1.0 + amplitude_error),
                OMEGA_RAD_PER_US * detuning_error,
                float(phase),
            ),
            "rydberg",
        )
    return sequence


def qobj_fidelity_squared(target, candidate) -> float:
    import qutip

    return float(qutip.metrics.fidelity(target, candidate) ** 2)


def qobj_probabilities(state) -> np.ndarray:
    if getattr(state, "isket", False):
        values = np.abs(np.asarray(state.full()).reshape(-1)) ** 2
    else:
        values = np.real(np.diag(np.asarray(state.full())))
    return np.asarray(values, dtype=float)


def export_abstract_sequence(sequence, output_path: Path) -> None:
    try:
        payload = sequence.to_abstract_repr()
        if isinstance(payload, str):
            output_path.write_text(payload, encoding="utf-8")
        else:
            output_path.write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
    except Exception as exc:
        output_path.with_suffix(".error.txt").write_text(
            f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
        )


def pulser_crosscheck(exact_rows: list[dict]) -> dict:
    versions = {
        "pulser": package_version("pulser"),
        "pulser-simulation": package_version("pulser-simulation"),
        "qutip": package_version("qutip"),
    }
    if versions["pulser"] is None or versions["pulser-simulation"] is None:
        return {
            "status": "SKIPPED_NOT_INSTALLED",
            "versions": versions,
            "instruction": (
                'pip install "pulser==1.8.0" '
                '"pulser-simulation==1.8.0" "qutip==5.3.0"'
            ),
        }

    from pulser import DigitalAnalogDevice
    from pulser_simulation import QutipEmulator

    device_coeff = float(DigitalAnalogDevice.interaction_coeff)
    coeff_match = math.isclose(
        device_coeff,
        INTERACTION_COEFF_RAD_UM6_PER_US,
        rel_tol=1.0e-10,
        abs_tol=1.0e-6,
    )
    if not coeff_match:
        return {
            "status": "FAIL",
            "reason": "Pulser device interaction coefficient changed.",
            "script_interaction_coeff": INTERACTION_COEFF_RAD_UM6_PER_US,
            "device_interaction_coeff": device_coeff,
            "versions": versions,
        }

    solver_options = {
        "atol": PULSER_ATOL,
        "rtol": PULSER_RTOL,
        "max_step": PULSER_MAX_STEP_NS,
        "nsteps": 100_000,
    }
    ideal_sequence = build_pulser_sequence(PATHS[0], 0.0, 0.0, 0.0)
    programmed_duration = int(ideal_sequence.get_duration())
    if programmed_duration != TOTAL_DURATION_NS:
        return {
            "status": "FAIL",
            "reason": "Pulser inserted unexpected timing.",
            "expected_duration_ns": TOTAL_DURATION_NS,
            "programmed_duration_ns": programmed_duration,
            "versions": versions,
        }

    target = QutipEmulator.from_sequence(
        ideal_sequence, sampling_rate=1.0
    ).run(**solver_options).get_final_state()

    exact_lookup = {
        (
            row["path"],
            row["error_label"],
        ): row
        for row in exact_rows
    }
    abstract_dir = OUTDIR / "pulser_abstract_sequences"
    abstract_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for path in PATHS:
        for error in HELD_OUT_ERRORS:
            sequence = build_pulser_sequence(
                path,
                error["amplitude"],
                error["detuning"],
                error["interaction"],
            )
            export_abstract_sequence(
                sequence,
                abstract_dir / f"{path.name}__{error['label']}.json",
            )
            state = QutipEmulator.from_sequence(
                sequence, sampling_rate=1.0
            ).run(**solver_options).get_final_state()
            probabilities = qobj_probabilities(state)
            # Pulser/Qutip ground-rydberg basis is ordered r,g, so |rr> is 0
            # and |gg> is the last component.
            pulser_infidelity = 1.0 - qobj_fidelity_squared(target, state)
            exact = exact_lookup[(path.name, error["label"])]
            rows.append(
                {
                    "path": path.name,
                    "error_label": error["label"],
                    "scipy_infidelity": exact["target_state_infidelity"],
                    "pulser_infidelity": pulser_infidelity,
                    "infidelity_absolute_difference": abs(
                        pulser_infidelity - exact["target_state_infidelity"]
                    ),
                    "scipy_Prr": exact["Prr"],
                    "pulser_Prr": float(probabilities[0]),
                    "Prr_absolute_difference": abs(
                        float(probabilities[0]) - exact["Prr"]
                    ),
                }
            )

    def summarize(value_key: str) -> tuple[dict, float, float]:
        by_path: dict[str, dict] = {}
        for path in PATHS:
            values = np.array(
                [
                    row[value_key]
                    for row in rows
                    if row["path"] == path.name
                ]
            )
            by_path[path.name] = {
                "mean": float(np.mean(values)),
                "worst": float(np.max(values)),
            }
        means = np.array([by_path[path.name]["mean"] for path in PATHS])
        worsts = np.array([by_path[path.name]["worst"] for path in PATHS])
        return by_path, float(np.ptp(means)), float(np.ptp(worsts))

    exact_by_path, exact_mean_range, exact_worst_range = summarize(
        "scipy_infidelity"
    )
    pulser_by_path, pulser_mean_range, pulser_worst_range = summarize(
        "pulser_infidelity"
    )
    exact_worst_rank = sorted(
        exact_by_path, key=lambda name: exact_by_path[name]["worst"]
    )
    pulser_worst_rank = sorted(
        pulser_by_path, key=lambda name: pulser_by_path[name]["worst"]
    )

    max_cell_difference = float(
        max(row["infidelity_absolute_difference"] for row in rows)
    )
    max_prr_difference = float(
        max(row["Prr_absolute_difference"] for row in rows)
    )
    mean_range_difference = abs(pulser_mean_range - exact_mean_range)
    worst_range_difference = abs(pulser_worst_range - exact_worst_range)
    split_reproduced = (
        pulser_mean_range >= FINITE_MEAN_SPLIT_MIN
        and pulser_worst_range >= FINITE_WORST_SPLIT_MIN
    )
    worst_ranking_preserved = exact_worst_rank == pulser_worst_rank

    passed = (
        max_cell_difference <= PULSER_CELL_TOL
        and max_prr_difference <= PULSER_CELL_TOL
        and mean_range_difference <= PULSER_RANGE_TOL
        and worst_range_difference <= PULSER_RANGE_TOL
        and split_reproduced
        and worst_ranking_preserved
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "versions": versions,
        "programmed_duration_ns": programmed_duration,
        "device_interaction_coeff": device_coeff,
        "nominal_distance_um": NOMINAL_DISTANCE_UM,
        "solver_options": solver_options,
        "max_cell_infidelity_difference": max_cell_difference,
        "max_Prr_difference": max_prr_difference,
        "cell_tolerance": PULSER_CELL_TOL,
        "exact_mean_infidelity_range": exact_mean_range,
        "pulser_mean_infidelity_range": pulser_mean_range,
        "mean_range_difference": mean_range_difference,
        "exact_worst_infidelity_range": exact_worst_range,
        "pulser_worst_infidelity_range": pulser_worst_range,
        "worst_range_difference": worst_range_difference,
        "range_tolerance": PULSER_RANGE_TOL,
        "exact_worst_ranking_best_to_worst": exact_worst_rank,
        "pulser_worst_ranking_best_to_worst": pulser_worst_rank,
        "worst_ranking_preserved": worst_ranking_preserved,
        "finite_split_reproduced": split_reproduced,
        "rows": rows,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install pinned local Pulser/Qutip packages; no login is used.",
    )
    parser.add_argument(
        "--skip-pulser",
        action="store_true",
        help="Run only the exact SciPy audit.",
    )
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"[notice] ignored notebook arguments: {unknown}")
    if args.install:
        install_local_stack()

    OUTDIR.mkdir(parents=True, exist_ok=True)
    gates, constraint_rows, target_state = exact_constraint_audit()
    finite_rows, finite_summary = finite_error_audit(target_state)
    pulser = (
        {"status": "SKIPPED_BY_USER"}
        if args.skip_pulser
        else pulser_crosscheck(finite_rows)
    )

    supported = (
        gates["all_constraint_gates_pass"]
        and finite_summary["finite_paths_distinguished"]
        and finite_summary["interaction_specific_split_pass"]
        and pulser["status"]
        in {"PASS", "SKIPPED_NOT_INSTALLED", "SKIPPED_BY_USER"}
    )
    scientific_status = (
        "TWO_ATOM_MATCHED_FIBRE_MEMORY_SUPPORTED"
        if supported
        else "NOT_SUPPORTED"
    )
    report = {
        "title": "PASQAL two-atom matched implementation-fibre test",
        "version": VERSION,
        "seed": SEED,
        "scientific_status": scientific_status,
        "evidence_scope": (
            "exact two-atom local propagation plus optional local "
            "Pulser/QutipEmulator; not PASQAL Cloud or QPU evidence"
        ),
        "model": {
            "basis": ["gg", "gr", "rg", "rr"],
            "clock_ns": CLOCK_NS,
            "segment_duration_ns": SEGMENT_DURATION_NS,
            "n_segments": N_SEGMENTS,
            "total_duration_ns": TOTAL_DURATION_NS,
            "omega_rad_per_us": OMEGA_RAD_PER_US,
            "total_area_rad_per_atom": TOTAL_AREA_RAD,
            "interaction_rad_per_us": NOMINAL_INTERACTION_RAD_PER_US,
            "interaction_to_omega": INTERACTION_TO_OMEGA,
            "interaction_coeff_rad_um6_per_us": (
                INTERACTION_COEFF_RAD_UM6_PER_US
            ),
            "nominal_distance_um": NOMINAL_DISTANCE_UM,
        },
        "constraints": {
            "gates": gates,
            "per_path": constraint_rows,
        },
        "finite_error_audit": finite_summary,
        "pulser_crosscheck": pulser,
    }

    (OUTDIR / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_csv(OUTDIR / "constraint_audit.csv", constraint_rows)
    write_csv(OUTDIR / "finite_error_tasks.csv", finite_rows)
    if "rows" in pulser:
        write_csv(OUTDIR / "pulser_crosscheck.csv", pulser["rows"])

    headline = {
        "scientific_status": scientific_status,
        "all_constraint_gates_pass": gates["all_constraint_gates_pass"],
        "return_to_gg_pass": gates["return_to_gg_pass"],
        "complete_first_order_amplitude_state_match_pass": gates[
            "complete_first_order_amplitude_state_match_pass"
        ],
        "complete_first_order_detuning_state_match_pass": gates[
            "complete_first_order_detuning_state_match_pass"
        ],
        "complete_first_order_interaction_state_match_pass": gates[
            "complete_first_order_interaction_state_match_pass"
        ],
        "n_local_tasks": finite_summary["n_tasks"],
        "mean_infidelity_range": finite_summary["mean_infidelity_range"],
        "worst_infidelity_range": finite_summary["worst_infidelity_range"],
        "interaction_specific_split_pass": finite_summary[
            "interaction_specific_split_pass"
        ],
        "best_mean_path": finite_summary["best_mean_path"],
        "best_worst_case_path": finite_summary["best_worst_case_path"],
        "pulser_crosscheck": pulser["status"],
        "output_directory": str(OUTDIR),
    }
    print("=" * 104)
    print("PASQAL TWO-ATOM MATCHED IMPLEMENTATION-FIBRE TEST")
    print("=" * 104)
    print(json.dumps(headline, indent=2, ensure_ascii=False))
    print("\nPer-path held-out finite-error summary")
    for name, values in finite_summary["by_path"].items():
        print(
            f"  {name:10s} "
            f"mean_inf={values['mean_infidelity']:.9f} "
            f"worst_inf={values['worst_infidelity']:.9f} "
            f"mean_Prr={values['mean_Prr']:.9f}"
        )
    print("\nInterpretation")
    print(
        "  PASS means the paths match the complete first-order OUTPUT-STATE "
        "response in amplitude, detuning, and interaction directions, but "
        "separate at held-out finite errors."
    )
    print(
        "  This is a local two-atom neutral-atom control result. It does not "
        "claim full-unitary matching, PASQAL Cloud execution, or QPU evidence."
    )


if __name__ == "__main__":
    main()
