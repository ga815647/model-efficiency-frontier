# Frontier v4 — API 首跑（2026-09-24）

- as-of: 2026-09-24 / benchmark AA-Intelligence-Index @ AA-Intelligence-Index-v4.3（API envelope `intelligence_index_version=v4.3`；只到 major.minor，patch 不可見）/ cost basis api / min-score 39（floor 見三檔；禁令 6）/ eps_score=2.0（沿用）+ eps_cp=5% / privacy 註記 only（不分桶；禁令 8 RETIRED）/ 分級規則：錨點=合併表 CP 峰值＋級距 3.5×eps（展示 only；禁令 12）
- 收錄：`fetch_aa.py` 拉 `/language/models/free`（671 entries，154 有 score+cost，517 null 跳過；snapshot `aa_snapshot.json` 隨 run 存檔）→ chain-relevant 39 行＋Haiku＋Contributor 手動行＝40 行。provider 全 AA-median（Free 跨 provider 中位數，不拆 provider；plan 維度 API 沒有，Contributor 照舊手動）。
- Contributor（GRADE-B）：score 取同 checkpoint API 新數 45.1；cost＝1.3678（API Standard xhigh）×0.0414/0.78＝$0.07（Meta 定價頁當日重驗有效：Standard $1.25/$4.25/cached $0.15 vs Contributor $0.10/$0.20/cached $0.002；RPM/TPM 3000/4M vs 100/3M；`muse-spark-1.3-contributor` 仍在名單）。
- vs v3（網站抄數）：同源漂移均在 eps 內——GLM-max 45→44.8、Astra-max 53→52.7、Spark-xhigh 45→45.1、Kimi-max 44→43.6；三檔結論不變。API 錨全真：C-head GPT-6 Luna low 20.9（去後綴＋exact-prefix 修後落地）、C-mid DeepSeek V4.1 Flash 39.5、C-tail Haiku Reasoning 16.9。
- 腳本變更：`recommend.py find_best` 加 exact-prefix 優先（`gpt 6 luna low` 誤錨 `gpt 5.6 luna low`；norm 把 5.6 拆成 5 6 所致；退回語義不變，v3 回歸驗過）。

## 腳本輸出 verbatim（compute_frontier）

```
# Frontier result (as-of run: `runs/2026-09-24-general-v4/candidates.csv`)
- min-score=39, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all
- Rule: merged single table (privacy display only); FREE rows never in numeric frontier.

## AA-Intelligence-Index @ AA-Intelligence-Index-v4.3 | basis=api (n=40)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 57.6 | Claude Opus 5.5 Adaptive Reasoning, Max Effort, Default Fallback AA-median Free | $5.98 | 9.6 | AA-median |  | highest-capability start of this bucket |
| 52.7 | GPT-6 Astra max AA-median Free | $3.26 | 16.2 | AA-median |  | CP new high +68.0%% at score step -4.90 |
| 52.4 | GPT-6 Astra xhigh AA-median Free | $2.31 | 22.7 | AA-median |  | same-tier (gap 0.30 < 2.0) CP takeover +40.3%% |
| 50.9 | GPT-6 Astra high AA-median Free | $1.73 | 29.5 | AA-median |  | same-tier (gap 1.80 < 2.0) CP takeover +30.0%% |
| 49.6 | GPT-6 Astra medium AA-median Free | $1.54 | 32.2 | AA-median |  | CP new high +9.1%% at score step -3.10 |
| 47.5 | GPT-6 Sol max AA-median Free | $1.06 | 45.0 | AA-median |  | CP new high +39.7%% at score step -2.10 |
| 45.8 | GPT-6 Astra low AA-median Free | $0.82 | 56.0 | AA-median |  | same-tier (gap 1.70 < 2.0) CP takeover +24.6%% |
| 45.1 | Muse Spark 1.3 xhigh Meta Contributor | $0.07 | 621.2 | Meta |  | CP new high +1008.8%% at score step -2.40 |

<details><summary>Dominated / excluded sample (32, top 5)</summary>

- Claude Fable 5.1 Adaptive Reasoning, Max Effort, Default Fallback AA-median Free (S=53.4, $7.63): CP no new high (7.00 <= best 9.63 x 1.05)
- Muse Spark 1.3 max AA-median Free (S=48.1, $1.60): CP no new high (29.97 <= best 32.20 x 1.05)
- Claude Fable 5.1 Adaptive Reasoning, Low Effort, Default Fallback AA-median Free (S=46.8, $2.37): CP no new high (19.74 <= best 44.96 x 1.05)
- Muse Spark 1.3 xhigh AA-median Free (S=45.1, $1.37): CP no new high (32.97 <= best 621.21 x 1.05)
- GLM-5.3 max AA-median Free (S=44.8, $2.01): CP no new high (22.34 <= best 621.21 x 1.05)
</details>

## FREE sidecar: none in this input.
```

