# Fixed-window CP Ladder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將已確認的CP-new-high＋固定2分視窗精簡接入正式Chat／CI，直接輸出選好的檔位及兩個final-only摘要入口。

**Architecture:** 保持現行來源與身份驗證，重用frozen第一階段；新的純計算模組擁有第二階段、投影、摘要、升級及B診斷。result v2與v1分派驗證；Markdown／HTML消費同一payload。先建立可獨立測試的新模組，最後一次整合切換預設產品，不在半成品階段發布。

**Tech Stack:** Python 3.11標準庫、unittest、靜態單檔HTML、Git／GitHub Actions／gh CLI；不新增套件或服務。

**Spec:** `docs/superpowers/specs/2026-09-27-window-knee-production-design.md`（使用者已確認；執行者必讀全篇）。

**Status:** 計畫待使用者審閱；執行方式已選Subagent-driven，不再重問方法。此文件不是已執行證據。

## Global Constraints

- 第一階段調用未改動的`compute_frontier.compute_one_group`：`eps_score=2`、`eps_cp=.05`；同分同價沿原CSV順序的stable sort。
- 固定`h=2.0`與`r=2.0`，`abs(ΔScore) < r`才可取代；不加隱藏epsilon、不pin最高分／最高CP、不按family分組。
- 缺完整雙側視窗給`k=0`／`neutral_missing_window`，不外插；負k合法，非正g或非有限數值報`selection_numeric`。
- GPT×18、Grok×16、Contributor×1；General／同benchmark version／同basis，min-score必填及理由；free／GRADE-C不參戰。
- `Muse Spark 1.3 max Meta Contributor`排名前excluded，原歷史CSV保留；fresh能力／價格證據及失敗發布guard保持有效。
- Claude-family只比较；摘要及upgrade只取非Claude final；沒有final非Claude時兩入口null，不從被淘汰行補位。
- result v2、request v1；新publisher可讀寫合法舊v1結果，舊資料不重標成新算法。
- 舊`runs/`、已發布results、`scripts/compute_frontier.py`、`scripts/ladder.py`、`scripts/ladder_extra.py`及兩份敏感度實驗不改。
- JSON／Markdown／HTML同一主結果；B反事實診斷使用副本、不改主結果。renderer無網路、無重新選檔。
- 單檔HTML及Chat結報，不部署網站、不恢復Notion；bootstrap不需改定位，既有Chat能力證據沿用。
- 當前Inkling／MiniMax-M2.7缺cost不是本次修復範圍；不得靜默刪候選、補舊價或宣稱fixture等於live fresh成功。

## Review Focus

1. 相同Score／cost的不同route：第一階段必須沿原CSV次序選定，第二階段不可擅自保留或改名合併（Task 1）。
2. 全部是B或可用B被約束排完：診斷副本為空不能讓主結果失敗，不能遺失B標記（Task 2）。
3. 合法v1帶舊cut原因但没有新trace：過渡publisher仍接受；v1混入v2根欄位及`schema_version=True`則拒絕（Task 3／5）。
4. 被cut行被偽装成摘要／trace winner、或trace重複刪同一行：看似完整的成功JSON仍須拒絕（Task 3）。
5. 後期missing_candidate失敗删光能力證據：即使operation=null或結果改成v2也不能發布；真正早期models fetch／parse failure仍可發布診斷（Task 5）。

---

## File map and execution order

| Files | Owner / responsibility |
|---|---|
| `bridge/window_ladder.py` | Tasks 1–2：純選擇、投影、摘要、升級、B診斷 |
| `tests/window_fixtures.py`, `tests/test_window_ladder.py` | Tasks 1–2：小型解析案例及固定歷史來源fixture |
| `bridge/result_v1.py` | Task 3：現有result實作的隔離副本，維持v1行為；不呼叫它生成新制結果 |
| `bridge/result_v2.py` | Task 3：v2來源投影、組裝、驗證 |
| `bridge/result.py` | Task 3先做相容facade；Task 5才切預設計算／生成為v2 |
| `tests/test_bridge_result_v2.py` | Task 3：新契約、未知／混合schema、偽造關係 |
| `bridge/window_report.py` | Task 4：v2 Markdown與HTML，只讀payload |
| `bridge/html_report.py`, `tests/test_bridge_html.py` | Task 4：依payload政策分派v1／v2 HTML |
| `tests/test_window_report.py` | Task 4：兩視圖一致、稽核與escape |
| `bridge/runner.py`, `bridge/publish.py`, `bridge/inventory.py` | Task 5只修必要相容接點，不重寫傳輸／證據演算法 |
| `tests/test_bridge_result.py`, `tests/test_bridge_runner.py`, `tests/test_bridge_publish.py` | Task 5：保留明確v1測試＋新增v2整合 |
| `chatgpt-instructions.md`, `docs/contracts/chat-ci.md`, `README.md`, `AGENTS.md` | Task 6：正式新語義、真實驗收狀態 |
| `docs/superpowers/notes/2026-09-27-window-knee-acceptance.md` | Task 6：本地、cloud、固定產物證據 |

