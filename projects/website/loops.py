"""Seamless loops of the website stills (gallery.py), kept as assets for later use.

Each loop rebuilds a gallery shot exactly as for its still (same structures, colours, cuts and framing, so frame 1
is the approved still) and adds two kinds of motion:

- Camera. The camera, its focus empty and the lights form one rig that turns rigidly about a pivot, so the
  lighting on the molecule never changes as it turns: optically the same as the molecule turning in place. A
  'turn' is one full 360 deg revolution at constant speed, about the vertical (z), the DNA's helix axis or the
  nucleosome disc's axis. A 'drift' is a small ellipse around the still's viewpoint (azimuth +-A, elevation up to
  +2B) for shots whose composition only works from the front: the membrane cut in front of aquaporin, the
  agents constellation, p53 on its DNA, and the antibody's Y (edge-on, mid-turn, it reads as a column).
  Camera-aimed cuts (the GFP funnel, the KcsA section) follow the camera.
- Thermal motion: illustrative noise, not a simulation (gallery.THERMAL, molanim.blender.groups.thermal),
  sampled on a loop, so frame FRAMES + 1 equals frame 1.

Loops render at the size the website shows them (960 x 720 for the 4:3 cards, 1280 x 720 and 1280 x 800 for
the wide ones), 64 samples, adaptive 0.02, denoised.

Headless (from the repo root):
  blender -b --factory-startup --python projects/website/loops.py -- --shot hemoglobin --save
  blender -b projects/website/loops/hemoglobin.blend --python tools/render.py -- --frames 1-289 --out renders/website/loops/hemoglobin/take-01/
  blender -b --factory-startup --python projects/website/loops.py -- --shot hemoglobin --still renders/website/loops/look/hemoglobin-145.png --frame 145
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gallery as G  # noqa: E402  (sets up molanim and the website looks)
from molanim.blender import scene as SC  # noqa: E402

FPS, SAMPLES = 24, 64
LOOP_RES = {(1600, 1200): (960, 720), (1600, 900): (1280, 720), (1600, 1000): (1280, 800)}
DNA_AXIS = tuple(G.rot('y', 32) @ np.array([0.0, 0.0, 1.0]))     # shot_dna tilts the helix axis by 32 deg about y
# shot: (frames, motion). ('turn', axis, pivot) or ('drift', A deg, B deg); pivot None = the camera's aim.
LOOPS = {
    'hemoglobin': (288, ('turn', (0, 0, 1), None)),
    'dna': (288, ('turn', DNA_AXIS, (0, 0, 0))),
    'p53dna': (240, ('drift', 16, 4)),
    'gfp': (288, ('turn', (0, 0, 1), None)),
    'kcsa': (288, ('turn', (0, 0, 1), None)),
    'aquaporin': (240, ('drift', 14, 4)),
    'igg': (240, ('drift', 20, 5)),
    'nucleosome': (288, ('turn', (0, 1, 0), (0, 0, 0))),
    'agents': (240, ('drift', 8, 3)),
}


def rig_rotation(motion, direction, u):
    """Rotation of the camera rig at loop phase u (0..1); identity at u = 0 and u = 1."""
    if motion[0] == 'turn':
        return Quaternion(Vector(motion[1]).normalized(), 2 * math.pi * u)
    _, A, B = motion
    phi = 2 * math.pi * u
    d_az, d_el = math.radians(A) * math.sin(phi), math.radians(B) * (1 - math.cos(phi))
    horiz = Vector((direction[0], direction[1], 0.0)).normalized()
    right = Vector((-horiz.y, horiz.x, 0.0))            # horizontal, perpendicular to the view: tilting about it
    return Quaternion((0, 0, 1), d_az) @ Quaternion(right, -d_el)   # changes elevation without roll


def track_matrix(loc, aim):
    """World matrix of a camera at `loc` looking at `aim` with +Z up and no roll (as TRACK_TO, UP_Y)."""
    f = (Vector(aim) - Vector(loc)).normalized()
    right = f.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(f)
    M = Matrix((right, up, -f)).transposed().to_4x4()
    M.translation = Vector(loc)
    return M


def build(shot):
    frames, motion = LOOPS[shot]
    look_name, res, fn = G.SHOTS[shot]
    loop_res = LOOP_RES[res]
    S = G.Stage(shot, look_name, loop_res, loop=frames)
    report = {'shot': shot, 'look': look_name, **fn(S)}
    scene = S.finish(SAMPLES)
    scene.frame_end, scene.render.fps = frames, FPS

    # One rigid rig: camera (constraint baked out), its focus empty and the suns.
    cam, aim = S.cam, S.aim
    loc, aim_pt = Vector(cam.location), Vector(S.aim_point)
    cam.constraints.clear()
    cam.animation_data_clear()
    aim.animation_data_clear()
    cam.matrix_basis = track_matrix(loc, aim_pt)
    aim.location = aim_pt
    pivot = Vector(motion[2]) if motion[0] == 'turn' and motion[2] is not None else aim_pt
    rig = SC.empty(G.PREFIX + 'LoopRig', S.rigc, tuple(pivot))
    rig.rotation_mode = 'QUATERNION'
    suns = [o for o in S.rigc.objects if o.type == 'LIGHT']
    for obj in [cam, aim] + suns:
        obj.parent = rig
        obj.matrix_parent_inverse = Matrix.Translation(-pivot)
    prev = None
    for f in range(1, frames + 2):
        q = rig_rotation(motion, S.direction, (f - 1) / frames)
        if prev is not None and prev.dot(q) < 0:
            q.negate()
        rig.rotation_quaternion = q
        rig.keyframe_insert('rotation_quaternion', frame=f)
        prev = q
    SC.set_linear(rig)
    scene.frame_set(1)
    report.update({'frames': frames, 'fps': FPS, 'res': list(loop_res), 'motion': list(motion[:2]) if motion[0] == 'drift'
                   else ['turn', [round(float(v), 3) for v in motion[1]]], 'pivot': [round(v, 2) for v in pivot],
                   'samples': SAMPLES})
    return scene, report


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', required=True, choices=sorted(LOOPS))
    ap.add_argument('--save', action='store_true')
    ap.add_argument('--still')
    ap.add_argument('--frame', type=int, default=1)
    ap.add_argument('--percent', type=int, default=100)
    args = ap.parse_args(argv)
    G.W.gpu()
    scene, report = build(args.shot)
    scene.render.resolution_percentage = args.percent
    if args.save:
        path = HERE / 'loops' / f'{args.shot}.blend'
        SC.save_scene(scene, path)
        report['blend'] = str(path)
    if args.still:
        out = Path(args.still).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        scene.frame_set(args.frame)
        scene.render.filepath = str(out)
        with bpy.context.temp_override(scene=scene):
            bpy.ops.render.render(write_still=True, scene=scene.name)
        report['still'] = str(out)
    print('RESULT ' + json.dumps(report))
