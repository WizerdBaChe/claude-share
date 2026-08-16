# OPERATOR-GUIDE — 操作者手冊與環境搬移指南

> 給「不是原作者的操作者」與「要把整個環境搬到別台機器」的人。
> 一份文件、兩個部分：Part 1 怎麼操作；Part 2–3 資產有哪些、怎麼搬。
> 跨 agent 系統（opencode/codex/Antigravity）的規則同步是另一件事，
> 見 `interop/README.md` — 本文件只處理 Claude Code → Claude Code。
> 建立於 2026-07-14。

---

## Part 1 — 操作者手冊（新手 10 分鐘版）

### 1.1 這個環境的分層

| 層 | 位置 | 作用 | 誰可以改 |
|---|---|---|---|
| 全域偏好 | `CLAUDE.md` | 條件式工作規則，每 session 載入 | 只有人（主 session 經同意） |
| 專案規則 | `<專案>/CLAUDE.md` | 蓋過全域 | 同上 |
| ops 規則層 | `ops/`（入口 `ops/OPS.md`） | 專案作業 SOP：派工、判斷、帳本 | 同上；subagent 永遠只能交草稿 |
| Skills | `skills/` + `skill-trigger-dict.md` | 情境觸發的方法論套件 | 同上 |
| Hooks | `hooks/` + `settings.json` | 機械強制（模型管不到的部分） | 同上 |
| 記憶 | `projects/<slug>/memory/` | 跨對話的使用者/專案事實 | 模型自動維護 |

優先序：全域 CLAUDE.md > 專案 CLAUDE.md > ops 層。衝突時高層贏。

### 1.2 權限模式怎麼選（plan / accept edits / auto）

- **plan mode**：大且含糊的實作任務——動手前你想看到完整計畫並簽核。
  不必記得自己開：模型判定任務夠重時會主動請求進入，或在一般模式下
  直接產出 boundary contract（等價物，見 1.3）。
- **accept edits（日常預設）**：逐次核准檔案修改。
- **auto / bypass**：你信任範圍內的批次工作。護欄仍在：hooks 與
  invariant 規則不受模式影響。

### 1.3 會被問到的三件事（怎麼答）

1. **ops-relaxation 等級（L0/L1/L2）**：主模型是旗艦級、專案又沒記錄
   等級時會問一次。意義：L0 = 全部規則照字面執行（預設，最保守）；
   L1 = 核心流程儀式改為事後自查；L2 = 全部鷹架改 advisory，換取模型
   在任務入口產出 boundary contract（4 節 ≤15 行：解讀分岔／邊界輸入
   ／驗收標準／不做清單）。不確定就不答 → 自動 L0，安全。
   答了之後模型會提議把 `ops-relaxation: L<n>` 記進專案 CLAUDE.md，
   同意即一勞永逸。定義：`ops/05-authority.md`。
2. **價值分岔**（錢 vs 時間、隱私 vs 方便、美感取捨）：這類問題模型
   被規定必須問，不會自己選。
3. **不可逆動作**：刪除、對外發布、覆蓋既有文件——同上。

### 1.4 口令與訊號

- 「**深想**」→ 強制深度模式（兩段式自查）；「**快答**」→ 強制直答。
- 開 session 看到 `[ops-health] ...`：這是健康檢查 hook 的提醒，
  一行一項。`ops-relaxation level unset` → 回答 1.3-1 的問題即可；
  其他多為維護提示（檔案超預算等），交給模型處理或忽略皆可。
- Skill 通常自動觸發；也可 `/<skill-name>` 手動叫。哪個情境對應哪個
  skill 查 `skill-trigger-dict.md`。

### 1.5 環境慣例（違反會被視為 bug）

- **永不刪除**：淘汰的檔案移 `archive/` 附註記，不刪。
- **報告開新檔**：不覆蓋既有文件。
- **Commit**：Conventional Commits（`type(scope): subject`），模板與
  type 判斷表見 `COMMIT-TEMPLATES.md`；規則層變更的理由記入
  `ops/rule-registry.md`（事件本身由 commit message 承載）。
