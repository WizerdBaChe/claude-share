# Skill Toolkit｜可攜式技能工具箱

> **中文摘要｜Chinese summary**：本層收錄 21 顆可攜式 AI-agent skills 與觸發關鍵詞
> 索引。每顆技能以 SKILL.md 定義用途與邊界，細節依需載入 references；這份 README
> 先幫你選對技能、判斷缺件，再進入個別 SKILL.md。
>
> **English summary**: This directory contains 21 portable AI-agent skills and the
> trigger dictionary. Each skill defines its scope in SKILL.md and loads supporting
> references on demand. Use this README to select a skill and understand exclusions
> before reading its implementation contract.

## 快速導覽｜Quick guide

| 項目 | 中文 | English |
|---|---|---|
| 適合誰 | 要選技能、審查技能可攜性或安裝一組 skills 的維護者 | Maintainers selecting, auditing, or installing skills |
| 入口 | 先看下面的情境索引，再讀目標資料夾的 SKILL.md | Use the scenario index, then read the target SKILL.md |
| 安裝 | 只保留 SKILL.md 與它明確引用的 repo-local references/assets | Keep SKILL.md and its explicitly referenced repo-local references/assets |
| 不包含 | agent executor、secrets、帳號設定、自動同步與來源端私有工具 | No executor, secrets, account settings, auto-sync, or source-private tools |

一組可攜式的 AI agent 技能 (skills) 與觸發關鍵詞索引。此分享適合用於審查、研究、產品設計、環境維護與工作階段管理；每項技能皆以 `SKILL.md` 定義其適用範圍與操作邊界。

## 設計重點｜Design principles

一般的 prompt 合集給你「一段話」，這套件給你的是**工程紀律**。三個貫穿全套件的共通設計：

1. **每顆技能都是路由＋參考檔分層**：`SKILL.md` 只做入口路由，細節放 `references/` 按需載入，不會把 agent 的上下文塞爆。
2. **規則都附強制機制**：不是「請注意 X」，而是「用這條檢查擋 X」——檢查項都標明驗證方式，結論可以被重跑驗證。
3. **有配套系統**：觸發字典負責消歧（教你怎麼提問才會命中對的技能）、更新紀錄採附加式不改寫，全程可稽核。

## 內容與技能索引｜Contents and skill index

