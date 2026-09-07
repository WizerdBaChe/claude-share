# 規則層使用書 (Ops Rules Usage Dictionary)

雙語對照 (bilingual)。索引檔 (index only)，各檔本文為準：查「每層規則管什
麼、改規則動哪個檔、這件事歸哪層/哪檔/哪個 skill」時讀本檔。`ops/` 性質宣
告見 `OPS.md` 開頭。

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
| 6. 自動記憶 | harness memory（MEMORY.md 索引）、`ops/lessons.md` | 記憶＝使用者偏好/專案脈絡/外部參照；**坑的唯一歸宿＝`ops/lessons.md`**（sole pitfall ledger） | 🟢 隨改（查重、標 superseded） |
| 7. 知識庫 (knowledge vault) | 使用者本機的 Obsidian 知識庫（權威＋lint 工具，皆為 source-only，未隨此 repo 收錄）；wing：`domains/`＝scientific-research-guide、`lexicon/`＝LexiconVault | **宣告式知識**：概念、文獻、主題地圖、術語候選；收納決策表與筆記契約住在該 vault 的權威檔；wing 只讀，內容改動走各自 owner 的流程。使用者裁定 2026-09-02：一切以此 vault 為根 | 🟡 主 session 可改原生區＋lint 0 FAIL；wing 內 🔴 不在此改 |

判別法 (how to route a rule)：
- 「使用者希望事情**怎麼被對待**」→ CLAUDE.md（偏好）
- 「這個專案**是什麼、不能碰什麼**」→ 專案 CLAUDE.md（事實）
- 「任務該**怎麼被執行與驗證**」→ ops/（作業方法）
- 「需要一套**帶步驟的深度流程**」→ skill（流程）
- 「必須**每次強制發生**、不能靠模型記得」→ hook/settings（機制）
- 「是**事實知識**（API 特性、環境細節、有效做法）→ 記憶/lessons（知識），不進規則」
- 「是**要留下來讀的知識內容**（概念、文獻、主題地圖、術語候選）→ 使用者本機的
  Obsidian 知識庫（source-only，未隨此 repo 收錄），先讀其權威檔 §3 收納決策表；
  領域框架 packet → scientific-research-guide §9，素材 → AssetVault
  （source-only，未隨此 repo 收錄），都不是 vault 原生區」

## 二、ops/ 內部路由 (routing within ops/)

| 情境 | 讀 |
|---|---|
| 接到任何非瑣碎指令（入口） | `10-command-loop.md` |
| 要派工、選模型、寫派工 prompt | `20-dispatch.md` |
| 卡在「該升級嗎/算完成嗎/該問嗎/方法錯了嗎」 | `30-judgment.md` |
| 要改 ops 檔、或剛踩了值得記的坑 | `40-maintenance.md` |
| 想校準思考方式（非旗艦模型的後設習慣） | `50-coach.md` |
| 新專案首個 session、ticket 帳本、切票 (tracer-bullet)、施工卡 (work card)、詞彙表 (glossary)、決策日誌 (decision journal) | `60-bootstrap.md` |
| 要提案改 guardrail（settings/hooks/權限）、知識該進記憶還是規則 | `70-evolution.md` |
| 動手前查歷史坑 | `lessons.md`（先 grep；每條是 card，完整敘事在 `references/lessons-detail.md` 同編號章節） |

**`ops/references/`（2026-08-12 起）**：ops 檔超標時「具體內容」的落點——範例、
指令區塊、佐證案例搬進去，**規則本文只留規則、條件、路由**。由 owner 檔的該節
以指標帶入，**不進上面這張路由表**（跟 `skills/*/references/` 同語意：隨用隨載，
不在 session start 計費）。上限單位與兩類計費模型見 `40-maintenance.md` §3。

## 三、ops/ 與各 skill 的分工 (boundaries vs skills)

原則：ops/ 是隨時生效的判斷框架（無需觸發句）；skill 是被觸發的深度流程。
需要深度流程時路由到 skill，不重寫其內容。

### vs `ai-coding-guardrails`
- ops/ 管：這一個 session 裡「這次派工要不要紅隊、驗收怎麼寫」的即時判斷。
- skill 管：為團隊/專案**設計整套護欄制度**（權限、CI、恢復程序、AGENTS.md）。
- 判別：發現是「流程性/制度性」問題（review 追不上、權限設計）→ skill；
  是「這一次交付怎麼驗」→ ops/ `30-judgment.md` R5。

### vs `config-self-audit`
- ops/ 管：改規則檔的**時機與權限分層**（`40-maintenance.md` §1）。
- skill 管：兩個 mode。預設 mode 對**單一設定物件**（skill/hook/CLAUDE.md
  條目/ops 檔）跑稽核清單；**adoption mode** 對「從別的環境搬進來的一整層規則」
  審**彼此的關係**（觸發碰撞、順序、機制沒跟著到）——這是唯一會超出單一物件
  範圍的 mode，且僅限被採用的集合與其直接鄰居。
