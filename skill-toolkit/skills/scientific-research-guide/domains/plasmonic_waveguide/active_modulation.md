# Sub-profile: Active Plasmonic Modulation — under Plasmonic Waveguide

> Parent domain: `plasmonic_waveguide.md`
> Branch axis: method / material platform
> Scope: electrically or optically tunable graphene, conducting-oxide/ENZ, and
> topological-insulator plasmonic waveguides or resonators.
> Inherits from parent: Nodes 1–3 unless overridden below.

## 4. Branch-Specific Modeling and Fitting

### Bias-to-spectrum chain

**Applicable conditions**: a device reports voltage-dependent effective index, loss,
resonance position, or transmission.

**Common error**: ⚠️ fitting spectral displacement directly against voltage and naming
one microscopic mechanism without validating the intermediate material response.

**Correct approach**: validate the chain in order:

```
electrical/optical drive
→ carrier and temperature distribution
→ complex material response versus frequency
→ complex modal index and overlap
→ finite-device spectrum
```

Report which links were measured, which were simulated, and which were assumed. Fit the
complex response, not only the resonance wavelength.

## 5. Branch-Specific Quality Metrics

| Metric | Physical meaning | Required context |
|---|---|---|
| Extinction ratio | On/off transmission contrast | Device length, wavelength, polarization, and drive condition |
| Insertion loss | Loss in the transmitting state | Coupler de-embedding and reference device |
| Modulation efficiency | Optical change per drive or length | Exact definition and electrical boundary conditions |
| Energy per bit / capacitance | Electrical switching cost | Drive waveform, device capacitance, resistance, and bandwidth |
| Spectral shift | Drive-induced resonance displacement | Thermal drift, hysteresis, linewidth, and uncertainty |
| Complex effective-index change | Phase and attenuation response | Material model, mode normalization, and overlap |

Do not provide a universal “typical range” for these metrics: platform, wavelength,
device length, resonance quality factor, and drive convention change the comparison.

## 6. Branch-Specific Assumption Pitfalls

| Pitfall | Trigger condition | How to recognize it | Correct approach |
|---|---|---|---|
| Treating ENZ as loss-free index enhancement | User says only that `Re(ε) ≈ 0` | Imaginary permittivity and field overlap are omitted | Use measured complex permittivity and report the absorption/confinement trade-off |
| Assuming accumulation, depletion, and injection are interchangeable | Bias changes an ITO or semiconductor device | No electrostatic stack or carrier profile is given | Confirm polarity, contacts, oxide, equilibrium carrier density, and the solved carrier distribution |
| Assigning every spectral shift to free carriers | Resonance moves with bias or pump | Temperature, charging, trapping, and hysteresis were not checked | Use controls or time/voltage sweeps that separate thermal, electrostatic, and trap-mediated effects |
| Reusing bulk ITO data for a fabricated film | ENZ wavelength is taken from a generic table | Deposition, anneal, and carrier density are unreported | Measure the actual film or use a process-matched optical/electrical dataset |
| Ignoring active-layer overlap | Large material-index change is claimed to guarantee large device modulation | Mode overlap is absent | Compute the complex modal response with the actual layer thickness and geometry |
| Attributing Bi₂Se₃ response solely to topological surface states | A TI device is called a “topological modulator” | Bulk carriers, 2DEG states, and optical phonons are omitted | Fit or constrain all plausible carrier and phonon contributions with transport/spectroscopy |
| Treating graphene gating as a scalar refractive-index change | Graphene is inserted into a 3D bulk-material solver | Surface conductivity and Fermi-level dependence are absent | Use an appropriate sheet-conductivity model and verify the scattering rate and gating regime |
| Ignoring electrical parasitics | Optical simulation alone is used to claim speed or energy | RC parameters and contacts are absent | Separate optical modulation depth from electrical bandwidth and switching-energy evidence |

## AI Decision-Trigger Checklist for This Sub-profile

- [ ] User reports an ENZ device using only `Re(ε)` → ask for `Im(ε)`, film provenance,
      wavelength, and the active-mode overlap.
- [ ] User reports a bias-induced spectral displacement → ask which thermal, trapping,
      electrostatic, and carrier controls were performed.
- [ ] User calls a Bi₂Se₃ modulation signal a topological-surface-state response → ask
      how bulk carriers, 2DEG states, and phonons were excluded.
- [ ] User compares graphene, ITO, and TI modulators → ask for the governing wavelength,
      drive mechanism, and whether the priority is loss, footprint, bandwidth, or energy.
- [ ] User quotes extinction ratio without device length and insertion loss → request
      both before comparing platforms.
- [ ] User predicts speed or energy from an optical-only model → require an electrical
      equivalent circuit or measurement.

## Evidence Anchors

- Oulton et al., *Nature Photonics* (2008), hybrid plasmonic geometry.
  DOI: https://doi.org/10.1038/nphoton.2008.131
- Ansell et al., “Hybrid graphene–plasmonic waveguide modulators,”
  *Nature Communications* 6, 8846 (2015). DOI: https://doi.org/10.1038/ncomms9846
- Swillam et al., “On chip optical modulator using epsilon-near-zero hybrid plasmonic
  platform,” *Scientific Reports* 9, 6669 (2019).
  DOI: https://doi.org/10.1038/s41598-019-42675-z
- Chen et al., “Real-space nanoimaging of THz polaritons in the topological insulator
  Bi₂Se₃,” *Nature Communications* 13, 1374 (2022).
  DOI: https://doi.org/10.1038/s41467-022-28791-x
