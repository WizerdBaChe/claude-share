---
name: skill-co-upgrade
description: >-
  Field-test co-upgrade loop for this environment's skills: run a REAL task
  through a skill, collect gaps under the standard "a gap exists iff the
  executor had to BYPASS the skill", then verify, adopt, and hand off via
  disposition files so the loop continues across sessions. Trigger on
  「跑一輪迴圈」「交互升級」「co-upgrade」「硬化這個 skill」
  「這個 skill 實測有缺口/繞過了才做對」「拿這份指南/規範對照升級這個 skill」.
  OFFER once — never run unprompted — when a skill visibly misfired or had to
  be bypassed during real work, when a substantially rewritten skill is about
  to take its first real run, or when an external standard arrives. NOT a
  static content audit of one artifact (→ config-self-audit; it runs INSIDE
  this loop as the upgrader's verification step), not skill authoring
  (→ skill-creator), not file cleanup (→ env-cleanup).
---

# Skill Co-Upgrade Loop

Turns skill maintenance from opinion into field evidence. Origin: 2026-08-16,
4 skills / 7 rounds, 43 gaps adopted, 1 discarded, 0 weakened; method ruling
D-032 in `references/claude-config-decisions.md`.

## The standard (load-bearing — do not soften)

**A gap exists iff the executor had to BYPASS the skill to do the right
thing.** "Followed it and it worked" and "ignored it and it went badly" are
both non-gaps. Every proposed gap names a concrete failure scenario or is
discarded (hallucination gate). Adjustments NARROW (guards, bounds, honest
rationale), never weaken — consent-gate wording keeps full strength.

## Roles and modes

- **Two-session default**: an executor session runs the skill on real work and
  writes the gap report; a separate upgrader session verifies every citation
  against the artifact before adopting. The split keeps verification honest —
  sessions cannot see each other's conversations, so the report and the
  disposition ARE the protocol.
- **Single-session variant** (user-directed): declare executor==upgrader in
  the report's credibility bounds; expect execution-level gaps only —
  structural blind spots still need a second body in a later round. Report
  and disposition may merge into one file when fixes land the same turn.
- **Standard-comparison round** (the carrier is an external standard, not a
  task — a library guide, a policy, a checklist the user hands over). The
  bypass standard cannot fire (nobody executed anything), so this shape has
  its own, equally strict one: **a gap exists iff the standard names a
  concrete failure scenario that the skill can neither DETECT nor PREVENT by
  a mechanism** — a prose warning the executor may skip is not a mechanism.
  Protocol: inventory the skill's existing measures per theme → a 裁定 table
  (item · locator in the standard · current state · 採納/採納-適配/不變/
  不採納 · reason) where the 不採納 rows are mandatory and reasoned → design
  → user rulings on the values forks (ask, recommended value first) → work
  cards → the upgrader leg below. Measured 2026-09-11 (literature-search-
  extract round 2, NTU library AI-literacy guide, 29 slides): 25 items → 15
  adopted / 3 adapted / 4 unchanged / 3 not adopted, six mechanisms built.

## Round protocol

0. **Locate the loop state.** Glob `~/.claude/outputs/skill-reviews/
   <skill>-gaps-*.md` — the LOOSE pattern: legacy round-1 files may lack a
   `roundN` token entirely (measured: `project-retrospective-gaps-2026-08-16.md`
   is round 1), so a `-round*` glob undercounts and would restart a loop at a
   colliding "round 1". Files without a token are round 1; this round's number
   is max+1. The latest disposition's "sharpest next test" section is this
   round's entry point (a merged single-file round IS its own disposition).
   No prior rounds → round 1, start from the skill's own trigger situation.
1. **Executor leg — real, owed work only.** Pick a task that is genuinely due
   (a real close-out, a due cleanup scan, an unaudited fresh rewrite), never a
   staged exercise: the round then pays twice. Follow the skill LITERALLY;
   every deliberate deviation is data, recorded with what following the letter
   would have produced.
2. **Gap report** — a NEW file, `<skill>-gaps-round<N>-<date>.md` in the
   output directory above. Per gap: current-text quote → what actually
   happened → paste-ready fix (English). Plus: credibility bounds up front
   (n, executor==evaluator?, what stayed untested), a 「不建議改」 list (what
   worked and must not be churned), and priority order (P0 = wrong output if
   unfixed / P1 = high-value miss / P2 = friction).
3. **Upgrader leg.** Verify every quote against the artifact before adopting
   — a citation that does not match voids that gap, not the report. Adopt or
   narrow; honor the 不建議改 list; run `config-self-audit` on the edited
   artifact; commit via branch → `--no-ff` merge (in `~/.claude` itself the
   branch-commit guard requires committing on `main` — commit there
   directly; round-1 ux-walkthrough field data 2026-09-07); write the **disposition**
   beside the report, named `<skill>-gaps-round<N>-<date>-disposition.md` —
   the name is load-bearing: step 0's lookup depends on it (per-gap verdict |
   where it landed | adjustments and why), ending with the **sharpest next
   test** for the following round.
   **Code-bearing rounds** (the fix is a gate, hook, or instrument): the
   shipped selftest going green is a claim about the selftest. Two more legs,
   author ≠ verifier, both dispatched: a **design review BEFORE build** when
   the round adds a mechanism (measured 2026-09-11: it caught the wrong
   Crossref key, `update-to` on the notice vs `updated-by` on the cited work,
   before a line was written), and an **adversarial QA AFTER build** that
   must probe beyond the suites with a fixed boundary list — trailing-dot
   host, path traversal in every name argument, a redirect that changes the
   host, the fixture's own inputs through every regex, a JSON line that parses
   but is not an object, a numeric argument passed as a string. Measured the
   same day: every suite 100% green, QA found 4 BLOCKERs, 0 covered by any
   suite. Every finding is reproduced by a command; the disposition table
   keeps the no-change rows with their reason.
   **A new gate on a skill with history** is born with a dated cutoff
   (`LEGACY_CUTOFF`, one constant shared by every reader): runs before it WARN,
   runs after it FAIL. Without the date the gate is either softened on the
   first old artifact it breaks or stays WARN forever (the inert-promotion
   shape of `entry-schema-lint`, 2026-09-09).
