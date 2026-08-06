# User-Supplied Citation Inventory

> Status: source inbox plus a small set of identity-checked promotion candidates
> Last updated: 2026-08-03
> Scope: URLs supplied with the GaN power, MicroLED, and Bi2Se3 material packets
> Evidence rule: A URL stored in the inbox is provenance, not evidence. Promote it into a domain profile only after identity, access level, locator, relevance, and claim scope are checked.

## Storage and triage rules

1. Preserve the user-provided URL verbatim in the source inbox. Do not silently replace a repository copy, thesis mirror, publisher page, or preprint with another URL.
2. Resolve a canonical identifier when available: DOI first, then PMID, arXiv ID, patent number, ISBN, or repository identifier.
3. Record access honestly: [full] means the full text was read; [partial] means only selected sections, a preview, or supplementary material was read; [abstract] means abstract or metadata only; [secondary] means the item was learned through another source; [untriaged] means identity or relevance is not yet checked.
4. Keep alternate versions under one citation identity when the identity is verified, but retain every user-provided access URL in the inbox.
5. Promote only the smallest useful set into a domain profile's Literature Anchors. A promoted entry must include why it matters and must not be used beyond the conditions actually read.
6. Treat Wikipedia, lectures, seminars, vendor pages, blogs, videos, search aggregators, patents, and theses as discovery or engineering-context sources unless the claim explicitly requires that source type. They are not substitutes for a peer-reviewed primary paper.
7. Keep unresolved or context-dependent terms in the inbox as [untriaged]; do not expand an acronym or infer a mechanism from the URL alone.
8. When a later search updates an entry, append a note with the date, access level, identifier, locator, and disposition. Do not erase the original provenance.

## Identity-checked promotion candidates

These entries were checked against the supplied URL, DOI/title metadata, or an accessible journal page during this pass. The access tag limits what may be asserted from the entry.

| Track | Canonical identity | User URL or access family | Access | Intended use | Disposition |
|---|---|---|---|---|---|
| Bi2Se3 | ACS Photonics, DOI 10.1021/acsphotonics.7b00524 | https://pubs.acs.org/doi/10.1021/acsphotonics.7b00524 | [abstract] | Spin-charge separation, inversion-layer and phonon-plasmon theory | Candidate anchor; publisher page was not readable in this pass |
| Bi2Se3 | Micromachines 15(5), 610, DOI 10.3390/mi15050610 | https://www.mdpi.com/2072-666X/15/5/610 | [partial] | Generic RTRR/HPWG refractive-index sensing route | Route to plasmonic_waveguide; not Bi2Se3 evidence |
| Bi2Se3 | NPG Asia Materials 12, 37 (2020), DOI 10.1038/s41427-020-0218-7 | https://www.nature.com/articles/s41427-020-0218-7 | [full] | Correlated plasmons, ellipsometry, ARPES, bulk/surface carrier competition | Candidate anchor |
| Bi2Se3 | Applied Physics Letters 119, 201103, DOI 10.1063/5.0071895 | https://pubs.aip.org/aip/apl/article/119/20/201103/40520 | [abstract] | In-plane plasmon coupling in Bi2Se3 stripe structures | Candidate anchor; full text not read |
| Bi2Se3 | Nature Communications 8, 2141 (2017), DOI 10.1038/s41467-017-02264-y | https://www.nature.com/articles/s41467-017-02264-y | [full] | Guided-photon coupling, spin-momentum locking, directional photocurrent controls | Candidate anchor |
| Bi2Se3 | Physical Review B 83, 035309, DOI 10.1103/PhysRevB.83.035309 | https://link.aps.org/doi/10.1103/PhysRevB.83.035309 | [full] | C3v, CPGE symmetry, Berry-curvature-dependent response | Candidate anchor |
| Bi2Se3 | Physical Review B 107, L161403, DOI 10.1103/PhysRevB.107.L161403 | https://link.aps.org/doi/10.1103/PhysRevB.107.L161403 | [partial] | Linear photogalvanic effect in TI surface states | Candidate follow-up; abstract/page metadata checked |
| Bi2Se3 | ACS Applied Materials & Interfaces, DOI 10.1021/acsami.9b23389 | https://pubs.acs.org/doi/10.1021/acsami.9b23389 | [untriaged] | User-supplied material/interface source | Identity and relevance still require checking |
| GaN | 1.3 kV Vertical GaN-Based Trench MOSFETs, Article 14 (2022), DOI 10.1186/s11671-022-03653-z | https://pmc.ncbi.nlm.nih.gov/articles/PMC8761181/ and https://link.springer.com/article/10.1186/s11671-022-03653-z | [full] | 1.3 kV vertical trench MOSFET; VTH, RON,sp, BV, FOM, TCAD calibration | Candidate anchor; Springer full article was readable |
| GaN | Scientific Reports, DOI 10.1038/s41598-024-84007-w | https://pmc.ncbi.nlm.nih.gov/articles/PMC11696899/ and https://www.nature.com/articles/s41598-024-84007-w | [partial] | Triple-shield BPSG-MOS design case | Candidate anchor; PMC page was blocked in this pass |
| GaN | Micromachines 14, 1937 (2023), DOI 10.3390/mi14101937 | https://www.mdpi.com/2072-666X/14/10/1937 | [partial] | Vertical GaN MOSFET review and architecture map | Candidate anchor; publisher page rate-limited |
| GaN | Journal of Applied Physics 131, 114502, DOI 10.1063/5.0079760 | https://pubs.aip.org/aip/jap/article/131/11/114502/2836737/ | [partial] | CAVET turn-on-voltage/interface barrier interpretation | Candidate anchor; publisher page was not directly readable |
| GaN | Micromachines 14, 2005 (2023), DOI 10.3390/mi14112005 | https://www.mdpi.com/2072-666X/14/11/2005 | [untriaged] | GaN trench field-plate/edge-termination method context | Identity known from supplied URL; full relevance check pending |
| GaN | ACS Applied Materials & Interfaces, DOI 10.1021/acsami.3c02840 | https://pubs.acs.org/doi/10.1021/acsami.3c02840 | [abstract] | TMAH/nonpolar-plane treatment and trench electrical effect | Candidate process-specific source; no universal recipe |
| MicroLED | Light: Science & Applications 14, 64 (2025), DOI 10.1038/s41377-025-01751-y | https://www.nature.com/articles/s41377-025-01751-y | [full] | InGaN sidewall effect, mitigation methods, EQE/packaging limits | Candidate anchor |
| MicroLED | Applied Physics Letters 111, 022104, DOI 10.1063/1.4993741 | https://pubs.aip.org/aip/apl/article/111/2/022104/34761/Shockley-Read-Hall-and-Auger-non-radiative | [full] | SRH/Auger size-effect modeling in GaN LEDs | Candidate anchor; accessible article page checked |
| MicroLED | Nanoscale Research Letters 16, 99 (2021), DOI 10.1186/s11671-021-03557-4 | https://pmc.ncbi.nlm.nih.gov/articles/PMC8175512/ | [partial] | InGaN microLED structure and low-current EQE modeling | Candidate follow-up; PMC page was blocked in this pass |

