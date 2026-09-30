# model-efficiency-frontier — workspace 規約

> **2026-09-30 修復已發布／真實fresh與固定重算驗收（最新）**：整條分支最終覆核兩項Important及一項Minor在`c68f3de9423b165b0ed46ca22f9d676cc424c4ee`單輪修正後，唯一限定再覆核全數ADDRESSED、無新Critical／Important；控制端新跑279tests／54.614s／OK、75保護Git物件不變，非force發布main並讀回。真實refresh `36698853013-1` success，request `7b8bad731d447dbb248fc9c0e06f9181b127f370`，publication `0d4a7b8962515930f1ddcf9340c409b83cf5b335`；固定該來源recompute `36699959889-1` success，request `3ac2139cf8f671e58d63c1aaa6e58963588d8362`，publication `4bc6fe50e0d49304312ed281b59f5e0048622c9e`。兩次來源皆9/30、v4.3.2 inferred、105paid／15chain／9final（2Claude僅比較、7非Claude）、Sol6.1 xhigh／Luna low兩入口；五份當次raw SHA獨立核對，JSON／MD／HTML一致，各artifact與固定Git bytes相同。GPT6.1五檔各有paid source row；MiniMax-M2.7 deprecated退出排行及追蹤，Inkling缺cost本次排除但仍追蹤。重算保留latest-refresh原bytes並只推進latest-success，舊refresh物件未改。Issue #2 pre-write guard已發布，有獨立10/10bounded離線GREEN及review；新版目標Chat實測／settings安裝仍獨立待確認，不重做既有connector問卷，不改bootstrap或settings、不自動close issues。下方同日「未發布／待覆核」均為發布前歷史，以本段及`docs/superpowers/notes/2026-09-30-refresh-reconciliation-acceptance.md`為準。

> **2026-09-30 最終覆核單輪修正（最新，未發布）**：整條分支首次最終覆核在`3b865a4`發現兩項Important：真實public量測可被一致重標身份、共同proof未綁sources manifest日期；另有一項Minor過期handoff狀態。已抽出純canonical mapping與producer共享、於共同gate綁六身份欄及canonical Gregorian checked_date；本輪RED後115 covering／279 full tests GREEN（51.897s），75保護Git物件0變更、五原頁SHA核對、9/30重播105paid／15chain／9final與9/26歷史155statuses／19chain／10final控制及CSV／MD／HTML bytes不變。Issue #2仍10/10 bounded離線GREEN及獨立覆核通過，routing行為bytes不改；新版目標Chat／settings未驗收。待控制端限定再覆核，尚非最終乾淨；未發布、未新建雲端request，既有有條件發布／live授權仍由控制端持有。詳見acceptance的Final review fix wave節及`.superpowers/sdd/2026-09-30-refresh-reconciliation/final-fix-report.md`。

> **2026-09-30 Task5本地驗證完成（最新，未發布）**：Task1–4及issue #2均獨立spec／quality覆核乾淨；issue #2有10/10bounded離線consumer GREEN，不等於目標Chat實測。Task5於`473b0b8`新跑276tests／49.915s／OK、75個execution-base Git mode/type/blob物件0變更、protected diff及whitespace exit0。保存9/30原頁五SHA獨立核對及離線取數／v2 JSON／MD／HTML對比通過：105paid／15chain／9final，Sol6.1 xhigh與Luna low兩入口；MiniMax-M2.7 retired退出追蹤，Inkling缺cost本次排除仍追蹤。原9/26控制仍155statuses／154usable／19chain／10final／Astra xhigh＋Luna low，source日期不變。保存重播不是live；下步由控制端唯一整條分支最終review，乾淨後非force main交付及live／固定重算驗收已授權但未執行，不另問一般批准。新版目標Chat／settings仍獨立待確認，無settings編輯或自動issue結案授權，bootstrap不改。詳見`docs/superpowers/notes/2026-09-30-refresh-reconciliation-acceptance.md`。

> **2026-09-30 Task1–4分支本地進度（最新，未發布）**：Task1 `152ff0a`／239測試、Task2 `207d1d1`／252測試獨立spec及quality覆核通過；Task3 `6b37e66`＋`b27ee66`／274測試，原P與重複gate修正後獨立再覆核乾淨，Task2 expected-stderr Minor已解決。Task4只把共享 `來源退出：` caveats投影至anchors後／階梯前並更新契約，待控制端獨立覆核；不改selector、schema或issue #2路由。原P由source evidence精確三欄 `previous_inventory` Git locator及immutable introduction獨立驗證，不從本次map自證。使用者最新要求完成後可去Chat說「開始」，控制端已獲非force發布及live／固定重算驗收授權，須整條分支最終覆核乾淨後執行，尚未發布或新建雲端request。9/27與9/30真實fresh失敗仍為歷史證據；離線成功不等於live成功。issue #2 pre-write guard、新版目標Chat與settings驗收仍獨立待完成；bootstrap不改。詳見 `docs/superpowers/notes/2026-09-30-refresh-reconciliation-acceptance.md`。下方「不等於發布授權」為較早批准範圍，現已有上述有條件授權；無issue結案或settings編輯授權。

> **2026-09-30 issue #1 計畫已批准、開始實作（最新，未發布）**：使用者在五任務計畫審閱及每次retired／missing_task_cost判定說明後回覆「可以了」，沿用Subagent-driven＋TDD，在既有`.worktrees/window-knee`／`docs/refresh-reconciliation`實作；固定execution base為`bcb70e1bf78079facf3525858f15c593bc855a7d`。issue #2按前述bounded短設計另做pre-write freshness guard與對談fixtures／路由驗收，不用#1取數成功替代。進度見`docs/superpowers/notes/2026-09-30-refresh-reconciliation-acceptance.md`；正式產品仍舊v2，尚未發布修復或建立新的雲端驗收request。實作批准不等於merge／push／發布／issue結案授權。

> **2026-09-30 issue #1 書面規格已確認、實作計畫待審（最新，尚未實作／發布）**：使用者在 `2026-09-30-refresh-reconciliation-design.md` 的書面審閱請求後回覆「繼續」，本規格已確認。五任務計畫位於 `docs/superpowers/plans/2026-09-30-refresh-reconciliation.md`，待審閱後沿用既有 Subagent-driven；涵蓋純來源分類、proof／可信policy、新producer与Git／發布接線、退出摘要及整體／雲端驗收。對談及文件批准不等於已修產品或授權force發布；產品仍為既有v2，fresh尚有舊hard guard。issue #2 的bounded短設計另行確認／驗收，不用#1結果替代。

