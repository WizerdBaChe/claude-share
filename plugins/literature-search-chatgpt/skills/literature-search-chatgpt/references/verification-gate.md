# Verification gate — proving the deliverable against the documents

Companion to SKILL.md P4→P5. This is the step between "extraction is written"
and "deliverable ships". Tool: `../verify/citecheck.py`.

Everything the skill did before this file was **self-report**: the same model
that might fabricate a citation also decided whether the citation was
fabricated. That is not a check — it is the same judgement twice.

## The three failure modes, ranked by how hard they are to see

| # | Failure | Visible to a reader? | Caught by | Evidence it is real |
|---|---|---|---|---|
| F1 | Invented identifier — DOI/arXiv/page that does not exist | only if they click | identifier resolution (already in P2) | Tow Center/CJR 2025: across 1,600 queries, 8 AI search products cited wrongly >60% of the time; Gemini and Grok 3 returned more fabricated than correct links |
| F2 | **Real source, cited for something it does not say** | **no** | support-span check (this gate) | ALCE (arXiv:2305.14627): on ELI5 even the best systems "lack complete citation support 50% of the time" |
| F3 | Real source, real support, but the number lost its conditions | only to a specialist | P4 exactness rule + locator | SKILL.md failure mode #4 |

**F2 is the one to build for.** It survives every check the skill had, it is
invisible in the finished document, and it is actively *rewarded*: Search Arena
(arXiv:2506.05334, ICLR 2026, n=24,069 conversations) found people rate answers
higher for carrying more citations **even when the cited content does not
support the attributed claim**. Citation density reads as rigor. So a
deliverable that "looks well-cited" is evidence of nothing, including to its
own author.

## The move that makes F2 checkable

Whether a source *supports* a claim needs an entailment judgement, which a
script cannot make. But it becomes checkable if the writer must name the exact
span it relies on:

> A script cannot judge support. A script CAN check that the quoted span exists
> verbatim in the retrieved text.

That converts "trust me, it says so" into a falsifiable statement. A
reconstructed-from-memory quote fails immediately, with no model in the loop.
The residual judgement — does this real span actually entail this claim — stays
human, but the ledger prints claim and span side by side, so it takes seconds
instead of a re-read.

## The evidence ledger

One JSONL line per load-bearing claim, written **before** the gate runs:

```json
{"claim_id":"C1","claim":"Single-crystal Ag films reach L_spp = 200 um at 780 nm.",
 "source_id":"10.1021/nl803811g","cite_as":"Nagpal 2009","expect_year":2009,
 "locator":"Fig. 3","access_tag":"full",
 "support_span":"propagation length of 200 um","source_text":"sources/nagpal2009.txt"}
```

Two rules about the ledger itself, both learned the hard way elsewhere:

- **Persist before the gate runs.** The retrieved `source_text` and the ledger
  are written first, then checked. A gate must never be able to destroy the
  evidence it rejects — otherwise a failed run leaves nothing to diagnose and
  the re-run pays for the same fetches twice. They live in the run folder
  `<home>/<run_id>/` (`ledger.jsonl` beside `sources/`), which is the path this
  script is pointed at; its `--json` output is stored there as `citecheck.json`
  (`feedback-loop.md`, loop INV-1).
- **The ledger is not the deliverable.** It is the audit trail behind it. It
  stays behind the deliverable — persisted with the run (loop INV-1), never
  pasted into it (INV-2) — unless the caller asks for it.

## What runs, and what it may rule on

`python ../verify/citecheck.py ledger.jsonl`

**FAIL — determinable and closed:**
identifier does not resolve · resolved metadata contradicts `cite_as`
(author surname absent from the author list, or year off by >1) · `support_span`
absent from the stored text · no locator · access tag above what was retrieved.

**WARN — undeterminable here, forwarded rather than vetoed:**
no stored text for the source · network down (`--offline`) ·
`[abstract]`/`[secondary]` rows, where span checking is out of scope by
definition.

**Never ruled on:** whether an existing span actually entails the claim. The
gate says nothing it cannot demonstrate — a check that guesses is worse than no
check, because its silence gets trusted.

Calibration is two-sided and shipped: `citecheck.py --selftest` runs 4 must-pass
and 7 must-fail cases. The must-pass side is load-bearing — a gate that rejects
everything scores 100% on a one-sided test. It distinguishes typography (PDF
hyphenation, ligatures, curly quotes, collapsed whitespace — must pass) from
wording (`µm` where the source wrote `um`, an added hedge — must fail). It does
not guess intent.

## When to run it

