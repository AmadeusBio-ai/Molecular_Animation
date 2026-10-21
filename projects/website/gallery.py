"""Website stills for amadeusbio.ai: one molecule per component, each chosen for what it shows.

  hemoglobin  2HHB      the four globins and their hemes (amber)              principle: biology comes first
  dna         1BNA      B-DNA dodecamer; Watson-Crick hydrogen bonds measured  principle: evaluate with care
                        from the coordinates, drawn as dotted markers
  p53         AF-P04637-F1 (AlphaFold DB, CC BY 4.0) coloured by per-residue  principle: make uncertainty clear
                        confidence (pLDDT); low-confidence regions translucent
  p53dna      AlphaFold Server (AlphaFold 3) model of the p53 tetramer on the p21     principle: make uncertainty clear
                        response element (af3/), coloured by pLDDT; below 70 translucent, DNA in amber.
                        AlphaFold Server Output Terms apply (af3/model/terms_of_use.md)
  gfp         1EMA      a camera-aimed cutaway opens the barrel to the chromophore    gallery: cutaways
  kcsa        1K4C      potassium channel tetramer, section through the pore, measured gallery: cavity tubes
                        free-radius profile as a tube, the deposited K+ ions
  aquaporin   1J4N      aquaporin-1 tetramer in a procedural bilayer, cut in front     gallery: membranes
  igg         1IGT      intact IgG2a antibody, glycans in amber                         card: Molecular Animation
  nucleosome  1KX5      DNA wrapped on the histone octamer, soft close-up (deep look)   call to action
  agents      several   the molecules above as a constellation, joined by amber trails card: agentic systems (illustration)

Structures are from the RCSB PDB (CC0) and the AlphaFold Protein Structure Database (CC BY 4.0), kept in
projects/website/pdb. Tetramers come from the deposited assembly operators. Evidence levels are in record.md.

Headless (from the repo root):
  blender -b --factory-startup --python projects/website/gallery.py -- --shot gfp --still renders/website/final/gfp.png
Options: --percent P, --samples N.
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
sys.path[:0] = [str(ROOT), str(HERE)]
import molanim  # noqa: E402

molanim.reload()
from molanim import color, membrane  # noqa: E402
from molanim import pathway as Pw  # noqa: E402
from molanim import structure as St  # noqa: E402
from molanim.blender import groups, look, mesh, rig  # noqa: E402
from molanim.blender import scene as SC  # noqa: E402
from molanim.blender.nodes import set_modifier_inputs  # noqa: E402
import website as W  # noqa: E402  (looks, radial backdrop, GPU selection)

PREFIX = 'WGL_'
PDB = HERE / 'pdb'
SUGARS = {'NAG', 'BMA', 'MAN', 'FUC', 'FUL', 'GAL', 'NDG', 'SIA'}
BACKBONE_NA = {'P', 'OP1', 'OP2', 'OP3', "O5'", "C5'", "C4'", "O4'", "C3'", "O3'", "C2'", "C1'"}

AMBER = ((226, 136, 28), (255, 192, 84))
GREEN = ((40, 170, 96), (120, 226, 156))          # the GFP chromophore fluoresces green
NAVY = ((20, 50, 98), (78, 110, 156))
STEEL = ((72, 102, 146), (128, 154, 190))
SLATE = ((118, 140, 170), (176, 191, 211))
PALE = ((186, 198, 214), (226, 232, 240))
PORCELAIN = ((200, 213, 230), (246, 248, 252))
AZURE = ((84, 124, 180), (146, 178, 220))
CREAM = ((214, 190, 150), (250, 236, 210))
ELEMENT = {'C': ((198, 205, 214), (236, 240, 244)), 'N': ((52, 94, 204), (96, 136, 236)),
           'O': ((208, 72, 62), (236, 112, 98)), 'S': ((226, 186, 40), (246, 214, 90)), 'P': ((236, 150, 60), (250, 180, 90))}
# Loops only (loops.py): illustrative thermal motion, as in the channelrhodopsin film. RMS displacement per axis in
# A of the coherent and the fine noise field (molanim.blender.groups.thermal). Backbones barely move; side chains
# move more toward their tips (side + step x remoteness, CB = 1 ... NH = 6); atoms in ball-and-stick get almost no
# fine motion so their sticks do not stretch; lipids move most.
AMINO = {'ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'GLY', 'HIS', 'ILE', 'LEU', 'LYS', 'MET', 'PHE', 'PRO', 'SER',
         'THR', 'TRP', 'TYR', 'VAL', 'MSE'}
REMOTENESS = {'B': 1, 'G': 2, 'D': 3, 'E': 4, 'Z': 5, 'H': 6}
THERMAL = {'backbone': (0.10, 0.04), 'side': (0.14, 0.04), 'step': (0.06, 0.025), 'other': (0.15, 0.04),
           'stick_fine': 0.02, 'lipid_head': (0.9, 0.15), 'lipid_tail': (1.2, 0.22)}


# ----------------------------------------------------------------------------- structures

def load(name, chains=None, ops=None, skip=frozenset(), model_first=True):
    """Atom table of projects/website/pdb/<name>.cif: first model, first conformer, chosen chains, and
    copies by assembly operators (chain ids get the copy number appended)."""
    t, lines = St.read_mmcif(PDB / f'{name}.cif', skip=St.WATERS | St.ADDITIVES | set(skip))
    if model_first:
        t = St.select(t, t['model'] == t['model'].min())
    t = St.first_conformer(t)
    if chains:
        t = St.select(t, np.isin(t['chain'], chains))
    if ops:
        parts = []
        for k, op in enumerate(ops):
            c = {key: v.copy() for key, v in t.items()}
            c['xyz'] = St.transform(t['xyz'], St.assembly_operator(lines, op))
            c['chain'] = np.array([f'{ch}{k}' for ch in t['chain']])
            parts.append(c)
        t = {key: np.concatenate([p[key] for p in parts]) for key in t}
    return t, lines


def operator_axis(lines, op):
    """Rotation axis (unit vector) and a point on it of an assembly operator (a pure rotation + translation)."""
    M = St.assembly_operator(lines, op)
    R, tv = M[:3, :3], M[:3, 3]
    w, V = np.linalg.eig(R)
    axis = np.real(V[:, np.argmin(np.abs(w - 1))])
    point = np.linalg.lstsq(np.eye(3) - R, tv, rcond=None)[0]
    return axis / np.linalg.norm(axis), point


def bfactors(lines):
    """Per-atom B-factor column of the atom_site loop (same order as read_mmcif with hydrogens skipped)."""
    i = next(n for n, line in enumerate(lines) if line.startswith('_atom_site.'))
    cols = []
    while lines[i].startswith('_atom_site.'):
        cols.append(lines[i].split('.', 1)[1].strip())
        i += 1
    c = {k: n for n, k in enumerate(cols)}
    out = []
    while i < len(lines) and lines[i].startswith(('ATOM', 'HETATM')):
        r = lines[i].split()
        if r[c['type_symbol']] not in ('H', 'D'):
            out.append(float(r[c['B_iso_or_equiv']]))
        i += 1
    return np.array(out)


def rotation_to(a, b):
    """Rotation matrix taking unit vector a onto unit vector b."""
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    v, cos = np.cross(a, b), float(a @ b)
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if cos > 0 else np.diag([1.0, -1.0, -1.0])
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - cos) / np.linalg.norm(v) ** 2)


def principal_frame(X, up=None, origin=None):
    """Stage coordinates: origin at the bounding-box centre (or `origin`), longest principal axis (or `up`)
    along +Z, the thinnest along Y (the camera's depth), so the default camera sees the broadest face."""
    c = (X.min(0) + X.max(0)) / 2 if origin is None else np.asarray(origin, float)
    P = X - c
    if up is not None:
        R1 = rotation_to(np.asarray(up, float), np.array([0.0, 0.0, 1.0]))
        Q = P @ R1.T
        w, V = np.linalg.eigh(Q[:, :2].T @ Q[:, :2])
        a = V[:, int(np.argmax(w))]                        # broad in-plane axis -> X
        ang = math.atan2(a[1], a[0])
        Rz = np.array([[math.cos(-ang), -math.sin(-ang), 0], [math.sin(-ang), math.cos(-ang), 0], [0, 0, 1]])
        return P @ (Rz @ R1).T
    w, V = np.linalg.eigh(P.T @ P)
    order = np.argsort(w)[::-1]
    R = np.stack([V[:, order[1]], V[:, order[2]], V[:, order[0]]])
    if np.linalg.det(R) < 0:
        R[0] *= -1
    return P @ R.T


def thermal_amplitudes(t, role):
    """Per-atom 'thermal' and 'thermal_fine' attributes (see THERMAL)."""
    names = t['name']
    aa = np.isin(t['resn'], list(AMINO))
    backbone = (aa & np.isin(names, ['N', 'CA', 'C', 'O', 'OXT'])) | np.isin(names, list(BACKBONE_NA))
    side = aa & ~backbone
    level = np.array([REMOTENESS.get(nm[1:2], 0) for nm in names])
    amp = np.tile(np.array(THERMAL['other'], float), (len(names), 1))
    amp[backbone] = THERMAL['backbone']
    amp[side] = np.array(THERMAL['side']) + np.array(THERMAL['step']) * level[side, None]
    amp[np.asarray(role) > 0, 1] = THERMAL['stick_fine']
    return {'thermal': ('FLOAT', amp[:, 0]), 'thermal_fine': ('FLOAT', amp[:, 1])}


def rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return {'x': np.array([[1, 0, 0], [0, c, -s], [0, s, c]]), 'y': np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]),
            'z': np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])}[axis]


