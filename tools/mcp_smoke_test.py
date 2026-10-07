"""Blender MCP smoke test: ball-and-stick water molecule with a looping spin.

Run inside Blender through Blender MCP (execute_blender_code):

    import runpy
    result = runpy.run_path(r'<repo>/tools/mcp_smoke_test.py', run_name='__main__')['RESULT']

or headless:  blender -b --python tools/mcp_smoke_test.py

Rebuilds the `MCP_Smoke_Test` scene from scratch, writes only that scene (and its
dependencies) to renders/mcp-smoke-test/, and renders one frame there.
"""
import math
from pathlib import Path

import bmesh
import bpy
from bpy_extras import anim_utils
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SCENE_NAME = 'MCP_Smoke_Test'
PREFIX = 'H2O_'
BLEND_PATH = ROOT / 'renders' / 'mcp-smoke-test' / 'mcp-smoke-test.blend'
RENDER_PATH = ROOT / 'renders' / 'mcp-smoke-test' / 'still.png'
FRAME_START, FRAME_END, FPS = 1, 96, 24

# 1 Blender unit = 1 Angstrom. Ball-and-stick radii, not van der Waals radii.
BOND_LENGTH = 0.96
HALF_ANGLE = math.radians(104.5 / 2)
O_RADIUS, H_RADIUS, BOND_RADIUS = 0.38, 0.24, 0.09


def window():
    wm = bpy.context.window_manager
    return bpy.context.window or (wm.windows[0] if wm and wm.windows else None)


def reset_scene():
    scene = bpy.data.scenes.new(SCENE_NAME + '_build')
    win = window()
    if win:
        win.scene = scene
    old = bpy.data.scenes.get(SCENE_NAME)
    if old:
        for obj in list(old.objects):
            if len(obj.users_scene) == 1:
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.scenes.remove(old)
    for blocks in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                   bpy.data.lights, bpy.data.worlds, bpy.data.actions):
        for block in list(blocks):
            if block.name.startswith(PREFIX) and block.users == 0:
                blocks.remove(block)
    scene.name = SCENE_NAME
    return scene


def material(name, color, rough=.35, coat=0.):
    m = bpy.data.materials.new(PREFIX + name)
    m.diffuse_color = (*color, 1)
    if m.node_tree is None:
        m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Coat Weight'].default_value = coat
    return m


def mesh_object(scene, name, build, mat, parent, loc=(0, 0, 0), rot=(0, 0, 0), sharp_angle=None):
    me = bpy.data.meshes.new(PREFIX + name)
    bm = bmesh.new()
    build(bm)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    if sharp_angle is not None:
        me.set_sharp_from_angle(angle=sharp_angle)
    me.materials.append(mat)
    obj = bpy.data.objects.new(PREFIX + name, me)
    obj.location, obj.rotation_euler, obj.parent = loc, rot, parent
    scene.collection.objects.link(obj)
    return obj


def atom(scene, name, pos, radius, mat, parent):
    build = lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=radius)
    return mesh_object(scene, name, build, mat, parent, loc=pos)


def bond(scene, name, a, b, mat, parent):
    a, b = Vector(a), Vector(b)
    build = lambda bm: bmesh.ops.create_cone(
        bm, cap_ends=True, segments=32, radius1=BOND_RADIUS, radius2=BOND_RADIUS, depth=(b - a).length)
    rot = Vector((0, 0, 1)).rotation_difference(b - a).to_euler()
    return mesh_object(scene, name, build, mat, parent, loc=(a + b) / 2, rot=rot, sharp_angle=math.radians(30))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def build():
    scene = reset_scene()
    oxygen = material('Oxygen', (.80, .07, .06), .32, .4)
    hydrogen = material('Hydrogen', (.93, .93, .91), .30, .4)
    stick = material('Bond', (.55, .56, .58), .45)

    mol = bpy.data.objects.new(PREFIX + 'Molecule', None)
    mol.empty_display_type = 'SPHERE'
    mol.empty_display_size = .2
    scene.collection.objects.link(mol)

    o = (0, 0, 0)
    h1 = (BOND_LENGTH * math.sin(HALF_ANGLE), 0, -BOND_LENGTH * math.cos(HALF_ANGLE))
    h2 = (-h1[0], 0, h1[2])
    atom(scene, 'O', o, O_RADIUS, oxygen, mol)
    atom(scene, 'H1', h1, H_RADIUS, hydrogen, mol)
    atom(scene, 'H2', h2, H_RADIUS, hydrogen, mol)
    bond(scene, 'Bond_OH1', o, h1, stick, mol)
    bond(scene, 'Bond_OH2', o, h2, stick, mol)

    # Seamless loop: the key after FRAME_END equals the first key plus one full turn.
    mol.rotation_euler = (0, 0, 0)
    mol.keyframe_insert('rotation_euler', index=2, frame=FRAME_START)
    mol.rotation_euler = (0, 0, 2 * math.pi)
    mol.keyframe_insert('rotation_euler', index=2, frame=FRAME_END + 1)
    anim = mol.animation_data
    # Blender 5.x: fcurves live in the action's channelbag for the object's slot.
    channelbag = anim_utils.action_get_channelbag_for_slot(anim.action, anim.action_slot)
    for fc in channelbag.fcurves:
        for key in fc.keyframe_points:
            key.interpolation = 'LINEAR'

    cam = bpy.data.objects.new(PREFIX + 'Camera', bpy.data.cameras.new(PREFIX + 'Camera'))
    cam.location = (0, -4.2, .6)
    look_at(cam, (0, 0, -.25))
    scene.collection.objects.link(cam)
    scene.camera = cam

    for name, loc, power, size in [('Key', (-3, -4, 4), 450, 4), ('Rim', (3.5, 2.5, 2.5), 300, 3)]:
        light = bpy.data.objects.new(PREFIX + name, bpy.data.lights.new(PREFIX + name, 'AREA'))
        light.data.energy, light.data.shape, light.data.size = power, 'DISK', size
        light.location = loc
        look_at(light, (0, 0, -.25))
        scene.collection.objects.link(light)

    world = bpy.data.worlds.new(PREFIX + 'World')
    world.color = (.2, .21, .23)
    if world.node_tree is None:
        world.use_nodes = True
    background = world.node_tree.nodes['Background']
    background.inputs['Color'].default_value = (.2, .21, .23, 1)
    background.inputs['Strength'].default_value = .6
    scene.world = world

    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.frame_start, scene.frame_end, scene.render.fps = FRAME_START, FRAME_END, FPS
    scene.render.resolution_x, scene.render.resolution_y = 640, 360
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(RENDER_PATH)

    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.data.libraries.write(str(BLEND_PATH), {scene}, path_remap='RELATIVE_ALL', fake_user=True)

    scene.frame_set(FRAME_START + (FRAME_END - FRAME_START + 1) // 8)
    RENDER_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True, scene=scene.name)

    return {
        'blender': bpy.app.version_string,
        'scene': scene.name,
        'objects': sorted(o.name for o in scene.objects),
        'engine': scene.render.engine,
        'frames': [scene.frame_start, scene.frame_end, scene.render.fps],
        'action': anim.action.name,
        'fcurves': [(fc.data_path, fc.array_index, len(fc.keyframe_points)) for fc in channelbag.fcurves],
        'rotation_at_frame_49_deg': round(math.degrees(channelbag.fcurves[0].evaluate(49)), 3),
        'blend': str(BLEND_PATH),
        'render': str(RENDER_PATH),
        'render_exists': RENDER_PATH.exists(),
    }


RESULT = build()
