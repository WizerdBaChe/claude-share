---
paths:
  - "**/*.{glsl,frag,vert,vs,fs}"
  - "**/shaders/**"
  - "**/glsl/**"
  - "**/webgl/**"
  - "**/*shader*.{ts,tsx,js,jsx,mjs}"
  - "**/*glsl*.{ts,tsx,js,jsx,mjs}"
  - "**/*webgl*.{ts,tsx,js,jsx,mjs}"
  - "**/*three*.{ts,tsx,js,jsx,mjs}"
  - "**/parallax*.{ts,tsx,js,jsx,mjs}"
  - "**/ldi*.{ts,tsx,js,jsx,mjs}"
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

## Glob history — read this before trusting the trigger (2026-08-19)

The original globs (`**/*.{glsl,frag,vert,vs,fs}` + `shaders/**`) matched
**zero files in the project this rule was extracted from**, and the rule fired
exactly **once in 1,094 sessions**. Every line of GLSL in the 3D Photo
Synthesis Engine lives in template strings inside `frontend/src/parallax.ts`
and `ldi.ts` — matching WORK existed (three rounds of GLSL debugging, one of
them the exact silent-blank described above); matching FILES did not.

Measured over 1,361 first-party source files under the local work root (vendor,
`node_modules` and archives excluded), of which exactly 2 contain GLSL:

| glob set | matched | hits | recall |
|---|---:|---:|---:|
| original | 8 | 0 | 0% |
| + filename signals (`*shader*`, `*glsl*`, `*webgl*`) | 8 | 0 | 0% |
| + technique names (`parallax*`, `ldi*`) — shipped | 10 | 2 | **100%** |

**Know what is load-bearing here: `parallax*` and `ldi*` carry the entire
recall.** Drop them and it returns to 0%. Filename signals that sound right
(`*shader*`, `*glsl*`, `*webgl*`) contribute nothing on this corpus and are
kept only because they cost nothing — 8 of the 10 matches are `.fs` Tcl font
files in a vendored Python toolchain that is never read, so precision on files
actually opened is 2/2.

That is the honest shape of the fix: a glob cannot see inside a template
string, so this one works by naming the two files already known to contain
GLSL. **It will miss the next project that embeds GLSL under a name nobody
predicted, in exactly the same silent way, and the symptom will again be that
this rule never fires.** If you are writing GLSL in a file that did not load
this rule, add its pattern above — and if that happens twice, the conclusion is
that path globs are the wrong carrier for content-embedded shader code, not
that the list needs a third patch.
