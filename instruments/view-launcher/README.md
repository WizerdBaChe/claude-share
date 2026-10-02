# view-launcher — 最外層的檢視入口（側邊欄＋儀表）

**這是什麼**：一個啟動器（概念同遊戲／瀏覽器的 launcher）。左邊側邊欄是所有專案（最近有動的排上面），右邊是儀表：釘選的核心頁、各專案每一輪產出的頁面與簡報、最近更新。**頁面本身都留在原處，不搬、不複製、不修改。**

> **分享版說明 (SHARE EDITION)**：`views.json` 是範本——只留資料結構（群組、側邊欄、家族）與一列示範頁，
> 示範頁路徑裡的 `<CLAUDE_HOME>` 要換成你的設定目錄，或直接刪掉改成自己的頁面。「自動收錄」那一半讀的是
> 產出檔索引（`tools/cross-index`，來源環境的工具，沒有一起出貨），沒有它時啟動器只顯示釘選頁面並印出警告，
> 這是設計好的降級行為。建置會把 `All-View-Pages-Launcher.html`／`.md` 寫在設定目錄根，並在桌面補一個捷徑。

## 怎麼用

- 打開桌面的 `All-View-Pages-Launcher` 捷徑，或直接開 `~\.claude\All-View-Pages-Launcher.html`（2026-09-25 前叫 VIEWS.html；捷徑由每次建置自動補上）。
- 在 Obsidian 裡看同一份清單：`~\.claude\All-View-Pages-Launcher.md`。
- 側邊欄點專案 → 右邊依「輪次資料夾」分段列出，最新的輪次在最上面。
- 側邊欄的分組和首頁的分區是同一套（AI 工作系統／研究與文獻／模擬與參數調校／個人專案），組內順序固定，寫在 `views.json` 的 `sidebar`。綠點與右側數字＝七天內更新了幾個檔案。同一個家族的專案（例如 SSLD）收成一層；封存與維護、未登記的專案收合在最下面。
- 上方搜尋框：在首頁是搜全部，在專案頁是只篩這個專案。目前看的專案與搜尋字都寫在網址裡，重新整理、上一頁、加書籤都會回到同一個畫面。

## 新東西怎麼進來（不需要任何人登記）

| 來源 | 內容 | 誰維護 |
|---|---|---|
| 產出檔索引（每日 00:00 自動重發） | 已登記資料夾底下的 html／pptx／docx／xlsx。**新的輪次、新的頁面隔天自動出現**，依專案與輪次歸類 | 機器 |
| 專案登記表 `references\PROJECTS.md` | 專案名稱、狀態、根目錄。沒登記的資料夾照樣列出，標「未登記」 | 既有流程 |
| 釘選名冊 `tools\view-launcher\views.json` | 索引收不到的核心頁（例如各工具 `out\` 底下的監看頁），以**功能名稱**列在首頁 | agent 提案、你同意 |

啟動器在每日索引重發**之後**自動重建。要立刻重建：

```powershell
python -X utf8 $HOME\.claude\tools\view-launcher\build.py
```

## 已知限制

- 今天才產生的檔案要等當晚索引重發（或手動跑 `python -X utf8 ~\.claude\tools\cross-index\xi.py emit` 再重建）才會出現。
- 不在任何已登記資料夾底下的檔案不會自動出現——要嘛把資料夾登記進產出檔索引，要嘛釘選。
- 靜態頁面無法替你啟動需要伺服器的程式；這類項目只能顯示指令讓你複製。
- pptx／docx 點了是交給瀏覽器處理（通常是下載或用預設程式開）。
- 「多久前更新」看的是檔案修改時間，不代表內容是最新的。

## 自測

```powershell
python -X utf8 $HOME\.claude\tools\view-launcher\build.py --selftest
```

規則：`rules\naming-and-placement.md` PL-6（檢視頁先決定怎麼進最外層入口）；登錄 `ops\rule-registry.md` 的 `CORE_VIEW_ENTRY`。
