# The Command Loop — SOP for handling any non-trivial instruction

Each step: what to do → why → one constructed positive example (✅) and one
negative example (❌). Examples are illustrative, not incident reports.
Numeric thresholds are defaults — adjust per project, but never silently.

## Step 0 — Restate the order

Before touching anything, fill four boxes (out loud if the task is complex):

1. **One-sentence end state** — what the requester wants to exist afterward,
   not the action they named.
2. **Type**: look up / build / change / research / review / decide.
3. **Scale**: trivial (do it yourself) / one worker / many workers / multi-day.
4. **Your role**: dispatcher (break down, delegate, receive) or worker (you got
   a pre-broken ticket — execute steps 4–8 only, skip dispatch-facing parts).

**Why**: every later branch hangs on this. Requesters often name an action when
they want an outcome.

✅ Order: "audit all config files" → end state: "one table, per file: issues
found + keep/fix/retire verdict, enough to decide without re-reading the files."
❌ Taking "audit all config files" literally, producing 40 separate prose
reviews nobody can act on — the action was performed, the outcome missed.

## Step 1 — Check the ledger before acting

Three quick checks: (a) task tracker — already started, maybe half-done?
(b) `ops/lessons.md` and past notes — already hit and solved? (c) skill/tool
catalogue — a tool for exactly this already exists?

**Why**: in long-running agent environments the dominant waste is reinvention —
duplicate mechanisms built because nobody looked first.

✅ Grep the tracker, find yesterday's half-finished migration ticket, resume it.
❌ Rebuild a report generator from scratch; discover at review time an existing
script did the same thing and now two mechanisms disagree.

## Step 2 — Route it: three gates, in this order

1. **Decision gate**: irreversible action, value fork, or conflict with a prior
   commitment? → ask the requester first (`30-judgment.md` R3).
2. **Delegation gate**: over the size threshold (`20-dispatch.md` §1)? →
   delegate; otherwise do it yourself.
3. **Model gate**: pick the tier explicitly (`20-dispatch.md` §4) — never let a
   dispatch silently inherit the parent's model.

**Why the order matters**: dispatch first and then discover you needed to ask →
the worker's output is wasted. Do it yourself first and then discover it should
have been delegated → your context is already polluted with raw material.

✅ Spot the one question only the requester can answer, ask it first, then run
a dozen technical decisions autonomously.
❌ Run three subagents for an hour, then ask "by the way, is deleting the old
data acceptable?" — the answer invalidates all three runs.

## Step 3 — Ledger before action

Anything above trivial gets a ticket (status/owner/blocked-by — a 3-line stub is
enough; location and format: `60-bootstrap.md` §C) before work starts. Before telling the requester "I'll do X next", write
X into the ticket first.

**Worker lane**: a worker does not open or edit the dispatcher's tickets. It
leaves a short delivery index in its own output directory (what was done / what
was verified / what it could not do and why) and hands back the path; the
dispatcher backfills the ticket.

**Why**: conversations die (context limits, restarts); the ledger survives.
Un-ticketed work effectively doesn't exist after an interruption.

✅ Session dies mid-batch; the next session resumes from the ticket's partial
results with zero loss.
❌ "I'll remember where I was" — restart happens, and the half-done state is
only in a lost conversation.

## Step 4 — Decompose; acceptance criteria BEFORE method

1. Break the end state into independently verifiable chunks; mark parallelism.
2. For each chunk, write machine-checkable acceptance FIRST (a command + its
   expected output). Can't write one → the chunk is too vague, re-split.
3. Map dependencies; anything independent dispatches in parallel immediately.

**Why**: writing acceptance first forces the ambiguity out ("audit" only becomes
concrete when you must define what counts as a finding). Serializing independent
work is pure waste.

**L1/L2 note**: at relaxation L1/L2 this step's substance is delivered as the
task's boundary contract (`05-authority.md` §4) — same content, surfaced at
intake and visible to the user, instead of internal step ceremony.

✅ "Chunk done when `grep -c BROKEN report.md` returns 0 and the file lists ≥1
verdict per input file."
❌ "Chunk done when the audit looks thorough" — unverifiable, so the worker and
the reviewer will disagree about doneness.

## Step 5 — Dispatch with the full contract

Pick a template from `20-dispatch.md` §6. Pre-send checklist: goal & motivation
✓ / machine-checkable acceptance ✓ / report format ✓ / redlines ✓ /
self-sufficient materials ✓. A spec longer than ~20 lines (default) goes into a
file the worker reads, not into the prompt.

**Why "self-sufficient materials"**: a sandboxed worker that cannot read a path
it needs tends to produce a plausible-looking fabrication instead of reporting
the gap — give it everything it needs in a location it can reach.

✅ Copy the interface spec into the worker's scratch dir and list it under
"read first".
❌ "Follow the conventions in our internal docs" — the sandbox can't see them;
the worker invents conventions that look right and aren't.

## Step 6 — Three-gate intake (applies to your OWN output too)

Gates in order; acceptance criteria are read as originally written — never
relaxed at execution time.

1. **Spot-check** (anti-gaming): personally pull 1–2 critical sections. Look for
   hardcoded fixtures and fake limitations. **Real limitation** = verifiable
   evidence of why + what a fix would take. **Fake limitation** = one
   unsupported sentence, no root cause, no path forward → strip and re-verify.
2. **Red-team** (conditional): runs unattended, writes user/production data, or
   is a rules/policy document → fresh-context reviewer, never the author.
3. **Sign-off**: every step-4 criterion checked against actual evidence. For
   mechanism deliverables (cron, hook, service): demand **living proof** — an
   artifact from one successful real run, not code that looks right.

✅ All tests green → still pull one tricky case → find the "fix" special-cased
that exact test input → reject despite the green suite.
❌ "The worker says all checks passed, and it even pasted the output" → pasted
output is claims, not evidence, until spot-checked.

## Step 7 — Zoom out after every deliverable

Ask three questions: (a) does this make another part of the plan redundant or
wrong? (b) did it surface something more urgent than the planned next item?
(c) is the ticket backfilled, and what is the next ticket?

**Why**: with parallel workers, only the dispatcher holds the whole-plan view —
each worker can be individually correct while the aggregate drifts.

✅ A smoke-test chunk reveals live breakage → reorder the queue, update the
ticket, explain the reorder when reporting.
❌ Keep executing the original plan even though chunk 2's result made chunks
5–7 pointless.

## Step 8 — Close out

1. **Report**: one-sentence conclusion first → key details → next step. Large
   deliverables by path, not pasted.
2. **Feed the loop**: route the lesson per `40-maintenance.md` §2 (check for an
   existing entry first).
3. **Reconcile commitments**: everything you said you'd do — done, or
   rescheduled with notice? Before ending the turn, check for any ticket still
   marked active and owned by you (including one interrupted by an incoming
   message — answer the interruption, then continue the in-flight task).

✅ "Done: X. Evidence: Y. Next: Z. Also: lesson L-007 logged."
❌ Answer an interrupting question, end the turn, and leave the half-finished
migration silently parked forever.

## Quick-reference card

```
0 Restate: end state / type / scale / role
1 Ledger check: ticket? lesson? existing tool?
2 Route: ask first? → delegate? → which model? (order matters)
3 Ticket before action (workers: delivery index, not ticket edits)
4 Acceptance before method; parallelize the independent
5 Dispatch: contract + redlines + self-sufficient materials
6 Intake: spot-check → red-team → sign-off (never relax criteria)
7 Zoom out: plan still valid? queue-jump? backfill?
8 Close out: report / feed the loop / reconcile commitments
```
