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
from bridge.inventory import InventoryError, validate_fresh_inventory
from bridge.request import RequestError, decode_request, validate_request
from bridge.result import calculate_snapshot, make_envelope, validate_envelope
from bridge.source_policy import PolicyError, decode_refresh_policy
from scripts.refresh_snapshot import refresh_snapshot, fetch_public, _previous_slugs
from scripts.refresh_inventory import tracked_public_slugs


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
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate source JSON key')
            result[key] = value
        return result
    try:
        return json.loads(_read(repo, sha, path), object_pairs_hook=pairs)
    except (ValueError, UnicodeDecodeError) as exc:
        raise RunnerError('invalid_source_json: ' + path) from exc


def _has_file(repo, sha, path):
    return bool(_git(repo, 'ls-tree', sha, '--', path))


def _refresh_policy(repository, product_sha, *, approved_main_sha=None):
    """Authorize original product against execution-start main; never infer policy from maps."""
    _commit(repository, product_sha)
    authority = (approved_main_sha if approved_main_sha is not None else
                 _git(repository, 'rev-parse', '--verify', 'refs/bridge/approved-main').decode().strip())
    _commit(repository, authority)
    if not _ancestor(repository, product_sha, authority):
        raise RunnerError('source_product_not_authorized')
    path = 'bridge/refresh-policy.json'
    data = _read(repository, product_sha, path) if _has_file(repository, product_sha, path) else None
    try:
        return decode_refresh_policy(data)
    except PolicyError as exc:
        raise RunnerError('invalid_refresh_policy') from exc


def _inventory_evidence(repository, publication_sha, prefix):
    return {name: _read(repository, publication_sha, prefix + 'snapshot/evidence/' + name)
            for name in ('leaderboard.html', 'leaderboard_records.json', 'sources.json')}


def _publication_origin(repo, sha, prefix):
    path = prefix + 'result.json'
    history = _git(repo, 'rev-list', '--full-history', '--reverse', '--topo-order', sha,
                   '--', path).decode().splitlines()
    origins = []
    for commit in history:
        parents = _git(repo, 'rev-list', '--parents', '-n', '1', commit).decode().split()[1:]
        if _has_file(repo, commit, path) and all(not _has_file(repo, parent, path) for parent in parents):
            origins.append(commit)
    # An immutable append-only attempt has one introduction. Full history is
    # essential: TREESAME merge simplification can hide a conflicting sibling.
    if len(origins) != 1:
        raise RunnerError('ambiguous_publication_origin')
    return origins[0]


def _published_refresh_policy(repo, sha, prefix, envelope, *, approved_main_sha=None):
    original = _json(repo, _publication_origin(repo, sha, prefix), prefix + 'result.json')
    if original.get('product_sha') != envelope['product_sha']:
        raise RunnerError('source_product_changed')
    return _refresh_policy(repo, original['product_sha'], approved_main_sha=approved_main_sha)


def _legacy_workflow_context(bootstrap, *, event_sha, ref_name):
    """Repeat the authenticated bootstrap gate, read-only, for the old CLI wire.

    These paths are workflow constants, not output/request-controlled locators.
    Bootstrap HEAD is its fixed approved-main checkout, never a moving ref.
    """
    bootstrap = Path(bootstrap)
    source = bootstrap.parent / 'product'
    handoff = bootstrap.parent / 'handoff'
    facts = _verified_transport(bootstrap, event_sha=event_sha, ref_name=ref_name)
    product, main, raw = (facts[key] for key in ('product_sha', 'approved_main_sha', 'request_bytes'))
    if (handoff / 'product.sha').read_text(encoding='ascii').strip().lower() != product.lower() or (
            handoff / 'request.json').read_bytes() != raw:
        raise RunnerError('invalid_product_handoff')
    if _git(source, 'rev-parse', 'HEAD').decode().strip().lower() != product.lower():
        raise RunnerError('product_context_mismatch')
    if _refresh_policy(source, product, approved_main_sha=main) is not None:
        raise RunnerError('legacy_workflow_requires_legacy_product')
    return source, product, main


