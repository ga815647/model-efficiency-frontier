import unittest
from bridge.view_evidence import source_observations
from bridge.choice_report import render_html
import test_choice_report as choice_fixture


class SourceViewTests(unittest.TestCase):
    def test_retired_source_keeps_canonical_unspecified_effort(self):
        rows=source_observations([dict(name='MiniMax-M2.7',slug='minimax-m2-7')],
             {'reconciliation':{'status_by_slug':{'minimax-m2-7':{'state':'retired','reason':'deprecated'}}}})
        self.assertEqual(rows[0].get('effort'),'unspecified')
        choice_fixture.ChoiceReportTests.setUpClass()
        page=render_html(choice_fixture.ChoiceReportTests.payload,observations=rows)
        self.assertIn('data-search="MiniMax-M2.7 MiniMax-M2.7 unspecified"',page)
        self.assertIn('來源未標示（unspecified）',page)

    def test_ambiguous_source_qualifier_stays_literal_without_inferred_effort(self):
        rows=source_observations([dict(name='Old Model (unknown qualifier)',slug='old')],
             {'reconciliation':{'status_by_slug':{'old':{'state':'retired','reason':'deprecated'}}}})
        self.assertIsNone(rows[0]['effort'])
        self.assertEqual(rows[0]['name'],'Old Model (unknown qualifier)')


if __name__=='__main__':unittest.main()
