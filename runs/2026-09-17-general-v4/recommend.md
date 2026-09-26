# Recommendation matrix (as-of run: `runs/2026-09-17-general-v4/candidates.csv`)
- min-score=30, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all
- tier rule: anchor=safe CP peak (GPT-5.6 Luna max OpenAI API Standard S=38 CP=211.1); width=3.5 x eps_score=7; T1=[52,+inf) T2=[45,52) T3=[38,45) T4=[31,38) T5=(-inf,31)
- Rule: frontier math by compute_frontier only; tiers display only; buckets never merged; FREE rows excluded.

| 級別 | private-safe | other |
|---|---|---|
| T1 | ★ GPT-6 Astra xhigh OpenAI API Standard（S=53, $2.31, CP=22.9）攻堅＝省錢；不推：GPT-6 Astra max OpenAI API Standard、Claude Fable 5.1 xhigh-fallback Anthropic API Standard、Claude Fable 5.1 max-fallback Anthropic API Standard | 從缺 |
| T2 | 攻堅 ★ GPT-6 Astra high OpenAI API Standard（S=51, $1.72）；省錢 ★ GPT-6 Astra low OpenAI API Standard（CP=56.1）；不推：Claude Fable 5.1 high-fallback Anthropic API Standard、Claude Fable 5 max-fallback Anthropic API Standard、Claude Fable 5.1 medium-fallback Anthropic API Standard、Muse Spark 1.3 max Meta Standard、Claude Opus 5 high Anthropic API Standard、GPT-5.6 Sol max OpenAI API Standard、Claude Fable 5.1 low-fallback Anthropic API Standard、Muse Spark 1.3 xhigh Meta Standard | ★ Muse Spark 1.3 xhigh Meta Contributor（S=45, $0.07, CP=642.9）攻堅＝省錢（B級推導） |
| T3 | 攻堅 ★ GPT-5.6 Sol medium OpenAI API Standard（S=39, $0.50）；省錢 ★ GPT-5.6 Luna max OpenAI API Standard（CP=211.1）；不推：GPT-5.6 Terra max OpenAI API Standard | 從缺（Kimi K3 max Kimi API Standard、GLM-5.3-Flash Z.AI API Standard 全被淘汰，不推） |
| T4 | 從缺（GPT-5.6 Sol low OpenAI API Standard、GPT-5.6 Terra high OpenAI API Standard、Claude Sonnet 5 high Anthropic API Standard 全被淘汰，不推） | 從缺 |
| T5 | 從缺 | 從缺（Kimi K3 low Kimi API Standard 全被淘汰，不推） |

FREE sidecar: 0 row(s), excluded from math.
