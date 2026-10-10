---
xi: 1
what: system-hmi — 唯讀的系統級監控中介層，把既有的每一種檢查正規化成 state × quality 讀值與衍生完整度
tags: [system-hmi, monitoring, hmi-report, registry]
aliases: [系統監控 HMI, system-hmi 說明]
layer: instrument
audience: builder
date: 2026-09-19
status: live
status_note: 核心已建（HMI-01..06 + conform）；2026-09-22 加上發布邊界子系統（本機 CI/CD，設計 17）；HMI-07 與趨勢線未做
---

# system-hmi

`~/.claude` 既有的每一種系統級檢查（ops-health、integrity sweep、`pol.py`、排程餵入的狀態檔……）
各自用不同的形狀回報。system-hmi 是唯讀的中介層：把它們全部轉成同一種讀值
`state × quality`，寫成一份 Snapshot，agent 用 CLI／JSON 讀。

STATUS: LIVE since 2026-09-19（HMI-01/02/03/04-redefined + `conform`）；2026-09-22 加上 HMI-05 與發布邊界（設計 17）
Proof-of-life: `python tools/system-hmi/controls.py`

> **分享版說明 (SHARE EDITION)**：這份是範本。`registry/` 底下的子系統、監看點、來源、忽略清單、群組與外部 repo
> 清單，在這裡都縮減成「資料結構 (schema) ＋ 一列示範」；下文提到的數量與子系統名稱描述的是來源環境自己的登錄表，
> 不是這份範本的內容。來源環境的其他工具（`pol.py`、`place-ledger`、`graph-snapshot` 等）沒有一起出貨，所以依賴它們的
> 來源（`sources.json`）與 hook 套件監看點在這裡不存在。`controls.py` 內有幾項「活登錄表」檢查綁著來源環境的登錄表與
> 工具；另外兩個發報器 `emitters/editions.py`（讀來源環境一個私有工作台的版次紀錄）與 `emitters/telemetry_trend.py`（連同它的登錄表 `registry/telemetry.json`）沒有出貨，下文講到它們的段落描述的是來源環境。`controls.py` 共 125 項檢查，換上範本登錄表後有 18 項失敗（其餘 107 項通過；沒有 hook 目錄時是 19 項）：兩項斷言來源登錄表裡的特定列，一項讀來源環境的記憶管線工具，另 15 項（版次 9、遙測趨勢 6）要載入上述兩個沒出貨的發報器；失敗是預期的，不是壞掉。

**定位（使用者裁示 2026-09-22）**：system-hmi 是本機的 SCADA。CI/CD（自動化整合監控）屬於它，
不另起一套——見下方「發布邊界」一節（設計文件留在來源環境，未出貨）。

## 發布邊界 (release)：本機 CI/CD（設計 17，2026-09-22）

`~/.claude` 的 main 就是全機正式環境，hook **存檔即上線**。三個機制對應 CI/CD 的三個不變式：

| 機制 | 做什麼 | 對應 |
|---|---|---|
| `python -X utf8 tools/system-hmi/hmi.py verdict` | 跑 `collect --full`，只看**自我測試類**的點（所有 `hook-suite.*` ＋ registry 標 `"gate": "known-good"` 的點）判 HEAD：`GOOD`／`BAD`／`PARTIAL`。只有「完整收集＋沒有被修改的已追蹤程式碼」的 GOOD 才寫入 `out/known-good.json`（已知良好點，回滾目標）。`--due` 快但永遠不標記 | I-1 已知良好、I-2 獨立判官 |
| `hooks/golive_check.py`（PostToolUse） | 編輯到某支已登錄 hook（或它的 proof-of-life 指令點名的檔案／工具目錄）時，當場跑那支 hook 的 proof-of-life；失敗只發通知，不擋 | I-3 在真正的上線時刻觸發 |
| `hooks/system_hmi_summary.py`（SessionStart，HMI-05） | 開場只讀快照：幾個 fail／warn、每個警報已長駐幾天（`standing N d`）、HEAD 距已知良好點幾個 commit | I-3 session 邊界、長駐警報的年齡 |

