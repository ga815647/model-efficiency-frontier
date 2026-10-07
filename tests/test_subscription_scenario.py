"""Versioned subscription factors must affect cost without changing evidence."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import test_bridge_runner as runner_fixture

from bridge.request import RequestError
from bridge.result import calculate_snapshot, make_envelope, validate_envelope
from bridge.result_v2 import calculate_v2
from bridge import site
from test_bridge_request import request_data, validate
from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE, recompute_data
from test_bridge_result_v2 import EXECUTION

PARAMS = dict(PARAMETERS, gpt_factor=18.9, gemini_factor=6, claude_factor=37)


class SubscriptionScenarioTests(unittest.TestCase):
    def test_request_v2_carries_all_factors_and_v1_stays_exact(self):
        request = dict(request_data(), schema_version=2, parameters=PARAMS)
        self.assertEqual(validate(request), request)
        for version, params in ((1, PARAMS), (2, PARAMETERS)):
            with self.subTest(version=version), self.assertRaises(RequestError):
                validate(dict(request, schema_version=version, parameters=params))
        for key in ('gemini_factor', 'claude_factor'):
            for value in (True, 0, -1, float('inf'), '6'):
                with self.subTest(key=key, value=value), self.assertRaises(RequestError):
                    validate(dict(request, parameters=dict(PARAMS, **{key: value})))

    def envelope(self):
        calculation, _ = calculate_snapshot(SNAPSHOT, PARAMS, PROVENANCE)
        return make_envelope(dict(recompute_data(), schema_version=2, parameters=PARAMS),
                             EXECUTION, calculation=calculation, errors=[])

    def test_costs_use_each_family_factor_and_originals_are_unchanged(self):
        old = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)
        new = self.envelope()
        self.assertEqual(new['schema_version'], 3)
        self.assertEqual(validate_envelope(new), new)
        old_rows = {r['identity']: r for r in old['candidate_statuses']}
        families = set()
        for row in new['candidate_statuses']:
            previous = old_rows[row['identity']]
            for key in ('model', 'effort', 'score', 'cost_orig', 'cp_orig', 'grade', 'source_date', 'source_url'):
                self.assertEqual(row[key], previous[key])
            expected = (1 if row['is_contributor'] else 18.9 if row['identity'].startswith('GPT-')
                        else 16 if row['is_grok'] else 37 if row['comparison_only']
                        else 6 if row['identity'].lower().startswith('gemini ') else 1)
            self.assertEqual(row['factor'], expected, row['identity'])
            self.assertAlmostEqual(row['cost_adj'], row['cost_orig'] / expected)
            families.add(expected)
        self.assertTrue({1, 6, 16, 18.9, 37} <= families)
        for anchor in new['anchors'].values():
            self.assertTrue(anchor is None or not anchor['comparison_only'])

    def test_versions_cannot_be_relabeled_and_tampering_is_rejected(self):
        original = self.envelope()
        for change in ('version', 'missing', 'extra', 'factor', 'cost'):
            env = deepcopy(original)
            if change == 'version': env['schema_version'] = 2
            elif change == 'missing': del env['parameters']['gemini_factor']
            elif change == 'extra': env['parameters']['invented_factor'] = 10
            elif change == 'factor': next(r for r in env['candidate_statuses'] if r['factor'] != 1)['factor'] = 1
            else: env['candidate_statuses'][0]['cost_adj'] *= 2
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_envelope(env)

    def test_pages_keeps_old_fixed_results_and_rejects_other_scenarios_as_home(self):
        old_calc = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)
        old = make_envelope(recompute_data(), dict(EXECUTION, run_id='old'), calculation=old_calc, errors=[])
        def record(env):
            return dict(envelope=env, publication_commit='c'*40, result_bytes=json.dumps(env).encode(),
                        report_bytes=b'original report', csv_sha256='d'*64, observations=[])
        new = record(self.envelope()); historical = record(old)
        experiment = deepcopy(new); experiment['envelope']['parameters']['gemini_factor'] = 99
        experiment['envelope']['created_at'] = '2099-01-01T00:00:00Z'
        self.assertIs(site.select_home([experiment, historical, new], PARAMS), new)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)/'site'
            site.write_site([historical, new], output, formal_parameters=PARAMS,
                            site_product_commit='e'*40, base_path='/model-efficiency-frontier/')
            manifest = json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['parameters'], PARAMS)
            self.assertEqual(manifest['result_schema_version'], 3)
            self.assertEqual((output/f'results/{old["request_id"]}/old-1/report.html').read_bytes(), b'original report')
            html = (output/'index.html').read_text()
            for text in ('GPT ×18.9', 'Gemini ×6', 'Claude ×37', 'Grok ×16', 'Contributor ×1'):
                self.assertIn(text, html)
            self.assertNotIn('GPT 預設 ×18 ', html)


class SubscriptionRunnerTests(unittest.TestCase):
    def fixture(self):
        fixture = runner_fixture.RunnerTests('test_approved_historical_adapter_is_pinned_and_html_matches')
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        return fixture

    def test_single_file_bridge_executes_v3_without_fetching_sources(self):
        fixture = self.fixture()
        request, execution = fixture.submit(schema_version=2, params=PARAMS)
        envelope, output = fixture.run_request(request, execution)
        self.assertEqual(envelope['status'], 'success', envelope['errors'])
        self.assertEqual(envelope['schema_version'], 3)
        self.assertEqual(envelope['parameters'], PARAMS)
        self.assertEqual(envelope['source_snapshot'], fixture.locator)
        self.assertIn('Gemini ×6', (output/'report.html').read_text())

    def test_v3_publication_and_pages_readback_revalidate_exact_request_and_source(self):
        from bridge.publish import publish_result
        import test_bridge_publish as publish_fixture
        fixture = self.fixture()
        request, execution = fixture.submit(schema_version=2, params=PARAMS)
        envelope, output = fixture.run_request(request, execution)
        publisher = publish_fixture.PublishTests()
        publisher.setUp(); self.addCleanup(publisher.doCleanups)
        publication = publish_result(output, remote=str(publisher.remote),
                                     source_repository=fixture.repo, trusted_product_sha=fixture.product)
        runner_fixture.git(fixture.repo, 'fetch', '-q', str(publisher.remote),
                           'refs/heads/results:refs/heads/results')
        path = f'results/{request["request_id"]}/123-1/result.json'
        record = site.load_record(fixture.repo, publication, path)
        self.assertEqual(record['envelope'], envelope)
        self.assertEqual(record['report_bytes'], (output/'report.html').read_bytes())

    def test_invalid_new_request_has_correlated_v3_failure_without_report(self):
        fixture = self.fixture()
        request, execution = fixture.submit(schema_version=2, params=dict(PARAMS, claude_factor=True))
        envelope, output = fixture.run_request(request, execution)
        self.assertEqual(envelope['schema_version'], 3)
        self.assertEqual(envelope['status'], 'failed')
        self.assertEqual(envelope['request_commit_sha'], execution['request_commit_sha'])
        self.assertFalse((output/'report.html').exists())


if __name__ == '__main__': unittest.main()