# ----------------------------------------------------------------------------- scene building

class Stage:
    """One shot: scene, collections, rig, the shared molecule node group and materials."""

    def __init__(self, name, look_name, res, frames=1, loop=None):
        self.L = W.LOOKS[look_name]
        self.loop = loop
        self.look, self.res = look_name, res
        self.scene = SC.reset_scene('Web_' + name, PREFIX)
        self.col = SC.collection(self.scene, PREFIX + 'Main')
        self.fx = SC.collection(self.scene, PREFIX + 'Effects')
        self.rigc = SC.collection(self.scene, PREFIX + 'Rig')
        self.rng = np.random.default_rng(11)
        self.cam = bpy.data.objects.new(PREFIX + 'Camera', bpy.data.cameras.new(PREFIX + 'Camera'))
        self.rigc.objects.link(self.cam)
        self.scene.camera = self.cam
        self.aim = SC.empty(PREFIX + 'Aim', self.rigc)
        self.target = SC.empty(PREFIX + 'CutTarget', self.rigc)
        self.slab = SC.empty(PREFIX + 'Slab', self.rigc)
        self.cut = SC.empty(PREFIX + 'Ctl_Cut', self.rigc)
        self.lookc = SC.empty(PREFIX + 'Ctl_Look', self.rigc)
        self.lookc.location = (1.0, 1.4, 0.0)
        self.path = SC.empty(PREFIX + 'Ctl_Path', self.rigc)
        if loop:        # loops.py: no breathing; thermal motion that repeats every `loop` frames
            self.breath = groups.breath(PREFIX, sway=0.0, jitter=0.0)
            self.thermal = groups.thermal(PREFIX, loop_frames=loop)
        else:
            self.breath = groups.breath(PREFIX, sway=0.25, jitter=0.08)
            self.thermal = None
        self.ng = groups.molecule(PREFIX, self.breath, 0.64, 0.28, 0.16, self.L['section'], 0.4, thermal_group=self.thermal)
        self.mat = look.attr_material(PREFIX + 'Atom', roughness=0.40, specular=0.5, sheen=0.2)
        self.direction = None

    def camera(self, aim, dist, az, el, lens=50, dof=0.01):
        a, e = math.radians(az), math.radians(el)
        self.direction = np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
        self.aim_point = np.asarray(aim, float)
        path = [(1, self.aim_point + dist * self.direction, self.aim_point, dist, lens)]
        rig.bake_camera(self.cam, self.aim, path, max(dof, 1e-4), clip=(0.5, 60 * dist))

    def fit(self, X, aim, lens=50, margin=1.08, pct=99.7):
        r = float(np.percentile(np.linalg.norm(X - aim, axis=1), pct))
        half = math.atan(0.5 * 36.0 * min(1.0, self.res[1] / self.res[0]) / lens)
        return r / math.tan(half) * margin

    def molecule(self, name, X, t, ctx, hi=None, role=None, emit=None, scale=0.64, ball=0.28, stick=0.16,
                 cut=0.0, material=None, collection=None):
        n = len(X)
        role = np.zeros(n) if role is None else role
        hi = ctx if hi is None else hi
        shown = np.nonzero(role > 0)[0]
        if len(shown) > 1:
            sub = {k: v[shown] for k, v in t.items()}
            edges = shown[St.bonds(sub, X[shown])]
        else:
            edges = np.zeros((0, 2), int)
        attrs = {'vdw': ('FLOAT', St.radii(t['element'])), 'role': ('FLOAT', role), 'ball': ('FLOAT', np.ones(n)),
                 'stick_w': ('FLOAT', np.ones(n)), 'dilate': ('FLOAT_VECTOR', np.zeros((n, 3))),
                 'g0': ('FLOAT', (role >= 1).astype(float)), 'g1': ('FLOAT', np.zeros(n)), 'g2': ('FLOAT', np.zeros(n)),
                 'col_ctx': ('FLOAT_COLOR', ctx), 'col_hi': ('FLOAT_COLOR', hi),
                 'emit_w': ('FLOAT', np.zeros(n) if emit is None else emit), 'glow_w': ('FLOAT', np.zeros(n))}
        if self.thermal:
            attrs.update(thermal_amplitudes(t, role))
        obj = mesh.points_mesh(PREFIX + name, X, edges, attrs, collection or self.col)
        mod = obj.modifiers.new('Atoms', 'NODES')
        mod.node_group = self.ng
        set_modifier_inputs(mod, {'Material': material or self.mat, 'Camera': self.cam, 'Target': self.target,
                                  'Slab': self.slab, 'Cut': self.cut, 'Look': self.lookc, 'Cut Enable': cut,
                                  'Path Control': self.path, 'Scale': scale, 'Ball': ball, 'Stick': stick, 'Funnel': 7.5})
        return obj

    def shade(self, ramp, n, lo=0.0, hi=1.0):
        return color.shade(self.rng, ramp, n, lo, hi)

    def elements(self, t, carbon=None):
        out = np.zeros((len(t['element']), 3))
        for el, tones in ELEMENT.items():
            sel = t['element'] == el
            out[sel] = self.shade(tones, sel.sum(), 0.3, 1.0)
        if carbon is not None:
            sel = t['element'] == 'C'
            out[sel] = self.shade(carbon, sel.sum(), 0.4, 1.0)
        return out

    def dotted(self, name, p1, p2, rgb=(255, 214, 140), strength=6.0, dots=5, bead=0.14):
        # Under thermal motion the marker's ends move with the base atoms they join (THERMAL 'other', stick_fine).
        attrs = ({'thermal': ('FLOAT', [THERMAL['other'][0]] * 2), 'thermal_fine': ('FLOAT', [THERMAL['stick_fine']] * 2)}
                 if self.thermal else None)
        b = mesh.points_mesh(PREFIX + name, [p1, p2], [(0, 1)], attrs, self.fx)
        m = b.modifiers.new('Bridge', 'NODES')
        if not hasattr(self, '_dotted'):
            self._dotted = groups.dotted_link(PREFIX, self.breath, dots=dots, bead=bead, thermal_group=self.thermal)
            self._dot_mat = look.glow_material(PREFIX + 'Dot', rgb, strength)[0]
            self._dot_show = SC.empty(PREFIX + 'Ctl_Dots', self.rigc, (1.0, 0, 0))
        m.node_group = self._dotted
        set_modifier_inputs(m, {'Material': self._dot_mat, 'Show': self._dot_show, 'Dots': dots, 'Bead': bead})
        b.visible_shadow = False

    def finish(self, samples):
        L = self.L
        kind, top, bottom = L['world']
        if kind == 'radial':
            self.scene.world = W.radial_world(PREFIX + 'World', top, bottom, *L['ambient'], self.res)
        else:
            self.scene.world = look.gradient_world(PREFIX + 'World', top, bottom, *L['ambient'])[0]
        dist = float(np.linalg.norm(self.cam.location - self.aim.location)) if self.direction is not None else 300
        for key in ('key', 'rim', 'fill'):
            d, e, rgb = L[key]
            SC.sun(PREFIX + key.title(), d, e, 24 if key == 'key' else 14, self.rigc, rgb, distance=3 * dist)
        SC.cycles_settings(self.scene, self.res, 1, 24, samples=samples)
        look.bloom(self.scene, PREFIX + 'Bloom', threshold=1.0, strength=0.45, size=0.6)
        self.scene.frame_set(1)
        return self.scene


