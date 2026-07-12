# Lessons — append-only pitfall log

Routing and fold-in rules: `40-maintenance.md` §2. Before starting any task,
grep this file for relevant keywords. Trim trigger: ~30 unfolded entries.
This file is the SOLE pitfall ledger (the memory pitfall-card mechanism was
merged in here 2026-07-12, with zero cards ever written). `tags:` must
include at least one task-type trigger word (e.g. canvas-animation,
cross-session, subagent-dispatch, docs-versioning) so pre-task greps hit by
task type, not only by keyword.

Entry format:
```
## L-NNN <YYYY-MM-DD> tags: <env|dispatch|verify|...> hits: 1
Context: <what was being done>
Pitfall: <what went wrong>
Fix: <the durable fix, and where it now lives if folded in>
```
Recurs? Bump `hits:` instead of adding a duplicate. Replaced? Mark
`SUPERSEDED by L-XXX`, don't delete.

## L-001 2026-07-10 tags: dispatch|cost-cap|hooks hits: 1
Context: eval-5 subagent (spawned sonnet) was killed by a usage limit and
resumed via SendMessage; transcript showed cache_miss_reason model_changed
(claude-sonnet-5 -> claude-fable-5) — resume inherits the MAIN session model.
Pitfall: model_cap_guard.py cannot intercept the resume path. Verified vs
official hooks docs 2026-07-10: PreToolUse fires on SendMessage but the
payload ({to, summary, message}) has no model/resume info; SubagentStart has
no model field and cannot block; no AgentResume event exists.
Fix: rules-side mitigation folded into `ops/environment.md` (Enforcement,
known gap 2): prefer re-spawning a fresh capped agent over SendMessage-resume
for cost-capped work; disclose to the user if a resume is unavoidable. Hook
header documents the hole. Re-check when the hooks API adds resume events.

## L-002 2026-07-12 tags: verify|docs|design|evidence hits: 1
Context: Prism `docs/PSM_REMEDIATION_v1.0.md` (self-titled v1.1) was authored
as the "sole build basis"; an external review (Codex GPT5.6, 8 findings) was
re-audited in-session — all substantially confirmed (one sub-point unfair:
the doc could not cite its own commit hash; the real miss was phase-log).
Pitfall: four failure modes, not one —
(1) Delta-doc economy: normative content delegated via "沿用" to an ARCHIVED
base while claiming sole-basis status; decision gates D-1..D-10 never inlined,
yet their suggested (unapproved) values entered milestone plans as if decided.
(2) Append-only version bump without a consistency pass: filename/title drift,
stale present-tense status lines, new §10.3 items missing from the §3
milestone list they cite, phase-log never updated.
(3) Claim strength > evidence strength: "complete / no gaps / sole basis /
premise refuted" declared on one-pass-survey evidence.
(4) Semantic compression: a two-proposition finding (current machine dead vs
cross-machine not reproducible) "refuted" in one sentence, silently inverting
the surviving proposition.
Additional trigger miss: user explicitly asked for a PSM-grade remediation
plan but product-design-thinking did not fire (remediation of an existing
product read as "implementing an existing spec"), so the doc bypassed the
skill's build-ready bar entirely.
Fix (folded in): (3)+(4) → `30-judgment.md` R2 claim-calibration corollary;
(1)+(2) → product-design-thinking Phase 3.4 sole-source contract rules;
trigger miss → skill description + `skill-trigger-dict.md` widened to
PSM-grade remediation/re-planning. Finding 8 (market claims without
source/date) was already covered by R5's "cite or label unverified" — that
was a violation of an existing rule, not a rule gap.

---
## Archived (folded into another file, or retired)
(none yet)
