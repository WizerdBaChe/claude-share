# 真火驗收清單 (real-fire acceptance)

裝完之後,用一次**真的** `/compact` 驗收整條鏈。每項都是盲測可執行:具體動作 +
預期觀察;4–7 是壓力項。檢查手段全為唯讀,不動任何狀態。

| # | 動作 | 預期觀察 |
|---|---|---|
| 1 | 任一 session 跑 `/compact`,完成後問模型:「你有 [compact-recovery] 卡嗎」 | 引出卡片:trigger、時刻、digest 路徑、`lines 1-N` 區段、召回政策 |
| 2 | 查 `<CLAUDE_HOME>/cache/compact-recovery/<session-id>.json` | 存在;`ts` 為剛剛;`line_count` > 0;數值與卡片一致 |
| 3 | 查 `<CLAUDE_HOME>/memory-archive/digests/<專案槽名>/<session-id>.md` 的 mtime | ≈ 壓縮時刻(未裝 preserve 則卡上應標 not generated) |
| 4 | 請模型找回一個摘要沒有的具體細節(愈具名愈好:一句裁決、一個數字) | 它先 Grep digest(≤3 hits、小 -C),不整檔讀;digest 被截斷才升級到 jsonl 區段 |
| 5 | 同 session 快速連壓兩次 | 書籤被覆寫;卡片重發;`line_count` 變大 |
| 6 | 直接要求「整份舊 transcript 讀出來」 | guard deny 訊息現身(含合規路徑指引);模型改走 grep + 視窗讀 |
| 7 | 放著讓 auto-compact 自然觸發一次 | 卡上 `trigger=auto`(來源環境唯一還空著的證據格) |

## 來源環境已驗過的(2026-08-16)

- 19/19 真資料驗收:三檔 compile、書籤對真實 4.4MB transcript(行數/大小/靜默)、
  完整卡與降級卡、guard 拒/放/域外/小檔/非 Read 六案矩陣、活 session digest
  刷新(mtime_age 0s)。
- **全鏈真火**(manual `/compact`):書籤 `manual, 160 lines/0.87MB` → 壓縮後
  卡片注入且區段數值與書籤一致 → digest 在卡片時點是新的 → 召回梯實走
  (digest 一次命中;被截斷的事實依政策升級到 jsonl 區段 Grep 命中)→
  壓縮後 guard 再次 deny(**guard 熬過 compaction**)。
- 額外觀察:hooks 對進行中 session 立即生效,免重開;壓縮換手期間可能另有一次
  preserve 執行(SessionEnd 路徑),與 PreCompact 鏈式那次互為雙保險。

## 判讀提醒

第 4 項在考的是**紀律**不是能力:一個「找回了、但用整檔重讀找回」的結果是
不及格——那正是這個模式存在要防止的行為。deny 訊息出現不是故障,是規則在開火。
