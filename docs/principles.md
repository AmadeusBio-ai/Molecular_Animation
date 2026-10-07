# Principles

These principles come from the case study (`examples/channelrhodopsin/`) and earlier productions in the same pipeline. Numbers quoted without a source are defaults that worked; numbers attributed to the case study were measured there. Apply them with judgement, not as a checklist.

## 1. A film explains one causal idea

- State the film's idea as a causal chain in one sentence, and make every beat serve it. A glowing protein rotating in space is scenery, not a story.
- Make the cause readable first. Then pause. Then show the effect. In channelrhodopsin, the retinal finishes its twist, the camera holds, and only then does the interaction network rearrange. The pause shows causality without exaggerating the motion.
- Prove the approach on one short, polished shot before scaling up. That shot must show four things:
  - the molecular geometry stays credible;
  - the change is readable;
  - the transitions between representations are elegant;
  - the evidence level is clear.
- Small structural changes can carry a big functional story. You don't have to exaggerate the displacement; reveal it with framing, colour and timing.

## 2. Evidence is part of the picture

- Give every beat an evidence level:
  - **experimental:** deposited coordinates;
  - **simulation-derived:** a trajectory, kept with its construct, ions and conditions;
  - **illustrative:** an interpolation, model or symbol.

  Keep the level in three places: the timeline constants, an on-screen tag in labelled films, and the record. Channelrhodopsin's tags read "X-RAY STRUCTURE · PDB 9GO1", "ILLUSTRATIVE MORPH · 9GO1 → 9GO2", and "ILLUSTRATIVE CONDUCTING-STATE MODEL".
- Check claims numerically at build time and report the numbers in `RESULT`. That covers dihedrals, distances, occupancies and free radii.
- When the data disagrees with the story, show what the data says first. Then add the illustrative step and label it. For example, 9GO2's pathway is interrupted (free radius about 0 Å), so the film shows it closed before the labelled open model.
- Handle structure details explicitly and record each decision:
  - alt-locs (which conformer is the activated one);
  - assembly operators (build the oligomer from the deposited operator);
  - atoms with no partner state (keep them in place and count them);
  - crystallisation additives (drop waters and monoolein);
  - chimera or mutant numbering.
- Don't invent features. Follow each protomer's own pathway, not a pore at the dimer interface. Don't relabel an ion to fit the narration. Don't present an animated rate as physiological.
- Mark time and scale honestly. Use changing timescale labels ("within a picosecond", "microseconds", "milliseconds") rather than one running clock. Make symbols such as photons drawn as wave packets, or a blue key light, either labelled or obviously symbolic.

## 3. One coordinate source, many representations

- Animate atoms, then derive everything else from them. Spheres, sticks, salt-bridge markers and surfaces all read the same per-frame positions. Channelrhodopsin stores its morph as absolute shape keys on one mesh. Never animate separate copies of the same molecule.
- Generate surfaces from the atoms on every frame (`Points to SDF Grid` → `SDF Grid Offset` → `Grid to Mesh`; see `docs/blender-5.md`). Never blend independently meshed surfaces, whose vertices don't correspond.
- Morph between structures by constrained interpolation, not by a raw lerp (`molanim.morph`):
  - match atoms by chain, residue and name;
  - keep bond lengths, angles and 1–4 distances, and keep non-bonded atoms apart;
  - stage the motion so parts that must move together do. Retinal moves with Trp262, because the twist alone puts the C20 methyl 1.9 Å into the ring;
  - make the key dihedral change monotonically;
  - report the worst bond deviation (0.15–0.22 Å here).
- Use three representation modes:
  - **surface (spheres)** for location and scale;
  - **ball-and-stick** for mechanism;
  - **cavity** for connectivity.

  Move between them deliberately, with one mode dominant at a time. Open a camera-aimed cutaway or section rather than making the whole protein transparent, which turns a mechanism into noise.

## 4. The house look: studio molecular

This is the default look of `templates/shot/` and the case study. A brief that asks for something else wins.

**Scale and atoms**
- 1 Blender unit = 1 Å.
- Atoms are point-cloud spheres from one geometry-nodes group (`molanim.blender.groups.molecule`). This is cheap even for hundreds of thousands of atoms.
- Context protein uses about 0.64 × the van der Waals radius, so the beads stay legible.
- Each atom mixes randomly between a dark and a light tone of its colour (the `shade` attribute). This gives the beaded, tactile texture.

**Backdrop and light**
- The camera sees a pale, flat or softly graded backdrop, while objects are lit by a separate ambient colour (`Light Path: Is Camera Ray`; see `molanim.blender.look.gradient_world`).
- Add a soft key light and a restrained rim.

**Colour**
- Keep the subject muted (teal or slate protein) and give one warm accent to the hero: amber retinal.
- Use element colours only on the few chemically important atoms.
- Reserve brightness and glow for the interaction that is happening now.

**Depth of field**
- Use a shallow depth of field, but keep both interaction partners in the focal plane.
- Channelrhodopsin uses an aperture radius of 0.016 × the focus distance.
- For depth behind the subject, place enlarged copies of molecules (about ×20, thousands of Å behind) so they defocus into bokeh. Check the blur disc sizes against the thin-lens prediction rather than guessing.

