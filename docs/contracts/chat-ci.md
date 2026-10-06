# Chat → CI 契約（request v1／result v2＋歷史v1；2026-09-27）

**10/6 實作與重跑已完成：** [PR #3](https://github.com/ga815647/model-efficiency-frontier/pull/3) 已合併，產品 `1f487a2bddf121acfe3d24993edc2fe2cc8b7b43`；295 項測試、獨立 review 與產品 CI 通過。新固定快照 recompute [37501847653-1](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37501847653) 成功，publication `c3cd3307b956b776334a4668c62b6580a80f864e`。自動 Pages build [37501895642-1](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37501895642) 成功，**deploy job skipped、repo 仍 private、沒有已上線網址**；來源為 2026-09-30，不是新抓來源。詳見本次驗收紀錄。

**2026-10-06 展示與交付增量（優先於下方歷史狀態）**：正式入口改為 GitHub Pages，HTML artifact 為備用；產品實作使用獨立 branch／PR，資料 refresh／recompute 仍走本契約唯一 request bridge，精確 schema、演算法與來源驗證不改。公開檢查通過後才能 public 及部署，目前第三方再散布問題阻擋公開，見 [公開檢查](../publication-review.md)。完整 Pages 權限、流程、allowlist、manifest、正式情境與順序控制見 [部署契約](../deployment.md)。以下過去「私人 repo／不部署／bootstrap 不改」均描述歷史，不再禁止本次已授權網站實作，也不改寫歷史驗收。Git 文件更新不代表 Project Settings 已更新。

**9/30增量已發布／OpenCode雲端驗收通過。** 產品 `c68f3de9423b165b0ed46ca22f9d676cc424c4ee` 最終修正再覆核通過，已非force發布main並讀回；279 tests、75保護物件及9/26控制通過。真實refresh `36698853013-1`、固定該9/30來源的recompute `36699959889-1` 均success：105paid／15chain／9final、Sol6.1 xhigh／Luna low；兩份HTML artifact各自與固定Git報告bytes相同，重算不替換latest-refresh。issue #2已發布的pre-write disclosure有獨立10/10離線consumer GREEN及review，不等於新版目標Chat實測或settings安裝。下方舊產品失敗仍為歷史證據，bootstrap不改，未自動close issues。完整三SHA／來源／hash見 [9/30驗收帳](../superpowers/notes/2026-09-30-refresh-reconciliation-acceptance.md)。

此文件描述**已發布v2實作**；2026-09-27 OpenCode控制端完成雲端重算成功與預期來源缺口失敗診斷驗收，詳見 [v2驗收帳](../superpowers/notes/2026-09-27-window-knee-acceptance.md)；該次未證明live fresh成功，9/30修復後的真實fresh證據見上方增量。新Chat端實測與Chat Project settings安裝仍獨立確認。私人目標 `ga815647/model-efficiency-frontier`；產品 `main`，發佈 `results`；不得同步或恢復已移往用戶垃圾桶父頁的 Notion 頁，不部署網站。`bridge/request.py`、`bridge/result.py`、`bridge/runner.py`、`bridge/publish.py` 和 `.github/workflows/chat-execution.yml` 是精確欄位與驗證的實作來源。

## 工具與三個固定版本

**9/27 能力增量覆蓋下段的「僅可見／待Task8」狀態：**使用者已帶回本私人庫的實際request提交、push run查詢及成功／失敗結果讀回，OpenCode另核對固定Git結果，見`docs/superpowers/notes/2026-09-27-chat-readback-and-source-gap.md`。沿用已通過能力，不重做問卷；下段介面參數仍有效，驗收狀態是9/26歷史。

下列是**使用者提供的 2026-09-26 ChatGPT 端證據**：在另一私人庫實測 `mcp__GitHub__fetch_file(repository_full_name, path, ref, encoding="utf-8")` 完整讀取（不傳 start/end_line）、`mcp__GitHub__fetch(url="https://api.github.com/repos/{owner}/{repo}/commits/{ref}")` 解析 commit、`mcp__GitHub__fetch` GET `/repos/{owner}/{repo}/actions/runs` 與 `/actions/runs/{run_id}`。`mcp__GitHub__create_branch(repository_full_name, branch_name, sha)`、`mcp__GitHub__create_file(repository_full_name, path, content, message, branch)` 僅工具可見，**未在本庫實測寫入**；前者 `sha` 與 `base_ref` 二選一，後者 `content` 是 UTF-8 字串、回傳 `result.commit_sha`。無 workflow_dispatch 或任意 REST POST；`mcp__GitHub__fetch_commit_workflow_runs(repo_full_name, commit_sha)` 僅 PR-triggered 第一頁，不用來找一般 push run。GET-only `fetch` 不能寫入。新私人庫 access、push、讀回仍需 Task 8 驗證。

每次對話任務 GET `/commits/main` 的 `sha` 得**產品 commit**；以該 SHA 完整讀 `chatgpt-instructions.md`、本契約及必要規則。同一任務不在讀到一半改用新 main。`fetch_file` 回傳 `sha` 是 **blob SHA**，不是產品／請求／發佈 commit。`request_commit_sha` 來自 create_file 的 `result.commit_sha` 或 GET 分支 HEAD；結果的 commit 須另 GET `/commits/results` 或查該 run 發佈摘要取得並固定。三者不能互換。

## 請求與使用者意圖

查既有結果只讀，不發 CI；只有明確刷新來源（`refresh`）或對固定快照重算（`recompute`）才提交。因用戶明確要求單次請求而非日常手動 Actions，不以手動按鈕替代缺失的 Git write。係數未另指定時 `gpt_factor=18`、`grok_factor=16`；Contributor 仍 ×1。無全域 floor：新刷新缺 `min_score` 時提案數字、**請使用者確認理由**，不能偷用 0；重算缺 floor 時可從選定的**已驗證來源成功 envelope**明示繼承其 `parameters.min_score` 和 `min_score_reason`，歷史 CSV 無相鄰 envelope 或無法驗證時請用戶確認。`max_cost` 未指定用 `null`；它限制調整後成本。EPS 由產品規則決定，不是請求欄位。

`decode_request(text)` 拒絕重複 JSON key、NaN/Infinity；`validate_request(request, *, branch, parent_sha, changed_paths)` 要求下列**精確**欄位（未知／缺欄拒絕）：

| operation | 根欄位 | 額外欄位 |
| --- | --- | --- |
| `refresh` | `schema_version: 1`, `request_id`, `created_at`, `product_sha`, `operation`, `parameters` | 不許 `source_snapshot` |
| `recompute` | 同上 | `source_snapshot: {"commit":"<40-hex>","path":"..."}` |

`request_id` 是 canonical lower-case UUIDv4；`created_at` 是帶時區 ISO8601 秒（可小數秒；`Z` 或 ±HH:MM）；`product_sha` 是 40-hex commit。`parameters` **恰好**五欄：`gpt_factor`、`grok_factor` 有限正數；`min_score` 有限非負數；`min_score_reason` 非空白字串；`max_cost` 為 null 或有限正數。布林非數字。`source_snapshot.path` 僅 `runs/<segment>/candidates.csv` 或 `results/<uuid>/<run_id>-<attempt>/snapshot/candidates.csv`；對應 `commit` 必須固定，禁止 URL、跳脫、symlink 與未授權 Git 歷史。results 快照必須在同一固定 commit 的相鄰 `result.json` 為**成功 refresh**，路徑 request/run/attempt 和 CSV SHA-256 與 acquired locator 相符，version/inventory 證據亦須過檢。已歸檔 `runs/` 來源目前僅 runner 明確核准 `runs/2026-09-26-general-grok16/candidates.csv` 與其證據；別的歷史檔即使符合語法也不能承諾可重算。

### 寫入前執行身份（對談要求，不新增schema欄位）

按對話中當前已授權的來源意圖判斷，而非以「開始／繼續／跑吧／新版／現在」單字預設operation：

- 明確歷史來源、同一快照改係數／門檻或套新版產品／演算法：`recompute`；已核對且已授權就直接續接，不重做確認問卷。新product SHA不代表新模型資料。
- 最新意圖要求剛發布模型、當前全部模型或重新取得公開來源：已授權refresh參數（含floor＋理由）才 `refresh`，請求不含 `source_snapshot`。缺授權floor／理由或來源意圖未解，停在兩項Git寫入之前，只問缺的決策；固定重算已授權floor不自動授權fresh。要求固定9/26又加入快照後新模型是互斥來源要求，說明衝突後問要哪個，不寫入。
- 已提交且pending的request續接：以原request commit／ID／run及attempt查詢，不建新request。「下載上次HTML」或查既有結果（含「現在」措辭）只讀；沿用有限輪詢、無背景通知及同ID冪等恢復規則。

**在 `create_branch` 與 `create_file` 任一呼叫之前，先給用戶可見執行更新，核對它與將提交的JSON一致。** `recompute`更新必含operation、實際 `source_snapshot.path`、已核對來源日期及明文「不會重新抓取新模型，快照後新增模型不會出現」；例如實際選用9/26archive時：「本次執行 recompute，來源 `runs/2026-09-26-general-grok16/candidates.csv`（2026-09-26固定快照）；不會重新抓取新模型，快照後新增模型不會出現。」以另一成功refresh快照重算須使用該實際path及日期。來源固定commit照原契約核對；此揭露不是第二次確認，已授權就可提交。`refresh`更新必含operation及「將重新取得公開來源」，尚未取得的來源日期不冒稱已驗證；結報才使用實際取得日期。更新在兩次寫入之前可共用一次；若擬提交的operation／來源改變，重新核對及揭露。寫入後或跑完才補註不能替代本門檻。

以下**僅示意 JSON**，UUID、兩個 SHA 和 snapshot commit 必須替換為真實固定值；不是已提交的 production 請求：

```json
{
  "schema_version": 1,
  "request_id": "c49aef65-50dd-4fc2-b2f2-8ecccf4ff24d",
  "created_at": "2026-09-26T12:00:00+00:00",
  "product_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "operation": "recompute",
  "parameters": {"gpt_factor": 18, "grok_factor": 16, "min_score": 0, "min_score_reason": "用戶確認全候選情境比較", "max_cost": null},
  "source_snapshot": {"commit": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "path": "runs/2026-09-26-general-grok16/candidates.csv"}
}
```

建立唯一 `efficiency-run/<request_id>`：`create_branch(..., sha=product_sha)`；GET `/commits/efficiency-run/<request_id>` 驗 HEAD 為 product SHA，然後 `create_file(..., path="bridge/requests/<request_id>.json", content=<JSON字串>, message=<說明>, branch=<該分支>)`。只新增該檔；新 commit 唯一 parent 必等於 `product_sha`，diff 僅 `A bridge/requests/<request_id>.json`。請求分支 push 觸發 Actions；不用建立第二個 request 來「催」一次執行。若 create_file 回應遺失，先以**原分支及精確 path**讀回，GET 分支 HEAD/commit，核對 JSON bytes/identity、parent 與 sole added path；一致則採用已存在 commit 繼續查 run，不一致停止並報衝突。確認未提交且仍指向原 product SHA、原 path 不存在才可用**同一** ID/path 重試；不能盲目重試或用新的 ID 隱藏未知結果。

## 查 run、固定發佈與讀回

**版本範圍：**下方原有「成功 envelope」欄位清單中的 `picks` 及原row欄位描述是**歷史v1**；v2的完整差異與成功／失敗契約見下一節。產品 `575f78fbdb8acc0c2ec5c2490cd08a503f8aace2` 已發布並關聯讀回：recompute `36341140428-1` 成功，固定publication為 `912e9e1df03a2e9d829d6a5c5d06b67d0e1a8a3d`；refresh `36341142058-1` 來源成本缺值失敗，固定publication為 `667062064abc45e467b1058e3565d360018f0a4f`。見 [驗收帳](../superpowers/notes/2026-09-27-window-knee-acceptance.md)。依固定結果的 `schema_version` 判讀，不依pointer名称猜版本。

Contributor 身份修復新增取得證據：`snapshot/evidence/models.html`、`meta_models.json`、`availability.json`，並在 `sources.json` 記官方models來源雜湊。新refresh先驗effort可用性，再換價；已取得的能力證據在成功及失敗發布均驗證。早於修復的成功快照仍可讀取／重算，原CSV保留；修正後計算把其中不可用的Muse Spark1.3 Contributor max明確列為excluded。詳見 `docs/superpowers/notes/2026-09-27-contributor-effort-correction.md` 的發布及驗收狀態。

查 `/actions/runs?event=push&head_sha=<request_commit_sha>`（依 GitHub API 實際支援的篩選，否則分頁列表逐筆篩）並查 `/actions/runs/{run_id}`；要求 `event=push`、`head_sha=request_commit_sha`、`head_branch=efficiency-run/<request_id>`，核對 `run_id` 和 `run_attempt`。不要使用 PR-only helper、單看「最新」run、或以 request ID 字串搜尋冒充關聯。未完成則在可用工具預算內有限次查詢，不能承諾背景通知；保留 ID／run URL 供下次續查。

結果在 `results` 分支 `results/<request_id>/<run_id>-<attempt>/result.json`；若 transport 身分無效且 request_id=null，診斷位置是 `results/invalid-<request_commit_sha>/<run_id>-<attempt>/result.json`，**永非成功 pick**。完成 run 從 job summary 的 publication SHA 或 GET `/commits/results` 取得**發佈 commit**，只以其固定 ref 讀特定 result；即使 results 又前進也不得把另一 attempt 的「最新」當本次。讀 `latest-success.json` 可發現既有成功結果，但須以其 `result_path` 與 metadata 再讀回驗證；`latest-refresh.json` 僅刷新成功。pointer 不是當次 run 成功的證據。若發佈失敗、檔案未見、SHA 不可固定，回報不可用，不拿舊 success 填補。

成功 envelope 由 `validate_envelope` 檢查：`schema_version`, `operation`, `status="success"`, `request_id`, `request_commit_sha`, `product_sha`, `created_at`, `run_id`, `run_attempt`, `run_url`, `source_snapshot`, `parameters`, `source_dates`, `errors=[]`, `benchmark`, `benchmark_version`, `version_status` (`explicit`/`inferred`), `cost_basis`, `eps` (`score`,`cp`), `caveats`, `candidate_count`, `ladder`, `picks`, `candidate_statuses`。每個 candidate row 含 `identity`, `model`, `effort`, `score`, `cost_orig`, `cost_adj`, `cp_orig`, `cp_adj`, `factor`, `grade`, `status`, `reason`, `winner`, `source_url`, `source_date`, `notes`, `is_grok`, `is_contributor`；status `final`/`cut`/`excluded`，`picks` keys `strong`/`middle`/`cheap`（可 null）。驗 `request_id`、request commit、product SHA、operation、parameters、run_id/attempt 與**提交的 JSON 和查到的 run**逐項一致；refresh `source_snapshot={"kind":"acquired","path":"snapshot/candidates.csv","sha256":"<64-hex>"}`，同發佈 commit 讀相鄰 CSV 原始 bytes 計算 SHA-256 比對，並查相鄰 `snapshot/evidence/version.json` 和 `snapshot/evidence/source_map.json`。完整 fresh 來源證據另含 `snapshot/evidence/sources.json`、公開排行榜／release 原頁、`meta_pricing.html`、`meta_pricing.json`、`snapshot/run-notes.md`；涉及 Contributor 時核對當次官方有效 Standard/Contributor 費率、有效 plan／訓練條款、cache-write 假設、同版成本組件與 GRADE-B caveat。若有 `api_diagnostic.json`／`api_envelopes.json`，認證 API 版本獨立陳述，不混公開候選；缺檔不能聲稱 API 已收集。recompute 的 `{commit,path}` 必與 request 相同，固定來源 commit 讀其 CSV 和證據核對，不把 Git blob SHA 當 CSV SHA-256。哈希比對是 acquired 成功宣稱的驗收檢查，不是所有 Git instructions 讀取的全球門檻。不得把 API v4.3 重標為推定公開 v4.3.2。

`status="failed"` 有 `errors: [{code,message},...]`，無 ladder/picks/benchmark 等成功欄位；允許 `request_id=null`（無效 transport 診斷）、`operation/created_at/parameters/source_snapshot` 不完整。先保留 `request_commit_sha`、run URL、錯誤碼與具體缺口，不對無效診斷身分套成功關聯規則，也絕不使用舊 picks。Actions 成功 + envelope 不完整／身份錯誤亦**不可交付**；Actions 失敗時即使有 envelope 只報失敗。

成功同一次計算輸出 `report.md`、`report.html`（自包含單檔）與 JSON。HTML 在該 run 的 Actions artifact `report-<request_id>-<run_id>-<attempt>` 可下載，且 Git `results/<request_id>/<run_id>-<attempt>/report.html` 為耐久路徑；它不是公開 Pages 或網站。Chat 附件能力未驗證，不承諾直接在對話附檔；若無法直接附加，提供對應 Actions run/artifact 下載入口或固定 Git 檔定位，私人庫需授權登入。不要在 Notion 同步。

成功 `recompute` 結報在anchors／推薦結論旁列實際 `source_dates`，明示「固定快照重算，非重新抓取來源」；例如run在9/30成功、來源9/26，推薦仍標2026-09-26快照，不以run時間／新版product commit稱當前新模型。fresh失敗回報實際失敗operation及診斷，不改成重算成功或拿舊結果補位。此對談要求與來源退出caveats同時保留，request v1／result v2／歷史v1及三個固定commit不變。

## result v2 精確欄位與遷移

### 9/30分支來源政策、proof與原始前次追蹤

新產品固定標記 `bridge/refresh-policy.json` 精確為 `{"policy":"observed-inventory-v1"}`；可信policy由已授權固定產品Git commit的ordinary blob解碼，不能從untrusted source map自行宣稱新policy或legacy。標記缺席只有在已驗證的真正舊產品上下文才表示legacy；標記壞掉／未知policy不得降級。舊wire（沒有新flags）adapter仍使用同一唯讀驗證gate核對event、單parent、fixed main、UUID與唯一新增request path，驗證固定handoff及checkout相等後只容許marker-absent舊產品；新產品不能借old-wire繞過proof。

分類優先序固定為 `deprecated → estimated → missing_score → missing_task_cost → zero_cost → usable_paid`。只依當次AA `deprecated=true` 退役；缺欄／null不推定，其他型別拒絕。未退役、非estimated、有有效score但缺task cost者本次排除，不擋其餘有效模型、仍追蹤；不沿用舊價、不代入successor或其他effort。前次追蹤者estimated／missing_score／zero_cost仍以 `present_candidate_unusable` 硬失敗；真正未觀測且無退出依據仍 `missing_candidate`，三遍核對證據照實保留。無paid候選仍 `empty_paid`；floor／cap排空仍可合法空階梯及null anchors。

`snapshot/evidence/source_map.json` 的 `reconciliation` 分離observed（當次全部觀測）、usable（有效public paid）、tracked與retired。精確欄位是 `policy`, `previous_tracked_slugs`, `observed_slugs`, `tracked_slugs`, `retired_slugs`, `status_by_slug`；各slug array排序去重，status值恰為 `state`／`reason`。`tracked_slugs = (P ∪ U) − R`：P為獨立驗證原前次追蹤集合，U為本次usable public集合，R為當次明確retired。paid CSV的public部分／`inventory.slugs`／`source_by_slug`只含U，Contributor仍另按原有規則驗證；缺價及retired留來源證據／退出caveats，不造數字cost或新增 `candidate_statuses` 行。

proof核對同一固定commit的 `leaderboard.html`、`sources.json` SHA-256、精確 `leaderboard_records.json` 重新解析結果、分類／reconciliation／excluded完整對帳、public score與task cost精度、CSV／result／source日期及 `來源退出：` caveats。原有版本、四個Grok／Muse精確crosschecks、官方models證據及Contributor max Standard-only guard不降級。request v1、result v2／歷史v1及row精確欄位全部不變。

production新policy source map另有 **恰好三欄** 的 `previous_inventory`（不是request或result欄位）：

```json
{"product_sha":"<原refresh產品40-hex commit>","results_commit":null,"result_path":null}
```

上例僅示意initial無本地results的null型別，不是已提交證據。有本地results時 `results_commit` 為execution-start已固定的40-hex ordinary commit；有已驗證成功refresh pointer時 `result_path` 為該commit的 `latest-refresh.json` 精確result path。runner在取數前獨立固定此context；publisher獨立解析同一已本地context，要求locator完全相同，retry不以新publication tip替換。無本地results才容許null results commit；initial／archive fallback的path為null。非null commit但null path的recompute-only／orphan固定tree須掃描，若已有成功refresh却缺pointer則拒絕。archive永遠只取原授權產品commit的固定 `runs/2026-09-26-general-grok16/public_candidate_source_map.json`，不接受map自訂路徑或以本次P自證。

固定source reader與前次reader均獨立解析locator並以導出的P驗proof；完整新policy predecessor遞迴驗證，真正legacy predecessor沿用paid-map檢查，不追補新locator。results predecessor必須是publication嚴格ancestor且不含本次result path；驗精確pointer path、ordinary commit／blob並拒絕duplicate JSON keys、cycle、非commit、自指或偽造context。原產品policy與locator固定在result唯一的immutable Git introduction，完整history要求唯一introduction，拒絕ambiguous／reintroduced，不能改寫較晚副本或換另一合法archive來抹掉P；append parent不是P權威。

成功JSON的 `來源退出：` caveats由共享producer產生；Markdown在兩anchors後、階梯前列「本次來源退出」，HTML在cards後以escaped text列同區，完整footer不刪。Chat結論附近同樣原樣揭露：retired是當次排行退役並退出強制追蹤，不等於服務永久關閉；缺task cost不是free或退役，不手估cost。無退出不造空區。新成功refresh的固定重算保留該來源退出；9/26歷史重算不套今天deprecated或重新抓來源。issue #2實際pre-request freshness路由不由本節或fixture成功代替。

`bridge/result.py` 新計算／envelope預設v2，`validate_envelope` 分派合法v1/v2，未知版本與混合欄位拒絕。request仍v1，五個parameters、唯一push分支與三個固定commit不變。新bootstrap可發布排隊中舊product生成的v1；runner、publisher、inventory、固定成功refresh來源及 `assert-success` 皆接受合法v1/v2。`latest-success`／`latest-refresh` 延續append-only與原排序規則；讀到v1不自動觸發重算、不把三picks或表格手推為v2。原Project bootstrap定位不變，無需因本次改制重貼；Git指示發布不證明settings安裝。

v2根欄位（成功與失敗共有）精確為：`schema_version`（2）、`operation`、`status`、`request_id`、`request_commit_sha`、`product_sha`、`created_at`、`run_id`、`run_attempt`、`run_url`、`source_snapshot`、`parameters`、`source_dates`、`errors`。成功為 `status="success"`、`errors=[]`，另有下列欄位，**沒有 `picks`**：

| 欄位 | 語義 |
| --- | --- |
| `benchmark`, `benchmark_version`, `version_status`, `cost_basis`, `caveats`, `candidate_count` | 單一General同版本同basis；原始paid稽核數含不可用身份 |
| `selection_policy` | `cp-new-high-window-v1` |
| `eps` | `{"score":2.0,"cp":0.05}`，frozen第一階段参数 |
| `selection_parameters` | `{"window_score":2.0,"replacement_score":2.0}`，固定產品政策，不是request欄位 |
| `ladder` | 全部final行，Score降序，含Claude僅比較 |
| `anchors` | 恰好 `highest_retained_score`（最強保留檔）、`lowest_retained_cost`（最低情境成本保留檔）；完整row或null |
| `candidate_statuses` | 全部原始paid行，原輸入順序 |
| `chain_identities` | 第一階段CP鏈，原順序，等於final與cut的集合 |
| `selection_trace` | 每步恰好 `step`, `winner`, `strength`, `support`, `removed` |
| `grade_b_effects` | 每項恰好 `identity`, `with_b_retained`, `without_b_retained`；依identity排序的A行保留差異 |

v2 row精確欄位：`identity`, `model`, `effort`, `score`, `cost_orig`, `cost_adj`, `cp_orig`, `cp_adj`, `factor`, `grade`, `status`, `reason`, `winner`, `source_url`, `source_date`, `notes`, `is_grok`, `is_contributor`, `comparison_only`, `upgrade`。同一identity在ladder／anchors／statuses內容一致：

- `final`：reason/winner皆null；`cut`：reason=`within_replacement_radius`，winner指向final且分差嚴格小於2；`excluded`：第一階段未入鏈，保留排除理由、winner=null。不可用Muse Spark1.3 Contributor max必為excluded；不得轉用max分數到xhigh，歷史CSV原樣保存。
- Claude-family `comparison_only=true`，數學照常參戰但不進anchors或升級路線。兩入口只來自final非Claude，可相同；無非Claude時皆null，不從cut／excluded補位，也不反向保送全候選最高分。
- `upgrade` 為null或恰好 `cheaper_identity`, `delta_score`, `cost_multiple`, `delta_cost_adj`；比較下一個較低分非Claude保留行。最低非Claude行、Claude及非final行皆null。
- trace的step從1起；removed按當時Score降序，每個cut只移除一次。support僅 `full_window`／`neutral_missing_window`，後者strength=0，不外插；完整視窗strength可負。剩餘鏈左右各2分log-CP插值後逐次重算，以strength、CP、Score降序及identity字典序選代表；剛好2分不替代，不按相鄰距離串群。最終相鄰分差至少2分。
- B行照常參戰且標GRADE／推導假設；去除全部可用B後以相同兩階段診斷A行是否仍保留，`grade_b_effects`只記狀態改變者，無可用B則空陣列。winner為A仍可能受B插值或第一階段間接影響，不能解釋成單一B唯一因果。硬邊界與逐次選擇仍敏感，非完全穩健保證。

v2失敗 `status="failed"`、`errors=[{"code":...,"message":...},...]`，僅共有根欄位，無ladder／anchors／candidate_statuses／selection_trace等成功衍生欄位；無效transport可有null身份及不完整請求資訊。保留原關聯驗證及失敗處理，不以舊成功補位。當前真實refresh `36341142058-1` 已驗證因Inkling／MiniMax-M2.7 task cost缺值而失敗，錯誤碼 `missing_candidate`；當次原頁、能力／退出及缺值診斷已發布，無成功快照或報表，兩個成功pointer皆未因失敗推進。這是既有來源缺口，不是live fresh成功或產品回歸；修算法不授權略過候選或沿用舊價。後續新的真實fresh結果仍須逐次驗收。

JSON、Markdown與HTML消費同一主結果，完整呈現Grok／Contributor狀態、cut/excluded理由及B影響；renderer不重新選檔或抓來源。歷史輸出不回寫，新結果固定於新的request/run路徑。v2成功refresh可作後續固定重算來源，v1成功refresh仍可讀／重算，所有來源hash、版本、inventory及能力證據檢查延續。
