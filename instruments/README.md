# instruments — 可攜驗證工具｜Portable verification instruments

> **中文摘要｜Chinese summary**：本層收兩類東西。（一）本 repo 出貨的規則檔直接引用為
> Enforcement 的驗證工具：page-fill-gate 與 check_cap_binding.py。（二）2026-10-02 使用者
> 裁決之後收進來的 hook 測試套件與 lint／存活證明工具：它們的**對象**是本 repo 出貨的
> hook、規則或紀錄格式，資料檔只是 fixture。不是完整 tools tree，也不是新的 runtime；
> 收錄理由、安裝位置、每支工具的需求與已知限制，都在這份 README。
>
> **English summary**: This directory ships (1) the two portable instruments named by
> shipped rules as enforcement, and (2) since the 2026-10-02 owner ruling, the hook test
> suites and lint / proof-of-life instruments whose SUBJECT is a hook, rule or record
> format this repo ships. It is not the source tools tree and not a new runtime. Almost
> every suite here is written for an INSTALLED config home; the table below says which
> ones also run from this repo's own tree, and what each one needs.

## 快速導覽｜Quick guide

| 項目 | 中文 | English |
|---|---|---|
| 收錄 | 18 個資料夾、43 個檔案（本 README 之外） | 18 directories, 43 files besides this README |
| 先讀 | 收錄標準，再看「每支工具」表的「需要什麼」欄 | Read the admission criterion, then the "needs" column |
| 驗證 | 每個套件雙側校準（known-TRUE 與 known-FALSE）；數字見「本輪實測」 | Every suite is two-sided; measured counts are under "Measured this round" |
| 不包含 | 來源環境的 tools tree 其餘部分、操作者私有檔案清單的守衛測試、私有索引工具 | The rest of the source tools tree, suites of guards that gate one operator's private files, private-index tools |

## 收錄標準｜Admission criterion

2026-09-12（兩支工具）與 2026-10-02（hook 測試套件，使用者裁決）兩次裁決疊加。一個資料夾收，
當且僅當：

1. 它的**對象**（subject）是本 repo 出貨的 hook、規則或紀錄格式（或本輪經 hooks 管線出貨的
   hook）——被測的東西在這裡，測試才有意義；
2. 它的**資料檔是 fixture，不是這台機器的紀錄**（真實 session id、遙測列、私有路徑清單都不收，
   或收成空模板）；
3. 只用標準庫 (stdlib-only)，page-fill-gate 另需 Playwright（見其 README）；
4. 自帶雙側校準：同時驗 known-TRUE 與 known-FALSE。一支只回報過乾淨結果的檢查器，其 100%
   通過率本身就是要先懷疑的紅旗。

**明確不收，附理由：**

- `secret-guard-test`：對象 `hooks/secret_file_guard.py` 不出貨（它的政策就是一個操作者的私有
  檔名清單，見 manifest 該 hook 的 `not_shipped` 條目）。對象不在，測試無從跑。
- `session-board-test`：對象 `hooks/session_board_register.py` 不出貨，且它寫入的 session-board
  登記簿是來源環境的私有紀錄。
- `skill-routing-audit-test`：測試跟著對象走，對象是 `skill-routing-audit.py`，它出不出貨由 `tools/` 的
  manifest 條目決定；它的測試用合成逐字稿，但沒有對象就沒有東西可測。
- 對私有樹建索引的工具（`graph-snapshot`、`version-census`、`copy-census` 等）：離開來源環境
  自己的目錄結構，沒有東西可查。

## 每支工具｜Instrument inventory

「在地」指在本 repo 樹內原地執行；「裝好」指複製到 `~/.claude/tools/NAME/` 並與 `hooks/`、
`ops/`、`rules/`、`agents/` 同在一個設定家目錄下。**驗證過的版面是「裝好」**；在地欄只寫實際
跑過的。

### A. 原有兩支｜The original two

| 工具 | 檢查什麼 | 怎麼跑 | 需要什麼 | 自帶校準 |
|---|---|---|---|---|
| `page-fill-gate/fill_gate.py` | 人讀 HTML 有沒有留下不對稱右側空白（靠左錨定上限）；每頁該填多少由 `page_classes.json` 決定 | `python instruments/page-fill-gate/fill_gate.py PAGE.html [--class X]`（在地可跑） | Playwright 加 chromium | 每次先跑 `fixtures/` 的 known-bad 必 FAIL、known-good 必 PASS，否則整次無效 |
| `ops-health-test/check_cap_binding.py` | sweep check 7b：cap 常數在機制（`hooks/ops_health_nudge.py`）與規則文字（`ops/40-maintenance.md`、`ops/rule-registry.md`）兩邊是否一致 | `python tools/ops-health-test/check_cap_binding.py [--selftest]`（裝好） | 設定家目錄的 `ops/` 與 `hooks/` | `--selftest`：1 個 known-TRUE 加 4 個 known-FALSE |

