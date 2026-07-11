---
name: ai-coding-guardrails
description: >-
  Design the guardrail SYSTEM and review PROCESS around AI coding agents: context setup
  (AGENTS.md / CLAUDE.md design), permission/sandbox boundaries, AI-PR review flow,
  test/eval gates, destructive-action recovery. Trigger on process-level pain: "AI 寫壞了",
  "agent 刪了不該刪的", "怎麼限制 agent", "AI PR 審不完", or adopting AI coding safely in a team. NOT
  for reviewing one specific diff (→ /code-review or code-review-deep-checklist) or
  human-only coding. Full disambiguation: ~/.claude/skill-trigger-dict.md.
---

# AI Coding Guardrails — bound the agent by mechanism, not vigilance

An AI agent optimizes for the shortest path to a stated goal, not for what is
engineering-correct — to it, deleting a database and deleting a temp file carry the
same cognitive weight. Effective protection therefore comes from making the wrong
action structurally impossible, not from a human staring at every diff. Human review
attention degrades with volume; AI-generated PR volume does not. Every
recommendation below exists to close that asymmetry.

## The three failure classes (know which one you are defending against)

Every AI-coding incident falls into one of three classes. Identify the class first —
it determines which sections apply and how urgent they are:

1. **Wrong-but-plausible code** — compiles, passes a shallow review, is subtly wrong
   or architecturally foreign. Defended by Sections 1–4 (context, architecture
   lint, tests, review process).
2. **Destructive action** — irreversible damage in seconds: dropped table, force-push,
   deleted directory, leaked secret. Defended by Sections 5 and 8 (permissions,
   sandbox, recovery). These must be in place BEFORE the agent runs, not after.
3. **Slow drift** — stale docs, replicated anti-patterns, eroding coverage, review
   rubber-stamping. Defended by Sections 6, 7, 9 (observability, feedback loops,
   governance). Invisible day-to-day; fatal over quarters.

## Scenario router

Identify which situation the user is in, read ONLY the matching reference file(s),
then produce the concrete artifact the situation calls for. Do not lecture through
all nine sections when the user has one specific problem.

| Situation | Read | Deliverable to produce |
|---|---|---|
| Setting up context for an agent (new repo, new team, "agent keeps ignoring our architecture") | [references/context-architecture.md](references/context-architecture.md) | Layered AGENTS.md/CLAUDE.md skeleton + arch-lint CI rule |
| Deciding what the agent may touch (DB, infra, secrets, permissions) | [references/safety-policy.md](references/safety-policy.md) | risk-tiers.json + deny lists + hook/sandbox config |
| Reviewing or merging AI-generated PRs ("review can't keep up") | [references/testing-ci.md](references/testing-ci.md) | Diff-cap policy + cross-model review setup + merge gates |
| Designing tests/evals AI code must pass | [references/testing-ci.md](references/testing-ci.md) | Test-layer gates + incident-to-testcase rule |
| Planning for / recovering from a destructive agent action | [references/recovery-governance.md](references/recovery-governance.md) | Recovery runbook + pre-enabled backup checklist |
| Diagnosing why agents keep failing the same way; fighting drift | [references/observability-feedback.md](references/observability-feedback.md) | Tracing setup + capability-gap diagnosis + GC tasks |
| Team asks "should we adopt all this?" / rollout planning | [references/recovery-governance.md](references/recovery-governance.md) | Scale-tiered adoption plan + wager-clause KPIs |

Two-pass discipline: after identifying the situation, first write a 3-line
diagnosis from the one-screen summary alone — the failure class, the applicable
section(s), and your expected MVG — THEN open the matching reference file to
verify and enrich it. If the reference contradicts your diagnosis, resolve the
divergence explicitly instead of silently adopting the template. Exception: an
incident in progress skips this — recovery first, diagnosis after.

An actual incident in progress ("the agent just dropped X") → recovery FIRST
(reference file, Recovery section), root-cause and guardrail design after service is
restored.

## The nine sections in one screen

Each section below gives the core claim and its **minimum viable guardrail (MVG)** —
the single cheapest enforcement to install if nothing else. Full detail, tooling
tables, and copy-paste templates live in the reference files.

1. **Context System** — what the agent is told about the architecture decides whether
   it builds inside your design or invents a parallel one. MVG: a root AGENTS.md
   under ~100 lines with four mandatory blocks (architecture principles, forbidden
   actions, risk-tier index, test requirements), pointing into `docs/` for depth.
2. **Architecture Guardrails** — enforce invariants in CI, not in review comments.
   MVG: one dependency-direction lint (dependency-cruiser / import-linter / ArchUnit)
   whose error message contains the fix instruction.
3. **Eval & Test Harness** — tests are the control plane for AI code quality, not
   just a safety net; quality ≈ 80% test coverage + 20% prompt quality. MVG: every
   incident fix must land with a test reproducing the failure before the incident
   closes.
