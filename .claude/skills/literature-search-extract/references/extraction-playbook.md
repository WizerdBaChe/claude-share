# Extraction Playbook — worked examples per information-need type

Companion to SKILL.md P4. For each information-need type in the P1 table, this file shows
WHERE to extract from, HOW to record the result, and a wrong-vs-right contrast targeting
failure mode #3 (generic summarization instead of targeted extraction).

> **All sources in the examples below are FICTIONAL placeholders** (e.g. "Chen 2023").
> They illustrate output shape only. In real runs, every citation must resolve to a real,
> verified identifier — see failure mode #1.

Conventions used throughout:
- Every extracted item carries `(Author Year, locator) [access-tag]`.
- `[read from figure]` — value estimated from a plot, not a printed number.
- `[not stated]` — information required by the target list but absent from the source.
- `[synthesis]` — your own inference, derived from cited material and labeled as yours.

---

## 1. Definition / concept / taxonomy

**Where it lives.** Review-article Introductions (they define terms to frame the field)
and textbook chapter openings / glossaries (most stable, most citable). Research-paper
Introductions define terms only as needed for that paper — treat those as *usage*, not
*definition*, unless the paper is the term's origin.

**Procedure.**
1. Prefer the canonical textbook or a highly-cited review for the base definition; quote
   it (short, marked, with locator) because exact wording is load-bearing for definitions.
2. Collect definitions from 2–3 independent sources before writing anything.
3. If sources disagree, DO NOT merge into one smooth definition. Present each version
   with its source, then state the scope of disagreement.
4. For taxonomies: extract the classification criteria (what axis splits the classes),
   not just the class names — names without criteria are unusable to callers.

**Handling multi-source inconsistency (worked example).**

> **Definition of "propagation length" (L_spp):**
> - "the distance over which the SPP intensity decays to 1/e"
>   (Maier-style textbook, Ch. 2 §2.3) [partial]
> - "the 1/e decay length of the field amplitude, i.e. twice the intensity decay length"
>   (Chen 2023 review, §1.2) [full]
> - **Conflict:** the two definitions differ by a factor of 2 (intensity vs field
>   amplitude convention). Both are in active use; any numeric comparison across papers
>   must first identify which convention each paper adopts. → recorded in `confidence`.

**Wrong vs right.**
- ✗ Wrong: "Propagation length is how far an SPP travels before dying out, typically
  tens of microns." — no source, no convention, folds a typical value into a definition,
  and silently averages conflicting conventions.
- ✓ Right: the worked example above — each definition quoted/paraphrased with locator and
  access tag, the factor-of-2 conflict surfaced as a finding.

---

## 2. How a method / protocol works

**Where it lives.** Methods section for the skeleton; **Supplementary Information for the
parts that make it actually reproducible** (exact recipes, instrument settings, code).
Textbook worked-example sections give the pedagogical version — good for understanding,
rarely sufficient for reproduction.

**Procedure.**
1. Reconstruct the method as an ordered step list, each step with its locator.
2. For each step, extract: inputs, action, parameters/settings, outputs.
3. **Gap-mark aggressively**: anything reproduction would need but the paper does not
   state gets an explicit `[not stated]` entry — a step list that looks complete but
   silently papered over gaps is worse than one with visible holes.
4. Check Supplementary before declaring a gap; papers routinely push critical details
   there.
5. Also extract the method's stated preconditions (sample requirements, regime of
   validity) — see §4; a method summary without its preconditions is incomplete.

**Worked example (method summary fragment).**

> **Template-stripping fabrication of ultrasmooth Ag films** (Park 2022, Methods §2.1 +
> Suppl. S1) [full]
> 1. Deposit Ag on freshly cleaved mica template — thickness 200 nm, e-beam evaporation,
>    rate 0.5 Å/s (Suppl. S1).
> 2. Bond glass backing with epoxy — epoxy type `[not stated]`; curing 24 h at room
>    temperature (Methods §2.1).
> 3. Mechanically strip template immediately before use — maximum storage time before
>    stripping `[not stated]`, though Discussion §4 implies films degrade within days.
> - **Reproduction gaps:** epoxy identity; chamber base pressure; mica cleaving method.