# ----------------------------------------------------------------------------- shots

def shot_hemoglobin(S):
    t, _ = load('2HHB', chains=['A', 'B', 'C', 'D'])
    X = principal_frame(t['xyz'])
    heme = t['resn'] == 'HEM'
    alpha = np.isin(t['chain'], ['A', 'C'])
    n = len(X)
    ctx = np.where(alpha[:, None], S.shade(NAVY, n), S.shade(SLATE, n))
    ctx[heme] = S.shade(((214, 120, 20), (246, 170, 60)), heme.sum(), 0.2, 1.0)
    prot = ~heme
    S.molecule('Globins', X[prot], St.select(t, prot), ctx[prot], scale=0.62)
    S.molecule('Hemes', X[heme], St.select(t, heme), ctx[heme], emit=np.full(heme.sum(), 0.22), scale=0.86)
    aim = np.zeros(3)
    S.camera(aim, S.fit(X, aim) * 1.0, az=-28, el=16, dof=0.008)
    return {'atoms': int(n), 'heme_atoms': int(heme.sum()), 'chains': 4}


def shot_dna(S):
    t, _ = load('1BNA', chains=['A', 'B'])
    X = principal_frame(t['xyz']) @ rot('y', 32).T            # helix axis tilted across the frame
    n = len(X)
    back = np.isin(t['name'], list(BACKBONE_NA))
    strand_a = t['chain'] == 'A'
    ctx = np.where(strand_a[:, None], S.shade(NAVY, n), S.shade(STEEL, n))
    role = np.where(back, 0.0, 2.0)                             # bases as ball-and-stick, backbone as spheres
    hi = S.elements(t, carbon=PALE)
    S.molecule('Duplex', X, t, ctx, hi=hi, role=role, scale=0.62, ball=0.26, stick=0.15)
    # Watson-Crick hydrogen bonds only: the canonical donor-acceptor atom pairs of G-C (3) and A-T (2) between
    # each base and its partner on the other strand, drawn where the measured distance is below 3.4 A.
    wc = {('DG', 'DC'): [('N1', 'N3'), ('N2', 'O2'), ('O6', 'N4')], ('DA', 'DT'): [('N1', 'N3'), ('N6', 'O4')]}
    wc.update({(b, a): [(y, x) for x, y in v] for (a, b), v in list(wc.items())})

    def atom(ch, ri, nm):
        k = np.nonzero((t['chain'] == ch) & (t['resi'] == ri) & (t['name'] == nm))[0]
        return int(k[0]) if len(k) else None

    def resn(ch, ri):
        return t['resn'][(t['chain'] == ch) & (t['resi'] == ri)][0]

    def hub(ch, ri):                                   # N1 of purines, N3 of pyrimidines: the central pair
        return atom(ch, ri, 'N1' if resn(ch, ri) in ('DG', 'DA') else 'N3')
    pairs = []
    for i in sorted(set(t['resi'][strand_a].tolist())):
        cands = [j for j in sorted(set(t['resi'][~strand_a].tolist())) if (resn('A', i), resn('B', j)) in wc]
        if not cands:
            continue
        j = min(cands, key=lambda j: np.linalg.norm(X[hub('A', i)] - X[hub('B', j)]))
        if np.linalg.norm(X[hub('A', i)] - X[hub('B', j)]) > 3.6:
            continue
        for na, nb in wc[(resn('A', i), resn('B', j))]:
            a, b = atom('A', i, na), atom('B', j, nb)
            if a is not None and b is not None and np.linalg.norm(X[a] - X[b]) < 3.4:
                pairs.append((a, b, float(np.linalg.norm(X[a] - X[b]))))
    for k, (a, b, _) in enumerate(pairs):
        S.dotted(f'HBond{k}', X[a], X[b], rgb=(250, 176, 64), strength=5.0, dots=5, bead=0.17)
    aim = np.zeros(3)
    S.camera(aim, S.fit(X, aim) * 1.0, az=18, el=6, dof=0.010)
    dist = [p[2] for p in pairs]
    return {'atoms': int(n), 'hbonds': len(pairs), 'hbond_A': [round(min(dist), 2), round(float(np.mean(dist)), 2), round(max(dist), 2)]}


