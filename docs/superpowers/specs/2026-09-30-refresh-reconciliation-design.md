# Fresh 候選對帳：舊模型退役與本次缺價退出，不綁架整批刷新

日期：2026-09-30。**狀態：對談方向已確認，書面規格待使用者審閱；尚未批准實作計畫、改產品程式或發布修復。** 對應 [issue #1](https://github.com/ga815647/model-efficiency-frontier/issues/1)。本規格更換 fresh 來源候選對帳政策，不更換已發布 v2 的階梯數學；下方技術落地選擇屬本次書面審閱內容，不把方向確認當作文件批准。

## 1. 目的與已確認前提

有效的新模型正常進入 fresh 比較；個別舊候選已淘汰或本次缺 task cost，不再被錯報為消失而阻斷整批 pipeline。允許候選有理由地退出，不承諾目錄每一行都能參戰，也不把有明示缺口的結果宣稱為全市場完整排名。

使用者要求「如果只是因為已經是舊版模型、沒有使用價值，可以直接丟掉，不要因為垃圾把整個 pipeline 卡住」，並對以下具體方向回覆「好」：

- MiniMax-M2.7 當次 `deprecated=true`：排行退役，不再強制後續刷新找回。
- Inkling 當次 `deprecated=false`、task cost 缺值：本次來源排除，不宣稱永久退役，不擋其他有效模型。
- 「丟掉」是退出候選與強制保留義務，不是刪除歷史快照、原頁或稽核證據。

本版自動退役只依當次 AA 明確的 `deprecated=true`，不依模型年份、名字看起來老、另有 successor、分數偏低或人工推定購買價值。這是比較記錄的來源淘汰標記，不代表 provider 的 API 已下線。其他退役依據與人工黑名單不在本版範圍。

維持 request v1／result v2 與歷史 v1 相容、固定三個 commit、單一 General 同版本／同 cost basis、floor＋理由、GRADE-A/B、Contributor effort 可用性、CP-new-high＋固定兩分視窗、final-only 兩入口及 no-Claude 推薦限制。不得沿用舊 task cost、套近似身份／successor 的分數或成本、用 token 單價猜 task cost，亦不得改歷史輸入或已發布結果。

## 2. 根因與重現基線

已發布產品 `0a6ea5dbbd929ecc9d57cd36d4402db640638ca4` 先把缺分數／成本的行放入 excluded，再以 `previous_slugs - included_slugs` 當 lost，因此把「仍在當次來源但不可計算」誤報為 `missing_candidate`。

固定失敗證據：request `c8435e4c-b45f-4d7d-a6c3-48df75ba7a11`、run `36666859368-1`、publication `ef77e1fff6980164aac5c0610ead7eff26bcd671`。OpenCode 獨立取得該 publication 五份原頁，逐一計算並比對保存的 SHA-256，以相同 bytes 重播，復現 `missing_candidate: ...: inkling,minimax-m2-7`。這是歷史失敗重播，不是新 refresh。

| 身份／slug | 實測分數 | 當前 task cost | estimated | deprecated | 新政策預期 |
|---|---:|---:|---|---|---|
| Inkling／`inkling` | 24.9847810999384 | null | false | false | 本次缺價排除 |
| MiniMax-M2.7／`minimax-m2-7` | 22.7578150287271 | null | false | true | 排行退役 |
| GPT-6.1 Sol 五檔 | 當次各自實測 | 當次各自正值 | false | false | 五檔進付費候選，不保證五檔都留 final |

MiniMax-M3、Inkling Small 是另有當前分數／task cost 的獨立身份，可以各自參戰，不能作上述兩行的替代資料。

未修改產品基線：`python3 -m unittest discover -s tests`，229 測試通過。現有 null-cost 測試要求舊硬失敗；實作先以新政策測例形成 red，再改產品，不能把基線通過稱為修復完成。

## 3. 生產政策及失敗邊界

前提是當次來源通過解析、唯一 slug、數值及同版佐證。`deprecated` 僅接受 boolean 或缺值：只有 true 可退役，缺欄／null 不推定淘汰，其他型別是來源形狀錯誤。分類優先序：deprecated → estimated → missing_score → missing_task_cost → zero_cost → usable_paid。

| 當次狀態 | 本次處理 | 前次受追蹤身份的對帳 |
|---|---|---|
| 明確 deprecated=true | `retired`，即使仍有分數／成本也不參戰 | 記理由並退出後續強制追蹤，不阻擋 |
| 非退役、非 estimated，有有效分數，但 task cost 為 null／缺欄／Flight `$undefined` | `observed_unusable`，reason=`missing_task_cost`，不參與 CP | 已觀測、不算消失；本次排除、不阻擋，仍留追蹤 |
| 有有效實測分數及正值當前 task cost、身份可用 | `usable_paid`，沿現行候選流程 | 繼續追蹤 |
| 非退役但 estimated、分數缺失或成本為零 | 依既有 estimated／缺分數／free 邊界，不進付費比較 | 若原本受追蹤，保留硬失敗，但報 `present_candidate_unusable` 而非 missing |
| 受追蹤 exact slug 當次不存在，沒有已驗證退出依據 | 不推定退役，不用其他 effort 補位 | `missing_candidate`，保留三遍核對的已完成／待核對證據，不冒稱已證明不存在 |
| 結構損壞、衝突 slug、非法數值、身份／版本模糊 | 不產生可交付成功結果 | 沿來源完整性硬失敗 |

未曾受追蹤的新 estimated／缺分數／zero-cost 行仍按既有 sidecar 排除，不因此阻擋整頁。新缺價行同樣保留當次原始資料及明確理由，但不把所有從未可用的來源行列為未來強制保留義務。

不擴大版本豁免：Grok／Muse 四個精確分數／成本 crosschecks 仍須完整一致，佐證行缺值而無法確認同版就失敗。Contributor 當次費率、同版組件、有效 plan 與官方 effort proof 同樣不降級；Muse Spark 1.3 Contributor max 的 Standard-only 排除及歷史退出證據不變。

排行退役不是永久黑名單：日後同一 exact slug 再次有當次非退役、可用實測資料，可重新參戰；不恢復舊資料或改寫之前的退役記錄。若排除後沒有任何 paid 候選，延續 `empty_paid` 失敗，不製造可交付排名；有 paid 候選但 floor／cap 使階梯為空，仍沿現行 v2 空階梯及 null anchors 規則。

## 4. 可用清單與追蹤清單分開

`source_by_slug`、`inventory.slugs`、CSV 仍只列本次可用 paid public 候選；`inventory.contributor_efforts` 仍只列實際生成的可用 Contributor 行。不得把 null-cost 行塞入這些數字集合。

`snapshot/evidence/source_map.json` 新增 `reconciliation` 節：

| 欄位 | 定義 |
|---|---|
| `policy` | 固定 `observed-inventory-v1`，未知值拒絕 |
| `previous_tracked_slugs` | 從已驗證前次來源取得的受追蹤 public slug |
| `observed_slugs` | 本次解析到的全部 public slug |
| `tracked_slugs` | 下次仍須對帳的 public slug |
| `retired_slugs` | 本次明確 deprecated=true 的 public slug |
| `status_by_slug` | 每個 observed slug 恰好一項 `{state, reason}` |

四個 slug 陣列均排序、無重複。state 僅 `usable_paid`／`observed_unusable`／`retired`；usable 的 reason=null，retired 的 reason=`deprecated`，其餘 reason 僅 `estimated`／`missing_score`／`missing_task_cost`／`zero_cost`，遵守第 3 節優先序。姓名、score、cost、estimated／deprecated 原值與來源日期／雜湊保留於當次 `leaderboard_records.json`、原頁及 `sources.json`。

令 P 為前次受追蹤集合、U 為本次可用 public 集合、R 為本次明確退役集合，成功時 `tracked_slugs = (P ∪ U) − R`。新版前次來源的 P 取其已驗證 tracked；legacy 已發布來源或核准歷史快照的 P 沿既有 paid inventory 取得；首次無前次來源則 P 為空。

Inkling 一次缺價仍留追蹤，恢復價格後可入列，不能排除一次就忘掉身份。MiniMax-M2.7 退役後不在下次 P，之後不再出現在來源也不阻擋或反覆尋找。當次退役資訊完整保存即可，不新增永久黑名單或跨快照複製整套舊原頁。

`excluded` 與 `free-sidecar.json` 以精確 reason 區分缺價／free／估計值／退役。失敗亦保存已完成對帳及具體缺口；`missing_candidates.json` 只把未觀測身份標 missing，已觀測但不符合本版放行條件者另保留 present-but-unusable 診斷，不混成消失。

## 5. 模組、驗證與相容

- `scripts/aa_public.py`：精度及 optional deprecated flag 的嚴格解析。
- `scripts/refresh_snapshot.py`：對帳前區分觀測／可用／退役，生成同一份分類及追蹤證據；有合法候選就繼續生成新 CSV。
- `bridge/inventory.py`：共用驗證 usable 與 CSV／result 一致、observed 與原頁解析一致、退役必有當次 true 證據、缺價必對應當次實測分數及 null task cost、tracked 公式成立。
- `bridge/runner.py`：latest-refresh 前次來源及 fixed-source 重算均讀固定 publication，驗證新版證據；重算不取今天來源替固定舊資料佐證。
- `bridge/publish.py`：驗證後才發布／更新 pointer，新錯誤碼納入既有 models-proof 之後的能力證據檢查，不削弱 Contributor guard。

新產品帶 `bridge/refresh-policy.json`，精確內容 `{"policy":"observed-inventory-v1"}`。發布端及 Git 來源讀取端從**已驗證、固定的 product commit**判定政策：有此標記的新產品成功 refresh 產物必須帶完整 reconciliation 與原頁／parsed／hash 證據，缺失就拒絕；沒有標記的已核准舊產品來源使用 legacy 規則。未知標記拒絕。不得讓 untrusted source map 自稱 legacy 來降級驗證，也不執行來源產品程式來判讀標記。recompute 則依其固定 refresh 來源原始 envelope 的 product 判定來源政策，不能因本次重算使用新產品就要求舊快照有新欄位。

舊已發布 v1/v2 成功快照延續原完整 paid inventory／CSV／result 檢查，不強加當年不存在的欄位；排隊中合法舊產品產物依可信 product 標記走 legacy 發布。新 source map 中 present-but-unusable／retired 不能藉相容模式漏驗。request 及 result 精確欄位不變，來源 policy 標記不是新 request 參數。

共用 inventory 入口取得 leaderboard 原始 bytes、parsed records、source hashes 與可信政策模式，不能只驗 CSV digest。三個消費端共用同一規則，不各自另寫分類。原頁 hash／parsed 不一致、分類遺漏、假退役、舊價混入或缺價行進 CSV 均拒絕；現有 Meta proof 與版本檢查延續。

## 6. 結果、展示與發布

`candidate_count`／`candidate_statuses` 仍只指生成 CSV 的 paid 行；缺價／退役來源行只在來源稽核，不偽裝成具備數字 cost 的候選。GPT-6.1 五檔正常進候選後由原 v2 決定 final／cut／excluded，不保送新模型。

沿用 result `caveats` 明示受追蹤候選的退出，例如「MiniMax-M2.7 來源標示淘汰，退出新比較；Inkling 當前 task cost 缺值，本次未參戰且未沿用舊價」。短摘要由同一對帳結果生成，validator 核對應披露的身份／理由未遺漏；Markdown／HTML 與 Chat 結論附近保留它，完整記錄留來源證據，不把幾百個未曾可用的舊來源行全部印在推薦表。來源日期照實講，不宣稱缺價身份永久退役或候選全部完整。

`latest-success`／`latest-refresh` 仍只按驗證過的 success envelope 及原排序規則推進，合法排除不新增第三種 result status。完整性失敗照常發布診斷，不發布部分報表、不更新成功 pointer、不用舊推薦補位。

歷史 CSV／result／report 不回寫。固定 9/26 重算不套今天 deprecated、不抓新來源；其結果仍依原 pinned CSV、原 v2 演算法及既有身份修復。新 successful refresh 可供之後固定重算，保留當次來源排除 caveats 與驗證鏈。

實作完成才更新 Git 規則及 Chat 指示的生產狀態；bootstrap 定位、Project settings、Notion 與網站政策不改。Git 更新不等於 Chat 已讀或完成新流程實測。

## 7. 驗收

1. 保存 9/30 類型 fixture：兩個舊身份仍存在且 cost null、MiniMax-M2.7 deprecated=true、Inkling deprecated=false、GPT-6.1 五檔完整；附原頁來源及 fixture 精簡／變更說明。
2. 成功生成新 snapshot、v2 result／Markdown／HTML；MiniMax 退役、Inkling 缺價排除，兩者均不在 paid CSV／CP／ladder；GPT-6.1 五檔在候選，不硬編碼 final 名單。
3. 有成本但 deprecated=true 仍退役；deprecated=false 且成本恢復可參戰。缺欄／null 不當 true，非法 deprecated 型別及衝突身份失敗。
4. 下一次退役 slug 消失不阻擋；曾缺價但未退役的追蹤 slug 消失仍報 missing 並留 pending 核對；恢復成本後可重新入列。
5. 舊身份 present+estimated／missing_score／zero_cost 的硬邊界保留，報 present-but-unusable；新 sidecar 不產生假失敗。版本 crosscheck／Meta 能力或組件缺口仍失敗。
6. 原頁、parsed、hash、分類、tracked／retired、退出 caveat 被修改／遺漏，在發布與 pointer 推進前拒絕；覆蓋舊價填 null、假 deprecated、缺價當 free、去掉新證據冒稱 legacy。
7. Contributor max unavailable、exact identity 退出、xhigh 自身資料及 Grade-B 換價不回歸；成功與失敗皆驗官方 models proof。
8. legacy v1/v2 來源仍可讀／固定重算；新刷新可作 `_previous` 與 subsequent recompute，CSV hash／版本／inventory／退出 caveats 一致，不在重算中抓今天資料。可信產品 policy 未知或缺失不能逃逸新產物驗證。
9. pointer 成功／失敗／日期排序、append-only、JSON／Markdown／HTML 身份一致及 artifact bytes 過檢；全套測試通過，政策變更測試經 red-green 更新，不刪完整性測試。
10. 審閱及發布後實際雲端 refresh：先明示 operation=refresh，再重新取得當次來源；固定 request／product／publication／run，核對來源日期、分類、CSV、result、報表及兩個 pointer。live 如有其他完整性問題照實記失敗，不用 fixture 成功冒充 live 成功。

## 8. Issue #2 與下一關卡

Issue #2 是獨立的 Chat 短續接 freshness guard：寫 request 前明示 operation／固定來源日期與「不會抓新模型」，最新資料意圖不得直接沿用 pinned recompute；其 bounded 短設計已提出，不因本次 #1 政策確認就視為已實作／驗收。它不改 request schema，也不能用 #1 取數成功代替對談路由驗收。

本規格先經使用者書面審閱。確認後才用 writing-plans 寫 #1 實作計畫，計畫審閱與執行方式確認後進 TDD／實作。#2 的短設計另行確認後按 bounded 流程處理，不另新增 architectural 規格。
