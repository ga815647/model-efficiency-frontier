"""Source-checked window results and strict relational validation for schema v2.

Validation checks the published evidence graph, not source authenticity or a
second implementation of CP selection / window-strength calculation.
"""
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

from scripts.meta_availability import unavailable_reason

from . import result_v1 as v1
from .window_ladder import calculate_ladder, select_anchors
from .subscription_cost import LEGACY_PARAMETERS, SUBSCRIPTION_PARAMETERS, adjust_rows, factor_for

ResultError = v1.ResultError
extra = v1.extra
POLICY = 'cp-new-high-window-v1'
_COMMON = {'schema_version', 'operation', 'status', 'request_id', 'request_commit_sha',
           'product_sha', 'created_at', 'run_id', 'run_attempt', 'run_url',
           'source_snapshot', 'parameters', 'source_dates', 'errors'}
_SUCCESS = {'selection_policy', 'selection_parameters', 'eps', 'ladder', 'anchors',
            'candidate_statuses', 'chain_identities', 'selection_trace', 'grade_b_effects',
            'benchmark', 'benchmark_version', 'version_status', 'cost_basis', 'caveats',
            'candidate_count'}
_ROW_FIELDS = set(v1._FIELDS) | {'comparison_only', 'upgrade'}


def _parameters(params, schema_version=2):
    keys = LEGACY_PARAMETERS if schema_version == 2 else SUBSCRIPTION_PARAMETERS
    if (type(params) is not dict or set(params) !=
            keys
            or any(not v1._number(params[k], positive=True)
                   for k in keys - {'min_score', 'min_score_reason', 'max_cost'})
            or not v1._number(params['min_score'])
            or not v1._nonempty(params['min_score_reason'])
            or params['max_cost'] is not None and not v1._number(params['max_cost'], positive=True)):
        raise ResultError('invalid_parameters')


def calculate_v2(csv_path: Path, parameters: dict, provenance: dict) -> dict:
    return _calculate(csv_path, parameters, provenance, schema_version=2)


def _calculate(csv_path, parameters, provenance, *, schema_version):
    """Validate source bytes and provenance before invoking the window calculator."""
    v1._provenance(provenance)
    if provenance['benchmark'] != 'AA-Intelligence-Index':
        raise ResultError('unsupported_benchmark')
    locator = provenance['source_locator']
    if locator.get('kind') == 'acquired' and hashlib.sha256(
            Path(csv_path).read_bytes()).hexdigest().lower() != locator['sha256'].lower():
        raise ResultError('source_hash_mismatch')
    _parameters(parameters, schema_version)
    paid = adjust_rows(extra.load_rows(csv_path), parameters)
    if not paid:
        raise ResultError('empty_paid')
    expected = (provenance['benchmark'], provenance['benchmark_version'], provenance['cost_basis'])
    if {(r['benchmark'], r['benchmark_version'], r['cost_basis']) for r in paid} != {expected}:
        raise ResultError('mixed_or_mismatched_source')
    if any(extra.grade_of(r) not in ('A', 'B') for r in paid):
        raise ResultError('unknown_cost_grade')
    if any(extra.grade_of(r) == 'B' for r in paid) and not provenance['caveats']:
        raise ResultError('missing_grade_b_caveat')
    if not all(r.get('checked_date') in provenance['source_dates'] and r.get('evidence_url') for r in paid):
        raise ResultError('source_provenance_mismatch')
    if len({r['identity'] for r in paid}) != len(paid):
        raise ResultError('duplicate_identity')
    payload = dict(calculate_ladder(paid, min_score=parameters['min_score'],
                                    max_cost=parameters['max_cost']),
                   selection_policy=POLICY,
                   selection_parameters={'window_score': 2.0, 'replacement_score': 2.0},
                   parameters=dict(parameters), eps={'score': 2.0, 'cp': 0.05},
                   source_snapshot=dict(locator), source_dates=list(provenance['source_dates']),
                   benchmark=expected[0], benchmark_version=expected[1], cost_basis=expected[2],
                   version_status=provenance['version_status'], caveats=list(provenance['caveats']))
    json.dumps(payload, allow_nan=False)
    return payload


def _close(actual, expected):
    return (type(actual) in (int, float) and math.isfinite(actual)
            and math.isfinite(expected)
            and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12))


