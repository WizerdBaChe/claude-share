---
name: literature-search-extract
description: >-
  Literature search & extraction SERVICE — locate formal scholarly sources (papers,
  preprints, textbooks, standards) and extract targeted information into a
  caller-specified deliverable (evidence tables, method comparisons, parameter sheets,
  annotated bibliographies) with full citation traceability; zero fabricated citations.
  Trigger on 「幫我找 X 主題的論文」「這篇 paper 的重點」「教科書怎麼定義 X」「查這個參數的文獻值」, or when another skill
  invokes it as a sub-service with a request contract. NOT for broad topic reports (→
  deep-research) or advising the user's OWN study methodology (→
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
  author list, numeric value, or quotation. If a needed fact was not found, say "not found
  in searched sources" — an honest gap is a valid deliverable; a plausible-looking fake
  reference is the worst possible failure of this skill.
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
contract** so the caller can continue its own workflow. Known callers and their typical
requests:
- `scientific-research-guide` — Tier 1 literature review support, method-canon
  verification (its Gate B), parameter/typical-value lookup for domain profiles.
- `product-design-thinking` — mandatory prior-art & open-source search before designing.
- Any skill needing "what does the published literature say about X".

**Request contract** (caller fills; defaults in parentheses):
```
purpose:        why the information is needed — drives extraction targets (required)
question:       the specific information need, as concretely as possible (required)
source_types:   papers | preprints | textbooks | standards | any (any)
scope:          field/date/venue constraints, known key papers or authors (none)
output_format:  one of the catalog below, or "caller-specified template" (inline summary)
depth:          quick (3–5 sources) | standard (5–15) | exhaustive (standard)
                — exhaustive wraps the pipeline in the PRISMA-style procedure of
                references/exhaustive-prisma.md (protocol, logged search, two-pass
                screening, flow accounting); budget-warn the caller before running
language:       language of the deliverable (Traditional Chinese for human docs,
                English for machine-consumed returns)
```

**Result contract** (always return, even on partial failure):
```
findings:       the deliverable in the requested format
sources:        list of {citation, identifier (DOI/ISBN/arXiv), access_level, locators used}
gaps:           what was asked but NOT found, and where it was looked for
confidence:     per key claim — how many independent sources support it, any conflicts
search_trail:   queries run + databases/tools used (so the caller can audit or extend)
```

## Pipeline (P1 → P5, run in order)

### P1 — Parse the need into extraction targets
Before searching, translate `purpose` + `question` into *what kind of information* is
sought, because each kind lives in a different place and needs a different output shape:

| Information need | Typical home in a paper | Typical home in a textbook |
|---|---|---|
| Definition / concept / taxonomy | Introduction, review articles | Chapter openings, glossary |
| How a method/protocol works | Methods (+ supplementary) | Worked-example sections |
| Quantitative values, parameters | Results tables, figures, abstract headline numbers | Data tables, appendices |
| Validity limits, assumptions | Discussion, Limitations | Derivation preconditions |
| State of the art / who did what | Related Work, recent reviews | Latest-edition survey chapters |
| Canonical equations / derivations | Theory section, appendix | Core chapters (most reliable) |
| Contradictions / open questions | Discussion, review "future work" | Rarely — use reviews instead |

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

Tool priority: **a local corpus / reference-manager MCP if available** (e.g. `prism`,
a Zotero MCP, an Obsidian-vault MCP — these rank/relate sources the user already
collected; they do not search the web) → **WebSearch/WebFetch** against scholarly
indexes for discovery. The skill must remain fully functional with web search alone. Per-channel strategies, identifier resolution, local-corpus tool usage, and citation-chasing
rules live in `references/search-sources.md` — read it before any `standard`/`exhaustive`
search. Core principles:
- Build queries from: core terms + synonyms/aliases + field-specific vocabulary; iterate
  once with the terminology *found in the first hits* (papers name things differently
  than users do).
