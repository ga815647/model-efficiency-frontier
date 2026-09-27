"""Acquire an auditable fresh public candidate snapshot; never mutate old runs."""
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import time
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path

from scripts.aa_public import (GROK, LEADERBOARD, MUSE, SourceError,
                               corroborate_version, parse_leaderboard, parse_release)
from scripts.fetch_aa import COLUMNS
from scripts.meta_pricing import URL as META, parse_meta_pricing, rescale_contributor
from scripts.meta_availability import MODELS_URL, parse_meta_models, unavailable_reason

SOURCES = (LEADERBOARD, GROK, MUSE, META, MODELS_URL)


def fetch_public(url: str) -> bytes:
    """Only approved first-party pages; bounded network and retries."""
    if url not in SOURCES:
        raise SourceError('unapproved_url', url)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'model-efficiency-frontier/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.geturl() != url:
                    raise SourceError('redirect', url)
                data = response.read(8_000_001)
                if len(data) > 8_000_000:
                    raise SourceError('oversize', url)
                return data
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == 2:
                raise SourceError('fetch_failed', url, type(exc).__name__) from exc
            time.sleep(attempt + 1)
    raise AssertionError('unreachable')


def _json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n')


def _model_effort(name, slug):
    """Only documented reasoning labels become effort; slug pins checkpoint/variant.

    Dates/versions are *not* reasoning levels; keep their visible qualifier in
    model as well as the slug in model_version. Unknown qualifiers fail closed.
    """
    match = re.fullmatch(r'(.*?)\s*\(([^()]*)\)', name)
    if not match:
        return name.strip(), 'unspecified', slug
    base, qualifier = match.group(1).strip(), match.group(2).strip()
    label = qualifier.lower()
    direct = {'off', 'low', 'medium', 'high', 'xhigh', 'max', 'reasoning', 'non-reasoning'}
    if label in direct:
        return base, label, slug
    effort = re.fullmatch(r'(?:adaptive )?reasoning, (max|xhigh|high|medium|low) effort(?:, .+)?', label)
    if not effort:
        effort = re.fullmatch(r'(max|xhigh|high|medium|low) effort(?:, .+)?', label)
    if not effort:
        effort = re.fullmatch(r'(max|xhigh|high|medium|low), based on .+', label)
    if effort:
        return base, effort.group(1), slug
    if re.fullmatch(r'(?:[A-Za-z]+\s+)?(?:\d{2,4}|\d{4}-\d{2}(?:-\d{2})?|\d{4})', qualifier) or re.fullmatch(
            r"[A-Za-z]+\s+'\d{2}", qualifier):
        return name.strip(), 'unspecified', slug
    raise SourceError('effort_ambiguous', LEADERBOARD, slug)


def _previous_slugs(previous):
    """Runner supplies approved prior inventory as {'slugs': [...]} or {'candidates': [...]}.

    A candidate entry must have a slug or a CSV identity + pricing_plan;
    absence of inventory is valid only for the initial refresh.
    """
    if previous is None:
        return set(), set()
    if 'inventory' in previous:
        return _previous_slugs(previous['inventory'])
    if 'source_by_slug' in previous:
        efforts = set()
        for row in previous.get('contributor', []):
            if 'effort' in row:
                efforts.add(row['effort'])
            elif 'model' in row:
                _, effort, _ = _model_effort(row['model'], 'previous-contributor')
                if effort == 'unspecified':
                    raise SourceError('previous_inventory_missing', MUSE, 'Contributor effort unspecified')
                efforts.add(effort)
            else:
                raise SourceError('previous_inventory_missing', MUSE, 'Contributor identity missing')
        return set(previous['source_by_slug']), efforts
    if 'slugs' in previous:
        return set(previous['slugs']), set(previous.get('contributor_efforts', []))
    if 'candidates' in previous:
        return ({r['slug'] for r in previous['candidates'] if r.get('pricing_plan') != 'Contributor'},
                {r['effort'] for r in previous['candidates'] if r.get('pricing_plan') == 'Contributor'})
    raise SourceError('previous_inventory_missing', LEADERBOARD)