- `skill-trigger-dict.md`：雙語觸發字典；用於在相近技能間消歧，並提供較能命中技能的提問句型。
- 更新紀錄已於 2026-08-07 上移至 repo 根目錄的 `Global_skill_update.md`：它記錄的是整個來源環境的變更（`ops/`、全域 `CLAUDE.md`、hooks 都包含在內），不只此技能組，放在這一層屬於歸錯檔。
- `skills/`：21 個可獨立閱讀及匯入的技能資料夾，以及它們所需的參考文件與評估資料。
  2026-10-02 新收錄三顆：`case-library`（同類案例流的分類→蒐集→量測→模仿→workflow）、
  `comsol-agent-pipeline`（COMSOL 6.2 無頭管線：路由、API 陷阱表、模式卡、腳本骨架；
  產生陷阱表的同步腳本綁在來源端的測試區，不出貨）、`pptx-review`（PowerPoint 註解迴圈）。
  來源環境共有 35 顆；未收錄的是十四顆——`asset-vault`，它操作一個寫死在本機磁碟路徑的
  私有素材庫，並把權威委派給該素材庫自己的（非公開）`AGENTS.md`，拆掉耦合之後只會剩下
  一份在描述你沒有的東西的說明；兩個知識包 `render-perf`、`system-design`，2026-08-17
  因來源端尚未成型而暫緩（半成品的知識包只會輸出一個沒有內容支撐的觸發字）；兩個
  機器綁定的包裝 `graph-query`、`media-fetch-pipeline`（2026-08-27 裁定：前者查詢的
  衍生圖譜、後者包裝的 `mfp` CLI 都只存在於來源機器上，殼出貨了也無從運作）；`post-brief`
  （2026-09-02 新增：它是 `mfp` CLI 與本機 `tools/post-brief` 的迴圈，兩者都不隨此包
  出貨，殼一樣無從運作）；`model3d-pipeline`（2026-09-02 owner 裁定暫緩出貨——
  它路由的整條 CAD 管線活在來源環境之外的另一個磁碟根目錄，晚一輪待管線調整完成後
  再透過 mechanism-share-packaging 路徑收錄）；2026-09-07 新增的四顆——
  `knowledge-vault`（與 `asset-vault` 同類：操作使用者本機的 Obsidian 知識庫，權威
  委派給該庫自己的非公開契約檔）、`app-residue-sweep`（殼在此、本體在來源環境的
  `tools/` 樹，與 `post-brief` 同型）、以及 `paper-distill`／`paper-story` 這對
  （2026-09-03 於來源端分家；其交付物與 `evals/` 是某個實驗室的模板、口吻與實際
  演講紀錄，屬於特定群體的內容而非可移植的方法，比照 `model3d-pipeline` 的
  「明講暫緩並寫下重看時機」處理）；以及 2026-09-12 新增的 `patents-grabber`
  （來源端 2026-09-11 新增：與 `media-fetch-pipeline`／`post-brief` 同型的薄殼，
  每個操作都呼叫另一顆磁碟根目錄上的獨立程式，憑證檔與圖檔快取也都在殼外）；以及
  2026-10-02 新增的兩顆——`motion-video`（2026-09-30 自 `motion-design` 拆出的整支影片
  router，證據與量測工具都留在來源端另一顆磁碟上的實驗室；它另以獨立分享包發行，不在
  此 repo）與第三個知識包 `code-layering`（2026-09-23 自 `system-design` 拆出）。
  **三個知識包（`render-perf`、`system-design`、`code-layering`）依 2026-10-02 使用者裁定
  一律不出貨**；代表它們的那一頁隨 `environment-guide/` 出——
  [`../environment-guide/KNOWLEDGE-PACKS.md`](../environment-guide/KNOWLEDGE-PACKS.md)
  記錄包的形狀、四條包層級判準（可登記／可依賴／可分享／拆包退役）與每個包的現況列；
  manifest 裡三個包條目的 review-when 都改指向該頁的「可分享」四條。`paper-distill`／
  `paper-story` 這對同樣另以獨立分享包發行。理由記在
  [`../tools/share-manifest.toml`](../tools/share-manifest.toml) 的 `[[not_shipped]]`，
  寫在這裡是為了讓「少十四顆」是講明的，不是被發現的。

