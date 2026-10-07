# Case study: channelrhodopsin, "The twist that opens a pathway"

| | | |
| --- | --- | --- |
| ![Membrane section](../../docs/media/channelrhodopsin-wide.jpg) | ![Retinal twist](../../docs/media/channelrhodopsin-retinal.jpg) | ![Open pathway](../../docs/media/channelrhodopsin-channel.jpg) |

A 21 s scientific illustration for the 2026 Nobel Prize in Physiology or Medicine (light-gated ion channels and optogenetics), made from a single brief with this framework:
1. A photon isomerises retinal in channelrhodopsin C1C2.
2. The protein's interaction network rearranges (Lys132 swings to Glu129).
3. The cation pathway is shown first as the crystal has it, interrupted, then open in a labelled, illustrative conducting-state model.

The film comes in a labelled and a clean version (1920×1080, 24 fps, MP4 + WebM), published in the `v0.1.0` release. Get them with `python pipeline.py fetch channelrhodopsin`.

## From brief to film

| Step | Here |
| --- | --- |
| **Brief as given** | `sources/Nobel_Med_2026.md`, generated with ChatGPT; provenance in `sources/README.md`. It proposes six directions and recommends the retinal-pocket shot first. |
| **Brief as understood** | `brief.md`: the one idea, structures with evidence levels, the claims to verify, look and deliverables |
| **Science, checked in code** | `c1c2.py`: 9GO1/9GO2 matched atom by atom (alt B, +307 numbering); retinal dihedral −176° → +0.6°; Lys132–Glu129 9.0 → 2.66 Å; the 9GO2 pathway is interrupted (free radius ≈ 0 Å) |
| **Storyboard as constants** | top of `channelrhodopsin.py`: timeline beats, camera keys, palette, captions, evidence tags, timescales, pointers |
| **Build** | `python pipeline.py build channelrhodopsin` (~25 s): 2 × 2,321 protein atoms, 494k lipid atoms, ions, photons, a label scene |
| **Render and deliver** | `shots.json`: take, label pass, CRFs and poster frames; `pipeline.py render` / `deliver` |
| **Record** | `record.md`: what was built, the numbers, evidence per beat, checks, review method, known limits |

## What it demonstrates

- **Evidence levels on screen.** Each beat is tagged as X-ray structure, illustrative morph or illustrative model. Timescales are labels ("within a picosecond", "microseconds", "milliseconds"), not a running clock.
- **One coordinate source.** A constrained morph between deposited states is baked as absolute shape keys. Spheres, sticks and the salt-bridge marker all follow it (`molanim.morph`, `molanim.blender.mesh.absolute_keys`).
- **Representation modes.** The camera moves from a sphere surface to ball-and-stick for the mechanism, then to a cavity tube for connectivity. Camera-aimed cutaways and a section slab replace global transparency (`molanim.blender.groups.molecule`).
- **Data before story.** The crystal's pathway is interrupted, so the film shows that first. The opening is a labelled illustrative step (`molanim.pathway`).
- **Honest particles.** Ions dwell irregularly at binding sites, never share a site, and keep at least 1.70 Å from every atom surface (`molanim.particles`).
- **Separate label pass.** The labelled and clean films come from one Cycles render (`molanim.blender.labels`).

## Reproduce

```
python pipeline.py build channelrhodopsin
python pipeline.py fetch channelrhodopsin       # the delivered films and posters
python pipeline.py check channelrhodopsin       # renders frame 70 and compares it with the delivered poster
```

A full re-render takes about 2.7 h on an RTX 5060 Ti (128 samples, 1080p); `record.md` gives the commands. The refactor onto `molanim` was verified to reproduce the delivered pictures: posters within 1/255, label frames pixel-identical.