## Canonical duplicate groups

The following groups are treated as one citation identity only where the identity is supported by the identifier:

| Identity | Alternate user URLs |
|---|---|
| ACS Photonics DOI 10.1021/acsphotonics.7b00524 | https://pubs.acs.org/doi/10.1021/acsphotonics.7b00524; https://pubs.acs.org/doi/abs/10.1021/acsphotonics.7b00524; https://arxiv.org/pdf/1706.09403.pdf |
| GaN 1.3 kV trench MOSFET DOI 10.1186/s11671-022-03653-z | https://pmc.ncbi.nlm.nih.gov/articles/PMC8761181/; https://link.springer.com/article/10.1186/s11671-022-03653-z; https://www.semiconductor-today.com/news_items/2023/sep/swegan-210923.shtml |
| GaN triple-shield DOI 10.1038/s41598-024-84007-w | https://pmc.ncbi.nlm.nih.gov/articles/PMC11696899/; https://www.nature.com/articles/s41598-024-84007-w; https://csmantech.org/wp-content/uploads/2025/05/2A.2-Final.2025.pdf |
| Generic RTRR/HPWG DOI 10.3390/mi15050610 | https://www.mdpi.com/2072-666X/15/5/610; https://www.semanticscholar.org/paper/2944335ea0059073531b43eab410d4d63c |
| Nature Communications DOI 10.1038/s41467-017-02264-y | https://www.nature.com/articles/s41467-017-02264-y; https://lilab.faculty.wvu.edu/highlights/electrical-detection-of-spin-momentum-locking |

The supplied arXiv PDF is an alternate access route for the ACS Photonics topic. Preserve the exact user URL in the inbox below and resolve the arXiv identifier before citation.

## User-provided source inbox: Bi2Se3

All entries below are preserved as source-provided provenance. Unless promoted above, treat them as [untriaged].

