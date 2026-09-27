from math import exp, log, nextafter, inf
from copy import deepcopy
import hashlib
import json
import unittest

from bridge.window_ladder import SelectionError, select_chain, thin_chain, window_strengths
from bridge import window_ladder
from window_fixtures import ROOT, SNAPSHOT, historical_rows, point


class WindowLadderTests(unittest.TestCase):
    def test_interpolated_window_has_known_slope_ratio(self):
        rows = [point(str(s), s, s/exp(.5*(10-s) if s >= 6 else 2+.1*(6-s)))
                for s in (10., 9., 6., 3., 2.)]
        value, support = window_strengths(rows)['6.0']
        self.assertAlmostEqual(value, log(5))
        self.assertEqual(support, 'full_window')
        self.assertEqual(window_strengths(rows)['10.0'], (0., 'neutral_missing_window'))

    def test_highest_score_is_not_pinned(self):
        rows = [point('top', 10., 10.), point('middle', 9., 3.), point('tail', 6., 1.5)]
        kept, trace = thin_chain(rows)
        self.assertEqual([r['identity'] for r in kept], ['middle', 'tail'])
        self.assertEqual(trace[0]['removed'], ['top'])

    def test_equal_score_cost_preserves_frozen_input_order(self):
        a, b = point('route-z', 10., 1.), point('route-a', 10., 1.)
        self.assertEqual(select_chain([a,b], min_score=0, max_cost=None)['chain'][0]['identity'], 'route-z')
        self.assertEqual(select_chain([b,a], min_score=0, max_cost=None)['chain'][0]['identity'], 'route-a')

    def test_replacement_radius_is_strict_without_tolerance(self):
        for score, expected in ((8., ['a', 'b']), (8.0001, ['b'])):
            with self.subTest(score=score):
                kept, _ = thin_chain([point('a', 10, 10), point('b', score, 4)])
                self.assertEqual([r['identity'] for r in kept], expected)

    def test_empty_and_zero_singleton_do_not_take_logs(self):
        for rows in ([], [point('zero', 0, 1)]):
            with self.subTest(rows=rows):
                self.assertEqual(thin_chain(rows), (rows, []))
                result = select_chain(rows, min_score=0, max_cost=None)
                self.assertEqual(result, dict(chain=rows, final=rows, excluded=[], cuts={}, trace=[]))
                self.assertEqual(window_strengths(rows), {
                    r['identity']: (0., 'neutral_missing_window') for r in rows})

    def test_floor_and_adjusted_cost_cap_apply_before_thinning(self):
        good = [point('a', 10, .2), point('b', 8, .1)]
        bad = point('bad', 9, .5)
        result = select_chain([good[0], bad, good[1]], min_score=0, max_cost=.25)
        self.assertEqual(result['final'], good)
        self.assertEqual(result['chain'], good)
        self.assertEqual(result['excluded'][0][0]['identity'], 'bad')
        self.assertIn('over max-cost cap', result['excluded'][0][1])
        filtered = select_chain(good, min_score=11, max_cost=None)
        self.assertEqual(filtered['final'], [])
        self.assertEqual(len(filtered['excluded']), 2)

    def test_exact_window_endpoints_and_straight_log_cp(self):
        rows = [point(str(s), s, s/exp((10-s)/2)) for s in (10., 8., 6.)]
        values = window_strengths(rows)
        self.assertAlmostEqual(values['8.0'][0], 0.)
        self.assertEqual(values['8.0'][1], 'full_window')
        rows[-1] = point('near', 6.0001, 6.0001/exp(2))
        self.assertEqual(window_strengths(rows)['8.0'], (0., 'neutral_missing_window'))

    def test_cp_scaling_does_not_change_strengths_or_selection(self):
        rows = [point(str(s), s, s/exp(.5*(10-s) if s >= 6 else 2+.1*(6-s)))
                for s in (10., 9., 6., 5., 3., 2.)]
        scaled = deepcopy(rows)
        for row in scaled:
            row['_cp'] *= 1000
            row['_cost'] /= 1000
        original_values, scaled_values = window_strengths(rows), window_strengths(scaled)
        for identity, (strength, support) in original_values.items():
            self.assertAlmostEqual(strength, scaled_values[identity][0])
            self.assertEqual(support, scaled_values[identity][1])
        self.assertEqual([r['identity'] for r in thin_chain(rows)[0]],
                         [r['identity'] for r in thin_chain(scaled)[0]])

    def test_nonfinite_chain_numbers_raise_structured_error(self):
        for field in ('_score', '_cp'):
            for number in (float('nan'), float('inf'), -float('inf')):
                with self.subTest(field=field, number=number):
                    rows = [point('a', 10, 10), point('b', 8, 4), point('c', 6, 1)]
                    rows[1][field] = number
                    with self.assertRaises(SelectionError) as caught:
                        window_strengths(rows)
                    self.assertEqual(caught.exception.code, 'selection_numeric')

    def test_nonpositive_log_gains_are_not_clamped(self):
        for cp in (0., -1., 1., .5):
            with self.subTest(cp=cp):
                rows = [point('a', 10, 10), point('b', 8, 4), point('c', 6, 1)]
                rows[1]['_cp'] = cp
                with self.assertRaises(SelectionError) as caught:
                    window_strengths(rows)
                self.assertEqual(caught.exception.code, 'selection_numeric')

    def test_negative_strength_is_valid(self):
        rows = [point('a', 10, 10), point('b', 8, 8/exp(.2)),
                point('c', 6, 6/exp(1.2))]
        self.assertAlmostEqual(window_strengths(rows)['b'][0], log(.2))

    def test_positive_monotone_cp_with_rounded_zero_gain_fails(self):
        rows = [point('a', 10, 10), point('b', 8, 4), point('c', 6, 1)]
        for row, cp in zip(rows, (1e100, nextafter(1e100, inf), 2e100)):
            row['_cp'] = cp
        with self.assertRaises(SelectionError) as caught:
            window_strengths(rows)
        self.assertEqual(caught.exception.code, 'selection_numeric')

    def test_frozen_recalculation_and_returned_rows_cannot_mutate_input(self):
        row = point('a', 10, 1)
        row['_cp'] = -123
        row['audit'] = {'evidence': ['original']}
        original = deepcopy(row)
        result = select_chain([row], min_score=0, max_cost=None)
        self.assertEqual(result['chain'][0]['_cp'], 10)
        result['chain'][0]['audit']['evidence'].append('returned change')
        result['final'][0]['audit']['evidence'].append('another change')
        self.assertEqual(row, original)

    def test_direct_radius_does_not_form_transitive_groups(self):
        rows = [point('a', 10, 10), point('b', 8.5, 4), point('c', 7, 2)]
        kept, trace = thin_chain(rows)
        self.assertEqual([r['identity'] for r in kept], ['a', 'c'])
        self.assertEqual(trace, [dict(step=1, winner='c', strength=0.,
                                     support='neutral_missing_window', removed=['b'])])

    def test_historical_selection_matches_recorded_window_evidence(self):
        rows = historical_rows()
        original = deepcopy(rows)
        self.assertEqual(len(rows), 155)
        self.assertEqual(hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(),
                         'e3916f8405904154f0e1dc648588bb08ce92f483cd616ba9be0ff2e5c726ed22')
        result = select_chain(rows, min_score=0, max_cost=None)
        self.assertEqual(rows, original)
        self.assertEqual((len(result['chain']), len(result['final']), len(result['cuts']),
                          len(result['excluded'])), (19, 10, 9, 136))
        self.assertIn('Muse Spark 1.3 max Meta Contributor',
                      [r['identity'] for r, _ in result['excluded']])
        evidence = json.loads((ROOT / 'experiments/2026-09-27-cp-chain-regularized/result.json').read_text())['modes']['window']
        self.assertEqual([r['identity'] for r in result['final']],
                         [r['identity'] for r in evidence['baseline']])
        current = result['chain'][:]
        self.assertEqual(len(result['trace']), len(evidence['trace']))
        for index, (actual, expected) in enumerate(zip(result['trace'], evidence['trace']), 1):
            self.assertEqual(actual['step'], index)
            self.assertEqual(actual['winner'], expected['winner'])
            self.assertEqual(actual['removed'], expected['removed'])
            self.assertAlmostEqual(actual['strength'], expected['strength'])
            self.assertEqual(actual['support'], 'full_window' if index <= 5 else 'neutral_missing_window')
            winner = next(r for r in current if r['identity'] == actual['winner'])
            for identity in actual['removed']:
                removed = next(r for r in current if r['identity'] == identity)
                self.assertLess(abs(winner['_score'] - removed['_score']), 2.)
            current = [r for r in current if r['identity'] not in actual['removed']]
        self.assertEqual(current, result['final'])
        final_ids = {r['identity'] for r in result['final']}
        self.assertTrue(set(result['cuts'].values()) <= final_ids)
        self.assertTrue(all(a['_score'] - b['_score'] >= 2. and a['_cp'] < b['_cp']
                            for a, b in zip(result['final'], result['final'][1:])))
        result['final'][0]['notes'] = 'changed returned copy'
        self.assertEqual(rows, original)


class WindowCompositionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(getattr(window_ladder, 'calculate_ladder', None)),
                        'Task 2 must expose calculate_ladder')
        self.calculate = window_ladder.calculate_ladder

    def test_anchors_only_use_final_non_claude(self):
        result = self.calculate(historical_rows(), min_score=0, max_cost=None)
        self.assertEqual(result['anchors']['highest_retained_score']['identity'],
                         'GPT-6 Astra xhigh AA-public published-price')
        self.assertEqual(result['anchors']['lowest_retained_cost']['identity'],
                         'GPT-6 Luna low AA-public published-price')
        finals = {r['identity'] for r in result['ladder']}
        self.assertTrue(all(r is None or r['identity'] in finals
                            for r in result['anchors'].values()))

    def test_b_counterfactual_can_change_a_membership_without_mutating_main(self):
        rows = [point('A-high',10,10), point('B-middle',9,1,'B'), point('A-low',6,1)]
        original = deepcopy(rows)
        result = self.calculate(rows, min_score=0, max_cost=None)
        self.assertEqual([r['identity'] for r in result['ladder']], ['B-middle'])
        self.assertEqual(result['grade_b_effects'], [
            {'identity':'A-high','with_b_retained':False,'without_b_retained':True},
            {'identity':'A-low','with_b_retained':False,'without_b_retained':True}])
        self.assertEqual(rows, original)

    def test_all_b_has_valid_empty_counterfactual(self):
        result = self.calculate([point('B-only',9,1,'B')], min_score=0, max_cost=None)
        self.assertEqual(result['grade_b_effects'], [])
        self.assertEqual(result['ladder'][0]['grade'], 'B')

    def test_b_influences_interpolation_even_when_cut_winner_is_a(self):
        rows = [point('B-top',12,12,'B'), point('A-10',10,1),
                point('A-9',9,9/11), point('A-7',7,7/20), point('A-5',5,5/30)]
        result = self.calculate(rows, min_score=0, max_cost=None)
        self.assertEqual(result['selection_trace'][0]['winner'], 'A-10')
        self.assertEqual(result['grade_b_effects'], [
            {'identity':'A-10','with_b_retained':True,'without_b_retained':False},
            {'identity':'A-9','with_b_retained':False,'without_b_retained':True}])

    def test_claude_only_cannot_resurrect_cut_non_claude(self):
        for rows in ([point('Claude test',10,1)],
                     [point('A cut',11,10), point('Claude test',10,1)]):
            with self.subTest(rows=rows):
                result = self.calculate(rows, min_score=0, max_cost=None)
                self.assertEqual(result['anchors'],
                                 dict(highest_retained_score=None, lowest_retained_cost=None))
                self.assertEqual(len(result['ladder']), 1)
                self.assertTrue(result['ladder'][0]['comparison_only'])
                self.assertIsNone(result['ladder'][0]['upgrade'])

    def test_single_non_claude_is_both_anchors_without_upgrade(self):
        result = self.calculate([point('A only',10,1)], min_score=0, max_cost=None)
        row = result['ladder'][0]
        self.assertFalse(row['comparison_only'])
        self.assertIsNone(row['upgrade'])
        self.assertEqual(set(result['anchors']), {'highest_retained_score', 'lowest_retained_cost'})
        for anchor in result['anchors'].values():
            self.assertIs(anchor, row)

    def test_upgrade_has_exact_differences_and_shared_projection(self):
        result = self.calculate([point('upper',10,10), point('lower',7,2)],
                                min_score=0, max_cost=None)
        upper, lower = result['ladder']
        self.assertEqual(upper['upgrade'], dict(cheaper_identity='lower', delta_score=3,
                                               cost_multiple=5, delta_cost_adj=8))
        self.assertIsNone(lower['upgrade'])
        self.assertIs(upper, result['candidate_statuses'][0])
        self.assertIs(upper, result['anchors']['highest_retained_score'])
        self.assertIs(lower, result['anchors']['lowest_retained_cost'])

    def test_upgrade_skips_claude_comparison_row(self):
        result = self.calculate([point('upper',12,12), point('Claude middle',10,5),
                                 point('lower',7,2)], min_score=0, max_cost=None)
        self.assertEqual(len(result['ladder']), 3)
        self.assertEqual(result['ladder'][0]['upgrade'],
                         dict(cheaper_identity='lower', delta_score=5,
                              cost_multiple=6, delta_cost_adj=10))
        self.assertIsNone(result['ladder'][1]['upgrade'])
        self.assertIsNone(result['ladder'][2]['upgrade'])

    def test_floor_excludes_all_but_preserves_statuses(self):
        rows = [point('low',7,2), point('high',10,10)]
        result = self.calculate(rows, min_score=11, max_cost=None)
        self.assertEqual(result['candidate_count'], 2)
        self.assertEqual(result['ladder'], [])
        self.assertEqual(result['chain_identities'], [])
        self.assertEqual(result['selection_trace'], [])
        self.assertEqual(result['anchors'], dict(highest_retained_score=None, lowest_retained_cost=None))
        self.assertEqual([r['identity'] for r in result['candidate_statuses']], ['low', 'high'])
        for row in result['candidate_statuses']:
            self.assertEqual(row['status'], 'excluded')
            self.assertIn('below min-score', row['reason'])
            self.assertIsNone(row['winner'])
            self.assertIsNone(row['upgrade'])

    def test_cap_excluded_b_has_no_effect(self):
        result = self.calculate([point('B capped',12,12,'B'), point('A',10,1)],
                                min_score=0, max_cost=2)
        self.assertEqual(result['grade_b_effects'], [])
        self.assertIn('over max-cost cap', result['candidate_statuses'][0]['reason'])
        self.assertEqual([r['identity'] for r in result['ladder']], ['A'])

    def test_historical_statuses_preserve_full_audit_and_original_prices(self):
        rows = historical_rows()
        original = deepcopy(rows)
        result = self.calculate(rows, min_score=0, max_cost=None)
        statuses = result['candidate_statuses']
        self.assertEqual(result['candidate_count'], 155)
        self.assertEqual([r['identity'] for r in statuses], [r['identity'] for r in rows])
        self.assertEqual([sum(r['status'] == s for r in statuses)
                          for s in ('excluded', 'cut', 'final')], [136, 9, 10])
        self.assertEqual(sum(r['is_grok'] for r in statuses), 9)
        self.assertEqual(sum(r['is_contributor'] for r in statuses), 2)
        final_ids = {r['identity'] for r in result['ladder']}
        for source, row in zip(rows, statuses):
            self.assertEqual(row['cost_orig'], source['_cost_orig'])
            self.assertEqual(row['cp_orig'], source['_cp_orig'])
            self.assertEqual(row['factor'], source['_factor'])
            self.assertEqual(row['source_url'], source['evidence_url'])
            self.assertEqual(row['source_date'], source['checked_date'])
            self.assertEqual(row['notes'], source['notes'])
            if row['status'] == 'cut':
                self.assertEqual(row['reason'], 'within_replacement_radius')
                self.assertIn(row['winner'], final_ids)
            if row['status'] == 'final':
                self.assertIsNone(row['reason'])
                self.assertIsNone(row['winner'])
                self.assertEqual(row, next(r for r in result['ladder'] if r['identity'] == row['identity']))
            else:
                self.assertIsNone(row['upgrade'])
        invalid = next(r for r in statuses if r['identity'] == 'Muse Spark 1.3 max Meta Contributor')
        self.assertEqual(invalid['status'], 'excluded')
        self.assertIsNotNone(invalid['reason'])
        without_invalid = self.calculate([r for r in rows if r['identity'] != invalid['identity']],
                                         min_score=0, max_cost=None)
        self.assertEqual(result['grade_b_effects'], without_invalid['grade_b_effects'])
        self.assertEqual(result['ladder'], without_invalid['ladder'])
        self.assertEqual(rows, original)

    def test_select_anchors_uses_cost_score_and_identity_ties(self):
        rows = [dict(identity=name, score=score, cost_adj=cost, comparison_only=claude)
                for name, score, cost, claude in (
                    ('Claude',20,.1,True), ('expensive',10,5,False),
                    ('z',10,4,False), ('a',10,4,False), ('weak',6,1,False),
                    ('cheap-z',7,1,False), ('cheap-a',7,1,False))]
        anchors = window_ladder.select_anchors(rows)
        self.assertEqual(anchors['highest_retained_score']['identity'], 'a')
        self.assertEqual(anchors['lowest_retained_cost']['identity'], 'cheap-a')
