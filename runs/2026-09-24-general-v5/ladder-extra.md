# 番外篇 / 個人實測係數估算；Notion 主展示（非官方 AA 成本）
- 原因：ChatGPT 訂閱用好用滿，個人實測約 18.9 倍 API 用量；預設保守取整採 ×18（本次 ×18），並非實測 18，也非 AA 實測。
- 細節：factor=18（預設 ×18；原始實測約 18.9），prefix=GPT-；$20+$59 組合（預設合計 $79）；匹配前綴的行 cost_adj=cost_orig/18、CP_adj=CP_orig×18；N 用滿水位由使用者指定。
- CP_orig、CP_adj 由原始未四捨五入的 Score 與 Cost_orig 計算，表中數字僅供顯示時取整。
- 不進正式表：正式表 `runs/2026-09-24-general-v5/ladder.md` 保持原狀；此為獨立情境估算。
- 來源快照日期（checked_date）：2026-09-24；生成日期：2026-09-26；來源檔：`runs/2026-09-24-general-v5/candidates.csv`。來源日期不等於生成日期，未重新抓取 AA 或定價。
- benchmark 來源 URL：https://artificialanalysis.ai/api/v2/language/models/free
- min-score=0（floor 理由：同一來源快照全候選比較，沿用原版 floor=0；非新 AA 研究 run）；max-cost=none（以情境 cost_adj 比較）；eps_score=2（規約預設，AA CI 未公布沿用）；eps_cp=5%（固定成本側容忍度）。
- 其他定價／計算證據 URL：https://dev.meta.ai/docs/pricing-rate-limits
- privacy：純註記（2026-09-24 取消分桶；不過濾付費行）。GRADE A/B 為原價證據等級，×18 僅個人情境估算，不升格為 AA 實測或 GRADE-B。
- `AA-median Free` 是 AA API 資料的 provider/plan 標記（跨 provider median），不是零成本 API 或可免費取得相同服務的推論；只有明確 is_free=true/yes/1/y 的行不進數字運算。
- 算法按 Score 由高到低建立 CP_adj 新高與連帶去重；下表按 Score 由高到低展示（強→弱），CP_adj 為效率欄而非排序鍵。

## 階梯表：AA-Intelligence-Index @ AA-Intelligence-Index-v4.3 | basis=api (n=12；Score 降序)
| # | Score | Cost_orig | CP_orig | CP_adj | Identity | ×18? | GRADE | 註記 |
|---|---|---|---|---|---|---|---|---|
| 1 | 57.6 | $5.9820 | 9.63 | 9.63 | Claude Opus 5.5 Adaptive Reasoning, Max Effort, Default Fallback AA-median Free | — | A | GRADE-A AA API實測 57.6 / $5.982; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=claude-opus-5-5; price_1m_in=4 price_1m_out=20 |
| 2 | 52.4 | $2.3088 | 22.70 | 408.52 | GPT-6 Astra xhigh AA-median Free | ✓ | A | GRADE-A AA API實測 52.4 / $2.3088; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-astra-xhigh; price_1m_in=10 price_1m_out=50；情境：cost_adj=Cost_orig/18, CP_adj=CP_orig×18 |
| 3 | 50.9 | $1.7253 | 29.50 | 531.04 | GPT-6 Astra high AA-median Free | ✓ | A | GRADE-A AA API實測 50.9 / $1.7253; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-astra-high; price_1m_in=10 price_1m_out=50；情境：cost_adj=Cost_orig/18, CP_adj=CP_orig×18 |
| 4 | 49.6 | $1.5406 | 32.20 | 579.51 | GPT-6 Astra medium AA-median Free | ✓ | A | GRADE-A AA API實測 49.6 / $1.5406; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-astra-medium; price_1m_in=10 price_1m_out=50；情境：cost_adj=Cost_orig/18, CP_adj=CP_orig×18 |
| 5 | 47.5 | $1.0564 | 44.96 | 809.35 | GPT-6 Sol max AA-median Free | ✓ | A | GRADE-A AA API實測 47.5 / $1.0564; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-sol; price_1m_in=2 price_1m_out=10；情境：cost_adj=Cost_orig/18, CP_adj=CP_orig×18 |
| 6 | 45.8 | $0.8175 | 56.02 | 1008.44 | GPT-6 Astra low AA-median Free | ✓ | A | GRADE-A AA API實測 45.8 / $0.8175; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-astra-low; price_1m_in=10 price_1m_out=50；情境：cost_adj=Cost_orig/18, CP_adj=CP_orig×18 |
| 7 | 39.8 | $0.2482 | 160.35 | 2886.38 | GPT-6 Sol medium AA-median Free | ✓ | A | GRADE-A AA API實測 39.8 / $0.2482; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-sol-medium; price_1m_in=2 price_1m_out=10；情境：cost_adj=Cost_orig/18, CP_adj=CP_orig×18 |
| 8 | 37.3 | $0.0681 | 547.72 | 9859.03 | GPT-6 Luna max AA-median Free | ✓ | A | GRADE-A AA API實測 37.3 / $0.0681; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-luna; price_1m_in=0.1 price_1m_out=0.5；情境：cost_adj=Cost_orig/18, CP_adj=CP_orig×18 |
| 9 | 33.9 | $0.0417 | 812.95 | 14633.09 | GPT-6 Luna xhigh AA-median Free | ✓ | A | GRADE-A AA API實測 33.9 / $0.0417; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-luna-xhigh; price_1m_in=0.1 price_1m_out=0.5；情境：cost_adj=Cost_orig/18, CP_adj=CP_orig×18 |
| 10 | 32.1 | $0.0286 | 1122.38 | 20202.80 | GPT-6 Luna high AA-median Free | ✓ | A | GRADE-A AA API實測 32.1 / $0.0286; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-luna-high; price_1m_in=0.1 price_1m_out=0.5；情境：cost_adj=Cost_orig/18, CP_adj=CP_orig×18 |
| 11 | 29.5 | $0.0173 | 1705.20 | 30693.64 | GPT-6 Luna medium AA-median Free | ✓ | A | GRADE-A AA API實測 29.5 / $0.0173; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-luna-medium; price_1m_in=0.1 price_1m_out=0.5；情境：cost_adj=Cost_orig/18, CP_adj=CP_orig×18 |
| 12 | 20.9 | $0.0045 | 4644.44 | 83600.00 | GPT-6 Luna low AA-median Free | ✓ | A | GRADE-A AA API實測 20.9 / $0.0045; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-luna-low; price_1m_in=0.1 price_1m_out=0.5；情境：cost_adj=Cost_orig/18, CP_adj=CP_orig×18 |

