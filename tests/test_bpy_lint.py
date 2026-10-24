"""tools/bpy_lint.py: every rule fires on the stale form and not on the 5.2 form, the repo is clean, and every
rule cites a fact that tools/api_probe.py checks inside Blender (so nothing is linted on memory alone)."""
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bpy_lint', ROOT / 'tools' / 'bpy_lint.py')
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)

# rule: (what a model trained on older Blender writes, what works in 5.2)
CASES = {
    'eevee-next': ("scene.render.engine = 'BLENDER_EEVEE_NEXT'", "scene.render.engine = 'BLENDER_EEVEE'"),
    'scene-node-tree': ('tree = bpy.context.scene.node_tree', 'tree = bpy.context.scene.compositing_node_group'),
    'action-fcurves': ('for fc in ob.animation_data.action.fcurves:\n    pass', 'for fc in channelbag.fcurves:\n    pass'),
    'auto-smooth': ('me.use_auto_smooth = True', 'me.set_sharp_from_angle(angle=0.5)'),
    'calc-normals': ('me.calc_normals_split()', 'normals = me.corner_normals'),
    'modifier-idprop': ("mod['Socket_2'] = 1.0", "getattr(mod.properties.inputs, 'Socket_2').value = 1.0"),
    'boolean-fast': ("mod.solver = 'FAST'", "mod.solver = 'FLOAT'"),
    'shadow-method': ("mat.shadow_method = 'NONE'", 'ob.visible_shadow = False'),
    'bgl': ('import bgl', 'import gpu'),
    'vse-sequences': ('strips = scene.sequence_editor.sequences_all', 'strips = scene.sequence_editor.strips_all'),
    'compositor-node': ("out = nodes.new('CompositorNodeComposite')", "out = nodes.new('NodeGroupOutput')"),
    'group-sockets': ("ng.inputs.new('NodeSocketFloat', 'Scale')",
                      "ng.interface.new_socket('Scale', in_out='INPUT', socket_type='NodeSocketFloat')"),
    'io-operator': ('bpy.ops.export_scene.obj(filepath=p)', 'bpy.ops.wm.obj_export(filepath=p)'),
    'eevee-legacy': ('scene.eevee.use_bloom = True', 'scene.eevee.use_raytracing = True'),
    'sky-nishita': ("sky.sky_type = 'NISHITA'", "sky.sky_type = 'MULTIPLE_SCATTERING'"),
    'shader-node': ("n = nodes.new('ShaderNodeTexMusgrave')", "n = nodes.new('ShaderNodeTexNoise')"),
    'principled-name': ("p.inputs['Specular'].default_value = 0.5", "p.inputs['Specular IOR Level'].default_value = 0.5"),
    'context-dict': ("bpy.ops.object.delete({'selected_objects': objs})",
                     'with bpy.context.temp_override(selected_objects=objs):\n    bpy.ops.object.delete()'),
    'ffmpeg-format': ("im.file_format = 'FFMPEG'", "im.media_type = 'VIDEO'\nim.file_format = 'FFMPEG'"),
    'props-dict': ("scene['cycles']['samples'] = 64", 'scene.cycles.samples = 64'),
    'armature-layers': ('arm.layers[3] = True', "arm.collections.new('FK')"),
    'use-nodes': ('mat.use_nodes = True', 'nt = mat.node_tree'),
    'node-by-name': ("p = nt.nodes['Principled BSDF']", "p = by_type(nt, 'BSDF_PRINCIPLED')"),
    'blend-method': ("mat.blend_method = 'BLEND'", "mat.surface_render_method = 'BLENDED'"),
    'mix-rgb': ("mix = nodes.new('ShaderNodeMixRGB')", "mix = nodes.new('ShaderNodeMix')"),
    'primitive-add': ('bpy.ops.mesh.primitive_cube_add(size=1)', 'bmesh.ops.create_cube(bm, size=1.0)'),
    'user-file': ('bpy.data.orphans_purge(do_recursive=True)', "scene = reset_scene('Shot', 'SH_')"),
    'operator': ("bpy.ops.object.modifier_apply(modifier='Boolean')",
                 'me = bpy.data.meshes.new_from_object(ob.evaluated_get(depsgraph))'),
}


def rules(text):
    return {f.rule for f in L.lint_text(text)}


def test_every_rule_has_a_case():
    assert set(CASES) == {r.name for r in L.RULES}


@pytest.mark.parametrize('name', sorted(CASES))
def test_rule_fires_on_the_stale_form_only(name):
    stale, current = CASES[name]
    assert name in rules(stale), stale
    assert name not in rules(current), current


def test_comments_and_docstrings_are_not_checked():
    text = ('"""Older scripts set mod[\'Socket_0\'] and BLENDER_EEVEE_NEXT."""\n'
            "def f():\n    '''scene.node_tree is gone.'''\n    return 1  # was scene.node_tree\n")
    assert L.lint_text(text) == []
    assert rules("engine = 'BLENDER_EEVEE_NEXT'  # a string in code is checked") == {'eevee-next'}


def test_pragmas():
    assert L.lint_text("mat.use_nodes = True  # bpy-lint: ignore\n") == []
    assert L.lint_text("# bpy-lint: skip-file\nmat.use_nodes = True\n") == []


def test_rules_cite_facts_the_probe_checks():
    probe = (ROOT / 'tools' / 'api_probe.py').read_text(encoding='utf-8')
    facts = set(re.findall(r"@fact\('(\w+)'\)", probe))
    cited = {r.fact for r in L.RULES if r.fact}
    assert cited <= facts, cited - facts
    assert all(r.fact for r in L.RULES if r.level == 'error'), 'an error must be proved by a probe fact'


def test_directories_lint_only_blender_scripts(tmp_path):
    (tmp_path / 'shot.py').write_text("import bpy\nscene.render.engine = 'BLENDER_EEVEE_NEXT'\n")
    (tmp_path / 'science.py').write_text("import numpy\nNAME = 'BLENDER_EEVEE_NEXT'\n")
    assert [p.name for p in L.files([tmp_path])] == ['shot.py']
    assert [f.rule for f in L.lint([tmp_path])] == ['eevee-next']


def test_the_repo_is_clean():
    found = L.lint()
    assert not found, L.report(found, len(L.files()))
