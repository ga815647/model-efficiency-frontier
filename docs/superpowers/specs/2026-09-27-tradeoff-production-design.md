# 正式取捨表：雙軸支配、升級代價與兩個客觀入口

> **2026-09-27 最新狀態：需修訂，禁止依下方原稿實作。** 使用者糾正：原表是 Score 降序、往下 CP_adj 創新高才留；問題是如何精簡這條鏈的過密檔位並直接給出選擇。下方「取消 CP-new-high、改用全候選嚴格雙軸支配」是 assistant 偏離原前提的設計，撤回其作為正式實作依據。使用者另已否定最高分必保留，以及近分群一律取最便宜而導致最低分必勝。原稿與試版留存供追溯；後續剔除／推薦方案尚未定案，原兩入口安排也不能凌駕上述最新要求。

日期：2026-09-27。**狀態：使用者已選「正式採用」及「兩個客觀入口」；本書面規格待審閱，尚未開始正式版實作。** 執行方法沿用先前選定的 Subagent-driven development；書面規格確認後再寫實作計畫。

## 1. 目的與已確認決定

讓使用者看懂各個能力／成本檔位的存在理由，以及向上一檔要多付多少。只憑 Score 與成本不宣稱某個通用加價比例必然值得；不將 Score 視為等距的實務效用或任務成功率。

使用者試看 `experiments/2026-09-27-tradeoffs/` 後批准：

- 正式 Chat／CI 以 Score、Cost_adj 的雙軸支配規則取代舊 CP-new-high＋band 去重。
- 每個保留點展示相對緊鄰較便宜保留價位的 ΔScore、成本倍率、ΔCost_adj。
- `eps_score=2` 只作分差註記／展示折疊；不因分差小刪行，不以 5% 決定購買價值。
- 結報頂部改為非 Claude 的 **最高分**、**最低情境成本**兩個客觀入口。取消「列表中間那行＝平衡」及固定三 picks；最低成本不再指最高 CP。
- GPT 預設 ×18、Grok 預設 ×16、Contributor ×1；原價、情境價與證據等級清楚區分。

既有 trial 僅用 9/26 固定 CSV，155 候選得到 21 個保留點、134 個被支配行、13 個小分差升級。這些是指定快照＋指定參數的回歸基準，不是新快照必須符合的數量。

## 2. 決策規則

### 2.1 同組候選與約束

仍只比較 General、相同 benchmark_version、相同原始 cost basis 的付費 A/B 級資料。free 分流、不進數學；Grade-C、無效付費值、重複 identity、來源／版本不一致維持拒絕規則。來源取得與本次數學更換分開處理。

先用既有情境轉換產生 Cost_adj，再以 `Score >= min_score` 及選填 `Cost_adj <= max_cost` 篩選。門檻仍須理由；不新增全域 floor。約束排除與支配排除分開記錄，超預算者不能支配預算內候選。若兩個限制都不符合，以 below_min_score 為主原因、原始數字可供核對。

### 2.2 嚴格雙軸支配

A 可取代 B，當且僅當 `A.score >= B.score` 且 `A.cost_adj <= B.cost_adj`，至少一項嚴格不等。

- 用未作展示取整的數值比較；不將 eps_score 或 eps_cp 放入判定，不用 CP 先砍候選。
- 同分同價的不同 identity 全留；不得把 route／plan／effort 合併。
- 每個被支配行附一個**最終保留行**作證據；以 cost_adj 升序、score 降序、identity 字典序選定可重現的證據行。
- GRADE-B 照常參戰；若選中的支配證據為 B，顯示其推導價及假設，不能冒充 A 或精確實測價。僅 B 能支配的案例須明示依賴 B 推導成本。
- 不另 pin 最高分／最高 CP 行。最高分同分較貴者也適用相同規則；其存在於輸入及狀態表，不竄改來源。
- 這只是兩個所選軸的支配關係，不宣稱模型對所有用途都沒有價值。

### 2.3 相鄰升級

保留點按 cost_adj 升序分成相同價格組。每組使用前一個**嚴格較便宜**組的代表作比較，同價組內各 identity 共用比較基準；代表依 identity 字典序固定。保留點相同價格時也必同分，否則低分者應已被支配。

