# Environment bridge — what this machine requires on top of the vendored material

The vendored packages were written for a generic Claude Code install. This file
maps them onto the standing rules in `~/.claude/CLAUDE.md`. **These are not
suggestions from the upstream authors — they are local obligations**, and they
outrank vendored advice on conflict.

## 1. Motion work is visual work — the visual gate applies

Global rule: *green tests or a correct backend response prove the data path, NOT
the picture.* Everything this skill covers renders something a human looks at.

- Never report an animation, shader, or 3D scene as "working" on the strength of
  a passing build, a clean console, or a correct data structure.
- A change is done when **the user has confirmed it in the real environment**.
- Because motion cannot be statically verified, every delivery here ends with a
  **manual-acceptance checklist** (`[BC]` rule): numbered steps, concrete action
  + expected observation per step, executable blind by a non-author, with **no
  fewer stress-path items than happy-path items**. For motion specifically the
  stress path means: rapid re-trigger / spam-clicking, interrupting an animation
  mid-flight, tab-switch and return (rAF throttling), window resize during
  animation, and `prefers-reduced-motion: reduce` enabled.

## 2. Failures must announce themselves

Global rule: a silent blank screen is a design defect. This bites hardest in 3D.

- **Every animation / particle / realtime-render deliverable ships a toggleable
  FPS + object-count readout.** Not optional, not "if there's time".
- WebGL context creation, asset loading (`GLTFLoader`, textures, HDR), and shader
  compilation must each have a visible failure path — an on-screen notice or a
  degraded fallback, plus a structured `console.error`. A black canvas that could
  mean "loading", "failed", or "camera pointing the wrong way" is a defect.
- State the likely failure modes in the delivery note, and what the user would
  actually see for each.

### GLSL ES — the known trap (global `CLAUDE.md`, verbatim obligation)

When writing shaders (see a Three.js reference for API specifics — this
package does not ship one, see `NOTICE.md`):

- **Unroll multi-texture sampling into named uniforms.** Variable-indexed sampler
  arrays and dynamic loop bounds **fail to compile as a silent blank** on GLSL ES.
- **Attach a shader-error callback** so a compile failure surfaces as a message
  rather than an empty canvas.

## 3. Tunables must be centralized, and degradation declared up front

Motion work is almost entirely aesthetic parameters — the exact case the global
`[BC]` rules target.

- Put every timing, easing, amplitude, stagger, colour, and camera constant in
  **one commented config block**, and append an **adjustment table** to the
  delivery: *desired change → parameter → sane range*. The duration / easing /
  personality tables in `SKILL.md` supply the sane ranges.
- If the deliverable may not fit the round's budget, **declare the degradation
  order before building**: drop X → Y → Z, guaranteed core W. For 3D that
  ordering is usually: post-processing → ambient/secondary layers → shadow
  quality → particle count → (guaranteed core) the primary interaction itself.

## 4. Interaction semantics are the user's call

Global rule: changes that alter click behaviour, camera/viewport, keyboard, or
defaults need the direction confirmed **before** implementing. In 3D this covers
more than it looks like — `OrbitControls` tuning, scroll hijacking, click-vs-drag
selection thresholds, and auto-rotate defaults are all interaction semantics.
Pure internal choices (which easing helper, how the render loop is structured)
are yours to make; just say what you picked.

## 5. Check the asset vault before hand-rolling

`asset-vault` Mode B self-triggers on generic capabilities, and animation assets
are its most likely stock: loaders/spinners, transitions, easing helpers, scene
boilerplate. If an `asset-vault`-equivalent skill is installed, check its
registry **before** writing a generic animated component from scratch (the
source environment's registry path is machine-specific and is not shipped —
see that skill's own docs for where yours lives). If it is absent, hand-roll
and consider Mode A extraction afterward.

## 6. Accessibility is already covered upstream — use it, don't re-derive

`vendor/lottiefiles/director/context-adaptation.md` has the reduced-motion
substitution table, vestibular triggers, and platform duration scaling. Apply it
rather than improvising; `prefers-reduced-motion` handling is a hard requirement
of any motion deliverable here, not a nice-to-have.

## 7. Trust boundary

This package ships no vendored Three.js text (see `NOTICE.md`). If you fetch a
Three.js reference yourself, read `currency.md` first — it documents the ~25-
release drift the source environment found in its own (now-excluded) copy, as
a template for checking whatever you fetch.
