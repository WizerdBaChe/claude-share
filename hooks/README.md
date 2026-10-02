# hooks/ — 機械強制層｜Mechanical enforcement layer

> **中文摘要｜Chinese summary**：目前的 mounting template 掛載 33 支 hook；另有
> `deny_receipt.py` 與 `handoff_snapshot.py` 這類不掛載的共用函式庫，以及兩支已
> 退役但仍保留檔案的 probe（`fieldwork_threshold_notice.py`、
> `delivery_gate_shadow.py`）。所有 shipped guards 都 fail-open；是否真的生效取決於
> `settings.json` 的掛載，不是檔案存在本身。其中多支會呼叫 method tool（出貨在
> `../instruments/<name>/`，要複製到 `<CLAUDE_HOME>/tools/<name>/` 才找得到）。
>
> **English summary**: The current mounting template wires 33 hooks. Shared libraries
> such as `deny_receipt.py` and `handoff_snapshot.py` are shipped but not mounted, and
> `fieldwork_threshold_notice.py` and `delivery_gate_shadow.py` are retained but retired.
> All shipped guards fail open; presence on disk is not proof of activation—registration
> in `settings.json` is. Many of the hooks call a method tool that ships under
> `../instruments/<name>/` and must be copied to `<CLAUDE_HOME>/tools/<name>/`.

## 快速導覽｜Quick guide

| 項目 | 中文 | English |
|---|---|---|
| 先看 | 先讀本 README 的採用前注意事項，再看 `settings.example.json` | Read the adoption notes, then inspect `settings.example.json` |
| 目前狀態 | 33 支 mounted hooks；共用函式庫與 retired 檔案另標明，不列為掛載 hook | 33 mounted hooks; shared libraries and retired files are labelled separately |
| 驗收 | 逐支手動跑 fail-open self-test，並確認平台真的載入設定 | Run each available self-test and confirm the host registered the settings |
| 不包含 | 不包含 Claude hook runner、外部 credentials、來源端未出貨 tools tree | No hook runner, external credentials, or excluded source tools tree is included |

> **十六支 hook（2026-08-29 起）。** 2026-08-14 首次收錄十二支，2026-08-29 補齊
> 四支殼層／git 強制層（`shell_transport_guard`、`ps_errorpref_guard`、
> `ps_pipeline_close_guard`、`branch_commit_guard`）——那四支都被本 repo 已出貨的規則檔
> 引用當作機制，卻一直沒附；這正是下面那段警語講的同一類漏宣告，只是換了一批檔案。
> 四支全部先過可攜性掃描才收。`settings.example.json` 掛載其中**每一支**，這是它的
> 不變式；`tests/` 底下的回歸矩陣不掛載（測試不是 hook）。

> 這批檔案是 2026-08-14 才補進本 repo 的。在那之前，`claude-ops/` 與
> `environment-guide/` 有 20 多處引用它們當作「機械強制」的依據，但檔案一個都沒附，
> 而 manifest 把原因寫成「machine-bound（綁機器）」——**那個判斷是錯的**。
> 逐檔查證後：所有 hook 全部用 `Path.home()`／`os.path.expanduser`／
> `CLAUDE_CONFIG_DIR`／`os.environ["TEMP"]` 解析路徑，**零個寫死的帳號或絕對路徑**。
> 它們不是不能分享，是從來沒被撈進來。收錄程序見
> [`../tools/COLLECTION-RULES.md`](../tools/COLLECTION-RULES.md)。

> **2026-09-07 refresh：十八支 hook。** +2：`compact_loss_record.py`
> （PostCompact，compact-recovery 第四支，記錄每次壓縮的漏失稽核用資料）與
> `appdata_view_guard.py`（PreToolUse `Bash\|PowerShell`，assistant shell／
> user shell 讀到不同答案的標註型 guard；收錄時把四行校準測資裡的帳號名換成
> `<user>` 佔位符，行為不變）。`handoff_snapshot.py` 這輪也一起到，但它**不是
> hook**——是 `compact_bookmark.py`／`compact_pointer.py`／`context_runway_shadow.py`
> 三支共用的函式庫，沒有自己的事件掛載，跟 `tests/` 不算 hook 是同一類。另外三個
> 候選讀完全文後排除，理由跟下面「為什麼是 hook」段落點名的漏宣告同一類，只是換了
> 目標：`intake_guard.py`／`intake_match_shadow.py` 是 `tools/closeout-intake/`
> 的一半（它們管的 `ops/lessons/` 存放區本 repo 也不出貨），`unattended_run.py`
> 是 `tools/process-ledger/` 的一半（它的 Stop guard 判斷條件本身需要那支工具才能
> 產生的報告檔）——出貨與否見 `tools/share-manifest.toml` 的 `[[not_shipped]]`
> 條目，`settings.example.json` 的 `_README` 也各留一行。

