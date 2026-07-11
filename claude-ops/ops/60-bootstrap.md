# Bootstrap & Ledger — first session in a project, and where progress lives

Two things every project needs before the command loop can run properly: verified
environment facts (step B) and a durable task ledger (step C). Without them,
`10-command-loop.md` steps 1 and 3 have nothing to read or write.

## A. First-session-in-a-project checklist (run once, ~10 minutes)

1. **Read what exists**: project `CLAUDE.md`, `references/<project>-phase-log.md`
   (if the `workflow-checkpoint` skill has been used), `references/<project>-tickets.md`,
   and grep `~/.claude/ops/lessons.md` for the project name. Never assume a fresh start.
2. **No project CLAUDE.md?** Offer to run `/init`, then add the Environment-facts
   block (template below) with values you actually looked up this session.
3. **No ticket ledger?** Create `references/<project>-tickets.md` from the template
   in §C (ask first if the project has its own tracker — one ledger, not two).
4. **Verify, don't inherit**: any command, path, or tool name you plan to rely on —
   run it or `Test-Path` it once now. Record what you verified; write
   "couldn't determine" for what you couldn't.

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
acceptance: <machine-checkable command + expected output>
notes: <optional: decisions, reorders with reasons, partial results path>
```

Rules: update `status` BEFORE announcing "I'll do X next"; reorders are edited
into the ticket before acting and explained when reporting; `done` requires the
evidence demanded by `30-judgment.md` R2. Completed tickets move to an
`## Archive` section at the bottom — never deleted.

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
