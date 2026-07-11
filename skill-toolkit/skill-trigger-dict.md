# Skill 觸發關鍵詞字典 (Skill Trigger Keyword Dictionary)

雙語對照 (bilingual)。用途 (purpose)：
1. 給你 (human)：對話時採用「精準句型」欄的說法，可最大化命中正確的 skill。
2. 給 AI (machine)：路由歧義時可讀本檔輔助判斷；本檔為索引，不取代各 SKILL.md 的 description（以 description 為準）。

格式 (format)：每個 skill 一個條目 —
`觸發關鍵詞 (keywords)` / `精準句型 (precise phrasing)` / `避免說法 (avoid — 會誤觸其他 skill)`

---

## 審查家族 (Review Family) — 最容易互相誤觸，先看這區

### code-review-deep-checklist（深度審查方法論 / deep-methodology review）
- 關鍵詞：深入review、完整審查、健檢 (health check)、代碼異味 (code smell)、需求追溯 (traceability)、選型評估 (dependency fitness)、全專案審查 (whole-project review)
- 精準句型：
  - Mode A：「幫我**深入 review** 這個 PR/檔案」/ "do a **deep review** of this file"
  - Mode B：「幫**整個專案**做架構**健檢**」/ "whole-project architecture health check"
  - Mode C：「評估 X 套件對這個專案**還適不適合**」/ "audit whether library X is still the right fit"
- 避免說法：「merge 前幫我看一下」（→ /code-review）、「盤點技術債列 backlog」（→ engineering:tech-debt）

### /code-review（內建快速抓蟲 / fast pre-merge bug hunt）
- 關鍵詞：merge前、review this diff、有沒有bug、安全嗎 (is this safe)
- 精準句型：「merge 前幫我 review 這個 diff」/ "review this before I merge"；深層多代理雲端版加 `ultra`
- 避免說法：「深入/完整」字眼（會升級到 deep-checklist）

### /simplify（品質清理 / quality-only cleanup）
- 關鍵詞：簡化 (simplify)、重複代碼 (reuse)、精簡
- 精準句型：「幫我簡化這次改動的代碼」— 只做品質，不抓 bug
- 避免說法：「順便看有沒有 bug」（→ /code-review）

### /review（GitHub PR 審查）
- 精準句型：「review PR #123」— 給 GitHub 上的 PR；本地 diff 用 /code-review

### /security-review（安全快查 / fast security gate on pending changes）
- 關鍵詞：security review、改動有沒有安全問題
- 精準句型：「對**目前分支的改動**做 security review」— 只看 pending diff 的快速安全閘門
- 避免說法：「資安健檢」「整個專案找漏洞」（→ security-deep-checklist）

### security-deep-checklist（深度資安稽核 / blue-team informed security audit）
- 關鍵詞：資安檢核、資安健檢 (security health check)、找漏洞 (vulnerability sweep)、XSS、SQL injection、CSRF、部署安全 (deployment posture)、供應鏈 (supply chain)、內網/不聯網風險 (air-gapped risk)、偵測與應變 (detection & response)、OWASP
- 精準句型：
  - Mode A：「幫這個模組/專案做**程式碼資安稽核**」/ "security audit of this module"
  - Mode B：「檢查**部署與設定**的安全姿態」/ "deployment security posture review"
  - Mode C：「如果被攻擊我們**看得到嗎**？檢查 logging/alerting/IR 準備」
  - 全套：「幫整個系統做**資安健檢**」
- 避免說法：「merge 前看一下安全」（→ /security-review）、「順便看 code 品質」（→ code-review-deep-checklist）、「新系統該怎麼設計權限」（設計期 → product-design-thinking Phase 2 security-by-design）

### engineering:tech-debt（技術債盤點 / debt backlog deliverable)
- 關鍵詞：技術債 (tech debt)、重構優先序 (refactor priorities)、code health
- 精準句型：「幫我**盤點技術債，列成優先序 backlog**」— 交付物是債務清單本身
- 避免說法：「健檢」（→ deep-checklist Mode B；它只把債當透鏡，不產 backlog）

