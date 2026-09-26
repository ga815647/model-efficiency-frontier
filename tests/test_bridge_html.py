import html
import unittest

from bridge.html_report import render_html
from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE
from bridge.result import calculate_snapshot


class HTMLTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
