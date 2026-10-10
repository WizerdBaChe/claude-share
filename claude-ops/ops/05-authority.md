# Authority & Relaxation — rule classes and the per-project relaxation gate

Why this file exists: the ops layer was written for a non-frontier **main-loop
model** — the model the main session actually runs on (the main session itself
has no tier; subagents carry their own). When that model is frontier-tier,
process scaffolding duplicates its native judgment and taxes tokens. The fix is
NOT self-granted freedom — it is a user-decided, per-project relaxation level.
The model states who it is; the USER decides how much the rules loosen. Read
the tier live, never from a config pin: `environment.md` "Main-loop model".

**Scale direction (read this before using the labels)**: L-numbers measure
RELAXATION, not rigor — L0 = zero relaxation (strictest, the default), L2 =
full relaxation (loosest). This is inverted relative to ASVS-style
"higher = stricter" scales, so every use of a bare label outside this file
carries a qualifier (e.g. "L2 (fully relaxed)") — see the scale-label rule in
`40-maintenance.md` §3.

**Orthogonal to precedence**: the `global CLAUDE.md > project CLAUDE.md > ops`
precedence order resolves CONFLICTS between rule sources; it does not rank how
binding they are. An ops rule with no conflicting higher rule binds fully at
L0. Relaxation (this file) is the only mechanism that loosens ops rules, and
only the user grants it.

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
  ordering, routing-table pre-reads. For a frontier-tier main-loop model these
  may bind as *advisory* (see §2); for cheap/mid main-loop models and ALL
  subagents they stay hard.

## §2 The relaxation gate (user-decided, never self-granted)

**Trigger** — fire at the FIRST of these observable events, not at a predicted
"start of heavyweight work" (a model in execution momentum reliably misjudges
that prediction, and a rule keyed on it never fires):

- (a) about to dispatch the first subagent of a project task;
- (b) about to create or first open a ticket ledger;
- (c) about to enter plan mode / present a plan for a multi-phase task;
- (d) a `[ops-health]` session-start nudge reports the project's relaxation
  level is unset.

