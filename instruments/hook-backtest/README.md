---
xi: 1
what: hook-backtest — 把 hook 的判斷函式拿去重播過去所有對話記錄裡的工具呼叫，算出會觸發幾次、各在哪裡，絕不印出指令內容 (shared transcript backtest harness for hooks)
tags: [hook, backtest, transcript, gate, calibration]
aliases: [hook 回測, 回測工具, 上線前回測, hook backtest harness, transcript replay]
layer: instrument
audience: builder
date: 2026-10-03
status: live
---

# hook-backtest

**為什麼有這個**：新 hook 上線前要先拿過去的對話記錄回測 (backtest)，看它在真實資料上會觸發幾次、誤判多少。這條規矩的出處是 `ops/40-maintenance.md` §2a(4)「no baseline yet → backtest first」和 `ops/lessons/L-011.md` 第五型。

之前每次回測都各寫一支腳本，裡面同一段「走訪記錄 → 抽出工具呼叫 → 去重 → 餵給判斷函式」各抄一份：
- `tools/ps-errorpref-backtest/backtest.py`
- `tools/ps-pipeline-close-backtest/backtest.py`
- 2026-10-03 `secret_file_guard` property 2 的回測（只留在 scratchpad，沒提交）

三份抄本的去重鍵 (dedupe key) 與記錄過濾已經不一樣了。抄本一多，數字就不能互相比較。第三份出現，符合「三次才抽共用」(rule of three)，所以抽成這一份。

## 用法

```
python -X utf8 tools/hook-backtest/hook_backtest.py <模組>:<函式>
python -X utf8 tools/hook-backtest/hook_backtest.py adapters:secret_print
python -X utf8 tools/hook-backtest/hook_backtest.py adapters:ps_errorpref --root <快照資料夾>
python -X utf8 tools/hook-backtest/hook_backtest.py 草稿_guard.py:would_fire --tools Bash --dedupe content
python -X utf8 tools/hook-backtest/tests/test_harness.py
```

- `<模組>`：`.py` 路徑，或一個名字。名字先找正在運作的 `~/.claude/hooks/`，再找本資料夾（`adapters.py`）。
- `<函式>(工具名稱, 工具輸入)`：不觸發回傳空值；觸發回傳一個字串（類別名稱）、一個帶 `kind` 的 dict，或任何為真的值（類別記為 `fire`）。
- 常用旗標：`--root`（可重複，預設只有 `~/.claude/projects`；來源版另有一個離線封存目錄，本版已移除，用 `--root` 補）、`--tools`、`--dedupe ts-head|content|none`、`--all-records`、`--json <檔>`。
- 結束碼：0 = 有跑完（不論有沒有觸發）；2 = 沒有任何呼叫符合篩選。第二種情況不能當成「0 次觸發」，因為那只代表這把尺沒碰到資料。

## 輸出：預設不出現指令內容

每次觸發只印五欄：日期、session 前 8 碼、工具、類別、定位 (locator，`專案資料夾/檔名:行號`)。用定位可以回頭打開那次呼叫。

- 要看內容才加 `--excerpt N`。內容會先用 `tools/cred-sweep` 的憑證樣式遮罩，值換成 `<redacted:類別>`。
- 遮罩器載入失敗時，不給內容，只印「withheld」。不會退回原文。
- `--json` 傾印也照同一條規則：只有定位、類別、`tool_use_id`，加了 `--excerpt` 才多一欄遮罩後的摘錄。

## 寫一個新 hook 的回測

1. hook 已有 `(tool, input) -> 判斷` 這種函式：直接 `hook名:函式名`。
2. 沒有（hook 的入口是 `main()` 讀 stdin）：在 `adapters.py` 寫一個轉接函式。
   - 轉接函式只能**組合** hook 匯出的零件，例如 `payload_for`、`analyze`、編譯好的樣式、`MARKER` / `OVERRIDE`。不准抄 regex 或門檻。
   - 函式屬性 `tools` / `dedupe` / `assistant_only` 就是 CLI 預設值。
   - 在 `tests/test_harness.py` 補一個已知會觸發、一個已知不觸發的輸入，對 live hook 跑。
