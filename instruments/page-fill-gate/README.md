# page-fill-gate — HTML 寬度使用閘門｜Human-readable page-fill gate

> **中文摘要｜Chinese summary**：這支 instrument 檢查人讀 HTML 交付物是否因
> left-anchored cap 留下不對稱右側空白。它只回答「頁面是否使用了被分配的寬度」，
> 不回答閱讀行寬、垂直溢出或美觀；每次執行都先跑 known-bad／known-good controls。
>
> **English summary**: This instrument checks whether a human-readable HTML deliverable
> uses its allocated width instead of leaving an asymmetric right-side void caused by a
> left-anchored cap. It does not judge line length, vertical overflow, or aesthetics;
> every run calibrates itself with known-bad and known-good controls.

## 快速導覽｜Quick guide

| 項目 | 中文 | English |
|---|---|---|
| 入口 | 先看 class table，再依 built HTML 執行 fill gate | Read the class table, then run the gate on built HTML |
| 正確期待 | exit 0 = 無 FAIL；exit 1 = 有 FAIL；exit 2 = 儀器缺席，不能宣稱 pass | 0 = no FAIL, 1 = FAIL found, 2 = instrument unavailable and no pass claim |
| 校準 | known-bad 必須 FAIL、known-good 必須 PASS，任一失敗整次無效 | The bad control must fail and the good control must pass |
| 不回答 | 不取代人眼 visual review，也不處理高度方向 fit | It does not replace visual review or vertical fit checks |

status: live 2026-09-04 · owner: 使用者裁決（寬度缺陷診斷筆記，來源環境 outputs/ 樹下的一份紀錄，不隨本分享收錄）

## 它守哪一條性質｜Property under test

在這台機器（2560×1440 @150% → 邏輯視窗 1707×830；外接 FHD 1920×950）上，人讀的 HTML 交付物
**不得留下不對稱的右側空白**。具名缺陷叫 **靠左錨定上限 (left-anchored cap)**：頁面容器或有
底色／邊框、獨佔一列的區塊被 `max-width` 卡住又靠左貼齊，右邊空一大塊。2026-09-04 量到一個殼
的 `max-width:1060px` 擴散成 13 份交付物，使用率只有 60–69%。

置中而左右對稱的空白（短篇閱讀欄）是另一種、被允許的形狀。**一頁該填多少，看它的類別。**

## 類別是資料，不是程式分支｜Classes are data, not code branches

`page_classes.json` 一列＝一類：`mode`（centered / fill / centered-or-fill）＋門檻。頁面用
`<html data-page-class="…">` 宣告；沒宣告的頁面由結構推斷，判決降級（FAIL→WARN），因為閘門
只能裁它判定得了的事。推斷升格為宣告的觸發條件寫在 `unknown_policy.promotion_trigger`。

| class | 中文 | 規則 | 目前對應 |
|---|---|---|---|
| document-short | 短篇閱讀頁 | 置中、左右留白差 ≤ 8px、fill ≥ 45% | audience-fit 報告、owner-view |
| document-long | 長篇參考文件 | reach ≥ 85%；`data-rail` 側欄算內容 | SSLD 教科書殼血脈（主文＋本節速查 rail） |
| deck | 一頁一螢幕簡報 | 每張 `.slide` 各自量，reach ≥ 85% | deck-shell（vault、paper-story、paper-distill、SSLD 快照） |
| tool | 操作型 GUI | reach ≥ 90%；> 1920px 的上限是 clamp 不是 cap | DIT、AssetVault GUI、HTMLToolsLobby 工具 |
| diagram | 圖為主載體 | 置中對稱 **或** reach ≥ 85%；fill ≥ 60% | diagram-authoring 產物 |
| dashboard | 卡片與表格儀表 | reach ≥ 85% | auto-fit 卡片格 |

**新類別怎麼加**：在 `page_classes.json` 加一列（`zh`、`mode`、門檻、`notes`），在
`tests/test_fill_gate.py` 的 `CASES` 加一對正負 fixture，跑測試；少任一邊，測試會故意失敗
（單邊校準等於沒校準）。不要為新類別寫程式分支，也不要在規則檔用散文開例外。

**區塊層級升格**：某個選擇器的「較窄靠左區塊」被人回報過一次後，把選擇器前綴寫進
`block_fail_selectors`，該類發現從 WARN 變 FAIL。

## 用法｜Usage

