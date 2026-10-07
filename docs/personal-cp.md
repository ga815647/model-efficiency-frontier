# 本次個人主力 CP MVP

2026-10-07 使用者選定：本次以 Sol XHIGH 為標竿，容許向下 1×score EPS，在達標候選中選既有 CP_adj 最高者。這是個人接受程度，不是通用推薦，也不是 AA 的統計誤差。標竿不保送；更高分仍有資格。不得固定 50 分、固定勝出模型或改動 LADDER 數學。

## 選擇規則

`minimum_score = benchmark.score - tolerance_multiplier * result.eps.score`。

從同一已驗證成功結果的完整 `candidate_statuses`，保留可用身份、符合既有 `parameters.min_score`／`max_cost`、有推薦資格且 `score >= minimum_score` 的行。不限於 LADDER final；被 CP-new-high 或視窗精簡剔除的行也可能是個人主力。沿用原始 `cp_adj`，排序為 CP 高、分數高、成本低、identity 字典序，沒有候選就 null／從缺。綜合與 ChatGPT、Gemini、Claude、Grok 四頁共用綜合結果的同一標竿、EPS 和門檻，只改供應商範圍。Contributor 可在綜合參戰，不混入四種訂閱集合。歷史 v2/v3 的 Claude 僅比較資格仍適用。

## 每次新計算的 Chat 流程

1. 依同版 Chat 契約固定 main 與來源，列出已驗證來源中代表模型的精確 model／effort／identity、分數與 score EPS，先問本次個人標竿与容許幾個 EPS（可選 0，不容許向下）。不得因上一輪選過而默默繼承；同一 pending 請求續查與既有結果查詢不重問。這次已接受的 Sol XHIGH／1×EPS 不重問。
2. 保留使用者明示選擇，執行既有唯一 request v3 → result v4 流程。個人門檻不取代 LADDER 的 min_score，也不塞進嚴格 request 的七欄 parameters。refresh 用本次新結果的標竿分數，不沿用舊分數；標竿在新結果缺失或不可用就說明缺口，不代入近似模型／effort。
3. 成功後依同版契約驗證固定 publication、完整 envelope、來源與結果 bytes。以精確結果 path、新結果 SHA-256、使用者已選的 benchmark identity／tolerance 更新 `bridge/personal-cp-policy.json`，走獨立 `feat/*` 產品 PR、測試／review／合併與 Pages 部署。這一步保存已授權選擇，不再要同一次選擇確認。既有 policy entries 保留；不可把選擇當成之後所有計算的預設。若當前工具僅能送 request、不能完成產品 PR，明示個人選擇尚未發布，不冒稱網站已更新。
4. 個人摘要只讀本次網站 `personal-cp.json` 的已驗證 view／manifest，核對 parent result hash、publication、request/run/attempt、標竿與容許值；Chat 不手算或強迫 Sol HIGH。尚未保存選擇的新結果不產生個人主力卡片，仍顯示其既有客觀 LADDER；不得回退到舊個人主力。

## 保存與網站發布

`bridge/personal-cp-policy.json` 為精確 schema：根欄位 `schema_version=1`、`choices`；choices 以完整 `results/<request_id>/<run_id>-<attempt>/result.json` 為 key，value 恰有 `result_sha256`、`benchmark_identity`、`tolerance_multiplier`。容許值需有限且非負，布林／NaN／Infinity／未知欄位拒絕。

網站先完成既有 `load_record` 的 immutable introduction、request transport、來源 proof、CSV hash 與重播核對，再驗個人選擇的 result hash。任一不匹配、結果不存在、標竿缺失／不可用則在建立新輸出前失敗。選擇只綁一個結果，不自動套其他 run／attempt 或最新首頁。原 request v3／result v4、anchors、upgrade、provider-ladder view、歷史 report／CSV／raw sources 完全不改寫。

新增獨立 `kind=personal-cp`／`schema_version=1` 的 `personal-cp.json`，帶 parent_result_sha256、parent_publication_commit、request/run/attempt、標竿實際分數、EPS、容許倍數、門檻、五範圍 qualified identities 與 selected row。網站 manifest 另記 URL／SHA-256，四家 manifest 連向同一個 view。所有選型在 Python 完成，瀏覽器只讀卡片、搜尋與展開；無 JavaScript 仍可閱讀。

正式輸出 allowlist 只在有明確選擇的固定結果目錄增加 `personal-cp.json`；不發布 policy 工作檔或任何憑證。現有公開前檢查、main Product CI、deployment gate、唯一 Pages artifact 與 main/results snapshot consistency 檢查維持。來源退出清單仍在全部供應商頁最後。

## 驗收

單元測試驗 inclusive threshold、無上限、全候選、可換勝者、平手順序、零容許、空供應商、既有 min/cap／不可用身份與歷史推薦資格。Site 測試驗 SHA 綁定、未知結果 fail-before-write、immutable bytes、不同 run 不沿用。Chromium 驗 360／390／1280px、五頁、no-JS 與無橫向溢出。

公開站必須驗精確部署產品 commit、固定結果與 personal policy，不能只靠綠色 build：

```sh
python3 scripts/verify_site.py --url https://ga815647.github.io/model-efficiency-frontier/ --expected-json /tmp/current-result.json --expected-site-product <merged-main-sha> --personal-policy bridge/personal-cp-policy.json --output /tmp/personal-cp-evidence
```

Git 指示更新不等於 ChatGPT Project Settings 已更新；bootstrap 提供可貼文字，不冒稱已安裝。
