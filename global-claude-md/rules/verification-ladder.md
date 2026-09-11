---
paths:
  - "**/tests/**"
  - "**/test_*.py"
  - "**/*_test.py"
  - "**/conftest.py"
  - "**/verify*.py"
  - "**/*gate*.py"
  - "**/*.lean"
  - "**/*.test.{ts,tsx,js,jsx}"
  - "**/verify/**"
  - "**/*_audit.json"
  - "**/*_results.json"
  - "**/*_run.txt"
---

# Verification ladder: an invariant names the rung of evidence it carries

Written 2026-09-06 from the Lean 4 evaluation + spike (dated records in the
source environment's own `outputs/` tree — source-only, does not ship here).
The trigger is "a test, a gate, or a proof file is in play", which `paths:`
observes directly. It replaces the ai-coding-guardrails §2 wording, which
telemetry showed never fires (0 sessions invoked that skill; product-design-
thinking 31). Index line lives in `CLAUDE.md`; review-when: Hypothesis is
absent from the interpreter that runs a project's suite (rung 2 then needs a
venv or falls to rung 1), or a project adopts a framework that owns property
testing (schemathesis, fast-check) — the rung numbering stays, the tool
column changes.

## The property, not the reminder

**A test suite, gate, or invariant claim states which rung of evidence it carries,
and a rung is never claimed above what the domain allows or below what it demands.**

| rung | evidence | when it is the right stop | must ship with |
|---|---|---|---|
| 0 | example tests | a scenario, never a property | — |
| 1 | exhaustive enumeration (`parametrize` over the whole domain) | the domain is FINITE (an enum, a transition table, a small product) — exhaustive tests ARE the proof; nothing above adds truth | the enumeration derived from the table, not hand-listed |
| 2 | property-based test (Hypothesis) | the DEFAULT for a pure function over an infinite domain (strings, paths, numbers, lists): the property is named in the test name; generators encode the boundary structure (neighbours of a value, not uniform noise) | a known-true positive: a mutant or a historic bug the property fails on |
| 3 | concolic counterexample search (CrossHair) | rung 2 keeps passing but a counterexample is suspected, AND the function is analysable (no `unicodedata`, no subprocess) | the same positive, caught in SYMBOLIC mode — measured 2026-09-06: CrossHair 0.0.110 returned CONFIRMED on `re`-based code whose `$` and `.` newline semantics differ from CPython in its own regex model (`relib.py`); it caught the positive only when the input was fully concrete. A CONFIRMED that the positive did not pass through is a verdict about the tool's model; "not analysable / timeout" is recorded, never read as verified |
| 4 | proof of a mirrored model + differential test (Lean 4, a source-only verifier tool — does not ship here) | a universal statement is itself the deliverable — a named INV-n that says "for every input" and must be quoted as proven | gates A (no `sorry`) / C (`#print axioms` allowlist) / D (Python vs model on hand + random fixtures), with a sorry-mutant and a semantics-mutant control |
| 5 | verified core replaces the implementation | correctness-critical and performance allows | — (no live instance) |

Consequences the ladder settles:

- A finite state machine stops at rung 1. Proving its table in Lean re-proves what
  the exhaustive test already established (media-fetch-pipeline `test_queue.py` is
  the instance: every legal and illegal edge, `ACTIONS ⊆ LEGAL_TRANSITIONS`).
- Rung 2 is not "more tests"; it is the first rung whose evidence is about ALL
  inputs. Its cost on the reference target was one file and 1.3 s of run time; it
  found the same trailing-newline divergence the Lean differential found, and a
  second one (`.` vs newline) the Lean random fixtures had excluded — both fixed
  in `xi_scan.glob_to_regex` the same day (`\Z` + DOTALL) and locked at rungs 0/2/4.
- Rung 4 proved what rung 2 cannot state: the property holds for every path, not
  for every generated path. Reach for it when that sentence is what the design
  document must say — otherwise it is a 3.1 GB toolchain re-stating a test.
- Every rung ≥ 2 runs its known-true positive in the same invocation as the
  real check (two-sided calibration, global CLAUDE.md gate rule): a property that
  has never failed is not known to be measuring.
