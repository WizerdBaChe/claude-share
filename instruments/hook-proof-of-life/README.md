---
xi: 1
what: 執行每個已註冊 hook 自己宣告的存活證明 (runs the proof-of-life suite each registered hook declares in its own docstring)
tags: [tools, hooks, proof-of-life, gate, PH-11, AP-63]
aliases: [hook 存活證明, proof-of-life, pol.py, hook 有沒有還活著]
date: 2026-09-08
status: live
---

# hook-proof-of-life

Status: live 2026-09-08 ｜ severity: FAIL 當已宣告的對照套件失敗、或宣告讀不出來；
WARN 當一個 hook 什麼都沒宣告（消費者＝讀 sweep 的人／模型）｜ controls:
`controls.py`（雙側，最後一行 `ALL PASS n/n`）｜ wired: `ops/references/integrity-sweep.md` 檢查 31。

## 為什麼存在

`PHILOSOPHY.md` §一.11／`ops/references/principle-design-guide.md` **AP-63**：
機制需要的是**復發的**存活證明，不是出生時那一次。**被 sweep 具名不等於被 sweep 執行。**

實測案例：`hooks/unattended_run.py` 呼叫了 `_receipt()` 卻沒 import 它——每一次
scope deny、每一次 stop block 都拋 `NameError`，而**崩潰的 hook 等於放行**，離線 run
的兩個守衛整整一天是空的。它的對照套件一直都在，跑下去也立刻會過；只是沒有東西去跑它。

所以這支工具**執行**套件，而不是列出它們。

## 用法

```powershell
python tools/hook-proof-of-life/pol.py            # 執行所有已宣告的套件（約 5 分鐘）
python tools/hook-proof-of-life/pol.py --list     # 只分類，不執行（秒級，sweep 第一趟用）
python tools/hook-proof-of-life/controls.py       # 校準；最後一行 ALL PASS n/n
```

離開碼：任何已宣告套件失敗、或任何宣告讀不出來 → 1；否則 0。**沒有宣告不會讓它變紅**，
只會被具名列出——不能決定的事就不下判決（downgrade-and-forward，不是 veto）。

## 宣告寫在 hook 自己的 docstring（AP-61）

```
Proof-of-life: `python tools/<x>/controls.py`      <- executable，會被執行
Proof-of-life: `python hooks/<x>.py --selftest`    <- executable
Proof-of-life: integrity-sweep check 21            <- manual，會被列出但永不算作證明
```

**新增覆蓋率只要在該 hook 的 docstring 加這一行**，這個目錄裡不需要維護任何清單。
一個 hook 可以有多個 `Proof-of-life:` 標記——**最強的那個勝出**（executable > manual >
undetermined），因為若取「第一個」，類別就取決於一段會成長的文字裡的位置，那正是 AP-45
指名的缺陷（`session_board_register.py` 就有兩個標記，舊的指向 sweep 檢查、新的指向套件）。

## 類別（列舉且封閉，AP-62）

| 類別 | 意義 |
|---|---|
| `executable` | 宣告了可執行指令；本工具實際執行它 |
| `manual` | 只指向一個 sweep 檢查；列出，但**永不**算作證明 |
| `uncovered` | 完全沒有 `Proof-of-life:` 行 |
| `undetermined` | 檔案讀不到／解析不了，或宣告了但找不到可執行指令 |

`undetermined` **絕不**併入 `uncovered`：「沒人寫下來」和「我看不了」是兩種不同的發現，
合併它們正是「數字看起來合理但沒有意義」的來源。

## 基線 2026-09-08

**建立時**：29 個已註冊 hook，`executable` 19 ／ `manual` 2 ／ `uncovered` 8 ／
`undetermined` 0。建立這支工具之前只有 3 個 hook 宣告了可執行的證明；其餘 16 個的套件
**早就存在**，缺的只是那一行宣告——這就是「偵測是事件綁定、修復是注意力綁定」的具體樣子。

