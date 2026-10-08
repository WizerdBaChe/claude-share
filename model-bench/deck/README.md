# deck/ — 通用講解版簡報的建置來源｜Build source of the teaching deck

產出：`../Haiku派工實測_通用講解.pptx`（14 頁，16:9，可編輯）。對象是「想把工作分給便宜模型的人」，
重點是做法與觀念，不是測試報告；數字只取 `../results/` 已有的紀錄。

```
python build_deck.py      # 需要 python-pptx 與 Pillow；建置後跑文字閘門，exit 0 才算過
```

| 檔案 | 作用 |
|---|---|
| `build_deck.py` | 內容與版面（每頁一段），以及閘門：承重數值逐字存在（含備註）、禁用建置者詞彙（檔名、題號、本機路徑）、字級下限；每次建置帶正反對照 |
| `deck_layout.py`、`deck_builder.py` | 版面層與底層 helper，取自一份共用的 python-pptx 建置骨架（字級分層、中文字型與語言標記、防孤行、扁平無陰影） |

改內容：只改 `build_deck.py`，重跑一次；新增數字時一併加進 `VALUES`。
宣告：class = presentation（展示用）、density = 繁複（分享出去、沒有講者在旁，所以字要夠讀）。
