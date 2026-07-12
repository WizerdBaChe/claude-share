# literature-search-extract — 待補實作清單 (deferred work)

> 狀態：SKILL.md 已完成並可獨立運作（quick/standard 深度）。以下為延後實作項目，
> 依優先序排列。每項完成後請同步更新 SKILL.md 的 Reference map（移除 *(planned)* 標記）。

## P1 — references/ 參照檔案（依優先序）

### ~~1. `references/extraction-playbook.md`~~ ✅ 已完成（2026-07-07）
- 已撰寫 `references/extraction-playbook.md`：P1 表格全部 7 種資訊需求類型各一節，
  含操作步驟、實作示範（全用虛構占位來源）、錯誤 vs 正確對照、P5 前總檢查清單。
- SKILL.md P4 段落與 Reference map 已同步更新（移除 *(planned)*）。

<details><summary>原始需求（存檔）</summary>
- 針對 P1 表格的每一種資訊需求類型 (information need)，寫一份「實作示範 (worked example)」：
  - 定義/概念類：如何從 review article 的 Introduction 與教科書章節開頭萃取，並處理多來源定義不一致。
  - 方法/協定類：如何從 Methods + Supplementary 重建步驟清單，含「論文沒寫但重現必需」的缺口標記法。
  - 數值/參數類：從 Results 表格與圖中讀值的規範（含從圖讀值時標記 `[read from figure]` 的精度警語）、單位換算紀錄。
  - 效度界限類：Discussion/Limitations 的萃取範本，以及作者「沒說的限制」如何以 `[synthesis]` 標記推論。
- 每種類型附一段「錯誤示範 vs 正確示範」對照（呼應 SKILL.md 的 failure mode #3）。

</details>

### ~~2. `references/output-templates.md`~~ ✅ 已完成（2026-07-07）
- 已撰寫 `references/output-templates.md`：7 種格式各含欄位定義 + 填好的示例（虛構占位
  來源）、Mode 1（繁中人讀）vs Mode 2（英文、欄位名穩定）語言規則、result contract
  完整 JSON-like 範例（含 partial-failure 行為說明）。
- SKILL.md P5 段落與 Reference map 已同步更新（移除 *(planned)*）。

### ~~3. `references/search-sources.md`~~ ✅ 已完成（2026-07-07）
- 已撰寫 `references/search-sources.md`：TODO 列的 8 個管道 + OpenAlex（驗證中發現值得
  納入）各一節；識別碼解析流程（DOI/arXiv/PMID/ISBN，含版本-頁碼警告與純引用字串的
  Crossref fuzzy lookup）；prism MCP 六個工具的用法表 + fallback 規則（實測確認 prism
  是本地語料庫工具，非網路檢索）；引文追蹤步驟與 4 種停止條件。
- 管道現況已於 2026-07-07 以 web search 驗證（要點：OpenAlex 2026-02 起需 API key、
  Crossref 2025-12 調整速率限制、IEEE Xplore API 需人工核發 key 故按不可用處理）。
  檔頭註明驗證日期與「行為異常時先重新驗證」規則。
- SKILL.md P2 段落與 Reference map 已同步更新（移除 *(planned)*）。

### ~~4. `references/credibility-rubric.md`~~ ✅ 已完成（2026-07-07）— P1 全數完成
- 已撰寫 `references/credibility-rubric.md`：venue 五級分層（A–D + X 排除級）、
  work-level 修正因子（被引脈絡而非被引數、preprint→已刊出強制檢查、時效、獨立性）、
  retraction 檢查流程（Retraction Watch 已由 Crossref 收購並免費開放，經 `update-to`/
  `relation` 欄位查核——2026-07-07 驗證）、掠奪性期刊多訊號篩查（Beall's List 2017 起
  停更僅剩鏡像，故採白名單正訊號 + 紅旗匯聚制）、教科書 canonicity 查法與版本規則、
  一則評分實作示範（虛構來源）。
- SKILL.md P3 段落與 Reference map 已同步更新（移除 *(planned)*）。

## P2 — 生態系整合 ✅ 全數完成（2026-07-07）

