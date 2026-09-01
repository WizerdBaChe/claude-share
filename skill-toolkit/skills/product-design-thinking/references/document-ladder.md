# Phase 3 detail — Document ladder, sole-source rules, handoff

Load when writing or verifying any rung of the ladder. The rung table and the
language column live in SKILL.md; this file carries the per-rung content bar.

**Industry anchor — this ladder IS an SDD.** What IEEE 1016 calls a Software
Design Description — design views + recorded rationale, one view per concern —
maps rung-for-rung onto this ladder: CIM ≈ problem/scope + constraints; PIM ≈
architecture/data/behavior views; PSM ≈ implementation plan; 選型 blocks ≈ ADR
rationale. The PSM doubles as spec-driven development's executable spec — the
artifact an implementing session consumes (industry naming per the 2026-08-27
intake memo: IEEE 1016, github/spec-kit, martinfowler.com, Microsoft
spec-first guidance). Use those terms when mapping outside material; the
ladder's own rung names stay authoritative here.

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
  invariants guard each transition. View selection and blind-spot pairing (when a
  statechart, decision table, sequence pair, or Petri slice):
  `representation-models.md`.

Keep the DSL at this level — vocabulary + schemas + invariants. Do NOT build a formal
grammar/parser DSL; maintenance cost exceeds value at this user's scale.

## 3. Verification — semantic gate (HARD gate between PIM and PSM)

- **Preconditions — checked and reported present/absent before anything else**:
  (a) the mode tier is recorded per SKILL.md Phase 0.6 — if absent, infer it from
  the tier drivers, label it PROVISIONAL, verify against the inferred tier, and
  surface it for confirmation (the tier sets the required view set and ladder
  shape; a pass without one is not reproducible); (b) the CIM version the PIM
  declares as its basis is the current one; (c) each document's own
  version/change-log statements are internally consistent; (d) every file path an
  under-review document asserts as existing (persisted glossary, referenced spec)
  actually exists — a false pointer costs the next session a silent re-derivation.
- **Traceability matrix**: every CIM business rule maps to ≥1 PIM element, and
  every PIM element is assigned one of three ancestries: (1) a CIM business rule;
  (2) a **cross-cutting standing rule** — a named rule from `design-rules.md`,
  global CLAUDE.md, or ops (fail-closed error paths, escaping untrusted input,
  failures that announce themselves, swappable weak points) — legitimate, and it
  must cite its rule by name; do NOT push it into the CIM, which is business
  language only (§1); (3) **orphan** — no ancestry of either kind. Matrix defects
  are class (3) and un-cited class (2); orphans BLOCK entry to PSM — resolve or
  get an explicit user waiver. Trace business-rule **sub-clauses** individually:
  "visually alignable AND mutually navigable" is two obligations, covered only
  when both are — whole-rule matching is the standard way a matrix returns a
  clean sheet over an incomplete design.
- **Design-input → PIM leg**: where a Phase 1 / first-principles input document
  exists, every load-bearing mechanism it commits to — one the cost, feasibility,
  or differentiation argument depends on — has a PIM representation or an
  explicitly recorded deferral to the PSM. A mechanism that carries the product's
  economic case and appears in no rung is a finding, not an implementation detail.
- **Semantic gap register**: for each PIM semantic with no direct representation on
  the target platform, record the gap, the bridging strategy, and whether the bridge
  distorts the semantic (if yes → the priority rule in `design-rules.md` applies).
  **No PSM yet is the normal case at this rung**: the platform is chosen in the
  PSM, so write the register against the *platform class the PIM has already
  committed to* — every platform property it asserts as an invariant or role
  definition (offline artifact, browser document, provider-backed model). Mark
  every entry `platform-conditional`; the PSM must re-run the register against the
  chosen stack. An empty register is a gate FAILURE, not a pass: if the PIM truly
  constrains no platform property, say so and name what was checked.
