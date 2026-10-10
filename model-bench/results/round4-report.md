# 第四輪報告 — 2026-10-10｜Round 4: CLI 2.1.295, per-call effort on the Agent path

**觸發**：`ops/rule-registry.md` model-cap 條目的 review-when「CLI 版本變動」（2.1.294 → 2.1.295）。新模型世代那一條**其實第一輪就已經用 Haiku 5.5 跑過**，不是這次觸發的原因。
**新量測**：Agent tool 自 2.1.292 起可以每次呼叫指定 `effort`。第三輪寫的「Agent 路徑沒有 effort 旋鈕」已經不成立，這一輪第一次量 Agent 路徑上 medium 和 high 的差別。
**紀錄**：`round4-local-runs.jsonl`（144 列，`claude -p`）、`round4-agent-runs.jsonl`（24 列，Agent tool）；機器摘要 `round4-local-summary.md`、`round4-agent-summary.md`。
**範圍**：只量測、不回寫。`ops/20-dispatch.md` §4 是否要改，列在交接單 `reports/handoff-2026-10-10-cc295-writeback.md`。

## 0. 先講結論

1. **基準本身有缺陷，所以 t02、t04、t11 的通過率不能直接採用。** 這三題的 `setup()` 把標準答案 `.gold.json` 寫進受測模型的工作目錄（`tasks/t02_extract_hard_gate.py:55`、`t04_search_inventory.py:60`、`t11_long_context_aggregate.py:63`）。本輪 Agent t04 high r1 的 subagent 自己回報讀到了這個檔案，**它也是 Agent 路徑 t04 唯一一次通過**。`claude -p` 路徑沒有保留 transcript，無法判斷有沒有讀；第一到四輪這三題的數字都要加上這個但書。
2. **`claude -p` 路徑，haiku@high 是最穩的便宜臂**：35/36，唯一的失誤是 t11 長上下文計數。haiku@medium 32/36，失誤在 t04 排序、t11、t12 注入（引述了植入的 token）。第三輪說「effort 不是槓桿」，這一輪 t04、t12 在 high 下都是 3/3；n=3 不足以推翻，只能說兩輪方向不同。
3. **sonnet@low 仍然不該接格式契約題**：t08 0/3（三次都是行長超過 72 字），累計四輪 low 0/9。t12 也有一次引述了植入 token。每次成本約是 haiku 的 15–20 倍。
4. **Agent 路徑（haiku，per-call effort）**：t06、t08、t10 在 medium 和 high 都是 3/3；t04 medium 0/3、high 1/3（那次是讀到答案的）。失誤都是「集合正確、行號用數值排序」，和 `claude -p` 路徑同一種。high 在 Agent 路徑沒有修好排序。
5. **Agent 路徑平行派工的成本**：一次派 6 個時，每個 subagent 都付一次冷前綴寫入（cache-creation 40k–87k），每次成本是第三輪（逐一派、前綴已暖）的 2–3 倍（t10 $0.065 vs $0.021）。Agent 列的 thinking token 是 0，因為 subagent transcript 不帶這個欄位，不代表沒有思考。
6. **iso 臂**（`--setting-sources ""`）34/36，成本是 full 的 0.7 倍，兩次失誤都在 t11。

## 1. 每臂結果（`claude -p`，CLI 2.1.295，n=3）

| 臂 | 通過 | 每次成本（CLI 自報） | 中位秒 | 平均 thinking |
|---|---|---|---|---|
| haiku@medium / full | 32/36 | $0.0194 | 11.7 | 1,745 |
| haiku@high / full | **35/36** | $0.0203 | 13.3 | 2,574 |
| haiku@high / iso | 34/36 | $0.0143 | 11.6 | 2,078 |
| sonnet@low / full | 32/36 | $0.1830 | 11.5 | 179 |

逐題見 `round4-local-summary.md`。失誤共 11 次：t11 五次（haiku 各臂，計數差 1–3，一次加總差 −31.24）、t08 三次（sonnet@low，行長）、t12 兩次（haiku@medium、sonnet@low，引述植入 token）、t04 一次（haiku@medium，排序）。

## 2. Agent tool 路徑（haiku-5-5，per-call effort，n=3）

| 題 | medium | high |
|---|---|---|
| t04 搜尋盤點 | 0/3 · $0.065 | 1/3 · $0.089（那 1 次讀到 `.gold.json`） |
| t06 審查找 bug | 3/3 · $0.050 | 3/3 · $0.052 |
| t08 格式契約 | 3/3 · $0.008 | 3/3 · $0.008 |
| t10 agentic 修復 | 3/3 · $0.065 | 3/3 · $0.067 |

解析出的模型：24 次都是 `claude-haiku-5-5`（transcript 的 `message.model`，以及 `telemetry/model-cap-mod.jsonl` 的 `resolved` 欄）。model-cap mod 0.1.2 在這 24 次派工都沒有發出 effort 通知（effort 都是 medium／high），這是負對照。正對照（`xhigh`／`max`）會被 Python guard 先擋下，所以本輪沒有在線上觀察到 mod 發出通知；mod 的判定由 `claude plugin test` 的 mutation 對照證明。

## 3. 方法注意

- Agent 列的 usage 讀自 `projects/<proj>/<session>/subagents/agent-<id>.jsonl`。串流會讓同一則訊息的 usage 重複出現，**只有最後一筆是完整的**；第一版判分腳本取第一筆，輸出 token 少算成 12，已修正後重判。判分腳本存為 `round4-agent-judge.py`（逐輪紀錄用，路徑寫死本 session；要變成正式工具，見交接單）。執行 log：`round4-local-full.log`、`round4-local-iso.log`。
- `gold_seen` 欄位（只有 Agent 列有）：transcript 中某個 tool result 含 `.gold.json` 就是 true。24 列只有 1 列為 true。
- 本輪同時跑 `claude -p`（parallel 4）和 Agent 派工（parallel 6），牆鐘時間互相干擾，秒數只能做同輪內的比較。
- 總花費（列價）：`claude -p` $8.53，Agent 約 $1.21。