4. **Cross-skill sweep before closing.** A gap fixed here often has a twin in
   a sibling skill (the same ask-consolidation shape appeared in three
   skills), and in a **rule-tier file the skill executes**: a rule written on
   day N leaves the skill's playbook saying the pre-rule thing on day N+1
   (measured: `rules/literature-access.md` 2026-09-10 forbade circumvention;
   `search-sources.md` rung 3b still told the executor to render anti-bot
   pages headless — grep the skill for the OLD instruction, not the new rule).
   And if any ruling this round REPLACED mechanism A with B, grep same-day
   artifacts for stale references to A — a rejected-then-referenced
   mechanism reads as correct forever.

## Engine-skill techniques (skills that act on the environment)

- **Differential double-run**: run a checklist skill twice in one session on
  different targets and diff which checks each run actually executed —
  silent skips surface immediately.
- **Reflexive scope**: the skill itself is a valid target of its own scan
  (env-cleanup found its own stale desktop-cache duplicate). Its **worked
  examples and fixtures are inputs to its own gate**: every identifier or
  number a skill's manual cites as an example is a claim — resolve each one
  live once and keep it as a calibration fixture (measured 2026-09-11: the
  citation gate's own docstring attached "Nagpal 2009" to a DOI that resolves
  to another paper; it sat there 15 days and surfaced only when the example
  became a must-pass case of the gate it illustrated).
- **Desk dry-run rule**: a code path no natural task exercises within ~2
  rounds gets a desk walkthrough or sandbox instead of waiting — waiting a
  third round is not testing, it is luck. Keep the untested flag until a real
  run confirms.

## Artifact-skill techniques (skills that produce deliverables)

Adopted 2026-08-28 from the diagram-authoring F1/F2 field series (a planned
field test, not a formal loop round; user-directed adoption).

- **Consumer-position round (reuse-as-audit)**: make one round REUSE the
  previous round's artifact as a component (copy its framework, import its
  output). Acceptance examines a deliverable from the reader's seat; reuse
  exercises it from a consumer's seat and surfaces what both machine checks
  and the human gate miss (measured: F2's framework copy exposed 56
  silently-missing arrowheads in the ACCEPTED F1 deliverable — two
  verification rungs and a user gate had all passed it).
- **Post-acceptance defect = loop data, not an emergency**: report it with a
  proposed version bump and let the user rule — never silently fix an
  accepted artifact. The fix ships WITH the check that would have caught the
  class (positive-control calibrated: break one instance, the check must
  fire), and the round re-verifies the artifact's accepted behaviours
  unchanged. The check, not the fix, is what upgrades the skill.

## Convergence and stopping

Findings should converge (measured: 14 → 7 → 4 → 4, structural → seam-level).
When a round yields no P0/P1, recommend CLOSING the loop for that skill —
core need met → stop; further rounds are on-demand (next natural misfire,
rewrite, or an external standard arriving), never scheduled. Never run a
round just to have run one.

## Reflexivity

This skill is itself in scope of the loop, with one definitional rule: a
standalone round TARGETING this skill has no natural carrier task, so it is a
**desk dry-run by definition** — declare it as such, keep its findings flagged
text-level, and let the next real round (any target, run THROUGH this skill)
serve as the field confirmation. Gaps in THIS file follow the same protocol,
same output directory, same standard.
