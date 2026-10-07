"""View contracts: projections must preserve evidence, never choose identities."""
from contextlib import ExitStack
from copy import deepcopy
from html import escape
from html.parser import HTMLParser
import importlib.util
import re
import unittest
from unittest.mock import patch

from bridge.result_v2 import calculate_v2
from scripts.refresh_inventory import DISCLOSURE_PREFIX
from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE


class WindowReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)

    def views(self, payload):
        self.assertIsNotNone(importlib.util.find_spec('bridge.window_report'),
                             'v2 read-only report module must exist')
        from bridge.window_report import render_html, render_markdown
        before = deepcopy(payload)
        result = render_markdown(payload), render_html(payload)
        self.assertEqual(payload, before)
        return result

    def test_selected_anchors_ladder_and_complete_audit(self):
        md, page = self.views(self.payload)
        # Compare visible text after Markdown backslash escapes, not its syntax.
        for output in (re.sub(r'\\([\\`*_{}\[\]()#!~])', r'\1', md), page):
            for anchor in self.payload['anchors'].values():
                self.assertIn(anchor['identity'], output)
            for row in self.payload['candidate_statuses']:
                self.assertIn(escape(row['identity']), output)
            for label in ('Cost_orig',
                          'Cost_adj', 'CP_adj', 'GRADE', '僅比較',
                          'Standard tier only', '2026-09-26', '推定',
                          PROVENANCE['source_locator']['path'], 'a' * 40,
                          '$79', '不自動續訂', '硬2分邊界'):
                self.assertIn(label, output)
            self.assertNotIn('階梯中段', output)
        self.assertEqual(sorted(int(i) for i in re.findall(r'data-rank="(\d+)"', page)),
                         list(range(1, 11)))
        self.assertNotIn('aria-label="三檔推薦"', page)
        table = page.split('<tbody>', 1)[1].split('</tbody>', 1)[0]
        positions = [table.index(escape(r['model'])) for r in self.payload['ladder'] if not r['comparison_only']]
        self.assertEqual(positions, sorted(positions))

    def test_source_date_visible_and_full_policy_available_in_details(self):
        md, page = self.views(self.payload)
        for output in (md, page):
            for value in ('2026-09-26', 'AA-Intelligence-Index-v4.3.2',
                          '推定', 'full-candidate comparison', '0.05', 'Privacy'):
                self.assertIn(value, output)
        self.assertIn('2026-09-26', page.split('aria-label="保留檔入口"')[0])
        self.assertIn('<details id="calculation"', page)

    def test_source_exits_are_at_html_end_and_escaped(self):
        payload = deepcopy(self.payload)
        exits = [
            DISCLOSURE_PREFIX + 'MiniMax-M2.7：當次 deprecated=true，排行退役。',
            DISCLOSURE_PREFIX + '<img src=x onerror=alert(1)>|line\nnext：當前 task cost 缺值，本次未參戰，未沿用舊價。',
        ]
        payload['caveats'].extend(exits)
        md, page = self.views(payload)
        self.assertIn('## 本次來源退出', md)
        self.assertIn('data-family="source-exits"', page)
        self.assertLess(md.index('最低情境成本保留檔'), md.index('## 本次來源退出'))
        self.assertLess(md.index('## 本次來源退出'), md.index('## 已選好階梯'))
        self.assertLess(page.index('aria-label="保留檔入口"'), page.index('data-family="source-exits"'))
        self.assertGreater(page.index('data-family="source-exits"'), page.index('id="calculation"'))
        self.assertLess(page.index('data-family="source-exits"'), page.index('<footer'))
        md_summary = md.split('## 本次來源退出', 1)[1].split('## 已選好階梯', 1)[0]
        html_summary = page.split('data-family="source-exits"', 1)[1].split('</section>', 1)[0]
        for summary in (md_summary, html_summary):
            self.assertLess(summary.index('MiniMax-M2.7'), summary.index('&lt;img src=x'))
            self.assertIn('本次未參戰，未沿用舊價', summary)
            self.assertNotIn('<img src=x', summary)
        self.assertIn('&#124;line<br>next', md_summary)
        self.assertIn(escape(exits[1]), html_summary)
        # Keep each exit once at the end, while preserving the source payload.
        for note in exits:
            self.assertEqual(page.count(escape(note)), 1)
        self.assertIn('GRADE-B', page.split('<h2>來源與限制</h2>', 1)[1])
        self.assertEqual(payload['caveats'][-2:], exits)

    def test_no_source_exits_means_no_empty_warning_and_other_caveats_remain(self):
        payload = deepcopy(self.payload)
        payload['caveats'].extend(['Ordinary B caveat', 'not-prefix ' + DISCLOSURE_PREFIX + 'not an exit'])
        md, page = self.views(payload)
        self.assertNotIn('## 本次來源退出', md)
        self.assertNotIn('data-family="source-exits"', page)
        for output in (md, page):
            for value in ('Ordinary B caveat', 'not an exit', 'GRADE-B', 'Contributor ×1', '推定'):
                self.assertIn(value, output)

    def test_upgrade_trace_and_b_diagnostic_are_payload_projections(self):
        payload = deepcopy(self.payload)
        row = payload['ladder'][1]
        row['upgrade'] = dict(cheaper_identity='Supplied target', delta_score=7.125,
                              cost_multiple=3.25, delta_cost_adj=0.125)
        step = payload['selection_trace'][0]
        step.update(support='neutral_missing_window', strength=0)
        winner = next(r for r in payload['candidate_statuses'] if r['identity'] == step['winner'])
        winner['grade'] = 'B'
        payload['grade_b_effects'] = [dict(identity='Indirect A effect',
                                        with_b_retained=False, without_b_retained=True)]
        for output in self.views(payload):
            for value in ('Supplied target', '7.125', '3.25', '0.125',
                          '缺雙側視窗、依CP解平手', '分差', 'GRADE-B',
                          'Indirect A effect', '有B：不保留', '無B：保留',
                          'B組', '非單一B的唯一因果證明'):
                self.assertIn(value, output)
            removed = next(r for r in payload['candidate_statuses'] if r['identity'] == step['removed'][0])
            self.assertIn(f'{abs(removed["score"] - winner["score"]):.6f}', output)

    def test_empty_and_claude_only_do_not_resurrect_excluded_anchors(self):
        for ladder in ([], self.payload['ladder'][:1]):
            payload = deepcopy(self.payload)
            payload['ladder'] = deepcopy(ladder)
            payload['anchors'] = dict(highest_retained_score=None, lowest_retained_cost=None)
            md, page = self.views(payload)
            cards = page.split('aria-label="保留檔入口"', 1)[1].split('</section>', 1)[0]
            self.assertEqual(cards.count('從缺'), 2)
            self.assertEqual(md.count('：從缺'), 2)
            self.assertEqual(page.count('data-rank="'), len(ladder))
            self.assertIn('Standard tier only', page)

    def test_same_identity_can_fill_both_cards(self):
        payload = deepcopy(self.payload)
        row = payload['anchors']['highest_retained_score']
        payload['anchors']['lowest_retained_cost'] = row
        _, page = self.views(payload)
        cards = page.split('aria-label="保留檔入口"', 1)[1].split('</section>', 1)[0]
        self.assertEqual(cards.count(escape(row['identity'])), 2)

    def test_untrusted_strings_and_markdown_cells_are_escaped(self):
        payload = deepcopy(self.payload)
        evil = '<script>alert("x")</script>|line\nnext'
        for row in payload['candidate_statuses'] + payload['ladder'] + list(payload['anchors'].values()):
            for key in ('identity', 'notes', 'reason', 'source_url', 'source_date', 'effort'):
                row[key] = evil
        # Keep trace references resolvable while testing malicious identifiers.
        payload['selection_trace'] = []
        payload['source_snapshot']['path'] = evil
        payload['caveats'].append(evil)
        md, page = self.views(payload)
        self.assertNotIn('<script>', page)
        self.assertIn(escape(evil), page)
        self.assertIn('&lt;script&gt;', md)
        self.assertIn('&#124;line<br>next', md)
        self.assertNotIn('|line\nnext', md)

    def test_offline_no_active_source_urls(self):
        class ActiveContent(HTMLParser):
            def __init__(self):
                super().__init__()
                self.active = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag in ('script', 'link', 'iframe', 'img', 'object'):
                    if tag != 'script' or attrs.get('id') != 'model-search-script':
                        self.active.append(tag)
                if any(k.startswith('on') for k in attrs):
                    self.active.append('event')
                if 'href' in attrs and not attrs['href'].startswith('#'):
                    self.active.append('unsafe link')
        payload = deepcopy(self.payload)
        for row in payload['candidate_statuses']:
            row['source_url'] = 'javascript:alert(1)'
        _, page = self.views(payload)
        parser = ActiveContent()
        parser.feed(page)
        self.assertEqual(parser.active, [])
        self.assertIn('javascript:alert(1)', page)
        self.assertIn('name="viewport"', page)
        self.assertIn('@media', page)

    def test_rendering_does_not_fetch_select_or_validate_by_recalculation(self):
        targets = ('urllib.request.urlopen', 'bridge.result_v2.calculate_v2',
                   'bridge.result_v2.select_anchors', 'bridge.window_ladder.calculate_ladder',
                   'bridge.window_ladder.select_anchors',
                   'compute_frontier.compute_one_group')
        with ExitStack() as stack:
            for target in targets:
                stack.enter_context(patch(target, side_effect=AssertionError('renderer performed calculation/fetch')))
            md, page = self.views(self.payload)
        self.assertIn('GPT-6 Astra xhigh', md)
        self.assertIn('GPT-6 Astra xhigh', page)


if __name__ == '__main__':
    unittest.main()
