# 正式階梯改制：CP-new-high＋固定2分視窗精簡

日期：2026-09-27。**狀態：使用者已在書面規格審閱請求後回覆「好」，本規格已確認；實作計畫待審閱，尚未開始產品實作。** 本文取代已撤回的Pareto正式化草案，不取代既有歷史快照。計畫見 [固定視窗實作計畫](../plans/2026-09-27-window-knee-production.md)，執行方式沿用Subagent-driven。

## 1. 目的、已確認前提與提案邊界

直接選出值得保留的模型檔位，避免大量相近effort占滿表格。第一階段始終是**Score降序，向下只有CP_adj創新高才留**；本次更換其後的精簡與推薦摘要。

已確認：

- 所有family／provider／plan混排，包含Astra、Sol、Luna、Grok及可用Contributor；沒有每家配額。
- 不保送最高分，不把每個近分群固定選成最便宜；不到2分可由較值得選的代表取代，並不宣稱能力相同。
- 採固定視窗方向：在剩餘CP鏈上向兩側各看2分，衡量log-CP增益的轉折。
- GPT×18是個人約18.9倍的保守取整，Grok×16是用戶指定情境；Contributor×1，原價與GRADE不改。
- Claude-family留作比較，永不推薦；單一General／同版本／同cost basis、floor必填及來源完整性要求延續。

本次書面審閱確認的落地決策：摘要只從最後保留的非Claude行取「最強保留檔／最低情境成本保留檔」；新結果schema v2、舊v1可讀；輸出附完整精簡理由與升級差額。批准來源是本次書面審閱，不是更早的試算方向確認。

## 2. 演算法

### 2.1 驗證、身份、情境及第一階段

1. 沿用現行來源／hash／benchmark version／付費數值／唯一identity／GRADE-A或B驗證。free分流，不把C級送入數字排名。
2. 沿用已發布的Meta能力驗證。不可用的Muse Spark1.3 Contributor max在任何排名前excluded；舊155行CSV仍保留原始行及身份稽核，不改名或轉用分數。fresh取得的當次能力／費率／退出證據及發布驗證不退化。
3. 情境調整沿用現行helper：cost_adj=cost_orig/factor、CP_adj=score/cost_adj，Contributor最多且僅×1。
4. 可用身份交給**未改動的**`compute_frontier.compute_one_group`：min_score、max_cost（作用於cost_adj）、eps_score=2、eps_cp=.05。第一階段排除理由與same-tier takeover语義沿用。5%不是新增的購買價值門檻。
5. 取得有序CP鏈C；不執行旧dedup_bands，也不先改用全候選Pareto。單次主計算只使用一個benchmark/version/basis組。

第一階段的同分同價處理沿用frozen的stable sort及原CSV順序，不另承諾所有等價route皆保留，不新增其他排序以改變其既有行為。多點有效鏈Score嚴格下降、CP嚴格上升。空鏈直接輸出空表；單點直接保留，不取log；因此僅有零分候選的單點鏈亦不計log(0)。無原始paid候選仍沿用`empty_paid`錯誤。

### 2.2 固定視窗轉折

常數：視窗半寬 `h=2.0`、替代半徑 `r=2.0`。數值相同但作用不同；首版固定於產品政策，不新增request參數。

對**目前剩餘鏈**，以Score作橫軸、`y=ln(CP_adj)`作縱軸，作分段線性插值。每個候選B若有完整區間`[Score_B−h, Score_B+h]`：

```text
g_in(B)  = [y(Score_B) − y(Score_B+h)] / h
g_out(B) = [y(Score_B−h) − y(Score_B)] / h
k(B)     = ln(g_in(B) / g_out(B))
```

越大表示到B為止的降檔效率增益較強，再繼續降檔的增益較弱。它是選檔指標，不是任務成功率或購買效用。

- 窗口剛好落在觀測端點有效；超出任一端時 `k=0`、support=`neutral_missing_window`，不外插。真正端點以及缺一側完整窗口的近端點適用相同規則。
- 插值不新增identity、不替換AA分數或用量；只影響B的選擇優先序。
- 使用完整精度，不先把分數四捨五入。浮點比較遵循正常二進位數值比較，不加隱藏容忍範圍。若有效鏈仍造成非有限／非正log增益，回報結構化`selection_numeric`失敗，禁止補極小數湊結果。

### 2.3 逐次精簡

1. 找出至少有一個其他剩餘點與其Score差**嚴格小於r**的候選池。剛好2分不互相取代。
2. 重算剩餘鏈上各點的k；候選池排序為k降序、CP_adj降序、Score降序、identity字典序。
3. 選第一個代表B，刪除所有與B分差小於r的其他點。直接與B比較，不用相鄰距離連鎖串成大群。
4. 保存當次B、k、support與被刪身份，重建剩餘鏈的插值，再重複。
5. 無近鄰即停止；孤立點留下。代表刪完所有r內近鄰後不可能在後續被替代，故每個cut的winner必是最終保留行。

