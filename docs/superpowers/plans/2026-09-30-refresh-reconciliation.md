# Fresh Inventory Reconciliation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓已淘汰舊候選退役、當前缺 task cost 的已觀測候選明示退出，解除 GPT-6.1 fresh 的阻塞，同時保持來源、身份及發布驗證。

**Architecture:** 純來源分類模組擁有 observed／usable／tracked／retired 及退出摘要；現有 acquirer 用它生成證據，共用 inventory validator 從原頁再次驗證。Git 消費端只從可信固定產品判定新／legacy 政策，publisher 使用已驗證 handoff 與執行開始時固定的 results ref；renderer 只展示同一結果，不重算選檔。

**Tech Stack:** Python 3.11 標準庫、unittest、Decimal、Git／GitHub Actions／gh CLI、離線單檔 HTML；不新增套件、服務或 credentials。

**Spec:** `docs/superpowers/specs/2026-09-30-refresh-reconciliation-design.md`（使用者於書面審閱請求後回覆「繼續」，已確認；執行者必讀全篇）。

**Status:** 使用者審阅計畫並釐清每次退役／缺值判定後回覆「可以了」，計畫已批准，開始產品實作。沿用既有 Subagent-driven，不重問執行方法。Issue #2 沿前述已確認的 bounded 短設計另外實作／驗收，不混入本計畫來源子系統。尚未授權正式發布或提交雲端驗收請求。

## Global Constraints

- 自動排行退役只依當次 AA `deprecated=true`；缺欄／null 不推定淘汰，其他型別拒絕。
- 分類優先序：deprecated → estimated → missing_score → missing_task_cost → zero_cost → usable_paid。
- 未退役、非 estimated、有有效分數但當前 task cost 缺值：本次排除、不阻擋，仍追蹤；不沿用舊價、不套 successor／其他 effort 資料。
- 前次受追蹤身份 estimated／missing_score／zero_cost 仍硬失敗為 `present_candidate_unusable`；真正未觀測且無退出依據仍 `missing_candidate`，三遍核對狀態照實保留。
- `tracked_slugs = (P ∪ U) − R`；P 是已驗證前次受追蹤集合，U 是本次可用 public 集合，R 是當次明確退役集合。
- 新 source policy 固定 `observed-inventory-v1`；產品標記 `bridge/refresh-policy.json` 精確為 `{"policy":"observed-inventory-v1"}`，不得從 untrusted map 推定可信 legacy 模式。
- request v1／result v2／歷史 v1 的精確根欄位及 row 不改；缺價行不能進付費 CSV 或偽裝成數字 cost 的 `candidate_statuses`。
- 單一 General／同 benchmark version／同 cost basis、floor＋理由、Grade-A/B、Grok／Muse 四個精確 crosschecks、官方 models proof 與 Contributor max Standard-only guard 不降級。
- CP-new-high＋固定兩分視窗、final-only 兩入口、Claude 僅比較不推薦、GPT ×18／Grok ×16／Contributor ×1 不改。
- 原 `runs/`、已發布 results、`scripts/compute_frontier.py`、`scripts/ladder.py`、`scripts/ladder_extra.py`、既有實驗及歷史 fixture 原樣保留；新 fixture 寫新檔。
- 固定 9/26 重算不套今天 deprecated、不抓新來源；新成功 refresh 的後續重算保留來源退出 caveats。
- 無 paid 候選延續 `empty_paid`；有 paid 候選但 floor／cap 排空仍可輸出合法空階梯／null anchors。
- 只做 Chat＋按需 HTML，不部署網站、不恢復 Notion；bootstrap 定位不變，不把 Git push 當 Chat 已同步。
- 逐 task TDD、獨立 spec／quality review、單 writer；整條分支完成前不得發布中間態。每次 commit 只 stage 本 task 的具體檔案。

## Review Focus

1. `deprecated` 缺欄、null、False、數字 0/1 及字串 `"false"`：不能把 false-like 值都當有效 boolean，亦不能把未知當 true（Task 1）。
2. task cost 改動小到轉 float 後相同：新證據驗證仍須用 Decimal 抓到 CSV／原頁的精度差，不只沿用原 float 關係檢查（Task 2）。
3. 新產品刪掉 reconciliation、冒用舊 product SHA、或 policy blob 是 symlink：必須在 Git write／pointer 前拒絕，不因 bootstrap 較新／source map 自稱 legacy 而降級（Task 3）。
4. 新的 latest-success 是 recompute、floor／cap 排除部分候選：下一輪仍取固定 latest-refresh 的完整 tracked inventory，不按 final 名單決定是否追蹤（Task 3）。
5. 退出模型名稱含 Markdown／HTML 攻擊文字：結論附近摘要須 escape，不能變成腳本，也不能因 source-only 行不在 CSV 就遺漏提示（Task 4）。

---

## File Map and Execution Order

| Files | Responsibility |
|---|---|
| `scripts/refresh_inventory.py` | Task 1：純分類、追蹤對帳、blocking 分類、deterministic 退出 caveats |
| `scripts/aa_public.py` | Task 1：deprecated 的 optional boolean 嚴格解析 |
| `tests/refresh_inventory_fixtures.py`, `tests/test_refresh_inventory.py` | Tasks 1–2：解析型小 record、Flight 生成、來源證據 unit bundle |
| `bridge/source_policy.py`, `tests/test_source_policy.py` | Task 2：只解碼可信產品 policy bytes，不讀 moving refs、不執行來源程式 |
| `bridge/inventory.py`, `tests/test_bridge_inventory.py` | Task 2：舊 paid 檢查＋新 raw／parsed／hash／分類／摘要檢查 |
| `scripts/refresh_snapshot.py`, `bridge/refresh-policy.json` | Task 3：新取得流程及正式產品 policy 標記 |
| `bridge/runner.py`, `bridge/publish.py`, `.github/workflows/chat-execution.yml` | Task 3：可信產品／前次來源上下文、固定 Git 消費、發布與 CLI 接線 |
| `tests/fixtures/refresh/current-inventory-2026-09-30-flight.html`, `tests/fixtures/refresh/current-inventory-2026-09-30.json` | Task 3：含 GPT-6.1 五檔、兩個舊缺价身份及四個 version anchors 的新最小 fixture／provenance |
| `tests/test_refresh_sources.py`, `tests/test_bridge_runner.py`, `tests/test_bridge_publish.py`, `tests/test_bridge_workflow.py` | Task 3：完整管線、legacy、新政策、失敗 evidence、pointer／transport 回歸 |
| `bridge/window_report.py`, `tests/test_window_report.py`, `chatgpt-instructions.md`, `docs/contracts/chat-ci.md` | Task 4：退出摘要在結論附近，來源及 Chat 語義一致 |
| `README.md`, `AGENTS.md`, `docs/superpowers/notes/2026-09-30-refresh-reconciliation-acceptance.md` | Tasks 4–5：分支實作／正式發布／cloud／Chat 驗收分項帳 |

