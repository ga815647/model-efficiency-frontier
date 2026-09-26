import json
import tempfile
import unittest
from unittest.mock import patch
from decimal import Decimal
from pathlib import Path

from scripts.aa_public import SourceError, parse_leaderboard, parse_release, corroborate_version
from scripts.meta_pricing import parse_meta_pricing, rescale_contributor
from scripts.refresh_snapshot import refresh_snapshot, _diagnostic

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

    def test_missing_previous_candidate_blocks(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(SourceError) as caught:
                refresh_snapshot(Path(temp) / 'snapshot', previous={'slugs': ['missing-model-xhigh']}, fetch=data.__getitem__)
            self.assertEqual(caught.exception.code, 'missing_candidate')
            self.assertTrue((Path(temp) / 'snapshot/evidence/missing_candidates.json').exists())
            self.assertFalse((Path(temp) / 'snapshot/candidates.csv').exists())

    def test_fresh_fixture_provenance(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            result = refresh_snapshot(dest, previous=None, fetch=data.__getitem__)
            self.assertEqual(result['version_status'], 'inferred')
            self.assertEqual(result['source_locator']['kind'], 'acquired')
            self.assertTrue((dest / 'candidates.csv').exists())


if __name__ == '__main__':
    unittest.main()
