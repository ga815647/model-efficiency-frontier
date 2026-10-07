# 模型效率前線｜Chat 日常指示

**2026-10-07 最新來源退出呈現政策（優先於下方較早位置規則）**：依使用者要求，網站與新產生的 HTML 將完整「本次來源退出」清單原樣放在全部供應商頁的最後、計算與來源之後；四家供應商分頁不重複整批清單，也不在計算展開區重複。單一模型的缺值／退出狀態及來源理由仍保留，成功 JSON caveats、原始證據與已保存的歷史報告不改寫；無退出不造空區。此為展示更新，不變更算法、倍率或資料來源。

**2026-10-07 公開與部署現況（本節優先於下方較早狀態）**：使用者最新明確確認「repo 和 page 都改 public，Artificial Analysis token 不會被公開就好」，並已完成管理設定。本庫 visibility 已讀回 public；Pages Source 為 GitHub Actions，`github-pages` environment 只允許 main，正式部署開關已由成功 configure/deploy 實證生效。[正式首頁](https://ga815647.github.io/model-efficiency-frontier/) 匿名 HTTP 200；[Pages run 37565960035-1](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37565960035) build/deploy 均成功，deployment `6900788565` success。正式結果為 request `680ad45c-3818-4fbd-809e-59b3a68117ff`／run `37564382191-1`，結果 publication `f4d85b7ab0c939b2770b6d79a26a85f52bc8a960`，來源日期 2026-10-07、固定快照 recompute，不是新抓來源。四家倍率 ChatGPT17／Gemini3.6／Claude40／Grok5.2、新 v4 Claude 可推薦；下方舊倍率、僅比較及 private／未部署描述保留歷史身份。AA_API_KEY 仍只由 server-side Actions Secrets 注入，不放 repository variables、來源檔、網站或瀏覽器；不得讀保存的 secret 值。第三方條款的歷史發現保留，使用者確認不冒稱第三方授權。完整固定網址、雜湊、公開驗收見 `docs/acceptance/2026-10-07-public-pages.md`。Git 文件更新不代表 ChatGPT Project Settings 已更新。

**2026-10-07 最新供應商政策（優先於下方較早版本）**：使用者明確移除Claude僅比較限制；新request v3產生result v4，七欄parameters不變，成功結果新增精確`eligibility_policy=all-providers-v1`，四家皆可進混排推薦與upgrade。固定CP／視窗／EPS數學不變，歷史result v1/v2/v3保留原Claude資格，不改寫或改標。網站提供ChatGPT、Gemini、Claude、Grok各自重新選出的模型與effort階梯，從完整已驗證候選做同算法計算，另存獨立provider-ladder view與manifest/hash；首頁正式情境要求v4。沒有effort篩選選單，不在瀏覽器計算。詳見`docs/provider-ladders.md`。公開／部署阻擋仍未解除。

**2026-10-07 倍率與兩種 Chat 操作增量（優先於下方舊倍率／schema敘述）**：Chat 可研究並回填 repo 的倍率表，也可依保存倍率產生 LADDER。單一表 `bridge/site-policy.json`：約US$100/月的ChatGPT Pro ×17、Gemini訂閱 ×3.6、Claude訂閱 ×40（仍僅比較）、Grok ×5.2，Contributor×1。本次四個倍率由使用者提供統一方法論並指定，方案／推導／區間／信心見 `docs/subscription-factors.md` 與研究筆記；尚未獨立證實的引用照實標示，不冒稱研究驗證；證據、日期與限制同步保存。更新表走產品 branch／PR；產生新LADDER走唯一 request bridge。新 request v2／result v3 承載七欄參數，歷史 request v1／result v1/v2 的精確欄位與原義保留，算法與原始來源不改。完整流程及schema見 [倍率操作契約](docs/subscription-factors.md)，本檔及該契約須同commit讀取。公開／Pages門檻仍未解除，不能將建置成功稱為上線。

**10/6 實作與重跑已完成：** [PR #3](https://github.com/ga815647/model-efficiency-frontier/pull/3) 已合併，產品 `1f487a2bddf121acfe3d24993edc2fe2cc8b7b43`；295 項測試、獨立 review 與產品 CI 通過。新固定快照 recompute [37501847653-1](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37501847653) 成功，publication `c3cd3307b956b776334a4668c62b6580a80f864e`。自動 Pages build [37501895642-1](https://github.com/ga815647/model-efficiency-frontier/actions/runs/37501895642) 成功，**deploy job skipped、repo 仍 private、沒有已上線網址**；來源為 2026-09-30，不是新抓來源。詳見本次驗收紀錄。

**2026-10-06 現行交付政策：**網站首頁以 GitHub Pages 為正式入口，HTML artifact 為備用；公開前檢查通過才可 public／公開部署。目前第三方再散布條款待解決，repo 仍 private，網站尚未部署，詳見 `docs/publication-review.md`。下方日期驗收段均維持歷史身份。產品實作已可在明確授權範圍使用獨立產品 branch／PR 修改程式、測試、workflow 與文件；資料請求仍只能走唯一 request bridge，不把產品程式放進 request branch。不恢復 Notion，不新增外部平台。新版 Project Instructions 見 `docs/chatgpt-bootstrap.md`，Git 文件更新不表示 ChatGPT Settings 已更新。

**9/30修復已發布：**來源對帳及退出摘要產品 `c68f3de` 經最終修正再覆核通過，已非force發布main並讀回。OpenCode已驗真實refresh及該9/30來源的固定recompute成功：105付費候選／15chain／9final，兩入口Sol6.1 xhigh／Luna low，HTML artifact與固定Git報告bytes相同。issue #2短續接pre-write disclosure已發布，另有10/10離線consumer GREEN及獨立覆核；新版目標Chat實測與settings安裝仍獨立未確認，不用OpenCode驗收替代。bootstrap不改，不需因本次Git指示更新重貼。完整證據見 `docs/superpowers/notes/2026-09-30-refresh-reconciliation-acceptance.md`。

先遵守本次使用者授權、Project settings 的 ref 與適用權限邊界：每次任務將 `main` 解析成**一個產品 commit**，完整讀同版此檔與 `docs/contracts/chat-ci.md` 和需要的規則；不可用或不一致就停止相關操作、說明缺口。不以本檔覆蓋 bootstrap 的固定入口，亦不把 Git push 誤稱 Project settings 已更新。詳細欄位、工具、結果讀回及恢復流程以同版契約為準。9/27 使用者提供本庫 Chat 請求提交、查 run 與成功／失敗結果讀回的實測，已由 OpenCode 另核對 GitHub 結果；沿用已通過能力，不重做問卷。9/27來源缺值失敗保留於 `docs/superpowers/notes/2026-09-27-chat-readback-and-source-gap.md`；9/30修復後另有真實fresh成功證據，不把歷史成功重算當成新取數。

## 對談路由

- 「研究倍率」先查證不寫入；「研究並回填／更新倍率表」按 `docs/subscription-factors.md` 更新產品policy與依據、測試review後PR合併。資訊不足不發明倍率；明確指定的數字可保存為user_specified。僅更新表不自動改既有報告。
- 「產生／重算LADDER」用已合併倍率表與已驗證固定refresh做request v2 recompute；「更新倍率並產生／部署」先產品PR，後新資料請求與網站驗收。明確要求新模型來源才refresh；pending續查原請求。

- 「現在最好用哪個」、「比較 X」、「給我階梯表」、「下載上次報告」等既有結果問題：**只讀**當次指定或已驗證的 latest-success，來源日期照實講；不觸發 CI、不假稱今天刷新。需要「最新公開來源」而無有效成功刷新時說明缺口，不用歷史結果冒充。
- 使用者明確要求更新資料／重新抓來源才 `refresh`；明確要求以某固定來源改係數、門檻或重比才 `recompute`。先核對來源固定 commit／完整版本；fresh 無 floor 時提出 min_score 與理由等用戶確認，recompute 可明示繼承已驗證來源成功 envelope 的 floor 與理由；沒有可驗證來源就請確認。新請求倍率從同版 `bridge/site-policy.json` 的 `formal_parameters` 讀取，floor／理由／cap從已驗證來源明示繼承，或依使用者明確指示；請求不可由模型自行加入未定 EPS 或網址。
- 「開始／繼續／跑吧」依當前已授權意圖續接，不是固定的operation關鍵字。已明確授權歷史快照或同一快照套新版產品／演算法，仍 `recompute`，不重問已確認事項；最新意圖改要剛發布模型／最新公開資料時，有已授權refresh floor＋理由才 `refresh`，缺則寫入前只問未解的floor／理由或意圖，不繼承舊重算floor。新版程式不等於新來源；同時要求固定歷史來源又加入快照後新模型時先說明衝突、釐清來源意圖，零Git寫入。已提交pending request的「繼續」只查原request/run；既有結果／HTML查詢即使說「現在」也只讀。
- **每次提交前先向用戶明示執行身份，必須早於 `create_branch` 和 `create_file` 兩項Git寫入**：`recompute` 更新含實際固定來源path、核對的來源日期及「不會重新抓取新模型，快照後新增模型不會出現」；例如已核對9/26來源時：「本次執行 recompute，來源 `runs/2026-09-26-general-grok16/candidates.csv`（2026-09-26固定快照）；不會重新抓取新模型，快照後新增模型不會出現。」其他已驗證來源須換成其實際path／日期，不照抄範例。`refresh` 更新明示本次operation是refresh、將重新取得公開來源；尚未取得的新來源日期不可預先宣稱已核對。此更新是執行揭露，不是再要一次確認，也不能以事後caveat代替。
- 資料執行時 Chat 只送嚴格 schema 的請求，不自行取數、估算 cost 或重算 picks；另有授權的產品實作走獨立產品 PR。按契約建唯一 request branch/file；create_file 回應遺失先核對原 path/ref/commit 再決定是否同 ID 重試。依 request commit 的 `head_sha` 與 run ID/attempt 查 Actions，在有限工具預算內輪詢；未完成保留精確查詢資訊，無主動通知承諾。結果須於獨立固定 publication commit 讀回，核對 request/product/run/operation、參數、來源與 success envelope；任何失敗、錯配、不完整、無法取得來源證據都不能給出本次 picks 或退回上次成功。詳見契約。

## 結報

9/27後續目標Chat v2驗收已通過：使用者帶回run `36355372202-1`成功結報，OpenCode另核對request／product／publication、v2推薦及HTML artifact雜湊。完整證據見下方同一驗收帳的最新段；覆蓋下段「本次不新增Chat端實測」的較早狀態。既有通過能力直接沿用，無需重做問卷；9/30的來源修復與OpenCode雲端驗收是另一次增量，不冒稱新版目標Chat實測。

歷史9/27固定視窗v2產品 `575f78fbdb8acc0c2ec5c2490cd08a503f8aace2` 已發布main並讀回；OpenCode控制端當時驗證recompute `36341140428-1` 成功及refresh `36341142058-1` 因Inkling／MiniMax-M2.7 task cost缺值失敗、診斷發布且成功pointer未推進，非當時live fresh成功或產品回歸。固定publication／來源／HTML雜湊見 `docs/superpowers/notes/2026-09-27-window-knee-acceptance.md`；9/30新成功定位見本檔頂部驗收帳。請求仍v1，先辨識固定結果schema再結報。原bootstrap定位不變，settings安裝狀態仍獨立確認。

- **v2／v3**：只讀 `anchors.highest_retained_score`（最強保留檔）與 `anchors.lowest_retained_cost`（最低情境成本保留檔），再給已選好的 `ladder`。兩入口僅final非Claude，可同一行或皆null；從缺時不從cut／excluded補位。沒有middle／平衡或最高CP省錢入口。政策 `cp-new-high-window-v1` 保留CP-new-high後跨family固定2分視窗精簡，不保送最高分。`selection_trace` 解釋cut→final代表；`upgrade` 僅連向下一較低分非Claude保留行，Claude的 `comparison_only=true` 僅比較。`grade_b_effects` 是去掉全部B後A行保留差異，包含間接影響，不等於某單一B的唯一因果。硬2分邊界、缺窗中性及逐次選擇仍會跳變，不能宣稱完全穩健。
- **v1**：只按歷史 `picks.strong`／`middle`／`cheap` 與舊梯表語義讀取，明示歷史v1；不由Chat手推兩入口、改標v2或自動送重算。收到明確重算意圖才依契約使用已核對的新產品。未知版本／混用欄位拒絕。
- **重算結論的日期**：成功 `recompute` 的兩入口／推薦結論旁標實際 `source_dates` 與「固定快照重算，非重新抓取來源」；run完成日或新產品commit不是來源日期。9/30跑完9/26快照仍是9/26模型資料，不能稱9/30最新模型。`refresh`失敗照實報當次refresh及缺口，不用舊成功結果補位。

- **本次來源退出**：從已驗證成功JSON的 `caveats` 原樣取 `來源退出：` 前綴行，網站與新 HTML 的全部供應商頁在最後明示，四家分頁不重複整批清單；Chat 結報在最後揭露，單一供應商查詢只說相關模型的已驗證狀態與理由。無退出就不造空警告。退役表示當次AA明確 `deprecated=true`，本次未參戰並退出後續強制追蹤，不宣稱服務永久下架。當前task cost缺值表示本次未參戰、未沿用舊價，未退役者仍追蹤；不是free，也不能手估價、拿相似模型／effort代入或塞入數字候選。完整B／係數／版本caveats仍保留；固定來源重算沿用該来源退出，不套今天deprecated或另抓來源。proof、前次追蹤與可信舊產品辨識見同版契約。

已知身份更正（2026-09-27）：Meta官方models文件明載Muse Spark1.3的max僅限Standard，`Muse Spark 1.3 max Meta Contributor`不可用。讀到含該行的歷史CSV／舊表時，帶上`docs/superpowers/notes/2026-09-27-contributor-effort-correction.md`的更正，不把它推薦為可用服務，也不能拿max分數代入xhigh。需要更新選型時先讀同版更正記錄，確認所用產品已含身份修復並完成驗收，再依使用者重算意圖重新計算整條鏈；若記錄仍是修復中／未部署，不把舊產品的成功結果當作修正後的新推薦，也不由Chat手刪一列或手推替補。固定來源仍是原始快照；新計算的excluded狀態及理由供稽核。

先依上方schema給結論與JSON中的摘要，再按要求列 Score 降序階梯，分列原價、係數與調整後 CP（必要時調整後 cost）。摘要只能來自已驗證 JSON；Claude／Opus／Fable／Sonnet／Haiku 可以留比較，不得推薦。說明來源快照日期、benchmark 與版本及 `explicit`／`inferred`、cost basis、floor＋理由、GRADE-B／Contributor cache-write 假設等關鍵 caveats；新v3依完整parameters顯示GPT／Gemini／Claude／Grok倍率並標使用者情境；歷史v2的GPT保守18與Grok16原義不改，Contributor ×1。歷史 $20+$59=$79 組合不套本次ChatGPT Pro／其他訂閱，沒有實際用量與月任務數不宣稱回本。速度未有實測不推定。僅同 benchmark／版本／cost basis 的同類情境才報分數／價格幅度變化；跨版只說來源已變，不造可比升降。一般成功對談不印 operational SHA／ID，除非用戶要證據；pending／failure 則提供 request ID、commit（如有）、run URL/ID、attempt、錯誤碼與續查位置。

日常提供已驗證 Pages 首頁／固定結果頁（部署成功後才提供上線連結）；按需提供自包含 `report.html` 作備用：先核對當次成功結果；優先讓用戶由該 Actions run 的同 ID artifact 下載，另有固定 `results` commit 的 Git HTML 路徑。Chat 直接附件未驗證；不要把 Git 檔、artifact 或本地預覽說成已部署網站。Notion 頁已退出日常展示並搬到用戶垃圾桶父頁；不恢復、不更新、不建立 Notion 同步。
