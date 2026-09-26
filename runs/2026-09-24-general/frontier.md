# Frontier — General / AA Intelligence Index v4.3 (2026-09-24) — merged single frontier：Opus 5.5 登頂，Contributor 收尾（floor 39）

- as-of: 2026-09-24 ｜ benchmark: General — AA Intelligence Index v4.3（live v4.3.2，同 10-eval 系；pages 標 v4.3.2，run 記 v4.3） ｜ URL: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3
- composition: AA-Briefcase v1.1, GDPval-AA v2.1, AutomationBench-AA, Terminal-Bench 4.0, SciCode, HLE, GDP.pdf, CritPt, AA-Omniscience, AA-LCR v1.1（v4.3.2 methodology 頁確認，同系）
- cost basis: api only ｜ min-score: 39（A>=B 約束：max(有 A 級 cost 證據的最低分付費行，coding floor 39)；理由：coding run floor 39 既定，General 不得低於它；禁令 6 門檻＋理由俱在） ｜ max-cost: 無 ｜ eps: score 2.0 / CP 5%
- eps 來源：AA methodology 頁公布 95% CI < ±1%（v4.3.2 仍有效，2026-09-24 re-confirmed）；eps_score = 2×CI = 2.0（沿用＋fresh confirmation，非新數字）；eps_cp = 5% 固定
- 分級線（本版專用，換版重切；錨點＝合併 frontier CP 峰值 Contributor 45／CP 642.9，級距 7＝3.5×2.0）：T1 52+／T2 45–51／T3 38–44／T4 31–37／T5 30–；錨點搬家（min-30 版 Luna high 32／1066.7→本版 Contributor 45／642.9）：floor 39 排除 Luna 尾端後峰值回到 Contributor，屬 floor 驅動的錨點回遷，分級跟著重切正確
- privacy 註記 only (2026-09-24 取消分桶；欄位保留作註記，不分組不過濾）
- script: scripts/compute_frontier.py --min-score 39 --eps-score 2.0 --privacy-mode all ｜ snapshot: runs/2026-09-24-general/candidates.csv（frozen；50 行合併計算，全 GRADE-A 除 Contributor 1 行 GRADE-B）

## TL;DR（merged single frontier，7 行：58 Opus 5.5 max → 45 Contributor）

- 合併 frontier 共 7 留：58 Opus 5.5 max-fb $5.98／56 xhigh $3.46／54 high $1.82／51 medium $1.34／48 GPT-6 Sol max $1.06／46 Astra low $0.82／45 Contributor $0.07[B]。
- 尾端由 Muse Spark 1.3 xhigh Meta Contributor 45/$0.07（B）same-tier takeover（gap 1.00 < 2.0，+1046.0%）收尾；Luna 尾端（xhigh 34、high 32）與全部 sub-39 行被 floor 39 排除，直說：不是被演算淘汰，是門檻擋掉；錨點回到 Contributor 45／CP 642.9，tier 線重切（T1 52+／T2 45–51／T3 38–44／T4 31–37／T5 30–）。
- vs split-bucket 版掉出者（被 Contributor 線壓制，直說）：Sol 6 xhigh 44／high 43／medium 40、Luna 6 max 37、Grok 4.7 xhigh 46 均未留下；合併後只有一條 frontier，無桶對桶並列。
- 本次 delta vs runs/2026-09-17-general-v4/（frozen）：+25 行（GPT-6 Sol/Luna 全系、Opus 5.5 全系、Opus 5 max/xhigh/medium/low、Sonnet 5 max/xhigh、Grok 4.7、5.6 Terra xhigh/medium、5.6 Sol xhigh/high、5.6 Luna xhigh/high）；3 分數下調各 1 分（Astra xhigh 53→52、5.6 Sol low 34→33、5.6 Luna max 38→37，cost 不變，疑 v4.3.2 rescore）；Kimi low 30/$1.15 變 estimate 無 cost（GRADE-C 剔除）。

## 能力五級矩陣（展示用；★ = frontier 成員；privacy 僅註記，[B]=推導 cost）

| 級別（本版） | 成員（★=frontier；privacy 註記） |
|---|---|
| T1 旗艦 52+ | Opus 5.5 max★ 58/$5.98；Opus 5.5 xhigh★ 56/$3.46；Opus 5.5 high★ 54/$1.82；Astra max 53/$3.26；Fable 5.1 max-fb 53/$7.63；Fable 5.1 xhigh-fb 53/$5.98；Astra xhigh 52/$2.31 |
| T2 強 45–51 | Astra high 51/$1.72；Opus 5.5 med★ 51/$1.34；Opus 5 max 51/$5.86；Fable 5.1 high-fb 51/$3.91；Astra med 50/$1.54；Opus 5 xhigh 50/$4.88；Fable 5 max-fb 50/$8.75；Fable 5.1 med-fb 49/$2.98；Spark max 48/$1.60；Opus 5 high 48/$3.61；GPT-6 Sol max★ 48/$1.06；Sol 5.6 max 47/$1.99；Fable 5.1 low-fb 47/$2.37；Astra low★ 46/$0.82；Grok 4.7 xhigh 46/$3.74（註記 other，~7.1 min/task 離線批量）；Opus 5 med 45/$2.19；Spark xhigh-Std 45/$1.37；Contributor★ 45/$0.07[B]（註記 other） |
| T3 主力 38–44 | Sol 6 xhigh 44/$0.53；Sol 5.6 xhigh 44/$1.18；Kimi max 44/$2.00（註記 other）；Sol 6 high 43/$0.37；Sol 5.6 high 42/$0.81；Terra 5.6 max 42/$1.40；Opus 5.5 low 42/$0.55；GLM Flash 42/$0.25（註記 other）；Sol 6 med 40/$0.25；Sol 5.6 med 39/$0.50；Opus 5 low 39/$1.10；Terra 5.6 xhigh 38/$0.63；Sonnet 5 max 38/$5.09 |
| T4 輕量 31–37 | 全 floor-excluded（見下）：Luna 6 max 37/$0.07；Luna 5.6 max 37/$0.18；Luna 5.6 xhigh 35/$0.09；Sol 6 low 34/$0.13；Luna 6 xhigh 34/$0.04；Terra 5.6 high 34/$0.34；Sonnet 5 xhigh 34/$2.87；Sol 5.6 low 33/$0.26；Luna 6 high 32/$0.03；Luna 5.6 high 32/$0.04；Sonnet 5 high 32/$1.79 |
| T5 門檻 30– | Terra 5.6 med 30/$0.18（floor-excluded） |

註：T4 整級＋T5 均為 floor-excluded（<39，未進演算）；T1–T3 為演算範圍。Grok 速度註記：AA 實測 ~81k out-tok/task、~7.1 min/task，只做展示註記（AGENTS.md 速度註記規則）。

## Frontier（merged single table，50 進 → 7 留；privacy 僅註記）

| Score | Identity | $/task | CP | 判決 |
|---|---|---|---|---|
| 58 | Claude Opus 5.5 max-fallback Anthropic API Standard | $5.98 | 9.7 | 起點：AA 最高實測分（Sept-22 文章） |
| 56 | Claude Opus 5.5 xhigh-fallback Anthropic API Standard | $3.46 | 16.2 | 新高 +66.9%（-2 分） |
| 54 | Claude Opus 5.5 high-fallback Anthropic API Standard | $1.82 | 29.7 | 新高 +83.3%（-2 分） |
| 51 | Claude Opus 5.5 medium-fallback Anthropic API Standard | $1.34 | 38.1 | 新高 +28.3%（-3 分） |
| 48 | GPT-6 Sol max OpenAI API Standard | $1.06 | 45.3 | 新高 +19.0%（-3 分） |
| 46 | GPT-6 Astra low OpenAI API Standard | $0.82 | 56.1 | 新高 +23.9%（-2 分） |
| 45 | Muse Spark 1.3 xhigh Meta Contributor [B] | $0.07 | 642.9 | 同層接管 +1046.0%（gap 1 < 2；推導值，見 caveat；全 run CP 峰值＝分級錨點） |

B-caveat：Contributor 接管行由 B 級推導 cost 單獨決定中段台階；margin 巨大（642.9 vs Astra low 56.1），結論穩健但按禁令 9 標示。GRADE-B 公式：1.37（AA Standard xhigh cost 2026-09-24）× 0.0414/0.78（Standard $1.25/$4.25 blended $0.78，providers 頁 2026-09-24 確認）；假設跨 plan token 用量一致。

## 淘汰與排除一覽（合併演算覆核，非排名；privacy 僅註記）

### 演算淘汰（script 理由，列有助理解者）

| Identity | S | $/task | 判決 |
|---|---|---|---|
| Astra max | 53 | $3.26 | CP 無新高（被 Opus 5.5 high 線壓制） |
| Fable 5.1 xhigh-fb / max-fb | 53 | $5.98/$7.63 | 同分更貴 |
| Astra xhigh | 52 | $2.31 | CP 無新高（且 53→52 下調） |
| Astra high / Fable 5.1 high-fb / Opus 5 max | 51 | $1.72/$3.91/$5.86 | 全被 Opus 5.5 medium 線（38.1）壓制 |
| Astra med / Opus 5 xhigh / Fable 5 max-fb | 50 | $1.54/$4.88/$8.75 | 同上 |
| Fable 5.1 med-fb / Spark max / Opus 5 high | 49/48/48 | $2.98/$1.60/$3.61 | 被 GPT-6 Sol max 線（45.3）壓制 |
| Sol 5.6 max / Fable 5.1 low-fb | 47 | $1.99/$2.37 | 同上 |
| Grok 4.7 xhigh（註記 other） | 46 | $3.74 | 被 Contributor 線（642.9）壓制，合併後掉出 |
| Spark xhigh-Std / Opus 5 med / Sol 5.6 xhigh | 45/45/44 | $1.37/$2.19/$1.18 | 被 Contributor 線壓制 |
| GPT-6 Sol xhigh / high / medium | 44/43/40 | $0.53/$0.37/$0.25 | 被 Contributor 線壓制（vs split-bucket 版掉出，直說） |
| Kimi K3 max（註記 other）/ GLM Flash（註記 other） | 44/42 | $2.00/$0.25 | CP 無新高 |
| Opus 5.5 low / Terra 5.6 max / Sol 5.6 high | 42 | $0.55/$1.40/$0.81 | 被 Contributor 線壓制 |
| Sol 5.6 med / Opus 5 low | 39 | $0.50/$1.10 | 同上 |
| Terra 5.6 xhigh / Sonnet 5 max | 38 | $0.63/$5.09 | floor-excluded（<39，未進演算） |

### floor-excluded（<39，未進演算；非演算淘汰）

| Identity | S | $/task |
|---|---|---|
| Terra 5.6 xhigh / Sonnet 5 max | 38 | $0.63/$5.09 |
| Luna 6 max / Luna 5.6 max | 37 | $0.07/$0.18 |
| Luna 5.6 xhigh | 35 | $0.09 |
| Sol 6 low / Luna 6 xhigh / Terra 5.6 high / Sonnet 5 xhigh | 34 | $0.13/$0.04/$0.34/$2.87 |
| Sol 5.6 low | 33 | $0.26 |
| Luna 6 high / Luna 5.6 high / Sonnet 5 high | 32 | $0.03/$0.04/$1.79 |
| Terra 5.6 med | 30 | $0.18 |

### 方法排除（未進演算）

| 對象 | 原因 |
|---|---|
| Kimi K3 low（原 30/$1.15） | 現為 estimate 34 無 AA cost，GRADE-C 剔除 |
| GPT-6 Sol NR 28、GPT-6 Luna medium 29、Sonnet 5 medium 28、Terra 5.6 low 27、Luna 5.6 medium 25 等 | 低於 floor 39，未入候選 |
| GPT-5.6 Sol NR（cost "—"）、Sonnet 5 NR（cost "–"）、Grok 4.7 非 xhigh efforts、Claude 4.5 Haiku | 有分無 AA 實測 cost，GRADE-C 禁入 |
| v4.1.1 殘留（Spark 61/$0.55 等） | 不同任務集，禁令 1；本 run 無此行 |

## 附錄

<details><summary>證據 / 來源 / delta</summary>

- privacy 註記（沿用 v4，未重驗；欄位保留不分組）：OpenAI https://developers.openai.com/api/docs/guides/your-data；Anthropic https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training；Meta Standard / Contributor：https://ai.developer.meta.com/docs/pricing-rate-limits/
- 新文章（2026-09-24 检索）：Opus 5.5 https://artificialanalysis.ai/articles/claude-opus-5-5（58 分最高實測）；GPT-6 Sol/Luna https://artificialanalysis.ai/articles/gpt-6-sol-and-luna-push-the-cost-efficiency-frontier（Sept-22）；Grok 4.7 https://artificialanalysis.ai/articles/benchmarking-grok-4-7（Sept-21，xhigh-only）
- 3 分數下調（cost 不變，疑 v4.3→v4.3.2 rescore）：Astra xhigh 53→52（https://artificialanalysis.ai/models/gpt-6-astra-xhigh）；5.6 Sol low 34→33（https://artificialanalysis.ai/models/gpt-5-6-sol-low）；5.6 Luna max 38→37（https://artificialanalysis.ai/models/gpt-5-6-luna）
- Opus 5.5 max 模型頁 Speed N/A（無 output-speed），但 cost/task 實測存在，仍 GRADE-A（速度缺值只影響展示註記）
- delta vs runs/2026-09-17-general-v4/（frozen）：+25 行（見 TL;DR），floor 39（A>=B 約束，coding floor 39 既定），同 benchmark+版本+cost basis；v4.3 仍最新（v5 在途，v4.3.2 為 live patch，同系可比）

</details>

<details><summary>腳本輸出原文（verbatim）</summary>

```
# Frontier result (as-of run: `runs/2026-09-24-general/candidates.csv`)
- min-score=39, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all
- Rule: merged single table (privacy display only); FREE rows never in numeric frontier.

## General @ AA-Intelligence-Index-v4.3 | basis=api (n=50)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 58 | Claude Opus 5.5 max-fallback Anthropic API Standard | $5.98 | 9.7 | Anthropic | private-safe | highest-capability start of this bucket |
| 56 | Claude Opus 5.5 xhigh-fallback Anthropic API Standard | $3.46 | 16.2 | Anthropic | private-safe | CP new high +66.9%% at score step -2.00 |
| 54 | Claude Opus 5.5 high-fallback Anthropic API Standard | $1.82 | 29.7 | Anthropic | private-safe | CP new high +83.3%% at score step -2.00 |
| 51 | Claude Opus 5.5 medium-fallback Anthropic API Standard | $1.34 | 38.1 | Anthropic | private-safe | CP new high +28.3%% at score step -3.00 |
| 48 | GPT-6 Sol max OpenAI API Standard | $1.06 | 45.3 | OpenAI | private-safe | CP new high +19.0%% at score step -3.00 |
| 46 | GPT-6 Astra low OpenAI API Standard | $0.82 | 56.1 | OpenAI | private-safe | CP new high +23.9%% at score step -2.00 |
| 45 | Muse Spark 1.3 xhigh Meta Contributor | $0.07 | 642.9 | Meta | other | same-tier (gap 1.00 < 2.0) CP takeover +1046.0%% |
```

</details>
