# Model Efficiency Frontier

**2026-10-07 能力與成本平衡推薦**：以本次選定標竿 − 容許倍數×score EPS 為共同能力門檻，達標的完整可用候選中選 CP_adj 最高；更高分可參選，四家無候選從缺。網站上方依序顯示能力最高、能力與成本平衡、情境成本最低；四家平衡摘要列出分數與每任務情境成本。同一模型可同時符合多個推薦方向。標竿／容許值逐次選擇並綁精確結果，與原客觀 LADDER 並列。這是個人容許分差，不是 AA 統計誤差；[操作與驗收契約](docs/personal-cp.md)。

**2026-10-07 產品發布與重跑修正**：正式 Pages 除成功計算外，也在同庫 main 的 Product CI（push）通過後自動建置部署；PR、fork、失敗或已落後 main 的 CI 不可觸發產品發布，產品 checkout 固定為通過 CI 的完整 SHA。Chat execution 仍核對獨立 request/run/attempt，產品 CI 不冒充新計算。build 產生 `github-pages-<run_id>-<build_attempt>` 名稱並以 job output 傳給官方 upload/deploy action；只重跑 deploy 仍使用成功 build 的原 artifact，重跑 build 則產生新名稱，避免同名歧義及 attempt 漂移；不刪舊 artifacts 或歷史證據。deploy 前另以 contents:read 讀回 main／results refs，必須等於成功 build 固定的產品／results tip；較舊 artifact 不可透過 deploy-only 重跑蓋掉新產品或結果。所有來源／結果驗證、其餘最小權限及正式情境門檻維持。

**2026-10-07 最新來源退出呈現政策（優先於下方較早位置規則）**：依使用者要求，網站與新產生的 HTML 將完整「本次來源退出」清單原樣放在全部供應商頁的最後、計算與來源之後；四家供應商分頁不重複整批清單，也不在計算展開區重複。單一模型的缺值／退出狀態及來源理由仍保留，成功 JSON caveats、原始證據與已保存的歷史報告不改寫；無退出不造空區。此為展示更新，不變更算法、倍率或資料來源。

