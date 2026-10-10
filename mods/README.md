# mods — Claude Code 外掛（mod）的程式碼本體｜Claude Code mods, as code

> **English summary**: Two Claude Code mods (in-process plugins, CC 2.1.287+) collected from
> the source environment. `model-cap-mod` is the in-process subagent model cost cap;
> `feedback-observer` is an observe-only side check that feeds the feedback pool in shadow
> mode. Both run from a plugin directory with no source machine; both come with tests that
> need only the `claude` CLI. A third mod, `pending-items`, is not shipped.

2026-10-10 新增的根目錄。其他資料夾放的是規則與 hook 的文字與 Python 程式；這裡放的是
**用 TypeScript 寫、由 Claude Code 引擎在行程內載入**的 mod，因此 hook 逾時不會變成放行。

## 收了什麼｜What is here

| mod | 做什麼 | 對應的規則／工具 |
|---|---|---|
| `model-cap-mod/` | 在 `agent.spawn` 同步擋下 opus／fable 的子代理派工，並在子代理第一個 step 判**引擎解析後**的模型，超過上限就不送請求；每次派工寫一列紀錄。 | 鏡像 `hooks/model_cap_guard.py`；測試套件 `instruments/model-cap-test/`；deny 文字形狀見 `global-claude-md/rules/hook-deny-message.md` |
| `feedback-observer/` | 有份量的回合結束與收工時，用 sonnet（medium）讀剛才的對話節錄，找出子系統被繞過／誤擋／漏用的地方，寫成回饋池的感測來源 S-8。**shadow**：只記錄、不計入 due 門檻，不寫進主模型的 context。 | `instruments/feedback-pool/`（`feedback.py report` 讀它的紀錄）；`judge.py` 記使用者的逐則判定 |

## 怎麼裝｜Install

1. 需要 Claude Code 2.1.287 以上（mod 支援）。
2. 把要用的資料夾放進你的 `~/.claude/mods/`，在 `settings.json` 的 `env.CLAUDE_CODE_PLUGIN_DIRS`
   列出路徑（多個以 `;` 分隔；Desktop 啟動的 session 讀 user settings 的 env 區塊）。
3. 驗證：`claude plugin validate mods/<名稱>`、`claude plugin test mods/<名稱>`。
   本 repo 內已實測：`model-cap-mod` 11/11、`feedback-observer` 24/24；測試不需要來源端，
   只用到 `claude` CLI（收錄時的 2.1.295）。

`model-cap-mod` 的 README 描述它與 `hooks/model_cap_guard.py` 的分工（心跳檔 `telemetry/model-cap-mod-alive.json`）：
沒載入 mod 的 session 不會比只有 Python hook 時更鬆。兩份 `BLOCKED`／`WITHIN_CAP` 清單各存一份，
加 family 要兩邊都改（README「漂移點」）。

## 沒出貨的部分｜What is not here

- **`pending-items`**（側欄列出「待續事項」的 mod）：它執行來源端的個人工具 `tools/pending-items/pending.py`，
  讀的是操作者自己的待辦紀錄，沒有該工具就是一個空窗格。`share-manifest.toml` 的 `[[not_shipped]]` 有理由。
- **`feedback-observer/calibration/` 的校準資料**（兩份對話節錄 fixture、期望檔、上次校準的輸出）：
  是真實對話的節錄，含操作者的專案與路徑，不能公開。`make_fixture.py` 有出貨——
  用它從你自己的 transcript 切出 fixture，`/fo-calibrate` 就能對你的資料跑 prompt。沒有 fixture 時
  `/fo-calibrate` 回報 0/0，其餘功能不受影響。
- 兩個 mod 的 README 提到的上線審查工具 `tools/mod-review/`（產生審查紀錄）屬來源端的 `tools/`，不隨包出貨；
  上面兩條 `claude plugin` 指令就是本 repo 內可跑的驗證。
- 兩個 mod 的 README 與程式註解引用的**設計正本、建置日誌、評估報告**（`references/…`、`reports/…`）留在來源端，
  不隨包出貨；規則編號（FO-INV-n、FO-R-n）與裁決日期保留，供有來源端的人對照。

## 去識別化｜De-identification

逐檔的編輯清單在 `tools/share-manifest.toml`（`mods/` 的 `[[collected]]` 條目）。類別：一個 home 路徑改為 `~/` 寫法、
一個 session 識別碼與一條非系統磁碟上的探測紀錄指標移除（敘述保留）、一個註解範例中的帳號名改為 `you`、
一個測試用的假 session id 改為非 UUID 形狀。
