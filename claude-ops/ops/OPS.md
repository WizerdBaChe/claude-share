# OPS — Project-Operations Rules Layer (entry point)

**What this is**: a RULES LAYER, not training data. It is a judgment framework
injected at the start of project work so a non-frontier model does not have to
improvise on already-solved situations. It does not make the model smarter; it
removes the need to re-derive known decisions at runtime. The non-normative
worldview behind all of this lives in `~/.claude/PHILOSOPHY.md` (human-read).

**Precedence**: user's global `~/.claude/CLAUDE.md` > project `CLAUDE.md` > this
layer. On conflict the higher layer wins; log the conflict in `ops/lessons.md`.

**Scope**: multi-step or multi-agent project work — dispatching subagents, batch
operations, tasks spanning sessions. A quick question or a single small edit does
not need this layer.

**Environment facts are never assumed**: any model id, tool name, or mechanism
name mentioned in these files is an example. Verify in the current environment
before relying on it; write "couldn't determine" rather than guess.

## Hard rules (every session, every subagent — details via routing table)

These are hard rules, not suggestions — the target reader is a non-frontier
model. If the environment genuinely prevents one (e.g. no subagent mechanism),
state the deviation explicitly and keep the underlying invariant via the
degraded-mode fallbacks (`20-dispatch.md` §1a, `70-evolution.md` §4).
A frontier-tier MAIN session may have scaffolding rules relaxed to advisory —
but only via the user-decided gate in `05-authority.md`; never self-granted.
Rules 1–6 below are invariants and never relax.

1. **The dispatcher does no fieldwork**: repo-wide scans, large reads, batch
   edits go to subagents; the main context receives conclusions + `file:line`
   only. → `20-dispatch.md` §1
2. **Acceptance criteria before method**, and machine-checkable. If you cannot
   write one, the chunk is too vague — re-split. → `10-command-loop.md` step 4
3. **Verify, don't self-verify**: the author of a deliverable is never its
   verifier. "Done" requires evidence, not "should be fine". → `30-judgment.md` R2
4. **Two retries max per problem** (default, adjustable): the third attempt must
   change method, model, or stop and ask. → `20-dispatch.md` §5
5. **Ask about value forks, not technical choices**; surface contradictions
   instead of silently picking a side. → `30-judgment.md` R3
6. **Subagents never write rule-tier files** (CLAUDE.md at any scope, ops/,
   skills/, hooks/, settings.json): drafts only; the main session reviews and
   performs the actual write. → `40-maintenance.md` §1

## Routing table (read the matching file BEFORE doing this kind of thing)

| Situation | Read |
|---|---|
| Starting heavyweight/systemic work: rule classes + relaxation gate | `ops/05-authority.md` |
| Handling any non-trivial instruction (start here) | `ops/10-command-loop.md` |
| Dispatching a subagent, choosing model/effort, writing a dispatch prompt | `ops/20-dispatch.md` |
| Environment facts: tier→model mapping, cost cap, available mechanisms | `ops/environment.md` |
| Stuck on: escalate? actually done? should I ask? wrong approach? | `ops/30-judgment.md` |
| About to change any ops/rule file, or a lesson worth recording just happened | `ops/40-maintenance.md` |
| Meta-heuristics: how to think through a task (for non-frontier models) | `ops/50-coach.md` |
| First session in a project; where tickets/progress live; ledger templates | `ops/60-bootstrap.md` |
| Proposing/applying guardrail changes; where knowledge belongs (memory vs rules) | `ops/70-evolution.md` |
| Which layer/skill owns what (boundaries vs CLAUDE.md and skills) | `ops/rules-usage-dict.md` |
| Before starting work: grep for past pitfalls | `ops/lessons.md` |
