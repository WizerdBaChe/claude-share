# Mode B — Whole-Project Review (Systems-Engineering Lens)

Project-wide license applies: legacy code IS in scope here. This mode is recurring
by design — its value is in trends (coupling, debt ratio, hotspot movement), not a
one-off snapshot. These are the same principles product-design-thinking enforces at
design time; here they are audited retrospectively.

## Holism & Boundaries

- Is each module's boundary clearly defined — what it should and should NOT own?
  Watch for boundary erosion: e.g. a validation layer slowly absorbing business
  logic.
- Verify component behavior WITHIN the whole system, not just in isolation, against
  stakeholders' actual understanding of requirements.
- Traceability: can a line of code be traced back to the requirement and design
  rationale that produced it? Loss of this thread is a long-term maintainability
  risk. (Per-unit mechanics: single-review.md §6.)

## Coupling & Cohesion — the most basic, most overlooked health metric

- Coupling = how dependent one module is on another; cohesion = how well a module's
  internals serve a single purpose.
- Project-scope question: does changing one module force changes in several
  seemingly unrelated modules (high coupling), or are modules independently
  replaceable and testable (loose)?
- Low cohesion is the early symptom of a God class / junk-drawer module —
  unrelated responsibilities lumped together for convenience.
- Coupling and cohesion trade off; judge whether the trade-off fits THIS project's
  actual complexity — there is no universal answer.
- Package-level coupling/cohesion metrics are empirically usable to gauge
  modularization quality and flag when remodularization is needed. Measure them
  (import graphs, dependency-cruiser/import-linter output) rather than asserting.

## SOLID as systems-engineering principles at project scope

