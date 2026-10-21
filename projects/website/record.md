# Website assets for amadeusbio.ai: production record

Brief (from the site owner, October 2026): the website should feel designed component by component, the way reference research sites give every section its own picture in one art direction. Make those pictures with this framework, from structures already in the repository, so each one is honest about what it shows.

Script: `projects/website/website.py` (one scene per shot, prefix `WEB_`). Structures and science come from the channelrhodopsin case study (`examples/channelrhodopsin/c1c2.py`): 9GO1 (dark state) and 9GO2 alt B (early light-activated state), matched atom by atom; the dimer mate comes from the deposited assembly operator.

**AlphaFold Server output is not in the public repository:** `af3/` is gitignored except the job request `af3/p53-tetramer-p21.json`, so the p53 plate (`gallery.py` / `plates.py --shot p53dna`) builds only after the job is re-run on AlphaFold Server and model 0 is unpacked into `af3/model/`.

## Looks

| Look | Backdrop | Atoms | Light | Used for |
| --- | --- | --- | --- | --- |
| deep | radial glow `#244E84` → edge `#051634` (the website's hero panel colour) | protomer A porcelain, B azure | warm key, strong azure rim | hero loop, agents card, call-to-action art |
| mist | vertical `#F7F9FC` → `#DBE3EC` (the website's image wells) | protomer A navy, B slate | soft studio key and rim | principle cards, framework gallery |

Amber (`#E9A63C` family) marks one thing per picture: the retinal, the salt-bridge partners, or the agent markers.

## Shots and evidence

| Shot | Picture | Evidence level |
| --- | --- | --- |
| hero | C1C2 dimer (9GO1), one turn of a turntable per loop, 300 frames at 24 fps, 960 × 960 | Coordinates deposited; breathing illustrative. Camera and lights orbit together, so the molecule's transform stays identity |
| spheres | the dimer, side by side, mist look | Deposited (9GO1) |
| bridge | Lys132 NZ – Glu129 OE1 in 9GO2 alt B, ball-and-stick with a dotted marker, cutaway funnel | Deposited; distance reported by the build: **2.66 Å** |
| states | retinal + Lys296: dark state (amber), end of the twist stage (13-cis, blue), three twist intermediates as ghosts | Endpoints from 9GO1 / 9GO2; intermediates are the case study's illustrative morph. C12–C13=C14–C15 dihedral along the shown steps: −176°, 175°, 98°, 19°, 1° |
| cutaway | camera-aimed funnel to the retinal; pocket side chains as ball-and-stick | Deposited (9GO1) |
| cavity | 9GO2 pathway free-radius profile as a tube, section through protomer A | Measured profile, not the illustrative open state: the pathway shows as separate pockets (minimum free radius below 0 Å) |
| context | dimer in a procedural POPC-like bilayer, cut in front | Membrane procedural, not simulated |
| agents | dimer with eight amber markers on exposed atoms, joined into one trail | Illustration (not a result); the website tags it "Illustration" |
| cta | soft close-up of the dimer, deep look | Deposited (9GO1); decorative crop |

## Commands

```
blender -b --factory-startup --python projects/website/website.py -- --shot <shot> --still renders/website/final/<shot>.png
blender -b --factory-startup --python projects/website/website.py -- --shot hero --save
blender -b projects/website/hero.blend --python tools/render.py -- --out renders/website/hero/take-01
```

Stills: 256 samples, denoised. Loop: 48 samples, adaptive threshold 0.03, bounces (4, 2, 1), denoised. The encodes for the website are described in the website repository's `docs/media.md`.

## Second round (October 2026): one subject per component

The owner found the first round leaned on the channelrhodopsin case study for everything. The site now uses the case study only for its film. Every other component has its own molecule, chosen for what it shows. Two new scripts:

- `mark.py`: the hero loop. It is the silhouette object from `archive/art/amadeus_silhouette.py`, a staircase of bevelled cubes in the six brand tones whose front view is exactly the logo. The original tumbled the object about a tilted axis while it nodded, exploded and drifted in frame. Here the cubes stay still and centred, and only the camera moves: a 1 s hold on the logo, one smoothstep-eased 360° orbit around the bounding-box centre with a soft rise in elevation (24° at the middle), then a hold on the logo again. The lights ride with the camera. 336 frames at 24 fps (14 s), 960 × 960, deep look; frame 337 equals frame 1 (camera seam 0).
- `gallery.py`: the stills. Structures are in `projects/website/pdb/`: RCSB PDB files (CC0) and the AlphaFold DB model AF-P04637-F1 v6 (CC BY 4.0). Tetramers come from their deposited assembly operators 1–4.

| Shot | Subject | Evidence and measured values (build report) |
| --- | --- | --- |
| hemoglobin | 2HHB, human deoxyhemoglobin, chains A–D with four hemes (172 atoms, amber) | Deposited |
| dna | 1BNA, B-DNA dodecamer CGCGAATTCGCG | Deposited. Watson–Crick hydrogen bonds: canonical donor–acceptor pairs of each base pair, drawn when under 3.4 Å. Found **32** (8 G·C × 3 + 4 A·T × 2), 2.61–3.25 Å, mean 2.83 Å |
| p53 | AlphaFold DB AF-P04637-F1 (v6), 393 residues | Predicted. Mean pLDDT 75.1; 59.8 % of residues ≥ 70, drawn solid (navy ≥ 90, steel 70–90); the rest translucent |
| gfp | 1EMA, the chromophore (CRO, 22 atoms) in green ball-and-stick, camera-aimed cutaway | Deposited |
| kcsa | 1K4C chain C × 4, section through the pore, 7 deposited K⁺ ions | Deposited. Free-radius profile along the four-fold axis (protein atoms only): narrowest in the selectivity filter (Gly77–Tyr78), where the K⁺ ions sit; a second constriction of about 1.4 Å at the closed bundle crossing; widest in the central cavity. The exact minimum depends on the slice search, so no single number is quoted |
| aquaporin | 1J4N chain A × 4 in a POPC-like bilayer, cut in front | Deposited; membrane procedural |
| igg | 1IGT, intact IgG2a with its glycans (220 atoms, amber) | Deposited |
| nucleosome | 1KX5, histone octamer and 147 bp of DNA, soft close-up | Deposited; decorative crop |
| agents | the subjects above as a constellation joined by an amber trail | Illustration (the website tags it) |

An optional AlphaFold Server job for a stronger "uncertainty" picture is in `af3/p53-tetramer-p21.json`: full-length p53 × 4 on the p21 response element (both strands) with four Zn²⁺.

## Third round (October 2026): outline mark for the Approach page

The owner asked for silhouette-clean (`archive/delivery/amadeus/silhouette-clean.mp4`) again, but with a smooth camera, to replace the hypercube on the website's Approach page.

- `outline.py`: the drawing of `archive/art/amadeus_silhouette.py`'s clean variant (Workbench flat brand fills on white, navy outline from the mask SDF, fills that drain and return on the original's keys), with `mark.py`'s camera. The cubes never turn. An orthographic camera holds on the logo, makes one smoothstep-eased 360° orbit about the bounding-box centre with a 24° rise at the middle (frames 44–322), and holds again. The original tumbled the object about a tilted axis, nodded it and re-centred it on its silhouette every frame, so the outline wobbled in frame. The mid-turn spread (×1.18 spacing, ×0.70 size at most) is kept so the outline shows separate cubes. 1080 × 1080, 30 fps, 360 frames; frame 361 equals frame 1 (max pixel difference 0).
- Commands:

```
blender -b --factory-startup --python projects/website/outline.py -- --save
blender -b projects/website/outline.blend --python tools/render.py -- --frames 1-361 --out renders/website/outline/take-01/
```

The website encode is `approach-outline` (see the website repository's `docs/media.md`).

### AlphaFold Server model: p53 tetramer on the p21 response element

The job in `af3/p53-tetramer-p21.json` was run on AlphaFold Server; the download is `af3/fold_p53_tetramer_on_the_p21_response_element.zip`, and model 0 (ranking score 0.83, the top of five), its summary confidences and the terms are extracted to `af3/model/`. The owner decided (October 2026) that the website, which presents the open-source Molecular Animation release, uses it under the open-source-release exception of the AlphaFold Server Output Terms of Use (`af3/model/terms_of_use.md`). The terms require a conspicuous notice of the terms and of our changes wherever the picture is published.

| Shot | Subject | Evidence and measured values (build report) |
| --- | --- | --- |
| p53dna | AlphaFold Server (AlphaFold 3) model 0: p53 × 4 (chains A–D, 393 residues each), 4 Zn²⁺, the 20 bp p21 response element (chains I, J). DNA axis across the stage, tetramerisation domain above; camera 31° off the DNA axis (azimuth 66°, elevation 20°) | Predicted. ipTM 0.58, pTM 0.58, fraction disordered 0.50, no clashes. Mean pLDDT: DNA-binding domains 89.9, tetramerisation 60.2, transactivation 34.6, proline-rich 41.1, linker 34.6, C-terminal 28.8, DNA 51.2; 50.8 % of protein residues ≥ 70. Drawn solid at pLDDT ≥ 70 (navy ≥ 90, steel 70–90), translucent below; the DNA, all below 70, in translucent amber. Each DNA-binding domain has 24–31 heavy atoms within 4 Å of the DNA |

```
blender -b --factory-startup --python projects/website/gallery.py -- --shot p53dna --still renders/website/final2/p53dna.png
```

## Fourth round (October 2026): coloured cubes, thermal motion, loops

- **Hero mark, take-02.** Every cube now has its own tone (`mark.py`, `BACK_TONES`). The front cube of each column keeps its logo tone, so the front view (frames 1–24 and the end hold) is still exactly the logo. The four cubes behind them, seen only as the camera turns, are three blues (`#2F6DB5`, `#6FA3E0`, `#B8D3F2`) and one amber (`#E9A63C`, the deepest cube). Camera, lights and timing are unchanged.
  Rendered from `mark-deep.blend` (saved before frame 1) into `renders/website/mark/take-02/`, 336 frames, in three runs: 1–187 on 7 October, 188–264 and 265–336 on 8 October. The second run ended in a GPU fault after frame 264 (CUDA error 999; the machine then had to be power-cycled). The joins do not show: the mean frame-to-frame change at 187→188 and 264→265 is 1.27 and 0.79 levels, as in the frames around them, and the seam from frame 336 to frame 1 is 0.00. Website encode `hero-mark`: WebM 362,126 B, MP4 676,651 B, poster 13,232 B; PSNR against the source on every 28th frame WebM 45.1 dB (min 43.5), MP4 45.4 dB (min 44.1).
- **Gallery loops** (`loops.py`, assets for later use, not on the website). Each loop rebuilds a `gallery.py` shot exactly as for its still, at the size the website shows it, and adds camera motion plus illustrative thermal motion (`gallery.THERMAL`, the same amplitudes as the channelrhodopsin film v2), sampled on a loop so frame N + 1 equals frame 1. Camera, focus empty and lights turn as one rigid rig, which is optically the same as the molecule turning under fixed lights; camera-aimed cuts follow.

  | Loop | Frames (24 fps) | Size | Motion |
  | --- | --- | --- | --- |
  | hemoglobin | 288 (12 s) | 960 × 720 | one turn about the vertical |
  | dna | 288 | 960 × 720 | one turn about the helix axis |
  | p53dna | 240 (10 s) | 960 × 720 | drift: azimuth ±16°, elevation up to +8° |
  | gfp | 288 | 960 × 720 | one turn about the vertical (the funnel follows) |
  | kcsa | 288 | 960 × 720 | one turn about the pore axis (the section follows) |
  | aquaporin | 240 | 960 × 720 | drift ±14°, up to +8° (the membrane is cut in front) |
  | igg | 240 | 1280 × 720 | drift ±20°, up to +10° (edge-on, mid-turn, the Y reads as a column) |
  | nucleosome | 288 | 1280 × 720 | one turn about the disc axis |
  | agents | 240 | 1280 × 800 | drift ±8°, up to +6° |

  Render: 64 samples, adaptive 0.02, denoised, into `renders/website/loops/<shot>/take-01/` (frames 1–N + 1; the extra frame checks the seam).

  Status on 17 October: not finished. `renders/resume-all.sh` started hemoglobin at 15:28 (about 5 s per frame at 960 × 720), but the render was stopped at frame 45 of 289 because the machine was out of memory: 2.6 GB of RAM free, and 63.7 of 66.9 GB committed, mostly by another job. The other eight loops have not started; `hemoglobin.blend` is built. Re-running `resume-all.sh` continues from frame 46. Encode with the website repository's `artifacts/handoff/encode_loops.sh`, check each seam, and record the sizes here.
- **Channelrhodopsin film v2 on the website.** See `examples/channelrhodopsin/record.md`, "Version 2", and the website repository's `docs/media.md`.

## Aurora stills (20 October 2026): the website's dark redesign

The site moved to a dark look after the Google DeepMind research pages (grain, glowing and translucent shapes, colour gradients). `aurora.py` re-renders the nine stills by running `gallery.py`'s shot functions unchanged and swapping only the look (it overrides `Stage`; nothing in `gallery.py` or `molanim` was edited):

- **Atoms:** `candy_material`: Principled BSDF with subsurface 0.45, clear coat 0.55, roughness 0.32, sheen 0.25, emission = the `emit` highlights plus a Fresnel rim in the atom's own, lightened colour (0.35–0.55 by look).
- **Colour:** gallery's tones are remapped (`TONES`: navy → cobalt, steel → cyan, slate → orchid, pale → pearl, cream → peach, amber kept) and a cyan → blue → violet → rose gradient along the frame's diagonal is mixed in at 50 %, never on highlighted (emissive) atoms. Each shot keeps its distinctions (α/β chains, pLDDT bands, strands).
- **Envelope** (`envelope_group`, optional per molecule): the evaluated points (radius as drawn, so it follows every cut) → `Points to SDF Grid` at 1.5 × the drawn radius → dilate by a 3.5 Å probe, erode by 2.0 Å (net lift 1.5 Å; both steps stay inside the narrow band, a mesh threshold off zero would not) → Laplacian smoothing (14) → mesh at 1 Å voxels. Material `aura_material`: transparent, a translucent frost of 0.1 rising to 0.3 at the rim, a Fresnel glossy sheen and rim emission. DNA uses a thin coat (grow 1.2, probe 1.2, lift 0.5, smooth 3, voxel 0.5). It is a styling layer, not a framework representation; the website says so under the gallery.
- **Low-confidence and predicted DNA** (p53): `glass_ghost`, a lit, see-through tint, in place of `ghost_material`.
- **Backdrop:** window-space washes, colour blobs and out-of-focus discs (2D Voronoi) drawn by the world shader for camera rays only; objects are lit by a flat ambient, as before. Looks: `nebula` (dark), `pastel` (lavender-pink), `sky` (pale blue).
- **Camera and post:** depth of field × 2.2 (GFP × 1.6, nucleosome × 1.3), four suns (warm key, violet and rose rims, cool fill), Standard view transform, bloom (threshold 0.75, strength 0.7, size 0.75) and lens dispersion 0.012. AgX was tried and dropped: it greyed the pastel backdrops. A thin-film shell (420 nm) was tried and dropped: it turned sun glints green.

Shots (look, envelope): hemoglobin (pastel, globins), dna (sky, thin coat), p53dna (pastel, confident chains), gfp (nebula, none), kcsa (nebula, channel), aquaporin (sky, tetramer), igg (sky, antibody), nucleosome (nebula, none), agents (nebula, all six). Rendered to `renders/website/aurora/take-01/` by `take-01/render.sh` (320 samples, about 30 s per shot on the RTX 5060 Ti; it waits for 16 GB of free RAM before each shot). The build reports equal those of the earlier gallery renders in `renders/website/final2.log` (32 hydrogen bonds at 2.61–3.25 Å; 7 K⁺; pore free radius 0.16–6.39 Å; 4,556 hemoglobin atoms with 172 heme atoms), as they must, since the shots are the same code. Previews and look tests are in `renders/website/aurora/test/`. The website encodes and sizes are in the website repository's `docs/media.md` ("sixth round").

## Plates (20 October 2026): the white website

The owner asked for an all-white site, assets that blend into the page, and molecules that look like molecules,
each layer standing for something physical. The aurora stills above were retired (website `artifacts/removed-media/round6/`).
`plates.py` renders the nine stills from new framework layers (`molanim.cartoon`, `molanim.electro`,
`groups.envelope`, `look.ribbon_material` / `skin_material` / `fluorescence_material`; tests in
`tests/test_cartoon_electro.py`; sources in `docs/depiction-sources.md`):

- **Fold:** cartoons from the deposited secondary structure; the AlphaFold Server p53 model has none, so its
  confident domains use `estimate_secondary_structure` (said in the AF notice). DNA as ladders (backbone tubes
  through P, base slabs from the ring atoms); in the 1BNA close-up the bases are atoms, because its measured
  hydrogen bonds join atoms.
- **Electrons:** the van der Waals envelope as a faint skin (hemoglobin, IgG, agents); on the nucleosome the
  histone spool's envelope is coloured by the histones' own Coulombic potential (formal charges, epsilon = 4r,
  read 1.4 A outside, +-10 kcal/(mol e); p5-p95 of the vertices +1.2 to +21.0), and the DNA's phosphate backbone
  is drawn in the same negative red (charges: histones +148 e, DNA -292 e). Pi lobes (offset 0.95 A, a drawing
  choice) over the heme porphyrins, the 1BNA bases and the GFP chromophore.
- **Light:** only the GFP chromophore emits (`fluorescence_material`, strength 2.5): 1EMA is the S65T variant,
  which emits at 509-511 nm (Ormo et al. 1996).
- **White:** the camera sees 1.0 white; no bloom. Nothing reaches the frame edge (the aquaporin membrane is a
  98 A round patch whose lipids pale toward its rim; p53's low-confidence chain fades with distance from the
  DNA-binding core), so a plate sits on the page with no frame. The website's encoder lifts near-white residue
  (min channel >= 246, spread < 6) to 255 and whitens a 3 px border of stray denoiser pixels.

Takes: `renders/website/plates/take-01/` (256 samples; 2000 px wide, the nucleosome 3200 x 1800 for the
contact band; superseded framings in `take-01/superseded/`). Build reports repeat the earlier measurements
(32 hydrogen bonds, 2.61-3.25 A; 7 K+; pore 0.16-6.39 A). The hero loop has a `paper` look in `mark.py`
(camera sees pure white), rendered as `renders/website/mark/take-03/` (336 frames) from `mark-paper.blend`.

## Plate loops (21 October 2026): the plates, moving

The owner asked to render the gallery loops and put them on the website. `loops.py` (fourth round) animates the
retired gallery stills, so its loops were never rendered; `plate_loops.py` makes them from the current plates
instead. Each loop rebuilds its plate (same structures, layers, colours, cuts and framing) at the size the site
shows it and moves only the camera: the camera, its focus empty and the three suns turn as one rig about a pivot
(`loops.rig_rotation`, `loops.track_matrix`), so the lighting on the molecule never changes and nothing in the
molecule moves. Frame N + 1 equals frame 1, so a loop is frames 1..N.

| Shot | Motion | Frames | Size | Render |
|---|---|---|---|---|
| hemoglobin | turn about the vertical, camera 8 % further out (take-02) | 288 | 960 x 720 | 18 min |
| dna | turn about the helix axis | 288 | 960 x 720 | 13 min |
| p53dna | drift +-12 deg / +6 deg | 240 | 960 x 720 | 11 min |
| gfp | drift +-8 deg / +4 deg | 240 | 960 x 720 | 10 min |
| kcsa | drift +-12 deg / +6 deg | 240 | 960 x 720 | 10 min |
| aquaporin | drift +-12 deg / +6 deg | 240 | 960 x 720 | 11 min |
| igg | drift +-14 deg / +8 deg | 240 | 1280 x 720 | 16 min |
| nucleosome | drift +-12 deg / +6 deg | 240 | 1600 x 900 | 25 min |
| agents | drift +-8 deg / +6 deg | 240 | 1280 x 800 | 18 min |

- **Turn or drift.** The plates' cutaways are fixed geometry chosen for the plate's view (the GFP barrel's front
  residues are left out, the aquaporin membrane is cut in front, KcsA shows two opposite subunits), so only
  hemoglobin and the DNA turn all the way round. The nucleosome is seen nearly face-on, where a turn about its disc
  axis would read as a flat spin, so it drifts too.
- **Checks before rendering.** Stills at loop phases 0, 0.25, 0.5 and 0.75 (50 %) for every shot, with the edge
  rule (`loop_edges.py`: no picture within 6 px of the edge, outside the 3 px border the website encoder whitens).
  Three consecutive full-size frames of the nucleosome and aquaporin show no denoiser shimmer: the change over two
  frames is about 1.75 times the change over one (steady motion), not equal to it (noise).
- **Check after rendering.** Every frame of every loop (`loop_margins.py`, and the website's encoder):
  hemoglobin's take-01 swung the faint envelope through the bottom edge on frames 241-260, which the four-phase
  stills had missed, so take-02 frames it 8 % wider (`ZOOM`) and starts on its own frame 1 rather than the plate.
  All other loops keep at least 6 px of white to every edge; p53's faint low-confidence chain tints the 6 px band
  by at most 16 grey levels.
- **Seam and poster.** The nucleosome's step from frame 240 back to frame 1 equals its other steps (mean 0.96
  levels); its frame 1 matches the plate (mean difference 0.96 levels, render noise), so the plate is its poster.
- Build reports repeat the plates' measurements (32 hydrogen bonds, 2.61-3.25 A; 7 K+; pore 0.16-6.39 A;
  histones +148 e, DNA -292 e). Takes: `renders/website/plate-loops/<shot>/take-01/` (hemoglobin: take-02),
  64 samples, adaptive 0.02, denoised, Blender 5.2.2, OptiX on the RTX 5060 Ti. To render them all (resumable):
  `bash projects/website/render_plate_loops.sh`. It reproduces the final takes; the renders above ran from two
  local queue scripts with the same commands (take-01 for all nine, then hemoglobin take-02 after the margin check).
- **Website:** H.264 only, CRF 23 (on these loops x264 was smaller than VP9 at equal quality); sizes, PSNR and
  tags are in the website repository's `docs/media.md`, "tenth round".