按Task 1→6順序。每個task用新implementer及獨立spec／quality review，通過才進下一task；同一模組不可交給同時工作的writer。使用worktree skill在執行開始建立隔離環境；先記錄工作起點SHA、確認乾淨並跑一次現有全套基準。規劃階段不建worktree、不啟動implementer。

執行開始在隔離worktree執行`git rev-parse HEAD > /tmp/opencode/window-knee-execution-base.sha`，並把同一SHA抄入執行ledger，供最後保護檔差異檢查；不得在中途覆寫這個起點。

## Task 1: Frozen chain plus fixed-window thinning

**Files:** Create `bridge/window_ladder.py`, `tests/window_fixtures.py`, `tests/test_window_ladder.py`.

**Interfaces:**
- Consumes: `extra.adjust_rows(...)`產生的獨立候選dict；`unavailable_reason(row)`；`cf.compute_one_group(rows,min_score,max_cost,2,.05)`。
- Produces: `SelectionError(ValueError)`（`code`字串）、`window_strengths(rows: list[dict]) -> dict[str, tuple[float,str]]`、`thin_chain(rows: list[dict]) -> tuple[list[dict],list[dict]]`、`select_chain(rows: list[dict], *, min_score: float, max_cost: float|None) -> dict`。
- `select_chain`返回`chain`、`final`（rows），`excluded`（`[(row, reason)]`），`cuts`（identity→winner），`trace`。输入不修改，顺序保持；内部空rows合法，公共來源empty_paid由Task 3處理。

- [ ] **1. Add fixture helpers and analytical failing tests.** `point`直接建已調整row，不需要CSV或網路：

```python
def point(name, score, cost, grade='A'):
    return dict(identity=name, model=name, effort='unspecified', provider='test',
        pricing_plan='Standard', benchmark='AA-Intelligence-Index',
        benchmark_version='AA-Intelligence-Index-v4.3.2', cost_basis='api',
        evidence_url='https://example.test/model', checked_date='2026-09-26',
        notes=f'GRADE-{grade} test evidence', _score=score, _cost=cost,
        _cost_orig=cost, _cp=score/cost, _cp_orig=score/cost, _factor=1)
```

`tests/window_fixtures.py`另提供`historical_rows()`，在函式內`import sys`並插入repo/scripts，再import ladder_extra，return `adjust_rows(load_rows(SNAPSHOT))`；SNAPSHOT等沿`test_bridge_result`的既有常數。解析測試：

```python
def test_interpolated_window_has_known_slope_ratio(self):
    from math import exp, log
    rows = [point(str(s), s, s/exp(.5*(10-s) if s >= 6 else 2+.1*(6-s)))
            for s in (10., 9., 6., 3., 2.)]
    value, support = window_strengths(rows)['6.0']
    self.assertAlmostEqual(value, log(5))
    self.assertEqual(support, 'full_window')
    self.assertEqual(window_strengths(rows)['10.0'], (0., 'neutral_missing_window'))

def test_highest_score_is_not_pinned(self):
    rows = [point('top', 10., 10.), point('middle', 9., 3.), point('tail', 6., 1.5)]
    kept, trace = thin_chain(rows)
    self.assertEqual([r['identity'] for r in kept], ['middle', 'tail'])
    self.assertEqual(trace[0]['removed'], ['top'])

def test_equal_score_cost_preserves_frozen_input_order(self):
    a, b = point('route-z', 10., 1.), point('route-a', 10., 1.)
    self.assertEqual(select_chain([a,b], min_score=0, max_cost=None)['chain'][0]['identity'], 'route-z')
    self.assertEqual(select_chain([b,a], min_score=0, max_cost=None)['chain'][0]['identity'], 'route-a')
```

- [ ] **2. RED:** `python3 -m unittest discover -s tests -p 'test_window_ladder.py' -v`，确认失败是新module／functions缺失。
- [ ] **3. Implement exact selection, no new policy choices.** 使用`deepcopy`隔離輸入；availability先partition，其他交cf，保持既有stable tie；cut由trace投影。核心数学与排序为：

