"""Run one request from a verified Git event; never consult moving source files."""

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

from bridge.html_report import render_html
from bridge.request import RequestError, decode_request, validate_request
from bridge.result import calculate_snapshot, make_envelope, validate_envelope
from scripts.refresh_snapshot import refresh_snapshot, fetch_public


class RunnerError(ValueError):
    """An untrusted Git source or transport has failed verification."""


SHA = re.compile(r'[0-9a-fA-F]{40}\Z')
UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z')
ARCHIVE = 'runs/2026-09-26-general-grok16'


def _git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    if result.returncode:
        raise RunnerError('git_read_failed: ' + ' '.join(args[:2]))
    return result.stdout


def _commit(repo, sha):
    if type(sha) is not str or not SHA.fullmatch(sha):
        raise RunnerError('invalid_commit')
    if _git(repo, 'rev-parse', '--verify', sha + '^{commit}').decode().strip().lower() != sha.lower():
        raise RunnerError('not_commit')


def _ancestor(repo, older, newer):
    return subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', older, newer],
                          capture_output=True).returncode == 0


def _read(repo, sha, path):
    """Read only ordinary blobs, with no filesystem dereference or path options."""
    _commit(repo, sha)
    if (type(path) is not str or not path or path.startswith('/') or
            any(part in ('', '.', '..') for part in path.split('/')) or '\\' in path or ':' in path):
        raise RunnerError('invalid_git_path')
    tree = _git(repo, 'ls-tree', sha, '--', path).decode().splitlines()
    if len(tree) != 1 or not tree[0].startswith('100644 blob ') and not tree[0].startswith('100755 blob '):
        raise RunnerError('source_not_regular_blob: ' + path)
    if tree[0].split('\t', 1)[-1] != path:
        raise RunnerError('source_path_mismatch')
    return _git(repo, 'show', sha + ':' + path)


def _json(repo, sha, path):
    try:
        return json.loads(_read(repo, sha, path))
    except (ValueError, UnicodeDecodeError) as exc:
        raise RunnerError('invalid_source_json: ' + path) from exc


def _has_file(repo, sha, path):
    return bool(_git(repo, 'ls-tree', sha, '--', path))


def _atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.')
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _historical(repo, sha, path, data):
    if path != ARCHIVE + '/candidates.csv':
        raise RunnerError('unapproved_historical_source')
    base = ARCHIVE + '/'
    mapping = _json(repo, sha, base + 'public_candidate_source_map.json')
    exact = _json(repo, sha, base + 'public_leaderboard_exact.json')
    meta = _json(repo, sha, base + 'meta_pricing_verification.json')
    notes = _read(repo, sha, base + 'run-notes.md').decode('utf-8')
    version = 'AA-Intelligence-Index-v4.3.2'
    if (mapping.get('benchmark') != version or exact.get('benchmark') != version or
            mapping.get('date') != '2026-09-26' or exact.get('checked_date') != '2026-09-26' or
            meta.get('checked_date') != '2026-09-26' or
            mapping.get('source_data') != 'public_leaderboard_exact.json' or
            'v4.3.2' not in notes or len(exact.get('release_page_crosschecks', [])) != 4 or
            not exact.get('version_attribution') or not exact.get('release_page_sha256') or
            not meta.get('USD_per_1M_tokens')):
        raise RunnerError('historical_evidence_mismatch')
    sources = mapping.get('source_by_slug')
    contributors = mapping.get('contributor')
    if type(sources) is not dict or type(contributors) is not list:
        raise RunnerError('historical_inventory_missing')
    try:
        rows = list(csv.DictReader(io.StringIO(data.decode('utf-8'))))
        public = [r for r in rows if r['pricing_plan'] != 'Contributor']
        derived = [r for r in rows if r['pricing_plan'] == 'Contributor']
        slugs = [r['notes'].split(' slug=', 1)[1].split(';', 1)[0] for r in public]
        if (set(slugs) != set(sources) or len(slugs) != len(sources) or
                len(derived) != len(contributors) or
                {r['model'] + ' (' + r['effort'] + ')' for r in derived} !=
                {r['model'] for r in contributors}):
            raise RunnerError('historical_inventory_mismatch')
        for row, slug in zip(public, slugs):
            entry = sources[slug]
            if (float(row['score']) != entry['score'] or
                    float(row['cost_per_task']) != entry['cost_per_task'] or
                    row['checked_date'] != entry['checked_date'] or
                    row['evidence_url'] != entry['source_url']):
                raise RunnerError('historical_source_mismatch')
        for row in derived:
            entry = next(c for c in contributors if c['model'] == row['model'] + ' (' + row['effort'] + ')')
            if (row['cost_per_task'] != entry['derived_cost_per_task'] or
                    row['evidence_url'] != entry['score_source'] or
                    row['checked_date'] != entry['score_source_date']):
                raise RunnerError('historical_contributor_mismatch')
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise RunnerError('historical_evidence_mismatch') from exc
    return {'benchmark': 'AA-Intelligence-Index', 'benchmark_version': version,
            'version_status': 'inferred', 'cost_basis': 'api', 'source_dates': ['2026-09-26'],
            'caveats': [
                'Public leaderboard does not label version; v4.3.2 inferred by Grok 4.7 and Muse Spark 1.3 release crosschecks.',
                'Contributor GRADE-B cache-write charged at ordinary input rate; not confirmed by Meta.',
                'GPT ×18 conservatively rounded from personal ~18.9 usage; Grok ×16 user scenario, not measured.',
            ]}


