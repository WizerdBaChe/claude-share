# Domain Profile: Topological Insulator (拓撲絕緣體, topological insulator, TI)

> Scope of applicability:
> - Bulk-gapped, edge/surface-conducting quantum materials described as topological insulators(拓撲絕緣體, topological insulator, TI).
> - Includes both 2D quantum spin Hall insulators(量子自旋霍爾絕緣體, quantum spin Hall insulator) and 3D topological insulators(三維拓撲絕緣體, three-dimensional topological insulator, 3D TI).[web:22][web:39]
>
> Scientific nature:
> - Band topology (能帶拓撲, band topology) of time-reversal-symmetric(時間反轉對稱, time-reversal symmetry, TRS) electronic systems classified by Z₂ topological invariants(Z₂ 拓撲不變量, Z₂ topological invariants).[web:45][web:48]
> - Bulk–boundary correspondence(體積–邊界對應, bulk–boundary correspondence) guaranteeing protected gapless boundary states.[web:22][web:40]
>
> Engineering nature:
> - Materials and heterostructures providing robust spin-polarized surface or edge channels for transport, spintronics, quantum metrology, and proximity-induced phases (e.g. quantum anomalous Hall effect(量子反常霍爾效應, quantum anomalous Hall effect, QAHE), Majorana zero modes(馬約拉納零能模, Majorana zero modes)).[web:39][web:35][web:54]
>
> Profile metadata:
> - Profile ID: TI.domain.v1
> - Profile version: 0.2 (minor corrections for measurement and HLN usage)
> - Last updated: 2026-07-07
> - Author(s) / Maintainer(s): Perplexity (research assistant profile)
>
> Primary source types:
> - Textbooks:
>   - Lecture notes and introductory materials on topological insulators and superconductors (e.g. Qi & Zhang 2011, Bernevig course notes).[web:39][web:51][web:58]
> - Review articles:
>   - Hasan & Kane, “Colloquium: Topological insulators” (Rev. Mod. Phys. 2010).[web:22][web:55]
>   - Qi & Zhang, “Topological insulators and superconductors” (Rev. Mod. Phys. 2011).[web:39][web:54]
>   - Pedagogical review “Topological insulator materials”.[web:40][web:41]
> - Methods / standards papers:
>   - First-principles predictions of Bi₂Se₃/Bi₂Te₃/Sb₂Te₃ topological phases.[web:52][web:29]
>   - Magnetotransport WAL/WL studies using Hikami–Larkin–Nagaoka equation(希神–拉金–納卡奧方程, Hikami–Larkin–Nagaoka equation, HLN equation).[web:33][web:30][web:36][web:62]
> - Other (e.g. datasheets, industry standards):
>   - Materials-chemistry studies of Bi₂Se₃/Bi₂Te₃ surface reactivity and acceptable preparation/handling conditions.[web:56][web:63]
>
> Notes for AI use:
> - Intended use:
>   - Provide first-principles and materials-level reasoning for queries about topological insulators(拓撲絕緣體), their classification, transport signatures, and heterostructure effects before jumping to device-level optimization.
> - Validation status / usage note:
>   - This profile is anchored to canonical RMP reviews and established materials papers; when user queries touch speculative TI candidates or non-electronic “topological” systems, the AI should explicitly flag evidence levels and stay within this profile’s validated scope.[web:22][web:39][web:40]

---

## 1. Theoretical Framework Anchoring

### Core first principles

