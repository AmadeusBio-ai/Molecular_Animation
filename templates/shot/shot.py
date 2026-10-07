"""__TITLE__: a studio shot of PDB __PDB__, scaffolded by `python pipeline.py new __NAME__`.

This is a starting point. The constants at the top are the storyboard (timeline, camera, look, labels); change
them, and add what the brief needs from molanim (morphs between states, pathways, membranes, particles; see
docs/framework.md and the case study in examples/channelrhodopsin/).

The default film establishes the molecule, dives through a camera-aimed cutaway to the highlighted residues
(by default the largest ligand) and holds on them with a label. With LOOP = True it is a seamless orbit instead.

Evidence: the coordinates are the deposited experimental model; the breathing motion is illustrative. The
on-screen tag says so. Give everything you add an evidence level (docs/principles.md).

Run:  python pipeline.py build __NAME__        or, in Blender through MCP:
    import runpy; runpy.run_path(r'<repo>/projects/__NAME__/__SCRIPT__.py', run_name='__main__')['RESULT']
"""
import math
import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT)]
import molanim  # noqa: E402

molanim.reload()
from molanim import color  # noqa: E402
from molanim import structure as St  # noqa: E402
from molanim import timeline as TL  # noqa: E402
from molanim.blender import groups, labels, look, mesh, rig  # noqa: E402
from molanim.blender import scene as SC  # noqa: E402
from molanim.blender.nodes import set_modifier_inputs  # noqa: E402

NAME, SCENE_NAME, PREFIX = '__NAME__', '__SCENE__', '__PREFIX__'
PDB_ID = '__PDB__'
PDB = ROOT / 'assets' / 'pdb' / f'{PDB_ID}.cif'
BLEND_PATH = HERE / f'{NAME}.blend'
LABEL_BLEND = HERE / f'{NAME}-labels.blend'
FPS, FRAMES, RES = __FPS__, __FRAMES__, (1920, 1080)
LOOP = __LOOP__                  # True: seamless orbit (frame FRAMES + 1 = frame 1); False: narrative dive
SAMPLES = 128

# Structure.
CHAINS = __CHAINS__              # chains to include, e.g. ['A', 'B']; None = every chain
HIGHLIGHT = __HIGHLIGHT__        # featured residues: names ('RET'), numbers (296) or 'A:296'; None = the largest ligand
POCKET_RADIUS = 4.5              # side chains within this distance (A) of the highlight join it as ball-and-stick

# Timeline as fractions of the film (editorial time, not molecular time).
BEATS = {
    'establish': (0.0, 0.30),    # the whole molecule, slow drift
    'dive': (0.30, 0.62),        # camera moves in on the highlight
    'cut': (0.34, 0.58),         # cutaway funnel opens toward the highlight
    'reveal': (0.45, 0.66),      # pocket side chains turn to ball-and-stick
    'glow': (0.62, 0.74),        # the highlight brightens briefly
}
# Camera keys: (time 0-1, aim, distance, azimuth deg, elevation deg, lens mm). Aims: 'centre' or 'focus' (the
# highlight). Distance in A, or 'fit' (whole molecule in frame) or ('fit', k) for k x fit.
CAMERA = [
    (0.0, 'centre', 'fit', -24, 12, 50),
    (0.30, 'centre', ('fit', 0.88), -10, 8, 50),
    (0.62, 'focus', 40, -2, 5, 50),
    (1.0, 'focus', 36, 10, 6, 50),
]
ORBIT = {'distance': ('fit', 0.95), 'elevation': 10, 'lens': 50, 'azimuth0': -20, 'turns': 1.0}   # LOOP = True
APERTURE_RATIO = 0.016           # aperture radius / focus distance: shallow, but the highlight stays sharp

# Look (sRGB 0-255): muted chains, one warm accent on the highlight, element colours only where it matters.
BACKDROP_TOP, BACKDROP_BOTTOM = (228, 232, 235), (204, 209, 214)
AMBIENT_RGB, AMBIENT_STRENGTH = (215, 218, 222), 0.45
CHAIN_TONES = [((48, 124, 128), (112, 182, 174)), ((96, 118, 140), (156, 174, 192)), ((110, 128, 96), (170, 186, 150)),
               ((140, 120, 104), (198, 180, 160)), ((112, 104, 140), (176, 168, 200))]
ACCENT_C = ((236, 140, 24), (255, 186, 70))       # carbons of the highlight
ELEMENT = {'C': ((196, 198, 196), (232, 232, 228)), 'N': ((52, 92, 220), (92, 132, 245)),
           'O': ((214, 52, 44), (240, 92, 80)), 'S': ((226, 186, 40), (246, 214, 90)), 'P': ((236, 150, 60), (250, 180, 90))}
