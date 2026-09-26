# Frontier — General v2 補收錄 / AA Intelligence Index v4.3 + v4.3.2 split (2026-09-24) — A-tail/C-tail 真錨點落地（floor 39 不變）

- as-of: 2026-09-24 ｜ benchmark: General — AA Intelligence Index **v4.3（50 行，frozen 承接）＋ v4.3.2（4 行新增，禁令 10 分開算）** ｜ URL: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3 ＋ sweep 來源 /tmp/chain-sweep.md（各行 model page URL 見 candidates.csv notes）
- composition: v4.3 系 10 evals（AA-Briefcase v1.1, GDPval-AA v2.1, AutomationBench-AA, Terminal-Bench 4.0, SciCode, HLE, GDP.pdf, CritPt, AA-Omniscience, AA-LCR v1.1）；v4.3.2 為同系 live patch，版本字串不同故分組計算、永不合併（禁令 10）
- cost basis: api only ｜ min-score: 39（承接 v1：A>=B 約束，coding floor 39 既定；v4.3.2 組同門檻套用，GLM-5.3 max 45 通過、其餘 3 行被門檻擋；禁令 6 門檻＋理由俱在） ｜ max-cost: 無 ｜ eps: score 2.0 / CP 5%
- eps 來源：AA methodology 頁公布 95% CI < ±1%（v4.3.2 仍有效，2026-09-24 re-confirmed）；eps_score = 2×CI = 2.0（沿用＋fresh confirmation）；eps_cp = 5% 固定
- 分級線（本版專用，換版重切；錨點＝v4.3 合併 frontier CP 峰值 Contributor 45／CP 642.9，級距 7＝3.5×2.0）：T1 52+／T2 45–51／T3 38–44／T4 31–37／T5 30–；v4.3.2 組不另立分級（僅 1 行過門檻，展示併入 T2 註記）
- privacy 註記 only (2026-09-24 取消分桶；欄位保留作註記，不分組不過濾）
- script: scripts/compute_frontier.py --min-score 39 --eps-score 2.0 --privacy-mode all ｜ snapshot: runs/2026-09-24-general-v2/candidates.csv（54 行＝50 frozen 承接＋4 新增 GRADE-A；GRADE-C 2 行未加：opus-4-6 max 32 無 cost、grok-nonreasoning 15 est 無 cost）
- 版本分裂聲明（禁令 10）：腳本按 (benchmark, benchmark_version, cost_basis) 分組，v4.3（n=50）與 v4.3.2（n=4）各自獨立 frontier；General-side floor 決策一律用 v4.3 組（既有），v4.3.2 組僅報告、不混入 v4.3 數學

## TL;DR（兩組各自 frontier；floor 決策用 v4.3）

- v4.3 組（n=50）：frontier 與 v1 完全一致，7 留（58 Opus 5.5 max-fb $5.98 → 45 Contributor $0.07[B]）；新增行不在此組，數學零變動。
- v4.3.2 組（n=4）：GLM-5.3 max 45/$2.01（CP 22.4）為該組起點（highest-capability start）；Qwen3.7 Plus 25/$0.30、MiniMax M2.7 23/$0.10、Haiku reasoning 17/$0.21 均 below min-score floor（未進演算，非演算淘汰）。
- 錨點落地（本次核心修復）：A-tail anchor 不再是 `無AA分數→退回`——GLM-5.3 max 45 實測存在，band [43,+inf) 開出（見 recommend.md Group A）；C-tail anchor 不再是 generation 誤判——Haiku reasoning 17 實測存在，band [15,+inf) 開出（見 recommend.md Group C；pick 排除 Claude-family 後為 Contributor 45，floor 值 45）。
- Haiku 行進數學（frontier 比較保留）但永不當 pick（--exclude-family，禁令 14）；opus-4-6 max 32 與 grok-nonreasoning 15 因無 AA 實測 cost（GRADE-C）未加行，禁令 9/方法排除俱在。

## 能力五級矩陣（展示用；★ = v4.3 frontier 成員；◆ = v4.3.2 新增行；privacy 僅註記，[B]=推導 cost）

| 級別（本版，錨點 Contributor 45／642.9） | 成員 |
|---|---|
| T1 旗艦 52+ | Opus 5.5 max★ 58/$5.98；Opus 5.5 xhigh★ 56/$3.46；Opus 5.5 high★ 54/$1.82；Astra max 53/$3.26；Fable 5.1 max-fb 53/$7.63；Fable 5.1 xhigh-fb 53/$5.98；Astra xhigh 52/$2.31（全 v4.3） |
| T2 強 45–51 | Astra high 51/$1.72；Opus 5.5 med★ 51/$1.34；Opus 5 max 51/$5.86；Fable 5.1 high-fb 51/$3.91；Astra med 50/$1.54；Opus 5 xhigh 50/$4.88；Fable 5 max-fb 50/$8.75；Fable 5.1 med-fb 49/$2.98；Spark max 48/$1.60；Opus 5 high 48/$3.61；GPT-6 Sol max★ 48/$1.06；Sol 5.6 max 47/$1.99；Fable 5.1 low-fb 47/$2.37；Astra low★ 46/$0.82；Grok 4.7 xhigh 46/$3.74（註記 other）；Opus 5 med 45/$2.19；Spark xhigh-Std 45/$1.37；Contributor★ 45/$0.07[B]（註記 other）；◆ GLM-5.3 max 45/$2.01（v4.3.2，註記 other，同分併列展示、數學分組獨立） |
| T3 主力 38–44 | Sol 6 xhigh 44/$0.53；Sol 5.6 xhigh 44/$1.18；Kimi max 44/$2.00（註記 other）；Sol 6 high 43/$0.37；Sol 5.6 high 42/$0.81；Terra 5.6 max 42/$1.40；Opus 5.5 low 42/$0.55；GLM Flash 42/$0.25（註記 other）；Sol 6 med 40/$0.25；Sol 5.6 med 39/$0.50；Opus 5 low 39/$1.10；Terra 5.6 xhigh 38/$0.63；Sonnet 5 max 38/$5.09（全 v4.3） |
| T4 輕量 31–37 | 全 floor-excluded（v4.3）：Luna 6 max 37/$0.07；Luna 5.6 max 37/$0.18；Luna 5.6 xhigh 35/$0.09；Sol 6 low 34/$0.13；Luna 6 xhigh 34/$0.04；Terra 5.6 high 34/$0.34；Sonnet 5 xhigh 34/$2.87；Sol 5.6 low 33/$0.26；Luna 6 high 32/$0.03；Luna 5.6 high 32/$0.04；Sonnet 5 high 32/$1.79 |
| T5 門檻 30– | Terra 5.6 med 30/$0.18（v4.3 floor-excluded）；◆ Qwen3.7 Plus 25/$0.30、MiniMax M2.7 23/$0.10（v4.3.2，floor-excluded）；◆ Haiku reasoning 17/$0.21（v4.3.2，floor-excluded，Claude-family 永不 pick） |

註：T4 整級＋T5 均為 floor-excluded（<39，未進演算）；分級錨點仍為 v4.3 Contributor（未搬家：v4.3.2 GLM-5.3 max CP 22.4 未過 eps_cp margin 挑戰峰值，且跨版本不比 CP）。

## Frontier v4.3 組（50 進 → 7 留；與 v1 一致，verbatim 見附錄）

| Score | Identity | $/task | CP | 判決 |
|---|---|---|---|---|
| 58 | Claude Opus 5.5 max-fallback Anthropic API Standard | $5.98 | 9.7 | 起點：AA 最高實測分 |
| 56 | Claude Opus 5.5 xhigh-fallback Anthropic API Standard | $3.46 | 16.2 | 新高 +66.9%（-2 分） |
| 54 | Claude Opus 5.5 high-fallback Anthropic API Standard | $1.82 | 29.7 | 新高 +83.3%（-2 分） |
| 51 | Claude Opus 5.5 medium-fallback Anthropic API Standard | $1.34 | 38.1 | 新高 +28.3%（-3 分） |
| 48 | GPT-6 Sol max OpenAI API Standard | $1.06 | 45.3 | 新高 +19.0%（-3 分） |
| 46 | GPT-6 Astra low OpenAI API Standard | $0.82 | 56.1 | 新高 +23.9%（-2 分） |
| 45 | Muse Spark 1.3 xhigh Meta Contributor [B] | $0.07 | 642.9 | 同層接管 +1046.0%（gap 1 < 2；推導值，見 caveat） |

B-caveat（承接 v1）：Contributor 接管行由 B 級推導 cost 單獨決定中段台階；margin 巨大（642.9 vs Astra low 56.1），結論穩健但按禁令 9 標示。

## Frontier v4.3.2 組（4 進 → 1 留；獨立計算，永不與 v4.3 混排）

| Score | Identity | $/task | CP | 判決 |
|---|---|---|---|---|
| 45 | GLM-5.3 max Z.AI API Standard | $2.01 | 22.4 | 該組起點（highest-capability start；同組唯一過門檻行） |

floor-excluded（<39，未進演算；非演算淘汰）：Qwen3.7 Plus 25/$0.30；MiniMax M2.7 23/$0.10；Haiku reasoning 17/$0.21（Claude-family，另受禁令 14 pick 排除）。

## 方法排除（未進演算；v2 新增）

| 對象 | 原因 |
|---|---|
| claude-opus-4-6 (max) 32 | 有分無 AA 實測 cost（cost `–`），GRADE-C 禁入（sweep 行 30–32） |
| xai grok-4.20-0309-non-reasoning 15 est | estimated 分＋cost N/A，GRADE-C 禁入（sweep 行 41） |
| gpt-6-luna-fast (low)、kimi-for-coding-highspeed (off)、gpt-6-sol-fast (medium)、qwen3.6-flash (low) | sweep 三遍核對後真退回（sweep 行 13–20、25–28、37–40）；closest 同族行（Luna low 21、Sol medium 40、Kimi K2.7 Code 26、Qwen3.6 35B A3B 18）為不同 ID，永不代入 |
| Coding 側全部新行 | Coding Agent Index 為 JS-rendered，static 證據下全真退回（sweep 行 12/16/20/24/28/32/34/36/40/42）；JS 表需重驗——註記，不發明行，故無 Coding 新 run |

## 附錄 A：pick 變化 vs v1（/tmp/omo-picks.md 基線；詳見 recommend.md）

- A-tail：v1 `無AA分數→退回` → fallback 39 → v2 anchor GLM-5.3 max 45 實測，band [43,+inf) 開出；band CP-best 仍 Contributor 45（與平衡檔同值）→ suppression 上檔 CP ≥ 下檔 CP → floor 檔從缺（原 pick 註記保留）。floor 數字決策仍用 v4.3 組：A floor 沿用 39（A>=B：39 ≥ coding 39 ✓）。
- C-tail：v1 `無AA分數→退回`（理由誤寫為 generation miss）→ v2 anchor Haiku reasoning 17 實測，band [15,+inf) 開出；pick 排除 Claude-family 後為 Contributor 45 → floor 值 45（band CP-best，非 Claude 保送；anchor ≠ pick 屬設計本意）。C floor 39→45 的變化僅反映 band 開出後的 CP-best 查找，不改變 coding floor 39 本體。
- B/D：anchor 與 pick 均無變化（B floor 從缺維持，D floor 45 維持）。
- A>=B 不變量：v2 各組 floor（A 從缺→沿用 39；B 從缺；C 45；D 45）皆 ≥ coding-floor 39，腳本 `A>=B check: pass`。

## 附錄 B

<details><summary>腳本輸出原文（verbatim，compute_frontier.py exit 0）</summary>

```
# Frontier result (as-of run: `runs/2026-09-24-general-v2/candidates.csv`)
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

<details><summary>Dominated / excluded sample (43, top 5)</summary>

- GPT-6 Astra max OpenAI API Standard (S=53, $3.26): CP no new high (16.26 <= best 29.67 x 1.05)
- Claude Fable 5.1 xhigh-fallback Anthropic API Standard (S=53, $5.98): CP no new high (8.86 <= best 29.67 x 1.05)
- Claude Fable 5.1 max-fallback Anthropic API Standard (S=53, $7.63): CP no new high (6.95 <= best 29.67 x 1.05)
- GPT-6 Astra xhigh OpenAI API Standard (S=52, $2.31): CP no new high (22.51 <= best 29.67 x 1.05)
- GPT-6 Astra high OpenAI API Standard (S=51, $1.72): CP no new high (29.65 <= best 38.06 x 1.05)
</details>

## General @ AA-Intelligence-Index-v4.3.2 | basis=api (n=4)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 45 | GLM-5.3 max Z.AI API Standard | $2.01 | 22.4 | Z.AI | other | highest-capability start of this bucket |

<details><summary>Dominated / excluded sample (3, top 5)</summary>

- Qwen3.7 Plus default Alibaba API Standard (S=25, $0.30): below min-score floor (25.0 < 39.0)
- MiniMax M2.7 default MiniMax API Standard (S=23, $0.10): below min-score floor (23.0 < 39.0)
- Claude Haiku 4.5 reasoning Anthropic API Standard (S=17, $0.21): below min-score floor (17.0 < 39.0)
</details>

## FREE sidecar: none in this input.
```

</details>
