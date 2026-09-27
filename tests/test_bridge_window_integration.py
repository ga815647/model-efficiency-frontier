"""Cutover acceptance through public APIs, pinned Git sources and bare publication."""
import json
from collections import Counter
import unittest

from bridge import result, result_v1
from bridge.html_report import render_html
from bridge.publish import PublishError, publish_result
from bridge.runner import execute_request, materialize_snapshot, _previous, main, verify_transport
from test_bridge_request import request_data
from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE, recompute_data
import test_bridge_runner as runner_tests
import test_bridge_publish as publish_tests

EXECUTION = {'request_commit_sha': 'b' * 40, 'run_id': '900', 'run_attempt': 1,
             'run_url': 'https://github.com/example/actions/runs/900'}


class WindowIntegrationTests(unittest.TestCase):
    def publisher(self):
        harness = publish_tests.PublishTests()
        harness.setUp()
        self.addCleanup(harness.doCleanups)
        return harness

    def test_both_failure_schemas_enforce_source_capability_proof(self):
        for api in (result_v1, result):
            for method in (
                'test_late_missing_candidate_cannot_publish_without_proof_or_with_unparsed_models',
                'test_preproof_models_parse_failure_remains_publishable_as_failure',
                'test_preproof_models_fetch_failure_remains_publishable_as_failure',
            ):
                with self.subTest(api=api.__name__, case=method):
                    getattr(self.publisher(), method)(make_api=api.make_envelope)

    def test_mixed_version_append_only_publication_and_pointer_order(self):
        harness = self.publisher()
        old, envelope = harness.output(run='100', operation='refresh', schema_version=1)
        self.assertEqual(envelope['schema_version'], 1)
        self.assertEqual(main(['assert-success', '--output', str(old)]), 0)
        publish_result(old, remote=str(harness.remote))
        new, envelope = harness.output(run='200', operation='refresh', schema_version=2,
                                      created='2026-09-27T12:00:00+00:00')
        self.assertEqual(envelope['schema_version'], 2)
        self.assertEqual(main(['assert-success', '--output', str(new)]), 0)
        tip = publish_result(new, remote=str(harness.remote))
        self.assertEqual(publish_result(new, remote=str(harness.remote)), tip)
        pointers = {name: harness.pointer(name) for name in ('latest-success.json', 'latest-refresh.json')}
        for version in (1, 2):
            failed, _ = harness.output(run=str(300 + version), status='failed', schema_version=version)
            self.assertEqual(main(['assert-success', '--output', str(failed)]), 1)
            publish_result(failed, remote=str(harness.remote))
            older, _ = harness.output(run=str(400 + version), operation='refresh', schema_version=version)
            publish_result(older, remote=str(harness.remote))
            for name, pointer in pointers.items():
                self.assertEqual(harness.pointer(name), pointer)
        for run, version in (('100', 1), ('200', 2)):
            readback = json.loads(publish_tests.git(harness.remote, 'show',
                f'refs/heads/results:results/{envelope["request_id"]}/{run}-1/result.json'))
            self.assertEqual(readback['schema_version'], version)
            result.validate_envelope(readback)
        (new / 'report.html').write_text('conflicting bytes')
        with self.assertRaises(PublishError):
            publish_result(new, remote=str(harness.remote))

    def test_modern_five_source_runner_publication_and_pinned_recompute(self):
        from test_refresh_sources import FIX, URLS
        harness = runner_tests.RunnerTests()
        harness.setUp()
        self.addCleanup(harness.doCleanups)
        publisher = self.publisher()
        req = dict(request_data(), product_sha=harness.product)
        request_path = harness.repo / 'bridge/requests' / (req['request_id'] + '.json')
        request_path.parent.mkdir(parents=True)
        request_path.write_text(json.dumps(req))
        runner_tests.git(harness.repo, 'add', '.')
        runner_tests.git(harness.repo, 'commit', '-qm', 'refresh request')
        execution = dict(EXECUTION, request_commit_sha=runner_tests.git(harness.repo, 'rev-parse', 'HEAD'),
                         product_sha=harness.product, branch='efficiency-run/' + req['request_id'])
        pages = {URLS[name]: (FIX / name).with_suffix('.html').read_bytes() for name in URLS}
        output = publisher.base / 'modern'
        envelope = execute_request(req, execution=execution, repository=harness.repo,
                                   output=output, fetch=pages.__getitem__)
        self.assertEqual(envelope['status'], 'success')
        self.assertEqual(envelope['schema_version'], 2)
        self.assertEqual(envelope['candidate_count'], 154)
        self.assertEqual(len(envelope['candidate_statuses']), 154)
        self.assertEqual(len(envelope['ladder']), 10)
        tip = publish_result(output, remote=str(publisher.remote))
        target = f'results/{req["request_id"]}/900-1'
        readback = json.loads(publish_tests.git(publisher.remote, 'show', f'{tip}:{target}/result.json'))
        self.assertEqual(readback, envelope)
        result.validate_envelope(readback)
        for name in ('report.md', 'report.html'):
            self.assertEqual(publish_tests.git(publisher.remote, 'show', f'{tip}:{target}/{name}'),
                             (output / name).read_text().strip())
        runner_tests.git(harness.repo, 'fetch', '-q', str(publisher.remote),
                         'refs/heads/results:refs/heads/results')
        self.assertEqual(_previous(harness.repo, harness.product)['inventory']['contributor_efforts'], ['xhigh'])
        locator = {'commit': tip, 'path': target + '/snapshot/candidates.csv'}
        runner_tests.git(harness.repo, 'checkout', '-q', '-B', 'recompute', harness.product)
        req, execution = harness.submit(locator=locator)
        recomputed, recomputed_output = harness.run_request(req, execution)
        self.assertEqual(recomputed['status'], 'success')
        self.assertEqual(recomputed['schema_version'], 2)
        self.assertEqual(recomputed['ladder'], envelope['ladder'])
        self.assertEqual((recomputed_output / 'snapshot/candidates.csv').read_bytes(),
                         (output / 'snapshot/candidates.csv').read_bytes())
        # A CSV blob cannot be substituted for the commit locator accepted above.
        blob = runner_tests.git(harness.repo, 'rev-parse', f'{tip}:{locator["path"]}')
        with self.assertRaises(ValueError):
            materialize_snapshot(dict(locator, commit=blob), harness.repo, publisher.base / 'blob')

    def test_public_default_is_v2(self):
        calc, markdown = result.calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)
        envelope = result.make_envelope(recompute_data(), EXECUTION, calculation=calc, errors=[])
        self.assertEqual(envelope['schema_version'], 2)
        self.assertEqual(envelope['selection_policy'], 'cp-new-high-window-v1')
        self.assertNotIn('picks', envelope)
        self.assertEqual(len(envelope['ladder']), 10)
        self.assertEqual(Counter(r['status'] for r in envelope['candidate_statuses']),
                         {'excluded': 136, 'cut': 9, 'final': 10})
        self.assertEqual(envelope['anchors']['highest_retained_score']['identity'],
                         'GPT-6 Astra xhigh AA-public published-price')
        self.assertEqual(envelope['anchors']['lowest_retained_cost']['identity'],
                         'GPT-6 Luna low AA-public published-price')
        self.assertIn(envelope['anchors']['highest_retained_score']['identity'], markdown)
        self.assertEqual(render_html(calc).count('data-rank="'), 10)
        result.validate_envelope(envelope)

    def test_transport_and_diagnostic_failures_are_v2(self):
        harness = runner_tests.RunnerTests()
        harness.setUp()
        self.addCleanup(harness.doCleanups)
        output = harness.repo / 'failure'
        product_file = harness.repo / 'handoff/product-sha'
        self.assertFalse(verify_transport(harness.repo, event_sha='invalid',
            ref_name='efficiency-run/' + runner_tests.UUID, run_id='901', run_attempt=1,
            output=output, product_sha_file=product_file))
        envelope = json.loads((output / 'result.json').read_text())
        self.assertEqual(envelope['schema_version'], 2)
        self.assertEqual(envelope['status'], 'failed')
        self.assertNotIn('ladder', envelope)
        result.validate_envelope(envelope)
        product_file.parent.mkdir(parents=True)
        product_file.write_text(harness.product)
        main(['diagnostic-failure', '--event-sha', harness.product,
              '--ref-name', 'efficiency-run/' + runner_tests.UUID,
              '--product-sha-file', str(product_file), '--run-id', '902',
              '--run-attempt', '1', '--output', str(output)])
        envelope = json.loads((output / 'result.json').read_text())
        self.assertEqual(envelope['schema_version'], 2)
        self.assertEqual(envelope['status'], 'failed')
        result.validate_envelope(envelope)

    def test_old_and_new_fresh_sources_recompute_as_v2_with_original_bytes(self):
        for version in (1, 2):
            with self.subTest(version=version):
                harness = runner_tests.RunnerTests()
                harness.setUp()
                self.addCleanup(harness.doCleanups)
                source = harness.publish_refresh_fixture(schema_version=version)
                self.assertEqual(source['schema_version'], version)
                locator = {'commit': runner_tests.git(harness.repo, 'rev-parse', 'HEAD'),
                           'path': f'results/{runner_tests.UUID}/777-1/snapshot/candidates.csv'}
                original = (harness.repo / locator['path']).read_bytes()
                runner_tests.git(harness.repo, 'checkout', '-q', '-B', 'main', harness.product)
                req, execution = harness.submit(locator=locator)
                envelope, output = harness.run_request(req, execution)
                self.assertEqual(envelope['status'], 'success')
                self.assertEqual(envelope['schema_version'], 2)
                self.assertEqual(len(envelope['ladder']), 10)
                self.assertEqual(len(envelope['candidate_statuses']), 155)
                self.assertEqual((output / 'snapshot/candidates.csv').read_bytes(), original)
                result.validate_envelope(envelope)
