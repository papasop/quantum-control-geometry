"""Regression tests for the deterministic P0 audit artifact."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
P0_PATH = ROOT / "tests" / "audit_closure" / "p0_preconditioner_nonsingularity.py"

SPEC = importlib.util.spec_from_file_location("p0_preconditioner", P0_PATH)
assert SPEC is not None and SPEC.loader is not None
try:
    P0 = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(P0)
    P0_IMPORT_ERROR = None
except ModuleNotFoundError as exc:
    P0 = None
    P0_IMPORT_ERROR = exc


@unittest.skipIf(P0_IMPORT_ERROR is not None, f"python-flint unavailable: {P0_IMPORT_ERROR}")
class P0DeterministicArtifactTests(unittest.TestCase):
    def test_runtime_inverse_is_not_used(self) -> None:
        source = P0_PATH.read_text(encoding="utf-8")
        self.assertNotIn("np.linalg.inv", source)
        self.assertNotIn("numpy.linalg.inv", source)

    def test_two_regenerations_are_byte_identical(self) -> None:
        first = P0.certificate_bytes(P0.build_certificate())
        second = P0.certificate_bytes(P0.build_certificate())
        self.assertEqual(first, second)

    def test_regenerated_certificate_matches_committed_payload(self) -> None:
        regenerated = P0.certificate_bytes(P0.build_certificate())
        committed = P0.P0_CERTIFICATE.read_bytes()
        self.assertEqual(regenerated, committed)

    def test_default_p0_command_leaves_git_diff_unchanged(self) -> None:
        before = subprocess.run(
            ["git", "diff", "--binary"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        subprocess.run(
            [sys.executable, str(P0_PATH)],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        after = subprocess.run(
            ["git", "diff", "--binary"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        self.assertEqual(after, before)

    def test_changing_one_frozen_inverse_entry_is_detected(self) -> None:
        frozen = json.loads(P0.FROZEN_INVERSE_DATA.read_text(encoding="utf-8"))
        altered = copy.deepcopy(frozen)
        value = float.fromhex(altered["matrices"]["pv01"][0][0])
        altered["matrices"]["pv01"][0][0] = value.hex().replace("1.", "1.1", 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p0_frozen_inverse_hex.json"
            path.write_text(json.dumps(altered, indent=1, sort_keys=True) + "\n")
            with self.assertRaisesRegex(ValueError, "non-canonical float hex"):
                P0.build_certificate(inverse_data_path=path)

    def test_changing_production_preconditioner_entry_is_detected(self) -> None:
        cohort = json.loads(P0.COHORT.read_text(encoding="utf-8"))
        cohort["paths"][0]["point_preconditioner_decimal"][0][0] = "1.0"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cohort.json"
            path.write_text(json.dumps(cohort, indent=1) + "\n")
            with self.assertRaisesRegex(ValueError, "cohort SHA-256"):
                P0.build_certificate(cohort_path=path)

    def test_all_rho_gates_remain_true(self) -> None:
        certificate = P0.build_certificate()
        self.assertTrue(certificate["all_nonsingular"])
        self.assertEqual(len(certificate["results"]), 12)
        for row in certificate["results"]:
            self.assertTrue(row["nonsingular"])
            self.assertLess(float(row["rho_upper"]), 1.0)


if __name__ == "__main__":
    unittest.main()
