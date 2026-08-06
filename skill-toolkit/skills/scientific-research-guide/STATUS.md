# scientific-research-guide — Status (as of 2026-08-03)

> Single-file context rebuild. Reading this alone should be enough to know what is
> done, what is verified, and where to pick up. Detail lives in FUTURE-WORK.md.

## What this skill is
Advisory companion for natural/engineering-science research methodology. Three
layers: Layer A generic tier framework (`references/`), Layer B domain profiles
(`domains/`), Layer C session context. Non-intrusive: advice first, acts on data/
code only on explicit request (Gate C).

## Structure
- `SKILL.md` — operating protocol, 5 stage-gates (A triage / B verify / C
  non-intrusion / D deliverable / E iteration). 251 lines (~1 line over the 250 soft
  budget after the 2026-08-03 sync; not worth a churn-only trim).
- `references/` — tier-framework.md (7 tiers), method-selection.md, deliverables.md,
  user-supplied-citations.md (source-provenance inbox, added 2026-08-03).
- `domains/` — `_routing.md` manifest (single source of truth for the load list),
  `_template.md`, `domain-expansion-guide.md`; base profiles
  `plasmonic_waveguide.md`, `topological_insulator.md`, `gan_power_device.md`,
  `microled.md`; sub-profiles/reference/boundary notes:
  `topological_insulator/{bi2se3_material,bi2se3_plasmonic_photoresponse,
  wal_hln_transport,surface_and_composition_characterization,device_fabrication}.md`,
  `plasmonic_waveguide/{active_modulation,terminology_and_geometry(ref),
  split_ring_resonators(boundary)}.md`.
- `evals/evals.json` — 5 cases (tier triage / stat-test choice / explicit-action
  boundary / Bi₂Se₃ sub-profile routing / research-state continuity), with
  `evals/fixtures/research-state.example.md` backing case 5.

## 2026-07-28 domain expansion (synced from external editing copy)
6 new domain files added under `domains/plasmonic_waveguide/` and
`domains/topological_insulator/` (2 sub-profiles, 1 reference, 1 boundary note under
plasmonics; 3 sub-profiles under TI), plus a content addition to the existing
`bi2se3_material.md` sub-profile. Source: a chaptered notes attachment, cross-checked
against 24 resolvable-DOI literature sources — no unsourced recipe values or chat/UI
fragments carried in; ambiguous terms (`LSRR`, `MIN`, `consort`, `KOH` role) kept as
guardrails, not resolved by guessing. Full audit trail:
`reports/2026-07-28-scientific-research-guide-domain-integration-audit.md`.
Verified before merge: `domains/_routing.md` entries match actual files; each new
sub-profile follows the mini-template (parent link, branch axis, inherited nodes,
Node 4-6 as applicable, Decision-Trigger Checklist, Evidence Anchors).

## 2026-08-03 domain expansion (synced from external editing copy)
Two new base domains and one new TI sub-profile, integrated from a supplied material
packet (GaN power devices, MicroLED, Bi2Se3 plasmonic/photogalvanic response) cross-checked
against resolvable-DOI literature: `domains/gan_power_device.md` (vertical GaN power
devices: trench MOSFET/OG-FET/CAVET, field-shield design, TCAD, electrical extraction),
`domains/microled.md` (InGaN blue-green and AlGaInP red microLED: size/sidewall effect,
recombination, optical extraction), and `domains/topological_insulator/
bi2se3_plasmonic_photoresponse.md` (Bi2Se3 Dirac/bulk/2DEG plasmon channels, CPGE/LPGE,
waveguide-coupled photocurrent — a method sub-profile of the existing `topological_insulator`
domain, not a new domain). `bi2se3_material.md` gained a cross-reference to the new
sub-profile without duplicating its material/thickness/oxidation/transport content.
Also added `references/user-supplied-citations.md`: a source-provenance inbox for
user-supplied URLs (identity/DOI-checked promotion candidates vs. [untriaged] entries),
referenced from `SKILL.md`'s reference-file index. No unsourced recipe values, coverage
checklists, or unresolved `[web:n]` markers were carried into the new profiles; ambiguous
terms (`TBD` outside its one traceable paper, `TDEL`, "front-light collection", "scorching
heat generation", "angular modulation") were kept as guardrails, not resolved by guessing.
Full audit trail: `reports/2026-08-03-scientific-research-guide-material-integration.md`.
Verified before merge: `domains/_routing.md` rows match actual files and have no keyword
collisions with existing domains; each new profile follows the 7-node template (or the
sub-profile mini-template) with the required Decision-Trigger Checklist.

## Known pre-existing debt (not touched by the 2026-07-28 or 2026-08-03 syncs — flagging, not fixing)
- `domains/topological_insulator.md` (base profile) is truncated: it ends immediately
  after the "## 3. Standard Modeling Toolchain" heading with no body and no Nodes 4-8.
  Any sub-profile under this domain currently states "parent Node 3 is incomplete."
- The same file still carries 35 `[web:n]` placeholder citations instead of resolved
  literature anchors.
- This STATUS.md's prior "all cross-references verified consistent" claim did not
  account for the above — softened in this revision.

## Verified
- **Evals executed 2026-07-12** (sonnet=Sonnet 5, subagents, protocol-level
  adversarial grading): **5/5 cases pass, 19/19 assertions.** Results + evidence
  written back into evals/evals.json (`run` block + per-assertion `passed`/`evidence`).
- Structural consistency: every SKILL.md / _routing.md reference points to a file
  that exists; routing manifest matches actual domain files and eval #4's routing
  assumption. No broken links.

## Known limitation (recorded, accepted for v1)
- Plausibility/range-check only fires for a loaded domain profile. A generic metric
  (e.g. CNN Dice=0.82) has no calibrated range flag — caught only via generic
  V&V/UQ gap-naming. A generic-metric sanity band would strengthen case-1 behaviour.

## Open items (from FUTURE-WORK.md — none block "v1 verified")
1. **research-state.md mechanism** — DONE 2026-07-12 (branch
   feat/research-state-mechanism): Gate A continuity check + Gate D consent-gated
   update + deliverables.md template + eval case 5 (run, pass).
2. **description-trigger optimization loop** (skill-creator run_loop, 20 queries) —
   never run; run only if under/over-triggering is observed.
3. **config-self-audit** — no formal audit yet. Cheap; worth doing.
4. **scripts/ deterministic tools** — DELIBERATELY deferred (build only after the
   same analysis is hand-written ≥2×). NOT a gap; do not flag as incomplete.

## Pick up here
Open-item ① is done. Remaining cheap hygiene: ②(trigger loop, only if mis-triggering
seen) and ③(config-self-audit). Leave ④ alone until real repeated need appears. Two
prose-only residual gaps are logged in evals.json `run.known_limitation` (generic-metric
range band; research-state prerequisite convergence check) — optional hardening, not blockers.