def _verified_transport(repo, *, event_sha, ref_name):
    """Read-only authentication gate shared by prepare and old-wire publication."""
    parent = None
    try:
        if type(event_sha) is not str or not SHA.fullmatch(event_sha):
            raise RunnerError('invalid_event_sha')
        _commit(repo, event_sha)
        parents = _git(repo, 'rev-list', '--parents', '-n', '1', event_sha).decode().split()
        if len(parents) != 2:
            raise RunnerError('invalid_request_parents')
        parent = parents[1]
        main = _git(repo, 'rev-parse', 'HEAD').decode().strip()
        _commit(repo, main)
        if not _ancestor(repo, parent, main):
            raise RunnerError('product_not_on_main')
        identity = ref_name.removeprefix('efficiency-run/') if ref_name.startswith('efficiency-run/') else ''
        if not UUID.fullmatch(identity):
            raise RunnerError('invalid_event_ref')
        path = 'bridge/requests/' + identity + '.json'
        changes = _git(repo, 'diff-tree', '--no-commit-id', '--name-status', '-r', event_sha).decode().splitlines()
        if changes != ['A\t' + path]:
            raise RunnerError('invalid_changed_paths')
        raw = _read(repo, event_sha, path)
        request = decode_request(raw.decode('utf-8'))
        validate_request(request, branch=ref_name, parent_sha=parent, changed_paths=[('A', path)])
        return dict(product_sha=parent, approved_main_sha=main, request_bytes=raw, request=request)
    except Exception as exc:
        # Prepare retains correlation with a verified single parent even when a
        # later check fails; the gate itself writes no diagnostics or handoff.
        exc.product_sha = parent
        raise


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


def _fresh_inventory(data, source_map, envelope, *, error_code, refresh_policy=None,
                     evidence=None, expected_previous_slugs=None):
    """Preserve RunnerError at the Git read boundary; share reconciliation."""
    try:
        validate_fresh_inventory(data, source_map, envelope, error_code=error_code,
                                 refresh_policy=refresh_policy, evidence=evidence,
                                 expected_previous_slugs=expected_previous_slugs)
    except InventoryError as exc:
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
        policy = _published_refresh_policy(repository, sha, prefix, envelope)
        proof = _inventory_evidence(repository, sha, prefix) if policy else None
        previous = _original_previous(repository, sha, prefix, envelope, inventory) if policy else None
        _fresh_inventory(data, inventory, envelope, error_code='result_inventory_mismatch',
                         refresh_policy=policy, evidence=proof, expected_previous_slugs=previous)
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


def _previous(repo, product_sha, *, approved_main_sha=None):
    return _previous_context(repo, product_sha, approved_main_sha=approved_main_sha)[0]


def _previous_context(repo, product_sha, *, approved_main_sha=None):
    # Resolve results once; subsequent reads use only that exact object ID.
    ref = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', 'refs/heads/results'],
                         capture_output=True)
    tip = None if ref.returncode else ref.stdout.decode().strip()
    inventory, path = _previous_at(repo, product_sha, tip, approved_main_sha=approved_main_sha)
    return inventory, dict(product_sha=product_sha, results_commit=tip, result_path=path)


def _original_previous(repo, publication_sha, prefix, envelope, inventory, *, approved_main_sha=None, seen=None):
    """Derive P from an immutable predecessor, never from this map's reconciliation."""
    locator = inventory.get('previous_inventory')
    if (type(locator) is not dict or set(locator) != {'product_sha', 'results_commit', 'result_path'} or
            locator['product_sha'] != envelope['product_sha']):
        raise RunnerError('invalid_previous_inventory')
    # Anchor the locator to the immutable first introduction of this result.
    # Otherwise a later coherent rewrite could replace a real results context
    # with a valid-but-different archive context and erase newly tracked slugs.
    # Do not infer execution context from the append parent: concurrent writers
    # may legitimately append after a result they did not observe at startup.
    original = _json(repo, _publication_origin(repo, publication_sha, prefix),
                     prefix + 'snapshot/evidence/source_map.json')
    if original.get('previous_inventory') != locator:
        raise RunnerError('previous_inventory_origin_mismatch')
    _commit(repo, locator['product_sha'])
    seen = set() if seen is None else set(seen)
    key = (publication_sha, prefix)
    if key in seen:
        raise RunnerError('previous_inventory_cycle')
    seen.add(key)
    predecessor = locator['results_commit']
    if predecessor is None:
        if locator['result_path'] is not None:
            raise RunnerError('invalid_previous_inventory')
    else:
        _commit(repo, predecessor)
        if (predecessor == publication_sha or not _ancestor(repo, predecessor, publication_sha) or
                _has_file(repo, predecessor, prefix + 'result.json')):
            raise RunnerError('invalid_previous_inventory_ancestry')
    previous, path = _previous_at(repo, locator['product_sha'], predecessor,
                                  approved_main_sha=approved_main_sha, seen=seen)
    if locator['result_path'] != path:
        raise RunnerError('previous_inventory_path_mismatch')
    return tracked_public_slugs(previous, _previous_slugs(previous)[0])