### engineering:architecture（架構決策記錄 / ADR）
- 關鍵詞：ADR、技術選型（**新決策**）、Kafka vs SQS、trade-off
- 精準句型：「該選 A 還是 B？幫我寫 ADR」— **向前看的新決策**
- 避免說法：「現在用的 X 還適合嗎」（回顧性 → deep-checklist Mode C）

### ai-coding-guardrails（AI 協作防護體系 / guardrail SYSTEM & process）
- 關鍵詞：AI寫壞了、agent刪了不該刪的、怎麼限制agent、AI PR審不完、護欄 (guardrails)、AGENTS.md設計
- 精準句型：「AI PR 量太大 review 追不上，幫我設計**流程/機制**」— 對象是制度，不是單一改動
- 避免說法：「幫我深審這段 AI 產的 code」（單一改動 → deep-checklist Mode A §9）

### config-self-audit（Claude Code 設定檔稽核）
- 關鍵詞：稽核skill (audit skill)、檢查hook、這條global規則安全嗎
- 精準句型：「幫我 audit 這個 skill/hook/CLAUDE.md 規則」— 只審 Claude Code 設定物件，不審專案代碼

---

## 設計與規劃 (Design & Planning)

### product-design-thinking（高強度產品/功能設計）
- 關鍵詞：新產品構想、新工具設計 (new tool design)、可行性評估 (feasibility)、Concept Note、CIM、PIM、PSM、語義契約 (semantic contract / DSL)、語義鴻溝驗證 (semantic gap)、RPD、複雜新功能規劃
- 精準句型：「我有一個新產品想法，幫我做第一性原理拆解與設計」/「我需要設計一個新工具，進入設計模式」
- 適用時機：對話中途出現設計需求也應觸發，不限開場；中途沒中時，明講 skill 名稱（「用 product-design-thinking 來做」）100% 命中
- 避免說法：bug 修復、按圖施工、小型加功能、「寫個小工具/腳本」（都不觸發，這是重量級模式）

### design-system-suite（多產品共用設計系統）
- 關鍵詞：design tokens、theme packs、產品套件 (product suite)、跨產品導航 (cross-app nav)
- 精準句型：「把幾個 app 統一到共用 design tokens + 主題包」
- 避免說法：單一 app 的樣式調整（不觸發）

### engineering:system-design（單一系統/服務架構設計）
- 精準句型：「幫我設計一個處理 X 的系統/API/資料模型」— 範圍窄於 product-design-thinking

### product-management:write-spec（寫 PRD/spec）
- 精準句型：「把這個功能想法寫成一份 PRD」

---

## 流程與階段管理 (Workflow & Phases)

### workflow-checkpoint（階段封存 + 續作回溯）
- 關鍵詞：階段完成 (phase done)、存檔 (checkpoint)、回顧專案繼續做 (recap and continue)
- 精準句型：「這個階段完成了，做一次 checkpoint」/「我要接續之前的 X 專案」
- 避免說法：「專案結束了幫我總結」（→ project-retrospective）

### project-retrospective（結案回顧 / lessons learned）
- 關鍵詞：回顧 (retrospective)、踩了什麼坑、總結這個專案、幫我寫CLAUDE.md規則
- 精準句型：「專案**結束**了，萃取經驗寫成 guide + CLAUDE.md 規則」
- 避免說法：「告一段落，之後繼續」（→ workflow-checkpoint）

---

## 執行與驗證 (Execution & Verification)

### verify（實跑驗證改動）
- 精準句型：「實際跑起來**驗證**這個 fix 有效」/ "verify the fix works"

### run（啟動專案 app）
- 精準句型：「把 app 跑起來 / 截圖給我看改動效果」

### engineering:debug（結構化除錯）
- 關鍵詞：錯誤訊息、stack trace、staging好的prod壞
- 精準句型：「這個 error 幫我 debug：<貼錯誤>」

### engineering:testing-strategy（測試策略）
- 精準句型：「這個模組該怎麼測 / 幫我規劃 test plan」

### deep-research（深度研究報告）
- 精準句型：「幫我做一份有引用來源的深度研究：X」— 題目要夠具體
- 避免說法：「我這個**實驗/研究**下一步該做什麼」（做自己的研究流程 → scientific-research-guide）

