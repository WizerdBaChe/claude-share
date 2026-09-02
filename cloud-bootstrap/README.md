# cloud-bootstrap — 讓雲端容器長得像本機 (LikeLocal)

> 給人讀的手冊。機器讀的本體：`bootstrap.py`（安裝器／驗收）、
> `ops-environment.cloud.md`（雲端容器的環境事實，安裝時覆蓋 `ops/environment.md`）、
> repo 根目錄的 `.claude/settings.json`（SessionStart 掛載＋十六支 hook 的掛載）與
> `.claude/hooks/session-start.sh`、`.claude/hooks/run-hook.sh`（兩支殼層包裝）。
> 建立於 2026-09-02。

## 這是什麼

Claude Code on the web（claude.ai/code）的每個 session 都跑在一個**用完即丟的容器**裡：
repo 重新 clone，`~/.claude` 重新生成，裡面沒有任何操作者自己的環境——沒有全域
`CLAUDE.md`、沒有 ops 規則層、沒有 skills、沒有 hooks、沒有 agents。

本 repo 已經是那個環境去識別化後的副本，而且每個分享資料夾都寫了「怎麼手動搬到一台
機器上」（`environment-guide/OPERATOR-GUIDE.md` Part 3、各資料夾的 README）。
這一層做的事只有一件：**把那套手動程序做成機械動作**，讓 repo 自己在每次 session
開始時把自己裝進容器的 `~/.claude`，所以雲端 session 跟本機 session 讀的是同一套
全域偏好、同一層規則、同一組 skills 與 guards。

搬進去的**只有 repo 裡本來就出貨的東西**；本層不會、也不能補上 repo 刻意不出貨的
部分（見下方「明知不蓋的地方」）。

## 機制：兩個入口、一個安裝器

```
Session 開始（CLAUDE_CODE_REMOTE=true）
   │
   ├─ .claude/settings.json  SessionStart ──► .claude/hooks/session-start.sh
   │        1. python3 cloud-bootstrap/bootstrap.py install   （log 寫到 ~/.claude/cloud-bootstrap.log）
   │        2. bootstrap.py summary   → 一行卡片進 context
   │        3. 接著跑 hooks/ops_health_nudge.py（同一份 stdin）→ [ops-health] 行進 context
   │
   └─ .claude/settings.json  PreToolUse / PostToolUse / PreCompact / SubagentStop /
      InstructionsLoaded / UserPromptSubmit / SessionStart(compact)
            每一支都經 .claude/hooks/run-hook.sh <name>.py
            → 找得到 repo 的 hooks/<name>.py 就 exec，找不到就 exit 0（fail-open）
```

`bootstrap.py install` 的複製表（來源 → `~/.claude/` 相對位置）：

| repo 內 | 裝到 | 備註 |
|---|---|---|
| `global-claude-md/CLAUDE.md` | `CLAUDE.md` | **渲染**：`<OS_NAME>`→Linux (Ubuntu 24.04)、`<DEFAULT_SHELL_NAME>`→bash、次要 shell 子句刪除、`<LINE_ENDING_CONVENTION>`→LF；給採用者看的 `<!-- Placeholder note -->` 全部拿掉（每 session 都要付的位元組）。repo 內的範本**不動** |
| `global-claude-md/rules/*.md` | `rules/` | path-scoped 規則，五份 |
| `claude-ops/ops/**` | `ops/` | 22 檔；然後 `ops-environment.cloud.md` **覆蓋** `ops/environment.md`（Windows 那份留在 repo 當紀錄） |
| `claude-ops/references/PROJECTS.md` | `references/PROJECTS.md` | 只有表頭格式 |
| `skill-toolkit/skill-trigger-dict.md`、`skills/*` | `skill-trigger-dict.md`、`skills/<name>/` | 17 顆；裝進去即生效（本 session 實測：安裝後 skill 名冊立刻多出 17 個） |
| `hooks/*.py`、`hooks/*.json` | `hooks/` | 16 支＋2 份 JSON；規則檔以 `hooks/` 開頭引用的每一支因此可解析。掛載走 repo 副本（見上圖） |
| `agents/*.md`（README 除外） | `agents/` | 8 支 subagent 定義 |
| `environment-guide/{PHILOSOPHY,OPERATOR-GUIDE,COMMIT-TEMPLATES}.md` | 根目錄 | 規則檔以 `~/.claude/PHILOSOPHY.md` 等路徑引用 |
| `compact-recovery/preserve.py` | `tools/memory-pipeline/preserve.py` | `compact_bookmark.py` 以這個路徑呼叫它 |
| `architecture-diagramming/archdiag/` | `tools/archdiag/` | `diagram-authoring` skill 以來源路徑 `tools/archdiag` 路由 |
| `thinking-notes/*.md` | `thinking-notes/` | 設計思考筆記 |
| `hooks/settings.example.json` 的一部分 | `settings.json` | 只在檔案**不存在或是本層寫的**時才寫；帶 permissions／env／`disableWorkflows`／`cleanupPeriodDays`；**不帶** `hooks`（由 repo 的 `.claude/settings.json` 掛）、**不帶** `model`／`effortLevel`（雲端由主機決定） |

