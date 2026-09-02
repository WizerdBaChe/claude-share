# Domain Routing Manifest

> Single source of truth for **which domain files exist** and **when to load each**.
> Gate A Step 0 (SKILL.md) consults this file before loading any Layer-B content.
> Keep it terse — this file is read on every domain-triage turn. One row per file.

## How Gate A uses this manifest

1. **Identify domain** — match the user's field against the `base` rows' triggers.
2. **Load the base profile** — always load the matched domain's base profile alongside
   the tier framework. Its standing triggers — Node 6's `Trigger condition` rows (primary),
   Node 1's constraints + Decision point, the Node 2/4 warning columns, and the Conflict
   Notes questions (`domain-expansion-guide.md` §3.6) — become standing if-then rules for
   the whole turn.
3. **Scan sub-profiles of that domain** — for every `sub-profile` row whose parent is the
   matched domain, check its load trigger against the user's wording. On a match, **load it
   and activate its own standing triggers** (they fire like the base profile's).
4. **Pull references on demand only** — `reference` / `boundary` rows are loaded only when
   the specific topic is explicitly engaged; they carry no standing triggers. A `boundary`
   row's job is to route the user *out* to a sibling domain when they cross the edge.
5. **Fuzzy questions (no literal keyword hit)** — the keyword column is a precision anchor,
   not the whole recall path. Route by the `Covers / role` column plus whatever cluster /
   disambiguation sections you add below, per SKILL.md Step 0's resolution ladder: one candidate →
   load with a stated routing basis; several → ask the disambiguation table's own axis
   question; none → generic framework. Never widen recall by adding broad keywords
   (§ Maintenance). *Authoring consequence*: write `Covers / role` in the asker's frame
   (what the question is about) — it doubles as the fuzzy-routing index.

**How a keyword is compared (the matching rule).** Case-**sensitive** — `TI`, `RIN`, `SPP`
and 35 other short ASCII acronyms match inside ordinary words once lower-cased, measured
2026-08-26 over the eval prompts. Variant-**insensitive** — put both the user's wording and
the keyword into Unicode NFKC before comparing, so the compatibility spellings of one term
are one term: `Bi₂Se₃` = `Bi2Se3`, `Z₂` = `Z2`, `µLED`(U+00B5) = `μLED`(U+03BC), `cm²` = `cm2`,
full-width `Ｂｉ２Ｓｅ３` = `Bi2Se3`. A row therefore lists **one** spelling of a term and
never a variant list — see § Maintenance. `tools/routing_sim.py` implements exactly this.

Type semantics are defined in `domain-expansion-guide.md` §2 (the two-gate decision tree).

## Manifest
**This share ships the manifest FORMAT with no rows.** The source environment's
filled manifest listed its author's own research fields; those domain profiles are
subject-matter knowledge and were excluded from this share (see `README.md` in this
folder). Author your own rows — one per file you actually create. The source's own
cluster, disambiguation and lint-exception sections went with them: each one is a
routing ruling *about those profiles*, and a ruling about files you do not have is
worse than no ruling. Their shapes are described in `domain-expansion-guide.md`.

| Type | File | Parent | Load trigger (keywords) | Covers / role | Active triggers? |
|---|---|---|---|---|---|
| base | `<domain>.md` | — | 5–10 field-identifying keywords a user would actually type | The domain's 7-node base profile | yes (Node 6) |
| sub-profile | `<domain>/<phenomenon_or_method>.md` | `<domain>` | keywords naming that specific phenomenon, method, or material | Specialized branch whose pitfalls fire as standing rules | yes (Node 6) |
| reference | `<domain>/<terminology>.md` | `<domain>` | terms, symbols, abbreviations the field overloads | Look-up material, pulled only when the topic is explicitly engaged | no |
| boundary | `<domain>/<adjacent_field>.md` | `<domain>` | keywords belonging to the NEIGHBOURING field | Routes the user OUT to a sibling domain and corrects false equivalences | no |

Delete the four template rows above once you have real ones. Row-type semantics —
and when a topic deserves a `sub-profile` versus a line inside the base profile —
are decided by the two-gate tree in `domain-expansion-guide.md` §2.

**Only list files that ACTUALLY EXIST.** Gate A will try to load whatever it finds
here; a row pointing at a missing file is a load failure, not a no-op.

## Maintenance

- SKILL.md must NOT hardcode domain file paths — it points here. When you add a domain
  file, add its row here in the same change; that is the only place the load list lives.
- `base` files stay lean (the 7-node profile = the domain's shared core). Specialized
  branches go in `sub-profile` rows, not the base file — see the decision tree.
- **A trigger keyword must be a word the *asking* user would type, not the answer.** Two rejected
  additions from the 2026-08-24 eval pass are worth not repeating: (a) `35.26°` alone was useless
  as a `fiber_chip_passive_alignment` trigger — a user who has made the wedge-half-angle error
  types `54.74°`, never the corrected value — and an English-only phrase does not fire on a
  Chinese prompt, so the Chinese form was added beside it; (b) generic packaging-timeline words
  (`封裝製程`, `封裝前後`, `封裝完之後`) were added to `siph_packaging_reliability` and then
  **reverted**: they matched three sibling profiles' core scenarios verbatim (a V-groove etch-angle
  question says `封裝製程`; a pre/post-attach IL question says `封裝前後`), so the row would have
  over-loaded across the whole cluster. That profile owns qualification and lifetime — a bare
  packaging-timeline word is not evidence of that scope. Where a cross-domain question cannot be
  caught by an honest keyword, let the two profiles' own Cross-Domain Links carry it; that is
  weaker routing but it does not manufacture false loads.
- **A spelling variant is not a broad keyword, and the trade runs the other way.** The rule above
  is about a keyword that means something *wider* than the row's scope. `Bi₂Se₃` beside `Bi2Se3`
  is the same term in a different codepoint: it cannot pull in a question the ASCII form would not
  have pulled in, so it cannot manufacture a false load — it can only recover a miss. User ruling
  2026-08-26: for this class a miss is the worse failure, because the consumer is an LLM that can
  discard an extra file but cannot read one that never loaded. **The fix is the matching rule, not
  the row** — matching is NFKC-folded (see § How Gate A uses this manifest), so list ONE spelling
  and let the fold cover the rest. Hand-listing variants is what the fold replaces: no such list is
  ever complete, and `profile-lint.py` reports a row carrying two spellings of one term as
  REDUNDANT-VARIANT.
- **Recall gaps are found by simulation, not by reading the row.** The 2026-08-26 triage found that
  `topological_insulator.md` had never listed `Bi2Se3` — the domain's single most typed material —
  so eval case 4's prompt matched no base row at all and the Bi₂Se₃ sub-profile was unreachable,
  while the eval's own recorded evidence claimed it loaded. Prose review had passed that row
  repeatedly. `tools/eval-impact.py`'s baseline is what surfaced it; run it after touching a row.

*review-when:* the Step-0 matching rule changes (case sensitivity, folding, or the two-level
scan). All three are stated in § How Gate A uses this manifest and implemented in
`tools/routing_sim.py`; if one moves and the other does not, both this section and the lint
calibration counts in `profile-lint.py`'s docstring are wrong.
