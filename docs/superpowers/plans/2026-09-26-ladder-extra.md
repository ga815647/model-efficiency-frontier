# Ladder-extra Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 生成 GPT- ×18（原始個人實測約 18.9，保守取整）情境番外篇，並替換現有 Notion 主展示，讓檔位選擇與 API 成本判斷同頁可見。

**Architecture:** 新增獨立 CLI，複製 ladder 顯示層去重函式，委派 frozen compute_frontier 計算。調整成本只存記憶體，原價與 CP_adj 分欄。本地結果驗證後整頁同步既有 Notion 頁。

**Tech Stack:** Python 3 stdlib、unittest、Notion MCP。

**Spec:** `docs/superpowers/specs/2026-09-26-ladder-extra-design.md`

**2026-09-26 USER AMENDMENT（覆蓋下文 CP_adj 展示排序舊決策）:** 用戶要求階梯按 Score 降序（強→弱），算法已按 score 由強至弱不改。表與 Notion 同步改為 Score 降序；CP_adj 仍為效率欄；×18 數學、Contributor 及三 pick 不變。原任務記錄保留作歷史。

## Global Constraints

- `factor=18`（用戶較保守修訂；原始個人實測約 18.9，非實測 18）、`prefix=GPT-`、`subscription-total=79`；min-score 必填，沿用來源 run 時須載明原門檻與理由。
- compute_frontier.py frozen；不 import recommend.py 或 ladder.py。
- 不改 candidates.csv 與本地 ladder.md；輸出 ladder-extra.md。
- 各 benchmark/version/basis 獨立計算，free 不入數學；Claude 留比較表但不推薦。
- Notion 頁 `3e539f3f-a67c-810a-9eca-f2de2c0fe1a5` 替換為番外篇並改標題。
- CP_adj 不冒充 AA 實測 CP；B 級仍標 B。
- 現工作區非 git repo，不執行 commit。

## Review Focus

- NaN/Infinity、非正 factor/cost：CLI exit 2，原檔不受損。
- 無付費行或門檻以上無行：明示空表，無虛構 pick。
- 多 benchmark 組：各自產表及 picks，不跨組挑 CP 峰值。
- monthly-tasks 缺值或 0：分別公式模式或零 API 支出，不能把缺值當 0。
- 展示次序與計算次序：兩者均按 Score 降序（同分表格按 adjusted cost 升序）；CP_adj 不作展示排序鍵，平衡位置依非 Claude 能力階梯計算。舊 CP 展示排序見下方歷史任務記錄。

---

### Task 1: 情境計算與輸入驗證

**Files:** Create `scripts/ladder_extra.py`, `tests/test_ladder_extra.py`。

**Interfaces:** `adjust_rows(rows, factor=18, prefix="GPT-") -> list[dict]`，回傳獨立副本含 `_score`, `_cost`, `_cost_orig`, `_cp_orig`；`dedup_bands(rows, eps_score) -> (final, cuts)` 複製現有實作。

- [x] 建立測試，先確認 import failure：

```python
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from ladder_extra import adjust_rows

class AdjustmentTests(unittest.TestCase):
    def test_adjustment_keeps_original_and_other_models(self):
        rows = [dict(identity='GPT-X', score='40', cost_per_task='2'),
                dict(identity='Other', score='40', cost_per_task='2')]
        got = adjust_rows(rows)
        self.assertAlmostEqual(got[0]['_cost'], 2 / 18)
        self.assertEqual(got[1]['_cost'], 2)
        self.assertEqual(got[0]['_cost_orig'], 2)
        self.assertEqual(rows[0]['cost_per_task'], '2')

    def test_nonfinite_factor_rejected(self):
        for factor in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                adjust_rows([], factor)
```

- [x] Run `python3 -m unittest discover -s tests -p test_ladder_extra.py -v`，確認失敗來自尚未實作。
- [x] 實作核心轉換，free 分流由 cf.is_free_row 完成，paid 的非有限 score/cost 與 cost<=0 拋 ValueError：

```python
def adjust_rows(rows, factor=18, prefix='GPT-'):
    if not math.isfinite(factor) or factor <= 0:
        raise ValueError('factor must be finite and positive')
    result = []
    for source in rows:
        if cf.is_free_row(source):
            continue
        r = dict(source)
        s, c = float(r['score']), float(r['cost_per_task'])
        if not math.isfinite(s) or not math.isfinite(c) or c <= 0:
            raise ValueError('invalid paid score/cost')
        r.update(_score=s, _cost_orig=c, _cp_orig=s/c,
                 _cost=c/factor if r['identity'].startswith(prefix) else c)
        result.append(r)
    return result
```

