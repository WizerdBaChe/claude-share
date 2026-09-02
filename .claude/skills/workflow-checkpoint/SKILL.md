---
name: workflow-checkpoint
description: >-
  Phase archiving + context reconstruction. Fires inside ONE long session, not
  only across sessions. (a) A phase boundary passes and work goes on later —
  proactively ASK whether to checkpoint. Boundaries are usually SPOKEN, not
  committed: 「先到這邊」「本輪的終止」「收尾」「我會再新開 session/對話」
  「先設計（留文件）再動手」, UAT/驗收 passing, a key document delivered
  (spec/design/施工卡), or work shifting from discussion into implementation
  — that last shift IS a boundary. (b) A session opens with
  「繼續這個專案 / recap / 接續上次」 — rebuild from the phase-log alone. Do NOT
  fire on minor edits, single-file changes, pure Q&A, or mid-phase work. Work
  continues → here; project ENDS with lessons extraction →
  project-retrospective. Disambiguation: ~/.claude/skill-trigger-dict.md.
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

1. **Ask ONCE, carrying all three decisions** (one interruption, not three):
   "要不要為此階段做一次 checkpoint？順帶回答：本階段有沒有新術語該進詞彙表？
   寫完之後要不要 /compact？" — explain that the result will be written to the
   project's phase-log. Steps 5 and §B then act on this answer instead of
   asking again.
2. Upon consent, **draft** a high-quality but concise phase summary (do not compact yet).
3. **Resolve the record home FIRST** — and note whether it is git-tracked, which
   decides step 6b's branch — then write to `<home>/<project>-phase-log.md`:
   - If the project already keeps records somewhere (an existing
     `<project>-phase-log.md` in `~/.claude/references/` OR
     `<project-root>/references/`), that existing home WINS — never start a
     second home.
   - Otherwise default to `~/.claude/references/` (user-level: it survives repo
     moves and is where sibling skills look first).
   - State the chosen home in the PROJECTS.md row's entry chain so readers
     never have to guess.
   - Create the directory and the file if they do not exist; **always append a new section — never overwrite existing content**.
   - **Write the entire phase log section in English** — this file is read by AI in future sessions, and English maximises token efficiency and parsing reliability.
   - Sections should be **concise and scannable, like index entries**: one sentence per point, focused on keywords and highlights for rapid navigation.
   - **Two-layer principle**: keep the log concise; if this phase has longer details worth preserving (full decision rationale, extended design notes, post-mortems), write them to a separate file `references/<project>-phase<N>-<slug>.md` and add a `- Detail: references/...` line in the log section header. The log itself stays summary-only. Detail files must also be written in English.
4. **Self-check the appended section** before reporting: all four headings present
   (Goals / Decisions / Changes / Open Questions), Date is absolute, `- Detail:` link
   resolves if present. Fix in place if not — a checkpoint written near context
   exhaustion is exactly when sections silently go missing.
5. **Glossary sweep**: per the step-1 answer (ask again only if step 1 did not
   cover it), update `references/<project>-context.md` with any crystallized or
   changed terms (format and rules: `~/.claude/ops/60-bootstrap.md` §E — create
   lazily, update live, one definition per term). Skip silently if the project
   has no glossary and no new terms.
5b. **Journal sweep**: likewise check whether this phase produced unrecorded
   decisions (rejected options + why) or process problems (≥2-round walls, dead
   ends); if yes, append D-/P- entries and refresh the `## Now` block (frontier /
   premises / open) in `references/<project>-decisions.md` (format and
   write-triggers: `~/.claude/ops/60-bootstrap.md` §G — create lazily). Skip
   silently if nothing qualifies. A journal entry written here is a checkpoint
   artifact: step 6b persists it with the phase-log — an uncommitted, unhanded
   D-/P- entry is the same defect as an uncommitted section.
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
   next). **Re-read the file immediately before editing** — in a multi-session
   environment the row may have changed since you last saw it; edit against the
   fresh copy, never a cached one. Create the file from its header template if
   missing; add the row if the project is not yet registered. Column semantics
   live in the file's header comment.
   Then run `python ~/.claude/tools/project-dashboard.py` to regenerate the derived
   views; if Python is unavailable, say so and continue — the checkpoint never
   blocks on the dashboard. The row is a checkpoint artifact: step 6b persists
   it with the phase-log; the dashboard's derived views are regenerable and are
   NOT staged unless the repo already tracks them.