**2026-10-07 公開與部署現況（本節優先於下方較早狀態）**：使用者最新明確確認「repo 和 page 都改 public，Artificial Analysis token 不會被公開就好」，並已完成管理設定。本庫 visibility 已讀回 public；Pages Source 為 GitHub Actions，`github-pages` environment 只允許 main，正式部署開關已由成功 configure/deploy 實證生效。[正式首頁](https://ga815647.github.io/model-efficiency-frontier/) 匿名 HTTP 200；[Pages run 37565960035-1](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37565960035) build/deploy 均成功，deployment `6900788565` success。正式結果為 request `680ad45c-3818-4fbd-809e-59b3a68117ff`／run `37564382191-1`，結果 publication `f4d85b7ab0c939b2770b6d79a26a85f52bc8a960`，來源日期 2026-10-07、固定快照 recompute，不是新抓來源。四家倍率 ChatGPT17／Gemini3.6／Claude40／Grok5.2、新 v4 Claude 可推薦；下方舊倍率、僅比較及 private／未部署描述保留歷史身份。AA_API_KEY 仍只由 server-side Actions Secrets 注入，不放 repository variables、來源檔、網站或瀏覽器；不得讀保存的 secret 值。第三方條款的歷史發現保留，使用者確認不冒稱第三方授權。完整固定網址、雜湊、公開驗收見 `docs/acceptance/2026-10-07-public-pages.md`。Git 文件更新不代表 ChatGPT Project Settings 已更新。

**2026-10-07 最新供應商政策（優先於下方較早版本）**：使用者明確移除Claude僅比較限制；新request v3產生result v4，七欄parameters不變，成功結果新增精確`eligibility_policy=all-providers-v1`，四家皆可進混排推薦與upgrade。固定CP／視窗／EPS數學不變，歷史result v1/v2/v3保留原Claude資格，不改寫或改標。網站提供ChatGPT、Gemini、Claude、Grok各自重新選出的模型與effort階梯，從完整已驗證候選做同算法計算，另存獨立provider-ladder view與manifest/hash；首頁正式情境要求v4。沒有effort篩選選單，不在瀏覽器計算。詳見`docs/provider-ladders.md`。公開／部署阻擋仍未解除。

**2026-10-07 倍率與兩種 Chat 操作增量（優先於下方舊倍率／schema敘述）**：Chat 可研究並回填 repo 的倍率表，也可依保存倍率產生 LADDER。單一表 `bridge/site-policy.json`：約US$100/月的ChatGPT Pro ×17、Gemini訂閱 ×3.6、Claude訂閱 ×40（仍僅比較）、Grok ×5.2，Contributor×1。本次四個倍率由使用者提供統一方法論並指定，方案／推導／區間／信心見 `docs/subscription-factors.md` 與研究筆記；尚未獨立證實的引用照實標示，不冒稱研究驗證；證據、日期與限制同步保存。更新表走產品 branch／PR；產生新LADDER走唯一 request bridge。新 request v2／result v3 承載七欄參數，歷史 request v1／result v1/v2 的精確欄位與原義保留，算法與原始來源不改。完整流程及schema見 [倍率操作契約](docs/subscription-factors.md)，本檔及該契約須同commit讀取。公開／Pages門檻仍未解除，不能將建置成功稱為上線。

**10/6 實作與重跑已完成：** [PR #3](https://github.com/ga815647/model-efficiency-frontier/pull/3) 已合併，產品 `1f487a2bddf121acfe3d24993edc2fe2cc8b7b43`；295 項測試、獨立 review 與產品 CI 通過。新固定快照 recompute [37501847653-1](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37501847653) 成功，publication `c3cd3307b956b776334a4668c62b6580a80f864e`。自動 Pages build [37501895642-1](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37501895642) 成功，**deploy job skipped、repo 仍 private、沒有已上線網址**；來源為 2026-09-30，不是新抓來源。詳見本次驗收紀錄。

**模型怎麼選：先看「推薦中能力最高」與「推薦中情境成本最低」，再看推薦階梯。** 新介面採繁體中文、手機卡片／桌面精簡表格，可依名稱與 effort 搜尋，完整稽核與證據放在展開區；HTML 仍可離線開啟。正式交付政策改為 GitHub Pages，HTML artifact 為備用。**目前 repo 仍 private，公開與 Pages 部署受 AA 再散布條款阻擋；沒有已驗證上線網址。** 不能把本地預覽或 Pages artifact 說成網站已上線。

- [網站部署與驗證契約](docs/deployment.md)
- [公開前檢查與阻擋](docs/publication-review.md)
- [新版 ChatGPT Project Instructions（須由使用者貼入 Settings）](docs/chatgpt-bootstrap.md)
- [本次實作與重跑驗收](docs/acceptance/2026-10-06-pages.md)

正式首頁情境固定在 `bridge/site-policy.json`，從 9/30 最新成功 refresh 的固定 envelope 繼承 GPT ×18、Grok ×16、min_score=0、理由「同版本全候選情境比較」、max_cost=null。首頁與固定結果頁共用已驗證 JSON，不在瀏覽器抓價或計算推薦。選型算法與既有 request/result schema 不變；歷史 v1、CSV、原始來源及報告不回寫。

以下保留各日期歷史交付與驗收紀錄；其中「不部署網站／私人 repo／bootstrap 不改」不是 10/6 新任務的限制，過去 HTML 驗收不改標成當時已部署。

**9/30 來源對帳修復已發布，真實fresh與固定重算均成功。** 產品 `c68f3de` 經最終修正再覆核通過，已非force發布main並讀回；279tests及75保護物件通過。OpenCode [live refresh](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36698853013) 取得9/30來源：[固定報表](https://github.com/ga815647/model-efficiency-frontier/blob/0d4a7b8962515930f1ddcf9340c409b83cf5b335/results/c6d618b9-98d5-46b7-a933-58334aed4944/36698853013-1/report.md) 為105付費候選／15chain／9final（2 Claude僅比較、7非Claude），两入口Sol6.1 xhigh／Luna low。[固定新來源重算](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36699959889) 同樣通過，HTML artifacts各與固定Git bytes一致，latest-refresh保持原刷新。完整三SHA／來源／hash見 [9/30驗收帳](docs/superpowers/notes/2026-09-30-refresh-reconciliation-acceptance.md)。MiniMax-M2.7當次 `deprecated=true` 退出排行及強制追蹤；Inkling缺task cost明示排除、仍追蹤，不沿用舊價、不擋其他有效候選。issue #2 pre-write路由已發布，另有10/10離線consumer GREEN及獨立覆核；新版目標Chat實測及settings安裝仍獨立，bootstrap不改、無需因本次Git更新重貼。

**歷史9/27 v2驗收：雲端重算成功，當時fresh因来源缺價失敗。** 產品 `575f78fbdb8acc0c2ec5c2490cd08a503f8aace2` 已發布main並讀回，229項本地測試通過。[v2重算run](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36341140428) 的10階結果、兩入口及HTML artifact已關聯核對；[refresh run](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36341142058) 保存Inkling／MiniMax-M2.7缺task-cost診斷並維持failed，未推進成功pointer，非產品回歸。此失敗不改寫成9/30成功；完整定位見 [v2驗收帳](docs/superpowers/notes/2026-09-27-window-knee-acceptance.md)。下方16階連結是歷史 v1 證據。

新 Chat CI 計算使用 **CP-new-high → 全 family 混排的固定2分視窗精簡**，無最高分保送。只從 final 非Claude行取「最強保留檔」與「最低情境成本保留檔」兩入口；可相同，無符合行時從缺。Claude僅比較，cut指向最終代表並附trace；非Claude相鄰保留檔附升級分差、成本倍率及成本差。GRADE-B照常參戰，另列去除全部B後A行保留變化，非單一B因果證明。硬2分邊界、缺窗中性0及逐次選擇仍可能跳變。

請求仍 `schema_version=1`，新結果為v2；合法v1結果仍按舊三picks語義讀取，不手推成v2、不自動重算。新成功結果位置為 `results/<request_id>/<run_id>-<attempt>/{result.json,report.md,report.html}`；[歷史固定v2報表](https://github.com/ga815647/model-efficiency-frontier/blob/912e9e1df03a2e9d829d6a5c5d06b67d0e1a8a3d/results/04fce363-c20c-4832-bd34-dc0117239ff4/36341140428-1/report.md) 為9/26固定快照的雲端重算：155稽核行、154可用身份、19個CP鏈點、10個保留檔，兩入口為Astra xhigh／Luna low；此固定控制不變，不套用9/30 fresh。此次OpenCode驗收不冒充新的Chat端實測。Git指示已發布，沿用原Project bootstrap，不需因本次改制重貼；settings安裝狀態仍獨立確認。

> **9/27 身份更正：**歷史155行快照及先前試版含不可用的 **Muse Spark 1.3 Contributor max**；官方max僅限Standard。引用舊輸出須附 [更正說明](docs/superpowers/notes/2026-09-27-contributor-effort-correction.md)，選型須排除該行後重算整條鏈。

身份修復已發布並通過 [雲端重算驗收](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36294948064)（16階；HTML可由該run下載）。[固定更正報表](https://github.com/ga815647/model-efficiency-frontier/blob/bbb5fadaf04633aae0e6849f9fbb74924a5040ad/results/95a3ddbc-5d8d-4985-9c6d-1a73c251e0f4/36294948064-1/report.md)是9/26歷史輸入的修正重算；即時fresh仍受兩個task-cost缺值阻擋。

AA Intelligence Index 的付費模型成本／能力快照與個人使用情境階梯。階梯以同一 benchmark 版本、API cost basis 的候選重算；`Cost_orig` 是 AA 每任務原價，`CP_adj` 是情境效率，**不是實際 API 折扣或 AA 實測成本**。政策及流程見 [AGENTS.md](AGENTS.md)。

歷史封存：[2026-09-26 GPT ×18／Grok ×16 番外篇](runs/2026-09-26-general-grok16/ladder-extra.md)（16 階；155 個付費候選；4 個零成本報值另見 [sidecar](runs/2026-09-26-general-grok16/free-sidecar.md)）。[run notes](runs/2026-09-26-general-grok16/run-notes.md) 說明版本推定、GRADE-B 公式、資料來源與重現方式。舊 run 原樣封存。

9/27 另做 [升級代價試版](experiments/2026-09-27-tradeoffs/README.md)（[單檔 HTML](experiments/2026-09-27-tradeoffs/report.html)）：同一 9/26 快照的 155 候選留下 21 個 Score／Cost_adj 取捨點，逐階列分數增加、成本倍率與差額；2 分只作註記／折疊。此為試看用比較，不取代上方正式階梯。

結報方向已確認為 **Chat 對談＋按需單檔 HTML**，不部署網站。私人 [GitHub repo](https://github.com/ga815647/model-efficiency-frontier) 的 `main` 已有 Chat → CI 實作，遠端 Actions 已驗證歷史重算、fresh 公開取數、失敗路徑與 HTML artifact。**9/27 目標 Chat 的請求提交、run 查詢及成功／失敗讀回也已通過；當前 fresh 仍有來源成本缺值，不能宣稱更新成功**。Project settings 安裝未另獲明確確認。操作契約見 [Chat／CI 契約](docs/contracts/chat-ci.md)，分項證據見 [驗收帳](docs/superpowers/notes/2026-09-26-chat-ci-acceptance.md) 與 [9/27 來源缺口](docs/superpowers/notes/2026-09-27-chat-readback-and-source-gap.md)。Notion 已停止展示與同步，原頁已移到用戶的「垃圾桶」父頁，待用戶日後手動刪除；既有本地快照仍可用。

歷史 v1 CLI 重現方式（非固定視窗v2）：可在 repo 根目錄對**同一歷史輸入**重算到新檔（不會抓資料；不覆寫原 run）。v2使用上述Chat CI路徑：

```sh
python3 scripts/ladder_extra.py --input runs/2026-09-26-general-grok16/candidates.csv --min-score 0 --min-score-reason '用戶確認：同版本全候選比較' --factor 18 --grok-factor 16 --output /tmp/opencode/model-efficiency-corrected-ladder.md
```

新資料擷取與憑證取得／安全載入另見 [資料存取手記](docs/superpowers/notes/2026-09-26-grok16-data-access.md)；腳本使用環境變數 `AA_API_KEY`，絕不追蹤密鑰或將值輸出到命令、日誌與快照。認證 API 回覆版本 4.3 與此公開頁推定 4.3.2 快照**不可混用**。
