"""Validated serving routes beside immutable model-family result contracts.

Advertised support is research. Numeric route scenarios additionally require an
owner-accepted factor, terms acceptance and exact, sourced applicability proof.
"""
from copy import deepcopy
from datetime import date
import hashlib
import math
import re
from urllib.parse import urlsplit

from .publish import _json
from .result import validate_envelope
from .result_v1 import extra

GATES = ('alias', 'version', 'effort', 'quantization', 'region', 'use_case', 'current_terms')
_ID = re.compile(r'[a-z0-9]+(?:[._-][a-z0-9]+)*\Z')
_LABELS = ('confirmed', 'potential', 'conflicting', 'historical')


def _fields(value, keys, error):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError(error)


def _text(value):
    return type(value) is str and bool(value.strip())


def _day(value):
    if type(value) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('invalid_serving_date')
    date.fromisoformat(value)


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def _records(items, fields):
    if type(items) is not list or not items:
        raise ValueError('invalid_serving_records')
    mapped = {}
    for item in items:
        _fields(item, fields, 'invalid_serving_record')
        key = item['id']
        if type(key) is not str or not _ID.fullmatch(key) or key in mapped:
            raise ValueError('duplicate_or_invalid_serving_id')
        mapped[key] = item
    return mapped


def _references(ids, sources):
    if (type(ids) is not list or not ids or any(type(s) is not str for s in ids)
            or len(set(ids)) != len(ids) or not set(ids) <= set(sources)):
        raise ValueError('invalid_serving_source_reference')


def validate_research(research):
    _fields(research, ('schema_version', 'research_id', 'as_of', 'provider_id', 'sources', 'findings'),
            'invalid_serving_research')
    if (type(research['schema_version']) is not int or research['schema_version'] != 1
            or not _text(research['research_id']) or not _text(research['provider_id'])):
        raise ValueError('invalid_serving_research')
    _day(research['as_of'])
    sources = _records(research['sources'], ('id', 'url', 'updated_at', 'checked_date', 'verification', 'notes'))
    for source in sources.values():
        parsed = urlsplit(source['url']) if type(source['url']) is str else None
        if (not parsed or parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password
                or source['verification'] not in ('retrieved_official', 'owner_supplied_not_retrieved')
                or not _text(source['updated_at']) or not _text(source['notes'])):
            raise ValueError('invalid_serving_research_source')
        _day(source['checked_date'])
        if source['checked_date'] > research['as_of']:
            raise ValueError('invalid_serving_research_date')
    if type(research['findings']) is not list or not research['findings']:
        raise ValueError('invalid_serving_findings')
    for finding in research['findings']:
        _fields(finding, ('label', 'text', 'source_ids'), 'invalid_serving_finding')
        if finding['label'] not in _LABELS or not _text(finding['text']):
            raise ValueError('invalid_serving_finding')
        _references(finding['source_ids'], sources)
        if finding['label'] == 'confirmed' and any(sources[s]['verification'] != 'retrieved_official'
                                                   for s in finding['source_ids']):
            raise ValueError('unverified_confirmed_finding')
    return research


def _context(value):
    _fields(value, ('identity', 'serving_provider', 'plan_id', 'route_id', *GATES), 'invalid_serving_context')
    if not all(_text(v) for v in value.values()):
        raise ValueError('invalid_serving_context')


