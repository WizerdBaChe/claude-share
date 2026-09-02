# Sections 3–4: Eval & Test Harness, CI/PR Automation

Section 3 defines the gates; Section 4 defines the pipeline that flows through them.
Together they answer the core scaling problem: AI output velocity exceeds human
review velocity, so quality control must be mostly mechanical.

## Section 3 — Eval & Test Harness

Tests double as the control plane for AI-generated code quality, not just a safety
net. An agent iterating against a good test suite converges on correct behavior
without a human in the loop; an agent iterating against a weak suite converges on
"passes the weak suite".

### Core heuristic

AI-generated code quality ≈ **80% test coverage + 20% prompt quality**. Coverage is
the durable lever: a better prompt improves one task, a better test protects every
future task. When a user asks "how do I prompt better so the AI stops breaking X",
the usually-correct answer is "add a test for X".

### Classic three layers as hard merge gates

- **Unit / Integration / E2E**, all blocking merge. AI-generated PRs get no lighter
  gate than human PRs — they need a heavier one, because the author cannot be
  embarrassed into carefulness.
- Coverage floor on changed lines (not whole-repo average, which legacy code
  distorts). Risk-tiered: critical paths demand more than low-tier paths.

### Agent-specific evals

- Benchmark "can it actually fix the issue" — SWE-bench-style task suites built
  from your own repo's history (past bugs + their fixing commits make ready-made
  eval cases).
- Turn prompt/agent-behavior tests into regression-checkable CI assets (promptfoo-
  style tooling): when you change AGENTS.md or the agent's system prompt, the eval
  suite tells you whether agent behavior regressed, the same way unit tests do for
  code.
- Treat the eval harness as a first-class artifact: version it alongside the code.
  A harness written once at project start and abandoned measures the project as it
  was, not as it is.

### Incident-to-testcase institutionalization

Every production incident fix must add a test reproducing the failure condition
BEFORE the incident is closed. This is the mechanism that makes coverage growth
track real risk rather than developer guesses. It is also the cheapest rule in this
whole framework relative to its value — pure process, zero tooling.

## Section 4 — CI/PR Automation

When AI output velocity exceeds human review velocity, waiting costs more than
fixing, so the merge philosophy has to adapt — without quietly degrading review into
rubber-stamping.

### Automated PR loop

Human prompts the task → agent opens PR → agent self-reviews → requests additional
agent reviews → responds to feedback → iterates to green. The human's job moves from
line-by-line reading to (a) defining the task well and (b) spot-auditing the loop's
outputs, weighted by risk tier.

### Cross-model review

Have the code-writing AI and the code-reviewing AI be different models and/or
different prompts. The writer optimizes for task completion; the reviewer is
prompted purely to hunt risk. A single model reviewing itself shares its own blind
spots — cross-model review catches the systemic ones. Minimum viable version: same
model, adversarial reviewer prompt, no shared conversation context with the writer.

### Diff-size cap: 50–150 lines per task

Review effectiveness drops off a cliff past ~200 lines. Keep AI task scope small
enough that a human can meaningfully review each PR. Consequences:

- Task decomposition happens BEFORE prompting the agent, not after seeing a 900-line
  PR. A task that cannot be expressed in a ≤150-line diff is multiple tasks.
- Enforce mechanically (CI warns/fails over the cap) with an explicit escape hatch
  for mechanical bulk changes (renames, codemods, lockfiles) — those get a different
  review protocol (verify the transform, not every instance).

### Three-part commit/PR message: what / why / risk

The **risk** section must honestly list: deleted files, changed public exports, new
dependencies, touched risk-tier paths, and any migration/infra side effects.

```
feat(orders): add bulk-cancel endpoint

WHY: support ops team cancelling stuck orders in one call (ticket #482).

RISK:
- new dependency: p-limit@5 (concurrency control)
- touches high-tier path: services/orders (tests added)
- no deleted files, no changed exports, no migrations
```

Rationale: the risk section is machine-checkable (CI can verify claimed
deletions/deps against the actual diff) and gives the human reviewer a triage
signal before reading a single line of code.

### Minimize blocking gates (but never the safety-critical ones)

Keep PRs short-lived; prefer fixing flaky tests after the fact over indefinitely
blocking the pipeline on them. Distinguish two gate classes:

- **Safety gates** (arch lint, risk-tier checks, secret scans, coverage on changed
  lines): never bypassable.
- **Hygiene gates** (flaky E2E, style nits): can be quarantined with an auto-filed
  fix task, so the pipeline keeps moving without the debt silently vanishing.

### Review protocol for an AI-generated PR (ordered)

1. Read the risk section of the PR message; verify its claims against the diff
   (CI-assisted where possible).
2. Check touched paths against risk-tiers.json — tier determines depth of review,
   not the diff's apparent simplicity.
3. Check the tests: do they test the new behavior, or restate the implementation?
   An AI writing both code and tests can produce mutually confirming errors.
4. Check for architecture-foreign constructs: new patterns, new directories, new
   dependencies — anything that smells like a parallel design.
5. Only then read the implementation lines.
