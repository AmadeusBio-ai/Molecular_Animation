# Blender 5.x notes

These were checked on Blender 5.2.2 LTS while building the shots in this repo. Before relying on an API, check it against the bundled docs (Blender MCP `search_api_docs` / `get_python_api_docs`).

## Python API

- **Animation.** F-curves live in channelbags: `bpy_extras.anim_utils.action_get_channelbag_for_slot(action, slot)`. `Action.fcurves` is gone.
- **Engines.** EEVEE's id is `BLENDER_EEVEE`. Older scripts may try `BLENDER_EEVEE_NEXT` as a fallback.
- **Principled BSDF.** Inputs are named `Coat Weight`, `Transmission Weight`, `Sheen Weight`, `Specular IOR Level`, and so on.
- **Geometry-nodes modifier inputs.** Set them with `getattr(mod.properties.inputs, socket.identifier).value = x`. `mod['Socket_0'] = x` raises "doesn't support IDProperties". `molanim.blender.nodes.set_modifier_inputs` wraps this.
- **Mix node.** Address `ShaderNodeMix` sockets by identifier (`A_Color`, `B_Color`, `Factor_Float`, `Result_Color`), because several sockets share a name.
- **Compositor.** The compositor is a node group: `scene.compositing_node_group = bpy.data.node_groups.new(name, 'CompositorNodeTree')`.
  - It must end in a `NodeGroupOutput` with an `Image` interface socket.
  - Math nodes there are `ShaderNodeMath`.
  - `CompositorNodeMaskToSDF` turns a boolean mask into a pixel-distance field, which is useful for drawing outlines of a mask.
- **Volume-grid nodes.** `GeometryNodePointsToSDFGrid`, `SDFGridOffset`, `SDFGridMean` and `GridToMesh` are available. A negative `SDFGridOffset` distance shrinks the surface.
- **View layers.** Objects in a collection excluded from the window's view layer are not evaluated by `scene.frame_set`. Read them through `scene.view_layers[name].depsgraph` after `depsgraph.update()`.
- **Context.** Code run by the MCP add-on runs from a timer, where `bpy.context.window` may be `None`. Fall back to `bpy.context.window_manager.windows[0]`, and prefer the data API to `bpy.ops`.
- **Saving one scene.** `bpy.data.libraries.write(path, {scene}, path_remap='RELATIVE_ALL', fake_user=True)` writes that scene and its dependencies without changing the open file's path or touching other scenes.

## Rendering

- Headless: `blender -b --factory-startup <file.blend> --python tools/render.py -- ...`. `--factory-startup` ignores user preferences and add-ons, so `render.py` selects the Cycles device itself (OptiX, then CUDA, HIP, Metal, oneAPI).
- A plain `blender -b file.blend -a` renders with whatever device the user preferences hold, possibly the CPU.
- Add `--python-exit-code 1` so a Python error fails the process. `pipeline.py` does this.

## ffmpeg

- Recent builds: use `-fps_mode`, not `-vsync`.
- The VP9 WebM container gets new random IDs on every encode, so re-encoded WebMs differ byte-for-byte while their decoded frames are identical. Compare with `ffmpeg -i f.webm -f framemd5 -`.
