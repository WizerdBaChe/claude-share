# Step 6.2 detail — global-candidate triage, persistence, and the backlog report

Extracted VERBATIM from SKILL.md Step 6.2 on 2026-09-06 (BODY_CAP trim; content
unchanged — this file is the full protocol, SKILL.md Step 6.2 keeps the rule and
points here). The rule that stays in SKILL.md is the one that must never be
missed: **this skill NEVER writes to `~/.claude/CLAUDE.md`** (user ruling
2026-08-31). Everything below is how the triage is performed and recorded.

## The four gates — triage, not write authorization

They produce a per-candidate recommendation (adopt / merge into X / reject) for
a FUTURE batch session. A candidate destined for global would have to pass ALL
four:

- (a) **Generalizable — and checked, not estimated.** Judge this on Step 2.4's
  rule-sibling-scan results, never on reasoning alone. A rule that two projects
  arrived at independently is evidence-backed; a rule seen once is a
  hypothesis. Record which it is in the candidate table's "why" column.
- (b) **Not already covered** — read the current `~/.claude/CLAUDE.md` AND the
  skill descriptions before proposing. A rule that duplicates an
  always-triggering skill is charged twice; the fix is that skill's trigger,
  not a new global line.
- (c) **Not better merged** — if it is the *how* of an existing rule, propose it
  as an amendment to that rule, not a new one. Two rules competing for one
  situation is worse than one rule that is slightly longer.
- (d) **Worth its rent** — global is charged to every session. Rank by observed
  occurrences across projects, not by how important it feels. A sharp rule that
  fires twice a year belongs in `~/.claude/ops/lessons.md`, not global. A rule
  whose occurrence count went UP because of this project's evidence should be
  re-proposed even if a previous retrospective rejected it — say so explicitly,
  with the old verdict and what changed. The rejected-candidate history lives
  in `global-rule-candidates-*.md`, not in Document 2.

Present candidates as the Step-4 table (rule | recommendation: adopt / merge
into X / reject | why) for information/correction only.

## Persist the full candidate table

Including every rejection and its why, as
`global-rule-candidates-[project-name]-[date].md` in the output directory.

- The header MUST state the batch's status — default is
  `judged-but-deferred (pending batch session)`. **`executed` may only ever be
  written by the batch session, never by this skill.**
- The tail MUST carry a section "Input for the next Step 2.4" saying, per
  candidate, what new evidence would re-open it.

A candidate with no status is invisible to the next round — it cannot tell
"judged and rejected" from "judged and parked" from "never ruled", and those
three answer "re-propose?" differently. That file IS both the
rejected-candidate history a future Step 2.4 scans AND the work queue the batch
session consumes; if it is not written, the candidates simply vanish.

## Report the accumulated backlog — the deliverable of this step

Glob `global-rule-candidates-*.md` in the output directory, count the
candidates in files whose header status is still pending/deferred, and state it
in the check-in or close-out:

> "N pending global-rule candidates across M files — 批次處理時另開一個
> session 即可"

The count, not a question, is what the user acts on. Do not push for that
session, and never treat the check-in's silence as anything: there is nothing
to approve here.
