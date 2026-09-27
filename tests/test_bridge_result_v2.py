import csv
from collections import Counter
from copy import deepcopy
import hashlib
import tempfile
import unittest
from pathlib import Path

from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE, recompute_data
from bridge.result import calculate_snapshot, make_envelope, validate_envelope
from bridge.result_v2 import calculate_v2, make_v2_envelope

EXECUTION = dict(request_commit_sha='b'*40, run_id='9753', run_attempt=1,
                 run_url='https://github.com/example/actions/runs/9753')


class V2ResultTests(unittest.TestCase):
    def source_envelope(self, rows, parameters=None):
        params = PARAMETERS if parameters is None else parameters
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidates.csv'
            with path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            return make_v2_envelope(dict(recompute_data(), parameters=params), EXECUTION,
                                    calculation=calculate_v2(path, params, PROVENANCE), errors=[])

    def envelope(self, parameters=None):
        params = PARAMETERS if parameters is None else parameters
        return make_v2_envelope(dict(recompute_data(), parameters=params), EXECUTION,
                                calculation=calculate_v2(SNAPSHOT, params, PROVENANCE), errors=[])

    def test_v2_roundtrip_and_partition(self):
        env = self.envelope()
        self.assertEqual(env['schema_version'], 2)
        self.assertNotIn('picks', env)
        self.assertEqual(validate_envelope(env), env)
        self.assertEqual(Counter(r['status'] for r in env['candidate_statuses']),
                         {'final': 10, 'cut': 9, 'excluded': 136})
        self.assertEqual(env['anchors']['highest_retained_score']['identity'],
                         'GPT-6 Astra xhigh AA-public published-price')
        self.assertEqual(env['anchors']['lowest_retained_cost']['identity'],
                         'GPT-6 Luna low AA-public published-price')

    def test_v2_cannot_resurrect_a_cut_as_anchor(self):
        env = self.envelope()
        env['anchors']['highest_retained_score'] = next(
            r for r in env['candidate_statuses'] if r['status'] == 'cut')
        with self.assertRaises(ValueError):
            validate_envelope(env)

    def test_relation_and_numeric_tampering_rejected(self):
        base = self.envelope()
        cut_id = next(r['identity'] for r in base['candidate_statuses'] if r['status'] == 'cut')
        mutations = {
            'boolean schema': lambda e: e.update(schema_version=True),
            'unknown schema': lambda e: e.update(schema_version=3),
            'mixed picks': lambda e: e.update(picks={}),
            'cut winner': lambda e: e['selection_trace'][0].update(winner=cut_id),
            'duplicate removal': lambda e: e['selection_trace'][0]['removed'].append(e['selection_trace'][0]['removed'][0]),
            'missing step': lambda e: e['selection_trace'].pop(),
            'unknown support': lambda e: e['selection_trace'][0].update(support='invented'),
            'neutral strength': lambda e: e['selection_trace'][0].update(support='neutral_missing_window', strength=1),
            'nonfinite strength': lambda e: e['selection_trace'][0].update(strength=float('inf')),
            'bool strength': lambda e: e['selection_trace'][0].update(strength=True),
            'step bool': lambda e: e['selection_trace'][0].update(step=True),
            'out of chain final': lambda e: e['chain_identities'].remove(e['ladder'][0]['identity']),
            'chain order': lambda e: e['chain_identities'].reverse(),
            'duplicate chain': lambda e: e['chain_identities'].append(e['chain_identities'][0]),
            'factor': lambda e: e['candidate_statuses'][0].update(factor=2),
            'cp': lambda e: e['candidate_statuses'][0].update(cp_adj=123),
            'cost': lambda e: e['candidate_statuses'][0].update(cost_adj=123),
            'family': lambda e: e['candidate_statuses'][0].update(is_grok=True),
            'comparison': lambda e: e['ladder'][0].update(comparison_only=False),
            'boolean score': lambda e: e['candidate_statuses'][0].update(score=True),
            'nonfinite score': lambda e: e['candidate_statuses'][0].update(score=float('nan')),
            'negative cost': lambda e: e['candidate_statuses'][0].update(cost_orig=-1),
            'claude upgrade': lambda e: e['ladder'][1]['upgrade'].update(cheaper_identity=e['ladder'][0]['identity']),
            'upgrade delta': lambda e: e['ladder'][1]['upgrade'].update(delta_score=999),
            'fake B effect': lambda e: e.update(grade_b_effects=[dict(identity=e['ladder'][1]['identity'], with_b_retained=False, without_b_retained=True)]),
            'equal B flags': lambda e: e.update(grade_b_effects=[dict(identity=e['ladder'][1]['identity'], with_b_retained=True, without_b_retained=True)]),
            'B identity': lambda e: e.update(grade_b_effects=[dict(identity=next(r['identity'] for r in e['candidate_statuses'] if r['grade']=='B'), with_b_retained=False, without_b_retained=True)]),
            'duplicate B effects': lambda e: e.update(grade_b_effects=[dict(identity=e['ladder'][1]['identity'], with_b_retained=True, without_b_retained=False)] * 2),
            'unsorted B effects': lambda e: e.update(grade_b_effects=[dict(identity=i, with_b_retained=True, without_b_retained=False) for i in sorted((r['identity'] for r in e['ladder'][1:3]), reverse=True)]),
            'bool B flags': lambda e: e.update(grade_b_effects=[dict(identity=e['ladder'][1]['identity'], with_b_retained=1, without_b_retained=False)]),
            'policy': lambda e: e.update(selection_policy='other'),
            'radius': lambda e: e['selection_parameters'].update(replacement_score=3),
            'eps': lambda e: e['eps'].update(cp=.1),
            'count': lambda e: e.update(candidate_count=True),
            'duplicate status': lambda e: e['candidate_statuses'].__setitem__(-1, e['candidate_statuses'][0]),
            'correlation': lambda e: e.update(request_commit_sha='bad'),
            'timestamp': lambda e: e.update(created_at='2026-09-27'),
            'source date': lambda e: e.update(source_dates=['2026-09-25']),
            'parameters': lambda e: e['parameters'].update(gpt_factor=True),
            'empty anchors': lambda e: e.update(anchors={}),
            'malformed trace': lambda e: e.update(selection_trace=[None]),
            'malformed row': lambda e: e['candidate_statuses'].__setitem__(0, None),
            'trace removed order': lambda e: next(s for s in e['selection_trace'] if len(s['removed']) > 1)['removed'].reverse(),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                env = deepcopy(base)
                mutate(env)
                with self.assertRaises(ValueError):
                    validate_envelope(env)

    def test_exact_two_point_cut_distance_is_rejected(self):
        with SNAPSHOT.open(newline='', encoding='utf-8') as f:
            row = next(csv.DictReader(f))
        row.update(model='Example', effort='off', notes='GRADE-A measured')
        env = self.source_envelope([
            dict(row, identity='Example upper', score='10', cost_per_task='10'),
            dict(row, identity='Example lower', score='9', cost_per_task='4.5'),
        ])
        step = env['selection_trace'][0]
        rows = {r['identity']: r for r in env['candidate_statuses']}
        cut = rows[step['removed'][0]]
        cut['score'] = rows[step['winner']]['score'] + 2
        cut['cp_orig'] = cut['score'] / cut['cost_orig']
        cut['cp_adj'] = cut['score'] / cut['cost_adj']
        with self.assertRaisesRegex(ValueError, 'invalid_trace_removal'):
            validate_envelope(env)

    def test_failure_drops_all_calculation_fields(self):
        calc = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)
        request = dict(recompute_data(), parameters={'unparsed': True})
        env = make_v2_envelope(request, EXECUTION, calculation=calc,
                               errors=[dict(code='invalid_request', message='Bad parameters')])
        self.assertEqual(env['status'], 'failed')
        self.assertEqual(env['parameters'], {'unparsed': True})
        for key in set(calc) - {'parameters', 'source_snapshot', 'source_dates'}:
            self.assertNotIn(key, env)
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_envelope(dict(env, **{key: calc[key]}))
        self.assertEqual(validate_envelope(env), env)
        for updates in ({'errors': []}, {'run_attempt': True}, {'source_dates': ['2026-09-26']},
                        {'parameters': []}, {'request_id': ''}, {'picks': {}},
                        {'errors': [dict(code='', message='bad')]}):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                validate_envelope(dict(env, **updates))

    def test_creation_requires_matching_parameters_and_real_calculation(self):
        with self.assertRaisesRegex(ValueError, 'missing_calculation'):
            make_v2_envelope(recompute_data(), EXECUTION, calculation=None, errors=[])
        calc = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)
        with self.assertRaisesRegex(ValueError, 'parameters_mismatch'):
            make_v2_envelope(dict(recompute_data(), parameters=dict(PARAMETERS, min_score=1)),
                             EXECUTION, calculation=calc, errors=[])
        for updates in ({'schema_version': 1}, {'picks': {}}, {'status': 'success'}):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                make_v2_envelope(recompute_data(), EXECUTION, calculation=dict(calc, **updates), errors=[])

    def test_full_window_negative_strength_is_legal(self):
        env = self.envelope()
        step = next(s for s in env['selection_trace'] if s['support'] == 'full_window')
        step['strength'] = -0.5
        self.assertEqual(validate_envelope(env), env)

    def test_v1_defaults_and_legacy_cut_remain_readable(self):
        from bridge import result_v1
        calc, _ = calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)
        env = make_envelope(recompute_data(), EXECUTION, calculation=calc, errors=[])
        self.assertEqual(env['schema_version'], 1)
        self.assertEqual(len(env['ladder']), 16)
        self.assertEqual(set(env['picks']), {'strong', 'middle', 'cheap'})
        self.assertEqual(validate_envelope(env), env)
        with self.assertRaises(ValueError):
            validate_envelope(dict(env, anchors={}))
        old = next(r for r in env['candidate_statuses'] if r['identity']=='Muse Spark 1.3 max Meta Contributor')
        old.update(status='cut', reason='same-score band', winner='GPT-6 Sol max AA-public published-price')
        self.assertNotIn('selection_trace', env)
        self.assertEqual(validate_envelope(env), env)
        self.assertEqual(result_v1.validate_envelope(env), env)

    def test_all_filtered_succeeds_with_empty_anchors(self):
        env = self.envelope(dict(PARAMETERS, min_score=999))
        self.assertEqual(env['ladder'], [])
        self.assertEqual(env['chain_identities'], [])
        self.assertEqual(env['selection_trace'], [])
        self.assertEqual(env['anchors'], dict(highest_retained_score=None, lowest_retained_cost=None))

    def test_source_checks_reject_invalid_rows(self):
        with SNAPSHOT.open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        for name, subset in (
            ('version', [rows[0], dict(rows[1], benchmark_version='wrong')]),
            ('grade C', [dict(rows[0], notes='GRADE-C guessed')]),
            ('duplicate', [rows[0], rows[0]]),
            ('date', [dict(rows[0], checked_date='2026-09-25')]),
            ('url', [dict(rows[0], evidence_url='')]),
            ('empty', []),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as d:
                path = Path(d) / 'candidates.csv'
                with path.open('w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(subset)
                with self.assertRaises(ValueError):
                    calculate_v2(path, PARAMETERS, PROVENANCE)
        with self.assertRaisesRegex(ValueError, 'missing_grade_b_caveat'):
            calculate_v2(SNAPSHOT, PARAMETERS, dict(PROVENANCE, version_status='explicit', caveats=[]))
        acquired = dict(PROVENANCE, source_locator=dict(kind='acquired', path='snapshot/candidates.csv', sha256='0'*64))
        with self.assertRaisesRegex(ValueError, 'source_hash_mismatch'):
            calculate_v2(SNAPSHOT, PARAMETERS, acquired)
        acquired['source_locator']['sha256'] = hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()
        calc = calculate_v2(SNAPSHOT, PARAMETERS, acquired)
        env = make_v2_envelope(dict(recompute_data(), operation='refresh'), EXECUTION,
                               calculation=calc, errors=[])
        self.assertEqual(validate_envelope(env), env)
        with self.assertRaises(ValueError):
            validate_envelope(dict(env, operation='recompute'))

    def test_homogeneous_non_general_source_is_rejected(self):
        with SNAPSHOT.open(newline='', encoding='utf-8') as f:
            rows = [dict(row, benchmark='Coding') for row in csv.DictReader(f)]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidates.csv'
            with path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, 'unsupported_benchmark'):
                calculate_v2(path, PARAMETERS, dict(PROVENANCE, benchmark='Coding'))

    def test_non_general_success_envelope_is_rejected(self):
        env = self.envelope()
        env['benchmark'] = 'Coding'
        with self.assertRaisesRegex(ValueError, 'unsupported_benchmark'):
            validate_envelope(env)

    def test_v1_non_general_history_remains_readable(self):
        calc, _ = calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)
        env = make_envelope(recompute_data(), EXECUTION, calculation=calc, errors=[])
        env['benchmark'] = 'Coding'
        self.assertEqual(validate_envelope(env), env)

    def test_factor_uses_same_identity_predicate_as_source_adjustment(self):
        with SNAPSHOT.open(newline='', encoding='utf-8') as f:
            row = next(r for r in csv.DictReader(f) if r['identity'].startswith('GPT-'))
        row['model'] = 'Display alias'
        env = self.source_envelope([row])
        self.assertEqual(env['ladder'][0]['factor'], 18)

    def test_detached_row_copies_cannot_hide_boolean_numbers(self):
        with SNAPSHOT.open(newline='', encoding='utf-8') as f:
            row = next(csv.DictReader(f))
        row.update(identity='Example paid', model='Example', effort='off',
                   score='1', cost_per_task='1', notes='GRADE-A measured')
        base = self.source_envelope([row])
        for location in ('ladder', 'anchor'):
            with self.subTest(location=location):
                env = deepcopy(base)
                if location == 'ladder':
                    env['ladder'] = deepcopy(env['ladder'])
                    env['ladder'][0]['factor'] = True
                else:
                    env['anchors'] = deepcopy(env['anchors'])
                    env['anchors']['highest_retained_score']['factor'] = True
                with self.assertRaises(ValueError):
                    validate_envelope(env)

    def test_zero_score_singleton_and_claude_only_are_valid(self):
        with SNAPSHOT.open(newline='', encoding='utf-8') as f:
            row = next(r for r in csv.DictReader(f) if 'Claude' in r['identity'])
        row['score'] = '0'
        env = self.source_envelope([row])
        self.assertEqual(len(env['ladder']), 1)
        self.assertEqual(env['ladder'][0]['cp_adj'], 0)
        self.assertEqual(env['anchors'], dict(highest_retained_score=None, lowest_retained_cost=None))
        self.assertIsNone(env['ladder'][0]['upgrade'])


if __name__ == '__main__':
    unittest.main()
