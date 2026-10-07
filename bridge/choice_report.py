"""Progressively enhanced, offline model chooser. No acquisition or selection."""
from html import escape

from .window_report import _context, _html, _metadata, _number, _source_exits, _tables, _upgrade

WEBSITE_VERSION = '1.2.1'

CSS = '''
:root{color-scheme:light;--ink:#19352f;--muted:#52675f;--line:#d9e2d9;--accent:#14614d;--paper:#fffefa;--bg:#f4f5ee}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--ink);background:var(--bg);font:16px/1.7 system-ui,-apple-system,sans-serif}main{max-width:1120px;margin:auto;padding:28px 24px 70px}h1{font-size:clamp(2.1rem,5vw,3.8rem);letter-spacing:-.05em;line-height:1.17;margin:28px 0 16px}h2{font-size:1.45rem;line-height:1.4;margin:0 0 16px}h3{font-size:1.1rem}p{margin:.6em 0}a{color:var(--accent);text-underline-offset:4px}a,summary,input{touch-action:manipulation}a:focus-visible,summary:focus-visible,input:focus-visible{outline:3px solid #bd702a;outline-offset:4px}nav{display:flex;flex-wrap:wrap;gap:12px 24px;font-size:.9rem}nav a{padding:8px 0}.eyebrow{font-size:.8rem;letter-spacing:.13em;font-weight:700;color:var(--accent)}.muted,small,.intro{color:var(--muted)}.intro{max-width:750px}.stamp{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}.stamp span,.badge{border-radius:6px;padding:3px 9px;background:#e6eddf;font-size:.8rem}.panel,.card{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:26px;min-width:0;overflow-wrap:anywhere}.panel{margin:24px 0}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:28px 0 12px}.card h2{font-size:.9rem;color:var(--accent);margin-bottom:18px}.model-name{display:block;font-size:1.5rem;line-height:1.4}.effort{display:block;font-size:.9rem;color:var(--muted);margin:4px 0 18px}.metrics{display:flex;gap:32px;flex-wrap:wrap;margin:18px 0}.metrics b{font-size:1.35rem;display:block;font-variant-numeric:tabular-nums}.metrics span{font-size:.8rem;color:var(--muted)}.note{font-size:.88rem;color:var(--muted)}summary{cursor:pointer;padding:8px 0;font-weight:600;color:var(--accent)}details[open]>summary{margin-bottom:16px}.table-wrap{overflow-x:auto;max-width:100%}table{width:100%;border-collapse:collapse;font-size:.9rem}th,td{padding:18px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{font-size:.8rem;color:var(--muted)}.chooser th:first-child{width:29%}.chooser th:last-child{width:35%}.chooser td strong{display:block}.chooser td small{display:block}.chooser .effort{margin:0}.chooser .number{white-space:nowrap;font-variant-numeric:tabular-nums}.chooser details{font-size:.8rem}.audit table{min-width:1100px}.audit td{max-width:360px}.audit td:last-child{min-width:220px}.candidate-list{list-style:none;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.candidate-list li{border:1px solid var(--line);border-radius:12px;padding:20px;min-width:0}.candidate-list h3{margin:0 0 8px}.candidate-list p{font-size:.9rem}.candidate-list small{display:block}.search-control label{display:block;font-weight:600}.search-control input{font:inherit;width:100%;border:1px solid var(--muted);border-radius:10px;padding:13px 16px;margin:8px 0}.search-control{margin-bottom:16px}.source-meta{font-size:.85rem;overflow-wrap:anywhere}.source-meta code{word-break:break-all}.skip{position:absolute;left:16px;top:-100px}.skip:focus{top:16px;background:white;padding:10px}.exit{border-left:4px solid #b47b37}.footer{font-size:.8rem;color:var(--muted);margin-top:40px}[hidden]{display:none!important}
@media(max-width:700px){main{padding:20px 16px 48px}.cards,.candidate-list{grid-template-columns:1fr}.panel,.card{padding:22px 18px}h1{margin-top:22px}.chooser,.chooser tbody,.chooser tr,.chooser td{display:block;width:100%}.chooser thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}.chooser tr{border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}.chooser td{padding:6px 0;border:none}.chooser td[data-label]:before{content:attr(data-label);display:inline-block;color:var(--muted);font-size:.8rem;min-width:85px}.chooser td:first-child{padding-bottom:12px}.chooser td:last-child{padding-top:12px;border-top:1px solid var(--line);margin-top:8px}.chooser .number{white-space:normal}.table-wrap:has(.chooser){overflow:visible}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
.provider-chooser{margin:18px 0;gap:8px}.provider-chooser a{padding:9px 14px;border:1px solid var(--line);border-radius:9px;background:var(--paper)}.provider-chooser a[aria-current=page]{background:var(--accent);color:white}.provider-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.provider-cards article{border:1px solid var(--line);border-radius:12px;padding:20px;min-width:0}.provider-cards h3{margin:0 0 12px}.provider-cards strong{display:block;overflow-wrap:anywhere}@media(max-width:700px){.provider-cards{grid-template-columns:1fr}}
'''