順序 Task 1 → 5。Task 1–2 只建立可獨立測試的能力，不先切正式 producer；Task 3 一次接通 producer／validator／Git consumers／publisher，以免中間態把新 map 當 legacy 發布。Task 4 展示同一已驗證資料，Task 5 驗收與整合。

目前工作區為已有 linked worktree `.worktrees/window-knee`、branch `docs/refresh-reconciliation`，原 root `feat/chat-ci` 不動。使用 worktree skill 先確認現有隔離，不另自動建立第二個 worktree。執行開始寫 ledger `docs/superpowers/notes/2026-09-30-refresh-reconciliation-acceptance.md`，記錄 `git rev-parse HEAD` 的起點，後續保護檔比較只用該固定值。上次未修改產品基線為 229 tests；執行時再跑一次，不拿規劃時的結果替代。

執行開始時建立 ledger（若檔案已存在，先讀其狀態並沿用原 execution base，不覆寫）：

```python
from pathlib import Path
import subprocess

ledger = Path('docs/superpowers/notes/2026-09-30-refresh-reconciliation-acceptance.md')
base = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
with ledger.open('x', encoding='utf-8') as stream:
    stream.write('# Refresh Reconciliation Acceptance\n\nExecution base: ' + base +
                 '\n\n狀態：計畫已批准，產品實作開始；尚未發布或完成 live 驗收。\n')
```

## Task 1: Pure Source States and Tracking

**Files:** Create `scripts/refresh_inventory.py`, `tests/refresh_inventory_fixtures.py`, `tests/test_refresh_inventory.py`. Modify `scripts/aa_public.py:116-144` and deprecated scalar cases in `tests/test_refresh_sources.py`.

**Interfaces:**
- Consumes: `parse_leaderboard(html) -> list[dict]` 的原精度 parsed records、已確認 `previous_slugs: set[str]`。
- Produces: `POLICY = 'observed-inventory-v1'`, `DISCLOSURE_PREFIX = '來源退出：'`。
- `classify_record(record: dict) -> dict` 恰好返回 `{state, reason}`，三種 state 與五種非 null reason 沿 spec。
- `build_reconciliation(records: list[dict], previous_slugs: set[str]) -> dict` 返回 spec 的精確六欄，沒有 fail 時額外欄位。
- `blocking_candidates(reconciliation: dict) -> dict[str,list[str]]` 恰好 keys `missing`／`unusable`，sorted slug lists。
- `tracked_public_slugs(source_map: dict|None, fallback: set[str]) -> set[str]`：合法新版取 tracked；legacy 用 fallback；新版 shape／policy 不合法報 `SourceError('previous_inventory_missing', LEADERBOARD, ...)`，不忽略坏欄。
- `source_exit_caveats(records: list[dict], reconciliation: dict) -> list[str]`：只披露 P 中本次退役／缺价的身份，按 slug 排序，不修改輸入。

- [ ] **1. Write parsed-record helper and state/sequence tests.** Fixture helper 保留 Decimal、None 與 boolean，不預先把坏值 coercion：

```python
from decimal import Decimal

def record(slug, *, name=None, score='40', cost='1', estimated=False, deprecated=False):
    scalar = lambda value: Decimal(value) if type(value) is str else value
    return dict(slug=slug, name=name or slug, creator='Fixture',
        score=scalar(score), cost_per_task=scalar(cost), is_estimated=estimated,
        deprecated=deprecated, price1m_input=None, price1m_output=None, cache_hit_price=None)

def test_retired_and_missing_cost_do_not_block(self):
    rows = [record('inkling', cost=None), record('minimax-m2-7', cost=None, deprecated=True),
            record('gpt-6-1-sol', score='51.8332597011541', cost='0.7241670655535033')]
    before = deepcopy(rows)
    rec = build_reconciliation(rows, {'inkling', 'minimax-m2-7'})
    self.assertEqual(rec['tracked_slugs'], ['gpt-6-1-sol', 'inkling'])
    self.assertEqual(rec['retired_slugs'], ['minimax-m2-7'])
    self.assertEqual(rec['status_by_slug']['inkling'],
                     {'state':'observed_unusable', 'reason':'missing_task_cost'})
    self.assertEqual(blocking_candidates(rec), {'missing':[], 'unusable':[]})
    self.assertEqual(rows, before)

def test_retired_absence_and_active_absence_are_different(self):
    first = build_reconciliation([record('old', deprecated=True), record('active', cost=None)],
                                 {'old', 'active'})
    second = build_reconciliation([record('new')], set(first['tracked_slugs']))
    self.assertEqual(blocking_candidates(second), {'missing':['active'], 'unusable':[]})
    restored = build_reconciliation([record('active'), record('old')], set(first['tracked_slugs']))
    self.assertEqual(restored['tracked_slugs'], ['active', 'old'])

def test_estimated_missing_score_zero_and_unknown_are_precise(self):
    rows = [record('estimated', estimated=True), record('no-score', score=None), record('free', cost=0)]
    rec = build_reconciliation(rows, {'estimated','no-score','free','absent'})
    self.assertEqual(blocking_candidates(rec),
                     {'missing':['absent'], 'unusable':['estimated','free','no-score']})
```

`TestCase` imports `deepcopy`、上述 helper 及本 task 所有 interfaces。再加有成本但 deprecated=true、非退役成本恢復、未追蹤新缺分数／估計值不阻擋、已退役即使 estimated/score/cost 都缺也優先退休、arrays sorted/unique、P/U/R 公式、輸入不 mutation，以及未知 reconciliation policy 不能 legacy fallback。

