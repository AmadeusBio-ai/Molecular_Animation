"""Flag Blender Python written for an older Blender than the pinned 5.2. Plain Python: no Blender needed.

    python tools/bpy_lint.py [paths ...]          (python pipeline.py lint; pipeline.py build runs it first)

Coding models learned bpy mostly from 2.8-4.x code, so they write names that Blender 5.x removed, confidently, and
a render rarely shows which one broke. Each rule cites the fact in tools/api_probe.py that shows the old API is gone
or deprecated on the pinned Blender, and says what to write instead; docs/blender-5.md has the whole table.

Errors are APIs that 5.2 rejects. Warnings are deprecated or fragile: `use_nodes`, default nodes found by name,
operators where the data API works. Comments and docstrings are not checked. Mark a line that is right anyway with
`# bpy-lint: ignore`, or a whole file with `# bpy-lint: skip-file`. Exits with status 1 when there are errors.
"""
# bpy-lint: skip-file  (the rules below spell out the stale names)
import io
import re
import sys
import tokenize
from collections import namedtuple
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = ('molanim', 'tools', 'templates', 'examples', 'projects')
USES_BPY = re.compile(r'^\s*(?:import|from)\s+(?:bpy|bmesh|bpy_extras|mathutils)\b', re.M)

Rule = namedtuple('Rule', 'name level pattern message fact')
Finding = namedtuple('Finding', 'path line rule level message')

