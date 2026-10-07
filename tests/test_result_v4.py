"""New eligibility is versioned; historical comparison-only contracts stay exact."""
from copy import deepcopy
import importlib.util
import unittest
from bridge.result import make_envelope,validate_envelope
from bridge.request import validate_request,RequestError
from test_bridge_result import SNAPSHOT,PROVENANCE,recompute_data
from test_bridge_result_v2 import EXECUTION
from test_subscription_scenario import PARAMS


class ResultV4Tests(unittest.TestCase):
    def calculate(self):
        self.assertIsNotNone(importlib.util.find_spec('bridge.result_v4'),'v4 calculation missing')
        from bridge.result_v4 import calculate_v4
        return calculate_v4(SNAPSHOT,PARAMS,PROVENANCE)

    def envelope(self):
        return make_envelope(dict(recompute_data(),schema_version=3,parameters=PARAMS),EXECUTION,calculation=self.calculate(),errors=[])

    def test_new_request_accepts_same_seven_parameters(self):
        request=dict(recompute_data(),schema_version=3,parameters=PARAMS)
        try:
            validated=validate_request(request,branch='efficiency-run/'+request['request_id'],parent_sha=request['product_sha'],changed_paths=[('A','bridge/requests/'+request['request_id']+'.json')])
        except RequestError as exc:
            self.fail('new request rejected: '+str(exc))
        self.assertEqual(validated,request)

    def test_claude_is_recommended_only_in_new_eligibility_version(self):
        from bridge.result_v3 import calculate_v3
        old=calculate_v3(SNAPSHOT,PARAMS,PROVENANCE)
        new=self.envelope()
        self.assertEqual(new['schema_version'],4)
        self.assertEqual(new['eligibility_policy'],'all-providers-v1')
        self.assertEqual(validate_envelope(new),new)
        self.assertEqual(new['chain_identities'],old['chain_identities'])
        self.assertEqual(new['selection_trace'],old['selection_trace'])
        self.assertTrue(any(r['comparison_only'] for r in old['ladder']))
        self.assertTrue(all(not r['comparison_only'] for r in new['candidate_statuses']))
        self.assertEqual(new['anchors']['highest_retained_score'],new['ladder'][0])
        for altered in ('version','missing','policy','flag'):
            env=deepcopy(new)
            if altered=='version':env['schema_version']=3
            elif altered=='missing':del env['eligibility_policy']
            elif altered=='policy':env['eligibility_policy']='guess'
            else:env['candidate_statuses'][0]['comparison_only']=True
            with self.subTest(altered=altered),self.assertRaises(ValueError):validate_envelope(env)

    def test_provider_claude_has_real_anchors_and_upgrades(self):
        from bridge.provider_view import calculate_provider_view
        view=calculate_provider_view(self.envelope(),'claude')['calculation']
        self.assertIsNotNone(view['anchors']['highest_retained_score'])
        self.assertIsNotNone(view['anchors']['lowest_retained_cost'])
        self.assertTrue(all(not r['comparison_only'] for r in view['ladder']))
        self.assertTrue(all(r['upgrade'] for r in view['ladder'][:-1]))

    def test_formal_v4_does_not_accept_older_eligibility_as_home(self):
        from bridge.site import select_home,SiteError
        from bridge.result_v3 import calculate_v3
        old=make_envelope(dict(recompute_data(),schema_version=2,parameters=PARAMS),EXECUTION,
                          calculation=calculate_v3(SNAPSHOT,PARAMS,PROVENANCE),errors=[])
        old['created_at']='2099-01-01T00:00:00Z'
        latest={'envelope':self.envelope()}
        self.assertIs(select_home([{'envelope':old},latest],PARAMS,4),latest)
        with self.assertRaises(SiteError):select_home([{'envelope':old}],PARAMS,4)

    def test_request_bridge_publication_and_readback_keep_v4_identity(self):
        import test_bridge_runner as fixture_module
        import test_bridge_publish as publish_module
        from bridge.publish import publish_result
        from bridge.site import load_record
        fixture=fixture_module.RunnerTests('test_approved_historical_adapter_is_pinned_and_html_matches')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        request,execution=fixture.submit(schema_version=3,params=PARAMS)
        envelope,output=fixture.run_request(request,execution)
        self.assertEqual(envelope['status'],'success',envelope['errors'])
        self.assertEqual(envelope['schema_version'],4)
        self.assertNotIn('僅供比較',(output/'report.html').read_text())
        publisher=publish_module.PublishTests();publisher.setUp();self.addCleanup(publisher.doCleanups)
        publication=publish_result(output,remote=str(publisher.remote),source_repository=fixture.repo,trusted_product_sha=fixture.product)
        fixture_module.git(fixture.repo,'fetch','-q',str(publisher.remote),'refs/heads/results:refs/heads/results')
        record=load_record(fixture.repo,publication,f'results/{request["request_id"]}/123-1/result.json')
        self.assertEqual(record['envelope'],envelope)

    def test_invalid_v3_request_gets_v4_failure_without_success_fields(self):
        import test_bridge_runner as fixture_module
        fixture=fixture_module.RunnerTests('test_approved_historical_adapter_is_pinned_and_html_matches')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        request,execution=fixture.submit(schema_version=3,params=dict(PARAMS,claude_factor=True))
        envelope,output=fixture.run_request(request,execution)
        self.assertEqual(envelope['schema_version'],4)
        self.assertEqual(envelope['status'],'failed')
        self.assertNotIn('eligibility_policy',envelope)
        self.assertFalse((output/'report.html').exists())


if __name__=='__main__':unittest.main()
