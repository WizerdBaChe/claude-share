# Phase 3 detail — Document ladder, sole-source rules, handoff

Load when writing or verifying any rung of the ladder. The rung table and the
language column live in SKILL.md; this file carries the per-rung content bar.

## 1. CIM — computation-independent model

Pain, actors, business rules, boundaries, in business language ONLY. No technology
nouns — if one appears, a solution has leaked upstream (the Phase 0.1 test). A
pre-existing Concept Note serves as the CIM; don't duplicate it.

## 2. PIM + semantic contract (the lightweight DSL)

Domain concepts, relations, invariants, plus a semantic-contract section:

- **Glossary**: every domain noun gets exactly one definition and one name, used
  verbatim in every downstream doc and in code identifiers. Persist crystallized
  terms to `references/<project>-context.md` (`ops/60-bootstrap.md` §E, English
  only) so later sessions inherit the vocabulary; challenge conflicts with existing
  entries instead of silently redefining.
- **Invariants**: numbered (INV-1, INV-2, …) statements that must hold in any
  implementation. The IDs are quoted by the PSM and by code comments, so they stay
  English even in Chinese prose.
- **State machines** for anything with a lifecycle: states, transitions, and which
  invariants guard each transition.

Keep the DSL at this level — vocabulary + schemas + invariants. Do NOT build a formal
grammar/parser DSL; maintenance cost exceeds value at this user's scale.

## 3. Verification — semantic gate (HARD gate between PIM and PSM)

- **Traceability matrix**: every CIM business rule maps to ≥1 PIM element, and every
  PIM element traces back to a CIM rule. Orphans in either direction BLOCK entry to
  PSM — resolve them or get an explicit user waiver first.
- **Semantic gap register**: for each PIM semantic with no direct representation on
  the target platform, record the gap, the bridging strategy, and whether the bridge
  distorts the semantic (if yes → the priority rule in `design-rules.md` applies).
- The verification pass is done by a session/subagent that did NOT author the PIM
  where the environment allows it (ops hard rule: author ≠ verifier).

## 4. PSM + traceability (platform-specific model)

Stack versions, file layout, contracts, milestone order (M0/M1/…), per-milestone
acceptance checks. Every technical construct cites the PIM element / invariant it
implements ("implements INV-3"); platform compromises live in the gap register,
never as silent edits to the PIM. ADR rule: anything the contract doesn't cover gets
recorded and asked, not invented.

### Sole-source contract rules

Apply to any doc declared the sole build basis — PSM, remediation plan, 施工合約.
From the 2026-07 Prism incident, `ops/lessons.md` L-002.

- **Self-contained**: a sole-basis doc may not delegate normative content ("沿用原
  清單") to superseded or archived files — inline it, or drop the sole-basis claim.
  Archive is provenance, never spec.
- **Build-ready bar per item**: files touched, contracts/schemas, error paths,
  migration + rollback, test mapping (Unit/SIT/UAT), acceptance evidence. An item
  missing these is a SKELETON and must be labeled so. Recommended rendering: the
  work-card format (`ops/60-bootstrap.md` §F).
- **Skeleton over silent thinness**: when budget or context can't fill every item to
  the bar, deliver the outline PLUS an explicit "incomplete: items X, Y need a
  dedicated pass" report so the user can re-dispatch. A summary-grade doc presented
  as build-ready is worse than an admitted outline, because the next session builds
  on it without knowing.
- **Decision register completeness**: ALL decision gates in ONE table with status
  (pending/approved/rejected/superseded), decider, and date. A pending gate's
  suggested value may not appear inside a milestone plan as if decided.
- **In-place version bumps need a full-doc consistency pass**: filename / title /
  frontmatter version agree; status statements re-tensed against current reality;
  items added by a new section also land in the milestone lists they cite; the
  supersede note and phase-log entry ship in the same commit.

## 5. Selection decisions (選型)

Present each significant choice as recommendation + plain-language why + rejected
alternatives, in one short block. Get confirmation, then record it in the doc so
later sessions don't re-litigate it.

## 6. Change-tracking discipline (git-first, minimal logs)

When the docs live in a git repo, git history IS the change log — do not maintain
per-action "updated log" sections. Write a log entry only for what a diff cannot
show: a decision's why (選型 block / ADR), a user waiver at the Verification gate, or
a semantic change to the PIM. Non-git contexts fall back to a short change-log block
per document. Task progress stays in the ops ticket ledger; phase boundaries stay
with `workflow-checkpoint` — don't create a fourth system.

## 7. Handoff

End with (a) open questions the user must answer, (b) a manual acceptance checklist
for the first milestone, and (c) an offer to checkpoint (`workflow-checkpoint`)
before implementation starts. When implementation begins as multi-step/multi-agent
work, dispatch per `ops/OPS.md` routing — this skill does not define its own dispatch
rules.
