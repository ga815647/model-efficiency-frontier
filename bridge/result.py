"""Project one validated source snapshot into a correlated scenario result.

The frozen calculator is invoked once by ladder_extra.compute_groups; Markdown
and JSON consume that same groups object. Provenance is supplied by the source
adapter, not derived from a version string in the candidate CSV.
"""

import json
import hashlib
from datetime import date, datetime
import math
from pathlib import Path
from types import SimpleNamespace
import sys
import re

_SCRIPTS = str(Path(__file__).resolve().parents[1] / 'scripts')
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
import ladder_extra as extra


class ResultError(ValueError):
    """A snapshot, provenance, or result envelope is inconsistent."""


_SHA = re.compile(r'[0-9a-fA-F]{40}\Z')
_DIGEST = re.compile(r'[0-9a-fA-F]{64}\Z')
_UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z')
_RUN_PATH = re.compile(r'runs/[A-Za-z0-9][A-Za-z0-9._-]*/candidates\.csv\Z')
_RESULT_PATH = re.compile(r'results/[0-9a-f-]+/[A-Za-z0-9][A-Za-z0-9._-]*/snapshot/candidates\.csv\Z')


def _nonempty(value):
    return type(value) is str and bool(value.strip())


def _date(value):
    try:
        return type(value) is str and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _locator(locator):
    if type(locator) is not dict:
        raise ResultError('invalid_source_locator')
    if set(locator) == {'commit', 'path'}:
        path = locator['path']
        parts = path.split('/') if type(path) is str else []
        published = (_RESULT_PATH.fullmatch(path) is not None and
                     _UUID.fullmatch(parts[1]) is not None and
                     re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*-[1-9][0-9]*', parts[2]) is not None)
        archived = type(path) is str and _RUN_PATH.fullmatch(path) is not None
        if (not _nonempty(locator['commit']) or not _SHA.fullmatch(locator['commit']) or
                not (archived or published)):
            raise ResultError('invalid_source_locator')
    elif set(locator) == {'kind', 'path', 'sha256'}:
        if (locator['kind'] != 'acquired' or locator['path'] != 'snapshot/candidates.csv' or
                type(locator['sha256']) is not str or not _DIGEST.fullmatch(locator['sha256'])):
            raise ResultError('invalid_source_locator')
    else:
        raise ResultError('invalid_source_locator')


def _provenance(provenance):
    required = ('benchmark', 'benchmark_version', 'version_status', 'cost_basis',
                'source_dates', 'source_locator', 'caveats')
    if type(provenance) is not dict or any(k not in provenance for k in required):
        raise ResultError('missing_provenance')
    if (any(not _nonempty(provenance[k]) for k in ('benchmark', 'benchmark_version', 'cost_basis'))
            or provenance['version_status'] not in ('explicit', 'inferred')
            or type(provenance['source_dates']) is not list or not provenance['source_dates']
            or not all(_date(d) for d in provenance['source_dates'])
            or type(provenance['caveats']) is not list
            or not all(_nonempty(c) for c in provenance['caveats'])
            or provenance['version_status'] == 'inferred' and not provenance['caveats']):
        raise ResultError('invalid_provenance')
    _locator(provenance['source_locator'])


def _project(row, status, reason=None, winner=None):
    return {
        'identity': row['identity'], 'model': row.get('model') or '',
        'effort': row.get('effort') or '', 'score': row['_score'],
        'cost_orig': row['_cost_orig'], 'cost_adj': row['_cost'],
        'cp_orig': row['_cp_orig'], 'cp_adj': extra._cp_adj(row),
        'factor': row['_factor'], 'grade': extra.grade_of(row),
        'status': status, 'reason': extra._reason(reason) if reason else None,
        'winner': winner, 'source_url': row.get('evidence_url') or '',
        'source_date': row.get('checked_date') or '', 'notes': row.get('notes') or '',
        'is_grok': extra._grok(row), 'is_contributor': extra._contributor(row),
    }


def calculate_snapshot(csv_path: Path, parameters: dict, provenance: dict) -> tuple[dict, str]:
    """Calculate paid candidates once and render two views of the same result."""
    _provenance(provenance)
    locator = provenance['source_locator']
    if locator.get('kind') == 'acquired' and hashlib.sha256(
            Path(csv_path).read_bytes()).hexdigest().lower() != locator['sha256'].lower():
        raise ResultError('source_hash_mismatch')
    if not isinstance(parameters, dict):
        raise ResultError('invalid_parameters')
    try:
        args = SimpleNamespace(input=str(csv_path), factor=parameters['gpt_factor'],
                               prefix='GPT-', grok_factor=parameters['grok_factor'],
                               min_score=parameters['min_score'], max_cost=parameters['max_cost'],
                               min_score_reason=parameters['min_score_reason'],
                               eps_score=2.0, eps_cp=0.05, monthly_tasks=None,
                               subscription_total=79)
    except KeyError as exc:
        raise ResultError('invalid_parameters') from exc
    raw = extra.load_rows(csv_path)
    paid = extra.adjust_rows(raw, args.factor, args.prefix, args.grok_factor)
    if not paid:
        raise ResultError('empty_paid')
    keys = {(r['benchmark'], r['benchmark_version'], r['cost_basis']) for r in paid}
    expected = (provenance['benchmark'], provenance['benchmark_version'], provenance['cost_basis'])
    if keys != {expected}:
        raise ResultError('mixed_or_mismatched_source')
    if any(extra.grade_of(r) not in ('A', 'B') for r in paid):
        raise ResultError('unknown_cost_grade')
    if any(extra.grade_of(r) == 'B' for r in paid) and not provenance['caveats']:
        raise ResultError('missing_grade_b_caveat')
    if (not all(r.get('checked_date') in provenance['source_dates'] and r.get('evidence_url')
                for r in paid)):
        raise ResultError('source_provenance_mismatch')
    if len({r['identity'] for r in paid}) != len(paid):
        raise ResultError('duplicate_identity')
    groups = extra.compute_groups(paid, args)
    result = groups[expected]
    final, cuts, excluded = result['final'], result['cuts'], result['excluded']
    picks = extra.select_picks(final)
    excluded_reasons = {r['identity']: why for r, why in excluded}
    statuses = []
    final_ids = {r['identity'] for r in final}
    for r in paid:
        identity = r['identity']
        if identity in final_ids:
            statuses.append(_project(r, 'final'))
        elif identity in cuts:
            statuses.append(_project(r, 'cut', 'same-score band', cuts[identity]))
        else:
            statuses.append(_project(r, 'excluded', excluded_reasons.get(identity, 'not final')))
    projected = {r['identity']: r for r in statuses}
    payload = {
        'parameters': dict(parameters), 'eps': {'score': args.eps_score, 'cp': args.eps_cp},
        'source_snapshot': dict(provenance['source_locator']),
        'source_dates': list(provenance['source_dates']),
        'benchmark': expected[0], 'benchmark_version': expected[1],
        'version_status': provenance['version_status'], 'cost_basis': expected[2],
        'caveats': list(provenance['caveats']),
        'ladder': [projected[r['identity']] for r in final],
        'picks': {name: projected[row['identity']] if row is not None else None
                  for name, row in picks.items()},
        'candidate_statuses': statuses,
        'candidate_count': len(paid),
    }
    json.dumps(payload, allow_nan=False)
    report = extra.render(groups, paid, args, title='# 模型效率前線｜Chat 情境結報（非官方 AA 成本）')
    return payload, report


_FIELDS = ('identity', 'model', 'effort', 'score', 'cost_orig', 'cost_adj',
           'cp_orig', 'cp_adj', 'factor', 'grade', 'status', 'reason', 'winner',
           'source_url', 'source_date', 'notes', 'is_grok', 'is_contributor')


def _number(value, *, positive=False):
    try:
        return (type(value) in (int, float) and math.isfinite(value)
                and (value > 0 if positive else value >= 0))
    except OverflowError:
        return False


def _row_shape(row):
    if (type(row) is not dict or any(k not in row for k in _FIELDS)
            or not _nonempty(row['identity']) or row['status'] not in ('final', 'cut', 'excluded')
            or row['grade'] not in ('A', 'B')
            or any(type(row[k]) is not str for k in ('model', 'effort', 'source_url', 'notes'))
            or not _nonempty(row['source_url']) or not _date(row['source_date'])
            or any(type(row[k]) is not bool for k in ('is_grok', 'is_contributor'))
            or not _number(row['score'])
            or any(not _number(row[k], positive=True) for k in
                   ('cost_orig', 'cost_adj', 'factor'))
            or any(not _number(row[k]) for k in ('cp_orig', 'cp_adj'))):
        raise ResultError('invalid_candidate_row')
    if row['status'] == 'final' and (row['winner'] is not None or row['reason'] is not None):
        raise ResultError('invalid_final_row')
    if row['status'] == 'cut' and not _nonempty(row['winner']):
        raise ResultError('invalid_cut_row')
    if row['status'] == 'excluded' and row['winner'] is not None:
        raise ResultError('invalid_excluded_row')
    if row['status'] != 'final' and not _nonempty(row['reason']):
        raise ResultError('missing_row_reason')


def validate_envelope(envelope: dict) -> dict:
    """Validate public shape/correlation, not provenance authenticity or frontier math.

    Upstream must validate a request and, for pinned Git locators, fetch and
    verify bytes at that commit. Acquired locators are hash-checked while
    calculating. Failed requests may carry unvalidated parameters or null
    request identity but must not claim any success-derived fields.
    """
    common = ('schema_version', 'operation', 'status', 'request_id', 'request_commit_sha',
              'product_sha', 'created_at', 'run_id', 'run_attempt', 'run_url',
              'source_snapshot', 'parameters', 'source_dates', 'errors')
    if type(envelope) is not dict or any(k not in envelope for k in common):
        raise ResultError('incomplete_envelope')
    if (type(envelope['schema_version']) is not int or envelope['schema_version'] != 1
            or type(envelope['request_commit_sha']) is not str
            or not _SHA.fullmatch(envelope['request_commit_sha'])
            or not _nonempty(envelope['run_id'])
            or type(envelope['run_attempt']) is not int or envelope['run_attempt'] < 1
            or not _nonempty(envelope['run_url'])
            or type(envelope['errors']) is not list
            or any(type(e) is not dict or not _nonempty(e.get('code'))
                   or not _nonempty(e.get('message')) for e in envelope['errors'])):
        raise ResultError('invalid_correlation_or_errors')
    if envelope['status'] == 'success':
        if (envelope['operation'] not in ('refresh', 'recompute') or
                type(envelope['request_id']) is not str or not _UUID.fullmatch(envelope['request_id'])
                or type(envelope['product_sha']) is not str or not _SHA.fullmatch(envelope['product_sha'])
                or not _nonempty(envelope['created_at'])):
            raise ResultError('invalid_success_identity')
        try:
            timestamp = datetime.fromisoformat(envelope['created_at'])
            if timestamp.utcoffset() is None:
                raise ValueError('missing timezone')
        except (TypeError, ValueError) as exc:
            raise ResultError('invalid_created_at') from exc
        if envelope['errors'] or any(k not in envelope for k in
                                     ('ladder', 'picks', 'candidate_statuses', 'benchmark',
                                       'benchmark_version', 'version_status', 'cost_basis', 'caveats', 'eps',
                                       'candidate_count')):
            raise ResultError('invalid_success')
        _provenance(dict(benchmark=envelope['benchmark'], benchmark_version=envelope['benchmark_version'],
                         version_status=envelope['version_status'], cost_basis=envelope['cost_basis'],
                         source_dates=envelope['source_dates'], source_locator=envelope['source_snapshot'],
                         caveats=envelope['caveats']))
        params = envelope['parameters']
        if (type(params) is not dict or set(params) !=
                {'gpt_factor', 'grok_factor', 'min_score', 'min_score_reason', 'max_cost'}
                or not _number(params['gpt_factor'], positive=True)
                or not _number(params['grok_factor'], positive=True)
                or not _number(params['min_score'])
                or not _nonempty(params['min_score_reason'])
                or params['max_cost'] is not None and not _number(params['max_cost'], positive=True)
                or type(envelope['eps']) is not dict or set(envelope['eps']) != {'score', 'cp'}
                or not _number(envelope['eps']['score'], positive=True)
                or not _number(envelope['eps']['cp'])):
            raise ResultError('invalid_success_parameters')
        ladder, statuses, picks = (envelope[k] for k in ('ladder', 'candidate_statuses', 'picks'))
        if (type(envelope['candidate_count']) is not int or envelope['candidate_count'] < 1
                or type(ladder) is not list or type(statuses) is not list or
                len(statuses) != envelope['candidate_count']
                or type(picks) is not dict or set(picks) != {'strong', 'middle', 'cheap'}):
            raise ResultError('invalid_success_rows')
        for row in statuses:
            _row_shape(row)
            if row['source_date'] not in envelope['source_dates']:
                raise ResultError('source_date_mismatch')
        if any(r['grade'] == 'B' for r in statuses) and not envelope['caveats']:
            raise ResultError('missing_grade_b_caveat')
        identities = {row['identity'] for row in statuses}
        if len(identities) != len(statuses):
            raise ResultError('duplicate_identity')
        by_identity = {row['identity']: row for row in statuses}
        finals = [r for r in statuses if r['status'] == 'final']
        if (len(ladder) != len(finals)
                or any(type(r) is not dict or r.get('identity') not in by_identity
                       or r != by_identity[r['identity']] or r['status'] != 'final' for r in ladder)
                or {r['identity'] for r in ladder} != {r['identity'] for r in finals}
                or any(ladder[i]['score'] < ladder[i+1]['score'] for i in range(len(ladder)-1))):
            raise ResultError('invalid_ladder')
        # Reuse the renderer's pick selector over projected numbers; never
        # re-run the frozen calculator or recompute the candidate frontier.
        projected_picks = extra.select_picks([
            dict(row, _score=row['score'], _cost=row['cost_adj'], _cp=row['cp_adj'])
            for row in ladder])
        if any(picks[key] != (by_identity[expected['identity']] if expected else None)
               for key, expected in projected_picks.items()):
            raise ResultError('invalid_picks')
        if any(r['status'] == 'cut' and r['winner'] not in by_identity for r in statuses):
            raise ResultError('invalid_cut_winner')
    elif envelope['status'] == 'failed':
        if not isinstance(envelope['errors'], list) or not envelope['errors'] or any(
                k in envelope for k in ('ladder', 'picks', 'candidate_statuses',
                                       'benchmark', 'benchmark_version', 'version_status',
                                        'cost_basis', 'caveats', 'eps', 'candidate_count')):
            raise ResultError('invalid_failure')
        if (envelope['request_id'] is not None and not _nonempty(envelope['request_id'])
                or envelope['parameters'] is not None and type(envelope['parameters']) is not dict
                or envelope['source_dates'] != []):
            raise ResultError('invalid_failure_metadata')
    else:
        raise ResultError('invalid_status')
    try:
        json.dumps(envelope, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ResultError('invalid_json_result') from exc
    return envelope


def make_envelope(request: dict, execution: dict, *, calculation: dict | None,
                  errors: list[dict]) -> dict:
    """Flatten successful calculation into the public result; never carry stale picks."""
    status = 'failed' if errors else 'success'
    if status == 'success' and calculation is None:
        raise ResultError('missing_calculation')
    envelope = {
        'schema_version': 1, 'operation': request['operation'], 'status': status,
        'request_id': request['request_id'], 'request_commit_sha': execution['request_commit_sha'],
        'product_sha': request['product_sha'], 'created_at': request['created_at'],
        'run_id': execution['run_id'], 'run_attempt': execution['run_attempt'],
        'run_url': execution['run_url'],
        'source_snapshot': calculation['source_snapshot'] if status == 'success' else
                           request.get('source_snapshot'),
        'parameters': request.get('parameters'),
        'source_dates': calculation['source_dates'] if status == 'success' else [], 'errors': errors,
    }
    if status == 'success':
        if calculation['parameters'] != request['parameters']:
            raise ResultError('parameters_mismatch')
        envelope.update({k: v for k, v in calculation.items()
                         if k not in ('parameters', 'source_snapshot', 'source_dates')})
    return validate_envelope(envelope)