RULES = [Rule(*r) for r in (
    # errors: rejected by Blender 5.2
    ('eevee-next', 'error', r'BLENDER_EEVEE_NEXT',
     "EEVEE's engine id is 'BLENDER_EEVEE' again in 5.x (BLENDER_EEVEE_NEXT existed only in 4.2-4.5)", 'eevee_id'),
    ('scene-node-tree', 'error', r'\b(?:scene|scn|sc)\.node_tree\b|\bscenes\[[^\]]*\]\.node_tree\b',
     "the compositor is a node group (5.0): scene.compositing_node_group = "
     "bpy.data.node_groups.new(name, 'CompositorNodeTree')", 'compositor_node_group'),
    ('action-fcurves', 'error', r'(?:\.action|\b(?:action|act))\.(?:fcurves|groups|id_root)\b',
     "F-curves live in the slot's channelbag (5.0): bpy_extras.anim_utils.action_get_channelbag_for_slot("
     "action, slot).fcurves (molanim.blender.scene.fcurves)", 'action_layered'),
    ('auto-smooth', 'error', r'\b(?:use_auto_smooth|auto_smooth_angle)\b',
     'auto smooth was removed in 4.1: mesh.shade_smooth() then mesh.set_sharp_from_angle(angle=...)', 'mesh_normals'),
    ('calc-normals', 'error', r'\.calc_normals(?:_split)?\s*\(',
     'removed in 4.0-4.1: normals stay up to date; read mesh.corner_normals (and mesh.normals_domain)',
     'mesh_normals'),
    ('modifier-idprop', 'error', r'''\[\s*['"](?:Socket|Input|Output)_\d+(?:_use_attribute|_attribute_name)?['"]\s*\]''',
     'geometry-node modifier inputs are RNA in 5.2: getattr(mod.properties.inputs, identifier).value = x '
     '(molanim.blender.nodes.set_modifier_inputs)', 'gn_modifier_inputs'),
    ('boolean-fast', 'error', r'''solver\s*=\s*['"]FAST['"]''',
     "the Boolean solver 'FAST' is 'FLOAT' since 5.0 (the default is 'EXACT'; 'MANIFOLD' needs manifold input)",
     'boolean_solvers'),
    ('shadow-method', 'error', r'\.shadow_method\b',
     'removed in 4.2: turn off an object\'s shadow with obj.visible_shadow = False', 'render_method'),
    ('bgl', 'error', r'^\s*(?:import\s+bgl\b|from\s+bgl\b)',
     'bgl was removed in 5.0: use the gpu module (call gpu.init() first under --background, 5.2)',
     'bgl_gone_gpu_init'),
    ('vse-sequences', 'error', r'\b(?:sequence_editor|sed?|seq_editor)\.sequences(?:_all)?\b',
     "the sequencer's strips are sequence_editor.strips / strips_all (5.0)", 'vse_strips'),
    ('compositor-node', 'error', r'''['"]CompositorNode(?:Composite|MixRGB|Math|Value|MapRange|SepRGBA|CombRGBA)['"]''',
     "not in the 5.x compositor: end the group in a NodeGroupOutput with an 'Image' socket (no Composite node); "
     'use ShaderNodeMix, ShaderNodeMath, ShaderNodeValue, ShaderNodeMapRange, CompositorNodeSeparateColor / '
     'CombineColor', 'compositor_nodes_moved'),
    ('group-sockets', 'error', r'\b(?:ng|group|node_group|tree|nt|node_tree)\.(?:inputs|outputs)\.new\s*\(',
     "node-group sockets live on the interface (4.0): ng.interface.new_socket(name, in_out='INPUT', "
     "socket_type='NodeSocketFloat')", 'gn_modifier_inputs'),
    ('io-operator', 'error', r'\bbpy\.ops\.(?:export_scene\.obj|import_scene\.obj|export_mesh\.(?:stl|ply)|import_mesh\.(?:stl|ply))\b',
     'the importers and exporters are bpy.ops.wm.obj_export / obj_import / stl_export / stl_import / '
     'ply_export / ply_import', 'io_operators'),
    ('eevee-legacy', 'error', r'\.(?:use_gtao|gtao_distance|use_bloom|bloom_threshold|bloom_intensity|use_ssr'
                              r'|use_ssr_refraction|use_soft_shadows|shadow_cube_size)\b',
     'EEVEE Legacy settings were removed in 4.2: bloom is a compositor Glare (molanim.blender.look.bloom), the AO '
     'distance is view_layer.eevee.ambient_occlusion_distance, reflections come from scene.eevee.use_raytracing',
     'eevee_legacy_gone'),
    ('sky-nishita', 'error', r'''['"]NISHITA['"]''',
     "the sky texture's physical models are 'MULTIPLE_SCATTERING' and 'SINGLE_SCATTERING' in 5.x", 'sky_types'),
    ('shader-node', 'error', r'''['"]ShaderNode(?:TexMusgrave|SeparateRGB|CombineRGB|SeparateHSV|CombineHSV|TexPointDensity)['"]''',
     'removed: Musgrave is ShaderNodeTexNoise with noise_type (4.1); Separate/Combine RGB and HSV are '
     'ShaderNodeSeparateColor / CombineColor with a mode; Point Density is gone', 'shader_nodes_removed'),
    ('principled-name', 'error',
     r'''inputs(?:\[|\.get\()\s*['"](?:Specular|Transmission|Clearcoat(?: Roughness| Normal)?|Sheen|Emission|Subsurface(?: Color)?)['"]''',
     "Principled BSDF inputs were renamed in 4.0: 'Specular IOR Level', 'Transmission Weight', 'Coat Weight' "
     "('Coat Roughness', 'Coat Normal'), 'Sheen Weight', 'Emission Color', 'Subsurface Weight' (the subsurface "
     'colour is the base colour)', 'principled_names'),
    ('context-dict', 'error', r'\bbpy\.ops\.\w+\.\w+\(\s*(?:\{|\w*override\w*\s*[,)]|ctx\s*[,)])',
     'operators no longer take a context dict (4.0): with bpy.context.temp_override(object=ob, ...): '
     "bpy.ops...(), and check that it returns {'FINISHED'}", 'ops_context_dict_gone'),
    ('ffmpeg-format', 'error', r'''file_format\s*=\s*['"]FFMPEG['"]''',
     "set image_settings.media_type = 'VIDEO' before file_format = 'FFMPEG' (5.0); this repo renders PNG frames "
     'and encodes them with tools/encode.py', 'media_type_first'),
    ('props-dict', 'error', r'''\b(?:scene|sc|scn)\[\s*['"](?:cycles|eevee|render|view_settings)['"]\s*\]''',
     'RNA settings are not dict items (5.0): scene.cycles, scene.eevee, scene.render', 'props_no_dict_access'),
    ('armature-layers', 'error', r'\b\w*(?:arm|armature|bone)\w*(?:\.data)?\.layers\b',
     'bone layers became bone collections in 4.0: armature.collections.new(name), bcoll.assign(bone)',
     'bone_collections'),
    # warnings: still accepted by 5.2, but deprecated or fragile
    ('use-nodes', 'warning', r'\.use_nodes\b',
     'deprecated in 5.0, to be removed in 6.0: new materials and worlds already have node trees, and the '
     'compositor is scene.compositing_node_group', 'use_nodes_deprecated'),
    ('node-by-name', 'warning',
     r'''nodes\[\s*['"](?:Principled BSDF|Material Output|World Output|Background|Emission|Principled Volume|'''
     r'''Image Texture|Diffuse BSDF|Render Layers|Composite|Group Input|Group Output)['"]\s*\]''',
     "default node names follow the UI language ('Translate New Data Names' is on by default), so this fails in a "
     "localised Blender: find the node by type, e.g. molanim.blender.nodes.by_type(tree, 'BSDF_PRINCIPLED') "
     "('OUTPUT_MATERIAL', 'OUTPUT_WORLD', 'BACKGROUND')", 'default_names_translate'),
    ('blend-method', 'warning', r'\.blend_method\b',
     "deprecated since 4.2: EEVEE reads material.surface_render_method ('DITHERED' or 'BLENDED')",
     'render_method'),
    ('mix-rgb', 'warning', r'''['"]ShaderNodeMixRGB['"]''',
     "legacy: use ShaderNodeMix with data_type='RGBA' and address its sockets by identifier (A_Color, B_Color, "
     'Factor_Float, Result_Color)', 'mix_node'),
    ('primitive-add', 'warning', r'\bprimitive_\w+_add\s*\(',
     'primitive_cube_add() makes a 2 m cube (size is the full edge) and depends on context: build meshes from '
     'data (bmesh.ops.create_cube / create_uvsphere, mesh.from_pydata)', 'cube_sizes'),
    ('user-file', 'warning', r'\b(?:read_factory_settings|read_homefile|orphans_purge)\b',
     "in a live MCP session the open file holds the user's work: rebuild only your own prefixed scene "
     '(molanim.blender.scene.reset_scene) instead of resetting the file or purging orphans file-wide', None),
    ('operator', 'warning', r'\bbpy\.ops\.(?:mesh|object|curve|transform|uv|node|material|outliner)\.',
     'operators need a context (mode, selection, active object, area) that headless runs and the MCP timer may '
     "lack, and return only {'FINISHED'}: prefer the data API and bmesh (docs/blender-5.md lists replacements)",
     None),
)]
_COMPILED = [(r, re.compile(r.pattern)) for r in RULES]


