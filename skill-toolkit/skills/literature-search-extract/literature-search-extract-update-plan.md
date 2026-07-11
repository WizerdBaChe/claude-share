# `literature-search-extract` 更新規劃

> 文件狀態：規劃已確認，尚未實作  
> 建立日期：2026-07-11  
> 目標 skill：`<local-workspace>/skills/literature-search-extract`  
> 本文件只定義後續修正內容、驗證方式與停止條件，不授權立即修改 skill。

## 1. 背景與問題定義

`literature-search-extract` 已具備完整的學術來源搜尋、來源可信度判斷、定向萃取、引用定位、缺口揭露及多種輸出模板。核心需求已經滿足，不需要重寫成新的研究系統。

目前需要處理的是語意契約與實際能力不完全一致：

1. 「SERVICE」容易被誤解為只能附屬於 `scientific-research-guide` 等其他 skill，沒有充分表達它可由使用者直接啟用。
2. Direct mode、Service mode、直接回答、結構化內容及檔案輸出的關係不夠明確。
3. 現行流程固定經過搜尋階段，沒有正式區分「使用者已提供來源」「需要搜尋新來源」及「以指定來源為核心再補充搜尋」。
4. 請求的研究目的不清楚與單純輸出格式不清楚，目前使用相同的澄清策略，可能造成不必要的中斷或事後重工。
5. 搜尋與輸出格式耦合，缺少格式中立的證據核心，使用者若稍後改變格式，可能需要重做整理。
6. `exhaustive (PRISMA-style)` 超過目前已實作的系統性回顧能力。
7. 檔案輸出規則可能被解讀為 agent 可自行決定建立文件。
8. `full citation traceability` 對 abstract-only 或 secondary sources 的表述過強。
9. Claude 端內建的 `deep-research`、`marketing:competitive-brief` 在 Codex 環境不存在屬正常跨平台差異，現行文字缺少 capability-aware handoff 規則。
10. Reference map、TODO 狀態及實際檔案完成度不一致。
11. Frontmatter 與 `SKILL.md` 本體偏長，部分細節與 references 重複。
12. 尚缺針對觸發、澄清時機、來源路由、輸出授權及跨 skill 邊界的行為驗證案例。

## 2. 已確認的目標定位

更新後的核心定位為：

> 一個可獨立運作、具有 Direct mode 與 Service mode 的學術證據搜尋及定向萃取 skill。它可以直接回答使用者，也可以向其他已啟用的 skill 提供結構化證據；它負責報告正式學術來源說了什麼，不負責替使用者設計研究、做研究決策、持久化錄入資料或管理完整系統性回顧。

英文語意基準：

> A standalone-capable, dual-entry scholarly evidence retrieval and targeted extraction skill. It may answer users directly or provide structured evidence to another active skill. It reports what scholarly sources say; it does not design the user's study, make research decisions, perform persistent data entry, or manage an entire systematic review.

### 2.1 Direct mode

使用者可直接要求：

- 搜尋某個主題的 papers、preprints、textbooks、monographs 或 standards。
- 閱讀及萃取使用者提供的單篇或多篇來源。
- 整理定義、分類、方法、protocol、參數、數值、方程式、限制、矛盾或研究現況。
- 產出 inline summary、annotated bibliography、evidence table、method summary、parameter sheet、comparison matrix 或 quote pack。

Direct mode 預設回覆人類可讀內容，不顯示不必要的機器 contract 外殼。

### 2.2 Service mode

當其他 skill 需要「正式學術來源實際說了什麼」時，可依 request contract 啟用本 skill。Service mode 回傳穩定 result contract，供上層 skill 繼續推理或建構其交付物。

這是同一 agent 套用多份 skill 指令時的協作契約，不宣稱存在正式的自動 RPC 或固定的 skill-to-skill 呼叫機制。

### 2.3 與 `scientific-research-guide` 的邊界

