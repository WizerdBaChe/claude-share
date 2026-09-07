---
xi: 1
what: literature-search-extract 與每個消費者的橋接——依情況互相呼叫、共用什麼、什麼不跨越；由登錄表產生，勿手改 (bridge between the literature skill and its consumers, generated from consumers/registry.json)
tags: [literature-search-extract, bridge, consumers, generated]
aliases: [LSE 橋接, 文獻 skill 消費者橋接, lse bridge, literature-search-extract bridge]
date: 2026-09-07
status: live
---
<!-- generated-from: consumers/registry.json sha256:2d82f1ff56838a747ce75e27644265475b7b3b643afe86f2a73daad6010fca9d — rendered by loop/runs.py bridge; never hand-edit (design D-L17) -->

# Bridge — literature-search-extract and its consumers (generated)

A consumer is a ROW in `consumers/registry.json`; this file is that registry rendered for reading.
Edit the row, then `python loop/runs.py bridge`.

## Shared by design

- **Evidence run**: every LSE run that reaches P4.5 persists in the vault home (`references/feedback-loop.md`);
  a Mode 2 return carries `run_id` and `sources[].key`, so a consumer can cite without re-resolving.
- **Identity key**: one normalizer (`loop/idkey.py`); joins are computed at read time from each store's
  identity field — no store is migrated.
- **Reflux**: the only write path back is `loop/reflux.py` (consumed / correction / retraction / handoff / rerun).

## What never crosses

