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
- **A control is proven by the ASSERTED VALUE differing between the correct and
  the defective build — record both values, not the verdict flip** (`ops/lessons.md`
  L-062, re-folded here 2026-09-23 from a global CLAUDE.md clause that sat outside
  the test files where its recurrences happened). Every shape L-062 collected is
  this one tell: an assertion aimed at a decision label the defect does not move;
  two sufficient defences, each hiding the other's removal; a requirement another
  requirement already satisfies; a hardcoded verdict; a mutation that lands in a
  gap of the data (next bullets). In each, the asserted value is IDENTICAL on both
  sides, and a record that prints the pair shows it in one run — the 2026-09-11
  SSLD T58d catch (19.36 / 28.32 pt on both sides) is the positive instance. A
  control whose record carries only PASS/FAIL is rung 0 about itself.
- **When the real input already FAILS an assertion, its known-true side must be a
  REPAIRED input, never a mutant** (SSLD 操作手冊 audit 2026-09-13). The usual
  calibration shape — perturb the value the assertion rests on, watch the verdict
  flip — silently degenerates on an assertion that is already False: False → False
  reads as "the control fired" while the assertion has discriminated nothing. So
  the pair is stated by VERDICT, not by direction: one input that must return True
  and one that must return False, whichever side the real data happens to sit on.
  For an already-failing check the True side is constructed by applying the fix
  (there: the label split normalised so it closes over its denominator, and the
  unreproducible quote replaced by the number the preserved transcript prints) —
  which also proves the proposed fix is the fix. Measured: a checker written the
  usual way reported `INSTRUMENT FAULT` on exactly the two of its five assertions
  that were already failing.
- **A control set whose size is FIXED while the artifact grows is an anecdote;
  generate the controls FROM the artifact** (2026-09-13, SSLD T01 DIR-1). One
  hand-written mutant proves the instrument can fire once. Mutating every object
  the artifact already carries — flip the direction word in each of the deck's
  own passing sentences, re-judge, require all of them caught — makes the control
  count scale with what is being checked, so it keeps measuring as the artifact
  grows instead of certifying the one case its author imagined. Measured: 6 fixed
  controls plus 4/4 artifact-derived mutants; the fixed six would still have passed
  a build whose new pages the gate could not reach.
- **The control's MUTATION MAGNITUDE comes from the data too, not only its
  existence** (2026-09-16, local-transcript-maker gap Q; L-062's eighth
  recurrence). The assertion can be aimed at exactly the value the defect would
  change and the control still not fire, because the mutation was too small to
  move that value: a threshold nudged from −1.0 to −0.5 changed a 31/61 count to
  31/61, since `avg_logprob` is a per-WINDOW number and the 61 neighbours carried
  **three** distinct values (−1.1691 / −0.3084 / −0.2071) — the new threshold
  landed in the gap between two clusters. The test read as calibrated and measured
  nothing. So a mutation is derived from the values actually present (here: the
  recording's own maximum, which forces `bad == total`), never picked because it
  looks like a reasonable number. Tell: the mutated run returns the SAME value as
  the unmutated one, and the test passes anyway because it only asserts a
  difference downstream.
- **A gate that declines to rule publishes its declined pile, and reads it BY HAND
  once.** The global gate rule says anything a gate cannot determine is
  downgrade-and-forward, never veto — which quietly creates a second pile nobody
  audits, and a screen can reach a perfect record by declining everything. So the
  first run of such a gate reads every out-of-range object once and records how
  many were read: measured 2026-09-13, 4 in-range against 30 out-of-range, all 30
  read, no missed claim — and one source-quoted line found that the gate correctly
  could not judge and a human could. Publish the two counts side by side forever
  after; a 4-verdict gate reported without its 30 declines reads as coverage.
- **Two independent passes over one deliverable report their OVERLAP.** Running a
  second reviewer is only evidence if the two are not reading the same thing.
  Measured (SSLD T01): an external review of the deck and two independent verifier
  passes produced DISJOINT defect sets — zero overlap, which is what justifies
  keeping both. High overlap is the signal to drop one, and it is not knowable
  without the comparison.
- **A gate that compares a computed result with a reference THROUGH an estimator
  (a fit, a slope, a window average, a quadrature) runs that estimator on the
  reference's own samples first, at the gate's grid and window, and it must
  return the reference inside the gate tolerance** (2026-09-15, COMSOL_Test
  round 24; `ops/lessons.md` L-097). "Calibrate with a known-TRUE input" was
  being read as "the control fires"; the missing half is "the ruler recovers
  the reference". Two gates read FAIL at −7 % with both model and closed form
  right — a log-slope ruler assuming a Gaussian the profile did not have, and a
  window fit compared with a t = 0 derivative — and each cost three solver runs
  before the ruler was blamed. The self-test costs seconds and no solver time; a
  ruler that fails it is a defect of the spec, and the gate does not run until
  it passes.
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

**A verbatim span certifies PRESENCE, not SUPPORT** (2026-09-13, SSLD T01,
independent data audit). A screen that keeps the triggering sentence with every
code looks self-evidencing, and the discipline is real — but "this sentence is
in the source" and "this sentence supports this code" are different claims, and
only the first is mechanically checked. Measured: three published values rested
on spans that were verbatim, quoted, and about something else — solder REFLOW
compatibility read as solder self-ALIGNMENT, a technique's own name ("photonic
wire bonding") read as a bonded interface, index-matching OIL read as a solid
bond. So a screen that publishes spans also publishes a **support** rate from a
sample a reader judged, and it is sampled **per CODE, not per axis**: the axis
looked ordinary while one of its codes was 6/6 wrong, because a rate averaged
over an instrument's codes hides the code that is entirely wrong. Audit the
lowest-support codes first — they are both the most likely to be artefacts and
the cheapest to enumerate exhaustively.

## The third property — a claim class whose evidence is a READER, and the trap in saying so

Added 2026-09-13 from SSLD T01. The ladder assumes a rung is reachable in
process. Some claim classes have none: the defect is not a property of the
artifact but of the **inference a reader draws from it**, so every gate reads a
file in which nothing is wrong.

**A deliverable naming such a class carries one external (non-author) READ before
it is called accepted, and the record names WHICH classes that read covered.**
An external read named only as "reviewed" certifies nothing — same rule as a gate
that matches zero objects.

The measured instance: a slide listed "fill the gap with a high-index medium"
among the ways to escape a tolerance line whose own printed table showed the
product FALLING with index. Every number was right; the direction was not. Five
text gates held green. Four classes generalise from that round — framing that
licenses a stronger inference than it states; terminology precision; ontology
mixing inside a published vocabulary; an aggregate used as if it were a member —
plus direction claims about relations the artifact does not publish.

**The trap, and the reason this property is written with a deletion rule.**
"Needs human judgement" is the cheapest possible excuse, and it is usually
wrong: of the twelve reader-found defects in that round, seven were mechanisable
and became gates the same day. So the class list is CLOSED, each row carries the
instance it came from, and **a row leaves the list the day an instrument reaches
it**, its regression case moving into that instrument. A direction claim about a
relation the deliverable DOES publish is gated, not read: model each relation's
variables with the sign of ∂outcome/∂variable, rule only on sentences that assert
a direction for one of them, and publish the out-of-range count beside the
verdicts (SSLD's own T01-round verify script `check_claim_direction_T01.py`, internal path, not shared; DIR-1). Review-when:
a project adds a sixth class without an instance — that is the list rotting back
into an excuse.
