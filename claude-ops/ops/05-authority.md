# Authority & Relaxation — rule classes and the per-project relaxation gate

Why this file exists: the ops layer was written for a non-frontier main model.
When the main session runs on a frontier-tier model, process scaffolding
duplicates its native judgment and taxes tokens. The fix is NOT self-granted
freedom — it is a user-decided, per-project relaxation level. The model states
who it is; the USER decides how much the rules loosen.

## §1 Rule classes

Every ops rule belongs to exactly one class:

- **Invariant** — never relaxes, at any level, for any model. These encode the
  requester's values, safety, and output contracts, which no model tier can
  derive on its own: evidence-based "done" (`30-judgment.md` R2), reviewer ≠
  author, ask-at-value-forks (decision charter, global CLAUDE.md), citation
  honesty / never fabricate, archive-not-delete, subagent model cost cap
  (`model_cap_guard.py`), rule-tier write protection (`40-maintenance.md` §1),
  irreversible-action confirmation.
- **Scaffolding** — process rules that substitute for judgment where judgment
  is scarce: R8 two-pass protocol, R1/R4/R6 rubrics, `10-command-loop.md` step
  ordering, routing-table pre-reads. For a frontier main model these may bind
  as *advisory* (see §2); for cheap/mid main models and ALL subagents they
  stay hard.

## §2 The relaxation gate (user-decided, never self-granted)

**Trigger** — fire at the FIRST of these observable events, not at a predicted
"start of heavyweight work" (a model in execution momentum reliably misjudges
that prediction, and a rule keyed on it never fires):

- (a) about to dispatch the first subagent of a project task;
- (b) about to create or first open a ticket ledger;
- (c) about to enter plan mode / present a plan for a multi-phase task;
- (d) a `[ops-health]` session-start nudge reports the project's relaxation
  level is unset.

At that moment the main model states its model identity/tier in one line and
asks the user to pick this project's relaxation level. One question, three
options:

- **L0 (default)** — everything binds as written. Applies automatically when
  the question was not asked or not answered, and whenever the main model is
  cheap/mid tier.
- **L1 (core)** — R8 two-pass and `10-command-loop.md` step ceremony become
  advisory for the main session: think first in the model's own order, then
  run ONE post-check against the rule after the work, and note any deviation.
  The six OPS.md hard rules still bind even where they cite scaffolding files.
- **L2 (full)** — all scaffolding becomes advisory for the main session
  (think-first + post-check + deviation note). Invariants unchanged.

**Hard boundaries at every level**:
- The model NEVER self-relaxes. No user answer → L0.
- Subagents always receive hard rules regardless of level (they run at
  cheap/mid tier by cap and lack session context).
- Invariants (§1) never relax.

**Deviation note** (L1/L2): when a scaffolding rule is skipped or reordered,
leave one line — `[deviated] <rule ref> — <reason>` — in the response or the
project ledger. This replaces ex-ante compliance with ex-post accountability;
skipping the note voids the relaxation for that task.

**Recording**: after the user answers, offer IN THE SAME TURN to record
`ops-relaxation: L1` (or L0/L2) in the project's CLAUDE.md — the level is a
project property, and one recorded line replaces every future per-session ask
(the ask-every-session variant proved unreliable; see the trigger note).
`60-bootstrap.md` §A includes this as a first-session step. Re-ask only when
the user changes it.

## §3 Relation to the decision charter

The decision charter (owner: global CLAUDE.md, engineering judgement) governs
WHICH decisions the main model may take alone — it applies at every relaxation
level and is not part of this gate. This gate only governs HOW MUCH process
the main model must run while executing.

## §4 Boundary contract (the L1/L2 exchange: scaffolding out, specification in)

Why: a frontier model's dominant failure mode is not execution but silent
scope narrowing — unstated interpretation forks resolved by private guesswork,
over-confident "done", boundaries nobody wrote down. L1/L2 removes procedural
scaffolding the model doesn't need; in exchange, the boundary work it DOES
need is made explicit at task intake. The contract is a per-task artifact,
never a standing rule — it costs context only on the tasks that need it.

**Trigger**: relaxation level is L1 or L2, AND the task is an implementation
task of Tier-2 weight (depth-tier triage, global CLAUDE.md). Analysis/
evaluation answers route to `30-judgment.md` R8 instead — same tier words,
different protocol. Emit the contract BEFORE method or design work starts.

**Format** — 4 sections, HARD CAP 15 lines total; an empty section is the
single word "none". The cap is load-bearing: a contract too long to read in
seconds becomes a fake gate the user skims past.

    ## Boundary Contract — <task>
    1. Interpretation forks: <ambiguity> → chose <reading> because <why>;
       isolation point: <module/param that flips the call if wrong>
    2. Boundary inputs: <inputs/states that break it, trimmed to known env>
    3. Acceptance: <blind-executable checks; mark machine-checkable vs
       human-eye items>
    4. Non-goals & degradation: <explicitly out>; drop <X→Y→Z>, core <W>

**Carrier**: inline in the response for single-session tasks; AS the plan
content when plan mode is active (plan approval = contract sign-off — never
build a parallel gate beside plan mode); copied into the ticket for
multi-session projects. Not a new file format.

**Delivery-time duty**: at close-out, re-check the deliverable against the
contract's section 3 item by item and state the result; deviations are
reported, never silently absorbed. Self-binding is the point — the contract
works even on turns the user doesn't read it, because writing it forces the
forks into the open before momentum builds.

**Supersession**: while a task has a live boundary contract, the four global
CLAUDE.md rules tagged `[BC]` are satisfied BY the contract (don't run them
twice): manual-acceptance checklist (→ section 3), boundary/compatibility
enumeration (→ section 2), degradation-order declaration (→ section 4),
doubted-interpretation isolation point (→ section 1). At L0, or when no
contract exists, those rules bind as written — they serve models and tasks
this mechanism doesn't cover.
