# Sections 1–2: Context System & Architecture Guardrails

Section 1 controls what the agent KNOWS; Section 2 controls what the CI will ACCEPT.
They pair: context tells the agent the rules, architecture lint catches the cases
where context failed (was stale, was ignored, was ambiguous). Never deploy one
without the other — context without enforcement drifts, enforcement without context
produces agents that fail lint repeatedly without understanding why.

## Section 1 — Context System

What the AI is told about the existing architecture determines whether it builds
inside your design or invents a parallel one. The most expensive AI failure mode is
not broken code — it is a second, plausible-looking architecture growing beside the
real one.

### Layered AGENTS.md

- Root file ~100 lines maximum. It is a directory, not a manual: it states the four
  mandatory blocks and points into `docs/` for structured knowledge. A giant
  monolithic manual goes stale fast, cannot be validated, and (on some platforms)
  hits size caps — e.g. 32KiB for some tools.
- Instruction-chain merge order: global → repo root → path-level files STACK rather
  than conflict. Put universal rules at the top, directory-specific rules
  (e.g. `frontend/AGENTS.md`) close to the code they govern.
- Knowledge sedimentation rule: any architecture decision that exists only in
  Slack/verbal discussion is treated as nonexistent to the AI until written into the
  repo. When a user reports "the agent keeps doing X wrong", first ask: is the rule
  against X actually written anywhere the agent reads?

### The four mandatory blocks (every root AGENTS.md)

1. **Architecture principles** — layering, allowed dependency direction, disallowed
   reverse dependencies. Name the layers explicitly.
2. **Forbidden actions** — no direct prod DB writes, no destroy-and-rebuild infra,
   no editing generated files, whatever is locally irreversible. Each entry should
   also exist as a mechanical control (Section 5) — the doc entry explains WHY, the
   mechanism enforces.
3. **Risk-tier index** — a pointer to `risk-tiers.json` (see safety-policy.md) so the
   agent can check the tier of a path before touching it.
4. **Test requirements** — coverage floor, required test types per risk tier, and
   the command that runs them.

### AGENTS.md root skeleton (copy-paste starting point)

```markdown
# <Project> — Agent Instructions

## Architecture principles
- Layers (dependencies point left→right only): Types → Config → Repo → Service → API → UI
- Never import from a higher layer. CI enforces this (see .dependency-cruiser.js).
- New modules go under <where>; do not create new top-level directories.

## Forbidden actions
- No writes to production DB. Agents hold read-only roles; write SQL is produced
  for human review, never executed directly.
- No `git push --force`, no history rewrites on shared branches.
- No new dependencies without flagging in the PR risk section.

## Risk tiers
- See risk-tiers.json. Before modifying a path, check its tier; critical-tier
  paths require the workflow in docs/critical-change-process.md.

## Test requirements
- Run: <test command>. Coverage floor: <N>% on changed lines.
- Any change under a high/critical path must include tests in the same PR.

## Deep docs (read on demand)
- docs/architecture.md — full layering rationale
- docs/decisions/ — ADRs; treat as binding
```

### Keeping context alive (anti-"Context Rot")

Stale instructions are worse than none: the AI faithfully follows guidance that now
contradicts the real architecture, and the human assumes the doc is covering things.

- **Doc Freshness checks in CI**: flag docs untouched >90 days; validate that links
  inside AGENTS.md still resolve to existing files.
- **doc-gardening agent**: a scheduled job that scans for stale docs and opens its
  own PRs to refresh them — replaces "20% of Friday spent manually tidying docs".
  The refresh PRs go through normal review; the agent proposes, humans confirm.
- When an ADR is superseded, update AGENTS.md pointers in the same PR — a dangling
  pointer to a dead decision is a context-rot seed.

## Section 2 — Architecture Guardrails

Enforce invariants mechanically in CI rather than micromanaging implementation
choices in review. The goal is to turn "is this coupling allowed" from a judgment
call into a pass/fail, so it costs zero review attention per PR forever after.

### Fixed dependency direction

Define layers explicitly (e.g. Types → Config → Repo → Service → API → UI) and
forbid reverse imports. This one rule blocks the majority of "parallel architecture"
damage, because a foreign architecture almost always needs an illegal import to
attach itself.

Tool mapping by stack:

| Stack | Tool | Notes |
|---|---|---|
| JS/TS | dependency-cruiser | rules in `.dependency-cruiser.js`; also Nx `enforce-module-boundaries` in Nx monorepos |
| Python | import-linter | contracts in `pyproject.toml` / `.importlinter`; `layers` contract type maps directly to the layer model |
| Java/Kotlin | ArchUnit | rules are unit tests — they run wherever tests run, no extra CI step |
| Go | `depguard` / `gomodguard` (golangci-lint) | plus internal packages for hard boundaries |

### Fix-instructions embedded in lint errors

The violation message must state exactly how to correct it, e.g.:

```
ERROR: ui/OrderTable.tsx imports from repo/orders.ts (UI may not import Repo).
FIX: call the service layer instead — services/orderService.ts exposes listOrders().
If no service method exists, add one there; do not widen this rule.
```

Rationale: the agent gets remediation context at the exact moment of failure, inside
the CI output it is already reading. Write the rule once; it teaches every future
change — human or AI — with zero marginal review cost.

### Anti-pattern propagation control

AI faithfully copies existing bad patterns in the repo — it reads them as house
style. One bad pattern can spread across multiple modules within days, because every
new AI task that touches similar code replicates it.

- Catch with structural tests (arch lint, custom AST checks), not human eyeballing —
  humans notice the third copy, CI notices the first.
- When you find a bad pattern: (1) add a lint/structural rule banning NEW instances
  immediately, (2) schedule cleanup of existing instances separately. Blocking
  propagation is urgent; cleanup is not.
- Mark known-bad legacy areas in AGENTS.md ("do not use X as a reference
  implementation; canonical example is Y") so the agent picks a good template.

### Golden principles + background GC task

Keep a short list of core invariants (single digits, not dozens). Pair with an
automated background job that scans for drift and opens refactor PRs — architectural
entropy is continuous, so the counter-pressure must be continuous too. (Mechanics of
GC tasks: see observability-feedback.md, Section 7.)
