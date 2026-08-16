# ACCEPTANCE — red-team 運作模式的真火驗收清單

這份清單分兩段。**A 段**是純本機、不需要任何模型、任何人都能盲跑的機械驗收——
來源環境與這份 share 拷貝都已驗過,你應該在採用前自己再跑一次。**B 段**需要
真的模型,來源環境已於 2026-08-15/16 驗過,但**在你的環境裡仍然是開放的**,
因為它驗的是你的模型層,不是這幾支腳本。

驗收原則沿用這個 repo 的規矩:**一個閘只能對它能判定的事下判斷**,而
「100% 通過」本身是要先懷疑量具的訊號。A 段每一項都同時說明「通過長什麼樣」
與「這一項驗不到什麼」。

---

## A 段 — 機械驗收(本機,無需模型)

> 前置:Python 3.10+;`cd` 進 `red-team/`。全部只用標準庫,不需要安裝任何東西。

### A1 · 錨點層的十個回歸案例

```git bash
python test_score_anchor.py
```

**預期**:最後一行印出 `10/10 cases behave as specified.`,離開碼 0,並印出
「An invented quote still voids the report」。

**重點在第 4 與第 9 個案例**(`invented quote`、`one repairable + one invented`):
它們是 2026-08-16 把這一層**放寬**時加上的守門案例。放寬一道閘,唯一站得住腳的
交代方式就是證明它仍然抓得到原本要抓的東西。若這兩項變成 PASS 以外的任何結果,
這份 share 對你就是壞的,不要用。

**這一項驗不到**:引文是否**真的**指出一個缺陷。那是層 5 的問題。

### A2 · JSON 取值的八個邊界案例

```git bash
python test_parser_rulers.py
```

**預期**:離開碼 0,印出 `disagreements: 4/8`,且**不要**出現
`WARNING: ... case(s) did not behave as this file predicts`。

四個分歧全都是「貪婪正則讀不到、平衡掃描讀得到」的方向。若出現 WARNING,
代表檔案裡那段邊界宣稱已經過期,要重新量而不是改測試。

**這一項驗不到**:你的模型實際會產出哪種形狀的回覆。它量的是兩把尺的差別。

### A3 · 端到端:引錯行號的報告會被修好,不是被殺掉

建立一個三行的假專案與一份「引文正確、行號差一」的報告,然後評分。

```git bash
mkdir -p /tmp/rt-fixture
printf 'def load(path):\n    handle = open(path)\n    data = handle.read()\n    return data\n' > /tmp/rt-fixture/mod.py
printf '```json\n[{"file":"mod.py","line":4,"quote":"    data = handle.read()","defect":"handle never closed","failure":"repeated calls exhaust descriptors","severity":"medium"}]\n```' > /tmp/rt-report.json
python score_redteam.py --repo /tmp/rt-fixture --report /tmp/rt-report.json --repair /tmp/rt-repaired.json
```

**預期**:`REPORT VERDICT: ACCEPTED-WITH-REPAIRS`,離開碼 0,那一列顯示
`mod.py:4->3`,並產生 `/tmp/rt-repaired.json`。

**為什麼這一項重要**:2026-08-16 之前,這份報告會被判 `REJECTED`。真實代價是
一個**已證實的目錄穿越 (directory traversal) 漏洞**被連坐丟掉,只因為同一份
報告裡另一個發現把行號寫錯一行。

### A4 · 捏造仍然作廢整份報告(A3 的負控制)

把 A3 的 `quote` 換成一句檔案裡沒有的話:

```git bash
printf '```json\n[{"file":"mod.py","line":2,"quote":"    handle.close()  # always closed","defect":"x","failure":"y","severity":"low"}]\n```' > /tmp/rt-fake.json
python score_redteam.py --repo /tmp/rt-fixture --report /tmp/rt-fake.json
```

**預期**:`REPORT VERDICT: REJECTED`,離開碼 **1**,該列verdict 為 `FABRICATED`,
並印出「an invented quote ... voids the whole report」。

A3 與 A4 必須**同時**成立。只有 A3 過代表閘被放寬到失效;只有 A4 過代表閘
嚴到會吃掉真發現。

### A5 · 層 5 的四條拒絕路徑

這四項不花任何一次模型呼叫,因為它們全部在呼叫**之前**就拒絕。

