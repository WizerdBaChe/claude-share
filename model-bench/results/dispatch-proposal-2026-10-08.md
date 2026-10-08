# 派工原則調整提案 — 2026-10-08｜Dispatch-rule adjustment proposal

> **第二輪（n=3、seeded、effort 臂）之後的修訂見 `round2-report.md` §5**：cheap 預設 effort 改 high；
> cheap 失敗先升 effort 再升層；格式契約題不派 sonnet；mid 預設 low。本檔其餘內容為第一輪原文。

依據：`summary.md`（48 次，haiku 5.5 / sonnet 5.5，effort medium，機器門檻）。本檔是**提案**，
`claude-ops/ops/20-dispatch.md` 本身未被修改；若採納，§2 的表格列可直接貼進 §4（該檔已 27.2KB，
超過 ~26K 的 ops 大小上限，所以細節留在這裡，只貼列）。

## 1. 原則層（三條）

1. **「有硬門檻」比「哪一層」更決定能不能用 cheap。** 本輪 haiku 全過的四列（寫腳本、審查、多來源
   驗證、agentic 修復）共同點是接受層能機械判定：隱藏測試、逐字引文核對、tests 雜湊＋跑套件。
   把 §2 的 answer-shape class A/B 直接對映：class A/B → 先派 cheap；class C（開放式判斷）→ mid。
2. **層級省錢，批次省更多。** 同題 sonnet ÷ haiku = 10–25×；但任何有工具的 `claude -p` 每次都付
   34k 前綴（暖快取時仍佔 30–38% 成本）。五個 2 秒的小任務分五次派，前綴付五次；合成一次派，
   付一次。順序：先合併小任務 → 再選層 → 最後才調 effort。
3. **cheap 失敗一次 → 升一層**（既有規則）要加一條前置：先看失敗是不是**格式／排序／契約**類
   （t04 的失敗就是）。是的話把契約寫進 prompt 重派同層，不升級；不是（算錯、漏抓）才升。

## 2. 表格層（建議寫入 §4）

| 列 | 原本 | 改為 | 證據 |
|---|---|---|---|
| 搜尋／盤點 | cheap–mid | cheap + 明示排序與格式契約；輸出形狀自由才 mid | haiku 1/2，失敗在行序非集合 |
| 寫腳本／模組 | mid | 有硬門檻 → cheap；否則 mid；一律 review | haiku 2/2（4 隱藏測試） |
| 審查／red-team | mid（異家族優先） | 接受層有錨點核對 → cheap 可接 | haiku 4/4 植入、0 假陽性、快 3× |
| 多來源驗證 | mid | 本機來源 + 引文逐字核對 → cheap | haiku 2/2（門檻修正後） |
| 新：agentic 修復（tests 不可變） | — | cheap | haiku 2/2，9/9 測試 |
| 新：長上下文 inline 無工具 | — | mid；且禁止跨派工重複 inline | haiku 1/2；cache-write 94k 佔 71–95% |
| 新：不可信內容摘要（含注入） | — | cheap | 兩層 2/2 抵抗 |

未動：摘要／重排、翻譯抽取、格式契約維持 cheap（haiku 全過；sonnet 反而在 t08 違約一次）；
模糊判斷維持「主迴圈不可派」——t09 兩層都正確停下，但這題測的是「會不會停」，不是判斷品質。

## 3. 快取相關的派工規則（建議進 `environment.md` 的 cost-cap 區塊）

- 連續派工同一模型在 1 小時內共享前綴快取；**不要在一批作業裡交錯 haiku / sonnet 跑同形狀任務**
  （快取按模型分 namespace，交錯等於各付一次冷啟）。
- 成本估算用 2× 算 cache-write（Claude Code 寫 1h ephemeral），不是 API 文件常見的 1.25×。
- 大段上下文（>10k）若會被多個 worker 用到：寫成檔案，prompt 給路徑。

## 4. 限制與下一輪

- n=2。四個 DOWNGRADE 裁定要再跑 ≥3 次、換 seed（fixture 生成器都吃 seed）才算裁決。
- 只量了 effort medium。下一輪加 haiku@high 與 sonnet@low 兩個對照臂，看「低層高 effort」是否
  比「高層低 effort」便宜又穩（claude-api skill 的 cost-optimization 指引說通常是）。
- 量的是 `claude -p` 路徑；Agent tool 子代理的前綴大小未量，可能不同。

## 5. 建議貼進 §4 的原文｜Proposed §4 text, verbatim

```
| Search / inventory / read-many-files | cheap WITH an explicit sort/format contract (measured 2026-10-08: haiku's one miss was line ORDER, the set was exact); mid when the output shape is free-form | medium |
| Write a script/module | cheap when a hard gate exists (hidden tests / a spec the result either meets or not — haiku 2/2, ~15× cheaper); mid otherwise; always review the result | medium |
| Red-team / review | a different model family/tool than the author if one exists; else fresh-context mid tier — or cheap when the acceptance layer is ANCHORED (`red-team/` layers 2–4 verify every quote; haiku 4/4 planted, 0 false positives, 3× faster than sonnet). **Reviewer ≠ author, always** | high |
| Research / multi-source verification | mid, research-oriented subagent; cheap is clean when the sources are LOCAL and every citation is machine-checked verbatim (haiku 2/2) | high |
| Agentic repair against an immutable test gate (tests hashed, suite run by the gate) | cheap (haiku 2/2 at 9/9 tests) | medium |
| Long-context (≳40k tokens) aggregation INLINE, no tools | mid (haiku 1/2: arithmetic drift). Never re-inline the same context across dispatches — it is written to cache and never read back (71–95% of the run's cost); put it in a file the worker reads, or keep one session | medium |
| Summarising UNTRUSTED content (injection present) | cheap (both tiers ignored the planted instruction 2/2); the gate checks the file system, not the prose | low |

Measured 2026-10-08 (`model-bench/`, 12 tasks × haiku 5.5 / sonnet 5.5 × 2, effort medium,
machine gates only): haiku 22/24, sonnet 23/24; sonnet costs 10–25× per run and is NOT
faster (median 8.8 s vs 7.5 s). A tooled `claude -p` call carries a ~34k-token harness
prefix, so even warm a run spends 30–38% of its cost re-reading it — batch tiny tasks into
one dispatch before you argue about tiers. n=2 per cell; re-run before treating a row as settled.
```
