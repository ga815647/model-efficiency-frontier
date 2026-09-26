# Ladder（as-of run: `/tmp/gemini-candidates.csv`)
- min-score=0, max-cost=none, eps_score=2（規約預設；AA 當版 CI 未公布則沿用上一版）, eps_cp=5.0%（成本側容忍度，固定）
- 去重規則：0.5eps 連帶＋pinned（全表最高分行＋最高 CP 行自動 pinned，不參與被砍）
- privacy：純註記（2026-09-24 取消分桶；evidence_url + checked_date 見行，不分組不過濾）

## 階梯表：AA-Intelligence-Index @ AA-Intelligence-Index-v4.3 | basis=api (n=4)
| # | Score | Cost/task | CP | Identity | GRADE | 註記 |
|---|---|---|---|---|---|---|
| 1 | 40.9 | $1.2428 | 32.9 | Gemini 3.8 Flash high AA-median Free | A | GRADE-A AA API實測 40.9 / $1.2428; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gemini-3-8-flash; price_1m_in=0.75 price_1m_out=3.75 |
| 2 | 39.8 | $0.9310 | 42.7 | Gemini 3.8 Flash medium AA-median Free | A | GRADE-A AA API實測 39.8 / $0.931; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gemini-3-8-flash-medium; price_1m_in=0.75 price_1m_out=3.75 |
| 3 | 22.2 | $0.1235 | 179.8 | Gemini 3.5 Flash-Lite Gemini 3.5 Flash-Lite AA-median Free | A | GRADE-A AA API實測 22.2 / $0.1235; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gemini-3-5-flash-lite; price_1m_in=0.3 price_1m_out=2.5 |
| 4 | 15.6 | $0.0394 | 395.9 | Gemini 3.1 Flash-Lite Gemini 3.1 Flash-Lite AA-median Free | A | GRADE-A AA API實測 15.6 / $0.0394; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gemini-3-1-flash-lite-preview; price_1m_in=0.25 price_1m_out=1.5 |

<details><summary>Excluded sample (5, top 5)</summary>

- Gemini 3.7 Flash high AA-median Free (S=39.1, $0.9253): CP no new high (42.26 <= best 42.75 x 1.05)
- Gemini 3.6 Flash high AA-median Free (S=34, $0.9288): CP no new high (36.61 <= best 42.75 x 1.05)
- Gemini 3.5 Flash high AA-median Free (S=32.6, $1.5625): CP no new high (20.86 <= best 42.75 x 1.05)
- Gemini 3.1 Pro Preview Gemini 3.1 Pro Preview AA-median Free (S=29.7, $0.6747): CP no new high (44.02 <= best 42.75 x 1.05)
- Gemini 2.5 Pro Gemini 2.5 Pro AA-median Free (S=16.1, $0.2317): CP no new high (69.49 <= best 179.76 x 1.05)
</details>

## 配置驗證（config: `~/.config/opencode/opencode.json`）
- root `openai/gpt-6-astra` → ⚠ 不在表上，建議 CP 峰值 Gemini 3.1 Flash-Lite Gemini 3.1 Flash-Lite AA-median Free（S=15.6 $0.0394 CP=395.9）
- general `meta/muse-spark-1.3-contributor#xhigh` → ⚠ 不在表上，建議 CP 峰值 Gemini 3.1 Flash-Lite Gemini 3.1 Flash-Lite AA-median Free（S=15.6 $0.0394 CP=395.9）
- explore `openai/gpt-6-luna#low` → ⚠ 不在表上，建議 CP 峰值 Gemini 3.1 Flash-Lite Gemini 3.1 Flash-Lite AA-median Free（S=15.6 $0.0394 CP=395.9）