def _fresh_inventory(data, source_map, envelope, *, error_code):
    """Reconcile published fresh evidence with its immutable CSV and result.

    Never let a truncated source map become the baseline for a future refresh.
    The CSV's paid identities/slug and Contributor effort are authoritative.
    """
    try:
        if type(source_map) is not dict or type(source_map.get('inventory')) is not dict:
            raise ValueError('invalid inventory')
        inventory = source_map['inventory']
        slugs, efforts = inventory['slugs'], inventory['contributor_efforts']
        if (type(slugs) is not list or not slugs or type(efforts) is not list or
                any(type(x) is not str or not x for x in slugs + efforts) or
                len(slugs) != len(set(slugs)) or len(efforts) != len(set(efforts))):
            raise ValueError('invalid inventory sets')
        rows = list(csv.DictReader(io.StringIO(data.decode('utf-8'))))
        if len(rows) != envelope['candidate_count']:
            raise ValueError('candidate count')
        by_id = {r['identity']: r for r in envelope['candidate_statuses']}
        if len(by_id) != len(rows) or {r['identity'] for r in rows} != set(by_id):
            raise ValueError('candidate identities')
        public = [r for r in rows if r['pricing_plan'] != 'Contributor']
        contributor = [r for r in rows if r['pricing_plan'] == 'Contributor']
        csv_slugs = [r['model_version'] for r in public]
        csv_efforts = [r['effort'] for r in contributor]
        if (any(not s or ' slug=' + s + ';' not in r['notes'] for s, r in zip(csv_slugs, public)) or
                set(csv_slugs) != set(slugs) or len(csv_slugs) != len(slugs) or
                set(csv_efforts) != set(efforts) or len(csv_efforts) != len(efforts)):
            raise ValueError('CSV inventory disagreement')
        sources = source_map['source_by_slug']
        contributions = source_map['contributor']
        contributor_keys = [(r['model_version'].split('@', 1)[0], r['effort']) for r in contributor]
        if (type(sources) is not dict or set(sources) != set(csv_slugs) or
                type(contributions) is not list or len(contributions) != len(contributor) or
                {(r['slug'], r['effort']) for r in contributions} !=
                set(contributor_keys) or len(set(contributor_keys)) != len(contributor)):
            raise ValueError('source inventory disagreement')
        for row in rows:
            old = by_id[row['identity']]
            if (float(row['score']) != old['score'] or
                    float(row['cost_per_task']) != old['cost_orig'] or
                    row['checked_date'] != old['source_date'] or
                    row['evidence_url'] != old['source_url'] or
                    row['benchmark_version'] != envelope['benchmark_version'] or
                    row['benchmark'] != envelope['benchmark'] or row['cost_basis'] != envelope['cost_basis']):
                raise ValueError('result inventory disagreement')
        for row in public:
            evidence = sources[row['model_version']]
            if (float(row['score']) != float(evidence['score']) or
                    float(row['cost_per_task']) != float(evidence['cost_per_task']) or
                    row['checked_date'] != evidence['checked_date'] or
                    row['evidence_url'] != evidence['source_url']):
                raise ValueError('public evidence disagreement')
        by_contributor = {(r['slug'], r['effort']): r for r in contributions}
        for row in contributor:
            evidence = by_contributor[(row['model_version'].split('@', 1)[0], row['effort'])]
            if row['cost_per_task'] != str(evidence['derived_cost']):
                raise ValueError('Contributor evidence disagreement')
    except (KeyError, ValueError, TypeError, UnicodeError, OverflowError) as exc:
        raise RunnerError(error_code) from exc


