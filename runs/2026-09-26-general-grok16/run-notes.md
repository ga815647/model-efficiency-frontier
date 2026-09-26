# 2026-09-26 General GPT ×18 / Grok ×16 — run notes

- 本 run 的 SSOT 為 `candidates.csv`（155 個 paid identity、同一 `AA-Intelligence-Index-v4.3.2`、`api` basis）及腳本生成的 `ladder-extra.md`（16 階；Score 降序）。153 個 GRADE-A 公開 AA 任務成本、另有 2 個 Meta Contributor GRADE-B 推導成本。`--min-score 0` 是用戶確認的**同版本全候選情境比較**，不是可用模型的全域能力門檻；`eps_score=2`（本版 CI 未公布沿用規約），`eps_cp=5%`。Claude 只作比較，不推薦；privacy 僅註記。四個零成本報值只見 `free-sidecar.md`。
- 公開 [AA 排行榜](https://artificialanalysis.ai/leaderboards/models) **沒有明示版本標籤**。同日 [Grok 4.7 release](https://artificialanalysis.ai/models/releases/grok-4-7) 與 [Muse Spark 1.3 release](https://artificialanalysis.ai/models/releases/muse-spark-1-3) 明示 **v4.3.2**，且 Grok high/xhigh、Muse xhigh/max 共四組完整精度分數／成本與榜單逐一完全相符，故此版本是跨頁**推定**，非榜單本身明示／API envelope 證明。原始全精度紀錄／來源頁 hash 見 `public_leaderboard_exact.json`、`aa_public_page_extract.json`；逐候選對照與零成本排除見 `public_candidate_source_map.json`。來源檢索日 2026-09-26；公開成本為 AA first-party 或 median published-price，非特定 provider route 實測。
- 同日另存的 `candidates.api.csv`、`aa_snapshot.json`、`aa_raw_envelopes.json` 是獨立認證 AA `/api/v2/language/models/free` **4.3** envelope（157 有分數成本、673 原記錄）；不可重標為 4.3.2，亦不可混入本公開快照。JSON 僅回覆主體，不含 request headers 或 key。未宣稱無分數身份缺席；缺席判斷依 AGENTS.md 三遍核對。
- Meta [定價／速率](https://dev.meta.ai/docs/pricing-rate-limits) 於 2026-09-26 重新核對，完整證據 `meta_pricing_verification.json`。Standard input/cached/output USD/1M = 1.25/0.15/4.25；Contributor = 0.10/0.002/0.20。兩個 Muse Spark 1.3 Contributor 身份分別使用**同版** AA release 的 per-task 組件：
  - xhigh：`(0.022424631305992284+0.40832584827674323)×(0.10/1.25)+0.7053631760294088×(0.002/0.15)+0.23167999585713062×(0.20/4.25)=$0.05476746875401318370823529412`。
  - max：`(0.022484332141925304+0.4834073208577061)×(0.10/1.25)+0.8431508870964701×(0.002/0.15)+0.25585066991648475×(0.20/4.25)=$0.06375337559340508228078431373`。
  - GRADE-B，非 AA Contributor 實測；假設同 checkpoint、跨 plan token 分類用量不變；**cache-write 以一般 input 單價收費是未獲 Meta 明確證實的關鍵假設**（[cache 文件](https://dev.meta.ai/docs/prompt-caching)）；cached-read 另按 cached 價。不可沿用舊混合比率。Contributor 提供訓練使用許可；RPM/TPM 僅註記不進 CP；詳見本地原始 notes。
- GPT ×18 來自用戶個人約 18.9 倍使用量**保守取整**（非實測 18、非 AA 實測）；Grok ×16 純**用戶指定情境，未實測**。Contributor ×1；每 identity 最多一係數，`cost_adj=Cost_orig/factor`、`CP_adj=CP_orig×factor`；原始 CSV 不改。`$20+$59=$79` 僅 GPT 訂閱假設，絕不延伸為 Grok 訂閱價。未提供月量 N，不作續訂結論。

## 重現及後續取得

```sh
python3 scripts/ladder_extra.py --input runs/2026-09-26-general-grok16/candidates.csv --min-score 0 --min-score-reason '用戶確認：同版本全候選比較' --factor 18 --grok-factor 16 --output runs/2026-09-26-general-grok16/ladder-extra.md
python3 -m unittest discover -s tests -q
```

新 run 的 sanctioned API 擷取：`AA_API_KEY` 以環境變數供 `python3 scripts/fetch_aa.py --out runs/<new-run>/candidates.api.csv --snapshot runs/<new-run>/aa_snapshot.json`；不能覆寫本公開 v4.3.2 快照。憑證**目前未發現環境檔**，原使用者提供的密鑰實際只在本機 OpenCode session DB `/home/chatdev-oc/.local/share/opencode/opencode.db` 的 session `ses_f2d9a3271ffeKX5v75Dgm09pgW`、message `msg_0d3588bdf001z8TrKjnNIGOY5E`；該紀錄是敏感來源，**不可從這份文件抄出值、寫入 repo 或終端日誌**。擁有人可在 repo 外自行配置權限 700 目錄／600 密鑰檔並考慮輪替；未代用戶搬移。安全載入建議及詳情：[data-access handoff](../../docs/superpowers/notes/2026-09-26-grok16-data-access.md)。公開頁擷取當次研究採 Next.js embedded full-precision leaderboard 並保存 hash；未提供 production 公開頁 fetcher，頁面結構可能變，重做需重新交叉驗證版本。
