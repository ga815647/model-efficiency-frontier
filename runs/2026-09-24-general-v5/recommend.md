# Recommendation (official-chain three-pick; as-of run: `runs/2026-09-24-general-v5/candidates.csv`)
- min-score=0, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all (no-op), coding-floor=none
- Rule: frontier math by compute_frontier only; chain picks are display lookups (identity substring, ordered-token match); unmatched chain rung = 無AA分數→退回, never substituted; FREE rows excluded.

- band rule: band=[anchor-1*eps_score,+inf), pick=highest-CP in band (tie: higher score, then cheaper); picks exclude family [claude,opus,fable,sonnet,haiku] (math untouched); suppression top-down on CP only (upper CP >= lower CP -> lower 從缺).

## Group daily-normal
- 最適合 (chain head `opus 5 5 medium`)：無AA分數→退回（本 input 無匹配行，不代入、不推定）
- 平衡 (chain mid `kimi k3 max`；band [41.6,+inf), anchor Kimi K3 max AA-median Free（S=43.6, $2.00, CP=21.8, effort=max, GRADE-A）)：★ Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）
- floor (chain tail `glm 5 3 max`；band [42.8,+inf), anchor GLM-5.3 max AA-median Free（S=44.8, $2.01, CP=22.3, effort=max, GRADE-A）)：從缺 (upper 平衡 CP 621.2 >= 本檔 CP 621.2；⚠ score diff +0 僅註記；本檔原 pick Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）)

## Group geeky-normal
- 最適合 (chain head `gpt 5 6 sol medium`；band [37.2,+inf), anchor GPT-5.6 Sol medium AA-median Free（S=39.2, $0.51, CP=77.6, effort=medium, GRADE-A）)：★ Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）
- 平衡 (chain mid ``)：無AA分數→退回（本 input 無匹配行，不代入、不推定）
- floor：14（chain tail `` 無AA分數→退回 → fallback evidence bottom：Grok 4.3 Non-reasoning AA-median Free（S=14, $0.14, CP=101.9, effort=Non-reasoning, GRADE-A）；同 benchmark 同版本內最低可用實測行）

## Group geeky-heavy
- 最適合 (chain head `gpt 6 astra xhigh`；band [50.4,+inf), anchor GPT-6 Astra xhigh AA-median Free（S=52.4, $2.31, CP=22.7, effort=xhigh, GRADE-A）)：★ GPT-6 Astra high AA-median Free（S=50.9, $1.73, CP=29.5, effort=high, GRADE-A）
- 平衡 (chain mid ``)：無AA分數→退回（本 input 無匹配行，不代入、不推定）
- floor：14（chain tail `` 無AA分數→退回 → fallback evidence bottom：Grok 4.3 Non-reasoning AA-median Free（S=14, $0.14, CP=101.9, effort=Non-reasoning, GRADE-A）；同 benchmark 同版本內最低可用實測行）

## Group explore
- 最適合 (chain head `kimi for coding highspeed off`)：無AA分數→退回（本 input 無匹配行，不代入、不推定）
- 平衡 (chain mid `gpt 6 luna fast low | gpt 6 luna low | deepseek flash | qwen3 7 plus | minimax m2 7`；band [23.2,+inf), anchor Qwen3.7 Plus Qwen3.7 Plus AA-median Free（S=25.2, $0.30, CP=85.4, effort=Qwen3.7 Plus, GRADE-A）)：★ GPT-6 Luna medium AA-median Free（S=29.5, $0.02, CP=1705.2, effort=medium, GRADE-A）
- floor (chain tail `haiku`；band [14.9,+inf), anchor Claude 4.5 Haiku Reasoning AA-median Free（S=16.9, $0.21, CP=81.4, effort=Reasoning, GRADE-A）)：20.9（band CP-best GPT-6 Luna low AA-median Free（S=20.9, $0.00, CP=4644.4, effort=low, GRADE-A））