def validate_registry(registry, research=None):
    _fields(registry, ('schema_version', 'research', 'providers', 'plans', 'routes'), 'invalid_serving_registry')
    if type(registry['schema_version']) is not int or registry['schema_version'] != 1:
        raise ValueError('invalid_serving_registry')
    _fields(registry['research'], ('path', 'sha256'), 'invalid_serving_research_locator')
    locator = registry['research']
    if (type(locator['path']) is not str
            or not re.fullmatch(r'bridge/research/[a-z0-9]+(?:[._-][a-z0-9]+)*\.json', locator['path'])
            or type(locator['sha256']) is not str or not re.fullmatch('[0-9a-f]{64}', locator['sha256'])):
        raise ValueError('invalid_serving_research_locator')
    providers = _records(registry['providers'], ('id', 'label'))
    routes = _records(registry['routes'], ('id', 'provider_id', 'alias', 'model_owner', 'matches'))
    plans = _records(registry['plans'], ('id', 'provider_id', 'label', 'currency', 'monthly_price', 'factor', 'route_ids'))
    sources = None
    if research is not None:
        validate_research(research)
        if research['provider_id'] not in providers:
            raise ValueError('serving_research_provider_mismatch')
        sources = {s['id']: s for s in research['sources']}
    for provider in providers.values():
        if not _text(provider['label']):
            raise ValueError('invalid_serving_provider')
    for plan in plans.values():
        ids = plan['route_ids']
        if (plan['provider_id'] not in providers or not _text(plan['label'])
                or plan['currency'] != 'USD' or not _positive(plan['monthly_price'])
                or type(ids) is not list or not ids or any(type(r) is not str for r in ids)
                or len(ids) != len(set(ids)) or not set(ids) <= set(routes)
                or any(routes[r]['provider_id'] != plan['provider_id'] for r in ids)):
            raise ValueError('invalid_serving_plan')
        factor = plan['factor']
        if factor is not None:
            _fields(factor, ('value', 'basis', 'accepted_by_owner', 'terms_accepted_by_owner', 'as_of', 'valid_until', 'context'),
                    'invalid_serving_factor')
            if (not _positive(factor['value']) or factor['basis'] != 'owner_accepted_scenario'
                    or type(factor['accepted_by_owner']) is not bool
                    or type(factor['terms_accepted_by_owner']) is not bool):
                raise ValueError('invalid_serving_factor')
            _day(factor['as_of']); _day(factor['valid_until']); _context(factor['context'])
            if factor['valid_until'] < factor['as_of']:
                raise ValueError('invalid_serving_factor_dates')
    aliases = set()
    for route in routes.values():
        alias_key = (route['provider_id'], route['alias'])
        if (route['provider_id'] not in providers or not _text(route['alias']) or not _text(route['model_owner'])
                or alias_key in aliases or type(route['matches']) is not list):
            raise ValueError('invalid_serving_route')
        aliases.add(alias_key)
        seen = set()
        for match in route['matches']:
            _fields(match, ('model', 'effort', 'identity', 'label', 'reason', 'proof'), 'invalid_serving_match')
            key = (match['model'], match['effort'])
            if (not all(_text(match[k]) for k in ('model', 'effort', 'identity', 'reason'))
                    or match['label'] not in ('confirmed', 'potential') or key in seen):
                raise ValueError('invalid_serving_match')
            seen.add(key)
            _fields(match['proof'], GATES, 'invalid_serving_proof')
            for gate, proof in match['proof'].items():
                if proof is None:
                    continue
                _fields(proof, ('value', 'source_ids', 'checked_date', 'valid_until'), 'invalid_serving_proof')
                if not _text(proof['value']):
                    raise ValueError('invalid_serving_proof')
                _day(proof['checked_date']); _day(proof['valid_until'])
                if proof['valid_until'] < proof['checked_date']:
                    raise ValueError('invalid_serving_proof_dates')
                if gate == 'alias' and proof['value'] != route['alias']:
                    raise ValueError('serving_alias_proof_mismatch')
                if gate == 'effort' and proof['value'] != match['effort']:
                    raise ValueError('serving_effort_proof_mismatch')
                if sources is not None:
                    _references(proof['source_ids'], sources)
                    if any(sources[s]['verification'] != 'retrieved_official' for s in proof['source_ids']):
                        raise ValueError('unverified_applicability_proof')
                    if any(sources[s]['checked_date'] != proof['checked_date'] for s in proof['source_ids']):
                        raise ValueError('serving_proof_date_mismatch')
                    if gate == 'current_terms' and not any(sources[s]['updated_at'] == proof['value']
                                                           for s in proof['source_ids']):
                        raise ValueError('serving_terms_version_mismatch')
                elif type(proof['source_ids']) is not list or not proof['source_ids']:
                    raise ValueError('invalid_serving_proof')
    return registry


def validate_bundle(registry_bytes, research_bytes):
    registry = validate_registry(_json(registry_bytes))
    if hashlib.sha256(research_bytes).hexdigest() != registry['research']['sha256']:
        raise ValueError('serving_research_hash_mismatch')
    research = validate_research(_json(research_bytes))
    validate_registry(registry, research)
    return registry, research