> **2026-09-12 refresh（source 27196ab -> 7c9867b）：二十一支掛載 hook。**
> +4：`deny_receipt.py`（不是 hook，是 deny/notice 訊息的 receipt 共用函式庫，
> 供下面幾支 import）、`dispatch_commit_notice.py`（PreToolUse
> `Bash\|PowerShell`／`Agent\|Workflow` + SubagentStop 三處掛載，subagent
> 派工紀錄與「commit 落地卻沒對應紀錄呼叫」的標註）、`published_record_guard.py`
> （PreToolUse `Write\|Edit`，任何帶 `tools/COLLECTION-RULES.md` 的樹——本 repo
> 自己也算——內容匹配私有值形狀就擋；這支同時是**這次收錄工作本身的即時管制**，
> 過程中真的擋過一次已加placeholder的測資與一次描述 scrub 的說明文字，兩次都靠
> 換管道或改用類別描述解決，不是放寬規則）、`worktree_scope_guard.py`
> （SessionStart 公告 + PreToolUse `Write\|Edit\|NotebookEdit\|Bash\|PowerShell`，
> git worktree 內的 session 要 mutate canonical checkout 一律擋，除非帶 opt-in
> 或改用 canonical cwd——這支正是管著**這次收錄工作自己這個 session** 的機制）。
> `fieldwork_threshold_notice.py` 這輪在來源端**退役**：source commit `bd834ea`
> （user ruling R-3，rules-debt audit）把它的 `Read\|Grep\|Glob` 掛載整段拿掉——
> 293 筆 shadow row 裡 >=52% 可量化為假陽性，30 天寬限期也早過了。檔案與
> telemetry 形狀留著（下面照舊列出，標 RETIRED），但 `settings.example.json`
> 不再掛它，跟來源端的掛載狀態一致。此輪也新收三支 `tests/` 回歸矩陣（測本輪新收
> 或已在本 repo 的 hook），另兩支新測試檔（測 `extdispatch_entrypoint_guard.py`
> 與 `project_registry_gist.py`）因為測的 hook 本身不出貨，同樣不出貨——見
> manifest 的 `[[not_shipped]]`。同一輪另一個並行工作項目收進 literature-access
> 機制：`literature_host_guard.py`（掛載見範本）、它的政策表
> `literature-host-policy.json` 與回歸測試 `tests/test_literature_host_guard.py`。
> 合計 18 + 3 − 1 + 1，掛載數是**二十一支**。

