---
name: project-retrospective
description: >-
  At project END (or a major milestone), scan the conversation history to extract
  lessons, pitfalls, decisions, and user preferences, then synthesize an
  experience-guide document plus a ready-to-paste CLAUDE.md snippet. Trigger on
  "summarize this project", "retrospective", "踩了什麼坑", "幫我寫 CLAUDE.md 規則", "wrap up what
  we learned". If a project merely seems to be wrapping up, ask once — never scan
  unprompted. User will CONTINUE after a phase → workflow-checkpoint. Full
  disambiguation: ~/.claude/skill-trigger-dict.md.
---

# Project Retrospective Skill

Extract reusable knowledge from conversation history. Output a human-readable experience guide and a Claude-readable CLAUDE.md instruction snippet.

---

## Overall Flow

```
1. Scan conversation → 2. Classify & extract → 3. Confirm with user → 4. Output documents
→ 5. Write project CLAUDE.md → ask before merging generalizable rules into global → log
```

Before starting, read `references/extraction-taxonomy.md` for the full classification system.

---

## Step 1: Scan the Conversation (and the durable records)

Besides the conversation itself, also pull two cheap durable sources when they
exist — they capture what earlier sessions hit but this conversation may not
mention:
- `~/.claude/ops/lessons.md`: grep for the project name/keywords; any matching
  pitfall cards are retrospective input (and mark them folded-in afterward per
  `ops/40-maintenance.md` §2).
- Git history: if the project (and/or `~/.claude`) is a git repo,
  `git log --oneline --since=<project start>` — commit subjects are a timeline
  of decisions and fixes worth cross-checking against the conversation.

Review the entire conversation and flag the following signals:

**High-value signals (always extract)**
- User says "no", "redo", "that's not what I meant" → log the root cause of the misunderstanding
- User says "use this", "this is better", "let's go with X" → log the decision outcome
- Claude went in the wrong direction and was corrected → log the correct path
- A term or concept appears repeatedly → log the definition
- A direction was explicitly abandoned with a reason → log the rejected option

**Medium-value signals (extract when present)**
- User adds "oh, and one more thing..." → often signals a key constraint
- A tool or API error appeared and was resolved → log the pitfall and workaround
- User expressed a preference about format, tone, or pacing

**Low-value signals (skip or summarize briefly)**
- Pure small talk or off-topic exchanges
- Standard procedures already documented elsewhere

---

## Step 2: Classify & Extract

Map each flagged item to one of the six categories in `references/extraction-taxonomy.md`:

1. **Technical Decisions** — what was chosen, why, and what was rejected
2. **Pitfalls & Bugs** — traps, wrong assumptions, version/environment issues
3. **Effective Workflows** — what prompt patterns worked, how tasks were best broken down
4. **Project Constraints & Context** — hard limits, project-specific term definitions
5. **User Preferences** — format, tone, confirmation rhythm
6. **Reusable Principles** — generalizable rules that apply beyond this project

---

## Step 3: Confirm with User

After drafting, ask the user **once** — consolidate everything into a single check-in, not multiple separate questions:

```
"Here's what I extracted. Please check if anything is missing or incorrect:

[bullet summary of extracted items]

A few quick questions:
- Any decision that felt significant but wasn't explained clearly in the conversation?
- Any pitfall you think is very easy to fall into again next time?
- Should the output be written for your future self only, or also for other people (e.g. future Claude instances)?"
```

Incorporate the answers, then move to output.

---

## Step 4: Output Documents

Produce two documents using templates from `references/output-templates.md`:

### Document 1: `retrospective-[project-name]-[date].md`
Human-readable experience guide — full version with context and explanations. Written in the user's preferred language (default: Traditional Chinese).

### Document 2: `claude-instructions-[project-name].md`
Compact CLAUDE.md-ready instruction snippet. **MANDATORY format (do not deviate):**
- **Conditional triggers only** — every rule MUST be phrased "When X, do Y" / "Do not ... because ...", firing only when its situation is hit. NO blanket always-on behavioral rules. (Read-only definitions/term glossaries are exempt — they state facts, not behaviors.)
- **Precise and concise** — name concrete files/APIs/symbols; cut anything a future Claude can't immediately act on.
- Tag each rule's source with `[from: category]`.

---

## Step 5: Merge into CLAUDE.md + log the change (MANDATORY)

After producing Document 2, do ALL of the following in order (do not skip — this is the deliverable, not optional):

1. **Write the project `CLAUDE.md` first.** Merge Document 2's rules into the project root `CLAUDE.md` (create it if absent; preserve existing content — append/merge, never overwrite; keep conditional-trigger phrasing intact). This holds ALL rules, including project-specific ones (file names, endpoints, this project's terms). Tell the user the exact path.

2. **Then check for generalizable rules and CONFIRM WITH THE USER before touching global.** Re-read the project CLAUDE.md you just wrote and split the rules:
   - **Project-specific** (names a file/endpoint/symbol/term that only exists here) → stays in the project CLAUDE.md only.
   - **Generalizable** (would still be useful in a completely different project — passes the Category-6 test) → candidate for global `~/.claude/CLAUDE.md`.
   Present the generalizable candidates to the user and **ask whether to merge them into global CLAUDE.md** — do NOT write global unilaterally. Putting project-specific rules in global pollutes every future project, so this gate is mandatory.
   - If the user says yes: merge ONLY the generalizable rules into `~/.claude/CLAUDE.md`, matching its existing conditional-section style (append/merge, never overwrite). If no: leave global untouched.

3. **Append an entry to the `Global_skill_update` changelog** at `~/.claude/Global_skill_update.md` (create it if absent, with an `# Global Skill Update Log` heading). Log BOTH the project-CLAUDE.md write and (if it happened) the global merge — separate entries are fine. Each entry:
   ```
   ## [YYYY-MM-DD HH:MM] <project-name> — <project CLAUDE.md | global CLAUDE.md>
   - Target CLAUDE.md: <absolute path written/merged>
   - Added/changed: <one-line description of the new rules>
   - Outputs: <paths to Document 1 / Document 2>   (first entry only)
   ```
   Always convert relative dates to an absolute timestamp. Append, never overwrite.

---

## Output Principles

- **Specific over abstract**: Write "don't use `fs.readFileSync` on large files — it causes OOM, use streams instead" not "be careful with memory"
- **Conditional, not blanket**: A rule that fires every turn is noise. Gate each one on a trigger situation so it stays silent when irrelevant.
- **Rules with context**: Each rule should carry a brief "why" so future Claude can judge if it applies
- **Layered**: Distinguish "this project only" rules from "universally applicable" principles
- **Actionable**: Every rule should pass the test — "can I immediately decide whether to follow this right now?"

---

## Notes

- For long conversations, do a keyword scan first (errors, decisions, preferences) before reading fully
- Don't stuff in everything — only extract turning points, corrections, and explicit choices
- If the project has no clear name, ask the user or default to "this-project"
- CLAUDE.md snippet rules must be conditional-triggered ("When X, do Y" / "Do not..., because...") — never blanket always-on behaviors. Read-only term/definition entries are the only exception.
- Step 5 is not optional: write the project CLAUDE.md, then ASK before merging any generalizable rule into global `~/.claude/CLAUDE.md` (never write global unilaterally), then append to `~/.claude/Global_skill_update.md`.
