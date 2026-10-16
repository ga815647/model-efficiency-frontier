"""Published serving sidecars must independently reproduce their bound view."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from bridge import site
import test_site as site_fixtures


class ServingVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        site_fixtures.SiteTests.setUpClass()
        spec=importlib.util.spec_from_file_location('verify_site',Path(__file__).resolve().parents[1]/'scripts/verify_site.py')
        cls.verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.verifier)

    def test_independent_verifier_rejects_hash_rebinding_and_view_number_forgery(self):
        self.assertTrue(hasattr(self.verifier,'validate_serving_payloads'),'serving sidecar verifier missing')
        root=Path(__file__).resolve().parents[1]
        registry_raw=(root/'bridge/serving-plans.json').read_bytes()
        research_raw=(root/json.loads(registry_raw)['research']['path']).read_bytes()
        record=site_fixtures.SiteTests().record()
        with tempfile.TemporaryDirectory() as d:
            manifest=site.write_site([record],Path(d)/'site',formal_parameters=record['envelope']['parameters'],
                site_product_commit='d'*40,base_path='/demo/',serving_registry=registry_raw,serving_research=research_raw)
            view_raw=(Path(d)/'site/plan-view.json').read_bytes()
            validated=self.verifier.validate_serving_payloads(manifest,record['envelope'],registry_raw,research_raw,view_raw)
            self.assertFalse(validated['numeric_benefit_applied'])
            for registry_bytes,research_bytes in ((registry_raw+b' ',research_raw),(registry_raw,research_raw+b' ')):
                with self.assertRaises((AssertionError,ValueError)):
                    self.verifier.validate_serving_payloads(manifest,record['envelope'],registry_bytes,research_bytes,view_raw)
            forged=json.loads(view_raw);forged['potential_candidate_count']+=1
            forged_raw=json.dumps(forged).encode();altered=deepcopy(manifest)
            altered['serving_plans']['view_sha256']=hashlib.sha256(forged_raw).hexdigest()
            with self.assertRaises((AssertionError,ValueError)):
                self.verifier.validate_serving_payloads(altered,record['envelope'],registry_raw,research_raw,forged_raw)
            altered=deepcopy(manifest);altered['serving_plans']['research_url']='https://example.test/secret'
            with self.assertRaises((AssertionError,ValueError)):
                self.verifier.validate_serving_payloads(altered,record['envelope'],registry_raw,research_raw,view_raw)

    def test_coherently_rebound_public_bundle_cannot_change_trusted_product_research(self):
        from bridge.serving_plan import calculate_plan_view
        root=Path(__file__).resolve().parents[1]
        registry=json.loads((root/'bridge/serving-plans.json').read_bytes())
        research=json.loads((root/registry['research']['path']).read_bytes())
        record=site_fixtures.SiteTests().record()
        with tempfile.TemporaryDirectory() as d:
            registry_raw=json.dumps(registry).encode();research_raw=(root/registry['research']['path']).read_bytes()
            # Construct an ordinary publication first with the approved bytes.
            approved_raw=(root/'bridge/serving-plans.json').read_bytes()
            manifest=site.write_site([record],Path(d)/'site',formal_parameters=record['envelope']['parameters'],
                site_product_commit='d'*40,base_path='/demo/',serving_registry=approved_raw,serving_research=research_raw)
            research['findings'][0]['text']='Attacker replacement with all downstream hashes updated.'
            research_raw=json.dumps(research).encode()
            registry['research']['sha256']=hashlib.sha256(research_raw).hexdigest()
            registry_raw=json.dumps(registry).encode()
            view=calculate_plan_view(record['envelope'],registry,research)
            view.update(parent_result_sha256=manifest['result_sha256'],parent_publication_commit=manifest['publication_commit'],
                        registry_sha256=hashlib.sha256(registry_raw).hexdigest(),research_sha256=hashlib.sha256(research_raw).hexdigest())
            view_raw=json.dumps(view).encode()
            for key,raw in (('registry',registry_raw),('research',research_raw),('view',view_raw)):
                manifest['serving_plans'][key+'_sha256']=hashlib.sha256(raw).hexdigest()
            with self.assertRaisesRegex((AssertionError,ValueError),'trusted_serving'):
                self.verifier.validate_serving_payloads(manifest,record['envelope'],registry_raw,research_raw,view_raw)


if __name__=='__main__':unittest.main()