### ~~5. 註冊到 `~/.claude/skill-trigger-dict.md`~~ ✅
- 已於「執行與驗證」區新增本 skill 條目（關鍵詞/精準句型/性質/避免說法）+ 消歧速查表
  三列。消歧對象：deep-research（廣域）、scientific-research-guide（方法論，且註明其反向
  調用本 skill）、marketing:competitive-brief（市場情報）。

### ~~6. 修改 `scientific-research-guide` 完成雙向掛接~~ ✅
- SKILL.md Gate B：新增委派 bullet（Tier 1 搜尋+萃取可調用本 skill Mode 2，傳/接
  request-result contract，方法學判斷留在該 skill）。
- `references/tier-framework.md` §1 標頭：加註調用點（1.1/1.3/1.4/1.6 可整段委派）。
- `FUTURE-WORK.md` item ③：已調和並標記 HOOKED UP——主路徑改為本 skill（精準萃取），
  deep-research 降為次路徑（廣域偵察），並給出兩者選用準則。

### ~~7. `product-design-thinking` 的 prior-art 搜尋段落~~ ✅
- Phase 1 step 1 新增「formal-literature slice only」子項：正式學術文獻切面委派本 skill
  Mode 2；明確界定 OSS 盤點/競品/環境三步仍留在原 skill（本 skill 只管學術來源）。

## P3 — 品質驗證 ✅ 全數完成（2026-07-07）

### ~~8. 執行 config-self-audit~~ ✅ 已完成（2026-07-07）
- 已跑 config-self-audit：4 個 references/ 檔案 Test-Path 皆 true；無安全面（無 hook/
  無執行/無權限繞過，deliverable 只寫新檔、無 secrets）；語言規範通過（機讀檔全英文，
  中文僅出現於 description 範例句、output-templates 的 Mode 1 示例、人讀 TODO）。
- 修正 1 項：SKILL.md Reference map 前言原寫「Remaining planned reference files」但四檔
  皆已存在 → 改為「All four ship」（STATIC-VERIFY：`grep planned SKILL.md` = 0）。
- 未修正註記：deep-research 為 plugin skill，其 description 無法在此加反向消歧，已由
  trigger-dict + 本 skill「Do NOT trigger」句覆蓋；SKILL.md 222 行略超 150 軟上限
  （output catalog 表與 output-templates.md 部分重疊，經判斷保留為 inline 快查，列為
  可選未來精簡項）。
- 稽核紀錄已附至 `~/.claude/Global_skill_update.md`。

### ~~9. Evals（比照 scientific-research-guide 的 evals/ 目錄）~~ ✅ 已完成（2026-07-07）
- 已建立 `evals/evals.json`（比照 scientific-research-guide 格式，assertions 帶
  passed/evidence 欄位待實跑填入）：
  - eval 1 — Mode 1 直接請求（SPP 降損方法比較）→ 檢查 comparison matrix + 每格引用 +
    數值帶條件 + gaps/confidence 段落 + 零捏造。
  - eval 2 — Mode 2 服務調用（模擬 scientific-research-guide 傳 Drude gamma 參數請求）→
    檢查服務模式不回問使用者 + result contract 五欄位齊全（含 search_trail）+ 英文機讀。
  - eval 3 — 反幻覺（問 Johnson & Christy 1972 中不存在的熱導率值）→ 檢查回報 gap、
    不捏造數值、正確描述該論文實際涵蓋範圍。
  - eval 4 — 觸發準確度負向控制（「review 這段 code」）→ 檢查本 skill 不誤觸發、應路由到
    code-review 家族。
- ~~註：assertions 的 passed 欄位尚未實跑填值~~ ✅ 已實跑（2026-07-10）：每個 eval 各派
  一個 sonnet subagent 執行（evals 1–3 實際上網檢索；eval 4 以 routing-arbiter 代理測試），
  主 session 逐條評分回填 → **4/4 evals、16/16 assertions 全數通過**，證據見 evals.json。

## P5 — 韌性與偏誤補強 ✅ 全數完成（2026-07-10，外部檢視回饋觸發）

外部檢視點名的缺口，經確認後修正（生態整合被點名「未完成」屬過時指控——items 5–7
的三處掛接以 grep 驗證均已存在）：