安裝完成在 `~/.claude` 根目錄寫下 `cloud-bootstrap.json` 標記（安裝時間、repo commit、檔案數）；
`bootstrap.py status` 拿它跟目前 HEAD 比，不一致就叫你重裝。

## 為什麼 hook 從 repo 的 `.claude/settings.json` 掛，而不是寫進 `~/.claude/settings.json`

1. **時序**：project-scope 的掛載從第一個 session 的第一次工具呼叫就生效；由
   SessionStart hook 寫出來的 user-scope `settings.json`，不保證在同一個 session 的
   第一支 hook 觸發前被讀到。
2. **fail-open 要延伸到掛載本身**：直接 `python3 <path>` 掛一個不存在的檔，python
   exit 2，Claude Code 視為**阻擋**——每一次符合 matcher 的工具呼叫都被擋
   （`hooks/branch_commit_guard.py` 事故 #3 就是這樣全機癱掉的）。`run-hook.sh`
   找不到檔案就 exit 0，所以任何一個分支少了某支 hook 都不會把 session 鎖死。
3. **不重複執行**：`run-hook.sh` 與 `session-start.sh` 都先看 `CLAUDE_CODE_REMOTE`，
   不是 `true` 就立刻 exit 0。操作者在自己機器上開這個 repo 時，這份
   `.claude/settings.json` 是惰性的，本機 `~/.claude/settings.json` 掛的那一份
   才是唯一在跑的。

掛載表與 `hooks/settings.example.json` 逐事件、逐 matcher 對齊，唯一刻意的差別：
`ops_health_nudge.py` 不是 SessionStart 的**平行兄弟**，而是接在安裝之後
（同一組 matcher 的 hooks 是平行跑的；全新容器上 nudge 會 stat 到一個還不存在的
`ops/`，fail-open 所以安靜，等於少檢查一次）。

## 日常操作

```bash
python3 cloud-bootstrap/bootstrap.py install   # 重裝（冪等；改了 repo 內任何會被複製的東西之後跑）
python3 cloud-bootstrap/bootstrap.py verify    # 驗收：檔案齊、CLAUDE.md 無殘留佔位符、16 支 hook 空輸入皆 exit 0、兩支 guard 對已知壞輸入 deny／好輸入 allow、掛載表與 hooks/ 一致
python3 cloud-bootstrap/bootstrap.py status    # 裝的是哪個 commit；HEAD 變了會 exit 1
python3 cloud-bootstrap/bootstrap.py summary   # SessionStart 印的那一行
```

正常情況下不用手動跑——每次 session 開始都會自動 `install`。手動跑的時機：
同一個 session 內改了 `hooks/`、`claude-ops/`、`global-claude-md/`、`skill-toolkit/`、
`agents/`、`cloud-bootstrap/` 任何一處之後（複製不等於生效；`verify` 的輸出貼進交付）。

## 每次 session 開頭會看到的兩行

1. `[cloud-bootstrap] ~/.claude installed from repo <sha> (N files: …)` — 安裝器的卡片。
   若寫的是 `install FAILED`，讀 `~/.claude/cloud-bootstrap.log`。
2. `[ops-health] …` — 健康檢查。**以下幾條在雲端是預期會出現的，不是本層的缺陷**：
   - `ops/cc-reconciled.json missing` — 版本對帳戳記是來源機器的產物；容器的 CLI
     （2.1.258）比 `ops/` 最後對帳的版本新，這條說的是實話。要消音就在來源環境做一輪
     對帳再重新收錄 `ops/`，不是在這裡偽造戳記。
   - `skill(s) absent from skill-trigger-dict.md: session-start-hook` — 那是平台放進
     容器 `~/.claude/skills/` 的 skill，不是本 repo 的；字典是收錄檔，不在這裡改。
   - `SKILL.md over 300 lines` / `CLAUDE.md 19.9K over 19.5K` / `lessons.md 32 entries` —
     來源環境當下的狀態，本機也會看到同樣的提醒。

## 活體驗收（`[BC]`：照 `OPERATOR-GUIDE.md` Part 3 第 8 步的形式）

A 必驗（不過就不算搬完）：

1. **全新 session 的第一句回覆是繁體中文**，且模型能說出自己讀到的
   `~/.claude/CLAUDE.md`「Environment」條寫的是 Linux／bash／LF。
   → 證明全域 CLAUDE.md 在第一個 system prompt 之前就位。**這是本層唯一沒在容器裡
   實測過的時序**（安裝在本 session 內完成，無法重開 session 觀察）；從快取容器的
   第二個 session 起檔案早就存在，一定會載入。若第一個 session 沒中：容器快取之後
   再開一次即可，並把觀察記進 `ops-environment.cloud.md`「Instruction-loading」段。