**Wrong vs right.**
- ✗ Wrong: "They used template stripping to make smooth silver films and got very low
  roughness." — abstract-level paraphrase; nothing here enables reproduction, checking,
  or comparison. Could have been written without opening the Methods section.
- ✓ Right: the step list above — ordered, parameterized, per-step locators, gaps marked.

---

## 3. Quantitative values / parameters

**Where it lives.** Results tables first (exact printed numbers), then figures (estimated
numbers), then abstract headline numbers (rounded, cherry-picked — use only to
cross-check, never as the primary extraction). Textbook data tables and appendices for
reference values.

**Procedure.**
1. Extract as a tuple: **value + uncertainty + unit + measurement/computation conditions
   + locator**. A number missing any element is an incomplete extraction (failure
   mode #4).
2. Printed table value → cite the table. Value read off a plot → tag
   `[read from figure]` and state your estimated read-off precision (e.g. "±5 μm from
   axis gridline spacing"). Never present a figure-read value with more significant
   figures than the plot supports.
3. **Unit conversion**: if the deliverable needs a different unit than the source uses,
   record BOTH — original value as printed, converted value, and the conversion factor —
   so the caller can audit: `22 μm (as printed) = 2.2×10⁻⁵ m [converted, ×10⁻⁶]`.
4. When multiple sources report the same parameter, tabulate them side by side with
   conditions; differences in conditions usually explain differences in values — say so
   only with `[synthesis]` or a source that says it.

**Worked example (parameter-sheet rows).**

> | Parameter | Value | Conditions | Source + locator |
> |---|---|---|---|
> | L_spp (Ag/air) | 22 ± 3 μm | λ = 633 nm, template-stripped film, intensity 1/e convention | (Park 2022, Table 2) [full] |
> | L_spp (Ag/air) | ~35 μm `[read from figure]` (±5 μm) | λ = 785 nm, single-crystal flake | (Chen 2023, Fig. 4b) [full] |
>
> The two values are NOT in conflict: different wavelength and film quality
> `[synthesis]`; Chen 2023 §3.2 attributes flake values exceeding evaporated-film values
> to grain-boundary scattering.

**Wrong vs right.**
- ✗ Wrong: "Silver SPPs propagate about 20–35 microns." — no wavelength, no film type,
  no convention, no per-value source; merges two differently-conditioned measurements
  into one range. This is the "number stripped of its conditions" landmine.
- ✓ Right: the table above — every value a full tuple, figure-reads tagged with
  precision, apparent disagreement explained with labeled synthesis.

---

## 4. Validity limits / assumptions

**Where it lives.** Discussion and Limitations sections for what the authors admit;
Methods for implicit assumptions (what they controlled reveals what they assumed
matters); textbook derivation preconditions for theory. This is the extraction callers
like scientific-research-guide need MOST and papers advertise LEAST.

**Procedure.**
1. Extract stated limits verbatim-ish (paraphrase with locator; quote if the hedging
   wording itself matters).
2. Separate three categories: (a) assumptions the method requires, (b) the tested/valid
   range, (c) known failure modes the authors report.
3. **Unstated limits**: you may infer limits the authors did not state — e.g. "all
   samples were measured at room temperature, so temperature dependence is untested" —
   but ONLY tagged `[synthesis]` and only when derivable from cited material (here: the
   Methods' sample list). Never present an inferred limit as an author statement.
4. Absence of a Limitations discussion is itself a finding — record it.

**Worked example.**

> **Validity limits of the coupled-mode model in Park 2022:**
> - Stated: model assumes gap width ≪ λ; authors report breakdown for gaps > 100 nm
>   (Discussion §4.2) [full].
> - Stated: derivation assumes lossless dielectric cladding (Theory §3, Eq. 7
>   precondition) [full].
> - `[synthesis]`: all validation was at λ = 633–785 nm (Methods, Table 1); applicability
>   in the near-IR is untested by this paper — the paper does not claim it either way.

**Wrong vs right.**
- ✗ Wrong: "The model works well and matches experiment." — extracts the claim and
  discards the limits, which were the extraction target.
- ✓ Right: the list above — stated limits with locators, inferred limits explicitly
  tagged `[synthesis]` with the evidence they derive from.

---

## 5. State of the art / who did what

**Where it lives.** Related Work sections and, better, recent review articles (they do
the mapping for you and are citable for the map itself). Latest-edition textbook survey
chapters for slower-moving fields.

**Procedure.**
1. Anchor on 1–2 recent reviews; extract their field map (groups/approaches, key papers
   per approach) citing the review as the source of the map.
2. Attribute each "X was first shown by Y" claim to whoever makes it: if you only know
   it from the review, the tag is `[secondary]` ("Y, as cited in Review Z") unless you
   opened Y itself.
3. Check recency: a 2019 review does not cover 2020+; state the coverage boundary as a
   gap rather than silently presenting an old map as current.

**Wrong vs right.**
- ✗ Wrong: "Many groups have studied this; key advances include A, B and C." — unsourced
  map, no dates, no attribution of who says A/B/C were key.
- ✓ Right: "Per Chen 2023's review (§2, Table 1) [full], three approaches dominate: …
  The review covers work through mid-2022; later work is outside its map (→ gaps)."

---

## 6. Canonical equations / derivations

**Where it lives.** Textbook core chapters (most reliable — derivations are refereed by
generations of readers); paper Theory sections and appendices otherwise.

**Procedure.**
1. Extract the equation WITH: equation number + source, symbol definitions (each symbol,
   from the source's own nomenclature), and the derivation's preconditions (§4 applies).
2. Sign/convention traps: note the source's conventions explicitly (e.g. e^{-iωt} vs
   e^{+iωt} time convention) — cross-source equation comparison without convention
   bookkeeping produces phantom sign errors.
3. Do not re-derive or "fix" a source's equation; if two sources' forms differ, treat it
   as a conflict (§1 procedure) unless one source itself explains the mapping.

**Wrong vs right.**
- ✗ Wrong: reproducing an equation from memory "as commonly written" and attaching the
  nearest textbook as citation — this is fabrication (failure mode #1) applied to math.
- ✓ Right: "Dispersion relation as given in (Maier-style text, Eq. 2.14) [partial]:
  β = k₀√(ε₁ε₂/(ε₁+ε₂)), where ε₁, ε₂ are the dielectric functions of metal and
  cladding (source's notation); assumes a single flat interface and e^{-iωt} convention
  (Ch. 2 §2.2)."

---

## 7. Contradictions / open questions

**Where it lives.** Discussion sections (authors positioning against prior work) and
review-article "future work" / "open challenges" sections. Textbooks rarely carry live
controversies — use reviews.

**Procedure.**
1. A contradiction is only reportable when you can cite BOTH sides with locators.
2. Record each position in its own words (short quote or tight paraphrase), plus any
   third source that comments on the disagreement.
3. Resist resolution: your job is to report that the field disagrees and why each side
   says it's right; picking a winner is allowed only as clearly-tagged `[synthesis]`
   with the reasoning shown, and only if the caller's `purpose` needs a recommendation.
4. Open questions: extract only ones a source explicitly poses; "this seems unexplored"
   from your own reading is `[synthesis]` and belongs in `gaps`.

**Wrong vs right.**
- ✗ Wrong: "There is some debate about the loss mechanism, but it is generally accepted
  that grain boundaries dominate." — resolves the conflict by fiat ("generally
  accepted" with no source) — this is failure mode #5.
- ✓ Right: "Park 2022 (Discussion §4.3) [full] attributes excess loss to grain-boundary
  scattering; Chen 2023 (§3.4) [full] argues surface roughness dominates below 50 nm
  grain size, citing their Fig. 6. No searched source reconciles the two → recorded as
  a conflict in `confidence`."

---

## Cross-cutting checklist (run before P5 for every source)

- [ ] Every extracted item has a locator and inherits the source's access tag.
- [ ] Every number is a full tuple (value, uncertainty, unit, conditions).
- [ ] Figure-read values tagged `[read from figure]` with read-off precision.
- [ ] Unit conversions show original, converted, and factor.
- [ ] Reproduction gaps and unstated limits marked `[not stated]` / `[synthesis]`.
- [ ] No conflict silently resolved; all conflicts routed to `confidence`.
- [ ] Nothing in the deliverable could have been written from abstracts alone — if a
      section could, redo P4 for it.
