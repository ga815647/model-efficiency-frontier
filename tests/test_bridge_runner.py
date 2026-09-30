import csv
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from bridge.runner import execute_request, materialize_snapshot
from test_bridge_request import request_data

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = 'runs/2026-09-26-general-grok16'
UUID = request_data()['request_id']


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args]).decode().strip()


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.email', 'test@example.com')
        git(self.repo, 'config', 'user.name', 'Test')
        dest = self.repo / ARCHIVE
        dest.mkdir(parents=True)
        for name in ('candidates.csv', 'public_candidate_source_map.json',
                     'public_leaderboard_exact.json', 'meta_pricing_verification.json',
                     'run-notes.md'):
            (dest / name).write_bytes((ROOT / ARCHIVE / name).read_bytes())
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'product')
        self.product = git(self.repo, 'rev-parse', 'HEAD')
        git(self.repo, 'update-ref', 'refs/bridge/approved-main', self.product)
        self.locator = {'commit': self.product, 'path': ARCHIVE + '/candidates.csv'}

    def submit(self, *, params=None, locator=None):
        req = dict(request_data(), product_sha=self.product, operation='recompute',
                   source_snapshot=locator or self.locator)
        if params is not None:
            req['parameters'] = params
        dest = self.repo / 'bridge/requests'
        dest.mkdir(parents=True, exist_ok=True)
        (dest / (UUID + '.json')).write_text(json.dumps(req))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'request')
        execution = dict(request_commit_sha=git(self.repo, 'rev-parse', 'HEAD'), product_sha=self.product,
                         branch='efficiency-run/' + UUID, run_id='123', run_attempt=1,
                         run_url='https://github.com/example/actions/runs/123')
        return req, execution

    def run_request(self, req, execution):
        output = Path(self.tmp.name) / 'output'
        def no_network(_):
            raise AssertionError('recompute must not fetch')
        return execute_request(req, execution=execution, repository=self.repo,
                               output=output, fetch=no_network), output

    def publish_refresh_fixture(self, *, pointer=True, omit_slug=False, schema_version=1):
        # A real results branch containing a successful fresh result and its
        # committed CSV/evidence, without invoking public network fetching.
        git(self.repo, 'branch', 'results')
        git(self.repo, 'checkout', '-q', 'results')
        target = self.repo / f'results/{UUID}/777-1'
        snapshot = target / 'snapshot'
        evidence = snapshot / 'evidence'
        evidence.mkdir(parents=True)
        with (ROOT / ARCHIVE / 'candidates.csv').open(newline='') as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        for row in rows:
            if row['pricing_plan'] != 'Contributor':
                row['model_version'] = row['notes'].split(' slug=', 1)[1].split(';', 1)[0]
            else:
                row['model_version'] = 'muse-spark-1-3' + (('-' + row['effort']) if row['effort'] != 'max' else '') + '@2026-09-02'
        buf = io.StringIO(newline='')
        writer = csv.DictWriter(buf, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        csv_data = buf.getvalue().encode()
        (snapshot / 'candidates.csv').write_bytes(csv_data)
        source_map = json.loads((ROOT / ARCHIVE / 'public_candidate_source_map.json').read_text())
        source_map['contributor'] = [{
            'slug': 'muse-spark-1-3' + (('-' + r['effort']) if r['effort'] != 'max' else ''),
            'effort': r['effort'], 'derived_cost': r['cost_per_task'],
        } for r in rows if r['pricing_plan'] == 'Contributor']
        source_map['inventory'] = {'slugs': sorted(source_map['source_by_slug']),
                                   'contributor_efforts': ['max', 'xhigh']}
        if omit_slug:
            source_map['inventory']['slugs'].pop()
        (evidence / 'source_map.json').write_text(json.dumps(source_map))
        (evidence / 'version.json').write_text(json.dumps({'benchmark_version': 'AA-Intelligence-Index-v4.3.2'}))
        acquired = {'kind': 'acquired', 'path': 'snapshot/candidates.csv',
                    'sha256': hashlib.sha256(csv_data).hexdigest()}
        provenance = {'benchmark': 'AA-Intelligence-Index',
                      'benchmark_version': 'AA-Intelligence-Index-v4.3.2',
                      'version_status': 'inferred', 'cost_basis': 'api',
                      'source_dates': ['2026-09-26'], 'source_locator': acquired,
                      'caveats': ['Public version inferred from release pages',
                                  'Contributor GRADE-B cache-write assumption']}
        params = request_data()['parameters']
        from bridge import result, result_v1
        api = result_v1 if schema_version == 1 else result
        calculation, _ = api.calculate_snapshot(snapshot / 'candidates.csv', params, provenance)
        fresh_req = dict(request_data(), product_sha=self.product)
        fresh_execution = {'request_commit_sha': git(self.repo, 'rev-parse', 'HEAD'),
                           'run_id': '777', 'run_attempt': 1,
                           'run_url': 'https://github.com/example/actions/runs/777'}
        result = api.make_envelope(fresh_req, fresh_execution, calculation=calculation, errors=[])
        (target / 'result.json').write_text(json.dumps(result))
        if pointer:
            (self.repo / 'latest-refresh.json').write_text(json.dumps({
                'result_path': f'results/{UUID}/777-1/result.json',
                'request_commit_sha': fresh_execution['request_commit_sha']}))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'published refresh')
        return result

    def test_approved_historical_adapter_is_pinned_and_html_matches(self):
        req, execution = self.submit()
        # Neither the working tree nor a later commit may change pinned bytes.
        (self.repo / self.locator['path']).write_text('malicious,working,copy\n')
        envelope, output = self.run_request(req, execution)
        self.assertEqual(envelope['status'], 'success')
        self.assertEqual(envelope['source_snapshot'], self.locator)
        self.assertEqual(envelope['candidate_count'], 155)
        self.assertEqual(envelope['benchmark_version'], 'AA-Intelligence-Index-v4.3.2')
        original = (ROOT / self.locator['path']).read_bytes()
        self.assertEqual((output / 'snapshot/candidates.csv').read_bytes(), original)
        self.assertEqual(hashlib.sha256((output / 'snapshot/candidates.csv').read_bytes()).hexdigest(),
                         hashlib.sha256(original).hexdigest())
        self.assertEqual(envelope['schema_version'], 2)
        self.assertEqual(len(envelope['ladder']), 10)
        self.assertIn(envelope['anchors']['highest_retained_score']['identity'],
                      (output / 'report.html').read_text())
        self.assertEqual(json.loads((output / 'result.json').read_text()), envelope)

    def test_policy_uses_only_pinned_main_and_ordinary_product_blob(self):
        from bridge import runner
        marker = self.repo / 'bridge/refresh-policy.json'
        marker.parent.mkdir()
        marker.write_text('{"policy":"observed-inventory-v1"}')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'approved B')
        b = git(self.repo, 'rev-parse', 'HEAD')
        git(self.repo, 'update-ref', 'refs/bridge/approved-main', b)
        git(self.repo, 'checkout', '-q', '--detach', self.product)
        self.assertEqual(runner._refresh_policy(self.repo, b), 'observed-inventory-v1')
        self.assertIsNone(runner._refresh_policy(self.repo, self.product))
        git(self.repo, 'checkout', '-q', '--detach', b)
        marker.unlink()
        self.assertEqual(runner._refresh_policy(self.repo, b), 'observed-inventory-v1')
        marker.write_text('{"policy":"unknown"}')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'unapproved successor')
        x = git(self.repo, 'rev-parse', 'HEAD')
        git(self.repo, 'update-ref', 'refs/remotes/origin/main', x)
        with self.assertRaisesRegex(ValueError, 'source_product_not_authorized'):
            runner._refresh_policy(self.repo, x)
        git(self.repo, 'update-ref', '-d', 'refs/bridge/approved-main')
        with self.assertRaises(ValueError):
            runner._refresh_policy(self.repo, self.product)
        blob = git(self.repo, 'rev-parse', b + ':bridge/refresh-policy.json')
        git(self.repo, 'update-ref', 'refs/bridge/approved-main', blob)
        with self.assertRaises(ValueError):
            runner._refresh_policy(self.repo, self.product)

    def test_invalid_policy_markers_and_unrelated_product_rejected(self):
        from bridge import runner
        for value in ('{"policy":"unknown"}', '{"policy":"observed-inventory-v1","policy":"observed-inventory-v1"}', 'symlink'):
            with self.subTest(value=value):
                marker = self.repo / 'bridge/refresh-policy.json'
                marker.parent.mkdir(exist_ok=True)
                marker.unlink(missing_ok=True)
                if value == 'symlink':
                    marker.symlink_to('../run-notes.md')
                else:
                    marker.write_text(value)
                git(self.repo, 'add', '.')
                git(self.repo, 'commit', '-qm', 'bad marker')
                sha = git(self.repo, 'rev-parse', 'HEAD')
                git(self.repo, 'update-ref', 'refs/bridge/approved-main', sha)
                with self.assertRaises(ValueError):
                    runner._refresh_policy(self.repo, sha)
        git(self.repo, 'checkout', '-q', '--orphan', 'unrelated')
        git(self.repo, 'commit', '-qm', 'unrelated', '--allow-empty')
        with self.assertRaisesRegex(ValueError, 'source_product_not_authorized'):
            runner._refresh_policy(self.repo, git(self.repo, 'rev-parse', 'HEAD'))

    def new_product(self):
        marker = self.repo / 'bridge/refresh-policy.json'
        marker.parent.mkdir(exist_ok=True)
        marker.write_text('{"policy":"observed-inventory-v1"}')
        (self.repo / ARCHIVE / 'public_candidate_source_map.json').write_text(
            json.dumps({'slugs': ['inkling', 'minimax-m2-7']}))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'new product')
        self.product = git(self.repo, 'rev-parse', 'HEAD')
        git(self.repo, 'update-ref', 'refs/bridge/approved-main', self.product)

    def fresh_request(self, params=None):
        req = dict(request_data(), product_sha=self.product)
        if params is not None:
            req['parameters'] = params
        path = self.repo / 'bridge/requests' / (UUID + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(req))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'request')
        execution = dict(request_commit_sha=git(self.repo, 'rev-parse', 'HEAD'), product_sha=self.product,
                         branch='efficiency-run/' + UUID, run_id='new', run_attempt=1,
                         run_url='https://github.com/example/actions/runs/new')
        return req, execution

    def test_new_refresh_previous_and_fixed_recompute_preserve_tracking(self):
        from refresh_inventory_fixtures import refresh_pages
        from bridge.runner import _previous
        self.new_product()
        req, execution = self.fresh_request()
        output = Path(self.tmp.name) / 'new-output'
        envelope = execute_request(req, execution=execution, repository=self.repo, output=output,
                                   fetch=refresh_pages().__getitem__)
        self.assertEqual(envelope['status'], 'success', envelope['errors'])
        git(self.repo, 'checkout', '-q', '-b', 'results')
        target = f'results/{UUID}/new-1'
        import shutil
        shutil.copytree(output, self.repo / target)
        (self.repo / 'latest-refresh.json').write_text(json.dumps(dict(result_path=target + '/result.json',
            request_commit_sha=execution['request_commit_sha'])))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'new refresh publication')
        publication = git(self.repo, 'rev-parse', 'HEAD')
        previous = _previous(self.repo, self.product)
        self.assertIn('inkling', previous['reconciliation']['tracked_slugs'])
        self.assertNotIn('minimax-m2-7', previous['reconciliation']['tracked_slugs'])
        git(self.repo, 'checkout', '-q', '--detach', self.product)
        req, execution = self.submit(locator=dict(commit=publication, path=target + '/snapshot/candidates.csv'))
        result, _ = self.run_request(req, execution)
        self.assertEqual(result['status'], 'success', result['errors'])
        self.assertEqual(result['caveats'], envelope['caveats'])

    def new_snapshot_output(self):
        from refresh_inventory_fixtures import refresh_pages
        self.new_product()
        req, execution = self.fresh_request()
        output = Path(self.tmp.name) / 'new-output'
        envelope = execute_request(req, execution=execution, repository=self.repo, output=output,
                                   fetch=refresh_pages().__getitem__)
        self.assertEqual(envelope['status'], 'success', envelope['errors'])
        return output, envelope

    def install_new_output(self, output, envelope):
        import shutil
        git(self.repo, 'checkout', '-q', '-B', 'results')
        target = f'results/{UUID}/{envelope["run_id"]}-1'
        shutil.copytree(output, self.repo / target)
        (self.repo / 'latest-refresh.json').write_text(json.dumps(dict(result_path=target + '/result.json',
            request_commit_sha=envelope['request_commit_sha'])))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'fixed new refresh')
        return dict(commit=git(self.repo, 'rev-parse', 'HEAD'), path=target + '/snapshot/candidates.csv')

    def test_fixed_source_readers_reject_coherent_predecessor_forgery(self):
        from bridge.runner import _previous
        output, envelope = self.new_snapshot_output()
        path = output / 'snapshot/evidence/source_map.json'
        mapping = json.loads(path.read_text())
        # Independently literal original context; do not derive the expected P
        # from the reconciliation being attacked.
        mapping['previous_inventory'] = dict(product_sha=self.product, results_commit=None, result_path=None)
        self.assertEqual(mapping['reconciliation']['previous_tracked_slugs'], ['inkling', 'minimax-m2-7'])
        mapping['reconciliation']['previous_tracked_slugs'] = []
        mapping['reconciliation']['tracked_slugs'] = sorted(mapping['inventory']['slugs'])
        envelope['caveats'] = [c for c in envelope['caveats'] if not c.startswith('來源退出：')]
        path.write_text(json.dumps(mapping))
        (output / 'result.json').write_text(json.dumps(envelope))
        locator = self.install_new_output(output, envelope)
        for reader in ('previous', 'materialize'):
            with self.subTest(reader=reader), self.assertRaises(ValueError):
                if reader == 'previous':
                    _previous(self.repo, self.product)
                else:
                    materialize_snapshot(locator, self.repo, Path(self.tmp.name) / 'forged')

    def test_fixed_readers_require_exact_predecessor_locator(self):
        from bridge.runner import _previous
        output, envelope = self.new_snapshot_output()
        path = output / 'snapshot/evidence/source_map.json'
        original = json.loads(path.read_text())
        original['previous_inventory'] = dict(product_sha=self.product, results_commit=None, result_path=None)
        locator = self.install_new_output(output, envelope)
        current_map = self.repo / locator['path'].removesuffix('candidates.csv') / 'evidence/source_map.json'
        for change in ('absent', 'product', 'noncommit', 'self', 'unknown_field', 'duplicate'):
            mapping = json.loads(json.dumps(original))
            if change == 'absent':
                del mapping['previous_inventory']
            elif change == 'product':
                mapping['previous_inventory']['product_sha'] = self.locator['commit']
            elif change == 'noncommit':
                mapping['previous_inventory']['results_commit'] = git(self.repo, 'rev-parse', 'HEAD:' + ARCHIVE + '/candidates.csv')
            elif change == 'self':
                mapping['previous_inventory']['results_commit'] = locator['commit']
                mapping['previous_inventory']['result_path'] = locator['path'].removesuffix('snapshot/candidates.csv') + 'result.json'
            elif change == 'unknown_field':
                mapping['previous_inventory']['extra'] = 'not allowed'
            raw = json.dumps(mapping)
            if change == 'duplicate':
                raw = raw.replace('"results_commit": null', '"results_commit": null, "results_commit": null')
            current_map.write_text(raw)
            git(self.repo, 'add', '.')
            git(self.repo, 'commit', '-qm', 'tampered locator ' + change)
            forged = dict(locator, commit=git(self.repo, 'rev-parse', 'HEAD'))
            for reader in ('previous', 'materialize'):
                with self.subTest(change=change, reader=reader), self.assertRaises(ValueError):
                    if reader == 'previous':
                        _previous(self.repo, self.product)
                    else:
                        materialize_snapshot(forged, self.repo, Path(self.tmp.name) / change)

    def test_new_source_cannot_strip_locator_by_claiming_legacy_product(self):
        from bridge.runner import _previous
        output, envelope = self.new_snapshot_output()
        locator = self.install_new_output(output, envelope)
        prefix = locator['path'].removesuffix('snapshot/candidates.csv')
        path = self.repo / prefix / 'snapshot/evidence/source_map.json'
        mapping = json.loads(path.read_text())
        del mapping['reconciliation']
        mapping.pop('previous_inventory', None)
        envelope['product_sha'] = self.locator['commit']  # authorized but not original product
        envelope['caveats'] = [c for c in envelope['caveats'] if not c.startswith('來源退出：')]
        path.write_text(json.dumps(mapping))
        (self.repo / prefix / 'result.json').write_text(json.dumps(envelope))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'forged legacy downgrade')
        forged = dict(locator, commit=git(self.repo, 'rev-parse', 'HEAD'))
        for reader in ('previous', 'materialize'):
            with self.subTest(reader=reader), self.assertRaises(ValueError):
                if reader == 'previous':
                    _previous(self.repo, self.product)
                else:
                    materialize_snapshot(forged, self.repo, Path(self.tmp.name) / 'legacy-forgery')

    def test_new_product_recompute_legacy_source_does_not_require_new_proof(self):
        self.publish_refresh_fixture(schema_version=2)
        locator = dict(commit=git(self.repo, 'rev-parse', 'HEAD'), path=f'results/{UUID}/777-1/snapshot/candidates.csv')
        git(self.repo, 'checkout', '-q', '--detach', self.product)
        self.new_product()
        req, execution = self.submit(locator=locator)
        result, _ = self.run_request(req, execution)
        self.assertEqual(result['status'], 'success', result['errors'])

    def test_floor_cap_empty_ladder_does_not_change_tracking(self):
        from refresh_inventory_fixtures import refresh_pages
        self.new_product()
        params = dict(request_data()['parameters'], min_score=100, min_score_reason='empty ladder boundary')
        req, execution = self.fresh_request(params)
        output = Path(self.tmp.name) / 'empty-ladder'
        result = execute_request(req, execution=execution, repository=self.repo, output=output,
                                 fetch=refresh_pages().__getitem__)
        self.assertEqual(result['status'], 'success', result['errors'])
        self.assertEqual(result['ladder'], [])
        self.assertTrue(all(value is None for value in result['anchors'].values()))
        rec = json.loads((output / 'snapshot/evidence/source_map.json').read_text())['reconciliation']
        self.assertIn('inkling', rec['tracked_slugs'])
        self.assertIn('gpt-6-1-sol', rec['tracked_slugs'])

    def test_empty_paid_and_retired_unknown_effort_boundary(self):
        from refresh_inventory_fixtures import refresh_pages, flight
        from scripts.aa_public import LEADERBOARD, parse_leaderboard
        self.new_product()
        req, execution = self.fresh_request()
        pages = refresh_pages()
        rows = parse_leaderboard(pages[LEADERBOARD].decode())
        for row in rows:
            row['deprecated'] = True
        rows[-1]['name'] = 'Retired (garbage unknown qualifier)'
        pages[LEADERBOARD] = flight(rows)
        output = Path(self.tmp.name) / 'empty-paid'
        result = execute_request(req, execution=execution, repository=self.repo, output=output, fetch=pages.__getitem__)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['errors'][0]['code'], 'empty_paid')
        self.assertFalse((output / 'report.html').exists())

    def test_fixed_commit_rejects_later_conflicting_evidence(self):
        req, execution = self.submit()
        # Alter evidence at the pinned product commit via a new commit (never considered).
        p = self.repo / ARCHIVE / 'public_candidate_source_map.json'
        p.write_text('{}')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'later conflicting evidence')
        result, _ = self.run_request(req, execution)
        self.assertEqual(result['status'], 'success')

    def test_invalid_pinned_evidence_is_rejected_before_calculation(self):
        p = self.repo / ARCHIVE / 'public_candidate_source_map.json'
        p.write_text('{}')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'bad evidence')
        loc = dict(self.locator, commit=git(self.repo, 'rev-parse', 'HEAD'))
        req, execution = self.submit(locator=loc)
        result, output = self.run_request(req, execution)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse((output / 'report.md').exists())
        self.assertFalse((output / 'report.html').exists())

    def test_failed_or_missing_adjacent_results_envelope_rejected(self):
        result_path = f'results/{UUID}/777-1/snapshot/candidates.csv'
        p = self.repo / result_path
        p.parent.mkdir(parents=True)
        p.write_bytes((ROOT / ARCHIVE / 'candidates.csv').read_bytes())
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'results')
        git(self.repo, 'branch', 'results')
        locator = dict(commit=git(self.repo, 'rev-parse', 'HEAD'), path=result_path)
        with self.assertRaises(ValueError):
            materialize_snapshot(locator, self.repo, Path(self.tmp.name) / 'materialized')
        (p.parent.parent / 'result.json').write_text(json.dumps({'status': 'failed'}))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'failed envelope')
        with self.assertRaises(ValueError):
            materialize_snapshot(dict(locator, commit=git(self.repo, 'rev-parse', 'HEAD')),
                                 self.repo, Path(self.tmp.name) / 'materialized')

    def test_invalid_request_still_has_correlated_failure(self):
        req, execution = self.submit(params=dict(request_data()['parameters'], grok_factor=True))
        result, output = self.run_request(req, execution)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['request_id'], UUID)
        self.assertEqual(result['request_commit_sha'], execution['request_commit_sha'])
        self.assertEqual(json.loads((output / 'result.json').read_text()), result)
        self.assertFalse((output / 'report.md').exists())

    def test_nonfinite_parameter_produces_parseable_failed_envelope(self):
        req, execution = self.submit(params=dict(request_data()['parameters'], min_score=float('nan')))
        result, output = self.run_request(req, execution)
        self.assertEqual(result['status'], 'failed')
        self.assertIsNone(json.loads((output / 'result.json').read_text())['parameters']['min_score'])

    def test_refresh_failure_preserves_diagnostics_but_not_ladder(self):
        req = dict(request_data(), product_sha=self.product)
        dest = self.repo / 'bridge/requests'
        dest.mkdir(parents=True)
        (dest / (UUID + '.json')).write_text(json.dumps(req))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'request')
        execution = dict(request_commit_sha=git(self.repo, 'rev-parse', 'HEAD'), product_sha=self.product,
                         branch='efficiency-run/' + UUID, run_id='123', run_attempt=1,
                         run_url='https://github.com/example/actions/runs/123')
        output = Path(self.tmp.name) / 'output'
        def fail(url):
            raise ValueError('source_unavailable: ' + url)
        result = execute_request(req, execution=execution, repository=self.repo,
                                 output=output, fetch=fail)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue((output / 'snapshot/evidence').is_dir())
        self.assertFalse((output / 'snapshot/candidates.csv').exists())
        self.assertFalse((output / 'report.html').exists())

    def test_symlink_source_is_rejected(self):
        p = self.repo / ARCHIVE / 'candidates.csv'
        p.unlink()
        os.symlink('run-notes.md', p)
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'symlink source')
        loc = dict(self.locator, commit=git(self.repo, 'rev-parse', 'HEAD'))
        with self.assertRaisesRegex(ValueError, 'source_not_regular_blob'):
            materialize_snapshot(loc, self.repo, Path(self.tmp.name) / 'materialized')

    def test_additional_diff_is_rejected_with_correlated_failure(self):
        req, execution = self.submit()
        (self.repo / 'extra.txt').write_text('extra')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '--amend', '--no-edit', '-q')
        execution['request_commit_sha'] = git(self.repo, 'rev-parse', 'HEAD')
        result, output = self.run_request(req, execution)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['request_commit_sha'], execution['request_commit_sha'])
        self.assertEqual(json.loads((output / 'result.json').read_text())['errors'][0]['code'],
                         'invalid_changed_paths')

    def test_missing_refresh_pointer_with_published_success_fails_closed(self):
        req, execution = self.submit()
        self.publish_refresh_fixture(pointer=False)
        from bridge.runner import _previous
        with self.assertRaisesRegex(ValueError, 'missing_latest_refresh'):
            _previous(self.repo, self.product)

    def test_recompute_only_results_branch_allows_first_refresh_fallback(self):
        req, execution = self.submit()
        completed, output = self.run_request(req, execution)
        self.assertEqual(completed['status'], 'success')
        git(self.repo, 'branch', 'results')
        git(self.repo, 'checkout', '-q', 'results')
        path = self.repo / f'results/{UUID}/123-1/result.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(completed))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'recompute published first')
        from bridge.runner import _previous
        previous = _previous(self.repo, self.product)
        self.assertEqual(previous['source_by_slug'], json.loads(
            (ROOT / ARCHIVE / 'public_candidate_source_map.json').read_text())['source_by_slug'])

    def test_latest_refresh_missing_one_inventory_slug_fails(self):
        req, execution = self.submit()
        self.publish_refresh_fixture(omit_slug=True)
        from bridge.runner import _previous
        with self.assertRaisesRegex(ValueError, 'invalid_latest_refresh_inventory'):
            _previous(self.repo, self.product)

    def test_valid_latest_refresh_uses_full_pinned_inventory(self):
        req, execution = self.submit()
        self.publish_refresh_fixture()
        from bridge.runner import _previous
        inventory = _previous(self.repo, self.product)
        self.assertEqual(len(inventory['inventory']['slugs']), 153)
        self.assertEqual(inventory['inventory']['contributor_efforts'], ['max', 'xhigh'])

    def test_recompute_rejects_published_refresh_with_incomplete_map(self):
        req, execution = self.submit()
        self.publish_refresh_fixture(omit_slug=True)
        locator = {'commit': git(self.repo, 'rev-parse', 'HEAD'),
                   'path': f'results/{UUID}/777-1/snapshot/candidates.csv'}
        with self.assertRaisesRegex(ValueError, 'result_inventory_mismatch'):
            materialize_snapshot(locator, self.repo, Path(self.tmp.name) / 'materialized')


if __name__ == '__main__':
    unittest.main()
