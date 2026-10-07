"""The label pass: a separate, cheap EEVEE scene of transparent PNG frames, composited over the picture at
encode time (`tools/encode.py --overlay` / `pipeline.py deliver`). One picture render then gives a labelled
and a clean film, and text can change without re-rendering Cycles.

The spec is a dict (all frames 1-based, positions in pixels from the top-left):

    ink        {'dark': rgb, 'light': rgb}           text colours (sRGB 0-255)
    halo       {'dark': rgb, 'light': rgb}           soft halo behind ink of the same key
    shot_ink   [(frame, 'dark'|'light'), ...]         which ink from which frame: follow the picture's brightness
    header     (start, end, text) or None             e.g. the occasion, top left
    captions   [(start, end, title, subtitle), ...]   one per beat, bottom left
    tags       [(start, end, text), ...]              evidence level of what is on screen, top right
    times      [(start, end, text), ...]              timescale label under the tags
    pointers   [(start, end, anchor, text, (dx, dy) or None), ...]
               anchors are names in `anchors` (a stage point or a (frames, 3) track); (dx, dy) places the
               text relative to the anchor with a leader line and ring; None centres a plain region label
    tags_left_from  frame from which tags and timescale move to the top left (or None)
"""
import math

import bpy
import numpy as np

from ..color import lin
from ..timeline import project
from .scene import reset_scene, save_scene, set_linear

LAYOUT = {
    'margin': 96, 'header': (84, 17), 'title': (118, 42), 'subtitle': (76, 25), 'tag': (84, 17), 'time': (120, 24),
    'pointer': 27, 'region': 26, 'tracking': 1.12, 'ring': (6.0, 2.0), 'leader': 1.8, 'fade': 8, 'halo_blur': 9.0,
    'halo_gain': 1.1, 'time_prefix': 'Timescale  ', 'samples': 16,
}


