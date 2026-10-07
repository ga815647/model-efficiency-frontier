# 2026-10-07：約 US$100 個人訂閱的 API-equivalent 倍率

這版由使用者提供研究、指定取值並授權回填。正式表保存在 `bridge/site-policy.json`，四項依據均為 `basis=user_specified`。本專案核對了下列可存取頁面的相關敘述，但未取得各使用者的原始 token logs；不能把頁面可讀、公式可重算說成全部實測已獨立驗證。這版取代先前 Gemini 6／Claude 37／ChatGPT 18.9／Grok 16；歷史結果保持原情境。

| 平台／標準方案 | 月費 USD | 固定倍率 | 使用者建議範圍 | 使用者信心 |
| --- | ---: | ---: | --- | --- |
| Claude Max 5x | 100 | 40× | 約32–45× | 中 |
| ChatGPT Pro 100 / 5x | 100 | 17× | 約14–21× | 中 |
| SuperGrok Plus | 100 | 5.2× | 約3–6× | 中低 |
| Google AI Ultra 5x | 99.99 | 3.6× | 約3.5–6× | 低～中 |

## 統一口徑與公式

僅計文字／推理／coding／agent 的模型運算。空間、YouTube、圖片影片、Voice、GCP credits、獨立 Agent SDK credits 等不納入分子。採美元標價，未額外推估地區差價、稅、匯率或促銷月費；實際方案不同時須另立情境。

`M = 訂閱額度的同廠商 API-equivalent 金額 / 訂閱月費`。

完整週額度的 API 等值為 `W` 時，`M = W × (52/12) / 月費`。只有部分 weekly meter 時，先以 `W = 該段 token 的 API 等值 / meter 消耗比例` 外推。這是假設當期額度可用且用滿的經濟情境；未用滿、模型組合、限流與額度改動都會影響實際比值。官方案名的 5x／20x 只表示同公司方案的用量關係，不能直接當 API 倍率。

token 等值須依當時真正模型的 input、output、cache read/write 價格加總。可觀測 thinking tokens 才計入，不補造不可觀測量。證據優先序：完整額度加 logs／API 費率；部分 meter 加 logs；多週或多帳號交叉檢查；官方方案間用量比例。沒有可換算用量的體感描述不作正式常數依據。

網站仍用 `Cost_adj = Cost_orig / M`，`CP_adj = Score / Cost_adj`。倍率衡量訂閱相對 API 的費用，不是能力分數；選型視窗、EPS、分數、原價及 Claude 僅比較規則不變。

## 四項推導與查證界線

### Claude：40×

使用者取 Max 5x 每週約 $1,000–1,200 API-equivalent，將臨時 +50% 額度正常化至 +25%：

`(1000–1200) × 1.25/1.50 × 52/12 / 100 = 約36.1–43.3×`；中點約39.72，固定40。