```python
left_gain = log_cp_at_b - interpolate(score_b + 2.0)
right_gain = interpolate(score_b - 2.0) - log_cp_at_b
if not all(math.isfinite(x) and x > 0 for x in (left_gain, right_gain)):
    raise SelectionError('selection_numeric')
strength = math.log(left_gain / right_gain)
winner = min(pool, key=lambda r: (-values[r['identity']][0], -r['_cp'],
                                  -r['_score'], r['identity']))
```

`interpolate`使用目前剩餘链的log-CP線性插值；缺窗口直接中性。空／單點thin直接返回，避免log(0)。trace每步包含`step`（1起）、winner、strength、support、removed（当时Score降序）。以同一算法不断缩减current，绝不调用旧dedup。imports依現有scripts路徑方式，不import實驗模組或recommend.py。
- [ ] **4. Add boundary/counterexample tests in small red→green cycles.** 實際案例用明确值：`[point('a',10,10),point('b',8,4)]`相差2全部保留；把b改8.0001則只留b。`[]`、`[point('zero',0,1)]`不取log。`point('bad',9,0.5)`被cost cap=.25排除而不影響其餘決策；全被floor篩掉回空。有效單調链上的NaN/Inf或非正插值增益报SelectionError，不clamp。直線log-CP为0、CP乘1000相同、source row逐字deepcopy相等。歴史來源断言155不变、invalidmaxexcluded、chain19、final10／cuts9，final名單對照实验window；support欄位由本算法驗，strength用`assertAlmostEqual`而選檔仍不設tolerance。
- [ ] **5. GREEN／commit:** 同Step 2測試通過；`git diff --check`；只stage上述三檔，commit `feat: add fixed-window thinning on the frozen CP chain`。獨立review重点：同分同價、2分嚴格邊界、代表永遠final、缺窗不是自動保送最高分。

## Task 2: Final-only anchors, upgrades and B-impact audit

**Files:** Modify `bridge/window_ladder.py`, `tests/test_window_ladder.py`.

**Interfaces:**
- Consumes: Task 1 `select_chain`與調整後rows。
- Produces: `calculate_ladder(rows, *, min_score, max_cost) -> dict`，包含`ladder`, `anchors`, `candidate_statuses`, `candidate_count`, `chain_identities`, `selection_trace`, `grade_b_effects`。
- Produces: `select_anchors(ladder: list[dict]) -> dict`（输入為projected rows），供Task 3驗證摘要复用；键严格为`highest_retained_score`／`lowest_retained_cost`。

- [ ] **1. Write failing tests for non-resurrection and B diagnostics.**

```python
def test_anchors_only_use_final_non_claude(self):
    result = calculate_ladder(historical_rows(), min_score=0, max_cost=None)
    self.assertEqual(result['anchors']['highest_retained_score']['identity'],
                     'GPT-6 Astra xhigh AA-public published-price')
    self.assertEqual(result['anchors']['lowest_retained_cost']['identity'],
                     'GPT-6 Luna low AA-public published-price')
    finals = {r['identity'] for r in result['ladder']}
    self.assertTrue(all(r is None or r['identity'] in finals for r in result['anchors'].values()))

def test_b_counterfactual_can_change_a_membership_without_mutating_main(self):
    from copy import deepcopy
    rows = [point('A-high',10,10), point('B-middle',9,1,'B'), point('A-low',6,1)]
    original = deepcopy(rows)
    result = calculate_ladder(rows, min_score=0, max_cost=None)
    self.assertEqual([r['identity'] for r in result['ladder']], ['B-middle'])
    self.assertEqual(result['grade_b_effects'], [
        {'identity':'A-high','with_b_retained':False,'without_b_retained':True},
        {'identity':'A-low','with_b_retained':False,'without_b_retained':True}])
    self.assertEqual(rows, original)

def test_all_b_has_valid_empty_counterfactual(self):
    result = calculate_ladder([point('B-only',9,1,'B')], min_score=0, max_cost=None)
    self.assertEqual(result['grade_b_effects'], [])
    self.assertEqual(result['ladder'][0]['grade'], 'B')

def test_b_influences_interpolation_even_when_cut_winner_is_a(self):
    rows = [point('B-top',12,12,'B'), point('A-10',10,1),
            point('A-9',9,9/11), point('A-7',7,7/20), point('A-5',5,5/30)]
    result = calculate_ladder(rows, min_score=0, max_cost=None)
    self.assertEqual(result['selection_trace'][0]['winner'], 'A-10')
    self.assertEqual(result['grade_b_effects'], [
        {'identity':'A-10','with_b_retained':True,'without_b_retained':False},
        {'identity':'A-9','with_b_retained':False,'without_b_retained':True}])
```

