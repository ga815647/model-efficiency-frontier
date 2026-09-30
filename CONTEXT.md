# 模型效率前線

付費模型的能力／成本比較與個人使用情境階梯。此檔只記術語；現行政策與狀態以專案規約及來源契約為準。

## Language

**Identity（候選身份）**：
由模型版本、reasoning effort、provider／route、pricing plan 與 cost basis 等條件共同界定的比較單位；任一條件不同就是另一身份。
_Avoid_: 只用模型 family 名稱代表同一候選

**Observed candidate（已觀測候選）**：
當次來源中能確認存在的候選；存在不代表分數、成本或使用資格足以參與數字比較。
_Avoid_: 可用候選

**Usable paid candidate（可用付費候選）**：
具備同一 benchmark 版本的有效實測分數、正值當前 task cost，且身份與使用資格成立、未排行退役的候選。
_Avoid_: 來源中所有模型

**Ranking retirement（排行退役）**：
來源確認淘汰的候選退出新比較與後續強制保留清單；不等於 API 服務下線，也不等於刪除歷史證據。
_Avoid_: 候選消失、歷史刪除

**Current-source exclusion（本次來源排除）**：
已觀測身份因本次來源資料不適合數字比較而未參戰；單次缺價不表示身份永久退役，缺價也不是零成本。
_Avoid_: 永久淘汰、免費模型
