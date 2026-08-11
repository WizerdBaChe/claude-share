---
paths:
  - "**/*.{glsl,frag,vert,vs,fs}"
  - "shaders/**"
---

# Shader failure modes (GLSL ES)

Sunk from global `CLAUDE.md` on 2026-08-11 (T-007). The general rule it was
attached to — "a deliverable that can fail at runtime must announce its
failures" — stays in `CLAUDE.md`; only this file-type-specific case moved.
Index line lives in `CLAUDE.md`; review 2026-11.

- **GLSL ES, multi-texture sampling:** unroll into named uniforms.
  Variable-indexed sampler arrays and dynamic loop bounds **compile-fail as a
  silent blank** — the worst failure shape, because nothing reports it. Attach a
  shader-error callback so the compile failure surfaces instead of blanking.
- Corollary from the parent rule: a blank canvas is a defect, not a null result.
  State the likely failure modes and what the user would see for each.
