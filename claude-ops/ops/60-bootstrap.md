# Bootstrap & Ledger — first session in a project, and where progress lives

Two things every project needs before the command loop can run properly: verified
environment facts (step B) and a durable task ledger (step C). Without them,
`10-command-loop.md` steps 1 and 3 have nothing to read or write.

## A. First-session-in-a-project checklist (run once, ~10 minutes)

1. **Read what exists**: `~/.claude/references/PROJECTS.md` (global project index —
   register this project's row if missing), project `CLAUDE.md`,
   `references/<project>-phase-log.md` (if the `workflow-checkpoint` skill has been
   used), `references/<project>-tickets.md`, `references/<project>-context.md`
   (domain glossary, §E — if present), `references/<project>-decisions.md`
   (§G — if present, re-confirm its `## Now` premises before acting), and grep
   `~/.claude/ops/lessons.md` for the project name. Never assume a fresh start.
2. **No project CLAUDE.md?** Offer to run `/init`, then add the Environment-facts
   block (template below) with values you actually looked up this session.
3. **No ticket ledger?** Create `references/<project>-tickets.md` from the template
   in §C (ask first if the project has its own tracker — one ledger, not two).
4. **Verify, don't inherit**: any command, path, or tool name you plan to rely on —
   run it or `Test-Path` it once now. Record what you verified; write
   "couldn't determine" for what you couldn't.
5. **Relaxation level**: if the main-loop model is frontier-tier and the project
   CLAUDE.md has no `ops-relaxation:` line, ask the user to pick a level now —
   L0 strictest (no relaxation, default) / L1 core relaxed / L2 loosest
   (`05-authority.md` §2) and record the answer in the project CLAUDE.md —
   one ask per project, not per session.

✅ Read phase-log → phase 2 finished last week → resume from the open ticket.
❌ Start restructuring "helpfully"; hour two reveals a half-finished migration
ticket already covered it — two conflicting efforts.

## B. Environment-facts block (append to the PROJECT CLAUDE.md, dated, verified)

```markdown
## Environment facts (verified <YYYY-MM-DD>; re-verify before relying on)
- Build: <command> | Test: <command> | Run: <command>
- Model tiers available this environment: <looked up, or "couldn't determine">
- Dispatch mechanism: <e.g. Agent tool / Workflow tool — as actually available>
- Project-specific redlines: <files/dirs never to touch>
- Ticket ledger: references/<project>-tickets.md
```

Facts carry a date because they rot. A fact you didn't verify this environment is
a guess (`50-coach.md` C1).

## C. The durable ticket ledger (progress lives in files, not conversations)

Location: `references/<project>-tickets.md` — sibling of the phase-log so
`workflow-checkpoint` finds both. In-session task tools are session-scoped:
anything that must survive a restart gets mirrored here; the file is the
authority on resume.

Ticket stub (3 lines minimum — `10-command-loop.md` step 3):

```markdown
## T-NNN <one-line end state, not the action>
status: open|active|blocked|done  owner: <dispatcher|worker-id|human>  blocked-by: <T-NNN|->
type: build|investigation   (optional; default build)
acceptance: <machine-checkable command + expected output>
notes: <optional: decisions, reorders with reasons, partial results path>
```

Rules: update `status` BEFORE announcing "I'll do X next"; reorders are edited
into the ticket before acting and explained when reporting; `done` requires the
evidence demanded by `30-judgment.md` R2. Completed tickets move to an
`## Archive` section at the bottom — never deleted.

### Slicing a plan into tickets (tracer-bullet discipline)

When decomposing a plan/design doc into tickets (typically after a
product-design-thinking PSM is fixed), each `build` ticket is a **tracer
bullet**: a narrow but COMPLETE vertical slice through every affected layer
(schema → logic → surface → tests), demoable on its own, sized to one fresh
context window, written from the user's perspective — not a layer breakdown.
`blocked-by` edges only where genuine gating exists.

- **Exception — wide mechanical refactors**: don't force them into tracer
  bullets (breaks green-state between tickets). Use expand-contract instead:
  introduce the new form alongside the old → migrate call sites in batches →
  retire the old form when unused.
- **`investigation` tickets** resolve ONE decision, not a deliverable; the
  answer is recorded in the ticket's `notes`. One investigation per session.
- **Fog stays coarse**: questions not yet sharp enough to ticket go under an
  optional `## Not yet specified` section at the top of the ledger — promote
  to a ticket only when the frontier reaches them; never pre-slice fog.

✅ "T-012 user can export a report as PDF" (schema+API+button+test, demoable).
❌ "T-012 write the PDF service layer" + "T-013 wire up the UI" — horizontal
slices, neither verifiable alone.
✅ Crash resume: `grep "status: active" references/*-tickets.md` → pick up
exactly where the ledger says. ❌ Progress only in the session task list →
restart → gone; "where was I" costs an hour.

## D. Worker delivery index (the worker-side ledger — not a ticket edit)

A worker executing a dispatched ticket writes `DELIVERY.md` in its own output
directory and hands back the path (the dispatcher backfills the real ticket):

```markdown
# Delivery: <ticket/task id>
Did: <≤5 lines>
Verified: <commands run + key output lines>
Could not do: <honesty clause — what, why, evidence, proposed path forward>
Artifacts: <paths>
```

## E. Project domain glossary (`references/<project>-context.md`)

The project's shared language — where domain terms are defined ONCE so sessions
don't drift apart on vocabulary. Scope boundary: environment-level vocabulary
lives in `skill-trigger-dict.md` (skill routing) and `ops/rules-usage-dict.md`
(layer boundaries); THIS file is project-level domain terms only.

**Create lazily**: only when a domain-heavy multi-session project produces its
first term worth pinning — not a standard fixture for every project. Format:

```markdown
# <project> — Domain Glossary
<!-- One definition per term. Updated live, never batched. English only. -->
- **<Term>** (<YYYY-MM-DD>): <one-sentence definition>. [superseded: <old>]
```

Rules:
- **Update live**: record a term the moment it crystallizes — batching updates
  is how glossaries die.
- **Challenge, don't just consume**: requester usage contradicts an entry →
  surface it and update; a stale definition is worse than none.
- **Glossary only**: no specs, implementation notes, or scratch content.
- **ADR gate** (three ALL required, else no ADR): hard to reverse + surprising
  without context + a genuine trade-off existed. ADRs live in the project's
  own docs (`docs/adr/` or per convention), one line of gist here.

Maintenance mounts (who keeps it alive): `workflow-checkpoint` asks at each
phase checkpoint whether new terms crystallized; `product-design-thinking`
Phase 3 persists its PIM glossary here; §A step 1 reads it every first session.

## F. Work-card format (施工卡 — build-ready rendering of ONE change item)

A work card is a FORMAT, not a ledger: its content lives where the item
already lives (a PSM/remediation-doc item, or a ticket's body under `notes:`).
Never create a separate card file or registry beside the ticket ledger.

Fields: Severity/Confidence, Objects, Why, Change, Blast radius, Rollback,
Acceptance (machine-checkable first), Commit. **Full template + the
field-ownership map (language, severity scale, commit format, build-ready
bar): `ops/60-record-templates.md` §1 — read it before writing a card.**
Objects/Rollback/Acceptance render the sole-source build-ready bar; a
bar-compliant item missing only card-level fields is NOT a skeleton.

When to use: RECOMMENDED for items in sole-basis build docs (PSM, remediation
plan) and for deep-review remediation output (`code-review-deep-checklist`,
`security-deep-checklist`) when actionable fixes are requested. OPTIONAL for
ticket bodies (§C's 3-line stub stays the tracking minimum), dispatch work
orders, expand-contract batches, and postmortem action items.

✅ "SYNC-01 — SSE relay off the event loop": objects `routers/sync.py`; change
`await asyncio.to_thread(events.get)` + disconnect handling; acceptance
"`/api/health` responds during a slow-worker test".
❌ "Refactor renderer for cleanliness" — no acceptance, no rollback, no blast
radius: a wish, not a work card.

## G. Decision & Process Journal (`references/<project>-decisions.md`)

The know-why layer between ADR (heavy, three-gate — §E) and a ticket's
one-line `notes:`: decisions WITH their reasoning and rejected options, plus
process problems (dead ends, walls) below lessons.md's global-pitfall bar.
Per-project only — cross-project abstraction/export is `project-retrospective`'s
job, never this file's.

**Write-triggers** (ANY fires; create the file lazily at the first): a
serious candidate was rejected; a problem took ≥2 rounds to crack; the user
made a ruling; the plan deviated from its original course.

Format: append-only, NEWEST ENTRY FIRST, English body (Traditional Chinese
only in fields the user rules on). Sections: `## Now` (frontier / premises /
open — the resume anchor) + `## D-NNN` decisions (status / context / options /
choice+why / revisit-if / links) + `## P-NNN` problems (status / trail /
resolution / links). **Full template: `ops/60-record-templates.md` §2 — read
it before writing an entry.** Minimum fields are invariant-class (registry:
`ops/rules-usage-dict.md` §7); narrative style is free.

Rules:
- **`## Now` is the resume anchor**: every NEW SESSION on a continuing task
  re-reads it and re-confirms the premises BEFORE acting — P-env re-verified
  (facts rot), P-intent/P-validity re-stated to the user in one short block;
  origin-(user) premises follow the overturn hierarchy (`30-judgment.md` R2:
  ask with evidence, never auto-overturn). A session-start duty, not a
  per-turn one; `workflow-checkpoint`'s reconstruction flow mounts it.
- **Boundaries**: ADR-grade (three gates all pass, §E) → project `docs/adr/`,
  one gist line here; a pitfall that generalizes beyond the project →
  promote to `ops/lessons.md`, mark `promoted→L-NNN`; tickets carry D/P ids
  in `notes:`, never the content (one rule, one file).
- **Maintenance mounts**: `workflow-checkpoint` sweeps for unrecorded D/P
  entries at each checkpoint (same pattern as the §E glossary sweep);
  `10-command-loop.md` Step 8 checks once at close-out.

✅ "D-004 chose SQLite over Postgres: single-user desktop app; revisit-if:
multi-user sync becomes a goal."
❌ Ticket note "decided to use SQLite" with the why lost — three sessions
later the decision gets relitigated from zero.
