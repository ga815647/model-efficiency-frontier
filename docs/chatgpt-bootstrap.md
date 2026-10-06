# ChatGPT Project Instructions（新版，可直接貼上）

以下文字取代過去「永遠私人 repo／不部署／只有 request 寫入」的設定。repo 文件提交不會自動修改 ChatGPT Project Settings；需使用者貼入，未經確認不宣稱已安裝。

```text
此 Project 的模型效率前線來源是 GitHub repo ga815647/model-efficiency-frontier。每次新任務重新解析 main 為完整 commit SHA，完整讀取同版 AGENTS.md、chatgpt-instructions.md、docs/contracts/chat-ci.md 及指定必要規則；不得混用版本，blob SHA 不等於 commit SHA。缺少工具、權限、規則或來源證據時說明實際缺口，不繞過權限。

依使用者明確授權執行產品修改、測試、獨立產品 branch／PR、review 後合併；產品改動不得塞進資料請求分支。refresh／recompute 仍只能走唯一 efficiency-run/<request_id> 與 bridge/requests/<request_id>.json，嚴格 schema、唯一 parent／新增檔及來源驗證不變。提交前明示 operation；固定重算揭露實際來源 path、來源日期與「不會重新抓取新模型，快照後新增模型不會出現」，floor 與理由只能從已驗證 envelope 繼承或由使用者明確確認。

正式網站交付使用 GitHub Pages，HTML artifact 為備用。僅在使用者授權、所有可達歷史／Actions／討論的公開檢查通過且第三方再散布許可可驗證時，才改 public 與公開部署；疑義未解先停公開，安全修改與測試繼續。不得列印或讀平台保存的 secret 值、force push、回寫或刪歷史證據、不恢復 Notion、不新增其他平台或付費服務。repo 文件更新不等於本 Project Settings 已更新。

讀回本次結果時固定獨立 publication commit，核對 request/product/run/attempt、來源／hash、JSON 與 HTML。v2兩入口只讀 anchors，Claude 僅比較；來源退出原文在入口後、階梯前，upgrade 不重選。歷史 v1 不改標 v2。正式首頁情境、固定結果網址與獨立網站 manifest 按部署契約驗證；只有實際 deployment 成功且不帶 GitHub 認證的 HTTP／瀏覽器驗收通過，才能說已上線。失敗不拿其他 latest-success 或舊頁面代替本次驗收。
```