- **View integrity & correspondence pass**: run `view-integrity-checks.md`
  (§1 per view, §2 across the tier's required view set) over every view the
  documents carry — on the structural text (state tables, node/edge lists),
  never on rendered images. A §1 defect admitting no correct implementation
  (unreachable state, undefined transition on a reachable event) is a
  SKILL.md gate-(c) BLOCK; a missing tier-required view files under §8
  gate 5; the rest are should-fix findings.
- The verification pass is done by a session/subagent that did NOT author the PIM
  where the environment allows it (ops hard rule: author ≠ verifier). Independence
  is a procedure, not just a different session: build the forward and reverse
  matrices from the CIM and PIM text FIRST, and read the author's own traceability
  table LAST, as a diff against yours — a row-by-row audit of the author's table
  can only find wrong rows, never missing elements, and the most common real
  defect is an element absent from the table paired with a "no orphans" claim.

### Deliverable shape (Verification rung)

ONE new file per pass, never an edit to the documents under review — a verifier
reports, never fixes:
`docs/verification_<upstream>-<ver>_<downstream>-<ver>_<date>.md`. In order:
verdict first (pass / blocked, counts per severity, plus a premises &
refutability line per global CLAUDE.md); preconditions; forward matrix; reverse
matrix; semantic gap register; SDD pitfall gate results (§8); consolidated
open-question register (restated, NEVER answered — each load-bearing open
question names what it blocks); the minimum action set that unblocks the next
rung; and a **passed-checks appendix** naming what was examined and found sound
(without it the report is a pure defect list, and the next revision churns what
was deliberately correct). Severities: **BLOCK** (the SKILL.md gate conditions),
**user-ruling-required** (correct only after a decision the user owns),
**should-fix** (a defect with a known, uncontroversial repair). Findings take
stable per-report IDs (V-n traceability/model, SG-n gap register); outside the
report, the first citation carries the report filename (LABEL-REGISTRY §2,
INV-n convention).

## 4. PSM + traceability (platform-specific model)

Stack versions, file layout, contracts, milestone order (M0/M1/…), per-milestone
acceptance checks. Every technical construct cites the PIM element / invariant it
implements ("implements INV-3"); platform compromises live in the gap register,
never as silent edits to the PIM. ADR rule: anything the contract doesn't cover gets
recorded and asked, not invented.

### Sole-source contract rules

Apply to any doc declared the sole build basis — PSM, remediation plan, 施工合約.
From the 2026-07 Prism incident, `ops/lessons.md` L-002. **Exception to this
scope line: the decision-register principle binds at EVERY rung** — a pending
gate's suggested value may not be built on as if decided anywhere; a PIM whose
state machine, invariants, or contracts assume one answer to an open question
says so at the point of use and names the sections that flip with the answer.
Verification checks this (§3 open-question register).

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
for the first milestone — two consequence-ranked sections, `A. 必驗` (≤7) then
`B. 體驗`, never grouped by module or technology (`ops/references/uat.md`) — and
(c) an offer to checkpoint (`workflow-checkpoint`)
before implementation starts. When implementation begins as multi-step/multi-agent
work, dispatch per `ops/OPS.md` routing — this skill does not define its own dispatch
rules.

## 8. SDD pitfall gates (checked at Verification, re-checked at Handoff)

Five design-doc failure modes (IEEE 1016 practice; 2026-08-27 intake). Where a
gate has an existing owner, the owner stays the rule — the gate is only the
scheduled check:

1. **假精確 (false precision)**: a still-exploratory part carrying frozen
   class/table/endpoint detail. Label it 探索中 with a swappable-interface
   isolation point (`design-rules.md`; global `[BC]` rule) — or delete the detail.
2. **Rationale-free choice**: a picked stack/library with no alternatives + why.
   Owner: §5 選型 blocks — retrofit before the doc ships.
3. **Unverifiable quality claims**: "快/穩/安全" with no target, failure
   scenario, or acceptance hook. Owner: the §4 build-ready bar — quantify it or
   label the item SKELETON.
4. **Doc-code divergence by design**: a doc with no named re-check trigger.
   Every rung names when it must be re-read (release, migration, PIM semantic
   change); in-place bumps take the §4 full consistency pass. Owner: §6.
5. **過度統一化 / view inadequacy**: one mega-diagram for every question — or
   the tier's required view set missing members, or a completeness claim carried
   by a lone scenario view (a sequence diagram is one scenario, not the behavior
   space) — split and back per `representation-models.md`; at 全梯 with flagged
   concurrency drivers this includes the Petri-slice analysis. At 速寫 Sketch
   the gates still run, on the single doc.