## Group librarian
- 最適合 (chain head `kimi for coding highspeed off`)：無AA分數→退回（本 input 無匹配行，不代入、不推定）
- 平衡 (chain mid `gpt 6 luna fast low | gpt 6 luna low | deepseek flash | qwen3 7 plus | minimax m2 7`；band [23.2,+inf), anchor Qwen3.7 Plus Qwen3.7 Plus AA-median Free（S=25.2, $0.30, CP=85.4, effort=Qwen3.7 Plus, GRADE-A）)：★ GPT-6 Luna medium AA-median Free（S=29.5, $0.02, CP=1705.2, effort=medium, GRADE-A）
- floor (chain tail `haiku`；band [14.9,+inf), anchor Claude 4.5 Haiku Reasoning AA-median Free（S=16.9, $0.21, CP=81.4, effort=Reasoning, GRADE-A）)：20.9（band CP-best GPT-6 Luna low AA-median Free（S=20.9, $0.00, CP=4644.4, effort=low, GRADE-A））

## Group quick
- 最適合 (chain head `gpt 6 luna fast low | gpt 6 luna low`；band [18.9,+inf), anchor GPT-6 Luna low AA-median Free（S=20.9, $0.00, CP=4644.4, effort=low, GRADE-A）)：★ GPT-6 Luna low AA-median Free（S=20.9, $0.00, CP=4644.4, effort=low, GRADE-A）
- 平衡 (chain mid `deepseek flash`；band [37.5,+inf), anchor DeepSeek V4.1 Flash Reasoning, Max Effort AA-median Free（S=39.5, $0.27, CP=148.9, effort=Reasoning, Max Effort, GRADE-A）)：從缺 (upper 最適合 CP 4644.4 >= 本檔 CP 621.2；⚠ score diff +24.2 僅註記；本檔原 pick Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）)
- floor (chain tail `haiku`；band [14.9,+inf), anchor Claude 4.5 Haiku Reasoning AA-median Free（S=16.9, $0.21, CP=81.4, effort=Reasoning, GRADE-A）)：從缺 (upper 最適合 CP 4644.4 >= 本檔 CP 4644.4；⚠ score diff +0 僅註記；本檔原 pick GPT-6 Luna low AA-median Free（S=20.9, $0.00, CP=4644.4, effort=low, GRADE-A）)

## Group visual-engineering
- 最適合 (chain head `claude fable 5 1 max`；band [51.4,+inf), anchor Claude Fable 5.1 Adaptive Reasoning, Max Effort, Default Fallback AA-median Free（S=53.4, $7.63, CP=7.0, effort=Adaptive Reasoning, Max Effort, Default Fallback, GRADE-A）)：★ GPT-6 Astra xhigh AA-median Free（S=52.4, $2.31, CP=22.7, effort=xhigh, GRADE-A）
- 平衡 (chain mid `opus 5 5 max`；band [55.6,+inf), anchor Claude Opus 5.5 Adaptive Reasoning, Max Effort, Default Fallback AA-median Free（S=57.6, $5.98, CP=9.6, effort=Adaptive Reasoning, Max Effort, Default Fallback, GRADE-A）)：band 內無可用 pick（min/max-cost 或 family 排除後從缺）
- floor (chain tail `kimi k3 max`；band [41.6,+inf), anchor Kimi K3 max AA-median Free（S=43.6, $2.00, CP=21.8, effort=max, GRADE-A）)：45.1（band CP-best Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B））

## Group writing
- 最適合 (chain head `claude fable 5 1 low`；band [44.8,+inf), anchor Claude Fable 5.1 Adaptive Reasoning, Low Effort, Default Fallback AA-median Free（S=46.8, $2.37, CP=19.7, effort=Adaptive Reasoning, Low Effort, Default Fallback, GRADE-A）)：★ Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）
- 平衡 (chain mid `opus 5 5 low`；band [40.3,+inf), anchor Claude Opus 5.5 Adaptive Reasoning, Low Effort, Default Fallback AA-median Free（S=42.3, $0.55, CP=76.7, effort=Adaptive Reasoning, Low Effort, Default Fallback, GRADE-A）)：從缺 (upper 最適合 CP 621.2 >= 本檔 CP 621.2；⚠ score diff +0 僅註記；本檔原 pick Muse Spark 1.3 xhigh Meta Contributor（S=45.1, $0.07, CP=621.2, effort=xhigh, GRADE-B）)
- floor：14（chain tail `opus 4 6 max` 無AA分數→退回 → fallback evidence bottom：Grok 4.3 Non-reasoning AA-median Free（S=14, $0.14, CP=101.9, effort=Non-reasoning, GRADE-A）；同 benchmark 同版本內最低可用實測行）

A>=B check: skipped (--coding-floor not given).

FREE sidecar: 0 row(s), excluded from math.
Tier display: deprecated secondary output (hidden; pass --show-tiers to restore).
