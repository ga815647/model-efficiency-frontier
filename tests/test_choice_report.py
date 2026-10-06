"""The public view projects supplied recommendations; it never selects models."""
from copy import deepcopy
from html import escape
import unittest

from bridge.result_v2 import calculate_v2
from bridge.html_report import render_html
from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE


class ChoiceReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)

    def test_conclusion_first_and_audit_disclosed_on_demand(self):
        page = render_html(self.payload)
        self.assertIn('推薦中能力最高', page)
        self.assertIn('推薦中情境成本最低', page)
        self.assertIn('不是所有人的公開 API 售價', page)
        self.assertLess(page.index('推薦中能力最高'), page.index('推薦階梯'))
        self.assertIn('<details id="calculation"', page)
        self.assertIn('id="model-search"', page)
        self.assertIn('本次來源沒有觀測到', page)
        self.assertIn('data-label="情境成本"', page)

    def test_same_and_null_anchors_are_not_backfilled(self):
        payload = deepcopy(self.payload)
        row = payload['anchors']['highest_retained_score']
        payload['anchors']['lowest_retained_cost'] = row
        page = render_html(payload)
        self.assertIn('兩個入口是同一模型與 effort', page)
        payload['anchors'] = dict.fromkeys(payload['anchors'])
        page = render_html(payload)
        cards = page.split('aria-label="保留檔入口"')[1].split('</section>')[0]
        self.assertEqual(cards.count('從缺'), 2)
        self.assertNotIn(row['identity'], cards)

    def test_comparison_route_upgrade_and_hostile_text(self):
        payload = deepcopy(self.payload)
        payload['caveats'].append('來源退出：<img src=x onerror=alert(1)>')
        payload['candidate_statuses'][0]['notes'] = '</script><script>alert(1)</script>'
        page = render_html(payload)
        self.assertIn('僅供比較', page)
        self.assertIn('id="comparison"', page)
        self.assertNotIn('<img src=x', page)
        self.assertIn(escape(payload['candidate_statuses'][0]['notes']), page)
        self.assertLess(page.index('data-family="source-exits"'), page.index('data-family="ladder"'))
        for r in payload['ladder']:
            if r['upgrade']:
                self.assertIn(escape(r['upgrade']['cheaper_identity']), page)

    def test_operation_and_actual_source_date_are_visible(self):
        page = render_html(dict(self.payload, operation='recompute'))
        self.assertIn('recompute', page)
        self.assertIn('固定快照重算，非重新抓取來源', page)
        self.assertIn('2026-09-26', page)


if __name__ == '__main__':
    unittest.main()