> **2026-09-30 issue #1 政策方向已確認、書面規格待審（最新，尚未實作／發布）**：使用者要求已淘汰的舊模型可退出，不能綁架整批 pipeline，並對「MiniMax-M2.7 當次 deprecated=true 排行退役；Inkling deprecated=false 但本次 task cost 缺值，明示排除、不擋其他有效模型」回覆「好」。新對帳分開 observed／usable／tracked／retired，不沿用舊價、不代入相似身份、保留當次證據；退役退出後續強制追蹤，缺價未退役者仍追蹤。規格位於 `docs/superpowers/specs/2026-09-30-refresh-reconciliation-design.md`，待書面審閱；產品仍是 `0a6ea5d` 的已發布v2，live fresh仍有舊硬阻擋，不能宣稱修復或更新成功。9/30固定失敗原頁五個hash已獨立驗證並重播；未修改產品229測試基線通過。`CONTEXT.md` 只記術語，不取代本檔政策。issue #2 的短續接freshness guard另行處理／驗收，不把#1方向確認當作兩項均已完成。

> **2026-09-27 Chat v2驗收完成（最新）**：使用者带回目標Chat實測，run `36355372202-1` success，product `fdabaad`、request commit `12bd4b11b0fe12b0f3dbe70fa8eb0473f5822cbc`、publication `a9b3361f7aa6aba98a9adb337a2aac4d14a156c5`。OpenCode独立核对请求parent／唯一文件、run关联、v2 envelope、155/19/10、Astra xhigh／Luna low及非法Contributor max排除；下载HTML artifact与固定Git hash相同。本次固定视窗改制已完成Chat端到端验收，不再重做能力问卷。live fresh成本缺值为独立问题；settings安装／Chat直接附件不额外推定。详见v2验收帐最新段。

> **2026-09-27 v2 已發布／雲端重算與失敗診斷驗收（最新，覆蓋下方待審與舊 ladder 政策）**：使用者已批准規格與六任務計畫；Task 1–5 及身份驗證修補、phase A文件獨立覆核通過，產品 `575f78fbdb8acc0c2ec5c2490cd08a503f8aace2` 已非force發布main並讀回。Chat CI 的新計算產生 result v2，request 仍 v1；新路徑為 `bridge/result.py` → `bridge/window_ladder.py`，保留 frozen CP-new-high，再跨 family 以左右各2分 log-CP 視窗逐次精簡（替代距離嚴格小於2分，缺完整雙側視窗為中性0、不外插、不 pin 最高分）。`ladder` 含 Claude 僅比較行；兩摘要 `anchors.highest_retained_score`（最強保留檔）／`anchors.lowest_retained_cost`（最低情境成本保留檔）只取 final 非Claude，可相同或皆null，cut／excluded 不補位。原三 picks、band/pinned 及舊 CLI 僅作歷史 v1 路徑；不得從舊表手推 v2。GRADE-B 照常參戰，`grade_b_effects` 記去除全部B後A行保留差異；不可用 Contributor max 在CP前excluded且仍留原CSV稽核。雲端recompute `36341140428-1` 成功，固定結果commit `912e9e1df03a2e9d829d6a5c5d06b67d0e1a8a3d`：155 statuses／154可用／19 chain／10 final、Astra xhigh／Luna low兩入口，JSON／Markdown／HTML身份一致且artifact與固定HTML bytes相同；仍是9/26固定快照，非新取數。229項本地測試通過。真實refresh `36341142058-1` 仍因 Inkling／MiniMax-M2.7 task cost 缺值失敗，診斷固定於 `667062064abc45e467b1058e3565d360018f0a4f`，成功pointer未推進；這是既有來源缺口，不是live fresh成功或产品回歸。此次為OpenCode驗收，未新增Chat端實測，Project settings安裝仍未確認。新輸出寫新 `results/<request_id>/<run_id>-<attempt>/`，歷史 runs 不回寫。詳見 [v2驗收帳](docs/superpowers/notes/2026-09-27-window-knee-acceptance.md)、[契約](docs/contracts/chat-ci.md)；下方歷史日期條目及流程衝突時以本段為準。

> **2026-09-27 書面規格已確認、實作計畫待審（最新）**：使用者對固定視窗正式規格審閱請求回覆「好」，`docs/superpowers/specs/2026-09-27-window-knee-production-design.md` 已確認。六任務實作計畫位於 `docs/superpowers/plans/2026-09-27-window-knee-production.md`，待使用者審閱後沿用Subagent-driven。計畫涵蓋選擇核心、final-only兩入口／B診斷、v1/v2相容、報表、整合及雲端驗收；尚未改產品程式或切換正式16階。下方「規格待審」為較早狀態。

> **2026-09-27 固定視窗正式規格待審**：使用者對固定視窗改善結果回覆「好」，已整理 `docs/superpowers/specs/2026-09-27-window-knee-production-design.md` 供書面審閱。保留CP-new-high→跨family固定2分視窗精簡；摘要提案只從final非Claude行取最強／最低情境成本，沒有保送原最高分或淘汰行補位。新result v2／request v1、升級比較、B影響診斷及舊結果相容均為本稿待確認內容。尚未批准書面規格／實作計畫，不把方向確認當作已部署；原Pareto草案继续撤回。

> **2026-09-27 轉折公式改善試算（最新，未切正式）**：使用者要求改善極小分差敏感度並複驗。分母floor／smooth及局部chord均未改善整體；較好的候選為剩餘混合CP鏈上左右各2分的log-CP插值增益比，缺完整雙側視窗給中性0、不外插。原Astra max+0.25／xhigh−0.25反例消失，但新增high+0.25會由xhigh＋medium改high。相同全154逐行擾動中，非Claude名單改變數（每組308）由原2／4／0／2變2／3／0／2（Score±.1／±.25、Cost±1%／±5%），只屬有限改善。基準仍9個非Claude原名單，Claude比較行由max改xhigh。證據、未採候選及剩餘敏感性見 `experiments/2026-09-27-cp-chain-regularized/`。尚未批准正式公式、spec或部署；維持CP-new-high第一階段與正式16階。

> **2026-09-27 精簡方向與敏感度（最新設計狀態）**：使用者已接受探討「不到2分可由較值得選的轉折點代表」，不是正式算法／書面spec批准。更正身份後19點鏈的敏感度試算：1.75–2.0門檻同留10點，2.1–2.5少Astra medium；其與Sol max僅差2.042794。逐行Score±0.25假設中，Astra max升0.25會讓第二階段由xhigh／medium改選max／high（第一階段成員不變），故不能宣稱原始斜率轉折公式穩健。建議保留2分替代原則、先處理極小分差放大，再定公式；尚未新增平滑規則或改正式16階。可重現探針及證據見 `experiments/2026-09-27-cp-chain-sensitivity/`；非新取數、非AA信賴區間。