> **2026-10-02 refresh（source 7c9867b -> 183c129）：三十三支掛載 hook。**
> 使用者 2026-10-02 裁示：`tools/` 開放給 method tool 與 hook 測試套件，所以「唯一
> 私有依賴就是這類 tool」的 hook 連同 tool 一起出貨（tool 落在 `../instruments/<同名>/`）。
> 據此翻案 2026-09-07 與 2026-08-29 排除的四支：`intake_guard.py`、
> `intake_match_shadow.py`（`tools/closeout-intake/`）、`unattended_run.py`
> （`tools/process-ledger/`、`tools/hook-proof-of-life/`）、`secret_file_guard.py`
> （判準本身是通用的憑證檔名樣式；測試套件 `tools/secret-guard-test/`），以及
> `project_registry_gist.py` 與它的測試。另 +8 支新收：`boundary_contract_notice.py`、
> `feedback_notice.py`、`tree_noise_gist.py`、`golive_check.py`、`system_hmi_summary.py`、
> `view_launcher_gist.py`、`verbatim_dispatch_notice.py`、`session_search_query_notice.py`。
> 其中 `system_hmi_summary.py`、`view_launcher_gist.py`、`project_registry_gist.py`、
> `golive_check.py` 讀的登錄檔（`registry/subsystems.json`、`views.json`、
> `references/PROJECTS.md`）本 repo 只出樣板：樣板沒填之前它們安靜或只印一行說明，
> 不擋任何東西。已出貨 12 支的 refresh 在各自 manifest 條目裡逐項記錄；本輪最大的
> 行為變動是 `shell_transport_guard.py` 新增第 (4) 條（未加引號的 Windows 磁碟路徑，
> 可解析時 deny、不可解析時 notice）、`worktree_scope_guard.py` 的 reparse point
> 計數（L-120），以及 `delivery_gate_shadow.py` 在來源端**退役**（SubagentStop 掛載
> 移除，檔案保留、範本不再掛）。**刻意不收**：`registry_row_guard.py`——它直接
> import `user_profile_gist.py`（個人檔案，不出貨），沒有它 `--selftest` 會 crash、
> 守衛永遠 no-op，出貨一支結構上無法運作的 guard 比不出貨更糟；另外
> `codex_dispatch_guard.py`、`extdispatch_*`、`session_board_register.py`、
> `moc_closeout_notice.py`、`deliverable_birth_notice.py`、`xi_card_guard.py`、
> `past_work_recall_inject.py`、`subagent_retrieval_brief.py`、`user_profile_gist.py`
> 也都不出貨（理由與替代路徑見 `[[not_shipped]]`）。掛載數 21 − 1 + 13 = **33**。

## 為什麼是 hook，而不是規則文字｜Why a hook instead of prose

規則層寫「請記得 X」，模型在自信的當下會讀過去。這幾支的共同判準（`ops/lessons.md`
L-011）是：**觸發形狀如果是一個具名工具呼叫、且參數可檢查，就該用 hook 擋，不該用散文提醒。**
`ui_verify_guard` 的兩個事故在純文字規則下復發了約一個月，換成 hook 之後才停。

全部 **fail-open**：解析錯誤一律 exit 0。守衛的 bug 不能變成工作的阻礙。

## 內容｜Inventory

