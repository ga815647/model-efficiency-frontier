# Chat → CI 驗收帳（2026-09-26）

| 能力 | 現有證據／狀態 | 待 Task 8 證據 |
| --- | --- | --- |
| 本地契約／完整指示／薄型 bootstrap | Task 7 本地檔，尚未發布 | 固定 product commit 完整讀回 |
| 私人遠端及 Git access | `ga815647/model-efficiency-frontier` 用戶批准名稱，尚未由此工作建立 | URL、private/main、Chat 讀／寫權限 |
| Chat 工具介面 | 使用者提供另一私人庫的讀取及 Actions GET 實測；建分支／建檔僅可見；見 `docs/superpowers/notes/2026-09-26-chat-ci-capability.md` 與全域 connectors.md | 本庫 create_branch、create_file、push run、結果固定 commit 完整讀回 |
| Project settings | 上述 bootstrap 是草稿，未獲使用者確認貼上 | 用戶確認貼上與目標 Chat 同版讀取 |
| CI recompute／refresh／錯誤 | 本地單測與 dry exercise 不等於遠端 Actions | 真實 run、來源證據、失敗紅燈、同版固定結果 |
| HTML／Notion／網站 | 本地固定模板；Notion 已搬至用戶垃圾桶父頁並停止日常同步；不部署站 | Actions artifact 與 Git HTML 下載驗證；Chat 附件能力仍未知 |

Task 7 dry exercise 與具體命令輸出記在 `.superpowers/sdd/2026-09-26-chat-ci/task-7-report.md`。這是本地契約驗證，不宣稱 Chat 端工具實際執行或 Project 安裝。既有 run 快照仍為資料來源；失敗不得回傳舊 picks。
