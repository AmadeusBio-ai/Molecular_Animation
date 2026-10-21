"""amadeusbio.ai website assets, built with molanim from the channelrhodopsin case study (PDB 9GO1 / 9GO2).

One script, one scene per shot (prefix WEB_). Every shot uses one of the website's two looks:
  deep  navy gradient backdrop, pale porcelain atoms, cool rim light (dark panels)
  mist  pale blue-grey gradient backdrop, navy atoms, soft studio light (light cards)
with the brand's amber as the single accent.

Evidence (docs/principles.md): coordinates are the deposited models, 9GO1 (dark state) and 9GO2 alt B (early
light-activated state), matched atom by atom by the case study's c1c2.states(). The breathing motion, the morph
intermediates, the open pathway, the membrane and the agent markers are illustrative; the website's captions say so.

Headless (from the repo root):
  blender -b --factory-startup --python projects/website/website.py -- --shot hero --save
  blender -b --factory-startup --python projects/website/website.py -- --shot bridge --still renders/website/bridge.png
Options: --percent P (resolution %), --samples N. `--save` writes projects/website/<shot>.blend for
tools/render.py (loops); `--still PATH` renders frame 1.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CASE = ROOT / 'examples' / 'channelrhodopsin'
sys.path[:0] = [str(ROOT), str(CASE)]
import molanim  # noqa: E402

molanim.reload()
import c1c2 as S  # noqa: E402
from molanim import color, membrane  # noqa: E402
from molanim import structure as St  # noqa: E402
from molanim.blender import groups, look, mesh, rig  # noqa: E402
from molanim.blender import scene as SC  # noqa: E402
from molanim.blender.nodes import set_modifier_inputs  # noqa: E402

if 'c1c2' in sys.modules:
    import importlib
    importlib.reload(S)

PREFIX = 'WEB_'
DARK, LIGHT = ROOT / 'assets' / 'pdb' / '9GO1.cif', ROOT / 'assets' / 'pdb' / '9GO2.cif'
MEMBRANE_Y = 33.0                 # crystal y of the bilayer centre (as in the case study)

# Brand (sRGB 0-255): the navy ramp of the AmadeusBio mark and the amber of the retinal chromophore.
AMBER = (233, 166, 60)
RETINAL_C = ((226, 136, 28), (255, 192, 84))
ELEMENT = {'C': ((198, 205, 214), (236, 240, 244)), 'N': ((52, 94, 204), (96, 136, 236)),
           'O': ((208, 72, 62), (236, 112, 98)), 'S': ((226, 186, 40), (246, 214, 90))}

LOOKS = {
    'deep': {
        'world': ('radial', (36, 78, 132), (5, 22, 52)), 'ambient': ((84, 114, 164), 0.36),
        'prot_a': ((200, 213, 230), (246, 248, 252)), 'prot_b': ((84, 124, 180), (146, 178, 220)),
        'lipid_head': ((64, 92, 134), (98, 126, 166)), 'lipid_tail': ((40, 64, 102), (66, 92, 130)),
        'key': ((-0.55, -0.8, 0.75), 4.2, (255, 244, 228)), 'rim': ((0.75, 0.85, 0.3), 6.5, (122, 172, 255)),
        'fill': ((0.1, -1.0, -0.45), 0.7, (150, 182, 236)), 'section': (196, 214, 238),
    },
    'mist': {
        'world': ('vertical', (247, 249, 252), (219, 227, 236)), 'ambient': ((224, 230, 238), 0.50),
        'prot_a': ((20, 50, 98), (78, 110, 156)), 'prot_b': ((118, 140, 170), (176, 191, 211)),
        'lipid_head': ((128, 150, 180), (172, 188, 208)), 'lipid_tail': ((184, 197, 214), (214, 222, 232)),
        'key': ((-0.55, -0.75, 0.9), 3.4, (255, 250, 242)), 'rim': ((0.6, 1.0, 0.5), 1.8, (255, 255, 255)),
        'fill': ((0.3, -1.0, -0.2), 0.4, (236, 242, 250)), 'section': (176, 200, 232),
    },
}
PROTEIN_SCALE, BALL_SCALE, STICK_RADIUS = 0.64, 0.28, 0.16

# Each shot: look, resolution, frames (1 = still), camera (aim, distance A or ('fit', k), azimuth, elevation,
# lens), depth of field (aperture radius / focus distance) and what to show.
SHOTS = {
    'hero': dict(look='deep', res=(960, 960), frames=300, aim='centre', dist=('fit', 1.18), az=-24, el=9, lens=50,
                 dof=0.006, turn=True, side=True, scale=0.92),
    'agents': dict(look='deep', res=(1600, 1000), frames=1, aim='centre', dist=('fit', 1.1), az=-30, el=12, lens=50,
                   dof=0.008, agents=True, side=True, scale=0.92),
    'context': dict(look='mist', res=(1600, 1200), frames=1, aim=('centre', (0, 0, 2)), dist=215, az=-30, el=11, lens=50,
                    dof=0.014, membrane=True),
    'bridge': dict(look='mist', res=(1600, 1200), frames=1, aim='bridge', dist=37, az=28, el=10, lens=50, dof=0.016,
                   state='light', bridge=True, cut='bridge', prot_a=((64, 96, 144), (138, 162, 196)), prot_b=((150, 166, 190), (200, 210, 224))),
    'states': dict(look='mist', res=(1600, 1200), frames=1, aim='retinal', dist=40, az=-8, el=38, lens=50, dof=0.014,
                   states=True, cut='retinal', prot_a=((64, 96, 144), (138, 162, 196)), prot_b=((150, 166, 190), (200, 210, 224))),
    'cta': dict(look='deep', res=(1600, 900), frames=1, aim=('centre', (0, 0, 10)), dist=('fit', 0.5), az=38, el=22,
                lens=50, dof=0.03, side=True, scale=0.92),
    'spheres': dict(look='mist', res=(1600, 1200), frames=1, aim='centre', dist=('fit', 1.08), az=-38, el=8, lens=50,
                    dof=0.006, side=True, scale=0.92),
    'cutaway': dict(look='mist', res=(1600, 1200), frames=1, aim='retinal', dist=72, az=-12, el=8, lens=50, dof=0.012,
                    pocket=True, cut='retinal'),
    'cavity': dict(look='mist', res=(1600, 1200), frames=1, aim=('cavity', (0, 0, 0)), dist=112, az=24, el=5, lens=50,
                   dof=0.008, state='light', cavity=True, slab=True, scale=0.8, prot_a=((64, 96, 144), (138, 162, 196)), prot_b=((150, 166, 190), (200, 210, 224))),
}


def gpu():
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for backend in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            if any(d.type == backend for d in prefs.devices):
                break
        except TypeError:
            continue
    for d in prefs.devices:
        d.use = d.type == prefs.compute_device_type


def radial_world(name, centre, edge, ambient, strength, res, focus=(0.56, 0.54), reach=0.78):
    """The camera sees a soft radial glow (`centre` colour around `focus` in window coordinates, fading to `edge`
    at distance `reach`, aspect-corrected); objects are lit by a flat `ambient` instead."""
    w = bpy.data.worlds.new(name)
    if w.node_tree is None:
        w.use_nodes = True
    nt = w.node_tree
    out = nt.nodes['World Output']
    for n in list(nt.nodes):
        if n != out:
            nt.nodes.remove(n)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sub = nt.nodes.new('ShaderNodeVectorMath')
    sub.operation = 'SUBTRACT'
    sub.inputs[1].default_value = (focus[0], focus[1], 0.0)
    mul = nt.nodes.new('ShaderNodeVectorMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = (res[0] / res[1], 1.0, 0.0)
    length = nt.nodes.new('ShaderNodeVectorMath')
    length.operation = 'LENGTH'
    rmap = nt.nodes.new('ShaderNodeMapRange')
    rmap.interpolation_type = 'SMOOTHERSTEP'
    rmap.inputs['From Min'].default_value, rmap.inputs['From Max'].default_value = 0.0, reach
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    sock = {s.identifier: s for s in mix.inputs}
    sock['A_Color'].default_value = (*color.lin(centre), 1)
    sock['B_Color'].default_value = (*color.lin(edge), 1)
    nt.links.new(tc.outputs['Window'], sub.inputs[0])
    nt.links.new(sub.outputs[0], mul.inputs[0])
    nt.links.new(mul.outputs[0], length.inputs[0])
    nt.links.new(length.outputs['Value'], rmap.inputs['Value'])
    nt.links.new(rmap.outputs['Result'], sock['Factor_Float'])
    seen, lit = nt.nodes.new('ShaderNodeBackground'), nt.nodes.new('ShaderNodeBackground')
    nt.links.new(next(s for s in mix.outputs if s.identifier == 'Result_Color'), seen.inputs['Color'])
    lit.inputs['Color'].default_value = (*color.lin(ambient), 1)
    lit.inputs['Strength'].default_value = strength
    path, pick = nt.nodes.new('ShaderNodeLightPath'), nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(path.outputs['Is Camera Ray'], pick.inputs[0])
    nt.links.new(lit.outputs[0], pick.inputs[1])
    nt.links.new(seen.outputs[0], pick.inputs[2])
    nt.links.new(pick.outputs[0], out.inputs['Surface'])
    return w


def structures(cavity=False):
    """Protomer A (and B from the deposited assembly) on the stage, dark and light coordinates, and points."""
    s = S.states(DARK, LIGHT)
    edges = S.bonds(s)
    Tm = S.stage_matrix(s, MEMBRANE_Y, 0.0)
    xyz = {k: St.transform(s[k], Tm) for k in ('dark', 'light')}
    xyz_b = {k: St.transform(St.transform(s[k], s['operator']), Tm) for k in ('dark', 'light')}
    ret = s['resn'] == 'RET'

    def at(resi, name, state='dark'):
        return xyz[state][S.atom_index(s, resi, name)]
    both = np.vstack([xyz['dark'], xyz_b['dark']])
    pts = {
        'axis': np.array([0.0, 0.0, 4.0]),
        'centre': (both.min(0) + both.max(0)) / 2,
        'A': xyz['dark'].mean(0), 'B': xyz_b['dark'].mean(0),
        'retinal': xyz['dark'][ret].mean(0),
        'bridge': (at(132, 'NZ', 'light') + at(129, 'OE1', 'light')) / 2,
        'pore': (np.mean([at(r, a, 'light') for r, a in S.GATE_ATOMS['central']], 0)
                 + np.mean([at(r, a, 'light') for r, a in S.GATE_ATOMS['inner']], 0)) / 2,
    }
    if cavity:
        line, r_free, _, _ = S.pathway(s, s['light'], Tm, [(140, 'CD'), (136, 'CD'), (129, 'CD'), (122, 'CD')])
        pts['cavity'] = line.mean(0)
        pts['cavity_line'], pts['cavity_r'] = line, r_free
    return s, edges, Tm, xyz, xyz_b, pts


def build(name, percent=100, samples=None):
    cfg = SHOTS[name]
    L = LOOKS[cfg['look']]
    frames, res = cfg['frames'], cfg['res']
    scene = SC.reset_scene('Web_' + name, PREFIX)
    col_main, col_fx, col_rig = (SC.collection(scene, PREFIX + c) for c in ('Main', 'Effects', 'Rig'))
    rng = np.random.default_rng(7)
    s, edges, Tm, xyz, xyz_b, pts = structures(cavity=bool(cfg.get('cavity')))
    n = len(s['name'])
    ret = s['resn'] == 'RET'
    side = ~np.isin(s['name'], ['N', 'C', 'O'])
    vdw = St.radii(s['element'])
    state = cfg.get('state', 'dark')
    report = {'shot': name, 'look': cfg['look'], 'atoms_per_protomer': n, 'state': state}

    def resolve(v):
        if isinstance(v, tuple):
            return pts[v[0]] + np.asarray(v[1], float)
        return pts[v]
    aim = resolve(cfg['aim'])

    # --- roles: 2 = always ball-and-stick, 1 = revealed pocket side chains
    role = np.zeros(n)
    if cfg.get('pocket') or cfg.get('states'):
        k296 = (s['resi'] == 296) & ~ret & side
        role[ret | k296] = 2
    if cfg.get('pocket'):
        for resi in (262, 132, 129, 300, 266, 297, 205, 169):
            role[(s['resi'] == resi) & ~ret & side] = 1
    if cfg.get('bridge'):
        for resi in (132, 129):
            role[(s['resi'] == resi) & ~ret & side] = 2
        role[ret] = 0

    # --- colours
    ctx_a = color.shade(rng, cfg.get('prot_a', L['prot_a']), n, 0.0, 1.0)
    ctx_b = color.shade(rng, cfg.get('prot_b', L['prot_b']), n, 0.0, 1.0)
    hi = np.zeros((n, 3))
    for el, tones in ELEMENT.items():
        sel = s['element'] == el
        hi[sel] = color.shade(rng, tones, sel.sum(), 0.3, 1.0)
    ret_c = ret & (s['element'] == 'C')
    hi[ret_c] = color.shade(rng, RETINAL_C, ret_c.sum(), 0.4, 1.0)
    if cfg.get('glow'):                            # the retinal keeps its amber in the sphere model and glows
        ctx_a[ret] = color.shade(rng, RETINAL_C, ret.sum(), 0.4, 1.0)
        ctx_b[ret] = color.shade(rng, RETINAL_C, ret.sum(), 0.4, 1.0)
    if cfg.get('bridge'):                          # the two salt-bridge partners carry the accent
        partners = np.isin(s['resi'], [132, 129]) & ~ret & side & (s['element'] == 'C')
        hi[partners] = color.shade(rng, RETINAL_C, partners.sum(), 0.4, 1.0)

    # --- rig
    cam = bpy.data.objects.new(PREFIX + 'Camera', bpy.data.cameras.new(PREFIX + 'Camera'))
    col_rig.objects.link(cam)
    scene.camera = cam
    aim_obj = SC.empty(PREFIX + 'Aim', col_rig, aim)
    target = SC.empty(PREFIX + 'CutTarget', col_rig, pts[cfg['cut']] if cfg.get('cut') else aim)
    slab = SC.empty(PREFIX + 'Slab', col_rig, pts[cfg.get('slab_at', 'pore')])
    ctl_cut = SC.empty(PREFIX + 'Ctl_Cut', col_rig)
    ctl_look = SC.empty(PREFIX + 'Ctl_Look', col_rig)
    ctl_path = SC.empty(PREFIX + 'Ctl_Path', col_rig)
    ctl_cut.location = (1.0 if cfg.get('cut') else 0.0, 1.0 if cfg.get('slab') else 0.0, 0.0)
    ctl_look.location = (1.0, 1.4, 2.2 if cfg.get('glow') else 0.0)
    cut_enable = 1.0 if (cfg.get('cut') or cfg.get('slab')) else 0.0

    radius = float(np.percentile(np.linalg.norm(np.vstack([xyz['dark'], xyz_b['dark']]) - pts['centre'], axis=1), 99.5))
    half = math.atan(0.5 * 36.0 * min(1.0, res[1] / res[0]) / cfg['lens'])
    fit = radius / math.tan(half) * 1.06
    dist = cfg['dist']
    dist = fit * dist[1] if isinstance(dist, tuple) else float(dist)
    az0 = 0.0
    if cfg.get('side'):                             # azimuth 0 = looking across the dimer, both protomers side by side
        v = pts['B'] - pts['A']
        az0 = math.degrees(math.atan2(v[1], v[0]))
        az0 = az0 - 180.0 if math.cos(math.radians(az0)) < 0 else az0
    az, el = math.radians(az0 + cfg['az']), math.radians(cfg['el'])
    direction = np.array([math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)])
    path = [(1, aim + dist * direction, aim, dist, cfg['lens'])]
    rig.bake_camera(cam, aim_obj, path, max(cfg['dof'], 1e-4), clip=(0.5, 40 * dist))
    report.update(radius_A=round(radius, 1), fit_A=round(fit, 1), distance_A=round(dist, 1))

    breath = groups.breath(PREFIX, sway=0.30, jitter=0.10, loop_frames=frames if frames > 1 else None)
    ng = groups.molecule(PREFIX, breath, cfg.get('scale', PROTEIN_SCALE), BALL_SCALE, STICK_RADIUS, L['section'], 0.4)
    atom_mat = look.attr_material(PREFIX + 'Atom', roughness=0.40, specular=0.5, sheen=0.2)

    # --- the two protomers (A is the annotated one)
    for pname, coords, ctx, enable in (('ProtomerA', xyz[state], ctx_a, 1.0), ('ProtomerB', xyz_b[state], ctx_b, 0.0)):
        r = role * enable
        attrs = {'vdw': ('FLOAT', vdw), 'role': ('FLOAT', r), 'ball': ('FLOAT', np.ones(n)), 'stick_w': ('FLOAT', np.ones(n)),
                 'dilate': ('FLOAT_VECTOR', np.zeros((n, 3))), 'g0': ('FLOAT', (r == 2).astype(float)),
                 'g1': ('FLOAT', (r == 1).astype(float)), 'g2': ('FLOAT', np.zeros(n)),
                 'col_ctx': ('FLOAT_COLOR', ctx), 'col_hi': ('FLOAT_COLOR', hi if enable else ctx),
                 'emit_w': ('FLOAT', np.where(ret, 0.5, 0.0) * enable * (r > 0)),
                 'glow_w': ('FLOAT', np.where(ret, 1.0, 0.0) if cfg.get('glow') else np.zeros(n))}
        obj = mesh.points_mesh(PREFIX + pname, coords, edges, attrs, col_main)
        mod = obj.modifiers.new('Atoms', 'NODES')
        mod.node_group = ng
        set_modifier_inputs(mod, {'Material': atom_mat, 'Camera': cam, 'Target': target, 'Slab': slab, 'Cut': ctl_cut,
                                  'Look': ctl_look, 'Cut Enable': cut_enable * enable,
                                  'Path Control': ctl_path, 'Funnel': 7.5})

    # --- retinal states: the two deposited endpoints solid, the illustrative morph between them as ghosts
    if cfg.get('states'):
        snaps, morph_report = S.activation_path(s, edges, 12, 12)
        snaps = [St.transform(x, Tm) for x in snaps]
        unit = np.nonzero(ret | ((s['resi'] == 296) & ~ret & side))[0]
        remap = {old: k for k, old in enumerate(unit)}
        unit_edges = [(remap[a], remap[b]) for a, b in edges if a in remap and b in remap]
        m = len(unit)
        gmat, galpha = look.ghost_material(PREFIX + 'Ghost', (214, 228, 250))
        galpha.default_value = 0.38
        for k in (3, 6, 9):                     # intermediates of morph stage 1 (the twist)
            g = mesh.points_mesh(PREFIX + f'Ghost{k}', snaps[k][unit], unit_edges, {
                'vdw': ('FLOAT', vdw[unit]), 'role': ('FLOAT', np.full(m, 2.0)), 'g0': ('FLOAT', np.ones(m)),
                'ball': ('FLOAT', np.ones(m)), 'stick_w': ('FLOAT', np.ones(m)), 'dilate': ('FLOAT_VECTOR', np.zeros((m, 3))),
                'g1': ('FLOAT', np.zeros(m)), 'g2': ('FLOAT', np.zeros(m)),
                'col_ctx': ('FLOAT_COLOR', color.tile((214, 228, 250), m)), 'col_hi': ('FLOAT_COLOR', color.tile((214, 228, 250), m)),
                'emit_w': ('FLOAT', np.zeros(m)), 'glow_w': ('FLOAT', np.zeros(m))}, col_fx)
            gm = g.modifiers.new('Atoms', 'NODES')
            gm.node_group = ng
            set_modifier_inputs(gm, {'Material': gmat, 'Camera': cam, 'Target': target, 'Slab': slab, 'Cut': ctl_cut,
                                     'Look': ctl_look, 'Cut Enable': 0.0, 'Ball': 0.22, 'Stick': 0.10})
            g.visible_shadow = False
        # the 13-cis endpoint (end of the twist), in steel blue
        endp = snaps[12][unit]
        steel = color.shade(rng, ((70, 104, 150), (120, 150, 190)), m, 0.2, 1.0)
        e = mesh.points_mesh(PREFIX + 'Twisted', endp, unit_edges, {
            'vdw': ('FLOAT', vdw[unit]), 'role': ('FLOAT', np.full(m, 2.0)), 'g0': ('FLOAT', np.ones(m)),
            'ball': ('FLOAT', np.ones(m)), 'stick_w': ('FLOAT', np.ones(m)), 'dilate': ('FLOAT_VECTOR', np.zeros((m, 3))),
            'g1': ('FLOAT', np.zeros(m)), 'g2': ('FLOAT', np.zeros(m)),
            'col_ctx': ('FLOAT_COLOR', steel), 'col_hi': ('FLOAT_COLOR', steel),
            'emit_w': ('FLOAT', np.zeros(m)), 'glow_w': ('FLOAT', np.zeros(m))}, col_main)
        em = e.modifiers.new('Atoms', 'NODES')
        em.node_group = ng
        set_modifier_inputs(em, {'Material': atom_mat, 'Camera': cam, 'Target': target, 'Slab': slab, 'Cut': ctl_cut,
                                 'Look': ctl_look, 'Cut Enable': 0.0})
        report['twist_dihedral_deg'] = [morph_report['twist_dihedral_deg'][k] for k in (0, 3, 6, 9, 12)]

    # --- salt bridge: Lys132 NZ - Glu129 OE1 in the light-activated state (deposited coordinates)
    if cfg.get('bridge'):
        i1, i2 = S.atom_index(s, 132, 'NZ'), S.atom_index(s, 129, 'OE1')
        p1, p2 = xyz['light'][i1], xyz['light'][i2]
        b = mesh.points_mesh(PREFIX + 'SaltBridge', [p1, p2], [(0, 1)], None, col_fx)
        bm = b.modifiers.new('Bridge', 'NODES')
        bm.node_group = groups.dotted_link(PREFIX, breath, dots=6, bead=0.16)
        show = SC.empty(PREFIX + 'Ctl_Bridge', col_rig, (1.0, 0, 0))
        set_modifier_inputs(bm, {'Material': look.glow_material(PREFIX + 'Bridge', (255, 214, 140), 7.0)[0], 'Show': show})
        b.visible_shadow = False
        report['k132_e129_A'] = round(float(np.linalg.norm(p1 - p2)), 2)

    # --- cation pathway (9GO2 free-radius profile; shown as measured, interrupted at the gates)
    if cfg.get('cavity'):
        line, r_free = pts['cavity_line'], pts['cavity_r']
        r0 = np.clip(r_free, 0.0, None)
        arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))])
        taper = np.clip(np.minimum(arc, arc[-1] - arc) / 6.0, 0, 1) ** 0.5
        cav = mesh.points_mesh(PREFIX + 'Cavity', line, [(k, k + 1) for k in range(len(line) - 1)],
                               {'r0': ('FLOAT', r0), 'r1': ('FLOAT', np.maximum(r0, 1.3)), 'taper': ('FLOAT', taper)}, col_fx)
        cm = cav.modifiers.new('Cavity', 'NODES')
        cm.node_group = groups.tube(PREFIX, margin=0.5)
        ctl_path.location = (1.0, 0.0, 0.0)
        set_modifier_inputs(cm, {'Material': look.glow_material(PREFIX + 'Cavity', (96, 160, 240), 1.3, rim=True)[0],
                                 'Control': ctl_path})
        cav.visible_shadow = False
        report['pathway_min_free_radius_A'] = round(float(r_free.min()), 2)

    # --- membrane: a section (context) or a round patch (hero), procedural, not simulated
    if cfg.get('membrane') or cfg.get('disc'):
        prot = np.vstack([xyz[state], xyz_b[state]])
        if cfg.get('disc'):
            R = cfg['disc']
            mem = membrane.bilayer((-R, R, -R, R), prot, seed=5, keep=lambda p: p @ p < R * R)
        else:
            mem = membrane.bilayer((-210.0, 210.0, -4.0, 260.0), prot, seed=5, keep=lambda p: p[1] > -4.0)
        head = mem['part'] == 'head'
        mcol = np.where(head[:, None], color.shade(rng, L['lipid_head'], len(head)), color.shade(rng, L['lipid_tail'], len(head)))
        mrad = St.radii(mem['element']) * np.where(head, 0.62, 0.78)
        lip = mesh.points_mesh(PREFIX + 'Membrane', mem['xyz'], None, {'radius': ('FLOAT', mrad), 'col': ('FLOAT_COLOR', mcol)}, col_main)
        lm = lip.modifiers.new('Lipids', 'NODES')
        lm.node_group = groups.spheres(PREFIX, breath)
        set_modifier_inputs(lm, {'Material': look.attr_material(PREFIX + 'Lipid', roughness=0.5, specular=0.3, sheen=0.1)})
        report.update(lipids=int(mem['count']), lipid_atoms=len(mem['xyz']))

    # --- agent markers: amber beads on exposed atoms, joined into one connected trail (an illustration)
    if cfg.get('agents'):
        both = np.vstack([xyz['dark'], xyz_b['dark']])
        cam_dir = direction
        centre = both.mean(0)
        outward = both - centre
        facing = (outward @ cam_dir) / (np.linalg.norm(outward, axis=1) + 1e-9)
        exposed = np.linalg.norm(outward, axis=1) > np.percentile(np.linalg.norm(outward, axis=1), 70)
        cand = np.nonzero(exposed & (facing > 0.4))[0]
        picks = [int(cand[np.argmax(facing[cand])])]  # start from the atom facing the camera most directly
        while len(picks) < 8:                       # farthest-point sampling over the visible surface
            d = np.min(np.linalg.norm(both[cand][:, None] - both[picks][None], axis=2), axis=1)
            picks.append(int(cand[np.argmax(d)]))
        P = both[picks]
        P = P + (P - centre) / np.linalg.norm(P - centre, axis=1)[:, None] * 2.2
        order = [0]                                 # nearest-neighbour tour through the markers
        while len(order) < len(P):
            rest = [k for k in range(len(P)) if k not in order]
            order.append(min(rest, key=lambda k: np.linalg.norm(P[k] - P[order[-1]])))
        P = P[order]
        marks = mesh.points_mesh(PREFIX + 'Agents', P, None, {'radius': ('FLOAT', np.full(len(P), 1.5))}, col_fx)
        am = marks.modifiers.new('Agents', 'NODES')
        am.node_group = groups.spheres(PREFIX, None, name='Agents')
        set_modifier_inputs(am, {'Material': look.glow_material(PREFIX + 'Agent', AMBER, 9.0)[0]})
        marks.visible_shadow = False
        # trail: curved arcs between consecutive markers, lifted off the surface
        cu = bpy.data.curves.new(PREFIX + 'Trail', 'CURVE')
        cu.dimensions, cu.bevel_depth, cu.bevel_resolution = '3D', 0.15, 3
        for a, b in zip(P[:-1], P[1:]):
            mid = (a + b) / 2
            lift = (mid - centre) / np.linalg.norm(mid - centre) * (0.2 * np.linalg.norm(b - a))
            sp = cu.splines.new('BEZIER')
            sp.bezier_points.add(1)
            for bp, p, h in ((sp.bezier_points[0], a, a + (mid + lift - a) * 0.6), (sp.bezier_points[1], b, b + (mid + lift - b) * 0.6)):
                bp.co = p
                bp.handle_left_type = bp.handle_right_type = 'FREE'
                bp.handle_left = bp.handle_right = h
        trail = bpy.data.objects.new(PREFIX + 'Trail', cu)
        trail.data.materials.append(look.glow_material(PREFIX + 'TrailGlow', AMBER, 1.6)[0])
        trail.visible_shadow = False
        col_fx.objects.link(trail)
        report['agent_markers'] = len(P)

    # --- world, lights
    kind, top, bottom = L['world']
    if kind == 'radial':
        scene.world = radial_world(PREFIX + 'World', top, bottom, *L['ambient'], res)
    else:
        scene.world = look.gradient_world(PREFIX + 'World', top, bottom, *L['ambient'])[0]
    lights = []
    for key in ('key', 'rim', 'fill'):
        d, e, rgb = L[key]
        lights.append(SC.sun(PREFIX + key.title(), d, e, 24 if key == 'key' else 14, col_rig, rgb, distance=3 * dist))

    # --- turntable: camera and lights orbit together (the molecule's object transform stays identity, which the
    # camera-aimed cut needs); one full turn per loop, so frame frames + 1 equals frame 1
    if cfg.get('turn'):
        turn = SC.empty(PREFIX + 'Turn', col_rig)
        for obj in [cam, *lights]:
            obj.parent = turn
        turn.rotation_euler = (0, 0, 0)
        turn.keyframe_insert('rotation_euler', index=2, frame=1)
        turn.rotation_euler = (0, 0, 2 * math.pi)
        turn.keyframe_insert('rotation_euler', index=2, frame=frames + 1)
        SC.set_linear(turn)

    if frames > 1:                                  # loops: denoised at low sample counts, short light paths
        SC.cycles_settings(scene, res, frames, 24, samples=samples or 48, adaptive=0.03, bounces=(4, 2, 1))
    else:
        SC.cycles_settings(scene, res, frames, 24, samples=samples or 256)
    scene.render.resolution_percentage = percent
    look.bloom(scene, PREFIX + 'Bloom', threshold=1.0, strength=0.5, size=0.6)
    scene.frame_set(1)
    return scene, report


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', required=True, choices=sorted(SHOTS))
    ap.add_argument('--still')
    ap.add_argument('--save', action='store_true')
    ap.add_argument('--percent', type=int, default=100)
    ap.add_argument('--samples', type=int)
    args = ap.parse_args(argv)
    gpu()
    scene, report = build(args.shot, args.percent, args.samples)
    if args.save:
        SC.save_scene(scene, HERE / f'{args.shot}.blend')
        report['blend'] = str(HERE / f'{args.shot}.blend')
    if args.still:
        out = Path(args.still).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(out)
        with bpy.context.temp_override(scene=scene):
            bpy.ops.render.render(write_still=True, scene=scene.name)
        report['still'] = str(out)
    print('RESULT ' + json.dumps(report))