- [ ] **2. RED:** `python3 -m unittest discover -s tests -p 'test_window_ladder.py' -v`。
- [ ] **3. Implement result composition over the one main selection.** 投影使用既有`bridge/result.py:_project`的字段含義，不import它造成cycle；本模組唯一project helper擁有新row組裝，含`comparison_only`及`upgrade`。以source paid順序建立statuses，cut理由固定`within_replacement_radius`，winner来自Task1，final理由null；excluded保留原說明。只有final非Claude建立upgrade，所有anchors引用完整同一row內容。

```python
eligible = [r for r in ladder if not r['comparison_only']]
anchors = {
    'highest_retained_score': min(eligible, key=lambda r:(-r['score'],r['cost_adj'],r['identity'])) if eligible else None,
    'lowest_retained_cost': min(eligible, key=lambda r:(r['cost_adj'],-r['score'],r['identity'])) if eligible else None,
}
for upper, lower in zip(eligible, eligible[1:]):
    upper['upgrade'] = {'cheaper_identity':lower['identity'],
        'delta_score':upper['score']-lower['score'],
        'cost_multiple':upper['cost_adj']/lower['cost_adj'],
        'delta_cost_adj':upper['cost_adj']-lower['cost_adj']}
```

只在有可用B時以獨立副本呼叫`select_chain`移除所有B重播，比较A最終membership并按identity排序；不遞迴调用含B診斷的`calculate_ladder`。要先完成upgrade再讓statuses、ladder、anchors共用一致投影，不能留下三份不同row。
- [ ] **4. Extend tests and GREEN.** `[point('Claude test',10,1)]`兩anchors為null、upgrade=null；`[point('A only',10,1)]`兩anchors相同且upgrade=null。三個相差至少2的rows中間為Claude，比較上方非Claude的upgrade必跳過Claude指向下方非Claude。用score10/cost10、score7/cost2驗delta3、倍率5、增額8。全部被floor筛掉仍保留原status數；所有B被cap排除时grade_b_effects为空。historical_invalidmax不参与B反事實；各row不可丢失9Grok／2Contributor原稽核。重跑Task1–2測試。
- [ ] **5. Commit／review:** `feat: compose window ladder anchors upgrades and grade-B audit`；重点看B以間接插值／第一階段影響A時，不能只看winner的grade。

## Task 3: Versioned result contracts, without activating v2 generation yet

**Files:** Create `bridge/result_v1.py`, `bridge/result_v2.py`, `tests/test_bridge_result_v2.py`; modify `bridge/result.py`.

**Interfaces:**
- `result_v1.py`先复制当前`bridge/result.py`完整實作，保持其公开calculate／make／validate签名及v1语义；不與v2互相import。
- `result_v2.calculate_v2(csv_path: Path, parameters: dict, provenance: dict) -> dict`，来源驗證後调用Task2。
- `result_v2.make_v2_envelope(request, execution, *, calculation, errors) -> dict`；`validate_v2_envelope(envelope) -> dict`。
- facade `result.validate_envelope`此task開始分派兩版；`result.calculate_snapshot`與`make_envelope`先仍转发v1，直到Task5；`ResultError`统一alias到result_v1.ResultError。

- [ ] **1. RED: add tests for new v2 projection and relation tampering.** 重用`test_bridge_result`的SNAPSHOT／PARAMETERS／PROVENANCE／recompute_data；execution使用以下固定fixture，不需要网络：

```python
EXECUTION = dict(request_commit_sha='b'*40, run_id='9753', run_attempt=1,
                 run_url='https://github.com/example/actions/runs/9753')

def test_v2_roundtrip_and_partition(self):
    calc = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)
    env = make_v2_envelope(recompute_data(), EXECUTION, calculation=calc, errors=[])
    self.assertEqual(env['schema_version'], 2)
    self.assertNotIn('picks', env)
    self.assertEqual(validate_envelope(env), env)
    from collections import Counter
    self.assertEqual(Counter(r['status'] for r in env['candidate_statuses']),
                     {'final':10,'cut':9,'excluded':136})

def test_v2_cannot_resurrect_a_cut_as_anchor(self):
    calc = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)
    env = make_v2_envelope(recompute_data(), EXECUTION, calculation=calc, errors=[])
    env['anchors']['highest_retained_score'] = next(r for r in env['candidate_statuses'] if r['status']=='cut')
    with self.assertRaises(ValueError):
        validate_envelope(env)
```

