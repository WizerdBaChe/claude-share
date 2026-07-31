# Lessons — append-only pitfall log

Routing and fold-in rules: `40-maintenance.md` §2. Before starting any task,
grep this file for relevant keywords. Trim trigger: ~30 unfolded entries.
This file is the SOLE pitfall ledger (the memory pitfall-card mechanism was
merged in here 2026-07-12, with zero cards ever written). `tags:` must
include at least one task-type trigger word (e.g. canvas-animation,
cross-session, subagent-dispatch, docs-versioning) so pre-task greps hit by
task type, not only by keyword.

Entry format:
```
## L-NNN <YYYY-MM-DD> tags: <env|dispatch|verify|...> hits: 1
Context: <what was being done>
Pitfall: <what went wrong>
Fix: <the durable fix, and where it now lives if folded in>
```
Recurs? Bump `hits:` instead of adding a duplicate. Replaced? Mark
`SUPERSEDED by L-XXX`, don't delete.

## L-001 2026-07-10 tags: dispatch|cost-cap|hooks hits: 1
Context: eval-5 subagent (spawned sonnet) was killed by a usage limit and
resumed via SendMessage; transcript showed cache_miss_reason model_changed
(claude-sonnet-5 -> claude-fable-5) — resume inherits the MAIN session model.
Pitfall: model_cap_guard.py cannot intercept the resume path. Verified vs
official hooks docs 2026-07-10: PreToolUse fires on SendMessage but the
payload ({to, summary, message}) has no model/resume info; SubagentStart has
no model field and cannot block; no AgentResume event exists.
Fix: rules-side mitigation folded into `ops/environment.md` (Enforcement,
known gap 2): prefer re-spawning a fresh capped agent over SendMessage-resume
for cost-capped work; disclose to the user if a resume is unavoidable. Hook
header documents the hole. Re-check when the hooks API adds resume events.

## L-002 2026-07-12 tags: verify|docs|design|evidence hits: 1
Context: Prism `docs/PSM_REMEDIATION_v1.0.md` (self-titled v1.1) was authored
as the "sole build basis"; an external review (Codex GPT5.6, 8 findings) was
re-audited in-session — all substantially confirmed (one sub-point unfair:
the doc could not cite its own commit hash; the real miss was phase-log).
Pitfall: four failure modes, not one —
(1) Delta-doc economy: normative content delegated via "沿用" to an ARCHIVED
base while claiming sole-basis status; decision gates D-1..D-10 never inlined,
yet their suggested (unapproved) values entered milestone plans as if decided.
(2) Append-only version bump without a consistency pass: filename/title drift,
stale present-tense status lines, new §10.3 items missing from the §3
milestone list they cite, phase-log never updated.
(3) Claim strength > evidence strength: "complete / no gaps / sole basis /
premise refuted" declared on one-pass-survey evidence.
(4) Semantic compression: a two-proposition finding (current machine dead vs
cross-machine not reproducible) "refuted" in one sentence, silently inverting
the surviving proposition.
Additional trigger miss: user explicitly asked for a PSM-grade remediation
plan but product-design-thinking did not fire (remediation of an existing
product read as "implementing an existing spec"), so the doc bypassed the
skill's build-ready bar entirely.
Fix (folded in): (3)+(4) → `30-judgment.md` R2 claim-calibration corollary;
(1)+(2) → product-design-thinking sole-source contract rules
(`skills/product-design-thinking/references/document-ladder.md` §4);
trigger miss → skill description + `skill-trigger-dict.md` widened to
PSM-grade remediation/re-planning. Finding 8 (market claims without
source/date) was already covered by R5's "cite or label unverified" — that
was a violation of an existing rule, not a rule gap.

## L-003 2026-07-12 tags: interop|cross-platform|skills-sync|env hits: 1
Context: `~/.agents/skills/` and `~/.codex/skills/` hold full raw copies of
`~/.claude/skills/` (synced 2026-07-11) so codex can use them. On 2026-07-12
codex, on user instruction, hand-edited its copy of workflow-checkpoint
(stripped Claude-only /compact flow; SHA-256-verified backups kept). Earlier,
a stale 07-08 copy in `.agents` caused an external AI review to file 12
findings against an outdated skill version — 8 of 12 were invalid
(update-plan v2 §0.1).
Pitfall: raw skill copies across agent homes violate the interop principle
("never copy raw skill files; curate/compile instead") and create two failure
modes: (a) staleness — external reviewers/agents read outdated copies and
produce wrong findings; (b) silent drift — target-side adaptations (e.g.
/compact removal) never flow back and are overwritten by the next naive
re-sync.
Fix: copies declared one-way build artifacts. `README-PROVENANCE.md` placed
in both `~/.agents/skills/` and `~/.codex/skills/` (canonical source, sync
date, adaptation log; hand-edits must be logged there and re-applied on
re-sync). Durable rule: before reviewing/planning against any skill file,
confirm the path is the canonical `~/.claude/skills/` tree; before re-syncing,
read the adaptation log and re-apply platform patches. Long-term option
(user-owned decision, not yet taken): extend interop.py with a skills-compile
profile per skill-share-packaging Mode A.