- [ ] **2. RED.** Run `python3 -m unittest discover -s tests -p 'test_refresh_inventory.py' -v`；預期 missing module／functions。deprecated parser 測試用現有 `flight_record()` 及真實欄位，對 `True,False,None`／缺欄成功，對 `0,1,'false',{},[]` 逐一預期 `invalid_measurement`，不能只測 helper。
- [ ] **3. Implement pure functions and optional boolean.** 順序不允許從 cost 推定退休：

```python
if item.get('deprecated') is True:
    return {'state':'retired', 'reason':'deprecated'}
if item['is_estimated']:
    return {'state':'observed_unusable', 'reason':'estimated'}
if item['score'] is None:
    return {'state':'observed_unusable', 'reason':'missing_score'}
if item['cost_per_task'] is None:
    return {'state':'observed_unusable', 'reason':'missing_task_cost'}
if item['cost_per_task'] == 0:
    return {'state':'observed_unusable', 'reason':'zero_cost'}
return {'state':'usable_paid', 'reason':None}
```

在 parser 中只有 `value is None or type(value) is bool` 合法，其他值 `SourceError('invalid_measurement', LEADERBOARD, slug + ': deprecated')`。沿原 `_scalar` 數值驗證，不補價格。blocking 的 missing=P−observed，unusable 只含 P∩observed 中非退休且 reason 不為 missing_task_cost 的 observed_unusable。摘要精確模板：`來源退出：{name}（{slug}）：來源標示淘汰，本次未參戰，已退出後續強制追蹤。` 或 `來源退出：{name}（{slug}）：當前 task cost 缺值，本次未參戰，未沿用舊價。` 不印幾百個非 P 舊模型。

`build_reconciliation` 保留 parser 的唯一 slug 前提；完整返回六欄如下，後續 consumers 不另重寫公式：

```python
status = {row['slug']: classify_record(row) for row in records}
usable = {slug for slug, fact in status.items() if fact['state'] == 'usable_paid'}
retired = {slug for slug, fact in status.items() if fact['state'] == 'retired'}
return dict(policy=POLICY, previous_tracked_slugs=sorted(previous_slugs),
            observed_slugs=sorted(status), tracked_slugs=sorted((previous_slugs | usable) - retired),
            retired_slugs=sorted(retired), status_by_slug=status)
```

`blocking_candidates` 從這六欄計算，不以 included 集合推定缺席：

```python
previous = set(reconciliation['previous_tracked_slugs'])
status = reconciliation['status_by_slug']
return dict(missing=sorted(previous - set(status)),
            unusable=sorted(slug for slug in previous & set(status)
                            if status[slug]['state'] == 'observed_unusable'
                            and status[slug]['reason'] != 'missing_task_cost'))
```
- [ ] **4. GREEN and regression.** Run `python3 -m unittest discover -s tests -p 'test_refresh_inventory.py' -v`、`python3 -m unittest discover -s tests -p 'test_refresh_sources.py' -v`，確認新 core 與舊來源測試通過；此 task 不變更 producer 的 lost 判定。
- [ ] **5. Commit.** `git add scripts/refresh_inventory.py scripts/aa_public.py tests/refresh_inventory_fixtures.py tests/test_refresh_inventory.py tests/test_refresh_sources.py`；`git diff --cached --check`；`git commit -m 'feat: model observed usable and retired public candidates'`。

## Task 2: Strict Proof Validation and Trusted Policy Decoder

**Files:** Create `bridge/source_policy.py`, `tests/test_source_policy.py`, `tests/test_bridge_inventory.py`. Modify `bridge/inventory.py:11-66`, `tests/refresh_inventory_fixtures.py`.

**Interfaces:**
- Consumes: Task 1 的四個純對帳／摘要 functions、`parse_leaderboard`、既有 CSV／result paid 關係。
- Produces: `PolicyError(ValueError)`、`decode_refresh_policy(data: bytes|None) -> str|None`；None 是沒有 marker 的可信舊產品，JSON 重複 key、未知／額外 key、非字串 policy、未知值及非法 UTF-8 都拒絕。
- Extend `validate_fresh_inventory(data, source_map, envelope, *, error_code, refresh_policy: str|None=None, evidence: dict[str,bytes]|None=None, expected_previous_slugs: set[str]|None=None) -> None`。保留舊 callers 的合法 legacy 檢查；new policy 必須有 proof，新 map 不得在 legacy mode 被當成合格。
- Fixture helpers `flight(records: list[dict]) -> bytes`、`inventory_bundle(records: list[dict], previous_slugs: set[str]) -> tuple[bytes,dict,dict,dict[str,bytes]]`；返回 CSV bytes、source_map、成功 v2 envelope、以檔名索引的 evidence。這是 validator unit fixture，不聲稱經完整版本／Meta取得流程。

- [ ] **1. Add Flight serializer and proof unit bundle.** Decimal 以 raw JSON number 發出，不能用 `default=str` 使 measurement 變成字串：

```python
def numeric_json(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k) + ':' + numeric_json(v) for k,v in value.items()) + '}'
    if isinstance(value, list):
        return '[' + ','.join(numeric_json(v) for v in value) + ']'
    return json.dumps(value, ensure_ascii=False, allow_nan=False)

def flight(records):
    objects = [dict(slug=r['slug'], name=r['name'], shortName=r['name'],
        modelCreatorName=r['creator'], intelligenceIndex=r['score'],
        intelligenceIndexIsEstimated=r['is_estimated'],
        intelligenceIndexCostPerTask=r['cost_per_task'], deprecated=r['deprecated']) for r in records]
    return ''.join('<script>self.__next_f.push([1,' + json.dumps(numeric_json(obj)) + '])</script>'
                   for obj in objects).encode()
```

`inventory_bundle` 用 `parse_leaderboard(flight(records).decode())` 的 canonical records 建 rec；U 每行填既有 `scripts.fetch_aa.COLUMNS`，沿 `_model_effort` 建 model/effort/identity/model_version，provider=`AA-public (first-party/median)`、pricing_plan=`published-price`、General v4.3.2／api、date=`2026-09-30`、is_free=false、notes=`GRADE-A fixture; slug={slug};`。所有未使用欄位填空字串；`source_by_slug` 的 score/cost 取 parsed 原值，inventory.contributor_efforts=[]、contributor=[]、excluded 列所有非 U 的 slug/name/reason。

