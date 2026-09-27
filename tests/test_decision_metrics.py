import unittest
from invariantcell.decision import select, digest
from invariantcell.decision_metrics import continuous_evaluation
from test_decision import fixture


class ContinuousMetricTests(unittest.TestCase):
    def test_oracle_is_evaluation_only_and_does_not_change_selections(self):
        panel, protocol, _, outcomes = fixture()
        decision = select(panel, protocol, 'native'); before = digest(decision)
        errors = [3., 2., 0., 1.]
        for o, e in zip(outcomes, errors): o['agreement_error'] = e
        r = continuous_evaluation({'native':decision},panel,protocol,outcomes)['policies']['native']
        self.assertEqual(r['selected_mean_error'], 2.5)
        self.assertEqual(r['selected_median_error'], 2.5)
        self.assertEqual(r['oracle_mean_error_at_matched_count'], .5)
        self.assertEqual(r['mean_error_regret_at_matched_count'], 2.)
        self.assertEqual(before, digest(decision))

    def test_missing_outcomes_rejected(self):
        panel, protocol, _, outcomes = fixture()
        d = select(panel,protocol,'native')
        with self.assertRaises(ValueError): continuous_evaluation({'native':d},panel,protocol,outcomes[:-1])

    def test_no_selection_is_not_zero_error_or_oracle_win(self):
        panel, protocol, _, outcomes = fixture()
        from invariantcell.decision import freeze_panel
        protocol['fixed_rules']['max_native_uncertainty'] = 0
        panel = freeze_panel(panel['candidates'],protocol,panel['model_snapshot'])
        d = select(panel,protocol,'fixed_rules')
        r = continuous_evaluation({'fixed_rules':d},panel,protocol,outcomes)['policies']['fixed_rules']
        self.assertIsNone(r['mean_error_regret_at_matched_count'])
        self.assertEqual(r['coverage'],0)
        self.assertEqual(r['unused_capacity'],protocol['budget'])