不pin最高分／最高CP；不設family配額；不因B是Claude或GRADE-B就豁免精簡規則。兩個近端點均中性時仍以CP解平手，須如實記錄「缺雙側視窗、依CP解平手」，不能寫成實測轉折證明。

輸出保持Score降序、CP上升；最終相鄰分差至少r，每個第一階段點均可對應距離小於r的最終代表（保留點代表自身）。不保證全局最優或對所有誤差不變。

## 3. 推薦與呈現

### 3.1 選好整條階梯，再取摘要

最終非Claude保留行**全是已選好的檔位**；不是把未決群組折疊後交給使用者選。Claude行醒目標「僅比較」。被cut或excluded的行不能復活成摘要推薦。

摘要提出兩個客觀入口，均僅從最終非Claude保留集合選：

- **最強保留檔** `highest_retained_score`：Score最高，同分成本低，再identity字典序。
- **最低情境成本保留檔** `lowest_retained_cost`：cost_adj最低，同價分數高，再identity字典序。

兩者可相同；無非Claude保留行時皆null並顯示從缺，不另從被Claude淘汰的身份補位。取消原「列表中間一行＝平衡」；最低成本不借用「最高CP」作語義。取摘要發生在精簡後，**不反向保護全候選最高分**。

### 3.2 升級與剔除理由

每個非Claude保留行與下一個較低分的非Claude保留行比較：`cheaper_identity`、`delta_score`、`cost_multiple`、`delta_cost_adj`。在有效正分CP鏈中，較低分且較高CP必然更便宜；最便宜非Claude行及Claude比較行的upgrade為null。如此不會把Claude當作推薦的升降級路線。

表內同時顯示Score、Cost_orig、Cost_adj、CP_adj、factor、GRADE及身份；小數只作展示取整。cut節列原行→最終代表、分差、當時轉折或中性tie-break理由；第一階段excluded與能力不可用排除另列。全部Grok／Contributor狀態完整，不被top-N節錄隱藏。

不提供無根據的固定「加價多少一定值得」門檻。$79是GPT特定訂閱組合假設，不從非GPT入口推論續訂；N未提供時只保留原有假設说明，不產生新的月費決策。

### 3.3 GRADE-B與敏感性

- B行照常參戰且顯示公式與假設；成本推導與情境係數分開標示。
- 有可用B行時，核心另做一次「去除所有B行」的診斷重播（其餘參數及兩階段相同），比較A行最終保留與否。這只標記B組對選檔的影響，不改主結果、不稱為單一B的唯一因果證明。
- JSON的`grade_b_effects`列每個最終保留與否改變的A身份及有B／無B的布林狀態，依identity字典序；report明示B依賴，B代表直接cut亦附B標記。沒有可用B行時為空陣列。不可因winner是A就聲稱它未受B影響：插值及第一階段可能間接受B影響。診斷使用獨立資料副本，不修改主結果。
- 顯示固定政策限制：硬2分邊界、缺窗中性規則及逐次選擇仍可能跳變。不得寫「99%穩健」；不在日常每次run自動跑整套擾動作投票，更不以投票改選。

## 4. 計算模組與結果契約（提案）

### 4.1 單一計算入口

新增 `bridge/window_ladder.py`：吃已驗證、情境調整後的候選及floor/cap；内部先排不可用身份、調用frozen第一階段，再執行本規格精簡，產生名單、各階段狀態、trace、摘要、升級與B診斷。

`bridge/result.py`組裝provenance與版本化envelope；Markdown／HTML僅消費同一主結果，不各自計算推薦、抓來源或猜摘要。B反事實診斷是明確的附加計算，不是第二套選擇實現。

保留`compute_frontier.py`、`ladder.py`、`ladder_extra.py`及其既有CLI作歷史路徑，不修改舊band算法，不import退役recommend.py。可以重用既有情境／family helper；正式模組不import固定快照probe，實作其已確認的數學。歷史輸出、原CSV及已發布results不回寫。

### 4.2 result v2／request v1

請求仍v1（refresh／recompute、五個parameters、固定product/source/request commit、唯一push分支）。新產品產生結果v2。

成功v2保留correlation、parameters、source locator、source_dates、benchmark/version/status、cost_basis、caveats、candidate_count、errors欄位，並使用：

| 欄位 | 定義 |
|---|---|
| `selection_policy` | `cp-new-high-window-v1` |
| `eps` | `{"score":2.0,"cp":0.05}`，仍作用於frozen第一階段 |
| `selection_parameters` | `{"window_score":2.0,"replacement_score":2.0}` |
| `ladder` | 最終所有保留行，Score降序，含Claude比較行 |
| `anchors` | `highest_retained_score`、`lowest_retained_cost`，完整row或null；沒有舊picks |
| `candidate_statuses` | 全部原始paid行，不因身份不可用而漏掉歷史稽核 |
| `chain_identities` | 第一階段CP鏈，依其原順序 |
| `selection_trace` | 每次剔除的step（1起）、winner、strength、support、removed身份陣列 |
| `grade_b_effects` | 3.3定義的A身份保留狀態差異；物件鍵為identity、with_b_retained、without_b_retained |

