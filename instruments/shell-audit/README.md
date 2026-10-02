# shell-audit — the instruments behind L-024

Phase 8 (2026-08-19) measured two silent defects in the Bash tool's command
transport and shipped rules, a hook and a `.gitattributes` against them. These
are the instruments that produced those numbers, extracted from the session
scratchpad so the numbers can be re-derived rather than re-believed.

Report: the source environment's shell-command error audit (2026-08-18) ·
Rule: `ops/lessons.md` L-024 · Registry: `ops/rule-registry.md`

## Why these are files and not a scratchpad

Two reasons, both concrete:

1. **The evidence expires.** `cleanupPeriodDays` (default 30) deletes the
   transcripts every number here rests on — the 2026-08 corpus goes around
   2026-09-08. The daily mirror keeps them, so `sweep.py --root
   <mirror-dir>` still works afterwards. Without the tool, the
   only surviving artifact would be a report nobody can re-check.
2. **Four registered `review-when` entries name these runs.** A review trigger
   whose action is "re-derive the analysis from scratch" is a trigger that fires
   and gets skipped — which is exactly what happened to the instruction-loading
   entry, stamped Claude Code 2.1.220 while the machine ran 2.1.233 for 13
   builds.

## What is here

| file | answers | automatable? |
|---|---|---|
| `sweep.py` | per-tool and per-task-shape error rates; the Bash size-vs-failure distribution; backslash exposure | yes |
| `invariants.py` | do Phase 8's repo properties still hold — zero mixed line endings, `.gitattributes` resolving, guard registered, guard telemetry sane | yes |
| `PROBES.md` | the five tool-boundary probes, with results recorded 2026-08-19 | **no — and that is the point** |

`PROBES.md` is a runbook because the defects live at Claude Code's tool
boundary. A script calling `subprocess.run(["bash", "-c", ...])` never crosses
that boundary and reports everything healthy — a false negative convincing
enough to close the investigation.

Two siblings live elsewhere because they answer questions about rules, not shells:

- `tools/context-budget/rule_loads.py` — what loads at session start and what
  fires on `path_glob_match`.
- `tools/glob-fitness.py` — whether a path-scoped rule's globs can actually
  reach the code the rule is about. Built after `shader-failure-modes` was found
  matching zero files in its own source project.

## When to run what

| trigger (registered in `ops/rule-registry.md`) | run |
|---|---|
| any Claude Code upgrade | `PROBES.md` P1/P2/P4/P5, then `sweep.py`, then `rule_loads.py` |
| ~2026-10, `shader-failure-modes` re-check | `rule_loads.py` (fire rate) + `glob-fitness.py` (can it reach its subject) |
| guard feels noisy or silent | `invariants.py`, then compare its notice count against `sweep.py`'s Bash total |
| any change to `.gitattributes` or a bulk file write | `invariants.py` |
| a claim in the report is questioned | `sweep.py --json errors.json` and read the records |

## Reading the output honestly

- **Compare absolute counts, not rates, across runs.** Between 2026-08-14 and
  2026-08-19 `frontend-layering` went 7 -> 8 fires while its rate fell
  3.3% -> 0.7%, because the denominator grew 4.5x. Same behaviour, different
  number.
- **Deduplication is not optional.** Sidechain and compaction rewrites repeat a
  call verbatim, up to 6x; the raw 472 rows were 370 real errors.
- **A high backslash-exposure rate is exposure, not damage.** The collapse is
  silent, so the calls that did NOT error are where corrupted bytes reached
  disk.
- **The guard telemetry is seeded with test rows.** `test_shell_transport_guard.py`
  writes real entries every run, so treat the first ~90 rows as synthetic and
  judge the organic rate on what accumulates after.
- **A gate that only ever agrees with you has not been calibrated.** Every rate
  in the report came with a control arm; keep that habit when re-running.