判決不看新鮮度／排程類的點：Codex 編譯落後是該處理的事，但不是程式碼不能回滾到這個 commit 的理由。
回滾：`git diff <known-good sha> -- <path>` 比對、`git checkout <sha> -- <path>` 還原；離碟副本見 home-bundle。
已知限制：已登錄 hook 匯入、但沒被它的 proof-of-life 指令點名的工具，編輯時不會觸發檢查（每日完整判決仍會涵蓋）。

## 兩條軸

- **State**（子系統自己說的健康）：`pass` / `warn` / `fail` / `null`。只有在 `quality=good` 時才當
  現值採信（INV-2）。
- **Quality**（HMI 對這次讀值可信度的判斷）：
  - `good` — 探測成功，state 可信
  - `stale` — 沿用舊讀值（`stale_reason`: `tier-not-run` 這輪沒排到慢 tier，或
    `source-older-than-max-age` 來源內容本身太舊）
  - `probe_error` — 探測本身沒跑起來（逾時、找不到檔、解析失敗、元件不存在）
  - `undetermined` — 有 Probe 但機器不能判（`manual` adapter、原生文件缺這個 id、`ran:false`）
  - `no_probe` — 誠實的空白：這個東西被登錄了，但沒有任何 Probe 在看它（disposition
    `retired`/`out_of_service`，或 CLAUDE_SHARE、AgentExchange、Textbook、
    memory-pipeline、auto-memory 這五個使用者親自點名「沒人在看」的對象）

`no_probe`／`undetermined` **永遠不會**顯示成 PASS（INV-3）——沒有讀到不是通過。

**延後 (deferred) 是 state 旁的註記，不是第三條軸**（2026-09-23，`hmi/deferral.py`）。「已知、刻意延後、
現在沒事要做」的 warn 如果一直亮橘燈，會教人忽略橘燈（ISA-18.2 的長駐警報）。所以一個點若帶有
**具名觸發條件 (trigger)** 的延後宣告，而且觸發條件還沒成立，讀值記成 `state: pass` ＋
`deferral.status: "holding"`（原始的 warn 與證據保留在註記裡），總覽頁用灰色「暫停」符號、獨立計數顯示，
不進警報列、不上色。觸發條件成立 → 回到 `warn`（`fired`）；沒寫觸發條件、人工觸發卻沒有裁示出處、
或機器讀不出觸發條件 → 照樣 `warn`（`rejected`）。只作用在 `quality=good` 的 `warn`：fail 不能延後，
探針壞掉也不能被延後蓋住。宣告來源兩處：registry 點上的 `deferral`（機器可查的 `probe` 觸發，或
附裁示的 `manual` 觸發），或原生文件的 `deferred`（PROTOCOL.md E-7／R-6）。

和 `shelved` 的差別：shelve 是人把一個**仍然異常**的警報靜音一段**時間**（必須有 `until`）；
延後是設計上由一個**條件**壓住，條件一變就自己回來——ISA-18.2 的 shelving 與 suppressed-by-design。
現役兩例：`ops-health.advisory-outputs`（numberref 紀錄，人工觸發，裁示＝檔案自己的狀態行）、
`memory.hybrid-index-fresh`（觸發＝`index_freshness.py --consumers` 找到有 recall leg 用這個索引；
使用者裁示 2026-09-19／09-23：沒有使用者之前不重建）。

## 8 個 Adapter（封閉集合）

`line-scan` 須宣告 `ok_exits`（預設 `[0]`）；離開碼不在其中＝`probe_error`。宣告 `pass_regex` 則 pass 必須是**正向**比對到，沉默不算通過。

`native`（讀 `hmi-report/1` 文件，見 `PROTOCOL.md`）、`exit-code`、`tail-sentinel`、
`empty-output`、`line-scan`、`status-file`、`fs-link`、`manual`。新增類別＝改語意契約，不是施工
時的自由裁量。

