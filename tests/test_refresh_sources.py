import json
import csv
import tempfile
import unittest
from unittest.mock import patch
from decimal import Decimal
from pathlib import Path

from scripts.aa_public import SourceError, parse_leaderboard, parse_release, corroborate_version
from scripts.meta_pricing import parse_meta_pricing, rescale_contributor
from scripts.meta_availability import parse_meta_models, unavailable_reason, MODELS_URL
from scripts.refresh_snapshot import refresh_snapshot, _diagnostic
from scripts.refresh_snapshot import _model_effort
from scripts.refresh_inventory import classify_record

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests/fixtures/refresh'
URLS = {'leader': 'https://artificialanalysis.ai/leaderboards/models',
        'grok': 'https://artificialanalysis.ai/models/releases/grok-4-7',
        'muse': 'https://artificialanalysis.ai/models/releases/muse-spark-1-3',
         'meta': 'https://dev.meta.ai/docs/pricing-rate-limits', 'models': MODELS_URL}


def flight_record(raw):
    """Wrap a small first-party model JSON object in its escaped Flight transport."""
    return '<script>self.__next_f.push([1,' + json.dumps(raw) + '])</script>'


class RefreshSourcesTest(unittest.TestCase):
    def test_current_minimized_fixture_provenance_and_exact_primary_values(self):
        import hashlib
        from refresh_inventory_fixtures import GPT_ENTRIES
        raw = (FIX / 'current-inventory-2026-09-30-flight.html').read_bytes()
        provenance = json.loads((FIX / 'current-inventory-2026-09-30.json').read_text())
        self.assertEqual(provenance['fixture_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(provenance['publication'], 'ef77e1fff6980164aac5c0610ead7eff26bcd671')
        self.assertEqual(provenance['run'], '36666859368-1')
        records = {r['slug']: r for r in parse_leaderboard(raw.decode())}
        for slug, effort, score, cost in GPT_ENTRIES:
            with self.subTest(slug=slug):
                self.assertEqual(records[slug]['score'], Decimal(score))
                self.assertEqual(records[slug]['cost_per_task'], Decimal(cost))
                self.assertEqual(records[slug]['creator'], 'OpenAI')
                self.assertIs(records[slug]['deprecated'], False)
                self.assertIn('(' + effort + ')', records[slug]['name'])
        self.assertIs(records['inkling']['deprecated'], False)
        self.assertIs(records['minimax-m2-7']['deprecated'], True)

    def test_fresh_current_inventory_succeeds_without_old_cost(self):
        from refresh_inventory_fixtures import refresh_pages, GPT_ENTRIES
        pages = refresh_pages()
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'fresh'
            prov = refresh_snapshot(dest, previous={'slugs': ['inkling', 'minimax-m2-7']}, fetch=pages.__getitem__)
            with (dest / 'candidates.csv').open(newline='') as stream:
                rows = list(csv.DictReader(stream))
            public = {r['model_version'] for r in rows if r['pricing_plan'] != 'Contributor'}
            self.assertTrue({entry[0] for entry in GPT_ENTRIES}.issubset(public))
            self.assertFalse({'inkling', 'minimax-m2-7'} & public)
            rec = json.loads((dest / 'evidence/source_map.json').read_text())['reconciliation']
            self.assertIn('inkling', rec['tracked_slugs'])
            self.assertNotIn('minimax-m2-7', rec['tracked_slugs'])
            self.assertTrue(any('未沿用舊價' in c for c in prov['caveats']))

    def test_tracking_next_refresh_and_precise_blocking_diagnostics(self):
        from refresh_inventory_fixtures import refresh_pages, flight
        pages = refresh_pages()
        records = parse_leaderboard(pages[URLS['leader']].decode())
        for change in ('retired_absent', 'tracked_absent', 'restored', 'estimated', 'both'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temp:
                current = [dict(r) for r in records if not (change in ('retired_absent', 'both') and r['slug'] == 'minimax-m2-7')]
                if change in ('tracked_absent', 'both'):
                    current = [r for r in current if r['slug'] != 'inkling']
                if change in ('restored', 'estimated'):
                    item = next(r for r in current if r['slug'] == 'inkling')
                    item['cost_per_task'] = Decimal('1')
                    item['is_estimated'] = change == 'estimated'
                data = dict(pages, **{})
                data[URLS['leader']] = flight(current)
                dest = Path(temp) / 'snapshot'
                previous = {'slugs': ['inkling']}
                if change in ('tracked_absent', 'estimated', 'both'):
                    with self.assertRaises(SourceError) as caught:
                        refresh_snapshot(dest, previous=previous, fetch=data.__getitem__)
                    self.assertEqual(caught.exception.code, 'present_candidate_unusable' if change == 'estimated' else 'missing_candidate')
                    artifact = 'unusable_candidates.json' if change == 'estimated' else 'missing_candidates.json'
                    self.assertTrue((dest / 'evidence' / artifact).exists())
                    self.assertTrue((dest / 'evidence/source_map.json').exists())
                else:
                    refresh_snapshot(dest, previous=previous, fetch=data.__getitem__)

    def test_missing_and_unusable_failures_both_preserve_precise_evidence(self):
        from refresh_inventory_fixtures import refresh_pages, flight
        pages = refresh_pages()
        records = parse_leaderboard(pages[URLS['leader']].decode())
        next(r for r in records if r['slug'] == 'inkling')['is_estimated'] = True
        pages[URLS['leader']] = flight(records)
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            with self.assertRaises(SourceError) as caught:
                refresh_snapshot(dest, previous={'slugs': ['absent', 'inkling']}, fetch=pages.__getitem__)
            self.assertEqual(caught.exception.code, 'missing_candidate')
            missing = json.loads((dest / 'evidence/missing_candidates.json').read_text())
            unusable = json.loads((dest / 'evidence/unusable_candidates.json').read_text())
            self.assertEqual([r['slug'] for r in missing], ['absent'])
            self.assertEqual([(r['slug'], r['reason']) for r in unusable], [('inkling', 'estimated')])

    def test_deprecated_accepts_only_optional_boolean(self):
        base = {'slug': 'inkling', 'name': 'Inkling (xhigh)', 'shortName': 'Inkling',
                'modelCreatorName': 'Thinking Machines', 'intelligenceIndex': 24.9847810999384,
                'intelligenceIndexIsEstimated': False, 'intelligenceIndexCostPerTask': 0.6070445010820831}
        for value in (True, False, None):
            with self.subTest(value=value):
                row = parse_leaderboard(flight_record(json.dumps({**base, 'deprecated': value})))[0]
                self.assertIs(row['deprecated'], value)
        self.assertIsNone(parse_leaderboard(flight_record(json.dumps(base)))[0]['deprecated'])
        for value in (0, 1, 'false', {}, []):
            with self.subTest(value=value):
                with self.assertRaises(SourceError) as caught:
                    parse_leaderboard(flight_record(json.dumps({**base, 'deprecated': value})))
                self.assertEqual(caught.exception.code, 'invalid_measurement')
                self.assertEqual(caught.exception.url, URLS['leader'])
                self.assertIn('inkling: deprecated', str(caught.exception))

    def test_models_page_proves_exact_muse_version_and_max_plan_restriction(self):
        html = (FIX / 'models.html').read_text()
        fact = parse_meta_models(html)
        self.assertEqual(fact['model_id'], 'muse-spark-1.3')
        self.assertEqual(fact['max_plan'], 'Standard')
        for change in (html.replace('available on Standard tier only', 'available on both tiers'),
                       html.replace('muse-spark-1.3</code>', 'muse-spark-1.2</code>'),
                       html.replace('Supports all', 'Does not support all'),
                       html.replace('Recommended for new work.', 'Contributor now supports max. Recommended for new work.')):
            self.assertNotEqual(change, html)
            with self.subTest(change=change), self.assertRaises(SourceError):
                parse_meta_models(change + '<footer>Muse Spark 1.3 muse-spark-1.3 max available on Standard tier only</footer>')

    def test_eligibility_is_exact_identity_not_family_or_rate_inference(self):
        bad = dict(model='Muse Spark 1.3', effort='max', pricing_plan='Contributor',
                   identity='Muse Spark 1.3 max Meta Contributor')
        self.assertIn(MODELS_URL, unavailable_reason(bad))
        for update in (dict(effort='xhigh', identity='Muse Spark 1.3 xhigh Meta Contributor'),
                       dict(pricing_plan='published-price', identity='Muse Spark 1.3 max AA-public published-price'),
                       dict(pricing_plan='Standard', identity='Muse Spark 1.3 max Meta Standard'),
                       dict(model='Muse Spark 1.2', identity='Muse Spark 1.2 max Meta Contributor'),
                       dict(model='Muse Spark 1.30', identity='Muse Spark 1.30 max Meta Contributor'),
                       dict(model='Grok 4.7', identity='Grok 4.7 max Meta Contributor')):
            self.assertIsNone(unavailable_reason(dict(bad, **update)))

    def test_structured_and_identity_aliases_must_agree_on_disproven_identity(self):
        canonical = dict(model='Muse Spark 1.3', effort='max', pricing_plan='Contributor',
                         identity='Muse Spark 1.3 max Meta Contributor')
        self.assertIn(MODELS_URL, unavailable_reason(dict(canonical, model='Muse Spark 1.3 (max)')))
        self.assertIn(MODELS_URL, unavailable_reason(dict(canonical, model='muse-spark-1.3')))
        self.assertIn(MODELS_URL, unavailable_reason(dict(canonical, model='Muse Spark1.3')))
        self.assertIn(MODELS_URL, unavailable_reason(dict(canonical, model='muse-spark-1-3')))
        for update in (dict(model='Grok 4.7'),
                       dict(identity='Grok 4.7 max Meta Contributor'),
                       dict(effort='xhigh'),
                       dict(pricing_plan='Standard'),
                       dict(model='Muse Spark 1.3 (xhigh)')):
            with self.subTest(update=update), self.assertRaisesRegex(ValueError, 'identity_mismatch'):
                unavailable_reason(dict(canonical, **update))

    def test_previous_max_retires_only_with_models_proof_and_saves_audit(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        archived = json.loads((ROOT / 'runs/2026-09-26-general-grok16/public_candidate_source_map.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            refresh_snapshot(dest, previous=archived, fetch=data.__getitem__)
            with (dest / 'candidates.csv').open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), sum(classify_record(r)['state'] == 'usable_paid'
                                          for r in parse_leaderboard(data[URLS['leader']].decode())) + 1)
            self.assertEqual([r['effort'] for r in rows if r['pricing_plan'] == 'Contributor'], ['xhigh'])
            self.assertTrue(any(r['effort'] == 'max' and r['pricing_plan'] == 'published-price' for r in rows))
            audit = json.loads((dest / 'evidence/availability.json').read_text())
            self.assertEqual(audit['retired_previous_efforts'][0]['effort'], 'max')
            self.assertEqual(audit['retired_previous_efforts'][0]['source_url'], MODELS_URL)
            self.assertEqual(json.loads((dest / 'evidence/source_map.json').read_text())['inventory']['contributor_efforts'], ['xhigh'])
            self.assertEqual(json.loads((dest / 'evidence/meta_models.json').read_text())['max_plan'], 'Standard')
            self.assertEqual((dest / 'evidence/models.html').read_bytes(), data[MODELS_URL])
            self.assertEqual(len(json.loads((dest / 'evidence/sources.json').read_text())['sha256_by_url']), 5)

    def test_previous_max_retirement_audit_survives_unrelated_missing_candidate(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        before = data[URLS['leader']]
        data[URLS['leader']] = before.replace(b'intelligenceIndexCostPerTask\\":0.4637245706928438',
                                               b'intelligenceIndexCostPerTask\\":\\"$undefined\\"', 1)
        self.assertNotEqual(before, data[URLS['leader']])
        archived = json.loads((ROOT / 'runs/2026-09-26-general-grok16/public_candidate_source_map.json').read_text())
        archived['source_by_slug']['actually-missing'] = {}
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            with self.assertRaises(SourceError) as caught:
                refresh_snapshot(dest, previous=archived, fetch=data.__getitem__)
            self.assertEqual(caught.exception.code, 'missing_candidate')
            self.assertEqual(json.loads((dest / 'evidence/availability.json').read_text())['retired_previous_efforts'][0]['effort'], 'max')
            self.assertTrue((dest / 'evidence/missing_candidates.json').exists())
            self.assertFalse((dest / 'candidates.csv').exists())

    def test_prior_other_model_or_ambiguous_max_does_not_retire_muse_13(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        for previous, effort in (({'source_by_slug': {}, 'contributor': [{'model': 'Muse Spark 1.2 (max)'}]}, 'max'),
                                 ({'source_by_slug': {}, 'contributor': [{'model': 'Muse Spark 1.2 (xhigh)'}]}, 'xhigh'),
                                 ({'slugs': [], 'contributor_efforts': ['max']}, 'max'),
                                 ({'inventory': {'slugs': [], 'contributor_efforts': ['max']}}, 'max')):
            with self.subTest(previous=previous), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp) / 'snapshot'
                with self.assertRaises(SourceError) as caught:
                    refresh_snapshot(dest, previous=previous, fetch=data.__getitem__)
                self.assertEqual(caught.exception.code, 'missing_candidate')
                audit = json.loads((dest / 'evidence/availability.json').read_text())
                self.assertEqual(audit['retired_previous_efforts'], [])
                missing = json.loads((dest / 'evidence/missing_candidates.json').read_text())
                self.assertEqual(missing[0]['effort'], effort)
                self.assertNotEqual(missing[0]['identity'], 'Muse Spark 1.3 max Meta Contributor')
                self.assertFalse((dest / 'candidates.csv').exists())

    def test_prior_slug_or_model_conflict_fails_closed_before_retirement(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        for contributor in ({'slug': 'muse-spark-1-3-xhigh', 'effort': 'max'},
                            {'slug': 'muse-spark-1-3', 'model': 'Muse Spark 1.2 (max)'},
                            {'model': 'Muse Spark 1.3 (max)', 'identity': 'Grok 4.7 max Meta Contributor'}):
            with self.subTest(contributor=contributor), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp) / 'snapshot'
                with self.assertRaises(SourceError) as caught:
                    refresh_snapshot(dest, previous={'source_by_slug': {},
                        'contributor': [contributor]}, fetch=data.__getitem__)
                self.assertEqual(caught.exception.code, 'previous_inventory_missing')
                self.assertFalse((dest / 'candidates.csv').exists())

    def test_prior_new_source_map_preserves_muse_identity_through_inventory(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / 'first'
            refresh_snapshot(first, previous=None, fetch=data.__getitem__)
            previous = json.loads((first / 'evidence/source_map.json').read_text())
            self.assertEqual(previous['inventory']['contributor_efforts'], ['xhigh'])
            second = Path(temp) / 'second'
            refresh_snapshot(second, previous=previous, fetch=data.__getitem__)
            self.assertEqual(json.loads((second / 'evidence/availability.json').read_text())['retired_previous_efforts'], [])

    def test_prior_supported_model_alias_max_is_retired_not_misclassified_missing(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            refresh_snapshot(dest, previous={'source_by_slug': {},
                                              'contributor': [{'model': 'Muse Spark1.3 (max)'}]},
                             fetch=data.__getitem__)
            audit = json.loads((dest / 'evidence/availability.json').read_text())
            self.assertEqual(audit['retired_previous_efforts'][0]['identity'], 'Muse Spark 1.3 max Meta Contributor')

    def test_optional_price_scalars_use_strict_numeric_decimals_or_missing(self):
        base = {'slug': 'inkling', 'name': 'Inkling (xhigh)', 'shortName': 'Inkling',
                'modelCreatorName': 'Thinking Machines', 'intelligenceIndex': 24.9847810999384,
                'intelligenceIndexIsEstimated': False, 'intelligenceIndexCostPerTask': 0.6070445010820831}
        fields = {'price1mInputTokens': 'price1m_input', 'price1mOutputTokens': 'price1m_output',
                  'cacheHitPrice': 'cache_hit_price'}
        for source, parsed in fields.items():
            for raw, expected in (('0.0000123456789012345', Decimal('0.0000123456789012345')),
                                  ('1.25e-6', Decimal('1.25e-6')),
                                  (0.15, Decimal('0.15')), (0, 0), ('$undefined', None), (None, None)):
                with self.subTest(source=source, raw=raw):
                    row = parse_leaderboard(flight_record(json.dumps({**base, source: raw})))[0]
                    self.assertEqual(row[parsed], expected)
                    if expected is None:
                        self.assertIsNone(row[parsed])
            row = parse_leaderboard(flight_record(json.dumps(base)))[0]
            self.assertIsNone(row[parsed])
            for bad in ('garbage', '$Undefined', 'NaN', 'Infinity', ' 0.25 ',
                        True, False, {}, [], float('nan'), float('inf'), '-0.1', -1):
                with self.subTest(source=source, bad=bad):
                    with self.assertRaises(SourceError) as caught:
                        parse_leaderboard(flight_record(json.dumps({**base, source: bad})))
                    self.assertEqual(caught.exception.code, 'invalid_measurement')
                    self.assertIn('inkling: ' + source, str(caught.exception))

    def test_saved_flight_undefined_is_missing_not_free_or_numeric(self):
        # Minimal real failed-page model: its score is numeric, but the cost
        # arrived as the literal string "$undefined" inside the Flight JSON.
        raw = ('{"slug":"mistral-medium-3-1","name":"Mistral Medium 3.1",'
               '"modelCreatorName":"Mistral","shortName":"Mistral Medium 3.1",'
               '"intelligenceIndex":9.18437902519296,"intelligenceIndexIsEstimated":false,'
               '"intelligenceIndexCostPerTask":"$undefined"}')
        html = flight_record(raw)
        self.assertIn(r'\"intelligenceIndexCostPerTask\":\"$undefined\"', html)
        row = parse_leaderboard(html)[0]
        self.assertEqual(row['score'], Decimal('9.18437902519296'))
        self.assertIsNone(row['cost_per_task'])
        missing_score = parse_leaderboard(flight_record(raw.replace('9.18437902519296', '"$undefined"')))[0]
        self.assertIsNone(missing_score['score'])
        self.assertIsNone(missing_score['cost_per_task'])

        # A never-paid model is sidecar material; a prior paid model instead
        # must trip the missing-candidate guard (covered below).
        base = (FIX / 'leader.html').read_bytes()
        altered = base.replace(b'intelligenceIndexCostPerTask\\":0.4637245706928438',
                               b'intelligenceIndexCostPerTask\\":\\"$undefined\\"', 1)
        self.assertNotEqual(base, altered)
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        data[URLS['leader']] = altered
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            refresh_snapshot(dest, previous=None, fetch=data.__getitem__)
            excluded = json.loads((dest / 'free-sidecar.json').read_text())['excluded_non_paid_or_unusable']
            self.assertTrue(any(r['reason'] == 'missing_task_cost' for r in excluded))
            self.assertIn({'slug': 'apodex-1-1', 'name': 'Apodex 1.1', 'reason': 'missing_task_cost'}, excluded)
            self.assertFalse(any(r['reason'] == 'zero_cost' and r['slug'] == 'apodex-1-1' for r in excluded))

    def test_bad_scalar_fields_fail_with_slug_and_field(self):
        base = {'slug': 'inkling', 'name': 'Inkling (xhigh)', 'shortName': 'Inkling',
                'modelCreatorName': 'Thinking Machines', 'intelligenceIndex': 24.9847810999384,
                'intelligenceIndexIsEstimated': False, 'intelligenceIndexCostPerTask': 0.6070445010820831}
        for field in ('intelligenceIndex', 'intelligenceIndexCostPerTask'):
            for bad in ('garbage', '$undefined', '$Undefined', '0.6070445010820831',
                        True, False, {}, [], float('nan'), float('inf')):
                if bad == '$undefined':
                    continue
                with self.subTest(field=field, bad=bad):
                    with self.assertRaises(SourceError) as caught:
                        parse_leaderboard(flight_record(json.dumps({**base, field: bad})))
                    self.assertEqual(caught.exception.code, 'invalid_measurement')
                    self.assertIn('inkling', str(caught.exception))
                    self.assertIn(field, str(caught.exception))
        with self.assertRaises(SourceError) as caught:
            parse_leaderboard(flight_record(json.dumps({**base, 'intelligenceIndexCostPerTask': -1})))
        self.assertEqual(caught.exception.code, 'invalid_measurement')

    def test_null_absent_zero_and_precision_stay_distinct(self):
        base = ('{"slug":"inkling","name":"Inkling (xhigh)","shortName":"Inkling",'
                '"modelCreatorName":"Thinking Machines","intelligenceIndex":24.9847810999384,'
                '"intelligenceIndexIsEstimated":false')
        for suffix, expected in (('', None), (',"intelligenceIndexCostPerTask":null', None),
                                 (',"intelligenceIndexCostPerTask":0', 0),
                                 (',"intelligenceIndexCostPerTask":0.6070445010820831',
                                  Decimal('0.6070445010820831'))):
            with self.subTest(suffix=suffix):
                row = parse_leaderboard(flight_record(base + suffix + '}'))[0]
                self.assertEqual(row['score'], Decimal('24.9847810999384'))
                self.assertEqual(row['cost_per_task'], expected)
                if expected is None:
                    self.assertIsNone(row['cost_per_task'])

    def test_release_and_crosscheck_reject_invalid_scalars(self):
        release_html = (FIX / 'grok.html').read_text()
        marker = 'intelligenceIndexCostPerTask\\":{\\"cost\\":{\\"total\\":3.738325952106939'
        self.assertIn(marker, release_html)
        for value in ('true', 'NaN', '\\"not-a-number\\"', '-1'):
            with self.subTest(value=value):
                with self.assertRaises(SourceError) as caught:
                    parse_release(release_html.replace(marker, marker.replace('3.738325952106939', value), 1),
                                  URLS['grok'])
                self.assertEqual(caught.exception.code, 'invalid_measurement')
                self.assertIn('intelligenceIndexCostPerTask.cost.total', str(caught.exception))
        with self.assertRaises(SourceError) as caught:
            parse_release(release_html.replace(marker, marker.replace('3.738325952106939', 'null'), 1),
                          URLS['grok'])
        self.assertEqual(caught.exception.code, 'release_shape_drift')
        rows = parse_leaderboard((FIX / 'leader.html').read_text())
        releases = [parse_release((FIX / k).with_suffix('.html').read_text(), URLS[k]) for k in ('grok', 'muse')]
        target = next(r for r in rows if r['slug'] == 'grok-4-7-high')
        for value in (True, 'garbage', float('nan')):
            with self.subTest(crosscheck=value):
                target['score'] = value
                with self.assertRaises(SourceError) as caught:
                    corroborate_version(rows, releases)
                self.assertEqual(caught.exception.code, 'invalid_measurement')
                self.assertIn('grok-4-7-high: intelligenceIndex', str(caught.exception))
        target['score'] = Decimal('46.3321770885625')
        target['cost_per_task'] = '$undefined'
        with self.assertRaises(SourceError) as caught:
            corroborate_version(rows, releases)
        self.assertEqual(caught.exception.code, 'invalid_measurement')
        self.assertIn('grok-4-7-high: intelligenceIndexCostPerTask', str(caught.exception))

    def test_missing_prior_paid_score_blocks_and_keeps_diagnostic(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        before = data[URLS['leader']]
        data[URLS['leader']] = before.replace(b'intelligenceIndex\\":26.4103686249117',
                                              b'intelligenceIndex\\":\\"$undefined\\"', 1)
        self.assertNotEqual(before, data[URLS['leader']])
        archived = json.loads((ROOT / 'runs/2026-09-26-general-grok16/public_candidate_source_map.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            with self.assertRaises(SourceError) as caught:
                refresh_snapshot(dest, previous=archived, fetch=data.__getitem__)
            self.assertEqual(caught.exception.code, 'present_candidate_unusable')
            missing = json.loads((dest / 'evidence/unusable_candidates.json').read_text())
            self.assertTrue(any(r['record']['score'] is None and r['reason'] == 'missing_score' for r in missing))
            self.assertFalse((dest / 'candidates.csv').exists())

    def test_saved_two_paid_missing_costs_are_disclosed_without_stale_prices(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in ('grok', 'muse', 'meta', 'models')}
        data[URLS['leader']] = (FIX / 'failed-two-costs-flight.html').read_bytes()
        previous = {'slugs': ['inkling', 'minimax-m2-7']}
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            provenance = refresh_snapshot(dest, previous=previous, fetch=data.__getitem__)
            self.assertEqual(len([c for c in provenance['caveats'] if '未沿用舊價' in c]), 2)
            mapping = json.loads((dest / 'evidence/source_map.json').read_text())
            self.assertFalse({'inkling', 'minimax-m2-7'} & set(mapping['inventory']['slugs']))
            self.assertTrue((dest / 'candidates.csv').exists())

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

    def test_name_first_model_record_is_not_lost(self):
        base = {'name': 'New Model (high)', 'slug': 'new-model-high', 'shortName': 'New Model',
                'modelCreatorName': 'New Creator', 'intelligenceIndex': 42.125,
                'intelligenceIndexIsEstimated': False, 'intelligenceIndexCostPerTask': 0.275}
        good = '<script>self.__next_f.push([1,' + json.dumps(json.dumps(base)) + '])</script>'
        parsed = parse_leaderboard(good)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['slug'], 'new-model-high')
        self.assertEqual(parsed[0]['cost_per_task'], Decimal('0.275'))
        bad = json.dumps(base).replace('"intelligenceIndex": 42.125', '"intelligenceIndex": oops')
        malformed = '<script>self.__next_f.push([1,' + json.dumps(bad) + '])</script>'
        with self.assertRaises(SourceError) as caught:
            parse_leaderboard(malformed)
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
            self.assertEqual(len([x for x in sidecar['excluded_non_paid_or_unusable'] if x['reason'] == 'zero_cost']),
                             sum(classify_record(r)['reason'] == 'zero_cost' for r in rows))

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

    def test_previous_contributor_effort_loss_records_three_pass_pending_evidence(self):
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            with self.assertRaises(SourceError) as caught:
                refresh_snapshot(dest, previous={'slugs': [], 'contributor_efforts': ['high']},
                                 fetch=data.__getitem__)
            self.assertEqual(caught.exception.code, 'missing_candidate')
            missing = json.loads((dest / 'evidence/missing_candidates.json').read_text())
            self.assertEqual(len(missing), 1)
            row = missing[0]
            self.assertEqual(row['pricing_plan'], 'Contributor')
            self.assertEqual(row['effort'], 'high')
            self.assertIn('high', str(caught.exception))
            for key in ('local_snapshot_search', 'leaderboard_source_check',
                        'model_and_index_check', 'effort_id_disambiguation'):
                self.assertIn(key, row)
            self.assertIn('pending', row['model_and_index_check'].lower())
            self.assertFalse((dest / 'candidates.csv').exists())

    def test_prior_paid_model_losing_score_blocks_publication(self):
        archived = json.loads((ROOT / 'runs/2026-09-26-general-grok16/public_candidate_source_map.json').read_text())
        data = {URLS[k]: (FIX / k).with_suffix('.html').read_bytes() for k in URLS}
        data[URLS['leader']] = data[URLS['leader']].replace(
            b'intelligenceIndex\\":26.4103686249117',
            b'intelligenceIndex\\":null', 1)
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'snapshot'
            with self.assertRaises(SourceError) as caught:
                refresh_snapshot(dest, previous=archived, fetch=data.__getitem__)
            self.assertEqual(caught.exception.code, 'present_candidate_unusable')
            self.assertTrue((dest / 'evidence/unusable_candidates.json').exists())
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
            self.assertEqual(len(rows), sum(classify_record(r)['state'] == 'usable_paid'
                                          for r in parse_leaderboard(data[URLS['leader']].decode())) + 1)
            self.assertEqual(len([r for r in rows if r['effort'] in ("Jan '25", '0902', 'June 2026')]), 0)
            self.assertTrue(all(r['model_version'] for r in rows))
            excluded = json.loads((dest / 'free-sidecar.json').read_text())['excluded_non_paid_or_unusable']
            self.assertTrue(any(row['reason'] in ('missing_score', 'missing_task_cost') for row in excluded))


if __name__ == '__main__':
    unittest.main()
