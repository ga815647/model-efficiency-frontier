# 固定視窗 v2 發布與雲端驗收帳

## 最新：目標Chat v2端到端驗收通過

2026-09-27使用者帶回Chat實測結報（自報處理時間3m11s），完成recompute提交、查run、固定結果讀回及HTML下載入口。OpenCode另以GitHub API核對下列固定物件，並下載artifact驗雜湊；此增量覆蓋下方「未新增Chat端實測」的較早狀態。

- 產品 `fdabaad096b1dbd4dfcd0ef3a49faf86a980ac0e`；request `ab8e82a1-b8da-48af-b5f0-9ec1c6541caa`；request commit `12bd4b11b0fe12b0f3dbe70fa8eb0473f5822cbc`，唯一parent為產品、唯一added path為對應request JSON。
- [run 36355372202](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36355372202)，attempt1、push、success，head_sha／branch逐項相符。
- 固定publication `a9b3361f7aa6aba98a9adb337a2aac4d14a156c5`；目錄 `results/ab8e82a1-b8da-48af-b5f0-9ec1c6541caa/36355372202-1/`。
- 公開validator驗result v2、policy `cp-new-high-window-v1`；155 statuses／19 chain／10 final，兩入口Astra xhigh與Luna low；Contributor max明確excluded並含Standard-only理由。
- 參數逐項與request一致：18/16、min0、max_cost=null、理由「同版本全候選情境比較」；source locator為產品commit內9/26固定CSV。JSON／Markdown／HTML含相同final身份。
- 下載artifact `report-ab8e82a1-b8da-48af-b5f0-9ec1c6541caa-36355372202-1`，HTML SHA-256與固定Git檔同為 `568c95c19795a6e84c4c2bb98f0da5002d29ca39e48ad8ee67c11157015c5d4b`。

本次改制的Chat端到端驗收完成。當前live fresh缺cost仍為獨立來源問題；Project settings是否實際貼上、Chat直接附件能力不由這次結報推定，也不作此次改制再開驗收的門檻。

日期：2026-09-27。**v2已發布；真實recompute成功，真實refresh按既有來源成本缺口失敗並完成診斷發布驗收。** 不是live fresh成功，也不是產品回歸。
產品／phase A文件 `575f78fbdb8acc0c2ec5c2490cd08a503f8aace2` 已由控制端非force推送main並以GitHub API讀回相同SHA；發布前確認main為祖先。產品基準 `eb3ecf1` 的覆核及phase A文件獨立覆核均已通過。此次是OpenCode控制端雲端驗收，不新增目標Chat端實測或Project settings安裝證明。規格：[固定視窗設計](../specs/2026-09-27-window-knee-production-design.md)；契約：[request v1／result v2](../../contracts/chat-ci.md)。

## 本地實作與覆核

- Task 1–5已實作選擇核心、final-only兩入口／升級／B診斷、v1/v2相容、共用Markdown／HTML與預設v2切換。
- 本地SDD覆核紀錄：`.superpowers/sdd/2026-09-27-window-knee-production/` 下 `task-1-review.md`、`task-2-review.md`、`task-3-rereview-1.md`、`task-4-rereview-evidence.md`、`task-5-review.md`。此為控制端本地證據目錄，非遠端發布路徑。
- 發布前全產品覆核發現v2 validator可接受偽造但內部一致的不可用Contributor max推薦；`eb3ecf1`增加v2身份可用性guard及正反測例，`prepublish-rereview.md`確認已解決，無新增Critical／Important問題。v1歷史結果保持可讀。
- 修補後紀錄：result contracts **27/27**、selection **27/27**、bridge **98/98**、full **229/229**；詳見本地 `prepublish-fix-report.md`。完整測試有既有missing-config案例預期警告 `/nonexistent/opencode.json`，無失敗。
- 文件階段核對 `bridge/result_v2.py` 的 `_COMMON`／`_SUCCESS`／`_ROW_FIELDS` 及trace、anchors、upgrade、B effects鍵；request保持五個parameters。workflow實際仍以 `efficiency-run/**` push及 `bridge/requests/*.json` 觸發，無需改配置。
- 文件階段重跑 `python3 -m unittest discover -s tests`：**229 tests，35.747s，OK**（同一既有預期警告）。`git diff --check`通過；Python核對所有v2共有／成功／row鍵均出現在契約、policy一致，五份文件的本地Markdown連結皆存在。
- phase B驗收文件階段再跑完整測試一次：**229 tests，35.489s，OK**（同一既有預期警告）。固定兩個publication直接Git讀回、公開validator、請求／來源／雜湊／pointer及契約鍵核對通過；27個本地或固定Git文件連結已核對，未重新提交雲端請求。

