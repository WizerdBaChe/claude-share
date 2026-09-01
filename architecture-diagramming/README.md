# architecture-diagramming — 架構圖的選型・繪製・體檢能力集合 (architecture-diagram capability set)

> 這不是一顆 skill,是**三顆 skill 拼成的能力集合 (capability set)**:理論層選
> 「哪種圖回答哪種問題」,生產層把資料變成**可驗證**的圖,稽核層從 code 反向
> 重建視圖並找缺口。三顆各自能動,但只有合起來才構成完整迴路——所以本資料夾
> 把它們當一個機制交付,並附外部驗證清單 [`ACCEPTANCE.md`](ACCEPTANCE.md)。
>
> 首次實戰 2026-08-27 於來源環境:以 audit-drawing 模式重建一個 CPO
> (co-packaged optics) 產品全架構,含結構模型與缺口表;五項現場修正
> (FT-1–FT-5) 已回收進 skill 本體。

## 問題形狀

架構圖 (block diagram)、狀態機 (FSM/statechart)、Petri net 這類圖,實務上壞在
三個地方,而且三個壞法互相獨立:

1. **選錯圖**:用一張「萬用大圖」同時回答架構+資料+狀態+時序+資源,結果每
   個問題都答不好。單一視圖也永遠證明不了完整性——sequence diagram 是一條
   情境,不是行為空間。
2. **畫出來的內容是編的**:模型憑印象補上資料沒有的連線與狀態,圖看起來完整、
   實際不可證偽。在真實系統上,圖的職責是**暴露**缺口,不是弄平它。
3. **圖與系統漂移**:改了像素沒改模型,下次要更新只能重畫,圖退化成截圖。

三顆 skill 各治一個壞法,邊界互不重疊(每顆的 SKILL.md 都明訂 handoff)。

## 機制:一條迴路、兩個入口

```
【設計入口】要一張新圖
   問題 ──► representation-models.md      選型:一個問題一種主圖 + 盲點配對
              │                            (Petri slice 何時開、decision table 何時開)
              ▼
          diagram-authoring Step 0–2      來源資料閘門(fabrication firewall)
              │                            → 結構化文字模型(state×event 矩陣、node/edge 表)
              ▼
          view-integrity-checks.md §1–§2  單視圖健全性 + 跨視圖對應
              │                            缺口先進 gap report,再談渲染
              ▼
          diagram-authoring Step 3–5      載體選擇(mermaid/SVG/HTML/PPTX)
              │                            → 幾何自檢(機器)→ 外觀(人)三段驗證
              ▼
          交付 = 圖 + 圖例 + 缺口表 + 再生源(模型+腳本)

【稽核入口】體檢既有系統
   codebase ──► code-review-deep-checklist Mode B(體檢視圖層)
                  從 code 重建 Standard-tier 視圖組(不是抄文件)
                  ──► 同一支 view-integrity-checks 儀器 → review.arch.view-* findings
                  ──► 重建視圖 + 缺口表隨報告留檔,下次體檢 diff
                  (要做成給人看的簡報級交付 → 回到 diagram-authoring)
```

理論永遠只有一份:選型與健全性檢查住在 product-design-thinking 的兩個
reference 檔,生產與稽核兩顆 skill 都**指過去引用、不複寫**——第二份規則就是
一個會漂移的分叉,這是整套環境的標準紀律。

## 檔案(都已收錄在本 repo,manifest 條目見 `tools/share-manifest.toml`)

| 檔案 | 角色 | 擁有什麼 |
|---|---|---|
| `../skill-toolkit/skills/product-design-thinking/references/representation-models.md` | 理論:選型 | 「問題→主圖」選型表(含 Petri net、timing、BPMN、decision table)、盲點配對規則、per-tier 預設視圖組 |
| `../skill-toolkit/skills/product-design-thinking/references/view-integrity-checks.md` | 理論:健全性 | 各圖種完整性檢查(state×event 矩陣、boundary reconciliation、token 守恆…)、跨視圖對應(ISO/IEC/IEEE 42010 correspondence)、缺口表格式 |
| `../skill-toolkit/skills/diagram-authoring/SKILL.md` | 生產:流程 | 模式路由、fabrication firewall、結構模型先行、三段驗證、交付物定義 |
| `../skill-toolkit/skills/diagram-authoring/references/notation-precision.md` | 生產:畫法 | Physics of Notations 派生繪圖規則、各圖種畫法慣例、幾何自檢斷言組 |
| `../skill-toolkit/skills/diagram-authoring/references/carrier-playbook.md` | 生產:載體 | mermaid/SVG/HTML/PPTX 精度天花板與驗證路徑、再生紀律 |
| `../skill-toolkit/skills/code-review-deep-checklist/references/project-review.md` | 稽核 | Mode B 體檢視圖層:從 code 重建視圖、integrity pass、與既有圖比對、留檔 |
| `archdiag/`(11 檔,**2026-08-29 新收**) | 生產:執行層 | 把上面那些紀律變成會跑的程式:schema 驗證 → build-time 幾何斷言 → marker 閉合 → 決定性輸出 → sha256 收據;`selfcheck.mjs` 是頁內第四段自檢的**唯一來源**;`route.mjs` 正交走線;`delta.mjs` 模型 diff |

