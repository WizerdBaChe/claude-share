# Credibility Rubric — source-quality scoring for P3 triage

Companion to SKILL.md P3. Purpose: turn the coarse ordering in P3 into checkable
criteria. Score sources BEFORE extraction effort is spent; a low-credibility source can
still be included, but its tier travels with it into the deliverable's `quality` /
`confidence` fields.

External-service facts below (Retraction Watch access, list statuses) verified by web
search on **2026-07-07**; re-verify on unexpected behavior.

## 1. Venue tier (base score)

| Tier | Venue type | Handling |
|---|---|---|
| A | Established peer-reviewed journal / top conference in the field; established textbook (see §5) | default trust; still run §3–§4 checks for load-bearing claims |
| B | Solid peer-reviewed venue, lower profile; newer OA journal listed in DOAJ | usable; prefer an A-tier corroboration for load-bearing claims |
| C | Preprint (arXiv, bioRxiv…), thesis, technical report, standards-body draft | usable with the §2 published-version check; label as preprint in the source list |
| D | Non-reviewed web source (blog, vendor whitepaper, Wikipedia) | never load-bearing on its own; use only as a pointer to A–C sources, or cite explicitly as "secondary web source" when the caller asks about practice/tooling rather than science |
| X | Suspected predatory venue (§4), retracted work (§3) | exclude; if the caller explicitly asked about it, report WITH the flag, never silently include |

Venue tier is about the VENUE's process, not the paper's correctness — a Tier A paper
can still be wrong; conflicts found in P4 outrank venue tier.

## 2. Work-level modifiers

Apply to the base tier:

- **Citation context, not citation count.** Raw counts inflate with field size and age.
  What matters: is the paper cited FOR the claim you're extracting, and are those
  citations supportive, corrective, or refuting? (Semantic Scholar citation contexts /
  "highly influential citations" help here.) A heavily cited-as-refuted paper is a
  negative signal dressed as a positive one.
- **Preprint → published check (mandatory for every Tier C source).** Query Semantic
  Scholar `externalIds` / Crossref for a journal version. If published: cite the
  published version (it may differ from the preprint — note the version you actually
  read). If a preprint has been public for years with no publication and visible
  citations, treat claims as unreplicated until corroborated.
- **Age vs field speed.** For fast-moving topics, a 10-year-old measurement may be
  superseded — check forward citations (search-sources.md) before presenting old
  values as current. For canonical theory, age is fine (often a positive).
- **Independence.** Two papers from the same group/apparatus are ONE line of evidence
  for `confidence` counting, not two.

## 3. Retraction check (mandatory for load-bearing sources)

The Retraction Watch database is free via Crossref (acquired 2023; >63k entries,
updated daily as of verification).

Procedure per DOI: fetch `api.crossref.org/works/<doi>` and inspect `update-to` /
`relation` fields for retraction, correction, or expression-of-concern notices; or
search the Retraction Watch database directly (no registration needed). No DOI (old
book chapters, reports): WebSearch `"<title>" retraction` as a best-effort check.

- Retracted → Tier X. If it must be mentioned (caller asked about it, or it's the
  origin of a still-circulating claim), state the retraction with its notice locator.
- Correction/erratum → usable, but extract from the CORRECTED version and note the
  correction in the source list.
- Expression of concern → usable with the concern stated in `confidence`.

Run this check for: every source whose claim is load-bearing in the deliverable, and
every source that a conflict resolution hinges on. Skipping it for background-only
sources at `quick` depth is acceptable — say so in `search_trail`.

## 4. Predatory-venue screening

No single authoritative blacklist exists. Beall's List has been unmaintained since
2017 (community mirrors exist — treat as one dated input, never sufficient alone);
Cabells lists are paywalled. Use converging signals:

Positive (whitelist-side) checks, any one is strong:
- Listed in DOAJ (reviewed OA whitelist), Scopus, or Web of Science.
- Publisher is a COPE/OASPA member.
- The venue routinely publishes the field's recognizable groups.

Red flags (≥2 → treat as Tier X pending further evidence):
- Not indexed anywhere above despite years of operation.
- Promised review turnaround of days; prominent APC with no visible review process.
- Editorial board members unverifiable or unaware (spot-check one name).
- Journal title mimics an established journal's title.
- Scope is absurdly broad ("International Journal of Science and Engineering
  Research"-pattern).

When uncertain, keep the source at Tier D handling (pointer, not evidence) and record
the doubt in `confidence` rather than deciding the venue's reputation yourself.

## 5. Textbook credibility & edition judgment

**Canonical-text discovery** ("the standard reference for X"): WebSearch university
syllabi and qualifying-exam reading lists (2–3 independent programs naming the same
book is a strong signal); check how often papers in the field cite the book for
fundamentals; review articles' introductions usually cite the canonical text. Record
HOW canonicity was established (one line in the source list) — "widely used textbook"
without evidence is an unsupported claim like any other.

**Edition rules:**
- Locate and cite the edition you actually read — page/section locators do not
  transfer across editions (see search-sources.md ISBN resolution).
- Prefer the latest edition for state-of-the-art chapters and pedagogy; an older
  edition is acceptable for unchanged fundamentals, but check the newer edition's
  changelog/preface if the topic might have moved (e.g. a field that had a
  paradigm-relevant result since the old edition).
- If only an old edition is accessible, tag the risk: "3rd ed. (2008); 4th ed. (2019)
  exists but was not accessible — sections on <topic> may be outdated" → `gaps`.
- Beware "international/adapted editions" with shuffled chapter numbers; identify by
  ISBN, not title alone.

## 6. Bias & coverage-balance check (set-level; run before P5 at standard/exhaustive)

§1–§5 score each source alone; this check looks at the included SET. Any hit goes to
`confidence`/`gaps`; if the affected claim is load-bearing, run ONE targeted
counter-search before synthesis:

- **Citation bubble.** If every source arrived via citation chasing from one seed, the
  set may be a single citing lineage. Test: did at least one included source arrive
  from an independent route (fresh keyword query, different database)? If not, run one
  independent-seed query before claiming consensus.
- **Group/apparatus concentration.** §2 Independence per pair; here per set — if most
  load-bearing values trace to ≤2 research groups, state that in `confidence`.
- **Geographic/language skew.** English-only searching on a topic with strong
  non-English activity (see search-sources.md §Non-English) → record the restriction
  as a `gaps` entry rather than presenting coverage as complete.
- **Positive-result skew.** Published values cluster around successes; null results and
  failed replications are undercited. For contested claims, explicitly search for
  contradicting/replication work (forward chase with "comment", "reply",
  "replication" terms) before reporting one-sided support.

## 7. Scoring worked example (fictional)

> Candidate: "Lee 2021, J. Placeholder Optics" — needed for a load-bearing loss value.
> - Venue: established journal → Tier A.
> - Citations: 40 citations; spot-checked 3 via citation contexts — one is a
>   correction-style comment (Kim 2022) disputing the calibration → modifier: negative.
> - Retraction check: Crossref `update-to` shows an erratum (2022) revising Table 1
>   values → extract from the erratum, not the original table.
> - Net: include at Tier A with notes; the Kim 2022 dispute goes to `confidence` as a
>   conflict; the extracted value cites "(Lee 2021, Table 1 as corrected by 2022
>   erratum) [full]".
