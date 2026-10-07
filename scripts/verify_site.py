"""Unauthenticated HTTP/Chromium acceptance; works with real Pages or local HTTP.

The supplied URL determines what is verified. Local success never proves Pages.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen


def verify_site(url, expected, output):
    from playwright.sync_api import sync_playwright
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    root=url.rstrip('/')+'/'
    manifest=json.loads(urlopen(urljoin(root,'manifest.json')).read())
    for field in ('request_id','run_id','run_attempt','operation','parameters','source_dates'):
        assert manifest[field]==expected[field], field
    assert manifest['product_commit']==expected['product_sha']
    assert manifest['request_commit']==expected['request_commit_sha']
    fixed=urljoin(root,manifest['result_url'])
    raw=urlopen(urljoin(fixed,'result.json')).read()
    assert json.loads(raw)==expected
    assert hashlib.sha256(raw).hexdigest()==manifest['result_sha256']
    assert json.loads(urlopen(urljoin(fixed,'manifest.json')).read())==manifest
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

    evidence=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for width in (360,390,1280):
            page=browser.new_page(viewport={'width':width,'height':900})
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            response=page.goto(root,wait_until='networkidle'); assert response.status==200
            check_global_source_exits(page)
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
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
                for anchor,row in view['calculation']['anchors'].items():
                    assert page.locator(f'[data-anchor="{anchor}"] .model-name').inner_text()==(row['model'] if row else '從缺')
                page.screenshot(path=str(output/f'{key}-{width}.png'),full_page=True)
                provider_url=page.url
                assert page.goto(urljoin(root,f'providers/{key}/'),wait_until='networkidle').status==200
                check_provider_source_exits(page)
                providers.append(dict(provider=key,url=provider_url,view_sha256=entry['view_sha256'],anchors=True,overflow=False,source_exit_summary=False))
            assert not errors,errors
            evidence.append(dict(width=width,http_status=response.status,search=True,empty=True,keyboard=True,overflow=False,script_errors=errors,providers=providers,source_exits_at_end=True))
            page.close()
        page=browser.new_page(java_script_enabled=False,viewport={'width':360,'height':900})
        assert page.goto(root).status==200
        assert page.locator('[data-anchor]').count()==2
        assert page.locator('#ladder > .table-wrap tbody tr').count()==len(formal)
        page.locator('#search-results > summary').click()
        assert page.locator('[data-search]:visible').count()>=expected['candidate_count']
        browser.close()
    result=dict(url=root,fixed_url=fixed,manifest=manifest,viewports=evidence,no_javascript=True)
    (output/'browser-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',required=True)
    parser.add_argument('--expected-json',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(verify_site(args.url,json.loads(args.expected_json.read_bytes()),args.output),ensure_ascii=False))