2. session 開頭出現 `[cloud-bootstrap] … installed` 與 `[ops-health] …` 兩行。
3. 派一個 subagent 指定 `model: "opus"` → 被 `model_cap_guard.py` 擋下，訊息提到
   `[user-approved-top-tier]`。（`verify` 已用同一 payload 離線證明 deny；這一步證明
   掛載真的在跑。）
4. 下一個 `git push --force …` 或 `rm -rf <非 tmp 路徑>` 被 `dangerous_command_guard.py`
   擋下。
5. 問一句該由 `scientific-research-guide` 或 `code-review-deep-checklist` 接的問題 →
   正確的 skill 接手（skill 名冊已在本 session 實測出現）。

B 體驗：

6. `/compact` 之後出現 compact-recovery 的指標卡（`compact_pointer.py`；書籤由
   `compact_bookmark.py` 在壓縮前寫）。
7. `python3 cloud-bootstrap/bootstrap.py status` 在改動 repo 並 commit 後 exit 1，
   重裝後 exit 0。

看它判什麼、不破壞地看：`~/.claude` 根目錄的 `cloud-bootstrap.json`（裝了什麼）、
`~/.claude/cloud-bootstrap.log`（每次安裝的逐行紀錄）、`~/.claude/telemetry/*.jsonl`
（各 shadow hook 的觀測列）。

## 明知不蓋的地方（是設計，不是缺陷）

- **記憶不搬。** `projects/<slug>/memory/` 從來不在 git、也不在本 repo
  （OPERATOR-GUIDE.md 2.2）。雲端 session 需要某個「上次說過」的事實時，要問或從已
  commit 的紀錄讀。平台同步進容器的 `import-memory` skill 是把匯出檔匯進去的路，
  但匯出檔本身得由操作者提供。
- **interop 不裝。** 容器裡沒有 opencode 或任何其他 agent CLI；
  `ops_health_nudge.py` check 12 在 `interop/` 不存在時本來就安靜，裝了反而會永遠
  報「目標未部署」。
- **外部派工層不存在。** `tools/extdispatch/` 與它的兩支 hook 本來就不出貨
  （`tools/share-manifest.toml`）；`20-dispatch.md` §4a 走「沒有外部 tier」那條分支，
  紅隊審查用 fresh-context sonnet 的 fallback。
- **瀏覽器窗格與 PowerShell 的 hook 是掛著但不會觸發的。** 容器沒有 in-app Browser
  pane 的 MCP 工具、沒有 PowerShell 工具；`ui_verify_guard`、`browser_pane_scope_guard`、
  `ps_errorpref_guard`、`ps_pipeline_close_guard` 留在掛載表是為了逐一對齊範本，
  代價是零（matcher 不會命中）。
- **`model` 與 `effortLevel` 不寫進 `settings.json`。** 雲端每個 session 的模型與
  effort 由主機／使用者在 claude.ai 上選，寫一個 pin 只會跟那個選擇打架。
  `disableWorkflows: true` 有寫，但只從快取容器的第二個 session 起生效
  （設定在程序啟動時讀）。
- **`hooks/tests/test_transcript_read_guard.py` 在 Linux 上跑不起來**（它用
  `ctypes.windll` 算 Windows 短路徑）；`transcript_read_guard.py` 本身正常，`verify`
  只證明它 fail-open，回歸矩陣要在 Windows 上跑。
- **`share_gate.py --source ~/.claude` 在容器裡沒有意義**：那棵樹是本 repo 裝出來的
  副本，V 會拿 repo 跟自己比。閘門與 `test_share_gate.py` 都認得
  `cloud-bootstrap.json` 標記，看到就明說不跑 V，不會當成通過。
- **repo 內 `global-claude-md/CLAUDE.md` 會被 Claude Code 當成子目錄的專案規則。**
  只在讀到該目錄下的檔案時載入，內容與已裝進 `~/.claude/CLAUDE.md` 的同源，
  代價是偶爾重複一次；`ADOPTERS.md`「Where to put things」講的風險在這裡是刻意接受的。

## 平台契約備忘（review-when）

本層押在四個平台行為上，任一個變了先復查再信卡片：

1. project-scope `.claude/settings.json` 的 hooks 在遠端 session 會被執行，且指令經
   shell 展開 `$CLAUDE_PROJECT_DIR`（2026-09-02 依 `session-start-hook` skill 的說明
   與本 session 內的 hook 執行實測）。
2. SessionStart hook 的 stdout 注入 context；`CLAUDE_CODE_REMOTE=true` 在遠端 session
   一定設定（本 session 環境變數實測）。
3. 容器在 SessionStart hook 完成後被快取（`session-start-hook` skill 的說明）。
4. `~/.claude/skills/<name>/` 放進去即被登錄（本 session 實測，無需重啟）。
