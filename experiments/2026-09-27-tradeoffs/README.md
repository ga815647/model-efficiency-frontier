# 雙軸取捨：非正式歷史快照試驗

開啟 [report.html](report.html) 看自包含視覺報告；[report.md](report.md) 為完整文字表，[result.json](result.json) 為全精度機器可讀數據。這不是正式 ladder / 三 picks；沒有抓取新資料或改寫原 run。

## 重算（請用新目錄，不覆寫本快照）

```sh
python3 scripts/tradeoff_trial.py --input runs/2026-09-26-general-grok16/candidates.csv --output-dir /tmp/opencode/tradeoff-replay --factor 18 --grok-factor 16 --eps-score 2 --min-score 0 --min-score-reason '同版本全候選取捨示意；不是實用能力門檻'
```

原價／推定版本及 Contributor cache-write 假設詳見 `runs/2026-09-26-general-grok16/run-notes.md`。
