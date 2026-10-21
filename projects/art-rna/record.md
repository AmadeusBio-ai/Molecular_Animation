# ART: a hidden repertoire of RNA · production record

**Status:** version 1 delivered 2026-10-17 (`delivery/art-rna/`, take-01 + labels-01). Version 2, with Brownian and thermal motion from physical rates, delivered 2026-10-18 (`delivery/art-rna-v2/`, take-03 + labels-03). Version 3, drawn for the website, delivered 2026-10-21 (`delivery/art-rna-v3/`, take-01 + labels-01; see the last section). Release v0.3.0 carries version 3's delivery.

**AlphaFold Server output is not in the public repository** (`af3/` is gitignored): it is the owner's, under the AlphaFold Server Output Terms of Use, and only its renders are distributed, with the terms (`ALPHAFOLD-SERVER-OUTPUT-TERMS.md` in each delivery). Without `af3/` the scripts that read the models (`art_rna.py`, `art_rna_v3.py`) cannot build, and the test that needs them is skipped; `sources/af3-job-package/` holds the job inputs, so the predictions can be re-run on AlphaFold Server. Take-02 was rendered and rejected for frame-scale lurching (see Take-02). Not committed, not published.

A 31 s scientific illustration for `sources/CRISPR-Like.txt` (an AI-generated brief; provenance in `sources/README.md`). It follows the brief's recommended core: a repeat pattern in the genome of Staphylococcus phage SA1 becomes visible, the array's RNAs appear beneath their units, the camera travels to the reverse transcriptase and its YADD motif, and the film ends on the open question of how RNA, RT and partner work together. The look is the amadeusbio.ai "mist" look. Choices and what was left out: `brief.md`.

## What was built

