# Modes — one card per measured capability

Each card: when it applies → the pattern that closed the loop on the rig → the gates and controls that
proved it → cost → the evidence round (`<round>/` under the rig root — a private tree on a non-system drive at the
source; README zh-TW + script + logs).
Numbers are the rig's measurements (2026-09-13/14, COMSOL 6.2, MPh 1.4.0, `cores=8`, 31 GB RAM); they are
budgets, not device claims. Rules named `R-…` are in `api-rules.md`.

Capability level vocabulary (09 §1): **L3** closed loop with controls (a card below); **L2** module + seed
present, no closed loop; **L1** needs extra machinery; **L0** not in COMSOL 6.2.

## Choosing a mode

| The brief asks for … | Mode | Evidence |
|---|---|---|
| n_eff, mode field, MFD, overlap/misalignment of a waveguide or fibre cross-section | 1 截面模場 | 10 |
| field in a 2D semiconductor device (trench corner, junction, gate) under bias | 2 2D 元件場 | 07, 11 |
| I-V of a field-effect transistor (MESFET; HEMT = same route once a 2DEG seed exists) | 7 電晶體 I-V | 14 |
| Gummel plot, β, output family of a BJT (HBT = same route + heterojunction emitter, untested) | 7 電晶體 I-V | 15 |
| small-signal C(V) of a junction / MOS capacitor | 5 小訊號 | 13 (U6) |
| transmission-line cross-section Z₀, ε_eff (CPW, microstrip) | 4 RF 截面 | 13 (U5) |
| ring-resonator spectrum, FSR, Q, coupling; any "load a library model and sweep it" | 6 程式庫模型驅動 | 12 |
| Gaussian beam through free space / glass, waist evolution, CPO FAU↔OE air-gap segment | 3 傳播 (ewbe) | 17 |
| 2D-material / TI surface sheet (Kubo/Drude σ), SPP dispersion, THz absorber | 8 表面片 | 16 |
| best value of one geometric parameter for a scalar target | 9 最佳化 | 18 |
| tolerance / distribution of an output under input scatter | 10 UQ | 18 |
| 3D taper / spot-size converter transmission, or "how long a 3D structure can we afford" | 11 3D 傳播 | 19 |
| a FIGURE for a report/paper: field map, I-V plot, geometry/mesh picture, per-solution frame | 12 出圖 | 21 |
| a semiconductor device coupled to a circuit in the time domain (rectifier, driver, device vs lumped model) | 13 半導體＋電路時域 | 21 |
| a 3D library seed (coupler / scatterer / 3D device): run it, gate it against a closed form, export 3D figures | 14 3D 程式庫種子 | 22 |
| a thermal PROCESS step: dopant diffusion / anneal profile, thermal oxidation thickness, RTP wafer temperature history, post-deposition film stress or wafer bow | 15 熱製程 | 24 |
| full-wave field of a rotationally-symmetric free-space/glass beam path (fold mirrors, lens stack, circular polarization), when a 2D/3D vector solve is needed for credibility | 16 軸對稱全波 (ewfd m=1) | SSLD T14 |
| packaging thermal (3D heat sink, moisture, heater cross-talk, thermo-optic) | — deferred by user ruling 2026-09-14 (U8, U10–U12) | 09 §4 |

Never route by module name; route by the observable the brief names.

## Card 1 — 截面模場 (2D ewfd Mode Analysis)
- **Pattern**: from text: 2D geometry (`lengthUnit("um")`), core `BoxSelection`, `RefractiveIndex` materials, `ewfd`
  with `wee1.DisplacementFieldModel = RefractiveIndex`, `ModeAnalysis` step (`modeFreq`, `neigsactive/neigs` as
  `jpype.JInt`, `shiftactive/shift = n_core` → highest n_eff first). Fields at points via `Interp` (R-INTERP-UNIT,
  R-INTERP-SHAPE); confinement via `Integration` couplings.
- **Gates**: MFD vs Marcuse/Petermann closed form (8.860 vs 8.900 µm), overlap η(d) vs Gaussian (max|Δ| 0.0035),
  guided-mode count; control: wrong-index ruler. Cost 15–32 s per case.
- **Evidence**: `10_U1_mode-field-MFD/u1_mode_field_mfd.py` PASS 8/8.