def _constants(value, expected):
    return (type(value) is dict and set(value) == set(expected)
            and all(v1._number(value[k], positive=True) and value[k] == v for k, v in expected.items()))


def _row_shape(row):
    v1._row_shape(row)
    if set(row) != _ROW_FIELDS or type(row['comparison_only']) is not bool:
        raise ResultError('invalid_candidate_row')
    upgrade = row['upgrade']
    if upgrade is not None and (
            type(upgrade) is not dict
            or set(upgrade) != {'cheaper_identity', 'delta_score', 'cost_multiple', 'delta_cost_adj'}
            or not v1._nonempty(upgrade['cheaper_identity'])
            or any(not v1._number(upgrade[k], positive=True)
                   for k in ('delta_score', 'cost_multiple', 'delta_cost_adj'))):
        raise ResultError('invalid_upgrade')


def _rows(envelope):
    statuses, ladder = envelope['candidate_statuses'], envelope['ladder']
    if (type(envelope['candidate_count']) is not int or envelope['candidate_count'] < 1
            or type(statuses) is not list or len(statuses) != envelope['candidate_count']
            or type(ladder) is not list):
        raise ResultError('invalid_success_rows')
    params = envelope['parameters']
    for row in statuses:
        _row_shape(row)
        if unavailable_reason(row) and row['status'] != 'excluded':
            raise ResultError('unavailable_identity_not_excluded')
        if row['source_date'] not in envelope['source_dates']:
            raise ResultError('source_date_mismatch')
        if (row['is_grok'] != extra._grok(row) or row['is_contributor'] != extra._contributor(row)
                or row['comparison_only'] != extra._is_claude(row['identity'])):
            raise ResultError('invalid_family_flags')
        factor = factor_for(row, params)
        if (row['factor'] != factor
                or not _close(row['cost_adj'], row['cost_orig'] / factor)
                or not _close(row['cp_orig'], row['score'] / row['cost_orig'])
                or not _close(row['cp_adj'], row['score'] / row['cost_adj'])
                or not _close(row['cp_adj'], row['cp_orig'] * factor)):
            raise ResultError('invalid_row_arithmetic')
        if row['status'] == 'cut' and row['reason'] != 'within_replacement_radius':
            raise ResultError('invalid_cut_reason')
        if (row['status'] != 'final' or row['comparison_only']) and row['upgrade'] is not None:
            raise ResultError('invalid_upgrade')
    if any(r['grade'] == 'B' for r in statuses) and not envelope['caveats']:
        raise ResultError('missing_grade_b_caveat')
    by_id = {r['identity']: r for r in statuses}
    if len(by_id) != len(statuses):
        raise ResultError('duplicate_identity')
    finals = {r['identity'] for r in statuses if r['status'] == 'final'}
    for row in ladder:
        _row_shape(row)
    if (len(ladder) != len(finals)
            or any(type(r) is not dict or type(r.get('identity')) is not str
                   or r['identity'] not in finals or r != by_id[r['identity']] for r in ladder)
            or {r['identity'] for r in ladder} != finals
            or any(a['score'] - b['score'] < 2.0 for a, b in zip(ladder, ladder[1:]))):
        raise ResultError('invalid_ladder')
    return by_id, finals