def label_pass(scene_name, prefix, spec, path, anchors, res, frames, fps, blend_path, layout=None):
    """Build the label scene (orthographic camera in pixel units, x right, -y down) and save it to `blend_path`.
    `path` is the picture's per-frame camera path (timeline.camera_path), used to project pointer anchors."""
    L = {**LAYOUT, **(layout or {})}
    shot_ink = spec['shot_ink']
    scene = reset_scene(scene_name, prefix)
    col = bpy.data.collections.new(prefix + 'Labels')
    scene.collection.children.link(col)
    cam = bpy.data.objects.new(prefix + 'Camera', bpy.data.cameras.new(prefix + 'Camera'))
    cam.data.type, cam.data.ortho_scale = 'ORTHO', res[0]
    cam.location = (res[0] / 2, -res[1] / 2, 50)
    col.objects.link(cam)
    scene.camera = cam
    count = [0]

    def ink_at(frame):
        return [ink for f, ink in shot_ink if f <= frame][-1]

    def ink_material(start, end, fade=L['fade']):
        count[0] += 1
        m = bpy.data.materials.new(f'{prefix}Ink_{count[0]:02d}')
        if m.node_tree is None:
            m.use_nodes = True
        nt = m.node_tree
        out = nt.nodes['Material Output']
        for nd in list(nt.nodes):
            if nd != out:
                nt.nodes.remove(nd)
        em, clear, mix, val = (nt.nodes.new(k) for k in ('ShaderNodeEmission', 'ShaderNodeBsdfTransparent',
                                                          'ShaderNodeMixShader', 'ShaderNodeValue'))
        for f, ink in shot_ink:
            for g_, k_ in ((f - 1, ink_at(max(f - 1, 1))), (f + 4, ink)):
                em.inputs['Color'].default_value = (*lin(spec['ink'][k_]), 1)
                em.inputs['Color'].keyframe_insert('default_value', frame=max(g_, 1))
        nt.links.new(val.outputs[0], mix.inputs[0])
        nt.links.new(clear.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs['Surface'])
        sock = val.outputs[0]
        for f, v in ((start - fade, 0.0), (start, 1.0), (end - fade, 1.0), (end, 0.0)):
            sock.default_value = v
            sock.keyframe_insert('default_value', frame=f)
        m.surface_render_method = 'BLENDED'
        return m

    def text(name, body, x, y, size, mat, align='LEFT', valign='BOTTOM_BASELINE', spacing=1.0, parent=None):
        cu = bpy.data.curves.new(prefix + name, 'FONT')
        cu.body, cu.size, cu.align_x, cu.align_y, cu.space_character = body, size, align, valign, spacing
        cu.materials.append(mat)
        obj = bpy.data.objects.new(prefix + name, cu)
        obj.location = (x, -y, 0)
        obj.parent = parent
        col.objects.link(obj)
        return obj

    def segment(name, a, b, width, mat, parent):
        me = bpy.data.meshes.new(prefix + name)
        d = np.array(b, float) - np.array(a, float)
        nrm = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-9) * width / 2
        quad = [(*(np.array(a) + nrm), 0), (*(np.array(b) + nrm), 0), (*(np.array(b) - nrm), 0), (*(np.array(a) - nrm), 0)]
        me.from_pydata(quad, [], [(0, 1, 2, 3)])
        me.materials.append(mat)
        obj = bpy.data.objects.new(prefix + name, me)
        obj.parent = parent
        col.objects.link(obj)
        return obj

    def ring(name, radius, width, mat, parent):
        me = bpy.data.meshes.new(prefix + name)
        k = 32
        outer = [(radius * math.cos(2 * math.pi * i / k), radius * math.sin(2 * math.pi * i / k), 0) for i in range(k)]
        inner = [((radius - width) * math.cos(2 * math.pi * i / k), (radius - width) * math.sin(2 * math.pi * i / k), 0) for i in range(k)]
        me.from_pydata(outer + inner, [], [(i, (i + 1) % k, k + (i + 1) % k, k + i) for i in range(k)])
        me.materials.append(mat)
        obj = bpy.data.objects.new(prefix + name, me)
        obj.parent = parent
        col.objects.link(obj)
        return obj

    def track(anchor):
        a = np.asarray(anchors[anchor], float)
        return a if a.ndim == 2 else np.repeat(a[None], frames, 0)

    x0, x1 = L['margin'], res[0] - L['margin']
    left_from = spec.get('tags_left_from')
    if spec.get('header'):
        f0, f1, body = spec['header']
        text('Header', body, x0, L['header'][0], L['header'][1], ink_material(f0, f1), spacing=L['tracking'])
    for k, (f0, f1, title, sub) in enumerate(spec.get('captions', [])):
        m = ink_material(f0, f1)
        text(f'Title_{k}', title, x0, res[1] - L['title'][0], L['title'][1], m)
        text(f'Sub_{k}', sub, x0, res[1] - L['subtitle'][0], L['subtitle'][1], m)
    for k, (f0, f1, body) in enumerate(spec.get('tags', [])):
        left = left_from is not None and f0 >= left_from
        text(f'Tag_{k}', body, x0 if left else x1, L['tag'][0], L['tag'][1], ink_material(f0, f1),
             align='LEFT' if left else 'RIGHT', spacing=L['tracking'])
    for k, (f0, f1, body) in enumerate(spec.get('times', [])):
        left = left_from is not None and f0 >= left_from
        text(f'Time_{k}', L['time_prefix'] + body, x0 if left else x1, L['time'][0], L['time'][1], ink_material(f0, f1),
             align='LEFT' if left else 'RIGHT')
    for k, (f0, f1, anchor, body, offset) in enumerate(spec.get('pointers', [])):
        m = ink_material(f0, f1)
        pivot = bpy.data.objects.new(f'{prefix}Pin_{k:02d}', None)
        col.objects.link(pivot)
        tr = track(anchor)
        for f in range(max(1, f0 - 10), min(frames, f1 + 1) + 1):
            _, loc, aim_pt, _, lens = path[f - 1]
            xy, _ = project(tr[f - 1], loc, aim_pt, lens, res)
            pivot.location = (xy[0], -xy[1], 0)
            pivot.keyframe_insert('location', frame=f)
        set_linear(pivot)
        if offset is None:                      # plain region label, centred on its anchor
            text(f'Pin_{k:02d}_Text', body, 0, 0, L['region'], m, align='CENTER', valign='CENTER', spacing=1.05, parent=pivot)
            continue
        dx, dy = offset
        ring(f'Pin_{k:02d}_Dot', *L['ring'], m, pivot)
        u = np.array([dx, -dy], float) / math.hypot(dx, dy)
        segment(f'Pin_{k:02d}_Line', u * 9, np.array([dx, -dy]) - u * 12, L['leader'], m, pivot)
        text(f'Pin_{k:02d}_Text', body, dx + (8 if dx > 0 else -8), dy, L['pointer'], m, align='LEFT' if dx > 0 else 'RIGHT',
             valign='CENTER', parent=pivot)

    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = L['samples']
    scene.render.film_transparent = True
    scene.view_settings.view_transform, scene.view_settings.look = 'Standard', 'None'
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.frame_start, scene.frame_end, scene.render.fps = 1, frames, fps
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    # Compositor: a soft halo (blurred alpha in the contrasting colour) under the ink.
    ng = bpy.data.node_groups.new(prefix + 'Halo', 'CompositorNodeTree')
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl, blur, rgb, setalpha, over, gain, out = (ng.nodes.new(t) for t in (
        'CompositorNodeRLayers', 'CompositorNodeBlur', 'CompositorNodeRGB', 'CompositorNodeSetAlpha',
        'CompositorNodeAlphaOver', 'ShaderNodeMath', 'NodeGroupOutput'))
    rl.scene = scene
    blur.inputs['Size'].default_value = (L['halo_blur'], L['halo_blur'])
    gain.operation, gain.use_clamp = 'MULTIPLY', True
    gain.inputs[1].default_value = L['halo_gain']
    setalpha.inputs['Type'].default_value = 'Replace Alpha'
    for f, ink in shot_ink:
        for g_, k_ in ((f - 1, ink_at(max(f - 1, 1))), (f + 4, ink)):
            rgb.outputs[0].default_value = (*lin(spec['halo'][k_]), 1)
            rgb.outputs[0].keyframe_insert('default_value', frame=max(g_, 1))
    ng.links.new(rl.outputs['Alpha'], blur.inputs['Image'])
    ng.links.new(blur.outputs['Image'], gain.inputs[0])
    ng.links.new(rgb.outputs[0], setalpha.inputs['Image'])
    ng.links.new(gain.outputs[0], setalpha.inputs['Alpha'])
    ng.links.new(setalpha.outputs['Image'], over.inputs['Background'])
    ng.links.new(rl.outputs['Image'], over.inputs['Foreground'])
    ng.links.new(over.outputs['Image'], out.inputs['Image'])
    scene.compositing_node_group = ng
    scene.render.use_compositing = True
    scene.frame_set(1)
    save_scene(scene, blend_path)
    return {'scene': scene.name, 'objects': len(scene.objects), 'blend': str(blend_path)}