> **2026-09-27 Contributor 身份修復已發布／雲端驗收**：修復 `365e699`＋`3b4313a`＋`d62cfd8` 已隨產品 `076c7ca` 發布main，獨立覆核通過、控制端169測試通過。重算run `36294948064`成功：保留155行歷史稽核、154行可用身份，非法max在CP前excluded，正式仍16階；新推薦規則尚未實施。最新更正重算結果固定commit `bbb5fadaf04633aae0e6849f9fbb74924a5040ad`，路徑 `results/95a3ddbc-5d8d-4985-9c6d-1a73c251e0f4/36294948064-1/`。fresh `36294949623`仍因Inkling／MiniMax-M2.7 cost缺值失敗，已保存models原頁、解析限制及精確舊身份退出證據；不是fresh成功。下段「修復待進行」為修復前歷史，現由本段覆蓋。完整驗收見 `docs/superpowers/notes/2026-09-27-contributor-effort-correction.md`。

> **2026-09-27 Contributor max 身份錯誤（最新資料更正）**：用戶指出 Muse Spark 1.3 Contributor 不提供 max；已直接取得 `https://dev.meta.ai/docs/models`，官方明載 max「available on Standard tier only」。禁止將 Standard max 分數／用量套 Contributor 費率製造可用 identity；`Muse Spark 1.3 max Meta Contributor` 不得推薦或參與新比較。舊快照保留為歷史錯誤證據，不回寫；xhigh 不得代入 max 分數。現行取得程式只驗 model/plan 價格、未驗 effort 可用性，修復尚待進行。排除該行後的歷史情境試算為154候選／19個CP新高點；同一候選轉折法得10點，見 probe 更正段。先前以該行淘汰 Astra medium／Sol max 的結論撤回，不能只從舊結果刪掉 Muse 一列。

> **2026-09-27 用戶最新糾正（覆蓋下方純雙軸改制方向）**：這張表的前提一直是 **Score 由高至低，向下只有 CP_adj 創新高才留**。目前討論要改的是這條鏈上過密檔位的後續剔除／直接推薦，不能擅自取消 CP-new-high 改用全候選 Pareto。用戶不接受最高分必保留，也不接受「近分群一律留最便宜」造成固定選最低分；需要直接選好而非只折疊資料讓用戶自行判斷。`2026-09-27-tradeoff-production-design.md` 已標記需修訂，不可照原稿實作。正式剔除／推薦細則尚未定案；既有已部署數學未改，試版保留為歷史探索。

> **同日比較範圍補充**：使用者明確提醒 Astra 要與 Sol 等其他模型一起比較。第二階段也沿全 family 混排的 CP-new-high 鏈評估，不按模型／family 分組、不保證每家各留一檔。Astra 內部案例只供說明，不能單獨據此定最終推薦；Contributor／Grok 等已入鏈 identity 同樣參與，來源分組及 B caveat 維持。

> **2026-09-27 正式改制方向已確認、尚待書面規格審閱／實作**：使用者已選「正式採用」試版的雙軸支配＋升級代價，並選非 Claude「最高分／最低情境成本」兩個客觀入口，取消原三 picks 的平衡中段與最高 CP 省錢語義。設計見 `docs/superpowers/specs/2026-09-27-tradeoff-production-design.md`；目前部署仍是 v1 舊制，勿把方向批准當作已切換。規格確認後寫計畫，沿用 Subagent-driven。

> **2026-09-27 最新增量（覆蓋下方 Chat 尚未讀寫的狀態）**：使用者帶回目標 Chat 實測，recompute `36282186076` 成功、refresh `36282226673` 失敗；OpenCode 另核對固定結果。Chat 對本私人庫的提交／查 run／成功及失敗讀回已通過，不重做能力問卷。fresh 的 Flight `$undefined` parser 錯誤已修正、覆核並發布於 `0174e98`，本地重播仍受 Inkling xhigh／MiniMax-M2.7 當前 task cost 缺值阻擋；已三遍核對，不靜默移除或沿用舊價。settings 安裝確認與當前 fresh 成功仍不推定。證據見 `docs/superpowers/notes/2026-09-27-chat-readback-and-source-gap.md`。

> **2026-09-27 試版授權**：用戶「試試看」批准以 9/26 固定快照另做升級取捨展示：僅按 Score／Cost_adj 的嚴格支配排除，逐相鄰檔列 ΔScore、成本倍率、ΔCost_adj；2 分只作差異註記／折疊，不作同能力宣稱，不套 5% 購買價值門檻。此為 `experiments/` 診斷試版，不取代正式 ladder／三 picks／frozen 數學，須看過結果再定正式政策。

> **2026-09-26 最新展示／部署狀態（覆蓋下方 Notion 展示／同步政策）**：用戶採 Chat 結報＋按需單檔 HTML，不部署網站。私人 `ga815647/model-efficiency-frontier` 的 `main` 已發布 Chat → CI 實作，Actions 實際重算／fresh／失敗／HTML 驗證完成；但 ChatGPT Project bootstrap 尚待用戶安裝、目標 Chat 的讀寫／結果讀回尚未驗收，因此尚未切換日常 Chat 入口，勿宣稱端到端完成。Notion 已退出日常展示與同步：原頁 `3e539f3f-a67c-810a-9eca-f2de2c0fe1a5` 已搬入用戶「垃圾桶」父頁 `3e639f3f-a67c-8111-a4f9-d682d34f06b7` 並回讀確認，保留內容等用戶手動刪除；不再自動更新／恢復該頁。既有本地 run 快照仍為 SSOT；部署證據見 `docs/superpowers/notes/2026-09-26-chat-ci-acceptance.md`，契約見 `docs/contracts/chat-ci.md`。

> 最新展示 SSOT：`runs/2026-09-26-general-grok16/ladder-extra.md`（2026-09-26 公開頁 **推定 v4.3.2**，GPT ×18／Grok ×16；資料與版本限制見同目錄 `run-notes.md`；唯一 Notion 頁 `3e539f3f-a67c-810a-9eca-f2de2c0fe1a5` 標題更新為「模型效率前線｜番外篇 GPT×18／Grok×16（2026-09-26 快照）」）。原有 v5 ladder／番外篇快照封存不可改；認證 API v4.3 另外留存，不能混入本次公開 v4.3.2 情境。頂層 `README.md` 為入口。

> 定位：這裡存的是**狀態**（每次研究的日期、價格快照、證據、frontier 結果）。
> 流程方法未來穩定後再抽成 skill；本檔是目前唯一的事實來源，流程改了先改這裡。

## 1. 已確認的設計（2026-09-17，用戶確認）

