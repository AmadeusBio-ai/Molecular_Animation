# Channelrhodopsin shot: production record · 2026-10-06

**Status:** delivered 2026-10-06. Rebuilt on the `molanim` framework on 2026-10-07 with identical output (see Checks). Version 2 (thermal motion, website palette) delivered 2026-10-07; version 3 (motion from physics) delivered 2026-10-18 to `delivery/channelrhodopsin-v3/` (take-04, labels-05) and published in release v0.2.0. Version 4 (drawn for the website) delivered 2026-10-21 to `delivery/channelrhodopsin-v4/` (take-01, labels-02; see the last section).

A 21 s scientific illustration for `sources/Nobel_Med_2026.md` (generated with ChatGPT; provenance in `sources/README.md`), direction 1, "The twist that opens a pathway". The brief recommends building this shot first. A photon isomerises retinal in the channelrhodopsin C1C2, the protein rearranges (Lys132 swings to Glu129), and the cation pathway is shown first interrupted, then open in an illustrative conducting-state model. The look is the studio molecular style: atoms as spheres, a pale backdrop, shallow depth of field, a teal protein with an amber chromophore (navy and slate from version 2).

## What was built

| File | Role |
| --- | --- |
| `channelrhodopsin.py` | Shot script. Rebuilds scene `Channelrhodopsin` (written to `channelrhodopsin.blend`) and the label scene `Channelrhodopsin_Labels` (`channelrhodopsin-labels.blend`). Timeline, camera keys, colours and label text are constants at the top. |
| `c1c2.py` | C1C2-specific science, pure numpy (tested in `tests/test_c1c2.py`): state matching with alt-loc B and the +307 renumbering, the Schiff-base bond, the stage frame, the two-stage morph, the pathway and its sites, and the illustrative dilation. |
| `molanim/` (framework) | mmCIF reading and assembly operators (`structure`), the constrained morph (`morph`), the pore profile (`pathway`), the procedural POPC-like bilayer (`membrane`), ion drift/transit motion and clearance (`particles`), camera paths (`timeline`), and the Blender node groups, materials, camera rig and label pass (`molanim.blender`). |
| `molanim.dynamics`, `membrane.lipid_handles`, `groups.dynamics`, `groups.lipid_motion` (version 3) | Thermal motion from physical rates on one clock: normal modes, side-chain turns, lipids as molecules, diffusing Na⁺ (see Version 3). |
| `tools/encode.py` | `--overlay DIR` lays an RGBA frame sequence (the label pass) over the picture. |
| `assets/pdb/9GO1.cif`, `9GO2.cif` | C1C2 dark (2.59 Å) and light-activated (2.70 Å) SMX structures from RCSB. |

## Structural basis (checked numerically at build)

- **States.** 9GO1 is the dark state. 9GO2 carries two conformers: alt A (occupancy 0.7) is identical to the dark model; alt B (0.3) is the activated one, numbered +307 (retinal +300). Dark and light are matched by residue and atom: 2,316 of 2,321 heavy atoms; the five without a light partner keep their dark position. Waters and monoolein are left out.
- **Retinal.** The C12-C13=C14-C15 dihedral is -176° in the dark state and +0.6° in alt B (all-trans to 13-cis). The Lys296 NZ-C15 Schiff-base bond is 1.33 Å in both.
- **Network.** Lys132 NZ to Glu129 OE1 is 9.0 Å dark and 2.66 Å light. Trp262 moves with the retinal: if the twist runs alone, the C20 methyl comes within 1.9 Å of the Trp262 ring.
- **Dimer.** The mate comes from `_pdbx_struct_oper_list` 2 (-x, y, -z+47.2). Its two-fold axis is crystal y, taken as the membrane normal; extracellular is -y (N-terminus side). The bilayer centre is set at crystal y = 33 Å, from the hydrophobic belt (about 19-50 Å) and the aromatic belts (about 16 and 47 Å).
- **Pathway.** Protomer A's pathway (not the dimer interface) is found by a slice-wise free-space search guided by Glu140, Glu136, the central gate (Ser102, Glu129, Asn297) and the inner gate (Glu122, His173, Tyr109). It is then relaxed into a smooth elastic band (89 Å long across a 60 Å span), and the free radius is measured along it. In 9GO2 the free radius falls to about 0 Å (or below) at several points between the vestibules, so the light-activated crystal state is not a continuous pathway. This matches the brief's warning that 9GO2 is an early state, not a conducting one.

## Motion and evidence levels

