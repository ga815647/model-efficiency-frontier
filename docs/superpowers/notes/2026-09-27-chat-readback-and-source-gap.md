# Chat 實際讀回與 fresh 來源缺口（2026-09-27）

## 證據範圍

使用者於本對話帶回 `pasted-context-1.txt`，回報目標 Chat 已提交 recompute／refresh、查詢 Actions 並讀回各自結果。這是**使用者提供的 Chat 端證據**；OpenCode 另以唯讀 GitHub API 核對以下 run 與固定 publication commit 的 envelope，不冒充由 OpenCode 操作 Chat。Project 顯示名稱與 settings 貼上確認未另提供，不從執行成功推定設定 UI 已安裝。

兩次請求共用同一產品 commit `03d0692d56feddaf1ef6a3a1b8ed765c491b1bd9`，各有不同 request commit；均為 `event=push`、`run_attempt=1`。

| 操作 | request ID／request commit | Actions | 固定 publication commit |
| --- | --- | --- | --- |
| recompute | `0d0851f5-082a-448c-8cf6-fd96a9ae0bf0`／`474c4689d98fd6bf1f8e5d0c812d49dfdd1a4483` | [36282186076，成功](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36282186076) | `f080fa6b3104707a419335b1489ab2be7cee4ba8` |
| refresh | `9435f830-dfa7-4620-b557-fd14b47a435a`／`cc587e868a95c664a9a9bbbbfe4bb32c7d217d08` | [36282226673，失敗](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36282226673) | `a097c434e2532875289092865e5a594bb6371973` |

各 envelope 路徑均為 `results/<request_id>/<run_id>-1/result.json`。run 的 head SHA、branch、operation、request/product/run/attempt 與對應 envelope 一致。recompute 來源為 `ba7911db85e5634f3853d90b9180a84a5cbf449b` 下 `results/118b299c-bddd-4228-be1e-e7cd49403d77/36259726459-1/snapshot/candidates.csv`。refresh 回傳 `status=failed`、`execution_failed`／`Decimal.ConversionSyntax`，不是舊成功 picks。

**已通過：本私人庫的 Chat 請求提交、push 觸發、精確 run 查詢，以及成功／失敗結果讀回。** 不再要求重做工具能力問卷。**尚缺：當前公開來源可完成的新 refresh**；Chat 直接附件能力與 settings 安裝確認仍不能由此推定。

## 已定位的 parser 錯誤

失敗 run 保存的 AA leaderboard 把 517 個成本欄位序列化成 React Flight `"$undefined"`；parser 原樣交給 `Decimal`，第一個崩潰 identity 是 `mistral-medium-3-1`。保存的四份來源可離線重現，leaderboard SHA-256 為 `60a7a6e68dc9b509840a5e7b5a7d43195dcadb98e8400043efb02cdd15cde71a`。

修訂 `fc92603`、`0174e98` 將精確 missing marker 分類為缺值，不作零成本或估價；score／task cost 及三個 optional token-price 欄位拒絕非法值並提供欄位＋slug 診斷。合法 optional price 十進位字串保留。140 項測試通過，獨立覆核通過；完整重播改為正確的 `missing_candidate`，仍不產生 CSV。已將覆核後的 `0174e98` fast-forward 推送至私人 `main`；重播驗證是本地證據，不宣稱遠端新 refresh 已成功。

## 兩個先前付費候選的成本確實缺失

2026-09-27 約 00:33–00:36 UTC 重新查得：

| identity | 同版 exact Score | index Cost per Task | 模型專頁 |
| --- | ---: | --- | --- |
| Inkling xhigh，slug `inkling` | 24.9847810999384 | `"$undefined"` | [v4.3.2 專頁](https://artificialanalysis.ai/models/inkling)有同分、無 task-cost 欄 |
| MiniMax-M2.7 unspecified，slug `minimax-m2-7` | 22.7578150287271 | `"$undefined"` | [v4.3.2 專頁](https://artificialanalysis.ai/models/minimax-m2-7)有同分、無 task-cost 欄 |

- **pass 1：本地 exact＋case-insensitive。** 已掃 `runs/*/candidates.csv` 與固定成功 fresh CSV；兩者原本存在，9/26 成本各為 `0.6070445010820831`／`0.10166685146353358`。這是歷史成本，不能當新抓值。
- **pass 2：index＋模型專頁＋拼寫變體。** 重新保存 index、Inkling／MiniMax-M2.7 canonical pages、release URL redirects，以及同 family 變體頁面；同 ID 分數存在、成本缺失。Grok／Muse release 的四組同分同價核對仍支持 index **推定** v4.3.2。token 單價不是 task cost。
- **pass 3：ID／effort 正向排除。** Inkling `0de09623-2b1a-4c8d-86ef-7f5245d4e24b` 為 xhigh；Inkling Small `7261504e-503c-4a66-a9d3-a3272cdf9ad6` 是不同 checkpoint 且分數估計。MiniMax-M2.7 `4bbceacb-cf47-464b-b60f-e1d1fe016d67` 不等於 M1 40k／80k、M2、M2.1、M2.5 或 M3；近代 M2.5 的 22.7966473221872 是估計分，M3 的 29.2202932236316／0.5076126905781733 屬不同 successor ID `277f939a-985b-4b37-859d-b3eabc7c0b26`，均不可代入。

本次 live index SHA-256 `835c7f9bfdff7470aeb8823ede43500f953d6b750a439c3021ae89bbdebd59ee`；Inkling 頁 `e30ab316234788e74922fc7b40bf2a664b789aa1271455b4e4ef8f323e052278`；MiniMax-M2.7 頁 `1f8685b520f93e3ff739eb73f98e64b662697fda9c49eba74c1a83f3fcef43be`。完整三遍結果、原頁、fetch metadata、全部近似 ID 和重播腳本保存在本機 `/tmp/opencode/2026-09-27-refresh-debug/`（`diagnosis.md`、`missing-cost-check.md`、`fix-report.md`；此本機目錄不冒充 Git 歸檔來源）。失敗 run 的四份原頁另已固定於上述 results commit。

目前 guard 維持阻擋，不靜默縮表、不沿用舊成本。模型 identity／Score 存在，缺的是當前精確 AA task cost。試版檔位比較使用已批准的 9/26 歷史快照，不宣称當日 fresh 成功。
