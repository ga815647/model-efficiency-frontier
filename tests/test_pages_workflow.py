from copy import deepcopy
from pathlib import Path
import unittest

from bridge import site


class PagesTriggerTests(unittest.TestCase):
    def test_upstream_requires_successful_same_repo_push_and_exact_workflow(self):
        run=dict(id=123,run_attempt=2,event='push',status='completed',conclusion='success',
                 path='.github/workflows/chat-execution.yml',head_sha='a'*40,
                 head_branch='efficiency-run/834cf811-f1ca-467e-a72f-291fd0195f61',
                 repository={'full_name':'ga815647/model-efficiency-frontier'},
                 head_repository={'full_name':'ga815647/model-efficiency-frontier'})
        self.assertEqual(site.validate_upstream(run,'ga815647/model-efficiency-frontier'),('123',2,'a'*40))
        for key,value in [('event','pull_request'),('conclusion','failure'),('path','.github/workflows/other.yml'),
                          ('head_branch','main'),('repository',{'full_name':'attacker/fork'}),
                          ('head_repository',{'full_name':'attacker/fork'})]:
            wrong=deepcopy(run); wrong[key]=value
            with self.subTest(key=key), self.assertRaises(site.SiteError):
                site.validate_upstream(wrong,'ga815647/model-efficiency-frontier')

    def test_workflows_keep_external_prs_away_from_publish_and_deploy(self):
        import yaml
        root=Path(__file__).resolve().parents[1]
        pages=yaml.load((root/'.github/workflows/pages.yml').read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(set(pages['on']),{'workflow_run','workflow_dispatch'})
        self.assertEqual(pages['on']['workflow_run']['workflows'],['Chat execution','Product CI'])
        build=pages['jobs']['build']
        for guard in ("conclusion == 'success'", "event == 'push'",
                      'repository.full_name == github.repository',
                      'head_repository.full_name == github.repository',
                      "name == 'Product CI'", "head_branch == 'main'",
                      'head_sha == github.sha', "path == '.github/workflows/product-ci.yml'"):
            self.assertIn(guard,build['if'])
        checkout=build['steps'][0]['with']['ref']
        self.assertIn("name == 'Product CI'",checkout)
        self.assertIn('workflow_run.head_sha',checkout)
        current=next(step for step in build['steps'] if step.get('name')=='Reject superseded product CI')
        self.assertIn('refs/remotes/origin/main',current['run'])
        self.assertIn("name == 'Product CI'",current['if'])
        for name in ('Read authenticated upstream run','Validate upstream identity'):
            step=next(step for step in build['steps'] if step.get('name')==name)
            self.assertIn("name == 'Chat execution'",step['if'])
        upload=next(step for step in build['steps'] if step.get('uses','').startswith('actions/upload-pages-artifact@'))
        deploy=pages['jobs']['deploy']['steps'][0]
        artifact='github-pages-${{ github.run_id }}-${{ github.run_attempt }}'
        self.assertEqual(upload['with']['name'],artifact)
        self.assertEqual(deploy['with']['artifact_name'],artifact)
        self.assertEqual(pages['permissions'],{'contents':'read'})
        self.assertEqual(pages['jobs']['deploy']['permissions'],{'pages':'write','id-token':'write'})
        self.assertIn('PUBLICATION_REVIEW_PASSED',pages['jobs']['deploy']['if'])
        self.assertEqual(pages['concurrency']['cancel-in-progress'],'false')
        ci=yaml.load((root/'.github/workflows/product-ci.yml').read_text(),Loader=yaml.BaseLoader)
        self.assertIn('pull_request',ci['on'])
        self.assertNotIn('pull_request_target',ci['on'])
        self.assertEqual(ci['permissions'],{'contents':'read'})
        execution=yaml.load((root/'.github/workflows/chat-execution.yml').read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(set(execution['on']),{'push'})
        self.assertEqual(execution['on']['push']['branches'],['efficiency-run/**'])


if __name__=='__main__': unittest.main()
