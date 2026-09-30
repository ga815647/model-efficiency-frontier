# Refresh Reconciliation Acceptance

**最新狀態：Task1–4獨立覆核通過；Issue #2對談指示／fixtures本地修訂，離線consumer GREEN及獨立覆核待控制端。整條分支尚未正式發布或執行修復後live驗收。** 使用者最新要求完成Chat/main可用性，控制端已獲最終覆核乾淨後非force發布及live／固定重算驗收授權；不需再問一般實作批准，不代表遠端動作已完成。

Execution base: bcb70e1bf78079facf3525858f15c593bc855a7d

## Approval and scope

使用者在 #1 五任務計畫審閱請求後詢問每次如何判斷退役／缺值；確認依當次明確deprecated flag、不將缺價或消失推定退役、不改歷史快照後回覆「可以了」。#1計畫及前述#2 bounded短設計進入實作；當時不推定發布或request Git write授權。其後「卡在哪 直接做完給我去chat 說“開始”啊」已由控制端記錄為整條分支最終覆核後非force發布及planned live／fixed-recompute驗收授權；仍無issue自動結案或settings編輯授權，Task4不執行遠端動作。

規格：`docs/superpowers/specs/2026-09-30-refresh-reconciliation-design.md`。
計畫：`docs/superpowers/plans/2026-09-30-refresh-reconciliation.md`。
工作區：既有linked worktree `.worktrees/window-knee`，branch `docs/refresh-reconciliation`；root工作區不動。

## Execution baseline

- 開始前工作樹乾淨；Git dir與common dir不同、無superproject，確認現有隔離。
- `python3 -m unittest discover -s tests`：229 tests，OK，37.186s；既有測試刻意對缺檔config輸出WARNING。這是舊產品基線，不是修復驗收。
- Python僅用標準庫；不新增dependencies或網路測試。

## Task checklist

- [x] Task 1：來源純分類與追蹤，`152ff0a`，239 tests OK；task-1-review spec compliant／quality approved，無issues。
- [x] Task 2：proof及可信policy解碼，`207d1d1`，252 tests OK；task-2-review spec compliant／quality approved；expected-stderr Minor原記progress，已於Task3解決。
- [x] Task 3：producer／runner／publisher／workflow整合，`6b37e66`＋`b27ee66`，274 tests OK；原P及duplicated-gate findings修正後獨立再覆核乾淨，expected output已捕捉。
- [x] Task 4：退出摘要及契約，實作／TDD本地完成（report 10、HTML 5、full 276 tests OK）；本次控制端交接確認已獨立覆核通過，execution baseline `387fb0f`。
- [ ] Issue #2 bounded task：pre-write freshness disclosure／十個對談fixtures本地修訂；離線consumer GREEN及獨立review仍待控制端。
- [ ] Task 5 local：完整測試、保護檔、固定historical重算、whole-branch review。
- [ ] 正式整合／發布：已授權最終覆核乾淨後由控制端非force執行，尚未執行。
- [ ] 新live refresh／新fixed recompute／artifact及pointer：已授權，由控制端於發布後驗收，尚未執行。
- [ ] 目標Chat新版退場摘要／短續接路由：待實測，不重做connector能力問卷。

## Status

Task4只是共享 `DISCLOSURE_PREFIX` 的只讀filter投影：Markdown anchors後／tables前，HTML cards後／ladder前；escaping、順序、不變payload、無空警告及完整footer皆經測試。無新request／result／row欄位，不改selector或路由。production新policy原P以恰好 `product_sha`／`results_commit`／`result_path` 的 `previous_inventory` 固定Git locator獨立導出，archive路徑及result唯一immutable introduction為權威；trusted legacy與old-wire gate不從untrusted map降級，契約已記錄。

RED：10 report tests中來源退出summary缺席導致1 failure；GREEN：report 10 tests（0.378s）、HTML 5 tests（0.058s）、full discovery一次276 tests（50.257s），全部OK且無stderr警告。logs：`/tmp/opencode/task4-red.log`、`task4-report-green.log`、`task4-html-green.log`、`task4-full-green.log`（後三同目錄）。詳細檔案／自查／commit證據见 `.superpowers/sdd/2026-09-30-refresh-reconciliation/task-4-report.md`。

