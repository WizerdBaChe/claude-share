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
Recurs? Bump `hits:` instead of adding a duplicate. Replaced? Mark
`SUPERSEDED by L-XXX`, don't delete.

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
Recurrence (hit 3, 2026-08-15, the interop layer's target registry): two target
rows were verified once and never re-checked. Five weeks later a note was added
justifying keeping them — "the path + profile + cross-tool caveat are verified
facts worth keeping if this ever comes back" — which restated the original
verification flat, in the present tense, one screen below a heading saying these
locations are volatile facts requiring re-verification. By then one of the two
applications had been uninstalled, so its row was unverifiable in principle, and
the note still read as fact. Same shape as (b) above: an inherited assertion in
the same authoritative voice as the measured ones. Fixed by the durable route
rather than by re-wording — both rows were REMOVED, so adding a target now has
to go through the checklist step that re-derives the paths from the platform's
current docs. Registry rows are the high-risk carrier: a table reads as a fact
sheet even when its cells are quotations.

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
browser process. Over-firing guard: a timeout with `visibilityState: "visible"`
is a different fault.
2026-08-08 amendment: the rules-layer version of this was not enough — see
L-011 on why a CLAUDE.md line cannot carry a mid-measurement rule. Enforcement
moved to a PreToolUse hook (screenshot branch), which denies the screenshot
until a `visibilityState` probe has run in this session (short TTL); the
CLAUDE.md line stays as the explanation the denial points at.

## L-010 2026-08-08 tags: env|browser-pane|verify|ui-testing|flaky|css hits: 1
Context: browser-pane UI verification — hover/focus a control, then read
`getComputedStyle` to check the rendered value against a design token.
Pitfall: `getComputedStyle()` during a CSS transition returns the INTERPOLATED
mid-flight value (CSSOM resolved value), not the target, and tool round-trip
latency is non-deterministic. So the failure mode is FLAKY, not stably wrong —
the same code passes and fails across runs, which sends the reader to debug
correct code. Compounding: the obvious fallback (look at a screenshot) is
exactly what L-009 takes away, so a round of verification can end with no
trustworthy output at all. Measured control (a headless-probe verify script):
on a 5s transition, hover-then-measure never reaches the target colour;
finishing animations first reaches it on 3/3 runs.
Fix (folded in): (1) settle before measuring —
`el.getAnimations({subtree:true}).forEach(a => a.finish())` is SYNCHRONOUS, so
it needs no promise and no sleep; infinite keyframes cannot finish() and take
an injected `transition:none;animation-duration:0s` stylesheet instead.
(2) prefer asserting STATE (`data-state`, `aria-expanded`, class flips) over
asserting a rendered pixel value — state assertions are timing-free.
(3) enforcement is a PreToolUse hook that denies a script-execution call
containing `getComputedStyle` with no settle token in the same call.
(4) the out-of-process tool that does all of this: a headless-browser probe
(utility/node) implementing the same settle-then-measure logic.

## L-011 2026-08-08 tags: rules-design|enforcement|hooks|layering hits: 1
Context: deciding where to put the L-009/L-010 UI-verification rules so they
actually fire. Raised by the user as a design question, not discovered by a
failure: whether the ops layer and lessons.md sit low enough in priority that
routing through global CLAUDE.md could not reliably reach them.
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

## L-012 2026-08-11 tags: verify|evidence|claim-calibration|delivery|self-review hits: 1
Context: a context-budget/instrumentation task with several sub-deliverables
tracked across a session. Four over-claims in one task, all caught, none by
re-reading the text that contained them.
Pitfall: **proxy promotion** — a proxy is measured, then spoken about in the
voice of the thing it stands for. Same shape every time: (1) a static byte
estimate for an always-loaded instructions file was used to rank a trim as
the root-cause fix; a measured startup floor showed it was a much smaller
share of the total, an adherence lever, not a token lever. (2) a CLI warning
about one permission-rule shape was read as "the confirmation gate is
broken"; only one component had actually been tested, never the live half of
the mechanism. (3) a probe carrying the SAME path-scope list as a real rule
file fired → treated as evidence that file works; the probe could not have
failed on that file's behalf, because it never touched it. (4) a recalled
count from an earlier read (six items) turned out to be four on recount.
Why an existing claim-calibration rule did not stop it: it is a
DELIVERY-TIME duty, executed by the author, on the author's own sentences,
while the author is still holding only the proxy. Re-reading one's own claim
re-derives it from the same evidence and it looks true again. A refutability
block written in that state inherits the error instead of catching it.
Detection, all four cases: an action taken for an UNRELATED reason produced an
output that could disagree — running the baseline script, opening the config
to edit it, checking an empty log. Where no such action existed, the claim
survived until a reviewer demanded measurement.
Fix: (1) **name the substitution in the sentence**, not a hedge — "bytes, not
tokens", "the pattern, not this file", "one rule shape, not the gate". A hedge
word keeps the proxy invisible; naming it hands the reader the thing to
attack. (2) Before writing "X works", ask: *could the evidence I have have
come out differently for the specific artifact I am claiming about?* No → it
is not evidence about that artifact. (3) When the claim is load-bearing for
the requester's decision, build the disagreeing artifact ON PURPOSE instead
of waiting for one to appear incidentally. Companion example under
`30-judgment.md` R2.
Evidence: session (this project's) | digest unrecorded | locator: instance (1)
a startup-baseline script's first run vs the preceding turn's estimate table;
instance (3) an empty rule-load log after reading a file matched by a
probe-copy scope | captured 2026-08-11

## L-016 2026-08-15 tags: verify|hooks|checks|acceptance-eval|config|silent-failure|self-audit hits: 1
Context: interop-layer maintenance pass. Three independent checks were examined
in one day and all three turned out to be incapable of failing. None of them
was broken in a way anything reports.
Pitfall: **a check that cannot fail is indistinguishable from a check that
passes**, and the three ways it happens do not look alike.
(1) *The predicate is satisfied by the wrong thing.* `ops_health_nudge.py`
check 11 tested `"ops-relaxation:" not in text`. The global CLAUDE.md contains
that token in PROSE ("offer to record `ops-relaxation:` in project CLAUDE.md"),
so every project CLAUDE.md derived from it passed vacuously. An environment-wide
grep that day found zero real declarations anywhere — the check had never once
fired correctly since birth, and its silence had been read as health.
(2) *Nothing invokes it.* `interop.py status` was correct: it printed the target
as `[missing]` and exited 1 for four days. No hook, no CI, no habit ran it, so
the target sat undeployed. A report nobody runs is not a check; exit codes only
matter to a caller.
(3) *Its subject was retired.* An acceptance eval required the target agent to
read a playbook directory that had been retired two weeks earlier and exists
nowhere. It could neither PASS nor FAIL — coverage on paper.
Why each survived: all three FAILED SILENT, and silence is the healthy signal
for a nudge, a status report and an unrun eval alike. Nothing in the artifacts
distinguishes "nothing wrong" from "asked nothing".
Fix, three parts, each cheap:
(a) **Test the check against a positive case, not just the corpus.** Every one
of these dies to one synthetic input that SHOULD trip it. A synthetic-tree suite
does it: the case named "PROSE MENTION ONLY -> must fire" is the whole lesson in
one line. Another case in the same suite caught a first-draft bug the same way
— a machine without the interop layer got a permanent, unfixable nudge.
(b) **A mention is not a declaration — require the VALUE, not the key.** Any
check keyed on a token appearing in a document is one prose sentence away from
vacuous. Match the shape that carries meaning (`ops-relaxation: L1`), anchored
to line start.
(c) **A report needs a caller, and the caller must be cheap and automatic.**
Check 12 is that caller for `status` — a stat()-only session-start screen whose
only remedy is "run `status`". Note the restraint: it routes to the authority
rather than re-implementing it, because mtime is not the commit comparison
`status` makes, so a false positive costs one command instead of a wrong build.
Detection when you cannot write a test: ask of any check, "what input would make
this print something?" If the answer takes real thought, or names a file that no
longer exists, it is already broken.
Evidence: source-environment session 2026-08-15, interop maintenance | locator
three commits that day (check 11 precision, check 12 + suite, eval 8 replaced);
the grep is `grep -rn "ops-relaxation:"` over the whole config tree |
captured 2026-08-15

---
## Archived (folded into another file, or retired)
(none yet)
