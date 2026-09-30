from decimal import Decimal
import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path

from scripts.aa_public import LEADERBOARD, parse_leaderboard
from scripts.fetch_aa import COLUMNS
from scripts.refresh_inventory import build_reconciliation, source_exit_caveats
from scripts.refresh_snapshot import _model_effort


def numeric_json(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k) + ':' + numeric_json(v) for k, v in value.items()) + '}'
    if isinstance(value, list):
        return '[' + ','.join(numeric_json(v) for v in value) + ']'
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def flight(records):
    objects = [dict(slug=r['slug'], name=r['name'], shortName=r['name'],
        modelCreatorName=r['creator'], intelligenceIndex=r['score'],
        intelligenceIndexIsEstimated=r['is_estimated'],
        intelligenceIndexCostPerTask=r['cost_per_task'], deprecated=r['deprecated']) for r in records]
    return ''.join('<script>self.__next_f.push([1,' + json.dumps(numeric_json(obj)) + '])</script>'
                   for obj in objects).encode()


def inventory_bundle(records, previous_slugs):
    from bridge.result import calculate_snapshot, make_envelope
    from test_bridge_request import request_data
    from test_bridge_result import PARAMETERS

    raw = flight(records)
    parsed = parse_leaderboard(raw.decode())
    rec = build_reconciliation(parsed, previous_slugs)
    rows, sources, excluded = [], {}, []
    for item in parsed:
        slug = item['slug']
        fact = rec['status_by_slug'][slug]
        if fact['state'] != 'usable_paid':
            excluded.append(dict(slug=slug, name=item['name'], reason=fact['reason']))
            continue
        model, effort, checkpoint = _model_effort(item['name'], slug)
        row = dict.fromkeys(COLUMNS, '')
        row.update(identity=f'{model} {effort} AA-public published-price', model=model,
                   effort=effort, model_version=checkpoint, provider='AA-public (first-party/median)',
                   pricing_plan='published-price', benchmark='AA-Intelligence-Index',
                   benchmark_version='AA-Intelligence-Index-v4.3.2', cost_basis='api',
                   score=str(item['score']), cost_per_task=str(item['cost_per_task']),
                   checked_date='2026-09-30', evidence_url=LEADERBOARD, is_free='false',
                   notes=f'GRADE-A fixture; slug={slug};')
        rows.append(row)
        sources[slug] = dict(source_url=LEADERBOARD, checked_date='2026-09-30',
                             score=item['score'], cost_per_task=item['cost_per_task'])
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    data = buf.getvalue().encode()
    mapping = dict(reconciliation=rec, source_by_slug=sources, excluded=excluded,
                   inventory=dict(slugs=sorted(sources), contributor_efforts=[]), contributor=[])
    provenance = dict(benchmark='AA-Intelligence-Index', benchmark_version='AA-Intelligence-Index-v4.3.2',
                      cost_basis='api', version_status='inferred', source_dates=['2026-09-30'],
                      source_locator=dict(kind='acquired', path='snapshot/candidates.csv',
                                          sha256=hashlib.sha256(data).hexdigest()),
                      caveats=['Inventory-unit fixture, not live acquisition'] + source_exit_caveats(parsed, rec))
    evidence = {'leaderboard.html': raw,
                'leaderboard_records.json': json.dumps(parsed, default=str).encode(),
                'sources.json': json.dumps({'sha256_by_url': {LEADERBOARD: hashlib.sha256(raw).hexdigest()}}).encode()}
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'candidates.csv'
        path.write_bytes(data)
        calculation, _ = calculate_snapshot(path, PARAMETERS, provenance)
        data = path.read_bytes()
    envelope = make_envelope(request_data(), dict(request_commit_sha='b' * 40,
        run_id='inventory-unit', run_attempt=1,
        run_url='https://github.com/example/actions/runs/inventory-unit'),
        calculation=calculation, errors=[])
    return data, mapping, envelope, evidence


def record(slug, *, name=None, score='40', cost='1', estimated=False, deprecated=False):
    scalar = lambda value: Decimal(value) if type(value) is str else value
    return dict(slug=slug, name=name or slug, creator='Fixture',
                score=scalar(score), cost_per_task=scalar(cost), is_estimated=estimated,
                deprecated=deprecated, price1m_input=None, price1m_output=None, cache_hit_price=None)
