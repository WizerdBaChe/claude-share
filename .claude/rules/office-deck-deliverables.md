---
paths:
  - "**/*pptx*.py"
  - "**/*.pptx"
---

# Programmatic PPTX deliverables (python-pptx decks)

Sunk from the SSLD professor-deck round (2026-08-31): two editions, 45 slides,
every rule below paid for by a real UAT failure or a COM-render catch. Sibling
rule for HTML decks: `deliverable-doc-refs.md` (define-before-use + hover cards
+ build gates). Reference implementation with these fixes verbatim: a reference
implementation lives in the source environment's asset library (helpers
script-derived from the working builder; run its sample to see every rule fire).

**Asset properties — a generated .pptx must satisfy all of these, and the
build script is where they are enforced:**

- **Local-file hyperlinks are stored in PowerPoint's CANONICAL format**:
  `"file:///" + str(path)` — raw backslashes, CJK unencoded.
  `Path.as_uri()`'s percent-encoded form makes PowerPoint fail with
  "cannot open the specified file". When any Office app rejects a generated
  construct, PROBE the canonical form: drive the app itself (COM) to produce
  the same construct, unzip, read what it stored, replicate byte-for-byte
  (`ops/lessons.md` L-041). Build asserts link targets exist. Tell the user
  about PowerPoint's one-time security prompt, or the fix reads as broken.
- **CJK text sets an east-asian typeface explicitly**: `font.name` covers
  Latin only; append `a:ea`/`a:cs` typeface elements to `rPr`, or Chinese
  silently renders in the theme font.
- **No orphan wraps** (user layout ruling 2026-08-31): a line that would spill
  ≤8 characters onto the next line is not allowed — widen the block first
  (kill python-pptx's default 0.1 in textbox side insets), then shrink the
  font. Width estimators run ~4% narrow against bold JhengHei — carry a
  measured safety factor. Second failure class (T22): wide NON-CJK glyphs
  (⇒ ⇔ → ± and other U+2190–U+22FF symbols) get counted at Latin width but
  render full-width, so fit_w passes and the title still wraps a 1-char tail.
  The estimator's fullwidth-extra set must include them; the robust fix for
  TITLES is rewording to comfortably one line — COM-render and eyeball stays
  the only authority.
- **Text gates are per deliverable FAMILY, not per project**: a deck about a
  different mechanism gets its OWN canonical-term set and load-bearing-value
  list (reuse the gate machinery + injected-violation controls, never another
  family's term-frequency requirements — forcing 凹面鏡×5 into a flat-facet
  deck would gate in noise). A consolidated deck spanning families runs BOTH
  value sets (SSLD build_pptx7: six-case 34 values + P7 10 values).
- **Bottom source strip = "References", literature only** (user ruling
  2026-08-31): cite the literature itself (author-year-venue as recorded —
  never fabricate bibliography the project has not recorded); internal
  instruments/PASS-counts live inside slide content; a page resting on
  internal derivation alone gets NO strip.
- **Page numbers stamped by a post-pass** from slide order — never hardcoded
  in content (same rot as the HTML-deck rule).
- **Every stored file:// hyperlink must resolve — as a BUILD GATE, read out of
  the package rels** (T23c 2026-08-31): when a linked artifact is renamed,
  moved, or archived, a dead jump button renders exactly like a live one, and
  term/value/fit gates are all blind to it (they read text and layout, never
  targets). Gate reads `*.rels` from the pptx zip, asserts every target exists,
  and carries a missing-target positive control per build. Thresholds are PER
  EDITION, not per project — the gate's first run caught a 4:3 edition that
  legitimately has 7 links against a 9-link threshold copied from the 16:9
  edition. Corollary for artifact PATHS: a new member of a proposal/figure
  family belongs in that family's existing output directory — the reader looks
  there by convention, so a correct file in a novel folder reads as missing.
- **Text gates run over the text EXTRACTED from the built pptx** (shapes +
  table cells + speaker notes): canonical-vocabulary lint and verbatim
  load-bearing-value check, shared across ALL editions of the deliverable
  family, each with an injected-violation positive control every build.
- **Visual acceptance is a render loop, not a claim**: export slides to PNG
  via PowerPoint COM (`SaveAs(dir, 18)`; filenames are locale-dependent —
  投影片N.PNG on zh-TW systems) and eyeball for orphan wraps, overlaps
  (tables AUTO-GROW on wrap and cover fixed-y content below), and font
  fallbacks. Measure image aspect ratios (PIL) BEFORE computing layout —
  a guessed aspect is how stacked figures overflow the slide.
- Unzipping/inspecting pptx: use a Python script file — PowerShell 5.1 lacks
  `System.IO.Compression.ZipFile` by default, and inline `python -c` with
  CJK/quotes breaks in PowerShell.
