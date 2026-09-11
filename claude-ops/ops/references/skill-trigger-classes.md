# Skill trigger classes and routing-surface composition

<!--
Class (b) file: charged only when routed to. Read by tools/skill-routing-audit.py
and by a human running the T-016 review. NEVER loaded at session start, and
deliberately NOT stored in SKILL.md frontmatter — the loader accepts `name` and
`description` only, and anything added there is charged to every session.

WHY THIS FILE EXISTS. A firing rate is uninterpretable on its own (user ruling,
2026-08-15). Before this file, `motion-design` at 0 fires and
`ai-coding-guardrails` at 0 fires printed as the same finding; the first is a
phase-gated skill with no UI phase in 43 days, the second looked like the one
real defect in the set. Classifying them took the count from 6 alleged defects
to 2 — and then adjudication took it to 0: `ai-coding-guardrails` turned out to
be second-order (T-017) and `asset-vault`'s omission problem was dissolved by a
user ruling (T-018). Every zero in this environment is currently explained.
That is the point: the tool now reads `class:` and stops reporting expected
silence as news, so a real defect will stand out when one appears.

FORMAT — line-based, one block per skill, parsed by the tool:
  ## <skill-dir-name>
  class:      one of the five below
  source:     utterance | artifact-context | omission | sub-service
  on-fire:    execute | ask-first
  zero-means: free text, printed next to an unexplained zero
  proc:       an exact substring of the description that is PROCEDURE (repeat)

CLASSES
- always-on    fires on every occasion of its kind; a zero IS a defect.
- conditional  fires when a described situation arises; a zero means the
               situation did not arise — check occasions before calling it a bug.
- phase-gated  fires only inside a project phase of a given kind; a zero outside
               that phase is the skill working correctly.
- user-manual  awaits an explicit ask; a zero is evidence of nothing at all.
- sub-service  invoked by another skill, not by the user; an utterance-based
               audit is structurally blind to it.
- second-order reached mainly through a HANDOFF edge from another skill. Its
               zero is only readable together with the upstream skill's count:
               ai-coding-guardrails fired 0x, and the two skills that hand off
               to it fired 0x and 1x. Fixing its routing surface would change
               nothing (found 2026-08-15, T-017).

ON-FIRE — what a fire is allowed to do before the user is consulted. Orthogonal
to class (user ruling, 2026-08-15): class decides WHEN to select, on-fire decides
what selection COSTS. The test is whether firing itself already spends something.

- execute    the first action is read-only, or the skill carries its own consent
             gate further in. A false fire costs a few tokens and self-corrects,
             so asking first is pure friction. Ruled: config-self-audit ("叫到就
             驗，只會好不會壞") and product-design-thinking (15 fires, zero false
             positives to date, and its Phase 0 is a status question anyway — a
             wrong fire gets stopped there).
- ask-first  firing commits real time or writes files. Ruled: workflow-checkpoint
             and project-retrospective, both heavyweight and both file-writing.

Corollary for the routing surface: for an `execute` skill the "ask" sentences are
PROCEDURE and belong in the body. For an `ask-first` PROACTIVE skill the ask IS
the fire — `workflow-checkpoint` keeps "proactively ASK" in its description for
that reason, and it is routing there, not procedure.

SOURCE — what selects the skill. `skill-trigger-dict.md` models `utterance`
only, so a dict entry for an artifact-context or omission skill is fiction by
construction, not by neglect (see the glossary in
references/claude-config-context.md).

THE ROUTING/PROCEDURE TEST. Routing = text that changes WHETHER OR WHEN the
skill is selected. Procedure = text that only changes what happens AFTER it is
selected. Phrasing does not decide it: "never scan unprompted" reads like an
instruction but changes the selection, so it is routing; "ALWAYS asks per
category" also reads like an instruction but only constrains execution, so it is
procedure. Procedure on a routing surface is charged in every session, buys no
routing, and displaces the trigger vocabulary that would.

A `proc:` fragment that no longer matches means the description was rewritten
and the classification is stale. The tool prints STALE; re-classify, do not
delete the line to silence it.

Measured 2026-08-15 (14 skills). Rewritten this pass: project-retrospective
34.3% -> 0%, env-cleanup 33.4% -> 0%, skill-share-packaging 27.0% -> 0% (that
one was also at 97.5% of DESC_CAP, i.e. saturated). Every removed sentence was
verified present in the skill body first, which loads on invoke; nothing was
compressed to hit a number (P-003).

review-when: a skill is added or removed under ~/.claude/skills/, or the audit
prints STALE for any fragment.
-->

