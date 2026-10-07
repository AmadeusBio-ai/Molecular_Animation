# Contributing

Thanks for helping. This project values honest science and readable code as much as beautiful pictures.

## Getting set up

Follow `docs/setup.md`. For framework work without Blender:

```
pip install -r requirements.txt pytest
python -m pytest tests
```

For anything that touches `molanim.blender`, a shot script or the pipeline, you also need Blender 5.2 and a GPU. Run `python pipeline.py doctor`.

## What to contribute

- **Framework features** (`molanim/`). A feature belongs here when more than one film needs it: a structure parser, a representation, a motion model, a camera move, a label style.
  - Keep science in pure numpy with a unit test.
  - Keep Blender code thin.
  - Document the feature in `docs/framework.md`.
- **Case studies** (`examples/<name>/`). A finished film made with the framework, with:
  - its brief and sources, with provenance;
  - the shot script and project science;
  - a `shots.json` and a complete `record.md`;
  - a test that pins its key scientific numbers.

  Large media go in a GitHub release (`"release"` in `shots.json`), not in git.
- **Fixes and portability**: macOS and Linux reports, newer Blender versions (`docs/blender-5.md`), documentation.

## Rules that keep the project trustworthy

- **Evidence levels.** Every animated claim is labelled experimental, simulation-derived or illustrative, in the script, on screen and in the record. Claims are measured in code, not copied from a brief.
- **Reproducibility.**
  - Every picture rebuilds from its script.
  - New structures come in through `python pipeline.py pdb` (which records checksums).
  - Changes to existing behaviour keep `python pipeline.py check channelrhodopsin` passing, or include an updated, re-verified case study.
- **Rights.**
  - Don't commit third-party media (reference clips, logos, fonts, renders of other people's work) unless the license allows redistribution.
  - Say where every source document came from, including AI-generated briefs (tool and share link).
  - PDB data are CC0.
- **Honest records.** Say how each thing was checked, and whether a film was watched as playback or only inspected as frames.

## Style

- Python 3.10+, numpy, standard library. Blender scripts use the data API and `bmesh` in preference to `bpy.ops`.
- Match the surrounding code: concise docstrings that say why, constants at the top of shot scripts, colours as sRGB 0–255.
- Keep functions small and named for what they do in the film (`molecule`, `tube`, `keep_clear`).

## Pull requests

1. Open an issue first for anything large.
2. Keep each PR focused, with tests (and `docs/framework.md`) updated in the same PR.
3. CI runs `compileall`, the test suite and the structure checksums. For visual changes, attach a still or contact sheet, and the `pipeline.py check` output if the case study is affected.

By contributing you agree that your contributions are licensed under the Apache License 2.0 (`LICENSE`).
