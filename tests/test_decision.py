"""Software-contract fixtures only: no challenge experiment or scientific result."""
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
from invariantcell.decision import POLICIES, digest, evaluate, fit_calibration, freeze_panel, select, verify_decisions


def fixture():
    protocol = {"objective": "reliability_triage", "objective_version": "fixture-v1",
                "budget": 2, "seed": 17, "knowledge_boundary": "2026-01-01T00:00:00Z",
                "strict_historical": False, "reliability_max_error": 0.5,
                "calibration_bin_edges": [0.3], "minimum_calibration_support": 2,
                "fixed_rules": {"max_native_uncertainty": 0.8, "require_supported_evidence": True}, "risk_limit": 0.5}
    model = {"model_hash": "fixture-model", "dependencies": [
        {"name": "fixture-weights", "sha256": "fixture-weight-hash", "available_at": "2025-01-01T00:00:00Z"}]}
    candidates = []
    for index in range(4):
        candidates.append({"candidate_id": f"candidate-{index}", "context_id": f"context-{index % 2}",
            "target_id": f"gene-{index}", "intervention_protocol": "synthetic-fixture-crispri",
            "prediction_score": index * 2.0, "model_hash": "fixture-model", "prediction_hash": f"prediction-{index}",
            "native_uncertainty": (index + 1) / 10, "native_uncertainty_kind": "fixture_standard_deviation",
            "formal_status": "passed", "evidence_status": "supported",
            "evidence_available_at": "2025-12-01T00:00:00Z", "evidence_context_id": f"context-{index % 2}",
            "evidence_snapshot_hash": "fixture-evidence", "supporting_evidence_refs": ["synthetic-fixture-source"]})
    panel = freeze_panel(candidates, protocol, model)
    development = [{"candidate_id": f"development-{i}", "context_id": "development-context", "split": "development",
        "model_hash": "fixture-model", "native_uncertainty": 0.1 if i < 2 else 0.4,
        "native_uncertainty_kind": "fixture_standard_deviation", "agreement_error": 0.1 if i < 2 else 0.9,
        "available_at": "2025-12-01T00:00:00Z"} for i in range(4)]
    outcomes = [{"candidate_id": candidate["candidate_id"], "agreement_error": i / 2}
                for i, candidate in enumerate(candidates)]
    return panel, protocol, development, outcomes


