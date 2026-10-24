"""Check, inside Blender, the API facts that docs/blender-5.md states and tools/bpy_lint.py enforces.

    blender -b --factory-startup --python tools/api_probe.py          (python pipeline.py doctor runs it)

Prints one line, API_PROBE {"blender": ..., "python": ..., "facts": {name: true | "what failed"}}.

Coding models learned bpy mostly from 2.8-4.x code and write stale names with confidence; a render rarely shows
which one broke. Each fact is a claim about the pinned Blender (5.2) that such code gets wrong. After a Blender
upgrade, a failing fact names the row of docs/blender-5.md and the lint rule to revise, together.
"""
# bpy-lint: skip-file  (this file uses the stale names on purpose, to prove they are gone)
import json
import sys
import warnings

import bmesh
import bpy
from bpy_extras import anim_utils

FACTS = {}


def fact(name):
    def register(fn):
        FACTS[name] = fn
        return fn
    return register


def has(owner, name):
    """hasattr, but for a bpy type also its RNA properties and functions (hasattr on the class misses many)."""
    rna = getattr(owner, 'bl_rna', None) if isinstance(owner, type) else None
    return hasattr(owner, name) or (rna is not None and (name in rna.properties or name in rna.functions))


def absent(owner, *names):
    there = [n for n in names if has(owner, n)]
    assert not there, f'still present: {there}'


def present(owner, *names):
    missing = [n for n in names if not has(owner, n)]
    assert not missing, f'missing: {missing}'


def rejects(owner, prop, value):
    """Assigning `value` raises TypeError (an enum identifier that no longer exists)."""
    try:
        setattr(owner, prop, value)
    except TypeError:
        return
    raise AssertionError(f'{prop} = {value!r} was accepted')


def warns_removal(fn):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        fn()
    assert any('removed' in str(w.message) for w in caught), 'no deprecation warning'


def scene():
    return bpy.context.scene


@fact('python_313')
def _():
    assert sys.version_info[:2] == (3, 13), sys.version


@fact('eevee_id')
def _():
    r = scene().render
    rejects(r, 'engine', 'BLENDER_EEVEE_NEXT')
    for engine in ('BLENDER_EEVEE', 'CYCLES', 'BLENDER_WORKBENCH'):
        r.engine = engine


@fact('enum_error_lists_values')
def _():
    try:
        scene().render.engine = '__probe__'
    except TypeError as e:
        assert 'CYCLES' in str(e) and 'BLENDER_EEVEE' in str(e), str(e)
        return
    raise AssertionError('invalid engine accepted')


@fact('action_layered')
def _():
    absent(bpy.types.Action, 'fcurves', 'groups', 'id_root')
    present(anim_utils, 'action_get_channelbag_for_slot', 'action_ensure_channelbag_for_slot')
    ob = bpy.data.objects.new('Probe_Anim', None)
    scene().collection.objects.link(ob)
    ob.keyframe_insert('location', frame=1)
    ad = ob.animation_data
    assert len(anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves) == 3


@fact('compositor_node_group')
def _():
    absent(bpy.types.Scene, 'node_tree')
    present(bpy.types.Scene, 'compositing_node_group')


@fact('compositor_nodes_moved')
def _():
    absent(bpy.types, 'CompositorNodeComposite', 'CompositorNodeMixRGB', 'CompositorNodeMath', 'CompositorNodeValue',
           'CompositorNodeMapRange', 'CompositorNodeSepRGBA', 'CompositorNodeCombRGBA')
    ng = bpy.data.node_groups.new('Probe_Comp', 'CompositorNodeTree')
    for kind in ('ShaderNodeMath', 'ShaderNodeValue', 'ShaderNodeMapRange', 'ShaderNodeMix', 'NodeGroupOutput',
                 'CompositorNodeRLayers', 'CompositorNodeSeparateColor', 'CompositorNodeCombineColor'):
        ng.nodes.new(kind)


@fact('glare_options_are_inputs')
def _():
    ng = bpy.data.node_groups.new('Probe_Glare', 'CompositorNodeTree')
    glare = ng.nodes.new('CompositorNodeGlare')
    names = {s.name for s in glare.inputs}
    assert {'Type', 'Quality', 'Threshold', 'Strength', 'Size'} <= names, sorted(names)
    absent(glare, 'glare_type', 'threshold')


