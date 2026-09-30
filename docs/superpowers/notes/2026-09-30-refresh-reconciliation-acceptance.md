# Refresh Reconciliation Acceptance

**最新狀態：Task1–4及Issue #2獨立覆核通過；Task5本地完整測試／75保護物件／9/30保存原頁重播／9/26固定控制驗證通過，待控制端唯一整條分支最終覆核。整條分支尚未正式發布或執行修復後live驗收。** 使用者最新要求完成Chat/main可用性，控制端已獲最終覆核乾淨後非force發布及live／固定重算驗收授權；不需再問一般實作批准，不代表遠端動作已完成。

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
- [x] Issue #2 bounded task：`473b0b8`，pre-write freshness disclosure／十個對談fixtures；10/10離線consumer GREEN，独立spec／quality review approved。
- [x] Task 5 local：完整測試、75保護物件、保存原頁重播、固定historical重算及docs自查。
- [ ] Task 5 whole-branch review：控制端下一步，worker未派reviewer。
- [ ] 正式整合／發布：已授權最終覆核乾淨後由控制端非force執行，尚未執行。
- [ ] 新live refresh／新fixed recompute／artifact及pointer：已授權，由控制端於發布後驗收，尚未執行。
- [ ] 目標Chat新版退場摘要／短續接路由：待實測，不重做connector能力問卷。

## Status

Task4只是共享 `DISCLOSURE_PREFIX` 的只讀filter投影：Markdown anchors後／tables前，HTML cards後／ladder前；escaping、順序、不變payload、無空警告及完整footer皆經測試。無新request／result／row欄位，不改selector或路由。production新policy原P以恰好 `product_sha`／`results_commit`／`result_path` 的 `previous_inventory` 固定Git locator獨立導出，archive路徑及result唯一immutable introduction為權威；trusted legacy與old-wire gate不從untrusted map降級，契約已記錄。

RED：10 report tests中來源退出summary缺席導致1 failure；GREEN：report 10 tests（0.378s）、HTML 5 tests（0.058s）、full discovery一次276 tests（50.257s），全部OK且無stderr警告。logs：`/tmp/opencode/task4-red.log`、`task4-report-green.log`、`task4-html-green.log`、`task4-full-green.log`（後三同目錄）。詳細檔案／自查／commit證據见 `.superpowers/sdd/2026-09-30-refresh-reconciliation/task-4-report.md`。

尚未發布、尚无修復後live成功證據；9/27真實fresh `36341142058-1`及9/30已固定失敗原頁／重播證據照舊保留，不用離線fixture成功替代或抹掉失敗。issue #2 pre-write guard及獨立本地routing驗證已完成（下方最新段），source修復成功不等於短續接路由驗收。舊目標Chat v2已通過能力直接沿用，但新版退出摘要／短續接仍待目標Chat實測；Project settings安裝仍獨立、不因instructions修訂或Git push推定已安裝。bootstrap不改、Notion及網站政策不改。

## Issue #2 bounded instruction bugfix — local candidate

本段覆蓋上方issue #2「另待下一task」的較早狀態。Worker依控制端bounded brief、global constraints及已記錄baseline修訂，不讀完整計畫、不新增router／schema，不派consumer／reviewer或執行遠端動作。執行基線 `387fb0fff3e7abc81ff0b16e7b7c08af016f5d49`，開始時工作樹乾淨。

