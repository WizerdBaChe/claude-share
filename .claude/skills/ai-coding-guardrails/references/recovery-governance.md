# Sections 8–9: Recovery & Governance/Rollout

Section 8 assumes guardrails failed; Section 9 decides how much guardrail to build
in the first place. Read Section 8 with one question in mind: "is this enabled
RIGHT NOW?" — every recovery mechanism here is useless if turned on after the
incident.

## Section 8 — Recovery

Guardrails will still fail sometimes, so "can we recover" is the hard metric — not
"has nothing gone wrong yet."

### If an incident is in progress (do this first, in order)

1. Stop the agent (kill the session/process; revoke its tokens if it may still act).
2. Snapshot current state before any repair attempt (copy the worktree, snapshot
   the DB) — repair attempts on the only copy convert a bad incident into an
   unrecoverable one.
3. Identify the recovery layer that applies (git / file / DB, below) and restore.
4. Preserve the agent transcript — root cause comes after service restoration, but
   the evidence must survive.
5. Afterwards: incident-to-testcase (testing-ci.md) + capability-gap diagnosis
   (observability-feedback.md). The incident is not closed until both exist.

### Git-level recovery

- `git reflog` recovers any HEAD state from roughly the last 30 days — commits,
  resets, and rebases that look "gone" usually are not. Deleted UNCOMMITTED work is
  the truly dangerous case, which is why agents should commit early and often on
  their own branches.
- Pair reflog with the full agent transcript (reasoning + tool-call log) to
  pinpoint root cause: the transcript tells you WHY the damaging command was run,
  reflog tells you exactly WHAT state to restore.

### File-level recovery

Files an AI deletes via `rm`/CLI do NOT go through the OS recycle bin. Pre-enable
at least one of: Time Machine / Windows File History, cloud-sync version history
(Dropbox/OneDrive/Drive), IDE Local History (JetBrains/VS Code keep per-file edit
history that survives external deletion). Verify which of these actually covers
the directories agents work in — a backup that excludes the repo directory is
decorative.

### Database-level recovery (PITR)

Continuous WAL archiving plus periodic base backups enable restoring to any
transaction boundary — e.g. one second before a DROP TABLE. Plain nightly dumps
lose up to 24h; PITR loses seconds. Must be enabled in advance; there is no
retroactive PITR. Managed offerings (RDS, Cloud SQL, Azure) have it as a checkbox —
verify it is checked and the retention window is sane.

### Cross-region / cross-account backup

Daily cross-region, ideally cross-ACCOUNT DB snapshots retained 30–90 days. The
threat model is a single compromised account or over-scoped token wiping both the
data and its same-account backups. An agent token that can touch backups violates
Section 5.2's scoping rule by definition.

### Code Freeze mechanism

During high-risk windows (48h pre-launch, major campaigns): force agents to
read-only and route all deploys through human approval. Enforce at the system
level — revoke write tokens, disable deploy credentials — not just in a document.
Agents have been observed ignoring freeze instructions given only as text; a
freeze that exists as prose is a suggestion, a freeze that exists as a revoked
credential is a fact.

### Quarterly recovery drill (live-fire)

Pick one scenario per quarter — "restore this table to 14:03:07 yesterday",
"recover this deleted directory", "roll back this bad merge" — and execute it for
real in a safe environment, measuring time-to-restore. An untested backup is a
hypothesis. The drill also keeps the runbook current and the team calm during real
incidents.

## Section 9 — Governance & Rollout

Decide whether and how aggressively to adopt this framework — over-engineering a
team that isn't ready is itself a failure mode, and recommending everything at once
guarantees nothing gets adopted.

### Pre-adoption checklist (all three, or fix infrastructure first)

1. Modern infra in place: git, CI, a staging environment, regular snapshots.
2. Engineering leadership willing to codify SOPs (risk tiers, review rules) rather
   than relying on tribal judgment.
3. Organization able to tolerate a short-term productivity dip before the
   long-term gain.

If any is missing, the correct advice is "fix infrastructure first" — agents
amplify whatever process exists, including a bad one.

### Scale-tiered rollout

| Team scale | Adopt |
|---|---|
| Small (≤ ~10 eng) | AGENTS.md + basic sandboxing + ONE architecture lint + CI automation + the zero-cost moves. Stop there until pain says otherwise. |
| Mid-size | Add multi-repo AGENTS.md templating, layered evals, risk-tier enforcement in CI, cross-model review. |
| Enterprise | Add multi-tenant governance, policy-as-code (OPA-style), org-wide SBOM/provenance, dedicated eval infrastructure. |

### Wager clauses (KPI design)

Commitments with teeth, agreed in advance so the decision is automatic under
pressure:

- "Any production data incident within 3 months triggers an immediate rollback to
  Plan-Mode-only operation for agents."
- "Quarterly review of post-hoc bug rate on AI-authored commits" (requires tagging
  authorship in commit metadata from day one).
- "Quarterly live-fire recovery drill" (Section 8) with time-to-restore tracked as
  a trend.

### Zero-cost starting moves for tomorrow

1. Write a `risk-tiers.json` (template in safety-policy.md).
2. Add a CI rule requiring tests for any high-risk-path change before merge.
3. Adopt the team habit: write the failing test before closing any incident.
4. Verify recovery preconditions (reflog availability, file history enabled, DB
   PITR checkbox) — 30 minutes of checking, potentially the whole company saved.
