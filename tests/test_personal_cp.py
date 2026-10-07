"""Personal acceptance threshold uses all usable candidates, independently of LADDER."""
from copy import deepcopy
import unittest

from bridge.personal_cp import calculate_personal_cp, validate_choices
from bridge.provider_view import PROVIDERS
from bridge.result import make_envelope
from bridge.result_v4 import calculate_v4
from test_bridge_result import SNAPSHOT, PROVENANCE, recompute_data
from test_bridge_result_v2 import EXECUTION
from test_subscription_scenario import PARAMS


class PersonalCPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.envelope = make_envelope(dict(recompute_data(), schema_version=3, parameters=PARAMS),
            EXECUTION, calculation=calculate_v4(SNAPSHOT, PARAMS, PROVENANCE), errors=[])
        cls.benchmark = next(r for r in cls.envelope['candidate_statuses']
                             if r['model']=='GPT-6 Sol' and r['effort']=='max')

    def choice(self, multiplier=1):
        return dict(benchmark_identity=self.benchmark['identity'], tolerance_multiplier=multiplier,
                    result_sha256='a'*64)

    def test_uses_full_candidates_same_threshold_and_never_mutates_result(self):
        before = deepcopy(self.envelope)
        view = calculate_personal_cp(self.envelope, self.choice())
        threshold = self.benchmark['score'] - self.envelope['eps']['score']
        self.assertEqual(view['minimum_score'], threshold)
        for scope in ('all', *PROVIDERS):
            self.assertEqual(view['scopes'][scope]['minimum_score'], threshold)
        self.assertEqual(self.envelope, before)
        # Sol max is cut by LADDER in this fixture, but can be a personal benchmark.
        self.assertNotEqual(self.benchmark['status'], 'final')
        winner = view['scopes']['all']['selected']
        self.assertGreaterEqual(winner['score'], threshold)

    def test_boundary_is_inclusive_and_no_upper_bound_or_hardcoded_winner(self):
        from bridge.personal_cp import select_candidate
        def row(identity, score, cp, cost=1):
            return dict(identity=identity, model=identity, effort='high', score=score,
                        cp_adj=cp, cost_adj=cost, comparison_only=False)
        rows = [row('below', 49-1e-10, 999), row('boundary',49,20), row('above',70,30)]
        self.assertEqual(select_candidate(rows,49,0,None)['identity'], 'above')
        self.assertEqual(select_candidate(rows[:2],49,0,None)['identity'], 'boundary')
        self.assertIsNone(select_candidate(rows,71,0,None))
        self.assertIsNone(select_candidate([],49,0,None))

    def test_ties_are_deterministic_and_existing_eligibility_applies(self):
        from bridge.personal_cp import select_candidate
        rows = [dict(identity=i,model=i,effort='high',score=s,cp_adj=10,cost_adj=c,
                     comparison_only=False) for i,s,c in [('z',50,2),('b',51,2),('a',51,1)]]
        for pool in (rows, list(reversed(rows))):
            self.assertEqual(select_candidate(pool,49,0,None)['identity'],'a')
        rows[1].update(score=51,cost_adj=1)
        self.assertEqual(select_candidate(rows,49,0,None)['identity'],'a')
        rows[2]['comparison_only']=True
        self.assertEqual(select_candidate(rows,49,0,1)['identity'],'b')
        self.assertIsNone(select_candidate(rows,49,52,None))
        unavailable = dict(rows[0],identity='Muse Spark 1.3 max Meta Contributor',
                           model='Muse Spark 1.3',effort='max',cp_adj=10000)
        self.assertIsNone(select_candidate([unavailable],49,0,None))

    def test_zero_tolerance_allows_benchmark_and_empty_provider_stays_empty(self):
        view=calculate_personal_cp(self.envelope,self.choice(0))
        self.assertEqual(view['minimum_score'],self.benchmark['score'])
        self.assertIn(self.benchmark['identity'],view['scopes']['gpt']['qualified_identities'])
        self.assertIsNone(view['scopes']['grok']['selected'])

    def test_choice_validation_rejects_ambiguous_or_unusable_input(self):
        path='results/'+self.envelope['request_id']+'/123-1/result.json'
        policy=dict(schema_version=1,choices={path:self.choice()})
        self.assertEqual(validate_choices(policy),policy['choices'])
        for value in (True, -1, float('nan'), float('inf'), '1'):
            bad=deepcopy(policy);bad['choices'][path]['tolerance_multiplier']=value
            with self.assertRaises(ValueError): validate_choices(bad)
        for field,value in [('result_sha256','oops'),('benchmark_identity','')]:
            bad=deepcopy(policy);bad['choices'][path][field]=value
            with self.assertRaises(ValueError): validate_choices(bad)
        bad=deepcopy(policy);bad['unexpected']=1
        with self.assertRaises(ValueError): validate_choices(bad)
        bad=deepcopy(policy);bad['choices']={'../result.json':self.choice()}
        with self.assertRaises(ValueError): validate_choices(bad)
        with self.assertRaises(ValueError):
            calculate_personal_cp(self.envelope,dict(self.choice(),benchmark_identity='not in snapshot'))
        with self.assertRaises(ValueError):
            calculate_personal_cp(self.envelope,dict(self.choice(),tolerance_multiplier=1e308))


if __name__=='__main__': unittest.main()