用 `csv.DictWriter` 建 CSV，provenance 含 acquired locator SHA-256、同 date、inferred version 及 `['Inventory-unit fixture, not live acquisition'] + source_exit_caveats(...)`。**从 `bridge.result` import `calculate_snapshot`／`make_envelope`**，不能從仍為v1的 `test_bridge_result` import 同名函數；只從該測試檔取PARAMETERS。用 `test_bridge_request.request_data()` 生成真實 v2 envelope，不 mock validator。evidence 存 `leaderboard.html`、`leaderboard_records.json`（與 producer 相同 `json.dumps(..., default=str)`）、`sources.json`（當次 fixture bytes 的 hash，不寫成原完整頁 hash）。

`inventory_bundle` 的 calculation／envelope 部分使用暫存 CSV，回傳前讀回完整 bytes；計算不需要真 Git context，產品policy的Git信任鏈留Task3整合測試：

```python
from bridge.result import calculate_snapshot, make_envelope
from test_bridge_request import request_data
from test_bridge_result import PARAMETERS

with tempfile.TemporaryDirectory() as temp:
    path = Path(temp) / 'candidates.csv'
    path.write_bytes(data)
    calculation, _ = calculate_snapshot(path, PARAMETERS, provenance)
envelope = make_envelope(request_data(), dict(request_commit_sha='b' * 40,
    run_id='inventory-unit', run_attempt=1,
    run_url='https://github.com/example/actions/runs/inventory-unit'),
    calculation=calculation, errors=[])
return data, mapping, envelope, evidence
```

- [ ] **2. Write valid proof and tamper tests, then RED.**

```python
def test_current_cost_exclusion_is_proven_not_invented(self):
    rows = [record('inkling', cost=None), record('minimax-m2-7', deprecated=True, cost=None),
            record('gpt-6-1-sol', score='51.8332597011541', cost='0.7241670655535033')]
    data, mapping, envelope, evidence = inventory_bundle(rows, {'inkling','minimax-m2-7'})
    validate_fresh_inventory(data, mapping, envelope, error_code='bad-proof',
        refresh_policy=POLICY, evidence=evidence, expected_previous_slugs={'inkling','minimax-m2-7'})
    for key in ('retired_slugs', 'tracked_slugs', 'observed_slugs'):
        bad = deepcopy(mapping)
        bad['reconciliation'][key].append('invented')
        with self.subTest(key=key), self.assertRaises(InventoryError):
            validate_fresh_inventory(data, bad, envelope, error_code='bad-proof',
                refresh_policy=POLICY, evidence=evidence,
                expected_previous_slugs={'inkling','minimax-m2-7'})

def test_decimal_difference_cannot_hide_behind_equal_float(self):
    data, mapping, envelope, evidence = inventory_bundle([record('paid', cost='1.0000000000000000000000001')], set())
    bad_data = data.replace(b'1.0000000000000000000000001', b'1.0000000000000000000000002')
    self.assertNotEqual(data, bad_data)
    self.assertEqual(float('1.0000000000000000000000001'), float('1.0000000000000000000000002'))
    with self.assertRaises(InventoryError):
        validate_fresh_inventory(bad_data, mapping, envelope, error_code='bad-proof',
                                 refresh_policy=POLICY, evidence=evidence)
```

另逐一 tamper raw/hash/parsed/estimated/deprecated/reason/P/disclosure；移除新版 block／evidence、把 null 改旧 cost、把 null 當 zero、legacy mode 帶新版 map、缺退出 caveat都拒絕。decoder 对 `None` 与精确 marker 成功，對 `{"policy":true}`、重複 policy、未知policy、額外key、坏 bytes拒絕。Run `python3 -m unittest discover -s tests -p 'test_bridge_inventory.py' -v` 及 `-p 'test_source_policy.py' -v`；預期缺新 keyword/module/function。
- [ ] **3. Implement strict decoding and shared validation.** 保留原 paid checks，new mode 再執行：

```python
parsed = parse_leaderboard(evidence['leaderboard.html'].decode('utf-8'))
sources = strict_json(evidence['sources.json'])
if sources['sha256_by_url'][LEADERBOARD] != sha256(evidence['leaderboard.html']).hexdigest():
    raise ValueError('leaderboard hash mismatch')
saved = strict_json(evidence['leaderboard_records.json'])
canonical = lambda value: json.dumps(value, default=str, sort_keys=True, allow_nan=False)
if canonical(saved) != canonical(parsed):
    raise ValueError('parsed record mismatch')
rec = source_map['reconciliation']
previous = set(rec['previous_tracked_slugs'])
if expected_previous_slugs is not None and previous != expected_previous_slugs:
    raise ValueError('previous tracking mismatch')
if rec != build_reconciliation(parsed, previous) or any(blocking_candidates(rec).values()):
    raise ValueError('reconciliation mismatch')
```

`strict_json(data:bytes)->object` 是本 task 在 `bridge/inventory.py` 新增的 private helper，object_pairs_hook 拒絕 duplicate keys、parse_constant 拒絕 NaN/Infinity。比較前先要求六欄精確、arrays 是 sorted unique strings、status_by_slug shape精確（不能靠 Python `True==1` 過檢）。source date 要與 envelope、public CSV 與 source_by_slug 一致；U 恰好等於 inventory／source_by_slug／CSV public slugs；excluded 與所有非 U parsed record 的 reason一致。以 Decimal 比 CSV 原始 score/cost 與 parsed 原值，不先float；保留原 envelope float relational checks。每個 expected exit caveat 恰好一次且不能冒造同 prefix 的額外退出；Meta／Contributor 原檢查不移除。
- [ ] **4. GREEN and legacy regression.** Run 新兩檔、`python3 -m unittest discover -s tests`。本 task 尚無產品 marker／producer切換，現有 legacy fixtures 應仍過檢。
- [ ] **5. Commit.** Stage 本 task 六個具體檔案（含 fixture helper），`git diff --cached --check`，commit `feat: validate observed inventory proof and product policy bytes`。

## Task 3: One Integration Switch Across Acquisition, Git Reads and Publication