def evaluate_route(row, registry, plan_id, route_id, *, context=None, research=None, as_of=None):
    """Evaluate one route with at most one factor; never mutate the source row.

    Missing research or execution context is deliberately inapplicable.
    """
    validate_registry(registry, research)
    as_of = date.today().isoformat() if as_of is None else as_of
    _day(as_of)
    plan = next((p for p in registry['plans'] if p['id'] == plan_id), None)
    route = next((r for r in registry['routes'] if r['id'] == route_id), None)
    if plan is None or route is None or route_id not in plan['route_ids']:
        raise ValueError('unknown_serving_route')
    if context is not None:
        _context(context)
    matches = [m for m in route['matches'] if (m['model'], m['effort'], m['identity']) ==
               (row['model'], row['effort'], row['identity'])]
    pending = []
    factor = plan['factor']
    if research is None or as_of != research['as_of']:
        pending.append('current_research')
    if factor is None or not factor['accepted_by_owner']:
        pending.append('owner_accepted_factor')
    if factor is None or not factor['terms_accepted_by_owner']:
        pending.append('owner_accepted_terms')
    if factor is None or not factor['as_of'] <= as_of <= factor['valid_until']:
        pending.append('scenario_current')
    binding = dict(serving_provider=route['provider_id'], plan_id=plan_id, route_id=route_id)
    if (context is None or factor is None or
            any(context[k] != v or factor['context'][k] != v for k, v in binding.items())):
        pending.append('provider_plan_route')
    if len(matches) != 1 or context is None or context['identity'] != row['identity']:
        pending.append('exact_identity')
    if len(matches) != 1 or matches[0]['label'] != 'confirmed':
        pending.append('confirmed_route')
    for gate in GATES:
        proof = matches[0]['proof'][gate] if len(matches) == 1 else None
        if (proof is None or not proof['checked_date'] <= as_of <= proof['valid_until']
                or context is None or proof['value'] != context[gate]
                or factor is None or factor['context'][gate] != context[gate]
                or factor['context']['identity'] != row['identity']):
            pending.append(gate)
    contributor = row.get('is_contributor') or extra._contributor(row)
    if contributor:
        pending.append('contributor_fixed_factor')
    multiplier = 1 if pending else factor['value']
    cost = row['cost_orig'] / multiplier
    cp = row['score'] / cost
    if not (_positive(cost) and type(cp) in (int, float) and math.isfinite(cp)):
        raise ValueError('invalid_serving_cost')
    return dict(plan_id=plan_id, route_id=route_id, serving_provider=route['provider_id'],
                model_owner=route['model_owner'], alias=route['alias'], factor=multiplier,
                cost_adj=cost, cp_adj=cp, cost_basis='api-only' if pending else 'owner-accepted-scenario',
                pending_gates=pending)


def calculate_plan_view(envelope, registry, research, *, as_of=None):
    validate_envelope(envelope)
    validate_registry(registry, research)
    if envelope['status'] != 'success' or envelope['schema_version'] not in (2, 3, 4):
        raise ValueError('invalid_serving_parent')
    as_of = date.today().isoformat() if as_of is None else as_of
    _day(as_of)
    opportunities = []
    for row in envelope['candidate_statuses']:
        evaluations = []
        reasons = []
        for route in registry['routes']:
            matched = [m for m in route['matches'] if (m['model'], m['effort'], m['identity']) ==
                       (row['model'], row['effort'], row['identity'])]
            if not matched:
                continue
            reasons.extend(m['reason'] for m in matched)
            for plan in registry['plans']:
                if route['id'] in plan['route_ids']:
                    context = plan['factor']['context'] if plan['factor'] else None
                    evaluations.append(evaluate_route(row, registry, plan['id'], route['id'],
                        context=context,research=research,as_of=as_of))
        if evaluations:
            opportunities.append(dict(identity=row['identity'], model=row['model'], effort=row['effort'],
                label='confirmed' if any(not e['pending_gates'] for e in evaluations) else 'potential',
                api_cost_per_task=row['cost_orig'], api_cp=row['score']/row['cost_orig'],
                plan_ids=sorted({e['plan_id'] for e in evaluations}), reasons=sorted(set(reasons)), routes=evaluations))
    return dict(schema_version=1, kind='serving-plan-research', research_id=research['research_id'],
                as_of=research['as_of'], evaluated_as_of=as_of,
                providers=deepcopy(registry['providers']), plans=deepcopy(registry['plans']),
                advertised_routes=[{k:r[k] for k in ('id','provider_id','alias','model_owner')} for r in registry['routes']],
                potential_candidate_count=sum(c['label'] == 'potential' for c in opportunities),
                confirmed_candidate_count=sum(c['label'] == 'confirmed' for c in opportunities),
                numeric_benefit_applied=any(not e['pending_gates'] for c in opportunities for e in c['routes']),
                candidates=opportunities)
