# Output Templates

---

## Document 1: Full Experience Guide  
Filename: `retrospective-[project-name]-[date].md`

This document is for the **human's future self**. Prioritize readability and context.  
Write in the user's preferred language (default: Traditional Chinese).

```markdown
# [專案名稱] 經驗守則
**整理日期**：[日期]  
**專案期間**：[開始] → [結束/當前階段]  
**核心目標**：[這個專案在做什麼，一句話]  
**涵蓋範圍 (coverage)**：[涵蓋哪幾個 Phase；來源為 phase-log / decisions journal /
對話視窗 / git 中的哪些；哪一段不可考——例如「Phase 2 的逐步除錯過程已隨 compact
遺失」。讀者必須能看出這份回顧「不知道什麼」。]  
**本回顧改動了什麼 (what this retrospective changed)**：[Step 3 修訂的紀錄檔、
Step 2.5 修掉的缺陷、產生的 commit。回顧不是唯讀產物——讀者必須能區分哪些狀態
是回顧「觀察到」的、哪些是回顧「造成」的。]

---

## TL;DR（最重要的三件事）

> 如果只能記住三件事：
> 1. [最重要的教訓]
> 2. [最大的坑]
> 3. [最有效的做法]

---

## 技術決策紀錄

[填入 Category 1 的提取結果]

---

## 踩雷紀錄

[填入 Category 2 的提取結果]

---

## 有效工作模式

[填入 Category 3 的提取結果]

---

## 專案約束與術語

[填入 Category 4 的提取結果]

---

## 使用者偏好紀錄

[填入 Category 5 的提取結果]

---

## 可複用守則（帶進下個專案）

[填入 Category 6 的提取結果]

---

## 乾淨路徑（下次同類專案的施工順序）

<!-- 只在專案屬於可重複的類型時填寫（Category 7）；一次性專案明說「無可泛化的
乾淨路徑」，不要硬編。 -->

[填入 Category 7 的提取結果：施工順序（每步帶 gate）+ 選型表]

---

## 全案反問（5W1H 深入回顧）

<!-- SKILL.md Step 2 的 5W1H 反問結果：對「全案／整段對話」而非單一項目發問。
問題是依「這個專案的模型」逐軸推導出來的，不是抄固定清單——每軸先寫出實際
問的專案特定問題，再寫答案，讓讀者能同時檢驗問題與答案。某軸對此專案確實
無意義 → 一行明說並附理由，取代該軸，不得硬填泛用答案。答不出來的問題本身
就是發現——同時列進涵蓋範圍或未解決的問題，不得靜默跳過。 -->

- **Why**：〔本專案的問法：…〕→ [答案]
- **What**：〔本專案的問法：…〕→ [答案]
- **Who**：〔本專案的問法：…〕→ [答案]
- **When**：〔本專案的問法：…〕→ [答案]
- **Where**：〔本專案的問法：…〕→ [答案]
- **How**：〔本專案的問法：…〕→ [答案]

---

## 未解決的問題

> 經過對帳（SKILL.md Step 3）後仍然開放的——這次沒解決、下次還要面對的：

- [ ] [問題一]
- [ ] [問題二]

### 已關閉（本輪收尾時關掉的）

<!-- 曾列為開放、在專案最後階段被關閉的項目，附上是什麼關閉了它。
若來源紀錄（phase-log / decisions journal）沒跟上，修的是來源紀錄，不是只改這裡。 -->

- [x] [項目] — 關閉依據：[什麼事把它關掉的]

---

## 下次想嘗試的做法

- [想法一]
- [想法二]
```

---

## Document 2: CLAUDE.md Instruction Snippet  
Filename: `claude-instructions-[project-name].md`

This document is for **future Claude instances**. Write in English — compact, imperative, no explanations.

**Format rules:**
- Use second-person imperative: "You should...", "When X, do Y", "Do not..., because..."
- No background context needed — rules must stand alone
- Each rule must be independently actionable
- Tag the source of each rule with `[from: category name]` so future readers know where it came from
- **Size discipline**: this file is loaded into every future session of the
  project. Cap at ~25 rules; order by expected trigger frequency (most likely to
  fire first); if over the cap, cut from the bottom — the cut material is not
  lost, it stays in Document 1
- **Destination tag** on every rule: `[dest: project]` (the repo's rules layer,
  or its CLAUDE.md if it has none) / `[dest: global]` (Step 6.2 candidate) /
  `[dest: lessons]` (sharp but rarely triggered → `ops/lessons.md` L-nnn).
  Order by trigger frequency, not by destination
- **Supersession header**: if this project has any earlier Document 1/2 under a
  different name, open with `# Supersedes <old file>` and name the rules this
  round rewrote (not merely added) — SKILL.md Step 5

```markdown
# Claude Instructions — [Project Name]
# Extracted from project retrospective on [date]
# Ready to paste into CLAUDE.md or a skill preamble

---

## Technical Rules

<!-- From Categories 1 & 2 -->

- [Specific actionable rule] `[from: technical decisions]`
- [Specific actionable rule] `[from: pitfalls]`

---

## Workflow Rules

<!-- From Category 3 -->

- [Specific actionable rule] `[from: effective workflows]`

---

## Project-Specific Definitions

<!-- From Category 4 -->

- **[Term]** means: [definition in this project's context]
- The following constraints are fixed and must not be changed: [list]

---

## User Preferences

<!-- From Category 5 -->

- Output format: [preference]
- Tone: [preference]
- Confirmation rhythm: [preference]

---

## Reusable Principles (carry to other projects)

<!-- From Category 6 -->

- [Principle one]
- [Principle two]
```

