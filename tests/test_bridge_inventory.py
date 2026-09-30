from copy import deepcopy
import hashlib
import json
import unittest

from bridge.inventory import InventoryError, validate_fresh_inventory
from scripts.aa_public import LEADERBOARD
from scripts.refresh_inventory import POLICY, DISCLOSURE_PREFIX
from refresh_inventory_fixtures import record, inventory_bundle, flight


class InventoryProofTests(unittest.TestCase):
    def setUp(self):
        self.previous = {'inkling', 'minimax-m2-7'}
        self.records = [record('inkling', cost=None), record('minimax-m2-7', deprecated=True, cost=None),
                        record('gpt-6-1-sol', score='51.8332597011541', cost='0.7241670655535033')]
        self.data, self.mapping, self.envelope, self.evidence = inventory_bundle(self.records, self.previous)

    def validate(self, data=None, mapping=None, envelope=None, evidence=None, **kwargs):
        validate_fresh_inventory(self.data if data is None else data,
            self.mapping if mapping is None else mapping, self.envelope if envelope is None else envelope,
            error_code='bad-proof', refresh_policy=POLICY,
            evidence=self.evidence if evidence is None else evidence, **kwargs)

    def test_current_cost_exclusion_is_proven_not_invented(self):
        self.validate(expected_previous_slugs=self.previous)
        self.assertEqual(self.envelope['schema_version'], 2)
        for key in ('retired_slugs', 'tracked_slugs', 'observed_slugs'):
            bad = deepcopy(self.mapping)
            bad['reconciliation'][key].append('invented')
            with self.subTest(key=key), self.assertRaises(InventoryError):
                self.validate(mapping=bad, expected_previous_slugs=self.previous)

    def test_decimal_difference_cannot_hide_behind_equal_float(self):
        data, mapping, envelope, evidence = inventory_bundle([record('paid', cost='1.0000000000000000000000001')], set())
        bad_data = data.replace(b'1.0000000000000000000000001', b'1.0000000000000000000000002')
        self.assertNotEqual(data, bad_data)
        self.assertEqual(float('1.0000000000000000000000001'), float('1.0000000000000000000000002'))
        with self.assertRaises(InventoryError):
            self.validate(data=bad_data, mapping=mapping, envelope=envelope, evidence=evidence)

    def test_proof_tampering(self):
        variants = []
        for key in self.evidence:
            bad = dict(self.evidence)
            del bad[key]
            variants.append(bad)
        bad = dict(self.evidence)
        bad['leaderboard.html'] += b'changed'
        variants.append(bad)
        bad = dict(self.evidence)
        bad['sources.json'] = json.dumps({'sha256_by_url': {LEADERBOARD: '0' * 64}}).encode()
        variants.append(bad)
        bad = dict(self.evidence)
        saved = json.loads(bad['leaderboard_records.json'])
        saved[0]['cost_per_task'] = '1'
        bad['leaderboard_records.json'] = json.dumps(saved).encode()
        variants.append(bad)
        for changes in ({'cost_per_task': 0}, {'cost_per_task': 1}, {'is_estimated': True}, {'deprecated': True}):
            records = deepcopy(self.records)
            records[0].update(changes)
            bad = dict(self.evidence)
            bad['leaderboard.html'] = flight(records)
            bad['sources.json'] = json.dumps({'sha256_by_url': {LEADERBOARD: hashlib.sha256(bad['leaderboard.html']).hexdigest()}}).encode()
            variants.append(bad)
        for bad in variants:
            with self.subTest(evidence=bad), self.assertRaises(InventoryError):
                self.validate(evidence=bad)

    def test_reconciliation_shape_reason_previous_and_exclusions(self):
        variants = []
        bad = deepcopy(self.mapping)
        del bad['reconciliation']
        variants.append(bad)
        for key, value in (('policy', True), ('extra', 1), ('previous_tracked_slugs', ['inkling', 'inkling']),
                           ('observed_slugs', [True]), ('retired_slugs', ['minimax-m2-7', 'inkling'])):
            bad = deepcopy(self.mapping)
            bad['reconciliation'][key] = value
            variants.append(bad)
        for value in ({'state': 'observed_unusable', 'reason': 'zero_cost'},
                      {'state': 'observed_unusable', 'reason': True},
                      {'state': 'observed_unusable', 'reason': 'missing_task_cost', 'extra': 1}):
            bad = deepcopy(self.mapping)
            bad['reconciliation']['status_by_slug']['inkling'] = value
            variants.append(bad)
        bad = deepcopy(self.mapping)
        bad['excluded'][0]['reason'] = 'zero_cost'
        variants.append(bad)
        for bad in variants:
            with self.subTest(mapping=bad), self.assertRaises(InventoryError):
                self.validate(mapping=bad)
        with self.assertRaises(InventoryError):
            self.validate(expected_previous_slugs={'invented'})

    def test_missing_or_invented_disclosure_and_dates(self):
        for caveats in ([], self.envelope['caveats'] * 2,
                        self.envelope['caveats'] + [DISCLOSURE_PREFIX + 'invented']):
            bad = deepcopy(self.envelope)
            bad['caveats'] = caveats
            with self.subTest(caveats=caveats), self.assertRaises(InventoryError):
                self.validate(envelope=bad)
        bad = deepcopy(self.envelope)
        bad['source_dates'] = ['2026-09-26']
        with self.assertRaises(InventoryError):
            self.validate(envelope=bad)

    def test_new_map_cannot_downgrade_to_legacy(self):
        with self.assertRaises(InventoryError):
            validate_fresh_inventory(self.data, self.mapping, self.envelope, error_code='bad-proof')
        with self.assertRaises(InventoryError):
            self.validate(evidence={})

    def test_legacy_paid_validation_is_preserved(self):
        legacy = deepcopy(self.mapping)
        del legacy['reconciliation']
        validate_fresh_inventory(self.data, legacy, self.envelope, error_code='bad-proof')
        bad = deepcopy(legacy)
        bad['source_by_slug']['gpt-6-1-sol']['cost_per_task'] = 99
        with self.assertRaises(InventoryError):
            validate_fresh_inventory(self.data, bad, self.envelope, error_code='bad-proof')

    def test_strict_json_rejects_duplicate_keys_constants_and_bad_utf8(self):
        for key in ('sources.json', 'leaderboard_records.json'):
            for value in (b'{"a":1,"a":1}', b'{"a":NaN}', b'{"a":Infinity}', b'\xff'):
                bad = dict(self.evidence)
                bad[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(InventoryError):
                    self.validate(evidence=bad)

    def test_precise_source_map_and_inventory_sets(self):
        variants = []
        for key, value in (('score', '51.833259701154100000001'),
                           ('cost_per_task', '0.72416706555350330000001'),
                           ('checked_date', '2026-09-26'), ('source_url', 'invented')):
            bad = deepcopy(self.mapping)
            bad['source_by_slug']['gpt-6-1-sol'][key] = value
            variants.append(bad)
        bad = deepcopy(self.mapping)
        bad['source_by_slug']['invented'] = bad['source_by_slug']['gpt-6-1-sol']
        variants.append(bad)
        bad = deepcopy(self.mapping)
        bad['inventory']['slugs'].append('invented')
        variants.append(bad)
        bad = deepcopy(self.mapping)
        bad['excluded'].append(bad['excluded'][0])
        variants.append(bad)
        for bad in variants:
            with self.subTest(mapping=bad), self.assertRaises(InventoryError):
                self.validate(mapping=bad)

    def test_untracked_unusable_records_need_no_exit_disclosure(self):
        records = [record('estimated', estimated=True), record('missing', score=None),
                   record('zero', cost='0'), record('paid')]
        data, mapping, envelope, evidence = inventory_bundle(records, set())
        self.validate(data=data, mapping=mapping, envelope=envelope, evidence=evidence)

    def test_blocking_previous_records(self):
        for excluded in (record('inkling', estimated=True), record('inkling', score=None), record('inkling', cost='0')):
            data, mapping, envelope, evidence = inventory_bundle([excluded, record('paid')], {'inkling'})
            with self.subTest(record=excluded), self.assertRaises(InventoryError):
                self.validate(data=data, mapping=mapping, envelope=envelope, evidence=evidence)
        data, mapping, envelope, evidence = inventory_bundle([record('paid')], {'absent'})
        with self.assertRaises(InventoryError):
            self.validate(data=data, mapping=mapping, envelope=envelope, evidence=evidence)