## ai-coding-guardrails
class: second-order
source: utterance
on-fire: ask-first    # heavyweight design work; produces mechanisms, not findings
zero-means: expected, and settled — T-017, RESOLVED 2026-08-15, not a defect.
  Two independent causes, neither on the routing surface. (1) Both audit skills
  already hand off INTO it and they fired 0x and 1x, so its zero is downstream
  of theirs. (2) The always-on expectation is served by a higher layer: 8 of its
  9 sections are already covered by an always-on rule or the harness (coverage
  table in the ticket). The 9th, section 8 Recovery, became integrity-sweep
  check 19. Its description is NOT the cause — 0% procedure, 64% of cap, clean
  trigger vocabulary. Do not rewrite it, retire it, or reduce it to a
  lightweight always-on version.

## asset-vault
class: user-manual
source: utterance
on-fire: execute      # a vault lookup is read-only; Modes A/C write and gate themselves
zero-means: expected — user ruling 2026-08-15: ALL THREE MODES wait for an
  explicit ask, none self-triggers mid-build. This replaced an always-on reading
  of Mode B whose failure was omission-shaped and therefore unmeasurable (the
  old T-018). The ruling dissolves the problem rather than solving it: with no
  expectation of an automatic fire, a check that never ran is not a failure, and
  the greppable-marker mechanism L-011 P2 would have built is not needed.

## code-review-deep-checklist
class: user-manual
source: utterance
on-fire: ask-first    # a full deep pass is a long commitment
zero-means: expected — the description requires an explicit DEEP/HOLISTIC ask.
proc: Modes: (A) single file/PR deep review, (B) whole-project architecture health, (C) dependency fitness audit:

## config-self-audit
class: always-on
source: artifact-context
on-fire: execute      # user ruling: 叫到就驗，只會好不會壞
zero-means: would be a defect; measured 28 fires, so it is healthy. Its 0% dict
  coverage is the dict's limit, not the skill's — the object under edit selects
  it, and no utterance vocabulary can capture that.
proc: fixes only after consent

## design-system-suite
class: phase-gated
source: utterance
on-fire: ask-first    # methodology adoption, not a lookup
zero-means: expected — no multi-product suite work occurred in the window.
proc: Contract-first methodology + Day-1 checklist

## env-cleanup
class: user-manual
source: utterance
on-fire: execute      # the scan is read-only; archiving has its own per-category gate
zero-means: expected — awaits a cleanup ask.

## literature-search-extract
class: sub-service
source: sub-service
on-fire: execute      # the calling skill already decided
zero-means: expected AND partly invisible — another skill can invoke it with a
  request contract, which no utterance audit sees.
proc: into a caller-specified deliverable
proc: with full citation traceability; zero fabricated citations.

## motion-design
class: phase-gated
source: utterance
on-fire: execute      # reference and methodology, read-only
zero-means: expected — fires only in a UI/animation implementation phase, and
  13 dict occasions in 43 days were discussion, not implementation.

## product-design-thinking
class: conditional
source: utterance
on-fire: execute      # user ruling: Phase 0 asks anyway; 15 fires, 0 false positives
zero-means: would need the situation checked first; measured 15 fires, healthy.
proc: decomposition, prior-art search BEFORE designing, convergence into build-ready documents

## project-retrospective
class: phase-gated
source: utterance
on-fire: ask-first    # user ruling: heavyweight, scans history, writes files
zero-means: expected, and PERMANENTLY so for claude-config. No project ENDED in
  the window, and under the user's 2026-08-15 ruling that this environment is a
  PRODUCT rather than a project it never will — so this skill's zero here is
  structural, not a routing defect to keep re-investigating. It remains live for
  other projects. Its neighbour workflow-checkpoint fired 24x over the same
  period, which is the correct split.

## scientific-research-guide
class: conditional
source: utterance
on-fire: execute      # declares itself advice-first and non-intrusive
zero-means: expected — domain-gated, and no research question was asked.
proc: Non-intrusive: advice first; writes code or touches data only on explicit request.

## security-deep-checklist
class: user-manual
source: utterance
on-fire: ask-first    # a long audit
zero-means: expected — awaits an explicit 資安檢核 ask.
proc: Modes: (A) code-level audit, (B) deployment & environment posture, (C) detection & response readiness.

## skill-share-packaging
class: user-manual
source: utterance
on-fire: ask-first    # builds a share copy
zero-means: expected, and its 21 dict occasions are the trap this file exists to
  mark — this project IS about skills, so the vocabulary appears constantly in
  development context without ever being a request.

## workflow-checkpoint
class: conditional
source: utterance
on-fire: ask-first    # user ruling: the ask IS the fire
zero-means: would be a defect; measured 24 fires but only 1 of 37 invocations was
  proactive. Under a 30-day acceptance from 2026-08-15 on that rate, not on the
  count.
proc: rebuild from the phase-log alone

## skill-co-upgrade
class:      conditional
source:     utterance
on-fire:    ask-first
zero-means: no skill accumulated field-test debt in the window (no misfire or bypass was reported, no fresh rewrite took a first real run) and the user did not ask for a round; the loop is deliberately on-demand after convergence
proc:       then verify, adopt, and hand off via disposition files so the loop continues across sessions

