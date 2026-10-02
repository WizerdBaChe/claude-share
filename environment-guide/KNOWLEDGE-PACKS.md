---
xi: 1
what: 知識包的形狀、抽象判準與現況紀錄——三個知識包本體不分享時，對外代表它們的那一頁 (knowledge-pack shape, criteria and status record; the page that stands in for the packs when they are withheld from a share)
tags: [knowledge-pack, philosophy, share, status-record]
aliases: [知識包, knowledge pack, 知識包判準, 知識包現況, render-perf 現況, system-design 現況, code-layering 現況]
status: live
---

# 知識包 (Knowledge Packs)：形狀、判準與現況

> **這份文件描述，不規定。** 定位與 `PHILOSOPHY.md` 相同：寫給人看，說明「知識包」
> 這一類資產長什麼樣、什麼時候算得上可依賴、什麼時候可以對外分享，並記錄此刻
> 三個知識包各自走到哪裡。規範力在各包的 intake 規格
> （`skills/render-perf/INTAKE.md`，§6a 起約束所有知識包）與各包自己的 `SKILL.md`；
> 與它們衝突時，規範檔贏。
>
> 它存在的直接原因：2026-10-02 的分享版同步 (CLAUDE_SHARE refresh) 裁定知識包本體
> 不出（內容是主人的策展，而且三包都還在「種子」狀態），但「這類東西是什麼、
> 怎麼判斷它成熟了」這份資訊應該出去。所以本檔在分享版裡代替知識包本體。

---

## 一、形狀 (the shape)

一個知識包是一個 skill，但分工跟一般 skill 相反：一般 skill 是**程序**（怎麼做），
知識包是**參照**（讀什麼再答）。固定形狀：

| 部件 | 內容 | 不放什麼 |
|---|---|---|
| `SKILL.md` | 判斷與路由：觸發句、triage、Route 1 覆蓋表（決策面 → 參照檔）、Route 2 收集、ask gate、split watch | 知識本體 |
| `references/<topic>.md` | 一題一檔，以它服務的**決策**命名；四欄 front matter `date / source / verified / review-when` 缺一不可；主張分型 FACT／HEURISTIC／NUMBER | 沒有裝置等級與日期的數字 |
| origin 欄 | `user-supplied`（主人交付的原文，最高位階）或 `model-authored`（從已稽核的 session 交付物蒸餾，必須附「執行過／抓取過什麼」的 `verified:` 行與「本檔未驗證」段） | 模型記憶 |

三條姿態，每包都寫在自己的 `SKILL.md` 裡：

- **缺口要說出口**：觸發命中但沒有參照檔的分支，回答「this branch has no pack
  reference yet」再從一般知識作答並標明；永遠不把模型記憶包裝成策展內容。
- **ask gate**：庫存稀疏時，路由或「收不收」有歧義就問一句，不猜（使用者裁定
  2026-08-16，2026-09-23 重申）。
- **檔數與 Route 1 表是同一個事實**：任何 intake 都在同一個動作更新兩者。

---

## 二、抽象判準 (the criteria)

判準寫成「這個包的性質」，不寫成「做某事時要記得」。四個狀態，各自獨立：

**可登記 (registrable)** — `SKILL.draft.md` 可改名為 `SKILL.md` 的條件：至少一個真實
主題檔存在，且觸發字典列在同一個 commit 加入（INTAKE §7）。

**可依賴 (dependable)** — 以**分支**為單位，不以包為單位。一個分支「有覆蓋」若且唯若
一個四欄齊全的參照檔存在、且 Route 1 表有一列指向它；表裡不得出現指向不存在檔案的列
（INTAKE §6）。「這個包完整了」在這個系統裡**沒有定義**；有定義的只有「這個分支有覆蓋」。

**可分享 (shareable)** — 四個條件同時成立，才把本體放進分享版；差一個，分享版放的
就是本檔，不是包：

1. 每個參照檔的 origin 是主人可再散佈的：user-supplied 策展是主人自己的東西；
   model-authored 檔帶著它的執行證據行。
2. 沒有任何參照檔帶著「編輯不掉」的私有樹指標（非系統碟絕對路徑、session id、
   只在本機存在的交付物名）。附帶性的（一行 `source:` 裡的來源路徑）可以在收錄時
   按類別去識別；構成內容本身的不行。
