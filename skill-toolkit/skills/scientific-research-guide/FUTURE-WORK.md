# scientific-research-guide — Future Expansion Notes (planned 2026-07-07, not yet implemented)

> Context: skill v1 + the plasmonic domain profile merged to main on 2026-07-07
> (commit aaa167d). This file records expansion items that have already been
> evaluated and are awaiting a future session's decision/implementation, ordered
> by value-to-risk ratio.
> On resuming work: reading this file alone should be enough to rebuild context —
> no need to re-read the original conversation.

## Backlog (priority order)

### ① Research-state file mechanism — IMPLEMENTED 2026-07-12
- Goal: zero re-explaining across sessions. Each research project maintains a
  `research-state.md` (current Tier, per-section completion, iteration log —
  i.e. a living-document version of the tier-framework §7.4 output artifact).
- Done: SKILL.md Gate A gained a "Continuity check (fires before Step 0)" that
  reads `research-state.md` first and rebuilds state without re-asking; Gate D
  gained a consent-gated update rule (offer on tier/decision/iteration advance,
  write only on yes, append-only iteration log). Template added to
  deliverables.md (跨 Session 進度追蹤器). Eval case 5 + fixture
  (evals/fixtures/research-state.example.md) added and run.
- Branch: feat/research-state-mechanism.

### ② scripts/ deterministic analysis tools (wait for repeated need to emerge; don't build ahead of time)
- Candidates: statistical-test selector, Bootstrap 95% CI (5000 iterations),
  four-panel residual diagnostics, PRISMA counter.
- Principle: skill-creator's "package only once you see repetition" — the same
  analysis must be hand-written ≥2 times in actual use before it's worth
  promoting into scripts/.
- Boundary: execution still falls under Gate C (only runs on explicit request),
  consistent with "semi-automatic = propose → confirm → execute."

### ③ Tier 1 literature-scan dispatch (don't extend this skill — compose instead) — HOOKED UP 2026-07-07
- Primary route (targeted search + extraction with citation traceability): delegate
  to the `literature-search-extract` skill (Mode 2, request/result contract). This is
  now wired into SKILL.md Gate B and tier-framework.md §1. Use it for locating sources
  and extracting methods/parameters/limits per §1.1/1.3/1.4/1.6.
- Secondary route (broad multi-source topic reconnaissance, not per-source extraction):
  compose with deep-research. Rule of thumb: literature-search-extract when you need
  cited, source-anchored extraction; deep-research when you need a wide topic sweep.
- Constraint: subagent model cap is haiku/sonnet (see memory:
  subagent-model-cost-cap); workflow-level multi-agent dispatch requires
  explicit user request each time.

### ④ settings.json hooks — evaluated, **not adopted**
- Reason: a global hook would pollute non-research conversations, which
  conflicts with this skill's on-demand trigger nature; item ① achieves the
  same goal at lower cost.

## Fixed procedure for adding a new domain (finalized, follow as-is)
1. Use `domains/domain-expansion-guide.md` §2's three trigger conditions to
   decide "new profile vs. extend existing."
2. Copy `domains/_template.md` and fill in the seven required sections plus the
   boundary section and decision-trigger checklist; Node 5 (typical value
   ranges) and Node 6 (≥6 pitfalls) need domain-expert input from the user
   (can be supplied as an external markdown handoff).
3. Run the quality checklist in the guide's §6; per Gate B, verify the cited
   literature anchors point to sources the user can actually access.
4. Wire in at three places: add the domain's trigger keywords + reference map
   to SKILL.md's description; add an entry to skill-trigger-dict.md; add a
   pitfall-trigger test case to evals/evals.json and actually run it (use the
   Drude test case as a reference).
5. Feature branch → tests pass → merge to main.

## Other open items
- The description-trigger optimization loop (skill-creator's run_loop, 20
  should/should-not queries) has never been run; run it if under- or
  over-triggering is observed.
- config-self-audit has not yet run a formal audit on this skill.

## Status log
- 2026-07-12 — evals/evals.json executed for the first time (4 cases, sonnet /
  Sonnet 5, protocol-level grading via 4 subagents): 4/4 pass, 15/15 assertions.
  One known limitation recorded in the file's `run.known_limitation` (generic
  metrics have no calibrated range-check; only loaded domain profiles do).
  Behaviour is now verified, not just designed. See STATUS.md for the full picture.
- Note on backlog item ②: scripts/ is a DELIBERATE deferral (build only once the
  same analysis is hand-written ≥2×), NOT an unfinished gap — do not treat as
  incomplete in a future audit.
