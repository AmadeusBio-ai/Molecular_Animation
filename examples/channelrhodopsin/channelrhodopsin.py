"""Channelrhodopsin shot: light twists retinal, the protein answers, a cation pathway opens.

Scientific illustration after sources/Nobel_Med_2026.md, direction 1 ("The twist that opens a pathway"), in the
studio look: atoms as spheres, soft light, shallow depth of field, one warm accent.

Coordinates (assets/pdb):
  9GO1  C1C2 channelrhodopsin, dark state (SMX, 2.59 A). The dimer mate comes from the deposited assembly.
  9GO2  C1C2 light-activated (2.70 A): alt B (30 % occupancy) is the activated, early M390-like conformer.
Motion between the two is an illustrative constrained morph (molanim.morph), not a trajectory. The cation
pathway and ion passage at the end are an illustrative conducting-state model: 9GO2 itself is not conducting.
Thermal motion (docs/motion.md) runs on one clock, 1 s of film = 1 ns, from literature rates: normal modes and
side-chain turns for the protein, lipids moving as molecules, Na+ diffusing. Illustrative, not simulated.

Beats (24 fps): wide membrane section, photons arrive (0-4 s) -> dive into protomer A's retinal pocket (4-7 s)
-> photon absorbed, all-trans -> 13-cis with Trp262 repacking (7-10.5 s) -> Lys132 swings to Glu129 (11-14 s)
-> section through the pathway, gates, illustrative opening and cation passage (14-21 s).

Run through Blender MCP:
    import runpy
    result = runpy.run_path(r'<repo>/examples/channelrhodopsin/channelrhodopsin.py', run_name='__main__')['RESULT']
or headless:  python pipeline.py build channelrhodopsin

Rebuilds scene `Channelrhodopsin` (written to channelrhodopsin.blend next to this script) and the label scene
`Channelrhodopsin_Labels` (channelrhodopsin-labels.blend).
"""
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
from molanim import color, membrane, particles  # noqa: E402
from molanim import dynamics as D  # noqa: E402
from molanim import structure as St  # noqa: E402
from molanim import timeline as TL  # noqa: E402
from molanim.blender import groups, labels, look, mesh, rig  # noqa: E402
from molanim.blender import scene as SC  # noqa: E402
from molanim.blender.nodes import set_modifier_inputs  # noqa: E402

if 'c1c2' in sys.modules:
    import importlib
    importlib.reload(S)

SCENE_NAME, PREFIX = 'Channelrhodopsin', 'CHR_'
DARK, LIGHT = ROOT / 'assets' / 'pdb' / '9GO1.cif', ROOT / 'assets' / 'pdb' / '9GO2.cif'
BLEND_PATH = HERE / 'channelrhodopsin.blend'
FPS, FRAMES, RES = 24, 504, (1920, 1080)

# Stage: X right, Y away from the camera, Z up = extracellular. Membrane centre at Z = 0, dimer axis at X = Y = 0.
MEMBRANE_Y = 33.0          # crystal y of the bilayer centre (hydrophobic belt ~19-50, aromatic belts ~16 and ~47)
YAW_OFFSET = 0.0           # deg, turns the dimer about the normal after the retinal faces the camera
SECTION_Y = 2.0            # membrane is cut away in front of this plane (an architectural section)
MEMBRANE_BOUNDS = (-320.0, 320.0, SECTION_Y - 6.0, 480.0)

# Timeline (frames). Editorial timing, not molecular time.
T = {
    'photons': (14, 104),       # photons rain in from the extracellular side
    'light': (24, 84),          # blue light floods the scene
    'cut': (92, 150),           # cutaway funnel opens toward protomer A's retinal
    'reveal': (108, 156),       # pocket residues turn to ball-and-stick
    'hero': (154, 176),         # one photon streaks into the opened pocket
    'flash': 176,               # ... and is absorbed
    'twist': (180, 228),        # all-trans -> 13-cis (morph stage 1, with Trp262)
    'ghost': (230, 276),        # dark-state retinal shown as a ghost for comparison
    'network': (262, 318),      # protein rearrangement (stage 2: Lys132 swings to Glu129)
    'bridge': (306, 326),       # salt-bridge marker appears
    'slab': (356, 400),         # a section through the pathway sweeps in
    'uncut': (392, 420),        # the funnel closes once the camera has pulled clear
    'gates': (366, 400),        # gate residues revealed
    'cavity': (380, 404),       # pathway cavity shown (light-state profile: interrupted at the gates)
    'open': (410, 436),         # illustrative conducting-state pathway
}
ION_ENTRIES = (420, 438, 455, 472, 488)
TWIST_STEPS, NETWORK_STEPS = 12, 12

# Look (sRGB 0-255): the amadeusbio.ai website's "mist" look, so the film sits in
# the website's palette: pale blue-grey backdrop, navy and slate protein, blue-grey lipids, one amber accent.
BACKDROP_TOP, BACKDROP_BOTTOM = (247, 249, 252), (219, 227, 236)
BLUE_TOP, BLUE_BOTTOM = (198, 216, 242), (210, 220, 234)
AMBIENT_RGB, AMBIENT_STRENGTH = (224, 230, 238), 0.50
PROT_A = ((20, 50, 98), (78, 110, 156))         # protomer A: navy
PROT_A_TINT = (72, 112, 170)                     # drifts toward azure along the sequence
PROT_B = ((118, 140, 170), (176, 191, 211))      # protomer B: slate
SECTION_RGB, SECTION_TINT_MIX = (176, 200, 232), 0.45   # pale tint of atoms on cut surfaces
LIPID_HEAD = ((128, 150, 180), (172, 188, 208))
LIPID_TAIL = ((184, 197, 214), (214, 222, 232))
RETINAL_C = ((226, 136, 28), (255, 192, 84))     # the website's amber
ELEMENT = {'C': ((198, 205, 214), (236, 240, 244)), 'N': ((52, 94, 204), (96, 136, 236)),
           'O': ((208, 72, 62), (236, 112, 98)), 'S': ((226, 186, 40), (246, 214, 90))}
