# GitHub Pages 展示與交付契約

2026-10-07 個人主力增量：已驗證成功結果可按明示選擇另發布 `personal-cp.json`，只在該固定結果目錄加入 allowlist，manifest 記 URL／SHA-256、五頁共用同一 view；不改原結果／報告／provider-ladder。選擇綁 result path／hash，不自動沿用至新計算。產品 CI／publication review／main-results consistency gates 維持。保存、Chat 操作與精確部署版本驗收見同版 [personal-cp.md](personal-cp.md)。

**2026-10-07 產品發布與重跑修正**：正式 Pages 除成功計算外，也在同庫 main 的 Product CI（push）通過後自動建置部署；PR、fork、失敗或已落後 main 的 CI 不可觸發產品發布，產品 checkout 固定為通過 CI 的完整 SHA。Chat execution 仍核對獨立 request/run/attempt，產品 CI 不冒充新計算。build 產生 `github-pages-<run_id>-<build_attempt>` 名稱並以 job output 傳給官方 upload/deploy action；只重跑 deploy 仍使用成功 build 的原 artifact，重跑 build 則產生新名稱，避免同名歧義及 attempt 漂移；不刪舊 artifacts 或歷史證據。deploy 前另以 contents:read 讀回 main／results refs，必須等於成功 build 固定的產品／results tip；較舊 artifact 不可透過 deploy-only 重跑蓋掉新產品或結果。所有來源／結果驗證、其餘最小權限及正式情境門檻維持。

**2026-10-07 最新來源退出呈現政策（優先於下方較早位置規則）**：依使用者要求，網站與新產生的 HTML 將完整「本次來源退出」清單原樣放在全部供應商頁的最後、計算與來源之後；四家供應商分頁不重複整批清單，也不在計算展開區重複。單一模型的缺值／退出狀態及來源理由仍保留，成功 JSON caveats、原始證據與已保存的歷史報告不改寫；無退出不造空區。此為展示更新，不變更算法、倍率或資料來源。