def _previous_at(repo, product_sha, tip, *, approved_main_sha=None, seen=None):
    """Read one fixed results context, including proven archive fallback states."""
    if tip is None:
        previous = _json(repo, product_sha, ARCHIVE + '/public_candidate_source_map.json')
        _previous_slugs(previous)
        return previous, None
    _commit(repo, tip)
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
        previous = _json(repo, product_sha, ARCHIVE + '/public_candidate_source_map.json')
        _previous_slugs(previous)
        return previous, None
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
    version = _json(repo, tip, prefix + 'snapshot/evidence/version.json')
    if version.get('benchmark_version') != envelope['benchmark_version']:
        raise RunnerError('result_version_mismatch')
    policy = _published_refresh_policy(repo, tip, prefix, envelope, approved_main_sha=approved_main_sha)
    proof = _inventory_evidence(repo, tip, prefix) if policy else None
    previous = _original_previous(repo, tip, prefix, envelope, inventory,
                                  approved_main_sha=approved_main_sha, seen=seen) if policy else None
    _fresh_inventory(data, inventory, envelope, error_code='invalid_latest_refresh_inventory',
                     refresh_policy=policy, evidence=proof, expected_previous_slugs=previous)
    return inventory, path


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
            policy = _refresh_policy(repository, execution['product_sha'])
            previous, previous_inventory = _previous_context(repository, execution['product_sha'])
            expected = tracked_public_slugs(previous, _previous_slugs(previous)[0])
            provenance = refresh_snapshot(output / 'snapshot',
                                          previous=previous, fetch=fetch,
                                          previous_inventory=previous_inventory if policy else None)
            source_path = output / 'snapshot/candidates.csv'
        else:
            if validated['source_snapshot']['path'].startswith('runs/') and not _ancestor(
                    repository, validated['source_snapshot']['commit'], execution['product_sha']):
                raise RunnerError('source_commit_not_authorized')
            source_path, provenance = materialize_snapshot(validated['source_snapshot'], repository, output)
        calculation, report = calculate_snapshot(source_path, validated['parameters'], provenance)
        envelope = make_envelope(validated, execution, calculation=calculation, errors=[])
        if validated['operation'] == 'refresh':
            evidence = output / 'snapshot/evidence'
            proof = {name: (evidence / name).read_bytes() for name in
                     ('leaderboard.html', 'leaderboard_records.json', 'sources.json')} if policy else None
            _fresh_inventory(source_path.read_bytes(), json.loads((evidence / 'source_map.json').read_bytes()),
                             envelope, error_code='invalid_refresh_inventory', refresh_policy=policy,
                             evidence=proof, expected_previous_slugs=expected if policy else None)
        from bridge.view_evidence import source_observations
        # The source has already passed materialization/proof validation above.
        observations = []
        if validated['operation'] == 'refresh':
            source_map = json.loads((output / 'snapshot/evidence/source_map.json').read_bytes())
            records = json.loads((output / 'snapshot/evidence/leaderboard_records.json').read_bytes())
            observations = source_observations(records, source_map)
        elif validated['source_snapshot']['path'].startswith('results/'):
            source = validated['source_snapshot']
            base = source['path'].removesuffix('candidates.csv') + 'evidence/'
            if _has_file(repository, source['commit'], base + 'leaderboard_records.json'):
                observations = source_observations(
                    _json(repository, source['commit'], base + 'leaderboard_records.json'),
                    _json(repository, source['commit'], base + 'source_map.json'))
        html = render_html(envelope, observations=observations)
        _atomic(output / 'report.md', report.encode('utf-8'))
        _atomic(output / 'report.html', html.encode('utf-8'))
    except Exception as exc:
        for name in ('report.md', 'report.html'):
            (output / name).unlink(missing_ok=True)
        code = getattr(exc, 'code', None) or (str(exc).split(':', 1)[0] if isinstance(exc, ValueError) else 'execution_failed')
        # Event-ref UUID and commit are trusted for correlation, not arbitrary JSON identity.
        branch = execution.get('branch', '')
        identity = branch.removeprefix('efficiency-run/') if branch.startswith('efficiency-run/') else None
        safe_request = {'schema_version': 2 if type(request) is dict and type(request.get('schema_version')) is int and request['schema_version'] == 2 else 1,
                        'operation': request.get('operation') if type(request) is dict else None,
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


def verify_transport(repo: Path, *, event_sha: str, ref_name: str, run_id: str,
                     run_attempt: int, output: Path, product_sha_file: Path,
                     github_output: Path | None = None) -> bool:
    """Bootstrap gate: inspect the authenticated push commit, never its checkout."""
    output = Path(output)
    product_sha_file = Path(product_sha_file)
    product_sha_file.unlink(missing_ok=True)
    parent = None
    try:
        facts = _verified_transport(repo, event_sha=event_sha, ref_name=ref_name)
        parent, request_bytes, request = (facts[key] for key in ('product_sha', 'request_bytes', 'request'))
        # An atomic handoff; no JSON-derived paths are used by the workflow.
        _atomic(product_sha_file.parent / 'request.json', request_bytes)
        _atomic(product_sha_file, (parent + '\n').encode('ascii'))
        if github_output is not None:
            with Path(github_output).open('a') as stream:
                stream.write('product_sha=' + parent + '\noperation=' + request['operation'] +
                             '\nrequest_id=' + request['request_id'] + '\n')
        return True
    except Exception as exc:
        parent = getattr(exc, 'product_sha', parent)
        (product_sha_file.parent / 'request.json').unlink(missing_ok=True)
        write_diagnostic_failure(output, event_sha=event_sha, ref_name=ref_name,
                                 product_sha=parent, run_id=run_id, run_attempt=run_attempt,
                                 code=str(exc).split(':', 1)[0] or 'transport_failed')
        return False


def write_diagnostic_failure(output: Path, *, event_sha: str, ref_name: str,
                             product_sha: str | None, run_id: str, run_attempt: int,
                             code: str) -> None:
    identity = ref_name.removeprefix('efficiency-run/') if ref_name.startswith('efficiency-run/') else ''
    request = dict(operation=None, request_id=identity if UUID.fullmatch(identity) else None,
                   product_sha=product_sha if product_sha and SHA.fullmatch(product_sha) else '0' * 40,
                   created_at=None, source_snapshot=None, parameters=None)
    execution = dict(request_commit_sha=event_sha if SHA.fullmatch(event_sha) else '0' * 40,
                     run_id=run_id, run_attempt=run_attempt,
                     run_url=os.environ.get('GITHUB_RUN_URL') or
                     f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'unknown/unknown')}/actions/runs/{run_id}")
    envelope = make_envelope(request, execution, calculation=None,
                             errors=[{'code': code, 'message': code}])
    _atomic(Path(output) / 'result.json',
            (json.dumps(envelope, ensure_ascii=False, indent=2) + '\n').encode())


