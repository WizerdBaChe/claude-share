# Domain Profile: <Domain Name> (English full name)

> Scope of applicability:
> Scientific nature:
> Engineering nature:
>
> Cluster membership (only if this profile partitions one physical system with peer base
> profiles): member of the <name> cluster — this profile owns <X>; the split is tabulated in
> `_routing.md` § Clusters. (Delete this line otherwise; see `domain-expansion-guide.md` §2.)
>
> Profile metadata:
> - Profile ID:
> - Profile version:
> - Last updated:
> - Author(s) / Maintainer(s):
>
> Primary source types:
> - Textbooks:
> - Review articles:
> - Methods / standards papers:
> - Other (e.g. datasheets, industry standards):
>
> Notes for AI use:
> - Intended use:
> - Validation status / usage note:

---

## Citation convention (read before filling in Nodes 1–6) — REQUIRED, not optional boilerplate

> This block exists because an early profile in this SKILL was authored with an AI research
> tool's opaque citation numbering (`[web:12]`, `[ref:3]`, ...) with no bibliography attached
> — most of those numbers turned out to be unresolvable after the fact, and one resolvable
> number turned out to cite the wrong material system entirely (a quoted roughness figure
> from a titanium biomedical study, silently reused for a silicon MEMS claim). Both failure
> modes are prevented by the two rules below, not by adding more verification after the fact.

1. **Every inline citation MUST be a human-resolvable key**, e.g. `[Shikida2000]` or
   `[Weninger2026]` (surname + year; disambiguate with a letter if a source repeats a
   surname+year), and that key MUST have a matching row in the **Source Ledger** (§7b,
   below) before the profile is considered complete. Never write a bare sequential index
   number (`[12]`, `[web:44]`) with no attached bibliography — if a research tool hands you
   a citation as an opaque number, resolve it to a real reference (author/venue/year/DOI or
   URL) *before* the number goes into the profile, not after.
2. **Every quantitative claim states its conditions in the same breath as the number** —
   material system, measurement method, wavelength/temperature/concentration, sample type —
   not only in a table column that a reader (or a future editor copy-pasting the row) might
   drop. Write `"7.5 nm Ra, KOH + ultrasonic agitation + anionic surfactant, 100°C, Si(111)
   [Author2015]"`, not `"7.5 nm [12]"` with the conditions living three columns away. A
   number stripped of its conditions is a landmine for whoever reuses it next.
3. **Every citation of a versioned source pins the exact issue/version consulted** — a
   standard's issue (write `GR-1221-CORE Issue 2`, not `GR-1221`), a preprint's arXiv vN, a
   vendor datasheet's rev, a software tool's version — in the Identifier or Full citation.
   The Source Ledger's `Verified (date)` says *when* a claim was last checked; the pin says
   *against what* — and a `review-when: next revision` note is undecidable without it (see
   `domain-expansion-guide.md` §3.7).

These rules exist to keep every load-bearing claim in this profile at the same
traceability standard as `literature-search-extract`'s own P4 extraction discipline
(locator + exact conditions + access tag per claim) — a domain profile is exactly the kind
of load-bearing, long-lived artifact that discipline is for.

---

## 1. Theoretical Framework Anchoring

### Core first principles

| Scale/problem type | Foundational theory | Core physical quantity |
|------------|---------|-----------|
| | | |

### Inviolable physical constraints (the AI should warn the user here)

1. [Constraint statement, with source key, e.g. ...as established in [Author Year]]
2.
3.

> **Decision point (mandatory Tier 0 confirmation)**: when the user describes
> [X], the AI must confirm:
> "Is your goal (A)... / (B)... / (C)...?"
> The three goals correspond to entirely different [measurement / modeling /
> analysis] paths.

---

## 2. Measurement Tool Inventory

### <Measurement category 1>

| Measurement target | Tool | Output information | Applicable conditions | Common misuse | Source [Key] |
|---------|------|---------|---------|---------|---------|
| | | | | | |

### <Measurement category 2>

| Measurement target | Tool | Output information | Applicable conditions | Common misuse | Source [Key] |
|---------|------|---------|---------|---------|---------|
| | | | | | |

---

## 3. Standard Modeling Toolchain

```
<First-principles-scale tool>
→ Output:
    ↓
<Intermediate-scale tool>
→ Input:
→ Output:
    ↓
<Device/application-scale tool>
→ Output:
```

---

## 4. Domain-Specific Fitting Methods

| Method | Applicable question | Applicable conditions | Common error | Correct approach | Source [Key] |
|---|---|---|---|---|---|
| | | | ⚠️ | | |

> **Table, not prose-per-method (standardized 2026-08-24).** An earlier version of this
> template used a `### Method name` + bullet-field prose block per method. Two of this
> SKILL's four base profiles (`gan_power_device.md`, `microled.md`) had already converged
> independently on a table instead — and a table is the better choice for the reasons in
> `domain-expansion-guide.md` §3.3 (Grep/RAG atomicity: one row is one self-contained,
> citable fact; a prose block is not). All base profiles now use this table form. "Applicable
> question" is optional — omit the column if a method's applicability is already fully
> captured by "Applicable conditions."

---

## 5. Domain-Specific Quality Metrics