### scientific-research-guide（科研方法論顧問 / research methodology advisor）
- 關鍵詞：研究流程走到哪、實驗怎麼設計、該用哪個統計檢定、對照組/抽樣/樣本量、模型 V&V/不確定性、擬合好不好/殘差、多重比較、投稿前要補什麼、可重現性、PRISMA/文獻空缺
- 精準句型：
  - 定位：「我的**研究/實驗**做到 X 了，**下一步該做什麼、還缺什麼**？」
  - 方法：「三組數據 n=6，**該用哪個統計檢定**？」/「這個**實驗怎麼設計對照組**」
  - 投稿：「**投稿前**方法學上還要補什麼？」
- 性質：顧問型，預設只診斷/建議/寫規劃文件；**未經明確要求不寫程式、不動資料**（明確要求則照做並套方法論）。
- 領域特化 (domain profiles)：內建 plasmonic waveguide（SPP/近場光學/SERS/FDTD-FEM 模擬方法論）— 該領域研究問題也觸發本 skill；新增領域依 `domains/domain-expansion-guide.md`。
- 避免說法：「幫我做一份有來源的深度研究報告」（查某主題 → deep-research）、「純寫程式/修 bug」（→ engineering skills）、「寫 PRD」（→ product-management:write-spec）

### literature-search-extract（文獻檢索與萃取服務 / literature search & extraction service）
- 關鍵詞：找論文、這篇paper重點、教科書怎麼定義X、整理幾篇的方法比較、查參數的文獻值、evidence table、annotated bibliography、comparison matrix、引用可追溯 (citation traceability)、access tag
- 精準句型：
  - 直接：「幫我**找 X 主題的論文**並整理**方法比較**（每格要有引用）」/「這篇 paper 的**重點/方法/限制**是什麼」/「**教科書**裡怎麼定義 X」/「幫我**查這個參數的文獻值**」
  - 服務：其他 skill 傳入 request contract（purpose/question/output_format），接回 result contract（findings/sources/gaps/confidence）
- 性質：取回並萃取**已發表正式來源**（期刊/預印本/教科書/標準）的內容，逐條帶 source locator + access tag，**零捏造引用**；核心能力是「知道每種資訊住在論文哪一節」的定向萃取，不是通用摘要。
- 避免說法：「幫我做某主題的**深度研究報告**」（廣域多來源事實查核 → deep-research）、「我這個**研究下一步**該做什麼」（自己研究的方法論建議 → scientific-research-guide，它可能**反過來調用本 skill** 做 Tier 1 文獻）、「competitor/市場情報」（→ marketing:competitive-brief）

---

## 環境設定 (Claude Code Config)

### update-config（settings.json / 權限 / hooks）
- 關鍵詞：allow X、加權限、設環境變數、每次X之後自動Y (automation via hooks)
- 精準句型：「以後每次 X 時自動 Y」/「把 npm 加進允許清單」

### anthropic-skills:skill-creator（建立/優化 skill）
- 精準句型：「幫我建一個新 skill / 優化這個 skill 的 description / 跑 eval」
- 避免說法：「檢查這個 skill 安不安全」（→ config-self-audit）、「打包 skill 分享給別人」（→ skill-share-packaging）

### env-cleanup（環境自清潔 / file-level environment cleanup）
- 關鍵詞：清理環境 (clean up environment)、無關檔案 (leftover/stray files)、環境整理、掃描垃圾檔、封存舊檔 (archive stale files)
- 精準句型：
  - Mode A：「幫我**清理 .claude 環境**，列出不再使用的檔案」/ "clean up my .claude"
  - Mode B：「**掃描這個專案的無關檔案**並整理封存」/ "tidy this project's stray files"
- 避免說法：「稽核/檢查這個 skill 安不安全」（審內容 → config-self-audit）、「規則檔太肥幫我修剪」（修內容 → ops/40-maintenance §3）、「盤點技術債」（→ engineering:tech-debt）
- 邊界：本 skill 只判斷「檔案還該不該存在」並移動封存，**永不編輯檔案內容、永不刪除**；一律先列表徵詢

