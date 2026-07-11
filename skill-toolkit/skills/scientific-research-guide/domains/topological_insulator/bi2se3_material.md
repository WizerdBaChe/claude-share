# Sub-Profile: Bi₂Se₃ Material Branch (Bi₂Se₃-based topological insulator)

> Parent Domain: Topological Insulator(拓撲絕緣體, topological insulator, TI)
>
> Scope of applicability:
> - Material-scoped sub-profile for Bi₂Se₃(三硒化二鉍, bismuth selenide, Bi₂Se₃) and closely related Bi₂Se₃-based compounds.
> - Active only when the user is explicitly working with Bi₂Se₃ crystals, thin films, nanosheets, or Bi₂Se₃-derived alloys/intercalates.
>
> Scientific nature:
> - Focuses on how Bi₂Se₃ realizes the TI band topology (single surface Dirac cone, band inversion at Γ) and how its defects, chemistry, and thickness tune that topology.
>
> Engineering nature:
> - Provides Bi₂Se₃-specific traps for transport, ARPES, growth, and surface chemistry (e.g. bulk conduction from Se vacancies, aging/oxidation), beyond the parent TI profile’s generic guidance.

---

## Node 1. Localized Theoretical Anchoring (relative to the parent TI profile)

> This node reuses the parent domain’s first principles and only highlights what is *special* or *non-generic* for Bi₂Se₃.

- Bi₂Se₃ is a prototypical 3D strong topological insulator(三維強拓撲絕緣體, three-dimensional strong topological insulator) with:
  - a relatively large bulk band gap (~0.2–0.3 eV) compared to many other TI;
  - a *single* Dirac cone(單一狄拉克錐, single Dirac cone) on each surface, centred at the Γ point.
- Its tetradymite-type structure consists of stacked 五原子層(quintuple layers, QLs) Se₁–Bi–Se₂–Bi–Se₁ along the c-axis, separated by 范德華間隙(van der Waals gaps).
- First-principles calculations show band inversion at Γ due to strong 自旋–軌道耦合(spin–orbit coupling, SOC), driving a non-trivial Z₂ topology; Sb₂Se₃ in the same family is trivial and used as a reference.
- Spin- and angle-resolved ARPES (SARPES) confirm 自旋–動量鎖定(spin–momentum locking) with near-unit intrinsic spin polarization in the topological surface state, limited experimentally by overlap with bulk bands and instrumental resolution.

**Local inviolable constraints (Bi₂Se₃-specific additions)**

1. Bi₂Se₃’s “ideal TI” description (single Dirac cone + insulating bulk) only holds when carrier densities are low and defects are controlled; many real samples are strongly n-type metallic due to Se vacancies and must *not* be treated as bulk insulators without evidence.
2. In ultrathin Bi₂Se₃ films (thickness ≲ 6 QL), top and bottom surface states hybridize and open a gap at the Dirac point; edge/surface transport must account for this thickness-dependent gap and possible Rashba-type splitting.
3. Bi₂Se₃ surface chemistry is relatively inert but not immune: long exposure and certain dopants/intercalants (e.g. Cu) cause oxidation and composition gradients that can strongly distort ARPES and transport signatures if not controlled.
4. Ternary derivatives such as Bi₂Se₂S can be topologically trivial; extrapolating Bi₂Se₃’s TI behaviour to all Se-based Bi compounds is invalid.

---

## Node 2. Local Measurement & Preparation Rules

> This node narrows the parent TI measurement inventory down to Bi₂Se₃-specific usage patterns and preparation requirements.

### 2.1 Sample growth and preparation

- Single crystals:
  - Grown typically by Bridgman or self-flux methods; Se stoichiometry and cool-down protocols strongly affect defect concentrations and bulk carrier density.
  - For ARPES and transport, crystals should be cleaved along the (111)-like QL plane, ideally *in situ* under UHV to minimize oxidation and band bending.
- Thin films:
  - MBE growth on sapphire(0001), graphene/SiC, Ge(111), and other substrates enables thickness control down to a few QL and smooth surfaces suitable for quantum transport.
  - Growth temperature, Se/Bi flux ratio, and post-growth annealing affect film roughness, QL stacking quality, and Se vacancy density.

**Local pitfalls (preparation)**

- Cleaving Bi₂Se₃ in air and later loading into UHV is sometimes acceptable for qualitative band mapping, but can shift band positions and broaden surface states; high-precision spin-texture or gap measurements require *in situ* UHV cleaving or passivation protocols.
- On conductive substrates (e.g. doped Ge, heavily doped Si), substrate conduction may contaminate Bi₂Se₃ transport unless the substrate doping and geometry are chosen to suppress leakage in the measurement window.

### 2.2 ARPES and SARPES on Bi₂Se₃

- Goals:
  - Resolve the single Dirac cone and its spin texture.
  - Separate surface states from bulk bands and quantum well states in ultrathin films.
- Conditions:
  - UHV better than ~10⁻¹⁰ mbar; controlled photon energy to maximize surface sensitivity.
  - For thin films, photon energy and incidence geometry must be chosen to distinguish QW subbands from true surface states.

