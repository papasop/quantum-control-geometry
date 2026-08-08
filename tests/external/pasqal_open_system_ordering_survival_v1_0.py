#!/usr/bin/env python3
"""Open-system ordering-survival audit for quantum-control-geometry v1.0.

Purpose
-------
Stress-test the twelve frozen exact-root controls from
papasop/quantum-control-geometry v0.3.2 under explicitly declared Lindblad
decay and dephasing channels.  This script does *not* modify or extend the
Arb/Krawczyk proof.  It asks how much of the certified unitary-model ordering
survives under an open-system model discrepancy.

Colab installation
-------------------
    %pip install -q "qutip==5.1.1" "numpy==2.0.2" "scipy==1.13.1"

Recommended prospective use
---------------------------
1. Freeze the embedded protocol and record its SHA-256:

    !python pasqal_open_system_ordering_survival_v1_0.py --freeze-only

2. Run the full audit while requiring that frozen hash:

    !python pasqal_open_system_ordering_survival_v1_0.py \
        --expected-protocol-sha <SHA_FROM_STEP_1>

For a faster code/finite-value smoke test:

    !python pasqal_open_system_ordering_survival_v1_0.py --quick

Scientific boundary
-------------------
This is a local QuTiP open-system stress test of a documented two-atom model.
It is not interval arithmetic, not a second proof, not PASQAL Cloud, and not
QPU/hardware evidence.  The dimensionless rate grid is a declared stress
grid, not a claim about calibrated hardware rates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import sys
import time
import urllib.request
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import numpy as np

try:
    import qutip
    from scipy.stats import rankdata, spearmanr
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependencies. In Colab run:\n"
        "%pip install -q 'qutip==5.1.1' 'numpy==2.0.2' 'scipy==1.13.1'"
    ) from exc


VERSION = "1.0"
SOURCE_TAG = "v0.3.2"
SOURCE_BASE = (
    "https://raw.githubusercontent.com/papasop/quantum-control-geometry/"
    f"{SOURCE_TAG}/"
)
KRAWCZYK_PATH = "results/exact_fibre_krawczyk/krawczyk_certificate.json"
ORDERING_PATH = "results/exact_root_ordering/exact_root_ordering_certificate.json"

# Frozen two-atom serialized model, in microsecond/radian units.
OMEGA = 2.0 * math.pi
V_NOMINAL = 4.0 * OMEGA
DT_US = 0.1
N_SEGMENTS = 24
TOTAL_TIME_US = DT_US * N_SEGMENTS

REFERENCE_PHASES = [
    5.395938949660, 4.364190556336, 4.065716153363, 4.362035605699,
    5.384474017704, 1.275621345422, 1.330584917556, 4.407856703296,
    4.811419315138, 4.022090674744, 0.414000889690, 1.067187010905,
    1.401546960667, 3.017636778929, 2.942592144415, 3.205438748314,
    0.757976217375, 5.846203422983, 3.626398737602, 5.777000471280,
    3.048480766333, 4.247669043136, 2.313878941042, 3.714910179805,
]

ERROR_POINTS = [
    {"label": "amp_minus", "amplitude": -0.06, "detuning": 0.00, "interaction": 0.00},
    {"label": "amp_plus", "amplitude": +0.06, "detuning": 0.00, "interaction": 0.00},
    {"label": "det_minus", "amplitude": 0.00, "detuning": -0.04, "interaction": 0.00},
    {"label": "det_plus", "amplitude": 0.00, "detuning": +0.04, "interaction": 0.00},
    {"label": "int_minus", "amplitude": 0.00, "detuning": 0.00, "interaction": -0.05},
    {"label": "int_plus", "amplitude": 0.00, "detuning": 0.00, "interaction": +0.05},
]

# Integrated rates Gamma*T.  These are stress coordinates, not calibrated
# device specifications.  A physical rate in 1/us is severity / TOTAL_TIME_US.
SINGLE_RATE_GRID = [0.0, 1.0e-4, 3.0e-4, 1.0e-3, 3.0e-3, 1.0e-2, 3.0e-2]
JOINT_RATE_GRID = [1.0e-3, 3.0e-3, 1.0e-2, 3.0e-2]
EVALUATION_SEVERITY = 1.0e-2

# Predeclared interpretation gates at integrated severity 0.01.  These are
# empirical stress-test gates; they are not part of the formal certificate.
RHO_GATE = 0.90
PAIR_SURVIVAL_GATE = 60

SOLVER_OPTIONS = {
    "method": "adams",
    "atol": 1.0e-11,
    "rtol": 1.0e-11,
    "nsteps": 100_000,
    "max_step": 0.005,
    "progress_bar": "",
}


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_object(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(obj, handle, indent=2, sort_keys=False, ensure_ascii=False)
        handle.write("\n")


def fetch_json(relative_path: str, source_dir: Path | None = None) -> dict[str, Any]:
    if source_dir is not None:
        with (source_dir / relative_path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    url = SOURCE_BASE + relative_path
    with urllib.request.urlopen(url, timeout=90) as response:
        return json.load(response)


def first_decimal(text: str) -> float:
    match = re.search(
        r"\[([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)", text
    )
    if not match:
        raise ValueError(f"Could not parse Arb endpoint: {text!r}")
    return float(match.group(1))


@dataclass(frozen=True)
class FrozenInputs:
    phases: dict[str, list[float]]
    intervals: dict[str, tuple[float, float]]
    frozen_order: list[str]
    frozen_pairs: list[tuple[str, str]]
    margins: dict[str, float]
    source_hashes: dict[str, str]


def load_frozen_inputs(source_dir: Path | None = None) -> FrozenInputs:
    krawczyk = fetch_json(KRAWCZYK_PATH, source_dir)
    ordering = fetch_json(ORDERING_PATH, source_dir)

    raw_phases = krawczyk["candidate_phases_decimal"]
    phases = {name: [float(x) for x in values] for name, values in raw_phases.items()}
    if sorted(phases) != [f"pv{i:02d}" for i in range(1, 13)]:
        raise RuntimeError("Expected exactly frozen paths pv01..pv12.")
    if any(len(values) != N_SEGMENTS for values in phases.values()):
        raise RuntimeError("Every frozen path must contain 24 phases.")

    intervals: dict[str, tuple[float, float]] = {}
    for row in ordering["path_rows"]:
        interval = row["direct_mean_interval"]
        intervals[row["path"]] = (
            first_decimal(interval["lower"]),
            first_decimal(interval["upper"]),
        )

    frozen_order = sorted(intervals, key=lambda p: sum(intervals[p]) / 2.0)
    frozen_pairs = [
        (row["better"], row["worse"]) for row in ordering["direct_certified_pairs"]
    ]
    if len(frozen_order) != 12 or len(frozen_pairs) != 66:
        raise RuntimeError("Expected 12 ordered paths and 66 certified pairs.")

    margins: dict[str, float] = {}
    for better, worse in frozen_pairs:
        margin = intervals[worse][0] - intervals[better][1]
        if not margin > 0.0:
            raise RuntimeError(f"Nonpositive frozen margin for {better}/{worse}.")
        margins[f"{better}>{worse}"] = margin

    return FrozenInputs(
        phases=phases,
        intervals=intervals,
        frozen_order=frozen_order,
        frozen_pairs=frozen_pairs,
        margins=margins,
        source_hashes={
            "krawczyk_payload_sha256": sha256_object(krawczyk),
            "ordering_payload_sha256": sha256_object(ordering),
        },
    )


def build_protocol(quick: bool) -> dict[str, Any]:
    single_grid = [0.0, 1.0e-2] if quick else SINGLE_RATE_GRID
    joint_grid = [1.0e-2] if quick else JOINT_RATE_GRID
    return {
        "schema": "open_system_ordering_survival_protocol",
        "version": VERSION,
        "source_repository": "papasop/quantum-control-geometry",
        "source_tag": SOURCE_TAG,
        "path_count": 12,
        "segments_per_path": N_SEGMENTS,
        "error_points": ERROR_POINTS,
        "model": {
            "basis": ["gg", "gr", "rg", "rr"],
            "omega_rad_per_us": OMEGA,
            "nominal_interaction_rad_per_us": V_NOMINAL,
            "segment_duration_us": DT_US,
            "total_duration_us": TOTAL_TIME_US,
            "master_equation": "Lindblad GKSL",
            "decay_operator": "sqrt(Gamma_r) |g><r| on each atom",
            "dephasing_operator": "sqrt(2 Gamma_phi) |r><r| on each atom",
            "dephasing_convention": (
                "An isolated g-r coherence decays at rate Gamma_phi."
            ),
        },
        "stress_grid": {
            "coordinate": "integrated rate Gamma*T",
            "single_channel": single_grid,
            "joint_positive_axes": joint_grid,
            "evaluation_severity": EVALUATION_SEVERITY,
            "hardware_calibrated": False,
        },
        "primary_metrics": [
            "Spearman correlation to frozen order",
            "certified pair directions preserved out of 66",
            "top-1 remains top-2",
            "bottom-1 remains bottom-2",
        ],
        "predeclared_empirical_gates_at_evaluation_severity": {
            "spearman_at_least": RHO_GATE,
            "pair_directions_preserved_at_least": PAIR_SURVIVAL_GATE,
            "frozen_best_in_observed_top_2": True,
            "frozen_worst_in_observed_bottom_2": True,
        },
        "strong_gate": "all 66 pair directions preserved",
        "scope": {
            "formal_interval_proof": False,
            "pasqal_cloud": False,
            "qpu_hardware": False,
            "calibrated_device_noise": False,
            "purpose": "open-system model-discrepancy stress test",
        },
        "quick_mode": quick,
        "outcomes_unlocked": False,
    }


# Two-qubit model operators in the ordered basis gg, gr, rg, rr.
I2 = qutip.qeye(2)
X = qutip.Qobj(np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex))
Y = qutip.Qobj(np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex))
N = qutip.Qobj(np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex))
LOWER = qutip.Qobj(np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex))

GX = qutip.tensor(X, I2) + qutip.tensor(I2, X)
GY = qutip.tensor(Y, I2) + qutip.tensor(I2, Y)
NTOT = qutip.tensor(N, I2) + qutip.tensor(I2, N)
NRR = qutip.tensor(N, N)
LOWER_1 = qutip.tensor(LOWER, I2)
LOWER_2 = qutip.tensor(I2, LOWER)
N_1 = qutip.tensor(N, I2)
N_2 = qutip.tensor(I2, N)
GG = qutip.tensor(qutip.basis(2, 0), qutip.basis(2, 0))


def hamiltonian(
    phase: float,
    amplitude_error: float,
    detuning_error: float,
    interaction_error: float,
) -> qutip.Qobj:
    return (
        0.5
        * OMEGA
        * (1.0 + amplitude_error)
        * (math.cos(phase) * GX + math.sin(phase) * GY)
        - OMEGA * detuning_error * NTOT
        + V_NOMINAL * (1.0 + interaction_error) * NRR
    )


def collapse_operators(
    integrated_decay: float, integrated_dephasing: float
) -> list[qutip.Qobj]:
    if integrated_decay < 0.0 or integrated_dephasing < 0.0:
        raise ValueError("Integrated rates must be nonnegative.")
    gamma_r = integrated_decay / TOTAL_TIME_US
    gamma_phi = integrated_dephasing / TOTAL_TIME_US
    ops: list[qutip.Qobj] = []
    if gamma_r > 0.0:
        ops.extend([math.sqrt(gamma_r) * LOWER_1, math.sqrt(gamma_r) * LOWER_2])
    if gamma_phi > 0.0:
        # For L=sqrt(2*gamma_phi)*|r><r|, a single-atom g-r
        # off-diagonal density-matrix element decays at gamma_phi.
        ops.extend([
            math.sqrt(2.0 * gamma_phi) * N_1,
            math.sqrt(2.0 * gamma_phi) * N_2,
        ])
    return ops


def propagate(
    phases: Iterable[float],
    amplitude_error: float = 0.0,
    detuning_error: float = 0.0,
    interaction_error: float = 0.0,
    integrated_decay: float = 0.0,
    integrated_dephasing: float = 0.0,
    initial: qutip.Qobj | None = None,
) -> qutip.Qobj:
    state = qutip.ket2dm(GG) if initial is None else initial
    c_ops = collapse_operators(integrated_decay, integrated_dephasing)
    tlist = [0.0, DT_US]
    for phase in phases:
        h = hamiltonian(
            float(phase), amplitude_error, detuning_error, interaction_error
        )
        state = qutip.mesolve(
            h,
            state,
            tlist,
            c_ops=c_ops,
            e_ops=None,
            options=SOLVER_OPTIONS,
        ).final_state
    return state


def target_state() -> qutip.Qobj:
    # The target is the frozen reference schedule's nominal unitary output.
    rho = propagate(REFERENCE_PHASES)
    values, vectors = rho.eigenstates()
    return vectors[int(np.argmax(values))]


def fidelity_loss(target: qutip.Qobj, rho: qutip.Qobj) -> float:
    overlap = qutip.expect(qutip.ket2dm(target), rho)
    value = float(np.real(overlap))
    if value < -1.0e-8 or value > 1.0 + 1.0e-8:
        raise RuntimeError(f"Unphysical target population {value}.")
    return float(1.0 - min(1.0, max(0.0, value)))


def condition_key(decay: float, dephasing: float) -> str:
    return f"decay={decay:.12g}|dephasing={dephasing:.12g}"


def condition_list(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    single = protocol["stress_grid"]["single_channel"]
    joint = protocol["stress_grid"]["joint_positive_axes"]
    conditions = [{"family": "unitary", "decay": 0.0, "dephasing": 0.0}]
    conditions += [
        {"family": "decay", "decay": float(x), "dephasing": 0.0}
        for x in single
        if x > 0.0
    ]
    conditions += [
        {"family": "dephasing", "decay": 0.0, "dephasing": float(x)}
        for x in single
        if x > 0.0
    ]
    conditions += [
        {"family": "joint", "decay": float(x), "dephasing": float(y)}
        for x in joint
        for y in joint
    ]
    return conditions


def analyse_condition(
    condition: dict[str, Any],
    means: dict[str, float],
    frozen: FrozenInputs,
) -> dict[str, Any]:
    observed_order = sorted(means, key=means.get)
    frozen_rank = {p: i for i, p in enumerate(frozen.frozen_order)}
    observed_rank = {p: i for i, p in enumerate(observed_order)}
    names = sorted(means)
    rho = float(
        spearmanr(
            [frozen_rank[p] for p in names],
            [observed_rank[p] for p in names],
        ).statistic
    )

    pair_rows = []
    for better, worse in frozen.frozen_pairs:
        preserved = means[better] < means[worse]
        pair_rows.append({
            "better": better,
            "worse": worse,
            "certificate_margin": frozen.margins[f"{better}>{worse}"],
            "open_system_difference": means[worse] - means[better],
            "preserved": bool(preserved),
        })

    preserved_count = sum(row["preserved"] for row in pair_rows)
    best = frozen.frozen_order[0]
    worst = frozen.frozen_order[-1]
    return {
        **condition,
        "condition_key": condition_key(condition["decay"], condition["dephasing"]),
        "means": means,
        "observed_order": observed_order,
        "spearman_rho": rho,
        "pair_directions_preserved": preserved_count,
        "pair_directions_total": 66,
        "full_order_preserved": observed_order == frozen.frozen_order,
        "frozen_best_rank_zero_based": observed_rank[best],
        "frozen_worst_rank_zero_based": observed_rank[worst],
        "frozen_best_in_top_2": observed_rank[best] <= 1,
        "frozen_worst_in_bottom_2": observed_rank[worst] >= 10,
        "reversed_pairs": [row for row in pair_rows if not row["preserved"]],
        "pair_rows": pair_rows,
    }


def severity_of(row: dict[str, Any]) -> float:
    if row["family"] == "decay":
        return float(row["decay"])
    if row["family"] == "dephasing":
        return float(row["dephasing"])
    return max(float(row["decay"]), float(row["dephasing"]))


def closest_condition(
    analyses: list[dict[str, Any]], family: str, decay: float, dephasing: float
) -> dict[str, Any] | None:
    candidates = [row for row in analyses if row["family"] == family]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda row: abs(row["decay"] - decay) + abs(row["dephasing"] - dephasing),
    )


def pair_flip_summary(
    analyses: list[dict[str, Any]], frozen: FrozenInputs
) -> list[dict[str, Any]]:
    output = []
    for better, worse in frozen.frozen_pairs:
        key = f"{better}>{worse}"
        family_thresholds: dict[str, Any] = {}
        for family in ("decay", "dephasing", "joint"):
            rows = sorted(
                [row for row in analyses if row["family"] == family],
                key=lambda row: (severity_of(row), row["decay"], row["dephasing"]),
            )
            first = None
            for row in rows:
                pair = next(
                    item
                    for item in row["pair_rows"]
                    if item["better"] == better and item["worse"] == worse
                )
                if not pair["preserved"]:
                    first = {
                        "integrated_decay": row["decay"],
                        "integrated_dephasing": row["dephasing"],
                        "open_system_difference": pair["open_system_difference"],
                    }
                    break
            family_thresholds[family] = first
        output.append({
            "better": better,
            "worse": worse,
            "certificate_margin": frozen.margins[key],
            "first_observed_flip": family_thresholds,
        })
    return output


def margin_flip_association(pair_summary: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for family in ("decay", "dephasing"):
        margins = []
        thresholds = []
        for row in pair_summary:
            flip = row["first_observed_flip"][family]
            if flip is not None:
                margins.append(float(row["certificate_margin"]))
                thresholds.append(
                    float(flip["integrated_decay"] or flip["integrated_dephasing"])
                )
        if len(margins) >= 3 and len(set(thresholds)) >= 2:
            stat = spearmanr(margins, thresholds)
            result[family] = {
                "flipped_pairs_with_observed_threshold": len(margins),
                "spearman_margin_vs_first_flip": float(stat.statistic),
                "pvalue": float(stat.pvalue),
                "censoring_note": (
                    "Pairs not flipped by the maximum grid value are right-censored "
                    "and excluded; this metric is exploratory, not a formal survival model."
                ),
            }
        else:
            result[family] = {
                "flipped_pairs_with_observed_threshold": len(margins),
                "spearman_margin_vs_first_flip": None,
                "pvalue": None,
                "censoring_note": "Insufficient uncensored threshold variation.",
            }
    return result


def run_audit(
    protocol: dict[str, Any],
    frozen: FrozenInputs,
    protocol_sha: str,
) -> dict[str, Any]:
    target = target_state()
    conditions = condition_list(protocol)
    total = len(conditions) * len(frozen.phases) * len(ERROR_POINTS)
    print("=" * 88)
    print("OPEN-SYSTEM ORDERING-SURVIVAL AUDIT v1.0")
    print("=" * 88)
    print(f"source: {SOURCE_TAG}")
    print(f"protocol sha256: {protocol_sha}")
    print(f"conditions: {len(conditions)}")
    print(f"planned density-matrix propagations: {total}")
    print("scope: local QuTiP stress test; not Arb proof; not PASQAL QPU evidence")

    analyses: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []
    completed = 0
    start = time.time()
    for c_index, condition in enumerate(conditions, start=1):
        means: dict[str, float] = {}
        print(
            f"[{c_index:02d}/{len(conditions):02d}] {condition['family']} "
            f"Gamma_r*T={condition['decay']:.4g} "
            f"Gamma_phi*T={condition['dephasing']:.4g}",
            flush=True,
        )
        for path in frozen.frozen_order:
            losses = []
            for error in ERROR_POINTS:
                rho = propagate(
                    frozen.phases[path],
                    amplitude_error=float(error["amplitude"]),
                    detuning_error=float(error["detuning"]),
                    interaction_error=float(error["interaction"]),
                    integrated_decay=float(condition["decay"]),
                    integrated_dephasing=float(condition["dephasing"]),
                )
                loss = fidelity_loss(target, rho)
                if not math.isfinite(loss):
                    raise RuntimeError("Non-finite loss encountered.")
                losses.append(loss)
                completed += 1
                cell_rows.append({
                    "condition_key": condition_key(
                        condition["decay"], condition["dephasing"]
                    ),
                    "family": condition["family"],
                    "integrated_decay": condition["decay"],
                    "integrated_dephasing": condition["dephasing"],
                    "path": path,
                    "error_label": error["label"],
                    "loss": loss,
                })
            means[path] = float(np.mean(losses))
        analysis = analyse_condition(condition, means, frozen)
        analyses.append(analysis)
        print(
            f"    rho={analysis['spearman_rho']:.6f}  "
            f"pairs={analysis['pair_directions_preserved']}/66  "
            f"full_order={analysis['full_order_preserved']}",
            flush=True,
        )

    pair_summary = pair_flip_summary(analyses, frozen)
    evaluation_rows = {
        "decay": closest_condition(
            analyses, "decay", EVALUATION_SEVERITY, 0.0
        ),
        "dephasing": closest_condition(
            analyses, "dephasing", 0.0, EVALUATION_SEVERITY
        ),
        "joint": closest_condition(
            analyses, "joint", EVALUATION_SEVERITY, EVALUATION_SEVERITY
        ),
    }

    empirical_gates: dict[str, Any] = {}
    for name, row in evaluation_rows.items():
        if row is None:
            empirical_gates[name] = {"available": False, "pass": False}
            continue
        tests = {
            "spearman_at_least_0_90": row["spearman_rho"] >= RHO_GATE,
            "at_least_60_of_66_pairs": (
                row["pair_directions_preserved"] >= PAIR_SURVIVAL_GATE
            ),
            "frozen_best_in_top_2": row["frozen_best_in_top_2"],
            "frozen_worst_in_bottom_2": row["frozen_worst_in_bottom_2"],
        }
        empirical_gates[name] = {
            "available": True,
            "condition_key": row["condition_key"],
            "tests": tests,
            "pass": all(tests.values()),
            "strong_66_of_66_gate": row["pair_directions_preserved"] == 66,
        }

    unitary = next(row for row in analyses if row["family"] == "unitary")
    all_finite = completed == total and all(
        math.isfinite(float(row["loss"])) for row in cell_rows
    )
    summary = {
        "planned_propagations": total,
        "completed_propagations": completed,
        "all_finite": all_finite,
        "unitary_reconstruction": {
            "spearman_rho": unitary["spearman_rho"],
            "pair_directions_preserved": unitary["pair_directions_preserved"],
            "full_order_preserved": unitary["full_order_preserved"],
        },
        "evaluation_gates": empirical_gates,
        "all_empirical_evaluation_gates_pass": all(
            row.get("pass", False) for row in empirical_gates.values()
        ),
        "margin_flip_association": margin_flip_association(pair_summary),
        "minimum_certificate_margin": min(frozen.margins.values()),
        "minimum_margin_pair": min(frozen.margins, key=frozen.margins.get),
    }

    status = (
        "OPEN_SYSTEM_STRESS_AUDIT_COMPLETE"
        if all_finite
        else "OPEN_SYSTEM_STRESS_AUDIT_INCOMPLETE"
    )
    elapsed = time.time() - start
    report = {
        "schema": "open_system_ordering_survival_report",
        "schema_version": 1,
        "scientific_status": status,
        "protocol_sha256": protocol_sha,
        "prospective_freeze_verified_by_expected_hash": False,
        "protocol": protocol,
        "source_hashes": frozen.source_hashes,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": __import__("scipy").__version__,
            "qutip": qutip.__version__,
            "elapsed_seconds": elapsed,
        },
        "frozen_order": frozen.frozen_order,
        "certificate_margins": frozen.margins,
        "summary": summary,
        "condition_results": analyses,
        "pair_flip_summary": pair_summary,
        "cell_results": cell_rows,
        "non_claims": [
            "This report is not an Arb or interval certificate.",
            "The stress-rate grid is not calibrated PASQAL hardware noise.",
            "This report is not PASQAL Cloud, FRESNEL, or QPU evidence.",
            "This report does not modify the frozen exact-root theorem.",
        ],
    }
    return report


def print_final(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print("\n" + "=" * 88)
    print("FINAL SUMMARY")
    print("=" * 88)
    print(
        f"propagations: {summary['completed_propagations']}/"
        f"{summary['planned_propagations']}"
    )
    print(f"all finite: {summary['all_finite']}")
    print(
        "unitary reconstruction: "
        f"rho={summary['unitary_reconstruction']['spearman_rho']:.6f}, "
        f"pairs={summary['unitary_reconstruction']['pair_directions_preserved']}/66, "
        f"full_order={summary['unitary_reconstruction']['full_order_preserved']}"
    )
    print(
        "minimum certified margin: "
        f"{summary['minimum_certificate_margin']:.12e} "
        f"({summary['minimum_margin_pair']})"
    )
    for family, gate in summary["evaluation_gates"].items():
        if not gate["available"]:
            print(f"{family}: unavailable")
        else:
            print(
                f"{family} @ evaluation severity: pass={gate['pass']}, "
                f"strong_66/66={gate['strong_66_of_66_gate']}"
            )
    print(f"RESULT: {report['scientific_status']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="pasqal_open_system_ordering_survival_v1_0_report.json",
        help="Machine-readable output report.",
    )
    parser.add_argument(
        "--protocol-output",
        default="pasqal_open_system_ordering_survival_v1_0_protocol.json",
        help="Write the frozen outcome-free protocol here.",
    )
    parser.add_argument(
        "--freeze-only",
        action="store_true",
        help="Write/print the outcome-free protocol and exit.",
    )
    parser.add_argument(
        "--expected-protocol-sha",
        default=None,
        help="Require this pre-recorded protocol SHA-256 before running.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Small stress grid for code/finite-value smoke testing only.",
    )
    parser.add_argument(
        "--source-dir",
        default=None,
        help=(
            "Optional local checkout of quantum-control-geometry v0.3.2. "
            "When omitted, frozen JSON inputs are downloaded from the tag."
        ),
    )
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        print(f"[notice] ignored notebook/kernel arguments: {unknown}")

    protocol = build_protocol(bool(args.quick))
    protocol_sha = sha256_object(protocol)
    write_json(Path(args.protocol_output), protocol)
    print(f"protocol: {args.protocol_output}")
    print(f"protocol sha256: {protocol_sha}")

    if args.expected_protocol_sha is not None:
        if args.expected_protocol_sha != protocol_sha:
            raise SystemExit(
                "Protocol SHA mismatch: refusing to reveal outcomes under a changed protocol."
            )
        freeze_verified = True
    else:
        freeze_verified = False

    if args.freeze_only:
        print("outcomes remain locked; no propagation was run")
        return 0

    source_dir = Path(args.source_dir).resolve() if args.source_dir else None
    frozen = load_frozen_inputs(source_dir)
    report = run_audit(protocol, frozen, protocol_sha)
    report["prospective_freeze_verified_by_expected_hash"] = freeze_verified
    write_json(Path(args.output), report)
    print_final(report)
    print(f"report: {args.output}")
    return 0 if report["scientific_status"] == "OPEN_SYSTEM_STRESS_AUDIT_COMPLETE" else 2


if __name__ == "__main__":
    _exit_code = main()
    # A pasted Colab/Jupyter cell should finish cleanly instead of asking
    # IPython to render SystemExit (which can itself trigger an ultratb bug).
    if "ipykernel" not in sys.modules:
        sys.exit(_exit_code)
