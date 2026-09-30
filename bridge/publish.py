"""Append one immutable execution result to a Git branch with monotone pointers."""

import argparse
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from urllib.parse import urlsplit

from bridge.inventory import InventoryError, validate_fresh_inventory
from bridge.result import validate_envelope
from bridge.request import RequestError
from scripts.meta_availability import MODELS_URL, parse_meta_models, unavailable_reason
from scripts.aa_public import SourceError
from bridge.runner import RunnerError, _refresh_policy, _previous, _legacy_workflow_context
from scripts.refresh_snapshot import _previous_slugs
from scripts.refresh_inventory import tracked_public_slugs
import csv
import io


class PublishError(ValueError):
    """The result is unsafe or cannot be appended without losing another run."""


_UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z')
_RUN = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*\Z')
_BRANCH = re.compile(r'[A-Za-z0-9][A-Za-z0-9._/-]*\Z')
_EVIDENCE = {'leaderboard.html', 'grok_release.html', 'muse_release.html',
               'meta_pricing.html', 'models.html', 'sources.json', 'meta_models.json',
               'availability.json', 'leaderboard_records.json',
              'releases.json', 'version.json', 'meta_pricing.json',
               'missing_candidates.json', 'unusable_candidates.json', 'source_map.json', 'api_diagnostic.json',
              'api_envelopes.json'}
_FILES = {'result.json', 'report.md', 'report.html', 'snapshot/candidates.csv',
           'snapshot/free-sidecar.json', 'snapshot/run-notes.md'} | {
               'snapshot/evidence/' + name for name in _EVIDENCE}
# refresh_snapshot fetches/parses the models page before these validations. A
# failed result with one of these codes cannot legitimately predate that proof.
# Previous-inventory parsing is the sole listed stage before availability.json.
_POST_PROOF_REFRESH_ERRORS = {
    'previous_inventory_missing', 'missing_candidate', 'present_candidate_unusable', 'invalid_measurement',
    'markup_drift', 'model_markup_drift', 'model_shape_drift', 'invalid_identity',
    'conflicting_slug', 'release_shape_drift', 'release_missing', 'version_missing',
    'version_disagreement', 'crosscheck_mismatch', 'model_missing',
    'training_terms_changed', 'pricing_markup', 'pricing_semantics', 'pricing_missing',
    'components_missing', 'components_inconsistent', 'effort_ambiguous',
    'api_diagnostic_failed', 'api_envelope_invalid', 'api_pagination_limit',
    'api_version_drift',
}


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise PublishError('duplicate_json_key')
        result[key] = value
    return result


def _json(data):
    try:
        return json.loads(data, object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(PublishError('nonfinite_json')))
    except (UnicodeError, ValueError) as exc:
        raise PublishError('invalid_json') from exc


def _api_response_bodies(data):
    """Only bounded API response envelopes, never captured request/response headers."""
    pages = _json(data)
    if type(pages) is not list or not 1 <= len(pages) <= 20:
        raise PublishError('invalid_api_evidence')

    def no_headers(value):
        if type(value) is dict:
            if any(key.lower() in {'headers', 'request_headers', 'response_headers',
                                   'authorization', 'x-api-key', 'cookie', 'set-cookie'}
                   for key in value):
                raise PublishError('api_evidence_contains_headers')
            for child in value.values():
                no_headers(child)
        elif type(value) is list:
            for child in value:
                no_headers(child)

    no_headers(pages)
    if any(type(page) is not dict or
           type(page.get('intelligence_index_version')) is not str or
           not page['intelligence_index_version'].strip() or
           type(page.get('data')) is not list or len(page['data']) > 200
           for page in pages):
        raise PublishError('invalid_api_evidence')
    return pages


def _date(value):
    try:
        if type(value) is not str or date.fromisoformat(value).isoformat() != value:
            raise ValueError()
        return value
    except ValueError as exc:
        raise PublishError('invalid_source_date') from exc


