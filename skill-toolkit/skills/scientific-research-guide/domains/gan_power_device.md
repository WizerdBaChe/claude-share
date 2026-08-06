# Domain Profile: Vertical GaN Power Devices

> Scope of applicability: Vertical gallium-nitride power devices, with emphasis on trench MOSFETs, OG-FET/OG-MOSFET variants, CAVETs, field plates, field shields, fabrication, electrical extraction, and TCAD.
> Scientific nature: Wide-bandgap semiconductor electrostatics, transport, interface physics, recombination/trapping, and coupled optical/electrical field analysis.
> Engineering nature: Vertical power-device architecture, process integration, blocking/conduction trade-offs, switching parasitics, TCAD calibration, and measurement conditions.
>
> Profile metadata:
> - Profile ID: gan_power_device.domain.v1
> - Profile version: 1.0
> - Last updated: 2026-08-03
> - Author(s) / Maintainer(s): Scientific Research Guide integration pass
>
> Primary source types:
> - Textbooks: Wide-bandgap semiconductor device and power-electronics textbooks when a canonical definition is needed
> - Review articles: Vertical GaN architecture, materials, and processing reviews
> - Methods / standards papers: Device extraction, breakdown, capacitance, gate-charge, and TCAD methodology papers
> - Other: Primary architecture/process papers; datasheets only for explicitly identified engineering benchmarks
>
> Notes for AI use:
> - Intended use: Route vertical GaN architecture, measurement, fitting, process, and TCAD questions with condition-aware warnings
> - Validation status / usage note: Integrated from the supplied packet and targeted literature; study-specific numbers are not universal ranges

This profile covers vertical GaN power-device reasoning. It is not a general GaN materials profile and it does not replace a lateral HEMT profile. Route a lateral 2DEG HEMT question to a dedicated HEMT profile if one is added later.

## 1. Theoretical Framework Anchoring

### 1.1 Architecture boundary

Vertical devices carry current through the wafer thickness and use a designed drift region to sustain voltage. Lateral HEMTs primarily conduct through a surface or heterointerface channel, often a two-dimensional electron gas. The distinction changes the dominant resistance, electric-field geometry, thermal path, measurement conditions, and failure modes.

The vertical architecture family in scope includes:

| Architecture | Distinguishing structure | Primary question |
|---|---|---|
| Vertical trench MOSFET | Recessed gate in a trench with a vertical drift path | Can the gate/channel and trench dielectric support the target current and voltage? |
| OG-FET or OG-MOSFET | A vertical or regrown channel with an oxide-gated control region; some variants use an in-situ or regrown oxide/channel stack | Is the channel/interface sufficiently low-loss and stable? |
| CAVET | Current aperture, current-blocking layer, vertical drift path, and regrown or buried-gate-related interfaces | Is the aperture, UID layer, aperture doping, gate-overlap length, gate type, or regrowth interface limiting turn-on and dynamic resistance? |
| Field-plate or field-shield variant | Conductive, dielectric, p-type, split-gate, or triple-shield structures redistribute the trench or edge electric field in a RESURF-like design space | Does the field redistribute without creating a new dielectric, capacitance, or process limit? |

For an OG-FET or CAVET design, keep the aperture/current-blocking-layer label, aperture length and doping, gate-overlap length, UID thickness, gate type, and any delta-doping or regrowth-interface treatment as separate variables. These names identify a design parameter set; they do not establish a universal optimum.

