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

from bridge.result import validate_envelope


class PublishError(ValueError):
    """The result is unsafe or cannot be appended without losing another run."""


_UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z')
_RUN = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*\Z')
_BRANCH = re.compile(r'[A-Za-z0-9][A-Za-z0-9._/-]*\Z')
_EVIDENCE = {'leaderboard.html', 'grok_release.html', 'muse_release.html',
             'meta_pricing.html', 'sources.json', 'leaderboard_records.json',
             'releases.json', 'version.json', 'meta_pricing.json',
             'missing_candidates.json', 'source_map.json', 'api_diagnostic.json'}
_FILES = {'result.json', 'report.md', 'report.html', 'snapshot/candidates.csv',
          'snapshot/free-sidecar.json', 'snapshot/run-notes.md'} | {
              'snapshot/evidence/' + name for name in _EVIDENCE}


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


def _output_files(output):
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
    request_id, run_id, attempt = (envelope[k] for k in ('request_id', 'run_id', 'run_attempt'))
    if (type(request_id) is not str or not _UUID.fullmatch(request_id) or
            type(run_id) is not str or not _RUN.fullmatch(run_id) or run_id in ('.', '..')):
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
        elif 'snapshot/candidates.csv' in files:
            # Recompute materializes a copy for diagnostics; the source remains pinned Git.
            pass
    elif reports & files.keys():
        raise PublishError('partial_failure_report')
    return files, envelope, f'results/{request_id}/{run_id}-{attempt}'


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


def publish_result(output: Path, *, remote: str, branch: str = 'results') -> str:
    """Return publication SHA; retry contested fast-forward pushes at most three times."""
    files, envelope, target = _output_files(output)
    if (type(branch) is not str or not _BRANCH.fullmatch(branch) or '..' in branch or
            branch.endswith(('/', '.')) or type(remote) is not str or not remote):
        raise PublishError('invalid_remote_or_branch')
    parts = urlsplit(remote)
    if parts.scheme in ('http', 'https') and (parts.username or parts.password):
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
            tip = _tip(repo, remote, branch, env)
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
    args = parser.parse_args(argv)
    print(publish_result(args.output, remote=args.remote, branch=args.branch))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
