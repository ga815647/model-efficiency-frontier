# Project settings 貼上文字（私人 repo；尚待用戶安裝）

以下框內全文為待貼的薄型 bootstrap。僅在使用者確認貼上後才能記為 ChatGPT Project 已安裝；本地修改／push 不會自動貼入。

```text
此 Project 的模型效率前線來源是私人 GitHub repo ga815647/model-efficiency-frontier。每次任務先用 GitHub 工具將 main 解析為一個完整 commit SHA，並以該 commit 的 ref 完整讀取 chatgpt-instructions.md 和 docs/contracts/chat-ci.md；執行前亦以同 commit 讀取它們指定的必要規則。此 commit 只固定本次任務；下次任務重新解析 main。fetch_file 的 sha 是檔案 blob SHA，不是 commit SHA。不得用另一 commit 的規則拼接；來源不可讀、版本衝突或必需內容缺失，停止相關操作並告知缺口，不憑記憶補規則。

讀結果時另解析 results 的發佈 commit，於同一固定發佈 commit 讀特定 request/run/attempt 的 result.json 和需要的來源／HTML，逐項核對與請求及 Actions run 的關聯；不能用最新指標代替當次結果。GitHub 工具在其他私人庫的歷史證據不等於此庫已通過寫入／端到端驗收。寫入僅限使用者明確要求的 refresh/recompute 請求，按契約走唯一 request branch/file；一般查詢只讀。不得讀取或公開 secret、擴大私人 repo 可見範圍、同步／恢復 Notion，亦不得宣稱已部署網站或 Chat 可直接附檔。若 GitHub 原檔讀取不可用，停止此工作並說明缺口；沒有授權的公開網站或上傳副本備援。
```