---

## Pre-output Quality Checklist

This checklist covers content QUALITY (judgment calls). The mechanical
existence/integrity checks live in SKILL.md Step 6.4 and are a required flow
step, not advisory. Before finalizing output, verify:

- [ ] Every rule is specific, not vague ("when X occurs, do Y" beats "be careful with X")
- [ ] Every pitfall has a **prevention** — not just a description of what went wrong
- [ ] Every pitfall carries **cost / times hit / status** — an accepted workaround is not written as if solved (a defect fixed mid-retrospective is `Status: fixed during the retrospective`, per SKILL.md Step 2.5)
- [ ] Every Document 2 rule carries BOTH a `[from:]` and a `[dest:]` tag
- [ ] User preferences include an **anti-pattern** (knowing what they dislike is as valuable as knowing what they like)
- [ ] Reusable principles have an **applies-when** condition (to prevent over-generalization)
- [ ] Every rule in the CLAUDE.md snippet can be understood without reading the full retrospective
- [ ] Document 2 is within the size cap (~25 rules) and ordered by trigger frequency
- [ ] Document 1 has a TL;DR — readers who skim should still get the key takeaways
- [ ] Document 1's coverage header names its sources, what is unrecoverable, AND what the retrospective itself changed (observed vs caused)
- [ ] Unresolved problems are the RECONCILED list (Step 3) — closed items moved to 已關閉 with their closing evidence
- [ ] The 5W1H section covers all six axes about the WHOLE project — each axis shows the project-specific question it derived (not the generic seed verbatim) OR a one-line reasoned opt-out; an unanswerable question is recorded as a finding (coverage header or 未解決的問題), never silently dropped

---

## Moved verbatim from SKILL.md 2026-08-16 (BODY_CAP trim — content unchanged)

### Step 4 check-in template (SKILL.md Step 4 points here)

```
"Here's what I extracted. Please check if anything is missing or incorrect:

[bullet summary of extracted items]

- Any decision that felt significant but wasn't explained clearly in the conversation?
- Any pitfall you think is very easy to fall into again next time?

Global-rule candidates — FYI only, nothing is written to global CLAUDE.md in
this retrospective; they accumulate for a dedicated batch session (SKILL.md
Step 6.2):
| rule | recommendation (adopt / merge into X / reject) | why |

Accumulated backlog: N pending candidates across M files in the output
directory — 批次處理時另開一個 session 即可，由你決定何時值得處理。

[If README is stale or missing:] The project README is [stale/missing] — want me
to refresh it from the retrospective content?"
```

### Document 1 format (authoritative — SKILL.md Step 5 points here)

Human-readable experience guide — full version with context and explanations.
Written in the user's preferred language (default: Traditional Chinese).
**MUST open with a coverage header**: which phases it covers, which sources fed
it (phase-log / decisions journal / conversation window / git), which stretches
are unrecoverable (e.g. lost to compaction), AND **what this retrospective
CHANGED** — files amended in Step 3, defects fixed per Step 2.5, commits
produced. A retrospective is not a read-only artifact: a reader must be able to
tell both what it does NOT know and what it observed versus what it caused.

### Document 2 format (authoritative — SKILL.md Step 5 points here)

Compact CLAUDE.md-ready instruction snippet. **MANDATORY format (do not deviate):**
- **Conditional triggers only** — every rule MUST be phrased "When X, do Y" / "Do not ... because ...", firing only when its situation is hit. NO blanket always-on behavioral rules. (Read-only definitions/term glossaries are exempt — they state facts, not behaviors.)
- **Precise and concise** — name concrete files/APIs/symbols; cut anything a future Claude can't immediately act on.
- **Size discipline** — this file is loaded into every future session of the
  project. Cap at ~25 rules; order rules by expected trigger frequency; if over
  the cap, cut from the bottom (the cut material stays in Document 1).
- Tag each rule's source with `[from: category]`.
- **Tag each rule with a destination**, not only a source category:
  `[dest: project]` (this repo's rules layer — `ops/`, `rules/`, or the project
  CLAUDE.md if it has none), `[dest: global]` (a Step 6.2 candidate), or
  `[dest: lessons]` (sharp but rarely triggered — `~/.claude/ops/lessons.md`,
  written as an L-nnn per Step 6.5). Order the file by expected trigger
  frequency, not by destination. Two destinations is the special case where the
  project has no rules layer; do not assume it.

### Step 6.5 record-entry shape (SKILL.md Step 6.5 points here)

```
## [YYYY-MM-DD HH:MM] <project-name> — <project CLAUDE.md | global CLAUDE.md>
- Target CLAUDE.md: <absolute path written/merged>
- Added/changed: <one-line description of the new rules>
- Outputs: <paths to Document 1 / Document 2>   (first entry only)
```

### Output principles (SKILL.md "Output Principles" points here)

- **Specific over abstract**: Write "don't use `fs.readFileSync` on large files — it causes OOM, use streams instead" not "be careful with memory"
- **Conditional, not blanket**: A rule that fires every turn is noise. Gate each one on a trigger situation so it stays silent when irrelevant.
- **Rules with context**: Each rule should carry a brief "why" so future Claude can judge if it applies
- **Layered**: Distinguish "this project only" rules from "universally applicable" principles
- **Actionable**: Every rule should pass the test — "can I immediately decide whether to follow this right now?"
- **Honest about coverage**: the retrospective states what it cannot know (compacted stretches, missing records) instead of silently presenting a partial view as complete. A retrospective that lies is worse than none — it looks authoritative.
