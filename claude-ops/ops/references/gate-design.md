# Gate design — the full clause set behind CLAUDE.md's automated-gate bullet

Owner: global CLAUDE.md, Engineering judgement, "When you design, modify, or
read the output of an automated gate". CLAUDE.md keeps the trigger and the core
duties; this file keeps every clause with its incident. Moved here verbatim on
2026-09-19 when CLAUDE.md went over its byte cap (user ruling;
ops/40-maintenance.md §3: extract, never compress). ops/30-judgment.md R2 item 2
states the same duty at a second altitude — the two must not drift.

review-when: a clause here is cited by a gate failure that CLAUDE.md's short
form would not have prevented — that clause moves back up (and something else
comes down), because the short form is then too short.

## The bullet as it stood in CLAUDE.md (verbatim)

(acceptance layer, CI check, parser, evaluator, lint rule): it may only rule on
what it can DETERMINE — anything else is downgrade-and-forward, never veto. A
negative-but-plausible verdict is a false negative until the instrument is
checked: report the ruler beside the rate; measure the idle baseline first (a
value uniform across the whole window is the floor, not a signal); calibrate
with a known-TRUE input and a known-false one and CONFIRM the positive control
fires — a control that never fails is no control, and an inverted case that
still passes is usually an assertion aimed outside the defect's scope: assert
on the value the defect would CHANGE, never on the decision label (L-062). A
fresh checker returning one verdict for n≥3 inputs is an instrument fault until
the positive control refutes it; a new mechanism's first real output never
feeds downstream in the same step (a reject-everything gate, or a rollup whose
ranking makes rejection unreachable, scores 100% one-sided; L-072). Persist
whatever the gate may reject BEFORE it runs; never publish a rate the metric
cannot print the evidence for. **The gate reads the EMITTED artifact, never the
producer's own intermediate state**, and **its object vocabulary must cover
every class the governing rule names** — when the same symptom recurs after N
fixes, first ask which object class the complaint names that the model has no
word for (L-044). **A gate's predicate must not be a POSITION in an artifact
that grows** (a region, a dense id, an offset): growth moves things across the
boundary while the number stays plausible — prefer the position-free form and
flag the out-of-region case separately (L-047).

## Clause index (what CLAUDE.md now says in one word each)

| clause | CLAUDE.md keeps | detail kept here | lesson |
|---|---|---|---|
| determinable-only | yes | — | — |
| false negative until checked | pointer only (2026-09-28) | ruler beside the rate; idle baseline = the floor | — |
| two-sided calibration | yes | a control that never fails is no control | — |
| assert the changed value | yes | an inverted case that still passes = mis-aimed assertion | L-062 |
| unanimous fresh checker | pointer only (2026-09-28) | reject-everything gate / unreachable-rejection rollup | L-072 |
| first output not fed downstream | yes | same | L-072 |
| persist before reject | yes | — | — |
| no rate without evidence | pointer only (2026-09-28) | — | — |
| emitted artifact | pointer only (2026-09-28) | — | — |
| object vocabulary | pointer only (2026-09-28) | recurring symptom → which class has no word | L-044 |
| position-free predicate | pointer only (2026-09-28) | region / dense id / offset; flag out-of-region separately | L-047 |
| wired to the event | not in CLAUDE.md (folded here 2026-09-29, budget) | a gate's verdict runs at the EVENT that changes its input — a save-time hook on the declared files (`Live-reads:` docstring line, golive_check) or a commit-time point — never only in a monitor that reads it later; a check the monitor alone runs turns "see the red lamp, come back and fix" into a required step, and the red then looks like a new defect each time (hit 1: a live-read Markdown register; hit 2: the class-closure verdict that ran only in the manual sweep; hit 3, 2026-09-28: the save-time NOTICE fired and was ignored — a notice cannot change the call it annotates, so where a cost-free equivalent call exists the event-wired gate is a DENY carrying that call: `hooks/registry_row_guard.py`, `REGISTRY_ROW_GUARD`) | L-121 |
| event baseline | not in CLAUDE.md (2026-10-05, CLAUDE.md over budget) | a gate that judges "changed since my last action" keeps its baseline as a record written AT that action (a content snapshot in its own log, or a stamp taken after a commit-first precondition, or its own atomic self-commit) — never re-derived from commit history, and its own writes never count as evidence (blank them before comparing). A commit is not an event: a tool's uncommitted write rides in whatever commit comes next, so "the last commit touching my marker" can contain the very change the gate is looking for (hit 1, 2026-10-04/05: `tools/lab-skill-sync` refused a real write-back 4 times, and its sibling pair passed only because the dirty marker line counted as a write-back). Survivors that hold by construction: `moc_regen --commit` (self-commit), `interop curated` (commit-first). Overriding a gate is the substitute act for reporting it, so registered override flags raise a feedback notice (`tools/feedback-pool/gate-overrides.json`, `hooks/feedback_notice.py`) | L-140 |
| input-class coverage | not in CLAUDE.md (2026-10-09; the «object vocabulary» clause states the principle, this row the build-time check) | before a gate is called calibrated, write the map «each input class the governing artifact PROMISES (file types, scripts, size ranges, source kinds) → the control that exercises it»; a promised class with no control is either given one or declared unsupported in the gate's own docstring, and an input the gate cannot read is counted apart and withholds the pass verdict — never skipped silently into it. Self-written fixtures drift toward the one class the author had in mind, so the map is built from the PROMISE, not from the fixtures (hit 1, 2026-10-09: `skills/clean-room-rebuild` Step 0 promised PDF / book / URL sources, its gate read plain text only, 24/24 controls + config-self-audit + a one-source dry run all passed; an external read-only review found it; fixed `176077f`, controls W3/W4/X1/P14). Checked by config-self-audit §1 | L-044 |
| backtest before birth | not in CLAUDE.md (pointer row, 2026-10-03) | the rule lives in `ops/40-maintenance.md` §2a(4) ("no baseline yet → backtest first") and L-011's fifth shape (measure each trigger's surface on the corpus); the instrument is `tools/hook-backtest/` — name the hook's `<module>:<function>` (or an `adapters.py` predicate composed from the hook's own exports, never a copy) and it replays every recorded tool call, printing fire count + per-fire date / session / locator and never the call's text unless redacted | L-011 |

"pointer only" = CLAUDE.md names the clause family in its closing parenthesis
(instrument checks, emitted-artifact reads, position-free predicates, rate
publication) and this file carries the rule; trimmed 2026-09-28 to bring
CLAUDE.md under its 23,552-byte budget after a `/doctor prompt-audit` run.

Related, path-scoped: `rules/verification-ladder.md` (rung of evidence, mutation
magnitude from the data, the verification record).
