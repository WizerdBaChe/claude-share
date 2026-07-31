# Sub-profile: Surface and Composition Characterization — under Topological Insulator

> Parent domain: `topological_insulator.md`
> Branch axis: method
> Scope: UPS work-function/valence measurements, XPS chemical-state analysis, and
> SEM/TEM-EDS composition mapping for TI surfaces, films, and interfaces.
> Inherits from parent: available Nodes 1–2. The parent Node 3 is currently
> incomplete; use the method-specific rules below rather than assuming a toolchain.

## Contents

- Measurement rules
- Extraction methods
- Assumption pitfalls
- Decision triggers
- Evidence anchors

## 2. Branch-Specific Measurement Rules

| Target | Method | Valid output | Critical limitation |
|---|---|---|---|
| Work function and occupied valence states | UPS | Spectrum width, secondary-electron cutoff (SECO), valence onset | Surface condition, analyzer geometry, sample bias, charging, and energy-axis convention |
| Elemental/chemical state near the surface | XPS | Core-level energies, line shapes, relative intensities, composition under a stated model | Information depth depends on electron energy, material, emission geometry, and analysis definition |
| Spatial elemental distribution | SEM-EDS or TEM/STEM-EDS | Characteristic X-ray spectra/maps and model-dependent composition | Interaction/generation volume, peak overlap, absorption, fluorescence, standards, thickness, and geometry |

UPS, XPS, and EDS answer different questions. Do not present them as interchangeable
surface-composition measurements.

## 4. Branch-Specific Extraction Methods

### UPS work function from SECO

**Applicable conditions**: the sample is sufficiently conductive and flat for the chosen
method, the energy scale is calibrated, sample bias is optimized, and the cutoff is
resolved.

**Common error**: ⚠️ reading a cutoff from a plotted binding-energy axis without stating
the axis convention or bias correction.

**Correct approach**: calculate work function from the calibrated photon energy and the
measured spectrum width (Fermi edge to SECO), propagate uncertainty, and document sample
orientation, bias, surface preparation, and cutoff model. Treat multiple or sloped
onsets as an interpretation problem, not an invitation to select the desired intercept.

### XPS chemical-state and composition analysis

**Applicable conditions**: the peak model, energy reference, background, line shape,
relative sensitivity factors, and information-depth definition are stated.

**Common error**: ⚠️ using a fixed “5–10 nm depth,” arbitrary adventitious-carbon
referencing, or peak positions alone to assign oxidation states.

**Correct approach**: report kinetic energy/material/emission geometry for depth claims;
use chemically and physically constrained peak models; state the reference strategy and
quantification assumptions.

### EDS mapping and quantification

**Applicable conditions**: beam energy, current/dose, specimen geometry/thickness,
detector configuration, standards/model, and resolvable X-ray lines are documented.

**Common error**: ⚠️ treating a color map or standardless atomic percentage as direct,
surface-specific stoichiometry.

**Correct approach**: inspect spectra behind the map, deconvolve overlaps, model the
generation/interaction volume, and use standards and matrix/thin-film corrections when
the conclusion depends on quantitative composition.

## 6. Branch-Specific Assumption Pitfalls

| Pitfall | Trigger condition | How to recognize it | Correct approach |
|---|---|---|---|
| Calling XPS or UPS strictly nondestructive | Sensitive TI surfaces are repeatedly irradiated | Dose/time history is absent | Check beam-induced chemistry, charging, desorption, and drift with dose/time controls |
| Treating one XPS spectrum as bulk composition | Surface spectrum is generalized to the whole crystal | No depth or complementary bulk method | State the information depth and pair with an appropriate bulk/cross-section method |
| Treating EDS as surface-sensitive | SEM-EDS is compared directly with XPS | Interaction volume is not modeled | Use beam/geometry simulation or TEM/STEM geometry and describe the sampled volume |
| Inferring exact stoichiometry from a map | Bi:Se ratio is read from display colors | No standards, peak-fit, absorption, or uncertainty | Quantify spectra with an appropriate model and uncertainty |
| Ignoring heterogeneous-work-function behavior | UPS SECO is broad or multi-onset | One line is chosen without a model | Report heterogeneity and cross-check with spatially resolved or contact-potential methods |
| Assigning transport channels from chemistry alone | XPS/UPS/EDS are used to claim surface-dominated conduction | No transport or band-dispersion evidence | Combine chemistry with ARPES/transport and channel-specific tests |

## AI Decision-Trigger Checklist for This Sub-profile

- [ ] User reports a UPS work function → ask for photon energy, energy-axis convention,
      calibration, sample bias, geometry, surface preparation, and uncertainty.
- [ ] User reports a fixed XPS depth → ask for kinetic energy, material, take-off angle,
      and whether the quantity is IMFP, EAL, MED, or information depth.
- [ ] User assigns an XPS oxidation state from one peak position → request reference,
      line shape, satellites, related core levels, and controls.
- [ ] User claims EDS proves exact Bi:Se stoichiometry → request raw spectra, standards
      or quantification model, overlap handling, sampled volume, and uncertainty.
- [ ] User proposes a measurement sequence → place lower-dose/non-destructive checks
      before destructive sectioning, while confirming beam sensitivity for the actual sample.

## Evidence Anchors

- Helander et al., “Pitfalls in measuring work function using photoelectron
  spectroscopy,” *Applied Surface Science* 256, 2602–2605 (2010).
  DOI: https://doi.org/10.1016/j.apsusc.2009.11.002
- Kim et al., “Work function measurement by ultraviolet photoelectron spectroscopy:
  VAMAS interlaboratory study,” *Journal of Vacuum Science & Technology A* 41,
  053211 (2023). DOI: https://doi.org/10.1116/6.0002852
- Baer et al., “Practical guides for X-ray photoelectron spectroscopy: First steps in
  planning, conducting, and reporting XPS measurements,” *JVST A* 37, 031401 (2019).
  DOI: https://doi.org/10.1116/1.5065501
- Powell, “Practical guide for IMFPs, EALs, MEDs, and information depths in XPS,”
  *JVST A* 38, 023209 (2020), with erratum.
  DOI: https://doi.org/10.1116/1.5141079; erratum: https://doi.org/10.1116/6.0000463
- Ritchie et al., “Quantification of Unsupported Thin-Film X-ray Spectra Using Bulk
  Standards,” *Microscopy and Microanalysis* 29 (2023).
  DOI: https://doi.org/10.1093/micmic/ozad109
