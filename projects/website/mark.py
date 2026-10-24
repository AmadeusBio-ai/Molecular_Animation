"""The AmadeusBio mark as a staircase of cubes, revealed by one smooth camera orbit. Seamless loop.

A remake of archive/art/amadeus_silhouette.py for the website hero. The object is the same: every cell of
the mark carries a column of (col - row + 1) bevelled cubes stacked away from the camera, on the mark's
1 : 0.18 square-to-gap lattice, so seen from the front it is exactly the logo. What changes is the motion:
the cubes stay still and centred, and only the camera moves.

Camera: hold on the logo, then one eased orbit (azimuth 0 -> 360 deg, smoothstep, so it starts and stops
gently) around the object's bounding-box centre, with a soft rise in elevation that peaks halfway and
returns to zero, then hold on the logo again. Distance and aim never change, so nothing drifts in frame,
and frame FRAMES + 1 equals frame 1.

Looks: 'deep' (the website's navy hero panel: radial glow #244E84 -> #051634), 'mist' (pale backdrop) or 'paper'
(pure white, the white website's page colour).

Headless (from the repo root):
  blender -b --factory-startup --python projects/website/mark.py -- --look deep --save
  blender -b --factory-startup --python projects/website/mark.py -- --look deep --still renders/website/look/mark.png --frame 120
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
sys.path[:0] = [str(ROOT), str(ROOT / 'archive' / 'art')]
import amadeus as A  # noqa: E402
import molanim  # noqa: E402

molanim.reload()
from molanim.blender import scene as SC  # noqa: E402
from molanim.blender.nodes import by_type  # noqa: E402

sys.path.insert(0, str(HERE))
import website as W  # noqa: E402  (the shared radial backdrop, so the page's CSS glow can match it)

PREFIX, SCENE_NAME = 'WMK_', 'Web_Mark'
FPS, FRAMES = 24, 336                     # 14 s
RES = (960, 960)
HOLD = 0.07                               # share of the loop held on the logo at each end (~1 s each)
ELEVATION = 24.0                          # deg at the middle of the orbit
LENS = 110.0                              # long lens: the front view stays close to the flat logo
FIT = 0.88                                # bounding sphere diameter / frame height
BEVEL, BEVEL_SEGMENTS = 0.06, 4
ROUGHNESS, COAT = 0.42, 0.12
# Albedo gain per tone (linear RGB), from archive/art/amadeus_cubes.py (front faces match the brand tones).
ALBEDO_GAIN = {
    'slate': (1.021, 1.035, 1.029), 'shade': (1.0, 0.599, 0.97), 'steel': (0.93, 1.052, 1.096),
    'mist': (1.215, 1.178, 1.145), 'navy': (1.0, 0.874, 1.162), 'pale': (1.323, 1.294, 1.238),
}
# Every cube has its own tone. The front cube of each column keeps the logo's tone, so the front view is still
# exactly the logo; the four cubes behind them, seen only as the camera turns, take tones from the website's
# renders: three blues and one amber accent on the deepest cube. Keys are (row, col, depth).
BACK_TONES = {(0, 1, 1): '#2F6DB5', (1, 2, 1): '#6FA3E0', (0, 2, 1): '#B8D3F2', (0, 2, 2): '#E9A63C'}
LOOKS = {
    'deep': {'centre': (36, 78, 132), 'edge': (5, 22, 52), 'ambient': ('#5470A0', 0.22),
             'lights': (('Key', (-7, -10, 8), 2100, 7, '#FFF6EA'), ('Fill', (9, -8, -2), 420, 9, '#9DB7E6'),
                        ('Rim', (5, 9, 7), 3600, 4, '#86B0FF'), ('Back', (-6, 8, 4), 1800, 4, '#7FA6F0'))},
    'mist': {'centre': (243, 245, 248), 'edge': (217, 223, 231), 'ambient': ('#E6EBF2', 0.28),
             'lights': (('Key', (-8, -11, 9), 1900, 8, '#FFFFFF'), ('Fill', (11, -9, -1), 650, 10, '#E4ECF7'),
                        ('Rim', (5, 10, 8), 1500, 5, '#FFFFFF'))},
    # The white website (late October 2026): the camera sees the page's own white, so the loop has no frame.
    'paper': {'centre': (255, 255, 255), 'edge': (255, 255, 255), 'ambient': ('#E6EBF2', 0.28),
              'lights': (('Key', (-8, -11, 9), 1900, 8, '#FFFFFF'), ('Fill', (11, -9, -1), 650, 10, '#E4ECF7'),
                         ('Rim', (5, 10, 8), 1500, 5, '#FFFFFF'))},
}


def cubes():
    """[(centre, tone)] with front faces on the plane y = -0.5 (as in amadeus_silhouette.cubes()). The front cube
    (depth 0) carries the logo tone of its cell, the others their BACK_TONES entry."""
    out = []
    for row, col, name in A.MARK:
        x, z = A.cell_centre(row, col)
        for k in range(col - row + 1):
            out.append((Vector((x, k * A.PITCH, z)), name if k == 0 else BACK_TONES[(row, col, k)]))
    return out


def cube_mesh(name):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=A.SQUARE)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=BEVEL, segments=BEVEL_SEGMENTS, profile=0.5, affect='EDGES',
                    clamp_overlap=True)
    for f in bm.faces:
        n = f.normal
        f.smooth = max(abs(n.x), abs(n.y), abs(n.z)) < 0.999   # flat faces stay flat, bevels shade smoothly
    bm.to_mesh(me)
    bm.free()
    return me


def tone_material(tone):
    m = bpy.data.materials.new(PREFIX + tone.lstrip('#').capitalize())
    rgb = np.array(A.linear(tone)) * np.array(ALBEDO_GAIN.get(tone, (1.0, 1.0, 1.0)))
    p = by_type(m.node_tree, 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = ROUGHNESS
    p.inputs['Specular IOR Level'].default_value = 0.25
    p.inputs['Coat Weight'].default_value = COAT
    p.inputs['Coat Roughness'].default_value = 0.12
    return m


def camera_path(centre, distance):
    """Per frame 1..FRAMES+1: (location, azimuth deg, elevation deg). Smooth: C1 at the holds."""
    out = []
    for f in range(1, FRAMES + 2):
        u = ((f - 1) % FRAMES) / FRAMES
        p = min(max((u - HOLD) / (1 - 2 * HOLD), 0.0), 1.0)
        p = p * p * (3 - 2 * p)                          # smoothstep: gentle start and stop
        az = 360.0 * p
        el = ELEVATION * math.sin(math.pi * p) ** 2
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        out.append((centre + d * distance, az, el))
    return out


def build(look):
    L = LOOKS[look]
    scene = SC.reset_scene(SCENE_NAME, PREFIX)
    col = SC.collection(scene, PREFIX + 'Mark')
    me = cube_mesh(PREFIX + 'Cube')
    me.materials.append(None)                    # one slot, linked per object: each column keeps its tone
    items = cubes()
    mats = {t: tone_material(t) for t in dict.fromkeys(tone for _, tone in items)}
    for k, (c, tone) in enumerate(items):
        obj = bpy.data.objects.new(f'{PREFIX}Cube_{k}', me)
        obj.location = c
        col.objects.link(obj)
        obj.material_slots[0].link = 'OBJECT'
        obj.material_slots[0].material = mats[tone]

    pts = np.array([[*(c + Vector((sx, sy, sz)) * 0.5)] for c, _ in items for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    lo, hi = pts.min(0), pts.max(0)
    centre = Vector(((lo + hi) / 2).tolist())
    radius = float(np.linalg.norm(pts - np.array(centre), axis=1).max())
    half = math.atan(0.5 * 36.0 / LENS)
    distance = radius / FIT / math.tan(half)

    cam = bpy.data.objects.new(PREFIX + 'Camera', bpy.data.cameras.new(PREFIX + 'Camera'))
    cam.data.lens, cam.data.clip_start, cam.data.clip_end = LENS, 0.5, 400
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = distance
    cam.data.dof.aperture_fstop = 11.0
    col.objects.link(cam)
    scene.camera = cam
    aim = SC.empty(PREFIX + 'Aim', col, centre)
    track = cam.constraints.new('TRACK_TO')
    track.target, track.track_axis, track.up_axis = aim, 'TRACK_NEGATIVE_Z', 'UP_Y'
    path = camera_path(centre, distance)
    for f, (loc, _, _) in enumerate(path, 1):
        cam.location = loc
        cam.keyframe_insert('location', frame=f)
    SC.set_linear(cam)

    # Lights ride with the camera (parented to an empty that follows its azimuth), so the shading of the
    # faces stays consistent as it orbits: the turn reads as a turn, not as the light sweeping around.
    rig = SC.empty(PREFIX + 'LightRig', col, centre)
    for f, (_, az, _) in enumerate(path, 1):
        rig.rotation_euler = (0, 0, math.radians(az))
        rig.keyframe_insert('rotation_euler', index=2, frame=f)
    SC.set_linear(rig)
    for name, loc, energy, size, colour in L['lights']:
        light = bpy.data.objects.new(PREFIX + name, bpy.data.lights.new(PREFIX + name, 'AREA'))
        light.data.energy, light.data.shape, light.data.size = energy, 'DISK', size
        light.data.color = A.linear(colour)
        light.location = Vector(loc) + centre
        SC.look_at(light, centre)
        light.parent = rig
        light.matrix_parent_inverse = rig.matrix_world.inverted()
        col.objects.link(light)
    amb, strength = L['ambient']
    scene.world = W.radial_world(PREFIX + 'World', L['centre'], L['edge'], A.hex_rgb(amb) and
                                 tuple(round(255 * c) for c in A.hex_rgb(amb)), strength, RES, focus=(0.5, 0.5), reach=0.78)
    SC.cycles_settings(scene, RES, FRAMES, FPS, samples=64, adaptive=0.02, bounces=(4, 2, 2))
    scene.frame_set(1)
    return scene, {'look': look, 'frames': FRAMES, 'fps': FPS, 'cubes': len(items), 'radius': round(radius, 3),
                   'distance': round(distance, 3), 'centre': [round(v, 3) for v in centre],
                   'seam': [round(v, 6) for v in (path[0][0] - path[FRAMES][0])]}


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--look', default='deep', choices=sorted(LOOKS))
    ap.add_argument('--still')
    ap.add_argument('--frame', type=int, default=1)
    ap.add_argument('--save', action='store_true')
    ap.add_argument('--percent', type=int, default=100)
    args = ap.parse_args(argv)
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    scene, report = build(args.look)
    scene.render.resolution_percentage = args.percent
    if args.save:
        SC.save_scene(scene, HERE / f'mark-{args.look}.blend')
        report['blend'] = str(HERE / f'mark-{args.look}.blend')
    if args.still:
        out = Path(args.still).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        scene.frame_set(args.frame)
        scene.render.filepath = str(out)
        with bpy.context.temp_override(scene=scene):
            bpy.ops.render.render(write_still=True, scene=scene.name)
        report['still'] = str(out)
    print('RESULT ' + json.dumps(report))