def _order(pointer):
    dates = pointer.get('source_dates')
    try:
        if type(dates) is not list or not dates:
            raise ValueError()
        latest = max(_date(value) for value in dates)
        timestamp = datetime.fromisoformat(pointer['created_at'])
        if timestamp.utcoffset() is None:
            raise ValueError()
        commit = pointer['request_commit_sha']
        if type(commit) is not str or not re.fullmatch('[0-9a-fA-F]{40}', commit):
            raise ValueError()
    except (KeyError, TypeError, ValueError) as exc:
        raise PublishError('invalid_pointer_order') from exc
    return (latest, timestamp.astimezone(timezone.utc), commit.lower())


def _capability_evidence(files, envelope, source_map=None):
    """Validate a completed proof stage even when a later refresh step failed."""
    base = 'snapshot/evidence/'
    needed = {base + name for name in ('models.html', 'meta_models.json', 'sources.json')}
    present = needed & files.keys()
    audit_path = base + 'availability.json'
    # Error codes come from the runner's exception boundary; a failed envelope's
    # operation field is untrusted and may be null, even for a refresh failure.
    late_codes = ({error['code'] for error in envelope['errors']} if
                  envelope['status'] == 'failed' else set())
    if late_codes & _POST_PROOF_REFRESH_ERRORS and (
            needed - files.keys() or
            audit_path not in files and late_codes != {'previous_inventory_missing'}):
        raise PublishError('missing_capability_evidence')
    if present == {base + 'models.html'} and audit_path not in files and source_map is None:
        return  # Fetch completed but semantic parsing may have failed before proof.
    if not present and audit_path not in files:
        if source_map is not None:
            raise PublishError('missing_capability_evidence')
        return
    if (needed - files.keys() or
            audit_path not in files and (source_map is not None or any(
                base + name in files for name in ('leaderboard_records.json', 'missing_candidates.json', 'source_map.json')))):
        raise PublishError('missing_capability_evidence')
    try:
        raw = files[base + 'models.html']
        sources = _json(files[base + 'sources.json'])
        fact = parse_meta_models(raw.decode('utf-8'))
        parsed = _json(files[base + 'meta_models.json'])
        day = parsed['checked_date']
        if (sources['sha256_by_url'][MODELS_URL] != hashlib.sha256(raw).hexdigest()
                or sources['checked_date'] != day or parsed != dict(fact, checked_date=day)
                or envelope['status'] == 'success' and day not in envelope['source_dates']):
            raise ValueError('inconsistent models proof')
        if audit_path not in files:
            return  # Previous-inventory parsing failed after the models proof completed.
        audit = _json(files[audit_path])
        retired = audit['retired_previous_efforts']
        excluded = audit['excluded_current_identities']
        identity = 'Muse Spark 1.3 max Meta Contributor'
        reason = unavailable_reason({'identity': identity})
        retirement = {'identity': identity, 'effort': 'max', 'source_url': MODELS_URL,
                      'checked_date': day, 'reason': reason}
        current_exclusion = {'slug': 'muse-spark-1-3', 'identity': identity,
                             'reason': reason, 'source_url': MODELS_URL, 'checked_date': day}
        if (audit['source_url'] != MODELS_URL or audit['checked_date'] != day
                or retired not in ([], [retirement])
                or excluded not in ([], [current_exclusion])
                or source_map is not None and source_map.get('availability') != audit):
            raise ValueError('invalid capability audit')
        if source_map is not None:
            rows = list(csv.DictReader(io.StringIO(files['snapshot/candidates.csv'].decode())))
            if any(unavailable_reason(row) for row in rows):
                raise ValueError('unavailable candidate in fresh CSV')
            expected = [current_exclusion] if 'muse-spark-1-3' in source_map['source_by_slug'] else []
            if excluded != expected:
                raise ValueError('missing or invented effort exclusion audit')
    except (SourceError, KeyError, ValueError, TypeError, UnicodeError) as exc:
        raise PublishError('invalid_capability_evidence') from exc


def choose_latest(existing: dict | None, incoming: dict, *, refresh_only: bool) -> dict | None:
    """Select a successful result by source date, request time, then commit ID."""
    if incoming['status'] != 'success' or refresh_only and incoming['operation'] != 'refresh':
        return existing
    new_order = _order(incoming)
    if existing is None or new_order > _order(existing):
        return incoming
    return existing


