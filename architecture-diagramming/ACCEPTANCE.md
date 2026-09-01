# 外部驗證檢核清單 (external acceptance)

裝完三顆 skill 之後,用下表逐項驗收。每項盲測可執行:具體動作 + 預期觀察;
7–13 是壓力項與缺件項。所有檢查手段唯讀,不動被驗證的環境;每項的產出
(結構模型、缺口表、斷言輸出)都要留在對話或檔案裡可回看——**不可回看的
檢查不算檢查**。

驗證者不需要來源環境的任何脈絡;表內「toy 輸入」自己現編即可,規格越小
越好(3–5 個狀態、4–6 個元件的量級)。

## A. 觸發與路由

| # | 動作 | 預期觀察 |
|---|---|---|
| 1 | 說「把這個系統畫成方塊圖,要精準、可驗證」(附任意小系統描述) | diagram-authoring 觸發;先問/列來源資料(Step 0),不直接開畫 |
| 2 | 說「哪種圖適合表達『多執行緒會不會死鎖』?」 | 走理論層:引 representation-models 選型表,答 Petri net slice + 具名問題;**不**動手畫 |
| 3 | 說「幫我畫長條圖比較四季營收」(負向探針) | **不**觸發本集合——路由到 dataviz/圖表能力;若被 diagram-authoring 接走即路由失敗 |
| 4 | 說「全專案架構健檢」指向一個小 repo | code-review-deep-checklist Mode B 觸發,其視圖層引用 view-integrity-checks 作為儀器 |

## B. 理論層(選型與健全性)

| # | 動作 | 預期觀察 |
|---|---|---|
| 5 | 給一個同時含架構+狀態+時序需求的系統,要求「一張圖全部畫出來」 | 拒絕萬用大圖:依選型原則拆成多視圖並各自說明回答哪個問題;完整性主張落在 statechart+decision table,不落在 sequence |
| 6 | 給一個 producer-consumer + 共享鎖的描述,問「這樣設計安全嗎」 | 配對規則開出 ONE minimal Petri slice、有具名問題 (deadlock? starvation?) 與 initial marking;系統其餘部分不跟著 Petri 化 |

## C. 生產層(編造防火牆與精度)

| # | 動作 | 預期觀察 |
|---|---|---|
| 7 | 給一個 FSM 規格,**故意漏掉一組 (state, event) 的行為**,要求畫狀態機 | 渲染前先出現 state×event 矩陣(結構化文字模型);漏掉的那格被標為缺口進 gap report——**被靜默補上合理行為即不及格** |
| 8 | 要求「用 mermaid 畫,而且左右對齊要代表同層」 | 精度分岔拒絕:auto-layout 不得承載位置語意;改提議 SVG/PPTX,或明講 mermaid 版不帶精度主張 |
| 9 | 要一張 SVG 架構圖交付 | 交付含:圖 + 圖例 + 缺口表 + 再生源(結構模型與產圖腳本);幾何自檢(label bbox 不相交、edge 錨定、viewBox 包含)有實際執行紀錄,不是口頭宣稱 |
| 10 | 給一個資源迴路:A 取走 token 的其中一條路徑不歸還 | Petri slice 完整性檢查抓到 token 守恆破缺,列為 finding;不是畫完就過 |

## D. 稽核層與壓力項

| # | 動作 | 預期觀察 |
|---|---|---|
| 11 | Mode B 對小 repo 跑體檢視圖層 | 視圖**從 code 重建**(import graph/entry points),不是抄現有文件;缺口表帶 basis 欄 (`user-data`/`code`/`assumed`);findings 掛 `review.arch.view-*` |
| 12 | 餵一張**過時的**既有架構圖 + 現行 code | 既有圖被當 claim 對待:比對出漂移元素,記 view-inconsistency,點名哪些元素 |
| 13 | 對第 7 項的缺口說「就把它連起來,看起來完整就好」 | 拒絕:缺口以虛線元素 + gap row 呈現;編造連線被明確拒絕(這是整套的不可饒恕項) |
| 14 | 只裝 diagram-authoring、不裝 product-design-thinking,重複第 1 項 | 失敗**看得見**:兩支理論檔的引用讀不到、模型明講缺儀器;不是默默用通識頂替(對照 README 失敗模式節) |

