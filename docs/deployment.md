# GitHub Pages 展示與交付契約

本網站沿用 Python bridge／靜態單檔 HTML。選型、來源取得及精確 schema 不變，瀏覽器只做文字搜尋與展開；JavaScript 關閉仍可讀兩入口、階梯與全部候選。

## 狀態與公開門檻

2026-10-06：產品 PR #3 已合併、固定快照 recompute 與自動 Pages build 成功；deploy job skipped。repo 保持 private，AA 再散布授權待解，尚未有成功 Pages deployment。公開檢查見 [publication-review.md](publication-review.md)。現有 token 讀 Pages／branch protection 設定 API 回傳 403，metadata 的 admin=true 不代表每個 endpoint 具權限。

公開檢查必須涵蓋所有遠端 branches／tags 可達歷史、logs／artifacts、issue／PR／discussion 內容及原始第三方來源。未確認敏感或再散布問題時停止 public 與公開部署；不得以刪歷史、force push 或自行改授權排除問題。

## 成功計算到部署

1. `chat-execution.yml` 只接受本庫 `efficiency-run/**` request push；bootstrap 從 main 驗證 request 唯一 parent／唯一新增檔，再執行已在 main 的產品。失敗保存診斷，run 維持紅色。
2. `publish.py` 將結果 append 到 results，保留原先來源／hash／schema gate、不可回寫與 monotone pointers。
3. `pages.yml` 使用 `workflow_run: Chat execution completed`。成功才啟動，與 GITHUB_TOKEN 推送 results 的 push event 無關。可用 `workflow_dispatch` 重試部署，僅 main。
4. Pages build 只 checkout main，不 checkout／執行 upstream branch、artifact 或任何不受信任程式。以 GitHub API 讀精確 upstream run／attempt，核對同庫、push、成功、精確 workflow path、branch 和 head；再由 Git transport gate 核對 request。取得實際 results tip 後所有讀取均固定 commit。
5. `bridge.site` 逐一驗證成功 v2 envelope、immutable introduction、request 關聯與原始來源 proof／CSV hash，再以既有計算核對保存結果。呈現與 JSON 使用同一 envelope，renderer 不重選檔。歷史 v1 不改標 v2，也不自動重新解釋。
6. 每次完整輸出全部已驗證成功 v2 的固定 `results/<request_id>/<run_id>-<attempt>/` 頁；重新部署仍指向相同結果。首頁只選正式參數完全相符的成功結果。正式情境在 `site-policy.json`，可追至固定 refresh envelope；實驗不無聲覆蓋首頁。
7. `concurrency: model-efficiency-pages, cancel-in-progress:false` 序列化整條 build→deploy，每次排隊後重新固定最新 results；首頁按來源日期、created_at、request commit、run／attempt 排序。因此較早 request 較晚完成時仍保留最新正式結果，失敗／無正式成功／驗證錯誤不產生新的可部署輸出。
8. 只有 `repository.private=false` 且 repo variable `PUBLICATION_REVIEW_PASSED=true` 才 configure／deploy。build 只需 contents:read、actions:read；deploy 只需 pages:write、id-token:write，使用 github-pages environment。外部 PR 僅 Product CI read token、無 secrets／發布／部署，無 pull_request_target。

## 部署設定（公開門檻解除後）

具管理權限的身分讀回 visibility 為 public，再於 Settings → Pages 選 Source **GitHub Actions**（REST `POST /repos/{owner}/{repo}/pages` 或既有站 `PUT`、`build_type=workflow`）；建立／核對 `github-pages` environment，部署只允許 main。使用預設網域，沒有 CNAME 或自訂網域。設置 `PUBLICATION_REVIEW_PASSED=true` 前記錄可驗證的第三方授權及最新遮罩掃描。

以 `gh workflow run pages.yml --ref main` 進行初次或失敗重試；之後成功 request run 自動串接。查實際 Pages setting `html_url` 與 deploy-pages 的 `page_url`，核對 deployment 成功、manifest 和固定結果，不從預期網域猜測上線狀態。標準 ubuntu-24.04 hosted runner，沒有 larger runner 或付費平台設定。

所用官方 Actions 經 2026-10-06 官方 releases／Git refs 核對，固定 commit：configure-pages v6.0.0、upload-pages-artifact v5.0.0、deploy-pages v5.0.1（SHA 見 workflow；支援現行標準 hosted runner）。`enablement:false` 避免 workflow 靜默擴大站點公開範圍。

## 發布 allowlist 與 manifest

只發布 `.nojekyll`、首頁 `index.html`／`manifest.json`、每個固定結果的 `index.html`／`result.json`／原始備用 `report.html`／`manifest.json`；不把 repo、snapshot、原頁、API 診斷或 `.git` 直接當網站目錄。來源證據保留於固定 Git publication 供稽核。

manifest 獨立於 result schema，記 website_version、site_product_commit、結果 product_commit、publication_commit、request_commit、request_id、run_id、run_attempt、operation、來源日期、正式情境及 result/report/source CSV SHA-256。首頁 manifest 指向當次選定固定結果頁；資料來源日期與部署時間分開。網址內使用實際 Pages base_path，以支援 project subpath。

## 驗收

合併後重新固定 main，讀同版規約；從最近已驗證 refresh 固定 envelope 繼承參數／floor／理由。提交之前揭露實際來源 path、來源日期及「不會重新抓取新模型，快照後新增模型不會出現」。仍走唯一 request bridge，讀回 parent／唯一 added path、run head／branch／ID／attempt，再固定本次 publication，驗證 JSON、CSV／原頁與 HTML 雜湊。

部署成功後以不帶 GitHub 認證的 HTTP／Chromium 驗證首頁、固定頁及 manifest。`scripts/verify_site.py --url <實際網站根網址> --expected-json <本次固定 result.json> --output <證據目錄>` 檢查 360、390、1280px、搜尋、空結果、展開、鍵盤、no-JS 內容及整頁無橫向溢出。此腳本也可驗本地 HTTP，但本地成功不等於公開站驗收。
