"""Unauthenticated HTTP/Chromium acceptance; works with real Pages or local HTTP.

The supplied URL determines what is verified. Local success never proves Pages.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen

# The documented direct CLI must resolve bridge modules as well as -m usage.
if __package__ in (None, ''):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def verify_site(url, expected, output, *, expected_site_product=None, personal_policy=None):
    from playwright.sync_api import sync_playwright
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    root=url.rstrip('/')+'/'
    manifest=json.loads(urlopen(urljoin(root,'manifest.json')).read())
    if expected_site_product:
        assert manifest['site_product_commit']==expected_site_product, 'site_product_commit'
    for field in ('request_id','run_id','run_attempt','operation','parameters','source_dates'):
        assert manifest[field]==expected[field], field
    assert manifest['product_commit']==expected['product_sha']
    assert manifest['request_commit']==expected['request_commit_sha']
    fixed=urljoin(root,manifest['result_url'])
    raw=urlopen(urljoin(fixed,'result.json')).read()
    assert json.loads(raw)==expected
    assert hashlib.sha256(raw).hexdigest()==manifest['result_sha256']
    assert json.loads(urlopen(urljoin(fixed,'manifest.json')).read())==manifest
    personal=None
    if personal_policy is not None:
        from bridge.personal_cp import validate_choices
        path=f'results/{expected["request_id"]}/{expected["run_id"]}-{expected["run_attempt"]}/result.json'
        choice=validate_choices(personal_policy).get(path)
        assert bool(manifest.get('personal_cp'))==bool(choice), 'personal_choice_missing_or_inherited'
        if choice:
            assert choice['result_sha256']==manifest['result_sha256']
    if 'personal_cp' in manifest:
        from bridge.personal_cp import calculate_personal_cp
        raw_personal=urlopen(urljoin(root,manifest['personal_cp']['view_url'])).read()
        assert hashlib.sha256(raw_personal).hexdigest()==manifest['personal_cp']['view_sha256']
        personal=json.loads(raw_personal)
        assert personal['parent_result_sha256']==manifest['result_sha256']
        assert personal['parent_publication_commit']==manifest['publication_commit']
        for field in ('request_id','run_id','run_attempt'):
            assert personal[field]==expected[field]
        choice=dict(benchmark_identity=personal['benchmark']['identity'],
                    tolerance_multiplier=personal['tolerance_multiplier'],result_sha256=manifest['result_sha256'])
        if personal_policy is not None:
            assert choice==validate_choices(personal_policy)[path]
        recalculated=calculate_personal_cp(expected,choice)
        for key,value in recalculated.items(): assert personal[key]==value,key
    report=urlopen(urljoin(fixed,'report.html')).read()
    assert hashlib.sha256(report).hexdigest()==manifest['report_sha256']
    source_exits=[note for note in expected['caveats'] if note.startswith('來源退出：')]
    def check_global_source_exits(page):
        section=page.locator('[data-family="source-exits"]')
        assert section.count()==int(bool(source_exits))
        if source_exits:
            assert section.locator('li').all_inner_texts()==source_exits
            assert section.evaluate('(node) => node.previousElementSibling.id === "calculation"')
        context=page.locator('#calculation').text_content()
        assert all(note not in context for note in source_exits)

    def check_provider_source_exits(page):
        assert page.locator('[data-family="source-exits"]').count()==0
        content=page.locator('body').text_content()
        assert all(note not in content for note in source_exits)

    def check_personal_cp(page,scope='all'):
        card=page.locator('#personal-cp')
        assert card.count()==int(personal is not None)
        if personal:
            assert page.locator('#recommendations > article > h2').all_inner_texts()==[
                '推薦中能力最高','能力與成本平衡推薦','推薦中情境成本最低']
            row=personal['scopes'][scope]['selected']
            assert card.locator('.model-name').inner_text()==(row['model'] if row else '從缺')
            assert f'≥ {personal["minimum_score"]:.2f}' in card.locator('[data-personal-threshold]').text_content()
            assert personal['benchmark']['model'] in card.locator('[data-personal-benchmark]').text_content()
            assert '並非 AA 的統計誤差' in card.text_content()
            if row:
                assert row['effort'] in card.locator('.effort').inner_text()
                assert card.locator('.metrics b').all_inner_texts()==[f'{row["score"]:.2f}',f'${row["cost_adj"]:.4f}']
            else:
                assert card.locator('.metrics').count()==0
            if scope=='all':
                for key,entry in manifest.get('provider_views',{}).items():
                    summary=page.locator(f'[data-provider-summary="{key}"] [data-personal-summary]')
                    selected=personal['scopes'][key]['selected']
                    assert '能力與成本平衡推薦' in summary.inner_text()
                    assert summary.locator('strong').inner_text()==(
                        selected['model']+' · '+selected['effort'] if selected else '從缺')
                    if selected:
                        assert f'分數 {selected["score"]:.2f}' in summary.inner_text()
                        assert f'${selected["cost_adj"]:.4f}／任務' in summary.inner_text()
                    else:
                        assert '／任務' not in summary.inner_text()

    evidence=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for width in (360,390,1280):
            page=browser.new_page(viewport={'width':width,'height':900})
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            response=page.goto(root,wait_until='networkidle'); assert response.status==200
            check_global_source_exits(page)
            check_personal_cp(page)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
            for key,row in expected['anchors'].items():
                card=page.locator(f'[data-anchor="{key}"]')
                if row:
                    assert card.locator('.model-name').inner_text()==row['model']
                    assert row['effort'] in card.locator('.effort').inner_text()
                    assert card.locator('.metrics b').all_inner_texts()==[f'{row["score"]:.2f}',f'${row["cost_adj"]:.4f}']
                else: assert '從缺' in card.inner_text()
            formal=[r for r in expected['ladder'] if not r['comparison_only']]
            rows=page.locator('#ladder > .table-wrap tbody tr')
            assert rows.count()==len(formal)
            for i,row in enumerate(formal):
                assert rows.nth(i).locator('td strong').inner_text()==row['model']
                assert rows.nth(i).locator('[data-label="能力分數"]').inner_text()==f'{row["score"]:.2f}'
                assert rows.nth(i).locator('[data-label="情境成本"]').inner_text()==f'${row["cost_adj"]:.4f}'
            page.screenshot(path=str(output/f'home-{width}.png'),full_page=True)
            for query in ('Astra max','Sol max'):
                page.locator('#model-search').fill(query)
                assert page.locator('[data-search]:visible').count()>0,query
                for candidate in page.locator('[data-search]:visible').all():
                    assert all(t.lower() in candidate.get_attribute('data-search').lower() for t in query.split())
            page.locator('#model-search').fill('unobserved-model-7c3c5')
            assert page.locator('#search-empty').is_visible()
            page.locator('#model-search').press('Escape');assert page.locator('#model-search').input_value()==''
            summary=page.locator('#calculation > summary');summary.focus();summary.press('Enter')
            assert page.locator('#calculation').get_attribute('open') is not None
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
            assert not errors,errors
            assert page.goto(fixed,wait_until='networkidle').status==200
            check_global_source_exits(page)
            check_personal_cp(page)
            highest=expected['anchors']['highest_retained_score']
            assert page.locator('[data-anchor="highest_retained_score"] .model-name').inner_text()==(highest['model'] if highest else '從缺')
            providers=[]
            for key,entry in manifest.get('provider_views',{}).items():
                view_raw=urlopen(urljoin(root,entry['view_url'])).read()
                assert hashlib.sha256(view_raw).hexdigest()==entry['view_sha256']
                view=json.loads(view_raw)
                assert view['parent_result_sha256']==manifest['result_sha256']
                assert view['parent_publication_commit']==manifest['publication_commit']
                assert view['provider']==key and view['kind']=='provider-ladder'
                for field in ('parameters','source_dates','request_id','run_id','run_attempt'):
                    assert view['calculation'][field]==expected[field]
                scoped_manifest=json.loads(urlopen(urljoin(root,entry['url']+'manifest.json')).read())
                assert scoped_manifest['selection_scope']==key
                assert scoped_manifest['provider_view_sha256']==entry['view_sha256']
                page.locator(f'#provider-chooser [data-provider="{key}"]').focus()
                page.locator(f'#provider-chooser [data-provider="{key}"]').press('Enter')
                page.wait_for_load_state('networkidle')
                assert page.url==urljoin(root,entry['url'])
                assert page.locator('#effort-filter').count()==0
                assert page.locator('[data-selection-scope]').get_attribute('data-selection-scope')==key
                check_provider_source_exits(page)
                check_personal_cp(page,key)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
                for anchor,row in view['calculation']['anchors'].items():
                    assert page.locator(f'[data-anchor="{anchor}"] .model-name').inner_text()==(row['model'] if row else '從缺')
                page.screenshot(path=str(output/f'{key}-{width}.png'),full_page=True)
                provider_url=page.url
                assert page.goto(urljoin(root,f'providers/{key}/'),wait_until='networkidle').status==200
                check_provider_source_exits(page)
                check_personal_cp(page,key)
                providers.append(dict(provider=key,url=provider_url,view_sha256=entry['view_sha256'],anchors=True,overflow=False,source_exit_summary=False))
            assert not errors,errors
            evidence.append(dict(width=width,http_status=response.status,search=True,empty=True,keyboard=True,overflow=False,script_errors=errors,providers=providers,source_exits_at_end=True))
            page.close()
        page=browser.new_page(java_script_enabled=False,viewport={'width':360,'height':900})
        assert page.goto(root).status==200
        check_personal_cp(page)
        assert page.locator('[data-anchor]').count()==2
        assert page.locator('#ladder > .table-wrap tbody tr').count()==len(formal)
        page.locator('#search-results > summary').click()
        assert page.locator('[data-search]:visible').count()>=expected['candidate_count']
        for key in manifest.get('provider_views',{}):
            assert page.goto(urljoin(root,f'providers/{key}/')).status==200
            check_personal_cp(page,key)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
        browser.close()
    result=dict(url=root,fixed_url=fixed,manifest=manifest,viewports=evidence,no_javascript=True,personal_cp=personal)
    (output/'browser-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',required=True)
    parser.add_argument('--expected-json',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expected-site-product')
    parser.add_argument('--personal-policy',type=Path)
    args=parser.parse_args()
    print(json.dumps(verify_site(args.url,json.loads(args.expected_json.read_bytes()),args.output,
        expected_site_product=args.expected_site_product,
        personal_policy=json.loads(args.personal_policy.read_bytes()) if args.personal_policy else None),ensure_ascii=False))
