# Molecular Animation: agent guide

This repository turns a brief into finished molecular animation. A brief is a request, plus any source documents and reference media. The result is a scripted Blender scene, rendered takes, MP4 and WebM films with posters, and a production record that says what is experimental and what is illustrative. Everything is built in Blender 5.2, usually driven through Blender MCP, with the `molanim` framework, and every result can be rebuilt from its script.

Read before starting a film:
- `docs/workflow.md`: how a brief becomes a delivered film.
- `docs/principles.md`: what makes these films good and honest.
- `docs/framework.md`: the `molanim` API and the pipeline tools.
- `docs/motion.md`: how molecules move, with rates and sources, and how the films show it.
- `docs/blender-5.md`: the Blender 5.2 API, and what models trained on older Blender write instead.
- `examples/channelrhodopsin/`: the worked case study, from brief to delivered film.

Setup is in `docs/setup.md`.

## Operating rules

- **Understand → Build → Inspect → Refine → Deliver.**
  - Read the brief and its sources, and decide what the film must make clear.
  - Build it from a script.
  - Look at real renders and fix what you see.
  - Encode the film and write the record.

  Iterate on stills and cheap previews. Spend final-render hours only on a scene that already works.
- **Art first, honest science.** The goal is beautiful, readable illustration, not scientific validation, but the evidence must never be misrepresented.
  - Every beat carries an evidence level: experimental, simulation-derived or illustrative. It appears in the script, on screen when the film is labelled, and in the record.
  - Check the brief's structural claims numerically before animating them. Briefs, including AI-generated ones, can be wrong.
- **Judgement over procedure.** These rules describe what has worked. Adapt them to the brief, own the creative decisions, and record why you made them.
- **One idea per shot.** Find the causal chain the brief cares about and stage it so a viewer can follow it. When a brief proposes several directions, first make one polished shot: its recommended first shot, or the strongest one.
- **Generalise deliberately.** Project-specific science lives next to the shot (like `examples/channelrhodopsin/c1c2.py`). Promote code into `molanim` only when it is general, and give it a test.
- **Honest review.** Say how each thing was checked: stills, contact sheets, statistics, decoded frames or playback. Never claim a visual match you did not check.

## Given a new brief

