# Claude Ops Snapshot

這個資料夾是個人 `~/.claude/ops/` 作業規範的手動快照，供參考、移植或擷取可重用的代理工作流程。

## 內容

- `ops/`：權限、命令迴圈、任務派送、判斷、維護、教練、啟動與演進等作業規範。
- `ops/environment.md`：擷取時的工具環境與模型成本上限紀錄。
- `ops/OPS.md`：各規範文件的入口與使用索引。

## 路徑對照（採用前先看這張表）

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
| `hooks/*.py`、`settings.json` | **未隨附** | 見下 |

**這層引用了但沒附的東西**：`hooks/model_cap_guard.py`、`hooks/ops_health_nudge.py`、
`~/.claude/references/PROJECTS.md`、`~/.claude/LABEL-REGISTRY.md`、`reports/`、
`settings.json`。每一項的原因與「你實際拿到的是什麼」記在
[`../tools/share-manifest.toml`](../tools/share-manifest.toml) 的 `[[not_shipped]]`；
`../tools/share_gate.py` 的 R 檢查會擋下任何新的未宣告引用。

重點只有一句：**規則檔寫「由 hook 機械強制」的地方，你拿到的是散文。**
不是規則失效，是強制力降級——引用處寫的效果與你實際得到的效果不同，要自己補。

## 去識別化

此快照已移除來源中出現的使用者名稱；未修改規範文件之間的交叉引用，以保留其原始結構與可讀性。分享前仍應依自己的環境檢查路徑、帳號、主機名稱、電子郵件與存取權杖等本機資訊。

## 使用方式

將本資料夾視為可閱讀的參考資料，而非自動同步來源。若要採用其中內容，請依所使用的代理工具與本機安全政策選擇性調整。

## 授權

本資料夾隨母專案採用 [MIT License](../LICENSE)。