- **2026-09-26 番外篇 GPT/Grok 雙 family 情境（最新批准）**：只改 `scripts/ladder_extra.py` 顯示／情境層。GPT- 仍以用戶個人約 18.9 倍實測保守取 ×18（`--factor`、`--prefix` 舊介面保留）；Grok 模型名稱以不分大小寫、起首獨立 `Grok` 詞匹配（如 `Grok 4.7`、`Grok-4.7`），採 `--grok-factor` 預設 ×16，**此 16 是用戶指定情境，不是個人或 AA 實測**。每行最多一個係數，Contributor 行無論 family 均 ×1；原價、GRADE 與輸入快照不變，按 adjusted cost 重跑 frozen 數學，仍 Score 降序展示。Grok high/xhigh 包括被排除者須完整報狀態。$20+$59=$79 只屬 GPT 訂閱組合，非 GPT 省錢 pick 不得以此推論 Grok 續訂；renderer 不抓資料，顯示來源快照日期而非假稱當天抓取。新同版本 fresh run 可用 `--min-score 0` 作全候選情境比較，需附理由；資料取得、發布及 Notion 同步為獨立步驟，不因 renderer 變更而自動進行。詳見 `docs/superpowers/specs/2026-09-26-ladder-extra-design.md`。
- **2026-09-26 番外篇係數最新修訂（覆蓋下條原 18.9 計算係數）**：用戶要求較保守，GPT- 前綴行現以 `cost_adj=cost_orig/18`、`CP_adj=CP_orig×18` 全候選重比；預設、測試、輸出、Notion 公式一律用 18。來源仍是用戶個人實測約 18.9 倍，18 是保守取整，**不是**實測 18，更非 AA 實測。原 run 快照及原版 ladder 不改。
- **2026-09-26 番外篇最新排序修訂（覆蓋舊 CP_adj 展示排序）**：用戶要求階梯表按 Score 降序（強→弱），本地生成結果與既有 Notion 表均如此展示，編號 1 起由最強排至最弱；CP_adj 僅為效率欄而非排序鍵。frozen 演算法本來即由高分往低分找 CP_adj 新高，不改數學／×18／Contributor 參戰／非 Claude 三 picks；Claude 可列於比較表首行但不推薦。
- **2026-09-26 番外篇展示修訂（展示政策仍有效；原 18.9 計算係數已由上條覆蓋）**：用戶決定 Notion 只展示番外篇，原版退出展示，GPT 不再霸榜時再回看。允許新增 `scripts/ladder_extra.py` 生成 `runs/<run>/ladder-extra.md`：GPT- 前綴行採保守係數 CP×18，全候選重比；原價與 CP_adj 分欄，標明係數來源、公式及 $20+$59 組合。既有 Notion 頁 `3e539f3f-a67c-810a-9eca-f2de2c0fe1a5` 改標題並整頁換成番外篇。本地原版快照留存供日後回看。此為個人使用情境估算，不冒充 AA 實測成本；frozen 數學與 no-Claude 推薦規則維持。詳見 `docs/superpowers/specs/2026-09-26-ladder-extra-design.md`。

- **核心輸出【2026-09-24 用戶決定：frontier retired，recommend-only】【RETIRED 2026-09-24：OMO 脫鉤，ladder 取代；見 docs/superpowers/specs/2026-09-24-ladder-design.md】**：~~descending-Intelligence CP frontier，不是 Top-10 CP 排名。~~ ~~取代政策：唯一 sanctioned 輸出＝`scripts/recommend.py` 的 official-chain three-pick（每角色 head/mid/tail band pick）；frontier 不再生成、不再作為輸出。~~ 取代政策：唯一輸出＝`scripts/ladder.py` 生成的階梯表（`runs/<run>/ladder.md`）。
- **CP 定義**：`CP = benchmark score / Cost per Task`。有 AA 的 Cost per Task 就用它，不自己拿 token 單價粗算。
- **排行單位（identity）**：`Model × Reasoning Effort × Provider × Pricing/Data Plan`（+ 版本快照，見 §4）。
- **Privacy 二元分桶（已簡化）【SUPERSEDED 2026-09-24，用戶決定「不要分桶，不管會不會被訓練，取消以前分桶政策」】**：
  - ~~`private-safe`：找到官方說法稱預設不拿 input/output 訓練，才進此桶。~~
  - ~~`other`：其他全部（含明確訓練、查不到保證、不想查的）。不過度細分，不說謊。~~
  - ~~命名注意：叫 `private-safe (best-effort)`，不叫 `strict no-training`，因為我們不做深度法務查證。~~
  - 取代政策見下一條「Privacy 註記（2026-09-24）」；以下歷史保留不刪，僅作廢。
- **Privacy 註記（2026-09-24 用戶決定：取消分桶）**：privacy 欄保留作純註記（`evidence_url + checked_date` 仍記錄），永不用於分組／分表／過濾 frontier。所有付費行進入同一張合併 frontier 混排。
- **雙邊排名（用戶 2026-09-17 補充）【SUPERSEDED 2026-09-24，同上取消分桶】**：~~`private-safe` 和 `other` 各自獨立算一條 frontier，永不混排。~~
  ~~用戶按需求選邊使用；`mode=all` = 同時輸出兩條 frontier，不是合併成一條。~~
  取代政策：單一合併 frontier（merged single table）；`mode=all` 舊語義作廢，不再分開算、分開表。
- **Free tier**：永不進入數字 frontier。主 frontier 只含付費 route；free/quota 另開 sidecar 表。
- **Benchmark 單一主線（2026-09-24 用戶決定；原「Benchmark 分離」作廢，歷史保留）**：全角色主線＝Intelligence（General）only，單一合併 frontier；Coding runs 歸檔保留、不刪除、不再開新 run、不再參與 picks。~~General Model / Coding Agent 各自獨立 frontier，連 Cost/task 都不跨 benchmark 比。~~
- **Epsilon（anti-noise）**：`eps_score = 2.0` 分，`eps_cp = 5%`。低於此視為 noise，不構成新台階。
- **MVP 參數**：`benchmark_type`、`minimum_intelligence`（必填）、`max_cost_per_task`（選填）。【2026-09-24 清理：`privacy_mode` 已隨分桶取消刪除】
  其餘（provider 白名單、context window）只做顯示或後過濾，不改變 frontier 定義。
- **計算交給腳本【2026-09-24 用戶決定：frontier retired，recommend-only】【RETIRED 2026-09-24：OMO 脫鉤，ladder 取代；見 docs/superpowers/specs/2026-09-24-ladder-design.md】**：~~`scripts/compute_frontier.py` 是唯一合法的 frontier 算法實現，人工不手算。~~ ~~取代政策：`scripts/compute_frontier.py` RETIRED（保留作歷史，不再調用）；`scripts/recommend.py` 是唯一 sanctioned run 輸出（official-chain three-pick），人工不手推 picks。~~ 取代政策：`scripts/compute_frontier.py` frozen 數學（唯一算法實現）＋ `scripts/ladder.py` 唯一輸出，人工不手算。
- **Cost 證據等級（2026-09-17 v2 補）**：
  - `GRADE-A`：AA 實測該 identity route 的 Cost per Task，直接用。
  - `GRADE-B`：AA 實測 token 用量 × 該 plan 官方面價的 documented rescale；notes 必須寫公式 + 假設，frontier 行必須標 `B`；B 級行可參戰，但若它單獨決定台階（淘汰/建立新台階只因它）輸出必須加 caveat。
  - `GRADE-C`：猜測用量 / 第三方估計 / 無來源，禁入數字 frontier。