**Local misuse**

- Misidentifying quantum well subbands in Bi₂Se₃ thin films as “additional Dirac cones” without thickness-dependent or photon-energy-dependent analysis.
- Interpreting ARPES spectra after heavy Cu intercalation or long-term ambient exposure as if they were pristine Bi₂Se₃, ignoring near-surface composition changes.

### 2.3 Transport and magnetotransport on Bi₂Se₃

- DC transport:
  - Temperature-dependent resistivity and Hall measurements reveal whether the sample is bulk metallic (n-type) or closer to bulk insulating, and help quantify bulk vs surface conduction.
- Quantum transport:
  - Low-temperature magnetoconductivity often shows WAL signatures that can be fitted with HLN-type models, but Bi₂Se₃ generally has multi-channel transport (bulk + surface + possible 2D subbands).
- Thickness and dimensional crossover:
  - Films approaching ~6 nm show a crossover from 3D-like to 2D-like transport, two-dimensional localization, and WAL; thinner films may exhibit WL due to gap opening and electron–electron interactions.

**Local misuse**

- Treating WAL observed in thick, bulk-conducting Bi₂Se₃ films as “pure surface WAL” without modelling bulk channels; WAL can arise from bulk SOC and 2D bulk subbands as well.
- Ignoring substrate and interface contributions (e.g. Ge conduction, interface states) in Bi₂Se₃/semiconductor heterostructure magnetotransport.

---

## Node 3. Local Modeling & Toolchain Hooks

> This node shows how Bi₂Se₃ hooks into the parent TI modeling toolchain and where Bi₂Se₃-specific parameters or models are needed.

- First-principles:
  - DFT (possibly with hybrid functionals) for bulk Bi₂Se₃, including SOC, to obtain accurate band gaps, band inversion at Γ, and parity eigenvalues for Z₂ indices.
  - Ab initio simulations of Bi₂Se₃ surfaces and slabs to capture surface-state dispersion and Rashba splitting in thin films.
- Effective models:
  - k·p Dirac Hamiltonians fitted specifically to Bi₂Se₃ band parameters (mass term, velocities, SOC strength).
  - Tight-binding models incorporating QL stacking and van der Waals gaps to simulate thickness-dependent hybridization and quantum well states.
- Transport and fitting:
  - Multi-channel HLN-type magnetoconductivity models combining WAL from surface/2D channels and WL/WAL from bulk channels.
  - Thickness- and substrate-dependent transport simulations to separate Bi₂Se₃ contributions from substrate leakage and interface states.

---

## Node 4. Bi₂Se₃-Specific Fitting Methods & Traps

> This node defines *named* fitting workflows where Bi₂Se₃ behaves differently from a generic TI and where the AI should auto-warn.

### 4.1 Multi-channel HLN fitting in Bi₂Se₃ films

**Applicable conditions**:  
- Bi₂Se₃ thin films with thickness in the few–tens of QL regime, showing WAL/WL features but known (from Hall and resistivity) to have both bulk and surface conduction.

**Common errors**: ⚠️  
- Using a single-channel HLN fit with a single α and Lϕ for all fields and temperatures, then over-interpreting α as “number of surface channels” while ignoring bulk.  
- Fitting over a too-wide field range where classical MR, Zeeman effects, or higher-order quantum corrections become significant, making HLN invalid.

**Correct approach**:  
- Restrict HLN fits to the low-field window where quantum interference dominates; treat α and Lϕ as field-range- and temperature-dependent, and cross-check with thickness and carrier-density trends.  
- Use multi-channel models (surface WAL + bulk WL/WAL) where α is decomposed into contributions, and validate the decomposition by comparing with thickness series and composition series (e.g. Bi₂TeₓSe₃₋ₓ).  

**AI trigger example**:  
> User says: “I fitted Bi₂Se₃ film magnetoresistance with HLN and got α ≈ −1.”  
> AI should ask: “Did you verify whether multiple channels (bulk + surface + 2D subbands) are contributing, and did you restrict the fit to the low-field WAL regime?”

### 4.2 Thickness-dependent gap & quantum well state analysis

**Applicable conditions**:  
- Bi₂Se₃ films with thickness ≤ ~6 QL, ARPES or transport hints of gap opening or Rashba splitting.

**Common errors**: ⚠️  
- Interpreting gap opening purely as “destroyed topology” without considering coupled surface states or substrate-induced inversion symmetry breaking.  
- Confusing QW subbands with extra Dirac cones or “second TI surface” without a thickness series or band-structure modelling.

**Correct approach**:  
- Use slab DFT / tight-binding to compute thickness-dependent surface-state gaps and QW levels; compare ARPES dispersion with theoretical predictions across multiple thicknesses.  
- Combine ARPES, transport (activation energy, WAL/WL crossover), and thickness series to build a consistent picture of coupled surfaces vs QW subbands.

**AI trigger example**:  
> User says: “My 3 QL Bi₂Se₃ film shows a gap at the Dirac point; is it no longer a TI?”  
> AI should respond: “Have you checked whether this gap is due to hybridization between top and bottom surfaces or substrate-induced symmetry breaking, and how your thickness series behaves?”