## 兩類判決（PIM v1.3，使用者裁決 2026-09-19）

每個點屬於一類，子系統**分開 rollup**（`r_state`／`i_state`），互不折算；`state`＝兩者取最差，只供排序：

- **R 帳實相符 (reconcile)**：磁碟實況與**紀錄**對不對得起來——git（commit／merge／branch）、Registry、
  路由與索引、manifest。＝飄移程度。進行中（新於寬限期）＝`warn`，超過＝`fail`；寬限期讀自
  `hooks/ops_health_nudge.py` 的 `STALE_WORK_DAYS`，HMI 不重述（INV-4）。
- **I 系統完整性 (integrity)**：它現在能不能運作——測試、調用、連結。＝可用程度。

通用 R 來源：`emitters/reconcile.py`（每個 repo 一次 git status，依路徑分攤到子系統；外部 repo 列在
`registry/reconcile.json`）、`emitters/awareness.py`（記憶索引封閉性）、以及 native 來源 `place-ledger`
（`tools/place-ledger/place.py emit`：以 agent 足跡為準的地點帳——等你同意的種類建議、已歸類未後處理、未宣告的區、
該有 repo 卻沒有、足跡管道健康；**沒有 ignore 清單**，不需照顧的地點是一個種類，仍在帳上）。

## 掃描分級（D-6，仿 SCADA 靜態資料＋完整性輪詢）

slow 點的判決在「宣告的輸入指紋沒變」**且**「距上次實跑 < `registry/scan.json` 的 `integrity_poll_days`（3 天）」
時沿用為 `good`（`carried: inputs-unchanged`）；否則標 `due`。`collect --due` 只重跑 due 的點。
點可宣告 `inputs`（預設＝它的構件路徑）；指紋只讀 metadata，不讀內容。指紋只涵蓋**宣告的**輸入，
未宣告的相依靠完整性輪詢保底——所以那個數字不能是「永不」。

## 完整度＝可監控覆蓋（跟判決完全獨立，INV-7）

C1 registered · C2 R-covered（有 R 類點照到它）· C3 I-covered（有 I 類點照到它）· C4 self-tested ·
C5 watched（HMI 之外已有機制在看）。點照到構件的三條路：綁在它上面、`covers` glob 命中、
`covers_subsystem`（該子系統的全部 home 構件）。標籤 `COMPLETE`／`PARTIAL`／`BARE`／`N/A`／`UNDETERMINED`。
「有沒有文件」已不在評分表內——那是一個該亮燈的 R 類事實，不是完整度。

## 群組與能力面（使用者裁決 M5，2026-09-19）

`registry/groups.json`：群組是既有子系統之上的**檢視**，不改任何子系統 id。第一個群組 `memory-index`（記憶與索引）
分四個能力面——A 知道有什麼、B 記得決定過什麼、C 找得到內容、D 知道自己不知道什麼——每面各自 rollup R／I，
只採 `good` 讀值；沒有任何點照到的面顯示 `-`（不是 PASS）。點的面＝`groups.json` 的 `points` 對應，否則跟著它的子系統。
A 面目前是空的：等地點帳 (place ledger) 施工（設計文件留在來源環境，未出貨）。

## 用法