### ~~10. 韌性與 session 經濟（SKILL.md 新增 Resilience & session economy 節）~~ ✅
- context/token 預算（>~10 篇 [full] 前警告 + 分批萃取筆記化）、重用先於重搜
  （舊 deliverable 作 seed、UPDATE run 輸出新檔並註明差異＝版本感知）、
  partial failure 回傳可續跑契約（gaps + search_trail 為 resume seed）、
  迴饋迭代（只重跑 P1 目標清單 + 受影響的 P4→P5，不整條重來）。

### ~~11. 降級階梯 + 成本透明 + 非英文文獻（search-sources.md 新增兩節）~~ ✅
- 四層降級階梯（keyed API → free API → WebSearch/WebFetch → prism-only）、
  rate-limit 不重試迴圈規則、成本透明（動用個人 key/polite pool 須記入 search_trail）。
- 非英文策略：雙語查詢、CNKI（摘要免費/全文付費牆）與 J-STAGE/CiNii（大量 OA）
  管道定位、原文萃取+契約語言交付、rubric 同標準適用（管道事實 2026-07-10 web 驗證）。

### ~~12. 偏誤檢查（credibility-rubric.md 新增 §6 set-level bias check）~~ ✅
- citation bubble（獨立種子測試）、群集集中度、地理/語言偏斜、正結果偏斜；
  SKILL.md failure mode #7 同步收錄。exhaustive 深度在契約中誠實標註
  「PRISMA 流程未出貨，以加寬版 standard 執行」（P4 item 維持延後）。

## P4 — 可選強化 ✅ 全數完成（2026-07-10，使用者指示補齊）

### ~~13. PRISMA 級 `exhaustive` 深度完整流程~~ ✅
- 新增 `references/exhaustive-prisma.md`（僅 exhaustive 深度載入）：E0 protocol 先行
  （納入/排除準則在檢索前固定）、E1 檢索紀錄表（含死路查詢）、E2 兩段式篩選
  （六種排除代碼，全文不可得＝E4 進 gaps 而非內容排除）、E3 流程計數表（數字須自洽）、
  E4 全來源升級查核（rubric/撤稿/引文追蹤 2-hop 全量化）、E5 交付物新增段 + 飽和聲明。
- 範疇誠實條款：明示這是 PRISMA-style 可追溯檢索萃取，非人工系統性回顧（無雙盲
  雙審、無 meta-analysis）；執行前強制預算警告。
- SKILL.md depth 契約、Reference map（four→five）已同步；eval 5（exhaustive 結構測試，
  Bi₂Se₃ WAL HLN α 前置因子）已加入 evals.json 並實跑評分。

### ~~14. 本地 PDF 庫支援~~ ✅
- `references/search-sources.md` 新增 Local PDF library 管道節：先盤點建索引再萃取、
  `[full]` 存取層級、線上識別碼/撤稿仍須查核（本地檔證明內容非書目正確性）、
  收藏偏誤須補網路管道並記入 search_trail、prism 排序 + 讀原檔組合用法。
- 無 fixture PDF 可自動測試 → 列 MANUAL-VERIFY：下次使用者以本地資料夾調用時驗收。
- 使用者說明文件 `PDF-GUIDE.md`（繁中人讀：觸發方式、執行行為、限制、驗收狀態）
  已於 2026-07-10 新增；與機讀規則出入時以 search-sources.md 為準。

## P6 — 語意契約小補丁 ✅ 全數完成（2026-07-11，update-plan v2）

