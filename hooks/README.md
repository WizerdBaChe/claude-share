# hooks/ — 機械強制層

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

## 為什麼是 hook 而不是規則文字

規則層寫「請記得 X」，模型在自信的當下會讀過去。這幾支的共同判準（`ops/lessons.md`
L-011）是：**觸發形狀如果是一個具名工具呼叫、且參數可檢查，就該用 hook 擋，不該用散文提醒。**
`ui_verify_guard` 的兩個事故在純文字規則下復發了約一個月，換成 hook 之後才停。

全部 **fail-open**：解析錯誤一律 exit 0。守衛的 bug 不能變成工作的阻礙。

## 內容

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
| `ops_health_nudge.py` | SessionStart | 17 項維護門檻（檔案大小、ghost rule、skill 預載預算、字典同步、relaxation 等級未設定、advisory output 未處理…）。健康時完全安靜。**2026-09-07 refresh**：check 1（原本數 `ops/lessons.md` 未摺疊條目數）改成呼叫 `tools/closeout-intake/intake.py report --nudge`，本 repo 不出貨那支工具，所以這一項在本 repo 是永久的靜默 no-op（fail-open 早就把「工具缺席」列為合法降級路徑，不是新洞）；同輪也把 check 15 訊息裡漏宣告的一個排程任務名（前幾輪的疏漏，跟 check 17 的 mirror 任務同類）換成能力描述 |
| `delivery_gate_shadow.py` | SubagentStop | **影子模式，永不阻擋**。只記錄「如果會擋，會擋什麼」，讓誤判率先被量出來再談強制 |
| `context_runway_shadow.py` | UserPromptSubmit | **影子模式**。context 已經很長**且**這個 session 還沒寫過 checkpoint——兩個條件的**合取**才是觸發點：只看長度會在 65% 的 session 誤報，加上第二個條件降到 26% |
| `fieldwork_threshold_notice.py` | 無（**RETIRED 2026-09-12**） | **影子模式**。主 session 自己讀檔的量對照 `20-dispatch.md` §1 的字面門檻。來源端 commit `bd834ea`（user ruling R-3）已把 `Read\|Grep\|Glob` 掛載整段拿掉：293 筆 shadow row 裡 >=52% 可量化為假陽性，30 天寬限期已過。**檔案與 telemetry 形狀留著、不掛載**，跟來源端一致；退場前的成本說明與退場條件仍在 docstring 裡 |
| `instructions_loaded_logger.py` | InstructionsLoaded | 只做觀測：哪些指令檔在什麼時候被載入。是決定「哪條規則可以搬去 path-scoped」的證據來源 |
| `compact_bookmark.py` | PreCompact | **2026-08-16，compact-recovery 三支之一**（總覽與召回紀律：[`../compact-recovery/README.md`](../compact-recovery/README.md)）。壓縮前把 transcript 路徑／行數／大小／trigger 寫成書籤，再 best-effort 跑 preserve.py，讓活 session 的摘要卡在壓縮當下就存在 |
| `compact_pointer.py` | SessionStart `compact` | 壓縮後注入 ~130 token 指標卡：digest 優先、原檔壓縮前區段（lines 1..N）、兩個召回觸發條件、視窗紀律。書籤缺失時出降級卡而非沉默。**2026-09-07 refresh**：卡片內容加了 handoff snapshot 與 process ledger 兩段（讀 `handoff_snapshot.py`／`<session>.ledger.jsonl`），兩者本 repo 皆不出貨對應工具，指標卡本身照樣運作，只是那兩段在沒有工具寫入時印出「none for this session」 |
| `compact_loss_record.py` | PostCompact | **2026-09-07 新收，compact-recovery 第四支**。每次壓縮寫一列到 `telemetry/compact-loss.jsonl`：書籤、handoff snapshot 存在與否、壓縮前 Write/Edit 過的路徑清單——供之後 `tools/compact-loss-audit`（不隨本 repo 出貨）判讀「摘要有沒有漏、有沒有誤導」。每 5 次 auto compact 提醒跑一次稽核；來源環境收錄時仍有一段未提交的 docstring 補述，見 manifest 的 `source_dirty_ack` |
| `handoff_snapshot.py` | — | **不是 hook**，是共用函式庫（`compact_bookmark.py`／`compact_pointer.py`／`context_runway_shadow.py` 都 import 它），管 `cache/handoff/<session>.md` 交接快照的路徑、新鮮度判斷與提醒文案。沒有自己的事件掛載，跟 `tests/` 不是 hook 屬同一類，`settings.example.json` 不掛它 |
| `deny_receipt.py` | — | **2026-09-12 新收，不是 hook**。deny/notice 訊息的 receipt 共用函式庫（`clause()`／`notice_clause()`／`fp_clause()`），讓讀到 deny 文字的 agent 能側向去 telemetry 核對這句話真的來自本機 hook、不是被注入的假冒指令。沒有自己的事件掛載，`settings.example.json` 不掛它 |
| `published_record_guard.py` | PreToolUse `Write\|Edit` | **2026-09-12 新收**。目標樹的根目錄帶 `tools/COLLECTION-RULES.md`（本 repo 自己也算）時，payload 內容匹配私有值形狀（磁碟根絕對路徑、POSIX home 路徑、執行期讀到的帳號名、32+ 位十六進位、UUID）就擋寫入。`--selftest` 18/18 全過；收錄過程中對這支自己的即時運作有第一手觀察，見 manifest 條目 |
| `worktree_scope_guard.py` | SessionStart + PreToolUse `Write\|Edit\|NotebookEdit\|Bash\|PowerShell` | **2026-09-12 新收**。session 若跑在 git worktree 裡，SessionStart 先公告 worktree／canonical checkout 的關係，之後任何會 mutate canonical checkout 的「builder」指令一律擋，除非帶 opt-in 標記或直接在 canonical cwd 執行。`--selftest` 37/37 全過 |
| `transcript_read_guard.py` | PreToolUse `Read` | 語料根目錄下 >128KB 的**會談紀錄 (session record)** 無 `limit` 或 >120 行一律 deny，訊息只講限制與重試方式。**2026-08-29 起身分改看形狀不看位置**：`.jsonl`／`digests/` 下的 `.md` 才算紀錄，同目錄的 WebFetch 快取、PDF、索引檔自由讀（誤擋 2 次後的修正，docstring 有誤報紀錄與決策表） |
| `shell_transport_guard.py` | PreToolUse `Bash` | **2026-08-29 新收**。Bash tool 三個**靜默**傳輸缺陷：連續反斜線減半（標註不擋——4,913 次呼叫回測顯示 89/112 命中其實是作者在補償）、≥7,700 B 指令被 OS 截斷（可判定，直接擋）、MSYS 把 `/c`、`/PID` 改寫成路徑（標註）。否決前先把整條指令寫進 telemetry |
| `ps_errorpref_guard.py` | PreToolUse `Write\|PowerShell` | **2026-08-29 新收**。`$ErrorActionPreference='Stop'` 管到原生 exe 時**兩個方向都錯**：stderr 被重導時無害警告變終止錯誤；非零 exit code 反而完全不觸發。只標註不擋。掛在 Write 而非 Edit/Bash 是回測結果：53 個真實 payload 有 47 個經 Write 進來 |
| `ps_pipeline_close_guard.py` | PreToolUse `PowerShell` | **2026-08-29 新收**。`… \| Select-Object -First N` 會**關閉管線並殺掉上游行程**：`python build.py \| Select-Object -First 5` 不是「跑完取前 5 行」，是跑到第 5 行殺掉、回傳 exit 255。同一份回測說這支的真實表面和上一支相反（PowerShell 3411 / Write 0），所以掛載點不同 |
| `branch_commit_guard.py` | PreToolUse `Bash\|PowerShell` | **2026-08-29 新收**。`~/.claude` 內的 checkout 上 `git commit` 時 HEAD 不在 `main` 就擋，除非帶 `[branch-ok]` 或該 worktree 有 opt-in 檔。兩次真實事故（commit 落到同伴 session 的分支）的補償控制——原本的散文儀式當時**有跑，但它在 `&&` 鏈裡不具否決權** |
| `settings.example.json` | — | 掛載範本，見下 |
| `tests/test_transcript_read_guard.py` | — | `transcript_read_guard.py` 的回歸矩陣（26 個案例，含 4 個 unclassifiable-input）。**手動跑，不是 hook**：`python hooks/tests/test_transcript_read_guard.py` |
| `tests/test_browser_pane_scope_guard.py` | — | **2026-09-12 新收**。`browser_pane_scope_guard.py` 的回歸矩陣。手動跑，不是 hook |
| `tests/test_fieldwork_threshold_notice.py` | — | **2026-09-12 新收**。`fieldwork_threshold_notice.py` 的回歸矩陣（26 案例）——那支 hook 雖已退役（不掛載），檔案仍出貨，所以測它的這支也出貨。手動跑，不是 hook |
| `tests/test_instructions_loaded_logger.py` | — | **2026-09-12 新收**。`instructions_loaded_logger.py` 的回歸矩陣。手動跑，不是 hook |