def shot_p53(S):
    t, lines = load('AF-P04637-F1')
    plddt = bfactors(lines)
    assert len(plddt) == len(t['name'])
    X = principal_frame(t['xyz'])
    n = len(X)
    ctx = np.zeros((n, 3))
    bands = [(90, 101, NAVY), (70, 90, STEEL), (50, 70, SLATE), (0, 50, PALE)]
    for lo, hi_, ramp in bands:
        sel = (plddt >= lo) & (plddt < hi_)
        ctx[sel] = S.shade(ramp, sel.sum())
    sure = plddt >= 70
    S.molecule('Confident', X[sure], St.select(t, sure), ctx[sure], scale=0.66)
    ghost, alpha = look.ghost_material(PREFIX + 'Uncertain', (176, 194, 220))
    alpha.default_value = 0.55
    unsure = ~sure
    S.molecule('Uncertain', X[unsure], St.select(t, unsure), ctx[unsure], scale=0.5, material=ghost)
    aim = np.zeros(3)
    S.camera(aim, S.fit(X, aim, pct=98.0) * 0.86, az=-20, el=12, dof=0.006)
    res = np.unique(t['resi'])
    per_res = np.array([plddt[t['resi'] == r][0] for r in res])
    return {'atoms': int(n), 'residues': len(res), 'plddt_mean': round(float(per_res.mean()), 1),
            'fraction_residues_plddt_ge_70': round(float((per_res >= 70).mean()), 3)}