| File | Role |
| --- | --- |
| `art_rna.py` | Shot script. Rebuilds scene `ArtRna` (`art-rna.blend`) and the label scene `ArtRna_Labels` (`art-rna-labels.blend`). Timeline, camera keys, palette, placements and label text are constants at the top. |
| `art_locus.py` | Project science, pure numpy (tested in `tests/test_art_rna.py`): the GenBank excerpt, the repeat search and comparison, B-DNA from sequence (1BNA templates, bent onto a path), the AlphaFold 3 models with pLDDT, confidence summaries, and the illustrative rigid drift. |
| `af3/` | AlphaFold Server output (unchanged from the owner's zip; `terms_of_use.md` applies). |
| `molanim/blender/labels.py` | New optional `links` in the label spec: a solid or dashed line between two anchors, with optional mid text. Used for the guide lines and the "?" links. Existing specs are unaffected. |
| `assets/pdb/1BNA.cif` | B-DNA dodecamer (RCSB), base-pair templates. |

## Structural basis (checked numerically at build)

- **The locus.** GenBank MW218148.1, positions 9421–13020 (job package excerpt). The 14-nt seed `ATATGAATACGTAT` occurs at 9598, 9810, 9981, 10182 and 10358 (mismatches 1, 0, 0, 0, 1), on the + strand only, inside the non-coding tract 9448–10646 (72 % A+T). The RT CDS (10647) and the partner CDS (12154) both start with ATG.
- **The repeat.** Comparing the copies: the three that agree best (9981, 10182, 10358) share a 49-nt element from 30 nt before to 18 nt after the seed start (single mismatches bridged). Consensus `AGATATTCTATAATTAATTTTATAGACATTATATGAATACGTATAATGA`. Identity to it: copy 1 63 %, copy 2 57 %, copies 3–5 100, 98, 98 %. Spacers between copies: 163, 122, 152, 127 nt; seed period 212, 171, 201, 176 nt. These match the reported ART ranges (repeats 15–49 nt, spacers 120–220 nt). They are our boundaries, not the authors' annotation. In the film, each copy's nucleotides that match the consensus light up (204 nt). The two degenerate copies therefore light up partly, which is what the sequence shows.
- **DNA geometry.** 1,480 bp (9421–10900), 60,680 heavy atoms. Each base pair is a 1BNA base pair of the same type, in its own frame (origin at the C1′–C1′ midpoint). They are stacked with an ideal B-DNA step of 36.0° and 3.38 Å about the screw axis fitted to 1BNA's central steps (fit: 34.35°, 3.362 Å). Phosphates sit 9.7 Å from the axis. The O3′–P links between stacked templates are 1.17–2.67 Å (median 2.06; a bond is 1.6 Å), because 1BNA's base pairs differ slightly; this is invisible with spheres at 0.70 × vdW. The helix is bent onto a Catmull–Rom path (smallest radius of curvature 555 Å) with rotation-minimising frames. The largest change of any covalent-range distance from bending is 0.024 Å. The path is illustrative.
- **RNAs.** AF3 model 0 of the four genomic-window RNAs (W1 9598–9809, 212 nt; W2 171; W3 201; W4 176). Mean pLDDT 39.7, 45.6, 40.8, 49.5, with ≤ 2 % of atoms at pLDDT ≥ 70; pTM 0.15–0.20. The five samples per RNA differ by 5.6–48 Å C4′ RMSD, so the global folds are not determined. About 30 % of nucleotides sit in Watson–Crick-like N1–N3 contacts (< 3.2 Å) in model 0. The ends are window choices (motif to motif), not mapped transcripts.
- **RT.** AF3 model 0 of QPI16926.1 (501 aa): pTM 0.80, mean pLDDT 78.2, 75 % of atoms at pLDDT ≥ 70 (the N-terminal ~125 residues are lower). The five samples agree within 1.2–3.4 Å Cα RMSD. YADD is residues 366–369 (pLDDT 92), 22 Å from the centroid, so a camera-aimed cutaway opens to it.
- **Partner.** AF3 model 0 of QPI16927.1 (265 aa): pTM 0.21, mean pLDDT 33.3, no atom at pLDDT ≥ 70. Samples differ by 19–22 Å.
- **Complexes, not shown.** The 23 complex jobs (RT–partner, RT–RNA, partner–RNA, RT–partner–RNA, with three seeds where run) have ipTM 0.07–0.24. No interface is confident, so the film places the molecules apart and draws the question, not a contact.

## Motion and evidence levels

| Screen time | What moves | Evidence level (also the on-screen tag) |
| --- | --- | --- |
| 0–7 s | Camera close on the DNA, tracking; repeat copy 1 lights (frame 46), then the camera pulls back (log-distance, ≈ 2.8 % per frame) as copies 2–5 light (100, 124, 144, 162) | Sequence: GenBank. Repeat positions: our comparison. DNA shape: illustrative |
| 7–11 s | Hold on the array; locus map in the label pass (array, RT gene, partner gene) | GenBank annotation (CDS coordinates) |
| 11–17.5 s | The four RNAs resolve (an atom-by-atom dissolve, not in sequence order, so it does not suggest transcription or folding) below their units; guide lines in the label pass | AF3 predictions, low confidence; RNA ends assumed |
| 18–24.5 s | Lateral travel past RNA 4, dive to the RT; cutaway to YADD, which turns to amber ball-and-stick | AF3 prediction (pTM 0.80) |
| 25–31 s | Pull back; the partner resolves; dashed "?" links between RNA, RT and partner | Hypotheses; no confident interface (ipTM ≤ 0.24) |

- **Free molecules.** RNAs and the partner drift rigidly (sums of slow sinusoids; RMS 7 Å and 3° for RNAs, 5 Å and 3° for the partner) and carry illustrative thermal jitter (`groups.thermal`, RMS 0.22 Å coherent, 0.05 Å fine). The RT does not drift (its cutaway is computed in stage space); it has thermal jitter of 0.12 / 0.04 Å. The DNA sways (`groups.breath`, 0.5 Å over 40 Å). None of this is simulated.
- **Placement.** The RNAs hang 150–200 Å below their units; the RT and partner sit beyond unit 4. These are editorial choices. Smallest gaps over the film (every 31st frame): RNA 4–RT 105.7 Å; every other pair, and every molecule to the DNA, stays more than 120 Å apart. Nothing touches.
- **Confidence on screen.** As on the website's AlphaFold stills: pLDDT ≥ 70 solid (≥ 90 navy, 70–90 steel), below 70 translucent. RNA colour and opacity ramp with pLDDT (pale and more transparent where lower). The partner is translucent throughout. The RT stays hidden until frame 300, while it is off screen, so it does not show as an unexplained speck in the wide shot.

## Reproduce

```
python pipeline.py build art-rna                                  # both scenes, ~17 s
python pipeline.py render art-rna --take take-01                  # ~9 s/frame, ~1.9 h on an RTX 5060 Ti
python pipeline.py render art-rna --overlay --take labels-01      # EEVEE label pass
python pipeline.py deliver art-rna
```

The AlphaFold results must be unpacked into `af3/` first (model CIFs, summary confidences, job requests and the terms file from `CRISPR-Like/folds_2026_10_08_04_51.zip`).

## Checks

- **Build.** About 17 s headless. Two builds in one Blender session leave identical datablock counts (120 objects, 44 meshes, 39 materials, 8 node groups, 75 actions), no `.001` duplicates and no `ART_`/`ARTL_` orphans. `RESULT` (`renders/art-rna/build-result.json`) reports the repeat analysis, DNA fit, links and bending strain, per-RNA nucleotides and pLDDT, the RT's YADD pLDDT, the minimum clearances and all AF3 confidences. `pytest tests/test_art_rna.py`: 5 passed.
- **Look-dev.** Stills at 50 % of frames 30, 60, 64, 120, 140, 220, 230, 300, 330, 344, 400, 420, 424, 460, 470, 494, 520, 530, 600, 640, 648, 700, 720 and 744 were viewed in four rounds, with the label pass composited at 60, 120, 230, 330, 400, 530 and 700. Fixes from them: a repeat "pulse" that blew out to white; RNAs too small and faint; decorative background DNA that read as smudges (removed); an empty frame on the way to the RT; a closing frame that lost the array; the RT as a stray speck in the wide shot; "?" links collapsed onto one line; pointers and a scale bar colliding with captions. Frames 340 and 700 at 100 % (96 samples): no visible noise.
- **Preview.** `preview-01` (every 4th frame, 25 %, 16 samples) reviewed from its contact sheet. `pipeline.py motion`: median step 2.0, p95 10.6, maximum 14.3 at frame 477 (the dive to the RT); no step above 2× its local median.
- **Final take.** `take-01-sheet.png` matches the preview. `pipeline.py motion` on all 744 frames: median step 0.62, p95 6.5, maximum 10.3 at frame 23 (the opening track along the DNA); no step above 2× its local median. Frames 617 and 625 (the partner resolving) were inspected at full size.
- **Reproducibility.** `pipeline.py check art-rna` rebuilds from the script and renders the first poster frame (72) at delivery settings: mean difference 0.000, max 1/255 against the delivered poster (frame 220 before the poster change: same result).
- **Delivery** (`delivery/art-rna/`, verified by `tools/encode.py` with ffprobe `-count_frames`; PSNR in yuv420p over all 744 frames against the PNG take, or against the take with the label pass composited for the labelled files):

  | File | Codec | Frames | Duration | Size | PSNR mean / min |
  |---|---|---|---|---|---|
  | `art-rna.mp4` (labelled) | H.264, CRF 16 | 744 | 31.0 s | 11.0 MB | 52.9 / 50.5 dB |
  | `art-rna.webm` (labelled) | VP9, CRF 24 | 744 | 31.0 s | 6.1 MB | 51.2 / 49.5 dB |
  | `art-rna-clean.mp4` | H.264, CRF 16 | 744 | 31.0 s | 9.9 MB | 53.7 / 50.9 dB |
  | `art-rna-clean.webm` | VP9, CRF 24 | 744 | 31.0 s | 5.0 MB | 51.8 / 49.8 dB |

  All are 1920×1080 at 24 fps. Posters (clean frames of the take): `-poster-repeat.png` (72), `-poster-rnas.png` (360), `-poster-yadd.png` (540), `-poster-question.png` (720). `ALPHAFOLD-SERVER-OUTPUT-TERMS.md` is the AlphaFold Server terms file, unchanged. Decoded frames 60, 120, 230, 330, 530 and 700 of `art-rna.mp4` were inspected: the label composite, the locus map, pointers, guide and "?" links, captions, tags and the terms notice are correct. A first whole-film PSNR run on the WebM paired frames one apart (WebM stores millisecond timestamps), giving a false 22.6 dB minimum; single frames compared directly (frame 21: 44.8 dB, frame 480: 43.7 dB in RGB) and a re-run with the input rate forced (`-r 24`) give the table's numbers.
- **Render cost.** Cycles, OptiX on the RTX 5060 Ti, 96 samples, adaptive 0.02, denoised: 108 min for 744 frames (8.7 s per frame). Label pass (EEVEE): 3.8 min. Encoding: about 3 min.
- **Review method.** Reviewed from stills, crops, contact sheets, motion statistics, PSNR and decoded frames. The film was not watched as continuous playback in this session.

## Known differences and limits

- **Not a CRISPR system.** The brief's title says "CRISPR-like" and so does press coverage; the film says only that the repeat layout resembles a CRISPR array, which is what Anthropic's announcement says.
- **Not verified against the preprint.** Captions use facts from Anthropic's announcement and a trade-press summary of the preprint (`sources/README.md`). The 8 % figure and "loci lack cas genes" come from that summary.
- **RNA shapes are not known.** The four RNAs are low-confidence predictions of window-defined sequences. They are shown so the viewer sees a repertoire, not to claim folds.
- **Left out:** the phage exterior and the comparison systems (6AR1 RT chemistry, the 9LM3 and 8QBM retrons). See `brief.md`.
- **AlphaFold Server Output Terms of Use** apply to the RNA, RT and partner coordinates and to renders derived from them. The labelled film carries a notice; the clean film does not, so distribute it with `af3/terms_of_use.md`.

## Version 2 (2026-10-17): Brownian motion

**Request (owner, 2026-10-17):** "for the CRISPR-like animation, add motions like brownian motion to the molecule to make it look more realistic ... think about molecularly of how everything should move, search in depth, then output based on an accurate schematic."

**What changed.** Version 1's free molecules drifted on slow sums of sinusoids (RMS 5–7 Å and 3°) with per-atom jitter, and the DNA swayed by per-atom noise (0.5 Å). Version 2 moves every molecule as a molecule, at rates from the literature, on one clock. Sources and the reasoning are in `docs/motion.md`; the code is in `molanim.dynamics` and the geometry-node groups `dynamics` and `chain_motion`. Timeline, palette, labels, placements and evidence levels are unchanged.
- **The clock.** 1 s of film = 5 ns at 37 °C. Each frame shows a triangle-weighted average over 16 frames of it (3.3 ns; see Take-02 for why). The film covers 155 ns. The clock is stated in this record and in `docs/motion.md`, not on screen: the label pass's timescale slots carry the confidence notes.
- **Tumbling and diffusion.** Each RNA, the RT and the partner is a Perrin prolate spheroid fitted to its own atoms (second moments + 3 Å hydration). Elongated RNAs tumble end over end ten times more slowly than a sphere of the same volume would. Crowding slows translation 4× and rotation 2× (E. coli data: no S. aureus measurements exist). The molecules are held within RMS 9 Å and 20° of their editorial places by a soft tether, which over a few seconds of film is free diffusion. Per film-second (median):

  | Molecule | Semi-axes (Å) | D_t (µm²/s, crowded) | Shift | Turn |
  |---|---|---|---|---|
  | RNA W1 | 188 × 35 × 18 | 11.8 | 4.6 Å | 6.1° |
  | RNA W2 | 132 × 29 × 20 | 15.2 | 5.3 Å | 7.0° |
  | RNA W3 | 80 × 41 × 31 | 16.6 | 5.5 Å | 8.3° |
  | RNA W4 | 151 × 21 × 17 | 15.2 | 5.4 Å | 5.3° |
  | RT | 69 × 31 × 23 | 20.7 | 6.5 Å | 10.0° |
  | Partner | 43 × 26 × 24 | 26.7 | 6.8 Å | 15.0° |

  The RT draws from its own random stream (`RT_SEED` = 339). Of 3,000 seeds tried, its close-up pose stays nearest take-02's, a mean 12.5° away over frames 474–600, so the active-site cleft faces the camera as designed. Choosing a seed picks one of many equally likely paths; the rates are unchanged.

- **Internal motion.**
  - **RNAs:** normal modes of a P-atom elastic network (20 Å cutoff, P–P springs ×10, 24 modes). Mean P RMSF 2.5 Å, softest τ 60 ns; RNA junctions bend on ns timescales.
  - **RT:** Cα network (15 Å, 24 modes), mean RMSF 1.0 Å, softest τ 50 ns, plus side-chain χ1/χ2 turns about bonds (8–18°, τ 1.5–0.3 ns; the 3.3 ns window shows 6–8.5°).
  - **Partner:** Cα network, mean RMSF 2.0 Å (low pLDDT, likely flexible), softest τ 30 ns.
  - In all three, atoms blend their residue's and the neighbouring node's displacement, so bonds keep their lengths to first order.
- **DNA** bends and twists as a worm-like chain about its designed path (persistence length 50 nm, twist persistence 75 nm, cytoplasmic friction ×2). Base pairs move as units:

  | Waveband | RMS | τ |
  |---|---|---|
  | 150 Å | 1.2 Å | 3.3 ns (the window) |
  | 300 Å | 4.4 Å | 13 ns |
  | 600 Å | 12.7 Å | 170 ns |
  | Twist over 200 Å | 22° | 3.3 ns (the window) |

  Base-pair opening (~10 ms) is never shown.
- **The RT and the camera.** The RT tumbles, so its cutaway now follows YADD: the CutTarget is YADD's track, and the RT's cut reads the camera in the RT's own frame. During the close-up (frames 440–640, eased) the camera follows YADD as an operator would. YADD travels up to 37 Å from its rest position. The `yadd`, `rt` and `rt_low` label anchors are tracks.
- **Clearances** (every 16th frame, with every molecule's tumbling and internal motion; DNA at rest). The smallest gap is RNA 4–RT, 107.1 Å; every other pair stays more than 120 Å apart. The DNA's bending (≤ 13 Å RMS) cannot close these gaps.
- **Checks before take-02** (3-frame box window).
  - Frozen-camera sequences at 50 %: the DNA close-up (frames 36–43), the RNAs (336–378, every 6th) and YADD (528–549, every 3rd).
  - Contact sheet `preview-02` against `preview-01`, and `pipeline.py motion` on both:

    | Preview | Step median | Max | Steps above 2× local median |
    |---|---|---|---|
    | `preview-01` (v1) | 2.00 | 14.26 (the dive) | none |
    | `preview-02` (v2) | 2.94 | 14.26 | none |

- **Take-02 (rendered, rejected).** Take-02 used a 3-frame box window. It was rendered on 17–18 October (136.3 min; labels-02 3.5 min) and encoded, but never shown.
  - `pipeline.py motion` on all 744 frames gave a median step of 1.50, p95 6.93 and maximum 9.39. Steps 555→556 and 556→557 measured 6.5 against a local median of 3.1, the only steps above 2× (`renders/art-rna/take-02-motion.txt`).
  - The cause is the RT's tumbling in the close-up. The RT's transforms were read from the `.blend` on every frame and projected through the camera (`renders/art-rna/rigid_probe.py`, `rigid_stats.py`, `take-02-rt-probe.json`).
    - Its rotation per frame went 1.3, 1.6, 3.1, 2.7, 1.0, 0.6°, and its far end's screen step went 1, 16, 26, 26, 11, 1 px.
    - Over frames 494–566 the far end's velocity changed by 0.67 of its step every frame. That is a lurch: the same "too random" fault as channelrhodopsin version 2, at the scale of a whole molecule.
  - The earlier checks missed it because `preview-02` sampled every 4th frame and the YADD frozen-camera run every 3rd. Neither can show a change at the scale of one frame.
  - The fix is a 16-frame triangle window (`shutter='triangle'` in `molanim.dynamics`). Numpy trials at the RT's own rates compared windows by the change of the far end's velocity per frame, relative to its step:

    | Window | Box 3 | Box 12 | Triangle 12 | Triangle 16 |
    |---|---|---|---|---|
    | Change of velocity per step | 0.70 | 0.34 | 0.27 | 0.20 |

    Turn per film-second fell from 11.3° to 10.6°. The new window changed every random draw, which is why the RT now has its own seed (above).
- **Checks of take-03.**
  - Probe of the take-03 build over frames 494–566 (`take-03-rt-probe.json`), against take-02:

    | | Take-02 | Take-03 |
    |---|---|---|
    | Rotation per frame, median (p95) | 1.26° (2.73°) | 0.81° (1.50°) |
    | Far end's screen step, median | 10.1 px | 4.0 px |
    | Change of its velocity per frame, median | 6.7 px | 1.1 px |
    | Agreement of consecutive steps (cos), median | 0.89 | 0.99 |

  - Frozen-camera run of 13 consecutive frames (548–560, 50 %), on the build just before the RT got its own seed (same window): the steps change smoothly (4.0 → 2.8 → 3.9 levels at 960×540), and YADD's side chains do not shimmer.
  - Contact sheet `preview-03` (every 8th frame, 25 %) against `preview-02`. Compositions hold. In the close-up the RT shows the cleft with YADD in it, at least 52 px inside the frame.
  - Labelled stills at frames 400, 540 and 700 (50 %): the pointers sit on Unit 4, YADD, the RT, the partner and the array RNA.
  - `pytest`: 40 passed.
- **Render** (`art-rna.blend` and the label scene built 2026-10-18, before frame 1). take-03: 744 frames in 104.9 min (8.5 s a frame); labels-03: 3.5 min.
- **Motion of the picture** (`pipeline.py motion`, 480×270, all 744 frames): median step 1.15, p95 6.75, maximum 9.26 at frame 22 (the opening track along the DNA); no step above 2× its local median (`renders/art-rna/take-03-motion.txt`). Per 48-frame block against take-02, the close-up (frames 481–577) fell from 3.1–3.5 to 1.7–2.6 levels per frame and the tableau (625–744) from 0.5–0.6 to 0.3. Frames 548–564 step smoothly, 2.9 → 1.8 → 3.4; take-02 alternated between 2.1 and 6.5 there. `take-03-sheet.png` matches `preview-03`.
- **Labels.** Frames 60, 120, 230, 340, 420, 520, 580, 650 and 700 were decoded from the delivered `art-rna.mp4`. The pointers sit on the repeat, the spacer, units 2 and 3, YADD, the RT, the partner and the array RNA. The locus map, the "?" links, the captions and the tags are correct.
- **Delivery** (`delivery/art-rna-v2/`, `python pipeline.py deliver art-rna`, checked by `tools/encode.py`; PSNR in RGB over every 24th frame, against the PNG take or the take composited with the label pass, so not comparable with version 1's yuv420p figures):

  | File | Codec | Frames | Duration | Size | PSNR mean / min |
  |---|---|---|---|---|---|
  | `art-rna.mp4` (labelled) | H.264, CRF 16 | 744 | 31.0 s | 12.6 MB | 43.7 / 42.7 dB |
  | `art-rna.webm` (labelled) | VP9, CRF 24 | 744 | 31.0 s | 7.8 MB | 43.8 / 42.9 dB |
  | `art-rna-clean.mp4` | H.264, CRF 16 | 744 | 31.0 s | 11.5 MB | 44.1 / 43.0 dB |
  | `art-rna-clean.webm` | VP9, CRF 24 | 744 | 31.0 s | 6.6 MB | 44.3 / 43.3 dB |

  All are 1920×1080 at 24 fps. Posters (clean frames of take-03): `-poster-repeat.png` (72), `-poster-rnas.png` (360), `-poster-yadd.png` (540), `-poster-question.png` (720). `ALPHAFOLD-SERVER-OUTPUT-TERMS.md` was copied unchanged from `delivery/art-rna/`. Take-02's encodes were overwritten. `pipeline.py check art-rna` re-rendered frame 72: mean difference 0.000, max 1/255.
- **Review method.** Stills, crops, frozen-camera sequences, contact sheets, motion statistics, transform probes, PSNR and decoded frames. The film was not watched as continuous playback in this session.
- **Limits.**
  - The hydrodynamics treat each molecule as a rigid spheroid; real crowding in S. aureus is unmeasured.
  - The elastic networks are built on low-confidence predictions (RNAs, partner), so their modes illustrate flexibility; they are not predictions of it.
  - DNA bending moves base pairs across the local frame without tilting them (sub-Å).
  - The tether keeps the composition and is not physical over the whole film: untethered, the RT would wander about 25 Å per axis and the molecules would turn 35–60° in 155 ns.

## Website (2026-10-18)

Version 2 (take-03 + labels-03) is the second case study on amadeusbio.ai's Molecular Animation page, labelled and clean, at 1080 and 720 in WebM and MP4 (`docs/media.md` in the website repository, "October 2026, fifth round"). Four chapters start at 0, 11, 18 and 25 s; the thumbnails are the delivered posters' frames (72, 360, 540, 720), and the poster is frame 720. The film moves little against a flat backdrop, so VP9 350k / 250k and H.264 500k / 350k still give 39.4–42.2 dB (labelled and clean), and its eight files take 11.4 MB. The page names the film ART, says only that the repeat layout resembles a CRISPR array, and shows the AlphaFold Server Output Terms notice under the player, naming the changes (placement, illustrative motion, view and colours), because the clean film carries none. This rests on the owner's open-source-release reading of the terms, as for the website's p53 still. Not deployed, and this project is not yet on GitHub, so the page does not link to this record.

## Version 3 (2026-10-20): drawn for the website

**Request (owner, 2026-10-20):** "redo the two ART and Nobel animation videos as well, with the newest physical details and aesthetic. Think about how to best represent them and fit into the website, make them website native." Earlier in the same session: "rethink about how to represent the DNA helix other than smooth tubes, which does not look like molecule." Owner's choices: labels as live HTML captions on the page, the film frameless on the website's panel, and stills approved before the final renders.

**What changed.** The science, placements, timeline, camera and motion are version 2's, drawn from the same random streams in the same order. The build checks this against version 2's RESULT (`same_as_v2`): locus, confidences, camera points, and every molecule's tumbling come out identical, and so do the clearances (smallest gap RNA 4 to RT 107.1 Å). What changed is the drawing, as on the website's plates. Files: `art_rna_v3.py` (scene), `story_v3.py` (constants); new in `art_locus.py`: `nucleic_table`, `o3p_links`, `close_backbone` (tested in `tests/test_art_rna.py`). The shot is `art-rna-v3` in `shots.json`.
- **DNA, atom by atom:**
  - A stick for each of the 68,078 covalent bonds. Each phosphate group (P, OP1, OP2) is drawn as red balls: one negative charge, as on the website. The 7,400 sugar and base rings are filled as plates. Strand tones and the base colour follow the website's DNA plate (bases one step deeper, sticks 0.28 Å instead of 0.2: many bases overlap at the opening's 165 Å).
  - The stacked 1BNA templates left O3′–P gaps of 1.17–2.67 Å (median 2.06), which sticks would show. A bond-length projection over the sugar-phosphate atoms closes all 2,958 links to 1.60 Å. Bases are held fixed, every other bond keeps its template length (largest change below 0.001 Å), and atoms move at most 0.67 Å (p95 0.27). Bending strain after closing is 0.022 Å.
  - The repeat copies light in the website's amber, by colour only.
  - As the camera pulls back (frames 104–150, about 550 to 2,500 Å) the same atoms swell to space-filling at 0.70 × vdW and the sticks thin away (`groups.ball_stick`, Detail controller). Far away the array is drawn as version 2 drew it.
- **RNAs, atom by atom:** sticks 0.42 Å (about two pixels at 1,000–1,300 Å), phosphate groups red, rings as translucent plates, teal paling and turning translucent where pLDDT is low. They resolve atom by atom, as in version 2. Plates move with their nucleotide's mean mode shape.
- **RT: a cartoon** whose secondary structure is estimated from the predicted Cα positions (`cartoon.estimate_secondary_structure`; 209 residues helix, 119 strand). It is coloured by confidence: pLDDT ≥ 90 navy, 70–90 steel, below 70 pale at 40 % opacity. The camera-aimed cut removes whole cross-sections (`groups.section(group='ring', space='RELATIVE')`). YADD's side chains are ball-and-stick with amber carbons, revealed on version 2's beat, with version 2's side-chain turns. YADD no longer glows.
- **Partner: a coral cartoon**, 35–60 % opaque with pLDDT (mean 33). The estimator calls 222 of its 265 residues helical from the predicted Cα geometry, so it is drawn as the low-confidence model it is. It fades in on version 2's beat.
- **White ground, no glow, no bloom.** The film is multiplied onto the website's panel.
- **Labels.** The build writes `delivery/art-rna-v3/labels.json`: captions, evidence tags with their level, timescales, pointers, and the seven links (four guides, three dashed "?") projected on every frame. It also carries the locus map as primitives (frames 196–258) and the AlphaFold notice (630–744), in fractions of the frame. The website draws them over the clean film. Because camera and motion are version 2's, they also sit correctly on version 2's clean film. The label pass (`art-rna-v3-labels.blend`) keeps the map and notice for the downloadable labelled film.
- **AlphaFold Server Output Terms.** Any page or file that shows this film must say that the representation is ours: cartoons with secondary structure estimated from the predicted Cα positions, atom-by-atom RNA, and colours by confidence.
- **Stills** (50 %, 96 samples, about 9 s each with scene load): frames 30, 64, 120, 220, 330, 420, 530 and 700, plus frame 30 at 100 % (17 s with scene load). Fix from them: a thin, pale opening (thicker sticks, deeper and more opaque base plates, bolder RNA sticks).
- **Approval.** The owner approved the stills on 2026-10-20.
- **Render** (Blender 5.2.2, Cycles, OptiX on the RTX 5060 Ti). take-01: frames 1–672 on 2026-10-20 in 107 min (about 9.6 s a frame); the run was stopped at 20:50 because other jobs had taken the machine to 2.9 GB of free memory, and frames 673–744 were rendered on 2026-10-21 in 11.5 min by the same command, which skips existing frames. The `.blend` was not rebuilt between the two runs, so the take is one scene. labels-01: 744 frames in 5.1 min.
- **Delivery** (`pipeline.py deliver art-rna-v3`, version 1 settings, CRF 16 / 24), all 1920×1080 at 24 fps, 744 frames, 31.0 s:

  | File | Codec | Size |
  |---|---|---|
  | `art-rna-v3.mp4` (labelled) | H.264 | 12,042,979 B |
  | `art-rna-v3.webm` (labelled) | VP9 | 9,717,731 B |
  | `art-rna-v3-clean.mp4` | H.264 | 11,001,364 B |
  | `art-rna-v3-clean.webm` | VP9 | 8,532,309 B |

  Posters (clean): `-poster-repeat.png` (frame 72), `-poster-rnas.png` (360), `-poster-yadd.png` (540), `-poster-question.png` (720). Frames 220 and 700 of the labelled MP4 were decoded: the locus map, the pointers, the dashed "?" links and the AlphaFold notice sit where they should. On frame 700 the top-right evidence line ("Partner mean pLDDT 33 · complexes ipTM ≤ 0.24") runs over the DNA and reads less clearly there; the website's labels have a halo and read clearly.
- **Website** (2026-10-21). Version 3 replaces version 2 on amadeusbio.ai as a clean film (VP9 700k / 550k, H.264 900k / 700k, 1080 / 720), and the page draws the labels from `labels.json`. At version 2's web rates the atom-by-atom DNA cost about 3 dB; at these rates every file measures above version 2's web encode (42.4 / 41.8 dB at 1080, WebM / MP4; 41.8 / 41.6 dB at 720). The page's terms notice names this representation (cartoons with secondary structure estimated from the predicted Cα positions, RNA atom by atom, colours by confidence). Details: `docs/media.md` in the website repository, "ninth round". Not deployed.