SEARCH_JS = '''
(() => {
 const input = document.getElementById('model-search');
 if (!input) return;
 const items = [...document.querySelectorAll('[data-search]')];
 const status = document.getElementById('search-status');
 const empty = document.getElementById('search-empty');
 const list = document.getElementById('search-results');
 document.getElementById('search-control').hidden = false;
 const fold = text => text.normalize('NFKC').toLocaleLowerCase().trim();
 function search() {
   const tokens = fold(input.value).split(/\\s+/).filter(Boolean);
   let count = 0;
   for (const item of items) {
     item.hidden = !tokens.length || !tokens.every(t => fold(item.dataset.search).includes(t));
     if (!item.hidden) count++;
   }
   list.hidden = !tokens.length;
   list.open = Boolean(tokens.length);
   empty.hidden = !tokens.length || count > 0;
   status.textContent = tokens.length ? `找到 ${count} 個模型／effort 記錄` : '輸入模型名稱與 effort，查看本次來源狀態。';
 }
 input.addEventListener('input', search);
 input.addEventListener('keydown', event => { if (event.key === 'Escape') {input.value = ''; search();} });
 search();
})();
'''


def _metrics(row):
    return (f'<div class="metrics"><div><b>{row["score"]:.2f}</b><span>能力分數</span></div>'
            f'<div><b>${row["cost_adj"]:.4f}</b><span>情境成本／任務</span></div></div>')


def _row_details(row):
    return (f'<details><summary>成本與來源細節 · GRADE-{_html(row["grade"])}</summary>'
            f'<p>{_html(row["identity"])}</p><p>Cost_orig ${_number(row["cost_orig"])} · factor ×{_html(row["factor"])}'
            f' · Cost_adj ${_number(row["cost_adj"])} · CP_adj {_number(row["cp_adj"])}</p>'
            f'<small>{_html(row["source_date"])} · {_html(row["source_url"])}</small>'
            f'<p>{_html(row["notes"])}</p></details>')


def _ladder(rows, by_id):
    body = []
    for rank, row in rows:
        upgrade = row['upgrade']
        if row['comparison_only']:
            detail = '僅供比較'
        elif upgrade is None:
            detail = '最低一檔正式推薦；沒有下一檔升級比較。'
        else:
            target = by_id.get(upgrade['cheaper_identity'])
            name = target['model'] + ' · ' + target['effort'] if target else upgrade['cheaper_identity']
            detail = (f'比 {name} 多 {upgrade["delta_score"]:.2f} 分；'
                      f'成本 {upgrade["cost_multiple"]:.2f} 倍（每任務 +${upgrade["delta_cost_adj"]:.4f}）。')
        precise = ('<details><summary>精確升級數值</summary><p>' + _html(_upgrade(row)) + '</p></details>') if upgrade else ''
        body.append(f'<tr data-rank="{rank}"><td><strong>{_html(row["model"])}</strong>'
                    f'<span class="effort">effort：{_html(row["effort"])}</span>'
                    '</td>'
                    f'<td class="number" data-label="能力分數">{row["score"]:.2f}</td>'
                    f'<td class="number" data-label="情境成本">${row["cost_adj"]:.4f}</td>'
                    f'<td>{_html(detail)}{precise}{_row_details(row)}</td></tr>')
    if not body:
        return '<p>從缺：本次沒有符合條件的保留行。</p>'
    return ('<div class="table-wrap"><table class="chooser"><thead><tr><th scope="col">模型與 effort</th>'
            '<th scope="col">能力分數</th><th scope="col">情境成本／任務</th><th scope="col">與下一檔相比</th>'
            '</tr></thead><tbody>' + ''.join(body) + '</tbody></table></div>')


