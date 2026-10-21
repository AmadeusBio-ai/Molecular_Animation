"""The AmadeusBio mark drawn in outline on white, revealed by one smooth camera orbit. Seamless loop.

A remake of the clean variant of archive/art/amadeus_silhouette.py (delivery/amadeus/silhouette-clean.mp4) for
the website's Approach page, with the camera of mark.py. The drawing is unchanged: the staircase of cubes in
flat brand fills on white paper; the fills drain toward each square's centre while a navy outline takes over,
and return at the end. What changes is the motion. The original tumbled the object about a tilted axis while
it nodded, and re-centred it frame by frame on its silhouette's bounding box, so the outline wobbled in frame.
Here the cubes never turn. An orthographic camera holds on the logo, makes one smoothstep-eased 360 deg orbit
about the object's bounding-box centre with a soft rise in elevation (24 deg at the middle, as mark.py), and
holds on the logo again. Aim and scale never change. As in the original, the cubes spread apart a little
mid-orbit (following the same eased progress), so the outline shows separate cubes instead of one blob.
Frame LOOP + 1 equals frame 1.

Headless (from the repo root):
  blender -b --factory-startup --python projects/website/outline.py -- --save
  blender -b projects/website/outline.blend --python tools/render.py -- --frames 1-361 --out renders/website/outline/take-01/
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / 'archive' / 'art')]
import amadeus as A  # noqa: E402

PREFIX, SCENE_NAME = 'WOL_', 'Web_Outline'
RES, FPS, LOOP = (1080, 1080), 30, 360     # 12 s, as the original
TURN_FRAMES = (44, 322)                     # the original's turn window, so its fill and ink keys still fit
ELEVATION = 24.0                            # deg at the middle of the orbit (mark.py)
SPREAD, SHRINK = 0.18, 0.30                 # at full spread: centres x (1 + SPREAD), cube size x (1 - SHRINK)
EXPLODE_RAMP = 0.22                         # share of the orbit over which the spread grows (and shrinks)
# Fill inset (px) and outline opacity per frame, from the original.
INSET_KEYS = ((1, 0.0), (40, 0.0), (64, 90.0), (302, 90.0), (326, 0.0), (361, 0.0))
INK_KEYS = ((1, 0.0), (38, 0.0), (46, 1.0), (322, 1.0), (332, 0.0), (361, 0.0))
FRAME_FILL = 0.88                           # the orbit's widest screen reach fills this much of the frame
DISTANCE = 50.0                             # orthographic: only keeps the camera clear of the object
LINE_PX = 2.0
INK = '#002655'
PAPER = '#FFFFFF'


def cubes():
    """[(centre, colour name)], front faces on the plane y = -0.5 (as amadeus_silhouette.cubes())."""
    out = []
    for row, col, name in A.MARK:
        x, z = A.cell_centre(row, col)
        for k in range(col - row + 1):
            out.append((Vector((x, k * A.PITCH, z)), name))
    return out


def progress(frame):
    """Orbit progress 0..1 at `frame`: held at 0 before the turn window and at 1 after it, smoothstep inside."""
    f0, f1 = TURN_FRAMES
    return A.smoothstep((frame - f0) / (f1 - f0))


def explode(frame):
    p = progress(frame)
    return A.smoothstep(p / EXPLODE_RAMP) * A.smoothstep((1 - p) / EXPLODE_RAMP)


def view(frame):
    """Unit vector from the aim point to the camera, and the azimuth and elevation in degrees."""
    p = progress(frame)
    az, el = 360.0 * p, ELEVATION * math.sin(math.pi * p) ** 2
    a, e = math.radians(az), math.radians(el)
    return np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)]), az, el


def screen_reach(items, centre):
    """Largest |x| and |y| on screen (stage units from the aim point) of any cube corner over the loop."""
    corners = np.array([(sx, sy, sz) for sx in (-0.5, 0.5) for sy in (-0.5, 0.5) for sz in (-0.5, 0.5)])
    rel = np.array([np.array(c - centre) for c, _ in items])
    reach = np.zeros(2)
    for f in range(1, LOOP + 1):
        d, _, _ = view(f)
        right = np.cross(-d, (0, 0, 1))
        right /= np.linalg.norm(right)
        up = np.cross(right, -d)
        e = explode(f)
        pts = (rel[:, None] * (1 + SPREAD * e) + corners[None] * (1 - SHRINK * e)).reshape(-1, 3)
        reach = np.maximum(reach, [np.abs(pts @ right).max(), np.abs(pts @ up).max()])
    return reach


def cube_mesh(name):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=A.SQUARE)
    bm.to_mesh(me)
    bm.free()
    return me


def compositor(scene):
    """Paper, brand fills and the outline band of the mask SDF (amadeus_silhouette.compositor without the
    triangle layer)."""
    ng = bpy.data.node_groups.new(PREFIX + 'Ink', 'CompositorNodeTree')
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    N, L = ng.nodes, ng.links
    op = A.math_builder(ng)
    keyed = {}
    for name in ('Inset', 'Ink'):
        n = N.new('ShaderNodeValue')
        n.name = n.label = name
        keyed[name] = n
    shape = N.new('CompositorNodeRLayers')
    shape.scene, shape.layer = scene, 'Shape'
    sep = N.new('CompositorNodeSeparateColor')
    L.new(shape.outputs['Image'], sep.inputs[0])
    # Outline: band |d| < LINE_PX / 2 around the mask boundary, one-pixel ramp.
    inside = op('GREATER_THAN', shape.outputs['Alpha'], 0.5)
    sdf = N.new('CompositorNodeMaskToSDF')
    L.new(inside, sdf.inputs['Mask'])
    line = op('SUBTRACT', LINE_PX / 2 + 0.5, op('ABSOLUTE', sdf.outputs['SDF']))
    line = op('MULTIPLY', op('MINIMUM', op('MAXIMUM', line, 0.0), 1.0), keyed['Ink'].outputs[0])
    # Fill: brand colour wherever the pixel lies deeper than `Inset` px inside the silhouette.
    deep = op('MINIMUM', op('MAXIMUM', op('SUBTRACT', op('MULTIPLY', sdf.outputs['SDF'], -1.0),
                                          op('SUBTRACT', keyed['Inset'].outputs[0], 0.5)), 0.0), 1.0)
    # Fully drained means no fill at all: merged silhouettes are deeper than any square.
    drained = op('GREATER_THAN', keyed['Inset'].outputs[0], INSET_KEYS[2][1] - 0.5)
    deep = op('MULTIPLY', deep, op('SUBTRACT', 1.0, drained))
    alpha = shape.outputs['Alpha']
    fill_a = op('MULTIPLY', alpha, op('MAXIMUM', deep, op('LESS_THAN', keyed['Inset'].outputs[0], 0.01)))
    paper, ink = A.linear(PAPER), A.linear(INK)
    out = N.new('CompositorNodeCombineColor')
    for k in range(3):
        colour = op('DIVIDE', sep.outputs[k], op('MAXIMUM', alpha, 1e-4))      # un-premultiply
        base = op('ADD', op('MULTIPLY', paper[k], op('SUBTRACT', 1.0, fill_a)), op('MULTIPLY', colour, fill_a))
        L.new(op('ADD', op('MULTIPLY', base, op('SUBTRACT', 1.0, line)), op('MULTIPLY', ink[k], line)), out.inputs[k])
    out.inputs[3].default_value = 1.0
    gout = N.new('NodeGroupOutput')
    L.new(out.outputs[0], gout.inputs[0])
    scene.compositing_node_group = ng
    A.key_value_node(keyed['Inset'], INSET_KEYS)
    A.key_value_node(keyed['Ink'], INK_KEYS)
    for fc in A.fcurves(ng):
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'


def build():
    scene = A.reset_scene(SCENE_NAME, PREFIX)
    shape_col = bpy.data.collections.new(PREFIX + 'Shape')
    rig_col = bpy.data.collections.new(PREFIX + 'Rig')
    for col in (shape_col, rig_col):
        scene.collection.children.link(col)

    items = cubes()
    pts = np.array([[*(c + Vector((sx, sy, sz)) * 0.5)] for c, _ in items for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    centre = Vector(((pts.min(0) + pts.max(0)) / 2).tolist())

    me = cube_mesh(PREFIX + 'Cube')
    for k, (c, name) in enumerate(items):
        obj = bpy.data.objects.new(f'{PREFIX}Cube_{k:02d}', me)
        obj.color = (*A.linear(name), 1.0)
        shape_col.objects.link(obj)
        for f in range(1, LOOP + 2):          # spread: one key per frame, linear in between
            e = explode(f)
            obj.location = centre + (c - centre) * (1 + SPREAD * e)
            obj.scale = (1 - SHRINK * e,) * 3
            obj.keyframe_insert('location', frame=f)
            obj.keyframe_insert('scale', frame=f)
        A.set_interpolation(obj, 'LINEAR')

    reach = screen_reach(items, centre)
    ortho = 2 * reach.max() / FRAME_FILL
    cam = bpy.data.objects.new(PREFIX + 'Camera', bpy.data.cameras.new(PREFIX + 'Camera'))
    cam.data.type, cam.data.ortho_scale = 'ORTHO', ortho
    cam.data.clip_start, cam.data.clip_end = 1, 200
    rig_col.objects.link(cam)
    scene.camera = cam
    aim = bpy.data.objects.new(PREFIX + 'Aim', None)
    aim.location = centre
    rig_col.objects.link(aim)
    track = cam.constraints.new('TRACK_TO')
    track.target, track.track_axis, track.up_axis = aim, 'TRACK_NEGATIVE_Z', 'UP_Y'
    for f in range(1, LOOP + 2):
        d, _, _ = view(f)
        cam.location = centre + Vector(d.tolist()) * DISTANCE
        cam.keyframe_insert('location', frame=f)
    A.set_interpolation(cam, 'LINEAR')

    scene.render.engine = 'BLENDER_WORKBENCH'
    shading = scene.display.shading
    shading.light, shading.color_type = 'FLAT', 'OBJECT'
    shading.show_object_outline = shading.show_cavity = shading.show_shadows = False
    scene.display.render_aa = '32'
    scene.render.film_transparent = True
    scene.view_settings.view_transform, scene.view_settings.look = 'Standard', 'None'
    world = bpy.data.worlds.new(PREFIX + 'World')
    world.color = (1, 1, 1)
    scene.world = world
    layer = scene.view_layers[0]
    layer.name = 'Shape'
    compositor(scene)

    scene.frame_start, scene.frame_end, scene.render.fps = 1, LOOP, FPS
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.frame_set(1)
    d0, d1 = view(1)[0], view(LOOP + 1)[0]
    return scene, {'blender': bpy.app.version_string, 'cubes': len(items), 'frames': [1, LOOP, FPS],
                   'centre': [round(v, 3) for v in centre], 'ortho_scale': round(float(ortho), 3),
                   'reach': [round(float(v), 3) for v in reach],
                   'logo_px': round(float((3 * A.PITCH - A.GAP) / ortho * RES[1]), 1),
                   'seam': float(np.abs(d0 - d1).max())}


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--save', action='store_true')
    ap.add_argument('--still')
    ap.add_argument('--frame', type=int, default=1)
    args = ap.parse_args(argv)
    scene, report = build()
    if args.save:
        A.save_scene(scene, HERE / 'outline.blend')
        report['blend'] = str(HERE / 'outline.blend')
    if args.still:
        out = Path(args.still).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        scene.frame_set(args.frame)
        scene.render.filepath = str(out)
        with bpy.context.temp_override(scene=scene):
            bpy.ops.render.render(write_still=True, scene=scene.name)
        report['still'] = str(out)
    print('RESULT ' + json.dumps(report))
