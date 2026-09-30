# Refresh Reconciliation Acceptance

Execution base: bcb70e1bf78079facf3525858f15c593bc855a7d

## Approval and scope

使用者在 #1 五任務計畫審閱請求後詢問每次如何判斷退役／缺值；確認依當次明確deprecated flag、不將缺價或消失推定退役、不改歷史快照後回覆「可以了」。#1計畫及前述#2 bounded短設計進入實作；不推定正式發布、request Git write或issue結案授權。

規格：`docs/superpowers/specs/2026-09-30-refresh-reconciliation-design.md`。
計畫：`docs/superpowers/plans/2026-09-30-refresh-reconciliation.md`。
工作區：既有linked worktree `.worktrees/window-knee`，branch `docs/refresh-reconciliation`；root工作區不動。

## Execution baseline

- 開始前工作樹乾淨；Git dir與common dir不同、無superproject，確認現有隔離。
- `python3 -m unittest discover -s tests`：229 tests，OK，37.186s；既有測試刻意對缺檔config輸出WARNING。這是舊產品基線，不是修復驗收。
- Python僅用標準庫；不新增dependencies或網路測試。

## Task checklist

- [ ] Task 1：來源純分類與追蹤，TDD／獨立task review。
- [ ] Task 2：proof及可信policy解碼，TDD／獨立task review。
- [ ] Task 3：producer／runner／publisher／workflow整合，TDD／獨立task review。
- [ ] Task 4：退出摘要及契約，TDD／獨立task review。
- [ ] Issue #2 bounded task：pre-write freshness guard／對談fixtures／獨立review。
- [ ] Task 5 local：完整測試、保護檔、固定historical重算、whole-branch review。
- [ ] 正式整合／發布：待授權。
- [ ] 新live refresh／新fixed recompute／artifact及pointer：待發布與驗收授權。
- [ ] 目標Chat新版退場摘要／短續接路由：待實測，不重做connector能力問卷。

## Status

開始實作，尚未發布、尚无修復後live成功證據。Project settings安裝仍獨立，不因本地instructions修訂推定已安裝；bootstrap不改、Notion及網站政策不改。