### B. Hook 測試套件｜Hook test suites（2026-10-02）

每支都以 subprocess 驅動 hook、餵真的 JSON stdin，把遙測重導到暫存目錄（正式紀錄不被碰，
並斷言這件事）。

| 資料夾（對象 hook） | 怎麼跑 | 需要什麼 | 已知限制 |
|---|---|---|---|
| `branch-guard-test`（`hooks/branch_commit_guard.py`） | `python tools/branch-guard-test/test_branch_commit_guard.py` | 裝好；git | 讀 `parents[2]` 找 hook，在地需 `hooks/` 與來源版本一致 |
| `dangerous-command-test`（`hooks/dangerous_command_guard.py`） | `python tools/dangerous-command-test/test_dangerous_command_guard.py` | 裝好 | 同上 |
| `model-cap-test`（`hooks/model_cap_guard.py`） | `python tools/model-cap-test/test_model_cap_guard.py` | 裝好；`agents/` 要有 api-tester 與 work-card-executor 兩個定義（本 repo 的 `agents/` 有） | 在地需 `hooks/` 加 `agents/` |
| `ps-errorpref-test`（`hooks/ps_errorpref_guard.py`） | `python tools/ps-errorpref-test/test_ps_errorpref_guard.py [HOOK路徑]` | 只要 hook 檔 | **可在地跑**：第一個參數給 hook 路徑 |
| `ps-pipeline-close-test`（`hooks/ps_pipeline_close_guard.py`） | `python tools/ps-pipeline-close-test/test_ps_pipeline_close_guard.py [HOOK路徑]` | 只要 hook 檔 | 可在地跑，同上 |
| `shell-transport-test`（`hooks/shell_transport_guard.py`） | `python tools/shell-transport-test/test_shell_transport_guard.py [HOOK路徑]` | 只要 hook 檔 | 可在地跑，同上 |
| `ui-verify-test`（`hooks/ui_verify_guard.py`） | `python tools/ui-verify-test/test_ui_verify_guard.py [HOOK路徑]` | 只要 hook 檔 | 可在地跑；斷言正式 receipts 檔大小不變。來源樹的一次 `pol.py` 掃描裡它曾是 25/26，原因未釐清（單獨跑與暫存樹裡都是 26/26） |
| `e2-gate-test`（`hooks/delivery_gate_shadow.py`） | `python tools/e2-gate-test/test_shadow_hook.py`；另有 `make_fixture.py`（建沙盒）與 `check_shadow_log.py`（讀影子紀錄） | 裝好 | 測試用合成逐字稿，不依賴任何真實 session；`check_shadow_log.py` 要等 hook 真的跑過才有東西可讀 |
| `ops-health-test`（`hooks/ops_health_nudge.py`），剩下的 `test_ops_health_nudge.py` | `python tools/ops-health-test/test_ops_health_nudge.py [HOOK路徑]` | 裝好；git 身分；`tools/tracking-refs/`（check 18 載入它，**本 repo 不出貨**，缺它時 112 個案例有 1 個失敗） | 數分鐘（未計時）。hook 路徑含 `CLAUDE_SHARE` 時，套件改按本 repo 宣告的特化（check 11 看 ops 層在不在）判讀；掛在別的目錄名下就按來源版判讀。case 17 與 19 對「排程任務名」只斷言訊息裡有 `task` 一字（任務名是私有字面值，已改，見 manifest） |

### C. 規則、紀錄格式與存活證明工具｜Rule / record-format / proof-of-life instruments

