# Currency & accuracy caveats — read before trusting a Three.js reference package

> **Note:** this share does not include `vendor/threejs/` (see `../NOTICE.md`
> for why — an upstream licence defect). Everything below documents the source
> environment's now-excluded copy of that package. It is kept here as a
> ready-made currency check to re-run if you fetch it yourself — the version
> gap, spot-checks and known gaps describe that specific upstream, not
> anything shipped in this package.

Import date: **2026-08-01**. This file records what was actually verified and
what was not. Treat it as the trust boundary on vendored API text.

## The version gap (the one that matters)

| | Version |
|---|---|
| Upstream README claims audit against | **r160+** |
| Three.js current release at import | **r185** (`three@0.185.1`, released 2026-07-01) |

That is roughly 25 releases of drift. Three.js does not follow semver; each
`r` release may remove deprecated API.

## What was spot-checked at import (and passed)

Greps across all ten vendored files found **no** use of API removed since r160:

- No `outputEncoding` / `sRGBEncoding` / `LinearEncoding` — the modern
  `outputColorSpace` / `SRGBColorSpace` / `.colorSpace` API is used instead
  (in `fundamentals.md`, `loaders.md`, `textures.md`).
- No `useLegacyLights` / `physicallyCorrectLights` (removed r165).
- No legacy `new THREE.Geometry()` — `BufferGeometry` throughout.
- Import paths use the current `three/addons/…` form.

So the **core content is usable**. The gap is coverage and pins, not rot.

## Known gaps — do NOT rely on `vendor/threejs/` for these

1. **WebGPU is entirely absent.** No `WebGPURenderer`, no `three/webgpu`
   entry point, no TSL (Three.js Shading Language). `vendor/threejs/shaders.md`
   teaches raw GLSL + `ShaderMaterial` only. If the task targets WebGPU or TSL,
   the vendored text is silent — go to the official docs, do not extrapolate.
2. **`loaders.md` pins CDN URLs to `three@0.160.0`** (KTX2 basis transcoder
   path) and Draco `1.5.6`. Bump these to match the project's installed `three`
   version rather than copying verbatim.
3. **Renderer/color-management defaults** have shifted repeatedly across r16x–r18x.
   Verify defaults against the installed version instead of assuming.
4. **Post-processing** is migrating toward the WebGPU node-based pipeline
   upstream; `postprocessing.md` documents the classic `EffectComposer` path.
   Still valid for WebGLRenderer, but it is no longer the only path.

## Standing rule for this skill

Global `CLAUDE.md` requires verifying volatile external facts (library
versions, API signatures) rather than answering from memory. `vendor/threejs/`
is a **starting point, not an authority**:

- Check the project's installed version first — `node -p "require('three').REVISION"`
  or the `three` entry in `package.json`.
- If it is materially newer than r160 **and** the task touches renderer setup,
  color management, post-processing, or shaders, confirm the specific signature
  against https://threejs.org/docs/ before writing code.
- Framework-agnostic content in `vendor/lottiefiles/` has no such expiry — it is
  design methodology (timing, easing, choreography), not API surface.

## Refreshing the vendored copy

Both upstreams are git repos. To refresh, re-clone and re-run the same
mechanical transform recorded in `../NOTICE.md` (strip frontmatter, rename,
rewrite `See Also` links), then update the commit hashes there and re-check
this file's claims. Do not hand-edit vendored files in place — that destroys
the "unmodified upstream" property the notice depends on.
