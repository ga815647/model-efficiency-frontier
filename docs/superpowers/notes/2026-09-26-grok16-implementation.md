# Grok ×16 番外篇 renderer 實作（2026-09-26）

只更動 `scripts/ladder_extra.py`、對應單元測試及政策文檔；不取得新資料、不寫既有 run、不發布 Notion。GPT `--factor` 預設 18、`--prefix GPT-` 不變；`--grok-factor` 預設 16（用戶指定情境、非實測）。Contributor 原價 ×1。Grok 只匹配起首獨立詞（大小寫不敏感），每行僅一係數；表格 Score 降序並顯示各行係數、Grok 全量狀態與原價。$79 比較僅用於 GPT 訂閱組合。

用法（等待獨立資料工作完成並核對同一 benchmark_version、來源日期與 floor 理由後；此處不執行、不覆蓋既有輸出）：

```bash
python3 scripts/ladder_extra.py \
  --input runs/2026-09-26-general-grok16/candidates.csv \
  --output runs/2026-09-26-general-grok16/ladder-extra.md \
  --factor 18 --prefix GPT- --grok-factor 16 \
  --min-score 0 --min-score-reason '同版本新鮮全候選情境比較，暫不設能力下限'
```

驗證命令：`python3 -m unittest tests.test_ladder_extra -q`；`python3 -m unittest discover -s tests -q`。測試含兩家與 Contributor 的原價／調整價、單係數、prefix 邊界、CLI 非有限／非正數、Score 降序、excluded Grok 完整狀態與非 GPT 訂閱比較。來源日期依輸入 `checked_date` 顯示，產生報表本身不抓資料。
