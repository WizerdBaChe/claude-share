---
what: routing-loop 一頁講解 — skill 路由與模型路由的回饋迴圈：怎麼運作、怎麼跑、怎麼判斷、怎麼講給別人聽
tags: [routing, skill-routing, model-routing, feedback-loop]
aliases: [路由迴圈, skill 觸發次數統計, 觸發條件統計, 路由檢討, routing loop]
layer: audience entry
audience: user
date: 2026-09-25
status: live v1
---

# 路由回饋迴圈 (routing-loop)

**一句話**：我把「這句話該用哪個 skill」「這件工作該派哪個模型」當成**可以被觀測的預測**。
字典和 description 是規格，探針事先預測，逐字稿事後驗證；每一次沒接住的都按「模式」歸類、
判斷原因，再回頭修規格。字典有大小上限，不會越修越胖。

設計：[routing-loop-design.md](../../references/routing-loop-design.md) ·
施工規格：[routing-loop-psm.md](../../references/routing-loop-psm.md)

## 1. 迴圈與負責的檔案

```
  SPEC 規格 ──▶ PREDICT 預測 ──▶ OBSERVE 觀測 ──▶ CLASSIFY 分類 ──▶ JUDGE 判斷 ─┐
    ▲                                                                        │
    └──────────── CONSTRAIN 約束（上限、擋下）◀── 使用者裁定的規格修改 ◀─────────┘
```

| 階段 | Skill 路由 | 模型路由 |
|---|---|---|
| SPEC 規格 | `skill-trigger-dict.md` 關鍵詞、各 `SKILL.md` description | subagent 上限政策（haiku/sonnet；opus/fable 需核准）、Codex luna 分級 |
| PREDICT 預測 | `tools/trigger-probe/`（固定句組 → 預測會路由到哪） | —（不預測） |
| OBSERVE 觀測 | **本工具** `loop.py derive`（共用 `tools/skill-routing-audit.py` 的解析器） | **本工具**（Agent 派工的 model 參數、被擋紀錄、codex/extdispatch 呼叫） |
| CLASSIFY 分類 | `ops/references/skill-trigger-classes.md`（零觸發是不是新聞） | agent 類型 |
| JUDGE 判斷 | **本工具** `queue` → `label`（寫進 `labels.jsonl`）；實戰缺口用 `skill-co-upgrade` | 同左 |
| CONSTRAIN 約束 | 字典上限 56K（`hooks/ops_health_nudge.py`） | `hooks/model_cap_guard.py` |

## 2. 平常怎麼用

```powershell
python -X utf8 tools/routing-loop/loop.py run
```
約 1 分鐘：推導事件 → audit 留一筆快照 → 跑預測探針 → 寫一筆執行紀錄。**兩週跑一次**，或看到
`routing-loop.freshness` 變 warn 時跑（下一輪接上 system-hmi 後會自動提醒）。

```powershell
python -X utf8 tools/routing-loop/loop.py status
```
六個點：新鮮度、推導、待判斷群組、字典沒預測到的觸發佔比、探針、未指定模型的派工。

```powershell
python -X utf8 tools/routing-loop/loop.py queue
```
列出 2026-09-26 基準日 (baseline) 之後才**第一次出現**、還沒判斷的**模式群組**（依大小排序，
附最新一筆的原文摘錄）。基準日之前的舊積壓（首跑約 200 個群組）不算進 `skill-backlog` 警示，
要看就加 `--history`（可配 `--window N` 只看最近 N 天有動靜的）。

**判斷節奏**（使用者裁定 2026-09-26）：`loop.py run` 照舊兩週一次；只有兩種情況才去判斷——
出現新模式（`queue` 不是 0），或你回報某次路由判錯（用 `queue --history` 找到那個群組再判）。

```powershell
python -X utf8 tools/routing-loop/loop.py label g1e14d612a76 dict-gap --why "gate 是通用英文詞，comsol 以外的對話也會命中" --origin user
```

## 3. 事件與判斷

| 結果 (outcome) | 意思 | 要判斷嗎 |
|---|---|---|
| HIT | 字典的詞出現，該 skill 也觸發了 | 否 |
| BYPASS | 詞出現，但別的 skill 觸發了 | 要：誰對？ |
| MISS | 詞出現，沒有任何 skill 觸發（LATE = 同 session 稍後才觸發） | 要：該觸發，還是正確沉默？ |
| UNPREDICTED | skill 自動觸發了，但字典沒有任何詞預測到 | 要：字典缺詞嗎？ |
| SLASH | 使用者用 `/名稱` 手動叫 | 否（手動叫多 = 路由沒接住的候選） |
| EXPLICIT / PINNED / INHERITED / DENIED / EXTERNAL | 派工有指定模型／沒指定但 agent 定義檔的 frontmatter 已釘住模型／沒指定而繼承主迴圈／被上限擋下／外部載體 | INHERITED 要判斷 |

