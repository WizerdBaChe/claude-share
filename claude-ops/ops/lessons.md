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
Evidence: session <id> | digest <memory-archive/digests/<card>.md> |
          locator <turn no. / tool_use_id / quoted command> | captured <YYYY-MM-DD>
```
**Recurrence check — mandatory before writing any new entry.** Grep this file
for the new entry's MECHANISM, not its topic (the second occurrence rarely
shares vocabulary with the first). Recurs? Bump the existing `hits:` and add a
one-line `Recurrence:` pointer there — instead of a duplicate entry, or
alongside a new entry when the new one also carries genuinely new failure
classes. A second hit filed as a fresh entry leaves the ledger reading like two
unrelated one-off accidents, which is exactly how a broken fix stays invisible.
`hits:` is the ONLY instrument of global CLAUDE.md's "same symptom reported
unfixed a 2nd time" rule and of `40-maintenance.md` §4.4; nobody increments it,
neither rule can ever fire. A climbing `hits:` under an unchanged `Fix:` is this
system's own evidence that the fix does not work. Every entry carries the field
— `hits: 1` on the day it is written. Replaced? Mark `SUPERSEDED by L-XXX`,
don't delete.

**Evidence line** (required for entries written from 2026-08-11 on; older
entries are NOT backfilled — same precedent as the audit-entry-schema).
`session` alone locates a conversation, not a fact; `locator` is what lets the
next reader re-derive the judgement instead of re-litigating it. Use `digest`
when the raw transcript may age out of a readable format, and write
"unrecorded" rather than inventing an id — a fabricated pointer is worse than
an absent one. Rationale and the wider trace-linking rule: `70-evolution.md` §2.

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

## L-005 2026-07-30 tags: handoff|carried-claims|verification|docs|registry|volatile-facts hits: 3
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
Recurrence (hit 3, 2026-08-15, `interop/MIGRATION-MAP.md` target registry): the
codex and Antigravity rows were verified 2026-07-10 and never re-checked. On
2026-08-11 a note was added justifying keeping them — "the path + profile +
cross-tool caveat are verified facts worth keeping if this ever comes back" —
which restated the July verification flat, in the present tense, one screen
below a heading that says these locations are volatile facts requiring
re-verification. By 2026-08-13 the Antigravity application was uninstalled, so
the row was unverifiable in principle, and the note still read as fact. Same
shape as (b) above: an inherited assertion in the same authoritative voice as
the measured ones. Fixed by the durable route, not by re-wording — both rows
were REMOVED (`archive/2026-08-15-interop-targets-removed/`), so re-adding a
target now has to go through the README checklist step that re-derives the
paths from the platform's current docs. Registry rows are the high-risk
carrier: a table reads as a fact sheet even when its cells are quotations.

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

## L-008 2026-07-31 tags: rules-editing|naming|scale-labels|ux|project-artifacts|uat hits: 3
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

Recurrence 2 (2026-08-12, environment sweep): the corollary did not hold. Live
count `Mode A` x54 / `B` x48 / `C` x20 across SEVEN skills with unrelated
meanings; `Tier` carries FIVE senses, two of which differ only by a hyphen —
`Tier-2` (depth-triage, 30-judgment R8) vs `Tier 2` (research stage,
scientific-research-guide). Root cause found: the corollary lived in §3's
Scale-label bullet, i.e. inside TRIM discipline, which fires when something is
over cap — but a label is minted during AUTHORING, when nothing is over cap.
The rule could not fire at the moment it was needed. Same shape as the
05-authority §2 relaxation gate (rule correct, invisible at the decision
point).

Recurrence 3 (2026-08-12, user-reported, PROJECT level — a third axis the rule
never covered): within one project, an old checklist numbered 1-14 (bare
ordinals, scoped only by "PSM §17") coexisted with a new round numbered R0-R7
(items R5-1..R5-15). "the 5th item" resolved to two different tests, and both
readings were legitimate, so the conversation ran to completion on the wrong
artifact. Worse than recurrences 1-2: those produce visibly odd results, this
one silently validates the wrong thing. Three distinct defects — bare ordinals
with no generation prefix; the same digit holding different RANKS (item vs
round); filenames not carrying the generation.
Fix (folded in, 2026-08-12): corollary MOVED from §3 Scale-label to §3 Birth
budgets (the authoring decision point) with a back-pointer; NEW root
`LABEL-REGISTRY.md` as the one definition table, keyed on the collision axis —
owner-file for environment labels, generation for project lists; 60-bootstrap
§E widened so list/round IDs are glossary terms and inherit `[superseded:]`.
Governing principle recorded there: a label must carry enough qualifier to
resolve its referent at EVERY point it is cited.

## L-009 2026-08-05 tags: env|browser-pane|screenshot|verify|diagnosis hits: 1
Context: ~1 month of intermittent `computer{action:"screenshot"}` timeouts in
the in-app Browser pane, repeatedly misdiagnosed as permission/sandbox and
"fixed" by opening more permissions. Actual state: `document.visibilityState
=== "hidden"` (window visible but fully occluded by an elevated maximized
app), while `read_page`/`get_page_text`/`read_console_messages`/
`javascript_tool` kept working over CDP.
Pitfall (two, one root). (a) The tell was present from the first occurrence
and was read past: ONE tool in a group failed while its siblings stayed
green, and the failure was a TIMEOUT — a denied permission returns a refusal,
not a timeout. Asymmetry inside a tool group rules out permissions before any
investigation starts. (b) The first write-up asserted the mechanism
("Chromium stops compositing") as fact; that is the wording of the TOOL'S OWN
error string, never independently checked, and an OS-level window-pixel grab
fits the same evidence. A quoted error string is the tool author's assertion,
not confirmation — record such claims at correlation level.
Fix (folded in): global CLAUDE.md carries a DETECTION-first rule (probe
`visibilityState` before invoking screenshot) rather than a prohibition the
agent must recall while already misdiagnosing; pictures come from a separate
browser process. Prism CLAUDE.md holds the project command. Over-firing
guard: a timeout with `visibilityState: "visible"` is a different fault.
2026-08-08 amendment: the rules-layer version of this was not enough — see
L-011 on why a CLAUDE.md line cannot carry a mid-measurement rule. Enforcement
moved to `hooks/ui_verify_guard.py` (screenshot branch), which denies the
screenshot until a `visibilityState` probe has run in this session (5 min TTL);
the CLAUDE.md line stays as the explanation the denial points at.
2026-08-16 amendment: the premise under the remedy was wrong. `hidden` is this
machine's STEADY STATE (user's foreground is not commandeerable; a fresh
`preview_start` pane is born hidden — 0×0, rAF stalled, measured — and steals
no focus), so "restore visibility and retry" was never an available remedy;
the pane screenshot timeout measures 5s today, zero pixels, while headless
delivers a PNG in 1.4–1.5s. Pixels therefore route OUT-OF-PROCESS BY DEFAULT;
the probe's remaining job is the discriminator (`visible` + timeout = a
different fault). Premise: `environment.md` "Browser pane"; recipes:
`ops/references/browser-pane-pixel-route.md`. Not a recurrence — no new
failure event; `hits:` unchanged.

## L-010 2026-08-08 tags: env|browser-pane|verify|ui-testing|flaky|css hits: 1
Context: browser-pane UI verification — hover/focus a control, then read
`getComputedStyle` to check the rendered value against a design token.
Pitfall: `getComputedStyle()` during a CSS transition returns the INTERPOLATED
mid-flight value (CSSOM resolved value), not the target, and the MCP round-trip
latency is non-deterministic. So the failure mode is FLAKY, not stably wrong —
the same code passes and fails across runs, which sends the reader to debug
correct code. Compounding: the obvious fallback (look at a screenshot) is
exactly what L-009 takes away, so a round of verification can end with no
trustworthy output at all. Measured control (an out-of-process settle-then-
measure helper, 2026-08-08): on a 5s transition, hover-then-measure never reaches
the target colour; finishing animations first reaches it on 3/3 runs.
Fix (folded in): (1) settle before measuring —
`el.getAnimations({subtree:true}).forEach(a => a.finish())` is SYNCHRONOUS, so
it needs no promise and no sleep; infinite keyframes cannot finish() and take
an injected `transition:none;animation-duration:0s` stylesheet instead.
(2) prefer asserting STATE (`data-state`, `aria-expanded`, class flips) over
asserting a rendered pixel value — state assertions are timing-free.
(3) enforcement is `hooks/ui_verify_guard.py`, which denies a `javascript_tool`
call containing `getComputedStyle` with no settle token in the same call.
(4) do all of this from an out-of-process tool. The source environment's is a
private asset and is not shipped; `npx playwright screenshot` plus the settle
call above is the portable equivalent.

## L-011 2026-08-08 tags: rules-design|enforcement|hooks|layering|omission|harness hits: 2
Context: deciding where to put the L-009/L-010 UI-verification rules so they
actually fire. Raised by the user as a design question, not discovered by a
failure: "OPS 層級偏低且 lesson 的資料更低,CLAUDE 的那個路由真的能保證調到嗎".
Pitfall: the three rule layers have very different firing guarantees, and
writing a rule into the wrong one produces a rule that reads as durable and
is in fact dead. `ops/lessons.md` is NOT in context — it fires only when
something greps it, i.e. essentially never on its own. `ops/*` fires only when
CLAUDE.md's project-operations clause routes there, which a UI-verification
task never triggers, because it is not a multi-step project task. Global
CLAUDE.md IS always in context, but it fires only if the trigger words match
what the agent is about to do — and that match is unreliable for rules that
must fire MID-MEASUREMENT, when the agent is already confident and reading
past reminders (L-009 recurred for ~1 month under exactly such a line).
Fix: the layer must be chosen by TRIGGER SHAPE, not by importance.
- Trigger is a named tool call with inspectable input → PreToolUse hook. The
  harness executes it; the model cannot skip it. Deny beats warn: a warning is
  text the agent may skim, a denial forces the corrected call, and it costs
  exactly one retry.
- Trigger is a task-shaped judgement ("when designing a module layering
  scheme") → global CLAUDE.md conditional rule.
- Trigger is "someone is already investigating this topic" → ops/lessons.md,
  as the detail the shorter layers point AT, never as the enforcement.
Corollary: when a hook carries the enforcement, the CLAUDE.md line stays but
changes job — it becomes the explanation the denial message cites, so the two
must not drift. Both the hook docstring and the CLAUDE.md line name the
lessons entry, so a reader landing from either arrives at the same place.

FOURTH TRIGGER SHAPE — OMISSION (added 2026-08-14, second hit). The three
shapes above are all COMMISSION: something happened — a tool call, a recognised
task shape, a grep. A rule whose violation is "the step never happened"
generates no event at all, so none of the three fire. Worse, the task-shape
layer is least likely to fire at exactly the moment it is needed, because the
model is already confident it can skip the step — the same mechanism that let
L-009 recur for a month. Three paths, each with a precedent already running here:
- **P1 gate the substitute.** An omission is almost always accompanied by a
  substitute commission: not dispatching means reading the files yourself.
  Gate the substitute, not the absence. → PreToolUse on the substitute's tools.
- **P2 make the absence greppable.** Require a literal marker at the point of
  use; a MISSING marker is then a defect a periodic sweep can enumerate.
  Precedents: the `PROVISIONAL` token (`rule-registry.md` header, sweep check
  11) and the `hits:` field (sweep check 5).
- **P3 end-of-action gate.** Check, at the event that ENDS the action, whether
  what should be there is there. Precedent: `delivery_gate_shadow.py`
  (SubagentStop).
Choosing: P1 when the substitute is a named tool call; P2 when the rule leaves
a durable artifact someone later reads; P3 when the omission is only knowable
once the work is finished.
HARNESS-COMPATIBILITY CONSTRAINT (user ruling 2026-08-14). The harness's own
injected instructions cannot be edited or overridden from this side, so an
omission gate must NARROW WITHIN them, never contradict them. Where the harness
withholds an action pending user authorisation, the gate's job is to SURFACE
THE DECISION to the user — not to take the action. A gate that tells the model
to disobey an injected instruction is mis-designed even when its content is
right: it loses silently at the next harness change, with the original symptom
intact. Where the harness states a default and lists alternatives, choosing a
listed alternative with a stated reason is narrowing; asserting the default is
wrong is not.
COST OF P1/P3: a hook that does not run is itself silent, so every hook added
under this shape ships with a proof-of-life line in `integrity-sweep.md` in the
SAME commit. Case: `browser-nav.jsonl` was asserted in `rule-registry.md` as
"every pane navigation is LOGGED" while the file did not exist (2026-08-14) —
benign (no navigation had occurred since the hook was written) but
indistinguishable from a dead hook without the check.

## L-012 2026-08-11 tags: verify|evidence|claim-calibration|delivery|self-review hits: 2
Context: the harness context-budget work (E1/E4/T-007). Four over-claims in one
task, all caught, none by re-reading the text that contained them.
Pitfall: **proxy promotion** — a proxy is measured, then spoken about in the
voice of the thing it stands for. Same shape every time:
(1) 16 KB of CLAUDE.md → "≈4-5k tokens paid every session", used to rank E1 as
the root-cause fix; the measured startup floor made it ~11% of the cost, an
adherence lever, not a token lever. (2) CLI warns "`Write(...)` ask-rules never
match" → "the 🔴 confirmation gate is broken"; only one component was tested,
never the live `Edit(...)` side. (3) A probe carrying the SAME `paths:` list as
`rules/frontend-layering.md` fired → treated as evidence that file works; the
probe could not have failed on that file's behalf, because it never touched it.
(4) "6 條 Write 規則" recalled from a file read earlier; there were 4.
Why the existing rule (R2 claim-calibration, L-002) did not stop it: it is a
DELIVERY-TIME duty, executed by the author, on the author's own sentences,
while the author is still holding only the proxy. Re-reading one's own claim
re-derives it from the same evidence and it looks true again. A refutability
block written in that state inherits the error instead of catching it.
Detection, all four cases: an action taken for an UNRELATED reason produced an
output that could disagree — running the baseline script, opening settings.json
to edit it, checking an empty log. Where no such action existed, the claim
survived until the user's reviewer demanded measurement.
Fix: (1) **name the substitution in the sentence**, not a hedge — "bytes, not
tokens", "the pattern, not this file", "the Write rules, not the gate". A hedge
word keeps the proxy invisible; naming it hands the reader the thing to attack.
(2) Before writing "X works", ask: *could the evidence I have have come out
differently for the specific artifact I am claiming about?* No → it is not
evidence about that artifact. (3) When the claim is load-bearing for the
requester's decision, build the disagreeing artifact ON PURPOSE instead of
waiting for one to appear incidentally. Companion example under
`30-judgment.md` R2.
Recurrence (2026-08-12, hit 2): L-015 (1) is this same mechanism — symptom
measured, identity asserted — surviving because it sat in DESIGN-RATIONALE
prose while fix (1) had been applied only to the evidence prose of the same
document. Nobody declared that scope; it was set by feel. The scope was made
explicit in `30-judgment.md` R2's claim-calibration corollary rather than by
rewriting this entry, because the mechanism recorded here was correct — its
boundary was missing. Fix (3) of this entry is now also a close-out step
(`50-coach.md` C11 question 4), since it is the only one of the three with any
recorded catch: 4/4 here, 3/3 in L-015, versus 0 for the phrasing fixes (1)(2).
Evidence: session (a local transcript) | digest unrecorded |
locator: instance (1) `tools/context-budget/startup_baseline.py` first run vs
the preceding turn's estimate table; instance (3) `telemetry/rule-loads.jsonl`
empty after reading a `.tsx` while `_probe-copy.md` matched | captured 2026-08-11

## L-013 2026-08-12 tags: env|browser-pane|crash|third-party-content|forensics|diagnosis hits: 1
Context: the desktop app's window vanished twice around midnight 2026-08-11/12
while the process tree stayed alive. Windows recorded no Application Error, Hang
or display event; `main.log` had two identical `GPU process gone { reason:
'crashed', exitCode: 101457950 }` lines and then went silent for 8m26s.
Pitfall: the three earlier browser-pane entries (L-009, L-010, L-011) all treat
the pane as a MEASUREMENT INSTRUMENT whose worst failure is that you cannot
trust what you read out of it. The pane is also a live execution surface for
third-party content, and in that direction the failure is not local: a page it
loads can kill the Electron GPU child, Electron does not relaunch it, the window
stops compositing, the main process wedges, and the in-flight turn of every
session in the app is lost. Three concrete holes, in ascending order of how much
of it was ours to prevent:
(a) No scope rule said third-party pages are a different risk class from
localhost / own-build previews, so a bot-challenged download-aggregator page
went into the pane like any dev server.
(b) No forensic record. `main.log` logs a preview's `serverId` and `tabId` and
NEVER the URL - so "saveclip never appears in main.log" reads like evidence of
lost logging and is in fact expected behaviour. The trigger was recoverable only
because the CLI transcript happened to still be readable.
(c) No repeat suppression: after the restart the agent re-issued the IDENTICAL
`preview_start` on the same URL and crashed the app a second time within 40s of
launch. One crash became two by retry.
Evidence for the trigger, kept separate from the mechanism, because they are
different strength: TRIGGER - both crashes 3-4s after `preview_start
https://saveclip.app/zh-tw`, against ~180 other pane opens in the same
2026-08-02..12 log that never crashed (2/2 with a ~180:0 base rate; an Instagram
session in the same pane nine minutes earlier was fine). MECHANISM CANDIDATE -
the page is behind Cloudflare and its challenge script
(`/cdn-cgi/challenge-platform/h/g/orchestrate/chl_page/v1`) calls
`navigator.gpu.requestAdapter()` on first load, measured out-of-process with
headless Playwright on this machine; zero canvas/WebGL contexts. That makes
WebGPU adapter init a candidate, not a proven cause - proving it would mean
crashing the app again on purpose. Upstream `anthropics/claude-code#81698`
reports the identical exit code on the same OS build and an NVIDIA laptop GPU
and points at WebGL/WebGPU; `#81836` describes the same wedged-main-process
aftermath. Both are user reports, not maintainer confirmation.
Two decoys ruled out, recorded so they are not re-investigated: `LiveKernelEvent
1d4` is NOT a display-driver signal here - the WER 1001 attachment names
`C:\Windows\LiveKernelReports\UcmUcsiCx.sys\...` (USB-C connector driver), every
report since 08-09 attaches the SAME 08-04 22:00 dump, and none of its
timestamps coincide with either GPU crash. And the NVIDIA driver was already
32.0.16.1088 (610.88, 2026-07-22), newer than the 610.47 in the matching
upstream report, so "update the GPU driver" is not the lever. Not memory either:
14.4 GB free, GPU child at 127 MB, 15 minutes before the crash.
Fix: enforcement is `hooks/browser_pane_scope_guard.py` (PreToolUse, matcher
`mcp__(Claude_Browser\|claude-in-chrome)__(navigate\|preview_start)`), which (1)
appends every pane navigation to `telemetry/browser-nav.jsonl`, closing (b)
permanently, and (2) denies a host listed in `hooks/browser-pane-blocklist.json`
when the call targets the IN-APP pane, closing (c). The deny is scoped to
`mcp__Claude_Browser__*` on purpose: `claude-in-chrome` drives a separate Chrome
process and is one of the escapes the denial names, alongside WebFetch and
headless Playwright. Hole (a) is deliberately NOT in global CLAUDE.md yet (user
ruling 2026-08-12): the standing rule of thumb lives here instead - **the in-app
pane is for localhost, your own build, and pages the user wants to see; a
third-party page, especially a download aggregator or anything behind a bot
challenge, goes to WebFetch -> claude-in-chrome -> headless Playwright first;
and a URL that was loaded immediately before a pane or app death is never
retried in the pane.** Promote it to a CLAUDE.md conditional rule if a second
independent incident occurs - which is the exact trigger shape of the
"same symptom reported unfixed a 2nd time" rule. Hook tested 2026-08-12 against
10 synthetic payloads (deny/allow both branches, subdomain match, lookalike-host
non-match, scheme-less URL, cross-server scoping, `navigate back`, dev-server
`preview_start`, missing blocklist, malformed stdin): 10/10.
Evidence: session (a local transcript) | digest unrecorded |
locator: `%APPDATA%\Claude\logs\main.log` lines 59189/59744 (`GPU process gone`)
vs the session's own local transcript jsonl,
turns at 23:59:26 and 00:08:32 (`preview_start` on the same URL); WebGPU stack
captured out-of-process, Playwright 1.62.1 | captured 2026-08-12

## L-014 2026-08-12 tags: agents|subagent|tools|capability|skills|silent-failure|config hits: 1
Context: rewriting the `agents/*.md` definitions, a `tools:` allowlist was added
to each so that "read-only reviewer" stopped being prose with nothing behind it.
The proposed reviewer list was `Read, Glob, Grep`.
Pitfall: `tools:` is an allowlist, and `Skill` is a tool. That list would have
silently and permanently disabled every skill the agent could otherwise invoke —
the official wording is explicit that omitting `Skill` from `tools`, or listing
it in `disallowedTools`, is the documented way to *prevent* a subagent from
using skills at all. Nothing errors, nothing warns; the agent simply never
routes to a skill again and no one finds out, because a missing skill
invocation looks identical to a task that did not need one.
The general shape: **tightening a capability boundary silently removes
capabilities you were not thinking about.** An allowlist written against one
axis (write access) also cuts every other axis it happens to intersect
(skills, search, MCP). Two other near-misses in the same edit: dropping `Bash`
removes the ability to run `git diff` at all, and `permissionMode: dontAsk`
auto-denies anything outside `settings.json`'s allowlist — which would have
paralysed the implementer agents, since `Edit` is not in it.
Rule: after writing any `tools:` list, enumerate what it REMOVES, not what it
keeps, and check that list against (a) skill invocation, (b) the agent's own
verification path, (c) the session permission allowlist. Read-only ≠ three
tools; read-only = the write tools are absent and everything else survives.
Detection: `grep -L 'Skill' agents/*.md` returns any definition that cannot
reach a skill. Should be empty unless a definition deliberately forbids them.
Evidence: `code.claude.com/docs/en/sub-agents` — "To prevent a subagent from
invoking skills entirely, omit `Skill` from the `tools` list or add it to
`disallowedTools`"; the background-subagent tool filter retains `Skill`.
Caught in review before dispatch, not in production | captured 2026-08-12

## L-015 2026-08-12 tags: verify|claim-calibration|design-docs|self-review|scope-gating|research hits: 1
Context: Prism R9. A pipeline redesign (`DESIGN-06`) was written, then self-audited
a few hours later against the artifacts it superseded. Six findings; three are the
instructive ones and they are NOT one failure class.
Pitfall, three distinct shapes:
(1) **Claim calibration silently scoped to the evidence sections.** The measurement
prose was disciplined — probe numbers bounded, P1-P4 stated with falsifiers, claim
ceilings explicit, one of them volunteering "does not support P0 beating P1/P2". The
DESIGN sections of the same document were never subjected to the same question, and
nobody decided they should be exempt. §5.1 claimed a table-cell defect and
evidence-span anchoring were "the same problem"; they share a symptom (several
candidate locations) and need different evidence (bbox geometry vs textual context).
That is L-012 proxy promotion exactly — symptom measured, identity asserted — but it
survived because it sat in a justification sentence, not a findings sentence.
(2) **Deferral without blast radius.** `DERIVED` bbox acquisition was deferred to a
future design as a generic future item. Two queries (q004, q010) are *entirely*
figure-derived, so the deferral silently left them dead. The deferral was never asked
"which existing data depends on this?"
(3) **Two known facts never multiplied.** The truth set has 4 `absent` queries;
ROADMAP-02 §2 requires 12 real absences to calibrate the three-state policy. Both
numbers were quoted BY ME in this same session — the composition in the first status
report, the requirement while reading the roadmap. A fact and its own acceptance
criterion, both in hand, never joined.
Why L-012 did not stop it: L-012's fixes act on what you SAY. Only (1) is a claim at
all. (2) and (3) are checks never run — omission, not overstatement — and no amount of
hedging or naming-the-substitution reaches them. For (1) specifically, L-012 was
applied, but to one class of sentence in the document and not the other.
Detection, all three: the same mechanism, and it is L-012's own fix (3) — run a
computation for an UNRELATED reason and let its output disagree. A query-type
breakdown, executed to fix a different finding, emitted (2) and (3) as byproducts.
(1) came from an adversarial question sourced OUTSIDE the claim ("would the fix for one
fix the other?"), not from re-reading; re-reading re-derives the claim from the same
evidence and it looks true again.
Fix: (1) claim calibration covers design-rationale prose, not just evidence prose —
any sentence asserting two things are the same, or that X follows from Y, gets the
"could my evidence have come out differently?" test. (2) when deferring a capability,
enumerate what currently depends on it before writing the deferral; a deferral with no
blast-radius line is incomplete. (3) when a document states a quantity and another
states its acceptance threshold, join them at that moment — the comparison is free
while both are on screen and expensive once either has scrolled away.
Caveat worth carrying: six findings in one pass over a document written hours earlier
means it was written faster than it was checked. A high find-rate predicts more
remaining, not that the sweep finished. F-1 (a headline figure quoted four or five
times before being taken apart) is the evidence for that.
Evidence: session (a local transcript) | digest unrecorded |
locator: `Prism/research-r9/AUDIT-04-design06-self-audit-and-legacy-fit-2026-08-12.md`
F-1/F-4/F-5/F-6; the byproduct run is the query-type breakdown behind F-2 | captured 2026-08-12

## L-016 2026-08-15 tags: verify|hooks|checks|acceptance-eval|config|silent-failure|self-audit hits: 1
Context: interop-layer maintenance pass. Three independent checks were examined
in one day and all three turned out to be incapable of failing. None of them
was broken in a way anything reports.
Pitfall: **a check that cannot fail is indistinguishable from a check that
passes**, and the three ways it happens do not look alike.
(1) *The predicate is satisfied by the wrong thing.* `ops_health_nudge.py`
check 11 tested `"ops-relaxation:" not in text`. The global CLAUDE.md contains
that token in PROSE ("offer to record `ops-relaxation:` in project CLAUDE.md"),
so every project CLAUDE.md derived from it passed vacuously. A source-wide grep
that day found zero real declarations anywhere — the check had never once fired
correctly since birth, and its silence had been read as health.
(2) *Nothing invokes it.* `interop.py status` was correct: it printed
`[missing] opencode` and exited 1 from 2026-08-11. No hook, no CI, no habit ran
it, so the target sat undeployed for four days. A report nobody runs is not a
check; exit codes only matter to a caller.
(3) *Its subject was retired.* `acceptance-evals.md` eval 8 required the agent
to read `interop-refs/design-protocol.md`, a directory retired 2026-08-11 that
exists at no target. It could neither PASS nor FAIL — coverage on paper.
Why each survived: all three FAILED SILENT and silence is the healthy signal
for a nudge, a status report and an unrun eval alike. Nothing in the artifacts
distinguishes "nothing wrong" from "asked nothing".
Fix, three parts, each cheap:
(a) **Test the check against a positive case, not just the corpus.** Every one
of these dies to one synthetic input that SHOULD trip it. That is what
`tools/ops-health-test/test_ops_health_nudge.py` is for (21 cases); the case
named "PROSE MENTION ONLY -> must fire" is the whole lesson in one line. One
other case there caught a first-draft bug the same way — a machine with no
`interop/` got a permanent unfixable nudge.
(b) **A mention is not a declaration — require the VALUE, not the key.** Any
check keyed on a token appearing in a document is one prose sentence away from
vacuous. Match the shape that carries meaning (`ops-relaxation: L1`), anchored
to line start.
(c) **A report needs a caller, and the caller must be cheap and automatic.**
Check 12 is that caller for `status` — a stat()-only session-start screen whose
only remedy is "run `status`". Note the restraint: it routes to the authority
rather than re-implementing it, because mtime is not the commit comparison
`status` makes, so a false positive costs one command instead of a wrong build.
Detection when you cannot write a test: ask of any check, "what input would
make this print something?" If the answer takes real thought, or names a file
that no longer exists, it is already broken.
Evidence: session 2026-08-15 interop maintenance | locator commits 9480f39
(check 11), 8fab5cb (check 12 + suite), 9521c20 (eval 8); the grep is
`grep -rn "ops-relaxation:" ~/.claude` on that date | captured 2026-08-15

## L-017 2026-08-16 tags: rules-design|checklists|security|invariants|verify|remediation hits: 1
Context: NTUMail2TG Phase 3 -> 4. A full A+B+C security audit wrote EP-1 as "`D:\`
must not grant `BUILTIN\Users` FullControl". The user declined: it is a drive root,
and locking it would cut off the local AI sandbox accounts that legitimately work
there. The prerequisite then sat NOT SATISFIED across two phases while the risk it
existed to prevent had already been eliminated by other means — the binary was moved
to `%LOCALAPPDATA%\Programs\MailBridge`, ACL verified owner-only.
Pitfall: the prerequisite named a LOCATION, not a PROPERTY. What the invariant behind
it (SI-4) actually requires is "the directory autostart executes from is not writable
by broad principals", and that was fully satisfied — but the checklist could not see
it, because the checklist was asking about a drive. Two consequences, the second worse
than the first: (a) the report claimed a HIGH finding was live when its attack path had
already been cut; (b) a permanently-red item teaches the user that this checklist can
be ignored, which spends the credibility of every OTHER item on it.
Why it survives review: an instruction-shaped control reads as more concrete and more
actionable than a property-shaped one. That concreteness IS the failure mode — it names
one solution and cannot recognise any other.
Detection: for each red item on a standing checklist, ask "what would a DIFFERENT valid
fix look like, and would this item notice it?" An item satisfiable exactly one way is
written against the wrong object. Second signal, cheaper: an item the user has declined
twice is a specification problem, not a compliance problem.
Fix, three parts: (a) write the invariant as a property of the asset it protects and
make the checklist item a test of that property. (b) When the user declines a
remediation, convert it into an accepted risk carrying its compensating control and
revisit conditions — never leave it open, so every line reads either "satisfied" or
"known and decided". (c) Prefer a compensating control that cannot decay: the
leaf-directory ACL option was declined here because `publish.ps1` deletes and recreates
that directory, so the hardening would silently revert on the next publish. A control
that rots unnoticed is worse than none; detection (git) was chosen over prevention.
Evidence: session (a local transcript) | locator:
`NTUMail2TG/SECURITY-POLICY.md` EP-1 + AR-5;
`~/.claude/references/NTUMail2TG-decisions.md` P-004 / D-010 | captured 2026-08-16

## L-018 2026-08-16 tags: testing|harness|isolation|forensics|logging|silent-failure hits: 1
Context: NTUMail2TG. The offline harness deliberately drives the REAL engine with a fake
mail source and a fake Telegram sink — the property that makes it worth having. `Logger`
wrote to a hard-coded path. Every test run therefore appended synthetic deliveries and
read failures to the user's operational `bridge.log`, `[security]` channel included,
indistinguishable from real events after the fact.
Pitfall: the fakes covered the two things that FELT external — the network and the
mailbox. The log is the app's only evidence of what happened, and it stayed pointed at
production because the question asked was "what does this code READ?" A test double gets
built at the boundary already under consideration, and by default that is the input side.
Why it survives review: nothing fails. Tests pass, the log grows, and the contamination
is discoverable only by reading the log with the question already in mind. The damage is
retroactive and silent — it lands on records that already existed.
Detection: enumerate what the code under test WRITES — log files, state files, registry
values, caches, outbound notifications, telemetry — and require each one to be redirected
or asserted-unchanged. Cheap positive check: assert the production artifact's byte length
is identical across a full harness run (4653 -> 4653 here).
Fix: `Logger.RedirectTo`, one-way and single-use. Single-use is the security-relevant
half — a log path that can be swapped at will is itself a way to make records disappear,
so the redirect must be impossible to re-target once logging has begun. The harness
redirects before anything can log, and a test asserts a second call throws.
Evidence: session (a local transcript) | locator:
`NTUMail2TG/MailBridge/Core/Logger.cs`, `MailBridge.Tests/Program.cs`;
`~/.claude/references/NTUMail2TG-decisions.md` P-005 | captured 2026-08-16

## L-019 2026-08-16 tags: verify|acceptance-eval|parsing|subagent-dispatch|interop|gate-design|silent-failure hits: 4
Context: acceptance gates over model output — a JSON extractor, an evidence-anchor
checker, a structure checker, an adversarial verifier. Four separate gates, built
weeks apart, three of them by me and one by an independent peer team.
Pitfall: a gate ruling on a question it has no power to decide, and the ruling
always lands as REJECT. Four instances in one night:
  (1) transport failure (unparseable reply, dead dispatch) recorded as "the claim
      was refuted" — two independently-proven-true findings destroyed;
  (2) a UTF-8 BOM from PowerShell's `Out-File -Encoding utf8` recorded as
      STRUCTURE-FAIL on a report whose JSON was perfect;
  (3) a verbatim quote filed under the wrong line number recorded as a fabricated
      anchor, voiding a report that contained a real directory-traversal hole;
  (4) peer team, same night, independently: `re.search(r"\{.*\}|\[.*\]", body,
      re.S)` then `json.loads`. Greedy on both branches AND ordered, so an array
      payload preceded by any prose containing `{` is captured from that stray
      brace to the last `}`. They re-scanned 10 archived rejects with a lenient
      reader: 10/10 held valid JSON. Their models had never once refused.
Why it survives review: the gate is CORRECT about the thing it can see (the bytes
did not parse; the line number is wrong) and silently extrapolates to a thing it
cannot see (the content is bad; the model fabricated). Nothing errors. The output
is a confident, plausible negative — and a false negative reads like a finding
("the free tier is unreliable"), which is why it is never questioned.
Detection: for each gate ask "what can this layer actually determine?" A quote
check proves the model READ the file — you cannot copy a line out of a file you
never opened — and proves nothing about whether the claim is TRUE. Then look at
where a failure of the OTHER kind currently lands. If every failure lands on
REJECT, the gate is ruling beyond its authority. Cheap test: feed it a known-TRUE
input, not only a known-false one. A gate that rejects everything scores 100% on
a specificity-only calibration.
Fix: a gate may only rule on what it can determine; for everything else the
correct output is DOWNGRADE AND FORWARD, never veto. Concretely: three-valued
outcomes with the third state named and loud (`survived`/`refuted`/
`inconclusive`, with "INCONCLUSIVE IS NOT REFUTED" printed); `MISALIGNED` +
auto-repaired line number vs `FABRICATED` (quote nowhere in the file), only the
latter fatal; a parser strictly more lenient than the prompt that demanded the
format. Corollary that generalises the four: the RECEIVING side's strictness is
itself a measured variable — grade the same answers with both rulers and the
gap is parser attribution, not model quality (ticket 3: strict 0/5 vs lenient
5/5 on identical answers, chunk size held constant).
Evidence: session (a local transcript) | locator:
`~/.claude/tools/extdispatch/redteam_verify.py` `verdict_of()`/`_find_verdict_object()`,
`score_redteam.py` `check_anchor()`, `test_score_anchor.py` (10/10, incl. the
fabrication guard), `peer_experiments.py` `_balanced_candidates()`;
`reports/2026-08-16-machine-first-verification-scoping.md` §7.5;
`reports/2026-08-16-verification-round-and-peer-tickets.md` | captured 2026-08-16

## L-020 2026-08-16 tags: refactor|duplication|testing|verify|retrospective|dead-code|silent-failure hits: 2
Recurrence 2026-08-16, THIRTY MINUTES after this entry was written, by its
author: the `<status>` block contract (its regex and its required-key tuple) was
written twice -- once in `peer_experiments.grade_dual`, the live grader, and once
in `regrade_dual.grade`, the grader whose output was sent to a peer team. Two
definitions of "what counts as a valid status block", one edit away from the
running experiment and the published figures disagreeing. Caught by the same
sibling scan, on the next run of the same skill. Extracted to
`peer_experiments.status_block_ok()`; re-grading produced byte-identical numbers.
What this adds to the entry: writing the lesson does not raise the felt urgency
of checking for the second copy, because the second copy is created in the same
motion as the first piece of new code -- the duplication is not a later decision
you could have reconsidered, it is the default shape of "I need this here too".
Only a scan catches it, which is why the DETECTION line below is the load-bearing
half of this entry and the fix line is not.
Context: a retrospective's sibling scan on `~/.claude/tools/extdispatch/` — the
step that asks "was any of this written twice?" — run after the milestone had
already shipped, been tested and been merged.
Pitfall: one algorithm existed in THREE places and only two had been fixed. The
same greedy JSON slice (`find("[")` .. `rfind("]")`) was corrected in the layer-5
verifier and again in the experiment harness, while a third copy sat unfixed in
`score_redteam.extract_findings` — the STRUCTURE layer, the first gate every
dispatched report passes through. Confirmed live: a report reading
`Findings (see item [1] below):` followed by a perfectly valid array returned
STRUCTURE-FAIL.
Why it survives review: **two independent fixes of one bug is the mechanism by
which a third copy survives.** Each fix is complete from where it was made, and
each one lowers the felt urgency of looking further — the bug now reads as
"handled". A grep for the SYMPTOM finds nothing, because the two fixed copies no
longer exhibit it.
Second half, worse: `test_parser_rulers.py` imported the experiment harness's
copy while acceptance layer 5 ran the verifier's. **A test that covers a
duplicate reports on code nobody runs**, and it reports green, so the duplication
is actively disguised by the test suite.
Detection: after fixing any MECHANISM-level bug (not a typo), grep the tree for
the mechanism rather than the symptom — the depth-tracking loop, the regex
shape, the sentinel value — and count the call sites. Then check which copy the
tests import. Neither of these is expensive; what makes them not happen is that
the second fix feels like the last one.
Fix: extract to one module the moment a second copy is created, not the third
(`tools/extdispatch/jsonspan.py`), and point the test at the shared symbol
directly rather than at any consumer's re-export. Note that the sibling scan
found this AFTER the code was merged with four green test suites — the
retrospective step is doing work no gate in the pipeline does.
Evidence: session (a local transcript) | locator: commit
`b5062a7`; `~/.claude/tools/extdispatch/jsonspan.py` module docstring;
`outputs/retrospectives/retrospective-extdispatch-2026-08-16.md` Category 2 |
captured 2026-08-16

## L-021 2026-08-16 tags: env|powershell|shell|git|quoting hits: 1
Context: `git commit -m @''...''@` from PowerShell 5.1 with a here-string that
contained embedded double quotes ("what this retrospective CHANGED").
Pitfall: PS 5.1 passes the here-string as ONE PowerShell string, but its native
argument encoder does NOT escape embedded `"` for the child process — the quote
ends the argument mid-message, and git parsed the message tail as pathspecs
(`error: pathspec ''this'' did not match`). The commit silently did not happen
while the rest of the command chain (checkout, merge, branch -d) kept running:
the merge reported "Already up to date" and the branch was deleted un-merged.
Here-strings solve MULTILINE, not EMBEDDED-QUOTE, and the two failure modes are
easy to conflate.
Why it survives review: the here-string advice ("use @''...''@ for multiline
messages") reads as the complete fix, and messages without inner double quotes
work for months before one with a quoted phrase hits.
Detection/prevention: for any native-exe argument that may contain `"` in PS
5.1, write the content to a file and pass the file (`git commit -F <msgfile>`),
or drop the inner double quotes. After any chained git sequence, verify with
`git log --oneline -1` that the commit actually landed before acting on it.

## L-022 2026-08-16 tags: signal-processing|thresholds|ml-depth|imaging|diagnosis hits: 1
Context: 3D Photo Synthesis Engine — cutting depth discontinuities out of an
ML-predicted depth map (Phase 1 edge masking; Phase 2 mesh culling).
Pitfall: hunting a sharp feature in a smoothed signal. ML depth (like any
model/filter output) smears true foreground/background steps into multi-pixel
ramps, so the per-pixel difference stays below any reasonable threshold, and
`percentile(gradient, 95)` always cuts "the steepest 5%" — which in a smoothed
signal is noise, ranked. A full tuning round covered 0.16% of pixels: loose
mis-cuts a sheet, tight cuts nothing.
Why it survives review: every individual threshold value looks defensible, and
each retune produces a visibly different (still wrong) mask, which reads as
progress rather than as a wrong axis.
Fix: change the measured QUANTITY, not the threshold — find a space in which
the outlier is genuinely an outlier. Here: 3D edge length / median ratio
(max/median = 576.9x, clean bimodal histogram) — one cut, view-independent.
Detection: before tuning any threshold, ask whether the sharp feature being
sought can exist in this signal at all; if the signal came through a model or
filter, it usually cannot.
Status: single project, two phases — hypothesis tier. Global candidate H-6
deferred per the R-1 precedent; re-propose on a second project's hit.
Evidence: outputs/retrospectives/
global-rule-candidates-3D-photo-engine-2026-08-16.md H-6 | captured 2026-08-16

---
## Archived (folded into another file, or retired)
(none yet)
