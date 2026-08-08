"""Regression tests for the protocol-only v1.1 susceptibility freeze."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.verify_dissipative_susceptibility_protocol import (
    EXPECTED_CANONICAL_SHA256,
    PROTOCOL_PATH,
    canonical_protocol_sha256,
    verify,
)


ROOT = Path(__file__).resolve().parents[1]


class DissipativeSusceptibilityProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))

    def test_verifier_passes(self) -> None:
        messages = verify()
        self.assertIn("protocol-only freeze flags: PASS", messages)
        self.assertEqual(
            messages[-1],
            f"canonical protocol SHA-256: {EXPECTED_CANONICAL_SHA256}",
        )

    def test_canonical_hash_is_stable(self) -> None:
        self.assertEqual(
            self.protocol["canonical_protocol_sha256"],
            EXPECTED_CANONICAL_SHA256,
        )
        self.assertEqual(canonical_protocol_sha256(self.protocol), EXPECTED_CANONICAL_SHA256)

    def test_protocol_only_no_result_files_or_result_keys(self) -> None:
        self.assertTrue(self.protocol["status"]["protocol_only"])
        self.assertFalse(self.protocol["status"]["holdout_computed"])
        self.assertFalse(self.protocol["status"]["outcomes_unlocked"])
        self.assertFalse(self.protocol["status"]["results_file_expected_in_this_pr"])
        self.assertFalse(
            (ROOT / "results/external/open_system_v1_1/results.json").exists()
        )
        rendered = json.dumps(self.protocol, sort_keys=True)
        for forbidden in (
            "holdout_results",
            "observed_holdout",
            "actual_holdout",
            "pass_fail_result",
            "scientific_status",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_holdout_grid_is_new(self) -> None:
        training = set(
            self.protocol["training_data_policy"]["single_channel_training_lambdas"]
        )
        self.assertEqual(training, {0.0, 0.0001, 0.0003})
        single = set(self.protocol["holdout_grid"]["single_channel_holdout_lambdas"])
        joint = {
            row["decay"] for row in self.protocol["holdout_grid"]["joint_holdout_lambdas"]
        }
        self.assertFalse(single & training)
        self.assertFalse(joint & training)
        self.assertEqual(len(single), 10)
        self.assertEqual(len(joint), 6)

    def test_primary_gates_are_frozen(self) -> None:
        gates = self.protocol["primary_gates"]
        self.assertEqual(gates["lambda_zero_reconstructs_pair_directions"], "66/66")
        self.assertEqual(
            gates["holdout_pair_direction_classification_accuracy_at_least"],
            0.90,
        )
        self.assertEqual(gates["harrell_concordance_index_at_least"], 0.75)
        self.assertEqual(
            gates[
                "factor_of_two_accuracy_for_actual_flips_with_positive_predictions_at_least"
            ],
            0.70,
        )
        self.assertFalse(gates["diagnostic_pairs_decide_pass_fail"])

    def test_scope_doc_keeps_post_hoc_boundary(self) -> None:
        text = (
            ROOT / "docs/dissipative_susceptibility_v1_1_scope.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        self.assertIn("protocol-only", normalized)
        self.assertIn("must not run the holdout grid", normalized)
        self.assertIn("post-hoc v1.1 hypothesis", normalized)
        self.assertIn(EXPECTED_CANONICAL_SHA256, text)


if __name__ == "__main__":
    unittest.main()
