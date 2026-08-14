# agents/ — subagent 定義（8 支）

`claude-ops/ops/20-dispatch.md` 的派工表點名這 8 個 agent type，但定義檔在
2026-08-14 之前從未隨附——引用得到、拿不到本體。現已補齊，逐檔 byte-verbatim。

## 名冊

| 檔案 | agent type | 邊界（描述裡就寫死的那條線） |
|---|---|---|
| `engineering-backend-architect.md` | `backend-architect` | 實作已決定的形狀；**不**做架構選型 |
| `engineering-frontend-developer.md` | `frontend-developer` | 實作已決定的設計；**不**決定設計方向；動到互動語意要先問 |
| `engineering-software-architect.md` | `software-architect` | 選型與取捨、ADR；**不**產實作計畫、**不**做任務拆分 |
| `engineering-code-reviewer.md` | `code-reviewer` | 唯讀對抗式審查；**只**回報，永不編輯或 commit |
| `engineering-security-engineer.md` | `security-engineer` | 唯讀防禦性資安審查；不寫 exploit |
| `testing-qa-engineer.md` | `testing-qa-engineer` | 用跑的驗證，不是用讀的 |
| `testing-api-tester.md` | `api-tester` | 從外部測契約；**不**改實作去讓測試過 |
| `testing-bug-fixer.md` | `testing-bug-fixer` | 修因不修症；根因沒命名就不算修好 |

## 三個貫穿全部的設計

1. **`tools:` 白名單即權限邊界。** 審查類（code-reviewer、security-engineer）
   沒有 `Edit`／`Write`，所以「唯讀」不是請求而是能力事實，另配 `permissionMode: dontAsk`。
2. **每支都必含 `Skill`，且 body 明寫「roster 才是真相來源」**——不准照著寫死在
   prompt 或本檔裡的技能名字工作。這是防止定義檔腐爛成過期名單。
3. **Output 段規定交付格式**，包含證據分級（`Confirmed`／`Hypothesis`／`Unverified`）
   與歸屬分級（`introduced`／`pre-existing`／`amplified`）。沒到證據門檻就回
   `No findings.`，不准補場面話。

## 血緣與授權

每個檔案第一行 HTML 註解都留著出處：2026-07-06 由第三方套件 **ai-team-os** 一次帶入
22 個定義，2026-08-12 其中 8 個 body **整份重寫**（行為不變量改為源自 CLAUDE.md 與
`ops/`，並補上 `tools:` 白名單），其餘 14 個封存退役。

因此本目錄的內文是本環境自撰，不含第三方文字；`adopted-from` 註解保留，是為了讓
血緣可追溯，不是授權聲明。前身套件的授權狀態未經查證——若你要回頭找原始 22 個
定義，那份授權要自己確認。

> 對照：`skill-toolkit/motion-design` 的 Three.js 參考套件因為上游沒有正式 LICENSE
> 而**完全不收錄**。兩者判準一致，結論不同的原因只有一個：這裡的內文已經不是對方的了。

## 安裝

複製到你的 `~/.claude/agents/`。檔名不影響路由，`name:` 才是；派工時用的是
`backend-architect` 這種 `name`，不是檔名。

`model: sonnet` 與 `effort: high` 是來源環境的成本政策（配合
`hooks/model_cap_guard.py` 的上限），不是通用建議——自己的成本結構自己定。