### skill-share-packaging（skill 跨環境打包與匯入稽核 / cross-environment packaging & import audit）
- 關鍵詞：分享 skill (share a skill)、打包 (package)、匯出 (export)、分享版、裝別人的 skill (install a third-party skill)、匯入稽核 (import audit)
- 精準句型：
  - Mode A：「把 X skill **打包成分享版**給別人用」/ "package this skill to share"
  - Mode B：「我從網路抓了一個 skill，**檢查能不能安全裝**」/ "audit this downloaded skill before installing"
- 避免說法：「建/改 skill」（→ skill-creator）、「稽核我自己的 skill 內容」（→ config-self-audit）、「清理環境檔案」（→ env-cleanup）
- 邊界：正典 skill 永不為分享而修改；分享副本是單向建置產物，放 `~/.claude/outputs/skill-share/`；匯入一律先隔離稽核再入 `skills/`

### /loop、/schedule（排程與循環）
- 精準句型：「每 5 分鐘跑一次 /X」（loop）/「每天早上 9 點自動執行 X」（schedule）

---

## 規則層邊界 (Ops Rules Layer — not a skill)

### ~/.claude/ops/（專案作業規則層 / project-ops rules layer）
- 性質：多步驟/多代理任務的即時判斷框架（派工、驗收、驗證、升級、思考姿勢）。**不是 skill、無觸發句** — 遇到非瑣碎專案任務直接讀 `ops/OPS.md` 路由表。
- 邊界（詳細分工表見 `ops/rules-usage-dict.md`）：制度/流程設計 → ai-coding-guardrails；單一設定檔稽核（含 ops/ 檔案本身）→ config-self-audit；深度審 code → code-review-deep-checklist；階段封存 → workflow-checkpoint；結案萃取 → project-retrospective。
- 避免混淆：本檔管「哪句話觸發哪個 skill」；`ops/rules-usage-dict.md` 管「哪條規則/職責歸哪一層」。

---

## 消歧速查表 (Disambiguation Quick Table)

| 你想說的一句話 | 正確目標 (correct target) |
|---|---|
| merge 前看一下 diff | /code-review |
| 目前分支改動的安全快查 | /security-review |
| 資安健檢 / 全專案找漏洞 | security-deep-checklist |
| 部署/設定安全姿態、供應鏈風險 | security-deep-checklist (B) |
| 被攻擊看得到嗎（logging/IR） | security-deep-checklist (C) |
| 新系統的權限/驗證怎麼設計 | product-design-thinking (Phase 2 security-by-design) |
| 深入 review 這個 PR | code-review-deep-checklist (A) |
| 全專案架構健檢 | code-review-deep-checklist (B) |
| 套件 X 還適合嗎 | code-review-deep-checklist (C) |
| 我這個實驗/研究下一步該做什麼 | scientific-research-guide |
| 該用哪個統計檢定 / 實驗怎麼設計 | scientific-research-guide |
| 投稿前方法學要補什麼 | scientific-research-guide |
| 把這個 skill 打包分享給別人 | skill-share-packaging (A) |
| 網路抓的 skill 能不能安全裝 | skill-share-packaging (B) |
| 找論文 / 整理方法比較 / 查文獻參數值 | literature-search-extract |
| 這篇 paper 的重點/方法/限制 | literature-search-extract |
| 教科書裡怎麼定義 X | literature-search-extract |
| 幫我做某主題的深度研究報告 | deep-research |
| 盤點技術債列 backlog | engineering:tech-debt |
| 該選 A 還是 B（新決策） | engineering:architecture |
| AI PR 審不完（流程） | ai-coding-guardrails |
| 深審這段 AI 產的 code | code-review-deep-checklist (A §9) |
| 稽核這個 skill/hook | config-self-audit |
| 清理 .claude / 專案的無關檔案 | env-cleanup |
| 新產品構想設計 | product-design-thinking |
| 階段完成存檔、之後續作 | workflow-checkpoint |
| 專案結束萃取經驗 | project-retrospective |
