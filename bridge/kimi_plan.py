"""Validate source-backed Kimi first-party membership research.

This study does not modify model identity, v3/v4 result contracts, or LADDER.
A null factor is deliberately not treated as a 1x subscription estimate.
"""
from datetime import date
import math
import re
from urllib.parse import urlsplit

from .publish import _json


def _keys(value, expected, error):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError(error)


def _date(text):
    if type(text) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', text):
        raise ValueError('invalid_kimi_research_date')
    date.fromisoformat(text)


def _text(value):
    return type(value) is str and bool(value.strip())


def _amount(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def validate_kimi_research(raw):
    """Only accept an allowlisted, attributable, research-only payload."""
    if type(raw) is not bytes:
        raise ValueError('invalid_kimi_research_bytes')
    data = _json(raw)
    _keys(data, ('schema_version', 'research_id', 'as_of', 'region',
                 'currency', 'pricing_capture_date', 'factor', 'factor_basis',
                 'factor_formula', 'model', 'plans', 'quotas', 'sources', 'limitations'),
          'invalid_kimi_research')
    if (type(data['schema_version']) is not int or data['schema_version'] != 1
            or not _text(data['research_id'])
            or data['region'] != 'international' or data['currency'] != 'USD'
            or data['factor'] is not None
            or data['factor_basis'] != 'insufficient_api_equivalent_quota_evidence'
            or not _text(data['factor_formula'])):
        raise ValueError('invalid_kimi_factor_or_research')
    _date(data['as_of'])
    _date(data['pricing_capture_date'])
    if data['pricing_capture_date'] > data['as_of']:
        raise ValueError('invalid_kimi_pricing_date')

    model = data['model']
    _keys(model, ('name', 'released_on', 'benchmark', 'benchmark_score',
                  'api_usd_per_million_input_tokens',
                  'api_usd_per_million_output_tokens', 'thinking_levels'),
          'invalid_kimi_model')
    _date(model['released_on'])
    if (model['released_on'] > data['as_of']
            or not _text(model['name']) or not _text(model['benchmark'])
            or not _amount(model['benchmark_score'])
            or not _amount(model['api_usd_per_million_input_tokens'])
            or not _amount(model['api_usd_per_million_output_tokens'])
            or model['thinking_levels'] != ['low', 'high', 'max']):
        raise ValueError('invalid_kimi_model')

    plans = data['plans']
    if type(plans) is not list or len(plans) != 4:
        raise ValueError('invalid_kimi_plans')
    for plan, (pid, label, credits, highspeed) in zip(
        plans, [('kimi-plus','Plus',1,False),('kimi-pro','Pro',2,True),
                ('kimi-max','Max',5,True),('kimi-ultra','Ultra',10,True)]
    ):
        _keys(plan, ('id','label','monthly_usd','annual_total_usd',
                     'annual_monthly_equivalent_usd','relative_agent_credits',
                     'context_tokens','highspeed','kimi_code'), 'invalid_kimi_plan')
        if (plan['id'] != pid or plan['label'] != label
                or not _amount(plan['monthly_usd'])
                or not _amount(plan['annual_total_usd'])
                or not _amount(plan['annual_monthly_equivalent_usd'])
                or abs(plan['annual_total_usd'] / 12 - plan['annual_monthly_equivalent_usd']) > 1e-9
                or plan['annual_monthly_equivalent_usd'] > plan['monthly_usd']
                or plan['relative_agent_credits'] != credits
                or type(plan['relative_agent_credits']) is not int
                or type(plan['context_tokens']) is not int or plan['context_tokens'] < 1
                or plan['highspeed'] is not highspeed or plan['kimi_code'] is not True):
            raise ValueError('invalid_kimi_plan')

    quotas = data['quotas']
    _keys(quotas, ('rolling_five_hour_window','weekly_limit_new_plans',
                   'monthly_shared_pool','published_api_equivalent_budget_usd'),
          'invalid_kimi_quota')
    if (quotas['rolling_five_hour_window'] is not True
            or quotas['weekly_limit_new_plans'] is not False
            or quotas['monthly_shared_pool'] is not True
            or quotas['published_api_equivalent_budget_usd'] is not None):
        raise ValueError('invalid_kimi_quota')

    sources = data['sources']
    if type(sources) is not list or not sources:
        raise ValueError('invalid_kimi_sources')
    indexed = {}
    for source in sources:
        _keys(source, ('id','url','checked_date','verification','note'),
              'invalid_kimi_source')
        if (not _text(source['id']) or source['id'] in indexed or
                source['id'] not in ('price','benefits','code','model','aa')
                or not _text(source['note']) or type(source['url']) is not str):
            raise ValueError('invalid_kimi_source')
        _date(source['checked_date'])
        url = urlsplit(source['url'])
        approved = ('artificialanalysis.ai' if source['id']=='aa' else
                    'www.kimi.ai' if source['id'] in ('price','benefits') else 'www.kimi.com')
        verification = ('retrieved_public_benchmark' if source['id']=='aa' else 'retrieved_official')
        if (source['checked_date'] > data['as_of'] or url.scheme != 'https'
                or url.hostname != approved or url.username or url.password or
                source['verification'] != verification):
            raise ValueError('invalid_kimi_source_provenance')
        indexed[source['id']] = source
    if set(indexed) != {'price','benefits','code','model','aa'}:
        raise ValueError('missing_kimi_source')
    if (type(data['limitations']) is not list or not data['limitations']
            or any(not _text(x) for x in data['limitations'])):
        raise ValueError('invalid_kimi_limitations')
    return data
