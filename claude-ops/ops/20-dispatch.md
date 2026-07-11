# Dispatch Rules — handing work to subagents without getting burned

Written to be followed mechanically — no taste required. Numeric thresholds are
defaults, adjustable per project but never silently. Tier names ("cheap / mid /
top") are roles, not model ids — map them to the current environment's actual
models at session start; never assume ids from memory.

## §0 Establish the environment first (once per environment, never from memory)

Check and record: available model tiers, the subagent/dispatch mechanism,
whether an independent second CLI agent exists (a genuinely different vantage
point for red-teaming), and whether scripted calls to your own CLI behave
normally (supervisor setups sometimes shadow the command).

**Where to record**: `ops/environment.md` — one file per environment holding
the tier→model mapping, cost-cap policy, and available dispatch mechanisms.
Read it before the first dispatch of a session; update it when facts change
(it lists its own refresh triggers). If it's missing or stale, re-establish
the facts first — never dispatch on remembered model ids.

## §1 Core rule: the dispatcher does no fieldwork

The dispatcher's job: read tickets, dispatch, receive conclusions, verify,
backfill, talk to the requester. Every raw file the dispatcher reads itself
permanently occupies main-context space.

**Delegate when any of these holds** (defaults): touches >3 files or >200
lines; repo-wide scan / broad grep / read-many-files-to-answer; web research
beyond a quick ≤3-source lookup; writing a new script/module; batch edits
(isolate in a worktree if large).

**Do it yourself when**: single-file edit under ~50 lines; urgent
stop-the-bleeding fix; taking over after a worker failed the same subtask
twice; the final write of any rule-tier file (workers draft, main session
writes — see `40-maintenance.md` §1).

✅ "Find every caller of X across the repo" → search subagent returns 12
`file:line` refs; main context grows by 12 lines.
❌ Dispatcher greps the repo itself and pages through 3,000 lines of matches —
the rest of the session now pays rent on that noise.

**§1a Degraded environments (no subagent mechanism)**: the separation of
duties is the invariant; the mechanism is negotiable. Run scanning as a
separate phase whose raw output is reduced to conclusions + refs BEFORE the
decision phase reads it; simulate reviewer separation with a fresh pass under
a different role framing ("review as tomorrow's inheritor, no memory of
writing it"). State the deviation explicitly.

## §2 The dispatch contract (all five parts, or it doesn't go out)

1. **Goal AND motivation** — a worker that knows why can make correct calls on
   details you didn't spell out.
2. **Machine-checkable acceptance + output-format contract** (exact structure,
   schema, verbatim-preserve fields). Format drift is a more common failure
   than wrong content. State the goal, not the proof ritual — "prove your
   own work passes" invites an expensive self-verification loop. The worker
   self-checks FORMAT compliance only; ACCEPTANCE verification belongs to
   the dispatcher with fresh context (`10-command-loop.md` Step 6).
3. **Report format** — the shape of the conclusion + where artifacts land.
4. **Redlines** — the explicit do-not-touch list (rule-tier files, production,
   anything the project protects).
5. **Self-sufficient materials** — copy specs/references the sandbox may not be
   able to reach into a path the worker CAN read. A worker that can't read what
   it needs tends to fabricate a plausible answer rather than report the gap.

✅ "Goal: unify date formats (downstream parser needs ISO-8601 — that's why).
Acceptance: `python check_dates.py out/` prints OK. Output: JSON per schema in
schema.json. Redlines: don't touch archive/. Read first: spec.md (copied to
your scratch dir)."
❌ "Clean up the dates in these files, you know what I mean" — no acceptance,
no format, no redlines; whatever comes back is unreviewable.

## §3 Gotchas when dispatching to an external CLI agent (verify in your env)

1. Background jobs: redirect stdin from `/dev/null`, or some CLIs hang waiting.
2. Launch from a genuine scratch dir, not an OS-protected folder — some
   sandboxes silently fail to read protected paths and fabricate instead.
3. Always wrap with an outer timeout — some agents hang silently.
4. Non-git working dirs may need an explicit "trust this directory" flag.

## §4 Model / effort assignment (two axes: model × effort)

Strength has two axes: model tier AND effort/thinking level. The current
environment's tier→model-id mapping, cost cap, and
enforcement mechanism live in `ops/environment.md`; this table stays in role
terms. **Cap rule**: everything above "mid tier + high effort" requires
explicit per-instance user approval (mechanically enforced where the
environment supports it — see `environment.md`).

| Task shape / severity | Model tier | Effort |
|---|---|---|
| Summarize / reformat / dictionary-style lookups | cheap | low |
| Translation / extraction / small to-spec scripts — anything with a hard machine-checkable gate | cheap + explicit output-format contract (a hard gate substitutes for tier quality on internal work; outward-facing "always top-tier" project rules still win) | low |
| Search / inventory / read-many-files | cheap–mid, search-oriented subagent | medium |
| Write a script/module | mid; always review the result | medium |
| Red-team / review | a different model family/tool than the author if one exists; else fresh-context mid tier. **Reviewer ≠ author, always** | high |
| Research / multi-source verification | mid, research-oriented subagent | high |
| Taste, ambiguous judgment, policy wording | main session — not delegable, see `30-judgment.md` R6 | — |

Where the dispatch mechanism supports a machine-enforced output schema (see
`environment.md`), use it instead of prompt-side format instructions — format
drift is the most common cheap-tier failure, and a schema eliminates it.

## §5 Escalation and de-escalation

- Cheap-tier fails once → re-dispatch one tier up. Same-tier retries usually
  reproduce the same failure.
- Same subtask fails twice → diagnose the reasons first (`30-judgment.md` R1):
  the SAME reason twice = an environment problem → fix the environment, don't
  escalate; two DIFFERENT reasons = the task exceeds the tier → top tier or
  take over in the main session, carrying the COMPLETE failure trail (both
  rounds' prompts + errors) — never discard it.
- Once the top tier cracks a pattern → write it as explicit steps, push batch
  execution back down to the cheap tier.
- **Two retries max per problem** (default): the third attempt must change
  method, model family, or stop and ask.
- External quota exhausted → schedule a retry at the reset window or switch
  agents; don't idle.

✅ Escalate with both failed prompts attached → the stronger model sees how
its predecessors died.
❌ Re-send the identical prompt to the identical tier a third time "in case it
works now".

## §6 Dispatch templates (fill brackets; contract parts are non-negotiable)

**T1 Search/inventory** (read-only): task / motivation / scope (explicit globs)
/ match criteria + one worked example / output path + format (count →
categorized list, each `file:line` + ≤80-char excerpt) / redline: write only
the report file / reply: count + top 3 findings.

**T2 Implementation**: task + spec-file path (spec as file, not pasted) / read
first: self-sufficient materials / to-do (one verifiable action per line) /
design constraints stated as fixed / acceptance commands / redlines / reply:
≤5-line summary + acceptance output + known limitations.

**T3 Refactor/batch edit**: old→new pattern + scope / motivation /
**do-not-touch list (more important than the change list)** / per-file verify
command / batch cap of N files with a count per batch / ambiguous cases →
"needs a human" list, never guessed / output: change list + skipped list +
verify output.

**T4 Research** (read-only + one report): question / background + what decision
it feeds / starting sources (worker may add a few, each with URL + one-line
justification) / live search required, no training-data recall; every claim
cited / output structure: conclusion first → comparison table → verdicts
(adopt / don't / needs-human, each with evidence; mark uncertainty, never
fabricate) / reply: one-line method + top 3 conclusions.

**T5 Review/red-team** (read-only, never the author): target / context (runs
unattended? touches user data?) / cross-reference paths / focus areas ranked
by risk / verdict: PASS/FAIL first line + WARNING list (HIGH/MED/LOW, each
with `file:line` + failure scenario) / adversarial stance: raise at least 3
specific challenges.

Template rules of thumb: long spec → file first, then dispatch; acceptance is
written for the worker but the dispatcher still spot-checks (never a
substitute); on re-dispatch, put the previous failure output in "read first".

## §7 The report contract (what a worker hands back)

- Conclusions + `file:line` refs only; large artifacts to disk, path returned.
- Delivery summary: what was done (≤5 lines) + what was verified (commands +
  key output lines) + honesty clause (what couldn't be reached, what was
  skipped, and why).
- Any numeric or factual claim carries a source; no source → label
  "unverified". Never fabricate.

## §8 Token discipline (main-session hygiene)

- Batch micro-tasks: each dispatch has fixed overhead — don't send sub-minute
  tasks one at a time; one worker, several items, each verified individually.
- Small reference material: pass a path anyway (keeps the prompt short and the
  material updatable).
- Large tool output: check size first; read tail/summary before deciding to
  read more. Sanity-check output before treating it as content (does it look
  like an error string? suspiciously short or empty?).
