---
paths:
  - "**/*pptx*.py"
  - "**/*deck*.py"
  - "**/*slide*.py"
  - "**/*.pptx"
---

# Programmatic PPTX deliverables (python-pptx decks)

Sunk from the SSLD professor-deck round (2026-08-31): two editions, 45 slides,
every rule below paid for by a real UAT failure or a COM-render catch. Sibling
rule for HTML decks: `deliverable-doc-refs.md` (define-before-use + hover cards
+ build gates). Reference implementation with these fixes verbatim: a reference
implementation lives in the source environment's asset library (helpers
script-derived from the working builder; run its sample to see every rule fire). Index line lives
in `CLAUDE.md`; review-when: python-pptx changes how it stores hyperlink targets
(or gains an API that emits PowerPoint's canonical `file:///` form itself), or a
PowerPoint build starts accepting the percent-encoded form — either event turns
the first rule below from a fix into a workaround, and the verdict is a COM probe
(`ops/lessons.md` L-041), never a changelog.

**Acceptance severity is set by the deck's CLASS, declared by the build**
(user ruling 2026-09-15, SSLD T04: "不要出現明顯重疊或歪斜就行 … 不用花太多時間跟額度處理這種小事"):

| class | what it is | blocks delivery | non-blocking (report once, no fix loop) |
|---|---|---|---|
| **conclusion** (結論式／工作報告) | a deck that carries results for reading and editing: figure decks, round-result decks, analysis notes | obvious OVERLAP (text on text, text on drawing, a leader through text) and SKEW (a shape rotated or displaced off its structure); anything that makes content unreadable or wrong | a shape past the slide edge, a tight footer band, orphan wraps, spacing/alignment/aesthetics, headroom findings |
| **presentation** (展示用) | a deck shown to an audience: proposal, lab meeting, defence | every bullet below | — |

A deck with no declared class is treated as **presentation** (the stricter reading).
For a conclusion-class deck the bullets below still SHAPE the builder (fonts, links,
notes gates keep their full force: they are about content, not looks), but a
layout/aesthetic finding is a WARN line in the build output, never a rebuild, and
the COM visual read covers one page per layout kind plus every page a gate flagged,
not every page. Downgrade keeps DETECTION: the check still runs and its positive
control still fires; only its exit severity changes. review-when: the user
reclassifies a deck, or a conclusion-class deck is promoted to be presented.

**Presentation-class content: P1–P5** (P5 added 2026-09-21; user ruling 2026-09-20, B-14: post EP005 「平凡簡報術」 folded with
the SSLD rulings T20 「結論先行、用圖說話」, T43 「圖為主、文字為輔」, T58 「圖是產品、文字是輔助」, v3
2026-09-10 and L-077). These cover every audience-facing deck, PPTX or HTML (the HTML deck class points here from
`deliverable-doc-refs.md`). **Paper talks are excluded**: paper-story decks must carry the paper's content and
follow its own `lab-template.md` R6 rules. Project-only rulings stay in their projects (SSLD's black/white/grey,
no code names, PM register).

- **P1 Figure-led (presentation class).** A "figure" is any carrier that shows instead of tells: a picture or
  photo, a GRAPH (chart), a TABLE, or a diagram. A graph or table often carries more information than prose
  and is still effective. A long explanation goes to the speaker notes. Pick the carrier by the question the
  page answers, and write the choice down:
  photo/picture when the object's appearance is the claim (a device, a setup, a micrograph); graph when the
  SHAPE of the numbers is the message (trend → line, comparison → bar, spread → box/histogram, relation → scatter;
  load the `dataviz` skill before any chart code, and its form heuristic decides the form); table when the
  reader needs exact values, or items × ≥ 3 attributes, or parallel items; diagram when structure or flow is the
  message (`diagram-authoring`); text only when none of these can carry it, and say why. The build declares per
  page `figure kind + the question it answers`.
  **「半頁」 is a CONTENT-DENSITY limit, not an area or pixel ratio** (user ruling 2026-09-20; this corrects
  L-077's "figure over half the page"). If more than 50 % of a page's narrative is information a figure could
  carry (numbers to compare, parallel items, a sequence or structure, a before/after), the page is **過重**:
  move that part into a photo, graph, table or diagram. How much of the slide the figure covers is not the
  measure. A text gate cannot tell which sentences could have been a figure, so the check is a reader pass: the
  sample page (P4) and a per-page review. A figure-area share was tried and dropped: it measures layout, and
  accepted decks sit at a median of 23–38 %.
- **P2 Density is declared.** Every deck states its density: **極簡** (default for presentation class: subheading
  4–8 字 + one sentence; two sentences only when a number backs the claim) or **繁複** (enough text to be read
  or presented from; allowed for conclusion class, and chosen deliberately when the speaker needs the script on
  the slide). **超簡** is a named defect: a page reduced to a keyword that the audience cannot follow once the
  speaker digresses. The declaration is checkable; whether the density suits the room is the reader's call.
- **P3 Flat and clean (every class).** The emitted deck carries no gradient, shadow, glow, reflection, soft
  edge, bevel or extrusion on shapes, lines, text or table cells. This includes decoration INHERITED from the
  theme: an untouched python-pptx `add_shape()` inherits an outer shadow, so builders set
  `shadow.inherit = False` and an explicit fill. At most 3 distinct non-grey colours per slide, with figures
  exempt. Gate: a source-only presentation-gate tool (does not ship here), run with `--class <class>`. Decoration FAILs a
  presentation deck and WARNs a conclusion deck; the colour count is always WARN. HTML decks follow the same
  property (no decorative `box-shadow` / gradients on slide content; UI chrome such as hover cards is exempt),
  as an authoring rule until an HTML check exists.
- **P4 Sample page first (presentation class).** Build the most representative page and show it before
  generating the whole deck; density, page count, number placement and footer are settled on the sample
  (L-077). The sample is the first `A 必驗` item.

- **P5 Hierarchy by type size; title and description are separate objects (every audience deck).** The
  reading order is carried by FIXED type tiers, not by boxes, rules or colour: the eye finds the page title, then
  the page's one-sentence description, then each block's subheading, then its sentence. Tiers (16:9, JhengHei;
  a template's own masters override): page title 26–28 pt bold · description sentence 16 pt, its OWN text object
  under the title, never a run inside the title or a card · block subheading 18–20 pt bold · block sentence /
  body 15–16 pt · table 13–15 pt · figure label and caption 12 pt · kicker / page number 11–12 pt. Adjacent tiers
  differ by ≥ 2 pt; body text in a presentation deck never goes below 14 pt (SSLD T58 「字級固定 pt、下限 14」);
  a page that only fits below the floor is split or its text moves to the notes, it is never shrunk. The build
  declares the tiers as constants and the size search steps WITHIN a tier, never across it. Origin: the L-077
  user quote 「子標題A＋一句話短描述、切換子標題B…用視覺層級提供閱讀引導的排版」 (2026-09-10) — its density half
  became P2; this, its layout half, was lost in that promotion and cost COMSOL_Test round 32 a rejected deck
  (2026-09-21: 「用字體大小自然分層」「title 跟 describe 分開放置」). Checkable: font sizes per text object read from
  the emitted file (smallest body run ≥ 14 pt; title and description are two shapes). review-when: the user rules
  different tiers, or a lab template with its own masters becomes the default.
- **Shared layout code lives in one place and rulings flow back to it.** A project that copies a layout engine
  ("copies, not imports") must port a GENERIC ruling it gains back to the shared asset
  (the source environment's asset-library deck builder, not shipped here) or record why not; otherwise the next project starts from the stale copy —
  measured 2026-09-21: the shared builder still carried 2026-08-31 defaults (table 10.5 pt, no line spacing, no
  tiers) while SSLD's copy had all of them.

Cross-medium counterparts of P1–P5 (the same principles as derived for posts and videos, with evidence) are in
a source-only cross-medium design-principles note (does not ship here); this file stays canonical for decks.

Not adopted from the source post, with reasons: making keywords as big as possible conflicts with fixed type
levels; masks and text over images count as overlap; always using Chinese contradicts English lab decks; the
cover-first claim cites no source.

**Intake — one question, options from the store, choice recorded in the deck** (user
ruling 2026-09-29, borrowed from open-slide's integration model): a NEW deck project
starts by listing its options, never by recalling them —
`python -X utf8 <vault>/tools/consumers.py options` (vault deck assets,
zh capability, preview image + `preview_state`, html demo path) plus this rule's own
enums (class: presentation | conclusion; density: 極簡 | 繁複). ONE `AskUserQuestion`
settles class, density and builder/shell, the preview path in each option's text.
The builder is then copied with `consumers.py take <asset> <project> --dir build`,
which writes `<project>/asset-choices.json`; class and density go in the same file
under `"decks": {"<deliver file>": {"class", "density", "build"}}` — one key per edition, so a
project shipping several editions of one content (極簡 / 繁複 / conclusion) records each. `consumers.py sync <project>` later says whether
the vault or the copy moved (vault-ahead → pull; project-ahead → back-port candidate,
the "rulings flow back" bullet below). Paper talks keep paper-story's own intake.

**Review loop**: the user reviews a built deck in PowerPoint itself (select or
comment a shape). `skills/pptx-review` reads the cursor and the comments
(`tools/pptx-review`) and applies them to the BUILD SOURCE. A builder therefore
names every content shape (`shape.name` = its content key) — an unnamed
`TextBox 12` cannot be mapped back to the source a comment is about.

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
- **Height, not only width** (SSLD proposal deck 2026-09-10, `ops/lessons.md` L-078):
  a block-height estimator for Microsoft JhengHei must use a line pitch of
  ≥1.5 × font size (1.55 for body); 1.35–1.4 under-counts and the last
  block lands on the template footer band while python-pptx, PowerPoint and
  validate.py all stay silent. Any layout helper that distributes blocks over
  a box shrinks the font (0.5 pt steps) until estimated heights + gaps fit,
  and the COM render is checked for ink inside the footer band — a pixel gate
  with a deliberately over-filled page as the positive control is the target
  shape; until it exists, the eyeball pass covers every page, not a sample.
  **1.55 is the pitch for a bottom-anchored block, not for text inside a drawn
  rectangle** (SSLD 操作手冊 2026-09-13): measured off that deck's own COM
  render, 13 pt CJK lines came back at 0.30 in, a real pitch of ~1.66. An
  anchored block absorbs the under-count silently (the extra height grows into
  empty space); a tinted rect does not — its own border cuts the last line,
  and the build reports the page as clean. Text in a rect gets its own pitch
  (1.70 keeps the bias safe: box slightly too tall, font one step small), its
  own size search, and reports its own fit finding.
- **Body text breathes: 1.5 line spacing, 6 pt between paragraphs** (user ruling
  2026-09-21, SSLD T16: 「如果版面放得下，優先1.5行距或者下行行距6PT，現在很多字有點擠」,
  then 「行距設定拉到全域級」). Every class. Every multi-line body paragraph — text blocks,
  bullets, table cells, text in rects — is emitted with `line_spacing = 1.5`; inside a
  cell or block holding several paragraphs, each paragraph but the last gets
  `space_after = 6 pt`. Exempt: titles, kickers, footers, page numbers, figure labels
  and other one-line labels. The height estimators above MULTIPLY their pitch by the
  line spacing and ADD the paragraph gaps (T16 `layout.py` `est_h` / `_row_h` is the
  instance), so a page that stops fitting is reported by the fit gate, never
  overflows silently. When a page does not fit, in order: split the page if its
  content splits; if the page's purpose is being ONE page (a whole-procedure
  overview, a lookup table), step the spacing down 1.25 → 1.0 before shrinking the
  font; the build output names each page that left 1.5 and why. Measured cost at T16:
  a 43-slide manual became 52 (step pages split), the two 12-row overview tables
  held one page at 1.25. A user-supplied template whose masters set their own
  spacing keeps it. review-when: the user rules a different default, or a template
  family adopts one.
- **One width inflation cannot serve both a budget and a stored geometry**
  (SSLD 操作手冊 2026-09-13). A safety factor over the width model (~1.04 for
  bold JhengHei) is the right bias for a BUDGET — over-count and the table
  still fits — and the wrong one for the row height actually written into the
  file: a cell landing at 100–103 % of its column is given a line PowerPoint
  never draws, and that row sits a line taller than its neighbours, which
  reads as random spacing inside one table. Store heights at ~1.01 (the raw
  model is itself ~1 % wide), keep the fit decision, the size search and the
  height the table helper RETURNS to its callers at the full factor: anything
  stacked below still clears the reserved height, so a boundary cell that does
  wrap grows into space already paid for instead of into the foot. Same split
  as the orphan-tail rule above (raw width for a tail, inflated for a height) —
  when one number serves two decisions, ask which direction each wants.
  Corollary for any late instrument change: its blast radius is MEASURABLE —
  wrap the helper, recompute both ways, and print the exact list of pages whose
  visual acceptance the change invalidated (7 of 50 there); re-read those, and
  keep the list in the run transcript. A remembered scope is not a scope.
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
- **A deck delivered as EDITABLE survives one more line of its own kind in
  every content frame.** Every other check here measures the deck standing
  still; this one measures the reader's first edit, which is why the file was
  shipped editable at all. Gate: a source-only headroom-measurement tool (does
  not ship here), run as `<deck> --content <shape-name regex>` — it duplicates each frame's own last
  paragraph (self-similar, so the probe scales with the frame), re-measures with
  PowerPoint's layout engine, restores, and rules on three breaks: CLIP
  (an `autosize=none` frame now taller than its inner height), ESCAPE (a growing
  frame leaves the slide), COLLIDE (a growing frame — or a table, whose row
  heights recompute — enters a shape it did not touch before; the auto-grow
  hazard named two bullets down, now measurable instead of eyeballed).
  **Which frames are content is not determinable** — a page number and a
  paragraph are both text frames — so the BUILD declares them; an undeclared run
  closes nothing (WARN, exit 1) and says so. `autosize=2` is UNDET and
  forwarded, with its promotion trigger in the tool's README. Two-sided
  calibration ships with it (`--selftest`: 3 known-true, one per mode, 2
  known-false, plus an undeclared-closes-nothing check). Field baseline: SSLD
  報告版, 248 frames — 15 FAIL, every one of them the page title colliding with
  the block below; the other 57 findings were chrome. Read that rate beside its
  ruler: undeclared it reads as 29 % broken, which is the instrument's scope
  and not the deck's condition. Review-when: PowerPoint's autofit behaviour
  changes, or python-pptx starts reconciling autofit height at write time —
  today the height python-pptx WRITES is not the height PowerPoint uses (a
  stored 374.4 pt textbox collapsed to ~93 pt on first text touch, measured
  2026-09-10), and a gate reading stored geometry rules on a discarded number.
- **CJK runs carry a language, and no wrapped line opens with a closing mark**
  (open-slide-borrow pilot 2026-09-29, seen twice before the cause was
  isolated). A run with no `lang` is laid out by Latin rules — no kinsoku — so
  ，、。 can start a line; `lang="zh-TW"` alone fixes it (`eaLnBrk` /
  `hangingPunct` alone do not). Builders set `lang`/`altLang` on every run
  (the source environment's asset-library deck builder, `_set_font`; not shipped here). Where a line breaks is known only to
  PowerPoint, so the gate reads its layout:
  a source-only line-start gate (does not ship here), run as `<deck>` (COM `TextRange.Lines`,
  two-sided width-sweep controls every run; exit 3 = uncalibrated, no ruling).
  Presentation class blocks on a hit; conclusion reports it once.
- **Visual acceptance is a render loop, not a claim**: export slides to PNG
  via PowerPoint COM (`SaveAs(dir, 18)`; filenames are locale-dependent —
  投影片N.PNG on zh-TW systems) and eyeball for orphan wraps, overlaps
  (tables AUTO-GROW on wrap and cover fixed-y content below), and font
  fallbacks. Measure image aspect ratios (PIL) BEFORE computing layout —
  a guessed aspect is how stacked figures overflow the slide.
- Unzipping/inspecting pptx: use a Python script file — PowerShell 5.1 lacks
  `System.IO.Compression.ZipFile` by default, and inline `python -c` with
  CJK/quotes breaks in PowerShell.
- **Speaker notes are part of the emitted deck, and the usual text gate does not
  read them.** A helper that walks `slide.shapes` sees every table cell and text
  frame and zero notes; the rendered PNGs a human reads do not show notes either.
  So a deck can pass a language gate, a markup gate, a page-by-page model read
  AND an external review with the same content unexamined in all four —
  measured 2026-09-13 (SSLD T01): 24 of 26 notes carried English source spans
  through a full green board, found only by an independent audit reading the
  builder's call graph. Any gate whose property is about TEXT walks
  `slide.notes_slide.notes_text_frame` as well, and its control writes a note
  (a layout function usually does not write notes — the builder does, so a
  control that only calls the layout has no note to judge and passes hollow).
  Where a note legitimately holds foreign-language text — a verbatim evidence
  span, which must stay in its source language or it is not verbatim — declare a
  quotation frame and gate the FRAME, never exempt the notes.
- **A layout's degradation policy is inherited with it, and there is usually more
  than one path.** Borrowed layouts degrade silently in kind-specific ways: a
  figure+table layout drops table ROWS, a full-width table layout shrinks the
  FONT. Failing the build on the first leaves the second unmeasured, and its
  zero reads as safety when it means the check cannot reach those pages. Measure
  degradation on the EMITTED file (smallest run size per table, rows present per
  table) where every path has already landed, and enumerate which layout kinds
  each page uses before believing a count.
- **Content the layout never reads is invisible to every gate that reads the
  emitted file** (SSLD T01 2026-09-13: the cover's three authored lines — a stats
  line, a purpose line, a date — were dropped by a layout function that does not
  look at those keys, and no gate could see it because the text is not in the
  .pptx at all). A content layer that hands a dict to a layout layer therefore
  checks the contract at the PRODUCER: derive the consumed key set from the layout
  functions' own source, diff it against the authored keys, and fail on an
  authored-but-unread key — with a control that adds one. The general form outlives
  pptx: wherever a producer emits fields a consumer may silently drop, the
  emitted-artifact gate is structurally blind and the check belongs upstream.
- **A fixed-height band is a carrier choice, not a size to negotiate.** When a
  line no longer fits its band (measured need 0.69 in against a 0.5 in sentence
  band), move that content to a carrier that grows — a table row, a conditions
  page — rather than enlarging the box or shrinking the type: the band's height
  is load-bearing for every other page built by the same layout.
