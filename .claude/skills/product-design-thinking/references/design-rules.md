# Phase 2 detail — Systems-engineering design rules & security by design

Load while shaping the architecture, before writing the PIM.

## Architecture rules

- **Semantics over implementation (priority rule)**: when an implementation
  constraint conflicts with the semantic model, change the PSM's bridging strategy —
  never bend a PIM semantic to fit a platform. If no bridge preserves the semantic,
  that is a value fork: report it for a user ruling (`ops/30-judgment.md` R3) rather
  than picking a side, because the choice trades away meaning the user owns.
- **Low coupling, explicit interfaces**: modules talk through named contracts
  (schemas, API shapes) written into the design doc, so any part can be rebuilt alone.
- **Swappable weak points**: any component whose quality is doubtful (an OCR engine,
  a depth model, an LLM) sits behind a provider interface. This is already a global
  CLAUDE.md rule — the point here is to apply it at design time, when it is free,
  instead of retrofitting it after the weak part disappoints.
- **Self-checkable**: design the verification path in — health endpoints, smoke-test
  fixtures, a sample input with a known-correct output. Decide now which of
  UNIT / SIT / UAT layers this product needs, and list acceptance items per layer.
  Test LAYERS are a machine-side split; the UAT layer's own items are ranked by
  consequence (`A. 必驗` ≤7 → `B. 體驗`), never re-grouped by module or by which
  layer they came from — `ops/references/uat.md`. Anything a UNIT/SIT layer
  already covers does not reappear as a human item.
- **Maintainable & documented**: plan the asset set — user README vs DEV_README
  split, phase log (`workflow-checkpoint`), i18n/language module if user-facing.
  This user ships bilingual zh-TW/EN products by default; ask early rather than
  bolting i18n on later.
- **Extension points, not extensions**: reserve interfaces for the labeled future
  extensions from Phase 0.3; do not build them now.
- **UX semantics are user decisions**: interaction behaviour (click/drag/camera/
  keyboard/defaults/foolproofing) is confirmed with a question before being designed
  in. This is the #1 historical rework cause here — a unilateral pick reads as
  finished work and gets discovered late.
- **Anti-slop styling**: when the product has a UI, ask for the visual direction
  before defaulting to framework-flavored generic styling. This user prefers plain,
  deliberate design over "AI 味" defaults.

## Security by design (資安內建 — decided HERE, not retrofitted)

"先做功能，安全之後再說" is a named failure mode: security absent at design time
becomes an architecture-level finding later that no patch fixes cleanly. When the
product handles user input, accounts, or data worth stealing, settle these in the
PIM/PSM. Each maps to an audit item in `security-deep-checklist`, which checks at
review time what this list should have decided at design time.

- **Threat-model lite (three questions, written into the design doc)**: what assets
  would an attacker want; where does untrusted data enter (every entry point listed);
  what's the worst realistic abuse case per actor? Depth follows asset value — a
  local single-user tool needs one paragraph, not a workshop.
- **Least privilege as the default**: permission model designed before features —
  default role is the LOWEST; every privilege check server-side (UI-only checks count
  as none); admin functions separated. "權限先放寬，避免影響測試" must be a labeled
  temporary state with a revert task, or it ships.
- **One input-validation layer at the trust boundary**: a unified, server-side,
  allowlist (type/length/format/range) validation layer is an architectural element
  in the PSM — per-module ad-hoc filtering guarantees drift and misses.
- **Error paths fail closed**: design exception flows explicitly — a failed security
  check denies, never skips; production errors return generic messages (detail goes
  to logs); partial-failure states get transactions/rollback.
- **Data classification & secrets policy**: name the sensitive fields in the PIM
  glossary; decide at design time how they are stored (hashed/encrypted), that they
  never appear in logs/debug output, and where secrets live (env/manager — never in
  code). Use platform crypto libraries only; hand-rolled crypto is banned by default.
- **Dependency intake rule**: new third-party packages get a quick vet (canonical
  name, maintenance state, install scripts) and land in a pinned manifest — this
  extends the Phase 1 open-source inventory, which already records license and
  maintenance state.
- **Design in the defender's signals**: security events worth logging (auth events,
  denied access, data export) are listed at design time next to the
  self-checkable/observability items — detection cannot be bolted on later
  (review-time counterpart: `security-deep-checklist` Mode C).
