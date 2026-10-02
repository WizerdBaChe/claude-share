# rule-usage-census — 規則使用率普查 (rule usage census)

> status: advisory — WARN-only；讀者是人或 LLM，沒有任何下游工具消費它的輸出。

**回答的問題**：哪些規則面（全域 `CLAUDE.md` 的條文、`ops/*`、`rules/*`、skill）在真實 session 裡
真的被用到，以及用到它們的主迴圈模型 (main-loop model) 是誰。這是 `ops/40-maintenance.md` §3
「刪條文前先找活著的證據」那一步的儀器 (instrument)；在它之前那一步只有 grep。

**資料來源（都是既有的，本工具不寫任何 telemetry）**

| 來源 | 給什麼 | 既有讀取工具 |
|---|---|---|
| `~/.claude/projects/<project>/<session>.jsonl`（`--archive` 可改指到同結構的逐字稿鏡像目錄） | 每個 session 的主迴圈模型、工具呼叫、助理輸出文字 | `tools/session-find.py`（查單一 session） |
| `telemetry/rule-loads.jsonl` | 哪個規則檔在哪個 session 被載入 (InstructionsLoaded) | `tools/context-budget/rule_loads.py`（只看載入） |

**先前工具與本工具的差別**：`context-budget/rule_loads.py` 只看載入事件、看不到 `ops/*` 的 Read；
`model-effort-audit` 看模型×強度、不看規則；`trigger-probe` 量 skill 觸發。本工具是三者的交叉：
**規則 × 模型家族**。

## 用法

```powershell
python tools/rule-usage-census/census.py --selftest
python tools/rule-usage-census/census.py
python tools/rule-usage-census/census.py --since 2026-09-01
```

先跑 `--selftest`：它用兩份合成逐字稿做正對照（已知模型＋一個探針詞＋一次 `ops/OPS.md` 讀取，
必須被數到）與負對照（什麼都沒有，必須數到零）；任一側錯就 FAIL。整批掃描約 10 秒（555 份）。

## 讀表的規矩

- **探針 (probe) 量的是「這條規則的詞彙出現了」，不是「規則被遵守了」。** 觸發條件稀有的規則本來
  就少發，低比率只是 trim **候選**，不是判決（`40-maintenance.md` §3：absence of evidence ≠ proof of
  no effect）。要拿比率當刪除依據，先從同一語料算出該規則的**觸發頻率**。
- 探針表 `PROBES` 在 `census.py` 頂端；`CLAUDE.md` 新增一條就補一列，條文離開就退休那一列。
- Bench 目錄（`D--BenchRuns-*`）自動排除在 live 統計之外。
- Subagent 逐字稿不掃（它們也載入 `CLAUDE.md`，但規則面對它們的作用要另量）。

## 已知盲點

- `InstructionsLoaded` 看不到 `ops/*` 的 Read（不是 path-scoped），所以 `ops/*` 的使用率只來自
  逐字稿裡的 Read / shell 呼叫；hook 注入的規則文字（如 shell_transport_guard 的 notice）不算讀取。
- 2026-09-10 量到 `rule-loads.jsonl` 裡 **2,726 個未歸檔 session**（每天約 55 個、cwd 多在 `~`）也各載入
  一次 `CLAUDE.md`；來源未定（headless／helper session），本工具無法歸類——見首份報告的未決項。

首份報告：`reports/2026-09-10-rules-debt-audit.md`。
