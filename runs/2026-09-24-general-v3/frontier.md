# Frontier — General v3 full-family 補收錄 / AA Intelligence Index v4.3 + v4.3.2 split (2026-09-24) — C-head/C-mid 真錨點落地

- as-of: 2026-09-24 ｜ benchmark: General — AA Intelligence Index **v4.3（50 行，frozen 承接）＋ v4.3.2（14 行：4 承接＋10 新增，禁令 10 分開算）** ｜ URL: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3 ＋ release pages（gpt-6-luna／gpt-6-sol／gpt-5-6-sol／gpt-5-6-terra／gpt-5-6-luna）＋ model page（deepseek-v4-1-flash）＋ sweep /tmp/chain-sweep.md（各行 URL 見 candidates.csv notes）
- composition: v4.3 系 10 evals（AA-Briefcase v1.1, GDPval-AA v2.1, AutomationBench-AA, Terminal-Bench 4.0, SciCode, HLE, GDP.pdf, CritPt, AA-Omniscience, AA-LCR v1.1）；v4.3.2 為同系 live patch，版本字串不同故分組計算、永不合併（禁令 10）
- cost basis: api only ｜ min-score: 39（承接 v1/v2；禁令 6 門檻＋理由俱在） ｜ max-cost: 無 ｜ eps: score 2.0 / CP 5%
- eps 來源：AA methodology 頁公布 95% CI < ±1%（v4.3.2 仍有效，2026-09-24 re-confirmed）；eps_score = 2×CI = 2.0（沿用＋fresh confirmation）；eps_cp = 5% 固定
- 分級線（本版專用，換版重切；錨點＝v4.3 合併 frontier CP 峰值 Contributor 45／CP 642.9，級距 7＝3.5×2.0）：T1 52+／T2 45–51／T3 38–44／T4 31–37／T5 30–；v4.3.2 組不另立分級（僅 2 行過門檻，展示併入 T2/T3 註記）
- privacy 註記 only (2026-09-24 取消分桶；欄位保留作註記，不分組不過濾）
- A>=B DELETED（2026-09-24 單一主線：全角色 General only，Coding runs 歸檔保留、不刪除、不再開新 run、不再參與 picks；跨 benchmark 比較無意義，故無 A>=B 檢查）
- script: scripts/compute_frontier.py --min-score 39 --eps-score 2.0 --privacy-mode all ｜ snapshot: runs/2026-09-24-general-v3/candidates.csv（64 行＝54 v2 承接＋10 新增 GRADE-A；GRADE-C 仍排除：opus-4-6 max 32 無 cost、grok-nonreasoning 15 est 無 cost、gpt-5-6-sol-nonreasoning 無 cost（release 頁 cost `–`））
- 版本分裂聲明（禁令 10）：腳本按 (benchmark, benchmark_version, cost_basis) 分組，v4.3（n=50）與 v4.3.2（n=14）各自獨立 frontier；floor 決策用錨點所在組（A/B/D 用 v4.3，C 用 v4.3.2 新錨點），兩組各自報告、不混入對方數學

## TL;DR（兩組各自 frontier；floor 決策用錨點所在組）

- v4.3 組（n=50）：frontier 與 v1/v2 完全一致，7 留（58 Opus 5.5 max-fb $5.98 → 45 Contributor $0.07[B]）；新增行不在此組，數學零變動。
- v4.3.2 組（n=14）：2 留——GLM-5.3 max 45/$2.01（CP 22.4，該組起點）→ DeepSeek V4.1 Flash max 39/$0.27（CP 144.4，新高 +545.2%，-6 分）；其餘 12 行 below min-score floor（未進演算，非演算淘汰）。
- 錨點落地（本次核心修復）：C-head 不再是 `無AA分數→退回`——GPT-6 Luna low 21 實測存在（release 頁＋user screenshot），chain query 加 alias `gpt 6 luna low` 後 anchor 落地，band [19,+inf) 開出；C-mid 不再是 `無AA分數→退回`——DeepSeek V4.1 Flash max 39 實測存在（model page＋user screenshot），anchor 落地，band [37,+inf) 開出。A-tail（GLM-max 45）、C-tail（Haiku reasoning 17）維持 v2 真錨點。
- Luna low 行進數學（frontier 比較保留）但永不當 pick（band CP-best 仍是 Contributor 45；禁令 14 僅排除 Claude-family，Luna 是被 CP 規則自然落選，非排除）。
- Sol/Terra/Luna 缺口關閉：release 頁 6-effort sweep 確認 v2 已收 max/xhigh/high/medium/low（Sol-6、Terra-5.6、Luna-5.6），v3 補上 non-reasoning（Sol-6 28/$0.33、Terra-5.6 21/$0.14、Luna-5.6 16/$0.01）＋ Luna-6 medium 29/$0.02、low 21/$0.0045、non-reasoning 18/$0.01 ＋ Terra-5.6 low 27/$0.14 ＋ Luna-5.6 medium 25/$0.02、low 21/$0.01；gpt-5-6-sol-nonreasoning 有分（28）無 cost（release 頁 `–`）→ GRADE-C 未加行。

## 能力五級矩陣（展示用；★ = v4.3 frontier 成員；◆ = v4.3.2 行；privacy 僅註記，[B]=推導 cost）

| 級別（本版，錨點 Contributor 45／642.9） | 成員 |
|---|---|
| T1 旗艦 52+ | Opus 5.5 max★ 58/$5.98；Opus 5.5 xhigh★ 56/$3.46；Opus 5.5 high★ 54/$1.82；Astra max 53/$3.26；Fable 5.1 max-fb 53/$7.63；Fable 5.1 xhigh-fb 53/$5.98；Astra xhigh 52/$2.31（全 v4.3） |
| T2 強 45–51 | Astra high 51/$1.72；Opus 5.5 med★ 51/$1.34；Opus 5 max 51/$5.86；Fable 5.1 high-fb 51/$3.91；Astra med 50/$1.54；Opus 5 xhigh 50/$4.88；Fable 5 max-fb 50/$8.75；Fable 5.1 med-fb 49/$2.98；Spark max 48/$1.60；Opus 5 high 48/$3.61；GPT-6 Sol max★ 48/$1.06；Sol 5.6 max 47/$1.99；Fable 5.1 low-fb 47/$2.37；Astra low★ 46/$0.82；Grok 4.7 xhigh 46/$3.74（註記 other）；Opus 5 med 45/$2.19；Spark xhigh-Std 45/$1.37；Contributor★ 45/$0.07[B]（註記 other）；◆ GLM-5.3 max 45/$2.01（v4.3.2，註記 other，同分併列展示、數學分組獨立） |
| T3 主力 38–44 | Sol 6 xhigh 44/$0.53；Sol 5.6 xhigh 44/$1.18；Kimi max 44/$2.00（註記 other）；Sol 6 high 43/$0.37；Sol 5.6 high 42/$0.81；Terra 5.6 max 42/$1.40；Opus 5.5 low 42/$0.55；GLM Flash 42/$0.25（註記 other）；Sol 6 med 40/$0.25；Sol 5.6 med 39/$0.50；Opus 5 low 39/$1.10；Terra 5.6 xhigh 38/$0.63；Sonnet 5 max 38/$5.09（v4.3）；◆ DeepSeek V4.1 Flash max 39/$0.27（v4.3.2，註記 other，數學分組獨立） |
| T4 輕量 31–37 | 全 floor-excluded（v4.3）：Luna 6 max 37/$0.07；Luna 5.6 max 37/$0.18；Luna 5.6 xhigh 35/$0.09；Sol 6 low 34/$0.13；Luna 6 xhigh 34/$0.04；Terra 5.6 high 34/$0.34；Sonnet 5 xhigh 34/$2.87；Sol 5.6 low 33/$0.26；Luna 6 high 32/$0.03；Luna 5.6 high 32/$0.04；Sonnet 5 high 32/$1.79 |
| T5 門檻 30– | Terra 5.6 med 30/$0.18（v4.3 floor-excluded）；◆ Luna 6 medium 29/$0.02、Sol 6 non-reasoning 28/$0.33、Terra 5.6 low 27/$0.14、Luna 5.6 medium 25/$0.02、Qwen3.7 Plus 25/$0.30、MiniMax M2.7 23/$0.10、Luna 6 low 21/$0.0045、Terra 5.6 non-reasoning 21/$0.14、Luna 5.6 low 21/$0.01、Luna 6 non-reasoning 18/$0.01、Haiku reasoning 17/$0.21（Claude-family 永不 pick）、Luna 5.6 non-reasoning 16/$0.01（全 v4.3.2，floor-excluded） |

註：T4 整級＋T5 均為 floor-excluded（<39，未進演算）；分級錨點仍為 v4.3 Contributor（未搬家：v4.3.2 DeepSeek CP 144.4 未挑戰 v4.3 峰值 642.9，且跨版本不比 CP）。

## Frontier v4.3 組（50 進 → 7 留；與 v1/v2 一致，verbatim 見附錄）

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

## Frontier v4.3.2 組（14 進 → 2 留；獨立計算，永不與 v4.3 混排）

| Score | Identity | $/task | CP | 判決 |
|---|---|---|---|---|
| 45 | GLM-5.3 max Z.AI API Standard | $2.01 | 22.4 | 該組起點（highest-capability start） |
| 39 | DeepSeek V4.1 Flash max DeepSeek API Standard | $0.27 | 144.4 | 新高 +545.2%（-6 分；v3 新增，用戶截圖＋model page 雙證） |

floor-excluded（<39，未進演算；非演算淘汰）：Luna 6 medium 29/$0.02；Sol 6 non-reasoning 28/$0.33；Terra 5.6 low 27/$0.14；Luna 5.6 medium 25/$0.02；Qwen3.7 Plus 25/$0.30；MiniMax M2.7 23/$0.10；Luna 6 low 21/$0.0045；Terra 5.6 non-reasoning 21/$0.14；Luna 5.6 low 21/$0.01；Luna 6 non-reasoning 18/$0.01；Haiku reasoning 17/$0.21（Claude-family，另受禁令 14 pick 排除）；Luna 5.6 non-reasoning 16/$0.01。

## 方法排除（未進演算；v3 更新）

| 對象 | 原因 |
|---|---|
| claude-opus-4-6 (max) 32 | 有分無 AA 實測 cost（cost `–`），GRADE-C 禁入（sweep 行 30–32） |
| xai grok-4.20-0309-non-reasoning 15 est | estimated 分＋cost N/A，GRADE-C 禁入（sweep 行 41） |
| gpt-5-6-sol-non-reasoning 28 | release 頁 cost `–`（無 AA 實測 cost），GRADE-C 禁入（v3 sweep 新確認） |
| kimi-for-coding-highspeed (off)、gpt-6-sol-fast (medium)、qwen3.6-flash (low) | sweep 三遍核對後真退回（sweep 行 17–20、25–28、37–40）；closest 同族行（Kimi K2.7 Code 26、Sol medium 40、Qwen3.6 35B A3B 18）為不同 ID，永不代入。gpt-6-luna-fast (low) 本體仍真退回（無 AA ID），但其 base-effort 對應行 Luna low 21 已收錄並作 C-head alias anchor（fast=strip suffix，非代入） |
| Coding 側全部新行 | 歸檔保留、不刪除、不再開新 run、不再參與 picks（單一主線政策）；Coding Agent Index 為 JS-rendered，static 證據下全真退回（sweep 行 12/16/20/24/28/32/34/36/40/42）——註記，不發明行 |

## 附錄 A：pick 變化 vs v2（詳見 recommend.md）

- C-head：v2 `無AA分數→退回` → v3 anchor Luna low 21 實測，band [19,+inf) 開出；band CP-best Contributor 45（anchor ≠ pick 屬設計本意；Luna low 自身 CP 4666.7 雖更高但 S=21 < min-score 39 被門檻擋，故不當 pick——門檻先於 CP，禁令 6）。
- C-mid：v2 `無AA分數→退回` → v3 anchor DeepSeek V4.1 Flash max 39 實測，band [37,+inf) 開出；band CP-best 與 head 同值 → suppression → 從缺（原 pick 註記保留）。
- C-tail：維持 v2（anchor Haiku reasoning 17，band [15,+inf)；pick 排除 Claude-family 後 Contributor 45 → 上檔 CP ≥ 本檔 CP → 從缺）。
- A/B/D：anchor 與 pick 均無變化（A floor 從缺→沿用 39；B 從缺；D floor 45）。
- A>=B DELETED：單一主線下無 coding-floor 比較；腳本 `A>=B check: skipped`（未傳 --coding-floor，屬預期行為，非錯誤）。

## 附錄 B

<details><summary>腳本輸出原文（verbatim，compute_frontier.py exit 0）</summary>

```
# Frontier result (as-of run: `runs/2026-09-24-general-v3/candidates.csv`)
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

## General @ AA-Intelligence-Index-v4.3.2 | basis=api (n=14)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 45 | GLM-5.3 max Z.AI API Standard | $2.01 | 22.4 | Z.AI | other | highest-capability start of this bucket |
| 39 | DeepSeek V4.1 Flash max DeepSeek API Standard | $0.27 | 144.4 | DeepSeek | other | CP new high +545.2%% at score step -6.00 |

<details><summary>Dominated / excluded sample (12, top 5)</summary>

- GPT-6 Luna medium OpenAI API Standard (S=29, $0.02): below min-score floor (29.0 < 39.0)
- GPT-6 Sol non-reasoning OpenAI API Standard (S=28, $0.33): below min-score floor (28.0 < 39.0)
- GPT-5.6 Terra low OpenAI API Standard (S=27, $0.14): below min-score floor (27.0 < 39.0)
- GPT-5.6 Luna medium OpenAI API Standard (S=25, $0.02): below min-score floor (25.0 < 39.0)
- Qwen3.7 Plus default Alibaba API Standard (S=25, $0.30): below min-score floor (25.0 < 39.0)
</details>

## FREE sidecar: none in this input.
```

</details>
