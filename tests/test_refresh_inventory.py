import importlib.util
import unittest
from copy import deepcopy
from decimal import Decimal

from refresh_inventory_fixtures import record
from scripts.aa_public import LEADERBOARD, SourceError


class RefreshInventoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert importlib.util.find_spec('scripts.refresh_inventory') is not None, \
            'Missing feature: pure fresh-inventory reconciliation module'
        global POLICY, DISCLOSURE_PREFIX, classify_record, build_reconciliation
        global blocking_candidates, tracked_public_slugs, source_exit_caveats
        from scripts.refresh_inventory import (POLICY, DISCLOSURE_PREFIX, classify_record,
            build_reconciliation, blocking_candidates, tracked_public_slugs, source_exit_caveats)

    def test_classification_priority_and_exact_states(self):
        cases = [
            (record('paid'), {'state': 'usable_paid', 'reason': None}),
            (record('retired', deprecated=True), {'state': 'retired', 'reason': 'deprecated'}),
            (record('retired', deprecated=True, estimated=True, score=None, cost=None),
             {'state': 'retired', 'reason': 'deprecated'}),
            (record('estimated', estimated=True, score=None, cost=None),
             {'state': 'observed_unusable', 'reason': 'estimated'}),
            (record('score', score=None, cost=None),
             {'state': 'observed_unusable', 'reason': 'missing_score'}),
            (record('cost', cost=None), {'state': 'observed_unusable', 'reason': 'missing_task_cost'}),
            (record('free', cost=0), {'state': 'observed_unusable', 'reason': 'zero_cost'}),
        ]
        for row, expected in cases:
            with self.subTest(row=row):
                before = deepcopy(row)
                self.assertEqual(classify_record(row), expected)
                self.assertEqual(row, before)
        for deprecated in (None, False):
            self.assertEqual(classify_record(record('paid', deprecated=deprecated)),
                             {'state': 'usable_paid', 'reason': None})
        row = record('paid')
        del row['deprecated']
        self.assertEqual(classify_record(row), {'state': 'usable_paid', 'reason': None})

    def test_retired_and_missing_cost_do_not_block(self):
        rows = [record('inkling', cost=None), record('minimax-m2-7', cost=None, deprecated=True),
                record('gpt-6-1-sol', score='51.8332597011541', cost='0.7241670655535033')]
        before = deepcopy(rows)
        previous = {'inkling', 'minimax-m2-7'}
        rec = build_reconciliation(rows, previous)
        self.assertEqual(rec, {
            'policy': 'observed-inventory-v1', 'previous_tracked_slugs': ['inkling', 'minimax-m2-7'],
            'observed_slugs': ['gpt-6-1-sol', 'inkling', 'minimax-m2-7'],
            'tracked_slugs': ['gpt-6-1-sol', 'inkling'], 'retired_slugs': ['minimax-m2-7'],
            'status_by_slug': {
                'inkling': {'state': 'observed_unusable', 'reason': 'missing_task_cost'},
                'minimax-m2-7': {'state': 'retired', 'reason': 'deprecated'},
                'gpt-6-1-sol': {'state': 'usable_paid', 'reason': None}}})
        self.assertEqual(blocking_candidates(rec), {'missing': [], 'unusable': []})
        self.assertEqual(rows, before)
        self.assertEqual(previous, {'inkling', 'minimax-m2-7'})
        self.assertEqual(rows[2]['score'], Decimal('51.8332597011541'))
        self.assertEqual(rows[2]['cost_per_task'], Decimal('0.7241670655535033'))
        self.assertEqual(POLICY, rec['policy'])

    def test_retired_absence_and_active_absence_are_different(self):
        first = build_reconciliation([record('old', deprecated=True), record('active', cost=None)],
                                     {'old', 'active'})
        second = build_reconciliation([record('new')], set(first['tracked_slugs']))
        self.assertEqual(blocking_candidates(second), {'missing': ['active'], 'unusable': []})
        restored = build_reconciliation([record('active'), record('old')], set(first['tracked_slugs']))
        self.assertEqual(restored['tracked_slugs'], ['active', 'old'])
        self.assertEqual(restored['retired_slugs'], [])
        self.assertEqual(blocking_candidates(restored), {'missing': [], 'unusable': []})

    def test_estimated_missing_score_zero_and_unknown_are_precise(self):
        rows = [record('estimated', estimated=True), record('no-score', score=None), record('free', cost=0)]
        rec = build_reconciliation(rows, {'estimated', 'no-score', 'free', 'absent'})
        self.assertEqual(blocking_candidates(rec),
                         {'missing': ['absent'], 'unusable': ['estimated', 'free', 'no-score']})
        self.assertEqual(set(rec), {'policy', 'previous_tracked_slugs', 'observed_slugs',
                                   'tracked_slugs', 'retired_slugs', 'status_by_slug'})

    def test_new_unusable_is_not_tracked_or_blocking(self):
        rows = [record('z'), record('b', cost=None), record('a', score=None),
                record('c', estimated=True), record('retired', deprecated=True), record('free', cost=0)]
        rec = build_reconciliation(rows, {'missing', 'b', 'retired', 'z'})
        self.assertEqual(rec['tracked_slugs'], ['b', 'missing', 'z'])
        self.assertEqual(rec['observed_slugs'], ['a', 'b', 'c', 'free', 'retired', 'z'])
        self.assertEqual(rec['retired_slugs'], ['retired'])
        self.assertEqual(blocking_candidates(rec), {'missing': ['missing'], 'unusable': []})
        for key in ('previous_tracked_slugs', 'observed_slugs', 'tracked_slugs', 'retired_slugs'):
            self.assertEqual(rec[key], sorted(set(rec[key])))

    def test_empty_inventory_keeps_missing_previous_tracked(self):
        self.assertEqual(build_reconciliation([], set()), {
            'policy': 'observed-inventory-v1', 'previous_tracked_slugs': [], 'observed_slugs': [],
            'tracked_slugs': [], 'retired_slugs': [], 'status_by_slug': {}})
        rec = build_reconciliation([], {'old'})
        self.assertEqual(rec['tracked_slugs'], ['old'])
        self.assertEqual(blocking_candidates(rec), {'missing': ['old'], 'unusable': []})

    def test_tracked_reader_uses_new_inventory_instead_of_paid_fallback(self):
        rec = build_reconciliation([record('missing-cost', cost=None), record('old', deprecated=True)],
                                   {'missing-cost', 'old'})
        source = {'reconciliation': rec}
        before = deepcopy(source)
        self.assertEqual(tracked_public_slugs(source, {'old'}), {'missing-cost'})
        self.assertEqual(source, before)
        for legacy in (None, {}, {'inventory': {'slugs': ['ignored']}}):
            fallback = {'legacy'}
            result = tracked_public_slugs(legacy, fallback)
            self.assertEqual(result, {'legacy'})
            result.add('changed')
            self.assertEqual(fallback, {'legacy'})

    def test_new_inventory_invalid_shape_or_policy_never_falls_back(self):
        valid = build_reconciliation([record('paid')], set())
        invalid = [None, [], {}, dict(valid, policy='unknown'), dict(valid, extra=True)]
        for key in valid:
            missing = deepcopy(valid)
            del missing[key]
            invalid.append(missing)
        for key in ('previous_tracked_slugs', 'observed_slugs', 'tracked_slugs', 'retired_slugs'):
            for bad in (None, 'paid', {}, [1], [''], ['paid', 'paid'], ['z', 'a']):
                invalid.append(dict(valid, **{key: bad}))
        for bad in (None, [], {'paid': {}}, {'paid': {'state': 'unknown', 'reason': None}},
                    {'paid': {'state': 'usable_paid', 'reason': 'deprecated'}},
                    {'paid': {'state': 'usable_paid', 'reason': None, 'extra': True}}):
            invalid.append(dict(valid, status_by_slug=bad))
        invalid.extend([dict(valid, observed_slugs=[]), dict(valid, tracked_slugs=[]),
                        dict(valid, retired_slugs=['paid'])])
        for rec in invalid:
            with self.subTest(rec=rec):
                with self.assertRaises(SourceError) as caught:
                    tracked_public_slugs({'reconciliation': rec}, {'fallback'})
                self.assertEqual(caught.exception.code, 'previous_inventory_missing')
                self.assertEqual(caught.exception.url, LEADERBOARD)

    def test_exit_caveats_only_disclose_previous_retired_and_missing_cost_sorted(self):
        rows = [record('z-retired', name='Old', deprecated=True),
                record('a-cost', name='Inkling', cost=None), record('new-retired', deprecated=True),
                record('new-cost', cost=None), record('estimated', estimated=True), record('paid')]
        rec = build_reconciliation(rows, {'z-retired', 'a-cost', 'estimated', 'paid', 'absent'})
        before = deepcopy((rows, rec))
        self.assertEqual(source_exit_caveats(rows, rec), [
            '來源退出：Inkling（a-cost）：當前 task cost 缺值，本次未參戰，未沿用舊價。',
            '來源退出：Old（z-retired）：來源標示淘汰，本次未參戰，已退出後續強制追蹤。'])
        self.assertEqual((rows, rec), before)
        self.assertEqual(DISCLOSURE_PREFIX, '來源退出：')
        self.assertEqual(source_exit_caveats(rows, build_reconciliation(rows, set())), [])