**Files:** Create `bridge/refresh-policy.json`, `tests/fixtures/refresh/current-inventory-2026-09-30-flight.html`, `tests/fixtures/refresh/current-inventory-2026-09-30.json`。Modify `scripts/refresh_snapshot.py:76-139,203-252,316-339`, `bridge/runner.py:142-189,211-248,264-303`, `bridge/publish.py:30-51,208-286,347-404`, `.github/workflows/chat-execution.yml:112-113`, `tests/refresh_inventory_fixtures.py`, `tests/test_refresh_sources.py`, `tests/test_bridge_runner.py`, `tests/test_bridge_publish.py`, `tests/test_bridge_workflow.py`。

**Interfaces:**
- Consumes: Tasks 1–2 全部 interfaces、既有 `_read/_commit/_ancestor/_has_file`、verified `handoff/product.sha`。
- Produces: `_refresh_policy(repository:Path, product_sha:str) -> str|None`，以固定 Git ordinary blob 調用 decoder；product commit 必是已核准當前 checkout 的 ancestor，沒有 marker才 legacy。
- `_inventory_evidence(repository:Path, publication_sha:str, prefix:str) -> dict[str,bytes]` 只讀固定 publication 的 `snapshot/evidence/{leaderboard.html,leaderboard_records.json,sources.json}`，不 consult moving refs。
- Extend `_fresh_inventory(..., error_code, refresh_policy=None, evidence=None, expected_previous_slugs=None)`，轉接 Task 2，仍保持 RunnerError 邊界。
- Extend `publish_result(output, *, remote, branch='results', source_repository:Path|None=None, trusted_product_sha:str|None=None) -> str`。success refresh（包括 legacy）必須有可信 context；缺 context拒絕。failed／recompute 不為此新增不必要來源模式門檻。
- Publisher CLI新增 `--source-repository` 與 `--product-sha-file`。二者只來自 workflow 常量路徑／verified handoff，不是 request fields；product SHA 不由 envelope 自報決定。

- [ ] **1. Create new minimized fixture from fixed primary values.** 不改 `failed-two-costs-flight.html`。以其中四個 Grok／Muse anchors 的 parsed values，加以下 exact records 用 Task 2 Flight serializer產生新檔（creator改為各真實creator），MiniMax flag=true、Inkling flag=false，GPT五檔flags皆false：

```python
gpt = [
    ('gpt-6-1-sol','max','51.8332597011541','0.7241670655535033'),
    ('gpt-6-1-sol-xhigh','xhigh','51.0377679093761','0.39286117158850653'),
    ('gpt-6-1-sol-high','high','50.2377777519769','0.31914442375664703'),
    ('gpt-6-1-sol-medium','medium','47.7833271274065','0.21370088267875537'),
    ('gpt-6-1-sol-low','low','42.0835618555848','0.13075190869859377'),
]
old = [record('inkling', name='Inkling (xhigh)', score='24.9847810999384', cost=None),
       record('minimax-m2-7', name='MiniMax-M2.7', score='22.7578150287271', cost=None, deprecated=True)]
```

provenance JSON 記 fixed publication `ef77e1fff6980164aac5c0610ead7eff26bcd671`、run36666859368-1、original leaderboard hash `b030c6f00885a629ab46d6ec83ea06fd5ecb8b828f91721f23bfa6b4a46df648`、新 fixture 自己的hash及「選取原值、重新生成最小 Flight transport，非完整原頁」。原頁曾獨立 hash 驗證；如需再核對從固定Git原檔讀，不必重新抓現在頁來改fixture。`refresh_pages()` 測試helper取新leader＋既有四份grok/muse/meta/models fixtures，禁網。
- [ ] **2. Write acquisition red tests and real Git context helpers.**

```python
def test_fresh_current_inventory_succeeds_without_old_cost(self):
    pages = refresh_pages()
    with tempfile.TemporaryDirectory() as temp:
        dest = Path(temp) / 'fresh'
        prov = refresh_snapshot(dest, previous={'slugs':['inkling','minimax-m2-7']}, fetch=pages.__getitem__)
        with (dest / 'candidates.csv').open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        public = {r['model_version'] for r in rows if r['pricing_plan'] != 'Contributor'}
        self.assertTrue({entry[0] for entry in GPT_ENTRIES}.issubset(public))
        self.assertFalse({'inkling','minimax-m2-7'} & public)
        mapping = json.loads((dest / 'evidence/source_map.json').read_text())
        self.assertIn('inkling', mapping['reconciliation']['tracked_slugs'])
        self.assertNotIn('minimax-m2-7', mapping['reconciliation']['tracked_slugs'])
        self.assertTrue(any('未沿用舊價' in c for c in prov['caveats']))
```

`GPT_ENTRIES` 與 `refresh_pages()` 加入 fixture helper，GPT_ENTRIES就是上方五tuple，不重新估值。下一次 leader去掉minimax record成功；去掉tracked Inkling報missing；改Inkling cost恢復可入列；改估計值報present_candidate_unusable。Minifier只刪 exact slug record，不用大範圍字串replace誤刪其他effort。

pipeline測試使用暫存真Git：產品commit內保存 marker（new或缺marker的legacy）、核准archive的previous source map，request唯一commit是產品child，results ref在執行前固定。既有 `PublishTests.valid_refresh_output()` 的legacy result沿原fixture保留；成功refresh所有callers提供來源repo及實際產品SHA，不再用 `a*40` 假產品去證明policy。測試helper `product_context(base:Path, previous:dict, *, new_policy:bool) -> tuple[Path,str]` 在temp repo只建立這些控制檔、git init/config/add/commit並返回HEAD；`publish(output, context)` wrapper僅透傳可信context，不 mock decoder／inventory。

將 `product_context` 加入fixture helper；此 helper只服務publication的控制context，需要歷史materialize測試時仍沿 `RunnerTests.setUp()` 複製原有五份歷史證據，不能假造 `_historical` 所需檔案：

