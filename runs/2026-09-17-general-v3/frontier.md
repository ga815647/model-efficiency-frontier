# Frontier — General / AA Intelligence Index v4.3 (2026-09-17) — v3

- as-of: 2026-09-17 ｜ benchmark: General — AA Intelligence Index v4.3 ｜ URL: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3
- composition: AA-Briefcase, GDPval-AA v2, AutomationBench-AA, Terminal-Bench 4.0, SciCode, HLE, GDP.pdf, CritPt, AA-Omniscience, AA-LCR v1.1
- cost basis: api only ｜ min-score: 40（本次確認） ｜ max-cost: 無 ｜ eps: score 2.0 / CP 5%
- privacy 定義版本: AGENTS.md 2026-09-17 binary（best-effort）；兩桶獨立計算；mode=all
- version check: v4.3（2026-09-07）仍是最新發布版（v5 目標 10 月底），無混版
- script: scripts/compute_frontier.py --min-score 40 --privacy-mode all ｜ snapshot: runs/2026-09-17-general-v3/candidates.csv（frozen）

## TL;DR

- private-safe：Astra 四階不變（53 → 51 → 50同層 → 46），新增 4 個挑戰者全被淘汰。
- other：Contributor（B 級推導）獨佔；新增 Kimi 與 GLM Flash 皆敗。
- 本次 delta：+5 行（v2 15 → v3 20）；frontier 成員零變動。

## 能力分級 × 兩桶矩陣（展示用；分級線僅適用 v4.3，換版重切；★ = frontier 成員）

| 級別（v4.3 分數帶） | private-safe | other |
|---|---|---|
| T1 旗艦 52+ | Astra max 53/$3.26；Astra xhigh★ 53/$2.31；Fable max-fb 53/$7.63；Fable xhigh-fb 53/$5.98 | 從缺 |
| T2 強 50–51 | Astra high★ 51/$1.72；Fable high-fb 51/$3.91；Astra med★ 50/$1.54；Fable5 max-fb 50/$8.75 | 從缺 |
| T3 主力 47–49 | Fable med-fb 49/$2.98；Spark max 48/$1.60；Opus high 48/$3.61；Fable low-fb 47/$2.37；Sol max 47/$1.99 | 從缺 |
| T4 輕量 44–46 | Astra low★ 46/$0.82；Spark xhigh Std 45/$1.37 | Contributor★ 45/$0.07[B]；Kimi max 44/$2.00 |
| T5 門檻 40–43 | Terra max 42/$1.40 | GLM Flash 42/$0.25 |

註：Luna max（38）低於門檻 40，不列入矩陣；矩陣只管展示對應，frontier 數學不變。

## Frontier（兩桶獨立計算，並列展示，不混排）

### private-safe（17 進 → 4 留）

| Score | Identity | $/task | CP | 判決 |
|---|---|---|---|---|
| 53 | GPT-6 Astra xhigh OpenAI API Standard | $2.31 | 22.9 | 起點：同分最便宜 |
| 51 | GPT-6 Astra high OpenAI API Standard | $1.72 | 29.7 | 新高 +29%（-2 分） |
| 50 | GPT-6 Astra medium OpenAI API Standard | $1.54 | 32.5 | 同層接管 +9.5%（gap 1 < 2） |
| 46 | GPT-6 Astra low OpenAI API Standard | $0.82 | 56.1 | 新高 +72.8%（-5 分） |

### other（3 進 → 1 留；★= B 級推導 cost）

| Score | Identity | $/task | CP | 判決 |
|---|---|---|---|---|
| 45 | Muse Spark 1.3 xhigh Meta Contributor ★ | $0.07 | 642.9 | 起點（推導值，見 caveat） |

B-caveat：other 台階由 Contributor 單獨決定；margin 3.8x（642.9 vs 次位 168，推導需偏 ~4x 才翻轉），結論穩健但按禁令 9 標示。

## 淘汰與排除一覽（覆核並列，非排名）

### 演算淘汰（script 理由）

| Identity | S | $/task | 桶 | 判決 |
|---|---|---|---|---|
| GPT-6 Astra max | 53 | $3.26 | safe | 同分更貴（CP 16.3） |
| Claude Fable 5.1 xhigh-fb | 53 | $5.98 | safe | 同分更貴（CP 8.9） |
| Claude Fable 5.1 max-fb | 53 | $7.63 | safe | 同分更貴（CP 7.0） |
| Claude Fable 5.1 high-fb | 51 | $3.91 | safe | 同分更貴（CP 13.0） |
| Claude Fable 5 max-fb（new） | 50 | $8.75 | safe | 全 run 最貴，無 CP 優勢 |
| Claude Fable 5.1 medium-fb | 49 | $2.98 | safe | CP 無新高（16.4） |
| Muse Spark 1.3 max（new） | 48 | $1.60 | safe | 同段無優勢（CP 30.0 < 34.1） |
| Claude Opus 5 high（new） | 48 | $3.61 | safe | CP 無新高（13.3） |
| Claude Fable 5.1 low-fb | 47 | $2.37 | safe | CP 無新高（19.8） |
| GPT-5.6 Sol max（new） | 47 | $1.99 | safe | CP 無新高（23.6） |
| Muse Spark 1.3 xhigh Standard | 45 | $1.37 | safe | 低段無優勢（CP 32.9 < 58.9） |
| GPT-5.6 Terra max | 42 | $1.40 | safe | 低段無優勢（CP 30.0） |
| GPT-5.6 Luna max | 38 | $0.18 | safe | 低於門檻 40 |
| Kimi K3 max（new） | 44 | $2.00 | other | CP 無新高（22.0，GRADE-A 仍輸 B 行 29x） |
| GLM-5.3-Flash | 42 | $0.25 | other | CP 無新高（168.0） |