## 固定快照與OAT證據（非新取數）

來源：`runs/2026-09-26-general-grok16/candidates.csv`；SHA-256：`e3916f8405904154f0e1dc648588bb08ce92f483cd616ba9be0ff2e5c726ed22`。參數GPT18／Grok16、min_score=0（使用者確認同版本全候選比較）、max_cost=null；公開來源版本推定v4.3.2，不混認證API v4.3。

155原始paid稽核＝136 excluded（含不可用Muse Spark1.3 Contributor max）＋9 cut＋10 final；154可用身份→19 CP鏈點→10保留點。final為Claude Opus5.5 xhigh（僅比較）、Astra xhigh／medium、Sol max／high／medium、Luna max／high／medium／low。兩入口為Astra xhigh與Luna low；全cut winner均為final。這是固定歷史輸入的本地結果，非live候選數承諾。

Task5的本地 `task-5-oat.py`／`task-5-oat.json` 保存1,232個production/probe對照情境。final身份與trace winner／removed順序完全一致；strength比較使用Python `math.isclose(abs_tol=1e-12)`，同時保留預設 `rel_tol=1e-9`，不是僅絕對容差。選擇比較本身未加容差。各308情境的非Claude名單改變數：Score±0.1＝2、Score±0.25＝3、Cost±1%＝0、Cost±5%＝2。Astra high+0.25仍改選；原max+0.25／xhigh−0.25不改非Claude名單。此為敏感度證據，不是可靠度機率。

## 本地HTML瀏覽器證據

控制端Task4使用真實Chromium驗證；本文件階段回讀保存的 `/tmp/opencode/window-knee-review/browser-acceptance.json`（未冒稱重新跑瀏覽器）。1280／390px下document與body寬度皆等於viewport，兩卡呈2欄／1欄，10個ladder rows，六個table wrappers皆 `overflow-x:auto`。僅載入本地file URL，external requests均為空。

控制端已目視 `task-4-1280-viewport-font.png`／`task-4-390-viewport-font.png` 的中文字與卡片布局；`task-4-rereview-evidence.md`關閉原瀏覽器證據缺口。樣本 `/tmp/opencode/window-knee-review/task-4-window-report.html` 使用fixture合成commit定位，僅本地renderer驗證，不是Git發布或artifact比對證據。

已知非阻擋限制：renderer中性support理由概稱CP tie-break，但中性0也可能勝過負strength而非真正平手；數值／選檔不因此改變，覆核已記錄延後。不能將此文字解讀為所有中性勝出都經CP平手。

## 真實雲端請求與固定讀回

控制端只提交一個recompute及一個refresh。請求原文／bytes雜湊保存於本地 `/tmp/opencode/window-v2-requests.json`，關聯驗證摘要在 `/tmp/opencode/window-knee-review/cloud/verified.json`；這些不是遠端發布路徑。控制端核對每個request commit唯一parent等於上述產品SHA，唯一新增檔為 `bridge/requests/<request_id>.json`；Actions為push事件，head_sha／head_branch／attempt逐項吻合。兩份固定result均通過公開 `bridge.result.validate_envelope`，request/product/run/operation/parameters逐欄相符。

共同請求：`schema_version=1`；`product_sha=575f78fbdb8acc0c2ec5c2490cd08a503f8aace2`；五個parameters精確為 `gpt_factor=18`、`grok_factor=16`、`min_score=0`、`min_score_reason="用戶確認：同版本全候選情境比較；固定視窗正式改制驗收"`、`max_cost=null`。result均為 `schema_version=2`。

