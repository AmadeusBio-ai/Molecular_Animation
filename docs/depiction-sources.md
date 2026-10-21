# Depicting biomolecular physics honestly: sources

The sources behind `molanim.electro`, `molanim.cartoon` and the captions of pictures built with them (the van der Waals
envelope, Coulombic colouring, pi lobes, fluorescence). Compiled 2026-10-20 from a literature check; every claim
carries the tag below saying how far it was verified. Each point gives the fact, the number, and the source, with a verification tag.

**Verification tags**

- **[V-text]**: I read the primary text, or a faithful full-text copy of it, and the quote or number comes from that text.
- **[V-abstract]**: the abstract (via Europe PMC/PubMed) or a database record (RCSB PDB, UniProt, NIST) confirms the claim.
- **[V-biblio]**: only the citation details (authors, journal, volume, pages, DOI) are confirmed, via Crossref or RCSB. I did not read the content.
- **[UNVERIFIED]**: I found no primary or authoritative confirmation. Do not publish without checking.
- **[DERIVED]**: my own arithmetic from the verified inputs named. It is not a literature value.

---

## Corrections to the brief's starting assumptions (read first)

1. **PDB 1EMA is not wild-type GFP.** It is the S65T mutant: the chromophore is Thr65-Tyr66-Gly67. Wild-type GFP is PDB 1GFL. See §6.
2. **GFP emission is not "509 nm" for wild type.** Tsien (1998) gives 508 nm (excitation at 395 nm), 503 nm (excitation at 475 nm) and 504 nm (Table 1). The 509–511 nm value belongs to S65T. See §6.
3. **KcsA site S4 is not all backbone carbonyl.** Sites S1–S3 are carbonyl oxygens only. S4 is made of 4 carbonyl oxygens plus 4 Thr75 side-chain hydroxyl oxygens. See §8.
4. **Porphyrin as an "18π annulene" is the textbook picture, and modern ring-current work disputes it.** See §4.
5. **Nucleobases differ in how aromatic they are.** HOMA runs from 0.47 for thymine to 0.92 for adenine. See §4.
6. **The 0.001 vs 0.002 au attribution is mixed in the literature.** Bader et al. 1967 proposed 0.002 e/bohr³. Boyd 1977 motivated 0.001. Bader et al. 1987 is the *conventional* citation for the 0.001 au surface. See §1.
7. **The ESP colour convention is not universal.** ChimeraX uses red for negative. Politzer & Murray's figures use red for *most positive*. See §3.
8. **The α-helix numbers of 3.6 residues per turn and 1.5 Å per residue are not in the 1951 helix paper as quoted.** The original proposal was a 3.7-residue helix. 3.6 residues per turn is the 18-residue/5-turn version. See §9.
9. **The offset of the π-density maximum from the ring plane is unsourced.** I found nothing for 0.5–1 Å. See §4.

---

## 1. The van der Waals surface as the edge of the electron cloud