@fact('use_nodes_deprecated')
def _():
    m, w = bpy.data.materials.new('Probe_Mat'), bpy.data.worlds.new('Probe_World')
    assert {n.type for n in m.node_tree.nodes} == {'BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'}
    assert {n.type for n in w.node_tree.nodes} == {'BACKGROUND', 'OUTPUT_WORLD'}
    for owner in (m, w, scene()):
        warns_removal(lambda: setattr(owner, 'use_nodes', True))


@fact('default_names_translate')
def _():
    assert bpy.context.preferences.view.use_translate_new_dataname, 'new data names are not translated'


@fact('principled_names')
def _():
    m = bpy.data.materials.new('Probe_Principled')
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    names = {s.name for s in p.inputs}
    new = {'Specular IOR Level', 'Transmission Weight', 'Coat Weight', 'Sheen Weight', 'Emission Color',
           'Subsurface Weight', 'Emission Strength'}
    old = {'Specular', 'Transmission', 'Clearcoat', 'Clearcoat Roughness', 'Clearcoat Normal', 'Sheen', 'Emission',
           'Subsurface', 'Subsurface Color'}
    assert new <= names and not old & names, (sorted(new - names), sorted(old & names))


@fact('mix_node')
def _():
    present(bpy.types, 'ShaderNodeMixRGB')          # legacy, still there
    m = bpy.data.materials.new('Probe_Mix')
    mix = m.node_tree.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    ids = {s.identifier for s in mix.inputs} | {s.identifier for s in mix.outputs}
    assert {'A_Color', 'B_Color', 'Factor_Float', 'Result_Color'} <= ids, sorted(ids)
    assert len({s.name for s in mix.inputs}) < len(mix.inputs), 'socket names are unique now: identifiers optional'


@fact('render_method')
def _():
    absent(bpy.types.Material, 'shadow_method')
    m = bpy.data.materials.new('Probe_Blend')
    for v in ('DITHERED', 'BLENDED'):
        m.surface_render_method = v
    assert 'Deprecated' in bpy.types.Material.bl_rna.properties['blend_method'].description


