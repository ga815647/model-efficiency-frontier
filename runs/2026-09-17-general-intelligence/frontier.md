# Frontier — General / AA Intelligence Index v4.3 (2026-09-17)

- as-of date: 2026-09-17 (prices/scores snapshot date; checked_date=2026-09-17)
- benchmark: General — Artificial Analysis Intelligence Index v4.3
- benchmark URL: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3
- eval page: https://artificialanalysis.ai/evaluations/artificial-analysis-intelligence-index
- benchmark composition (v4.3, 10 evals): AA-Briefcase, GDPval-AA v2, AutomationBench-AA, Terminal-Bench 4.0, SciCode, Humanity's Last Exam, GDP.pdf, CritPt, AA-Omniscience, AA-LCR v1.1
- category weights: Agents 30% / Coding 20% / General 30% / Scientific Reasoning 20%
- cost basis: api only (AA Cost per Intelligence Index Task = weighted-average USD per task from input/cache/reasoning/answer token prices x tokens, weighted by index weights, divided by task count; script groups by cost_basis, never mixed)
- min-score (minimum_intelligence, required): 40
- max-cost: none
- eps: eps_score=2.0, eps_cp=5%
- privacy definition version: AGENTS.md 2026-09-17 simplified binary — private-safe (best-effort) = official statement saying inputs/outputs not used for training by default; other = everything else (no inference from open-weight per ban 3, retention!=no-training per ban 4); buckets computed separately, never merged; mode=all = two tables
- privacy evidence:
  - OpenAI API rows: https://developers.openai.com/api/docs/guides/your-data ("data sent to the OpenAI API is not used to train or improve OpenAI models unless you explicitly opt in") + https://openai.com/business-data/
  - Anthropic API rows: https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training ("By default, we will not use your inputs or outputs from our commercial products to train our models")
  - GLM-5.3-Flash (Z.AI): other — open-weight, no no-training claim inferred (ban 3); score/cost source = AA eval page
- input snapshot: runs/2026-09-17-general-intelligence/candidates.csv (frozen, do not edit after run)
- script: scripts/compute_frontier.py (sole legal implementation), run: --min-score 40 --privacy-mode all

## 人工覆核 (dominated sample review)
- GPT-6 Astra max ($3.26 @53) 被同分 xhigh ($2.31 @53) 淘汰：合理，同 capability 取便宜者。
- Claude Fable 5.1 max/xhigh (@53, $7.63/$5.98) 被淘汰：合理，同分但 2-3x 貴，CP 無新高。
- Claude high (@51, $3.91) vs Astra high (@51, $1.72)：合理，同分貴 2.27x。
- Claude medium (@49, $2.98, CP 16.4) vs 當時 best 32.5：合理。
- 未列入 top5 的其餘排除：Claude low (@47, CP ~19.8 < 56.1x1.05)、Terra max (@42, CP 30.0 < 56.1x1.05) 均為 CP 無新高；Luna max (@38) 低於 min-score floor 40。合理。
- other 桶僅 GLM 一行 (n=1)，無淘汰可比；不與 private-safe 混排（禁令 8 遵守）。

---
--- script output below (verbatim) ---

# Frontier result (as-of run: `runs/2026-09-17-general-intelligence/candidates.csv`)
- min-score=40, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all
- Rule: buckets never merged; FREE rows never in numeric frontier.

## General @ AA-Intelligence-Index-v4.3 | basis=api | bucket=other (n=1)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 42 | GLM-5.3-Flash Z.AI API Standard | $0.25 | 168.0 | Z.AI | other | highest-capability start of this bucket |

## General @ AA-Intelligence-Index-v4.3 | basis=api | bucket=private-safe (n=12)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 53 | GPT-6 Astra xhigh OpenAI API Standard | $2.31 | 22.9 | OpenAI | private-safe | highest-capability start of this bucket |
| 51 | GPT-6 Astra high OpenAI API Standard | $1.72 | 29.7 | OpenAI | private-safe | CP new high +29.2%% at score step -2.00 |
| 50 | GPT-6 Astra medium OpenAI API Standard | $1.54 | 32.5 | OpenAI | private-safe | same-tier (gap 1.00 < 2.0) CP takeover +9.5%% |
| 46 | GPT-6 Astra low OpenAI API Standard | $0.82 | 56.1 | OpenAI | private-safe | CP new high +72.8%% at score step -5.00 |

<details><summary>Dominated / excluded sample (8, top 5)</summary>

- GPT-6 Astra max OpenAI API Standard (S=53, $3.26): CP no new high (16.26 <= best 22.94 x 1.05)
- Claude Fable 5.1 xhigh-fallback Anthropic API Standard (S=53, $5.98): CP no new high (8.86 <= best 22.94 x 1.05)
- Claude Fable 5.1 max-fallback Anthropic API Standard (S=53, $7.63): CP no new high (6.95 <= best 22.94 x 1.05)
- Claude Fable 5.1 high-fallback Anthropic API Standard (S=51, $3.91): CP no new high (13.04 <= best 29.65 x 1.05)
- Claude Fable 5.1 medium-fallback Anthropic API Standard (S=49, $2.98): CP no new high (16.44 <= best 32.47 x 1.05)
</details>

## FREE sidecar: none in this input.
