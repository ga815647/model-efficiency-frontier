import html
import re
import unittest
from html.parser import HTMLParser

from bridge.html_report import render_html
from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE
from bridge.result import calculate_snapshot


class HTMLTests(unittest.TestCase):
    def test_v2_policy_dispatches_to_two_anchor_report(self):
        from bridge.result_v2 import calculate_v2
        payload = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)
        page = render_html(payload)
        self.assertIn('最強保留檔', page)
        self.assertEqual(page.count('data-rank="'), 10)
        self.assertNotIn('三檔推薦', page)

    @classmethod
    def setUpClass(cls):
        cls.payload, _ = calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)

    def test_offline_responsive_and_same_picks_order(self):
        page = render_html(self.payload)
        self.assertIn('<!doctype html>', page.lower())
        self.assertIn('<style>', page)
        self.assertIn('name="viewport"', page)
        self.assertIn('@media', page)
        self.assertNotIn('<script', page)
        self.assertNotIn('<link', page)
        self.assertIn('Cost_orig', page)
        self.assertIn('CP_adj', page)
        for row in self.payload['picks'].values():
            self.assertIn(html.escape(row['identity']), page)
        positions = [page.index('data-rank="%s"' % n) for n in range(1, 17)]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(self.payload['ladder']), page.count('data-rank='))
        self.assertIn('Contributor', page)
        self.assertIn('Grok', page)
        self.assertIn('cache-write', page)

    def test_untrusted_strings_escaped_everywhere(self):
        from copy import deepcopy
        payload = deepcopy(self.payload)
        evil = '<img src=x onerror=alert(1)>'
        payload['ladder'][0]['identity'] = evil
        payload['ladder'][0]['notes'] = evil
        payload['candidate_statuses'][0]['reason'] = evil
        payload['caveats'].append(evil)
        payload['picks']['strong']['identity'] = evil
        payload['source_snapshot']['path'] = evil
        page = render_html(payload)
        self.assertNotIn(evil, page)
        self.assertIn(html.escape(evil), page)

    def test_verbose_status_notes_are_collapsed_but_essential_status_visible(self):
        page = render_html(self.payload)
        for family in ('grok', 'contributor'):
            section = page.split(f'data-family="{family}"', 1)[1].split('</section>', 1)[0]
            rows = [r for r in self.payload['candidate_statuses'] if r['is_' + family]]
            self.assertEqual(section.count('<details'), len(rows))
            self.assertEqual(section.count('<summary>原始註記</summary>'), len(rows))
            for row in rows:
                card = next(s for s in section.split('<li>')[1:] if
                            f'<strong>{html.escape(row["identity"], quote=True)}</strong>' in s)
                visible, collapsed = card.split('<details>', 1)
                for key in ('identity', 'status', 'source_url', 'source_date'):
                    self.assertIn(html.escape(str(row[key]), quote=True), visible)
                self.assertIn('Cost_orig', visible)
                self.assertIn('CP_adj', visible)
                self.assertIn(html.escape(row['notes'], quote=True), collapsed)

    def test_cards_table_and_states_match_payload_with_override_factors(self):
        class Sections(HTMLParser):
            def __init__(self):
                super().__init__()
                self.sections = {'card': [], 'tr': [], 'li': []}
                self.stack = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'article' and attrs.get('class') == 'card':
                    self.stack.append(('card', ''))
                elif tag == 'tr' and 'data-rank' in attrs:
                    self.stack.append(('tr', ''))
                elif tag == 'li' and self.stack == []:
                    self.stack.append(('li', ''))
            def handle_data(self, data):
                if self.stack:
                    kind, text = self.stack[-1]
                    self.stack[-1] = (kind, text + data)
            def handle_endtag(self, tag):
                if self.stack and ((tag == 'article' and self.stack[-1][0] == 'card') or
                                   (tag == 'tr' and self.stack[-1][0] == 'tr') or
                                   (tag == 'li' and self.stack[-1][0] == 'li')):
                    kind, text = self.stack.pop()
                    self.sections[kind].append(text)
        params = dict(PARAMETERS, gpt_factor=3, grok_factor=4)
        payload, _ = calculate_snapshot(SNAPSHOT, params, PROVENANCE)
        page = render_html(payload)
        parser = Sections()
        parser.feed(page)
        for card, name in zip(parser.sections['card'], ('strong', 'middle', 'cheap')):
            self.assertIn(payload['picks'][name]['identity'], card)
        self.assertEqual(len(parser.sections['tr']), len(payload['ladder']))
        for line, row in zip(parser.sections['tr'], payload['ladder']):
            self.assertIn(row['identity'], line)
            self.assertIn('×' + str(row['factor']), line)
        self.assertIn('GPT ×3', page)
        self.assertIn('Grok ×4', page)
        self.assertNotIn('GPT ×18 為個人情境', page)
        self.assertNotIn('Grok ×16 非實測', page)
        self.assertEqual(sum(r['is_grok'] for r in payload['candidate_statuses']), 9)
        self.assertEqual(sum(r['is_contributor'] for r in payload['candidate_statuses']), 2)
        for family, flag in (('grok', 'is_grok'), ('contributor', 'is_contributor')):
            section = page.split(f'data-family="{family}"', 1)[1].split('</section>', 1)[0]
            identities = [html.unescape(s) for s in re.findall(r'<li><strong>(.*?)</strong>', section)]
            expected = [r['identity'] for r in payload['candidate_statuses'] if r[flag]]
            self.assertEqual(identities, expected)
            for row in (r for r in payload['candidate_statuses'] if r[flag]):
                self.assertIn('>' + row['status'] + '</span>', section)


if __name__ == '__main__':
    unittest.main()
