# Search Sources — per-channel strategies, identifier resolution, citation chasing

Companion to SKILL.md P2 — applies to the **discovery** and **mixed** paths only; on
the source-provided path do not expand the literature set beyond the supplied sources
(see SKILL.md P2 routing). Channel facts below (endpoints, auth, limits) are volatile:
base verified **2026-07-07**, OpenAlex and Semantic Scholar re-verified **2026-08-26**,
the §Source classes beyond journals and books channels verified **2026-09-03**.
If a channel behaves differently than described (404s, auth walls, new limits),
re-verify with a web search before concluding the channel is unusable, and update this
file.

**review-when** (the events that invalidate this file, not a calendar): a channel
returns 401/403/409 where this file says keyless · a rate limit or quota quoted here is
contradicted by a live response header · a channel is used for the first time in >60
days · a connector in `../connectors/registry.json` changes status. Any of those is a
re-verify trigger for **that channel only** — the whole file does not rot at once, and
re-verifying all of it on a schedule is how a currency rule turns into a chore nobody
runs. Stamp the date beside the fact you changed, as the two 2026-08-26 entries do.

## Tool routing (read first)

Two fundamentally different tool classes serve P2:

1. **Local-corpus tools** — they rank, relate, and export sources the user has ALREADY
   collected. They do NOT search the web and cannot discover anything outside the
   corpus. Whichever one is live, the routing rules are the same, and an empty local
   result never means "literature not found".
2. **WebSearch / WebFetch** — discovery of new sources on the open web, plus direct
   fetching of scholarly API endpoints (Crossref, OpenAlex, arXiv export — these return
   JSON/XML that WebFetch can read).

> **`prism` is RETIRED (user ruling 2026-08-27)** — the MCP server is off and the system
> behind it is being rebuilt. Do not route to it, do not probe for it, and do not record
> its absence in `gaps`: an absent retired channel costs no coverage. The prism-specific
> tool table that used to live here has moved to the tombstone in
> `../connectors/registry.json`, so a reader who meets the name in an older
> `search_trail` can find out what happened to it. If the rebuilt system returns under a
> new name, register it as a NEW connector. What it taught the slot is kept below.

**Routing rule:** consult `../connectors/registry.json` for a `local_corpus` connector
with status `live`/`available`, and use it ONLY when the question plausibly concerns
material the user has curated before. If one matches, rank inside it first; web search
then fills gaps and finds newer work. If none is live — the situation as of 2026-08-27,
with `local_pdf_library` awaiting a path and `zotero_local` unbuilt — go straight to
WebSearch. Never treat an empty or absent local corpus as "literature not found".

### What survives prism — the rules, which were never prism-specific

The per-tool table that used to sit here is gone with the server. These four rules were
written for prism but belong to the SLOT, so they bind whatever fills it next (Zotero, a
PDF folder, the rebuilt system):

- **Rank inside the corpus first, then let web search fill gaps and find newer work.**
  A curated corpus is a relevance shortcut, never a coverage claim.
- **A digest or excerpt is `[partial]` at best.** To claim `[full]`, fetch and read the
  actual document via its identifier. This is the rule that stops a tidy corpus summary
  from being mistaken for having read the paper.
- **Fall back to WebSearch when** nothing matches the question, the corpus is stale
  relative to the question's recency needs, ranking returns low-relevance items, or the
  extraction targets need full text the corpus cannot provide.
- **Log in `search_trail` whether a local corpus was used, skipped, or unavailable** —
  with one exception added 2026-08-27: a RETIRED channel is not "unavailable", it is
  gone, and listing it every run trains the reader to skim the trail.

## Per-channel strategies (web)

General pattern for all channels: reach them through WebSearch (site-scoped queries)
and WebFetch (API endpoints or landing pages). This skill runs interactively at low
request volume — rate limits below matter mainly as "don't loop fetches" guidance.

