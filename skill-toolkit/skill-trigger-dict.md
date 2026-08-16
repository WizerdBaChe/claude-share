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
- **兩個 mode**：預設 mode 審**單一物件**；**adoption mode** 審「從別的環境搬進來的設定」之間的**關係**（觸發碰撞、順序、機制沒跟著到）。觸發詞：「移植過來的規則跟原本的打架」「我把別人的設定 repo 併進來了」、或磁碟上有 `reconciled: no` 戳記。搬進來的**單一** skill 走 `skill-share-packaging` Mode B，不走這裡
- 與官方 `/doctor`（`/checkup`）的分工：本 skill **自足**，`/doctor` 是最低優先的可選輸入，其輸出一律當未驗證宣稱。判定理由與 2026-07-25 實測細節見 SKILL.md §9 與 `skills/config-self-audit/references/telemetry.md`

---

## 設計與規劃 (Design & Planning)

### product-design-thinking（高強度產品/功能設計）
- 關鍵詞：新產品構想、新工具設計 (new tool design)、可行性評估 (feasibility)、Concept Note、CIM、PIM、PSM、語義契約 (semantic contract / DSL)、語義鴻溝驗證 (semantic gap)、RPD、複雜新功能規劃
- 精準句型：「我有一個新產品想法，幫我做第一性原理拆解與設計」/「我需要設計一個新工具，進入設計模式」
- 適用時機：對話中途出現設計需求也應觸發，不限開場；中途沒中時，明講 skill 名稱（「用 product-design-thinking 來做」）100% 命中
- 也觸發：「給我 **PSM 等級**的修正案/重規劃」「build-ready 的修正規劃文件」— 既有產品的修正**規劃**仍屬本 skill（產出物是 PSM 嚴謹度的文件），只有「按既有 PSM 施工」才不觸發（2026-07-12 新增，源自 ops/lessons.md L-002：未觸發導致差分式偷薄文件被當成唯一施工依據）
- 也觸發：把既有功能**換成完全不同的技術路線**（re-architecture、搬平台、換渲染路徑）——即使它以「實作任務」的措辭出現。判別子：要做的東西有業界專有名詞（"3D photo"、"parallax"、"LDI"…）＝有公認做法，選架構前的 prior-art 查證屬設計工作（2026-08-16 新增，源自 3D-photo-engine H-3 否決：Web 重架構被當實作任務，兩個 Phase 後才發現業界標準做法便宜一個數量級）
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
- 關鍵詞：階段完成 (phase done)、存檔 (checkpoint)、寫 phase log、回顧專案繼續做 (recap and continue)、收尾、本輪的終止、先到這邊、驗收/UAT 全數通過、我會再新開 session
- 精準句型：邊界多半「講出來」而非 commit 出來（實測 2026-06~08）：「先到這邊，我會再新開 session」/「本輪的終止要是…」/「合併吧，結束後寫 phase log」/「驗收已全數通過」/「先設計(留文件)再動手」；續作：「接續之前的 X 專案」/「recap」
- 避免說法：「專案結束了幫我總結」（→ project-retrospective）
- **收尾 vs 結案**：判準是「後面還有沒有事」，不是聽起來多終局。收尾+會繼續 → 本 skill；結案+萃取經驗 → project-retrospective
- 不該觸發：小修、單檔改動、純問答、階段進行中

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

## 素材庫 (Asset Library)

### asset-vault（個人跨棧素材庫操作 / personal cross-stack asset library；此 skill 未隨本 repo 出貨，見 tools/share-manifest.toml）
- 關鍵詞：素材庫、元件庫、抽進素材庫 (extract to vault)、查素材庫 (check the vault)、有沒有現成的X、可重用素材 (reusable asset)、素材庫健檢
- 精準句型：
  - Mode A：「把 X **抽進素材庫**」/ "extract this into the asset library"
  - Mode B：「**查素材庫**有沒有現成的 loader/dialog/parser」；建置任務中遇到通用能力需求時 AI 應**自觸發**先查庫再手刻
  - Mode C：「**素材庫健檢**」→ validate.py 完整性檢查