```
python tools/system-hmi/hmi.py validate            # 檢查 registry/*.json，exit 0/1
python tools/system-hmi/hmi.py scan                 # 磁碟↔registry 兩個方向的收斂，exit 0/1
python tools/system-hmi/hmi.py collect [--full|--due]  # 預設只跑 cheap（~20 s，slow 判決依指紋沿用）；--due 只補跑失效的 slow 點；--full 全部重跑（~2 分鐘，單獨跑）
python tools/system-hmi/hmi.py show [--json|--summary] [--subsystem ID]   # 只讀 Snapshot，exit 0/1/2/3
python tools/system-hmi/hmi.py conform reconcile      # 檢查一個原生 emitter（換成 sources.json 裡的來源 id）是否符合 hmi-report/1
python tools/system-hmi/hmi.py static               # 產生靜態總覽頁 out/mimic.html（不能重跑檢查）
python tools/system-hmi/hmi.py serve [--port 8787] [--idle-exit MIN]  # 本機服務：同一張頁面＋「重跑檢查」按鈕；--idle-exit＝頁面關掉 MIN 分鐘後自動結束
tools/system-hmi/open_hmi.pyw                       # 人用這個：桌面捷徑「系統監看（可重跑）」→ 無終端機視窗，服務沒開就開（閒置 15 分鐘自動結束），Chrome 應用程式視窗打開；
                                                    #   已在跑的服務只有「載入的程式＝磁碟上的程式」才沿用，舊版（改程式前啟動的）自動換新（2026-09-23）
tools/system-hmi/open-hmi.bat                       # 舊版同功能，會留一個終端機視窗（2026-09-22 起改用上面那個）
```

## 給人看的頁面（HMI-06，2026-09-19）

一張 SCADA 式總覽（產生器 `mimic_view.py`；設計依據寫在它的 docstring：ISA-101／High Performance
HMI ＋ Siemens PCS 7 APL Style Guide ＋單線圖母線畫法）。點面板彈出詳情，兩個分頁：「警報與狀態」
「監看覆蓋」（後者逐條列出五個條件各缺哪些元件——回答「那條為什麼沒滿」）。檢視狀態在 URL hash。

本機服務（`hmi/server.py`）的邊界，每一條都在 `controls.py` 有對照測試（INV-8）：

- 只綁 `127.0.0.1`；`Host`（與存在時的 `Origin`）不是本機這個埠 → 403。
- `POST /refresh` 要帶每次啟動隨機產生、只嵌在頁面裡的 token → 否則 403。
- 請求**只能**觸發 `hmi.py collect`，參數只能是登錄表裡的一個點 id／子系統 id，或 `cheap`／`full`
  兩個層級名稱；未知 id → 404。請求給不了指令、路徑或參數字串；多餘的 JSON 欄位直接忽略。
- 以上拒絕情境一律**不啟動任何子程序**（測試用啟動計數器斷言）。另一個收集在跑 → 409 並顯示持有者。
- 等待契約：按下後按鈕全部停用、顯示已等秒數、不能取消；完成後頁面自動重載並保留目前檢視；
  失敗顯示原因並恢復按鈕。頁面每 20 秒問一次快照時間，別處跑了收集也會自動更新；服務沒回應會說。
- 靜態檔沒有 token、沒有按鈕，並在右上角說明原因。

每次收集另寫一行精簡紀錄到 `out/history.jsonl`（計數、各子系統 R/I、每點狀態），留給之後畫趨勢。

`out/`（snapshot.json、snapshot.previous.json、collector.lock）不進 git。

## 本輪沒做（範圍外，不是遺漏）

- ~~HMI-05（SessionStart 摘要 hook）~~ — 2026-09-22 已做（`hooks/system_hmi_summary.py`），見「發布邊界」一節。
- ~~HMI-06（本機服務 + 頁面）~~ — 2026-09-19 已做，見上節。趨勢線／量表尚未畫（等 `history.jsonl` 累積）。
- HMI-07（自我登錄：PROJECTS.md、sweep 新檢查、`gsnap.py build`）— 不在本輪 Objects。

## 已知的誠實限制

- E5「有人在看」只認 Registry 宣告（PIM §7，2026-09-19 修正）：有 `watched_by` 且查得到＝是；
  有宣告但查不到＝`?`；**沒宣告＝否**。實際上有別的機制在看卻沒宣告，要回 Registry 補，HMI 不猜。
- 跨子系統的點（一個 emitter 評判多個子系統，例如 ops-health 的預算檢查）在點上宣告
  `subsystem`，rollup 依它歸屬；沒宣告就跟著構件走。validate 會拒絕未知的 `subsystem`。
