---
paths:
  - "**/*.{html,htm}"
  - "**/render_story.py"
  - "**/render_onepager.py"
  - "**/build_deck*.py"
  - "**/build_dossiers.py"
  - "**/build_pack.py"
  - "**/build_textbook.py"
  - "**/*shell*.html"
---

# Coded references and symbols in human-facing deliverables

Sunk from a user-named failure class (2026-08-31, SSLD deck UAT): a deliverable
whose slide 1 said "P1 設計點 FAIL" before the reader ever met P1, and threw
θ_c / g2 / α around undefined. The user flagged both as recurring deliverable-level
defects, not one-off typos. Index line lives in `CLAUDE.md`; review-when: the
delivery machine's display or its scaling changes (the measured 2560×1440 @
AppliedDPI 144 → ~1707×830 below becomes wrong, and the page-class widths with
it — re-measure, never re-infer), or a page class is added to the source-only
page-class registry (not shipped here) without a width allocation here. The
define-before-use and hover-card properties rest on nothing outside the repo and
do not expire. A date is not a trigger: this line replaced "review 2027-02" on
2026-09-08 (ES-3).

**Asset property — a human-facing HTML deliverable (deck, report, dashboard-doc)
must not contain a coded ID or symbol whose definition the reader has not been
given a path to.** Three layers, cheapest first; the first is mandatory, the
other two whenever the document has ≥ ~5 coded IDs or any symbol vocabulary:

1. **Define-before-use (content, no tech):** conclusion-first cover carries a
   one-line legend strip of the ID families; a nomenclature slide/section
   (coding-system table + symbol diagram + operating hints) sits before content;
   the FIRST body-text mention of an ID carries an inline gloss —
   "P1（面內兩鏡，現行）", not bare "P1". An ID you cannot define in one line
   should not appear in body text.
2. **Registry-driven hover cards + jump/return:** a REFS/SYMS JS registry feeds
   a text scanner; tokens get dotted underlines, ~350 ms hover definition cards
   (Wikipedia page-previews pattern), click-to-jump to the defining slide, and
   Backspace-return (kills the jump-around cost of plain anchors). Mark
   high-frequency abbreviations glossary-only (`n:1`) so pages don't drown in
   dotted noise.
3. **Global glossary overlay** (G key): full listing incl. glossary-only
   entries, rows jumpable.

