---
paths:
  - "**/figs/**"
  - "**/*plot*.py"
  - "**/*fig*.py"
  - "**/native*/**"
  - "**/*.mph"
review-when: a tool this rule covers loses headless native export (e.g. a COMSOL/MPh upgrade breaks the `Image` export node), or the user rules that a figure class may ship redraw-only
---

# Native render first: a tool result's figure ships its tool's own picture

User ruling 2026-09-19 (SSLD T14 fold2d): 「各種未來相關出圖（同時作為其他自動化工具參考的話）都要跑原生，
先出完，判定效果不好也留著再跑自己的腳本，一起呈現出來並記錄」. Index line lives in `CLAUDE.md`.

## The property (asset class: a figure that depicts a result computed by a tool with its own renderer)

Tools in scope — any solver / CAD / layout / optics tool this machine drives headlessly that can export its own
view: COMSOL (`Image` export node), Lumerical / Tidy3D / MEEP plotting of their own monitors, Zemax / Optiland /
rayoptics layout plots, FreeCAD TechDraw, KLayout / gdsfactory layout render, Blender scene render, and any future
tool with an export-image call.

1. **The native render is emitted FIRST and always kept.** Same expression / monitor / object the gate read, the
   tool's own colour table and axes. Judged weak (full-domain window, SI labels, no CJK, logo, fixed scale) → the
   weakness is written down beside it; the file is never dropped or replaced.
2. **A self-written redraw (Matplotlib, SVG, PPTX shapes) is ADDITIONAL**, made only for a named need (analytic
   overlay, shared multi-panel layout or normalisation, CJK annotation, a quantity the tool cannot plot). It is
   drawn from the same arrays the gate ruled on (`rules/figure-self-read.md`).
3. **Both are presented together** (side by side on a page/slide, or adjacent entries in the figure viewer), each
   captioned native vs redraw, and the record (round record / verify JSON / README) states per figure: native
   file, redraw file (or "none"), the named need for the redraw, and the native's noted weakness.
4. A tool with NO native export (e.g. a self-written BPM) says so in its generator docstring; the redraw is then the
   only figure and is labelled as such.

## Why (the instance that paid for it)

SSLD T14 shipped the COMSOL fold2d and axisymmetric field maps as Matplotlib redraws only; the process record said
「沒試原生」. Root cause: the COMSOL skill's figure card defaulted audience figures to the redraw route, the arrays
were already in Python for the gates, and the choice was never surfaced. The 09-18 native fix covered only the
figures literally asked for and missed fold2d. Loading a solved model to add Results nodes costs ~1 min, no re-solve.
