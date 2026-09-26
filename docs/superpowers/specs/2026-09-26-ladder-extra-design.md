# Ladder-extra 番外篇 Design Spec (2026-09-26)

> 狀態：design 已在 chat 逐段 present，用戶回覆「可」批准（2026-09-26）。
> 2026-09-26 用戶修訂：Notion 只展示番外篇，原版退出展示；GPT 不再霸榜時再回看原版。
> 定位：番外篇個人估算；本地 `ladder-extra.md` 為番外篇來源，現有 Notion 頁改以番外篇為主。

## 0. 決策 log（用戶確認，不可擅改）

- 2026-09-26 最新展示決策覆蓋先前 Notion 隔離限制：現有 Notion 頁整頁替換為番外篇並改標題，不另建頁、不附原版表；本地原版留存供日後回看。

- 2026-09-26 最新係數決策覆蓋以下原 18.9 計算係數：用戶要求「改18.9變成18好了 比較保守」。個人原始實測約 18.9 倍；**現在計算採保守 18 倍**，不能表述為實測 18 或 AA 實測。所有後續公式、預設、表頭及 Notion 都用 ×18；來源註記仍保留約 18.9。
- 2026-09-26 最新排序修訂：「階梯應該是 分數降序才對 演算法也是先從強的找 比較合邏輯」。覆蓋下方舊 CP_adj 展示排序決策：算法原本已按 score 降序，不改 frozen 數學；本地與 Notion 的 12 行表格改按 Score 降序（強→弱），CP_adj 僅為效率欄。原 18 倍調整、Contributor 參戰、三項非 Claude picks 不變。

- 2026-09-26：開番外篇 `ladder-extra`，不動正式表。`GPT-` 全家 `CP×18`（保守取整；選項 A：cost 顯示原價，加 `CP_adj` 欄 + 備註原因）。
- 範圍修訂：全進重比（不只 GPT- 行），`GPT-` 行以 `cost/18` 跑 frozen 數學，非 `GPT-` 行成本不動，一起重排階梯+去重。
- 排序用新 CP（歷史決策，展示排序已由上方最新排序修訂覆蓋）：frozen 數學仍依 score 降序建階梯，舊版展示表依 CP_adj 降序；渲染 cost 寫回原價。
- 2026-09-26 執行確認：GPT ×18 + Contributor + 其他付費候選全部進入重算；Contributor 不預先排除，是否留下由相同算法決定，需明示其結果與原因。
- 標題寫名原因和細節：頂部強制四行（番外篇/非官方/個人估算 + 原因 + 細節 + 不進正式表）。
- 前綴定義：`GPT-`（`runs/2026-09-24-general-v5/candidates.csv:2-21` 約 20 行，Astra/Sol/Luna/Terra）。
- 檔位 + 外部 API 一次呈現：同頁給攻堅/省錢/平衡三結論 + break-even 試算（N 由用戶填）。

## 1. Goal

從同一 `candidates.csv` 產番外篇階梯 `ladder-extra.md`：`GPT-` 行以保守 18x 用量假設（個人原始實測：ChatGPT 訂閱用好用滿 ≈ 18.9 倍 API 用量；採 18 保守取整，$20+$59 組合）重算 CP 並全表重比，結果按分數降序展示，一次回答「用哪個檔位」+「該不該開外部 API」。全程標個人估算，不污染正式數學。

## 2. Architecture

- `scripts/compute_frontier.py`：**frozen**，不動一字（`compute_one_group` 唯一數學實現）。
- `scripts/recommend.py`：**RETIRED**，新腳本禁止 import。
- `scripts/ladder_extra.py`（新增，fork `ladder.py` 顯示層）：load rows → GPT- 行 `cost_adj=cost/18` → `compute_one_group` → `dedup_bands`（copy 自 `ladder.py:34-78`，不 import ladder 以免耦合正式表）→ render `ladder-extra.md`。
- 輸出：`runs/<run>/ladder-extra.md`；Notion 現有頁同步此番外篇，本地 `ladder.md` 留存供日後回看。
- `tests/test_ladder_extra.py`（新增，stdlib unittest）。

Data flow：`candidates.csv` → ladder_extra.py（math 委派 compute_frontier；adjusted cost 只在記憶體內）→ `ladder-extra.md`。

CLI：`python3 scripts/ladder_extra.py --input <candidates> --output <ladder-extra.md> --factor 18 --prefix GPT- --min-score <F> [--max-cost <X>] [--eps-score 2.0] [--eps-cp 0.05] [--monthly-tasks <N>] [--subscription-total 79]`。`--min-score` 必填（禁令 6 沿用）。`--factor` 預設 18（須 >0）。`--output` 若指向 `ladder.md` 直接 exit 2 拒寫。錯誤（缺欄、非數值、cost<=0 非 free、factor<=0）exit 2。