- 問「文獻說什麼」：`literature-search-extract` 主導。
- 問「我的研究應該怎麼做」：`scientific-research-guide` 主導。
- 同時包含兩者：`scientific-research-guide` 負責整體研究判斷，`literature-search-extract` 只負責具體證據搜尋與萃取。
- 本 skill 可標記跨來源綜合為 `[synthesis]`，但不得把綜合結果偷渡成研究方法建議。

本次只修正 `literature-search-extract` 自己的邊界文字，不修改 `scientific-research-guide`。

## 3. 防膨脹硬限制

本次更新必須同時符合以下限制：

- 不建立新的 skill。
- 不新增資料錄入、資料庫寫入、Zotero、Excel、CSV upsert 或其他持久化能力。
- 不新增 PRISMA workflow、篩選狀態機、risk-of-bias、meta-analysis 或 systematic-review orchestrator。
- 不新增 scripts。
- 不新增 references。
- 不修改其他 skill。
- 不重新設計搜尋來源生態系。
- 不因 skill-creator 將 `agents/openai.yaml` 列為推薦項就順手新增；目前沒有明確 UI metadata 需求。
- 不建立 README、CHANGELOG、設計說明或其他輔助文件。
- 除一份最小必要的 `evals/evals.json` 外，不新增測試輔助檔。
- 修改後 runtime 會載入的核心文字量不得高於修改前，並以縮短 `SKILL.md` 為目標。
- 核心修正完成且驗收通過後立即停止，不延伸鄰近功能。

## 4. 預計變更檔案

### 4.1 必須修改

1. `<local-workspace>/skills/literature-search-extract/SKILL.md`
2. `<local-workspace>/skills/literature-search-extract/references/output-templates.md`
3. `<local-workspace>/skills/literature-search-extract/references/search-sources.md`
4. `<local-workspace>/skills/literature-search-extract/TODO.md`

### 4.2 必須新增

1. `<local-workspace>/skills/literature-search-extract/evals/evals.json`

### 4.3 原則上不修改

1. `references/extraction-playbook.md`
2. `references/credibility-rubric.md`

只有最終語意檢查發現直接衝突的舊術語時，才允許對上述兩檔做最小文字同步；不得藉此擴充內容。

## 5. `SKILL.md` 修正設計

### 5.1 精簡 frontmatter

Frontmatter 只保留：

- standalone-capable、dual-entry 的核心能力。
- Direct mode 的具體觸發情境。
- Service mode 的觸發情境。
- 正式學術來源與定向萃取的能力範圍。
- 與研究方法建議、廣域一般調查及市場情報的核心消歧。
- capability-aware handoff 原則。

移除：

- 過長的輸出格式列舉。
- P1–P5 操作細節。
- 可移至 body 或 references 的範例。
- 把特定 caller 描述成固定或唯一入口的文字。

### 5.2 重寫 Operating stance

保留並精簡以下 hard constraints：

- 只報告來源可支持的內容。
- 不捏造 citation、DOI、作者、頁碼、數值或引文。
- 來源存取層級必須誠實。
- 自身推論必須標記 `[synthesis]`。
- 尊重著作權與付費牆。

將 `full citation traceability` 改為：

> Every load-bearing claim must be traceable to the material actually accessed, with an explicit access level and the most precise available locator.

Locator 精度依來源狀態分級：

- `[full]`：頁碼、section、table、figure、equation 等可重新定位資訊。
- `[partial]`：實際可讀片段的精確範圍。
- `[abstract]`：只標示 abstract，不假裝已讀 Methods 或 Results。
- `[secondary]`：明確標示 as cited in。

### 5.3 建立前置智慧判定

完整搜尋前先判斷未決資訊是否會改變：

- 搜尋範圍。
- Extraction targets。
- 比較條件或 decision criteria。
- 來源類型。
- 時間、領域或 venue 限制。
- 工作深度。

