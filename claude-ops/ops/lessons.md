# Lessons — append-only pitfall log (the ledger)

Routing and fold-in rules: `40-maintenance.md` §2; where an ENFORCEMENT goes,
by trigger shape: `40-maintenance.md` §2a. Before starting any task, grep this
file for relevant keywords — by MECHANISM and by task-type tag, not only by
topic. Trim trigger: ~30 unfolded entries. This file is the SOLE pitfall ledger
(the memory pitfall-card mechanism was merged in here 2026-07-12, with zero
cards ever written). `tags:` must include at least one task-type trigger word
(e.g. canvas-animation, cross-session, subagent-dispatch, docs-versioning) so
pre-task greps hit by task type, not only by keyword.

**Shape (since 2026-08-21): one CARD per entry here, the FULL RECORD in
`ops/references/lessons-detail.md`** under the same `## L-nnn` heading —
the original write-up, every recurrence block, retraction, provenance note and
corpus number, verbatim and append-only. The card is the index and never
contradicts the detail; when they differ the detail is the record. A new entry
is born in BOTH files in the same commit — the card here, the seed of its full
record there: a card born alone has no append target for its recurrences and
nothing to survive its eventual fold (L-030..L-035 were exactly that, and were
backfilled 2026-08-27). `hits:` is maintained ONLY on the card's header line
(sweep check 5 counts it here; check 5b matches heading ID SETS across the two
files — counts are a proxy, and already collided once at 29=29 while six ids
differed each way). Cross-references such as
"L-011 hit 3", "L-011 P2", "L-025 (B4)", "L-027 hit 1" resolve in the detail
file. Extracted per `40-maintenance.md` §3 when the ledger reached 116 KB and
the pre-task grep it exists for had become a full read.

Card format:
```
## L-NNN <YYYY-MM-DD> tags: <env|dispatch|verify|...> hits: 1
Context: <what was being done — one or two lines>
Pitfall: <the MECHANISM, not the story>
Fix: <the durable fix, and where it now lives if folded in>
Detection: <the cheap check that would have caught it>   (when there is one)
Recurrences: <hit N (date, project) — one line on what it ADDED, and whether the fix HELD>
Evidence: session <id> | digest <path> | locator <turn / tool_use_id / quoted command> | captured <YYYY-MM-DD>
Detail: `lessons-detail.md` §L-NNN
```
**Recurrence check — mandatory before writing any new entry.** Grep this file
for the new entry's MECHANISM, not its topic (the second occurrence rarely
shares vocabulary with the first). Recurs? Bump the existing `hits:`, add ONE
`Recurrences:` line to the card saying whether the fix HELD, and APPEND the
narrative to the detail file — instead of a duplicate entry, or alongside a new
entry when the new one also carries genuinely new failure classes. A second hit
filed as a fresh entry leaves the ledger reading like two unrelated one-off
accidents, which is exactly how a broken fix stays invisible. `hits:` is the
ONLY instrument of global CLAUDE.md's "same symptom reported unfixed a 2nd
time" rule and of `40-maintenance.md` §4.4; nobody increments it, neither rule
can ever fire. A climbing `hits:` under an unchanged `Fix:` is this system's
own evidence that the fix does not work — unless the line says the fix HELD
(the trap recurred and the executor caught it: L-024 hits 5/7). **A card whose
`hits:` reaches 2 is routed through `40-maintenance.md` §2a before it is
considered finished** (L-011 hit 4: the table does not apply itself). Replaced?
Mark `SUPERSEDED by L-XXX`, don't delete.

**Evidence line** (required for entries written from 2026-08-11 on; older
entries are NOT backfilled). `session` alone locates a conversation, not a
fact; `locator` is what lets the next reader re-derive the judgement instead of
re-litigating it. Use `digest` when the raw transcript may age out, and write
"unrecorded" rather than inventing an id — a fabricated pointer is worse than
an absent one. Rationale and the wider trace-linking rule: `70-evolution.md` §2.

## L-001 2026-07-10 tags: dispatch|cost-cap|hooks hits: 1
Context: eval-5 subagent (spawned sonnet) was killed by a usage limit and
resumed via SendMessage; transcript showed `cache_miss_reason model_changed`
(sonnet → fable) — resume inherits the MAIN session model.
Pitfall: `model_cap_guard.py` cannot intercept the resume path. Verified vs the
official hooks docs 2026-07-10: PreToolUse fires on SendMessage but its payload
has no model/resume info; SubagentStart has no model field and cannot block; no
AgentResume event exists.
Fix: rules-side mitigation in `ops/environment.md` (Enforcement, known gap 2):
prefer re-spawning a fresh capped agent over SendMessage-resume for cost-capped
work; disclose to the user if a resume is unavoidable. Hook header documents the
hole. Re-check when the hooks API adds resume events.
Detail: `lessons-detail.md` §L-001