SECTION_RGB, SECTION_MIX = (176, 220, 212), 0.45
PROTEIN_SCALE, BALL_SCALE, STICK_RADIUS = 0.64, 0.28, 0.16
BREATH = {'sway': 0.35, 'sway_size': 30.0, 'jitter': 0.12, 'jitter_size': 5.0}
KEY_DIR, KEY_STRENGTH, RIM_DIR, RIM_STRENGTH = (-0.55, -0.75, 0.9), 3.6, (0.6, 1.0, 0.5), 1.6
BLOOM = {'threshold': 1.0, 'strength': 0.45, 'size': 0.55}

# Labels (a separate pass; pipeline.py deliver makes labelled and clean films). None = generated from the entry.
LABELS_ON = True
TITLE = '__TITLE__'
SUBTITLE = None                  # default: the PDB entry's title
FOCUS_TEXT = None                # default: the highlighted residue names
INK = {'dark': (30, 42, 52), 'light': (248, 250, 252)}
HALO = {'dark': (236, 240, 244), 'light': (8, 20, 28)}

STANDARD = {'ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'GLY', 'HIS', 'ILE', 'LEU', 'LYS', 'MET', 'PHE', 'PRO',
            'SER', 'THR', 'TRP', 'TYR', 'VAL', 'MSE', 'SEC', 'PYL', 'DA', 'DC', 'DG', 'DT', 'A', 'C', 'G', 'U'}


def beat(name):
    a, b = BEATS[name]
    return 1 + round(a * (FRAMES - 1)), 1 + round(b * (FRAMES - 1))


def pick_highlight(t):
    """Boolean mask of the featured residues."""
    residue = list(zip(t['chain'], t['resi'], t['resn']))
    if HIGHLIGHT is None:                       # the largest non-standard residue (ligand, chromophore, cofactor)
        sizes = {}
        for r in residue:
            if r[2] not in STANDARD | St.IONS:
                sizes[r] = sizes.get(r, 0) + 1
        if not sizes:
            return np.zeros(len(residue), bool)
        best = max(sizes, key=sizes.get)
        return np.array([r == best for r in residue])
    mask = np.zeros(len(residue), bool)
    for token in HIGHLIGHT:
        token = str(token)
        if ':' in token:
            ch, num = token.split(':')
            mask |= (t['chain'] == ch) & (t['resi'] == int(num))
        elif token.lstrip('-').isdigit():
            mask |= t['resi'] == int(token)
        else:
            mask |= t['resn'] == token.upper()
    return mask


def stage_matrix(xyz, focus):
    """Molecule -> stage: centroid at the origin, the highlight facing the camera (-Y), long axis up (+Z)."""
    c = xyz.mean(0)
    v = focus - c
    v = v / np.linalg.norm(v) if np.linalg.norm(v) > 2.0 else np.array([0.0, -1.0, 0.0])
    t = np.array([0.0, -1.0, 0.0])
    axis, cos = np.cross(v, t), float(v @ t)
    if np.linalg.norm(axis) < 1e-8:
        R1 = np.eye(3) if cos > 0 else np.diag([-1.0, -1.0, 1.0])
    else:
        k = axis / np.linalg.norm(axis)
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        s = math.sqrt(max(0.0, 1 - cos * cos))
        R1 = np.eye(3) + s * K + (1 - cos) * K @ K
    P = (xyz - c) @ R1.T
    w, V = np.linalg.eigh(P.T @ P)
    a = V[:, int(np.argmax(w))]
    roll = math.atan2(-a[0], a[2])
    Ry = np.array([[math.cos(roll), 0, math.sin(roll)], [0, 1, 0], [-math.sin(roll), 0, math.cos(roll)]])
    T = np.eye(4)
    T[:3, :3] = Ry @ R1
    T[:3, 3] = -T[:3, :3] @ c
    return T