- 關係：ops/ 的 🟡 級改動**以此 skill 作為紅隊步驟** — 互相引用，不重疊。

### 外部進來的東西該走哪條（inbound routing，2026-08-12）

依**粒度**分流（粒度決定失效模式）：單一 skill → `skill-share-packaging`
Mode B；一整層規則／ops 樹 → `config-self-audit` adoption mode；
plugin／市集包／MCP → **只能偵測**，那些檔案受管、每 session 重生、在
`~/.claude` 之外，蓋不了戳也不該改。實測數字、outbound 分歧標記規則、
opencode 反向依賴未決項：`ops/references/inbound-routing.md`。

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

**詞彙三層 (vocabulary tiers)** — 一個「定義」該記在哪（亦即本檔與
`skill-trigger-dict.md` 的分工）：
1. 哪句話觸發哪個 skill → `skill-trigger-dict.md`（環境層）
2. 哪條職責歸哪一層 → 本檔（環境層）
3. 專案領域名詞的定義 → `references/<project>-context.md`（`60-bootstrap.md`
   §E；維護掛 workflow-checkpoint 與 product-design-thinking Phase 3）

同步規則：路由面變動時三者同 commit 更新 — 見 `40-maintenance.md` §2。

## 四、與全域 CLAUDE.md 的重疊處置 (overlap resolution)

以下重疊為**有意的互補**，以 CLAUDE.md 為準、ops/ 不重複本文：

| 主題 | CLAUDE.md 已管 | ops/ 補充的維度 |
|---|---|---|
| 重試上限 | 「同一視覺症狀第 2 次未修就停手、做對照分析」 | 泛化到派工：任何問題兩輪未解，第三次必須換法（`20-dispatch.md` §5） |
| 驗收 | 「無法靜態驗證的改動附人工驗收清單」「視覺閘門需人確認」 | 機器可查驗收先於方法、living proof（`10` Step 4、`30` R2）；清單本身的分段、排序軸與收錄門檻＝`references/uat.md`（該紀錄型別的 owner） |
| 檔案衛生 | archive-not-delete、報告開新檔 | 規則檔分層權限與修剪紀律（`40`） |
| 查證優先 | 「概念性錯誤先查 canonical 方法再改」 | 一般化為 C2/C6 思考習慣（`50-coach.md`） |

## 五、Agent 名冊路由 → 已移至 `20-dispatch.md`

任務形狀 → agentType → model×effort 的名冊是**派工路由**，owner 是
`20-dispatch.md`（本檔管的是層級與 skill 的職責邊界）。移動於 2026-08-11。

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
| 踩了坑要記下來 | `ops/lessons.md`（先查重） |
| 把計畫拆成票（tracer-bullet / investigation） | `ops/60-bootstrap.md` §C |
| 單項修改要寫成施工卡（欄位、何時必用） | `ops/60-bootstrap.md` §F |
| 專案領域名詞該定義在哪 | `references/<project>-context.md`（`60-bootstrap.md` §E） |
| 決策理由/被否決選項/過程死路要記在哪 (know-why) | `references/<project>-decisions.md`（`60-bootstrap.md` §G） |
| 交付要附可反駁性聲明 (refutability statement)、前提怎麼標 | `ops/30-judgment.md` R2、`ops/05-authority.md` §4 第 0 節 |
| 四條 `[BC]` 交付形狀規則的機制（BC-1 手動驗收清單／BC-2 可換介面與詮釋隔離點／BC-3 降級順序／BC-4 邊界相容枚舉） | `ops/05-authority.md` §4a（觸發詞留在全域 CLAUDE.md；boundary contract 存續時由契約滿足，見 §4 Supersession） |
| 某類紀錄文件的最小欄位是什麼 | 本檔 §7 登記表 |
| 規則該放哪一層 | 本檔第一節判別法 |

## 七、紀錄類型格式登記表 (§7 Record-Type Schema Registry)

最小欄位以 owner 檔本文為準，本表不複製全文。出生規則與 invariant 級宣告見
`40-maintenance.md` §3（新紀錄類型同 commit 登記於此）。

