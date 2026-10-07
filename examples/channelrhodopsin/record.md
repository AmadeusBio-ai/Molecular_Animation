# Channelrhodopsin shot: production record · 2026-10-06

**Status:** delivered 2026-10-06. Rebuilt on the `molanim` framework on 2026-10-07 with identical output (see Checks).

A 21 s scientific illustration for `sources/Nobel_Med_2026.md` (generated with ChatGPT; provenance in `sources/README.md`), direction 1, "The twist that opens a pathway". The brief recommends building this shot first. A photon isomerises retinal in the channelrhodopsin C1C2, the protein rearranges (Lys132 swings to Glu129), and the cation pathway is shown first interrupted, then open in an illustrative conducting-state model. The look is the studio molecular style: atoms as spheres, a pale backdrop, shallow depth of field, a teal protein with an amber chromophore.

## What was built

| File | Role |
| --- | --- |
| `channelrhodopsin.py` | Shot script. Rebuilds scene `Channelrhodopsin` (written to `channelrhodopsin.blend`) and the label scene `Channelrhodopsin_Labels` (`channelrhodopsin-labels.blend`). Timeline, camera keys, colours and label text are constants at the top. |
| `c1c2.py` | C1C2-specific science, pure numpy (tested in `tests/test_c1c2.py`): state matching with alt-loc B and the +307 renumbering, the Schiff-base bond, the stage frame, the two-stage morph, the pathway and its sites, and the illustrative dilation. |
| `molanim/` (framework) | mmCIF reading and assembly operators (`structure`), the constrained morph (`morph`), the pore profile (`pathway`), the procedural POPC-like bilayer (`membrane`), ion drift/transit motion and clearance (`particles`), camera paths (`timeline`), and the Blender node groups, materials, camera rig and label pass (`molanim.blender`). |
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
python pipeline.py build channelrhodopsin                                  # both scenes, ~25 s
python pipeline.py render channelrhodopsin --take take-01                  # ~2.7 h on an RTX 5060 Ti
python pipeline.py render channelrhodopsin --overlay --take labels-01     # ~5 min
python pipeline.py deliver channelrhodopsin --take take-01                 # set the label take in shots.json
```

The delivered take-02 is take-01 frames 1-395 plus a re-render of 396-504 (`--frames 396-504` into a new take) after the ion-clearance and dilation fix. That fix changes nothing before the pathway opens: the re-rendered frames 396-409 match take-01 to within 1/255, with no pixel differing by more than 2. A full render from scratch gives the same picture. `labels-03` pairs with take-02 (the Na⁺ pointer follows the adjusted ion).

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
- **README clip** (2026-10-07). `channelrhodopsin-readme.mp4` is the labelled film re-encoded from take-02 and labels-03 to fit GitHub's 10 MB attachment limit: H.264 High, CRF 21, preset `veryslow`, faststart, 504 frames, 21.0 s, 9.06 MB. Against the PNG composite its PSNR is 46.5 dB mean and 44.0 dB minimum over all frames, and decoded frame 204 was inspected. It is uploaded to GitHub as an attachment and embedded in the top-level README; it is not part of the release zip.

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