def build():
    scene = SC.reset_scene(SCENE_NAME, PREFIX)
    col_main, col_rig = SC.collection(scene, PREFIX + 'Main'), SC.collection(scene, PREFIX + 'Rig')
    rng = np.random.default_rng(1)
    lin = color.lin

    # --- structure: first model, first conformer, chosen chains
    t, lines = St.read_mmcif(PDB)
    t = St.select(t, t['model'] == t['model'].min())
    t = St.first_conformer(t)
    if CHAINS:
        t = St.select(t, np.isin(t['chain'], CHAINS))
    n = len(t['name'])
    hl = pick_highlight(t)
    focus_raw = t['xyz'][hl].mean(0) if hl.any() else t['xyz'].mean(0)
    Tm = stage_matrix(t['xyz'], focus_raw)
    X = St.transform(t['xyz'], Tm)
    focus = St.transform(focus_raw[None], Tm)[0]

    # --- roles: highlight (always ball-and-stick once uncovered), pocket side chains (revealed by Look.x)
    side = ~np.isin(t['name'], ['N', 'C', 'O'])
    pocket = np.zeros(n, bool)
    if hl.any():
        near = np.min(np.linalg.norm(X[:, None] - X[hl][None], axis=2), axis=1) < POCKET_RADIUS
        residue = np.array([f'{c}:{r}:{s}' for c, r, s in zip(t['chain'], t['resi'], t['resn'])])
        pocket = np.isin(residue, np.unique(residue[near & ~hl])) & side & np.isin(t['resn'], list(STANDARD))
    role = np.where(hl, 2.0, np.where(pocket, 1.0, 0.0))
    shown = np.nonzero(role > 0)[0]
    sub = {k: v[shown] for k, v in t.items()}
    edges = shown[St.bonds(sub, X[shown])] if len(shown) > 1 else np.zeros((0, 2), int)

    # --- colours: muted per chain; element colours (accent carbons on the highlight) when revealed
    chains = list(dict.fromkeys(t['chain'].tolist()))
    ctx = np.zeros((n, 3))
    for k, ch in enumerate(chains):
        sel = t['chain'] == ch
        ctx[sel] = color.shade(rng, CHAIN_TONES[k % len(CHAIN_TONES)], sel.sum(), 0.15, 1.0)
    hi = ctx.copy()
    for el, tones in ELEMENT.items():
        sel = t['element'] == el
        hi[sel] = color.shade(rng, tones, sel.sum(), 0.3, 1.0)
    acc = hl & (t['element'] == 'C')
    hi[acc] = color.shade(rng, ACCENT_C, acc.sum(), 0.4, 1.0)

    breath = groups.breath(PREFIX, loop_frames=FRAMES if LOOP else None, **BREATH)
    ng = groups.molecule(PREFIX, breath, PROTEIN_SCALE, BALL_SCALE, STICK_RADIUS, SECTION_RGB, SECTION_MIX)
    mat = look.attr_material(PREFIX + 'Atom', roughness=0.42, specular=0.45, sheen=0.15)

    cam = bpy.data.objects.new(PREFIX + 'Camera', bpy.data.cameras.new(PREFIX + 'Camera'))
    col_rig.objects.link(cam)
    scene.camera = cam
    aim = SC.empty(PREFIX + 'Aim', col_rig)
    target = SC.empty(PREFIX + 'CutTarget', col_rig, focus)
    slab = SC.empty(PREFIX + 'Slab', col_rig, focus)          # section plane: animate Ctl_Cut.y to sweep it in
    ctl_cut = SC.empty(PREFIX + 'Ctl_Cut', col_rig)           # x funnel open, y slab open, z group-2 reveal
    ctl_look = SC.empty(PREFIX + 'Ctl_Look', col_rig)         # x pocket reveal, y highlight glow
    attrs = {'vdw': ('FLOAT', St.radii(t['element'])), 'role': ('FLOAT', role), 'ball': ('FLOAT', np.ones(n)),
             'stick_w': ('FLOAT', np.ones(n)), 'dilate': ('FLOAT_VECTOR', np.zeros((n, 3))),
             'g0': ('FLOAT', (role == 2).astype(float)), 'g1': ('FLOAT', (role == 1).astype(float)), 'g2': ('FLOAT', np.zeros(n)),
             'col_ctx': ('FLOAT_COLOR', ctx), 'col_hi': ('FLOAT_COLOR', hi),
             'emit_w': ('FLOAT', np.where(hl, 0.6, 0.0)), 'glow_w': ('FLOAT', np.zeros(n))}
    mol = mesh.points_mesh(PREFIX + 'Molecule', X, edges, attrs, col_main)
    mod = mol.modifiers.new('Atoms', 'NODES')
    mod.node_group = ng
    set_modifier_inputs(mod, {'Material': mat, 'Camera': cam, 'Target': target, 'Slab': slab, 'Cut': ctl_cut,
                              'Look': ctl_look, 'Cut Enable': 0.0 if LOOP else 1.0})

    # --- camera
    radius = float(np.percentile(np.linalg.norm(X, axis=1), 98))
    fit = radius / math.tan(math.atan(0.5 * 36.0 * RES[1] / RES[0] / 50.0)) * 1.15   # whole molecule, 50 mm lens

    def dist(v):
        return fit if v == 'fit' else fit * v[1] if isinstance(v, tuple) else float(v)
    points = {'centre': np.zeros(3), 'focus': focus}
    if LOOP:
        path = TL.orbit_path(np.zeros(3), dist(ORBIT['distance']), ORBIT['elevation'], ORBIT['lens'], FRAMES,
                             ORBIT['azimuth0'], ORBIT['turns'])
    else:
        keys = [(1 + round(u * (FRAMES - 1)), a, dist(d), az, el, lens) for u, a, d, az, el, lens in CAMERA]
        path = TL.camera_path(keys, points, FRAMES)
    rig.bake_camera(cam, aim, path, APERTURE_RATIO, clip=(0.5, 20 * fit))

    # --- choreography on the controllers
    if not LOOP:
        (c0, c1), (r0, r1), (g0, g1) = beat('cut'), beat('reveal'), beat('glow')
        SC.keys(ctl_cut, 'location', [(1, 0.0), (c0, 0.0), (c1, 1.0)], 0)
        SC.keys(ctl_look, 'location', [(1, 0.0), (r0, 0.0), (r1, 1.0)], 0)
        SC.keys(ctl_look, 'location', [(1, 0.2), (g0, 0.2), ((g0 + g1) // 2, 1.6), (g1, 0.4)], 1)
    else:
        ctl_look.location = (1.0, 0.3, 0.0)

    # --- world, lights, render settings
    world, _, _ = look.gradient_world(PREFIX + 'World', BACKDROP_TOP, BACKDROP_BOTTOM, AMBIENT_RGB, AMBIENT_STRENGTH)
    scene.world = world
    SC.sun(PREFIX + 'Key', KEY_DIR, KEY_STRENGTH, 28, col_rig, distance=3 * fit)
    SC.sun(PREFIX + 'Rim', RIM_DIR, RIM_STRENGTH, 18, col_rig, distance=3 * fit)
    SC.cycles_settings(scene, RES, FRAMES + 1 if LOOP else FRAMES, FPS, samples=SAMPLES)
    look.bloom(scene, PREFIX + 'Bloom', **BLOOM)
    scene.frame_set(1)
    SC.save_scene(scene, BLEND_PATH)

    # --- labels
    entry_title, entry_method = St.title(lines), St.method(lines) or 'EXPERIMENTAL STRUCTURE'
    names = sorted({f'{r}{n}' for r, n in zip(t['resn'][hl], t['resi'][hl])})
    focus_text = FOCUS_TEXT or (', '.join(names[:3]) + (' ...' if len(names) > 3 else '') if names else '')
    label_result = None
    if LABELS_ON:
        (e0, e1), (r0, r1) = beat('establish'), beat('reveal')
        spec = {'ink': INK, 'halo': HALO,
                'shot_ink': [(1, 'dark')] if LOOP else [(1, 'dark'), (beat('cut')[1], 'light')],
                'captions': [(10, FRAMES if LOOP else max(e1, 60), TITLE, SUBTITLE or (entry_title.capitalize() if entry_title.isupper() else entry_title))],
                'tags': [(10, FRAMES, f'{entry_method}  ·  PDB {PDB_ID}  ·  MOTION ILLUSTRATIVE')],
                'pointers': []}
        if not LOOP and focus_text:
            spec['captions'].append((r0, FRAMES, focus_text, 'Highlighted residues as ball-and-stick'))
            spec['pointers'].append((r0 + 6, FRAMES, 'focus', focus_text, (170, -130)))
        label_result = labels.label_pass(SCENE_NAME + '_Labels', PREFIX + 'L_', spec, path, {'focus': focus}, RES,
                                         FRAMES + 1 if LOOP else FRAMES, FPS, LABEL_BLEND)
    SC.show(scene)

    return {
        'blender': bpy.app.version_string, 'scene': scene.name, 'pdb': PDB_ID, 'title': entry_title,
        'method': entry_method, 'atoms': n, 'chains': chains, 'highlight': names, 'pocket_atoms': int(pocket.sum()),
        'stick_bonds': len(edges), 'radius_A': round(radius, 1), 'fit_distance_A': round(fit, 1), 'loop': LOOP,
        'frames': FRAMES, 'camera_seam_A': round(float(np.linalg.norm(path[FRAMES][1] - path[0][1])), 6) if LOOP else None,
        'blend': str(BLEND_PATH), 'labels': label_result,
    }


RESULT = build()
