# 原 CP-new-high 鏈：跨模型轉折精簡試算

> **同日資料更正，覆蓋下方原試算：**使用者指出 Contributor 不支援 max；OpenCode 直接取得 [官方模型文件](https://dev.meta.ai/docs/models)，其 Muse Spark 1.3 說明明載 `"max" level for extended reasoning (available on Standard tier only)`。原候選 `Muse Spark 1.3 max Meta Contributor` 是錯誤的跨plan/effort身份，撤回其推薦及作為剔除證據的效力。GRADE-B換價不證明檔位可用。

排除該錯誤 identity 後，從原 CSV 的記憶體副本重跑 frozen CP-new-high 及下列同一候選轉折規則（18/16、min0、eps2/.05），得 **154候選→19個CP新高點→10個試算保留點**：Claude Opus5.5 max（僅比較）、GPT-6 Astra xhigh、Astra medium、Sol max、Sol high、Sol medium、Luna max、Luna high、Luna medium、Luna low。Astra medium與Sol max恢復，原試算Astra low也因新鄰點重新判斷而不保留。這是以已核對可用性更正的歷史情境試算，不是新取數；原CSV未改。以下原表只保留作錯誤分析，不再視為有效推薦。生產取數 effort 可用性驗證仍待修復。

日期：2026-09-27。**候選判準的探索結果，未批准為正式演算法、未更換部署。** 此文件不恢復已撤回的全候選 Pareto 改制草案。

## 輸入與不變前提

使用 `runs/2026-09-26-general-grok16/candidates.csv`（SHA-256 `e3916f8405904154f0e1dc648588bb08ce92f483cd616ba9be0ff2e5c726ed22`），公開版本推定 v4.3.2，api cost basis。GPT×18、Grok×16、Contributor×1；min_score=0，理由為同版本全候選情境比較，max_cost=None；原 frozen `compute_one_group` 的 eps_score=2、eps_cp=0.05 原樣調用。155 個付費候選產生 **20 個 CP-new-high 點**，本次只探索其後的精簡，不改第一階段。原正式 band 去重得16階，先前 Pareto 試版21點，三者不能混稱。

## 本次候選規則（尚待評估）

1. 對 Score 降序、CP_adj 遞增的**整條混合模型鏈**，每段降檔收益為 `g(A→B) = ln(CP_B/CP_A) / (Score_A-Score_B)`。這是相對效率變化的幾何診斷，不是實務成功率或效用估計。
2. 中間點 B 的轉折強度 `k(B) = ln(g(A→B)/g(B→C))`；越大表示到 B 之後，繼續降檔的收益越弱。首尾缺少兩側證據，暫給中性值0，**不是無限分或固定保送**；此端點處理是待評估的設計選擇。
3. 只在與其他現存點分差嚴格小於2分的點之間進行精簡。找轉折強度最高者，平手依CP高、Score高、identity排序；保留該點，移除距它不到2分的其他點。分差始終對照被選代表，不傳遞串群。
4. 剔除後重算剩餘鏈的新鄰點／轉折，再處理下一個近分區段，直到不存在相鄰分差小於2分的點。孤立的不同能力檔位保留；不按family配額，也不自動選每群最低分。

2分在這個**新候選判準**中是近分代表範圍，會影響第二階段剔除，不是先前純展示折疊的規則。它不宣稱2分內能力相等；需使用者接受此决策容忍度後才能採用。5%仍僅是原 frozen CP-new-high 的既有 anti-noise，未另發明5%購買價值門檻。

## 原始試算輸出

| 保留點 | Score | CP_adj | 註記 |
| --- | ---: | ---: | --- |
| Claude Opus 5.5 max | 57.6224 | 9.63 | 僅比較，不推薦 |
| GPT-6 Astra xhigh | 52.3863 | 408.42 | 留中間檔，非最高／最低 effort |
| Muse Spark 1.3 max Contributor | 48.0923 | 754.35 | GRADE-B，×1 |
| GPT-6 Astra low | 45.7819 | 1008.03 | 跨 family 混排 |
| GPT-6 Sol high | 42.8216 | 2057.45 | 跨 family 混排 |
| GPT-6 Sol medium | 39.7821 | 2885.06 | 與相鄰保留點已有不同分數層級 |
| GPT-6 Luna max | 37.2560 | 9848.12 | 跨代替代 |
| GPT-6 Luna high | 32.1482 | 20219.26 | 非最低 effort |
| GPT-6 Luna medium | 29.4620 | 30736.50 | 不因CP繼續上升而全部刪光 |
| GPT-6 Luna low | 20.9225 | 83992.39 | 此floor下的鏈尾 |

共10點，其中9個非Claude。剔除順序與當次代表：

1. GPT-6 Luna max → 剔 GPT-5.6 Luna max。
2. GPT-6 Astra xhigh → 剔 Claude Opus5.5 high、Astra max、Astra high。
3. GPT-6 Sol high → 剔 Sol xhigh。
4. Muse Contributor max → 剔 Astra medium、Sol max（此代表選擇依賴Contributor B成本假設）。
5. GPT-6 Luna high → 剔 Luna xhigh。
6. GPT-6 Luna low → 剔 GPT-5.6 Luna low。
7. Claude Opus5.5 max → 剔 Opus5.5 xhigh，皆只作比較。

本次 inline Python 計算另驗：保留點 Score 嚴格下降、CP_adj 嚴格上升；保留點相鄰分差至少2；每一個原20點都能在最終10點找到分差不到2的代表（含自身）。只做本快照的探索，不把這些 assertions 當通用正確性或正式選擇驗收。

## 解讀限制與下一步

- 本次可得到Astra xhigh、Muse Contributor、Sol high等中間轉折，沒有固定往最低分收斂。
- 端點中性值、近分範圍、全鏈貪心順序與數據微擾下的穩定性仍需評估；不能僅因本快照結果好看就宣稱最優演算法。
- Contributor成本是B級組件換價，cache-write按一般input價是未獲官方明示的假設；若成本證據改變，相關跨模型剔除要重算。
- 這是9/26歷史快照，不是9/27 fresh。當前 Inkling／MiniMax-M2.7 的成本缺口維持獨立阻擋。
