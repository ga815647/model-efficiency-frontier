# 模型效率前線：Chat → GitHub CI 設計

日期：2026-09-26。狀態：設計、私人遠端定位及修訂後計畫已獲使用者確認並指示繼續；實作中，尚未部署／完成 Chat 端驗收。

## 最新修訂：結報與 Notion 退役（2026-09-26 用戶確認）

本節覆蓋下方原「端到端完成後才停 Notion」的切換時點。用戶選擇 Chat 日常結報＋按需單檔 HTML，不部署網站；分享採截圖或傳 HTML。CI 結果同時支持機器可讀 JSON、內部 Markdown 和固定模板的自包含 HTML，數學僅算一次；HTML 內嵌樣式，不依賴 CDN，不每次由模型重寫。Chat 是否能直接提供附件尚未驗證，可由 CI 可下載產物交付，不宣稱 Chat 內建預覽已可用。

用戶另明確要求立即將 Notion 原頁移入「垃圾桶」，日後自行手刪。已 fetch 核對原標題、move、fetch 父頁確認 child listing；原頁 `3e539f3f-a67c-810a-9eca-f2de2c0fe1a5`，父頁 `3e639f3f-a67c-8111-a4f9-d682d34f06b7`。這是搬到用戶垃圾桶頁，不是永久刪除或 Notion 原生 in_trash；內容保留。Notion 即日起停止同步，不等待新 CI 驗收。CI／HTML 未實作，既有本地結果仍可使用。

## 1. 目的與成功條件

ChatGPT Project 是日常操作、模型比較與結果呈現入口；GitHub Actions 執行取數、計算、驗證；Git 保存可追溯資料與結果。使用者說「更新一次，GPT ×18、Grok ×16」即可提交請求，無須日常手動操作 Actions。查詢已有結果不啟動 CI。Chat 不自行推算 picks。

遠端定位：`ga815647/model-efficiency-frontier`，私人庫；預設產品分支 main。既有本地快照及 frozen 數學完整保留。端到端驗收後 Notion 退出日常同步，舊頁保留。

## 2. 已有能力與選擇

使用者提供的 ChatGPT 端證據：固定 commit 讀檔、解析 ref、查 Actions run 已在另一私人庫實測；create_branch/create_file 工具可見，create_file 回傳 commit_sha。沒有 workflow_dispatch。這些證據不等於本專案已獲授權連線或寫入成功。

選擇每請求唯一分支的 push bridge，沿用既有 ziping 傳輸模式。固定控制分支容易被並行請求覆寫；新增 dispatch MCP 會增加本案不需要的服務。具體資料契約與結果保存採本專案規則，不搬入其他專案的領域規則。

## 3. 請求契約

Chat 先解析 main 為完整 commit SHA，按同一 commit 讀取完整 instructions 與必要契約，產生 UUIDv4 request_id，從該 commit 建立 `efficiency-run/<request_id>`；只新增 `bridge/requests/<request_id>.json`。create_file 回傳的 commit 為 request_commit_sha。

schema_version=1，共同必填：request_id、created_at（含時區 ISO8601）、product_sha（完整 main commit）、operation（refresh 或 recompute）、parameters。未知欄位或操作拒絕，不接受命令字串。

parameters：gpt_factor、grok_factor 為有限正數；min_score 為有限非負數，min_score_reason 非空；max_cost 可空，非空須為有限正數。既有 eps 規則由產品版規則讀取，不由 Chat 任意更改。初始情境 GPT=18、Grok=16。floor 無全域預設；重算未指定時明示繼承來源快照門檻與理由；fresh 未指定時請使用者確認門檻。

recompute 另外必填 source_snapshot={commit,path}，commit 固定來源版本、path 必須是 runs 下既有封存候選或 results 下已成功 refresh 的候選快照；後者須同版讀取成功 envelope 驗證来源。拒絕路徑跳脫及任意外部 URL。只使用可由本專案 Git 讀取的快照。refresh 不接受此欄位。

create_file 回應遺失時，先讀回唯一請求路徑並確認提交再決定重試；不能另發一份請求冒充同一次執行。retry 使用相同 request ID 時不得重複改寫原始快照。

## 4. CI 執行與來源

workflow 只在指定 request branch pattern 和 request JSON path 的 push 觸發。驗證 branch、request ID、檔案名稱及 commit 對應，提交只能新增該請求檔，不能夾帶程式修改。確認 product_sha 與建立請求的產品版本一致；產品程式從該不可變 commit 的獨立 checkout 執行，不偷偷改用較新的 main。

runner 只將 JSON 當資料，參數經型別／範圍驗證後傳給固定 Python 入口。業務計算重用 ladder_extra 與 frozen compute_frontier；GPT/Grok 每行最多一個係數、Contributor ×1、Score 降序、Claude 僅比較不推薦等規則維持。

refresh 建立新資料快照，保存來源、取得日期、benchmark_version 與成本證據。取數 adapter 需將此次公開頁提取與 Contributor 核價流程做成可重現程式：同 family 全 efforts、不混 benchmark/version/cost basis，缺 cost 不猜，零成本分流。

認證 API 與公開資料分開留存，不以公開版本重標 API 行。公開版本若只能交叉推定，須記 version_status=inferred 與支持證據；與最新推定公開版不一致的 API 不能靜默取代它並宣稱最新。不能建立一致版本／來源時，本次 refresh 失敗並列出缺口。

