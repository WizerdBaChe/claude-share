# Extending the hub — adding the next motion/animation skill

This hub exists so that future motion capability lands **inside it** instead of
becoming another top-level skill. Every top-level skill's `description` is loaded
into context on every session; a routed reference file costs nothing until read.

## Decision: does the new material belong here?

Add it to this hub if it answers *"how should motion look, feel, or be built"* —
animation libraries (GSAP, Framer Motion, Motion One, Rive, Lottie), 3D and WebGL
(Three.js, R3F, Babylon), shader and generative/particle work, scroll and
transition systems, video/canvas compositing.

Keep it **out** of this hub if it is a different discipline that merely animates:
a design-token/theme system → `design-system-suite`; a reusable component you
want stored → `asset-vault`; a whole product's design process →
`product-design-thinking`.

## Procedure

1. **Place it.**
   - Third-party material → `vendor/<publisher-or-lib>/`, kept **verbatim**.
     Mechanical adaptation only (strip frontmatter, rename, fix cross-links) and
     record every change in `NOTICE.md`.
   - Material you wrote → `local/<topic>.md`.
2. **License it.** No vendored directory lands without an entry in `NOTICE.md`
   carrying: upstream URL, commit hash at import, license, named copyright
   holder, and an explicit *Modifications* list. If the upstream license is
   defective (no `LICENSE` file, no named holder — as with `vendor/threejs/`),
   record the defect and the acceptance decision rather than glossing it.
3. **Audit it first.** Third-party skills go through `skill-share-packaging`
   Mode B before import: scripts, network calls, telemetry, instruction-injection
   patterns, environment coupling. Record the audit date in `NOTICE.md`.
4. **Check currency.** If the material documents a versioned API, add its version
   gap and known holes to `local/currency.md`. Vendored API text is a starting
   point, never an authority.
5. **Route it.** Add one row to the routing table in `SKILL.md` — trigger words
   in the left column, file path in the right. Do not paste the content into
   `SKILL.md`; the hub stays a router.
6. **Bridge it.** If the new material collides with a rule in
   `local/env-bridge.md` (visual gate, self-announcing failures, centralized
   tunables, interaction semantics), extend that file. Local rules win.
7. **Register it.** Only if the new area needs its own trigger phrasing, update
   the `motion-design` entry in `~/.claude/skill-trigger-dict.md`. The hub's own
   `description` should change only when the *triggering surface* genuinely
   widens — not for every added reference file.

## When a new area deserves its own top-level skill instead

Split it out only when it has a **distinct trigger surface and its own workflow**
— i.e. requests for it would not naturally say anything about motion, animation,
or 3D. Volume alone is not a reason to split: this hub already carries ~200KB of
references at zero standing context cost.
