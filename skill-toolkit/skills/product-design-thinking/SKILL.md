---
name: product-design-thinking
description: >-
  High-rigor DESIGN/PLANNING mode for a new product or complex new feature/subsystem:
  first-principles decomposition, mandatory prior-art search BEFORE designing,
  systems-engineering principles, convergence into build-ready documents (Concept Note /
  CIM / RPD / PIM / PSM / DSL semantic contract) with semantic-gap verification between
  layers. Trigger on new product ideas, NEW TOOL/utility design requests (「新工具設計」),
  feasibility evaluation, design-document chains, or planning a complex feature with an
  undecided approach — including MID-CONVERSATION, whenever such a need first emerges,
  not only as an opening request. Deliberately heavyweight —
  NOT for bug fixes, small additions, or implementing an existing spec. Full
  disambiguation: ~/.claude/skill-trigger-dict.md.
---

# Product Design Thinking

A staged thinking protocol for new-product / complex-feature design. Document chain
follows an MDA-style ladder (CIM → PIM+DSL → Verification → PSM+DSL → Implement; see
Phase 3). Derived from this user's real product pipeline and from
recurring failure modes found in a 2026-07 session-history audit: reinvented wheels,
premature implementation, camera/UX semantics decided unilaterally, designs that
drifted from intent, and effort spent where an open-source solution already existed.