def _candidate(row):
    if row['comparison_only']:
        status = '僅供比較 · ' + ('保留' if row['status'] == 'final' else '未入選')
    else:
        status = '正式推薦' if row['status'] == 'final' else '未入選'
    reason = ('已通過本次選型。' if row['reason'] is None else
              '由保留模型代表（within_replacement_radius）。' if row['reason'] == 'within_replacement_radius'
              else row['reason'])
    winner = f'<p>結果提供的代表：{_html(row["winner"])}</p>' if row['winner'] else ''
    return (f'<li data-search="{_html(row["model"] + " " + row["effort"] + " " + row["identity"])}">'
            f'<h3>{_html(row["model"])}</h3><span class="badge">{_html(status)}</span>'
            f'<p>effort：{_html(row["effort"])} · 分數 {row["score"]:.2f} · 情境成本 ${row["cost_adj"]:.4f}</p>'
            f'<small>{_html(row["identity"])}</small><p>{_html(reason)}</p>{winner}{_row_details(row)}</li>')


def _observation(row):
    search = ' '.join(v for v in (row['name'], row.get('model'), row.get('effort')) if v)
    effort = ('來源未標示（unspecified）' if row.get('effort') == 'unspecified' else
              row.get('effort') or '來源原文未能辨識，沒有代入其他 effort')
    return (f'<li data-search="{_html(search)}"><h3>{_html(row.get("model") or row["name"])}</h3>'
            '<span class="badge">來源缺值／退出 · 本次未參戰</span>'
            f'<p>effort：{_html(effort)}</p><small>來源原名：{_html(row["name"])}</small>'
            f'<p>{_html(row["state"])}：{_html(row["reason"])}</p>'
            '<p>不沿用舊價、不推定成本，也不借用其他 effort 的數字。</p>'
            f'<small>來源證據：{_html(row["slug"])}</small></li>')


