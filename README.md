# Model Efficiency Frontier

AA Intelligence Index 的付費模型成本／能力快照與個人使用情境階梯。階梯以同一 benchmark 版本、API cost basis 的候選重算；`Cost_orig` 是 AA 每任務原價，`CP_adj` 是情境效率，**不是實際 API 折扣或 AA 實測成本**。政策及流程見 [AGENTS.md](AGENTS.md)。

最新結果：[2026-09-26 GPT ×18／Grok ×16 番外篇](runs/2026-09-26-general-grok16/ladder-extra.md)（16 階；155 個付費候選；4 個零成本報值另見 [sidecar](runs/2026-09-26-general-grok16/free-sidecar.md)）。[run notes](runs/2026-09-26-general-grok16/run-notes.md) 說明版本推定、GRADE-B 公式、資料來源與重現方式。舊 run 原樣封存。

結報方向已確認為 **Chat 對談＋按需單檔 HTML**，CI／HTML 尚待實作，不部署網站。Notion 已停止展示與同步，原頁已移到用戶的「垃圾桶」父頁，待用戶日後手动刪除。詳見 [Chat／CI 設計](docs/superpowers/specs/2026-09-26-chat-ci-design.md)。

在 repo 根目錄重新產出**同一快照**（不會抓資料）：

```sh
python3 scripts/ladder_extra.py --input runs/2026-09-26-general-grok16/candidates.csv --min-score 0 --min-score-reason '用戶確認：同版本全候選比較' --factor 18 --grok-factor 16 --output runs/2026-09-26-general-grok16/ladder-extra.md
```

新資料擷取與憑證取得／安全載入另見 [資料存取手記](docs/superpowers/notes/2026-09-26-grok16-data-access.md)；腳本使用環境變數 `AA_API_KEY`，絕不追蹤密鑰或將值輸出到命令、日誌與快照。認證 API 回覆版本 4.3 與此公開頁推定 4.3.2 快照**不可混用**。