| 資料夾 | 檢查什麼 | 怎麼跑 | 需要什麼 | 已知限制 |
|---|---|---|---|---|
| `hook-deny-lint` | 每個 hook 送進工具結果的字串（deny 與 notice 兩個面）是否合 `global-claude-md/rules/hook-deny-message.md`；`report_fp.py` 是每則合格 deny 訊息都點名的誤擋回報出口 | `python tools/hook-deny-lint/lint.py [--controls]` | 裝好（讀 `hooks/`、`settings.json`、`rules/`）；`--controls` 不需要樹 | 靜態 AST 抽取，FAIL 只做結構判斷，語意層一律 WARN |
| `hook-proof-of-life` | 執行每個已註冊 hook 在自己 docstring 宣告的存活證明套件（AP-63） | `python tools/hook-proof-of-life/pol.py [--list]`；`controls.py` 校準 | 裝好；每個被宣告的套件都要在 | 約 3 至 5 分鐘。宣告了但本機沒有的套件，照實報 FAIL，不隱藏；本輪量測見下 |
| `class-closure` | 每個控制套件是否帶著一個它必須判為 `undetermined` 的案例（AP-62）：`closure.py` 靜態檢查，`exercise.py` 實際執行並用 `probe/` 探針確認那條分支真的被走到 | `python tools/class-closure/closure.py`；`exercise.py`；`controls.py` | 裝好（讀 hook 與已宣告的套件） | 讀不到或宣告了卻不存在的套件列為 undetermined、不算進任何計數。來源的 golive_check hook（若本 repo 出貨它）會 import `closure.py` |
| `entry-schema-lint` | 規則條目格式（`claude-ops/ops/references/entry-schema.md`）與 `principle-design-guide.md` 的資產屬性中有機械偵測的那幾條 | `python -X utf8 tools/entry-schema-lint/lint.py`；`controls.py` | 裝好；**ES-9 需要來源的 `tools/system-hmi/` 登記簿** | 少了 system-hmi：`lint.py` 報 ES-9 錨點遺失並以 2 結束（不可判定，絕不當成通過），`controls.py` 有 3 個控制（C-00、C-32、C-35）會 FAIL。詳見「本輪實測」 |
| `telemetry-framing` | `telemetry/*.jsonl` 裡不可解析的列數（損壞框架），對照有日期的基線 | `python tools/telemetry-framing/framing.py`；`controls.py` | 裝好 | `framing.py` 的 BASELINE（16，2026-09-08）是來源機器的量測，採用者要依檔內 review-when 自己重錄。`suite-sessions.json` 出貨成**空模板**（`session_files` 為空），缺檔或為空都不跳過任何列 |
| `context-budget` | 啟動時付出多少 context：`startup_baseline.py` 讀逐字稿算第一則助理訊息的 token 與常駐指令檔大小；`rule_loads.py` 拆解 InstructionsLoaded 遙測；`ACCEPTANCE.md` 是人工驗收程序 | `python tools/context-budget/startup_baseline.py [--project DIR]` | 裝好；有逐字稿與遙測才有輸出 | 沒有 `telemetry/rule-loads.jsonl` 時 `rule_loads.py` 以 2 結束。沒有自帶校準套件（量測腳本加人工程序） |
| `ps-errorpref-backtest`、`ps-pipeline-close-backtest` | 把對應 hook 的 `analyze()` 放到真實逐字稿語料上，印觸發率 | `python tools/ps-errorpref-backtest/backtest.py [--root DIR] [--sample N]` | 逐字稿語料（預設只有設定家目錄的 `projects/`；來源版另有一個離線封存目錄，已移除，用 `--root` 補） | 沒有語料時印「no PowerShell-language payloads found」並以 1 結束。內嵌的 BASELINE 是來源機器的量測，不是你的 |

## 安裝｜Install

複製 `instruments/NAME/` 整個資料夾到 `~/.claude/tools/NAME/`。子路徑刻意跟來源環境一致，所以
已出貨規則檔與 hook docstring 裡原封不動的 `tools/NAME/...` 引用，裝完就直接解析得到。大多數
套件從 `parents[2]` 或 `~/.claude` 找 hook，所以設定家目錄還要有 `hooks/`、`ops/`（本 repo 的
`claude-ops/ops/` 對應到它）、`rules/`（本 repo 的 `global-claude-md/rules/`）與 `agents/`。

## 本輪實測｜Measured this round

2026-10-02，來源 HEAD 183c129。方法：一個暫存的「裝好」版面（來源的 `hooks/`、`ops/`、`rules/`、
`agents/`、`references/`、`skills/` 加上本資料夾的副本，家目錄環境變數指向暫存樹），每個套件從
暫存家目錄跑。**不是**在本 repo 樹內跑，也沒有對照 hooks 管線尚未合併的版本逐一重跑（見下）。

| 套件 | 結果 |
|---|---|
| dangerous-command-test | 80/80 |
| branch-guard-test | 25/25 |
| model-cap-test | 40/40 |
| e2-gate-test | 22/22 |
| ps-errorpref-test | 47/47 |
| ps-pipeline-close-test | 56/56 |
| shell-transport-test | 57/57 |
| ui-verify-test | 26/26 |
| ops-health-test | 112/112 在 `tools/tracking-refs/` 同在時；少了它是 111/112（失敗的是 check 18） |
| check_cap_binding.py | 10 個站點全部一致；`--selftest` 全部判對 |
| class-closure `controls.py` | 62/62 |
| hook-proof-of-life `controls.py` | 29/29 |
| telemetry-framing `controls.py` | 25/25 |
| entry-schema-lint `controls.py` | 46/46 有 system-hmi；43/46 沒有 |
| hook-deny-lint | 四個控制行為正確；對來源 30 個 hook 掃描，FAIL 0 |
| hook-proof-of-life `pol.py` | 43 個已註冊 hook、39 個不同套件，19 個 FAIL 且以 1 結束；19 個都是不在本資料夾的工具或需要來源私有資料的 hook 自測，本資料夾出貨的每個套件在那一輪裡都通過。來源樹自己跑同一支掃描另有 1 個 FAIL（ui-verify-test 25/26，原因未釐清，見上表該列的限制） |