| Scale / problem type | Foundational theory | Core physical quantity |
|----------------------|---------------------|------------------------|
| Bulk band classification of insulators | Band theory + Z₂ topological invariant(Z₂ 拓撲不變量, Z₂ topological invariant) for TRS systems | Z₂ indices \((\nu_0;\nu_1,\nu_2,\nu_3)\) distinguishing trivial vs strong/weak TI phases.[web:45][web:48] |
| Boundary state existence and robustness | Bulk–boundary correspondence(體積–邊界對應, bulk–boundary correspondence) | Topologically protected gapless edge/surface modes and their symmetry protection.[web:22][web:40] |
| 2D TI / quantum spin Hall physics | Quantum spin Hall theory(量子自旋霍爾理論, quantum spin Hall theory) for 2D TRS systems | Helical edge states(螺旋邊界態, helical edge states) and spin-resolved edge conductance.[web:22][web:26] |
| 3D TI surface states | Effective Dirac Hamiltonian(Dirac 哈密頓量, effective Dirac Hamiltonian) for TI surfaces | Dirac cone(狄拉克錐, Dirac cone) dispersion, spin–momentum locking(自旋–動量鎖定, spin–momentum locking), Berry phase(貝里相位, Berry phase).[web:22][web:38][web:68] |
| Disorder and quantum corrections | Quantum interference theory for weak localization(弱局域化, weak localization, WL) and weak antilocalization(弱反局域化, weak antilocalization, WAL) | Phase coherence length(相干長度, phase coherence length), magnetoconductivity corrections, HLN equation parameters.[web:30][web:33][web:62] |
| Symmetry-breaking and proximity-induced phases | TRS breaking and superconducting proximity in TI | Surface gaps, quantum anomalous Hall effect(量子反常霍爾效應, QAHE), Majorana zero modes(馬約拉納零能模, Majorana zero modes).[web:39][web:54] |

### Inviolable physical constraints (the AI should warn the user here)

1. TI boundary states require a non-trivial bulk topology with appropriate protecting symmetries (typically TRS); boundary states cannot be arbitrarily added by “engineering” without changing bulk band topology.[web:22][web:39]
2. Z₂ classification applies only to band insulators with TRS; using Z₂ indices outside their applicability (e.g. strongly interacting, symmetry-broken systems) is physically invalid.[web:45][web:48]
3. In realistic Bi₂Se₃/Bi₂Te₃ samples, bulk conduction can be substantial; assuming “perfectly insulating bulk” for transport interpretation without checking carrier densities and defect chemistry is unsafe.[web:17][web:56][web:65]
4. WAL/WL analysis using HLN equation assumes quasi-2D transport, diffusive regime, and specific disorder/SOC regimes; blindly fitting 3D or strongly inhomogeneous systems to HLN without checking dimensionality, dephasing mechanisms, and multi-channel contributions leads to false conclusions.[web:33][web:30][web:62]
5. TI surface-state robustness applies to non-magnetic disorder; magnetic impurities or magnetic proximity can break TRS and open gaps, invalidating simple “protected transport” assumptions and requiring QAHE/topological magnetism frameworks instead.[web:22][web:39][web:36][web:66]

> **Decision point (mandatory Tier 0 confirmation)**: when the user describes a “topological insulator device or experiment”,  
> the AI must confirm:  
> “Is your goal (A) to understand/classify the bulk band topology, (B) to interpret edge/surface transport signatures (e.g. WAL, ARPES), or (C) to design/assess a heterostructure or proximity-induced phase?”  
> The three goals correspond to entirely different measurement, modeling, and analysis paths:
> - (A): focus on band-structure calculations, Z₂ indices, and canonical TI vs trivial materials.[web:45][web:52]
> - (B): focus on transport, magnetotransport, ARPES, and surface vs bulk conduction separation, including WAL/WL and multi-channel analysis.[web:22][web:33][web:62]
> - (C): focus on interface quality, materials matching, and proximity-effect theory (graphene/TI, magnetic/TI, superconducting/TI).[web:35][web:39][web:54][web:56]

---

## 2. Measurement Tool Inventory

### Electronic structure and boundary-state spectroscopy

