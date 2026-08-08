#!/usr/bin/env python3
"""Blind prospective Pulser test of response-fibre geometry, v1.0.

This test uses the *pre-outcome frozen* G4 ordering and 20 candidate phase
schedules from quantum-control-geometry v0.3.2.  It then evaluates all twenty
schedules at six finite-error points with Pulser 1.9 (120 propagations) and
reveals whether the frozen geometric prediction orders the Pulser losses.

This is a local Pulser/PASQAL-model blind prospective test.  It is not an Arb
proof, a PASQAL Cloud run, or QPU/hardware evidence.

Colab install:
    %pip install -q "pulser==1.9.0" "pulser-simulation==1.9.0" \
        "numpy==2.0.2" "scipy==1.13.1"

Run:
    !python pasqal_blind_response_fibre_v1_0.py

Optional quick smoke test (4 paths, not a scientific verdict):
    !python pasqal_blind_response_fibre_v1_0.py --quick
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import sys
import urllib.request
import warnings
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import rankdata, spearmanr

try:
    import pulser
    import pulser_simulation
    import qutip
    from pulser import Pulse, Register, Sequence
    from pulser.devices import MockDevice
    from pulser_simulation import QutipEmulator
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing Pulser dependencies. In Colab run:\n"
        "%pip install -q 'pulser==1.9.0' 'pulser-simulation==1.9.0' "
        "'numpy==2.0.2' 'scipy==1.13.1'"
    ) from exc


VERSION = "1.0"
TAG = "v0.3.2"
BASE_URL = (
    "https://raw.githubusercontent.com/papasop/"
    f"quantum-control-geometry/{TAG}/"
)
CERTIFICATE_PATH = "results/g4_prospective/ranking_certificate.json"

OMEGA = 2.0 * math.pi          # rad / us
V_NOMINAL = 4.0 * OMEGA        # rad / us
SEGMENT_NS = 100
NSEG = 24
SEED = 20260808

REFERENCE_PHASES = [
    5.395938949660, 4.364190556336, 4.065716153363, 4.362035605699,
    5.384474017704, 1.275621345422, 1.330584917556, 4.407856703296,
    4.811419315138, 4.022090674744, 0.414000889690, 1.067187010905,
    1.401546960667, 3.017636778929, 2.942592144415, 3.205438748314,
    0.757976217375, 5.846203422983, 3.626398737602, 5.777000471280,
    3.048480766333, 4.247669043136, 2.313878941042, 3.714910179805,
]

# These six finite-error points are frozen before Pulser outcomes are opened.
ERROR_POINTS = [
    (-0.06, 0.00, 0.00),
    (+0.06, 0.00, 0.00),
    (0.00, -0.04, 0.00),
    (0.00, +0.04, 0.00),
    (0.00, 0.00, -0.05),
    (0.00, 0.00, +0.05),
]

SOLVER_OPTIONS = {
    "atol": 1e-12,
    "rtol": 1e-12,
    "max_step": 5,
    "nsteps": 100000,
}

# Predeclared scientific gates.  The quick mode never issues a scientific
# PASS, regardless of its numerical output.
RHO_GATE = 0.80
PERMUTATION_P_GATE = 0.05
N_PERMUTATIONS = 20000
N_BOOTSTRAPS = 20000
GROUP_SIZE = 5


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_object(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def fetch_frozen_certificate() -> dict[str, Any]:
    url = BASE_URL + CERTIFICATE_PATH
    with urllib.request.urlopen(url, timeout=60) as response:
        data = json.load(response)
    required = {
        "protocol_sha256",
        "outcomes_unlocked",
        "predicted_order_best_to_worst",
        "candidate_phases",
    }
    if not required.issubset(data):
        raise RuntimeError("Prospective certificate is missing required fields.")
    if data["outcomes_unlocked"] is not False:
        raise RuntimeError("Expected a pre-outcome frozen prediction certificate.")
    return data


C6 = float(MockDevice.interaction_coeff)


def atom_distance(eps_int: float = 0.0) -> float:
    requested_v = V_NOMINAL * (1.0 + eps_int)
    if requested_v <= 0.0:
        raise ValueError("Interaction multiplier must remain positive.")
    return float((C6 / requested_v) ** (1.0 / 6.0))


def build_sequence(
    phases: list[float],
    eps_amp: float = 0.0,
    eps_det: float = 0.0,
    eps_int: float = 0.0,
) -> Sequence:
    if len(phases) != NSEG:
        raise ValueError(f"Expected {NSEG} phases, received {len(phases)}")
    register = Register(
        {"q0": (0.0, 0.0), "q1": (atom_distance(eps_int), 0.0)}
    )
    sequence = Sequence(register, MockDevice)
    sequence.declare_channel("rydberg", "rydberg_global")
    amplitude = OMEGA * (1.0 + eps_amp)
    detuning = OMEGA * eps_det
    for phase in phases:
        sequence.add(
            Pulse.ConstantPulse(
                duration=SEGMENT_NS,
                amplitude=amplitude,
                detuning=detuning,
                phase=float(phase),
            ),
            "rydberg",
            protocol="no-delay",
        )
    if sequence.get_duration() != NSEG * SEGMENT_NS:
        raise RuntimeError("Unexpected Pulser sequence duration.")
    return sequence


def qutip_vector(state: object) -> np.ndarray:
    if hasattr(state, "full"):
        vector = state.full().reshape(-1)
    elif hasattr(state, "to_qobj"):
        vector = state.to_qobj().full().reshape(-1)
    else:
        vector = np.asarray(state).reshape(-1)
    vector = np.asarray(vector, dtype=complex)
    norm = float(np.linalg.norm(vector))
    if not np.isfinite(norm) or norm == 0.0:
        raise RuntimeError("Pulser returned a non-finite or zero-norm state.")
    return vector / norm


def final_state(
    phases: list[float],
    eps_amp: float = 0.0,
    eps_det: float = 0.0,
    eps_int: float = 0.0,
) -> np.ndarray:
    sequence = build_sequence(phases, eps_amp, eps_det, eps_int)
    emulator = QutipEmulator.from_sequence(
        sequence, sampling_rate=1.0, evaluation_times=[1.0]
    )
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", message="QutipEmulator is deprecated.*",
            category=DeprecationWarning,
        )
        result = emulator.run(**SOLVER_OPTIONS)
    return qutip_vector(result.get_final_state())


def infidelity(target: np.ndarray, state: np.ndarray) -> float:
    value = float(1.0 - abs(np.vdot(target, state)) ** 2)
    if value < -1e-12:
        raise RuntimeError(f"Invalid negative infidelity: {value}")
    return max(0.0, value)


def phase_total_variation(phases: list[float]) -> float:
    values = np.asarray(phases, dtype=float)
    steps = np.angle(np.exp(1j * np.diff(values)))
    return float(np.sum(np.abs(steps)))


def permutation_pvalue(
    predicted_ranks: np.ndarray,
    observed_losses: np.ndarray,
    observed_rho: float,
    rng: np.random.Generator,
) -> float:
    hits = 0
    for _ in range(N_PERMUTATIONS):
        shuffled = rng.permutation(observed_losses)
        rho = float(spearmanr(predicted_ranks, shuffled).statistic)
        if rho >= observed_rho - 1e-15:
            hits += 1
    return float((hits + 1) / (N_PERMUTATIONS + 1))


def bootstrap_group_advantage(
    best_values: np.ndarray,
    worst_values: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, float]:
    # Positive advantage means the predicted-best group has lower loss.
    samples = np.empty(N_BOOTSTRAPS, dtype=float)
    for index in range(N_BOOTSTRAPS):
        best = rng.choice(best_values, size=len(best_values), replace=True)
        worst = rng.choice(worst_values, size=len(worst_values), replace=True)
        samples[index] = float(np.mean(worst) - np.mean(best))
    return {
        "point": float(np.mean(worst_values) - np.mean(best_values)),
        "ci95_lower": float(np.quantile(samples, 0.025)),
        "ci95_upper": float(np.quantile(samples, 0.975)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", default="pasqal_blind_response_fibre_v1_0_report.json"
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Run four paths as a smoke test; never produces scientific PASS.",
    )
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        print("[notice] ignored notebook/kernel arguments:", unknown)

    random.seed(SEED)
    rng = np.random.default_rng(SEED)
    certificate = fetch_frozen_certificate()
    predicted_order = list(certificate["predicted_order_best_to_worst"])
    candidates = certificate["candidate_phases"]

    if len(predicted_order) != 20 or set(predicted_order) != set(candidates):
        raise RuntimeError("Expected exactly twenty frozen prospective paths.")

    selected = predicted_order
    if args.quick:
        # Two predicted-best plus two predicted-worst schedules.
        selected = predicted_order[:2] + predicted_order[-2:]

    freeze_payload = {
        "tag": TAG,
        "source_protocol_sha256": certificate["protocol_sha256"],
        "predicted_order_best_to_worst": predicted_order,
        "candidate_phases": candidates,
        "error_points": ERROR_POINTS,
        "gates": {
            "rho_min": RHO_GATE,
            "permutation_p_max": PERMUTATION_P_GATE,
            "group_size": GROUP_SIZE,
        },
    }
    prediction_freeze_sha256 = sha256_object(freeze_payload)

    print("=" * 92)
    print("PASQAL/PULSER BLIND RESPONSE-FIBRE PROSPECTIVE TEST v1.0")
    print("=" * 92)
    print("scope: local Pulser model test; not Arb proof; not Cloud/QPU evidence")
    print("pulser:", pulser.__version__)
    print("pulser_simulation:", pulser_simulation.__version__)
    print("prediction protocol:", certificate["protocol_sha256"])
    print("prediction freeze sha256:", prediction_freeze_sha256)
    print("outcomes unlocked in source certificate:", certificate["outcomes_unlocked"])
    print("paths:", len(selected), "error points:", len(ERROR_POINTS))
    print("planned propagations:", len(selected) * len(ERROR_POINTS))
    if args.quick:
        print("QUICK MODE: smoke test only; scientific verdict is disabled")

    target = final_state(REFERENCE_PHASES)
    gg = np.array([0.0, 0.0, 0.0, 1.0], dtype=complex)
    reference_return_infidelity = infidelity(gg, target)
    print("reference return infidelity:", f"{reference_return_infidelity:.12e}")

    rows: list[dict[str, Any]] = []
    print("\nPulser reveal")
    for path_index, name in enumerate(selected, start=1):
        phases = [float(value) for value in candidates[name]]
        cells = []
        for error_index, error in enumerate(ERROR_POINTS, start=1):
            state = final_state(phases, *error)
            loss = infidelity(target, state)
            cells.append(loss)
            print(
                f"[{path_index:02d}/{len(selected):02d}] {name} "
                f"[{error_index}/6] error={error} loss={loss:.12f}"
            )
        rows.append({
            "path": name,
            "predicted_rank": predicted_order.index(name) + 1,
            "phase_total_variation": phase_total_variation(phases),
            "cells": cells,
            "mean_loss": float(np.mean(cells)),
        })

    means = {row["path"]: row["mean_loss"] for row in rows}
    observed_order = sorted(selected, key=means.get)
    predicted_ranks = np.asarray(
        [predicted_order.index(name) + 1 for name in selected], dtype=float
    )
    observed_losses = np.asarray([means[name] for name in selected], dtype=float)
    rho = float(spearmanr(predicted_ranks, observed_losses).statistic)
    p_perm = permutation_pvalue(predicted_ranks, observed_losses, rho, rng)

    # Simple, outcome-independent baseline: cyclic phase total variation.
    phase_tv = np.asarray([
        next(row["phase_total_variation"] for row in rows if row["path"] == name)
        for name in selected
    ])
    baseline_rho = float(spearmanr(phase_tv, observed_losses).statistic)

    if args.quick:
        advantage = {"point": None, "ci95_lower": None, "ci95_upper": None}
    else:
        best_names = predicted_order[:GROUP_SIZE]
        worst_names = predicted_order[-GROUP_SIZE:]
        advantage = bootstrap_group_advantage(
            np.asarray([means[name] for name in best_names]),
            np.asarray([means[name] for name in worst_names]),
            rng,
        )

    all_finite = bool(np.all(np.isfinite(observed_losses))) and all(
        np.isfinite(value) for row in rows for value in row["cells"]
    )
    if args.quick:
        gates = {
            "full_120_propagations": False,
            "all_finite": all_finite,
            "spearman_at_least_0_80": False,
            "permutation_p_below_0_05": False,
            "best_vs_worst_ci_above_zero": False,
        }
        verdict = "QUICK_SMOKE_TEST_ONLY"
    else:
        gates = {
            "full_120_propagations": len(rows) == 20 and all(
                len(row["cells"]) == 6 for row in rows
            ),
            "all_finite": all_finite,
            "spearman_at_least_0_80": rho >= RHO_GATE,
            "permutation_p_below_0_05": p_perm < PERMUTATION_P_GATE,
            "best_vs_worst_ci_above_zero": advantage["ci95_lower"] > 0.0,
            "beats_phase_variation_baseline": rho > abs(baseline_rho),
        }
        primary_pass = all([
            gates["full_120_propagations"],
            gates["all_finite"],
            gates["spearman_at_least_0_80"],
            gates["permutation_p_below_0_05"],
            gates["best_vs_worst_ci_above_zero"],
        ])
        verdict = (
            "BLIND_PULSER_RESPONSE_FIBRE_PREDICTION_SUPPORTED"
            if primary_pass else
            "BLIND_PULSER_RESPONSE_FIBRE_PREDICTION_NOT_SUPPORTED"
        )

    report = {
        "audit": "PASQAL_BLIND_RESPONSE_FIBRE_PROSPECTIVE_TEST",
        "version": VERSION,
        "mode": "quick" if args.quick else "full",
        "scientific_status": verdict,
        "claim_boundary": (
            "Blind prospective test in the local Pulser two-atom model; "
            "not an interval proof, PASQAL Cloud run, or QPU result."
        ),
        "source": {
            "repository": "papasop/quantum-control-geometry",
            "tag": TAG,
            "certificate_path": CERTIFICATE_PATH,
            "protocol_sha256": certificate["protocol_sha256"],
            "source_outcomes_unlocked": certificate["outcomes_unlocked"],
            "prediction_freeze_sha256": prediction_freeze_sha256,
        },
        "environment": {
            "python": platform.python_version(),
            "pulser": pulser.__version__,
            "pulser_simulation": pulser_simulation.__version__,
            "qutip": qutip.__version__,
            "numpy": np.__version__,
        },
        "model": {
            "omega_rad_per_us": OMEGA,
            "interaction_rad_per_us": V_NOMINAL,
            "c6": C6,
            "segments": NSEG,
            "segment_ns": SEGMENT_NS,
            "error_points": ERROR_POINTS,
            "solver_options": SOLVER_OPTIONS,
            "reference_return_infidelity": reference_return_infidelity,
        },
        "predeclared_gates": {
            "rho_min": RHO_GATE,
            "permutation_p_max": PERMUTATION_P_GATE,
            "group_size": GROUP_SIZE,
            "permutations": N_PERMUTATIONS,
            "bootstraps": N_BOOTSTRAPS,
        },
        "predicted_order_best_to_worst": predicted_order,
        "selected_paths": selected,
        "observed_order_best_to_worst": observed_order,
        "path_rows": rows,
        "metrics": {
            "propagations": sum(len(row["cells"]) for row in rows),
            "spearman_prediction_vs_pulser": rho,
            "one_sided_permutation_p": p_perm,
            "phase_total_variation_baseline_spearman": baseline_rho,
            "best_vs_worst_mean_loss_advantage": advantage,
        },
        "gates": gates,
    }
    report["report_payload_sha256"] = sha256_object(report)
    Path(args.report).write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print("\n" + "=" * 92)
    print("BLIND REVEAL SUMMARY")
    print("=" * 92)
    print("Predicted order:", " ".join(name for name in predicted_order if name in selected))
    print("Observed order :", " ".join(observed_order))
    print("Spearman rho   :", f"{rho:.6f}")
    print("Permutation p  :", f"{p_perm:.6g}")
    print("Phase-TV rho   :", f"{baseline_rho:.6f}")
    if not args.quick:
        print("Best/worst advantage:", f"{advantage['point']:.6e}")
        print("Bootstrap 95% CI    :", 
              f"[{advantage['ci95_lower']:.6e}, {advantage['ci95_upper']:.6e}]")
    print("Gates:", json.dumps(gates, sort_keys=True))
    print("RESULT:", verdict)
    print("Report:", args.report)
    return 0 if verdict in {
        "BLIND_PULSER_RESPONSE_FIBRE_PREDICTION_SUPPORTED",
        "QUICK_SMOKE_TEST_ONLY",
    } else 1


if __name__ == "__main__":
    code = main()
    if "ipykernel" not in sys.modules:
        sys.exit(code)