AF3 = HERE / 'af3' / 'model'
AF3_JOB = 'fold_p53_tetramer_on_the_p21_response_element'


def shot_p53_dna(S):
    """AlphaFold Server (AlphaFold 3) model 0 of af3/p53-tetramer-p21.json: four full-length p53 chains (A-D),
    four Zn2+ (E-H) and the 20 bp p21 response element (I, J). Coordinates as predicted, only turned rigidly
    to stage them. Colour by per-atom pLDDT: >= 90 navy, 70-90 steel, both solid; everything below 70
    translucent, the DNA in translucent amber."""
    t, lines = St.read_mmcif(AF3 / f'{AF3_JOB}_model_0.cif')
    plddt = bfactors(lines)
    assert len(plddt) == len(t['name'])
    summary = json.loads((AF3 / f'{AF3_JOB}_summary_confidences_0.json').read_text())
    prot = np.isin(t['chain'], list('ABCD'))
    dna = np.isin(t['chain'], ['I', 'J'])
    zinc = t['resn'] == 'ZN'
    dbd = prot & (t['resi'] >= 94) & (t['resi'] <= 292)
    tet = prot & (t['resi'] >= 325) & (t['resi'] <= 356)
    # Stage: DNA axis across the frame (X), the tetramerisation domain above it (+Z).
    D = t['xyz'][dna]
    c = D.mean(0)
    w, V = np.linalg.eigh((D - c).T @ (D - c))
    ex = V[:, -1]
    v = t['xyz'][tet].mean(0) - c
    ez = v - (v @ ex) * ex
    ez /= np.linalg.norm(ez)
    ey = np.cross(ez, ex)
    X = (t['xyz'] - c) @ np.stack([ex, ey, ez]).T
    n = len(X)
    ctx = np.zeros((n, 3))
    for lo, hi_, ramp in [(90, 101, NAVY), (70, 90, STEEL), (50, 70, SLATE), (0, 50, PALE)]:
        sel = (plddt >= lo) & (plddt < hi_)
        ctx[sel] = S.shade(ramp, sel.sum())
    sure = (plddt >= 70) & ~dna
    S.molecule('Confident', X[sure], St.select(t, sure), ctx[sure], scale=0.66)
    ghost, alpha = look.ghost_material(PREFIX + 'Uncertain', (176, 194, 220))
    alpha.default_value = 0.55
    unsure = (plddt < 70) & ~dna
    S.molecule('Uncertain', X[unsure], St.select(t, unsure), ctx[unsure], scale=0.5, material=ghost)
    amber, a_alpha = look.ghost_material(PREFIX + 'DnaGhost', (233, 166, 60))
    a_alpha.default_value = 0.7
    weak_dna = dna & (plddt < 70)
    assert weak_dna.sum() == dna.sum(), 'some DNA is >= pLDDT 70: draw it solid'
    S.molecule('DNA', X[dna], St.select(t, dna), ctx[dna], scale=0.6, material=amber)
    # Measured: DBD heavy atoms within 4 A of the DNA, per chain, and the closest DNA-contact residues.
    contacts = {}
    for ch in 'ABCD':
        s = dbd & (t['chain'] == ch)
        d = np.linalg.norm(X[s][:, None] - X[dna][None], axis=2).min(1)
        contacts[ch] = int((d < 4.0).sum())
    aim = (X[dbd].min(0) + X[dbd].max(0)) / 2
    core = np.concatenate([X[dbd | tet | dna], X[prot][::7]])
    S.camera(aim, S.fit(core, aim, pct=97.0) * 0.9, az=66, el=20, dof=0.006)
    res = [(ch, r) for ch in 'ABCD' for r in sorted(set(t['resi'][t['chain'] == ch].tolist()))]
    per_res = np.array([plddt[(t['chain'] == ch) & (t['resi'] == r)].mean() for ch, r in res])
    dom = {name: round(float(plddt[prot & (t['resi'] >= lo) & (t['resi'] <= hi_)].mean()), 1)
           for name, lo, hi_ in (('tad', 1, 61), ('prd', 62, 93), ('dbd', 94, 292), ('linker', 293, 324),
                                 ('tet', 325, 356), ('ctd', 357, 393))}
    return {'atoms': int(n), 'protein_residues': len(res), 'zinc': int(zinc.sum()),
            'plddt_protein_mean': round(float(per_res.mean()), 1),
            'fraction_protein_residues_plddt_ge_70': round(float((per_res >= 70).mean()), 3),
            'plddt_domains': dom, 'plddt_dna_mean': round(float(plddt[dna].mean()), 1),
            'dbd_atoms_within_4A_of_dna': contacts,
            'iptm': summary['iptm'], 'ptm': summary['ptm'], 'ranking_score': summary['ranking_score'],
            'fraction_disordered': summary['fraction_disordered'], 'has_clash': summary['has_clash']}


