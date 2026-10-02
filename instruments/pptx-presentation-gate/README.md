# pptx-presentation-gate

Rule P3 (flat and clean) of `rules/office-deck-deliverables.md` §Presentation-class content, checked on the EMITTED
`.pptx`. Severity, the theme-inheritance trap and the UNDET scope are in the `presentation_gate.py` docstring.

```
python presentation_gate.py deck.pptx [--class presentation|conclusion] [--max-colours 3] [--json out.json]
python presentation_gate.py --selftest   # 8 cases: clean, inherited shadow, gradient, conclusion downgrade,
                                         # explicit shadow, bevel, 5 colours (WARN), 6 greys (known-false)
```

Field baseline (2026-09-20, all PASS). Read the ruler beside the zero:

| deck | slides | shapes (theme-styled) | max non-grey colours / slide | verdict |
|---|---|---|---|---|
| SSLD proposal, lab template (black/white/grey ruling) | 19 | 174 (8) | 0 | PASS: agrees with the ruling (known-true point) |
| PaperSurvey Mu 2020 lab deck (user-final edition) | 24 | 85 (17) | 3 | PASS |
| SSLD report deck | 18 | 139 (31) | 3 | PASS |

**Why P1 (figure-led) is not in this tool.** A figure-area share was built and removed on 2026-09-20. The user ruled
that 「半頁」 is a content-density limit: more than 50 % of a page's narrative being information a figure could
carry makes the page 過重. That is not an area ratio, and accepted decks measure a median of 23–38 % figure area
anyway. Which sentences could have been a figure cannot be determined from the package, so P1 stays a reader pass.

The builders behind all three decks already set `shadow.inherit = False`. An untouched python-pptx `add_shape()`
inherits the default theme's outer shadow (effectRef idx 2) and fails: selftest case `default-add_shape`.

Review-when: python-pptx changes its autoshape `p:style` default, or a template theme whose fillStyle / effectStyle
lists are not three entries long ships through a builder.
