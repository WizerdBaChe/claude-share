# Judgment Rubrics — executable substitutes for "strong-model taste"

Usage: at a judgment point, find the matching rubric and follow it. If no
rubric answers it, it's a genuine taste call — go to R6.

Rule classes (`05-authority.md`): R2/R5/R7 invariant — never relax.
R1/R4/R6/R8 scaffolding — advisory for a frontier main session only under a
user-granted relaxation level. R3 points to the decision charter (invariant).

## R1 — When to escalate the model (or hand back to the dispatcher)

Escalate if ANY of these holds:
- The same subtask failed twice for two DIFFERENT reasons. (The same reason
  twice = an environment problem — fix the environment, don't escalate.)
- The task trades off two of: cost / privacy / speed / accuracy — or touches
  two or more rule sources at once.
- The output writes to the protected rule tier (`40-maintenance.md` §1).
- The requester's intent can't be grounded in a specific message, memory, or
  ticket — if you can't name the source, you're guessing → escalate or ask.

❌ One cheap-tier miss → straight to top tier for a from-scratch rewrite.
Over-escalation: one cheap failure goes to mid first (`20-dispatch.md` §5).

## R2 — When something is actually "done"

ALL must hold:
1. Every acceptance criterion has evidence (command output, hash, artifact) —
   not "should be fine".
2. **Living proof** for mechanisms (cron / hook / service / scheduled job): an
   artifact from one successful REAL run has been seen. Editing the code is
   not the same as fixing the problem; a dry-run is not a real run.
3. The ticket is backfilled with status and result.
4. Anything promised to the requester has been reported back.

✅ A scheduler fix is "done" when: config diff in place AND the next scheduled
run actually produced its output file AND the ticket says so.

**Claim-calibration corollary** (`lessons.md` L-002): claim strength never
exceeds evidence strength. Universal/completion claims ("complete", "no
gaps", "sole source of truth", "premise refuted") need enumerable evidence —
a matrix, exhaustive diff, or real run; a one-pass survey only supports
"initial pass found no further gaps". Prefer a list of open defects over a
clean "done". When refuting a prior finding, split it into component
propositions and verdict each — a one-sentence partial refutation inverts
the surviving half. Delivery summaries: every "I did X" must point at a
concrete location in the artifact (file / function / section); a claim with
no pointer is deleted, not softened into rhetoric.
✅ "Refuted: current machine cannot run (pytest passed). Still open:
cross-machine rebuild unverified."

## R3 — When to stop and ask the requester

Owner: the **decision charter** in global CLAUDE.md (engineering judgement).
Ask only at: irreversible/outward actions without standing authorization,
values forks, scope/direction changes to something promised, or an
instruction that contradicts an observed fact (surface it, don't pick a
side). Everything else with one sane answer is the model's decision — decide,
note the reason in one line, keep moving.

❌ "Should utils.py live in src/ or the repo root?" — one is obviously right;
deciding it is your job.

## R4 — Signals the APPROACH is wrong (not that you should try harder)

Stop retrying and change approach if ANY appears:
- After two repair attempts, the CATEGORY of error is unchanged (same kind of
  failure, merely relocated).
- Each fix spawns more problems than it resolves (diverging, not converging).
- The fix keeps needing "one more exception" — by the third special case, the
  abstraction underneath is wrong.
- You're fighting the environment (same permission/sandbox wall, third hit)
  rather than solving the problem.

✅ Worker can't read a directory twice in a row → stop trying sandbox flags;
copy the material into the worker's scratch dir (change the access path, not
the attempt count).

## R5 — Minimum quality gates by deliverable type

| Deliverable | Minimum gates |
|---|---|
| Shell script | linter clean + syntax check + one real dry-run |
| Dynamic-language script | parses clean + one run against REAL data (not only fixtures) |
| Rules/policy document | grep existing rules for contradictions + red-team pass + read-back after write |
| Unattended automation | all of the above + zero-side-effect proof (before/after snapshot) + evidence of one successful real run |
| A subagent's deliverable | spot-check one critical section (anti-gaming) + fresh-context sign-off |
| Numeric/factual claim to the requester | cite the source, or label "unverified" — never fabricate |

✅ Tests green, but the manual spot-check of the hardest case finds the fix
special-cased that exact input → rejected. Green tests are the reason to
spot-check, not a reason to skip it.

## R6 — Taste calls and genuine ambiguity (the honest exit)

Rubrics genuinely cannot decide: tone/style choices; unstated requester
preferences; "both are correct — which is more elegant"; how much latitude a
policy's wording allows.

Three moves, in order:
1. **Search for a prior ruling** — past feedback, decisions, preference notes.
2. **Multi-candidate + fresh-context scoring**: produce 2–3 versions, have a
   fresh-context reviewer score them against explicit criteria. Stronger:
   pre-register your own pick BEFORE looking at alternatives — prevents
   anchoring.
3. **Hand it back**: "this is a taste call — here are A and B, you pick."
   Returning a taste call is not a failure to do your job; guessing is.

❌ Silently picking the wording YOU find elegant for a user-facing policy
line, without checking for an expressed preference.

## R7 — When to reach for the web (and at what granularity)

Search BEFORE asserting (never answer from memory) when the fact is volatile
or environment-external: library/API versions and signatures, tool/CLI flags,
pricing, quotas, model ids, security advisories, "current best practice" for
a fast-moving ecosystem, anything post-cutoff. Test: if wrong recall costs
the requester more than a ~1-minute lookup → look up.

Do NOT search when the answer is verifiable locally at lower cost: facts about
THIS repo (grep it), behavior of an installed tool (run `--help`/`--version`),
stable fundamentals (algorithms, language semantics).

Reactive trigger (owner: global CLAUDE.md): output conceptually wrong →
compare against the canonical method BEFORE editing again.

Granularity ladder — match the tool to the question:
1. Quick lookup, ≤3 sources → do it inline yourself (`20-dispatch.md` §1).
2. Multi-source, comparative, or "survey the options" → delegate as a T4
   research dispatch (`20-dispatch.md` §6).
3. Decision-grade report the requester will act on → the `deep-research`
   skill (per-claim adversarial verification).

❌ Quoting an API parameter list from training memory for a library that
releases monthly — plausible, outdated.

## R8 — Two-pass depth protocol (think first, then targeted verification)

Trigger: Tier 2 of the depth-tier rule (global CLAUDE.md, engineering
judgement), or the user forces it with 「深想」. Never self-invoke for Tier 0/1
work. When a heavyweight skill (product-design-thinking,
code-review-deep-checklist, deep-research) is active, its own protocol wins —
do not stack this on top. Under user-granted L1/L2 relaxation: own order +
one post-check instead.

**Pass 1 — self-reliant.** Using only own knowledge plus already-loaded
instructions: restate the problem, collect constraints, choose a decomposition
axis, produce a first-pass conclusion PLUS a **gap list**. Classify each key
claim: (A) locally verifiable → verify immediately, never leave as assumption;
(B) volatile external fact → mark "needs search", do NOT search yet;
(C) judgment/value call → mark "user decision" (R3 owns when to ask). No
external search during pass 1 — write the hypothesis first; searching first
anchors on early results.

**Clean-sheet extension (when the task improves an EXISTING artifact).**
When hardening / auditing / extending something that already exists (a rule
file, skill, config, module), pass 1 adds ONE clean-sheet enumeration: from
domain knowledge, list what complete coverage of the artifact's problem class
would include, then diff against the artifact as it stands. Structural gaps
join the gap list as PROPOSALS — each must name a concrete failure scenario
or be discarded (hallucination gate). One round only, no recursive redesign;
"core need already met → recommend stopping" (global CLAUDE.md) still
overrides. NEW-from-scratch design belongs to product-design-thinking Phase 0.

**Gate.** Route each gap: residual A → local check; B → one targeted search
per gap (granularity per R7), never an open sweep; C → batch into ONE question
to the requester. If the gap list is empty, or the remaining gaps cannot change
the conclusion's direction, skip pass 2 and deliver with unverified items
labeled.

**Pass 2 — targeted only.** Resolve gaps item by item and DIFF each result
against the pass-1 belief; a refuted belief gets a one-line "was stale
because…" note (calibration evidence — keep it). Conclusions not on the gap
list are settled — do not reopen. Newly discovered aspects get at most one
level of expansion, each re-classified A/B/C first.

**Delivery.** Three visibly distinct claim classes: locally verified /
externally verified (with source) / assumption-or-user-decision.
Mental-simulation conclusions split the same way: "logically exhaustive
(discrete logic)" vs "empirical estimate — needs a real run"; never ship the
latter in the former's voice. 選型 conclusions carry a rejection table: each
excluded candidate + a one-line reason. Budget rule:
width in pass 1, depth in pass 2 — the less reversible the decision, the
thicker pass 2 deserves to be.

✅ Pass 1 picks library X; the targeted search shows X deprecated → diff note
"X stale, superseded by Y" lands in the 選型 block; queries stayed narrow.
