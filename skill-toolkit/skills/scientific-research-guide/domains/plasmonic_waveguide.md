# Domain Profile: Plasmonic Waveguide (Plasmonic Waveguide)

> Scope of applicability:
> Surface plasmon polariton (SPP) guided-wave structures at metal-dielectric interfaces; passive and quasi-passive plasmonic waveguides; dielectric-loaded, long-range, and hybrid plasmonic waveguide geometries; waveguide-level measurement, modeling, fitting, and interpretation.
> Scientific nature:
> Electromagnetics, wave physics, optical material response, nanoscale light-matter interaction.
> Engineering nature:
> Nanophotonics, integrated photonics, plasmonic device design, nanoscale metrology, numerical modeling.
>
> Profile metadata:
> - Profile ID: DP-PLWG-001
> - Profile version: 1.0-draft
> - Last updated: 2026-07-07
> - Author(s) / Maintainer(s): Generated working draft for SKILL knowledge-base authoring
>
> Primary source types:
> - Textbooks: Maier, *Plasmonics: Fundamentals and Applications* (2007)
> - Review articles: Messner et al., *Plasmonic, photonic, or hybrid? Reviewing waveguide geometries for electro-optic modulators* (2023); Holmgaard and Bozhevolnyi, *Dielectric-loaded plasmonic waveguide components: Going practical* (2013)
> - Methods / standards papers: Johnson and Christy, *Optical Constants of the Noble Metals* (1972); Berini et al., *Characterization of long-range surface-plasmon-polariton waveguides* (2005)
> - Other (e.g. datasheets, industry standards): Thin-film permittivity measurements and geometry-specific numerical benchmarking studies
>
> Notes for AI use:
> - Intended use: Foundational reference for reasoning about plasmonic waveguide physics, modeling, measurement, and interpretation before moving to active-device applications.
> - Validation status / usage note: Suitable as a baseline domain profile for passive and quasi-passive waveguide analysis; modulator-specific metrics such as extinction ratio and electro-optic bandwidth are intentionally out of scope.

---

## 1. Theoretical Framework Anchoring

### Core first principles

| Scale / problem type | Foundational theory | Core physical quantity |
|------------|---------|-----------|
| Metal optical response | Maxwell equations with complex constitutive relations | Complex permittivity \(\varepsilon(\omega)\), refractive index, loss tangent |
| Free-electron-dominated metal response | Drude or Drude-Lorentz description, with caution at optical frequencies | Plasma frequency, damping rate, interband contribution |
| Single metal-dielectric interface | Boundary-condition solution for surface plasmon polaritons | SPP wave vector, penetration depth, modal confinement |
| Guided plasmonic structure | Eigenmode theory in open, lossy waveguides | Effective index, complex propagation constant, mode area |
| Real fabricated waveguide | Perturbation from roughness, finite thickness, substrate asymmetry, and coupling structures | Propagation loss, coupling efficiency, fabrication tolerance |

### Core definitions and baseline equations

For a planar metal-dielectric interface, the SPP dispersion relation is commonly written as

$$
k_{SPP} = k_0 \sqrt{\frac{\varepsilon_m \varepsilon_d}{\varepsilon_m + \varepsilon_d}}
$$

where $k_0 = \omega/c$, $\varepsilon_m$ is the metal permittivity, and $\varepsilon_d$ is the dielectric permittivity.

The complex propagation constant is typically written as

$$
\beta = \beta' + i\beta''
$$

where $\beta'$ governs phase propagation and $\beta''$ governs attenuation. A common propagation-length definition is

$$
L_{prop} = \frac{1}{2\beta''}
$$

for power decay to $1/e$.

The existence of a bound SPP mode at a simple interface typically requires a metal with negative real permittivity and a magnitude relationship that allows an interface-bound TM-polarized solution.

### Inviolable physical constraints (the AI should warn the user here)

1. **Confinement-loss trade-off**: stronger subwavelength confinement generally increases overlap with lossy metal regions and therefore increases propagation loss.
2. **Momentum-matching constraint**: free-space illumination does not usually satisfy the in-plane momentum required for direct SPP excitation, so prisms, gratings, edges, or near-field couplers are required.
3. **Material-data validity constraint**: optical-frequency Au and Ag behavior cannot be treated reliably by a simplistic Drude-only fit for final results; interband transitions matter.
4. **Scale-validity constraint**: when feature sizes approach the deep-nanometer regime, nonlocal response, spill-out, and other beyond-local effects can invalidate purely local classical models.
5. **Geometry sensitivity constraint**: substrate asymmetry, thin-film morphology, and sidewall roughness can shift mode properties enough that ideal symmetric models become misleading.