| Screen time | What moves | Evidence level (also the on-screen tag) |
| --- | --- | --- |
| 0-4 s | Wide section of the dimer in a bilayer; photons (wave packets) arrive from the extracellular side; blue light | Structure: 9GO1. Photons and light: symbolic |
| 4-7 s | Camera dives into protomer A; a camera-aimed cutaway opens to the retinal pocket | 9GO1 |
| 7-10.5 s | Photon absorbed (flash), all-trans to 13-cis with Trp262 repacking; ghost of the dark retinal for comparison | Illustrative morph between 9GO1 and 9GO2 coordinates |
| 11-14.5 s | Lys132 swings to Glu129; salt-bridge marker appears | Endpoint: 9GO2 alt B; path: illustrative morph |
| 15-17 s | Section through the pathway; gates in element colours; cavity shown as separate pockets | 9GO2 free-radius profile |
| 17-21 s | Pockets join; 27 lining residues step back rigidly (at most 3.1 Å) so the line has ~2 Å free radius; Na⁺ ions cross with stop-and-go motion | Illustrative conducting-state model |

- **Morph.** This is not a trajectory. Each snapshot is the linear interpolation, relaxed by position-based projection: bond lengths and angles follow their interpolated values, 1-4 distances are kept within the retinal unit, and non-bonded contacts are kept apart. Stage 1 (12 steps) moves the retinal, the Lys296 side chain and Trp262. Stage 2 (12 steps) moves the remaining 650 atoms that shift more than 0.5 Å. The retinal dihedral turns monotonically (-176, -178, 180, 175, 164, 138, 98, 64, 37, 19, 10, 4, 1°). The worst transient bond-length deviation is 0.15 Å in stage 1 and 0.22 Å in stage 2. Snapshots are absolute shape keys, so every representation (spheres, sticks, salt-bridge marker) follows one coordinate source.
- **Ions.** Ions dwell at sites near Glu140, Glu136, Glu129 and Glu122 for irregular times (5-16 frames). They never share a site with the ion ahead, and they jitter laterally by up to 0.3 Å. Hops average at most 1.4 Å per frame. An offset steering pass (`keep_clear`) keeps every ion centre at least 1.70 Å (ion radius 1.35 + 0.35) from each rendered atom surface; until an ion first touches an atom its track is unchanged. The motion is illustrative: there is no simulation, and the rate is not physiological.
- **Timescales on screen.** "Within a picosecond" for the isomerisation, "microseconds" for the early light-activated state, "milliseconds" for channel opening. They are labels, not a running clock.

## Reproduce

```
python pipeline.py build channelrhodopsin                                  # both scenes, ~70 s
python pipeline.py render channelrhodopsin --take take-04                  # ~2.7 h on an RTX 5060 Ti
python pipeline.py render channelrhodopsin --overlay --take labels-05     # ~3 min
python pipeline.py deliver channelrhodopsin                                # the takes named in shots.json
```

These are version 3's take names, which `shots.json` names; if those folders already exist, render into new ones and update `shots.json`. In version 1 the build took about 25 s, and the delivered take-02 is take-01 frames 1-395 plus a re-render of 396-504 (`--frames 396-504` into a new take) after the ion-clearance and dilation fix. That fix changes nothing before the pathway opens: the re-rendered frames 396-409 match take-01 to within 1/255, with no pixel differing by more than 2. A full render from scratch gives the same picture. `labels-03` pairs with take-02 (the Na⁺ pointer follows the adjusted ion).

## Checks

- **Build.** Headless build takes about 25 s; 494k lipid atoms and 2 × 2,321 protein atoms. Two consecutive builds in the live Blender leave no `.001` duplicates and no `CHR_`/`CHRL_` orphans. The user's other scenes are untouched. The cleanup repeats until stable, because text curves hold materials and node groups nest.
- **Timing, evaluated from the shape keys in Blender.** Retinal C12-C13=C14-C15: -176° through frame 180, 98° at 204, 9° at 216, 1° from 228. Lys132 NZ-Glu129 OE1: 9.01 Å through 262, 6.13 Å at 290, 2.66 Å from 318.
- **Ions.** Smallest gap from an ion centre to a rendered atom surface over all frames: 1.70 Å (the target). Largest step 2.11 Å/frame; largest change of step 0.55 Å/frame, the same as the unconstrained path. (Take-01 failed this check: gaps went down to 0.2 Å near frames 436-460, so ions clipped into atoms. That is why the open section was re-rendered.)
- **Motion of the picture.** Frame-to-frame mean |diff| was measured at 480×270 over all 504 frames. No step exceeds 2× its local median except the absorption flash (frames 172-175, intended) and the ghost fading in (231-236). Large absolute steps belong to camera moves: the dive peaks at 30/255 around frame 120 (a steady 3-4 % zoom per frame, checked frame by frame), and the network move and pull-back peak at about 24. The take-01/take-02 seam (395→396) continues the surrounding trend (12.7, 11.0, 9.5, 7.8). Flicker probe: a static backdrop patch changes by about 1/255 per frame at 128 samples.
- **Labels.** The labels are a separate EEVEE pass with a soft contrasting halo; ink and halo switch together at shot changes. Decoded frames from the delivered MP4 were checked at frames 1, 70, 100, 150, 241, 330, 400, 446 and 470: the alpha composite is correct, and pointers sit on Retinal, Lys296, C13=C14, Trp262, the dark-state ghost, Lys132, Glu129, the central and inner gates, and a Na⁺ ion. Na⁺ renders with a true superscript. In the pathway shot, tags move to the top left, clear of the protein.
- **Delivery** (`delivery/channelrhodopsin/`, checked by `tools/encode.py` with ffprobe `-count_frames`):

  | File | Codec | Frames | Duration | Size |
  |---|---|---|---|---|
  | `channelrhodopsin.mp4` (labelled) | H.264 | 504 | 21.0 s | 18.4 MB |
  | `channelrhodopsin.webm` (labelled) | VP9 | 504 | 21.0 s | 10.1 MB |
  | `channelrhodopsin-clean.mp4` | H.264 | 504 | 21.0 s | 17.5 MB |
  | `channelrhodopsin-clean.webm` | VP9 | 504 | 21.0 s | 8.9 MB |

  All are 1920×1080 at 24 fps. Posters (clean): `-poster-wide.png` (frame 70), `-poster-retinal.png` (204, mid-twist), `-poster-channel.png` (470).