- **SRP**: does a module change for more than one unrelated reason ("business rule
  changed" AND "database changed")? Cross-check with git log churn reasons.
- **OCP**: can behavior be extended by ADDING modules rather than modifying
  existing ones?
- **DIP**: do details depend on high-level abstractions, or the reverse? Key probe:
  is any module hard-locked to a specific third-party library instead of wrapped
  behind an interface? (Feeds Mode C lock-in assessment.)
- **ISP**: is any module forced to depend on an oversized interface where it needs
  a fraction of the methods?

## Cross-Module State Ownership (project-scope FSM lens)

Per-unit state machines are Mode A §10; this lens audits state as a COUPLING
channel across the project — the class of problem invisible in any single diff
and invisible in the import graph:

- **Distributed state inventory**: where does the same logical state live in
  more than one place (DB + cache + client store + message queue + search
  index)? For each, name the authoritative copy and the reconciliation path
  when copies diverge. No answer = split-brain by design → finding.
- **Implicit shared state as hidden coupling**: globals, singletons,
  module-level caches, env vars mutated at runtime, files used as flags. Each
  is a dependency edge that import-graph coupling metrics miss — enumerate
  them (grep for module-level mutables) and add them to the coupling picture.
- **Lifecycle ownership**: does each business lifecycle (order, user, job…)
  have ONE owning module through which all transitions pass, or do several
  modules write the status field directly? Many writers = shotgun surgery for
  state: one rule change forces edits everywhere, and Mode A §10's invariants
  become unenforceable.
- **Trend metric**: writers-per-lifecycle-field over time (grep count of
  mutation sites). Rising = state boundary eroding, even if every PR passed.

## Contract & Twin-Logic Drift (cross-boundary lens)

Same reconstruction discipline as the FSM lens: the design semantics say "one
rule", the codebase holds N copies of it, and no diff ever shows them drifting
apart. Per-PR checks are single-review.md §11; this lens does the project-wide
inventory (ruleId namespace `review.contract.*`):

- **Boundary-contract inventory**: enumerate the seams — HTTP/RPC APIs, event
  and message schemas, shared enums, error shapes. For each: what is the
  authoritative artifact, and is code on both sides DERIVED from it (codegen,
  shared schema package) or hand-mirrored? Build the table before judging;
  it is also the re-review baseline.
- **Twin-implementation inventory**: rules deliberately implemented on both
  sides — validation (client UX copy + server enforcing copy), permission
  visibility (UI hiding + server authz), lifecycle enums (frontend + backend +
  DB constraint), derived values computed in two places. Twins are legitimate;
  UNGATED twins are the finding. For each pair: shared/generated source, or a
  drift gate (consumer-driven contract test, schema diff in CI, round-trip
  serialization test)? Neither → finding with the derivation mechanism as the
  remediation.
- **Compatibility policy**: is there a stated versioning/evolution rule for
  each contract (additive-only, deprecation window, unknown-field tolerance),
  or does every deploy silently assume both sides ship in lockstep?
- **Architecture fitness functions**: are the intended dependency directions
  and layer boundaries executable (dependency-cruiser / import-linter /
  ArchUnit-style rules in CI), or prose in a wiki? Measure with the tool
  output where present — same rule as coupling metrics above: measure, don't
  assert. An intended boundary with no executable check is drift waiting to
  be discovered by an outage.
- **Documentation drift spot-check**: treat docs (README, API docs, ADRs,
  onboarding guides) as CLAIMS about the code. Sample the highest-traffic
  claims (setup steps, listed endpoints, stated invariants, ADR "we chose X
  because Y") and verify each against the code; every mismatch is a
  `review.contract.doc-drift` finding. Detection only — rewriting or
  restructuring the docs is engineering:documentation's deliverable, and a
  doc-debt backlog is engineering:tech-debt's; hand off with the mismatch
  list.
- **Security note**: the attacker-facing projections of these drifts (client-
  only validation, hidden-but-unprotected functions, enforcement-point desync)
  are already security-deep-checklist territory — record them as `sec.*`
  discovery candidates, do not re-audit them here.

## Architecture View Reconstruction & Integrity Audit（體檢視圖層）

The lenses above audit principles; this lens audits the PICTURE the project
claims to have — and rebuilds it when there is none. Findings namespace:
`review.arch.view-*` (output-contract.md §2). Instrument:
`~/.claude/skills/product-design-thinking/references/view-integrity-checks.md`;
view selection / tier view set: `representation-models.md` beside it.

- **Reconstruct from code, not from docs**: build the Standard-tier view set
  (representation-models.md) from the codebase itself — a component/C4 view
  from the import graph + entry points; a statechart per lifecycle entity
  (same reconstruction discipline as single-review.md §10, applied
  project-wide); ONE sequence pair (success + failure/retry) per critical
  entry point; decision tables where guards are rule-dense. Structural text
  models first (node/edge lists, state×event matrices) — they are the
  auditable artifact and the re-review baseline; render only after they
  check out.
- **Integrity pass**: run view-integrity-checks §1 on each reconstructed
  view; every failed check is a finding (`review.arch.view-gap` — e.g. a
  reachable event with no handling cell, an interface with no contract row;
  per-unit FSM defects found in Mode A keep their `review.state.*` ruleIds).
- **Correspondence pass**: run §2 across the reconstructed set AND against
  the project's existing diagrams — an existing diagram is a CLAIM about the
  code, exactly like doc-drift above; every mismatch files as
  `review.arch.view-inconsistency` with the drifting elements named.
- **Gap table**: emit the §3 gap report; `data-gap` rows mark what the code
  cannot answer (a state no one writes, an interface with no contract, an
  entry point reaching nothing) — those are findings about the SYSTEM, not
  about the drawing.
- **留檔 (archival)**: the reconstructed views + gap table ship WITH the
  report (same basename — embedded mermaid/SVG or a `<report-basename>-views/`
  folder) and are named in coverage.json as units; they are the baseline the
  next recurring review diffs against, like findings (persisting/resolved).
  Presentation-grade rendering for humans (HTML/PPTX) hands off to
  diagram-authoring — this mode's embedded views need to be correct, not
  polished.

## Risk-Management Lens

- Is there a formalized risk list with extra verification for high-risk components
  (risk planning → assessment → control as explicit stages)?
- Is ambition realistically matched to available resources, or is this "ambition
  exceeding capacity" — a feasibility risk, not merely technical?

## Organizational Debt-Management Lens

(Report on these as observations; building the backlog itself is
engineering:tech-debt's deliverable.)

- Is technical debt a living, visible backlog (description, tags, severity,
  suggested owner), or tribal knowledge?
- Is remediation embedded into every sprint's capacity, or a separate initiative
  that never gets scheduled?
- Are tech leads actively pulling debt items into sprints (framed as enabling work
  for upcoming features), rather than waiting for volunteers?

## Mode B output additions

Beyond the standard contract in SKILL.md:
- A hotspot list: change-frequency × quality, from git history + metrics — where
  review/refactor attention should concentrate.
- Trend framing: state explicitly what should be re-measured at the next recurring
  review so the numbers become a trend line.
- The reconstructed view set + gap table, archived beside the report (view-audit
  lens above) — re-derived and diffed at the next recurring review.
