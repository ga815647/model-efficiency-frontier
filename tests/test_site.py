"""Publication safety and project-subpath contracts for the Pages builder."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from bridge import site
from bridge.result import make_envelope
from bridge.result_v2 import calculate_v2
from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE, recompute_data
import test_bridge_runner as runner_fixture
from test_bridge_runner import git


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        calc = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)
        cls.envelope = make_envelope(recompute_data(), dict(request_commit_sha='b'*40,
            run_id='123', run_attempt=1, run_url='https://github.com/example/actions/runs/123'), calculation=calc, errors=[])

    def record(self, envelope=None):
        e = deepcopy(envelope or self.envelope)
        return dict(envelope=e, publication_commit='c'*40,
                    result_bytes=json.dumps(e).encode(), report_bytes=b'offline-report',
                    csv_sha256=hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(), observations=[])

    def test_only_formal_success_can_select_home_and_order_is_monotone(self):
        original = self.record()
        experiment = self.record(); experiment['envelope']['parameters']['gpt_factor'] = 99
        experiment['envelope']['created_at'] = '2099-01-01T00:00:00Z'
        self.assertIs(site.select_home([experiment, original], PARAMETERS), original)
        failed = self.record(); failed['envelope']['status'] = 'failed'
        self.assertIs(site.select_home([failed, original], PARAMETERS), original)
        newer = self.record(); newer['envelope']['created_at'] = '2026-10-06T00:00:00Z'
        for records in ([newer, original], [original, newer]):
            self.assertIs(site.select_home(records, PARAMETERS), newer)
        repeated = self.record(newer['envelope']); repeated['envelope']['run_attempt'] = 2
        self.assertIs(site.select_home([repeated, newer], PARAMETERS), repeated)
        with self.assertRaises(site.SiteError):
            site.select_home([experiment, failed], PARAMETERS)

    def test_explicit_allowlist_subpath_manifests_and_durable_results(self):
        record = self.record()
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)/'site'
            site.write_site([record], output, formal_parameters=PARAMETERS,
                            site_product_commit='d'*40, base_path='/model-efficiency-frontier/')
            fixed = f'results/{self.envelope["request_id"]}/123-1/'
            expected = {'.nojekyll','index.html','manifest.json'} | {fixed+n for n in ('index.html','result.json','report.html','manifest.json')}
            self.assertEqual({p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}, expected)
            manifest = json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['publication_commit'], 'c'*40)
            self.assertEqual(manifest['result_sha256'], hashlib.sha256(record['result_bytes']).hexdigest())
            self.assertEqual(manifest['result_url'], '/model-efficiency-frontier/'+fixed)
            self.assertEqual(manifest['product_commit'], self.envelope['product_sha'])
            self.assertEqual(manifest['site_product_commit'], 'd'*40)
            self.assertIn('/model-efficiency-frontier/'+fixed+'result.json', (output/'index.html').read_text())
            self.assertEqual((output/fixed/'report.html').read_bytes(), record['report_bytes'])

    def test_invalid_and_duplicate_results_fail_before_output_changes(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)/'site'; output.mkdir(); (output/'index.html').write_text('previous success')
            failed = self.record(); failed['envelope']['status'] = 'failed'
            for records in ([failed], [self.record(), self.record()]):
                with self.assertRaises(site.SiteError):
                    site.write_site(records, output, formal_parameters=PARAMETERS,
                                    site_product_commit='d'*40, base_path='/model-efficiency-frontier/')
                self.assertEqual((output/'index.html').read_text(), 'previous success')

    def test_rejects_unsafe_project_paths(self):
        for path in ('//evil.test/', '/x/../', 'javascript:x', '/x"/', '/x?y/'):
            with self.subTest(path=path), self.assertRaises(site.SiteError):
                site.validate_base_path(path)


class SiteGitValidationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = runner_fixture.RunnerTests('test_approved_historical_adapter_is_pinned_and_html_matches')
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        req, execution = f.submit()
        self.envelope, output = f.run_request(req, execution)
        self.req, self.execution = req, execution
        git(f.repo, 'checkout', '-q', '--orphan', 'results')
        git(f.repo, 'rm', '-rf', '.')
        target = f.repo/f'results/{req["request_id"]}/123-1'
        target.mkdir(parents=True)
        for name in ('result.json','report.html','report.md'):
            (target/name).write_bytes((output/name).read_bytes())
        git(f.repo, 'add', '.'); git(f.repo, 'commit', '-qm', 'publication')
        self.publication = git(f.repo, 'rev-parse','HEAD')
        git(f.repo, 'checkout', '-q', '--detach', f.product)

    def test_fixed_git_result_is_source_and_transport_validated(self):
        f=self.fixture
        record=site.load_record(f.repo, self.publication, f'results/{self.req["request_id"]}/123-1/result.json')
        self.assertEqual(record['envelope'],self.envelope)
        self.assertEqual(record['publication_commit'],self.publication)
        self.assertEqual(record['csv_sha256'],hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest())

    def test_forged_result_must_not_publish(self):
        f=self.fixture
        git(f.repo,'checkout','-q','results')
        path=f.repo/f'results/{self.req["request_id"]}/123-1/result.json'
        e=json.loads(path.read_text()); e['parameters']['gpt_factor']=99
        path.write_text(json.dumps(e)); git(f.repo,'add','.'); git(f.repo,'commit','-qm','forged')
        tip=git(f.repo,'rev-parse','HEAD'); git(f.repo,'checkout','-q','--detach',f.product)
        with self.assertRaises(ValueError):
            site.load_record(f.repo,tip,path.relative_to(f.repo).as_posix())


if __name__ == '__main__': unittest.main()
