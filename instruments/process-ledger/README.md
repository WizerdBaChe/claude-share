# process-ledger — 過程資料在產生當下落盤，之後每個續接點都機械地讀到

**狀態**：live 2026-09-05｜原則與反駁 `references/long-run-probe-design.md` §0｜嚴重度：離線分支的兩個 hook 為 FAIL（只判可判定事實），其餘 WARN advisory｜回歸對照 `controls.py`＋`tools/compact-loss-audit/hook_controls.py`

## 不可約原則（使用者裁定 2026-09-05）

> 過程資料在**產生當下**以精華形式落盤，之後**每個續接點**（壓縮後、新 session、讀者）都能**機械地**讀到，不被任何清洗步驟（摘要、截斷、覆寫、快取清理）移除。

全域觸發；離線任務只是特化分支。

## 一般分支（任何 session）

| 何時 | 誰 | 做什麼 | 落點 |
|---|---|---|---|
| 每次決策（含使用者口頭裁定） | 模型，依 CLAUDE.md 決策憲章 | `ledger.py add --subject … --choice … --reason … --reversible yes\|no --origin user\|model [--ref D-xxx] [--quote "<使用者原話>"]` | `projects/<proj>/<session>.ledger.jsonl`（transcript 旁，每日鏡像會複製） |

> **使用者原話核對 (quote check) 2026-10-06。** `--origin user` 的列一律帶 `quote_check`：
> `--quote` 的文字（空白正規化後）若是本 session 對話記錄裡某則**使用者親手輸入**訊息的子字串 → `verified`（附 `quote_line`）；
> 找不到 → `not-found`；找不到對話記錄 → `no-transcript`；沒給 `--quote` → `absent`。
> 比對時排除 `<system-reminder>` 區段、工具輸出 (tool_result)、壓縮摘要與子代理訊息。
> 列**照寫不擋**（先落地再標記）；只有 `verified` 代表「使用者原話」，其餘只代表「被模型記錄為使用者裁示」。
> 對照組在 `controls.py` 的 `[user-origin quote check]`。
| 每則 prompt | runway hook | 寫 `cache/handoff/current-session.json`，讓 Bash 端的 `ledger.py` 找得到 session | cache |

> **已修補 (FIXED) 2026-09-07 — 原診斷是錯的：不是過期，是併發。**
> 舊條目寫的是「指標檔停在前一個 session 的 ts」，把它當成**過期 (staleness)**
> 問題。2026-09-07 實測推翻：misfile 發生時指標檔是**新鮮且正確的——只是屬於
> 別人**。`cache/handoff/current-session.json` 是**全域單一檔案**，每個 session
> 的每則 prompt 都覆寫它，所以三個併發 session 之間最後 prompt 的那個贏。當日
> 量測：本 session 的 8 列有 **5 列**落進另外**兩個** session 的帳本、跨**三個**
> 不同 project 目錄。指標檔沒有「我過期了」欄位是真的，但那不是根因——**它連
> 「我是誰的」都無法表達**，而這才是問題。
>
> 兩種診斷的修法不同：過期需要時效欄位；併發需要**行程本地的身分來源**。
> 修法採後者——`current_session()` 現在優先讀本行程的 `CLAUDE_CODE_SESSION_ID`
> （Bash 與 PowerShell 子行程都繼承得到，已驗證），指標檔降為 fallback。
> 兩個指標檔的判讀邏輯原封不動保留，只是排在 env 之後。
> env 與指標檔不一致時會印一行 stderr 提示，讓併發情形保持可觀測。
>
> 驗收（三側對照，2026-09-07）：env 存在 → 本 session（正對照，當時指標檔確實
> 指向別人，所以對照真的會觸發）／env 移除 → 退回舊行為（負對照，證明測得出差別）
> ／env 為非 UUID 垃圾值 → 安全退回指標檔。端到端：新列落回正確檔案。
> 同日把 5 列誤寫資料搬回原主（來源檔屬活躍 session，先備份並以 size+mtime
> 檢查防併發覆寫）。相關：`ops/lessons.md` L-053（原症狀）、L-055（為何錯誤
> 診斷能撐 1 天：限制／缺陷記錄缺少 probe set）。
>
> **review-when**：shell 呼叫裡 `CLAUDE_CODE_SESSION_ID` 變成空的（harness 改名
> 或移除）——fallback 仍可運作，但併發缺陷會一併回來，需重新探測新變數名。
| 脈絡跨 150k（一次） | runway hook（D3 修訂） | 植 canary 對：keep token（新檔第一行要帶）＋假細節（摘要不得留）；提醒 ledger | `projects/<proj>/<session>.canary.json` |
| 脈絡跨 300k、每 40k | runway hook | snapshot 通知（整份重寫；決策項引用 ledger） | `cache/handoff/<session>.md` |
| 壓縮後第一回合 | `compact_pointer.py` | 卡片帶 snapshot 全文＋ledger 最新 40 列 | 注入 |
| 事後 | `run_audit.py <session>` | F1 重決／F4 重工／F6 報告失真／canary（摘要有沒有帶 keep、有沒有漏 drop）；F3／F7 標「attended 不適用」 | stdout |