3. 包已達到「對它自己宣告的範圍而言算完整」：`SKILL.md` 描述承諾的每個觸發面，
   在 Route 1 表都有檔；或者描述的觸發句已縮到只剩有覆蓋的列。兩者擇一即可——
   一個誠實縮小範圍的包，可以在三個檔的時候就達標。
4. 觸發字典裡該包的段落跟著本體一起出（兩段式動作：收錄＋改路由，缺一個就是
   讀者跟著指標走到空處）。

**拆包／退役 (split / retire)** — split 的訊號事先登記在 `SKILL.md` 的 split watch，
依**任務型態**（觸發句不相交）拆，不依大小拆；退役只封存，不刪除。

> 判準「可分享」第 3 條是 2026-10-02 本檔提出的操作化定義，尚未被任何一個包的
> 達標事件驗證過。review-when：第一個包達標、或被判定「宣告範圍永遠縮不到覆蓋
> 範圍」時，重寫這一條。

---

## 三、現況紀錄 (status record，as-of 2026-10-02)

本節是**投影**：每列從各包 `SKILL.md` 的 Route 1 表與 `references/` front matter
讀出，任何 intake、拆包、退役都在同一個動作更新這裡（INTAKE §8）。單獨改這裡
而不改包，是第二份會爛掉的副本。

| 包 | 題目 | 檔數 | 有覆蓋的分支 | 描述承諾但無檔的分支 | origin | 最近 `date` | 姿態 | 可分享？ |
|---|---|---|---|---|---|---|---|---|
| `render-perf` | 前端渲染效能：DOM／元件數量與渲染管線 | 1 | 長列表虛擬化 (list virtualization) | 每幀 style/layout/paint 成本；GPU／合成層爆炸 | user-supplied | 2026-08-16 | 先量再改（measure-first triage） | 否（第 3 條：表內 3 列只有 1 列有檔） |
| `system-design` | 服務的外側：queue、容量、延遲 | 2 | 要不要上訊息佇列及其義務；Little's Law／M/M/1 容量與延遲 | broker 選型、分片、一致性模型、快取策略、重試預算 | user-supplied | 2026-08-16 | 低回答優先、高收集可用性；ask gate | 否（第 3 條） |
| `code-layering` | 一個程式的內側：怎麼切、怎麼接線、怎麼測 | 3 | 依賴方向與要不要抽埠；組裝根與生命週期；轉接器契約測試 | 模組邊界、DDD 聚合、schema 演進、錯誤模型、套件結構 | model-authored（已稽核交付物＋執行過的測試） | 2026-09-23 | ask gate | 否（第 3 條；第 2 條的 `source:` 行帶本機路徑，屬附帶性，可去識別） |

Split watch（各包自己登記的下一個訊號）：`system-design` 等「投遞機制」（broker
選型、分區、順序）成為第三個以上的檔；`code-layering` 等 DDD 戰術設計或錯誤模型
聚成兩個檔。`render-perf` 未登記。

版本線（只記主人裁定與結構事件；逐 diff 看 git log）：

- 2026-08-16｜`render-perf`、`system-design` 登記；姿態「低回答優先、高收集可用性」。
- 2026-08-17｜兩包不進分享版 (CLAUDE_SHARE)：未完成。觸發字典的知識包段落在分享版
  同步移除。
- 2026-09-23｜「拆包」：結構叢（分層、組裝根、契約測試）自 `system-design` 分出為
  `code-layering`；INTAKE §6a 增訂 origin classes，三個 model-authored 檔是第一批。
- 2026-10-02｜分享版同步裁定：三包本體仍不出；新增本檔（判準＋現況）隨分享版出，
  各包在分享版 manifest 的 not_shipped 條目改指向本檔。

---

## 四、這份文件自己的規矩

- 只描述、不規定。想寫「必須／禁止」時，那句話屬於 INTAKE.md 或該包的 `SKILL.md`。
- §三 是投影，不是帳本：更新它的動作永遠是「改了包，順手改這裡」，不是反過來。
- review-when：(a) 任一包通過「可分享」四條 → 分享版 manifest 該包條目的 review-when
  同時觸發，重新裁定；(b) 第四個包誕生 → 本節加一列，同 commit；(c) INTAKE.md 的
  front matter 欄位集改變 → §一 的表重讀；(d) 判準第 3 條依上面的註記重寫。
- 分享版：本檔隨 `environment-guide/` 出，形式 verbatim；三包本體與各自的
  `references/` 不出。本檔不得出現非系統碟絕對路徑或 session id——它是為了能
  verbatim 出去而寫的。
