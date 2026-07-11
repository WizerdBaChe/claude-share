# Search Sources — per-channel strategies, identifier resolution, citation chasing

Companion to SKILL.md P2 — applies to the **discovery** and **mixed** paths only; on
the source-provided path do not expand the literature set beyond the supplied sources
(see SKILL.md P2 routing). Channel facts below (endpoints, auth, limits) were verified by
web search on **2026-07-07**; they are volatile. If a channel behaves differently than
described (404s, auth walls, new limits), re-verify with a web search before concluding
the channel is unusable, and update this file.

## Tool routing (read first)

Two fundamentally different tool classes serve P2:

1. **`prism` MCP (`mcp__prism__*`)** — a LOCAL corpus tool. It ranks, relates, and
   exports nodes inside universes the user has already ingested. It does NOT search the
   web and cannot discover sources outside the corpus.
2. **WebSearch / WebFetch** — discovery of new sources on the open web, plus direct
   fetching of scholarly API endpoints (Crossref, OpenAlex, arXiv export — these return
   JSON/XML that WebFetch can read).

`prism` is the reference implementation of the local-corpus slot; any reference-manager
MCP (e.g. a Zotero MCP, an Obsidian-vault MCP) slots into the same routing rules —
local tool = already-collected corpus only, and an empty local result never means
"literature not found". Verify the specific server's actual tool set before relying on
it; the table below is prism-specific.

**Routing rule:** start with `prism list_topics` ONLY when the question plausibly
concerns a topic the user has curated before (it's one cheap call — when in doubt,
check). If a matching universe exists, rank inside it first; web search then fills gaps
and finds newer work. If no universe matches, go straight to WebSearch — do not treat an
empty prism result as "literature not found".

### prism MCP usage

| Tool | Use for | Notes |
|---|---|---|
| `list_topics` | discover available universes/topic lenses + node counts | call first; a universe with few nodes ⇒ thin coverage, weight web search higher |
| `rank_by_topic` | rank corpus nodes against a topic | pass `description` for an ad-hoc lens (not persisted), or `topic_id` for a saved lens; `top_k` default 20 |
| `get_citation_map` | ranked citable list + manual-link chains for a saved topic | requires `topic_id`; the corpus-side analogue of citation chasing |
| `get_node` | metadata + digest/excerpt (≤500 chars) for one node | the excerpt is NOT full text — extraction from a prism node alone is at most `[partial]` |
| `similar_nodes` | neighbors of a known-relevant node | corpus-side "more like this" |
| `export_bibliography` | BibTeX / CSL-JSON for selected nodes | for the `sources` field of the result contract |

Access-tag rule for prism-sourced items: a node digest supports `[partial]` at best;
to claim `[full]`, fetch and read the actual document (via its identifier) yourself.

**Fallback to WebSearch when:** no universe matches the question; the matching universe
is stale relative to the question's recency needs; `rank_by_topic` returns low-relevance
nodes; or the extraction targets need full text that the corpus digest can't provide.
Always log in `search_trail` whether prism was used, skipped, or unavailable.

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
- API: `api.semanticscholar.org/graph/v1/` — works unauthenticated at a shared, low
  rate; free API key raises it (~1 request/s baseline as of verification). Fine for
  this skill's volumes via WebFetch.
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
- API: `api.openalex.org` — **requires an API key since 2026-02-13** (credit-based
  free tier covers typical interactive use; keyless calls get only a small trial
  allowance then 409s). If keyless calls fail, fall back to Semantic Scholar/Crossref.
- Strengths: ~250M works, concepts/venues/authors as first-class entities, good for
  "who works on X" and coverage checks.

### arXiv (physics/math/CS preprints)
- API: `export.arxiv.org/api/query` — free, no key; be gentle (~1 request per 3 s,
  single connection; arXiv actively 429s bursty clients as of early 2026).
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
  assume UNAVAILABLE for this skill. Use instead: WebSearch scoped
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
- **With prism**: if the collection is ingested in prism, rank/relate there first, then
  Read the underlying PDF for `[full]`-level extraction (a prism digest alone stays
  `[partial]`).

## Degradation ladder & cost transparency

When a planned channel fails (auth wall, 429/409 bursts, outage), substitute down this
ladder instead of aborting P2, and record every substitution in `search_trail`:

1. Keyed/limited APIs (OpenAlex keyed, Semantic Scholar keyed tier) →
2. Free unkeyed APIs (Semantic Scholar shared tier, Crossref polite pool, arXiv export,
   PubMed E-utilities) →
3. WebSearch site-scoped queries + landing-page WebFetch (always available) →
4. prism local corpus alone (coverage limited to ingested docs — flag in `gaps`).

Rules:
- Never retry-loop a rate-limited endpoint: back off once, retry once, then degrade.
- A degraded run is a valid run — state which channels were skipped and what coverage
  that may cost (feeds `gaps`), instead of failing the whole request.
- **Cost transparency:** when a run spends a personal resource — an OpenAlex key's
  credits, a keyed Semantic Scholar tier, or the Crossref polite pool (which sends the
  user's `mailto`) — name it in `search_trail` so the caller knows what was consumed.

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