def shot_gfp(S):
    t, _ = load('1EMA', chains=['A'])
    cro = t['resn'] == 'CRO'
    X0 = t['xyz']
    X = principal_frame(X0)
    focus = X[cro].mean(0)
    n = len(X)
    side = ~np.isin(t['name'], ['N', 'C', 'O'])
    near = np.min(np.linalg.norm(X[:, None] - X[cro][None], axis=2), axis=1) < 4.2
    residue = np.array([f'{c}:{r}' for c, r in zip(t['chain'], t['resi'])])
    pocket = np.isin(residue, np.unique(residue[near & ~cro])) & side & ~cro
    role = np.where(cro, 2.0, 0.0)                    # only the chromophore in ball-and-stick: one clear subject
    ctx = S.shade(NAVY, n)
    ctx[t['resi'] > 150] = S.shade(STEEL, (t['resi'] > 150).sum())
    hi = S.elements(t)
    hi[cro] = S.shade(GREEN, int(cro.sum()), 0.3, 1.0)
    emit = np.where(cro, 0.3, 0.0)
    S.target.location = focus
    S.cut.location = (1.0, 0.0, 0.0)
    S.molecule('Barrel', X, t, ctx, hi=hi, role=role, emit=emit, cut=1.0, ball=0.32, stick=0.18)
    S.camera(focus, 78.0, az=-14, el=10, dof=0.012)
    return {'atoms': int(n), 'chromophore_atoms': int(cro.sum()), 'pocket_atoms': int(pocket.sum())}


def shot_kcsa(S):
    t, lines = load('1K4C', chains=['C'], ops=['1', '2', '3', '4'], skip={'DGA', 'F09'})
    axis, point = operator_axis(lines, '2')
    ions = t['resn'] == 'K'
    # The ions on the four-fold axis map onto themselves: keep one copy of each.
    keep = np.ones(len(ions), bool)
    idx = np.nonzero(ions)[0]
    for a_i, a in enumerate(idx):
        for b in idx[:a_i]:
            if keep[b] and np.linalg.norm(t['xyz'][a] - t['xyz'][b]) < 0.8:
                keep[a] = False
    t = St.select(t, keep)
    ions = t['resn'] == 'K'
    origin = t['xyz'][ions].mean(0) if ions.any() else point
    X = principal_frame(t['xyz'], up=axis, origin=origin)
    prot = ~ions
    n = int(prot.sum())
    sub = St.select(t, prot)
    sub_k = np.array([int(c[-1]) for c in sub['chain']])
    tones = [NAVY, STEEL, NAVY, STEEL]
    ctx = np.zeros((n, 3))
    for k in range(4):
        sel = sub_k == k
        ctx[sel] = S.shade(tones[k], sel.sum())
    S.slab.location = (0.0, 0.0, 0.0)
    S.cut.location = (0.0, 1.0, 0.0)
    S.molecule('Channel', X[prot], sub, ctx, cut=1.0, scale=0.72)
    # Pore: slice search along the four-fold axis (stage Z), elastic band, free radius.
    vdw = St.radii(sub['element'])
    zs = np.arange(X[prot][:, 2].min() + 2, X[prot][:, 2].max() - 2, 1.0)
    guide = [(0.0, 0.0, zs[0]), (0.0, 0.0, zs[-1])]
    centres, free = Pw.pore_profile(X[prot], vdw, guide, zs, axis=2)
    line = Pw.polyline(Pw.relax_path(centres, X[prot], vdw, axis=2), spacing=0.5, smooth=2)
    r = Pw.clearance(line, X[prot], vdw)
    r = np.convolve(np.pad(r, 2, mode='edge'), np.ones(5) / 5, mode='valid')
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))])
    taper = np.clip(np.minimum(arc, arc[-1] - arc) / 6.0, 0, 1) ** 0.5
    cav = mesh.points_mesh(PREFIX + 'Pore', line, [(k, k + 1) for k in range(len(line) - 1)],
                           {'r0': ('FLOAT', np.clip(r, 0, None)), 'r1': ('FLOAT', np.clip(r, 0, None)),
                            'taper': ('FLOAT', taper)}, S.fx)
    cm = cav.modifiers.new('Pore', 'NODES')
    cm.node_group = groups.tube(PREFIX, margin=0.4, cap=6.0)
    S.path.location = (1.0, 0.0, 0.0)
    set_modifier_inputs(cm, {'Material': look.glow_material(PREFIX + 'PoreGlow', (96, 160, 240), 1.2, rim=True)[0],
                             'Control': S.path})
    cav.visible_shadow = False
    kx = X[ions]
    km = mesh.points_mesh(PREFIX + 'Potassium', kx, None, {'radius': ('FLOAT', np.full(len(kx), 1.33))}, S.fx)
    kmod = km.modifiers.new('Ions', 'NODES')
    kmod.node_group = groups.spheres(PREFIX, None, name='Ions')
    set_modifier_inputs(kmod, {'Material': look.glow_material(PREFIX + 'K', (250, 186, 80), 4.0)[0]})
    aim = np.array([0.0, 0.0, -4.0])
    S.camera(aim, 132.0, az=0, el=4, dof=0.008)
    return {'protein_atoms': n, 'k_ions': int(ions.sum()), 'pore_min_free_radius_A': round(float(r.min()), 2),
            'pore_max_free_radius_A': round(float(r.max()), 2)}


