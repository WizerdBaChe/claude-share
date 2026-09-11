# instruments — 已出貨規則引用為「強制機制」的可攜驗證工具

> 這個資料夾放兩支工具，不是一套運作模式。來源環境的 `tools/` 整體排除
> （見 `tools/share-manifest.toml` 的 `[[not_shipped]] path = "tools/"`），
> 但這兩支被本 repo **已出貨**的規則檔直接 `import`，或以「Enforcement:」
> 唯一點名為機制——排除到今天，等於留下兩條指向空無一物的活死鏈
> (live dead pointer)。2026-09-12 使用者裁決：只讓這兩支出貨，`tools/`
> 其餘部分維持排除。證據見該 `not_shipped` 條目的
> `USER RULING 2026-09-12` 段落。

## 收錄標準 (admission criterion)

四個條件同時成立才收：

1. 本 repo **已出貨**的檔案**執行、import，或以「Enforcement:」點名**它
   作為機制——不是背景色、不是「將來可能會用到」。
2. 只用標準庫 (stdlib-only)。
3. 自帶校準：跑一次就同時驗一個 known-TRUE 與至少一個 known-FALSE／已知好壞
   對照組（見下表最後一欄）——一支只回報過乾淨結果的檢查器，其 100% 通過率
   本身就是要先懷疑的紅旗。
4. 不依賴來源環境的私有樹（不讀 `memory/`、`projects/`、
   `references/<project>-*` 之類）。

**明確不收的類別，附理由：**

- **Hook 自己的回歸測試套件**（`*-test/` 一類，例如
  `tools/ops-health-test/` 裡剩下的 `test_ops_health_nudge.py`）——這是那支
  hook 開發時的附屬品，測的是「這支 hook 本身對不對」，不是「一份交付物對不
  對」；讀者不需要它就能用這兩支工具。
- **任何對私有樹建索引的工具**（`graph-snapshot`、`version-census`、
  `rule-usage-census`、`copy-census`、`class-closure`）——條件 4 不成立：
  離開來源環境自己的目錄結構，這些工具沒有東西可查，收錄了也是空殼。

## 每支工具

| 工具 | 檢查什麼 | 哪個已出貨檔案引用它 | 怎麼跑 | 自帶校準 |
|---|---|---|---|---|
| `page-fill-gate/fill_gate.py` | 人讀 HTML 有沒有留下不對稱右側空白（具名缺陷：靠左錨定上限 left-anchored cap）；每頁該填多少由 `page_classes.json` 的類別列決定，不是程式分支 | `claude-ops/ops/environment.md`（§Display，"Enforcement:" 一行）、`claude-ops/ops/rule-registry.md`、`claude-ops/ops/references/uat.md`、`claude-ops/ops/lessons.md`（L-048）、`skill-toolkit/skills/ux-walkthrough/SKILL.md` | `python tools/page-fill-gate/fill_gate.py <built.html> [--class X]`（裝到 `~/.claude` 後從那裡跑；也可以在任何目錄下用完整或相對路徑呼叫，見下「已知限制」） | 每次執行先跑 `fixtures/known-bad-left-cap.html`（必須 FAIL）與 `fixtures/known-good-fill.html`（必須 PASS）；任一沒觸發，整次判為無效並丟 `RuntimeError`，不給出任何頁面的判決 |
| `ops-health-test/check_cap_binding.py` | sweep check 7b：同一個 cap 數值常數，在 `hooks/ops_health_nudge.py`（機制）與 `ops/40-maintenance.md`／`ops/rule-registry.md`（規則文字）兩邊是否一致（DRIFT）、或規則文字的錨點還找不找得到（ANCHOR LOST） | `hooks/ops_health_nudge.py`（docstring 點名為 "TEST SEAM"）、`claude-ops/ops/references/integrity-sweep.md`（check 7b，直接 `import hook_caps`）、`claude-ops/ops/40-maintenance.md`、`claude-ops/ops/rule-registry.md` | `python tools/ops-health-test/check_cap_binding.py`（見下「已知限制」——路徑是相對自己算出來的，裝到哪裡跑才對很重要） | `--selftest`：一組 known-TRUE（五個常數全部一致 → 必須回報乾淨）＋四組 known-FALSE（規則文字值漂移、docstring 復述了數值、規則段落標題改名讓錨點找不到、常數整個從機制刪掉），五案例都要判對才算通過 |

## 安裝

複製 `instruments/<x>/` 整個資料夾到 `~/.claude/tools/<x>/`。子路徑刻意跟來源
環境一致，所以已出貨規則檔裡原封不動的引用——`tools/page-fill-gate/...`、
`tools/ops-health-test/check_cap_binding.py`——裝完就直接解析得到。

- `page-fill-gate` 另外需要 `pip install playwright` 加
  `playwright install chromium`（實際的頁面量測用 Playwright 開一個無頭
  Chromium）；用法細節見它自己的 `page-fill-gate/README.md`。
