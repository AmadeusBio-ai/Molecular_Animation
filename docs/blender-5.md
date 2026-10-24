# Blender 5.x notes

This repo pins Blender 5.2 (5.2.2 LTS, Python 3.13). The coding models that drive it, Opus 5.5 included, learned `bpy` mostly from 2.8–4.x code. They write names that Blender 5 removed, confidently, and a render rarely shows which one broke. Three guards are kept in step:

- **This file:** what models write, and what works in 5.2.
- **`tools/api_probe.py`** checks each claim inside Blender. `pipeline.py doctor` runs it; on 5.2.2 all 30 facts hold. After a Blender upgrade, a failing fact names the row to revise.
- **`tools/bpy_lint.py`** flags the stale forms without Blender. Run it with `pipeline.py lint`; `pipeline.py build` runs it before Blender starts, and the test suite keeps the repo clean.

When an API surprises you, add a row here, a fact to the probe and a rule to the lint, in the same change.

## What models write, and what works in 5.2

Each row is a probe fact and, where code can show it, a lint rule.

| Area | A model writes | Blender 5.2 | Changed in |
| --- | --- | --- | --- |
| Engine id | `'BLENDER_EEVEE_NEXT'` | `'BLENDER_EEVEE'` (also `'CYCLES'`, `'BLENDER_WORKBENCH'`) | 5.0; `_NEXT` existed only in 4.2–4.5 |
| Python | 3.11 | 3.13. Compiled wheels must match it | 5.1 |
| Keyframes | `action.fcurves`, `action.groups`, `action.id_root` | `bpy_extras.anim_utils.action_get_channelbag_for_slot(action, slot).fcurves` (`action_ensure_channelbag_for_slot` creates one). `obj.keyframe_insert(path, frame=f)` makes the action, slot and channelbag. `molanim.blender.scene.fcurves` wraps it | 5.0 |
| Compositor | `scene.use_nodes = True`, `scene.node_tree` | `scene.compositing_node_group = bpy.data.node_groups.new(name, 'CompositorNodeTree')`, ending in a `NodeGroupOutput` with an `Image` socket (`molanim.blender.look.bloom`) | 5.0 |
| Compositor nodes | `CompositorNodeComposite`, `CompositorNodeMixRGB`, `…Math`, `…Value`, `…MapRange`, `…SepRGBA`, `…CombRGBA` | The group output (there is no Composite node); `ShaderNodeMix`, `ShaderNodeMath`, `ShaderNodeValue`, `ShaderNodeMapRange`; `CompositorNodeSeparateColor`, `CompositorNodeCombineColor` | 5.0 |
| Glare | `glare.glare_type = 'BLOOM'`, `glare.threshold` | Input sockets: `glare.inputs['Type'].default_value = 'Bloom'`, and `'Quality'`, `'Threshold'`, `'Strength'`, `'Size'` | 5.x |
| Materials, worlds | `mat.use_nodes = True` | Nothing: a new material has `Principled BSDF` + `Material Output`, a new world `Background` + `World Output`. Setting or reading `use_nodes` warns "expected to be removed in Blender 6.0" | 5.0 |
| Default nodes | `nt.nodes['Principled BSDF']` | `molanim.blender.nodes.by_type(nt, 'BSDF_PRINCIPLED')` (`'OUTPUT_MATERIAL'`, `'OUTPUT_WORLD'`, `'BACKGROUND'`). Default node names follow the UI language, because *Translate New Data Names* is on by default | always |
| Principled BSDF | `'Specular'`, `'Transmission'`, `'Clearcoat'`, `'Sheen'`, `'Emission'`, `'Subsurface'`, `'Subsurface Color'` | `'Specular IOR Level'`, `'Transmission Weight'`, `'Coat Weight'`, `'Sheen Weight'`, `'Emission Color'`, `'Subsurface Weight'`. The subsurface colour is the base colour | 4.0 |
| Transparency | `mat.blend_method = 'BLEND'`, `mat.shadow_method` | `mat.surface_render_method = 'BLENDED'` or `'DITHERED'`. `blend_method` remains but is marked deprecated; `shadow_method` is gone (`obj.visible_shadow`) | 4.2 |
| Mix node | `ShaderNodeMixRGB` (legacy, still present) | `ShaderNodeMix` with `data_type='RGBA'`. Address its sockets by identifier (`A_Color`, `B_Color`, `Factor_Float`, `Result_Color`), because several share a name | 3.4 |
| Geometry-node modifier inputs | `mod['Socket_2'] = x` (raises "id properties not supported for this type") | `getattr(mod.properties.inputs, identifier).value = x` (`molanim.blender.nodes.set_modifier_inputs`) | 5.2 |
| Node-group sockets | `ng.inputs.new(...)` | `ng.interface.new_socket(name, in_out='INPUT', socket_type='NodeSocketFloat')` | 4.0 |
| Shader nodes | `ShaderNodeTexMusgrave`; `ShaderNodeSeparateRGB`, `CombineRGB`, `SeparateHSV`, `CombineHSV`; `ShaderNodeTexPointDensity` | `ShaderNodeTexNoise` with `noise_type` (`'FBM'`, …); `ShaderNodeSeparateColor` and `CombineColor` with a mode; Point Density is gone | 3.3–5.0 |
| Sky texture | `sky_type = 'NISHITA'` | `'MULTIPLE_SCATTERING'` or `'SINGLE_SCATTERING'` | 5.x |
| EEVEE settings | `eevee.use_bloom`, `bloom_threshold`, `use_gtao`, `gtao_distance`, `use_ssr`, `use_soft_shadows` | Gone with EEVEE Legacy. Bloom is a compositor Glare; the AO distance is `view_layer.eevee.ambient_occlusion_distance`; reflections come from `eevee.use_raytracing` | 4.2 |
| Smooth shading | `mesh.use_auto_smooth`, `auto_smooth_angle`, `calc_normals()`, `calc_normals_split()` | `mesh.shade_smooth()`, then `mesh.set_sharp_from_angle(angle=…)`. Normals are always current: `mesh.corner_normals`, `mesh.normals_domain` | 4.0–4.1 |
| Boolean solver | `solver='FAST'` | `'FLOAT'`. The default is `'EXACT'`; `'MANIFOLD'` (4.5) needs manifold input | 5.0 |
| Video output | `image_settings.file_format = 'FFMPEG'` | Set `image_settings.media_type = 'VIDEO'` first (`'IMAGE'`, `'MULTI_LAYER_IMAGE'`). This repo writes PNG frames and encodes them with `tools/encode.py` | 5.0 |
| Drawing | `import bgl` | `gpu`. Call `gpu.init()` first under `--background` | 5.0; `gpu.init` 5.2 |
| Sequencer | `sequence_editor.sequences`, `sequences_all` | `strips`, `strips_all`; `context.sequencer_scene` | 5.0 |
| Operator context | `bpy.ops.x.y({'area': …}, …)` | `with bpy.context.temp_override(area=…, object=…):`, then check for `{'FINISHED'}` | 4.0 |
| Import and export | `bpy.ops.export_scene.obj`, `import_scene.obj`, `export_mesh.stl`, `import_mesh.ply`, … | `bpy.ops.wm.obj_export` / `obj_import`, `stl_export` / `stl_import`, `ply_export` / `ply_import` | 4.0–4.2 |
| Settings as dict items | `scene['cycles']['samples']` | `scene.cycles.samples`: RNA settings are not ID properties | 5.0 |
| Bone layers | `armature.layers`, `bone.layers` | Bone collections: `armature.collections.new(name)`, `bcoll.assign(bone)` | 4.0 |
| Primitives | `bpy.ops.mesh.primitive_cube_add()` for a 1-unit cube | It makes a 2-unit cube (`size` is the full edge length) and needs a context. Build from data: `bmesh.ops.create_cube(bm, size=1.0)`, `mesh.from_pydata` | always |

