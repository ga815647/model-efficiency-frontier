# Frontier — General / AA Intelligence Index v4.3 (2026-09-17) — v2: +Meta provider plans

- as-of date: 2026-09-17 (checked_date=2026-09-17)
- benchmark: General — Artificial Analysis Intelligence Index v4.3
- benchmark URL: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3
- eval page: https://artificialanalysis.ai/evaluations/artificial-analysis-intelligence-index
- benchmark composition (v4.3, 10 evals): AA-Briefcase, GDPval-AA v2, AutomationBench-AA, Terminal-Bench 4.0, SciCode, HLE, GDP.pdf, CritPt, AA-Omniscience, AA-LCR v1.1
- cost basis: api only (AA Cost per Intelligence Index Task; groups never mixed)
- min-score: 40; max-cost: none; eps: eps_score=2.0, eps_cp=5%
- privacy definition version: AGENTS.md 2026-09-17 binary (best-effort); buckets never merged; mode=all
- privacy evidence (new rows):
  - Muse Spark 1.3 Standard → private-safe: https://ai.developer.meta.com/docs/pricing-rate-limits/ ("Standard pricing; your prompts and completions are not used to train Meta models")
  - Muse Spark 1.3 Contributor → other: same URL ("Heavily discounted token pricing in exchange for permission to use your prompts and completions to train future Meta models") — explicit training clause, no inference needed
- v2 delta vs runs/2026-09-17-general-intelligence/ (frozen, untouched): +2 rows, same Model x Effort x Provider, different Pricing Plan (Standard vs Contributor) — §4 分行示範
- score/cost sources:
  - prior 13 rows: AA v4.3 article 2026-09-07 + eval comparison table (see v1 frontier.md)
  - Spark Standard (45, $1.37): AA model page live v4.3 https://artificialanalysis.ai/models/muse-spark-1-3-xhigh (2026-09-17)
  - Spark Contributor (45, $0.07): DERIVED, not AA-measured — 1.37 × blended unit-price ratio 0.0414/0.78 under AA 7:2:1 cache/input/output mix assumption; evidence grade B; replace when AA publishes contributor route
- v4.1.1 trap (deliberately excluded): Spark xhigh 61 / $0.55 belongs to Index v4.1.1 (Sep-02 article) — different task set, ban 1 forbids merging into this v4.3 run
- script: scripts/compute_frontier.py --min-score 40 --privacy-mode all
- input snapshot: runs/2026-09-17-general-v2/candidates.csv (frozen)

## 人工覆核
- other 桶：Contributor (45, CP 642.9) 起點；GLM-5.3-Flash (42, CP 168) 被淘汰 — 數學正確，但 Contributor cost 是推導值，若真實 token mix 偏離 7:2:1 假設則 CP 跟著動；另 Contributor 有 60 RPM 上限（Standard 3000），agentic 高併發場景吞吐受限，frontier 只比 $/task 不比吞吐，特此註記。
- private-safe 桶：維持 Astra 四階（xhigh→high→medium同層→low）；Spark Standard (45, $1.37, CP 32.8) 被 Astra low (CP 56.1) 壓制淘汰 — 合理，同桶內它沒有價格優勢。
- 同 checkpoint 跨桶分列（Standard進private-safe、Contributor進other）正是 §4 要的：用資料換低價必須分行，且兩桶永不混排。

---
--- script output below (verbatim) ---

# Frontier result (as-of run: `runs/2026-09-17-general-v2/candidates.csv`)
- min-score=40, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all
- Rule: buckets never merged; FREE rows never in numeric frontier.

## General @ AA-Intelligence-Index-v4.3 | basis=api | bucket=other (n=2)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 45 | Muse Spark 1.3 xhigh Meta Contributor | $0.07 | 642.9 | Meta | other | highest-capability start of this bucket |

<details><summary>Dominated / excluded sample (1, top 5)</summary>

- GLM-5.3-Flash Z.AI API Standard (S=42, $0.25): CP no new high (168.00 <= best 642.86 x 1.05)
</details>

## General @ AA-Intelligence-Index-v4.3 | basis=api | bucket=private-safe (n=13)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 53 | GPT-6 Astra xhigh OpenAI API Standard | $2.31 | 22.9 | OpenAI | private-safe | highest-capability start of this bucket |
| 51 | GPT-6 Astra high OpenAI API Standard | $1.72 | 29.7 | OpenAI | private-safe | CP new high +29.2%% at score step -2.00 |
| 50 | GPT-6 Astra medium OpenAI API Standard | $1.54 | 32.5 | OpenAI | private-safe | same-tier (gap 1.00 < 2.0) CP takeover +9.5%% |
| 46 | GPT-6 Astra low OpenAI API Standard | $0.82 | 56.1 | OpenAI | private-safe | CP new high +72.8%% at score step -5.00 |

<details><summary>Dominated / excluded sample (9, top 5)</summary>

- GPT-6 Astra max OpenAI API Standard (S=53, $3.26): CP no new high (16.26 <= best 22.94 x 1.05)
- Claude Fable 5.1 xhigh-fallback Anthropic API Standard (S=53, $5.98): CP no new high (8.86 <= best 22.94 x 1.05)
- Claude Fable 5.1 max-fallback Anthropic API Standard (S=53, $7.63): CP no new high (6.95 <= best 22.94 x 1.05)
- Claude Fable 5.1 high-fallback Anthropic API Standard (S=51, $3.91): CP no new high (13.04 <= best 29.65 x 1.05)
- Claude Fable 5.1 medium-fallback Anthropic API Standard (S=49, $2.98): CP no new high (16.44 <= best 32.47 x 1.05)
</details>

## FREE sidecar: none in this input.
