---
name: comsol-agent-pipeline
description: Drive COMSOL 6.2 headlessly from Python (MPh) to a machine-checked, labelled result — build or load a model from a written brief, solve, read back, gate against an analytic control, verdict PASS/FAIL/UNDET. Use for 跑 COMSOL、COMSOL 建模求解、MPh、模場/MFD、2D 元件電場、電晶體 I-V、C(V)、CPW Z₀、MRR 光譜、光束傳播、表面電導片/SPP、參數最佳化、UQ/容差、3D taper 可行性、熱製程（摻雜擴散/退火分佈、熱氧化厚度、RTP 晶圓溫度、沉積後薄膜應力/翹曲、移動邊界） — "用 COMSOL 算 X 對不對" / "把這個 brief 跑成 COMSOL 結果". Not for research planning or which observable to measure (scientific-research-guide), literature values (literature-search-extract), or CAD/GDS geometry (model3d-pipeline).
---

# comsol-agent-pipeline

Executes a written brief as a COMSOL 6.2 study through Python `MPh` (in-process JVM; `model.java`
is the COMSOL Java API) and returns a verdict a machine checked. No GUI, no vision, one process.
Evidence for every claim here is a closed round in the rig `COMSOL_Test` (a private test-rig project on a
non-system drive at the source; rounds 06–24, 2026-09-13/15); the rig is a test area — its numbers are
budgets, never device statements.

## Non-negotiables (each is a measured failure, not a style choice)

1. **Route by observable, not by module** — pick the mode card in `references/modes.md` whose
   gate matches what the brief wants to know; a brief no card covers gets an L2/L1 statement and a
   probe proposal, never an improvised result.
2. **Every number is tagged** `[L]` seed / `[D]` derivation / `[E]` labelled guess / `[X?]` not stated
   by the source. Untagged = defect. Any `[X?]` caps the label at `design-study`; labels are
   `reproduces-paper` / `calibrated-to-paper` / `design-study`.
3. **A gate is a closed form + a tolerance + a control that must fire** (mechanism removed or wrong
   ruler). A control that does not separate → `UNDET`, never `PASS`. Mesh/consistency gates are
   evaluated in the regime of the physics gate (R-GATE-REGIME). Report-only lines are marked
   `REPORT` and are not counted.
4. **`mph.start(cores=8)`** — measured optimum on this machine (16 slower, 32 twice as slow); no GPU
   path exists in 6.2. `MPh>=1.4`, JPype; Python ints as `jpype.JInt` (R-JPYPE).
5. **Read `references/api-rules.md` before writing API calls** — 98 measured traps, 85 API + 13 process-layer (default tags
   taken, reserved names `h s w t`, Interp coordinates in geometry units and points×expressions
   shape, EvalGlobal expressions×solutions, figures via an `Image` export node with a pinned
   property order (`options2d` first, `manualprint` mm + dpi, `looplevel` per parameter level),
   `comp1.` prefix in Optimization/UQ objectives, key/value matrix UQ inputs, sweeps start at
   equilibrium, Newton `maxiter` on the shipped semi+circuit transient, an `ewbe` `k1 = k*n` whose
   `n` is a domain-scoped VARIABLE with non-overlapping selections, …). Data export / table.save
   stays the primary numeric route; a `Plot` text export is usable only after its file size is
   checked > 0 in the same run (R-EXPORT, R-EXPORT-PLOT-TEXT), is addressed by `plotgroup` + `plot`,
   and its first column is arc length in the PLOT AXIS unit — neither metres nor the geometry unit,
   so parse the header (R-EXPORT-PLOT-PROPS, R-EXPORT-PLOT-ABSCISSA-UNIT). A new
   trap found in a run is written back to the SOURCE (`pipeline-draft.md` §2 of the rig) with the
   run that measured it, then the source's `tools/sync_rules.py` regenerates the copy (the generator is not
   shipped in this share — it reads the rig's rule ledger by a fixed private path; the generated copy is).
