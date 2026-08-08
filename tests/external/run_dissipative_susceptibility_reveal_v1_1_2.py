#!/usr/bin/env python3
"""Manual v1.1.2 dissipative-susceptibility holdout reveal.

This script is intentionally not used by push or pull-request CI. It is wired
only to a manual `workflow_dispatch` workflow. It verifies the merged protocol
commit and canonical protocol hash before any propagation is started, then
writes the complete reveal report to the requested output path, normally
under `/tmp`.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
MERGED_PROTOCOL_COMMIT = "03055196b5b58d022a5cfcea46b007cb752cea44"
EXPECTED_PROTOCOL_SHA256 = (
    "0c220213ba9485fd06268c56b726848c33b684da10c9d715c96690e9e7ae8476"
)

sys.path.insert(0, str(ROOT))

from tools.verify_dissipative_susceptibility_protocol import (  # noqa: E402
    canonical_protocol_sha256,
    load_protocol,
    verify as verify_protocol,
)
from tools.verify_dissipative_susceptibility_reveal import (  # noqa: E402
    holdout_conditions,
    score_reveal_payload,
    verify_report,
)


OPEN_SYSTEM_PATH = ROOT / "tests/external/pasqal_open_system_ordering_survival_v1_0.py"


def load_open_system_module() -> Any:
    spec = importlib.util.spec_from_file_location("open_system_v1_0", OPEN_SYSTEM_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load open-system v1.0 module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def verify_commit_binding() -> str:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", MERGED_PROTOCOL_COMMIT, "HEAD"],
        check=True,
    )
    return head


def condition_key(family: str, decay: float, dephasing: float) -> str:
    if family == "unitary":
        return "unitary"
    if family == "decay":
        return f"decay:{decay:.12g}"
    if family == "dephasing":
        return f"dephasing:{dephasing:.12g}"
    return f"joint:{decay:.12g}:{dephasing:.12g}"


def compute_means_for_condition(
    *,
    open_system: Any,
    frozen: Any,
    family: str,
    decay: float,
    dephasing: float,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    target = open_system.target_state()
    means: dict[str, float] = {}
    cells: list[dict[str, Any]] = []
    for path in frozen.frozen_order:
        losses: list[float] = []
        for error in open_system.ERROR_POINTS:
            rho = open_system.propagate(
                frozen.phases[path],
                amplitude_error=float(error["amplitude"]),
                detuning_error=float(error["detuning"]),
                interaction_error=float(error["interaction"]),
                integrated_decay=decay,
                integrated_dephasing=dephasing,
            )
            loss = open_system.fidelity_loss(target, rho)
            if not math.isfinite(loss):
                raise RuntimeError("non-finite reveal loss encountered")
            losses.append(float(loss))
            cells.append({
                "family": family,
                "decay": decay,
                "dephasing": dephasing,
                "path": path,
                "error_label": error["label"],
                "loss": float(loss),
            })
        means[path] = float(np.mean(losses))
    return means, cells


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/dissipative_susceptibility_reveal_v1_1_2_report.json"),
    )
    args = parser.parse_args(argv)

    if not str(args.output).startswith("/tmp/"):
        raise SystemExit("reveal output must be written under /tmp")

    print("Verifying merged protocol commit and canonical protocol hash.")
    head = verify_commit_binding()
    messages = verify_protocol()
    for message in messages:
        print(message)
    protocol = load_protocol()
    protocol_sha = canonical_protocol_sha256(protocol)
    if protocol_sha != EXPECTED_PROTOCOL_SHA256:
        raise SystemExit(f"protocol hash mismatch: {protocol_sha}")
    if protocol["canonical_protocol_sha256"] != EXPECTED_PROTOCOL_SHA256:
        raise SystemExit("embedded protocol hash mismatch")

    print("Starting manual holdout reveal. Outcomes become unlocked by this run.")
    open_system = load_open_system_module()
    frozen = open_system.load_frozen_inputs(source_dir=ROOT)

    training_conditions = [
        {"family": "unitary", "decay": 0.0, "dephasing": 0.0},
        {"family": "decay", "decay": 0.0001, "dephasing": 0.0},
        {"family": "decay", "decay": 0.0003, "dephasing": 0.0},
        {"family": "dephasing", "decay": 0.0, "dephasing": 0.0001},
        {"family": "dephasing", "decay": 0.0, "dephasing": 0.0003},
    ]
    reveal_conditions = training_conditions + holdout_conditions(protocol)
    total = len(reveal_conditions) * len(frozen.frozen_order) * len(open_system.ERROR_POINTS)
    print(f"planned reveal propagations: {total}")
    print("scope: manual QuTiP reveal; not Arb proof; not PASQAL QPU evidence")

    training_means: dict[str, dict[str, float]] = {}
    holdout_means: list[dict[str, Any]] = []
    cell_results: list[dict[str, Any]] = []
    start = time.time()
    for index, condition in enumerate(reveal_conditions, start=1):
        family = condition["family"]
        decay = float(condition["decay"])
        dephasing = float(condition["dephasing"])
        print(
            f"[{index:02d}/{len(reveal_conditions):02d}] {family} "
            f"Gamma_r*T={decay:.6g} Gamma_phi*T={dephasing:.6g}",
            flush=True,
        )
        means, cells = compute_means_for_condition(
            open_system=open_system,
            frozen=frozen,
            family=family,
            decay=decay,
            dephasing=dephasing,
        )
        cell_results.extend(cells)
        key = condition_key(family, decay, dephasing)
        if condition in training_conditions:
            training_means[key] = means
        else:
            holdout_means.append({**condition, "means": means})

    pairs = [
        {"better": better, "worse": worse}
        for better, worse in frozen.frozen_pairs
    ]
    metrics = score_reveal_payload(
        protocol=protocol,
        pairs=pairs,
        training_means=training_means,
        holdout_means=holdout_means,
    )
    report = {
        "schema": "dissipative_susceptibility_reveal_report",
        "schema_version": "1.1.2",
        "merged_protocol_commit": MERGED_PROTOCOL_COMMIT,
        "executed_commit": head,
        "source_commit": protocol["source_commit"],
        "protocol_sha256": protocol_sha,
        "protocol": protocol,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": __import__("scipy").__version__,
            "qutip": open_system.qutip.__version__,
            "elapsed_seconds": time.time() - start,
        },
        "training_means": training_means,
        "holdout_means": holdout_means,
        "cell_results": cell_results,
        "metrics": metrics,
        "non_claims": [
            "This reveal is not an Arb interval proof.",
            "This reveal is not calibrated PASQAL hardware noise.",
            "This reveal is not PASQAL Cloud, FRESNEL, or QPU evidence.",
            "This reveal does not modify protocol thresholds or results.",
        ],
    }
    for message in verify_report(report):
        print(message)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"wrote reveal report: {args.output}")
    print(f"RESULT all_gates_pass={metrics['all_gates_pass']}")
    if metrics["failures"]:
        print("failures: " + ", ".join(metrics["failures"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
