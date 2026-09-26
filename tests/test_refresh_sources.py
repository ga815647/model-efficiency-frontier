import json
import csv
import tempfile
import unittest
from unittest.mock import patch
from decimal import Decimal
from pathlib import Path

from scripts.aa_public import SourceError, parse_leaderboard, parse_release, corroborate_version
from scripts.meta_pricing import parse_meta_pricing, rescale_contributor
from scripts.refresh_snapshot import refresh_snapshot, _diagnostic
from scripts.refresh_snapshot import _model_effort

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests/fixtures/refresh'
URLS = {'leader': 'https://artificialanalysis.ai/leaderboards/models',
        'grok': 'https://artificialanalysis.ai/models/releases/grok-4-7',
        'muse': 'https://artificialanalysis.ai/models/releases/muse-spark-1-3',
        'meta': 'https://dev.meta.ai/docs/pricing-rate-limits'}


class RefreshSourcesTest(unittest.TestCase):
    def test_real_flight_and_version(self):
        rows = parse_leaderboard((FIX / 'leader.html').read_text())
        releases = [parse_release((FIX / k).with_suffix('.html').read_text(), URLS[k]) for k in ('grok', 'muse')]
        result = corroborate_version(rows, releases)
        self.assertEqual(result['benchmark_version'], 'AA-Intelligence-Index-v4.3.2')
        self.assertEqual(len(result['crosschecks']), 4)
        self.assertEqual(next(r for r in rows if r['slug'] == 'grok-4-7-high')['score'], Decimal('46.3321770885625'))

    def test_raw_markup_missing_required_model_fields_fails(self):
        html = (FIX / 'leader.html').read_text()
        for original, replacement in (('name\\":\\"Grok 4.7 (high)', 'name_REMOVED\\":\\"Grok 4.7 (high)'),
                                      ('intelligenceIndexIsEstimated\\":false',
                                       'intelligenceIndexIsEstimated_REMOVED\\":false')):
            self.assertIn(original, html)
            with self.subTest(original=original), self.assertRaises(SourceError):
                parse_leaderboard(html.replace(original, replacement, 1))
        release = (FIX / 'muse.html').read_text()
        self.assertIn('intelligenceIndexCostPerTask\\":{\\"cost\\":', release)
        with self.assertRaises(SourceError):
            parse_release(release.replace('intelligenceIndexCostPerTask\\":{\\"cost\\":',
                                          'intelligenceIndexCostPerTask\\":{\\"changedCost\\":', 1), URLS['muse'])
        # A missing cost key is legitimate on this page, but must survive as
        # explicit missing-cost evidence (and fail inventory if formerly paid).
        missing_cost = parse_leaderboard(html.replace('intelligenceIndexCostPerTask\\":2.726106691786027',
                                                      'intelligenceIndexCostPerTask_REMOVED\\":2.726106691786027', 1))
        self.assertIsNone(next(r for r in missing_cost if r['slug'] == 'grok-4-7-high')['cost_per_task'])

    def test_malformed_model_object_does_not_silently_disappear(self):
        html = (FIX / 'leader.html').read_text()
        # Corrupt a model object's JSON value without altering unrelated site slug payloads.
        self.assertIn('intelligenceIndexCostPerTask\\":2.726106691786027', html)
        with self.assertRaises(SourceError):
            parse_leaderboard(html.replace('intelligenceIndexCostPerTask\\":2.726106691786027',
                                           'intelligenceIndexCostPerTask\\":oops', 1))

    def test_reordered_or_distant_model_marker_cannot_hide_broken_json(self):
        for raw in ('{"slug":"new-model","creator":"X","name":"New","shortName":"New","score":oops}',
                    '{"slug":"new-model","creator":"' + 'x' * 600 + '","name":"New",'
                    '"shortName":"New","intelligenceIndexCostPerTask":oops}'):
            html = '<script>self.__next_f.push([1,' + json.dumps(raw) + '])</script>'
            with self.subTest(raw=raw[:70]), self.assertRaises(SourceError) as caught:
                parse_leaderboard(html)
            self.assertEqual(caught.exception.code, 'model_markup_drift')

    def test_effort_and_checkpoint_identity(self):
        self.assertEqual(_model_effort("DeepSeek R1 (Jan '25)", 'deepseek-r1-0120'),
                         ("DeepSeek R1 (Jan '25)", 'unspecified', 'deepseek-r1-0120'))
        self.assertEqual(_model_effort('Qwen3.8 Max (0902)', 'qwen3-8-max'),
                         ('Qwen3.8 Max (0902)', 'unspecified', 'qwen3-8-max'))
        self.assertEqual(_model_effort('Grok 4.7 (high)', 'grok-4-7-high'),
                         ('Grok 4.7', 'high', 'grok-4-7-high'))
        with self.assertRaises(SourceError):
            _model_effort('Unknown (unreviewed suffix)', 'unknown-suffix')

    def test_conflicting_duplicate_and_markup(self):
        html = (FIX / 'leader.html').read_text()
        self.assertEqual(parse_leaderboard(html + html), parse_leaderboard(html))
        with self.assertRaises(SourceError):
            parse_leaderboard(html.replace('46.3321770885625', '43.2', 1) + html)
        with self.assertRaises(SourceError) as caught:
            parse_leaderboard('<div>no flight data</div>')
        self.assertEqual(caught.exception.code, 'markup_drift')

    def test_missing_crosscheck_and_disagreement(self):
        rows = parse_leaderboard((FIX / 'leader.html').read_text())
        releases = [parse_release((FIX / k).with_suffix('.html').read_text(), URLS[k]) for k in ('grok', 'muse')]
        releases[1]['declared_version'] = '4.3'
        with self.assertRaises(SourceError) as caught:
            corroborate_version(rows, releases)
        self.assertEqual(caught.exception.code, 'version_disagreement')
        releases[1]['declared_version'] = '4.3.2'
        del releases[1]['records']['muse-spark-1-3-xhigh']
        with self.assertRaises(SourceError):
            corroborate_version(rows, releases)

    def test_missing_score_estimated_and_zero_cost_sidecar(self):
        html = (FIX / 'leader.html').read_text()
        rows = parse_leaderboard(html)
        self.assertTrue(any(r['cost_per_task'] == 0 for r in rows))
        self.assertIsNone(next(r for r in parse_leaderboard(html.replace('46.3321770885625', 'null'))
                               if r['slug'] == 'grok-4-7-high')['score'])
        self.assertTrue(any(r['is_estimated'] for r in parse_leaderboard(
            html.replace('intelligenceIndexIsEstimated\\":false', 'intelligenceIndexIsEstimated\\":true', 1))))
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        with tempfile.TemporaryDirectory() as temp:
            refresh_snapshot(Path(temp) / 'snapshot', previous=None, fetch=data.__getitem__)
            sidecar = json.loads((Path(temp) / 'snapshot/free-sidecar.json').read_text())
            self.assertEqual(len([x for x in sidecar['excluded_non_paid_or_unusable'] if x['reason'] == 'zero_cost']), 4)

    def test_api_envelopes_drift_separately_from_public(self):
        class Response:
            def __init__(self, page):
                self.page = page
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self, *args):
                return json.dumps({'intelligence_index_version': '4.3' if self.page == 1 else '4.3.1',
                                   'data': [{}] * (200 if self.page == 1 else 1)}).encode()
        with tempfile.TemporaryDirectory() as temp, patch.dict('os.environ', {'AA_API_KEY': 'dummy'}), patch(
                'scripts.refresh_snapshot.urllib.request.urlopen', side_effect=[Response(1), Response(2)]):
            with self.assertRaises(SourceError) as caught:
                _diagnostic(Path(temp), 'AA-Intelligence-Index-v4.3.2')
            self.assertEqual(caught.exception.code, 'api_version_drift')

    def test_meta_rates_and_components(self):
        prices = parse_meta_pricing((FIX / 'meta.html').read_text())
        self.assertEqual(prices['USD_per_1M_tokens']['Contributor']['input'], Decimal('0.10'))
        release = parse_release((FIX / 'muse.html').read_text(), URLS['muse'])
        components = release['records']['muse-spark-1-3-xhigh']['components']
        cost = rescale_contributor(components, prices['USD_per_1M_tokens'])
        self.assertLess(abs(cost - Decimal('0.05476746875401318370823529412')), Decimal('1e-25'))

    def test_meta_historical_mentions_cannot_satisfy_active_plan_or_terms(self):
        html = (FIX / 'meta.html').read_text()
        self.assertIn('muse-spark-1.3-contributor', html)
        # Keep historical mentions in a footer; active labelled list must still fail.
        dropped = html.replace('Models: <code', 'Models: <code', 1).replace(
            'muse-spark-1.3-contributor</code>', 'retired-contributor</code>', 1)
        with self.assertRaises(SourceError):
            parse_meta_pricing(dropped + '<footer>muse-spark-1.3-contributor</footer>')
        without_terms = html.replace('permission to use your prompts and completions to train future Meta models',
                                     'without permission to train', 1)
        with self.assertRaises(SourceError):
            parse_meta_pricing(without_terms + '<footer>permission to use your prompts and completions to train future Meta models</footer>')

    def test_meta_active_plan_terms_require_positive_exact_meaning(self):
        html = (FIX / 'meta.html').read_text()
        contributor_negated = html.replace('permission to use your prompts and completions to train future Meta models',
                                           'WITHOUT permission to use your prompts and completions to train future Meta models', 1)
        standard_changed = html.replace('your prompts and completions are not used to train Meta models',
                                        'your prompts and completions may be used to train Meta models', 1)
        for altered in (contributor_negated, standard_changed):
            self.assertNotEqual(altered, html)
            with self.subTest(altered=altered != html), self.assertRaises(SourceError):
                parse_meta_pricing(altered)

    def test_missing_previous_candidate_blocks(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(SourceError) as caught:
                refresh_snapshot(Path(temp) / 'snapshot', previous={'slugs': ['missing-model-xhigh']}, fetch=data.__getitem__)
            self.assertEqual(caught.exception.code, 'missing_candidate')
            self.assertTrue((Path(temp) / 'snapshot/evidence/missing_candidates.json').exists())
            self.assertFalse((Path(temp) / 'snapshot/candidates.csv').exists())

    def test_prior_paid_model_losing_cost_key_blocks_publication(self):
        archived = json.loads((ROOT / 'runs/2026-09-26-general-grok16/public_candidate_source_map.json').read_text())
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        data[URLS['leader']] = data[URLS['leader']].replace(
            b'intelligenceIndexCostPerTask\\":0.4637245706928438',
            b'intelligenceIndexCostPerTask_REMOVED\\":0.4637245706928438', 1)
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            with self.assertRaises(SourceError) as caught:
                refresh_snapshot(dest, previous=archived, fetch=data.__getitem__)
            self.assertEqual(caught.exception.code, 'missing_candidate')
            self.assertTrue((dest / 'evidence/missing_candidates.json').exists())
            self.assertFalse((dest / 'candidates.csv').exists())

    def test_fresh_fixture_provenance(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            result = refresh_snapshot(dest, previous=None, fetch=data.__getitem__)
            self.assertEqual(result['version_status'], 'inferred')
            self.assertEqual(result['source_locator']['kind'], 'acquired')
            self.assertTrue((dest / 'candidates.csv').exists())

    def test_archived_source_map_is_valid_previous_inventory(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        archived = json.loads((ROOT / 'runs/2026-09-26-general-grok16/public_candidate_source_map.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            refresh_snapshot(dest, previous=archived, fetch=data.__getitem__)
            with (dest / 'candidates.csv').open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 155)
            self.assertEqual(len([r for r in rows if r['effort'] in ("Jan '25", '0902', 'June 2026')]), 0)
            self.assertTrue(all(r['model_version'] for r in rows))
            excluded = json.loads((dest / 'free-sidecar.json').read_text())['excluded_non_paid_or_unusable']
            self.assertTrue(any(row['reason'] == 'missing_score_or_cost' for row in excluded))


if __name__ == '__main__':
    unittest.main()