| Fact | Number | Source | Tag |
|---|---|---|---|
| An atom or molecule has no hard edge. Its "surface" is a chosen contour of electron density. The conventional outer contour for electrostatic-potential work is ρ = 0.001 e/bohr³ | 0.001 e/bohr³ = **0.00675 e/Å³** | Bader RFW, Carroll MT, Cheeseman JR, Chang C (1987) "Properties of atoms in molecules: atomic volumes." *J. Am. Chem. Soc.* **109**(26):7968–7979. doi:10.1021/ja00260a006 | [V-biblio]. Paywalled; I could not read the text |
| The 1987 paper is the standard citation for the 0.001 au surface: "defined as an outer contour of its electronic density [6], typically the 0.001 au contour" (ref. 6 = Bader et al. 1987) | — | Politzer P, Murray JS (2021) "The Neglected Nuclei." *Molecules* **26**:2982. doi:10.3390/molecules26102982 | [V-text] |
| History: "Bader et al. were first to propose an electron density cutoff of 0.002 e bohr⁻³ as the van der Waals boundary of molecules" (citing Bader, Henneker & Cade 1967). "A limiting electron density value of 0.001 e bohr⁻³ was later motivated by Boyd." | 0.002 (1967) → 0.001 (1977) | Rahm M, Hoffmann R, Ashcroft NW (2016) "Atomic and Ionic Radii of Elements 1–96." *Chem. Eur. J.* **22**:14625–14632. doi:10.1002/chem.201602949. Cited works: Bader RFW, Henneker WH, Cade PE (1967) *J. Chem. Phys.* **46**:3341–3363, doi:10.1063/1.1841222; Boyd RJ (1977) *J. Phys. B* **10**:2283–2291, doi:10.1088/0022-3700/10/12/007 | Rahm: [V-text]. 1967 and 1977 papers: [V-biblio] |
| **Match to vdW radii.** Free-atom radii at the 0.001 e/bohr³ contour versus Alvarez's crystallographic vdW radii (89 elements): on average **0.01 Å smaller (0.5 %)**, SD **0.21 Å** (0.16 Å without Group 1); r² = 0.769 (0.856 without the alkali metals). Versus Batsanov's 61 radii: r² = 0.876 (Li, Na, K, Rb and Cs omitted), but the 0.001 contour radii are **28 % larger** on average. For the noble gases, a fit forced through zero gives slope 1.01 and r² = 0.986 | see left | Rahm et al. 2016 (above) | [V-text] |
| Carbon's 0.001 e/bohr³ radius is **1.90 Å**. Half the graphite interlayer spacing (3.35 Å) is **1.68 Å**. The difference is attributed to dispersion attraction. | 1.90 vs 1.68 Å | Rahm et al. 2016 | [V-text] |
| The "best" cutoff is still debated: a 2024 study proposes 0.0016 a.u. | 0.0016 a.u. | Alibakhshi A, Schäfer L (2024) *Nat. Commun.* **15**:6086. doi:10.1038/s41467-024-50408-8 | [V-biblio]. The value comes from a search snippet only, so treat it as [UNVERIFIED] |
| The 0.001 au envelope encloses about 98–99 % of the electron density and matches gas-phase virial and viscosity sizes | 98–99 % | Said to be in Bader's *Atoms in Molecules* (1990), p. 183, but the only source is a CCL forum quote | **[UNVERIFIED]** |
| Bondi's van der Waals radii | H 1.20, C 1.70, N 1.55, O 1.52, P 1.80, S 1.80 Å | Bondi A (1964) "van der Waals Volumes and Radii." *J. Phys. Chem.* **68**(3):441–451. doi:10.1021/j100785a001 | Citation: [V-biblio]. **Values [UNVERIFIED]** against the primary (they are consistent across secondary tables) |
| Bondi's H radius is about 0.1 Å too long for organic crystal contacts (≈1.1 Å) | ~1.1 Å | Rowland RS, Taylor R (1996) *J. Phys. Chem.* **100**:7384–7391. doi:10.1021/jp953141+ | Citation: [V-biblio]. **Finding [UNVERIFIED]** (search snippet only) |

**Depiction:** a vdW or isodensity surface is a *convention*. It is one contour of a density that decays smoothly and roughly exponentially (Rahm 2016, Fig. 1). A soft, translucent falloff is more honest than a hard shell. If a hard surface is drawn, the caption should name the cutoff or radius set used.

**Caption-safe:** "The surface marks where the electron cloud thins to about a thousandth of an electron per cubic bohr. The cloud has no sharp edge, so the line is a convention."

---

## 2. Space-filling (CPK) models depict van der Waals spheres

| Fact | Number | Source | Tag |
|---|---|---|---|
| Corey–Pauling wooden models: "Van der Waals radii, bond radii, and bond angles have the dimensions generally found in crystals of amino acids, peptides and other organic compounds." The scale is 1 in. = 1 Å (and 1 in. = 2 Å for the flexible plastic version) | 1 in. = 1 Å | Corey RB, Pauling L (1953) "Molecular Models of Amino Acids, Peptides, and Proteins." *Rev. Sci. Instrum.* **24**(8):621–627. doi:10.1063/1.1770803 | [V-text] (NLM OCR full text) |
| Caveat in the same paper: buried atoms are *not* vdW spheres. For the tetrahedral carbon, "the radius of the ball (1.25 in.) bears no relationship to the van der Waals radius (1.5 A)". In the exposed direction of a double-bonded C, "the radius of the ball (1.50 in.) corresponds to the van der Waals radius of carbon." Hydrogen has a bond radius of 0.30 Å and a vdW radius of 1.20 Å, and the vdW radius is reduced at large angles to the bond | C 1.5 Å; H 1.20 Å | Corey & Pauling 1953 | [V-text] |
| Koltun's CPK units: "the atom units are formed to represent the Van der Waals radii of the represented atoms, and their bond radii, to suitable scale; the preferred scale being a scale of 1.25 centimeters per angstrom unit." Each unit is a sphere of vdW radius "truncated normal to the respective bond axes at distances … corresponding to the normal bond radii concerned, less a constant" | 1.25 cm/Å | Koltun WL, US Patent 3,170,246, "Space filling atomic units and connectors for molecular models", filed 23 Feb 1962, issued 23 Feb 1965. https://patents.google.com/patent/US3170246 | [V-text] |

