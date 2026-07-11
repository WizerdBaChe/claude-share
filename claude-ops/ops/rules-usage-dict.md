# 規則層使用書 (Ops Rules Usage Dictionary)

雙語對照 (bilingual)。用途 (purpose)：
1. 給你 (human)：了解每一層規則管什麼、改規則時該動哪個檔案。
2. 給 AI (machine)：判斷「這件事歸哪一層/哪個檔案/哪個 skill 管」時讀本檔。
   本檔為索引 (index only)，各檔案本文為準 (source files remain authoritative)。

**性質聲明 (nature)**：`ops/` 是規則層 (rules layer)，不是訓練資料 (not
training data)。它是 session 開頭注入的判斷框架 — 不會讓模型變聰明，只讓它在
已知情境下不必臨場重新推導。

---

## 一、層級總圖 (Layer Map) — 誰管什麼、衝突時誰贏

優先序 (precedence)，高者勝：

| 層 (layer) | 檔案 | 管什麼 (owns) | 誰能改 (who edits) |
|---|---|---|---|
| 1. 使用者全域偏好 | `~/.claude/CLAUDE.md` | 跨專案**條件式偏好**：git 工作流、工程判斷紅線、語言規則、檔案衛生。「當 X 時偏好 Y」 | 🔴 需使用者確認 |
| 2. 專案規則 | `<project>/CLAUDE.md` | 該專案的事實與紅線（指令、禁區、架構天花板） | 🔴 需使用者確認 |
| 3. 作業規則層 | `~/.claude/ops/*` | **怎麼執行多步驟/多代理工作**：派工、驗收、驗證、升級、思考姿勢 | 🟡 主 session 可改＋稽核 |
| 4. Skills | `~/.claude/skills/*` | 各自的**深度流程**（見下方分工表），按觸發句啟動 | 🟡 主 session 可改＋稽核 |
| 5. Harness 設定 | `settings.json`、`hooks/` | 機器強制的行為（權限、hook 自動化）— 規則寫了模型可能忘，hook 不會忘 | 🔴 需使用者確認（提案格式見 `70-evolution.md` §2） |
| 6. 自動記憶 | harness memory（MEMORY.md 索引）、`ops/lessons.md` | agent 自行累積的知識與坑（instruction memory 之外的 auto-memory） | 🟢 隨改（查重、標 superseded） |

判別法 (how to route a rule)：
- 「使用者希望事情**怎麼被對待**」→ CLAUDE.md（偏好）
- 「這個專案**是什麼、不能碰什麼**」→ 專案 CLAUDE.md（事實）
- 「任務該**怎麼被執行與驗證**」→ ops/（作業方法）
- 「需要一套**帶步驟的深度流程**」→ skill（流程）
- 「必須**每次強制發生**、不能靠模型記得」→ hook/settings（機制）
- 「是**事實知識**（API 特性、環境細節、有效做法）→ 記憶/lessons（知識），不進規則」

## 二、ops/ 內部路由 (routing within ops/)

| 情境 | 讀 |
|---|---|
| 接到任何非瑣碎指令（入口） | `10-command-loop.md` |
| 要派工、選模型、寫派工 prompt | `20-dispatch.md` |
| 卡在「該升級嗎/算完成嗎/該問嗎/方法錯了嗎」 | `30-judgment.md` |
| 要改 ops 檔、或剛踩了值得記的坑 | `40-maintenance.md` |
| 想校準思考方式（非旗艦模型的後設習慣） | `50-coach.md` |
| 新專案第一個 session、ticket 帳本位置與格式 | `60-bootstrap.md` |
| 要提案改 guardrail（settings/hooks/權限）、知識該進記憶還是規則 | `70-evolution.md` |
| 動手前查歷史坑 | `lessons.md`（先 grep） |

## 三、ops/ 與各 skill 的分工 (boundaries vs skills)

原則：ops/ 是**隨時生效的判斷框架**（無需觸發句）；skill 是**被觸發的深度流
程**。ops/ 遇到需要深度流程的情況，路由到 skill，不重寫其內容。

### vs `ai-coding-guardrails`
- ops/ 管：這一個 session 裡「這次派工要不要紅隊、驗收怎麼寫」的即時判斷。
- skill 管：為團隊/專案**設計整套護欄制度**（權限、CI、恢復程序、AGENTS.md）。
- 判別：發現是「流程性/制度性」問題（review 追不上、權限設計）→ skill；
  是「這一次交付怎麼驗」→ ops/ `30-judgment.md` R5。

### vs `config-self-audit`
- ops/ 管：改規則檔的**時機與權限分層**（`40-maintenance.md` §1）。
- skill 管：對**單一設定物件**（skill/hook/CLAUDE.md 條目/ops 檔）跑稽核清單。
- 關係：ops/ 的 🟡 級改動**以此 skill 作為紅隊步驟** — 互相引用，不重疊。

### vs `code-review-deep-checklist` / `/code-review`
- ops/ 管：收件三關卡（抽查/紅隊/簽核）— 對**任何**交付的通用收件紀律。
- skills 管：對**程式碼**的具體審查方法（快速抓蟲 → /code-review；深度健檢
  → deep-checklist）。收件關卡的「紅隊」遇到程式碼時，路由到這些 skill 執行。