- **語言**：對話回覆用繁體中文。**檔案輸出不看副檔名、看主要消費者**
  （人讀文件／機器讀內容／agent 執行的施工卡／概念層 PIM 共四類），
  完整判定規則見全域 `CLAUDE.md` 的 **File output** 條——此處不複述，
  以該條為準。

---

## Part 2 — 資產地圖（具體有哪些、各是什麼性質）

### 2.1 正典設定（git 追蹤 — 搬移即 `git clone`）

| 資產 | 內容 |
|---|---|
| `CLAUDE.md` | 全域工作規則（常駐預算 15K bytes，2026-08-01 由 12K 調升） |
| `LABEL-REGISTRY.md` | 可列舉標籤（`Mode X`/`L2`/`Tier-3`/清單序號）的唯一定義表；造新標籤前必讀 |
| `settings.json` | 權限、hooks 掛載、模型預設 ⚠️ 內含機器綁定路徑，見 3.4 |
| `skill-trigger-dict.md` | skill 路由消歧義表 |
| `audit-archive/` | **已凍結 2026-08-11** 的歷史事件日誌，唯讀。現行分流：事件→commit message、規則現行理由→`ops/rule-registry.md`、踩到的坑→`ops/lessons.md` |
| `PHILOSOPHY.md` | 整套環境背後的世界觀（人讀） |
| `ops/`（12 檔） | 專案作業規則層 |
| `skills/`（52 檔） | 自製 skills 本體 |
| `hooks/`（7 個 .py + 1 資料檔） | `model_cap_guard.py`（subagent 模型上限）、`ops_health_nudge.py`（健康提醒 + 放寬等級提醒）、`dangerous_command_guard.py`（危險 shell 指令）、`ui_verify_guard.py`（瀏覽器窗格量測紀律 L-009/L-010）、`browser_pane_scope_guard.py`（窗格導航記錄 + 已知崩潰站點封鎖 L-013，配 `browser-pane-blocklist.json`）、`instructions_loaded_logger.py`（規則載入遙測）、`delivery_gate_shadow.py`（交付閘門，shadow）— 皆以 `~/.claude` 解析路徑，可攜 |
| `agents/`（8 檔） | 自訂 subagent 定義。全部於 2026-08-12 依本環境重寫（前身是第三方 ai-team-os 套件的 22 個定義，其餘已封存）。每個都帶 `tools:` 能力白名單且必含 `Skill`；路由表 `ops/20-dispatch.md`，政策 `ops/rule-registry.md` |
| `interop/` | 跨 agent 同步層（編譯器 + 地圖 + 驗收） |
| `thinking-notes/` | 設計思考筆記（編號系列） |
| `reports/`（部分） | 少數被追蹤的報告 |

### 2.2 記憶（❗不在 git，最容易漏搬的資產）

- 位置：`projects/C--Users-gunda--claude/memory/`（`MEMORY.md` 索引 +
  一事實一檔）。
- slug 是**專案路徑衍生**的：路徑中非字母數字的字元轉 `-`。換了機器
  或使用者名稱，slug 會不同 → 必須搬到**新路徑對應的新 slug 目錄**，
  否則 Claude Code 找不到（見 3.5）。
- `projects/` 其餘內容是對話紀錄（transcript），屬執行期狀態，不搬。

### 2.3 有價值但刻意不進 git（選擇性搬運）

`archive/`（淘汰檔案的歸宿）、`backups/`（規則變更前的快照）、
`drafts/`（計畫草稿）、`reports/` 其餘、`outputs/`。
搬不搬取決於你要不要歷史脈絡；純運行不需要。

### 2.4 不搬的東西

- **執行期狀態**（新機器自動重生）：`sessions/`、`shell-snapshots/`、
  `file-history/`、`tasks/`、`data/`、`plans/`、`telemetry/`、`debug/`、
  `ide/`、`cache/`、`downloads/`、`session-env/`、`.last-cleanup`。
- **秘密（絕不搬、絕不進 git）**：`.credentials.json` — 新機器重新
  登入即重生；`mcp-needs-auth-cache.json` 同理。
