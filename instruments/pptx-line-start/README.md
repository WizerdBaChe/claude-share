# pptx-line-start

Does any wrapped line in this deck open with a closing punctuation mark (，、。；：！？）」…)?

## Why a separate gate

Where a line breaks is decided by PowerPoint's layout engine, not by the file:
width estimators, `presentation_gate` (static XML) and `headroom` (height and
collision) are all blind to it, and the eye catches it only on the page where it
happens to land. Found twice on the open-slide-borrow pilot (2026-09-29, 極簡 p3
and 繁複 p2) before the cause was isolated.

**Cause (measured, one frame, four variants):** a run with no `lang` attribute
is laid out with Latin line breaking, so no kinsoku. `lang="zh-TW"` alone
removes the line-start mark; `eaLnBrk` / `hangingPunct` alone do not. The
builder fix is one line per run — AssetVault `pptx-deck-builder` `_set_font`
carries it since 2026-09-29.

## What it does

Opens the deck read-only through PowerPoint COM and walks every text frame,
grouped shape and table cell. A line is a hit when it is not the first line of
its paragraph (`TextRange.Lines(j).Start` is not a paragraph start) and its
first character is a closing mark. Each hit prints slide, shape name, line
number and the run's `LanguageID` — `-2` (mixed / unset) is the cause above.

## Calibration, every run

One CJK sentence laid out at a sweep of widths (2.0–5.0 in, 0.07 in steps):

| control | run language | must give |
|---|---|---|
| known-false | stripped | ≥ 1 hit (22 measured 2026-09-29) |
| known-true | zh-TW | 0 hits |

If either misbehaves the deck's hits are listed with no ruling (exit 3). Real-
deck check at birth: the pilot's 繁複 edition with every `lang` stripped gives
exactly the original defect (slide 2, `conclusion3`, line 3); as built, 0.

## Usage

```powershell
python -X utf8 line_start.py deck.pptx [--json out.json]   # 0 clean · 1 hits · 3 uncalibrated
python -X utf8 line_start.py --selftest                       # the two controls only
```

Needs PowerPoint (Windows) and python-pptx (for the controls). The delivered
file is opened read-only and never changed. A deck's CLASS decides severity:
presentation blocks on a hit, conclusion reports it once
(`rules/office-deck-deliverables.md`).

review-when: PowerPoint starts applying kinsoku to runs without a language, or
python-pptx starts writing `lang` itself — either turns the builder fix and
this gate's known-false control into dead weight (the control would stop
firing, and the gate says UNCALIBRATED, which is the signal).