### vs `workflow-checkpoint`
- ops/ 管：**任務內**的帳本（ticket、交付索引）— 以小時計的粒度。
- skill 管：**階段間**的封存與回溯（phase-log）— 以天/週計的粒度。
- 判別：「這個 chunk 做完了」→ ops/ Step 8；「這個階段做完了，之後接續」→ skill。

### vs `project-retrospective`
- ops/ 管：進行中的教訓即時歸檔（`lessons.md`、`40-maintenance.md` §2）。
- skill 管：**結案時**批次萃取經驗、經確認寫入 CLAUDE.md。
- 關係：retrospective 掃描時應把 `ops/lessons.md` 當輸入之一。

### vs `skill-trigger-dict.md`
- 那份管：**skill 之間**的觸發消歧（哪句話觸發哪個 skill）。
- 本檔管：**層與層之間**的職責邊界（規則該放哪、誰管什麼）。

## 四、與全域 CLAUDE.md 的重疊處置 (overlap resolution)

以下重疊為**有意的互補**，以 CLAUDE.md 為準、ops/ 不重複本文：

| 主題 | CLAUDE.md 已管 | ops/ 補充的維度 |
|---|---|---|
| 重試上限 | 「同一視覺症狀第 2 次未修就停手、做對照分析」 | 泛化到派工：任何問題兩輪未解，第三次必須換法（`20-dispatch.md` §5） |
| 驗收 | 「無法靜態驗證的改動附人工驗收清單」「視覺閘門需人確認」 | 機器可查驗收先於方法、living proof（`10` Step 4、`30` R2） |
| 檔案衛生 | archive-not-delete、報告開新檔 | 規則檔分層權限與修剪紀律（`40`） |
| 查證優先 | 「概念性錯誤先查 canonical 方法再改」 | 一般化為 C2/C6 思考習慣（`50-coach.md`） |

## 五、Agent 名冊路由 (Agent Roster Routing) — task shape → agentType → 強度

派工時的第三個維度：`skill-trigger-dict.md` 管 skill、本檔一~四節管層級，
本節管「派給哪個 agent、用什麼強度」。模型上限政策與 tier 映射見
`ops/environment.md`（上限：haiku/sonnet，opus/fable 需使用者當次核可，
由 `hooks/model_cap_guard.py` 強制）。

| 任務形狀 (task shape) | agentType | model × effort |
|---|---|---|
| 搜尋/盤點/read-many-files | `Explore`（內建，唯讀） | haiku~sonnet × medium |
| 機械性、有硬驗收閘（轉檔/翻譯/照規格腳本） | `general-purpose` | haiku × low |
| 後端/API 實作 | `backend-architect` | sonnet × medium |
| 前端實作 | `frontend-developer` | sonnet × medium |
| 寫測試、QA 驗證 | `testing-qa-engineer` / `api-tester` | sonnet × medium |
| Bug 根因定位與修復 | `testing-bug-fixer` | sonnet × medium~high |
| 紅隊/審查（reviewer ≠ author） | `code-reviewer`（fresh context） | sonnet × high |
| 安全審查 | `security-engineer` | sonnet × high |
| 架構規劃（派工版） | `Plan`（內建）或 `software-architect` | sonnet × high |
| 研究/多源查證 | `general-purpose` + T4 契約 | sonnet × high |
| 品味/政策措辭/模糊判斷 | **不派工** — 主 session 自做（`30-judgment.md` R6） | — |

消歧（易混淆組）：
- `code-reviewer` agent vs `/code-review` skill vs `code-review-deep-checklist`：
  skill 是**方法論**（快速抓蟲/深度健檢），agent 是**執行載體**。主 session 收件
  紅隊時派 `code-reviewer` agent；使用者主動要求 review 時走 skill 路由
  （`skill-trigger-dict.md` 審查家族）。
- `software-architect` vs `management-tech-lead` vs `Plan`：單純要一份實作計畫
  → `Plan`；要 ADR/選型 trade-off → `software-architect`；要任務拆分與派工建議
  → 那是 dispatcher 本人的工作（`10-command-loop.md`），不外派。
- 名冊中其餘 agent（mobile/devops/sre/mcp-builder/performance 等）按 description
  對號入座；本表只列高頻與易混淆者。

## 六、消歧速查表 (Disambiguation Quick Table)

| 你想做的事 | 去哪裡 |
|---|---|
| 這次任務怎麼拆、怎麼派、怎麼驗 | `ops/10`、`20`、`30` |
| 設計團隊級 AI 護欄制度 | ai-coding-guardrails |
| 稽核某個 skill/hook/規則檔安不安全 | config-self-audit |
| 深度審這段 code | code-review-deep-checklist |
| 階段完成、封存後續作 | workflow-checkpoint |
| 專案結束、萃取經驗進 CLAUDE.md | project-retrospective |
| 想「每次 X 自動 Y」（強制機制） | update-config（hooks） |
| 新增/修改使用者跨專案偏好 | 全域 CLAUDE.md（🔴 需確認） |
| 剛踩了一個坑要記下來 | `ops/lessons.md`（先查重） |
| 這條規則到底該放哪一層 | 本檔第一節判別法 |
