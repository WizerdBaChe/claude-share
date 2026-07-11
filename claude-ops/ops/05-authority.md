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

**Trigger**: at the start of heavyweight / systemic work (project development,
multi-phase or multi-session tasks — anything that would engage this ops
layer), the main model states its model identity/tier in one line and asks the
user to pick this project's relaxation level. One question, three options:

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

**Recording**: the chosen level applies to the current project. To make it
standing, the user may ask to record `ops-relaxation: L1` (or L2) in the
project's CLAUDE.md; then re-asking is unnecessary until the user changes it.

## §3 Relation to the decision charter

The decision charter (owner: global CLAUDE.md, engineering judgement) governs
WHICH decisions the main model may take alone — it applies at every relaxation
level and is not part of this gate. This gate only governs HOW MUCH process
the main model must run while executing.