## Card 2 — 2D 元件場 (semi drift-diffusion, 2D)
- **Pattern**: from text: Boolean geometry with fillets, `GateContact` (`V0`, `epsilon_ins`, `d_ins`),
  `AnalyticDopingModel` (`impurityType`, `NDc/NAc`), `TrapAssistedRecombination` for τ (not on `smm1`),
  equilibrium step then a `Vd` sweep starting at 0 (R-SWEEP-START), boundary sampling line for |E| (R-MAXOP-BOUNDARY:
  a `maxop` maximum is a mesh quantity — read the field at a fixed offset instead), `semi.normE` not `-d(V,x)`.
- **Gates**: planar field vs depletion closed form (595.5 vs 626.8 kV/cm, −5 %), 1D cross-check, corner-concentration
  monotone in fillet radius (1.29 → 1.02), mesh 3.6 %. Known gap: a 200 nm radius did not converge on the final mesh.
- **Evidence**: `11_U3_trench-2D-E-field/u3_trench_efield.py` PASS 5/5; 1D heterojunction PD `07_S2_field-profile/` 6/6.

## Card 3 — 傳播 (Beam Envelopes, 2D from text / 3D seed)
- **Pattern**: `ewbe` out-of-plane, `UniDirectionality`, per-domain `k1 = ["k0*nloc","0","0"]` with a variable node per
  domain, `MatchedBoundaryCondition` Gaussian launch with the 3-vector `Eg0` (R-EWBE-2D-AMPLITUDE), mapped mesh,
  second-moment width from `Interp` cuts (or an `Integration` coupling variable, card 9).
- **Gates**: width vs q-parameter/ABCD law at the air end and glass exit (+0.3 / +0.2 %), seed w(z) law
  (+0.02…+0.06 %); controls: waist-at-input, glass→air (+19.8 % separation); mesh < 0.02 %. 6–12 s per case.
- **Evidence**: `17_U7_beam-envelopes-propagation/u7_beam_envelopes.py` PASS 6/6. Not built: folded mirrors, Fresnel
  reflection (unidirectional), Poynting-flux read-out (the n·Σ|E|² proxy ratio 0.796 is unexplained — use flux).

## Card 4 — RF 截面 (CPW Z₀ / ε_eff)
- **Pattern**: from text: `es` electrostatics C′ (with and without dielectric → Z₀, ε_eff), `emw` 2D Mode Analysis
  n_eff (R-MODES-RF: metal thick enough for the mesh), hole/difference selections (R-SEL-HOLE/DIFF). The library CPW
  seed is a download stub (R-LIB-PREVIEW: files < 200 kB are previews).
- **Gates**: Z₀ +1.1/−0.5 %, ε_eff +0.1/−0.8 % vs Gupta; mode vs es +0.11 %; air control; mesh 0.00 %.
  **3D S-parameters untested (L2).**
- **Evidence**: `13_U5-U6_RF-CPW-and-CV/u5_cpw_impedance.py` PASS 7/7.

## Card 5 — 小訊號 (C(V), Frequencylinearized)
- **Pattern**: library small-signal seed; read the perturbation solution with `differential=True` and a second
  parameter read (R-PERTURB-READ).
- **Gates**: accumulation vs C_ox (330 vs 345 pF), HF minimum vs closed form (83.7 vs 88.0), LF inversion recovery,
  LF/HF ratio. 3–5 s per point.
- **Evidence**: `13_U5-U6_RF-CPW-and-CV/u6_moscap_cv.py` PASS 4/4.

## Card 6 — 程式庫模型驅動 (load `.mph`, change parameters, sweep, read per solution)
- **Pattern**: `client.load(seed)`; parameters via `param().set`; batch/parametric sweeps via `plistarr`; per-solution
  global reads (R-BATCH-SOLS); convert any seed to a text template with `model.java.save(path, "java")` (R-SAVE-JAVA)
  and read it before editing.
- **Gates**: MRR FSR 26.097 vs λ²/(n_g L) 26.092 nm, mode order, Q, mesh shift 0.03 % FSR; decoupled-bus control
  T > 0.985. 161 points in 4.3 min.
- **Evidence**: `12_U22_MRR-spectrum/u22_mrr_spectrum.py` PASS 6/6.

