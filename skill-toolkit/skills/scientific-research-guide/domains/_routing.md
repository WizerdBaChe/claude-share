# Domain Routing Manifest

> Single source of truth for **which domain files exist** and **when to load each**.
> Gate A Step 0 (SKILL.md) consults this file before loading any Layer-B content.
> Keep it terse — this file is read on every domain-triage turn. One row per file.

## How Gate A uses this manifest

1. **Identify domain** — match the user's field against the `base` rows' triggers.
2. **Load the base profile** — always load the matched domain's base profile alongside
   the tier framework. Its Node 6 (pitfalls) + Node 8 (decision triggers) become standing
   if-then rules for the whole turn.
3. **Scan sub-profiles of that domain** — for every `sub-profile` row whose parent is the
   matched domain, check its load trigger against the user's wording. On a match, **load it
   and activate its own Node 6/8 triggers** (they fire like the base profile's).
4. **Pull references on demand only** — `reference` / `boundary` rows are loaded only when
   the specific topic is explicitly engaged; they carry no standing triggers. A `boundary`
   row's job is to route the user *out* to a sibling domain when they cross the edge.

Type semantics are defined in `domain-expansion-guide.md` §2 (the two-gate decision tree).

## Manifest

| Type | File | Parent | Load trigger (keywords) | Covers / role | Active triggers? |
|---|---|---|---|---|---|
| base | `plasmonic_waveguide.md` | — | SPP, plasmonics, surface plasmon, nanophotonic waveguide, SERS, near-field optics | Plasmonic/SPP waveguide domain profile | yes (Node 6+8) |
| base | `topological_insulator.md` | — | topological insulator, TI, Z₂, quantum spin Hall, Dirac surface state, QAHE, Majorana | Topological-insulator domain profile | yes (Node 6+8) |
| sub-profile | `topological_insulator/bi2se3_material.md` | topological_insulator | Bi2Se3, bismuth selenide, Se vacancy, bulk conduction, quintuple layer, ultrathin film, HLN, intercalation | Material-scoped sub-profile: Bi₂Se₃ bulk-conduction / thickness-gap / surface-chemistry traps | yes (Node 6+8) |

<!--
Add rows as content is authored. Only list files that ACTUALLY EXIST (Gate A will try to
load what it finds here). Row templates for the other two content types:

| sub-profile | `topological_insulator/wal.md`     | topological_insulator | WAL, weak antilocalization, HLN, Hikami-Larkin-Nagaoka, magnetoconductance | Phenomenon/method sub-profile: HLN-fit pitfalls | yes (Node 6+8) |
| sub-profile | `topological_insulator/hoti.md`    | topological_insulator | HOTI, higher-order topological, hinge state, corner state, nested Wilson loop | New-territory sub-profile: higher-order bulk-boundary | yes (Node 6+8) |
| boundary    | `topological_insulator/spt_vs_topological_order.md` | topological_insulator | SPT, symmetry-protected, topological order, long-range entanglement, anyon | Boundary note: routes OUT to a future intrinsic-topological-order domain | no |
-->

## Maintenance

- SKILL.md must NOT hardcode domain file paths — it points here. When you add a domain
  file, add its row here in the same change; that is the only place the load list lives.
- `base` files stay lean (the 7-node profile = the domain's shared core). Specialized
  branches go in `sub-profile` rows, not the base file — see the decision tree.