Run `python3 -m unittest discover -s tests -p 'test_bridge_result_v2.py' -v`，先见新module缺失。
- [ ] **2. Isolate v1 and implement source checks plus v2 creation.** 复制而不是削弱v1算法；result_v2可重用v1的`_provenance`／`_number`／`_date`／`_locator`及ResultError，不调其calculate_snapshot（那会跑旧band）。把现有calculate_snapshot的hash、parameters、group、GRADE、來源日期／URL、重复identity验证按原条件用于v2来源入口，再调用`calculate_ladder`。不引入固定historical hash到通用入口。

```python
POLICY = 'cp-new-high-window-v1'
payload = dict(calculate_ladder(paid, min_score=parameters['min_score'],
                               max_cost=parameters['max_cost']),
    selection_policy=POLICY, selection_parameters={'window_score':2.0,'replacement_score':2.0},
    parameters=dict(parameters), eps={'score':2.0,'cp':0.05},
    source_snapshot=dict(provenance['source_locator']), source_dates=list(provenance['source_dates']),
    benchmark=provenance['benchmark'], benchmark_version=provenance['benchmark_version'],
    version_status=provenance['version_status'], cost_basis=provenance['cost_basis'],
    caveats=list(provenance['caveats']))
```

`make_v2_envelope`沿v1相關身份組裝但schema=2；失敗不帶計算欄位，即使傳入calculation也忽略成功部分，parameters不受信任仍可保留为诊断。case无有效paid报empty_paid，全部被参数筛掉仍成功空ladder。
- [ ] **3. Implement strict schema dispatch and v2 validation.**

```python
def validate_envelope(envelope):
    if type(envelope) is not dict or type(envelope.get('schema_version')) is not int:
        raise ResultError('invalid_result_schema')
    version = envelope['schema_version']
    if version == 1:
        if set(envelope) & {'selection_policy','selection_parameters','anchors',
                            'chain_identities','selection_trace','grade_b_effects'}:
            raise ResultError('mixed_result_schema')
        return result_v1.validate_envelope(envelope)
    if version == 2:
        return result_v2.validate_v2_envelope(envelope)
    raise ResultError('invalid_result_schema')
```

v2驗證不通过填假的v1 picks再套旧validator：明确检查spec根字段／政策常數，request参数、correlation及provenance与v1同严；正数、非有限、bool冒充数字均拒绝。检查row投影算术（`cost_orig/factor`、CP关系以`math.isclose(rel_tol=1e-12,abs_tol=1e-12)`只用于驗證，選檔仍exact），family标记／comparison_only、statuses唯一且count一致；chain为final∪cut且有序、excluded不入链；ladder与final内容完全相同且gap≥2。

trace逐step检查removed仍在當時存活集合、分差<2、winner为final且未被移除、support枚举／有限strength／neutral为0，最后集合等于ladder；不允许漏cut或重复removed。anchors复用select_anchors；upgrade只指向下一非Claude final且数字正确；grade_b_effects唯一排序、只含A、with_b与实际final相符、两布林不同。不在validator重跑CP或发明第二套算法。
- [ ] **4. GREEN and mutation tests.** 加入schema=True／3／v1含anchors／v2含picks、trace winner=cut、重复removed、漏掉一step、cut距离正好2、out-of-chain final、错factor／CP、伪upgrade指Claude、伪grade_b_effects、未知support及neutral非0；所有失败携带ladder/anchors/trace/B诊断皆拒绝。历史v1原16階及三picks roundtrip照旧通过，v1合法旧same-score cut无需v2 trace。来源mixed-version／GRADE-C／缺B caveat／错hash／重复identity全部沿原拒绝。

旧v1身份错误仍是可读的历史证据，明确增加此测试（不要求新算法重现旧错误）：

```python
def test_legacy_cut_identity_is_readable_without_v2_trace(self):
    from bridge import result_v1
    calc, _ = result_v1.calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)
    env = result_v1.make_envelope(recompute_data(), EXECUTION, calculation=calc, errors=[])
    old = next(r for r in env['candidate_statuses'] if r['identity']=='Muse Spark 1.3 max Meta Contributor')
    old.update(status='cut', reason='same-score band', winner='GPT-6 Sol max AA-public published-price')
    self.assertNotIn('selection_trace', env)
    self.assertEqual(validate_envelope(env), env)
```

Run both `python3 -m unittest discover -s tests -p 'test_bridge_result*.py' -v` and Task1–2 suite；此时默认生成仍v1，因此原runner／publisher不应因新schema破坏。
- [ ] **5. Commit／review:** `feat: add v2 window result contract with legacy validation`；重点为未知schema、失败清理及伪造看似完整的关系。

## Task 4: Shared v2 Markdown and offline HTML

**Files:** Create `bridge/window_report.py`, `tests/test_window_report.py`; modify `bridge/html_report.py`, `tests/test_bridge_html.py`（保持v1 tests）。