def render_html(calculation, *, observations=(), links=(), provider_links=(), provider=None, provider_views=None):
    from .provider_view import PROVIDERS
    all_eligible=calculation.get('eligibility_policy')=='all-providers-v1'
    provider_name=PROVIDERS.get(provider)
    heading=f'{provider_name} 訂閱，<br>模型與檔位怎麼選？' if provider_name else '模型怎麼選？<br>先看這兩個入口。'
    provider_nav='<nav id="provider-chooser" class="provider-chooser" aria-label="選供應商">'+''.join(
        f'<a data-provider="{_html(key)}" href="{escape(url,quote=True)}"'+(' aria-current="page"' if key==(provider or 'all') else '')+f'>{_html(label)}</a>' for key,label,url in provider_links)+'</nav>' if provider_links else ''
    scope_note=(f'<p class="note" data-selection-scope="{provider}">本頁只在{_html(provider_name)}候選內，使用相同來源、情境成本與選型政策算出建議模型及effort檔位。訂閱方案當期可用模型／檔位，仍需以供應商介面確認。</p>' if provider_name else '')
    cards = []
    for key, title, explanation in (
        ('highest_retained_score', '推薦中能力最高', '先看能力：這是本次正式推薦中分數最高的保留檔。'),
        ('lowest_retained_cost', '推薦中情境成本最低', '先看成本：這是本次正式推薦中情境成本最低的保留檔。')):
        row = calculation['anchors'][key]
        content = (f'<strong class="model-name">{_html(row["model"])}</strong>'
                   f'<span class="effort">effort：{_html(row["effort"])}</span>'
                   + _metrics(row) if row else '<strong class="model-name">從缺</strong><p>無非 Claude 保留行，不另補位。</p>')
        if row:
            content += (f'<p class="note">GRADE-B 推導成本，假設見細節。</p>' if row['grade'] == 'B' else '') + _row_details(row)
        cards.append(f'<article class="card" data-anchor="{key}"><h2>{title}</h2>{content}<p class="note">{explanation}</p></article>')
    anchors = list(calculation['anchors'].values())
    same = '<p class="note">兩個入口是同一模型與 effort，這次推薦不必再做二選一。</p>' if anchors[0] and anchors[0] == anchors[1] else ''
    exits = _source_exits(calculation)
    exit_section = ('<section class="panel exit" data-family="source-exits"><h2>本次來源退出</h2><ul>'
                    + ''.join('<li>' + _html(x) + '</li>' for x in exits) + '</ul></section>') if exits and not provider_name else ''
    ranked = list(enumerate(calculation['ladder'], 1))
    selected = [(i, r) for i, r in ranked if not r['comparison_only']]
    comparison = [(i, r) for i, r in ranked if r['comparison_only']]
    comparison_section=('<details id="comparison"><summary>Claude-family 僅供比較（'+str(len(comparison))+' 檔），不列正式推薦</summary><p>僅比較：不進兩個入口或正式升級路線。</p>'+_ladder(comparison, {r['identity']:r for r in calculation['candidate_statuses']})+'</details>') if not all_eligible else ''
    by_id = {r['identity']: r for r in calculation['candidate_statuses']}
    audit = []
    for key, title, columns, rows in _tables(calculation):
        if key == 'ladder':
            continue
        table = ('<div class="table-wrap"><table><thead><tr>' + ''.join(f'<th scope="col">{_html(c)}</th>' for c in columns)
                 + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + _html(v) + '</td>' for v in r) + '</tr>' for r in rows)
                 + '</tbody></table></div>') if rows else '<p>無</p>'
        audit.append(f'<details data-family="{key}"><summary>{title}（{len(rows)}）</summary>{table}</details>')
    operation = calculation.get('operation') or ('refresh' if calculation['source_snapshot'].get('kind') == 'acquired' else 'recompute')
    operation_note = '固定快照重算，非重新抓取來源' if operation == 'recompute' else '重新取得公開來源的固定快照'
    params = calculation['parameters']
    from .subscription_cost import SUBSCRIPTION_PARAMETERS, scenario_label
    cost_note = ('使用者成本情境：' + scenario_label(params,include_claude=all_eligible) + '。倍率不是保證額度。'+('' if all_eligible else 'Claude 僅供比較。')
                 if set(params) == SUBSCRIPTION_PARAMETERS else
                 f'使用者成本情境：GPT ×{params["gpt_factor"]}／Grok ×{params["grok_factor"]}／Contributor ×1。'
                 'GPT 預設 ×18 由個人約18.9倍保守取整；Grok 預設 ×16 為指定情境、非實測。')
    if provider_name:
        factor_key={'gpt':'gpt_factor','gemini':'gemini_factor','claude':'claude_factor','grok':'grok_factor'}[provider]
        cost_note=f'使用者成本情境：{provider_name} ×{params.get(factor_key,1)}。倍率不是保證額度。'
    metadata = ''.join(f'<p>{_html(x)}</p>' for x in _metadata(calculation))
    for key in ('product_sha', 'request_commit_sha', 'request_id', 'run_id', 'run_attempt'):
        if key in calculation:
            metadata += f'<p>{key}：{_html(calculation[key])}</p>'
    context = ''.join('<li>' + _html(x) + '</li>' for x in _context(calculation) if x not in exits)
    downloads = ''.join(f'<li><a href="{escape(url, quote=True)}">{_html(label)}</a></li>' for label, url in links)
    provider_summary=''
    if provider_views:
        urls={key:url for key,_,url in provider_links}
        previews=[]
        for key,view in provider_views.items():
            summaries=[]
            for anchor,label in (('highest_retained_score','能力優先'),('lowest_retained_cost','成本優先')):
                row=view['calculation']['anchors'][anchor]
                summaries.append(f'<p>{label}<strong>{_html(row["model"])} · {_html(row["effort"])}</strong>分數 {row["score"]:.2f} · ${row["cost_adj"]:.4f}／任務</p>' if row else f'<p>{label}：從缺'+('（此歷史版本Claude僅比較）' if key=='claude' and not all_eligible else '')+'</p>')
            previews.append(f'<article data-provider-summary="{key}"><h3>{PROVIDERS[key]}</h3>'+''.join(summaries)+f'<a href="{escape(urls[key],quote=True)}">查看 {_html(PROVIDERS[key])} 完整階梯</a></article>')
        provider_summary='<section class="panel"><h2>四種訂閱，各自怎麼選？</h2><p class="note">每家獨立比較該家全部候選，檔位由既有選型政策決定。</p><div class="provider-cards">'+''.join(previews)+'</div></section>'
    return f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="先看推薦中能力最高與情境成本最低，再比較每一檔模型與 effort。">
