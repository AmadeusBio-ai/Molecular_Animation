"""Channelrhodopsin shot, version 4: the same science, timeline, camera and motion as version 3, drawn so that each
layer stands for something physical, on a white ground for the website (storyboard_v4.py says what changed).

  protein     cartoons from 9GO1's deposited secondary structure, re-ribboned for every snapshot of the morph,
              moved by version 3's elastic-network modes (each vertex carries its residue's Calpha mode shapes);
              protomer A opens with the camera-aimed funnel and the section slab (groups.section)
  actors      the pocket and gate residues, Lys296 and retinal in ball-and-stick (element colours, retinal's
              carbons amber), revealed on version 3's beats, with side-chain turns
  electrons   retinal's conjugated chain (C5 ... C15=NZ) with its pi lobes, per snapshot, so the lobes separate at
              C13=C14 while it twists and close again in 13-cis (electro.pi_chain_lobes); they brighten when the
              photon is absorbed (an illustrative excitation, not emitted light)
  light       the photons (wave packets) are the only things that glow
  context     a round patch of membrane (version 3's lipid motion), Na+ diffusing and crossing (version 3's tracks
              and clearance checks against atoms at 0.64 x van der Waals), the pore as the measured tube
Coordinates and evidence as version 3 (record.md): 9GO1 dark, 9GO2 alt B light; morph and conducting state are
illustrative.

    python pipeline.py build channelrhodopsin-v4
Rebuilds scene `Channelrhodopsin_v4` (channelrhodopsin-v4.blend), its label scene (channelrhodopsin-v4-labels.blend)
and the web labels (delivery/channelrhodopsin-v4/labels.json).
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(HERE)]
import molanim  # noqa: E402

molanim.reload()
import c1c2 as S  # noqa: E402
import labels_data as LD  # noqa: E402
import storyboard_v4 as B  # noqa: E402
from molanim import cartoon as Ct  # noqa: E402
from molanim import color, membrane, particles  # noqa: E402
from molanim import dynamics as D  # noqa: E402
from molanim import electro as E  # noqa: E402
from molanim import structure as St  # noqa: E402
from molanim import timeline as TL  # noqa: E402
from molanim.blender import groups, labels, look, mesh, rig  # noqa: E402
from molanim.blender import scene as SC  # noqa: E402
from molanim.blender.nodes import set_modifier_inputs  # noqa: E402

for _m in ('c1c2', 'storyboard_v4', 'labels_data'):
    if _m in sys.modules:
        import importlib
        importlib.reload(sys.modules[_m])

SCENE_NAME, PREFIX = 'Channelrhodopsin_v4', 'CH4_'
DARK, LIGHT = ROOT / 'assets' / 'pdb' / '9GO1.cif', ROOT / 'assets' / 'pdb' / '9GO2.cif'
BLEND_PATH = HERE / 'channelrhodopsin-v4.blend'
LABEL_BLEND = HERE / 'channelrhodopsin-v4-labels.blend'
WEB_LABELS = ROOT / 'delivery' / 'channelrhodopsin-v4' / 'labels.json'
V3_RESULT = ROOT / 'renders' / 'channelrhodopsin' / 'build-result.json'
FPS, FRAMES, RES, T = B.FPS, B.FRAMES, B.RES, B.T


def ramp(tones, u):
    a, b = np.array(color.lin(tones[0])), np.array(color.lin(tones[1]))
    return a + (b - a) * np.asarray(u, float)[:, None]


def build():
    scene = SC.reset_scene(SCENE_NAME, PREFIX)
    cols = {k: SC.collection(scene, PREFIX + k) for k in ('Main', 'Membrane', 'Effects', 'Rig')}
    col_main, col_mem, col_fx, col_rig = cols['Main'], cols['Membrane'], cols['Effects'], cols['Rig']
    rng = np.random.default_rng(3)
    lin = color.lin

    # --- structure, activation path, stage (as version 3)
    s = S.states(DARK, LIGHT)
    edges = S.bonds(s)
    snaps, report = S.activation_path(s, edges, B.TWIST_STEPS, B.NETWORK_STEPS)
    Tm = S.stage_matrix(s, B.MEMBRANE_Y, B.YAW_OFFSET)
    A_snaps = [St.transform(x, Tm) for x in snaps]
    B_snaps = [St.transform(St.transform(x, s['operator']), Tm) for x in snaps]
    n = len(s['name'])
    ret = s['resn'] == 'RET'
    _, dark_lines = St.read_mmcif(DARK, skip=S.SKIP)
    ss = Ct.secondary_structure(dark_lines, s)

    def at(resi, name, snap=0):
        return A_snaps[snap][S.atom_index(s, resi, name)]

    def centre(names, snap=0):
        return np.mean([at(r, a, snap) for r, a in names], axis=0)
    points = {
        'dimer_top': np.array([0.0, 0.0, 6.0]), 'retinal': A_snaps[0][ret].mean(0),
        'network': centre([(132, 'NZ'), (129, 'CD'), ('RET', 'C15'), (262, 'CZ2')]),
        'central_gate': centre(S.GATE_ATOMS['central']), 'inner_gate': centre(S.GATE_ATOMS['inner']),
    }
    line, r_free, site_s, pore_report = S.pathway(s, snaps[-1], Tm, B.SITES)
    points['pore'] = (points['central_gate'] + points['inner_gate']) / 2

    # --- thermal motion (version 3, unchanged)
    mrng = np.random.default_rng(41)
    times, rate = D.clock(FRAMES, B.CLOCK_NS / FPS, B.CLOCK_HOLDS)
    window = rate * B.EXPOSURE
    nodes, node_of = D.residue_nodes(s['resi'], s['name'])
    node_of[ret] = node_of[S.atom_index(s, 296, 'CA')]
    m = len(nodes)
    links = D.sequence_pairs(A_snaps[0], nodes)
    eig, vec = D.anm(np.vstack([A_snaps[0][nodes], B_snaps[0][nodes]]), B.ANM['cutoff'], modes=B.ANM['modes'],
                     bonded=links + [(i + m, j + m) for i, j in links])
    mode_scale = D.mode_scale(eig, vec, B.ANM['rmsf'])
    q = D.mode_amplitudes(mrng, eig, times, window, mode_scale, B.ANM['tau'])
    unit_mask = ret | (s['resi'] == 296)
    shapes = {'A': D.atom_shapes(A_snaps[0], vec[:m], nodes, node_of, links, unit_mask),
              'B': D.atom_shapes(B_snaps[0], vec[m:], nodes, node_of, links, unit_mask)}
    topo = D.chi_topology(s['resn'], s['resi'], s['name'])
    n_res = topo['residues']
    held = np.isin(s['resi'], B.CHI['held']) | ret
    for k in ('chi1_w', 'chi2_w'):
        topo[k] = np.where(held, 0.0, topo[k])
    probe = []
    for r in range(n_res):
        idx = np.nonzero(topo['slot'] == r)[0]
        probe.append(next((i for nm in ('CB', 'CA') for i in idx if s['name'][i] == nm), idx[0]))
    probe = np.array(probe)
    both = np.vstack([A_snaps[0], B_snaps[0]])
    crowd = np.concatenate([D.burial(both, probe), D.burial(both, probe + n)])
    exposed = np.clip((np.percentile(crowd, 90) - crowd) / np.ptp(np.percentile(crowd, [10, 90])), 0, 1)
    chi_sd = np.radians(B.CHI['sd'][0] + (B.CHI['sd'][1] - B.CHI['sd'][0]) * exposed)
    chi_tau = B.CHI['tau'][0] * (B.CHI['tau'][1] / B.CHI['tau'][0]) ** exposed
    chi = D.ou(mrng, times, window, (2 * n_res, 2), chi_sd[:, None], chi_tau[:, None])
    clock = SC.empty(PREFIX + 'Clock', col_rig)
    rig.bake_track(clock, np.stack([times, np.zeros(FRAMES), np.zeros(FRAMES)], 1))
    n_modes = q.shape[1]
    modes_tab = mesh.table(PREFIX + 'Modes', {f'q{j}': np.pad(q, ((0, 0), (0, -n_modes % 3)))[:, 3 * j:3 * j + 3]
                                              for j in range((n_modes + 2) // 3)}, col_rig)
    chi_tab = mesh.table(PREFIX + 'Chi', {'chi': np.pad(chi, ((0, 0), (0, 0), (0, 1))).reshape(-1, 3)}, col_rig)
    dyn_turns = groups.dynamics(PREFIX, modes_tab, FRAMES, n_modes, chi_tab, 2 * n_res, name='Dynamics')
    dyn_modes = groups.dynamics(PREFIX, modes_tab, FRAMES, n_modes, None, name='DynamicsModes')

    def moves(X, protomer, f):
        off = n_res if protomer == 'B' else 0
        turned = D.apply_chi(X, topo, chi[f, off:off + n_res, 0], chi[f, off:off + n_res, 1])
        return turned - X + shapes[protomer] @ q[f]

    # --- rig and controllers (as version 3)
    cam = bpy.data.objects.new(PREFIX + 'Camera', bpy.data.cameras.new(PREFIX + 'Camera'))
    col_rig.objects.link(cam)
    scene.camera = cam
    aim = SC.empty(PREFIX + 'Aim', col_rig)
    target = SC.empty(PREFIX + 'CutTarget', col_rig)
    slab = SC.empty(PREFIX + 'Slab', col_rig, points['pore'])
    ctl_cut = SC.empty(PREFIX + 'Ctl_Cut', col_rig)          # x funnel, y slab, z gate reveal
    ctl_look = SC.empty(PREFIX + 'Ctl_Look', col_rig)        # x pocket reveal
    ctl_bridge = SC.empty(PREFIX + 'Ctl_Bridge', col_rig)
    ctl_path = SC.empty(PREFIX + 'Ctl_Path', col_rig)        # x cavity shown, y illustrative opening
    eval_keys = [(1, 0.0), (T['twist'][0], 0.0), (T['twist'][1], 10.0 * B.TWIST_STEPS),
                 (T['network'][0], 10.0 * B.TWIST_STEPS), (T['network'][1], 10.0 * (len(snaps) - 1))]

    # --- the pathway: cavity tube (light-state free radius; illustrative opening to r1)
    r0 = np.clip(r_free, 0.0, None)
    r1 = np.maximum(r0, B.OPEN_RADIUS)
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))])
    taper = np.clip(np.minimum(arc, arc[-1] - arc) / 6.0, 0, 1) ** 0.5
    cav = mesh.points_mesh(PREFIX + 'Cavity', line, [(k, k + 1) for k in range(len(line) - 1)],
                           {'r0': ('FLOAT', r0), 'r1': ('FLOAT', r1), 'taper': ('FLOAT', taper)}, col_fx)
    cmod = cav.modifiers.new('Cavity', 'NODES')
    cmod.node_group = groups.tube(PREFIX, margin=B.CAVITY_MARGIN)
    set_modifier_inputs(cmod, {'Material': look.skin_material(PREFIX + 'Cavity', 0.22, 0.6, B.CAVITY_RGB), 'Control': ctl_path})
    cav.visible_shadow = False

    k296 = (s['resi'] == 296) & ~ret & ~np.isin(s['name'], ['N', 'C', 'O'])
    dilate = S.dilation(s, A_snaps[-1], line, ret | k296, B.DILATE, B.DILATE_MAX)

    # --- protein: cartoons per snapshot, keyed through the morph, moved by the modes
    ribbon_mat = look.ribbon_material(PREFIX + 'Ribbon')
    section_ng = groups.section(PREFIX, group='ring')     # whole cross-sections: clean cut ends
    seq_u = np.clip((s['resi'] - 50) / 300.0, 0, 1)
    shape_cols = {f'm{k}': shapes['A'][:, :, k] for k in range(n_modes)}
    ribbon_report = {}
    for name, snapset, tones, enable in (('ProtomerA', A_snaps, B.PROT_A, 1.0), ('ProtomerB', B_snaps, B.PROT_B, 0.0)):
        P = name[-1]
        per_atom = {'col': ramp(tones, seq_u), 'dilate': dilate * enable,
                    **{f'm{k}': shapes[P][:, :, k] for k in range(n_modes)}}
        frames_v = []
        for x in snapset:
            t = {**s, 'xyz': x}
            v, f, a, segs = Ct.cartoon(t, ss, per_atom=per_atom)
            frames_v.append(v)
        assert len({len(v) for v in frames_v}) == 1, 'ribbon vertex count changed between snapshots'
        attrs = {'col': a['col'], 'dilate': ('FLOAT_VECTOR', a['dilate']), 'ring': ('INT', a['ring']),
                 **{f'm{k}': ('FLOAT_VECTOR', a[f'm{k}']) for k in range(n_modes)}}
        obj = mesh.surface_mesh(PREFIX + name, frames_v[0], f, attrs, col_main)
        obj.data.materials.append(ribbon_mat)
        SC.keys(mesh.absolute_keys(obj, frames_v), 'eval_time', eval_keys)
        # Cut before the motion (as molecule() does): a cross-section near the funnel wall must not cross it and
        # pop in and out from frame to frame.
        for mod_name, ng, inputs in (('Open', groups.offset_by(PREFIX, name='Open'), {'Control': ctl_path}),
                                     ('Section', section_ng, {'Camera': cam, 'Target': target, 'Slab': slab,
                                                              'Cut': ctl_cut, 'Cut Enable': enable}),
                                     ('Motion', dyn_modes, {})):
            md = obj.modifiers.new(mod_name, 'NODES')
            md.node_group = ng
            if inputs:
                set_modifier_inputs(md, inputs)
        ribbon_report[name] = {'segments': len(segs), 'residues': int(sum(len(sg['ca']) for sg in segs)),
                               'helix': int(sum((sg['ss'] == Ct.HELIX).sum() for sg in segs)),
                               'strand': int(sum((sg['ss'] == Ct.STRAND).sum() for sg in segs)), 'vertices': len(frames_v[0])}
    del shape_cols

    # --- actors: the residues that act, in ball-and-stick, revealed on version 3's beats
    side = ~np.isin(s['name'], ['N', 'C', 'O'])
    role = np.zeros(n)
    group = np.zeros(n, int)
    for resi, grp in {**B.POCKET, **B.GATES}.items():
        sel = (s['resi'] == resi) & ~ret & side
        role[sel], group[sel] = 1, grp
    role[ret | k296] = 2
    group[ret | k296] = 0
    act = np.nonzero(role > 0)[0]
    remap = {old: k for k, old in enumerate(act)}
    act_edges = [(remap[a_], remap[b_]) for a_, b_ in edges if a_ in remap and b_ in remap]
    hi = np.tile(np.array(lin((196, 206, 220))), (n, 1))         # carbon: pale steel
    for el, rgb in B.ELEMENT.items():
        hi[s['element'] == el] = lin(rgb)
    hi[ret & (s['element'] == 'C')] = lin(B.RETINAL_C)
    vdw = St.radii(s['element'])
    # Side-chain turns on the actor mesh: the full topology's slots and weights, its axis atoms re-indexed.
    loc_idx = {old: k for k, old in enumerate(act)}
    i_axes = {k: np.array([loc_idx.get(int(i), -1) if i >= 0 else -1 for i in topo[k][act]]) for k in ('i_ca', 'i_cb', 'i_cg')}
    act_attrs = {
        'vdw': ('FLOAT', vdw[act]), 'role': ('FLOAT', role[act]), 'ball': ('FLOAT', np.ones(len(act))),
        'stick_w': ('FLOAT', np.ones(len(act))), 'dilate': ('FLOAT_VECTOR', dilate[act]),
        'g0': ('FLOAT', (group[act] == 0).astype(float)), 'g1': ('FLOAT', (group[act] == 1).astype(float)),
        'g2': ('FLOAT', (group[act] == 2).astype(float)),
        'col_ctx': ('FLOAT_COLOR', hi[act]), 'col_hi': ('FLOAT_COLOR', hi[act]),
        'emit_w': ('FLOAT', np.zeros(len(act))), 'glow_w': ('FLOAT', np.zeros(len(act))),
        **{f'm{k}': ('FLOAT_VECTOR', shapes['A'][act, :, k]) for k in range(n_modes)},
        'res_i': ('FLOAT', topo['slot'][act]), 'chi1_w': ('FLOAT', topo['chi1_w'][act]), 'chi2_w': ('FLOAT', topo['chi2_w'][act]),
        **{k: ('FLOAT', v) for k, v in i_axes.items()},
    }
    actors = mesh.points_mesh(PREFIX + 'Actors', A_snaps[0][act], act_edges, act_attrs, col_main)
    SC.keys(mesh.absolute_keys(actors, [x[act] for x in A_snaps]), 'eval_time', eval_keys)
    act_ng = groups.molecule(PREFIX, None, 0.0, 0.26, 0.15, (220, 228, 240), 0.0, name='Actors', thermal_group=dyn_turns)
    amod = actors.modifiers.new('Atoms', 'NODES')
    amod.node_group = act_ng
    atom_mat = look.attr_material(PREFIX + 'Atom', roughness=0.32, specular=0.5)
    set_modifier_inputs(amod, {'Material': atom_mat, 'Camera': cam, 'Target': target, 'Slab': slab, 'Cut': ctl_cut,
                               'Look': ctl_look, 'Cut Enable': 0.0, 'Path Control': ctl_path})

    # --- retinal's pi lobes, per snapshot: they separate at C13=C14 while it twists
    chain_idx = [S.atom_index(s, 'RET', nm) for nm in E.RETINAL_CHAIN] + [S.atom_index(s, 296, 'NZ')]
    # In stage 2 retinal is already 13-cis and the morph only carries it along; one of its snapshots bends the chain
    # by up to 0.2 A, which the lobe normals would turn into a false break of the conjugation. There the lobes
    # follow the light-state chain, superposed onto each snapshot's.
    lobes, twists = [], []
    end_chain = A_snaps[-1][chain_idx]
    for k, x in enumerate(A_snaps):
        chain = x[chain_idx]
        if k > B.TWIST_STEPS:
            R, t_ = St.kabsch(end_chain, chain)
            chain = end_chain @ R.T + t_
        up, down, _, tw = E.pi_chain_lobes(chain)
        lobes.append(np.vstack([up, down]))
        twists.append(tw)
    lobe_shapes = np.concatenate([shapes['A'][chain_idx]] * 2)
    pi = mesh.points_mesh(PREFIX + 'RetinalPi', lobes[0], None,
                          {'radius': ('FLOAT', np.full(len(lobes[0]), 0.82)),
                           **{f'm{k}': ('FLOAT_VECTOR', lobe_shapes[:, :, k]) for k in range(n_modes)}}, col_main)
    SC.keys(mesh.absolute_keys(pi, lobes), 'eval_time', eval_keys)
    pi_mat = look.skin_material(PREFIX + 'Pi', 0.2, 0.55, B.PI_RGB)
    for mod_name, ng, inputs in (('Motion', dyn_modes, {}),
                                 ('Lobes', groups.envelope(PREFIX, name='Lobes'), {'Material': pi_mat, 'Voxel': 0.12, 'Smooth': 2})):
        md = pi.modifiers.new(mod_name, 'NODES')
        md.node_group = ng
        if inputs:
            set_modifier_inputs(md, inputs)
    # Absorption (illustrative): on white, the lobes deepen in colour and opacity for a moment rather than pale.
    base = pi_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color']
    pramp = next(nd for nd in pi_mat.node_tree.nodes if nd.bl_idname == 'ShaderNodeMapRange')
    f0 = T['flash']
    for f, rgb, (lo, hi_) in ((1, B.PI_RGB, (0.2, 0.55)), (f0 - 2, B.PI_RGB, (0.2, 0.55)),
                              (f0, B.PI_EXCITED_RGB, (0.5, 0.85)), (f0 + 30, B.PI_RGB, (0.2, 0.55))):
        base.default_value = (*lin(rgb), 1)
        base.keyframe_insert('default_value', frame=f)
        for sock, v in ((pramp.inputs['To Min'], lo), (pramp.inputs['To Max'], hi_)):
            sock.default_value = v
            sock.keyframe_insert('default_value', frame=f)
    pi.visible_shadow = False

    # --- ghost of the dark-state retinal unit, for comparison after the twist
    unit = np.nonzero(ret | k296)[0]
    uremap = {old: k for k, old in enumerate(unit)}
    unit_edges = [(uremap[a_], uremap[b_]) for a_, b_ in edges if a_ in uremap and b_ in uremap]
    ghost = mesh.points_mesh(PREFIX + 'Ghost', A_snaps[0][unit], unit_edges, {
        'vdw': ('FLOAT', vdw[unit]), 'role': ('FLOAT', np.full(len(unit), 2.0)), 'g0': ('FLOAT', np.ones(len(unit))),
        'ball': ('FLOAT', np.ones(len(unit))), 'stick_w': ('FLOAT', np.ones(len(unit))),
        'dilate': ('FLOAT_VECTOR', np.zeros((len(unit), 3))), 'g1': ('FLOAT', np.zeros(len(unit))),
        'g2': ('FLOAT', np.zeros(len(unit))), 'col_ctx': ('FLOAT_COLOR', color.tile(B.GHOST_RGB, len(unit))),
        'col_hi': ('FLOAT_COLOR', color.tile(B.GHOST_RGB, len(unit))), 'emit_w': ('FLOAT', np.zeros(len(unit))),
        'glow_w': ('FLOAT', np.zeros(len(unit))), **{f'm{k}': ('FLOAT_VECTOR', shapes['A'][unit, :, k]) for k in range(n_modes)}},
        col_main)
    ghost_ng = groups.molecule(PREFIX, None, 0.0, 0.24, 0.11, (220, 228, 240), 0.0, name='Ghost', thermal_group=dyn_modes)
    gmat = look.skin_material(PREFIX + 'GhostSkin', 0.0, 0.0, B.GHOST_RGB)
    gramp = next(nd for nd in gmat.node_tree.nodes if nd.bl_idname == 'ShaderNodeMapRange')
    for sock, peak in ((gramp.inputs['To Min'], 0.35), (gramp.inputs['To Max'], 0.7)):
        for f, v in ((1, 0.0), (T['ghost'][0], 0.0), (T['ghost'][0] + 10, peak), (T['ghost'][1] - 14, peak), (T['ghost'][1], 0.0)):
            sock.default_value = v
            sock.keyframe_insert('default_value', frame=f)
    gmod = ghost.modifiers.new('Atoms', 'NODES')
    gmod.node_group = ghost_ng
    set_modifier_inputs(gmod, {'Material': gmat, 'Camera': cam, 'Target': target, 'Slab': slab, 'Cut': ctl_cut,
                               'Look': ctl_look, 'Cut Enable': 0.0})
    ghost.visible_shadow = False

    # --- salt bridge Lys132 NZ - Glu129 OE1: an amber marker, as measured in 9GO2 (2.66 A)
    i1, i2 = S.atom_index(s, 132, 'NZ'), S.atom_index(s, 129, 'OE1')
    bridge = mesh.points_mesh(PREFIX + 'SaltBridge', [A_snaps[0][i1], A_snaps[0][i2]], [(0, 1)],
                              {f'm{k}': ('FLOAT_VECTOR', shapes['A'][[i1, i2], :, k]) for k in range(n_modes)}, col_main)
    SC.keys(mesh.absolute_keys(bridge, [x[[i1, i2]] for x in A_snaps]), 'eval_time', eval_keys)
    bmod = bridge.modifiers.new('Bridge', 'NODES')
    bmod.node_group = groups.dotted_link(PREFIX, None, thermal_group=dyn_modes)
    set_modifier_inputs(bmod, {'Material': look.flat_material(PREFIX + 'Bridge', B.BRIDGE_RGB, roughness=0.4), 'Show': ctl_bridge})
    bridge.visible_shadow = False

    # --- membrane: a round patch, cut in front of SECTION_Y, lipids paling toward its rim (version 3's motion)
    R = B.MEMBRANE_RADIUS
    prot_all = np.vstack(A_snaps[::4] + B_snaps[::4])
    mem = membrane.bilayer((-R, R, B.SECTION_Y - 6.0, R), prot_all, seed=5,
                           keep=lambda p: (p[1] > B.SECTION_Y) & (np.hypot(p[0], p[1]) < R))
    head = mem['part'] == 'head'
    mcol = np.where(head[:, None], color.shade(rng, B.LIPID_HEAD, len(head)), color.shade(rng, B.LIPID_TAIL, len(head)))
    rim = np.clip((np.hypot(mem['xyz'][:, 0], mem['xyz'][:, 1]) - 0.7 * R) / (0.3 * R), 0, 1)[:, None]
    mcol = mcol * (1 - rim) + rim
    mrad = St.radii(mem['element']) * np.where(head, B.LIPID_SCALE['head'], B.LIPID_SCALE['tail'])
    handles = membrane.lipid_handles(mem, mrng, prot_all)
    lipids = mesh.points_mesh(PREFIX + 'Membrane', mem['xyz'], None, {
        'radius': ('FLOAT', mrad), 'col': ('FLOAT_COLOR', mcol),
        **{k: ('FLOAT_VECTOR' if np.ndim(v) == 2 else 'FLOAT', v) for k, v in handles.items()}}, col_mem)
    win = float(np.median(window))
    lipid_motion = {k: (v[0] * D.exposure_factor(v[1], win), max(v[1], win), *v[2:]) for k, v in B.LIPID.items()}
    mmod = lipids.modifiers.new('Lipids', 'NODES')
    mmod.node_group = groups.spheres(PREFIX, None, thermal_group=groups.lipid_motion(PREFIX, clock, lipid_motion))
    set_modifier_inputs(mmod, {'Material': look.attr_material(PREFIX + 'Lipid', roughness=0.5, specular=0.3)})

    # --- ions: bulk Na+ diffusing above and below the patch, illustrative transits through protomer A; both kept
    # clear of the moving protein's atoms (0.64 x van der Waals), as version 3 checks them
    prot_occ = membrane.occupancy(np.vstack([A_snaps[-1], B_snaps[-1]]), 9.0, voxel=2.0)
    bulk = []
    while len(bulk) < 120:
        p = np.array([rng.uniform(-R, R), rng.uniform(-R, R), rng.choice([-1, 1]) * rng.uniform(31, 100)])
        if np.hypot(p[0], p[1]) < 0.85 * R and not prot_occ(p[None])[0]:
            bulk.append(p)
    bulk = np.array(bulk)
    sgn = np.sign(bulk[:, 2])[:, None]
    lo = np.where(sgn > 0, [-R, -R, 30.0], [-R, -R, -100.0])
    hi_b = np.where(sgn > 0, [R, R, 100.0], [R, R, -30.0])
    bulk = particles.brownian(mrng, bulk, times, rate * B.ION_EXPOSURE, B.ION_D, lo, hi_b)
    dimer = np.vstack([A_snaps[-1], B_snaps[-1]])
    bulk, bulk_gap = particles.keep_clear(bulk, dimer, B.ION_RADIUS + B.ION_MARGIN, np.concatenate([vdw, vdw]) * B.PROTEIN_SCALE,
                                          moves=lambda f: np.vstack([moves(A_snaps[-1], 'A', f), moves(B_snaps[-1], 'B', f)]),
                                          drop_below=B.ION_RADIUS + B.ION_MARGIN - 0.1)
    through = particles.transits(rng, line, site_s, B.ION_ENTRIES, FRAMES, lateral=0.3)
    opened = np.array([TL.ramp(f, *T['open']) for f in range(1, FRAMES + 1)])
    through, ion_gap = particles.keep_clear(through, A_snaps[-1], B.ION_RADIUS + B.ION_MARGIN, vdw * B.PROTEIN_SCALE,
                                            offsets=dilate, weights=opened, iterations=120,
                                            moves=lambda f: moves(A_snaps[-1] + dilate * opened[f], 'A', f))
    tracks = np.concatenate([bulk, through], axis=1)
    ions = mesh.frame_tracks(PREFIX + 'Ions', tracks, {'radius': ('FLOAT', np.full(tracks.shape[1], B.ION_RADIUS))}, col_fx)
    imod = ions.modifiers.new('Ions', 'NODES')
    imod.node_group = groups.frame_spheres(PREFIX)
    set_modifier_inputs(imod, {'Material': look.flat_material(PREFIX + 'Ion', B.ION_RGB, emission=0.0, roughness=0.3)})

    # --- photons: light, the one thing that glows
    path = TL.camera_path(B.CAMERA, points, FRAMES)
    heads = []
    for k in range(48):
        f0_ = int(rng.integers(T['photons'][0], T['photons'][1]))
        d = np.array([rng.normal(scale=0.12), rng.normal(scale=0.12), -1.0])
        d /= np.linalg.norm(d)
        p0 = np.array([rng.uniform(-0.8 * R, 0.8 * R), rng.uniform(-0.6 * R, 0.9 * R), rng.uniform(150, 210)])
        size, speed = rng.uniform(30, 42), rng.uniform(7.5, 9.5)
        for f in range(f0_, FRAMES + 1):
            p = p0 + d * speed * (f - f0_)
            if p[2] < -170:
                break
            heads.append((f, p, d, size, 0.32))
    cam_hero = path[T['hero'][1] - 8][1]
    d = points['retinal'] - (points['retinal'] + 0.55 * (cam_hero - points['retinal']) / np.linalg.norm(cam_hero - points['retinal']) * 30
                             + np.array([0, 0, 22.0]))
    d /= np.linalg.norm(d)
    for f in range(T['hero'][0], T['flash'] + 1):
        u = TL.smootherstep((f - T['hero'][0]) / (T['flash'] - T['hero'][0])) * 0.3 + 0.7 * (f - T['hero'][0]) / (T['flash'] - T['hero'][0])
        heads.append((f, points['retinal'] - d * 30 * (1 - u), d, 11.0 * (1 - 0.6 * u), 0.14))
    ph = mesh.frame_tracks(PREFIX + 'Photons', np.array([h[1] for h in heads])[None], {
        'dir': ('FLOAT_VECTOR', np.array([h[2] for h in heads])[None]), 'size': ('FLOAT', np.array([h[3] for h in heads])[None]),
        'thick': ('FLOAT', np.array([h[4] for h in heads])[None])}, col_fx)
    ph.data.attributes['f'].data.foreach_set('value', np.array([h[0] for h in heads], np.float32))
    pmod = ph.modifiers.new('Photons', 'NODES')
    pmod.node_group = groups.wave_packets(PREFIX)
    set_modifier_inputs(pmod, {'Material': look.glow_material(PREFIX + 'Photon', B.PHOTON_RGB, 5.0)[0]})
    ph.visible_shadow = False

    # --- camera, cut target, controllers (version 3's keys)
    rig.bake_camera(cam, aim, path, B.APERTURE_RATIO)
    rig.bake_location(target, B.CUT_TARGET, points, FRAMES)
    SC.keys(ctl_cut, 'location', [(1, 0.0), (T['cut'][0], 0.0), (T['cut'][1], 1.0), (T['uncut'][0], 1.0), (T['uncut'][1], 0.0)], 0)
    SC.keys(ctl_cut, 'location', [(1, 0.0), (T['slab'][0], 0.0), (T['slab'][1], 1.0)], 1)
    SC.keys(ctl_cut, 'location', [(1, 0.0), (T['gates'][0], 0.0), (T['gates'][1], 1.0)], 2)
    SC.keys(ctl_look, 'location', [(1, 0.0), (T['reveal'][0], 0.0), (T['reveal'][1], 1.0)], 0)
    SC.keys(ctl_bridge, 'location', [(1, 0.0), (T['bridge'][0], 0.0), (T['bridge'][1], 1.0), (T['slab'][1], 1.0), (T['open'][1], 0.0)], 0)
    SC.keys(ctl_path, 'location', [(1, 0.0), (T['cavity'][0], 0.0), (T['cavity'][1], 1.0)], 0)
    SC.keys(ctl_path, 'location', [(1, 0.0), (T['open'][0], 0.0), (T['open'][1], 1.0)], 1)

    # --- white world, lights: blue light falls on the molecules while the photons arrive
    scene.world = look.gradient_world(PREFIX + 'World', (255, 255, 255), (255, 255, 255), B.AMBIENT_RGB, B.AMBIENT_STRENGTH)[0]
    dist0 = float(np.linalg.norm(path[0][1] - path[0][2]))
    SC.sun(PREFIX + 'Key', B.KEY_DIR, B.KEY_STRENGTH, 24, col_rig, (255, 247, 238))
    SC.sun(PREFIX + 'Fill', B.FILL_DIR, B.FILL_STRENGTH, 30, col_rig, (226, 236, 255))
    SC.sun(PREFIX + 'Rim', B.RIM_DIR, B.RIM_STRENGTH, 14, col_rig)
    blue = SC.sun(PREFIX + 'Blue', B.BLUE_DIR, 0.0, 12, col_rig, B.BLUE_RGB)
    SC.keys(blue.data, 'energy', [(1, 0.0), (T['light'][0], 0.0), (T['light'][1], B.BLUE_STRENGTH), (T['network'][1], 1.1), (FRAMES, 0.8)])
    fill = bpy.data.objects.new(PREFIX + 'FunnelFill', bpy.data.lights.new(PREFIX + 'FunnelFill', 'POINT'))
    fill.data.use_shadow, fill.data.shadow_soft_size = False, 2.0
    col_rig.objects.link(fill)
    for f, loc, aim_pt, dist, lens in path:
        fill.location = aim_pt + (loc - aim_pt) * 0.55 + np.array((0, 0, 0.12 * dist))
        fill.keyframe_insert('location', frame=f)
        fill.data.energy = 1.0 * (0.55 * dist) ** 2 * TL.ramp(f, T['cut'][0], T['cut'][1])
        fill.data.keyframe_insert('energy', frame=f)
    SC.set_linear(fill)
    SC.set_linear(fill.data)
    SC.cycles_settings(scene, RES, FRAMES, FPS, samples=B.SAMPLES, bounces=(8, 4, 4), transparent=24)
    look.bloom(scene, PREFIX + 'Bloom', threshold=1.2, strength=0.35, size=0.5)
    scene.frame_set(1)
    SC.save_scene(scene, BLEND_PATH)

    # --- labels: the web page's data (from this build's own anchors and ion tracks) and the label pass
    anchors = LD.anchors(s, A_snaps, points, through)
    web = LD.export(path, anchors, WEB_LABELS)
    label_result = labels.label_pass(B.LABEL_SCENE, B.LABEL_PREFIX, B.LABELS, path, anchors, RES, FRAMES, FPS, LABEL_BLEND)
    SC.show(scene)

    tw = np.array(twists)
    c13 = E.RETINAL_CHAIN.index('C13')
    result = {
        'blender': bpy.app.version_string, 'scene': scene.name, 'blend': str(BLEND_PATH),
        'atoms_per_protomer': n, 'bonds': len(edges), 'matched_light_atoms': int(s['matched'].sum()),
        'snapshots': len(snaps), 'morph': report,
        'dilated_residues': int(len({int(r) for r in s['resi'][np.linalg.norm(dilate, axis=1) > 0]})),
        'max_dilation_A': round(float(np.linalg.norm(dilate, axis=1).max()), 2),
        'pathway': {'length_A': round(float(arc[-1]), 1), 'sites_A': [round(v, 1) for v in site_s],
                    'min_free_radius_A': round(float(r_free.min()), 2), **pore_report},
        'ribbons': ribbon_report, 'actors': int(len(act)),
        'retinal_pi': {'c13_c14_twist_deg_max': round(float(tw[:, c13].max()), 1),
                       'c13_c14_twist_deg_start_end': [round(float(tw[0, c13]), 1), round(float(tw[-1, c13]), 1)],
                       'polyene_twist_deg_max_outside_c13': round(float(np.delete(tw[:, 2:], c13 - 2, axis=1).max()), 1)},
        'lipids': int(mem['count']), 'lipid_atoms': len(mem['xyz']), 'membrane_radius_A': R,
        'ions': {'bulk': len(bulk[0]), 'transits': len(B.ION_ENTRIES), 'min_gap_to_atom_surface_A': ion_gap, 'bulk_gap_A': bulk_gap},
        'photon_samples': len(heads), 'web_labels': {'file': str(WEB_LABELS), 'pointers': len(web['pointers'])},
        'labels': label_result, 'objects': len(scene.objects),
    }
    # Version 3's science must come out unchanged: the representation changed, not the structures or the model.
    if V3_RESULT.exists():
        v3 = json.loads(V3_RESULT.read_text())
        same = {k: v3.get(k) == json.loads(json.dumps(result[k], default=str)) for k in ('matched_light_atoms', 'snapshots', 'morph', 'dilated_residues',
                                                      'max_dilation_A', 'pathway', 'atoms_per_protomer', 'bonds')}
        result['same_as_v3'] = same
    return result


RESULT = build()