**Do not reinvent:** a reference implementation lives in the source
environment's asset library — CSS + chrome + mechanism JS verbatim from the UAT'd SSLD deck,
sample slides + fill-point comments, README with the five measured pitfalls
(uppercase turns µm into ΜM; hardcoded page numbers rot on slide insertion —
name pages, renumber via JS; SVG label spacing budget; abbreviation-decoration
noise; focusin doesn't fire in background tabs — test artifact, not a bug).
Native alternative when single-file compat is not required: Popover API
(Baseline 2025) + CSS anchor positioning (Baseline 2026).

**Asset property — one slide is one screen** (sunk 2026-08-31 from a user
report: "尺寸不對，預設反而超出版面，每一個 page 都要滑一下才能看完整"; measured
14 of 18 slides overflowing at 1280×610). **A slide-style HTML deliverable must
not present a page whose content exceeds the viewport, and when it cannot fit
one, it must say so rather than clip.** The root cause generalises past decks:
**`max-width` on media is not a layout constraint** — bind width only and the
element's height is set by column width, decoupled from viewport height. Three
stages, each engaging only when the previous cannot cope: (A) CSS — media
blocks become flex items that absorb leftover height (`flex:1 1 auto;
min-height:0` on the block, `flex:0 1 auto` + `object-fit:contain` on the
image), text blocks never shrink; (B) JS — wrap each page's content and
uniformly `transform:scale()` it, floored at a legibility MIN_SCALE; (C) JS —
below the floor, make that page scrollable and show a banner naming it. Give
media a `min-height` floor so stage A cannot shrink a figure to invisibility
(that is a second silent failure), gate strict mode behind a JS-added class so
a JS-dead page keeps degrading to a scrollable document, switch strict mode off
on phone-size viewports (otherwise every page carries a warning), and put
`min-width:0` on grid/flex children so `white-space:nowrap` values cannot force
a horizontal scrollbar. Reference implementation and the measured before/after
live in the source environment's asset library (README §版面吻合).

**Reference viewports are measured, never guessed** (same round): the first
threshold was inferred from "1080p at 150%" and forced eight unnecessary page
splits; the delivery machine actually reports 2560×1440 @ AppliedDPI 144 →
logical 1707×960 → ~1707×830 maximised. Read the real geometry
(`System.Windows.Forms.Screen` + `HKCU\...\WindowMetrics\AppliedDPI` on
Windows), subtract taskbar and browser chrome, and hang a `review-when` on the
screen or its scaling changing. Report smaller windows as advisory rather than
failing them.

**Hard gates beat proof-reading** (added after a second UAT caught silent
terminology drift on the load-bearing concept — 曲面鏡 vs 凹面鏡): wire into the
deliverable's build (a) a canonical-terminology lint (forbidden variants +
required-presence) run over ALL sibling deliverables with one ruler, (b) a
law-of-reflection (or equivalent domain-law) check on schematic diagram
coordinates via an embedded GEOM-CHECK JSON block, and (c) when the deliverable
ships in multiple editions (technical / audience / summary), a shared-value gate
asserting every load-bearing audited number appears VERBATIM in every edition —
paraphrased editions are where numbers silently drift. Each gate carries an
injected-violation positive control that runs EVERY build. Reference: the SSLD
deck's build_deck.py gates (term / geom / value), summarized in that
implementation's README.

**A text gate cannot see layout** (2026-08-31: the sizing defect walked past
term/geom/value because all three read text). Add (d) a **measured fit-gate**:
the build drives a real headless browser over the BUILT files and calls the
page's own `window.__fitReport()` at each reference viewport. Playwright's
Python package is a few MB and the browser usually already exists under
`%LOCALAPPDATA%\ms-playwright` — check before pricing it as a heavy dependency.
Two-sided calibration every run: a known-FALSE injection (a 4000 px block must
be caught) AND a known-TRUE one (a nearly empty slide must pass) — with only
the first, a reject-everything gate scores 100%. When the instrument is
unavailable, **downgrade and forward** with a loud warning; a gate may only rule
on what it can determine. And (e) when one engine is shared across editions and
an extracted vault asset, assert the shared block is **byte-identical** across
all of them, with a one-character-mutated copy as the positive control —
hand-porting is the drift source.

