# audience-fit-gate

The `audience-fit` skill's first instrument. Two of its prose rules are
determinable; this makes them so, and refuses to pretend about the third.

```powershell
python afgate.py voice  <companion>              # no builder artifact in the reader's text
python afgate.py values <original> <companion>   # every number accounted for by the original
python afgate.py limits <original> <companion>   # inventory of the original's limitations (REPORT)
python afgate.py all    <original> <companion>
python afgate.py --selftest                      # two-sided calibration, 9 checks
```

Exit `2` = FAIL · `1` = WARN only · `0` = clean.

## What each check rules on

| check | rules | severity |
|---|---|---|
| `voice` | closed classes a non-builder reader cannot act on: a bare `<n> PASS`, a file path, a sha, a run id, a gate/invariant id | **FAIL** in the reader's main text |
| `voice` | builder vocabulary (`stdout`, `schema`, `commit`, `閘`, …) | WARN — a `power_user` audience legitimately reads some of these |
| `values` | a number in the companion that no number in the canonical original explains, under identity or a **named** transform | **FAIL** — "invent nothing", made checkable |
| `limits` | the original's limitation lines and which have no lexical counterpart | **reports, rules on nothing** |

## Two scope facts, both measured

**The delivery apparatus is not the reader's text.** audience-fit *mandates* a
provenance block (canonical link, audience, as-of anchor) and, for an A1
re-render, the aggregation mapping table. Both legitimately carry paths, shas
and lesson ids — they address the auditor who must trace the companion back.
The gate's first run against an already-accepted owner view
(an owner view, user gate PASS 2026-08-31) raised
6 FAILs, every one inside those two regions. So `voice` splits the text at the
first line naming the apparatus, closes only over the main text, and **prints
both zone sizes** — a reader paragraph that drifts below the marker would
otherwise be exempted silently. `--no-apparatus` disables the split.

**`values` is a SCREEN, not a proof, and says so in its own output.** Only
tokens with 3+ significant digits are certified; 1–2 digit tokens are counting
words, thresholds and round figures, and the output states how many fell in
each class rather than hiding the weaker half. audience-fit *transforms*
numbers on purpose (`1.336×` becomes `比基準高 33.6%`), so a companion number is
accounted for by identity or by one of ten named transforms — the transform is
printed beside the match. `--allow VALUE=REASON` carries a legitimate exception
inline.

## Calibration

`--selftest` builds four fixtures — a canonical original plus a clean, an
invented-number and a leaky companion — and requires nine separations,
including "`limits` never returns FAIL" and "33.6% is recognised as a named
transform of 1.336". Artifact-level baseline: the three accepted owner views in
the source environment's diagram-authoring outputs return 0 FAIL.

Borrowed 2026-09-10 from SSLD's audience-pack gates (INV17Gate,
ParityGate) and a record-numbers check from the same project.
ParityGate proper does not transfer — an audience-fit companion is a rewrite,
not a copy — but its question does, asked of the parts that must not change.

Review-when: audience-fit stops mandating the provenance block or the
aggregation table (the apparatus zone then has no basis), or a companion class
appears whose numbers are legitimately new (then `values` needs a declared
source beyond the original).

**If `values` ever false-accepts a number a human then catches, that is not just
a bug here — it is the firing trigger for the NumberRef extraction**
(a deferral note in the source environment, deferred 2026-09-10 for
want of a second customer). This check matches value to value across two prose
documents; the deferred one resolves a value to the FIELD that produced it, and
a false accept is the evidence that the screen is not enough. Record the case in
that file before fixing anything here.
