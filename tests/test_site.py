"""Publication safety and project-subpath contracts for the Pages builder."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from bridge import site
from bridge.result import make_envelope
from bridge.result_v2 import calculate_v2
from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE, recompute_data
import test_bridge_runner as runner_fixture
from test_bridge_runner import git


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        calc = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)
        cls.envelope = make_envelope(recompute_data(), dict(request_commit_sha='b'*40,
            run_id='123', run_attempt=1, run_url='https://github.com/example/actions/runs/123'), calculation=calc, errors=[])

    def record(self, envelope=None):
        e = deepcopy(envelope or self.envelope)
        return dict(envelope=e, publication_commit='c'*40,
                    result_bytes=json.dumps(e).encode(), report_bytes=b'offline-report',
                    csv_sha256=hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(), observations=[])

    def test_only_formal_success_can_select_home_and_order_is_monotone(self):
        original = self.record()
        experiment = self.record(); experiment['envelope']['parameters']['gpt_factor'] = 99
        experiment['envelope']['created_at'] = '2099-01-01T00:00:00Z'
        self.assertIs(site.select_home([experiment, original], PARAMETERS), original)
        failed = self.record(); failed['envelope']['status'] = 'failed'
        self.assertIs(site.select_home([failed, original], PARAMETERS), original)
        newer = self.record(); newer['envelope']['created_at'] = '2026-10-06T00:00:00Z'
        for records in ([newer, original], [original, newer]):
            self.assertIs(site.select_home(records, PARAMETERS), newer)
        repeated = self.record(newer['envelope']); repeated['envelope']['run_attempt'] = 2
        self.assertIs(site.select_home([repeated, newer], PARAMETERS), repeated)
        with self.assertRaises(site.SiteError):
            site.select_home([experiment, failed], PARAMETERS)

    def test_explicit_allowlist_subpath_manifests_and_durable_results(self):
        record = self.record()
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)/'site'
            site.write_site([record], output, formal_parameters=PARAMETERS,
                            site_product_commit='d'*40, base_path='/model-efficiency-frontier/')
            fixed = f'results/{self.envelope["request_id"]}/123-1/'
            expected = {'.nojekyll','index.html','manifest.json'} | {fixed+n for n in ('index.html','result.json','report.html','manifest.json')}
            expected |= {prefix+f'providers/{provider}/{name}' for prefix in ('',fixed)
                         for provider in ('gpt','gemini','claude','grok') for name in ('index.html','view.json','manifest.json')}
            self.assertEqual({p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}, expected)
            manifest = json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['publication_commit'], 'c'*40)
            self.assertEqual(manifest['result_sha256'], hashlib.sha256(record['result_bytes']).hexdigest())
            self.assertEqual(manifest['result_url'], '/model-efficiency-frontier/'+fixed)
            self.assertEqual(manifest['product_commit'], self.envelope['product_sha'])
            self.assertEqual(manifest['site_product_commit'], 'd'*40)
            self.assertIn('/model-efficiency-frontier/'+fixed+'result.json', (output/'index.html').read_text())
            self.assertEqual((output/fixed/'report.html').read_bytes(), record['report_bytes'])
            for provider in ('gpt','gemini','claude','grok'):
                view=json.loads((output/f'providers/{provider}/view.json').read_text())
                self.assertEqual(view['provider'],provider)
                self.assertEqual(view['parent_result_sha256'],manifest['result_sha256'])
                link=manifest['provider_views'][provider]
                self.assertEqual(link['view_sha256'],hashlib.sha256((output/f'providers/{provider}/view.json').read_bytes()).hexdigest())
                self.assertTrue((output/fixed/f'providers/{provider}/index.html').exists())
            self.assertNotIn('effort-filter',(output/'index.html').read_text())

    def test_invalid_and_duplicate_results_fail_before_output_changes(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)/'site'; output.mkdir(); (output/'index.html').write_text('previous success')
            failed = self.record(); failed['envelope']['status'] = 'failed'
            for records in ([failed], [self.record(), self.record()]):
                with self.assertRaises(site.SiteError):
                    site.write_site(records, output, formal_parameters=PARAMETERS,
                                    site_product_commit='d'*40, base_path='/model-efficiency-frontier/')
                self.assertEqual((output/'index.html').read_text(), 'previous success')

    def test_serving_sidecars_are_hash_bound_allowlisted_and_visible_in_five_scopes(self):
        from bridge.serving_plan import calculate_plan_view, validate_bundle
        root=Path(__file__).resolve().parents[1]
        registry_raw=(root/'bridge/serving-plans.json').read_bytes()
        research_raw=(root/json.loads(registry_raw)['research']['path']).read_bytes()
        registry,research=validate_bundle(registry_raw,research_raw)
        record=self.record();original=deepcopy(record)
        fixed=f'results/{record["envelope"]["request_id"]}/123-1/'
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/'site'
            manifest=site.write_site([record],output,formal_parameters=PARAMETERS,
                site_product_commit='d'*40,base_path='/demo/',serving_registry=registry_raw,serving_research=research_raw)
            entry=manifest['serving_plans']
            for name,key in (('serving-plans.json','registry'),('plan-research.json','research'),('plan-view.json','view')):
                raw=(output/fixed/name).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),entry[key+'_sha256'])
                self.assertEqual(entry[key+'_url'],'/demo/'+fixed+name)
                self.assertEqual((output/name).read_bytes(),raw)
            view=json.loads((output/'plan-view.json').read_bytes())
            expected=calculate_plan_view(record['envelope'],registry,research)
            self.assertEqual({k:view[k] for k in expected},expected)
            self.assertEqual(view['parent_result_sha256'],manifest['result_sha256'])
            for scope in ('all','gpt','gemini','claude','grok'):
                prefix='' if scope=='all' else f'providers/{scope}/'
                page=(output/prefix/'index.html').read_text()
                self.assertIn('id="serving-plans"',page)
                self.assertIn('BytePlus ModelArk',page)
                self.assertIn('尚未套用數值優惠',page)
                self.assertIn('Coding Plan Lite',page);self.assertIn('Coding Plan Pro',page)
                self.assertEqual(page.count('data-provider="'),5)
                scoped_manifest=json.loads((output/prefix/'manifest.json').read_bytes())
                self.assertEqual(scoped_manifest['serving_plans'],entry)
                self.assertLess(page.index('id="serving-plans"'),page.index('id="calculation"'))
            self.assertEqual((output/fixed/'result.json').read_bytes(),record['result_bytes'])
            self.assertEqual((output/fixed/'report.html').read_bytes(),record['report_bytes'])
            self.assertFalse((output/'bridge').exists())
        self.assertEqual(record,original)

    def test_kimi_research_is_hash_bound_visible_in_all_five_scopes_and_not_ranked(self):
        from bridge.kimi_plan import validate_kimi_research
        root=Path(__file__).resolve().parents[1]
        raw=(root/'bridge/kimi-plans.json').read_bytes()
        study=validate_kimi_research(raw)
        record=self.record()
        original=deepcopy(record)
        fixed=f'results/{record["envelope"]["request_id"]}/123-1/'
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/'site'
            manifest=site.write_site([record],output,formal_parameters=PARAMETERS,
                site_product_commit='d'*40,base_path='/demo/',kimi_research=raw)
            entry=manifest['kimi_plans']
            self.assertEqual(entry['research_id'],study['research_id'])
            self.assertEqual(entry['research_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(entry['research_url'],'/demo/'+fixed+'kimi-plans.json')
            self.assertEqual((output/'kimi-plans.json').read_bytes(),raw)
            self.assertEqual((output/fixed/'kimi-plans.json').read_bytes(),raw)
            self.assertEqual(manifest['parameters'],record['envelope']['parameters'])
            for scope in ('all','gpt','gemini','claude','grok'):
                prefix='' if scope=='all' else f'providers/{scope}/'
                page=(output/prefix/'index.html').read_text()
                self.assertIn('id="kimi-plans"',page)
                self.assertIn('倍率未知，不進正式 LADDER',page)
                self.assertIn('不能混入 2026-10-07 固定快照',page)
                self.assertEqual(page.count('data-kimi-plan='),4)
                self.assertEqual(page.count('data-provider='),5)
                self.assertLess(page.index('id="kimi-plans"'),page.index('id="calculation"'))
                scoped=json.loads((output/prefix/'manifest.json').read_bytes())
                self.assertEqual(scoped['kimi_plans'],entry)
            self.assertEqual((output/fixed/'result.json').read_bytes(),record['result_bytes'])
            self.assertEqual((output/fixed/'report.html').read_bytes(),record['report_bytes'])
            self.assertFalse((output/'bridge').exists())
        self.assertEqual(record,original)

    def test_invalid_kimi_research_fails_before_writing(self):
        root=Path(__file__).resolve().parents[1]
        raw=(root/'bridge/kimi-plans.json').read_bytes()
        data=json.loads(raw);data['factor']=99
        altered=(json.dumps(data)+'\n').encode()
        for payload in (altered,b'not-json',b'{}',None):
            if payload is None:
                continue  # absence is explicitly optional for old offline fixtures
            with tempfile.TemporaryDirectory() as d:
                output=Path(d)/'site'
                with self.assertRaises(ValueError):
                    site.write_site([self.record()],output,formal_parameters=PARAMETERS,
                        site_product_commit='d'*40,base_path='/demo/',kimi_research=payload)
                self.assertFalse(output.exists())

    def test_invalid_serving_registry_or_research_fails_before_any_write(self):
        root=Path(__file__).resolve().parents[1]
        raw=(root/'bridge/serving-plans.json').read_bytes()
        research=(root/json.loads(raw)['research']['path']).read_bytes()
        bad=json.loads(raw);bad['research']['path']='../../secret'
        for registry_bytes,research_bytes in ((raw,research+b' '),(json.dumps(bad).encode(),research),
                                             (raw,None),(None,research)):
            with self.subTest(registry=registry_bytes is not None),tempfile.TemporaryDirectory() as d:
                output=Path(d)/'site'
                with self.assertRaises(ValueError):
                    site.write_site([self.record()],output,formal_parameters=PARAMETERS,
                        site_product_commit='d'*40,base_path='/demo/',serving_registry=registry_bytes,serving_research=research_bytes)
                self.assertFalse(output.exists())

    def test_rejects_unsafe_project_paths(self):
        for path in ('//evil.test/', '/x/../', 'javascript:x', '/x"/', '/x?y/'):
            with self.subTest(path=path), self.assertRaises(site.SiteError):
                site.validate_base_path(path)

    def test_personal_choice_is_bound_to_exact_result_and_shared_by_all_pages(self):
        from bridge.personal_cp import calculate_personal_cp
        record = self.record()
        env = record['envelope']
        path = f'results/{env["request_id"]}/123-1/'
        benchmark = env['candidate_statuses'][0]
        choice = dict(benchmark_identity=benchmark['identity'], tolerance_multiplier=1,
                      result_sha256=hashlib.sha256(record['result_bytes']).hexdigest())
        policy = dict(schema_version=1,choices={path+'result.json':choice})
        original = deepcopy(record)
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/'valid'
            manifest=site.write_site([record],output,formal_parameters=PARAMETERS,
                site_product_commit='d'*40,base_path='/demo/',personal_choices=policy)
            raw=(output/path/'personal-cp.json').read_bytes()
            view=json.loads(raw)
            self.assertEqual(manifest['personal_cp']['view_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(view['parent_result_sha256'],choice['result_sha256'])
            expected=calculate_personal_cp(env,choice)
            for key in ('benchmark','minimum_score','scopes'):
                self.assertEqual(view[key],expected[key])
            for scope in ('all','gpt','gemini','claude','grok'):
                prefix='' if scope=='all' else f'providers/{scope}/'
                page=(output/prefix/'index.html').read_text(encoding='utf-8')
                self.assertIn('id="personal-cp"',page)
                self.assertIn(f'能力門檻 ≥ {view["minimum_score"]:.2f}',page)
                row=view['scopes'][scope]['selected']
                personal=page.split('id="personal-cp"')[1].split('</article>')[0]
                self.assertIn(row['model'] if row else '從缺',personal)
            self.assertEqual((output/path/'result.json').read_bytes(),record['result_bytes'])
            self.assertEqual((output/path/'report.html').read_bytes(),record['report_bytes'])
            bad=deepcopy(policy);bad['choices'][path+'result.json']['result_sha256']='e'*64
            with self.assertRaisesRegex(site.SiteError,'personal_cp_result_hash_mismatch'):
                site.write_site([record],Path(d)/'bad',formal_parameters=PARAMETERS,
                    site_product_commit='d'*40,base_path='/demo/',personal_choices=bad)
            self.assertFalse((Path(d)/'bad').exists())
            newer=self.record();newer['envelope']['run_id']='456'
            newer['envelope']['created_at']='2026-10-06T00:00:00Z'
            site.write_site([record,newer],Path(d)/'new',formal_parameters=PARAMETERS,
                site_product_commit='d'*40,base_path='/demo/',personal_choices=policy)
            self.assertNotIn('id="personal-cp"',(Path(d)/'new/index.html').read_text(encoding='utf-8'))
            self.assertNotIn('personal_cp',json.loads((Path(d)/'new/manifest.json').read_bytes()))
            with self.assertRaisesRegex(site.SiteError,'personal_cp_result_missing'):
                site.write_site([newer],Path(d)/'missing',formal_parameters=PARAMETERS,
                    site_product_commit='d'*40,base_path='/demo/',personal_choices=policy)
        self.assertEqual(record,original)


class SiteGitValidationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = runner_fixture.RunnerTests('test_approved_historical_adapter_is_pinned_and_html_matches')
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        req, execution = f.submit()
        self.envelope, output = f.run_request(req, execution)
        self.req, self.execution = req, execution
        git(f.repo, 'checkout', '-q', '--orphan', 'results')
        git(f.repo, 'rm', '-rf', '.')
        target = f.repo/f'results/{req["request_id"]}/123-1'
        target.mkdir(parents=True)
        for name in ('result.json','report.html','report.md'):
            (target/name).write_bytes((output/name).read_bytes())
        git(f.repo, 'add', '.'); git(f.repo, 'commit', '-qm', 'publication')
        self.publication = git(f.repo, 'rev-parse','HEAD')
        git(f.repo, 'checkout', '-q', '--detach', f.product)

    def test_fixed_git_result_is_source_and_transport_validated(self):
        f=self.fixture
        record=site.load_record(f.repo, self.publication, f'results/{self.req["request_id"]}/123-1/result.json')
        self.assertEqual(record['envelope'],self.envelope)
        self.assertEqual(record['publication_commit'],self.publication)
        self.assertEqual(record['csv_sha256'],hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest())

    def test_forged_result_must_not_publish(self):
        f=self.fixture
        git(f.repo,'checkout','-q','results')
        path=f.repo/f'results/{self.req["request_id"]}/123-1/result.json'
        e=json.loads(path.read_text()); e['parameters']['gpt_factor']=99
        path.write_text(json.dumps(e)); git(f.repo,'add','.'); git(f.repo,'commit','-qm','forged')
        tip=git(f.repo,'rev-parse','HEAD'); git(f.repo,'checkout','-q','--detach',f.product)
        with self.assertRaises(ValueError):
            site.load_record(f.repo,tip,path.relative_to(f.repo).as_posix())


if __name__ == '__main__': unittest.main()
