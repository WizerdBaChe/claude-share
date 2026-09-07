# Lessons — generated index of ops/lessons/ (at the source; a guard there blocks hand-edits — this shipped copy carries no such enforcement)

Every card below is a PROJECTION of one intake record `ops/lessons/L-nnn.md` — the record
is the authoritative, lossless text; the card is capped so a pre-task grep hit can be read
in one screen. A new lesson, at the source, is captured with the intake tool's own `add`
step after drafting a file with front matter `what` (中文 (English)) + `tags`, a `## Record`
block with `locator:`, and `## Context` / `## Pitfall` / `## Fix` sections (+ optional
`## Detection`, `## Narrative`) — that intake tool and the per-lesson record tree it writes
into are both source-side and do not ship here; an adopter keeping their own such ledger can
reuse the card shape by hand.

Recurrence (the "same symptom a 2nd time" rule): grep this file for the MECHANISM first — at
the source, a hit is then logged with the intake tool's own `event` step; a card whose `hits`
reaches 2 is routed through `ops/40-maintenance.md` §2a (fold into the target file named in
its `state:`). Full text, recurrences and provenance live behind the `Record:` path on each
card — informational here, since the `ops/lessons/` tree it names does not ship in this repo.
generated-at: 2026-09-07T11:52:55+08:00   records: 56   (the source line also carries a `generated-from:` sha256 over the `ops/lessons/` record tree; that tree does not ship here, so the receipt is dropped rather than published as a value nothing in this copy can check)

## L-001 2026-07-10 tags: dispatch|cost-cap|hooks hits: 1 state: folded→hooks/model_cap_guard.py
what: L-001 舊帳本搬入 (legacy import, folded): a cost cap enforced at DISPATCH time does not survive a `SendMessage` resume: th
Context: a cost cap enforced at DISPATCH time does not survive a `SendMessage` resume: the resumed subagent inherits the MAIN session's model (`cache_miss_reason model_changed`, sonnet → fable), and no hook event can intercept it — PreToolUse fires on SendMessage with no model/resume field, SubagentStart cannot block, no AgentResume event exists (verified against the hooks docs 2026-07-10). Folded 2026 …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → hooks/model_cap_guard.py
Record: ops/lessons/L-001.md

## L-002 2026-07-12 tags: verify|docs|design|evidence hits: 1 state: folded→30-judgment.md
what: L-002 舊帳本搬入 (legacy import, folded): PSM/delta-doc failure modes: normative content delegated via 「沿用」 to an ARCHIVED
Context: PSM/delta-doc failure modes: normative content delegated via 「沿用」 to an ARCHIVED base under a sole-basis claim; version bump without a consistency pass; claim strength > evidence strength; semantic compression inverting the surviving half of a two-proposition finding. Folded 2026-08-27 (2nd pass): (3)+(4) live in `30-judgment.md` R2 claim-calibration, (1)+(2) in product-design-thinking's s …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → 30-judgment.md
Record: ops/lessons/L-002.md

