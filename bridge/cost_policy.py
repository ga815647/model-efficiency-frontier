"""Validate the single Chat-maintained subscription table and its provenance."""
import argparse
from datetime import date
from pathlib import Path
import re
from urllib.parse import urlsplit

from .request import _snapshot
from .result_v2 import _parameters
from .subscription_cost import FACTOR_KEYS, scenario_label


def validate_policy(policy):
    if type(policy) is not dict:
        raise ValueError('invalid_site_policy')
    legacy = set(policy) == {'formal_parameters', 'source_refresh'}
    if not legacy and (set(policy) != {'schema_version', 'formal_parameters', 'source_refresh', 'factor_evidence'}
                       or type(policy['schema_version']) is not int or policy['schema_version'] != 2):
        raise ValueError('invalid_site_policy')
    _parameters(policy['formal_parameters'], 2 if legacy else 3)
    locator = policy['source_refresh']
    if type(locator) is not dict or set(locator) != {'commit', 'path'} or type(locator['path']) is not str:
        raise ValueError('invalid_policy_source')
    if not re.fullmatch(r'results/[0-9a-f-]{36}/[A-Za-z0-9._-]+-[1-9][0-9]*/result\.json', locator['path']):
        raise ValueError('invalid_policy_source')
    _snapshot(dict(commit=locator['commit'], path=locator['path'].removesuffix('result.json')+'snapshot/candidates.csv'))
    if legacy:
        return policy
    evidence = policy['factor_evidence']
    if type(evidence) is not dict or set(evidence) != set(FACTOR_KEYS):
        raise ValueError('missing_factor_evidence')
    for item in evidence.values():
        if (type(item) is not dict or set(item) != {'basis', 'as_of', 'references', 'calculation', 'limitations'}
                or item['basis'] not in ('user_specified', 'researched', 'inherited')
                or type(item['as_of']) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', item['as_of'])
                or type(item['references']) is not list or not item['references']
                or any(type(r) is not str or not r.strip() for r in item['references'])
                or type(item['limitations']) is not str or not item['limitations'].strip()
                or item['calculation'] is not None and (type(item['calculation']) is not str or not item['calculation'].strip())):
            raise ValueError('invalid_factor_evidence')
        date.fromisoformat(item['as_of'])
        if item['basis'] == 'researched' and (item['calculation'] is None or
                any(urlsplit(r).scheme != 'https' or not urlsplit(r).netloc or urlsplit(r).username
                    for r in item['references'])):
            raise ValueError('unverifiable_factor_research')
    return policy


def validate_source_parameters(policy, source_parameters):
    validate_policy(policy)
    formal = policy['formal_parameters']
    if 'schema_version' not in policy:
        equal = source_parameters == formal
    else:
        # Subscription factors deliberately change; the source's authorized
        # floor/reason/cap remain independent and must be inherited exactly.
        equal = all(source_parameters.get(k) == formal[k]
                    for k in ('min_score', 'min_score_reason', 'max_cost'))
    if not equal:
        raise ValueError('formal_policy_source_mismatch')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('check', 'show'))
    parser.add_argument('--policy', type=Path, default=Path('bridge/site-policy.json'))
    args = parser.parse_args(argv)
    from .request import decode_request
    policy = validate_policy(decode_request(args.policy.read_text()))
    if args.operation == 'show':
        print(scenario_label(policy['formal_parameters']))
        for key, item in policy.get('factor_evidence', {}).items():
            print(f'{key}: {item["basis"]}; {item["as_of"]}; ' + ' / '.join(item['references']))
    else:
        print('subscription policy valid')
    return 0


if __name__ == '__main__': raise SystemExit(main())