## 離線分支（`[unattended-run]`）

在一般分支之上加：manifest（scope 預設專案根、slug、交付物／驗收由模型首回合推導並標 `filled_by: model`）、scope deny（PreToolUse Write/Edit）、stop block（問句收尾或無 run report，上限 2）、`report.py` 骨架、F3／F7 生效。操作流程見下。

**run 的結束（2026-09-06 補）**：你回來後送出的第一則**不帶 tag 的**訊息就結束 run——manifest 標 `ended`（檔案保留給 `run_audit.py`）、兩個守衛解除、`current-run.json` 移除、模型收到一行 `[unattended-run] run … ENDED` 的脈絡。harness 注入的純標籤 prompt（`<task-notification>`、`<system-reminder>`、斜線指令）不算你回來。再貼一次 `[unattended-run]` 就重新開一場。session scratchpad（`%LOCALAPPDATA%\Temp\claude\…`）永遠可寫；`current-run.json` 只由 kickoff 寫，deny／block 只更新 manifest 計數。此前沒有任何結束轉移：第一場在你回來 2 小時 42 分後仍擋下你剛要求的寫入（來源環境的一支容器寫入守衛 hook），模型把那次 deny 讀成「機制正常」而繞路——回歸對照在 `controls.py` 的 `[run end]` 段。

## 派工與寫入原則（離線期間，2026-09-06 量測）

- 子代理 (subagent) 的 Write/Edit 走同一個 scope 守衛、記在母 session 名下——量測：haiku 子代理寫 `%LOCALAPPDATA%\Temp\ur-probe\probe.md` 被 deny，telemetry 列的 session 是母 session；子代理的第一則 prompt **不會**結束 run（manifest `ended` 仍為 null）。
- 子代理的 shell 端寫入與主迴圈一樣不在守衛內 → 事後 F3。
- 派工模型上限 haiku/sonnet（`hooks/model_cap_guard.py`）不因離線放寬；一個只做兩個工具呼叫的探針子代理就吃掉 52k tokens 的自己脈絡——紀錄（ledger／snapshot／report）留在主迴圈寫，子代理不寫帳；主迴圈把「派了誰、為什麼」記一列就夠。
- 寫入：交付物走 scope；scratchpad 與 `~/.claude/{cache/handoff,reports,telemetry}` 永遠可寫；其他一律具名阻塞、不繞路（deny 的出現本身就證明使用者還沒回來）。

## 紀錄成本與度量（F8，2026-09-06）

使用者問：幾乎每一步都寫紀錄，重模型的 write 消耗會不會過大？量了 9 場有寫帳的真實 session（依 `requestId` 分請求；成本用相對於未快取輸入的價格比：opus 家族 cache read 0.1×、輸出 5×；fable 家族 cache read 0.025×；絕對價見 `reports/2026-09-06-auto-compact-cost-audit.md`）：

| session | 請求數 | 紀錄呼叫 | 單獨請求 | 併發請求 | 額外負擔（opus 比） | 其中：單獨請求的脈絡重讀 | 其中：紀錄輸出本身 |
|---|---|---|---|---|---|---|---|
| 場次 A（維護回合） | 614 | 30 | 29 | 1 | 5.1% | 4.3% | 0.8% |
| 場次 B（AWD 離線場） | 589 | 23 | 20 | 3 | 4.1% | 3.4% | 0.7% |
| 場次 C（13 次 snapshot 重寫） | 130 | 44 | 6 | 27 | 7.9% | 3.1% | 4.8% |
| 場次 D（本場，稽核型） | 77 | 36 | 9 | 15 | 13.8% | 5.7% | 8.1% |
| 其餘 5 場 | 22–209 | 2–8 | 0–8 | 0–5 | 1.2–4.1% | 0–3.6% | 0.3–1.8% |

