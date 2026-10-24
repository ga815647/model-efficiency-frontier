# Kimi 國際版訂閱方案研究（2026-10-24）

## 結論與範圍

本次產品新增 **Kimi 第一方訂閱方案研究**，與 BytePlus ModelArk 的代管方案 registry 分開；尚**不**宣稱 Kimi 是正式第五條訂閱 LADDER，也不替 Kimi 模型指定任何未證實的訂閱倍率。研究 sidecar 為 `bridge/kimi-plans.json`，研究 ID `kimi-international-membership-2026-10-24-v1`，查證日 2026-10-24。月費和年繳總額的價格截圖日期是 2026-10-19，購買時仍需重新確認地區與結帳價格。

| Kimi plan | 直接按月付（USD） | 年繳總額（USD） | 年繳折算月費（非逐月支付） | Agent credits 相對 Plus | K3.1 Pro context / 高速 |
| --- | ---: | ---: | ---: | ---: | --- |
| Plus | 19 | 180 | 15 | 1× | 256K / 無 |
| Pro | 39 | 372 | 31 | 2× | 最高 1M / 有 |
| Max | 99 | 948 | 79 | 5× | 最高 1M / 有 |
| Ultra | 199 | 1908 | 159 | 10× | 最高 1M / 有 |

所有四個新方案都有 Kimi Code 與 K3.1 Pro；K3.1 Pro Highspeed 需 Pro 以上。2026-10-23 推出的 K3.1 Pro 僅能在思考開啟下使用 low／high／max，官方稱 Highspeed 性能相同、速度約 2–3 倍。Kimi Code 的官方新方案有滾動五小時限額、共享的每月額度、**不再有舊方案的每週限額**；不表示「無限」使用。舊會員的舊方案另有每週限制，不可混寫。Kimi Code 的 CLI／Desktop／VS Code／第三方工具共用額度。

## 為何不能直接給出 2×／5×／10× 的本專案倍率

本專案倍率定義：

`M = 某訂閱方案一個月可實際使用的文字、推理、coding、agent 模型運算 API-equivalent 費用 / 其訂閱月費`

明確排除影音、圖片、3D、雲端儲存、一般辦公工具福利與另購的 API credits。官方「Agent credits」的相對 2×／5×／10× 是方案福利／共享額度的比值，**不是可折算成 API-equivalent 金額的本專案 M**。缺少可靠的完整月度使用、5 小時限流後可用吞吐、模型 effort 組合與 API 等價成本量測，故 sidecar `factor: null`；不能猜 1×、套借其他訂閱倍率，亦不對既有正式四家表加 Kimi 鍵。

2026-10-23 公開的 Artificial Analysis K3.1 Pro 是 Intelligence Index 55 分、API 約每百萬輸入 token USD2、輸出 USD10；這是**新模型的 API 價格和能力研究**，不是訂閱成本或本專案的有效推薦輸入。正式網站固定來源 2026-10-07，早於模型發布。沒有使用者明確要求來源 refresh、同版驗證成功及新計算前，不得把 55 分混入 10/7 快照排名或推算 Kimi 專屬 LADDER。

## 儲存、驗證與更新規則

- 研究 payload：`bridge/kimi-plans.json`，由 `bridge/kimi_plan.py` 嚴格檢查方案、價格、日期、可用限制、官方與 AA URL、`factor:null`。
- GitHub Pages builder 只複製 allowlist 的 sidecar `kimi-plans.json`，首頁與所有四家訂閱 scope 都顯示研究入口 `#kimi-plans`；不篡改 `result.json`、`report.html`、候選、算法或排名。
- `manifest.json` 的 `kimi_plans.research_sha256` 綁 exact bytes，提供研究 `research_id`、固定頁研究 URL；公開驗證除了 hash，也會跟當版產品 checkout 的完整 bytes 比較，防止網站單靠修改 manifest 重綁假證據。
- 登錄新品與研究更動仍使用獨立產品 branch／PR、CI、review，合併後另驗 Pages build/deploy 及匿名可讀網站；原 `bridge/site-policy.json` 正式四家倍率不變。新計算只走 request v3／result v4 的既有資料運行契約，歷史結果不回寫。

## 查證來源（2026-10-24）

1. [Kimi Help — Pricing details](https://www.kimi.ai/help/membership/membership-pricing)：方案價格、年繳、舊/新會員配額區別；網頁註記 10/19 截圖。
2. [Kimi Help — Membership plans overview](https://www.kimi.ai/help/membership/membership-overview)：Agent credits 相對額度、功能共用池。
3. [Kimi Code — Membership Benefits](https://www.kimi.com/code/docs/en/kimi-code/membership.html)：rolling 5h、無週限額（新）、每月配額、1M 與 Highspeed 適用條件。
4. [Kimi Code — What's New](https://www.kimi.com/code/docs/en/kimi-code/whats-new.html)：10/23 K3.1 Pro、高速版與 thinking effort。
5. [Artificial Analysis — Kimi K3.1 Pro](https://artificialanalysis.ai/models/kimi-k3-1-pro)：2026-10-24 查得新模型 55 分、API 2/10 美元/百萬 token，不能偷換先前快照。

「研究已存」不代表新模型來源已 refresh、得出正式倍率、套入訂閱 LADDER、完成 merge，或已在公開 Pages 部署，狀態應逐層驗收。
