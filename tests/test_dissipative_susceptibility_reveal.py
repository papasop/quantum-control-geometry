"""Synthetic-only tests for the v1.1.2 reveal scorer.

These tests must never run the real holdout propagation path.
"""

from __future__ import annotations

import json
import importlib.util
import math
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tools.verify_dissipative_susceptibility_protocol import load_protocol
from tools.verify_dissipative_susceptibility_reveal import (
    CLASSIFICATION_DENOMINATOR,
    EXPECTED_PROTOCOL_SHA256,
    MERGED_PROTOCOL_COMMIT,
    factor_of_two_summary,
    family_c_index,
    holdout_conditions,
    predicted_difference,
    score_reveal_payload,
    verify_report,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tests/external/run_dissipative_susceptibility_reveal_v1_1_2.py"


def synthetic_pairs() -> list[dict[str, str]]:
    names = [f"pv{i:02d}" for i in range(1, 13)]
    return [
        {"better": names[i], "worse": names[j]}
        for i in range(len(names))
        for j in range(i + 1, len(names))
    ]


def synthetic_means(names: list[str], family: str, lam: float) -> dict[str, float]:
    means = {}
    for index, name in enumerate(names):
        base = 0.01 * index
        if family == "unitary":
            drift = 0.0
        elif family == "decay":
            drift = -0.2 * index * lam
        elif family == "dephasing":
            drift = -0.1 * index * lam
        else:
            drift = -0.3 * index * lam
        means[name] = base + drift
    return means


class DissipativeSusceptibilityRevealTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = load_protocol()
        self.names = [f"pv{i:02d}" for i in range(1, 13)]
        self.pairs = synthetic_pairs()

    def test_prediction_formula_uses_plus_sign_joint_model(self) -> None:
        condition = {"family": "joint", "decay": 0.25, "dephasing": 0.5}
        value = predicted_difference(1.0, -2.0, -4.0, condition)
        self.assertEqual(value, 1.0 - 0.5 - 2.0)

    def test_full_synthetic_payload_has_1716_denominator(self) -> None:
        training = {
            "unitary": synthetic_means(self.names, "unitary", 0.0),
            "decay:0.0001": synthetic_means(self.names, "decay", 0.0001),
            "decay:0.0003": synthetic_means(self.names, "decay", 0.0003),
            "dephasing:0.0001": synthetic_means(self.names, "dephasing", 0.0001),
            "dephasing:0.0003": synthetic_means(self.names, "dephasing", 0.0003),
        }
        holdouts = []
        for condition in holdout_conditions(self.protocol):
            holdouts.append({
                **condition,
                "means": synthetic_means(
                    self.names,
                    condition["family"],
                    float(condition["lambda"]),
                ),
            })
        metrics = score_reveal_payload(
            protocol=self.protocol,
            pairs=self.pairs,
            training_means=training,
            holdout_means=holdouts,
        )
        self.assertEqual(metrics["classification"]["denominator"], CLASSIFICATION_DENOMINATOR)
        self.assertEqual(CLASSIFICATION_DENOMINATOR, 66 * 26)
        self.assertEqual(len(metrics["pair_condition_rows"]), 1716)
        self.assertEqual(len(metrics["pair_predictions"]), 66 * 3)

        report = {
            "schema": "dissipative_susceptibility_reveal_report",
            "schema_version": "1.1.2",
            "merged_protocol_commit": MERGED_PROTOCOL_COMMIT,
            "executed_commit": "synthetic",
            "source_commit": self.protocol["source_commit"],
            "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
            "protocol": self.protocol,
            "metrics": metrics,
        }
        self.assertIn("scoring denominators: PASS", verify_report(report))

    def test_c_index_handles_censoring_and_prediction_ties(self) -> None:
        rows = [
            {"actual_first_flip": 0.001, "predicted_first_flip": 0.001},
            {"actual_first_flip": 0.002, "predicted_first_flip": 0.001},
            {"actual_first_flip": None, "predicted_first_flip": None},
            {"actual_first_flip": 0.002, "predicted_first_flip": 0.004},
        ]
        result = family_c_index(rows)
        self.assertEqual(result["comparable_count"], 5)
        self.assertTrue(math.isclose(result["concordance_credit"], 4.5))
        self.assertTrue(math.isclose(result["c_index"], 0.9))

    def test_c_index_zero_denominator_is_reported_as_none(self) -> None:
        result = family_c_index([
            {"actual_first_flip": None, "predicted_first_flip": None},
            {"actual_first_flip": None, "predicted_first_flip": 0.001},
        ])
        self.assertEqual(result["comparable_count"], 0)
        self.assertIsNone(result["c_index"])

    def test_factor_of_two_uses_only_actual_flip_positive_prediction_items(self) -> None:
        result = factor_of_two_summary([
            {"actual_first_flip": 0.002, "predicted_first_flip": 0.003},
            {"actual_first_flip": 0.002, "predicted_first_flip": 0.006},
            {"actual_first_flip": None, "predicted_first_flip": 0.001},
            {"actual_first_flip": 0.002, "predicted_first_flip": None},
        ])
        self.assertEqual(result["eligible_count"], 2)
        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["fraction"], 0.5)

    def test_workflow_is_manual_only_when_present(self) -> None:
        workflow = ROOT / ".github/workflows/dissipative_susceptibility_reveal.yml"
        if workflow.exists():
            text = workflow.read_text(encoding="utf-8")
            self.assertIn("workflow_dispatch:", text)
            self.assertNotIn("pull_request:", text)
            self.assertNotIn("push:", text)
            self.assertIn("if: always()", text)
            self.assertIn("set -o pipefail", text)
            self.assertIn(
                "test -s /tmp/dissipative_susceptibility_reveal_v1_1_2_report.json",
                text,
            )
            self.assertIn("python -m tools.verify_dissipative_susceptibility_reveal", text)

    def test_open_system_loader_registers_and_cleans_sys_modules(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        register = "sys.modules[spec.name] = module"
        execute = "spec.loader.exec_module(module)"
        cleanup = "sys.modules.pop(spec.name, None)"
        self.assertIn(register, text)
        self.assertIn(execute, text)
        self.assertIn(cleanup, text)
        self.assertLess(text.index(register), text.index(execute))
        self.assertLess(text.index(execute), text.index(cleanup))

    def test_open_system_module_loads_with_dataclass_registration(self) -> None:
        if importlib.util.find_spec("numpy") is None:
            self.skipTest("numpy unavailable in dependency-light CI")
        from tests.external.run_dissipative_susceptibility_reveal_v1_1_2 import (
            load_open_system_module,
        )

        try:
            module = load_open_system_module()
        except SystemExit as exc:
            self.skipTest(f"open-system dependencies unavailable: {exc}")
        self.assertEqual(module.VERSION, "1.0")
        self.assertTrue(hasattr(module, "FrozenInputs"))
        self.assertIs(sys.modules.get("open_system_v1_0"), module)

    def test_verifier_module_execution_resolves_imports(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.verify_dissipative_susceptibility_reveal",
                "--help",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--report", completed.stdout)

    def test_pipefail_prevents_tee_from_masking_python_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "fail.py"
            log = Path(tmp) / "fail.log"
            script.write_text("raise SystemExit(7)\n", encoding="utf-8")
            command = textwrap.dedent(
                f"""
                set -o pipefail
                {sys.executable} {script} 2>&1 | tee {log}
                """
            )
            completed = subprocess.run(
                ["bash", "-c", command],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 7)


if __name__ == "__main__":
    unittest.main()