**Depiction:** a space-filling model shows the *contact envelope* (vdW spheres truncated at bond radii). It does not show nuclei, and it does not show where the electrons "are". The radii are crystal-contact radii, which scatter by about ±0.2 Å against density-based radii (§1).

---

## 3. Electrostatic-potential colouring of molecular surfaces

**UCSF ChimeraX `coulombic` documentation.** URL: https://www.cgl.ucsf.edu/chimerax/docs/user/commands/coulombic.html. Page footer: "UCSF Resource for Biocomputing, Visualization, and Informatics / January 2026". **[V-text]** Exact quotes:

- Colour convention: "with default coloring ranging from **red for negative potential through white to blue for positive potential**"
- Formula: "φ = Σ [qi / (εdi)]"
- **Units:** "The resulting potential is in units of **kcal/(mol·e) at 298 K**."
- **Dielectric:** "By default, distDep true and dielectric 4.0 are used: **ε = 4d**". With `distDep false`, ε is the constant given by the `dielectric` option.
- **Range:** "The default palette-options for coloring are : **palette red-white-blue range -10,10**". In the stated units this is ±10 kcal/(mol·e).
- **Offset:** "The default of **1.4 Å** is typically used for coloring a molecular surface by electrostatic potential." "An offset of 1.4 Å approximates the solvent-accessible surface". The potential shown is therefore evaluated 1.4 Å *outside* the drawn surface.
- **Charges:** "Partial atomic charges are looked up for standard residues". For nonstandard residues they are "calculated by Antechamber according to the chargeMethod option (default am1-bcc)".
- [DERIVED] At 298 K, kT ≈ 0.592 kcal/mol, so ±10 kcal/(mol·e) ≈ ±16.9 kT/e. This matters if you compare with tools that use kT/e.

**The convention is not universal.** Politzer & Murray (2021, *Molecules* 26:2982, above) give their colour ranges as "red, more positive than 15; yellow, between 15 and zero; green, between zero…" (kcal/mol), mapped on the 0.001 au isodensity surface. **[V-text]** In their figures red is *positive*.

**Depiction and captions:** always state the convention, the range and units, the model (Coulombic with ε = 4r is a screening approximation, not Poisson–Boltzmann and not quantum ESP), and the surface or offset. Include a colour key.

---

## 4. π-electron delocalization and aromaticity

