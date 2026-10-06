# 2026-10-06 公開前檢查

**結論：暫停 public 與公開部署，repo 保持 private。** 這是使用者指定「敏感或再散布問題無法確認時先停止公開」的門檻，安全的產品實作、測試、合併與固定快照重跑可繼續。

## 檢查範圍與結果

- 起始 main：`69a7aff6663034db9f20d6bf5413cab7487f6542`。完整 fetch 的 main、results、16 個 request branches 與 tags（當時無 tag），共 103 個可達 commit／1040 個可達 Git object；包含原始 sources、API 快照、失敗診斷及歷史報告。以 gitleaks v8.30.1、官方 archive checksum 核對後，`git --log-opts=--all --redact=100` 掃描，0 命中。沒有 `.env`、SSH private-key 或 credentials 命名的追蹤檔案。
- Actions 當時全部 16 runs，32 份可下載 logs、全部 11 個 report artifacts 已下載掃描；2 個 issues、0 個 issue／PR inline／commit comments、0 release，Discussions 未啟用。遠端內容 gitleaks 遮罩掃描 0 命中。CLI artifact redirect 不可用，改用已授權 GitHub connector 下載並掃描，沒有用缺失資料冒充通過。
- 未讀取平台保存的 secret 值、未列印 secret 或匯出未遮罩 finding。腳本中的環境變數名稱、dummy test tokens 與公開第三方 script 不是 token 值。掃描未命中不代表保證沒有一切敏感內容。
- 公開頁／Meta 文件／AA API 回應與個人情境註記均在既有歷史；完整公開會連同这些 bytes 一起開放，不能只檢查目前 main 或只排除網站輸出。

## 明確再散布阻擋

官方 [Artificial Analysis Terms of Use](https://artificialanalysis.ai/terms-of-use) §2.1 限制 personal, noncommercial use；§2.2(d) 明列：

> except as expressly stated herein, no part of the Site may be copied, reproduced, distributed, republished, downloaded, displayed, posted or transmitted in any form or by any means.

本庫所有可達歷史包含完整 AA leaderboard／release HTML 原頁，例如固定 publication `9bcabcee80ba3c2850dffc8df1c865afe6cf3cbb` 中 `results/834cf811-f1ca-467e-a72f-291fd0195f61/36703900975-1/snapshot/evidence/leaderboard.html`，以及歷史 `runs/` 原頁和 AA API 回應。沒有找到可驗證、允許本庫這些保存內容公開再散布的授權；不自行判定公開原頁等於允許再發布，不替第三方改授權，也不自行聯絡第三方。

解除本項所需最小資訊：可驗證的 AA 書面許可／適用授權，明確涵蓋歷史原頁、API 回應與衍生展示的公開散布。不是一般「繼續／同意公開」就能代表第三方授權。歷史不改寫、不 force push、不刪證據。

## GitHub 設定權限

repo metadata visibility 讀回 **private**，permissions.admin／push=true；實際 `GET /pages` 及 `GET /branches/main/protection` 回傳 **403 Resource not accessible by integration**。因此不將 metadata admin=true 當作 Pages 設定／branch protection 可用權限。未嘗試用其他身分繞過。公開門檻解除後，需具該 endpoint 權限的正常管理身分完成 `docs/deployment.md` 的 Pages source／environment 設定，然後讀回。

`PUBLICATION_REVIEW_PASSED` 尚未設 true；部署 job 強制同時要求 repo public，避免此阻擋未解除時自動公開。保留已成功網站的失敗保護可測試，但目前不存在可冒稱「上一版已上線」的網站。