- `check_cap_binding.py` 只用標準庫（`ast`／`os`／`re`／`sys`），裝完即可跑，
  不需要額外安裝。

## 已知限制（附實測結果，2026-09-12）

`check_cap_binding.py` 用 `os.path.dirname(__file__)` 往上兩層算「repo 根」，
再接 `ops/40-maintenance.md`、`ops/rule-registry.md`、
`hooks/ops_health_nudge.py`。這在**裝進 `~/.claude` 之後**是對的——那三個
都在同一個根目錄下一層。但這個 share repo 自己的目錄結構把來源的 `ops/`
改名成 `claude-ops/ops/`，所以直接在**這個 repo 自己的樹裡原地跑**
（`python instruments/ops-health-test/check_cap_binding.py`）會找不到檔案：

```
FileNotFoundError: [Errno 2] No such file or directory:
'...\ops\40-maintenance.md'
```

（本輪實測，於本 repo worktree 根目錄執行，訊息逐字重現，未改動任何檔案。）
這不是這支工具的 bug——它本來就是為了裝進 `~/.claude` 而寫的路徑假設；只是
這個 share repo 自己的樹狀結構跟安裝後的樹狀結構不同。要在本 repo 自己的樹
裡驗證這支工具，建一份暫存目錄，把 `claude-ops/ops/`、`hooks/` 分別複製成
`ops/`、`hooks/` 兩個平行目錄，工具本體放進 `tools/ops-health-test/`，從那個
暫存目錄跑（下面「已於本 repo 驗證」用的就是這個作法）。

`fill_gate.py` 沒有這個限制：它只用自己旁邊的 `page_classes.json` 與
`fixtures/`（`HERE = pathlib.Path(__file__).resolve().parent`），不假設任何
repo 根目錄結構，在這個 repo 的樹裡原地跑就是對的。

## 已於本 repo 驗證

- `python instruments/page-fill-gate/tests/test_fill_gate.py` —— 15 個案例、
  兩個對照組全部判對（PASS）。
- `python instruments/page-fill-gate/fill_gate.py architecture-diagramming/capability-set.html` ——
  0 FAIL / 3 WARN：三個 viewport 都因為該頁沒宣告 `data-page-class` 被判
  INFERRED，判決依規則降級為 WARN（不是 FAIL），對照組照常一 FAIL 一 PASS。
  沒有 FAIL，本輪未因此改動該 html。
- `python tools/ops-health-test/check_cap_binding.py` 與 `--selftest`：來源
  環境直接跑一次（10 個站點核對，全部一致；五個 selftest 案例全部判對）；
  另在一份模擬「裝進 `~/.claude`」樹狀結構的暫存目錄裡重跑一次主檢查，
  同樣是 10 個站點、全部一致——確認裝對位置就能用，不需要修改這支工具本身。

## 去識別化說明 (de-identification notes)

依 `tools/COLLECTION-RULES.md` 收錄，每筆編輯登記在 `tools/share-manifest.toml`
的 `[[collected]] edits`。讀者會注意到的兩處，都在 `page-fill-gate/README.md`
裡：一行 owner/status 說明原本指向來源環境 `outputs/` 樹下一份寬度缺陷診斷
筆記的路徑（`outputs/` 不隨本分享收錄）——保留「有這份使用者裁決診斷」這件
事，拿掉指不到東西的路徑；兩行用法範例原本寫著這支工具在來源機器上的絕對
安裝路徑（含帳號名）——換成這個 repo 其他地方（例如
`claude-ops/ops/environment.md`）已經在用、未經編輯的 repo 相對路徑形式，
字面不同、指的是同一支工具同一種呼叫方式。`fill_gate.py`、
`page_classes.json`、兩個 fixture html、`test_fill_gate.py`、
`check_cap_binding.py` 六個檔案逐位元組核對過，與來源完全一致，未作任何編輯。

## 與這個 repo 其他部分的關係

| 你可能在找 | 在哪 |
|---|---|
| 這兩支工具為什麼出貨、為什麼只有這兩支、`tools/` 其餘部分為什麼不出貨 | `tools/share-manifest.toml`，`[[not_shipped]] path = "tools/"` 條目，特別是 `USER RULING 2026-09-12` 段落 |
| page-fill-gate 的完整用法、頁面類別表、量測基準數據 | `instruments/page-fill-gate/README.md` |
| check_cap_binding.py 守的規則本身（cap 常數表、各站點現行值） | `claude-ops/ops/40-maintenance.md` §3、`claude-ops/ops/rule-registry.md` |
| 這兩支工具收錄前的逐工具評估（33 個候選路徑）結論 | 同一個 `[[not_shipped]] path = "tools/"` 條目的 `PER-FILE RE-CHECK 2026-09-12` 段落（逐工具的工作表是本輪的內部文件，不公開） |
