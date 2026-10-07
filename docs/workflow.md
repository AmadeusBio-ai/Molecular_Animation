# Workflow: from a brief to a delivered film

Every film follows the same path. The worked example is `examples/channelrhodopsin/`:
- **Input:** `sources/Nobel_Med_2026.md`, with the request "generate scientific illustrative animation for the molecular interaction. Make it pretty".
- **Output:** a 21 s narrative film in labelled and clean versions, MP4 and WebM, with three posters.

Times are for one RTX 5060 Ti and are only a guide.

## 0. Before you start

- Run `python pipeline.py doctor` (setup: `docs/setup.md`).
- If you will work interactively, open Blender 5.2 with the MCP add-on running.
- If you are continuing a project, read its `record.md`. The status line at the top says where it stands.

## 1. Understand the brief

**Goal:** a one-page `brief.md` that a stranger could build from.

1. **Scaffold the project.** Run `python pipeline.py new <name> --pdb <ID>`. It creates `projects/<name>/` with a working shot script, `shots.json`, `brief.md` and `record.md`. Pick the main structure now; you can add more later.
2. **Keep the inputs.**
   - Copy source documents unchanged into `projects/<name>/sources/`, and record where each came from (a person, a paper, an AI chat with its share link).
   - Keep reference clips and images in `references/`, which git ignores. Describe them in the brief instead of committing them.
   - Quote the request verbatim.
3. **Find the one idea.** Long briefs often propose several directions. Pick the one the brief recommends building first, or the strongest one, and state its causal chain in one sentence. For channelrhodopsin, the brief recommended a 12–15 s retinal-pocket shot. Its chain: "a photon isomerises retinal → the protein rearranges → a cation pathway connects".
4. **Name the evidence.** For each beat, write down which structure or data it comes from and its evidence level:
   - **experimental:** deposited coordinates;
   - **simulation-derived:** a trajectory, with its conditions;
   - **illustrative:** interpolation, a model or a symbol.

   Carry the brief's own warnings through. Channelrhodopsin carried "9GO2 is an early light-activated state, not a conducting one".
5. **Choose the look.** If the brief names a style or reference, match it. Otherwise use the studio molecular look:
   - atoms as spheres on a pale backdrop;
   - shallow depth of field;
   - one warm accent on the subject.
6. **Fix the deliverables.** Write down:
   - resolution, fps, length;
   - loop or narrative;
   - labelled and clean versions;
   - formats, posters, delivery folder.

   Default to 1920×1080. Use 24 fps for narrative films and 30 fps for web loops. Deliver MP4 + WebM + posters.
7. **Ask only what you can't decide.** Make sensible assumptions, write them in the brief, and keep going.

## 2. Ground the science

**Goal:** numbers you can trust, computed by code, not remembered.

1. Fetch every structure with `python pipeline.py pdb <IDs>`. Files go to `assets/pdb/`, and their checksums are recorded in `SHA256SUMS`.
2. Inspect each entry with `molanim.structure`:
   - chains;
   - the assembly operator for oligomers;
   - alt-locs and their occupancies;
   - ligands and their covalent links;
   - waters and crystallisation additives to drop;
   - missing atoms;
   - numbering (chimeras and mutants).

   For example, 9GO2 holds the activated conformer as alt B at 30 % occupancy, numbered +307. Alt A duplicates the dark state.
3. Measure every claim you will animate, and keep the numbers.
   - The retinal C12-C13=C14-C15 dihedral goes from −176° to +0.6°.
   - Lys132 NZ to Glu129 OE1 goes from 9.0 Å to 2.66 Å.
4. When the data and the story disagree, show the data and label the extra step as illustrative. In 9GO2 the pathway's free radius falls to about 0 Å at several points, so the film shows it interrupted first, then an illustrative open state.
5. Put project-specific science in a pure-numpy module next to the shot (like `examples/channelrhodopsin/c1c2.py`), with a test in `tests/`. Move anything general into `molanim` (`docs/framework.md`).

## 3. Plan the film in the script header

The constants at the top of the shot script are the storyboard. Edit them before writing scene code:

- **Beats and timeline:** named beats with frame ranges (or fractions of the film). This is editorial time, not molecular time.
- **`CAMERA`:** keys of (frame, aim, distance, azimuth, elevation, lens), with named aims resolved at build.
- **The palette:** sRGB 0–255, muted subject and one accent.
- **Representation scale factors.**
- **Labels:** captions, evidence tags, timescale labels and pointers, for a labelled film.

For a narrative science film, a good beat structure is:
1. Establish the context (wide view, the membrane, the light arriving).
2. Locate the actor (dive in, cut away to the pocket).
3. The cause.
4. A pause.
5. The effect.
6. The consequence (pathway, ions).

Hold each beat long enough to read. Channelrhodopsin spends 2–4 s per beat across 21 s.

Keep `shots.json` in step with the script: fps, count, render range, label pass, CRFs and posters.

## 4. Build