At that moment the main session states its main-loop model identity/tier in one
line — observed, not read off `settings.json` (`environment.md` "Main-loop
model", step 1) — and asks the user to pick this project's relaxation level.
One question, three options:

- **L0 (default)** — everything binds as written. Applies automatically when
  the question was not asked or not answered, and whenever the main-loop model
  is cheap/mid tier.
- **L1 (core)** — R8 two-pass and `10-command-loop.md` step ceremony become
  advisory for the main session: think first in the model's own order, then
  run ONE post-check against the rule after the work, and note any deviation.
  The six OPS.md hard rules still bind even where they cite scaffolding files.
- **L2 (full)** — all scaffolding becomes advisory for the main session
  (think-first + post-check + deviation note). Invariants unchanged.

**Standing ruling (user, 2026-08-11)**: an **Opus-tier** main-loop model runs at
**L1 (core relaxed)** in every project — the gate does not ask, it states the
observed identity and the resulting level in one line. This is a user grant
recorded once, not a self-relaxation; a project CLAUDE.md `ops-relaxation:`
line still overrides it, and every other tier follows the ask flow above.

**Standing ruling (user, 2026-08-30)**: a **Fable-family** main-loop model runs
at **L2 (fully relaxed)** in every project — same mechanics as the 2026-08-11
grant: state observed identity + level in one line, never ask. Safety boundary
of the grant, stated explicitly because L2 is the loosest level: it loosens
SCAFFOLDING ONLY for the main session. Invariants (§1) — evidence-based done,
reviewer ≠ author, subagent model cost cap, rule-tier write protection,
ask-at-value-forks, irreversible-action confirmation — and every
hook-enforced rule (model_cap_guard, branch/secret guards, ui_verify_guard)
bind exactly as at L0; subagents still receive hard rules; the deviation-note
duty (`[deviated] <rule ref> — <reason>`) remains mandatory and skipping it
voids the relaxation for that task. A project CLAUDE.md `ops-relaxation:`
line still overrides in either direction.

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

## §3 The decision charter, and its relation to this gate

The decision charter governs WHICH decisions the main session may take alone —
it applies at every relaxation level and is not part of this gate. This gate
only governs HOW MUCH process the main session must run while executing.
Global CLAUDE.md carries the trigger and the ask-list; this section is the full
text (moved here verbatim 2026-09-19 when CLAUDE.md went over its byte cap —
user ruling, ops/40-maintenance.md §3 "extract, never compress").

**Full text.** When a decision point arises mid-task: standing authority over
implementation-layer decisions that are (a) reversible, (b) not a values fork
(money vs time, privacy vs convenience, aesthetics the user owns), (c) not
changing promised scope or UX/interaction semantics — decide, log choice+reason
in one line AND append it to the process ledger at that moment
(`tools/process-ledger/ledger.py add`, flags in its README; a user ruling
spoken in chat is logged too, with `--origin user --quote "<the user's words,
copied exactly>"` — the tool checks the quote against what the user typed and
labels the row `quote_check`; only `verified` counts as the user's own words,
a paraphrase is the model's reading of a ruling, not the ruling (2026-10-06,
outside critique 3a); a scope narrowed for a
TEMPORARY limit logs, on the same line, the event that lifts it — or it
silently becomes permanent) — the ledger is what survives compaction and is
re-injected after it, the chat line is not. Ask ONLY for: irreversible/outward
actions without standing authorization, values forks, scope/direction changes
to a promise, UX-semantic changes (see CLAUDE.md Interaction style), or an
instruction contradicting an observed fact (surface it). Handing back a
one-sane-answer decision exports decision cost — a miss, not caution. Applies
at every ops-relaxation level.