- **README clip** (2026-10-07). `channelrhodopsin-readme.mp4` is the labelled film re-encoded from take-02 and labels-03 to fit GitHub's 10 MB attachment limit: H.264 High, CRF 21, preset `veryslow`, faststart, 504 frames, 21.0 s, 9.06 MB. Against the PNG composite its PSNR is 46.5 dB mean and 44.0 dB minimum over all frames, and decoded frame 204 was inspected. It was uploaded to GitHub as an attachment and embedded in the top-level README until version 3's clip replaced it on 2026-10-18; it is not part of the release zip.

  ```
  ffmpeg -framerate 24 -i renders/channelrhodopsin/take-02/%04d.png -framerate 24 -i renders/channelrhodopsin/labels-03/%04d.png \
    -filter_complex "[0:v][1:v]overlay=format=auto[v]" -map "[v]" -frames:v 504 \
    -c:v libx264 -preset veryslow -crf 21 -pix_fmt yuv420p -movflags +faststart -an delivery/channelrhodopsin/channelrhodopsin-readme.mp4
  ```
- **Render cost.** Cycles, OptiX on the RTX 5060 Ti, 128 samples, adaptive 0.02, denoised: about 19 s per frame at 1920×1080, 2.7 h for 504 frames. The label pass takes about 5 min.
- **Framework refactor (2026-10-07).** The general code moved from the shot into `molanim/`, and the C1C2 specifics into `c1c2.py`. The rebuilt scene was checked against the delivered film:
  - every RESULT number (morph, pathway profile, sites, ion gaps, lipid counts, camera points) equals the original build;
  - the `.blend` files have the original byte sizes;
  - frames 70, 204 and 470, rendered at delivery settings, match the delivered posters (mean difference 0.000, max 1/255);
  - label frames 150, 330 and 446 are pixel-identical to the delivered label pass.

  `python pipeline.py check channelrhodopsin` repeats the poster test.
- **Review method.** The film was reviewed from contact sheets of two full low-res previews, full-resolution stills, frames decoded from the delivered MP4, and the statistics above. It was not watched as continuous playback.

## Known differences and limits

- **Evidence.** Only the endpoints are experimental, and the light endpoint is a 30 %-occupancy conformer. The path between them, the conducting state, the dilation, the cavity opening and all ion motion are illustrative and labelled as such. Five atoms have no light-state partner and stay put.
- **Surface side chains.** Some surface side chains move a lot between the deposited conformers (Tyr211 OH 9.2 Å, Arg246 7.1 Å, Lys325 4.5 Å). They are kept as deposited; they move during the network beat, mostly off camera.
- **Photons.** Photons are drawn as blue wave packets: a convention, not to scale. Only the molecule is shown absorbing one. The scene's blue key light is mood, not a spectrum.
- **Membrane.** The bilayer is procedural and POPC-like (about 64 Å² per lipid, P-P about 39 Å), not simulated. Lipids clashing with the protein are dropped, which leaves small annular gaps. The bilayer centre and normal come from the dimer's two-fold axis and a hydrophobic profile, not from OPM.
- **Protomer B.** Protomer B is context only. Its retinal is not opened up, although in the crystal both protomers carry the same change.
- **Ions.** Na⁺ stands in for "cations". No hydration shells are drawn, although simulations of related channels retain coordinated water.
- **Timescales.** The on-screen timescales are qualitative.
- **Pacing.** The dive (frames 85-170) is quick. The last caption fades out over the final 8 frames, and the film ends on the open channel without an end card.
- **Font.** Typography uses Blender's built-in font (no external font files).

## Version 2 (2026-10-07): thermal motion and the website palette