## Finding out what is valid

- **Enum values.** `[i.identifier for i in T.bl_rna.properties[p].enum_items]`. Dynamic enums under-report: on 5.2.2, `render.engine`'s list holds only `BLENDER_EEVEE`. Assign inside `try`/`except TypeError` instead; the message lists the valid values.
- **Whether a property exists.** Use `name in T.bl_rna.properties` (or `.functions`), or `hasattr` on an instance. `hasattr(bpy.types.Scene, 'compositing_node_group')` is `False` on 5.2.2: on the class, `hasattr` misses RNA properties, so it can't prove that something is gone.
- **Then the documentation.** Search the bundled docs through Blender MCP (`search_api_docs`, `get_python_api_docs`), then call `dir()` on a live object.

## Operators are the UI; scripts write data

A background run, or code from the MCP add-on's timer, has no 3D View, edit mode or selection for an operator to poll. Operators return only `{'FINISHED'}` or `{'CANCELLED'}`. On 5.2.2 a failed poll often names what was missing ("An edit-mesh with vertex or edge selection mode is required"), but the fix is the same: write to the data.

| A model reaches for | Write instead |
| --- | --- |
| `bpy.ops.object.modifier_apply()` | `bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))`; for a temporary mesh, `eo.to_mesh()` … `eo.to_mesh_clear()` |
| `bpy.ops.mesh.primitive_*_add()` | `bmesh.ops.create_*` or `mesh.from_pydata`; for molecules, `molanim.blender.mesh.points_mesh` |
| `bpy.ops.object.shade_smooth()` | `mesh.shade_smooth()`, `mesh.set_sharp_from_angle(angle=…)` |
| `bpy.ops.object.mode_set()` + `bpy.ops.mesh.*` | `bmesh` in object mode: `bm.from_mesh(me)` … `bm.to_mesh(me)` |
| `bpy.ops.wm.save_as_mainfile()` | `molanim.blender.scene.save_scene(scene, path)`: only that scene, and the open file keeps its path |
| `bpy.ops.outliner.orphans_purge()` | Remove only your prefix's datablocks (`molanim.blender.scene.reset_scene`) |