```python
def product_context(base, previous, *, new_policy):
    repo = Path(base) / ('source-new' if new_policy else 'source-legacy')
    repo.mkdir()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args],
                                       stderr=subprocess.PIPE).decode().strip()
    git('init', '-q')
    git('config', 'user.name', 'Fixture')
    git('config', 'user.email', 'fixture@example.com')
    archive = repo / 'runs/2026-09-26-general-grok16/public_candidate_source_map.json'
    archive.parent.mkdir(parents=True)
    archive.write_text(json.dumps(previous))
    if new_policy:
        marker = repo / 'bridge/refresh-policy.json'
        marker.parent.mkdir()
        marker.write_text(json.dumps({'policy': POLICY}))
    git('add', '.')
    git('commit', '-qm', 'trusted fixture product')
    return repo, git('rev-parse', 'HEAD')
```

每個subtest使用獨立temp base避免已存在repo；產物的request.product_sha改為回傳SHA。`publish` wrapper使用 `publish_result(output, remote=str(self.remote), source_repository=context[0], trusted_product_sha=context[1])`，failure仍保留無context發布路徑。
- [ ] **3. RED targeted suite.** Run source、runner、publish、workflow四檔；新success test應因舊 missing_candidate失敗，可信context／CLI tests應因缺參數或沒有policy接線失敗。
- [ ] **4. Switch producer and preserve diagnostics.** `_previous_slugs` 原Contributor身份解析保留；只以 `tracked_public_slugs(previous, legacy_slugs)` 覆寫public追蹤集合。取得／保存models proof及version／pricing不移序。解析完建立rec，以 `classify_record` 篩 U，非U保留 precise reason；不要對已退役垃圾行強迫解析無用effort。

```python
rec = build_reconciliation(records, prev_slugs)
blocked = blocking_candidates(rec)
source_map['reconciliation'] = rec
if blocked['missing']:
    save_missing_diagnostics(blocked['missing'], records)
if blocked['unusable']:
    save_unusable_diagnostics(blocked['unusable'], records, rec)
if any(blocked.values()):
    _json(evidence / 'source_map.json', source_map)
    code = 'missing_candidate' if blocked['missing'] else 'present_candidate_unusable'
    raise SourceError(code, LEADERBOARD, ','.join(blocked['missing'] or blocked['unusable']))
```

`source_map` 在producer內先以已完成的included／excluded／availability、contributor=[]與public inventory初始化；成功完成Contributor段後覆寫contributor／efforts。`save_missing_diagnostics(slugs, records)`／`save_unusable_diagnostics(slugs, records, rec)` 是此 task 的局部 helpers，closure 使用evidence path；前者沿原三遍核對欄位只寫真missing，後者新寫 `unusable_candidates.json`，每項 slug、當次record、精確reason，不能偽造manual review已完成。兩種同時存在都保存，primary code按上方順序，但完整報告不能遺漏另一種。new artifact加入publisher whitelist；present_candidate_unusable加入post-models-proof codes。

成功source map／sidecar／notes用同一分類，return provenance.caveats追加 Task 1 摘要。Contributor max仍先 unavailable再換價，精確previous退休證據不改。9/26 fixture中若其他paid行原已deprecated=true，測試期待數量要從當次U導出，不為維持154硬保送；固定9/26重算155稽核／10final不變。
- [ ] **5. Wire trusted policy and frozen predecessor through three consumers.** `_refresh_policy` 先 `_commit`／ancestor確認，以 `_has_file`區分真正缺檔，以 `_read`拒絕symlink/nonblob；只decoder bytes，不import Git產品程式。materialize／_previous 用來源原 envelope.product_sha，不用本次計算product來判旧snapshot；new模式讀同一固定publication的三份extra evidence。

在 `bridge/runner.py` 新增兩個Git讀取helpers，供兩個runner consumers與bootstrap publisher共用；publisher已import result／inventory，runner不import publish，因此不形成循環：

```python
from bridge.source_policy import PolicyError, decode_refresh_policy

def _refresh_policy(repository, product_sha):
    _commit(repository, product_sha)
    head = _git(repository, 'rev-parse', 'HEAD').decode().strip()
    if not _ancestor(repository, product_sha, head):
        raise RunnerError('source_product_not_authorized')
    path = 'bridge/refresh-policy.json'
    data = _read(repository, product_sha, path) if _has_file(repository, product_sha, path) else None
    try:
        return decode_refresh_policy(data)
    except PolicyError as exc:
        raise RunnerError('invalid_refresh_policy') from exc

def _inventory_evidence(repository, publication_sha, prefix):
    return {name: _read(repository, publication_sha, prefix + 'snapshot/evidence/' + name)
            for name in ('leaderboard.html', 'leaderboard_records.json', 'sources.json')}
```

對materialize／_previous現有 `_fresh_inventory` call：先取 `policy = _refresh_policy(repository, envelope['product_sha'])`，new時才取extra evidence，完整參數為 `refresh_policy=policy, evidence=proof`；舊map不能帶新reconciliation。`execute_request` 的新refresh則多傳當次已保存的P為 `expected_previous_slugs`。

新execute_request refresh先只解析一次 `_previous`，保存該map與P供producer及成功後 `_fresh_inventory`；make envelope之後、寫report前驗newproof，失敗仍無部分報表。publisher success refresh要求source_repository與trusted_product_sha、核對envelope.product_sha相同；从product checkout中执行開始時已固定的results ref讀相同P，不能在發布前重新fetch moving latest來改P。先驗policy／rawproof／P／disclosure，才呼叫原append/pointer流程。

將可信context透傳到 `_output_files(output, *, source_repository=None, trusted_product_sha=None)`，success refresh validation段新增如下。`_refresh_policy`、`_previous`取自runner；`tracked_public_slugs`取自Task1；`_previous_slugs`取自既有acquirer，保留Contributor辨識；所有RunnerError／SourceError轉為PublishError，不能繼續append：

```python
if source_repository is None or type(trusted_product_sha) is not str:
    raise PublishError('missing_trusted_product_context')
try:
    policy = _refresh_policy(source_repository, trusted_product_sha)
    if envelope['product_sha'].lower() != trusted_product_sha.lower():
        raise PublishError('product_context_mismatch')
    previous = _previous(source_repository, trusted_product_sha)
    expected = tracked_public_slugs(previous, _previous_slugs(previous)[0])
    proof = {name: files['snapshot/evidence/' + name]
             for name in ('leaderboard.html', 'leaderboard_records.json', 'sources.json')} if policy else None
    validate_fresh_inventory(files['snapshot/candidates.csv'], source_map, envelope,
        error_code='invalid_refresh_inventory', refresh_policy=policy,
        evidence=proof, expected_previous_slugs=expected if policy else None)
except (RunnerError, SourceError, InventoryError, KeyError) as exc:
    raise PublishError('invalid_refresh_inventory') from exc
```

