"""Strict, precision-preserving adapters for the approved AA public pages."""
import json
import re
from decimal import Decimal

LEADERBOARD = 'https://artificialanalysis.ai/leaderboards/models'
GROK = 'https://artificialanalysis.ai/models/releases/grok-4-7'
MUSE = 'https://artificialanalysis.ai/models/releases/muse-spark-1-3'
RELEASE_SLUGS = {GROK: ('grok-4-7-high', 'grok-4-7'),
                 MUSE: ('muse-spark-1-3-xhigh', 'muse-spark-1-3')}
FLIGHT = re.compile(r'self\.__next_f\.push\(\[\d+,\s*("(?:\\.|[^"\\])*")\]\)')
OBJECT = re.compile(r'\{(?:"id":"[^"]+",)?"slug":')


class SourceError(ValueError):
    def __init__(self, code, url, detail=''):
        self.code, self.url = code, url
        super().__init__(f'{code}: {url}: {detail}')


def _objects(html, url):
    decoder = json.JSONDecoder(parse_float=Decimal)
    found = False
    for match in FLIGHT.finditer(html):
        try:
            chunk = json.loads(match[1])
        except ValueError as exc:
            raise SourceError('markup_drift', url, 'invalid flight string') from exc
        for item in OBJECT.finditer(chunk):
            try:
                record, _ = decoder.raw_decode(chunk, item.start())
            except ValueError:
                continue
            if isinstance(record, dict) and 'slug' in record:
                found = True
                yield record
    if not found:
        raise SourceError('markup_drift', url, 'no JSON flight slug records')


def _unique(records, url):
    result = {}
    for record in records:
        slug = record['slug']
        if not isinstance(slug, str) or not slug:
            raise SourceError('invalid_identity', url, 'empty slug')
        if slug in result and result[slug] != record:
            raise SourceError('conflicting_slug', url, slug)
        result[slug] = record
    if not result:
        raise SourceError('markup_drift', url, 'no measured records')
    return result


def parse_leaderboard(html: str) -> list[dict]:
    records = []
    for obj in _objects(html, LEADERBOARD):
        if 'intelligenceIndexCostPerTask' not in obj or 'name' not in obj:
            continue
        if not isinstance(obj['name'], str) or not isinstance(obj.get('intelligenceIndexIsEstimated'), bool):
            raise SourceError('invalid_measurement', LEADERBOARD, str(obj.get('slug')))
        records.append({'slug': obj['slug'], 'name': obj['name'],
                        'creator': obj.get('modelCreatorName'),
                        'score': obj.get('intelligenceIndex'),
                        'cost_per_task': obj['intelligenceIndexCostPerTask'],
                        'is_estimated': obj.get('intelligenceIndexIsEstimated'),
                        'deprecated': obj.get('deprecated'),
                        'price1m_input': obj.get('price1mInputTokens'),
                        'price1m_output': obj.get('price1mOutputTokens'),
                        'cache_hit_price': obj.get('cacheHitPrice')})
    return list(_unique(records, LEADERBOARD).values())


def parse_release(html: str, url: str) -> dict:
    if url not in RELEASE_SLUGS:
        raise SourceError('unapproved_url', url)
    versions = set(re.findall(r'Artificial Analysis Intelligence Index v(\d+\.\d+(?:\.\d+)?)', html))
    if len(versions) != 1:
        raise SourceError('version_missing', url, 'requires one explicit release-page version')
    selected = set(RELEASE_SLUGS[url])
    records = []
    for obj in _objects(html, url):
        if obj['slug'] not in selected or not isinstance(obj.get('intelligenceIndexCostPerTask'), dict):
            continue
        cost = obj['intelligenceIndexCostPerTask'].get('cost', {})
        records.append({'slug': obj['slug'], 'score': obj.get('intelligenceIndex'),
                        'cost_per_task': cost.get('total'), 'components': cost})
    return {'url': url, 'declared_version': versions.pop(), 'records': _unique(records, url)}


def corroborate_version(records: list[dict], releases: list[dict]) -> dict:
    if {r.get('url') for r in releases} != set(RELEASE_SLUGS) or len(releases) != 2:
        raise SourceError('release_missing', LEADERBOARD)
    versions = {r['declared_version'] for r in releases}
    if len(versions) != 1:
        raise SourceError('version_disagreement', LEADERBOARD)
    public = _unique(records, LEADERBOARD)
    crosschecks = []
    for release in releases:
        for slug in RELEASE_SLUGS[release['url']]:
            row = release['records'].get(slug)
            if not row or slug not in public or any(
                    row.get(k) is None or public[slug].get(k) is None or
                    Decimal(str(row[k])) != Decimal(str(public[slug][k]))
                    for k in ('score', 'cost_per_task')):
                raise SourceError('crosscheck_mismatch', release['url'], slug)
            crosschecks.append({'slug': slug, 'url': release['url'],
                                'score': public[slug]['score'], 'cost_per_task': public[slug]['cost_per_task']})
    return {'benchmark_version': 'AA-Intelligence-Index-v' + versions.pop(),
            'version_status': 'inferred', 'crosschecks': crosschecks}
