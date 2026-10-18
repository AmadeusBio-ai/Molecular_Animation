# How molecules move, and how the films show it

This is the motion schematic behind the films' thermal and Brownian motion. Each row is a real motion with a measured or hydrodynamic rate, the time it takes, and how a film shows it. The code is `molanim/dynamics.py` (pure numpy, tested in `tests/test_dynamics.py`), `molanim.membrane.lipid_handles` and three geometry-node groups in `molanim/blender/groups.py`:
- `dynamics`: normal modes and side-chain turns from frame tables;
- `lipid_motion`: lipids as molecules;
- `chain_motion`: a worm-like double helix.

For a single protein or nucleic acid, `dynamics.protein_motion` packages the protein rows below (normal modes, side-chain turns, ligands riding on the residue they bond to) for any structure; the shot template uses it.

The two films it was built for are the channelrhodopsin case study (`examples/channelrhodopsin/`, version 3) and ART, a film on the reverse transcriptase, RNA array and partner protein of a phage retroelement made with the same framework (not published in this repository). Their numbers are quoted below.

None of it is a simulation of the molecules shown. The motion is labelled illustrative, but its amplitudes and speeds come from the sources below.

## Rules

1. **One clock per film.** Pick how much molecular time one second of film shows: 1 ns for the channelrhodopsin membrane, 5 ns for the ART cytoplasm. Every motion runs on that clock, so relative speeds are right: small things move faster than large ones, and lipids faster than proteins. State the clock in the record, and on screen where there is room (Jantzen, McGill & Jenkinson 2024 recommend a timescale indicator).
2. **Each frame is an exposure.** A frame shows the average of the motion over its exposure, a few frames of clock time, as MD movies are window-averaged (VMD's smoothing). Motion much faster than that averages out. Its residue is `dynamics.exposure_factor`, which for a box window is √(2(τ/T)²(T/τ − 1 + e^(−T/τ))). This covers bond vibrations, methyl spins, chain isomerisations and BI/BII flips. Motion much slower than the film looks frozen, such as the DNA's overall shape or a membrane protein's rotation. What you see is the band between.

   The window also sets how free Brownian motion reads, because a diffusing path has no smooth velocity. Through a box window, each frame's edges add a fresh random kick to the velocity. ART version 2 (take-02) used a 3-frame box. In its close-up, the tumbling RT's rotation went 1.3 → 1.6 → 3.1 → 2.7 → 1.0 → 0.6° per frame within six frames: the far end's screen speed jumped from 1 to 26 px a frame and back. Velocity changed by two-thirds of itself every frame, and `pipeline.py motion` flagged 2× steps at frames 555–557. The fix is `shutter='triangle'` (a box of half the width applied twice) over a longer window. ART now uses 16 frames (3.3 ns). The far end's change of velocity per frame fell from 0.67 to 0.3 of its step, and rotation per frame from 1.26° to 0.8° (median). Displacement per film-second fell by less than 10 %, because averaging hardly changes long-time motion. Channelrhodopsin has no free tumbling (the frame follows the protein) and keeps a 2-frame box; its ions use 6 frames.
3. **Molecules move as molecules.** The motion is built in layers:
   - whole bodies diffuse and tumble;
   - inside them, collective normal modes move residues together;
   - side chains, lipid chains and head groups turn about bonds;
   - covalent geometry is kept (bond lengths to first order, exactly for turns about bonds).

   Never move atoms by independent noise: that was version 2's mistake (below).
4. **Size and shape set the speed.** D_t ∝ 1/r and D_r ∝ 1/r³, and elongated molecules tumble end over end far more slowly than spheres (Perrin). Crowding slows translation more than rotation.
5. **Tether for composition, and say so.** Free molecules diffuse at their true short-time rate but are held near their editorial places by an Ornstein–Uhlenbeck tether (RMS 9 Å, 20°). Over a few seconds of film this is free diffusion; over the whole film the molecule stays in frame.
6. **Motion never starts or stops by itself** (Jantzen et al. 2024). The one exception is a labelled timescale change: channelrhodopsin's clock stops for the "within a picosecond" twist, because on that timescale nothing else moves.
7. **Loops repeat the physics.** With `period` (the loop's length in clock time) every process is drawn from the same spectrum on the loop's harmonics (`dynamics.periodic_ou`), so frame N + 1 equals frame 1 without any noise trick. A motion slower than the loop cannot repeat and freezes into an offset: an 8 s loop at 1 ns/s shows 8 ns, and in the template's 8 s GFP loop the median backbone RMSF is 0.09 Å.

## The schematic

Clock columns give what the film shows: RMS amplitude and correlation time, after exposure averaging.

### Proteins

| Motion | Physical value | Source | Shown as | ChR (1 ns/s) | ART (5 ns/s) |
|---|---|---|---|---|---|
| Bond vibration, methyl spin | 0.05 Å, fs; ps | — | averaged out | — | — |
| Side-chain χ1/χ2 within a rotamer well | ≈ 20° rms; rotamer jumps 22 ps – 8 ns, ~20× faster at the surface | Li et al. 2015 JACS (NMR, GB3); Scouras & Daggett 2011 Protein Sci | Ornstein–Uhlenbeck turns about CA–CB and CB–CG. Bonds exact; rotamer jumps not shown | 8° (buried) – 18° (exposed), τ 1.5 – 0.3 ns | RT only, same rates; the 3.3 ns window shows 6–8.5° |
| Collective motion | elastic network: mode variance ∝ kT/λ, overdamped τ ∝ 1/λ | Atilgan et al. 2001 Biophys J; cutoff 13–15 Å (Eyal 2006) | Cα network, 15 Å, backbone springs ×10. Each atom blends its own and the neighbouring Cα's displacement | 30 modes, mean Cα RMSF 0.8 Å, softest τ 50 ns | RT 1.0 Å / 50 ns; partner 2.0 Å / 30 ns (low pLDDT) |
| Amplitude scale | C1C2 TM backbone RMSD 0.5 Å over 120 ns; ChR2 helices 1.1 Å over 4 µs; 9GO1 B = 57 Å² (≤ 1.47 Å) | VanGordon et al. 2017; Ardevol & Hummer 2018; this structure | calibrates RMSF | film RMSF: backbone 0.28 Å, side chains 0.48 Å (median) | — |
| Membrane-protein diffusion | 1–3 µm²/s; rotation ~15 µs | Ramadurai 2010; Cherry & Godfrey 1981 | negligible on the clock: the frame follows the protein | — | — |

### Lipids (POPC-like)

| Motion | Physical value | Source | Shown as | ChR (1 ns/s) |
|---|---|---|---|---|
| Lateral diffusion | D ≈ 10 µm²/s, caged from 10 ps to 10 ns | Heinemann 2012 Langmuir (FCS); Gaede & Gawrisch 2003 (NMR); Flenner 2009 | own rattle | 1.1 Å, τ 0.3 ns |
| Concerted flow | neighbours move together over ~30 Å; flow patterns last 100s of ns | Rheinstädter 2008 PRL; Falck 2008 JACS; Apajalahti 2010 | a flow field sampled at each lipid's glycerol | 4 Å, τ 20 ns, 30 Å |
| Wobble | D⊥ 1–2 × 10⁸ s⁻¹, cone 38° | Klauda 2008 Biophys J | rigid tilt about the glycerol | 10°, τ 1 ns |
| Axial spin | D∥ 10⁷ – 1.6 × 10⁸ s⁻¹ (8–32° per ns) | Klauda 2008; Essmann & Berkowitz 1999 | rigid turn about the normal | 57°, τ 5 ns |
| Protrusion | ~2.7 Å | Essmann & Berkowitz 1999 | vertical bob | 1 Å, τ 2 ns |
| Chains | S_CD 0.2 on the plateau, 0.02 at the end; trans/gauche lifetimes 40–200 ps | Ferreira 2013 PCCP; Pasenkiewicz-Gierula & Róg 1997 | each chain bends about its ester carbon, growing toward its end; single isomerisations averaged out | 15° at the end, τ 0.5 ns |
| Head group | P–N vector ≈ 80° from the normal, τ 3.7 ns | Gurtovenko 2004; Pasenkiewicz-Gierula 1997 | choline turns about the phosphate | 26°, τ 3.7 ns |
| Annular lipids | hug the protein | — | mobility falls to 0.25 within 4–16 Å of the protein | — |
| Flip-flop | hours to days | Marquardt 2017 | never | — |

### Ions

| Motion | Physical value | Source | Shown as | ChR (1 ns/s) |
|---|---|---|---|---|
| Na⁺ diffusion | D = 1.33 × 10⁻⁹ m²/s (25 °C) | CRC Handbook; Mills 1973 | free diffusion, reflected at the membrane surfaces, kept clear of the moving protein (`particles.brownian`, `keep_clear`). Ions outrun a frame, so they are window-averaged over 6 frames (250 ps) | ~16 Å per s per axis; median step 1.8 Å per frame |
| Na⁺ binding to PC | not specific at sub-molar concentrations (MD force fields overbind) | Catte et al. 2016 PCCP | no binding shown | — |

The channel transits stay an illustrative conducting-state model on their own ("milliseconds") timescale, as labelled.

### Free molecules in cytoplasm (ART)

| Motion | Physical value | Source | Shown as | ART (5 ns/s) |
|---|---|---|---|---|
| Translation, tumbling | Stokes–Einstein(–Debye); checks: lysozyme τc 6–8 ns, GFP 87 µm²/s | Halle & Davidovic 2003 PNAS; Swaminathan et al. 1997 | Perrin prolate ellipsoid from each structure's second moments + 3 Å hydration (Perrin 1934, Koenig 1975), 37 °C; 16-frame triangle window | RT 6.5 Å and 10° per film-second; RNAs 4.6–5.5 Å and 5–8°; partner 6.8 Å and 15° |
| Crowding | short-time translation ≈ 20 % of dilute; long-time GFP 7.7 µm²/s in E. coli; rotation 1.5–3× slower | Roosen-Runge 2011 PNAS; Elowitz 1999; Bellotto 2022; Swaminathan 1997; Chen 2018 | translation ÷ 4, rotation ÷ 2 (no S. aureus data) | — |
| RNA internal | interhelical bends of 20–90° on ns; helices stiff, junctions flexible | Mustoe, Brooks & Al-Hashimi 2014 Annu Rev Biochem | P-atom elastic network, 20 Å cutoff (Pinamonti 2015), P–P springs ×10 | mean P RMSF 2.5 Å, softest τ 60 ns |

### DNA

| Motion | Physical value | Source | Shown as | ART (5 ns/s) |
|---|---|---|---|---|
| Bending | Lp ≈ 50 nm; a band of wavelengths [λ/2, λ] has RMS √(7λ³ / (12 Lp (2π)⁴)) and τ ∝ λ⁴ (10 nm ≈ 0.1 ns, 100 nm ≈ 1 µs) | Baumann 1997 PNAS; worm-like-chain hydrodynamics (`dynamics.wlc_bend`) | base pairs move together across the local frame, 3 wavebands, friction ×2 (cytoplasm) | 150 Å: 1.2 Å / 3.3 ns (window); 300 Å: 4.4 Å / 13 ns; 600 Å: 12.7 Å / 170 ns |
| Twisting | twist persistence 40–100 nm (75 nm used); Barkley–Zimm relaxation | Lipfert 2010; Bryant 2003; `dynamics.wlc_twist` | base pairs turn about the axis | 22° over 200 Å, τ 3.3 ns (window) |
| Base-pair steps | twist 6.3°, roll 5.1°, tilt 3.4° SD; BII flips 110–370 ps | Olson 1998 PNAS; Trieb 2004 | inside the twist and bend fields; flips averaged out | — |
| Base-pair opening | open ~10–100 ns once per ~10 ms | Guéron et al. 1987 Nature | never (≈ 0.1 events per base pair in a film) | — |
| Whole-strand diffusion | ≈ 2.6 µm²/s at 1,480 bp; far slower in cells | Lukacs et al. 2000 JBC | the path stays put | — |

## Version 2's mistake

Channelrhodopsin version 2 moved every atom by its own position-and-time noise: a 6 Å coherent field plus a 3 Hz fine field. Atoms of one molecule moved apart and atoms of neighbouring molecules moved together. Measured on 153 lipids over ten frames, against version 3's motion:

| | Version 2 | Version 3 |
|---|---|---|
| Bond stretch inside lipids, median / p99 | 0.62 / 2.39 Å | 0.04 / 0.35 Å |
| Per-frame step, median | 0.33 Å | 0.33 Å |
| Non-rigid part of the step, median | 0.32 Å | 0.14 Å |
| Close contacts (< 2.2 Å) between different lipids, change from rest | +32 % | +5 to +12 % |

The amount of motion was similar; its structure was wrong. Per-atom noise reads as boiling, and neighbouring lipids merge into foam.

## Sources not verified

The research behind this table was done from abstracts and full texts in October 2026. Some values were seen only in secondary sources and are marked so in the project records:
- the 0.6 ns/kDa rule of thumb;
- the axial lipid spin D∥, which disagrees by 16× between papers;
- the protrusion timescale;
- a typical TM-helix RMSF (the papers report RMSD).
