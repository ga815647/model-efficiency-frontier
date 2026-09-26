# Frontier — General / AA Intelligence Index v4.3 (2026-09-17) — v4: floor 30，七分級矩陣

- as-of: 2026-09-17 ｜ benchmark: General — AA Intelligence Index v4.3 ｜ URL: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3
- composition: AA-Briefcase, GDPval-AA v2, AutomationBench-AA, Terminal-Bench 4.0, SciCode, HLE, GDP.pdf, CritPt, AA-Omniscience, AA-LCR v1.1
- cost basis: api only ｜ min-score: 30（v3 的 40 → v4 用戶確認下調） ｜ max-cost: 無 ｜ eps: score 2.0 / CP 5%
- 分級線（v4.3 專用，換版重切）：T1 52+／T2 45–51／T3 38–44／T4 31–37／T5 24–30；級距 7 分（錨點 53/46/39，遠大於噪音帶 2.0，級間為真差異）
- floor 30 理由：T5 有 Kimi low 30 實證；30 以下（MiMo 26、Sol NR 28無 cost，o3 20*為估計值）無 A 級數據，正好當證據線（禁令 6 仍滿足：門檻存在且有理由）
- privacy 定義版本: AGENTS.md 2026-09-17 binary（best-effort）；兩桶獨立計算；mode=all
- script: scripts/compute_frontier.py --min-score 30 --privacy-mode all ｜ snapshot: runs/2026-09-17-general-v4/candidates.csv（frozen；25 行 = v3 20 + 5 new）

## TL;DR

- private-safe：Astra 四階 + 新增兩階尾巴（Sol medium 39 新高 → Luna 38 同層接管 CP 211）。
- other：Contributor（B）獨佔不變；Kimi low 30 入列即被淘汰。
- 本次 delta：+5 GRADE-A（Sol med/low、Terra high、Sonnet high、Kimi low）；frontier 6+1。

## 能力分級 × 兩桶矩陣（展示用；★ = frontier 成員）

| 級別（v4.3） | private-safe | other |
|---|---|---|
| T1 旗艦 52+ | Astra max 53/$3.26；Astra xhigh★ 53/$2.31；Fable max-fb 53/$7.63；Fable xhigh-fb 53/$5.98 | 從缺 |
| T2 強 45–51 | Astra high★ 51/$1.72；Fable high-fb 51/$3.91；Astra med★ 50/$1.54；Fable5 max-fb 50/$8.75；Fable med-fb 49/$2.98；Spark max 48/$1.60；Opus high 48/$3.61；Fable low-fb 47/$2.37；Sol max 47/$1.99；Astra low★ 46/$0.82；Spark Std 45/$1.37 | Contributor★ 45/$0.07[B] |
| T3 主力 38–44 | Terra max 42/$1.40；Sol med★ 39/$0.50；Luna★ 38/$0.18 | Kimi max 44/$2.00；GLM Flash 42/$0.25 |
| T4 輕量 31–37 | Sol low 34/$0.26；Terra high 34/$0.34；Sonnet high 32/$1.79 | 從缺 |
| T5 門檻 24–30 | 從缺 | Kimi low 30/$1.15 |

註：T4 safe 三行全被 Luna 同層接管線淘汰（非無數據）；T5 safe、other T1／T4 從缺屬正常。

## Frontier（兩桶獨立計算，並列展示，不混排）

### private-safe（21 進 → 6 留）

| Score | Identity | $/task | CP | 判決 |
|---|---|---|---|---|
| 53 | GPT-6 Astra xhigh OpenAI API Standard | $2.31 | 22.9 | 起點：同分最便宜 |
| 51 | GPT-6 Astra high OpenAI API Standard | $1.72 | 29.7 | 新高 +29%（-2 分） |
| 50 | GPT-6 Astra medium OpenAI API Standard | $1.54 | 32.5 | 同層接管 +9.5%（gap 1 < 2） |
| 46 | GPT-6 Astra low OpenAI API Standard | $0.82 | 56.1 | 新高 +72.8%（-5 分） |
| 39 | GPT-5.6 Sol medium OpenAI API Standard | $0.50 | 78.0 | 新高 +39%（-7 分） |
| 38 | GPT-5.6 Luna max OpenAI API Standard | $0.18 | 211.1 | 同層接管 +170.7%（gap 1 < 2） |