## Card 7 — 電晶體 I-V (2D semi, seed-driven)
- **Pattern**: MESFET seed (`mesfet.mph`) or BJT seed (`bipolar_transistor.mph`): change L/W/N_d, rebuild geom+mesh,
  `(Vg, Vd)` stationary sweep from the equilibrium point (R-SWEEP-START: stop ~0.2 V short of V_T; use `semi.T0`,
  `semi.Nc`, `semi.N`), chained studies via `useinitsol` and voltage↔current terminal swap via `disabledphysics`
  (R-STUDY-CHAIN), mesh gate in the bias regime of the physics gate (R-GATE-REGIME).
- **Gates**: TLM dR/dL vs Shockley (−0.0/−0.7 %), V_p 1.764 vs 1.753 V, N_d×2 control −0.4 %, V_bi; Gummel n_C 1.014
  / n_B 1.007, β_peak 159, output family vs Gummel +0.2/+2.4 %, N_B×2 control 0.510. 8–21 s per curve/study.
  **Not built (L2): heterojunction 2DEG HEMT, heterojunction-emitter HBT** — same route, needs a heterostructure seed.
- **Evidence**: `14_U19_MESFET-IV/u19_mesfet_iv.py` 8/8; `15_U20_HBT-Gummel/u20_bjt_gummel.py` 6/6.

## Card 8 — 表面片 (TI / 2D material sheet + SPP)
- **Pattern**: graphene absorber seed (3D ewfd periodic unit cell, `Transition BC` with Kubo/Drude σ(ω)), E_f sweep by
  `plistarr` + batch; SPP seed: BMA complex n_eff (`real/imag(ewfd.beta_1)/ewfd.k0`). A TI surface state enters
  Maxwell the same way (a sheet conductivity) — anisotropic / magneto-optic tensors not built.
- **Gates**: σ_intra read-back 0.000 %, A_max 0.9992 with A+R=1, E_f=0 control 0.184, SPP n_eff vs √(ε_m/(ε_m+1))
  −0.01 % real, wrong-ε_d ruler control 32–41 %; mesh (physics-controlled → user-controlled) +0.01 %.
- **Evidence**: `16_U21_surface-sheet-and-SPP/u21_sheet_spp.py` PASS 6/6.

## Card 9 — 最佳化 (one parameter, scalar target)
- **Pattern A (Python)**: `scipy.optimize.brentq` around a one-solve function (build or `param().set` + `study.run()`).
- **Pattern B (native)**: `Optimization` study step, `optsolver bobyqa`, objective written with the component prefix
  (`comp1.wq`, R-OPT-SCOPE), `pname/initval/scale/lbound/ubound` via `setIndex`; the optimum is in the result table
  whose header contains `Objective` — the global parameter is NOT updated.
- **Gates**: both routes L_g* 171.97 vs q-law 173.06 µm (−0.63 %, 0.00 % apart); unreachable-target control hits the
  bound. Native 11 evaluations / 62 s, Python 5 solves / 27 s on a 6-s model.
- **Evidence**: `18_U13-U14_UQ-and-optimisation/u13_u14_uq_opt.py` PASS 8/8. Not built: shape optimisation, multi-
  variable, gradient solvers.

## Card 10 — UQ / 容差
- **Pattern A (Python MC)**: draw inputs, re-solve per sample, compare mean to the analytic mean AT THE SAME SAMPLES
  (not the nominal — a 32-sample draw is biased), std to the linearised RSS, sensitivities by regression; control =
  the complementary single-input draw (the one that carries most of the RSS is not a control).
- **Pattern B (native)**: `UncertaintyQuantification` step, `uqtype uncertaintypropagation`, `uqmethod sbmontecarlo`
  (only value), per-input columns ONLY as `q.set(prop, [["col1", value]])` in SI without units (R-UQ-KEYVALUE),
  `qoiexpression comp1.<var>`; read the statistics table by its header (`Mean, STD, …`), never by table tag.
- **Gates**: MC mean +0.15 %, std +5.0 % vs RSS (N 32, 170 s); native mean +0.19 %, std −0.8 % (110 s); n_g-only
  control −86 %.
- **Evidence**: same round as card 9. Not built: multi-input native UQ (`[["col1",v1],["col2",v2]]` untested),
  screening / reliability types.