如果會實質改變上述內容：

1. 不先執行完整搜尋。
2. 必要時只做低成本術語或來源預查。
3. 說明目前理解。
4. 只問一個真正會改變工作方向的問題。
5. 使用者回答後再建立完整 evidence core。

如果只影響呈現形式：

1. 不阻斷工作。
2. 建立 evidence core。
3. 依任務動詞推定 renderer。
4. 沒有單一合理 renderer 時，預設 inline summary。
5. 只有替代格式具實際價值且不需重新搜尋時，才在交付核心結果後詢問是否轉換。

### 5.4 新增來源路由

在主流程前明確選擇一條路徑：

#### Source-provided path

- 使用者已提供或明確指定來源。
- 先驗證來源身分與可讀範圍，再直接 triage/extract。
- 不主動搜尋其他文獻。
- 只有使用者要求補充、來源版本需核對，或核心缺口無法由指定來源回答時，才提出 mixed path。

#### Discovery path

- 使用者要求尋找新來源。
- 依 P1 targets 建立查詢，執行搜尋、triage、extraction、synthesis。

#### Mixed path

- 指定來源作為核心，再搜尋 published version、correction、supplementary、前後引文或缺漏資訊。
- Search trail 必須區分使用者提供來源與新增發現來源。

### 5.5 建立格式中立 Evidence Core

搜尋和萃取的內部結果統一為：

```text
evidence_core:
  interpreted_question
  extraction_targets
  source_records
  extracted_items
  locators
  access_levels
  gaps
  conflicts
  confidence
  search_trail
```

Evidence core 是內部工作結構，不要求 Direct mode 原樣輸出，也不另建 schema 檔或 validator script。

### 5.6 Renderer 智慧映射

| 任務語意 | 預設 renderer |
|---|---|
| 找幾篇、閱讀清單、代表性文獻 | Annotated bibliography |
| 摘要、重點、快速說明 | Inline summary |
| 方法、protocol、重現步驟 | Method summary |
| 參數、數值、典型值 | Parameter sheet |
| 比較方法、材料、模型 | Comparison matrix |
| 證據是否支持某主張 | Evidence table |
| 原文定義、標準條文、精確措辭 | Quote pack |
| 供其他 skill 使用 | Result contract |

若比較標準不清楚且不同標準會改變 extraction targets，必須在完整搜尋前詢問；不得先建立可能方向錯誤的 comparison matrix。

### 5.7 輸出與寫檔規則

Direct mode：

- 預設 inline 回答。
- 自然呈現 sources、gaps、confidence，不包裝成不必要的機器 contract。
- 使用者明確要求 JSON、固定欄位或 contract 時，才輸出 machine-consumed structure。

Service mode：

- 維持穩定欄位：`findings`、`sources`、`gaps`、`confidence`、`search_trail`。
- Partial failure 仍回傳相同欄位，失敗與缺漏放入 `gaps`。

File artifact：

- 只有使用者或 caller contract 明確要求檔案時才建立。
- 不因內容較長而自行寫檔。
- 寫檔時建立新檔，不覆寫既有報告。

### 5.8 搜尋深度

將：

- `quick`
- `standard`
- `exhaustive (PRISMA-style)`

改為：

- `quick`
- `standard`
- `extended`

並加入：

> Extended search is not, by itself, a systematic review or a PRISMA-compliant process.

`extended` 可增加：

- 搜尋管道覆蓋。
- Citation chasing 深度。
- Load-bearing sources 的可信度檢查。
- Search trail 完整度。

但不得包含完整 systematic-review governance。

### 5.9 Capability-aware handoff

對 `deep-research`、`marketing:competitive-brief` 等 Claude 端內建能力採條件式文字：

- 對應能力存在時可具名轉交。
- 不存在時不把它判成 skill 配置錯誤。
- 不聲稱一定能自動呼叫。
- 若目前環境沒有替代 skill，僅說明本 skill 的邊界，並依現有能力繼續處理或向使用者揭露限制。