fable 比下同一批是 1.6–5.1%／8.8%／15.2%。結論：一般 session 的紀錄負擔 1–5%，寫帳密集的 5–8%，稽核型 14%。**寫帳為主的場（場次 A、B）八成是「單獨請求」的脈絡重讀**——一列 150 token 的 ledger 單獨佔一個請求，整份 160–300k 的脈絡就為它再讀一次（cache read 價）；把同一個呼叫放進下一個真實工具呼叫的同一則訊息裡，這部分歸零。snapshot／report 重的場則以紀錄輸出本身為主，那是要留紀錄就得付的；最大單項是 snapshot 整份重寫（每次 3–5k 輸出 token；場次 C 重寫 13 次）——300k 之後每 40k 一次的節奏屬於 runway 機制，本輪不動，數字放這裡給裁定用。

- 度量：`run_audit.py <session>` 的 **F8**——單獨／併發紀錄請求數、各類紀錄呼叫數、`overhead_pct`（opus／fable 比）拆成脈絡重讀與紀錄輸出、單獨請求平均重讀脈絡。WARN 級（讀者是模型）；升級觸發：連續兩場 `solo_ctx_pct` 高於本表基線（0–5.7%）。
- 原則（kickoff 義務第 2 條也寫了）：紀錄呼叫**不單獨成一則訊息**；多列用一個 Bash 呼叫串接。重模型尤其如此——紀錄的輸出 token 數不隨模型變，重讀整份脈絡的價才隨模型變。
- 紀錄本身不縮：ledger 一列 ~150 token，是這套機制最便宜的部分；縮它省不到 1%。

## 操作流程（第一場：SSLD）

**離線前**：在 SSLD session 照常寫任務，訊息裡任一處放 `[unattended-run]`；要加限制才多一行（`rulings: …`、`budget: …`）。送出後確認第一則回覆前有 `[unattended-run] Manifest written:`，沒有就別走。

**回來後**：你的第一則訊息就結束 run（不用任何指令；那一回合的回覆會帶 `[unattended-run] run … ENDED`，沒看到＝kickoff hook 沒跑到，再送一則純文字訊息）。接著看最後一則是否「report 路徑＋具名阻塞＋未做清單」；跑

```powershell
python tools/process-ledger/run_audit.py
python tools/compact-loss-audit/notice_compliance.py
```

（`run_audit.py` 可再接一個舊 session id，對歷史場次重跑；無 manifest、無 canary 的場次只出 F4／F7。）打開 `reports/<date>-run-<slug>.md`：第一行 `filled_by` 若為 `model`，先核對交付物清單等不等於你的意圖；再讀 §2 驗收、§3 未做、§5 canary、§6 收尾。

| 現象 | 意義 | 處置 |
|---|---|---|
| 回來後寫入仍被 scope 擋 | run 沒結束（hook 沒跑到，或你的訊息只有標籤） | 再送一則純文字訊息；仍擋就查 `telemetry/unattended-run.jsonl` 有無該 session 的 `end` 列 |
| canary drop 出現在摘要 | 摘要器留噪音 | 摘要器問題；window 拉 500k 再試一場 |
| canary keep 不在摘要 | 摘要器丟了常設約束 | 同上，且 Compact Instructions 要加「常設約束」一項 |
| F1 hits > 0 | 壓縮後改了決定沒說 | 看 ledger 兩列的理由，判是否合理重決 |
| F3 hits > 0（離線） | scope 窄了或真漂移 | 看 deny 理由 |
| F4 hits > 0 | 壓縮後整檔重讀 | recall ladder 沒守；累 3 次再升 hook |
| F6 absent > 0 | 報告漏了 ledger 項 | 對照 §3 未做是否列出 |
| F7 stop_blocks > 0（離線） | stop guard 擋過 | 規則生效；看 block 前那則 |
| ledger 0 列且脈絡 >150k | 模型沒照憲章寫 | C 層合規失敗樣本；累 3 場升 hook 或改注入 |

## 不涵蓋（具名轉交）

shell 端寫檔不被 scope guard 擋、F3 也不解析；prose scope 只存原文；問句藏中段不算 F7；登記表層級重決由讀者比 diff；ledger 寫入本身靠模型照憲章（C 層），以「ledger 列數／session」與 `notice_compliance.py` 量。

review-when：Claude Code 改 Stop／PreToolUse hook 契約；鏡像腳本不再複製 `projects/`（ledger 落點的耐久性前提）；任一 control FAIL。
