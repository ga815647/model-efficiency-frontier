import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from bridge.runner import execute_request, materialize_snapshot
from test_bridge_request import request_data

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = 'runs/2026-09-26-general-grok16'
UUID = request_data()['request_id']


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args]).decode().strip()


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.email', 'test@example.com')
        git(self.repo, 'config', 'user.name', 'Test')
        dest = self.repo / ARCHIVE
        dest.mkdir(parents=True)
        for name in ('candidates.csv', 'public_candidate_source_map.json',
                     'public_leaderboard_exact.json', 'meta_pricing_verification.json',
                     'run-notes.md'):
            (dest / name).write_bytes((ROOT / ARCHIVE / name).read_bytes())
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'product')
        self.product = git(self.repo, 'rev-parse', 'HEAD')
        self.locator = {'commit': self.product, 'path': ARCHIVE + '/candidates.csv'}

    def submit(self, *, params=None, locator=None):
        req = dict(request_data(), product_sha=self.product, operation='recompute',
                   source_snapshot=locator or self.locator)
        if params is not None:
            req['parameters'] = params
        dest = self.repo / 'bridge/requests'
        dest.mkdir(parents=True, exist_ok=True)
        (dest / (UUID + '.json')).write_text(json.dumps(req))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'request')
        execution = dict(request_commit_sha=git(self.repo, 'rev-parse', 'HEAD'), product_sha=self.product,
                         branch='efficiency-run/' + UUID, run_id='123', run_attempt=1,
                         run_url='https://github.com/example/actions/runs/123')
        return req, execution

    def run_request(self, req, execution):
        output = Path(self.tmp.name) / 'output'
        def no_network(_):
            raise AssertionError('recompute must not fetch')
        return execute_request(req, execution=execution, repository=self.repo,
                               output=output, fetch=no_network), output

    def test_approved_historical_adapter_is_pinned_and_html_matches(self):
        req, execution = self.submit()
        # Neither the working tree nor a later commit may change pinned bytes.
        (self.repo / self.locator['path']).write_text('malicious,working,copy\n')
        envelope, output = self.run_request(req, execution)
        self.assertEqual(envelope['status'], 'success')
        self.assertEqual(envelope['source_snapshot'], self.locator)
        self.assertEqual(envelope['candidate_count'], 155)
        self.assertEqual(envelope['benchmark_version'], 'AA-Intelligence-Index-v4.3.2')
        original = (ROOT / self.locator['path']).read_bytes()
        self.assertEqual((output / 'snapshot/candidates.csv').read_bytes(), original)
        self.assertEqual(hashlib.sha256((output / 'snapshot/candidates.csv').read_bytes()).hexdigest(),
                         hashlib.sha256(original).hexdigest())
        self.assertIn(envelope['picks']['strong']['identity'], (output / 'report.html').read_text())
        self.assertEqual(json.loads((output / 'result.json').read_text()), envelope)

    def test_fixed_commit_rejects_later_conflicting_evidence(self):
        req, execution = self.submit()
        # Alter evidence at the pinned product commit via a new commit (never considered).
        p = self.repo / ARCHIVE / 'public_candidate_source_map.json'
        p.write_text('{}')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'later conflicting evidence')
        result, _ = self.run_request(req, execution)
        self.assertEqual(result['status'], 'success')

    def test_invalid_pinned_evidence_is_rejected_before_calculation(self):
        p = self.repo / ARCHIVE / 'public_candidate_source_map.json'
        p.write_text('{}')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'bad evidence')
        loc = dict(self.locator, commit=git(self.repo, 'rev-parse', 'HEAD'))
        req, execution = self.submit(locator=loc)
        result, output = self.run_request(req, execution)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse((output / 'report.md').exists())
        self.assertFalse((output / 'report.html').exists())

    def test_failed_or_missing_adjacent_results_envelope_rejected(self):
        result_path = f'results/{UUID}/777-1/snapshot/candidates.csv'
        p = self.repo / result_path
        p.parent.mkdir(parents=True)
        p.write_bytes((ROOT / ARCHIVE / 'candidates.csv').read_bytes())
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'results')
        git(self.repo, 'branch', 'results')
        locator = dict(commit=git(self.repo, 'rev-parse', 'HEAD'), path=result_path)
        with self.assertRaises(ValueError):
            materialize_snapshot(locator, self.repo, Path(self.tmp.name) / 'materialized')
        (p.parent.parent / 'result.json').write_text(json.dumps({'status': 'failed'}))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'failed envelope')
        with self.assertRaises(ValueError):
            materialize_snapshot(dict(locator, commit=git(self.repo, 'rev-parse', 'HEAD')),
                                 self.repo, Path(self.tmp.name) / 'materialized')

    def test_invalid_request_still_has_correlated_failure(self):
        req, execution = self.submit(params=dict(request_data()['parameters'], grok_factor=True))
        result, output = self.run_request(req, execution)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['request_id'], UUID)
        self.assertEqual(result['request_commit_sha'], execution['request_commit_sha'])
        self.assertEqual(json.loads((output / 'result.json').read_text()), result)
        self.assertFalse((output / 'report.md').exists())

    def test_nonfinite_parameter_produces_parseable_failed_envelope(self):
        req, execution = self.submit(params=dict(request_data()['parameters'], min_score=float('nan')))
        result, output = self.run_request(req, execution)
        self.assertEqual(result['status'], 'failed')
        self.assertIsNone(json.loads((output / 'result.json').read_text())['parameters']['min_score'])

    def test_refresh_failure_preserves_diagnostics_but_not_ladder(self):
        req = dict(request_data(), product_sha=self.product)
        dest = self.repo / 'bridge/requests'
        dest.mkdir(parents=True)
        (dest / (UUID + '.json')).write_text(json.dumps(req))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'request')
        execution = dict(request_commit_sha=git(self.repo, 'rev-parse', 'HEAD'), product_sha=self.product,
                         branch='efficiency-run/' + UUID, run_id='123', run_attempt=1,
                         run_url='https://github.com/example/actions/runs/123')
        output = Path(self.tmp.name) / 'output'
        def fail(url):
            raise ValueError('source_unavailable: ' + url)
        result = execute_request(req, execution=execution, repository=self.repo,
                                 output=output, fetch=fail)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue((output / 'snapshot/evidence').is_dir())
        self.assertFalse((output / 'snapshot/candidates.csv').exists())
        self.assertFalse((output / 'report.html').exists())

    def test_symlink_source_is_rejected(self):
        p = self.repo / ARCHIVE / 'candidates.csv'
        p.unlink()
        os.symlink('run-notes.md', p)
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'symlink source')
        loc = dict(self.locator, commit=git(self.repo, 'rev-parse', 'HEAD'))
        with self.assertRaisesRegex(ValueError, 'source_not_regular_blob'):
            materialize_snapshot(loc, self.repo, Path(self.tmp.name) / 'materialized')

    def test_additional_diff_is_rejected_with_correlated_failure(self):
        req, execution = self.submit()
        (self.repo / 'extra.txt').write_text('extra')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '--amend', '--no-edit', '-q')
        execution['request_commit_sha'] = git(self.repo, 'rev-parse', 'HEAD')
        result, output = self.run_request(req, execution)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['request_commit_sha'], execution['request_commit_sha'])
        self.assertEqual(json.loads((output / 'result.json').read_text())['errors'][0]['code'],
                         'invalid_changed_paths')


if __name__ == '__main__':
    unittest.main()
