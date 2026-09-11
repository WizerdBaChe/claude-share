# Dispatch templates T1–T5 (owner: `20-dispatch.md` §6)

Detail file for `20-dispatch.md` §6. Fill the brackets; the five contract parts
(`20-dispatch.md` §2 — goal+motivation, machine-checkable acceptance +
output-format contract, report format, redlines, self-sufficient materials) are
non-negotiable whichever template is used. Loaded on demand.

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

**Fragment-writing briefs** (an addendum to ANY template above; the property
itself is owned by `20-dispatch.md` §2): when the worker writes into a governed
record — a manifest, ledger or audit file that is itself published, reviewed or
gated — the brief carries that record's own record-writing rule in its body,
the operative line quoted, or a read-first path when the rule is long. Why it
is the brief's job and not the worker's: `20-dispatch.md` §2, which owns the
rationale. Measured 2026-09-07 (a de-identification
round, seven parallel workers over disjoint path sets, each writing one
manifest fragment): the gate reported 38 leaks, every one of them in the merged
manifest and none in the collected files, because each fragment had recorded
its edits by quoting the value it removed. The class had been written down 11
days earlier — in the ORCHESTRATOR's skill, a layer no worker loads
(`ops/lessons.md` L-057).
✅ as an acceptance line in the brief: "each `edits` entry names the CLASS
replaced and the replacement, never the replaced value — this record ships with
the files it describes."
❌ "record each edit as `line N: <old> -> <new>`" — the record now carries what
the edit removed, published as widely as the file it was removed from.

Rules of thumb: long spec → file first, then dispatch; acceptance is written
for the worker but the dispatcher still spot-checks (never a substitute); on
re-dispatch, put the previous failure output in "read first". Which agentType
carries each shape: `20-dispatch.md` Agent roster routing. Which PATH
(subagent vs external tier): `20-dispatch.md` §4a; external-tier prompt shape
and failure signatures: `ops/references/external-dispatch.md`.

Worked example of the §2 contract (the shape every template must reduce to):
✅ "Goal: unify date formats (downstream parser needs ISO-8601 — that's why).
Acceptance: `python check_dates.py out/` prints OK. Output: JSON per schema in
schema.json. Redlines: don't touch archive/. Read first: spec.md (copied to
your scratch dir)."
❌ "Clean up the dates in these files, you know what I mean" — no acceptance,
no format, no redlines; whatever comes back is unreviewable.
