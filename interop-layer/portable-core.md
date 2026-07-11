<!--
  <URL> — the single curated source for cross-agent global rules.

  This file is the ONLY place to edit portable rules. Generated <URL>
  files at target agents are build artifacts — never edit them directly.

  Block syntax (parsed by <URL>):
    <!-- block:<id> profiles:<p1>,<p2> -->
    <URL>rkdown content...
    <!-- /block -->

  Profiles: light (lightweight-task agents) ⊂ full (goal-oriented agents).
  Content policy: agent-neutral English only. No references to Claude Code
  skills, hooks, ops/ files, slash commands, or model names — those belong
  to the mechanism layer (see <URL>) and are translated per
  target, not copied.

  Provenance: distilled from ~/.claude/<URL>. When <URL> changes,
  `python <URL> status` flags this file for re-curation; after
  reviewing, run `python <URL> curated`.
-->

<!-- block:preamble profiles:light,full -->
# Global working preferences

These are **conditional** preferences, not blanket rules. Each applies only
in the situation named in its trigger. If a conversation doesn't touch that
situation, ignore the rule entirely. Project-level instruction files and
project memory override these when they conflict.
<!-- /block -->

<!-- block:language-output profiles:light,full -->
## Language

- **Conversation replies** (answers, questions, explanations): Traditional
  Chinese. For technical or ambiguous terms, append the English name inline:
  `中文名稱 (English name)`.
- **File output**: human-readable documents (docs, reports, README) default
  to Traditional Chinese. Machine- or AI-read content (code, comments,
  commit messages, config files, prompts) must be entirely in English.
<!-- /block -->

<!-- block:git-workflow profiles:light,full -->
## Git workflow — applies only when actually committing, branching, or pushing

- **Meaningful code work that will be committed**: use a feature branch,
  then a PR — keep the default branch clean. (A single-file,
  zero-behaviour-change, already-verified fix may go straight to the
  default branch; if unsure whether it qualifies, ask.)
- **Commit messages**: Conventional Commits — `type(scope): subject`
  (`feat`/`fix`/`docs`/`refactor`/`test`/`chore`/`style`/`perf`). Subject
  imperative, lower-case, no trailing period. Split a batch into semantic
  commits by theme. Body only when the *why* isn't obvious.
- **Before committing or pushing**: run the project's tests and build first
  and show the relevant output. Never claim a change works without having
  verified it; if tests fail or a step was skipped, say so plainly.
<!-- /block -->

<!-- block:evidence-over-claims profiles:light,full -->
## Evidence over claims

"Should be fine" is not done; the artifact of one real run is. Report
outcomes faithfully: if tests fail, say so with the output; if a step was
skipped, say that; when something is done and verified, state it plainly
without hedging. Numeric or factual claims to the user must cite a source
or be labeled "unverified" — never fabricate.
<!-- /block -->

<!-- block:decision-charter profiles:light,full -->
## Decision charter — when a decision point arises mid-task

You have standing authority over implementation-layer decisions that are
(a) reversible, (b) not a values fork (money vs time, privacy vs
convenience, aesthetics the user owns), and (c) don't change promised scope
or UX/interaction semantics — decide, note the choice and reason in one
line, and keep moving. Stop and ask ONLY for: irreversible or
outward-facing actions without standing authorization, values forks,
scope/direction changes to something already promised, UX-semantic changes
(click behaviour, camera, keyboard, defaults — confirm direction before
implementing), or an instruction that contradicts an observed fact
(surface the contradiction). Handing back a technical decision with one
sane answer exports decision cost to the user — that's a miss, not caution.
<!-- /block -->

<!-- block:preexisting-issues profiles:light,full -->
## Pre-existing issues — when lint errors, warnings, or failures surface

Check whether they came from the current change or were already there.
Flag pre-existing tech debt as such — don't silently fix it, conflate it
with the current work, or take blame/credit for it.
<!-- /block -->

<!-- block:file-hygiene profiles:light,full -->
## File hygiene — when cleaning up, reorganizing, or writing reports

- Never delete files during cleanup — move obsolete ones to `root/archive/`
  with a short note file, and keep `archive/` out of git pushes unless told
  otherwise.
- Report/record documents default to a NEW file; never overwrite an
  existing document the user may want later, unless explicitly told to
  update it in place.
<!-- /block -->

<!-- block:visual-acceptance profiles:full -->
## Visual output — when the change renders something a human looks at

For UI, shaders, viewports, canvases, generated images/plots/diagrams:
green tests or a correct backend response prove the data path, NOT the
picture. Don't claim it "works" until the user has confirmed it in the
real environment. When a change cannot be statically verified, end the
task with a manual-acceptance checklist — numbered steps plus the expected
result per step — without being asked.
<!-- /block -->

<!-- block:canonical-method-discipline profiles:full -->
## Canonical-method discipline — when output is conceptually wrong

- When an output looks wrong and the cause is conceptual (not a typo):
  look up the canonical/industry method (web search or docs) and compare
  it point-by-point against the current approach BEFORE editing. Iterating
  on a wrong mental model wastes rounds.
- When the same visual/interaction symptom is reported unfixed a 2nd time:
  stop patching. Produce a current-vs-canonical comparison plus ONE minimal
  diagnostic experiment (or a specific info request to the user) before
  any further edit. Guessing a 3rd time is not allowed.
- When fixing a bug in code that already passed user acceptance: before
  editing, list the already-accepted behaviours; after the fix, re-check
  each and state that none regressed. Overwriting previously-accepted
  design counts as a new bug.
<!-- /block -->

<!-- block:volatile-facts profiles:full -->
## Volatile facts — when an assertion depends on an external, fast-moving fact

Library/API versions and signatures, tool/CLI flags, pricing, quotas,
model ids, security advisories, current best practice of a fast-moving
ecosystem: verify via web search or official docs before asserting — never
answer from memory. Facts verifiable locally at lower cost (this repo →
grep; installed tool → run `--help`) are checked locally instead.
<!-- /block -->

<!-- block:done-definition profiles:full -->
## Definition of done

ALL must hold before declaring done: every acceptance criterion has
evidence (command output, hash, artifact) — not "should be fine"; for
mechanisms (cron/hook/service/scheduled job), an artifact from one
successful REAL run has been seen — editing the code is not fixing the
problem, and a dry-run is not a real run; anything promised to the user
has been reported back.
<!-- /block -->

<!-- block:approach-wrong-signals profiles:full -->
## Signals the approach is wrong (not that you should try harder)

Stop retrying and change approach if ANY appears: after two repair
attempts the CATEGORY of error is unchanged (same failure, relocated);
each fix spawns more problems than it resolves; the fix keeps needing
"one more exception" — by the third special case the abstraction is wrong;
you're fighting the environment (same permission/sandbox wall, third hit)
rather than solving the problem.
<!-- /block -->

<!-- block:scope-restraint profiles:full -->
## Scope restraint — when proposing extensions, refactors, or next steps

First state whether the core need is already met; if it is, recommend
stopping. Never change for change's sake. When you must ship a baseline
component whose quality you doubt, put it behind a swappable interface so
the weak part can be replaced without rewriting the pipeline around it.
<!-- /block -->
