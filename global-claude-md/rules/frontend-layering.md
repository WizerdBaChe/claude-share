---
paths:
  - "**/*.{ts,tsx,js,jsx,vue,svelte}"
  - "src/**"
---

# Frontend module layering

Sunk from global `CLAUDE.md` on 2026-08-11 (T-007): the trigger is "a file of
this kind is in play", which `paths:` observes directly, so this rule costs
nothing until it is relevant. Index line lives in `CLAUDE.md`; review-when: FSD
publishes a version that renames or renumbers the six layers (the names below go
stale, the "no same-tier lateral imports" property does not), or a project adopts
a framework whose own routing conventions own the top layers (Next.js app router,
Nuxt layers) — then the layer names are the framework's and only the
import-direction constraint carries over. A date is not a trigger: this line
replaced "review 2026-11" on 2026-09-08 (ES-3).

- **When laying out a frontend's module structure:** anchor on Feature-Sliced
  Design (FSD) v2.1+'s 6 layers — `app / pages / widgets / features / entities /
  shared` (top→bottom, each layer imports only from layers below). The rule with
  real teeth: **slices within the same layer must never import each other** —
  the one unidirectional constraint a lint/import-boundary check can
  mechanically enforce, turning "decoupled" from slogan into fact. Apply "no
  same-tier lateral imports" by analogy to backend/module layering even where
  FSD's layer names don't literally fit.