| # | 指令 | 預期 |
|---|---|---|
| a | `python redteam_verify.py --repo . --report /tmp/rt-repaired.json --author m1 --verifier m2 --grant t` | `REFUSED: no dispatcher module 'extdispatch'`,離開碼 1 |
| b | 同上,`--dispatcher` 指向一個只有 `MODELS`、沒有 `dispatch` 的檔案 | `REFUSED: ... missing ['dispatch']`,離開碼 1 |
| c | 用一個合格 dispatcher,但 `--author` 給一個它不認識的鍵 | `REFUSED: --author ... is not a model this dispatcher knows`,離開碼 2 |
| d | 用一個合格 dispatcher,`--author` 與 `--verifier` **相同** | `REFUSED: verifier must differ from author`,離開碼 2 |

(d) 是這一層的核心紀律:模型檢查自己的作品會複製自己的錯誤。它是硬性拒絕,
不是警告。

### A6 · 層 5 走完一次(用樁 dispatcher)

寫一個回傳固定答案的 20 行 dispatcher(契約見 `README.md`),然後:

```git bash
python redteam_verify.py --repo /tmp/rt-fixture --report /tmp/rt-repaired.json --author model-a --verifier model-b --grant t --dispatcher ./my_dispatcher.py
```

**預期**:印出 `1 survived / 0 refuted / 0 inconclusive, of 1.`。

**這一項驗不到**:你的模型會不會反駁。它驗的是**接線**——報告讀得進來、
prompt 組得起來、判決解析得出來、三值統計正確。

---

## B 段 — 真火驗收(需要真模型;你的環境仍是開放的)

下列每一項來源環境都在 2026-08-15/16 用真的外部模型跑過,結果寫在
`README.md` 的量測表。它們在你的環境**沒有**被驗過,因為驗的是你的模型層。

| # | 要驗什麼 | 怎麼驗 | 來源環境結果 |
|---|---|---|---|
| B1 | 格式指令放第一行是否真的有差 | 同一任務兩個 arm,格式指令一個放頭一個放尾 | 12/12 接受 vs 8/8 拒絕 |
| B2 | 明列受審檔案能否止住範圍漂移 | 一個 arm 只給 commit,一個給檔案清單,兩者都帶 `--commit` 評分 | 未列:438 秒錨在未追蹤檔案;列出:3/3 錨定、110 秒 |
| B3 | 授權空答案能否降低捏造 | 對一個**乾淨**的 commit 派工,看回不回得出 `[]` | `EMPTY-ACCEPTED` 是正確結果 |
| B4 | 錨定 prompt 的抑制代價 | 同一 reviewer、同一 commit,錨定/未錨定各跑一次,比較發現數 | 7(未錨定)vs 2(錨定) |
| B5 | 層 5 會不會把真發現誤殺 | 塞一個**已知為真**的發現進去驗證 | 首次實跑 3 個裡錯 2 個——原因是把工具失敗當成反駁,已修 |
| B6 | 層 5 會不會放過假發現 | 塞一個**已知為假**的發現進去驗證(正控制) | 校準用;缺這一項的話 B5 單邊校準沒有意義 |

**B5 與 B6 必須成對做。** 只用「該抓的」校準,一個全部否決的驗證器會拿到
100 分。這是這個 repo 反覆記錄的同一類錯誤。

---

## 這份拷貝的驗證狀態

| 項目 | 狀態 |
|---|---|
| A1 `test_score_anchor.py` | **2026-08-17 於本 share 拷貝實跑通過**(10/10,離開碼 0) |
| A2 `test_parser_rulers.py` | **2026-08-17 於本 share 拷貝實跑通過**(8 案例、4 分歧、無 WARNING) |
| A3 / A4 端到端評分與負控制 | **2026-08-17 實跑通過**(`ACCEPTED-WITH-REPAIRS` 4→3;捏造案由 A1 案例 4、9 覆蓋) |
| A5 四條拒絕路徑 | **2026-08-17 實跑通過**(離開碼 1/1/2/2,如上表) |
| A6 層 5 接線 | **2026-08-17 以樁 dispatcher 實跑通過**(1 survived / 0 / 0) |
| B1–B6 | **開放**。來源環境 2026-08-15/16 已驗;此拷貝**未**接過任何真實模型 |

A6 的樁 dispatcher 是為了驗接線而寫的,**不是**一次真實的對抗性驗證。
把「腳本會動」與「模型會反駁」分開記,是這份清單存在的理由。