> **Decision point (mandatory Tier 0 confirmation)**: when the user describes a plasmonic waveguide design problem,
> the AI must confirm:
> "Is your priority (A) longest propagation length, (B) strongest confinement, or (C) the best confinement-loss trade-off?"
> The three goals correspond to different geometries, materials, and validation strategies.

---

## 2. Measurement Tool Inventory

### Mode and field characterization

| Measurement target | Tool | Output information | Applicable conditions | Common misuse |
|---------|------|---------|---------|---------|
| Near-field intensity distribution | Near-field scanning optical microscopy (NSOM/SNOM) | Spatial field map, modal localization, decay profile | Subwavelength probe access and stable scanning | Treating probe-perturbed fields as the unperturbed native mode |
| Leakage radiation from supported plasmonic modes | Leakage radiation microscopy (LRM) | Real-space and Fourier-space information on propagation and directionality | Structures with leakage into substrate or collection path | Assuming every guided mode is observable by leakage radiation |
| Excitation condition at planar or thin-film interfaces | Attenuated total reflection (ATR) / prism coupling | Reflectivity dip versus angle or wavelength, resonance condition | Prism-coupled or Kretschmann-like structures | Interpreting dip position without accounting for metal thickness sensitivity |
| Mode profile and coupling behavior | Far-field imaging with designed out-couplers | Relative mode content and coupling trends | Structures with engineered scattering or grating outputs | Confusing out-coupler efficiency variation with intrinsic propagation change |

### Propagation and loss characterization

| Measurement target | Tool | Output information | Applicable conditions | Common misuse |
|---------|------|---------|---------|---------|
| Propagation length | Spatial decay measurement from near-field or distributed out-scattering | \(L_{prop}\), decay constant | Single dominant mode and known out-scattering behavior | Fitting geometric scattering loss and intrinsic propagation loss as one quantity |
| Waveguide attenuation | Cut-back method | Propagation loss per unit length after separating coupling loss | Multiple nominally identical lengths | Using a single device length and calling total insertion loss "waveguide loss" |
| Coupling efficiency | Input-output power measurement with known launch geometry | Launch efficiency into the guided plasmonic mode | Reproducible couplers and reference structures | Mixing coupling variation with intrinsic waveguide performance |
| Thin-film optical constants for model input | Ellipsometry | Complex permittivity or refractive index of deposited films | Separate calibration films or representative fabrication stacks | Extracting bulk constants from a patterned device structure |

### Geometry and fabrication characterization

| Measurement target | Tool | Output information | Applicable conditions | Common misuse |
|---------|------|---------|---------|---------|
| Lateral dimensions and pattern fidelity | SEM | Width, spacing, edge roughness trend | Conductive coating or charge management as needed | Treating SEM edge visibility as exact sidewall metrology |
| Surface height and roughness | AFM | Height profile, RMS roughness, local topography | Accessible top surfaces | Using AFM to infer buried interface quality directly |
| Cross-sectional stack and interface quality | TEM cross-section / FIB-assisted sectioning | Layer thickness, buried geometry, interface continuity | Destructive sample prep accepted | Ignoring FIB-induced damage or redeposition artifacts |

---

## 3. Standard Modeling Toolchain

```
Analytical / semi-analytical interface or simplified waveguide model
→ Output: dispersion, penetration depth, trend-level confinement-loss behavior
    ↓
Eigenmode FEM or frequency-domain mode solver
→ Input: geometry, experimentally grounded permittivity, substrate stack
→ Output: effective index, complex propagation constant, field profile, mode area
    ↓
FDTD or broadband full-wave simulation
→ Input: finite device geometry, couplers, discontinuities, material dispersion
→ Output: transmission trend, scattering, field evolution, coupling behavior
    ↓
RCWA (only for periodic gratings or periodic plasmonic structures)
→ Output: diffraction efficiencies, reflection / transmission spectra, phase response
```

### Toolchain interpretation rules

- Start with the simplest model that preserves the dominant physics.
- Use analytical or semi-analytical models for intuition and parameter scanning.
- Use eigenmode solvers when the main question concerns modal constants, confinement, and propagation loss.
- Use FDTD when discontinuities, couplers, finite sections, or broadband behavior dominate the question.
- Use RCWA only when periodicity is central; it is not a default waveguide solver.

### Material-model caution

The most important modeling input is usually the metal permittivity dataset. For Au and Ag in the optical regime, literature and experimental practice repeatedly show that realistic interband contributions are important and that Johnson and Christy data remain a standard anchor for noble-metal optical constants. Thin films and nanostructures may deviate from bulk-reference values due to morphology, grain structure, roughness, and surface scattering.

---

## 4. Domain-Specific Fitting Methods

### Propagation-length extraction from spatial decay

