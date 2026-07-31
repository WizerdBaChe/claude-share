# Reference: Plasmonic Terminology and Waveguide Geometry

> Parent domain: `plasmonic_waveguide.md`
> Type: reference; load only for terminology, geometry classification, or loss-accounting questions.
> Role: normalize the chaptered notes without creating standing triggers.

## Terminology map

| Term | Use | Do not infer |
|---|---|---|
| Surface plasmon (SP) | Broad label for collective charge oscillations associated with a surface. | Do not use it as a precise substitute for SPP or LSP when propagation matters. |
| Surface plasmon polariton (SPP) | A propagating, interface-bound electromagnetic/material mode. For a simple planar interface it is TM-polarized and decays away from the interface. | A bright spectral dip alone does not prove that an SPP was launched. |
| Surface plasmon resonance (SPR) | A resonance or measurement condition used to excite a surface-plasmon mode; state the geometry (for example prism or grating coupling). | Do not treat SPR as a unique mode name independent of the experiment. |
| Localized surface plasmon (LSP) | A spatially confined plasmonic eigenmode of a finite structure. | Do not assign a propagation length as if it were an SPP waveguide mode. |
| Localized surface plasmon resonance (LSPR) | The resonant optical response associated with an LSP. | Do not collapse the mode (LSP) and the observed resonance (LSPR) when fitting spectra. |
| Localized surface plasmon polariton (LSPP) | Non-uniform terminology used by some authors. | Preserve the source author's definition; do not introduce this abbreviation as a preferred synonym. |
| LSRR | Unresolved abbreviation in the supplied notes. | Do not expand it to “L-shaped SRR,” “left-handed SRR,” or another form without the source figure, caption, or explicit expansion. |

## Geometry map

| Geometry | Shared physical picture | Primary trade-off |
|---|---|---|
| Insulator-metal-insulator (IMI) | A finite metal film between dielectric regions; coupled interface modes may support a long-range branch when the stack is sufficiently symmetric. | Reduced attenuation generally comes with weaker confinement and sensitivity to asymmetry. |
| Metal-insulator-metal (MIM) | A dielectric gap between metal regions; the gap mode can be deeply confined. | Strong metal overlap increases absorption and fabrication sensitivity. |
| Hybrid plasmonic waveguide (HPW) | A dielectric guided mode hybridizes with an SPP across a low-index nanoscale gap. | Confinement, propagation distance, and fabrication tolerance must be optimized together. |

Treat `MIN` in the supplied notes as a probable transposition of `MIM`, but ask for the
original figure or layer stack before silently correcting a manuscript or dataset.

## Classification and loss accounting

- Call a structure plasmonic only after identifying the carrier response and an
  SPP/LSP-like mode. A literal noble-metal layer is not mandatory: conducting oxides,
  doped semiconductors, graphene, and other materials can be plasmonic in an appropriate
  frequency range.
- A metal-containing structure is not automatically a plasmonic waveguide. Confirm that
  the reported mode is interface-bound and that the material model supports the claimed
  response at the operating frequency.
- Treat `Au film` and `Au grating` as material/geometry descriptions, not mode names.
  For a film, state the thickness and both adjacent media; for a grating, distinguish
  momentum coupling, a localized resonance, and a propagating mode using fields,
  dispersion, polarization, or angle dependence.
- Separate coupling loss from propagation loss. Use multiple lengths or an equivalent
  calibrated de-embedding method; a single insertion-loss value cannot identify the two
  contributions.
- State whether propagation length refers to field-amplitude or power/intensity decay.
  These conventions differ by a factor of two.
- Route bias-tunable graphene, ITO/ENZ, or topological-insulator devices to
  `active_modulation.md`.
- Route SRR/LSRR/metamaterial questions to `split_ring_resonators.md`.

## Evidence anchors

- Oulton et al., “A hybrid plasmonic waveguide for subwavelength confinement and
  long-range propagation,” *Nature Photonics* 2, 496–500 (2008).
  DOI: https://doi.org/10.1038/nphoton.2008.131
- Berini, “Long-range surface plasmon polaritons,” *Advances in Optics and Photonics*
  1, 484–588 (2009). DOI: https://doi.org/10.1364/AOP.1.000484
- Maier, *Plasmonics: Fundamentals and Applications* (Springer, 2007).
  DOI: https://doi.org/10.1007/0-387-37825-1