ION_RGB, ION_RADIUS = (74, 128, 214), 1.35
ION_MARGIN = 0.4                # extra clearance kept between ion surfaces and rendered atoms (atom motion is exact)
# Thermal motion (docs/motion.md; illustrative, from measured rates, not simulated). One clock: 1 s of film =
# CLOCK_NS ns, stopped for the picosecond twist, and each frame shows the average over EXPOSURE frames of it (as
# MD movies are window-averaged), so faster motion averages out. Molecules move as molecules: the protein by
# elastic-network normal modes plus side-chain turns about bonds; each lipid as a body that spins, wobbles, bobs
# and rattles in a flow shared with its neighbours, with bending chains and a swinging choline; Na+ by diffusion.
CLOCK_NS, EXPOSURE = 1.0, 2.0
CLOCK_HOLDS = [(T['twist'][0], T['twist'][1], 0.0, 6)]     # 'within a picosecond': nothing else moves
ANM = {'cutoff': 15.0, 'modes': 30, 'rmsf': 0.8, 'tau': 50.0}   # CA network (A; backbone springs 10x), mean CA RMSF (A), softest mode (ns)
CHI = {'sd': (8.0, 18.0), 'tau': (1.5, 0.3), 'held': (129, 132, 296)}   # deg, ns: buried -> exposed; residues held
LIPID = {'head': (0.45, 3.7), 'tail': (0.26, 0.5), 'axial': (1.0, 5.0), 'wobble': (0.17, 1.0),   # RMS rad, tau ns
         'rattle': (1.2, 0.3), 'bob': (1.0, 2.0), 'flow': (4.0, 20.0, 30.0)}                     # RMS A, tau ns, length A
ION_D, ION_EXPOSURE = 133.0, 6.0   # Na+ in water, A^2/ns (1.33e-9 m^2/s at 25 C); frames averaged (ions outrun a frame)
PHOTON_RGB, CAVITY_RGB, BRIDGE_RGB, GHOST_RGB = (70, 140, 255), (120, 185, 255), (255, 236, 170), (255, 250, 240)
PROTEIN_SCALE, BALL_SCALE, STICK_RADIUS = 0.64, 0.28, 0.16
OPEN_RADIUS, CAVITY_MARGIN = 1.3, 0.5      # illustrative open free radius; tube = free radius + margin (spheres < vdW)
DILATE, DILATE_MAX = 3.8, 3.2                # residues lining the open pathway step back to this distance (A), at most this far
LIPID_SCALE = {'head': 0.62, 'tail': 0.78}
KEY_DIR, KEY_STRENGTH, RIM_DIR, RIM_STRENGTH = (-0.55, -0.75, 0.9), 3.6, (0.6, 1.0, 0.5), 1.6
BLUE_DIR, BLUE_STRENGTH, BLUE_RGB = (0.15, -0.35, 1.0), 2.6, (90, 150, 255)
BLOOM = {'threshold': 1.0, 'strength': 0.55, 'size': 0.55}
SAMPLES = 128

# Residues shown as ball-and-stick. Group 1 = retinal pocket and network, 2 = central/inner gates.
POCKET = {262: 1, 132: 1, 129: 1}
GATES = {102: 2, 297: 2, 122: 2, 173: 2, 109: 2}
# Ion-binding sites along the pathway (residue, atom), extracellular to cytoplasmic.
SITES = [(140, 'CD'), (136, 'CD'), (129, 'CD'), (122, 'CD')]

# Camera: (frame, aim, distance A, azimuth deg from front toward +X, elevation deg, lens mm).
# Aims are named points (see build()) or (name, offset). Moves between keys ease in and out.
CAMERA = [
    (1, 'dimer_top', 330, -28, 14, 50),
    (84, 'dimer_top', 250, -10, 9, 50),
    (160, 'retinal', 44, -2, 5, 50),
    (240, 'retinal', 38, 6, 4, 50),
    (300, 'network', 40, 24, 8, 50),
    (344, 'network', 37, 30, 9, 50),
    (404, ('pore', (-26, -10, 4)), 165, 26, 5, 50),
    (504, ('pore', (-19, -6, 2)), 128, 12, 3, 50),
]
CUT_TARGET = [(1, 'retinal'), (240, 'retinal'), (300, 'network'), (350, 'network'), (392, 'pore')]
APERTURE_RATIO = 0.016          # aperture radius / focus distance