def materialize_snapshot(locator: dict, repository: Path, output: Path) -> tuple[Path, dict]:
    """Copy validated, reachable historical or successful-results CSV by Git object ID."""
    if type(locator) is not dict or set(locator) != {'commit', 'path'}:
        raise RunnerError('invalid_source_locator')
    sha, path = locator['commit'], locator['path']
    _commit(repository, sha)
    historical = path == ARCHIVE + '/candidates.csv'
    match = re.fullmatch(r'results/([0-9a-f-]+)/([A-Za-z0-9][A-Za-z0-9._-]*-[1-9][0-9]*)/snapshot/candidates\.csv', path) if type(path) is str else None
    if not historical and (not match or not UUID.fullmatch(match[1])):
        raise RunnerError('invalid_source_locator')
    if historical:
        authorized = _git(repository, 'rev-parse', 'HEAD').decode().strip()
    else:
        authorized = _git(repository, 'rev-parse', '--verify', 'refs/heads/results').decode().strip()
    if not _ancestor(repository, sha, authorized):
        raise RunnerError('source_commit_not_authorized')
    data = _read(repository, sha, path)
    if historical:
        provenance = _historical(repository, sha, path, data)
    else:
        prefix = path.removesuffix('snapshot/candidates.csv')
        envelope = _json(repository, sha, prefix + 'result.json')
        validate_envelope(envelope)
        if (envelope['status'] != 'success' or envelope['operation'] != 'refresh' or
                envelope['request_id'] != match[1] or
                match[2] != f"{envelope['run_id']}-{envelope['run_attempt']}" or
                envelope['source_snapshot'] != {'kind': 'acquired', 'path': 'snapshot/candidates.csv',
                                                'sha256': hashlib.sha256(data).hexdigest()}):
            raise RunnerError('result_source_not_successful_refresh')
        inventory = _json(repository, sha, prefix + 'snapshot/evidence/source_map.json')
        version = _json(repository, sha, prefix + 'snapshot/evidence/version.json')
        if version.get('benchmark_version') != envelope['benchmark_version']:
            raise RunnerError('result_version_mismatch')
        _fresh_inventory(data, inventory, envelope, error_code='result_inventory_mismatch')
        provenance = {key: envelope[key] for key in ('benchmark', 'benchmark_version',
                      'version_status', 'cost_basis', 'source_dates', 'caveats')}
    provenance['source_locator'] = dict(locator)
    source_path = Path(output) / 'snapshot/candidates.csv'
    _atomic(source_path, data)
    return source_path, provenance


def _transport(repo, request, execution):
    sha = execution['request_commit_sha']
    _commit(repo, sha)
    parents = _git(repo, 'rev-list', '--parents', '-n', '1', sha).decode().split()
    if len(parents) != 2:
        raise RunnerError('invalid_request_parents')
    parent = parents[1]
    paths = _git(repo, 'diff-tree', '--no-commit-id', '--name-status', '-r', sha).decode().splitlines()
    changed = [tuple(line.split('\t', 1)) for line in paths]
    validated = validate_request(request, branch=execution['branch'], parent_sha=parent,
                                 changed_paths=changed)
    if (execution['product_sha'] != parent or not _ancestor(repo, parent, sha) or
            _read(repo, sha, 'bridge/requests/' + validated['request_id'] + '.json') !=
            json.dumps(request).encode('utf-8') and
            decode_request(_read(repo, sha, 'bridge/requests/' + validated['request_id'] + '.json').decode()) != request):
        raise RunnerError('event_request_mismatch')
    return validated


def _previous(repo, product_sha):
    # Resolve results once; subsequent reads use only that exact object ID.
    ref = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', 'refs/heads/results'],
                         capture_output=True)
    if ref.returncode:
        return _json(repo, product_sha, ARCHIVE + '/public_candidate_source_map.json')
    tip = ref.stdout.decode().strip()
    if not _has_file(repo, tip, 'latest-refresh.json'):
        # An orphan results branch or recompute-only publications are allowed.
        # A successful refresh without its pointer is inconsistent; do not
        # silently use the older archived inventory and lose new models.
        names = _git(repo, 'ls-tree', '-r', '--name-only', tip, '--', 'results').decode().splitlines()
        for name in names:
            if not re.fullmatch(r'results/[0-9a-f-]+/[A-Za-z0-9._-]+/result\.json', name):
                continue
            published = _json(repo, tip, name)
            validate_envelope(published)
            if published['status'] == 'success' and published['operation'] == 'refresh':
                raise RunnerError('missing_latest_refresh')
        return _json(repo, product_sha, ARCHIVE + '/public_candidate_source_map.json')
    pointer = _json(repo, tip, 'latest-refresh.json')
    path = pointer.get('result_path')
    if type(path) is not str or not re.fullmatch(r'results/[0-9a-f-]+/[A-Za-z0-9._-]+/result\.json', path):
        raise RunnerError('invalid_latest_refresh')
    envelope = _json(repo, tip, path)
    validate_envelope(envelope)
    if (envelope['status'] != 'success' or envelope['operation'] != 'refresh' or
            pointer.get('request_commit_sha') != envelope['request_commit_sha'] or
            path != f"results/{envelope['request_id']}/{envelope['run_id']}-{envelope['run_attempt']}/result.json"):
        raise RunnerError('invalid_latest_refresh')
    prefix = path.removesuffix('result.json')
    data = _read(repo, tip, prefix + 'snapshot/candidates.csv')
    if envelope['source_snapshot'] != {'kind': 'acquired', 'path': 'snapshot/candidates.csv',
                                       'sha256': hashlib.sha256(data).hexdigest()}:
        raise RunnerError('invalid_latest_refresh_source')
    inventory = _json(repo, tip, prefix + 'snapshot/evidence/source_map.json')
    _fresh_inventory(data, inventory, envelope, error_code='invalid_latest_refresh_inventory')
    return inventory


