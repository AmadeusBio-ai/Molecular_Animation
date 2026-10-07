"""Scene housekeeping for idempotent builds, keyframes and render settings (Blender 5.x).

Every shot rebuilds one named scene whose datablocks share a name prefix. reset_scene() removes the
previous build and only that prefix's orphans, so other scenes in the open file are never touched.
"""
import math
from pathlib import Path

import bpy
from bpy_extras import anim_utils
from mathutils import Vector

from ..color import lin

BLOCK_TYPES = ('collections', 'meshes', 'curves', 'cameras', 'lights', 'materials', 'worlds', 'node_groups',
               'actions', 'images')


def window():
    """The UI window, or None when headless. Code run by the MCP add-on's timer may lack context.window."""
    wm = bpy.context.window_manager
    return bpy.context.window or (wm.windows[0] if wm and wm.windows else None)


def reset_scene(name, prefix):
    """Fresh scene `name`; removes the previous build and the `prefix` orphans it left behind."""
    scene = bpy.data.scenes.new(name + '_build')
    win = window()
    if win:
        win.scene = scene
    old = bpy.data.scenes.get(name)
    if old:
        for obj in list(old.objects):
            if len(obj.users_scene) == 1:
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.scenes.remove(old)
    # Containers before what they hold (text curves keep materials, node groups nest); repeat until stable.
    removed = True
    while removed:
        removed = False
        for attr in BLOCK_TYPES:
            blocks = getattr(bpy.data, attr)
            for block in list(blocks):
                if block.name.startswith(prefix) and block.users == 0:
                    blocks.remove(block)
                    removed = True
    scene.name = name
    return scene


def save_scene(scene, path):
    """Write only `scene` and its dependencies to `path` (the open file's path and other scenes are untouched)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.data.libraries.write(str(path), {scene}, path_remap='RELATIVE_ALL', fake_user=True)


def show(scene):
    """Make `scene` the window's scene (no-op headless)."""
    win = window()
    if win:
        win.scene = scene


def collection(scene, name):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    return col


def empty(name, collection, location=(0, 0, 0), size=3):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_size = size
    obj.location = location
    collection.objects.link(obj)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def keys(target, path, pairs, index=-1):
    """Keyframe a property at (frame, value) pairs (Bezier, auto-clamped: eases in and out of each key)."""
    for frame, value in pairs:
        if index >= 0:
            getattr(target, path)[index] = value
        else:
            setattr(target, path, value)
        target.keyframe_insert(path, index=index, frame=frame)


def fcurves(id_block):
    """F-curves of an ID's action (Blender 5.x: they live in the slot's channelbag)."""
    ad = id_block.animation_data
    return anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves


def set_linear(id_block):
    for fc in fcurves(id_block):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'


def sun(name, direction, strength, angle, collection, rgb=(255, 255, 255), distance=300):
    """Sun light shining from `direction` toward the origin; `angle` (deg) sets shadow softness."""
    light = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN'))
    light.data.energy, light.data.angle, light.data.color = strength, math.radians(angle), lin(rgb)
    light.location = Vector(direction) * distance
    look_at(light, (0, 0, 0))
    collection.objects.link(light)
    return light


def cycles_settings(scene, res, frames, fps, samples=128, adaptive=0.02, bounces=(6, 3, 2), transparent=12):
    """Studio defaults: GPU Cycles, adaptive sampling, denoised, Standard view transform, PNG frames 1..frames."""
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples, scene.cycles.adaptive_threshold = samples, adaptive
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces, scene.cycles.diffuse_bounces, scene.cycles.glossy_bounces = bounces
    scene.cycles.transparent_max_bounces = transparent
    scene.view_settings.view_transform, scene.view_settings.look = 'Standard', 'None'
    scene.frame_start, scene.frame_end, scene.render.fps = 1, frames, fps
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.use_persistent_data = True
    scene.render.image_settings.file_format = 'PNG'
