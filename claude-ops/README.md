# Claude Ops Snapshot｜作業規範快照

> **中文摘要｜Chinese summary**：這是個人 `~/.claude/ops/` 作業規範的手動快照，
> 用來閱讀、挑選可重用的工作流程，或在 Claude Code 環境中採用。它保留 Claude
> 路徑與交叉引用；要搬到 Codex／ChatGPT，請改讀
> [`../interop-layer/README.md`](../interop-layer/README.md)，不要直接複製這層的路徑。
>
> **English summary**: This is a reviewed snapshot of a personal `~/.claude/ops/`
> rules layer. It is suitable for reading and selective adoption in Claude Code.
> Its paths and cross-references are Claude-specific; use the interop layer for
> Codex or ChatGPT migration instead of copying this directory verbatim.

## 快速導覽｜Quick guide

| 項目 | 中文 | English |
|---|---|---|
| 主要用途 | 讀作業規則、派工、維護與啟動流程 | Read operational rules, dispatch, maintenance, and bootstrap workflows |
| 先讀 | [`ops/OPS.md`](ops/OPS.md) 是規則入口與 routing table | `ops/OPS.md` is the entry point and routing table |
| 採用前 | 先看路徑對照，再依 `hooks/README.md` 與 manifest 檢查缺件 | Read the path map, then check hooks and manifest for missing pieces |
| 不直接搬移 | `~/.claude/ops/` 是 Claude 的 host contract，不是 Codex／ChatGPT package | `~/.claude/ops/` is a Claude host contract, not a Codex/ChatGPT package |

## 內容｜Contents

- `ops/`：權限、命令迴圈、任務派送、判斷、維護、教練、啟動與演進等作業規範。
- `ops/environment.md`：擷取時的工具環境與模型成本上限紀錄。
- `ops/OPS.md`：各規範文件的入口與使用索引。
- `ops/references/`：規範背後的細節檔（integrity-sweep 檢查清單、entry-schema、
  gate-design、maintenance-cases、harness-measurements 量測帳等，共 14 份；
  `harness-measurements.md` 自 2026-10-02 起隨附，是 `environment.md` 各段
  事實背後的量測紀錄）。
- `ops/lessons.md`：踩坑索引（generated index）的快照，2026-10-02 對齊 source
  的 134 筆；每筆 `Record:` 指向的 `ops/lessons/` 逐筆紀錄樹**不**隨附。
- `ops/rule-registry.md`：規則登記簿；凡引用未隨附工具之處都附有 `Share note`。

## 路徑對照｜Path map (read before adoption)

`ops/` 底下的檔案彼此以 `~/.claude/ops/...` 互相引用，而且**刻意保留原樣**——
`~` 在任何機器上都會展開成當前使用者的家目錄，不含帳號名，本身就是可攜寫法。
但這也代表：這批規則預設自己被放在 `~/.claude/ops/`。放到別的位置（例如
`~/.codex/ops/`）時，交叉引用不會自動跟著改。

| 規則檔內寫的路徑 | 在本 repo 的位置 | 要生效需放到 |
|---|---|---|
| `~/.claude/ops/*.md` | [`claude-ops/ops/`](ops/) | 目標機器的 `~/.claude/ops/` |
| `~/.claude/CLAUDE.md` | [`../global-claude-md/CLAUDE.md`](../global-claude-md/CLAUDE.md) | 目標機器的 `~/.claude/CLAUDE.md` |
| `~/.claude/skill-trigger-dict.md` | [`../skill-toolkit/skill-trigger-dict.md`](../skill-toolkit/skill-trigger-dict.md) | 目標機器的 `~/.claude/skill-trigger-dict.md` |
| `~/.claude/PHILOSOPHY.md` | [`../environment-guide/PHILOSOPHY.md`](../environment-guide/PHILOSOPHY.md) | 目標機器的 `~/.claude/PHILOSOPHY.md` |
| `hooks/*.py` | [`../hooks/`](../hooks/)（歷次 refresh 已更新；目前掛載數與共用函式庫狀態以 [`../hooks/README.md`](../hooks/README.md) 為準） | 目標機器的 `~/.claude/hooks/` + 掛載設定 |
| `agents/*.md` | [`../agents/`](../agents/)（目前 9 支，以該層 README 為準） | 目標機器的 `~/.claude/agents/` |
| `~/.claude/references/PROJECTS.md` | [`references/PROJECTS.md`](references/PROJECTS.md)（只有格式，沒有資料列；2026-10-02 起含 `predecessor` 欄與 USER-PROFILE 前置規則） | 目標機器的 `~/.claude/references/PROJECTS.md` |
| `settings.json` | [`../hooks/settings.example.json`](../hooks/settings.example.json)（範本） | 併進你自己的 `settings.json` |

**2026-08-14 更正**：這段原本寫「規則檔說『由 hook 機械強制』的地方，你拿到的是散文」。
那是因為 hook 從來沒被撈進來，而 manifest 把原因誤判成「綁機器」。查證結果是七支
hook 完全可攜，現已隨附——所以**強制力不再是降級的**，只要你照
[`../hooks/README.md`](../hooks/README.md) 掛上去。

仍然引用了但沒附的是：`~/.claude/LABEL-REGISTRY.md`、`reports/`、以及 `settings.json`
裡兩個絕對路徑。每一項的原因與「你實際拿到的是什麼」記在
[`../tools/share-manifest.toml`](../tools/share-manifest.toml) 的 `[[not_shipped]]`；
`../tools/share_gate.py` 的 R 檢查會擋下任何新的未宣告引用。

## 去識別化與限制｜De-identification and limits

此快照已移除來源中出現的使用者名稱；未修改規範文件之間的交叉引用，以保留其原始結構與可讀性。分享前仍應依自己的環境檢查路徑、帳號、主機名稱、電子郵件與存取權杖等本機資訊。

## 使用方式｜How to use

將本資料夾視為可閱讀的參考資料，而非自動同步來源。若要採用其中內容，請依所使用的代理工具與本機安全政策選擇性調整。

## 授權｜License

本資料夾隨母專案採用 [MIT License](../LICENSE)。
