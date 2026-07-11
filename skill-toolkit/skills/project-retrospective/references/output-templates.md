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

## 未解決的問題

> 這次沒解決、下次還要面對的：

- [ ] [問題一]
- [ ] [問題二]

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

Before finalizing output, verify:

- [ ] Every rule is specific, not vague ("when X occurs, do Y" beats "be careful with X")
- [ ] Every pitfall has a **prevention** — not just a description of what went wrong
- [ ] User preferences include an **anti-pattern** (knowing what they dislike is as valuable as knowing what they like)
- [ ] Reusable principles have an **applies-when** condition (to prevent over-generalization)
- [ ] Every rule in the CLAUDE.md snippet can be understood without reading the full retrospective
- [ ] Document 1 has a TL;DR — readers who skim should still get the key takeaways
- [ ] Unresolved problems are listed honestly — don't pretend everything was solved
