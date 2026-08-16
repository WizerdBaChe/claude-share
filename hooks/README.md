# hooks/ — 機械強制層

> 這批檔案是 2026-08-14 才補進本 repo 的。在那之前，`claude-ops/` 與
> `environment-guide/` 有 20 多處引用它們當作「機械強制」的依據，但檔案一個都沒附，
> 而 manifest 把原因寫成「machine-bound（綁機器）」——**那個判斷是錯的**。
> 逐檔查證後：所有 hook 全部用 `Path.home()`／`os.path.expanduser`／
> `CLAUDE_CONFIG_DIR`／`os.environ["TEMP"]` 解析路徑，**零個寫死的帳號或絕對路徑**。
> 它們不是不能分享，是從來沒被撈進來。收錄程序見
> [`../tools/COLLECTION-RULES.md`](../tools/COLLECTION-RULES.md)。

## 為什麼是 hook 而不是規則文字

規則層寫「請記得 X」，模型在自信的當下會讀過去。這幾支的共同判準（`ops/lessons.md`
L-011）是：**觸發形狀如果是一個具名工具呼叫、且參數可檢查，就該用 hook 擋，不該用散文提醒。**
`ui_verify_guard` 的兩個事故在純文字規則下復發了約一個月，換成 hook 之後才停。

全部 **fail-open**：解析錯誤一律 exit 0。守衛的 bug 不能變成工作的阻礙。

## 內容

| 檔案 | 事件 | 做什麼 |
|---|---|---|
| `dangerous_command_guard.py` | PreToolUse `Bash\|PowerShell` | 不可逆指令的確定性拒絕清單：遞迴強制刪除、`git push --force`／`reset --hard`／`clean -f`、registry 寫入、關機／格式化。放寬 allowlist 後的補償控制 |
| `model_cap_guard.py` | PreToolUse `Agent\|Workflow` | subagent 模型成本上限（只准 haiku/sonnet）。已知繞過：SendMessage-resume 路徑無攔截點，docstring 有完整查證紀錄 |
| `ui_verify_guard.py` | PreToolUse 瀏覽器 `computer\|javascript_tool` | 擋下「沒先探 `visibilityState` 就要截圖」與「動畫未落停就讀 `getComputedStyle`」。有 per-session marker 與 `intentional-midflight` 逃生口 |
| `browser_pane_scope_guard.py` | PreToolUse 瀏覽器 `navigate\|preview_start` | 記錄每次導覽（app 端 log 不記 URL）。**2026-08-14 起改為白名單 (allowlist)**：loopback 由 hook 自己放行，其餘一律拒絕並改走 out-of-process 路徑。只管 in-app pane，Chrome 那條路永遠不擋 |
| `browser-pane-allowlist.json` | — | 上面那支讀的白名單，出貨時 `hosts` 是空的。手改、進版控，加一筆是刻意行為 |
| `browser-pane-blocklist.json` | — | 保留：它記著每個 host 當初為什麼炸掉，讓拒絕訊息講得出具體理由 |
| `ops_health_nudge.py` | SessionStart | 13 項維護門檻（檔案大小、ghost rule、skill 預載預算、字典同步、relaxation 等級未設定、advisory output 未處理…）。健康時完全安靜 |
| `delivery_gate_shadow.py` | SubagentStop | **影子模式，永不阻擋**。只記錄「如果會擋，會擋什麼」，讓誤判率先被量出來再談強制 |
| `context_runway_shadow.py` | UserPromptSubmit | **影子模式**。context 已經很長**且**這個 session 還沒寫過 checkpoint——兩個條件的**合取**才是觸發點：只看長度會在 65% 的 session 誤報，加上第二個條件降到 26% |
| `fieldwork_threshold_notice.py` | PreToolUse `Read\|Grep\|Glob` | **影子模式**。主 session 自己讀檔的量對照 `20-dispatch.md` §1 的字面門檻。**高頻 matcher**：每次呼叫多付一次 Python 啟動（約 100ms），掛載前先讀它 docstring 裡的成本說明與退場條件 |
| `instructions_loaded_logger.py` | InstructionsLoaded | 只做觀測：哪些指令檔在什麼時候被載入。是決定「哪條規則可以搬去 path-scoped」的證據來源 |
| `settings.example.json` | — | 掛載範本，見下 |

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
- **來源環境還有一支 SessionEnd 的 memory-pipeline hook**，那支腳本不在本次分享範圍，
  所以範本裡整個區塊移除，而不是留一個指向不存在檔案的掛載。
- **`environment-guide/` 裡寫「hooks/（2 檔）」的地方是 2026-07-31 的快照**，
  當時確實只有兩支。那些檔案作為快照保持原樣，正確數字以本目錄為準。