workflow的bootstrap publisher command改為：

```sh
publication=$(python3 -m bridge.publish --output ../output \
  --remote "https://github.com/$REPOSITORY.git" \
  --source-repository ../product --product-sha-file ../handoff/product.sha)
```

prepare失敗時product路徑／handoff可不存在，但只有failed診斷可發布；success refresh缺context永不降級。CLI讀handoff為ASCII合法40hex，不能取output内另造檔；currentproduct ordinaryblob驗證沿用既有安全讀法。來源repo只讀，publisher依然在自己的temp Git repo append／fast-forward retry，不修改這個固定results ref。marker JSON於此task才加入產品。

CLI的兩個新選項不設 `required=True`，以便early failure發布；它們只對success refresh成為必要context。handoff檔不存在時傳None（由success guard拒絕）；存在但非法則拒絕，不能回退None：

```python
parser.add_argument('--source-repository', type=Path)
parser.add_argument('--product-sha-file', type=Path)
trusted_sha = None
if args.product_sha_file is not None and args.product_sha_file.exists():
    try:
        trusted_sha = args.product_sha_file.read_text(encoding='ascii').strip()
    except (OSError, UnicodeError) as exc:
        raise PublishError('invalid_product_handoff') from exc
    if not re.fullmatch('[0-9a-fA-F]{40}', trusted_sha):
        raise PublishError('invalid_product_handoff')
print(publish_result(args.output, remote=args.remote, branch=args.branch,
                     source_repository=args.source_repository, trusted_product_sha=trusted_sha))
```

上段讀handoff放在 `args = parser.parse_args(argv)` 之後；`publish_result`先把兩參數傳到 `_output_files`。固定product來源讀普通Gitblob，不直接讀可能被working tree變更的marker。
- [ ] **6. Complete regression matrix and GREEN.** 保留并重定向原late-failure proof tamper tests：原nullcost不再fail，就用真正missing slug／estimated tracked或版本完整性錯誤觸發失敗，再測刪models/hash/audit被拒；不能直接刪掉这些測試。

覆蓋：new產品剝除rec/raw/parsed/hash拒絕、可信handoff新SHA但envelope冒用oldSHA拒絕、marker symlink／duplicateJSON／未知policy拒絕、valid legacy v1/v2 markerabsent讀取與排隊發布成功、newrefresh→_previous→新fixed recompute成功、newrecompute用oldrefresh不要求newproof、floor/cap改變final不改追蹤、latest-success重算不替代latest-refresh、failed新碼仍要求models proof、早期fetch/parsefailure仍可發布、empty_paid/empty ladder邊界。Run `python3 -m unittest discover -s tests`，全套green才提交。
- [ ] **7. Commit.** Stage Task 3 file map列出的產品與pipeline／新fixture檔（fixturehelper也列明），`git diff --cached --check`，commit `fix: reconcile present missing-cost candidates without stale prices`。不得在此中途push main。

## Task 4: Visible Source Exits and Contract Documentation

**Files:** Modify `bridge/window_report.py:85-134,154-194`, `tests/test_window_report.py`, `chatgpt-instructions.md`, `docs/contracts/chat-ci.md`, `README.md`, `AGENTS.md`. Create acceptance ledger if未於執行起點建立。

**Interfaces:**
- Consumes: 既有calculation.caveats中由Task1生成的 `DISCLOSURE_PREFIX` 退出摘要；没有新result欄位。
- Produces: `_source_exits(calculation:dict) -> list[str]`，只filter prefix，不重新判retired、不抓來源、不排序候選。

- [ ] **1. Write placement and escaping red tests.**

```python
def test_source_exit_is_visible_before_ladder_and_escaped(self):
    calculation = deepcopy(self.payload)
    exit_line = DISCLOSURE_PREFIX + '<img src=x onerror=alert(1)>：當前 task cost 缺值，本次未參戰，未沿用舊價。'
    calculation['caveats'].append(exit_line)
    md, page = self.views(calculation)
    self.assertLess(md.index('本次來源退出'), md.index('## 已選好階梯'))
    self.assertLess(page.index('data-family="source-exits"'), page.index('data-family="ladder"'))
    self.assertNotIn('<img src=x', page)
    self.assertIn('&lt;img src=x', page)
    self.assertEqual(calculation['caveats'][-1], exit_line)
```

在既有 `test_window_report.py` TestCase 中沿用 `calculate_v2` 生成的 `self.payload`，不另mock selector；same JSON兩種退出皆被顯示，无exit时不產生空警告區，其他B／係數／版本caveat仍完整。測試import Task1的 `DISCLOSURE_PREFIX`；renderer從 `scripts.refresh_inventory` import同一常量。Run `python3 -m unittest discover -s tests -p 'test_window_report.py' -v`，預期摘要仍只在footer或没有summary section。
- [ ] **2. Implement projection only.**

```python
def _source_exits(calculation):
    return [line for line in calculation['caveats'] if line.startswith(DISCLOSURE_PREFIX)]
```

MD在anchors後、tables前加 `## 本次來源退出` 与 `_markdown`；HTML在cards後、sections前加 `section data-family="source-exits"`與 `_html` escaping。footer仍保留原caveats以維持完整上下文；不把source-only退出塞進candidate_statuses。Run report、HTML與全suitegreen。

在MD anchors loop後插入：

```python
exits = _source_exits(calculation)
if exits:
    lines.extend(['', '## 本次來源退出', ''])
    lines.extend('- ' + _markdown(line) for line in exits)
```

在HTML return前產生summary，在cards section後插入 `{exit_section}`：