## 安裝

1. 把 `*.py` 與兩份 `browser-pane-*.json` 複製到你的 `~/.claude/hooks/`。
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

## 採用前要知道的事

- **`settings.example.json` 的 permissions 是「一個人的威脅模型」，不是建議值。**
  逐行讀過再決定；照抄一份你沒自己決定過的 allowlist，比沒有 allowlist 更糟。
  `ask` 那半段才是重點——它讓「改設定」這件事本身變成需要確認的動作。
- **`ops_health_nudge.py` 假設 `~/.claude/ops/`、`~/.claude/skills/` 的目錄結構存在**
  （對應本 repo 的 `claude-ops/ops/`、`skill-toolkit/skills/`）。結構不同就會安靜地
  什麼都不檢查——這是 fail-open 的代價，不是 bug。
- **`delivery_gate_shadow.py` 是實驗儀器的第一階段**，不是成品閘門。它 docstring 裡
  自己列出三個 proxy 的不可靠之處；照抄它的 verify allowlist 當標準會被 Goodhart。
- **SessionEnd 的 memory-pipeline 腳本（preserve.py）自 2026-08-16 起隨
  [`../compact-recovery/`](../compact-recovery/README.md) 出貨**，但它裝在
  `tools/memory-pipeline/` 而非 hooks/，所以掛載範例放在那份 README 的安裝章——
  本目錄的範本維持「只掛 hooks/ 內檔案」的不變量。
- **`environment-guide/` 裡寫「hooks/（7 個 .py + 1 資料檔）」的地方是 2026-08-14 的快照**，
  當時確實只有七支。那些檔案作為快照保持原樣，正確數字（本輪起為**二十一支掛載 hook**；
  另有 `deny_receipt.py`／`handoff_snapshot.py` 兩支不掛載的共用函式庫，以及
  `fieldwork_threshold_notice.py` 一支已退役、檔案仍出貨但不掛載）以本目錄為準——這行
  本身在 2026-08-29 升到十六支、2026-09-07 升到十八支、2026-09-12 升到二十一支時都沒
  跟著改過，是同一類「refresh 讓計數變假」的疏漏，此輪一併修正。
- **`ops_health_nudge.py` 假設 `tools/closeout-intake/`（check 1 用）與
  `tools/process-ledger/`（多支 hook 的訊息文字引用）存在**，本 repo 兩者都不出貨。
  check 1 因此永久靜默 no-op；引用 process-ledger 指令的訊息文字仍會印出，照抄指令
  會找不到檔案——這是文件性質的能力描述，不是本 repo 出貨的可執行路徑。