def _git(repo, *args, env=None, check=True):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, env=env)
    if check and result.returncode:
        # Remote URLs and credential-helper diagnostics must not appear in logs.
        raise PublishError('git_operation_failed: ' + args[0])
    return result


def _push(repo, remote, branch, env):
    return _git(repo, 'push', remote, f'HEAD:refs/heads/{branch}', env=env, check=False).returncode == 0


def _output_files(output, *, source_repository=None, trusted_product_sha=None, approved_main_sha=None):
    output = Path(output)
    if not output.is_dir() or not stat.S_ISDIR(output.lstat().st_mode):
        raise PublishError('invalid_output_directory')
    files = {}
    for root, dirs, names in os.walk(output, followlinks=False):
        for name in dirs + names:
            path = Path(root) / name
            mode = path.lstat().st_mode
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise PublishError('unsafe_output_entry')
            relative = path.relative_to(output).as_posix()
            if stat.S_ISDIR(mode) and not any(f.startswith(relative + '/') for f in _FILES):
                raise PublishError('unapproved_output_directory')
            if stat.S_ISREG(mode):
                if relative not in _FILES:
                    raise PublishError('unapproved_output_file')
                files[relative] = path.read_bytes()
    if 'result.json' not in files:
        raise PublishError('missing_result')
    envelope = validate_envelope(_json(files['result.json']))
    if envelope['status'] == 'failed':
        _capability_evidence(files, envelope)
    if 'snapshot/evidence/api_envelopes.json' in files:
        pages = _api_response_bodies(files['snapshot/evidence/api_envelopes.json'])
        if envelope['status'] == 'success':
            if envelope['operation'] != 'refresh' or 'snapshot/evidence/api_diagnostic.json' not in files:
                raise PublishError('unexpected_api_evidence')
            diagnostic = _json(files['snapshot/evidence/api_diagnostic.json'])
            versions = {page['intelligence_index_version'] for page in pages}
            if (type(diagnostic) is not dict or diagnostic.get('status') != 'collected_separately'
                    or diagnostic.get('mixed_into_public_rows') is not False
                    or versions != {diagnostic.get('envelope_version')}
                    or diagnostic.get('public_version') != envelope['benchmark_version']):
                raise PublishError('invalid_api_diagnostic')
    request_id, run_id, attempt = (envelope[k] for k in ('request_id', 'run_id', 'run_attempt'))
    if (type(run_id) is not str or not _RUN.fullmatch(run_id) or run_id in ('.', '..') or
            request_id is not None and (type(request_id) is not str or not _UUID.fullmatch(request_id)) or
            request_id is None and envelope['status'] != 'failed'):
        raise PublishError('invalid_result_path_identity')
    reports = {'report.md', 'report.html'}
    if envelope['status'] == 'success':
        if not reports <= files.keys():
            raise PublishError('missing_success_report')
        try:
            if any(not files[name].decode('utf-8').strip() for name in reports):
                raise PublishError('empty_success_report')
        except UnicodeError as exc:
            raise PublishError('invalid_success_report_encoding') from exc
        if envelope['operation'] == 'refresh':
            mandatory = {'snapshot/candidates.csv', 'snapshot/evidence/source_map.json',
                         'snapshot/evidence/version.json'}
            if not mandatory <= files.keys():
                raise PublishError('missing_refresh_snapshot')
            source = envelope['source_snapshot']
            if source != {'kind': 'acquired', 'path': 'snapshot/candidates.csv',
                          'sha256': hashlib.sha256(files['snapshot/candidates.csv']).hexdigest()}:
                raise PublishError('refresh_hash_mismatch')
            version = _json(files['snapshot/evidence/version.json'])
            source_map = _json(files['snapshot/evidence/source_map.json'])
            if (type(version) is not dict or version.get('benchmark_version') != envelope['benchmark_version']
                    or type(source_map) is not dict or type(source_map.get('inventory')) is not dict):
                raise PublishError('invalid_refresh_evidence')
            if max(envelope['source_dates']) >= '2026-09-27':
                _capability_evidence(files, envelope, source_map)
            elif 'snapshot/evidence/meta_models.json' in files:
                _capability_evidence(files, envelope, source_map)
            try:
                if source_repository is None or type(trusted_product_sha) is not str:
                    raise PublishError('missing_trusted_product_context')
                policy = _refresh_policy(source_repository, trusted_product_sha, approved_main_sha=approved_main_sha)
                if envelope['product_sha'].lower() != trusted_product_sha.lower():
                    raise PublishError('product_context_mismatch')
                previous = _previous(source_repository, trusted_product_sha, approved_main_sha=approved_main_sha)
                expected = tracked_public_slugs(previous, _previous_slugs(previous)[0])
                proof = {name: files['snapshot/evidence/' + name] for name in
                         ('leaderboard.html', 'leaderboard_records.json', 'sources.json')} if policy else None
                validate_fresh_inventory(files['snapshot/candidates.csv'], source_map, envelope,
                                         error_code='invalid_refresh_inventory', refresh_policy=policy,
                                         evidence=proof, expected_previous_slugs=expected if policy else None)
            except (RunnerError, SourceError, InventoryError, KeyError) as exc:
                raise PublishError('invalid_refresh_inventory') from exc
        elif 'snapshot/candidates.csv' in files:
            # Recompute materializes a copy for diagnostics; the source remains pinned Git.
            pass
    elif reports & files.keys():
        raise PublishError('partial_failure_report')
    directory = request_id if request_id is not None else 'invalid-' + envelope['request_commit_sha'].lower()
    return files, envelope, f'results/{directory}/{run_id}-{attempt}'


