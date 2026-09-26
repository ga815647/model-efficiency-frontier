# Chat → CI 驗收帳（2026-09-26）

| 能力 | 現有證據／狀態 | 待 Task 8 證據 |
| --- | --- | --- |
| 契約／完整指示／薄型 bootstrap | 已發佈至私人 `main` `16e9a2d8eae26d8bf191e8118f4841754f0c75ca`；OpenCode 已從本地審核內容及遠端 commit 身分核對，非目標 Chat 讀回 | Chat 在同一固定 product commit 完整讀回 |
| 私人遠端及 Git access | [ga815647/model-efficiency-frontier](https://github.com/ga815647/model-efficiency-frontier)：OpenCode 以 `ga815647` 建立；GitHub 回報 `isPrivate=true`、default=`main`，reviewed product commit 已推送 | 目標 Chat 私人庫讀／寫權限 |
| Chat 工具介面 | 使用者提供另一私人庫的讀取及 Actions GET 實測；建分支／建檔僅可見；本庫 OpenCode 經 `gh` Git write 實測但**不是 Chat connector 證明** | 本庫 Chat `create_branch`、`create_file`、push run、固定結果讀回 |
| Project settings | 上述 bootstrap 是草稿，未獲使用者確認貼上 | 用戶確認貼上與目標 Chat 同版讀取 |
| CI recompute／refresh／錯誤 | **OpenCode 遠端實測完成**：下列三個精確 push run；refresh 真正擷取公開來源且保存來源 hash，錯誤 run 紅燈不推進成功指標 | 目標 Chat 發起請求及讀回仍未驗證 |
| HTML／Notion／網站 | fresh [Actions artifact](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36259726459) 已下載，與固定 results commit 的 `report.html` 位元組一致；Notion 不同步，不部署網站 | Chat 直接附件能力未知，可用需授權的 artifact／Git HTML |

Task 7 dry exercise 與具體命令輸出記在 `.superpowers/sdd/2026-09-26-chat-ci/task-7-report.md`。這是本地契約驗證，不宣稱 Chat 端工具實際執行或 Project 安裝。既有 run 快照仍為資料來源；失敗不得回傳舊 picks。

## Task 8 遠端實測（OpenCode，非 Chat）

共同 product commit `16e9a2d8eae26d8bf191e8118f4841754f0c75ca`，全部為各自唯一 `efficiency-run/<request_id>` branch 的單一 JSON 新增提交，push event；`run_attempt=1`。固定 Git 發佈 commit 下讀回當次 result；GitHub Actions run `head_sha`、branch、run ID 與 envelope 的 request/product/run 身分已核對。

| 操作 | request ID／request commit | run | 固定發佈 commit／結果 |
| --- | --- | --- | --- |
| 歷史 recompute，`min_score=0`、GPT×18、Grok×16 | `2a1f7dee-9d4d-4f40-8ab7-a4fdaab7d4ee`／`c1c59dbabb884a08fdea4cf389fb4a24f5b924ce` | [36259676894，綠燈](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36259676894) | `edd41ee03d2979f44a4f3f49d931fe35bc4985b2`／`results/2a1f7dee-9d4d-4f40-8ab7-a4fdaab7d4ee/36259676894-1/result.json` |
| 故意非法 `gpt_factor=0` | `af09db61-1e70-4b65-a28f-afc3427ce479`／`11a37e75fd41069d4fe3da09077df263c651d3a0` | [36259725263，紅燈](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36259725263) | `d2c3e1ac93d442207fa5d9fae9a3baef36303fae`／`results/af09db61-1e70-4b65-a28f-afc3427ce479/36259725263-1/result.json`；`status=failed`、`invalid_range`，無成功 picks；與上一發佈 commit 的 `latest-success.json` 位元組相同 |
| 公開來源 fresh refresh，`min_score=0`、GPT×18、Grok×16 | `118b299c-bddd-4228-be1e-e7cd49403d77`／`710865a9173dd767c03d94c8e2a6a973a8ad0db1` | [36259726459，綠燈／HTML artifact](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36259726459) | `ba7911db85e5634f3853d90b9180a84a5cbf449b`／`results/118b299c-bddd-4228-be1e-e7cd49403d77/36259726459-1/result.json` |

歷史重算來源是固定 product commit 的 `runs/2026-09-26-general-grok16/candidates.csv`；結果為 155 行、16 階、9 個 Grok 狀態、2 個 Contributor（皆 GRADE-B、×1）；三 picks 為 GPT-6 Astra max／GPT-6 Sol high／GPT-6 Luna low。fresh 同為 155／16／9／2 及同三 picks，但**新取得**公開頁與 Meta 頁，不把重算冒充抓新數據。fresh CSV SHA-256 `4fd1d3323a49e862ba2103d338e4a3772673782f0c8756dcafde9efe9f2bfa40` 與 envelope 一致；155 行版號均 `AA-Intelligence-Index-v4.3.2`（`inferred`）且 cost basis=`api`。四個原頁 SHA-256 與 `sources.json` 相符；兩個 release 的四組交叉核對記在 `version.json`。Meta `meta_pricing.json` 記 Standard input/cached/output `1.25/0.15/4.25`、Contributor `0.10/0.002/0.20`（USD／百萬 token）、RPM/TPM 與訓練條款；兩行 Contributor 由當次同版用量組件換價，cache-write 以一般 input 計價是**未獲官方明示的假設**，非 AA 實測 Contributor 成本。`api_diagnostic.json` 為 `AA_API_KEY absent`／`not_collected`；不聲稱認證 API 取數。fresh artifact 下載後與該固定 commit 的 `report.html` byte-identical，非網站。

發佈排序按 `(source_dates, created_at, request_commit_sha)` 而非完成順序；這次 fresh 成功後 `latest-refresh.json` 指向 fresh，`latest-success.json` 仍指向先前 recompute（同日期／秒、request SHA 排序）；查當次結果必用上表的精確路徑，不能把 pointer 當成當次成功證明。Project bootstrap 仍需用戶安裝確認，目標 Chat connector 對新私人庫的 access、request 寫入、run 查詢及同一固定發佈 commit 的讀回尚待用戶提供實測；未達端到端 cutover。