- [x] 複製 `ladder.py` 的 keep_key/dedup_bands/group_rows/grade_of 與 Claude family 檢查；依 spec CLI 解析參數並驗證 finite 值；用 `cf.compute_one_group` 跑每組。
- [x] 同一測試命令確認 PASS；追加 cost NaN/Infinity/0、free 分流、多組隔離案例。

### Task 2: 呈現與決策

**Files:** Modify `scripts/ladder_extra.py`, `tests/test_ladder_extra.py`。

**Interfaces:** `api_comparison(cost_orig, monthly_tasks, subscription_total) -> str`；`main()` 為 CLI entry。render 接收每組 final/cuts/excluded 與 CLI args。

- [x] 先加失敗測試：

```python
class DecisionTests(unittest.TestCase):
    def test_missing_usage_is_not_zero(self):
        from ladder_extra import api_comparison
        self.assertIn('N 未定', api_comparison(2, None, 79))
        self.assertIn('開外部API', api_comparison(2, 0, 79))
        self.assertIn('續訂閱', api_comparison(2, 40, 79))
```

- [x] 執行專項 unittest 確認失敗，實作：

```python
def api_comparison(cost_orig, monthly_tasks, subscription_total):
    formula = f'N × ${cost_orig:g} vs ${subscription_total:g}'
    if monthly_tasks is None:
        return f'N 未定，只給公式不給結論：{formula}'
    monthly_api = monthly_tasks * cost_orig
    choice = '開外部API' if monthly_api < subscription_total else '續訂閱'
    return f'{choice}（此用量假設下）：{monthly_tasks:g} × ${cost_orig:g} = ${monthly_api:g} vs ${subscription_total:g}'
```

- [x] render 標題含原始個人實測約 18.9 保守取整、GPT- ×18、$20+$59、日期（不可稱實測 18）；header 含 benchmark URL、來源日期、floor 理由、eps 與 privacy 版本；原價、CP_orig、CP_adj、GRADE 分欄。
- [x] 非 Claude final 以 score 降序取攻堅、索引 len//2 取平衡、最高 CP_adj 取省錢；空集合顯示從缺。歷史實作表按 `sorted(final, key=lambda r: (-r['_cp'], -r['_score'], r['_cost']))` 呈現（已由上方 USER AMENDMENT 覆蓋，現在按 Score 降序），附 cuts、excluded 前五、B caveat。外部 API 節明示 N 指 benchmark 等價任務量，並非一般聊天次數。
- [x] CLI 拒寫任何 basename 為 ladder.md、與 input 同路徑或同檔 inode 的 output；捕捉 ValueError/OSError，stderr 說明、exit 2。
- [x] 增加 subprocess 臨時 CSV 測試：空表、兩 benchmark、缺 monthly-tasks、CLI 非有限參數、原檔 hash 不變、標題包含來源、CP_adj 降序、no-Claude picks。Run 專項 unittest 至 PASS。

### Task 3: 產出與同步

**Files:** Create `runs/2026-09-24-general-v5/ladder-extra.md`；更新本 plan checkboxes。

**Interfaces:** Task 2 CLI；Notion 現有 page replace_content/update_properties。

- [x] 讀來源 ladder.md 取得已使用 min-score 與理由；將其作為此同快照情境重算的 CLI 參數，不自行創造新門檻。
- [x] 執行完整 `python3 -m unittest discover -s tests -v`；以 hashlib 記錄 frozen 腳本及原 candidates/ladder，產出後比對未變。
- [x] 使用 Task 2 CLI 產 ladder-extra.md，factor 18，prefix GPT-，subscription-total 79，未提供 N 保持公式模式。
- [x] 逐項 eyeball 原价與 CP_adj 欄、表次序、檔位、B 註記、空 N 語義。
- [x] discover Notion fetch/update 工具，先讀既有頁；整頁 replace_content 成番外篇精簡版並 update_properties 改標題，移除原版展示。
- [x] fetch 回讀驗證頁標題、保守 ×18 公式（原始個人實測約 18.9）、三 pick 與本地一致；回覆實際結果及 Notion 連結。

## Self-review

- 規格主要需求已覆蓋三任務；最新 Notion 指令已覆蓋舊隔離限制。
- 舊解讀（已由 USER AMENDMENT 覆蓋）：新 CP 排序指 CP_adj 降序展示；現用戶已明確改為 Score 降序，frozen 演算仍按能力降序建階梯。
- 不假定每月任務數；不以 AA 任務成本聲稱真實聊天月帳單。