## 3. 數學與去重（exact）

1. 解析：同 `ladder.py:277-290`（score/cost 浮點化，cost<=0 非 free 即錯）。
2. 調整：`identity.startswith(prefix)` 行 `cost_adj = cost / factor`，其餘 `cost_adj = cost`；保留 `cost_orig` 供顯示，`_cost = cost_adj` 供數學，`_score` 不變。
3. 分組：同正式表按 `(benchmark, benchmark_version, cost_basis)` 分組（`ladder.py:219-224` 語義），adjusted 仍在原 basis 組內比（番外篇不另開 basis，靠標題警告區隔）。
4. 階梯：`compute_one_group(groups[key], min-score, max-cost, eps-score, eps-cp)`。
5. 去重：`dedup_bands` 基於 `ladder.py:34-78`（0.5eps 連帶 + pinned 最高分行/最高 CP_adj 行）。番外篇修正原 helper 的雙 pinned 特例：2 行帶若兩行分別為最高分與最高 CP_adj，兩行都保留，不因 copy 原 bug 砍掉最高分；原版檔案不改。
6. 顯示：`CP_orig = score / cost_orig`，`CP_adj = score / cost_adj`（= GPT- 行 `CP_orig×factor`，非 GPT- 行兩者相等）；kept+dedup 完成後依 Score 降序展示（同分以 adjusted cost 升序）；平衡 pick 依非 Claude score 降序的能力階梯取中間列。

## 4. ladder-extra.md 格式

頂部強制 header（缺一即視為錯誤輸出）：
- `番外篇 / 個人實測係數估算；Notion 主展示`
- 原因：ChatGPT 訂閱用好用滿個人實測 ≈ 18.9 倍 API 用量，保守取整以 18 倍計算（非 AA 實測；不是實測 18）
- 細節：`factor=18（原始實測約 18.9，保守取整）, prefix=GPT-, $20+$59 組合、用滿水位 N 假設、日期 2026-09-26、CP_adj≠score/cost_orig`
- `不進正式表` + 正式表路徑指回 `ladder.md`

正文：
- 階梯表欄位：`| # | Score | Cost_orig | CP_orig | CP_adj | Identity | ×18? | 註記 |`（GPT- 行 `×18?` 欄打勾 + notes 追記公式）。
- cut 名單 + excluded sample（沿用邏輯，前 5）。
- 檔位結論三行：攻堅=最高分行、省錢=最高 CP_adj 行、平衡=中間階梯行（附 identity + S/CP_adj）。
- 外部 API break-even（exact，不進階梯數學）：取省錢 pick 行的 `cost_orig` 為 API 單價，`monthly_api = N × cost_orig`，`N = --monthly-tasks`（未傳則寫 `N 未定，只給公式不給結論`）；`subscription_total = --subscription-total`（預設 79，即 $20+$59）。`monthly_api < subscription_total` 寫 `開外部API`，否則寫 `續訂閱`，附公式全式。

## 5. Guardrails（不可妥協）

- `CP_adj` 永不寫成 `CP`；欄名、結論句必須帶 `adj` 或 `×18` 標記（禁令 9 類推：推導值不當實測呈現）。
- 不覆寫本地 `ladder.md`；Notion page_id `3e539f3f-a67c-810a-9eca-f2de2c0fe1a5` 整頁替換番外篇並更新標題，標明保守 ×18 的來源與公式，原版表退出展示。
- `compute_frontier.py` frozen、`recommend.py` retired 兩條紅線沿用。
- GRADE 欄沿用 `grade_of`（A/B/未知），番外篇不新設 GRADE，18x 情境以 `×18?` 欄 + 標題聲明承載（即個人估算，非 GRADE-B）。

## 6. 測試

- `test_factor_math`：v5 `candidates.csv` 上 GPT- 行 `CP_adj≈CP_orig×18`（容差 1e-6），非 GPT- 行兩者相等。
- `test_title_guards`：輸出含四行 header 關鍵字（番外篇/原因/細節/不進正式表），缺一即 fail。
- `test_no_clobber`：`--output` 指 `ladder.md` 時 exit 2 且不寫檔；正常跑完 `ladder.md` mtime 不變。
- `test_sort_uses_adj`（舊名語義已覆蓋）：驗證全候選以 adjusted cost 跑 frozen 算法，但展示 Score 降序、CP_adj 數值仍由調整後成本計；具體 fixture 驗證 Contributor 參戰但可被 GPT 淘汰，不能只用與原表順序不同當數學正確證據。