**Batch approval does not reach a named-authorization item (2026-09-22).** A
recommendation list the user may answer with one word (「走建議」「全部走建議」)
carries every item that needs a NAMED yes — a guardrail constant such as
`DICT_CAP`/`CLAUDE_MD_CAP` (`ops/70-evolution.md` §1 invariant 1), a push to a
public remote, a system setting — in its own labelled block (「需你點名」),
never mixed into the batch; the one-word answer covers the batch only. Two
incidents: 2026-09-08 DICT_CAP raised under "finish fixing these debts" and
ratified afterwards; 2026-09-22 the same constant sat inside a 走建議 list and
cost one extra round trip. The fault in both was the list's shape, not the
reader's.

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
**Classify by what the round will PRODUCE, never by how the request is
phrased** (`lessons.md` L-104, three rounds): a question or an estimate request
("why is there no X?", "has this figure been drawn?", "estimate the loss
items") that will end in new code, figures, numbers or claim scripts is an
implementation task from the moment its first spec, premise list or script is
written — emit the contract THEN, before the premises are drafted. The recall
line alone did not hold; a project whose rounds run through a kit carries the
omission gate there (P2 of `40-maintenance.md` §2a: a `boundary_contract`
field in the round skeleton that the close check refuses empty — SSLD
`open_round.py` v1.1). Everywhere else the contract, or a one-line waiver for a
task that is not Tier-2, is also recorded as ONE process-ledger row
(`ledger.py add --subject boundary-contract`): chat text does not reliably
reach the transcript, the ledger does, and `hooks/boundary_contract_notice.py`
notices the first code write of a session that has neither (registry
`BOUNDARY_CONTRACT_NOTICE`).

**Format** — 5 sections, HARD CAP 18 lines total; an empty section is the
single word "none". The cap is load-bearing: a contract too long to read in
seconds becomes a fake gate the user skims past.

    ## Boundary Contract — <task>
    0. Premises: <irreducible assumptions the task rests on — wrong ⇒ whole
       deliverable invalid>; each tagged [P-env verified <how>] |
       [P-intent reported/asked] | [P-validity verified <how> / ASSUMED,
       blast radius: <impact>]; origin marked (user)/(model) — overturn
       rules: `30-judgment.md` R2 overturn hierarchy
    1. Interpretation forks: <ambiguity> → chose <reading> because <why>;
       isolation point: <module/param that flips the call if wrong>.
       A deliverable that CREATES a new operational unit (tool, hook, store
       tier, index leg, skill mode, gate) also states here: design-mode
       verdict — `Mode B <tier>` (product-design-thinking) or `not Mode B:
       <why>` — and build-here vs hand-off (heavy-round split). A unit born
       as the REMEDY for a defect found mid-session is still Mode B; the fix
       framing exempts nothing. The first question put to the user carries
       the extend-vs-new fork (which existing store/mechanism this would
       duplicate, and why not extend it) before any parameter question.
       Recorded miss 2026-10-05 (AssetVault candidate shelf, L-143): a
       two-repo increment designed in 3 min as a fix, four parameter asks,
       built in the last 50 min of a content session after two compactions.
    2. Boundary inputs: <inputs/states that break it, trimmed to known env>
    3. Acceptance: <machine-checkable checks first; then human-eye items
       ranked `A 必驗` → `B 體驗` per `references/uat.md` (cap, rungs and
       admission gate live there; absolute paths + visible pass, P8/P9)>
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

## §4a The four `[BC]` rules in full

Moved here from global CLAUDE.md 2026-09-06 (that file was 3.6K over its cap
and these four are the one cluster with a real destination: §4 above already
names all four and says when they bind). **The TRIGGERS stay in CLAUDE.md** —
one bullet, so they still fire on a trigger-word match at every relaxation
level; what moved is the mechanics, which are only needed once a trigger has
fired. Read this section when it does, and skip it when a boundary contract is
live.

**BC-1 — a change that cannot be statically verified** (a human must run or
see it). End with an UNASKED manual-acceptance checklist: numbered action +
expected observation, blind-executable by a non-author, plus a non-destructive
way to see what each item judges. Rank by CONSEQUENCE, not by technology:
`A 必驗` (capped; anything that cannot block use → demote) then `B 體驗`, each
ordered high→low so a reader may stop anywhere, and stress paths before happy
ones. The cap's VALUE, the four A rungs, the three B rungs and the admission
gate are stated once, in `ops/references/uat.md` — never restated here. **Absolute paths and copy-runnable commands throughout**
(uat.md P8, user ruling 2026-09-09): the author reads the list from inside the
tree, the user reads it at a fresh prompt, and a repo-relative path silently
serves only the first. Axis and worked examples: `ops/references/uat.md`.

**BC-2 — shipping a baseline you doubt** (the component's quality, or your
reading of the requirement). Put it behind a swappable interface
(provider/injection point) — but ONLY when the replacement is NAMED. A nameless
future is not doubt, it is speculative generality: one interface, one
implementation, until a second is real. For a doubted INTERPRETATION the
artifact is different: name the isolation point in the delivery — which module
or parameter flips the call if the reading turns out wrong.

**BC-3 — a deliverable that may not fit the round's budget or scope.** Declare
the degradation order UP FRONT (drop X → Y → Z, guaranteed core W) instead of
shipping every part at 60 %. Aesthetic or tunable parameters go in one
commented config block with an adjustment-entry table (desired change →
parameter → sane range), so the user can move them without reading the code.

**BC-4 — enumerating boundary or compatibility cases** (resize, DPI,
reduced-motion, devices, browsers). Check the KNOWN environment facts first —
repo config, CLAUDE.md, `ops/environment.md`, what the conversation already
established — and trim the generic list to what actually applies; any item
kept only because the environment is unknown is labelled as a guess. A generic
matrix pasted into a delivery reads as coverage and is not.