def _json_safe(value):
    """Keep malformed user parameters diagnosable without non-JSON floats."""
    if type(value) is float and not math.isfinite(value):
        return None
    if type(value) is dict:
        return {str(k): _json_safe(v) for k, v in value.items()}
    if type(value) is list:
        return [_json_safe(v) for v in value]
    if value is None or type(value) in (str, bool, int, float):
        return value
    return str(value)


def execute_request(request: dict, *, execution: dict, repository: Path,
                    output: Path, fetch) -> dict:
    """Always write a correlated failure if execution metadata and output are trusted."""
    output = Path(output)
    source_path = None
    try:
        validated = _transport(repository, request, execution)
        if validated['operation'] == 'refresh':
            provenance = refresh_snapshot(output / 'snapshot',
                                          previous=_previous(repository, execution['product_sha']), fetch=fetch)
            source_path = output / 'snapshot/candidates.csv'
        else:
            if validated['source_snapshot']['path'].startswith('runs/') and not _ancestor(
                    repository, validated['source_snapshot']['commit'], execution['product_sha']):
                raise RunnerError('source_commit_not_authorized')
            source_path, provenance = materialize_snapshot(validated['source_snapshot'], repository, output)
        calculation, report = calculate_snapshot(source_path, validated['parameters'], provenance)
        envelope = make_envelope(validated, execution, calculation=calculation, errors=[])
        html = render_html(calculation)
        _atomic(output / 'report.md', report.encode('utf-8'))
        _atomic(output / 'report.html', html.encode('utf-8'))
    except Exception as exc:
        for name in ('report.md', 'report.html'):
            (output / name).unlink(missing_ok=True)
        code = getattr(exc, 'code', None) or (str(exc).split(':', 1)[0] if isinstance(exc, ValueError) else 'execution_failed')
        # Event-ref UUID and commit are trusted for correlation, not arbitrary JSON identity.
        branch = execution.get('branch', '')
        identity = branch.removeprefix('efficiency-run/') if branch.startswith('efficiency-run/') else None
        safe_request = {'operation': request.get('operation') if type(request) is dict else None,
                        'request_id': identity if identity and UUID.fullmatch(identity) else None,
                        'product_sha': execution.get('product_sha'),
                        'created_at': request.get('created_at') if type(request) is dict else None,
                        'source_snapshot': None,
                        'parameters': _json_safe(request['parameters']) if type(request) is dict and type(request.get('parameters')) is dict else None}
        safe_execution = {k: execution.get(k) for k in ('request_commit_sha', 'run_id', 'run_attempt', 'run_url')}
        envelope = make_envelope(safe_request, safe_execution, calculation=None,
                                 errors=[{'code': str(code), 'message': str(exc) or type(exc).__name__}])
    _atomic(output / 'result.json', (json.dumps(envelope, ensure_ascii=False, indent=2,
                                               allow_nan=False) + '\n').encode('utf-8'))
    return envelope


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    parser.add_argument('--event-sha', required=True)
    parser.add_argument('--ref-name', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--run-attempt', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    repo = Path.cwd()
    try:
        request = decode_request(Path(args.request).read_text())
    except (ValueError, OSError):
        request = {}
    try:
        parents = _git(repo, 'rev-list', '--parents', '-n', '1', args.event_sha).decode().split()
        product_sha = parents[1] if len(parents) == 2 else '0' * 40
    except ValueError:
        product_sha = '0' * 40
    execution = dict(request_commit_sha=args.event_sha, product_sha=product_sha,
                     branch=args.ref_name, run_id=args.run_id, run_attempt=args.run_attempt,
                     run_url=os.environ.get('GITHUB_RUN_URL') or
                     f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'unknown/unknown')}/actions/runs/{args.run_id}")
    result = execute_request(request, execution=execution, repository=repo,
                             output=args.output, fetch=fetch_public)
    return 0 if result['status'] == 'success' else 1


if __name__ == '__main__':
    raise SystemExit(main())