- 歷史實際RED（目標Chat，非本次worker親測）：9/30短「開始」送出9/26固定重算，未先揭露freshness執行身份；request `7f3d85a2-6e34-4bd4-9d91-4d6d11c7a4b8`、run `36665990363-1`、publication `171c1b797c8db6a9606ed3a9f42acce8df3c9cbc`。
- 控制端離線baseline consumer `ses_f0f032daaffeLAE1Jva8CBJ2iA`：a/d/i正確選recompute、說9/26與不重抓，但兩項Git寫入前沒有可見實際固定path及快照後新模型不會出現的明文後果，這兩項為RED；並非宣稱所有route失敗。b/e refresh、c/f clarification、g/h只讀與j日期結論已符合當次觀察，保留為非回歸controls。逐字記錄／評估：`.superpowers/sdd/2026-09-30-refresh-reconciliation/routing-baseline-observations.json`、`routing-baseline-assessment.md`。
- 最小修訂：`chatgpt-instructions.md`及同版契約要求在 `create_branch`／`create_file`兩者之前可見operation／來源身份；固定重算揭露實際path、來源日期與「不會重新抓取新模型，快照後新增模型不會出現」。依已授權當前意圖續接；新版程式不強制fresh，最新模型意圖只在refresh floor＋理由已授權時提交，缺決策或互斥來源要求則零寫入。pending續查與report lookup只讀；重算結論旁標source_dates與非fresh，失敗不回退旧成功。
- `tests/fixtures/chat-routing/shorthand-freshness.json`十個bounded cases及README：對話／核對context／可觀測行為／禁止寫入，probe a–j與原inputs一一對應。控制端須用原 `routing-probe-inputs.json`相同輸入做fresh blind consumer，consumer不可讀expectations或本報告；逐項人工判讀操作順序與可見訊息，沒有假keyword unittest。
- **離線GREEN consumer pending，獨立review pending**。既有完整suite只驗pipeline／schema非回歸，不證明路由遵循；本地candidate、posted main、cloud live／fixed重算與artifact、目標Chat新版routing/readback及settings證據分開。Worker未發布或新建cloud request，controller最終覆核後交付授權仍有效；bootstrap不改、Project不用因本次Git指示修改重貼，settings安裝不推定。
- Worker完整suite一次：`python3 -m unittest discover -s tests`，276 tests／49.493s／OK，exit0，無stderr警告；log `/tmp/opencode/issue2-full-suite.log`。JSON結構檢查確認十個fixture的shared source／parameters、a–j context及last turn與原probe inputs完全相同；這只驗fixture對齊，不是consumer GREEN。

Worker測試／自查／commit交接另見 `.superpowers/sdd/2026-09-30-refresh-reconciliation/issue-2-report.md`；控制端consumer及review結果應在實際取得後另補，不預填通過。

## Task5 LOCAL verification — 2026-09-30（覆蓋上方worker交接的pending狀態）

本地執行基線 `473b0b8913864cb85e6ce4c05f145785fe55a73f`，開始工作樹乾淨。只讀產品、tests及歷史物件；本次tracked變更只有狀態／驗收文件及本地計畫checkbox。未取live、未寫remote／request／issue／settings，未派reviewer。控制端負責一次整條分支最終review及已授權的非force main交付、live與固定重算。以下保存原頁重播是**歷史9/30來源、本地回歸證據，不是新live refresh**。

### 實際命令與輸出

```sh
env -u AA_API_KEY python3 -m unittest discover -s tests > .superpowers/sdd/2026-09-30-refresh-reconciliation/task-5-full-tests.log 2>&1
env -u AA_API_KEY python3 .superpowers/sdd/2026-09-30-refresh-reconciliation/task-5-local-verify.py
git diff --check
```

- Full suite：`Ran 276 tests in 49.915s`／`OK`，exit0，無stderr警告。移除只限子process環境，不讀取或輸出key值；API diagnostic實際為`not_collected / AA_API_KEY absent`。
- 驗證腳本exit0；`git diff --check` exit0。腳本以`protected-baseline.json`固定execution base逐一查`git ls-tree <base|HEAD> -- <path>`，75個mode/type/blob物件皆一致，0 changes；另執行Task5 brief完整protected `git diff --exit-code bcb70e1bf78079facf3525858f15c593bc855a7d -- runs scripts/compute_frontier.py scripts/ladder.py scripts/ladder_extra.py experiments tests/fixtures/refresh/failed-two-costs-flight.html tests/fixtures/refresh/leader.html tests/fixtures/refresh/grok.html tests/fixtures/refresh/muse.html tests/fixtures/refresh/meta.html tests/fixtures/refresh/models.html tests/fixtures/refresh/README.json`：exit0、空diff。新增fixture不算歷史物件改動。
- Scratch證據：`.superpowers/sdd/2026-09-30-refresh-reconciliation/task-5-local-results.json`、`task-5-full-tests.log`、`task-5-local-verify.py`、`task-5-replay-v2/`、`task-5-historical-v2/`。保存重播取數位於同scratch `task-5-saved-replay-w07lx_bq/snapshot/`。這些為ignored本地交接，不當作雲端publication。