### Google Scholar
- No official API (long-standing policy); automated scraping is blocked. Use it via
  WebSearch queries mentioning the topic + "scholar" or by fetching a known result URL —
  expect this to be unreliable; prefer Semantic Scholar/OpenAlex for programmatic needs.
- Best use: quick citation-count sanity checks and finding which venues host a topic.

### Semantic Scholar (papers, citation graph)
- API: `api.semanticscholar.org/graph/v1/` — works unauthenticated. Re-verified
  2026-08-26 against the official tutorial: unauthenticated callers **share a single
  key**, so the effective rate depends on everyone else's traffic and is throttled under
  load; an individual free key buys a **guaranteed 1 request/s across all endpoints**.
  The key is therefore a *floor*, not a raise — do not treat keyless as equivalent under
  load. Fine for this skill's volumes via WebFetch either way.
- Strengths: citation contexts, TLDRs, `references`/`citations` endpoints — the
  cheapest programmatic backward/forward chasing.
- Query strategy: `/paper/search?query=...` with field list
  (`fields=title,year,abstract,externalIds,citationCount`); then
  `/paper/{DOI|arXiv:id}/references` and `/citations` for chasing.

### Crossref (DOI metadata authority)
- API: `api.crossref.org/works/...` — free, no key. Rate limits were revised
  2025-12-01; "polite pool" (append `mailto=` parameter) gets more reliable service.
  Current limits are advertised per-response in `x-rate-limit-*` headers.
