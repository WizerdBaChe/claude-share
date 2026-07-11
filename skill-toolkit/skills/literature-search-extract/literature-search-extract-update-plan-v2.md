# `literature-search-extract` 更新規劃 v2（修正版）

> 文件狀態：規劃已修正，尚未實作
> 建立日期：2026-07-11
> 取代：`literature-search-extract-update-plan.md`（原版保留供對照，不再作為實作依據）
> 目標 skill：`<local-workspace>/skills/literature-search-extract`（live 正典）
> 本文件只定義修正內容與驗證方式，不授權立即修改 skill。

## 0. 對原計劃的總判定

原計劃評估的對象是 `<local-workspace>/skills/literature-search-extract` —— 一份
**2026-07-08 的過時原始副本**。live 版（`.claude\skills`）在 2026-07-10 已完成
P4/P5 兩輪補強（commits `792b857`、`38d7b96`、`8ba63a4`），原計劃列出的 12 項問題中
**8 項已失效或誤判**，僅 3 項半仍然成立，且都只需小補丁，不需要原計劃規模的重構。

### 0.1 逐項裁決

| 原計劃問題 | 裁決 | 依據（live 版現況） |
|---|---|---|
| 1. SERVICE 易被誤解為僅附屬 | 大致失效 | frontmatter 已列直接觸發句型在前；Mode 1 明確定義；trigger-dict 已註冊 |
| 2. Direct/Service 關係不明 | 失效 | Invocation modes 節已分立定義兩模式與各自輸出語言 |
| 3. 缺來源路由（已提供 vs 需搜尋） | **成立** | pipeline 固定經過 P2 搜尋，「這篇 paper 的重點」情境無跳過搜尋的明文規則 |
| 4. 目的歧義與格式歧義同一澄清策略 | **成立（半）** | Mode 1 的 ONE question 允許拿格式當提問對象，可能造成不必要阻斷 |
| 5. 缺格式中立 evidence core | 失效 | P1 target list → P4 extracted items（含 locator）→ P5 render 已是結構分離；Feedback iteration 節明文只重跑受影響的 P4→P5 |
| 6. exhaustive 超出已實作能力 | **失效（反向危險）** | `references/exhaustive-prisma.md` 已於 07-10 出貨，含範疇誠實條款與預算警告，eval 5 實跑通過。改名 `extended` 會**刪除已驗證能力**，必須否決 |
| 7. 寫檔規則可被讀成 agent 自行決定 | **成立（半）** | P5 的「If the deliverable is a standalone document, write a NEW file」未寫明由誰決定產生檔案 |
| 8. full citation traceability 對 abstract-only 過強 | 大致失效 | access-level 四級標籤（[full]/[partial]/[abstract]/[secondary]）已定義語意，frontmatter 是觸發摘要非規格文字 |
| 9. 缺 capability-aware handoff（Codex 無 deep-research） | **誤置範疇** | 跨平台可攜是 `~/.claude/interop/` 層的職責，且該層明文「永不直接複製原始 skill 檔」。live skill 只在 Claude 環境執行，具名 skill 均存在 |
| 10. Reference map/TODO 不一致 | 失效 | TODO.md 07-10 已全面更新，五個 references 與 map 一致 |
| 11. frontmatter/SKILL.md 偏長 | 失效 | frontmatter 已於 commit `347412c` 精簡（19 行→8 行）；body 222 行已經 config-self-audit 裁決保留並記錄理由 |
| 12. 缺 evals | 失效 | `evals/evals.json` 已存在 5 條 eval，07-10 全數實跑通過（含 exhaustive 結構測試） |

### 0.2 原計劃提案的明確否決清單

以下提案不得實作，理由如上表：

- `exhaustive` → `extended` 更名（§5.8）：會刪除已出貨、已驗證的 PRISMA-style 能力。
- `evidence_core:` 內部 schema（§5.5）：結構分離已存在，新 schema 只加術語不改行為。
- Frontmatter 全面重寫（§5.1）：已精簡並穩定，重寫增加 trigger 回歸風險。
- Capability-aware handoff 條文（§5.9）：屬 interop 層職責，不進 skill 本體。
- TODO.md 重寫為英文精簡清單（§7）：TODO 已最新；語言規則方面它是人讀維運文件，
  繁中可接受（若日後要改語言屬獨立小事，不綁進本計劃）。
- 新建 `evals/evals.json`（§8）：檔案已存在且有實跑紀錄；只允許**追加**，不得重建。
- Renderer 映射表（§5.6）：output format catalog 的「Use when」欄已承載同一資訊。

## 1. 本次實際要做的修正（全部為小補丁）

### 1.1 SKILL.md — 來源路由（對應原問題 3）

在 P2 開頭（或 Mode 1 之後）加入一小段（目標 ≤ 8 行）：

- **Source-provided**：使用者已提供/明確指定來源 → 驗證來源身分與可讀範圍後直接
  P3→P4，**不自動搜尋其他文獻**；只有使用者要求補充、需核對出版版本/勘誤，或指定
  來源無法回答核心 targets 時，才提議混合路徑。
- **Discovery**（現行預設）：需要尋找新來源 → 完整 P2。
- **Mixed**：指定來源為核心 + 定向補充搜尋；`search_trail` 區分 supplied 與
  discovered sources。

### 1.2 SKILL.md — 澄清策略分流（對應原問題 4）

修改 Mode 1 的 ONE-question 規則（目標 ≤ 4 行）：