**同日補完三個機器級執法者之後**：`executable` 22 ／ `manual` 2 ／ `uncovered` 5 ／
`undetermined` 0，0 FAIL，全跑 **508 秒**（18 個不重複套件）。新增的三套：
`tools/branch-guard-test/` · `tools/dangerous-command-test/` · `tools/model-cap-test/`，
每一套都做過雙向變異測試（讓 hook 永不拒絕、讓 hook 全部拒絕；6 個變異體，6 個被抓到）
——沒失敗過的套件，不能算「已知在量測」。

仍然 `uncovered` 的 5 個（真的沒有對照套件，不是漏寫宣告）：
`appdata_view_guard` · `extdispatch_entrypoint_guard` · `instructions_loaded_logger` ·
`project_registry_gist` · `xi_card_guard`。

**同日稍晚，補完最後五套之後（現行基線）**：`executable` **29** ／ `manual` 0 ／
`uncovered` 0 ／ `undetermined` 0，0 FAIL，25 個不重複套件跑 **57 秒**。
`appdata_view_guard`（本來就有 `--selftest`）與 `xi_card_guard`（套件已存在於
`hooks/tests/`）只是補上宣告行；其餘三個是新寫的：`browser_pane_scope_guard` ·
`fieldwork_threshold_notice` · `extdispatch_entrypoint_guard` ·
`instructions_loaded_logger` · `project_registry_gist`（皆在 `hooks/tests/`）。

`uncovered` 於此刻**由 WARN 升為 FAIL**——這是 check 31 事先寫下的升級條件
（「uncovered 歸零就升級」），不是事後追認。`manual` 維持 WARN：「被點名但沒被跑」
比「什麼都沒有」是較弱的發現。

**508 秒那個數字是錯的**，一併更正：它是在三個 sweep 同時跑的時候量的，當時卻被記成
「在閒置機器上量測」。單獨重量：ops-health 8.0 秒、closeout-intake 5.3 秒、全跑 57 秒。
`TIMEOUT = 420` **不因此調低**——它保護的正是那個被塞爆的情境。

**第一次真實執行就抓到兩件事**（這是它存在的理由，不是巧合）：
`test_session_board_register.py` 的 H7/H8 在閒置機器上會紅——那是情境未發生，不是 hook
壞掉，已改為 exit 3 `inconclusive`；`tools/compact-loss-audit/hook_controls.py` 印
`29 / 30 passed` 卻回傳 0，而那個 C1 從寫下的隔天就一直是紅的（夾具把摘要時間戳寫死在
2026-09-05，壓縮列卻是執行當下的時間）。

## review-when

- `settings.json` 的 hook command 形狀改變（`hooks/<name>.py` 正則不再命中）→
  `registered_hooks()` 會變瞎；controls 的 C-08 只證明讀不到時不會假 PASS，**不會**
  抓到這個，harness 升級後要重看。
- 任何套件的執行時間超過 `TIMEOUT`（420 s，取自**負載下**最慢者 ops-health 106.6 s 的
  四倍餘裕；閒置時同一套只要 8.0 s）→
  判為 `inconclusive` 而**非** FAIL：套件沒跑到判決，這支工具也就沒有判決。看到
  `[INCONCLUSIVE]` 先單獨重跑那一套再相信它。
- 全跑時間逼近 15 分鐘 → 拆分（例如只跑 git 動過的 hook），而不是讓它默默不再被執行。
  跑不起的存活證明會退化成沒人跑的存活證明，那正是 AP-63 要防的失敗。
- `uncovered` 降到 0 → 把 AP-63 的 `detect:` 從候選升級為本檢查，並考慮讓 WARN 升為 FAIL。
- **同時跑多份 sweep 會製造假紅**（實測 2026-09-08：三份並跑，兩套被餓死超時，報告點名了
  無辜的 hook）。這支工具要單獨跑。
