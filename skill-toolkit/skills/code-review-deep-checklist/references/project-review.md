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