| Metric | Abbreviation | Physical meaning | Typical value range | Conditions (material/method/wavelength/temp…) | Source [Key] |
|------|------|---------|------------|------|------|
| | | | | | |

> **Conditions is not optional-if-obvious.** This is the column that would have caught a
> real past error in this SKILL: a correctly-quoted roughness figure from a *different*
> material system was silently presented as if it applied to this profile's domain. If the
> "Conditions" cell would just restate the domain name, that is a signal the source hasn't
> actually been checked against this domain's specific material/method — go check it.
> A "research frontier level" range additionally states its **as-of year** in the same cell
> (e.g. "frontier as of [Key]'s 2024 review") — the frontier moves while the cited source
> stays valid, so no ledger date can flag it (guide §4 Node 5).

---

## 6. Common Assumption Pitfalls

| Pitfall | Trigger condition | How to recognize it | Correct approach | Source [Key] |
|------|---------|---------|---------|---------|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

> **This table is the profile's primary standing-trigger home** — there is no separate trigger
> checklist node (see `domain-expansion-guide.md` §3.6 for the full trigger architecture and
> why the former "Node 8" was abolished). Write every `Trigger condition` in the **asker's
> words**, not the answer's: the condition must match what an erring user actually types.
> Entries that are not pitfalls belong elsewhere: goal clarifications → Node 1's Decision
> point; cross-profile handoffs → Cross-Domain Links / Conflict Notes; metric-context asks →
> Node 5's Conditions column.

---

## 7a. Literature Anchors

> The curated "every researcher in this field should know these" list — 3–5 canonical
> sources (prefer Textbook > Review > Methods paper). This is a *reading list*, distinct
> from the Source Ledger below, which is the *citation registry* for every specific claim
> made in Nodes 1–6. A source can appear in both if it is both canonical reading and the
> origin of a specific quoted number.

| Type | Reference | Why it matters |
|------|------|-------|
| | | |
| | | |
| | | |

---

## 7b. Source Ledger (REQUIRED — the resolution key for every `[Key]` used in Nodes 1–6)

> Legend — **Access tag** (same as `literature-search-extract` P3): `[full]` full text read ·
> `[partial]` preview/excerpt/supplementary only · `[abstract]` abstract/metadata only,
> paywalled — extract only what the abstract states · `[secondary]` known only via another
> source citing it, attribute as "B, as cited in A."
> **Verification status**: ✅ Confirmed (checked directly against the primary source) ·
> `~` Approximate (general claim/order-of-magnitude corroborated; exact figure not
> independently pinned to one source) · ⚠ Unconfirmed (flagged, not yet verified — usable
> only with that caveat visible wherever it's cited) · ❌ Withdrawn (previously claimed in
> an earlier version of this profile, found false or unverifiable, removed from Nodes 1–6
> but kept here as a record of what NOT to re-add without new evidence).
> **Verified (date)** (added 2026-08-25 — see `domain-expansion-guide.md` §3.7): the date this
> row's claim was last checked against the primary source — NOT the source's own publication
> year (that lives in Full citation). Many fields are time-sensitive (standards get revised,
> preprints get corrected, vendor pages get silently edited, a review's stated range gets
> superseded by a later meta-analysis); this date is what lets a future reader judge whether a
> re-check is due, and doubles as the anchor for an inline `review-when:` note on rows whose
> underlying fact is known to change on a specific trigger (a standard's next revision, a paper
> moving from preprint to peer-reviewed, a paywalled source becoming accessible). Stamp it at
> anchor-resolution time (guide §9 step 2), not in a cleanup pass; an access tag is likewise a
> dated observation, not a permanent property — its date is this same cell's.

| Key | Full citation | Identifier (DOI/arXiv/URL/patent/vendor spec) | Access tag | Verification status | Verified (date) | Locator (section/table/fig/page) | Used in (Node/row) |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

---

## Cross-Domain Links

### Closest Related Domain Profiles

| Profile name | Overlap dimensions | Typical use split |
|------|------|-------|
|  |  |  |
|  |  |  |
|  |  |  |

### Authoring notes (TEMPLATE-ONLY — DELETE this whole block in a filled profile)

- List the nearest existing Domain Profiles that overlap with this one in measurement tools, first principles, quality metrics, or interpretation logic.
- In **Overlap dimensions**, prefer short phrases such as `measurement tools`, `first principles`, `quality metrics`, `fitting methods`, or `application targets`.
- In **Typical use split**, state when the AI should prefer this profile versus the related one.
- If two profiles are close but still should remain separate, the difference must be stated explicitly here.

---

## Cross-Domain Conflict Notes

| Issue / constraint | Other profile(s) involved | Potential conflict | AI confirmation question |
|------|------|-------|-------|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

### Authoring notes (TEMPLATE-ONLY — DELETE this whole block in a filled profile)

- Use this section only for conflicts that can realistically occur when one user query spans more than one Domain Profile.
- A **Potential conflict** should describe why the two profiles may lead the AI to different judgments, warnings, or recommended workflows.
- Prefer conflicts tied to inviolable physical constraints, measurement validity, model applicability, quality-metric interpretation, or scale mismatch.
- The **AI confirmation question** must be written as a direct question the AI can reuse in conversation.
- If no meaningful cross-domain conflict is expected, keep at least one row and state `None currently identified` instead of deleting the section.
