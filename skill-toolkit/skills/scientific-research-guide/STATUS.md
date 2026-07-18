# scientific-research-guide — Status (as of 2026-07-12)

> Single-file context rebuild. Reading this alone should be enough to know what is
> done, what is verified, and where to pick up. Detail lives in FUTURE-WORK.md.

## What this skill is
Advisory companion for natural/engineering-science research methodology. Three
layers: Layer A generic tier framework (`references/`), Layer B domain profiles
(`domains/`), Layer C session context. Non-intrusive: advice first, acts on data/
code only on explicit request (Gate C).

## Structure (all cross-references verified consistent)
- `SKILL.md` — operating protocol, 5 stage-gates (A triage / B verify / C
  non-intrusion / D deliverable / E iteration). 232 lines (under the 250 budget).
- `references/` — tier-framework.md (7 tiers), method-selection.md, deliverables.md.
- `domains/` — `_routing.md` manifest (single source of truth for the load list),
  `_template.md`, `domain-expansion-guide.md`; base profiles
  `plasmonic_waveguide.md`, `topological_insulator.md`; sub-profile
  `topological_insulator/bi2se3_material.md`.
- `evals/evals.json` — 5 cases (tier triage / stat-test choice / explicit-action
  boundary / Bi₂Se₃ sub-profile routing / research-state continuity), with
  `evals/fixtures/research-state.example.md` backing case 5.

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
