# Sub-profile: Bi2Se3 Plasmonic and Photogalvanic Branch

> Parent domain: topological_insulator
> Branch axis: method
> Scope: Bi2Se3 surface, bulk, and massive-2DEG plasmon contributions; plasmonic or waveguide integration; polarization-resolved CPGE/LPGE and directional photocurrent.
> Inherits: topological_insulator.md and bi2se3_material.md
> Last updated: 2026-08-03

Use this file together with bi2se3_material.md. The parent material branch remains authoritative for thickness, defects, oxidation, composition, ARPES, transport, and multi-channel fitting. Generic plasmonic geometry remains in the plasmonic_waveguide domain; this file adds the Bi2Se3-specific material, symmetry, and photoresponse constraints.

## 1. Theoretical Framework Anchoring

### 1.1 Carrier and mode decomposition

For a Bi2Se3 optical or terahertz response, keep the possible channels separate:

| Channel | Physical origin | What must be established |
|---|---|---|
| Dirac surface state | Topological surface band with approximately linear dispersion near the Dirac point | Surface-state energy, chemical potential, thickness, disorder and surface quality |
| Conventional surface or inversion-layer 2DEG | Band bending, accumulation, quantum-well subbands, or trivial surface states | Subband occupation, carrier density, confinement and distinction from the TSS |
| Bulk carriers | Defects, vacancies, unintentional doping or substrate contribution | Bulk carrier density, mobility, temperature dependence and geometry dependence |
| Collective plasmon or plasmon-polariton | Coupled charge response of one or more channels and the electromagnetic environment | Dispersion, damping, mode polarization, dielectric environment and carrier model |
| Thermo-electric or photo-thermal response | Absorption, heating, Seebeck or bolometric response | Temperature rise, power dependence, temporal response and thermal boundary |