The pipeline uses one operator, `bpy.ops.render.render(write_still=True)`. It is fine headless; through MCP it blocks Blender's UI, so render with `pipeline.py`.

## References you hold

- Removing an object, modifier or other datablock invalidates Python references to it. Reading one afterwards raises `ReferenceError`, so collect names first.
- `obj.evaluated_get(depsgraph)` gives the result with modifiers and geometry nodes applied. Free a `to_mesh()` with `to_mesh_clear()`.
- Don't trust default names (`Cube.001`). Keep references, and give every datablock the shot's prefix.

## Measure, then look

Much of what goes wrong in a scene doesn't show in a still:
- a deprecated call that will break in 6.0;
- a geometry-node input of the wrong type, which Blender reports as an INFO-level node warning while the node outputs nothing;
- a stale API on a code path that the rendered frame didn't exercise.

After `RESULT`, `pipeline.py build` prints these: Python deprecation warnings (including those raised inside `molanim`), geometry-node warnings, lint warnings, and a Blender other than 5.2. Read them, and `RESULT`'s numbers, before rendering stills.

Guides on model habits in Blender, such as the article below, recommend a geometry census (watertight, manifold, self-intersection) before any render. That census is for meshes that will be 3D-printed or exported. The molecules here are point clouds drawn as spheres and SDF envelopes, so their equivalent is `RESULT`'s measured geometry, `pipeline.py motion` and `pipeline.py check`.

## Claims that did not hold on 5.2.2