補充（各驗一次）：ps-errorpref-test、ps-pipeline-close-test、shell-transport-test、ui-verify-test
在本 repo 版面下，對 hooks 管線工作樹中的 hook 檔跑（第一個參數給 hook 路徑），全數通過；
dangerous-command-test、branch-guard-test、model-cap-test 在一份 `hooks/` 取自 hooks 管線、
`agents/` 取自本 repo 的暫存「repo 版面」樹裡，同樣是 80/80、25/25、40/40。ops-health-test 在
路徑含 `CLAUDE_SHARE` 的暫存樹、對 hooks 管線的 hook 版本（含 `tools/tracking-refs/`）跑，是 112/112。

## 已知限制｜Known limits

`check_cap_binding.py` 與上面多數套件用 `os.path.dirname(__file__)` 往上兩層算「repo 根」，再接
`ops/`、`hooks/`。這在**裝進 `~/.claude` 之後**是對的；但本 repo 把來源的 `ops/` 改名成
`claude-ops/ops/`，所以原地執行會找不到 `ops/40-maintenance.md`（`FileNotFoundError`）。這不是
工具的 bug，是安裝後與本 repo 樹狀結構的差異。要在本 repo 樹裡驗證，建一份暫存目錄，把
`claude-ops/ops/`、`hooks/` 各複製成 `ops/`、`hooks/`，工具放進 `tools/NAME/`，從那裡跑。
`fill_gate.py` 沒有這個限制。

另外：**這些套件測的是 hook 的來源版本。** 本 repo 的 `hooks/` 由 manifest 逐檔核對與來源一致
（gate 的 check V），所以 hook 同步之後這裡的數字才是本 repo 版本的數字；同步之前請以來源版為準。

## 去識別化說明｜De-identification notes

依 `tools/COLLECTION-RULES.md` 收錄，每筆編輯登記在 `tools/share-manifest.toml` 的
`[[collected]] edits`。本輪的編輯分五類：

- **帳號名**：fixture 裡的家目錄路徑，帳號段改成單一字元 `x`（保留路徑形狀，守衛判的是形狀）。
- **私有專案路徑**：非系統磁碟上的真實專案目錄，換成虛構的兩層路徑，同一檔內全部位置一致替換。
- **私有指標**：指向來源 `outputs/`、`reports/`、`drafts/`、`references/` 的具名檔案，改成「私有紀錄，
  不隨本分享收錄」，日期與數字保留。
- **session id**：改成「某個本機 session」。
- **模板**：`telemetry-framing/suite-sessions.json` 的 `session_files` 清空，結構不變。

守衛測試**必須含有**它要擋的字面值，所以那類 fixture（虛構的非系統磁碟路徑、一字元佔位樹）不是
去識別化對象，而是以 manifest 的 `[[allow]]` 宣告（理由寫在條目裡）。`test_shadow_hook.py` 還有一處
**來源缺陷**的修補：真實遙測紀錄不存在時（全新安裝）最後一行會 TypeError，副本裡改成容錯，來源未動。

## 與 repo 其他部分的關係｜Repository map

| 你可能在找 | 在哪 |
|---|---|
| 這些工具為什麼出貨、為什麼只有這些、`tools/` 其餘部分為什麼不出貨 | `tools/share-manifest.toml`，`[[not_shipped]] path = "tools/"` 條目，特別是 `USER RULING 2026-09-12` 與 2026-10-02 的段落 |
| page-fill-gate 的完整用法、頁面類別表、量測基準 | `instruments/page-fill-gate/README.md` |
| check_cap_binding.py 守的規則本身 | `claude-ops/ops/40-maintenance.md` §3、`claude-ops/ops/rule-registry.md` |
| hook-deny-lint 守的規則本身 | `global-claude-md/rules/hook-deny-message.md` |
| 被測的 hook | `hooks/`，各 hook 的 docstring 開頭有 STATUS／Proof-of-life 標頭 |

<!-- MAIN: rows for the W5b (method tools) and W5c (system-hmi / view-launcher templates)
     lanes go in a new subsection here, "D. 方法工具與模板｜Method tools and templates",
     using the same column set as section C. Update the counts in the Quick guide table. -->