| Fact | Number | Source | Tag |
|---|---|---|---|
| Benzene: "each carbon has a p orbital perpendicular to the plane of the six-membered ring"; "all six π electrons are free to move about the entire ring"; "all its carbon–carbon bonds have the same length—139 pm" | C–C 139 pm | McMurry J, *Organic Chemistry* (OpenStax, 2023), §15.2. https://openstax.org/books/organic-chemistry/pages/15-2-structure-and-stability-of-benzene | [V-text] |
| Hückel rule: "a molecule is aromatic only if it has a planar, monocyclic system of conjugation and contains a total of 4n + 2 π electrons" | 4n+2 | OpenStax *Organic Chemistry* §15.3 | [V-text] |
| Physical evidence that the π density sits above and below the ring: benzene's experimental quadrupole moment is negative along the ring axis, so the faces are negative and the rim is positive. C₆F₆ has the opposite sign | C₆H₆ Θzz = **−8.70 ± 0.5 D·Å**; C₆F₆ Θzz = **+9.50 D·Å** | NIST CCCBDB, "Experimental Quadrupoles", https://cccbdb.nist.gov/quadlistx.asp, citing Battaglia MR, Buckingham AD, Williams JH (1981) *Chem. Phys. Lett.* **78**:421. doi:10.1016/0009-2614(81)85228-1 | NIST: [V-text]. 1981 paper: [V-biblio] via NIST |
| **Offset of the π-density maximum from the ring plane** | no sourced number | none found | **[UNVERIFIED]**. The 0.5–1 Å guess is not supported by anything I found |
| Back-of-envelope estimate (not a source): a single Slater-type C 2p orbital with Clementi–Raimondi Z_eff = 3.136 (ζ = 1.568 bohr⁻¹) has its peak density along the p axis at z = 1/ζ | ≈0.64 bohr ≈ **0.34 Å** | [DERIVED]. Z_eff from the Wikipedia "Effective nuclear charge" table, citing Clementi E, Raimondi DL (1963) *J. Chem. Phys.* **38**:2686, doi:10.1063/1.1733573 | [DERIVED]. The Z_eff value was not checked against the primary |
| The *contact* half-thickness of an aromatic sheet, which is not the density maximum | **1.68 Å** (half of graphite's 3.35 Å) | Rahm et al. 2016 | [V-text] |
| **Porphyrin/heme, textbook view:** an 18-π-electron (4n+2, n = 4) [18]annulene-type pathway | 18 π | Vogel E (1993) "The porphyrins from the 'annulene chemist's' perspective." *Pure Appl. Chem.* **65**(1):143–152. doi:10.1351/pac199365010143 | [V-biblio] only. Do not attribute specific content to it |
| **Porphyrin, current view:** the macrocycle is strongly aromatic, but "All conjugated chemical bonds participate in the current transport independently of the formal number of π electrons"; "The traditional 18π [18]annulene with inactive NH bridges is not how the ring-current flows around the macroring." | ring current 1.5–2.5× benzene; porphin ≈ **27 nA/T** | Fliegl H, Sundholm D (2012) *J. Org. Chem.* **77**:3408–3414. doi:10.1021/jo300182b | [V-abstract] |
| Also: "porphyrinoid aromaticity is not due primarily to the macrocyclic π conjugation of the corresponding annulene perimeters". The appended 6π pyrrole rings contribute more per atom | — | Wu JI, Fernández I, Schleyer PvR (2013) "Description of Aromaticity in Porphyrinoids." *J. Am. Chem. Soc.* **135**:315–321. doi:10.1021/ja309434t | [V-abstract] (free-base porphyrinoids, not Fe-heme specifically) |
| **Nucleobases** are aromatic heterocycles, but to different degrees: HOMA 0.466 (thymine) to 0.917 (adenine) at B3LYP. "Aromaticity of the bases decreases markedly with an increase of the number of double-bond C=X (X = N, O) substituents". Watson–Crick H-bonds *increase* ring aromaticity | HOMA 0.47–0.92 | Cyrański MK, Gilski M, Jaskólski M, Krygowski TM (2003) *J. Org. Chem.* **68**:8607–8613. doi:10.1021/jo034760e | [V-abstract] |
| "Pyrimidine … is the parent ring system in cytosine, thymine, and uracil"; pyridine and pyrrole each have six π electrons | 6 π | OpenStax *Organic Chemistry* §15.5 | [V-text] |

**Depiction:** draw π density as two continuous rings above and below the faces. There is no sourced value for how far out the peak lies; a single-orbital estimate ([DERIVED]) puts it at about 0.3 Å. The contact surface is about 1.7 Å out ([V-text], Rahm 2016). Benzene's faces are electron-rich (negative). For heme, say "delocalized over the whole conjugated macrocycle" rather than drawing a single 18-atom loop. Do not draw pyrimidine bases (T, U, C) with the same "full aromatic ring" emphasis as the purines.

---

## 5. DNA base stacking

| Fact | Number | Source | Tag |
|---|---|---|---|
| "There is a residue on each every 3.4 A. in the z-direction. We have assumed an angle of 36° between adjacent residues in the same chain, so that the structure repeats after 10 residues on each chain, that is, after 34 A." "The distance of a phosphorus atom from the fibre axis is 10 A." | rise 3.4 Å; 10 bp/turn (fibre model) | Watson JD, Crick FHC (1953) *Nature* **171**:737–738. doi:10.1038/171737a0 | [V-text] (Exploratorium reprint) |
| Helical repeat in solution: "10.4 base pairs per turn under physiological conditions, with an estimated probable error of +/- 0.1", "significantly different from the value 10.0 base pairs per turn for the B form fiber structure" | **10.4 ± 0.1** bp/turn | Wang JC (1979) *PNAS* **76**:200–203. doi:10.1073/pnas.76.1.200 | [V-abstract] |
| Measured with DNase I on surface-bound DNA | **10.6 ± 0.1** bp/turn | Rhodes D, Klug A (1980) *Nature* **286**:573–578. doi:10.1038/286573a0 | [V-abstract] |
| "base-stacking is the main stabilizing factor in the DNA double helix. A•T pairing is always destabilizing and G•C pairing contributes almost no stabilization." | mean ΔG_BP(A•T) = **+0.57**, ΔG_BP(G•C) = **−0.11** kcal/mol (15 mM Na⁺) | Yakovchuk P, Protozanova E, Frank-Kamenetskii MD (2006) *Nucleic Acids Res.* **34**:564–574. doi:10.1093/nar/gkj454 (PMC1360284) | [V-text] |

**Caption-safe:** "Base pairs stack about 3.4 Å apart, roughly 10.5 per turn in solution (10.4–10.6 measured). Stacking between neighbouring bases, more than the hydrogen bonds within a pair, is what holds the helix together thermodynamically." Base pairing still sets the sequence *specificity*.

---

## 6. GFP

| Fact | Number | Source | Tag |
|---|---|---|---|
| "The chromophore is a p-hydroxybenzylideneimidazolinone … formed from residues 65-67, which are Ser-Tyr-Gly in the native protein." | Ser65-Tyr66-Gly67 | Tsien RY (1998) "The Green Fluorescent Protein." *Annu. Rev. Biochem.* **67**:509–544. doi:10.1146/annurev.biochem.67.1.509 | [V-text] |
| Wild type: "a major excitation peak at 395 nm that is about three times higher in amplitude than a minor peak at 475 nm. In normal solution, excitation at 395 nm gives emission peaking at 508 nm, whereas excitation at 475 nm gives a maximum at 503 nm." Table 1: excitation 395–397 / 470–475 nm, emission **504 nm** (QY 0.79) | 395/475 → 508/503 nm | Tsien 1998 | [V-text] |
| Only the chromophore produces the visible fluorescence, and it needs the barrel: "Denatured GFPs or small proteolytic fragments carrying the chromophore are essentially totally nonfluorescent". Ormö et al.: the chromophore "requires the native protein fold for both formation and fluorescence emission" | — | Tsien 1998; Ormö et al. 1996 | [V-text] / [V-abstract] |
| **PDB 1EMA = S65T GFP**: "The structure of Thr65 GFP has been determined at 1.9 angstrom resolution"; "11-stranded beta barrel with a coaxial helix, with the chromophore forming from the central helix". RCSB lists the modification as "65 - 67 REPLACED BY CRO, Q80R", where CRO's parent residues are THR-TYR-GLY | 1.9 Å; Thr65-Tyr66-Gly67 | Ormö M, Cubitt AB, Kallio K, Gross LA, Tsien RY, Remington SJ (1996) *Science* **273**:1392–1395. doi:10.1126/science.273.5280.1392; RCSB 1EMA | [V-abstract] + RCSB |
| S65T spectra: the 395 nm peak is suppressed and the anion peak is "shifted to 489-490 nm". Table 1: excitation **489 nm**, emission **509–511 nm** (QY 0.64) | 489 → 509–511 nm | Tsien 1998 | [V-text] |
| Wild-type structure: PDB **1GFL**, 1.9 Å (RCSB lists only Q80R) | 1.9 Å | Yang F, Moss LG, Phillips GN Jr (1996) *Nat. Biotechnol.* **14**:1246–1251. doi:10.1038/nbt1096-1246 | [V-abstract] + RCSB |

**Caption-safe (when using 1EMA):** "GFP (S65T variant, PDB 1EMA). Only the chromophore at the centre of the barrel, made from three of the protein's own amino acids, emits the green light. The barrel shields it, and without the barrel it goes dark." Do not label 1EMA as wild type, and do not quote 395/475 nm for it.

---

## 7. Nucleosome

| Fact | Number | Source | Tag |
|---|---|---|---|
| **1KX5**: nucleosome core particle with "a 147 base pair, defined-sequence DNA … at 1.9 Å resolution"; "Over 3000 water molecules and 18 ions"; "Water molecules residing in the minor groove play an important role in facilitating insertion of arginine side-chains"; bound anions "damp the electrostatic interaction between the histone proteins and the DNA" | 147 bp; 1.9 Å in the title, **1.94 Å** in RCSB; both strands 147 nt | Davey CA, Sargent DF, Luger K, Maeder AW, Richmond TJ (2002) *J. Mol. Biol.* **319**(5):1097–1113. doi:10.1016/S0022-2836(02)00386-8 | [V-abstract] + RCSB |
| The first core-particle structure: 146 bp, 2.8 Å, PDB **1AOI** | 146 bp; 2.8 Å | Luger K, Mäder AW, Richmond RK, Sargent DF, Richmond TJ (1997) *Nature* **389**:251–260. doi:10.1038/38444 | [V-abstract] + RCSB |
| In 1KX5 there are "14 minima in minor groove width corresponding to regions where the DNA bends so as to wrap around the histone core". The electrostatic potential differs by about 6 kT/e between the narrowest and widest grooves. "arginines are found in 9 of the 14 minima" under a <6 Å criterion, and the paper notes that all 14 are contacted by arginines (per Davey 2002). Narrow minor grooves "strongly enhance the negative electrostatic potential" | 14 sites; 9/14 (<6 Å); ~6 kT/e | Rohs R, West SM, Sosinsky A, Liu P, Mann RS, Honig B (2009) *Nature* **461**:1248–1253. doi:10.1038/nature08473 (PMC2793086) | [V-text] |
| "The surface of the histone octamer … is decorated with positively charged amino acids"; "These interact strongly with the negatively-charged phosphate groups on the DNA" | — | Goodsell DS, PDB-101 Molecule of the Month: Nucleosome (July 2000). doi:10.2210/rcsb_pdb/mom_2000_7 | [V-text] |
| Charge bookkeeping for the 1KX5 octamer (2 × H3, H4, H2A, H2B; full sample sequences including tails) | **220 Lys+Arg vs 74 Asp+Glu**, net ≈ **+146**, against ≈ **292** DNA phosphates (2 × 146 linkages) | [DERIVED] from the RCSB 1KX5 entity sequences (per copy: H3 K13/R18, H4 K11/R14, H2A K13/R13, H2B K20/R8). His and termini are ignored | [DERIVED] |

**Depiction:** the contact is electrostatic and hydrated. Show arginines reaching into the minor groove where it faces the octamer, about every 10 bp, with water between protein and DNA (bridging waters about equal in number to direct H-bonds, per Davey 2002). The octamer's net positive charge offsets only about half of the DNA phosphate charge [DERIVED]. Ions and the histone tails do the rest; that last point is not verified here.

---

## 8. KcsA selectivity filter

| Fact | Number | Source | Tag |
|---|---|---|---|
| **1K4C**: KcsA–Fab complex in high K⁺, 2.0 Å. "Carbonyl oxygen atoms within the selectivity filter form a very similar square antiprism around each K+ binding site, as if to mimic the waters of hydration." In the cavity a K⁺ sits "in a square antiprism of water molecules" | 2.0 Å | Zhou Y, Morais-Cabral JH, Kaufman A, MacKinnon R (2001) *Nature* **414**:43–48. doi:10.1038/35102009 | [V-abstract] + RCSB |
| The filter is "a linear queue of four equal-spaced ion-binding sites spanning a distance of 12Å. Each site is formed of eight oxygen atoms from the protein. The first three sites … exclusively main-chain carbonyl oxygen atoms. The fourth site, closest to the intracellular side, is made of four main-chain carbonyl oxygen atoms and four threonine side-chain hydroxyl oxygen atoms." In conduction, "a pair of K ions switch between energetically balanced 1,3 and 2,4 configurations" | 4 sites, 8 O each, 12 Å | Zhou M, MacKinnon R (2004) *J. Mol. Biol.* **338**:839–846. doi:10.1016/j.jmb.2004.03.020 | [V-abstract] |
| Signature sequence TVGYG = KcsA residues **75–79** | 75–79 | UniProt P0A334 (KcsA, 160 aa) | [V-text] (sequence) |
| "Main chain carbonyl oxygen atoms from the K+ channel signature sequence line the selectivity filter, which is held open by structural constraints to coordinate K+ ions but not smaller Na+ ions"; "two K+ ions about 7.5 angstroms apart" | 12 Å filter; 7.5 Å ion spacing | Doyle DA, Morais Cabral J, Pfuetzner RA, Kuo A, Gulbis JM, Cohen SL, Chait BT, MacKinnon R (1998) *Science* **280**:69–77. doi:10.1126/science.280.5360.69 | [V-abstract] |

**Depiction:** show *two* dehydrated K⁺ ions in the filter (1,3 or 2,4) with waters between them, not four ions at once. Four ions in the crystal map is a time and ensemble average. Each ion sits in a cage of 8 oxygens (4 subunits × 2). At the innermost site, the oxygens include Thr75 hydroxyls.

---

## 9. Protein cartoon (ribbon) representation and the α-helix

| Fact | Number | Source | Tag |
|---|---|---|---|
| Ribbon convention: "Spiral ribbons represent α-helices and arrows represent strands of β sheet." (Fig. 1 caption) | — | Richardson JS (1981) "The Anatomy and Taxonomy of Protein Structure." *Adv. Protein Chem.* **34**:167–339. doi:10.1016/S0065-3233(08)60520-3. Web transcription: https://www.boscoh.com/longform/anatax (a third-party mirror; its credits name the Richardson lab as the transcribers. The official host, kinemage.biochem.duke.edu/teaching/anatax/, refused connections when checked) | Citation: [V-biblio]. Quote: [V-text] via the transcription |
| Same source: "the α-helix has 3.6 residues per turn"; "The rise per residue along the helix axis is 1.5Å." | 3.6 res/turn; 1.5 Å/res (→ 5.4 Å pitch, [DERIVED]) | Richardson 1981 (transcription) | [V-text] via transcription |
| Original proposal: a **3.7-residue** helix; "a translation per residue of 1.47 A corresponds to a hydrogen-bond distance 2.73 A". The 18-residue/5-turn helix (that is, 3.6 per turn): "a translation of 1.50 A per residue (5.40 A per turn, 27.0 A identity distance along the axis)" | 3.7 (→3.6); 1.47–1.50 Å; 5.40 Å/turn | Pauling L, Corey RB (1951) "Atomic Coordinates and Structure Factors for Two Helical Configurations of Polypeptide Chains." *PNAS* **37**(5):235–240. doi:10.1073/pnas.37.5.235 | [V-text] |
| The α-helix proposal itself | — | Pauling L, Corey RB, Branson HR (1951) *PNAS* **37**(4):205–211. doi:10.1073/pnas.37.4.205 | [V-biblio] |
| Later methods paper on schematic drawings | — | Richardson JS (1985) "Schematic drawings of protein structures." *Methods Enzymol.* **115**:359–380. doi:10.1016/0076-6879(85)15026-3 | [V-biblio] |

**Depiction:** a ribbon is a hand-designed abstraction of the backbone path. It hides side chains and the space-filling volume. Captions should say "cartoon" or "ribbon", and the cartoon should not be shown as if it were the molecule's physical surface.

---

## Still UNVERIFIED (do not publish as fact)

- The content of Bader et al. 1987 itself, including the "98–99 % of electrons enclosed" claim and the gas-phase size agreement.
- The individual Bondi (1964) radius values (H 1.20, C 1.70, N 1.55, O 1.52, P/S 1.80 Å). The citation is verified; the numbers come only from secondary tables.
- Rowland & Taylor (1996) H ≈ 1.1 Å.
- Alibakhshi & Schäfer (2024) 0.0016 a.u. (citation verified, value from a snippet).
- Any literature value for the height of the π-density maximum above an aromatic ring plane. The 0.34 Å figure is my own estimate.
- The content of Vogel 1993 (citation verified only).
- "Histones are lysine/arginine-rich" as a sourced statement. The PDB-101 quote says "positively charged amino acids"; the residue counts above are [DERIVED].