- **快照衛生（2026-09-17 v2 補）**：每行記錄 `score_source + source_date`（檢索日）；同 run 允許不同檢索快照，但 `benchmark_version` 必須完全一致。前例：Spark xhigh v4.1.1 的 61 / $0.55 禁入 v4.3 run。
- **非價格約束只註記（2026-09-17 v2 補）**：RPM / TPM 配額、ZDR、context window 只做顯示或註記，永不折算成 cost 併入 CP（比照 provider 白名單）。
- **數據換價前例（2026-09-17 v2 補）**：條款含訓練授權的 pricing plan（Contributor 類）預設進 `other`；Standard 類仍需官方不訓練說法才進 `private-safe`。同 checkpoint 跨 plan 必須分行，分屬兩桶。
- **能力五級展示矩陣【RETIRED 2026-09-24：frontier retired，recommend-only；以下歷史保留不刪，僅作廢】**：~~（2026-09-17 v4 補，用戶確認；只做展示，永不進數學）：~~
  - 五級＝用途角色＋當代錨點，不寫死分數：T1 旗艦攻堅／T2 強（旗艦效率）／T3 均衡主力（balanced）／T4 輕量批量／T5 門檻堪用。
  - 生成規則（版本無關，數字每版重算）：錨點＝safe 桶 CP 峰值（kept rows CP 最大者，腳本已算）；級距＝3.5 × eps_score（k=3.5 設計常數，固定；v4.3：3.5×2.0＝7，反向驗證吻合 53/46/39 節奏）；T3 含峰值，上下各一級距展開，永遠五級，填不滿就從缺。
  - 兩桶共用同一把尺（展示對應用），各自 frontier 計算不動（禁令 8）。
  - 錨點搬家條件（2026-09-18 反例覆核：v3→v4 同版本錨點 46→38）：只在出現 CP 更高（過 eps_cp margin）的 kept 行時搬家；同參數重跑不動。搬家＝效率地貌真變，分級跟著重定是正確行為。
  - T 標籤 run-local（2026-09-18）：T3＝「當版 safe 效率最高點」，語義每版為真；跨 run 比的是 identity＋分數，每版附錄記錄錨點，不直接比 T 標籤。
  - B-peak caveat（2026-09-18）：若 safe 峰值為 B 級行，錨點即站推導值上，分級輸出必須標示；目前 safe 全 A，先記不觸發。
  - 外部依據：AA 方法論 95% CI ±1%（eps 2.0≈2σ，級距 7≈7σ）；RouteLLM 以 DP 分 Elo 層（arXiv:2406.18665，分層方法前例）；CheapestInference "compare positions, not scores"（禁令 10 同行背書）；OpenAI 官方選型＝workload 角色制（flagship／balanced／cost-efficient，不寫分數）。
- **eps 抓取規則（2026-09-17 v4 補）**：eps_score＝2×當版 AA 公布 CI；未公布則沿用上一版＋註記；eps_cp＝5% 固定（成本側容忍度）；跑腳本以 `--eps-score` 帶入。
- **角色分組與 official-chain（2026-09-24 用戶確認 landing；2026-09-24 native-group 修訂：ABCD 作廢，official native groups only）【RETIRED 2026-09-24：OMO 脫鉤，ladder 取代；以下整條＋子條歷史保留不刪，僅作廢；見 docs/superpowers/specs/2026-09-24-ladder-design.md】**：~~只用官方原生分組——lanes（`daily-normal`、`geeky-normal`、`geeky-heavy`）、curated agents（`explore`、`librarian`，byte-identical chains）、categories（`quick`、`visual-engineering`、`writing`），不發明角色。chain 原文以 OmO `agent-model-matching.md @ HEAD 60cfa1a41e5534d9c9305d4c3aef71c677da116c（2026-09-24）` 為準；AA 分數僅取自本地 `candidates.csv`，無分數一律標 `無AA分數→退回`，不代入、不推定（不同 ID／不同 effort 不可代）：~~
  - ~~lanes表 `daily-normal`：`…/claude-opus-5-5 (medium)` -> `…/kimi-k3 (max)` -> `…/glm-5.3 (max)`；rung定義 `packages/omo-senpi/src/components/model-profile/builtin-profiles.ts`。~~
  - ~~lanes表 `geeky-normal`：`…/gpt-5.6-sol (medium)`（single；HEAD 60cfa1a 2026-09-24 錨點修正）。舊鏈 `…/gpt-6-sol-fast (medium)` -> `…/gpt-6-sol (medium)`（chain drift，已作廢，見本條 drift note）。~~
  - ~~lanes表 `geeky-heavy`：`…/gpt-6-astra (xhigh)`（single 即 head）。~~
  - ~~curated agents表 `explore` ＋ `librarian`（byte-identical，兩鏈逐字相同）：`…/kimi-for-coding-highspeed (off)` -> `…/gpt-6-luna-fast (low)` -> `deepseek/deepseek-flash (max)` -> `qwen3.7-plus` -> `minimax-m2.7` -> `…/claude-haiku-4-5`（源 `packages/senpi-task/src/agents/builtin/fallback-chains.ts`）。~~
  - ~~categories表 `quick`：`…/gpt-6-luna-fast (low)` -> `deepseek/deepseek-flash (off)` -> `qwen3.6-flash (low)` -> `minimax-m3 (max)` -> `minimax-m2.7 (max)` -> `xai/grok-4.20-0309-non-reasoning` -> `claude-haiku-4-5 (off)`（utility rungs 已展開；源 `packages/senpi-task/src/category/fallback-chains.ts`）。~~
  - ~~categories表 `visual-engineering`：`claude-fable-5-1 (max)` -> `claude-opus-5-5 (max)` -> `…/kimi-k3 (max)`。~~
  - ~~categories表 `writing`：`claude-fable-5-1 (low)` -> `claude-opus-5-5 (low)` -> `claude-opus-4-6 (max)`。~~
  - ~~ABCD presentation grouping（A orchestration／B implementation／C lightweight／D visual+writing）：2026-09-24 用戶決定退役，僅為展示合併，歷史見本行舊文，不再用於收錄／band／pick。~~
  - ~~**OmO role inventory（2026-09-24 用戶指令：inventory 全角色；OmO 源文件不在本 workspace，以上 chain 引文＋`/tmp/omo-picks.md`＋`/tmp/chain-sweep.md` 為唯一證據，不發明角色；chain 逐字列出，Claude 出現處保留原文，禁令 14 只管 picks 不管 mapping）**：lane `daily-normal`（lanes表，orchestration 日常主鏈）／lane `geeky-normal`（lanes表，code implementation 主鏈，現 single rung）／lane `geeky-heavy`（lanes表，code 攻堅單 rung 即 head）／curated agent `explore`（curated agents表，read-only 輕量搜索鏈）／curated agent `librarian`（curated agents表，與 explore byte-identical）／category `quick`（categories表，輕量快鏈）／category `visual-engineering`（categories表，視覺工程鏈）／category `writing`（categories表，寫作鏈）。~~
    - ~~subagent dispatch-target 註記（非 model pick，不進 band 數學，只定語義親和）：subagent `explore`／`librarian` -> `quick`／`explore` affinity（只讀搜索／廉價查閱）；subagent `oracle`／`metis`／`momus` -> `daily-normal` affinity（重量級判斷仲裁／策略規劃／批判覆核，屬 orchestration 級決策）。~~
  - ~~Benchmark 主線：General＝AA-Intelligence-Index-v4.3（唯一主線）；Coding runs 歸檔保留、不刪除、不再開新 run、不再參與 picks；frontier 數學為單一合併表，同 benchmark＋版本內比（禁令 1、10），永不跨 benchmark 合併 score/cost；`A >= B` 不變量已刪除（2026-09-24：原跨 benchmark 比較，單一主線下無意義；歷史見本行舊文）。2026-09-24 picks 前例見 `/tmp/omo-picks.md`【ABCD-era 歷史快照，數字不跨版沿用】（A 51/44/floor 39；B 52/40/floor 40；C 平衡 39/floor 39；D 53/58/47/floor 42）。~~
