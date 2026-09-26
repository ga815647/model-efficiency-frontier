# Frontier — Coding / AA Coding Agent Index v1.5 (2026-09-24) — merged single table：Opus 5.5 登頂，Flash 守門

- as-of: 2026-09-24 ｜ benchmark: Coding — AA Coding Agent Index v1.5 ｜ URL: https://artificialanalysis.ai/agents/coding-agents
- composition: DeepSWE v1.1（113 tasks）＋ Terminal-Bench 4.0（66 tasks）＋ SWE-Atlas-QnA（124 tasks）；303 tasks；equal-weight avg pass@1；methodology: https://artificialanalysis.ai/methodology/coding-agents-benchmarking/
- cost basis: api only（Average pay-per-token API cost per task，含 cache 折扣＋write charges；subscription 明確排除） ｜ min-score: 39（A 級證據下限：DeepSeek V4 Flash 39/$0.09 守門；禁令 6 門檻＋理由俱在） ｜ max-cost: 無 ｜ eps: score 2.0 / CP 5%
- eps 來源：Coding Index methodology 全文無 CI 公布（2026-09-24 確認）；按 eps 抓取規則沿用上一版 2.0＋本註記；eps_cp＝5% 固定
- 分級線（本版專用，換版重切；錨點＝Codex GPT-6 Luna max 41／CP 227.8，級距 7＝3.5×2.0）：T1 55+／T2 48–54／T3 41–47／T4 34–40／T5 33–
- privacy 註記 only (2026-09-24 取消分桶）
- script: scripts/compute_frontier.py --min-score 39 --eps-score 2.0 --privacy-mode all ｜ snapshot: runs/2026-09-24-coding/candidates.csv（frozen；18 行 (17A+1B) 合併計算）
- 計算：merged single frontier（privacy 僅註記，不分桶、不分開算、不混排以外的第二條線）

## TL;DR（merged single frontier，5 留）

- 66 Opus 5.5 max $13.04 起點 → 62 Astra max $7.47 → 57 Sol max $2.99（DeepSWE 69% 全 run 最高，效率中樞）→ 48.3 Spark xhigh Contributor **B** $0.18（CP 268.3；same-composite takeover：同 composite 48.3 接管 Standard $3.47 行）→ 39 DeepSeek Flash $0.09 守門（CP 433.3 全 run 峰值）。
- 被 Contributor 線壓制（合併後 dominated，直說）：DeepSeek Pro 43/$0.24、Luna 6 max 41/$0.18、Luna 5.6 max 43/$0.44、Spark Standard xhigh 48.3/$3.47、Spark Standard max 54.3/$3.98——同分或同 composite 下無 CP 新高，全被 Contributor 行（48.3/$0.18，CP 268.3）接管。
- B-caveat：Contributor 行為 GRADE-B 推導 cost（非 AA 實測）：公式 3.47 × 0.0414/0.78（AA Standard xhigh Cost to run × blended ratio；Standard $1.25/$4.25 blended $0.78；Contributor $0.10/$0.20）；假設：same 1.3 checkpoint（Meta models page）、7:2:1 proxy（true 1.33%–8% by cache/output mix）、xhigh 可推導（兩 tier 皆有）、max 不推導（Standard-only per Meta docs）；frontier 行標 B。
- B 組結論不變：Coding 側 Luna max 41 遠低於 Intelligence 側的統治地位，且 DeepSWE 墊底群證明便宜≠能幹活，實作另看一張表是對的。

## 能力分級 × 合併表（展示用；★ = frontier 成員；privacy 僅註記）

| 級別（本版） | 成員（privacy 註記） |
|---|---|
| T1 旗艦 55+ | Opus 5.5 max★ 66/$13.04（private-safe）；Fable 5.1 max-fb 62/$12.39（private-safe）；Astra max★ 62/$7.47（private-safe）；Devin Fusion 61.68/$7.90（other，複合 harness caveat，dominated）；Opus 5 max 60/$10.79（private-safe）；Sol 6 max★ 57/$2.99（private-safe）；Grok 4.7 xhigh 56.27/$8.82（other）；Sol 5.6 max 55/$6.35（private-safe） |
| T2 強 48–54 | Spark max 54.30/$3.98（other，合併後 dominated，被 Contributor 線壓制）；GLM-5.3 53.55/$4.24（other）；Kimi K3 51.93/$5.05（other）；Spark xhigh Contributor★ **B** 48.30/$0.18（other，same-composite 接管 Standard 行）；Spark xhigh Standard 48.30/$3.47（other，合併後 dominated，被 Contributor 同 composite 接管） |
| T3 主力 41–47 | DeepSeek Pro 43/$0.24（other，合併後 dominated，被 Contributor 線壓制）；Luna 5.6 max 43/$0.44（private-safe，合併後 dominated，被 Contributor 線壓制）；Qwen3.8 Max 43/$3.48（other）；Luna 6 max 41/$0.18（private-safe，合併後 dominated，被 Contributor 線壓制） |
| T4 輕量 34–40 | DeepSeek Flash★ 39/$0.09（other，守門行） |
| T5 門檻 33– | 從缺 |

註：速度註記：Coding 每任務 18–66 分鐘，全線只適離線批量（展示註記，不進數學）。Contributor RPM 100 / TPM 3M vs Standard 3000 / 4M——僅顯示，不進數學。

## Frontier（merged single table，18 進 → 5 留；privacy 僅註記）

| Score | Identity | $/task | CP | privacy註記 | 判決 |
|---|---|---|---|---|---|
| 66 | Claude Code Opus 5.5 max Anthropic API Standard | $13.04 | 5.1 | private-safe | 起點：Coding 最高實測分 |
| 62 | Codex GPT-6 Astra max OpenAI API Standard | $7.47 | 8.3 | private-safe | 新高 +64.0%（-4 分；同 62 比 Fable 便宜 40%） |
| 57 | Codex GPT-6 Sol max OpenAI API Standard | $2.99 | 19.1 | private-safe | 新高 +129.7%（-5 分；DeepSWE 69% 全 run 最高） |
| 48.3 | Muse Code Muse Spark 1.3 xhigh Meta Contributor **B** | $0.18 | 268.3 | other | 新高 +1307.6%（-8.7 分；same-composite 接管 Standard 行；B級推導） |
| 39 | Codex DeepSeek V4 Flash 0731 max DeepSeek API Standard | $0.09 | 433.3 | other | 新高 +61.5%（-9.3 分；守門行） |

## 淘汰與排除一覽（merged；privacy 僅註記，非分組）

### 演算淘汰（script 理由；合併表下 13 行 dominated）

| Identity | S | $/task | privacy註記 | 判決 |
|---|---|---|---|---|
| Devin Fusion CLI Fable 5.1 XHigh + SWE-2 Medium | 61.68 | $7.90 | other | dominated（複合 harness caveat：雙模型 Fable 5.1 XHigh＋SWE-2 Medium sidekick，$7.90 為混合 cost；合併表下無 CP 新高，只做歷史起點註記） |
| Fable 5.1 max-fb | 62 | $12.39 | private-safe | 同分更貴（CP 5.0 < 8.3；被 Astra max 接管） |
| Opus 5 max | 60 | $10.79 | private-safe | CP 無新高（5.6） |
| Grok 4.7 xhigh | 56.27 | $8.82 | other | CP 無新高（被 Sol max 線壓制；TB-v4 33.3 偏弱） |
| Sol 5.6 max | 55 | $6.35 | private-safe | CP 無新高（8.7 < 19.1；被 Sol 6 max 接管；live $6.35 取代 stale $6.58） |
| Spark max | 54.30 | $3.98 | other | 合併後 dominated（被 Contributor 線壓制，無 CP 新高） |
| GLM-5.3 | 53.55 | $4.24 | other | CP 無新高（被 Sol max 線壓制） |
| Kimi K3 | 51.93 | $5.05 | other | CP 無新高（TB-v4 21.2 偏弱） |
| Spark xhigh Standard | 48.30 | $3.47 | other | 合併後 dominated（same-composite 被 Contributor $0.18 接管） |
| DeepSeek Pro | 43 | $0.24 | other | 合併後 dominated（被 Contributor 線壓制，無 CP 新高） |
| Luna 6 max | 41 | $0.18 | private-safe | 合併後 dominated（被 Contributor 線壓制，無 CP 新高） |
| Luna 5.6 max | 43 | $0.44 | private-safe | 合併後掉出：被 Contributor 線壓制 |
| Qwen3.8 Max | 43 | $3.48 | other | 被 DeepSeek Pro 同分更便宜（$0.24）接管 |

### 方法排除（未進演算）

| 對象 | 原因 |
|---|---|
| Terra 77 系、Sol 80 / Luna 74.6 系、Astra $1.41→$4.72/62→67 | v1.1 或 TB v2.1 舊版，禁令 10 |
| Fable 5、Sonnet 5、Haiku 4.5、5.6 Terra、非 max efforts、Grok 4.6 | Coding leaderboard 無行，無 AA cost，GRADE-C 禁入 |
| Spark Contributor | 無 AA-measured Cost to run（僅 Standard 行）；rescale 為 GRADE-B 已做，見 TL;DR B-caveat；frontier 行標 B |
| GPT-6 Sol max 57/$2.99 的 stale 質疑 | 已用原文頁驗證為 live v1.5 值（69/43/58），採入；5.6 Sol $6.58 同理更新為 live $6.35 |

## 附錄

<details><summary>證據 / 來源</summary>

- leaderboard: https://artificialanalysis.ai/agents/coding-agents（v1.5；payload materialized 2026-09-24T02:35:53Z）
- 原文頁驗證（2026-09-24 fetch）：https://artificialanalysis.ai/agents/coding-agents/comparisons/claude-code-vs-codex（v1.5 表頭確認；Sol 6 max 57/$2.99、Astra max $7.47 取代 09-09 文章 $7.09、5.6 Sol max $6.35 取代 mirror $6.58）
- methodology: https://artificialanalysis.ai/methodology/coding-agents-benchmarking/（v1.5；303 tasks；stale /pt v1.4 mirror 忽略）
- privacy 註記（2026-09-24 取消分桶，不再分組）：OpenAI / Anthropic 沿用 General run 說法；Meta Standard→other（open-weight 不推定，禁令 3）；xAI/DeepSeek/Alibaba/Moonshot/Z.ai/Cognition 無聲明→other；僅註記，不進數學
- CI：Coding methodology 全文無 CI；eps 2.0 沿用＋註記

</details>

<details><summary>腳本輸出原文（verbatim）</summary>

```
# Frontier result (as-of run: `runs/2026-09-24-coding/candidates.csv`)
- min-score=39, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all
- Rule: merged single table (privacy display only); FREE rows never in numeric frontier.

## Coding @ AA-Coding-Agent-Index-v1.5 | basis=api (n=18)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 66 | Claude Code Opus 5.5 max Anthropic API Standard | $13.04 | 5.1 | Anthropic | private-safe | highest-capability start of this bucket |
| 62 | Codex GPT-6 Astra max OpenAI API Standard | $7.47 | 8.3 | OpenAI | private-safe | CP new high +64.0%% at score step -4.00 |
| 57 | Codex GPT-6 Sol max OpenAI API Standard | $2.99 | 19.1 | OpenAI | private-safe | CP new high +129.7%% at score step -5.00 |
| 48.3 | Muse Code Muse Spark 1.3 xhigh Meta Contributor | $0.18 | 268.3 | Meta | other | CP new high +1307.6%% at score step -8.70 |
| 39 | Codex DeepSeek V4 Flash 0731 max DeepSeek API Standard | $0.09 | 433.3 | DeepSeek | other | CP new high +61.5%% at score step -9.30 |
```

</details>