Contributor 每次 refresh 重抓定價，按該 identity 的同版成本組件重算 GRADE-B。保留目前已披露的 cache-write 按一般 input 費率假設；費率、計費語義或必要組件出現未覆蓋變更時不能沿用舊比率，回報需維護的來源缺口。缺失候選依既有三遍核對政策記錄，不自行降低資料完整性標準。

AA_API_KEY 由 Actions Secrets 注入；Chat instructions、請求、產物與日誌均不含值。secret 安裝依獨立設定步驟完成，不從聊天歷史自動搬移。

## 5. 結果與保存

每次邏輯請求以 request_id + request_commit_sha 識別；每次執行另外帶 run_id/run_attempt。重跑保留各 attempt，避免覆蓋歷史。

結果放獨立 `results` 分支，每次寫入 `results/<request_id>/<run_id>-<attempt>/`，含 result.json、report.md；fresh 另含候選、来源證據與 run notes。產品 main 不接受 CI 計算結果的自動寫入。發佈採序列化／衝突重試保存各次結果，不以 force push 覆蓋他人結果。

result.json 必含 schema_version、operation、status、request_id、request_commit_sha、product_sha、run_id、run_attempt、source_snapshot、parameters、source_dates、benchmark/version/status、cost_basis、ladder、picks、candidate_statuses、caveats、errors。ladder 與 report 由同一次計算生成；candidate_statuses 覆蓋全候選，含 Grok、Contributor 與 cuts。失敗結果也有完整關聯及結構化 errors，不能包裝為成功。

source_snapshot 區分兩種成功來源：recompute 為 `{commit,path}`，讀取已存在的固定 Git 快照；refresh 為 `{kind:"acquired",path:"snapshot/candidates.csv",sha256}`，hash 與本次新 CSV 位元組相符，不捏造新資料已存在於產品 commit。之後重算該 fresh 結果，請求使用已發布 results commit＋完整快照路徑，並核對相鄰成功 refresh envelope 與原始 hash。

結果 commit 不放進其自身內容形成循環；Chat 解析 results 分支 commit，再以該固定 commit 讀取特定 request/run 的 result.json。run 與 metadata 必須和本次請求一致。成功產物通過驗證後才更新同一提交內的 latest-success.json 指標；重算情境不改 latest-refresh.json。並行完成時 freshness 以來源／請求時間排序，不以最後 push 時間讓較舊結果覆蓋較新指標。

如業務失敗但失敗 envelope 已發佈，Actions 仍標失敗；如結果發布失敗，Chat 依 run 狀態回報結果不可用，不拿上次成功代替。逾時或對話工具預算不足時回報 request/run 狀態，後續對話可續查；不承諾無工具支援的主動背景通知。

## 6. Chat 指示與呈現

`chatgpt-instructions.md` 保存完整日常規則，`docs/contracts/chat-ci.md` 保存機械輸入／結果契約；Project settings 僅放私人 repo/path/main 入口及同版讀取要求。每次任務 main 解析為單一 commit，該任務固定，下次可讀新版。bootstrap 由使用者安裝並確認；本地檔或 push 不等於 ChatGPT 已安裝。

預設回覆：結論與三 picks → 階梯（Score 降序，原價／係數／CP_adj 分欄）→ 有意義的變化 → 日期、版本及必要 caveats。針對單一模型比較可縮短，不每次印全表。只有相容 benchmark/version 才做數值差異比較；跨版說明版本變化，不製造可比的升降幅。

保留 GPT 約18.9實測保守取18、Grok16用戶情境、Contributor B級與 cache-write 假設、原价非訂閱折扣等必要語義。$79 只屬 GPT 組合，無 monthly N 不下回本結論；無實測速度不推定執行時間。查詢既有結果時明示快照日期，不假稱本輪刷新。

## 7. 驗證與切換

測試需覆蓋：請求關聯錯誤、額外檔案／未知參數、並行與重試、錯版資料、來源缺失、Contributor rescale、失敗仍紅燈、JSON/Markdown 同源、重算保留來源及歷史快照、分數排序與 no-Claude picks。既有測試持續通過。

先在本專案遠端驗證 CI 的 recompute 與 refresh 成功／失敗路徑，接著由目標 Chat 建分支提交請求、查該 run、以結果 commit 完整讀回；區分 OpenCode 實測與使用者提供的 Chat 端證據。實際驗收包括一個可與既有快照比對的 recompute，以及一個有新來源證據的 refresh。

只有 Chat 整條鏈成功、bootstrap 安裝獲確認後才更新 README/AGENTS 最新入口並停止 Notion 日常同步。既有 Notion 與所有歷史快照保留。

## 8. 可重用 skill 與專案契約界線

適合補入 chatgpt-project-sync 的跨專案教訓：按業務能力盤點而非只搜尋 dispatch 名稱；辨識 push bridge；分清工具可見／呼叫成功／完整流程成功；分清 blob、product/request/result commit 與 run ID；GET 不冒充寫入；可觸發不等於可主動通知；以證據避免重複探測。

具體 owner/repo、branch/path、係數、來源版本、排除規則及展示 schema 留本專案。skill 修訂是另外的授權／測試工作；本規格不宣稱它已修改或安裝。