配套(消歧義):`../skill-toolkit/skill-trigger-dict.md` 有三列速查——精準繪製
→ diagram-authoring;選型理論 → representation-models;全架構重建找缺口 →
audit-drawing 模式。

## `archdiag/`:紀律變成會跑的程式(2026-08-29)

前四項是散文紀律,這一項不是。它存在的理由是一次**一天內就發生的漂移**:
兩份 audit 交付各自帶一份「頁內自檢框架」的副本,其中一份多了第 8 項檢查、
另一份沒有——而兩邊的報告都印 PASS。**一份會漂移的檢查器比沒有檢查器更糟,
因為它還在被信任。** 所以檢查器只准有一份:

| 模組 | 負責 | 為什麼是它 |
|---|---|---|
| `index.mjs` | `build(opts)`:schema → build-time 幾何斷言 → marker 閉合 → 輸出 → sha256 收據 | 任何一關失敗就 throw,不會產出「看起來對」的檔案 |
| `schema.mjs` | 型別、列舉、id 解析、宣告形狀 | **只裁決它能判定的事**;聚合方式、視圖選擇、節點位置屬語意,永遠留給人 |
| `asserts.mjs` | 寫檔前、在模型資料上:格線對齊、錨點貼邊、正交 | 在像素存在之前就否決 |
| `selfcheck.mjs` | 頁內第 1–8 項檢查 + 儀器前置條件 | **唯一來源**。build 腳本自帶副本就是把上面那個缺陷放回來 |
| `emit.mjs` | 樣式、`nodeSvg`/`viewSvg`/`DEFS`/`pageHtml` | 決定性:同樣的輸入 ⇒ 同樣的位元組(收據才有意義) |
| `route.mjs` | 正交走線 + 標籤置放,藏在 `RouterProvider` 介面後 | 節點位置是**輸入不是輸出**(位置帶語意);交叉數超過宣告值不會硬畫,回診斷 |
| `delta.mjs` | 模型層 diff(幾何 vs 語意分類、缺席邊分開算) | 取代一次量到約 12 分鐘的手工比對 |
| `vendor/archify-geometry.mjs` | 幾何原語,取自 tt-a1i/archify(MIT),逐字 | 上游 rect 形狀在呼叫邊界轉接,不就地改 |

三個**性質**(不是使用說明,是這批資產的不變式):

1. **決定性輸出。** 同樣的模型 ⇒ 同樣的位元組。所以 sha256 可以當凍結收據:
   驗收過的交付物換了位元組,就不是驗收過的那一份。
2. **檢查器只有一份。** 也因此它的任何修改都必須跑**雙向校準**——弄壞一個
   已知案例要看到它變紅,復原要看到它變綠。從來沒紅過的檢查器等於沒校準。
3. **行尾被釘死。** 收據是位元組的雜湊,而 template literal 會繼承來源檔的
   行尾——所以本 repo 的 `.gitattributes` 把 `archdiag/**` 釘成 LF。少了這個
   pin,一次 CRLF checkout 就能在**測試全綠、內容零變動**的情況下作廢每一張
   收據。這正是它自己 `MAINTENANCE.md` M1 要防的那件事。

不隨附的是來源環境的 build 腳本(在不出貨的 `outputs/` 樹裡)。出貨的是
**函式庫本體 + README 裡的 `build()` 契約**——build 腳本是照著那份契約寫的,
本資料夾的 [`archdiag-capability-set.html`](archdiag-capability-set.html) 就是
用出貨的這份程式碼現做的一份,可以當範例讀。

## 安裝

1. 把 `skill-toolkit/skills/` 下的三個資料夾整組複製到你的 skills 目錄:
   `diagram-authoring/`、`product-design-thinking/`、`code-review-deep-checklist/`。
   **並排安裝是硬需求**:diagram-authoring 以相對路徑
   `../product-design-thinking/references/…` 引用理論檔,code-review-deep-checklist
   以 `~/.claude/skills/product-design-thinking/…` 引用同一支儀器——拆開裝,
   指標就懸空(懸空的樣子見下方失敗模式)。
