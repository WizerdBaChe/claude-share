# tools/ — 發佈閘門（給維護者讀的操作手冊）

> 機器讀的本體：`share_gate.py`（六道 repo 內檢查 ＋ 一道要掛來源樹的 V）、`sharelib.py`（外洩樣式唯一源）、
> `share-manifest.toml`（唯一的例外宣告處）、`test_share_gate.py`（閘門自身的驗收）。
> 建立於 2026-08-14。

## 為什麼有這層

在這之前，「去識別化 (de-identification) 與資訊防護」是每次推送時口頭指定的。
同一個 repo 因此同時發生了兩種相反的失敗，而且**兩種都不是我們自己發現的**，
是外部採用者 (adopter) 撞上來才知道：

| 失敗類 | 實際發生的事 |
|---|---|
| **過度遮蔽 (over-scrub)** | `interop-layer/README.md` 有 23 處真實、無害、repo-relative 的路徑被換成單一個 `<URL>`；六個不同檔名塌縮成同一個 token，而且其中四處落在**可執行指令區塊裡**，導致整份手冊無法照著跑。 |
| **漏宣告 (under-declare)** | 20+ 份規則檔把 `hooks/model_cap_guard.py`、`hooks/ops_health_nudge.py`、`settings.json` 當成「機械強制」的依據來引用，但 repo 一個都沒附。採用者讀到「這條有機制擋」，拿到的是散文，而且無從分辨。`MIGRATION-MAP.md` 維運原則第 4 條（**降級要留痕**）本來就禁止這件事，只是沒有東西在檢查。 |

兩類現在都是機器判定的。推送時不再需要臨場判斷。

## 日常操作（三個指令）

```powershell
python tools/share_gate.py                        # repo 內六道全跑，有發現就 exit 1
python tools/share_gate.py --check P              # 只跑一道（L / P / R / S / C / D 任選）
python tools/share_gate.py --source ~/.claude     # 再加上 V：逐檔比對來源樹
python tools/test_share_gate.py                   # 驗收閘門本身：10 個案例
```

**推送前一定要跑一次 `share_gate.py`，exit 0 才推。** 它不會自動修任何東西——
自動塗改正是它要防的那件事。

**在「搬東西進來」的時候，一定要加 `--source`。** 沒加就不會跑 V，而 V 是唯一
看得見「宣告過的改動被一次 verbatim 覆蓋洗掉」的東西。2026-08-16 就是這樣一次
掃描讓六個去識別化決定無聲消失，repo 內的六道檢查全部通過——因為它們沒有一道在
比對任何東西。

## 六道 repo 內檢查，加一道要來源樹的

| 代號 | 名稱 | 擋什麼 | 過關的唯一方式 |
|---|---|---|---|
| **L** | leak | email、JWT、有前綴的 API key、secret 形狀的賦值、32 字元以上 hex、**任何帳號**的絕對家目錄路徑、私網 IP | 移除，或在 `[[allow]]` 寫一筆有理由的例外 |
| **P** | placeholder | 佔位符出現在**路徑位置**（緊鄰 `/`）或**指令位置**（行首是 `python`/`git`/`cd`…），以及同一 token 在單一檔案被當獨立值用 ≥4 次 | 還原真實值，或在 `[placeholders]` 宣告該 token |
| **R** | reference | 引用了來源環境的資產（`hooks/…`、`~/.claude/…`、`ops/…`）但 repo 沒附、manifest 也沒宣告 | 在 `[source_map]` 建立對應，或加一筆 `[[not_shipped]]` |
| **S** | structure | 巢狀 `SKILL.md`、缺 `SKILL.md`、clone 後會消失的空目錄、被追蹤的 `.claude/`／`__pycache__/`／`archive/`、技能清單表與實際樹不一致 | 修樹 |
| **C** | collection | 從來源環境搬進來的檔案（`collected_roots` 底下）沒登記出處、沒登記狀態，或狀態不是 `verbatim` 卻沒列出每一處改動 | 補 `[[collected]]` 條目 |
| **D** | dead-declaration | 已經對不上任何東西的宣告：`[[allow]]` 要豁免的那個發現已經不在、`[[not_shipped]]` 說沒出貨的檔案現在出貨了、`[placeholders]` 宣告的 token 全 repo 沒人用 | 刪掉那筆。過期的例外會一直被讀成「有在管」 |
| **V** | source-verify | *（要 `--source`）* 宣告 `verbatim` 卻和來源不一樣、宣告 `edited`/`template` 卻和來源**完全一樣**（＝宣告過的改動不見了）、宣告的來源路徑已不存在 | 重收、補回改動，或改掉那個宣告 |