def _pointer(envelope, target):
    return {key: envelope[key] for key in ('request_id', 'request_commit_sha', 'run_id',
                                            'run_attempt', 'operation', 'status', 'source_dates', 'created_at')} | {
        'result_path': target + '/result.json'}


def _install(repo, files, envelope, target):
    dest = repo / target
    # A pre-existing branch is untrusted: never dereference a symlink from its
    # tree when comparing an attempt or writing pointers/snapshots.
    for parent in (repo / 'results', dest.parent, dest):
        if parent.is_symlink() or parent.exists() and not parent.is_dir():
            raise PublishError('unsafe_existing_result_path')
    if dest.exists():
        old = {}
        for root, dirs, names in os.walk(dest, followlinks=False):
            for name in dirs + names:
                path = Path(root) / name
                mode = path.lstat().st_mode
                if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                    raise PublishError('unsafe_existing_result_path')
                if stat.S_ISREG(mode):
                    old[path.relative_to(dest).as_posix()] = path.read_bytes()
        if old != files:
            raise PublishError('attempt_content_conflict')
        return False
    for name, data in files.items():
        path = dest / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    _git(repo, 'add', '--', target)
    incoming = _pointer(envelope, target)
    for name, refresh_only in (('latest-success.json', False), ('latest-refresh.json', True)):
        path = repo / name
        if path.is_symlink() or path.exists() and not path.is_file():
            raise PublishError('unsafe_existing_pointer')
        existing = _json(path.read_bytes()) if path.exists() else None
        selected = choose_latest(existing, incoming, refresh_only=refresh_only)
        if selected is incoming:
            path.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + '\n')
            _git(repo, 'add', '--', name)
    return True


def _tip(repo, remote, branch, env):
    result = _git(repo, 'ls-remote', '--heads', remote, f'refs/heads/{branch}', env=env)
    lines = result.stdout.decode().splitlines()
    if not lines:
        return None
    if len(lines) != 1 or not re.fullmatch('[0-9a-f]{40}', lines[0].split('\t')[0]):
        raise PublishError('invalid_remote_tip')
    tip = lines[0].split('\t')[0]
    _git(repo, 'fetch', '--no-tags', remote, f'refs/heads/{branch}', env=env)
    if _git(repo, 'rev-parse', 'FETCH_HEAD').stdout.decode().strip() != tip:
        raise PublishError('remote_tip_changed_during_fetch')
    return tip


