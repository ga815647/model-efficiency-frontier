import csv
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
        request = request_data()
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


if __name__ == '__main__':
    unittest.main()
