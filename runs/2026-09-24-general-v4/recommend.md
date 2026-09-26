# Recommendation (official-chain three-pick; as-of run: `runs/2026-09-24-general-v4/candidates.csv`)
- min-score=0, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all (no-op), coding-floor=none
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
- 最適合 (chain head `kimi for coding highspeed off | gpt 6 luna fast low | gpt 6 luna low`；band [18.9,+inf), anchor GPT-6 Luna low AA-median Free（S=20.9, $0.00, CP=4644.4, effort=low, GRADE-A）)：★ GPT-6 Luna low AA-median Free（S=20.9, $0.00, CP=4644.4, effort=low, GRADE-A）
- 平衡 (chain mid `deepseek flash`；band [37.5,+inf), anchor DeepSeek V4.1 Flash Reasoning, Max Effort AA-median Free（S=39.5, $0.27, CP=148.9, effort=Reasoning, Max Effort, GRADE-A）)：從缺 (upper 最適合 CP 4644.4 >= 本檔 CP 621.2；⚠ score diff +24.2 僅註記；本檔原 pick Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）)
- floor：14（chain tail `` 無AA分數→退回 → fallback evidence bottom：Grok 4.3 Non-reasoning AA-median Free（S=14, $0.14, CP=101.9, effort=Non-reasoning, GRADE-A）；同 benchmark 同版本內最低可用實測行）

## Group D visual+writing (Claude專項)
- 最適合 (chain head `gpt 6 astra max`；band [50.7,+inf), anchor GPT-6 Astra max AA-median Free（S=52.7, $3.26, CP=16.2, effort=max, GRADE-A）)：★ GPT-6 Astra high AA-median Free（S=50.9, $1.73, CP=29.5, effort=high, GRADE-A）
- 平衡 (chain mid ``)：無AA分數→退回（本 input 無匹配行，不代入、不推定）
- floor：14（chain tail `gpt 5.5 terra max` 無AA分數→退回 → fallback evidence bottom：Grok 4.3 Non-reasoning AA-median Free（S=14, $0.14, CP=101.9, effort=Non-reasoning, GRADE-A）；同 benchmark 同版本內最低可用實測行）

A>=B check: skipped (--coding-floor not given).

FREE sidecar: 0 row(s), excluded from math.
Tier display: deprecated secondary output (hidden; pass --show-tiers to restore).
