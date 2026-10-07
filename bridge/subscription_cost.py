"""Explicit subscription cost scenarios; no source prices or selection changes."""
import math
import re

from .result_v1 import extra

LEGACY_PARAMETERS = {'gpt_factor', 'grok_factor', 'min_score', 'min_score_reason', 'max_cost'}
SUBSCRIPTION_PARAMETERS = LEGACY_PARAMETERS | {'gemini_factor', 'claude_factor'}
FACTOR_KEYS = ('gpt_factor', 'gemini_factor', 'claude_factor', 'grok_factor')


def factor_for(row, parameters):
    # Contributor pricing is already its own plan; never compound a factor.
    if extra._contributor(row):
        return 1
    identity = row['identity']
    if identity.startswith('GPT-'):
        return parameters['gpt_factor']
    if extra._grok(row):
        return parameters['grok_factor']
    if extra._is_claude(identity):
        return parameters.get('claude_factor', 1)
    if re.match(r'^gemini(?:$|[^a-z0-9])', identity, re.IGNORECASE):
        return parameters.get('gemini_factor', 1)
    return 1


def adjust_rows(rows, parameters):
    # Keep the existing paid-row validation and original projections intact.
    paid = extra.adjust_rows(rows, parameters['gpt_factor'], 'GPT-', parameters['grok_factor'])
    for row in paid:
        factor = factor_for(row, parameters)
        cost = row['_cost_orig'] / factor
        cp = row['_score'] / cost if cost else float('inf')
        if not (math.isfinite(cost) and cost > 0 and math.isfinite(cp)):
            raise ValueError('invalid adjusted cost/CP: ' + row['identity'])
        row.update(_cost=cost, _factor=factor)
    return paid


def scenario_label(parameters, *, include_claude=False):
    parts = [f'GPT ×{parameters["gpt_factor"]}']
    if set(parameters) == SUBSCRIPTION_PARAMETERS:
        parts.extend((f'Gemini ×{parameters["gemini_factor"]}', f'Claude ×{parameters["claude_factor"]}'+('' if include_claude else '（僅比較）')))
    parts.extend((f'Grok ×{parameters["grok_factor"]}', 'Contributor ×1'))
    return '／'.join(parts)
