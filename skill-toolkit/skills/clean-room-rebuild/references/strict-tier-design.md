# STRICT tier — design draft (not built)

> status: DEFERRED — trigger: the first rebuild whose result is publishable code AND whose source is copyleft or proprietary; residual: the controls below, ranked, for that round's build

User ruling R4 (2026-10-09): STRICT stays a draft until a real case needs it. Until
then a STRICT request runs STANDARD + the user's spec review and says the rest was
not available.

## What STRICT adds over STANDARD, and why

| # | control | closes which gap | determinable? | cost |
|---|---|---|---|---|
| S1 | the user reviews and signs each spec version before handoff | the gate cannot see copied structure (SSO) | human read | user time |
| S2 | the source lives in a quarantine path; the writer runs in a worktree / scratch root that does not contain it | STANDARD separation rests on the prompt alone | yes | low |
| S3 | transcript audit: count the writer's tool calls whose path or URL names the source; must be 0 | proves S2 held | yes (session transcript archive + `tools/session-find.py`) | low |
| S4 | every spec version and gate output retained, hashed in the record | NEC v. Intel: an intermediate version was the infringing one | yes | low |
| S5 | similarity lens for code (JPlag or token winnowing over the AST) in addition to `overlap_check` | prose shingles under-read renamed-variable code copies | partly (surface only) | needs Java or a new script |
| S6 | writer on a different model family (Codex luna tier) | diversifies, does not remove, training-data exposure | no — label it weak | quota |

Not planned: a PreToolUse hook denying the source path to every agent (S2+S3 give the
same evidence after the fact without a machine-wide hook; revisit only if S3 ever
finds a non-zero count).

Field note for S3 (STANDARD dry run 2026-10-09, the source environment's dry-run record, not shipped in this copy):
a regex over the writer's tool-call inputs for the source's NAME false-fired once —
the writer's own test file contained `from globmatch import fnmatch`, a merger name.
S3 must match READ-kind calls (Read, Grep, Glob, a shell read) whose target is the
source PATH, never the module or project name.

## Build order when the trigger fires

S4 → S2 → S3 → S1 (already manual) → S5 → S6. Calibrate S3 with a planted read
(positive) and a clean run (negative) before trusting it; S5 with a renamed-variable
copy (positive) and an independent implementation (negative).

## review-when

- A court or a major foundation rules on AI-assisted clean-room rewrites (the chardet
  7.0 dispute, 2026-03, was unresolved when this was written) → re-read the S-rows.
- The session transcript archive changes format → S3's grep must be re-calibrated.
