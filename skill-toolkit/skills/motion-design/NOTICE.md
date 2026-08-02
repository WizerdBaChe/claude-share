# Third-party notices — motion-design hub

This skill is a **router** written locally. Everything under `vendor/` is
third-party content redistributed under its own license. Nothing in `vendor/`
is our work; nothing in `local/` or `SKILL.md` is theirs.

Audited on import 2026-08-01 (skill-share-packaging Mode B): the vendored
package is pure Markdown — no scripts, no executables, no network calls made
by the skill itself, no telemetry, no data collection, no instruction-injection
patterns.

---

## vendor/lottiefiles/ — Motion Design Skill

- Upstream: https://github.com/LottieFiles/motion-design-skill
- Commit at import: `f9a8a04`
- License: **MIT** — full text in `vendor/lottiefiles/LICENSE`
- Copyright: **Copyright (c) 2025 LottieFiles**
- Upstream version: 1.0.0 (frontmatter `metadata.author: LottieFiles`)

**Modifications**: none. The `director/`, `reference/`, and `patterns/` trees
are byte-identical to upstream, and the upstream `SKILL.md` is preserved as
`vendor/lottiefiles/UPSTREAM-SKILL.md` (kept for its own routing table and so
upstream refreshes can be diffed).

## Three.js material — deliberately NOT included in this share

The canonical environment this skill was exported from also vendored a
Three.js reference package:

- Upstream: https://github.com/cloudai-x/threejs-skills
- Commit at import (canonical environment): `b1c6230`
- License: **MIT**, as stated in the upstream `README.md`:
  "MIT License - Feel free to use, modify, and distribute."

> ⚠️ **License defect — this is why it's excluded here.** The upstream
> repository ships **no `LICENSE` file and names no copyright holder** — the
> MIT grant exists only as a README sentence. The grant is explicit and
> unambiguous in intent, so private use and modification are clearly covered.
> But because no copyright holder is named, a strict MIT attribution notice
> cannot be reproduced faithfully, and the canonical environment's own import
> log recorded this defect as **blocking redistribution outside that
> machine** until upstream adds a proper `LICENSE` file. This share honours
> that ruling: the Three.js text itself is not reproduced here.
>
> If you want it, fetch it yourself from the upstream URL above and run your
> own license/audit judgment (`skill-share-packaging` Mode B if you use that
> skill) — `local/currency.md` in this package documents the version-gap
> analysis (upstream claims r160+, current Three.js is r185+) that applied to
> the canonical environment's copy at import time, useful as a starting point
> if you re-run the same check against whatever you fetch.

The canonical environment's mechanical adaptation of that package (frontmatter
stripped, files renamed `skills/threejs-<x>/SKILL.md` → `<x>.md`, `## See
Also` links rewritten) is not reproduced here either, since the underlying
content isn't present.

---

## Local content

`SKILL.md` and everything under `local/` are original work for this
environment, not derived from either upstream package.
