"""Regression tests for the protocol-only v1.1.1 susceptibility freeze."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.verify_dissipative_susceptibility_protocol import (
    EXPECTED_CANONICAL_SHA256,
    PROTOCOL_PATH,
    SUPERSEDED_V1_1_SHA256,
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
        self.assertEqual(self.protocol["schema_version"], "1.1.1")
        self.assertEqual(
            self.protocol["supersedes_protocol_sha256"],
            SUPERSEDED_V1_1_SHA256,
        )
        self.assertEqual(
            self.protocol["canonical_protocol_sha256"],
            EXPECTED_CANONICAL_SHA256,
        )
        self.assertEqual(canonical_protocol_sha256(self.protocol), EXPECTED_CANONICAL_SHA256)

    def test_protocol_only_no_result_files_or_result_keys(self) -> None:
        self.assertTrue(self.protocol["status"]["protocol_only"])
        self.assertFalse(self.protocol["status"]["holdout_computed"])
        self.assertFalse(self.protocol["status"]["outcomes_unlocked"])
        self.assertTrue(self.protocol["status"]["supersedes_v1_1"])
        self.assertTrue(self.protocol["status"]["clarification_only"])
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
        self.assertEqual(gates["holdout_condition_count"], 26)
        self.assertEqual(gates["classification_accuracy_denominator"], 1716)
        self.assertFalse(gates["diagnostic_pairs_decide_pass_fail"])

    def test_prediction_formulas_are_unambiguous(self) -> None:
        formulas = self.protocol["formulas"]
        self.assertEqual(
            formulas["single_channel_point_prediction"],
            "D_hat_ij(lambda) = Delta_ij + chi_ij * lambda",
        )
        self.assertEqual(
            formulas["single_channel_predicted_preserved"],
            "predicted_preserved iff D_hat_ij(lambda) > 0",
        )
        self.assertEqual(
            formulas["single_channel_predicted_flip"],
            "predicted_flip iff D_hat_ij(lambda) <= 0",
        )
        self.assertEqual(
            formulas["joint_additive_first_order_prediction"],
            "D_hat_ij(lambda_r, lambda_phi) = Delta_ij - chi_decay_ij * "
            "lambda_r - chi_dephasing_ij * lambda_phi",
        )
        self.assertIn("frozen discrete holdout grid", formulas["actual_first_flip_scale"])
        self.assertIn("not a claim about the continuous", formulas["actual_first_flip_scale"])

    def test_scoring_algorithms_are_frozen(self) -> None:
        rules = self.protocol["classification_rules"]
        self.assertEqual(
            rules["condition_count"],
            {
                "decay_holdout_conditions": 10,
                "dephasing_holdout_conditions": 10,
                "joint_holdout_conditions": 6,
                "total_holdout_conditions": 26,
            },
        )
        accuracy = rules["pair_direction_classification_accuracy"]
        self.assertEqual(accuracy["denominator"], 1716)
        self.assertIn("Do not remove any pair", accuracy["drop_policy"])
        self.assertEqual(accuracy["predicted_preserved"], "D_hat > 0")
        self.assertEqual(accuracy["predicted_flip"], "D_hat <= 0")

        c_index = rules["harrell_c_index"]
        self.assertEqual(c_index["family_values"], ["decay", "dephasing", "joint"])
        self.assertIn("right-censored", c_index["risk_score"])
        self.assertIn("0.5 concordance", c_index["prediction_ties"])
        self.assertIn("gate fails", c_index["zero_pooled_denominator"])

        factor = rules["factor_of_two_gate"]
        self.assertIn("positive finite lambda_pred", factor["eligible_pair_family"])
        self.assertIn("0.5 * actual_first_flip_lambda", factor["success_rule"])
        self.assertIn("gate fails", factor["zero_pooled_eligible"])

    def test_scope_doc_keeps_post_hoc_boundary(self) -> None:
        text = (
            ROOT / "docs/dissipative_susceptibility_v1_1_scope.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        self.assertIn("protocol-only", normalized)
        self.assertIn("must not run the holdout grid", normalized)
        self.assertIn("supersedes v1.1", normalized)
        self.assertIn("post-hoc v1.1 hypothesis", normalized)
        self.assertIn(EXPECTED_CANONICAL_SHA256, text)


if __name__ == "__main__":
    unittest.main()