def _diagnostic(evidence, benchmark):
    """Optional, separately versioned API diagnostic; never feeds public candidates."""
    key = os.environ.get('AA_API_KEY')
    if not key:
        return {'status': 'not_collected', 'reason': 'AA_API_KEY absent'}
    base = 'https://artificialanalysis.ai/api/v2/language/models/free'
    versions = set()
    pages = []
    for page in range(1, 21):
        url = f'{base}?page={page}&page_size=200'
        req = urllib.request.Request(url, headers={'x-api-key': key, 'User-Agent': 'model-efficiency-frontier/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read(8_000_001)
            envelope = json.loads(body, parse_float=Decimal)
        except (urllib.error.URLError, ValueError, TimeoutError) as exc:
            raise SourceError('api_diagnostic_failed', base, type(exc).__name__) from exc
        version = envelope.get('intelligence_index_version')
        entries = envelope.get('data')
        if not isinstance(version, str) or not isinstance(entries, list):
            raise SourceError('api_envelope_invalid', base)
        versions.add(version)
        pages.append(envelope)
        if len(entries) < 200:
            break
    else:
        raise SourceError('api_pagination_limit', base)
    _json(evidence / 'api_envelopes.json', pages)
    if len(versions) != 1:
        raise SourceError('api_version_drift', base)
    return {'status': 'collected_separately', 'envelope_version': versions.pop(),
            'public_version': benchmark, 'mixed_into_public_rows': False}


def refresh_snapshot(destination: Path, *, previous: dict | None, fetch=fetch_public) -> dict:
    """Create a new destination only. Failed validation leaves diagnostic evidence, not a CSV.

    Previous inventory: {'slugs': paid_public_slugs, 'contributor_efforts': ['xhigh', ...]}.
    The initial run may use None; normal runner supplies its approved latest-success
    inventory. Do not pass the leaderboard URL through user input.
    """
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    evidence = destination / 'evidence'
    evidence.mkdir()
    today = dt.date.today().isoformat()
    raw = {}
    hashes = {}
    for label, url in zip(('leaderboard', 'grok_release', 'muse_release', 'meta_pricing', 'models'), SOURCES):
        payload = fetch(url)
        if not isinstance(payload, bytes):
            raise SourceError('fetch_invalid', url, 'expected bytes')
        (evidence / (label + '.html')).write_bytes(payload)
        hashes[url] = hashlib.sha256(payload).hexdigest()
        try:
            raw[url] = payload.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise SourceError('encoding_invalid', url) from exc
    capability = parse_meta_models(raw[MODELS_URL])
    _json(evidence / 'sources.json', {'checked_date': today, 'sha256_by_url': hashes})
    _json(evidence / 'meta_models.json', dict(capability, checked_date=today))
    prev_slugs, prev_efforts = _previous_slugs(previous)
    retirement = [{'identity': 'Muse Spark 1.3 max Meta Contributor', 'effort': 'max',
                   'source_url': MODELS_URL, 'checked_date': today,
                   'reason': unavailable_reason({'model': 'Muse Spark 1.3', 'effort': 'max',
                                                 'pricing_plan': 'Contributor'})}] if 'max' in prev_efforts else []
    availability = {'source_url': MODELS_URL, 'checked_date': today,
                    'retired_previous_efforts': retirement, 'excluded_current_identities': []}
    _json(evidence / 'availability.json', availability)
    records = parse_leaderboard(raw[LEADERBOARD])
    releases = [parse_release(raw[url], url) for url in (GROK, MUSE)]
    version = corroborate_version(records, releases)
    meta = parse_meta_pricing(raw[META])
    _json(evidence / 'leaderboard_records.json', records)
    _json(evidence / 'releases.json', releases)
    _json(evidence / 'version.json', version)
    _json(evidence / 'meta_pricing.json', meta)
    included, excluded, rows = {}, [], []
    for item in records:
        score, cost = item['score'], item['cost_per_task']
        reason = ('estimated' if item['is_estimated'] else 'missing_score_or_cost' if score is None or cost is None
                  else 'zero_cost' if Decimal(str(cost)) == 0 else None)
        if reason:
            excluded.append({'slug': item['slug'], 'name': item['name'], 'reason': reason})
            continue
        if any(not Decimal(str(n)).is_finite() for n in (score, cost)) or Decimal(str(cost)) < 0:
            raise SourceError('invalid_measurement', LEADERBOARD, item['slug'])
        model, effort, checkpoint = _model_effort(item['name'], item['slug'])
        included[item['slug']] = {'source_url': LEADERBOARD, 'checked_date': today,
                                  'score': score, 'cost_per_task': cost}
        rows.append({'identity': f'{model} {effort} AA-public published-price',
                     'model': model, 'effort': effort, 'provider': 'AA-public (first-party/median)',
                     'pricing_plan': 'published-price', 'model_version': checkpoint,
                     'benchmark': 'AA-Intelligence-Index', 'benchmark_version': version['benchmark_version'],
                     'score': str(score), 'cost_per_task': str(cost), 'cost_basis': 'api',
                     'privacy': '', 'is_free': 'false', 'evidence_url': LEADERBOARD,
                     'checked_date': today, 'quota': '',
                     'notes': (f'GRADE-A public measured; score_source={LEADERBOARD} slug={item["slug"]}; '
                               f'source_date={today}; version inferred from both release pages and four exact pairs; '
                               'public first-party/provider median, not provider-specific; full-precision flight JSON'),
                     'ttft_s': '', 'time_per_task_s': ''})
    lost = sorted(prev_slugs - included.keys())
    if lost:
        current = {r['slug']: r for r in records}
        _json(evidence / 'missing_candidates.json', [
            {'slug': slug, 'local_snapshot_search': 'present in approved previous inventory',
             'leaderboard_source_check': current.get(slug, 'not present in current page'),
             'model_and_index_check': 'release/model page disambiguation required; not verified absent',
             'effort_id_disambiguation': 'manual review required; do not substitute similar effort/ID'}
            for slug in lost])
        raise SourceError('missing_candidate', LEADERBOARD, ','.join(lost))
    contributors = []
    muse = next(r for r in releases if r['url'] == MUSE)['records']
    # Same-family all available efforts with measured public cost must have
    # their own decomposition; never reuse another effort's blended rate.
    candidates = [r for r in records if r['slug'].startswith('muse-spark-1-3') and
                  r['slug'] in included]
    for item in candidates:
        slug = item['slug']
        model, effort, checkpoint = _model_effort(item['name'], slug)
        reason = unavailable_reason({'model': model, 'effort': effort, 'pricing_plan': 'Contributor'})
        if reason:
            availability['excluded_current_identities'].append({'slug': slug,
                'identity': f'{model} {effort} Meta Contributor', 'reason': reason,
                'source_url': MODELS_URL, 'checked_date': today})
            _json(evidence / 'availability.json', availability)
            continue
        if slug not in muse:
            raise SourceError('components_missing', MUSE, slug)
        parts = muse[slug]['components']
        derived = rescale_contributor(parts, meta['USD_per_1M_tokens'])
        limits = meta['rate_limits_per_team']['Contributor']
        notes = (f'GRADE-B DERIVED not AA-measured Contributor; score_source={MUSE}; source_date={today}; '
                 f'Meta pricing={META} checked={today}; formula '
                 f'({parts["nonCacheInput"]}+{parts["cacheWrite"]})×(Contributor input/Standard input) '
                 f'+{parts["cacheRead"]}×(Contributor cached/Standard cached) '
                 f'+{parts["output"]}×(Contributor output/Standard output)={derived}; '
                 'identical tokens/checkpoint assumed across plans; cache-write billed ordinary input '
                 'rate ASSUMPTION not explicitly confirmed by Meta; output already includes reasoning/answer; '
                 'training allowed, limits note only. B caveat required when decisive.')
        rows.append({'identity': f'{model} {effort} Meta Contributor', 'model': model,
                     'effort': effort, 'provider': 'Meta', 'pricing_plan': 'Contributor',
                     'model_version': checkpoint + '@2026-09-02', 'benchmark': 'AA-Intelligence-Index',
                     'benchmark_version': version['benchmark_version'], 'score': str(item['score']),
                     'cost_per_task': str(derived), 'cost_basis': 'api', 'privacy': 'training permitted',
                     'is_free': 'false', 'evidence_url': MUSE, 'checked_date': today,
                     'quota': f'{limits["RPM"]} RPM / {limits["TPM"]} TPM (per team, note only)',
                     'notes': notes, 'ttft_s': '', 'time_per_task_s': ''})
        contributors.append({'slug': slug, 'effort': effort, 'standard_components': parts,
                             'derived_cost': str(derived), 'formula': notes})
    lost_efforts = sorted(prev_efforts - {r['effort'] for r in contributors} - {'max'})
    if lost_efforts:
        # An effort is a previous plan identity, not proof that its exact slug
        # disappeared. Save what the acquired pages actually show and leave
        # source-page/ID disambiguation explicitly pending human review.
        _json(evidence / 'missing_candidates.json', [
            {'identity': f'Muse Spark 1.3 {effort} Meta Contributor',
             'pricing_plan': 'Contributor', 'effort': effort,
             'local_snapshot_search': 'present in approved previous Contributor effort inventory',
             'leaderboard_source_check': {
                 'status': 'observed_current_page_not_exhaustive',
                 'same_family': [{'slug': r['slug'], 'name': r['name'],
                                  'paid_public': r['slug'] in included}
                                 for r in records if r['slug'].startswith('muse-spark-1-3')]},
             'model_and_index_check': 'pending: model page and index search for exact Contributor identity/effort not verified',
             'effort_id_disambiguation': {
                 'status': 'pending_manual_review_do_not_substitute',
                 'release_page_slugs': sorted(muse),
                 'current_contributor_efforts': sorted(r['effort'] for r in contributors)}}
            for effort in lost_efforts])
        raise SourceError('missing_candidate', MUSE, 'previous Contributor efforts lost: ' + ','.join(lost_efforts))
    _json(evidence / 'source_map.json', {'source_by_slug': included, 'excluded': excluded,
                                          'availability': availability,
                                          'contributor': contributors, 'inventory': {'slugs': sorted(included),
                                                                                  'contributor_efforts': sorted(r['effort'] for r in contributors)}})
    diagnostic = _diagnostic(evidence, version['benchmark_version'])
    _json(evidence / 'api_diagnostic.json', diagnostic)
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=COLUMNS)
    writer.writeheader(); writer.writerows(rows)
    data = buf.getvalue().encode('utf-8')
    (destination / 'candidates.csv').write_bytes(data)
    _json(destination / 'free-sidecar.json', {'excluded_non_paid_or_unusable': excluded})
    (destination / 'run-notes.md').write_text(
        f'# Fresh public snapshot {today}\n\n{len(included)} paid public rows; {len(contributors)} GRADE-B '
        f'Contributor rows; {len(excluded)} excluded/unknown. Version {version["benchmark_version"]} '
        'inferred, not declared on leaderboard; release pages match four exact score/cost pairs. '
        'API diagnostic does not determine public version. Contributor assumes cache-write is ordinary input; '
        'limits and training are notes, not ranking factors.\n')
    return {'benchmark': 'AA-Intelligence-Index', 'benchmark_version': version['benchmark_version'],
            'version_status': 'inferred', 'cost_basis': 'api', 'source_dates': [today],
            'caveats': ['Public leaderboard version inferred by two explicit release pages and four exact pairs; not API envelope',
                        'Contributor GRADE-B derived; cache-write charged at ordinary input rate is an assumption'],
            'source_locator': {'kind': 'acquired', 'path': 'snapshot/candidates.csv',
                               'sha256': hashlib.sha256(data).hexdigest()}}
