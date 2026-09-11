---
name: literature-search-extract
description: >-
  Literature search & extraction SERVICE — locate formal scholarly sources (papers,
  preprints, textbooks, standards) and extract targeted information into a
  caller-specified deliverable (evidence tables, method comparisons, parameter sheets,
  annotated bibliographies) with full citation traceability; zero fabricated citations.
  Trigger on 「幫我找 X 主題的論文」「這篇 paper 的重點」「教科書怎麼定義 X」「查這個參數的文獻值」, or when another skill
  invokes it as a sub-service with a request contract. NOT for uncited broad sweeps (→ a T4
  research dispatch, ops/20-dispatch.md §6) or advising the user's OWN study methodology (→
  scientific-research-guide). Full disambiguation: ~/.claude/skill-trigger-dict.md.
---

# Literature Search & Extract

A retrieval-and-distillation service for formal scholarly sources. Its job is to turn an
information need into **verifiable, source-anchored text**: find the right papers/textbook
passages, extract exactly the information the caller needs from the right section, and
assemble it in the requested form — with every load-bearing claim traceable to a specific
source and location. It serves two kinds of callers: the human user directly, and other
skills that need literature input mid-workflow.

## Operating stance (read first)

- **You are a librarian-analyst, not an author of claims.** Output reports what sources
  say, attributed; your own inference is allowed only when explicitly labeled as such
  (`[synthesis]`) and derived from cited material.
- **Zero fabrication is the hard constraint.** Never invent a citation, DOI, page number,
  author list, numeric value, or quotation. An honest gap is a valid deliverable; a
  plausible-looking fake reference is this skill's worst failure — and **attaching a real
  source to a claim it does not make is the same sin better disguised** (failure mode #8,
  caught at P4.5). "Not found in searched sources" is itself a claim: failure mode #10.
- **Access honesty.** Distinguish what you actually read. Tag every source with an access
  level (see P3) and never present abstract-only knowledge as if the full text was read.
- **Copyright boundary.** Quote sparingly (short excerpts with quotation marks + locator);
  paraphrase by default; never reproduce full sections, full-text articles, or large
  verbatim blocks of a book.

## Invocation modes

### Mode 1 — Direct (user asks)
Parse the request into the same contract as Mode 2 (fill fields yourself from context).
Ask at most ONE question before searching, and only when the ambiguity would change the
search scope or extraction targets (purpose, comparison axes, source types, field/date
limits, depth). Presentation-only ambiguity never blocks: infer `output_format` from the
task verb via the catalog's "Use when" column (default: inline summary), deliver, and
offer a format conversion afterward only if an alternative adds real value.

### Mode 2 — Service (called by another skill)
The calling skill supplies a **request contract**. Run the pipeline without re-asking the
user unless a contract field is missing AND cannot be defaulted. Return the **result
contract** so the caller can continue its own workflow. Callers, their request presets and
what each consumes: `consumers/registry.json`; calls by situation: `references/bridge.md`.

**Request contract** (caller fills; defaults in parentheses):
```
purpose:        why the information is needed — drives extraction targets (required)
question:       the specific information need, as concretely as possible (required)
source_types:   papers | preprints | textbooks | standards | reports | theses |
                data (compilations, datasets) | patents | any (any) — channel per
                source class: references/connectors.md routing table
scope:          field/date/venue constraints, known key papers or authors (none)
                — named papers are seeds AND the P2 recall control, never ground truth
output_format:  one of the catalog below, or "caller-specified template" (inline summary)
depth:          quick (3–5 sources) | standard (5–15) | exhaustive (standard)
                — exhaustive wraps the pipeline in references/exhaustive-prisma.md;
                budget-warn the caller before running
language:       language of the deliverable (Traditional Chinese for human docs,
                English for machine-consumed returns)
```

