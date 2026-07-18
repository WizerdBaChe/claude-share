# literature-search-extract — 未結項清單

> 本檔只放**尚未完成**的事項。歷史完成紀錄（P1–P7 全部 21 項）已封存至
> `~/.claude/archive/2026-07-12-lse-update-plans/TODO.md`，勿在此重複。
> 事項完成後：從本檔移除，並在封存的 TODO 或 commit message 留紀錄即可。

## A. 待使用者決定

### A1. 分享版打包（原 TODO item 19）
若日後要把本 skill 分享到本機以外：走 skill-share-packaging Mode A——
剔除個人檔案（PDF-GUIDE / FUTURE-WORK / sample-run / evals 個人備註）、
generalize prism 字樣為 provider-neutral local-corpus slot、移除 frontmatter 的
trigger-dict 引用，只出貨 SKILL.md + references/ + evals.json。
**現況**：可攜性核心已由 `references/portability.md` 出貨（2026-07-12，P7），
剩的只是「打包剝離」這一步。不分享就不用做。

### A2. SKILL.md 精簡（可選）
現 261 行，超過 250 行軟上限（session 啟動 hook 會持續提示）。候選手段：
output format catalog 表與 output-templates.md 部分重疊，可移 references/。
不影響功能，純維運。

## B. MANUAL-VERIFY（等待真實使用情境驗收）

| # | 驗收項 | 驗收時機與判準 |
|---|---|---|
| B1 | 本地 PDF 庫支援（P4 item 14） | 下次以本地資料夾調用時：先盤點建索引、`[full]` 標籤正確、收藏偏誤記入 search_trail |
| B2 | portability 能力自評（P7 item 21） | 下次 codex（或任何非 Claude 環境）調用本 skill 時：有先讀 portability.md 做能力盤點、交付物聲明 profile 與降級 |
| B3 | eval 6 重測（source-provided 全文萃取） | 原測試因 Science 付費牆 1 條 assertion 留 null；改用 open-access 指定來源或本地 PDF 重跑補值 |

## C. 長期選項（ops 層，非本 skill 職權）

- interop.py 擴 skills-compile profile，取代手動複製到 `~/.agents`/`~/.codex`
  （裁決紀錄：`~/.claude/ops/lessons.md` L-003；決定權在使用者）。