```powershell
python tools/page-fill-gate/fill_gate.py <built.html> [...] [--viewport 1707x830] [--class deck] [--json] [--quiet]
python tools/page-fill-gate/tests/test_fill_gate.py      # 每類正負各一，controls 必須觸發
```

每次執行都先跑兩個對照：`fixtures/known-bad-left-cap.html` 必須 FAIL、`fixtures/known-good-fill.html`
必須 PASS，任一沒觸發就整次無效（RuntimeError）。退出碼 0 無 FAIL、1 有 FAIL、2 儀器缺席
（Playwright／Chromium 不在）——2 的時候呼叫端要大聲 WARN 並且不得宣稱此性質。

一行輸出長這樣：`fill-gate: FAIL 1707x830  class=document-long reach=69% fill=64% void L/R=72/439px  教科書….html`，
`reach` 是內容右緣到內容區右緣的比例，`fill` 是內容左右緣之間的比例，chrome（固定側欄 TOC）已扣除。

## 量法｜What it can and cannot see

只算有字、有底色／邊框、或是媒體的方塊，純包裝層不算，所以 `.sfit` 之類滿版 wrapper 不會遮掉裡面
卡在 56em 的框。deck 類逐張 `.slide` 量前 8 張。看不見的：字元級的閱讀行寬（那是設計判斷，
留給人）、高度方向的溢出（那是 fit-gate 的事）、外觀好不好看（人眼）。

## 接線位置｜Integration points

| 誰呼叫 | 何時 |
|---|---|
| SSLD `05_交付/deck-src/fit_gate.py` | fit 三視窗之後，同一批 built html |
| paper-story `render_story.py` S7b | 每次渲染，緊接 S7 fit |
| SSLD `07_案卷/tests/test_dossiers.py`、`09_討論包/_src/tests/test_pack.py` | DOM 段 |
| diagram-authoring `carrier-playbook.md` B-5 | 交付前的 containment 量測旁邊（上界之外補下界） |
| 全域規則 | `ops/environment.md` §Display（性質）、`rules/deliverable-doc-refs.md`（HTML 與產生器路徑觸發）、CLAUDE.md 一行 |

## 基準｜Baseline before the fix (measured 2026-09-04)

| 檔案 | class | 1707×830 reach | 判決 |
|---|---|---|---|
| SSLD 教科書／案卷 index | document-long | 69% | FAIL（靠左上限 1060px） |
| PaperSurvey onepage KEYPOINT 框 | deck | 框 65% 於同列獨佔 | WARN（區塊） |
| mfp-audit-f5 | diagram | 對稱 218/218px | PASS |
| SSLD 技術版簡報 | deck | 96% | PASS |
| audience-fit 前後對照 | document-short | 對稱 | PASS |

## 修正後｜After the fix (measured 2026-09-04)

| 檔案 | class | 1707×830 reach | 1920×950 | 判決 |
|---|---|---|---|---|
| SSLD 教科書（流動主欄＋本節速查 rail） | document-long | 100%（fill 95%） | 100%（96%） | PASS |
| SSLD 案卷 index ＋ 三案卷 | document-long | 100%（95%） | 100%（96%） | PASS |
| PaperSurvey 六篇 onepage／talk-deck（S7b） | deck | 93–100% | 97–100% | PASS |
| SSLD 四份簡報（fit_gate 內建 fill） | deck | 100% | 100% | PASS |
| HTMLToolsLobby 15 個工具（上限改 clamp 1920） | tool | 99% | 99% | PASS |
| cpo-architecture-v1／vault svg-diagram demo | diagram | 98%／91% | 92%／86% | PASS |
| audience-fit 前後對照（置中 900px） | document-short | 對稱 426/426 px | 532/532 px | PASS |

殼的已驗收行為回歸（hover 卡、點跳、Backspace、G 詞彙表、手機單欄、1280 隱藏 rail、列印隱藏 rail、
正對照）15/15，腳本在該輪的 scratchpad `textbook_regress.py`；教科書在 390px 的橫向溢出（一個 `<th>` 與
nowrap 代號）**修正前就存在**，記為既有技術債，不在本輪。

review-when：螢幕或縮放改變（改 `reference_viewports`）；Anthropic 內建 artifact-design 的行寬措辭改變；
新增類別列（同一個 commit 補 fixture 對）；Playwright `page.evaluate` 語意改變。