@fact('gn_modifier_inputs')
def _():
    ng = bpy.data.node_groups.new('Probe_GN', 'GeometryNodeTree')
    absent(ng, 'inputs', 'outputs')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    sock = ng.interface.new_socket('Scale', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ob = bpy.data.objects.new('Probe_GN', bpy.data.meshes.new('Probe_GN'))
    mod = ob.modifiers.new('Nodes', 'NODES')
    mod.node_group = ng
    try:
        mod[sock.identifier] = 2.0
        raise AssertionError('mod[identifier] = value was accepted')
    except TypeError:
        pass
    getattr(mod.properties.inputs, sock.identifier).value = 3.0
    assert getattr(mod.properties.inputs, sock.identifier).value == 3.0


@fact('node_warnings')
def _():
    item = bpy.types.NodesModifier.bl_rna.properties['node_warnings'].fixed_type
    assert {'type', 'message'} <= set(item.bl_rna.properties.keys())


@fact('shader_nodes_removed')
def _():
    absent(bpy.types, 'ShaderNodeTexMusgrave', 'ShaderNodeSeparateRGB', 'ShaderNodeCombineRGB',
           'ShaderNodeSeparateHSV', 'ShaderNodeCombineHSV', 'ShaderNodeTexPointDensity')
    present(bpy.types, 'ShaderNodeSeparateColor', 'ShaderNodeCombineColor', 'ShaderNodeMix', 'ShaderNodeTexNoise')
    assert 'FBM' in [i.identifier for i in bpy.types.ShaderNodeTexNoise.bl_rna.properties['noise_type'].enum_items]


@fact('sky_types')
def _():
    w = bpy.data.worlds.new('Probe_Sky')
    sky = w.node_tree.nodes.new('ShaderNodeTexSky')
    rejects(sky, 'sky_type', 'NISHITA')
    for v in ('MULTIPLE_SCATTERING', 'SINGLE_SCATTERING'):
        sky.sky_type = v


@fact('mesh_normals')
def _():
    absent(bpy.types.Mesh, 'use_auto_smooth', 'auto_smooth_angle', 'calc_normals', 'calc_normals_split', 'face_maps')
    present(bpy.types.Mesh, 'set_sharp_from_angle', 'shade_smooth', 'corner_normals', 'normals_domain')


@fact('boolean_solvers')
def _():
    ob = bpy.data.objects.new('Probe_Bool', bpy.data.meshes.new('Probe_Bool'))
    mod = ob.modifiers.new('Boolean', 'BOOLEAN')
    assert mod.solver == 'EXACT', mod.solver
    items = [i.identifier for i in mod.bl_rna.properties['solver'].enum_items]
    assert set(items) == {'FLOAT', 'EXACT', 'MANIFOLD'}, items
    rejects(mod, 'solver', 'FAST')


@fact('cube_sizes')
def _():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    xs = [v.co.x for v in bm.verts]
    bm.free()
    assert abs(max(xs) - min(xs) - 1.0) < 1e-6
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    dims = tuple(ob.dimensions)
    bpy.data.objects.remove(ob)
    assert dims == (2.0, 2.0, 2.0), dims


@fact('media_type_first')
def _():
    im = scene().render.image_settings
    im.media_type = 'IMAGE'
    rejects(im, 'file_format', 'FFMPEG')
    im.media_type = 'VIDEO'
    im.file_format = 'FFMPEG'
    im.media_type = 'IMAGE'
    im.file_format = 'PNG'


@fact('eevee_legacy_gone')
def _():
    absent(scene().eevee, 'use_gtao', 'gtao_distance', 'use_bloom', 'bloom_threshold', 'bloom_intensity', 'use_ssr',
           'use_ssr_refraction', 'use_soft_shadows', 'shadow_cube_size')
    present(scene().eevee, 'use_raytracing', 'taa_render_samples')
    present(bpy.context.view_layer.eevee, 'ambient_occlusion_distance')


@fact('view_transforms')
def _():
    vs = scene().view_settings
    for v in ('Standard', 'AgX', 'Khronos PBR Neutral', 'Filmic', 'ACES 2.0'):
        vs.view_transform = v
    vs.view_transform = 'Standard'


@fact('bgl_gone_gpu_init')
def _():
    try:
        __import__('bgl')
        raise AssertionError('bgl imports')
    except ImportError:
        pass
    import gpu
    present(gpu, 'init')


@fact('vse_strips')
def _():
    present(bpy.types.SequenceEditor, 'strips', 'strips_all')
    absent(bpy.types.SequenceEditor, 'sequences', 'sequences_all')
    present(bpy.context, 'sequencer_scene')


@fact('ops_context_dict_gone')
def _():
    try:
        bpy.ops.object.select_all({'area': None}, action='DESELECT')
        raise AssertionError('a context dict was accepted')
    except (TypeError, ValueError):
        pass
    present(bpy.context, 'temp_override')


@fact('io_operators')
def _():
    for op in ('obj_export', 'obj_import', 'stl_export', 'stl_import', 'ply_export', 'ply_import'):
        assert op in dir(bpy.ops.wm), op
    assert 'obj' not in dir(bpy.ops.export_scene) and 'obj' not in dir(bpy.ops.import_scene)
    assert not {'stl', 'ply'} & (set(dir(bpy.ops.export_mesh)) | set(dir(bpy.ops.import_mesh)))


@fact('props_no_dict_access')
def _():
    try:
        scene()['cycles']
        raise AssertionError("scene['cycles'] worked")
    except KeyError:
        pass


@fact('bone_collections')
def _():
    absent(bpy.types.Armature, 'layers')
    absent(bpy.types.Bone, 'layers')
    present(bpy.types.Armature, 'collections')


@fact('removed_reference')
def _():
    ob = bpy.data.objects.new('Probe_Freed', None)
    bpy.data.objects.remove(ob)
    try:
        ob.name
        raise AssertionError('a removed object is still readable')
    except ReferenceError:
        pass


@fact('evaluated_mesh')
def _():
    me = bpy.data.meshes.new('Probe_Eval')
    me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    ob = bpy.data.objects.new('Probe_Eval', me)
    scene().collection.objects.link(ob)
    ob.modifiers.new('Subdivision', 'SUBSURF').levels = 2
    eo = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    n = len(eo.to_mesh().polygons)
    eo.to_mesh_clear()
    assert len(me.polygons) == 1 and n > 1, n


def run():
    facts = {}
    for name, check in FACTS.items():
        try:
            check()
            facts[name] = True
        except Exception as e:
            facts[name] = f'{type(e).__name__}: {e}'[:300]
    return {'blender': bpy.app.version_string, 'python': sys.version.split()[0], 'facts': facts}


if __name__ == '__main__':
    print('API_PROBE ' + json.dumps(run()))