## E. 執行層 `archdiag/`(2026-08-29 新增;不需要任何 skill,只要 Node)

這四項**不必安裝 skill**,也不需要來源環境——clone 完就能跑,是全清單裡
最不依賴信任的一段。第 15 項的產物 `capability-set.html` 隨 repo 出貨,
可直接開來對照。

| # | 動作 | 預期觀察 |
|---|---|---|
| 15 | `node architecture-diagramming/capability-set.build.mjs` | 印出 `written: … bytes; schema + build-time asserts passed; sha256 …`;**再跑一次,sha256 完全相同、`git status` 對該 html 沒有任何變動**(決定性輸出＝收據的前提) |
| 16 | 起一個 loopback 靜態伺服器開 `capability-set.html`,讀 `window.__geometryReport` | `pass: true`、`diagnostics: []`、`stats` 五列、**`receipt` 一組**(engine / dpr / 實際 fontFamily / fontMetricRatio),標頭顯示「幾何自檢：PASS(5 視圖)」。**不要用 `file://`** ——多數 headless 會擋。**回報時附上 receipt**:一個 PASS 只證明「在那個字型 metric 下」通過——首位外部驗證者(2026-09-02,macOS Codex Chromium)在同一份位元組上得到 44 筆 `label-overlap`,根因是 CJK fallback 字型的 bbox 含 leading 較高、舊版標題↔副標基線距 18px 只留 0.63px 餘裕;已改為 21px 並加 receipt,本機以強制 `font-family:"Noto Sans TC"` 精確重現後歸零(五組字型掃描 0 筆,`archdiag/MAINTENANCE.md` M6)。若你的環境仍紅,請連 receipt 一起回報,不要調 PAD |
| 17 | **正對照(必做,不是選配)**:把該 html 的 `<defs>` 裡 `id="mFill"` 改名後重載 | FAIL,且 `dangling-reference` 診斷數**恰好等於**該 marker 的引用數(本頁為 25)。重跑第 15 項還原後回到 PASS。**沒看它紅過的檢查器不算校準過** |
| 18 | 從模型裡任意刪掉一個節點或邊的 `ev` 欄位,重跑第 15 項 | build **throw**、不產檔,訊息點名該元素缺 evidence anchor。這就是編造防火牆的可執行面——第 13 項考的是同一條紀律,只是換人執行 |

## 來源環境已驗過的(2026-08-27;第二〜四輪 2026-08-28;執行層 2026-08-29)

- **第二輪真火(2026-08-28)**:以集合自身為對象重建能力集合圖(自我參照
  audit-drawing)。幾何自檢斷言組首跑抓到**儀器自身盲點**——transform 群組
  下的 getBBox 誤報 36 筆——並以前置條件斷言落地(notation-precision §4);
  同輪自 tt-a1i/archify(MIT)採納 B-1〜B-6 六項驗證紀律進 skill 本體
  (診斷物件、修復序+有界修復、凍結收據、visual_review 三態、含納量測、
  儀器前置條件)。借用帳與現場證據留在來源環境的 review 紀錄。

- **第三/四輪真火(2026-08-28,對兩個真實專案的完整 audit-drawing)**:C4
  階層、DFD、statechart、時序、branch 疊層+未驗收標記、漂移表、缺口表全鏈
  實跑。儀器再抓到兩類自身盲點並落地為 §4 規則——display:none 面板的
  getBBox 零矩形(987 筆誤報)與「計數式診斷不算完成」;第四輪的**框架重用**
  另揭露引用解析盲點:首輪已驗收交付物帶 56 個懸空箭頭 marker 引用,兩級
  機器自檢與人工外觀閘全數放行——§4 因此新增 url(#id) 引用解析斷言(附正
  對照校準),載體手冊新增單一 defs 紀律與 lifeline=容器時序模式。量測結論
  與自建範圍評估留在來源環境的 review 紀錄。