### 方法排除（未進演算）

| 對象 | 原因 |
|---|---|
| Claude Opus 5 max（live 63） | 非 v4.3（article 為 51），禁令 10 |
| GLM-5.3 max | 來源分歧（44 vs 45），版本無法確認 |
| Qwen3.8 40、Sol xhigh 44 / high 42 | 有分數無 AA 實測 cost，GRADE-C 禁入 |
| v4.1.1 殘留（Spark 61/$0.55 等） | 不同任務集，禁令 1 |

## 附錄

<details><summary>證據 / 來源 / v3 delta</summary>

- privacy 證據（沿用 v1/v2）：OpenAI https://developers.openai.com/api/docs/guides/your-data；Anthropic https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training；Meta Standard→safe / Contributor→other：https://ai.developer.meta.com/docs/pricing-rate-limits/；Kimi→other（無不訓練聲明，不推定，禁令 3/5）
- 15 carried rows：同 v2（article 2026-09-07 + eval comparison table + Spark xhigh model page），notes 補 GRADE-A/B 前綴
- 5 new GRADE-A（comparison pages, retrieved 2026-09-17）：Spark max https://artificialanalysis.ai/models/comparisons/muse-spark-1-3-vs-muse-spark-1-3-xhigh；Sol max …/gpt-5-6-sol-low-vs-gpt-5-6-sol；Fable 5 …/gpt-5-6-sol-vs-claude-fable-5；Opus 5 high …/claude-opus-5-high-vs-kimi-k3；Kimi …/glm-5-3-vs-kimi-k3
- v3 delta vs runs/2026-09-17-general-v2/（frozen）：+5 行，同 benchmark+版本+cost basis

</details>

<details><summary>腳本輸出原文（verbatim，已校驗一致）</summary>

# Frontier result (as-of run: `runs/2026-09-17-general-v3/candidates.csv`)
- min-score=40, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all
- Rule: buckets never merged; FREE rows never in numeric frontier.

## General @ AA-Intelligence-Index-v4.3 | basis=api | bucket=other (n=3)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 45 | Muse Spark 1.3 xhigh Meta Contributor | $0.07 | 642.9 | Meta | other | highest-capability start of this bucket |

<details><summary>Dominated / excluded sample (2, top 5)</summary>

- Kimi K3 max Kimi API Standard (S=44, $2.00): CP no new high (22.00 <= best 642.86 x 1.05)
- GLM-5.3-Flash Z.AI API Standard (S=42, $0.25): CP no new high (168.00 <= best 642.86 x 1.05)
</details>

## General @ AA-Intelligence-Index-v4.3 | basis=api | bucket=private-safe (n=17)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 53 | GPT-6 Astra xhigh OpenAI API Standard | $2.31 | 22.9 | OpenAI | private-safe | highest-capability start of this bucket |
| 51 | GPT-6 Astra high OpenAI API Standard | $1.72 | 29.7 | OpenAI | private-safe | CP new high +29.2%% at score step -2.00 |
| 50 | GPT-6 Astra medium OpenAI API Standard | $1.54 | 32.5 | OpenAI | private-safe | same-tier (gap 1.00 < 2.0) CP takeover +9.5%% |
| 46 | GPT-6 Astra low OpenAI API Standard | $0.82 | 56.1 | OpenAI | private-safe | CP new high +72.8%% at score step -5.00 |

<details><summary>Dominated / excluded sample (13, top 5)</summary>

- GPT-6 Astra max OpenAI API Standard (S=53, $3.26): CP no new high (16.26 <= best 22.94 x 1.05)
- Claude Fable 5.1 xhigh-fallback Anthropic API Standard (S=53, $5.98): CP no new high (8.86 <= best 22.94 x 1.05)
- Claude Fable 5.1 max-fallback Anthropic API Standard (S=53, $7.63): CP no new high (6.95 <= best 22.94 x 1.05)
- Claude Fable 5.1 high-fallback Anthropic API Standard (S=51, $3.91): CP no new high (13.04 <= best 29.65 x 1.05)
- Claude Fable 5 max-fallback Anthropic API Standard (S=50, $8.75): CP no new high (5.71 <= best 32.47 x 1.05)
</details>

## FREE sidecar: none in this input.

</details>