**Interfaces:** `window_report.render_markdown(calculation: dict) -> str`、`window_report.render_html(calculation: dict) -> str`；只接受Task3的v2 calculation。现有`html_report.render_html`若见POLICY转发，否则保留原v1renderer。

- [ ] **1. Write failing view tests.**

```python
def test_both_reports_use_selected_anchors_and_all_audit_rows(self):
    calc = calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE)
    markdown, html = render_markdown(calc), render_html(calc)
    for name in ('highest_retained_score','lowest_retained_cost'):
        self.assertIn(calc['anchors'][name]['identity'], markdown)
        self.assertIn(calc['anchors'][name]['identity'], html)
    self.assertEqual(html.count('data-rank="'), 10)
    self.assertIn('Muse Spark 1.3 max Meta Contributor', html)
    self.assertIn('Standard tier only', html)
    self.assertNotIn('階梯中段', html)
    self.assertNotIn('aria-label="三檔推薦"', html)

def test_source_text_is_escaped(self):
    from copy import deepcopy
    calc = deepcopy(calculate_v2(SNAPSHOT, PARAMETERS, PROVENANCE))
    calc['caveats'].append('<script>alert(1)</script>')
    html = render_html(calc)
    self.assertNotIn('<script>', html)
    self.assertIn('&lt;script&gt;', html)
```

- [ ] **2. RED:** `python3 -m unittest discover -s tests -p 'test_window_report.py' -v`。
- [ ] **3. Implement views with no calculations that choose identities.** 两卡标签「最強保留檔」「最低情境成本保留檔」，null显示從缺。全表Score降序，显示原价／调整价／CP／factor／GRADE、comparison-only及已算upgrade。cut依trace输出分差与原因；当support中性不冒充真实双侧拐点证据。输出所有Grok／Contributor、source日期／locator、版本推定及B effects，保留旧GPT79假设边界，不自动续订。

```python
from html import escape

def text(value):
    return escape('—' if value is None else str(value), quote=True)

def anchor_card(title, row):
    body = text(row['identity']) if row else '從缺'
    return f'<article class="card"><h2>{text(title)}</h2><strong>{body}</strong></article>'
```

沿现有inline CSS／table-wrap布局，cards grid改2列、窄屏1列；每个ladder `<tr data-rank>`编号唯一。table横向滚动容器可超过viewport，但整页不能溢出。外部URL若显示为链接只允許http/https，否则当纯文本escape；不导入CDN／JS／字体。
- [ ] **4. GREEN and empty/Claude-only cases.** anchors皆null、ladder空但statuses非空、仅Claude一行、同一identity两卡、恶意notes／reason／identity／URL均不破坏HTML。Markdown escape管线／换行与HTML分开处理。所有渲染前后payload深比较相等，patch任何fetch／选择函数为抛异常时renderer仍成功。Run `test_window_report.py`与`test_bridge_html.py`；用Task3生成一份HTML到`/tmp/opencode/window-knee-review/`，浏览器1280／390px核对，记录本地路径及无外部请求。
- [ ] **5. Commit／review:** `feat: render fixed-window ladder reports from one payload`。

## Task 5: Activate v2 and prove runner/publisher interoperability

**Files:** Modify `bridge/result.py`, necessary seams in `bridge/runner.py`, `bridge/publish.py`, `bridge/inventory.py`; modify tests `test_bridge_result.py`, `test_bridge_runner.py`, `test_bridge_publish.py`, `test_bridge_html.py`; add `tests/test_bridge_window_integration.py`.

**Interfaces:** Public signatures stay `calculate_snapshot(csv_path,parameters,provenance)->(dict,str)`, `make_envelope(request,execution,*,calculation,errors)->dict`, `validate_envelope(envelope)->dict`, `render_html(calculation)->str`. Defaults nowv2；explicit v1 APIs only inresult_v1。

- [ ] **1. RED public-default test; preserve old tests explicitly.** 把`test_bridge_result.py`的calculate／make导入改成result_v1，validate仍指新facade，保证老16階测试真实存在、不批量改成10后失去v1覆盖。`test_bridge_html.py`明确旧fixture走result_v1，v2另有Task4测试。

```python
def test_public_default_is_v2(self):
    calc, markdown = calculate_snapshot(SNAPSHOT, PARAMETERS, PROVENANCE)
    result = make_envelope(recompute_data(), EXECUTION, calculation=calc, errors=[])
    self.assertEqual(result['schema_version'], 2)
    self.assertEqual(result['selection_policy'], 'cp-new-high-window-v1')
    self.assertNotIn('picks', result)
    self.assertEqual(len(result['ladder']), 10)
    self.assertIn(result['anchors']['highest_retained_score']['identity'], markdown)
```

