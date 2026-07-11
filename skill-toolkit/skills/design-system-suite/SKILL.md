---
name: design-system-suite
description: >-
  Contract-first methodology + Day-1 checklist for MULTI-PRODUCT frontend suites and
  shared design systems: bootstrapping a new product into a suite/hub, unifying sibling
  apps under shared design tokens + theme packs, a versioned data-exchange contract,
  cross-app navigation. Trigger when the user mentions design tokens, theme packs,
  product suite/hub, or anti-silo cross-product needs. NOT for ordinary single-app
  development or one-off styling. Full disambiguation: ~/.claude/skill-trigger-dict.md.
---

# Design-system suite — contract-first

Born from unifying a multi-product browser-app suite into one system
*after* they were built. The whole point of this skill: do it **up front** next time.

> One line: **define the shared things as contracts first; products consume the
> contracts and are born conformant** — instead of each growing its own and
> retrofitting later.

## Reference implementation (real, maintained)

A complete worked example and copy-paste templates should live in the suite's own
repository:

- Playbook (full rationale + Day-1 checklist): `<suite-repository>/docs/design-first-playbook.md`
- Starter template (index.html / theme.css / theme-switch.ts): `<suite-repository>/docs/new-product-starter/`
- Live shared packages: `packages/tokens/` (theme packs), `packages/ui/suite-nav.js`, `packages/schema/`

If working in or near that repo, **read those files and copy from them** rather than
re-deriving. Elsewhere, the methodology below stands alone.

## The four contracts to define first

1. **Design tokens** (`@suite/tokens` pattern): share **structure** (spacing /
   radius / type / font — same values everywhere), define **colour only as semantic
   role names** (`--suite-bg` / `--suite-surface` / `--suite-text` / `--suite-accent` / status).
   Values come from **switchable theme packs** (`.suite-theme-*` classes on `<html>`).
   Namespace tokens (`--suite-*`) so they never clash with a product's local vars.
2. **Data envelope** (`@suite/schema` pattern): every export/import uses a
   versioned envelope `{ "<suite>": "1.0", "kind": "...", "source": {...}, "payload": {...} }`
   so one product's output is another's input.
3. **Anti-silo nav** (`<suite-nav>` pattern): a framework-agnostic web component that
   reads a manifest. Injected shared components MUST be **self-isolating** (Shadow
   DOM), **theme-aware** (consume `--suite-*`, which pierce the shadow boundary, with
   fallbacks), and **lifted** (`:host { position: relative; z-index: N }`) so host
   page overlays don't mask them.
4. **Capability manifest** (`suite-manifest.json`): machine-readable registry
   (id / stage / solves / consumes / produces / url). Adding a product = one entry.
   Portal, nav, and AI guidance all read it as the single source of truth.

## The iron rule

**Structure shared, colour per theme pack.** Components only use `var(--…)`, never
hardcoded hex. A product aliases its local vars to `--suite-*`; its domain-specific
colours stay local and are overridden per theme pack for legibility.

```css
:root { --surface: var(--suite-surface); --text: var(--suite-text); /* alias to roles */ }
.suite-theme-light  { --domaincolor: #128a6e; }  /* product-specific, per theme */
.suite-theme-hacker { --domaincolor: #39ff6a; }
```

## Suite conventions (decide once, all products follow)

- **Default theme = Light** for every product (including future ones).
- **Theme choice is NOT persisted** — each load resets to the default. Privacy:
  nothing stored on the device. Set it statically: `<html class="suite-theme-light">`
  (no script, no flash, no localStorage read).

## Day-1 checklist for a new product in the suite

1. Register one entry in the manifest (`products` + pain-point index).
2. Drop a product-level `AGENTS.md` (what it owns; what it doesn't → which sibling).
3. Adopt tokens: static theme class on `<html>` + load `tokens.css`.
4. New components use `var(--suite-*)`; alias local vars; override domain colours per theme.
5. Mount the suite nav (`current=<id>`, `manifest-url=...`).
6. Add a theme switcher (Light default, no persistence).
7. All exports/imports go through the schema envelope.
8. Deploy: static Pages via a GitHub Actions workflow (don't switch Pages to
   "Actions" mode without adding the deploy workflow, or pushes stop deploying).

## Pitfalls this skill exists to prevent

- Retrofitting unification → re-vendoring N copies, per-product re-coloring. Avoid by
  defining contracts first.
- Side effects in a React `useState` initializer → StrictMode double-invokes and
  clobbers them. Keep initializers pure; do side effects in an effect.
- Injected shared component looks wrong / gets masked on a host page → make it
  theme-aware + self-isolating + z-index-lifted.
- A UI "bug" assumed without looking → check the live/computed state first
  (curl the served HTML, read computed styles), then conclude.
- Vendor drift → document the single source of truth + the copy list; sync on change;
  package it once stable.