### Cut 名單（2）
- GPT-6 Astra max AA-median Free（S=52.7, Cost_orig=$3.2575, CP_orig=16.18, CP_adj=291.20；GRADE A）→ 同帶贏家 GPT-6 Astra xhigh AA-median Free（S=52.4, Cost_orig=$2.3088, CP_orig=22.70, CP_adj=408.52；GRADE A）
- GPT-5.6 Luna low AA-median Free（S=21, Cost_orig=$0.0098, CP_orig=2142.86, CP_adj=38571.43；GRADE A）→ 同帶贏家 GPT-6 Luna low AA-median Free（S=20.9, Cost_orig=$0.0045, CP_orig=4644.44, CP_adj=83600.00；GRADE A）

<details><summary>Excluded sample (22, top 5)</summary>

- Claude Fable 5.1 Adaptive Reasoning, Max Effort, Default Fallback AA-median Free（S=53.4, Cost_orig=$7.6297, CP_orig=7.00, CP_adj=7.00；GRADE A）：CP_adj no new high (7.00 <= best 9.63 x 1.05)
- Muse Spark 1.3 max AA-median Free（S=48.1, Cost_orig=$1.6049, CP_orig=29.97, CP_adj=29.97；GRADE A）：CP_adj no new high (29.97 <= best 579.51 x 1.05)
- Claude Fable 5.1 Adaptive Reasoning, Low Effort, Default Fallback AA-median Free（S=46.8, Cost_orig=$2.3710, CP_orig=19.74, CP_adj=19.74；GRADE A）：CP_adj no new high (19.74 <= best 809.35 x 1.05)
- Muse Spark 1.3 xhigh Meta Contributor（S=45.1, Cost_orig=$0.0726, CP_orig=621.21, CP_adj=621.21；GRADE B）：CP_adj no new high (621.21 <= best 1008.44 x 1.05)
- Muse Spark 1.3 xhigh AA-median Free（S=45.1, Cost_orig=$1.3678, CP_orig=32.97, CP_adj=32.97；GRADE A）：CP_adj no new high (32.97 <= best 1008.44 x 1.05)
</details>

## Contributor 狀態（所有此組 Contributor，不受 excluded top 5 節錄影響）
- Muse Spark 1.3 xhigh Meta Contributor（S=45.1, Cost_orig=$0.0726, CP_orig=621.21, CP_adj=621.21；GRADE B）：excluded：CP_adj no new high (621.21 <= best 1008.44 x 1.05)；原價依據：GRADE-B DERIVED cost not AA-measured: 1.3678 (AA API Standard xhigh cost 2026-09-24) x blended ratio 0.0414/0.78 (Standard $1.25/$4.25 cached $0.15 vs Contributor $0.10/$0.20 cached $0.002 confirmed https://dev.meta.ai/docs/pricing-rate-limits 2026-09-24); assumes identical token usage across plans; same checkpoint as Standard; frontier row marked B

### B-caveat（原價證據等級，不是 ×18 的等級）
- GRADE-B 推導原價照常參戰，包括保留、決定 cut、或 CP_adj 新高而擋下其他行；其公式與假設見 notes。 個人 ×18 調整另行標示，不冒充 AA 實測。
- 此組 B 行：Muse Spark 1.3 xhigh Meta Contributor

## 檔位結論（僅非 Claude final）
- 攻堅：GPT-6 Astra xhigh AA-median Free（S=52.4, CP_adj=408.52）
- 平衡：GPT-6 Sol medium AA-median Free（S=39.8, CP_adj=2886.38）
- 省錢：GPT-6 Luna low AA-median Free（S=20.9, CP_adj=83600.00）

## 外部 API 試算（僅情境；不影響階梯）
- N 是每月 benchmark 等價任務量，不是一般聊天次數；每項 API 成本以省錢 pick 的 Cost_orig 而非 cost_adj 計。
- 訂閱組合 $20+$59（此處比較總額 $79）。已付訂閱的增量決策不同，不能無條件建議新購／續訂。
- GPT-6 Luna low AA-median Free：N 未定，只給公式不給結論：N × $0.0045 vs $79