4. **CI/PR Automation** — when AI output velocity exceeds review velocity, the merge
   process must adapt. MVG: 50–150 line diff cap per task + writer-model ≠
   reviewer-model.
5. **Safety & Policy** — three layers (risk tiers → permission isolation → sandbox/
   interception) so a bypass of one layer only exposes the next. MVG: a
   `risk-tiers.json` + read-only DB role for agents by default.
6. **Observability** — trace every agent run (reasoning, tool calls, results) so you
   can diff intent vs action; let agents read their own logs to self-debug. MVG:
   keep full agent transcripts.
7. **Feedback Loops** — every failure signals a missing capability (tool, guardrail,
   doc, or validation), not a cue to retry harder. MVG: a max-retry circuit breaker
   on any agent-fix → review → agent-fix loop.
8. **Recovery** — the hard metric is "can we recover", not "nothing has gone wrong
   yet". MVG: verify TODAY that git reflog, file-history, and DB PITR are actually
   enabled — all three are useless if turned on after the incident.
9. **Governance & Rollout** — match guardrail weight to team readiness; a team
   without CI/staging/snapshots must fix infrastructure before adopting agents.
   MVG: the pre-adoption checklist (modern infra + leadership buy-in + tolerance for
   a short-term dip).

## Non-negotiable design principles (apply to any artifact you produce)

- **A guardrail that is only a sentence in a doc does not exist.** Agents under task
  pressure have been observed ignoring text-only freeze rules. Every rule you write
  must name its enforcement mechanism: a revoked credential, a CI gate, a deny-list
  entry, a hook. If the user proposes a policy with no mechanism, say so and propose
  the mechanism.
- **Grade by blast radius, not by likelihood.** `db/`, `infrastructure/`, `auth/`,
  payment paths are critical regardless of how "simple" the change looks.
- **Dry-run → human approval → execute**, in that order, for every destructive
  operation, every time. No exception for "it's just staging" unless staging is
  verified disposable.
- **Default deny for the irreversible, default allow for the recoverable.** Friction
  budget is finite — spend it where undo is impossible (prod DB, force-push, secret
  access), not on read-only exploration.
- **Prompt-injection framing:** all external content the agent reads (issues, web
  pages, dependency READMEs) is untrusted input; any tool call with real-world side
  effects needs pre-action authorization independent of what the content says.
- **Right-size to the team (Section 9).** Recommending the full framework to a
  3-person startup is itself a failure of this skill. Anchor on the zero-cost moves
  first; add weight only where the blast radius justifies it.

## Zero-cost starting moves (offer these when the user is overwhelmed)

1. Write `risk-tiers.json` classifying paths into critical/high/medium/low.
2. Add one CI rule: changes under high-risk paths require tests to merge.
3. Team habit: write the failing test before closing any incident.
4. Verify recovery preconditions exist (reflog window, file history, DB PITR).

## Pitfalls this skill exists to prevent

- No design contract given as context → agent invents a plausible parallel
  architecture (S1+S2).
- One bad existing pattern faithfully replicated across many files within days —
  catch with structural tests, not eyeballs (S2).
- Review throughput < PR throughput → silent rubber-stamping (S4: diff caps,
  cross-model review).
- Broad write/delete access → irreversible action in seconds (S5: read-only default,
  dry-run; S8: pre-enabled PITR).
- Freeze/no-skip-permissions rules that exist only as prose get ignored under task
  pressure → enforce as revoked credentials or sandbox constraints (S5, S8).
- Eval harness written once at project start, never updated → coverage decouples
  from real risk (S3: incident-to-testcase).

## Reference files

- [references/context-architecture.md](references/context-architecture.md) — Sections 1–2: layered AGENTS.md design, doc freshness, dependency lint tooling, anti-pattern propagation. Includes AGENTS.md skeleton.
- [references/testing-ci.md](references/testing-ci.md) — Sections 3–4: test layers as merge gates, agent evals, automated PR loop, cross-model review, diff caps, commit format.
- [references/safety-policy.md](references/safety-policy.md) — Section 5: risk tiering, the five permission-isolation settings, sandbox/interception, Claude Code-specific mappings (settings.json deny lists, PreToolUse hooks, plan mode). Includes risk-tiers.json and hook templates.
- [references/observability-feedback.md](references/observability-feedback.md) — Sections 6–7: OTel tracing, intent-vs-action diffing, capability-gap diagnosis, GC tasks, remediation circuit breakers.
- [references/recovery-governance.md](references/recovery-governance.md) — Sections 8–9: git/file/DB recovery, cross-region backup, code freeze as revoked credentials, adoption checklist, scale-tiered rollout, wager-clause KPIs. Includes ordered incident-response steps and quarterly drill design.