def _code(text):
    """(lines with comments and bare string statements blanked, lines marked ignore, whether to skip the file).
    Bare string statements are docstrings, which may name old APIs to explain them."""
    lines = text.splitlines()
    ignored, skip = set(), False

    def blank(start, end):
        (r0, c0), (r1, c1) = start, end
        for r in range(r0, r1 + 1):
            a = c0 if r == r0 else 0
            b = c1 if r == r1 else len(lines[r - 1])
            lines[r - 1] = lines[r - 1][:a] + ' ' * (b - a) + lines[r - 1][b:]

    tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    quiet = (tokenize.NL, tokenize.COMMENT)
    prev = tokenize.NEWLINE
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.type == tokenize.COMMENT:
            if re.search(r'bpy-lint:\s*skip-file', t.string):
                skip = True
            elif re.search(r'bpy-lint:\s*ignore', t.string):
                ignored.add(t.start[0])
            blank(t.start, (t.start[0], len(lines[t.start[0] - 1])))
        elif t.type == tokenize.STRING and prev in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT):
            j = i
            while j + 1 < len(tokens) and tokens[j + 1].type in (tokenize.STRING, *quiet):
                j += 1
            after = tokens[j + 1].type if j + 1 < len(tokens) else tokenize.ENDMARKER
            if after in (tokenize.NEWLINE, tokenize.ENDMARKER):
                for s in tokens[i:j + 1]:
                    if s.type == tokenize.STRING:
                        blank(s.start, s.end)
        if t.type not in quiet:
            prev = t.type
        i += 1
    return lines, ignored, skip


def lint_text(text, path='<string>'):
    """Findings for one source text."""
    try:
        lines, ignored, skip = _code(text)
    except (tokenize.TokenError, IndentationError, SyntaxError) as e:
        return [Finding(path, getattr(e, 'lineno', 0) or 0, 'syntax', 'error', f'cannot tokenize: {e}')]
    if skip:
        return []
    code = '\n'.join(lines)
    found = []
    for n, line in enumerate(lines, 1):
        if n in ignored:
            continue
        for rule, rx in _COMPILED:
            if rx.search(line):
                if rule.name == 'ffmpeg-format' and 'media_type' in code:
                    continue
                found.append(Finding(path, n, rule.name, rule.level, rule.message))
    return found


def files(paths=None):
    """Python files to lint: files named explicitly, and in directories (default: the repo's script folders)
    every .py file that imports bpy, bmesh, bpy_extras or mathutils."""
    out = []
    for p in [Path(p) for p in paths] if paths else [ROOT / d for d in SCAN]:
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob('*.py')):
                if '__pycache__' not in f.parts and USES_BPY.search(f.read_text(encoding='utf-8', errors='replace')):
                    out.append(f)
    return out


def lint(paths=None):
    found = []
    for f in files(paths):
        found += lint_text(f.read_text(encoding='utf-8', errors='replace'), f)
    return found


def rel(p):
    try:
        return Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def report(found, checked):
    """Text report: one short line per finding, each rule's explanation once, then a summary line."""
    out = [f'{rel(f.path)}:{f.line}: {f.level} [{f.rule}]' for f in found]
    for name in dict.fromkeys(f.rule for f in found):
        out.append(f'  [{name}] ' + next(f.message for f in found if f.rule == name))
    errors = sum(f.level == 'error' for f in found)
    out.append(f'bpy-lint: {errors} errors, {len(found) - errors} warnings in {checked} files '
               '(pinned Blender 5.2; docs/blender-5.md)')
    return '\n'.join(out)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    found = lint(argv or None)
    print(report(found, len(files(argv or None))))
    return 1 if any(f.level == 'error' for f in found) else 0


if __name__ == '__main__':
    sys.exit(main())