- [ ] **2. Activate facade atomically, not old math.**

```python
def calculate_snapshot(csv_path, parameters, provenance):
    calculation = result_v2.calculate_v2(csv_path, parameters, provenance)
    return calculation, window_report.render_markdown(calculation)

def make_envelope(request, execution, *, calculation, errors):
    return result_v2.make_v2_envelope(request, execution, calculation=calculation, errors=errors)
```

runner既有顺序保留：source→calculate一次→make→renderHTML→atomic files；失败清掉旧report但保存证据。verify-transport／diagnostic-failure通过新make生成v2失败。inventory依shared row字段应无需语义重写；publisher仍调用facade验证及现有capability证据规则。只改证明必要的引用，不重写append-only机制。
- [ ] **3. Extend existing temp-Git fixtures for both versions.** `RunnerTests.publish_refresh_fixture`增加`schema_version=1`参数，v1显式用result_v1，v2用新public入口；默认保留1以继续测试真正旧fresh→新recompute。新增v2source分支，验证都物化固定CSV原始bytes、155历史status、新结果schema2／10阶。现代五来源fixture由`test_refresh_sources.FIX/URLS`生成154行；只把结果版本分派参数化，别以新算法改变source inventory。

```python
for version in (1, 2):
    # Each subtest uses a fresh temporary repo from the existing RunnerTests fixture.
    result = self.publish_refresh_fixture(schema_version=version)
    self.assertEqual(result['schema_version'], version)
```

上段循环实际放在独立subTest fixture中，不能在同一已有results branch连续创建两次；复用setUp创建repo的独立helper或拆成两方法。`publish_refresh_fixture`内仅schema分派，其真实source-map／CSV/hash核对全部保留。
- [ ] **4. Prove local bare-remote mixed-version publication and failure behavior.** 使用现有PublishTests remote，先合法v1成功再v2成功、重复相同run幂等、不同bytes同定位拒绝、失败不推进latest-success／latest-refresh、较旧成功不倒退pointer。保留source vs blob hash拒绝。对既有「missing_candidate删光proof／operation=null」「models parse早期失败」「models fetch早期失败」各跑v1与v2生成器；晚期仍拒绝，早期诊断仍发布为failed。正常五来源154fixture生成v2、完整写入bare results并回读validate；现代capabilityguard不可被schema分支绕过。
- [ ] **5. GREEN full integration and branch review.** Run scoped `python3 -m unittest discover -s tests -p 'test_bridge*.py'`，再一次`python3 -m unittest discover -s tests`。核对当前固定probewindow主名單／trace，并跑相同OAT比较（直接对production `select_chain`与原实验window比较，非在测试里复制公式）；要保留新high+.25反例，不能硬断言所有扰动都不变。移除未用v2入口不存在的过渡调用，保持result_v1可读。

保存全套命令／结果及base diff；`git diff --exit-code "$(cat /tmp/opencode/window-knee-execution-base.sha)" -- runs scripts/compute_frontier.py scripts/ladder.py scripts/ladder_extra.py experiments/2026-09-27-cp-chain-sensitivity experiments/2026-09-27-cp-chain-regularized`应无差异。起点与执行ledger核对，不使用猜测SHA。
- [ ] **6. Commit／review:** `feat: activate v2 window ladder in the Chat CI bridge`；独立全分支review重点mixed-version bootstrap、身份guard、numeric errors、renderer与来源证据。未通过不进入发布。

## Task 6: Documentation, deployment and correlated cloud acceptance

**Files:** Modify `AGENTS.md`, `README.md`, `chatgpt-instructions.md`, `docs/contracts/chat-ci.md`; create `docs/superpowers/notes/2026-09-27-window-knee-acceptance.md`。仅当真实配置不同才改`.github/workflows/chat-execution.yml`；当前workflow无需因result v2更换触发方式。

**Interfaces:** 沿用request v1、`efficiency-run/<uuid>`、`bridge/requests/<uuid>.json`、private `ga815647/model-efficiency-frontier` main/results；新的v2字段按spec精确读取。