### other（4 進 → 1 留；★= B 級推導 cost）

| Score | Identity | $/task | CP | 判決 |
|---|---|---|---|---|
| 45 | Muse Spark 1.3 xhigh Meta Contributor ★ | $0.07 | 642.9 | 起點（推導值，見 caveat） |

B-caveat：other 台階由 Contributor 單獨決定；margin 巨大（642.9 vs 次位 168），結論穩健但按禁令 9 標示。

## 淘汰與排除一覽（覆核並列，非排名）

### 演算淘汰（script 理由）

| Identity | S | $/task | 桶 | 判決 |
|---|---|---|---|---|
| GPT-6 Astra max | 53 | $3.26 | safe | 同分更貴（CP 16.3） |
| Claude Fable 5.1 xhigh-fb | 53 | $5.98 | safe | 同分更貴（CP 8.9） |
| Claude Fable 5.1 max-fb | 53 | $7.63 | safe | 同分更貴（CP 7.0） |
| Claude Fable 5.1 high-fb | 51 | $3.91 | safe | 同分更貴（CP 13.0） |
| Claude Fable 5 max-fb | 50 | $8.75 | safe | 全 run 最貴，無 CP 優勢 |
| Claude Fable 5.1 medium-fb | 49 | $2.98 | safe | CP 無新高（16.4） |
| Muse Spark 1.3 max | 48 | $1.60 | safe | 同段無優勢（CP 30.0 < 34.1） |
| Claude Opus 5 high | 48 | $3.61 | safe | CP 無新高（13.3） |
| Claude Fable 5.1 low-fb | 47 | $2.37 | safe | CP 無新高（19.8） |
| GPT-5.6 Sol max | 47 | $1.99 | safe | CP 無新高（23.6） |
| Muse Spark 1.3 xhigh Standard | 45 | $1.37 | safe | 低段無優勢（CP 32.9 < 58.9） |
| GPT-5.6 Terra max | 42 | $1.40 | safe | 低段無優勢（CP 30.0） |
| GPT-5.6 Sol low（new） | 34 | $0.26 | safe | 被 Luna 同層接管（CP 130.8 < 221.7） |
| GPT-5.6 Terra high（new） | 34 | $0.34 | safe | 同分更貴（CP 100.0） |
| Claude Sonnet 5 high（new） | 32 | $1.79 | safe | CP 無新高（17.9） |
| Kimi K3 max | 44 | $2.00 | other | CP 無新高（22.0） |
| GLM-5.3-Flash | 42 | $0.25 | other | CP 無新高（168.0） |
| Kimi K3 low（new） | 30 | $1.15 | other | CP 無新高（26.1） |

### 方法排除（未進演算）

| 對象 | 原因 |
|---|---|
| Claude Opus 5 max（live 63） | 非 v4.3（article 為 51），禁令 10 |
| GLM-5.3 max | 來源分歧（44 vs 45），版本無法確認 |
| Qwen3.8 40、Sol xhigh 44 / high 42、Terra medium 30、GPT-5.5 medium 34、DeepSeek 36、MiMo 26、Sol NR 28 | 有分數無 AA 實測 cost，GRADE-C 禁入 |
| Kimi K3 releases-page 60 | 與 comparison 頁 44 矛盾，屬他版，禁入 |
| v4.1.1 殘留（Spark 61/$0.55 等） | 不同任務集，禁令 1 |

## 附錄

<details><summary>證據 / 來源 / v4 delta</summary>