**2026-10-07 公開與部署現況（本節優先於下方較早狀態）**：使用者最新明確確認「repo 和 page 都改 public，Artificial Analysis token 不會被公開就好」，並已完成管理設定。本庫 visibility 已讀回 public；Pages Source 為 GitHub Actions，`github-pages` environment 只允許 main，正式部署開關已由成功 configure/deploy 實證生效。[正式首頁](https://ga815647.github.io/model-efficiency-frontier/) 匿名 HTTP 200；[Pages run 37565960035-1](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37565960035) build/deploy 均成功，deployment `6900788565` success。正式結果為 request `680ad45c-3818-4fbd-809e-59b3a68117ff`／run `37564382191-1`，結果 publication `f4d85b7ab0c939b2770b6d79a26a85f52bc8a960`，來源日期 2026-10-07、固定快照 recompute，不是新抓來源。四家倍率 ChatGPT17／Gemini3.6／Claude40／Grok5.2、新 v4 Claude 可推薦；下方舊倍率、僅比較及 private／未部署描述保留歷史身份。AA_API_KEY 仍只由 server-side Actions Secrets 注入，不放 repository variables、來源檔、網站或瀏覽器；不得讀保存的 secret 值。第三方條款的歷史發現保留，使用者確認不冒稱第三方授權。完整固定網址、雜湊、公開驗收見 `docs/acceptance/2026-10-07-public-pages.md`。Git 文件更新不代表 ChatGPT Project Settings 已更新。

2026-10-07最新增量：新正式request v3／result v4允許Claude推薦，網站新增四種訂閱專屬階梯及view/hash；以同版 [供應商契約](provider-ladders.md) 為準，下方v2/v3僅是相容歷史。allowlist另增加每個固定結果與首頁alias的四家`providers/<key>/index.html`、`view.json`、`manifest.json`。首頁要求新v4，不讓舊資格結果代替。

本網站沿用 Python bridge／靜態單檔 HTML。選型、來源取得及歷史精確 schema 保留；新版倍率使用request v2／result v3，見[倍率契約](subscription-factors.md)，瀏覽器只做文字搜尋與展開；JavaScript 關閉仍可讀兩入口、階梯與全部候選。

## 狀態與公開門檻

2026-10-06：產品 PR #3 已合併、固定快照 recompute 與自動 Pages build 成功；deploy job skipped。repo 保持 private，AA 再散布授權待解，尚未有成功 Pages deployment。公開檢查見 [publication-review.md](publication-review.md)。現有 token 讀 Pages／branch protection 設定 API 回傳 403，metadata 的 admin=true 不代表每個 endpoint 具權限。

公開檢查必須涵蓋所有遠端 branches／tags 可達歷史、logs／artifacts、issue／PR／discussion 內容及原始第三方來源。未確認敏感或再散布問題時停止 public 與公開部署；不得以刪歷史、force push 或自行改授權排除問題。

## 成功計算到部署

1. `chat-execution.yml` 只接受本庫 `efficiency-run/**` request push；bootstrap 從 main 驗證 request 唯一 parent／唯一新增檔，再執行已在 main 的產品。失敗保存診斷，run 維持紅色。
2. `publish.py` 將結果 append 到 results，保留原先來源／hash／schema gate、不可回寫與 monotone pointers。
3. `pages.yml` 使用 `workflow_run: Chat execution completed`。成功才啟動，與 GITHUB_TOKEN 推送 results 的 push event 無關。可用 `workflow_dispatch` 重試部署，僅 main。
4. Pages build 只 checkout main，不 checkout／執行 upstream branch、artifact 或任何不受信任程式。以 GitHub API 讀精確 upstream run／attempt，核對同庫、push、成功、精確 workflow path、branch 和 head；再由 Git transport gate 核對 request。取得實際 results tip 後所有讀取均固定 commit。
5. `bridge.site` 逐一驗證成功 v2/v3 envelope、immutable introduction、request 關聯與原始來源 proof／CSV hash，再以既有計算核對保存結果。呈現與 JSON 使用同一 envelope，renderer 不重選檔。歷史 v1 不改標 v2，也不自動重新解釋。
6. 每次完整輸出全部已驗證成功 v2/v3 的固定 `results/<request_id>/<run_id>-<attempt>/` 頁；重新部署仍指向相同結果。首頁只選正式參數完全相符的成功結果。正式情境在 `site-policy.json`，可追至固定 refresh envelope；新倍率另有factor_evidence，source floor／理由／cap仍核對相同；實驗不無聲覆蓋首頁。
7. `concurrency: model-efficiency-pages, cancel-in-progress:false` 序列化整條 build→deploy，每次排隊後重新固定最新 results；首頁按來源日期、created_at、request commit、run／attempt 排序。因此較早 request 較晚完成時仍保留最新正式結果，失敗／無正式成功／驗證錯誤不產生新的可部署輸出。
8. 只有 `repository.private=false` 且 repo variable `PUBLICATION_REVIEW_PASSED=true` 才 configure／deploy。build 只需 contents:read、actions:read；deploy 只需 pages:write、id-token:write，使用 github-pages environment。外部 PR 僅 Product CI read token、無 secrets／發布／部署，無 pull_request_target。

## 部署設定（公開門檻解除後）

具管理權限的身分讀回 visibility 為 public，再於 Settings → Pages 選 Source **GitHub Actions**（REST `POST /repos/{owner}/{repo}/pages` 或既有站 `PUT`、`build_type=workflow`）；建立／核對 `github-pages` environment，部署只允許 main。使用預設網域，沒有 CNAME 或自訂網域。設置 `PUBLICATION_REVIEW_PASSED=true` 前記錄可驗證的第三方授權及最新遮罩掃描。

以 `gh workflow run pages.yml --ref main` 進行初次或失敗重試；之後成功 request run 自動串接。查實際 Pages setting `html_url` 與 deploy-pages 的 `page_url`，核對 deployment 成功、manifest 和固定結果，不從預期網域猜測上線狀態。標準 ubuntu-24.04 hosted runner，沒有 larger runner 或付費平台設定。

所用官方 Actions 經 2026-10-06 官方 releases／Git refs 核對，固定 commit：configure-pages v6.0.0、upload-pages-artifact v5.0.0、deploy-pages v5.0.1（SHA 見 workflow；支援現行標準 hosted runner）。`enablement:false` 避免 workflow 靜默擴大站點公開範圍。

## 發布 allowlist 與 manifest

只發布 `.nojekyll`、首頁 `index.html`／`manifest.json`、每個固定結果的 `index.html`／`result.json`／原始備用 `report.html`／`manifest.json`；不把 repo、snapshot、原頁、API 診斷或 `.git` 直接當網站目錄。來源證據保留於固定 Git publication 供稽核。

manifest 獨立於 result schema，記 website_version、site_product_commit、結果 product_commit、publication_commit、request_commit、request_id、run_id、run_attempt、operation、來源日期、正式情境、result_schema_version及 result/report/source CSV SHA-256。首頁 manifest 指向當次選定固定結果頁；資料來源日期與部署時間分開。網址內使用實際 Pages base_path，以支援 project subpath。

## 驗收

合併後重新固定 main，讀同版規約；從最近已驗證 refresh 固定 envelope 繼承來源floor／理由／cap，倍率採已合併policy；僅更新表不自動改網站，要求新LADDER時走request v2。提交之前揭露實際來源 path、來源日期及「不會重新抓取新模型，快照後新增模型不會出現」。仍走唯一 request bridge，讀回 parent／唯一 added path、run head／branch／ID／attempt，再固定本次 publication，驗證 JSON、CSV／原頁與 HTML 雜湊。

部署成功後以不帶 GitHub 認證的 HTTP／Chromium 驗證首頁、固定頁及 manifest。`scripts/verify_site.py --url <實際網站根網址> --expected-json <本次固定 result.json> --output <證據目錄>` 檢查 360、390、1280px、搜尋、空結果、展開、鍵盤、no-JS 內容及整頁無橫向溢出。此腳本也可驗本地 HTTP，但本地成功不等於公開站驗收。