| 檔案 | 事件 | 做什麼 |
|---|---|---|
| `dangerous_command_guard.py` | PreToolUse `Bash\|PowerShell` | 不可逆指令的確定性拒絕清單：遞迴強制刪除、`git push --force`／`reset --hard`／`clean -f`、registry 寫入、關機／格式化。放寬 allowlist 後的補償控制 |
| `dispatch_commit_notice.py` | PreToolUse `Bash\|PowerShell`／`Agent\|Workflow` + SubagentStop | **2026-09-12 新收**。三處掛載共用一個追蹤：subagent 派工（spawn_task／Agent）先記一筆，之後若同一支代理跑了裸 `git commit` 卻沒有對應的 process-ledger 紀錄呼叫，就在下一次相關事件標註提醒（永不擋）。`--selftest` 32/32 全過 |
| `appdata_view_guard.py` | PreToolUse `Bash\|PowerShell` | **2026-09-07 新收**。同一台機器上，assistant shell 與使用者自己的 shell 對同一個 `%LOCALAPPDATA%` 路徑／同一個 HKCU 值可能回不同答案，且兩邊都不報錯（2026-09-05 事故，D-057：36 個看板設定被當成「重複檔」刪掉，其實是唯一一份）。只標註（`additionalContext`）不擋；`--selftest` 帶雙邊校準（六個必須觸發／六個必須沉默）。收錄時把校準測資裡的帳號名換成 `<user>` 佔位符，正則本身零機器綁定值 |
| `model_cap_guard.py` | PreToolUse `Agent\|Workflow` | subagent 模型成本上限（只准 haiku/sonnet）。已知繞過：SendMessage-resume 路徑無攔截點，docstring 有完整查證紀錄。**2026-09-07 refresh**：新增「省略 `model` 時讀本機 `agents/*.md` frontmatter 判斷是否在上限內」的繼承缺口補丁 |
| `ui_verify_guard.py` | PreToolUse 瀏覽器 `computer\|javascript_tool` | 擋下「沒先探 `visibilityState` 就要截圖」與「動畫未落停就讀 `getComputedStyle`」。有 per-session marker 與 `intentional-midflight` 逃生口 |
| `browser_pane_scope_guard.py` | PreToolUse 瀏覽器 `navigate\|preview_start` | 記錄每次導覽（app 端 log 不記 URL）。**2026-08-14 起改為白名單 (allowlist)**：loopback 由 hook 自己放行，其餘一律拒絕並改走 out-of-process 路徑。只管 in-app pane，Chrome 那條路永遠不擋 |
| `browser-pane-allowlist.json` | — | 上面那支讀的白名單，出貨時 `hosts` 是空的。手改、進版控，加一筆是刻意行為 |
| `browser-pane-blocklist.json` | — | 保留：它記著每個 host 當初為什麼炸掉，讓拒絕訊息講得出具體理由 |
| `literature_host_guard.py` | PreToolUse `WebFetch\|Bash\|PowerShell\|mcp__(Claude_Browser\|claude-in-chrome)__(navigate\|preview_start\|browser_batch)\|mcp__playwright-headless__browser_navigate` | **2026-09-12 新收**。在工具呼叫邊界執行 [`../global-claude-md/rules/literature-access.md`](../global-claude-md/rules/literature-access.md) 的學術文獻存取政策：查同目錄的 `literature-host-policy.json` 判斷目標 host 走哪一階（開放存取／程式化 API／人類步調可讀／禁止代理存取一律擋）。與技能側 `connectors/access_policy.py`（同一政策表的唯讀視角）、`verify/fetchsrc.py`（實際擷取並記錄 route／status／sha256）是同一機制的三個角色，這輪一起出貨。匯入 `deny_receipt` 走 try/except 容錯（另一機制 hook-deny-message 的模組，同一輪也收進本目錄，所以本 repo 裡匯入會成功）；`hooks/tests/test_literature_host_guard.py` 在本 repo 全數通過（ALL TESTS PASSED，2026-09-12 合併後實測） |
| `ops_health_nudge.py` | SessionStart | 17 項維護門檻（檔案大小、ghost rule、skill 預載預算、字典同步、relaxation 等級未設定、advisory output 未處理…）。健康時完全安靜。**2026-09-07 refresh**：check 1（原本數 `ops/lessons.md` 未摺疊條目數）改成呼叫 `tools/closeout-intake/intake.py report --nudge`，該工具自 2026-10-02 起隨 `../instruments/closeout-intake/` 出貨，複製到 `<CLAUDE_HOME>/tools/closeout-intake/` 才會生效，沒有它這一項是靜默 no-op（fail-open 早就把「工具缺席」列為合法降級路徑，不是新洞）；同輪也把 check 15 訊息裡漏宣告的一個排程任務名（前幾輪的疏漏，跟 check 17 的 mirror 任務同類）換成能力描述 |
| `delivery_gate_shadow.py` | 無（**RETIRED at source 2026-09-27**） | **影子模式，永不阻擋；來源端 commit `ef0d0eb` 已退役，SubagentStop 掛載移除，檔案保留不掛載。**只記錄「如果會擋，會擋什麼」，讓誤判率先被量出來再談強制 |
| `context_runway_shadow.py` | UserPromptSubmit | **影子模式**。context 已經很長**且**這個 session 還沒寫過 checkpoint——兩個條件的**合取**才是觸發點：只看長度會在 65% 的 session 誤報，加上第二個條件降到 26% |
| `fieldwork_threshold_notice.py` | 無（**RETIRED 2026-09-12**） | **影子模式**。主 session 自己讀檔的量對照 `20-dispatch.md` §1 的字面門檻。來源端 commit `bd834ea`（user ruling R-3）已把 `Read\|Grep\|Glob` 掛載整段拿掉：293 筆 shadow row 裡 >=52% 可量化為假陽性，30 天寬限期已過。**檔案與 telemetry 形狀留著、不掛載**，跟來源端一致；退場前的成本說明與退場條件仍在 docstring 裡 |
| `instructions_loaded_logger.py` | InstructionsLoaded | 只做觀測：哪些指令檔在什麼時候被載入。是決定「哪條規則可以搬去 path-scoped」的證據來源 |
| `compact_bookmark.py` | PreCompact | **2026-08-16，compact-recovery 三支之一**（總覽與召回紀律：[`../compact-recovery/README.md`](../compact-recovery/README.md)）。壓縮前把 transcript 路徑／行數／大小／trigger 寫成書籤，再 best-effort 跑 preserve.py，讓活 session 的摘要卡在壓縮當下就存在 |
| `compact_pointer.py` | SessionStart `compact` | 壓縮後注入 ~130 token 指標卡：digest 優先、原檔壓縮前區段（lines 1..N）、兩個召回觸發條件、視窗紀律。書籤缺失時出降級卡而非沉默。**2026-09-07 refresh**：卡片內容加了 handoff snapshot 與 process ledger 兩段（讀 `handoff_snapshot.py`／`<session>.ledger.jsonl`），兩者的寫入工具（`tools/process-ledger/` 等）自 2026-10-02 起隨 `../instruments/` 出貨；沒有工具寫入時指標卡照樣運作，只是那兩段印出「none for this session」 |
| `compact_loss_record.py` | PostCompact | **2026-09-07 新收，compact-recovery 第四支**。每次壓縮寫一列到 `telemetry/compact-loss.jsonl`：書籤、handoff snapshot 存在與否、壓縮前 Write/Edit 過的路徑清單——供之後 `tools/compact-loss-audit`（自 2026-10-02 起隨 `../instruments/compact-loss-audit/` 出貨）判讀「摘要有沒有漏、有沒有誤導」。每 5 次 auto compact 提醒跑一次稽核；來源環境收錄時仍有一段未提交的 docstring 補述，見 manifest 的 `source_dirty_ack` |
| `handoff_snapshot.py` | — | **不是 hook**，是共用函式庫（`compact_bookmark.py`／`compact_pointer.py`／`context_runway_shadow.py` 都 import 它），管 `cache/handoff/<session>.md` 交接快照的路徑、新鮮度判斷與提醒文案。沒有自己的事件掛載，跟 `tests/` 不是 hook 屬同一類，`settings.example.json` 不掛它 |
| `deny_receipt.py` | — | **2026-09-12 新收，不是 hook**。deny/notice 訊息的 receipt 共用函式庫（`clause()`／`notice_clause()`／`fp_clause()`），讓讀到 deny 文字的 agent 能側向去 telemetry 核對這句話真的來自本機 hook、不是被注入的假冒指令。沒有自己的事件掛載，`settings.example.json` 不掛它 |
| `published_record_guard.py` | PreToolUse `Write\|Edit` | **2026-09-12 新收**。目標樹的根目錄帶 `tools/COLLECTION-RULES.md`（本 repo 自己也算）時，payload 內容匹配私有值形狀（磁碟根絕對路徑、POSIX home 路徑、執行期讀到的帳號名、32+ 位十六進位、UUID）就擋寫入。`--selftest` 18/18 全過；收錄過程中對這支自己的即時運作有第一手觀察，見 manifest 條目 |
| `worktree_scope_guard.py` | SessionStart + PreToolUse `Write\|Edit\|NotebookEdit\|Bash\|PowerShell` | **2026-09-12 新收**。session 若跑在 git worktree 裡，SessionStart 先公告 worktree／canonical checkout 的關係，之後任何會 mutate canonical checkout 的「builder」指令一律擋，除非帶 opt-in 標記或直接在 canonical cwd 執行。`--selftest` 37/37 全過 |
| `transcript_read_guard.py` | PreToolUse `Read` | 語料根目錄下 >128KB 的**會談紀錄 (session record)** 無 `limit` 或 >120 行一律 deny，訊息只講限制與重試方式。**2026-08-29 起身分改看形狀不看位置**：`.jsonl`／`digests/` 下的 `.md` 才算紀錄，同目錄的 WebFetch 快取、PDF、索引檔自由讀（誤擋 2 次後的修正，docstring 有誤報紀錄與決策表） |
| `shell_transport_guard.py` | PreToolUse `Bash` | **2026-08-29 新收**。Bash tool 三個**靜默**傳輸缺陷：連續反斜線減半（標註不擋——4,913 次呼叫回測顯示 89/112 命中其實是作者在補償）、≥7,700 B 指令被 OS 截斷（可判定，直接擋）、MSYS 把 `/c`、`/PID` 改寫成路徑（標註）。否決前先把整條指令寫進 telemetry |
| `ps_errorpref_guard.py` | PreToolUse `Write\|PowerShell` | **2026-08-29 新收**。`$ErrorActionPreference='Stop'` 管到原生 exe 時**兩個方向都錯**：stderr 被重導時無害警告變終止錯誤；非零 exit code 反而完全不觸發。只標註不擋。掛在 Write 而非 Edit/Bash 是回測結果：53 個真實 payload 有 47 個經 Write 進來 |
| `ps_pipeline_close_guard.py` | PreToolUse `PowerShell` | **2026-08-29 新收**。`… \| Select-Object -First N` 會**關閉管線並殺掉上游行程**：`python build.py \| Select-Object -First 5` 不是「跑完取前 5 行」，是跑到第 5 行殺掉、回傳 exit 255。同一份回測說這支的真實表面和上一支相反（PowerShell 3411 / Write 0），所以掛載點不同 |
| `branch_commit_guard.py` | PreToolUse `Bash\|PowerShell` | **2026-08-29 新收**。`~/.claude` 內的 checkout 上 `git commit` 時 HEAD 不在 `main` 就擋，除非帶 `[branch-ok]` 或該 worktree 有 opt-in 檔。兩次真實事故（commit 落到同伴 session 的分支）的補償控制——原本的散文儀式當時**有跑，但它在 `&&` 鏈裡不具否決權** |
| `boundary_contract_notice.py` | PreToolUse `Write\|Edit\|NotebookEdit` | **2026-10-02 新收**。L1/L2 主迴圈第一次寫程式檔、而 process ledger 既沒有 boundary-contract 也沒有 waiver 時提醒一次（每 session 一次，只標註不擋）。依賴 `tools/process-ledger/ledger.py` |
| `feedback_notice.py` | PreToolUse `Write\|Edit\|NotebookEdit` | **2026-10-02 新收**。主迴圈第一次改動自己環境的子系統檔（hooks/skills/tools/ops/rules）而 ledger 沒有該目標的 feedback 列時提醒（只標註）。依賴 `tools/feedback-pool/feedback.py`、`tools/process-ledger/ledger.py` |
| `intake_guard.py` | PreToolUse `Write\|Edit\|Bash\|PowerShell` | **2026-10-02 翻案新收**。對 `ops/lessons/` 與 `ops/lessons.md` 的 DENY 守衛：記錄出生後不可改寫，只能走 `intake.py add／event／render`。deny 訊息指向 `tools/closeout-intake/`（出貨在 `instruments/`）。**沒有該 CLI 就會擋住一個你可能根本沒有的路徑——先裝工具再掛這支** |
| `intake_match_shadow.py` | UserPromptSubmit | **2026-10-02 翻案新收**。影子模式、永不印出、永不擋：每個 prompt 跑一次 `intake.py match`，只把「會注入哪些 lesson 卡」寫進 telemetry。依賴 `tools/closeout-intake/` |
| `unattended_run.py` | PreToolUse `Write\|Edit\|NotebookEdit`（`scope`）+ UserPromptSubmit（`kickoff`）+ Stop（`stop`） | **2026-10-02 翻案新收**。一個 run manifest 三個進入點的「無人值守執行」載體：只有 prompt 帶 `[unattended-run]` 時才武裝；武裝後 scope 守衛擋清單外寫入、Stop 守衛在沒有 run report 時擋結束，使用者下一個未標記的 prompt 即結束該 run。依賴 `tools/process-ledger/`、`tools/hook-proof-of-life/` |
| `secret_file_guard.py` | PreToolUse `Read\|Grep\|Bash\|PowerShell` | **2026-10-02 翻案新收**。擋讀取憑證檔名形狀（`.env`、`*.pem`、`*.key`、`credentials.json`、`id_rsa`…）；先剝掉 commit message 本文與只讀 metadata 的 git 子命令再掃描。逃生口 `[user-approved-secret-read]`。deny 訊息指向 literature-search-extract skill 的 connector probe。回歸套件 `tools/secret-guard-test/`（12 必擋、18 必放） |
| `tree_noise_gist.py` | SessionStart | **2026-10-02 新收**。用純 git 的 `tools/tree-noise/noise.py` 分類，只在有「雜訊」髒檔時印一行，告訴 session 那些不是未完成工作 |
| `project_registry_gist.py` | SessionStart | **2026-10-02 翻案新收**。把 `references/PROJECTS.md` 壓成每 session 注入的一張卡（錨定宣告欄位，欄位漂移時**說出來而不是注入垃圾**；超長時保名字、丟細節）。登錄檔缺席時靜默。測試 `tests/test_project_registry_gist.py` 的 L-1/L-2 需要真實登錄檔，缺席時 SKIP 並明說 |
| `golive_check.py` | PostToolUse `Write\|Edit\|MultiEdit` | **2026-10-02 新收**。hook 一存檔就等於上線，所以存檔當下跑它自己 docstring 宣告的 `Proof-of-life:` 指令（以及讀同一份資料的 hook 的套件）；不通過就出一則 notice，**永不擋**。每次執行都先寫 telemetry。依賴 `tools/hook-proof-of-life/pol.py`、`tools/class-closure/`、`tools/system-hmi/` |
| `system_hmi_summary.py` | SessionStart | **2026-10-02 新收**。把 system-hmi 最後一次快照裡「不健康」的項目與 known-good 位置講給 session 聽。快照不存在時印一行「snapshot unavailable」，不報錯。依賴 `tools/system-hmi/`（出貨為樣板） |
| `view_launcher_gist.py` | SessionStart | **2026-10-02 新收**。把核心檢視頁（功能名 -> 路徑）清單注入每個 session，讀 `tools/view-launcher/views.json`；登錄檔缺席時靜默。依賴 `tools/view-launcher/`（出貨為樣板） |
| `verbatim_dispatch_notice.py` | PreToolUse `Agent\|Workflow` | **2026-10-02 新收**。派工 prompt 要求逐字轉錄頁面／圖片時提醒（輸出過濾器會擋長篇受著作權保護的文字，整支 subagent 白跑）。只標註、永不 deny。依賴 `tools/quote-evidence/qe.py`，並執行 source-quotation-evidence 規則 |
| `session_search_query_notice.py` | PreToolUse `mcp__.*__search_session_transcripts` | **2026-10-02 新收**。session 搜尋工具把整個 query 當單一字面子字串，多字 query 幾乎必定回「No matching sessions found」，與真正的 null 不可區分——多字 query 時提醒改用單一關鍵字。只標註 |
| `settings.example.json` | — | 掛載範本，見下 |
| `tests/test_transcript_read_guard.py` | — | `transcript_read_guard.py` 的回歸矩陣（26 個案例，含 4 個 unclassifiable-input）。**手動跑，不是 hook**：`python hooks/tests/test_transcript_read_guard.py` |
| `tests/test_browser_pane_scope_guard.py` | — | **2026-09-12 新收**。`browser_pane_scope_guard.py` 的回歸矩陣。手動跑，不是 hook |
| `tests/test_fieldwork_threshold_notice.py` | — | **2026-09-12 新收**。`fieldwork_threshold_notice.py` 的回歸矩陣（26 案例）——那支 hook 雖已退役（不掛載），檔案仍出貨，所以測它的這支也出貨。手動跑，不是 hook |
| `tests/test_instructions_loaded_logger.py` | — | **2026-09-12 新收**。`instructions_loaded_logger.py` 的回歸矩陣。手動跑，不是 hook |
| `tests/test_project_registry_gist.py` | — | **2026-10-02 翻案新收**。`project_registry_gist.py` 的雙向校準（含「欄位被改名」的 UNDETERMINED 類）。L-1/L-2 檢查真實登錄檔，缺席時明講 SKIP。手動跑，不是 hook |
| `tests/test_golive_check.py` | — | **2026-10-02 新收**。`golive_check.py` 的回歸矩陣（22 案例）。其中 5 個 e2e／registry 案例要在 `<CLAUDE_HOME>/tools/hook-proof-of-life/` 與 `tools/system-hmi/` 都就位的樹裡才會過 |
| `tests/test_system_hmi_summary.py` | — | **2026-10-02 新收**。`system_hmi_summary.py` 的回歸矩陣（18 案例，含壞 JSON fail-open）。手動跑 |
| `tests/test_verbatim_dispatch_notice.py` | — | **2026-10-02 新收**。`verbatim_dispatch_notice.py` 的雙向矩陣（16 案例，含四種 undetermined 輸入）。手動跑 |
| `tests/test_session_search_query_notice.py` | — | **2026-10-02 新收**。`session_search_query_notice.py` 的雙向矩陣（17 案例：8 notice／9 silent）。手動跑 |