- The rung is written where the claim is: the test's name/docstring, the gate's
  status line, the INV-n `verified-by:` field (product-design-thinking
  document-ladder). A rung claimed in prose only is rung 0.

Live instances: rung 2 the source environment's `cross-index` tool test suite
(source-only, does not ship here); rung 4 its `lean-verify` tool (status line
`LEAN-VERIFY … severity=WARN`; source-only, does not ship here).

## The second property — the record, and when a task owes one

Added 2026-09-10 from the SSLD verify comparison (T47 `verify/dual_path_audit.json`
vs T48 `verify/`). The ladder above says how STRONG the evidence must be; it says
nothing about where the evidence lives afterwards, and a rung nobody can re-read
is a rung claimed in prose. Same subject, same file, one index line.

**A claim that outlives the session, and that a later reader cannot recompute
from what is in front of them, ships with a verification record placed beside
the thing it certifies.**

**Trigger — all three, or the task owes nothing.** Without this a project grows
a `verify/` in every corner:

1. the claim lands in a DURABLE artifact (document, page, deck, register), not
   only in the reply;
2. it was produced by RUNNING something — a computation, a gate, a measurement —
   not cited from a source and not a design statement;
3. someone will act on it WITHOUT re-running it.

Not owed: a one-shot analysis whose answer lives in the reply; a derivation
printed inline in full (the reply IS the record); a re-run of an instrument that
already writes its own record (extend that record — a second one beside it is
how two disagreeing histories start); a gate whose single verdict the delivery
quotes and nothing downstream cites. **The unit is the fact-producing RUN**, not
the task and not the gate: many gates, one transcript.

**The shape — two artifacts, and the split is the point.**

| artifact | answers | carries |
|---|---|---|
| fact layer — `<name>_results.json` / `_audit.json`, beside the outputs it feeds | what was computed, from what, under what controls | `schema` / `generated_by`, `inputs`, the results, `controls` named positive AND negative, the instrument's fidelity level, and `upstream` = path + sha256 of every input read |
| run transcript — `verify/<name>_run.txt` | that the check actually RAN, and what it printed at that moment | the control lines verbatim, the failing lines unscrubbed, and any self-reported rate BESIDE its ruler |

**Which SSLD format is better.** They are not two formats; they are the same one
at two degrees of separation, and the more separated is better wherever it is
available:

- T47 `dual_path_audit.json` (136 KB, one file): nine result sections,
  `controls[46]` + `control_summary`, `inputs`, `meta`, `upstream_sha256`. Facts
  and audit in ONE artifact written by ONE program — the instrument grades
  itself, which the global gate rule forbids for exactly this reason.
- T48: facts in named layers at the round root (`eb_results.json` 31 controls,
  `eb_design.json` 40, `figs/competitor_facts.json` with per-row sources), while
  `verify/` holds the CHECKER (`check_record_numbers.py`) and the run
  transcripts. The checker is a different program and reads the EMITTED record —
  3849 pooled values against 643 numeric tokens in the prose, 0 unaccounted,
  51 load-bearing numbers tied to the expression that produces them, with an
  injected-number negative control.

So: **T48's split, carrying T47's provenance block.** T47's single file stays
correct in one case — a closed-form derivation with no separately emitted
document to check; there is then no second artifact for a checker to read and
the split is ceremony. The moment a human-written record or a built page quotes
the numbers, the checker moves out and reads THAT.

Two honesty properties of the T48 record, both worth copying and neither
automatic: the checker **prints its own false-accept rate** (35.2% at 3+
significant digits, 95.3% at 1–2 — "the screen is therefore a SCREEN, not a
proof"), and the transcript **keeps its failures** (that round's page build
recorded a fill-gate FAIL rather than scrubbing it). A record with no rate and
no failures is a record of a run that was never at risk.

Live instances of this property: two source-only tools (both 2026-09-10, each
shipping its calibration in `--selftest`; do not ship here); SSLD T48 `verify/`.
Review-when: a project adopts a runner that writes its own immutable evidence
store (the transcript then names that store instead of a `_run.txt`).
