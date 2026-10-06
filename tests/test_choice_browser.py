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
        payload['caveats'].append('來源退出：Inkling 缺 task cost，不沿用舊价。')
        (cls.root/'index.html').write_text(render_html(payload,observations=[dict(name='SourceMissing xhigh',slug='source-missing',state='missing_task_cost',reason='task cost missing')]))
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


if __name__=='__main__': unittest.main()