2. 選配:`skill-trigger-dict.md` 放進 agent 可讀的共用位置(消歧義用)。
3. 選配整合(各自都有 "if available" 語意,缺了不擋主流程):
   - PPTX 載體需要平台的 pptx 技能(如 anthropic-skills:pptx);沒有就用
     HTML/SVG 載體。
   - 資料圖表(axes/series)本來就不歸這套管——有 dataviz 類 skill 就交過去。
4. 驗證:跑 [`ACCEPTANCE.md`](ACCEPTANCE.md)。**複製不等於能力成立**——清單
   考的是紀律有沒有跟著檔案一起到(尤其編造防火牆那一項)。

## 圖種涵蓋(誰擁有哪一格)

| 圖種 | 選型列 | 健全性檢查 | 畫法慣例 |
|---|---|---|---|
| Block / C4 / component / 爆炸圖 | ✓ | ✓(boundary reconciliation) | ✓(port 紀律) |
| FSM / statechart | ✓ | ✓(state×event 矩陣、substrate liveness) | ✓ |
| Sequence / communication | ✓ | ✓(request/response 配對) | ✓ |
| Activity / BPMN | ✓ | ✓(分支覆蓋、fork/join) | —(通用版面規則) |
| Data-flow / pipeline | ✓ | ✓(reader/writer 完整性) | ✓ |
| Timing | ✓ | ✓(單位+容差) | ✓ |
| **Petri net(slice)** | ✓(何時開 slice) | ✓(具名問題、initial marking、token 守恆) | ✓(無 mermaid 原生型 → place/transition 列表或 SVG) |
| Decision table | ✓(guard-dense 時) | ✓(2^n 覆蓋算術) | — |
| Event storming | ✓(標為探索用) | — | — |

「—」= 該格刻意空缺(不是漏):BPMN 的畫法紀律沿用通用版面規則;event
storming 明訂為探索輔助、不是可稽核產物。

## 主要可調參數(改哪裡)

| 想改什麼 | 所在 | 出貨值 |
|---|---|---|
| 每視圖主要元素上限 | notation-precision.md §2 | 7±2,超過就升層 |
| 相異符號數上限 | notation-precision.md §1 | ~6,超過拆視圖 |
| 網格單位 | notation-precision.md §2 | 8px SVG / 0.125in PPTX |
| 最小字級/對比 | notation-precision.md §2 | 11px / 4.5:1 (WCAG AA) |
| 每 tier 預設視圖組 | representation-models.md per-tier 節 | 速寫 2 圖上限 → 全梯 per-subsystem |
| 缺口表欄位 | view-integrity-checks.md §3 | view/element/defect/severity/basis |

## 失敗模式(缺件時你會看到什麼)

- **只裝 diagram-authoring**:SKILL.md Step 1/2 與 Reference files 節指向
  `../product-design-thinking/references/…` 的兩支檔案讀不到——選型退化成
  憑感覺、健全性檢查沒有儀器。圖還畫得出來,但這套集合要防的三個壞法回來
  兩個。
- **只裝理論兩檔**:知道該畫哪種圖、也知道怎麼檢查,但沒有載體紀律與幾何
  自檢——精度主張(對齊/包含/相鄰)無從驗證。
- **不裝 code-review-deep-checklist**:設計入口完整可用;少的是「從 code
  反向重建+留檔 diff」的稽核入口。
- **缺 pptx 技能**:PPTX 載體那一列不可用,mermaid/SVG/HTML 不受影響;
  diagram-authoring 會在載體選擇時明講。
- 任何載體的執行期失敗(字型、JS init)依全域慣例**必須自我宣告**——靜默
  空白畫布本身就是缺陷,不是環境問題。

## 邊界(明知不蓋的地方)

- 資料圖表(有軸、有 series 的 chart/plot/dashboard)→ 各自環境的 dataviz
  能力;UI mockup / 畫面流 → design 類工具;這套只管「系統結構與行為」的圖。
- Artifact / 網頁發佈機制(主題、頁面結構)不在集合內;集合只管圖的內容與
  精度。
- 來源環境 2026-08-27 已把「選型原則+盲點配對」升格為全域規則(global
  CLAUDE.md,指向 representation-models.md);本 repo 的
  `global-claude-md/CLAUDE.md` 是早於該規則的 template 快照,**尚未含這條**
  ——deferral 記錄在 manifest 的 representation-models 條目,下次
  global-claude-md refresh 收。採用者讀 representation-models.md 本體即得
  同一條規則。

## 自我參照的那一份 (`capability-set.html`)

