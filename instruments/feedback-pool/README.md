---
xi: 1
what: feedback-pool — 子系統回授池：把 ledger 手寫的 feedback 列與機器早就在產的六種缺陷訊號依 target 分組計數，到門檻就在 HMI 亮一個 warn 問使用者要不要檢視；不建新儲存、不建新頁面 (the subsystem feedback pool — model-written ledger rows plus six existing machine signals grouped per target; a threshold raises one HMI warn asking for the user's review; projection, not a store)
tags: [feedback-pool, feedback-loop, closed-loop, process-ledger, system-hmi, instrument]
aliases: [回授池, 子系統回授池, feedback pool, 檢視回授, 回授 buffer]
layer: instrument
audience: builder
date: 2026-09-22
status: live
---

# feedback-pool（回授池）

STATUS: LIVE since 2026-09-22（claude-config；設計 `references/feedback-pool-design.md`；使用者裁決：四個決策項走建議值、同輪施工）
Proof-of-life: `python tools/feedback-pool/controls.py`

## 它回答的一句話

「哪個子系統（skill／tool／hook／規則）的問題已經累積到值得我花一輪檢視？」——池子自動累積，**檢視由使用者同意才開始**（預算花在檢視端）。

## 閉路的四個部件

| 部件 | 在哪 | 誰寫 |
|---|---|---|
| 手寫入口 | `python -X utf8 tools/process-ledger/ledger.py feedback --target <t> --symptom "…" --action fixed-inline\|left\|worked-around\|planned-work [--proposal "…"]` | 主迴圈，在**發現當下**（write-at-origin）；`hooks/feedback_notice.py` 在你第一次動某個子系統的檔案時提醒一次 |
| 機器感測 | S-2 hook 誤擋 `telemetry/hook-false-positives.jsonl`・S-3 HMI 長駐 fail・S-4 教訓 `held=no` 再發（已 fold 的歸到 fold 目標規則）・S-5 skill-co-upgrade 有 gap report 沒 disposition 的回合・S-6 LSE `reflux.jsonl` correction・S-7 `golive-check` fail | 各來源自己；本工具**只讀** |
| 比較器 | `feedback.py collect`：同一 target 自上次 fold 起的事件數 ≥ 3（registry `FEEDBACK_POOL`）→ due | 本工具；產物 `out/pool.json` 是可重算的投影 |
| 排空 | 你說「檢視回授」→ `feedback.py review <target>` 列證據 → 檢視輪（改規則／skill-co-upgrade／開 ticket）→ `ledger.py feedback-fold --target <t> --outcome adopted\|rejected\|deferred --ref … [--trigger …]` 歸零 | 主迴圈，使用者同意後 |

呈現只有一處：system-hmi 點 `feedback-pool.due`（warn＝有 due target；開場摘要 `system_hmi_summary.py` 會帶到）。

## 用法

```
python -X utf8 tools/feedback-pool/feedback.py report [--mine]   # 決定要不要檢視的那張表；--mine 只看本 session 的列
python -X utf8 tools/feedback-pool/feedback.py review rule:ops/OPS.md   # (target 以 rule:ops/OPS.md 為例) 該 target 的每一筆事件＋locator＋預填好的 fold 指令
python -X utf8 tools/feedback-pool/feedback.py collect           # 重算 out/pool.json，一行摘要
python -X utf8 tools/feedback-pool/feedback.py emit              # hmi-report/1（HMI source）
python -X utf8 tools/feedback-pool/feedback.py target-of <path>  # 從路徑推 target 標籤（hook 用同一函式）
```

`target` 字首封閉：`hook: skill: tool: rule: subsystem: lesson: project:`（LABEL-REGISTRY §2）。

## 邊界：交付物驗收不是池子的事（使用者確認 2026-09-22）

簡報、GUI、圖表做完後的驗收修正，留在**專案自己的紀錄**（UAT 清單 `ops/references/uat.md`、專案 D-nnn／ticket、advisory status line）；作用對象是交付物本身，不進池子。
只有當修正暴露的是**產出器**的缺陷——某個 skill／tool／hook／規則，或專案自己的腳本、模板、round kit——才多寫一列 `feedback`：`target` 是產出器（系統資產用對應字首，專案自己的用 `project:<name>`），`locator` 指回專案紀錄。判準一句話：同一類修正你講了第二次，問「是哪個產出器讓它一再發生」，答得出名字就寫一列。

## 刻意不做（設計 §3.7）

跨來源去重（同一缺陷兩個來源各報一列，檢視者判）；時間週期排空；自動派 skill-co-upgrade；GUI；
advisory status line（check 13 已有自己的 queue 與 HMI 點，不重複告警）。

## review-when

`ledger.py` 改列格式或落點；HMI 快照搬家或 `hmi-report/1` 升大版；任一感測來源改檔名；
一個月內 ≥3 個 due target 且零次 fold（那是排空閘的設計錯，不是池子）；notice 的 `planned-work` 回答率 ≥80%（收窄到非 `~/.claude` cwd）。
