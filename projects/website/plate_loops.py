"""Seamless loops of the website plates (plates.py): the approved plate, seen by a camera that moves.

Each loop rebuilds a plate exactly as for its still (same structures, layers, colours, cuts and framing), at the
size the website shows it, and moves only the camera. The camera, its focus empty and the three suns form one rig
that turns rigidly about a pivot (loops.rig_rotation), so the lighting on the molecule never changes: optically
the same as the molecule turning in place. Nothing in the molecule moves, so the loop claims no dynamics.

- 'turn': one full revolution at constant speed, for plates that read from every side: hemoglobin about the
  vertical, the DNA about its helix axis.
- 'drift': a small ellipse around the plate's viewpoint (azimuth +-A, elevation up to +2B), for plates whose
  cut or composition is made for one view: the GFP cutaway and the aquaporin membrane are cut in front, KcsA
  shows two opposite subunits, p53 sits on its DNA, the antibody's Y and the agents constellation face the camera,
  and the nucleosome is seen nearly face-on (a turn about its disc axis would read as a flat spin).

A loop whose molecule would reach the frame edge somewhere in its motion is framed a little wider (ZOOM: the
camera's distance from its aim, scaled; frame 1 is then the plate seen from further away).

Frame N + 1 equals frame 1 by construction, so a loop is frames 1..N. Renders use 64 samples, adaptive 0.02,
denoised (as loops.py).

Headless (from the repo root):
  blender -b --factory-startup --python projects/website/plate_loops.py -- --shot dna --save
  blender -b projects/website/loops/plate-dna.blend --python tools/render.py -- --frames 1-288 --out renders/website/plate-loops/dna/take-01/
  blender -b --factory-startup --python projects/website/plate_loops.py -- --shot dna --stills 0,0.25,0.5,0.75 --out DIR --percent 50
"""
import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import loops as L  # noqa: E402  (rig_rotation, track_matrix, DNA_AXIS; imports gallery)
import plates as PL  # noqa: E402
from molanim.blender import scene as SC  # noqa: E402

FPS, SAMPLES = 24, 64
# shot: (frames, motion, loop size). ('turn', axis, pivot) or ('drift', A deg, B deg); pivot None = the camera's aim.
LOOPS = {
    'hemoglobin': (288, ('turn', (0, 0, 1), None), (960, 720)),
    'dna': (288, ('turn', L.DNA_AXIS, (0, 0, 0)), (960, 720)),     # plates.shot_dna tilts the helix as gallery does
    'p53dna': (240, ('drift', 12, 3), (960, 720)),
    'gfp': (240, ('drift', 8, 2), (960, 720)),
    'kcsa': (240, ('drift', 12, 3), (960, 720)),
    'aquaporin': (240, ('drift', 12, 3), (960, 720)),
    'igg': (240, ('drift', 14, 4), (1280, 720)),
    'nucleosome': (240, ('drift', 12, 3), (1600, 900)),   # face-on: a turn about the disc axis reads as a flat spin
    'agents': (240, ('drift', 8, 3), (1280, 800)),
}


# Camera distance factors: hemoglobin's turn swings its envelope through the bottom edge at the plate's distance
# (frames 241-260 of take-01).
ZOOM = {'hemoglobin': 1.08}


def build(shot):
    frames, motion, size = LOOPS[shot]
    res, fn = PL.SHOTS[shot]
    assert abs(size[0] / size[1] - res[0] / res[1]) < 1e-3, f'{shot}: loop size must keep the plate aspect {res}'
    P = PL.Plate(shot, size)
    report = {'shot': shot, **fn(P)}
    scene = P.finish(SAMPLES)
    scene.frame_end, scene.render.fps = frames, FPS

    # One rigid rig: camera (keys and TRACK_TO baked out at frame 1), its focus empty and the suns.
    scene.frame_set(1)
    cam, aim = P.cam, P.aim
    loc, aim_pt = Vector(cam.matrix_world.translation), Vector(aim.matrix_world.translation)
    loc = aim_pt + (loc - aim_pt) * ZOOM.get(shot, 1.0)
    cam.constraints.clear()
    cam.animation_data_clear()
    aim.animation_data_clear()
    cam.matrix_basis = L.track_matrix(loc, aim_pt)
    aim.location = aim_pt
    pivot = Vector(motion[2]) if motion[0] == 'turn' and motion[2] is not None else aim_pt
    rig = SC.empty(PL.PREFIX + 'LoopRig', P.rigc, tuple(pivot))
    rig.rotation_mode = 'QUATERNION'
    suns = [o for o in P.rigc.objects if o.type == 'LIGHT']
    for obj in [cam, aim] + suns:
        obj.parent = rig
        obj.matrix_parent_inverse = Matrix.Translation(-pivot)
    prev = None
    for f in range(1, frames + 2):
        q = L.rig_rotation(motion, P.direction, (f - 1) / frames)
        if prev is not None and prev.dot(q) < 0:
            q.negate()
        rig.rotation_quaternion = q
        rig.keyframe_insert('rotation_quaternion', frame=f)
        prev = q
    SC.set_linear(rig)
    scene.frame_set(1)
    report.update({'frames': frames, 'fps': FPS, 'res': list(size), 'samples': SAMPLES, 'suns': len(suns),
                   'zoom': ZOOM.get(shot, 1.0),
                   'motion': list(motion[:3]) if motion[0] == 'drift' else ['turn', [round(float(v), 3) for v in motion[1]]],
                   'pivot': [round(v, 2) for v in pivot]})
    return scene, report


def render_still(scene, frame, out):
    scene.frame_set(frame)
    scene.render.filepath = str(out)
    with bpy.context.temp_override(scene=scene):
        bpy.ops.render.render(write_still=True, scene=scene.name)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', required=True, choices=sorted(LOOPS))
    ap.add_argument('--save', action='store_true')
    ap.add_argument('--stills', help='comma-separated loop phases u in [0, 1) to render as stills')
    ap.add_argument('--frames', help='comma-separated frame numbers to render as stills')
    ap.add_argument('--out', help='folder for --stills / --frames')
    ap.add_argument('--percent', type=int, default=100)
    ap.add_argument('--samples', type=int)
    args = ap.parse_args(argv)
    PL.W.gpu()
    scene, report = build(args.shot)
    if args.save:
        path = HERE / 'loops' / f'plate-{args.shot}.blend'
        SC.save_scene(scene, path)
        report['blend'] = str(path)
    picks = []
    if args.stills:
        n = LOOPS[args.shot][0]
        picks += [1 + round(float(u) * n) for u in args.stills.split(',')]
    if args.frames:
        picks += [int(f) for f in args.frames.split(',')]
    if picks:
        scene.render.resolution_percentage = args.percent
        if args.samples:
            scene.cycles.samples = args.samples
        out_dir = Path(args.out).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        report['stills'] = []
        for f in picks:
            out = out_dir / f'{args.shot}-f{f:04d}.png'
            render_still(scene, f, out)
            report['stills'].append(str(out))
    print('RESULT ' + json.dumps(report))
