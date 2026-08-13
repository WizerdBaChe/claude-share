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
4. **Self-check the appended section** before reporting: all four headings present
   (Goals / Decisions / Changes / Open Questions), Date is absolute, `- Detail:` link
   resolves if present. Fix in place if not — a checkpoint written near context
   exhaustion is exactly when sections silently go missing.
5. **Glossary sweep**: ask whether any domain terms crystallized or changed meaning
   this phase; if yes, update `references/<project>-context.md` (format and rules:
   `~/.claude/ops/60-bootstrap.md` §E — create lazily, update live, one definition
   per term). Skip silently if the project has no glossary and no new terms.
5b. **Journal sweep**: likewise check whether this phase produced unrecorded
   decisions (rejected options + why) or process problems (≥2-round walls, dead
   ends); if yes, append D-/P- entries and refresh the `## Now` block (frontier /
   premises / open) in `references/<project>-decisions.md` (format and
   write-triggers: `~/.claude/ops/60-bootstrap.md` §G — create lazily). Skip
   silently if nothing qualifies.
5c. **Map sweep** (write-time half only — freshness is checked at session start,
   §C step 1, never here): if `references/<project>-map.md` exists, ask whether
   any `[infer]` in its `## Open [infer]` section got confirmed this phase — each
   confirmed one is PROMOTED into `-decisions.md`/`-context.md` and PRUNED from
   the map (a map that never shrinks means promotion is not happening). Also flag
   any regenerable fact (file lists, module structure, what connects to what) you
   just wrote into a write-time record — that belongs to the map, not there.
   Rules: `~/.claude/ops/60-bootstrap.md` §H; write classes:
   `ops/references/project-map.md` §9. Skip silently if no map exists.
6. **Index row update** (no extra consent needed — covered by the checkpoint consent):
   refresh this project's row in `references/PROJECTS.md` (status / last-checkpoint /
   next). Create the file from its header template if missing; add the row if the
   project is not yet registered. Column semantics live in the file's header comment.
   Then run `python ~/.claude/tools/project-dashboard.py` to regenerate the derived
   views; if Python is unavailable, say so and continue — the checkpoint never
   blocks on the dashboard.
7. After writing, **report** which file and which Phase section was written.
8. Then proceed to §B (ask whether to /compact).

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

1. **Minimum tokens first**: read only `references/<project>-phase-log.md`, plus `references/<project>-context.md` if it exists (domain glossary — small, prevents vocabulary drift across sessions), plus the `## Now` block of `references/<project>-decisions.md` if it exists. Do not replay history; do not read the entire repo first.
   - **Premise re-confirmation (mandatory for continuing tasks)**: before acting, re-confirm the `## Now` premises — re-verify P-env facts (they rot), and re-state P-intent / P-validity premises to the user in one short block. Origin-(user) premises are never auto-overturned: if evidence now contradicts one, ask with the evidence attached (`~/.claude/ops/30-judgment.md` R2 overturn hierarchy).
   - **Map fingerprint check (read-time, do it HERE not at checkpoint)**: if `references/<project>-map.md` exists, verify it BEFORE reading it — `git merge-base --is-ancestor <generated-from> HEAD`, then `git diff --name-only <generated-from>..HEAD` scoped to its `covers` globs. FRESH replaces a repo scan entirely; DRIFT means patch from the diff; STALE means regenerate. Reading first and verifying after spends exactly the tokens the check exists to save. The verdict is a P-env premise — report it in the block above. Algorithm and write classes: `~/.claude/ops/references/project-map.md` §6/§9.
   - **Fallback — phase-log missing or clearly stale** (session died before a
     checkpoint was written): tell the user reconstruction will cost more than a
     normal recap, and upon consent rebuild from persisted session transcripts
     (session-management search tools if available; otherwise recently modified
     files + `git log`). Afterwards, offer to write a catch-up checkpoint section
     so the next session doesn't pay this cost again.
2. Reconstruct understanding from the phase-log: project goals, Phase progress and status, most recent key decisions, unresolved TODOs.
3. Only load a detail file (`- Detail:` link) when deep-diving into a specific phase is necessary.
4. Summarize the current state in one sentence, then **ask the user** which Phase / TODO to start from.

---

## Design Principles
- Always **seek consent** before writing files or compacting.
- The phase-log is an **index / entry** — details live in separate files. Keep them separate to balance searchability and low read cost.
- The goal is always: **let the next session take over by reading just one small file**.