| 關聯欄位 | recompute | refresh |
| --- | --- | --- |
| request_id | `04fce363-c20c-4832-bd34-dc0117239ff4` | `bf70e74b-bd05-424c-9afd-5b8258bdffb9` |
| created_at | `2026-09-27T18:34:13.696944+00:00` | `2026-09-27T18:34:15.434770+00:00` |
| request branch | `efficiency-run/04fce363-c20c-4832-bd34-dc0117239ff4` | `efficiency-run/bf70e74b-bd05-424c-9afd-5b8258bdffb9` |
| request_commit_sha | `8394d2e073eecb5869f2d386f51a137f660eaaa5` | `86d1fe9cafb210fb9fbcd415b53c710e09180821` |
| request bytes SHA-256 | `b7ae25fd29a44950d9eb024e881e7ae2ebd99930c46fc521f3cb5ab327ffaaa0` | `b6ef6b6a5dc82759649162c38e31036710f10358ea7ec86f88b69507047a0094` |
| run URL／run_id | [36341140428](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36341140428) | [36341142058](https://github.com/ga815647/model-efficiency-frontier/actions/runs/36341142058) |
| run_attempt／Actions conclusion／result status | `1`／`success`／`success` | `1`／`failure`／`failed` |
| 固定publication SHA | `912e9e1df03a2e9d829d6a5c5d06b67d0e1a8a3d` | `667062064abc45e467b1058e3565d360018f0a4f` |
| 精確result_path | `results/04fce363-c20c-4832-bd34-dc0117239ff4/36341140428-1/result.json` | `results/bf70e74b-bd05-424c-9afd-5b8258bdffb9/36341142058-1/result.json` |

### recompute成功、來源與三種輸出一致

[固定result.json](https://github.com/ga815647/model-efficiency-frontier/blob/912e9e1df03a2e9d829d6a5c5d06b67d0e1a8a3d/results/04fce363-c20c-4832-bd34-dc0117239ff4/36341140428-1/result.json) 的 `source_snapshot` 精確為 `{"commit":"575f78fbdb8acc0c2ec5c2490cd08a503f8aace2","path":"runs/2026-09-26-general-grok16/candidates.csv"}`；原CSV與相鄰 `snapshot/candidates.csv` bytes相同，SHA-256均為 `e3916f8405904154f0e1dc648588bb08ce92f483cd616ba9be0ff2e5c726ed22`。來源仍9/26歷史公開快照、推定v4.3.2、General／api，不是9/27新取數。

雲端 `candidate_count=155`，155 statuses＝136 excluded＋9 cut＋10 final；154可用身份、19個 `chain_identities`、10個ladder rows，與上列固定快照名單相符。不可用 `Muse Spark 1.3 max Meta Contributor` 為excluded，理由含 `Standard tier only`。逐一核對9個cut的winner均在final，trace與嚴格小於2分距離由v2 validator驗證。

- `anchors.highest_retained_score.identity`＝`GPT-6 Astra xhigh AA-public published-price`。
- `anchors.lowest_retained_cost.identity`＝`GPT-6 Luna low AA-public published-price`。
- 兩者均為final非Claude；Claude Opus5.5 xhigh仍僅比較。
- [固定report.md](https://github.com/ga815647/model-efficiency-frontier/blob/912e9e1df03a2e9d829d6a5c5d06b67d0e1a8a3d/results/04fce363-c20c-4832-bd34-dc0117239ff4/36341140428-1/report.md) 與 [固定report.html](https://github.com/ga815647/model-efficiency-frontier/blob/912e9e1df03a2e9d829d6a5c5d06b67d0e1a8a3d/results/04fce363-c20c-4832-bd34-dc0117239ff4/36341140428-1/report.html) 含相同兩入口及全部10個final身份，HTML有10個 `data-rank` rows；不是由報表重新選檔。
- 同run artifact `report-04fce363-c20c-4832-bd34-dc0117239ff4-36341140428-1` 下載的 `report.html` 與上述固定Git HTML逐bytes相等；兩者SHA-256均為 `8c7bd0e266d128bfd5d8f124107662b0d1d326e8e9622197e59d53694c44c966`。Markdown SHA-256為 `a185ae12bc9e96650297db745fd409a9aa1c0adee6a89224731818b1cb22893b`。

### refresh：已驗證的來源成本缺口，非live fresh成功

[固定失敗result.json](https://github.com/ga815647/model-efficiency-frontier/blob/667062064abc45e467b1058e3565d360018f0a4f/results/bf70e74b-bd05-424c-9afd-5b8258bdffb9/36341142058-1/result.json) 的唯一錯誤碼為 `missing_candidate`，message為 `missing_candidate: https://artificialanalysis.ai/leaderboards/models: inkling,minimax-m2-7`；`source_snapshot=null`、`source_dates=[]`。無ladder／anchors／candidate_statuses／selection_trace／grade_b_effects，亦未發布report.md、report.html或成功candidates.csv。Actions在成功發布診斷後以 `Preserve failed execution as red run` 維持紅色，符合預期失敗語義。

固定失敗目錄共有14個發布檔案（含result與診斷），其中 `snapshot/evidence/` 保存 `leaderboard.html`、`leaderboard_records.json`、`missing_candidates.json`、`version.json`、`sources.json`、`models.html`、`meta_models.json`、`availability.json` 等。[缺值證據](https://github.com/ga815647/model-efficiency-frontier/blob/667062064abc45e467b1058e3565d360018f0a4f/results/bf70e74b-bd05-424c-9afd-5b8258bdffb9/36341142058-1/snapshot/evidence/missing_candidates.json) 記錄：

| 精確slug／原頁名稱 | creator／score | cost_per_task／其他來源狀態 |
| --- | --- | --- |
| `inkling`／`Inkling (xhigh)` | Thinking Machines／`24.9847810999384` | `null`；is_estimated=false、deprecated=false |
| `minimax-m2-7`／`MiniMax-M2.7` | MiniMax／`22.7578150287271` | `null`；is_estimated=false、deprecated=true |

兩行皆存在於前次核准inventory及當次leaderboard；有score與token單價不等於可用task cost。診斷明載model/index消歧仍需人工核對，未證實identity不存在，也不替換effort／ID或靜默放棄候選。延續 [先前三遍核對與來源限制](2026-09-27-chat-readback-and-source-gap.md) 及 [身份修復證據](2026-09-27-contributor-effort-correction.md)；本次不把保存leaderboard診斷冒稱重新完成全部model專頁核對。

官方 `https://dev.meta.ai/docs/models` 保存原頁SHA-256＝`3757469b5dea9eb20bec0b458cac6e135fa4f9f02bbadfe947b6a4ee09d93e82`，與 `sources.json.sha256_by_url` 一致；重新解析與 `meta_models.json` 相符，checked_date=`2026-09-27`。`availability.json.retired_previous_efforts` 保存不可用 `Muse Spark 1.3 max Meta Contributor` 的退出證據。

在refresh固定publication `667062064abc45e467b1058e3565d360018f0a4f`，`latest-success.json.result_path` 仍為本次recompute的 `results/04fce363-c20c-4832-bd34-dc0117239ff4/36341140428-1/result.json`；`latest-refresh.json.result_path` 仍為歷史 `results/118b299c-bddd-4228-be1e-e7cd49403d77/36259726459-1/result.json`。與recompute發布時兩個pointer逐bytes比較相同：此次失敗未推進任何成功pointer。不能用舊fresh或fixture成功替代本次失敗；來源補齊後須按當次真實來源另驗，不硬套154候選。

沿用既有目標Chat提交／查run／成功及失敗讀回證據；未新增Chat端實測。Project bootstrap定位維持，Git指示發布後不需因本次改制重貼；settings安裝狀態不推定。輸出為Chat＋按需單檔HTML，歷史runs與已發布結果不回寫。