- [ ] **1. Update docs to match verified local capabilities, with cloud status still pending.** 写清final-only两入口、新算法policy／参数、cut代表与trace、Claude比较、B effects、v1读法、fresh缺口；不让Chat从v1表手推v2。使用者不需重贴bootstrap；settings安装状态不因发布推定。保留旧spec／probe作为历史证据，README新输出写新路径而非覆盖旧run。
- [ ] **2. Check docs and commit.** `git diff --check`；逐项核对spec所有根／row字段与实际JSON键一致；确认两卡标签没有旧「平衡／最高CP省钱」语义。记录scoped／full tests、review结论、本地HTML证据。commit `docs: document window ladder v2 and migration semantics`。
- [ ] **3. Publish only after reviews pass.** `git fetch origin main results`；确认main是工作HEAD祖先，再`git push origin HEAD:main`（已选发布流程，不force）。如果远端分歧，先检查新commits，不能覆盖。以`gh api repos/ga815647/model-efficiency-frontier/commits/main --jq .sha`读回并核对产品SHA。合并产生任何产品改变时只重跑受影响检查／必要全套。
- [ ] **4. Submit one pinned recompute and one refresh acceptance request.** 用实际产品SHA及uuid4创建唯一branch；下面是可执行提交骨架，须从已发布产品工作树运行，保存回传commits以关联：

```python
import base64, datetime, json, pathlib, subprocess, uuid
repo = 'ga815647/model-efficiency-frontier'
def api(path, payload=None):
    cmd = ['gh','api',f'repos/{repo}/{path}']
    if payload is not None:
        cmd += ['--method','POST' if path=='git/refs' else 'PUT','--input','-']
    return json.loads(subprocess.check_output(cmd, input=json.dumps(payload).encode() if payload else None))
product = api('commits/main')['sha']
assert product == subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip()
records = []
for operation in ('recompute','refresh'):
    identity = str(uuid.uuid4())
    branch = 'efficiency-run/' + identity
    request = dict(schema_version=1, request_id=identity,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        product_sha=product, operation=operation,
        parameters=dict(gpt_factor=18,grok_factor=16,min_score=0,
            min_score_reason='用戶確認：同版本全候選情境比較；固定視窗正式改制驗收',max_cost=None))
    if operation=='recompute':
        request['source_snapshot'] = dict(commit=product,path='runs/2026-09-26-general-grok16/candidates.csv')
    api('git/refs',dict(ref='refs/heads/'+branch,sha=product))
    result = api('contents/bridge/requests/'+identity+'.json',dict(branch=branch,
        message='test: window v2 '+operation+' acceptance',
        content=base64.b64encode((json.dumps(request,ensure_ascii=False,indent=2)+'\n').encode()).decode()))
    records.append(dict(request=request,branch=branch,request_commit=result['commit']['sha']))
    pathlib.Path('/tmp/opencode/window-v2-requests.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    print(operation,identity,result['commit']['sha'])
```

提交响应不明时以同一UUID／branch/path回读，核对sole added path和parent，不能生成新UUID掩盖未知结果。
- [ ] **5. Read correlated results, not just green badges.** 按各request commit查`actions/runs?event=push&head_sha=...`，核对branch／run_id／attempt；完成后固定results commit，读精确`results/<uuid>/<run>-<attempt>/result.json`并用public validate_envelope验证。逐字段核对request／product／run／parameters／source locator；recompute断言155status、19chain、10final、两个anchors xhigh／Luna low、invalidmaxexcluded、所有cut winner final。下载该run HTML artifact，与相同固定commit report.html做`cmp`／SHA256；check JSON／Markdown／HTML主身份一致。

refresh若仍missing_candidate，确认无ladder/anchors、run failed且诊断证据完整发布、不推进成功pointer；若源站已补齐，则按完整来源／identity／inventory条件验证真实成功，不预设候选数必154。不能因为fixture有154就宣称live数量。失败若因本次代码回归，修复→review→必要重验；不能把它冒称既有来源缺口。
- [ ] **6. Record and publish acceptance status.** 在acceptance note记录实际request／product／result SHA、run URL、artifact hash、日期、参数及来源限制；AGENTS／README／Chat指示标明实装，旧v1只是历史。commit并push文档，确认git clean。只有Git指示更新才说Project不用重贴；OpenCode此次验收不冒充新的Chat端实测。

## Plan self-review / completion gate

- [x] Spec §§2.1–2.3→Task1；§§3.1–3.3→Task2；§4.2／4.3→Tasks3+5；§3.2及§5→Tasks4+6；§6→各task测试与cloud验收。
- [x] 核对所有跨task函数名、参数、row／trace键一致；Task3仍默认v1，Task5才激活v2。Task4测试导入window_report；Task5 EXECUTION导入test_bridge_result_v2的已定义fixture。
- [x] 五个Review Focus都有所属task与断言；补上B通过插值影响A但winner仍是A的解析案例，以及含非法身份旧cut的v1历史可读案例。
- [x] 自读确认无空白政策步骤；动态部署ID只在执行时生成并回读，执行起点SHA有明确保存命令。计划仍待使用者审阅。
