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

Live instances: rung 2 in the source environment's `cross-index` tool test
suite (source-only, does not ship here); rung 4 in its `lean-verify` tool
(status line `LEAN-VERIFY … severity=WARN`; source-only, does not ship here).