**No gate reads a SENTENCE, so the delivery carries a reader pass** (2026-09-10,
SSLD T56): the gates above bind numbers to sources, terms to a canon, blocks to
byte-equality — none of them has an object for whether a claim built out of
those pieces holds together. A page whose every number was registered shipped
reading 「最大的相對差是 6.489 %，遠小於 0.5 % 的判定門檻」 with 18 page gates and
52 figure gates green. So: **a human-facing deliverable claimed "gates pass"
ships with a model read of the RENDERED reader text** — strip the markup, read
what the reader reads, and check the claims against each other and against the
instrument's own record; state in the delivery that the pass was done and what
it named. This is the prose twin of `rules/figure-self-read.md` and neither
replaces the user's own confirmation. Two recurring shapes to look for: a
comparison whose two halves come from different classes (a max over a union
scored against one member's threshold), and a number the instrument reports as
NOT agreeing that the prose summarises inside a clean sweep.

**Controls belong on the load-bearing path.** Same round, a sibling calculator
shipped a physically impossible number with every control green, because no
control exercised the code path that produced the headline value. When adding a
control, name the path the answer travels and put the control on it; add a
domain invariant (energy conservation, monotonicity, a conserved total) asserted
over EVERY emitted value, not over a sample.

Audience/explanatory edition pattern (user-defined 2026-08-31, SSLD): "簡易版"
means ADD an explanation layer, never cut content — same slides, same numbers
(value-gated), plus visually-distinct guide blocks: 白話導讀 (plain-language
what/why), 這張圖怎麼看 (figure walkthrough), 口頭這樣說 (a quotable spoken
one-liner per key slide, so the owner can present it to peers without the
deck). Declare on the legend page that the added layer is the only delta.
Scope: this is the DECK/slide edition pattern. A diagram-carrier
deliverable's audience version is a presentational REDRAW instead
(audience-fit A1, `skills/audience-fit/references/presentational-view.md`)
— this pattern never overrides that form choice (2026-08-31: a
same-diagram + guide-layer edition was rejected as the wrong output).

**Width property — the page uses the width it is given** (sunk 2026-09-04 from
a user report spanning the SSLD textbook / dossiers / discussion pack and the
paper-story one-pages: 60–69 % fill at 1707×830, right void 439–652 px; the
generator scripts in this rule's `paths:` are listed because telemetry showed
the `*.html` glob never fired while those scripts emitted the pages; diagnosis
recorded in a dated source-only note, 2026-09-04). **A human-facing HTML
deliverable must not carry a left-anchored cap** — a container or a painted,
row-alone block capped in width and hugging the left edge. Each page declares
`<html data-page-class="…">`; the class rows (document-short centred &
symmetric · document-long / deck / tool / dashboard fill ≥ 85–90 % · diagram
centred-or-fill) and their thresholds are DATA in a source-only config file
(not shipped here), and the gate (a source-only build script, not shipped
here) runs with two-sided controls at the measured reference viewports and may only WARN on a page whose
class it had to infer. Generators run it on the BUILT files beside the
fit-gate and print the measured reach next to the fit result. The reading
measure (~65 ch) is achieved by column structure — a fluid main column plus a
`data-rail` aside, grids — never by capping one column; width is allocated in
fr / % / cqw / clamp and pixels are reserved for intrinsic sizes. Reference
implementations: long document = the SSLD project's own textbook shell
(fluid main + a rail-style 本節速查 aside, hidden below 1500 px and in print;
not shipped here); deck = the source environment's asset library reference
implementation (text blocks uncapped, `data-page-class="deck"`).

Interaction chrome standard carried by the same asset (user-accepted 2026-08-31):
←/→ paging, M TOC, counter + progress bar, print CSS, JS-dead degradation to a
scrollable document, phone-width single column, offline single file.

**Asset property — a SHARED shell's text is an interface, and its consumers are
not visible from inside it** (L-049, folded here 2026-09-08; measured on the
SSLD `shell.html` fix for L-048: three refusals in one round, ~40 minutes of
rebuild cycles, each from a consumer the edit never mentioned). The three
consumer classes, none of which reads the DOM:

- **adapters that patch the shell by exact string.** `build_dossiers.py`'s
  `_build_shell_from` anchors on literal lines with a count assertion; appending
  one line to that tail made the anchor 0-count and the build refused.
- **gates that scan the emitted bytes with no parser.** `link_gate` reads
  `href="…"` out of the text, so a link built as a JS string
  (`'<a href="#' + id + '">'`) is read as a dangling anchor. Emit links to
  gate-scanned documents with `createElement` + `setAttribute`, never
  string-concatenated markup.
- **the user's own open files.** A builder that rewrites every product
  unconditionally aborts the whole pack with `PermissionError` when a PPTX is
  open in PowerPoint — write only what changed, and say which file is locked.

So before editing a file matched by this rule's `**/*shell*.html`: grep the repo
for its path and run EVERY builder that names it, not only the one being fixed.
The shell renders correctly in the browser either way; that is precisely why
this failure is silent until a downstream build refuses.
