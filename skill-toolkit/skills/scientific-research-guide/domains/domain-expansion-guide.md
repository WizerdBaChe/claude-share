# Scientific Domain Expansion Guide
## How to Specialize the General-Purpose Research-Assistance SKILL

> This document defines the architectural conventions, decision-trigger
> mechanisms, and AI behavioral rules that apply when a new research Domain is
> added to the SKILL.
> Audience: anyone adding a new Domain Profile to the SKILL — users or
> developers.

---

## 1. Recap: The SKILL's Three-Layer Architecture

```
Layer A: Generic research skeleton (Tier 0-7)
  └─ references/tier-framework.md
  └─ Never modified directly. Supplies the structure shared by all domains.

Layer B: Domain-specific content (three kinds — see §2 decision tree)
  └─ domains/<domain_name>.md          = base profile (the domain's shared core, 7 nodes)
  └─ domains/<domain_name>/<x>.md      = sub-profile (a specialized branch: material /
  │                                      phenomenon / method; shares the domain's first
  │                                      principles but adds its own traps/methods/triggers)
  └─ domains/<domain_name>/<x>.md      = reference / boundary note (depth or orientation;
  │                                      NO standing triggers)
  └─ domains/_routing.md               = manifest: which files exist + when to load each
  └─ This document specifies how to write this layer.

Layer C: Task instance (Session Context)
  └─ Supplied by the user in each conversation (current research state,
     steps already completed, etc.)
  └─ Using Layer B's criteria, the AI maps Layer C onto Layer A's Tiers.
```

**Base profiles stay lean.** A base profile is the domain's *shared core* — the 7 nodes at
domain-general level. Specialized branches (a specific material, a specific phenomenon/
method) do NOT get appended to the base file; they become sub-profiles under
`domains/<domain_name>/`. This keeps the base = the intersection all sub-topics share, and
stops it from growing unbounded. Every new file must be registered in `domains/_routing.md`
in the same change — that manifest is the only place the AI's load list lives.

**AI's logical sequence when using this**:
1. Identify which domain the user is in (match against the `domains/` directory).
2. Load the corresponding Domain Profile (Layer B).
3. Map the user's input onto the generic framework's Tiers (Layer A).
4. Output: current position + gaps + next step + risk warnings.

---

## 2. Classifying new content: the two-gate decision tree

Whenever you want to add content, run it through **two gates in order**. This decides
whether it becomes a new domain, a sub-profile, or a reference/boundary note.

> **The test is NOT "is this new/unfamiliar content?"** Novelty alone never justifies a new
> domain — that fragments the taxonomy endlessly. Only the three divergence conditions in
> Gate 1 decide the domain boundary. New-but-related content that shares the domain's first
> principles and toolset stays *inside* the domain as a sub-profile.

### Gate 1 — Domain boundary: does it break any of the three divergence conditions?

If **any one** of the three conditions below holds, the content belongs to a **different
domain** (create a new base profile, or it belongs to a sibling domain that may not exist
yet). If **none** holds, the content stays inside the current domain → go to Gate 2.

#### Trigger condition 1: Non-overlapping measurement toolset

> The core characterization tools used in the new domain do not appear in any
> existing Domain Profile's tool inventory.

**Examples**:
- Expanding from "semiconductor physics" to "soft-matter biophysics" → adds
  Rheometer, Patch-Clamp, Confocal Microscopy → triggers a new profile
- Expanding from "semiconductor physics" to "III-V power devices" → tool
  overlap is high → stays in the same domain (Gate 2 decides sub-profile vs base)

#### Trigger condition 2: A shift in first principles

> The new domain's core theoretical framework is incompatible with existing
> Domain Profiles and cannot share the same set of "inviolable physical
> constraints."

**Examples**:
- Expanding from "electromagnetics/plasmonics" to "quantum many-body physics"
  → Maxwell's equations → second quantization; the core language changes →
  triggers a new profile
- Expanding from "plasmonics" to "photonic crystals" → still Maxwell's
  equations + periodic boundary conditions, same FDTD/FEM toolchain →
  stays in the same domain → Gate 2

#### Trigger condition 3: Incompatible quality-metric set

> The new domain's criteria for "what counts as good research" cannot be
> measured with an existing Domain Profile's metrics.

**Examples**:
- Expanding from "Ti materials" to "biomedical materials" → metrics shift from
  photocatalytic rate to cytotoxicity (IC₅₀) and osseointegration (BIC%) →
  triggers a new profile

### Gate 2 — Form: sub-profile vs reference/boundary note

Reached only when Gate 1 says the content stays inside the domain. Now decide its **shape**
by one question: **does it carry its own standing if-then rules?**

- **Sub-profile** — it has domain-specialist traps, named fitting methods, plausibility
  ranges, or decision triggers that a domain generalist would miss and that should fire
  automatically. Litmus test: *you can write "user says/does X → AI should warn/ask Y".* It
  reuses the parent's Nodes 1-3 (theory/tools/toolchain) and fills only the nodes where it
  adds specialist judgment — typically Node 4 (fitting), 5 (metrics), and above all Node 6
  (pitfalls, whose `Trigger condition` column is what makes the branch's triggers standing —
  see §3.6). See the sub-profile mini-template in §8. File: `domains/<domain>/<x>.md`,
  registered as `sub-profile` in the manifest with `Active triggers? = yes`.
- **Reference / boundary note** — pure depth (derivation, background) or orientation, with
  **no** standing triggers. A *boundary note* specifically demarcates the domain edge and
  routes the user OUT to a sibling domain when they cross it. File: `domains/<domain>/<x>.md`,
  registered as `reference` or `boundary` with `Active triggers? = no`.

One-line rule: **can write "user says X → auto-warn Y" ⇒ sub-profile; only readable ⇒
reference.**

### Base vs sub-profile: where does in-domain content go?

- **Base** = what *all* sub-topics of the domain share (the intersection). Only content
  every researcher in the domain needs belongs here.
- **Sub-profile** = a branch relevant only when the user is in that branch (a specific
  material, phenomenon, or method).

This is what keeps the base profile from bloating: it holds the shared core, branches live
beside it.

### Sibling clusters: when Gate 1 splits ONE physical system into several domains

Gate 1 can legitimately split a single physical assembly into several **peer base profiles** —
each pair breaks the divergence conditions against the other, yet all of them partition one
system a user experiences as a whole. This shape is a **sibling cluster**. It is a first-class
shape, not an unfinished folder: the four photonic-packaging profiles
(`v_groove_fabrication` / `adiabatic_taper_ssc` / `fiber_chip_passive_alignment` /
`siph_packaging_reliability`) are the standing example (ruling 2026-08-24, below).

**The intersection test — run it BEFORE building a parent.** When N co-triggering siblings look
like they "should" be a domain with a base profile, lay their Nodes 1–3 side by side and ask what
a shared base would actually contain:

- **Thick intersection** (shared first principles, overlapping toolset, commensurable metrics) →
  they were never separate domains; Gate 1 was misapplied. Build the base, demote them to
  sub-profiles.
- **Thin intersection** (only a shared application target, shared observables, shared standards
  vocabulary) → they are a sibling cluster. **A base built on a thin intersection is a fake
  parent**: it would hold no first principles of its own, every load would be a false load, and
  the real content would still live in the members. Do not build it.

Either way, **write the verdict down as a ruling** (STATUS.md + the cluster registration below),
with the intersection evidence. An undocumented flat structure looks like an accident of
authoring order and gets re-litigated by every new reader; a registered cluster does not.

**Registration requirements** (what makes the relationship structural rather than prose):