The observation of a plasmon-like resonance does not by itself identify a Dirac plasmon. Experiments on Bi2Se3 have reported interplay between bulk, conventional surface, and Dirac surface plasmons; see [Interplay of Surface and Dirac Plasmons in Topological Insulators](https://doi.org/10.1103/PhysRevLett.115.216802). Recent terahertz work likewise models bulk carriers, Dirac carriers, and massive 2DEG channels together: [Terahertz Plasmon Polaritons in Large Area Bi2Se3 Topological Insulators](https://doi.org/10.1002/adom.202301673).

In a thin slab, symmetric or antisymmetric collective modes are sometimes labelled optical and acoustic. Those labels describe a model limit and do not automatically mean pure charge and pure spin modes. Substrate asymmetry, bulk screening, inversion-layer carriers, phonons, and finite thickness can hybridize the modes. Treat spin-charge separation as a theory question that requires a channel and symmetry model, not as a default experimental interpretation.

### 1.2 Coupling and photogalvanic response

For an interface between dielectrics with relative permittivities epsilon1 and epsilon2, a local single-interface SPP estimate is:

~~~text
k_SPP = (omega / c) * sqrt(epsilon1 * epsilon2 / (epsilon1 + epsilon2))
~~~

Use a complex dielectric function or complex conductivity when loss matters. If the field varies as exp(i k x), then a field-amplitude propagation length is often written as L_field = 1 / (2 Im(k)). State the convention explicitly; an intensity-defined length can differ by a factor of two.

Waveguide-integrated Bi2Se3 can couple guided optical fields to spin-momentum-locked surface electrons. The relevant observable may be a propagation-direction-dependent photocurrent, but it must be separated from ordinary absorption, LPGE, CPGE, photon drag, contact asymmetry, and thermal gradients. See [Spin-momentum locked interaction between guided photons and surface electrons in topological insulators](https://doi.org/10.1038/s41467-017-02264-y).

Spintronics or spin-transfer-torque applications are downstream application questions. A plasmon resonance or a polarization-dependent current is not, by itself, evidence of a usable spin-transfer torque; require a defined torque observable, interface, current path, and control experiment.

For a C3v surface, a commonly used polarization-angle decomposition is:

~~~text
j(alpha) = C sin(2 alpha)
          + L1 sin(4 alpha)
          + L2 cos(4 alpha)
          + D
~~~

The coefficient names and angle zero must be defined in the experiment. C is not automatically a pure CPGE coefficient: direction reversal, helicity reversal, incidence-angle, TE/TM, power, temperature, and contact-symmetry controls are needed. In an ideal C3v surface at normal incidence, direct helicity-dependent current can be symmetry-suppressed; external in-plane symmetry breaking, strain, magnetic field, or oblique incidence can change the allowed response. Oblique incidence also permits photon-drag and related backgrounds. See [Circular photogalvanic effect on topological insulator surfaces](https://doi.org/10.1103/PhysRevB.83.035309).

### 1.3 Decision fork before modeling

When a user says “Bi2Se3 plasmonic” or “angular photocurrent,” classify the primary target:

- Dispersion or complex conductivity: use a multi-channel carrier model constrained by Hall, ARPES, ellipsometry, or near-field data.
- Waveguide-integrated directional response: identify the guided mode, field polarization, propagation direction, surface orientation, and reversal controls.
- Generic resonator or sensor geometry: route the geometry to plasmonic_waveguide and add Bi2Se3 material response only after calibration.
- Symmetry or photogalvanic tensor: define the point group, incidence geometry, polarization convention, and allowed background terms.

### 1.4 Inviolable constraints

1. A resonance shift or linewidth alone does not uniquely determine Bi2Se3 surface conductivity. Bulk carriers, massive 2DEG channels, substrate, geometry, radiation loss and fabrication bias can be correlated.
2. “Surface plasmon” is not proof of “Dirac plasmon.” Establish the band, carrier density, dispersion, and alternative channels.
3. SPP is a TM-like bound mode in the ideal planar interface problem; a measured resonance or guided mode can be hybrid, radiative, TE-like, or photonic. Identify the mode with field, polarization and dispersion evidence.
4. CPGE, LPGE, photon drag, thermoelectric, bolometric and contact-asymmetry currents can share angular harmonics. Polarization fits require controls, not only a good residual.
5. The C3v normal-incidence restriction is conditional on ideal symmetry and direct photocurrent. Do not rewrite it as “CPGE is only possible at oblique incidence.”
6. Oxidation, thickness, defects, band bending and substrate leakage from bi2se3_material.md remain active variables in any plasmonic or photogalvanic interpretation.
7. A generic HPWG or racetrack-ring sensitivity number is not a Bi2Se3 result unless Bi2Se3 optical constants, loss, carrier density and fabrication are part of the model and experiment.

## 2. Measurement Tool Inventory

| Target | Tool or measurement | Output | Conditions that must travel with the result | Common misuse |
|---|---|---|---|---|
| Surface band and chemical potential | ARPES or SARPES | Dirac point, surface bands, spin texture, band bending | Photon energy, polarization, temperature, cleave/aging, energy and momentum resolution | Treating every extra band as a new topological cone |
| Bulk and surface carriers | Hall and magnetotransport | Carrier density, mobility, channel multiplicity, temperature dependence | Geometry, thickness, contact arrangement, field range and fitting model | Using one-band Hall data as proof of a single Dirac channel |
| Composition and thickness | XPS, EDS, AFM, XRD, TEM, ellipsometry | Oxidation, thickness, roughness, optical constants, layer structure | Calibration, ambient exposure, roughness model, substrate and depth sensitivity | Feeding nominal film thickness or bulk optical constants into a thin-film inverse fit |
| Plasmon energy and dispersion | HREELS, IR/THz spectroscopy, near-field microscopy, holography | Resonance energy, q-dispersion, damping and mode profile | Momentum calibration, dielectric environment, temperature, polarization and excitation power | Assigning a peak to a Dirac plasmon without a carrier-model comparison |
| Complex optical response | Ellipsometry, reflection/transmission, calibrated near-field response | Complex dielectric function or conductivity | Layer model, surface roughness, substrate, frequency range and uncertainty | Fitting a surface response while ignoring bulk or substrate channels |
| Guided-mode coupling | TM/TE waveguide spectra, bidirectional propagation, near-field or leakage radiation | Coupling, propagation loss, mode polarization and directionality | Waveguide geometry, mode excitation, contact layout and reference arm | Calling any TM-polarized response an SPP |
| Photogalvanic current | Polarizer, quarter-wave plate, chopper, lock-in, calibrated power and angle stage | C, L1, L2, D or an equivalent tensor decomposition | Angle zero, helicity convention, incidence angle, modulation frequency, temperature and contacts | Calling C pure CPGE without helicity and direction controls |
| Thermal and photo-thermal response | Thermometry, power modulation, time response, thermal model | Temperature rise, bolometric or thermoelectric contribution | Thermal anchor, substrate, duty cycle, spot size, contacts and calibration | Calling an absorbed-power current a spin-selective photocurrent |

The original notes mention photonic crystals, racetrack ring resonators, hybrid plasmonic waveguides, RIE-defined geometry, TM/TE contrast, and C3v symmetry. These are valid method categories, but the geometry- and etch-specific implementation belongs in the existing plasmonic_waveguide base and terminology_and_geometry reference. This branch should only add the Bi2Se3 carrier, symmetry, and photoresponse interpretation.

## 3. Standard Modeling Toolchain

~~~text
Bi2Se3 growth and material characterization
    -> thickness, oxidation, carrier and optical-constant constraints
    -> bulk + Dirac-surface + massive-2DEG conductivity model
    -> analytical dispersion or RPA / k.p / tight-binding comparison
    -> FEM, FDTD, RCWA, eigenmode, HPWG or RTRR geometry model
    -> TM/TE, helicity, direction, temperature and power controls
    -> joint fit of spectra, transport and photocurrent
~~~

| Stage | Minimum inputs | Useful outputs | Boundary condition |
|---|---|---|---|
| Material state | Thickness, QL count, oxidation, chemical potential, bulk and surface carrier evidence, and growth route such as MBE | Plausible channel set and uncertainty | Load bi2se3_material.md before assigning a surface-only model |
| Conductivity model | Complex bulk, TSS, 2DEG and substrate responses; scattering and temperature | Frequency- and q-dependent response | Do not collapse correlated channels without an identifiability check |
| Plasmon or mode model | Dielectric environment, geometry, boundary condition, polarization and loss | Dispersion, mode profile, Q, propagation length, coupling | Identify whether the result is SPP, photonic, Bloch, cavity, or hybrid |
| Resonator or waveguide inverse fit | Resonance position, linewidth, baseline, geometry and reference | Candidate complex conductivity or effective index | Calibrate geometry and nuisance loss; do not infer unique conductivity from one shift |
| Photocurrent model | Point group, incident angle, polarization, contacts, thermal and photon-drag terms | CPGE/LPGE/background coefficients and uncertainty | Reversal and null controls are part of the model, not optional decoration |
| Joint validation | Spectra plus Hall/ARPES/temperature/direction/power data | Mechanism discrimination and residuals | A polarization-angle fit alone is not mechanism validation |

The generic RTRR and HPWG terms route as follows:

- Use plasmonic_waveguide.md for mode definitions, propagation loss, geometry, fitting, and generic sensor metrics.
- Use plasmonic_waveguide/terminology_and_geometry.md for SP/SPP/SPR/LSP/LSPR/LSPP and IMI/MIM/HPWG terminology.
- Use this file for whether a Bi2Se3 response is consistent with TSS, 2DEG, bulk, symmetry, or thermal channels.
- Treat SSH or other photonic-lattice language as a separate model only when the actual geometry and Hamiltonian justify it; it is not implied by the presence of Bi2Se3.

## 4. Domain-Specific Fitting Methods

| Method | Applicable question | Assumptions and required conditions | Common error | Correct practice |
|---|---|---|---|---|
| Dirac or mixed plasmon dispersion fit | Is the observed mode compatible with a TSS contribution? | q-dependent data, chemical potential, dielectric environment, bulk and 2DEG alternatives | Fit one surface channel to a mixed-carrier peak | Fit competing channel models and constrain with Hall/ARPES/ellipsometry |
| Resonance shift and linewidth inversion | Can an effective index or complex conductivity be estimated? | Calibrated geometry, reference device, radiative and material loss model | Equate shift with surface conductivity and linewidth with absorption only | Fit complex response with nuisance loss and independent material constraints |
| SPP propagation-length extraction | How far does a bound mode propagate? | Complex k, field/intensity convention, mode identification and substrate loss | Report 1/(2 k'') without defining whether k'' is field or intensity | State the exp(i k x) convention, mode, wavelength/frequency and loss partition |
| Polarization-angle harmonic fit | How do helicity and linear-polarization terms vary? | Defined alpha, QWP retardance, incidence geometry, point group and background terms | Interpret C as pure CPGE or L terms as unique mechanisms | Repeat with helicity, propagation direction, incidence angle, temperature and power reversals |
| TM/TE and bidirectional comparison | Is a guided mode or spin-momentum channel involved? | Matched coupling, mode overlap, contact symmetry and reference path | Attribute any TM enhancement to spin-momentum locking | Compare TM/TE and forward/backward propagation with field and thermal controls |
| Temperature/power photocurrent fit | Is the signal photo-thermal or photogalvanic? | Calibrated absorbed power, thermal time constant and contact geometry | Label a power-dependent current as CPGE | Fit thermal and photogalvanic terms together and report residual degeneracy |
| C3v tensor analysis | Which current components are symmetry-allowed? | Surface orientation, incidence direction, external symmetry breaking and third-rank tensor convention | Apply normal-incidence rules to oblique or strained samples | State the actual point group and geometry before reducing the tensor |

## 5. Domain-Specific Quality Metrics

| Metric | How to report it | Anchored examples or range status | Suspicious comparison |
|---|---|---|---|
| Plasmon energy and q | Frequency/energy, q calibration, temperature, carrier density, dielectric environment and mode label | HREELS work on Bi2Se3 reported a surface plasmon near 104 meV and a Dirac-plasmon feature near q about 0.04 inverse Angstrom under its own conditions: [study](https://doi.org/10.1103/PhysRevLett.115.216802). | Treating a single energy as a material constant |
| Effective index or confinement | Definition, reference medium, frequency, mode and geometry | Coupled Dirac-plasmon stripe-array work reports effective-index values up to about 211 for a specific geometry: [study](https://doi.org/10.1002/adom.201800113). | Transferring a stripe-array value to a generic waveguide |
| Propagation length | Field or intensity convention, frequency, mode, substrate and loss partition | No universal range accepted here; use device-specific measured or simulated values | Comparing field-length and intensity-length conventions |
| Resonance Q and linewidth | Resonance definition, fit window, baseline, radiation/material loss and temperature | No universal Bi2Se3 range accepted; Q is geometry and loss-model dependent | Comparing Q from different linewidth definitions |
| Complex surface conductivity | Frequency, real/imaginary convention, model, thickness, bulk/2DEG subtraction and uncertainty | No universal range accepted; one resonance does not identify it uniquely | Treating an effective-index fit as a direct conductivity measurement |
| CPGE/LPGE coefficients | Current density normalization, power, frequency, angle, helicity and tensor convention | No universal range accepted; coefficient definitions vary by geometry | Comparing C, L1 or L2 without identical conventions |
| Photocurrent directionality | Forward/backward ratio or signed current with contact layout and thermal controls | Study-specific; do not use a direction ratio without contact and thermal references | Calling contact asymmetry spin-momentum locking |
| RI sensing metric | RIU definition, analyte/environment, geometry, Q, linewidth and detection limit | Generic HPWG/RTRR papers are geometry references, not Bi2Se3 evidence; see [generic RTRR study](https://doi.org/10.3390/mi15050610). | Importing a generic sensitivity number into a Bi2Se3 device |

## 6. Common Assumption Pitfalls

| Pitfall | Trigger | Why it fails | Recovery |
|---|---|---|---|
| Surface-only conductivity assumed | A plasmon or resonance is fit with one TSS sheet | Bulk carriers, massive 2DEG, substrate and oxidation can dominate | Measure or constrain all plausible channels and run competing fits |
| Dirac plasmon claimed from a peak | Only a peak energy or one resonance is shown | Conventional surface or bulk plasmons can overlap | Require dispersion, carrier model, chemical-potential and alternative-channel checks |
| Optical/acoustic labels treated as pure charge/spin | Thin-slab modes are assigned a fixed character | Asymmetry, finite thickness and extra channels hybridize modes | State the symmetry/model limit and calculate mode composition |
| SPP assigned to every TM signal | A response is TM-polarized | Hybrid photonic, Bloch, cavity and radiative modes can also be TM-like | Show mode profile, dispersion, confinement and loss evidence |
| CPGE only-oblique rule overgeneralized | Normal-incidence data are dismissed or oblique data are called pure CPGE | Symmetry breaking and photon drag change the allowed terms | State C3v assumptions, incidence geometry and external symmetry breaking |
| CPGE/LPGE/thermal terms mixed | A harmonic fit has a good residual | Different mechanisms share angular harmonics and contact asymmetry | Use helicity, direction, TE/TM, temperature, power and null controls |
| Propagation-length convention hidden | L is calculated from Im(k) without a convention | Field and intensity decay lengths differ | Define the field convention and partition material, radiation and scattering loss |
| Generic RTRR transferred to Bi2Se3 | A generic RI sensitivity or Q is quoted as a material result | Geometry and material response are not the same evidence | Route geometry to plasmonic_waveguide and recalibrate Bi2Se3 response |
| Oxidation or thickness ignored | Fresh-film optical data are compared with aged or ultrathin data | Surface chemistry, hybridization, band bending and QW states change the response | Load bi2se3_material.md and report aging, QL count and thickness |
| “Scorching heat” treated as a validated term | Notes use informal heat language without a thermal measurement | It may mean local absorption, thermoplasmonic heating, or an unresolved guess | Rename only after defining temperature, power, spatial scale and thermal model |
| “Angular modulation” treated as a complete mechanism | A periodic angular curve is presented without geometry | The angle may refer to polarization, incidence, sample rotation or analyzer angle | Record the exact angle definition before fitting or interpreting |
| SSH or topological-photonics language imported automatically | A ring or photonic crystal is called SSH-like | The required lattice, coupling and Hamiltonian may be absent | Verify the actual geometry and model before using the term |

## 7. Literature Anchors

1. “Interplay of Surface and Dirac Plasmons in Topological Insulators: The Case of Bi2Se3,” *Physical Review Letters* 115, 216802 (2015). [DOI](https://doi.org/10.1103/PhysRevLett.115.216802)
2. “Coupled Dirac Plasmons in Topological Insulators,” *Advanced Optical Materials* 6, 1800113 (2018). [DOI](https://doi.org/10.1002/adom.201800113)
3. “Spin-momentum locked interaction between guided photons and surface electrons in topological insulators,” *Nature Communications* 8, 2141 (2017). [DOI](https://doi.org/10.1038/s41467-017-02264-y)
4. “Circular photogalvanic effect on topological insulator surfaces: Berry-curvature-dependent response,” *Physical Review B* 83, 035309 (2011). [DOI](https://doi.org/10.1103/PhysRevB.83.035309)
5. “Plasmonics in topological insulators: Spin-charge separation, influence of inversion layer, and phonon-plasmon coupling,” *ACS Photonics* (2017). [Publisher](https://pubs.acs.org/doi/10.1021/acsphotonics.7b00524)

## Cross-Domain Links

### Closest Related Domain Profiles

| Related profile | Link | Boundary |
|---|---|---|
| bi2se3_material.md | Required companion for QL thickness, oxidation, defects, ARPES, transport and multi-channel WAL/HLN | Do not duplicate its material characterization tables here |
| plasmonic_waveguide.md | Use for generic SPP/SP/SPR/LSP terminology, mode solving, waveguide fitting and loss accounting | Do not treat generic waveguide metrics as Bi2Se3 evidence |
| plasmonic_waveguide/terminology_and_geometry.md | Use for HPWG, MIM/IMI, resonator and geometry terminology | Generic geometry must be independently mapped to the Bi2Se3 material model |
| surface_and_composition_characterization.md | Use for surface-sensitive characterization planning | Photoresponse interpretation still needs the symmetry and thermal controls in this branch |

### Cross-Domain Conflict Notes

| Issue / constraint | Other profile(s) involved | Potential conflict | AI confirmation question |
|---|---|---|---|
| Generic SPP or resonator fit versus Bi2Se3 channel identification | plasmonic_waveguide.md | A valid optical mode fit does not establish a Dirac or surface-state carrier origin | “Which independent ARPES, Hall, ellipsometry, or dispersion evidence identifies the Bi2Se3 channel?” |
| Surface chemistry and photoresponse | bi2se3_material.md, surface_and_composition_characterization.md | Oxidation, thickness, and band bending can change the response before any symmetry fit is interpreted | “Are thickness, oxidation, carrier density, and surface composition controlled for this photocurrent?” |
| Photogalvanic current versus thermal current | parent TI domain | The same angular harmonic can be assigned to different mechanisms | “What helicity, direction, TE/TM, temperature, power, and thermal controls separate the terms?” |

The source packet contains several unexpanded or context-dependent phrases, including angular modulation, scorching heat generation, and generic resonator/photonic-crystal claims. They are retained only as diagnostic guardrails above; they are not asserted as established mechanisms.

## AI Decision-Trigger Checklist for This Sub-Profile

- [ ] User says “Bi2Se3 plasmon” → ask whether the target is Dirac, conventional surface/2DEG, bulk, or a hybrid mode and what dispersion evidence exists.
- [ ] User fits one resonance to surface conductivity → warn about bulk carriers, massive 2DEG, substrate, radiation loss and geometry correlation.
- [ ] User labels a TM signal as SPP → ask for mode profile, dispersion, polarization, confinement and loss evidence.
- [ ] User reports CPGE or LPGE → ask for point group, incidence angle, helicity convention, QWP calibration, direction reversal and thermal controls.
- [ ] User states “CPGE requires oblique incidence” → correct the rule: ideal C3v normal-incidence direct response can be suppressed, but symmetry breaking and geometry change the allowed terms.
- [ ] User fits j(alpha) harmonics → request the angle definition, coefficient convention, power/temperature series and null controls.
- [ ] User reports propagation length → ask whether the number is a field or intensity decay length and how loss channels were separated.
- [ ] User uses a generic RTRR/HPWG sensitivity or Q → route geometry to plasmonic_waveguide and require Bi2Se3-specific optical and carrier calibration.
- [ ] User uses “scorching heat” or “angular modulation” → ask for the source definition before converting the phrase into a physical claim.
