# Boundary Note: Split-Ring Resonators and Plasmonic Waveguides

> Parent domain: `plasmonic_waveguide.md`
> Type: boundary; load only when SRR, split-ring, LSRR, negative-index, or
> metamaterial terminology is explicit.
> Boundary: standalone SRR arrays are electromagnetic metamaterials or metasurfaces,
> not plasmonic waveguides merely because they contain metal.

## What can be retained from the supplied notes

- A split-ring resonator (SRR) is a subwavelength resonant element whose lowest-order
  behavior is often interpreted with an effective inductive-capacitive model.
- Geometry, material dispersion, loss, substrate, polarization, incidence angle, and
  coupling to neighboring resonators all affect the observed resonance.
- At optical and near-infrared frequencies, metallic SRRs support plasmonic current and
  charge modes. The circuit analogy becomes approximate because kinetic inductance,
  retardation, multipoles, bianisotropy, and material dispersion become important.
- SRRs can be placed in or near a guiding structure, but this does not make an SRR array
  equivalent to an IMI, MIM, or hybrid plasmonic waveguide.

## Corrections and boundary rules

1. **Do not expand `LSRR` without provenance.** It can denote different geometries or
   handedness conventions in different sources. Require the source's caption, diagram,
   or explicit definition.
2. **Do not equate an optical SRR resonance with generic LSPR.** Plasmonic language can
   be appropriate, but magnetic, electric, multipolar, and magnetoelectric responses
   must be identified from currents, charges, fields, symmetry, or parameter retrieval.
3. **Do not infer a negative refractive index from a transmission peak.** Verify phase
   dispersion or perform a causal effective-parameter retrieval; anisotropy and
   bianisotropy can invalidate a scalar `ε`/`μ` interpretation.
4. **Do not state that one SRR always supplies only negative permeability.** The
   electric and magnetic responses depend on geometry, orientation, coupling, and
   homogenization regime.
5. **Do not transfer microwave LC scaling unchanged to optical dimensions.** Use the
   actual dispersive material model and test whether homogenization remains valid.
6. **Do not use `n = -1` or “perfect lens” language as a device conclusion without**
   loss, bandwidth, impedance, spatial-dispersion, and finite-size evidence.

## Where to route the research question

- Route modal propagation, coupling loss, or IMI/MIM/HPW design back to
  `plasmonic_waveguide.md`.
- Route an SRR array's effective constitutive response, negative refraction, or
  metasurface retrieval to a future electromagnetic-metamaterial base profile.
- Route an optical SRR used only as a finite plasmonic resonator to a future
  plasmonic-resonator profile if that branch develops its own metrics and fitting rules.

## Evidence anchors

- Pendry et al., “Magnetism from conductors and enhanced nonlinear phenomena,”
  *IEEE Transactions on Microwave Theory and Techniques* 47, 2075–2084 (1999).
  DOI: https://doi.org/10.1109/22.798002
- Smith et al., “Composite medium with simultaneously negative permeability and
  permittivity,” *Physical Review Letters* 84, 4184–4187 (2000).
  DOI: https://doi.org/10.1103/PhysRevLett.84.4184
- Woodley et al., “Left-handed and right-handed metamaterials composed of split ring
  resonators and strip wires,” *Physical Review E* 71, 066605 (2005).
  DOI: https://doi.org/10.1103/PhysRevE.71.066605
- Seetharaman et al., “Electromagnetic interactions in a pair of coupled split-ring
  resonators,” *Physical Review B* 96, 085426 (2017).
  DOI: https://doi.org/10.1103/PhysRevB.96.085426