- **floor 規則（2026-09-17 v4 補；2026-09-24 用戶決定改為動態；2026-09-24 official-chain 版 landing；2026-09-24 one-sided band＋CP-best＋suppression 升級）【RETIRED 2026-09-24：OMO 脫鉤，ladder 取代；以下整條歷史保留不刪，僅作廢；見 docs/superpowers/specs/2026-09-24-ladder-design.md】**：~~floor 不訂全局數字，每 run 按角色動態推導。pick 規則＝official-chain band 版：每角色 band＝`[chain-rung anchor score − 1.0×eps_score, +inf)`（單邊向下，只擋低分不封頂；anchor＝該 rung chain 原文 model×effort 在 candidates.csv 內同 benchmark 同版本 AA 實測 score）；pick＝band 內通過 min/max-cost 的最高 CP 非 Claude 付費行（tie-break：高分優先，再低價優先；CP-best 已確認：anchor ≠ pick 屬設計本意，anchor 只開 band 不保送）；anchor 無 AA 實測→該檔標 `無AA分數→退回`（不開 band，不代入）；floor 檔＝chain tail band pick，tail 無 AA score 則 fallback evidence bottom（同 benchmark 同版本內最低可用實測行，附理由）不變；suppression：上檔 pick CP ≥ 下檔 pick CP→下檔 `從缺`（附理由）；effort mismatch（AA max vs chain xhigh/off 等）須註記，不代入；人工只做堪用判定（附理由），不手訂數字；`A >= B` 不變量已刪除（2026-09-24：原跨 benchmark 比較，單一主線下無意義）；門檻必須存在（禁令 6）。~~ 取代政策：ladder 不設 band floors；`--min-score` 必填（禁令 6）。
- **鏈外特例規則（2026-09-24 用戶確認 landing；2026-09-24 efficiency-dark-horse 擴充）【2026-09-24 部分 RETIRED：OMO 脫鉤，chain 句作廢，GRADE-B＋re-verification 維持；見 docs/superpowers/specs/2026-09-24-ladder-design.md】**：~~Contributor 類「用資料換低價」pricing plan 行＋ efficiency-dark-horse 行（鏈外、當版 top CP）允許以鏈外特例參戰，條件：~~identity 按 pricing plan 分行（§4）；cost 走 GRADE-B documented rescale（公式＋假設寫進 notes，frontier 行標 `B`，單獨決定台階時加 caveat；實測 cost 則 GRADE-A 不標 B）；~~永不移入官方 chain（chain 原文不動，head/mid/tail band pick 不取特例行）；~~Contributor re-verification（2026-09-24 用戶確認）：每 run ~~入 band 前~~必重抓 Meta pricing page（input/output/cached 單價＋RPM/TPM），若下架／改價則 Contributor 行退回鏈外並註記；GRADE-B ratio 每 run 重算，永不沿用舊值；privacy 欄僅註記，不分桶不過濾（2026-09-24 取消分桶政策）。
- **速度註記（2026-09-17 v4 補）**：TTFT／time-per-task 有 AA 實測數才寫入展示註記（前例：Luna max TTFT~2min、每任務~6min，只適離線批量；MiMo 26 每任務 524s）；永不進數學（禁令 11）。Phase 2 需機器可讀速度時用 candidates 選填欄 `ttft_s`／`time_per_task_s`（AA 實測 only；缺欄或空值＝未知，不擋行）。
- **兩階段路線（2026-09-17 v4 補）【2026-09-24 用戶決定：frontier retired，recommend-only；五級×兩桶矩陣作廢，歷史保留】【RETIRED 2026-09-24：OMO 脫鉤，ladder 取代；見 docs/superpowers/specs/2026-09-24-ladder-design.md】**：Phase 1＝分級凍結（本節）；Phase 2＝智慧推薦（需求→推薦，邏輯須寫成腳本~~如 compute_frontier.py~~，不手推；~~吃實務約束：桶／級／預算／速度；設計參考 FrugalGPT cascade＋RouteLLM router~~）。~~Phase 2 v1 實現＝`scripts/recommend.py`（唯一合法推薦實現）：無需求輸入，固定輸出五級×兩桶矩陣；frontier 數學重用 compute_frontier；每格攻堅選（最高分）＋省錢選（最高 CP；單一成員則合一）＋不推名單；空即從缺。~~ ~~取代政策：Phase 2 v1＝`scripts/recommend.py` official-chain three-pick（唯一 sanctioned run 輸出）。~~ 取代政策：推薦邏輯＝`scripts/ladder.py`（唯一 sanctioned run 輸出）；腳本原則維持（邏輯須寫成腳本，不手推）。
- **no-Claude forward policy（2026-09-24 用戶決定）**：未來 picks／mapping／opencode／Notion 永不推薦 Claude-family 模型（Claude／Opus／Fable／Sonnet／Haiku，任何 effort／provider），因 Claude plan 不能用來驅動 OpenCode。配置驗證／推薦一律排除 Claude-family（禁令 14）；frontier 數學保留 Claude 行作比較，但它們永不當最適合／平衡／floor。
- **ladder 政策（2026-09-24 用戶決定：OMO 脫鉤，ladder 取代 chain/band/suppression/tier/floor 體系；spec 見 docs/superpowers/specs/2026-09-24-ladder-design.md）**：主線＝General（AA-Intelligence-Index-v4.3 唯一主線）；算法＝top-down CP-new-high（`compute_frontier.compute_one_group`，frozen）→ 0.5eps 連帶去重（相鄰 gap＜0.5×eps_score 成帶；1 行帶保送；2 行帶留 keep-key＝CP高→分數高→便宜大者；3+ 行帶從中間迭代砍到剩頭尾）＋pinned（全表最高分行＋全表最高 CP 行不參與被砍）；B 級行（GRADE-B 推導價，行標 `B`）照常參戰（含設 best、含擋人），單獨決定生死時輸出加 caveat（禁令 9）；Claude 行留表作比較、永不推薦（禁令 14）；配置驗證三 ref（root `model`＋`agents.general.model`＋`agents.explore.model`，`small_model` 跳過；ref 解析＋ordered-token-subsequence 匹配 copy 自退役 `recommend.py`，不 import；命中→OK，命中被 cut 行→警告＋同帶贏家，只命中 excluded／無命中→警告＋全表 CP 峰值建議；缺檔→stderr 警告＋跳過，exit 0）；回歸（score~ln(cost)，剔 Contributor）只當手動診斷寫進 run 註記，不進腳本；唯一輸出＝`scripts/ladder.py` 生成的 `runs/<run>/ladder.md`（階梯表＋cut 名單＋配置驗證節＋dominated sample），生成後只 eyeball、不手改。

