---
xi: 1
what: model-cap — 子代理模型成本上限的 in-process 版本：Claude Code mod 在 `agent.spawn` 事件上同步擋下 opus／fable 派工，並記錄每次派工實際解析到的模型 (the model-cap mod: the subagent cost cap enforced on agent.spawn, synchronously, with the resolved model of every spawn logged)
tags: [model-cap, claude-mods, dispatch, cost, guard]
aliases: [model-cap mod, agent.spawn 上限, 子代理模型上限 mod]
layer: instrument
audience: builder
date: 2026-10-09
status: live
---

# model-cap（mod）

**為什麼有這個**：2026-10-02 SHARE 回合八個並行派工都沒帶 `model`，Python hook `hooks/model_cap_guard.py` 八個都寫了 deny，但其中兩個回應超過當時 5 秒的 hook timeout，而 **command hook 逾時＝放行**，兩個子代理就跑在 claude-fable-5-1 上。timeout 已改 30 秒（L-137），但任何 timeout 都還是放行；真正關上這個洞的是引擎會**等待**的 in-process hook。評估：`reports/2026-10-02-model-cap-escape-evaluation.md` §4；使用者裁決 2026-10-02：省略 model 時 **deny**，不改寫。2026-10-09 改判：省略時不再在 spawn 擋（那時引擎還沒解析模型），改在子代理第一個 step 判引擎解析後的模型；超過上限照樣擋、照樣不改寫。

## 規則（`hooks/policy.ts`；Python hook 是同一套規則的鏡像）

兩個判定點（使用者裁決 2026-10-09：判**引擎解析後的模型**，不再自己讀 agent 檔重算）：

**1. `agent.spawn`**：只判「光看這次呼叫就能確定」的情況。這個事件發生在引擎解析模型**之前**（型別檔 `AgentSpawnInput`：「before its model is resolved」）。

| 情況 | 判定 |
|---|---|
| prompt 含 `[user-approved-top-tier]` | pass（使用者逐案核准） |
| fork（`fork` 或 subagentType `fork`） | 看 **parentModel**：opus／fable → deny（fork 永遠繼承，`model` 被引擎忽略）；haiku／sonnet → pass；其他 → notice |
| `model` 有給 | opus／fable → deny；haiku／sonnet → pass；其他 → notice |
| `model` 省略 | `deferred`：放行，交給第 2 點 |

**2. `turn.step`（子代理迴圈 `e.agentId`，請求送出前）**：`e.model` 是引擎實際解析出的模型。定義不管來自哪裡（專案 `.claude/agents`、使用者 `agents/`、plugin agent、`--agents` JSON、managed），沒有釘選時就用父模型，全都已經算進去。

| 情況 | 判定 |
|---|---|
| haiku／sonnet | pass |
| 不在 `$.agent.list()`、也不是這個 mod 看過的 spawn | pass（引擎內部迴圈：compaction、memory。這類不能擋，擋了會毀掉摘要） |
| opus／fable，已核准（自己的第一則 prompt 含 marker；fork 只認 spawn 時看過的核准 prompt） | pass |
| opus／fable，未核准 | **不送請求**，直接回拒絕文字當子代理的答案（0 token），並寫一列 `refuse` |
| 其他 | notice（每個 agent＋模型只提示一次） |

判定以「agentId＋模型」快取，所以 SendMessage resume 落到主模型、或 fallback 換模型時，都會重新判。live 探測（2026-10-09，CC 2.1.294）：resume **沒有**落到主模型，定義釘選的 haiku、呼叫參數釘選的 sonnet 恢復後都還是原模型。所以這條防線目前備而未用，「它會擋」還沒有實例證明。

型別檢查：`tsc -p mods/model-cap-mod`（tsc 7.0.2，2026-10-09 起才有）。

**兩個 hook 都 fail closed**：`agent.spawn` 的 `.catch` 直接 deny；`turn.step` 的 `.catch` 在「子代理、解析成 opus／fable」時回拒絕文字（引擎內部迴圈除外）。第一個 step 可能比 spawn 的 `next()` 先到（probe：差 26 ms），所以判定前最多等 2 秒，讓進行中的 spawn 先落定。

**拒絕／擋下文字**一律寫明「如果模型本身就是實驗變因，**不要換模型**，停下來回報使用者」。step 層的拒絕文字只建議「把模型釘清楚」，不建議改派 sonnet（r22 教訓：擋下訊息把呼叫端導向 sonnet，等於悄悄換掉實驗變因）。