Checked on 2026-10-24 against two sources on model habits in Blender: the article [Opus 5.5 Writes Blender Python for the Wrong Blender](https://x.com/0xCodio/status/2109275834984915150) (Codio, 2026-10-11) and the [blender-skills](https://github.com/EL4CTEO/blender-skills) collection (version 1.1.0). Most of their API claims hold and are in the table above. These don't:

- **The Boolean default.** The article calls the default solver a trap for messy input. On 5.2.2 the Boolean modifier defaults to `EXACT`, the solver that handles overlapping geometry; `FLOAT` fails on overlaps and `MANIFOLD` needs manifold input.
- **Poll errors.** The article says a failed poll gives no reason. On 5.2.2 many polls name what was missing.
- **Deprecated is not removed.** `Material.blend_method`, `ShaderNodeMixRGB` and `CompositorNodeGamma` still exist on 5.2.2 (blender-skills lists Gamma as moved to shader nodes), and `use_nodes` still works but warns. Code that uses them runs today and is expected to break in 6.0, which is why the lint warns on them rather than failing.

## Measured notes

- **`CompositorNodeMaskToSDF`** turns a boolean mask into a pixel-distance field, which is useful for drawing outlines of a mask.
- **Noise Texture statistics** (measured, for calibrated motion). The RMS per axis of (Color − 0.5) is 0.0912 for 4D noise at Detail 1 and 0.1223 at Detail 0. At Detail 0 its autocorrelation falls to 1/e at a lag of 0.58 noise units, along W or in space. `molanim.blender.groups` divides by these, so its amplitudes are RMS displacements in Å and its correlation times are in clock time.
- **Lookup tables.** Geometry nodes read per-frame data (normal-mode amplitudes, side-chain angles) from a vertex-only mesh: `Object Info` with `transform_space='ORIGINAL'`, then `Sample Index` at row (frame − 1) × items + item (`molanim.blender.mesh.table`). Float attributes hold integer indices exactly below 2²⁴.
- **Volume-grid nodes.** `GeometryNodePointsToSDFGrid`, `SDFGridOffset`, `SDFGridMean` and `GridToMesh` are available. A negative `SDFGridOffset` distance shrinks the surface.
- **View layers.** Objects in a collection excluded from the window's view layer are not evaluated by `scene.frame_set`. Read them through `scene.view_layers[name].depsgraph` after `depsgraph.update()`.
- **Context.** Code run by the MCP add-on runs from a timer, where `bpy.context.window` may be `None`. Fall back to `bpy.context.window_manager.windows[0]`, and prefer the data API to `bpy.ops`.
- **Saving one scene.** `bpy.data.libraries.write(path, {scene}, path_remap='RELATIVE_ALL', fake_user=True)` writes that scene and its dependencies without changing the open file's path or touching other scenes.

## Rendering and the command line

- Headless: `blender -b --factory-startup <file.blend> --python tools/render.py -- ...`. `--factory-startup` ignores user preferences and add-ons, so `render.py` selects the Cycles device itself (OptiX, then CUDA, HIP, Metal, oneAPI).
- A plain `blender -b file.blend -a` renders with whatever device the user preferences hold, possibly the CPU.
- Add `--python-exit-code 1`, or a Python error leaves the exit status at 0 and a failed build looks like a success. `pipeline.py` adds it, and also requires the script's `RESULT` line.
- Arguments run in the order given (Blender manual, "Argument Order"). Open the `.blend` first, then set render options, then render: `blender -b file.blend -o //out/ -f 1`. An `-o` before the file is overwritten when the file loads, and a `-f` before `-o` renders first.
- Everything after `--` reaches Python as `sys.argv[sys.argv.index('--') + 1:]`.

## ffmpeg

- Recent builds: use `-fps_mode`, not `-vsync`.
- The VP9 WebM container gets new random IDs on every encode, so re-encoded WebMs differ byte-for-byte while their decoded frames are identical. Compare with `ffmpeg -i f.webm -f framemd5 -`.