P 檢查刻意**不**管一般散文模板（`<project name>`、`<title>` 之類，全 repo 約 160 個）。
管全部只會製造噪音而沒有保護；真正危險的只有兩個位置——那才是佔位符可能正藏著
讀者需要的真實值的地方。`<URL>` 事件同時違反 P 的三條規則。

## 要從 `~/.claude` 搬東西進來？

**先讀 [`COLLECTION-RULES.md`](COLLECTION-RULES.md)，不要自己臨場決定去識別化policy。**
那份是給 agent 讀的判定程序：七問決策表、五種判定詞、絕不收錄清單，以及
「先記來源 SHA → 逐字讀完 → 複製 → 對來源 diff → 登記每一處改動 → 跑閘門 →
確認來源沒被動到」的強制步驟。

第三種失敗就是這樣來的：2026-08-14 的來源稽核發現，三支 hook 被寫成
`referenced-only`「綁機器」整整一個月，實際上它們**完全可攜、只是從來沒被撈進來**。
判定一旦寫成散文、沒有東西會重測，它就會爛掉。C 檢查與那份規則就是為此存在。

## manifest 怎麼寫

`share-manifest.toml` 是**唯一**能讓發現通過的地方。三個原則：

1. **每筆都要有理由。** 沒有 `reason` 的 `[[allow]]` 不會生效（程式碼裡就是這樣判的）。
2. **窄勝於寬。** `file` 是精確比對，不接受萬用字元。
3. **`[placeholders]` 加一個 token，等於宣告「有人看過，這確實是讀者要自己填的參數，
   不是被腳本吃掉的真實路徑」。** 如果讀者其實填不出來，正解是還原，不是宣告。

`[[not_shipped]]` 的 `disposition` 只有四種，不要發明第五種：

| disposition | 意思 |
|---|---|
| `upstream-absent` | 來源環境根本沒有這個東西 |
| `referenced-only` | 來源有，但只有**意圖**隨附；從未產出可移植的成品 |
| `excluded-by-decision` | 有具體檔案，刻意不附 |
| `partial` | 只附了一部分 |

每筆都必須寫 `fallback`——採用者實際拿到的是什麼（機制？還是散文？）。
這一欄就是「降級要留痕」的機械化版本。

## 加一道新檢查時

1. 在 `share_gate.py` 寫成一個 `check_*(manifest, files, findings)` 函式，掛進 `CHECKS`。
2. 在 `test_share_gate.py` 加一個會**失敗**的案例——沒有人看過它 FAIL 的閘門不算證據。
3. 跑 `python tools/test_share_gate.py`，確認新案例與既有四案都符合預期。

## 想在 commit 時自動擋

本 repo **不**自動安裝 git hook（那是你機器上的持久設定，屬於你自己的決定）。
要的話自己建 `.git/hooks/pre-push`：

```git bash
#!/bin/sh
python tools/share_gate.py || exit 1
```

## 已知邊界（是設計，不是缺陷）

- **閘門只看得到已被 git 追蹤的檔案。** 還沒 `git add` 的新檔不在範圍內——
  這是刻意的（暫存區的東西還不算要發佈），但也代表「新增檔案後先 add 再跑」。
- **它證明不了語意。** 它能判定「這個 token 站在路徑位置」，判定不了
  「這段描述是否誠實」。`disposition` 與 `fallback` 的內容仍然要人寫、人審。
- **`[[allow]]` 一旦寫寬就等於關掉那一項。** 這是設計上留給人的權力，也是
  唯一一個可以無聲失效的地方；審 PR 時優先看 manifest 的 diff。D 檢查現在會抓
  「豁免的對象已經不存在」，但抓不到「一開始就寫太寬」。
- **V 是選配，而且只對「手上同時有兩棵樹」的人有效。** 採用者沒有來源樹可指，
  所以它預設不跑；它不會靜默跳過——沒下 `--source` 就是沒跑，輸出裡看得出來。
- **V 也證明不了「這次該不該重收」。** 它只回答「檔案和宣告是否一致」。來源自己
  改壞了、而你照抄，V 一樣是綠的。
