# 2026-10-07 GitHub Pages 公開部署驗收

本紀錄新增本日公開部署事實；10/6 的 private／HTML／deploy skipped 驗收維持原身份，不回寫歷史。

## 正式入口

- [首頁](https://ga815647.github.io/model-efficiency-frontier/)
- [本次固定結果](https://ga815647.github.io/model-efficiency-frontier/results/680ad45c-3818-4fbd-809e-59b3a68117ff/37564382191-1/)
- [ChatGPT](https://ga815647.github.io/model-efficiency-frontier/providers/gpt/)、[Gemini](https://ga815647.github.io/model-efficiency-frontier/providers/gemini/)、[Claude](https://ga815647.github.io/model-efficiency-frontier/providers/claude/)、[Grok](https://ga815647.github.io/model-efficiency-frontier/providers/grok/)。首頁 alias 隨正式結果更新；本次固定頁下相同 providers 子路徑不改指其他結果。

URL 由實際 Pages setting `html_url` 及成功 deployment status `environment_url` 取得，兩者相同；沒有猜測網域就宣稱上線。

## 固定結果與部署

| 身份 | 實際值 |
|---|---|
| 產品 PR | [#8](https://github.com/ga815647/model-efficiency-frontier/pull/8)，獨立產品 branch；317 項測試含 4 個 Chromium 實測、review 無 Critical／Important／Minor，PR／合併 CI 成功 |
| 結果產品 commit | `4abc1b699a6f2ea5b5ee4d5fd12206b8584c00c3` |
| request | `680ad45c-3818-4fbd-809e-59b3a68117ff`，schema v3；commit `a3904b2fa39ba4b7df2cf1bafa60ead8c9c6ac18` 唯一 parent 為產品 commit，唯一 added file 為同 UUID request JSON |
| 計算 run | [37564382191](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37564382191)，attempt 1、push、精確 request branch／head，success |
| publication | `f4d85b7ab0c939b2770b6d79a26a85f52bc8a960` |
| Pages 初次公開 run | [37565960035](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37565960035)，attempt 1，workflow_dispatch、main、上述產品 commit，build／deploy success |
| 公開 deployment | `6900788565`，github-pages，main，success；[deploy job](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37565960035/job/112613678933) |
| result SHA-256 | `153d781415b9bd990a193c9e46ab2c6a56b2a8f6dfb4251283644e1d51dc545c` |
| report SHA-256 | `412e574e363310179d452dbfe5a9203823445750fce0d3d4cfe10fe16920e40c` |
| source CSV SHA-256 | `d4236421edf6f4ecc5f8ec2bc600c3a33cecd498441b7c04d576d8b74c7e0dcc` |

固定來源 publication `77a72784521da1825718e23b0c9e1266720e6cd6`，CSV `results/4ab43e6d-54ab-4ae0-985f-5dc0ba9b4487/37555947564-1/snapshot/candidates.csv`；真實來源日期 **2026-10-07**，AA Intelligence Index v4.3.2 為 inferred。本次 recompute 不重新抓來源，快照後新增模型不會出現。從成功 refresh envelope 繼承 min_score=0、理由「同版本全候選情境比較」、max_cost=null；四倍率採已合併表 ChatGPT17／Gemini3.6／Claude40／Grok5.2，basis=user_specified。

新 result v4、eligibility_policy=all-providers-v1，105 候選、混排 9 檔；全候選來源／transport／版本／身份／hash／重播已核對。混排兩入口為 Claude Opus 5.5 xhigh 及 GPT-6 Luna low。各供應商以完整候選重選：ChatGPT 8 檔、Gemini 3、Claude 6、Grok 2；不混用 effort、不由瀏覽器選檔，歷史 v1/v2/v3 與原始證據不修改。

## 公開狀態與憑證

使用者最新明確確認「repo 和 page 都改 public，Artificial Analysis token 不會被公開就好」，並完成管理設定。API repository visibility=public、private=false；Pages build_type=workflow、public=true、HTTPS enforced、無 CNAME；github-pages environment custom branch policies 精確只允許 main。PUBLICATION_REVIEW_PASSED 的管理讀取仍 403，沒有推測其值；configure/deploy 實際執行成功證明 workflow gate 已開啟。曾經 visibility PATCH／Pages／Variables 403 的限制是當時 integration 管理權限，歷史證據保留；本次正常 workflow_dispatch API 實測成功，不繞過權限。

公開前掃描包括 28 分支、無 tags、129 遠端可達 commits／1297 objects，所有 results／runs／原始來源／診斷；39 runs／39 attempts、197 log files、17 個全部可下載 artifacts（含 3 個網站 bundles），無缺失 logs 或 artifacts。可見 issues／PR／review／inline／commit comments／releases 亦檢查，Discussions 關閉。gitleaks --redact=100：Git 56.71 MB 與 remote 76.72 MB，均 0 findings；未讀平台保存的 secret 值、不輸出未遮罩發現、不改寫或刪 Git 歷史。此統計固定在公開前時點，不當作未來變更保證。

AA_API_KEY 僅以 server-side Actions Secrets 注入 refresh；本次 recompute 和 Pages 都不需要它。網站發布明確 allowlist，不含來源 snapshot／整庫／憑證；外部 PR contents:read、无 secrets／結果寫入／部署，沒有 pull_request_target，高權限 Pages 僅執行可信 main。第三方原頁再散布條款的歷史發現仍留存，不把使用者確認冒稱第三方许可。

## 匿名 HTTP／瀏覽器驗收

以不帶 GitHub 認證的 urllib／Chromium 讀實際公開網址，首頁、本次固定頁、result.json／report.html／manifest 與四家 view.json／provider manifest 全部成功；JSON、來源日期、成本情境、anchors／階梯與已驗證固定結果一致，result/report/view SHA-256、parent publication 及 manifest 指向上述 request/run/attempt，沒有舊頁面或其他 latest-success 替代。

scripts/verify_site.py 完整執行通過：**360、390、1280px**，全部供應商與 alias、長模型名稱、Astra max／Sol max 搜尋、空結果、Escape 清除、Enter 展開、鍵盤連結與 no-JS 閱讀／切換。所有寬度沒有整頁橫向溢出與 script error。Pages artifact 11458066618 的 175 個檔案逐 byte 與獨立來源驗證建置相同；公開 HTTP 另核對全部可供瀏覽的 HTML／JSON／報告（.nojekyll 是建置標記），保留所有歷史固定頁。

初次公開成功後，本文件及規約做獨立文件 PR closeout；若部署此文件版本，site_product_commit 會是新的文件合併 commit，result 的 product_commit／publication／request/run/attempt 與上述 hash 維持不變。網站 manifest 明確區分這兩種 commit，不把文件更新當成新計算或來源更新。

## 限制與 Project Settings

四個倍率由使用者統一到約 US$100/月個人訂閱後指定，推導、來源缺口、部分 meter 外推與反證見 docs/subscription-factors.md；不是保證額度、能力分數或所有人的 API 售價。API／AA 身份有觀測不代表訂閱當期一定開放每個模型／effort。來源版本 inferred 與歷史 GRADE-B／退出规则保留。

新版可貼 Instructions 在 docs/chatgpt-bootstrap.md；repo 文件已更新，不代表已替使用者修改或驗收 ChatGPT Project Settings。
