"""Build an allowlisted Pages tree from immutable, independently verified Git results."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile

from bridge.choice_report import WEBSITE_VERSION, render_html
from bridge.publish import _order, _json
from bridge.result import calculate_snapshot, validate_envelope
from bridge.view_evidence import source_observations
from bridge.runner import (_git, _read, _publication_origin, _verified_transport,
                           materialize_snapshot)
from bridge.cost_policy import validate_policy, validate_source_parameters


class SiteError(ValueError):
    pass


RESULT_PATH = re.compile(r'results/[0-9a-f-]{36}/[A-Za-z0-9._-]+-[1-9][0-9]*/result\.json\Z')


def validate_upstream(run, repository):
    if (run.get('event') != 'push' or run.get('status') != 'completed' or run.get('conclusion') != 'success'
            or run.get('path') != '.github/workflows/chat-execution.yml'
            or run.get('repository', {}).get('full_name') != repository
            or run.get('head_repository', {}).get('full_name') != repository
            or not re.fullmatch(r'efficiency-run/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}', run.get('head_branch',''))
            or not re.fullmatch('[0-9a-f]{40}', run.get('head_sha',''))
            or type(run.get('id')) is not int or run['id'] <= 0
            or type(run.get('run_attempt')) is not int or run['run_attempt'] <= 0):
        raise SiteError('untrusted_upstream_run')
    return str(run['id']), run['run_attempt'], run['head_sha']


def validate_base_path(path):
    if not re.fullmatch(r'/(?:[A-Za-z0-9_-]+/)*', path):
        raise SiteError('invalid_base_path')
    return path


def observations_for_source(repo, envelope, publication):
    """Only call after source proof validation; no new pricing or inference."""
    source = envelope['source_snapshot']
    if envelope['operation'] == 'refresh':
        sha, base = publication, f'results/{envelope["request_id"]}/{envelope["run_id"]}-{envelope["run_attempt"]}/snapshot/evidence/'
    elif source['path'].startswith('results/'):
        sha, base = source['commit'], source['path'].removesuffix('candidates.csv') + 'evidence/'
    else:
        return []  # Archived sources have a different evidence contract.
    from bridge.runner import _has_file
    if not _has_file(repo, sha, base + 'leaderboard_records.json'):
        return []
    records = _json(_read(repo, sha, base + 'leaderboard_records.json'))
    source_map = _json(_read(repo, sha, base + 'source_map.json'))
    return source_observations(records, source_map)


def load_record(repo, results_commit, path):
    """Verify immutable introduction, strict envelope, request transport and source bytes."""
    if not RESULT_PATH.fullmatch(path):
        raise SiteError('invalid_result_path')
    raw = _read(repo, results_commit, path)
    envelope = validate_envelope(_json(raw))
    if envelope['status'] != 'success' or envelope['schema_version'] not in (2, 3):
        raise SiteError('not_successful_window_result')
    base = path.removesuffix('result.json')
    if base != f'results/{envelope["request_id"]}/{envelope["run_id"]}-{envelope["run_attempt"]}/':
        raise SiteError('result_path_identity_mismatch')
    origin = _publication_origin(repo, results_commit, base)
    if _read(repo, origin, path) != raw:
        raise SiteError('historical_result_changed')
    facts = _verified_transport(repo, event_sha=envelope['request_commit_sha'],
                                ref_name='efficiency-run/' + envelope['request_id'])
    request = facts['request']
    if envelope['schema_version'] != (3 if request['schema_version'] == 2 else 2):
        raise SiteError('request_result_schema_mismatch')
    for key in ('request_id', 'product_sha', 'operation', 'parameters', 'created_at'):
        if envelope[key] != request[key]:
            raise SiteError('request_result_mismatch: ' + key)
    if envelope['operation'] == 'recompute' and envelope['source_snapshot'] != request['source_snapshot']:
        raise SiteError('request_source_mismatch')
    locator = (dict(commit=origin, path=base + 'snapshot/candidates.csv')
               if envelope['operation'] == 'refresh' else envelope['source_snapshot'])
    with tempfile.TemporaryDirectory(prefix='pages-proof-') as temporary:
        csv_path, provenance = materialize_snapshot(locator, Path(repo), Path(temporary))
        if envelope['operation'] == 'refresh':
            provenance['source_locator'] = envelope['source_snapshot']
        calculation, _ = calculate_snapshot(csv_path, envelope['parameters'], provenance)
        if any(envelope.get(key) != value for key, value in calculation.items()):
            raise SiteError('source_result_mismatch')
        csv_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    report = _read(repo, origin, base + 'report.html')
    if report != _read(repo, results_commit, base + 'report.html'):
        raise SiteError('historical_report_changed')
    return dict(envelope=envelope, publication_commit=origin, result_bytes=raw,
                report_bytes=report, csv_sha256=csv_hash,
                observations=observations_for_source(repo, envelope, origin))


def _home_order(record):
    envelope = record['envelope']
    return _order(envelope) + (envelope['run_id'], envelope['run_attempt'])


def select_home(records, formal_parameters):
    formal = [r for r in records if r['envelope']['status'] == 'success'
              and r['envelope']['schema_version'] in (2, 3)
              and r['envelope']['parameters'] == formal_parameters]
    if not formal:
        raise SiteError('no_verified_formal_success')
    return max(formal, key=_home_order)


def _manifest(record, product, base_path):
    envelope = record['envelope']
    return dict(website_version=WEBSITE_VERSION, site_product_commit=product,
                product_commit=envelope['product_sha'], publication_commit=record['publication_commit'],
                request_commit=envelope['request_commit_sha'], request_id=envelope['request_id'],
                run_id=envelope['run_id'], run_attempt=envelope['run_attempt'],
                source_dates=envelope['source_dates'], operation=envelope['operation'],
                parameters=envelope['parameters'], result_schema_version=envelope['schema_version'],
                result_url=base_path + f'results/{envelope["request_id"]}/{envelope["run_id"]}-{envelope["run_attempt"]}/',
                result_sha256=hashlib.sha256(record['result_bytes']).hexdigest(),
                report_sha256=hashlib.sha256(record['report_bytes']).hexdigest(),
                source_csv_sha256=record['csv_sha256'])


def write_site(records, output, *, formal_parameters, site_product_commit, base_path):
    validate_base_path(base_path)
    home = select_home(records, formal_parameters)
    if not re.fullmatch('[0-9a-f]{40}', site_product_commit):
        raise SiteError('invalid_site_product_commit')
    files = {'.nojekyll': b''}
    for record in records:
        envelope = record['envelope']
        if envelope['status'] != 'success' or envelope['schema_version'] not in (2, 3):
            raise SiteError('not_successful_window_result')
        manifest = _manifest(record, site_product_commit, base_path)
        path = f'results/{envelope["request_id"]}/{envelope["run_id"]}-{envelope["run_attempt"]}/'
        if not RESULT_PATH.fullmatch(path + 'result.json') or path + 'index.html' in files:
            raise SiteError('duplicate_or_invalid_result_path')
        links = [('固定結果頁', manifest['result_url']), ('下載已驗證 JSON', manifest['result_url']+'result.json'),
                 ('下載備用 HTML', manifest['result_url']+'report.html'), ('網站發布 manifest', manifest['result_url']+'manifest.json')]
        page = render_html(envelope, observations=record['observations'], links=links).encode()
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode()
        files.update({path+'index.html':page, path+'result.json':record['result_bytes'],
                      path+'report.html':record['report_bytes'], path+'manifest.json':manifest_bytes})
        if record is home:
            files.update({'index.html':page, 'manifest.json':manifest_bytes})
    # Validate every record before touching the destination. Deployment receives
    # only this fresh tree, never a repository or raw evidence directory.
    output = Path(output)
    if output.exists():
        raise SiteError('output_must_be_new')
    output.mkdir(parents=True)
    for name, data in files.items():
        target=output/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
    return _manifest(home, site_product_commit, base_path)


def build_site(repository, results_commit, output, *, base_path, expected_run=None):
    repo = Path(repository)
    product = _git(repo,'rev-parse','HEAD').decode().strip()
    policy = validate_policy(_json(_read(repo, product, 'bridge/site-policy.json')))
    pinned = policy['source_refresh']
    formal_source = load_record(repo, pinned['commit'], pinned['path'])
    if formal_source['envelope']['operation'] != 'refresh':
        raise SiteError('formal_policy_source_mismatch')
    validate_source_parameters(policy, formal_source['envelope']['parameters'])
    paths = _git(repo, 'ls-tree','-r','--name-only',results_commit,'--','results').decode().splitlines()
    records=[]
    for path in paths:
        if RESULT_PATH.fullmatch(path):
            envelope=validate_envelope(_json(_read(repo,results_commit,path)))
            if envelope['status']=='success' and envelope['schema_version'] in (2, 3):
                records.append(load_record(repo,results_commit,path))
    if expected_run:
        matches=[r for r in records if (r['envelope']['run_id'],r['envelope']['run_attempt'],r['envelope']['request_commit_sha'])==expected_run]
        if len(matches)!=1:
            raise SiteError('upstream_run_result_missing')
    return write_site(records,output,formal_parameters=policy['formal_parameters'],
                      site_product_commit=product,base_path=base_path)


def main(argv=None):
    import sys
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == 'verify-upstream':
        parser=argparse.ArgumentParser()
        parser.add_argument('--run-json',type=Path,required=True)
        parser.add_argument('--repository',required=True)
        parser.add_argument('--github-output',type=Path,required=True)
        args=parser.parse_args(argv[1:])
        run,attempt,head=validate_upstream(_json(args.run_json.read_bytes()),args.repository)
        with args.github_output.open('a') as stream:
            stream.write(f'run={run}\nattempt={attempt}\nhead={head}\n')
        return 0
    parser=argparse.ArgumentParser()
    parser.add_argument('--repository',type=Path,default=Path('.'))
    parser.add_argument('--results-commit',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--base-path',required=True)
    parser.add_argument('--upstream-run')
    parser.add_argument('--upstream-attempt',type=int)
    parser.add_argument('--upstream-head')
    args=parser.parse_args(argv)
    expected=(args.upstream_run,args.upstream_attempt,args.upstream_head) if args.upstream_run else None
    manifest=build_site(args.repository,args.results_commit,args.output,base_path=args.base_path,expected_run=expected)
    print(json.dumps(manifest,ensure_ascii=False))
    return 0


if __name__=='__main__': raise SystemExit(main())
