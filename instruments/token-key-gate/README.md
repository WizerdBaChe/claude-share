# token-key-gate — 點過的代號不能吃掉整頁的快捷鍵

status: live 2026-10-05 · 規則出處：`rules/deliverable-doc-refs.md`（「a focused token yields every key except its own activation keys」段）

## 它守哪一條性質

定義卡機制的代號 (token，`.ref` / `.sym` / `.num`) 是 `tabIndex=0`，滑鼠一點就把焦點留在代號上。
這時鍵盤處理器 (keydown handler) **只能攔代號自己的 Enter / Space**，其他鍵——⌫ 返回、G 詞彙表、
M 目錄、翻頁——都必須照常送到頁面。

2026-10-05 在 R07 介紹頁沿用 SSLD 教科書殼時抓到：教科書殼與 AssetVault `briefing-deck-shell`
兩種殼都對「焦點在代號上」的**每一個鍵**直接 return，於是點代號跳過去之後，⌫ 回不來、G 打不開，
要先點別處才恢復。之前所有檢查都是在 `document` 上發鍵，從沒在「剛點過的代號」上發，所以沒抓到。

## 用法

```powershell
python -X utf8 tools/token-key-gate/token_key_gate.py run <建好的頁面.html> ...
```

```powershell
python -X utf8 tools/token-key-gate/token_key_gate.py static <殼、建置腳本或資料夾> ...
```

```powershell
python -X utf8 tools/token-key-gate/token_key_gate.py selftest
```

- `run`（權威判決）：無頭 Chromium（1707×830、reduced-motion）點一個會跳頁的代號，把焦點留在它身上，
  按 ⌫ —— 捲動位置必須回到原處；再按 G —— `#gloss` 必須打開。判決 PASS / FAIL / UNDET；
  頁面沒有會跳的代號或沒有 `#gloss` 時是 UNDET，絕不當 PASS。沒裝 playwright 時 exit 2 並大聲說沒檢查。
- `static`（便宜的初篩）：掃殼與建置腳本裡的缺陷簽名行。只認得 2026-10-05 量到的兩種寫法，
  最後以 `run` 為準。
- `selftest`：兩種模式各跑雙向對照——兩種壞寫法必須 FAIL／命中，修好的寫法必須 PASS／不命中。

## 修法（一行）

把「代號判斷」與「Enter／Space」合成同一個條件，其他鍵一律放行：

```js
if (e.target && e.target.closest && e.target.closest('.ref,.sym') && (e.key==='Enter'||e.key===' ')){ e.preventDefault(); /* 跳到定義 */ return; }
```

deck 殼的寫法是另有一個 listener 處理 Enter/Space，翻頁 listener 只需把 `return` 的條件加上
`&& (e.key === 'Enter' || e.key === ' ')`。

## 已修的上游（2026-10-05）

| 上游 | 角色 | 驗證 |
|---|---|---|
| AssetVault `briefing-deck-shell/deck-shell.html` | 共用 deck 殼（素材庫參考實作） | `run`：FAIL → PASS（⌫ 1660→0，G 4 列） |
| `skills/paper-story/assets/deck-shell.html` | paper-story 釘版副本 | 重新複製＋記 sha；S8 PASS |
| SSLD `05_交付/textbook-src/shell.html` | 長文件殼參考實作（規則點名） | 建好的教科書換這一行後 `run`：FAIL → PASS（⌫ 15129→0，G 98 列）；`build_textbook.py` 加了靜態守門（雙向對照過） |

會讀這些上游的建置器下次重建時自動帶入修正：`build_dossiers.py`（案卷殼由教科書殼產生，
`'.ref,.sym'` 錨點數不變，轉接器實跑通過）、T47–T55 `build_page_*.py`、`build_deck_v2.py`
（快照由 AssetVault 重寫）、n8n `exp-fast-tasks/build_pages.py`（建置時讀 AssetVault）、
paper-story `render_story.py`。

## 已知仍帶缺陷、刻意不修的副本（使用者裁決 2026-10-05：既有產出不重建，標錯就好）

清單是**衍生的**，隨時可用 `static` 對資料夾重掃；下表是 2026-10-05 的快照（共 75 檔）。

**下次建置仍會再產出缺陷的專案內副本**（要再用這些專案的建置器時，先套上面那一行修法）：

- COMSOL_TEST `20_manual-and-report\build_pages.py`（殼內嵌在腳本裡）
- SSLD 邊緣耦合調研 `教戰手冊_發布版\build\_shell.html`、`T00_…\pages\_shell_ssld_textbook_copy.html`（教科書殼的逐位元副本，帶 sha 記錄）
- SSLD 玻璃基板 `05_交付\deck-src\deck_template.html`、`deck_template_audience.html`（專案 deck 模板）

**只是既有產出（不再建置、不再讀）**：

- SSLD 玻璃基板：`05_交付` 的教科書與四份簡報、`deck-src` 的 artifact 片段與 20260901 快照、
  `07_案卷` 與 `討論包\02_案卷` 的案卷頁、`討論包\05_講稿與教材` 三份、`討論包\index.html`、
  T47／T48／T49／T50／T51／T55 展示頁
- SSLD 邊緣耦合調研：`廣蒐成冊教戰手冊.html`、`邊緣耦合元件設計調研_補充說明.html`
- COMSOL_TEST：`manual.html`、`report.html` 與 `展示與教學` 的兩份副本
- n8n-concept-survey：`deck-3-fast-task-fit.html`、`exp-fast-tasks\pages\deck3.src.html`
- obsidian_Nathan `literature\PaperSurvey\`：各論文的 `onepage.html`／`talk-deck.html`／`keypoint-onepager.html`（含 `_calibration`）
- design-style-testbed `out\ui-ux-pro-max\T2-iso.html`（實驗紀錄，保持原樣）
- `skills\paper-distill\archive\2026-09-03-split\assets\deck-shell.html`（封存）

使用者在這些舊頁上遇到「點了代號後 ⌫／G 沒反應」：先點頁面空白處再按即可。

review-when：任一共用殼的鍵盤處理器改寫成不同形狀（`static` 的簽名可能認不得，以 `run` 為準）；
或代號 class 增加新種類（`TOKENS` 要跟著加）。
