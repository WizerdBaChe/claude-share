---
paths:
  - "**/*.css"
  - "**/*.{scss,sass,less}"
  - "**/e2e/**"
  - "**/*.spec.{ts,tsx,js,jsx}"
  - "**/*geometry*.{ts,tsx,js,jsx}"
  - "**/theme.{css,ts,tsx}"
---

# Visual gates: measure the ink, and survey the class

Written 2026-09-02 from a media-fetch-pipeline UAT round. The trigger is "a
stylesheet or a browser-driven spec is in play", which `paths:` observes
directly, so this costs nothing until it is relevant. Index line lives in
`CLAUDE.md`; review-when: a project adopts a component library that owns its
own control primitives, which changes who is responsible for the first rule.

## The property, not the reminder

**A control's box is not its ink, and a check that measures the box is
measuring something the reader cannot see.** Two shapes, measured, both of
which passed every existing assertion:

- A **ghost box**: a control with no painted border or background contributes
  its padding to `getBoundingClientRect()` and nothing to the picture. A
  column header sat 11px left of the button text below it for a year.
- A **stretched fixed-size widget**: `input[type=radio]` and
  `input[type=checkbox]` paint a glyph of a size the CSS did not choose
  (13px in Chromium). Make one a flex item and the ELEMENT stretches while
  the glyph stays put and centres itself — a radio measured 64px wide and
  88px wide for a 13px circle, which on screen is a circle floating on its
  own line above words that start 25px to its left.

So: text contributes its GLYPH rects; a control contributes its box only when
it actually paints one; and a fixed-size widget must not be stretched at all.
The cheapest structural guard is two lines of CSS —
`input[type=radio],input[type=checkbox]{align-self:start;flex:none}` — which
is inert outside a flex container and makes the remaining defects visible to
any box-based assertion.

## Where the gate points

**A visual gate is a survey of a CLASS, never a witness to one incident.**
The recurring failure is not that gates are missing — it is that each one was
written at the site of the last report and stays aimed there. A panel written
afterwards therefore begins life with zero geometric coverage, and the next
defect is again found by a person.

Two properties of any suite that does browser geometry:

1. The sweep is driven by the app's OWN registry of views (the menu, the
   route table, the category list), so a view added later is surveyed the day
   it is registered rather than the day someone remembers the test.
2. A scope exemption ("buttons only, `<input>` belongs to the settings
   rework") carries the event that retires it. Both halves of that example
   shipped; only the exemption survived.

## What this does not claim

Geometry decides **placement**: is the ink where the box says, is a control on
its label's line, does a column's header sit over its own values. It does not
decide **appearance** — whether the result is legible, balanced or pleasant.
That still ends with a human looking at a picture, and "the geometry suite is
green" is not a substitute for one. Pixels for an appearance claim come out of
process and are delivered to the user; the pane's steady state is hidden and
nobody is asked to front a window.