- Verdict words (provisional / leaning / hypothetical / withhold) are paper-distill's; LSE quotes, never invents.
- Methodology (what to search for, how evidence bears on the user's study) stays with scientific-research-guide.
- LSE never advises on the user's own study design and never writes into a consumer's store or into Zotero.

## scientific-research-guide

- status `live` · direction `both` · registered 2026-09-03
- why it matters here: The first known caller; it already carries half a loop (Verified (date), review-when, Provenance log) and lacked only the join key and the row->run pointer.
- request presets (fill the rest from context):
  - `gate_b_verify`: purpose=Gate B: verify a method-canon or standard claim before advising; output_format=evidence table; depth=quick; source_types=papers | textbooks | standards
  - `citation_identity`: purpose=identity / access-tier / currency verification of a cited source (user-supplied-citations delegation rule; guide §9 step 2); output_format=caller-specified template: canonical identifier + access tag + one-line relevance + limitations (promotion-table columns); depth=quick; source_types=any
  - `parameter_lookup`: purpose=a literature value for a profile's typical-range cell; output_format=parameter sheet; depth=quick; source_types=papers | data
- consumes: `findings`, `sources[].key`, `gaps`, `confidence`, `search_trail`, `run_id`, `review_when`
- writes back: `consumed`, `correction`
- artifact: Source Ledger row (§7b) / user-supplied-citations promotion row · store `skills/scientific-research-guide/domains/**/*.md#7b ; skills/scientific-research-guide/references/user-supplied-citations.md` · identity field: Identifier cell (free text; the key is derived at read time by idkey.find_all — no migration) ; Canonical identity cell · run pointer: Verification status cell `run:<run_id>` ; Disposition cell `run:<run_id>`
- calls by situation:
  - Gate B verification: SRG fills `gate_b_verify`, consumes the evidence table + run_id, writes the §7b row with `run:<run_id>` in the Verification status cell, then a `consumed` event.
  - Citation intake or currency pass: one LSE run per profile (`citation_identity`); Checked (date) = the run date; the row cites `run:<run_id>`; the human report stays in ~/.claude/reports/.
  - A retraction or correction reaches a key its ledger cites: `runs.py affected <key> --scan-srg` names the profile row; SRG re-verifies per guide §3.8 and writes a `correction` event.
  - Never: SRG's packet -> profile pipeline (guide §9 steps 1, 3–7), profile-lint, eval-impact and routing stay SRG's own.
- review-when: domain-expansion-guide.md §3.7/§9 or user-supplied-citations.md Delegation rule change their cells

## product-design-thinking

- status `live` · direction `calls_lse` · registered 2026-09-03
- why it matters here: Its prior-art sweep is the second standing caller (references/prior-art-sweep.md); a patent channel exists that it did not know about.
- request presets (fill the rest from context):
  - `prior_art_slice`: purpose=Phase 1 formal-literature slice: an algorithm's canonical formulation, a reported figure, a standard's wording; output_format=annotated bibliography | evidence table; depth=quick; source_types=papers | standards | patents
- consumes: `findings`, `sources[].key`, `gaps`, `run_id`
- writes back: `consumed`
- artifact: design-doc prior-art block (hypothesis sheet diff, OSS inventory, borrow ledger) · store `the design document's Phase 1 block` · identity field: citation text (DOI / arXiv in the borrow ledger row) · run pointer: `run:<run_id>` beside the borrow-ledger row
- calls by situation:
  - A sub-problem hinges on published scholarly work: delegate that slice with `prior_art_slice`; OSS inventory, competitors and environment stay in PDT.
  - After the design ships: a `consumed` event per cited run, artifact = the design doc path + B-n row.
- review-when: prior-art-sweep.md §1 changes its delegation sentence

## zotero-local

- status `live` · direction `store` · registered 2026-09-03
- why it matters here: The user's library is the local corpus and the join target; Ow 2010 sat in it twice with case-different DOIs.
- artifact: Zotero item (read-only join) · store `<zotero-library> (copy-then-read via connectors/zotero_local.py)` · identity field: DOI ; preprint archiveID (`arXiv:` prefix) ; extra line `arXiv: …` ; ISBN · run pointer: (none — Zotero is never written, INV-9)
- calls by situation:
  - Join only: `runs.py affected <key>` lists the Zotero item keys whose DOI/arXiv normalize to the key, with their PDF state; duplicates are reported for the user to merge in Zotero, never merged here.
- review-when: Zotero changes its schema or the library path moves (connectors/registry.json zotero_local entry)

## a3-retraction-sweep

- status `planned` · direction `writes_back` · registered 2026-09-03
- why it matters here: Registered before it exists so its event kind and actor id are fixed; a sweep printing '0 retractions' is not believed until calibrated two-sided.
- writes back: `retraction`
- artifact: retraction events (Crossref update-to / relation over the Zotero DOIs) · store `(tool not built — credibility-rubric.md §3b names the rule)` · identity field: DOI from the Zotero collection · run pointer: event.evidence carries the notice locator
- calls by situation:
  - When built (needs a known-retracted and a known-good DOI as fixtures, OQ-5): after the Zotero close-out, every fired DOI becomes `python loop/reflux.py retraction --actor a3-retraction-sweep --key doi:… --evidence "<Crossref update-to notice>"` — the same path a person uses.
- review-when: the sweep tool ships (status -> live) or Crossref changes its retraction fields

## paperlens

- status `planned` · direction `calls_lse` · registered 2026-09-03
- why it matters here: A consumer that does not exist yet, wired by one row — the proof that adding a participant is a registry change, not a code path.
- request presets (fill the rest from context):
  - `term_check`: purpose=annotator: is this the standard term?; output_format=quote pack; depth=quick; source_types=textbooks | papers
  - `prior_results`: purpose=annotator: what did earlier work report on this claim; output_format=evidence table; depth=quick; source_types=papers
- consumes: `findings`, `sources[].key`, `run_id`
- writes back: `consumed`
- artifact: annotation card · store `<local-workspace>/PaperLens (design stage)` · identity field: its own doi field · run pointer: annotation id in event.artifact
- calls by situation:
  - The extensibility demonstration (design §3.8.3): this row is the ENTIRE wiring on the LSE side; PaperLens reads the generated bridge section, fills a preset, receives run_id + keys, writes `consumed` events with its annotation id, and `runs.py affected` later lists those ids when a key is retracted.
- review-when: PaperLens makes its first real call (status -> live) or its store/identity field is defined