User profile to respect throughout: product-minded, NOT deep-technical. Every
engineering choice must come with a plain-language reason and a recommendation
("我不太懂詳細技術" — explain trade-offs, don't just list options).

## Phase 0 — First-principles frame (before any solution talk)

Answer in writing, with the user, before designing anything:

1. **Irreducible pain**: what user pain must this product remove? One sentence.
   If the pain can't be stated without naming a technology, it's a solution in
   search of a problem — push back.
2. **Why must this exist**: what happens if it's never built? Who is the first
   real user (often the user themself — design for their actual environment)?
3. **Essential core vs accident**: strip the idea to the minimal capability that
   still removes the pain. Everything else is a labeled extension, not scope.
4. **Inherited design objects**: when reworking an existing concept/PIM, every
   pre-existing design object ("特定某種設計物件") gets challenged: does it need to
   exist? What's the first-principles alternative? Raise the questionable ones with
   the user instead of silently keeping them.
5. **Boundaries — what this product will NOT do**: write them down. "不要為了擴充
   而擴充" is a standing order; if the core need is already met, recommend stopping.

## Phase 1 — Prior art & open-source sweep (MANDATORY before designing complex parts)

Run this BEFORE proposing an architecture, not after a failed build:

0. **Hypothesis sheet first (two-pass discipline)**: BEFORE searching, write down
   in one short block what you currently believe: the canonical approach for each
   hard sub-problem, candidate OSS libraries from memory, and expected environment
   constraints. Then run the mandatory searches below and diff results against the
   sheet, explicitly recording which beliefs were stale. The sheet sharpens the
   queries and surfaces knowledge drift; it is NEVER a substitute for the search —
   steps 1–4 remain mandatory regardless of how confident the sheet feels.
1. **Search recent info** (WebSearch/WebFetch): current canonical approach for each
   hard sub-problem, recent (≤2y) libraries/models/standards, and how the leading
   existing product actually does it. Design docs written from memory of old
   knowledge are a known failure mode.
   - *Formal-literature slice only*: when a hard sub-problem hinges on published
     scholarly work (papers, standards, textbook methods) — e.g. an algorithm's
     canonical formulation or a reported performance figure — delegate that slice to
     the `literature-search-extract` skill (Mode 2): pass a request contract and
     consume its cited result contract. The OSS-inventory, competitor, and environment
     steps below stay here — literature-search-extract covers scholarly sources, not
     library ecosystems or market positioning.
2. **Open-source inventory**: for every complex capability, list candidate OSS
   libraries/algorithms/reference implementations with: license, maintenance state
   (last release), fit, and integration cost. **If a usable one exists, ASK the user
   whether to adopt it — never silently hand-roll what a maintained library does.**
   Hand-rolling is justified only by a written reason (license, size, learning goal).
3. **Competitor differentiation**: name the strongest incumbent(s). State what this
   product does that they don't, or for whom it's meaningfully better. If there is
   no honest answer, say so and recommend stopping or repositioning — do not design
   around the gap.
4. **Environment constraints, up front**: confirm target runtime early (user's real
   hardware — e.g. consumer GPU/VRAM limits, local-first preference, ollama-class
   local models, static-hosting deploy targets, Windows). A design that ignores the
   deploy environment gets rebuilt later.

## Phase 2 — Systems-engineering design rules

Apply while shaping the architecture:

- **Semantics over implementation (priority rule)**: when an implementation constraint
  conflicts with the semantic model, change the PSM's bridging strategy — never bend a
  PIM semantic to fit a platform. If no bridge preserves the semantic, that is a value
  fork: report it to the user for a ruling (`ops/30-judgment.md` R3), don't pick a side.
- **Low coupling, explicit interfaces**: modules communicate through named contracts
  (schemas, API shapes) written into the design doc, so parts can be rebuilt alone.
- **Swappable weak points**: any component whose quality is doubtful (an OCR engine,
  a depth model, an LLM) sits behind a provider interface so it can be replaced
  without rewriting the pipeline (already a global CLAUDE.md rule — apply it at
  design time, not as a retrofit).
- **Self-checkable**: design in the verification path — health endpoints, smoke-test
  fixtures, a sample input with a known-correct output. Decide at design time which
  of UNIT / SIT / UAT layers this product needs, and list acceptance items per layer.
- **Maintainable & documented**: plan the asset set — user README vs DEV_README
  split, phase log (workflow-checkpoint), i18n/language module if user-facing
  (this user ships bilingual zh-TW/EN products by default — ask early).
- **Extension points, not extensions**: reserve interfaces for the labeled future
  extensions from Phase 0.3; do not build them now.
- **UX semantics are user decisions**: interaction behaviour (click/drag/camera/
  keyboard/defaults/foolproofing) is confirmed with a question before designing it
  in — never picked unilaterally (global rule; it is the #1 historical rework cause).
- **Anti-slop styling**: when the product has a UI, ask for the visual direction
  before defaulting to framework-flavored generic styling; this user prefers plain,
  deliberate design over "AI 味" defaults.

### Security by design (資安內建 — decided HERE, not retrofitted)

"先做功能，安全之後再說" is a named failure mode: security absent at design time
becomes an architecture-level finding later that no patch fixes cleanly. When the
product handles user input, accounts, or data worth stealing, settle these in the
PIM/PSM — each maps to an audit item in security-deep-checklist, which checks at
review time what this list should have decided at design time:

- **Threat-model lite (three questions, written into the design doc)**: what
  assets would an attacker want; where does untrusted data enter (every entry
  point listed); what's the worst realistic abuse case per actor? Depth follows
  asset value — a local single-user tool needs one paragraph, not a workshop.
- **Least privilege as the default**: permission model designed before features —
  default role is the LOWEST; every privilege check server-side (UI-only checks
  count as none); admin functions separated. "權限先放寬，避免影響測試" must be
  a labeled temporary state with a revert task, or it ships.
- **One input-validation layer at the trust boundary**: a unified, server-side,
  allowlist (type/length/format/range) validation layer is an architectural
  element in the PSM — per-module ad-hoc filtering guarantees drift and misses.
- **Error paths fail closed**: design exception flows explicitly — a failed
  security check denies, never skips; production errors return generic messages
  (detail goes to logs); partial-failure states get transactions/rollback.
- **Data classification & secrets policy**: name the sensitive fields in the PIM
  glossary; decide at design time how they're stored (hashed/encrypted), that
  they never appear in logs/debug output, and where secrets live (env/manager —
  never in code). Use platform crypto libraries only; hand-rolled crypto is
  banned by default.
- **Dependency intake rule**: new third-party packages get a quick vet (canonical
  name, maintenance state, install scripts) and land in a pinned manifest — this
  extends the Phase 1 open-source inventory, which already records license and
  maintenance state.
- **Design in the defender's signals**: security events worth logging (auth
  events, denied access, data export) are listed at design time next to the
  self-checkable/observability items — detection can't be bolted on later
  (review-time counterpart: security-deep-checklist Mode C).

## Phase 3 — Converge into build-ready documents

The output of this mode is documents, not code. The document ladder is MDA-style
(CIM → PIM+DSL → Verification → PSM+DSL → Implement). Match whichever layer the
user is at; don't regenerate upstream docs that are already fixed ("拍板的施工合約").

1. **CIM — computation-independent model (why & business semantics)**: pain,
   actors, business rules, boundaries — in business language ONLY. No technology
   nouns; if one appears, it's a solution leaking upstream (Phase 0.1 test).
   A pre-existing "Concept Note" serves as the CIM — don't duplicate it.
2. **PIM + semantic contract (the lightweight DSL)**: platform-independent model =
   domain concepts, relations, invariants, PLUS a semantic-contract section:
   - **Glossary**: every domain noun gets exactly one definition and one name; that
     name is used verbatim in every downstream doc and in code identifiers.
   - **Invariants**: numbered (INV-1, INV-2, …) statements that must hold in any
     implementation.
   - **State machines** for anything with a lifecycle (states, transitions, and
     which invariants guard each transition).
   Keep the DSL at this level — vocabulary + schemas + invariants. Do NOT build a
   formal grammar/parser DSL; maintenance cost exceeds value for this user's scale.
3. **Verification — semantic gate (HARD gate between PIM and PSM)**:
   - **Traceability matrix**: every CIM business rule maps to ≥1 PIM element and
     every PIM element traces back to a CIM rule. Orphans in either direction BLOCK
     entry to PSM — resolve or get an explicit user waiver first.
   - **Semantic gap register**: for each PIM semantic with no direct representation
     on the target platform, record: the gap, the bridging strategy, and whether the
     bridge distorts the semantic (if yes → priority rule in Phase 2 applies).
   - The verification pass is done by a session/subagent that did NOT author the
     PIM where the environment allows it (ops hard rule: author ≠ verifier).
4. **PSM + traceability (platform-specific model)**: stack versions, file layout,
   contracts, milestone order (M0/M1/...), per-milestone acceptance checks. Every
   technical construct cites the PIM element / invariant it implements (e.g.
   "implements INV-3"); platform compromises live in the gap register, never as
   silent edits to the PIM. ADR rule: anything the contract doesn't cover gets
   recorded and asked, not invented.
5. **Selection decisions (選型)**: present each significant choice as
   recommendation + plain-language why + rejected alternatives in one short block,
   get confirmation, and record it in the doc so later sessions don't re-litigate.
6. **Change-tracking discipline (git-first, minimal logs)**: when the docs live in
   a git repo, git history IS the change log — do not maintain per-action or
   per-edit "updated log" sections. Write a log entry only for what a diff cannot
   show: a decision's why (選型 block / ADR), a user waiver at the Verification
   gate, or a semantic change to the PIM. Non-git contexts fall back to a short
   change-log block per document. Task progress stays in the ops ticket ledger;
   phase boundaries stay with workflow-checkpoint — don't create a fourth system.
7. **Handoff**: end with (a) open questions the user must answer, (b) a manual
   acceptance checklist for the first milestone, and (c) an offer to checkpoint
   (workflow-checkpoint) before implementation starts. When implementation begins
   as multi-step/multi-agent work, dispatch per `ops/OPS.md` routing — this skill
   does not define its own dispatch rules.

## Token discipline

This mode is expensive by design — use it only at genuine design/planning boundaries.
Inside a session, converge: once a decision is confirmed, stop revisiting it; put
long research details into the design doc, not the conversation.