# Labels: a separate, cheap EEVEE pass (transparent PNGs) composited at encode time, so the clean picture stays
# available and typography can change without re-rendering Cycles. Positions in 1920x1080 pixels.
LABEL_SCENE, LABEL_PREFIX = 'Channelrhodopsin_Labels', 'CHRL_'
LABEL_BLEND = HERE / 'channelrhodopsin-labels.blend'
LABELS = {
    'ink': {'dark': (10, 26, 49), 'light': (248, 250, 252)},
    'halo': {'dark': (240, 244, 248), 'light': (2, 15, 38)},     # soft halo behind the ink, for legibility
    'shot_ink': [(1, 'dark'), (112, 'light'), (384, 'dark')],   # ink follows the picture: light shots, dark close-ups
    'tags_left_from': 378,      # in the pathway shot the protein sits top right: tags and timescale move to the left
    'header': (10, 104, 'NOBEL PRIZE IN PHYSIOLOGY OR MEDICINE 2026  ·  LIGHT-GATED ION CHANNELS'),
    'captions': [  # (start, end, title, subtitle)
        (14, 104, 'Channelrhodopsin C1C2', 'Light-gated cation channel (ChR1/ChR2 chimera) in a membrane'),
        (116, 182, 'Retinal, the light sensor', 'Covalently bound to Lys296 inside each protomer'),
        (190, 256, 'A photon twists retinal', 'All-trans → 13-cis about the C13=C14 bond'),
        (264, 352, 'The protein responds', 'Lys132 swings to Glu129 and forms a salt bridge'),
        (378, 414, 'The pathway is still interrupted', 'In this early light-activated state the gates stay narrow'),
        (424, 504, 'Open channel: cations cross the membrane', 'Conducting state shown as an illustrative model'),
    ],
    'tags': [  # evidence level of what is on screen (top right)
        (14, 182, 'X-RAY STRUCTURE  ·  C1C2 DARK STATE  ·  PDB 9GO1'),
        (190, 256, 'ILLUSTRATIVE MORPH  ·  9GO1 → 9GO2'),
        (264, 362, 'X-RAY STRUCTURE  ·  EARLY LIGHT-ACTIVATED STATE  ·  PDB 9GO2'),
        (378, 414, 'PATHWAY FREE-RADIUS PROFILE  ·  PDB 9GO2'),
        (424, 504, 'ILLUSTRATIVE CONDUCTING-STATE MODEL'),
    ],
    'times': [(14, 182, '1 s of film ≈ 1 ns'), (190, 256, 'within a picosecond'), (264, 352, 'microseconds'),
              (378, 414, '1 s of film ≈ 1 ns'), (424, 504, 'milliseconds')],
    'pointers': [  # (start, end, anchor, text, (dx, dy) of the text from the anchor in px)
        (30, 104, 'extracellular', 'Extracellular', None),
        (30, 104, 'cytoplasm', 'Cytoplasm', None),
        (44, 104, 'bilayer', 'Lipid bilayer', (150, -70)),
        (122, 182, 'retinal', 'Retinal', (60, -210)),
        (128, 182, 'k296', 'Lys296', (150, 110)),
        (200, 250, 'c13c14', 'C13=C14', (50, -230)),
        (236, 268, 'ghost', 'dark-state position', (-60, -190)),
        (212, 262, 'w262', 'Trp262 shifts', (-110, -170)),
        (296, 352, 'k132', 'Lys132', (150, -100)),
        (296, 352, 'e129', 'Glu129', (160, 90)),
        (376, 414, 'central_gate', 'Central gate', (190, -60)),
        (382, 414, 'inner_gate', 'Inner gate', (190, 60)),
        (434, 470, 'ion', 'Na⁺', (150, -50)),
    ],
}