## 安裝與啟用｜Install and activate

1. 把 `*.py` 與兩份 `browser-pane-*.json` 複製到你的 `~/.claude/hooks/`；hook 引用的
   method tool 從 `../instruments/<name>/` 複製到 `~/.claude/tools/<name>/`。
2. 打開 `settings.example.json`，把需要的區塊**併進**你自己的 `settings.json`
   （不要整個覆蓋），並替換兩個佔位符：
   - `<PYTHON_EXE>`：Python 3.10+ 直譯器的**絕對路徑**
   - `<CLAUDE_HOME>`：你的 `.claude` 目錄**絕對路徑**

   兩者必須是絕對路徑：Claude Code 不會在 hook command 裡展開 `~` 或環境變數。
   這也是整份設定裡唯一真正綁機器的兩個值。
3. 逐支手動驗證會 exit 0：

   ```powershell
   <PYTHON_EXE> <CLAUDE_HOME>/hooks/ops_health_nudge.py < NUL
   ```

   全部 fail-open，所以「安靜地 exit 0」就是健康狀態。**複製不等於生效**——
   裝完請用你平台自己的方式確認 hook 真的註冊了，別用「檔案在」代替「會觸發」。

## 採用前要知道的事｜Before adoption

- **`settings.example.json` 的 permissions 是「一個人的威脅模型」，不是建議值。**
  逐行讀過再決定；照抄一份你沒自己決定過的 allowlist，比沒有 allowlist 更糟。
  `ask` 那半段才是重點——它讓「改設定」這件事本身變成需要確認的動作。