6b. **Persist** — the step that turns the section into a checkpoint. Property of
   the asset: **a phase-log section (and the glossary / journal / PROJECTS.md
   row this checkpoint edited) that is uncommitted AND unhanded is incomplete**;
   the deliverable is the record in git or in a named hand-off, never the file
   in the working tree. Measured 2026-08-21: 17 complete, correct record
   artifacts from 5 projects — 5 of them phase logs — sat uncommitted in
   `~/.claude` for up to 109 h because every writer stopped at "the file is
   written". Route by tracking state, then by coupling class:
   - **Record home not git-tracked**: say so in step 7's report; nothing else.
   - **Git-tracked, and the tree is yours or the coupling class allows it**
     (additive record work on a disjoint domain — `ops/references/shared-tree-git.md`
     §1): commit NOW, in this step, not at session end, by the ritual of the
     same file §2 carried here by reference — `git branch --show-current` →
     stage the EXPLICIT paths this checkpoint touched (never `-A`; never a
     peer's dirty path without their provenance in the message, §4) →
     `git commit -F <msgfile>` (`docs(<project>): checkpoint Phase <N> — <slug>`)
     → `git show --stat HEAD`, read for what you did NOT write.
   - **Git-tracked, tree shared, and the coupling class says SERIALIZE**
     (same workstream in two sessions, or a peer's in-flight work in a path you
     would stage): do NOT commit — **hand off explicitly**: name the dirty paths
     and the session/baton that owns the commit (identified by what it touches,
     never by cwd), and message that session if a hailing tool is available
     (§1 names the current one). The hand-off line is the deliverable here.
   L-023 routing is the caveat, not an exception: committing mid-session in a
   shared tree caused every L-023 incident, so this step NEVER reads "always
   commit" — it reads "commit or hand off, routed, and name which".
7. After writing, **report** which file and which Phase section was written AND
   how it was persisted: the commit sha from 6b's `git show --stat HEAD`, or the
   hand-off line (paths + owning session/baton), or "home not tracked". A
   report that names the file but none of the three is reporting an incomplete
   checkpoint.
8. Then proceed to §B (ask whether to /compact).

### Phase-Log Section Format (follow this order and headings strictly; write all content in English)

```
# Phase Checkpoint
- Project: <project name>
- Phase: <phase number and name, e.g. Phase 2 – UI Layout>
- Status: in-progress / completed
- Date: <timestamp>
- Detail: <references/...-detail.md — omit this line if no detail file>
- Transcript: <session-id>.jsonl — archived: yes/no  (the raw-history pointer;
  compaction chains continuations into NEW files, and cleanupPeriodDays
  — default 30 days — deletes them, so this line is what lets anyone find the
  history before it ages out)

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
- **Series hand-off naming duty (`ops/lessons.md` L-039)**: if `Open Questions / TODO` hands the next round a deliverable in a series (deck v2, report round N, audience-fit edition), that line NAMES the mandatory inputs — the predecessor deliverables AND their review/acceptance records, by path. A hand-off line that names only the plan ("assemble from X + Y") is how the next round opens blind: the summary becomes the sole material authority and the prior-art gate never arms.

---

## B. /compact Flow (after writing the checkpoint)

1. **Ask first**: "要不要現在對這段對話做 /compact？"
2. Upon consent (note: `/compact` is a user command — the model cannot execute it directly):
   - Remind the user (in Chinese): "phase-log 已記錄耐久上下文，這段對話可以放心有損壓縮。"
   - Provide a suggested compact note in **English** for the user to run as `/compact <key points>`.
     **Derive the note's contents from THIS session's own shape** — what kind of
     work it held (design round, implementation, audit, a deliverable series),
     and what the continuation will reach for first — never by transcribing the
     list below verbatim. The list is the FLOOR every project continuation
     needs preserved, not the note's outline; add the session-specific items
     the list cannot know, and skip a floor item only with the reason stated:
     - Project name and the structure / completion status of Phase 1 through Phase N
     - Key decision summaries from the most recent phase(s)
     - Modified files and their rough purpose
     - Critical rules that will definitely be needed to continue the project (design principles, important constraints)
     - For any in-flight deliverable series: the consulted prior-art list BY NAME (deliverables 1..N-1 + their review records) — a prior-art verdict survives compaction only as a named list, never as "already done" (`ops/lessons.md` L-039)
     - A reminder line that global language rules stay in force after compaction (replies in Traditional Chinese; machine-read output in English)
   - Safe to drop: debug details, outdated option exploration, step-by-step trial-and-error history.
3. **Transcript fate (state it, don't assume it)**: compaction deletes nothing —
   the continuation opens a NEW `.jsonl` chained to the old one — but
   `cleanupPeriodDays` (default 30) WILL delete both halves eventually. On
   the source machine a daily mirror task copies transcripts to an archive
   directory outside the retention window (ruling D-033); with one, check
   its own last-run status shows a recent OK, then set
   `archived: yes` and move on. If the mirror is absent or stale, offer to
   copy the session's `.jsonl` (and its `<id>/subagents/` folder, if present)
   to the archive folder manually. NEVER parse the jsonl internals — the
   format is documented as unstable; copy whole files only.

---

## C. New-Session Reconstruction Flow (user says "continue this project")

1. **Minimum tokens first**: read only `references/<project>-phase-log.md`, plus `references/<project>-context.md` if it exists (domain glossary — small, prevents vocabulary drift across sessions), plus the `## Now` block of `references/<project>-decisions.md` if it exists. Do not replay history; do not read the entire repo first.
   - **Premise re-confirmation (mandatory for continuing tasks)**: before acting, re-confirm the `## Now` premises — re-verify P-env facts (they rot), and re-state P-intent / P-validity premises to the user in one short block. Origin-(user) premises are never auto-overturned: if evidence now contradicts one, ask with the evidence attached (`~/.claude/ops/30-judgment.md` R2 overturn hierarchy).
   - **Series-continuation inputs (`ops/lessons.md` L-039)**: if the resumed work produces deliverable N of a series (deck v2, report round N, audience-fit edition), the predecessor deliverables + their review records named in the phase-log hand-off line are READ INPUTS before any design work — deferred past this step: NOT part of the minimum read; do it after the user picks the Phase/TODO (step 4), before designing. The phase-log is a pointer to them, never their substitute, and its summary never counts as the prior-art check already run for the new round. Hand-off line missing the names (pre-L-039 checkpoint)? Locate them now (project 交付/ folder, decisions journal) rather than proceeding on the summary alone.
   - **Map fingerprint check (read-time, do it HERE not at checkpoint)**: if `references/<project>-map.md` exists, verify it BEFORE reading it — `git merge-base --is-ancestor <generated-from> HEAD`, then `git diff --name-only <generated-from>..HEAD` scoped to its `covers` globs. FRESH replaces a repo scan entirely; DRIFT means patch from the diff; STALE means regenerate. Reading first and verifying after spends exactly the tokens the check exists to save. The verdict is a P-env premise — report it in the block above. Algorithm and write classes: `~/.claude/ops/references/project-map.md` §6/§9.
   - **Fallback — phase-log missing or clearly stale** (session died before a
     checkpoint was written): tell the user reconstruction will cost more than a
     normal recap, and upon consent rebuild from persisted session transcripts
     (session-management search tools if available; the transcript-archive
     folder and the DIT viewer are also reconstruction sources — a compacted
     session's older files chain via `logicalParentUuid`, but hand whole files
     to tools, never parse the jsonl internals yourself; otherwise recently
     modified files + `git log`). Afterwards, offer to write a catch-up
     checkpoint section so the next session doesn't pay this cost again.
2. Reconstruct understanding from the phase-log: project goals, Phase progress and status, most recent key decisions, unresolved TODOs.
3. Only load a detail file (`- Detail:` link) when deep-diving into a specific phase is necessary.
4. Summarize the current state in one sentence, then **ask the user** which Phase / TODO to start from.

---

## Design Principles
- Always **seek consent** before writing files or compacting.
- The phase-log is an **index / entry** — details live in separate files. Keep them separate to balance searchability and low read cost.
- A checkpoint lives in **git or in a named hand-off**, never only in a working tree — the file is the carrier, the commit (or the baton) is the deliverable (§A 6b).
- The goal is always: **let the next session take over by reading just one small file**.