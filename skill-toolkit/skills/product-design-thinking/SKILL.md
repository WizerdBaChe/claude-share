---
name: product-design-thinking
description: >-
  High-rigor DESIGN/PLANNING mode for a new product or complex new feature/subsystem:
  first-principles decomposition, mandatory prior-art search BEFORE designing,
  convergence into build-ready documents (Concept Note / CIM / RPD / PIM / PSM / DSL
  semantic contract). Trigger on new product ideas, NEW TOOL/utility design
  (「新工具設計」), feasibility evaluation, or planning a complex feature with an
  undecided approach — including MID-CONVERSATION; also PSM-grade / build-ready
  remediation planning for an EXISTING product (「PSM等級修正案」). Deliberately
  heavyweight — NOT for bug fixes, small additions, or implementing an existing
  spec. Full disambiguation: ~/.claude/skill-trigger-dict.md.
---

# Product Design Thinking

A staged thinking protocol for new-product / complex-feature design. The document
chain follows an MDA-style ladder (CIM → PIM+DSL → Verification → PSM+DSL →
Implement). Derived from this user's real product pipeline and from recurring failure
modes found in a 2026-07 session-history audit: reinvented wheels, premature
implementation, camera/UX semantics decided unilaterally, designs that drifted from
intent, and effort spent where an open-source solution already existed.

User profile to respect throughout: product-minded, NOT deep-technical. Every
engineering choice comes with a plain-language reason and a recommendation
("我不太懂詳細技術" — explain trade-offs, don't just list options).

## Where the detail lives

This file is the spine — the phases, the ladder, and the two things that get missed
when they are not in front of you (the language column, and what blocks a rung).
Load a reference file when you reach its phase; don't preload all three.

| Load | When |
|---|---|
| `references/prior-art-sweep.md` | Phase 1 — before proposing any architecture |
| `references/design-rules.md` | Phase 2 — while shaping architecture; includes security-by-design |
| `references/document-ladder.md` | Phase 3 — writing/verifying any rung; sole-source contract bar |

## Phase 0 — First-principles frame (before any solution talk)

Answer in writing, with the user, before designing anything:

1. **Irreducible pain**: what user pain must this remove? One sentence. If the pain
   can't be stated without naming a technology, it's a solution in search of a
   problem — push back.
2. **Why must this exist**: what happens if it's never built? Who is the first real
   user (often the user themself — design for their actual environment)?
3. **Essential core vs accident**: strip to the minimal capability that still removes
   the pain. Everything else is a labeled extension, not scope.
4. **Inherited design objects**: when reworking an existing concept/PIM, challenge
   every pre-existing design object ("特定某種設計物件") — does it need to exist?
   What's the first-principles alternative? Raise the questionable ones with the user
   instead of silently keeping them.
5. **Boundaries — what this will NOT do**: write them down. "不要為了擴充而擴充" is a
   standing order; if the core need is already met, recommend stopping.

## Phase 1 — Prior art & open-source sweep (before designing complex parts)

Run this BEFORE proposing an architecture, not after a failed build. Four steps,
detailed in `references/prior-art-sweep.md`: write a hypothesis sheet, then search
current canonical approaches, inventory OSS candidates (and **ask** before
hand-rolling what a maintained library does), state the differentiation honestly, and
confirm the real deploy environment. Load that file now if this phase is live.

## Phase 2 — Systems-engineering design rules

Full rule set in `references/design-rules.md`. The two that most often decide the
round: **semantics over implementation** (bend the PSM's bridge, never the PIM's
meaning — a semantic that can't be bridged is a user ruling, not your call), and
**UX semantics are user decisions** (interaction behaviour is confirmed by question
before it is designed in). Security is decided here too, not retrofitted — the
threat-model-lite and least-privilege items are in the same file.

## Phase 3 — Converge into build-ready documents

The output of this mode is documents, not code. Match whichever rung the user is at;
don't regenerate upstream docs already fixed ("拍板的施工合約").

| Rung | What it pins down | Language |
|---|---|---|
| Concept Note / CIM | Pain, actors, business rules, boundaries — business language only | Traditional Chinese |
| PIM + semantic contract | Concepts, relations, glossary, INV-n invariants, state machines | **Bilingual** — Chinese for concepts, relations, rationale (the user intervenes here); English for glossary terms, INV-n IDs, schema/type names, state names, because downstream docs and code quote them verbatim |
| Verification gate | Traceability matrix, semantic gap register | Chinese narrative, English for the IDs being traced |
| PSM / 施工卡 / remediation plan | Stack, file layout, contracts, milestones, acceptance | **English spec body** — files touched, contracts, schemas, milestone steps, commands, error paths, rollback, machine-checkable acceptance. **Traditional Chinese (+ inline English) only on the user's ruling surfaces**: measured results / 盤點, ADR rationale, decision register, manual UAT checklist, degradation declaration, open questions |

Why the PSM row is not "docs → Chinese": a PSM's next reader is an implementing
session, not the user. Defaulting it to Chinese because it is a `.md` under `docs/`
is a recorded miss (2026-07-25). This row implements the global CLAUDE.md **File
output** rule, which stays authoritative if the two ever diverge. Escape hatch: a
concept whose original Chinese wording carries the meaning stays Chinese inside an
English section — keep it and gloss it rather than force a lossy translation.

**Gates worth remembering without opening the reference file:**
- Verification is a HARD gate: an orphan in the traceability matrix blocks entry to
  PSM until it is resolved or the user waives it explicitly.
- A sole-basis doc may not delegate normative content to archived files — archive is
  provenance, never spec.
- An item missing files/contracts/error paths/rollback/test mapping/acceptance is a
  SKELETON and must be labeled so. Shipping it unlabeled is the expensive failure:
  the next session builds on it believing it was complete.

Everything else about the rungs — the per-rung content bar, sole-source contract
rules, 選型 blocks, change-tracking discipline, and the handoff checklist — is in
`references/document-ladder.md`.

## Token discipline

This mode is expensive by design — use it only at genuine design/planning boundaries.
Inside a session, converge: once a decision is confirmed, stop revisiting it; put long
research detail into the design doc, not the conversation.