- **`ops_health_nudge.py` 假設 `~/.claude/ops/`、`~/.claude/skills/` 的目錄結構存在**
  （對應本 repo 的 `claude-ops/ops/`、`skill-toolkit/skills/`）。結構不同就會安靜地
  什麼都不檢查——這是 fail-open 的代價，不是 bug。
- **`delivery_gate_shadow.py` 是實驗儀器的第一階段，且已在來源端退役**（2026-09-27），
  檔案留著供出處與回滾。它 docstring 裡自己列出三個 proxy 的不可靠之處；照抄它的
  verify allowlist 當標準會被 Goodhart。
- **SessionEnd 的 memory-pipeline 腳本（preserve.py）自 2026-08-16 起隨
  [`../compact-recovery/`](../compact-recovery/README.md) 出貨**，但它裝在
  `tools/memory-pipeline/` 而非 hooks/，所以掛載範例放在那份 README 的安裝章——
  本目錄的範本維持「只掛 hooks/ 內檔案」的不變量。
- **`environment-guide/` 裡寫「hooks/（7 個 .py + 1 資料檔）」的地方是 2026-08-14 的快照**，
  當時確實只有七支。那些檔案作為快照保持原樣，正確數字（本輪起為**三十三支掛載 hook**；
  另有 `deny_receipt.py`／`handoff_snapshot.py` 兩支不掛載的共用函式庫，以及
  `fieldwork_threshold_notice.py`、`delivery_gate_shadow.py` 兩支已退役、檔案仍出貨但不掛載）以本目錄為準——這行
  本身在 2026-08-29 升到十六支、2026-09-07 升到十八支、2026-09-12 升到二十一支時都沒
  跟著改過，是同一類「refresh 讓計數變假」的疏漏，此輪一併修正；2026-10-02 升到三十三支。
- **多支 hook 假設 method tool 在 `<CLAUDE_HOME>/tools/<name>/`。** 這些 tool 在本 repo
  出貨於 `../instruments/<name>/`（2026-10-02 起：`closeout-intake`、`process-ledger`、
  `feedback-pool`、`tree-noise`、`quote-evidence`、`hook-proof-of-life`、`class-closure`、
  `system-hmi`、`view-launcher` 等），hook 內的路徑寫的是**來源端**的 `tools/<name>/…`，
  沒有複製過去就找不到——找不到時 hook 一律靜默或降級為一行說明，不擋。
  `ops_health_nudge.py` 的 check 1 用 `tools/closeout-intake/`，缺席時是靜默 no-op。