| Skill | 用途 | 亮點 |
|---|---|---|
| `ai-coding-guardrails` | 設計 AI 協作的防護、審查與復原流程。 | 風險分級＋事故轉測試案例＋改動上限，把「AI 改壞 repo」從事後補救變成事前預防。 |
| `case-library` | **2026-10-02 新收錄。** 針對一「串」同類案例（影片、貼文、版面、UI 模式）建案例庫：分類→蒐集→特化分析→實測模仿→抽出可重複的 workflow。 | 八條不變量：受控詞彙＋驗證器自測、索引只能生成不能手改、未校準的儀器不准出數字、模仿是受控比較（≥3 次、區間不重疊才算效果）、「好不好看」只由使用者看片判定。參考實作是來源端的私有專案，SKILL.md 只以類別描述它。 |
| `comsol-agent-pipeline` | **2026-10-02 新收錄。** 以 Python（MPh）無頭驅動 COMSOL 6.2：依觀測量選模式卡→建模／載入種子→求解→讀回→以解析解閘門＋對照裁定 PASS／FAIL／UNDET。 | 每個數字帶來源標籤、每道閘門必附「必須觸發的對照」、106 條實測 API 陷阱（`references/api-rules.md`，來源端生成的快照）、16 張模式卡與腳本骨架。測試區（rig）本體與產生陷阱表的同步腳本不出貨，檔內已明講。 |
| `audience-fit` | 產出後的受眾調校：把工程口吻的成品改寫給非開發者讀者，或把 UI 文案從開發者視角換成使用者視角。 | 一份文件只服務一種主受眾＋改寫必須與原稿成對交付（前後對照），數據強度、因果語氣與限制不因改寫而變動。 |
| `code-review-deep-checklist` | 執行深入的程式、架構與依賴適用性審查。 | 三種模式（快掃／深審／架構）＋嚴重度合約，審查結論有固定格式不會漂移。 |
| `config-self-audit` | 稽核 agent 設定、hooks 與規則檔。 | 每條檢查項標明驗證方式（靜態檢查／人工確認分開標），稽核結論可重跑。 |
| `design-system-suite` | 為多產品建立契約優先的共享設計系統。 | 四份契約（tokens／資料信封／導覽／能力清單），多產品共用設計語言不走散。 |
| `diagram-authoring` | 把資料/設計文件/程式碼變成可視覺驗證的精準架構圖（方塊圖、FSM、時序、Petri net…）。 | 先建結構化文字模型再渲染＋幾何自檢斷言＋強制缺口表——「圖」是模型的投影，編造連線被 Step 0 防火牆擋下。與另兩顆合組 `architecture-diagramming/` 能力集合。 |
| `env-cleanup` | 判斷並封存不再需要的環境檔案。 | 以不變量判斷可否封存——只封存不刪除、活環境保護，不是憑感覺清檔案。 |
| `literature-search-extract` | 檢索學術來源並進行可追溯的定向萃取。 | 每條引用掛存取標籤，讀過全文與只看摘要標得不一樣，防止「假裝讀了全文」。 |
| `mechanism-share-packaging` | 把一組**行為機制**（跨 hook／工具／文件的運作模式）輸出到有治理規則的 share repo。 | 硬性委派：目的 repo 的收錄規則永遠是權威，規則內容**絕不**複寫進本 skill——第二份規則就是一個會漂移的分叉。已有兩次實跑（`compact-recovery`、`red-team`）。 |
| `motion-design` | 動效設計方法論總控（時長、緩動、編舞、品牌動態識別）。 | Router + 分層參考檔設計，平時不佔 context；**不含** Three.js 參考套件（見下方授權說明）。 |
| `pptx-review` | **2026-10-02 新收錄。** 在 PowerPoint 裡做簡報審閱迴圈：把「這頁／這個框」解析到使用者正開著的投影片與圖形；把使用者在 PowerPoint 留的註解套回簡報的建置原始碼，重建後回報套用／略過／通則裁定。 | 註解依定位信心分級處理（高：套用；中低：文字吻合才套；衝突：略過並回報，永不猜目標）、本地／通則分類（通則只記錄、升格成規則仍經使用者）、一次問完不零碎問。唯讀的游標／註解讀取器住在來源端的 `tools/` 樹，不隨此包出貨。 |
| `product-design-thinking` | 以第一性原理協助新產品或複雜功能設計。 | Phase 0 強制查重——先證明值得做、沒有現成輪子，才准進設計。 |
| `project-retrospective` | 在專案結束後萃取教訓與可重用規則。 | 六類信號分類＋合併進全域規則前必先徵詢，回顧結論不會悄悄污染全域設定。 |
| `scientific-research-guide` | 提供研究方法、實驗設計與驗證建議。 | 五道關卡＋領域設定檔三層分離，通用框架與領域知識不綁死。 |
| `security-deep-checklist` | 執行程式、部署與偵測應變的深度安全稽核。 | 藍隊三分法：程式／部署／偵測應變分開稽核，不是一張混在一起的清單。 |
| `skill-co-upgrade` | 用真實任務實測某個技能，收集缺口後驗證、採納，並以處置檔（disposition）跨工作階段接力。 | 缺口的判準是「執行者必須繞過技能才能把事做對」——「照做而成功」和「無視而失敗」都不算缺口，所以升級靠的是實測證據而非意見。 |
| `skill-share-packaging` | 將技能打包為可分享版本，或稽核第三方技能。 | 打包前先去除環境耦合（四類檢查）＋機械掃描腳本，雙層把關。 |
| `ux-walkthrough` | 對已存在或設計中的互動流程做任務級 UX 走查（認知走查）：特定使用者在特定情境下，找不找得到入口、預不預測得到每個動作的後果、等待／取消／失敗後救不救得回來。 | 判準是「任務有沒有走完」而不是「文案好不好讀」——產出是可執行的發現（任務・證據標記・層級・修法・驗證方式），顯示／停用／隱藏三選一要有裁決，等待-取消-復原要有契約。與 `audience-fit` 互相轉介：它管措辭，這顆管走得通。 |
| `workflow-checkpoint` | 建立可供後續工作階段快速接手的專案檢查點。 | 交接紀錄摘要／細節兩層分離，長期累積也不會讓檢查點檔案本身變肥。 |

