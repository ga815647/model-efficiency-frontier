# Chat → CI 能力查證（2026-09-26）

狀態：官方工具能力已查證；使用者 ChatGPT Project 的工具可見性、呼叫與業務鏈路尚未驗證。不是部署完成紀錄。

## 使用者方向

Chat 作日常對談與觸發入口，CI 執行取數／計算／驗證，Git 保存資料、證據與結果；文件定義輸出格式供 Chat 直接呈現。不要另做日常手動版。目標是讓 Notion 退出日常展示；現有展示尚未停用。

## 已查證

- 本地 `git status --short --branch` 為乾淨 main，`git remote -v` 無輸出；尚無已綁定遠端。
- 本次 OpenCode 工具目錄未提供 GitHub workflow 工具；不能代表另一端 ChatGPT 的工具清單。
- 本機 connectors.md 是 2026-09-22 另一專案的 Neon／Function 紀錄，不是本專案 Chat→GitHub 權限證據。
- GitHub 官方 MCP README 提供 `actions_run_trigger`，`method=run_workflow`，參數 owner、repo、workflow_id、ref、inputs；另有 `actions_list`、`actions_get` 可查 workflow/run，以及 repository 讀檔能力。
- 官方 MCP 預設 toolsets 是 context、repos、issues、pull_requests、users，**不含 actions**。因此連上 GitHub 不自動證明可觸發 CI。
- 官方 remote server 有 actions toolset endpoint `https://api.githubcopilot.com/mcp/x/actions`，以及 all endpoint；要兼具讀檔及 Actions，需要相應 tools/toolsets，而不是只具 Actions 或 readonly。

來源（查閱 main 分支，非固定發行版本）：
- https://github.com/github/github-mcp-server/blob/main/README.md
- https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md

## 下一個必要證據：Chat 端工具探測

讓目標 ChatGPT Project 列出實際可用的 GitHub 工具名稱與參數，確認：
1. 可讀指定 owner/repo/path/ref 的完整原檔及解析 commit。
2. 可觸發 workflow_dispatch（例如 actions_run_trigger / run_workflow，或等價工具）。
3. 可列出／查詢 workflow runs，讀取該次執行結果。

這一步只列工具，不觸發其他專案的 workflow、不建立測試資源。使用者帶回輸出後標為「使用者提供的 ChatGPT 端證據」；工具可見不等於實際 dispatch 成功。

之後在本專案遠端與 workflow 建立後，才驗證 dispatch → 精確 run 識別 → CI 成功 → 結果 commit 同版讀取。不要用「最新一筆 run」當作這次請求的唯一關聯；需要 request ID／run ID 對應。背景完成通知能力另外驗證。

## 待設計／安裝

### 後續證據：既有 push bridge

使用者提供的 ChatGPT 端證據（2026-09-26，另一私人庫 ga815647/ziping）：fetch_file 以固定 commit 讀檔成功、GET commits/ref 解析 commit 成功、GET Actions runs 與單一 run 成功；沒有 workflow_dispatch 或任意 REST POST 工具。fetch_file 的 sha 是 blob SHA，不是 commit SHA。這不能證明本專案庫可讀寫。

OpenCode 另外以 gh 唯讀取得 ziping 的 `.github/workflows/chatgpt-execution-bridge.yml` 與 `bridge/README.md`。現有 bridge 定義由 `mingli-run/**` branch 上 `bridge/requests/*.json` 的 push 觸發；Chat 建立 request branch 並提交 JSON，CI 執行後將結果寫入 issue/comments。README 明訂 request_id + request_commit_sha 關聯，並非 workflow_dispatch。

來源：https://github.com/ga815647/ziping/blob/main/bridge/README.md 與同庫上述 workflow。這是既有實作的直接讀取證據，不等於本輪 Chat 已成功提交請求；使用者回報的 run 34123141204 為 event=push、conclusion=success，未單憑此推定觸發者就是 Chat。

建議沿用 request-commit → push CI 的傳輸模式，不改成手動操作。新專案的業務輸入、資料版本和結果保存仍須獨立設計，不複製四柱領域規則。

### 第二次 Chat 工具回報

使用者提供的 ChatGPT 端證據（2026-09-26）：只檢查工具與唯讀 workflow，沒有執行寫入。

