import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from bridge.runner import main
from bridge.publish import publish_result
from bridge.result import make_envelope
from test_bridge_request import request_data


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args]).decode().strip()


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        self.repo.mkdir()
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.name', 'Tester')
        git(self.repo, 'config', 'user.email', 'tester@example.com')
        (self.repo / 'code.py').write_text('trusted\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'product')
        self.product = git(self.repo, 'rev-parse', 'HEAD')
        self.request = dict(request_data(), product_sha=self.product)
        self.branch = 'efficiency-run/' + self.request['request_id']
        git(self.repo, 'branch', 'main', self.product)
        git(self.repo, 'checkout', '-q', '-b', self.branch)
        self.output = Path(self.temp.name) / 'output'
        self.sha_file = Path(self.temp.name) / 'product.sha'

    def submit(self, raw=None, *, code=False):
        file = self.repo / 'bridge/requests' / (self.request['request_id'] + '.json')
        file.parent.mkdir(parents=True)
        file.write_text(json.dumps(self.request) if raw is None else raw)
        if code:
            (self.repo / 'code.py').write_text('hostile\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'request')
        self.event = git(self.repo, 'rev-parse', 'HEAD')
        git(self.repo, 'checkout', '-q', 'main')

    def verify(self, branch=None):
        return main(['verify-transport', '--repository', str(self.repo), '--event-sha', self.event,
                     '--ref-name', branch or self.branch, '--run-id', '123', '--run-attempt', '1',
                     '--output', str(self.output), '--product-sha-file', str(self.sha_file)])

    def test_clean_transport_pins_product_from_event_parent(self):
        self.submit()
        self.assertEqual(self.verify(), 0)
        self.assertEqual(self.sha_file.read_text().strip(), self.product)
        self.assertFalse((self.output / 'result.json').exists())

    def test_code_change_rejected_and_failed_output_correlated(self):
        self.submit(code=True)
        self.assertEqual(self.verify(), 1)
        result = json.loads((self.output / 'result.json').read_text())
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['request_id'], self.request['request_id'])
        self.assertEqual(result['request_commit_sha'], self.event)
        self.assertFalse(self.sha_file.exists())

    def test_malformed_json_uses_event_ref_not_claimed_payload(self):
        self.submit(raw='{"request_id": "someone-else", BAD')
        self.assertEqual(self.verify(), 1)
        result = json.loads((self.output / 'result.json').read_text())
        self.assertEqual(result['request_id'], self.request['request_id'])
        self.assertEqual(result['request_commit_sha'], self.event)
        self.assertIsNone(result['operation'])
        remote = Path(self.temp.name) / 'remote.git'
        subprocess.check_call(['git', 'init', '-q', '--bare', str(remote)])
        publication = publish_result(self.output, remote=str(remote))
        self.assertEqual(len(publication), 40)
        published = subprocess.check_output(['git', '--git-dir', str(remote), 'show',
                                             publication + ':results/' + self.request['request_id'] +
                                             '/123-1/result.json'])
        self.assertEqual(json.loads(published)['request_commit_sha'], self.event)
        self.assertEqual(main(['assert-success', '--output', str(self.output)]), 1)

    def test_product_must_be_ancestor_of_current_main(self):
        self.submit()
        git(self.repo, 'checkout', '-q', '--orphan', 'replacement')
        git(self.repo, 'commit', '-qm', 'unrelated', '--allow-empty')
        git(self.repo, 'branch', '-f', 'main', 'HEAD')
        git(self.repo, 'checkout', '-q', 'main')
        self.assertEqual(self.verify(), 1)

    def test_later_branch_tip_does_not_replace_authenticated_event_sha(self):
        self.submit()
        pinned = self.event
        git(self.repo, 'checkout', '-q', self.branch)
        (self.repo / 'later.txt').write_text('new tip\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'later branch tip')
        git(self.repo, 'checkout', '-q', 'main')
        self.assertEqual(self.verify(), 0)
        self.assertEqual(self.event, pinned)

    def test_diagnostic_failure_after_runner_interruption_uses_verified_identity(self):
        self.submit()
        self.assertEqual(self.verify(), 0)
        self.assertEqual(main(['diagnostic-failure', '--event-sha', self.event,
                               '--ref-name', self.branch, '--product-sha-file', str(self.sha_file),
                               '--run-id', '123', '--run-attempt', '1', '--output', str(self.output)]), 0)
        result = json.loads((self.output / 'result.json').read_text())
        self.assertEqual(result['request_id'], self.request['request_id'])
        self.assertEqual(result['product_sha'], self.product)
        self.assertEqual(main(['assert-success', '--output', str(self.output)]), 1)

    def test_assert_success_rejects_failed_result_after_publication(self):
        self.output.mkdir()
        failure = make_envelope({'operation': None, 'request_id': self.request['request_id'],
                                 'product_sha': self.product, 'created_at': None,
                                 'source_snapshot': None, 'parameters': None},
                                {'request_commit_sha': self.product, 'run_id': '123',
                                 'run_attempt': 1, 'run_url': 'https://example.org/run/123'},
                                calculation=None, errors=[{'code': 'bad', 'message': 'bad'}])
        (self.output / 'result.json').write_text(json.dumps(failure))
        self.assertEqual(main(['assert-success', '--output', str(self.output)]), 1)