- **機器管理**：`plugins/`（重裝）、根目錄 `AGENTS.md`（codex 遺留，
  interop build 會處理目標端）。
- **interop 目標端產物**（`~/.codex/AGENTS.md` 等）：是建置產物，
  新機器跑 `interop.py build` 重生，永不手搬。

---

## Part 3 — 整體搬移流程（Claude Code → 新機器的 Claude Code）

按順序執行；每步附驗證。

1. **舊機收尾**：`git -C ~/.claude status` 乾淨（該 commit 的先 commit
   並 push 到遠端；沒有遠端就打包整個 `.git`）。要帶歷史脈絡的話，
   另外打包 2.2 的 memory 與 2.3 想留的目錄。
2. **新機安裝**：裝 Claude Code，跑一次並登入（此時會自動生成新的
   `~/.claude/` 與 `.credentials.json`）。
3. **植入正典**：把新生成的 `~/.claude` 改名備份 → `git clone` 到
   `~/.claude` → 從備份把 `.credentials.json` 放回去。
4. **⚠️ 修 `settings.json` 的機器綁定路徑**（目前唯一寫死絕對路徑的
   追蹤檔，共兩處 hook command）：Python 直譯器路徑 + hook 腳本路徑
   改成新機器的實際位置。跨 OS（Windows→macOS/Linux）時直譯器通常是
   `python3`，路徑分隔與引號格式也要跟著改。
   驗證：`python <hooks path>/ops_health_nudge.py < /dev/null; echo $?`
   → 輸出 0。
5. **搬記憶**：算出新機器的 slug（新專案路徑，非字母數字轉 `-`），
   把舊 memory 放到 `~/.claude/projects/<新slug>/memory/`。
   驗證：開新 session，確認 MEMORY.md 內容出現在模型的記憶脈絡中
   （直接問它記得什麼即可）。
6. **重建授權面**：interactive session 跑 `/mcp` 重新授權 MCP、重裝
   plugins、確認 `/permissions` 內容合理。
7. **重生 interop 目標端**（若新機器也用 opencode/codex 等）：
   `python ~/.claude/interop/interop.py build`，然後 `status` 全綠。
8. **活體驗收（全部通過才算搬完）**：
   - [ ] 新 session 在任一個「有 CLAUDE.md 但沒記錄 ops-relaxation」
     的專案開啟 → 看到 `[ops-health] ... ops-relaxation ...` 提醒。
   - [ ] 對話回覆是繁體中文（全域 CLAUDE.md 生效）。
   - [ ] 記憶載入（步驟 5 的驗證）。
   - [ ] 觸發一個 skill（例如問一句該由 `scientific-research-guide`
     接的問題）→ 有正確接手。
   - [ ] 派一個 subagent → `model_cap_guard.py` 沒有報錯且上限生效
     （試指定 opus 應被攔）。

### 3.4 已知機器綁定點（搬移斷點清單，2026-07-14 盤點）

| 位置 | 綁定內容 | 處置 |
|---|---|---|
| `settings.json` hooks ×2 | Python 絕對路徑 + hook 絕對路徑 | 步驟 4 手改 |
| `projects/<slug>/` | slug = 路徑衍生 | 步驟 5 換目錄名 |
| `.credentials.json` | 帳號綁定 | 不搬，重登入 |
| `ops/environment.md` | 環境事實（模型層級、機制） | 到新環境後重新查證更新 |
| interop 目標端路徑 | 各 agent 的全域規則檔位置 | `interop.py` TARGETS，新機器查證 |

此清單的維護規則：任何人在追蹤檔裡新增絕對路徑或平台專屬指令時，
應同步在上表加一列（grep `C:[/\\]Users` 可自查）。

---

## Part 4 — 與 interop/ 的分工（避免混淆）

- **本文件**：同系統整體搬家（Claude Code → Claude Code），資產全帶。
- **`interop/`**：把 `~/.claude` 的**可攜子集**單向編譯給**其他** agent
  系統（opencode/codex/Antigravity）。它刻意不搬記憶、不搬 hooks、
  不搬 skill 觸發機制。兩者互不取代。