- `mcp__GitHub__create_branch(repository_full_name, branch_name, sha)` 可指定來源 commit；sha 與 base_ref 二選一。回應只有 result.branch，可另外 GET 分支 HEAD 驗證。
- `mcp__GitHub__create_file(repository_full_name, path, content, message, branch)` 接受 UTF-8 字串，回應 result.commit_sha；適合每次唯一 request ID 的新路徑，不需要反覆更新固定檔案。
- 工具介面足以組成 request branch → JSON commit → push Actions；狀態是「工具可見」，不是「本專案寫入成功」或「端到端驗收成功」。
- 使用者另回報 cheap-flight-radar 也採固定 control branch + JSON push 的模式，並保留 dispatch；本輪 OpenCode 未自行查證該庫，不跨專案推定權限。

架構設計階段：使用者已要求 Chat 作入口、CI 執行、Git 記錄、結果直接對談；待確認具體設計與遠端定位。優先提案每請求一個唯一分支／JSON，避免固定 control branch 的並發覆寫；結果存 Git 的 request-scoped 路徑，供現已實測的固定 commit 讀檔能力使用。正式 spec 尚未批准，尚未實作。

- 遠端 owner/repo 與可見性確認；提案為 ga815647/model-efficiency-frontier 私人庫，尚未建立或發布。
- CI 的 fresh/recompute 輸入與結果契約、資料來源版本處理、Contributor 核價流程。
- Git 完整 Chat instructions 與 Project 薄型 bootstrap；尚未建立、貼上或驗收。
- 機器可讀結果及 Markdown 階梯從同一次計算生成；Chat 只解讀，不另算 picks。
- Notion 在 Chat→CI→結果讀回驗收後退出日常同步，舊頁保留為歷史。

## 通用 skill 補強評估結果

2026-09-26：依使用者同意，對未修改的 chatgpt-project-sync 做五個 fresh-session 假設情境測試，涵蓋缺 dispatch 但有 push bridge、工具可見與跨端證據分層、按業務能力盤點、各種 SHA／run 關聯、部分證據與授權邊界。五個情境皆符合預期，未觀察到需要新增規則的 baseline failure，因此沒有修改 skill；無 post-edit green、無 skill commit/push，也未安裝或驗證 ChatGPT Project settings。

測試是情境應用檢查，不是每一情境五次重複的統計比較，也不能證明所有未來情境均會遵循。完整 prompts／逐字輸出／評估暫存於 `/tmp/opencode/chat-sync-skill-tests/`。本輪結論是保留既有 skill，具體傳輸契約留在本專案規格；先前建議補強並未直接視為必須改寫。

### 更正：跨 session 可發現性缺口與修復

使用者指出：前述測試把情境帶給代理，沒有測到下一個專案能否找到本輪能力紀錄。新測試限制 fresh-session 只從已安裝 sync skill、全域 connectors.md 及其相關連結開始找；不直接提供本專案筆記。

- RED（ses_f219551e8ffe3as1u3u6Ma07L3）：原紀錄只有 Neon／Function，代理回覆「沒有找到上次 GitHub 能力探測的紀錄」，需要再向使用者詢問紀錄位置。證實跨專案檢索缺口，並非 push bridge 推理能力不足。
- 修復：在 `/home/chatdev-oc/.config/opencode/connectors.md` 新增帶日期的 Chat GitHub 工具／參數／證據等級表與本文件定位，保留其他服務紀錄；已安裝 `chatgpt-project-sync/SKILL.md` 改為先讀紀錄，要求將使用者回報持久化，新增 session/repo 不單獨觸發重驗，只補 access／授權／本案端到端缺口。缺 dispatch 先查 push bridge；具體私人 repo 仍只在私人紀錄。
- GREEN（ses_f219475d9ffeEUn4AYQD5UqCXE）：相同 fresh-session 任務找到五項具體工具／參數，正確區分讀取實測與写入工具可見，回覆「不必再貼一輪 GitHub 工具探測」；只詢問該新專案的定位與寫入授權。這個測試的新專案定位刻意未提供；本專案定位／設計授權已記錄，不再重問。

此結果取代上節「不改 skill」決定。屬一次跨 session 檢索回歸測試，不是五次重複統計測試；沒有執行任何 GitHub 寫入，也不代表 ChatGPT settings 已安裝。Skill 及全域 connector 檔案在 repo 外、非 Git 管理；本專案保存變更摘要與測試證據。
