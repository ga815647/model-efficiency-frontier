# Free / quota sidecar — 2026-09-24 General v4.3 run

- as-of: 2026-09-24 ｜ benchmark: AA Intelligence Index v4.3（live v4.3.2） ｜ cost basis: n/a（sidecar 不進數學）
- 規則：free/quota 行永不進入數字 frontier（禁令 7）；初版只列 quota/throttle，不攤提 effective cost（AGENTS.md §6 月用量假設未定）。

## 本 run 的 free 行

無。AA model/provider 頁（Muse Spark 1.3、Kimi K3、GLM-5.3-Flash、Grok 4.7，2026-09-24 检索）未見 free-tier quota 可收錄行；candidates.csv 無 `is_free=true` 行（腳本輸出 "FREE sidecar: none" 佐證）。

## 備註

- Kimi K3 low 原 free-sidecar 候選？否——它是付費 Standard 行但變 estimate 無 cost，屬 GRADE-C 方法排除，不進 sidecar。
- 如後續從 provider docs 補 quota（如 Kimi free quota），另開行以 `is_free=true + quota` 記入，不動本次 frozen candidates.csv（改了要新開 run）。
