# Ladder 重構 Design Spec (2026-09-24)

> 狀態：design 已在 chat 逐段 present，用戶回覆「好」批准（2026-09-24）。
> 待用戶 review 本檔 → 然後走 writing-plans 產 implementation plan（執行方式已定：subagent-driven）。

## 0. 決策 log（用戶確認，不可擅改）

- 2026-09-24：OMO 完全脫鉤；專案唯一輸出＝階梯表＋general／explore 選型驗證。
- 階梯算法：top-down CP-new-high（`compute_frontier.compute_one_group`，frozen）→ 0.5eps 連帶去重 → v5 實測 10 階。
- Contributor（GRADE-B 推導價）參戰當門神，行標 `B`（政策 B 維持）。
- Claude 行留表作比較，永不推薦（禁令 14 維持）。
- 回歸（score~ln(cost)，剔 Contributor，v5 R²=0.984）只當手動診斷寫進 run 註記，不進腳本。
- Astra max（52.7，gap 0.3 貴 41%）確認不要；Luna max（37.3）被 Contributor 門神擋在門外，維持不特赦。
- 去重規則定案：連帶定義 gap<0.5eps，帶內留 CP 高者（2 行帶直接比；3+ 行帶從中間迭代砍到剩頭尾）。

## 1. Goal

把本專案重構成 OMO-free 的效率階梯專案：同 benchmark＋版本內，從最強往下排、只留 CP 創新高的階梯表，經 0.5eps 連帶去重後輸出，並驗證 `opencode.json` 的三個模型配置是否仍在表上（不在→警告）。

## 2. Architecture

- `scripts/compute_frontier.py`：**frozen**，階梯數學唯一實現，不動一字。
- `scripts/recommend.py`：**RETIRED**（檔案保留，永不再調用；新腳本禁止 import 它）。
- `scripts/ladder.py`（新增，約 120 行，顯示層）：load rows → `compute_one_group` → `dedup_bands` → match config → render `ladder.md`。
- `tests/test_ladder.py`（新增，stdlib unittest）。
- 新 run 只寫 `runs/<run>/ladder.md`；`recommend.md`／`frontier.md` 不再產出（舊 runs 歸檔不動）。
- `.omo/` 整目錄刪除。

Data flow：`candidates.csv` → ladder.py（math 委派 compute_frontier；去重＋驗證自含）→ `ladder.md`。另讀全域 `opencode.json`（唯讀，只做驗證，不寫回）。

CLI：`python3 scripts/ladder.py --input <candidates> --min-score <F> [--max-cost <X>] [--eps-score 2.0] [--eps-cp 0.05] [--config ~/.config/opencode/opencode.json] [--output <ladder.md>]`。`--min-score` 必填（禁令 6；v5 runs 傳 0）。錯誤（缺欄、非數值、cost<=0 非 free）exit 2，與現腳本一致；驗證警告不影響 exit code。

## 3. 去重算法（exact，deterministic）

輸入：kept list（score 降序；每行已有 `_score`、`_cost`、`_cp`），`eps_score`。

1. 連帶：相鄰 `gap = 上一行_score − 下一行_score < 0.5 × eps_score` 首尾相連成帶；否則斷帶。
2. pinned：全表最高分行＋全表最高 CP 行，按 identity 自動 pinned，不參與被砍（v5 即 Opus max 與 Luna low）。
3. 1 行帶：保送。
4. 2 行帶：留 keep-key 大者。keep-key＝（CP 高→分數高→便宜），即按 `(cp desc, score desc, cost asc)` 排序取首。被砍者記 cut 名單（含同帶贏家 identity）。
5. 3+ 行帶：`while len > 2`：`mid = len // 2`，pair＝`(w[mid-1], w[mid])`，drop＝pair 內 keep-key 小者；若 drop 被 pinned，改 drop 另一位；若兩位皆 pinned，break（全留）。被砍者記 cut 名單。
6. 輸出按 score 降序。

B 級行照常參戰（含設 best、含擋人），輸出標 `B`；單獨決定生死時輸出加 caveat（禁令 9 維持）。

## 4. 配置驗證（exact）

- 讀 JSON：root `model`＋`agents.general.model`＋`agents.explore.model`；`small_model` 跳過（utility 不驗）。缺檔→stderr 警告＋跳過本節，exit 0。
- ref 解析：`provider/model#variant` → tokens＝`norm(model part)` 分詞＋variant 分詞（variant `none` 映射為 `non reasoning`；無 variant 則不加）。ordered-token-subsequence 匹配＋exact-prefix 優先（語義 copy 自退役 `recommend.py` 的 `norm`／`match_query`／`find_best`，**copy 程式碼，不 import**）。
- 匹配對象＝最終階梯表（去重後），best＝最高分（tie：便宜）。
  - 命中→`OK（S=.. $.. CP=..）`。
  - 命中被 cut 行→`⚠ 被帶內去重淘汰（同帶贏家 S=.. CP=.. identity）`。
  - 只命中 excluded／無命中→`⚠ 不在表上`＋建議全表 CP 峰值行。
  - 命中 Claude-family→照報 presence＋`⚠ Claude-family 永不推薦（禁令 14）`。
