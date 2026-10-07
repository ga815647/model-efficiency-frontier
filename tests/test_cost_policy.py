"""Chat can update a table without weakening the result/source contracts."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from bridge.cost_policy import validate_policy, validate_source_parameters
from bridge.subscription_cost import factor_for
from test_subscription_scenario import PARAMS


class CostPolicyTests(unittest.TestCase):
    def policy(self):
        return json.loads((Path(__file__).resolve().parents[1]/'bridge/site-policy.json').read_text())

    def test_current_table_has_explicit_provenance_for_every_factor(self):
        policy = self.policy()
        self.assertEqual(validate_policy(policy), policy)
        self.assertEqual(policy['formal_parameters'], dict(PARAMS, gpt_factor=17, gemini_factor=3.6, claude_factor=40, grok_factor=5.2, min_score_reason='同版本全候選情境比較'))
        for key in ('gpt_factor', 'gemini_factor', 'claude_factor', 'grok_factor'):
            self.assertEqual(policy['factor_evidence'][key]['basis'], 'user_specified')
            self.assertEqual(policy['factor_evidence'][key]['as_of'], '2026-10-07')
        legacy = {k:v for k,v in policy.items() if k in ('formal_parameters', 'source_refresh')}
        legacy['formal_parameters'] = {k:v for k,v in PARAMS.items() if k not in ('gemini_factor','claude_factor')}
        self.assertEqual(validate_policy(legacy), legacy)

    def test_missing_or_unverifiable_research_evidence_is_rejected(self):
        for change in ('missing', 'unknown', 'date', 'reference', 'research_formula', 'research_source', 'number'):
            policy = deepcopy(self.policy())
            if change == 'missing': del policy['factor_evidence']['gemini_factor']
            elif change == 'unknown': policy['factor_evidence']['gpt_factor']['unexpected'] = True
            elif change == 'number': policy['formal_parameters']['claude_factor'] = True
            else:
                evidence = policy['factor_evidence']['gemini_factor']
                if change == 'date': evidence['as_of'] = '2026-02-30'
                elif change == 'reference': evidence['references'] = []
                else:
                    evidence['basis'] = 'researched'
                    evidence['calculation'] = None if change == 'research_formula' else 'API equivalent / subscription fee'
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_policy(policy)

    def test_new_factors_can_differ_from_snapshot_but_floor_must_be_inherited(self):
        policy = self.policy()
        original = dict(policy['formal_parameters'], gpt_factor=18, grok_factor=16)
        del original['gemini_factor']; del original['claude_factor']
        validate_source_parameters(policy, original)
        for field, value in (('min_score', 10), ('min_score_reason', 'guessed'), ('max_cost', 1)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_source_parameters(policy, dict(original, **{field:value}))

    def test_family_boundaries_and_contributor_never_compound(self):
        for identity, expected in (('Gemini 3 high',6), ('gemini-3 high',6), ('Geminiish high',1),
                                   ('Pre-Gemini high',1), ('Claude Sonnet high',37),
                                   ('Sonnet 4 high',37), ('GPT-6 high',18.9), ('Grokish high',1)):
            row = dict(identity=identity, pricing_plan='AA-public', provider='Other')
            self.assertEqual(factor_for(row, PARAMS), expected, identity)
            row.update(pricing_plan='Contributor', provider='Meta')
            self.assertEqual(factor_for(row, PARAMS),1)


if __name__ == '__main__': unittest.main()
