# Phase 1 detail — Prior art & open-source sweep

Load when Phase 1 fires (any complex sub-problem before an architecture exists).
Skipping this is a recorded failure mode: reinvented wheels, effort spent where a
maintained library already existed, designs written from stale memory.

## 0. Hypothesis sheet FIRST (two-pass discipline)

Before searching, write one short block of what you currently believe: the canonical
approach per hard sub-problem, candidate OSS libraries from memory, expected
environment constraints. Then search and diff the results against the sheet,
recording explicitly which beliefs were stale.

The sheet earns its keep by sharpening queries and exposing knowledge drift — it is
never a substitute for searching. Steps 1–4 stay mandatory no matter how confident
the sheet feels; confidence is exactly the signal that has been wrong before.

Tier scoping (SKILL.md mode table): at 標準 Standard and 全梯 Full-ladder all four
steps stay mandatory as written. At 速寫 Sketch the sweep narrows to step 2 (OSS
inventory) + step 4 (environment) with a 3-line sheet — but ask-before-hand-rolling
(step 2) never relaxes, and confidence still doesn't waive what remains; the tier,
not the sheet's confidence, is what narrows the sweep, and it is recorded in the doc.

## 1. Search recent info (WebSearch / WebFetch)

For each hard sub-problem: the current canonical approach, recent (≤2y)
libraries/models/standards, and how the leading existing product actually does it.

*Formal-literature slice*: when a sub-problem hinges on published scholarly work —
an algorithm's canonical formulation, a reported performance figure, a standard's
exact wording — delegate that slice to `literature-search-extract` (Mode 2): pass a
request contract, consume its cited result contract. That skill covers scholarly
sources only; the OSS-inventory, competitor, and environment steps below stay here.

## 2. Open-source inventory

For every complex capability, list candidates with: license, maintenance state (last
release), fit, integration cost.

If a usable one exists, **ask the user whether to adopt it** — silently hand-rolling
what a maintained library does is the single most expensive habit this phase exists
to stop. Hand-rolling needs a written reason (license conflict, bundle size, the user
wants the learning), recorded in the design doc so a later session doesn't re-litigate.

## 3. Competitor differentiation

Name the strongest incumbent(s). State what this product does that they don't, or for
whom it is meaningfully better. If there is no honest answer, say so and recommend
stopping or repositioning — designing around the gap just defers the reckoning.

## 4. Environment constraints, up front

Confirm the target runtime early against the user's real hardware: consumer GPU/VRAM
limits, local-first preference, ollama-class local models, static-hosting deploy
targets, Windows. A design that ignores the deploy environment gets rebuilt, and the
rebuild costs more than the question would have.

## Output of this phase

A short block in the design doc — not the conversation — carrying: the hypothesis
sheet's stale entries, the OSS inventory table, the differentiation statement, and
the confirmed environment constraints. Language: this block lives in the CIM/PIM
layer, so bilingual per the ladder table in SKILL.md (Chinese rationale, English
library/API/version names verbatim).