**判斷一個群組，不是一筆事件。** 群組 = 同一個 skill + 同一個命中詞（或同一個搶走的 skill、
同一種 agent）。判一次，之後同模式的新事件自動沿用，所以待判斷的量會收斂。單筆判斷優先於
群組判斷，用來標例外。

判斷詞彙：`correct`、`should-fire`（該觸發卻沒有）、`correct-silence`（沒觸發是對的）、
`dict-gap`（字典的詞有問題或缺詞）、`description-gap`（description 該改）、`wrong-skill`、
`abstain`（不確定，先停放；借自 Jev 式快速判斷模型的「第三種結果」）。模型路由：`fit`、
`over-provisioned`、`under-provisioned`、`abstain`。

**判斷不會自動改規格。** `dict-gap` / `description-gap` 累積起來，就是下一輪 dict-review
的待辦清單；改字典、改 description 仍然由使用者裁定。

## 4. 資料放在哪

| 檔案 | 內容 | 版控 |
|---|---|---|
| `~/.claude/cache/routing-loop/events.jsonl` | 推導出的事件，隨時可整檔重建 | 否 |
| `~/.claude/cache/routing-loop/last-run.json` | 最近一次執行紀錄 | 否 |
| `~/.claude/telemetry/routing-loop-runs.jsonl` | 每次執行一行（趨勢） | 否 |
| `tools/routing-loop/labels.jsonl` | **判斷**（只追加，是唯一不可重建的資料） | 是 |

任何持久檔都不存提示原文，只存指標（session、record uuid、命中詞）；摘錄是 `queue`
顯示時才從逐字稿讀。

## 5. 講給別人聽（講稿）

> 路由我不靠直覺調。我把它當成一個會出錯的預測器：字典跟 description 是規格；改動前用一組
> 固定句子預測路由結果，改動後拿真實對話紀錄驗證。每一筆沒接住的觸發都會被歸到一個「模式」，
> 判斷是字典缺詞、描述不清，還是本來就不該觸發；判斷會累積下來，下次同樣的模式就不用再判。
> 定期整理判斷去修規格，字典有上限，避免越補越胖。模型選擇也是同一個迴圈，只是約束換成
> 「subagent 最高用到哪一級」的上限 hook。

可以抽出去用的是**形狀**，不是這些檔案：「判斷節點 → 規格 / 預測 / 觀測 / 分類 / 判斷 /
約束」六格，加上三條紀律——推導資料可重建而判斷只追加、每個數字都附尺規、判斷以模式為單位。

## 6. 已知限制

- **UNPREDICTED 佔比高（首跑 85%，修正 audit 後 87%）是現況，不是本工具的錯**：字典只解釋了
  少數自動觸發，跟 rule-registry 既有的結論一致；描述 (description) 才是路由器真正讀的規格。
- **兩個常駐 warn 已暫緩（使用者裁定 2026-09-26）**，登記在回授池 (feedback pool) 的
  `tool:routing-loop` 暫緩列，觸發條件寫在那裡，session 開頭的 HMI 摘要會帶出回授池狀態：
  `model-inherited`（09-05 規則前的 11 筆，約 10-02 自然退出 30 天窗；10-03 後仍 warn 或出現
  09-05 之後的繼承就重看）、`skill-unpredicted`（要等使用者定覆蓋率目標；下一輪 dict-review、
  或 HMI-R1 裁 H-4 時重看）。查詢：`python -X utf8 tools/feedback-pool/feedback.py review tool:routing-loop`
- **已修（2026-09-26）**：audit 的人類發言過濾原本把系統注入的 `<task-notification>`（721 筆）、
  夾在真人發言前的 `<system-reminder>`、中斷標記都算成使用者輸入；修正後 comsol `gate` 的
  MISS 由 164 降到 38，剩下的是使用者自己打的字（字典用詞問題，屬判斷範圍）。
- 模型路由的 codex / extdispatch 偵測是字串比對（尺規記為 `heuristic-v2`：v1 把 frontmatter 釘住的自訂 agent 誤判為 INHERITED，也漏認舊版拒絕字樣；2026-09-26 修正後，09-05 上限規則之後的真實繼承為 0）。
- 測試證據等級：rung 0（範例情境），每個狀態點都有正反兩向對照；`tests/test_loop.py`。
- HMI 的綁點與架構圖檢視在下一輪（交接卡：`references/routing-loop-hmi-handoff.md`）。