1. Run `python pipeline.py new <name> --pdb <ID> [--highlight RES] [--loop]`. It scaffolds `projects/<name>/` from `templates/shot/`: a working shot script, `shots.json`, `brief.md`, `record.md` and `sources/`.
2. Put the source documents, unchanged, in `projects/<name>/sources/`, and record their provenance (e.g. an AI chat's share link). Keep reference media in `references/`, which git ignores. Fill in `brief.md`: the request verbatim, the chosen shot, structures and evidence levels, beats, look and deliverables.

   Defaults:
   - 1920×1080.
   - 24 fps for narrative science films; 30 fps for web loops.
   - MP4, WebM and poster PNGs.
   - A labelled and a clean version of science films.
3. Fetch any further structures with `python pipeline.py pdb <IDs>`. Inspect their chains, alt-locs, assemblies and ligands, and verify the facts you will animate.
4. Make the script yours, using `molanim` and the case study as needed. Then run `python pipeline.py build <name>`, and read `RESULT` and the notes printed after it.
5. Do look-dev on stills (`pipeline.py still`) and view them. Then render a preview (`pipeline.py preview`) and review its contact sheet and `pipeline.py motion`, and check the busiest moves on consecutive frames (`preview --frames A-B --step 1`).
6. Render the final take and the label pass (`pipeline.py render`), then run `pipeline.py deliver <name>`.
7. Complete `record.md`: the status, numbers, evidence per beat, checks with their method, and known limits.

## Layout

| Path | Contents |
| --- | --- |
| `molanim/` | The framework. Pure-numpy science (`structure`, `morph`, `pathway`, `membrane`, `dynamics`, `particles`, `timeline`, `color`) and Blender helpers (`molanim.blender`: `scene`, `nodes`, `groups`, `mesh`, `look`, `rig`, `labels`) |
| `examples/<name>/` | Finished case studies: `brief.md`, `sources/`, the shot script, project science, `shots.json`, `record.md` |
| `projects/<name>/` | Your films, scaffolded by `pipeline.py new` |
| `templates/shot/` | The scaffold copied by `pipeline.py new` |
| `assets/pdb/` | mmCIF structures from RCSB, with `SHA256SUMS` (shared by all projects) |
| `tools/` | `render.py` (inside Blender), `encode.py`, `bpy_lint.py` (stale Blender APIs, no Blender needed), `api_probe.py` (the 5.2 API facts, inside Blender), the MCP smoke test, the Windows MCP launcher |
| `tests/` | pytest suite for the pure layer, the case-study science and the lint; runs in CI without Blender |
| `references/` | Local reference media (git-ignored) |
| `renders/<shot>/` | `dev/` stills, `preview-NN/`, `take-NN/`, `labels-NN/` (git-ignored) |
| `delivery/<shot>/` | Encoded films and posters (git-ignored; the case study's are in the GitHub release) |

`.blend` files are build products. They are written next to their script and ignored by git.

## Pipeline

| Step | Command |
| --- | --- |
| Check the machine | `python pipeline.py doctor` (includes the Blender 5.2 API facts that `docs/blender-5.md` relies on) |
| Lint Blender code | `python pipeline.py lint [paths]` (`build` runs it on the shot's folder first) |
| Start a project | `python pipeline.py new <name> --pdb <ID>` |
| Fetch structures | `python pipeline.py pdb <IDs>` |
| Build a scene headless | `python pipeline.py build <shot>` (RESULT saved to `renders/<shot>/build-result.json`) |
| Still for look-dev | `python pipeline.py still <shot> <frame> [--percent 50] [--samples N] [--overlay]` |
| Preview sequence | `python pipeline.py preview <shot> [--frames A-B] [--step 4 --percent 25 --samples 16]` (writes a contact sheet) |
| Final take | `python pipeline.py render <shot> --take take-NN [--frames A-B]` (resumable; `--overlay --take labels-NN` for labels) |
| Inspect a sequence | `python pipeline.py sheet <dir>`, `python pipeline.py motion <dir> [--loop N]` |
| Encode and verify | `python pipeline.py deliver <shot>` |
| Reproducibility | `python -m pytest tests`, `python pipeline.py smoke`, `python pipeline.py check <shot>` (renders a poster frame and compares it with the delivered poster) |

Start a new take whenever the scene, assets or render settings change, and never mix takes. You may re-render part of a take only if the overlapping frames are checked to be identical.

## Script conventions

The template (`templates/shot/shot.py`) follows all of these.

- Find the repo root from `__file__` (`HERE.parents[1]` for a project folder), put it on `sys.path`, and call `molanim.reload()` before importing. Never hard-code an absolute path.
- Scripts are idempotent. Each one rebuilds one named scene with a datablock name prefix, through `molanim.blender.scene.reset_scene`. Never purge orphans file-wide or reset the file (`read_factory_settings`, `read_homefile`): the open file may hold the user's work.
- Save only the target scene (`scene.save_scene`).
- Prefer the data API and `bmesh` to `bpy.ops`. Scripts run from the MCP add-on's timer, where `context.window` may be missing.
- Put the storyboard (timeline, camera keys, palette in sRGB 0-255, label text) as constants at the top. When a still shows a problem, fix it in the constants first; change the code's structure only when the constants can't express the fix.
- Put project science in pure numpy with a test.
- End with a JSON-serialisable `RESULT` dict that summarises what was built and the numerical checks.
- Edit the script and rebuild. Ad-hoc code is fine for inspection and experiments, but fold anything worth keeping back into the script.

## Blender 5.2 and your habits

Your `bpy` knowledge comes mostly from 2.8–4.x code, and Blender 5 moved much of the API. Stale names come out with confidence, and a render rarely shows which one broke. This repo pins Blender 5.2 (5.2.2 LTS, Python 3.13).

- **Check before you write an API from memory.** `docs/blender-5.md` lists what models write and what works in 5.2, and `tools/api_probe.py` checks every row inside Blender (`pipeline.py doctor`). Then check the bundled docs (`search_api_docs`, `get_python_api_docs`), then `dir()`. The ones that bite most often:
  - F-curves live in channelbags.
  - EEVEE's engine id is `BLENDER_EEVEE`.
  - Modifier inputs are set through `mod.properties.inputs`.
  - The compositor is a node group. New materials and worlds already have node trees: don't set `use_nodes`.
  - Principled inputs are `Specular IOR Level`, `Coat Weight`, `Emission Color` and so on.
  - Find default nodes by type (`molanim.blender.nodes.by_type`), not by name: names follow the UI language.
- **The lint runs first.** `pipeline.py build` lints the shot's folder (`pipeline.py lint`). An error is an API that 5.2 rejects, and it stops the build before Blender starts. A warning is deprecated or fragile code. Fix the code; use `# bpy-lint: ignore` only for a line that is right anyway.
- **Measure, then look.** After `RESULT`, `build` prints what a render would not show: deprecation warnings, geometry-node warnings and lint warnings. Read them before rendering stills.
- **Close the loop.** When an API surprises you, add a row to `docs/blender-5.md`, a fact to `tools/api_probe.py` and a rule to `tools/bpy_lint.py`, in the same change.

## Blender MCP

- Run a script in the open Blender with `execute_blender_code`:
  ```python
  import runpy
  result = runpy.run_path(r'<repo>/projects/<name>/<script>.py', run_name='__main__')['RESULT']
  ```
- Live MCP calls block Blender's UI and time out after 300 s. Render headless (`pipeline.py`, which uses `--factory-startup` and selects the GPU itself).
- Review visually as well as numerically:
  - Render stills and look at them.
  - Use `get_screenshot_of_window_as_image` for the viewport.
  - Evaluate transforms and geometry at specific frames.

## Records and licensing

- `brief.md` records what was asked and where it came from. `record.md` records what was built, how to reproduce it, what was checked and how, the evidence levels, and the known limits. Keep both short and factual, and distinguish inspecting frames from watching playback.
- When something general is learned, add it to `docs/principles.md`, `docs/blender-5.md` or `molanim`, not only to one project's record.
- Don't commit third-party media (reference clips, logos, fonts) unless you hold the rights. PDB data are CC0.