The site owner found the delivered film too still: the lipids, side chains and retinal showed no Brownian motion. The existing `breath` offset (sway 0.35, jitter 0.12) was nominally in Å but, measured, moved atoms by only about a fifth of that, and slowly. Version 2 adds illustrative thermal motion and moves the look to the amadeusbio.ai palette. Timeline, camera, morph, pathway, labels and evidence levels are unchanged. Version 1 stays in `delivery/channelrhodopsin/` and in release v0.1.0; version 2 is delivered to `delivery/channelrhodopsin-v2/` (take-03, labels-04).

- **Thermal motion** (`molanim.blender.groups.thermal`, new): two 4D noise fields in position and time, applied after the cutaway and section are evaluated, so atoms never flicker across a cut surface. A coherent field (6 Å, 1.5 cycles/s) moves neighbouring atoms together; a fine field (1.6 Å, 3 cycles/s) moves them more independently. Per-atom amplitudes are RMS displacements per axis (calibrated in Blender 5.2: 40,000 samples give 1.00 Å per unit; the noise texture's own RMS is 0.0912):

  | Atoms | Coherent (Å) | Fine (Å) |
  | --- | --- | --- |
  | Backbone (N, CA, C, O) | 0.10 | 0.04 |
  | Side chains, by remoteness (CB = 1 … NH/OH = 6) | 0.14 + 0.06 × level (0.20–0.50) | 0.04 + 0.025 × level |
  | Retinal | 0.20 | 0.03 |
  | Atoms shown in ball-and-stick (fine field only) | as above | 0.02, so sticks do not visibly stretch |
  | Lipid heads / tails | 0.9 / 1.2 | 0.15 / 0.22 |

  The salt-bridge marker and the dark-state ghost carry the same amplitudes as the atoms they follow. B-factors were considered for the amplitudes and rejected: in 9GO1 the backbone and side chains have the same median B (about 50 Å²), so they would not show side chains moving more. The motion is a rendering layer, not a simulation, and it is labelled as illustrative on the website.
- **Ions.** `ION_MARGIN` rises from 0.35 to 0.6 Å to cover the larger motion. Measured at build, against rest positions: smallest gap from an ion centre to a rendered atom surface 1.95 Å (target 1.35 + 0.6); largest step 2.11 Å/frame.
- **Look** (the amadeusbio.ai website's "mist" look): backdrop `#F7F9FC` → `#DBE3EC` with a softer blue during the light beat, protomer A navy drifting toward azure along the sequence, protomer B slate, blue-grey lipids, the website's amber for the retinal carbons, Na⁺ in blue (`#4A80D6`), and label ink `#0A1A31` (light ink on the close-ups as before).
- **Render** (`channelrhodopsin.blend` and the label scene built 2026-10-07, before frame 1). take-03 was rendered in two runs: frames 1–276 on 8 October and 277–504 on 17 October. The first run ended after frame 276 without writing a log. From frame 251 its frames had slowed to about 2.5 min each, with the GPU mostly idle, which points to contention from other work on the machine. At full speed a frame takes 15–17 s (median 14.8 s in the second run), so the whole film takes about 2.2 h; labels-04 took 3 min. All 1,008 PNGs decode. The join does not show. Frame 276, rendered again on 17 October (`renders/channelrhodopsin/preview-04/`), matches the 8 October frame to within 1/255 (mean difference 0.000), so both runs give the same picture. At 480×270 the mean change is 15.5 levels at 275→276, 15.9 at 276→277 and 14.1 at 277→278, during a camera move.
- **Motion of the picture** (480×270, all 504 frames, as for version 1): no frame-to-frame step exceeds twice its local median. The thermal motion raises the baseline, so the absorption flash and the ghost's fade-in no longer stand out. The largest step is still the dive, 29.7 levels at frame 120.
- **Labels.** Composites of take-03 and labels-04 at frames 1, 70, 150, 204, 241, 330, 400, 446 and 470 were compared with version 1 (take-02 + labels-03). Every pointer sits where it did in version 1: on Retinal, Lys296, C13=C14, Trp262, the dark-state ghost, Lys132, Glu129, the central and inner gates, and a Na⁺ ion. On these frames, the thermal motion (RMS up to 0.5 Å per axis on side chains) has not moved any target away from its pointer.
- **Delivery** (`delivery/channelrhodopsin-v2/`, `python pipeline.py deliver channelrhodopsin`, checked by `tools/encode.py`):

  | File | Codec | Frames | Duration | Size |
  |---|---|---|---|---|
  | `channelrhodopsin.mp4` (labelled) | H.264 | 504 | 21.0 s | 31.4 MB |
  | `channelrhodopsin.webm` (labelled) | VP9 | 504 | 21.0 s | 20.5 MB |
  | `channelrhodopsin-clean.mp4` | H.264 | 504 | 21.0 s | 30.5 MB |
  | `channelrhodopsin-clean.webm` | VP9 | 504 | 21.0 s | 19.3 MB |

  All are 1920×1080 at 24 fps, at the version 1 settings (CRF 16 / 24). The thermal motion makes them 1.7–2.2 times the size of version 1. Against the PNG frames (every 24th frame) the clean MP4 measures 41.2 dB (min 39.7) and the clean WebM 41.8 dB (min 40.3). Posters (clean): `-poster-wide.png` (frame 70), `-poster-retinal.png` (204), `-poster-channel.png` (470). Release v0.1.0 holds version 1; version 2 was not released (version 3 is in v0.2.0).
- **Website.** The film replaces version 1 on amadeusbio.ai (`docs/media.md` in the website repository, "October 2026, fourth round"). The website encodes needed higher bitrates than version 1 to stay within 2 dB of it: VP9 1800k / 1300k and H.264 2200k / 2000k at 1080 / 720.

## Version 3 (2026-10-17): motion from physics

**Request (owner, 2026-10-17):** "for the channelrhodopsin v2 animation the motion looks unrealistic, and molecules seems to blur together since the movement is too random. think about molecularly of how everything should move, search in depth, then output based on an accurate schematic."

**Diagnosis.** Version 2 moved every atom by its own position-and-time noise (`groups.thermal`): a 6 Å coherent field plus a 3 Hz fine field. Atoms of one molecule moved apart and atoms of neighbouring molecules moved together. Measured on a patch of 153 lipids over ten consecutive frames (frames 60–69), with the version 2 motion rebuilt from `groups.thermal` on the same lipids:

| | Version 2 | Version 3 |
|---|---|---|
| Bond stretch inside lipids, median / p99 | 0.62 / 2.39 Å | 0.04 / 0.35 Å |
| Per-frame step, median | 0.33 Å | 0.33 Å |
| Non-rigid part of the step, median | 0.32 Å | 0.14 Å |
| Close contacts (< 2.2 Å) between different lipids, change from rest | +32 % | +5 to +12 % |

**What changed.** Thermal motion now follows a schematic of how each kind of molecule moves, with literature rates (`docs/motion.md`, which cites its sources). The motion comes from `molanim.dynamics` (new, tested), `membrane.lipid_handles` and the geometry-node groups `dynamics` and `lipid_motion`. Timeline, camera, morph, pathway, palette and evidence levels are unchanged.
- **The clock.** 1 s of film = 1 ns, and each frame shows the average over two frames of it (83 ps). The clock eases to a stop for the picosecond twist (frames 180–228, "within a picosecond"), because nothing else moves on that timescale; the film covers 18.7 ns. The labelled film states the clock under the evidence tag ("Timescale 1 s of film ≈ 1 ns", frames 14–182 and 378–414). To run the clock through the twist, set `CLOCK_HOLDS = []`.
- **Protein.**
  - Normal modes of an anisotropic network on the dimer's Cα atoms: 15 Å cutoff, sequence-neighbour springs ×10, 30 modes. Variance ∝ 1/λ, calibrated to a mean Cα RMSF of 0.8 Å; τ ∝ 1/λ from 50 ns (softest) to 4 ns.
  - Each atom blends its residue's and the neighbouring Cα's displacement along the chain, so bonds keep their lengths to first order.
  - Side chains turn about CA–CB and CB–CG (χ1, χ2): Ornstein–Uhlenbeck within the rotamer well, 8° buried to 18° exposed (by neighbour count), τ 1.5–0.3 ns. Rotamer jumps are not shown.
  - Measured over the film (every 6th frame): median RMSF 0.28 Å for the backbone, 0.48 Å for side chains (p95 1.23 Å), 0.16 Å for retinal.
  - Largest bond change 0.94 Å, on the disordered termini, invisible at 0.64 × vdW. The 99.9th percentile is 0.24 Å.
- **Retinal, Lys296, Lys132, Glu129.** No side-chain turns: they move with the backbone, so the salt-bridge marker stays on its atoms and the Schiff base stays bonded. The dark-state ghost and the marker carry the same mode shapes as the atoms they follow.
- **Lipids** move as molecules: each samples its own processes at its glycerol.
  - A rattle (1.1 Å, τ 0.3 ns) inside a flow shared with neighbours (4 Å, τ 20 ns, correlation length 30 Å).
  - Axial spin (57°, τ 5 ns), wobble (10°, τ 1 ns) and bobbing (1 Å, τ 2 ns).
  - Each chain bends about its ester carbon, growing to 15° at the chain end (τ 0.5 ns). The choline turns about its phosphate (26°, τ 3.7 ns).
  - Lipids within 4–16 Å of the protein move less (down to 25 %).
  - The bilayer is the same as in version 2 (same seed).
- **Na⁺ in the water** diffuses freely at 1.33 × 10⁻⁹ m²/s, about 16 Å per film-second per axis. It is reflected at the membrane surfaces (|z| = 30 Å) and the scene bounds, and kept clear of the moving protein.
  - Ions outrun a frame, so they are window-averaged over 6 frames (250 ps). Steps per frame: median 1.8 Å, p95 3.5, maximum 6.2.
  - Smallest gap from an ion centre to a rendered atom surface is 1.75 Å (radius 1.35 + margin 0.4), for both bulk ions and transits, against the protein's exact moving positions. Bulk ions are checked against the final-state protein on every frame; the morph moves only buried pocket atoms.
  - The channel transits remain the illustrative conducting-state model. The random sequence changed, so their timing differs from version 2.
- **Checks.**
  - Stills and crops: frames 60–67 and 290–293 at 100 %.
  - Frozen-camera sequences: frames 62–69, 296–303, 168–182 and 20–27 at 50 %.
  - Lipid metrics as above. Frame-to-frame mean change in the same crops and frames as version 2: pocket 8.1 → 4.6 levels; lipid crop 16.3 → 13.4, which includes the camera dolly.
  - Contact sheet `preview-05` and `pipeline.py motion` on it: no step above 2× its local median.
  - `pytest`: 40 passed.
- **Render** (`channelrhodopsin.blend` and the label scene built 2026-10-17, before frame 1). take-04: 504 frames in 160.5 min (about 19 s a frame); labels-05: 2.7 min. All 1,008 PNGs were written in one run each.
- **Motion of the picture** (`pipeline.py motion`, 480×270, all 504 frames): median step 6.0, p95 24.6, maximum 28.5 at frame 122 (the dive); no step above 2× its local median.
- **Labels.** Frames 1, 70, 150, 204, 241, 330, 400, 446 and 470 were decoded from the delivered labelled MP4 and compared with version 2 (take-03 + labels-04). Every pointer sits on its target, as in version 2. The transits' timing changed, so the Na⁺ pointer (frames 434–470) was also followed every 6th frame from 436 to 466: it stays on its ion.
- **Delivery** (`delivery/channelrhodopsin-v3/`, `python pipeline.py deliver channelrhodopsin`, checked by `tools/encode.py`):

  | File | Codec | Frames | Duration | Size |
  |---|---|---|---|---|
  | `channelrhodopsin.mp4` (labelled) | H.264 | 504 | 21.0 s | 26.2 MB |
  | `channelrhodopsin.webm` (labelled) | VP9 | 504 | 21.0 s | 16.6 MB |
  | `channelrhodopsin-clean.mp4` | H.264 | 504 | 21.0 s | 25.3 MB |
  | `channelrhodopsin-clean.webm` | VP9 | 504 | 21.0 s | 15.3 MB |

  All are 1920×1080 at 24 fps, at the version 1 settings (CRF 16 / 24), and 16–21 % smaller than version 2: per-atom noise was costly to encode. PSNR against the PNG frames (every 24th frame): clean MP4 41.9 dB (min 40.2), clean WebM 42.2 dB (min 40.5), labelled MP4 and WebM against the take composited with the label pass 41.5 dB (min 40.0) and 41.9 dB (min 40.3). Posters (clean): `-poster-wide.png` (frame 70), `-poster-retinal.png` (204), `-poster-channel.png` (470). `pipeline.py check channelrhodopsin` rebuilt the scene and re-rendered frame 70: mean difference 0.000, max 1/255. It ran after ART's soft shutter was added to `molanim.dynamics`, which shows that the default (box) path still builds this film unchanged.
- **README clip** (2026-10-18). `channelrhodopsin-readme.mp4` (in `delivery/channelrhodopsin-v3/`) is the labelled film encoded from take-04 and labels-05 for GitHub's 10 MB attachment limit. Version 3's motion costs more bits than version 1's stillness: CRF 21 gave 15.5 MB and CRF 23 12.6 MB, so it is a two-pass H.264 encode at 3.4 Mb/s instead: 504 frames, 21.0 s, 1920×1080, 8.89 MB. Against the PNG composite its PSNR is 42.8 dB mean and 39.6 dB minimum (frame 96) over all frames, and a decoded frame at 10 s was inspected. It was uploaded as a GitHub attachment (`user-attachments/assets/965c2aa4-...`; the served file is byte-identical, SHA-256 checked) and replaced version 1's clip in the top-level README on 2026-10-18. It is not part of the release zip.

  ```
  ffmpeg -framerate 24 -i renders/channelrhodopsin/take-04/%04d.png -framerate 24 -i renders/channelrhodopsin/labels-05/%04d.png \
    -filter_complex "[0:v][1:v]overlay=format=auto,format=yuv420p[v]" -map "[v]" \
    -c:v libx264 -preset slow -tune film -b:v 3400k -pass 1 -an -f mp4 NUL      # NUL: /dev/null outside Windows
  # then the same with -pass 2 -movflags +faststart delivery/channelrhodopsin-v3/channelrhodopsin-readme.mp4 as the output
  ```
- **Review method.** Stills, crops, frozen-camera sequences, contact sheets, motion statistics, lipid metrics, PSNR and decoded frames. The film was not watched as continuous playback in this session.
- **Limits.**
  - Rates are literature values for POPC-like bilayers and soluble or membrane proteins, not for C1C2. The lipid axial spin D∥ varies 16-fold between papers.
  - Elastic-network modes are harmonic: no unfolding or rotamer jumps.
  - The frame follows the protein (membrane-protein drift and rotation are negligible on 19 ns).
  - The timescale beats ("microseconds", "milliseconds") are compressed time, during which the thermal motion keeps its 1 ns clock.
- **Website** (2026-10-18). Version 3 replaces version 2 on amadeusbio.ai, encoded from take-04 and labels-05 (`docs/media.md` in the website repository, "October 2026, fifth round"). It needs about 2 dB less bitrate than version 2 for the same quality, so the web encodes use VP9 1300k / 900k and H.264 1600k / 1400k (1080 / 720) and match the version 2 web encodes at 28 % fewer bytes. Not deployed.

## Version 4 (2026-10-20): drawn for the website

**Request (owner, 2026-10-20):** "redo the two ART and Nobel animation videos as well, with the newest physical details and aesthetic. Think about how to best represent them and fit into the website, make them website native." Owner's choices: labels as live HTML captions on the page, the film frameless on the website's panel, and stills approved before the final renders.

**What changed.** The science, timeline, camera path and motion are version 3's; the depth of field is a little deeper (aperture radius 0.012 of the focus distance, version 3: 0.016), so the cartoons stay sharp on white. The build checks this: matched atoms, snapshots, morph, pathway, dilation, atoms and bonds equal version 3's RESULT (`same_as_v3`). What changed is how each layer is drawn (`docs/depiction-sources.md`) and where the film lives. Files: `channelrhodopsin_v4.py` (scene), `storyboard_v4.py` (constants), `labels_data.py` (labels as data); the shot is `channelrhodopsin-v4` in `shots.json`.
- **Protein: cartoons** from 9GO1's deposited secondary structure (`_struct_conf`, `_struct_sheet_range`): 294 residues per protomer, 199 in helices and 30 in strands. Each of the 25 morph snapshots is re-ribboned with the same secondary structure (28,062 vertices each, asserted) and keyed through the morph. Each vertex carries its residue's Cα normal-mode shapes, so the ribbons move with version 3's modes. Protomer A opens with the camera-aimed funnel and the section slab (`groups.section`), which now removes whole cross-sections (`group='ring'`), so cut ends are clean. The cut runs before the motion, so no section crosses the funnel wall from frame to frame.
- **Actors: ball-and-stick** for the residues that act (pocket and network 262, 132, 129; gates 102, 297, 122, 173, 109; Lys296 and retinal): 79 atoms, in element colours, with retinal's carbons amber. They appear on version 3's reveal beats, with version 3's side-chain turns.
- **Retinal's π system:** the conjugated chain C5…C15=NZ with its π lobes (`electro.pi_chain_lobes`), recomputed for each snapshot. The lobes separate where C13=C14 twists (82° between the two atoms' p-orbital normals mid-morph, 3.8° before and 0.6° after) and nowhere else (≤ 10.3° elsewhere along the polyene). One stage-2 snapshot bends the chain by up to 0.2 Å, which would have read as a false break; in stage 2 (retinal already 13-cis) the lobes therefore follow the light-state chain, superposed onto each snapshot. At absorption (frame 176) the lobes deepen in colour and opacity for a moment. This is an illustrative marker, not emitted light.
- **Charges are not drawn.** Lys132 and Glu129 keep element colours, and the captions keep version 3's wording. Glu129's protonation in the dark state is debated (it corresponds to ChR2 E90), and nothing in this record states it.
- **Only light glows:** the photons. The backdrop no longer turns blue; the blue light falls on the molecules. Retinal's flash light, the cavity's glow and the ions' emission are gone.
- **White ground, no frame.** The camera sees pure white. The membrane is a round patch (radius 112 Å) cut in front at y = 2 Å, its lipids paling to white over the outer 30 %: 566 lipids, 29,402 atoms (version 3: 9,500 lipids, 493,963 atoms, a slab out to the frame edges). Lipid heads are one step darker than the website's membrane plate, because the film's membrane fills more of the frame under a brighter key. The decoded H.264 and VP9 test encode of frame 470 keeps the white at 255 (median; p1 253 / 251), so the multiplied film shows no rectangle on the panel.
- **Ions.** 120 bulk Na⁺ start inside the patch (version 3: 180 in a wider box). The steering pass now drops an ion it cannot clear (`particles.keep_clear(drop_below=1.65)`): 9 were dropped, leaving 111, with the smallest gap from an ion centre to an atom surface at 0.64 × vdW of 1.68 Å. The five transits clear 1.75 Å (120 iterations). The random stream differs from version 3's, so the transits' timing differs; the web labels follow this build's tracks.
- **Labels.** The build writes `delivery/channelrhodopsin-v4/labels.json` (`timeline.label_data`): header, captions, evidence tags with their level, timescales, and the 13 pointers' anchors projected on every frame exactly as the label pass projects them, plus the label pass's layout hint (`tags_left_from` 378). The website draws them over the clean film. The label pass (`channelrhodopsin-v4-labels.blend`) is kept for the downloadable labelled film.
- **Stills** (50 %, 128 samples, about 10–15 s each with scene load): frames 40, 150, 176, 204, 250, 300, 330, 400 and 470. Frame 470 at 100 % took 26 s with scene load and showed no visible noise. Fixes from them: notched helix ends (whole-section cuts), snow-white lipids (darker heads), saturated ions (lightened), an invisible near-white ghost on white (now darker than the page), and an "excitation" that paled (now deepens).
- **Approval.** The owner approved the stills on 2026-10-20.
- **Render** (Blender 5.2.2, Cycles, OptiX on the RTX 5060 Ti; `channelrhodopsin-v4.blend` and the label scene built 2026-10-20 11:11, before frame 1). take-01: 504 frames in 127.4 min (about 15 s a frame), in one run. labels-01: 2.6 min.
- **Trp262 pointer (2026-10-21).** Versions 1–4 anchored the "Trp262 shifts" pointer on the final snapshot's indole ring, which is 1.6 Å from the ring as rendered during the twist, about 100 px off at 1920×1080 in frames 212–262. `labels_data.py` now anchors it on the ring at the end of the twist (`A[k]`). The rebuild (63 s; the previous `.blend` files, `labels.json` and `build-result.json` are kept in `renders/channelrhodopsin-v4/backup-before-labels-02/`) changed only that pointer's track, by 106–113 px. The other 12 tracks, Na⁺ included, the rest of `labels.json` and `build-result.json` are identical. take-01 was not re-rendered: `pipeline.py check channelrhodopsin-v4 --no-build` rendered frame 70 from the rebuilt `.blend` and matched the delivered poster (take-01) with mean difference 0.000, max 1/255. The new label pass is labels-02 (504 frames, 3.0 min), set in `shots.json`. Crops of take-01 at the projected positions show the pointer on the indole ring in frames 212, 225, 237, 250 and 262, and the Na⁺ pointer on its ion in frames 436–470. Frame 237 of the delivered labelled MP4 shows the same.
- **Delivery** (`pipeline.py deliver channelrhodopsin-v4`, CRF 16 / 24), all 1920×1080 at 24 fps, 504 frames, 21.0 s:

  | File | Codec | Size |
  |---|---|---|
  | `channelrhodopsin-v4.mp4` (take-01 + labels-02) | H.264 | 25,358,720 B |
  | `channelrhodopsin-v4.webm` (take-01 + labels-02) | VP9 | 16,465,072 B |
  | `channelrhodopsin-v4-clean.mp4` | H.264 | 24,308,060 B |
  | `channelrhodopsin-v4-clean.webm` | VP9 | 15,137,381 B |

  Posters (clean): `-poster-wide.png` (frame 70), `-poster-retinal.png` (204), `-poster-channel.png` (470). At the same CRF the four files are 1–4 % smaller than version 3's.
- **README clip and stills** (2026-10-21). `channelrhodopsin-v4-readme.mp4` (in `delivery/channelrhodopsin-v4/`, not in the release zip) is the labelled film for GitHub's 10 MB attachment limit, encoded like version 3's clip from take-01 with labels-02 laid over it, but with `-preset veryslow` at 3.7 Mb/s: 504 frames, 21.0 s, 1920×1080, 9,642,279 B. Against the PNG composite (every 24th frame) it measures 38.3 dB mean, 36.3 dB minimum (frame 97); at version 3's settings (`slow`, 3.4 Mb/s) it measured 37.9 dB at 8.92 MB. The white ground's sharp cartoon edges cost more bits than version 3's mist. `docs/media/channelrhodopsin-{wide,retinal,channel}.jpg` are now the version 4 posters (frames 70, 204, 470), 640×360, JPEG q 85. The clip was uploaded as a GitHub attachment (`user-attachments/assets/33a48c82-...`; the served file is byte-identical, SHA-256 checked) and replaced version 3's clip in the top-level README on 2026-10-21.
- **Website** (2026-10-21). Version 4 replaces version 3 on amadeusbio.ai as a clean film (VP9 1700k / 1200k, H.264 2000k / 1700k, 1080 / 720; at version 3's web rates version 4 measured up to 0.9 dB lower, so the rates were raised until all four files measure above version 3's web encodes). The page draws the labels from `labels.json`. Details: `docs/media.md` in the website repository, "ninth round". Not deployed.
