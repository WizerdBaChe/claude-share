# Sections 6–7: Observability & Feedback Loops

Section 6 makes agent behavior visible; Section 7 turns what you see into
capabilities. Observability without a feedback loop is a very detailed record of
problems you keep having.

## Section 6 — Observability

Observability here is both a debugging tool for humans and dynamic context the
agent itself can use to raise its own autonomy safely.

- **Standardize tracing on OpenTelemetry** for traces/metrics/logs — agent runs are
  distributed systems (model calls, tool calls, sub-agents) and benefit from the
  same tooling.
- **Make every agent run traceable**: log each reasoning step, tool call, and tool
  result. The key analysis primitive is diffing "what the agent intended" (its
  stated plan/reasoning) against "what it actually did" (the tool-call log). Most
  serious agent incidents show a divergence between the two well before the
  damaging call.
- **Keep full transcripts** even if you build nothing else — they are the raw
  material for root-cause analysis (recovery-governance.md pairs them with git
  reflog to reconstruct incidents) and for building eval cases later.
- **Monitor cost and latency trends** to catch runaway retry loops before they
  become runaway spend. A cost spike is often the first externally visible symptom
  of an agent stuck in a loop.
- **Prefer local/isolated observability stacks** tied to a worktree's lifecycle, so
  agents can query their own logs to self-debug without a human in the loop — an
  agent that can read its own failed test output and trace is an agent that needs
  fewer human interventions.

## Section 7 — Feedback Loops

Every failure is a signal about a missing system capability, not a cue to just
retry. Retrying with a slightly different prompt treats the symptom; the failure
class recurs on the next task.

### Capability-gap diagnosis

When an agent gets stuck or misbehaves, classify the missing piece before acting:

| Gap type | Symptom | Fix |
|---|---|---|
| Missing tool | Agent improvises fragile shell pipelines for a routine need | Build/bundle the tool or script once |
| Missing guardrail | Agent did something it shouldn't have been ABLE to do | Add deny rule / hook / permission change (safety-policy.md) |
| Missing documentation | Agent's plan contradicts unwritten team knowledge | Write it into AGENTS.md/docs (context-architecture.md) |
| Missing validation | Bad output passed silently and surfaced downstream | Add a test/eval/CI gate (testing-ci.md) |

Then add the fix as a reusable, mechanically enforced capability — the goal is that
this failure class becomes impossible, not merely less likely.

### Institutionalize GC tasks

Background jobs that scan for architectural drift, update quality tiers, and
auto-open refactor PRs — replacing periodic manual cleanup with continuous
counter-pressure. GC-agent PRs go through the same gates as any other PR; the
automation is in the finding and proposing, not in unsupervised merging.

### Bound the remediation loop

Agent-fixes → review-finds-more → agent-fixes-again needs an explicit max-retry /
circuit breaker (e.g. 3 rounds). Unbounded remediation loops are an industry-wide
open risk: each round can add new code the reviewer must re-review, so an
unconverging loop consumes budget AND grows the diff. On breaker trip: stop, run
capability-gap diagnosis above, involve a human — do not raise the retry limit.