每個升級含 `cheaper_identity`、`delta_score`、`cost_multiple`、`delta_cost_adj`、`within_noise`。最便宜組的 upgrade 為 null；其餘三個數字分別為分數相減、調整價相除、調整價相減。`within_noise = delta_score < eps_score`；剛好 2 分屬達門檻。

全表仍按 Score 降序（同分按成本、identity）展示，每行明示比較對象。小分差卡片可折疊，表格不刪行；不把多段小升級累積起來的大差異藏成「能力相同」。到達 2 分也不宣稱統計顯著或實務效果必然不同。

### 2.4 兩個非 Claude 入口

兩入口從**通過 min-score／max-cost 的非 Claude 候選**選出，表達該可使用範圍的客觀端點：

- `highest_score`：Score 最高；同分挑 cost_adj 最低，再依 identity 固定。
- `lowest_cost`：cost_adj 最低；同價挑 Score 最高，再依 identity 固定。

兩者可為同一 identity；沒有符合條件的非 Claude 行時皆 null，顯示從缺。Claude／Opus／Fable／Sonnet／Haiku 的任何 provider／effort 不作入口。

全表的支配計算仍包含 Claude 作比較。因此極端情況下，非 Claude 入口可能被 Claude 支配而不在保留表；此時入口卡須明示「非 Claude 範圍端點」及其全表狀態／支配證據，不假稱它是全表保留點，也不把 Claude 推薦給使用者。此規則避免比較用 Claude 使可用範圍的最高分或最低成本入口消失。

## 3. 計算與展示邊界

新增一個正式、可重用的取捨計算模組（建議 `bridge/tradeoffs.py`），吃已驗證／已作情境調整的候選，統一產出 statuses、保留表、升級資訊、兩入口。從 trial 的已驗證邏輯提取，補 max-cost、入口與生產欄位；不把 trial 的固定來源 hash、日期或 inferred 文字帶進泛用正式流程。

`bridge/result.py` 負責來源驗證與版本化結果組裝；JSON、Markdown、HTML 消費同一次計算。renderer 不抓來源、不重新跑支配規則、不自行猜入口。來源日期、版本聲明、caveats 取自當次驗證過的 provenance。

新正式 Chat／CI 計算不再調用舊 CP-new-high／band 去重。`compute_frontier.py`、`ladder.py`、`ladder_extra.py`、`recommend.py` 與原 `runs/`、已發佈 `results/`、試版快照保留為歷史可重現路徑；既有情境轉換／family 辨識等已測 helper 可重用，不改歷史數學內容。本次不另外擴充獨立通用 CLI，正式本地執行沿用 runner。

## 4. 結果契約與歷史相容

### 4.1 新結果 schema v2

**請求 schema 仍為 v1**，既有 refresh／recompute、唯一分支 JSON push、參數與三組 commit 關聯保持可用。請求 schema 與結果 schema 各自有版本，新產品 commit 執行時產生 result schema v2。

成功 v2 延續 correlation、parameters、source_snapshot、source_dates、benchmark/version/status、cost_basis、caveats、candidate_count、errors 等欄位，並明確使用：

- `selection_policy: "score-cost-pareto-v1"`。
- `eps: {"score": 2.0}`；v2 不帶有作用誤導的 `eps.cp`。
- `tradeoffs`：Score 降序的全部保留行；替代舊 `ladder`。
- `anchors: {"highest_score": <row|null>, "lowest_cost": <row|null>}`；替代舊 `picks`。
- `candidate_statuses`：所有付費候選，原價／調整價、CP（純顯示）、係數、grade、原始 identity/source 欄位仍完整。

v2 row 的 status 為 `retained`／`dominated`／`filtered`，含 `comparison_only`、`dominated_by`、`reason`、`upgrade`、`grade_b_dependency`。retained 的 dominated_by/reason 為 null；dominated 必連到真正支配它的 retained identity、reason 為 `dominated`；filtered 的 reason 為 `below_min_score` 或 `above_max_cost`、dominated_by 為 null。非 retained 的 upgrade 為 null。`grade_b_dependency` 只在 dominated 且全部通過約束的 A 級候選皆無法支配該行時為 true，其他為 false；不能僅從所選 witness 是 B 就推定只有 B 能淘汰它。同一 identity 在不同 payload 區域的內容須一致。

