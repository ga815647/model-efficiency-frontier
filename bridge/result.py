"""Project one validated source snapshot into a correlated scenario result.

The frozen calculator is invoked once by ladder_extra.compute_groups; Markdown
and JSON consume that same groups object. Provenance is supplied by the source
adapter, not derived from a version string in the candidate CSV.
"""

import json
from pathlib import Path
from types import SimpleNamespace
import sys

_SCRIPTS = str(Path(__file__).resolve().parents[1] / 'scripts')
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
import ladder_extra as extra


class ResultError(ValueError):
    """A snapshot, provenance, or result envelope is inconsistent."""


def _provenance(provenance):
    required = ('benchmark', 'benchmark_version', 'version_status', 'cost_basis',
                'source_dates', 'source_locator', 'caveats')
    if not isinstance(provenance, dict) or any(not provenance.get(k) for k in required):
        raise ResultError('missing_provenance')
    locator = provenance['source_locator']
    if (not isinstance(locator, dict) or not locator.get('commit') or
            not locator.get('path') or not isinstance(provenance['source_dates'], list) or
            not isinstance(provenance['caveats'], list)):
        raise ResultError('invalid_provenance')


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
    }


def calculate_snapshot(csv_path: Path, parameters: dict, provenance: dict) -> tuple[dict, str]:
    """Calculate paid candidates once and render two views of the same result."""
    _provenance(provenance)
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
    }
    json.dumps(payload, allow_nan=False)
    report = extra.render(groups, paid, args, title='# 模型效率前線｜Chat 情境結報（非官方 AA 成本）')
    return payload, report


def validate_envelope(envelope: dict) -> dict:
    """Reject stale successes and incomplete correlation before publication/reading."""
    common = ('schema_version', 'operation', 'status', 'request_id', 'request_commit_sha',
              'product_sha', 'created_at', 'run_id', 'run_attempt', 'run_url',
              'source_snapshot', 'parameters', 'source_dates', 'errors')
    if not isinstance(envelope, dict) or any(k not in envelope for k in common):
        raise ResultError('incomplete_envelope')
    if envelope['status'] == 'success':
        if envelope['errors'] or any(k not in envelope for k in
                                     ('ladder', 'picks', 'candidate_statuses', 'benchmark',
                                      'benchmark_version', 'version_status', 'cost_basis', 'caveats', 'eps')):
            raise ResultError('invalid_success')
    elif envelope['status'] == 'failed':
        if not isinstance(envelope['errors'], list) or not envelope['errors'] or any(
                k in envelope for k in ('ladder', 'picks', 'candidate_statuses')):
            raise ResultError('invalid_failure')
    else:
        raise ResultError('invalid_status')
    json.dumps(envelope, allow_nan=False)
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
        'source_snapshot': (calculation or {}).get('source_snapshot', request.get('source_snapshot')),
        'parameters': dict(request['parameters']),
        'source_dates': (calculation or {}).get('source_dates', []), 'errors': errors,
    }
    if status == 'success':
        if calculation['parameters'] != request['parameters']:
            raise ResultError('parameters_mismatch')
        envelope.update({k: v for k, v in calculation.items()
                         if k not in ('parameters', 'source_snapshot', 'source_dates')})
    return validate_envelope(envelope)