## L-005 2026-07-30 tags: handoff|carried-claims|verification|docs|registry|volatile-facts|numeric-constants hits: 4
Context: Prism UAT-R3.5 — a claim true when written ("batch-1 failures not yet
re-verified on the real machine") survived THREE handoff documents after it
became false; a copied verdict ("ResearchGate will keep failing, that is
correct") shipped as an instruction and was refuted in one step.
Pitfall: a claim copied from the previous round READS like an established fact
— the same authoritative voice as the measurements around it. Prose does not
decay loudly, and the receiver cannot tell "I verified this today" from "the
last document said this". Registry rows are worse carriers than prose (hit 3);
NUMBERS are the worst (hit 4): a constant, or a PRODUCT / RANGE / TOTAL inside
an equation, has no slot for a hedge, reads as measured by default, and fuses
several provenances into one token with no visible seam.
Fix: (1) carry a claim forward only by re-deriving it in-session or marking it
INHERITED with the round it came from — never restate it flat. (2) Make the
build check what it can (Prism DRIFT-01 `check_architecture.py::carried-
design-anchor` asserts every deferred-design anchor still resolves; prose decays
because nothing fails when it does). (3) Any number a design or conclusion RESTS
ON carries `measured-here` / `measured-elsewhere(what, when)` / `estimated` /
`inherited-default`, and anything not `measured-here` is re-measured before a
conclusion is published on it — ask of any derived figure which inputs went in
and whether they were all current at the same moment (now `30-judgment.md` R2
claim-calibration).
Detection: every hit-4 instance was found by READERS doing something else; the
verifier that checked the cited file EXISTS caught none — file existence is not
the check (L-025).
Recurrences: hit 3 (2026-08-15, `interop/MIGRATION-MAP.md`) — a July
verification restated flat in the present tense under a heading calling it
volatile; fixed by REMOVING the rows so re-adding must re-derive. · hit 4
(2026-08-21, bench-claude-arms) — a 200,000-token context window probed on a
smaller model (measured 1,000,000; it killed the pre-designed crossover), an
ESTIMATE 3.7× off and large enough to invert the cache-TTL verdict, and a
published product `13 × 5,715 = 51,435` whose second factor was stale
(authority 74,295); a peer session found a RANGE written from the subset in
view and a TOTAL whose n-cell covered a different set. `_bench-claude-arms\tools\paper_data.py`
now prints the derived products so prose can be diffed against data. Fix (1)
was in place; the fix did not reach constants until (3) was added.
Detail: `lessons-detail.md` §L-005

## L-006 2026-07-31 tags: skill-design|review-methodology|checklist|scope-gating hits: 2
Context: FSM/state-machine and cross-boundary contract-drift lenses added to the
deep-checklist skills (commits afb0c28, 19b00df).
Pitfall: checklist skills enumerate only code-visible defects; defect classes
that live in DESIGN SEMANTICS (state machines, mirrored FE/BE contracts,
twin-implemented rules, doc claims) have no grep target — and both naive fixes
fail: an always-on section taxes every review, duplicating the topic into the
quality AND security skill creates rule drift.
Fix (pattern, folded into code-review-deep-checklist Mode A §10/§11 + Mode B
lenses, security-deep-checklist Mode A §9): (1) reconstruct-and-compare —
rebuild the intended model as a REPORT ARTIFACT, then check code against it;
(2) every such section carries an explicit trigger gate and records skips, depth
capped (top 1–3 units); (3) single-owner placement — quality lens in
code-review, attacker projection in security, and check whether the second
skill's projection is ALREADY covered before adding; cross-skill traffic stays
discovery-candidate only.
Detail: `lessons-detail.md` §L-006

## L-007 2026-07-31 tags: rules-editing|structural-edit|verify hits: 1
Context: inserting section 10 into single-review.md; a misplaced Edit insert
followed by a PARTIAL revert left two "## 10" headers, one truncated.
Pitfall: insert-then-revert sequences on numbered checklist files corrupt
structure silently — each individual edit "succeeded"; the author pass did not
catch it, only config-self-audit's section-header listing did.
Fix: after any structural edit to a sectioned rules file, scan headers
(`Select-String '^## '`) and verify uniqueness + order BEFORE commit; prefer
append-at-end or a single scripted move over incremental insert+revert. This is
also the standing reason config-self-audit runs after every skill edit.
Detail: `lessons-detail.md` §L-007

## L-008 2026-07-31 tags: rules-editing|naming|scale-labels|ux|project-artifacts|uat hits: 3
Context: the ops-relaxation scale (05-authority §2). The user read "L2" as a
permission/strictness level; "L2/L3" was also reused in 70-evolution for a
different scale.
Pitfall: (a) a bare scale label carries no direction — readers fill it with the
dominant convention (ASVS: higher = stricter), inverted here; (b) label famines
— reusing a family for a second scale makes grep and recall collide.
Definitions live in one file; labels travel without them.
Fix (folded in): scale-label qualifier at every point of use (40-maintenance
§3); direction + precedence paragraphs in 05-authority §2; gate-ask glosses;
70-evolution renamed "(layer 2)/(layer 3)". Governing principle: a label
carries enough qualifier to resolve its referent at EVERY point it is cited;
`~/.claude/LABEL-REGISTRY.md` is the one definition table.
Recurrences: hit 2 (2026-08-12, environment sweep) — `Mode A` ×54 / `B` ×48 /
`C` ×20 across seven skills, `Tier` in five senses; root cause: the corollary
lived in TRIM discipline (fires over cap) while labels are minted at AUTHORING
— moved to §3 Birth budgets. · hit 3 (2026-08-12, user-reported, project
level) — an old checklist 1-14 and a new round R0-R7 coexisted; "the 5th item"
resolved to two tests and the conversation ran to completion on the wrong
artifact — silent, unlike hits 1-2. Fix: generation prefixes for project lists
(60-bootstrap §E), LABEL-REGISTRY created.
Detail: `lessons-detail.md` §L-008

## L-009 2026-08-05 tags: env|browser-pane|screenshot|verify|diagnosis hits: 1
Context: ~1 month of intermittent `computer{action:"screenshot"}` timeouts in
the in-app Browser pane, repeatedly misdiagnosed as permission/sandbox. Actual
state: `document.visibilityState === "hidden"` while every CDP read kept
working.
Pitfall: (a) the tell was present from the first occurrence — ONE tool in a
group failed with a TIMEOUT while its siblings stayed green; a denied permission
returns a refusal, not a timeout, so asymmetry inside a tool group rules out
permissions before any investigation starts. (b) The first write-up asserted
the mechanism as fact by quoting the tool's own error string — a quoted error
string is the tool author's assertion; record it at correlation level.
Fix: detection-first rule in global CLAUDE.md; enforcement moved 2026-08-08 to
`hooks/ui_verify_guard.py` (denies the screenshot until a `visibilityState`
probe ran — why a hook and not a line: L-011). Premise corrected 2026-08-16:
`hidden` is this machine's STEADY STATE (the foreground is not commandeerable;
a fresh pane is born hidden), so pixels route OUT-OF-PROCESS BY DEFAULT and the
probe's remaining job is the discriminator — `visible` + timeout is a DIFFERENT
fault. Premise: `environment.md` "Browser pane"; recipes:
`ops/references/browser-pane-pixel-route.md`.
Detail: `lessons-detail.md` §L-009

## L-010 2026-08-08 tags: env|browser-pane|verify|ui-testing|flaky|css hits: 1
Context: browser-pane UI verification — hover/focus a control, then read
`getComputedStyle` against a design token.
Pitfall: `getComputedStyle()` during a CSS transition returns the INTERPOLATED
mid-flight value, and the MCP round-trip is non-deterministic, so the failure is
FLAKY, not stably wrong — the same code passes and fails across runs and sends
the reader to debug correct code; the obvious fallback (a screenshot) is what
L-009 takes away. Measured (`ui-state-probe` verify.mjs, 5s transition):
hover-then-measure never reaches the target; finishing animations first does,
3/3.
Fix: (1) settle before measuring — `el.getAnimations({subtree:true}).forEach(a
=> a.finish())` is SYNCHRONOUS; infinite keyframes take an injected
`transition:none;animation-duration:0s` stylesheet; (2) prefer asserting STATE
(`data-state`, `aria-expanded`, class flips) over a rendered pixel value; (3)
enforcement `hooks/ui_verify_guard.py` denies a `javascript_tool` call carrying
`getComputedStyle` with no settle token; (4) the out-of-process tool: AssetVault
`ui-state-probe` (utility/node).
Detail: `lessons-detail.md` §L-010

## L-011 2026-08-08 tags: rules-design|enforcement|hooks|layering|omission|harness hits: 4
Context: deciding where to put the L-009/L-010 rules so they actually fire
(user question: can CLAUDE.md's routing really reach OPS and lessons?).
Pitfall: the three rule layers have very different firing guarantees, and a
rule written into the wrong one reads as durable and is dead. `ops/lessons.md`
fires only when something greps it; `ops/*` only when CLAUDE.md's
project-operations clause routes there; global CLAUDE.md is always in context
but fires only on a trigger-word match — unreliable for rules that must fire
MID-MEASUREMENT, when the agent is already confident (L-009 recurred for a
month under exactly such a line).
Fix (folded in 2026-08-21 → `40-maintenance.md` §2a): choose the layer by
TRIGGER SHAPE, not importance — a named tool call with inspectable input →
PreToolUse hook (deny beats warn); a task-shaped judgement → CLAUDE.md
conditional rule; "someone is already investigating this topic" → lessons.md,
as the detail the shorter layers point AT. When a hook carries the enforcement,
the CLAUDE.md line stays as the explanation the denial cites, and both name the
lessons entry. FOURTH SHAPE, omission (hit 2): a rule whose violation is "the
step never happened" generates no event — P1 gate the SUBSTITUTE commission
(PreToolUse on the substitute's tools), P2 make the ABSENCE greppable (a literal
marker a sweep enumerates), P3 gate at the event that ENDS the action (e.g.
SubagentStop). Harness-compatibility (user ruling 2026-08-14): an omission gate
NARROWS WITHIN injected harness instructions, never contradicts them — surface
the withheld decision to the user, never take the action. COST OF P1/P3: a hook
that does not run is itself silent, so every such hook ships with a
proof-of-life line in `integrity-sweep.md` in the SAME commit. FIFTH SHAPE (hit
3): choosing the right LAYER does not tell you the right SURFACE — before
shipping any trigger, find the last recorded instance of the failure AS A TOOL
CALL and confirm the trigger sees that shape; only the corpus answers it, and it
answered oppositely for two traps in the same language the same week (47 of 53
EAP='Stop' payloads through Write; 160 of 160 `| Select-Object -First` hazards
through the PowerShell tool). Price each surface (ms × fires) instead of
registering all of them.
Recurrences: hit 2 (2026-08-14) — the omission shape, above. · hit 3
(2026-08-21, bench-claude-arms) — the "hook 3/3 vs prose 0/1" comparison first
written here was RETRACTED by an adversarial review (one-sided sampling: the
prose arm's ≥3 successes uncounted, the hook layer's own defects uncounted,
different phases; Fisher p=0.25 at n=4). What stands: a rule can be correct,
current, globally rented AND the thing being written about, and still not fire
— a mechanism, not a rate; the lever is moving the TRIGGER to the moment of
danger. Closed by `hooks/ps_errorpref_guard.py`. · hit 4 (2026-08-21) — the
routing table did not apply itself to the entry being written two screens below
it: L-027 (a named-tool-call trigger, hit twice) was filed into lessons; caught
by the review, closed by `hooks/ps_pipeline_close_guard.py`. Hence the header
rule: a card whose `hits:` reaches 2 is routed through §2a before it is
finished.
Evidence: hits 3-4 — `_bench-claude-arms\REVIEW_RETRO_ADVERSARIAL_2026-08-21.md`
C-4 and §4.7 row 5 | captured 2026-08-21
Detail: `lessons-detail.md` §L-011 (the retraction in full, the corpus counts,
the surface pricing, the original A/B text kept for the record)

## L-012 2026-08-11 tags: verify|evidence|claim-calibration|delivery|self-review hits: 2
Context: harness context-budget work (E1/E4/T-007). Four over-claims in one
task, all caught, none by re-reading the text that contained them.
Pitfall: PROXY PROMOTION — a proxy is measured, then spoken about in the voice
of the thing it stands for (bytes → "tokens paid"; one component tested → "the
gate is broken"; a probe with the same config → "this file works"; a count
recalled → wrong). R2's claim-calibration duty did not stop it because it is
executed by the author, on the author's own sentences, while still holding only
the proxy — re-reading re-derives the claim from the same evidence and it looks
true again.
Fix: (1) NAME THE SUBSTITUTION in the sentence, not a hedge ("bytes, not
tokens"); (2) before "X works", ask whether the evidence could have come out
differently for the specific artifact; (3) when load-bearing, build the
disagreeing artifact ON PURPOSE — the only fix with a recorded catch (4/4 here,
3/3 in L-015, 0 for the phrasing fixes), now a close-out step (`50-coach.md`
C11 q4). Companion example: `30-judgment.md` R2.
Detection (all four): an action taken for an UNRELATED reason produced an
output that could disagree.
Recurrences: hit 2 (2026-08-12) — L-015 (1) is this mechanism surviving in
DESIGN-RATIONALE prose while the fix had been applied only to evidence prose;
the scope was made explicit in R2 rather than by rewriting this entry.
Evidence: session (a local transcript) | locator:
`tools/context-budget/startup_baseline.py` first run vs the preceding estimate
table; `telemetry/rule-loads.jsonl` empty after reading a `.tsx` | captured 2026-08-11
Detail: `lessons-detail.md` §L-012

## L-014 2026-08-12 tags: agents|subagent|tools|capability|skills|silent-failure|config hits: 1
Context: rewriting `agents/*.md`; a `tools:` allowlist was added so "read-only
reviewer" stopped being prose. The proposed list was `Read, Glob, Grep`.
Pitfall: `tools:` is an allowlist, and `Skill` is a tool — that list would have
silently and permanently disabled every skill the agent could invoke (the
official wording: omitting `Skill` is the documented way to PREVENT skill use).
General shape: tightening a capability boundary silently removes capabilities
you were not thinking about — an allowlist written against one axis (write
access) cuts every other axis it intersects (skills, search, MCP). Near-misses
in the same edit: dropping `Bash` removes `git diff`; `permissionMode: dontAsk`
auto-denies anything outside `settings.json`'s allowlist, which has no `Edit`.
Fix: after writing any `tools:` list, enumerate what it REMOVES and check that
against (a) skill invocation, (b) the agent's own verification path, (c) the
session permission allowlist. Read-only = the write tools are absent and
everything else survives.
Detection: `grep -L 'Skill' agents/*.md` must be empty unless a definition
deliberately forbids skills (sweep check 1).
Evidence: `code.claude.com/docs/en/sub-agents`; caught in review before
dispatch | captured 2026-08-12
Detail: `lessons-detail.md` §L-014

## L-015 2026-08-12 tags: verify|claim-calibration|design-docs|self-review|scope-gating|research hits: 1
Context: Prism R9 `DESIGN-06`, self-audited hours later against the artifacts
it superseded — six findings, three instructive and NOT one class.
Pitfall: (1) claim calibration silently scoped to the evidence sections — the
DESIGN sections asserted two problems were "the same" (shared symptom,
different evidence) and nobody decided they were exempt (L-012 in rationale
prose); (2) deferral without blast radius — a deferred capability silently left
two queries dead; (3) two known facts never multiplied — a quantity and its
acceptance threshold, both quoted in-session, never joined.
Fix: (1) calibration covers design-rationale prose — any "X and Y are the
same" / "X follows from Y" takes the "could my evidence have come out
differently?" test (now `30-judgment.md` R2 scope); (2) a deferral names what
currently depends on it, or it is incomplete; (3) when a document states a
quantity and another its threshold, join them at that moment. Caveat: six
findings in one pass means the document was written faster than it was checked
— a high find-rate predicts more remaining, not that the sweep finished.
Detection: the same mechanism as L-012 fix (3) — a computation run for an
unrelated reason emitted (2) and (3) as byproducts; (1) came from an
adversarial question sourced outside the claim, not from re-reading.
Evidence: session (a local transcript) | locator:
`Prism/research-r9/AUDIT-04-design06-self-audit-and-legacy-fit-2026-08-12.md`
F-1/F-4/F-5/F-6 | captured 2026-08-12
Detail: `lessons-detail.md` §L-015

## L-016 2026-08-15 tags: verify|hooks|checks|acceptance-eval|config|silent-failure|self-audit hits: 1
Context: interop maintenance — three independent checks examined in one day,
all incapable of failing, none broken in a way anything reports.
Pitfall: A CHECK THAT CANNOT FAIL IS INDISTINGUISHABLE FROM ONE THAT PASSES,
three ways: (1) the predicate is satisfied by the wrong thing
(`ops_health_nudge` check 11 keyed on the token `ops-relaxation:`, which the
global CLAUDE.md mentions in prose — it had never fired correctly since birth);
(2) nothing invokes it (`interop.py status` exited 1 for four days, nobody ran
it); (3) its subject was retired (eval 8 required a directory that no longer
existed). Silence is the healthy signal for a nudge, a status report and an
unrun eval alike.
Fix: (a) test the check against a POSITIVE case, not just the corpus
(`tools/ops-health-test/`, case "PROSE MENTION ONLY -> must fire"); (b) a
mention is not a declaration — match the VALUE shape (`ops-relaxation: L1`),
anchored to line start; (c) a report needs a cheap automatic caller (check 12
routes to `status` instead of re-implementing it).
Detection when you cannot write a test: ask "what input would make this print
something?" — if the answer takes real thought or names a file that no longer
exists, it is already broken.
Evidence: commits 9480f39 / 8fab5cb / 9521c20; `grep -rn "ops-relaxation:"
~/.claude` on 2026-08-15 | captured 2026-08-15
Detail: `lessons-detail.md` §L-016

## L-017 2026-08-16 tags: rules-design|checklists|security|invariants|verify|remediation hits: 2
Context: NTUMail2TG — security prerequisite EP-1 written as "`D:\` must not
grant BUILTIN\Users FullControl"; the user declined (drive root; sandbox
accounts work there); it sat NOT SATISFIED across two phases while the risk was
already eliminated another way (binary moved to an owner-only directory).
Pitfall: the item named a LOCATION, not the PROPERTY (SI-4: "the autostart
directory is not writable by broad principals"), so it could not recognise the
other valid fix. Consequences: a HIGH finding claimed live after its attack path
was cut, and a permanently-red item teaches the reader the checklist can be
ignored. Instruction-shaped controls read more concrete than property-shaped
ones; that concreteness IS the failure mode (now global CLAUDE.md: write the
invariant as a property of the asset).
Fix: (a) checklist item = a test of the property; (b) a declined remediation
converts into an accepted risk carrying its compensating control + revisit
conditions — every line reads "satisfied" or "known and decided"; (c) prefer a
compensating control that cannot decay (the leaf-dir ACL was declined because
`publish.ps1` recreates the dir — detection via git chosen over prevention).
Detection: for each red item ask "would this notice a DIFFERENT valid fix?"; an
item the user declined twice is a specification problem, not compliance.
Recurrences: hit 2 (2026-08-21, bench-claude-arms G4) — GUI screening item "no
repeated apply" named a MECHANISM; for a batch-rename tool a correct build fails
it and a click-swallowing build passes. Caught by the human operating the thing;
wording corrected RETROACTIVELY for the already-screened arm so both arms are
judged under one wording.
Evidence: session (a local transcript) | locator:
`NTUMail2TG/SECURITY-POLICY.md` EP-1 + AR-5;
`references/NTUMail2TG-decisions.md` P-004 / D-010 | captured 2026-08-16
Detail: `lessons-detail.md` §L-017

## L-018 2026-08-16 tags: testing|harness|isolation|forensics|logging|silent-failure hits: 1
Context: NTUMail2TG offline harness drives the REAL engine with a fake mail
source and a fake Telegram sink; `Logger` wrote to a hard-coded path, so every
test run appended synthetic deliveries to the user's operational `bridge.log`,
`[security]` channel included.
Pitfall: the fakes covered the two things that FELT external (network,
mailbox); the log stayed pointed at production because the question asked was
"what does this code READ?" A test double gets built at the boundary already
under consideration, and by default that is the input side. Nothing fails; the
contamination lands on records that already existed.
Fix: `Logger.RedirectTo`, one-way and SINGLE-USE (a log path that can be swapped
at will is itself a way to make records disappear); the harness redirects before
anything can log, and a test asserts a second call throws.
Detection: enumerate what the code under test WRITES — logs, state files,
registry, caches, notifications, telemetry — and require each redirected or
asserted-unchanged; cheap positive check: the production artifact's byte length
is identical across a full harness run (4653 → 4653).
Evidence: session (a local transcript) | locator:
`NTUMail2TG/MailBridge/Core/Logger.cs`, `MailBridge.Tests/Program.cs`;
`references/NTUMail2TG-decisions.md` P-005 | captured 2026-08-16
Detail: `lessons-detail.md` §L-018

## L-019 2026-08-16 tags: verify|acceptance-eval|parsing|subagent-dispatch|interop|gate-design|silent-failure hits: 6
Context: acceptance gates over model output — JSON extractor, evidence-anchor
checker, structure checker, adversarial verifier; four gates, three mine, one a
peer team's.
Pitfall: a gate ruling on a question it has no power to decide, and the ruling
landing as REJECT — transport failure recorded as "refuted"; a PowerShell BOM
recorded as STRUCTURE-FAIL; a verbatim quote under the wrong line number
recorded as FABRICATED; a greedy `\{.*\}|\[.*\]` slice voiding 10/10 valid
payloads. The gate is CORRECT about what it can see and silently extrapolates
to what it cannot; a confident plausible negative reads like a finding and is
never questioned. General form (hit 6): the gate returns ONE value where the
input supports several — A TIE-BREAK IS A RULING, in either direction.
Fix: a gate may only rule on what it can DETERMINE; everything else is
DOWNGRADE AND FORWARD, never veto — three-valued outcomes with the third state
loud (`inconclusive` ≠ `refuted`; `MISALIGNED` + auto-repaired line vs
`FABRICATED`); a parser strictly more lenient than the prompt; the receiving
side's strictness is itself a measured variable (strict 0/5 vs lenient 5/5 on
identical answers). Now global CLAUDE.md's gate rule and `30-judgment.md` R2.2.
Detection: feed a known-TRUE input, not only a known-false one — a gate that
rejects everything scores 100% on a one-sided calibration. Cheap tell (hit 5):
a UNANIMOUS verdict out of a freshly written checker is an instrument fault far
more often than a finding — a moment, not a design phase, so it fires when the
design-time trigger does not. For ACCEPTs (hit 6): ask "can it return the same
confident answer for two different inputs, and does anything print when it
does?" — and WHEN A LOOKUP'S POPULATION STOPS BEING HAND-MAINTAINED, RE-ASK
WHAT HAPPENS ON A TIE.
Recurrences: hit 5 (2026-08-21, bench-claude-arms) — three more
reject-everything gates with the rule already in global CLAUDE.md verbatim:
`[regex]::Escape` patterns passed to `-SimpleMatch` (11/11 sections "missing"),
an array compared to a scalar (4/4 runs "invalid"), an overlap probe whose
threshold only the RAW PAIRS revealed; the one instrument calibrated both ways
never produced a false verdict. · hit 6 (2026-08-21, session-board) — LANDED
ON ACCEPT: three tickets matched one session and `Resolve-Ticket` returned the
first in file order — invisible to this entry's own detection (all prior
instances were REJECTs) and to a 12-case two-sided self-test whose fixtures
never held two matching tickets; fixed with a fourth state AMBIGUOUS naming
every candidate (correct 2→3, wrong 1→0, UNBOUND 11→11; self-test 12/3 →
29/9).
Evidence: session (a local transcript) | locator:
`tools/extdispatch/redteam_verify.py` `verdict_of()`, `score_redteam.py`
`check_anchor()`, `test_score_anchor.py`; hit 6: session
(a local transcript), `tools/session-board/session-board.ps1`
`Resolve-Ticket`, commit `eaa0d3e` | captured 2026-08-16 / 2026-08-21
Detail: `lessons-detail.md` §L-019

## L-020 2026-08-16 tags: refactor|duplication|testing|verify|retrospective|dead-code|silent-failure hits: 2
Context: a retrospective's sibling scan on `tools/extdispatch/` ("was any of
this written twice?"), run after the milestone had shipped with four green
suites.
Pitfall: one algorithm existed in THREE places and two had been fixed; the
third (the STRUCTURE layer, the first gate every report passes) still returned
STRUCTURE-FAIL on valid input. TWO INDEPENDENT FIXES OF ONE BUG IS THE
MECHANISM BY WHICH A THIRD COPY SURVIVES — each fix lowers the felt urgency of
looking further, and a grep for the SYMPTOM finds nothing because the fixed
copies no longer exhibit it. Worse: a test imported one copy while the live
layer ran another — a test covering a duplicate reports green on code nobody
runs.
Fix: extract to one module the moment a SECOND copy is created
(`tools/extdispatch/jsonspan.py`; `peer_experiments.status_block_ok()`), and
point tests at the shared symbol, never a consumer's re-export.
Detection (the load-bearing half): after fixing any MECHANISM-level bug, grep
the tree for the mechanism (loop shape, regex, sentinel) and count call sites;
then check which copy the tests import. Writing the lesson does not raise the
urgency — the second copy is created in the same motion as the first piece of
new code ("I need this here too"); only a scan catches it.
Recurrences: hit 2 (2026-08-16, thirty minutes after this entry, same author)
— the `<status>` block contract written twice (live grader vs the grader whose
output went to a peer team); caught by the same sibling scan on the next run;
re-grading produced byte-identical numbers.
Evidence: session (a local transcript) | locator: commit
`b5062a7`; `outputs/retrospectives/retrospective-extdispatch-2026-08-16.md`
Category 2 | captured 2026-08-16
Detail: `lessons-detail.md` §L-020

## L-021 2026-08-16 tags: env|powershell|shell|git|quoting hits: 1
Context: `git commit -m @''...''@` from PowerShell 5.1 with a here-string that
contained embedded double quotes.
Pitfall: PS 5.1's native argument encoder does NOT escape embedded `"` for the
child process — the quote ends the argument mid-message, git parsed the tail as
pathspecs, the commit silently did not happen while the rest of the chain kept
running (merge "Already up to date", branch deleted un-merged). Here-strings
solve MULTILINE, not EMBEDDED-QUOTE; messages without inner quotes work for
months before one hits.
Fix: for any native-exe argument that may contain `"` in PS 5.1, write the
content to a file and pass the file (`git commit -F <msgfile>`), or drop the
inner quotes (global CLAUDE.md Environment). Verify after any chained git
sequence — and (amended 2026-08-21 from L-023 hit 2) `git log --oneline -1`
answers WHETHER a commit landed, never WHERE; pair it with `git branch
--show-current`, or name the branch: `git log --oneline -1 <branch>`.
Detail: `lessons-detail.md` §L-021

## L-022 2026-08-16 tags: signal-processing|thresholds|ml-depth|imaging|diagnosis hits: 1
Context: 3D Photo Synthesis Engine — cutting depth discontinuities out of an
ML-predicted depth map (edge masking; mesh culling).
Pitfall: hunting a sharp feature in a smoothed signal. ML depth smears true
steps into multi-pixel ramps, so the per-pixel difference stays below any
reasonable threshold and `percentile(gradient, 95)` cuts "the steepest 5%" —
noise, ranked. Every threshold value looks defensible and each retune produces
a visibly different (still wrong) mask, which reads as progress rather than as
a wrong axis.
Fix: change the measured QUANTITY, not the threshold — find a space in which
the outlier is genuinely an outlier (here 3D edge length / median: 576.9×,
clean bimodal histogram, one cut, view-independent).
Detection: before tuning any threshold, ask whether the sharp feature can exist
in this signal at all; if it came through a model or filter, it usually cannot.
Status: single project, hypothesis tier; global candidate H-6 deferred —
re-propose on a second project's hit.
Evidence: `outputs/retrospectives/global-rule-candidates-3D-photo-engine-2026-08-16.md`
H-6 | captured 2026-08-16
Detail: `lessons-detail.md` §L-022

## L-023 2026-08-17 tags: git|env|concurrency|shared-worktree|branch|dispatch|shared-index hits: 4
Context: two sessions working `~/.claude` at once; Session B ran `git checkout
-b` trusting its session-start snapshot ("Current branch: main") while HEAD was
A's feature branch — B forked off A's unfinished work and A's next two commits
landed on B's branch.
Pitfall: HEAD, `.git/index` and the working tree are SHARED MUTABLE STATE
between sessions in one tree. A checkout in either session silently redirects
the other's commits; a ref move without a checkout leaves a stale shared index
that the next commit in ANY session serializes as deletions (hit 3: 52 files,
no error); an uncommitted peer edit is ABSORBED into whoever stages that path
next (provenance lost, content intact). No command errors; ancestry checks pass
while content is wrong.
Fix: the shared-tree discipline lives in `ops/references/shared-tree-git.md`
(owner `20-dispatch.md` §7a) — routing by COUPLING CLASS (user ruling
2026-08-17: same workstream → SERIALIZE / baton-pass; disjoint domain → the
second session takes a worktree; live-environment verification → canonical tree,
ONE writer; true parallelism → split by TREE, never by ticket), the commit
ritual (`git branch --show-current` → stage explicit paths → commit → `git show
--stat HEAD` read for what you did NOT write), the content-vs-ancestry check
(`git cat-file -e <sha>:<path>`), and the recovery recipes (plumbing merge;
`git branch -f main <sha>` when caught within one commit; additive restore,
never revert). Hail peers with `ccd_session_mgmt list_sessions` +
`send_message`; a peer live in the tree is NORMAL — run the checks, do not stop
and report "another session is blocking" (that hand-back has happened).
Recurrences: hit 2 (2026-08-21) — SAME SHAPE, and the rule named the exact
command: a hook session ran `checkout -b` between a peer's status check and
commit; the two commands the peer DID run (`git status --porcelain`, `git log
--oneline -1`) cannot see the fault and look like diligence — `--porcelain`
prints no branch, a bare tip hash answers WHETHER not WHERE (L-021 amended).
Third time in one session a correct written rule failed to fire while its
neighbours ran (L-011 hit 3, L-019 hit 5). Fix did NOT hold. · hit 3
(2026-08-21, same day) — THE MITIGATION FOR HIT 2 CAUSED IT: publishing via
`git update-ref` (no checkout) left the shared index stale; the other session's
next two-file commit recorded 52 deletions; `merge-base --is-ancestor` still
said yes. General form: a mitigation that moves a fault from LOUD to SILENT is a
downgrade — ask "what shared state does this NOT synchronise, and how would I
see it?" Provenance: the hit-3 narrative was written by two sessions from
opposite sides of the incident, and the first attribution (by cwd) was WRONG —
identify a commit's author by what it TOUCHES, never by which session looks
busy; a mis-addressed all-clear is worse than none. · hit 4 (2026-08-27) —
same shape, ritual present and non-gating: c5468e6/f61b226 landed on peer
branches because `git branch --show-current` ran as a spectator in a `&&`
chain. The prose control is now ENFORCED: PreToolUse hook
`hooks/branch_commit_guard.py` denies any non-main commit targeting this
tree (escapes: `[branch-ok]` marker, per-worktree opt-in). Its docstring —
not this card — is the running log from here on (incidents #1–#3, FP
ledger, narrowing triggers, the registration outage rule: never delete a
live-registered hook file).
Evidence: hit 1 unrecorded | hits 2-3: commits `3121530`, `9d56150`, `0b257e7`
| captured 2026-08-17 / 2026-08-21
Detail: `lessons-detail.md` §L-023 (recovery recipes as first written, the
provenance note, the escalation ruling)

## L-024 2026-08-18 tags: env|shell|bash|powershell|tool-routing|silent-failure|encoding|line-endings|runaway hits: 9
Context: a 10-day sweep of every shell call in the transcript corpus (6,544
deduplicated calls, 370 errors) asking why PowerShell errored 4× more than
Bash. Answer: three silent defects in the Bash tool's command TRANSPORT, plus
a selection effect.
Pitfall: (1) BACKSLASH COLLAPSE — n consecutive backslashes arrive as
ceil(n/2) in every quoting context (`\n`/`\t`/`\"` untouched), the command
reports SUCCESS, escaping harder is halved twice; symptoms differ per language
and none name the cause. (2) SIZE CEILING — every Bash command ≥ ~7,700 B fails
`unexpected EOF` (truncated at the OS boundary; PowerShell succeeded at
8,053 B). (3) WINDOWS PATH FORMS — unquoted loses every backslash, a trailing
backslash inside double quotes escapes the closing quote. Line endings: Edit
is the ONLY write path that preserves the target's ending (Write → LF; `cat
>>` / `WriteAllText` → MIXED file; `Out-File`/`>` → BOM). Retraction kept:
PowerShell `2>&1` does NOT make the tool report failure (selection bias); the
real hazard is `$ErrorActionPreference='Stop'`, wrong in BOTH directions for
native exes.
Fix: routing at the source (global CLAUDE.md Environment bullet 1 — file
content → Write/Edit, search → Grep/Glob, the shell keeps git / programs /
pipelines; measured Write 0.1% vs Bash-writing-a-file 5.2%, Grep 0.9% vs
PS-searching 17.4%); the three limits stay in CLAUDE.md as the backstop.
Executors: `hooks/shell_transport_guard.py` (deny size, annotate backslashes),
`hooks/ps_errorpref_guard.py` (ANNOTATE-only, 2026-08-21, registered on
`Write|PowerShell` because 47 of 53 EAP='Stop' payloads arrived as `.ps1` files
through Write/Edit — the rule is about a LANGUAGE, mostly written into files).
All three traps hooked. Line endings pinned per repo by `.gitattributes`.
Recurrences: hits 5 & 7 (2026-08-21, bench-claude-arms) — backslash collapse
reached for THREE times, `shell_transport_guard` intercepted all three, nothing
lost — the fix HELD (hit 7 fired on a `sed 's|\\|/|g'` inside the self-check of
the retrospective arguing for hooks: the recall-vs-executor gap, demonstrated).
· hit 6 (2026-08-21) — the EAP='Stop' prose-only trap hit once, NOT prevented,
cost a diagnosis round; now hooked. The "3/3 vs 0/1" ratio was RETRACTED
(L-011 hit 3) — a mechanism, not a rate. Ledger rule from this bump: when
bumping `hits:`, say whether the fix HELD.
· hit 8 (2026-08-26, graph-snapshot phase 2) — the line-ending half: a
rule-registry append went through a Bash heredoc `cat >>` and produced a
MIXED file. The ROUTING fix did NOT hold (the executor reached for the shell
with Edit available and the rule in context); the DETECTION half held —
`tools/shell-audit/invariants.py` flagged it in-session, endings normalized
to CRLF, nothing lost. Multi-paragraph appends are exactly when the shell
looks convenient; that is the moment the routing rule is for.
Evidence: session (a local transcript) |
`outputs/shell-command-error-audit-2026-08-18.md` v2 §2.1 §2.2 §2.3 §2.4 §5 |
captured 2026-08-18. Review-when: Claude Code updates — re-run the three probes
(report §2.1, §2.4, §5.2) before trusting the numbers.
Detail: `lessons-detail.md` §L-024 (symptom catalogue per language, the full
line-ending matrix, the `2>&1` retraction reasoning, the EAP guard's organic
positive control)

Ninth hit (2026-08-28, media-fetch-pipeline) adds a COST the audit did not
measure, because it is invisible inside a session: a routed-wrong search that
also cannot terminate runs until somebody notices. `find / -maxdepth 6 -name
transcribe.py -path "*faster_whisper*" 2>/dev/null | head -3` ran **three
hours** and was killed by hand after the user asked what it was doing. Three
compounding facts, none of them about backslashes: (a) Git Bash's `/` is the
Git install dir, but `/c` and `/d` are MOUNTS INSIDE IT, so `find /` walks
both whole NTFS drives; (b) `head -N` exits only after N matches, and the
target sat at depth 8 so `-maxdepth 6` guaranteed **zero** -- the pipeline
could never close; (c) `2>/dev/null` ate every permission error, so there was
no symptom. The harness backgrounds a foreground command at the 120 s timeout
and **nothing reaps it afterwards**. Grep found the same file in seconds two
minutes later. Rule unchanged -- route search to Grep/Glob -- but add the check
that would have caught it anyway: **before backgrounding anything, ask whether
its exit condition is reachable.** A command that cannot succeed cannot stop.

## L-025 2026-08-21 tags: verify|instruments|calibration|measurement|silent-failure|self-audit|first-use|tooling|gate-design hits: 1
Context: bench-claude-arms, a 22-run controlled study. Its OBJECT got every
control (held-out suite calibrated both ways, differential fuzzing, mutation
testing); its own working tooling got none, and at least six improvised
scripts each failed on first real contact with data — every one straight into
a published number or a discard decision: a dedupe that inverted the
conclusion, a price table with a silent fallback, probes counted as runs, an
array-vs-scalar exclusion, an 11/11-missing self-check, a completion monitor
that trusted transcript silence and harvested an empty deliverable (B4 in the
retrospective index), and a verifier that checked files EXIST and never their
contents.
Pitfall (corrected by adversarial review C-3): rigor followed the PHASE, not
the thing — everything built inside the declared instrument-building phase was
calibrated, everything improvised mid-flight to unblock something was not. The
original "deliverable vs tooling" story was constructed afterwards (zero
instances in the record) — a retrospective's narrative is an unverified claim
and its author is the last person able to falsify it. THE BASE RATE ("6 of 6
failed") is RETRACTED as circular (the denominator was the set of failures):
"at least six, none caught by the author's same-moment check", no rate.
Fix: (a) a script that emits a VERDICT or an AGGREGATE gets one known-answer
input before its output is believed; (b) a unanimous verdict from a fresh
instrument is a STOP, not a result; (c) is NOT a new rule — it restates
`30-judgment.md` R2.2, whose trigger was a closed list ("cron/hook/service/
job") and was WIDENED 2026-08-21 to the property "anything whose output will be
BELIEVED rather than read line by line" (a scope defect, fixed by widening in
place; promotion ruled against; reopen if the widened R2.2 goes two projects
without one recorded firing); (d) "this pattern is happening again" written in
a turn becomes a rule with a trigger, or a ticket, in the SAME turn — L-027 is
what skipping it costs. Calibration's second dimension (same day, a peer
reviewing session-board): DIRECTION is not POPULATION — ask "what is the
smallest input that produces a WRONG answer rather than a missing one, and is
it in my fixture?" (a third ticket).
Detection: a script emits a verdict/aggregate; a unanimous verdict over n≥3;
"I am writing an unplanned checker right now" — known at the moment, unlike
"is this output load-bearing?", the judgement demonstrably got wrong six times.
Evidence: session (a local transcript) | digest
`memory-archive/digests/D--AIWork/187fd681-....md` L428 L462 L1115 L1137 L1195
L1273-L1295 L910 | `_bench-claude-arms\RETRO_INDEX_2026-08-21.md`
clusters A/B; `REVIEW_RETRO_ADVERSARIAL_2026-08-21.md` C-1/C-2/C-3/C-6 |
captured 2026-08-21. Cross-project occurrences: graph-snapshot 2026-08-20,
extdispatch 2026-08-16, AnnouncementWatchDog 2026-08-17.
Detail: `lessons-detail.md` §L-025 (the six mechanisms by name, the original
wrong wording, the R2.2 scope argument in full)

## L-027 2026-08-21 tags: env|powershell|shell|pipeline|truncation|silent-failure hits: 2
Context: bench-claude-arms — two debugging rounds lost to one call shape, days
apart, nothing written down in between.
Pitfall: in PowerShell, `<native or interpreter command> | Select-Object -First
N` closes the pipeline after N objects and TERMINATES the upstream process
(exit 255, truncated output) — both halves of the damage point at the program,
not the pipeline. Hit 1 sent the author hunting a missing `__main__` guard; hit
2 was diagnosable only because the truncated tail happened to prove the script
had been fine.
Fix: never truncate a native/interpreter command INSIDE the pipeline — capture
then slice (`$out = & python x.py; $out | Select-Object -First 30`),
`Get-Content -TotalCount` for files, or redirect to a file; `Where-Object` /
`Out-String` consume the whole pipeline and are safe. CLOSED 2026-08-21 by
`hooks/ps_pipeline_close_guard.py` (PowerShell, ANNOTATE-only; suite 49/49;
backtest 100 fires / 3,412 payloads = 2.93%, 1.79/day — a publish and a test
run in the corpus were killed to shorten a screen). Why a closing was needed:
this was filed into lessons — the layer L-011 calls "essentially never" firing
— on the day L-011 was being edited two screens up; a named-tool-call trigger
that had hit twice belongs in a hook (L-011 hit 4). The corpus said ALL 160
hazards were PowerShell-tool commands, ZERO in `.ps1` files — opposite to the
EAP trap; "measure THIS trigger's surface" is the rule, not "the surface is
script files".
Detection: a pitfall whose diagnosis cost more than one round gets its ledger
entry at the moment it is fixed, not at project end (L-025 fix (d)).
Evidence: session (a local transcript) | digest L1042 L1045
L1047 L1066 | captured 2026-08-21
Detail: `lessons-detail.md` §L-027

## L-028 2026-08-22 tags: env|powershell|self-test|scalar-unwrap|silent-failure|verify hits: 1
Context: `tools/session-board/session-board.ps1 -SelfTest` reported 28/29 with
exactly ONE claude session live; the failing case was "found >=1 live claude
session" while its sibling "at least one has a locatable transcript" PASSED on
the same data.
Pitfall: PS 5.1 hands back a SCALAR when a function returns a one-element
array (`return $out` with `$out = @(one)`), and a scalar has no `.Count`, so
`$live.Count -ge 1` is `$null -ge 1` = false — right at n=0 and n≥2, wrong at
exactly n=1: a verdict that depends on the SIZE of its input, not its content
(L-019's family). The sibling line was already wrapped in `@()` and passed,
which was the tell; it was still misread once as "environment-dependent" in a
delivery report before the sibling gave it away.
Fix: wrap every collection you will `.Count` in `@()` at the point of use
(`$live = @(Get-LiveSessions)`), not only inside the producer — the unwrap
happens at return. The live control now SKIPs (third verdict, exit code
untouched) when no session is live, so the suite never teaches its reader that
it fails routinely (L-017 (b)).
Detection: a check that fails while an adjacent check consuming the same
collection passes — diff the two expressions before blaming the environment;
a suite that passes at n=0/n≥2 and fails at n=1.
Evidence: `tools/session-board/session-board.ps1` `Invoke-SelfTest` live
control, run 2026-08-21 23:25 with one live session (this one); fix 2026-08-22 |
captured 2026-08-22
Detail: `lessons-detail.md` §L-028

## L-030 2026-08-23 tags: verify|ui-testing|css|silent-failure|frontend|claim-calibration|third-party-upgrade hits: 1
Context: a NiceGUI + AG Grid editor. Excluded rows were supposed to dim; the
row carried the right class and the summary count updated, but nothing looked
different. Two more rules from the same block — cell line-height and header
font-weight — had been assumed working for the whole session.
Pitfall: all three rules were scoped `.ag-theme-balham .ag-cell { … }`, and
**AG Grid 33+ generates its theme class names** (`ag-theme-params-5`,
`ag-theme-batchEditStyle-3`, …). `.ag-theme-balham` never existed in the DOM,
so every rule under it matched NOTHING — silently, with no console error, no
build warning, and no visible symptom for the two rules whose effect nobody was
watching. The general shape: a CSS rule that matches nothing is
indistinguishable from a CSS rule that matches and is overridden, and BOTH are
invisible to static review. A vendor major-version bump is the usual trigger,
because theme/class naming is exactly the kind of thing that changes there.
Fix: scope to structural classes (`.ag-cell`, `.ag-row.row-excluded`) rather
than to a theme class, and — the part that actually catches it — **assert the
COMPUTED value, never the presence of the class**:
`getComputedStyle(cell).opacity === '0.4'` catches it;
`row.className.includes('row-excluded')` passes while the styling is dead,
because the class IS applied. Same discipline as L-010's settle-token rule, one
layer earlier: L-010 is "the computed value may be mid-transition", this is
"there may be no rule producing that value at all".
Detection: a styling change that "did nothing" while the state class is present;
`document.querySelector('.<theme-class-you-wrote>')` returning null; a
`getComputedStyle` value equal to the framework default rather than yours.
Evidence: session (a local transcript) | locator:
`hasBalhamClass: false`, `themeClasses: "ag-theme-params-5 …"`,
`cellLineHeight: "26px"` (framework default) before the fix vs `"18.6px"`
after | captured 2026-08-23
Detail: `lessons-detail.md` §L-030

## L-031 2026-08-26 tags: inherited-algorithm|staleness|fingerprint|derived-view|working-tree|graph-snapshot hits: 1
Context: graph-snapshot indexes the ~/.claude WORKING TREE. Its freshness gate
was copied faithfully from `ops/references/project-map.md` §6, which
fingerprints a git COMMIT because a project map describes committed state.
Pitfall: an inherited algorithm carries its original context's TIME SEMANTICS.
Fingerprinting HEAD cannot see an uncommitted edit, so the gate reported FRESH
while `skill-trigger-dict.md` sat ` M` — a structural file on disk already
differed from what the graph reflected, and INV-3 ("a STALE graph refuses to
answer") was silently void. Faithful reuse is precisely what hid it: nothing
looked wrong, because the copy was correct — for the other context.
Fix: the authoritative fingerprint became `corpus_digest`, a hash over the
content manifest the build already computes; git stays for provenance and for
naming what changed, but no longer decides trustworthiness. Regression cases
pin the exact failing case (dirty structural file => STALE) with both inputs
injectable — the first version read the real corpus off disk and the key case
passed for the wrong reason.
Detection: a staleness/freshness/cache-validity check whose fingerprint source
(commit, mtime, version tag) differs from what the artifact is actually built
FROM; any derived view over uncommitted state gated by a git ref.
Applied (fix held at first deliberate use): `gs_watchdog.evaluate()` was born
pure with both inputs injected, citing this card (2026-08-26, commit
`ef47d2a`) — its 6 smoke cases cannot be contaminated by the real corpus,
which is exactly the contamination this card records.
Evidence: session (a local transcript) | locator:
`references/graph-snapshot-phase-log.md` "INV-3 was not actually enforced";
regression: `tools/graph-snapshot/tests/test_smoke.py` staleness-gate cases |
captured 2026-08-26
Detail: `lessons-detail.md` §L-031

## L-032 2026-08-26 tags: false-negative|benchmark|calibration|ablation|instrument-check|measurement hits: 3
Context: graph-snapshot phase 1 produced four negative verdicts, each of which
would have changed a decision. Rule home: the global CLAUDE.md automated-gate
rule (calibrate with known-TRUE and known-false); this card is the measured
instance and its detection surface.
Pitfall: a negative measurement is a claim about the INSTRUMENT until the
instrument is checked. All four negatives were false: a 73.6% resolution rate
(three separate resolver/classification faults), "the new edge types did
nothing" (they were never wired into traversal), a 100%-recall ablation that
was tautological (seeds entered the read set by construction), and a "title
drift in the corpus" finding that was a citation-granularity mismatch. Every
one LOOKED like a result, and read as bad news about the corpus or the design
rather than about the measuring code.
Fix: before acting on any negative verdict, run the instrument on a known-TRUE
input, a known-FALSE input, and — where a scope boundary exists — a
known-EXCLUDED input; graph-snapshot prints all three on every build. For a
benchmark, an arm that cannot lose (or cannot win) measures nothing: check
what each arm is seeded with before reading its score.
Detection: a freshly written checker returning a uniform verdict on n>=3
inputs; a negative finding about an artifact nobody reproduced against the raw
source; an ablation arm whose construction implies its own score.
Recurrence: hit 2 (2026-08-26, the SAME SESSION that wrote this card, while
testing watchdog check 15) — the three-sided control suite returned uniform
silence TWICE, positive controls included; both times the fault was the test
harness, not the check: PS 5.1's pipe prepended a BOM that broke the hook's
stdin JSON parse (the fail-open except ate it), then `Set-Content -Encoding
utf8` BOM'd the synthetic status file and the same fail-open ate the read.
The Detection line above ("uniform verdict on n>=3 inputs") caught it both
times, so the card's own protocol found its own harness — the fix HELD.
Hardening shipped: check 15 reads utf-8-sig. A fail-open reader plus a
BOM-carrying writer is a silent-disable pair: probe it with a positive
control, not by reading the code. hits:2 routing (40-maintenance §2a): the
trigger is a task-shaped judgement; enforcement already lives at the named
rule home (global CLAUDE.md automated-gate rule) — layer matches the danger
moment, no new mechanism owed.
Recurrence: hit 3 (2026-08-26, gap-fill round 4) — the flip side of the same
card: not a harness fault this time but a ONE-SIDED TEST I wrote. A dict-block
parser truncated every block to "#"; its test asserted only ABSENCE ("does not
contain the next family's heading") and passed over the empty output. Caught
by inspecting the REAL manifest before shipping, not by any test. The card's
fix line already names the cure (a known-TRUE input); it was skipped at
authoring time — fix did NOT hold by itself, inspection held. Both assertions
now paired (presence + absence) in tests/test_smoke.py. Corollary worth the
reread: an extraction test needs a positive control exactly as much as a gate
does — "returns nothing bad" is satisfied by returning nothing.
Evidence: session (a local transcript) | locator:
`reports/2026-08-20-graph-snapshot-m3-adversarial-evaluation.md` (six
instrument defects, four false negatives); phase-log "a finding I RETRACTED";
hit 2: graph-snapshot phase-log Phase 2 checkpoint + commit `ef47d2a`;
hit 3: gap-fill round 4 phase-log bullet + the export-bundle feat commit |
captured 2026-08-26
Detail: `lessons-detail.md` §L-032

## L-033 2026-08-27 tags: gate-design|calibration|false-negative|verification|doc-hygiene|regex|claim-calibration hits: 1
Context: the skill's backlog file (then `FUTURE-WORK.md`, renamed
`literature-search-extract-FUTURE-WORK.md` the same day under the owner-first
basename rule in `40-maintenance.md` §3) recorded
"SKILL.md 現 261 行". True on 2026-07-12,
false from 2026-07-19 when the file was trimmed to 250, unnoticed for five
weeks — then a later session took it as a BASELINE and did arithmetic on it,
producing a second wrong number in a new document. Wrote `staleclaim.py` to
re-measure that claim shape so the convention would not depend on memory.
Pitfall: the checker passed **5/5 synthetic cases and then MISSED THE REAL
BUG**. Bound-detection asked "is there an upper-bound word within ±40 chars",
and the real sentence carries two numbers — `現 261 行，超過 250 行軟上限` — so
250's 「上限」 vouched for 261 from five characters away. Every synthetic case
had ONE number per sentence, so the flaw was **unreachable by construction**:
the suite could not have failed for this reason no matter how many cases it
held. A green calibration measured my imagination, not the instrument.
Fix: before trusting any green, **replay a REAL past failure out of git and
demand a FAIL** — `git show <old-sha>:<file>` into a temp dir and run the
checker at it. Structural fix: scope an adjacency keyword to the span between
NEIGHBOURING numbers, never a fixed character window. Both language forms
(zh 「行…上限」, en "lines … cap") are now permanent regression fixtures.
Generalises past this tool: adding cases to a suite whose cases all share a
simplification the real data lacks buys nothing — the fixture must come from
production, not from the author.
Detection: a brand-new checker reports clean on its first pass over real data;
or every case in the suite shares a shape ("one X per line") the wild does not.
Evidence: session (a local transcript) | locator:
`skills/literature-search-extract/verify/staleclaim.py` `is_bound()` +
selftest cases 6–8; positive control = replay of
`git show 5c77d1f:skills/literature-search-extract/FUTURE-WORK.md` → must FAIL
(that path is the file's name AT THAT COMMIT — do NOT "fix" it to the current
owner-first name, the replay would stop resolving)
| captured 2026-08-27
Detail: `lessons-detail.md` §L-033

## L-034 2026-08-27 tags: hooks|config|cross-session|outage|recovery|git-merge|settings-json hits: 1
Context: a peer session registered `hooks/branch_commit_guard.py` machine-wide.
The primary checkout was on a feature branch, so the file sat UNTRACKED there
while `settings.json` (carrying main's content) already registered it. Peer's
advice, which I verified and followed: delete the untracked copy to clear an
untracked-file collision, then `git merge main` re-materialises the tracked one.
Pitfall: **the delete is not atomic with the restore.** The merge ABORTED — on
three *unrelated* untracked files belonging to other sessions — so the file was
gone and the merge had not run. `settings.json` still pointed at it, so every
`Bash` and `PowerShell` call in EVERY session died at PreToolUse with
`can't open file ... branch_commit_guard.py`, **including the calls needed to
restore it**. Only the Write tool remained. Second finding, contradicting a
common assumption: **hooks are NOT snapshotted at session start** — a session
that began hours before the hook existed still executed it, so `settings.json`
is re-read live and a hook edit reaches running sessions immediately.
Fix: never delete a file `settings.json` references. To convert untracked →
tracked with NO window where the file is absent, use
`git checkout <branch> -- <path>` instead of delete-then-merge. If a hook file
genuinely must go, **unregister it in settings.json FIRST**. When a merge is the
restore step, confirm it will actually run (`git merge --no-commit --no-ff`,
or clear every collision) before removing anything it depends on. Recovery of
last resort: the Write tool, with a **fail-CLOSED** stub — an unguarded window
is the exact failure the guard existed for, so a broken tool beats a silently
open one.
Detection: `can't open file '...hooks/*.py'` on every shell call, in every
session at once; `git status` showing a registered hook as `??`.
Attribution (corrected 2026-08-27, and the correction is itself the lesson):
the guard was authored/registered by session `dazzling-dijkstra-9c5682-17`,
whose advice I followed; the file was RESTORED by a different session,
`223b04ef` — the same session whose commits caused incidents #1 and #2. I
thanked the wrong session in writing, twice, because I assumed the session that
messaged me was the session that acted. In a shared tree, **the party who tells
you about a change is not necessarily the party who made it**; attribute from
the record (`git log`, the artifact's own log), never from who is in the
conversation. Caught by `dazzling-dijkstra-9c5682-17` correcting a mistake that
flattered it.
Evidence: session (a local transcript) | locator: attribution
recorded in `hooks/branch_commit_guard.py` docstring on main (`85774aa`, line
~49: "blocked until a local session restored the file from main into the
working tree"); my echoed-payload deny is logged there as FP-2, a false
positive, not a true block; outage ~01:05–01:08 2026-08-27 | captured
2026-08-27
Detail: `lessons-detail.md` §L-034

## L-035 2026-08-27 tags: instrument-check|calibration|gate-design|spec-drift|simulation|routing|false-positive|tooling hits: 1
(Renumbered 2026-08-27 from a duplicate "L-033" minted in parallel on the other
branch; the staleclaim entry keeps L-033 — `40-maintenance.md` §3 cites it by
number, this one had no external citation.)
Context: scientific-research-guide's routing linter (built 2026-08-26) reported
four keyword-overlap findings; a user ruling deferred them to a separate
triage. The triage found that two of the four described loads the documented
system never performs.
Pitfall: **two-sided calibration validates the implementation against its own
MODEL, not the model against the SPEC.** `routing_sim.load_set()` replayed
Gate A Step 0 as a FLAT scan of every manifest row, while both `SKILL.md` and
`_routing.md` document a TWO-LEVEL scan (base rows always; a sub-profile only
when its parent domain matched). The linter read the simulator as ground truth,
so it reported overlaps on rows that no prompt matching the containing keyword
can reach. Every control passed the whole time — seeded fixture and live tree
both fired exactly as documented — because the instrument was correct about its
own model and the model was wrong. L-032 is the same family from the opposite
direction (a NEGATIVE verdict is a claim about the instrument); its prescribed
cure, a known-TRUE plus known-FALSE control, was RUN here and could not catch
this, because both controls live inside the wrong model. The findings were then
written into a status file and a ticket as real defects, and the ticket offered
only two remedies, both edits to the ARTIFACT — following it would have recorded
an intent nobody held (that a topological-insulator process note belongs on a
silicon-photonics V-groove question) in order to silence a non-defect.
Fix: when an instrument SIMULATES a documented rule, state in its docstring
which levels/rungs it models and which it does not, and make the consumer that
REPORTS findings apply the unmodelled part instead of treating the simulator as
truth. Here `routing_sim.rung1_reachability()` is tri-state — `None` means the
manifest cannot decide, and it REPORTS rather than suppresses (downgrade-and-
forward, never veto) — and `profile-lint.py` applies it while `load_set()`
deliberately keeps the flat model for its other consumer, a re-run SELECTOR
whose safe error is the opposite. Two consumers of one primitive wanting
opposite errors: keep the primitive at the selector-safe setting and put the
judgment in the reporter.
Detection: a finding whose remedy list contains only changes to the ARTIFACT and
none to the instrument. Before acting, replay one finding by hand against the
SPEC PROSE rather than against the tool — if the spec has a gating clause the
tool's docstring does not mention, every finding of that class is suspect. The
two texts are usually adjacent and were never diffed.
Evidence: session (a local transcript) | locator: commits
`060983d` (matching rule) and `db67a01` (reachability + regression fixture),
merge `b1c37d2`; `skills/scientific-research-guide/STATUS.md` entry
"2026-08-26/27 routing-anchor triage", table "flat vs gated" (2 of 14 eval
prompts differ, and those two ARE findings 1 and 4) | captured 2026-08-27
Detail: `lessons-detail.md` §L-035

---
## L-036 2026-08-28 tags: testing|contract-drift|cross-boundary|api|gate-design|verify|silent-failure hits: 1
Context: media-fetch-pipeline Phase Z2. A user reported the settings panel
saying the engine was ready and the feature unusable in one viewport, and asked
whether state was out of sync. It was not -- the single source of truth held
throughout. Auditing the PROJECTION instead turned up seven contradictions, one
of which had shipped past 2,033 green tests.
Pitfall: **both sides of a contract were tested and the JOIN was not.** The
server emitted `action="pick-translation"`; a Python test asserted exactly that
string; the renderer's TypeScript union did not contain the name, so its label
ternary and its dispatch both fell through to the branch for a DIFFERENT action
-- and a user told to pick one of the models they already had got a button that
opened a browse-for-a-NEW-folder dialog. Neither suite was wrong about its own
side. Nothing read the two together. Four more of the same shape in the same
module: `optional` declared with a docstring promising that the panel would
never render an opt-in capability as a fault, defaulted to the wrong value, set
by neither builder and read by no renderer; `open-home` in the union, emitted by
no branch; `model_unusable` in the enum, produced by no branch; `headline`
computed for two capabilities and rendered for one, so one of them had never
reached a screen. **A field whose docstring describes a guarantee nothing
implements is worse than no field**, because the docstring is read as a
description of behaviour.
Fix: a CHECK, not a rename. A test parses the action literals out of the server
module and the union out of the type declarations and asserts set equality **in
both directions** -- a name added on one side only now fails, and so does a name
in the union that nothing emits. It skips with a reason when the other side's
sources are absent from the checkout. Cheap (one regex per side), and it is the
only artifact in the repo that reads both files.
This is L-006's prescription arriving as code: L-006 said reconstruct the
intended model as an artifact and check the code against it, which is what the
audit document did by hand. The generalisation is that when both sides are
MACHINE-READABLE, the reconstruction should be executable -- a hand-written
model has to be re-read to stay true, a parsing test fails on its own.
Detection: any enum, union, or action-name vocabulary that exists in two
languages. Grep each side's literals, diff the sets, and expect the diff to be
non-empty the first time.
Evidence: session (a local transcript) | commits `d0104b7`,
`3412885`, `49b857f` | model: `media-fetch-pipeline/docs/asr-readiness-view-model.md` §7
| project journal P-57.

## L-037 2026-08-28 tags: verify|test-design|ui-testing|visual-gate|frontend|claim-calibration hits: 1
Context: same session. Six assertions had just been written for one defect
class -- the same sentence printed twice in one viewport under two labels --
and the repair for a NEIGHBOURING defect reintroduced it. Every one of the six
stayed green.
Pitfall: **a suite of absence-assertions cannot see a redundant presence.**
Each of them read `expect(region).not.toHaveTextContent(X)`; the recurrence was
a correct sentence appearing a second time next to the first. Nothing was
missing, nothing was wrong, and no assertion in that class can be phrased to
catch it without knowing in advance which string would be duplicated. It was
found by rendering the page out-of-process and LOOKING at the image.
The global rule already says green tests prove the data path and not the
picture. What this adds is the mechanism, so the rule can be applied on purpose
rather than as a slogan: for a surface whose defect class is "two things that
disagree" or "one thing said twice", the assertions are necessarily written
about STRINGS, while both defects are properties of the LAYOUT -- adjacency and
repetition -- which no string assertion holds.
Fix: when the deliverable is a rendered surface and the defects are relational,
budget one out-of-process render per repair round and read it before believing
a green suite. Playwright headless into a PNG, delivered via `SendUserFile`,
costs one command and caught what six purpose-written assertions could not.
Pair it with the calibration rule that already exists -- break each new
assertion's fix and confirm the assertion fails, and keep one deliberate
POSITIVE CONTROL that must stay green -- because that pass proved the six were
sound, which is exactly why their blind spot was invisible.
Detection: a repair that removes a duplicated string and then has to put the
information back somewhere. That put-back is the moment the duplication
returns, and it returns in the region the assertions do not scope.
Evidence: session (a local transcript) | commit `3412885` |
project journal P-58 | the render that caught it: three panel states at
1180x1400 @2x.

## L-038 2026-08-29 tags: hook-design|gate-design|false-positive|identity-by-path|deny-message|prompt-injection|subagent|asset-property hits: 1
Context: transcript_read_guard.py denied subagent Reads of WebFetch-cached
arXiv PDFs. The cache lives under `projects/<slug>/<sid>/tool-results/` — the
same root as live transcripts — and the hook's identity test was "under a
corpus root AND >128KB ⇒ session record". Two subagents were hit: one fully
blocked, one bypassed via pdftotext, and both classified the deny message as a
prompt-injection attempt.
Pitfall: two distinct mechanisms, one incident. (1) **Identity-by-path rots
the moment the directory gains a new tenant.** The harness started caching
WebFetch downloads inside the transcript tree; "location = identity" silently
became false (36 non-record files >128KB at audit). Sharper: the docstring
DECLARED "asset property, not a path instruction" while the code implemented a
path prefix test — a declared invariant is not the implemented one, and the
declaration made the gap invisible to review. (2) **A deny message that
asserts the identity of an arbitrary file, claims "Policy:" authority, and
instructs the reader to go read another directory is shape-identical to prompt
injection.** A well-calibrated subagent that just fetched a PDF and is told
"this is 3.5 MB of session record; Policy: …; read <redlined dir> instead"
SHOULD refuse — it holds a falsifiable counter-fact. The better the agents,
the worse this failure mode gets.
Fix: (1) identify the asset by SHAPE (`*.jsonl`, digest `*.md` under
`digests/`), keep the root only as scope; name the invalidating event in
review-when ("a new tenant class appears under a corpus root"). (2) Deny-
message contract, now asserted by test: constraint + retry mechanics only —
name the hook as the source, no authority claims, no read-elsewhere
imperatives, nothing the reader can falsify. Loosening the gate shipped with
the regression case reproducing its original catch (big .jsonl unbounded →
deny) per the global loosening rule.
Detection: a hook denial reported as an "injection attack" by a subagent; or
any guard whose deny fires on a file the agent itself just created/fetched.
Evidence: hooks/tests/test_transcript_read_guard.py (11 hermetic + 6 live
cases); registry entry "compact recovery" evidence line 2026-08-29; diagnosis
delivered cross-session by the SSLD front-end research session (W1/W2 events).

## Archived (folded into another file, or retired)

> Folded ≠ deleted, and ≠ out of reach. The full record of every entry below is
> in `references/lessons-detail.md` under the same `## L-nnn` heading, and these
> lines stay IN this file on purpose — the pre-task grep still hits them, so the
> mechanism keywords are repeated here deliberately rather than trimmed. What
> folding changes is the unfolded COUNT (the hook counts `## L-\d+` above this
> heading) and the reading weight, not the searchability.
>
> Fold criterion used 2026-08-27: `hits: 1`, the fix is carried by a HOOK rather
> than by recall, and global `CLAUDE.md` does not cite the entry by number. An
> entry with a climbing `hits:` is never folded — that is the live evidence a fix
> is not working. Restore an entry to the unfolded region the moment it recurs.
>
> Second pass, same day (after the two branch merges brought both sides' cards
> together and the live count reached 32): same `hits: 1` bar and no by-number
> CLAUDE.md citation, but the carrier is a durable RULE FILE rather than a hook
> — or the mechanism the card warned about is retired outright.

- **L-002** (2026-07-12 · verify|docs|design|evidence) — PSM/delta-doc failure
  modes: normative content delegated via 「沿用」 to an ARCHIVED base under a
  sole-basis claim; version bump without a consistency pass; claim strength >
  evidence strength; semantic compression inverting the surviving half of a
  two-proposition finding. Folded 2026-08-27 (2nd pass): (3)+(4) live in
  `30-judgment.md` R2 claim-calibration, (1)+(2) in product-design-thinking's
  sole-source contract (`document-ladder.md` §4), the trigger widening in
  `skill-trigger-dict.md`. Promote back on recurrence. Full record:
  `lessons-detail.md` §L-002.
- **L-003** (2026-07-12 · interop|cross-platform|skills-sync|env) — raw skill
  copies across agent homes (`~/.agents`, `~/.codex`): staleness (reviews filed
  against outdated copies) + silent drift (target-side patches overwritten by
  the next naive re-sync). Folded 2026-08-27 (2nd pass): the mechanism is
  RETIRED — the interop layer no longer raw-copies at all; `interop/README.md`
  owns the compile/curate contract. Full record: `lessons-detail.md` §L-003.
- **L-004** (2026-07-12 · rules-editing|dict-sync|config-change|docs) — "update
  the dicts" executed as "update the files NAMED dict"; the index surface of a
  rule file is EVERY place that routes to it — enumerate by grep, never recall.
  Folded 2026-08-27 (2nd pass): the dict-sync corollary in `40-maintenance.md`
  §2 names OPS.md's routing table explicitly. Promote back on recurrence. Full
  record: `lessons-detail.md` §L-004.
- **L-033 / L-034 / L-035 are NOT folded** — the 2026-08-27 entries stay live:
  L-033 staleclaim (cited by number from `40-maintenance.md` §3), L-034
  registered-hook outage, L-035 routing-linter spec-drift (renumbered from a
  duplicate "L-033" minted in parallel on the other branch).
- **L-013** (2026-08-12 · env|browser-pane|crash|third-party-content|forensics) —
  a third-party page in the in-app **Browser pane** can kill the **Electron GPU
  child** (`exitCode 101457950`), wedge the main process and lose the in-flight
  turn of EVERY session; no relaunch. Folded 2026-08-27: forensics and the pane
  allowlist are enforced by `hooks/browser_pane_scope_guard.py`, and the standing
  rule of thumb (in-app pane = localhost / your own build / what the user wants to
  see; third-party or bot-challenged pages go WebFetch → claude-in-chrome →
  headless Playwright; never retry a URL that preceded a pane or app death) is
  reproduced here so a `preview_start` grep still lands. Promote back on a second
  independent incident. Full record: `lessons-detail.md` §L-013.
- **L-026** (2026-08-21 · measurement|benchmark|experiment-design|confound|apparatus)
  — things filed under "setup" that were INSIDE the experiment: the enforcement
  mechanism moves the outcome, a **platform cap correlated with the treatment is a
  confound not noise**, your own `settings.json` is APPARATUS, coupling collection
  to evaluation decides what you can still fix, and a pre-registered rule needs a
  "none of the above" branch. Folded 2026-08-27: the operative half ("measure the
  instrument before instrumenting with it") is the standing rule that L-025 and
  L-032 both carry live, and the rest is a single bench post-mortem. Full record:
  `lessons-detail.md` §L-026.
- **L-029** (2026-08-23 · env|shell|bash|**msys**|path-conversion|windows-native|silent-failure|hang)
  — the Bash tool IS Git Bash/MSYS2, which rewrites argv for native Windows exes:
  **`cmd /c` → `C:/`**, **`taskkill /PID` → `C:/Program Files/Git/PID`**. A Windows
  SWITCH is indistinguishable from a POSIX path at that layer; quoting does not
  help. `cmd` handed `C:/` starts an INTERACTIVE shell that hangs for the whole
  timeout. NOT one of L-024's three. Escapes: route through the **PowerShell tool**,
  or `MSYS_NO_PATHCONV=1`, or a doubled slash (`//c`, `//PID`). Folded 2026-08-27
  with a caveat worth keeping in view: `hooks/shell_transport_guard.py` rule (3)
  only **ANNOTATES** — the deny is deferred pending a corpus backtest — so this is
  the weakest of the three folds, and the keywords above are spelled out precisely
  because the hook will not stop anyone. Full record: `lessons-detail.md` §L-029.