Vertical GaN reviews identify high critical field and high saturation velocity as the motivation for vertical architectures, but the realized device is still constrained by defects, interfaces, contacts, substrate, thermal resistance, and processing. See the reviews [Materials and processing issues in vertical GaN power electronics](https://doi.org/10.1016/j.mssp.2017.09.033) and [Vertical GaN MOSFET Power Devices](https://doi.org/10.3390/mi14101937).

### 1.2 Shared physical chain

| Layer of reasoning | Governing idea | Observable or extracted quantity |
|---|---|---|
| Band structure and material | Wide-bandgap GaN sets the available band offsets and field scale; defects and compensation alter the practical carrier population | Band gap, carrier density, compensation, defect-related activation |
| Drift region | Poisson electrostatics and carrier transport determine field spreading, depletion, and voltage blocking | Drift thickness and doping, electric-field profile, breakdown voltage |
| MOS channel and interface | Gate electrostatics, channel mobility, interface traps, and roughness control threshold, on-state loss, and hysteresis | Threshold voltage, channel mobility, interface-trap response, transfer-curve history |
| Trench corner and shield | Geometry concentrates field at corners; dielectric, conductive, or p-type shields redistribute it | Local peak field, dielectric stress, breakdown, capacitance, charge |
| Switching parasitics | Gate-to-drain coupling and output capacitance set the charge and loss required during switching | Cgd, Coss, Qgd, Qoss, gate charge, Miller plateau |
| Regrowth and aperture | Regrowth interfaces, barriers, and space charge can add a turn-on knee that is not the MOS threshold | CAVET turn-on voltage, transient activation, aperture resistance |

### 1.3 Inviolable constraints

1. Breakdown voltage, specific on-resistance, capacitance, and switching loss form a coupled design problem. A field plate or shield cannot be credited with improving all of them without stating the geometry, bias, dielectric, and comparison baseline.
2. A trench bottom corner is a local field problem, not merely a nominal gate-voltage problem. The peak field and dielectric stress must be examined spatially.
3. Channel mobility, threshold stability, and hysteresis are interface- and process-dependent. Geometry alone cannot establish them.
4. A CAVET turn-on knee is not automatically the MOS threshold. Regrowth-interface barriers and space charge can dominate the knee; see [On the origin of the turn-on voltage drop of GaN-based CAVET](https://doi.org/10.1063/5.0079760).
5. A TCAD breakdown value is a model-defined result until mesh convergence, impact-ionization assumptions, boundary conditions, and experimental comparison are documented.
6. RDS(on), Ron,sp, Qgd, and hysteresis are condition-dependent. Report temperature, drain bias, gate bias, current density, pulse width or sweep history, package/contact treatment, and normalization before comparing papers.
7. A process recipe is not portable across crystal orientation, wafer stack, trench profile, dielectric, contact metallurgy, and anneal tool. Copy only a fully traceable recipe with its process window.

### 1.4 Tier-0 confirmation

Before giving a detailed recommendation, identify which path is intended:

- Device architecture: trench MOSFET, OG-FET/OG-MOSFET, CAVET, or a field-termination-only problem.
- Analysis target: blocking/breakdown, conduction/RDS(on), gate charge/switching, dynamic trapping, or process integration.
- Evidence target: analytical scaling, TCAD design study, measured wafer/device data, or reliability qualification.

## 2. Measurement Tool Inventory

| Target | Tool or measurement | Output | Conditions that must travel with the result | Common misuse |
|---|---|---|---|---|
| Trench and field-shield geometry | Cross-sectional SEM, FIB-SEM, TEM, AFM, profilometry | Trench depth, corner radius, dielectric and regrowth geometry, roughness | Cleave/FIB direction, calibration, sampling location, destructive status | Treating a nominal layout dimension as the fabricated corner radius |
| Surface and composition | XPS, EDS, SIMS or related depth-sensitive analysis | Elemental composition, contamination, oxidation, dopant profile | Sputter energy, calibration, depth resolution, surface preparation | Calling a surface signal a bulk concentration |
| Epitaxy and regrowth | XRD, TEM, Raman, defect mapping, cross-sectional microscopy | Crystal quality, strain, interface and defect evidence | Wafer position, orientation, film thickness, mapping area | Inferring interface trap density from a single structural image |
| DC transfer and output | Gate-voltage sweep, drain-voltage sweep, pulsed I-V where appropriate | Vth, transconductance, current density, on-state resistance, leakage | VDS, VGS range, sweep rate, temperature, compliance, hysteresis direction | Comparing Vth extracted with different conventions or drain biases |
| Low-resistance extraction | Kelvin or four-terminal structures; de-embedded package/contact measurement | Source, channel, accumulation/access, JFET or aperture, drift, substrate, contact, package, and total resistance components | Geometry, current level, temperature, contact and package de-embedding | Reporting one slope as intrinsic channel resistance |
| Carrier and interface response | Hall, C-V, charge pumping or other validated interface method | Carrier density, mobility, capacitance, trap response | Frequency, amplitude, geometry, temperature, model assumptions | Treating Hall mobility as MOS channel mobility |
| Blocking and breakdown | Quasi-static or pulsed breakdown, leakage, avalanche-current monitoring | VBD, leakage, failure mode, avalanche onset | Current criterion, ramp rate, temperature, compliance, destructive/non-destructive status | Equating simulated avalanche onset with catastrophic measured breakdown |
| Gate charge and capacitance | Double-pulse or standardized gate-charge measurement; impedance or C-V analysis | Qg, Qgs, Qgd, Cgd, Coss, Qoss, Miller plateau | VDS, VGS limits, gate current, temperature, frequency, fixture | Comparing Qgd without matching voltage and gate-current conditions |
| Dynamic trapping | Pulsed I-V, double-pulse, drain-current recovery, gate-bias history | Dynamic RON, current collapse, recovery time | Pulse width, duty cycle, quiescent bias, delay, temperature | Calling a dynamic increase an intrinsic DC resistance |
| Thermal behavior | Infrared, Raman thermometry, calibrated thermal test, electrothermal extraction | Junction or surface temperature, thermal resistance, drift | Emissivity/calibration, boundary conditions, duty cycle, heat sinking | Attributing temperature-driven drift to a field-plate mechanism |

## 3. Standard Modeling Toolchain

### 3.1 Modeling chain

~~~text
material and epitaxy
    -> process cross-section and mesh
    -> electrostatics and transport
    -> field, current, capacitance, and breakdown extraction
    -> mixed-mode or electrothermal switching analysis
    -> fabricated-device measurement and model calibration
~~~

| Stage | Minimum inputs | Useful outputs | Boundary condition |
|---|---|---|---|
| Material/epitaxy | Layer thicknesses, doping/compensation, contacts, defect assumptions | Band diagram, carrier profile, nominal material parameters | Do not use nominal doping as measured active carrier density |
| Process cross-section | Trench shape, corner radius, dielectric, shield, regrowth and contact geometry | Meshed device and process sensitivities | Mesh the field-concentrating corner and interface explicitly |
| DC device TCAD | Mobility, recombination, traps, impact-ionization and boundary models | Transfer/output curves, field map, RON, VBD | Record model names, parameters, convergence and bias path |
| Switching or mixed-mode | Gate resistance/current, circuit parasitics, C(V), temperature model | Gate charge, Miller behavior, switching loss, overshoot | A device-only result is not a packaged switching result |
| Calibration | Measured I-V, C-V, gate charge, pulse response, temperature | Calibrated parameters and residuals | Calibrate multiple observables; do not fit one curve and call the model validated |

Sentaurus Device or an equivalent drift-diffusion TCAD platform is suitable for baseline Poisson/continuity analysis. Hydrodynamic, Monte Carlo, quantum, or tunneling models are extensions, not automatic upgrades. Avalanche output should be reported with the selected impact-ionization model, local field quantity, mesh resolution, and the current or field criterion used to define onset.

For reproducibility, preserve the tool version, mesh controls, material parameter file, bias sweep, solver tolerances, and exported field/current data. File extensions such as TDR or PLT are tool-specific implementation details, not evidence by themselves.

### 3.2 Process flow and process-packet boundary

A common conceptual sequence is mesa isolation, trench definition, sidewall and bottom treatment, dielectric or regrowth formation, contact and via definition, source/drain and gate or field-plate metallization, and passivation. The actual sequence and thermal budget must be taken from the cited process paper.

The supplied packet mentions Cl-based ICP/RIE, wet treatment such as TMAH, ALD Al2O3 or HfO2, Ti/Al/Ni/Au-style contacts, high-temperature annealing, SiNx passivation, and gate/field-plate metal. These remain process examples rather than defaults because the packet did not preserve a traceable primary citation and the values are stack- and orientation-dependent. Do not present them as a universal recipe.

For shielded trench designs, preserve the actual conductive and dielectric topology. A triple-shield BPSG-MOS example in the packet combines a grounded split gate, a P+ shield, and a semi-wrapped BPSG structure; its reported capacitance or charge reduction is a design-case result, not a general rule.

## 4. Domain-Specific Fitting Methods

| Method | Applicable question | Assumptions and required conditions | Common error | Correct practice |
|---|---|---|---|---|
| Linear-extrapolation Vth | Operational threshold from a chosen transfer-curve regime | State VDS, temperature, sweep direction, current normalization, and linear window | Calling the intercept a material constant or comparing different windows | Report the convention and verify with hysteresis and a second extraction if threshold stability matters |
| Low-VDS slope or Kelvin RON | On-state resistance under a defined operating point | Separate channel, drift, contact, access, and package terms where possible | Treating total terminal slope as intrinsic channel resistance | Use Kelvin/de-embedded structures or provide a resistance budget |
| Gate-charge segmentation | Qgs, Qgd, Miller plateau and switching energy | Fixed VDS, gate current or gate resistance, VGS limits, temperature, fixture | Comparing Qgd with different drain voltages or gate currents | Show the full Qg curve and annotate the integration boundaries |
| C(V) and Qoss extraction | Output charge and capacitance for switching design | Frequency, AC amplitude, DC bias, fixture and loss model | Assuming a single constant Coss or ignoring frequency dependence | Use a bias-dependent curve and integrate over the actual switching voltage |
| TCAD avalanche-onset extraction | Model-defined onset or breakdown criterion | Mesh convergence, impact model, field variable, current criterion, bias path | Treating avalanche-current onset as measured destructive BV | Name the criterion and cross-check with a measured breakdown or a second model |
| CAVET turn-on-knee analysis | Separating aperture/interface activation from channel threshold | Transient or temperature dependence and an interface/barrier model | Calling the knee a gate Vth | Fit or compare the interface contribution explicitly; see the CAVET study cited above |
| Hysteresis analysis | Trap, polarization, leakage, or dielectric-history response | Bidirectional sweep, dwell time, temperature, pre-bias and recovery time | Assigning all hysteresis to one defect class | Report the full history protocol and compare with pulsed and temperature-dependent data |

## 5. Domain-Specific Quality Metrics

The following values are study-specific anchors, not universal acceptance bands:

| Metric | How to report it | Anchored examples or range status | Suspicious comparison |
|---|---|---|---|
| Breakdown voltage VBD | Voltage criterion, leakage/current limit, ramp, temperature, destructive status | A 1.3 kV vertical trench MOSFET study reported VTH = 3.15 V, RON,sp = 1.93 mOhm cm2, and BV = 1306 V under its own structure and test conditions: [study](https://doi.org/10.1186/s11671-022-03653-z). | Calling 334 V, 1.3 kV, and multi-kV devices one performance range without architecture and substrate |
| Specific on-resistance RON,sp | Area definition, current density, VGS, VDS, temperature, Kelvin/package treatment | The 1.3 kV study above is a device-case value, not a typical target. | Comparing a simulated drift-only value with a measured total value |
| Baliga-type figure of merit | State formula and whether RON,sp includes all terms | The supplied packet's 0.88 GW/cm2 value follows from the cited 1.3 kV case; treat it as a calculated case result. | Comparing different voltage and resistance definitions |
| Threshold voltage VTH | Extraction convention, drain bias, sweep and temperature | 3.15 V in the cited 1.3 kV study and 5 V in one later fully vertical device report are architecture-specific examples, not a universal window. | Mixing enhancement-mode threshold definitions |
| Qgd, Cgd, Qoss and Coss | Voltage interval, gate current/frequency, fixture and temperature | A triple-shield BPSG-MOS design reports a case-specific Cgd reduction and Qgd value; use the paper's exact conditions: [study](https://doi.org/10.1038/s41598-024-84007-w). | Treating simulated charge reduction as a measured switching guarantee |
| Peak dielectric or shield field | Spatial maximum, dielectric thickness, bias, mesh and model | A buried-field-shield study discusses a simulated dielectric-field limit below about 4 MV/cm and a geometry-dependent value near 5 MV/cm; these are study-specific design observations: [study](https://doi.org/10.1016/j.prime.2023.100218). | Using the number as a GaN dielectric universal limit |
| Dynamic RON or hysteresis | Ratio or delta relative to a stated DC reference, with pulse history | No universal range is accepted here; report the complete pulse and recovery protocol. | Comparing values from different quiescent biases |

Do not invent a single “good GaN” range when the supplied sources and verified literature support only study-specific examples. For a new device, report the full conditions first and classify the metric as application target, model result, wafer result, or packaged-device result.

## 6. Common Assumption Pitfalls

| Pitfall | Trigger | Why it fails | Recovery |
|---|---|---|---|
| Vertical/lateral category error | User compares a vertical trench MOSFET directly with a lateral 2DEG HEMT | The current path, drift region, capacitance, and thermal path are different | Split the comparison by architecture and normalize only after defining the metric |
| Field plate treated as a free improvement | User claims a field plate raises BV and lowers RON without a geometry or capacitance budget | Field redistribution trades against dielectric stress, area, capacitance, and process complexity | Request the field map, shield bias, dielectric, C(V), and baseline |
| Trench corner omitted | Mesh or layout uses nominal trench dimensions only | The local corner field can dominate dielectric stress and breakdown | Add corner-radius sensitivity and a locally refined mesh |
| TBD acronym expanded by guess | Notes use TBD without the original legend | TBD can be a project placeholder; one recent paper uses it for thick bottom dielectric | Preserve the ambiguity and cite the source context before expanding it. See [Analysis and Manufacturing of GaN Trench-Gate MOSFETs with Thick Bottom Dielectric](https://doi.org/10.1002/pssa.202400804) |
| Process recipe generalized | User copies RIE, wet treatment, ALD, contact, or anneal conditions to another stack | Orientation, sidewall chemistry, dielectric, and contact activation change the result | Require a traceable recipe and report the full process window |
| Single I-V slope called intrinsic RON | Only two-terminal output data are available | Contact, access, drift, and package terms may dominate | Use Kelvin/de-embedding or publish a resistance budget |
| Qgd compared without Miller conditions | Gate charge is quoted without VDS, gate current, or fixture | Qgd is bias- and measurement-dependent | Re-measure or replot under matched conditions |
| TCAD breakdown overclaimed | A single avalanche simulation is presented as device BV | Model, mesh, boundary and criterion uncertainty can be large | Run convergence and sensitivity checks; compare with measured or independently modeled behavior |
| CAVET knee called threshold | Turn-on voltage is inferred from a drain-current knee | Regrowth interface barriers and space charge can produce the knee | Separate MOS threshold from aperture/interface activation |
| Hysteresis assigned to one trap | Forward/backward VGS curves differ and the cause is declared | Traps, polarization, leakage, dielectric history and temperature can overlap | Vary sweep history, temperature, pulse timing and pre-bias |
| Study metric turned into a typical range | A single high-voltage or low-resistance result is repeated as a target | The result may be a simulation, a special wafer, or a different normalization | Label it as a case result and preserve architecture and conditions |

## 7. Literature Anchors

1. Langpoklakpam et al., “Vertical GaN MOSFET Power Devices,” *Micromachines* 14, 1937 (2023). [DOI](https://doi.org/10.3390/mi14101937)
2. Meneghini et al., “Materials and processing issues in vertical GaN power electronics,” *Materials Science in Semiconductor Processing* 78 (2018). [DOI](https://doi.org/10.1016/j.mssp.2017.09.033)
3. “1.3 kV Vertical GaN-Based Trench MOSFETs on 4-Inch Free Standing GaN Wafer,” *Nanoscale Research Letters* 17, 14 (2022). [DOI](https://doi.org/10.1186/s11671-022-03653-z)
4. “Gate protection for vertical gallium nitride trench MOSFETs: The buried field shield,” *e-Prime* 5 (2023). [DOI](https://doi.org/10.1016/j.prime.2023.100218)
5. “On the origin of the turn-on voltage drop of GaN-based CAVET,” *Journal of Applied Physics* 131, 114502 (2022). [DOI](https://doi.org/10.1063/5.0079760)

## Cross-Domain Links

### Closest Related Domain Profiles

| Related profile | Link | Boundary |
|---|---|---|
| Topological insulator / Bi2Se3 material | Use for defect, thickness, surface-state, transport, and multi-channel reasoning | Do not import TI surface-state assumptions into GaN MOS electrostatics |
| MicroLED | Shared GaN fabrication vocabulary and possible TCAD/process tools | MicroLED quality is dominated by recombination, extraction and optical metrics, not power-device blocking |
| Plasmonic waveguide | Shared electric-field and capacitance vocabulary in optical structures | SPP loss and optical mode fitting are not a substitute for power-device breakdown analysis |

### Cross-Domain Conflict Notes

| Issue / constraint | Other profile(s) involved | Potential conflict | AI confirmation question |
|---|---|---|---|
| Same GaN or RIE vocabulary, different quality metrics | microled.md | A fabrication change may be judged by RON/BV in one profile and EQE/SRV in the other | “Are we evaluating a power-device blocking/conduction target or a recombination/optical pixel target?” |
| Surface field language reused across optics and power devices | plasmonic_waveguide.md | Optical mode confinement and SPP loss do not establish semiconductor breakdown or dielectric reliability | “Is the field quantity optical and time-harmonic, or a DC/pulsed power-device blocking field?” |
| Bi2Se3 surface-state assumptions imported into GaN | topological_insulator/bi2se3_material.md | A topological surface state is not a MOS interface channel | “Is this a GaN interface/trap problem or a TI band-topology problem?” |

The current profile intentionally does not add a lateral HEMT branch, a full reliability qualification protocol, or a universal process recipe. Those are separate expansions with different evidence requirements.

## AI Decision-Trigger Checklist for This Profile

- [ ] User says “GaN power device” without architecture → ask whether the device is vertical trench MOSFET, OG-FET/OG-MOSFET, CAVET, lateral HEMT, or diode.
- [ ] User compares vertical and lateral devices → warn that current path, drift region, capacitance and thermal boundary differ before any metric comparison.
- [ ] User claims a field plate or shield improves BV and RON simultaneously → request geometry, shield bias, dielectric, field map, capacitance and baseline.
- [ ] User gives a trench TCAD breakdown result → ask for mesh convergence, impact-ionization model, field criterion, leakage/current criterion and experimental comparison.
- [ ] User reports VTH from a transfer curve → request VDS, temperature, sweep direction, current criterion and extraction window.
- [ ] User reports RON or RON,sp → request current density, VGS, VDS, temperature, area definition and contact/package treatment.
- [ ] User reports Qgd or Qoss → request voltage interval, gate current/frequency, fixture, temperature and full charge curve.
- [ ] User uses “TBD” in a trench design → preserve the abbreviation until the original legend or cited paper is identified.
- [ ] User explains a CAVET turn-on knee as MOS threshold → separate gate threshold from aperture/regrowth-interface activation.
- [ ] User presents a process recipe → ask for wafer orientation, stack, etch chemistry, sidewall treatment, dielectric, contact stack, anneal window and source.
