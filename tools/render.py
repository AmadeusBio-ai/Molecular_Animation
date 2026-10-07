"""Render a saved shot headless on the GPU. Frame sequences resume: existing frames are skipped.

    blender -b <shot>.blend --python tools/render.py -- --out renders/<shot>/<take>/
    blender -b <shot>.blend --python tools/render.py -- --still 1 --out renders/<shot>/still.png

Options: --frames A-B, --step N (preview every Nth frame), --percent P (resolution %), --samples N.
Start a new take folder whenever the scene, assets or render settings change; never mix takes.
"""
import argparse
import sys
from pathlib import Path

import bpy

parser = argparse.ArgumentParser()
parser.add_argument('--out', required=True)
parser.add_argument('--still', type=int)
parser.add_argument('--frames')
parser.add_argument('--step', type=int, default=1)
parser.add_argument('--percent', type=int)
parser.add_argument('--samples', type=int)
parser.add_argument('--border', help='x0,y0,x1,y1 in full-frame pixels (top-left origin); renders only that crop')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])

prefs = bpy.context.preferences.addons['cycles'].preferences
for backend in ('OPTIX', 'CUDA', 'HIP', 'METAL', 'ONEAPI'):
    try:
        prefs.compute_device_type = backend
        prefs.get_devices()
        if any(d.type == backend for d in prefs.devices):
            break
    except TypeError:
        continue
for device in prefs.devices:
    device.use = device.type == prefs.compute_device_type

scene = bpy.context.scene
scene.cycles.device = 'GPU'
if args.percent:
    scene.render.resolution_percentage = args.percent
if args.samples:
    scene.cycles.samples = args.samples
if args.border:
    x0, y0, x1, y1 = (int(v) for v in args.border.split(','))
    W, H = scene.render.resolution_x, scene.render.resolution_y
    scene.render.use_border, scene.render.use_crop_to_border = True, True
    scene.render.border_min_x, scene.render.border_max_x = x0 / W, x1 / W
    scene.render.border_min_y, scene.render.border_max_y = 1 - y1 / H, 1 - y0 / H
out = Path(args.out).resolve()

if args.still is not None:
    out.parent.mkdir(parents=True, exist_ok=True)
    scene.frame_set(args.still)
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
else:
    out.mkdir(parents=True, exist_ok=True)
    if args.frames:
        scene.frame_start, scene.frame_end = (int(v) for v in args.frames.split('-'))
    scene.frame_step = args.step
    scene.render.filepath = str(out) + '/'
    scene.render.use_overwrite = False
    scene.render.use_placeholder = False
    bpy.ops.render.render(animation=True)
print('RENDER_DEVICE', prefs.compute_device_type, [d.name for d in prefs.devices if d.use])