<title>模型效率前線｜模型怎麼選</title><style>{CSS}</style></head><body>
<a class="skip" href="#recommendations">跳到推薦</a><main>
<nav aria-label="頁面導覽"><a href="#recommendations">先看結論</a><a href="#ladder">推薦階梯</a><a href="#lookup">查模型</a><a href="#calculation">計算與來源</a></nav>
<header><p class="eyebrow">MODEL EFFICIENCY FRONTIER</p><h1>{heading}</h1>
<p class="intro">能力優先，或成本優先。從已選好的推薦階梯開始，依照你的任務比較每一檔的差異。</p>
<div class="stamp"><span>來源日期：{_html(', '.join(calculation['source_dates']))}</span><span>{_html(operation)} · {operation_note}</span></div>
<p class="note">{_html(cost_note)}這是使用者情境，不是所有人的公開 API 售價；金額為美元／任務。</p>
{provider_nav}{scope_note}
</header>
<section id="recommendations" class="cards" aria-label="保留檔入口">{''.join(cards)}</section>{same}
{provider_summary}
<section id="ladder" class="panel" data-family="ladder"><h2>推薦階梯</h2><p class="note">分數由高至低。每一檔列出相對下一檔的能力與成本差異。</p>{_ladder(selected, by_id)}
{comparison_section}</section>
<section id="lookup" class="panel"><h2>查詢單一模型</h2><p class="note">名稱與 effort 一起查，例如 Astra max、Sol max；不同 effort 分開列。</p>
<div id="search-control" class="search-control" hidden><label for="model-search">模型名稱與 effort</label><input id="model-search" type="search" placeholder="例如 Astra max" autocomplete="off" aria-controls="search-results"><p id="search-status" role="status" aria-live="polite"></p></div>
<p id="search-empty" hidden>本次來源沒有觀測到符合查詢的模型與 effort。這不代表模型太差、已退役或不存在；試試完整名稱，或查看其他 effort。</p>
<details id="search-results"><summary>查看候選與來源狀態</summary><ul class="candidate-list">{''.join(_candidate(r) for r in calculation['candidate_statuses'])}{''.join(_observation(r) for r in observations)}</ul></details>
<noscript><p>搜尋需要 JavaScript；你仍可展開全部候選、來源狀態及推薦細節。</p></noscript></section>
<details id="calculation" class="panel audit"><summary>計算與來源 · 全候選稽核、selection_trace、GRADE-B 與版本</summary>
<div class="source-meta">{metadata}</div>{''.join(audit)}<section><h2>來源與限制</h2><ul>{context}</ul></section><ul>{downloads}</ul></details>
{exit_section}
<footer class="footer">模型效率前線 · 網站版本 {WEBSITE_VERSION} · 資料日期以上方來源日期為準，部署日期不代表資料更新。</footer>
</main><script id="model-search-script">{SEARCH_JS}</script></body></html>'''