def shot_aquaporin(S):
    t, lines = load('1J4N', chains=['A'], ops=['1', '2', '3', '4'])
    axis, point = operator_axis(lines, '2')
    c = t['xyz'].mean(0)
    origin = point + axis * float((c - point) @ axis)
    X = principal_frame(t['xyz'], up=axis, origin=origin)
    n = len(X)
    k = np.array([int(ch[-1]) for ch in t['chain']])
    tones = [NAVY, ((110, 136, 176), (160, 182, 212)), NAVY, ((110, 136, 176), (160, 182, 212))]
    ctx = np.zeros((n, 3))
    for j in range(4):
        ctx[k == j] = S.shade(tones[j], (k == j).sum())
    S.molecule('Tetramer', X, t, ctx, scale=0.8)
    mem = membrane.bilayer((-260.0, 260.0, 4.0, 320.0), X, seed=5, keep=lambda p: p[1] > 4.0)
    head = mem['part'] == 'head'
    L = S.L
    mcol = np.where(head[:, None], S.shade(L['lipid_head'], len(head)), S.shade(L['lipid_tail'], len(head)))
    mrad = St.radii(mem['element']) * np.where(head, 0.62, 0.78)
    attrs = {'radius': ('FLOAT', mrad), 'col': ('FLOAT_COLOR', mcol)}
    if S.thermal:
        amp = np.where(head[:, None], THERMAL['lipid_head'], THERMAL['lipid_tail'])
        attrs.update({'thermal': ('FLOAT', amp[:, 0]), 'thermal_fine': ('FLOAT', amp[:, 1])})
    lip = mesh.points_mesh(PREFIX + 'Membrane', mem['xyz'], None, attrs, S.col)
    lm = lip.modifiers.new('Lipids', 'NODES')
    lm.node_group = groups.spheres(PREFIX, S.breath, thermal_group=S.thermal)
    set_modifier_inputs(lm, {'Material': look.attr_material(PREFIX + 'Lipid', roughness=0.5, specular=0.3, sheen=0.1)})
    S.camera(np.array([0.0, 10.0, -2.0]), 250.0, az=-22, el=14, dof=0.010)
    return {'atoms': int(n), 'lipids': int(mem['count'])}


def shot_igg(S):
    t, _ = load('1IGT', skip=set())
    X = principal_frame(t['xyz']) @ rot('z', 0).T
    n = len(X)
    sugar = np.isin(t['resn'], list(SUGARS))
    heavy = np.isin(t['chain'], ['B', 'D'])
    ctx = np.where(heavy[:, None], S.shade(NAVY, n), S.shade(SLATE, n))
    ctx[np.isin(t['chain'], ['D']) & ~sugar] = S.shade(STEEL, int((np.isin(t['chain'], ['D']) & ~sugar).sum()))
    ctx[sugar] = S.shade(AMBER, int(sugar.sum()), 0.3, 1.0)
    S.molecule('Antibody', X, t, ctx, emit=np.where(sugar, 0.35, 0.0), scale=0.72)
    aim = np.zeros(3)
    S.camera(aim, S.fit(X, aim) * 1.18, az=-12, el=8, dof=0.006)
    return {'atoms': int(n), 'glycan_atoms': int(sugar.sum())}


def shot_nucleosome(S):
    t, _ = load('1KX5')
    dna = np.isin(t['chain'], ['I', 'J'])
    X = principal_frame(t['xyz'])
    n = len(X)
    tones = {'A': AZURE, 'E': AZURE, 'B': STEEL, 'F': STEEL, 'C': ((60, 92, 140), (104, 136, 182)),
             'G': ((60, 92, 140), (104, 136, 182)), 'D': ((118, 150, 196), (176, 200, 232)), 'H': ((118, 150, 196), (176, 200, 232))}
    ctx = np.zeros((n, 3))
    for ch, ramp in tones.items():
        sel = t['chain'] == ch
        ctx[sel] = S.shade(ramp, sel.sum())
    back = np.isin(t['name'], list(BACKBONE_NA))
    ctx[dna & back] = S.shade(CREAM, int((dna & back).sum()))
    ctx[dna & ~back] = S.shade(AMBER, int((dna & ~back).sum()), 0.2, 0.8)
    S.molecule('Nucleosome', X, t, ctx, scale=0.8)
    # The disc's flat face: the thinnest principal axis is Y (camera depth). Close-up, off-centre.
    aim = np.array([12.0, 0.0, 6.0])
    S.camera(aim, 185.0, az=-34, el=24, dof=0.022)
    return {'atoms': int(n), 'dna_atoms': int(dna.sum())}