## 2. 禁令（違反即視為錯誤排名）

1. 禁止跨 benchmark（名稱、版本、任務集任一不同）合併 score 或 cost。
2. 禁止跨 cost basis 合併：`api` / `subscription-amortized` / `trial-credits` 永不混算。
3. 禁止用 open-weight 推定 provider 不訓練。
4. 禁止把 `retention=0` 畫等號於不訓練。
5. 禁止無 `as-of + benchmark_version + evidence_url + checked_date` 的 `private-safe` 標籤。
6. 禁止無 `minimum_intelligence` 的 frontier 輸出（尾端必被不可用的便宜模型霸榜）。
7. 禁止把 FREE 行送入 frontier 算法（`cost=0` 直接報錯或分流 sidecar）。
8. 【RETIRED 2026-09-24：用戶決定取消分桶，「不管會不會被訓練」；禁令原文保留作廢，不再執行。】~~禁止把兩桶 privacy 混排（`mode=all` 也必須分開算、分開表）。~~取代政策：單一合併 frontier，所有付費行混排。
9. 禁止把 B 級推導 cost 當 A 級呈現（frontier 行無 `B` 標示即視為錯誤排名）。
10. 禁止混用不同 `benchmark_version` 的 score / cost（即使同模型同名；v4.1.1 數字禁入 v4.3 run）。
11. 禁止把吞吐 / 配額 / ZDR 折算成 cost 併入 CP（只許註記）。
12. 【RETIRED 2026-09-24：frontier retired，recommend-only；禁令原文保留作廢，不再執行。】~~禁止把分級混入 frontier 數學（分級只做展示；峰值／級距只決定版面）。~~
13. 【RETIRED 2026-09-24：frontier retired，recommend-only；禁令原文保留作廢，不再執行。】~~禁止把分級線跨版沿用（數字每版重算；錨點＋k 規則不變）。~~
14. 禁止在未來 picks／mapping／opencode／Notion 推薦 Claude-family 模型（Claude／Opus／Fable／Sonnet／Haiku，任何 effort／provider；§1 no-Claude forward policy）。

## 3. 一次 run 的標準流程

1. 新建 `runs/<YYYY-MM-DD>-<topic>/candidates.csv`（從 `templates/candidates.template.csv` 複製）。
2. 填候選：每行一個 identity，單一 benchmark + 版本，單一 cost basis（默認 `api`）。~~按官方原生分組（lanes／curated agents／categories official-chain，見 §1 角色分組）收錄 head/mid/tail 行＋鏈外特例行（§1 鏈外特例規則）；~~收錄＝Full-family sweep（同 family 全部 efforts，不預挑）＋Contributor／provider-split 手動行；每行須有 `score_source + source_date`（寫進 notes）；notes 以 `GRADE-A`（AA 實測）或 `GRADE-B`（推導，寫公式 + 假設）開頭，C 級禁入。~~無 AA 分數的 chain rung 標 `無AA分數→退回`，不代入。~~無 AA 分數的候選 identity 不收錄（不代入、不推定）。
   - ~~chain-drift check（2026-09-24）：每次新 run 收錄前必先 diff 官方 chains 對 HEAD（`agent-model-matching.md @ HEAD`＋`builtin-profiles.ts`＋兩處 `fallback-chains.ts`）；chain 有變＝開新 run＋note 記錄 drift（舊 chain 逐字保留作廢，不刪），不沿用舊 chain 收錄。~~【RETIRED 2026-09-24：OMO 脫鉤】
   - 【RETIRED 2026-09-24：OMO 脫鉤】~~fast-suffix 映射（2026-09-24）：chain rung `X-fast (effort)` 對應 AA 模型 `X (effort)`（fast 屬 OmO 側命名，非模型版本；AA release 頁只列 max/xhigh/high/medium/low/non-reasoning，無 fast）；例 `luna-fast low`→`Luna low`。~~
    - Full-family 收錄（2026-09-24）：新 run 收錄必須 sweep 同 family 全部 efforts（不只收需要的 rung）；去重交給 `ladder.py`，人不預挑。
    - API 收錄路徑（2026-09-24 sanctioned）：新 run 收錄經 `python3 scripts/fetch_aa.py --out <run>/candidates.api.csv --snapshot <run>/aa_snapshot.json`（env `AA_API_KEY`；key server-side，永不 log）；envelope `intelligence_index_version` 即 `benchmark_version`；provider 為 AA-median（Free 跨 provider median，不分 provider/plan）；Contributor／provider-split 行維持手動；snapshot JSON 隨 run 歸檔。
3. 三遍核對才准放棄候選（2026-09-24 用戶指令：輕易放棄是根本問題；見 §7 教訓附錄）：任何候選 identity 在判定無 AA 分數不收錄之前，必須走完三遍核對並列出 passes 證據，缺一律不准放棄：
   - pass1＝本地 `candidates.csv` grep：exact＋case-insensitive 雙查（如 `glm-5.3`＋`GLM`、`haiku-4-5`＋`Haiku`），排除本地已有行被漏看。
   - pass2＝AA source table sweep：model 專頁＋index 總表雙掃；必須試 variant spellings（`Flash/max`、`4.5/4-5`、dashes/spaces、`deepseek/deepseek-flash` 類 provider alias 等），排除拼寫變體漏檢。
   - pass3＝effort/ID disambiguation（§4 identity 規則）：不同 ID／不同 effort 永不代入，但必須 positively ruled out（逐一列出近似行 ID×effort 並說明為何不是該候選），不許用「假設沒有」代替排除。
   只有三遍皆空、且 notes 列出三遍 passes，方可判定不收錄。