row保留v1的identity/model/effort/score、cost_orig/adj、cp_orig/adj、factor、grade、source_url/date、notes、is_grok/is_contributor、status/reason/winner；新增`comparison_only`及`upgrade`。status仍為`final`／`cut`／`excluded`，語義明確：

- final：reason與winner皆null。
- cut：第一階段入鏈，但第二階段移除；reason=`within_replacement_radius`，winner連到final，剔除證據在trace。
- excluded：未進第一階段鏈，reason保留來源可用性／frozen排除說明，winner=null。
- comparison_only按Claude-family辨識，不改該行數學status。非final行upgrade=null；Claude final也為null。

trace的support只有`full_window`／`neutral_missing_window`；後者strength必0。step依剔除順序，removed依當時Score降序；statuses沿原paid輸入順序。相同identity在ladder／anchors／statuses的row內容須一致。k為負是合法轉折，不與非正的g_in/g_out錯誤混淆。

失敗v2保留correlation與errors，不含ladder／anchors／statuses等成功衍生欄位。未知版本及v1/v2混用拒絕。驗證檢查完整性、數字關係、partition、chain順序、cut對應與距離、trace每步移除一次、摘要來源和upgrade差額；不在renderer另寫一套排序或選檔算法。

### 4.3 舊結果與過渡

`validate_envelope`依schema分派，保留原v1梯表／三picks檢查。新runner、publisher、inventory／固定成功fresh讀取、assert-success需接受合法v1與v2。新bootstrap仍可發布排隊中舊product產生的v1。

v1結果只按舊語義讀取，不自動冒稱固定視窗結果，也不自行觸發重算；收到重算意圖才用新產品。`latest-success`／`latest-refresh`維持現行append-only及排序政策，Chat從pointer取得固定結果後辨識schema。v2成功refresh快照可作後續固定重算來源，來源證據驗證不縮減。

## 5. Chat／HTML與資料缺口

- Chat先給兩個保留集合內入口及選好階梯；按需單檔HTML，不部署網站、不恢復Notion。
- HTML展示兩入口、Score降序階梯、upgrade、cut/excluded理由、全Grok／Contributor狀態及B／來源限制；折疊僅壓縮稽核文字，不取代選檔。
- 沿用inline CSS、文字escape、離線／窄螢幕及artifact／固定Git檔定位。Git instructions及契約更新，bootstrap定位不變，Project不需因本次改制重貼；既有Chat能力證據沿用。
- 當前Inkling／MiniMax-M2.7缺cost仍阻擋fresh；不以改算法為由忽略候選或沿用舊價。recompute先驗固定來源；fresh成功用保存原頁fixture驗，當前真實缺口維持失敗診斷發布。

## 6. 驗收與已知限制

1. 固定9/26 CSV hash `e3916f8405904154f0e1dc648588bb08ce92f483cd616ba9be0ff2e5c726ed22`、18/16、min0、無cap：155 statuses＝136 excluded（含不可用max）＋9 cut＋10 final；154可用身份→19個CP鏈點→10保留點。
2. final：Claude Opus5.5 xhigh（僅比較）；Astra xhigh／medium；Sol max／high／medium；Luna max／high／medium／low。摘要為Astra xhigh及Luna low。其他快照不硬套此數量／名單。
3. 與`experiments/2026-09-27-cp-chain-regularized/`的window名單、trace及同组擾動逐項對照。原Astra max+0.25／xhigh−0.25反例不換推薦；新high+0.25仍有連動，照實保留為敏感度結果，不改測例掩蓋。
4. 全154逐行分數±.1／±.25、成本±1%／±5%各308情境的非Claude名單改變數是2／3／0／2；這不是可靠度機率。硬2分邊界與較寬視窗仍能改選，不能宣稱完全穩健。不得為固定10點結果調參。
5. 有意義數學案例：空／單點含零分、剛好2分、端點支持剛好／不足2分、直線log-CP零轉折、解析ln5例、CP同比例縮放、最高分可被刪、多輪重建曲線、非串群覆蓋。多點非有限／非正增益正確失敗。
6. 業務案例：floor／cap、identity不可用、B透過插值或CP改變A保留、所有非Claude被刪時摘要從缺、same-source原價不變及全Grok／Contributor稽核完整。
7. v1/v2成功與失敗、舊fresh→新重算、新fresh→後續重算、過渡publisher及pointer；JSON／Markdown／HTML同一結果，惡意文字escape、手機／桌面離線無外部請求。
8. 新產品實際push CI→recompute v2成功→固定結果commit讀回與HTML artifact比對；真實fresh缺口成功保存能力及missing-cost證據但run維持failed。歷史檔位元組不變。

## 7. 書面審閱後

本規格已確認，包括**剩餘敏感性接受範圍、只從final取兩個摘要入口，以及不從被淘汰行補位**。writing-plans已將共用計算、契約相容、renderer／Chat更新及驗收拆成實作計畫，待使用者審閱後沿用Subagent-driven；不提前改產品程式。
