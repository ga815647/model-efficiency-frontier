# Recommendation — General v3 full-family / official-chain band picks (2026-09-24) — C-head/C-mid 真錨點落地

- as-of: 2026-09-24 ｜ benchmark: General — AA Intelligence Index v4.3（A/B/D 錨點組）＋ v4.3.2（C 新錨點＋A-tail 錨點證據組，分開算，禁令 10） ｜ URL: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3 ＋ release pages（見 frontier.md）＋ sweep /tmp/chain-sweep.md
- cost basis: api only ｜ min-score: 39 ｜ max-cost: 無 ｜ eps: score 2.0 / CP 5% ｜ band: [anchor − 1.0×eps_score, +inf) 單邊向下 ｜ picks exclude family [claude,opus,fable,sonnet,haiku]（數學不動，禁令 14）
- eps 來源：AA methodology 95% CI < ±1% re-confirmed 2026-09-24；eps_score = 2×CI = 2.0；eps_cp = 5% 固定
- privacy 註記 only (2026-09-24 取消分桶；欄位保留作註記，不分組不過濾）
- A>=B DELETED（2026-09-24 單一主線；Coding runs 歸檔保留、不刪除、不再開新 run、不再參與 picks；故未傳 --coding-floor，`A>=B check: skipped` 屬預期）
- tier rule（展示用；錨點＝v4.3 合併 frontier CP 峰值 Contributor 45／642.9，級距 7＝3.5×2.0）：T1 52+／T2 45–51／T3 38–44／T4 31–37／T5 30–
- script: scripts/recommend.py --min-score 39 --eps-score 2.0 --privacy-mode all --band-eps-mult 1.0 --exclude-family claude,opus,fable,sonnet,haiku（chain 覆寫見附錄命令；C-head 加 alias `gpt 6 luna low`，無腳本改動） ｜ snapshot: runs/2026-09-24-general-v3/candidates.csv（64 行）
- 版本分裂聲明：band anchor 允許引用 v4.3.2 實測（同系 live patch 錨點證據），但 floor 數字決策以錨點所在組為準；v4.3.2 行永不混入 v4.3 frontier 數學

## 三檔 picks（verbatim 見附錄；★ = 非 Claude 付費 pick）

- Group A：最適合 Astra medium 50/$1.54（head anchor Astra high 51，band [49,+inf)）；平衡 Contributor 45/$0.07[B]（mid anchor Kimi max 44，band [42,+inf)）；floor 從缺（tail anchor GLM-5.3 max 45 實測，band [43,+inf)；band CP-best 與平衡同值 → suppression；原 pick 註記保留）→ A floor 沿用 39
- Group B：最適合 Astra medium 50/$1.54；平衡 Contributor 45/$0.07[B]；floor 從缺（suppression，同上）→ B 無獨立 floor 數字（沿用約束 39）
- Group C：最適合 Contributor 45/$0.07[B]（head anchor Luna low 21 實測落地，band [19,+inf)；anchor ≠ pick 屬設計本意；Luna low 自身 CP 4666.7 雖更高但 S=21 < min-score 被門檻擋）；平衡從缺（mid anchor DeepSeek V4.1 Flash max 39 實測落地，band [37,+inf)；band CP-best 與 head 同值 → suppression）；floor 從缺（tail anchor Haiku reasoning 17，band [15,+inf)；同樣 suppression；原 pick 註記保留）→ C 無獨立 floor 數字（v2 的 floor 45 被 suppression 收回，屬規則正確執行：上檔 CP ≥ 下檔 CP）
- Group D：最適合 Astra high 51/$1.72（head anchor Astra max 53，band [51,+inf)）；平衡 `無AA分數→退回`（mid 空）；floor 45（tail anchor Terra max 42，band [40,+inf)；band CP-best Contributor 45/$0.07[B]）

## 附錄

<details><summary>腳本輸出原文（verbatim，recommend.py exit 0）</summary>

```
# Recommendation (official-chain three-pick; as-of run: `runs/2026-09-24-general-v3/candidates.csv`)
- min-score=39, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all (no-op), coding-floor=none
- Rule: frontier math by compute_frontier only; chain picks are display lookups (identity substring, ordered-token match); unmatched chain rung = 無AA分數→退回, never substituted; FREE rows excluded.

- band rule: band=[anchor-1*eps_score,+inf), pick=highest-CP in band (tie: higher score, then cheaper); picks exclude family [claude,opus,fable,sonnet,haiku] (math untouched); suppression top-down on CP only (upper CP >= lower CP -> lower 從缺).

## Group A daily-normal (General)
- 最適合 (chain head `gpt 6 astra high`；band [49,+inf), anchor GPT-6 Astra high OpenAI API Standard（S=51, $1.72, CP=29.7, effort=high, GRADE-A）)：★ GPT-6 Astra medium OpenAI API Standard（S=50, $1.54, CP=32.5, effort=medium, GRADE-A）
- 平衡 (chain mid `kimi k3 max`；band [42,+inf), anchor Kimi K3 max Kimi API Standard（S=44, $2.00, CP=22.0, effort=max, GRADE-A）)：★ Muse Spark 1.3 xhigh Meta Contributor（S=45, $0.07, CP=642.9, effort=xhigh, GRADE-B）
- floor (chain tail `glm 5 3 max`；band [43,+inf), anchor GLM-5.3 max Z.AI API Standard（S=45, $2.01, CP=22.4, effort=max, GRADE-A）)：從缺 (upper 平衡 CP 642.9 >= 本檔 CP 642.9；⚠ score diff +0 僅註記；本檔原 pick Muse Spark 1.3 xhigh Meta Contributor（S=45, $0.07, CP=642.9, effort=xhigh, GRADE-B）)

## Group B geeky-normal+heavy (GPT)
- 最適合 (chain head `gpt 6 astra xhigh`；band [50,+inf), anchor GPT-6 Astra xhigh OpenAI API Standard（S=52, $2.31, CP=22.5, effort=xhigh, GRADE-A）)：★ GPT-6 Astra medium OpenAI API Standard（S=50, $1.54, CP=32.5, effort=medium, GRADE-A）
- 平衡 (chain mid `gpt 6 sol medium`；band [38,+inf), anchor GPT-6 Sol medium OpenAI API Standard（S=40, $0.25, CP=160.0, effort=medium, GRADE-A）)：★ Muse Spark 1.3 xhigh Meta Contributor（S=45, $0.07, CP=642.9, effort=xhigh, GRADE-B）
- floor (chain tail `gpt 6 sol medium`；band [38,+inf), anchor GPT-6 Sol medium OpenAI API Standard（S=40, $0.25, CP=160.0, effort=medium, GRADE-A）)：從缺 (upper 平衡 CP 642.9 >= 本檔 CP 642.9；⚠ score diff +0 僅註記；本檔原 pick Muse Spark 1.3 xhigh Meta Contributor（S=45, $0.07, CP=642.9, effort=xhigh, GRADE-B）)

## Group C quick+explore (輕量)
- 最適合 (chain head `kimi for coding highspeed off | gpt 6 luna fast low | gpt 6 luna low`；band [19,+inf), anchor GPT-6 Luna low OpenAI API Standard（S=21, $0.00, CP=4666.7, effort=low, GRADE-A）)：★ Muse Spark 1.3 xhigh Meta Contributor（S=45, $0.07, CP=642.9, effort=xhigh, GRADE-B）
- 平衡 (chain mid `deepseek flash`；band [37,+inf), anchor DeepSeek V4.1 Flash max DeepSeek API Standard（S=39, $0.27, CP=144.4, effort=max, GRADE-A）)：從缺 (upper 最適合 CP 642.9 >= 本檔 CP 642.9；⚠ score diff +0 僅註記；本檔原 pick Muse Spark 1.3 xhigh Meta Contributor（S=45, $0.07, CP=642.9, effort=xhigh, GRADE-B）)
- floor (chain tail `claude haiku 4 5`；band [15,+inf), anchor Claude Haiku 4.5 reasoning Anthropic API Standard（S=17, $0.21, CP=81.0, effort=reasoning, GRADE-A）)：從缺 (upper 最適合 CP 642.9 >= 本檔 CP 642.9；⚠ score diff +0 僅註記；本檔原 pick Muse Spark 1.3 xhigh Meta Contributor（S=45, $0.07, CP=642.9, effort=xhigh, GRADE-B）)

## Group D visual+writing (Claude專項)
- 最適合 (chain head `gpt 6 astra max`；band [51,+inf), anchor GPT-6 Astra max OpenAI API Standard（S=53, $3.26, CP=16.3, effort=max, GRADE-A）)：★ GPT-6 Astra high OpenAI API Standard（S=51, $1.72, CP=29.7, effort=high, GRADE-A）
- 平衡 (chain mid ``)：無AA分數→退回（本 input 無匹配行，不代入、不推定）
- floor (chain tail `gpt 6 terra max`；band [40,+inf), anchor GPT-5.6 Terra max OpenAI API Standard（S=42, $1.40, CP=30.0, effort=max, GRADE-A))：45（band CP-best Muse Spark 1.3 xhigh Meta Contributor（S=45, $0.07, CP=642.9, effort=xhigh, GRADE-B））

A>=B check: skipped (--coding-floor not given).

FREE sidecar: 0 row(s), excluded from math.
Tier display: deprecated secondary output (hidden; pass --show-tiers to restore).
```

</details>

<details><summary>執行命令（repro）</summary>

```
python3 scripts/recommend.py --input runs/2026-09-24-general-v3/candidates.csv --min-score 39 --eps-score 2.0 --privacy-mode all --band-eps-mult 1.0 --exclude-family claude,opus,fable,sonnet,haiku --group-name "A daily-normal (General),B geeky-normal+heavy (GPT),C quick+explore (輕量),D visual+writing (Claude專項)" --chain-head "gpt 6 astra high,gpt 6 astra xhigh,kimi for coding highspeed off | gpt 6 luna fast low | gpt 6 luna low,gpt 6 astra max" --chain-mid "kimi k3 max,gpt 6 sol medium,deepseek flash," --chain-tail "glm 5 3 max,gpt 6 sol medium,claude haiku 4 5,gpt 6 terra max"
```

註：C-head 加 alias `gpt 6 luna low`（fast=strip suffix 到 base effort；luna-fast 本體仍無 AA ID、不代入）；C-mid `deepseek flash` 命中 DeepSeek V4.1 Flash max（ordered-token match；V4.1 Flash vs V4 Flash 0731 為不同 ID，General 側僅前者，Coding 側僅後者，各守本側）；D-mid 空＝D 無 mid rung，維持退回。

</details>