### 五份保存原頁 SHA-256（從bytes獨立算，全部與sources.json一致）

原bundle：`/tmp/opencode/model-efficiency-issue1-20260930-evidence/`。fetch callable只允許以下五URL的保存bytes，未知URL raises，無network fallback。以保存manifest的checked_date固定本地日期`2026-09-30`，不把重播時間冒充新取得時間。

| 保存檔／來源URL | 實算 SHA-256 |
|---|---|
| leaderboard.html · https://artificialanalysis.ai/leaderboards/models | `b030c6f00885a629ab46d6ec83ea06fd5ecb8b828f91721f23bfa6b4a46df648` |
| grok_release.html · https://artificialanalysis.ai/models/releases/grok-4-7 | `ad8fe1931725ae60da1e892f8a605271df9b317fbf2a4d7b03ebec32c8752af4` |
| muse_release.html · https://artificialanalysis.ai/models/releases/muse-spark-1-3 | `0c95c78bdbbce4f6677cade03e8de0430944659314e9530e9e631eba7dcba07d` |
| meta_pricing.html · https://dev.meta.ai/docs/pricing-rate-limits | `f250be41b52e399c692fce83adea17c756d4242dc16b88213203b3669b3a23f6` |
| models.html · https://dev.meta.ai/docs/models | `9c53e7c7b4ded4bfd571f835d42cf1c618916a0dab496c1285e8c074c1e18eb8` |

### 保存9/30取數／v2對比（實際pool，不套9/26名單）

`refresh_snapshot(... previous=原runs/2026-09-26-general-grok16/public_candidate_source_map.json, fetch=保存bytes)`成功；原map的153 public slugs作精確P，非本次map自證。common `validate_fresh_inventory`以新policy、raw/parsed/hash evidence及獨立前次P驗證PASS；此本地直接producer檢查不冒稱已驗hosted Git predecessor/publication鏈。

- observed686＝retired420＋observed_unusable162＋usable_paid104；tracked105；付費CSV105＝104 public＋1 Contributor xhigh；來源排除582。v2 statuses105＝excluded90＋cut6＋final9；chain15。64個前次來源退出caveats（63退役＋1缺價）於Markdown／HTML皆經解escape逐項對比，source-only exits未造數字cost或status rows。
- MiniMax-M2.7精確slug `minimax-m2-7`：retired／deprecated、不在paid或tracked。Inkling xhigh精確slug是`inkling`（不是`inkling-xhigh`）：observed_unusable／missing_task_cost，不在paid、仍tracked，不沿舊價。兩者在CSV／paid statuses缺席；來源證據與摘要保持退出理由。
- GPT-6.1 Sol五個paid精確slugs：`gpt-6-1-sol`、`gpt-6-1-sol-high`、`gpt-6-1-sol-low`、`gpt-6-1-sol-medium`、`gpt-6-1-sol-xhigh`。各有自身source row，並非要求全部final。
- 控制參數：18/16/min0/reason=`同版本全候選情境比較`/no cap。來源`2026-09-30`、General v4.3.2 inferred/API basis。JSON ladder、Markdown首表與HTML rank rows身份順序完全一致；envelope validator PASS。
- final9依序：Claude Opus5.5 xhigh／high（僅比較）；GPT-6.1 Sol xhigh／medium／low；GPT-6 Luna max／high／medium／low。兩入口＝`GPT-6.1 Sol xhigh AA-public published-price`／`GPT-6 Luna low AA-public published-price`，均只取final非Claude。