**Claim kind first, depth second.** The earlier version scoped the ledger by depth
alone, and that put the hole in the worst possible place: `quick` skipped the file, and
`quick` is what a single parameter lookup runs at — so the one number a user was most
likely to copy into their own work was the one claim in the whole pipeline that nothing
checked. Depth measures how much was searched; it says nothing about how load-bearing
the answer is. A one-source answer is not a low-stakes answer, it is a *thin* one.

| Trigger | Ledger scope | Overrides depth? |
|---|---|---|
| **Numeric claim** — any value the caller could act on, copy, or compute with | one row, always | **yes**, `quick` included |
| **Disputed claim** — sources conflict, or the claim is the one the caller is deciding on | one row per position | **yes**, `quick` included |
| `quick`, everything else | skip the file; still resolve every identifier before citing (P2 rule, unchanged) | — |
| `standard` | adds all load-bearing claims | — |
| `exhaustive` | every extracted item; the ledger is part of the PRISMA record | — |
| any depth, Mode 2 | a `[full]`/`[partial]` claim returned to a caller as fact gets a row — a downstream skill cannot re-check what it did not retrieve | yes |

**Why narrowing rather than softening.** The affordability worry is real and was
recorded before this change (`literature-search-extract-FUTURE-WORK.md` B4: an
unaffordable gate gets skipped silently, and silence still reads as a pass). The answer
is to shrink the *set of claims* the gate covers, never the *strength* of what it checks
on them. A numeric-and-disputed-only ledger at `quick` depth is typically one to three
rows — cheap enough that skipping it saves nothing worth having.

**Still measure it.** B4 stays open until a real `standard`-depth run reports the actual
cost of writing rows. If rows-per-run turns out unaffordable even under this narrowing,
the next move is still narrowing (numeric only), not weakening the span check.

## Reading the result

A FAIL is not a style note. That claim may not ship as cited. The repairs, in
order of what is usually true:

1. **Span not found** → most often the quote was rebuilt from memory. Go back to
   the stored text, find what it actually says, and rewrite the claim to match
   it. If the text does not support the claim at all, the claim is deleted and
   the target becomes a `gaps` entry. Deleting a claim is a valid outcome.
2. **Identifier does not resolve** → do not "fix" it by finding a nearby real
   DOI. Re-locate the source from scratch, or drop it.
3. **Metadata conflict** → the wrong source got attached to the right claim.
   Check whether other rows share the mistake.
4. **Tagged `[full]`, tiny stored text** → the tag was aspirational; downgrade
   it and re-check what the claim rests on.

## The same discipline, turned on this skill's own documents

P4.5 stops an unverified number reaching a deliverable. Nothing was stopping one
reaching this skill's **own** files — and one did:
`literature-search-extract-FUTURE-WORK.md` said
`SKILL.md` was "261 lines", true on 2026-07-12, false from 2026-07-19, unnoticed
for five weeks, then used as a baseline for arithmetic that produced a second
wrong number. A gate that only faces outward is half a gate.

```
python ../verify/staleclaim.py            # FAIL = a line-count claim that is now false
python ../verify/staleclaim.py --selftest # 8 cases, 5 must-pass / 3 must-fail
```

**Coverage is narrow on purpose, and stating the limit is part of using it.** It
re-measures only *line counts of named files*, because that is the one claim
shape a script can settle with no judgement. `116 PDFs`, `155 attachments`,
`47% from the last three years` are not re-derivable from the text, so they get
a WARN at most — for those the discipline is the convention, not the checker:
**a quantity is written as value + measurement date + the command to re-take it,
and one without a date is treated as expired.**

**Why the calibration is not decoration here.** Version 1 of that checker passed
every synthetic case and *missed the real bug*, because a bound word five
characters away from a measurement ("261 lines, over the 250 line cap") vouched
for it. It was only caught by replaying the actual five-week-old file from git
and demanding a FAIL. Both shapes are now permanent regression fixtures. The
lesson generalises: **a green self-test on cases you invented is not evidence
the instrument works on the case you built it for** — replay a real failure, or
you have tested your imagination.

## Set-level checks the script cannot do

Run these by hand before P5, and state the result:

- **Conflicts preserved?** Two sources disagreeing is a finding. The ledger
  holds both rows; `confidence` reports both positions with locators. Never
  average, never quietly pick one.
- **Citation-count illusion.** Search Arena's finding applies to the author too:
  more rows do not mean better support. One `[full]` row with a verified span
  beats five `[abstract]` rows.
- **Single-cluster evidence.** Run `credibility-rubric.md` §6 — one group, one
  citation bubble, one language is not consensus.
- **Retrieval currency.** For any claim whose source can change under the
  citation (legal status, a live database record, a web page, a moving standard),
  record the retrieval date. A stable DOI'd article needs none.
