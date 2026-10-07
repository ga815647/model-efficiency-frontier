# Chat 的兩種操作：維護倍率、產生 LADDER

2026-10-07 增量。倍率政策的唯一可修改表是 `bridge/site-policy.json`；Chat 透過正常 GitHub 產品 branch／PR 回填，無需新增網站管理後台或登入。`python3 -m bridge.cost_policy show` 顯示表格，`check` 與 Product CI 檢查數字、欄位及依據；檢查只能驗結構，研究內容仍需 review，不代表倍率已實測。

| 平台與方案 | 月費（USD） | 正式倍率 | 使用者建議範圍 | 使用者信心 |
| --- | ---: | ---: | --- | --- |
| ChatGPT Pro 100 / 5x | 100 | 17× | 約14–21× | 中 |
| Google AI Ultra 5x | 99.99 | 3.6× | 約3.5–6× | 低～中 |
| Claude Max 5x | 100 | 40× | 約32–45× | 中 |
| SuperGrok Plus | 100 | 5.2× | 約3–6× | 中低 |
| Contributor | 獨立定價 | 1× | 不套訂閱倍率 | 不適用 |

這是使用者2026-10-07最新明確指定，覆蓋先前18.9／6／37／16。僅計文字／推理／coding／agent模型運算，不計空間、影音、Voice、雲端credits或獨立Agent SDK credit。完整公式、研究來源與查證界線見 [研究筆記](research/2026-10-07-subscription-api-equivalent.md)。以可用且用滿額度為情境；實際用量或workload不同時倍率可能較低。

這些是使用者情境，不是供應商保證額度或公開 API 價格。未有完整推導時保存 `basis=user_specified`，不能把指定數字寫成研究驗證。沒有 Gemini／Claude 候選時不新增模型、借用其他 effort 或發明成本。

## 角色一：研究並回填倍率

先固定 main 並讀同版規則與表格。純「研究倍率」先查證、列依據，不自動寫入；「研究並回填／更新倍率表／把Gemini改成指定倍率」即授權在本庫回填，沿用既有授權，不重問批准。

倍率定義為相同工作量的 API 等值費用除以該段期間的訂閱費用。研究須保存方案／地區／幣別／稅、日期、模型與effort、觀測用量或限額及時間窗口、API對應費率、限制與公式。混用模型的等值API費用先按各自用量與費率加總，不混不同effort的能力或價格。消息上限、token額度、cache、工具及動態限流未必能相互換算；僅訂閱月費或「用到上限」不足以證明固定倍率。

先確認是實際用量的實測比值，或限額假設的理論情境；資訊不足時回報缺哪項，不自行猜token量、每則消息長度、實際可用額度或將估計當保證。可提出有明示假設的估算，但只有使用者接受的情境才回填正式表。Chat不得讀取平台保存的secret值、聯絡第三方或變更付費方案。

回填步驟：

1. 在 `feat/*` 產品 branch 改 `formal_parameters` 中相應 factor，同步更新 `factor_evidence`；必要時新增研究筆記，保留舊 Git 歷史，不改既有 results／原始來源。
2. 每個 factor 的 evidence **恰好**包含 `basis`（`user_specified`／`researched`／`inherited`）、`as_of`（有效YYYY-MM-DD）、非空 `references` 陣列、`calculation`（非空字串或null）、非空 `limitations`。`researched` 必須有HTTPS來源與非空公式；這只是最低結構門檻，人工review仍要確認方案、用量及公式相符。資料不足可保留舊倍率；使用者明確指定新數字可採 `user_specified` 並寫清缺口。
3. `python3 -m bridge.cost_policy check`、相關成本／歷史相容／網站測試及必要review通過後，以正常PR合併main。產品寫入不可放進 `efficiency-run/*`，不可force push。
4. 僅更新表不自動refresh來源或改已發布推薦。使用者同時要求「更新倍率並重算／產生LADDER／部署更新結果」時，合併後續接角色二。

## 角色二：產生 LADDER

「查既有階梯／給我階梯表」仍是只讀；「產生／重算LADDER」是新的計算。預設用固定快照 `recompute`；只有明確要求重新抓模型來源才 `refresh`。先重新固定合併後main、讀同版規則與倍率表，再核對最近成功refresh完整envelope、原始來源與hash；不能只憑latest pointer猜參數。

新請求使用 **request v2**，根欄位與transport保持原規則，`parameters` 恰好七欄：`gpt_factor`、`grok_factor`、`gemini_factor`、`claude_factor`、`min_score`、`min_score_reason`、`max_cost`。四個factor均有限正數，布林不是數字。倍率從已合併表讀；floor、理由及cap從已驗證來源明示繼承，或依明確使用者指示另設情境。正式首頁仍要求全部參數完全匹配政策，實驗不覆蓋首頁。

`recompute` 提交前說出實際source path、來源日期及「不會重新抓取新模型，快照後新增模型不會出現」。按唯一 `efficiency-run/<UUIDv4>`、唯一 `bridge/requests/<UUIDv4>.json` 提交；parent等於product_sha，僅新增這一檔。之後核對run head／branch／ID／attempt，固定獨立publication讀回本次JSON、來源證據與HTML。pending只續查原請求，失敗不退回舊成功冒充本次。

新 **result v3** 的根欄位、row、anchors、upgrade與source contracts沿用v2的精確欄位；只有 `schema_version=3` 和七欄parameters的語義擴充。request v1仍恰好五欄，生成result v2，Gemini／Claude沿用其歷史×1；合法歷史result v1/v2可讀，不改標新版本。新factor作用：GPT-前綴、起首獨立Gemini詞、既有Grok身份與既有Claude-family辨識；每行最多一個factor，Contributor優先×1。

公式仍是 `Cost_adj=Cost_orig/factor`、`CP_adj=Score/Cost_adj`。使用同一份已驗證CSV，原價／分數／GRADE不變；CP-new-high、固定2分視窗、EPS、來源／能力驗證、失敗處理均不改。Claude仍參戰比較但永不進正式兩入口／升級路線。

## 網站與版本

新政策 `schema_version=2`，根欄位恰好是 `schema_version`、`formal_parameters`、`source_refresh`、`factor_evidence`。`source_refresh` 是固定成功refresh的 `{commit,path}`；建置以同版政策驗證來源，floor／理由／cap必須一致，factor可有已記錄的更新。歷史無schema_version的兩欄policy保持原本參數全等檢查。

網站與備用HTML都讀同一份結果；manifest獨立記錄結果schema、完整情境、產品與publication，不修改result schema。成功計算自動觸發Pages build，所有已交付v2/v3固定頁保留；失敗不替換網站。public／公開deploy仍受 `docs/publication-review.md` 的第三方再散布門檻與真正GitHub權限約束，`deploy skipped` 不等於上線。

Project Settings由使用者貼入 `docs/chatgpt-bootstrap.md` 的新版文字。Git文件合併、離線測試、目標Chat實測與Settings安裝是不同證據，不互相冒充。