- https://pubs.acs.org/doi/10.1021/acsphotonics.7b00524
- https://www.mdpi.com/2072-666X/15/5/610
- https://www.spintec.fr/spin-orbitronics-at-a-topological-insulator-semiconductor-interface/
- https://iopscience.iop.org/article/10.1088/1361-648X/ac2928
- https://www.nature.com/articles/s41427-020-0218-7
- https://arxiv.org/html/2602.00251v2
- https://udspace.udel.edu/items/607d894e-27c1-4418-b6e9-f34c84025d8f
- https://www.semanticscholar.org/paper/2944335ea0059073531b43eab410d4d63c
- https://pubs.acs.org/doi/10.1021/acsami.9b23389
- https://pubs.aip.org/aip/apl/article/119/20/201103/40520
- https://pubs.acs.org/doi/abs/10.1021/acsphotonics.7b00524
- https://www.science.ntu.edu.tw/seminar/the-2nd-renaissance-of-spintronics-from-spin-transfer-torque-to-spin-orbit-torque-mram/
- https://arxiv.org/pdf/1706.09403.pdf
- https://lilab.faculty.wvu.edu/highlights/electrical-detection-of-spin-momentum-locking
- https://pubmed.ncbi.nlm.nih.gov/25056062/
- https://www.nature.com/articles/s41467-017-02264-y
- https://eunahkim.ccmr.cornell.edu/sites/kim/files/publications/1402.1124.pdf
- https://link.aps.org/doi/10.1103/PhysRevB.88.205427
- https://materialssciences.lbl.gov/2023/01/30/spin-momentum-locked-surface-states-in-amorphous-bi2se3/
- https://en.wikipedia.org/wiki/Spin-transfer_torque
- https://arxiv.org/abs/1103.3410
- https://link.aps.org/doi/10.1103/PhysRevB.89.235432
- https://www.sciencedirect.com/science/article/abs/pii/S1569441022000529
- https://en.wikipedia.org/wiki/Surface_plasmon_polariton
- https://arxiv.org/abs/2308.11429
- https://iopscience.iop.org/article/10.1088/2040-8986/ad535f
- https://dspace.mit.edu/bitstream/handle/1721.1/88644/PhysRevB.89.235432.pdf
- https://pubmed.ncbi.nlm.nih.gov/31012656/
- https://www.youtube.com/watch?v=oBThg3t9A-E
- https://people.engr.tamu.edu/spalermo/ecen689_oi/lecture11_ee689_rrm_tx.pdf
- https://nanohub.org/resources/1944/download/2006.10.12-ece695s-l10.pdf
- https://opg.optica.org/oe/fulltext.cfm?uri=oe-27-16-22819&id=416217
- https://link.aps.org/doi/10.1103/PhysRevB.107.L161403
- https://www.science.org/doi/10.1126/sciadv.abe5748
- https://arxiv.org/html/2407.05908v1
- https://einstein.nju.edu.cn/upload/uploadify/20220120/20220119-2201.06294-Topologicalphotoniccrystals_202201201933372427.pdf
- https://arxiv.org/abs/2211.14248
- https://link.aps.org/doi/10.1103/PhysRevB.93.081403
- https://epub.uni-regensburg.de/53798/1/PhysRevApplied.16.064030.pdf
- https://epub.ub.uni-greifswald.de/files/4543/Doktorarbeit_NM.pdf
- https://link.aps.org/doi/10.1103/PhysRevApplied.15.034053
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11057521/
- https://arxiv.org/pdf/2411.13947.pdf
- https://pubs.acs.org/doi/10.1021/acsnano.4c09295
- https://link.aps.org/pdf/10.1103/PhysRevResearch.4.033198
- https://www.emergentmind.com/topics/linear-photogalvanic-effect
- https://repository.uantwerpen.be/docstore/d:irua:30368
- https://arxiv.org/pdf/2602.00251.pdf
- https://pure.mpg.de/rest/items/item_2368434_9/component/file_2368620/content
- https://epub.uni-regensburg.de/22030/1/karch.pdf
- https://inspirehep.net/files/d7a2004e215a1c964b97bb8a90d8ce9a
- https://refubium.fu-berlin.de/bitstream/handle/fub188/1540/Dissertation_Junck.pdf
- https://repositorio.imdeananociencia.org/rest/api/core/bitstreams/d45bf024-cee0-40d7-824c-b49cf6b4a739/content
- https://phy.ntnu.edu.tw/~changmc/Teach/Topo/latex/2020/08.pdf
- https://oamonitor.ireland.openaire.eu/national/search/publication?pid=10.1103/physrevb.83.035309
- https://bib-pubdb1.desy.de/record/299366/files/TI_Rev_Revised.pdf

## User-provided source inbox: GaN power