def main(argv=None):
    if argv is None:
        import sys
        argv = sys.argv[1:]
    if argv and argv[0] == 'verify-transport':
        parser = argparse.ArgumentParser()
        parser.add_argument('--repository', type=Path, required=True)
        parser.add_argument('--event-sha', required=True)
        parser.add_argument('--ref-name', required=True)
        parser.add_argument('--run-id', required=True)
        parser.add_argument('--run-attempt', type=int, required=True)
        parser.add_argument('--output', type=Path, required=True)
        parser.add_argument('--product-sha-file', type=Path, required=True)
        parser.add_argument('--github-output', type=Path)
        args = parser.parse_args(argv[1:])
        return 0 if verify_transport(args.repository, event_sha=args.event_sha,
                                      ref_name=args.ref_name, run_id=args.run_id,
                                      run_attempt=args.run_attempt, output=args.output,
                                      product_sha_file=args.product_sha_file,
                                      github_output=args.github_output) else 1
    if argv and argv[0] == 'assert-success':
        parser = argparse.ArgumentParser()
        parser.add_argument('--output', type=Path, required=True)
        args = parser.parse_args(argv[1:])
        try:
            result = validate_envelope(json.loads((args.output / 'result.json').read_text()))
            return 0 if result['status'] == 'success' else 1
        except (OSError, ValueError):
            return 1
    if argv and argv[0] == 'diagnostic-failure':
        parser = argparse.ArgumentParser()
        parser.add_argument('--event-sha', required=True)
        parser.add_argument('--ref-name', required=True)
        parser.add_argument('--product-sha-file', type=Path, required=True)
        parser.add_argument('--run-id', required=True)
        parser.add_argument('--run-attempt', type=int, required=True)
        parser.add_argument('--output', type=Path, required=True)
        args = parser.parse_args(argv[1:])
        write_diagnostic_failure(args.output, event_sha=args.event_sha, ref_name=args.ref_name,
                                 product_sha=args.product_sha_file.read_text().strip(),
                                 run_id=args.run_id, run_attempt=args.run_attempt,
                                 code='runner_interrupted')
        return 0
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