## 6. References 同步設計

### 6.1 `output-templates.md`

更新內容：

- Direct mode 與 Service mode 的呈現差異。
- Evidence core 與 renderer 的關係。
- Inline default。
- File artifact 的明確授權門檻。
- Comparison criteria 不清楚時的先問規則。
- Mode 2 穩定欄位不變。
- `purpose_echo` 可繼續保持 optional，不升級成必填欄位。

不新增 output format，不建立新的 template reference。

### 6.2 `search-sources.md`

更新內容：

- 只有 Discovery path 與 Mixed path 執行搜尋。
- Source-provided path 不自動擴張文獻集合。
- `exhaustive` 全面改為 `extended`。
- Standard 與 Extended 的 citation-chasing 深度和停止條件。
- prism 或特定 scholarly channel 不存在時的正常降級。
- Search trail 必須記錄使用、跳過、不可用或失敗的管道。

本次不重新驗證外部 API 版本、配額或服務政策；只有實作時遇到現行管道行為與文件衝突，才依既有規則另行查證。

### 6.3 `extraction-playbook.md`

預設不修改。只有出現以下情況才允許最小修正：

- 舊詞彙直接引用 `exhaustive` 或 PRISMA-style。
- 範例與新的 access/locator 語意直接矛盾。
- 範例暗示 source-provided path 必須額外搜尋。

### 6.4 `credibility-rubric.md`

預設不修改。只有深度名稱或明確流程引用衝突時才做文字同步，不重寫可信度評分方法。

## 7. TODO 精簡策略

`TODO.md` 更新為英文的精簡 pending-work list，符合 machine-read 文件語言規則。

保留：

- Caller-side integration 是否未來同步到 `scientific-research-guide` 或其他 caller skill。
- 是否授權獨立 fresh-agent forward-test。
- 只有實際需求出現時才考慮的 local corpus 支援。

移除：

- 已完成 references 的歷史明細。
- 已完成的 trigger dictionary 註冊項。
- 不再屬於本 skill 的 PRISMA exhaustive 規劃。
- 本次修正完成後已不再 pending 的項目。

TODO 不作為 changelog，不保存所有歷史過程；如需保留舊內容，實作前依環境規則建立備份，不在 skill 內新增歷史檔。

## 8. 最小 Eval 設計

只新增 `evals/evals.json`，沿用 `scientific-research-guide/evals/evals.json` 的精簡結構：

- `skill_name`
- `evals[]`
- `id`
- `prompt`
- `expected_output`
- `files`
- `assertions[]`

不放完整理想回答，避免 eval 洩漏預期答案。

### Eval 1：清楚的直接搜尋

Prompt 類型：查某個明確參數的文獻值。

Assertions：

- 不詢問已能推定的 output format。
- 推定 parameter sheet 或精簡 inline table。
- 每個數值包含條件與 locator。
- 不自行建立檔案。

### Eval 2：會改變搜尋內容的模糊請求

Prompt 類型：「幫我整理 SPP waveguide 文獻。」

Assertions：

- 完整搜尋前只問一個高價值問題。
- 問題針對目的、比較軸或 extraction targets。
- 不先產出虛假的完整回顧。

### Eval 3：Source-provided path

Prompt 類型：只整理使用者提供論文的 Methods 與 Limitations。

Assertions：

- 不自動搜尋額外文獻。
- 從 Methods、Supplementary、Discussion/Limitations 萃取。
- 清楚標記指定來源未提供的資訊。

### Eval 4：Mixed path

Prompt 類型：以指定 preprint 為核心，確認是否有正式出版版或勘誤並補足限制。

Assertions：

- 保留指定來源為核心。
- 搜尋 published version、correction 或 supplementary。
- Search trail 區分 supplied 與 discovered sources。

### Eval 5：只有格式不明

