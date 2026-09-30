import hashlib
import io
from contextlib import redirect_stdout
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bridge.result import calculate_snapshot, make_envelope
from bridge.publish import PublishError, choose_latest, publish_result
from bridge.runner import _previous
from bridge.runner import execute_request
from test_bridge_request import request_data
from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE
from refresh_inventory_fixtures import product_context


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE).decode().strip()


class PublishTests(unittest.TestCase):
    def test_success_refresh_requires_trusted_context(self):
        output, _ = self.valid_refresh_output()
        with self.assertRaisesRegex(PublishError, 'missing_trusted_product_context'):
            publish_result(output, remote=str(self.remote))

    def test_new_inventory_requires_complete_proof_and_handoff_equality(self):
        from refresh_inventory_fixtures import product_context, refresh_pages
        from scripts.refresh_snapshot import refresh_snapshot
        from bridge.publish import _output_files
        previous = {'slugs': ['inkling', 'minimax-m2-7']}
        context = product_context(self.base, previous, new_policy=True)
        output = self.base / 'new-proof'
        output.mkdir()
        provenance = refresh_snapshot(output / 'snapshot', previous=previous, fetch=refresh_pages().__getitem__,
            previous_inventory=dict(product_sha=context[1], results_commit=None, result_path=None))
        calculation, report = calculate_snapshot(output / 'snapshot/candidates.csv', PARAMETERS, provenance)
        req = dict(request_data(), product_sha=context[1])
        execution = dict(request_commit_sha=context[1], run_id='new-proof', run_attempt=1,
                         run_url='https://github.com/example/actions/runs/new-proof')
        envelope = make_envelope(req, execution, calculation=calculation, errors=[])
        (output / 'result.json').write_text(json.dumps(envelope))
        (output / 'report.md').write_text(report)
        (output / 'report.html').write_text('<title>Report</title>')
        kwargs = dict(source_repository=context[0], trusted_product_sha=context[1])
        _output_files(output, **kwargs)
        for name in ('leaderboard.html', 'leaderboard_records.json', 'sources.json'):
            path = output / 'snapshot/evidence' / name
            saved = path.read_bytes()
            path.unlink()
            with self.subTest(name=name), self.assertRaises(PublishError):
                _output_files(output, **kwargs)
            path.write_bytes(saved)
        for name in ('leaderboard.html', 'leaderboard_records.json', 'sources.json'):
            path = output / 'snapshot/evidence' / name
            saved = path.read_bytes()
            if name == 'leaderboard.html':
                path.write_bytes(saved.replace(b'51.8332597011541', b'51.8332597011542'))
            else:
                parsed = json.loads(saved)
                if name == 'leaderboard_records.json':
                    parsed[0]['deprecated'] = True
                else:
                    from scripts.aa_public import LEADERBOARD
                    parsed['sha256_by_url'][LEADERBOARD] = '0' * 64
                path.write_text(json.dumps(parsed))
            with self.subTest(tampered=name), self.assertRaises(PublishError):
                _output_files(output, **kwargs)
            path.write_bytes(saved)
        path = output / 'snapshot/evidence/source_map.json'
        saved = path.read_bytes()
        mapping = json.loads(saved)
        del mapping['reconciliation']
        path.write_text(json.dumps(mapping))
        with self.assertRaises(PublishError):
            _output_files(output, **kwargs)
        path.write_bytes(saved)
        for change in ('absent', 'different_fixed_context'):
            mapping = json.loads(saved)
            if change == 'absent':
                del mapping['previous_inventory']
            else:
                mapping['previous_inventory']['results_commit'] = context[1]
            path.write_text(json.dumps(mapping))
            with self.subTest(locator=change), self.assertRaisesRegex(PublishError, 'previous_inventory_context_mismatch'):
                _output_files(output, **kwargs)
        path.write_bytes(saved)
        envelope['product_sha'] = 'a' * 40
        (output / 'result.json').write_text(json.dumps(envelope))
        with self.assertRaisesRegex(PublishError, 'product_context_mismatch'):
            _output_files(output, **kwargs)

    def test_frozen_concurrent_contexts_and_new_chain_reject_locator_rollback(self):
        from refresh_inventory_fixtures import refresh_pages, flight, record, GPT_ENTRIES
        from scripts.aa_public import LEADERBOARD, parse_leaderboard
        from scripts.refresh_inventory import build_reconciliation, source_exit_caveats
        from bridge.runner import materialize_snapshot
        repo, product = product_context(self.base, {'slugs': ['inkling', 'minimax-m2-7']}, new_policy=True)
        request = dict(request_data(), product_sha=product)
        request_path = repo / 'bridge/requests' / (request['request_id'] + '.json')
        request_path.parent.mkdir(parents=True)
        request_path.write_text(json.dumps(request))
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'verified refresh request')
        event = git(repo, 'rev-parse', 'HEAD')
        pages = refresh_pages()
        records = parse_leaderboard(pages[LEADERBOARD].decode())
        records.append(record('newly-tracked', name='Newly Tracked', score='40', cost='1'))
        pages[LEADERBOARD] = flight(records)
        outputs = []
        for run in ('concurrent-A', 'concurrent-B'):
            execution = dict(request_commit_sha=event, product_sha=product,
                branch='efficiency-run/' + request['request_id'], run_id=run, run_attempt=1,
                run_url='https://github.com/example/actions/runs/' + run)
            output = self.base / run
            envelope = execute_request(request, execution=execution, repository=repo,
                                       output=output, fetch=pages.__getitem__)
            self.assertEqual(envelope['status'], 'success', envelope['errors'])
            mapping = json.loads((output / 'snapshot/evidence/source_map.json').read_text())
            self.assertEqual(mapping['previous_inventory'],
                             dict(product_sha=product, results_commit=None, result_path=None))
            outputs.append(output)
        first = publish_result(outputs[0], remote=str(self.remote), source_repository=repo, trusted_product_sha=product)
        second = publish_result(outputs[1], remote=str(self.remote), source_repository=repo, trusted_product_sha=product)
        self.assertEqual(git(self.remote, 'rev-parse', second + '^'), first)
        # Both contexts froze no results before acquisition. B's append parent
        # now contains A; that must not replace B's original predecessor.
        git(repo, 'fetch', '-q', str(self.remote), 'refs/heads/results:refs/heads/results')
        target_b = f'results/{request["request_id"]}/concurrent-B-1'
        materialize_snapshot(dict(commit=second, path=target_b + '/snapshot/candidates.csv'), repo, self.base / 'B-read')
        git(repo, 'checkout', '-q', '--detach', product)
        request['created_at'] = '2026-09-30T13:00:00+00:00'
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(json.dumps(request))
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'new-chain request')
        next(r for r in records if r['slug'] == 'newly-tracked')['cost_per_task'] = None
        pages[LEADERBOARD] = flight(records)
        execution.update(request_commit_sha=git(repo, 'rev-parse', 'HEAD'), run_id='chain-C',
                         run_url='https://github.com/example/actions/runs/chain-C')
        output = self.base / 'chain-C'
        envelope = execute_request(request, execution=execution, repository=repo, output=output, fetch=pages.__getitem__)
        self.assertEqual(envelope['status'], 'success', envelope['errors'])
        mapping = json.loads((output / 'snapshot/evidence/source_map.json').read_text())
        expected = sorted([entry[0] for entry in GPT_ENTRIES] + [
            'grok-4-7-high', 'grok-4-7', 'muse-spark-1-3-xhigh', 'muse-spark-1-3', 'inkling', 'newly-tracked'])
        self.assertEqual(mapping['reconciliation']['previous_tracked_slugs'], expected)
        self.assertEqual(mapping['previous_inventory']['results_commit'], second)
        self.assertEqual(mapping['previous_inventory']['result_path'],
                         f'results/{request["request_id"]}/concurrent-A-1/result.json')
        third = publish_result(output, remote=str(self.remote), source_repository=repo, trusted_product_sha=product)
        git(repo, 'fetch', '-q', str(self.remote), '+refs/heads/results:refs/heads/results')
        self.assertIn('newly-tracked', _previous(repo, product)['reconciliation']['tracked_slugs'])
        target = f'results/{request["request_id"]}/chain-C-1'
        materialize_snapshot(dict(commit=third, path=target + '/snapshot/candidates.csv'), repo, self.base / 'C-read')
        # A coherent rollback to a different *valid* archive locator must not
        # erase the independently tracked identity introduced by the new chain.
        git(repo, 'checkout', '-q', 'results')
        mapping['previous_inventory'] = dict(product_sha=product, results_commit=None, result_path=None)
        mapping['reconciliation'] = build_reconciliation(records, {'inkling', 'minimax-m2-7'})
        envelope['caveats'] = [c for c in envelope['caveats'] if not c.startswith('來源退出：')] + source_exit_caveats(records, mapping['reconciliation'])
        (repo / target / 'snapshot/evidence/source_map.json').write_text(json.dumps(mapping))
        (repo / target / 'result.json').write_text(json.dumps(envelope))
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'coherent locator rollback')
        forged = git(repo, 'rev-parse', 'HEAD')
        for reader in ('previous', 'materialize'):
            with self.subTest(reader=reader), self.assertRaises(ValueError):
                if reader == 'previous':
                    _previous(repo, product)
                else:
                    materialize_snapshot(dict(commit=forged, path=target + '/snapshot/candidates.csv'),
                                         repo, self.base / 'rollback-read')
        # Path-limited Git history must not let a merge hide the original
        # introduction behind a second, coherently forged introduction.
        import shutil
        git(repo, 'checkout', '-q', '-b', 'forged-sibling', second)
        shutil.copytree(output, repo / target)
        (repo / target / 'snapshot/evidence/source_map.json').write_text(json.dumps(mapping))
        (repo / target / 'result.json').write_text(json.dumps(envelope))
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'second conflicting introduction')
        git(repo, 'checkout', '-q', '-B', 'results', third)
        git(repo, 'merge', '-q', '--no-ff', '--no-edit', '-X', 'theirs', 'forged-sibling')
        merged = git(repo, 'rev-parse', 'HEAD')
        for reader in ('previous', 'materialize'):
            with self.subTest(merge_reader=reader), self.assertRaises(ValueError):
                if reader == 'previous':
                    _previous(repo, product)
                else:
                    materialize_snapshot(dict(commit=merged, path=target + '/snapshot/candidates.csv'),
                                         repo, self.base / 'merge-forgery-read')

    def test_queued_legacy_publication_validates_newer_original_product(self):
        from refresh_inventory_fixtures import refresh_pages
        from scripts.refresh_snapshot import refresh_snapshot
        import shutil
        from bridge.runner import materialize_snapshot
        from bridge.publish import _output_files
        output, harness = self.valid_refresh_output()
        repo, a = harness.repo, harness.product
        git(repo, 'checkout', '-q', '--detach', a)
        marker = repo / 'bridge/refresh-policy.json'
        marker.parent.mkdir(exist_ok=True)
        marker.write_text('{"policy":"observed-inventory-v1"}')
        (repo / 'runs/2026-09-26-general-grok16/public_candidate_source_map.json').write_text(
            json.dumps({'slugs': ['inkling', 'minimax-m2-7']}))
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'approved newer B')
        b = git(repo, 'rev-parse', 'HEAD')
        git(repo, 'update-ref', 'refs/bridge/approved-main', b)
        # The released old workflow checks out newer main as bootstrap, verifies
        # authenticated transport, and uses the original no-new-flags CLI.
        bootstrap = self.base / 'bootstrap'
        git(self.base, 'clone', '-q', str(repo), str(bootstrap))
        git(bootstrap, 'checkout', '-q', '--detach', b)
        git(bootstrap, 'config', 'user.name', 'Fixture')
        git(bootstrap, 'config', 'user.email', 'fixture@example.com')
        git(bootstrap, 'checkout', '-q', '--detach', a)
        request = dict(request_data(), product_sha=a)
        request_path = bootstrap / 'bridge/requests' / (request['request_id'] + '.json')
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(json.dumps(request))
        git(bootstrap, 'add', '.')
        git(bootstrap, 'commit', '-qm', 'authenticated queued A request')
        event = git(bootstrap, 'rev-parse', 'HEAD')
        git(bootstrap, 'checkout', '-q', '--detach', b)
        from bridge.runner import verify_transport
        handoff = self.base / 'handoff/product.sha'
        self.assertTrue(verify_transport(bootstrap, event_sha=event,
            ref_name='efficiency-run/' + request['request_id'], run_id='777', run_attempt=1,
            output=self.base / 'prepare-output', product_sha_file=handoff))
        result_path = output / 'result.json'
        legacy_envelope = json.loads(result_path.read_text())
        legacy_envelope['request_commit_sha'] = event
        result_path.write_text(json.dumps(legacy_envelope))
        # B itself passes actual five-source acquisition/publication validation,
        # not merely an inventory-unit fixture masquerading as a publication.
        git(repo, 'branch', '-D', 'results')
        fresh_request = dict(request_data(), product_sha=b)
        path = repo / 'bridge/requests' / (fresh_request['request_id'] + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(fresh_request))
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'B refresh request')
        fresh_execution = dict(request_commit_sha=git(repo, 'rev-parse', 'HEAD'), run_id='B-fresh', run_attempt=1,
                               run_url='https://github.com/example/actions/runs/B-fresh')
        fresh = self.base / 'B-output'
        fresh.mkdir()
        prov = refresh_snapshot(fresh / 'snapshot', previous={'slugs': ['inkling', 'minimax-m2-7']},
                                fetch=refresh_pages().__getitem__,
                                previous_inventory=dict(product_sha=b, results_commit=None, result_path=None))
        calculation, report = calculate_snapshot(fresh / 'snapshot/candidates.csv', PARAMETERS, prov)
        envelope = make_envelope(fresh_request, fresh_execution, calculation=calculation, errors=[])
        (fresh / 'result.json').write_text(json.dumps(envelope))
        (fresh / 'report.md').write_text(report)
        (fresh / 'report.html').write_text('<title>B fresh</title>')
        _output_files(fresh, source_repository=repo, trusted_product_sha=b)
        data = (fresh / 'snapshot/candidates.csv').read_bytes()
        mapping = json.loads((fresh / 'snapshot/evidence/source_map.json').read_text())
        target = f'results/{envelope["request_id"]}/{envelope["run_id"]}-1'
        git(repo, 'checkout', '-q', '-B', 'results', b)
        dest = repo / target
        shutil.copytree(fresh, dest)
        (repo / 'latest-refresh.json').write_text(json.dumps(dict(result_path=target + '/result.json',
            request_commit_sha=envelope['request_commit_sha'])))
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'fixed B refresh predecessor')
        publication = git(repo, 'rev-parse', 'HEAD')
        git(repo, 'checkout', '-q', '--detach', a)
        self.assertEqual(_previous(repo, a)['reconciliation'], json.loads(json.dumps(mapping['reconciliation'])))
        locator = dict(commit=publication, path=target + '/snapshot/candidates.csv')
        path, provenance = materialize_snapshot(locator, repo, self.base / 'B-materialized')
        self.assertEqual(path.read_bytes(), data)
        self.assertTrue(any('未沿用舊價' in caveat for caveat in provenance['caveats']))
        # Handoff remains A; B is authorized only as the original predecessor product.
        tip = publish_result(output, remote=str(self.remote), source_repository=repo, trusted_product_sha=a)
        self.assertEqual(json.loads(git(self.remote, 'show', tip + ':' + f'results/{request_data()["request_id"]}/777-1/result.json'))['product_sha'], a)
        git(repo, 'checkout', '-q', 'results')
        (repo / target / 'snapshot/evidence/leaderboard.html').unlink()
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'missing new proof')
        git(repo, 'checkout', '-q', '--detach', a)
        with self.assertRaises(PublishError):
            _output_files(output, source_repository=repo, trusted_product_sha=a)
        # Restore complete B proof; old product checkout has no new authority ref.
        git(repo, 'update-ref', 'refs/heads/results', publication)
        git(repo, 'update-ref', '-d', 'refs/bridge/approved-main')
        product = self.base / 'product'
        repo.rename(product)
        from bridge.publish import main
        import os
        old_cwd = Path.cwd()
        try:
            os.chdir(bootstrap)
            env = dict(EVENT_SHA=event, EVENT_REF='efficiency-run/' + request['request_id'])
            with patch.dict('os.environ', env):
                with redirect_stdout(io.StringIO()) as stdout:
                    self.assertEqual(main(['--output', str(output), '--remote', str(self.remote)]), 0)
                self.assertEqual(stdout.getvalue(), tip + '\n')
                legacy_envelope['request_commit_sha'] = a
                result_path.write_text(json.dumps(legacy_envelope))
                with self.assertRaisesRegex(PublishError, 'event_result_mismatch'):
                    main(['--output', str(output), '--remote', str(self.remote)])
                legacy_envelope['request_commit_sha'] = event
                result_path.write_text(json.dumps(legacy_envelope))
                # Neither an envelope SHA nor intact files replace verified transport.
                with patch.dict('os.environ', {'EVENT_SHA': '0' * 40}):
                    with self.assertRaises(PublishError):
                        main(['--output', str(output), '--remote', str(self.remote)])
                with patch.dict('os.environ', {'EVENT_REF': 'efficiency-run/not-a-uuid'}):
                    with self.assertRaises(PublishError):
                        main(['--output', str(output), '--remote', str(self.remote)])
                request_handoff = self.base / 'handoff/request.json'
                saved_request = request_handoff.read_bytes()
                request_handoff.unlink()
                with self.assertRaises(PublishError):
                    main(['--output', str(output), '--remote', str(self.remote)])
                request_handoff.write_bytes(saved_request)
                handoff.write_text('0' * 40)
                with self.assertRaises(PublishError):
                    main(['--output', str(output), '--remote', str(self.remote)])
        finally:
            os.chdir(old_cwd)

    def test_old_cli_cannot_downgrade_verified_new_product(self):
        from bridge.runner import verify_transport
        from bridge.publish import main
        import os
        bootstrap, b = product_context(self.base, {'slugs': []}, new_policy=True)
        product = self.base / 'product'
        git(self.base, 'clone', '-q', str(bootstrap), str(product))
        request = dict(request_data(), product_sha=b)
        path = bootstrap / 'bridge/requests' / (request['request_id'] + '.json')
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(request))
        git(bootstrap, 'add', '.')
        git(bootstrap, 'commit', '-qm', 'verified new request')
        event = git(bootstrap, 'rev-parse', 'HEAD')
        git(bootstrap, 'checkout', '-q', '--detach', b)
        self.assertTrue(verify_transport(bootstrap, event_sha=event,
            ref_name='efficiency-run/' + request['request_id'], run_id='777', run_attempt=1,
            output=self.base / 'prepare', product_sha_file=self.base / 'handoff/product.sha'))
        output, _ = self.valid_refresh_output()
        envelope = json.loads((output / 'result.json').read_text())
        envelope.update(product_sha=b, request_commit_sha=event)
        (output / 'result.json').write_text(json.dumps(envelope))
        old_cwd = Path.cwd()
        try:
            os.chdir(bootstrap)
            with patch.dict('os.environ', dict(EVENT_SHA=event, EVENT_REF='efficiency-run/' + request['request_id'])):
                with self.assertRaisesRegex(PublishError, 'missing_trusted_product_context'):
                    main(['--output', str(output), '--remote', str(self.remote)])
        finally:
            os.chdir(old_cwd)

    def test_publication_cli_validates_ascii_handoff_and_early_failure(self):
        from bridge.publish import main
        output, _ = self.output(status='failed')
        missing = self.base / 'missing.sha'
        argv = ['--output', str(output), '--remote', str(self.remote),
                '--source-repository', str(self.base / 'missing-product'), '--product-sha-file', str(missing)]
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(main(argv), 0)
        self.assertEqual(stdout.getvalue(), git(self.remote, 'rev-parse', 'refs/heads/results') + '\n')
        for raw in (b'not-a-sha', b'\xff', b'a' * 39):
            missing.write_bytes(raw)
            with self.subTest(raw=raw), self.assertRaisesRegex(PublishError, 'invalid_product_handoff'):
                main(argv)

    def test_present_unusable_failure_still_requires_complete_models_proof(self):
        from refresh_inventory_fixtures import refresh_pages, flight
        from scripts.refresh_snapshot import refresh_snapshot
        from scripts.aa_public import SourceError, LEADERBOARD, parse_leaderboard
        pages = refresh_pages()
        records = parse_leaderboard(pages[LEADERBOARD].decode())
        next(r for r in records if r['slug'] == 'inkling')['is_estimated'] = True
        pages[LEADERBOARD] = flight(records)
        output = self.base / 'unusable-failure'
        output.mkdir()
        with self.assertRaises(SourceError) as caught:
            refresh_snapshot(output / 'snapshot', previous={'slugs': ['inkling']}, fetch=pages.__getitem__)
        self.assertEqual(caught.exception.code, 'present_candidate_unusable')
        execution = dict(request_commit_sha='b' * 40, run_id='unusable', run_attempt=1,
                         run_url='https://github.com/example/actions/runs/unusable')
        (output / 'result.json').write_text(json.dumps(make_envelope(request_data(), execution,
            calculation=None, errors=[dict(code=caught.exception.code, message=str(caught.exception))])))
        # Valid late diagnostic is appendable, including its new artifact.
        tip = publish_result(output, remote=str(self.remote))
        self.assertIn('unusable_candidates.json', git(self.remote, 'ls-tree', '-r', '--name-only', tip))
        (output / 'snapshot/evidence/models.html').unlink()
        with self.assertRaisesRegex(PublishError, 'missing_capability_evidence'):
            publish_result(output, remote=str(self.remote))


    def test_late_missing_candidate_cannot_publish_without_proof_or_with_unparsed_models(self, make_api=make_envelope):
        from test_refresh_sources import FIX, URLS
        from scripts.refresh_snapshot import refresh_snapshot
        from scripts.aa_public import SourceError
        pages = {URLS[name]: (FIX / name).with_suffix('.html').read_bytes() for name in URLS}
        before = pages[URLS['leader']]
        pages[URLS['leader']] = before.replace(b'intelligenceIndexCostPerTask\\":0.4637245706928438',
                                               b'intelligenceIndexCostPerTask\\":\\"$undefined\\"', 1)
        self.assertNotEqual(before, pages[URLS['leader']])
        previous = json.loads((Path(__file__).resolve().parents[1] /
                              'runs/2026-09-26-general-grok16/public_candidate_source_map.json').read_text())
        previous['source_by_slug']['actually-missing'] = {}
        for removed in ('all_proof', 'leave_unparsed_models', 'untrusted_operation'):
            with self.subTest(removed=removed):
                output = self.base / ('late-' + removed)
                output.mkdir()
                with self.assertRaises(SourceError) as caught:
                    refresh_snapshot(output / 'snapshot', previous=previous, fetch=pages.__getitem__)
                self.assertEqual(caught.exception.code, 'missing_candidate')
                req = dict(request_data(), operation='refresh')
                execution = {'request_commit_sha': 'b' * 40, 'run_id': '804', 'run_attempt': 1,
                             'run_url': 'https://github.com/example/actions/runs/804'}
                result = make_api(
                    req, execution, calculation=None,
                    errors=[{'code': caught.exception.code, 'message': str(caught.exception)}])
                if removed == 'untrusted_operation':
                    result['operation'] = None
                (output / 'result.json').write_text(json.dumps(result))
                evidence = output / 'snapshot/evidence'
                for name in ('models.html', 'meta_models.json', 'sources.json', 'availability.json'):
                    (evidence / name).unlink()
                if removed == 'leave_unparsed_models':
                    (evidence / 'models.html').write_text('<li>fake, no parsed proof</li>')
                with self.assertRaisesRegex(PublishError, 'missing_capability_evidence'):
                    publish_result(output, remote=str(self.remote))
        self.assertNotEqual(subprocess.run(['git', '-C', str(self.remote), 'rev-parse', '--verify',
                                            'refs/heads/results'], capture_output=True).returncode, 0)

    def test_preproof_models_parse_failure_remains_publishable_as_failure(self, make_api=make_envelope):
        from test_refresh_sources import FIX, URLS
        from scripts.refresh_snapshot import refresh_snapshot
        from scripts.aa_public import SourceError
        pages = {URLS[name]: (FIX / name).with_suffix('.html').read_bytes() for name in URLS}
        pages[URLS['models']] = pages[URLS['models']].replace(b'available on Standard tier only',
                                                             b'available on all tiers')
        output = self.base / 'preproof-parse-failure'
        output.mkdir()
        with self.assertRaises(SourceError) as caught:
            refresh_snapshot(output / 'snapshot', previous=None, fetch=pages.__getitem__)
        self.assertEqual(caught.exception.code, 'model_capability_drift')
        req = dict(request_data(), operation='refresh')
        execution = {'request_commit_sha': 'b' * 40, 'run_id': '805', 'run_attempt': 1,
                     'run_url': 'https://github.com/example/actions/runs/805'}
        (output / 'result.json').write_text(json.dumps(make_api(req, execution, calculation=None,
            errors=[{'code': caught.exception.code, 'message': str(caught.exception)}])))
        self.assertTrue((output / 'snapshot/evidence/models.html').exists())
        self.assertFalse((output / 'snapshot/evidence/meta_models.json').exists())
        tip = publish_result(output, remote=str(self.remote))
        self.assertEqual(json.loads(git(self.remote, 'show',
            f'{tip}:results/{req["request_id"]}/805-1/result.json'))['status'], 'failed')

    def test_preproof_models_fetch_failure_remains_publishable_as_failure(self, make_api=make_envelope):
        from test_refresh_sources import FIX, URLS
        from scripts.refresh_snapshot import refresh_snapshot
        from scripts.aa_public import SourceError
        pages = {URLS[name]: (FIX / name).with_suffix('.html').read_bytes() for name in URLS}
        output = self.base / 'preproof-fetch-failure'
        output.mkdir()

        def fetch(url):
            if url == URLS['models']:
                raise SourceError('fetch_failed', url)
            return pages[url]

        with self.assertRaises(SourceError) as caught:
            refresh_snapshot(output / 'snapshot', previous=None, fetch=fetch)
        self.assertEqual(caught.exception.code, 'fetch_failed')
        req = dict(request_data(), operation='refresh')
        execution = {'request_commit_sha': 'b' * 40, 'run_id': '803', 'run_attempt': 1,
                     'run_url': 'https://github.com/example/actions/runs/803'}
        (output / 'result.json').write_text(json.dumps(make_api(req, execution, calculation=None,
            errors=[{'code': caught.exception.code, 'message': str(caught.exception)}])))
        self.assertFalse((output / 'snapshot/evidence/models.html').exists())
        tip = publish_result(output, remote=str(self.remote))
        self.assertEqual(json.loads(git(self.remote, 'show',
            f'{tip}:results/{req["request_id"]}/803-1/result.json'))['status'], 'failed')

    def test_failed_refresh_capability_evidence_cannot_be_forged_or_partial(self):
        from test_refresh_sources import FIX, URLS
        from scripts.refresh_snapshot import refresh_snapshot
        from scripts.aa_public import SourceError
        pages = {URLS[name]: (FIX / name).with_suffix('.html').read_bytes() for name in URLS}
        before = pages[URLS['leader']]
        pages[URLS['leader']] = before.replace(b'intelligenceIndexCostPerTask\\":0.4637245706928438',
                                               b'intelligenceIndexCostPerTask\\":\\"$undefined\\"', 1)
        self.assertNotEqual(before, pages[URLS['leader']])
        previous = json.loads((Path(__file__).resolve().parents[1] /
                              'runs/2026-09-26-general-grok16/public_candidate_source_map.json').read_text())
        previous['source_by_slug']['actually-missing'] = {}
        for tamper in ('models', 'hash', 'audit_identity', 'partial', 'missing_audit'):
            with self.subTest(tamper=tamper):
                output = self.base / ('failed-proof-' + tamper)
                output.mkdir()
                with self.assertRaises(SourceError) as caught:
                    refresh_snapshot(output / 'snapshot', previous=previous, fetch=pages.__getitem__)
                self.assertEqual(caught.exception.code, 'missing_candidate')
                req = dict(request_data(), operation='refresh')
                execution = {'request_commit_sha': 'b' * 40, 'run_id': '801', 'run_attempt': 1,
                             'run_url': 'https://github.com/example/actions/runs/801'}
                (output / 'result.json').write_text(json.dumps(make_envelope(
                    req, execution, calculation=None,
                    errors=[{'code': caught.exception.code, 'message': str(caught.exception)}])))
                evidence = output / 'snapshot/evidence'
                if tamper == 'models':
                    (evidence / 'models.html').write_text('<li>fabricated</li>')
                elif tamper == 'hash':
                    sources = json.loads((evidence / 'sources.json').read_text())
                    sources['sha256_by_url'][URLS['models']] = '0' * 64
                    (evidence / 'sources.json').write_text(json.dumps(sources))
                elif tamper == 'partial':
                    (evidence / 'meta_models.json').unlink()
                elif tamper == 'missing_audit':
                    (evidence / 'availability.json').unlink()
                else:
                    audit = json.loads((evidence / 'availability.json').read_text())
                    audit['retired_previous_efforts'][0].update(identity='Grok 4.7 max Meta Contributor',
                                                                  model='Muse Spark 1.3')
                    (evidence / 'availability.json').write_text(json.dumps(audit))
                with self.assertRaises(PublishError):
                    publish_result(output, remote=str(self.remote))
        self.assertNotEqual(subprocess.run(['git', '-C', str(self.remote), 'rev-parse', '--verify',
                                            'refs/heads/results'], capture_output=True).returncode, 0)

    def test_success_retirement_audit_rejects_conflicting_identity_even_if_map_matches(self):
        from test_refresh_sources import FIX, URLS
        from scripts.refresh_snapshot import refresh_snapshot
        pages = {URLS[name]: (FIX / name).with_suffix('.html').read_bytes() for name in URLS}
        previous = json.loads((Path(__file__).resolve().parents[1] /
                              'runs/2026-09-26-general-grok16/public_candidate_source_map.json').read_text())
        output = self.base / 'forged-success-retirement'
        output.mkdir()
        context = product_context(self.base, previous, new_policy=True)
        provenance = refresh_snapshot(output / 'snapshot', previous=previous, fetch=pages.__getitem__)
        calculation, _ = calculate_snapshot(output / 'snapshot/candidates.csv', PARAMETERS, provenance)
        req = dict(request_data(), operation='refresh', product_sha=context[1])
        execution = {'request_commit_sha': 'b' * 40, 'run_id': '802', 'run_attempt': 1,
                     'run_url': 'https://github.com/example/actions/runs/802'}
        (output / 'result.json').write_text(json.dumps(make_envelope(req, execution, calculation=calculation, errors=[])))
        (output / 'report.md').write_text('# Report')
        (output / 'report.html').write_text('<!doctype html><title>Report</title>')
        evidence = output / 'snapshot/evidence'
        audit = json.loads((evidence / 'availability.json').read_text())
        audit['retired_previous_efforts'][0].update(identity='Grok 4.7 max Meta Contributor',
                                                      model='Muse Spark 1.3')
        (evidence / 'availability.json').write_text(json.dumps(audit))
        mapping = json.loads((evidence / 'source_map.json').read_text())
        mapping['availability'] = audit
        (evidence / 'source_map.json').write_text(json.dumps(mapping))
        with self.assertRaises(PublishError):
            publish_result(output, remote=str(self.remote), source_repository=context[0], trusted_product_sha=context[1])

    def test_actual_five_source_refresh_and_failed_missing_cost_are_publishable(self):
        from test_refresh_sources import FIX, URLS
        from scripts.refresh_snapshot import refresh_snapshot
        from scripts.aa_public import SourceError
        pages = {URLS[name]: (FIX / name).with_suffix('.html').read_bytes() for name in URLS}
        previous = json.loads((Path(__file__).resolve().parents[1] /
                              'runs/2026-09-26-general-grok16/public_candidate_source_map.json').read_text())
        for run, missing in (('601', False), ('602', True)):
            with self.subTest(run=run):
                output = self.base / ('actual-' + run)
                output.mkdir()
                source = dict(pages)
                if missing:
                    before = source[URLS['leader']]
                    source[URLS['leader']] = before.replace(b'intelligenceIndexCostPerTask\\":0.4637245706928438',
                                                          b'intelligenceIndexCostPerTask\\":\\"$undefined\\"', 1)
                    self.assertNotEqual(source[URLS['leader']], before)
                req = dict(request_data(), operation='refresh')
                context_base = self.base / ('context-' + run)
                context_base.mkdir()
                context = product_context(context_base, previous, new_policy=True)
                req['product_sha'] = context[1]
                execution = {'request_commit_sha': 'b' * 40, 'run_id': run, 'run_attempt': 1,
                             'run_url': 'https://github.com/example/actions/runs/' + run}
                if missing:
                    previous = dict(previous, source_by_slug=dict(previous['source_by_slug'], **{'actually-missing': {}}))
                    with self.assertRaises(SourceError) as caught:
                        refresh_snapshot(output / 'snapshot', previous=previous, fetch=source.__getitem__)
                    self.assertEqual(caught.exception.code, 'missing_candidate')
                    result = make_envelope(req, execution, calculation=None,
                                           errors=[{'code': caught.exception.code, 'message': str(caught.exception)}])
                else:
                    provenance = refresh_snapshot(output / 'snapshot', previous=previous, fetch=source.__getitem__,
                        previous_inventory=dict(product_sha=context[1], results_commit=None, result_path=None))
                    calculation, report = calculate_snapshot(output / 'snapshot/candidates.csv', PARAMETERS, provenance)
                    from scripts.aa_public import parse_leaderboard
                    from scripts.refresh_inventory import classify_record
                    count = sum(classify_record(r)['state'] == 'usable_paid'
                                for r in parse_leaderboard(source[URLS['leader']].decode())) + 1
                    self.assertEqual(calculation['candidate_count'], count)
                    self.assertEqual(len(calculation['candidate_statuses']), count)
                    result = make_envelope(req, execution, calculation=calculation, errors=[])
                    (output / 'report.md').write_text(report)
                    (output / 'report.html').write_text('<!doctype html><title>Report</title>')
                (output / 'result.json').write_text(json.dumps(result))
                tip = publish_result(output, remote=str(self.remote), source_repository=context[0], trusted_product_sha=context[1])
                target = f'results/{req["request_id"]}/{run}-1'
                self.assertEqual(json.loads(git(self.remote, 'show', f'{tip}:{target}/result.json'))['status'],
                                 'failed' if missing else 'success')
                audit = json.loads(git(self.remote, 'show', f'{tip}:{target}/snapshot/evidence/availability.json'))
                self.assertEqual(audit['retired_previous_efforts'][0]['effort'], 'max')
                self.assertIn('snapshot/evidence/models.html', git(self.remote, 'ls-tree', '-r', '--name-only', tip))
                if missing:
                    self.assertIn('missing_candidates.json', git(self.remote, 'ls-tree', '-r', '--name-only', tip))
                    self.assertFalse((output / 'snapshot/candidates.csv').exists())
                else:
                    self.assertEqual(self.pointer('latest-refresh.json')['run_id'], '601')

    def test_new_refresh_rejects_tampered_capability_proof_before_git_write(self):
        from test_refresh_sources import FIX, URLS
        from scripts.refresh_snapshot import refresh_snapshot
        pages = {URLS[name]: (FIX / name).with_suffix('.html').read_bytes() for name in URLS}
        for tamper in ('models', 'audit', 'hash', 'both'):
            with self.subTest(tamper=tamper):
                output = self.base / ('tampered-' + tamper)
                output.mkdir()
                context_base = self.base / ('tampered-context-' + tamper)
                context_base.mkdir()
                context = product_context(context_base, {'slugs': []}, new_policy=True)
                provenance = refresh_snapshot(output / 'snapshot', previous=None, fetch=pages.__getitem__)
                calculation, _ = calculate_snapshot(output / 'snapshot/candidates.csv', PARAMETERS, provenance)
                req = dict(request_data(), operation='refresh', product_sha=context[1])
                execution = {'request_commit_sha': 'b' * 40, 'run_id': '701', 'run_attempt': 1,
                             'run_url': 'https://github.com/example/actions/runs/701'}
                (output / 'result.json').write_text(json.dumps(make_envelope(
                    req, execution, calculation=calculation, errors=[])))
                (output / 'report.md').write_text('# Report')
                (output / 'report.html').write_text('<!doctype html><title>Report</title>')
                evidence = output / 'snapshot/evidence'
                if tamper == 'models':
                    (evidence / 'models.html').write_text('<li>wrong</li>')
                elif tamper == 'audit':
                    (evidence / 'availability.json').write_text('{}')
                else:
                    if tamper == 'hash':
                        sources = json.loads((evidence / 'sources.json').read_text())
                        sources['sha256_by_url'][URLS['models']] = '0' * 64
                        (evidence / 'sources.json').write_text(json.dumps(sources))
                    else:
                        audit = json.loads((evidence / 'availability.json').read_text())
                        audit['excluded_current_identities'] = []
                        (evidence / 'availability.json').write_text(json.dumps(audit))
                        source_map = json.loads((evidence / 'source_map.json').read_text())
                        source_map['availability'] = audit
                        (evidence / 'source_map.json').write_text(json.dumps(source_map))
                with self.assertRaises(PublishError):
                    publish_result(output, remote=str(self.remote), source_repository=context[0], trusted_product_sha=context[1])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.remote = self.base / 'remote.git'
        git(self.base, 'init', '--bare', '-q', str(self.remote))
        self.contexts = {}

    def publish(self, output):
        context = self.contexts.get(output)
        kwargs = dict(source_repository=context[0], trusted_product_sha=context[1]) if context else {}
        return publish_result(output, remote=str(self.remote), **kwargs)

    def output(self, *, run='100', attempt=1, operation='recompute', status='success',
               created='2026-09-26T12:00:00+00:00', request=None, schema_version=2):
        dest = self.base / f'out-{run}-{attempt}-{operation}-{status}'
        dest.mkdir()
        req = dict(request_data(), operation=operation, created_at=created)
        if request:
            req['request_id'] = request
        from bridge import result, result_v1
        api = result_v1 if schema_version == 1 else result
        calculation, _ = api.calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)
        if operation == 'refresh':
            fresh, harness = self.valid_refresh_output()
            req['product_sha'] = harness.product
            self.contexts[dest] = (harness.repo, harness.product)
            csv = (fresh / 'snapshot/candidates.csv').read_bytes()
            calculation['source_snapshot'] = {'kind': 'acquired', 'path': 'snapshot/candidates.csv',
                                               'sha256': hashlib.sha256(csv).hexdigest()}
            (dest / 'snapshot/evidence').mkdir(parents=True)
            (dest / 'snapshot/candidates.csv').write_bytes(csv)
            for name in ('source_map.json', 'version.json'):
                (dest / 'snapshot/evidence' / name).write_bytes((fresh / 'snapshot/evidence' / name).read_bytes())
            calculation, _ = api.calculate_snapshot(dest / 'snapshot/candidates.csv', PARAMETERS,
                                                dict(PROVENANCE, source_locator=calculation['source_snapshot']))
        execution = {'request_commit_sha': 'b' * 40, 'run_id': run, 'run_attempt': attempt,
                     'run_url': 'https://github.com/example/actions/runs/' + run}
        if status == 'failed':
            envelope = api.make_envelope(req, execution, calculation=None,
                                     errors=[{'code': 'test_failure', 'message': 'test'}])
        else:
            envelope = api.make_envelope(req, execution, calculation=calculation, errors=[])
            (dest / 'report.md').write_text('# Report\n')
            (dest / 'report.html').write_text('<!doctype html><title>Report</title>')
        (dest / 'result.json').write_text(json.dumps(envelope))
        return dest, envelope

    def pointer(self, name):
        return json.loads(git(self.remote, 'show', f'refs/heads/results:{name}'))

    def valid_refresh_output(self):
        # Runner's independently verified fixture has a complete, consistent
        # candidate CSV/source-map/row inventory; don't mock the reconciliation.
        from test_bridge_runner import RunnerTests
        harness = RunnerTests()
        harness.setUp()
        self.addCleanup(harness.doCleanups)
        harness.publish_refresh_fixture()
        source = harness.repo / f'results/{request_data()["request_id"]}/777-1'
        dest = self.base / f'valid-refresh-{len(list(self.base.glob("valid-refresh-*")))}'
        (dest / 'snapshot/evidence').mkdir(parents=True)
        for name in ('result.json', 'snapshot/candidates.csv',
                     'snapshot/evidence/source_map.json', 'snapshot/evidence/version.json'):
            path = dest / name
            path.write_bytes((source / name).read_bytes())
        (dest / 'report.md').write_text('# Report\n')
        (dest / 'report.html').write_text('<!doctype html><title>Report</title>')
        self.contexts[dest] = (harness.repo, harness.product)
        return dest, harness

    def test_keyed_refresh_runner_publishes_api_body_for_success_and_diagnostic_failure(self):
        from test_refresh_sources import FIX, URLS
        repo = self.base / 'product'
        repo.mkdir()
        git(repo, 'init', '-q')
        git(repo, 'config', 'user.name', 'Tester')
        git(repo, 'config', 'user.email', 'test@example.com')
        archive = repo / 'runs/2026-09-26-general-grok16'
        archive.mkdir(parents=True)
        (archive / 'public_candidate_source_map.json').write_text(json.dumps({
            'inventory': {'slugs': [], 'contributor_efforts': []}}))
        (repo / 'bridge').mkdir()
        (repo / 'bridge/refresh-policy.json').write_text('{"policy":"observed-inventory-v1"}')
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'product')
        product = git(repo, 'rev-parse', 'HEAD')
        git(repo, 'update-ref', 'refs/bridge/approved-main', product)
        request = dict(request_data(), product_sha=product)
        path = repo / 'bridge/requests' / (request['request_id'] + '.json')
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(request))
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'request')
        event = git(repo, 'rev-parse', 'HEAD')
        pages = {URLS[name]: (FIX / name).with_suffix('.html').read_bytes() for name in URLS}

        class Response:
            def __init__(self, version, size):
                self.body = json.dumps({'intelligence_index_version': version,
                                        'data': [{'model': 'API-only'}] * size}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self, *args):
                return self.body

        for run, responses, status in (
            ('301', [Response('4.3', 1)], 'success'),
            ('302', [Response('4.3', 200), Response('4.3.1', 1)], 'failed'),
        ):
            with self.subTest(run=run):
                output = self.base / ('keyed-' + run)
                execution = {'request_commit_sha': event, 'product_sha': product,
                             'branch': 'efficiency-run/' + request['request_id'],
                             'run_id': run, 'run_attempt': 1,
                             'run_url': 'https://github.com/example/actions/runs/' + run}
                with patch.dict('os.environ', {'AA_API_KEY': 'test-key'}), patch(
                        'scripts.refresh_snapshot.urllib.request.urlopen', side_effect=responses):
                    result = execute_request(request, execution=execution, repository=repo,
                                             output=output, fetch=pages.__getitem__)
                self.assertEqual(result['status'], status)
                evidence = output / 'snapshot/evidence/api_envelopes.json'
                self.assertTrue(evidence.exists())
                self.assertNotIn(b'test-key', evidence.read_bytes())
                tip = publish_result(output, remote=str(self.remote), source_repository=repo, trusted_product_sha=product)
                target = f'results/{request["request_id"]}/{run}-1'
                published = git(self.remote, 'show', f'{tip}:{target}/snapshot/evidence/api_envelopes.json')
                self.assertEqual(json.loads(published), json.loads(evidence.read_text()))
                self.assertEqual(json.loads(git(self.remote, 'show', f'{tip}:{target}/result.json'))['status'], status)
                if status == 'failed':
                    self.assertEqual(result['errors'][0]['code'], 'api_version_drift')
                    self.assertFalse((output / 'report.html').exists())
                    self.assertEqual(self.pointer('latest-success.json')['run_id'], '301')
                    self.assertEqual(self.pointer('latest-refresh.json')['run_id'], '301')
                else:
                    self.assertTrue((output / 'report.html').exists())
                    self.assertEqual(self.pointer('latest-refresh.json')['run_id'], '301')

    def test_api_evidence_rejects_header_payload_and_non_envelopes(self):
        output, _ = self.output(status='failed')
        evidence = output / 'snapshot/evidence'
        evidence.mkdir(parents=True)
        for pages in ({'headers': {'x-api-key': 'secret'}},
                      [{'intelligence_index_version': '4.3', 'data': [],
                        'request_headers': {'authorization': 'secret'}}],
                      [{'intelligence_index_version': '4.3',
                        'data': [{'headers': {'x-api-key': 'secret'}}]}],
                      [{'intelligence_index_version': '4.3', 'data': 'not a list'}]):
            (evidence / 'api_envelopes.json').write_text(json.dumps(pages))
            with self.subTest(pages=pages), self.assertRaises(PublishError):
                publish_result(output, remote=str(self.remote))

    def test_incomplete_refresh_inventory_rejected_before_any_pointer(self):
        output, _ = self.output(operation='refresh')
        source_map = output / 'snapshot/evidence/source_map.json'
        inventory = json.loads(source_map.read_text())
        inventory['inventory']['slugs'].pop()
        source_map.write_text(json.dumps(inventory))
        with self.assertRaises(PublishError):
            self.publish(output)
        self.assertNotEqual(subprocess.run(['git', '-C', str(self.remote), 'rev-parse',
                                             '--verify', 'refs/heads/results'], capture_output=True).returncode, 0)

    def test_valid_published_fresh_inventory_is_usable_by_runner(self):
        output, harness = self.valid_refresh_output()
        published = self.publish(output)
        pointer = self.pointer('latest-refresh.json')
        self.assertEqual(pointer['result_path'],
                         f'results/{request_data()["request_id"]}/777-1/result.json')
        git(harness.repo, 'checkout', '-q', '-B', 'main', harness.product)
        git(harness.repo, 'branch', '-D', 'results')
        git(harness.repo, 'fetch', '-q', str(self.remote), 'refs/heads/results:refs/heads/results')
        self.assertEqual(git(harness.repo, 'rev-parse', 'results'), published)
        inventory = _previous(harness.repo, harness.product)
        self.assertTrue(inventory['inventory']['slugs'])
        self.assertEqual(inventory['inventory']['contributor_efforts'], ['max', 'xhigh'])

    def test_failure_without_request_uuid_uses_diagnostic_only_path(self):
        output, _ = self.output(status='failed')
        envelope = json.loads((output / 'result.json').read_text())
        envelope['request_id'] = None
        (output / 'result.json').write_text(json.dumps(envelope))
        (output / 'snapshot/evidence').mkdir(parents=True)
        (output / 'snapshot/evidence/missing_candidates.json').write_text('[]')
        tip = publish_result(output, remote=str(self.remote))
        path = f'results/invalid-{envelope["request_commit_sha"]}/{envelope["run_id"]}-{envelope["run_attempt"]}/result.json'
        self.assertIsNone(json.loads(git(self.remote, 'show', f'{tip}:{path}'))['request_id'])
        self.assertEqual(git(self.remote, 'show',
                             f'{tip}:{path.removesuffix("result.json")}snapshot/evidence/missing_candidates.json'), '[]')
        self.assertEqual(publish_result(output, remote=str(self.remote)), tip)
        self.assertNotIn('latest-success.json', git(self.remote, 'ls-tree', '--name-only', tip))
        self.assertNotIn('latest-refresh.json', git(self.remote, 'ls-tree', '--name-only', tip))

    def test_http_remote_query_fragment_and_userinfo_rejected_before_git(self):
        output, _ = self.output()
        for remote in ('https://example.test/repo.git?access_token=secret',
                       'https://example.test/repo.git#secret',
                       'https://name:secret@example.test/repo.git'):
            with self.subTest(remote=remote), patch('bridge.publish._git') as git_call:
                with self.assertRaises(PublishError):
                    publish_result(output, remote=remote)
                git_call.assert_not_called()

    def test_preserves_attempts_and_idempotence(self):
        first, envelope = self.output()
        sha = publish_result(first, remote=str(self.remote))
        self.assertEqual(publish_result(first, remote=str(self.remote)), sha)
        second, _ = self.output(attempt=2)
        tip = publish_result(second, remote=str(self.remote))
        self.assertNotEqual(tip, sha)
        for attempt in (1, 2):
            path = f'results/{envelope["request_id"]}/100-{attempt}/result.json'
            self.assertEqual(json.loads(git(self.remote, 'show', f'{tip}:{path}'))['run_attempt'], attempt)
        (first / 'report.html').write_text('different')
        with self.assertRaises(PublishError):
            publish_result(first, remote=str(self.remote))

    def test_pointer_order_and_failure(self):
        newer, _ = self.output(run='200', operation='refresh', created='2026-09-27T12:00:00+00:00')
        self.publish(newer)
        before = self.pointer('latest-refresh.json')
        older, _ = self.output(run='201', operation='refresh', created='2026-09-26T12:00:00+00:00')
        self.publish(older)
        self.assertEqual(self.pointer('latest-refresh.json'), before)
        self.assertEqual(self.pointer('latest-success.json'), before)
        recompute, _ = self.output(run='202')
        publish_result(recompute, remote=str(self.remote))
        self.assertEqual(self.pointer('latest-refresh.json'), before)
        success = self.pointer('latest-success.json')
        failed, _ = self.output(run='203', status='failed')
        publish_result(failed, remote=str(self.remote))
        self.assertEqual(self.pointer('latest-success.json'), success)
        self.assertEqual(self.pointer('latest-refresh.json'), before)

    def test_order_is_source_date_then_offset_aware_time_then_commit(self):
        old = {'status': 'success', 'operation': 'refresh', 'source_dates': ['2026-09-27'],
               'created_at': '2026-09-26T10:00:00+00:00', 'request_commit_sha': 'a'*40}
        incoming = dict(old, source_dates=['2026-09-26'], created_at='2026-09-28T10:00:00+00:00')
        self.assertIs(choose_latest(old, incoming, refresh_only=False), old)
        incoming['source_dates'] = ['2026-09-27']
        self.assertIs(choose_latest(old, incoming, refresh_only=False), incoming)
        incoming['source_dates'] = ['2026-02-30']
        with self.assertRaises(PublishError):
            choose_latest(old, incoming, refresh_only=False)

    def test_retry_exhaustion_does_not_force_push(self):
        from bridge import publish
        output, _ = self.output()
        with patch.object(publish, '_push', return_value=False) as push:
            with self.assertRaisesRegex(PublishError, 'retry_exhausted'):
                publish_result(output, remote=str(self.remote))
        self.assertEqual(push.call_count, 3)
        self.assertNotEqual(subprocess.run(['git', '-C', str(self.remote), 'rev-parse',
                                             '--verify', 'refs/heads/results'], capture_output=True).returncode, 0)

    def test_invalid_output_layout_and_hash(self):
        output, _ = self.output(operation='refresh')
        (output / 'snapshot/candidates.csv').write_text('changed')
        with self.assertRaises(PublishError):
            self.publish(output)
        good, _ = self.output(run='101')
        (good / 'extra.txt').write_text('unapproved')
        with self.assertRaises(PublishError):
            publish_result(good, remote=str(self.remote))
        (good / 'extra.txt').unlink()
        (good / 'report.html').unlink()
        (good / 'report.html').symlink_to('/etc/hosts')
        with self.assertRaises(PublishError):
            publish_result(good, remote=str(self.remote))

    def test_failed_output_has_no_partial_report(self):
        output, _ = self.output(status='failed')
        (output / 'report.md').write_text('partial')
        with self.assertRaises(PublishError):
            publish_result(output, remote=str(self.remote))

    def test_recompute_does_not_replace_refresh_pointer(self):
        old = {'operation': 'refresh', 'status': 'success', 'request_id': 'old'}
        new = {'operation': 'recompute', 'status': 'success', 'request_id': 'new'}
        self.assertEqual(choose_latest(old, new, refresh_only=True), old)

    def test_retries_nonfastforward_with_competing_publisher(self):
        from bridge import publish
        first, env = self.output(run='300')
        second, _ = self.output(run='301')
        original = publish._push
        calls = []

        def competing(*args, **kwargs):
            if not calls:
                calls.append(1)
                publish_result(second, remote=str(self.remote))
            return original(*args, **kwargs)

        with patch.object(publish, '_push', side_effect=competing):
            publish_result(first, remote=str(self.remote))
        tip = git(self.remote, 'rev-parse', 'refs/heads/results')
        self.assertIn(f'results/{env["request_id"]}/300-1/result.json', git(self.remote, 'ls-tree', '-r', '--name-only', tip))
        self.assertIn(f'results/{env["request_id"]}/301-1/result.json', git(self.remote, 'ls-tree', '-r', '--name-only', tip))

    def test_retries_remote_advance_between_ls_remote_and_fetch(self):
        from bridge import publish
        first, env = self.output(run='310')
        second, _ = self.output(run='311')
        seed, _ = self.output(run='309')
        publish_result(seed, remote=str(self.remote))
        original = publish._git
        raced = []

        def advance(repo, *args, **kwargs):
            if args[0] == 'fetch' and not raced:
                raced.append(True)
                publish_result(second, remote=str(self.remote))
            return original(repo, *args, **kwargs)

        with patch.object(publish, '_git', side_effect=advance):
            publish_result(first, remote=str(self.remote))
        self.assertEqual(len(raced), 1)
        tip = git(self.remote, 'rev-parse', 'refs/heads/results')
        for run in ('310', '311'):
            self.assertIn(f'results/{env["request_id"]}/{run}-1/result.json',
                          git(self.remote, 'ls-tree', '-r', '--name-only', tip))

    def test_fetch_race_uses_same_three_attempt_budget(self):
        from bridge import publish
        output, _ = self.output(run='312')
        original = publish._git
        fetches = []

        def mismatched_fetch(repo, *args, **kwargs):
            if args[0] == 'fetch':
                fetches.append(True)
                result = original(repo, *args, **kwargs)
                # Return a valid fetch, then simulate an advanced remote tip via rev-parse.
                return result
            if args[:2] == ('rev-parse', 'FETCH_HEAD'):
                return subprocess.CompletedProcess([], 0, b'0' * 40 + b'\n', b'')
            return original(repo, *args, **kwargs)

        # Initialize a real remote branch so each attempt actually fetches.
        seed, _ = self.output(run='313')
        publish_result(seed, remote=str(self.remote))
        with patch.object(publish, '_git', side_effect=mismatched_fetch):
            with self.assertRaisesRegex(PublishError, 'concurrent_publication_retry_exhausted'):
                publish_result(output, remote=str(self.remote))
        self.assertEqual(len(fetches), 3)
