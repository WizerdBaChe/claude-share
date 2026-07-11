# Exhaustive Depth — PRISMA-style procedure

Companion to SKILL.md; load ONLY when `depth: exhaustive`. It wraps the normal P1→P5
pipeline in PRISMA-style traceability (protocol → logged search → two-pass screening →
flow accounting). Quick/standard runs must NOT carry this overhead.

**Scope honesty (state this in every exhaustive deliverable):** this is a PRISMA-style
*traceable search and extraction* run by one agent — NOT a full human systematic review.
There are no dual independent reviewers, no formal risk-of-bias instrument, and no
meta-analysis. If the caller needs a publishable systematic review, this output is the
search/extraction backbone for one, not the review itself.

**Budget gate:** exhaustive multiplies reads (every included source gets full rubric +
retraction + 2-hop chasing). Before E1, estimate the volume (expected records screened,
expected `[full]` reads) and warn the caller per SKILL.md Resilience rules; get consent
in Mode 1 if the estimate is large. If the budget forces truncation mid-run, the flow
table (E3) records exactly where.

## E0 — Protocol first (before any search)

Write the protocol block; it ships as an appendix of the deliverable:

- **Question**: the contract `question`, decomposed (for comparative questions use a
  PICO-like split: population/system, intervention/method, comparator, outcomes).
- **Eligibility criteria**, fixed BEFORE searching:
  - Include: topic bounds, study/source types, date window, languages searched.
  - Exclude: predefined reason codes (see E2) — criteria may not be tightened after
    results are seen just to shrink the workload; any mid-run criteria change is
    logged with its reason.
- **Information sources planned**: at least 2 independent scholarly databases (e.g.
  Semantic Scholar + Crossref/OpenAlex) + 1 preprint server where the field uses one
  + citation chasing + any local corpus (prism / user PDF library). English-only
  searching must be an explicit, justified protocol decision (rubric §6 language skew).
- **Extraction targets**: the P1 target list, verbatim.

## E1 — Logged search

Every query is logged at execution time — no unlogged searches, including dead ends:

| # | date | channel | exact query / API call | filters | hits | taken to screening |
|---|---|---|---|---|---|---|

Run channels per `search-sources.md`; the degradation ladder applies, and every
substitution appears in this log. Stop per the standard stopping conditions, plus:
exhaustive requires a **saturation statement** — name the final queries that returned
nothing new before you stopped.

## E2 — Two-pass screening

Deduplicate first (same DOI/arXiv id/title+year); log the dedup count.

- **Pass 1 — title/abstract** vs eligibility criteria: include / exclude + reason code,
  one line each. Borderline → keep for pass 2.
- **Pass 2 — best available access level** (full text where accessible): final include /
  exclude + reason code. Inaccessible full text is NOT an exclusion by content — code
  it E4 and send it to `gaps`.

Reason codes (extend if needed, never merge):
`E1` off-topic / fails population bounds · `E2` wrong method/material/system ·
`E3` no extractable data for the target list · `E4` inaccessible (→ `gaps`) ·
`E5` duplicate or superseded version · `E6` fails credibility bar (Tier X: predatory /
retracted — cite the rubric check that fired).

## E3 — Flow accounting

Report the counts as a table; they must sum consistently (screened = identified −
duplicates; included = pass-2 assessed − pass-2 excluded):

| stage | count |
|---|---|
| records identified (per channel, then total) | |
| duplicates removed | |
| screened (pass 1) | |
| excluded pass 1 (per reason code) | |
| assessed (pass 2) | |
| excluded pass 2 (per reason code) | |
| **included** | |

## E4 — Extraction & verification upgrades at exhaustive depth

Relative to standard depth, the following become mandatory for EVERY included source
(not just load-bearing ones): full credibility rubric scoring, retraction check,
preprint→published check, and 2-hop backward+forward citation chasing. The rubric §6
bias/coverage check is reported as its own named section of the deliverable, not
folded into `confidence`.

## E5 — Deliverable additions

An exhaustive result contract carries, beyond the standard fields: the protocol block
(E0), the search log (E1), the screening/exclusion list with reason codes (E2), the
flow table (E3), the bias-check section (E4), and the saturation statement. `gaps`
must list every E4-coded (inaccessible) source individually.
