import csv
from copy import deepcopy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from bridge.result import calculate_snapshot, make_envelope, validate_envelope
from test_bridge_request import request_data

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'runs/2026-09-26-general-grok16/candidates.csv'
PARAMETERS = request_data()['parameters']
PROVENANCE = {
    'benchmark': 'AA-Intelligence-Index',
    'benchmark_version': 'AA-Intelligence-Index-v4.3.2',
    'version_status': 'inferred', 'cost_basis': 'api',
    'source_dates': ['2026-09-26'],
    'source_locator': {'commit': 'a' * 40, 'path': 'runs/2026-09-26-general-grok16/candidates.csv'},
    'caveats': [
        'Public leaderboard does not label version; v4.3.2 inferred by Grok 4.7 and Muse Spark 1.3 release crosschecks.',
        'Contributor GRADE-B cache-write charged at ordinary input rate; not confirmed by Meta.',
        'GPT ×18 conservatively rounded from personal ~18.9 usage; Grok ×16 user scenario, not measured.',
    ],
}


def recompute_data():
    return dict(request_data(), operation='recompute',
                source_snapshot=PROVENANCE['source_locator'])


class ResultTests(unittest.TestCase):
    def test_snapshot_projection_uses_same_calculation(self):
        payload, report = calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)
        self.assertEqual(len(payload['ladder']), 16)
        self.assertEqual(len(payload['candidate_statuses']), 155)
        self.assertEqual(len([r for r in payload['candidate_statuses'] if r['model'].lower().startswith('grok')]), 9)
        self.assertEqual(len([r for r in payload['candidate_statuses'] if 'Contributor' in r['identity']]), 2)
        self.assertEqual(payload['picks']['strong']['identity'], 'GPT-6 Astra max AA-public published-price')
        self.assertEqual([(payload['picks'][name]['identity'], payload['picks'][name]['score'])
                          for name in ('strong', 'middle', 'cheap')], [
            ('GPT-6 Astra max AA-public published-price', 52.673669395513),
            ('GPT-6 Sol high AA-public published-price', 42.8215513642985),
            ('GPT-6 Luna low AA-public published-price', 20.9225480080866)])
        self.assertIn(payload['picks']['strong']['identity'], report)
        for label, key in (('攻堅', 'strong'), ('平衡', 'middle'), ('省錢', 'cheap')):
            self.assertIn(f'- {label}：{payload["picks"][key]["identity"]}（S=', report)
        self.assertEqual(payload['version_status'], 'inferred')
        self.assertEqual([r['status'] for r in payload['ladder']], ['final'] * 16)
        self.assertEqual({r['status'] for r in payload['candidate_statuses']}, {'final', 'cut', 'excluded'})
        self.assertEqual(payload['source_snapshot'], PROVENANCE['source_locator'])
        json.dumps(payload, allow_nan=False)

    def test_rejects_claude_only_and_empty_paid(self):
        with SNAPSHOT.open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        for subset in ([next(r for r in rows if 'Claude' in r['identity'])], []):
            with tempfile.TemporaryDirectory() as d:
                file = Path(d) / 'candidates.csv'
                with file.open('w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(subset)
                if subset:
                    payload, _ = calculate_snapshot(file, PARAMETERS, PROVENANCE)
                    self.assertEqual(payload['picks'], {'strong': None, 'middle': None, 'cheap': None})
                    env = make_envelope(recompute_data(), dict(request_commit_sha='b'*40,
                        run_id='123', run_attempt=1, run_url='https://github.com/example/actions/runs/123'),
                        calculation=payload, errors=[])
                    self.assertEqual(env['status'], 'success')
                else:
                    with self.assertRaisesRegex(ValueError, 'empty_paid'):
                        calculate_snapshot(file, PARAMETERS, PROVENANCE)

    def test_rejects_mixed_version_unknown_grade_and_missing_provenance(self):
        with SNAPSHOT.open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        for mutation in ('version', 'grade'):
            with tempfile.TemporaryDirectory() as d:
                file = Path(d) / 'candidates.csv'
                selected = [dict(rows[0]), dict(rows[1])]
                selected[1]['benchmark_version' if mutation == 'version' else 'notes'] = 'wrong'
                with file.open('w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(selected)
                with self.assertRaises(ValueError):
                    calculate_snapshot(file, PARAMETERS, PROVENANCE)
        with self.assertRaises(ValueError):
            calculate_snapshot(SNAPSHOT, PARAMETERS, {k: v for k, v in PROVENANCE.items() if k != 'source_locator'})

    def test_envelope_success_and_failure_correlation(self):
        calc, _ = calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)
        request = recompute_data()
        execution = {'request_commit_sha': 'b' * 40, 'run_id': '9753', 'run_attempt': 2,
                     'run_url': 'https://github.com/example/actions/runs/9753'}
        success = make_envelope(request, execution, calculation=calc, errors=[])
        self.assertEqual(success['created_at'], request['created_at'])
        self.assertEqual(success['source_snapshot'], PROVENANCE['source_locator'])
        self.assertEqual(success['picks'], calc['picks'])
        self.assertEqual(success['run_attempt'], 2)
        self.assertEqual(validate_envelope(success), success)
        failed = make_envelope(request, execution, calculation=calc, errors=[{'code': 'bad_source', 'message': 'mismatch'}])
        self.assertEqual(failed['status'], 'failed')
        self.assertNotIn('picks', failed)
        self.assertNotIn('ladder', failed)
        self.assertEqual(validate_envelope(failed), failed)
        with self.assertRaises(ValueError):
            validate_envelope(dict(failed, picks=calc['picks']))

    def test_operation_requires_matching_success_locator(self):
        calc, _ = calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)
        execution = dict(request_commit_sha='b' * 40, run_id='9753', run_attempt=2,
                         run_url='https://github.com/example/actions/runs/9753')
        acquired = {'kind': 'acquired', 'path': 'snapshot/candidates.csv',
                    'sha256': hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()}
        refresh = make_envelope(request_data(), execution,
                                calculation=dict(calc, source_snapshot=acquired), errors=[])
        self.assertEqual(refresh['source_snapshot'], acquired)
        recompute_request = recompute_data()
        recompute = make_envelope(recompute_request, execution, calculation=calc, errors=[])
        self.assertEqual(recompute['source_snapshot'], PROVENANCE['source_locator'])
        for envelope in (dict(refresh, source_snapshot=PROVENANCE['source_locator']),
                         dict(recompute, source_snapshot=acquired)):
            with self.subTest(operation=envelope['operation']), self.assertRaises(ValueError):
                validate_envelope(envelope)

    def test_envelope_rejects_hollow_success_and_inconsistent_rows(self):
        calc, _ = calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)
        base = make_envelope(recompute_data(), dict(request_commit_sha='b' * 40, run_id='9753',
                             run_attempt=2, run_url='https://github.com/example/actions/runs/9753'),
                             calculation=calc, errors=[])
        mutations = (
            lambda e: e.update(request_id=''),
            lambda e: e.update(ladder=[], candidate_statuses=[], picks=dict.fromkeys(('strong','middle','cheap'))),
            lambda e: e['ladder'].reverse(),
            lambda e: e['candidate_statuses'].pop(),
            lambda e: e['picks'].update(strong=None),
            lambda e: e['picks'].update(cheap=e['candidate_statuses'][-1]),
            lambda e: e['candidate_statuses'][0].update(status='surprise'),
            lambda e: e.update(errors=[{'code': 'x', 'message': 'y'}]),
            lambda e: e.update(source_dates=['yesterday']),
            lambda e: e['ladder'][0].update(score=float('nan')),
            lambda e: e.update(candidate_count=True),
            lambda e: e.update(run_attempt=True),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                damaged = deepcopy(base)
                mutation(damaged)
                with self.assertRaises(ValueError):
                    validate_envelope(damaged)

    def test_failure_accepts_unvalidated_params_but_requires_safe_errors(self):
        r = request_data()
        r['parameters'] = {'unparsed': True}
        execution = dict(request_commit_sha='b' * 40, run_id='123', run_attempt=1,
                         run_url='https://github.com/example/actions/runs/123')
        failed = make_envelope(r, execution, calculation=None,
                               errors=[{'code': 'invalid_request', 'message': 'Bad parameters'}])
        self.assertEqual(failed['parameters'], {'unparsed': True})
        for errors in ([], [{'code': '', 'message': 'bad'}], [{'code': 'bad'}], ['bad']):
            with self.subTest(errors=errors), self.assertRaises(ValueError):
                validate_envelope(dict(failed, errors=errors))

    def test_acquired_locator_checks_hash_and_provenance_semantics(self):
        acquired = deepcopy(PROVENANCE)
        acquired['source_locator'] = {'kind': 'acquired', 'path': 'snapshot/candidates.csv',
                                      'sha256': hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()}
        payload, _ = calculate_snapshot(SNAPSHOT, PARAMETERS, acquired)
        self.assertEqual(payload['source_snapshot'], acquired['source_locator'])
        for bad in ({'commit': 'oops', 'path': PROVENANCE['source_locator']['path']},
                    {'commit': 'a' * 40, 'path': '../secret.csv'},
                    {'commit': 'a' * 40, 'path': None},
                    {'commit': 'a' * 40, 'path': 42},
                    {'commit': 'a' * 40, 'path': 'results/not-a-uuid/123-1/snapshot/candidates.csv'},
                    {'kind': 'acquired', 'path': 'snapshot/candidates.csv', 'sha256': '0' * 64}):
            with self.subTest(locator=bad), self.assertRaises(ValueError):
                calculate_snapshot(SNAPSHOT, PARAMETERS, dict(PROVENANCE, source_locator=bad))
        for updates in ({'version_status': 'unknown'}, {'source_dates': ['2026-15-50']},
                        {'caveats': []}):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                calculate_snapshot(SNAPSHOT, PARAMETERS, dict(PROVENANCE, **updates))
        with self.assertRaisesRegex(ValueError, 'missing_grade_b_caveat'):
            calculate_snapshot(SNAPSHOT, PARAMETERS, dict(PROVENANCE, version_status='explicit', caveats=[]))
        pinned = dict(PROVENANCE, source_locator={
            'commit': 'a' * 40,
            'path': 'results/c49aef65-50dd-4fc2-b2f2-8ecccf4ff24d/123-1/snapshot/candidates.csv'})
        self.assertEqual(calculate_snapshot(SNAPSHOT, PARAMETERS, pinned)[0]['source_snapshot'], pinned['source_locator'])

    def test_all_filtered_is_valid_success_and_flags_follow_math_predicates(self):
        params = dict(PARAMETERS, min_score=999)
        payload, _ = calculate_snapshot(SNAPSHOT, params, PROVENANCE)
        self.assertEqual(payload['ladder'], [])
        self.assertEqual(set(r['status'] for r in payload['candidate_statuses']), {'excluded'})
        self.assertEqual(payload['picks'], dict.fromkeys(('strong', 'middle', 'cheap')))
        self.assertEqual(sum(r['is_grok'] for r in payload['candidate_statuses']), 9)
        self.assertEqual(sum(r['is_contributor'] for r in payload['candidate_statuses']), 2)
        env = make_envelope(dict(recompute_data(), parameters=params),
                            dict(request_commit_sha='b'*40, run_id='123', run_attempt=1,
                                 run_url='https://github.com/example/actions/runs/123'),
                            calculation=payload, errors=[])
        self.assertEqual(env['status'], 'success')


if __name__ == '__main__':
    unittest.main()