Prompt 類型：任務內容明確但沒有指定表格或文章格式。

Assertions：

- 不在完整搜尋前詢問純呈現問題。
- 建立 evidence core 後使用合理預設 renderer。
- 只有替代格式有實際價值時才在結果後提出轉換選項。

### Eval 6：檔案授權

Prompt 類型：要求整理多篇論文但未要求建立報告。

Assertions：

- 直接 inline 回答。
- 不自行建立文件。
- 只有使用者明確要求 file artifact 才寫檔。

### Eval 7：Service mode contract

Prompt 類型：模擬 caller skill 傳入完整 request contract。

Assertions：

- 不重複向使用者詢問可合理預設的欄位。
- 回傳 `findings`、`sources`、`gaps`、`confidence`、`search_trail`。
- Partial failure 不改變 contract shape。

### Eval 8：研究方法邊界

Prompt 類型：詢問自己的研究應採用什麼方法，同時要求相關文獻證據。

Assertions：

- 辨認整體任務應由 scientific research advisory 主導。
- 本 skill 只負責來源搜尋與證據萃取。
- 不自行替使用者做研究設計決策。

### Eval 9：Extended 深度

Prompt 類型：要求較廣泛的 scholarly search，但沒有提供 systematic-review protocol。

Assertions：

- 可採 extended depth。
- 提供較完整 search trail 與 citation chasing。
- 不聲稱 PRISMA-compliant。
- 不自行建立納入排除流程或 PRISMA flow。

### Eval 10：跨平台 handoff

Prompt 類型：請求廣域一般調查或市場競品情報。

Assertions：

- 說明不屬於 formal scholarly extraction 的核心範圍。
- 對應 skill 存在時可具名轉交。
- 對應 skill 不存在時不宣稱配置損壞或自動呼叫成功。

## 9. 實作順序

1. 在允許修改的環境中建立原 skill 備份；不覆寫既有備份。
2. 先重寫 `SKILL.md` frontmatter、角色與 invocation/output 路由。
3. 重構來源路由、evidence core、renderer、file authorization 與深度語意。
4. 同步 `output-templates.md`。
5. 同步 `search-sources.md`。
6. 以語意 grep 判斷另兩份 references 是否需要最小同步。
7. 精簡 `TODO.md`。
8. 新增 `evals/evals.json`。
9. 執行靜態與格式驗證。
10. 執行 `config-self-audit`。
11. 若另獲使用者明確授權，再使用 fresh subagent 做獨立 forward-test；未授權時不得啟動。
12. 只修正此次變更引入或直接暴露的問題，驗收成立後停止。

## 10. 靜態驗證

### 10.1 結構與存在性

- `SKILL.md` frontmatter 只有 `name` 與 `description`。
- 所有 `references/` 路徑存在。
- `evals/evals.json` 是有效 JSON。
- 沒有新增不在規劃內的檔案或資料夾。

### 10.2 語意 grep

以下舊語意應歸零或只存在於明確的否定說明：

- `exhaustive`
- `PRISMA-style`
- `Remaining planned reference files`
- 未經明確要求就寫 standalone document 的指令
- 把某個具名 skill 描述成必然存在或必然可呼叫的文字

以下新語意必須可定位：

- `standalone-capable`
- `Direct mode`
- `Service mode`
- `source-provided`
- `discovery`
- `mixed`
- `evidence core`
- `extended`
- `file artifact`
- `explicitly requests`
- capability-aware handoff

### 10.3 Contract 相容性

Mode 2 必須繼續包含：

- `findings`
- `sources`
- `gaps`
- `confidence`
- `search_trail`

不得因重構而任意改名或刪除。

### 10.4 官方 validator

優先使用 bundled workspace Python 執行 `skill-creator/scripts/quick_validate.py`，不自行安裝套件。

若仍因缺少 `PyYAML` 無法執行：

