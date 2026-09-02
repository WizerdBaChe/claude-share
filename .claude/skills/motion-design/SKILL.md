---
name: motion-design
description: >-
  Hub for motion, animation, and 3D/WebGL work. Motion design methodology —
  timing, easing, choreography, Disney principles, motion personality — for
  CSS, Framer Motion, GSAP, Lottie, Spring, or any animation system. Trigger
  on UI animation, transitions, micro-interactions, loading/success/error
  states, page transitions, scroll effects, brand motion identity, particles,
  WebGL — 「這個按鈕的動效怎麼做（時長、緩動、編舞）」「定品牌動態識別」「轉場/微互動怎麼設計」「用 Three.js
  做 X」「寫 shader/GLSL 效果」. NOT design tokens across a
  product suite (→ design-system-suite) or storing a reusable component (→
  asset-vault). Disambiguation: ~/.claude/skill-trigger-dict.md.
---

# motion-design — the animation hub

Router skill. The material lives in reference files; this page holds only the
tables needed on almost every job, plus the routing table.

**Read `local/env-bridge.md` before delivering any motion work** — it carries
this machine's hard obligations (visual gate, FPS readout, self-announcing
failures, the GLSL ES blank-screen trap, centralized tunables). Those outrank
anything in `vendor/`.

`vendor/` is third-party MIT content, unmodified. See `NOTICE.md`.

> **This share does not include a Three.js reference package.** The source
> environment vendored one, but its upstream ships no `LICENSE` file and names
> no copyright holder — the MIT grant exists only as a README sentence — so it
> was excluded rather than redistributed. Every routing row below that points
> at `vendor/threejs/` is therefore a pointer to something you must supply:
> use the official Three.js documentation, and read `local/currency.md` first
> for how to check whatever you fetch.

---

## Routing table

| If the task is about… | Read |
|---|---|
| **Local obligations, every delivery** | `local/env-bridge.md` |
| Whether the vendored Three.js text is still accurate | `local/currency.md` |
| Adding a new motion skill/library to this hub | `local/extending.md` |
| Why an animation should exist at all; three pillars, motion layers | `vendor/lottiefiles/director/core-philosophy.md` |
| Full decision pipeline from brief → keyframes | `vendor/lottiefiles/director/decision-framework.md` |
| Anticipation, follow-through, squash/stretch, arcs (12 principles, UI-adapted) | `vendor/lottiefiles/director/disney-principles.md` |
| Brand motion identity; the 4 personality archetypes in depth | `vendor/lottiefiles/director/motion-personality.md` |
| "It should feel joyful / calm / urgent"; colour psychology | `vendor/lottiefiles/director/emotion-mapping.md` |
| Multi-element coordination, stagger, counter-motion, hero staging | `vendor/lottiefiles/director/choreography.md` |
| Micro-story framing: setup → action → resolution | `vendor/lottiefiles/director/narrative-structure.md` |
| Mobile/tablet/watch scaling, **reduced-motion & a11y**, perf budgets, dark mode | `vendor/lottiefiles/director/context-adaptation.md` |
| Duration and easing lookup tables (full) | `vendor/lottiefiles/reference/timing-easing-tables.md` |
| Which property to animate, and what each communicates | `vendor/lottiefiles/reference/property-selection.md` |
| "It looks wrong but I can't say why" — animation smells | `vendor/lottiefiles/reference/troubleshooting.md` |
| Evaluating a finished animation | `vendor/lottiefiles/reference/quality-checklist.md` |
| Entrance/exit recipes | `vendor/lottiefiles/patterns/entrance-exit.md` |
| Hover, press, loading, success, error states | `vendor/lottiefiles/patterns/state-feedback.md` |
| Looping, breathing, parallax, background life | `vendor/lottiefiles/patterns/ambient-continuous.md` |
| Stagger and multi-element recipes | `vendor/lottiefiles/patterns/multi-element.md` |
| **Three.js** — scene, camera, renderer, Object3D, transforms | `vendor/threejs/fundamentals.md` |
| Shapes, BufferGeometry, custom meshes, instancing | `vendor/threejs/geometry.md` |
| PBR/basic/phong materials, material properties | `vendor/threejs/materials.md` |
| Lights, shadows, IBL/environment lighting | `vendor/threejs/lighting.md` |
| Textures, UV, cubemaps, HDR, render targets | `vendor/threejs/textures.md` |
| AnimationMixer, clips, skeletal, morph targets, blending | `vendor/threejs/animation.md` |
| GLTF/GLB, Draco, async loading, progress, caching | `vendor/threejs/loaders.md` |
| GLSL, ShaderMaterial, uniforms, custom effects | `vendor/threejs/shaders.md` |
| EffectComposer, bloom, DOF, custom passes | `vendor/threejs/postprocessing.md` |
| Raycasting, OrbitControls, mouse/touch, object picking | `vendor/threejs/interaction.md` |