[`capability-set.html`](capability-set.html) 是這套集合**用自己的工具鏈畫自己**
的成果,再生源是 [`capability-set.build.mjs`](capability-set.build.mjs)。它同時
是三件事:機制的架構掃描結果、`build()` 契約的可讀範例、以及 `archdiag` 出貨
副本的煙霧測試。

五張視圖各答一個問題(一問題一主圖):(1) 誰擁有哪一層 (2) 設計入口資料流
(3) 稽核入口資料流 (4) 驗證階梯狀態機 (5) archdiag 模組依賴。第 4 張刻意是
狀態機而非時序圖——**完整性主張只有狀態機扛得住**,時序圖只是一條情境。

頁尾第三張表是**缺口表**,不是免責聲明:五筆,含一筆 `inherent`(人審判準
無法機器化)與一筆 `by design`(整組沒有時序視圖,因為這五個問題沒有一個是
時間問題)。缺口是產物,這條規則對自己也適用。

量測結果(2026-08-29,本 repo 內、用本 repo 出貨的程式碼):建置期首跑通過;
49/49 邊機器走線、0 人工修正、實際交叉全 0;頁內自檢 PASS / 0 診斷 / 1,493
組標籤配對;正對照恰好 25 筆 `dangling-reference` 後還原歸零;重跑 sha256
位元組相同。**外觀人審那一段仍是開的**——見 `ACCEPTANCE.md` 最後一段。

**2026-09-02 外部驗證修正**:首位外部驗證者(macOS Codex Chromium)在同一份
位元組上得到 44 筆 `label-overlap`——不是版面真的碰撞,是 CJK fallback 字型
的 `getBBox()` 含 leading 較高,而標題↔副標 18px 基線距只留 0.63px 餘裕。來源
環境以強制 `font-family:"Noto Sans TC"` **精確重現**(44,各視圖 9/9/7/8/11)。
修法在版型不在容忍值:副標基線 +3px(`emit.mjs` `NODE_TEXT`,router 估算同源)、
`__geometryReport.receipt` 記錄實際量測字型/DPR/引擎、`MAINTENANCE.md` M6 五組
字型掃描。上面那段 PASS 因此要讀成「在 Segoe UI 下 PASS」——現在報告會自己說。

## 識別化說明 (de-identification)

依本 repo `tools/COLLECTION-RULES.md`;每筆編輯宣告於 `tools/share-manifest.toml`:

- 整組 13 檔(6 支本集合檔 + 7 支同輪 refresh 檔)只有**一筆內容編輯**:
  carrier-playbook.md 的現場測試 ledger 指標(指向來源私有 outputs/ 樹的
  dated 檔)改為描述句;FT-1–FT-5 編號保留——那是讓主張可被有來源的人查證
  的部分。
- **2026-08-28 refresh**:來源側第二輪真火後,skill 本體新增六項驗證紀律
  (B-1〜B-6,借自 tt-a1i/archify,MIT:診斷物件格式、修復次序+有界修復、
  凍結+SHA-256 收據、visual_review 三態回報、視窗含納量測、幾何自檢儀器
  前置條件);三支集合檔隨之重刷(SKILL.md 仍 verbatim)。新增**兩筆內容
  編輯**,同一類:來源新增的借用帳指標(指向同一棵不出貨的 outputs/ 樹的
  dated 分析檔)改為描述句,B-n 編號保留。
- view-integrity-checks.md §3 的 CPO 例子是**經考慮的保留**:公開產業術語、
  data-gap 類的錨定範例,不是被扣住不出貨的領域 profile 知識(界線與舊字典
  出貨領域名、不出貨 profile 檔一致)。
- carrier-playbook.md 的 headless 驗證三事實(port 服法、截圖落點)是**來源
  機器的實測值**,檔內附 review-when 復查配方;採用者環境不同就照配方重測,
  別直接信值。
- **2026-08-29(執行層收錄)**:`archdiag/` 11 檔進來,其中 9 檔 verbatim。
  兩筆編輯,同一類、都已宣告:`MAINTENANCE.md` 的維護儀式指令操作在來源
  不出貨的 `outputs/diagram-authoring/` 樹上,指令逐字保留、上方加share note
  說明採用者的對應目錄;`carrier-playbook.md` 的 `Reference builds:` 那行
  (三支同樣在 `outputs/` 裡的 build 腳本)改為描述句,並補上函式庫在本 repo
  的落點。同輪本 repo 新增 `.gitattributes` 把 `archdiag/**` 釘成 LF——**這不是
  格式偏好,是收據的前提**:少了它,一次 CRLF checkout 就能在測試全綠的情況下
  作廢每一張已驗收交付物的 sha256。`vendor/archify-geometry.mjs` 是第三方
  (tt-a1i/archify,MIT)逐字收錄,檔頭帶上游授權行與 review-when。