def shot_agents(S):
    rng = np.random.default_rng(5)
    specs = [  # (structure, chains, ops, centre on stage, extra rotation, tone)
        ('1KX5', None, None, (-112, 50, 22), ('x', 70), AZURE),
        ('2HHB', ['A', 'B', 'C', 'D'], None, (-18, -25, -34), ('z', 20), PORCELAIN),
        ('1IGT', None, None, (96, 55, 26), ('z', -25), AZURE),
        ('1EMA', ['A'], None, (30, -60, 44), ('x', 30), PORCELAIN),
        ('1K4C', ['C'], ['1', '2', '3', '4'], (128, -15, -44), ('y', 20), PORCELAIN),
        ('AF-P04637-F1', None, None, (-92, -50, -56), ('z', 60), AZURE),
    ]
    everything, markers = [], []
    for k, (name, chains, ops, centre, (ax, deg), tone) in enumerate(specs):
        t, _ = load(name, chains=chains, ops=ops, skip={'DGA', 'F09', 'K'} if name == '1K4C' else set())
        if name == 'AF-P04637-F1':                      # the confident core only: the DNA-binding domain
            t = St.select(t, (t['resi'] >= 94) & (t['resi'] <= 292))
        X = principal_frame(t['xyz']) @ rot(ax, deg).T + np.asarray(centre, float)
        ctx = S.shade(tone, len(X))
        S.molecule(f'M{k}', X, t, ctx, scale=0.9)
        everything.append(X)
        # one marker on the exposed, camera-facing surface of each molecule
        c = X.mean(0)
        out = X - c
        markers.append((X, c, out))
    allx = np.vstack(everything)
    aim = (allx.min(0) + allx.max(0)) / 2
    dist = S.fit(allx, aim, pct=99.5) * 0.86
    S.camera(aim, dist, az=-8, el=10, dof=0.012)
    P = []
    for X, c, out in markers:
        r = np.linalg.norm(out, axis=1)
        facing = (out @ S.direction) / (r + 1e-9)
        cand = np.nonzero((r > np.percentile(r, 75)) & (facing > 0.45))[0]
        i = int(cand[rng.integers(len(cand))]) if len(cand) else int(np.argmax(facing))
        p = X[i] + out[i] / (r[i] + 1e-9) * 2.5
        P.append(p)
    P = np.array(P)
    # A path that visits every molecule once, in order of angle around the centre as the camera sees it, so
    # the trail never crosses itself.
    right = np.cross(S.direction, (0.0, 0.0, 1.0))
    right /= np.linalg.norm(right)
    up = np.cross(right, S.direction)
    ang = np.arctan2((P - aim) @ up, (P - aim) @ right)
    P = P[np.argsort(ang)]
    marks = mesh.points_mesh(PREFIX + 'Agents', P, None, {'radius': ('FLOAT', np.full(len(P), 3.2))}, S.fx)
    am = marks.modifiers.new('Agents', 'NODES')
    am.node_group = groups.spheres(PREFIX, None, name='Agents')
    set_modifier_inputs(am, {'Material': look.glow_material(PREFIX + 'Agent', (233, 166, 60), 9.0)[0]})
    marks.visible_shadow = False
    cu = bpy.data.curves.new(PREFIX + 'Trail', 'CURVE')
    cu.dimensions, cu.bevel_depth, cu.bevel_resolution = '3D', 0.45, 3
    for a, b in zip(P[:-1], P[1:]):
        mid = (a + b) / 2 + np.array([0.0, -0.12 * np.linalg.norm(b - a), 0.10 * np.linalg.norm(b - a)])
        sp = cu.splines.new('BEZIER')
        sp.bezier_points.add(1)
        for bp, p, h in ((sp.bezier_points[0], a, a + (mid - a) * 0.6), (sp.bezier_points[1], b, b + (mid - b) * 0.6)):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = 'FREE'
            bp.handle_left = bp.handle_right = h
    trail = bpy.data.objects.new(PREFIX + 'Trail', cu)
    trail.data.materials.append(look.glow_material(PREFIX + 'TrailGlow', (233, 166, 60), 1.8)[0])
    trail.visible_shadow = False
    S.fx.objects.link(trail)
    return {'molecules': [s[0] for s in specs], 'markers': len(P)}


SHOTS = {
    'hemoglobin': ('mist', (1600, 1200), shot_hemoglobin),
    'dna': ('mist', (1600, 1200), shot_dna),
    'p53': ('mist', (1600, 1200), shot_p53),
    'p53dna': ('mist', (1600, 1200), shot_p53_dna),
    'gfp': ('mist', (1600, 1200), shot_gfp),
    'kcsa': ('mist', (1600, 1200), shot_kcsa),
    'aquaporin': ('mist', (1600, 1200), shot_aquaporin),
    'igg': ('mist', (1600, 900), shot_igg),
    'nucleosome': ('deep', (1600, 900), shot_nucleosome),
    'agents': ('deep', (1600, 1000), shot_agents),
}


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', required=True, choices=sorted(SHOTS))
    ap.add_argument('--still', required=True)
    ap.add_argument('--percent', type=int, default=100)
    ap.add_argument('--samples', type=int, default=256)
    args = ap.parse_args(argv)
    W.gpu()
    look_name, res, fn = SHOTS[args.shot]
    S = Stage(args.shot, look_name, res)
    report = {'shot': args.shot, 'look': look_name, **fn(S)}
    scene = S.finish(args.samples)
    scene.render.resolution_percentage = args.percent
    out = Path(args.still).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out)
    with bpy.context.temp_override(scene=scene):
        bpy.ops.render.render(write_still=True, scene=scene.name)
    report['still'] = str(out)
    print('RESULT ' + json.dumps(report))