3. 需要更多表格（分母、分層、被壓下的類別）：像兩支 ps 腳本那樣，用 `harness.iter_calls()` 取呼叫，只寫自己的報表。

**轉接函式的殘留風險**：分支的**順序**是在這裡重寫的，例如哪個工具走哪支、哪個逃生標記先檢查。hook 的 `main()` 新增或調換分支時，轉接函式要跟著改。測試裡的成對案例就是用來抓這種脫節。

## 共用的部分（`harness.py`）

| 項目 | 內容 |
|---|---|
| 語料 | 每個 `*.jsonl`，逐行讀，只取 `tool_use` 區塊 |
| 去重 `ts-head` | (時間戳, 工具, 指令或路徑前 400 字)：同一時間的重寫算一次，之後重打算兩次。兩支 ps 回測用這個 |
| 去重 `content` | (工具, 完整指令)：同一個指令形式只算一次。secret 回測用這個 |
| 記錄過濾 | 預設只看 `type: assistant`；`--all-records` 不檢查 |
| 統計 | 檔案數、不同日期數、各工具呼叫數 |
| 註冊狀態 | `registered_tools()` 從 `settings.json` 讀出 hook 實際掛在哪些工具上（推導，不另存一份） |
| 每次呼叫成本 | `MS_PER_CALL = 105`（2026-08-21 實測，幾乎都是 Python 啟動時間） |

hook 一律從正式目錄 `~/.claude/hooks/` 匯入。即使這個工具是在 worktree 裡跑，量的也是正在運作的 hook。

## 移植驗證（2026-10-03）

兩支 ps 回測改成呼叫 harness 之後，在**同一份凍結快照**上比較改前改後。快照做法：`~/.claude/projects` 用 hardlink，近 6 小時有變動的檔實體複製；再加上離線 session 封存目錄（本版不含）。

| 回測 | 改前 | 改後 | 差異 |
|---|---|---|---|
| ps-errorpref 文字輸出 | 27 fires / 119,441 calls | 27 / 119,441 | 只差 `--json` 輸出路徑那一行（刻意不同） |
| ps-errorpref `--json` | 27 筆 | 27 筆 | 逐位元組相同 |
| ps-pipeline-close 文字輸出 | 243 / 119,441 | 243 / 119,441 | 同上，只差路徑行 |
| ps-pipeline-close `--json` | 243 筆 | 243 筆 | 逐位元組相同 |
| 通用 CLI `adapters:ps_errorpref` / `ps_pipeline_close` | — | 27 / 243 | 與上面總數相同 |
| secret property 2（scratchpad 版 → `adapters:secret_print`） | 22 / 78,693 | **21** / 78,693 | 見下 |

secret 差的那 1 筆（一則 2026-08-18 的逐字稿紀錄，定位已省略）：指令同時點名了憑證檔。hook 的 `main()` 會先用 property 1 拒絕，所以 property 2 根本不會被問到。scratchpad 版沒照 `main()` 的順序判斷，把它算成 property 2。

結論：hook 實際拒絕的總數仍是 22；其中 property 2 自己觸發的是 21。

## 已知限制

- 語料會長：跑回測的 session 自己也在寫記錄，所以 `calls` 每跑一次都會往上漂。要比較前後，請用凍結快照，不要比兩次即時結果。
- 只讀 `tool_use` 的輸入，不讀工具結果。要判斷「這次呼叫有沒有成功」的回測，得自己另外讀 `tool_result`。
- 來源版另有兩份記錄來源（一個離線封存目錄、一份含工具呼叫的鏡像），本版都不含；預設只讀 `~/.claude/projects`，要納入別的記錄就加 `--root`。來源版預設不納入鏡像，是為了和既有基準（`ops/rule-registry.md` 裡的數字）保持可比。