## 腳本輸出 verbatim（recommend）

```
# Recommendation (official-chain three-pick; as-of run: `runs/2026-09-24-general-v4/candidates.csv`)
- min-score=39, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all (no-op), coding-floor=none
- Rule: frontier math by compute_frontier only; chain picks are display lookups (identity substring, ordered-token match); unmatched chain rung = 無AA分數→退回, never substituted; FREE rows excluded.

- band rule: band=[anchor-1*eps_score,+inf), pick=highest-CP in band (tie: higher score, then cheaper); picks exclude family [claude,opus,fable,sonnet,haiku] (math untouched); suppression top-down on CP only (upper CP >= lower CP -> lower 從缺).

## Group A daily-normal (General)
- 最適合 (chain head `gpt 6 astra high`；band [48.9,+inf), anchor GPT-6 Astra high AA-median Free（S=50.9, $1.73, CP=29.5, effort=high, GRADE-A）)：★ GPT-6 Astra medium AA-median Free（S=49.6, $1.54, CP=32.2, effort=medium, GRADE-A）
- 平衡 (chain mid `kimi k3 max`；band [41.6,+inf), anchor Kimi K3 max AA-median Free（S=43.6, $2.00, CP=21.8, effort=max, GRADE-A）)：★ Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）
- floor (chain tail `glm 5 3 max`；band [42.8,+inf), anchor GLM-5.3 max AA-median Free（S=44.8, $2.01, CP=22.3, effort=max, GRADE-A）)：從缺 (upper 平衡 CP 621.2 >= 本檔 CP 621.2；⚠ score diff +0 僅註記；本檔原 pick Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）)

## Group B geeky-normal+heavy (GPT)
- 最適合 (chain head `gpt 6 astra xhigh`；band [50.4,+inf), anchor GPT-6 Astra xhigh AA-median Free（S=52.4, $2.31, CP=22.7, effort=xhigh, GRADE-A）)：★ GPT-6 Astra high AA-median Free（S=50.9, $1.73, CP=29.5, effort=high, GRADE-A）
- 平衡 (chain mid `gpt 6 sol medium`；band [37.8,+inf), anchor GPT-6 Sol medium AA-median Free（S=39.8, $0.25, CP=160.4, effort=medium, GRADE-A）)：★ Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）
- floor (chain tail `gpt 6 sol medium`；band [37.8,+inf), anchor GPT-6 Sol medium AA-median Free（S=39.8, $0.25, CP=160.4, effort=medium, GRADE-A）)：從缺 (upper 平衡 CP 621.2 >= 本檔 CP 621.2；⚠ score diff +0 僅註記；本檔原 pick Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）)

## Group C quick+explore (輕量)
- 最適合 (chain head `kimi for coding highspeed off | gpt 6 luna fast low | gpt 6 luna low`；band [18.9,+inf), anchor GPT-6 Luna low AA-median Free（S=20.9, $0.00, CP=4644.4, effort=low, GRADE-A）)：★ Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）
- 平衡 (chain mid `deepseek flash`；band [37.5,+inf), anchor DeepSeek V4.1 Flash Reasoning, Max Effort AA-median Free（S=39.5, $0.27, CP=148.9, effort=Reasoning, Max Effort, GRADE-A）)：從缺 (upper 最適合 CP 621.2 >= 本檔 CP 621.2；⚠ score diff +0 僅註記；本檔原 pick Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）)
- floor：39.5（chain tail `` 無AA分數→退回 → fallback evidence bottom：DeepSeek V4.1 Flash Reasoning, Max Effort AA-median Free（S=39.5, $0.27, CP=148.9, effort=Reasoning, Max Effort, GRADE-A）；同 benchmark 同版本內最低可用實測行）

## Group D visual+writing (Claude專項)
- 最適合 (chain head `gpt 6 astra max`；band [50.7,+inf), anchor GPT-6 Astra max AA-median Free（S=52.7, $3.26, CP=16.2, effort=max, GRADE-A）)：★ GPT-6 Astra high AA-median Free（S=50.9, $1.73, CP=29.5, effort=high, GRADE-A）
- 平衡 (chain mid ``)：無AA分數→退回（本 input 無匹配行，不代入、不推定）
- floor：39.5（chain tail `gpt 5.5 terra max` 無AA分數→退回 → fallback evidence bottom：DeepSeek V4.1 Flash Reasoning, Max Effort AA-median Free（S=39.5, $0.27, CP=148.9, effort=Reasoning, Max Effort, GRADE-A）；同 benchmark 同版本內最低可用實測行）

A>=B check: skipped (--coding-floor not given).

FREE sidecar: 0 row(s), excluded from math.
Tier display: deprecated secondary output (hidden; pass --show-tiers to restore).
```
