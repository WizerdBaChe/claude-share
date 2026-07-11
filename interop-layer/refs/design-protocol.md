<!--
  <URL> — curated, agent-neutral distillation of the
  product-design-thinking methodology (canonical source:
  ~/.claude/skills/product-design-thinking/<URL>).

  Reference-compile class (<URL>): the ROUTING mechanism
  (automatic skill triggering) does not migrate; this file carries the
  methodology CONTENT only. Target agents are pointed here by a prose
  index in their generated <URL> — a deliberate degradation from
  mechanical triggering to instructed reading.

  Content policy: agent-neutral English. No references to platform-specific
  skills, hooks, subagent dispatch, or file paths outside this folder.
  When the canonical skill changes, the curation loop (status → review →
  curated) is responsible for re-distilling this file.
-->

# Design Protocol — staged thinking for new products / complex features

Use when designing a new product, a new tool/utility, or a complex feature
whose approach is undecided. Deliberately heavyweight — NOT for bug fixes,
small additions, or implementing an existing spec.

User profile to respect: product-minded, not deep-technical. Every
engineering choice comes with a plain-language reason and a recommendation —
explain trade-offs, don't just list options.

## Phase 0 — First-principles frame (before any solution talk)

Answer in writing, with the user, before designing anything:

1. **Irreducible pain**: what user pain must this remove? One sentence. If
   the pain can't be stated without naming a technology, it's a solution in
   search of a problem — push back.
2. **Why must this exist**: what happens if it's never built? Who is the
   first real user (often the user themself — design for their actual
   environment)?
3. **Essential core vs accident**: strip the idea to the minimal capability
   that still removes the pain. Everything else is a labeled extension, not
   scope.
4. **Inherited design objects**: when reworking an existing concept, every
   pre-existing design object gets challenged: does it need to exist? What's
   the first-principles alternative? Raise questionable ones with the user
   instead of silently keeping them.
5. **Boundaries — what this will NOT do**: write them down. If the core need
   is already met, recommend stopping; never extend for extension's sake.

## Phase 1 — Prior art & open-source sweep (MANDATORY before designing)

Run BEFORE proposing an architecture, not after a failed build:

0. **Hypothesis sheet first**: before searching, write down current beliefs —
   canonical approach per hard sub-problem, candidate libraries from memory,
   expected environment constraints. Then search and diff results against the
   sheet, recording which beliefs were stale. The sheet sharpens queries; it
   never substitutes for the search.
1. **Search recent info**: current canonical approach for each hard
   sub-problem, recent (≤2y) libraries/models/standards, how the leading
   existing product does it. Designs written from memory of old knowledge
   are a known failure mode.
2. **Open-source inventory**: for every complex capability, list candidate
   libraries with license, maintenance state (last release), fit, and
   integration cost. If a usable one exists, ASK the user whether to adopt
   it — never silently hand-roll what a maintained library does.
   Hand-rolling needs a written reason (license, size, learning goal).
3. **Competitor differentiation**: name the strongest incumbent(s). State
   what this product does that they don't, or for whom it's better. No
   honest answer → say so and recommend stopping or repositioning.
4. **Environment constraints up front**: confirm target runtime early (real
   hardware limits, local-first preference, deploy targets, OS). A design
   that ignores the deploy environment gets rebuilt later.

## Phase 2 — Systems-engineering design rules

- **Semantics over implementation**: when an implementation constraint
  conflicts with the semantic model, change the platform-specific bridging
  strategy — never bend a platform-independent semantic to fit a platform.
  If no bridge preserves the semantic, that is a value fork: report it to
  the user for a ruling, don't pick a side.
- **Low coupling, explicit interfaces**: modules communicate through named
  contracts (schemas, API shapes) written into the design doc.
- **Swappable weak points**: any component of doubtful quality (an OCR
  engine, a model, an external service) sits behind a provider interface so
  it can be replaced without rewriting the pipeline.
- **Self-checkable**: design in the verification path — health endpoints,
  smoke-test fixtures, a sample input with known-correct output. Decide at
  design time which of UNIT / SIT / UAT layers apply; list acceptance items
  per layer.
- **Maintainable & documented**: plan the asset set — user README vs dev
  README split, a phase log (see the phase-log protocol), i18n module if
  user-facing (this user ships bilingual zh-TW/EN products by default — ask
  early).