def publish_result(output: Path, *, remote: str, branch: str = 'results',
                   source_repository: Path | None = None, trusted_product_sha: str | None = None,
                   approved_main_sha: str | None = None) -> str:
    """Return publication SHA; retry contested fast-forward pushes at most three times."""
    files, envelope, target = _output_files(output, source_repository=source_repository,
                                            trusted_product_sha=trusted_product_sha,
                                            approved_main_sha=approved_main_sha)
    if (type(branch) is not str or not _BRANCH.fullmatch(branch) or '..' in branch or
            branch.endswith(('/', '.')) or type(remote) is not str or not remote):
        raise PublishError('invalid_remote_or_branch')
    parts = urlsplit(remote)
    if parts.scheme in ('http', 'https') and (parts.username or parts.password or parts.query or parts.fragment):
        raise PublishError('credentials_in_remote_url')
    with tempfile.TemporaryDirectory(prefix='chat-publish-') as directory:
        env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
        # The helper reads GITHUB_TOKEN from the process environment at invocation
        # time. Neither Git arguments nor the helper file contain its value.
        if env.get('GITHUB_TOKEN'):
            helper = Path(directory) / 'askpass.sh'
            helper.write_text('#!/bin/sh\ncase "$1" in\n  *Username*) printf "%s\\n" x-access-token;;\n  *Password*) printf "%s\\n" "$GITHUB_TOKEN";;\nesac\n')
            helper.chmod(0o700)
            env['GIT_ASKPASS'] = str(helper)
        for attempt in range(3):
            # A fresh isolated checkout also handles contention when two writers
            # race to initialize the previously absent orphan branch.
            repo = Path(directory) / f'checkout-{attempt}'
            repo.mkdir()
            _git(repo, 'init', '-q')
            _git(repo, 'config', 'user.name', 'Chat result publisher')
            _git(repo, 'config', 'user.email', 'chat-results@users.noreply.github.com')
            try:
                tip = _tip(repo, remote, branch, env)
            except PublishError as exc:
                if str(exc) == 'remote_tip_changed_during_fetch':
                    continue
                raise
            if tip:
                _git(repo, 'checkout', '-q', '-B', branch, tip)
            else:
                _git(repo, 'checkout', '-q', '--orphan', branch)
            if not _install(repo, files, envelope, target):
                # A previous identical attempt is already present at an authorized tip.
                return tip
            _git(repo, 'commit', '-qm', 'Append correlated execution result')
            commit = _git(repo, 'rev-parse', 'HEAD').stdout.decode().strip()
            if _push(repo, remote, branch, env):
                return commit
        raise PublishError('concurrent_publication_retry_exhausted')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--remote', required=True)
    parser.add_argument('--branch', default='results')
    parser.add_argument('--source-repository', type=Path)
    parser.add_argument('--product-sha-file', type=Path)
    args = parser.parse_args(argv)
    trusted_sha = None
    approved_main = None
    if args.product_sha_file is not None and args.product_sha_file.exists():
        try:
            trusted_sha = args.product_sha_file.read_text(encoding='ascii').strip()
        except (OSError, UnicodeError) as exc:
            raise PublishError('invalid_product_handoff') from exc
        if not re.fullmatch('[0-9a-fA-F]{40}', trusted_sha):
            raise PublishError('invalid_product_handoff')
    if args.source_repository is None and args.product_sha_file is None:
        envelope = validate_envelope(_json((args.output / 'result.json').read_bytes()))
        if envelope['status'] == 'success' and envelope['operation'] == 'refresh':
            try:
                event = os.environ.get('EVENT_SHA', '')
                args.source_repository, trusted_sha, approved_main = _legacy_workflow_context(
                    Path.cwd(), event_sha=event, ref_name=os.environ.get('EVENT_REF', ''))
                if envelope['request_commit_sha'].lower() != event.lower():
                    raise PublishError('event_result_mismatch')
            except (RunnerError, RequestError, OSError, UnicodeError) as exc:
                raise PublishError('missing_trusted_product_context') from exc
    print(publish_result(args.output, remote=args.remote, branch=args.branch,
                         source_repository=args.source_repository, trusted_product_sha=trusted_sha,
                         approved_main_sha=approved_main))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