<!-- Batch added 2026-09-08 (debt sweep): the registry covered 15 of 29 skills.
     The audit's `quiet` population is built from the DICT, so an unregistered
     skill was not printed as a bad verdict -- it was printed as nothing at all,
     and the report's silence about it read exactly like a clean bill. Coverage
     is now printed by the tool itself (skill-routing-audit.py --classes-coverage
     line) so a partial registry cannot be mistaken for a complete one again. -->

## app-residue-sweep
class:      conditional
source:     utterance
on-fire:    ask-first    # it ARCHIVES a file class and emits an admin script; both are the user's call
zero-means: no application was uninstalled in the window, which is the normal
  state -- the skill's occasion is an uninstall, not a schedule. v1 shipped
  2026-09-05 with one profile (codex-chatgpt); a zero until the next real
  uninstall is the skill working correctly.

## audience-fit
class:      conditional
source:     artifact-context
on-fire:    execute
zero-means: no deliverable aimed at a NON-BUILDER reader was produced in the
  window. Its occasion is an artifact's audience, not an utterance, so an
  utterance-based audit is partially blind to it (blind spot 1 above): a zero
  here is weaker evidence than a zero for an utterance-triggered skill.

## diagram-authoring
class:      conditional
source:     utterance
on-fire:    execute
zero-means: no diagram was asked for and no existing system needed
  reconstructing in the window.

## graph-query
class:      conditional
source:     utterance
on-fire:    execute      # read-only queries over a derived graph
zero-means: nobody asked what must be read with X, or what is broken/orphaned.
  Note its second entry point is not an utterance at all: the ops-health graph
  alarm's `harvest due` line routes here, so a zero alongside a live alarm is a
  finding about the ROUTE, not about occasions.

## knowledge-vault
class:      conditional
source:     utterance
on-fire:    ask-first    # Mode A writes into a governed vault with its own AGENTS.md
zero-means: nothing was filed into or looked up from the user's local Obsidian
  knowledge vault. Its first real run is also its calibration (offer
  skill-co-upgrade then), so an early zero carries no verdict about the skill.

## mechanism-share-packaging
class:      conditional
source:     utterance
on-fire:    ask-first    # it writes into a share repo -- outward-facing, the user transmits
zero-means: no mechanism was exported in the window. Occasions are rare by
  construction (one packaged mechanism is months of work), so a zero is the
  expected steady state and says nothing.

## media-fetch-pipeline
class:      conditional
source:     utterance
on-fire:    execute
zero-means: no post link was pasted with intent to save. MEASURED 2026-09-08:
  it fired 1x while the dict explains 0 -- the dict records the wrong words for
  it, which is a defect in `skill-trigger-dict.md`, not in this class.

## model3d-pipeline
class:      conditional
source:     utterance
on-fire:    execute
zero-means: no 3D/CAD/model/drawing-sheet request arose. The capability lives
  outside this repo (`model3d-pipeline`, a separate local project tree) and its
  venv can be stale, so before reading a zero as a routing defect, check the
  pipeline still runs.

## paper-distill
class:      conditional
source:     utterance
on-fire:    execute
zero-means: no paper/preprint/patent was handed over for an evidence audit.
  Paired with paper-story since the 2026-09-03 split (distill = evidence audit,
  story = narrative); a zero for one while the other fires is a ROUTING finding
  between the two, not an occasion finding.

## paper-story
class:      conditional
source:     utterance
on-fire:    execute
zero-means: no paper needed turning into a talk or deck. See paper-distill: the
  pair must be read together, and the lab's weekly cycle is the occasion
  generator for both.

## post-brief
class:      conditional
source:     utterance
on-fire:    execute
zero-means: nobody asked what a pasted post says. Stage 1 of 2 by design; the
  GUI stage is a separate product and its absence is not this skill's zero.

## render-perf
class:      conditional
source:     utterance
on-fire:    execute      # a knowledge pack: it loads references, it does not act
zero-means: no rendering-performance symptom was reported (jank, dropped
  frames, DOM blowup). A knowledge pack's occasion is a SYMPTOM, so a zero
  during a period with no frontend work is expected.

## system-design
class:      conditional
source:     utterance
on-fire:    ask-first    # user ruling: collection-first, ASK-GATE on ambiguity -- never guess
zero-means: expected and RULED so. The pack is early-stage (2 files) and
  registered primarily to COLLECT, not to answer; answering priority is
  deliberately low. A zero is not a defect until the pack is declared
  answer-ready.

## ux-walkthrough
class:      conditional
source:     utterance
on-fire:    execute
zero-means: no interactive surface was walked. Its occasion is an existing or
  designed UI plus a named person and situation; with no UI phase in the
  window, a zero is the skill working correctly.
