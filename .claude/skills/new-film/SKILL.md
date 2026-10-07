---
name: new-film
description: Turn a brief (a request plus source documents and/or reference media, e.g. a document like examples/channelrhodopsin/sources/Nobel_Med_2026.md) into a delivered molecular animation with this repo's framework - project scaffold, brief, science checks, Blender shot script, look-dev, preview, final take, encoded MP4/WebM + posters, and a production record. Use when the user hands over a brief, a reference clip or a scientific document and asks for an animation, film, loop or still.
argument-hint: <brief, source document or reference>
---

# New film from a brief

Input: $ARGUMENTS

Follow `docs/workflow.md`. It is the authority; the steps below are a checklist. Read `docs/principles.md`, `docs/framework.md` and the case study `examples/channelrhodopsin/` before planning. Use judgement: adapt the steps to the brief and record your decisions.

1. **Intake.**
   - Read the brief and pick the main structure.
   - Run `python pipeline.py new <name> --pdb <ID> [--highlight RES] [--loop]`.
   - Copy the source document unchanged into `projects/<name>/sources/` and record its provenance. If the user gives one, include the generating tool and its share link.
   - Fill in `brief.md`: the request verbatim, the one idea, the chosen first shot, structures with evidence levels, beats, look and deliverables.
   - Ask the user only about decisions you genuinely can't make. Otherwise state your assumptions in the brief and continue.
2. **Science.**
   - Fetch more structures if needed with `python pipeline.py pdb <IDs>`.
   - Inspect chains, alt-locs, assemblies, ligands and numbering with `molanim.structure`.
   - Measure every claim the film depends on, with code: put it in a pure-numpy module next to the shot, with a test.
   - Where the data and the story disagree, show the data and label the illustrative step.
3. **Plan in the script header.** Set the timeline, camera keys, palette and label text as constants. Add what the brief needs from `molanim`: morph, pathway, membrane, particles, more structures. The case study shows each one.
4. **Build.** Run `python pipeline.py build <name>`, or `runpy` through Blender MCP. Read `RESULT`, which should report the numerical checks.
5. **Look-dev.**
   - Run `python pipeline.py still <name> <frame> --percent 50` (add `--overlay` for labels) at each key frame, and read the PNGs.
   - Fold every fix back into the script.
6. **Preview.** Run `python pipeline.py preview <name>` and read the contact sheet. Run `python pipeline.py motion` on the preview folder. Fix timing before any final render.
7. **Final.**
   - Run `python pipeline.py render <name> --take take-NN` in the background, then `--overlay --take labels-NN`.
   - Point `shots.json` at both takes, then run `python pipeline.py deliver <name>`.
   - Decode a few delivered frames and look at them.
8. **Record.** Complete `record.md` (model: `examples/channelrhodopsin/record.md`). Add general lessons to `docs/principles.md`, and general code to `molanim` with tests.

When a step needs hours of rendering, say so and give an estimate (about 19 s per 1080p Cycles frame at 128 samples on an RTX 5060 Ti) before starting it.

Report at the end:
- the delivered files;
- the evidence levels;
- what was checked and how;
- the known limits, including whether the film was watched as playback or only inspected as frames.