- Prefer identifiers when known: DOI, arXiv ID, ISBN — resolve directly.
- When a channel fails (key wall, rate limit, outage), the topic's literature is
  partly non-English, or the user has a local PDF collection, apply the matching
  strategy in `references/search-sources.md` (degradation ladder / non-English /
  local PDF library) — log substitutions and language coverage in `search_trail`,
  including any personal API key or polite-pool resource spent.
- For textbooks: search for the canonical text of the field ("standard reference for X"),
  then locate the relevant chapter/section via table of contents, publisher preview,
  or citations to it.
- Chase citations both ways for `standard`/`exhaustive` depth: references OF a key paper
  (backward) and papers CITING it (forward) — the fastest route to the load-bearing
  literature.
- **Stopping rule:** stop when new queries return only already-seen sources (saturation),
  or when the depth quota is met and the extraction targets are filled. Log what was NOT
  searched if stopping early (feeds `gaps` and `search_trail`).

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

Paywall handling: report the paywall, extract what is legally visible, suggest the user
retrieve it via institutional access if the source is load-bearing. Do not attempt to
circumvent access controls.

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

### P5 — Synthesis into the requested deliverable
Assemble extracted items into the `output_format`, in the requested `language`:
- Every load-bearing claim: inline citation + access tag, e.g. `(Smith 2024, Table 2) [full]`.
- Structure follows the format catalog below; ready-to-copy templates with field
  definitions, filled examples, and a complete result-contract example live in
  `references/output-templates.md` — use its field/column sets verbatim for Mode 2
  returns (callers parse by field name).
- End with the **gaps** and **confidence** sections — mandatory, even when empty
  ("all targets filled; no conflicts found").
- Deliver inline by default. Create a file only when the user (Mode 1) or the caller
  contract (Mode 2) explicitly requests a file deliverable — never because the content
  is long. When writing, always a NEW file (never overwrite an existing report), in
  Traditional Chinese for human readers; Mode 2 machine-consumed returns stay in English.

## Resilience & session economy

- **Context/token budget.** Full-text reading is the expensive step. If P3 selection
  implies more than ~10 `[full]` reads, warn the caller with a volume estimate, then
  narrow the selection or batch: extract each source into compact target-list notes,
  discard the raw text, run P5 from notes only. Never hold many full texts at once.
- **Reuse before re-search.** Before P2, check for a prior deliverable on the same
  question (project report location; ask in Mode 1). If found, offer an UPDATE run:
  seed P2 with its `sources` + `search_trail`, search only unfilled gaps and the period
  since, and write a NEW file stating what changed versus the prior version.
- **Partial failure returns a partial, resumable contract.** If the run dies mid-pipeline,
  still return the result contract — `gaps` names the unprocessed portion, `search_trail`
  is complete up to the failure — so a later run resumes by seeding P2 from that trail.
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

## Reference map

All five reference files below ship with the skill; load each on demand at the point the
pipeline names it. The P1→P5 pipeline is self-sufficient at `quick`/`standard` depth
without them, but they are required for `exhaustive` depth and for non-trivial extraction.
- `references/search-sources.md` — per-channel query strategies (scholarly indexes,
  preprint servers, textbook discovery), identifier resolution, local-corpus MCP usage
  (prism reference implementation) and fallback rules, citation-chasing procedure with
  stopping conditions, degradation
  ladder & cost transparency, non-English literature strategy. Channel facts
  verified 2026-07-07; re-verify on unexpected channel behavior.
- `references/extraction-playbook.md` — worked examples of P4 per information-need type,
  wrong-vs-right contrasts, and a pre-P5 extraction checklist.
- `references/output-templates.md` — templates for each catalog format (field
  definitions + filled examples), Mode 1/Mode 2 language rules, full result-contract
  example.
- `references/exhaustive-prisma.md` — PRISMA-style procedure for `exhaustive` depth
  only: protocol block, logged search, two-pass screening with reason codes, flow
  accounting, saturation statement, deliverable additions. Never load at quick/standard.
- `references/credibility-rubric.md` — source-quality scoring: venue tiers, citation
  context, preprint→published check, retraction check (Retraction Watch via Crossref),
  predatory-venue screening, textbook canonicity & edition rules, set-level
  bias/coverage-balance check.