```python
exits = _source_exits(calculation)
exit_section = ('<section class="panel" data-family="source-exits"><h2>本次來源退出</h2><ul>' +
                ''.join('<li>' + _html(line) + '</li>' for line in exits) + '</ul></section>') if exits else ''
```
- [ ] **3. Update docs and acceptance ledger precisely.** 契約新增新policy／proof／tracked語義與旧產品可信legacy辨識；Chat結報近結論顯示來源退出、不當free或永久退休、不手估cost。保留历史fresh失敗記錄，頂部新增「分支實作本地已驗、尚待正式發布／live驗收」狀態；未有雲端結果前不得寫live已成功。README入口分清固定9/26與newfresh；AGENTS保持当前狀態SSOT；不動bootstrap、不建立Notion同步。issue#2路由guard此task不偷偷實作或宣稱驗收。
- [ ] **4. Commit.** Stage本task具體文件，`git diff --cached --check`，commit `feat: disclose current source exclusions beside recommendations`。

## Task 5: Whole-Branch Verification, Integration and Live Acceptance

**Files:** acceptance ledger、README／AGENTS／契約生產狀態；不改算法或既有輸出。

**Interfaces:** Consumes 已測的producer／validator／runner／publisher／reports；produces 固定本地測試證據、review結果與（經批准發布後）new cloud request/run/publication/source/artifact/pointers關聯。

- [ ] **1. Fresh local verification and protected-file comparison.** 用 execution ledger 中起點SHA，不在中途重取HEAD冒充base。Run `python3 -m unittest discover -s tests`、`git diff --check`，再用下列命令驗保護檔diff必為空。記錄實際test數與exit，不沿用229或fixture-success作live證據。

```sh
execution_base=$(sed -n 's/^Execution base: \([0-9a-f]\{40\}\)$/\1/p' docs/superpowers/notes/2026-09-30-refresh-reconciliation-acceptance.md)
test "${#execution_base}" -eq 40
git diff --exit-code "$execution_base" -- runs scripts/compute_frontier.py scripts/ladder.py scripts/ladder_extra.py experiments tests/fixtures/refresh/failed-two-costs-flight.html tests/fixtures/refresh/leader.html tests/fixtures/refresh/grok.html tests/fixtures/refresh/muse.html tests/fixtures/refresh/meta.html tests/fixtures/refresh/models.html tests/fixtures/refresh/README.json
```
- [ ] **2. Verify real fixed historical recompute is unchanged.** 用既有runner測試／本地受控request以原9/26固定CSV、18/16、min0、無cap重算；不得手改原檔。核對155 statuses／154身份可用／19chain／10final、兩入口Astra xhigh／Luna low、不可用Contributor max excluded、source date仍9/26。newfresh的pool與final不套此名單。
- [ ] **3. Independent whole-branch review.** 按 selected subagent-driven skill先完成每task spec/quality review，再 request whole-branch review；review只讀所有diff與完整spec/plan，特别看可信context、legacy downgrade、null-cost no-substitution、tracked continuation、source-only摘要escape。修feedback先 receiving-code-review／TDD／再全驗，不把reviewer一句完成當證據。
- [ ] **4. Integration decision.** 使用 finishing-a-development-branch 呈現整合選項，按使用者選擇走PR／merge／發布。未獲具體發布授權前，不push main、不建立驗收request、不close issue；任何push不得force或刪既有分支。若選PR，cloud驗收保持待PR合併與發布，不能先宣稱修復已上線。
- [ ] **5. Live refresh after approved publication.** 先解析main固定新產品，驗Gitpolicy marker與發布SHA。驗收請求擬沿用9/30實際refresh情境：`gpt_factor=18,grok_factor=16,min_score=0,min_score_reason="同版本全候選情境比較",max_cost=null`；發布／驗收時確認沿用這組floor與理由，未確認不另造floor。

在任何request Git write前明示「operation=refresh，重新取得當次公開來源，不重用9/26快照」。建立UUIDv4唯一requestbranch/file、parent=newproduct、soleA requestpath、created_at有timezone，不改schema；查到run與attempt後固定publication讀回CSV原始bytes算SHA、raw／parsed／分類、v2result／報表／HTMLartifactbytes、pointer排序。對今天實際看到的已退休／缺價候選照實核對，不能硬要求來源仍恰好兩個缺口。

success時GPT-6.1五檔若當次仍完整可用，均在候選並有各自source row；final由算法選，不以五檔全留作成功門檻。若另有source/version/proof問題，保存精確faileddiagnostic、成功pointer不因失敗推進，不用fixture或舊成功補位。另跑新成功refresh的固定recompute验证完整證據鏈，不重新fetch來源。
- [ ] **6. Close out evidence and status.** 固定product／request／publication三SHA、runID/attempt、source日期／version、退出原因、test/review證據與artifacthash写ledger；更新README／AGENTS／契約為實際發布及cloud結果。OpenCode驗收、目標Chat讀新版及route實測、Projectsettings安裝各自回報；沿用已通過connector能力、不重問整包盤點。完成#1驗收後才按選定issue流程結案；#2須獨立route驗收，不能一併冒稱closed。

## Self-Review Coverage

- Spec §§1–3：Task1 strictstates與優先序、Task3 source／Contributor／版本 hard邊界。
- Spec §4：Task1公式／復活／退休消失、Task2精確mapproof、Task3固定前次與legacy。
- Spec §5：Task2decoder／validator、Task3可信Gitpolicy／handoff／publisher／workflow與新錯誤碼。
- Spec §6：Task3 paid/status/count與pointer、Task4近結論摘要、Task5historical／live／artifact。
- Spec §7：上述targetedmatrix與Task5完整測試／review／cloud，不以歷史或fixture冒充live。
- Spec §8：issue#2不混入#1schema／取數驗收；其bounded短設計另行確認。

- [x] 規格逐節覆蓋：八節皆有上方對應task；技術scope未擴大為新算法／schema／網站。
- [x] Placeholder scan：沒有待補欄位或未定helpers；執行起點由ledger實際寫入／讀取，不用佔位SHA。
- [x] Interface consistency：v2fixture從 `bridge.result` 生成；report測試沿現有 `self.payload`／`self.views`；新Git／CLI介面均有宣告及接線位置。
- [x] Review Focus：五項均已分配Task1–4測例，包括Decimal小差、legacy降級、固定前次與source-only escape。

使用者已對計畫及判定說明回覆「可以了」，依已選Subagent-driven逐項執行；進度以各task checkbox與驗收帳為準。實作批准不是正式發布授權。