- [Anthropic Max 說明](https://support.claude.com/zh-TW/articles/11049741-%E4%BB%80%E9%BA%BC%E6%98%AF-max-%E6%96%B9%E6%A1%88)：已核對 $100 Max 5x、5 小時窗口及 weekly 限制；未公開可直接換成 API 金額的絕對 quota。
- [DevelopersIO 三帳號研究](https://dev.classmethod.jp/articles/claude-max-20x-weekly-limit-not-4x/)（2026-08-20）：已核對 JSONL 去重、ccusage 交叉檢查、上述每週 API-equivalent 區間與促銷背景。比較帳號的模型使用不同，部分帳號的網頁使用紀錄不完整；並非三個完全相同 workload 的完整對照。
- [Danube Labs](https://danubelabs.net/en/blog/claude-max-weekly-limits-cut)：已核對其 +50%→+25% 轉述與單帳號 calendar-week 量測。額度調整的原始公告未在本次取得；重算的正常化仍是有條件假設。reset 不一定對齊日曆週，模型與費率改動也可能影響等值。獨立 Agent SDK credit 不算入40×。

### ChatGPT：17×

使用者下緣：`959.87 / 3 × 52/12 / 100 ≈ 13.86×`；上緣：`481 × 52/12 / 100 ≈ 20.84×`。採乘法中點 `sqrt(13.86 × 20.84) ≈ 17.0`。

- [OpenAI Pro tiers](https://help.openai.com/en/articles/9793128-about-chatgpt-pro-tiers)：已核對 Pro 100 為 $100/月；目前頁面沒有足以獨立確認該實測「5x」額度及固定 weekly quota 的敘述。
- $959.87／三個完整 weekly meters／707,989,104 tokens 的下緣，在使用者提供文字中只有未解析的 content-reference，缺原始連結；本次未獨立核對。
- [ModelDial](https://modeldial.com/en/subscriptions?calc=work&calc_demand=1&calc_effort=max&calc_left=100&calc_row=openai-plus-gpt-6-sol&period=week)：已核對9/29 Astra 樣本約 $481/week，來自2% meter外推，樣本很小，不是完整週測量。兩端 workload 不同，中點是使用者選用情境，不是統計信賴區間。

### Gemini：3.6×

使用者先取約 `$1.5 / 5h window`，再以 `2800/250 = 11.2` 個 weekly window equivalents：

`1.5 × 11.2 × 52/12 / 19.99 ≈ 3.64×`。假設 Ultra 5x 的價格與相關額度都約為 Pro 五倍，固定3.6。

- [Google 方案頁](https://gemini.google/subscriptions/)：已核對 Pro $19.99、Ultra 5x $99.99 與相關較高用量敘述；頁面未公開此推導所需的全部 weekly token 額度。
- [Level Up Coding](https://levelup.gitconnected.com/geminis-new-usage-limits-set-reddit-aflame-with-hate-mail-fb2c2452bf3b)：本次HTTP403，未繞過限制；三個 prompts／約202k visible tokens／33%／$0.51 的敘述未獨立核對，thinking tokens 不完整。
- [RoninForge](https://roninforge.org/antigravity-credits/weekly-quota-lockout/)：已核對250 units/5h與2,800/week；頁面明示數字是社群量測，並非Google公布額度。其引用量測早於10/7，且 Antigravity 與 Gemini prompt 資料來自不同產品／時點；不能直接證明共享額度完全可比。
- [LLM Perks](https://www.llmperks.com/subscriptions/google/google-ai-ultra-5x)：已核對約$400/月估計含$40 GCP credits；扣除後約$360/$100=3.6。這仍是第三方 package-value 估計，不能當獨立完整 quota 實測。

### Grok：5.2×

`121 × 52/12 / 100 ≈ 5.24×`，固定5.2。另一 Heavy $300 方案 `401 × 52/12 / 300 ≈ 5.79×` 僅作方向比較。

- [xAI pricing](https://x.ai/pricing)：已核對 SuperGrok Plus $100/月與 higher usage 描述，未公開固定 weekly token quota；周邊功能不納入倍率。
- [ModelDial](https://modeldial.com/en/subscriptions?calc=work&calc_demand=1&calc_effort=max&calc_left=100&calc_row=openai-plus-gpt-6-sol&period=week)：已核對9/27 Plus 約$121/week 來自15 percentage points外推，Heavy約$401/week 是17-run估計。皆不是完整週額度量測，也不是相同方案、相同workload的對照。

## 查證紀錄與後續操作

上述連結於2026-10-07檢查：九個HTTP200，一個HTTP403；HTTP成功只表示頁面可讀。本庫保留摘要、計算與連結，不提交第三方整頁內容或私人使用者 logs。使用者的範圍與信心原樣標為「使用者建議」，不升格成專案獨立驗證。

未來 Chat 可先研究，再按明確「回填」指示更新正式表、日期、公式、依據與限制，經產品PR及review合併。要求產生LADDER時另走唯一request bridge；回填不能改寫既有結果。流程見 [兩種Chat操作](../subscription-factors.md)。