- 沿用的（`stale`）讀值保留**原觀測時間**，不併入子系統 `state`（INV-6），另以
  `last_known_state`／`last_known_oldest_observed_at` 顯示。要不要讓「夠新的」沿用讀值算數，是未裁的 D-6。
- 存在性探針（`fs-link`）的 pass 比內容探針弱得多；覆蓋現況與下一批探針見
  來源環境的探針覆蓋紀錄（未出貨）。
- `hook-suite.*`（HMI-04）點只在 `--full` 執行後才有真讀值；平時的 `collect`（cheap）之下它們是
  `undetermined`（第一次跑）或 `stale`（`tier-not-run`，沿用上次 `--full` 的結果）。

**遙測趨勢 (telemetry-trend)** — `telemetry-trend.guards`（`emitters/telemetry_trend.py`，登錄表 `registry/telemetry.json`；快照統一設計 02 §9.2）只做一件事：把每個守門 hook 的 `telemetry/*.jsonl` 依列內的時間戳（不看檔案 mtime）按「完整 ISO 週」數列數，近 8 個完整週（本週不算）裡，前 6 週平均至少 3 列、最後 2 週卻都是 0 → `sudden-zero`；最後一週超過前 7 週中位數的 5 倍且至少 10 列 → `spike`；整個檔案讀不出任何時間戳 → `unreadable`。它**能判斷的只有「列數的週變化」**：每條 finding 都印出 8 個週計數和閾值；歷史不到 8 週（第一列落在視窗第 1 週之後）的檔案不評判，只在 `young` 備註裡列名；空的 telemetry 目錄是 `warn`「no telemetry rows」，絕不報 pass。它**不能判斷**的有三件：一，攔截型 hook（只在擋下或提醒時才寫列）安靜是因為沒有東西撞上它，那是健康狀態，所以「安靜 ≠ 壞掉」，`sudden-zero` 只是問該 hook 的負責人一句話，不是判決；二，它不判「N 天沒動作」，也不讀列的內容；三，登錄表 `unowned` 裡的檔案（多寫入者、工具寫的、來源不明）完全不評判。閾值 `MIN_RATE=3`、`SPIKE_X=5` 是探索值（重放校準只有 6 個有資格的檔案），重新校準的觸發條件寫在發報器 docstring：累積到 20 組以上有資格的 (檔案, 視窗)。`hmi.py validate` 另外守住登錄表完整性：呼叫 `deny_receipt.clause()`／`receipt()` 或寫了字面 `telemetry/<name>.jsonl` 的 hook 必須有一列，只用 `notice_clause` 的 hook 不算寫入者，現存的 telemetry 檔案必須是某列的檔案或列在 `unowned`，列的檔案必須存在；已不符合條件的列只是警告（`validate()` 的 `warnings` 參數，`hmi.py` 目前不印）。

**版次信封 (edition-envelope/1)** — `emitters/editions.py`（快照統一設計 02 §2、§6，2026-10-09）把四個快照視圖（HMI、graph-snapshot、version-census、演進研究）各自的「描述到哪一刻」正規化成同一個信封：`view`、`repo`、`sha`（加 `sha_source` 說明 sha 從哪讀到）、`dirty`、`cut`、產生它的 `tool` 與參照。兩個點：`editions.register` 列出四個視圖各描述到何時（讀不到的視圖照實標 `undeclared`，不猜）；`editions.evolution` 讀演進研究的版次紀錄 `claude-se-history-workbench/out/editions.jsonl`（只追加，事件 opened／built／gated／accepted／tagged／abandoned／backfilled；狀態由事件推導），算出最新已接受版次落後 `~/.claude` HEAD 幾個 commit、幾天，超過 `LAG_DAYS=90` 或 `LAG_COMMITS=3000` 任一個就 `warn`，每條 finding 印出兩個數與閾值。它**只提醒、不出版**：開新版次一律由人跑 `edition.py`，沒有任何排程會替你開（INV-9）。它不讀工作台程式碼，視圖一律當純 JSON 檔讀。