| Measurement target | Tool | Output information | Applicable conditions | Common misuse |
|--------------------|------|--------------------|-----------------------|---------------|
| Bulk band topology and surface Dirac cones | ARPES (angle-resolved photoemission spectroscopy, 角解析光電子能譜) | Direct band dispersion, Dirac cone presence, band inversion at Γ, surface vs bulk bands.[web:22][web:52][web:68] | High-quality single crystals or epitaxial films with clean surfaces; ultrahigh vacuum (UHV); controlled cleaving or *in situ* preparation; sufficient energy and momentum resolution.[web:56][web:63] | Interpreting every linear-looking feature as a TI Dirac cone without checking surface sensitivity, bulk gap, or spin texture.[web:22][web:68] |
| Surface-state spin texture | Spin-resolved ARPES (自旋解析 ARPES) | Spin–momentum locking patterns, spin polarization of surface states.[web:22][web:68] | Same as ARPES plus spin detection capabilities, often lower count rates and stricter surface quality requirements.[web:68] | Assuming spin–momentum locking from band shape alone, without actual spin-resolved measurement. |
| Band gap magnitude and band inversion | Optical spectroscopy, STM/STS | Bulk band gap size, local density of states near Dirac point.[web:39][web:51] | Clean surfaces; well-characterized doping level; low temperatures for STS; careful distinction between surface and bulk features. | Treating local STS spectra as representative of entire bulk without regard to spatial inhomogeneity or defects. |

### Transport and magnetotransport

| Measurement target | Tool | Output information | Applicable conditions | Common misuse |
|--------------------|------|--------------------|-----------------------|---------------|
| Quantum corrections (WL/WAL) to conductivity | Low-temperature magnetotransport (四端或霍爾量測) | Magnetoconductivity curves, WAL/WL signatures, coherence length from HLN fits.[web:33][web:30][web:36][web:62] | Thin films or quasi-2D samples; temperatures low enough for phase coherence; diffusive transport regime; magnetic fields covering the WL/WAL regime but below strong quantum limit.[web:33][web:60] | Fitting HLN blindly to any magnetoresistance data (including 3D or ballistic regimes) without verifying dimensionality, SOC regime, dephasing mechanism, or multi-channel transport (bulk + surface).[web:33][web:62] |
| Surface vs bulk conduction contributions | Temperature-dependent resistivity and Hall measurements | Carrier densities, mobilities, activation behaviour vs metallic conduction; separating bulk and surface dominance.[web:17][web:65] | Wide temperature range; careful geometry; possibly gate-tuning or thickness variation to modulate surface carriers vs bulk; complementary spectroscopy if available. | Assuming “surface-only” conduction in Bi₂Se₃ family without measuring carrier density, thickness dependence, or performing gating/geometry analysis.[web:17][web:56][web:65] |
| Quantum anomalous Hall plateau | Low-temperature Hall measurements in magnetically doped TI films | Quantized Hall resistance, vanishing longitudinal resistance, evidence for QAHE.[web:39][web:58] | Very low temperatures; carefully controlled magnetic doping or proximity; thin-film geometry; stable magnetization orientation. | Interpreting any anomalous Hall signal as QAHE without quantization, clear plateau behaviour, or TI surface origin. |

### Interface and proximity characterization

| Measurement target | Tool | Output information | Applicable conditions | Common misuse |
|--------------------|------|--------------------|-----------------------|---------------|
| Graphene/TI proximity-induced SOC | ARPES, transport, spintronic measurements on graphene/TI stacks | SOC-induced band gaps in graphene, spin Hall signals, modified band structures.[web:35] | High-quality heterostructures with atomically clean interfaces; controlled graphene thickness and TI layer thickness; minimal contamination between layers.[web:35][web:56] | Attributing all changes in graphene transport to TI proximity without ruling out disorder, substrate effects, or charge transfer. |
| Magnetic/TI interfaces and surface gaps | ARPES, magnetotransport, Kerr microscopy | Surface gap opening, magnetization orientation, QAHE signatures.[web:39][web:58][web:66] | Magnetic order well defined; TI film thickness tuned; low temperatures; control of light source and measurement geometry (gap signatures can depend on probe).[web:66] | Assuming TRS is intact when magnetic signatures are clearly present; misusing TI “protected surface” language in magnetically ordered systems. |
| Superconducting/TI Majorana candidates | Tunneling spectroscopy, Josephson measurements | Zero-bias peaks, 4π-periodic Josephson signals indicative of Majorana modes.[web:39][web:54] | High-quality TI–superconductor interfaces; phase-coherent Josephson junctions; low-noise spectroscopy; control of trivial Andreev bound states. | Claiming Majorana modes from any zero-bias anomaly without systematic checks against trivial bound states, inhomogeneity, or measurement artifacts. |

---

## 3. Standard Modeling Toolchain