## L-003 2026-07-12 tags: interop|cross-platform|skills-sync|env hits: 1 state: folded→interop/README.md
what: L-003 舊帳本搬入 (legacy import, folded): raw skill copies across agent homes (`~/.agents`, `~/.codex`): staleness (review
Context: raw skill copies across agent homes (`~/.agents`, `~/.codex`): staleness (reviews filed against outdated copies) + silent drift (target-side patches overwritten by the next naive re-sync). Folded 2026-08-27 (2nd pass): the mechanism is RETIRED — the interop layer no longer raw-copies at all; `interop/README.md` owns the compile/curate contract. Full record: `lessons-detail.md` §L-003.
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → interop/README.md
Record: ops/lessons/L-003.md

## L-004 2026-07-12 tags: rules-editing|dict-sync|config-change|docs hits: 1 state: folded→40-maintenance.md §2
what: L-004 舊帳本搬入 (legacy import, folded): "update the dicts" executed as "update the files NAMED dict"; the index surface
Context: "update the dicts" executed as "update the files NAMED dict"; the index surface of a rule file is EVERY place that routes to it — enumerate by grep, never recall. Folded 2026-08-27 (2nd pass): the dict-sync corollary in `40-maintenance.md` §2 names OPS.md's routing table explicitly. Promote back on recurrence. Full record: `lessons-detail.md` §L-004.
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → 40-maintenance.md §2
Record: ops/lessons/L-004.md

## L-005 2026-07-30 tags: handoff|carried-claims|verification|docs|registry|volatile-facts|numeric-constants hits: 4 state: live
what: L-005 舊帳本搬入 (legacy import): Prism UAT-R3.5 — a claim true when written ("batch-1 failures not yet re-verifie
Context: Prism UAT-R3.5 — a claim true when written ("batch-1 failures not yet re-verified on the real machine") survived THREE handoff documents after it became false; a copied verdict ("ResearchGate will keep failing, that is correct") shipped as an instruction and was refuted in one step.
Pitfall: a claim copied from the previous round READS like an established fact — the same authoritative voice as the measurements around it. Prose does not decay loudly, and the receiver cannot tell "I verified this today" from "the last document said this". Registry rows are worse carriers than prose (hit 3); NUMBERS are the worst (hit 4): a constant, or a PRODUCT / RANGE / TOTAL inside an equation, has no slot for a hedge, reads as measured by default, and fuses several provenances into one token with no visible seam.
Fix: (1) carry a claim forward only by re-deriving it in-session or marking it INHERITED with the round it came from — never restate it flat. (2) Make the build check what it can (Prism DRIFT-01 `check_architecture.py::carried- design-anchor` asserts every deferred-design anchor still resolves; prose decays because nothing fails when it does). (3) Any number a design or conclusion RESTS ON carries `measured-here` / `measured-elsewhere(what, when)` / `estimated` / `inherited-default`, and anything not `measured-here` is re-measured before a conclusion is published on it — ask of any derived figure which inputs went in and whether they were all current at the same moment (now `30-judgment.md` R …[record]
Detection: every hit-4 instance was found by READERS doing something else; the verifier that checked the cited file EXISTS caught none — file existence is not the check (L-025).
Record: ops/lessons/L-005.md

## L-006 2026-07-31 tags: skill-design|review-methodology|checklist|scope-gating hits: 2 state: live
what: L-006 舊帳本搬入 (legacy import): FSM/state-machine and cross-boundary contract-drift lenses added to the deep-che
Context: FSM/state-machine and cross-boundary contract-drift lenses added to the deep-checklist skills (commits afb0c28, 19b00df).
Pitfall: checklist skills enumerate only code-visible defects; defect classes that live in DESIGN SEMANTICS (state machines, mirrored FE/BE contracts, twin-implemented rules, doc claims) have no grep target — and both naive fixes fail: an always-on section taxes every review, duplicating the topic into the quality AND security skill creates rule drift. Fix (pattern, folded into code-review-deep-checklist Mode A §10/§11 + Mode B lenses, security-deep-checklist Mode A §9): (1) reconstruct-and-compare — rebuild the intended model as a REPORT ARTIFACT, then check code against it; (2) every such section carries an explicit trigger gate and records skips, depth capped (top 1–3 units); (3) single-o …[record]
Fix: (legacy card had no Fix field — see Narrative)
Record: ops/lessons/L-006.md

## L-007 2026-07-31 tags: rules-editing|structural-edit|verify hits: 1 state: live
what: L-007 舊帳本搬入 (legacy import): inserting section 10 into single-review.md; a misplaced Edit insert followed by
Context: inserting section 10 into single-review.md; a misplaced Edit insert followed by a PARTIAL revert left two "## 10" headers, one truncated.
Pitfall: insert-then-revert sequences on numbered checklist files corrupt structure silently — each individual edit "succeeded"; the author pass did not catch it, only config-self-audit's section-header listing did.
Fix: after any structural edit to a sectioned rules file, scan headers (`Select-String '^## '`) and verify uniqueness + order BEFORE commit; prefer append-at-end or a single scripted move over incremental insert+revert. This is also the standing reason config-self-audit runs after every skill edit.
Record: ops/lessons/L-007.md

## L-008 2026-07-31 tags: rules-editing|naming|scale-labels|ux|project-artifacts|uat hits: 3 state: live
what: L-008 舊帳本搬入 (legacy import): the ops-relaxation scale (05-authority §2). The user read "L2" as a permission/s
Context: the ops-relaxation scale (05-authority §2). The user read "L2" as a permission/strictness level; "L2/L3" was also reused in 70-evolution for a different scale.
Pitfall: (a) a bare scale label carries no direction — readers fill it with the dominant convention (ASVS: higher = stricter), inverted here; (b) label famines — reusing a family for a second scale makes grep and recall collide. Definitions live in one file; labels travel without them.
Fix: scale-label qualifier at every point of use (40-maintenance §3); direction + precedence paragraphs in 05-authority §2; gate-ask glosses; 70-evolution renamed "(layer 2)/(layer 3)". Governing principle: a label carries enough qualifier to resolve its referent at EVERY point it is cited; `~/.claude/LABEL-REGISTRY.md` is the one definition table.
Record: ops/lessons/L-008.md

## L-009 2026-08-05 tags: env|browser-pane|screenshot|verify|diagnosis hits: 1 state: live
what: L-009 舊帳本搬入 (legacy import): ~1 month of intermittent `computer{action:"screenshot"}` timeouts in the in-app
Context: ~1 month of intermittent `computer{action:"screenshot"}` timeouts in the in-app Browser pane, repeatedly misdiagnosed as permission/sandbox. Actual state: `document.visibilityState === "hidden"` while every CDP read kept working.
Pitfall: (a) the tell was present from the first occurrence — ONE tool in a group failed with a TIMEOUT while its siblings stayed green; a denied permission returns a refusal, not a timeout, so asymmetry inside a tool group rules out permissions before any investigation starts. (b) The first write-up asserted the mechanism as fact by quoting the tool's own error string — a quoted error string is the tool author's assertion; record it at correlation level.
Fix: detection-first rule in global CLAUDE.md; enforcement moved 2026-08-08 to `hooks/ui_verify_guard.py` (denies the screenshot until a `visibilityState` probe ran — why a hook and not a line: L-011). Premise corrected 2026-08-16: `hidden` is this machine's STEADY STATE (the foreground is not commandeerable; a fresh pane is born hidden), so pixels route OUT-OF-PROCESS BY DEFAULT and the probe's remaining job is the discriminator — `visible` + timeout is a DIFFERENT fault. Premise: `environment.md` "Browser pane"; recipes: `ops/references/browser-pane-pixel-route.md`.
Record: ops/lessons/L-009.md

## L-010 2026-08-08 tags: env|browser-pane|verify|ui-testing|flaky|css hits: 1 state: live
what: L-010 舊帳本搬入 (legacy import): browser-pane UI verification — hover/focus a control, then read `getComputedStyl
Context: browser-pane UI verification — hover/focus a control, then read `getComputedStyle` against a design token.
Pitfall: `getComputedStyle()` during a CSS transition returns the INTERPOLATED mid-flight value, and the MCP round-trip is non-deterministic, so the failure is FLAKY, not stably wrong — the same code passes and fails across runs and sends the reader to debug correct code; the obvious fallback (a screenshot) is what L-009 takes away. Measured (`ui-state-probe` verify.mjs, 5s transition): hover-then-measure never reaches the target; finishing animations first does, 3/3.
Fix: (1) settle before measuring — `el.getAnimations({subtree:true}).forEach(a => a.finish())` is SYNCHRONOUS; infinite keyframes take an injected `transition:none;animation-duration:0s` stylesheet; (2) prefer asserting STATE (`data-state`, `aria-expanded`, class flips) over a rendered pixel value; (3) enforcement `hooks/ui_verify_guard.py` denies a `javascript_tool` call carrying `getComputedStyle` with no settle token; (4) the out-of-process tool: AssetVault `ui-state-probe` (utility/node).
Record: ops/lessons/L-010.md

## L-011 2026-08-08 tags: rules-design|enforcement|hooks|layering|omission|harness hits: 4 state: live
what: L-011 舊帳本搬入 (legacy import): deciding where to put the L-009/L-010 rules so they actually fire (user question
Context: deciding where to put the L-009/L-010 rules so they actually fire (user question: can CLAUDE.md's routing really reach OPS and lessons?).
Pitfall: the three rule layers have very different firing guarantees, and a rule written into the wrong one reads as durable and is dead. `ops/lessons.md` fires only when something greps it; `ops/*` only when CLAUDE.md's project-operations clause routes there; global CLAUDE.md is always in context but fires only on a trigger-word match — unreliable for rules that must fire MID-MEASUREMENT, when the agent is already confident (L-009 recurred for a month under exactly such a line).
Fix: choose the layer by TRIGGER SHAPE, not importance — a named tool call with inspectable input → PreToolUse hook (deny beats warn); a task-shaped judgement → CLAUDE.md conditional rule; "someone is already investigating this topic" → lessons.md, as the detail the shorter layers point AT. When a hook carries the enforcement, the CLAUDE.md line stays as the explanation the denial cites, and both name the lessons entry. FOURTH SHAPE, omission (hit 2): a rule whose violation is "the step never happened" generates no event — P1 gate the SUBSTITUTE commission (PreToolUse on the substitute's tools), P2 make the ABSENCE greppable (a literal marker a sweep enumerates), P3 gate at the event th …[record]
Record: ops/lessons/L-011.md

## L-012 2026-08-11 tags: verify|evidence|claim-calibration|delivery|self-review|polysemy|granularity|audit-record hits: 4 state: live
what: L-012 舊帳本搬入 (legacy import): harness context-budget work (E1/E4/T-007). Four over-claims in one task, all cau
Context: harness context-budget work (E1/E4/T-007). Four over-claims in one task, all caught, none by re-reading the text that contained them.
Pitfall: PROXY PROMOTION — a proxy is measured, then spoken about in the voice of the thing it stands for (bytes → "tokens paid"; one component tested → "the gate is broken"; a probe with the same config → "this file works"; a count recalled → wrong). R2's claim-calibration duty did not stop it because it is executed by the author, on the author's own sentences, while still holding only the proxy — re-reading re-derives the claim from the same evidence and it looks true again.
Fix: (1) NAME THE SUBSTITUTION in the sentence, not a hedge ("bytes, not tokens"); (2) before "X works", ask whether the evidence could have come out differently for the specific artifact; (3) when load-bearing, build the disagreeing artifact ON PURPOSE — the only fix with a recorded catch (4/4 here, 3/3 in L-015, 0 for the phrasing fixes), now a close-out step (`50-coach.md` C11 q4). Companion example: `30-judgment.md` R2.
Detection: an action taken for an UNRELATED reason produced an output that could disagree.
Record: ops/lessons/L-012.md

## L-013 2026-08-12 tags: env|browser-pane|crash|third-party-content|forensics hits: 1 state: folded→hooks/browser_pane_scope_guard.py
what: L-013 舊帳本搬入 (legacy import, folded): a third-party page in the in-app **Browser pane** can kill the **Electron GPU ch
Context: a third-party page in the in-app **Browser pane** can kill the **Electron GPU child** (`exitCode 101457950`), wedge the main process and lose the in-flight turn of EVERY session; no relaunch. Folded 2026-08-27: forensics and the pane allowlist are enforced by `hooks/browser_pane_scope_guard.py`, and the standing rule of thumb (in-app pane = localhost / your own build / what the user wants to see; …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → hooks/browser_pane_scope_guard.py
Record: ops/lessons/L-013.md

## L-014 2026-08-12 tags: agents|subagent|tools|capability|skills|silent-failure|config hits: 1 state: folded→integrity-sweep.md
what: L-014 舊帳本搬入 (legacy import, folded): `tools:` is an ALLOWLIST and `Skill` is a tool: a "read-only" list written again
Context: `tools:` is an ALLOWLIST and `Skill` is a tool: a "read-only" list written against one axis (write access) silently cuts every axis it intersects — skill invocation, search, MCP, the agent's own verification path. Folded 2026-08-31: detection is executable in `integrity-sweep.md` check 1 (`grep -L 'Skill' agents/*.md` must be empty) and every `agents/*.md` cites the entry inline. Promote back on …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → integrity-sweep.md
Record: ops/lessons/L-014.md

## L-015 2026-08-12 tags: verify|claim-calibration|design-docs|self-review|scope-gating hits: 1 state: folded→30-judgment.md
what: L-015 舊帳本搬入 (legacy import, folded): claim calibration silently scoped to the EVIDENCE sections while the design rati
Context: claim calibration silently scoped to the EVIDENCE sections while the design rationale asserted "X and Y are the same" unchecked; a deferral with no blast radius left two queries dead; a quantity and its acceptance threshold, both quoted in the same session, were never multiplied together. Also: six findings in one self-audit predicts MORE remaining, not a finished sweep. Folded 2026-09-06 (4th pas …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → 30-judgment.md
Record: ops/lessons/L-015.md

## L-016 2026-08-15 tags: verify|hooks|checks|acceptance-eval|config|silent-failure|self-audit hits: 1 state: folded→tools/ops-health-test/
what: L-016 舊帳本搬入 (legacy import, folded): a check that CANNOT fail is indistinguishable from one that passes: predicate sa
Context: a check that CANNOT fail is indistinguishable from one that passes: predicate satisfied by the wrong thing (prose mention vs the value shape `ops-relaxation: L1`), nothing invokes it, or its subject retired; silence is the healthy signal for a nudge, a status report and an unrun eval alike. Folded 2026-08-31: carried by the global CLAUDE.md automated-gate rule (known-TRUE + known-false calibration …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → tools/ops-health-test/
Record: ops/lessons/L-016.md

## L-017 2026-08-16 tags: rules-design|checklists|security|invariants|verify|remediation hits: 2 state: live
what: L-017 舊帳本搬入 (legacy import): NTUMail2TG — security prerequisite EP-1 written as "`D:\` must not grant BUILTIN
Context: NTUMail2TG — security prerequisite EP-1 written as "`D:\` must not grant BUILTIN\Users FullControl"; the user declined (drive root; sandbox accounts work there); it sat NOT SATISFIED across two phases while the risk was already eliminated another way (binary moved to an owner-only directory).
Pitfall: the item named a LOCATION, not the PROPERTY (SI-4: "the autostart directory is not writable by broad principals"), so it could not recognise the other valid fix. Consequences: a HIGH finding claimed live after its attack path was cut, and a permanently-red item teaches the reader the checklist can be ignored. Instruction-shaped controls read more concrete than property-shaped ones; that concreteness IS the failure mode (now global CLAUDE.md: write the invariant as a property of the asset).
Fix: (a) checklist item = a test of the property; (b) a declined remediation converts into an accepted risk carrying its compensating control + revisit conditions — every line reads "satisfied" or "known and decided"; (c) prefer a compensating control that cannot decay (the leaf-dir ACL was declined because `publish.ps1` recreates the dir — detection via git chosen over prevention).
Detection: for each red item ask "would this notice a DIFFERENT valid fix?"; an item the user declined twice is a specification problem, not compliance.
Record: ops/lessons/L-017.md

## L-018 2026-08-16 tags: testing|harness|isolation|forensics|logging|silent-failure hits: 1 state: live
what: L-018 舊帳本搬入 (legacy import): NTUMail2TG offline harness drives the REAL engine with a fake mail source and a
Context: NTUMail2TG offline harness drives the REAL engine with a fake mail source and a fake Telegram sink; `Logger` wrote to a hard-coded path, so every test run appended synthetic deliveries to the user's operational `bridge.log`, `[security]` channel included.
Pitfall: the fakes covered the two things that FELT external (network, mailbox); the log stayed pointed at production because the question asked was "what does this code READ?" A test double gets built at the boundary already under consideration, and by default that is the input side. Nothing fails; the contamination lands on records that already existed.
Fix: `Logger.RedirectTo`, one-way and SINGLE-USE (a log path that can be swapped at will is itself a way to make records disappear); the harness redirects before anything can log, and a test asserts a second call throws.
Detection: enumerate what the code under test WRITES — logs, state files, registry, caches, notifications, telemetry — and require each redirected or asserted-unchanged; cheap positive check: the production artifact's byte length is identical across a full harness run (4653 → 4653).
Record: ops/lessons/L-018.md

## L-019 2026-08-16 tags: verify|acceptance-eval|parsing|subagent-dispatch|interop|gate-design|silent-failure hits: 6 state: live
what: L-019 舊帳本搬入 (legacy import): acceptance gates over model output — JSON extractor, evidence-anchor checker, st
Context: acceptance gates over model output — JSON extractor, evidence-anchor checker, structure checker, adversarial verifier; four gates, three mine, one a peer team's.
Pitfall: a gate ruling on a question it has no power to decide, and the ruling landing as REJECT — transport failure recorded as "refuted"; a PowerShell BOM recorded as STRUCTURE-FAIL; a verbatim quote under the wrong line number recorded as FABRICATED; a greedy `\{.*\}|\[.*\]` slice voiding 10/10 valid payloads. The gate is CORRECT about what it can see and silently extrapolates to what it cannot; a confident plausible negative reads like a finding and is never questioned. General form (hit 6): the gate returns ONE value where the input supports several — A TIE-BREAK IS A RULING, in either direction.
Fix: a gate may only rule on what it can DETERMINE; everything else is DOWNGRADE AND FORWARD, never veto — three-valued outcomes with the third state loud (`inconclusive` ≠ `refuted`; `MISALIGNED` + auto-repaired line vs `FABRICATED`); a parser strictly more lenient than the prompt; the receiving side's strictness is itself a measured variable (strict 0/5 vs lenient 5/5 on identical answers). Now global CLAUDE.md's gate rule and `30-judgment.md` R2.2.
Detection: feed a known-TRUE input, not only a known-false one — a gate that rejects everything scores 100% on a one-sided calibration. Cheap tell (hit 5): a UNANIMOUS verdict out of a freshly written checker is an instrument fault far more often than a finding — a moment, not a design phase, so it fires w …[record]
Record: ops/lessons/L-019.md

## L-020 2026-08-16 tags: refactor|duplication|testing|verify|retrospective|dead-code|silent-failure hits: 2 state: live
what: L-020 舊帳本搬入 (legacy import): a retrospective's sibling scan on `tools/extdispatch/` ("was any of this written
Context: a retrospective's sibling scan on `tools/extdispatch/` ("was any of this written twice?"), run after the milestone had shipped with four green suites.
Pitfall: one algorithm existed in THREE places and two had been fixed; the third (the STRUCTURE layer, the first gate every report passes) still returned STRUCTURE-FAIL on valid input. TWO INDEPENDENT FIXES OF ONE BUG IS THE MECHANISM BY WHICH A THIRD COPY SURVIVES — each fix lowers the felt urgency of looking further, and a grep for the SYMPTOM finds nothing because the fixed copies no longer exhibit it. Worse: a test imported one copy while the live layer ran another — a test covering a duplicate reports green on code nobody runs.
Fix: extract to one module the moment a SECOND copy is created (`tools/extdispatch/jsonspan.py`; `peer_experiments.status_block_ok()`), and point tests at the shared symbol, never a consumer's re-export.
Detection: after fixing any MECHANISM-level bug, grep the tree for the mechanism (loop shape, regex, sentinel) and count call sites; then check which copy the tests import. Writing the lesson does not raise the urgency — the second copy is created in the same motion as the first piece of new code ("I need th …[record]
Record: ops/lessons/L-020.md

## L-021 2026-08-16 tags: env|powershell|shell|git|quoting hits: 1 state: folded→git commit -F <msgfile>
what: L-021 舊帳本搬入 (legacy import, folded): PS 5.1's native-arg encoder does not escape embedded `"`: a here-string commit m
Context: PS 5.1's native-arg encoder does not escape embedded `"`: a here-string commit message ends mid-argument, git parses the tail as pathspecs, the commit silently does not happen while the chain keeps running (branch deleted un-merged). Folded 2026-08-31: the fix is verbatim in global CLAUDE.md Environment (`git commit -F <msgfile>` / stdin, never inline; `merge-base --is-ancestor` after chained git; …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → git commit -F <msgfile>
Record: ops/lessons/L-021.md

## L-022 2026-08-16 tags: signal-processing|thresholds|ml-depth|imaging|diagnosis hits: 1 state: live
what: L-022 舊帳本搬入 (legacy import): 3D Photo Synthesis Engine — cutting depth discontinuities out of an ML-predicted
Context: 3D Photo Synthesis Engine — cutting depth discontinuities out of an ML-predicted depth map (edge masking; mesh culling).
Pitfall: hunting a sharp feature in a smoothed signal. ML depth smears true steps into multi-pixel ramps, so the per-pixel difference stays below any reasonable threshold and `percentile(gradient, 95)` cuts "the steepest 5%" — noise, ranked. Every threshold value looks defensible and each retune produces a visibly different (still wrong) mask, which reads as progress rather than as a wrong axis.
Fix: change the measured QUANTITY, not the threshold — find a space in which the outlier is genuinely an outlier (here 3D edge length / median: 576.9×, clean bimodal histogram, one cut, view-independent).
Detection: before tuning any threshold, ask whether the sharp feature can exist in this signal at all; if it came through a model or filter, it usually cannot. Status: single project, hypothesis tier; global candidate H-6 deferred — re-propose on a second project's hit.
Record: ops/lessons/L-022.md

## L-023 2026-08-17 tags: git|env|concurrency|shared-worktree|branch|dispatch|shared-index hits: 4 state: live
what: L-023 舊帳本搬入 (legacy import): two sessions working `~/.claude` at once; Session B ran `git checkout -b` trusti
Context: two sessions working `~/.claude` at once; Session B ran `git checkout -b` trusting its session-start snapshot ("Current branch: main") while HEAD was A's feature branch — B forked off A's unfinished work and A's next two commits landed on B's branch.
Pitfall: HEAD, `.git/index` and the working tree are SHARED MUTABLE STATE between sessions in one tree. A checkout in either session silently redirects the other's commits; a ref move without a checkout leaves a stale shared index that the next commit in ANY session serializes as deletions (hit 3: 52 files, no error); an uncommitted peer edit is ABSORBED into whoever stages that path next (provenance lost, content intact). No command errors; ancestry checks pass while content is wrong.
Fix: the shared-tree discipline lives in `ops/references/shared-tree-git.md` (owner `20-dispatch.md` §7a) — routing by COUPLING CLASS (user ruling 2026-08-17: same workstream → SERIALIZE / baton-pass; disjoint domain → the second session takes a worktree; live-environment verification → canonical tree, ONE writer; true parallelism → split by TREE, never by ticket), the commit ritual (`git branch --show-current` → stage explicit paths → commit → `git show --stat HEAD` read for what you did NOT write), the content-vs-ancestry check (`git cat-file -e <sha>:<path>`), and the recovery recipes (plumbing merge; `git branch -f main <sha>` when caught within one commit; additive restore, …[record]
Record: ops/lessons/L-023.md

## L-024 2026-08-18 tags: env|shell|bash|powershell|tool-routing|silent-failure|encoding|line-endings|runaway hits: 12 state: live
what: L-024 舊帳本搬入 (legacy import): a 10-day sweep of every shell call in the transcript corpus (6,544 deduplicated
Context: a 10-day sweep of every shell call in the transcript corpus (6,544 deduplicated calls, 370 errors) asking why PowerShell errored 4× more than Bash. Answer: three silent defects in the Bash tool's command TRANSPORT, plus a selection effect.
Pitfall: (1) BACKSLASH COLLAPSE — n consecutive backslashes arrive as ceil(n/2) in every quoting context (`\n`/`\t`/`\"` untouched), the command reports SUCCESS, escaping harder is halved twice; symptoms differ per language and none name the cause. (2) SIZE CEILING — every Bash command ≥ ~7,700 B fails `unexpected EOF` (truncated at the OS boundary; PowerShell succeeded at 8,053 B). (3) WINDOWS PATH FORMS — unquoted loses every backslash, a trailing backslash inside double quotes escapes the closing quote. Line endings: Edit is the ONLY write path that preserves the target's ending (Write → LF; `cat >>` / `WriteAllText` → MIXED file; `Out-File`/`>` → BOM). Retraction kept: PowerShell `2 …[record]
Fix: routing at the source (global CLAUDE.md Environment bullet 1 — file content → Write/Edit, search → Grep/Glob, the shell keeps git / programs / pipelines; measured Write 0.1% vs Bash-writing-a-file 5.2%, Grep 0.9% vs PS-searching 17.4%); the three limits stay in CLAUDE.md as the backstop. Executors: `hooks/shell_transport_guard.py` (deny size, annotate backslashes), `hooks/ps_errorpref_guard.py` (ANNOTATE-only, 2026-08-21, registered on `Write|PowerShell` because 47 of 53 EAP='Stop' payloads arrived as `.ps1` files through Write/Edit — the rule is about a LANGUAGE, mostly written into files). All three traps hooked. Line endings pinned per repo by `.gitattributes`.
Record: ops/lessons/L-024.md

## L-025 2026-08-21 tags: verify|instruments|calibration|measurement|silent-failure|self-audit|first-use|tooling|gate-design|forensics|output-channel hits: 3 state: live
what: L-025 舊帳本搬入 (legacy import): bench-claude-arms, a 22-run controlled study. Its OBJECT got every control (held
Context: bench-claude-arms, a 22-run controlled study. Its OBJECT got every control (held-out suite calibrated both ways, differential fuzzing, mutation testing); its own working tooling got none, and at least six improvised scripts each failed on first real contact with data — every one straight into a published number or a discard decision: a dedupe that inverted the conclusion, a price table with a si …[record]
Pitfall: rigor followed the PHASE, not the thing — everything built inside the declared instrument-building phase was calibrated, everything improvised mid-flight to unblock something was not. The original "deliverable vs tooling" story was constructed afterwards (zero instances in the record) — a retrospective's narrative is an unverified claim and its author is the last person able to falsify it. THE BASE RATE ("6 of 6 failed") is RETRACTED as circular (the denominator was the set of failures): "at least six, none caught by the author's same-moment check", no rate.
Fix: (a) a script that emits a VERDICT or an AGGREGATE gets one known-answer input before its output is believed; (b) a unanimous verdict from a fresh instrument is a STOP, not a result; (c) is NOT a new rule — it restates `30-judgment.md` R2.2, whose trigger was a closed list ("cron/hook/service/ job") and was WIDENED 2026-08-21 to the property "anything whose output will be BELIEVED rather than read line by line" (a scope defect, fixed by widening in place; promotion ruled against; reopen if the widened R2.2 goes two projects without one recorded firing); (d) "this pattern is happening again" written in a turn becomes a rule with a trigger, or a ticket, in the SAME turn — L-027 is what skip …[record]
Detection: a script emits a verdict/aggregate; a unanimous verdict over n≥3; "I am writing an unplanned checker right now" — known at the moment, unlike "is this output load-bearing?", the judgement demonstrably got wrong six times.
Record: ops/lessons/L-025.md

## L-026 2026-08-21 tags: measurement|benchmark|experiment-design|confound|apparatus hits: 1 state: folded→lessons-detail.md §L-026.
what: L-026 舊帳本搬入 (legacy import, folded): things filed under "setup" that were INSIDE the experiment: the enforcement mech
Context: things filed under "setup" that were INSIDE the experiment: the enforcement mechanism moves the outcome, a **platform cap correlated with the treatment is a confound not noise**, your own `settings.json` is APPARATUS, coupling collection to evaluation decides what you can still fix, and a pre-registered rule needs a "none of the above" branch. Folded 2026-08-27: the operative half ("measure the in …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → lessons-detail.md §L-026.
Record: ops/lessons/L-026.md

## L-027 2026-08-21 tags: env|powershell|shell|pipeline|truncation|silent-failure hits: 2 state: live
what: L-027 舊帳本搬入 (legacy import): bench-claude-arms — two debugging rounds lost to one call shape, days apart, not
Context: bench-claude-arms — two debugging rounds lost to one call shape, days apart, nothing written down in between.
Pitfall: in PowerShell, `<native or interpreter command> | Select-Object -First N` closes the pipeline after N objects and TERMINATES the upstream process (exit 255, truncated output) — both halves of the damage point at the program, not the pipeline. Hit 1 sent the author hunting a missing `__main__` guard; hit 2 was diagnosable only because the truncated tail happened to prove the script had been fine.
Fix: never truncate a native/interpreter command INSIDE the pipeline — capture then slice (`$out = & python x.py; $out | Select-Object -First 30`), `Get-Content -TotalCount` for files, or redirect to a file; `Where-Object` / `Out-String` consume the whole pipeline and are safe. CLOSED 2026-08-21 by `hooks/ps_pipeline_close_guard.py` (PowerShell, ANNOTATE-only; suite 49/49; backtest 100 fires / 3,412 payloads = 2.93%, 1.79/day — a publish and a test run in the corpus were killed to shorten a screen). Why a closing was needed: this was filed into lessons — the layer L-011 calls "essentially never" firing — on the day L-011 was being edited two screens up; a named-tool-call trigger that had …[record]
Detection: a pitfall whose diagnosis cost more than one round gets its ledger entry at the moment it is fixed, not at project end (L-025 fix (d)).
Record: ops/lessons/L-027.md

## L-028 2026-08-22 tags: env|powershell|self-test|scalar-unwrap|silent-failure|verify hits: 1 state: live
what: L-028 舊帳本搬入 (legacy import): `tools/session-board/session-board.ps1 -SelfTest` reported 28/29 with exactly ON
Context: `tools/session-board/session-board.ps1 -SelfTest` reported 28/29 with exactly ONE claude session live; the failing case was "found >=1 live claude session" while its sibling "at least one has a locatable transcript" PASSED on the same data.
Pitfall: PS 5.1 hands back a SCALAR when a function returns a one-element array (`return $out` with `$out = @(one)`), and a scalar has no `.Count`, so `$live.Count -ge 1` is `$null -ge 1` = false — right at n=0 and n≥2, wrong at exactly n=1: a verdict that depends on the SIZE of its input, not its content (L-019's family). The sibling line was already wrapped in `@()` and passed, which was the tell; it was still misread once as "environment-dependent" in a delivery report before the sibling gave it away.
Fix: wrap every collection you will `.Count` in `@()` at the point of use (`$live = @(Get-LiveSessions)`), not only inside the producer — the unwrap happens at return. The live control now SKIPs (third verdict, exit code untouched) when no session is live, so the suite never teaches its reader that it fails routinely (L-017 (b)).
Detection: a check that fails while an adjacent check consuming the same collection passes — diff the two expressions before blaming the environment; a suite that passes at n=0/n≥2 and fails at n=1.
Record: ops/lessons/L-028.md

## L-029 2026-08-23 tags: env|shell|bash|msys|path-conversion|windows-native|silent-failure|hang hits: 1 state: folded→hooks/shell_transport_guard.py
what: L-029 舊帳本搬入 (legacy import, folded): the Bash tool IS Git Bash/MSYS2, which rewrites argv for native Windows exes: **
Context: the Bash tool IS Git Bash/MSYS2, which rewrites argv for native Windows exes: **`cmd /c` → `C:/`**, **`taskkill /PID` → `C:/Program Files/Git/PID`**. A Windows SWITCH is indistinguishable from a POSIX path at that layer; quoting does not help. `cmd` handed `C:/` starts an INTERACTIVE shell that hangs for the whole timeout. NOT one of L-024's three. Escapes: route through the **PowerShell tool* …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → hooks/shell_transport_guard.py
Record: ops/lessons/L-029.md

## L-030 2026-08-23 tags: verify|ui-testing|css|silent-failure|frontend|claim-calibration|third-party-upgrade hits: 1 state: live
what: L-030 舊帳本搬入 (legacy import): a NiceGUI + AG Grid editor. Excluded rows were supposed to dim; the row carried
Context: a NiceGUI + AG Grid editor. Excluded rows were supposed to dim; the row carried the right class and the summary count updated, but nothing looked different. Two more rules from the same block — cell line-height and header font-weight — had been assumed working for the whole session.
Pitfall: all three rules were scoped `.ag-theme-balham .ag-cell { … }`, and **AG Grid 33+ generates its theme class names** (`ag-theme-params-5`, `ag-theme-batchEditStyle-3`, …). `.ag-theme-balham` never existed in the DOM, so every rule under it matched NOTHING — silently, with no console error, no build warning, and no visible symptom for the two rules whose effect nobody was watching. The general shape: a CSS rule that matches nothing is indistinguishable from a CSS rule that matches and is overridden, and BOTH are invisible to static review. A vendor major-version bump is the usual trigger, because theme/class naming is exactly the kind of thing that changes there.
Fix: scope to structural classes (`.ag-cell`, `.ag-row.row-excluded`) rather than to a theme class, and — the part that actually catches it — **assert the COMPUTED value, never the presence of the class**: `getComputedStyle(cell).opacity === '0.4'` catches it; `row.className.includes('row-excluded')` passes while the styling is dead, because the class IS applied. Same discipline as L-010's settle-token rule, one layer earlier: L-010 is "the computed value may be mid-transition", this is "there may be no rule producing that value at all".
Detection: a styling change that "did nothing" while the state class is present; `document.querySelector('.<theme-class-you-wrote>')` returning null; a `getComputedStyle` value equal to the framework default rather than yours.
Record: ops/lessons/L-030.md

## L-031 2026-08-26 tags: inherited-algorithm|staleness|fingerprint|derived-view|working-tree|graph-snapshot hits: 1 state: live
what: L-031 舊帳本搬入 (legacy import): graph-snapshot indexes the ~/.claude WORKING TREE. Its freshness gate was copied
Context: graph-snapshot indexes the ~/.claude WORKING TREE. Its freshness gate was copied faithfully from `ops/references/project-map.md` §6, which fingerprints a git COMMIT because a project map describes committed state.
Pitfall: an inherited algorithm carries its original context's TIME SEMANTICS. Fingerprinting HEAD cannot see an uncommitted edit, so the gate reported FRESH while `skill-trigger-dict.md` sat ` M` — a structural file on disk already differed from what the graph reflected, and INV-3 ("a STALE graph refuses to answer") was silently void. Faithful reuse is precisely what hid it: nothing looked wrong, because the copy was correct — for the other context.
Fix: the authoritative fingerprint became `corpus_digest`, a hash over the content manifest the build already computes; git stays for provenance and for naming what changed, but no longer decides trustworthiness. Regression cases pin the exact failing case (dirty structural file => STALE) with both inputs injectable — the first version read the real corpus off disk and the key case passed for the wrong reason.
Detection: a staleness/freshness/cache-validity check whose fingerprint source (commit, mtime, version tag) differs from what the artifact is actually built FROM; any derived view over uncommitted state gated by a git ref. Applied (fix held at first deliberate use): `gs_watchdog.evaluate()` was born pure with …[record]
Record: ops/lessons/L-031.md

## L-032 2026-08-26 tags: false-negative|benchmark|calibration|ablation|instrument-check|measurement hits: 3 state: live
what: L-032 舊帳本搬入 (legacy import): graph-snapshot phase 1 produced four negative verdicts, each of which would have
Context: graph-snapshot phase 1 produced four negative verdicts, each of which would have changed a decision. Rule home: the global CLAUDE.md automated-gate rule (calibrate with known-TRUE and known-false); this card is the measured instance and its detection surface.
Pitfall: a negative measurement is a claim about the INSTRUMENT until the instrument is checked. All four negatives were false: a 73.6% resolution rate (three separate resolver/classification faults), "the new edge types did nothing" (they were never wired into traversal), a 100%-recall ablation that was tautological (seeds entered the read set by construction), and a "title drift in the corpus" finding that was a citation-granularity mismatch. Every one LOOKED like a result, and read as bad news about the corpus or the design rather than about the measuring code.
Fix: before acting on any negative verdict, run the instrument on a known-TRUE input, a known-FALSE input, and — where a scope boundary exists — a known-EXCLUDED input; graph-snapshot prints all three on every build. For a benchmark, an arm that cannot lose (or cannot win) measures nothing: check what each arm is seeded with before reading its score.
Detection: a freshly written checker returning a uniform verdict on n>=3 inputs; a negative finding about an artifact nobody reproduced against the raw source; an ablation arm whose construction implies its own score. Recurrence: hit 2 (2026-08-26, the SAME SESSION that wrote this card, while testing watchdog …[record]
Record: ops/lessons/L-032.md

## L-033 2026-08-27 tags: gate-design|calibration|false-negative|verification|doc-hygiene|regex|claim-calibration|instrument-vocabulary hits: 2 state: live
what: L-033 舊帳本搬入 (legacy import): the skill's backlog file (then `FUTURE-WORK.md`, renamed `literature-search-extr
Context: the skill's backlog file (then `FUTURE-WORK.md`, renamed `literature-search-extract-FUTURE-WORK.md` the same day under the owner-first basename rule in `40-maintenance.md` §3) recorded "SKILL.md 現 261 行". True on 2026-07-12, false from 2026-07-19 when the file was trimmed to 250, unnoticed for five weeks — then a later session took it as a BASELINE and did arithmetic on it, producing a seco …[record]
Pitfall: the checker passed **5/5 synthetic cases and then MISSED THE REAL BUG**. Bound-detection asked "is there an upper-bound word within ±40 chars", and the real sentence carries two numbers — `現 261 行，超過 250 行軟上限` — so 250's 「上限」 vouched for 261 from five characters away. Every synthetic case had ONE number per sentence, so the flaw was **unreachable by construction**: the suite could not have failed for this reason no matter how many cases it held. A green calibration measured my imagination, not the instrument.
Fix: before trusting any green, **replay a REAL past failure out of git and demand a FAIL** — `git show <old-sha>:<file>` into a temp dir and run the checker at it. Structural fix: scope an adjacency keyword to the span between NEIGHBOURING numbers, never a fixed character window. Both language forms (zh 「行…上限」, en "lines … cap") are now permanent regression fixtures. Generalises past this tool: adding cases to a suite whose cases all share a simplification the real data lacks buys nothing — the fixture must come from production, not from the author. Hit 2 (2026-09-06, claude-config, graph-snapshot's live-surface count) — the same defect one level up, and it landed on THIS car …[record]
Detection: a brand-new checker reports clean on its first pass over real data; or every case in the suite shares a shape ("one X per line") the wild does not; or a rule file carries a "do not fix this" note aimed at a tool.
Record: ops/lessons/L-033.md

## L-034 2026-08-27 tags: hooks|config|cross-session|outage|recovery|git-merge|settings-json hits: 1 state: folded→70-evolution.md §1
what: L-034 舊帳本搬入 (legacy import, folded): deleting an untracked hook file that `settings.json` already registered, on the
Context: deleting an untracked hook file that `settings.json` already registered, on the assumption a `git merge` would restore it: the merge ABORTED on unrelated untracked files, so every `Bash`/`PowerShell` call in EVERY session died at PreToolUse (`can't open file ... branch_commit_guard.py`) — including the calls needed to restore it; only the Write tool remained. Second finding: **hooks are NOT snap …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → 70-evolution.md §1
Record: ops/lessons/L-034.md

## L-035 2026-08-27 tags: instrument-check|calibration|gate-design|spec-drift|simulation|routing|false-positive hits: 1 state: folded→lessons-detail.md §L-035.
what: L-035 舊帳本搬入 (legacy import, folded): **two-sided calibration validates the implementation against its own MODEL, not
Context: **two-sided calibration validates the implementation against its own MODEL, not the model against the SPEC**: a routing linter's simulator replayed a documented TWO-LEVEL scan as a flat one, so it reported overlaps on rows no matching prompt can reach, while every control passed the whole time. Folded 2026-09-06 (4th pass): the operative rule is global CLAUDE.md's automated-gate bullet (a gate may …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → lessons-detail.md §L-035.
Record: ops/lessons/L-035.md

## L-036 2026-08-28 tags: testing|contract-drift|cross-boundary|api|gate-design|verify|silent-failure hits: 1 state: live
what: L-036 舊帳本搬入 (legacy import): media-fetch-pipeline Phase Z2. A user reported the settings panel saying the eng
Context: media-fetch-pipeline Phase Z2. A user reported the settings panel saying the engine was ready and the feature unusable in one viewport, and asked whether state was out of sync. It was not -- the single source of truth held throughout. Auditing the PROJECTION instead turned up seven contradictions, one of which had shipped past 2,033 green tests.
Pitfall: **both sides of a contract were tested and the JOIN was not.** The server emitted `action="pick-translation"`; a Python test asserted exactly that string; the renderer's TypeScript union did not contain the name, so its label ternary and its dispatch both fell through to the branch for a DIFFERENT action -- and a user told to pick one of the models they already had got a button that opened a browse-for-a-NEW-folder dialog. Neither suite was wrong about its own side. Nothing read the two together. Four more of the same shape in the same module: `optional` declared with a docstring promising that the panel would never render an opt-in capability as a fault, defaulted to the wrong value, set by …[record]
Fix: a CHECK, not a rename. A test parses the action literals out of the server module and the union out of the type declarations and asserts set equality **in both directions** -- a name added on one side only now fails, and so does a name in the union that nothing emits. It skips with a reason when the other side's sources are absent from the checkout. Cheap (one regex per side), and it is the only artifact in the repo that reads both files. This is L-006's prescription arriving as code: L-006 said reconstruct the intended model as an artifact and check the code against it, which is what the audit document did by hand. The generalisation is that when both sides are MACHINE-READABLE, the reconst …[record]
Detection: any enum, union, or action-name vocabulary that exists in two languages. Grep each side's literals, diff the sets, and expect the diff to be non-empty the first time.
Record: ops/lessons/L-036.md

## L-037 2026-08-28 tags: verify|test-design|ui-testing|visual-gate|frontend|claim-calibration hits: 1 state: live
what: L-037 舊帳本搬入 (legacy import): same session. Six assertions had just been written for one defect class -- the s
Context: same session. Six assertions had just been written for one defect class -- the same sentence printed twice in one viewport under two labels -- and the repair for a NEIGHBOURING defect reintroduced it. Every one of the six stayed green.
Pitfall: **a suite of absence-assertions cannot see a redundant presence.** Each of them read `expect(region).not.toHaveTextContent(X)`; the recurrence was a correct sentence appearing a second time next to the first. Nothing was missing, nothing was wrong, and no assertion in that class can be phrased to catch it without knowing in advance which string would be duplicated. It was found by rendering the page out-of-process and LOOKING at the image. The global rule already says green tests prove the data path and not the picture. What this adds is the mechanism, so the rule can be applied on purpose rather than as a slogan: for a surface whose defect class is "two things that disagree" or "one thing s …[record]
Fix: when the deliverable is a rendered surface and the defects are relational, budget one out-of-process render per repair round and read it before believing a green suite. Playwright headless into a PNG, delivered via `SendUserFile`, costs one command and caught what six purpose-written assertions could not. Pair it with the calibration rule that already exists -- break each new assertion's fix and confirm the assertion fails, and keep one deliberate POSITIVE CONTROL that must stay green -- because that pass proved the six were sound, which is exactly why their blind spot was invisible.
Detection: a repair that removes a duplicated string and then has to put the information back somewhere. That put-back is the moment the duplication returns, and it returns in the region the assertions do not scope.
Record: ops/lessons/L-037.md

## L-038 2026-08-29 tags: hook-design|gate-design|false-positive|identity-by-path|deny-message|prompt-injection|subagent|asset-property hits: 1 state: folded→hooks/transcript_read_guard.py
what: L-038 舊帳本搬入 (legacy import, folded): identity-by-path rots when a corpus root gains a new tenant (WebFetch PDF caches
Context: identity-by-path rots when a corpus root gains a new tenant (WebFetch PDF caches under `**/tool-results/` denied as session records); a deny message asserting a file's identity + "Policy:" authority + a read-elsewhere imperative is shape-identical to prompt injection, and a well-calibrated subagent rightly refuses it. Folded 2026-08-31: carried by `hooks/transcript_read_guard.py` itself (shape-bas …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → hooks/transcript_read_guard.py
Record: ops/lessons/L-038.md

## L-039 2026-08-31 tags: retrieval|prior-art|compact|handoff|cross-session|scope-creep|deliverable-series|intake hits: 1 state: live
what: L-039 舊帳本搬入 (legacy import): SSLD Phase 5 presentation round, opened right after a compact. The round used on
Context: SSLD Phase 5 presentation round, opened right after a compact. The round used only the kickoff doc + compact summary; the professor-reviewed prior deck (SSLD_WG_Glass_FAU, 3 pptx + adversarial-review record) and the SRG sub-profile were pulled only after the user prompted. The late pull changed the deliverable in five places; two were impossible without the prior-work folder — the miss was mater …[record]
Pitfall: SUMMARY-HANDOFF GATE DISARM. A lossy summary (compact summary; a phase-log section at reconstruction; a worker ticket) rewrites how the task ARRIVES — "create deliverable N" arrives as "execute a settled list" — and every intake trigger (prior-art gate, domain-skill trigger words) keys on the ARRIVAL shape, so none fires while the summary inherits sole material authority. Two amplifiers: (1) single-source scope creep — a ruling scoped to one axis ("numbers come from the kickoff doc") read as authority over ALL content; (2) deposit gap — the predecessor deliverables + review records had no index entry anywhere (miss-ledger MISS-A family), so even an armed gate had nothing to hit. Sibl …[record]
Fix: (a) hook-carried re-arm at the danger moment — `compact_pointer.py`'s post-compact card gains an [intake re-arm] block: the gates are NOT satisfied by the summary; a prior-art verdict survives compaction only as a NAMED list of what was consulted, never as "already done". (b) global CLAUDE.md prior-art bullet gains the third trigger — continuing a deliverable series makes deliverables 1..N-1 + their review records mandatory inputs, and a single-source ruling covers only its named axis. (c) workflow-checkpoint §A/§B/§C — a checkpoint or compact note handing off a deliverable round NAMES the mandatory input set; reconstruction reads the phase-log as a pointer, never as prior-art-done.
Detection: a deliverable round that opens by reading only its arrival documents; the phrase "single source" applied to an axis it never ruled on.
Record: ops/lessons/L-039.md

## L-040 2026-08-30 tags: hook-design|gate-design|telemetry|shadow-mode|coverage-blind-spot|batch-operation hits: 1 state: folded→lessons-detail.md §L-040.
what: L-040 舊帳本搬入 (legacy import, folded): **a tool-matched hook measures the TOOL, not the EFFECT**: a `Write|Edit` PostTo
Context: **a tool-matched hook measures the TOOL, not the EFFECT**: a `Write|Edit` PostToolUse guard read 100 % ok over 20 rows while an 11-file script backfill inside its own `covers` produced ZERO rows, and the bypassing population is the highest-risk one (bulk operations). A shadow rate is a verdict distribution over what the instrument happened to see, never a coverage fraction. Folded 2026-09-06 (4th …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → lessons-detail.md §L-040.
Record: ops/lessons/L-040.md

## L-041 2026-08-31 tags: office-interop|pptx|hyperlink|canonical-probe|com|artifact-format|encoding hits: 1 state: folded→rules/deliverable-doc-refs.md
what: L-041 舊帳本搬入 (legacy import, folded): GUESSING A DESKTOP APP'S ARTIFACT FORMAT FROM THE STANDARD: PowerPoint stores lo
Context: GUESSING A DESKTOP APP'S ARTIFACT FORMAT FROM THE STANDARD: PowerPoint stores local links as `file:///D:\dir\檔.html` (raw backslashes, CJK unencoded) and rejects the spec-correct percent-encoded `Path.as_uri()` form with a one-bit error. The fix is a TOOL-AS-ORACLE CANONICAL PROBE — drive the app by COM to produce the same construct, unzip, read what it stored, replicate byte-for-byte, assert …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → rules/deliverable-doc-refs.md
Record: ops/lessons/L-041.md

## L-042 2026-09-01 tags: verify|invariants|composition|api-design|refactor|silent-failure|proof-scope|naming hits: 1 state: live
what: L-042 舊帳本搬入 (legacy import): media-fetch-pipeline's two transcript verbs — `correct` (substitutes inside a cu
Context: media-fetch-pipeline's two transcript verbs — `correct` (substitutes inside a cue) and `tidy` (deletes whole cues). Each was written as the LAST step, owning its transformation, its record AND its file names; each proves itself, `tidy.apply` by asserting that putting the removals back rebuilds its input exactly, which is this project's only guard against the one defect class it cannot see downst …[record]
Pitfall: **A PROOF IS RELATIVE TO ITS OWN INPUT, SO IT DOES NOT COMPOSE.** Chain the two by hand and the second step's input is an intermediate nobody keeps, so「the record can rebuild the original」silently weakens to「it can rebuild a file that no longer exists」— no test fails, no error appears, and the sentence everyone quotes is simply no longer the one that holds. The cheaper symptoms are the only visible ones and they read as cosmetic: the same content took two NAMES depending on the order run (`.corrected.tidy` vs `.tidy.corrected`), seven files landed where four were wanted, and the two machine records ended up in two coordinate systems — run the deleting step first and the other rec …[record]
Fix: one layer owns the composition — stage ORDER (index-preserving stages before index-collapsing ones, so every stage's record stays in the SOURCE's coordinates and the order stops being the caller's choice), naming, and ONE end-to-end proof that reverses every stage and must reproduce the ORIGINAL before a byte is written. Deliberately redundant against today's two stages: it is the check that still holds when a third arrives. A regression test plants a fault BOTH stages pass — the substituting step asserts cue count and timestamps, never that only the proposed spans changed — which only the composition catches.
Detection: two operations that each self-verify and can be run one after the other. Ask what each proof's baseline IS: if it is "my input" rather than "the artifact the user holds", chaining voids it. Second tell, cheap and visible from outside: **an order of operations that changes output NAMES** — that is …[record]
Record: ops/lessons/L-042.md

## L-043 2026-09-01 tags: coverage-blind-spot|testing|silent-failure|refactor|dead-path|multi-surface|gate-design|verify hits: 1 state: live
what: L-043 舊帳本搬入 (legacy import): media-fetch-pipeline reaches one feature from two surfaces — a CLI verb and an H
Context: media-fetch-pipeline reaches one feature from two surfaces — a CLI verb and an HTTP route the desktop calls. A 2026-08-30 refactor split `stack.py` and moved three names into `captions`/`cues`. The route's imports were updated; the CLI handler's function-local import was not.
Pitfall: **`mfp stack` raised ImportError before doing anything, for two days, with 2,500 tests green and the GUI feature working normally.** Every signal a person consults said fine. The suite was green because no test invoked that handler; the product looked healthy because the OTHER surface reached the same capability through correct imports. Two conditions produced it and both are ordinary: imports deferred into a handler (deliberate here — a missing Pillow must not stop `doctor` from reporting that Pillow is missing) are unchecked until that handler runs; and a capability with two entry points has a majority path that gets exercised and a minority path that does not. The minority path does not …[record]
Fix: a static gate that resolves every `from <package>.… import …` in the package, including function-local ones, so a moved symbol fails in CI rather than on a machine. Calibrated by restoring the original broken import and watching it go red. **Its first run reported 28 failures and every one was false** — `from pkg import submodule` names a submodule, and the package has no attribute for it until something imports it; the instrument was wrong, not the tree, and believing it would have "fixed" 28 correct lines.
Detection: ask which code paths NO test invokes — not which lines are uncovered, which is a different and weaker question. Two tells, both cheap: a capability offered from more than one surface where only one surface has tests; and any refactor that MOVES a name, since deferred imports do not resolve at impo …[record]
Record: ops/lessons/L-043.md

## L-044 2026-09-02 tags: gate-design|validity-model|vocabulary-gap|self-grading|recurring-symptom|figure|annotation|standards|verify|refactor hits: 1 state: live
what: L-044 舊帳本搬入 (legacy import): model3d-pipeline paper figures (SSLD, five cases). Four user reports on the same
Context: model3d-pipeline paper figures (SSLD, five cases). Four user reports on the same figures; occlusion fixed on the third, the fourth named a different class: dimension lines through parts, leaders across dimension lines, extension lines starting inside bodies, values not pulled clear.
Pitfall: **the clearance model had ONE object — the text box.** Lines were neither obstacles nor subjects, so every rule the drafting standards state about lines (ISO 129-1 §5.3, ASME Y14.5 §4.4.1–4.4.4) was unexpressible, and the gate re-ran the renderer's own layout and asked it whether it was happy — same code judging itself — so it stayed green on figures a reader would reject. Callers "fixed" it by hand-tuning offsets per figure (7 of them).
Fix: (1) one obstacle map in which every object class the rules name is first-class (fills, outlines, every placed stroke, every text); (2) a gate that reads the EMITTED SVG through role tags and rules on it independently, calibrated two-sided (every FAIL rule shown to fire on an injected fault); (3) rules derived from the standard, hard for "shall not", weighted for "avoid". Detail + the standards card: `ops/references/lessons-detail.md`.
Detection: the complaint names an object class ("線壓字", "箭頭沒框住") that the checker has no word for; the gate has never failed on a real input; the consumer carries per-instance magic numbers to stay green.
Record: ops/lessons/L-044.md

## L-045 2026-09-02 tags: registry|prior-art|coverage-blind-spot|project-audit|enrolment hits: 1 state: folded→70-evolution.md §2
what: L-045 舊帳本搬入 (legacy import, folded): the prior-art chain's first rung enumerates only what was ENROLLED: a dormant pr
Context: the prior-art chain's first rung enumerates only what was ENROLLED: a dormant project with a full design chain (`LexiconVault`, inventoried as #23 by an audit that never diffed against the registry) had no `PROJECTS.md` row, so a ruling made on the registry alone designed a near-duplicate. "Not registered" must be read as "unknown", never "absent". Folded 2026-09-06 (4th pass): enrolment-as-defini …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → 70-evolution.md §2
Record: ops/lessons/L-045.md

## L-046 2026-09-04 tags: agents|dispatch|harness|config|probe hits: 1 state: folded→20-dispatch.md §0
what: L-046 舊帳本搬入 (legacy import, folded): a new `agents/*.md` definition is NOT dispatchable when it is written: the Agent
Context: a new `agents/*.md` definition is NOT dispatchable when it is written: the Agent tool's roster is a harness snapshot refreshed on its own schedule, the type check runs before any hook, and `Agent type '<name>' not found` on the first dispatch either aborts it or forces an interim policy that must be unwound. Folded 2026-09-06 (4th pass): promoted to `20-dispatch.md` §0 (probe dispatch before rely …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → 20-dispatch.md §0
Record: ops/lessons/L-046.md

## L-047 2026-09-04 tags: gates|registry|identifiers|consumers|false-green|membership|instrument-check hits: 2 state: live
what: L-047 舊帳本搬入 (legacy import): SSLD T41. The explanation registry numbers its entries `E-nnnn` densely in sort
Context: SSLD T41. The explanation registry numbers its entries `E-nnnn` densely in sort order of `(source, path)`. One consumer (`build_explorable.py`) hard-coded 27 such ids. Card SP-01b grew the registry by 72 entries; every id after the insertion point shifted, and all 27 consumer references now resolved to OTHER quantities — a panel labelled "z_R (glass)" displayed a dust-loss dB value.
Pitfall: every gate stayed green. RegistryGate checked "id exists" (a dense id space makes every id exist), LinkGate checked "anchor exists in the dossier", ParityGate compared JS↔Python relations and never touched registry values. An existence-only gate over a positional id space cannot see silent re-pointing; the failure is invisible exactly when the registry is doing its job (growing).
Fix: (1) consumers address entries by the stable key — here NumberRef `(source, path)` — and DERIVE the display id at build time; a literal id in consumer source is a build-time assertion failure (KnownBad: inject one). (2) Link/registry gates verify KEY EQUALITY, not existence: the target anchor carries `data-ref="<source>::<path>"` and the gate compares it with the source's expectation (KnownBad: shift an id by +N → anchor exists, key differs → must FAIL). (3) A label gate ties each displayed value to its quantity (label ⇄ entry name/path leaf). Recorded as SSLD PIM INV-19.
Detection: a registry/ledger that renumbers on growth + any consumer with a literal id in its source (`grep -n "E-[0-9]\{4\}"` outside registry outputs); after a registry rebuild, sample a displayed value and read its entry text — if the label and the entry disagree while gates are green, this is it.
Record: ops/lessons/L-047.md

## L-048 2026-09-04 tags: layout|width|shell|gate-design|vocabulary-gap|prior|html|deliverable|recurring-symptom hits: 2 state: live
what: L-048 舊帳本搬入 (legacy import): the user asked why every long-form HTML deliverable (SSLD textbook, four dossier
Context: the user asked why every long-form HTML deliverable (SSLD textbook, four dossiers, the discussion pack, paper-story one-page KEYPOINT strips) left 30–40 % of a 2560×1440@150% screen empty on the right, although the display premise was recorded and every UAT had "版面" items. Measured at 1707×830: 69 % reach, right void 439 px; at 1920×950: 60 %, 652 px. A 268-file scan found 15 left-anchore …[record]
Pitfall: **an uncountered prior + one shared shell + one-sided gates = a CLASS recurrence, not an incident.** (1) The model's typographic default ("running text ~65 characters", stated verbatim by the built-in artifact-design skill, plus "avoid everything centred") produces a LEFT-ANCHORED narrow column whenever no rule of ours says otherwise — and none did: the display block was phrased as a compatibility baseline ("judge against FHD") and used only by the HEIGHT fit-gate. (2) Every instrument measured "too wide" (scrollWidth ≤ innerWidth, one-slide-one-screen, elements wider than the viewport) and none had an object called "unused width" (L-044 shape); the KnownBad control was a 4000 px block, …[record]
Fix: property, not reminder — `ops/environment.md` §Display "horizontal property" + `rules/deliverable-doc-refs.md` (paths now include the generator scripts); classes as DATA (`tools/page-fill-gate/page_classes.json`, one row = one class + a fixture pair) declared by `<html data-page-class>`, undeclared → inferred → WARN only; `fill_gate.py` with two-sided controls per run; shells fixed at the source (deck-shell ×4 uncapped; textbook shell fluid + `#rail` 本節速查) and propagated by the existing byte-identity/rebuild chains; UAT B3 example names the class. Proportional allocation (fr/%/cqw/clamp) with pixels reserved for intrinsic sizes is the design rule that stops the next cap.
Detection: `python tools/page-fill-gate/fill_gate.py <built html>` — a FAIL at a gating viewport, or a WARN carrying "inferred:" on a page that shipped; in CSS review, any `max-width` on a page container without `margin:auto`, or an `em`-capped painted block that is alone in its row.
Record: ops/lessons/L-048.md

## L-049 2026-09-04 tags: shell|shared-asset|generator|gate-design|anchors|file-lock|edit-blast-radius|html hits: 3 state: live
what: L-049 舊帳本搬入 (legacy import): fixing L-048 meant editing `05_交付/textbook-src/shell.html`, a shell that three d
Context: fixing L-048 meant editing `05_交付/textbook-src/shell.html`, a shell that three downstream builders consume. Three separate refusals in one round, each from a consumer the edit never mentioned: (1) the rail's figure links were built as a JS string `'<a href="#' + id + '">'` — `build_dossiers.link_gate` scans the EMITTED TEXT for `href="…"` and cannot tell JS from markup, so it read them as …[record]
Pitfall: **a shared shell's TEXT is an interface, not just its rendering.** Its consumers are (a) adapters that patch it by exact string, (b) gates that scan the emitted bytes without a parser, and (c) the user's own open files. None of them appear in the shell, none are listed in its header, and an edit that is correct in the browser can still be refused — or worse, silently mis-adapted — by all three. The round-trip cost is real: three rebuild cycles, ~40 minutes.
Fix: before editing a shell, `grep` for its path across the repo and run every builder that names it, not only the one you were fixing; emit links to gate-scanned documents with DOM calls (`createElement` + `setAttribute`), never string-concatenated markup; when adding to a file that adapters patch, add INSIDE an existing function body rather than at a file/IIFE boundary where the anchors live; and make a copying builder skip byte-identical writes so someone else's open file cannot fail a build that does not change it. What went RIGHT and must not be "simplified" away: all three failed LOUDLY and named the cause, because the adapter asserts an anchor count (`sub1` refuses at 0 or 2) instead of ca …[record]
Detection: after editing any file matched by `*shell*.html` or read by a `build_*.py`, run `grep -rl "<shell filename>" --include=*.py` and execute each hit; a refusal naming "anchor found 0 times" or a `PermissionError` on a copied artifact is this lesson, not a bug in the builder.
Record: ops/lessons/L-049.md

## L-050 2026-09-04 tags: retrieval|verify|external-state|publish|registry|claim-calibration|vocabulary-gap hits: 1 state: folded→30-judgment.md
what: L-050 舊帳本搬入 (legacy import, folded): THE RETRIEVAL UNIVERSE HAS ONLY ONE HALF: every index this environment owns (mem
Context: THE RETRIEVAL UNIVERSE HAS ONLY ONE HALF: every index this environment owns (memory, PROJECTS.md, cross-index, gsnap, session-find, phase logs, decision journals) indexes SELF-AUTHORED records, so "is the public page current" can run every ladder to its end and still answer from a corpus that is not downstream of the truth — `gh release list`, never run, showed the Releases page cut once at laun …[record]
Pitfall: (archived bullet — the mechanism is in the legacy full record under ## Narrative)
Fix: folded → 30-judgment.md
Record: ops/lessons/L-050.md

## L-051 2026-09-05 tags: env-cleanup|uninstall-residue|windows|sandbox|acl|firewall|powershell|shell-transport|tool-authoring hits: 1 state: live
what: L-051 舊帳本搬入 (legacy import): archiving every Codex/ChatGPT leftover before a reinstall, then generalising the
Context: archiving every Codex/ChatGPT leftover before a reinstall, then generalising the run into `tools/app-residue-sweep`.
Pitfall: (1) An "uninstalled" agent app's residue is NOT mostly files: Codex's elevated Windows sandbox left two local users + a group, 26 firewall rules, explicit ACEs on ~50 home subfolders and three D:\ workspace roots, and a Chrome native-messaging key — the layer the user's recurring errors lived in, and the layer no file scan sees. (2) Deleting the principals FIRST turns every ACE and policy token into an unresolvable SID, so the order is ACL → firewall → users. (3) PowerShell variables are case-insensitive: a loop `$p = …` silently overwrote the profile object `$P`, and the branch that read `$P.extensions` found nothing while the same code worked in isolation — a false negative that …[record]
Fix: the tool's inventory covers principals/firewall/ACL/registry/Store/ extensions as first-class categories and lists what it cannot determine under `needs_admin`; the generated admin script hard-codes the order and refuses non-admin runs; profile var renamed `$Prof`. Rule: never reuse a one-letter name for two things in a PowerShell script.
Detection: run the real profile against the LIVE machine and compare category counts with a hand probe (chrome_ext 0 vs a manifest that plainly exists).
Record: ops/lessons/L-051.md

## L-052 2026-09-06 tags: gate-design|calibration|instrument-model|execution-mode|verify|property-test|concolic|false-green hits: 1 state: live
what: L-052 舊帳本搬入 (legacy import): verification-ladder comparison on cross-index `glob_to_regex` — the same target
Context: verification-ladder comparison on cross-index `glob_to_regex` — the same target and the same known-true positive (Python `$` accepts a trailing newline) run through Hypothesis, CrossHair 0.0.110 and the Lean differential.
Pitfall: **an instrument with two execution paths is two instruments, and a positive that went through the other path calibrates nothing.** CrossHair "exhausted the call tree with CONFIRMED" on code that had the bug: for symbolic strings it runs its own regex interpreter (`relib.py`), whose `$` is a strict end of string; only a fully concrete input reaches CPython's `re`. A probe with `pre: s == "a\n"` was caught (concrete path); the symbolic run over `len(s) <= 4` never was. Two-sided calibration as the global gate rule words it was satisfied — a positive existed and fired — and still said nothing about the path that produced the verdict. Family: L-044 (the model has no word for the object), L-0 …[record]
Fix: `rules/verification-ladder.md` rung-3 row — an instrument's CONFIRMED counts only after the known-true positive is caught in the SAME MODE that produced the verdict (symbolic, cached, fast-path…); a verdict whose positive was concrete is a verdict about the tool's model. Rung 2 (Hypothesis, 1.3 s) found both newline divergences; CrossHair stays out of the global interpreter.
Detection: a verbose log that says realized/concretized (CrossHair `realize_*` path stats), a cache or fast-path flag, or "a model of library X" inside the instrument — then ask whether the positive went through that path. The tell: a CONFIRMED that arrives faster than the search space allows (`**` over 5^4 …[record]
Record: ops/lessons/L-052.md

## L-053 2026-09-06 tags: process-ledger|records|attribution|hooks|pointer-staleness|silent-failure|first-prompt|cross-session hits: 1 state: live
what: L-053 舊帳本搬入 (legacy import): this maintenance round logged six decisions with `tools/process-ledger/ledger.py
Context: this maintenance round logged six decisions with `tools/process-ledger/ledger.py add`. All six landed in the PREVIOUS session's ledger file (a different local session), not this one (this session).
Pitfall: the tool answers "which session am I" from `cache/handoff/current-session.json` — a pointer rewritten on every prompt by `hooks/context_runway_shadow.py` — and that hook produced NOTHING for this session: no pointer update, no `cache/context-runway/<id>.json`, no canary. **A pointer file has no way to say "I am stale."** Every consumer reads a syntactically valid id belonging to a session that ended ten minutes earlier and attributes the record to it. Worse, the misfile was visible only because a leftover `current-run.json` happened to DISAGREE and made the tool print a mismatch warning naming an id I recognised; with no run pointer in the tree the identical defect is completely silent. …[record]
Fix: NOT PATCHED — narrowed to two candidates that one probe separates. (a) The hook `sys.exit(0)`s when `transcript_path` is absent or not yet a file, which is the state at a session's FIRST prompt, so a one-prompt session never updates the pointer; (b) UserPromptSubmit hooks do not fire in this surface at all (SessionStart ones demonstrably did — the registry and ops-health lines were injected). Probe, at the start of the next session, before anything else: submit one prompt, then read the `ts` and `session` of `cache/handoff/current-session.json`. (a) ⇒ write the pointer BEFORE the early exits, or from a SessionStart hook that already has the id; (b) ⇒ the ledger needs a different id s …[record]
Detection: `ledger.py add` printing the "current-run.json names X but the prompting session is Y" warning with a Y you were not in; or `ledger.py show` naming a session you were not in. Habit until fixed: pass `--session` explicitly, or compare `current-session.json`'s `ts` against when this session started.
Record: ops/lessons/L-053.md

## L-054 2026-09-06 tags: rules-design|escape-hatch|version-control|gitignore|split-state|silent-divergence|auditability|maintenance hits: 1 state: live
what: L-054 舊帳本搬入 (legacy import): ~/.claude. The memory store was found 5-of-79 tracked, the rest ignored — the fi
Context: ~/.claude. The memory store was found 5-of-79 tracked, the rest ignored — the five put there by `git add -f`, one at a time, by sessions that noticed the file was ignored and pushed it through. Asked whether the fix was at the root, the honest answer was no: nothing in this repo could SEE a force-add. Running the detector for the first time (`git ls-files -ic --exclude-standard`) returned five f …[record]
Pitfall: **an escape hatch that leaves no record makes a rule and reality diverge silently, and the SPLIT state it produces is worse than either pure state.** Worse, specifically, because the items nobody forced are indistinguishable from deliberate exclusions: a reader who checks "is this tracked?" gets a plausible answer whichever way the coin fell. The second casualty is the RULE — a force-add papers over the pattern that was wrong, so `plugins/` stayed unanchored (and kept eating a required test fixture) for exactly as long as the override held. Third: what the override drops is not random. `archive/` is ignored and file hygiene REQUIRES a note per archived subtree, so the blanket rule guarante …[record]
Fix: (a) for any rule with a per-item override, name the VIEW that lists every use of the override; if there is none, the override is the defect, not a convenience. (b) A needed-but-excluded item means the RULE is wrong: anchor or narrow the pattern, or add a negation that names why — never force the item. (c) Contrast, and the reason this card is about `-f` and not overrides in general: `# noqa`, `eslint-disable`, `[branch-ok]`, `[unattended-run]` all leave their mark IN a file or a message, so they are greppable by construction. `git add -f` writes nothing anywhere; its only trace is a disagreement between two git subcommands that nobody runs.
Detection: any per-item override with no enumerating view; a directory whose members straddle a rule; `git ls-files -ic --exclude-standard` non-empty (integrity sweep 28, born red on 5 files).
Record: ops/lessons/L-054.md

## L-055 2026-09-07 tags: probe|capability|verification|claim-calibration|retrospective|external-state hits: 1 state: live
what: 一條被記錄為平台限制的結論，若沒附探測集合就會硬化成牆 (a recorded limit without its probe set ossifies into a wall)
Context: 2026-08-21 bench-claude-arms 記錄：computer-use 的 `request_access` 對散裝 exe 回 `notInstalled`，措辭精確——「解析器只比對 Start 選單註冊過的應用程式」，狀態標 `accepted（平台能力限制）`。2026-09-07 重測：寫一個 `.lnk` 到 Start 選單，30 秒後同一類 exe 就授權成功。限制躺了 17 天。
Pitfall: 限制的描述完全正確——正因為正確，它才被當成完整的。缺的不是事實，是「試過什麼」。沒有附帶探測集合 (probe set) 的限制記錄，讀者無法區分「試遍所有繞法都不行」與「試了一次就停」：兩者在文件上長得一模一樣，而且描述越精確越像已經窮盡。更尖銳的是，「只認 Start 選單」這句話本身就內含解法（那就註冊一個）；它沒被試不是因為難想到，是因為沒有任何欄位在問「你試過什麼」。
Fix: (a) 記錄外部限制時同時寫下 probe set：試過哪些繞法、各自結果，沒試過的標「未試」。沒有 probe set 的限制記錄是假設，不是事實。(b) 限制描述若內含機制（「只認 X」），把「那就製造 X」列為必答的第一個繞法——機制敘述是解法說明書，不是牆的照片。(c) 非同步操作（啟動、載入、渲染）的單次觀測不得寫成策略結論，需第二次觀測或明確 settle 步驟；與 L-010 同構。(d)「accepted（平台能力限制）」是最高風險的狀態標記，它同時關掉「還能不能修」與「是不是真的」，標它時 probe set 必填。
Detection: 寫著「平台不支援／做不到／解析不到」但沒列出試過什麼的記錄；回顧錄裡的 `accepted（平台能力限制）` 條目；對啟動、載入、渲染類操作只觀測一次就下的結論。
Record: ops/lessons/L-055.md

## L-056 2026-09-07 tags: coverage-blind-spot|gate-design|false-negative|verification|audit-record|subagent-dispatch|omission hits: 1 state: live
what: 排除側無稽核 (nothing audits what LEAVES): a harvest built a 12-check gate and three independent audits, all grading rows that were KEPT; 2 of 59 rows dropped as "restated-elsewhere" were authoritative facts recorded nowhere, and no instrument could have surfaced them
Context: A 12-batch harvest adjudicated 514 rows: 277 kept, 237 excluded with a reason code. A calibrated 12-check gate plus three independent audits all graded KEPT rows only. A late spot-check of the excluded file found an authoritative number dropped as "restated-elsewhere" that no kept row recorded; a dedicated audit of all 59 such rows returned 2 false-exclusions (3.4%).
Pitfall: **Verification had a direction, and only one: everything asked "is what we kept true?", nothing asked "is what we dropped safely dropped?"** Not a gap inside any instrument — each is sound over its own domain — a gap in what the SET of them points at. The gate cannot close it by construction: its inputs are the kept files. A wrong value is caught downstream by the next reader; **a wrong exclusion is the pipeline's only zero-trace failure** — nothing reports the absence of what was never written. Sub-mechanisms: judging "already recorded" on SOURCE identity, not QUANTITY identity; and deferring to another batch — a promise nobody is asked to keep, so deferral equals disposal.
Fix: 1. An exclusion reason that points elsewhere must NAME its target and be machine-verified: `already-recorded-in: <row id>` (that row must exist AND carry the same quantity), and `handed-off-to: <batch>` must be reconciled at round close — an unclaimed handoff is an ERROR, not a silent drop. 2. Give the acceptance run a second direction: sample the excluded file at a fixed rate and adjudicate the reason exactly as kept rows are adjudicated. Budget it from the start; it is not an extra, it is the other half. 3. A reason code asserting a comparison ("restated", "already intaken") must record that comparison's evidence, as `dedupe.evidence` already is for kept rows.
Detection: For every exclusion claiming the fact lives elsewhere, search the kept corpus for the QUANTITY (value + unit), not the citation. Zero hits ⇒ escalate. Over 59 rows: one subagent, both defects found — ~2% of round cost if planned at the start.
Record: ops/lessons/L-056.md
