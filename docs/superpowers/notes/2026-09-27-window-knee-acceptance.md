# 固定視窗 v2 驗收帳（草稿）

日期：2026-09-27。**LOCAL implementation reviewed；REMOTE PENDING**。
本稿只記本地證據與待驗欄位，尚非v2部署完成證明。產品基準 `eb3ecf1`，分支 `feat/window-knee`；文件獨立覆核後由控制端繼續遠端驗收。規格：[固定視窗設計](../specs/2026-09-27-window-knee-production-design.md)；契約：[request v1／result v2](../../contracts/chat-ci.md)。

## 本地實作與覆核

- Task 1–5已實作選擇核心、final-only兩入口／升級／B診斷、v1/v2相容、共用Markdown／HTML與預設v2切換。
- 本地SDD覆核紀錄：`.superpowers/sdd/2026-09-27-window-knee-production/` 下 `task-1-review.md`、`task-2-review.md`、`task-3-rereview-1.md`、`task-4-rereview-evidence.md`、`task-5-review.md`。此為控制端本地證據目錄，非遠端發布路徑。
- 發布前全產品覆核發現v2 validator可接受偽造但內部一致的不可用Contributor max推薦；`eb3ecf1`增加v2身份可用性guard及正反測例，`prepublish-rereview.md`確認已解決，無新增Critical／Important問題。v1歷史結果保持可讀。
- 修補後紀錄：result contracts **27/27**、selection **27/27**、bridge **98/98**、full **229/229**；詳見本地 `prepublish-fix-report.md`。完整測試有既有missing-config案例預期警告 `/nonexistent/opencode.json`，無失敗。
- 文件階段核對 `bridge/result_v2.py` 的 `_COMMON`／`_SUCCESS`／`_ROW_FIELDS` 及trace、anchors、upgrade、B effects鍵；request保持五個parameters。workflow實際仍以 `efficiency-run/**` push及 `bridge/requests/*.json` 觸發，無需改配置。
- 文件階段重跑 `python3 -m unittest discover -s tests`：**229 tests，35.747s，OK**（同一既有預期警告）。`git diff --check`通過；Python核對所有v2共有／成功／row鍵均出現在契約、policy一致，五份文件的本地Markdown連結皆存在。

## 固定快照與OAT證據（非新取數）

來源：`runs/2026-09-26-general-grok16/candidates.csv`；SHA-256：`e3916f8405904154f0e1dc648588bb08ce92f483cd616ba9be0ff2e5c726ed22`。參數GPT18／Grok16、min_score=0（使用者確認同版本全候選比較）、max_cost=null；公開來源版本推定v4.3.2，不混認證API v4.3。

155原始paid稽核＝136 excluded（含不可用Muse Spark1.3 Contributor max）＋9 cut＋10 final；154可用身份→19 CP鏈點→10保留點。final為Claude Opus5.5 xhigh（僅比較）、Astra xhigh／medium、Sol max／high／medium、Luna max／high／medium／low。兩入口為Astra xhigh與Luna low；全cut winner均為final。這是固定歷史輸入的本地結果，非live候選數承諾。

Task5的本地 `task-5-oat.py`／`task-5-oat.json` 保存1,232個production/probe對照情境。final身份與trace winner／removed順序完全一致；strength比較使用Python `math.isclose(abs_tol=1e-12)`，同時保留預設 `rel_tol=1e-9`，不是僅絕對容差。選擇比較本身未加容差。各308情境的非Claude名單改變數：Score±0.1＝2、Score±0.25＝3、Cost±1%＝0、Cost±5%＝2。Astra high+0.25仍改選；原max+0.25／xhigh−0.25不改非Claude名單。此為敏感度證據，不是可靠度機率。

## 本地HTML瀏覽器證據

控制端Task4使用真實Chromium驗證；本文件階段回讀保存的 `/tmp/opencode/window-knee-review/browser-acceptance.json`（未冒稱重新跑瀏覽器）。1280／390px下document與body寬度皆等於viewport，兩卡呈2欄／1欄，10個ladder rows，六個table wrappers皆 `overflow-x:auto`。僅載入本地file URL，external requests均為空。

控制端已目視 `task-4-1280-viewport-font.png`／`task-4-390-viewport-font.png` 的中文字與卡片布局；`task-4-rereview-evidence.md`關閉原瀏覽器證據缺口。樣本 `/tmp/opencode/window-knee-review/task-4-window-report.html` 使用fixture合成commit定位，僅本地renderer驗證，不是Git發布或artifact比對證據。

已知非阻擋限制：renderer中性support理由概稱CP tie-break，但中性0也可能勝過負strength而非真正平手；數值／選檔不因此改變，覆核已記錄延後。不能將此文字解讀為所有中性勝出都經CP平手。

## REMOTE PENDING（由控制端續填）

| 驗收欄位 | 狀態 |
| --- | --- |
| 文件獨立覆核／發布前main祖先檢查 | REMOTE PENDING；文件尚待控制端覆核 |
| 已發布產品完整SHA／main讀回 | REMOTE PENDING |
| recompute request UUID／request commit／branch | REMOTE PENDING |
| recompute run URL／run_id／attempt | REMOTE PENDING |
| recompute固定results commit／精確result路徑 | REMOTE PENDING |
| recompute request/product/run/parameters/source關聯與v2驗證 | REMOTE PENDING |
| 同run HTML artifact與固定Git report.html SHA-256／bytes比對 | REMOTE PENDING |
| refresh request UUID／request commit／branch | REMOTE PENDING |
| refresh run URL／run_id／attempt／固定results commit及路徑 | REMOTE PENDING |
| refresh成功或missing_candidate失敗證據及pointer檢查 | REMOTE PENDING |
| 驗收文檔發布／最終遠端讀回日期 | REMOTE PENDING |

目前最後已驗證的真實fresh仍受Inkling／MiniMax-M2.7 task cost缺值阻擋，見 [來源缺口](2026-09-27-chat-readback-and-source-gap.md) 與 [身份修復雲端證據](2026-09-27-contributor-effort-correction.md)。此次本地fixture成功不取代真實fresh。後續若仍missing_candidate，須確認失敗envelope無ladder／anchors、能力與缺值證據完整發布、成功pointer未推進；若來源補齊，按當次真實來源驗證，不硬套154候選。

沿用既有目標Chat提交／查run／成功及失敗讀回證據；未新增Chat端實測。Project bootstrap定位維持，Git指示發布後不需因本次改制重貼；settings安裝狀態不推定。輸出為Chat＋按需單檔HTML，歷史runs與已發布結果不回寫。