| 本地輸出 | 保存9/30重播 SHA-256 | 固定9/26控制 SHA-256 |
|---|---|---|
| candidates.csv | `478e852ce50cb640992236ff152739d9c0acec5355439024fa97e49453d2f1b1` | `e3916f8405904154f0e1dc648588bb08ce92f483cd616ba9be0ff2e5c726ed22` |
| result.json | `c2c951bfcc61abe5247a4ddc136e69aa91480cbdac3bb4beeaf51d9465cbc76d` | `7d806041b888ba969ba890c3802f9165aceeebf60ecbb9fef161d562498fe8c8` |
| report.md | `522ad48a9088a56844e736dc1c095d831161304112507f1422c206b9da7b98f7` | `dd69bbd1704b6a37f0febc251393f83eb3c4ebe145d28c4ef61d1916fe18ddd0` |
| report.html | `f4f834dc6f4ec85471124f63a35af5bd8c4f506c3f89a137961a9c7a10d0ec7f` | `78794d60f8f421c81e21ba48016d2b12edcbbacaf56bd3ec2cd245dfff721198` |

JSON內execution欄是**本地模擬**（run900、example URL），不是雲端run識別。以上為實際本地產物bytes，不保證不同execution metadata的JSON hash相同。

### 獨立固定9/26控制

原CSV直接走v2 `calculate_snapshot`／`make_envelope`，不fetch、不consult今天deprecated；18/16/min0/no cap。155 statuses／154 usable identities／19chain／10final，兩入口精確為`GPT-6 Astra xhigh AA-public published-price`及`GPT-6 Luna low AA-public published-price`；Muse Spark1.3 Contributor max唯一不可用身份excluded，source_dates仍`[2026-09-26]`。JSON／Markdown／HTML身份順序MATCH，無來源退出摘要，原CSV bytes及全部75保護物件不變。全suite亦覆蓋固定Git runner、舊／新source重算及local bare publication，並非新的hosted驗收。

### 獨立task覆核與修正裁定

| Task | Reviewed range／reviewer | 最終verdict |
|---|---|---|
| 1 | 3e539b9..152ff0a · ses_f0efc1a1fffemHFc8n2f273x34 | spec compliant／quality approved，0 issues |
| 2 | 152ff0a..207d1d1 · ses_f0eebb61bffeeyLrh0Fq2AAA3I | spec compliant／quality approved；expected-stderr Minor於Task3解決 |
| 3 | 207d1d1..b27ee66 · 初review ses_f0ec081d9ffeAb3WJhsbiCy3eN；再review ses_f0e9aeb49ffeCS4jrQN3Nxopjg | 初2 Important＋output Minor；6b37e66..b27ee66修正後0 open，spec／quality approved |
| 4 | b27ee66..387fb0f · ses_f0e8da644ffeIvjg7nf4p0jL82 | spec／quality approved，0 issues |
| Issue2 | 387fb0f..473b0b8 · ses_f0e7c2edbffeowXUtEJOEXhser | spec／quality approved，10 observations逐項人工核對，0 issues |

Task5 worker不作整條分支最終verdict，該覆核仍待控制端；各review原報告保留於同scratch。

以下保留controller所有`Ruling:`原文及reason/cost，不讓ignored scratch清理丟失裁定：

