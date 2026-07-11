# Skill Toolkit

一組可攜式的 AI agent 技能 (skills) 與觸發關鍵詞索引。此分享適合用於審查、研究、產品設計、環境維護與工作階段管理；每項技能皆以 `SKILL.md` 定義其適用範圍與操作邊界。

## 內容

- `skill-trigger-dict.md`：雙語觸發字典；用於在相近技能間消歧，並提供較能命中技能的提問句型。
- `skills/`：12 個可獨立閱讀及匯入的技能資料夾，以及它們所需的參考文件與評估資料。

| Skill | 用途 |
|---|---|
| `ai-coding-guardrails` | 設計 AI 協作的防護、審查與復原流程。 |
| `code-review-deep-checklist` | 執行深入的程式、架構與依賴適用性審查。 |
| `config-self-audit` | 稽核 agent 設定、hooks 與規則檔。 |
| `design-system-suite` | 為多產品建立契約優先的共享設計系統。 |
| `env-cleanup` | 判斷並封存不再需要的環境檔案。 |
| `literature-search-extract` | 檢索學術來源並進行可追溯的定向萃取。 |
| `product-design-thinking` | 以第一性原理協助新產品或複雜功能設計。 |
| `project-retrospective` | 在專案結束後萃取教訓與可重用規則。 |
| `scientific-research-guide` | 提供研究方法、實驗設計與驗證建議。 |
| `security-deep-checklist` | 執行程式、部署與偵測應變的深度安全稽核。 |
| `skill-share-packaging` | 將技能打包為可分享版本，或稽核第三方技能。 |
| `workflow-checkpoint` | 建立可供後續工作階段快速接手的專案檢查點。 |

## 使用方式

1. 先閱讀目標 agent 平台的技能安裝規範。
2. 選取需要的資料夾，將其複製到該平台的 skills 目錄。
3. 閱讀該資料夾的 `SKILL.md`，並一併保留它引用的 `references/`、`domains/` 或 `evals/` 內容。
4. 視需要把 `skill-trigger-dict.md` 放在 agent 可讀取的共用設定位置；它是輔助索引，並不取代各技能的 frontmatter description。

此套件是人工審閱的快照，並非與任何本機技能目錄自動同步；更新時請重新複製、審閱並驗證後再發布。

## 隱私與可攜性

本公開副本已移除或泛化個人帳號、絕對本機路徑、內部專案／套件名稱，以及執行期鎖定資訊。路徑範例使用 `<local-workspace>` 或 `<suite-repository>` 佔位符；使用前請替換為自己的環境。部分技能仍會提及特定 agent 平台的概念，這些屬於功能相容性說明，不代表需要存取原作者的環境。

## 範圍與授權

本資料夾只包含技能內容與其輔助資料，不包含 agent 執行器、秘密、帳號設定或自動同步機制。授權請見儲存庫根目錄的 [MIT License](../LICENSE)。