- privacy 證據（沿用）：OpenAI https://developers.openai.com/api/docs/guides/your-data；Anthropic https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training；Meta Standard→safe / Contributor→other：https://ai.developer.meta.com/docs/pricing-rate-limits/；Kimi→other（無聲明，不推定）
- 20 carried rows：同 v3（僅 Luna notes 更新為入門檻說明），其餘凍結
- 5 new GRADE-A（comparison pages, retrieved 2026-09-17）：Sol med …/claude-fable-5-1-high-vs-gpt-5-6-sol-medium（同頁 Fable high 51 交叉核對 v4.3）；Sol low …/gpt-5-6-sol-low-vs-gpt-5-6-sol；Terra high …/gpt-5-6-sol-vs-gpt-5-6-terra-high；Sonnet high + Kimi low …/kimi-k3-low-vs-claude-sonnet-5-high（頁含 TB-4.0 + AutomationBench-AA，v4.3 組件）
- v4 delta vs runs/2026-09-17-general-v3/（frozen）：+5 行，floor 40→30，同 benchmark+版本+cost basis

</details>

<details><summary>腳本輸出原文（verbatim）</summary>

# Frontier result (as-of run: `runs/2026-09-17-general-v4/candidates.csv`)
- min-score=30, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all
- Rule: buckets never merged; FREE rows never in numeric frontier.

## General @ AA-Intelligence-Index-v4.3 | basis=api | bucket=other (n=4)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 45 | Muse Spark 1.3 xhigh Meta Contributor | $0.07 | 642.9 | Meta | other | highest-capability start of this bucket |

<details><summary>Dominated / excluded sample (3, top 5)</summary>

- Kimi K3 max Kimi API Standard (S=44, $2.00): CP no new high (22.00 <= best 642.86 x 1.05)
- GLM-5.3-Flash Z.AI API Standard (S=42, $0.25): CP no new high (168.00 <= best 642.86 x 1.05)
- Kimi K3 low Kimi API Standard (S=30, $1.15): CP no new high (26.09 <= best 642.86 x 1.05)
</details>

## General @ AA-Intelligence-Index-v4.3 | basis=api | bucket=private-safe (n=21)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 53 | GPT-6 Astra xhigh OpenAI API Standard | $2.31 | 22.9 | OpenAI | private-safe | highest-capability start of this bucket |
| 51 | GPT-6 Astra high OpenAI API Standard | $1.72 | 29.7 | OpenAI | private-safe | CP new high +29.2%% at score step -2.00 |
| 50 | GPT-6 Astra medium OpenAI API Standard | $1.54 | 32.5 | OpenAI | private-safe | same-tier (gap 1.00 < 2.0) CP takeover +9.5%% |
| 46 | GPT-6 Astra low OpenAI API Standard | $0.82 | 56.1 | OpenAI | private-safe | CP new high +72.8%% at score step -5.00 |
| 39 | GPT-5.6 Sol medium OpenAI API Standard | $0.50 | 78.0 | OpenAI | private-safe | CP new high +39.0%% at score step -7.00 |
| 38 | GPT-5.6 Luna max OpenAI API Standard | $0.18 | 211.1 | OpenAI | private-safe | same-tier (gap 1.00 < 2.0) CP takeover +170.7%% |

<details><summary>Dominated / excluded sample (15, top 5)</summary>

- GPT-6 Astra max OpenAI API Standard (S=53, $3.26): CP no new high (16.26 <= best 22.94 x 1.05)
- Claude Fable 5.1 xhigh-fallback Anthropic API Standard (S=53, $5.98): CP no new high (8.86 <= best 22.94 x 1.05)
- Claude Fable 5.1 max-fallback Anthropic API Standard (S=53, $7.63): CP no new high (6.95 <= best 22.94 x 1.05)
- Claude Fable 5.1 high-fallback Anthropic API Standard (S=51, $3.91): CP no new high (13.04 <= best 29.65 x 1.05)
- Claude Fable 5 max-fallback Anthropic API Standard (S=50, $8.75): CP no new high (5.71 <= best 32.47 x 1.05)
</details>

## FREE sidecar: none in this input.

</details>
