"""Provider ladders rerun the same selector on every verified family candidate."""
from copy import deepcopy
import importlib.util
import json
import unittest

from bridge.result import make_envelope
from bridge.result_v2 import calculate_v2
from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE, recompute_data
from test_bridge_result_v2 import EXECUTION


class ProviderViewTests(unittest.TestCase):
    def view(self, envelope, key):
        self.assertIsNotNone(importlib.util.find_spec('bridge.provider_view'), 'provider calculation is missing')
        from bridge.provider_view import calculate_provider_view
        return calculate_provider_view(envelope,key)

    def envelope(self):
        return make_envelope(recompute_data(),EXECUTION,calculation=calculate_v2(SNAPSHOT,PARAMETERS,PROVENANCE),errors=[])

    def test_provider_reselects_all_candidates_without_mutating_full_result(self):
        env=self.envelope(); before=deepcopy(env)
        view=self.view(env,'gpt'); scoped=view['calculation']
        expected=[r for r in env['candidate_statuses'] if r['identity'].startswith('GPT-') and not r['is_contributor']]
        self.assertEqual(scoped['candidate_count'],len(expected))
        self.assertEqual(env,before)
        self.assertTrue(all(r['model'].startswith('GPT-') for r in scoped['candidate_statuses']))
        # A candidate rejected in the all-provider competition can return here.
        old_final={r['identity'] for r in env['ladder']}
        self.assertTrue(any(r['identity'] not in old_final for r in scoped['ladder']))
        for row in scoped['candidate_statuses']:
            original=next(r for r in expected if r['identity']==row['identity'])
            for key in ('score','cost_orig','cost_adj','factor','grade','effort'):
                self.assertEqual(row[key],original[key])
        identities={r['identity'] for r in scoped['ladder']}
        for row in scoped['ladder']:
            self.assertTrue(row['upgrade'] is None or row['upgrade']['cheaper_identity'] in identities)

    def test_all_providers_have_separate_scope_and_claude_keeps_comparison_flags(self):
        env=self.envelope()
        for key in ('gpt','gemini','grok','claude'):
            view=self.view(env,key)
            self.assertEqual(view['provider'],key)
            self.assertEqual(view['kind'],'provider-ladder')
            self.assertEqual(view['schema_version'],1)
            self.assertEqual(view['calculation']['parameters'],env['parameters'])
            if key=='claude':
                self.assertTrue(all(r['comparison_only'] for r in view['calculation']['ladder']))
                self.assertTrue(all(r is None for r in view['calculation']['anchors'].values()))
                self.assertIsNotNone(view['comparison_anchors']['highest_retained_score'])

    def test_floor_can_empty_a_provider_and_invalid_parent_is_rejected(self):
        env=self.envelope()
        env['parameters']['min_score']=100
        # Rebuild an actual validated empty-floor envelope rather than forge it.
        request=recompute_data();request['parameters']=env['parameters']
        empty=make_envelope(request,EXECUTION,calculation=calculate_v2(SNAPSHOT,env['parameters'],PROVENANCE),errors=[])
        view=self.view(empty,'gpt')
        self.assertEqual(view['calculation']['ladder'],[])
        self.assertTrue(all(r is None for r in view['calculation']['anchors'].values()))
        from bridge.provider_view import calculate_provider_view
        with self.assertRaises(ValueError): calculate_provider_view(empty,'../../x')
        invalid=self.envelope();invalid['candidate_statuses'][0]['cost_adj']*=2
        with self.assertRaises(ValueError): calculate_provider_view(invalid,'gpt')


if __name__=='__main__': unittest.main()
