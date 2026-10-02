---
paths:
  - "**/figs/**"
  - "**/build_fig*.py"
  - "**/build_sec*.py"
  - "**/m3p/section2d.py"
  - "**/m3p/npr3d.py"
  - "**/m3p/annot.py"
  - "**/m3p/figaudit.py"
review-when: the harness stops rendering PNG/JPG through the Read tool (the visual channel then needs a viewer tool), or a figure generator gains a raster diff gate that names layout classes (the read then narrows to appearance only)
---

# Figure self-read: a rendered figure ships with two channels of evidence

Written 2026-09-10 from the SSLD section-figure round (model3d-pipeline
`m3p.annot` / `m3p.figaudit`). Ten section figures across three rounds carried
0 FAIL from the audit while every one of them showed values 90-115 px from
their dimension line, chains split over two rungs and extension lines growing
out of construction levels. The audit had no word for any of those classes
(`ops/lessons.md` L-044 shape). The model CAN see them: the Read tool renders a
PNG, and the same session's first visual read named all three classes before
touching the code. Nothing had obliged it to look before the user did. Index
line lives in `CLAUDE.md`; mechanism: prose-only (candidate: a PostToolUse hook
that lists the PNGs a `build_*` run emitted and asks for the read record).

## The property, not the reminder

**A rendered figure (PNG/SVG/PDF emitted by a generator) whose delivery says
"pass", "clean" or "0 FAIL" carries two independent channels of evidence, both
named in the delivery or the verify record:**

1. **The instrument's verdict on the EMITTED artifact** (audit, gate, selftest
   with its two-sided calibration) — rules on what it can determine.
2. **A model visual read of the raster**, written as a record: which files were
   read (absolute paths), at what size, and what was seen, ending in either
   `no defect named` or a NAMED defect class per figure. A raster nobody read
   is at rung 0 of `rules/verification-ladder.md` whatever the audit says.

The two channels answer different questions and neither substitutes for the
other: the instrument measures position and crossing to the pixel, repeatably;
the visual read finds the CLASS the instrument has no object for. A visual read
that names a class the audit did not is a gate candidate and is written into
the instrument (rule + injected-fault control) BEFORE the figure ships, or the
gap is declared in the delivery. Neither channel replaces the user's own
appearance confirmation (global CLAUDE.md «When the change renders something a
human looks at»): the read is the model's obligation to look first, not a
licence to claim.

## How a read is done (so it is a record, not an impression)

- Read the PNG the generator wrote, one figure per Read, at its emitted size
  (a contact sheet hides px-scale defects — the thing being looked for).
- Name what was compared: every dimension's value against its own line, every
  extension line's origin against the feature it measures, every chain's
  rungs, every line against the outlines it runs near, every label against
  its leader's end. Vocabulary from the drafting standards the instrument
  cites (ISO 129-1, ASME Y14.5), not "looks off".
- Compare the named defects with the audit's FAIL/WARN list for the same file:
  a defect seen and not listed is the finding; a defect listed and not seen is
  a calibration question for the instrument.
- Write the record where the claim is: the verify JSON beside the figure
  (`visual_read:` field) or the delivery note's evidence list.

## Two clauses the read alone does not supply (SSLD T04, 2026-09-15)

- **A sentence that a figure SHOWS something names the view and axis where it is
  visible.** A multi-view figure can hold a feature in one panel and correctly
  lack it in another; "the refraction is drawn" was true for the side view's y
  and physically absent in the plan view's x, and the user, reading the plan,
  judged the report false (`ops/lessons.md` L-096). Same lesson, content side:
  a schematic convenience (a hold, clamp or fixed reach point) on a quantity a
  model computes must not erase a feature the reader expects from physics (a
  kink at a material interface); an expected feature that is physically absent
  is labelled on the figure.
- **An item kind a wrapper adds at runtime is outside the instrument's object
  vocabulary until the wrapper gates it.** A legend added around a frozen
  label placer kept a green collision gate while leaders crossed it; only the
  read saw it, and three layout patches later the fix was a different
  representation (the key in its own band below the view), not spacing
  (`ops/lessons.md` L-095). The wrapper ships its own read-back of the added
  kind, with a two-sided control, before the figure is called clean.

- **A figure is drawn from the SAME variables the gate ruled on, never from a
  recomputation inside the plotting code** (COMSOL_Test round 24, 2026-09-15).
  A gate used κ = 2·c₂ (PASS) while the plot block still carried the discarded
  −κ draft, so the shipped figure showed the reference parabola inverted
  against the model points it certified. The read caught it after the run;
  the property prevents it: the plot receives the gate's own arrays and
  scalars, and when only the drawing is wrong the figure is regenerated from
  the stored result file, not by a re-solve.

## Extension clause

A new figure class (a new generator, a new style preset, a new artifact kind
such as a plot or a diagram) joins this rule by adding its generator's glob to
`paths:` above and naming, in its verify record schema, the field that carries
the read — a class whose figures cannot carry the record is outside the rule
and says so in its generator docstring.