def _chain_and_trace(envelope, by_id, finals):
    chain, trace = envelope['chain_identities'], envelope['selection_trace']
    if (type(chain) is not list or any(type(i) is not str for i in chain)
            or len(set(chain)) != len(chain)
            or set(chain) != {i for i, r in by_id.items() if r['status'] != 'excluded'}):
        raise ResultError('invalid_chain')
    if any(by_id[a]['score'] <= by_id[b]['score'] or by_id[a]['cp_adj'] >= by_id[b]['cp_adj']
           for a, b in zip(chain, chain[1:])):
        raise ResultError('invalid_chain_order')
    if type(trace) is not list:
        raise ResultError('invalid_selection_trace')
    live = list(chain)
    for number, step in enumerate(trace, 1):
        if (type(step) is not dict or set(step) != {'step', 'winner', 'strength', 'support', 'removed'}
                or type(step['step']) is not int or step['step'] != number
                or type(step['winner']) is not str or step['winner'] not in finals
                or step['winner'] not in live
                or type(step['strength']) not in (int, float) or not math.isfinite(step['strength'])
                or step['support'] not in ('full_window', 'neutral_missing_window')
                or step['support'] == 'neutral_missing_window' and step['strength'] != 0
                or type(step['removed']) is not list or not step['removed']
                or any(type(i) is not str for i in step['removed'])
                or len(set(step['removed'])) != len(step['removed'])):
            raise ResultError('invalid_selection_trace')
        winner = by_id[step['winner']]
        removed = step['removed']
        # Check exactly the live direct neighbors, in chain order, without
        # recomputing the strength or choosing a different representative.
        neighbors = [i for i in live if i != step['winner']
                     and abs(by_id[i]['score'] - winner['score']) < 2.0]
        if (removed != neighbors or any(by_id[i]['status'] != 'cut'
                                       or by_id[i]['winner'] != step['winner'] for i in removed)):
            raise ResultError('invalid_trace_removal')
        full_window = (winner['score'] + 2.0 <= by_id[live[0]]['score']
                       and winner['score'] - 2.0 >= by_id[live[-1]]['score'])
        if (step['support'] == 'full_window') != full_window:
            raise ResultError('invalid_trace_support')
        live = [i for i in live if i not in removed]
    if live != [r['identity'] for r in envelope['ladder']]:
        raise ResultError('incomplete_selection_trace')


def _anchors_and_upgrades(envelope):
    ladder = envelope['ladder']
    anchors = envelope['anchors']
    if type(anchors) is not dict or set(anchors) != {'highest_retained_score', 'lowest_retained_cost'}:
        raise ResultError('invalid_anchors')
    for row in anchors.values():
        if row is not None:
            _row_shape(row)
    if envelope['anchors'] != select_anchors(ladder):
        raise ResultError('invalid_anchors')
    eligible = [r for r in ladder if not r['comparison_only']]
    for index, row in enumerate(eligible):
        upgrade = row['upgrade']
        if index == len(eligible) - 1:
            if upgrade is not None:
                raise ResultError('invalid_upgrade')
            continue
        lower = eligible[index + 1]
        expected = dict(delta_score=row['score'] - lower['score'],
                        cost_multiple=row['cost_adj'] / lower['cost_adj'],
                        delta_cost_adj=row['cost_adj'] - lower['cost_adj'])
        if (type(upgrade) is not dict or set(upgrade) != set(expected) | {'cheaper_identity'}
                or upgrade['cheaper_identity'] != lower['identity']
                or any(not v1._number(upgrade[k], positive=True) or not _close(upgrade[k], v)
                       for k, v in expected.items())):
            raise ResultError('invalid_upgrade')


def _b_effects(envelope, by_id, finals):
    effects = envelope['grade_b_effects']
    if type(effects) is not list:
        raise ResultError('invalid_grade_b_effects')
    identities = []
    for effect in effects:
        if (type(effect) is not dict or set(effect) != {'identity', 'with_b_retained', 'without_b_retained'}
                or type(effect['identity']) is not str or effect['identity'] not in by_id
                or by_id[effect['identity']]['grade'] != 'A'
                or type(effect['with_b_retained']) is not bool
                or type(effect['without_b_retained']) is not bool
                or effect['with_b_retained'] != (effect['identity'] in finals)
                or effect['with_b_retained'] == effect['without_b_retained']):
            raise ResultError('invalid_grade_b_effects')
        identities.append(effect['identity'])
    if identities != sorted(set(identities)):
        raise ResultError('invalid_grade_b_effects')


def validate_v2_envelope(envelope: dict) -> dict:
    """Validate v2 shape, provenance, numeric projections and selection relations."""
    try:
        return _validate(envelope)
    except (OverflowError, ZeroDivisionError) as exc:
        raise ResultError('invalid_numeric_result') from exc


