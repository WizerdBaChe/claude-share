---
name: workflow-checkpoint
description: >-
  Phase-archiving and context-reconstruction for long-running multi-phase /
  multi-session projects. Trigger when (a) a phase/milestone completes and the user will
  CONTINUE — ask whether to checkpoint, append a scannable section to
  references/<project>-phase-log.md (never overwrite), then offer /compact; or (b) a new
  session opens with "continue / recap project X" — read only the phase-log to rebuild
  state at minimum token cost. Always seek consent before writing or compacting. Project
  ENDING with lessons extraction → project-retrospective. Full disambiguation:
  ~/.claude/skill-trigger-dict.md.
---

# Workflow Checkpoint

Leaves high-quality but concise checkpoints at phase boundaries for long-running projects,
so that a future session only needs to read one small file to reconstruct context —
avoiding the need to replay full conversation history and saving usage.

## When to Trigger

**Proactively ask** whether to do a phase checkpoint in any of these situations:
- A Phase / milestone has clearly completed and the user is ready to move on.
- Work mode shifts: **from idea/discussion into implementation**, or **a key document asset is delivered** (RPD, spec, architecture, finalized design).
- A large task has just passed validation / been delivered (e.g., build all-green, feature accepted).
- The user explicitly says "checkpoint / 存檔 / 做個階段總結".

**New-session reconstruction:**
- When the user says "**繼續這個專案 / recap / 接續上次**" → enter §C reconstruction flow.

**Do not trigger:**
- Minor edits, single-file changes, pure Q&A, or mid-phase work still in progress.
- Never write files or execute /compact without explicit consent.

## Project Name Resolution (`project_name`)

- Prefer the project's existing short code (e.g., `DIT`); otherwise use a concise slug from the working directory name.
- Always use the **same** `project_name` across sessions so that `references/<project>-phase-log.md` remains consistent and appendable.

---

## A. Phase Checkpoint Flow

1. **Ask first**: "要不要為此階段做一次 checkpoint？" — explain that the result will be written to `references/<project>-phase-log.md`.
2. Upon consent, **draft** a high-quality but concise phase summary (do not compact yet).
3. Write to `references/<project>-phase-log.md`:
   - Create `references/` and the file if they do not exist; **always append a new section — never overwrite existing content**.
   - **Write the entire phase log section in English** — this file is read by AI in future sessions, and English maximises token efficiency and parsing reliability.
   - Sections should be **concise and scannable, like index entries**: one sentence per point, focused on keywords and highlights for rapid navigation.
   - **Two-layer principle**: keep the log concise; if this phase has longer details worth preserving (full decision rationale, extended design notes, post-mortems), write them to a separate file `references/<project>-phase<N>-<slug>.md` and add a `- Detail: references/...` line in the log section header. The log itself stays summary-only. Detail files must also be written in English.
4. After writing, **report** which file and which Phase section was written.
5. Then proceed to §B (ask whether to /compact).

### Phase-Log Section Format (follow this order and headings strictly; write all content in English)

```
# Phase Checkpoint
- Project: <project name>
- Phase: <phase number and name, e.g. Phase 2 – UI Layout>
- Status: in-progress / completed
- Date: <timestamp>
- Detail: <references/...-detail.md — omit this line if no detail file>

## Goals
- Bulleted list of goals for this phase

## Decisions
- Key design and technical decisions, including rejected alternatives and rationale

## Changes
- <file path>: <summary of what was changed>
- …

## Open Questions / TODO
- Unresolved issues and next actions
```

- Multiple checkpoints = multiple `# Phase Checkpoint` sections in the same file, appended chronologically.
- `Date` uses the current date (with time if needed); relative dates (e.g., "today") must be converted to absolute dates.

---

## B. /compact Flow (after writing the checkpoint)

1. **Ask first**: "要不要現在對這段對話做 /compact？"
2. Upon consent (note: `/compact` is a user command — the model cannot execute it directly):
   - Remind the user (in Chinese): "phase-log 已記錄耐久上下文，這段對話可以放心有損壓縮。"
   - Provide a suggested compact note in **English** for the user to run as `/compact <key points>`. Prioritize preserving:
     - Project name and the structure / completion status of Phase 1 through Phase N
     - Key decision summaries from the most recent phase(s)
     - Modified files and their rough purpose
     - Critical rules that will definitely be needed to continue the project (design principles, important constraints)
     - A reminder line that global language rules stay in force after compaction (replies in Traditional Chinese; machine-read output in English)
   - Safe to drop: debug details, outdated option exploration, step-by-step trial-and-error history.

---

## C. New-Session Reconstruction Flow (user says "continue this project")

1. **Minimum tokens first**: read only `references/<project>-phase-log.md` (do not replay history; do not read the entire repo first).
2. Reconstruct understanding from the phase-log: project goals, Phase progress and status, most recent key decisions, unresolved TODOs.
3. Only load a detail file (`- Detail:` link) when deep-diving into a specific phase is necessary.
4. Summarize the current state in one sentence, then **ask the user** which Phase / TODO to start from.

---

## Design Principles
- Always **seek consent** before writing files or compacting.
- The phase-log is an **index / entry** — details live in separate files. Keep them separate to balance searchability and low read cost.
- The goal is always: **let the next session take over by reading just one small file**.