Three.js tasks still go through the design tables below — an API-correct scene
with linear easing and no secondary motion is still bad motion.

---

## The 8-step checklist (run before any animation)

1. **Emotional target?** — joy, calm, urgency, elegance
2. **Motion personality?** — Playful, Premium, Corporate, Energetic
3. **Primary property?** — position, scale, rotation, opacity
4. **Duration?** — table below
5. **Easing family?** — entrance = decelerate, exit = accelerate
6. **Hero element?** — stage it
7. **Secondary + ambient layers?** — flat motion means these are missing
8. **1/3 rules?** — motion distance, simultaneous elements

**Three motion layers**, always: **primary** (the action followed) + **secondary**
(shadows, icons shifting) + **ambient** (background life).

## Motion personality — pick ONE per project

| Archetype | Duration | Easing | Overshoot | Keywords |
|---|---|---|---|---|
| Playful | 150–300ms | ease-out-back | 10–20% | fun, whimsical, bouncy |
| Premium | 350–600ms | cubic-bezier(0.4,0,0.2,1) | 0% | elegant, minimal, luxury |
| Corporate | 200–400ms | cubic-bezier(0.2,0,0,1) | 0–3% | clean, professional, dashboard |
| Energetic | 100–250ms | ease-out-expo | 15–30% | dynamic, bold, exciting |

Default: **Corporate** for UI, **Playful** for illustrations.

## Duration

| Element | Duration |
|---|---|
| Tooltip / micro-feedback | 80–120ms |
| Button press / toggle | 120–180ms |
| Icon transition | 150–250ms |
| Card enter / exit | 200–350ms |
| Modal / dialog | 300–400ms |
| Page transition | 400–600ms |
| Dramatic reveal | 600–1200ms |

Distance scales it: 100px = base, 200px = 1.3×, 400px = 1.6×.
Entrances run 30–50% longer than exits.

## Easing

Entrance → ease-out. Exit → ease-in. On-screen → ease-in-out. Ambient loop →
sine ease-in-out.

| Standard | Bezier | For |
|---|---|---|
| Material Design 3 | (0.2, 0, 0, 1) | default on-screen |
| MD3 Emphasized | (0.05, 0.7, 0.1, 1) | entrances, attention |
| MD3 Accelerate | (0.3, 0, 1, 1) | exits, dismissals |
| Apple HIG | (0.25, 0.1, 0.25, 1) | standard iOS |
| Gentle float | (0.4, 0, 0.2, 1) | ambient |
| Bounce settle | (0.175, 0.885, 0.32, 1.275) | overshoot, playful |

## Choreography

- Lead with the hero; keep entry direction spatially consistent.
- **1/3 rule (distance)**: no motion crosses more than 1/3 of the screen without
  an intermediate keyframe.
- **1/3 rule (elements)**: with 3+ elements, at most 1/3 move at once.
- Stagger: micro cascade 20–40ms, standard 50–100ms, dramatic 100–200ms.
  **Total stagger stays under 500ms.**

## Never break

1. **Never linear for spatial movement** (linear is for spinners and progress bars only).
2. **Never opacity-only** for an important state change — pair it with position or scale.
3. **Never exceed 1/3 screen** without an intermediate keyframe.
4. **Always three layers** — primary + secondary + ambient.
5. **Always honour `prefers-reduced-motion`** — substitution table in
   `vendor/lottiefiles/director/context-adaptation.md`.

## Fast triage

| Symptom | Cause | Fix |
|---|---|---|
| Robotic | linear easing, no arcs | easing curves + arc paths |
| Too slow | duration wrong for element type | check the duration table |
| Cheap / flat | no secondary or ambient | add shadow motion + background life |
| Distracting | too many elements moving | apply the 1/3 rules, cut amplitude |
| No personality | generic easing everywhere | commit to one archetype |
| **Blank canvas (3D)** | shader compile / context / asset failure | `local/env-bridge.md` §2 |

---

## Extending

New animation library, 3D framework, or motion technique → it lands **inside this
hub**, not as a new top-level skill. Procedure, licensing requirements, and the
split criterion: `local/extending.md`.