> ⚠️ **`motion-design` 授權說明：本分享不含 Three.js 參考套件。** 原環境曾以第三方
> MIT 內容 vendor 了 `CloudAI-X/threejs-skills`，但該上游未附 `LICENSE` 檔、未具名
> 著作權人，MIT 授權只存在於 README 的一句話——原環境自己的更新紀錄已將此判定為
> 「阻止對外分享，直到上游補上正式授權為止」。本分享尊重那個判定，**完全不收錄**
> 該套件內容，只在 `skills/motion-design/NOTICE.md`、`SKILL.md` 中留下上游連結，供
> 需要的人自行取用並自行做授權判斷。同一顆技能收錄的 `vendor/lottiefiles/` 授權完整
> （MIT + LICENSE + 具名著作權人），不受影響。

## 一眼案例：我遇到的是哪種情況？｜Choose by problem shape

- 「怕 AI 把我的 repo 改壞，要怎麼預防」→ `ai-coding-guardrails`
- 「PR 太多審不完，審了又怕漏」→ `code-review-deep-checklist`
- 「想做新功能，但怕做到一半發現重工」→ `product-design-thinking`

## 建議閱讀順序｜Suggested reading order

1. `ai-coding-guardrails`——觀念底座，先讀這顆。
2. 跟自己痛點對應的那顆——用上面的一眼案例對號入座。
3. `skill-trigger-dict.md`——安裝完成後才需要，負責消歧。

## 使用方式｜How to adopt

1. 先閱讀目標 agent 平台的技能安裝規範。
2. 選取需要的資料夾，將其複製到該平台的 skills 目錄。
3. 閱讀該資料夾的 `SKILL.md`，並一併保留它引用的 `references/`、`domains/` 或 `evals/` 內容。
4. 視需要把 `skill-trigger-dict.md` 放在 agent 可讀取的共用設定位置；它是輔助索引，並不取代各技能的 frontmatter description。

此套件是人工審閱的快照，並非與任何本機技能目錄自動同步；更新時請重新複製、審閱並驗證後再發布。

## 隱私與可攜性｜Privacy and portability

本公開副本已移除或泛化個人帳號、絕對本機路徑、內部專案／套件名稱，以及執行期鎖定資訊。路徑範例使用 `<local-workspace>`、`<suite-repository>`、`<project-repository>` 或 `<global-agent-home>` 佔位符；使用前請替換為自己的環境。唯一例外是 `Global_skill_update.md` 中**指向 skills 檔案的歷史路徑**：為保持該建置紀錄可追溯，這些路徑依原始內容保留。部分技能仍會提及特定 agent 平台的概念，這些屬於功能相容性說明，不代表需要存取原作者的環境。

## 範圍與授權｜Scope and license

本資料夾只包含技能內容與其輔助資料，不包含 agent 執行器、秘密、帳號設定或自動同步機制。授權請見儲存庫根目錄的 [MIT License](../LICENSE)。