**Membranes and ions**
- A membrane is context. Build it procedurally (`molanim.membrane.bilayer`), drop lipids that clash with the protein, and cut it away in front with an architectural section.
- Keep solvent and ions sparse, and show them only near the mechanism.

## 5. Motion

- **Breathing.** Sample coherent noise at (position + circle(t)). The result is spatially smooth and exactly periodic over the loop. Use a sway of a few tenths to a few Å over a large scale, plus a fine jitter below about 0.5 Å (`groups.breath`; set `loop_frames` for loops). When matching a reference, measure its motion in px per frame rather than guessing.
- **Camera.**
  - Use few keys, eased moves, and named aims (retinal, network, pore).
  - Interpolate dives in log-distance, so the zoom is a steady percentage per frame (3–4 % in channelrhodopsin).
  - Hold still on the signature moment.
- **Stochastic particles.**
  - Ions and waters wander, dwell at sites for irregular times (5–16 frames), and never share a site.
  - Keep them clear of atoms: every ion centre stays at least 1.70 Å from each rendered atom surface (`molanim.particles.keep_clear`).
  - Never make laminar streams, evenly spaced beads, or perfectly timed hand-offs.
- **Rigid bodies.** Check them for collisions on every frame, for example with a separating-axis test. Fix a collision in the motion (lift, shrink, re-time), not by hiding it.
- **Velocity continuity.** Limit the per-frame step and the change of step. A pop or stop at a beat boundary reads as a mistake.

## 6. Loops

- A seamless loop of N frames has frame N+1 identical to frame 1. Render N+1 as the seam check and deliver N.
- Drive everything with periodic functions of time: circles in noise space, cyclic keys, constant-speed orbits (`timeline.orbit_path`), or rotations that end on a symmetry of the object.
- Key one frame beyond each end (frame 0 = N, frame N+2 = 2), so that motion blur and velocity are continuous across the seam.
- Check the seam three ways:
  - evaluated geometry at 1 vs N+1 (zero);
  - pixels (mean below about 0.01 out of 255);
  - the N → 1 step against the typical step.

  Encoders put a keyframe on frame 1, so a slightly larger seam step in the MP4 is normal.

## 7. Labels and typography

- Labels are a separate, cheap EEVEE pass of transparent PNGs, composited at encode time (`tools/encode.py --overlay`; `molanim.blender.labels`). One picture render then yields both labelled and clean films, and text can change without re-rendering Cycles.
- Each label needs a soft halo behind its ink. Switch ink and halo together with the shot's brightness: dark ink on pale shots, light ink on close-ups.
- A labelled science film uses five label types:
  - a short caption (title and subtitle) per beat;
  - an evidence tag in a top corner;
  - a timescale label;
  - pointers anchored to projected 3D points that follow the motion;
  - a header for the occasion.
- Keep labels clear of the subject, and move them when the composition changes.
- Typeset properly: Na⁺ with a real superscript, arrows, and "·" separators.

## 8. Colour accuracy

- Write colours as sRGB 0–255 in the script and convert them exactly to linear (`molanim.color.srgb`).
- For brand or CSS matching, mix opacities in sRGB, then convert, so full-opacity colours stay exact.
- Measure rendered colour on the frame (the median of a region) against the target. Correct with per-tone albedo gains. Specular reflection lifts near-black tones by 15–20 levels in Cycles; correct or accept it knowingly.
- VP9 removes dither and fine grain at any CRF. Smooth gradients over about 20 levels may band in the WebM.

## 9. Rendering, takes and encoding

- Look-dev stills at 50 %. Previews at 25 %, with 16 samples, every 4th frame. Finals at full resolution, with 64–128 samples, adaptive and denoised.
- Render headless, never through MCP.
- Start a new take whenever anything changes. You may splice a partial re-render only after checking that the overlapping frames are identical.
- Choose CRFs by content.

  | Content | CRF (MP4 / WebM) |
  | --- | --- |
  | Science films | 16 / 24 |
  | Line art | 23 / 36 |
  | High-entropy content (particle clouds, many glowing lines) | 26–27 / 41–44 |
  | Grain or dither that must survive | 18–19 / 26–28 |

  Compare decoded frames with the PNGs by crops and PSNR. For the web, keep files under about 9 MB.
- Posters are frames of the delivered take, copied, not re-rendered. Choose an informative frame: mid-twist, or the reduced-motion pose for web loops.

## 10. Review honestly

- **Look.** Use full-resolution stills and crops, contact sheets, and frames decoded from the deliverable.
- **Measure.**
  - per-frame difference statistics (`pipeline.py motion`);
  - seams;
  - median colours;
  - clearances and collisions;
  - Blender's evaluated geometry against the numpy reference;
  - silhouette IoU against a reference.
- **Write down the method.** If the film was reviewed from frames and statistics and not watched as playback, say so. List the known differences from the reference and the limits of the evidence. Don't claim a match that wasn't measured.

## 11. Scripts are the source

- Every picture is rebuilt from a script, and the `.blend` is a build product. The scene reset is idempotent, scenes are named and prefixed, and only the target scene is saved.
- Put the plan (timeline, camera, palette, labels) in constants at the top of the script, so the script itself is the storyboard.
- Keep science in pure numpy where it can be tested, and keep Blender code thin around it.
- `RESULT` reports the checks on every build, so a regression shows up at build time, not after a four-hour render.