## Card 11 — 3D 傳播 / taper 可行性 (ewfd numeric ports; ewbe 3D)
- **Pattern**: from text: `Block` cladding + `WorkPlane(zx)`/`Polygon`/`Extrude` taper, numeric ports with one
  `BoundaryModeAnalysis` step per port before `Frequency` (R-3D-PORTS), scattering walls on a `UnionSelection`,
  swept prism mesh (R-SWEEP-MESH) so DOF is linear in length; DOF from `sol.getSize()`, memory by sampling the
  server RSS during the solve (R-DOF-MEM). ewbe 3D with the phase interpolated between the port propagation constants
  (R-EWBE-3D-PHASE) is the long-taper route — cheaper ONLY on a coarse z mesh.
- **Gates (run4, 2026-09-14)**: T(6 µm) 0.99850 → T(10 µm) 0.99935 monotone; reciprocity 0.000 %; energy R+T ≤ 1;
  sweep vs free-tet +0.004 %; mesh +0.000 %; 2D vs 3D port n_eff ±0.07 %; ewbe vs ewfd −0.07 % at 4.6× fewer DOF and
  13× less time. Control: an ABRUPT step (2 µm wide + 6 µm narrow) T 0.9297 — −7.0 % vs the 10 µm taper and 99× its
  radiated loss; the 0.5 µm taper (14° half-angle, T 0.9207) is no better than the step. PASS 8/8 after 4 runs +
  2 probes. Cost: ewfd direct solver
  160 k DOF/µm, 0.6–0.7 GB/µm; 6 µm = 0.99 M DOF, 165 s, +5.6 GB; 10 µm = 1.63 M DOF, ~870 s, +8 GB — time is
  superlinear, so ≈10–15 µm is the practical 3D full-wave length on a 31 GB / 8-core machine; ewbe 3D is
  memory-bound (20 µm: 0.67 M DOF but +20 GB). Iterative solvers untested.
- **Control lesson (R-CONTROL-OWNED)**: the step control took four runs + one isolation probe. Gate it on the loss
  ratio (≥10× the longest taper) and on T being ≥5 % below the adiabatic taper — quantities the model produces.
  The scalar-E overlap × Fresnel formula underestimates a Δn_eff 0.76 butt joint by 21 % (the H-weighted vector overlap
  matches to 0.4 %); report such formulas, never gate on them. Ports within 2 µm of a discontinuity cost ≤1.5 %.
- **Evidence**: `19_U15_3D-taper-feasibility/u15_taper3d.py` (run4 verdict in its README; `probe/u15_probe2.py`).

## Card 12 — 出圖 (figures: native `Image` export + Data→matplotlib)
- **Pattern**: two routes, both closed on the rig. NATIVE: `result().export().create(tag, "Image")` pointed at a
  plot group (or `sourcetype="geometry"|"mesh"` + `sourceobject`), pixel size via `size="manualprint"`, `unit="mm"`,
  `width`/`height` strings, `resolution` dpi; decorations `options2d=True` FIRST then `axes2d/legend2d/title2d`;
  per-solution frame via the plot group's `looplevel` (one index per parameter level — R-IMAGE-EXPORT). The PNG is
  what the GUI's Plot window shows: COMSOL colours, auto title (`Vg=4 V, Vd=5 V`, `Time=2.4E-5 s`), colour bar,
  geometry outline. REDRAW: `Interp`/`EvalGlobal` read-back (R-INTERP-SHAPE, R-INTERP-SHAPE-MULTI) → matplotlib —
  for analytic overlays (V_T extrapolation line), multi-panel comparisons, signed symlog doping (`semi.Nd-semi.Na`,
  R-NNETDOP-SIGN), device-vs-lumped overlays. Address nodes as `m.result(tag)` / `m.result().export(tag)`
  (R-RESULT-ACCESS).
- **Gates (run3, 2026-09-15)**: every PNG decodes and is non-blank (pixel std > 5) — 26/26 native, 9/9 redrawn;
  manifest = files; AND a recorded model read of each raster (figure-self-read): the read caught a moiré field map
  with a 1e25 V colour bar that the blank-check passed (multi-expression Interp reshape). Native 1260×787 at
  160×100 mm / 200 dpi; 26 images in 20 s, 9 redraws in 4 s.
