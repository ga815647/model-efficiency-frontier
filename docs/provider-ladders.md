# 四種訂閱：各自建議模型與effort階梯

2026-10-07使用者明確要求「移除僅供比較、全部混排，網頁直接產出四家供應商的建議模型與檔位LADDER」。本契約優先於此前Claude永不推薦條款，但只改新版本；不回寫歷史。

## 正式新結果

新request **v3**沿用v2精確根欄位、唯一request branch/file及七欄parameters；成功result **v4**沿用v3精確根欄位與row，僅新增成功欄位 `eligibility_policy`，值必為 `all-providers-v1`。失敗仍只有共有根欄位、不含資格或成功衍生欄位。v4所有候選的`comparison_only=false`，Claude可進anchors與相鄰upgrade。新產品獨立標記`bridge/recommendation-policy.json`精確為 `{"policy":"all-providers-v1","result_schema_version":4}`；首頁除全部情境參數相等，還必須是v4，舊資格即使日期較新也不能佔正式首頁。

CP-new-high、固定2分視窗、EPS、GRADE-B、身份／effort可用性及成本換算不變。Claude原本即參戰數學；新資格影響anchors及upgrade可用行，沒有調整chain或trace公式。request v1→result v2、request v2→result v3、合法歷史result v1均保留精確原義；來源重播按保存版本明確分派，不用新資格重新解釋舊結果。

## 四家專屬結果

首頁保留完整混排兩入口，另直接列出四種訂閱各自的能力／成本入口及完整階梯連結。選供應商後，僅該家所有已驗證候選重新跑相同選型器；不是從混排final行篩選，因此混排未入選的行可能在專屬比較中入選。effort是選出的檔位，不提供effort篩選選單。所有數字仍來自相同快照與倍率，不新增觀測、價格或訂閱可用性推定。

family按既有身份慣例：GPT-前綴→ChatGPT、獨立Gemini前綴→Google、既有Grok及Claude-family辨識；Contributor優先排除四種訂閱專屬集合，仍可在全部候選中參戰。供應商訂閱當期可用模型／effort須以供應商介面確認，不把AA/API身份等同訂閱保證開放。缺該家候選／floor排空時正確空階梯及null入口，不補位。

後端`bridge.provider_view`先驗完整成功envelope，從全`candidate_statuses`保留原價、分數、factor、GRADE與來源，重建選型器輸入。caller在發布前已由`site.load_record`核對immutable introduction、request關聯、原始source proof與同版本重播。view是獨立`kind=provider-ladder`／`schema_version=1`網站衍生資料，**不是result envelope**；其中calculation不冒稱新的request/run。另記parent result SHA-256及publication，manifest記view SHA-256、URL、scope與產品版本；原`result.json`完全不改。

每次allowlist增加各固定結果的 `providers/{gpt,gemini,claude,grok}/{index.html,view.json,manifest.json}`；首頁同時有這四組alias，全部指向同一次正式結果。固定結果的供應商URL永久對應該request/run/attempt；重新部署保留所有成功v2/v3/v4頁，歷史Claude專屬頁仍僅比較，不偽改當時資格。

供應商切換採原生連結，無JavaScript仍可切換與閱讀；瀏覽器只做文字搜尋、展開，不跑選型／抓費率。備用HTML保留完整混排已驗證結果。來源退出原文仍在兩入口後、階梯前；供應商頁沿用完整來源退出摘要，候選查詢只列該家數值或來源觀測。

## 驗收與部署

測試涵蓋真正重新選檔、同版本成本不變、資格版本偽造拒絕、舊結果不佔v4首頁、四家各自anchors／upgrade、空集合、唯一request執行／publication／來源讀回，以及360／390／1280px、鍵盤、搜尋、空結果、展開及no-JS切換。公開前第三方再散布檢查與實際GitHub Pages權限仍是獨立門檻；建置artifact不是已部署網址。