**Result contract** (always return, even on partial failure):
```
findings:       the deliverable in the requested format
sources:        list of {citation, identifier (DOI/ISBN/arXiv), key, access_level, locators used}
gaps:           what was asked but NOT found, and where it was looked for
confidence:     per key claim — how many independent sources support it, any conflicts
search_trail:   queries run + databases/tools used (so the caller can audit or extend)
run_id:         the persisted evidence run behind this return (references/feedback-loop.md)
```

## Pipeline (P1 → P5, run in order)

### P1 — Parse the need into extraction targets
Before searching, translate `purpose` + `question` into *what kind of information* is
sought — each kind lives in a different section of a paper or textbook and needs its own
output shape; the need → home map is `references/extraction-playbook.md` §0.
**Premise check first:** a question can presuppose a fact the source never states — name
the presupposition as its own target, so a false one ships as a gap, never as a number.
Write down (internally) the target list: fields to fill, per source. This becomes the
extraction checklist for P4 — extraction without a target list degenerates into
abstract-summarizing, which is the anti-pattern this skill exists to prevent.

### P2 — Search
**Route first — pick one path before any query:**
- **Source-provided** — the user/caller supplied or named the source(s): verify source
  identity and readable scope, then skip discovery and go straight to P3→P4. Do NOT
  search for additional literature unless the user asks for supplements, a published
  version/correction/supplementary needs checking, or the supplied sources cannot answer
  the core targets — in those cases propose the mixed path instead of silently expanding.
- **Discovery** (default) — new sources are needed: run this full P2.
- **Mixed** — supplied sources as the core plus targeted supplemental search;
  `search_trail` must distinguish supplied vs discovered sources.

