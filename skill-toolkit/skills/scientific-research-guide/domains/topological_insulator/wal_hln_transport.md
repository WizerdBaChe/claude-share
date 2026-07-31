# Sub-profile: WAL, HLN, and Hall Transport — under Topological Insulator

> Parent domain: `topological_insulator.md`
> Branch axis: phenomenon / method
> Scope: weak antilocalization (WAL), Hikami–Larkin–Nagaoka (HLN) fitting, and
> supporting Hall measurements in topological-insulator films and flakes.
> Inherits from parent: available Nodes 1–2. The parent Node 3 is currently
> incomplete; use the method-specific rules below rather than assuming a toolchain.

## 4. Branch-Specific Fitting Methods

### HLN magnetoconductance fitting

**Applicable conditions**: quantum-interference transport is quasi-two-dimensional and
diffusive over a justified low-field window; the elastic, phase-coherence, magnetic, and
spin-orbit length scales are compatible with the selected HLN form.

**Common error**: ⚠️ fitting magnetoresistance directly, using an arbitrary wide field
range, and interpreting the prefactor as a literal count of topological surfaces.

**Correct approach**:

1. Define `Δσ(B)` and the exact HLN sign/prefactor convention.
2. Convert resistance to conductivity using the actual tensor and device geometry.
3. Symmetrize/antisymmetrize field sweeps as appropriate and document background removal.
4. Fit a low-field window justified by the diffusive length scales.
5. Repeat across several nested fit windows and temperatures.
6. Inspect residuals and parameter covariance; report window sensitivity.
7. Interpret the prefactor only after considering bulk, surface, 2DEG, and coupled
   coherent channels.

### Hall extraction

**Applicable conditions**: a single dominant carrier produces a linear Hall response and
the sample geometry/contact assumptions are satisfied.

**Common error**: ⚠️ applying `n = 1/(qR_H)` and `μ = σ/(qn)` to nonlinear or multiband
Hall data and then using that result as proof of surface-only transport.

**Correct approach**: inspect Hall linearity, field range, contact offsets, and
longitudinal admixture. Use an explicitly justified multicarrier model when needed, and
report whether density is sheet or bulk density.

## 5. Branch-Specific Quality Metrics

| Metric | Interpretation rule |
|---|---|
| Phase-coherence length `L_phi` | Must be positive, physically scaled, and stable enough across fit windows to interpret; temperature dependence is more informative than one value |
| HLN prefactor | Convention- and model-dependent; never compare values before aligning equations and channel assumptions |
| Fit-window sensitivity | Large parameter drift across reasonable low-field windows signals model/background inadequacy |
| Residual structure | Systematic curvature or field-odd residuals indicate missing background, tensor mixing, or an unsuitable model |
| Hall linearity | A prerequisite for simple one-carrier extraction, not proof of a topological surface channel |

## 6. Branch-Specific Assumption Pitfalls

| Pitfall | Trigger condition | How to recognize it | Correct approach |
|---|---|---|---|
| Treating a zero-field cusp as unique proof of TSS transport | User identifies WAL by shape alone | No thickness, angle, gate, or channel evidence | Treat WAL as quantum-interference evidence; use complementary channel discrimination |
| Reading the HLN prefactor as an exact channel count | User maps one fitted value directly to top/bottom surfaces | Equation convention and channel coupling are unstated | Align conventions and test multiple-channel interpretations |
| Fitting outside the diffusive regime | Elastic mean free path is comparable to the magnetic length in the fit window | Parameters depend strongly on the high-field endpoint | Use a model valid for the measured regime or restrict the window |
| Ignoring classical magnetoresistance | Wide-field data are fit with HLN alone | Residuals curve systematically at larger fields | Model or remove a justified background before low-field interpretation |
| Fitting resistance instead of magnetoconductance | Raw `Rxx(B)` is inserted into the HLN expression | Hall mixing and tensor inversion are absent | Convert the measured tensor to conductivity with geometry corrections |
| Claiming “surface only” from Hall plus WAL | A one-carrier Hall result and WAL cusp are treated as decisive | Bulk/2DEG channels remain plausible | Add gate, thickness, angle, spectroscopy, or multichannel evidence |
| Treating `WAL@2 K` as a method name | Temperature is attached to the acronym | No temperature sweep or dephasing test | Record 2 K as one condition and analyze temperature dependence |

## AI Decision-Trigger Checklist for This Sub-profile

- [ ] User says `HNL equation` → correct it to HLN only after confirming the intended
      Hikami–Larkin–Nagaoka model.
- [ ] User reports an HLN prefactor as a channel count → request the exact equation,
      sign convention, field window, and multichannel assumptions.
- [ ] User fits a broad field range → ask how the diffusive low-field regime was chosen.
- [ ] User reports only the best-fit curve → require residuals, covariance/uncertainty,
      and fit-window stability.
- [ ] User uses linear Hall formulas on nonlinear Hall data → require a multicarrier or
      other physically justified model.
- [ ] User claims surface-state dominance from WAL alone → request independent
      thickness, gate, angle, or spectroscopic evidence.

## Evidence Anchors

- Hikami, Larkin, and Nagaoka, *Progress of Theoretical Physics* 63, 707–710 (1980).
  DOI: https://doi.org/10.1143/PTP.63.707
- Adroguer et al., “Conductivity corrections for topological insulators with
  spin-orbit impurities: Hikami–Larkin–Nagaoka formula revisited,”
  *Physical Review B* 92, 241402(R) (2015).
  DOI: https://doi.org/10.1103/PhysRevB.92.241402
- Wang et al., “Crossover between weak antilocalization and weak localization of bulk
  states in ultrathin Bi₂Se₃ films,” *Scientific Reports* 4, 5817 (2014).
  DOI: https://doi.org/10.1038/srep05817
- NIST, “Hall Effect Measurements,” archived measurement guide:
  https://www.nist.gov/pml/nanoscale-device-characterization-division/popular-links/hall-effect
