# 環境哲學與遷移指南 (Environment Philosophy & Migration Guide)

> **這份文件不是規定。** 它是這個 `~/.claude` 環境的世界觀說明——寫給人看的
> （至少給環境的主人看的），描述所有規則背後的「為什麼」、系統的整體形狀、
> 什麼是核心資產、以及整個環境如何搬到下一台機器或下一個平台。
> 它不具規範力：與任何規則檔（CLAUDE.md、ops/、skills/）衝突時，規則贏。
> AI 不會被路由來讀它；人類想理解或重建這個環境時，從這裡開始。

---

## 一、終極哲學（所有規則的共同母體）

這個環境的每一條規則，追根究柢都來自以下幾個信念。規則會改、會被修剪、
會過時；這些信念改得慢得多。如果某天你發現一條規則講不出它屬於哪個信念，
那條規則大概該被修剪了。

### 1. 規則是判斷力的替代品，不是美德
規則存在的唯一理由是「判斷力稀缺」。弱模型判斷力稀缺，所以規則是資產；
強模型判斷力充足，同一條規則就變成合規稅 (compliance tax)。因此規則分兩類：

- **不變量 (invariants)**：編碼「人的價值觀」——問價值分歧不問技術選擇、
  引用不捏造、證據才算完成、歸檔不刪除。這些不是任何等級的模型能自行推導
  的，永不放寬。
- **鷹架 (scaffolding)**：編碼「怎麼思考」的流程。它替弱模型補判斷，
  對強模型只是參考。放寬與否**由人決定，模型永不自行放寬**
  （機制見 `ops/05-authority.md`）。

### 2. 證據優先於宣稱 (evidence over claims)
「應該沒問題」不是完成；一次真實執行的產物才是。文件記錄的是意圖，
只有證據記錄現實。這條同時適用於 AI 的交付物和這個環境自己的機制——
每個 hook、每個排程，都要看過一次活的執行證明 (living proof) 才算存在。

### 3. 事後問責優於事前審批 (ex-post accountability over ex-ante approval)
層層審批讓改動成本高於改動價值，系統就會停止演化。這個環境的取向是：
授權在前（決策憲章、放寬等級），痕跡在後（deviation note、審計軌跡、
git 歷史）。放掉審批的同時絕不放掉痕跡——沒有痕跡的分權會失去改進迴路，
這是所有分權制度共同的死因。

### 4. 機械強制優於文字期望 (mechanism over prose)
希望模型「記得遵守」不如讓違規根本執行不了。成本上限用 hook 擋
（`model_cap_guard.py`），膨脹用開場檢查揪（`ops_health_nudge.py`），
而不是在文件裡多寫一段懇求。文字規則留給機械無法判斷的事。

### 5. 索引→按需載入 (index, then load on demand)
永遠在場的內容（全域 CLAUDE.md、skill 描述）是每個 session 都要付的房租，
必須極小；細節放在路由表、字典、references/ 後面，用到才載入。
在這個規模下，命名慣例 + 路由表就是最好的檢索系統——不需要向量資料庫。

### 6. 預防優於修剪 (birth budgets over trim passes)
膨脹不是靠定期大掃除解決的，是靠「出生時就在預算內」解決的
（`ops/40-maintenance.md` §3）。大掃除是預防失敗後的補救——2026-07-09
的大重整應該是最後一次「必須」的重整，之後只該有例行微調。

### 7. 永不刪除，只封存 (archive, never delete)
過時的規則移到 `archive/` 並留一行說明；審計軌跡只追加不改寫；改動前先
備份。可逆性是這個環境敢於快速演化的前提。

### 8. 三層角色
**人**是價值觀的最終仲裁者（價值分歧、放寬等級、不可逆動作）；
**主模型**是決策者與調度者（實作層決定自己拍板，田野工作派出去）；
**subagent** 是手腳（cheap/mid 層，硬規則約束，產出永遠被驗收）。

