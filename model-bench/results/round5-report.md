# 第五輪報告 — 2026-10-10｜Round 5: t02 / t04 / t11 re-measured without the gold leak

**觸發**：第四輪發現 t02、t04、t11 的 `setup()` 把標準答案 `.gold.json` 寫進受測模型的工作目錄（`round4-report.md` §0 第 1 點）。交接單 `reports/handoff-2026-10-10-cc295-writeback.md` WB-03 修正後，只重跑這三題。
**修正**：`tasks/_common.py` 新增 `gold_path(workdir)`，答案檔改放在工作目錄**旁邊**（`<workdir>.gold.json`），三題的寫入與讀取都改經由它（commit `e640c76a`）。這三個 task 模組之前其實沒有進版控（`.gitignore` 的 `tasks/` 一併吞掉了 `tools/model-bench/tasks/`），同一個 commit 補上；第一到四輪跑的是修正前、未進版控的版本。
**驗證**：`bench.py selftest` 51 個對照、0 個問題；負對照：`bench.py prep --task t04_search_inventory` 之後，工作目錄內沒有 `.gold.json`，旁邊的 `<workdir>.gold.json` 存在。
**紀錄**：`round5-local-runs.jsonl`（27 列，`claude -p`）、`round5-agent-runs.jsonl`（6 列，Agent tool）；機器摘要 `round5-local-summary.md`、`round5-agent-summary.md`；判分腳本 `round5-agent-judge.py`（`round4-agent-judge.py` 的副本，只改了 session 路徑）。
**範圍**：只量測。`ops/20-dispatch.md` §4 的表格數字是否回寫，仍待使用者裁決（R1）。

## 0. 先講結論

1. **`claude -p` 路徑：答案外洩沒有明顯灌水。** 修正前後三題的通過數差距都在 n=3 的雜訊範圍內（見 §1）。`claude -p` 沒有保留 transcript，第四輪是否有人讀過答案仍無法確認，但數字本身沒有因修正而下滑成另一個樣子。
2. **Agent 路徑 t04 反而變好**：medium 0/3 → 2/3，high 1/3（那 1 次讀到答案）→ 2/3；本輪 6 次 `gold_seen` 全為 false。失誤仍然只有一種：集合正確、排序錯（行號用數值排序，而題目要字典序）。high 依然沒有修好排序。
3. **t11 長上下文計數仍是 haiku 的弱點**：haiku@high 0/3、haiku@medium 2/3，sonnet@low 3/3。兩輪合計 haiku 在 t11 的 full 臂是 5/12，維持「t11 屬中階」的原判斷。
4. **t02 不受影響**：三臂兩輪都是 3/3。
5. 以上都是 n=3；第四、五輪方向一致的只有「t02 便宜層可接」「t11 haiku 不穩」「t04 失誤是排序」三點。

## 1. 修正前後對照（`claude -p`，full 變體，n=3）

| 題 | 臂 | 第四輪（答案在工作目錄內） | 第五輪（答案在外） | 第五輪每次成本 |
|---|---|---|---|---|
| t02 擷取 | haiku@medium | 3/3 | 3/3 | $0.0109 |
| t02 擷取 | haiku@high | 3/3 | 3/3 | $0.0110 |
| t02 擷取 | sonnet@low | 3/3 | 3/3 | $0.2089 |
| t04 搜尋盤點 | haiku@medium | 2/3 | 2/3 | $0.0125 |
| t04 搜尋盤點 | haiku@high | 3/3 | 2/3 | $0.0113 |
| t04 搜尋盤點 | sonnet@low | 3/3 | 3/3 | $0.2077 |
| t11 長上下文 | haiku@medium | 1/3 | 2/3 | $0.1325 |
| t11 長上下文 | haiku@high | 2/3 | 0/3 | $0.1478 |
| t11 長上下文 | sonnet@low | 3/3 | 3/3 | $0.4625 |

第五輪失誤 6 次：t04 兩次（haiku 兩臂各一次，「集合正確但未排序」）、t11 四次（計數差 1–3 三次，加總差 −31.24 一次——和第四輪同一個數字）。

## 2. Agent tool 路徑（haiku-5-5，per-call effort，t04，n=3）

| effort | 第四輪 | 第五輪 | 第五輪每次成本 | 第五輪 `gold_seen` |
|---|---|---|---|---|
| medium | 0/3 · $0.065 | 2/3 · $0.079 | $0.079 | 0/3 |
| high | 1/3 · $0.089（該次讀到答案） | 2/3 · $0.066 | $0.066 | 0/3 |

六次派工同時發出（`subagent_type: general-purpose`、`model: haiku`），prompt 與第四輪同形：一句工作目錄說明加上 `bench.py prep` 產生的題目。解析出的模型 6 次都是 `claude-haiku-5-5`。

## 3. 方法注意

- 答案檔現在放在工作目錄的**上一層**。受測模型若主動 `ls ..` 仍看得到；這是交接單指定的作法，`gold_seen` 偵測保留，作為這個殘留風險的觀測。本輪 0 次。
- 同一個 rep 編號在不同 effort 下產生的是**同一棵檔案樹**（例如 medium r1 與 high r1 都是 13 個定義），所以 effort 之間的比較是同題對照，不是不同題。
- 本輪 `claude -p` 與 Agent 派工先後執行，沒有互相干擾牆鐘時間。
- 總花費（列價）：`claude -p` 約 $3.62，Agent 約 $0.44。