- 避免說法：「設計素材庫新功能/改架構」（設計層 → product-design-thinking）、「清理素材庫無關檔案」（→ env-cleanup）、「多產品**套件**統一 design tokens/theme packs」（跨 app 設計系統方法論 → design-system-suite；asset-vault 只管「單件素材入庫/取用」）
- 邊界：GUI 接口 (gui/gui-contract.json) 鎖版，已由一個姊妹 repo 實作為可瀏覽目錄（新增 kind 要同步該 repo 的 FAMILIES 家族表）；素材永不刪除只 deprecated

---

## 動效與 3D (Motion & 3D)

### motion-design（動效與 3D 總控 / motion + animation + 3D hub）
- 關鍵詞：動畫 (animation)、動效、轉場 (transition)、微互動 (micro-interaction)、緩動 (easing)、時長 (duration)、編舞/交錯 (choreography / stagger)、載入/成功/錯誤狀態、捲動觸發 (scroll-triggered)、品牌動態識別 (brand motion identity)、粒子 (particles)、Three.js、WebGL、GLSL/shader、GLTF、後製特效 (post-processing)、raycasting、OrbitControls
- 精準句型：
  - 方法論：「這個按鈕/卡片的**動效**該怎麼做（時長、緩動、人格）」/「幫我定**品牌動態識別**」
  - 3D：「用 **Three.js** 做一個 X」/「寫個 **shader/GLSL** 效果」/「載入 **GLTF** 模型並播動畫」
- 性質：**hub（總控）**。SKILL.md 只有路由表與常用表；內容在 `vendor/`（第三方 MIT 原文：LottieFiles 方法論 16 檔 + Three.js 手冊 10 檔）與 `local/`（本機義務與時效說明）。平時不佔 context，用到才讀。
- 本機義務（交付前必讀 `local/env-bridge.md`）：視覺閘門（測試綠 ≠ 畫面對，需使用者實環境確認）、動效/3D 交付一律附可切換 FPS+物件數讀數、失敗要自曝（黑畫面算缺陷）、GLSL ES 多貼圖取樣必須展開成具名 uniform（否則靜默編譯失敗）、可調參數集中成一個 config 區塊 + 調整對照表。
- 時效邊界：`vendor/threejs/` 對齊 r160+，現行為 r185（落後約 25 個 release），**完全未涵蓋 WebGPU / TSL**；引用 API 簽名前先讀 `local/currency.md` 並對照專案實裝版本。
- 擴充：未來新增動效 skill/函式庫（GSAP、Framer Motion、Rive、R3F…）**一律併入本 hub**，不另開頂層 skill — 程序見 `skills/motion-design/local/extending.md`。
- 避免說法：「多產品統一 design tokens / theme packs」（→ design-system-suite）、「把這個動畫元件**存進素材庫**」（→ asset-vault）、「整個產品的設計流程」（→ product-design-thinking）

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

### skill-co-upgrade（skill 實測共升級迴圈 / field-test co-upgrade loop）
- 關鍵詞：跑一輪迴圈 (run a co-upgrade round)、交互升級 (co-upgrade)、硬化這個 skill (harden this skill)、實測缺口、繞過了才做對 (had to bypass the skill to do it right)
- 精準句型：「跑一輪 co-upgrade 迴圈」/「這個 skill 實測有缺口，硬化它」
- 主動提議（僅一次，never run unprompted）：實戰中 skill 明顯誤觸發或被繞過時、或大改寫後的 skill 即將上第一次實戰前
- 避免說法：「稽核這個 skill 的內容」（靜態稽核 → config-self-audit，它是本迴圈內升級者的驗證步驟）、「建/改 skill」（→ skill-creator）、「清理檔案」（→ env-cleanup）

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
| 這個動效/轉場該怎麼做（時長、緩動） | motion-design |
| Three.js / WebGL / shader / GLTF | motion-design |
| 品牌動態識別、編舞與交錯 | motion-design |
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
| 稽核這個 skill/hook | config-self-audit（預設 mode） |
| 搬進來的規則跟原本的打架 | config-self-audit（adoption mode） |
| 清理 .claude / 專案的無關檔案 | env-cleanup |
| 跑一輪 skill 升級迴圈 / 硬化這個 skill | skill-co-upgrade |
| 新產品構想設計 | product-design-thinking |
| 既有功能換完全不同技術路線（re-architecture） | product-design-thinking |
| 階段完成存檔、之後續作 | workflow-checkpoint |
| 專案結束萃取經驗 | project-retrospective |