- **Extension points, not extensions**: reserve interfaces for the labeled
  future extensions from Phase 0.3; do not build them now.
- **UX semantics are user decisions**: interaction behaviour (click/drag/
  camera/keyboard/defaults/foolproofing) is confirmed with a question before
  designing it in — never picked unilaterally.
- **Anti-slop styling**: when the product has a UI, ask for the visual
  direction before defaulting to framework-flavored generic styling; this
  user prefers plain, deliberate design over generic AI-default looks.

### Security by design (decided HERE, not retrofitted)

When the product handles user input, accounts, or data worth stealing,
settle these in the design docs:

- **Threat-model lite**: what assets would an attacker want; where does
  untrusted data enter (every entry point listed); worst realistic abuse
  case per actor. Depth follows asset value — a local single-user tool
  needs one paragraph, not a workshop.
- **Least privilege as default**: permission model before features; default
  role is the LOWEST; every privilege check server-side; admin separated.
  "Loosen permissions for testing" must be a labeled temporary state with a
  revert task, or it ships.
- **One input-validation layer at the trust boundary**: unified, server-side,
  allowlist validation as an architectural element — per-module ad-hoc
  filtering guarantees drift.
- **Error paths fail closed**: a failed security check denies, never skips;
  production errors return generic messages (detail to logs); partial
  failures get transactions/rollback.
- **Data classification & secrets policy**: name sensitive fields in the
  glossary; decide storage (hashed/encrypted), keep them out of logs, put
  secrets in env/manager — never in code. Platform crypto only; hand-rolled
  crypto is banned.
- **Dependency intake**: new packages get a quick vet (canonical name,
  maintenance state, install scripts) and land in a pinned manifest.
- **Defender's signals**: list security events worth logging (auth events,
  denied access, data export) at design time — detection can't be bolted on.

## Phase 3 — Converge into build-ready documents

Output is documents, not code. Document ladder (MDA-style):
CIM → PIM + semantic contract → Verification gate → PSM → Implement.
Match whichever layer the user is at; don't regenerate fixed upstream docs.

1. **CIM (computation-independent)**: pain, actors, business rules,
   boundaries — business language ONLY; a technology noun here is a solution
   leaking upstream.
2. **PIM + semantic contract**: domain concepts, relations, invariants, plus:
   - **Glossary**: every domain noun gets exactly one definition and one
     name, used verbatim in every downstream doc and in code identifiers.
   - **Invariants**: numbered (INV-1, INV-2, …) statements that must hold in
     any implementation.
   - **State machines** for anything with a lifecycle (states, transitions,
     which invariants guard each transition).
   Keep this level lightweight — vocabulary + schemas + invariants; do NOT
   build a formal grammar/parser DSL.
3. **Verification (HARD gate between PIM and PSM)**:
   - **Traceability matrix**: every business rule maps to ≥1 PIM element and
     back. Orphans in either direction BLOCK entry to PSM — resolve or get an
     explicit user waiver.
   - **Semantic gap register**: for each PIM semantic with no direct platform
     representation, record the gap, the bridging strategy, and whether the
     bridge distorts the semantic (if yes → semantics-over-implementation
     rule applies).
   - Where the environment allows, the verification pass is done by a
     reviewer that did NOT author the PIM.
4. **PSM + traceability**: stack versions, file layout, contracts, milestone
   order (M0/M1/…), per-milestone acceptance checks. Every technical
   construct cites the PIM element/invariant it implements; platform
   compromises live in the gap register, never as silent PIM edits. Anything
   the contract doesn't cover gets recorded and asked, not invented.
5. **Selection decisions**: each significant choice = recommendation +
   plain-language why + rejected alternatives in one short block; confirm
   with the user; record in the doc so later sessions don't re-litigate.
6. **Change tracking**: in a git repo, git history IS the change log — write
   a log entry only for what a diff cannot show (a decision's why, a user
   waiver at the verification gate, a semantic change to the PIM).
7. **Handoff**: end with (a) open questions the user must answer, (b) a
   manual acceptance checklist for the first milestone, (c) an offer to
   write a phase-log checkpoint before implementation starts.

## Token discipline

This protocol is expensive by design — use only at genuine design/planning
boundaries. Once a decision is confirmed, stop revisiting it; put long
research details into the design doc, not the conversation.
