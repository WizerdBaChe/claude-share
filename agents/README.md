# agents/ — subagent 定義｜Subagent definitions

> **中文摘要｜Chinese summary**：本層收錄 `20-dispatch.md` 會派出的 10 種
> subagent 定義。每份定義都把能力白名單、工作邊界、Skill 路由與輸出證據格式
> 寫在同一份檔案裡；這些檔案是 Claude-oriented dispatch assets，不是跨平台
> agent runtime。
>
> **English summary**: This directory contains the ten subagent definitions routed by
> `20-dispatch.md`. Each definition makes its tool boundary, role boundary, skill
> routing, and evidence-shaped output contract explicit. The files are Claude-oriented
> dispatch assets, not a portable agent runtime.

## 快速導覽｜Quick guide

| 項目 | 中文 | English |
|---|---|---|
| 讀者 | 要讀派工角色、審查邊界或安裝 Claude agent definitions 的維護者 | Maintainers who need the dispatch roster, review boundaries, or Claude agent installation |
| 入口 | 先讀 [`claude-ops/ops/20-dispatch.md`](../claude-ops/ops/20-dispatch.md)，再按 `name:` 找定義檔 | Start with `20-dispatch.md`, then select a definition by its `name:` field |
| 驗收 | 檢查 `tools:`、`Skill`、Output 段與角色專屬的唯讀／施工邊界 | Check `tools:`, `Skill`, the Output section, and each role's read-only/build boundary |
| 不包含 | 不包含 dispatcher、模型服務、credentials 或通用 runtime | No dispatcher, model service, credentials, or generic runtime is included |

## 名冊｜Roster

| 檔案 | agent type | 邊界（描述裡就寫死的那條線） |
|---|---|---|
| `engineering-backend-architect.md` | `backend-architect` | 實作已決定的形狀；**不**做架構選型；施工卡（附自己的驗收清單）交給 `work-card-executor` |
| `engineering-frontend-developer.md` | `frontend-developer` | 實作已決定的設計；**不**決定設計方向；動到互動語意要先問 |
| `engineering-software-architect.md` | `software-architect` | 選型與取捨、ADR；**不**產實作計畫、**不**做任務拆分 |
| `engineering-code-reviewer.md` | `code-reviewer` | 唯讀對抗式審查；**只**回報，永不編輯或 commit |
| `engineering-security-engineer.md` | `security-engineer` | 唯讀防禦性資安審查；不寫 exploit |
| `testing-qa-engineer.md` | `testing-qa-engineer` | 用跑的驗證，不是用讀的 |
| `testing-api-tester.md` | `api-tester` | 從外部測契約；**不**改實作去讓測試過 |
| `testing-bug-fixer.md` | `testing-bug-fixer` | 修因不修症；根因沒命名就不算修好；執行施工卡不算修 bug，交給 `work-card-executor` |
| `work-card-executor.md` | `work-card-executor` | 照一張已定案的施工卡機械化施工到驗收；卡沒解的解讀分歧就停下回報，**不**擴大範圍；規則層檔案（CLAUDE.md、`~/.claude/ops/`、skills/、hooks/、settings.json、agents/）永不寫入 |
| `cheap-worker.md` | `cheap-worker` | 便宜層（haiku）機械工：只接有硬性機器驗收閘的任務（抽取、改格式、照規格寫腳本、搜尋盤點後排序、有不可變測試的修復、摘要不可信內容）；**不帶**使用者指令層（`omitClaudeMd`），判斷、品味或需要規則層的工作交給 `general-purpose` 或 sonnet 角色 |

## 共通契約｜Shared contracts

1. **`tools:` 白名單即權限邊界。** 審查類（code-reviewer、security-engineer）
   沒有 `Edit`／`Write`，所以「唯讀」不是請求而是能力事實，另配 `permissionMode: dontAsk`。
2. **每支都必含 `Skill`，且 body 明寫「roster 才是真相來源」**——不准照著寫死在
   prompt 或本檔裡的技能名字工作。這是防止定義檔腐爛成過期名單。
3. **Output 段規定交付格式**，包含證據分級（`Confirmed`／`Hypothesis`／`Unverified`）
   與歸屬分級（`introduced`／`pre-existing`／`amplified`）。沒到證據門檻就回
   `No findings.`，不准補場面話。

## 來源與授權｜Lineage and licensing

上述 8 支（`work-card-executor.md` 與 `cheap-worker.md` 除外）第一行 HTML 註解都留著出處：2026-07-06
由第三方套件 **ai-team-os** 一次帶入 22 個定義，2026-08-12 其中 8 個 body
**整份重寫**（行為不變量改為源自 CLAUDE.md 與 `ops/`，並補上 `tools:` 白名單），
其餘 14 個封存退役。`work-card-executor.md` 血緣不同：2026-09-04 由 main session 為 SSLD
remediation round 直接原生撰寫，不經 ai-team-os，第一行註解記的是登記債
（誰欠補哪些索引列），不是第三方出處。

`cheap-worker.md` 也是原生撰寫（2026-10-08，由 `model-bench` 第三輪的結果而來：便宜層在每個有硬閘的列上都過，
它付出的代價是 prefix，所以這支定義不載入使用者指令層）。它的 `omitClaudeMd` 欄位需要 Claude Code 2.1.271 以上；
`effort: medium` 是來源端使用者的裁示下限，不是通用建議。

因此本目錄的內文是本環境自撰，不含第三方文字；`adopted-from` 註解保留，是為了讓
血緣可追溯，不是授權聲明。前身套件的授權狀態未經查證——若你要回頭找原始 22 個
定義，那份授權要自己確認。

> 對照：`skill-toolkit/motion-design` 的 Three.js 參考套件因為上游沒有正式 LICENSE
> 而**完全不收錄**。兩者判準一致，結論不同的原因只有一個：這裡的內文已經不是對方的了。

## 安裝與驗收｜Install and verify

複製到你的 `~/.claude/agents/`。檔名不影響路由，`name:` 才是；派工時用的是
`backend-architect` 這種 `name`，不是檔名。

`model: sonnet`／`haiku` 與 `effort: high`／`medium` 是來源環境的成本政策（配合
`hooks/model_cap_guard.py` 的上限），不是通用建議——自己的成本結構自己定。