4. 跑腳本（ladder 唯一輸出）：`python3 scripts/ladder.py --input runs/<run>/candidates.csv --min-score <F> [--max-cost <X>] [--eps-score <E>]`（`--min-score` 必填，禁令 6）。
5. 人工覆核 cut／排除理由是否合理（只保留有助理解的案例，不要全印）。
6. 新 run 只寫 `runs/<run>/ladder.md`（`ladder.py` 生成輸出，生成後只 eyeball、不手改；若錯＝修 code 重跑）；~~`recommend.md` 不再產出（舊 runs 的 `recommend.md` 歸檔保留、不刪除）~~；`frontier.md` 不再要求（舊 runs 的 `frontier.md` 歸檔保留、不刪除）。更新 `runs/<run>/free-sidecar.md`（如有 free）。
7. 每次輸出頂部必須有：`as-of date / benchmark name+version+URL / cost basis / --min-score＋理由 / eps 值+來源 / privacy 註記版本`。

## 4. Identity 去重規則（什麼算「同一行」）

以下任一不同即為不同 identity，不可合併行：

- model 名、checkpoint/版本日期、quantization
- reasoning effort（xhigh/high/medium/low…，跨 effort 不可比價差以外的能力）
- provider、endpoint/route
- pricing plan（Standard vs Contributor 那種「用資料換低價」必須分行）
- cost basis、cache 假設、thinking-token 計費方式、折扣類型（list/discounted/trial）

## 5. 目錄結構

- `AGENTS.md`：本檔。
- `scripts/compute_frontier.py`：frontier 數學 frozen 實現（階梯數學唯一實現，ladder.py 調用，不動一字）。
- ~~`scripts/recommend.py`：推薦矩陣唯一實現（分級＋推薦；frontier 數學調用 compute_frontier，不重寫）【2026-09-24：唯一 sanctioned run 輸出】。~~【RETIRED 2026-09-24：OMO 脫鉤，ladder 取代；檔案保留，永不再調用；新腳本禁止 import 它。】
- `scripts/ladder.py`：唯一輸出（顯示層：load rows → compute_one_group → dedup_bands → match config → render `ladder.md`；見 docs/superpowers/specs/2026-09-24-ladder-design.md）。
- `templates/candidates.template.csv`：候選表 schema。
- `runs/<run>/candidates.csv`：該次輸入快照（不可事後改，改了要新開 run）。
- `runs/<run>/frontier.md`：~~該次輸出（含單一合併 frontier + 能力五級矩陣 + dominated sample + verbatim 腳本輸出）~~【RETIRED 2026-09-24：不再產出；舊 runs 歸檔保留、不刪除】。
- ~~`runs/<run>/recommend.md`：該次推薦矩陣（`recommend.py` 輸出存檔）【2026-09-24：唯一 sanctioned run 輸出】。~~【RETIRED 2026-09-24：不再產出；舊 runs 歸檔保留、不刪除。】
- `runs/<run>/ladder.md`：該次輸出（`ladder.py` 生成：階梯表＋cut 名單＋配置驗證節＋dominated sample；生成後只 eyeball、不手改）。
- Notion 正式頁（2026-09-25 舊 ladder 展示，**2026-09-26 已由番外篇取代**）：唯一對外頁 page_id `3e539f3f-a67c-810a-9eca-f2de2c0fe1a5`，URL `https://app.notion.com/p/3e539f3fa67c810a9ecaf2de2c0fe1a5?pvs=204`；現標題 `模型效率前線｜番外篇 GPT×18／Grok×16（2026-09-26 快照）`，展示以 `runs/2026-09-26-general-grok16/ladder-extra.md` 為 SSOT 的精簡版（16 階 Score 降序、全 9 Grok 狀態、Contributor、cuts、B caveat、來源與推定版本限制）；同步須先 fetch 再 `replace_content` 與 `update_properties`，不得刪除子頁。舊 10 階與 `ladder.md` 只作歷史本地存檔，不再作 Notion 最新展示。
- `runs/<run>/free-sidecar.md`：free/quota 側表（如有）。

## 6. 待用戶定的預設值

- `minimum_intelligence`（floor）預設值：~~不設全局數字；每次 run 按 §1 floor 規則 official-chain 版動態推導（最適合=chain head official pick，有實測則引用、無則標 `無AA分數→退回`；平衡=chain mid；floor=chain tail AA score，tail 無分數則 fallback evidence bottom；effort mismatch 註記不代入；`A >= B` 不變量已刪除（2026-09-24，單一主線下無意義））＋用戶確認；~~`--min-score` 必填（禁令 6），ladder 不設 band floors；禁令 6：門檻＋理由必填。
- 月用量假設（free sidecar 的 effective cost 攤提）：未定，初版 sidecar 只列 quota/throttle，不攤提。
- 開跑互動預設（2026-09-17 用戶反饋：開頭問題太多）：`開跑` 預設 = General / AA 最新同版本 / max-cost 無 / candidates 由我搜集；只追問 `--min-score`（提案數字＋理由，用戶確認；禁令 6 必填、無全域預設）。用戶另有指定則覆寫預設，不逐項重問。

## 7. 教訓附錄（2026-09-24，用戶指令：輕易放棄是根本問題）

- 規則：**輕易放棄的複利**——一次 false retreat 會連鎖污染多個結論（anchor／tail／gap 全錯），修補成本遠高於當初多查三遍。§3 step 3 三遍核對即為此而設。
- case GLM-5.3 max：agent 只掃本地 candidates（pass1 當全部），把 `GLM-4.5-Flash` 誤當 `GLM-5.3 max` 的近似行排除，未做 AA source table sweep（pass2 缺）；用戶截圖曝光 AA 實測 `GLM-5.3 max 45 / $2.01` 真實存在。後果：C-anchor 誤判、A-tail 誤退回、D-gap 誤算，三處結論全毒。
- case Haiku 4.5：agent 以「generation 誤判」（以為 4.5 不存在／無分數）直接退回，未走 variant spellings（`4.5` vs `4-5`、dashes/spaces）＋model 專頁＋index 總表雙掃；實際是該 rung 有 AA score、缺的是可用 cost（屬 GRADE-C 無 cost 問題，不是無 score 問題）。後果：C-tail 退回理由寫錯，floor fallback 鏈跟著錯。
- 曝光來源：兩案皆由用戶截圖（AA 頁面實測數字）戳破，非 agent 自查發現；此後凡退回必須附三遍 passes 證據，用戶可直接複驗。
- case DeepSeek V4.1 Flash＋Luna family sweep 缺漏（2026-09-24）：agent 本地 grep 停在 Coding rows（`deepseek-flash` 只見 Coding 實測即止），未 sweep 同 family 全部 efforts，漏掉 General 主線 `DeepSeek V4.1 Flash 39 / $0.27`（用戶截圖曝光）；同 run 另漏 `Luna medium／low／non-reasoning`（只收了需要的 rung，未做 family sweep）。教訓：sweep 必須按 family 全 efforts 展開（§3 Full-family 收錄），不只補缺 rung；本地 grep 命中 Coding 行 ≠ General 無行。