1. Ruling: Task3 will pin product checkout's trusted local origin/main once at execution-start in refs/bridge/approved-main, alongside the frozen results ref, and authorize product policy blobs against that explicit commit instead of detached executing HEAD — the spec permits queued legacy products to consume newer approved refresh evidence, but neither a result map nor results reachability grants main authority — cost if wrong: direct local fresh consumers must now supply the pinned approved-main ref, and an unavailable authority fails closed rather than publishing; main history changes must be reflected only by a new execution context.
2. Ruling: add tests/test_bridge_window_integration.py to Task3's file map and permit narrowly scoped equivalent caller/setup migrations if the full suite exposes more — new guarded publication necessarily invalidates old fake-product/no-context fixtures, and preserving meaningful historical assertions is safer than weakening product guards or parking the task — cost if wrong: test-only setup changes require task/final review, with fixed historical selector assertions and protected bytes retained.
3. Ruling: preserve the released old workflow's no-new-flags CLI through a narrowly verified legacy adapter, with any explicit private authority argument coming only from authenticated bootstrap transport's fixed main context — queued old requests load new bootstrap code but cannot acquire new workflow flags or refs retroactively; the spec's compatibility requirement overrides the earlier private-helper sketch while the untrusted-output guard remains — cost if wrong: extra compatibility plumbing needs focused old-wire tests, and a source product outside that fixed authority must fail closed or be retried rather than silently accepted.
4. Ruling: persist a minimal fixed predecessor Git locator in new refresh source evidence, verify it against independently frozen execution context at publication, and resolve it against immutable approved older evidence in both source readers to derive original P; keep reconciliation's six fields and request/result schemas unchanged — the plan's reader sketch omitted independent original P and allowed coherent tracking forgery, contrary to the spec — cost if wrong: new source maps need this small locator and recursive predecessor validation adds Git reads; use cycle/ancestry checks and memoization where appropriate, never copy old source pages or use today's pointer as original context.
5. Ruling: share one read-only authenticated transport facts helper between prepare and the legacy CLI adapter — repeating the gate was permitted by earlier sketch but duplicates security-relevant decisions — cost if wrong: focused transport/legacy tests must catch any changed diagnostics or handoff behavior; externally visible transport contract must remain stable.

### Issue2独立10-case routing GREEN（不是取數驗收）

Blind consumer `ses_f0e804a28ffeFApojC6QT1JvLV`只讀instructions／contract／原inputs，未讀期待或baseline；controller人工檢查responses與ordered actions。policy `473b0b8`；所有action均模擬字串、零Chat/GitHub寫入。

| Case | After observable behavior／evidence lines | 結果 |
|---|---|---|
| a historical shorthand | recompute；固定path/9月26日/不含快照後新模型於5，announcement7早於writes10/12，無重問 | PASS |
| b latest-model shorthand | refresh及acquisition disclosure20/22，無pinned-source field24，writes25/27在揭露後 | PASS |
| c latest without floor | 只問未批准refresh floor/reason35/37，零writes38，不靜默繼承 | PASS |
| d explicit historical | recompute path/date/consequence44/46早於writes49/51，不強制fresh或問答循環 | PASS |
| e explicit refresh | acquisition disclosure58/60早於writes63/65，無source_snapshot62 | PASS |
| f incompatible fixed/new data | conflict72、問intent、零writes75，不混快照 | PASS |
| g pending continuation | 原exact request/run81/85，零新增／重複writes87 | PASS |
| h HTML lookup | 只讀locator93–98，不宣稱CI／attachment／website | PASS |
| i new code not new data | recompute actual path/date/no-new-model104/106早於writes109/111，Grok20保留108 | PASS |
| j recompute conclusion | source9月26日緊鄰anchors118/125，區分9月30日completion與來源，不新CI | PASS |

10/10 bounded sample PASS。Baseline a/d/i雖route正確但漏了寫入前actual path與快照後新模型不會出現後果；after兩項均可見。b/c/e/f/g/h/j非回歸controls保持相容。這是OpenCode離線consumer evidence，不是目標Chat新版end-to-end、settings安裝或統計保證／sandbox普遍限制證明；歷史目標Chat issue2 RED仍保留。

### 剩餘狀態與授權

- 已完成：各task獨立覆核、Issue2 bounded本地routing、Task5本地測試／raw replay／historical／docs自查。
- 待控制端唯一whole-branch review；乾淨後**已授權但未執行**非force main交付，planned新live refresh及其固定recompute、artifact bytes／pointer讀回。沿用18/16/min0/reason=`同版本全候選情境比較`/no cap，不另問一般批准。
- 目標Chat新版摘要／routing實測仍user-owned；settings安裝獨立未確認、無編輯授權。Git交付不等於Chat同步；bootstrap不改。不自動close issues、不force、不網站／Notion。
- 無產品失敗：worker scratch驗證器初次用了錯誤Inkling slug、Markdown欄索引／escape及舊map shape，均屬本地驗證腳本假設，已修正後完整PASS；沒有藉此修改產品/tests或歷史證據。
