# Ladder（as-of run: `runs/2026-09-24-general-v5/candidates.csv`)
- min-score=0, max-cost=none, eps_score=2（規約預設；AA 當版 CI 未公布則沿用上一版）, eps_cp=5.0%（成本側容忍度，固定）
- 去重規則：0.5eps 連帶＋pinned（全表最高分行＋最高 CP 行自動 pinned，不參與被砍）
- privacy：純註記（2026-09-24 取消分桶；evidence_url + checked_date 見行，不分組不過濾）

## 階梯表：AA-Intelligence-Index @ AA-Intelligence-Index-v4.3 | basis=api (n=10)
| # | Score | Cost/task | CP | Identity | GRADE | 註記 |
|---|---|---|---|---|---|---|
| 1 | 57.6 | $5.9820 | 9.6 | Claude Opus 5.5 Adaptive Reasoning, Max Effort, Default Fallback AA-median Free | A | GRADE-A AA API實測 57.6 / $5.982; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=claude-opus-5-5; price_1m_in=4 price_1m_out=20 |
| 2 | 52.4 | $2.3088 | 22.7 | GPT-6 Astra xhigh AA-median Free | A | GRADE-A AA API實測 52.4 / $2.3088; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-astra-xhigh; price_1m_in=10 price_1m_out=50 |
| 3 | 50.9 | $1.7253 | 29.5 | GPT-6 Astra high AA-median Free | A | GRADE-A AA API實測 50.9 / $1.7253; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-astra-high; price_1m_in=10 price_1m_out=50 |
| 4 | 49.6 | $1.5406 | 32.2 | GPT-6 Astra medium AA-median Free | A | GRADE-A AA API實測 49.6 / $1.5406; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-astra-medium; price_1m_in=10 price_1m_out=50 |
| 5 | 47.5 | $1.0564 | 45.0 | GPT-6 Sol max AA-median Free | A | GRADE-A AA API實測 47.5 / $1.0564; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-sol; price_1m_in=2 price_1m_out=10 |
| 6 | 45.1 | $0.0726 | 621.2 | Muse Spark 1.3 xhigh Meta Contributor | B | GRADE-B DERIVED cost not AA-measured: 1.3678 (AA API Standard xhigh cost 2026-09-24) x blended ratio 0.0414/0.78 (Standard $1.25/$4.25 cached $0.15 vs Contributor $0.10/$0.20 cached $0.002 confirmed https://dev.meta.ai/docs/pricing-rate-limits 2026-09-24); assumes identical token usage across plans; same checkpoint as Standard; frontier row marked B |
| 7 | 33.9 | $0.0417 | 812.9 | GPT-6 Luna xhigh AA-median Free | A | GRADE-A AA API實測 33.9 / $0.0417; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-luna-xhigh; price_1m_in=0.1 price_1m_out=0.5 |
| 8 | 32.1 | $0.0286 | 1122.4 | GPT-6 Luna high AA-median Free | A | GRADE-A AA API實測 32.1 / $0.0286; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-luna-high; price_1m_in=0.1 price_1m_out=0.5 |
| 9 | 29.5 | $0.0173 | 1705.2 | GPT-6 Luna medium AA-median Free | A | GRADE-A AA API實測 29.5 / $0.0173; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-luna-medium; price_1m_in=0.1 price_1m_out=0.5 |
| 10 | 20.9 | $0.0045 | 4644.4 | GPT-6 Luna low AA-median Free | A | GRADE-A AA API實測 20.9 / $0.0045; envelope intelligence_index_version=v4.3; fetched 2026-09-24; provider AA-median (Free tier cross-provider median, no provider/plan split); slug=gpt-6-luna-low; price_1m_in=0.1 price_1m_out=0.5 |

### Cut 名單（3）
- GPT-6 Astra max AA-median Free (S=52.7, CP=16.2 | A) → 同帶贏家 GPT-6 Astra xhigh AA-median Free (S=52.4, CP=22.7 | A)
- GPT-6 Astra low AA-median Free (S=45.8, CP=56.0 | A) → 同帶贏家 Muse Spark 1.3 xhigh Meta Contributor (S=45.1, CP=621.2 | B)
- GPT-5.6 Luna low AA-median Free (S=21, CP=2142.9 | A) → 同帶贏家 GPT-6 Luna low AA-median Free (S=20.9, CP=4644.4 | A)

<details><summary>Excluded sample (23, top 5)</summary>

- Claude Fable 5.1 Adaptive Reasoning, Max Effort, Default Fallback AA-median Free (S=53.4, $7.6297): CP no new high (7.00 <= best 9.63 x 1.05)
- Muse Spark 1.3 max AA-median Free (S=48.1, $1.6049): CP no new high (29.97 <= best 32.20 x 1.05)
- Claude Fable 5.1 Adaptive Reasoning, Low Effort, Default Fallback AA-median Free (S=46.8, $2.3710): CP no new high (19.74 <= best 44.96 x 1.05)
- Muse Spark 1.3 xhigh AA-median Free (S=45.1, $1.3678): CP no new high (32.97 <= best 621.21 x 1.05)
- GLM-5.3 max AA-median Free (S=44.8, $2.0056): CP no new high (22.34 <= best 621.21 x 1.05)
</details>

## B-caveat（禁令 9）
- B 級行在表上：Muse Spark 1.3 xhigh Meta Contributor
- B 級行決定 cut：Muse Spark 1.3 xhigh Meta Contributor（推導價參戰，公式＋假設見該行註記）

## 配置驗證（config: `~/.config/opencode/opencode.json`）
- root `openai/gpt-6-astra` → OK（S=52.4 $2.3088 CP=22.7 GPT-6 Astra xhigh AA-median Free）
- general `meta/muse-spark-1.3-contributor#xhigh` → OK（S=45.1 $0.0726 CP=621.2 Muse Spark 1.3 xhigh Meta Contributor）
- explore `openai/gpt-6-luna#high` → OK（S=32.1 $0.0286 CP=1122.4 GPT-6 Luna high AA-median Free）

