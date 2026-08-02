# Global CLAUDE.md Snapshot

這個資料夾是個人 `~/.claude/CLAUDE.md`（Claude Code 的全域指令入口，套用到所有專案）的手動快照，供參考或移植到其他機器使用。

## 內容

- `CLAUDE.md`：全域工作偏好設定，涵蓋 Git 工作流程、環境語法慣例、互動風格、工程判斷準則、前端分層架構（FSD）、技能路由、專案作業層級、檔案整理慣例、以及回覆語言規則。每條規則都標註了觸發情境（applies only when...），非情境內時應完全忽略、不主動提及。

## 去識別化

原始檔案本身未包含使用者名稱、電子郵件或帳號等個資，唯一需要處理的是**機器綁定資訊**：

- 「Environment」小節原文寫死「本機是 Windows 11、只用 PowerShell 5.1、換行為 CRLF」——這是單一機器的環境事實，不具可攜性。已替換為 `<OS_NAME>` / `<SHELL_NAME_AND_VERSION>` / `<LINE_ENDING_CONVENTION>` 三個佔位符，並保留原始設定作為行內註解，供對照。
- 「Project operations」「Engineering judgement」「Skill routing」小節中對 `~/.claude/ops/*.md` 與 `~/.claude/skill-trigger-dict.md` 的引用，已改寫為通用佔位符 `<OPS_DIR>` 與 `<SKILL_TRIGGER_DICT_PATH>`。這些引用在來源環境中對應本repo的 [`claude-ops/`](../claude-ops/) 與 [`skill-toolkit/skill-trigger-dict.md`](../skill-toolkit/skill-trigger-dict.md)——若要讓這份 CLAUDE.md 在新環境中完整運作，建議連同這兩個分享一併採用，並將佔位符換成實際路徑。
- 「Language」小節保留了原作者「對話一律用繁體中文回覆」的個人偏好，並加註說明可依採用者自身語言慣例替換或整段刪除。

## 使用方式

這是可讀取的參考快照，不是自動同步來源。若要在新機器或新 Claude Code 環境採用：

1. 複製 `CLAUDE.md` 到目標環境的 `~/.claude/CLAUDE.md`（或對應的全域指令位置）。
2. 依上方「去識別化」列出的佔位符，填入該機器實際的 OS/shell/換行慣例。
3. 若要讓 `<OPS_DIR>` 與 `<SKILL_TRIGGER_DICT_PATH>` 引用生效，一併採用 [`claude-ops/`](../claude-ops/) 與 [`skill-toolkit/`](../skill-toolkit/)，並更新路徑。
4. 「Language」小節按自己的回覆語言偏好調整或刪除。
5. 其餘規則（Git 工作流程、互動風格、工程判斷準則、FSD 架構、檔案整理慣例）與機器/帳號無關，可直接沿用。

## 快照細節

- 來源：`~/.claude/CLAUDE.md`，複製於 2026-08-02。
- 檢查範圍：使用者名稱、電子郵件、帳號、機器綁定的 OS/shell/路徑資訊。
- 結果：檔案本身無使用者個資；「Environment」小節的機器綁定設定（Windows 11 + PowerShell 5.1 + CRLF）已改為佔位符；跨檔引用（`~/.claude/ops/*`、`~/.claude/skill-trigger-dict.md`）已改為通用佔位符並在本 README 中說明對應關係。
- 這是時間點快照，不是自動同步目標。

## 授權

本資料夾隨母專案採用 [MIT License](../LICENSE)。