1. Extend the script with what the brief needs from `molanim`: morphs between states, pathways, membranes, particles, more structures. The case study shows each of these in use. Keep the housekeeping: scene reset by prefix, save only the scene, `RESULT`.
2. Build headless with `python pipeline.py build <name>`. Or, in the open Blender, run `runpy.run_path(...)` through MCP.
3. Make `RESULT` carry the checks:
   - counts;
   - the measured dihedrals and distances at the key frames;
   - the worst morph deviation;
   - the minimum clearances;
   - loop seam errors.

   Read it every time you build.
4. Rebuild twice in a live session and confirm that no `.001` duplicates or orphans with the prefix remain.

## 5. Look-dev on stills

1. Render the frames that define the film: the opening, each beat's key moment and the end. Run `python pipeline.py still <name> <frame> --percent 50`, and look at the PNG. Add `--overlay` to see the label pass.
2. Judge each frame:
   - Is the subject readable at a glance?
   - Is the change visible?
   - Does colour lead the eye to the active interaction?
   - Are the interacting partners in focus together?
3. When matching a reference, compare side by side and measure what can be measured: silhouette IoU, median colours, blur disc sizes.
4. Crop at full resolution to check fine detail (`tools/render.py --border x0,y0,x1,y1`).
5. Fold every change back into the script and rebuild.

## 6. Preview the motion

1. Run `python pipeline.py preview <name>`. It renders every 4th frame at 25 % with 16 samples into a new `preview-NN/` folder, and writes a contact sheet.
2. Check the timing on the contact sheet: beat order, holds, camera moves, label timing.
3. Evaluate motion numerically in Blender at specific frames: transforms, shape-key values, dihedrals over time, clearances.
4. `python pipeline.py motion <dir>` lists steps more than 2× their local median, which are jumps and pops. For loops, add `--loop N` to check the seam. Noise in low-sample previews inflates motion, so judge final motion on clean renders.
5. Iterate until the preview is right. Re-rendering a preview costs minutes; re-rendering a take costs hours.

## 7. Render the take

1. Run `python pipeline.py render <name> --take take-01`. It renders on the GPU, skips frames that already exist, and refuses to continue a take whose blend has changed. Channelrhodopsin took about 19 s per frame, 2.7 h for 504 frames, so run it in the background.
2. For loops, the render range includes the frame after the loop (`count + 1`) as a seam check. It must equal frame 1.
3. Render the label pass separately: `python pipeline.py render <name> --overlay --take labels-01`. It is a cheap EEVEE pass of a few minutes.
4. If a fix affects only some frames, you may re-render that range into a new take. Copy the unaffected frames across only after checking that the overlapping frames match: within 1/255, with no pixel off by more than 2. Record this in `record.md`.

## 8. Deliver

1. Run `python pipeline.py deliver <name>`. For each output it runs `tools/encode.py`, which produces:
   - H.264 MP4 (yuv420p, faststart) and VP9 WebM;
   - the label pass as an overlay, where configured;
   - a check that each file decodes to the expected frame count and duration.

   It then copies the poster frames from the take.
2. Decode a few frames from the delivered MP4 and look at them: the composite, the labels and the colour.
3. For web loops, choose CRFs per shot. Compare decoded frames with the PNGs, in crops and by PSNR, and balance file size. Record the choice in `shots.json`.
4. To play a film in a GitHub README, upload it as an attachment. GitHub strips `<video>` tags, and its content security policy blocks video served from the repository or a release. Only a file dropped into an issue or pull-request comment box plays: it becomes a `https://github.com/user-attachments/assets/...` URL, which renders as a player on a line of its own. Uploads are limited to 10 MB on free plans, so encode a lighter H.264 MP4 from the take and check it by PSNR against the PNGs (the case study's README clip is recorded in its `record.md`).

## 9. Record

1. Complete `record.md` (model: `examples/channelrhodopsin/record.md`):
   - a status line;
   - what was built;
   - the structural basis, with the numbers;
   - motion and evidence levels per beat;
   - how to reproduce it;
   - the checks, and how each was done;
   - the delivered files (codec, frames, duration, size);
   - render cost;
   - known differences and limits.
2. State the review method honestly, for example "reviewed from contact sheets, stills and decoded frames; not watched as continuous playback".
3. Add any general lesson to `docs/principles.md` or `docs/blender-5.md`, and any reusable code to `molanim`.

## Definition of done

- [ ] `brief.md` holds the request, its sources (with provenance), the chosen shot, evidence levels and deliverables.
- [ ] The shot script rebuilds the scene idempotently; `RESULT` reports the numerical checks.
- [ ] `shots.json` describes the shot, and `pipeline.py deliver <name>` reproduces the delivery from the take.
- [ ] Every beat has an evidence level, shown on screen in labelled films.
- [ ] Stills, a contact sheet and motion statistics were reviewed. Loops close (seam frame = frame 1).
- [ ] `delivery/<name>/` holds MP4, WebM and posters, all verified by `encode.py`.
- [ ] `record.md` is complete, including the review method and known limits.