All entries below are preserved as source-provided provenance. Unless promoted above, treat them as [untriaged].

- https://pmc.ncbi.nlm.nih.gov/articles/PMC8761181/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11696899/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6474137/
- https://www.mdpi.com/2072-666X/14/11/2005
- https://data.epo.org/publication-server/rest/v1.2/publication-dates/2025-01-08/patents/EP3896744NWB1/document.pdf
- https://www.nature.com/articles/s41598-024-84007-w
- https://csmantech.org/wp-content/uploads/2025/05/2A.2-Final.2025.pdf
- https://patents.google.com/patent/US20120043602A1/en
- https://toshiba.semicon-storage.com/content/dam/toshiba-ss-v3/master/en/company/technical-review/pdf/technical-review-32.pdf
- https://community.infineon.com/t5/Knowledge-Base-Articles/More-than-an-Evolution-a-New-Power-MOSFET-Technology-for-Higher-Efficiency
- https://www.mdpi.com/2072-666X/14/10/1937
- https://pubs.aip.org/aip/jap/article/131/11/114502/2836737/
- https://www.sciencedirect.com/science/article/abs/pii/S0167931725001078
- https://kb.osu.edu/bitstreams/e170fbf0-baff-476a-9e28-9028aeecc12b/download
- https://www.furukawaelectric.com/review/fr036/fr36_01.pdf
- https://wsiplaw.com/wp-content/uploads/2022/04/Doctoral-research_AlGaN_GaN-CAVET_1.pdf
- https://toshiba.semicon-storage.com/content/dam/toshiba-ss-v3/master/en/company/technical-review/pdf/75-06_A10_E.pdf
- https://escholarship.org/uc/item/8527906w
- https://dspace.mit.edu/bitstream/handle/1721.1/121717/MSSP_online_JieHu.pdf
- https://semiconductor-today.com/features/PDF/semiconductor-today-july-august-2017-Gallium-nitride.pdf
- https://www.scribd.com/document/896943058/1-s2-0-S2772671123001134-main
- https://www.osti.gov/biblio/1996311
- https://silvaco.com/zh-hans/simulation-standard-zh-hans/advanced-process-and-device-3d-tcad-simulation-of-split-gate-trench-umos
- https://patents.google.com/patent/US10777661B2/en
- https://www.semanticscholar.org/paper/Shield-Gate-Trench-MOSFET-With-Narrow-Gate
- https://www.researching.cn/ArticlePdf/m00098/2022/43/12/122802.pdf
- https://ptc.home.ece.ust.hk/Papers/2024/Fully-Vertical_GaN-on-SiC_Trench_MOSFETs.pdf
- https://link.springer.com/article/10.1186/s11671-022-03653-z
- https://www.ee.nthu.edu.tw/shhsu/journal%20papers/SST_GaN%20contanct%20engineering.pdf
- https://www.semiconductor-today.com/news_items/2023/sep/swegan-210923.shtml
- https://pubs.acs.org/doi/10.1021/acsami.3c02840
- https://www.infineon.com/assets/row/public/documents/24/54/infineon-power-mosfet-basics-article-en.pdf
- https://www.vishay.com/docs/73217/an608a.pdf
- https://ieeexplore.ieee.org/iel8/23/4689328/10925500.pdf
- https://www.sciencedirect.com/science/article/abs/pii/S0026269203001939
- https://www.powerelectronictips.com/what-is-gate-charge-and-why-does-it-matter-for-switching-speed/
- https://joam.inoe.ro/articles/deep-traps-responsible-for-capacitance-hysteresis-in-algangan-fat-hemts-studied-under-the-temperature
- https://www.shindengen.com/products/semi/column/basic/mosfet/mosfet_on_resistance.html
- https://psecommunity.org/wp-content/plugins/wpor/includes/file/2304/LAPSE-2023.31653-1v1.pdf
- https://techweb.rohm.com/product/transistors-diodes/transistors/23724/
- https://web.xidian.edu.cn/jjzhu/files/20180719_094206.pdf
- https://www.aosmd.com/res/application_notes/mosfets/Power_MOSFET_Basics.pdf
- https://ww1.microchip.com/downloads/aemDocuments/documents/PSDS/ApplicationNotes/ApplicationNotes/APT0103.pdf
- https://www.synopsys.com/manufacturing/tcad.html
- https://ieeexplore.ieee.org/document/8730978/
- https://kolegite.com/EE_library/books_and_lectures/
- https://www.scribd.com/document/306143489/03-TCAD-Laboratory-Overview-of-Synopsys-Sentaurus-TCAD-GBB-FinalAA13-14
- https://www-elec.inaoep.mx/seminario2013/ortiz_SNDA13.pdf
- https://theses.hal.science/tel-04213673/file/these.pdf
- https://indico.in2p3.fr/event/30704/contributions/128491/attachments/79535/119813/Nallet_SIMDET2023_School_Synopsys_Overview.pdf
- https://www.keysight.com/blogs/en/tech/sim-des/mosfet-threshold-voltage-extraction
- https://www.scribd.com/document/272257272/A-Review-of-Recent-MOSFET-Vth-Extraction-Methods
- https://scispace.com/pdf/gan-power-devices-discerning-application-specific-challenges-587q4a75b1.pdf
- https://sbmicro.org.br/sforum-eventos/sforum2019/Threshold%20Voltage%20Extraction%20Methods%20Applied%20to%20BESOI