- 建議只有以上兩條 deterministic 規則，不做建議引擎（A- 瘦身決議）。

## 5. ladder.md 格式

頂部 header：`as-of date / benchmark name+version+URL / cost basis / 去重規則（0.5eps 連帶＋pinned）/ eps 值+來源 / privacy 註記版本 / B-caveat（如有）/ 回歸註記（手動，R² 備查）`。正文：階梯表（rank／score／cost／CP／identity／GRADE／註記）＋cut 名單（含理由＋同帶贏家）＋配置驗證節＋dominated sample（沿用 compute_frontier excluded 前 5）。

## 6. OMO 脫鉤清單

- `rm -rf .omo/`。
- AGENTS.md：§1「角色分組與 official-chain」「floor 規則 official-chain 版」「鏈外特例規則」內 chain 相關句、「兩階段路線」Phase 2 v1 `recommend.py` 句、「核心輸出 recommend-only」句、「計算交給腳本」取代政策句；§3 step 4 跑腳本句；§5 `recommend.py`／`recommend.md` 條目；§6 floor 預設值內 official-chain 引用——全部劃線作廢（歷史保留不刪），並新增 dated ladder 政策條（本 spec §1–§5 要點＋`ladder.py` 唯一輸出＋去重規則＋驗證規則）。
- 舊 runs、`fetch_aa.py`、candidates schema、cost basis／GRADE／禁令 14 不動。`/tmp/omo-picks.md`、`/tmp/chain-sweep.md`、HEAD chain 引文不再是證據（無需動作，tmp  ephemeral）。

## 7. Testing

`tests/test_ladder.py`（stdlib unittest；`python3 -m unittest discover -s tests` 全綠）：

1. v5 integration：讀 `runs/2026-09-24-general-v5/candidates.csv`，斷言最終 10 個 identity 全等（順序 score 降序，見附錄 A）＋cut 3 行全等（Astra max／Astra low／5.6 Luna low＋各自贏家）。
2. 連帶邊界：合成 3 行（gaps 0.9／1.0，eps=2.0）→ 0.9 連帶、1.0 斷帶（嚴格 `<`）。
3. 3+ 行帶：合成 4 行連帶，斷言從中間砍到剩頭尾＋順序。
4. pinned 守衛：合成 2 行帶（CP 低者 pinned），斷言留 pinned 方。
5. 配置驗證：當前 `opencode.json` 三 ref（以測試內嵌 JSON 副本為準，不讀真檔）→ root 命中 Astra xhigh OK、general 命中 Contributor OK、explore 命中 Luna high OK；未知 slug → 不在表上＋CP 峰值建議。

## 8. Non-goals

- 不碰 `fetch_aa.py`、candidates schema、GRADE 判定、cost basis 分組、禁令 14。
- 回歸不進腳本；`frontier.md` 不恢復；不寫建議引擎；不動舊 runs。

## 附錄 A：v5 frozen 期望（測試 oracle，2026-09-24 實測 verbatim）

最終 10 階：57.6 Opus 5.5 max（$5.9820／CP 9.6／A）→ 52.4 Astra xhigh（$2.3088／22.7）→ 50.9 Astra high（$1.7253／29.5）→ 49.6 Astra medium（$1.5406／32.2）→ 47.5 Sol max（$1.0564／45.0）→ 45.1 Spark xhigh Contributor（$0.0726／621.2／**B**）→ 33.9 Luna xhigh（$0.0417／812.9）→ 32.1 Luna high（$0.0286／1122.4）→ 29.5 Luna medium（$0.0173／1705.2）→ 20.9 Luna low（$0.0045／4644.4）。Cut：Astra max 52.7（輸 xhigh，同帶 gap 0.30）／Astra low 45.8（輸 Contributor，同帶 gap 0.70）／5.6 Luna low 21.0（輸 Luna low，同帶 gap 0.10）。連帶（gap<1.0）：[57.6]［52.7,52.4]［50.9]［49.6]［47.5]［45.8,45.1]［33.9]［32.1]［29.5]［21,20.9]。驗證：三配置全 OK。回歸註記：剔 Contributor 後 12 階 A 行 score＝4.96×ln(cost)+47.85，R²=0.984；Contributor 殘差 +10.26（離群值，參戰維持政策 B）。