**Applicable conditions**: a single dominant guided mode is observed over a region where distributed scattering is either weak or independently characterized.

**Common error**: ⚠️ fitting the observed intensity decay without separating background light, local scattering hotspots, or multimode beating.

**Correct approach**: subtract background, inspect the data for multimode or oscillatory behavior, and fit only the spatial region where a physically meaningful exponential decay model is justified.

### Cut-back extraction of propagation loss

**Applicable conditions**: a family of nominally identical waveguides with different lengths is available.

**Common error**: ⚠️ reporting total input-output loss from a single device as intrinsic waveguide attenuation.

**Correct approach**: fit total loss versus length so that the slope estimates propagation loss and the intercept absorbs launch and collection loss.

### Permittivity fitting for simulation-ready material models

**Applicable conditions**: dispersion models are needed for frequency-domain or time-domain simulations.

**Common error**: ⚠️ using a Drude-only fit for Au or Ag over the visible or near-infrared range and then treating the result as quantitatively final.

**Correct approach**: fit or import a model that reproduces experimentally validated optical-constant data over the actual operating band, and note whether the target is bulk, thin-film, or nanostructure behavior.

### Effective mode-area evaluation

**Applicable conditions**: comparison of confinement across different waveguide geometries or materials.

**Common error**: ⚠️ comparing mode areas computed with inconsistent definitions, normalization choices, or energy-density conventions in lossy and dispersive media.

**Correct approach**: state the mode-area definition explicitly, keep the same normalization across all compared cases, and avoid mixing literature values computed under incompatible conventions.

---

## 5. Domain-Specific Quality Metrics

| Metric | Abbreviation | Physical meaning | Typical value range |
| :--- | :--- | :--- | :--- |
| Propagation length | $L_{prop}$ | Distance over which guided power decays to $1/e$ | Strongly geometry- and wavelength-dependent; from very short sub-10-µm scales in highly confined structures to much longer values in long-range or hybrid designs |
| Propagation loss | $\alpha$ | Attenuation per unit length | Often reported in dB/µm, dB/mm, or $cm^{-1}$; unit choice must be stated explicitly |
| Effective index | $n_{eff}$ | Modal phase constant normalized by free-space wave number | Usually larger than the cladding index for bound modes; complex in lossy structures |
| Effective mode area | $A_{eff}$ | Measure of modal confinement | Often far below the diffraction-limited area in strongly confined plasmonic modes |
| Confinement factor | $\Gamma$ | Fraction of modal energy in a target region | Highly definition-dependent; must be tied to a specific region |
| Coupling efficiency | $\eta$ | Fraction of launched power coupled into the target guided mode | Strongly dependent on coupler design and alignment, not only on the waveguide core |
| Crosstalk | — | Unwanted power transfer between nearby channels | Most important in dense integration or coupled-waveguide layouts |
| Figure of merit | FOM | Composite balance of confinement and attenuation | Not universal; definition must be written explicitly each time |

### Metric-usage rules

- Do not compare values across papers unless the metric definition and normalization are compatible.
- Never report a figure of merit without writing its exact formula.
- Keep waveguide metrics separate from modulator metrics such as extinction ratio, bandwidth, or energy per bit.

---

## 6. Common Assumption Pitfalls

| Pitfall | Trigger condition | How to recognize it | Correct approach |
|------|---------|---------|---------|
| Treating Drude-only Au/Ag as quantitatively final at optical frequencies | Visible or near-IR noble-metal modeling | Simulated resonance or loss disagrees strongly with standard optical-constant references | Use experimentally anchored optical constants or a validated Drude-Lorentz fit |
| Confusing coupling loss with propagation loss | Single-length transmission measurement | Reported loss changes dramatically with coupler redesign | Separate launch loss from propagation attenuation with cut-back or calibrated references |
| Treating nanostructure permittivity as bulk permittivity without qualification | Thin films, nanowires, ultra-small gaps | Measured behavior is systematically lossier or shifted than simulation | Use thin-film or geometry-aware material data when available |
| Ignoring substrate-induced asymmetry | Hybrid structures placed on dielectric substrates | Symmetric theory predicts behavior not seen in fabricated devices | Include the real substrate stack in the model and discuss asymmetry explicitly |
| Ignoring roughness-driven scattering | Fabricated metal sidewalls or films with nontrivial morphology | Measured loss exceeds smooth-interface predictions | Measure roughness and treat scattering as a separate or additional loss channel |
| Using insufficient mesh refinement at metal-dielectric boundaries | Full-wave simulation with strong field localization | Results change noticeably when mesh is refined | Apply local mesh refinement and perform convergence checks |
| Assuming every measured bright spot represents the native guided mode | Near-field or scattering-based imaging | Hotspots move or change with probe position or out-scatter geometry | Validate mode identity through multiple observables, not one image alone |
| Mixing passive waveguide metrics with active-device metrics | Discussion drifts toward modulators | Extinction ratio or drive conditions start appearing as primary criteria | Keep this profile waveguide-centered and move active-device optimization elsewhere |