外部 AI 檢視（讀到 `.agents\` 過時副本）提出 12 項問題，經對照 live 版逐項裁決：
8 項已失效/誤判（詳見 `literature-search-extract-update-plan-v2.md` §0.1），
3 項半成立並以最小補丁修正：

### ~~15. 來源路由（SKILL.md P2 開頭）~~ ✅
- 新增 route-first 規則：source-provided（不自動擴張搜尋）/ discovery（預設）/
  mixed（search_trail 區分 supplied vs discovered）。
- `search-sources.md` 檔頭同步標注僅適用 discovery/mixed。

### ~~16. 澄清策略分流（SKILL.md Mode 1）~~ ✅
- ONE question 僅限會改變搜尋範圍或 extraction targets 的歧義；
  純格式歧義不阻斷（依 catalog Use-when 推定，預設 inline summary，交付後才提轉換）。

### ~~17. 檔案輸出授權（SKILL.md P5 + output-templates.md）~~ ✅
- 預設 inline；僅使用者/caller contract 明確要求時寫檔；內容長度不構成寫檔理由。

### ~~18. Eval 6（source-provided）與 eval 7（file authorization）~~ ✅ 已實跑（2026-07-11）
- 使用者授權後各派一個 haiku subagent 實跑，主 session 評分回填：
  - Eval 6：4 條中 3 條通過；「全文萃取」1 條因 Science 付費牆不可演練（留 null），
    但降級行為全對（[abstract] 標籤、拒絕重建、不補料、不建檔、不搜額外文獻）。
    後續重測建議改用 open-access 指定來源或本地 PDF。
  - Eval 7：3/3 通過（inline 交付含 gaps/confidence、零建檔、零格式回問）。
    品質備註：haiku 層引用標籤偶有粗糙（PMC ID 當引用標籤），已記入 evidence。

### 19.（候選，待使用者決定）分享版打包 portability pass
- 若日後要對外分享本 skill：generalize P2/search-sources 的 prism 字樣為 provider-neutral
  local-corpus slot（例：prism / Zotero MCP / Obsidian vault MCP, if available）、
  移除 frontmatter 的 trigger-dict 引用、剔除個人檔案（TODO/PDF-GUIDE/update-plans/
  sample-run），只出貨 SKILL.md + references/ + evals.json。核心 fallback 已存在
  （prism「if available」+ 查無不等於不存在 + 降級階梯），不需為此改功能。

否決不做（記錄防止重提）：exhaustive→extended 更名（會刪除已出貨 PRISMA 能力）、
evidence_core schema、frontmatter 重寫、capability-aware handoff（屬 interop 層職責）。

## 維運紀錄（2026-07-12）

- 兩份 update-plan（原版 + v2）已全數執行完畢，封存至
  `~/.claude/archive/2026-07-12-lse-update-plans/`（含 ARCHIVE-NOTE.md）。
- 未結項僅剩 item 19（分享版打包，待使用者決定）。
- `.agents\skills\` 副本：查證發現已於 2026-07-11 11:39 被重新同步（與 live 版一致），
  非 plan v2 §2 所述的 07-08 過期狀態；是否封存改由使用者裁決，本輪未動。

## P7 — 可攜層 + 搜尋供應商補丁 ✅（2026-07-12，使用者授權）

### ~~20. search-sources.md 供應商補丁~~ ✅
- 降級階梯新增 3b「extraction fallback」（WebFetch 讀不動 → Tavily extract /
  Exa contents / 自架 Firecrawl，if-available slot 邏輯比照 prism）。
- 新增 general-web providers 事實表（2026-07-12 web 驗證）：Tavily 1000/月免費屬實；
  Brave 免費層 2026-02 已取消；DDGS 標註 best-effort 非官方爬蟲（禁標 unlimited）；
  Exa 月額度需綁卡；Firecrawl AGPL 可自架。

### ~~21. `references/portability.md`（能力自評可攜層）~~ ✅
- 任何 agent / 網頁 LLM 執行本 skill 前先跑能力盤點：7 個 capability slots
  （web_search / page_fetch / extract_render / local_corpus / pdf_read / file_write /
  subagent_dispatch）× 替代綁定 × 降級行為；最低可行 profile 判準（三者取一，
  全無則拒跑不捏造）；profile 與降級一律記入交付物；零捏造等不變量不隨能力降級。
- Claude 專屬機制（trigger-dict、跨 skill handoff、MCP 工具名）明文標記為
  ignore-don't-emulate；副本修改須登記 README-PROVENANCE adaptation log。
- SKILL.md Reference map 同步（five→six，新增 READ-FIRST-outside-Claude 條目）。
- 裁決註記：plan v2 曾否決「capability-aware handoff 進 skill 本體」；本輪經使用者
  明示指示（2026-07-12）以獨立 reference 檔形式實作，不佔 SKILL.md 本體，
  原否決的精神（本體防膨脹）維持。
- 同步：本 skill 目錄已重新同步到 `~/.agents/skills/` 與 `~/.codex/skills/`
  （兩處 README-PROVENANCE 的 sync 紀錄同步更新）。
- 未實跑驗證：portability 自評流程需在非 Claude 環境（如 codex）實測，
  列 MANUAL-VERIFY —— 下次 codex 調用本 skill 時驗收。
