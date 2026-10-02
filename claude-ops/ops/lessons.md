# Lessons — generated index of ops/lessons/ (at the source: do not edit, the guard denies direct writes; this shipped copy carries no such enforcement)

Every card below is a PROJECTION of one intake record `ops/lessons/L-nnn.md` — the record
is the authoritative, lossless text (that per-lesson record tree does not ship in this repo,
so every `Record:` path below is informational here); the card is capped so a pre-task grep hit can be read
in one screen. Write a new lesson: draft a file with the Write tool (front matter `what`
(中文 (English)) + `tags` (≥1 task-type word from tools/closeout-intake/tags.txt), a
`## Record` block with `locator:`, sections `## Context` / `## Pitfall` / `## Fix`
(+ `## Detection`, `## Narrative`), then (with `draft.md` being the file you just drafted)

    python tools/closeout-intake/intake.py add --from draft.md

Recurrence (the "same symptom a 2nd time" rule): grep this file for the MECHANISM first,
then `intake.py event L-nnn --kind recurrence --held yes|no --note "..."`. A card whose
hits reaches 2 is routed through `ops/40-maintenance.md` §2a (fold: `--kind fold --target
"<file §anchor>"`). Full text, recurrences and provenance: the `Record:` path on each card (at the source).
Rules and semantics: the intake design record under the source's references/ tree (not shipped).
generated-at: 2026-09-29T11:51:23+08:00   records: 134

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

## L-005 2026-07-30 tags: handoff|carried-claims|verification|docs|registry|volatile-facts|numeric-constants hits: 4 state: folded→ops/30-judgment.md
what: L-005 舊帳本搬入 (legacy import): Prism UAT-R3.5 — a claim true when written ("batch-1 failures not yet re-verifie
Context: Prism UAT-R3.5 — a claim true when written ("batch-1 failures not yet re-verified on the real machine") survived THREE handoff documents after it became false; a copied verdict ("ResearchGate will keep failing, that is correct") shipped as an instruction and was refuted in one step.
Pitfall: a claim copied from the previous round READS like an established fact — the same authoritative voice as the measurements around it. Prose does not decay loudly, and the receiver cannot tell "I verified this today" from "the last document said this". Registry rows are worse carriers than prose (hit 3); NUMBERS are the worst (hit 4): a constant, or a PRODUCT / RANGE / TOTAL inside an equation, has no slot for a hedge, reads as measured by default, and fuses several provenances into one token with no visible seam.
Fix: (1) carry a claim forward only by re-deriving it in-session or marking it INHERITED with the round it came from — never restate it flat. (2) Make the build check what it can (Prism DRIFT-01 `check_architecture.py::carried- design-anchor` asserts every deferred-design anchor still resolves; prose decays because nothing fails when it does). (3) Any number a design or conclusion RESTS ON carries `measured-here` / `measured-elsewhere(what, when)` / `estimated` / `inherited-default`, and anything not `measured-here` is re-measured before a conclusion is published on it — ask of any derived figure which inputs went in and whether they were all current at the same moment (now `30-judgment.md` R …[record]
Detection: every hit-4 instance was found by READERS doing something else; the verifier that checked the cited file EXISTS caught none — file existence is not the check (L-025).
Record: ops/lessons/L-005.md

## L-006 2026-07-31 tags: skill-design|review-methodology|checklist|scope-gating hits: 2 state: folded→skills/code-review-deep-checklist/SKILL.md
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

## L-008 2026-07-31 tags: rules-editing|naming|scale-labels|ux|project-artifacts|uat hits: 3 state: folded→ops/60-bootstrap.md
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

## L-011 2026-08-08 tags: rules-design|enforcement|hooks|layering|omission|harness hits: 4 state: folded→ops/40-maintenance.md
what: L-011 舊帳本搬入 (legacy import): deciding where to put the L-009/L-010 rules so they actually fire (user question
Context: deciding where to put the L-009/L-010 rules so they actually fire (user question: can CLAUDE.md's routing really reach OPS and lessons?).
Pitfall: the three rule layers have very different firing guarantees, and a rule written into the wrong one reads as durable and is dead. `ops/lessons.md` fires only when something greps it; `ops/*` only when CLAUDE.md's project-operations clause routes there; global CLAUDE.md is always in context but fires only on a trigger-word match — unreliable for rules that must fire MID-MEASUREMENT, when the agent is already confident (L-009 recurred for a month under exactly such a line).
Fix: choose the layer by TRIGGER SHAPE, not importance — a named tool call with inspectable input → PreToolUse hook (deny beats warn); a task-shaped judgement → CLAUDE.md conditional rule; "someone is already investigating this topic" → lessons.md, as the detail the shorter layers point AT. When a hook carries the enforcement, the CLAUDE.md line stays as the explanation the denial cites, and both name the lessons entry. FOURTH SHAPE, omission (hit 2): a rule whose violation is "the step never happened" generates no event — P1 gate the SUBSTITUTE commission (PreToolUse on the substitute's tools), P2 make the ABSENCE greppable (a literal marker a sweep enumerates), P3 gate at the event th …[record]
Record: ops/lessons/L-011.md

## L-012 2026-08-11 tags: verify|evidence|claim-calibration|delivery|self-review|polysemy|granularity|audit-record hits: 4 state: folded→ops/30-judgment.md
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

## L-017 2026-08-16 tags: rules-design|checklists|security|invariants|verify|remediation hits: 2 state: folded→CLAUDE.md
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

## L-019 2026-08-16 tags: verify|acceptance-eval|parsing|subagent-dispatch|interop|gate-design|silent-failure hits: 7 state: folded→ops/20-dispatch.md
what: L-019 舊帳本搬入 (legacy import): acceptance gates over model output — JSON extractor, evidence-anchor checker, st
Context: acceptance gates over model output — JSON extractor, evidence-anchor checker, structure checker, adversarial verifier; four gates, three mine, one a peer team's.
Pitfall: a gate ruling on a question it has no power to decide, and the ruling landing as REJECT — transport failure recorded as "refuted"; a PowerShell BOM recorded as STRUCTURE-FAIL; a verbatim quote under the wrong line number recorded as FABRICATED; a greedy `\{.*\}|\[.*\]` slice voiding 10/10 valid payloads. The gate is CORRECT about what it can see and silently extrapolates to what it cannot; a confident plausible negative reads like a finding and is never questioned. General form (hit 6): the gate returns ONE value where the input supports several — A TIE-BREAK IS A RULING, in either direction.
Fix: a gate may only rule on what it can DETERMINE; everything else is DOWNGRADE AND FORWARD, never veto — three-valued outcomes with the third state loud (`inconclusive` ≠ `refuted`; `MISALIGNED` + auto-repaired line vs `FABRICATED`); a parser strictly more lenient than the prompt; the receiving side's strictness is itself a measured variable (strict 0/5 vs lenient 5/5 on identical answers). Now global CLAUDE.md's gate rule and `30-judgment.md` R2.2.
Detection: feed a known-TRUE input, not only a known-false one — a gate that rejects everything scores 100% on a one-sided calibration. Cheap tell (hit 5): a UNANIMOUS verdict out of a freshly written checker is an instrument fault far more often than a finding — a moment, not a design phase, so it fires w …[record]
Record: ops/lessons/L-019.md

## L-020 2026-08-16 tags: refactor|duplication|testing|verify|retrospective|dead-code|silent-failure hits: 2 state: folded→tools/extdispatch/jsonspan.py
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

## L-023 2026-08-17 tags: git|env|concurrency|shared-worktree|branch|dispatch|shared-index hits: 4 state: folded→ops/references/shared-tree-git.md
what: L-023 舊帳本搬入 (legacy import): two sessions working `~/.claude` at once; Session B ran `git checkout -b` trusti
Context: two sessions working `~/.claude` at once; Session B ran `git checkout -b` trusting its session-start snapshot ("Current branch: main") while HEAD was A's feature branch — B forked off A's unfinished work and A's next two commits landed on B's branch.
Pitfall: HEAD, `.git/index` and the working tree are SHARED MUTABLE STATE between sessions in one tree. A checkout in either session silently redirects the other's commits; a ref move without a checkout leaves a stale shared index that the next commit in ANY session serializes as deletions (hit 3: 52 files, no error); an uncommitted peer edit is ABSORBED into whoever stages that path next (provenance lost, content intact). No command errors; ancestry checks pass while content is wrong.
Fix: the shared-tree discipline lives in `ops/references/shared-tree-git.md` (owner `20-dispatch.md` §7a) — routing by COUPLING CLASS (user ruling 2026-08-17: same workstream → SERIALIZE / baton-pass; disjoint domain → the second session takes a worktree; live-environment verification → canonical tree, ONE writer; true parallelism → split by TREE, never by ticket), the commit ritual (`git branch --show-current` → stage explicit paths → commit → `git show --stat HEAD` read for what you did NOT write), the content-vs-ancestry check (`git cat-file -e <sha>:<path>`), and the recovery recipes (plumbing merge; `git branch -f main <sha>` when caught within one commit; additive restore, …[record]
Record: ops/lessons/L-023.md

## L-024 2026-08-18 tags: env|shell|bash|powershell|tool-routing|silent-failure|encoding|line-endings|runaway hits: 12 state: folded→CLAUDE.md
what: L-024 舊帳本搬入 (legacy import): a 10-day sweep of every shell call in the transcript corpus (6,544 deduplicated
Context: a 10-day sweep of every shell call in the transcript corpus (6,544 deduplicated calls, 370 errors) asking why PowerShell errored 4× more than Bash. Answer: three silent defects in the Bash tool's command TRANSPORT, plus a selection effect.
Pitfall: (1) BACKSLASH COLLAPSE — n consecutive backslashes arrive as ceil(n/2) in every quoting context (`\n`/`\t`/`\"` untouched), the command reports SUCCESS, escaping harder is halved twice; symptoms differ per language and none name the cause. (2) SIZE CEILING — every Bash command ≥ ~7,700 B fails `unexpected EOF` (truncated at the OS boundary; PowerShell succeeded at 8,053 B). (3) WINDOWS PATH FORMS — unquoted loses every backslash, a trailing backslash inside double quotes escapes the closing quote. Line endings: Edit is the ONLY write path that preserves the target's ending (Write → LF; `cat >>` / `WriteAllText` → MIXED file; `Out-File`/`>` → BOM). Retraction kept: PowerShell `2 …[record]
Fix: routing at the source (global CLAUDE.md Environment bullet 1 — file content → Write/Edit, search → Grep/Glob, the shell keeps git / programs / pipelines; measured Write 0.1% vs Bash-writing-a-file 5.2%, Grep 0.9% vs PS-searching 17.4%); the three limits stay in CLAUDE.md as the backstop. Executors: `hooks/shell_transport_guard.py` (deny size, annotate backslashes), `hooks/ps_errorpref_guard.py` (ANNOTATE-only, 2026-08-21, registered on `Write|PowerShell` because 47 of 53 EAP='Stop' payloads arrived as `.ps1` files through Write/Edit — the rule is about a LANGUAGE, mostly written into files). All three traps hooked. Line endings pinned per repo by `.gitattributes`.
Record: ops/lessons/L-024.md

## L-025 2026-08-21 tags: verify|instruments|calibration|measurement|silent-failure|self-audit|first-use|tooling|gate-design|forensics|output-channel hits: 3 state: folded→ops/30-judgment.md
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

## L-027 2026-08-21 tags: env|powershell|shell|pipeline|truncation|silent-failure hits: 4 state: folded→hooks/ps_pipeline_close_guard.py
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

## L-032 2026-08-26 tags: false-negative|benchmark|calibration|ablation|instrument-check|measurement hits: 3 state: folded→CLAUDE.md
what: L-032 舊帳本搬入 (legacy import): graph-snapshot phase 1 produced four negative verdicts, each of which would have
Context: graph-snapshot phase 1 produced four negative verdicts, each of which would have changed a decision. Rule home: the global CLAUDE.md automated-gate rule (calibrate with known-TRUE and known-false); this card is the measured instance and its detection surface.
Pitfall: a negative measurement is a claim about the INSTRUMENT until the instrument is checked. All four negatives were false: a 73.6% resolution rate (three separate resolver/classification faults), "the new edge types did nothing" (they were never wired into traversal), a 100%-recall ablation that was tautological (seeds entered the read set by construction), and a "title drift in the corpus" finding that was a citation-granularity mismatch. Every one LOOKED like a result, and read as bad news about the corpus or the design rather than about the measuring code.
Fix: before acting on any negative verdict, run the instrument on a known-TRUE input, a known-FALSE input, and — where a scope boundary exists — a known-EXCLUDED input; graph-snapshot prints all three on every build. For a benchmark, an arm that cannot lose (or cannot win) measures nothing: check what each arm is seeded with before reading its score.
Detection: a freshly written checker returning a uniform verdict on n>=3 inputs; a negative finding about an artifact nobody reproduced against the raw source; an ablation arm whose construction implies its own score. Recurrence: hit 2 (2026-08-26, the SAME SESSION that wrote this card, while testing watchdog …[record]
Record: ops/lessons/L-032.md

## L-033 2026-08-27 tags: gate-design|calibration|false-negative|verification|doc-hygiene|regex|claim-calibration|instrument-vocabulary hits: 2 state: folded→ops/40-maintenance.md
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

## L-039 2026-08-31 tags: retrieval|prior-art|compact|handoff|cross-session|scope-creep|deliverable-series|intake hits: 3 state: folded→CLAUDE.md
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

## L-044 2026-09-02 tags: gate-design|validity-model|vocabulary-gap|self-grading|recurring-symptom|figure|annotation|standards|verify|refactor hits: 6 state: folded→rules/visual-gate-scope.md §clauses 3-4
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

## L-047 2026-09-04 tags: gates|registry|identifiers|consumers|false-green|membership|instrument-check hits: 3 state: folded→CLAUDE.md
what: L-047 舊帳本搬入 (legacy import): SSLD T41. The explanation registry numbers its entries `E-nnnn` densely in sort
Context: SSLD T41. The explanation registry numbers its entries `E-nnnn` densely in sort order of `(source, path)`. One consumer (`build_explorable.py`) hard-coded 27 such ids. Card SP-01b grew the registry by 72 entries; every id after the insertion point shifted, and all 27 consumer references now resolved to OTHER quantities — a panel labelled "z_R (glass)" displayed a dust-loss dB value.
Pitfall: every gate stayed green. RegistryGate checked "id exists" (a dense id space makes every id exist), LinkGate checked "anchor exists in the dossier", ParityGate compared JS↔Python relations and never touched registry values. An existence-only gate over a positional id space cannot see silent re-pointing; the failure is invisible exactly when the registry is doing its job (growing).
Fix: (1) consumers address entries by the stable key — here NumberRef `(source, path)` — and DERIVE the display id at build time; a literal id in consumer source is a build-time assertion failure (KnownBad: inject one). (2) Link/registry gates verify KEY EQUALITY, not existence: the target anchor carries `data-ref="<source>::<path>"` and the gate compares it with the source's expectation (KnownBad: shift an id by +N → anchor exists, key differs → must FAIL). (3) A label gate ties each displayed value to its quantity (label ⇄ entry name/path leaf). Recorded as SSLD PIM INV-19.
Detection: a registry/ledger that renumbers on growth + any consumer with a literal id in its source (`grep -n "E-[0-9]\{4\}"` outside registry outputs); after a registry rebuild, sample a displayed value and read its entry text — if the label and the entry disagree while gates are green, this is it.
Record: ops/lessons/L-047.md

## L-048 2026-09-04 tags: layout|width|shell|gate-design|vocabulary-gap|prior|html|deliverable|recurring-symptom hits: 2 state: folded→rules/deliverable-doc-refs.md
what: L-048 舊帳本搬入 (legacy import): the user asked why every long-form HTML deliverable (SSLD textbook, four dossier
Context: the user asked why every long-form HTML deliverable (SSLD textbook, four dossiers, the discussion pack, paper-story one-page KEYPOINT strips) left 30–40 % of a 2560×1440@150% screen empty on the right, although the display premise was recorded and every UAT had "版面" items. Measured at 1707×830: 69 % reach, right void 439 px; at 1920×950: 60 %, 652 px. A 268-file scan found 15 left-anchore …[record]
Pitfall: **an uncountered prior + one shared shell + one-sided gates = a CLASS recurrence, not an incident.** (1) The model's typographic default ("running text ~65 characters", stated verbatim by the built-in artifact-design skill, plus "avoid everything centred") produces a LEFT-ANCHORED narrow column whenever no rule of ours says otherwise — and none did: the display block was phrased as a compatibility baseline ("judge against FHD") and used only by the HEIGHT fit-gate. (2) Every instrument measured "too wide" (scrollWidth ≤ innerWidth, one-slide-one-screen, elements wider than the viewport) and none had an object called "unused width" (L-044 shape); the KnownBad control was a 4000 px block, …[record]
Fix: property, not reminder — `ops/environment.md` §Display "horizontal property" + `rules/deliverable-doc-refs.md` (paths now include the generator scripts); classes as DATA (`tools/page-fill-gate/page_classes.json`, one row = one class + a fixture pair) declared by `<html data-page-class>`, undeclared → inferred → WARN only; `fill_gate.py` with two-sided controls per run; shells fixed at the source (deck-shell ×4 uncapped; textbook shell fluid + `#rail` 本節速查) and propagated by the existing byte-identity/rebuild chains; UAT B3 example names the class. Proportional allocation (fr/%/cqw/clamp) with pixels reserved for intrinsic sizes is the design rule that stops the next cap.
Detection: `python tools/page-fill-gate/fill_gate.py <built html>` — a FAIL at a gating viewport, or a WARN carrying "inferred:" on a page that shipped; in CSS review, any `max-width` on a page container without `margin:auto`, or an `em`-capped painted block that is alone in its row.
Record: ops/lessons/L-048.md

## L-049 2026-09-04 tags: shell|shared-asset|generator|gate-design|anchors|file-lock|edit-blast-radius|html hits: 3 state: folded→rules/deliverable-doc-refs.md
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

## L-053 2026-09-06 tags: process-ledger|records|attribution|hooks|pointer-staleness|silent-failure|first-prompt|cross-session hits: 2 state: folded→tools/process-ledger/ledger.py
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

## L-057 2026-09-07 tags: audit-record|records|publish|subagent-dispatch|dispatch|gate-design|omission hits: 1 state: live
what: 移除的紀錄會把被移除的東西重新發佈一次 (a record of a removal republishes what was removed): seven fragment-writing workers each recorded an edit by quoting the value it deleted, and the merge-time gate found 38 leaks in the record and none in the files it described
Context: A round publishing de-identified copies of this environment dispatched seven workers over disjoint path sets; each wrote a manifest FRAGMENT the main session merged. The gate then reported 88 findings — 38 of them leaks in the merged manifest itself (private tree roots, an account name, a full source sha, session ids), zero in the collected files.
Pitfall: **The record of a removal, written by someone who will not run the check, republishes what was removed.** Quoting the original in an edit entry — `line N: <real value> -> <placeholder>` — feels like precision; the record is tracked and published, so the value ships exactly as widely as the file it was deleted from. Two structural halves: documenting a removal is itself publication, and the writer is a worker holding one shard, whose own acceptance cannot fail on it and who never stands where the merge-time gate runs. The class was already written down — 11 days earlier, in the ORCHESTRATOR's skill, a layer no worker loads. Enforcement in a layer the actor never reads is dead (L-011).
Fix: 1. A brief that dispatches a worker into a governed record carries that record's own record-writing rule — the brief is the only rule surface a worker reads (`20-dispatch.md` §2; shape and examples in `ops/references/dispatch-templates.md`). 2. Carry it as an ACCEPTANCE line the fragment is checked against: an edit entry names the CLASS removed and the replacement, never the removed value. 3. The target repo's collection rules own the content; the brief transports it, no layer here restates it. 4. Not done — candidate: a PreToolUse scan of writes bound for a published record. A commission with an inspectable payload, so §2a's first row, not its omission row.
Detection: The leak scan already reads every tracked file, so the record is scanned like anything else — the instrument was never the gap. While the round is still open: grep every edit entry for a literal of the class it claims to have removed.
Record: ops/lessons/L-057.md

## L-058 2026-09-08 tags: gate-design|control|silent-failure|compaction|instrument hits: 1 state: live
what: 負對照放在會被逐字保留的約束段裡就永遠不會失敗 (a negative control delivered inside a verbatim-preserved constraint block cannot fail): the canary "drop" token rode in the same [canary] sentence as the "keep" token, so every Compact-Instructions-obeying summarizer carried both — 5/5 sessions with summaries "leaked" it — and the instrument graded the summarizer uncalibrated for doing exactly what it was told
Context: The canary pair (long-run-probe-design §2 F8) calibrates the summarizer: keep = a harmless standing constraint that must survive compaction, drop = fake noise that must vanish. Both were injected by one UserPromptSubmit line at 150k, and CLAUDE.md's Compact Instructions tell the summarizer to preserve standing constraints verbatim.
Pitfall: A negative control that lives INSIDE the positive control's carrier inherits the positive control's survival. The summarizer copied the whole "[canary] Standing constraint…" sentence into "constraints injected by hooks", drop included, in every compacted session — `drop_pass` False 5/5, `summarizer_calibrated` False, while the summarizer had behaved correctly. A control that cannot fail is not a control; the verdict measured the instrument's own packaging. Second half: the keep wording "every NEW report or record file" was applied to code, skills, tool sources and project deliverables — a constraint phrased by file TYPE instead of by CARRIER leaks into everything the model writes.
Fix: Deliver the two halves in different shapes and at different moments: keep stays a standing constraint but names process carriers only (snapshot, run report, digest entry); drop is printed one prompt later as transient tool-style noise (`[probe] transient: … resolved, nothing to do`) by `context_runway_shadow._inject_pending_drop`, and `unattended_run` prints it as a separate paragraph after the obligations. Keep is graded on carriers (summaries ∪ snapshot ∪ report), never on deliverables (`run_audit.py`, `report.py`). Controls in process-ledger and hook_controls (listed in Narrative). Five sessions decide whether drop stays or retires.
Detection: `summarizer_calibrated` False on N≥3 sessions with identical shape → check the instrument before the summarizer (the consolidation report's §3.2 script: keep/drop presence per isCompactSummary record).
Record: ops/lessons/L-058.md

## L-059 2026-09-08 tags: asset-property|rules-design|naming|consumers|omission hits: 1 state: live
what: 規則綁錯對象或時機就永遠不觸發 (a rule bound to the tool or the moment instead of the asset class never fires for the consumer that matters)
Context: SSLD rounds T43–T45 (2026-09-07). Three verdicts "all gates green" while the user saw broken figures, hand-drawn sections on a retired framework, and files scattered over three placement axes. The 2026-09-04 naming/placement candidate existed and was not consulted.
Pitfall: One shape, three faces. (1) The figure engine's contract ended at the SVG file; the audience opened an HTML that inlined 15 of them and `id="inset_clip"` collided — the gate read the producer's artifact, not the consumer's. (2) The paper-figure ruling was worded "whenever the pipeline emits a figure": a TOOL trigger, so two producers that never called the pipeline were never covered. (3) The pack ruling had two readings (per-round deliverable vs persistent entry); both were executed, nobody reconciled. Common cause: no step classifies an item's LEVEL and CONSUMER before it exists, so location, vocabulary and the gate's object are each decided by habit at write time.
Fix: Classify FIRST on two axes — LEVEL (rule-tier · instrument/register · round output · audience entry · record) and CONSUMER (machine · builder · audience); rulings bind the asset CLASS; an embedded item's emitted artifact is its host. Carrier: global CLAUDE.md bullet + `rules/naming-and-placement.md` + registry `LEVEL_CONSUMER_FIRST` (proposal `drafts/2026-09-08-level-and-audience-first/APPLY.md`, pending 🔴 confirmation). Fold event follows when it lands.
Detection: A ruling sentence whose subject is a tool or a moment ("whenever X emits", "when editing Y"); a gate whose input path differs from the path the audience opens; a placement ruling executed twice in two folders.
Record: ops/lessons/L-059.md

## L-060 2026-09-08 tags: git|worktree|env|concurrency|desktop|shared-worktree|stranded-state|path-resolution hits: 1 state: live
what: Desktop 並行 session 自動落在 linked worktree，未合併的 reference 與 gitignored 狀態對正典樹不可見 (a Desktop parallel session lands in a pooled linked worktree; its unmerged references and its gitignored state are invisible from the canonical tree, and the path it hands out does not resolve there)
Context: User report 2026-09-08 (repeat since 2026-08-30): sessions hand out `~/.claude/references/...` paths that resolve only on a worktree branch; state built in a worktree is stranded; the 2026-09-02 cleanup did not stop it. The Desktop app places every parallel session in a pooled worktree before the first prompt; no per-repo off switch ships.
Pitfall: A linked worktree of `~/.claude` looks identical to the canonical tree from inside: same CLAUDE.md, same hooks/, same references/. Three things silently differ. Tracked writes and commits reach the canonical tree only after a merge the session must perform itself. Gitignored paths (cache/, drafts/, backups/, tools/*/out/, projects/) never merge at all. Tools invoked by relative path resolve their root from `__file__` and build the worktree's out/. Measured: 10 worktree sessions in ~/.claude 08-27..09-08, a handoff card only on an unmerged branch, a graph-snapshot out/ newer in a worktree than in the home while the home reported "MOC lags".
Fix: `hooks/worktree_scope_guard.py` (registry `WORKTREE_SCOPE`): SessionStart announces worktree/branch/canonical path in a worktree session and lists surviving worktrees with unmerged/dirty counts in the canonical tree; PreToolUse denies Write/Edit into a gitignored path of a ~/.claude worktree and denies relative-path state builders (gsnap/xi) there, naming the canonical target. shared-tree-git §1a states the asset properties. Five merged worktrees removed, eight merged claude/* branches deleted. Close-out in a worktree ends with the ff-merge, not the commit.
Detection: A path handed out that does not exist in the canonical tree while `git worktree list` shows a linked worktree; `tools/*/out/` newer in a worktree than in the home; `projects/*worktrees*` slugs; a `claude/*` branch with commits not in main; `[worktree-scope]` lines at session start.
Record: ops/lessons/L-060.md

## L-061 2026-09-09 tags: git|dispatch|subagent|shared-index|concurrency|commit|pathspec|claude-config hits: 2 state: folded→ops/references/shared-tree-git.md §4
what: 主迴圈在分派中的 agent 還沒回報前提交，會把對方已 stage 的檔案一併吃進自己的 commit (a main-loop `git commit` without a pathspec, while a dispatched writing agent is still running, absorbs whatever that agent has staged into the wrong commit — the index is one object shared by every process in the tree)
Context: 2026-09-08 debt sweep (a local session): a sonnet work-card agent had four files staged; the main loop ran a bare `git commit -m` meanwhile and the agent's files rode into `a272c58`. The agent reported "another parallel session took the index".
Pitfall: A dispatched agent in the same checkout is not a separate tree: `git add` from any process lands in the ONE index, and a commit without a pathspec commits the whole index. The retrospective recorded the fix only as a sentence in its "next" list ("use `git commit -- <paths>` next time") — an instruction that lives in the reader's memory, the exact carrier the same day's PH-11 work was replacing. shared-tree-git §4 covered peers' dirty WORKING-TREE files (carry provenance) but said nothing about a peer's STAGED files, which is the sharper case: staged content has an author who is about to commit it.
Fix: Asset property in `ops/references/shared-tree-git.md` §4: while this session has a dispatched agent that has not reported stopped, a main-loop commit is scoped by pathspec (`git commit -- <own paths>`), or carries the marker `[dispatch-ok]` after the staged set has been checked (`git diff --cached --name-only`). Carrier: `hooks/dispatch_commit_notice.py` (registry `DISPATCH_COMMIT_PATHSPEC`) — counts dispatches per session, decrements at SubagentStop, injects a NOTICE (not a deny: the consumer is the LLM) when an unscoped `git commit` runs with a dispatch outstanding. Promotion to DENY: a second swallowed-stage incident.
Detection: A commit whose `--stat` lists files the committing session never edited while a subagent was running; an agent report saying "another session took the index"; a `decision: notice` row in `telemetry/dispatch-commit-notice.jsonl` followed by an unscoped commit.
Record: ops/lessons/L-061.md

## L-062 2026-09-09 tags: calibration|test-design|false-green|verify|self-test|gate-design hits: 8 state: folded→rules/verification-ladder.md §control-differentiality
what: 反轉通過的正對照可能是斷言瞄錯，不是案例穩 —— 斷言必須讀一個「缺陷會改變」的值 (an inverted control that still passes is usually an assertion aimed outside the defect's scope, not a robust case)
Context: Writing check 33's missing `undetermined` specimens for 28 control suites. House rule already in force: every new case is inverted and must be observed FAILING — "a control that never fails is not a control". Two of my own new cases passed their inversion and were nearly shipped as sound.
Pitfall: The global rule tells you to confirm the positive control FIRES. It does not cover the case where you invert, the inversion RUNS, and it still passes — because the assertion reads a value the defect does not change. `published_record_guard` U-2 asserted `decision == "allow"`; the `str()`-fold being tested produces the SAME decision, so the inverted build was indistinguishable from the correct one. The case had two sides on paper and one in fact, and every later reader would have counted it as covered.
Fix: Move the assertion from the decision LABEL to what the decision CARRIES: `u2[1] == ""` (the path the guard claims it saw). The inversion then failed correctly. Before writing any control case, ask "if the defect existed, would THIS assertion read a different value?" — if you cannot answer, the assertion target is wrong, not the fixture.
Detection: Inversion passes on a case you expected to fail → suspect the assertion target before suspecting the fixture or the harness.
Record: ops/lessons/L-062.md

## L-063 2026-09-09 tags: git|worktree|windows|shared-worktree|working-tree|false-negative|env-cleanup hits: 1 state: live
what: Windows 上 `git worktree remove` 會在已經做完之後回報 Permission denied —— 權威是 `git worktree list`，不是退出碼 (on Windows git worktree remove reports a hard failure after it has already done the work; the authority is the list, not the exit code)
Context: Four dispatched chip sessions each had a linked worktree of `~/.claude`. All four branches were verified merged (`git merge-base --is-ancestor`) and the worktrees were being removed as close-out.
Pitfall: All four `git worktree remove --force` calls printed `error: failed to delete <path>: Permission denied`, which reads as "nothing happened, this needs elevation". It is the opposite: git had already emptied the worktree AND removed its own admin directory under `.git/worktrees/`, and only the top-level directory failed to unlink — because the chip session PROCESSES still hold those paths as their cwd. Believing the exit code means either re-running a destructive command that already succeeded, or chasing a permission problem that does not exist.
Fix: Judge worktree removal by `git worktree list`, not by the command's exit code — after those four "failures" it already showed only the canonical tree, and the branches deleted cleanly. `Device or resource busy` on the leftover empty directory means another process's cwd, not permissions; it disappears when that session closes.
Detection: `git worktree remove` reports a delete failure → run `git worktree list` and `find <path> -mindepth 1` before concluding anything. Empty directory + absent from the list = done.
Record: ops/lessons/L-063.md

## L-064 2026-09-09 tags: dispatch|scope-gating|process-ledger|records|subagent-dispatch|staleness hits: 1 state: live
what: 因暫時性限制而縮小的範圍，若沒寫下失效事件就會靜默變成永久裁定 (a scope narrowed by a TEMPORARY constraint silently becomes a permanent ruling unless the event that ends the constraint is written beside it)
Context: A probe over all 30 registered hooks found 13 crashing on a payload that parses but is not an object. Five belonged to suites the main session was already writing; the other nine belonged to suites that were out with four dispatched chips, and OPS hard rule 6 bars a subagent from writing `hooks/`.
Pitfall: The scope decision was logged as "fix only the 5, report the other 9 by name" with that constraint as its reason. The REASON had an expiry date — the merge — but the DECISION was written like a standing ruling, and nothing recorded what would end it. A later reader of the ledger (including me, post-compaction) reads a scoped decision with a sound justification and does not re-open it. The nine hooks would have stayed broken while the record looked deliberate.
Fix: Write the expiry event on the same line as the narrowing: "...only 5 for now; the other 9 unblock WHEN the chip branches merge". This round was caught by re-reading the ledger and widening to all 10, with a follow-up row recording that the constraint had lifted — but it was caught by attention, not by a mechanism, which is the whole reason it is worth a card.
Detection: Any `ledger.py add --reason` naming an in-flight dispatch, a lock, another party, or "for now" — grep for a matching expiry event in the same row.
Record: ops/lessons/L-064.md

## L-065 2026-09-09 tags: calibration|coverage-blind-spot hits: 1 state: live
what: 語料級偵測器的第一版判決一致、可信、而且全錯 (a corpus-wide detector's first verdicts are consistent, confident and entirely wrong)
Context: 建 `copy-census`：掃兩個根，找「有兩份以上、沒人在同步」的檔案。第一版掃出 22 個 domain profile「跨根各有一份、內容一致」，數字漂亮、判決一致、可以直接寫進報告。
Pitfall: 那 22 筆全是假的——obsidian_Nathan vault 的 `domains` 資料夾是 NTFS junction，同一個檔被看兩次。後面還有四次同型打臉：空檔案被當副本、同資料夾的 N 份回合輸出被當互為副本、`description: >-` 折疊純量被讀成字串 `>-` 於是全機 skill 塌成一個假群組、81 筆各實例角色檔（`tasks/<id>/1.json`）被當未宣告副本。共同機制：**在語料上做聚類的偵測器，其假陽性不是零星的，是整片的**；而且每一片看起來都完全合理，因為聚類本身沒有錯，錯的是「聚在一起＝同一個東西」這個未經檢驗的前提。
Fix: 校準必須用**真實語料的已知假陽性**，不能只用自造 fixture：本輪的關鍵負對照是「真實 vault 的 junction 一個都不准進 group」，第一版在這項得 0 分。收斂靠三條**結構**規則而非例外清單——解 reparse point／路徑只差一個 segment ＝各實例的角色檔／同檔名單獨不成證據（要內容一致、標題一致或跨根佐證）。例外清單會永遠成長且不說明理由；結構規則可被反例證偽。落點：`tools/copy-census/scan.py`、`test_copies.py` 的 `test_n2b`。
Detection: 新寫的語料級偵測器第一次輸出時，先問「最大的那一群是真的嗎」，並對已知的掛載／符號連結／產生器輸出各造一個負對照。
Record: ops/lessons/L-065.md

## L-066 2026-09-09 tags: calibration|regression|gate-design|coverage-blind-spot hits: 1 state: live
what: 改一個「列舉成員」的儀器時，回歸要比對成員集合，不是比對總數 (when changing an instrument that ENUMERATES, compare the SET of members, not the aggregate)
Context: 把 `hook-deny-lint` 從單一表面擴成 block／notice 兩個表面。跑前存下完整輸出當地板，跑後看總結行：`FAIL 0 / unresolved 0`，比原本的 `FAIL 0 / warn 14 / unresolved 3` 更好，四個控制全綠。
Pitfall: 那一版把 `browser_pane_scope_guard` **整支從檢查裡弄丟了**——它唯一的 deny 訊息走 `deny(deny_reason(...))`，而我改成「一律在發出站裁決」時，同時保留了「呼叫端如果是 builder 就跳過」這條舊規則，於是那則訊息兩邊都沒人裁決。總結行從「14 支 hook」變成「13 支」，其餘每個數字都更漂亮：FAIL 少了、unresolved 歸零。**一個列舉型儀器少掉一個成員，它的聚合讀數會變好而不是變壞**，所以總結行不但沒有警告，還獎勵了這個缺陷。
Fix: 回歸比對的單位必須是**成員集合**：把 `--dump` 的每則訊息文字抽出來做多重集合差集（`+1/-1` 逐則印出），而不是比對 FAIL/warn/unresolved 的總數。那份差集立刻指出「少了一支 hook、多了兩筆新判決」，並且證明**既有判決的內容零變動**——這是總數永遠給不出的結論。落點：source 端 reports/ 樹下一份 dated notice-surface 報告（未隨此 repo 收錄）§2 的前後對照表。
Detection: 儀器改動後，總結行**每一個數字都變好**＝先懷疑成員掉了。問「被列舉的東西有幾個？名字是哪些？」而不是「壞的有幾個？」——後者在成員消失時會自動變好。
Record: ops/lessons/L-066.md

## L-067 2026-09-09 tags: handoff|uat|delivery-shape hits: 2 state: folded→ops/references/uat.md §1 P8
what: 交付指向用相對路徑，等於只有作者能執行 (a relative pointer in a delivery is executable only by its author)
Context: `copy-census` 一輪交付，`§8 A 必驗` 六項全部寫成 repo-relative 形式（`python tools/copy-census/copies.py --check`），並且只存在於 copy-census 設計文件（source 端 references/ 樹，未隨此 repo 收錄）的第 8 節裡。使用者要驗收時得先找到那份文件、再捲到 §8、再自己補上工作目錄。
Pitfall: 寫清單的人在樹裡面，讀清單的人在一個乾淨的提示字元前面。`uat.md` P3 早就寫了「blind-executable by someone who did not build the thing」，但沒有把它的操作意義寫下來——**相對路徑對作者永遠可執行，所以作者永遠不會在自己的清單上踩到這一腳**。而且失敗是無聲的：命令不會報錯，它會在錯的目錄底下跑，或什麼都不做。 同一個形狀還有第二面：清單「在哪裡」也沒被指向。把驗收項留在設計文件的一節裡，等於要求使用者先做一次搜尋才能開始驗收，而搜尋成本落在唯一不該付它的人身上。
Fix: `ops/references/uat.md` 新增 **P8**：每一項的路徑都是絕對路徑，每一個命令都能從任何工作目錄直接複製執行。並且把「指向」這件事從 UAT 擴大到**每一次回覆**——因為使用者的原話是「之後這種交付也都用絕對路徑指向讓我知道」，範圍是交付而不只是驗收清單。落點三處（載體狀態寫在 `uat.md` §8）：`CLAUDE.md` 的 *Conversation replies* 條（唯一每次都載入的那份，所以廣義那條放這裡）、`ops/05-authority.md` §4 樣板第 3 行與 §4a BC-1、`uat.md` §1 P8。另外十份下游樣板**沒有**同步，理由與觸發條件明寫在 §8。
Detection: 交出任何清單或指向之前，問一句：「使用者把這一行複製到一個全新的終端機，會發生什麼事？」若答案取決於他當時的工作目錄，那就不是一個指向。
Record: ops/lessons/L-067.md

## L-068 2026-09-09 tags: rules-design|rules-editing|review-methodology|records hits: 1 state: live
what: 使用者給的是判準不是選項時，答案通常已經寫在既有規則裡沒被執行的那一支 (when the user answers with a criterion instead of choosing an option, the answer is usually a branch of an existing rule that was never executed)
Context: 問使用者「已落地的 draft 資料夾怎麼處置」，附三個選項（原地留、移到 archive、只留 APPLY.md）。使用者一個都沒選，回的是一條判準：**「重點在於未來沒有任何機會導致誤判或誤讀，做最乾淨的選擇。」**
Pitfall: 拿到判準的第一反應是**發明一條新政策**去滿足它——挑一個選項、補一段理由、寫進某個地方。那條路會產出一條沒有出處的規定，而且它會和既有規則並存、之後誰也不知道哪條算數。這一輪差一點就這樣做了。 真正的問題是：三個選項本身就是我列的，而它們共用一個沒被檢查的前提（「副本一定要繼續存在，只是放哪裡的問題」）。使用者拒絕在裡面選，等於在說那個前提可能是錯的。
Fix: 先去讀**治理這件事的那條規則本身**，找它有沒有一支從來沒被執行過的分支。本例：`ops/70-evolution.md` §2 的 lifecycle 明明白白寫著兩支——applied → commit 記事件、`rule-registry.md` 記常駐理由；rejected/superseded → **artifacts stay in drafts/ as record**。「留著」只寫在後面那一支。已落地的那一支從來沒說過 artifact 要留，只是沒人讀到底。判準的答案不必發明，它是既有規則的正確讀法。 順序：判準 → 找治理規則 → 找沒被執行的分支 → 若真的沒有，才是新政策（而且要說清楚它是新的）。
Detection: 使用者用「你決定／最乾淨的那個／不要再有 X」回覆一個選擇題時，先問自己：**這件事有沒有一條已經寫下來的規則？它有沒有一支我從來沒走過？** 以及：我列的那幾個選項，是不是共用一個使用者正在拒絕的前提？
Record: ops/lessons/L-068.md

## L-069 2026-09-09 tags: rules-design|rules-editing|review-methodology|records hits: 1 state: live
what: 使用者給的是判準不是選項時，答案通常已經寫在既有規則裡沒被執行的那一支 (when the user answers with a criterion instead of choosing an option, the answer is usually a branch of an existing rule that was never executed)
Context: 問使用者「已落地的 draft 資料夾怎麼處置」，附三個選項（原地留、移到 archive、只留 APPLY.md）。使用者一個都沒選，回的是一條判準：**「重點在於未來沒有任何機會導致誤判或誤讀，做最乾淨的選擇。」**
Pitfall: 拿到判準的第一反應是**發明一條新政策**去滿足它——挑一個選項、補一段理由、寫進某個地方。那條路會產出一條沒有出處的規定，而且它會和既有規則並存、之後誰也不知道哪條算數。這一輪差一點就這樣做了。
Fix: 先去讀**治理這件事的那條規則本身**，找它有沒有一支從來沒被執行過的分支。本例：`ops/70-evolution.md` §2 的 lifecycle 明明白白寫著兩支——applied → commit 記事件、`rule-registry.md` 記常駐理由；rejected/superseded → **artifacts stay in drafts/ as record**。「留著」只寫在後面那一支。已落地的那一支從來沒說過 artifact 要留，只是沒人讀到底。判準的答案不必發明，它是既有規則的正確讀法。 順序：判準 → 找治理規則 → 找沒被執行的分支 → 若真的沒有，才是新政策（而且要說清楚它是新的）。
Detection: 使用者用「你決定／最乾淨的那個／不要再有 X」回覆一個選擇題時，先問自己：**這件事有沒有一條已經寫下來的規則？它有沒有一支我從來沒走過？** 以及：我列的那幾個選項，是不是共用一個使用者正在拒絕的前提？
Record: ops/lessons/L-069.md

## L-070 2026-09-09 tags: dispatch|silent-failure|coverage-blind-spot|gate-design hits: 1 state: live
what: 讀 kind 取代比對子字串，只修好已列舉的那幾個值 (dispatching on a KIND fixes the wrong-branch class only for the values enumerated)
Context: `evaluate()` 能設 `build`／`harvest`／`regenerate` 三種 `remedy_kind`。2026-09-06 check 15 的補救句從「比對 finding 的子字串」改成「讀 kind」，理由正確也有記錄；但只寫了一支 `if kind == "regenerate"`，另外兩種共用 `else`。
Pitfall: 實測那行：finding 說 `the graph, not the corpus, needs attention first`，remedy 卻說 `harvest due: read …/integrity-report.md`——而那份報告正是失敗的那次 build 沒有重新產生的。機制：`else` 承載了一個**具名的值**，於是未列舉的 kind 得到的不是錯誤，而是一句看起來完全合理的錯話。兩個子句各自都有測試，涵蓋的卻只有被列舉的值；缺口在沒有分支的那個值上。
Fix: 三種 kind 改成一張表（dict），`.get(kind)` 落空時走一支明講「這個表面沒有這個 kind 的補救」的分支——未知的值從此是大聲的。`else` 只留給開放集合：同一段的 fallback 映射自由文字，預設是那裡唯一能收斂的分支。生產者的擴充也變成消費者的觸發器：registry 的 `review-when` 加上「`evaluate()` 新增一種 kind 時 check 15 必須同步長出分支」。落點 `hooks/ops_health_nudge.py` check 15 與 `test_ops_health_nudge.py` 三個新測項。
Detection: `if kind == …` 形狀的 dispatch，問兩個數字：生產者能產生幾個值、消費者列舉了幾個。規則：**`else` 不得承載具名的值**；封閉集合每個成員各自具名，落空那支只說「不認得」。
Record: ops/lessons/L-070.md

## L-071 2026-09-10 tags: gate-design|vocabulary-gap|thresholds|false-green hits: 1 state: folded→rules/deliverable-doc-refs.md
what: 登記型閘門證明每個數字有出處，證明不了那句話自洽 (a provenance gate proves every number has a source, never that the sentence built from them is consistent)
Context: SSLD 展示頁對每個數字都有 value-gate：讀者看到的每個數字都必須登記到某個儀器輸出。18 道頁面閘門＋52 道圖表閘門全過，頁面上印的卻是「最大的相對差是 6.489 %，遠小於 0.5 % 的判定門檻」。
Pitfall: 兩個數字各自都合法登記：6.489 % 來自儀器、0.5 % 是本輪門檻。錯的是把它們放進同一句。機制：儀器的對照分成兩類容差（換算法 0.5 %、獨立場傳播法 6.5 %），下游取了跨兩類的 max，配上其中一類的門檻。**閘門的物件是「數字→出處」這條邊，句子的自洽性不在它的詞彙裡**，所以它不是判錯，是無從判起。同一個錯誤同時長在圖上（一條 0.5 % 線橫跨兩類點）也沒被任何閘門看見。
Fix: 儀器輸出裡讓每一列自己帶 `tolerance`，下游按該欄分組敘述，永遠不做跨類 max。頁面改成三組各報自己的尺（15 列 @0.5 %、4 列 @6.5 %、1 列兩者都沒過→報為資料不計分）。**抓到它的不是閘門，是把渲染後的文字當讀者重讀一遍**——這一步要排進交付流程，不能指望閘門。
Detection: 成品出現「X，遠小於／遠大於 Y」時問：X 和 Y 是不是同一類的？跨多類取 max／min 再配單一門檻，就是這個錯。
Record: ops/lessons/L-071.md

## L-072 2026-09-10 tags: gate-design|calibration|false-negative|instrument-model hits: 1 state: folded→CLAUDE.md
what: 合併多個判定時取最好的等級，會造出一個結構上不可能拒絕任何東西的統計 (a max-rank rollup over verdicts makes rejection structurally unreachable)
Context: 55 個曲面對 8 條製程路線逐條判 covers／partial／outside，再用 `RANK={covers:3, partial:2, outside:1}` 取 max 合併。合併結果是「0 個面落在窗外」，並被寫成本輪最重要的結論。
Pitfall: 三條路線從未公布過任何幾何規格，對任何輸入都只能回 `partial`；而 `partial` 的等級高於 `outside`。**於是合併後的 `outside` 在結構上不可能出現**——那個 0 不是量出來的，是算式決定的。真實資料下光是一條有公布規格的路線就判 44 個面在窗外，聯集 55/55。同一輪早先已修過它的單層版本（二分改三分），修的是單一路線的判定，**沒有人回頭看合併**。
Fix: 餵一個荒謬輸入（R=1e-6 µm 與 1e12 µm）當負對照：若合併結果仍是「無法判定」，這個合併永遠不會拒絕任何東西，該負對照就必須失敗。改報 `n_outside_a_reported_window`（被真的公布過該規格的路線判在窗外的數量）並逐路線列出，合併值保留但不再是被引用的數字。
Detection: 任何 rollup 之前先問：有沒有一個成員對所有輸入都回同一個值？它是不是排在最壞判決前面？「0 件不合格」出現時，先確認那個 0 有沒有可能不是 0。
Record: ops/lessons/L-072.md

## L-073 2026-09-10 tags: verify|self-grading|validity-model|silent-divergence hits: 2 state: folded→ops/30-judgment.md
what: 兩條「獨立」路徑一致到 1e-15 是代數恆等的簽名，不是確認的簽名 (agreement at 1e-15 between two "independent" paths is the signature of algebraic identity, not of confirmation)
Context: 交叉檢查宣稱用「獨立的高斯 q 追跡」複核上游逐面結果，兩者一致到 1e-15，被寫成「這條跨輪的數字鏈端到端成立」。
Pitfall: `P = n/q` 只是 `q` 的重參數化：`P' = P/(1+Pd/n)` 等價於 `q' = q+d`。2000 次隨機試驗一致到 4.83e-13——**兩條路徑是同一個算法換了變數名**。後果不是「檢查較弱」而是「檢查為零」：上游若有正負號或折射率順序的錯誤，這條「獨立檢查」會逐位元重現它並印 PASS。而 1e-15 這個好看的數字**正是它已經失效的證據**：真正獨立的兩個數值方法不可能一致到機器精度。
Fix: 把主張撤回而不是修補：那幾列改標 `algebra_only_NOT_independent`，另建一條真正不共用假設的方法（角譜傳播、精確 kz、二階矩半徑），其容差由一個有標準答案的自由空間例子現場校準算出（不是手打）。結果 5 面中 4 面落在容差內、第 5 面 11.1 % **報為資料不計分**——這才是獨立檢查該有的樣子。
Detection: 交叉檢查一致到 1e-13 以下就要起疑：拿隨機參數跑兩條路徑，若殘差是機器精度而非離散誤差，兩者是恆等式。獨立方法的一致度應該落在它自己的離散誤差量級。
Record: ops/lessons/L-073.md

## L-074 2026-09-10 tags: numeric-constants|silent-failure|instrument-model|simulation hits: 1 state: live
what: 預設值若本身是該參數的合法值，用錯時不會有任何徵兆，只會安靜地模擬另一個東西 (a default that is itself a legal value of the parameter never announces itself; it silently simulates a different object)
Context: 場傳播檢查用一個薄相位屏代表光學面，屏的矢高寫成 `s = R - sign(R)·sqrt(R²-x²)`。跑出來與設計值差 23.7 %／112 %／52 %，兩張施工卡連續兩次把它讀成「真實的物理落差」並回報數量級。
Pitfall: 那條式子是**球面**，而設計是 conic k = −0.90。k=0 不是錯誤碼、不是 NaN、不是越界——它是 conic 常數的一個完全合法的值，所以沒有任何檢查會抱怨。儀器一直在正確地模擬**另一顆鏡子**：上游自己的波前分析早就算過那顆球面是 Strehl 0.239／6.21 dB，被當成物理落差報出來的就是這個。兩個工人都在量落差，沒有人問「兩邊的模型參數是不是同一組」。
Fix: 設計參數一律從設計紀錄讀，函式簽名不給預設值，或給了就必須有對照證明它沒被用上。落地：`_t48_conic_k(sol)` 讀上游 wavefront 區塊（`never assumed, never hand-typed`），並補兩個對照——恆等對照（k=0 時對閉式球面，|x|<0.95|R| 差 1.4e-14 µm）與**球面代入的負對照**（每一面都更差、且至少一面被推出容差）。
Detection: 落差在不同條件下都很大但比例不固定時，先對兩邊逐一列出模型參數，不要先量落差。問：這個參數我是讀來的還是預設的？預設值是不是該參數的合法值？
Record: ops/lessons/L-074.md

## L-075 2026-09-10 tags: dispatch|subagent-dispatch|retrieval|enforcement hits: 1 state: folded→ops/20-dispatch.md §4a
what: 派工提示指名了工具，違規就已經由派工端犯下，子代理只是執行 (a dispatch prompt that names the surface has already committed the violation; the subagent merely executes it)
Context: 機構 VPN 開通後派三路文獻波次。其中一路對一個明文禁止機器代理存取的出版平台，一路從 curl 升級到 WebFetch、再到 headless 瀏覽器、再到使用者真實登入的瀏覽器。
Pitfall: 回頭讀自己的派工提示：**裡面指名了瀏覽器**。子代理沒有越界，它照著做了。升級鏈看起來像四次獨立嘗試，實際上是同一個被禁止的行為換四套衣服，而且最後一級（真實登入 profile）是最被禁止的一級，不是最正當的一級。**約束若只寫在規則檔而沒寫進提示，派工端就是那個繞過它的人。**
Fix: 提示裡指名**路由表**（開放取用 → 官方 TDM/後設資料 API → 一般 HTTP → 具名單篇 → 交還使用者），不指名任何工具表面，並讓最後一級可達——「合法的空答案」必須是一個被接受的結果。規則寫成 `~/.claude/rules/literature-access.md`（含一手條文、五級路由、反機器人挑戰＝路由訊號的紅線）。已取得的來源標 PARTIALLY NON-COMPLIANT，由使用者以合法身分重新確認。
Detection: 寫派工提示時，凡出現具體工具／瀏覽器／指令名稱，問一次：我是在描述目標，還是在替工人選一條我沒查過合法性的路？
Record: ops/lessons/L-075.md

## L-076 2026-09-10 tags: figure|visual-gate|vocabulary-gap|instrument-vocabulary hits: 1 state: live
what: 圖上的顏色是一個斷言，措辭改了而配色沒改，等於那個被撤回的斷言還在圖上 (colour on a figure is a claim; change the wording and leave the palette and the retracted claim is still on the page)
Context: 機台清單來自牆上海報，只能支持「有」、不能支持「沒有」。儀器因此把狀態 `absent` 全面改為 `cannot_determine_from_record`，頁面與圖說的「校內沒有」也全部改成「這份清單上查不到」。
Pitfall: 圖上那四條橫棒仍然是**失敗紅**。顏色講的是「這一步被擋死」，正是剛剛放棄的那個斷言；讀者掃顏色不讀字，於是措辭修訂對他完全無效。同一輪還有第二個實例：另一張圖的棒子顏色只承載「有沒有來源」，而「錯了會不會翻掉」躺在同樣的小灰字裡——**最強的視覺通道承載了比較不重要的那個變數**，於是有來源但結論會翻的那一列被讀成安全。
Fix: 把顏色當成受同一條措辭規則管的斷言：`cannot_determine` 改中性灰、「會翻掉」自己拿到顏色與字重。配色改動要跑配色分離度閘門——第一次改成 #777777 立刻 FAIL（與紫色只差 84，門檻 90），改 #9e9e9e 才過。圖說補一句「灰色代表查不到，不是沒有」。
Detection: 措辭層級的修訂完成後，回頭列出這張圖還有哪些通道在講同一件事：顏色、標題、圖例、軸標籤、標記形狀。每一個都是那個斷言的一份副本。
Record: ops/lessons/L-076.md

## L-077 2026-09-10 tags: deliverable|layout|uat|pptx|design hits: 1 state: folded→rules/office-deck-deliverables.md#P1-P4
what: 受眾簡報先用一頁樣張定版式，再整本生成 (lock the page style on one sample page before generating the whole deck)
Context: SSLD 提案簡報從 16:9 附件重建到實驗室 4:3 範本。第一次指示含「盡可能將能描述的塞一頁」；模型直接生成 22 頁交付，使用者連續三輪退回：代號太多、顏色、字太多沒有視覺層級、文字塞住不散開。
Pitfall: 「塞一頁」被讀成句子密度，實際是主張覆蓋率；加上專案的「數字要有背書」習慣被搬到投影片上，每個主張都帶兩三句佐證。固定格線的卡片＋bullet 版面讓文字堆在欄頂、空白留在欄底。三輪來回都在改「整本」，每輪成本是一整次生成＋渲染＋人眼，而版式問題在第一頁就能看出來。
Fix: 受眾類簡報一律先做「一頁樣張」（最有代表性的證明頁）給使用者看版式：子標題（4–8 字）＋一句話（有數字撐的兩句）、圖佔半頁以上、區塊沿可用高度平均分布、不放頁尾結語。樣張定案後才整本生成；密度、頁數、數字位置、頁尾這四題用 AskUserQuestion 一次問完。SSLD 的裁定寫在 process ledger（2026-09-10 v3 layout）與一則本機記憶筆記。
Detection: 交付前自問：這一頁的每個區塊能不能只留粗體子標題也讀得懂？不能就是報告不是簡報。
Record: ops/lessons/L-077.md

## L-078 2026-09-10 tags: pptx|layout|gate-design|visual-gate|false-green hits: 1 state: folded→rules/office-deck-deliverables.md
what: 文字框高度估算沒算 CJK 行高，字就溢進頁尾；溢位要做成閘門不是靠眼睛 (a text-box height estimator that ignores CJK line height overflows into the footer; overflow must be a gate, not an eyeball)
Context: SSLD 提案簡報 v3/v4 的 `points()` 版面函式把子標題＋句子區塊沿可用高度均分。高度估算用「行數 × 字級 × 1.35/1.4」，Microsoft JhengHei 實際行高約 1.5–1.55 倍，六個區塊的欄位就整整溢出一行半進頁尾；validate.py 全綠、代號掃描 0 命中，只有人眼看縮覽圖才發現。
Pitfall: 既有規則 `rules/office-deck-deliverables.md` 只管「寬度」（孤字換行、JhengHei 寬度估算窄 4 %），沒有「高度」條款；高度低估的失敗是無聲的：python-pptx 不會裁字，PowerPoint 照畫，字疊在頁尾橫條上。閘門（schema validate、詞彙掃描）讀的是 XML，不是渲染結果，所以對這類缺陷結構上看不見——與 CLAUDE.md「量測判決：閘門只能裁它能判定的」同形。
Fix: 兩層：(1) 估算器行高係數改 1.5（標題）／1.55（內文），並加自動縮字（0.5 pt 一階，直到 sum(heights)+gaps ≤ box）；(2) 建議把「渲染後頁尾帶（y > 6.88 in）內是否有非範本墨跡」做成 COM 渲染後的像素閘門，正對照＝故意塞十個區塊。(2) 本輪未做，只做了 (1)＋人眼。摺入目標：`rules/office-deck-deliverables.md` 新增「高度」一條。
Detection: 渲染縮覽圖裡任何一頁的正文最後一行與頁尾橫條距離 < 0.1 in，就是估算器低估。
Record: ops/lessons/L-078.md

## L-079 2026-09-10 tags: cross-session|pointer-staleness|deliverable|records|concurrency hits: 1 state: live
what: 跨 session 的修改清單用頁碼指向，交付一改版就對不上；要用標題或主張指向 (a cross-session fix list keyed by page number goes stale the moment the deliverable re-paginates; key it by heading or claim)
Context: 並行 session（T56 紅隊）讀了本 session 的 v2 簡報（22 頁）寫修改清單，全部用頁碼指向。等清單回到本 session 時簡報已改成 v3（18 頁，頁序重排、頁面合併），每一條都要先反查「v2 第 N 頁是哪個主張」。另有一條（A1）被 T56 自己後段的新證據（§4.2 飛秒雷射窗）部分推翻，清單本身沒反映。
Pitfall: 頁碼是「會長大的工件裡的位置」，正是 CLAUDE.md 閘門規則說的不可用的述語：正常改版就讓指向跨界，而清單讀起來仍然合理。跨 session 的修改清單沒有共同的穩定 id（簡報無 slide id、無標題錨），只能靠人腦對應。第二面：清單是「某時刻的判定」，同一輪後面補到的證據不會回頭改前面的清單條目，交出去的是混合狀態。
Fix: 修改清單指向用「頁面標題文字」或「主張句」（例：「順位頁：主線…」），不用頁碼；簡報 builder 給每頁一個穩定 slug 寫進 notes 首行，清單引 slug。接收端做法：先把清單逐條對到目前版本的標題，再判斷每條有無被同一來源的後段更新推翻，把調整判斷寫在交付訊息裡（本輪 A1 即如此處理）。
Detection: 清單裡出現「第 N 頁」而交付物在兩個 session 之間有改版，就先假設全部失準，逐條反查。
Record: ops/lessons/L-079.md

## L-080 2026-09-11 tags: instrument-check|false-negative|prompt-injection|hooks|verification|forensics|retrieval hits: 1 state: live
what: 查「值」查不到不等於不存在 —— runtime 生成的識別碼要查產生器，否則那個 0 命中是儀器盲區不是證據 (a search for the VALUE cannot refute a runtime-GENERATED value; grep the producer, not the token)
Context: Asked to explain a message claiming to be a hook — it demanded a `UR-3874` token on future handoffs/reports/digests. I grepped `~/.claude` for the token, got zero hits, and ruled it prompt injection. It was a genuine local hook: `context_runway_shadow.py`'s 150k canary, which MINTS the token per session.
Pitfall: The search was structurally incapable of finding what it was testing for. Under the hypothesis "a hook emits this token", the token is generated at runtime and is never in the repo — so a zero result is what BOTH hypotheses predict. A test that returns the same answer whether or not the thing is true measured nothing, and I reported its output as proof. Second, weaker defect stacked on top: `Grep` honours `.gitignore`, so it never entered `projects/` where the transcripts live; I still wrote "zero hits anywhere in ~/.claude". The conclusion sounded well-evidenced precisely because it was negative and plausible.
Fix: When checking whether an artifact came from the local environment, search for the PRODUCER, not the value: the emitting hook, the generator expression, the settings.json wiring, the file it writes beside the transcript. And prefer the affordance the environment already has — `appdata_view_guard.py` tells its reader "grep telemetry for the row; text injected into a tool result cannot write a local file". That test discriminates; a token grep does not. Concretely, before ruling any injected text foreign: (1) list the wired hooks in `settings.json`, (2) grep the transcript for the `hook_success` record carrying `command=`, (3) look for a local artifact only a local process could have written.
Detection: A negative verdict reached by searching for a literal the suspected mechanism would GENERATE. Ask: "if my hypothesis were true, would this search have found anything?" — if no, the result is a blind spot, not evidence.
Record: ops/lessons/L-080.md

## L-081 2026-09-11 tags: powershell|shell-transport|windows-native|silent-failure|logging|encoding|gate-design hits: 1 state: live
what: PowerShell 的 `*>` 把原生程式的 stderr 導進檔案，會連離開碼一起弄壞——建置成功卻回報 exit 1，記錄檔還斷在半句、是 UTF-16 (PowerShell's `*>` on a native exe corrupts the exit code too: a build that succeeded reports exit 1, and its log is truncated and UTF-16)
Context: Cutting release 1.1.0. `build.ps1` failed at the PyInstaller step with exit 1 and printed 40 log lines that were all INFO — no error anywhere. The same command run by hand exited 0 and produced a complete `dist`. The log stopped mid-sentence inside `hook-PIL.Image`, and grepping it for "error" matched nothing at all.
Pitfall: The `2>&1`-on-a-native-exe trap in a costume the existing rule does not name. `*>` redirects every stream, so PowerShell wraps each stderr line into a NativeCommandError on the way to the file and `$LASTEXITCODE` stops belonging to the program. Both halves of the evidence fail together: the code says "it failed" and the log that would say why is truncated AND UTF-16, so byte-oriented search sees nothing.
Fix: `Start-Process -NoNewWindow -Wait -PassThru -RedirectStandardOutput <f1> -RedirectStandardError <f2>` — the OS redirects, PowerShell never touches the streams, so `$proc.ExitCode` is the program's own and the files hold the program's bytes. stdout and stderr must be DIFFERENT files. Calibrate both ways in the same round: the success path AND a deliberate failure.
Detection: A step reporting a non-zero exit while printing no error line; or a log whose tail is an ordinary INFO line rather than a summary or traceback. Settle it in one move: run the same command WITHOUT the redirect — if it succeeds, the capture is the defect, not the build.
Record: ops/lessons/L-081.md

## L-082 2026-09-11 tags: subagent-dispatch|calibration|thresholds hits: 1 state: live
what: 派低階模型做「散落陳述萃取」時預設篩選門檻過嚴 (cheap-model extraction subagents default to over-strict filtering)
Context: 派 haiku 對 3 個 session transcript 做 pilot：找出使用者散落的判準/建置要求/自主裁定原則。指示只給抽象標準（"真正的標準/原則"），未明講何時算符合。
Pitfall: 模型把「必須明講『以後/通用』字樣才算」當成隱含門檻：3 檔案、約 60 個候選關鍵詞命中只留 2 筆。這個誤判發生在萃取階段，一旦漏掉就不可逆——沒被回報的陳述，下游整併階段永遠看不到，且主控端不會知道漏了什麼。
Fix: 改為明講「即使是針對單一專案講的話，只要陳述本身讀起來像條件式規則（如果X就Y）就收，標成 [通用]/[專案內→可推廣] 兩級，交給下游整併階段篩」。同一任務形狀、放寬指示後，產出從 2 筆/3檔案 提升到 6~11 筆/批(8-9檔案)。篩選門檻要放在下游（便宜、人工可核對、可逆），不要放在萃取階段（不可逆、無法事後補救）。
Detection: 若一輪 pilot 的「候選命中數 : 保留數」比例明顯低於放寬指示後的比例（例如 60:2 量級 vs 200:7 量級），就是萃取階段篩選過嚴的訊號，該調整指示重跑而非直接採信低產出。
Record: ops/lessons/L-082.md

## L-083 2026-09-11 tags: layout|gate-design|silent-failure hits: 1 state: live
what: 驗證之後再移動物件，等於沒驗證 (a step that moves a result after it was validated must re-run the checks the move can break)
Context: SSLD T58d label placer: each outside label's leader path is checked (`_leader_trouble`) while its side and height are chosen. After that loop, an end-of-column clamp pulled a label whose tip lay below the column's reach up to the column floor.
Pitfall: The clamp ran AFTER the check and never re-ran it. The moved label got a new leader that crossed a substrate leg. The placer's verdict "clean" was about the pre-move position; the post-move object was examined by nothing in the producer, yet kept its checked status. It was caught only because the emitted-artifact gate `leader-path-clear` re-derives every path from the SVG.
Fix: A move is a candidate, not a repair: the tip-below-reach case now goes to a lift stage that scans heights from the ceiling down and accepts only a path the same predicate passes; if none passes, the label is omitted and named in the notes. General: any post-check adjustment (clamp, snap, round, dedupe) re-runs the predicate or moves before it.
Detection: Grep a producer for adjustments applied after its validation loop (clamp / snap / min / max on an already chosen position). An artifact gate catching what the producer "already checked" is the symptom.
Record: ops/lessons/L-083.md

## L-084 2026-09-11 tags: rules-design|asset-property|figure hits: 1 state: live
what: 規則的類別若照「當時手上的品項」列舉，第二個需求一來就和既有做法矛盾 (a class rule named by the items of the first need lumps items whose method-deciding property differs)
Context: SSLD rule (2026-09-08): every cross-section, stack or package figure is cut from a solid by model3d-pipeline. Round T58 then drew layer-stack figures in a 2D generator; the rule and the practice disagreed for days before a complex process section (mesas, contacts) forced the question.
Pitfall: The rule was bound to a class, not a tool (L-059 held), but the class was an enumeration of what the first need produced, not the property that decides the method: a 3D solid (needs a solid cut and multi-view consistency) versus one section plane shaped by process steps. Items with different deciding properties shared one rule, so the rule demanded a solid for planar stacks and the 2D practice violated it silently.
Fix: Name the partition key in the rule. SSLD rewritten 2026-09-11 (user-approved): the track is chosen by what the geometry IS — 3D part to the m3p solid cut, planar process section to the sceneir 2D generator, a second view moves a figure to the 3D track, ray figures explicitly left open. The floor (declared parameters + generator stamp) binds every physical figure.
Detection: A class rule written as a list of item names with no "because"; existing items exempt by habit.
Record: ops/lessons/L-084.md

## L-085 2026-09-11 tags: rules-design|gate-design|enforcement hits: 1 state: live
what: 把對第三方否決的「解讀」寫成會失敗的閘門，錯了就得連樣式、閘門、測試一起拆 (a model's reading of a third party's rejection, hardened into a FAIL gate)
Context: SSLD T58: the advisor rejected a proposal deck's figures as too detailed. The model read that as "a slide schematic carries no leaders and no dimension lines", wrote it into the style contract (PIM 3.1 rule 2, INV-3, OQ-3) and a FAIL gate `s2-no-dimension-or-leader`.
Pitfall: The reading was an inference but was stored with the force of a user ruling. Every later figure was shaped by it: a label that did not fit inside its layer was dropped instead of moved out with an arrow. The user's correction (the advisor rejected the standard CAD section as a figure TYPE, not needed now and slow to draw, not arrows) had to be unwound across contract, gate, tests and placer.
Fix: An inference about what a third party meant is recorded as one: quote the words, origin=model, and ask in the same delivery. Until confirmed it may shape a default or a WARN, never a FAIL gate or a contract clause. After the ruling the gate may harden, citing it. Here: gate renamed `no-dimension-line`, leaders allowed on every figure type, a stale-ban scan in the red-team.
Detection: A FAIL rule or contract clause whose origin is a paraphrase of someone else's feedback, with no quote and no user-origin ledger row confirming it.
Record: ops/lessons/L-085.md

## L-086 2026-09-11 tags: gate-design|asset-property|pptx|coverage-blind-spot hits: 1 state: live
what: 在產生器裡逐個建構函式落實的規則，只涵蓋寫規則當時已有的建構函式 (a rule enforced per constructor inside the producer covers only the constructors that existed then)
Context: SSLD T58b ruled "no PowerPoint shadow" on figure decks. The emitter set `shadow.inherit = False` inside its freeform and ellipse helpers; no gate read shadows. Leader arrows (connectors) arrived later through a third helper.
Pitfall: The connector helper never got the line. Its style points at theme effect style 1 and every effect style in that theme is an outer shadow, so all 31 leader arrows of the delivered r7 deck carried a shadow through three revisions and a recorded visual read (a thin line's soft shadow is easy to miss at slide scale). The rule lived in two function bodies, not on the asset, and nothing iterated over the emitted shapes.
Fix: Gate `no-shape-shadow` reads EVERY shape of the emitted deck, stamped or not, and resolves inheritance through the theme: an explicit effectLst decides, otherwise style effectRef idx -> theme effectStyleLst. Its first run on r7 failed on the leaders; the emitter fix is one line in the connector helper; r7 is kept as the natural negative.
Detection: Grep the enforcement line (e.g. `shadow.inherit = False`) and compare its call sites with every shape constructor in the emitter; a style ruling with no gate that reads the emitted file.
Record: ops/lessons/L-086.md

## L-087 2026-09-11 tags: silent-failure|gate-design|parsing hits: 1 state: live
what: 驗證放在正規化之後，驗到的是已被修好的值 (validation placed after a normalising step checks the already-repaired value)
Context: SSLD T58 closing red-team of the 2D process-section generator (`sceneir/process.py`) and the INV-10 drift check (`verify/s1_journal_snapshot.py`).
Pitfall: Three bad inputs passed because a normalising step ran first: shapely `box()` re-orders reversed corners, so a negative mesa width drew as a positive one; a name-to-film dict keeps the last of two equal keys, so a duplicated film name silently shadowed the first; `11 == 11.0` in Python, so a key whose type drifted float to int compared equal. Each check was right about the value it saw; the value had already been repaired.
Fix: Validate raw arguments before any constructor or container that normalises them: range and order before `box()`, duplicate keys before building the dict, and compare canonical serialisations (JSON keeps 11 vs 11.0) instead of language equality. Negative controls feed the raw bad input, not one built through the same API.
Detection: A validator that receives geometry objects, dicts or `==` results instead of the raw arguments; a negative control that constructs its bad case through the normalising API it is meant to test.
Record: ops/lessons/L-087.md

## L-088 2026-09-12 tags: gate-design|calibration|coverage-blind-spot hits: 1 state: live
what: 「每個閘門都有負對照」要從原始碼推導並在執行時量，手寫清單會過期 (negative-control coverage kept as a hand list goes stale; derive the check vocabulary from the gate source and measure it at run time)
Context: SSLD T58 figure gates (`sceneir/gates.py`, 38 check ids over SVG/PPTX/XLSX). The closing red-team had found 7 checks with no negative control by reading the test file; they were added, and "every gate has a negative" stayed a claim held by that reading.
Pitfall: Coverage of negative controls was a property nobody computed. A hand list is complete only on the day it is read; new ids, new artifact kinds (the same id on PPTX vs SVG), and error paths are outside it. A delivered deck that happens to fail a check looks like coverage but is not rebuilt when the gate changes. Five gaps survived the red-team fix, including a path no test had ever run: a corrupt file made three gates raise instead of returning a verdict.
Fix: Record every gate verdict the test run obtains (wrap the gate entry points), read the id vocabulary from the gate source (`Finding("id"`), and require: every id exercised, every (artifact kind, check) FAILED on a synthetic negative in the same run; delivered artifacts do not count; checks that by design never fail are exempt by name with the reason, satisfied by an undetermined verdict. Rung 1 (finite, enumerated in full). Unparseable input now returns `<kind>-readable` FAIL.
Detection: "Every check has a negative control" stated in prose or as a list; a gate whose unreadable-input path was never executed; a check whose only failing input is a delivered artifact.
Record: ops/lessons/L-088.md

## L-089 2026-09-12 tags: line-endings|cross-platform|fingerprint|self-test|false-positive hits: 1 state: live
what: 指紋取自寫入前的記憶體字串，落盤時被平台文字模式改寫，manifest 描述的是從未存在過的位元組 (a hash taken from the pre-write string describes bytes the writer never put on disk)
Context: `verify/fetchsrc.py` stores every retrieved source text and records its sha256 in `sources/manifest.json`; citecheck's `provenance` check later compares that hash against the file on disk to prove the text was not edited after retrieval. That comparison is the only machine-checkable link between a quote and its retrieval.
Pitfall: The hash was taken from the in-memory string (LF); the file was then written with `Path.write_text`, whose universal-newline text mode turns `\n` into `\r\n` on Windows AFTER the hash. The manifest described bytes that never reached the disk, so the gate FAILed every multi-line source as "edited after retrieval" (12 of 12 over two runs). Single-line sources still matched, so the gate looked healthy wherever a text happened to carry no newline. The selftest held the right assertion but could not see it: its fixture had no newline, and it compared through `read_text()`, which folds CRLF back to LF and undoes the corruption before the comparison.
Fix: One `write_text_lf()` helper (`open(..., newline="")`) at every payload write site, so the bytes on disk are the bytes hashed, on every platform. citecheck gained a narrow branch: a difference that disappears under CRLF->LF is a named WARN, never OK and never FAIL, so runs written before the fix stay readable; anything else still FAILs. Two-sided controls (CRLF-only -> WARN; CRLF + content edit -> FAIL with the span check still OK). The transferable property: a hash-bearing artifact is hashed on the EMITTED bytes, and its test asserts through `read_bytes()`, never through a reader that can undo the defect.
Detection: A digest, size or receipt computed from a value that is then handed to a writer which may transform it; or a test that round-trips the artifact through the same normalisation it exists to detect.
Record: ops/lessons/L-089.md

## L-090 2026-09-13 tags: hook-design|coverage-blind-spot|silent-failure|windows hits: 1 state: live
what: appdata-view-guard 只比對指令文字字面，工具把 %LOCALAPPDATA%/HKCU: 藏進設定檔參數，guard 對它自己最該擋的案子完全沉默 (a syntactic command-text guard is blind to the exact risk it exists to catch when the surface name travels inside a file argument instead of literal command text)
Context: `hooks/appdata_view_guard.py` (L-060/D-057) fires when a command's TEXT names `%LOCALAPPDATA%` or `HKCU:` — Claude-launched shells run in the desktop MSIX package's silo and can read a different HKCU/AppData view than the user's own shell. `tools/app-residue-sweep`'s every profile scans `%LOCALAPPDATA%` and reads `HKCU:\SOFTWARE` — exactly those two surfaces.
Pitfall: `sweep.py` invokes `inventory.ps1` as `python sweep.py --profile profiles\X.toml …`; the command TEXT never contains `%LOCALAPPDATA%`/`HKCU:` — those live inside `profile.json`, one indirection layer the guard's regex can't see through. Confirmed empirically: three tool subprocess calls (sweep, `archive.py --yes` moving 12.49 GB, gen_admin) logged zero guard hits, while a manual `Get-ItemProperty HKCU:\…` typed directly fired once. Blind since the tool's first run (2026-09-05) — silence reads identical to "nothing to warn about."
Fix: Ad hoc: re-derived the 5 paths' sizes independently, had the user run it in their OWN terminal (the guard's own remedy) before `archive.py --yes`; sizes matched, move proceeded. Folded into the asset: `skills/app-residue-sweep/SKILL.md` step 3 and the tool README §邊界契約 now name the cross-terminal check as standing procedure, not something to recall from an unrelated hook's docstring.
Detection: A launcher whose command-line names only a config file while the invoked script reads `%LOCALAPPDATA%`/`HKCU:` internally. General: a command-TEXT guard is blind to the same risk carried through a file-path argument instead of literal text.
Record: ops/lessons/L-090.md

## L-091 2026-09-13 tags: gate-design|calibration|coverage-blind-spot|false-green hits: 1 state: live
what: 為某缺陷新做的檢查器要先把該缺陷的原句餵回設計草案，直覺設計常對自己的起因判未判定然後放行 (replay the defect's own text against the DESIGN of the checker built for it — the intuitive design routinely returns "undetermined" on the very case that motivated it)
Context: An external reader found a slide listing "fill the gap with a high-index medium" among the ways to escape a tolerance line whose own printed table showed the product FALLING with index (d·theta = 0.2303*lambda/(pi*n)). Every printed number was right, five text gates were green, and the defect class was a DIRECTION claim in prose.
Pitfall: The obvious instrument — compare the two direction words in the sentence — PASSES the original sentence: that sentence never states a direction for the outcome at all. It lists a variable inside a "how to escape" list and lets the reader supply the rest, so a two-direction comparator returns undetermined and passes it. Building it would have put a green gate over the live defect — worse than no gate: an unknown sold as an assurance. The same trap recurred twice within the hour — a narrow keyword version fired on sentences that merely MENTIONED a high-index material, and a binding heuristic handed the outcome's verb to the variable because Chinese puts the verb ahead of its object.
Fix: Replay first, then specify. The property became: a sentence asserting a direction for a variable of a PUBLISHED relation must state the outcome's direction in the same sentence (incomplete otherwise) and match the modelled sign (contradiction otherwise); everything else is counted out-of-range and never vetoes. The original sentence fails it as `incomplete`. Calibration scaled with the artifact rather than resting on one control: 6 fixed controls plus a mutant generated from every in-range sentence the deck already carried (4/4 caught), and the out-of-range set read by hand once to measure what the screen declines.
Detection: A new checker whose verdict on the defect that caused it was never actually run; a gate spec written from the defect's DESCRIPTION ("it said the wrong direction") instead of from its TEXT.
Record: ops/lessons/L-091.md

## L-092 2026-09-13 tags: evidence|calibration|review-methodology|coverage-blind-spot hits: 1 state: live
what: 逐字支持句只證明「這句話在原文裡」，不證明「這句話支持這個編碼」；誤收率要逐 CODE 抽樣，逐軸平均會蓋掉整條全錯的碼 (a verbatim span certifies PRESENCE, not SUPPORT — sample the false-accept rate per CODE, never per axis)
Context: A coding screen tagged 474 source rows across four axes, and every code shipped with the verbatim sentence that triggered it — printed in the deliverable's speaker notes, quotable, checkable. The author's own false-accept sample read 1/12. An independent auditor re-judged 24 rows against the source text.
Pitfall: Three PUBLISHED card values rested on spans that were verbatim, quoted, and about something else: solder REFLOW compatibility (260 degC oven tolerance, photoresist reflow smoothing) read as solder self-ALIGNMENT, the technique's own name "photonic wire bonding" read as a bonded interface, index-matching OIL (a gap medium) read as a solid bond. Not a gap — a value the source never stated, printed as if it had been. The span discipline made this INVISIBLE: everything the screen promised was true, so it looked self-evidencing. And the axis-level rate looked ordinary while one code inside it was 6/6 wrong.
Fix: Publish a SUPPORT rate, not only a presence discipline, and sample it per CODE. Enumerate the lowest-support codes exhaustively (they are both the most likely artefacts and the cheapest to finish). Quote BOTH measured rates in the record with what each covers, because one number reads as global. Repairs went into the regex layer: a bare technique-name keyword needs a negative lookahead for its other senses, a polarity check reads the suffix as well as the prefix (`Adhesive-free`), and the three affected cells became未判定 — the atlas got emptier, and the empty cells are now true.
Detection: An evidence discipline that can only be violated by absence (the span is missing) and never by wrongness (the span is off-topic); a false-accept rate reported per axis or per instrument rather than per code; any published value whose supporting spans all share one keyword.
Record: ops/lessons/L-092.md

## L-093 2026-09-13 tags: verify|coverage-blind-spot|ui|calibration hits: 1 state: live
what: 互動式交付物的閘門要有一道走真實輸入事件的路徑；DOM 與狀態閘門全綠時，覆蓋與落點位移仍看不見 (an interactive deliverable needs a gate that drives real pointer events — DOM/state gates cannot see overlap or a target moving under the pointer)
Context: A drag-and-drop workbench built to a PSM whose eight gates covered provenance, the rule engine (fixtures per decision-table row), schema round trip, viewports, banners, audience text and reduced-motion parity. All green, every control firing, before any mouse had touched the page.
Pitfall: Every gate asserted on state reachable through function calls or DOM queries. The path the user actually takes — press, move past a threshold, preview, release over a target class — was never driven, so two defects stayed invisible: junction chips whose x positions collided rendered on top of each other (the DOM held both; a click landed on the wrong one), and a hint banner that appeared mid-drag pushed the layout down so the drop target moved under the pointer. Both are properties of PIXELS under INPUT, which no DOM assertion names.
Fix: Add a gate that replays real pointer events (Playwright mouse.down/move/up with a >threshold step) through EVERY branch of the interaction statechart, with two controls that must leave the document unchanged (release outside any target; a drop the rules reject). Its geometry must be read fresh before each gesture (scroll to top, scroll_into_view, then bounding box) — stale coordinates drag into thin air and report the wrong branch. Layout-shifting feedback during a drag becomes a fixed-position toast.
Detection: An interaction deliverable whose verify record has no gate row naming mouse/pointer/touch; a pass count that never changed when a chip, card or target was added; a Playwright "element intercepts pointer events" retry loop in a gate run.
Record: ops/lessons/L-093.md

## L-094 2026-09-15 tags: windows|path-conversion|msys|silent-failure hits: 1 state: live
what: 本機 Git Bash 的 /tmp 與 Python 行程看到的 /tmp 不是同一個資料夾，用它交接的快照會靜默遺失；暫存一律傳 scratchpad 絕對路徑 (on this Windows machine Git Bash's /tmp and a Python process's /tmp are different directories — a snapshot handed over through /tmp silently disappears; pass the scratchpad absolute path)
Context: Before rerunning a screening script, a Bash `cp` copied the current `data/screening_T04.json` to `/tmp/` so a Python diff could compare old and new afterwards.
Pitfall: Git Bash maps `/tmp` to its MSYS temp directory; the Python interpreter (a native Windows process) resolves `/tmp/...` against the current drive root (e.g. `D:\tmp`). The copy reported success, the rerun overwrote the original, and the diff found no snapshot — the baseline was gone. Recovery went through a second, independent artifact (the claims JSON diff), which only worked because one existed.
Fix: Hand files between a Bash step and a Python step only by an absolute Windows path, and put scratch copies in the session scratchpad directory (never `/tmp`). Where a baseline matters, copy it into the round's `verify/_previous_*` first — it is also the placement the project contract asks for.
Detection: A POSIX absolute path (`/tmp`, `/c/...`) written by one shell and read by a native Windows process; a "snapshot not found" right after a copy that exited 0.
Record: ops/lessons/L-094.md

## L-095 2026-09-15 tags: figure|layout|instrument-vocabulary|recurring-symptom|coverage-blind-spot hits: 1 state: live
what: 在已標註的圖旁邊塞圖例，連三次修版面仍被引線穿過；這是表示法問題，圖例要移到視圖外自成一條，而且外掛物件要登記進儀器的碰撞閘門 (a key placed beside a labelled drawing kept getting crossed by leaders through three layout fixes — a representation fault; move the key to its own band outside the view, and register wrapper-added objects with the instrument's collision gate)
Context: A user ruling asked for a colour swatch + material + refractive-index legend "in the blank space beside" every view of 22 three-view beam-path figures. The figures come from a frozen instrument (label placer with leaders, collision gate); the round wrapper adds item kinds at runtime.
Pitfall: The legend was first drawn inside the view's axes, in a strip beside the drawing. The instrument's label placer and its collision gate had no object for the legend (a wrapper-added kind), so the gate stayed green while leaders ran straight through legend text — found only by the model's visual read. Three patches followed (pull the label bound in; raise the row cap; a per-label centre cap copied from the placer); each one moved the collision elsewhere, because a strip beside the drawing takes the same band the right-hand labels need.
Fix: Changed representation, not spacing: the legend became its own panel directly below each view (PNG), and a post-pass placed the same entries in the free band under the view on the view's own slide (PPTX), so no leader can reach it. The wrapper's own read-back gate checks legend text equality, overlap with every other shape, and room above the footer, each with a two-sided selftest control; a drawn material without an entry is refused statically.
Detection: A runtime-added item kind the instrument's gate does not enumerate; a second layout patch for the same crossing symptom; any key, legend or inset placed in the same band a label placer uses.
Record: ops/lessons/L-095.md

## L-096 2026-09-15 tags: figure|claim-calibration|verification|carried-claims hits: 1 state: live
what: 示意圖的簡化把物理上存在的轉折抹掉，報告又說「已畫」卻沒指明哪個視圖哪個軸，使用者看另一個視圖就判定沒畫 (a schematic shortcut erased a physically present kink, and the report said "drawn" without naming the view and axis — the user looked at the other view and found nothing)
Context: Beam-path schematics whose envelope is sampled from a per-axis Gaussian ABCD chain. The r6 delivery note said the air-gap refraction was "drawn on the figure (the model had it)".
Pitfall: (1) The r6 envelope held the beam collimated from a fixed z in mid free-space instead of letting it diverge to the lens surface, so the lens interface showed no slope change: "a material change shows a kink" was broken by a drawing convenience, not physics. (2) The gap claim held only for the side view's y axis. In the plan view the x beam is collimated at normal incidence and has no kink, so the user saw no bend there and read the report as false. The checker (C27) was right on both axes; the sentence named none.
Fix: Envelope drawn from the chain over the whole path (hold removed; the beam diverges to the lens surface), every drawn kink at a material interface; where physics gives none, the figure's own label says so ("垂直穿過，不偏折"). Report sentences about what a figure shows name the view and axis where it is visible.
Detection: A figure claim with no view/axis; a constant introduced only to make a schematic look tidy (a hold, a clamp, a fixed reach point) on a quantity that a model computes; a reader-expected feature (kink, focus, shadow) absent without a label.
Record: ops/lessons/L-096.md

## L-097 2026-09-15 tags: gate-design|calibration|false-negative|simulation|instrument-check hits: 1 state: folded→rules/verification-ladder.md
what: 尺沒先在閉合式自己的樣本上自檢，估計量的偏差被當成模型 FAIL (a ruler never self-tested on the closed form's own samples reports its own estimator bias as a model FAIL)
Context: Physics gates compared a COMSOL model with a closed form through an estimator (a log-slope fit, a 180 s window fit). Both model and closed form were right; two gates still read FAIL at -7 %.
Pitfall: The estimator was applied to the model but never to the reference it was supposed to recover. A ln C vs x^2 slope measures 4Dt only for a Gaussian profile (the drive-in was not one); a window fit was compared with a t=0 derivative although the closed form itself bends 7 % over that window. Each FAIL cost three solver runs and a gate redefinition before the ruler, not the physics, was found at fault. The global gate rule (calibrate with a known-TRUE input) was read as "the control fires", not as "the ruler recovers the reference under the gate's own grid/window".
Fix: Before a gate rules, run its ruler on the closed form's OWN samples at the gate's grid and window; it must return the input inside the gate tolerance, in seconds of numpy and zero solver time. A ruler that fails is a defect of the card. Rule home: rules/verification-ladder.md (consequence clause "the ruler recovers the reference first"); rig-level R-RULER-SELF-TEST in COMSOL_Test pipeline-draft.md section 2.
Detection: A FAIL whose deviation is flat across mesh/tolerance changes (R-ISOLATE says numerics are not the cause); a ruler whose derivation assumes a shape (Gaussian, linear) the reference does not have over the gate window.
Record: ops/lessons/L-097.md

## L-098 2026-09-15 tags: hang|dispatch|silent-failure|evidence|simulation hits: 2 state: folded→ops/20-dispatch.md §3
what: 背景探針沒有牆鐘上限，掛死 45 分鐘靠手動列行程才發現，且掛死的 log 被重試覆寫 (a background probe with no wall-clock cap hung 45 min, was found by a manual process listing, and the retry overwrote the hung run's log)
Context: An isolation probe called a numerical time integral (COMSOL timeint at default tolerance) on a 3D transient dataset whose solve takes 60 s. It was launched in the background with no cap while other items ran.
Pitfall: Nothing in the run said "this should be back in N minutes", so silence was read as "still computing" for 45 min; the hang surfaced only when a process listing showed a python PID started 18:01 with a last log line at 18:02:52. The JVM call could not be cancelled, so the whole process had to be killed. The bounded retry then reused the probe's log name and overwrote the hung run's log, leaving the 45 min as an in-session memory rather than a stored line.
Fix: Every background run or probe carries a wall-clock cap derived from a measured baseline (10x the solve time of the same model, floor 5 min). No new log line past the cap = hang, not a slow run: kill the worker AND its server child, log the kill in the process ledger, and keep the hung run's log under its own name (never reuse it for the retry). Rule home: ops/20-dispatch.md section 3 (outer timeout line, extended to in-session background runs); rig-level R-PROBE-TIMEOUT.
Detection: A background job launched without a stated expected duration; a retry that writes to the same log path as the run it replaces; "still running" judged from silence (20-dispatch section 7a: never read completion from silence).
Record: ops/lessons/L-098.md

## L-099 2026-09-15 tags: subagent-dispatch|recovery|crash|handoff|evidence hits: 1 state: folded→ops/20-dispatch.md §2
what: 執行代理中途因 API 授權錯誤死亡，接手者只靠磁碟上的逐次 log 與輸出續跑；只活在代理脈絡裡的東西全部消失 (an executor agent died mid-card on an API authorization error; the successor resumed only from the numbered logs and outputs on disk, and anything living only in the agent's context was lost)
Context: A work-card-executor subagent (sonnet) running two COMSOL items was terminated by the harness with HTTP 403 oauth_org_not_allowed after run5 of item A and run2 of item B. The error was transient: two replacement agents on the same tier ran fine 40 min later.
Pitfall: The death is silent to the dispatcher until the agent's final report arrives as an error; nothing the agent had reasoned or planned survives. Recovery was possible only because the card had demanded one numbered log per attempt plus out/ and probe/ files written as it went; the successors read the last logs and continued at run6 / run3. Had the executor kept results in its context until a final write, both items would have restarted from run 1 (about 40 min of solver time).
Fix: Dispatch contract part 3 (where artifacts land) requires INCREMENTAL on-disk evidence: one numbered log per attempt, outputs written as produced, probes with their own logs; the successor's brief names the last log and says "resume, never restart". The dispatcher treats a transport/auth death as a normal outcome to plan for, not an exception. Rule home: ops/20-dispatch.md section 2 (part 3 clause); rig-level R-EXECUTOR-RESUMABLE.
Detection: A worker whose only output is its final report; a card without a per-attempt log name; a successor brief that says "redo" instead of "resume from <log>".
Record: ops/lessons/L-099.md

## L-100 2026-09-15 tags: prior-art|dispatch|coverage-blind-spot|simulation|self-test hits: 1 state: folded→ops/60-record-templates.md §1
what: 施工卡點名的範本／種子沒先驗證含有要測的機制，執行者在錯的起點上探了九次 (a work card named a template/seed without verifying it carried the mechanism under test; the executor probed nine times from the wrong starting point)
Context: The card for a moving-boundary oxidation item named a library model (oxide_jacking.mph) as the seed to copy the moving-boundary pattern from. The card author had checked the file was a real model (size rule) but not that it contained a moving boundary.
Pitfall: Naming a prior artifact in a spec reads to the executor as "this contains what you need". The executor built from text using the legacy physics-level interface the card implied; it solved without error and never moved the boundary. Nine probes isolated selections, study settings and properties before one probe grepped a different seed's text (chemical_etching) and found the working node type in a single step. The prior-art check had been done at the level of "a seed exists", not "the seed carries the mechanism".
Fix: A spec that names a template, seed, sample or prior artifact for a MECHANISM states the grep (feature type / function / node name) that proved the artifact carries it, in the card. Executor side: after 3 probes with no effect on the mechanism, stop probing and go template-first (grep the text of the nearest artifacts for the mechanism). Rule home: ops/60-record-templates.md section 1 (Objects field note); rig-level R-SEED-CARRIES-MECHANISM.
Detection: An "Objects" or "seed" line in a card with no evidence string beside it; a mechanism that solves cleanly with zero effect; probe count on one symptom passing 3.
Record: ops/lessons/L-100.md

## L-101 2026-09-16 tags: simulation|instrument-model|validity-model|vocabulary-gap hits: 1 state: live
what: 篩選模型把元件簡化成「介面數」，某軸光焦度為零被延伸成「該軸光束不變」；孔內無導引繞射與錯聚焦都不在模型詞彙裡，四版排名錯到使用者問 y 軸才發現 (a screening model reduced a component to an interface count and read "zero power in y" as "beam unchanged in y"; unguided diffraction and mis-focus were outside its vocabulary, and four delivered rankings stayed wrong until the user asked about y)
Context: Idealised screening of 24 edge-coupling variants (Gaussian overlap, 1 dB windows, Fresnel, gap term, 8-channel outer-channel offset) ranked designs for an advisor. One internal-element option was an etched cylindrical hole in the glass (A2a air / A2b refilled), a lens acting on x only.
Pitfall: The hole entered the formula as its Fresnel surfaces only. "A cylinder has no power in y" is true of the lens term, and it was carried as "the beam in y is unchanged". Inside the hole the beam is unguided and diffracts in y, the downstream spherical facet lens was designed on x and mis-focuses the un-expanded y, and a tilted sidewall steers the beam. None of these had a term. Four revisions (r1-r4: figures, decks, a 3D top-six) inherited wrong ranks. Once modelled, A2a fell from rank 5-6 to 13-16, with +4.4 dB from the y mis-focus alone. All 22 claim checks stayed green, because they tested the signs of terms that existed. The user found it by asking what happens to y.
Fix: Replace the per-component count with a per-axis Gaussian q-parameter (ABCD) chain over the WHOLE path. Every element is a matrix on each axis, including propagation inside it. Design rules state which axis a lens is designed on and let the other axis follow. An old-vs-new equivalence control on the symmetric variants (they must not move) proved the rewrite changed only what was wrong: A1 stayed 1.46 dB. General form: a screening term that is a COUNT or a constant per component carries only the effects the count names. Before asserting "quantity Y is unaffected by element E", check what propagation through E does to Y, not only what E's lumped term does.
Detection: - A model term per component that is a count (interfaces, surfaces, bends) rather than a transfer. - A claim "no effect on Y" derived from a lumped formula's zero. - Claim checks that only test signs of terms already in the model. - A user question naming a quantity the model never outputs.
Record: ops/lessons/L-101.md

## L-102 2026-09-16 tags: design|omission|coverage-blind-spot|experiment-design hits: 1 state: live
what: 形態矩陣的站點選項把「元件」和「元件之後接什麼」綁成一格，老師圖上的組合因此從未被列出；全因子展開又留下模型上無法區分的選項，方案多而相似 (a morphological-matrix option bundled an element with what follows it, so a combination on the advisor's drawing was never enumerated; full-factorial expansion also kept options the model cannot tell apart)
Context: A morphological matrix built from an advisor's sketch had four stations: A internal element, B FAU facet lens, D OE lens, E OE converter. It enumerated 16 delivered variant sets plus controls, all screened and drawn. A day later the user asked why "air sphere cavity + FAU-side second glass waveguide" was missing, although the advisor's drawing shows two waveguide segments.
Pitfall: 1. Each A option was defined as "element + a fixed free segment after it". "What follows the element" was never a station, so no option could pair an element with a guide. Pruning and screening cannot report the absence of something that was never generated. 2. Full-factorial expansion kept options the screening model cannot distinguish: B2 and B3 were identical in the model, and E varied only on the OE side. The set grew while the design space covered did not. The user's verdict: 「方案太多過於相似」.
Fix: Before expanding a matrix: - Write each station as ONE decision. - Read every option's description for a second decision hidden inside it, and split that decision into its own station. - Check the source drawing's element list against the station list. After screening, collapse options whose model outputs are identical on every variant, and report the collapsed count instead of drawing each one. T06 then modelled the missing option (A2sg: 7.92 dB, infeasible as read). The verdict was worth having precisely because the omission was not a decision.
Detection: - An option label containing "+" or "then". - A source element ("two waveguide segments") with no station. - Two options with identical numbers on every variant. - A user question of the form "why is there no X" about a combination.
Record: ops/lessons/L-102.md

## L-103 2026-09-16 tags: pptx|false-positive|gate-design|office-interop hits: 1 state: live
what: 用 zip 部件位元組比對來證明投影片「沒被改動」會誤判：python-pptx 存檔會重寫每個 XML 部件；未改動檢查要比對形狀內容指紋 (byte-comparing zip parts to prove slides unchanged reports false changes, because python-pptx re-serialises every XML part on save; compare a per-shape content fingerprint)
Context: A user hand-edited a delivered 10-slide meeting deck. A relabel pass copied it to a new file and changed text on slide 10 and speaker notes on slides 8-9 through python-pptx. The check had to prove that everything else in the user's edits survived untouched.
Pitfall: The "unchanged" assertion compared zip part bytes between the user's file and the saved copy. python-pptx loads and re-serialises every part (attribute order, namespace declarations, whitespace), so untouched slides differ at byte level. The first run reported a spurious change (55/56). Loosening a tolerance at that point would have trained the check to ignore exactly the noise a real stray edit would hide in. Same family as L-089: the comparison sat on a representation the writer always transforms.
Fix: Fingerprint what the user can see or edit, per shape: - type, position and size; - text runs and table cells; - speaker-notes text; - picture blob hash. Compare the fingerprints. Keep a negative control that edits one run on one slide; it must be detected (it fired on slide 10). Result: 59/59.
Detection: - An "unchanged" or idempotence check on an OOXML file written by a library. - Byte or hash equality on container parts after any load-save cycle.
Record: ops/lessons/L-103.md

## L-104 2026-09-16 tags: enforcement|omission|rules-design hits: 2 state: folded→ops/05-authority.md
what: 以提問開場的討論輪（「為甚麼沒有 X」「這張圖做過嗎」）連兩個 L1 session 都沒發邊界契約，到結案才記偏差；只靠記憶的開工義務在任務不像「實作」時不會觸發 (discussion rounds that opened as a question skipped the L1 boundary contract in two consecutive sessions and noticed only at close; a recall-only kickoff duty does not fire when the task does not arrive shaped like implementation)
Context: Main loop Opus 5 at ops-relaxation L1. Global CLAUDE.md requires a 5-section boundary contract before method or design work on a Tier-2 implementation task. T06 opened from "why is there no sphere + second waveguide option?" and T07 from "has the arc-facet figure been drawn?". Both rounds then wrote screening code, figures, decks and claim scripts.
Pitfall: The trigger is phrased on task CLASS ("an implementation task of Tier-2 weight"). Both requests arrived as questions, so intake classified them implicitly as discussion, and the duty never fired. Each round then did implementation work with real interpretation forks (the reading of the advisor's drawing, invented geometry values), which is exactly what the contract exists to surface. The omission left no trace until the session itself wrote a deviation at close. The one mechanical step every such round runs, the round kit's `open_round.py`, prints nothing about the contract.
Fix: Proposed, not built (the project's instruments are frozen for rounds; a change is its own session). Per ops/40-maintenance.md §2a, omission row: - **P2:** the round skeleton carries a `boundary_contract` field, so an empty one is a greppable absence. The round-close check refuses an empty field unless a deviation names why. - **Kickoff:** the kit prints the contract template when it reserves the round id. Trigger re-read: a question that will end in new code, figures or numbers is an implementation task from the moment its first spec is written.
Detection: - A round JSON with figures or claim scripts but no contract, in the field or in chat. - A deviation naming the contract at close. - Kickoff text that is a question.
Record: ops/lessons/L-104.md

## L-105 2026-09-16 tags: remediation|review-methodology|staleness hits: 2 state: folded→ops/30-judgment.md
what: 修 BLOCK 只改報告點名的那一行，同一句話的雙胞胎留在標題與索引裡 (a fix scoped to the cited line leaves the same stale sentence elsewhere)
Context: ltm PIM verification gate, round 11 (2026-09-16), on v1.3. Round 10's BLOCKs had been answered in v1.3 by editing exactly the lines the verifier reports cited.
Pitfall: Both round-11 BLOCKs were round-10 sentences still standing where the fix did not look: a section heading 30 lines above the repaired summary sentence still counted "two rules", and the evidence index still said "each case carries its own measured_at" after the docstring and the verdict doc were fixed. The repair searched the cited location, not the claim. Grepping the same keywords found three more twins, one of them a pointer to a gap letter the document deliberately never assigns.
Fix: Before editing a BLOCKed sentence, grep its keywords and numbers across the whole docs tree (index files and headings included); handle or explain every hit, then edit the cited line. Recorded as an author pre-step in ltm docs/gate-operations-2026-09-09.md (round 11).
Detection: A verifier quotes a sentence the previous round's change log says was fixed.
Record: ops/lessons/L-105.md

## L-106 2026-09-16 tags: scope-gating|process-ledger|handoff hits: 1 state: live
what: 離線 run 的 scope 不含 references/，收尾義務要的 digest 與 PROJECTS 列寫不進去 (unattended-run scope excludes references/, so the digest obligation cannot be met)
Context: [unattended-run] kickoff sets scope to the project root plus carriers cache/handoff, reports, telemetry. The global close-out rule and the manifest's acceptance item 4 ask for a session-digest entry in references/<project>-session-digest.md; the registry row is references/PROJECTS.md.
Pitfall: Both writes are denied by the scope guard (2026-09-16: PROJECTS.md, a telemetry row). The same deny hit the digest in the two 2026-09-11 ltm runs, so this is the third run in a row where a model-derived acceptance item is structurally unreachable and the entry is back-filled only after the user returns.
Fix: Not folded. Candidates for the process-ledger owner: add references/<project>-session-digest.md (append-only) to the carrier set, or have kickoff derive item 4 as "digest entry drafted in the run report". Until then the run pastes the entry into its report and names the blocker.
Detection: run_audit F3 or a deny row on references/*-session-digest.md inside an unattended run.
Record: ops/lessons/L-106.md

## L-107 2026-09-16 tags: subagent-dispatch|verification|tool-routing hits: 1 state: live
what: 驗證者的代理人型別決定它有沒有 shell，模型上限決定它的層級，兩者都要在派工前定 (a verifier's agent type fixes its tools and the model cap fixes its tier)
Context: ltm round 11 (2026-09-16) dispatched two independent verifiers during an unattended run: structure (software-architect) and numbers (testing-qa-engineer).
Pitfall: The opus dispatch was denied by model_cap_guard (subagent ceiling sonnet/haiku without user approval), costing a round trip. The software-architect type has only Read/Glob/Grep/Write, so the structural verifier could not run git diff or the project's pre-flight checker and reported both as undeterminable. Neither limit shows in the brief; both come from the dispatch choice.
Fix: In unattended runs plan verifiers as sonnet up front; pick an agent type whose tools cover every command the brief asks for, or have the author run the checker and put its output (not a verdict) into the brief. Recorded in ltm docs/gate-operations-2026-09-09.md, round 11.
Detection: A verifier report lists "no shell available" among its undeterminable items.
Record: ops/lessons/L-107.md

## L-108 2026-09-16 tags: experiment-design|evidence|measurement|recovery hits: 1 state: live
what: 會被中斷的實驗要邊跑邊落盤 (an experiment that writes its outputs only at the end loses every completed arm when it is killed)
Context: 四臂 GPU 實驗：前三臂 28 分鐘跑完並印出結果，第四臂（float32）兩小時又二十分鐘沒有完成**一次**解碼，顯示記憶體 7,679／8,151 MiB、使用率 100%。腳本在 `main()` 結尾才寫 `.json` 與 `.txt`。
Pitfall: 殺掉停住的第四臂，等於把已經跑完的前三臂一起丟掉——只剩 console 文字，而那還得靠當初有寫 `flush=True` 才在。**一個 GPU 實驗一定可能被中斷**（記憶體不夠、跑太久、機器要還給人），把唯一一次落盤放在最後，是拿最脆弱的那一刻去換全部的結果。第二個坑在同一個地方：那一臂沒有時間預算，所以「太貴」這件事只能靠人盯著才看得出來。
Fix: 每一臂跑完就寫一次完整輸出（帶 `complete: false`），最後一次才 `complete: true`。跑得起跑不起未知的那一臂，先跑**一次**量時間、對一個寫死的 wall-clock 預算判，超了就記「在這台機器上太貴」加上那個秒數並停——一個帶數字的結果，比一個沒有人設界限的等待有用。另外：縮短那一臂的輸入時，它的對照也要跟著縮，否則「沒有變異」分不出是修好了還是樣本太短。
Detection: 一支實驗腳本裡 `write_text`／`json.dump` 只出現在函式尾端，而它單次執行是分鐘級以上。
Record: ops/lessons/L-108.md

## L-109 2026-09-16 tags: docs|handoff|pointer-staleness|verify|records hits: 1 state: live
what: 掛在別的文件下一版上的待辦沒有主人 (a todo deferred to another document's next version is owned by nobody and surfaces only at the gate)
Context: 施工卡把一個型別的欄位歸屬寫成「這是對 PIM §2.1 的讀法，不是定案——logged for PIM v1.4 to reconcile」。卡片的讀法是對的；v1.4 寫完、發布、進閘，**沒有任何人去和解那一項**。
Pitfall: 延後項只寫在**來源**文件的註腳裡，目標文件的作者永遠不會讀到它——他手上是自己那份的變更清單。於是那一項不是被忘記，是**從一開始就沒有進過任何人的清單**。它最後由第十二輪的驗證者判成 BLOCK（文件宣告七欄、已出貨型別五欄）。閘抓到了，但那是最貴的一條路：一輪頂級模型的獨立驗證，換一句本來可以自己寫進待辦清單的話。
Fix: 延後項寫進**目標文件自己的開放項目**（該文件的 §13／open-items／變更紀錄待辦），來源文件只留指標；並且給它一個**事件型** review-when（「下一次那份文件改版號時」），不是一個版本號——版本號會過期而事件不會。判準：寫完之後問一句「**目標文件的作者下次打開他自己的清單時看得到這一項嗎**」，答案是「不會」就等於沒寫。
Detection: grep「logged for」「待 vN」「下一版再」這類措辭，逐一去目標文件裡找對應的項目；找不到的就是無主的。
Record: ops/lessons/L-109.md

## L-110 2026-09-20 tags: retrieval|prior|gate-design|hooks|records|recurring-symptom hits: 1 state: live
what: 能力都在、觸發邊只寫成條文，檢索就等於不存在 (a retrieval capability whose only trigger is a prose rule is, measured, not there)
Context: 使用者問「之前做出來的沒蒐集到文獻全文正本的 html 在哪」，Haiku 主迴圈搜尋二十餘次後回報找不到；完整路徑就寫在該工作目錄的記憶明細檔裡，索引行也看得到關鍵字。17 條檢索路徑裡 6 條沒有任何入口、6 條只靠條文。
Pitfall: 把「該查哪裡」寫成條文，就以為邊接好了。640 份對話實測：真的跨對話指涉之後有任何檢索的約 22%，而且各模型一致——不是 Haiku 的問題，是條文當觸發器的問題。同時兩個儀器會把「查法錯了」回報成「真的沒有」：session 搜尋是整串字面比對、Git Bash 吃掉未加引號路徑的反斜線；連續多次相同的空結果被當成結論而不是儀器故障。第三層：索引卡因 `status` 寫了自由文字被靜默退件，作者以為有卡。
Fix: 觸發邊交給機器並且出生就帶遙測：`past_work_recall_inject`（提問含過往用語 → 自動查並注入）、`subagent_retrieval_brief`（SubagentStart 送進子代理）、`shell_transport_guard` 規則 4、`session_search_query_notice`；`xi.py emit` 逐張印出退件卡；黃金題組掛成 system-hmi 探針。判準：新增任何檢索能力時問一句「沒有人記得它的那一天，是誰去呼叫它」，答不出機器的名字就等於沒建。
Detection: 同一個查詢目標連續 ≥3 次空結果 → 先懷疑儀器（換單一詞、加引號、換工具），不要下「沒有」的結論。`python tools/recall/trigger_followthrough.py` 的跟進率、`xi.py emit` 的 rejected 行、system-hmi 的 `cross-index.recall-golden`。
Record: ops/lessons/L-110.md

## L-111 2026-09-21 tags: silent-failure|validity-model|verify hits: 1 state: live
what: CAD 核心的布林／Compound／剖面操作可能靜默不做承諾的事或改變物件身分，回傳值看起來正常 (a CAD-kernel boolean, Compound, or section operation can silently skip its job or mutate object identity while the return value looks normal)
Context: T09 (build123d/OCCT, 7 CAD variants) and T15 (purified-component CAD + patent/engineering drawings) both hit CAD-kernel operations that completed without exception but did not do what the call implied.
Pitfall: Three instances, one mechanism: (1) OCCT's tangent boolean silently skipped — a 65449.8 um^3 sphere stayed fused with its block, no error; (2) build123d's `Compound` reparents child solids under the newest parent object, so the first STEP export silently dropped members that were still "there" in the Python object graph; (3) a section-boolean cut of a part lying wholly inside the kept region returns the SAME object handle rather than a new one, so the downstream code renamed the original part, corrupting a later view (T15 B-B section ran off the drawing frame). None threw; each needed a readback of the emitted result, not the API return, to be caught.
Fix: Verify a CAD-kernel op against the EMITTED geometry, never the call's return code or handle: after a boolean, diff volume/entity count against the pre-op value; build STEP exports from fresh copies rather than trust a Compound's live parent pointer, and count readback entities against the expected part list; after any section/cut, check the resulting object's identity and offset (not just absence of an exception) before reusing it downstream.
Detection: A boolean/Compound/section call returns normally, yet a downstream volume, entity count, part list, or rendered view disagrees with what was asked for.
Record: ops/lessons/L-111.md

## L-112 2026-09-21 tags: records|review-methodology|audit-record hits: 1 state: live
what: 整輪被判「部件、畫法、距離都錯」，紀錄只留使用者的判定，沒有記下錯在哪一步發生 (a whole round was rejected end-to-end and the record kept only the verdict, not which step first introduced each error)
Context: T10 (Z-fold loss-item list and premise table, built from the user's redrawn advisor sketch) was rejected wholesale at T11's open: "T10 那邊只有幾何的復現相對正確，但選用的每個部件跟畫法還有距離等都是錯的……連可能數據都不能直接用……開新輪。"
Pitfall: The only thing either round's record captured was the user's summary verdict ("parts, drawing convention, and distances are all wrong") — not WHERE in T10's pipeline (source-drawing reading, part selection, or distance derivation) each error first entered. T11 had no way to fix T10 selectively, so it discarded T10's outputs entirely ("一律不引用") and rebuilt every number from a fresh geometry script. A round-level rejection with no per-step fault trace cannot tell a later round whether the SAME step is about to fail again — it can only re-verify everything from zero, every time.
Fix: When a deliverable is rejected end-to-end, before or during the next round's open, capture which step first diverged (source-drawing reading vs. part selection vs. distance/geometry derivation), even if the round is going to be fully rebuilt anyway — record it as a locator in the round JSON deviation, not only the summary verdict, so a repeat of the SAME failing step across future rounds becomes greppable instead of invisible.
Detection: A round record whose only entry for a rejected prior deliverable is the rejecting party's one-sentence verdict, with the next round's record stating it will not cite ANY of the rejected round's outputs.
Record: ops/lessons/L-112.md

## L-113 2026-09-21 tags: design|validity-model|scope-gating hits: 1 state: live
what: 討論圖上的長度被當成規格、折返區被當成走線，照著建了一台四段可調參數的模擬機器，整輪最終廢案 (lengths shown in a discussion sketch were read as a fixed spec and a fold region as mere routing, so a whole round built a four-segment parametric simulation rig before the framing was corrected, and the round was abandoned)
Context: T11-T12 read the advisor's hand-sketch dimensions and the fold region's drawn shape as literal targets, and built T12 as a tunable, four-segment parametric COMSOL rig to hit them. T13 opened with the user's correction that the design point is component selection and function, not the drawn lengths.
Pitfall: Nobody asked, before building, what each drawn element's FUNCTION was (a fold region that expands the beam like a taper, vs. a length that is only a later tunable parameter). Skipping that question let two readings slip in unchallenged: a schematic length became "the spec to hit", and a beam-expanding element became "just a waveguide run". T12 built and calibrated an entire four-segment tunable apparatus against the wrong target; only after echo 24% / reference-case 87% exceeded the physical ceiling and OE parameters turned out self-contradictory did the round get abandoned wholesale ("T12當廢案停止"; the folded region even had a core layer, contradicting T13's core-less design).
Fix: Before building any parametrized model from a hand or advisor sketch, state each drawn element's FUNCTION in one sentence (not its shape or its drawn dimension) and get explicit confirmation of which drawn numbers are fixed requirements versus later-tunable choices; only start the quantitative build once both are confirmed. This generalizes the project's existing geometry-authority clause (lens words name function, not shape) to non-optical elements and to dimensions, not just shapes.
Detection: A model that treats every number in a sketch as a target to match, before the sketch's elements have each been asked what they are FOR; an apparatus growing in complexity (segments, tunable parameters) before the modeled object has been named in one function sentence.
Record: ops/lessons/L-113.md

## L-114 2026-09-21 tags: thresholds|calibration|numeric-constants hits: 1 state: live
what: 有可比的閉合式時仍先發布三點線性內插值當作 1 dB 容差點，事後才用二次律閉合式更正 (a three-point linear-interpolation estimate was published as the 1 dB tolerance point even though a comparable closed form was available, and had to be corrected afterward)
Context: T14's tolerance table needed the mirror-sidewall-verticality 1 dB point. The first version derived it from a 3-point linear interpolation across scalar-3D sample angles: about 0.12deg/face. A closed-form quadratic law (with a (d/L)^2 off-axis-source correction) was available for the same quantity and matched the scalar-3D points to within 3-4%.
Pitfall: The interpolation estimate was published into the round record and downstream documents (`out/tolerance_windows.json`, the proposal) as if it were the final number, before the already-derivable closed form was checked against it. The closed form gives 0.17deg/face, matching the scalar-3D samples at ratio 1.03-1.04 -- materially different (42% higher) from the 0.12deg interpolation. The interpolation was not flagged as provisional; it read as a result, not as a placeholder pending the closed form.
Fix: Whenever a closed form or analytic law for the same quantity is available, or can be cheaply derived from an already-validated model, compute and compare it BEFORE publishing an interpolated or few-point-fit estimate. Publish the closed-form value; keep the interpolation as a superseded check in the record, not as the headline number. A material disagreement between the two (as here) is itself the finding to report, not a rounding footnote.
Detection: A tolerance / crossing / 1-dB-point value derived from interpolation or a low-order fit across few sample points, in a round that already has (or could derive within the same session) a closed-form expression for the same quantity, published without a side-by-side comparison.
Record: ops/lessons/L-114.md

## L-115 2026-09-21 tags: simulation|instrument-model|validity-model hits: 1 state: live
what: 軸對稱 m=1 圓偏振全波在二次元素下，面內（curl 元素）與面外（Lagrange 元素）分量數值色散不同，沿程失相變成離軸環 (a COMSOL axisymmetric m=1 circularly-polarized full-wave run under quadratic elements shows different numerical dispersion between in-plane curl-element and out-of-plane Lagrange-element field components, dephasing the polarization along the path into off-axis rings)
Context: T14 needed a third-party-solver ("公信力") field map for the no-core Z-fold, rotationally symmetric about the propagation axis. COMSOL 2D-axisymmetric ewfd, m=1, was chosen to represent circular polarization ((Er,Ephi)=(G,-iG)) as the axisymmetric equivalent of a linearly-polarized Gaussian beam, at quadratic element order, lambda/4 mesh (carried over from the fold2d v2 recipe).
Pitfall: The full-length solve over-expanded the beam (facet w 32 vs. expected 25) and produced off-axis rings; gates G1 overlap 0.66 and G2 eta 0.50 both FAILed. Root cause, found by single-variable isolation on a 200 um short domain: quadratic elements represent the in-plane field components through curl (Nedelec-type) shape functions and the out-of-plane component through Lagrange shape functions, and the two have DIFFERENT numerical dispersion at the same mesh density -- so a circularly-polarized field dephases as it propagates, and the accumulated phase error shows up as a spurious reverse-helicity ring. A 40 um short probe of the same setup PASSed (see the paired probe-length card).
Fix: Switch to cubic elements at lambda/3 mesh. Verified by monotonic single-variable convergence on the 200 um short domain: quadratic lambda/4 overlap-to-reference ratio 0.933 -> lambda/6 0.995 -> lambda/8 0.999; cubic lambda/4 already 1.0000. Separately, the azimuthal helicity sign (Ephi = +-i*Er) is a genuine ambiguity in COMSOL's convention and was checked by running BOTH signs: the wrong sign produces an on-axis field singularity (regularity metric 1.7, overlap 0.04) and is immediately distinguishable.
Detection: A circularly-polarized axisymmetric full-wave run at quadratic or lower element order shows off-axis rings or a mismatched overlap gate only at longer lengths, while a short probe of the same setup passes; an on-axis singularity after launch signals the wrong helicity sign, not a mesh problem.
Record: ops/lessons/L-115.md

## L-116 2026-09-21 tags: gate-design|verify|false-negative hits: 1 state: live
what: 40 µm 短探針通過不代表全長通過；被測誤差要有足夠長度才累積得出來，正對照要放在全長模型裡 (a short probe passing does not certify the full-length model; the tested error needs enough propagation length to accumulate, so the positive control belongs in the full-length model, not only in the probe)
Context: Before the T14 axisymmetric full-length run, a short 40 um probe of the same recipe (same mesh order, same launch) was used as a fast sanity check and PASSed. The full-length (0.9 mm+) run then FAILed its positive-control gate (overlap 0.66 vs. expected ~1, efficiency 0.50).
Pitfall: The error the gate was meant to catch (numerical-dispersion dephasing between curl and Lagrange field components under quadratic elements, see the paired dispersion card) is CUMULATIVE with propagation distance. A probe short enough to run fast is, for exactly that reason, also short enough that the cumulative error has not grown past the gate's tolerance yet -- so a passing short probe is not evidence the full-length model is right; it may only mean the error had no room to show up.
Fix: When a probe or gate is meant to catch a cumulative numerical error (dispersion, drift, phase error, anything that grows with distance/time/iteration), size the probe -- or add a second, full-length positive control -- so the error has room to exceed the gate's tolerance before the gate is trusted. A short-range probe that only checks setup correctness (does the model build and solve) is not a substitute for a full-length positive control; state explicitly which of the two a given probe is standing in for.
Detection: A probe/gate shortened "to save time" with no companion full-length control; a gate that FAILs only after the domain is scaled up from a previously-passing short test; a mechanism in play (dispersion, leakage, drift) whose signature is known to be cumulative rather than local.
Record: ops/lessons/L-116.md

## L-117 2026-09-21 tags: design|html|ux|scope-gating hits: 1 state: folded→rules/deliverable-doc-refs.md
what: 把「說明文件好讀」的克制原則套到節點型啟動器頁，拿掉方框與顏色，結果層級被壓平、被否決 (prose-document restraint rules were applied to a node-view launcher page, removing boxes and colour, which flattened its hierarchy and was rejected)
Context: A Markdown->HTML->PDF lesson plan read well because of restraint (4 type sizes, almost no boxes, colour = link only). The four principles abstracted from it were applied in the same session to VIEWS.html, a launcher that the user called "too full", as a B copy: boxes removed, whitespace grouping, accent reserved for location.
Pitfall: The principles were abstracted from a PROSE document and applied without checking what the target page HOLDS. VIEWS.html shows subsystem NODES: each card is an entity, the box is its boundary, colour marks its class and group. Removing them made every item equal ("B 版反而把一切平級化"). The real clutter was elsewhere: an unsegmented flat project list in the side panel and a regenerate command shown at first glance. Measuring "boxes per page" treated a node container as decoration, so the instrument pointed at the wrong fix.
Fix: Classify content before transferring a style principle: prose (read top to bottom, document-*) vs node (scan and compare entities, dashboard/tool). Prose gets the restraint layer; nodes keep containers + colour and borrow only "few type tiers" and "one meaning per colour". Folded as an asset property in rules/deliverable-doc-refs.md (styling follows the CONTENT class); the prose layer is AssetVault prose-doc-layer. For node-view clutter, look at grouping and progressive disclosure first (side-panel survey: Linear, Primer, Atlassian, Fluent, Carbon, Apple HIG, M3).
Detection: A readability or declutter change that removes containers or colour from a page whose items are entities (cards per project/tool/subsystem), justified by a reference that is a document.
Record: ops/lessons/L-117.md

## L-118 2026-09-22 tags: verify|silent-failure|hooks hits: 1 state: live
what: 對話中顯示給使用者的文字不一定寫進 transcript .jsonl，靠掃 transcript 找「說過的話」的偵測器會把守規的 session 判成違規 (visible assistant text is not reliably persisted in the session transcript; a detector reading chat text calls a compliant session non-compliant)
Context: Building a hook that decides whether a session already wrote its boundary contract. The backtest scanned transcripts for the contract heading in assistant text blocks and reported only ~15% compliance across 10 days.
Pitfall: The session running the backtest had written its own contract in chat, yet the scan found nothing. Counting block types showed 10 text blocks against about 17 visible replies; the contract reply was one of the missing. Visible text that shares a turn with thinking and tool calls does not always reach the .jsonl. So "absent from the transcript" does not mean "never said", and any rate built on chat text is an upper bound on non-compliance, not a measurement.
Fix: A gate that must see something the model SAID reads a carrier written by a TOOL CALL (process-ledger row, file content), never chat text from the transcript. Applied in hooks/boundary_contract_notice.py (ledger row `boundary-contract`); ops/05-authority.md §4 states the carrier.
Detection: A transcript-based rate that looks implausibly low, or a session you know said X where the transcript scan finds no X. Count text blocks against visible replies before trusting it.
Record: ops/lessons/L-118.md

## L-119 2026-09-22 tags: records|stale-claim|advisory hits: 1 state: live
what: 建議文件的狀態行在被消化時沒人改，下一個 session 照著過期的「待裁決」行事，重做已完成的工作 (an advisory's status line is not updated when the advisory is consumed; the next session acts on the stale "awaiting ruling" and redoes finished work)
Context: Consuming the OPEN advisory outputs that ops-health had listed every session since 2026-08-17. The screen matches status-line vocabulary only (OPEN / await / 待裁).
Pitfall: Two advisories were already consumed. Seven trigger-probe calibration reports said "await USER RULING OQ-1", but PSM §13 had ruled OQ-1 on 2026-08-17. The DIT/Prism field analysis said "測驗計畫建議待裁決", but F1/F2 had run and been accepted on 2026-08-28 (98d05b8, 58ee1ea), and SPENT siblings in the same folder cited them. Reading only the status line, the session stamped the plan "ruled" and spawned a task to run rounds that were finished; that session found the history and corrected the stamp. The alarm had stood for about five weeks because the line never changed when its work landed.
Fix: A ruling or an execution that consumes an advisory updates its status line in the same commit (rules-usage-dict §7). ops-health check 13 also cross-checks each waiting stamp: an awaited ruling id found ruled in a register, or a later SPENT sibling in the same folder, prints "likely consumed, check before acting". tools/status-line/status_line.py rewrites one status line and keeps line endings and BOM.
Detection: An advisory that has stayed OPEN for weeks while its folder kept moving. Before acting on "awaiting X", grep the registers for X and look at git log for the advisory's folder after its date.
Record: ops/lessons/L-119.md

## L-120 2026-09-23 tags: git|worktree|windows|destructive|shared-tree hits: 1 state: folded→hooks/worktree_scope_guard.py
what: 把共用 checkout 的 .venv / node_modules 用 junction 接進 worktree，`git worktree remove --force` 會沿著 junction 把「目標」的內容刪光 (junctioning a shared checkout's dependency folders into a worktree makes that worktree's removal delete the SHARED copy's contents)
Context: A peer session held the shared checkout on its own branch, so this session moved its work into a linked worktree. The worktree had no `.venv` and no `node_modules`, and a release build needs both, so all three were junctioned (`New-Item -ItemType Junction`) from the shared checkout. The build, the GUI suite and the installers all worked.
Pitfall: Cleanup ran `git worktree remove --force`, which deletes the worktree directory recursively. On Windows a recursive delete over a DIRECTORY JUNCTION deletes the target's contents, not just the link — so the shared checkout's `.venv`, `gui\node_modules` and `electron\node_modules` came back as empty folders. The `Remove-Item` that was supposed to drop the junctions first failed in the same command (`NonInteractive mode`, no `-Recurse`), and its failure was not checked, so the destructive step ran with the links still in place. Nothing tracked was lost and `git status` stayed clean, which is exactly why it is quiet: the damage is entirely in ignored paths that no git command reports.
Fix: Do not junction a shared checkout's dependency folders into a worktree. Either build in the tree that owns them, or give the worktree its own (`py -m venv`, `npm ci`). If a junction is unavoidable, remove it with `cmd /c rmdir "<link>"` (never `Remove-Item -Recurse`, never a tool that deletes recursively) and VERIFY the target still has entries BEFORE running `git worktree remove`. A command whose purpose is to make the next step safe is checked for success, not assumed.
Detection: After removing a worktree on Windows: `Get-ChildItem <shared>\.venv | Measure-Object` and the same for each `node_modules`. Zero entries with the folder still present is this. Also: any `New-Item -ItemType Junction` inside a path that something will later delete recursively.
Record: ops/lessons/L-120.md

## L-121 2026-09-23 tags: verify|hooks|registry|gate-design|recurring-symptom hits: 3 state: folded→hooks/registry_row_guard.py
what: 一個檢查若只有監控會跑，「看到監控紅燈再回來修」就成了必要流程；被 hook 活讀的資料檔改動時沒有任何檢查 (a check only the monitor runs turns "see the red lamp, come back and fix" into a required step; editing a data file a hook reads live ran no check)
Context: PROJECTS.md gained project rows in three sessions (09-21; 09-23 04:24, 14 rows; 09-23 15:25-15:49). user_profile_gist's live check L-1 needs each one classified in the USER-PROFILE.md activity map.
Pitfall: Each registration left L-1 red, and only system-hmi found it. The fixes (efad74e, ace27b3) added the row and stopped, so the third time looked like the first. golive_check ran suites on save but only for CODE files named in the command. A Markdown register a hook reads live was invisible, and the 09-22 audit had routed this item (K4) to the SessionStart reminder, which is the monitor again.
Fix: A hook whose suite checks live data lists those files on a `Live-reads:` docstring line. golive_check maps an edit of any declared file (any suffix) to that suite and prints a notice at the edit. Declared: user_profile_gist, project_registry_gist. L-1's failure line names the unclassified projects. A hermetic suite declares nothing.
Detection: The same HMI row red again after a data-only fix: ask which event should have run the check. Named gaps: registers written by a script, and the hand-regenerated graph MOC (D-24).
Record: ops/lessons/L-121.md

## L-122 2026-09-24 tags: instrument-check|false-green|browser-pane|measurement hits: 1 state: live
what: document.fonts.check() 對沒有 @font-face 的字族一律回 true，拿它判斷「字型有沒有裝」會把缺字型報成可用 (document.fonts.check() returns true for any family with no @font-face rule, so it reports an uninstalled system font as available)
Context: DT-04 gates for 21 generated pages: offline load, and "did the page's declared body font actually render, or silently fall back to a system font".
Pitfall: The first probe used `document.fonts.check('16px "Fam"')`. Per the CSS Font Loading spec, check() answers "would loading be needed", not "is it installed": a family with no matching @font-face in the FontFaceSet needs no loading, so check() returns true. It reported "Iowan Old Style" (a macOS face) and "Source Han Serif TC" as available on this Windows machine — a silent fallback read as a pass, exactly the defect class the gate existed to catch.
Fix: Width comparison, the standard installed-font test: render a mixed Latin/CJK string in `"Fam", <generic>` and in `<generic>` alone for monospace/serif/sans-serif; any width difference means the face is present. Controls run on every page: Arial must read present, a nonsense family must read absent, else the probe throws.
Detection: A font "available" verdict for a family you know is platform-specific (Iowan, SF Pro, Helvetica Neue on Windows), or 100% availability across pages from varied generators.
Record: ops/lessons/L-122.md

## L-123 2026-09-24 tags: skills|routing|confound|experiment-design hits: 1 state: live
what: 在這台機器做 skill A/B 時，全域 skill 會搶走受測 skill 的觸發；「裝了」不等於「用了」，每格要從 transcript 讀實際觸發的是誰 (in a skill A/B on this machine, global skills steal the trigger from the skill under test; installed is not used — read the invoked skill from each run's transcript)
Context: design-style-testbed round 1: 7 page types x 3 arms (baseline, frontend-design, ui-ux-pro-max), headless `claude -p` with sonnet, cwd = arm folder so only that arm's project-scope skill loads. The prompt was identical for all arms and said "If a design skill is available to you, use it."
Pitfall: Global skills load in every arm. On the diagram type (T4) diagram-authoring was invoked in all three arms, displacing both skills under test; on the one-page paper type (T7) paper-story won in baseline and frontend-design; frontend-design on the deck (T2) invoked nothing. 4 of 14 skill-arm cells did not use their skill. Counting them as that arm's output would have attributed the global skill's look to the external skill.
Fix: The runner records `skills_invoked` from stream-json tool_use events per cell and flags `arm_skill_invoked=false`. Untriggered cells stay in the table marked as such, and are re-run once with the skill named in the prompt (tag `named`), reported separately. Any future skill A/B here reads invocation from the transcript, never from installation.
Detection: A skill-arm cell whose output resembles the baseline, or a type that has a strongly-matching global skill (diagram, paper one-pager, deck).
Record: ops/lessons/L-123.md

## L-124 2026-09-24 tags: skills|interop|silent-failure hits: 1 state: folded→skills/skill-share-packaging/SKILL.md
what: 以 plugin 形式發佈的第三方 skill 若用 ${CLAUDE_PLUGIN_ROOT} 找自己的腳本，改裝成專案範圍 skill 時該變數是空的，腳本路徑會壞掉 (a third-party skill written for plugin install locates its scripts via ${CLAUDE_PLUGIN_ROOT}; installed project-scope the variable is unset and the path breaks)
Context: Mode B import audit of ui-ux-pro-max (nextlevelbuilder, commit dcc40ff) before installing it under arms/ui-ux-pro-max/.claude/skills/ for an isolated test, never globally.
Pitfall: Every command in its SKILL.md is `python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py"`. Outside a plugin install the variable expands to empty, giving `/.claude/skills/...` — a path at the filesystem root. The skill still loads and still "triggers", so a trigger check passes while its whole data half is unreachable unless the model improvises a path.
Fix: Do not edit the vendored skill; set `CLAUDE_PLUGIN_ROOT=<install folder>` in the environment of the runs that use it (tools/run_cells.py). The Mode B import audit adds one grep: `CLAUDE_PLUGIN_ROOT|CLAUDE_PROJECT_DIR|\$\{` in SKILL.md — each hit is an install-shape assumption to satisfy or record. Rule home: skill-share-packaging Mode B "Reverse A2/A3" step.
Detection: A skill whose trigger is recorded but whose script calls fail or never appear in the transcript.
Record: ops/lessons/L-124.md

## L-125 2026-09-24 tags: instrument-vocabulary|gate-design|html hits: 1 state: live
what: fill_gate 的 deck 類假設所有 .slide 都有排版；一次只顯示一張的簡報其餘投影片是隱藏的，閘門量不到而降為 WARN，這是儀器詞彙缺口，不是頁面缺陷 (fill_gate's deck class assumes every .slide is laid out; a one-at-a-time deck hides the rest, so the gate measures nothing and downgrades to WARN — a vocabulary gap, not a page defect)
Context: All three generated decks (T2) in design-style-testbed round 1 are keyboard-paged: one `.slide.active` visible, the other 23 `display:none`.
Pitfall: fill_gate measures the first 8 `.slide` elements; hidden ones yield "no painted/text block found", reach=0% fill=0%, and the verdict is WARN on all three. It is the correct downgrade (the gate cannot determine), but read naively it looks like three failing decks, and it gives no measurement at all for the deck class the user's own deck-shell does not use.
Fix: Report these as "gate cannot measure" in the testbed tables, not as defects. A real fix belongs in page-fill-gate: for deck, force each slide visible in turn (add the active class or set display) before measuring, with a paged-deck positive and negative fixture pair per its README's new-class rule. Not done in this round (global tool, out of scope); named here so it is not re-diagnosed.
Detection: deck rows with reach=0% fill=0% and "no painted/text block" on slides 2+.
Record: ops/lessons/L-125.md

## L-126 2026-09-24 tags: confound|experiment-design|skills|isolation hits: 1 state: live
what: 在這台機器用 headless 子 session 做風格 A/B，使用者層 hook 會把偏好（淺色、書報襯線）注入每一格，把各組拉成同一種外觀，skill 的推薦被蓋掉；要比 skill 必須用 --setting-sources project,local 隔離，arms 放在 repo 外 (a style A/B run as headless sessions here inherits user-scope hooks that inject the user's look preference into every cell and override the skills; isolate with --setting-sources project,local and keep arm folders outside the repo)
Context: design-style-testbed round 1: 34 sonnet cells, 3 arms (baseline / frontend-design / ui-ux-pro-max), headless `claude -p`, cwd = arm folder. The user judged that the two skills visibly added nothing and asked why.
Pitfall: "Only this arm's skill loads" was treated as the whole isolation. Every cell also ran 7 SessionStart hooks (~8.6k chars incl. the user-profile line "light themes and an editorial serif look over dark AI SaaS"), ~/.claude/CLAUDE.md and ~60 global skills. 20/21 pages came out light, 18/21 serif; ui-ux-pro-max used 0/10 and 2/10 of its own recommended colours on T5/T6. The arm variable was swamped by a constant injected into all arms. Second leak: arms inside the repo also read the repo-root CLAUDE.md as ancestor memory.
Fix: Style/skill experiments run with `--setting-sources project,local` (0 hooks, no user skills, no user CLAUDE.md; verified from the init event) and arm folders outside any repo holding a CLAUDE.md. Implemented as `--isolated --arms-root` in tools/run_cells.py. Isolated re-run: recommended-colour use 7/10 and 9/10; arms split (frontend-design went dark, all sans); fill_gate 6/6 PASS vs 1/6.
Detection: Arms converging on the user's known preference; a skill's own logged recommendation absent from its output; count hook_response events and init.skills in the run transcript before trusting an arm comparison.
Record: ops/lessons/L-126.md

## L-127 2026-09-24 tags: batch-operation|experiment|batch-runner|rate-limit|headless|resumability hits: 1 state: live
what: 批次跑 headless claude -p 時，額度用完 (HTTP 429) 每格仍 exit 並在 2 秒內「完成」，佇列不停就把剩下的格子全燒成空失敗；批次驅動器必須讀 result 事件的 api_error_status，429 即全佇列停止，且重跑時跳過已產出的格子 (a headless claude -p batch keeps draining its queue after the quota runs out: each cell fails in 2 s with HTTP 429; the driver must read api_error_status from the result event, stop all queues on 429, and resume by skipping cells already produced)
Context: design-style-testbed round 2: 36 sonnet cells in two queues (tools/run_round2.py). The runner treated any exception as "record and continue".
Pitfall: At 12:12 the sonnet weekly limit was hit. `claude -p` does not raise: it exits 1 with a normal-looking result event (`subtype: success`, `is_error: true`, `api_error_status: 429`, `terminal_reason: api_error`, cost 0). The queue kept going and 21 cells "completed" in ~2 s each, each writing a run.json with html_written=false that the compare page then showed as a failure.
Fix: run_cells.py records `api_error_status` and the error text; run_round2.py sets a shared stop event on 429 (both queues stop) and skips any cell whose out HTML already exists, so a plain rerun resumes. The 21 empty records moved to archive/round2-ratelimit/.
Detection: A run of cells with seconds < 5 and cost 0; grep the transcript for `"error":"rate_limit"` / `api_error_status`.
Record: ops/lessons/L-127.md

## L-128 2026-09-26 tags: hooks|hook-design|false-negative|false-positive|worktree|git hits: 1 state: live
what: worktree_scope_guard 的 shell 半邊用 session cwd 判斷工作樹，看不到指令內的 cd (the guard's shell half resolves the checkout from the session cwd, never from a cd inside the command -- the shape the Bash tool forces)
Context: 2026-09-26. Session cwd at the source's second-drive work root (not a repo); the Bash tool resets cwd on every call, so every command into worktree .claude/worktrees/inv2-attribution began `cd <the home tree, POSIX-spelled>/.claude/worktrees/... &&`. A hermetic probe (temp repo + linked worktree, guard retargeted with WSG_HOME) fed decide() that shape.
Pitfall: decide() runs checkout_info(payload cwd). With cwd outside the worktree, `cd <worktree>/tools/graph-snapshot && python gsnap.py build` is ALLOWED -- the stranded-out/ build L-060 exists to deny (W1a Windows path, W1b Git Bash /c/ path). The only cd it parses is cd-to-canonical, compared via normcase, so `cd /c/Users/.../.claude` from inside a worktree is not recognised: a false DENY (W1d). KNOWN BOUNDARIES lists neither.
Fix: Not applied -- user review (feedback pool, hook:worktree_scope_guard). Proposal: take the EFFECTIVE cwd = last cd/pushd/Set-Location segment before the builder match, resolved against payload cwd, /x/... -> X:/... normalised; run checkout_info on it; reuse the normaliser in cd_to_canonical. Controls: W1a/W1b flip to deny-shell, W1c/W1d allow, selftest 41/41 unchanged.
Detection: A worktree tools/*/out/ newer than the canonical one; a deny row in telemetry/worktree-scope-guard.jsonl whose command starts `cd /c/`.
Record: ops/lessons/L-128.md

## L-129 2026-09-26 tags: graph-snapshot|identity-by-path|false-negative|worktree hits: 1 state: live
what: 在 linked worktree 裡，由 __file__ 推 home 的工具會把 repo 自己的正典 checkout 當成外部專案根 (a tool that derives home from __file__ sees, inside a linked worktree, the repo's own canonical checkout as a FOREIGN project root)
Context: 2026-09-26. Running tools/graph-snapshot tests inside worktree .claude/worktrees/inv2-attribution: test_placeholder.py failed ONE case ("a file that exists HERE is not routed through this class") that passes in the canonical tree, on code the round never touched.
Pitfall: gs_edges.load_foreign_roots(PROJECTS.md, home) skips registry paths under home. In a worktree home = ~/.claude/.claude/worktrees/<n>; the claude-config row names ~/.claude itself -- not under home, reachable -- so it loads as a foreign root (probe W2b True; W2a canonical home False). The test false-fails in every worktree, and a graph built there files a dead link whose target exists in the canonical tree as foreign-root, not broken: rot hidden where the worktree diverges.
Fix: Not applied -- user review (feedback pool, tool:graph-snapshot). Proposal: load_foreign_roots also skips the canonical root of the repo home belongs to (read <home>/.git file -> gitdir -> commondir -> parent; no subprocess). Controls: test_placeholder passes in a worktree; a registry root outside the repo still loads. Related: L-060 (same __file__ root, stranded out/).
Detection: A test green in the canonical tree and red only in a worktree; FOREIGN_ROOTS containing an ancestor of home.
Record: ops/lessons/L-129.md

## L-130 2026-09-26 tags: git|concurrency|shared-worktree|worktree hits: 1 state: live
what: git stash 在所有 worktree 間共用同一個 refs/stash，worktree 裡 stash 的東西會被正典樹的 git stash pop 拿走 (refs/stash is one ref for every worktree: a stash pushed in a worktree is popped by a peer's git stash pop in the canonical tree)
Context: 2026-09-26. Inside worktree inv2-attribution this session ran `git stash -q -- moc_regen.py` then `git stash pop` to run a test against the pre-fix file, while peer sessions committed in the canonical tree every few minutes. Nothing was lost (status read after the pop).
Pitfall: HEAD and the index are per-worktree; refs/stash is not. Probe W3 (temp repo): a stash pushed in the linked worktree shows in the canonical tree's `git stash list`, and `git stash pop` there exits 0 and writes the worktree's edit into the CANONICAL working tree; the worktree's own later pop then takes another entry or fails. shared-tree-git.md §0 lists HEAD, index and working tree and says nothing of stash, so a worktree reads as a safe place to stash.
Fix: Not applied -- rule text is the user's call (feedback pool, rule:ops/references/shared-tree-git.md). Proposal: a §0 row "refs/stash -- shared by every worktree and the canonical tree"; practice: to test against a pre-fix file, `git show <rev>:<path> > <scratch>` (used later the same session for gsnap.py) instead of stash.
Detection: `git stash list` in the canonical tree showing `On <worktree-branch>:` entries; a pop that brings changes nobody in this tree made.
Record: ops/lessons/L-130.md

## L-131 2026-09-27 tags: harness|instruments hits: 1 state: live
what: Claude Code 升級改了 harness 預設與措辭，本機的觀測與觸發條件都沒看到 (a harness upgrade changed a default and renamed a block; no local instrument or review-when trigger could see either)
Context: 2026-09-27. Since 2.1.277, a directory with no project CLAUDE.md loads AGENTS.md, so `~/.claude/AGENTS.md` (the 23 KB Codex rewrite) was injected into every `~/.claude` session and subagent. The harness browser block `<browser_surfaces>` was also split into `<browsers>`/`<built_in_browser>`.
Pitfall: InstructionsLoaded does not fire for an AGENTS.md read through the Project-instructions setting (this is documented), so rule_loads.py kept reporting CLAUDE.md at 100% and never showed the extra file. It was found only by reading the session's own context. Separately, six registry review-when lines were keyed on the literal `<browser_surfaces>`. A trigger keyed on a harness string that no longer appears can never fire, yet it is still trusted.
Fix: User ruling: `claudeMdExcludes` in settings.json for that one file, not the global `instructionFiles: claude-md`, because five projects have only an AGENTS.md. Checked with fresh `claude -p` probes, plus a positive control in the obsidian_Nathan vault that still loads its own AGENTS.md. The six triggers were renamed to the new tags, with the old name kept in parentheses.
Detection: During a reconcile, list the "Contents of <path>" headers in your own context and diff them against the expected set. For any review-when keyed on a harness literal, grep the current system prompt for that literal first.
Record: ops/lessons/L-131.md

## L-132 2026-09-27 tags: contracts|false-negative|testing|refactor hits: 1 state: live
what: 以症狀命名的失敗檢查其實守著兩件事；把症狀改成合法時，另一件也被一起拆掉 (a failure check named after its symptom guarded two facts; legalising the symptom silently removed the guard on the second)
Context: ltm I-22: a decode with zero segments raised engine-failed: no-segments. The fix made an empty decode a legal round (silence answered correctly) and deleted the check as unreachable.
Pitfall: The check was named after what it saw (no words) but also caught a different fact: a child that ignored a cancel and exited 0 having sent nothing. After the edit that child became a successful empty decode. Only an old negative-control test (pytest.raises on the vanished child) went red; nothing in the check's name or docstring said it covered that case.
Fix: Before deleting or relaxing a check, enumerate every input that currently reaches it (tests that expect its raise are the list), and re-home each non-target case under a code naming what was OBSERVED missing -- here no-report: a finished decode always sends its report event. Tighten the surviving test to assert the new code, not just a raise.
Detection: A check removed as "unreachable" or "now legal" in the same commit that makes a pytest.raises elsewhere start failing.
Record: ops/lessons/L-132.md

## L-133 2026-09-27 tags: calibration|thresholds|gate-design|false-positive hits: 1 state: live
what: 門檻校準時把「真實語料上的命中」預設為誤報；逐條用獨立訊號量過後，全部是真缺陷 (threshold calibration presumed a detector's hits on unlabelled real data were false positives; measured against an independent signal, every one was a true defect)
Context: ltm I-23 sparse-cue (long cue, few words). Positives came from constructed clips; the plan was to pick the bar where the user's real store (16,601 cues) had ~0-1 hits, treating those hits as the known-false side.
Pitfall: Unlabelled real data is not a negative control. Per-second audio level over each of the 5 real hits showed 3 spanning 13-25 s of noise floor (the defect) and 2 with sound throughout and 1-8 words (dropped words); the band under the bar was about half defect too. Tuning to "<= 1 real hit" would have tuned true positives away and called it precision.
Fix: Known-false comes from input correct BY CONSTRUCTION (a clip with speech end to end: 0 flags). Hits on unlabelled data are READ against an independent signal before they count as either side, and the declined band under the bar is published with its size; the bar is then stated as a cost choice, not a boundary.
Detection: A threshold justified by "only N hits on real data" with no per-hit check recorded.
Record: ops/lessons/L-133.md

## L-134 2026-09-28 tags: evidence|dispatch|harness|false-negative hits: 1 state: folded→rules/source-quotation-evidence.md §The property
what: 逐字轉錄受版權保護的書頁會被 API 輸出過濾擋下（400），錯誤長得像傳輸故障，重試只會再被擋 (verbatim transcription of a copyrighted page is blocked by the API output filter with a 400 that reads like a transport fault; a retry is blocked again)
Context: 當代中文 verb-section deck, 2026-09-28: sources were four photographed teacher's-manual pages. The plan was a two-reader blind transcription (main loop + a subagent) diffed against each other, to catch misreadings.
Pitfall: Both readers died on `API Error: 400 Output blocked by content filtering policy` — the main loop twice, then the subagent (whole run lost). The user asked whether it was the network or sensitive data; it was neither: the output filter blocks long reproduction of a copyrighted text. The error text names no copyright, so retrying, chunking the page, or switching model looks like the fix and is the same act again.
Fix: Route change, not retry: evidence = locator + one quote <= 15 CJK-eq; presence proven by local Windows OCR + fuzzy match (tools/quote-evidence/qe.py, PASS >= 0.80); an independent verifier opens the images and returns match/mismatch and paraphrase findings only. Result in the incident: 86/86 quotes matched, gate 270 PASS, nothing blocked. Rule: rules/source-quotation-evidence.md; dispatch notice: hooks/verbatim_dispatch_notice.py.
Detection: A dispatch prompt or a main-loop plan containing verbatim/transcribe/逐字/抄錄 next to pages/book/scan/image paths; or the string `Output blocked by content filtering policy` in a task-notification.
Record: ops/lessons/L-134.md
