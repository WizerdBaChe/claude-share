---
paths:
  - "**/router*.{ts,tsx,js,jsx}"
  - "**/routes/**"
  - "**/*nav*.{ts,tsx,js,jsx,vue,svelte}"
  - "**/*Nav*.{ts,tsx,js,jsx,vue,svelte}"
  - "**/index.html"
  - "**/main.html"
---

# Navigation state and addressability

Raised 2026-09-09 from a live two-sided measurement (`skills/ux-walkthrough/references/navigation-ia-contract.md`
§6): an external surface that routes cleanly by query parameter while **0 of its
23 navigation destinations are reachable by keyboard**, and this machine's own
HTMLToolsLobby, whose navigation is exemplary (`<a href>` + `aria-current`) while
its 18-tool filter and search keep **no state in the URL at all** (zero
`URLSearchParams|pushState|replaceState|location.hash` in `index.html` +
`assets/js/lobby.js`). Each surface passes where the other fails, so neither
property implies the other and both must be stated. Applies to interfaces this
repo AUTHORS, not to vendored or generated third-party files. Index line lives in
`CLAUDE.md`.

**Asset property — a web interface with more than one destination carries the
person's current destination in its URL.** Reload, Back, and a link opened in a
clean session all resolve to the same view. State deliberately excluded (secrets,
volume, privacy) is named with its reason at the routing seam; an exclusion with
no stated reason is a defect, not a decision.

**Asset property — every navigation destination is an operable control.** A
native `a[href]` or `button`, reachable by Tab, activated by Enter/Space, and the
current one marked with `aria-current`. A `div`/`nav` carrying `data-*` plus a
click handler routes correctly and affords nothing; routing correctness is not
evidence of navigability.

**Asset property — anything the interface remembers on the device declares its
scope where the person is.** The sentence saying what loses it (other device,
other browser, cleared storage) sits in the view that owns the state, and matches
the storage call.

Full vocabulary, the questions that produce these findings, and the ruling
attribution (which of them are the user's call and which are engineering's):
`skills/ux-walkthrough/references/navigation-ia-contract.md` — `NAV-6` / `NAV-8`
/ `NAV-10`, with `usability-evidence.md` §2 carrying the runnable checks.

## review-when

- A project adopts a framework whose router owns the URL contract (Next.js app
  router, Nuxt, TanStack Router): the addressability PROPERTY carries over
  unchanged, the mechanism becomes the framework's and this file stops naming it.
- The three checks in `usability-evidence.md` §2 gain a runnable harness (a
  `tools/` gate rather than a walk item): `detect:` moves from `audit` to that
  gate here and in the contract's entries.