6. **Seed before scratch**: the nearest library `.mph` (the `Multiphysics\applications\` library under the COMSOL 6.2 install root)
   is converted to text with `model.java.save(path, "java")` and read before editing; files < 200 kB are
   download stubs (R-LIB-PREVIEW). Build from text only when no seed carries the physics.
7. **Deposit shape**: a new round folder `<NN>_<what>/` with the script, `runN.log` per attempt,
   `out/` (result json, tables readable by `sap read`, `.mph`), and a zh-TW README with the
   gate table, controls, and an honest correction history (which runs failed and whether the cause
   was API-layer or physics-layer). **Verify it by instrument, not memory: `python tools/deposit_gate.py
   <folder>` before declaring the round closed** (R-DEPOSIT-MPH; it reads the emitted folder and names
   the missing property — a round that solves but saves no `.mph` is the miss it was built from).
   Never edit frozen briefs; never edit `~/.comsol/v62/comsol.prefs`.

## Procedure

0. **Ask the device catalog first — one command, before any design work.**
   `python 29_device-observable-catalog\ask.py <device|keyword>` (a path relative to the rig root, which is a
   private tree on a non-system drive at the source) returns, for
   that device class: the signature graph, every core/typical graph with its axes and its reading
   trap, the mode card that executes each observable block, the rig's MEASURED level, and the
   literature already collected (citation, DOI, access route). `--list` enumerates the 42 device
   rows, `--block M4` goes the other way. This exists so a round does not re-derive which graphs a
   device needs, and does not re-run a literature sweep that is already recorded.
   **The study then NAMES the device row it is executing (or states that no row fits) in its README
   gate table and its result json.** "No row fits" is a legal answer and is how the catalog learns
   it has a gap. The catalog is PRIOR ART: it has a collection cutoff, it covers how a device CLASS
   is characterised rather than the structure in front of you, and its levels describe this rig —
   so it cuts missed graphs and repeated mistakes, it does not replace reading for the actual brief.
1. Classify the brief: observable → mode card; list inputs with tags; write the gates + controls
   BEFORE the model (tolerances from the closed form's own accuracy, not from the first result).
   Run each ruler on the closed form's own samples first — it must return the input inside the
   tolerance (R-RULER-SELF-TEST; two round-24 gates failed on the ruler, not the physics). A seed
   named for the mechanism is grepped in its `.java` text for the feature type (R-SEED-CARRIES-MECHANISM).
2. Copy `references/script-skeleton.py`; implement `reference()` (pure Python), `build()`, gates.
   Keep the result-json keys the skeleton writes (R-RESULT-JSON-SCHEMA) — page builders read them.
3. Run `python <script>.py > run1.log 2>&1` in the background for anything over ~2 min (rig
   runs took 10–45 min; a foreground tool call times out at 10 min). Cap every background run at
   10× its measured solve time; past the cap kill Python AND `comsolmphserver.exe`, keep the log
   (R-PROBE-TIMEOUT). Two concurrent sessions are measured safe (R-CONCURRENT-SESSIONS).
4. A FAIL is isolated before it is reported (R-ISOLATE): one variable at a time, in the same
   script; a redefined gate is stated as such in the README (rig precedent: 18 §1, 19 C1) and its
   superseded ruler stays in the script as a `REPORT` line (R-REDEFINED-GATE-REPORT). A figure is
   drawn from the gate's own variables (R-FIG-FROM-GATE-VARS). Figures go NATIVE FIRST (Card 12 route
   order): the COMSOL `Image` export is always emitted and kept; a Matplotlib redraw is an addition for a
   named need, shown beside the native one, never instead of it.
5. Deposit (non-negotiable 7), log the verdict in the process ledger, update the rig's
   capability inventory (`09_capability-inventory/README.md` §2) if a level changed.

## Budgets measured (scale with DOF)

| Model | DOF | Time | Memory |
|---|---|---|---|
| 1D semi, 51-step sweep | small | 9–24 s | — |
| 2D ewfd 12 layers, 160 k elements | — | 11 s | — |
| 2D mode analysis / 2D semi device | — | 3–45 s | — |
| 3D ewfd taper, swept mesh | 165 k DOF/µm | 6 µm 165 s; 10 µm 906 s | ~1 GB/µm (direct) → ~13 µm at 80 % of 31 GB |
| 3D ewbe taper, coarse z | 36 k DOF/µm | 6 µm 13 s | small |
| 2D semi + circuit transient (seed), 50 BDF steps | 41 k | 212 s | small |
| 3D ewbe directional coupler, 2.1 mm, 20 longitudinal elements | 1.16 M | 35 s | small |
| 3D ewfd gold nanosphere + PML, per wavelength | 46 k | 3 s | small |
| 3D semi BJT (quarter), 90 k tets, V_C + V_B sweeps | 94 k | 143 s + 200 s | small |
| Native `Image` export, 1260×787 (2D) / 1260×866 (3D) | — | ~0.8 s per PNG | — |
| 1D tds diffusion / oxidation with a moving interface (Deformed Geometry), transient | < 1 k | 2–5 s per study | small |
| 2D-axi ht wafer transient (10 s, radiation) / 2D-axi solid film-on-substrate | 7 k / 3 k | 5–27 s | small |
| 3D ht seed `laser_heating_wafer`, 60 s transient | 4 k | ~60 s | small |

## Files

- `29_device-observable-catalog\` (under the rig root) — the DEVICE × OBSERVABLE catalog (step 0):
  8 device families / 42 devices × 12 measurement blocks / 64 graphs, each graph carrying its axes,
  its reading trap, its analytic control and its native `Image` export route; 42 verified
  references with DOI and access route. Query it with `ask.py`, never by reading `catalog.html`
  (that page is for a human). `blocks.json` maps every block to the mode card that executes it.
- `references/modes.md` — 15 mode cards (pattern, gates, cost, evidence round; 12 = figures, 13 = semi + circuit transient, 14 = 3D library seeds, 15 = thermal process: diffusion / oxidation with a moving interface / RTP / film stress) + the uncovered list.
- `references/api-rules.md` — GENERATED from the rig at the source by its `tools/sync_rules.py` (`--check` reports STALE there; the generator does not ship in this share, the generated copy does).
- `references/script-skeleton.py` — the round script shape (step/gate/report/verdict, read helpers).

Owner of the rules text: the rig's `06_feasibility-probe_agent-routes/pipeline-draft.md` §2.
Review-when: COMSOL upgraded past 6.2 (GPU, solver defaults, UQ property names) or MPh past 1.x.