def build():
    scene = SC.reset_scene(SCENE_NAME, PREFIX)
    col_main = bpy.data.collections.new(PREFIX + 'Main')
    col_mem = bpy.data.collections.new(PREFIX + 'Membrane')
    col_fx = bpy.data.collections.new(PREFIX + 'Effects')
    col_rig = bpy.data.collections.new(PREFIX + 'Rig')
    for c in (col_main, col_mem, col_fx, col_rig):
        scene.collection.children.link(c)
    rng = np.random.default_rng(3)
    lin = color.lin

    # --- structure and the activation path (crystal frame -> stage)
    s = S.states(DARK, LIGHT)
    edges = S.bonds(s)
    snaps, report = S.activation_path(s, edges, TWIST_STEPS, NETWORK_STEPS)
    Tm = S.stage_matrix(s, MEMBRANE_Y, YAW_OFFSET)
    A_snaps = [St.transform(x, Tm) for x in snaps]
    B_snaps = [St.transform(St.transform(x, s['operator']), Tm) for x in snaps]
    n = len(s['name'])
    ret = s['resn'] == 'RET'

    def at(resi, name, snap=0):
        return A_snaps[snap][S.atom_index(s, resi, name)]

    def centre(names, snap=0):
        return np.mean([at(r, a, snap) for r, a in names], axis=0)

    points = {
        'dimer_top': np.array([0.0, 0.0, 6.0]),
        'retinal': A_snaps[0][ret].mean(0),
        'network': centre([(132, 'NZ'), (129, 'CD'), ('RET', 'C15'), (262, 'CZ2')]),
        'central_gate': centre(S.GATE_ATOMS['central']),
        'inner_gate': centre(S.GATE_ATOMS['inner']),
    }
    line, r_free, site_s, pore_report = S.pathway(s, snaps[-1], Tm, SITES)
    points['pore'] = (points['central_gate'] + points['inner_gate']) / 2

    # --- per-atom styling (both protomers share topology)
    role = np.zeros(n)
    group = np.zeros(n, int)
    side = ~np.isin(s['name'], ['N', 'C', 'O'])
    for resi, grp in {**POCKET, **GATES}.items():
        sel = (s['resi'] == resi) & ~ret & side
        role[sel], group[sel] = 1, grp
    k296 = (s['resi'] == 296) & ~ret & side
    role[ret | k296] = 2
    group[ret | k296] = 0
    vdw = St.radii(s['element'])
    seq = np.clip((s['resi'] - 50) / 300.0, 0, 1)[:, None]
    ctx_a = color.shade(rng, PROT_A, n, 0.15, 1.0)
    ctx_a = ctx_a * (1 - 0.45 * seq) + np.array(lin(PROT_A_TINT)) * 0.45 * seq
    ctx_b = color.shade(rng, PROT_B, n, 0.15, 1.0)
    hi = np.zeros((n, 3))
    for el, ramp_ in ELEMENT.items():
        sel = s['element'] == el
        hi[sel] = color.shade(rng, ramp_, sel.sum(), 0.3, 1.0)
    ret_c = ret & (s['element'] == 'C')
    hi[ret_c] = color.shade(rng, RETINAL_C, ret_c.sum(), 0.4, 1.0)
    emit_w = np.where(ret, 0.6, 0.0)
    glow_w = np.where(ret & np.isin(s['name'], ['C13', 'C14']), 6.0, 0.0)
    gw = {f'g{k}': (group == k).astype(float) * (role > 0) for k in (0, 1, 2)}
    ball = np.where(group == 2, PROTEIN_SCALE / BALL_SCALE, 1.0)       # gates: full spheres, element colours
    stick_w = np.where(group == 2, 0.0, 1.0)
    # --- thermal motion (docs/motion.md): the clock, the dimer's normal modes, side-chain turns. numpy knows every
    # atom's displacement on every frame (moves()), so ion clearance is checked against the moving protein.
    mrng = np.random.default_rng(41)
    times, rate = D.clock(FRAMES, CLOCK_NS / FPS, CLOCK_HOLDS)
    window = rate * EXPOSURE
    nodes, node_of = D.residue_nodes(s['resi'], s['name'])
    node_of[ret] = node_of[S.atom_index(s, 296, 'CA')]                 # retinal rides on Lys296
    m = len(nodes)
    links = D.sequence_pairs(A_snaps[0], nodes)
    eig, vec = D.anm(np.vstack([A_snaps[0][nodes], B_snaps[0][nodes]]), ANM['cutoff'], modes=ANM['modes'],
                     bonded=links + [(i + m, j + m) for i, j in links])
    mode_scale = D.mode_scale(eig, vec, ANM['rmsf'])
    q = D.mode_amplitudes(mrng, eig, times, window, mode_scale, ANM['tau'])
    unit_mask = ret | (s['resi'] == 296)                                # retinal and Lys296 move as one, unblended
    shapes = {'A': D.atom_shapes(A_snaps[0], vec[:m], nodes, node_of, links, unit_mask),     # (atoms, 3, modes)
              'B': D.atom_shapes(B_snaps[0], vec[m:], nodes, node_of, links, unit_mask)}
    topo = D.chi_topology(s['resn'], s['resi'], s['name'])
    n_res = topo['residues']
    held = np.isin(s['resi'], CHI['held']) | ret
    for k in ('chi1_w', 'chi2_w'):
        topo[k] = np.where(held, 0.0, topo[k])
    probe = []                                                         # burial probe per residue: CB, else CA, else its first atom
    for r in range(n_res):
        idx = np.nonzero(topo['slot'] == r)[0]
        probe.append(next((i for nm in ('CB', 'CA') for i in idx if s['name'][i] == nm), idx[0]))
    probe = np.array(probe)
    both = np.vstack([A_snaps[0], B_snaps[0]])
    crowd = np.concatenate([D.burial(both, probe), D.burial(both, probe + n)])
    exposed = np.clip((np.percentile(crowd, 90) - crowd) / np.ptp(np.percentile(crowd, [10, 90])), 0, 1)
    chi_sd = np.radians(CHI['sd'][0] + (CHI['sd'][1] - CHI['sd'][0]) * exposed)
    chi_tau = CHI['tau'][0] * (CHI['tau'][1] / CHI['tau'][0]) ** exposed
    chi = D.ou(mrng, times, window, (2 * n_res, 2), chi_sd[:, None], chi_tau[:, None])        # (frames, residues, 2)
    clock = SC.empty(PREFIX + 'Clock', col_rig)                       # x = molecular time (ns), read by the lipids
    rig.bake_track(clock, np.stack([times, np.zeros(FRAMES), np.zeros(FRAMES)], 1))
    modes_tab = mesh.table(PREFIX + 'Modes', {f'q{j}': np.pad(q, ((0, 0), (0, -q.shape[1] % 3)))[:, 3 * j:3 * j + 3]
                                              for j in range((q.shape[1] + 2) // 3)}, col_rig)
    chi_tab = mesh.table(PREFIX + 'Chi', {'chi': np.pad(chi, ((0, 0), (0, 0), (0, 1))).reshape(-1, 3)}, col_rig)
    dyn = groups.dynamics(PREFIX, modes_tab, FRAMES, q.shape[1], chi_tab, 2 * n_res)

    def dyn_attrs(protomer, idx, turns=True):
        out = {f'm{k}': ('FLOAT_VECTOR', shapes[protomer][idx, :, k]) for k in range(q.shape[1])}
        if turns:
            out['res_i'] = ('FLOAT', topo['slot'][idx] + (n_res if protomer == 'B' else 0))
            out.update({k: ('FLOAT', topo[k][idx]) for k in ('chi1_w', 'chi2_w', 'i_ca', 'i_cb', 'i_cg')})
        return out

    def moves(X, protomer, f):
        """Displacement of a protomer's atoms (rest positions X) on frame index f, as the geometry nodes apply it."""
        off = n_res if protomer == 'B' else 0
        turned = D.apply_chi(X, topo, chi[f, off:off + n_res, 0], chi[f, off:off + n_res, 1])
        return turned - X + shapes[protomer] @ q[f]

    protein_ng = groups.molecule(PREFIX, None, PROTEIN_SCALE, BALL_SCALE, STICK_RADIUS, SECTION_RGB, SECTION_TINT_MIX,
                                 thermal_group=dyn)
    atom_mat = look.attr_material(PREFIX + 'Atom', roughness=0.42, specular=0.45, sheen=0.15)

    # --- rig: camera, aim, cut target, slab, controllers
    cam = bpy.data.objects.new(PREFIX + 'Camera', bpy.data.cameras.new(PREFIX + 'Camera'))
    col_rig.objects.link(cam)
    scene.camera = cam
    aim = SC.empty(PREFIX + 'Aim', col_rig)
    target = SC.empty(PREFIX + 'CutTarget', col_rig)
    slab = SC.empty(PREFIX + 'Slab', col_rig, points['pore'])
    ctl_cut = SC.empty(PREFIX + 'Ctl_Cut', col_rig)          # x funnel, y slab, z gate reveal
    ctl_look = SC.empty(PREFIX + 'Ctl_Look', col_rig)        # x pocket reveal, y retinal glow, z C13=C14 glow
    ctl_bridge = SC.empty(PREFIX + 'Ctl_Bridge', col_rig)    # x salt-bridge marker
    ctl_path = SC.empty(PREFIX + 'Ctl_Path', col_rig)        # x cavity shown, y illustrative opening

    # --- cation pathway: cavity tube (light-state free radius; illustrative opening to r1)
    r0 = np.clip(r_free, 0.0, None)
    r1 = np.maximum(r0, OPEN_RADIUS)
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))])
    taper = np.clip(np.minimum(arc, arc[-1] - arc) / 6.0, 0, 1) ** 0.5
    cav = mesh.points_mesh(PREFIX + 'Cavity', line, [(k, k + 1) for k in range(len(line) - 1)],
                           {'r0': ('FLOAT', r0), 'r1': ('FLOAT', r1), 'taper': ('FLOAT', taper)}, col_fx)
    cmod = cav.modifiers.new('Cavity', 'NODES')
    cmod.node_group = groups.tube(PREFIX, margin=CAVITY_MARGIN)
    cav_mat, cav_em = look.glow_material(PREFIX + 'Cavity', CAVITY_RGB, 1.1, rim=True)
    set_modifier_inputs(cmod, {'Material': cav_mat, 'Control': ctl_path})
    cav.visible_shadow = False

    dilate = S.dilation(s, A_snaps[-1], line, ret | k296, DILATE, DILATE_MAX)
    eval_keys = [(1, 0.0), (T['twist'][0], 0.0), (T['twist'][1], 10.0 * TWIST_STEPS),
                 (T['network'][0], 10.0 * TWIST_STEPS), (T['network'][1], 10.0 * (len(snaps) - 1))]
    for name, snapset, ctx, enable in (('ProtomerA', A_snaps, ctx_a, 1.0), ('ProtomerB', B_snaps, ctx_b, 0.0)):
        # Only the hero protomer A is opened up and annotated; B stays a plain sphere model.
        attrs = {'vdw': ('FLOAT', vdw), 'role': ('FLOAT', role * enable), 'ball': ('FLOAT', ball), 'stick_w': ('FLOAT', stick_w),
                 'dilate': ('FLOAT_VECTOR', dilate * enable),
                 **{k: ('FLOAT', v * enable) for k, v in gw.items()},
                 'col_ctx': ('FLOAT_COLOR', ctx), 'col_hi': ('FLOAT_COLOR', hi if enable else ctx),
                 'emit_w': ('FLOAT', emit_w * enable), 'glow_w': ('FLOAT', glow_w * enable), **dyn_attrs(name[-1], np.arange(n))}
        obj = mesh.points_mesh(PREFIX + name, snapset[0], edges, attrs, col_main)
        SC.keys(mesh.absolute_keys(obj, snapset), 'eval_time', eval_keys)
        mod = obj.modifiers.new('Atoms', 'NODES')
        mod.node_group = protein_ng
        set_modifier_inputs(mod, {'Material': atom_mat, 'Camera': cam, 'Target': target, 'Slab': slab, 'Cut': ctl_cut,
                                  'Look': ctl_look, 'Cut Enable': enable, 'Path Control': ctl_path})

    # --- ghost of the dark-state retinal unit (for comparison after the twist)
    unit = np.nonzero(ret | k296)[0]
    remap = {old: k for k, old in enumerate(unit)}
    unit_edges = [(remap[a], remap[b]) for a, b in edges if a in remap and b in remap]
    ghost = mesh.points_mesh(PREFIX + 'Ghost', A_snaps[0][unit], unit_edges, {
        'vdw': ('FLOAT', vdw[unit]), 'role': ('FLOAT', np.full(len(unit), 2.0)), 'g0': ('FLOAT', np.ones(len(unit))),
        'ball': ('FLOAT', np.ones(len(unit))), 'stick_w': ('FLOAT', np.ones(len(unit))), 'dilate': ('FLOAT_VECTOR', np.zeros((len(unit), 3))),
        'g1': ('FLOAT', np.zeros(len(unit))), 'g2': ('FLOAT', np.zeros(len(unit))),
        'col_ctx': ('FLOAT_COLOR', color.tile(GHOST_RGB, len(unit))), 'col_hi': ('FLOAT_COLOR', color.tile(GHOST_RGB, len(unit))),
        'emit_w': ('FLOAT', np.zeros(len(unit))), 'glow_w': ('FLOAT', np.zeros(len(unit))),
        **dyn_attrs('A', unit, turns=False)}, col_main)
    gmat, galpha = look.ghost_material(PREFIX + 'Ghost', GHOST_RGB)
    gmod = ghost.modifiers.new('Atoms', 'NODES')
    gmod.node_group = protein_ng
    set_modifier_inputs(gmod, {'Material': gmat, 'Camera': cam, 'Target': target, 'Slab': slab, 'Cut': ctl_cut,
                               'Look': ctl_look, 'Cut Enable': 0.0, 'Ball': 0.24, 'Stick': 0.11})
    SC.keys(galpha, 'default_value', [(1, 0.0), (T['ghost'][0], 0.0), (T['ghost'][0] + 10, 0.26), (T['ghost'][1] - 14, 0.26),
                                      (T['ghost'][1], 0.0)])
    ghost.visible_shadow = False

    # --- salt-bridge marker (follows Lys132 NZ and Glu129 OE1 through the same snapshots)
    i1, i2 = S.atom_index(s, 132, 'NZ'), S.atom_index(s, 129, 'OE1')
    bridge = mesh.points_mesh(PREFIX + 'SaltBridge', [A_snaps[0][i1], A_snaps[0][i2]], [(0, 1)],
                              dyn_attrs('A', np.array([i1, i2]), turns=False), col_main)
    SC.keys(mesh.absolute_keys(bridge, [x[[i1, i2]] for x in A_snaps]), 'eval_time', eval_keys)
    bmod = bridge.modifiers.new('Bridge', 'NODES')
    bmod.node_group = groups.dotted_link(PREFIX, None, thermal_group=dyn)
    set_modifier_inputs(bmod, {'Material': look.glow_material(PREFIX + 'Bridge', BRIDGE_RGB, 6.0)[0], 'Show': ctl_bridge})
    bridge.visible_shadow = False

    # --- membrane (section in front of SECTION_Y), excluding both protomers in both states
    prot_all = np.vstack(A_snaps[::4] + B_snaps[::4])
    mem = membrane.bilayer(MEMBRANE_BOUNDS, prot_all, seed=5, keep=lambda p: p[1] > SECTION_Y)
    head = mem['part'] == 'head'
    mcol = np.where(head[:, None], color.shade(rng, LIPID_HEAD, len(head)), color.shade(rng, LIPID_TAIL, len(head)))
    mrad = St.radii(mem['element']) * np.where(head, LIPID_SCALE['head'], LIPID_SCALE['tail'])
    handles = membrane.lipid_handles(mem, mrng, prot_all)
    lipids = mesh.points_mesh(PREFIX + 'Membrane', mem['xyz'], None, {
        'radius': ('FLOAT', mrad), 'col': ('FLOAT_COLOR', mcol),
        **{k: ('FLOAT_VECTOR' if np.ndim(v) == 2 else 'FLOAT', v) for k, v in handles.items()}}, col_mem)
    # Each frame shows the exposure average: processes faster than the window fade (and are no faster than it).
    win = float(np.median(window))
    lipid_motion = {k: (v[0] * D.exposure_factor(v[1], win), max(v[1], win), *v[2:]) for k, v in LIPID.items()}
    mmod = lipids.modifiers.new('Lipids', 'NODES')
    mmod.node_group = groups.spheres(PREFIX, None, thermal_group=groups.lipid_motion(PREFIX, clock, lipid_motion))
    set_modifier_inputs(mmod, {'Material': look.attr_material(PREFIX + 'Lipid', roughness=0.5, specular=0.3, sheen=0.1)})

    # --- ions: sparse bulk cations diffusing in the water on either side, plus illustrative transits through
    # protomer A. Both keep clear of the moving protein (exact positions from moves()).
    prot_occ = membrane.occupancy(np.vstack([A_snaps[-1], B_snaps[-1]]), 9.0, voxel=2.0)
    bulk = []
    while len(bulk) < 180:
        p = np.array([rng.uniform(-190, 190), rng.uniform(-130, 300), rng.choice([-1, 1]) * rng.uniform(31, 125)])
        if not prot_occ(p[None])[0]:
            bulk.append(p)
    bulk = np.array(bulk)
    side = np.sign(bulk[:, 2])[:, None]
    lo = np.where(side > 0, [-190.0, -130.0, 30.0], [-190.0, -130.0, -125.0])
    hi = np.where(side > 0, [190.0, 300.0, 125.0], [190.0, 300.0, -30.0])
    bulk = particles.brownian(mrng, bulk, times, rate * ION_EXPOSURE, ION_D, lo, hi)
    dimer = np.vstack([A_snaps[-1], B_snaps[-1]])
    bulk, bulk_gap = particles.keep_clear(bulk, dimer, ION_RADIUS + ION_MARGIN, np.concatenate([vdw, vdw]) * PROTEIN_SCALE,
                                          moves=lambda f: np.vstack([moves(A_snaps[-1], 'A', f), moves(B_snaps[-1], 'B', f)]))
    through = particles.transits(rng, line, site_s, ION_ENTRIES, FRAMES, lateral=0.3)
    opened = np.array([TL.ramp(f, *T['open']) for f in range(1, FRAMES + 1)])
    through, ion_gap = particles.keep_clear(through, A_snaps[-1], ION_RADIUS + ION_MARGIN, vdw * PROTEIN_SCALE,
                                            offsets=dilate, weights=opened,
                                            moves=lambda f: moves(A_snaps[-1] + dilate * opened[f], 'A', f))
    tracks = np.concatenate([bulk, through], axis=1)
    ions = mesh.frame_tracks(PREFIX + 'Ions', tracks, {'radius': ('FLOAT', np.full(tracks.shape[1], ION_RADIUS))}, col_fx)
    imod = ions.modifiers.new('Ions', 'NODES')
    imod.node_group = groups.frame_spheres(PREFIX)
    set_modifier_inputs(imod, {'Material': look.flat_material(PREFIX + 'Ion', ION_RGB, emission=0.35, roughness=0.3)})

    # --- photons: wave packets raining in from the extracellular side, then one into the open pocket
    path = TL.camera_path(CAMERA, points, FRAMES)
    heads = []
    for k in range(64):
        f0 = int(rng.integers(T['photons'][0], T['photons'][1]))
        d = np.array([rng.normal(scale=0.12), rng.normal(scale=0.12), -1.0])
        d /= np.linalg.norm(d)
        p0 = np.array([rng.uniform(-170, 170), rng.uniform(-120, 200), rng.uniform(150, 210)])
        size, speed = rng.uniform(30, 42), rng.uniform(7.5, 9.5)
        for f in range(f0, FRAMES + 1):
            p = p0 + d * speed * (f - f0)
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
    set_modifier_inputs(pmod, {'Material': look.glow_material(PREFIX + 'Photon', PHOTON_RGB, 5.0)[0]})
    ph.visible_shadow = False

    # --- camera animation (baked per frame), depth of field on the aim; the cutaway follows its own target
    rig.bake_camera(cam, aim, path, APERTURE_RATIO)
    rig.bake_location(target, CUT_TARGET, points, FRAMES)

    # --- controllers
    SC.keys(ctl_cut, 'location', [(1, 0.0), (T['cut'][0], 0.0), (T['cut'][1], 1.0), (T['uncut'][0], 1.0), (T['uncut'][1], 0.0)], 0)
    SC.keys(ctl_cut, 'location', [(1, 0.0), (T['slab'][0], 0.0), (T['slab'][1], 1.0)], 1)
    SC.keys(ctl_cut, 'location', [(1, 0.0), (T['gates'][0], 0.0), (T['gates'][1], 1.0)], 2)
    SC.keys(ctl_look, 'location', [(1, 0.0), (T['reveal'][0], 0.0), (T['reveal'][1], 1.0)], 0)
    f0 = T['flash']
    SC.keys(ctl_look, 'location', [(1, 0.15), (f0 - 6, 0.15), (f0, 2.6), (f0 + 18, 0.7), (T['network'][1], 0.35)], 1)
    SC.keys(ctl_look, 'location', [(1, 0.0), (f0 + 2, 0.0), (f0 + 8, 1.0), (T['twist'][1], 0.6), (T['twist'][1] + 30, 0.0)], 2)
    SC.keys(ctl_bridge, 'location', [(1, 0.0), (T['bridge'][0], 0.0), (T['bridge'][1], 1.0), (T['slab'][1], 1.0), (T['open'][1], 0.0)], 0)
    SC.keys(ctl_path, 'location', [(1, 0.0), (T['cavity'][0], 0.0), (T['cavity'][1], 1.0)], 0)
    SC.keys(ctl_path, 'location', [(1, 0.0), (T['open'][0], 0.0), (T['open'][1], 1.0)], 1)

    # --- lights and world
    world, wb, wt = look.gradient_world(PREFIX + 'World', BACKDROP_TOP, BACKDROP_BOTTOM, AMBIENT_RGB, AMBIENT_STRENGTH)
    scene.world = world
    for sock, base, blue in ((wt, BACKDROP_TOP, BLUE_TOP), (wb, BACKDROP_BOTTOM, BLUE_BOTTOM)):
        for f, mixv in ((1, 0.0), (T['light'][0], 0.0), (T['light'][1], 1.0), (T['network'][1], 0.55), (FRAMES, 0.4)):
            c = np.array(lin(base)) * (1 - mixv) + np.array(lin(blue)) * mixv
            sock.default_value = (*c, 1)
            sock.keyframe_insert('default_value', frame=f)
    SC.sun(PREFIX + 'Key', KEY_DIR, KEY_STRENGTH, 28, col_rig)
    SC.sun(PREFIX + 'Rim', RIM_DIR, RIM_STRENGTH, 18, col_rig)
    blue = SC.sun(PREFIX + 'Blue', BLUE_DIR, 0.0, 12, col_rig, BLUE_RGB)
    SC.keys(blue.data, 'energy', [(1, 0.0), (T['light'][0], 0.0), (T['light'][1], BLUE_STRENGTH), (T['network'][1], 1.4), (FRAMES, 1.0)])
    # Fill along the funnel: a shadowless point light between camera and target, scaled with distance^2.
    fill = bpy.data.objects.new(PREFIX + 'Fill', bpy.data.lights.new(PREFIX + 'Fill', 'POINT'))
    fill.data.use_shadow, fill.data.shadow_soft_size = False, 2.0
    col_rig.objects.link(fill)
    for f, loc, aim_pt, dist, lens in path:
        fill.location = aim_pt + (loc - aim_pt) * 0.55 + np.array((0, 0, 0.12 * dist))
        fill.keyframe_insert('location', frame=f)
        fill.data.energy = 1.4 * (0.55 * dist) ** 2 * TL.ramp(f, T['cut'][0], T['cut'][1])
        fill.data.keyframe_insert('energy', frame=f)
    SC.set_linear(fill)
    SC.set_linear(fill.data)
    # The retinal's own flash: a small blue-white point light at the chromophore.
    flash = bpy.data.objects.new(PREFIX + 'Flash', bpy.data.lights.new(PREFIX + 'Flash', 'POINT'))
    flash.location = points['retinal']
    flash.data.color, flash.data.shadow_soft_size = lin((150, 190, 255)), 1.0
    col_rig.objects.link(flash)
    SC.keys(flash.data, 'energy', [(1, 0.0), (f0 - 4, 0.0), (f0, 900.0), (f0 + 14, 120.0), (f0 + 40, 0.0)])

    # --- render settings
    SC.cycles_settings(scene, RES, FRAMES, FPS, samples=SAMPLES)
    look.bloom(scene, PREFIX + 'Bloom', **BLOOM)
    scene.frame_set(1)
    SC.save_scene(scene, BLEND_PATH)

    # --- labels (separate scene and file)
    ring_atoms = [S.atom_index(s, 262, n) for n in ('CD2', 'CE2', 'CE3', 'CZ2', 'CZ3', 'CH2')]
    anchors = {
        'extracellular': np.array([-62.0, 30.0, 40.0]), 'cytoplasm': np.array([-62.0, 30.0, -31.0]),
        'bilayer': np.array([58.0, SECTION_Y + 4, 4.0]),
        'retinal': points['retinal'], 'k296': at(296, 'NZ'),
        'c13c14': (at('RET', 'C13', TWIST_STEPS) + at('RET', 'C14', TWIST_STEPS)) / 2,
        'ghost': at('RET', 'C10'),
        'w262': A_snaps[-1][ring_atoms].mean(0), 'k132': at(132, 'NZ', -1), 'e129': at(129, 'OE1', -1),
        'central_gate': points['central_gate'], 'inner_gate': points['inner_gate'],
        'ion': through[:, 0],
    }
    label_result = labels.label_pass(LABEL_SCENE, LABEL_PREFIX, LABELS, path, anchors, RES, FRAMES, FPS, LABEL_BLEND)
    SC.show(scene)

    # --- what the thermal motion does, measured on the rest structure (every 6th frame)
    edges_a = np.asarray(edges)
    bond0 = np.linalg.norm(A_snaps[0][edges_a[:, 0]] - A_snaps[0][edges_a[:, 1]], axis=1)
    disp, bond_dev = [], 0.0
    for f in range(0, FRAMES, 6):
        X = A_snaps[0] + moves(A_snaps[0], 'A', f)
        disp.append(X - A_snaps[0])
        bond_dev = max(bond_dev, float(np.abs(np.linalg.norm(X[edges_a[:, 0]] - X[edges_a[:, 1]], axis=1) - bond0).max()))
    disp = np.array(disp)
    rmsf = np.sqrt(((disp - disp.mean(0)) ** 2).sum(2).mean(0))
    backbone = np.isin(s['name'], ['N', 'CA', 'C', 'O'])
    motion_report = {
        'clock_ns_per_s': CLOCK_NS, 'film_ns': round(float(times[-1]), 2), 'exposure_frames': EXPOSURE,
        'anm': {'modes': len(eig), 'eig_ratio_last_first': round(float(eig[-1] / eig[0]), 1),
                'ca_rmsf_equilibrium_A': round(float(np.sqrt((D.node_rmsf(eig, vec, mode_scale) ** 2).mean())), 2),
                'tau_ns_softest_stiffest': [ANM['tau'], round(ANM['tau'] * float(eig[0] / eig[-1]), 2)]},
        'chi_sd_deg': [round(float(np.degrees(v)), 1) for v in np.percentile(chi_sd, [0, 50, 100])],
        'film_rmsf_A': {'backbone_median': round(float(np.median(rmsf[backbone])), 2),
                        'side_chain_median': round(float(np.median(rmsf[~backbone & ~ret])), 2),
                        'side_chain_p95': round(float(np.percentile(rmsf[~backbone & ~ret], 95)), 2),
                        'retinal_median': round(float(np.median(rmsf[ret])), 2)},
        'max_bond_change_A': round(bond_dev, 3),
        'lipids': {k: [round(float(x), 3) for x in v] for k, v in lipid_motion.items()},
        'lipid_mobility_min_mean': [round(float(handles['mobility'].min()), 2), round(float(handles['mobility'].mean()), 3)],
    }

    return {
        'dilated_residues': int(len({int(r) for r in s['resi'][np.linalg.norm(dilate, axis=1) > 0]})),
        'max_dilation_A': round(float(np.linalg.norm(dilate, axis=1).max()), 2),
        'blender': bpy.app.version_string,
        'scene': scene.name,
        'atoms_per_protomer': n, 'bonds': len(edges), 'matched_light_atoms': int(s['matched'].sum()),
        'snapshots': len(snaps), 'morph': report,
        'lipids': int(mem['count']), 'lipid_atoms': len(mem['xyz']),
        'pathway': {'length_A': round(float(arc[-1]), 1), 'sites_A': [round(v, 1) for v in site_s],
                    'min_free_radius_A': round(float(r_free.min()), 2), **pore_report},
        'ions': {'bulk': 180, 'transits': len(ION_ENTRIES), 'min_gap_to_atom_surface_A': ion_gap, 'bulk_gap_A': bulk_gap,
                 'bulk_step_A': [round(float(v), 2) for v in np.percentile(np.linalg.norm(np.diff(bulk, axis=0), axis=2), [50, 95, 100])]},
        'motion': motion_report,
        'photon_samples': len(heads),
        'points': {k: [round(float(c), 1) for c in v] for k, v in points.items()},
        'objects': len(scene.objects),
        'blend': str(BLEND_PATH), 'labels': label_result,
    }


RESULT = build()