Tool priority: **registered connectors whose source class matches the need** (probe
before routing — a stale process returns 404, and a 404 reads as "no results") → **the
local corpus** (`zotero_local` + `local_pdf_library`: they rank what the user already
collected, never search the web) → **WebSearch/WebFetch** for discovery; the skill stays
fully functional with web search alone. Ladder, secret boundary, per-connector field maps:
`references/connectors.md`; per-channel strategies, identifier resolution, citation
chasing: `references/search-sources.md` — read it before any `standard`/`exhaustive` search.
**Host access policy before any fetch.** `connectors/access_policy.py --url <u> --check`
says which surface may touch which host (`~/.claude/hooks/literature-host-policy.json`); a
refused or challenged host is handed to the user as a named DOI/URL + query pack, never
retried through another User-Agent, browser or profile. Text that will be cited is retrieved
with `verify/fetchsrc.py`, which records route, status and sha256 per source.
Core principles:
- Build queries from a **vocabulary ledger**: core terms + synonyms + the three keyword
  layers a database exposes (author keywords, controlled vocabulary, index terms); iterate
  batch n → keyword set n+1 with the terms the first hits actually use, and run one
  **anchor round** (a review + the most-cited paper's co-citations) before saturation
  counts — `references/search-sources.md` §Query building.
- Prefer identifiers when known: DOI, arXiv ID, ISBN — resolve directly.
- When a channel fails (key wall, rate limit, outage), the literature is partly
  non-English, or the user has a local PDF collection, apply the matching strategy in
  `references/search-sources.md` — log substitutions, language coverage, and any
  personal key or polite-pool resource spent in `search_trail`.
- Chase citations both ways for `standard`/`exhaustive` depth: references OF a key paper
  (backward) and papers CITING it (forward) — the fastest route to the load-bearing
  literature.
- **Stopping rule:** stop when new queries return only already-seen sources (saturation),
  or when the depth quota is met and the extraction targets are filled. Log what was NOT
  searched if stopping early (feeds `gaps` and `search_trail`).
- **Recall check — the positive control for the search itself.** Saturation proves the
  query converged, not that it covered; a badly-built query converges *faster*. So
  before any "not found in searched sources" ships, withhold a source known to exist and
  be relevant, and check whether the queries as run surface it on their own. **A
  withheld known item the search misses condemns the QUERY, not the literature** —
  repair and re-run before reporting absence. Where controls come from, what to log, and
  what to say when none exists: `references/search-sources.md` §Recall check.

### P3 — Triage & access tagging
Rank candidates by (relevance to extraction targets) × (credibility) × (recency where it
matters). Credibility ordering, coarse: peer-reviewed journal/conference > established
textbook > preprint > technical report > secondary web source. The detailed rubric —
venue tiers, citation-context modifiers, mandatory retraction check for load-bearing
sources, predatory-venue screening, textbook edition rules, and the set-level
bias/coverage-balance check (citation bubble, group concentration, language skew) —
lives in `references/credibility-rubric.md`; apply it for `standard`/`exhaustive` depth.

Tag each source before extraction — this tag follows the source into the deliverable:
- `[full]` — full text read (open access, fetched PDF/HTML).
- `[partial]` — some sections read (preview, excerpt, supplementary only).
- `[abstract]` — abstract/metadata only (paywalled). Extract ONLY what the abstract
  states; flag that Methods/Results details are unverified.
- `[secondary]` — known only through another source citing it. Attribute as
  "B, as cited in A"; never present as directly read.

Paywall or access-controlled host: extract what the policy row permits, then hand the named
document to the user (`gaps`: "not retrieved, hand-to-user" + query pack). Never circumvent.

A locally-supplied PDF the Read tool refuses as "password-protected" is usually NOT
encrypted: probe and recover it per `references/search-sources.md` §Local PDF library
before downgrading the access tag.

### P4 — Extraction (the core competency)
For each selected source, work through the P1 target list against the section map:
- **Go to the section where the target lives** (P1 table); do not extract Results claims
  from the abstract's marketing framing — abstracts overstate, tables don't.
- **Record a locator with every extracted item**: section name, table/figure number,
  equation number, or page — enough for the caller to re-find it.
- **Preserve exactness for quantitative items**: value + unit + uncertainty/error bar +
  the conditions under which it was measured/computed (material, wavelength, temperature,
  dataset…). A number stripped of its conditions is a future landmine.
- **Capture stated limits, not just claims**: when extracting a method or result, also
  extract its stated assumptions and validity range from Discussion/Limitations — callers
  like scientific-research-guide need the limits more than the headline.
- **Quote vs. paraphrase**: quote (short, marked, with locator) when exact wording is
  load-bearing (definitions, disputed claims); paraphrase everything else.
- **Note disagreements verbatim**: when two sources conflict, record both positions with
  locators. NEVER average, harmonize, or silently pick one — conflicts go to the
  `confidence` field and are surfaced to the caller as a finding in their own right.
Worked examples per information-need type (including wrong-vs-right contrasts and the
pre-P5 checklist) live in `references/extraction-playbook.md` — read it when running P4
on a non-trivial extraction.

### P4.5 — Verification gate (between extraction and delivery)
Self-report is not a check: the judgement that a citation is sound cannot come from the
same pass that wrote it. Before P5, write an **evidence ledger** — one JSONL row per
load-bearing claim carrying the claim, identifier, locator, access tag, the **exact
support span** it rests on, and the path to the retrieved text — then run
`verify/citecheck.py` on it. Naming the span makes support falsifiable: a script cannot
judge support, but it can prove the quoted words are in the retrieved text. Persist
ledger and retrieved text in the run folder BEFORE the gate runs (`references/feedback-loop.md`).
Per row it also checks title/authors/venue against the resolved record, every number in the
claim against the span, the text's provenance manifest + access route, and retraction notices.
**Scope is by claim kind first, depth second.** Every **numeric or disputed** claim gets
a row at EVERY depth, `quick` included. Depth widens the net: `standard` adds all
load-bearing claims, `exhaustive` everything.
Protocol, repair order, set-level checks: `references/verification-gate.md`.

### P5 — Synthesis into the requested deliverable
Assemble extracted items into the `output_format`, in the requested `language`:
- Every load-bearing claim: inline citation + access tag, e.g. `(Smith 2024, Table 2) [full]`.
- Structure follows the format catalog below; ready-to-copy templates, filled examples
  and a full result-contract example live in `references/output-templates.md` — use its
  field/column sets verbatim for Mode 2 returns (callers parse by field name).
- End with the **gaps** and **confidence** sections — mandatory, even when empty
  ("all targets filled; no conflicts found") — then the loop footer: `run_id`, keys, review-when,
  and one **AI-use disclosure** line (which steps a model ran, what a human verified).
- Deliver inline by default. Create a file only when the user (Mode 1) or the caller
  contract (Mode 2) explicitly requests one — never because the content is long; and
  always a NEW file, never overwriting an existing report. Language rules per Mode:
  `references/output-templates.md`.
- **Zotero collection close-out** — standing step whenever the project keeps a Zotero
  collection: append the wave's newly READ papers (papers only — never a datasheet,
  patent, or `[secondary]`-only citation) to the project's bib JSON, then regenerate
  the RIS:
  ```
  python scripts/zotero_ris_export.py <bib.json> \
      --collection-name "<Zotero collection>" --out-dir <project>/references
  python scripts/zotero_ris_export.py <bib.json> ... --check     # same command, verify
  ```
  `--collection-name` is the project's Zotero collection name. The user refreshes
  Zotero via File → Import of the RIS; re-import duplicates existing items, so merge
  via Duplicate Items or hand the user a delta RIS of only the new wave. Never push via
  `localhost:23119` — `/api/` is read-only and `/connector/saveItems` cannot target a
  named collection. This copy inlines the full procedure because
  `references/connectors.md` does not ship here — `scripts/zotero_ris_export.py` does.