---

## 7. Literature Anchors

| Type | Reference | Why it matters |
|------|------|-------|
| Foundational textbook | Maier, *Plasmonics: Fundamentals and Applications* (2007) | Standard introductory anchor for plasmonics, metal optics, and SPP fundamentals |
| Optical-constant reference | Johnson and Christy, *Optical Constants of the Noble Metals* (1972) | Canonical experimental dataset for Au and Ag optical constants |
| Waveguide characterization methods | Berini et al., *Characterization of long-range surface-plasmon-polariton waveguides* (2005) | Clear waveguide-level framing using attenuation, coupling efficiency, and confinement |
| Practical waveguide review | Holmgaard and Bozhevolnyi, *Dielectric-loaded plasmonic waveguide components: Going practical* (2013) | Useful review for practical dielectric-loaded plasmonic-waveguide components |
| Comparative geometry review | Messner et al., *Plasmonic, photonic, or hybrid? Reviewing waveguide geometries for electro-optic modulators* (2023) | Valuable comparative framework for plasmonic, photonic, and hybrid geometries |
| Hybrid-geometry study | Studies on asymmetric and hybrid plasmonic waveguides on substrates | Important for geometry sensitivity, substrate asymmetry, and confinement-loss balancing |

---

## Cross-Domain Links

### Closest Related Domain Profiles

| Profile name | Overlap dimensions | Typical use split |
|------|------|-------|
| Silicon photonics waveguides | first principles, modeling tools, fabrication tolerance | Prefer the silicon-photonics profile when metal loss is not central and dielectric guiding dominates |
| Plasmonic modulators | geometry, materials, application targets | Prefer this waveguide profile for passive modal reasoning; switch to the modulator profile when bias-driven performance metrics dominate |
| Nanofabrication metrology | measurement tools, interpretation logic | Prefer the metrology profile when the main uncertainty is whether fabricated geometry matches design intent |
| Optical sensing / SERS platforms | confinement, field enhancement, application targets | Prefer this profile for mode and loss interpretation; prefer the sensing profile when analyte interaction and enhancement statistics become primary |

### Authoring notes

- This profile should remain separate from a plasmonic-modulator profile because the governing metrics and decision logic are not the same.
- It is acceptable for the same geometry to appear in more than one profile, provided each profile evaluates it using different primary criteria.

---

## Cross-Domain Conflict Notes

| Issue / constraint | Other profile(s) involved | Potential conflict | AI confirmation question |
|------|------|-------|-------|
| Long propagation versus compact active functionality | Plasmonic modulators | A geometry that is attractive for long propagation may be suboptimal for strong active modulation or compact switching | Is the priority passive transport performance or active modulation performance? |
| Bulk optical constants versus fabricated thin-film behavior | Nanofabrication metrology | Bulk-reference permittivity may underpredict loss or misplace resonances in real thin films | Should the analysis assume textbook bulk data or fabrication-specific thin-film data? |
| Strong confinement versus sensing robustness | Optical sensing / SERS platforms | A geometry optimized for extreme confinement may be more fabrication-sensitive and less reproducible | Is peak local enhancement or robust reproducible performance the main goal? |

### Authoring notes

- These conflict prompts should be used early, before the AI commits to a geometry recommendation.
- If a user asks for "best" plasmonic waveguide performance without stating a metric, the AI should ask a clarification question instead of assuming a single universal optimum.

---

## AI Decision-Trigger Checklist for This Profile

- [ ] User says "plasmonic waveguide" without a metric → AI should ask whether the priority is propagation length, confinement, or a trade-off.
- [ ] User uses Au or Ag optical-frequency simulations with a simple Drude fit → AI should warn about interband-transition limitations.
- [ ] User reports waveguide loss from a single transmission number → AI should ask whether coupling loss has been separated.
- [ ] User describes a hybrid geometry on a substrate → AI should ask whether substrate asymmetry is included in the model.
- [ ] User compares mode-area values from different papers → AI should ask whether the definitions are identical.
- [ ] User presents FDTD or FEM results near metal-dielectric boundaries → AI should ask about mesh convergence and local refinement.
- [ ] User claims unusually long propagation together with extreme confinement → AI should ask whether the result has been cross-validated and whether the metric definitions are explicit.
- [ ] User begins discussing extinction ratio, drive voltage, or modulation bandwidth → AI should recommend switching to a modulator-domain profile.