## User-provided source inbox: MicroLED

All entries below are preserved as source-provided provenance. Unless promoted above, treat them as [untriaged].

- https://www.sciencedirect.com/science/article/pii/S2211379722002029
- https://www.sciencedirect.com/science/article/abs/pii/S2773012323000390
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12521080/
- https://www.nature.com/articles/s41377-025-01751-y
- https://pmc.ncbi.nlm.nih.gov/articles/PMC8175512/
- https://pubs.aip.org/aip/apl/article/111/2/022104/34761/Shockley-Read-Hall-and-Auger-non-radiative
- https://www.light-am.com/article/pdf/preview/LAM2023010002.pdf
- https://www.fluxim.com/publications-overview/research-paper-far-field-electroluminescence-mapping-and-setfos-cavity-fitting-for-
- https://www.sciencedirect.com/science/article/abs/pii/S0038110104002631
- https://hal.science/hal-03124589v1/document
- https://www.sciencedirect.com/science/article/pii/S221137972200780X
- https://www.researching.cn/ArticlePdf/m00098/2020/41/4/041606.pdf

## Maintenance

- Keep this file as the source-provenance layer. Do not use it as a substitute for the domain profiles' 3–5 Literature Anchors.
- When promoting an entry, add its identifier, access tag, locator, relevance, and limitations to the promotion table.
- When a URL is dead, retain the URL and append a status note; do not delete user provenance.
- When a paper has a publisher page, repository mirror, preprint, and thesis version, verify that the versions share the same identity before grouping them.

### Delegation rule: updating this file through literature-search-extract

This file's own tables must not be hand-updated by an untraceable ad hoc search. Any
substantive change to it — promoting an `[untriaged]` entry, raising an access tag
(e.g. `[abstract]` → `[full]`), resolving a dead link, or adding a new identity-checked
row — is Tier 1 literature work and follows the same rule as any other Tier 1 task
(SKILL.md Gate B): delegate the actual search/read to the `literature-search-extract`
skill (Mode 2), do not do it inline from memory or a single unlogged fetch.

- **Request contract**: `purpose` = identity/access-tier verification or gap-fill for this
  inbox; `question` = the specific claim or track this entry should support (e.g. "does
  this URL resolve to a peer-reviewed source that supports the CAVET turn-on-knee claim
  in gan_power_device.md?"); `source_types` = per this file's §Storage-and-triage-rules
  item 6 (peer-reviewed primary/review preferred, engineering/vendor/preprint flagged as
  such); `scope` = the single track being updated (GaN power / MicroLED / Bi2Se3, etc.);
  `output_format` = canonical identifier + access tag + one-line relevance + limitations,
  matching this file's promotion-table columns; `depth` = targeted (one entry or one
  small batch), not a broad sweep.
- **Result contract**: consume `findings`/`sources`/`gaps`/`confidence`/`search_trail` and
  write them straight into the promotion table or the identity-checked row; do not
  paraphrase away the access tag or the stated limitations.
- **Traceability**: when an update was produced by a literature-search-extract run, note
  the date inline in the row's Disposition cell (or in the Canonical-duplicate-groups
  note for identity merges) so a future maintainer can see which entries were
  contract-verified versus carried over from an earlier integration pass. This mirrors
  how `reports/2026-08-03-scientific-research-guide-material-integration.md` records the
  Mode 2 contract used to build this file's first version.
- **Batch integration passes** (adding a whole new domain's citation set at once, as in
  the 2026-08-03 GaN/MicroLED/Bi2Se3 pass) should still run through the same contract per
  track, and should leave a dated audit-trail report in `reports/`, not only a diff to
  this file.
- This delegation rule does not apply to purely mechanical edits (fixing a typo, marking
  a URL dead without re-resolving it, reformatting a table) — those may be done directly.
