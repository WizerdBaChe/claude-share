# Bootstrap & Ledger — first session in a project, and where progress lives

Two things every project needs before the command loop can run properly: verified
environment facts (step B) and a durable task ledger (step C). Without them,
`10-command-loop.md` steps 1 and 3 have nothing to read or write.

## A. First-session-in-a-project checklist (run once, ~10 minutes)

1. **Read what exists**: project `CLAUDE.md`, `references/<project>-phase-log.md`
   (if the `workflow-checkpoint` skill has been used), `references/<project>-tickets.md`,
   `references/<project>-context.md` (domain glossary, §E — if present), and grep
   `~/.claude/ops/lessons.md` for the project name. Never assume a fresh start.
2. **No project CLAUDE.md?** Offer to run `/init`, then add the Environment-facts
   block (template below) with values you actually looked up this session.
3. **No ticket ledger?** Create `references/<project>-tickets.md` from the template
   in §C (ask first if the project has its own tracker — one ledger, not two).
4. **Verify, don't inherit**: any command, path, or tool name you plan to rely on —
   run it or `Test-Path` it once now. Record what you verified; write
   "couldn't determine" for what you couldn't.
5. **Relaxation level**: if the main model is frontier-tier and the project
   CLAUDE.md has no `ops-relaxation:` line, ask the user to pick L0/L1/L2 now
   (`05-authority.md` §2) and record the answer in the project CLAUDE.md —
   one ask per project, not per session.

✅ First session: read phase-log → discover phase 2 finished last week → resume
from the open ticket instead of re-planning from zero.
❌ First session: start "helpfully" restructuring, discover in hour two that a
half-finished migration ticket already covered this — now two conflicting efforts.

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

Location: `references/<project>-tickets.md` — sibling of the phase-log so the
`workflow-checkpoint` skill finds both. In-session task tools (TaskCreate etc.)
are fine for live tracking, but they are session-scoped: anything that must
survive a restart gets mirrored here. The file is the authority on resume.

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
(schema → logic → surface → tests), demoable or verifiable on its own, and
sized to fit one fresh context window. Write "what to build" from the user's
perspective, not as a layer breakdown. `blocked-by` edges only where genuine
gating exists — a ticket with no blockers can start immediately.

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

✅ Resume after a crash: `grep "status: active" references/*-tickets.md` → pick
up exactly where the ledger says, partial results path included.
❌ Progress tracked only via the session's task list → restart → the task list
is gone and "where was I" costs an hour of re-discovery.

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
- **Update live**: record a term the moment it crystallizes (design session,
  checkpoint, mid-task) — batching updates is how glossaries die.
- **Challenge, don't just consume**: when the requester's usage contradicts an
  entry ("glossary says cancellation = X, you now mean Y"), surface it and
  update — a stale definition is worse than none.
- **Glossary only**: no specs, no implementation notes, no scratch content.
- **ADR gate** (three ALL required, else no ADR): hard to reverse + surprising
  without context + a genuine trade-off existed. ADRs go in the project's own
  docs (`docs/adr/` or per project convention), one line of gist here.

Maintenance mounts (who keeps it alive): `workflow-checkpoint` asks at each
phase checkpoint whether new terms crystallized; `product-design-thinking`
Phase 3 persists its PIM glossary here; §A step 1 reads it every first session.