1. `_routing.md` carries a **§ Clusters** block: cluster name, members, the partition axis
   (one line per member: what it owns), the disambiguation table, and the ruling with its date.
2. Each member's header carries a short **Domain boundary / cluster membership** note naming the
   cluster, what this member owns, and where the split is tabulated (`_routing.md § Clusters`).
3. Cross-member numbers are referenced, never copied (each number has exactly one home profile).
4. **Folders stay reserved for sub-profiles.** A cluster does NOT get a directory: a
   `domains/<name>/` folder means "children of the same-named base profile", and breaking that
   invariant to gain directory legibility costs more than it buys (path churn + a second meaning
   for one convention).

**2026-08-24 ruling — the photonic-packaging cluster stays flat.** The intersection test was run
on the four members' Nodes 1–3: first principles are disjoint (crystallographic etch kinetics /
coupled-mode theory / contact mechanics + tolerance statistics / physics-of-failure +
thermo-mechanics), toolsets are disjoint (etch metrology / optical mode + loss instrumentation /
cure + CT metrology / stress chambers + failure analysis), metric sets are incommensurable
(etch rate & angle / adiabaticity & CL / ΔIL_cure & worst-channel / AF & Weibull). The shared
layer is exactly the thin kind: one application target, IL/RL observables, Telcordia vocabulary.
Option B (a `photonic_packaging.md` parent) was therefore rejected as a fake parent; the flat
structure is now a decision, not an accident.

### Worked examples (Topological Insulator domain)

| Content | Gate 1 | Gate 2 | Verdict |
|---|---|---|---|
| **Bi₂Se₃** specifics | shares TI first principles + ARPES/transport toolset → in-domain | material-specific traps (bulk conduction from Se vacancies, aging/oxidation) | **sub-profile** (material-scoped) |
| **WAL** (weak antilocalization) | shares TI framework + magnetotransport → in-domain | own fitting method (HLN) + fit pitfalls (single-field-range α, decoherence-length temperature dependence) | **sub-profile** (phenomenon/method-scoped) |
| **HOTI** (higher-order TI) | still single-particle band topology + tight-binding/DFT; extends bulk-boundary correspondence but does NOT break the 3 conditions → in-domain | new-territory traps (trivial corner states via filling anomaly, nested Wilson loop prerequisites) | **sub-profile** (new-territory; *candidate for future promotion* to its own domain if it later grows a non-overlapping toolset or incompatible metrics — do NOT pre-promote) |
| **SPT order vs Topological order** | the *comparison* is orientation; but *intrinsic topological order* itself breaks all 3 conditions (long-range entanglement, anyons/TQFT, entanglement-entropy metrics) → that side is a **future separate domain** | the comparison note carries no experimental traps; its job is to route out | **boundary note** in TI (points to the future intrinsic-topological-order domain) |

---

## 3. Required Structure of a Domain Profile (Seven Nodes + Source Ledger)

Every Domain Profile must contain the following seven nodes; none may be
omitted. This is the minimum requirement for the AI to use the Profile
correctly. Node 7 is split into **7a** (curated reading list, as before) and
**7b** (per-claim citation registry, added 2026-08-24 — see §3.2 for why).
There is **no separate trigger checklist node**: the standing triggers ARE the
trigger-bearing columns of Nodes 1–6 plus the Conflict Notes questions — see
§3.6 for the architecture and for why the former "Node 8" was abolished.

```markdown
# Domain Profile: <Domain Name> (English full name)

> Scope of applicability (2-3 lines)
> Scientific nature:
> Engineering nature:

## Citation convention (required — see §3.2 and _template.md)

## 1. Theoretical Framework Anchoring
## 2. Measurement Tool Inventory
## 3. Standard Modeling Toolchain
## 4. Domain-Specific Fitting Methods
## 5. Domain-Specific Quality Metrics
## 6. Common Assumption Pitfalls
## 7a. Literature Anchors
## 7b. Source Ledger
## Cross-Domain Links
## Cross-Domain Conflict Notes
```

### 3.2 Why a Source Ledger is required (added 2026-08-24)

Two Domain Profiles in this SKILL (`v_groove_fabrication.md`, compiled via an AI research
tool) were originally authored with an opaque citation-index convention (`[web:12]`,
`[web:44]`, …) that had **no bibliography attached at authoring time**. A later
`literature-search-extract` verification pass found: (a) most of those index numbers were
unresolvable after the fact — nobody, including the AI that wrote them, could say what
source they pointed to; (b) one number that *did* resolve to a real source turned out to
cite the wrong material system entirely — a quoted AFM-vs-profilometer roughness figure
from a **titanium biomedical** study, silently reused as if it were a silicon/glass MEMS
result. Both are now-documented failure modes, not hypothetical ones (see that profile's
own "Citation Verification Log" for the full record).

The fix is structural, not a promise to "be more careful": every inline citation must use a
human-resolvable key (`[Author Year]`) with a matching row in a per-profile **Source
Ledger** (Node 7b), and every quantitative claim must carry its conditions (material
system, measurement method, wavelength/temperature/concentration) in the same breath as the
number — not only in a column three cells away that a later editor can drop while copying a
row. See the "Citation convention" block at the top of `_template.md` for the exact rules;
authors fill in Node 7b as they write Nodes 1–6, not as a cleanup pass afterward — a ledger
assembled after the fact is exactly the expensive, lossy repair this SKILL just went
through twice.

### 3.3 Table-first formatting, and why Node 4 changed from prose to a table (added 2026-08-24)

A cross-profile consistency pass (2026-08-24) compared all four base profiles' Node 2/4/5/6
table schemas and found real drift: same node, different column names *and*, in places,
different column semantics, across files authored at different times. Two findings from that
pass are now standing rules:

1. **All of Nodes 2, 4, 5, 6 use a table**, one row per fact (tool, method, metric, or
   pitfall). `gan_power_device.md` and `microled.md` had already converged on a table for
   Node 4 independently; `plasmonic_waveguide.md` used a `### Method name` prose block per
   method. The table form won because it is strictly better for this SKILL's two real
   consumers: **Grep** (one row = one grep match with full context on that line) and any
   future **RAG-style chunking** (one row is a self-contained, independently citable fact —
   a prose block spanning several lines is not). Prose remains fine for connective narration
   *between* nodes; it is the wrong shape for the node's core payload.