- **Cannot produce**: GUI-tree / Settings-window screenshots (≈ half of a COMSOL tutorial's pages), annotated
  geometry (contact arrows) — state it, do not fake it. Untested: 3D images, `Animation` export, Report generator.
- **Route order — NATIVE FIRST, always (user ruling 2026-09-19, SSLD T14; global rule `rules/native-render-first.md`)**:
  every figure of a COMSOL result is FIRST emitted through the native `Image` export of a plot group on the SAME
  expression the gate read. The native PNG is kept even when judged weak (full-domain window, SI labels, no CJK,
  COMSOL logo, no per-panel normalisation) — the weakness is written down, the file is not dropped. A redraw is
  ADDITIONAL, never a replacement, and is made only for a named need (analytic overlay, multi-panel shared layout or
  normalisation, CJK annotation, signed symlog). Both are presented side by side with a record of which is which and
  why the redraw exists. Instance that paid for this: SSLD T14 shipped the fold2d and axisymmetric field maps as
  Matplotlib redraws only ("沒試原生"); the 09-18 native fix covered the axisymmetric stations and missed fold2d
  (`native_plots_fold2d_T14.py`, 2026-09-19). Loading a saved `.mph` only to add Results nodes needs no re-solve.
- **Delivery shape**: ≥ 2 figures → one offline single-file HTML viewer (data-URI PNGs, list, ←/→, hash, zoom/drag,
  reading note beside each) built by a per-round `build_viewer.py`; page declares `data-page-class` and passes
  `fill_gate.py`. The tutorial PDF's result pages map 1:1 to native images; paper/deck figures carry the native image
  plus, when a named need exists, the redraw beside it (route order above).
- **Evidence**: `21_tutorial-figures/u21_tutorial_figures.py`, `probe/p1–p2d`, `pages/figures_21.html`, README §2.

## Card 13 — 半導體＋電路時域 (2D semi device coupled to `cir`, transient)
- **Pattern**: library seed `pn_diode_circuit.mph` (half-wave rectifier: 2D P–N diode as a circuit element next to a
  lumped-diode copy). Shipped transient does NOT converge headlessly (Newton fails at t ≈ 17 µs under both
  `study.run()` and `sol.runAll()`); the single change that converges is `fc1.set("maxiter", jpype.JInt(25))`
  (R-NEWTON-MAXITER). Probe voltages via `EvalGlobal` over all time steps (`cir.R1_v`, `cir.IvsU1_v`, …); field
  frames at the source peaks via `looplevel` (Card 12).
- **Gates (run3)**: device vs lumped load voltage max |ΔV| 2.2 % of Vac; rectification V_load min −7e-6 V for t > 0;
  forward drop 0.866 V; field contact-voltage CHANGE vs circuit diode voltage +0.867 vs +0.867 V. Control: lumped
  diode reversed → load polarity flips (max +0.000, min −4.234 V). 41 347 DOF, 50 BDF steps, 212 s; lumped 2 s.
- **Two rulers that bit (gates were redefined after R-ISOLATE, README §3)**: the seed starts from a zero initial guess,
  so t = 0 carries an unphysical ±0.54 V sample — gate on t > 0 and REPORT it (R-T0-ARTEFACT; the tutorial's
  stationary-initial-step cure is untested); `V` at a Metal Contact includes each contact's equilibrium offset, so
  anode−cathode `V` reads the built-in potential (0.88 V) — compare changes relative to a zero-bias sample or read
  terminal variables (R-CONTACT-POTENTIAL).
- **Evidence**: `21_tutorial-figures/` (same script; `probe/p3`, `p3b`), README §1 PN table.

## Card 14 — 3D 程式庫種子 (3D library seeds: wave optics, scattering, 3D semiconductor)
- **Pattern**: the Application Library holds 58 3D seeds in Wave Optics / Semiconductor / RF / AC-DC, each with an
  official PDF under the COMSOL 6.2 install root at `Multiphysics\doc\help\wtpwebapps\ROOT\doc\com.comsol.help.models.<key>.<name>\`
  (owner-locked: read with pypdf `decrypt("")`). The PDFs give the model recipe and QUALITATIVE figures, never a number
  to gate on — gates still come from closed forms or conservation. Three seeds closed on the rig: `directional_coupler`
  (3D ewbe, four numeric ports; power transfer along x read by `Interp` at (x, ±d, 0) on the study-1 dataset, R-PORT-
  BETA-DATASET), `scattering_nanosphere` (3D ewfd + PML, quarter model; σ_abs from the seed's `int_L(ewfd.Qrh)`, σ_sca
  from a shell integration created via `cpl().create(tag, "Integration", "geom1")` over a ball-difference selection,
  R-CPL-CREATE-GEOM; the wavelength sweep is a batch → one solution object per λ, read per swept `sol`, R-BATCH-SOLS),
  `bipolar_transistor_3d` (3D semi quarter NPN; terminal currents `semi.I0_n` on the V_B-sweep dataset).
- **Gates (run3, 2026-09-15)**: coupler half-beat λ/(2Δn) 2.302 mm vs seed length 2.1 mm (+9.6 %), transfer law
  sin²(πx/L_beat) max|ΔF| 0.012 over 21 stations, F(exit) 0.981, longitudinal mesh 20→40 ΔF 0.000, bidirectional
  formulation 0.982; control length 2.1→0.7 mm fires and lands on the analytic sin² (probe p3: 0.218 vs 0.211).
  Sphere: σ_abs vs Mie (ruler cross-checked against miepython) −0.0 % at 400 nm, σ_sca within 15 % (−12.7 % at
  400 nm on the seed mesh); control lossless n 1.5 must zero σ_abs. BJT: terminal-current conservation 2.1e-4 of
  full scale, collector ideality 1.052, β plateau 135 vs the 2D seed round's 159; control N_B×2 on I_C(0.6 V) as in
  Card 7: I_C(0.6 V) ratio 0.534 (2D: 0.510); β does NOT move (+2.4 %) because N_B also enters this seed's emitter doping — REPORTed.
- **Cost (8 cores)**: coupler 1.16 M DOF 34 s (2.2 M DOF 58 s at 40 elements); sphere 46 k DOF 3 s per wavelength
  (66 k at a λ air shell); BJT 90 k tets / 94 k DOF, V_C sweep 140 s + 45-point V_B sweep 200 s — a 3D drift-
  diffusion round is ≈ 12 min per configuration, so its control is budget-gated (skip above 900 s).
- **3D figures**: same `Image` export recipe as Card 12 with `options3d/legend3d/title3d` (`axes3d`, `grid3d`,
  `axisorientation3d` do not exist — R-IMAGE-EXPORT-3D); the PNG uses the seed's view (camera, aspect scaling), so
  a 2.1 mm coupler renders as a cube and the nanosphere as a close-up — for a to-scale picture use the redraw route.
  Per-wavelength frames: point the plot group at the per-solution dataset, not `looplevel` on the sweep dataset.
- **Rulers that bit (README §3)**: a seed parameter used as a control without reading its geometry sequence (d 3→6 µm
  moved Δn by 3 %, R-SEED-PARAM-SEMANTICS); a control that does not converge (dn ×4); the 1e-13 A terminal-current
  floor (R-NOISE-FLOOR-RATIO); a Mie reference value remembered wrongly (R-MIE-RULER); plot groups of an un-run study
  export an empty frame that passes the blank check.
- **Evidence**: `22_3D-seed-figures/u22_3d_seed_figures.py`, `probe/p0–p3c`, `mie_ruler.py`, `pages/figures_22.html`, README.

## Card 15 — 熱製程 (thermal process physics: diffusion, oxidation, RTP, film stress)
COMSOL has no process simulator; the card tests the PHYSICS under each thermal step against its closed form. Four
patterns closed on the rig (`24_U24-U27_thermal-process/`, 2026-09-15), all from text unless noted:
- **Dopant diffusion (U24)**: 1D `tds`, `D = D0*exp(-Ea/(k_B*T))` as a parameter, predep = `Concentration` Dirichlet
  (`species`/`c0` by index), drive-in = second Time Dependent study with `useinitsol` from std1 AND
  `disabledphysics=["tds/conc1"]` + `useadvanceddisable=True` (R-DISABLEDPHYSICS-ADVANCED — without the flag the
  Dirichlet silently stays on, dose ratio 8.55). Gates: erfc profile / dose (0.06 % / 0.01 %), exact mirror-convolution
  drive-in (x_j −0.017 %), dose conservation 1.0000, Arrhenius ratio via a Dt least-squares fit (−0.10 %; a `ln C` vs
  `x²` slope is a biased ruler, R-GAUSSIAN-SLOPE-RULER-BIAS); controls: erfc ruler on the drive-in (92 %), Ea doubled;
  mesh×2 + rtol×0.1 needs `t1.consistent="off"` on a re-solve (R-TRANSIENT-RESOLVE-STALE-INIT). 2–5 s per study.
- **Thermal oxidation, Deal–Grove with a moving interface (U25)**: 1D oxide domain, `tds` with Dirichlet C* at the gas
  side and `FluxBoundary` `J0 = -k_s*c` at the Si side; the interface moves with the Definitions-level Deformed Geometry
  (`common().create(...,"DeformingDomainDeformedGeometry")`, `"FixedBoundaryDeformedGeometry"`,
  `"PrescribedNormalMeshVelocityDeformedGeometry"` with `prescribedNormalVelocity = k_s*c/N1`; fetch with `.get(tag)`,
  R-DG-COMMON-ROUTE / R-COMMON-ACCESSOR). The legacy `physics().create("dg","DeformedGeometry")` solves without error and
  never moves (R-DG-LEGACY-NOOP). Gates: x(t) vs x²+Ax=B(t+τ) 0.026 %, C_i/C* 0.000 %, window slope 0.011 % (against the
  same-window fit of the closed form, R-INSTANT-SLOPE-WINDOW); controls: k_s×100 → parabolic 0.54 %, nominal k_s must
  miss the parabolic ruler (−15.8 %). 3 s per solve.
- **RTP wafer heating (U26)**: 2D-axi `ht` (`solid1` properties set directly, R-HT-DEFAULTS), `HeatFluxBoundary` lamp
  flux, `SurfaceToAmbientRadiation` with its OWN `Tamb`; gates against the lumped ODE ρc_p d dT/dt = q − 2εσ(T⁴−T_a⁴)
  (≤ 0.18 % over 0.5–10 s), T_ss = (T_a⁴ + q/(2εσ))^¼ (+0.02 %, property-independent), initial ramp q/(ρc_p d) (+0.6 %),
  through-thickness (q/2)d/k (+0.2 %); control ε 0.7→0.35 lands on T_ss·2^¼ (+0.08 %). Seed route: `laser_heating_wafer.mph`
  (3D, moving+rotating spot) driven headlessly — source-conservation gate +0.1 %, power×2 control +0.3 %; the energy-balance
  gate over the seed's 61 stored times is quadrature-limited (see the round README §C-S2). 5–26 s (2D), ~60 s (3D seed).
- **Post-deposition film stress / wafer bow, Stoney (U27)**: 2D-axi `solid`, one `lemm1`+`te1` pair reading E/ν/α per
  material node (`layered_plate.mph` pattern, R-MULTI-MATERIAL-ELASTIC), `Tref = T_dep`, point `Displacement0`
  `["0","1","0"]` (R-SOLID-DEFAULTS), mapped mesh with `selection().geom("geom1",JInt(2))` (R-MESH-SEL-DIM), solver
  hardened to `pardiso` for the 250:1 aspect (R-SOLID-ASPECT-SOLVER). Gates: κ from a quadratic fit of w(r), r ≤ 0.7R
  (+0.70 % vs 6σ_f t_f(1−ν_s)/(E_s t_s²)), σ_φφ at film mid-thickness (+1.2 %, sign derived, R-CURVATURE-SIGN), t_f/2 → κ/2
  (+0.35 %); controls: α_f = α_s → κ = 0, uniaxial ruler misses by 34 %. 3–27 s.
- **Rulers that bit**: every gate in this card is self-consistency (inputs `[E]` textbook-order → `design-study`); bare
  relabelled units make native figure labels false (R-UNIT-RELABEL); a plot must use the gate's expression, not a draft's
  (R-FIG-FROM-GATE-VARS). Two gates failed on the ruler alone — self-test every ruler on the closed form's own samples
  first (R-RULER-SELF-TEST); the moving-boundary seed named in the card carried no moving boundary — grep the seed text
  for the feature type before issuing a card (R-SEED-CARRIES-MECHANISM); a native 1D figure under Deformed Geometry
  plots on the mesh frame (R-DG-NATIVE-1D-FRAME, fix unverified — use the matplotlib redraw for the audience).
- **Evidence**: `24_U24-U27_thermal-process/u24_dopant_diffusion.py` PASS 9/9, `u25_deal_grove.py` PASS 6/6,
  `u26_rtp_wafer.py`, `u27_film_stress_stoney.py` PASS 6/6, `probe/`, `seed/*.java`, `pages/figures_24.html`, README.
- **Not built**: 2D/3D oxidation (bird's beak), implantation profiles (no process simulator), temperature-dependent
  library materials inserted headlessly (unverified route), packaging thermal U8/U10–U12 (deferred), self-heating of a
  device under bias.

## Card 16 — 軸對稱全波 (2D-axisymmetric ewfd, m=1 circular polarization)
- **Pattern**: for a rotationally-symmetric free-space/glass beam path (fold mirrors, lens stack — a system with circular
  mode field, spherical lenses, circular apertures) where a full 3D vector solve is unaffordable (~1e9 elements) but a
  credible (non-self-written) full-wave field is required: 2D-axisymmetric `ewfd`, mode `m=1`, launch a circularly-
  polarized field `(Er, Ephi) = (G, -i*G)` (NOT `m=0`; a linearly-polarized Gaussian is not an m=0 field, but circular
  polarization is pure m=1 and matches `|E|` to a linear one at the near-axis order). Scattering BC at every open
  boundary is enough when wall power is negligible (measured 2.7e-6) and exit angle is small — skip axisymmetric PML
  setup risk. Split a long path into segments joined by the same closed-form Gaussian at the boundary when the whole
  domain will not fit in memory (31 GB machine: ~0.9 mm was already the split point). **Element order/mesh: CUBIC
  elements at lambda/3, not quadratic** — see the dispersion pitfall below (R-AXI-M1-CUBIC). The azimuthal helicity
  sign (`Ephi = +-i*Er`) is a genuine COMSOL-convention ambiguity: run BOTH signs once; the wrong one produces an
  on-axis field singularity (regularity 1.7, overlap 0.04) and is immediately obvious.
- **Pitfall (R-AXI-M1-CURL-LAGRANGE-DISPERSION, ops/lessons/L-115.md)**: at quadratic element order, the in-plane field
  components (curl/Nedelec-type shape functions) and the out-of-plane component (Lagrange shape functions) have
  DIFFERENT numerical dispersion at the same mesh density. A circularly-polarized field dephases along the path and
  the accumulated error shows up as a spurious reverse-helicity ring — NOT as a uniform blur. Measured (200 um short-
  domain single-variable isolation): quadratic lambda/4 overlap ratio 0.933 -> lambda/6 0.995 -> lambda/8 0.999
  (monotonic, never reaches 1); cubic lambda/4 is already 1.0000. Fix: cubic elements, lambda/3 mesh.
- **Control lesson (R-AXI-M1-PROBE-LENGTH, ops/lessons/L-116.md)**: because the dispersion error is CUMULATIVE with
  propagation distance, a short probe (40 um) of the identical recipe PASSED while the full-length run (0.9 mm+)
  FAILED (facet w 32 vs 25, overlap 0.66, eta 0.50). A short probe only proves the model builds and solves; put the
  positive control that is meant to catch a cumulative numerical error in the FULL-LENGTH model, or size the probe so
  the error has room to exceed the gate's tolerance before trusting a PASS.
- **Gates**: ruler self-check, positive control (uniform-glass segment vs. closed-form Gaussian), on-axis regularity,
  side-wall power, cross-validation against a scalar 3D model (±0.02), negative control (removing a lens must collapse
  the result).
- **Evidence**: SSLD T14 (not a COMSOL_Test round — a consuming project), `tools\comsol_axi_T14.py` in that project's T14 round folder (a private research tree on a non-system drive at the source);
  `out\comsol_axi\run1.log` (full-length failure), `run4_probe_cubic_div4.log`, `run5_cubic_div3.log` (cubic-element
  convergence); round record `T14_5d_過程紀錄_選法與撞牆統計_20260918.md` §2 (選法) and §3 (撞牆表 rows 1-2).

## What no card covers (state it, do not improvise)
Packaging thermal / moisture / thermo-optic (deferred; process thermal is Card 15), 3D RF S-parameters, heterostructure HEMT/HBT seeds, anisotropic
TI surface tensors, shape optimisation, multi-input native UQ, PML-backed ports, time-domain of anything other than
a semi+circuit seed (Card 13), ray optics, GUI-tree / Settings-window screenshots (Card 12 states the limit),
animations, 3D seeds outside the three closed ones (Card 14 gives the recipe; a new seed still needs its own gate
round), 3D models that exceed the memory budget (Card 11). A brief that needs one of these gets an L2/L1 statement
and a proposed probe, not a result.
