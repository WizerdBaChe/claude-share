# Output Templates — one per catalog format

Companion to SKILL.md P5. For each format in the output catalog: field definitions, a
ready-to-copy template, and one filled example row/entry. Ends with a complete result-
contract example for Mode 2 returns.

> **All sources in filled examples are FICTIONAL placeholders** (e.g. "Park 2022") —
> they show shape only. Real deliverables must use verified, resolvable citations.

## Language and Mode rules (apply to every format)

- **Mode 1 / human-facing document** → Traditional Chinese prose and headers; keep
  citations, identifiers, tags, and technical terms in English
  (e.g. 「傳播長度 (propagation length)」, `(Park 2022, Table 2) [full]`).
- **Mode 2 / machine-consumed return** → entirely English; keep the field names and
  column sets EXACTLY as defined here (stable structure is the point — the calling
  skill parses by field name, not by position).
- In both modes: every load-bearing claim carries `(Author Year, locator) [access-tag]`;
  the deliverable ends with mandatory **Gaps** and **Confidence** sections (write
  "all targets filled; no conflicts found" rather than omitting them).
- Field-level unknowns use the playbook markers: `[not stated]`, `[read from figure]`,
  `[synthesis]`, `[secondary]` — never leave a cell silently blank.
- **Delivery is inline by default.** Any format below becomes a file artifact only when
  the user (Mode 1) or the caller contract (Mode 2) explicitly requests a file — content
  length alone never justifies writing one.

---

## 1. Inline summary

**Use when:** quick answer, few sources, no standalone file needed.

**Structure:** 1–3 paragraphs of prose; every claim cited inline; then Gaps +
Confidence as short trailing lines (may be one sentence each).

**Filled example:**

> Template-stripped Ag films reach sub-nanometer roughness (0.4 ± 0.1 nm RMS) and
> support SPP propagation lengths of 22 ± 3 μm at λ = 633 nm (Park 2022, Table 2)
> [full]. Single-crystal flakes do better (~35 μm at 785 nm, Chen 2023, Fig. 4b
> [read from figure]) [full], but the two values are not directly comparable
> (different wavelength and film type).
>
> **Gaps:** no searched source reports L_spp for template-stripped films in the
> near-IR. **Confidence:** roughness value single-sourced; L_spp convention
> (intensity 1/e) confirmed in both sources.

---

## 2. Annotated bibliography

**Use when:** caller needs a reading list, not extracted content.

**Per-source entry fields:**
- `citation` — full citation with identifier (DOI/arXiv/ISBN).
- `access` — access tag.
- `relevance` — 2–4 sentences: what THIS source contributes to the caller's question
  (not a generic abstract paraphrase), and which sections matter.
- `caveat` (optional) — recency limit, preprint status, known dispute.

**Template + filled example:**

```
1. Park, J. et al. (2022). "Ultrasmooth silver films for plasmonics."
   J. Placeholder Phot. 15, 234. DOI: 10.0000/fake.2022.234  [full]
   Relevance: primary experimental source for template-stripping fabrication
   (Methods §2.1 + Suppl. S1) and measured L_spp values (Table 2). Discussion §4.2
   states the coupled-mode model's validity limits — read before reusing the model.
   Caveat: all data at visible wavelengths only.
```

---

## 3. Evidence table

**Use when:** claim-by-claim support is needed (e.g. verifying a design assumption).

**Columns (fixed set):**
| Column | Content |
|---|---|
| `claim` | the statement being checked, one row per claim |
| `source` | Author Year + identifier |
| `locator` | section/table/figure/page |
| `stance` | `supports` / `contradicts` / `partial` / `silent` |
| `quality` | coarse credibility note (venue tier, sample size, directness) |
| `access` | access tag |

**Filled example row:**

| claim | source | locator | stance | quality | access |
|---|---|---|---|---|---|
| Grain boundaries dominate SPP loss in polycrystalline Ag | Park 2022 | Discussion §4.3 | supports | peer-reviewed; direct measurement | [full] |
| (same claim) | Chen 2023 | §3.4, Fig. 6 | contradicts (roughness dominates < 50 nm grains) | peer-reviewed review; secondary analysis | [full] |

Contradictory rows stay adjacent under the same claim; the conflict is restated in
Confidence.

---

## 4. Method summary

**Use when:** the caller wants to reproduce or understand a technique.

**Sections (fixed order):**
1. `Method` — name + one-line purpose + primary source.
2. `Required inputs` — materials/data/equipment, cited.
3. `Steps` — ordered list; each step: action, parameters, locator; gaps marked
   `[not stated]`.
4. `Assumptions & validity range` — stated (with locators) then inferred
   (`[synthesis]`).
5. `Reproduction gaps` — consolidated `[not stated]` list.

**Filled example (fragment):** see the worked example in
`extraction-playbook.md` §2 — that fragment IS the template's Steps + Reproduction
gaps sections filled in.

---

## 5. Parameter sheet