- 如實記錄為 validator environment blocker。
- 不將它誤報為 skill 格式失敗。
- 補做 frontmatter delimiter、必要欄位、名稱與路徑的靜態檢查。

## 11. 防膨脹驗收

實作完成前必須逐項確認：

- `SKILL.md` body 目標約 150 行以內；若略超過，必須能說明每段為何屬於核心執行規則。
- Frontmatter 顯著短於目前版本。
- 修改後 runtime-loaded 核心文字量不高於修改前。
- 沒有新增 references。
- 沒有新增 scripts。
- 沒有新增新 skill。
- 沒有新增 `agents/openai.yaml`。
- 沒有修改 `scientific-research-guide`、`product-design-thinking` 或其他 caller skill。
- 沒有加入 persistent data ingestion。
- 沒有加入 PRISMA orchestration。
- 沒有加入 meta-analysis 或 statistical synthesis。
- Eval 檔只測試本次語意，不擴張能力範圍。

任一項不符合，先縮減變更，不以「未來可能有用」作為保留理由。

## 12. 行為驗證與限制

### 12.1 可在一般實作中完成

- 靜態文字與路徑檢查。
- JSON/YAML 格式檢查。
- Contract 欄位檢查。
- Reference existence check。
- 文字量與行數比較。
- `config-self-audit`。

### 12.2 需要另行授權

真正獨立的 behavioral forward-test 必須由 fresh agent 在不知道預期修正答案的情況下執行。依目前協作規則，未獲使用者明確要求前不得啟動 subagent。

若未授權：

- 可建立 eval cases。
- 可完成靜態驗證。
- 最終不得聲稱 behavioral eval 已通過。

若獲授權：

- 使用原始 prompt 與更新後 skill，不向測試 agent 洩漏診斷或預期修法。
- 檢查實際輸出與 assertions。
- 只根據真實失敗修正 skill。
- 不為通過單一案例加入特例；同類例外達三個時應重新檢查抽象設計。

## 13. Definition of Done

只有以下條件全部成立，才能宣告更新完成：

1. 雙入口定位清楚，Direct mode 與 Service mode 地位相同。
2. 使用者可直接搜尋、閱讀、萃取及取得結構化內容。
3. Source-provided、Discovery、Mixed 三條路徑明確。
4. 內容歧義會在完整搜尋前詢問；純格式歧義不造成不必要中斷。
5. Evidence core 與 renderer 分離。
6. Direct mode 預設人類可讀回答，Service mode 維持穩定 contract。
7. 未明確要求檔案時不寫檔。
8. `extended` 不冒充 PRISMA 或完整 systematic review。
9. Citation traceability 與實際 access level 一致。
10. Claude/Codex 跨平台 handoff 不假定所有具名 skill 都存在。
11. Reference map、TODO 與實際檔案狀態一致。
12. Eval cases 覆蓋已確認的核心邊界。
13. 所有可執行的靜態驗證通過；任何被環境阻擋的驗證均如實記錄。
14. 防膨脹驗收全部通過。
15. 沒有修改規劃範圍外的 skill 或功能。

## 14. 停止條件

達成 Definition of Done 後立即停止。以下項目一律留待獨立需求，不在本次更新中順手處理：

- `scientific-research-guide` 的 caller-side 雙向掛接。
- `product-design-thinking` 的 prior-art 整合。
- 資料錄入 skill。
- Local PDF corpus 管理。
- Systematic review orchestrator。
- Citation audit skill。
- Meta-analysis 或 evidence synthesis。
- UI metadata 或 marketplace packaging。

若實作過程發現上述項目確有價值，只記入後續候選，不修改本次承諾範圍。

## 15. 本文件的授權邊界

本文件是完整更新規劃，不代表已授權實作。後續只有在使用者另行要求開始實作後，才能修改目標 skill。Subagent forward-test、外部套件安裝、其他 skill 修改及任何範圍擴張均需另外取得明確授權。