class DecisionContractTests(TestCase):
    def setUp(self):
        self.panel, self.protocol, self.development, self.outcomes = fixture()

    def calibration(self):
        return fit_calibration(self.development, self.panel, self.protocol)

    def test_all_policies_share_frozen_predictions_universe_budget(self):
        calibration, before = self.calibration(), digest(self.panel)
        for policy in POLICIES:
            decision = select(self.panel, self.protocol, policy, calibration)
            self.assertEqual(decision["panel_hash"], self.panel["panel_hash"])
            self.assertEqual(decision["budget"], 2)
            self.assertEqual({r["candidate_id"] for r in decision["records"]}, {r["candidate_id"] for r in self.panel["candidates"]})
            self.assertTrue(verify_decisions(decision, self.panel, self.protocol, calibration))
        self.assertEqual(digest(self.panel), before)

    def test_model_and_protocol_mutations_are_rejected(self):
        self.panel["candidates"][0]["model_hash"] = "another-model"
        with self.assertRaisesRegex(ValueError, "Model hash"):
            select(self.panel, self.protocol, "native")
        self.panel, self.protocol, _, _ = fixture()
        self.protocol["budget"] = 1
        with self.assertRaisesRegex(ValueError, "snapshot"):
            select(self.panel, self.protocol, "native")

    def test_outcomes_and_indirect_features_rejected(self):
        for field in ("actual_outcome", "heldout_delta_summary", "retrieved_outcome_table", "n_cells"):
            panel = deepcopy(self.panel)
            panel["candidates"][0][field] = 123
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "Undeclared/indirect"):
                freeze_panel(panel["candidates"], self.protocol, panel["model_snapshot"])

    def test_selector_has_no_file_or_network_access(self):
        with patch("builtins.open", side_effect=AssertionError("outcome store inaccessible")), patch("socket.socket", side_effect=AssertionError("network inaccessible")):
            decision = select(self.panel, self.protocol, "native")
        self.assertEqual(len(decision["selected_ids"]), 2)

    def test_calibration_rejects_test_rows_and_overlap(self):
        for field, value in (("split", "locked_test"), ("context_id", "context-0"), ("candidate_id", "candidate-0")):
            development = deepcopy(self.development)
            development[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                fit_calibration(development, self.panel, self.protocol)

    def test_calibration_rejects_future_labels_wrong_model_and_kind(self):
        for field, value in (("available_at", "2027-01-01T00:00:00Z"), ("model_hash", "other"), ("native_uncertainty_kind", "another_scale")):
            rows = deepcopy(self.development)
            rows[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                fit_calibration(rows, self.panel, self.protocol)

    def test_unknown_native_confidence_is_never_invented(self):
        for candidate in self.panel["candidates"]:
            candidate["native_uncertainty"] = None
        self.panel = freeze_panel(self.panel["candidates"], self.protocol, self.panel["model_snapshot"])
        decision = select(self.panel, self.protocol, "native")
        self.assertEqual(decision["selected_ids"], ["candidate-0", "candidate-1"])
        for record in decision["records"]:
            self.assertIsNone(record["rank_score"])
            self.assertIsNone(record["risk_estimate"])
            self.assertIn("NO_NATIVE_UNCERTAINTY_UNSCORED_ID_FALLBACK", record["reason_codes"])

    def test_unsupported_calibration_risk_is_null(self):
        calibration = fit_calibration(self.development[:1], self.panel, self.protocol)
        decision = select(self.panel, self.protocol, "calibrated", calibration)
        self.assertEqual(decision["selected_ids"], [])
        self.assertTrue(all(record["risk_estimate"] is None for record in decision["records"]))

    def test_missing_or_extra_outcomes_fail(self):
        decisions = {"native": select(self.panel, self.protocol, "native")}
        for outcomes in (self.outcomes[:-1], self.outcomes + [{"candidate_id": "unexpected", "agreement_error": 0.0}]):
            with self.assertRaisesRegex(ValueError, "Missing/mismatched"):
                evaluate(decisions, self.panel, self.protocol, outcomes)

    def test_all_abstain_has_zero_yield_full_unused_capacity(self):
        decisions = {"calibrated": select(self.panel, self.protocol, "calibrated")}
        report = evaluate(decisions, self.panel, self.protocol, self.outcomes)["policies"]["calibrated"]
        self.assertEqual(report["reliable_yield_at_budget"], 0)
        self.assertIsNone(report["selected_precision"])
        self.assertEqual(report["coverage"], 0)
        self.assertEqual(report["unused_capacity"], 2)

    def test_context_conflict_and_failed_formal_checks_are_not_backfilled(self):
        for candidate in self.panel["candidates"]:
            candidate["formal_status"] = "failed"
            candidate["evidence_context_id"] = "wrong-context"
            candidate["evidence_status"] = "conflicting"
        self.panel = freeze_panel(self.panel["candidates"], self.protocol, self.panel["model_snapshot"])
        decision = select(self.panel, self.protocol, "verification", self.calibration())
        self.assertEqual(decision["selected_ids"], [])
        for record in decision["records"]:
            self.assertEqual(record["disposition"], "INELIGIBLE_UNDER_PROTOCOL")
            self.assertTrue({"FORMAL_CHECK_FAILED", "EVIDENCE_CONTEXT_MISMATCH", "UNRESOLVED_EVIDENCE_CONFLICT"} <= set(record["reason_codes"]))

    def test_later_evidence_and_strict_historical_dependencies_blocked(self):
        self.panel["candidates"][0]["evidence_available_at"] = "2026-01-02T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "information boundary"):
            freeze_panel(self.panel["candidates"], self.protocol, self.panel["model_snapshot"])
        self.panel, self.protocol, _, _ = fixture()
        self.protocol["strict_historical"] = True
        self.panel["model_snapshot"]["dependencies"][0]["available_at"] = "2026-01-02T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "historical boundary"):
            freeze_panel(self.panel["candidates"], self.protocol, self.panel["model_snapshot"])

    def test_self_rehashed_decision_tampering_fails_trusted_replay(self):
        decision = select(self.panel, self.protocol, "native")
        decision["selected_ids"] = ["candidate-3"]
        decision["decision_hash"] = digest({key: value for key, value in decision.items() if key != "decision_hash"})
        with self.assertRaisesRegex(ValueError, "tamper"):
            verify_decisions(decision, self.panel, self.protocol)

    def test_calibration_support_tampering_rejected_even_after_rehash(self):
        calibration = self.calibration()
        calibration["bins"][0]["risk"] = 0.4
        calibration["calibration_hash"] = digest({k: v for k, v in calibration.items() if k != "calibration_hash"})
        with self.assertRaisesRegex(ValueError, "development counts"):
            select(self.panel, self.protocol, "calibrated", calibration)

    def test_no_effect_accuracy_is_not_biological_success(self):
        for outcome in self.outcomes:
            outcome["agreement_error"] = 0.0
        decisions = {"native": select(self.panel, self.protocol, "native")}
        report = evaluate(decisions, self.panel, self.protocol, self.outcomes)
        self.assertEqual(report["policies"]["native"]["selected_precision"], 1)
        self.assertIsNone(report["policies"]["native"]["biological_benefit"])

    def test_paired_uncertainty_uses_contexts_and_rejects_cell_counts(self):
        decisions = {policy: select(self.panel, self.protocol, policy) for policy in ("native", "random")}
        report = evaluate(decisions, self.panel, self.protocol, self.outcomes)
        comparison = report["paired_comparisons"][0]
        self.assertEqual(report["experimental_unit_count"], 4)
        self.assertEqual(comparison["cluster_count"], 2)
        self.assertIsNone(comparison["interval_95"])
        self.outcomes[0]["n_cells"] = 10000
        with self.assertRaises(ValueError):
            evaluate(decisions, self.panel, self.protocol, self.outcomes)

    def test_seed_replay_is_deterministic(self):
        self.assertEqual(select(self.panel, self.protocol, "random"), select(self.panel, self.protocol, "random"))

    def test_nested_indirect_outcome_payload_rejected(self):
        for field in ("evidence_context_id", "evidence_snapshot_hash", "native_uncertainty_kind"):
            panel = deepcopy(self.panel)
            panel["candidates"][0]["evidence_status"] = "missing"
            panel["candidates"][0]["native_uncertainty"] = None
            panel["candidates"][0][field] = {"actual_outcome": 1.0}
            with self.subTest(field=field), self.assertRaises(ValueError):
                freeze_panel(panel["candidates"], self.protocol, panel["model_snapshot"])

    def test_evidence_update_preserves_predictions_and_replays_both_records(self):
        original = select(self.panel, self.protocol, "fixed_rules")
        updated_candidates, updated_protocol = deepcopy(self.panel["candidates"]), deepcopy(self.protocol)
        updated_protocol["knowledge_boundary"] = "2026-02-01T00:00:00Z"
        updated_candidates[0]["evidence_status"] = "conflicting"
        updated_candidates[0]["evidence_available_at"] = "2026-01-15T00:00:00Z"
        updated_candidates[0]["evidence_snapshot_hash"] = "synthetic-fixture-update"
        updated_panel = freeze_panel(updated_candidates, updated_protocol, self.panel["model_snapshot"])
        updated = select(updated_panel, updated_protocol, "fixed_rules")
        self.assertEqual([c["prediction_hash"] for c in self.panel["candidates"]], [c["prediction_hash"] for c in updated_panel["candidates"]])
        self.assertIn("candidate-0", original["selected_ids"])
        self.assertNotIn("candidate-0", updated["selected_ids"])
        self.assertTrue(verify_decisions(original, self.panel, self.protocol))
        self.assertTrue(verify_decisions(updated, updated_panel, updated_protocol))

    def test_partial_abstention_keeps_allocated_budget_denominator(self):
        for candidate in self.panel["candidates"][1:]:
            candidate["formal_status"] = "failed"
        panel = freeze_panel(self.panel["candidates"], self.protocol, self.panel["model_snapshot"])
        decision = select(panel, self.protocol, "fixed_rules")
        report = evaluate({"fixed_rules": decision}, panel, self.protocol, self.outcomes)["policies"]["fixed_rules"]
        self.assertEqual(report["selected_precision"], 1.0)
        self.assertEqual(report["reliable_yield_at_budget"], 0.5)
        self.assertEqual(report["unused_capacity"], 1)