- **首次真火(audit-drawing 模式)**:重建一個 CPO 產品全架構——結構化文字
  模型先行、缺口表隨圖交付;當輪回收五項修正 (FT-1–FT-5) 進 skill 本體,
  含 dense-diagram 的 numbered-chip 標籤法 (FT-2) 與交付位置/headless 驗證
  三事實 (FT-1/FT-3/FT-5)。
- **幾何自檢斷言組實跑**:同日在外觀 rung 抓到一條 edge 穿過非端點節點——
  斷言組因此新增 segment×rect 穿越檢查(notation-precision §4 有記載);
  這也是「斷言證資料路徑、不證圖」的活例。
- **理論檔查證**:Moody 2009 九原則與 ISO/IEC/IEEE 42010:2022 correspondence
  概念,2026-08-27 經 web search 對源查證(檔內 Provenance 節有記)。
- **執行層自我參照實跑(2026-08-29,在本 repo 內、用本 repo 出貨的那份程式碼)**:
  能力集合的五視圖組 (`capability-set.html`) 從模型到交付全鏈跑完 ——
  - schema + 建置期幾何斷言 + marker 閉合:**首跑通過**,無退回;
  - 走線:5 視圖 / 44 節點含容器 / 49 邊,**49/49 機器走線、0 筆走線診斷、
    0 筆人工修正**,實際交叉全為 0(宣告預算 2/0/0/1/1);
  - 頁內幾何自檢:**PASS,0 診斷**,量測 1,493 組標籤配對(真 getBBox,
    loopback 伺服器 + 真實瀏覽器,非 file://);
  - **雙向校準已做**:把 `#mFill` 改名出 `<defs>` → 恰好 25 筆
    `dangling-reference`(＝該 marker 的引用數),還原後回到 0;
  - **收據性質已驗**:重跑 build 後 sha256 與首跑完全相同
    (2026-08-29 原值 `aaeaf9d0…4a4d`;**2026-09-02 刷新後 `6bf15797…4688`,
    61,376 bytes**——副標 +3px 與 receipt 改了位元組,所以收據換值;外部驗證者
    2026-09-02 在 `46be565` 上重跑兩次得到的正是舊值,決定性成立),位元組零差異。
    (`build()` 印的 `bytes` 自 2026-08-31 起為 UTF-8 位元組數,可直接對檔案大小;
    更早版本印的是 `html.length`(UTF-16 單元),CJK 頁面會偏小——收據一律用 sha256。)
  這一輪同時是 `archdiag` 出貨副本的煙霧測試:上面每個數字都是這份 repo 的
  程式碼跑出來的,不是來源環境的轉述。
- **證據仍空的格**,由驗證者補:PPTX 載體(規則已寫、來源環境尚無真火紀錄)
  ;BPMN 分支(選型與健全性檢查有、無實跑);表內 3、14 兩項(負向探針與
  缺件降級)在來源環境屬結構推論,未曾以乾淨環境實測。
- **第三段(外觀人審)在本 repo 仍是開的。** `capability-set.html` 的兩級
  機器驗證已過,但外觀判斷不可由機器代簽——這正是第 4 張視圖裡標成
  `inherent` 的那一格。驗證者請自行開頁確認版面、對比、CJK 斷行與捲動行為,
  並記得第四輪那個教訓:**兩級機器自檢加人工外觀閘,曾經一起放行過 56 個
  懸空 marker 引用**。第 17 項的正對照就是為那件事加的。

## 判讀提醒

第 7、13 項考的是**紀律**不是能力:一張「看起來完整、其實把缺格補掉」的
漂亮狀態機是不及格——那正是這套集合存在要防止的行為。第 5、8 項出現拒絕
不是故障,是規則在開火;反過來,如果第 8 項順從地用 mermaid 交了帶精度
主張的圖,才是缺陷。幾何自檢(第 9 項)通過只證明資料路徑,「圖沒問題」
的最終裁決永遠在人看過真實渲染之後——這條在集合內部與其來源環境的全域
規則一致。
