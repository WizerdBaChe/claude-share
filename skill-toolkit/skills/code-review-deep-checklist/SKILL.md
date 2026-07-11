---
name: code-review-deep-checklist
description: >-
  Deep-methodology code review — only when the user explicitly asks for a DEEP /
  HOLISTIC / PROJECT-WIDE pass: "深入review", "完整審查", "健檢", full code-smell taxonomy,
  requirement traceability, or dependency/選型 fitness audit. Modes: (A) single file/PR
  deep review, (B) whole-project architecture health, (C) dependency fitness. NOT for
  routine pre-merge checks ("review this before I merge" → /code-review) or debt backlog
  deliverables (→ engineering:tech-debt). Full disambiguation:
  ~/.claude/skill-trigger-dict.md.
---

# Code Review Deep Checklist

Code review fails in two opposite directions: too shallow (only "does it compile")
or too unfocused (drowning in nits while missing that the code doesn't match the
requirement, or the architecture is quietly rotting). This skill is the deliberate
deep pass. It is NOT the fast pre-merge gate — if the user just wants "is this diff
safe to merge", stop and use /code-review instead.

## Mode router — settle this FIRST

| User's ask | Mode | Read |
|---|---|---|
| Deep review of one PR/diff/file/module | A: Single review | [references/single-review.md](references/single-review.md) |
| Whole-project / architecture health check | B: Project review | [references/project-review.md](references/project-review.md) |
| "Is library/framework/syntax X still right for us?" / audit dependencies | C: Fitness audit | [references/dependency-fitness.md](references/dependency-fitness.md) |
| Full health check ("整體健檢") | B then C | both project files |

Mode determines the review LICENSE (what you may flag) — see Scope Rules below.
Do not apply Mode B's project-wide license inside a Mode A review.

## Part 0 — Meta questions before reading any code

Answer these before opening the diff; they set intensity and lens:

1. **Purpose**: general pass, or focused on one dimension (security / performance /
   architecture-consistency)? Focused → concentrate depth there, relax elsewhere.
2. **Context before diff**: read the PR description, linked spec/design doc, and the
   "why" first. A context-free review catches "is the code written correctly" but
   misses "does this approach solve the right problem".
3. **Three-pass reading cadence**: pass 1 skim for scope + red flags; pass 2 deep on
   core logic (most time here); pass 3 sweep naming/comments/style. Never start at
   line 1 in detail mode — that's how architectural issues get missed.
4. **Six quality dimensions** as a standing mental checklist: Correctness,
   Completeness, Performance, Readability, Maintainability, Extensibility. Keep all
   six live so attention doesn't collapse onto one.
5. **Cheap tools before expensive attention**: when reviewing LOCALLY, actually run
   the linter/typecheck/tests before manual reading and report their output — don't
   assume. When commenting on a REMOTE PR with CI, assume CI covers them and don't
   duplicate. Reserve judgment-level attention for what tools can't decide.
6. **Business-requirement alignment is a separate check from technical correctness.**
   Code can be flawless and solve the wrong problem. Verify both independently.

## Scope Rules (conflict-resolution — these override checklist enthusiasm)

These resolve the internal tension between "full taxonomy" and "scope discipline",
and keep this skill consistent with the user's global preferences:

- **License by mode.** Mode A: smells/metrics/security checks apply ONLY to code
  this change touches or directly depends on. Pre-existing problems noticed along
  the way go in a separate report section titled "Pre-existing (not this change's
  responsibility)" — flagged as such, never mixed into the verdict on the change
  itself, and never silently fixed. Mode B/C carry project-wide license.
- **Findings-only by default.** This skill produces a report; it does not edit code.
  Apply fixes only when the user explicitly asks after seeing findings.
- **No change for change's sake.** Every refactor/extension proposal must first
  state whether the core need is already met; if it is, the default recommendation
  is to stop. Pair every proposal with cost, benefit, and why-now. Deletion-first
  questions are encouraged: "is this the simplest thing that could work?", "what if
  we deleted it instead?"
- **No personal preference flags.** "I'd have used a different library" is not a
  finding unless it fails a Mode C layer (license, maintenance, security, lock-in).
- **Traceability needs a source.** Part 2.6 checks require a spec/requirement doc.
  If none exists, ask the user for a one-line intent statement per unit under
  review, or mark the item "untraceable — no spec on record". Never fabricate a
  requirement to trace to.
- **Rendering code caveat.** If the reviewed code produces something a human looks
  at (UI, shader, canvas, plot), the verdict may cover the data path only — state
  that visual correctness is unverified and end with a numbered manual-acceptance
  checklist (steps + expected result each).
- **Report artifact.** When the user wants the review as a document: NEW file,
  never overwrite an existing report; human-readable body in Traditional Chinese
  with English technical terms inline.

## Handoffs (do not absorb neighboring skills' jobs)

- Fast pre-merge bug hunt → /code-review (or engineering:code-review).
- Security is the FOCUS (資安健檢, vulnerability sweep, posture/detection audit) →
  security-deep-checklist; Mode A §4 here is only a spot-check for general reviews.
- User wants a standalone, prioritized debt backlog as the deliverable →
  engineering:tech-debt (bring this skill's Mode A/B findings as input).
- Mode C concludes a dependency should be replaced → the decision record is an ADR;
  hand to engineering:architecture.
- Findings are process-level (AI PR volume outpacing review, missing diff caps,
  no cross-model review, agent permission gaps) → ai-coding-guardrails.
- The "requirement is wrong / feature needs redesign" → product-design-thinking.

## Severity & output contract (all modes)

Report findings ranked, each with:

- **Severity**: `blocker` (wrong result / data loss / security) > `should-fix`
  (correctness risk, requirement mismatch, boundary erosion) > `consider`
  (smell, debt, fitness concern — include remediation-cost estimate) > `nit`
  (only if a pass-3 sweep was requested).
- **Confidence**: state it, and how it was verified. An unverified suspicion is
  labeled a suspicion, not a finding.
- **Plain-language intent test**: for each core unit reviewed, one sentence on what
  it does and why this approach — if you cannot write that sentence, that itself is
  a `should-fix` finding (intent not expressed; common with AI-generated code).
- End with: what was NOT covered (dimension, directory, or check skipped) — silent
  truncation reads as full coverage.

## Pitfalls this skill exists to prevent

- Technically-correct diff that silently solves the wrong requirement → Mode A
  traceability checks (single-review.md §6).
- AI-generated code accepted because "it looks clean" with no owner → Mode A §9.
- Duplication/God-classes accumulating because no single PR looks bad enough →
  track file-level metrics over time (Mode B), not just per-PR.
- Dependency adopted for features while ignoring license/maintenance/lock-in →
  Mode C layered evaluation.
- Architecture review reduced to "each PR looks fine" → Mode B is recurring, not
  one-time: coupling/cohesion trends + living debt backlog.
- Debt fixed where it's most visible instead of where it slows the team → hotspot
  prioritization (change-frequency × poor-quality), not raw quality score.

## Reference files

- [references/single-review.md](references/single-review.md) — Mode A: design &
  correctness, error handling & tests, security, style, requirement–data
  consistency, full code-smell taxonomy, quantifiable debt metrics, AI-code checks.
- [references/project-review.md](references/project-review.md) — Mode B:
  systems-engineering principles, coupling/cohesion, SOLID at project scope, risk
  and organizational debt management.
- [references/dependency-fitness.md](references/dependency-fitness.md) — Mode C:
  six-layer fitness evaluation, build-vs-buy, lock-in assessment.