### 9. 可反駁性分層 (stratified refutability)
模型產出的一切——結論、前提、計畫——天生可被「實際數據＋合理推理」推翻，
推翻免請示、留一行紀錄即可；唯獨**使用者提出的不可約前提**（最終目標、
價值裁決）受保護：證據再強也只能附證據提問，由人同意才改，永不自動推翻。
交付物自帶可反駁性申報（什麼條件下成立、最可能被哪個檢查推翻）——一個
說不出自己怎麼被推翻的結論，還不算完成。這是信念 2（證據優先）與信念 8
（人是價值仲裁者）在同一條規則裡的交會（機制：`ops/30-judgment.md` R2、
`ops/05-authority.md` §4.0；源自 2026-08-06 的全域規則調整）。

### 10. Know-why 是資產，schema 是傳遞下限
決策的「為什麼」——被否決的選項、過程死路——與程式碼同級的資產，記在
per-project journal，新 session 從最新條目恢復進度並**重新確認前提**；
跨專案的抽象只經 retrospective 蒸餾，不自行外溢。每類紀錄文件有不可省略
的最小欄位：**敘事風格隨模型強弱自由，schema 永不鬆綁**——強模型可以用
抽象規則工作，但欄位是資訊跨 session、跨模型傳遞不失真的下限保證
（機制：`ops/60-bootstrap.md` §G、`ops/rules-usage-dict.md` §7 登記表、
`ops/40-maintenance.md` §3 birth schema；同日源起）。

---

## 二、系統地圖（各部件是什麼、為什麼存在）

```
~/.claude/                     ← 整個目錄是一個 git repo（版控即歷史）
├── CLAUDE.md                  憲法層：條件式偏好，每 session 必載（預算 ~15K，2026-08-01 起）
├── PHILOSOPHY.md              本文件：非規範性世界觀（人讀）
├── settings.json              權限、hooks 掛載、預設模型 ⚠️ 內含機器綁定路徑
├── skill-trigger-dict.md      skill 路由字典：哪句話觸發哪個 skill（按需載入）
├── audit-archive/     審計軌跡：已凍結（2026-08-11），僅存歷史敘事
│                   （本分享版把它以 `Global_skill_update.md` 之名放在 repo 根目錄）
├── ops/                       規則層：專案作業的判斷框架（路由表按需載入）
│   ├── OPS.md                 入口 + 六條硬規則 + 路由表
│   ├── 05-authority.md        規則分類 + 放寬閘門（人決定放寬程度）
│   ├── 10~70-*.md             指令迴圈/派工/判斷/維護/教練/引導/演化
│   ├── environment.md         ⚠️ 環境事實（模型對映、機制盤點）——遷移後必須重建
│   └── lessons.md             一次性教訓卡（有 hit-count 與封存機制）
├── skills/                    自製能力模組（11 個），描述極簡 + references/ 按需
├── hooks/                     機械強制層：model_cap_guard、ops_health_nudge
├── backups/<date>/            改動前快照（gitignored——git 本身已是歷史）
├── archive/                   退役內容（gitignored，磁碟保留）
└── projects/<slug>/memory/    ⚠️ 自動記憶——在版控之外（見遷移第 3 步）
```

各層的信任順位：使用者當下指示 > 全域 CLAUDE.md > 專案 CLAUDE.md >
ops/ > skill 內文。字典與索引永遠只是索引，本體以各自的檔案為準。

---

## 三、核心資產清單（遷移時什麼必須活著到對岸）

**Tier 1 —— 不可再生，遺失即重寫**（全部已在 git repo 內）：
- `CLAUDE.md`（全域偏好——多次專案回顧萃取的裁決紀錄）
- `ops/` 全部（除 `environment.md` 外都可跨環境攜帶）
- `skills/` 自製 14 個（含 references/、evals/）
- `hooks/` 7 支 Python 腳本 + `browser-pane-blocklist.json`
- `agents/` 自訂 subagent 定義 8 個（能力白名單 + 路由表 `ops/20-dispatch.md`）
- `skill-trigger-dict.md`、`audit-archive/`（凍結，歷史；本分享版即根目錄的
  `Global_skill_update.md`）、`.gitignore`、本文件