尚未發布、尚无修復後live成功證據；9/27真實fresh `36341142058-1`及9/30已固定失敗原頁／重播證據照舊保留，不用離線fixture成功替代或抹掉失敗。issue #2 pre-write guard另待下一task，source修復成功不等於短續接路由驗收。舊目標Chat v2已通過能力直接沿用，但新版退出摘要／短續接仍待目標Chat實測；Project settings安裝仍獨立、不因instructions修訂或Git push推定已安裝。bootstrap不改、Notion及網站政策不改。

## Issue #2 bounded instruction bugfix — local candidate

本段覆蓋上方issue #2「另待下一task」的較早狀態。Worker依控制端bounded brief、global constraints及已記錄baseline修訂，不讀完整計畫、不新增router／schema，不派consumer／reviewer或執行遠端動作。執行基線 `387fb0fff3e7abc81ff0b16e7b7c08af016f5d49`，開始時工作樹乾淨。

- 歷史實際RED（目標Chat，非本次worker親測）：9/30短「開始」送出9/26固定重算，未先揭露freshness執行身份；request `7f3d85a2-6e34-4bd4-9d91-4d6d11c7a4b8`、run `36665990363-1`、publication `171c1b797c8db6a9606ed3a9f42acce8df3c9cbc`。
- 控制端離線baseline consumer `ses_f0f032daaffeLAE1Jva8CBJ2iA`：a/d/i正確選recompute、說9/26與不重抓，但兩項Git寫入前沒有可見實際固定path及快照後新模型不會出現的明文後果，這兩項為RED；並非宣稱所有route失敗。b/e refresh、c/f clarification、g/h只讀與j日期結論已符合當次觀察，保留為非回歸controls。逐字記錄／評估：`.superpowers/sdd/2026-09-30-refresh-reconciliation/routing-baseline-observations.json`、`routing-baseline-assessment.md`。
- 最小修訂：`chatgpt-instructions.md`及同版契約要求在 `create_branch`／`create_file`兩者之前可見operation／來源身份；固定重算揭露實際path、來源日期與「不會重新抓取新模型，快照後新增模型不會出現」。依已授權當前意圖續接；新版程式不強制fresh，最新模型意圖只在refresh floor＋理由已授權時提交，缺決策或互斥來源要求則零寫入。pending續查與report lookup只讀；重算結論旁標source_dates與非fresh，失敗不回退旧成功。
- `tests/fixtures/chat-routing/shorthand-freshness.json`十個bounded cases及README：對話／核對context／可觀測行為／禁止寫入，probe a–j與原inputs一一對應。控制端須用原 `routing-probe-inputs.json`相同輸入做fresh blind consumer，consumer不可讀expectations或本報告；逐項人工判讀操作順序與可見訊息，沒有假keyword unittest。
- **離線GREEN consumer pending，獨立review pending**。既有完整suite只驗pipeline／schema非回歸，不證明路由遵循；本地candidate、posted main、cloud live／fixed重算與artifact、目標Chat新版routing/readback及settings證據分開。Worker未發布或新建cloud request，controller最終覆核後交付授權仍有效；bootstrap不改、Project不用因本次Git指示修改重貼，settings安裝不推定。
- Worker完整suite一次：`python3 -m unittest discover -s tests`，276 tests／49.493s／OK，exit0，無stderr警告；log `/tmp/opencode/issue2-full-suite.log`。JSON結構檢查確認十個fixture的shared source／parameters、a–j context及last turn與原probe inputs完全相同；這只驗fixture對齊，不是consumer GREEN。

Worker測試／自查／commit交接另見 `.superpowers/sdd/2026-09-30-refresh-reconciliation/issue-2-report.md`；控制端consumer及review結果應在實際取得後另補，不預填通過。
