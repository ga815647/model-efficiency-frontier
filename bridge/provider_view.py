"""Precompute provider-only ladders from source-verified full results.

These are separately identified website views, never replacement result envelopes.
The caller must validate the parent's immutable source proof before publication.
"""
from copy import deepcopy
import re

from .result import validate_envelope
from .result_v1 import extra
from .window_ladder import calculate_ladder

PROVIDERS = {'gpt':'ChatGPT', 'gemini':'Google Gemini', 'claude':'Claude', 'grok':'Grok'}
_CONTEXT = ('parameters', 'eps', 'selection_policy', 'selection_parameters',
            'source_snapshot', 'source_dates', 'benchmark', 'benchmark_version',
            'cost_basis', 'version_status', 'caveats', 'operation', 'product_sha',
            'request_commit_sha', 'request_id', 'run_id', 'run_attempt')


def provider_for(row):
    if row.get('is_contributor') or extra._contributor({'identity':row.get('identity','')}):
        return None
    identity = row.get('identity') or row.get('model') or row.get('name','')
    if identity.startswith('GPT-'):
        return 'gpt'
    if extra._grok({'identity':identity}):
        return 'grok'
    if extra._is_claude(identity):
        return 'claude'
    if re.match(r'^gemini(?:$|[^a-z0-9])', identity, re.IGNORECASE):
        return 'gemini'
    return None


def calculate_provider_view(envelope, provider):
    validate_envelope(envelope)
    if provider not in PROVIDERS or envelope['status'] != 'success' or envelope['schema_version'] not in (2,3,4):
        raise ValueError('invalid_provider_parent')
    candidates = [row for row in envelope['candidate_statuses'] if provider_for(row) == provider]
    # Rehydrate every family candidate, including those excluded in the mixed
    # competition. Preserve all source numbers; the existing selector decides.
    rows = [dict(identity=r['identity'], model=r['model'], effort=r['effort'],
                 notes=r['notes'], evidence_url=r['source_url'], checked_date=r['source_date'],
                 _score=r['score'], _cost=r['cost_adj'], _cost_orig=r['cost_orig'],
                 _cp_orig=r['cp_orig'], _factor=r['factor']) for r in candidates]
    params = envelope['parameters']
    calculation = calculate_ladder(rows,min_score=params['min_score'],max_cost=params['max_cost'],include_claude=envelope['schema_version']==4)
    calculation.update({key:deepcopy(envelope[key]) for key in _CONTEXT})
    if 'eligibility_policy' in envelope:
        calculation['eligibility_policy']=envelope['eligibility_policy']
    compared = calculation['ladder'] if provider == 'claude' else []
    comparison_anchors = {
        'highest_retained_score': min(compared,key=lambda r:(-r['score'],r['cost_adj'],r['identity'])) if compared else None,
        'lowest_retained_cost': min(compared,key=lambda r:(r['cost_adj'],-r['score'],r['identity'])) if compared else None}
    return dict(schema_version=1,kind='provider-ladder',provider=provider,
                provider_label=PROVIDERS[provider],calculation=calculation,
                comparison_anchors=comparison_anchors)