失敗 v2 沿用相關身份和結構化 errors，**沒有** tradeoffs／anchors／candidate_statuses 等成功衍生欄位；無效請求的診斷路徑規則延續，不填入上次成功的內容。未知版本、v1/v2 欄位混用或非法關聯須拒絕。

驗證需覆蓋表與 statuses 完整性／順序、證據行實際支配、數字與參數關係、入口選法、相鄰升級差值與同價基準。驗證層可檢查數字／關係但不另生成一套推薦；核心選擇只有一個實現。

### 4.2 舊結果讀取

`validate_envelope` 按 schema 分派：v1 以原 ladder／三 picks 規則驗證，v2 以新規則驗證。舊語義不得改寫成新語義。runner 的固定 fresh snapshot 讀取、inventory 驗證、publisher、assert-success 都須接受合法的 v1 與 v2。

這也涵蓋並行過渡：工作流程用新 main 的 bootstrap 發佈，但某個已排隊請求仍執行舊 product commit 並產 v1；新 publisher 必須能保存它。`latest-success`／`latest-refresh` 不需要為本次改制改寫排序機制，Chat 讀指標後須辨識實際 schema。讀到 v1 就稱舊制結果，不自動啟動 CI，也不當作新制輸出。

### 4.3 Chat 與 HTML

Chat 新制結報先給兩入口及其客觀語義，按需求列完整取捨表／重要升級，讀回數字而不手算。HTML 頂部兩卡、Score 降序全表、可折疊小分差卡、全部支配／約束原因，以及全 Grok／Contributor 狀態、來源及 B caveats。

原價、Cost_adj、CP_adj 如有顯示須各自標明；2 分與小分差卡片不叫「不值得」。單檔 HTML 仍 inline CSS、escape 外部文字、離線／窄螢幕可用，沿用 artifact 與固定 Git 路徑。Project bootstrap 的入口與權限邊界不變，使用者不用重貼；更新 Git 完整指示及契約，保留已通過的 Chat 工具驗收證據。

## 5. 取數缺口的處理

9/27 Inkling xhigh／MiniMax-M2.7 的當前 AA task cost 缺失，已三遍核對；改制不解除該資料完整性 guard，不以歷史價、零或 successor 價代入。parser 修復已發佈，當前 fresh 仍可能正確失敗。

新制先以固定批准快照完成 recompute 驗收；fresh 成功路徑用保存的原頁 fixture 驗證，而真實來源缺口按失敗路徑保存及結報。不能為了通過改制驗收而捏造 fresh 成功。

## 6. 驗收條件

1. 指定 9/26 原 CSV＋18/16＋min0＋無 cap：155 statuses、21 tradeoffs、134 dominated、13 小分差；入口為 GPT-6 Astra max 與 GPT-6 Luna low。固定成功 fresh CSV 也要另跑、按其 bytes／來源身份核對，不把不同 CSV hash 冒充同一來源。
2. 同分同價、多個價格組等價路線、邊界 2 分、Grade-B sole-dominator、成本 cap／floor、全部被篩掉、全 Claude、非 Claude 入口被 Claude 支配，都有針對性測試。不能靠添加或刪除等價 route 改變其他價位的升級數字。
3. JSON／Markdown／HTML 的 rows、兩入口、升級關係一致；原始未取整值正確、惡意字串被轉義，折疊只影響展示。桌面／手機離線視覺檢查及無外部請求。
4. v1 歷史成功／失敗仍能讀取驗證；成功 v1 refresh CSV 可由新產品重算為 v2。v2 fresh snapshot 可供後續重算；混合版本 publisher 仍 append-only、競爭重試與最新指標規則維持。
5. 新產品 commit 實際 request push → Actions recompute 成功 → result v2＋HTML artifact 固定 commit 讀回；非法請求或當前來源缺口產失敗 v2，不帶入口、不推進成功指標。
6. 原 run／results／frozen 檔案位元組不變；新輸出明標新 selection policy。Chat Git 指示依 schema 結報，用戶不再需要能力問卷或 bootstrap 重貼。

## 7. 書面規格確認後的下一步

依本規格寫實作計畫，拆分正式計算、v1/v2 契約相容、共用報告、Chat 指示與部署驗收；沿用使用者已選的 Subagent-driven。實作計畫確認前不開始產品修改。
