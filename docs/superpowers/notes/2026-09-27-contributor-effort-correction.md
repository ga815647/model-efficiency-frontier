# Muse Spark 1.3 Contributor max：不可用身份更正

日期：2026-09-27。使用者指出 Contributor 不提供 max；OpenCode 再直接取得 [Meta 官方模型文件](https://dev.meta.ai/docs/models)，確認：

> Supports all reasoning effort levels, including the "max" level for extended reasoning (available on Standard tier only).

同頁分列 `muse-spark-1.3`（Standard）及 `muse-spark-1.3-contributor`（Contributor）。**Muse Spark 1.3 max Meta Contributor 是不可用的 model×effort×plan 組合。** GRADE-B 換價不能讓不存在的服務組合成立。

## 根因與影響

原取數只驗 model 在定價頁的 plan 列表及費率，對 AA Muse Spark 1.3 的每個 effort 做跨 plan 組件換價，沒有先驗該 effort 是否在 Contributor 提供。受影響者包括9/26的155行CSV／原階梯／對應CI結果、9/27純雙軸試版、混合CP鏈轉折試算中含該行的原始版本。原檔保留為歷史證據；引用須帶本更正，不能直接當作目前有效推薦。

新的比較要先排除這個身份，再重跑CP-new-high及後處理；只從最終表刪Muse會遺漏之前被它擋掉的候選。不能把max改名xhigh、不能將max分數／用量移給xhigh。Standard／AA-public max保留原身份；Contributor xhigh使用自己的同版分數、組件及可用性證據。

唯讀核對舊Chat成功run `36282186076`、固定結果commit `f080fa6b3104707a419335b1489ab2be7cee4ba8`：155個status、16階；非法Contributor max當時是`cut → GPT-6 Sol max`，並未成為原正式三picks。Contributor xhigh是`excluded: CP_adj no new high`。直接錯推max發生在後來的實驗表／轉折試算；原正式計算仍錯誤允許它參戰，因此兩個入口都需修復，不能因最後cut掉就忽略。

## 修復範圍

- 新取數保存當次官方model／effort限制證據，先核對再換Contributor價。
- 歷史快照重算保留原CSV及完整候選稽核，把不可用max列為明確excluded，禁止參與CP更新、去重及picks。
- 舊baseline包含max時，只為這個已正向證偽的組合記錄有證據的退出；其餘候選／effort消失guard維持。
- 驗證新證據可由publisher保存，涵蓋成功與失敗路徑。

此修復不實施尚未定案的轉折精簡算法，也不解除Inkling／MiniMax-M2.7的即時task-cost缺值。已在記憶體排除不可用max重播候選轉折法：154有效候選／19個CP新高點／10個試算保留點，詳見 [試算更正](2026-09-27-cp-chain-knee-probe.md)。原CSV未改，這不是fresh或正式CI驗收。

## 實作驗收狀態

本地修復提交 `365e699`、覆核邊界補強 `3b4313a`。控制端重新執行 `python3 -m unittest discover -s tests`：167 tests，25.559秒，全部通過。三項覆核發現已補回歸：舊身份退出須精確綁定1.3 Contributor max、矛盾identity欄位拒絕、成功及失敗refresh均驗已取得的官方能力證據。

控制端另跑 `ladder_extra.py` 原155行快照至 `/tmp/opencode/model-efficiency-corrected-ladder.md`：16階；非法max在CP計算前excluded，理由包含官方URL及2026-09-27核對日；xhigh維持自己的分數／成本，依CP規則excluded。原run輸出未覆寫。本地bare-Git測試涵蓋五來源、154行成功fixture與失敗refresh證據發布；fixture不等同即時fresh成功。

雲端部署／重算驗收待追加；目前仍不能宣稱當前fresh成功。