## L-004 2026-07-12 tags: rules-editing|dict-sync|config-change|docs hits: 1
Context: mattpocock/skills fold-in extended `60-bootstrap.md`'s scope (ticket
slicing + domain glossary). The SAME changeset introduced the dict-sync rule
(40-maintenance §2 corollary) and dutifully updated `rules-usage-dict.md` —
yet still missed `OPS.md` routing table line 56, the PRIMARY router whose
breakage is the defined ghost-rule failure mode (§4.1). Caught only by the
config-self-audit red-team grep, not by authoring discipline.
Pitfall: "update the dicts" was executed as "update the files named dict" —
but the index surface of a rule file is EVERY place that routes to it (OPS.md
routing table, rules-usage-dict, skill-trigger-dict, global CLAUDE.md
pointers). Enumerating index files from memory misses the ones not named
"dict"; the very session that writes a sync rule can violate it in the same
commit.
Fix: when a rule file's scope/responsibilities change, grep the config tree
for references TO that file (`grep -r "60-bootstrap" ~/.claude` style) and
update every routing line in the same commit — enumerate by search, not by
recall. Folded in: 40-maintenance §2 corollary wording now names OPS.md's
routing table explicitly as an index file.

## L-005 2026-07-30 tags: handoff|carried-claims|verification|docs hits: 2
Context: Prism UAT-R3.5. Two separate defects, one shape. (a) 「batch-1 的未通過
項尚未在真機複驗」 was true when written, became false when the author ran batch
2, and survived THREE handoff documents afterwards. (b) 「ResearchGate 那一筆會
繼續算失敗，這是對的」 was copied from the R3 record into the batch-3 UAT sheet
and shipped to the author as an instruction; their real-machine run refuted it
in one step.
Pitfall: a claim copied from the previous round's document READS like an
established fact, because it is written in the same authoritative voice as the
facts around it. Nothing distinguishes "I verified this today" from "the last
document said this". Prose does not decay loudly -- and the receiving session
has no way to tell which sentences are load-bearing measurements and which are
inherited assertions.
Fix: (1) when carrying a claim forward into a new document, either re-derive it
from source in that session or mark it INHERITED with the round it came from --
never restate it flat. (2) For claims a build can check, make the build check
them: Prism's DRIFT-01 rule (`check_architecture.py::carried-design-anchor`)
asserts both that every file owing a deferred design carries its anchor and
that the referenced doc section still exists, so deleting or renumbering the
design goes red. Prose decays because nothing fails when it does; the durable
fix is to make something fail.

## L-006 2026-07-31 tags: skill-design|review-methodology|checklist|scope-gating hits: 1
Context: FSM/state-machine verification and cross-boundary contract-drift
lenses added to the deep-checklist skills (commits afb0c28, 19b00df).
Pitfall: checklist skills naturally enumerate only code-visible defects.
Defect classes that live in DESIGN SEMANTICS (state machines, mirrored
FE/BE contracts, twin-implemented rules, doc claims) have no grep target,
and both naive ways to add them fail: an always-on checklist section taxes
every review with irrelevant work, and duplicating the topic into both the
quality skill and the security skill creates rule drift between them.
Fix (pattern, folded into code-review-deep-checklist Mode A §10/§11 +
Mode B lenses, security-deep-checklist Mode A §9):
(1) reconstruct-and-compare — rebuild the intended model from design
semantics as a REPORT ARTIFACT (transition table, contract/twin inventory),
then check code against it; the artifact is what findings anchor to and
what re-reviews diff against.
(2) every such section carries an explicit trigger gate (stateful units /
boundary contracts only) and records skips in coverage — depth is capped
(top 1–3 units), not open-ended.
(3) single-owner placement: quality lens in code-review, attacker
projection in security — and BEFORE adding to the second skill, check
whether its projection is ALREADY covered (round 2: security intentionally
unchanged; client-only validation, hidden≠protected, enforcement desync
were already its §1/§4/§5/§9). Cross-skill traffic stays
discovery-candidate only. Same test for adjacent skills: doc-drift
DETECTION stayed in review; doc rewriting/backlog handed to
engineering:documentation / engineering:tech-debt.

## L-007 2026-07-31 tags: rules-editing|structural-edit|verify hits: 1
Context: same changeset — inserting section 10 into single-review.md.
Pitfall: a misplaced Edit insert followed by a PARTIAL revert left a
duplicated half-section (two "## 10" headers, one truncated). The author
pass did not catch it; only config-self-audit's section-header listing did.
Insert-then-revert sequences on numbered checklist files corrupt structure
silently — each individual edit "succeeded".
Fix: after any structural edit to a sectioned rules file, scan headers
(`Select-String '^## '`) and verify uniqueness + order BEFORE commit;
prefer append-at-end or a single scripted move over incremental
insert+revert. This is also the standing reason config-self-audit runs
after every skill edit — the gate worked as designed.

## L-008 2026-07-31 tags: rules-editing|naming|scale-labels|ux hits: 1
Context: the ops-relaxation scale (05-authority §2). The system's own user
read "L2" as a PERMISSION/strictness level ("權限L2") and later asked why
"L0 is strictest but the OPS layer seems optional" — conflating the scale
direction with the precedence order. Sweep also found "(L2)/(L3)" reused in
70-evolution.md §4 for a different scale (build-vs-adopt check layers).
Pitfall: two distinct defects with one root. (a) A bare scale label carries
no direction; readers fill it with the dominant industry convention
(ASVS/SIL: higher = stricter), which here is inverted — the designer's own
misreading is the proof. (b) Label famines: reusing "L2" for a second scale
in the same rule tree makes grep and recall collide. Definitions live in one
file, but labels travel through every other file WITHOUT their definitions.
Fix (folded in): scale-label qualifier rule in 40-maintenance §3 (qualify at
every point of use outside the defining file; never reuse a label family);
direction + precedence-orthogonality paragraphs added to 05-authority §2;
glosses added at the gate ask sites (global CLAUDE.md, 60-bootstrap §A);
70-evolution renamed to "(layer 2)/(layer 3)".

---
## Archived (folded into another file, or retired)
(none yet)
