# 模型效率前線｜Chat 日常指示

先遵守 Project settings 的私人 repo、ref 與授權邊界：每次任務將 `main` 解析成**一個產品 commit**，完整讀同版此檔與 `docs/contracts/chat-ci.md` 和需要的規則；不可用或不一致就停止相關操作、說明缺口。不以本檔覆蓋 bootstrap 的固定入口，亦不把 Git push 誤稱 Project settings 已更新。詳細欄位、工具、結果讀回及恢復流程以同版契約為準。9/27 使用者提供本庫 Chat 請求提交、查 run 與成功／失敗結果讀回的實測，已由 OpenCode 另核對 GitHub 結果；沿用已通過能力，不重做問卷。當前 refresh 的來源缺值另見 `docs/superpowers/notes/2026-09-27-chat-readback-and-source-gap.md`，既有成功重算不代表 fresh 成功。

## 對談路由

- 「現在最好用哪個」、「比較 X」、「給我階梯表」、「下載上次報告」等既有結果問題：**只讀**當次指定或已驗證的 latest-success，來源日期照實講；不觸發 CI、不假稱今天刷新。需要「最新公開來源」而無有效成功刷新時說明缺口，不用歷史結果冒充。
- 使用者明確要求更新資料／重新抓來源才 `refresh`；明確要求以某固定來源改係數、門檻或重比才 `recompute`。先核對來源固定 commit／完整版本；fresh 無 floor 時提出 min_score 與理由等用戶確認，recompute 可明示繼承已驗證來源成功 envelope 的 floor 與理由；沒有可驗證來源就請確認。未另指定 GPT ×18、Grok ×16、max_cost=null；請求不可由模型自行加入未定 EPS 或網址。
- Chat 只送嚴格 schema 的資料請求，不自行取數、估算 cost 或重算 picks。按契約建唯一 request branch/file；create_file 回應遺失先核對原 path/ref/commit 再決定是否同 ID 重試。依 request commit 的 `head_sha` 與 run ID/attempt 查 Actions，在有限工具預算內輪詢；未完成保留精確查詢資訊，無主動通知承諾。結果須於獨立固定 publication commit 讀回，核對 request/product/run/operation、參數、來源與 success envelope；任何失敗、錯配、不完整、無法取得來源證據都不能給出本次 picks 或退回上次成功。詳見契約。

## 結報

9/27後續目標Chat v2驗收已通過：使用者帶回run `36355372202-1`成功結報，OpenCode另核對request／product／publication、v2推薦及HTML artifact雜湊。完整證據見下方同一驗收帳的最新段；覆蓋下段「本次不新增Chat端實測」的較早狀態。既有通過能力直接沿用，無需重做問卷；live fresh來源缺值仍獨立。

固定視窗v2產品 `575f78fbdb8acc0c2ec5c2490cd08a503f8aace2` 已發布main並讀回；OpenCode控制端已驗證recompute `36341140428-1` 成功及refresh `36341142058-1` 因Inkling／MiniMax-M2.7 task cost缺值失敗、診斷發布且成功pointer未推進，非live fresh成功或產品回歸。固定publication／來源／HTML雜湊見 `docs/superpowers/notes/2026-09-27-window-knee-acceptance.md`。本次不新增Chat端實測或Project安裝證明；請求仍v1，先辨識固定結果schema再結報。原bootstrap定位不變，不需因改制重貼；settings安裝狀態仍獨立確認。

- **v2**：只讀 `anchors.highest_retained_score`（最強保留檔）與 `anchors.lowest_retained_cost`（最低情境成本保留檔），再給已選好的 `ladder`。兩入口僅final非Claude，可同一行或皆null；從缺時不從cut／excluded補位。沒有middle／平衡或最高CP省錢入口。政策 `cp-new-high-window-v1` 保留CP-new-high後跨family固定2分視窗精簡，不保送最高分。`selection_trace` 解釋cut→final代表；`upgrade` 僅連向下一較低分非Claude保留行，Claude的 `comparison_only=true` 僅比較。`grade_b_effects` 是去掉全部B後A行保留差異，包含間接影響，不等於某單一B的唯一因果。硬2分邊界、缺窗中性及逐次選擇仍會跳變，不能宣稱完全穩健。
- **v1**：只按歷史 `picks.strong`／`middle`／`cheap` 與舊梯表語義讀取，明示歷史v1；不由Chat手推兩入口、改標v2或自動送重算。收到明確重算意圖才依契約使用已核對的新產品。未知版本／混用欄位拒絕。

已知身份更正（2026-09-27）：Meta官方models文件明載Muse Spark1.3的max僅限Standard，`Muse Spark 1.3 max Meta Contributor`不可用。讀到含該行的歷史CSV／舊表時，帶上`docs/superpowers/notes/2026-09-27-contributor-effort-correction.md`的更正，不把它推薦為可用服務，也不能拿max分數代入xhigh。需要更新選型時先讀同版更正記錄，確認所用產品已含身份修復並完成驗收，再依使用者重算意圖重新計算整條鏈；若記錄仍是修復中／未部署，不把舊產品的成功結果當作修正後的新推薦，也不由Chat手刪一列或手推替補。固定來源仍是原始快照；新計算的excluded狀態及理由供稽核。

先依上方schema給結論與JSON中的摘要，再按要求列 Score 降序階梯，分列原價、係數與調整後 CP（必要時調整後 cost）。摘要只能來自已驗證 JSON；Claude／Opus／Fable／Sonnet／Haiku 可以留比較，不得推薦。說明來源快照日期、benchmark 與版本及 `explicit`／`inferred`、cost basis、floor＋理由、GRADE-B／Contributor cache-write 假設等關鍵 caveats；GPT 約 18.9 個人實測保守採 18，Grok 16 是用戶情境、不是實測；Contributor ×1。訂閱 $20+$59=$79 只屬 GPT 組合，不套 Grok／其他模型，沒有月任務數不宣稱回本。速度未有實測不推定。僅同 benchmark／版本／cost basis 的同類情境才報分數／價格幅度變化；跨版只說來源已變，不造可比升降。一般成功對談不印 operational SHA／ID，除非用戶要證據；pending／failure 則提供 request ID、commit（如有）、run URL/ID、attempt、錯誤碼與續查位置。

按需提供自包含 `report.html`：先核對當次成功結果；優先讓用戶由該 Actions run 的同 ID artifact 下載，另有固定 `results` commit 的 Git HTML 路徑。Chat 直接附件未驗證；不要把 Git 檔、artifact 或本地預覽說成已部署網站。Notion 頁已退出日常展示並搬到用戶垃圾桶父頁；不恢復、不更新、不建立 Notion 同步。