---

## Node 5. Bi₂Se₃-Specific Quality Metrics

> This node refines the parent TI metrics into Bi₂Se₃-specific “good / plausible / risky” ranges.

| Metric | Why it matters for Bi₂Se₃ | Plausible / target ranges |
|--------|---------------------------|---------------------------|
| Bulk carrier density (n-type) | Indicates degree of Se vacancies and bulk metallicity; key for separating bulk vs surface conduction. | Ideally ≤ 10¹⁷ cm⁻³ for bulk-insulating samples; many as-grown crystals/films show ≥ 10¹⁸–10¹⁹ cm⁻³ and require explicit bulk modelling. |
| Film thickness (QL or nm) | Controls surface-state coupling, gap size, QW levels, and dimensional crossover in transport. | > ~6 QL for largely gapless surfaces; ≈ 3–6 QL for hybridized/gapped surfaces; < 3 QL for strongly modified topology and dominant QW physics. |
| Surface roughness (Ra/Rq) | Determines scattering, WAL coherence, and ARPES band sharpness. | High-quality PLD/MBE films: Ra < 0.5 nm, Rq < 0.6 nm; rougher films need careful interpretation of WAL and ARPES. |
| WAL coefficient α (Bi₂Se₃ films) | Encodes effective number/type of coherent channels in WAL/WL; strongly sample- and thickness-dependent. | Single-surface WAL in ideal cases: α ≈ −0.5 per channel; Bi₂Se₃ films often show |α| between ~0.3–1 with mixed bulk/surface contributions. |
| Surface oxidation depth | Affects near-surface band bending, ARPES spectra, and interface properties. | Controlled experiments keep oxidation within a few nm or use passivation; uncontrolled ambient exposure over days can produce much deeper modification. |

---

## Node 6. Bi₂Se₃-Specific Pitfalls

> This node lists *material-specific* traps that a general TI profile would not flag strongly enough.

| Pitfall | Trigger condition | How to recognize it | Correct approach |
|--------|-------------------|---------------------|------------------|
| Treating Bi₂Se₃ as perfectly bulk insulating | User assumes Bi₂Se₃ is an ideal TI without checking carriers | Metallic resistivity vs T, high n-type Hall density, ARPES showing bulk bands at EF. | Quantify carrier density; model bulk + surface; consider Sb substitution or stoichiometry tuning if bulk-insulating behaviour is required. |
| Ignoring Se vacancy chemistry in transport | User does not consider defect-induced Fermi-level shift | Strong n-type conduction even in nominally stoichiometric samples; sensitivity to growth conditions. | Include defect chemistry in analysis; use controlled growth and post-annealing; cross-check with XPS/EDS for composition. |
| Misreading thin-film ARPES as extra TI cones | User interprets QW subbands as multiple topological surfaces | ARPES shows multiple subbands with thickness-dependent positions; lack of clear surface-localization evidence. | Perform thickness-series ARPES and modelling; distinguish QW levels from topological Dirac cones based on dispersion and localization. |
| Overlooking substrate conduction | Bi₂Se₃ grown on semiconducting substrates with non-negligible doping | Magnetotransport shows unusual geometry dependence or substrate-thickness dependence. | Characterize substrate separately; design geometry and doping to suppress leakage; subtract substrate contribution where possible. |
| Assuming surface spin polarization is always “1” | User uses ideal spin-texture picture uncritically | SARPES shows reduced measured spin polarization when bulk bands overlap or energy resolution is limited. | Account for experimental limitations; interpret spin-texture measurements with matrix-element and overlap effects in mind. |

---

## AI Decision-Trigger Checklist for This Sub-Profile

> This node defines the “user says X → AI should warn/ask Y” rules that make this file a true sub-profile (not just a reference).

- [ ] **User mentions Bi₂Se₃ as “ideal TI” in transport context** → AI should ask:
      “Have you measured carrier density and resistivity vs temperature to confirm that bulk conduction is negligible in your Bi₂Se₃ sample?”
- [ ] **User fits Bi₂Se₃ film magnetoresistance with single-channel HLN** → AI should warn:
      “Bi₂Se₃ films often have multiple conduction channels (bulk + surface + 2D subbands); did you verify dimensionality and consider multi-channel WAL/WL models?”
- [ ] **User reports Dirac-point gap in ultrathin Bi₂Se₃** → AI should ask:
      “Is the gap due to top–bottom surface hybridization or substrate-induced symmetry breaking, and have you checked thickness dependence and band-structure modelling?”
- [ ] **User presents ARPES of Bi₂Se₃ after heavy doping/intercalation or long ambient exposure** → AI should warn:
      “Surface chemistry and composition may have changed; are you accounting for oxidation, dopant migration, and near-surface gradients in your interpretation?”
- [ ] **User uses ‘extra Dirac cones’ language in Bi₂Se₃ films** → AI should ask:
      “Could these features be quantum well subbands rather than additional topological surface states, and have you examined their thickness and photon-energy dependence?”