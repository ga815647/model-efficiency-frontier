"""Serving opportunities cannot silently grant a subscription benefit."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

from test_bridge_result import SNAPSHOT, PARAMETERS, PROVENANCE, recompute_data
from test_bridge_result_v2 import EXECUTION
from bridge.result import make_envelope, validate_envelope
from bridge.result_v2 import calculate_v2


GATES = ('alias', 'version', 'effort', 'quantization', 'region', 'use_case', 'current_terms')


def fixture():
    context = dict(identity='Example high AA-public published-price', alias='example',
                   version='2026-10-01', effort='high', quantization='bf16',
                   region='ap-southeast-1', use_case='tool_based_coding', current_terms='2026-10-01',
                   serving_provider='example', plan_id='example-lite', route_id='example-route')
    proof = {key: dict(value=context[key], source_ids=['official'],checked_date='2026-10-16',valid_until='2026-10-16') for key in GATES}
    research = dict(schema_version=1, research_id='example-2026-10-16', as_of='2026-10-16',
        provider_id='example', sources=[dict(id='official', url='https://docs.example.com/plan',
        updated_at='2026-10-01', checked_date='2026-10-16', verification='retrieved_official', notes='Official plan.')],
        findings=[dict(label='confirmed', text='Standard price.', source_ids=['official'])])
    raw = (json.dumps(research, ensure_ascii=False, indent=2)+'\n').encode()
    registry = dict(schema_version=1, research=dict(path='bridge/research/example-2026-10-16.json',
        sha256=hashlib.sha256(raw).hexdigest()), providers=[dict(id='example', label='Example Serving')],
        plans=[dict(id='example-lite', provider_id='example', label='Lite', currency='USD', monthly_price=10,
            factor=None, route_ids=['example-route'])],
        routes=[dict(id='example-route', provider_id='example', alias='example', model_owner='Other Lab',
            matches=[dict(model='Example', effort='high', label='potential', reason='Exact backend pending.',
                          identity=context['identity'], proof=proof)])])
    row=dict(identity=context['identity'], model='Example', effort='high', score=40, cost_orig=2,
             cost_adj=2, cp_adj=20, factor=1, is_contributor=False)
    return registry, research, raw, row, context


class ServingPlanTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('bridge.serving_plan'), 'serving-plan registry missing')
        from bridge import serving_plan
        return serving_plan

    def accepted(self, registry, context):
        registry['plans'][0]['factor']=dict(value=10, basis='owner_accepted_scenario',
            accepted_by_owner=True, terms_accepted_by_owner=True, as_of='2026-10-16', valid_until='2026-10-16',context=deepcopy(context))
        registry['routes'][0]['matches'][0]['label']='confirmed'

    def test_unknown_factor_retains_api_only_cost_and_value(self):
        api=self.api(); registry,research,raw,row,context=fixture()
        result=api.evaluate_route(row,registry,'example-lite','example-route',context=context,research=research,as_of='2026-10-16')
        self.assertEqual((result['factor'],result['cost_adj'],result['cp_adj']),(1,2,20))
        self.assertEqual(result['cost_basis'],'api-only')
        self.assertIn('owner_accepted_factor',result['pending_gates'])
        self.assertEqual(row['cost_orig'],2)

    def test_every_gate_and_explicit_terms_acceptance_is_required_independently(self):
        api=self.api(); registry,research,raw,row,context=fixture(); self.accepted(registry,context)
        for gate in GATES:
            with self.subTest(gate=gate):
                bad=deepcopy(registry);bad['routes'][0]['matches'][0]['proof'][gate]=None
                result=api.evaluate_route(row,bad,'example-lite','example-route',context=context,research=research,as_of='2026-10-16')
                self.assertIn(gate,result['pending_gates']);self.assertEqual(result['cost_adj'],2)
                altered=dict(context);altered[gate]='different'
                result=api.evaluate_route(row,registry,'example-lite','example-route',context=altered,research=research,as_of='2026-10-16')
                self.assertEqual(result['factor'],1)
        for key in ('accepted_by_owner','terms_accepted_by_owner'):
            bad=deepcopy(registry);bad['plans'][0]['factor'][key]=False
            self.assertEqual(api.evaluate_route(row,bad,'example-lite','example-route',context=context,research=research,as_of='2026-10-16')['factor'],1)
        result=api.evaluate_route(row,registry,'example-lite','example-route',context=context,research=research,as_of='2026-10-16')
        self.assertEqual((result['factor'],result['cost_adj'],result['cp_adj']),(10,.2,200))

    def test_exact_identity_and_context_cannot_be_replaced_by_similar_model(self):
        api=self.api(); registry,research,raw,row,context=fixture(); self.accepted(registry,context)
        for key,value in (('model','Example Vision'),('effort','max'),('identity','Example high different route')):
            altered=dict(row);altered[key]=value
            result=api.evaluate_route(altered,registry,'example-lite','example-route',context=context,research=research,as_of='2026-10-16')
            self.assertEqual(result['factor'],1)
            self.assertIn('exact_identity',result['pending_gates'])
        self.assertEqual(api.evaluate_route(row,registry,'example-lite','example-route')['factor'],1)

    def test_contributor_never_stacks_and_original_factor_is_not_compounded(self):
        api=self.api(); registry,research,raw,row,context=fixture(); self.accepted(registry,context)
        row.update(factor=17,cost_adj=2/17,cp_adj=340)
        result=api.evaluate_route(row,registry,'example-lite','example-route',context=context,research=research,as_of='2026-10-16')
        self.assertEqual(result['cost_adj'],.2)
        for contributor in (dict(row,is_contributor=True),dict(row,identity=row['identity']+' Contributor')):
            result=api.evaluate_route(contributor,registry,'example-lite','example-route',context=context,research=research,as_of='2026-10-16')
            self.assertEqual((result['factor'],result['cost_adj']),(1,2))

    def test_strict_registry_rejects_unsafe_or_ambiguous_configuration(self):
        api=self.api(); registry,research,raw,row,context=fixture()
        self.assertEqual(api.validate_bundle(json.dumps(registry).encode(),raw)[0],registry)
        mutations=[lambda r:r.update(extra=True),lambda r:r['research'].update(path='../private.json'),
            lambda r:r['research'].update(sha256='f'*64),
            lambda r:r['providers'].append(deepcopy(r['providers'][0])),
            lambda r:r['plans'][0].update(monthly_price=True),
            lambda r:r['plans'][0].update(route_ids=['missing']),
            lambda r:r['routes'][0]['matches'][0]['proof']['version'].update(source_ids=['missing']),
            lambda r:r['routes'][0]['matches'][0]['proof']['version'].update(source_ids=['unretrieved']),
            lambda r:r['routes'].append(deepcopy(r['routes'][0]))]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                bad=deepcopy(registry);mutate(bad)
                with self.assertRaises(ValueError):api.validate_bundle(json.dumps(bad).encode(),raw)
        invalid=deepcopy(research);invalid['sources'][0]['verification']='owner_supplied_not_retrieved'
        invalid['findings'][0]['label']='potential'
        raw_bad=json.dumps(invalid).encode();bad=deepcopy(registry)
        bad['research']['sha256']=hashlib.sha256(raw_bad).hexdigest()
        with self.assertRaisesRegex(ValueError,'unverified_applicability_proof'):
            api.validate_bundle(json.dumps(bad).encode(),raw_bad)

    def test_production_research_lists_twelve_aliases_and_six_unique_potential_matches(self):
        api=self.api(); root=Path(__file__).resolve().parents[1]
        registry_raw=(root/'bridge/serving-plans.json').read_bytes()
        registry=json.loads(registry_raw);research_raw=(root/registry['research']['path']).read_bytes()
        registry,research=api.validate_bundle(registry_raw,research_raw)
        aliases={r['alias'] for r in registry['routes']}
        self.assertEqual(aliases,{'dola-seed-2.0-pro','dola-seed-2.0-lite','dola-seed-2.0-code',
            'bytedance-seed-code','glm-5.3-flash','glm-5.2','glm-5.1','kimi-k2.5','gpt-oss-120b',
            'deepseek-v4.1-flash','deepseek-v4-flash','deepseek-v4-pro'})
        self.assertEqual([p['monthly_price'] for p in registry['plans']],[10,50])
        matches=[m for r in registry['routes'] for m in r['matches']]
        self.assertEqual(len({(m['model'],m['effort']) for m in matches}),6)
        self.assertTrue(all(p['factor'] is None for p in registry['plans']))
        self.assertTrue(all(m['label']=='potential' for m in matches))
        text=json.dumps(research,ensure_ascii=False)
        for detail in ('1900','12000','24000','1200','9000','18000','52/12','dola-seed-2.0-lite','Claude Code','2026-09-30'):
            self.assertIn(detail,text)

    def test_plan_view_deduplicates_plans_without_mutating_results_or_strict_contracts(self):
        api=self.api(); registry,research,raw,row,context=fixture()
        env=make_envelope(recompute_data(),EXECUTION,calculation=calculate_v2(SNAPSHOT,PARAMETERS,PROVENANCE),errors=[])
        candidate=env['candidate_statuses'][0]
        match=registry['routes'][0]['matches'][0]
        match.update(model=candidate['model'],effort=candidate['effort'],identity=candidate['identity'])
        match['proof']['effort']=None
        registry['plans'].append(dict(registry['plans'][0],id='example-pro',label='Pro',monthly_price=50))
        original=deepcopy(env)
        view=api.calculate_plan_view(env,registry,research)
        self.assertEqual(view['potential_candidate_count'],1)
        self.assertEqual(view['candidates'][0]['plan_ids'],['example-lite','example-pro'])
        self.assertEqual(view['candidates'][0]['api_cost_per_task'],candidate['cost_orig'])
        self.assertFalse(view['numeric_benefit_applied'])
        self.assertEqual(env,original);validate_envelope(env)
        for field in ('plan_view','serving_provider','byteplus_factor'):
            bad=deepcopy(env);bad[field]={}
            with self.assertRaises(ValueError):validate_envelope(bad)

    def test_potential_match_dates_and_provider_plan_route_binding_cannot_be_bypassed(self):
        api=self.api();registry,research,raw,row,context=fixture();self.accepted(registry,context)
        self.assertEqual(api.evaluate_route(row,registry,'example-lite','example-route',context=context,research=research,as_of='2026-10-16')['factor'],10)
        bad=deepcopy(registry);bad['routes'][0]['matches'][0]['label']='potential'
        self.assertEqual(api.evaluate_route(row,bad,'example-lite','example-route',context=context,research=research)['factor'],1)
        for key in ('serving_provider','plan_id','route_id'):
            altered=dict(context);altered[key]='different'
            self.assertEqual(api.evaluate_route(row,registry,'example-lite','example-route',context=altered,research=research)['factor'],1)
        for day in ('2026-10-15','2026-10-17'):
            self.assertEqual(api.evaluate_route(row,registry,'example-lite','example-route',context=context,research=research,as_of=day)['factor'],1)
        stale=deepcopy(registry);stale['routes'][0]['matches'][0]['proof']['current_terms']['value']='old-terms'
        with self.assertRaisesRegex(ValueError,'serving_terms_version_mismatch'):
            api.validate_registry(stale,research)

    def test_request_v3_seven_parameter_contract_does_not_gain_serving_fields(self):
        from bridge.request import validate_request, RequestError
        from test_subscription_scenario import PARAMS
        request=dict(recompute_data(),schema_version=3,parameters=dict(PARAMS,byteplus_factor=10))
        with self.assertRaises(RequestError):
            validate_request(request,branch='efficiency-run/'+request['request_id'],
                parent_sha=request['product_sha'],changed_paths=[('A','bridge/requests/'+request['request_id']+'.json')])

    def test_another_provider_or_pricing_identity_is_not_counted_as_an_opportunity(self):
        api=self.api();registry,research,raw,row,context=fixture()
        env=make_envelope(recompute_data(),EXECUTION,calculation=calculate_v2(SNAPSHOT,PARAMETERS,PROVENANCE),errors=[])
        candidate=env['candidate_statuses'][0]
        match=registry['routes'][0]['matches'][0]
        match.update(model=candidate['model'],effort=candidate['effort'],identity=candidate['identity']+' Another-provider Contributor')
        match['proof']['effort']=None
        view=api.calculate_plan_view(env,registry,research)
        self.assertEqual(view['potential_candidate_count'],0)
        self.assertEqual(view['candidates'],[])

    def test_one_applicable_plan_is_counted_once_and_rendered_as_an_accepted_hypothesis(self):
        from bridge.choice_report import render_html
        api=self.api();registry,research,raw,row,context=fixture()
        env=make_envelope(recompute_data(),EXECUTION,calculation=calculate_v2(SNAPSHOT,PARAMETERS,PROVENANCE),errors=[])
        candidate=env['candidate_statuses'][0]
        context.update(identity=candidate['identity'],effort=candidate['effort'])
        match=registry['routes'][0]['matches'][0]
        match.update(model=candidate['model'],effort=candidate['effort'],identity=candidate['identity'])
        match['proof']['effort']['value']=candidate['effort']
        self.accepted(registry,context)
        registry['plans'].append(dict(registry['plans'][0],id='example-pro',label='Pro',monthly_price=50,factor=None))
        view=api.calculate_plan_view(env,registry,research,as_of='2026-10-16')
        self.assertEqual(view['confirmed_candidate_count'],1)
        self.assertEqual(view['potential_candidate_count'],0)
        self.assertTrue(view['numeric_benefit_applied'])
        page=render_html(env,plan_view=view,plan_research=research)
        section=page.split('id="serving-plans"')[1].split('id="calculation"')[0]
        self.assertIn('已驗證適用的假設情境',section)
        self.assertIn('×10',section)
        self.assertIn('data-plan-scenario',section)
        self.assertNotIn('尚未套用數值優惠',section)
        self.assertNotIn('目前沒有使用者接受',section)


if __name__=='__main__':unittest.main()