## Resilience & session economy

- **Context/token budget.** Full-text reading is the expensive step. Past ~10 `[full]`
  reads, warn the caller with a volume estimate, then narrow or batch: extract each
  source into compact target-list notes, discard the raw text, run P5 from notes only.
- **Reuse before re-search.** `loop/runs.py open` (P1) searches the evidence-run index for
  the same question and writes `reuse_check` into `run.json`; its line goes into
  `search_trail` (`register` refuses a run without it). On a hit, offer an UPDATE run: seed
  P2 with the prior `sources` + `search_trail`, search only unfilled gaps and the period since.
- **Partial failure returns a partial, resumable contract.** If the run dies mid-pipeline,
  still return the contract — `gaps` names the unprocessed portion, `search_trail` is
  complete to the failure — so a later run resumes by seeding P2 from that trail.
- **Feedback iteration.** When the caller says the extraction aimed at the wrong thing,
  do not restart: re-run P1 to rewrite the target list (at most ONE clarifying
  question), keep the P2 pool and P3 triage, redo P4→P5 only where targets changed.

## Output format catalog

| Format | Use when | Shape |
|---|---|---|
| Inline summary | quick answer, few sources | prose, cited claims |
| Annotated bibliography | caller needs a reading list | per-source: citation, 2–4 sentence relevance note, access tag |
| Evidence table | claim-by-claim support needed | rows = claims; cols = source, locator, supports/contradicts, quality |
| Method summary | reproduce/understand a technique | steps, required inputs, assumptions, stated validity range, per-step locators |
| Parameter sheet | numeric values needed | rows = parameter; cols = value±unc., unit, conditions, source+locator |
| Comparison matrix | choosing between methods/materials/models | rows = options; cols = caller's criteria; every cell cited |
| Quote pack | exact wording needed (definitions, standards) | short quotes + full locators |

## Failure modes to actively avoid

Numbered by history, not by severity — **#8 is the dangerous one**: it survives every
other check on this list and is invisible in the finished document.

1. **Fabricated or "reconstructed" citations** — the cardinal sin; verify every
   identifier resolves before including it.
2. **Abstract-only knowledge dressed as full-text reading** — the access tag exists to
   prevent this.
3. **Generic summarization instead of targeted extraction** — if the deliverable could
   have been written from abstracts alone, P1/P4 were skipped.
