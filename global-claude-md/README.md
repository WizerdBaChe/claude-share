# Global CLAUDE.md Snapshot

這個資料夾是個人 `~/.claude/CLAUDE.md`（Claude Code 的全域指令入口，套用到所有專案）的手動快照，供參考或移植到其他機器使用。

## 內容

- `CLAUDE.md`：全域工作偏好設定，涵蓋 Git 工作流程、環境語法慣例、互動風格、工程判斷準則、技能路由、專案作業層級、檔案整理慣例、以及回覆語言規則。每條規則都標註了觸發情境（applies only when...），非情境內時應完全忽略、不主動提及。開頭有一段「Path-scoped rules」索引，指到下面 `rules/` 資料夾。
- `rules/`：2026-08-11 新增。兩條原本內嵌在 `CLAUDE.md` 裡的規則被搬出來,改成只在讀到對應副檔名檔案時才載入的 `paths:`-scoped 規則檔——`frontend-layering.md`（FSD 分層）與 `shader-failure-modes.md`（GLSL 靜默失敗模式）。搬出來的理由：這兩條規則的觸發條件是「正在碰某種檔案」，`paths:` frontmatter 能直接對應這個觸發形狀,搬出去後**每個 session 啟動都不用再付它們的位元組成本**,只有真的讀到符合的檔案時才載入。要在自己的環境生效,必須放在對應機制存在的位置(Claude Code 是 `~/.claude/rules/`);若目標環境沒有等效的 path-scoped 規則機制,把這兩條規則的內容併回 `CLAUDE.md` 本體即可,只是會变回「每 session 都付費」。

## 去識別化 — 以及為什麼大部分路徑「原樣保留」

原始檔案本身未包含使用者名稱、電子郵件或帳號等個資。逐項檢查後只有一處真正屬於機器綁定資訊，其餘引用其實是可攜路徑，不需要泛化成佔位符：

- **真正機器綁定、已改為佔位符**：「Environment」小節原文寫死「本機是 Windows 11、只用 PowerShell 5.1、換行為 CRLF」——這是單一機器的環境事實，不具可攜性。已替換為 `<OS_NAME>` / `<SHELL_NAME_AND_VERSION>` / `<LINE_ENDING_CONVENTION>` 三個佔位符，並保留原始設定作為行內註解，供對照。
- **`~/.claude/ops/*.md`、`~/.claude/skill-trigger-dict.md` 等路徑——刻意保留原樣，不改成佔位符**：`~` 在任何機器上都會展開成當前使用者的家目錄，本身就是可攜寫法，不會洩漏使用者名稱；把它硬改成 `<OPS_DIR>` 之類的抽象佔位符反而模糊了「這條路徑其實有明確、可直接使用的預設值」這件事。這些路徑對應到**本 repo 已經附贈的內容**：

  | CLAUDE.md 內的路徑 | 對應到本 repo 的哪裡 | 要能生效，需先放到 |
  |---|---|---|
  | `~/.claude/ops/*.md`（`05-authority.md`、`30-judgment.md`、`OPS.md`、`rules-usage-dict.md`、`60-bootstrap.md` 等） | [`claude-ops/ops/`](../claude-ops/ops/) | 目標機器的 `~/.claude/ops/` |
  | `~/.claude/skill-trigger-dict.md` | [`skill-toolkit/skill-trigger-dict.md`](../skill-toolkit/skill-trigger-dict.md) | 目標機器的 `~/.claude/skill-trigger-dict.md` |

  換句話說：這份 `CLAUDE.md` 不是孤立文件，而是與本 repo 的 `claude-ops/` 和 `skill-toolkit/` **同一套環境的三個切片**，路徑寫法在設計上就是假設三者會被放在同一台機器的 `~/.claude/` 下。單獨只拿這份 `CLAUDE.md` 也能讀、能理解每條規則，但要讓上表那些引用真的可以被讀到，需要一併採用另外兩個分享（見下方「使用方式」）。

## 使用方式

這是可讀取的參考快照，不是自動同步來源。

**只想讀規則本身**：直接看 `CLAUDE.md`，每條規則的觸發情境與內容都是自足的，不需要另外兩個分享也能看懂。

**想在新機器上完整採用**（讓 `~/.claude/ops/...`、`~/.claude/skill-trigger-dict.md` 這些引用真正生效）：

1. 複製 `CLAUDE.md` 到目標環境的 `~/.claude/CLAUDE.md`。
2. 依「去識別化」表格，把 [`claude-ops/ops/`](../claude-ops/ops/) 複製到 `~/.claude/ops/`，把 [`skill-toolkit/skill-trigger-dict.md`](../skill-toolkit/skill-trigger-dict.md) 複製到 `~/.claude/skill-trigger-dict.md`。
3. 把「Environment」小節的 `<OS_NAME>` / `<SHELL_NAME_AND_VERSION>` / `<LINE_ENDING_CONVENTION>` 三個佔位符換成該機器實際的 OS/shell/換行慣例。
4. 「Language」小節按自己的回覆語言偏好調整或刪除（這條反映的是原作者個人偏好，不是通用建議）。
5. 若也想要 `skill-toolkit/` 裡實際的技能檔案（`~/.claude/skills/`），另外參考 `skill-toolkit/README.md` 的安裝說明。
6. 把 `rules/frontend-layering.md`、`rules/shader-failure-modes.md` 複製到目標機器的 `~/.claude/rules/`，才能讓 `CLAUDE.md` 開頭的 path-scoped 索引真的指到活的檔案。若目標環境沒有等效機制，直接把這兩份檔案的規則內容併回 `CLAUDE.md` 也可以。
7. 其餘規則（Git 工作流程、互動風格、工程判斷準則、檔案整理慣例）與機器/帳號無關，可直接沿用。

## 快照細節

- 來源：`~/.claude/CLAUDE.md`，複製於 2026-08-02；refreshed 2026-08-06、2026-08-11。
- 檢查範圍：使用者名稱、電子郵件、帳號、機器綁定的 OS/shell/路徑資訊。
- 結果：檔案本身無使用者個資；「Environment」小節的機器綁定設定（Windows 11 + PowerShell 5.1 + CRLF）已改為佔位符。`~/.claude/ops/*` 與 `~/.claude/skill-trigger-dict.md` 引用判定為可攜路徑（`~` 不含使用者名稱），故原樣保留，並在本 README 補上與本 repo `claude-ops/`、`skill-toolkit/` 的對應表，取代原先過度抽象化的 `<OPS_DIR>` 寫法。
- 2026-08-11 refresh：新增 path-scoped rules 索引行與 `rules/` 資料夾（兩條規則從 `CLAUDE.md` 本體搬出）；瀏覽器面板 UI 驗證那條規則改寫為「hook-enforced where the environment provides such a hook」，並附加行內註解說明原文額外指名一支 PreToolUse hook；relaxation gate 那條加了一則「Opus 主迴圈模型 = L1」的 standing ruling（附註解說明這是原作者自己的授權裁定，非泛用建議）；移除的 `## Architecture`（FSD）小節內容原樣搬進新的 `rules/frontend-layering.md`；GLSL 靜默失敗模式的括號子句搬進新的 `rules/shader-failure-modes.md`。無新增個資。
- 這是時間點快照，不是自動同步目標。

## 授權

本資料夾隨母專案採用 [MIT License](../LICENSE)。