- 只有**會改變搜尋範圍或 extraction targets** 的歧義（目的、比較軸、來源類型、
  時間/領域限制、深度）才在搜尋前提問，且仍只問一題。
- 純呈現形式歧義**不阻斷**：依任務動詞從 output catalog 推定格式，無明顯對應時
  預設 inline summary；只有替代格式具實際價值時，才在交付後提出轉換選項。

### 1.3 SKILL.md — 檔案輸出授權（對應原問題 7）

修改 P5 的寫檔句（1–2 行）：

- 預設 inline 回覆；只有使用者（Mode 1）或 caller contract（Mode 2）**明確要求**
  檔案交付物時才寫檔；寫檔一律新檔不覆寫（後半維持現文）。

### 1.4 References 條件式同步

- `output-templates.md`：在 Mode 1 語言規則附近加 1–2 行（inline 為預設、寫檔須
  明確要求）。
- `search-sources.md`：檔頭加 1 行（本檔僅適用 discovery/mixed 路徑；
  source-provided 路徑不自動擴張文獻集合）。
- `extraction-playbook.md`、`credibility-rubric.md`：預設不動；僅在語意 grep 發現
  與新路由直接矛盾的句子時做最小同步。

### 1.5 Evals — 追加 2 條（不重建）

在既有 `evals/evals.json` **追加**：

- **eval 6 — Source-provided path**：只整理使用者指定論文的 Methods 與 Limitations。
  Assertions：不自動搜尋額外文獻；從正確 section 萃取；指定來源未涵蓋處標記 gap。
- **eval 7 — 檔案授權**：要求整理多篇論文但未要求建立報告。
  Assertions：inline 回答；不自行建檔；僅在明確要求時寫檔。

沿用既有 eval 結構（assertions 帶 passed/evidence 欄位）；實跑須另獲 subagent
授權，未授權時 passed 留空並如實註記。

### 1.6 TODO.md — 追加而非重寫

完成後在 TODO.md 追加一節記錄本輪（路由/澄清/寫檔授權 + eval 6–7），不改動歷史段落。

## 2. 範圍外但須另行處置的發現

**`<local-workspace>/skills/` 含 11 份 2026-07-08 的原始 skill 副本（已過期）。**
這違反 interop 層「原始 skill 檔充滿 Claude 專屬引用，永不直接複製」的維運原則，
且正是本次原計劃誤判的根源（另一個 AI 讀到過時副本）。建議另開任務以 env-cleanup
規則處置（archive，非刪除），或若確認某外部 agent 需要 skill 內容，改走 interop
reference-compile 管道。**本計劃不動 `.agents\`。**

## 3. 防膨脹硬限制（沿用原計劃並收緊）

- 不建立新 skill、新 references、新 scripts、`agents/openai.yaml`、README/CHANGELOG。
- 不修改其他 skill；不加持久化/PRISMA orchestrator/meta-analysis（原計劃 §3 全數沿用）。
- SKILL.md 淨增行數 ≤ 15 行（1.1–1.3 合計）；若超出，先壓縮新文字而非刪既有內容。
- 不動 frontmatter description（trigger 已驗證，改動有回歸風險）。
- 核心修正完成且驗收通過後立即停止。

## 4. 實作順序

1. 備份現行 skill（`~/.claude/backups/`，不覆寫既有備份）。
2. SKILL.md 三處小補丁（1.1 → 1.2 → 1.3）。
3. References 條件式同步（1.4），以語意 grep 判定另兩檔是否需最小同步。
4. 追加 eval 6–7（1.5）。
5. TODO.md 追加記錄（1.6）。
6. 靜態驗證（§5）+ config-self-audit。
7. 若另獲授權，以 fresh subagent 實跑 eval 6–7；未授權則如實標記未實跑。
8. 驗收成立後停止。

## 5. 靜態驗證

- `SKILL.md` frontmatter 僅 `name`/`description` 且未被改動（diff 確認）。
- 新語意可定位：`source-provided`（或等義詞）、`discovery`、`mixed`、
  `explicitly requests`（寫檔門檻）、格式歧義不阻斷的規則。
- 舊語意不得出現：任何 `extended` 深度、`evidence_core` schema。
- `exhaustive` 與 `references/exhaustive-prisma.md` 引用**必須原樣保留**。
- Mode 2 result contract 五欄位（findings/sources/gaps/confidence/search_trail）不變。
- `evals/evals.json` 有效 JSON，既有 5 條 eval 與其 passed/evidence 未被改動。
- SKILL.md 淨增 ≤ 15 行。
- validator：優先 `skill-creator/scripts/quick_validate.py`；環境缺 PyYAML 時如實
  記錄為 environment blocker 並補手動 frontmatter 檢查（沿用原計劃 §10.4）。

## 6. Definition of Done

1. 三條來源路徑明文化，source-provided 不自動擴張搜尋。
2. 內容歧義先問一題；純格式歧義不阻斷。
3. 未明確要求檔案時不寫檔。
4. exhaustive/PRISMA 能力與既有 5 條 evals 完好無損。
5. 淨增行數與防膨脹限制全部通過；config-self-audit 通過。
6. `.agents\` 副本問題已向使用者回報（處置另開任務）。

## 7. 授權邊界

本文件是修正後規劃，不代表已授權實作。實作、subagent 實跑 eval、`.agents\` 清理
均需使用者另行指示。
