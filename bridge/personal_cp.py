"""A separately identified personal CP view of an already verified result.

The benchmark expresses personal acceptance, not AA measurement uncertainty.
Neither the saved result nor its LADDER/anchors are changed.
"""
from copy import deepcopy
import math
import re

from scripts.meta_availability import unavailable_reason
from .provider_view import PROVIDERS, provider_for
from .result import validate_envelope

POLICY = 'benchmark-minus-eps-cp-v1'
_RESULT_PATH = re.compile(r'results/[0-9a-f-]{36}/[A-Za-z0-9._-]+-[1-9][0-9]*/result\.json\Z')
_FIELDS = {'benchmark_identity', 'tolerance_multiplier', 'result_sha256'}


def validate_choice(choice):
    if (type(choice) is not dict or set(choice) != _FIELDS
            or type(choice['benchmark_identity']) is not str or not choice['benchmark_identity'].strip()
            or type(choice['result_sha256']) is not str
            or not re.fullmatch('[0-9a-f]{64}', choice['result_sha256'])):
        raise ValueError('invalid_personal_cp_choice')
    multiplier = choice['tolerance_multiplier']
    if type(multiplier) not in (int, float) or not math.isfinite(multiplier) or multiplier < 0:
        raise ValueError('invalid_personal_cp_tolerance')
    return choice


def validate_choices(policy):
    if (type(policy) is not dict or set(policy) != {'schema_version', 'choices'}
            or type(policy['schema_version']) is not int or policy['schema_version'] != 1
            or type(policy['choices']) is not dict):
        raise ValueError('invalid_personal_cp_policy')
    for path, choice in policy['choices'].items():
        if not _RESULT_PATH.fullmatch(path):
            raise ValueError('invalid_personal_cp_result_path')
        validate_choice(choice)
    return policy['choices']


def select_candidate(rows, minimum_score, scenario_floor, max_cost):
    qualified = [row for row in rows if not row['comparison_only'] and not unavailable_reason(row)
                 and row['score'] >= minimum_score and row['score'] >= scenario_floor
                 and (max_cost is None or row['cost_adj'] <= max_cost)]
    return min(qualified, key=lambda row: (-row['cp_adj'], -row['score'], row['cost_adj'], row['identity'])) if qualified else None


def calculate_personal_cp(envelope, choice):
    validate_envelope(envelope)
    validate_choice(choice)
    if envelope['status'] != 'success' or envelope['schema_version'] not in (2, 3, 4):
        raise ValueError('invalid_personal_cp_parent')
    rows = envelope['candidate_statuses']
    matches = [row for row in rows if row['identity'] == choice['benchmark_identity']]
    if len(matches) != 1 or unavailable_reason(matches[0]):
        raise ValueError('personal_cp_benchmark_unavailable')
    benchmark = matches[0]
    score_eps = envelope['eps']['score']
    tolerance = choice['tolerance_multiplier'] * score_eps
    threshold = benchmark['score'] - tolerance
    if not math.isfinite(tolerance) or not math.isfinite(threshold):
        raise ValueError('invalid_personal_cp_tolerance')
    params = envelope['parameters']
    scopes = {}
    for scope in ('all', *PROVIDERS):
        pool = [row for row in rows if scope == 'all' or provider_for(row) == scope]
        qualified = [row for row in pool if select_candidate([row], threshold, params['min_score'], params['max_cost'])]
        selected = select_candidate(qualified, threshold, params['min_score'], params['max_cost'])
        scopes[scope] = dict(minimum_score=threshold, qualified_identities=sorted(row['identity'] for row in qualified),
                             selected=deepcopy(selected))
    return dict(schema_version=1, kind='personal-cp', policy=POLICY,
                benchmark={key: benchmark[key] for key in ('identity', 'model', 'effort', 'score')},
                score_eps=score_eps, tolerance_multiplier=choice['tolerance_multiplier'],
                tolerance_points=tolerance, minimum_score=threshold, scenario_floor=params['min_score'],
                max_cost=params['max_cost'], scopes=scopes)