**Use when:** numeric values are the deliverable.

**Columns (fixed set):**
| Column | Content |
|---|---|
| `parameter` | name + symbol |
| `value` | value ± uncertainty (mark `[read from figure]` where applicable) |
| `unit` | as printed; if converted, show original + converted + factor |
| `conditions` | wavelength/temperature/material/dataset… — everything needed to reuse the number |
| `source` | Author Year + locator + access tag |

**Filled example row:**

| parameter | value | unit | conditions | source |
|---|---|---|---|---|
| Propagation length L_spp | 22 ± 3 | μm | λ = 633 nm; template-stripped Ag/air; intensity 1/e convention | (Park 2022, Table 2) [full] |

One row per (parameter × conditions × source) — do NOT merge same-parameter rows from
different conditions into a range.

---

## 6. Comparison matrix

**Use when:** the caller is choosing between methods/materials/models.

**Structure:** rows = options; columns = the CALLER's decision criteria (taken from
`purpose`; confirm criteria before building — a matrix on the wrong criteria is
wasted work). Every cell cited; empty knowledge = `[not stated]` in the cell, never a
blank. Add a final `Sources` column if per-cell citations make rows unreadable.

**Filled example:**

| option | L_spp @ 633 nm | fabrication complexity | wafer-scale? |
|---|---|---|---|
| Template-stripped Ag | 22 ± 3 μm (Park 2022, Table 2) [full] | low — no lithography (Park 2022, §2.1) [full] | yes (Park 2022, §5) [full] |
| Single-crystal flakes | `[not stated]` at 633 nm; ~35 μm @ 785 nm (Chen 2023, Fig. 4b) [read from figure] [full] | high — exfoliation yield limited (Chen 2023, §2.2) [full] | no (Chen 2023, §4) [full] |

No `winner` row unless the caller asked for a recommendation; if asked, add it tagged
`[synthesis]` with reasoning.

---

## 7. Quote pack

**Use when:** exact wording is load-bearing (definitions, standards clauses, disputed
claims).

**Per-quote entry fields:** verbatim quote (quotation marks, short — respect the
copyright boundary), full locator (page/section/clause), access tag, and a one-line
`why this wording matters` note.

**Filled example:**

> "the distance over which the SPP intensity decays to 1/e of its initial value"
> — Maier-style textbook, Ch. 2 §2.3, p. 27 [partial]
> Why: fixes the intensity (not field-amplitude) convention; cross-paper L_spp
> comparison depends on which convention each paper uses.

---

## Result contract — complete Mode 2 example

Returned to a calling skill (English, structure-stable). `findings` embeds one of the
seven formats above; the other four fields are always present.

```
{
  purpose_echo: "verify typical L_spp values for Ag waveguide design (from
                 scientific-research-guide Tier 1 request)",
  findings: {
    format: "parameter sheet",
    content: |
      | parameter | value | unit | conditions | source |
      |---|---|---|---|---|
      | L_spp | 22 ± 3 | μm | λ=633 nm; template-stripped Ag/air; intensity 1/e | (Park 2022, Table 2) [full] |
      | L_spp | ~35 [read from figure] (±5) | μm | λ=785 nm; single-crystal flake | (Chen 2023, Fig. 4b) [full] |
  },
  sources: [
    { citation: "Park, J. et al. (2022). J. Placeholder Phot. 15, 234.",
      identifier: "DOI: 10.0000/fake.2022.234",
      access_level: "full",
      locators_used: ["Methods §2.1", "Table 2", "Discussion §4.2"] },
    { citation: "Chen, L. (2023). Placeholder Rev. Nanophot. 8, 101.",
      identifier: "DOI: 10.0000/fake.2023.101",
      access_level: "full",
      locators_used: ["§1.2", "Fig. 4b", "§3.4"] }
  ],
  gaps: [
    "L_spp for template-stripped films in near-IR: not reported in any searched
     source (searched: Google Scholar, arXiv, 2 review bibliographies)."
  ],
  confidence: [
    { claim: "L_spp ≈ 22 μm @ 633 nm (template-stripped)",
      support: "1 source, direct measurement; convention confirmed",
      conflicts: "none" },
    { claim: "loss mechanism attribution",
      support: "2 sources, DISAGREE (grain boundaries vs roughness) — see
                evidence rows; unresolved in searched literature",
      conflicts: "Park 2022 §4.3 vs Chen 2023 §3.4" }
  ],
  search_trail: [
    "prism: rank_by_topic('silver SPP propagation length') — unavailable this
     session, fell back to WebSearch",
    "WebSearch: 'template-stripped silver SPP propagation length' (3 relevant hits)",
    "backward citation chase from Chen 2023 review bibliography (2 sources added)"
  ]
}
```

Notes:
- `purpose_echo` is optional but recommended — lets the caller detect a
  mis-parsed request cheaply.
- On partial failure, return the same structure with what WAS found; failures go in
  `gaps`, never silently dropped.