- `interop/`(跨 agent 同步層:可攜規則唯一源 + 編譯器 + 遷移地圖;
  手冊見 `interop/README.md`)
- `settings.json`（權限與 hook 掛載的形狀有價值；路徑要改，見下）

**Tier 2 —— 有價值但在版控之外，遷移要另外搬**：
- `projects/<slug>/memory/`：自動記憶。因為 `projects/` 含對話內容所以整目錄
  被 gitignore，但 memory 子目錄本身是精煉過的事實，值得手動複製。
- `backups/`、`archive/`：git 已涵蓋大部分歷史，通常可不搬。

**不是資產，不要搬**：`plugins/`（marketplace 快取，可再生）、
sessions/telemetry/cache 等執行期狀態、任何 credentials。

**未來可修性**：以上清單本身會過時。判準只有一條——「這個檔案遺失後，
需要多少小時的對話才能重建？」超過一小時的就是 Tier 1。新增核心資產時，
更新本節與 `.gitignore` 頂部的 TRACKED 註解。

---

## 四、遷移方法（新機器 / 新平台 / 災難重建）

1. **Clone**：`git clone <repo> ~/.claude`（或對應平台的 home 位置）。
   歷史、規則、skills、hooks 全部隨之而來。
2. **修機器綁定路徑**：`settings.json` 的 hooks 指向絕對 Python 路徑
   （例如 `C:/Users/<user>/.../Python312/python.exe`）——新機器必改。
   這是已知的第一大遷移坑。
3. **搬記憶**：從舊機器複製 `projects/<slug>/memory/` 到新機器對應位置
   （slug 由工作目錄路徑派生，跨機器可能不同——以新機器實際產生的為準）。
4. **重建 `ops/environment.md`**：模型層級對映、可用派工機制、成本上限
   政策都是環境事實，不能從記憶假設——照 `ops/20-dispatch.md` §0 重新確認。
5. **活體驗證**：手動跑一次兩支 hook（healthy 應靜默；用壓低門檻確認會觸發）、
   開一個 session 確認 skill 描述正常載入、ops 路由目標無缺檔
   （ops_health_nudge 的 ghost-rule 檢查會自動告訴你）。
6. **平台端重接**：plugins / MCP connectors 在 claude.ai 或桌面 app 的
   設定介面重新啟用——這部分不在檔案系統裡，無法隨 repo 遷移。
7. **跨 CLI 隔離**：若同機有其他 CLI agent（codex、gemini 等），狀態各歸各家
   （`AGENTS.md` 事件的教訓）——別讓兩套環境共用設定或互相複製殘留。

---

## 五、這份文件自己的規矩

- 定位為 🟢/🟡 之間：主 session 可直接更新，但它**只能描述、不能規定**——
  想寫「必須/禁止」時，那句話屬於 CLAUDE.md 或 ops/，不屬於這裡。
- **哲學跟在實踐後面，不走在前面**：只記錄已被驗證為真的信念（每條都有
  對應的實際事件或機制），不寫願景。某條信念若被實踐推翻，改寫它並在
  審計軌跡留一行——信念被推翻是系統在學習，不是失敗。
- 溯源：本文件初版寫於 2026-07-09，同日完成反官僚重整（放寬閘門、決策憲章、
  token 瘦身、防再膨脹護欄）。2026-08-11 前的演化敘事見已凍結的
  `audit-archive/`（本分享版：`Global_skill_update.md`），其後的規則理由見
  `ops/rule-registry.md`，
  逐 diff 歷史見 git log。
