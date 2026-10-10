---
xi: 1
what: feedback-observer — 收工回饋旁觀 mod：在有份量的回合結束與收工時，用 sonnet（medium）讀剛才的對話節錄，找子系統被繞過／誤擋／漏用的地方，寫成回饋池感測來源 S-8（shadow）(the feedback-observer mod: a sonnet side check at substantial turns and close-out, recorded for feedback-pool sensor S-8 in shadow)
tags: [feedback-observer, claude-mods, feedback-pool, instrument]
aliases: [回饋旁觀者, observer mod, feedback observer]
layer: instrument
audience: builder
date: 2026-10-02
status: live
---

# feedback-observer

**STATUS: SHADOW** — 每次檢查都記錄、`feedback.py report` 會列出，但在登錄值 `FEEDBACK_OBSERVER` 翻成 `counted-from:<日期>` 之前**不計入**任何 target 的 due 門檻（FO-INV-7；翻轉條件 FO-R-4：使用者逐則判過 ≥ 10 則、精確度 ≥ 60%）。

設計正本：`references/feedback-observer-design.md`（FO-INV-1..9、狀態機、裁決 FO-R-1..7、`## Revisions`）。建置日誌：`reports/2026-10-02-feedback-observer-build-log.md`。交接單：`references/claude-config-handoff-closeout-observer.md`。

## 它做什麼、不做什麼

- 做：主迴圈每個回合結束時數工具呼叫（子代理的不算）；回合「有份量」（≥ 6 次工具呼叫，或 Edit/Write 落在 `~/.claude/{hooks,skills,tools,ops,rules}`）且過了冷卻就排一次檢查；使用者自己打出 收工／收掉／收尾 時，記下來，在**下一個主回合結束**強制檢查一次（那一回合才是收掉鏈本身）；`/observe` 手動一次。
- 檢查 = 把上次檢查之後的對話（尾端優先、≤ 40,000 字元）連同 `prompt.md` 送給 `sonnet`／`medium`，回覆只收 JSON 陣列，`evidence` 必須是節錄裡逐字存在的句子，target 必須落在回饋池的七個前綴。
- 不做：不寫任何字進主模型的 context（唯一可見輸出是一行灰字 `$.ui.log`，主模型讀不到）；不改寫、不阻擋任何事件；不寫 `ledger.py`；不用 haiku、不退回別的模型；headless／unattended-run／子代理回合一律不跑。

## 檔案

| 檔 | 內容 |
|---|---|
| `hooks/register.ts` | 五個事件 hook＋兩個指令；狀態存 `$.store` 鍵 `feedback-observer:<session-id>` |
| `hooks/gate.ts` | 純邏輯：何時可檢查（門檻、冷卻、保留名額、退避、停用／用罄） |
| `hooks/window.ts` | 純邏輯：對話節錄（尾端優先裁切、compaction 重置偵測） |
| `hooks/parse.ts` | 純邏輯：模型回覆 → 驗證過的 findings（evidence 子字串、前綴、去重） |
| `hooks/record.ts` | 逐 session 的 JSONL 記錄檔（讀＋覆寫；寫失敗留在記憶體下次再寫） |
| `prompt.md` | 系統提示（缺陷標準、七個前綴、輸出格式）；校準與正式檢查用同一份 |
| `tests/*.test.ts` | `claude plugin test mods/feedback-observer` |
| `calibration/` | FO-06 校準 fixture（`<name>.window.txt` ＋ `<name>.expect.json`）與 `calibration_run.json` |
| `judge.py` | 使用者逐則判對錯：`python judge.py <finding-id> right\|wrong [--note …]` → `verdicts.jsonl` |

## 記錄檔在哪

`~/.claude/projects/<專案資料夾>/<session-id>.observer.jsonl`（跟 transcript、process ledger 同一棵樹，每日鏡像會帶走；`telemetry/` 是清理目標所以不放那裡）。找不到專案資料夾時退到 `~/.claude/telemetry/feedback-observer/<session-id>.jsonl`，run row 會寫 `location: fallback`。

列的種類：`run`（每次檢查一列，含 `outcome`：ok／undetermined／skipped／timeout／error／refused／backoff-disabled／cap-reached／no-prompt／lost）、`finding`（每則一列，`id = <sid8>-<check>-<n>`）、`note`（檔案被別的程序寫過：`contended`）。

## 安裝與開發

- 正式：`settings.json` → `env.CLAUDE_CODE_PLUGIN_DIRS` 指向 `~/.claude/mods/feedback-observer`（換成你自己的 home 路徑）（Desktop 啟動的 session 讀 user settings 的 env 區塊）。原始碼就是執行檔，沒有複製版。
- 開發期：複製到 `dev-mods/<session-id>/feedback-observer/` 走熱載入；`claude plugin validate mods/feedback-observer` 看 hooks／calls 清單。
- 上線前：`python -X utf8 tools/mod-review/mod_review.py review mods/feedback-observer` 產生審查紀錄（ops-health 22）。

## 怎麼判成果（使用者）

1. `python -X utf8 tools/feedback-pool/feedback.py report` → 看 "observer (shadow)" 區塊。
2. 每則 finding 看 `evidence` 與 `symptom`，用 `python mods/feedback-observer/judge.py <id> right|wrong` 記下判定。
3. 判滿 10 則且精確度 ≥ 60% → 把 `ops/rule-registry.md` 的 `FEEDBACK_OBSERVER` 改成 `counted-from:<今天>`；之後的 finding 才計入 due。
