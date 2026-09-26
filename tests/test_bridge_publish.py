import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bridge.result import calculate_snapshot, make_envelope
from bridge.publish import PublishError, choose_latest, publish_result
from bridge.runner import _previous
from test_bridge_request import request_data
from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE).decode().strip()


class PublishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calculation, _ = calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.remote = self.base / 'remote.git'
        git(self.base, 'init', '--bare', '-q', str(self.remote))

    def output(self, *, run='100', attempt=1, operation='recompute', status='success',
               created='2026-09-26T12:00:00+00:00', request=None):
        dest = self.base / f'out-{run}-{attempt}-{operation}-{status}'
        dest.mkdir()
        req = dict(request_data(), operation=operation, created_at=created)
        if request:
            req['request_id'] = request
        calculation = dict(self.calculation)
        if operation == 'refresh':
            fresh, _ = self.valid_refresh_output()
            csv = (fresh / 'snapshot/candidates.csv').read_bytes()
            calculation['source_snapshot'] = {'kind': 'acquired', 'path': 'snapshot/candidates.csv',
                                               'sha256': hashlib.sha256(csv).hexdigest()}
            (dest / 'snapshot/evidence').mkdir(parents=True)
            (dest / 'snapshot/candidates.csv').write_bytes(csv)
            for name in ('source_map.json', 'version.json'):
                (dest / 'snapshot/evidence' / name).write_bytes((fresh / 'snapshot/evidence' / name).read_bytes())
            calculation, _ = calculate_snapshot(dest / 'snapshot/candidates.csv', PARAMETERS,
                                                dict(PROVENANCE, source_locator=calculation['source_snapshot']))
        execution = {'request_commit_sha': 'b' * 40, 'run_id': run, 'run_attempt': attempt,
                     'run_url': 'https://github.com/example/actions/runs/' + run}
        if status == 'failed':
            envelope = make_envelope(req, execution, calculation=None,
                                     errors=[{'code': 'test_failure', 'message': 'test'}])
        else:
            envelope = make_envelope(req, execution, calculation=calculation, errors=[])
            (dest / 'report.md').write_text('# Report\n')
            (dest / 'report.html').write_text('<!doctype html><title>Report</title>')
        (dest / 'result.json').write_text(json.dumps(envelope))
        return dest, envelope

    def pointer(self, name):
        return json.loads(git(self.remote, 'show', f'refs/heads/results:{name}'))

    def valid_refresh_output(self):
        # Runner's independently verified fixture has a complete, consistent
        # candidate CSV/source-map/row inventory; don't mock the reconciliation.
        from test_bridge_runner import RunnerTests
        harness = RunnerTests()
        harness.setUp()
        self.addCleanup(harness.doCleanups)
        harness.publish_refresh_fixture()
        source = harness.repo / f'results/{request_data()["request_id"]}/777-1'
        dest = self.base / f'valid-refresh-{len(list(self.base.glob("valid-refresh-*")))}'
        (dest / 'snapshot/evidence').mkdir(parents=True)
        for name in ('result.json', 'snapshot/candidates.csv',
                     'snapshot/evidence/source_map.json', 'snapshot/evidence/version.json'):
            path = dest / name
            path.write_bytes((source / name).read_bytes())
        (dest / 'report.md').write_text('# Report\n')
        (dest / 'report.html').write_text('<!doctype html><title>Report</title>')
        return dest, harness

    def test_incomplete_refresh_inventory_rejected_before_any_pointer(self):
        output, _ = self.output(operation='refresh')
        source_map = output / 'snapshot/evidence/source_map.json'
        inventory = json.loads(source_map.read_text())
        inventory['inventory']['slugs'].pop()
        source_map.write_text(json.dumps(inventory))
        with self.assertRaises(PublishError):
            publish_result(output, remote=str(self.remote))
        self.assertNotEqual(subprocess.run(['git', '-C', str(self.remote), 'rev-parse',
                                             '--verify', 'refs/heads/results'], capture_output=True).returncode, 0)

    def test_valid_published_fresh_inventory_is_usable_by_runner(self):
        output, harness = self.valid_refresh_output()
        published = publish_result(output, remote=str(self.remote))
        pointer = self.pointer('latest-refresh.json')
        self.assertEqual(pointer['result_path'],
                         f'results/{request_data()["request_id"]}/777-1/result.json')
        git(harness.repo, 'checkout', '-q', '-B', 'main', harness.product)
        git(harness.repo, 'branch', '-D', 'results')
        git(harness.repo, 'fetch', '-q', str(self.remote), 'refs/heads/results:refs/heads/results')
        self.assertEqual(git(harness.repo, 'rev-parse', 'results'), published)
        inventory = _previous(harness.repo, harness.product)
        self.assertTrue(inventory['inventory']['slugs'])
        self.assertEqual(inventory['inventory']['contributor_efforts'], ['max', 'xhigh'])

    def test_failure_without_request_uuid_uses_diagnostic_only_path(self):
        output, _ = self.output(status='failed')
        envelope = json.loads((output / 'result.json').read_text())
        envelope['request_id'] = None
        (output / 'result.json').write_text(json.dumps(envelope))
        (output / 'snapshot/evidence').mkdir(parents=True)
        (output / 'snapshot/evidence/missing_candidates.json').write_text('[]')
        tip = publish_result(output, remote=str(self.remote))
        path = f'results/invalid-{envelope["request_commit_sha"]}/{envelope["run_id"]}-{envelope["run_attempt"]}/result.json'
        self.assertIsNone(json.loads(git(self.remote, 'show', f'{tip}:{path}'))['request_id'])
        self.assertEqual(git(self.remote, 'show',
                             f'{tip}:{path.removesuffix("result.json")}snapshot/evidence/missing_candidates.json'), '[]')
        self.assertEqual(publish_result(output, remote=str(self.remote)), tip)
        self.assertNotIn('latest-success.json', git(self.remote, 'ls-tree', '--name-only', tip))
        self.assertNotIn('latest-refresh.json', git(self.remote, 'ls-tree', '--name-only', tip))

    def test_http_remote_query_fragment_and_userinfo_rejected_before_git(self):
        output, _ = self.output()
        for remote in ('https://example.test/repo.git?access_token=secret',
                       'https://example.test/repo.git#secret',
                       'https://name:secret@example.test/repo.git'):
            with self.subTest(remote=remote), patch('bridge.publish._git') as git_call:
                with self.assertRaises(PublishError):
                    publish_result(output, remote=remote)
                git_call.assert_not_called()

    def test_preserves_attempts_and_idempotence(self):
        first, envelope = self.output()
        sha = publish_result(first, remote=str(self.remote))
        self.assertEqual(publish_result(first, remote=str(self.remote)), sha)
        second, _ = self.output(attempt=2)
        tip = publish_result(second, remote=str(self.remote))
        self.assertNotEqual(tip, sha)
        for attempt in (1, 2):
            path = f'results/{envelope["request_id"]}/100-{attempt}/result.json'
            self.assertEqual(json.loads(git(self.remote, 'show', f'{tip}:{path}'))['run_attempt'], attempt)
        (first / 'report.html').write_text('different')
        with self.assertRaises(PublishError):
            publish_result(first, remote=str(self.remote))

    def test_pointer_order_and_failure(self):
        newer, _ = self.output(run='200', operation='refresh', created='2026-09-27T12:00:00+00:00')
        publish_result(newer, remote=str(self.remote))
        before = self.pointer('latest-refresh.json')
        older, _ = self.output(run='201', operation='refresh', created='2026-09-26T12:00:00+00:00')
        publish_result(older, remote=str(self.remote))
        self.assertEqual(self.pointer('latest-refresh.json'), before)
        self.assertEqual(self.pointer('latest-success.json'), before)
        recompute, _ = self.output(run='202')
        publish_result(recompute, remote=str(self.remote))
        self.assertEqual(self.pointer('latest-refresh.json'), before)
        success = self.pointer('latest-success.json')
        failed, _ = self.output(run='203', status='failed')
        publish_result(failed, remote=str(self.remote))
        self.assertEqual(self.pointer('latest-success.json'), success)
        self.assertEqual(self.pointer('latest-refresh.json'), before)

    def test_order_is_source_date_then_offset_aware_time_then_commit(self):
        old = {'status': 'success', 'operation': 'refresh', 'source_dates': ['2026-09-27'],
               'created_at': '2026-09-26T10:00:00+00:00', 'request_commit_sha': 'a'*40}
        incoming = dict(old, source_dates=['2026-09-26'], created_at='2026-09-28T10:00:00+00:00')
        self.assertIs(choose_latest(old, incoming, refresh_only=False), old)
        incoming['source_dates'] = ['2026-09-27']
        self.assertIs(choose_latest(old, incoming, refresh_only=False), incoming)
        incoming['source_dates'] = ['2026-02-30']
        with self.assertRaises(PublishError):
            choose_latest(old, incoming, refresh_only=False)

    def test_retry_exhaustion_does_not_force_push(self):
        from bridge import publish
        output, _ = self.output()
        with patch.object(publish, '_push', return_value=False) as push:
            with self.assertRaisesRegex(PublishError, 'retry_exhausted'):
                publish_result(output, remote=str(self.remote))
        self.assertEqual(push.call_count, 3)
        self.assertNotEqual(subprocess.run(['git', '-C', str(self.remote), 'rev-parse',
                                             '--verify', 'refs/heads/results'], capture_output=True).returncode, 0)

    def test_invalid_output_layout_and_hash(self):
        output, _ = self.output(operation='refresh')
        (output / 'snapshot/candidates.csv').write_text('changed')
        with self.assertRaises(PublishError):
            publish_result(output, remote=str(self.remote))
        good, _ = self.output(run='101')
        (good / 'extra.txt').write_text('unapproved')
        with self.assertRaises(PublishError):
            publish_result(good, remote=str(self.remote))
        (good / 'extra.txt').unlink()
        (good / 'report.html').unlink()
        (good / 'report.html').symlink_to('/etc/hosts')
        with self.assertRaises(PublishError):
            publish_result(good, remote=str(self.remote))

    def test_failed_output_has_no_partial_report(self):
        output, _ = self.output(status='failed')
        (output / 'report.md').write_text('partial')
        with self.assertRaises(PublishError):
            publish_result(output, remote=str(self.remote))

    def test_recompute_does_not_replace_refresh_pointer(self):
        old = {'operation': 'refresh', 'status': 'success', 'request_id': 'old'}
        new = {'operation': 'recompute', 'status': 'success', 'request_id': 'new'}
        self.assertEqual(choose_latest(old, new, refresh_only=True), old)

    def test_retries_nonfastforward_with_competing_publisher(self):
        from bridge import publish
        first, env = self.output(run='300')
        second, _ = self.output(run='301')
        original = publish._push
        calls = []

        def competing(*args, **kwargs):
            if not calls:
                calls.append(1)
                publish_result(second, remote=str(self.remote))
            return original(*args, **kwargs)

        with patch.object(publish, '_push', side_effect=competing):
            publish_result(first, remote=str(self.remote))
        tip = git(self.remote, 'rev-parse', 'refs/heads/results')
        self.assertIn(f'results/{env["request_id"]}/300-1/result.json', git(self.remote, 'ls-tree', '-r', '--name-only', tip))
        self.assertIn(f'results/{env["request_id"]}/301-1/result.json', git(self.remote, 'ls-tree', '-r', '--name-only', tip))