deny 文字照 `rules/hook-deny-message.md`：第一句自報身分、重試方式、誤擋回報路徑（`report_fp.py --hook model-cap`）、收據（`telemetry/model-cap-mod.jsonl` 的 nonce）。`tools/hook-deny-lint` 只 lint `hooks/*.py`，這份 TS 的文字是 `tests/policy.test.ts` 用同樣的四禁二求做字串檢查（替代，不等價）。

## 跟 Python guard 的分工（`hooks/model_cap_guard.py`）

mod 在 `session.start` 把 session id 寫進 `telemetry/model-cap-mod-alive.json`（心跳）。Python guard 遇到「`model` 省略＋本地查不到定義」時，**只有在 payload 的 `session_id` 有心跳**才放行，交給 mod 的 step 層判；沒有心跳、檔案壞掉、payload 沒有 session_id，都照舊 deny。所以沒有 mod 的 session 不會比以前更鬆。本地查到的定義釘 opus／fable、或明給 opus／fable，照樣 deny。測試案例：`tools/model-cap-test` M-H1…M-H4。

## 隔離的 `claude -p`（使用者裁決 2026-10-09：不可排除）

mod 是透過 `settings.json` 的 `env.CLAUDE_CODE_PLUGIN_DIRS` 載入的，子行程會繼承這個環境變數，所以 `--setting-sources project,local` 擋不住 mod。但那個旗標**已經把 Python guard 排除掉了**，mod 是隔離 run 裡唯一的上限執法者，排除它等於沒有上限。結論：不提供排除開關。lab 端把 mod 當成**已宣告的環境常數**，在 run 紀錄裡寫下 `~/.claude` 的 commit sha（lab 端修改另開卡）。

## 它寫什麼

`telemetry/model-cap-mod.jsonl`：`deny`（spawn 時擋下）、`refuse`（step 時拒絕：nonce、resolved model、agentId）、`notice`、`step`（核准或引擎內部迴圈放行）、`spawn`（每次派工：requested／**resolved**／agentId／parentModel／fork）。檔案保留最後 5000 列。另有 `telemetry/model-cap-mod-alive.json`（心跳，保留最新 200 個 session）。

## 檔案

| 檔 | 內容 |
|---|---|
| `hooks/policy.ts` | 純函式：`tierOf`、`decide`（spawn）、`decideStep`（step）、`approvedIn`、`withHeartbeat`、各種文字 |
| `hooks/register.ts` | `session.start`（心跳）、`agent.spawn`、`turn.step` 三個 hook；寫 telemetry |
| `tests/policy.test.ts` | `claude plugin test mods/model-cap-mod`：spawn／step 的 must-deny／must-pass／must-notice、核准判定、文字形狀、心跳 |

## 安裝、驗證、漂移點

- 安裝：`settings.json` → `env.CLAUDE_CODE_PLUGIN_DIRS`（以 `;` 與 feedback-observer 並列）。
- 驗證：`claude plugin validate mods/model-cap-mod`、`claude plugin test mods/model-cap-mod`；上線紀錄 `python -X utf8 tools/mod-review/mod_review.py review mods/model-cap-mod`。
- **漂移點**：`BLOCKED`／`WITHIN_CAP` 在 `hooks/model_cap_guard.py` 和 `hooks/policy.ts` 各一份。加一個 family 要兩邊都加；`tools/model-cap-test` 的 coverage case 只讀 Python 那份——下一次改 family 時，把 TS 這份也納入該 case（review-when）。
- **漂移點 2**：Python guard 仍然自己讀 agent 檔（專案根目錄 → `~/.claude/agents`），但現在只用來「提早 deny 確定的 opus／fable 釘選」。查不到定義時，有心跳就交給 mod，所以查找漏掉的來源不會再變成誤擋。沒有心跳的 session（沒載入 mod）才會在查不到時 deny，跟以前一樣。
- Python hook 不拆：mod 補的是「逾時放行」、「fork 繼承」、「解析後模型」三件 Python 看不到的事；Python 補的是 Workflow script 掃描（mod 沒有），以及沒載入 mod 的 session 的底線。
- live 驗證（2026-10-09，fable 父迴圈）：專案釘 haiku 的 worker 在 `cd build` 後放行，跑在 haiku 上；專案釘 opus 的 worker 在 step 0 被拒絕，opus 用量 $0；8 個並行、省略 model、沒有定義的派工，8/8 在 step 0 被拒絕，每個子代理 0 token。紀錄在 `reports/2026-10-09-model-cap-resolved-model-design.md`。