| 類型 (type) | 最小欄位 (minimum fields) | owner | 何時必用 (mandatory when) |
|---|---|---|---|
| ticket stub | status / owner / blocked-by / acceptance | `60-bootstrap.md` §C | 非瑣碎任務開工前 |
| work card (施工卡) | severity·confidence / objects / why / change / blast radius / rollback / acceptance / commit | `60-bootstrap.md` §F（模板：`60-record-templates.md` §1） | sole-basis build docs、深審修繕輸出 |
| DELIVERY.md | did / verified / could-not-do / artifacts | `60-bootstrap.md` §D | 每個被派工的 worker |
| glossary entry | term / date / definition / [superseded] | `60-bootstrap.md` §E | 領域名詞固化時 |
| project map (read-time) | 檔頭 map-schema / repo / generated-at / **generated-from (SHA)** / covers / excludes / budget；本文 Entry&routing / Shape / Facts / Open [infer]；每條斷言帶 `[git]`\|`[read]`\|`[infer]` | `60-bootstrap.md` §H（格式：`ops/references/project-map.md`） | §A 找不到任何 write-time 紀錄、且任務不只一處具名修改時 |
| decision journal — Now / D / P | Now: frontier·premises·open；D: status·context·options·choice+why·revisit-if·links；P: status·trail·resolution·links | `60-bootstrap.md` §G（模板：`60-record-templates.md` §2） | §G write-triggers 任一成立 |
| lessons entry | 一檔一筆的 per-lesson record（source-only 樹，未隨此 repo 收錄）：xi front matter（`what` 雙語 / `tags` / `aliases` / `date` / `status` 投影）＋ `## Record`（id / kind / created / session / project / **locator** / digest）＋ Context / Pitfall / Fix（必填，各有位元組上限）/ Detection / Narrative（不限長、逐字）/ Events（只追加；`hits` 與狀態由此推導）；只能經一個 source-only guarded intake 工具出生，`ops/lessons.md` 為生成索引（此 repo 有收，唯讀） | 該 intake 工具（source-only，未隨此 repo 收錄；格式細節見其 README） | 全域級坑；2026-09-07 起（舊兩層制見 rule-registry `lessons ledger shape`，已被新制取代） |
| guardrail 提案 APPLY.md | problem (含 **evidence block**) / change / benefit / risks / rollout & verification | `70-evolution.md` §2 | 改 settings/hooks/權限 |
| evidence block | session_id / digest / locator / captured_at | `70-evolution.md` §2 | 2026-08-11 起：新 lessons 條目與 guardrail 提案的 problem 欄（舊資料不回填） |
| phase-log section | project / phase / status / date + Goals / Decisions / Changes / Open Questions | `workflow-checkpoint` SKILL.md | 每次 checkpoint |
| boundary contract | 0 premises / 1 forks / 2 boundary inputs / 3 acceptance / 4 non-goals (≤18 行) | `05-authority.md` §4 | L1/L2（已鬆綁）× Tier-2 實作任務 |
| manual-acceptance checklist（人工驗收清單／UAT） | 兩段：`A. 必驗`（≤7 項，後果由高到低：資料與不可逆狀態 → 運作與使用 → 失敗看得見 → 換環境存活）+ `B. 體驗`（看得懂 → 順手 → 觀感）；跨段連續編號；每項＝一個具體動作 + 預期觀察、非作者可盲測；空段寫 `無`；**不得以模組／技術面分組**；機器驗得到的不收錄（改貼測試輸出）；人眼項目需有免破壞的檢視入口 | `ops/references/uat.md` | 交付含「只有人跑得出／看得出來」的部分時（全域 CLAUDE.md `[BC]`；L1/L2 有 boundary contract 時併入其 §3，不另開一份） |
| UX finding（走查發現／可執行發現） | Finding ID / task+context（任務卡 id＋情境變體）/ evidence mark `已確認`·`推論`·`待測` / current UI+copy（逐字）/ user consequence / layer（wording·layout·interaction·state model·service·research）/ proposed change＋保留的既有行為 / verification（工程檢查或任務＋成功條件）/ owner＋unresolved decision；「需要更友善」不是一條發現 | `skills/ux-walkthrough/SKILL.md` Step 3 | ux-walkthrough 交付的每一條缺陷（2026-09-07 起）；措辭層的列改以 audience-fit Mode B 提案表格列交付，互不重跑 |
| refutability statement | holds-when / overturned-by / evidence-tier / not-covered | `30-judgment.md` R2 | Tier-2 交付全欄；Tier-1 一行；T0 免 |
| rule-registry entry | key / current / why / evidence / history / review-when / rollback；**值是猜測時 `evidence` 以 `PROVISIONAL` 開頭 + 何者可定案 + 觀測寫回本條目**（2026-08-13）；**值依賴本庫以外的事實時（harness 預設、平台能力、廠商文件、未量測的比率）必填 `review-when:`，寫「哪個可觀察事件會使它失效」而非日期**（2026-08-14） | `ops/rule-registry.md` 頭部 | 規則值、上限、常設裁定設定或變更時（就地取代該鍵）；**含「先出貨的猜測值」——未登記的猜測沒有資料落點，會靜默變成永久值**；**含「注入層預設 × 本機收窄」一節——harness 注入文字會隨產品改版靜默變動** |
| change event | trigger / change (before→after) / result / rollback | git commit message | 每次 🔴/🟡 變更 |
| environment-facts block | build·test·run / tiers / dispatch / redlines / ledger + 驗證日期 | `60-bootstrap.md` §B | 專案 CLAUDE.md 建立時 |
| adoption stamp | adopted-from / source / adopted / reconciled | 被採用檔案的檔頭（格式見 `skills/config-self-audit/references/imported-config.md`） | 從別的環境搬入任何持久設定時 |
| reconciliation ledger | artifact / source / collisions / class / resolution / mechanism status / stamp | `config-self-audit` SKILL.md `Output format` | adoption mode 每次執行 |
| label family entry | 家族 / 量的軸 / 方向·值域 / owner（唯一定義處） | `~/.claude/LABEL-REGISTRY.md` §2 | 造出會裸引用的可列舉標籤時（同 commit） |
| advisory-output status line（建議型產出狀態列） | 檔案**前 10 行**內一行可 grep 的狀態宣告：`> status: SPENT\|OPEN\|PARTIAL — 消費者（D-條目/commit/規則§）; residual: <殘餘價值或 re-open 條件>`（中文檔用 `**狀態**：` 開頭亦合規，兩種拼法都算）。**便宜入口（免翻檔）**：`powershell` `Get-ChildItem -Recurse ~\.claude\outputs -Filter *.md \| Select-String -Pattern '^(> status:\|\*\*狀態)' -List \| ForEach-Object { "$($_.Filename): $($_.Line)" }`。清理語意：OPEN 永不成為 cleanup 候選；SPENT 仍 KEEP（是已發表比率的可印證據），唯一淘汰路徑是新檔標 `Supersedes` | 本列即 owner（2026-08-16，源自使用者指出散落建議資料無入口、無事前宣告、無白名單） | `outputs/` 下任何**帶著建議/候選/待裁事項**、未來 session 可能要接手處理的產出（candidates 檔、實驗證據目錄的 metrics、disposition）誕生時；主動浮出＝ops-health check 13（2026-08-16 落地，registry key `advisory-output surfacing`） |
| list-generation entry | 前綴 / 涵蓋範圍 / `[superseded: <old>]` | `60-bootstrap.md` §E（規則見 `LABEL-REGISTRY.md` §3） | 專案清單／回合被新版取代時 |
| handoff（交接單） | 一句話 / 30 秒起手式（指令）/ 必讀順序 / **待裁決表（附建議值，先問再動工）** / DoD / could-not-do；施工卡用 §1 格式 | `60-record-templates.md` §3（2026-09-02 登記；先例見 source 端既有交接單） | 重型回合由使用者拆成「本 session 評估／設計、新 session 施工」時；遠端或同儕 session 把工作交回本機時 |
| gap report（視圖缺口表） | view / element / defect(integrity·correspondence·view-missing·data-gap) / severity / basis(user-data·code·assumed) | `skills/product-design-thinking/references/view-integrity-checks.md` §3 | 對既有系統做視圖稽核或重建繪圖時（PDT Verification 視圖過門、code-review-deep-checklist Mode B 視圖稽核、diagram-authoring audit drawing） |
| evidence run record（證據查證紀錄） | `run.json`（schema `lse-runs/run@1`：run · request · reuse_check · result · ledger · deliverables · keys · review_when · handoff · related · domain · provenance · invalidation）＋ `ledger.jsonl` ＋ `sources/` ＋ `citecheck.json` ＋ `record.md`（vault 卡 `kind: literature`）；home `<vault>\literature\EvidenceRuns\<run_id>\`；schema 檔 `skills/literature-search-extract/loop/schemas/run.schema.json` | `skills/literature-search-extract/references/feedback-loop.md`（其設計文件為 source-only，未隨此 repo 收錄；2026-09-03 登記） | 每次 literature-search-extract 走到 P4.5 的 run（`loop/runs.py open` 建、`register` 收；`register` 拒收沒有 `reuse_check` 的 run） |
| reflux event（回流事件） | `event_id / at / kind(consumed·correction·retraction·handoff·rerun) / actor / run_id\|key / artifact / evidence / note`（＋工具寫回的 `decision`、`affected`）；append-only `<home>/reflux.jsonl`，只經 `loop/reflux.py` 寫入、fail-closed 驗證、永不編輯或刪除；schema `loop/schemas/event.schema.json` | 同上（2026-09-03 登記） | 消費者用了 LSE 的結果、發現錯了、撤稿掃描命中、反向交接給 source-only 的深讀 skill（未隨此 repo 收錄）、同題重跑取代舊 run |