- Use for: resolving/verifying DOIs (failure-mode-#1 check), bibliographic metadata,
  `query.bibliographic=` fuzzy lookup from a citation string.
- NOT full text and often no abstract — metadata authority only.

### OpenAlex (broad scholarly graph)
- API: `api.openalex.org` — **requires an API key since 2026-02-13**. Re-verified
  2026-08-26 from the openalex-users announcement: keyed = 100,000 credits/day
  (singleton 1, list 10, search 100–1,000); **keyless = 100 credits/day for testing,
  then 409**. The **polite pool and the `mailto=` parameter were eliminated** in the
  same change — do not send one, and do not treat OpenAlex as a keyless channel.
  Without a key, fall back to Semantic Scholar/Crossref and log it in `gaps`.
- **Caution when re-verifying:** `github.com/ourresearch/openalex-docs` was archived
  2026-07-23 and still says "You don't need an API key" — a stale primary-looking
  source that contradicts the live one. Prefer the announcement/help centre, and treat
  an archived doc repo as secondary.
- Strengths: ~250M works, concepts/venues/authors as first-class entities, good for
  "who works on X" and coverage checks.

### arXiv (physics/math/CS preprints)
- API: `export.arxiv.org/api/query` — free, **no key and no account** (re-verified
  2026-08-27 against arXiv's Terms of Use for APIs; an arXiv login unlocks nothing here).
  Pacing is a ToU requirement, not advice: **1 request per 3 s, ONE connection at a
  time**. 429s have been reported since ~2026-02-25 even against clients that pace
  correctly, so back off once, retry once, then degrade — never loop.
- This skill's own scripts send a contact-bearing User-Agent to arXiv (registry entry
  `arxiv`, approved 2026-08-27). That consent is **arXiv-only**: Crossref's polite pool
  and Unpaywall were declined the same day, so no contact goes to them. WebFetch sends
  its own User-Agent and is anonymous to arXiv regardless.
- Query strategy: `search_query=all:"exact phrase"+AND+cat:physics.optics`-style field
  and category filters; resolve known IDs directly via `abs/<id>`.
- Always check whether an arXiv preprint was later published (Crossref/Semantic
  Scholar `externalIds`) — cite the published version when it exists, note the
  preprint-vs-published status in the source list.

### PubMed (biomedical)
- API: NCBI E-utilities (`eutils.ncbi.nlm.nih.gov`) — free; 3 requests/s keyless,
  10/s with a free key. `esearch` → PMIDs → `efetch`/`esummary`.
- Query strategy: use MeSH terms when the user's vocabulary is clinical
  (`"term"[MeSH]`), else `[tiab]` field tags. PubMed Central (PMC) subset = free full
  text → those sources can be `[full]`.

### IEEE Xplore (EE/CS/photonics)
- API exists but requires a registered developer account + manually issued key —
  assume UNAVAILABLE **unless `ieee_xplore` is `live` in `../connectors/registry.json`**;
  a key would arrive through that connector, never through the conversation. Note the
  two-stage trap recorded there: a key alone buys metadata + abstracts, and `[full]`
  additionally needs the subscription behind it — the probe must report which of the two
  is actually live, because the failure is otherwise silent. Use instead: WebSearch scoped
  `site:ieeexplore.ieee.org`, and extract from the public landing page (abstract,
  figures list, references are visible) → typically `[abstract]` or `[partial]`;
  full text is usually paywalled → paywall handling per P3.

### Publisher previews (Springer / Elsevier-ScienceDirect / Wiley)
- Treat as landing-page channels, not APIs (their APIs require institutional keys).
- What is legally visible without access: abstract, keywords, section headings,
  figure thumbnails/captions, reference list, and sometimes a free-preview first page.
  Figure captions and reference lists are underrated extraction targets at
  `[partial]` level.
- Springer Link book chapters often expose the first ~2 pages; note exactly which
  pages were visible in the locator.

### Google Books (textbooks)
- API: `www.googleapis.com/books/v1/volumes?q=...` — public volume search works
  without a key; `filter=partial` restricts to previewable books. Preview
  availability is geo-dependent (some previews US-only).
- Query strategy: `intitle:` and `isbn:` operators; use the API/site to locate the
  right chapter via search-inside-the-book, then read the preview pages → `[partial]`
  with page-range locator.
- For canonical-text discovery ("standard textbook for X"): WebSearch for syllabi and
  "recommended texts" threads, then verify the book's standing via citation counts of
  the book itself (Google Scholar/Semantic Scholar index books).

## Source classes beyond journals and books

Added 2026-09-03. These classes were absent from this file and from
`../connectors/registry.json` — not declined, *never considered* — which meant a
question whose answer lives in a handbook or an agency report could only ever come back
"not found in searched sources". A gap report that cannot name the right *kind* of
source is honest and useless. Credibility handling for the first two is
`credibility-rubric.md` §5b (Tier R) and §5c (Tier M).

### Reference data compilations (material constants, thermophysical data)

**The default home of a "what is the literature value of X" question in physical
science** — more often than a paper is. Channels are landing pages, not APIs; treat
them like publisher pages and read the entry.

- **NIST**: Chemistry WebBook and the Standard Reference Data collections
  (`webbook.nist.gov`, `nist.gov/srd`).
- **refractiveindex.info** — optical constants (n, k) by material and reference; the
  entry names the source dataset it plots, which is what makes cite-through possible.
- **Print handbooks**: CRC Handbook of Chemistry and Physics; Palik, *Handbook of
  Optical Constants of Solids*. Locate the edition via ISBN resolution (§Identifier
  resolution) — editions revise values.

**Extraction rule (this is the whole point):** take the value AND the primary source the
compilation names, then **cite the primary source, recording the compilation as the
route** — `(Johnson & Christy 1972, Table I; via refractiveindex.info, retrieved
<date>)`. A compilation is a high-quality index; it is not the measurement. Record the
retrieval date (online compilations change) and whether the row is measured or
interpolated. Full rules: `credibility-rubric.md` §5b.

### Agency / government technical reports

Free full text, peer-review status varies (usually internally reviewed, not journal
peer review → Tier C unless the report itself states otherwise).

- **NASA NTRS** — API root `ntrs.nasa.gov/api`, `POST /citations/search`, then
  `/citations/{id}` and `/citations/{id}/downloads` for the PDF; `page_size` 1–100,
  1-based `page`. No key seen. *Verified 2026-09-03 (search); NASA's own OpenAPI PDF is
  dated 2021-04-26 — treat parameter details as first-use-verify.*
- **DOE OSTI** — docs `www.osti.gov/api/v1/docs`, records endpoint
  `www.osti.gov/api/v1/records`. No API key or auth mentioned for search; no rate limit
  documented; records carry a `links` array where `"rel": "fulltext"` gives the document
  URL. Covers reports, journal articles, data, software, patents, conference papers.
  *Verified 2026-09-03 by fetching the docs page itself.*

Both yield `[full]` when a document link resolves. Because no rate limit is documented,
apply the standing rule anyway: do not loop fetches.

### Theses and dissertations

`credibility-rubric.md` Tier C already named theses; there was no channel. A thesis is
often the only place a method is described in reproducible detail — the chapter behind a
terse Methods section.

- **Taiwan — 臺灣博碩士論文知識加值系統 (NDLTD Taiwan)**, `ndltd.ncl.edu.tw`. National
  Central Library, Open Access basis; bibliographic + abstract search is free and needs
  no account. **Full text only where the author authorised it**, and downloading an
  authorised thesis requires member registration — so the honest default tag is
  `[abstract]`, rising to `[full]` only for an actually-retrieved authorised PDF.
  *Verified 2026-09-03.*
- **Elsewhere**: the institutional repository is usually the free full text; find it via
  OpenAlex/Semantic Scholar or a site-scoped WebSearch on the university domain.
  ProQuest Dissertations is paywalled — landing-page channel like IEEE Xplore.

### Datasets and research software

Increasingly where the actual number lives, especially when a paper's figure has
deposited source data.

- **Zenodo** — REST API over published records. Reading works without a token, but a
  token raises the limit from **60 to 100 requests/hour**; pass it as
  `Authorization: Bearer <token>`, not as a URL parameter. *Verified 2026-09-03.*
  No token is registered for this skill, so treat 60/hour as the ceiling.
- **Figshare**, and **Software Heritage** for code that has outlived its repo.
- A dataset has its own DOI: resolve and cite it as a source in its own right, with the
  file and column/field as the locator. Do not cite the paper for a number you took from
  its deposited data — cite the deposit, and note the paper it belongs to.

### Supplementary material (not a channel — a rule)

`extraction-playbook.md` §2 says to check Supplementary before declaring a reproduction
gap, and never said how to get it. SI usually sits behind its own link on the article
landing page, frequently as a separate PDF/XLSX, and is often open even when the article
is not. Procedure: fetch the landing page, take the SI links from it, fetch those; if
WebFetch cannot render the landing page, that is exactly ladder rung 3b (render it).
Cite SI with its own locator (`Suppl. S1`, `Suppl. Table S3`) — never fold an SI number
into a main-text table citation.

## Local PDF library (user-supplied corpus)

When the user points to a folder of paper PDFs they already have:

- **Inventory before extraction**: Glob `**/*.pdf`, then Read page 1 (+ metadata) of
  each candidate to identify title/authors/DOI, building a small path↔identifier index.
  Extraction then targets only the papers the P1 target list needs.
- **Access level**: `[full]` — the whole PDF is readable (paged, ≤20 pages/request;
  navigate by section using page 1's table of contents or the section map in P1).
- **Still verify online**: a local PDF proves content, not bibliographic correctness —
  resolve the DOI via Crossref to confirm citation fields and run the retraction check;
  if the PDF is a preprint, run the preprint→published check (rubric §2) and cite the
  published version.
- **Collection bias**: a personal library reflects its owner's reading history. At
  `standard`/`exhaustive` depth, complement it with web channels, and mark in
  `search_trail` which claims rest ONLY on the local library (rubric §6 bubble check).
- **With a corpus tool over the same folder**: if the collection is also indexed by a
  live `local_corpus` connector, rank/relate there first, then Read the underlying PDF
  for `[full]`-level extraction — a digest alone stays `[partial]`.

### "Password-protected" is usually a false refusal (SKILL.md P3 points here)

The Read tool refuses some PDFs as password-protected that are not encrypted at all — a
permissions flag alone is enough to make readers refuse, and rewriting the file via
pypdf does not clear the refusal. Probe before believing it:

- `fitz.open(path)` then check `needs_pass` / `is_encrypted`. Both false → the refusal
  was spurious and the file is readable.
- Working recipe (measured on SSLD, 2026-08-31): pymupdf `get_text()` per page **plus**
  `get_pixmap(dpi≈110)` page renders read as images — recovers full text AND figure
  dimensions, so the source is genuinely `[full]`, not `[partial]`.
- `needs_pass` true → it really is user-password-protected. That one goes back to the
  user; do not guess passwords and do not downgrade silently — it is a `gaps` entry.

## Degradation ladder & cost transparency

When a planned channel fails (auth wall, 429/409 bursts, outage), substitute down this
ladder instead of aborting P2, and record every substitution in `search_trail`:

0. Registered connectors (`../connectors/registry.json`) — authoritative primary
   documents held locally or behind the user's own key. A connector that probes FAIL
   drops out of the ladder for this run; say which one and what class of source went
   with it (`connectors.md`) →
1. Keyed/limited APIs (OpenAlex keyed, Semantic Scholar keyed tier) →
2. Free unkeyed APIs (Semantic Scholar shared tier, Crossref polite pool, arXiv export,
   PubMed E-utilities) →
3. WebSearch site-scoped queries + landing-page WebFetch (always available) →
3b. **Extraction fallback** — when WebFetch cannot render a needed page (JS-heavy,
   anti-bot, blocked publisher page, or a plain **403** — measured 2026-08-26 on
   perplexity.ai), render it before downgrading the access tag. In Claude Code the
   binding is a browser MCP: `playwright-headless` first, `claude-in-chrome` only when
   the page genuinely needs the user's logged-in session (say so in `search_trail` —
   it spends their authenticated identity). Elsewhere: Tavily extract, Exa contents, or
   a self-hosted Firecrawl instance. If none is available, keep the item at
   `[abstract]`/`[partial]` honestly — never reconstruct content. →
4. A live `local_corpus` connector alone (coverage limited to what was ingested — flag
   in `gaps`). **As of 2026-08-27 there is none**, so the ladder currently bottoms out
   at rung 3: if web search and rendering both fail, the honest output is "not found in
   searched sources", not a further fallback.

Rules:
- Never retry-loop a rate-limited endpoint: back off once, retry once, then degrade.
- A degraded run is a valid run — state which channels were skipped and what coverage
  that may cost (feeds `gaps`), instead of failing the whole request.
- **Cost transparency:** when a run spends a personal resource — an OpenAlex key's
  credits, a keyed Semantic Scholar tier, or the Crossref polite pool (which sends the
  user's `mailto`) — name it in `search_trail` so the caller knows what was consumed.

### General-web search/extract providers (facts verified 2026-07-12)

Mostly relevant in environments WITHOUT built-in WebSearch/WebFetch (see
`references/portability.md`); inside Claude Code the built-ins cost no quota and stay
the default search layer. Quotas are volatile — re-verify before relying on them.

| Provider | Search | Extract | Free tier (2026-07) | Caveats |
|---|---|---|---|---|
| Tavily | yes | yes | 1,000 credits/mo, no card | primary extraction fallback |
| Exa | yes | yes (`contents`, ~$1/1k pages) | $10 one-time; $7/mo credits ONLY with card on file | cheap extraction, card-gated |
| Brave Search API | yes | no | free 2k/mo tier KILLED 2026-02 → $5/mo metered (~1k queries), card required | legacy free users grandfathered |
| DDGS (python lib) | yes | no | unkeyed | **best-effort unofficial scraper, NOT an API**: IP blocks well before ~30 req/min, needs proxies at volume, ToS-gray — never plan it as "unlimited" |
| SearXNG | yes | no | self-hosted, unlimited | infra to run; search only |
| Firecrawl | yes | yes | AGPL-3.0 self-host (scrape/crawl/extract core) | managed-only surfaces excluded; local-infra slot |

Keyed/personal-resource usage from any of these goes into `search_trail` per the cost
transparency rule above.

## Non-English literature

When the topic has significant non-English literature (Chinese, Japanese, German…) or
the caller names non-English sources (facts below verified 2026-07-10):

- **Query bilingually**: run the key queries in English AND the source language
  (translate core terms; keep established romanizations). English-only querying
  systematically misses regional venues — log the language-coverage decision in
  `search_trail`; an English-only run on such a topic is a `gaps` entry.
- **Channels**: Google Scholar indexes most languages. CNKI (Chinese): metadata +
  abstracts free, full text paywalled → landing-page channel like IEEE Xplore, expect
  `[abstract]`/`[partial]`. J-STAGE (Japanese): largely open access full text; CiNii
  Research is the discovery/linking layer over it → `[full]` often achievable.
  European-language work is usually covered by the standard channels (Crossref/OpenAlex
  index non-English venues).
- **Taiwan** (this owner's own literature environment — added 2026-09-03):
  **臺灣博碩士論文知識加值系統** `ndltd.ncl.edu.tw` for theses (see §Theses above);
  **華藝 airitiLibrary** `airitilibrary.com` for Taiwanese journals and theses —
  **institutional access only**, external users need their institution's VPN, so
  without it this is metadata-and-abstract at best and the shortfall is a `gaps` entry
  (*verified 2026-09-03*); **國家圖書館期刊文獻資訊網** for Chinese-language periodical
  indexing. A Chinese-language topic searched only in English is a `gaps` entry under
  the language-skew rule below, and these three are where that gap gets closed.
- **Extraction**: extract in the source language, deliver in the contract `language`;
  when exact wording is load-bearing, quote the original with a translation.
- **Credibility**: same rubric — a regional-language venue is not automatically a lower
  tier, but verify indexing (Scopus/WoS/DOAJ cover non-English venues) per rubric §4.

## Identifier resolution

Resolve BEFORE citing — an identifier that does not resolve must not appear in the
deliverable (failure mode #1).

- **DOI** → `https://doi.org/<doi>` (redirects to publisher; confirms existence) and
  `https://api.crossref.org/works/<doi>` (returns authoritative metadata: title,
  authors, venue, year — cross-check against what you're about to write).
- **arXiv ID** → `https://arxiv.org/abs/<id>`; API `id_list=<id>` for metadata;
  check `externalIds.DOI` (via Semantic Scholar) for a published version.
- **PMID** → `esummary.fcgi?db=pubmed&id=<pmid>`; PMC ID means free full text.
- **ISBN** → Google Books `?q=isbn:<isbn>` or Open Library
  (`openlibrary.org/isbn/<isbn>`) for edition metadata. Then locate the chapter:
  table of contents (publisher page or Google Books preview) → chapter/section
  number → page range. **Edition matters**: page numbers and even chapter numbering
  shift between editions — the locator must name the edition
  (e.g. "3rd ed., §7.2, pp. 301–305").
- **Citation string only** (no identifier) → Crossref
  `query.bibliographic=<string>` → take the top hit ONLY if title+authors+year all
  match; otherwise treat the work as unresolved and say so.

## Citation chasing (backward / forward)

Run at `standard` depth for the 1–3 most load-bearing sources; at `exhaustive` depth
for every included source. Skip at `quick` depth unless an extraction target is
unfilled.

**Backward (references OF a key paper):**
1. Get the reference list — Semantic Scholar `/references`, the paper's own
   bibliography, or a publisher landing page.
2. Select only entries cited FOR the extraction targets (follow the in-text citation
   context when readable, e.g. via Semantic Scholar citation contexts) — not the whole
   list.
3. Resolve identifiers → triage (P3) → extract (P4).

**Forward (papers CITING a key paper):**
1. Semantic Scholar `/citations` (or OpenAlex `cites:` filter if key available),
   sorted by recency and citation count.
2. Purpose: find corrections, follow-ups, contradicting replications, and the current
   state of the art beyond the key paper's date.

**Stopping conditions (any one suffices — log which fired in `search_trail`):**
- Saturation: a chasing round adds no source that fills an unfilled extraction target.
- Quota: depth's source budget reached AND all extraction targets filled.
- Depth cap: chase at most 1 hop from seed papers at `standard` depth (2 hops at
  `exhaustive`); deeper chains almost always leave the caller's question.
- Diminishing credibility: remaining candidates are all below the credibility bar
  already applied in P3.

If stopping leaves targets unfilled, that is a `gaps` entry, not a reason to keep
searching past the quota.

## Recall check — the positive control for the search (SKILL.md P2 points here)

Every other check in this skill guards **precision**: that what was said is supported.
Nothing guarded **recall**: that what exists was found. Those are different failures and
only one of them was instrumented — P4.5 got a two-sided calibration, the search stage
had none at all.

The gap matters because of what the skill's output claims. `gaps` says "not found in
searched sources", and that sentence looks *identical* whether the literature is absent
or the query was malformed. Saturation does not separate them: it proves the query
converged, and **a query built on the wrong vocabulary converges faster than a good
one** — it exhausts its own small neighbourhood immediately. The bubble check
(`credibility-rubric.md` §6) does not either: it interrogates the sources that made it
in, never the ones that never surfaced.

### Where a control comes from (in preference order)

1. **A `scope` seed already grep-verified** against the corpus per SKILL.md failure
   mode #9. Best control: independently known to exist AND known to be relevant.
2. **A local-corpus hit** — `zotero_local.py --search` / `pdf_index.py --search`. The
   user's own library proves relevance by having been collected.
3. **A source found by a different route this run** — e.g. a paper reached by backward
   chasing. Weaker (it entered through a channel, so it tests the *other* channels).
4. **A source cited by a source already found**, resolved and confirmed on-topic.

### Procedure

1. Pick the control BEFORE concluding, and **withhold it** — do not put its title, DOI,
   or distinctive phrasing into any query.
2. Run the queries as they actually stand.
3. Ask: did those queries surface the control on their own?
   - **Found** → the query reaches this neighbourhood. A "not found" for a *different*
     target now means something.
   - **Missed** → **the query is condemned, not the literature.** Repair it — usually
     the paper's own vocabulary differs from the user's (the P2 "iterate once with the
     terminology found in the first hits" rule exists for exactly this) — and re-run
     before writing any absence claim.
4. Log in `search_trail`: which control, found or missed, and what the repair was.

### When no control is available

Say so, in the deliverable, in these words or equivalent:

> no recall control was available for this run — "not found" here means *not found by
> the queries listed in `search_trail`*, which were not calibrated against a known item.

That is an honest downgrade, not a failure. What is NOT acceptable is an unqualified
"not found in searched sources" from an uncalibrated search: it asserts absence with
the confidence of a measurement that was never taken.

**Cost.** One extra query round per run, and only on runs that will report an absence —
a run that fills every extraction target needs no control, because it is not claiming
anything is missing.

**Scope limit, stated deliberately.** This is a spot check with n=1, not a recall rate.
It catches a query built on the wrong vocabulary or pointed at the wrong channel — the
common, cheap failure. It cannot detect systematically missing coverage (a whole
literature in a language or venue nobody queried); that remains rubric §6's job.