def _validate(envelope, schema_version=2):
    if type(envelope) is not dict or not _COMMON <= set(envelope):
        raise ResultError('incomplete_envelope')
    if type(envelope['schema_version']) is not int or envelope['schema_version'] != schema_version:
        raise ResultError('invalid_result_schema')
    if (type(envelope['request_commit_sha']) is not str or not v1._SHA.fullmatch(envelope['request_commit_sha'])
            or not v1._nonempty(envelope['run_id'])
            or type(envelope['run_attempt']) is not int or envelope['run_attempt'] < 1
            or not v1._nonempty(envelope['run_url']) or type(envelope['errors']) is not list
            or any(type(e) is not dict or not v1._nonempty(e.get('code'))
                   or not v1._nonempty(e.get('message')) for e in envelope['errors'])):
        raise ResultError('invalid_correlation_or_errors')
    if envelope['status'] == 'success':
        if set(envelope) != _COMMON | _SUCCESS or envelope['errors']:
            raise ResultError('invalid_success')
        if (envelope['operation'] not in ('refresh', 'recompute')
                or type(envelope['request_id']) is not str or not v1._UUID.fullmatch(envelope['request_id'])
                or type(envelope['product_sha']) is not str or not v1._SHA.fullmatch(envelope['product_sha'])
                or not v1._nonempty(envelope['created_at'])):
            raise ResultError('invalid_success_identity')
        try:
            if datetime.fromisoformat(envelope['created_at']).utcoffset() is None:
                raise ValueError('missing timezone')
        except (TypeError, ValueError) as exc:
            raise ResultError('invalid_created_at') from exc
        v1._provenance(dict(benchmark=envelope['benchmark'], benchmark_version=envelope['benchmark_version'],
                            version_status=envelope['version_status'], cost_basis=envelope['cost_basis'],
                            source_dates=envelope['source_dates'], source_locator=envelope['source_snapshot'],
                            caveats=envelope['caveats']))
        if envelope['benchmark'] != 'AA-Intelligence-Index':
            raise ResultError('unsupported_benchmark')
        if (set(envelope['source_snapshot']) == {'commit', 'path'}) != (envelope['operation'] == 'recompute'):
            raise ResultError('operation_source_mismatch')
        _parameters(envelope['parameters'], schema_version)
        if (envelope['selection_policy'] != POLICY
                or not _constants(envelope['eps'], {'score': 2.0, 'cp': 0.05})
                or not _constants(envelope['selection_parameters'], {'window_score': 2.0, 'replacement_score': 2.0})):
            raise ResultError('invalid_selection_policy')
        by_id, finals = _rows(envelope)
        _chain_and_trace(envelope, by_id, finals)
        _anchors_and_upgrades(envelope)
        _b_effects(envelope, by_id, finals)
    elif envelope['status'] == 'failed':
        if set(envelope) != _COMMON or not envelope['errors']:
            raise ResultError('invalid_failure')
        if (envelope['request_id'] is not None and not v1._nonempty(envelope['request_id'])
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


def make_v2_envelope(request: dict, execution: dict, *, calculation: dict | None,
                     errors: list[dict]) -> dict:
    return _make_envelope(request, execution, calculation=calculation, errors=errors, schema_version=2)


def _make_envelope(request, execution, *, calculation, errors, schema_version):
    """Assemble correlated v2 output; failures discard every calculation field."""
    status = 'failed' if errors else 'success'
    if status == 'success' and calculation is None:
        raise ResultError('missing_calculation')
    envelope = {
        'schema_version': schema_version, 'operation': request['operation'], 'status': status,
        'request_id': request['request_id'], 'request_commit_sha': execution['request_commit_sha'],
        'product_sha': request['product_sha'], 'created_at': request['created_at'],
        'run_id': execution['run_id'], 'run_attempt': execution['run_attempt'], 'run_url': execution['run_url'],
        'source_snapshot': calculation['source_snapshot'] if status == 'success' else request.get('source_snapshot'),
        'parameters': request.get('parameters'),
        'source_dates': calculation['source_dates'] if status == 'success' else [], 'errors': errors,
    }
    if status == 'success':
        if calculation['parameters'] != request['parameters']:
            raise ResultError('parameters_mismatch')
        if set(calculation) != _SUCCESS | {'parameters', 'source_snapshot', 'source_dates'}:
            raise ResultError('invalid_calculation_fields')
        envelope.update({k: calculation[k] for k in _SUCCESS})
    try:
        return _validate(envelope, schema_version)
    except (OverflowError, ZeroDivisionError) as exc:
        raise ResultError('invalid_numeric_result') from exc
