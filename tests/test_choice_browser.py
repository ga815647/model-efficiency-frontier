"""Real Chromium regressions; opt in with FRONTIER_BROWSER_TESTS=1."""
from copy import deepcopy
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import os
from pathlib import Path
import tempfile
from threading import Thread
import unittest

from bridge.choice_report import render_html
from bridge.result_v2 import calculate_v2
from test_bridge_result import SNAPSHOT,PARAMETERS,PROVENANCE


@unittest.skipUnless(os.environ.get('FRONTIER_BROWSER_TESTS')=='1','Chromium tests opt-in')
class ChoiceBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.temp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temp.name)
        payload=calculate_v2(SNAPSHOT,PARAMETERS,PROVENANCE)
        # A source exit is absent from the current calculation; the older fixture
        # still contains this identity, so remove it to model that condition.
        payload['candidate_statuses']=[row for row in payload['candidate_statuses'] if row['model']!='MiniMax-M2.7']
        payload['candidate_count']=len(payload['candidate_statuses'])
        payload['caveats'].append('來源退出：Inkling 缺 task cost，不沿用舊价。')
        from bridge.view_evidence import source_observations
        observations=source_observations([dict(name='SourceMissing (xhigh)',slug='source-missing'),dict(name='MiniMax-M2.7',slug='minimax-m2-7')],
            {'reconciliation':{'status_by_slug':{
                'source-missing':dict(state='observed_unusable',reason='missing_task_cost'),
                'minimax-m2-7':dict(state='retired',reason='deprecated')}}})
        (cls.root/'index.html').write_text(render_html(payload,observations=observations))
        from bridge.result import calculate_snapshot
        from test_subscription_scenario import PARAMS
        subscription, _ = calculate_snapshot(SNAPSHOT, PARAMS, PROVENANCE)
        (cls.root/'subscription.html').write_text(render_html(subscription))
        from bridge import site
        from bridge.result_v4 import calculate_v4
        from bridge.result import make_envelope
        from test_bridge_result import recompute_data
        from test_bridge_result_v2 import EXECUTION
        import hashlib,json
        provider_provenance = dict(PROVENANCE, caveats=PROVENANCE['caveats'] +
                                   ['來源退出：SourceMissing 缺 task cost，不沿用舊價。'])
        env=make_envelope(dict(recompute_data(),schema_version=3,parameters=PARAMS),EXECUTION,
                          calculation=calculate_v4(SNAPSHOT,PARAMS,provider_provenance),errors=[])
        record=dict(envelope=env,publication_commit='c'*40,result_bytes=json.dumps(env).encode(),
                    report_bytes=b'original report',csv_sha256=hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(),observations=[])
        benchmark=next(r for r in env['candidate_statuses'] if r['model']=='GPT-6 Sol' and r['effort']=='max')
        choice=dict(benchmark_identity=benchmark['identity'],tolerance_multiplier=1,
                    result_sha256=hashlib.sha256(record['result_bytes']).hexdigest())
        choice_path=f'results/{env["request_id"]}/{env["run_id"]}-{env["run_attempt"]}/result.json'
        from bridge.personal_cp import calculate_personal_cp
        cls.personal=calculate_personal_cp(env,choice)
        site.write_site([record],cls.root/'provider-demo',formal_parameters=PARAMS,
                        site_product_commit='d'*40,base_path='/provider-demo/',formal_result_schema_version=4,
                        personal_choices=dict(schema_version=1,choices={choice_path:choice}))
        edge=deepcopy(payload)
        edge['anchors']=dict.fromkeys(edge['anchors'])
        for row in edge['ladder']:
            row['model']='Long<Model>&"'+('長名稱'*45)
        (cls.root/'edge.html').write_text(render_html(edge))
        class Silent(SimpleHTTPRequestHandler):
            def log_message(self,*args): pass
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),partial(Silent,directory=cls.temp.name))
        cls.thread=Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}/'
        cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.temp.cleanup()

    def test_mobile_desktop_keyboard_empty_and_source_states(self):
        for width in (360,390,1280):
            with self.subTest(width=width):
                page=self.browser.new_page(viewport={'width':width,'height':900})
                page.goto(self.url)
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
                search=page.locator('#model-search');search.fill('Astra max')
                self.assertGreater(page.locator('[data-search]:visible').count(),0)
                search.fill('Sol max'); self.assertGreater(page.locator('[data-search]:visible').count(),0)
                search.fill('SourceMissing xhigh');self.assertIn('來源缺值／退出',page.locator('[data-search]:visible').inner_text())
                search.fill('MiniMax-M2.7 unspecified');self.assertIn('retired',page.locator('[data-search]:visible').inner_text(timeout=1000))
                search.fill('not-observed-123');self.assertTrue(page.locator('#search-empty').is_visible())
                search.press('Escape');self.assertEqual(search.input_value(),'')
                summary=page.locator('#calculation > summary');summary.focus();summary.press('Enter')
                self.assertIsNotNone(page.locator('#calculation').get_attribute('open'))
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
                page.goto(self.url+'edge.html')
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
                self.assertEqual(page.locator('[data-anchor] .model-name').all_inner_texts(),['從缺','從缺'])
                page.close()

    def test_core_and_full_candidates_without_javascript(self):
        page=self.browser.new_page(java_script_enabled=False,viewport={'width':360,'height':900})
        page.goto(self.url)
        self.assertTrue(page.locator('[data-anchor="highest_retained_score"] .model-name').is_visible())
        self.assertGreater(page.locator('#ladder > .table-wrap tbody tr').count(),0)
        page.locator('#search-results > summary').click()
        self.assertGreater(page.locator('[data-search]:visible').count(),150)
        page.close()

    def test_personal_cp_all_scopes_mobile_desktop_and_no_javascript(self):
        for width in (360,390,1280):
            for js in (True,False):
                with self.subTest(width=width,javascript=js):
                    page=self.browser.new_page(viewport={'width':width,'height':900},java_script_enabled=js)
                    for scope in ('all','gpt','gemini','claude','grok'):
                        suffix='' if scope=='all' else f'providers/{scope}/'
                        page.goto(self.url+'provider-demo/'+suffix)
                        card=page.locator('#personal-cp')
                        row=self.personal['scopes'][scope]['selected']
                        self.assertEqual(card.locator('.model-name').inner_text(),row['model'] if row else '從缺')
                        if row: self.assertIn(row['effort'],card.locator('.effort').inner_text())
                        self.assertIn(f'≥ {self.personal["minimum_score"]:.2f}',card.locator('[data-personal-threshold]').inner_text())
                        self.assertIn('並非 AA 的統計誤差',card.inner_text())
                        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
                    page.close()

    def test_subscription_factors_are_readable_without_overflow_or_javascript(self):
        for width in (360,390,1280):
            page=self.browser.new_page(viewport={'width':width,'height':900},java_script_enabled=False)
            page.goto(self.url+'subscription.html')
            for text in ('GPT ×18.9','Gemini ×6','Claude ×37','Grok ×16','Contributor ×1'):
                self.assertIn(text,page.locator('header').inner_text())
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
            self.assertEqual(page.locator('[data-anchor]').count(),2)
            page.close()

    def test_four_subscription_ladders_and_native_provider_navigation(self):
        from bridge.provider_view import provider_for
        import json
        for width in (360,390,1280):
            page=self.browser.new_page(viewport={'width':width,'height':900})
            page.goto(self.url+'provider-demo/')
            self.assertEqual(page.locator('[data-provider-summary]').count(),4)
            self.assertEqual(page.locator('[data-family="source-exits"]').count(),1)
            self.assertTrue(page.locator('[data-family="source-exits"]').evaluate(
                '(node) => node.previousElementSibling.id === "calculation"'))
            self.assertEqual(page.locator('#effort-filter').count(),0)
            self.assertNotIn('僅供比較',page.locator('body').inner_text())
            for key in ('gpt','gemini','claude','grok'):
                link=page.locator(f'#provider-chooser [data-provider="{key}"]')
                link.focus();link.press('Enter')
                self.assertEqual(page.locator('[data-selection-scope]').get_attribute('data-selection-scope'),key)
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
                for model in page.locator('#ladder > .table-wrap tbody tr td strong').all_inner_texts():
                    self.assertEqual(provider_for({'identity':model}),key)
                raw=page.request.get(page.url+'view.json')
                self.assertEqual(raw.status,200)
                calculation=raw.json()['calculation']
                for anchor,row in calculation['anchors'].items():
                    displayed=page.locator(f'[data-anchor="{anchor}"] .model-name').inner_text()
                    self.assertEqual(displayed,row['model'] if row else '從缺')
                page.locator('#model-search').fill('not-observed-123')
                self.assertTrue(page.locator('#search-empty').is_visible())
                page.locator('#model-search').press('Escape')
                page.locator('#calculation > summary').click()
                self.assertEqual(page.locator('[data-family="source-exits"]').count(),0)
                self.assertNotIn('來源退出：SourceMissing',page.locator('body').inner_text())
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
            page.close()
        page=self.browser.new_page(java_script_enabled=False,viewport={'width':360,'height':900})
        page.goto(self.url+'provider-demo/')
        page.locator('#provider-chooser [data-provider="claude"]').click()
        self.assertTrue(page.locator('[data-anchor="highest_retained_score"] .model-name').is_visible())
        self.assertGreater(page.locator('#ladder > .table-wrap tbody tr').count(),0)
        page.close()


if __name__=='__main__': unittest.main()
