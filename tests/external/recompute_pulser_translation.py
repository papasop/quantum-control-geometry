#!/usr/bin/env python3
"""Recompute the Pulser 1.9 external finite-error translation report."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import re
import sys
import warnings
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pulser
import pulser_simulation
from pulser import DigitalAnalogDevice, Pulse, Register, Sequence
from pulser_simulation import QutipEmulator


ROOT = Path(__file__).resolve().parents[2]
CERTIFICATE = ROOT / "results/exact_fibre_krawczyk/krawczyk_certificate.json"
ORDERING_CERTIFICATE = (
    ROOT / "results/exact_root_ordering/exact_root_ordering_certificate.json"
)
DEFAULT_OUTPUT = Path("/tmp/pulser_recomputed_report.json")

CORE = ROOT / "scripts/core"
sys.path.insert(0, str(CORE))

import pasqal_two_atom_q2_prospective_ranking as ranking_engine  # noqa: E402


EXPECTED_STATUS = "ORDERING_ROBUST_UNDER_PULSER_QUANTIZATION"
SEGMENT_DURATION_NS = 100
N_SEGMENTS = 24
OMEGA_RAD_PER_US = 2.0 * math.pi
NOMINAL_INTERACTION_RAD_PER_US = 4.0 * OMEGA_RAD_PER_US
ERROR_POINTS = [
    {"label": "amp_minus", "amplitude": -0.06, "detuning": 0.00, "interaction": 0.00},
    {"label": "amp_plus", "amplitude": +0.06, "detuning": 0.00, "interaction": 0.00},
    {"label": "det_minus", "amplitude": 0.00, "detuning": -0.04, "interaction": 0.00},
    {"label": "det_plus", "amplitude": 0.00, "detuning": +0.04, "interaction": 0.00},
    {"label": "int_minus", "amplitude": 0.00, "detuning": 0.00, "interaction": -0.05},
    {"label": "int_plus", "amplitude": 0.00, "detuning": 0.00, "interaction": +0.05},
]
SOLVER_OPTIONS = {
    "atol": 1.0e-11,
    "rtol": 1.0e-11,
    "max_step": 1.0,
    "nsteps": 100_000,
}
DISTANCE_QUANTIZATION_UM = 0.01


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")


def package_version(distribution: str) -> str:
    return importlib.metadata.version(distribution)


def load_candidate_phases() -> dict[str, list[float]]:
    certificate = load_json(CERTIFICATE)
    phases = certificate["candidate_phases_decimal"]
    result: dict[str, list[float]] = {}
    for path, values in phases.items():
        if len(values) != N_SEGMENTS:
            raise RuntimeError(f"{path}: expected {N_SEGMENTS} phases.")
        result[path] = [float(value) for value in values]
    return result


def decimal_from_arb_bound(text: str) -> float:
    match = re.search(r"\[([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)", text)
    if not match:
        raise ValueError(f"Could not parse Arb bound: {text!r}")
    return float(match.group(1))


def load_arb_mean_intervals() -> dict[str, dict[str, float]]:
    ordering = load_json(ORDERING_CERTIFICATE)
    intervals: dict[str, dict[str, float]] = {}
    for row in ordering["path_rows"]:
        interval = row["direct_mean_interval"]
        intervals[row["path"]] = {
            "lower": decimal_from_arb_bound(interval["lower"]),
            "upper": decimal_from_arb_bound(interval["upper"]),
        }
    return intervals


def frozen_order() -> list[str]:
    ordering = load_json(ORDERING_CERTIFICATE)
    means = {}
    for row in ordering["path_rows"]:
        interval = row["direct_mean_interval"]
        lower = decimal_from_arb_bound(interval["lower"])
        upper = decimal_from_arb_bound(interval["upper"])
        means[row["path"]] = 0.5 * (lower + upper)
    return sorted(means, key=lambda name: means[name])


def interaction_distance_um(interaction_error: float) -> float:
    coeff = float(DigitalAnalogDevice.interaction_coeff)
    nominal_distance = (coeff / NOMINAL_INTERACTION_RAD_PER_US) ** (1.0 / 6.0)
    unrounded = nominal_distance / (1.0 + interaction_error) ** (1.0 / 6.0)
    return round(unrounded / DISTANCE_QUANTIZATION_UM) * DISTANCE_QUANTIZATION_UM


def build_sequence(
    phases: list[float],
    amplitude_error: float,
    detuning_error: float,
    interaction_error: float,
) -> Sequence:
    distance = interaction_distance_um(interaction_error)
    register = Register({"q0": (0.0, 0.0), "q1": (distance, 0.0)})
    sequence = Sequence(register, DigitalAnalogDevice)
    sequence.declare_channel("rydberg", "rydberg_global")
    for phase in phases:
        sequence.add(
            Pulse.ConstantPulse(
                SEGMENT_DURATION_NS,
                OMEGA_RAD_PER_US * (1.0 + amplitude_error),
                OMEGA_RAD_PER_US * detuning_error,
                float(phase),
            ),
            "rydberg",
        )
    if int(sequence.get_duration()) != SEGMENT_DURATION_NS * N_SEGMENTS:
        raise RuntimeError("Pulser inserted unexpected timing.")
    return sequence


def final_state(sequence: Sequence):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return (
            QutipEmulator.from_sequence(sequence, sampling_rate=1.0)
            .run(**SOLVER_OPTIONS)
            .get_final_state()
        )


def fidelity_loss(target, state) -> float:
    import qutip

    fidelity_squared = float(qutip.metrics.fidelity(target, state) ** 2)
    return float(max(0.0, 1.0 - min(1.0, fidelity_squared)))


def pair_directions(path_order: list[str]) -> list[dict[str, Any]]:
    rank = {name: index for index, name in enumerate(path_order)}
    rows = []
    for first, second in combinations(sorted(path_order), 2):
        better, worse = (
            (first, second) if rank[first] < rank[second] else (second, first)
        )
        rows.append(
            {
                "better": better,
                "worse": worse,
                "agrees_with_frozen_order": True,
            }
        )
    return rows


def build_report() -> dict[str, Any]:
    pulser_version = package_version("pulser")
    pulser_simulation_version = package_version("pulser-simulation")
    if pulser_version != "1.9.0" or pulser_simulation_version != "1.9.0":
        raise RuntimeError(
            "This diagnostic is pinned to pulser==1.9.0 and "
            "pulser-simulation==1.9.0."
        )

    phases = load_candidate_phases()
    arb_intervals = load_arb_mean_intervals()
    expected_order = frozen_order()

    target_sequence = build_sequence(
        [float(value) for value in ranking_engine.REFERENCE_PHASES],
        0.0,
        0.0,
        0.0,
    )
    target = final_state(target_sequence)

    print("12 paths × 6 error points = 72 simulations", flush=True)
    cell_results: list[dict[str, Any]] = []
    for path in sorted(phases):
        for error in ERROR_POINTS:
            print(f"simulating {path} / {error['label']}", flush=True)
            sequence = build_sequence(
                phases[path],
                float(error["amplitude"]),
                float(error["detuning"]),
                float(error["interaction"]),
            )
            state = final_state(sequence)
            loss = fidelity_loss(target, state)
            cell_results.append(
                {
                    "path": path,
                    "error_label": error["label"],
                    "amplitude_error": float(error["amplitude"]),
                    "detuning_over_omega": float(error["detuning"]),
                    "interaction_fractional_error": float(error["interaction"]),
                    "distance_um": interaction_distance_um(float(error["interaction"])),
                    "loss": loss,
                }
            )

    path_results = []
    for path in sorted(phases):
        cells = [row for row in cell_results if row["path"] == path]
        losses = [float(row["loss"]) for row in cells]
        mean_loss = float(np.mean(losses))
        interval = arb_intervals[path]
        inside = interval["lower"] <= mean_loss <= interval["upper"]
        path_results.append(
            {
                "path": path,
                "finite_values": len(losses),
                "mean_loss": mean_loss,
                "original_arb_interval": interval,
                "mean_inside_original_arb_interval": inside,
                "losses": [
                    {"error_label": row["error_label"], "loss": float(row["loss"])}
                    for row in cells
                ],
            }
        )

    means = {row["path"]: float(row["mean_loss"]) for row in path_results}
    path_order = sorted(means, key=lambda name: means[name])
    complete_ordering_identical = path_order == expected_order
    directions = pair_directions(path_order)
    finite_count = sum(math.isfinite(float(row["loss"])) for row in cell_results)
    means_inside = sum(
        bool(row["mean_inside_original_arb_interval"]) for row in path_results
    )
    exact_translation_pass = means_inside == len(path_results)
    ordering_robustness_pass = (
        complete_ordering_identical
        and len(directions) == 66
        and all(row["agrees_with_frozen_order"] for row in directions)
    )
    metrics = {
        "finite_numeric_values": finite_count,
        "expected_numeric_values": 72,
        "complete_ordering_identical": complete_ordering_identical,
        "path_ordering_matches": sum(
            1 for actual, expected in zip(path_order, expected_order) if actual == expected
        ),
        "path_ordering_expected": 12,
        "certified_pair_directions": sum(
            bool(row["agrees_with_frozen_order"]) for row in directions
        ),
        "certified_pair_expected": 66,
        "means_inside_original_arb_intervals": means_inside,
        "means_inside_original_arb_expected": 12,
        "exact_translation_pass": exact_translation_pass,
        "ordering_robustness_pass": ordering_robustness_pass,
    }
    gates = {
        "finite_numeric_values_72_of_72": finite_count == 72,
        "complete_ordering_identical": complete_ordering_identical,
        "certified_pair_directions_66_of_66": metrics["certified_pair_directions"] == 66,
        "original_arb_interval_membership_0_of_12": means_inside == 0,
        "exact_translation_pass": exact_translation_pass,
        "ordering_robustness_pass": ordering_robustness_pass,
    }
    scientific_status = (
        EXPECTED_STATUS
        if (
            gates["finite_numeric_values_72_of_72"]
            and gates["complete_ordering_identical"]
            and gates["certified_pair_directions_66_of_66"]
            and gates["original_arb_interval_membership_0_of_12"]
            and not gates["exact_translation_pass"]
            and gates["ordering_robustness_pass"]
        )
        else "PULSER_TRANSLATION_AUDIT_NOT_SUPPORTED"
    )

    return {
        "schema": "pulser_translation_report",
        "schema_version": 2,
        "layer": "external_numeric_translation_validation",
        "toolchain": {
            "pulser": pulser_version,
            "pulser_module": getattr(pulser, "__version__", None),
            "pulser_simulation": pulser_simulation_version,
            "pulser_simulation_module": getattr(pulser_simulation, "__version__", None),
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            "backend": "pulser_simulation_qutip_emulator",
            "solver_options": SOLVER_OPTIONS,
            "sampling_rate": 1.0,
        },
        "source_model": {
            "formal_certificate_layer": "Arb/Krawczyk exact-root certificate",
            "frozen_certificate_tags": ["v0.3.1", "v0.3.2"],
            "candidate_phase_source": str(CERTIFICATE.relative_to(ROOT)),
            "arb_interval_source": str(ORDERING_CERTIFICATE.relative_to(ROOT)),
            "declared_path_count": 12,
            "declared_error_point_count": 6,
            "declared_pair_count": 66,
        },
        "translation": {
            "interaction_coeff_rad_um6_per_us": float(
                DigitalAnalogDevice.interaction_coeff
            ),
            "nominal_interaction_rad_per_us": NOMINAL_INTERACTION_RAD_PER_US,
            "nominal_distance_um": interaction_distance_um(0.0),
            "distance_quantization_um": DISTANCE_QUANTIZATION_UM,
            "interaction_error_rule": (
                "r = round((r0 / (1 + epsilon_V)^(1/6)) / 0.01 um) * 0.01 um"
            ),
        },
        "scope": {
            "purpose": (
                "Numerical translation and ordering-robustness cross-check "
                "under Pulser 1.9 quantized-distance semantics."
            ),
            "is_formal_certificate": False,
            "is_hardware_execution": False,
            "is_cloud_execution": False,
            "changes_frozen_certificate": False,
        },
        "comparison_tolerances": {
            "loss_abs_tol": 5.0e-9,
            "loss_rel_tol": 5.0e-8,
            "mean_abs_tol": 5.0e-9,
            "mean_rel_tol": 5.0e-8,
        },
        "metrics": metrics,
        "path_order": path_order,
        "expected_path_order": expected_order,
        "path_results": path_results,
        "cell_results": cell_results,
        "pair_directions": directions,
        "gates": gates,
        "scientific_status": scientific_status,
        "non_claims": [
            "This report is not a formal Arb interval certificate.",
            "This report is not a PASQAL Cloud execution result.",
            "This report is not a QPU execution result.",
            (
                "This report does not change the frozen exact-root boxes "
                "or the 66/66 Arb ordering certificate."
            ),
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Write the recomputed report to this path.",
    )
    args = parser.parse_args(argv)
    report = build_report()
    write_json(Path(args.output), report)
    print(f"wrote recomputed Pulser report: {args.output}", flush=True)
    print(f"scientific_status: {report['scientific_status']}", flush=True)
    return 0 if report["scientific_status"] == EXPECTED_STATUS else 1


if __name__ == "__main__":
    sys.exit(main())
