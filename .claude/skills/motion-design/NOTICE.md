<!-- adopted-from: LottieFiles/motion-design-skill | source: f9a8a04 | adopted: 2026-08-01 | reconciled: 2026-08-12 -->
<!-- NOTE (share edition): the source environment's second adoption stamp, for
     a vendored Three.js package, is removed here because that package is NOT
     redistributed in this share — see the licence note below. A stamp for an
     absent tree would make config-self-audit adoption mode audit nothing. -->

# Third-party notices — motion-design hub

> The two stamps above are the machine-readable trigger for
> `config-self-audit` adoption mode (AD1). They deliberately carry **only** the
> four stamp fields — licence, modifications, and defects stay in the sections
> below, which are the human record. Duplicating them into the stamp would be a
> `40-maintenance.md` §2 violation.
>
> **Reconciliation ledger** (adoption pass 2026-08-12; the 2026-08-01 entry was
> `skill-share-packaging` Mode B, a security audit, which asks different
> questions):
>
> | artifact | source | collisions | class | resolution | mechanism | stamp |
> |---|---|---|---|---|---|---|
> | `vendor/lottiefiles/` | `f9a8a04` | 0 blocking | — | see AD notes | n/a — pure Markdown | `reconciled: 2026-08-12` |
> | `vendor/threejs/` | `b1c6230` | 0 blocking | — | frontmatter stripped at import | n/a — pure Markdown | `reconciled: 2026-08-12` |
>
> - **AD1** — provenance existed as prose but had no greppable trigger; that
>   was the finding, and these stamps are the fix.
> - **AD2** — `UPSTREAM-SKILL.md` retains `name: motion-design`, duplicating
>   the local skill's name and trigger list. NOT a defect: the rename away from
>   `SKILL.md` is what prevents registration, and it was done deliberately at
>   import. Recorded so the next reader does not "fix" it.
> - **AD3** — 29 cross-references resolved relative to their containing file;
>   0 broken. (A flat resolution check reports 2 false positives — resolve per
>   directory.)
> - **AD4** — no claim of external enforcement; both trees are pure Markdown.
> - **AD5** — the one real finding class. `vendor/lottiefiles/` carries
>   prescriptive craft defaults ("Never exceed 1/3 screen without intermediate
>   keyframe", "Always three motion layers"). For a METHODOLOGY package these
>   opinions are the payload, not contamination — unlike an inherited cap or
>   relaxation default, they advise on the domain rather than changing what the
>   agent does regardless of task. Accepted as defaults; revisit if they ever
>   override an explicit user direction on timing.

This skill is a **router** written locally. Everything under `vendor/` is
third-party content redistributed under its own license. Nothing in `vendor/`
is our work; nothing in `local/` or `SKILL.md` is theirs.

Audited on import 2026-08-01 (skill-share-packaging Mode B): both packages are
pure Markdown — no scripts, no executables, no network calls made by the skill
itself, no telemetry, no data collection, no instruction-injection patterns.
The only external URLs are Draco/KTX2 decoder CDN paths inside code examples.

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

## vendor/threejs/ — Three.js Skills

- Upstream: https://github.com/CloudAI-X/threejs-skills
- Commit at import: `b1c6230`
- License: **MIT**, as stated in the upstream `README.md`:
  "MIT License - Feel free to use, modify, and distribute."

> ⚠️ **License defect (recorded, accepted).** The upstream repository ships
> **no `LICENSE` file and names no copyright holder** — the MIT grant exists
> only as a README sentence. The grant is explicit and unambiguous in intent,
> so private use and modification are clearly covered. But because no copyright
> holder is named, a strict MIT attribution notice cannot be reproduced
> faithfully. Attribution here is therefore given to the repository itself.
> **If this content is ever redistributed outside this machine**, ask upstream
> to add a proper `LICENSE` file first, or replace the content. See
> `skill-share-packaging` before exporting.

**Modifications** (mechanical only, content unchanged):

1. YAML frontmatter removed from each file and replaced with a one-line HTML
   comment recording provenance — so these read as reference documents rather
   than registering as ten separate top-level skills.
2. Files renamed `skills/threejs-<x>/SKILL.md` → `vendor/threejs/<x>.md`.
3. `## See Also` cross-references rewritten from the bare skill name
   `` `threejs-loaders` `` to the new path `` `threejs/loaders.md` `` so the
   links still resolve.

No prose, table, or code example was edited. Verified by line-count parity
(each file is exactly `source − 4 + 2` lines, accounting for the frontmatter
swap).

---

## Local content

`SKILL.md` and everything under `local/` are original work for this
environment, not derived from either upstream package.
