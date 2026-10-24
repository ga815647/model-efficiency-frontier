"""2026-10-24 Kimi subscription research remains non-numeric until independently verified."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from bridge.kimi_plan import validate_kimi_research
from bridge.choice_report import render_html
from scripts.verify_site import validate_kimi_payload


ROOT=Path(__file__).resolve().parents[1]
RAW=(ROOT/'bridge/kimi-plans.json').read_bytes()


def encode(data):
    return (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()


class KimiResearchTests(unittest.TestCase):
    def test_current_pricing_and_model_are_source_backed_without_factor(self):
        data=validate_kimi_research(RAW)
        self.assertEqual(data['research_id'],'kimi-international-membership-2026-10-24-v1')
        self.assertEqual([(x['label'],x['monthly_usd']) for x in data['plans']],
                         [('Plus',19),('Pro',39),('Max',99),('Ultra',199)])
        self.assertEqual([x['annual_total_usd'] for x in data['plans']],[180,372,948,1908])
        self.assertEqual([x['relative_agent_credits'] for x in data['plans']],[1,2,5,10])
        self.assertEqual(data['model']['released_on'],'2026-10-23')
        self.assertEqual(data['model']['benchmark_score'],55)
        self.assertIsNone(data['factor'])
        self.assertIsNone(data['quotas']['published_api_equivalent_budget_usd'])
        self.assertTrue(data['quotas']['rolling_five_hour_window'])
        self.assertFalse(data['quotas']['weekly_limit_new_plans'])
        self.assertTrue(all(x['verification'].startswith('retrieved_') for x in data['sources']))

    def test_rejects_inferred_factor_or_altered_prices(self):
        baseline=validate_kimi_research(RAW)
        mutations=[
            lambda d:d.update(factor=5),
            lambda d:d.update(factor_basis='researched'),
            lambda d:d['quotas'].update(published_api_equivalent_budget_usd=100),
            lambda d:d['plans'][0].update(monthly_usd=0),
            lambda d:d['plans'][1].update(annual_monthly_equivalent_usd=999),
            lambda d:d['plans'][1].update(highspeed=False),
            lambda d:d['plans'][3].update(relative_agent_credits=100),
            lambda d:d['model'].update(released_on='2026-10-25'),
            lambda d:d['sources'][0].update(url='http://bad.example'),
            lambda d:d['sources'][0].update(verification='owner_supplied_not_retrieved'),
            lambda d:d['sources'][0].update(checked_date='2026-10-25'),
            lambda d:d['sources'].append(deepcopy(d['sources'][0])),
            lambda d:d.update(secret='unwanted'),
            lambda d:d['plans'].pop(),
        ]
        for change in mutations:
            candidate=deepcopy(baseline);change(candidate)
            with self.subTest(change=str(change)),self.assertRaises(ValueError):
                validate_kimi_research(encode(candidate))

    def test_public_exact_bytes_are_not_redefined_by_a_matching_rebound_manifest(self):
        research=validate_kimi_research(RAW)
        result_url='/model-efficiency-frontier/results/00000000-0000-4000-8000-000000000000/123-1/'
        manifest=dict(result_url=result_url,kimi_plans=dict(
            research_id=research['research_id'],research_url=result_url+'kimi-plans.json',
            research_sha256=hashlib.sha256(RAW).hexdigest()))
        self.assertEqual(validate_kimi_payload(manifest,RAW,trusted_raw=RAW),research)
        mutated=deepcopy(research);mutated['plans'][0]['monthly_usd']=1
        altered=encode(mutated)
        manifest['kimi_plans']['research_sha256']=hashlib.sha256(altered).hexdigest()
        with self.assertRaisesRegex(AssertionError,'trusted_kimi_research'):
            validate_kimi_payload(manifest,altered,trusted_raw=RAW)

    def test_escaped_html_cards_only_report_study_not_subscription_picks(self):
        from bridge.choice_report import _kimi_plans
        html=_kimi_plans(validate_kimi_research(RAW))
        self.assertEqual(html.count('data-kimi-plan='),4)
        self.assertIn('倍率未知，不進正式 LADDER',html)
        self.assertIn('不能混入 2026-10-07 固定快照',html)
        self.assertIn('K3.1 Pro Highspeed 可用',html)
        self.assertIn('www.kimi.com',html)
        self.assertNotIn('×55',html)


if __name__=='__main__':
    unittest.main()