2. **Each node's table must carry its required-core columns under the exact canonical names**
   given in `_template.md`; beyond the core, additions are free and one recommended column may
   be substituted. The distinction (settled 2026-08-24, when "exact canonical names for all
   columns" proved unenforceable against legitimately different semantics):
   - **Required core** — must be present, exact names: Node 2 `Applicable conditions` /
     `Common misuse` (the identity column legitimately varies: `Measurement target`, `Tool`,
     or a stress-matrix label like `Stress`); Node 4 `Method` / `Applicable conditions` /
     `Common error` / `Correct approach`; Node 5 `Metric` / `Typical value range` /
     `Conditions`; Node 6 `Pitfall` / `Trigger condition` / `Correct approach`. All of Nodes
     2/4/5/6 additionally require `Source [Key]` on base profiles. These are the columns a
     parser (Grep, a RAG pre-processor, the lint script) may rely on.
   - **Recommended** — Node 6 `How to recognize it` (symptom). A file MAY carry a different
     semantic dimension instead (e.g. `Why it fails` — mechanism, in `gan_power_device.md` /
     `microled.md`): keep the honest label rather than force a misleading rename.
   - **Free additions** — e.g. `Suspicious comparison`, `Device class`. Adding information is
     fine; silently renaming a column to a canonical name it doesn't actually mean is not.
   The enforcement instrument is `tools/profile-lint.py` (structure, core columns, opaque
   markers, manifest closure) — run it after any structural edit rather than eyeballing.
   For RAG-style chunking, note the tables assume **header-aware chunking** (each chunk carries
   its H1/H2 context); per-row stable IDs were considered and consciously rejected at the
   current scale (single maintainer, 150–500-line files) — revisit only if cross-file row-level
   citation becomes real.

### 3.4 The citation invariant, and how to check it (rewritten 2026-08-24)

This section previously asserted a **count** ("all six base profiles have a completed Source
Ledger"). That sentence was false within hours of being written — two base profiles authored the
same day never had a ledger, and three more base profiles were added afterwards. A frozen count is
the wrong shape for this control: it rots silently while still being trusted. State the invariant
as a property of the asset, and give the reader a way to re-derive the count instead.

> **Invariant.** Every base profile in `domains/` MUST contain a Node 7b Source Ledger, and MUST
> contain **no opaque citation index** (`[web:12]`, `[ref:3]`, bare `[12]`) anywhere in Nodes 1–6.
> Every inline `[Key]` in Nodes 1–6 MUST resolve to a ledger row. A newly-added profile starts
> from `_template.md` and ships with its ledger in its first version — backfill is remediation,
> never a planned phase.

Re-derive the current state rather than trusting any count written here (run from `domains/`):

```bash
for f in *.md; do printf "%-38s ledger:%s opaque:%s\n" "$f" "$(grep -cE '^#+ .*(7b|Source Ledger)' "$f")" "$(sed -n '/^## 1\./,/^## 7a/p' "$f" | grep -oE '\[(web|ref):[0-9]+\]' | wc -l)"; done
```

(`grep -o | wc -l` counts *markers*, not matching lines — `grep -c` undercounts badly here, since
these profiles routinely stack several markers on one line.)

A compliant base profile reads `ledger:1 opaque:0`. No known exception remains as of 2026-08-24:
`topological_insulator.md` was the last half-migrated file (ledger present, 73 `[web:NN]` markers
still inline) and its markers were rewritten the same day — all 23 tags resolved from that ledger's
own "formerly web:NN" annotations, none guessed. Treat a ledger-without-inline-rewrite as **not
done**, because a table that only resolves opaque indices still leaves every citation unreadable
without a lookup. Re-run the command rather than trusting this sentence.

Two counting traps this control has already hit, both of which made a file look worse or better than
it was: `grep -c` counts *lines*, not markers (23 vs. 73 on the file above); and a "formerly
web:39/54" annotation only matches the first number under a naive `web:(\d+)` pattern, which made
nine already-resolvable tags look unresolvable. When auditing the mapping, parse the slash groups.

*review-when:* a base profile is added, or any profile's citations are backfilled — re-run the
command above rather than editing a number into this paragraph.

### 3.5 Where a domain's Chinese-gloss terminology table lives (settled 2026-08-24)

Three profiles authored on the same day produced two different shapes for the same need — an inline
`## 0. Terminology & Chinese glosses` node (`fiber_chip_passive_alignment.md`, 25 terms;
`siph_packaging_reliability.md`, 47 terms) and a separate reference file
(`silicon_photonics_device_physics/terminology.md`, 44 terms). Both shapes are legal. What is **not**
optional is the invariant:

> **Invariant.** A domain has **exactly one** home for its Chinese glosses. Every other file in that
> domain points at it and carries no partial copy. If the home is a separate file, it is registered
> in `_routing.md` (type `reference`, `Active triggers? = no`) in the same change that creates it.

Which shape to choose, for a *new* domain:

- **Default: an inline Node 0 in the base profile.** A `reference` row is loaded on demand only, so
  glosses in a separate file are absent from the AI's context on the turns that most need them — the
  ones where it is reasoning in the domain and about to name a term in Chinese.
- **Promote to `domains/<domain>/terminology.md` when** the domain has sub-profiles that share the
  same vocabulary (one home beats N copies), or the table is large enough that carrying it on every
  domain turn costs more than fetching it (observed threshold: the ~45-row tables here are the point
  where this becomes arguable, not obviously wrong either way — so treat it as a judgement call, not
  a line to enforce).
- **Do not migrate existing files to match.** Both shapes already satisfy the invariant; converting
  one to the other is churn with no reader benefit.

Terminology content rule, independent of shape: the profile body is English (machine-consumed domain
reasoning), and Taiwan renderings are preferred over mainland ones, with the mainland/Japanese
variant marked ⚠ where the source packet used it — the recurring corrections so far are
anisotropic = 非等向性 (not 各向異性), creep = 潛變 (not 蠕變), hydrolysis = 水解 (not 加水分解),
reliability = 可靠度 (not 可靠性).

*review-when:* a new base profile adds a terminology table, or a domain gains its first sub-profile
that shares the parent's vocabulary.

### 3.7 Per-citation currency: the "Verified (date)" column (added 2026-08-25)

**Rationale.** A citation's *publication* year (already in Full citation) says when the source was
written; it says nothing about when THIS profile last checked the claim against it. Many
load-bearing facts in this SKILL are time-sensitive in ways a publication year cannot flag:
standards get revised (a JEDEC/Telcordia designation's conditions can change between issues), a
review's stated typical-value range can be superseded by a later meta-analysis, a preprint can be
corrected or retracted on peer review, a vendor page can be silently edited, and a paywalled source
marked `[abstract]` can become fully readable later. Without a per-row date, a stale claim is
indistinguishable from a freshly-checked one, and nothing prompts a future re-check.

**Requirement.** Every Node 7b Source Ledger row carries a **Verified (date)** cell: the date this
row's claim was last confirmed against the primary source (not merely re-typed from an earlier
version of the profile). Where a row's underlying fact is known to change on a specific, nameable
trigger — not just "eventually" — add an inline `review-when:` note in the same cell naming that
trigger (a standard's next revision, a paywalled source becoming accessible, a preprint moving to
peer review), following the same "property of the asset, not a vague reminder" discipline this
SKILL's author already applies to ops rules generally. A row with no specific trigger needs no
`review-when:` note — the bare date is sufficient; do not invent a generic "re-check periodically"
note that names no event, since that is exactly the silently-rotting-control failure mode this
column exists to prevent.

**Version pinning — the date's precondition for versioned sources (added 2026-08-26).** For a
source that exists in revisions — a standard (a JEDEC/Telcordia designation's issue), a preprint
(arXiv vN), a vendor datasheet or app note (rev), software documentation (tool version) — the
ledger row's Identifier or Full citation must pin the **exact issue/version consulted**. This is
the version analogue of the time tag: the date says *when* the claim was last checked, the pin
says *against what*. Without the pin, a `review-when: the standard's next revision` note is
undecidable — you cannot know whether the revision has happened if the row never recorded which
issue was read. A bare designation ("GR-1221", "JESD22-A101") with no issue number is the
versioned-source equivalent of an undated verification.

*Instrument (added 2026-08-26).* This is enforced the same way the date column is, not by prose:
`tools/profile-lint.py` WARNs on any ledger row whose Full-citation or Identifier cell names a
JEDEC / Telcordia / IEC / MIL-STD designation while the row records no issue, edition or revision
**value**. Two calibration facts are load-bearing and were each a real bug during authoring: a pin
is a value, never the word — a row saying "the issue letter is still unpinned" must not read as
pinned — and the revision patterns are matched **case-sensitively**, because under `re.I` a `[A-Z]`
revision letter also matches ordinary lowercase prose ("re**v**erified"), which silently marked
every row as pinned. Calibrated two-sided on the live tree: the nine rows that genuinely record no
issue fire; the six that record one (`JESD22-B103B.01`, `JESD22-B104C`, `JESD22-A106` revision B,
GR-468 Issue 2, GR-1221 Issue 3, IEC 61300-1 Ed. 5.1:2024) do not.

**Collection-side alignment (added 2026-08-26).** The same currency discipline applies *upstream*
of profiles, where sources are collected and triaged before any claim exists:

- An **access tag is a dated observation, not a permanent property** — paywalls open, pages die,
  vendor pages get silently edited. Wherever an access tag is assigned or changed
  (`references/user-supplied-citations.md`'s promotion table, a §7b ledger row), the date of that
  observation must be recoverable from the same row.
- The **intake pipeline stamps the date at resolution time** (§9 step 2), not in a later cleanup
  pass — the anchor-resolution step is by definition the moment the claim was last checked against
  the primary source, so the `Verified (date)` cell is free to fill there and expensive to
  reconstruct afterwards.
- **Anchor resolution includes an erratum/retraction check** while already at the primary source
  (publisher page / Crossref metadata carry these). A found correction or retraction is recorded
  in the ledger row (❌ Withdrawn if the claim falls), never silently dropped.

**Rollout stance (same as the Source Ledger itself, §3.2).** A newly-authored profile ships with
this column filled in from its first version — backfill is remediation, never a planned phase. Nine
base profiles predate this column and do not yet carry it; that gap is a **§3.8 category-3
(evidence-bearing) retrofit** — remediated at the next content touch of each file, never
backfilled wholesale (a date-stamping pass with no fresh verification would be false precision).
The debt is surfaced by instrument, not prose: `tools/profile-lint.py` WARNs on every base
profile whose ledger lacks the column, so the list of remaining files is re-derived on every run
instead of trusted from `STATUS.md`.

*review-when:* a profile's citation is found stale in a way an earlier `review-when:` note should
have caught but didn't — treat that as evidence the note was too vague, and re-write it naming the
actual trigger.

### 3.8 Retrofit rule: aligning already-ingested content with a new convention (added 2026-08-26)

Newly-authored content ships with the current conventions from its first version (§3.2/§3.7
rollout stance). Content ingested **before** a convention existed is a different problem: some of
it can be brought into line immediately, some of it must not be. Classify every retrofit by **what
filling the gap requires** — whether the information already exists, or must be produced by a
fresh act of verification:

1. **Structural retrofit — wholesale allowed.** The new shape can be filled entirely from
   information already recorded in the repo: renaming a heading to the canonical phrase, deleting
   scaffolding, re-pointing links, converting prose to a table, resolving markers from an existing
   documented mapping. Nothing is invented; only form changes. Precedents: the Node 8 abolition
   migration (§3.6), `topological_insulator.md`'s `[web:NN]`→`[Key]` rewrite (every tag resolved
   from the ledger's own "formerly web:NN" annotations — none guessed), the authoring-notes sweep.
2. **Provenance migration — allowed only against a documented record.** The new cell asks for a
   fact about a *past* act (when was this row checked; what did that pass read) and that act is
   documented with a date somewhere — a report, a verification log, a STATUS entry. Copying the
   documented record into the new column is recording history, not fabricating it. Annotate the
   migration so a reader can tell it from a fresh check (reference shape:
   `user-supplied-citations.md`'s Checked (date) = 2026-08-03, flagged as migrated provenance of
   the documented pass that built the table). **No document → no migration** — a remembered or
   plausible date is category 3, not category 2.
3. **Evidence-bearing retrofit — never wholesale; remediate at the next content touch.** The
   cell's value only means anything if a fresh act of verification stands behind it: a fresh
   `Verified (date)`, a verification-status upgrade, a Conditions cell that requires re-reading
   the source. Hard-filling these ("date-stamp everything today", "Conditions = the domain name")
   is false precision — the cell would carry the column's *authority* without the act that
   authority stands for, which is exactly the failure mode the column exists to prevent. These
   gaps close only when the file is next touched for content, or in a dedicated verification pass
   (reference shape: the 2026-08-26 `literature-search-extract` currency pass on
   `adhesives_polymer_reliability.md`, audit trail in `reports/`).

Two invariants apply across all three categories:

- **The remaining gap is surfaced by instrument, not prose** — a linter WARN or a re-derivable
  command (§3.4's lesson: a frozen list rots while still being trusted). A retrofit stance
  without its instrument is a plan, not a control; the `Verified (date)` debt's instrument is
  `tools/profile-lint.py`'s per-run WARN.
- **An honest gap beats a guessed value.** When a pass touches a file but a specific cell has
  neither fresh verification nor a documented record behind it, leave it *explicitly* open —
  `⚠ not re-verified since authoring` — rather than filling it to satisfy a completeness check.
  §6's "no blank cells" is satisfied by an honest marker, not only by a value.

*review-when:* a new convention's rollout paragraph is being written — cite this section and
classify the retrofit into a category, instead of restating the stance ad hoc.

### 3.6 Standing-trigger architecture: one trigger, one home (Node 8 abolished 2026-08-24)

**The standing if-then rules a loaded profile activates are the trigger-bearing columns that
Nodes 1–6 already carry, plus the Conflict Notes questions.** There is no separate checklist
node. The full standing set, each with exactly one home:

| Trigger class | Home | The firing column / block |
|---|---|---|
| Physical-constraint violations | Node 1 | "Inviolable physical constraints" (conditional statements) |
| Goal/scale ambiguity at Tier 0 | Node 1 | the mandatory "Decision point" block |
| Tool misapplication | Node 2 | `Common misuse` column |
| Fitting-method misapplication | Node 4 | `Common error` column (SKILL.md Category D) |
| Implausible / context-free numbers | Node 5 | `Typical value range` + `Conditions` columns (SKILL.md plausibility check) |
| Domain-expert traps (the primary home) | Node 6 | `Trigger condition` column |
| Cross-profile conflicts | Conflict Notes | `AI confirmation question` column |
| Profile-generic mechanics (§7b provenance check, terminology-home use, destructive ordering) | SKILL.md, stated once | Domain-profiles section — never copied into a profile |

**Why the former Node 8 was abolished, with the measurement.** Every profile used to end with a
required "AI Decision-Trigger Checklist" (`- [ ] user says X → do Y`, minimum 5 items). A
2026-08-24 audit counted its entries against Node 6's rows across all 15 trigger-bearing files:
the counts matched almost 1:1 (e.g. `siph_packaging_reliability` 14 vs 14, with 13 of 14 being
row rewrites), and the rewrites had **dropped two columns** in the copying — `How to recognize
it` and `Source [Key]` — making Node 8 an unsourced second copy of Node 6 inside the same file.
The residual non-Node-6 entries all turned out to be copies of OTHER homes: Node 1's decision
point (in two profiles that block existed only under a non-canonical heading invisible to the
canonical-phrase grep, so the checklist duplicated it instead of the heading being normalized),
the Conflict Notes questions, Node 2/4 warning columns, or profile-generic mechanics that belong
in SKILL.md once. The minimum-count requirement ("no fewer than 5 items") is what *forced* the
copying. The checkbox form also implied a completion state that could never be checked.

**Standing rules extracted from that incident:**

1. **The intra-file no-copy invariant.** "Numbers are cited, not copied" was already the
   cross-file rule; it now applies *within* a file too: a fact (trigger, number, rule) has one
   home node, and any other node that needs it points there. A parallel structure that restates
   another node's rows in a second format is prohibited — nobody audits intra-file duplication
   unless the rule names it.
2. **A required node must justify its existence measurably.** Any rule of the form "every
   profile must contain node X" must come with a re-runnable check showing X is not a
   re-encoding of another node (the instrument here was a per-file row count, Node 6 vs Node 8).
   A gate whose necessity cannot be measured will be filled by copying to satisfy the gate.
3. **Trigger conditions are written in the asker's words, not the answer's** — the same rule
   `_routing.md` § Maintenance already applies to load keywords. A Node 6 `Trigger condition`
   containing only the corrected value (e.g. `35.26°`) never fires; the erring user types the
   wrong value (`54.74°`).

Re-derive compliance (run from the skill root; the only legal hits are in this guide and in
history-recording files like STATUS.md):

```bash
grep -rln 'AI Decision-Trigger Checklist' domains/
```

A migration disposition was applied per entry, not wholesale: duplicate-of-Node-6 → deleted;
clarification asks → moved into (or verified present in) Node 1's decision point; routing asks →
verified present in Cross-Domain Links/Conflict Notes; generic mechanics → SKILL.md; the few
genuinely homeless entries → written as full Node 6 rows (with recognition column and source).
Nothing was deleted that did not verifiably exist in its proper home.

*review-when:* SKILL.md's Domain-profiles section changes how it activates profile triggers, or
a new node type carrying if-then content is proposed.

---

## 3.1 Optional profile metadata block (established convention, not yet a required node)

Every base profile in the source environment prepended a `> Profile metadata:` /
`> Primary source types:` / `> Notes for AI use:` block before Node 1. This is a useful,
low-cost convention worth continuing for new base profiles, but it is not yet part of §3's
required seven nodes — a profile missing it is not structurally invalid.

**When a `Notes for AI use:` line points at an optional external tool** (a local literature
corpus, a terminology/glossary vault, a simulation-tool inventory, etc.), write it as a
**swappable slot, not a hard dependency** — the same pattern already used for `prism` in
SKILL.md Gate B and for the local-corpus slot in `literature-search-extract`:

1. Name the *category* of tool and what it is for ("a local terminology/glossary vault",
   not just a product name).
2. State the domain's own lookup key if it has one (a DomainPath, a corpus tag) — this is
   domain-specific and belongs in the domain file even if the tool itself is generic.
3. Cite the currently-known reference implementation as an example ("the reference
   implementation as of <date> is X"), not as the only supported option.
4. State explicitly how the profile degrades when the tool is absent (fall back to this
   file's own Node 1 tables / a sibling reference file / etc.). A profile must remain
   fully usable without any optional external tool.
5. Do **not** hardcode a personal absolute filesystem path into the profile body. It
   breaks the moment the tool moves, and it becomes a data-leak/environment-coupling
   finding the moment the skill is shared (see `skill-share-packaging`'s de-environment
   pass). If a path is genuinely needed for a human reader, put it in a status or
   report file, not in content the AI loads as domain reasoning.

This same slot pattern is how the `prism` MCP hook in SKILL.md and the citation-inbox
delegation to `literature-search-extract` (see `references/user-supplied-citations.md`
§Delegation rule) are already written — a domain profile's terminology-vault hint should
read the same way, not invent its own convention.

---

## 4. Authoring Rules for Each Node

### Node 1: Theoretical Framework Anchoring

**Must include**:
- A table of core first principles, classified by scale or problem type
- A list of **"inviolable physical constraints"** (precise conditional
  statements the AI can use for automatic warnings)
- At least one "mandatory Tier 0 confirmation" decision point, in this format:

```markdown
> **Decision point (mandatory Tier 0 confirmation)**: when the user describes
> X, the AI must confirm:
> "Is your goal (A)... / (B)... / (C)...?"
> The three goals correspond to entirely different [measurement / modeling /
> analysis] paths.
```

**Authoring principles**:
- "Inviolable physical constraints" should be precise conditional statements,
  not vague "things to watch out for"
- Each constraint should note the consequence of violating it (wrong
  computed result / invalid measurement / conclusion that doesn't generalize)

### Node 2: Measurement Tool Inventory

**Must include**:
- A table organized around "measurement target," with columns: Tool / Output
  information / Applicable conditions / **Common misuse** / **Source [Key]**
- The "Common misuse" column is the core payload — it's what lets the AI give
  preventive warnings
- The "Source [Key]" column resolves to Node 7b (Source Ledger) — see §3.2

**Authoring principles**:
- For every tool, also write down the situations where it does *not* apply,
  not just what it can do
- Destructive vs. non-destructive measurements need to be flagged (this
  affects the ordering of an experimental sequence)

### Node 3: Standard Modeling Toolchain

**Must include**:
- A tool pipeline (ASCII flow diagram) running from "the most fundamental
  theoretical scale" to "the final application scale"
- For each tool: its input requirements + the conditions under which its
  output can be trusted

**Authoring principles**:
- Don't just list tool names — explain "under what conditions you'd use this
  tool instead of the next one"
- Note the data-handoff format between tools (so the AI doesn't recommend a
  tool combination that can't actually be chained together)

### Node 4: Domain-Specific Fitting Methods

**Must include**:
- A table (see §3.3) with one row per "named" standard fitting method (e.g. Tauc Plot,
  Oliver-Pharr, Scherrer)
- Columns: Method / [optional: Applicable question] / Applicable conditions / Common
  error (⚠️ format) / Correct approach / Source [Key] resolving to Node 7b

**Authoring principles**:
- The point isn't to explain the method's underlying principle, but to spell
  out clearly "under what circumstances this method gives a spurious result"
- If there's a corresponding "correct way to read off the value" (e.g. the
  standard linear-extrapolation procedure for a Tauc Plot), describe it
  explicitly

### Node 5: Domain-Specific Quality Metrics

**Must include**:
- Metric name / abbreviation / physical meaning / typical value range /
  **Conditions** / **Source [Key]**
- "Typical value range" is the key item — the AI needs this to judge whether
  the user's result is plausible
- **Conditions** (material system, measurement method, wavelength/
  temperature/concentration) sits in its own column, in the same row as the
  number — this is the column that would have caught a real incident in this
  SKILL: a correctly-quoted number from a *different* material system,
  silently presented as if it applied to the profile's own domain (see §3.2).
  If a Conditions cell would just restate the domain name, the source likely
  hasn't actually been checked against this domain's specific material/method.

**Authoring principles**:
- Typical value ranges should distinguish "industry/commercial level" from
  "research frontier level"
- Also flag the "suspicious result range" (both too good and too bad need
  confirmation)
- Never copy a numeric value into this table without also copying the
  condition it was measured/computed under, even when the source column
  feels redundant to write
- A "research frontier level" range is **dated by nature** — the frontier moves while the cited
  source stays valid, so the ledger's `Verified (date)` (which tracks when the *source* was
  checked) cannot flag it. State the as-of year in the Conditions cell itself (e.g. "frontier as
  of [Key]'s 2024 review") — the year is a condition of the number, same rule as
  material/method. Industry/commercial-level ranges drift much slower and need no year unless
  the source is old enough that staleness is plausible

### Node 6: Common Assumption Pitfalls

This is the **highest-value node** in the entire Domain Profile.

**Must include five columns**: Pitfall description / Trigger condition / How
to recognize it / Correct approach / **Source [Key]**

This node is also the **primary home of the profile's standing triggers** (§3.6): SKILL.md
turns each row's `Trigger condition` into a standing if-then rule for the whole turn. There is
no separate checklist to copy rows into.

**Authoring principles**:
- The "trigger condition" needs to be specific enough that the AI can
  automatically recognize it from the user's own wording
- **Write the trigger condition in the asker's words, not the answer's** — the condition must
  match what an *erring* user actually types (they type `54.74°`, never the corrected `35.26°`;
  they ask in the language they work in). Same rule as `_routing.md` § Maintenance for load
  keywords
- A pitfall should be tacit knowledge that only a domain expert would know,
  not an obvious mistake
- Target count: at least 6 pitfalls per domain
- If a candidate entry is not a *pitfall* — it is a goal clarification, a cross-profile
  handoff, or a metric-context ask — it belongs in another home (Node 1 decision point,
  Cross-Domain tables, Node 5's Conditions column; see the §3.6 table), not in a rephrased
  Node 6 row

**Example of how to write a trigger condition**:
```
Trigger condition: "User says: we used the Drude model to simulate the
response of Au nanostructures at 550 nm"
→ The AI should warn immediately, regardless of whatever the user says next
```

### Node 7a: Literature Anchors

**Must include**: 3-5 references that "every researcher in this field should
know"

**Authoring principles**:
- Prefer, in order: Textbook > Review > Methods paper
- For each reference, note "why this one is essential reading" (what
  standard terminology it defines, what methodology it established)
- This is a curated *reading list*, not the citation registry — a source can
  (and often should) appear in both 7a and 7b, but 7a alone does not satisfy
  the requirement that every inline `[Key]` used in Nodes 1-6 resolve
  somewhere in the profile

### Node 7b: Source Ledger (required — added 2026-08-24, see §3.2)

**Must include**, one row per citation key used anywhere in Nodes 1-6:
- **Key** — the exact `[Author Year]` string used inline
- **Full citation** — author(s), year, title, venue
- **Identifier** — DOI / arXiv ID / URL / patent number / vendor spec name —
  whatever lets a reader actually locate the source
- **Access tag** — `[full]` / `[partial]` / `[abstract]` / `[secondary]`,
  same semantics as `literature-search-extract` P3
- **Verification status** — ✅ Confirmed / `~` Approximate / ⚠ Unconfirmed /
  ❌ Withdrawn (see the legend in `_template.md`'s Node 7b for exact meaning)
- **Verified (date)** — the date this row's claim was last checked against the primary source,
  distinct from the source's own publication year; add an inline `review-when:` note only when a
  specific, nameable future trigger is known (§3.7)
- **Locator** — section/table/figure/page within the source where the cited
  claim actually lives
- **Used in** — which Node/row cites this key (so a later editor can find
  every place a correction needs to propagate)

**Authoring principles**:
- Fill this in *as you write* Nodes 1-6, not as a cleanup pass afterward —
  authoring citations without a ledger is exactly the failure this node
  exists to prevent (see §3.2 for the incident that motivated it)
- An entry does not need ✅ to be included — ⚠ Unconfirmed is an honest,
  useful status as long as it's visible wherever that key is cited; what's
  not acceptable is a key with *no* ledger row at all
- ❌ Withdrawn rows are not deleted — they document what was tried and found
  wrong, so a future editor doesn't re-introduce the same unverified claim

### Standing triggers (formerly "Node 8" — abolished 2026-08-24)

Profiles no longer end with an "AI Decision-Trigger Checklist". Measurement showed that node
was an unsourced second copy of Node 6 (and, for its residue, of Node 1's decision point, the
Cross-Domain tables, and SKILL.md's generic mechanics) — see §3.6 for the evidence, the
architecture that replaced it, and the migration dispositions. When authoring, put each
would-be "trigger" in its §3.6 home; do not create a checklist.

---

## 5. AI Behavioral Rules: When Confirmation with the User Is Mandatory

In the following situations, the AI must not assume anything on its own and
must confirm the user's current need and goal.

### Category A: Theoretical-framework divergence (scale/model choice)

**Trigger phrases**:
- "I want to simulate X" → must confirm the intended simulation scale
- "I want to compute Y" → confirm whether this is a first-principles
  calculation or a device-level one
- "I'm using model Z" → confirm whether model Z is applicable at the current
  problem's scale/material/frequency range

**Why the AI cannot assume**:
The same term (e.g. "simulate carrier transport") means something entirely
different at the DFT, k·p, and TCAD levels. Picking the wrong level
invalidates the entire computational path, and this is very hard to notice
partway through.

### Category B: Research-goal trade-off triangle

**Trigger phrases**:
- A design task described in terms of "performance metrics" (maximize
  efficiency, minimize loss)
- And the domain has a known "trade-off triangle" (e.g. SPP's
  confinement–propagation–loss triangle, or a semiconductor device's
  speed–power–breakdown-voltage triangle)

**How to confirm**:
"What is your priority ordering among design goals (A)... / (B)... / (C)...?
Different orderings lead to different optimization directions."

**Why the AI cannot assume**:
A trade-off triangle has no single "optimal solution" — only a "Pareto-optimal
point" for a specific goal. The AI choosing on its own is effectively making
the user's research-direction decision for them.

### Category C: Invasive/destructive measurement tools

**Trigger phrases**:
- The user has planned a sequence of measurement steps that includes a
  destructive measurement (TEM, SIMS, FIB)
- And that destructive measurement is placed in the middle of the sequence

**How to confirm**:
"[Tool name] is a destructive measurement — the sample cannot be used for
further measurements afterward. Has your measurement order already accounted
for this?"

**Why the AI cannot assume**:
Sample preparation is costly (epitaxy/nanofabrication can take days to
weeks); getting the destructive-measurement order wrong can make the rest of
the plan impossible to execute.

### Category D: Model choice in data fitting

**Trigger phrases**:
- The user describes a fitting task, and the Domain Profile has a
  corresponding "domain-specific pitfall" for it
- The user hasn't explained why they chose that particular fitting model

**How to confirm**:
"[Fitting method] has an applicability condition: [condition description].
Does your sample meet this condition?"

**Why the AI cannot assume**:
The wrong fitting model produces a result that "looks numerically reasonable
but is physically meaningless" — this is the hardest type of error to catch
after the fact.

### Category E: Anomalous results (too good or too bad)

**Trigger phrases**:
- The value the user reports for a metric falls outside the Domain Profile's
  "typical value range" (whether too high or too low)

**How to confirm**:
"The [metric] value you reported ([value]) is [above/below] the typical range
for this field ([typical value]). Has this been cross-confirmed with another
measurement method?"

**Why the AI cannot assume**:
An anomalous result could be either a major discovery or a measurement/
computation error. Until the user confirms which, the AI should not steer the
interpretation toward either direction.

### Category F: Cross-domain conflict (highest alert level)

**Trigger phrases**:
- The user's question spans two Domain Profiles, and the two Profiles'
  "inviolable physical constraints" potentially conflict

**How to confirm**:
"Your research spans [Domain A] and [Domain B], which apply different
judgment criteria on [specific issue]. Which domain's standard are you
currently treating as primary?"

**Example**:
- A user researching "TiN as an SPP waveguide material" → involves both
  ti_materials.md (TiN mechanical/compositional properties) and
  plasmonic_waveguide.md (ε(ω) accuracy)
- The two Profiles have different concerns about "how to measure TiN's
  optical properties" (the Ti-materials profile cares about composition; the
  Plasmonics profile cares about ε(ω) accuracy)

---

## 6. Domain Profile Quality Verification Checklist

Before a newly created Domain Profile is added to the SKILL, it should pass
the following checks:

### Structural completeness

- [ ] All seven nodes (1-6, 7a+7b) are present; Node 1 contains the mandatory Decision point
  under the canonical phrase **"Decision point (mandatory Tier 0 confirmation)"** — two
  profiles once carried it under an ad-hoc heading, which made it invisible to the canonical
  grep and invited a duplicate in the abolished Node 8 (see §3.6)
- [ ] **No "AI Decision-Trigger Checklist" section exists** (`grep -rln 'AI Decision-Trigger
  Checklist' domains/` finds nothing; §3.6). Every trigger lives in its §3.6 home
- [ ] Each node table carries its required-core columns (§3.3 rule 2); run
  `tools/profile-lint.py` rather than checking by eye
- [ ] All table columns are filled in (no blank cells; an explicit honest marker such as
  `⚠ not re-verified since authoring` counts as filled — §3.8)
- [ ] There are no fewer than 6 common assumption pitfalls, each with the core columns complete
  (including Source [Key]), and every `Trigger condition` written in the asker's words (§4
  Node 6)
- [ ] **No template instruction text survives in the profile.** A filled profile
  contains no `### Authoring notes` block copied verbatim from `_template.md`
  (the two blocks under Cross-Domain Links / Cross-Domain Conflict Notes are
  marked TEMPLATE-ONLY there and must be deleted, not left behind). If a profile
  genuinely needs to record a boundary ruling or a how-to-use note at that
  position, give it its own heading — `### Boundary & ownership notes` or
  `### How the AI should use these prompts` — so runtime content is never
  confused with authoring scaffolding. Re-derive across all profiles with:
  `grep -rn '^### Authoring notes' domains/` — the only legal hit is `_template.md`.
  *review-when:* `_template.md`'s tail sections change.

### Citation traceability (added 2026-08-24 — see §3.2)

- [ ] Every inline `[Key]` used in Nodes 1-6 has a matching row in the Node
  7b Source Ledger — no opaque index-only citations (`[web:12]`-style)
- [ ] Every Source Ledger row has an access tag and a verification status;
  ⚠ Unconfirmed is acceptable, a missing row is not
- [ ] Every Source Ledger row has a **Verified (date)** cell (§3.7); rows on a known-changeable
  fact (a standard, a vendor page, an abstract-only source pending full text) carry a
  `review-when:` note naming the specific trigger, not a vague "re-check later"
- [ ] Every row citing a **versioned source** (standard issue, arXiv vN, datasheet rev, software
  version) pins the exact issue/version consulted in Identifier or Full citation (§3.7) — a
  `review-when: next revision` note without the pin is undecidable
- [ ] Node 5 rows quoting a "research frontier level" range state the as-of year in the
  Conditions cell (§4 Node 5) — the frontier moves while the source stays valid
- [ ] Every quantitative claim in Node 5 (and any quoted number elsewhere)
  states its conditions (material system/method/wavelength/temperature) in
  the same row/sentence as the number, not only implied by the section title

### Content quality

- [ ] The "inviolable physical constraints" can be converted into precise
  if-then rules
- [ ] Every measurement tool has a description of "when it doesn't apply"
- [ ] Typical value ranges are backed by literature and distinguish research
  level from commercial level
- [ ] Literature anchors (7a) point to original papers that are actually
  accessible (not secondary sources)

### Boundary clarity

- [ ] The Profile's scope of applicability is clearly stated (to avoid
  overlap with other Profiles)
- [ ] A comparison against the closest existing Domain Profile confirms
  sufficient difference in measurement tools / first principles / quality
  metrics
- [ ] If the profile partitions one physical system with existing peers, the sibling-cluster
  registration (§2) is done in the same change: `_routing.md` § Clusters row + header
  membership note + no copied cross-member numbers

### Cross-domain compatibility

- [ ] The domains this profile is most likely to cross with have been
  identified
- [ ] In a cross-domain situation, there is a clear Layer-A-Tier mapping for
  how the AI should switch between the two Profiles

---

## 7. _template.md (Blank Template for Adding a New Domain Profile)

> **Canonical copy lives at `domains/_template.md` — not duplicated here.** An earlier
> version of this guide *did* paste a full second copy of the template inline, and the two
> copies drifted out of sync the moment one was updated and the other wasn't (fixed
> 2026-08-24, same pass that added the Source Ledger requirement in §3.2). One template, one
> location: open `_template.md` directly when starting a new profile. Its structure, in
> brief: the metadata block → a required "Citation convention" block (the two rules from
> §3.2) → Nodes 1-6 (each table now carries a `Source [Key]` column, and Node 5 also carries
> a `Conditions` column) → Node 7a (curated reading list) → Node 7b (Source Ledger — the
> resolution key for every `[Key]` used above, with access-tag and verification-status
> legends) → Cross-Domain Links → Cross-Domain Conflict Notes. There is no trailing trigger
> checklist (§3.6). Copy that file's current content wholesale to start a new profile; do not
> hand-retype it from this section.

---

## 8. Sub-profile mini-template (Blank Template for a Branch)

A sub-profile is NOT a full 7-node profile. It **inherits** the parent base profile's
Nodes 1-3 (theoretical framework, measurement tools, modeling toolchain) and fills only the
nodes where it adds specialist judgment. Omit any node it does not extend. It MUST have its
own Node 6 — branch pitfalls with a filled `Trigger condition` column — because standing
triggers are what make it a sub-profile rather than a reference (§3.6; the former trailing
checklist is abolished). If the branch has a goal fork of its own, add a `> **Decision point**`
block in the same format as a base profile's Node 1; do not encode clarification asks as
pitfall rows.

Register it in `domains/_routing.md` as a `sub-profile` row before it is considered done.
It follows the same citation convention as a base profile (§3.2 **and §3.7** — per-row
`Verified (date)`, `review-when:` only on nameable triggers, version pinning for versioned
sources): inline `[Key]` citations, never opaque indices, plus a Source Ledger — either its own
small `## Source Ledger` node (preferred if the branch introduces several new sources) or new
rows added directly to the parent's Node 7b (fine if it only cites one or two sources already
in the parent's ledger).

```markdown
# Sub-profile: <Branch Name> (English full name) — under <Parent Domain>

> Parent domain: <domain_name>.md
> Branch axis: material | phenomenon | method | new-territory
> Scope (1-2 lines): what this branch covers, and where it stops (defer to parent / sibling).
> Inherits from parent: Nodes 1-3 (theory / tools / toolchain) unless overridden below.

> **Decision point** (include only if the branch has its own goal fork): when the user
> describes [X], confirm: "Is your goal (A)… / (B)… / (C)…?"

## 4. Branch-Specific Fitting Methods   (include only if it adds any)

| Method | Applicable conditions | Common error | Correct approach | Source [Key] |
|---|---|---|---|---|
| | | ⚠️ | | |

## 5. Branch-Specific Quality Metrics   (include only if it adds any)

| Metric | Abbreviation | Physical meaning | Typical value range | Conditions | Source [Key] |
|------|------|---------|------------|------|------|
| | | | | | |

## 6. Branch-Specific Assumption Pitfalls   (the core payload)

| Pitfall | Trigger condition | How to recognize it | Correct approach | Source [Key] |
|------|---------|---------|---------|---------|
| | | | | |

## Source Ledger   (branch-specific sources only; or add rows to the parent's Node 7b instead)

| Key | Full citation | Identifier | Access tag | Verification status | Verified (date) | Locator | Used in |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
```

> **Promotion note.** A new-territory sub-profile that later grows a non-overlapping toolset
> or an incompatible quality-metric set has crossed Gate 1 — promote it to its own base
> profile (7 nodes) and leave a boundary note behind in the parent. Do not pre-promote.

---

## 9. Authoring pipeline: from source packet to registered profile

> One page, start to finish. This consolidates what previously lived scattered across
> scientific-research-guide-FUTURE-WORK.md's "fixed procedure", §3.2–§3.6, §6, and `_routing.md` § Maintenance — the
> scattering itself was a collection-side friction source. scientific-research-guide-FUTURE-WORK.md now points here.

**Intake stance: assume the packet is defective until each anchor is resolved.** Every
AI-research-tool packet ingested to date (three on 2026-08-24 alone) carried wrong first
authors, wrong titles/venues, mischaracterized mechanisms, or opaque citation indices. The
pipeline therefore front-loads citation resolution — it is cheaper than the two-pass repairs
this skill has already paid for twice.

1. **Classify** the content with §2's gates (and the sibling-cluster test if it partitions a
   system with existing peers): new base / sub-profile / reference / boundary note — or an
   extension of an existing file.
2. **Resolve every anchor BEFORE any claim enters a node.** For an AI-packet source: re-derive
   each citation against publisher metadata (Crossref/DOI) or the primary text; record the
   per-anchor verdicts as a **Provenance & correction log** inside §7b (required whenever the
   source is an AI-research packet — the pattern in `fiber_chip_passive_alignment.md` §7b).
   A claim may be added *or removed* only against text quotable with a locator; summaries
   locate candidates, never settle them. **Stamp each row's `Verified (date)` at resolution
   time** (§3.7) — this step *is* the last check against the primary source, so the cell is
   free to fill here and expensive to reconstruct later; while at the source, also check for
   errata/retraction, pin the issue/version of any versioned source, and add a `review-when:`
   note only where a specific nameable trigger exists.
3. **Fill the template** (`_template.md`, or §8's mini-template for a branch): Nodes 1–6 with
   `[Key]` citations and the ledger filled **as you write**, conditions in the same breath as
   every number (§3.2), triggers in their §3.6 homes, trigger conditions in the asker's words.
4. **Register**: `_routing.md` row (keywords = words the asker would type), cluster block if
   applicable, reciprocal Cross-Domain rows in the affected neighbours — remember each profile
   has TWO cross-domain tables (Links AND Conflict Notes); a re-pointing pass must sweep both.
   **Do not check keyword collisions by eye — step 5's linter does it.** Eyeballing compares
   strings for equality, and the real collisions are containments: the 2026-08-26 pass
   deliberately avoided reusing `siph_packaging_reliability`'s `thermal crosstalk` and still
   collided with it, because `ring-to-ring thermal crosstalk` contains it. An overlap the
   linter reports is either a keyword to narrow or a row to add to `_routing.md`
   § Known keyword overlaps — and adding that row is a routing decision (it asserts both files
   loading together is what you want), not a way to silence the lint. A *third* answer exists
   and was used on 2026-08-26: the overlap may be an instrument artefact, when the short
   keyword sits on a row the containing keyword cannot reach (a `sub-profile` whose parent
   domain the prompt never matches). Declaring one of those records an intent nobody holds —
   fix the check, not the manifest.
   **One spelling per term.** Matching is NFKC-folded, so `Bi₂Se₃`, `Bi2Se3` and the
   full-width form are one keyword; listing variants adds nothing and is reported as
   REDUNDANT-VARIANT. What the fold does NOT cover is a term the row never listed at all —
   step 6's baseline is what finds those.
5. **Verify mechanically**: run `tools/profile-lint.py` (structure, citation markers, manifest
   and register closure incl. dead rows, keyword overlaps, weak anchors, redundant variants);
   run §3.4's citation command; walk §6's checklist for the judgment-level items the linter
   cannot rule on. **Run the seeded fixture beside it** —
   `python tools/profile-lint.py --root evals/fixtures/routing-collision` — and check the
   counts against that fixture's own header. Since 2026-08-26 the live tree holds no
   KEYWORD-OVERLAP finding, so a clean live run no longer distinguishes a working check from
   a broken one; the fixture is the only positive control left.
6. **Wire in and test in the same change, not later**: SKILL.md description keywords,
   `~/.claude/skill-trigger-dict.md` entry, and an eval routing case in `evals/evals.json`,
   actually run. (Five profiles once shipped over three weeks with this step deferred; the
   first negative control written found a real defect immediately.) **Do not decide the re-run
   scope by eye either** — run `python tools/eval-impact.py` and re-grade the cases it names;
   it replays Gate A Step 0 rung 1 over every case's prompt and reports which load-sets your
   change actually moved. Give the new case a `depends_on` block while you are in the file
   (`grounded_in` from the evidence you just wrote; `routing_sensitive` true if the verdict
   depends on which files load), and refresh the baseline in the same commit as the re-grade:
   `python tools/eval-impact.py --update-baseline`. When in doubt, `--conservative`.
7. Feature branch → lint + evals pass → merge; STATUS.md entry records what was verified and
   what remains ⚠/❌.

---

## Appendix: SKILL Directory Structure (this skill's actual layout)

> **Share note**: the tree below is the source environment's layout, kept as a worked
> example of a populated `domains/`. The concrete profile files it names do NOT ship
> with this copy — see `README.md` in this folder. Read the names as illustrations of the
> base / sub-profile / reference / boundary pattern, not as files to look for.

```
skills/scientific-research-guide/
├── SKILL.md                          ← Operating protocol (Gate A-E; load order:
│                                        tier framework first, then domain, then session)
├── references/
│   ├── tier-framework.md             ← Layer A: generic Tier 0-7 skeleton
│   │                                    (not modified per domain)
│   ├── method-selection.md           ← Generic method-selection decision aids
│   └── deliverables.md               ← Output templates for each Tier
├── domains/                          ← Layer B: domain-specific content
│   ├── _routing.md                   ← Manifest: which domain files exist + load triggers
│   ├── _template.md                  ← Blank template for a new BASE profile (7 nodes)
│   ├── domain-expansion-guide.md     ← This document (expansion conventions)
│   ├── plasmonic_waveguide.md        ← base profile (established)
│   ├── plasmonic_waveguide/          ← that domain's sub-profiles, reference & boundary notes
│   │   ├── active_modulation.md          ← sub-profile (method/material platform)
│   │   ├── terminology_and_geometry.md   ← reference (no standing triggers)
│   │   └── split_ring_resonators.md      ← boundary note (routes to a future metamaterial domain)
│   ├── topological_insulator.md      ← base profile (established; structurally complete
│   │                                    as of 2026-08-24 — Nodes 3-8 authored, full Source
│   │                                    Ledger; two ledger entries remain representative-
│   │                                    rather-than-exact sources, see its own Node 7b)
│   ├── topological_insulator/        ← that domain's sub-profiles
│   │   ├── bi2se3_material.md            ← sub-profile (material)
│   │   ├── bi2se3_plasmonic_photoresponse.md ← sub-profile (method; Bi2Se3 plasmon/CPGE/LPGE)
│   │   ├── wal_hln_transport.md          ← sub-profile (phenomenon/method)
│   │   ├── surface_and_composition_characterization.md ← sub-profile (method)
│   │   └── device_fabrication.md         ← sub-profile (method)
│   ├── gan_power_device.md           ← base profile (vertical GaN power devices)
│   └── microled.md                   ← base profile (inorganic microLED devices)
├── references/
│   └── user-supplied-citations.md    ← source-provenance inbox for user-supplied URLs
│                                        (not a domain file; listed here for completeness)
├── tools/
│   └── profile-lint.py               ← Deterministic structure/schema/citation-marker linter
│                                        (run after any structural edit; see §3.3, §6)
└── evals/
    └── evals.json                    ← Test cases
```

> Sub-profile folders (`domains/<domain>/`) are created only when a domain actually needs
> its first branch — do not pre-create empty folders. This listing reflects the actual
> files as of 2026-08-03; treat it as a snapshot, not a guarantee — check the directory
> and `_routing.md` for the current state.
