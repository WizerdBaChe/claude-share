# pptx-edit-headroom

Does this deck survive the reader's own one-line edit?

An editable deck is delivered so a human can edit it. Every check we had ran on
the deck standing still — width estimators at build time, the orphan-wrap rule,
the PowerPoint COM render of the deck *as built*. None of them measured what
happens the moment its reader adds a line, which is the entire point of shipping
an editable file rather than a PDF.

Borrowed 2026-09-10 from SlideWeave (`bobyu89/codex-ppt-style-expanded`), whose
review step says: add one line to a representative page and confirm reflow.
Adapted from a spot check into a per-frame gate, because "representative page"
is a position predicate and positions move as a deck grows.

## What it does

Per text frame, on a temp copy (the delivered file is never touched):

    duplicate the frame's own last paragraph  ->  re-measure  ->  restore

The duplicated line is self-similar, so the probe scales with the frame and
carries no locale of its own — a fixed probe sentence made narrow footers look
catastrophic and wide bodies look safe.

Three determinable breaks:

| mode | when |
|---|---|
| `CLIP` | an `autosize=none` frame now lays out text taller than its inner height — the reader's line is invisible |
| `ESCAPE` | a growing frame (`autosize=shape-to-fit-text`) grew off the slide |
| `COLLIDE` | a growing frame — or a table, whose row heights recompute — grew into a shape it did not touch before |

Determination is PowerPoint's own layout engine (`TextRange2.BoundHeight`, and
`Shape.Height` after the edit), never an estimator.

## Usage

```powershell
python headroom.py deck.pptx --content "TextBox 2$" --content "body-.*" [--json out.json]
python headroom.py --selftest     # two-sided calibration, 5 controls
```

Exit `2` = a declared content frame breaks · `1` = findings but no roles
declared · `0` = clean.

**`--content` is required for the gate to close anything.** Whether a frame is
body content or chrome is not something this instrument can determine — a page
number and a paragraph are both text frames, and a reader never extends a badge
pill. So the build declares the content frames by shape-name regex; everything
else is still measured and printed as `INFO`. An undeclared run reports `WARN`
and says so — it never passes silently.

## Measured facts this is built on (2026-09-10, Office 16 + PowerPoint COM)

- **For autofit shapes, the height python-pptx wrote is not the height
  PowerPoint uses.** In an SSLD report deck a stored
  374.4 pt textbox collapsed to ~93 pt the instant its text was touched. A gate
  reading stored geometry would rule on a number PowerPoint had already
  discarded — hence the settle pass before any baseline is taken.
- **`TextRange2.Characters(start, length).Delete()` raises "collection not
  supported"** under late binding, so whole-text assignment is the restore
  primitive (it doubles as the settle touch).
- Not determinable here, reported `UNDET` and forwarded: `autosize=2`
  (shrink-text-to-fit) absorbs the line by scaling the font, and the scale lives
  in `a:normAutofit/@fontScale`, off the COM object model; shapes nested deeper
  than one group level. **Promotion trigger** for the first: the first deck
  family that actually ships `autosize=2` frames — then read `fontScale` out of
  the saved package and FAIL below that family's font floor.

## Calibration

`--selftest` builds a control deck and requires all five to behave:

- 3 known-TRUE, one per mode (a packed fixed frame, a growing frame on the
  bottom edge, a growing frame with a neighbour below) — all must FAIL;
- 2 known-false (a roomy fixed frame, a growing frame with the slide below it) —
  must stay silent;
- plus the severity check: the same deck run *undeclared* must close nothing.

A one-sided calibration would score 100 % on a gate that rejects everything.

## Field baseline

One SSLD report deck — 18 slides, 248 frames measured,
72 findings:

| class | count | verdict with roles declared |
|---|---|---|
| page title colliding with the block below | **15** (of 18 slides) | FAIL — the real finding: a longer title is the likeliest reader edit |
| badge / button pills clipping | 22 | INFO |
| header strip growing into the title | 17 | INFO |
| page-number footer leaving the slide | 18 | INFO |

Read the rate beside its ruler: undeclared, this deck looks 29 % broken; the
frames a reader actually extends put it at 15 slides with one real defect.

Rule this serves: `~/.claude/rules/office-deck-deliverables.md`.
Review-when: PowerPoint's autofit behaviour changes, python-pptx gains an API
that reconciles autofit height at write time, or `Characters().Delete()` starts
working under late binding — any of those turns a measured fact above back into
a guess.