4. **Numbers without conditions/units/uncertainty** — incomplete extraction, redo P4.
5. **Silently resolving source conflicts** — conflicts are findings, not noise.
6. **Unbounded search** — respect the depth quota and stopping rule; log the boundary.
7. **Single-cluster evidence** — "consensus" drawn from one citation bubble, one
   group, or one language; run the rubric's bias/coverage check before P5.
8. **A real source cited for something it does not say** — the identifier resolves, the
   author is right, the paper exists, and the claim is not in it. Invisible to a reader
   and actively *rewarded* (citation density reads as rigor); measured rates and their
   sources in `references/verification-gate.md`. P4.5 exists for this one.
9. **Dispatcher seed anchors trusted over the corpus** — a caller's "known papers" list
   is hints, not ground truth (it may be transcribed from a bibliography the project
   never read). Grep-verify every seed against the recorded corpus; reject and REPORT
   the misses. Verified seeds then become P2's positive control, not a shortcut.
10. **An unexamined "not found"** — the deliverable's most dangerous sentence, because
    it looks identical whether the literature is absent or the query was wrong. Never
    ship one that has not survived the P2 recall check.
11. **Machine retrieval from an access-controlled host** — a 403/CAPTCHA answered with another
    User-Agent, headless browser or logged-in profile; the publisher then blocks the whole IP range.

## Reference map

Seven of these nine reference files ship with this copy of the skill; load each on
demand at the point the pipeline names it. P1→P5 is self-sufficient at
`quick`/`standard` depth without them. Not shipped in this repo:
`references/connectors.md` and `references/verification-gate.md`, together with the
`connectors/` and `verify/` tool lanes they document — machine-bound to this owner's
local Zotero HTTP connector, local PDF index, and local registry, none of which
travel. Two files from those same directories ship despite that:
`connectors/access_policy.py` and `verify/fetchsrc.py` are the skill-side half of
`rules/literature-access.md`'s host access policy — a separate, portable mechanism
from the routing/registry content those two reference files document, with no
local-service dependency, and already named directly at P2 above. P5's Zotero
close-out above is inlined so it does not depend on connectors.md; P4.5's ledger
procedure is likewise self-contained in this file (the gate script automates a check
a reader can still do by hand: confirm the quoted span is actually in the retrieved
text).
- `references/feedback-loop.md` — the evidence feedback loop (persisted runs in the vault,
  identity key, reflux entry point, consumer registry, forcing functions). Tools:
  `loop/runs.py` (open/register/find/check/affected/bridge), `loop/reflux.py`, `loop/idkey.py`.
- `references/connectors.md` — **not shipped in this repo.** P2 routing for registered
  data systems, the host access policy, access-ceiling and cost rules, per-connector
  field maps, Zotero close-out. Contract and secret boundary: `connectors/README.md`
  (not shipped); probe: `connectors/probe.py` (not shipped). The separate host
  ACCESS-CONTROL policy named at P2 above (`connectors/access_policy.py`,
  `hooks/literature-host-policy.json`) is a different mechanism and does ship.
- `references/verification-gate.md` — **not shipped in this repo.** P4.5 protocol:
  evidence ledger, what the gate may and may not rule on, repair order. Tools:
  `verify/citecheck.py` (not shipped), `verify/fetchsrc.py` (ships).
- `references/portability.md` — READ FIRST when running outside Claude Code (other
  agents / web LLMs): capability slots, substitutes, degradation honesty. Else skip.
- `references/search-sources.md` — per-channel strategies (each channel carries its own
  verification stamp and `review-when`), identifier resolution, local-corpus usage,
  citation chasing, degradation ladder, non-English strategy.
- `references/extraction-playbook.md` — P4 worked examples per information-need type,
  wrong-vs-right contrasts, pre-P5 checklist.
- `references/output-templates.md` — templates per catalog format, Mode 1/2 language
  rules, full result-contract example.
- `references/exhaustive-prisma.md` — PRISMA procedure, `exhaustive` depth ONLY.
- `references/credibility-rubric.md` — venue tiers, retraction & predatory-venue
  checks, textbook canonicity/edition rules, set-level bias/coverage check.
