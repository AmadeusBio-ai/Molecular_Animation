"""Website stills for the white amadeusbio.ai (late October 2026): molecules drawn for what their parts are.

Each layer of a picture stands for something physical, and nothing glows unless it emits light:
  fold        protein cartoons from the deposited secondary structure (helix ribbons, strand arrows, coil tubes);
              nucleic acids atom by atom: sticks for every bond, sugar and base rings filled, phosphate groups
              (one negative charge each) as red balls (molanim.cartoon.ring_fills, structure.bonds)
  electrons   the van der Waals envelope, a translucent skin that approximates the outer edge of the electron
              cloud; where electrostatics is the story it is coloured by the Coulombic potential of the formal
              charges (red negative, blue positive); pi lobes over conjugated rings show their shared, delocalised
              electrons (molanim.electro)
  chemistry   cofactors and chromophores in ball-and-stick, in amber (the one thing that matters in each picture)
  light       emission only where the molecule emits light: the GFP chromophore fluoresces green
The camera sees pure white (the page's own colour), so every picture sits on the page without a frame.

Structures, staging and cameras follow gallery.py (same PDB entries, assembly operators and views).

Headless (from the repo root):
  blender -b --factory-startup --python projects/website/plates.py -- --shot nucleosome --still renders/website/plates/take-01/nucleosome.png
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
sys.path[:0] = [str(HERE)]
import gallery as G  # noqa: E402  (loaders, staging helpers; imports molanim and website)

from molanim import cartoon as Ct  # noqa: E402
from molanim import electro as E  # noqa: E402
from molanim import membrane  # noqa: E402
from molanim import pathway as Pw  # noqa: E402
from molanim import structure as St  # noqa: E402
from molanim.blender import groups, look, mesh, rig  # noqa: E402
from molanim.blender import scene as SC  # noqa: E402
from molanim.blender.nodes import set_modifier_inputs  # noqa: E402
from molanim.color import lin  # noqa: E402

W = G.W
PREFIX = 'WPL_'

# ----------------------------------------------------------------------------- palette (sRGB 0-255)
# Chains take ramps from the brand's navy and the hero's blues (dark at the N-terminus, lighter toward the C).
NAVY = ((16, 44, 92), (52, 98, 168))
AZURE = ((47, 109, 181), (138, 182, 234))
STEEL = ((51, 81, 119), (122, 148, 184))
SKY = ((92, 150, 214), (176, 208, 242))
SLATE_DNA = ((92, 112, 140), (150, 166, 190))
PALE = (204, 212, 221)
AMBER = (233, 166, 60)
ELEMENT = {'C': None, 'N': (58, 92, 196), 'O': (206, 68, 60), 'S': (226, 186, 40), 'P': (236, 150, 60),
           'FE': (178, 82, 34), 'ZN': (150, 158, 170)}
PI_BLUE = (104, 146, 228)        # pi lobes over bases and side chains
PHOSPHATE = (192, 62, 56)        # a phosphate group: one negative charge, in the potential scale's red
FLUOR_GREEN = (58, 196, 110)     # the GFP chromophore's own emission (about 509 nm)
POTENTIAL_LIMIT = 10.0           # kcal/(mol e): the colour scale saturates at +-10

SHOTS = {}


def shot(name, res):
    def wrap(fn):
        SHOTS[name] = (res, fn)
        return fn
    return wrap


# ----------------------------------------------------------------------------- structures

def load_ss(name, chains=None, ops=None, skip=frozenset()):
    """Atom table (first model and conformer, chosen chains, assembly copies) and per-atom secondary structure
    from the deposited annotation, matched before the copies get their numbered chain ids."""
    t, lines = St.read_mmcif(PDB / f'{name}.cif', skip=St.WATERS | St.ADDITIVES | set(skip))
    t = St.first_conformer(St.select(t, t['model'] == t['model'].min()))
    if chains:
        t = St.select(t, np.isin(t['chain'], chains))
    ss = Ct.secondary_structure(lines, t)
    if ops:
        parts, sss = [], []
        for k, op in enumerate(ops):
            c = {key: v.copy() for key, v in t.items()}
            c['xyz'] = St.transform(t['xyz'], St.assembly_operator(lines, op))
            c['chain'] = np.array([f'{ch}{k}' for ch in t['chain']])
            parts.append(c)
            sss.append(ss)
        t = {key: np.concatenate([p[key] for p in parts]) for key in t}
        ss = np.concatenate(sss)
    return t, lines, ss


PDB = G.PDB


def chain_fraction(t):
    """Per-atom position of its residue along its chain, 0 at the first residue and 1 at the last."""
    u = np.zeros(len(t['name']))
    for chain in dict.fromkeys(t['chain'].tolist()):
        on = t['chain'] == chain
        r = t['resi'][on]
        u[on] = (r - r.min()) / max(1, r.max() - r.min())
    return u


def ramp(tones, u):
    a, b = np.array(lin(tones[0])), np.array(lin(tones[1]))
    return a + (b - a) * np.asarray(u)[:, None]


def element_colors(t, carbon):
    out = np.tile(np.array(lin(carbon)), (len(t['name']), 1))
    for el, rgb in ELEMENT.items():
        if rgb is not None:
            out[t['element'] == el] = lin(rgb)
    return out


# ----------------------------------------------------------------------------- the plate

class Plate:
    """One picture: scene, rig, materials and the layer builders."""

    def __init__(self, name, res):
        self.res = res
        self.scene = SC.reset_scene('Plate_' + name, PREFIX)
        self.col = SC.collection(self.scene, PREFIX + 'Main')
        self.rigc = SC.collection(self.scene, PREFIX + 'Rig')
        self.cam = bpy.data.objects.new(PREFIX + 'Camera', bpy.data.cameras.new(PREFIX + 'Camera'))
        self.rigc.objects.link(self.cam)
        self.scene.camera = self.cam
        self.aim = SC.empty(PREFIX + 'Aim', self.rigc)
        self.ribbon = look.ribbon_material(PREFIX + 'Ribbon')
        self.atom = look.attr_material(PREFIX + 'Atom', roughness=0.32, specular=0.5)
        self._env = None
        self.report = {}

    # camera, as gallery.Stage
    def camera(self, aim, dist, az, el, lens=50, dof=0.006):
        a, e = math.radians(az), math.radians(el)
        self.direction = np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
        aim = np.asarray(aim, float)
        rig.bake_camera(self.cam, self.aim, [(1, aim + dist * self.direction, aim, dist, lens)], max(dof, 1e-4),
                        clip=(0.5, 60 * dist))

    def fit(self, X, aim, lens=50, margin=1.08, pct=99.7):
        r = float(np.percentile(np.linalg.norm(X - aim, axis=1), pct))
        half = math.atan(0.5 * 36.0 * min(1.0, self.res[1] / self.res[0]) / lens)
        return r / math.tan(half) * margin

    # fold
    def cartoon(self, name, t, ss, colors, material=None, min_residues=2):
        v, f, a, segs = Ct.cartoon(t, ss, per_atom={'col': colors}, min_residues=min_residues)
        obj = mesh.surface_mesh(PREFIX + name, v, f, {'col': a['col']}, self.col)
        obj.data.materials.append(material or self.ribbon)
        self.report[name] = {'segments': len(segs), 'residues': int(sum(len(s['ca']) for s in segs)),
                             'helix': int(sum((s['ss'] == Ct.HELIX).sum() for s in segs)),
                             'strand': int(sum((s['ss'] == Ct.STRAND).sum() for s in segs))}
        return obj

    def ladder(self, name, t, strand_tones, base_rgb, material=None, parts=(0, 1, 2)):
        """Ladder parts: 0 backbone tube, 1 rods, 2 base slabs (molanim.cartoon.ladder)."""
        v, f, a, nts = Ct.ladder(t)
        keep = np.isin(a['part'], parts)
        if not keep.all():
            remap = np.cumsum(keep) - 1
            f = [tuple(int(remap[i]) for i in face) for face in f if all(keep[i] for i in face)]
            v, a = v[keep], {k: val[keep] for k, val in a.items()}
        col = np.tile(np.array(lin(base_rgb)), (len(v), 1))
        back = a['part'] == 0
        for s in np.unique(a['strand']).astype(int):
            sel = back & (a['strand'] == s)
            col[sel] = ramp(strand_tones[s % len(strand_tones)], a['u'][sel])
        obj = mesh.surface_mesh(PREFIX + name, v, f, {'col': col}, self.col)
        obj.data.materials.append(material or self.ribbon)
        self.report[name] = {'nucleotides': len(nts)}
        return obj, nts

    def nucleic(self, name, t, strand_tones, base_rgb, phosphate_rgb, stick=0.24, material=None, fill=None):
        """A nucleic acid as the chain of atoms it is: a stick for every covalent bond (the backbone a zig-zag of
        sugars and phosphates, joined by phosphodiester bonds), the sugar and base rings filled as thin plates,
        and each phosphate group (P, OP1, OP2: one negative charge) as balls. Backbone atoms take their strand's
        tone, base atoms the base tone with nitrogen blue and oxygen red."""
        X = t['xyz']
        n = len(X)
        u = chain_fraction(t)
        back = np.isin(t['name'], list(G.BACKBONE_NA))
        phos = np.isin(t['name'], ['P', 'OP1', 'OP2'])
        col = element_colors(t, base_rgb)
        chains = list(dict.fromkeys(t['chain'].tolist()))
        for k, ch in enumerate(chains):
            on = (t['chain'] == ch) & back
            col[on] = ramp(strand_tones[k % len(strand_tones)], u[on])
        col[phos] = lin(phosphate_rgb)
        mat = material or self.ribbon
        edges = St.bonds(t)
        v, f, a = Ct.sticks(X, edges, stick)
        sticks = mesh.surface_mesh(PREFIX + name + 'Sticks', v, f, {'col': col[a['atom'].astype(int)]}, self.col)
        sticks.data.materials.append(mat)
        radius = np.full(n, stick)                          # every atom a joint as wide as its sticks
        radius[t['name'] == 'P'] = stick * 2.6
        radius[np.isin(t['name'], ['OP1', 'OP2'])] = stick * 1.9
        balls = mesh.points_mesh(PREFIX + name + 'Atoms', X, None,
                                 {'radius': ('FLOAT', radius), 'col': ('FLOAT_COLOR', col),
                                  'emit': ('FLOAT', np.zeros(n))}, self.col)
        m = balls.modifiers.new('Atoms', 'NODES')
        m.node_group = groups.spheres(PREFIX, None, name='NucleicAtoms')
        set_modifier_inputs(m, {'Material': material or self.atom})
        nts = Ct.nucleotides(t)
        fv, ff, fa = Ct.ring_fills(t)
        strand_of = {ch: k for k, ch in enumerate(chains)}
        fcol = np.zeros((len(fv), 3))
        for i_nt, nt in enumerate(nts):
            on = fa['nt'] == i_nt
            tone = strand_tones[strand_of[nt['chain']] % len(strand_tones)]
            fcol[on & (fa['part'] == 0)] = ramp(tone, np.full(int((on & (fa['part'] == 0)).sum()), 0.75))
            fcol[on & (fa['part'] == 1)] = lin(base_rgb)
        plates = mesh.surface_mesh(PREFIX + name + 'Rings', fv, ff, {'col': fcol}, self.col)
        plates.data.materials.append(fill or look.skin_material(PREFIX + name + 'Fill', 0.55, 0.85))
        o3p = sum(1 for i, j in edges if {t['name'][i], t['name'][j]} == {"O3'", 'P'})
        self.report[name] = {'nucleotides': len(nts), 'phosphodiester_bonds': o3p, 'phosphates': int((t['name'] == 'P').sum())}
        return sticks, nts

    # chemistry
    def ball_and_stick(self, name, t, colors, ball=0.24, stick=0.13, material=None):
        X = t['xyz']
        radius = St.radii(t['element']) * ball
        radius[np.isin(t['element'], ['FE', 'ZN', 'K'])] = 0.75
        pts = mesh.points_mesh(PREFIX + name + 'Balls', X, None,
                               {'radius': ('FLOAT', radius), 'col': ('FLOAT_COLOR', colors),
                                'emit': ('FLOAT', np.zeros(len(X)))}, self.col)
        m = pts.modifiers.new('Balls', 'NODES')
        m.node_group = groups.spheres(PREFIX, None, name='Balls')
        set_modifier_inputs(m, {'Material': material or self.atom})
        edges = St.bonds(t)
        if len(edges):
            v, f, a = Ct.sticks(X, edges, stick)
            obj = mesh.surface_mesh(PREFIX + name + 'Sticks', v, f, {'col': colors[a['atom'].astype(int)]}, self.col)
            obj.data.materials.append(material or self.ribbon)
        return pts

    def spheres(self, name, X, radius, rgb, material=None):
        X = np.asarray(X, float).reshape(-1, 3)
        pts = mesh.points_mesh(PREFIX + name, X, None, {'radius': ('FLOAT', np.broadcast_to(radius, len(X)).copy()),
                                                         'col': ('FLOAT_COLOR', np.tile(lin(rgb), (len(X), 1))),
                                                         'emit': ('FLOAT', np.zeros(len(X)))}, self.col)
        m = pts.modifiers.new('Spheres', 'NODES')
        m.node_group = groups.spheres(PREFIX, None, name='Spheres')
        set_modifier_inputs(m, {'Material': material or self.atom})
        return pts

    # electrons
    def _envelope_group(self):
        if self._env is None:
            self._env = groups.envelope(PREFIX)
        return self._env

    def skin(self, name, X, radii, material, voxel=0.6, smooth=2, offset=0.0):
        """A node-built surface around spheres (X, radii): the van der Waals envelope or pi lobes."""
        src = mesh.points_mesh(PREFIX + name + 'Src', X, None, {'radius': ('FLOAT', radii)}, self.col)
        m = src.modifiers.new('Envelope', 'NODES')
        m.node_group = self._envelope_group()
        set_modifier_inputs(m, {'Material': material, 'Voxel': voxel, 'Smooth': smooth, 'Offset': offset})
        return src

    def potential_skin(self, name, t, material, q=None, voxel=0.7, smooth=3, limit=POTENTIAL_LIMIT):
        """The van der Waals envelope of `t` coloured by the Coulombic potential of its formal charges, evaluated
        1.4 A outside the surface (as ChimeraX does), red negative, white neutral, blue positive."""
        src = self.skin(name, t['xyz'], St.radii(t['element']), material, voxel, smooth)
        bpy.context.view_layer.update()
        obj = mesh.realize(src, PREFIX + name, self.col)
        bpy.data.objects.remove(src, do_unlink=True)
        v = mesh.vertices(obj)
        nrm = np.empty(len(v) * 3, np.float32)
        obj.data.vertices.foreach_get('normal', nrm)
        q = E.formal_charges(t) if q is None else q
        phi = E.potential(v + 1.4 * nrm.reshape(-1, 3), t['xyz'], q)
        mesh.set_point_colors(obj, 'col', E.potential_colors(phi, limit))
        obj.data.materials.clear()
        obj.data.materials.append(material)
        self.report[name] = {'vertices': len(v), 'charge_e': round(float(q.sum()), 2),
                             'potential_p5_p95': [round(float(np.percentile(phi, p)), 1) for p in (5, 95)]}
        return obj

    def pi_clouds(self, name, t, systems, material, radius=0.85, offset=0.95):
        """Two lobes per conjugated group (electro.pi_lobes), drawn as smooth translucent skins."""
        pts, rms = [], []
        for _, _, _, idx in systems:
            above, below, _, r = E.pi_lobes(t['xyz'][idx], offset)
            pts += [above, below]
            rms.append(r)
        if not pts:
            return None
        P = np.vstack(pts)
        self.report[name] = {'groups': len(systems), 'plane_rms_max_A': round(max(rms), 3)}
        return self.skin(name, P, np.full(len(P), radius), material, voxel=0.12, smooth=2)

    def dotted(self, name, pairs, X, rgb, dots=5, radius=0.15):
        P = [X[a] + (X[b] - X[a]) * s for a, b in pairs for s in np.linspace(0.2, 0.8, dots)]
        return self.spheres(name, np.array(P), radius, rgb)

    def finish(self, samples):
        world, _, _ = look.gradient_world(PREFIX + 'World', (255, 255, 255), (255, 255, 255), (232, 238, 247), 0.75)
        self.scene.world = world
        dist = float(np.linalg.norm(self.cam.location - self.aim.location))
        for key, d, e, ang, rgb in (('Key', (-0.55, -0.8, 0.75), 3.0, 22, (255, 247, 238)),
                                    ('Fill', (0.7, -0.8, 0.05), 0.9, 30, (226, 236, 255)),
                                    ('Rim', (0.35, 0.9, 0.55), 2.2, 12, (255, 255, 255))):
            SC.sun(PREFIX + key, d, e, ang, self.rigc, rgb, distance=3 * dist)
        SC.cycles_settings(self.scene, self.res, 1, 24, samples=samples, bounces=(8, 4, 4), transparent=32)
        self.scene.render.use_compositing = False
        self.scene.frame_set(1)
        return self.scene


# ----------------------------------------------------------------------------- shots

def protein_colors(t, tones_by_chain, default=NAVY):
    u = chain_fraction(t)
    out = np.zeros((len(u), 3))
    for chain in dict.fromkeys(t['chain'].tolist()):
        on = t['chain'] == chain
        out[on] = ramp(tones_by_chain.get(chain, default), u[on])
    return out


@shot('hemoglobin', (2000, 1500))
def shot_hemoglobin(P):
    t, _, ss = load_ss('2HHB', chains=['A', 'B', 'C', 'D'])
    t['xyz'] = G.principal_frame(t['xyz'])
    heme = t['resn'] == 'HEM'
    prot = St.select(t, ~heme)
    cols = protein_colors(prot, {'A': NAVY, 'C': NAVY, 'B': AZURE, 'D': AZURE})
    P.cartoon('Globins', prot, ss[~heme], cols)
    h = St.select(t, heme)
    P.ball_and_stick('Hemes', h, element_colors(h, AMBER))
    P.pi_clouds('HemePi', h, E.pi_systems(h, {'HEM'}), look.skin_material(PREFIX + 'PiAmber', 0.28, 0.65, AMBER))
    P.skin('Envelope', prot['xyz'], St.radii(prot['element']), look.skin_material(PREFIX + 'Skin', 0.035, 0.3, (172, 192, 226)),
           voxel=0.7, smooth=3)
    aim = np.zeros(3)
    P.camera(aim, P.fit(t['xyz'], aim) * 1.02, az=-28, el=16, dof=0.006)
    return {'atoms': len(t['name']), 'heme_atoms': int(heme.sum())}


@shot('dna', (2000, 1500))
def shot_dna(P):
    t, _, _ = load_ss('1BNA', chains=['A', 'B'])
    t['xyz'] = G.principal_frame(t['xyz']) @ G.rot('y', 32).T
    X = t['xyz']
    # Atom by atom: the hydrogen bonds join atoms, and the backbone is a chain of sugars and phosphates.
    _, nts = P.nucleic('Duplex', t, [NAVY, STEEL], (190, 202, 218), PHOSPHATE, stick=0.2)
    P.pi_clouds('BasePi', t, E.pi_systems(t), look.skin_material(PREFIX + 'PiBlue', 0.1, 0.4, PI_BLUE), radius=0.72,
                offset=0.9)
    # Watson-Crick hydrogen bonds, measured as in gallery.shot_dna: canonical donor-acceptor pairs under 3.4 A.
    wc = {('DG', 'DC'): [('N1', 'N3'), ('N2', 'O2'), ('O6', 'N4')], ('DA', 'DT'): [('N1', 'N3'), ('N6', 'O4')]}
    wc.update({(b, a): [(y, x) for x, y in v] for (a, b), v in list(wc.items())})
    strand_a = t['chain'] == 'A'

    def atom(ch, ri, nm):
        k = np.nonzero((t['chain'] == ch) & (t['resi'] == ri) & (t['name'] == nm))[0]
        return int(k[0]) if len(k) else None

    def resn(ch, ri):
        return t['resn'][(t['chain'] == ch) & (t['resi'] == ri)][0]

    def hub(ch, ri):
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
    P.dotted('HBonds', [(a, b) for a, b, _ in pairs], X, AMBER, dots=4, radius=0.17)
    # Base stacking: the rise between neighbouring base-pair centres along the helix.
    aim = np.zeros(3)
    P.camera(aim, P.fit(X, aim) * 1.0, az=18, el=6, dof=0.006)
    dist = [p[2] for p in pairs]
    return {'atoms': len(X), 'nucleotides': len(nts), 'hbonds': len(pairs),
            'hbond_A': [round(min(dist), 2), round(float(np.mean(dist)), 2), round(max(dist), 2)]}


@shot('p53dna', (2000, 1500))
def shot_p53_dna(P):
    t, lines = St.read_mmcif(G.AF3 / f'{G.AF3_JOB}_model_0.cif')
    plddt = G.bfactors(lines)
    ss = Ct.secondary_structure(lines, t)
    dna = np.isin(t['chain'], ['I', 'J'])
    prot = np.isin(t['chain'], list('ABCD'))
    zinc = t['resn'] == 'ZN'
    tet = prot & (t['resi'] >= 325) & (t['resi'] <= 356)
    dbd = prot & (t['resi'] >= 94) & (t['resi'] <= 292)
    D = t['xyz'][dna]
    c = D.mean(0)
    _, V = np.linalg.eigh((D - c).T @ (D - c))
    ex = V[:, -1]
    v = t['xyz'][tet].mean(0) - c
    ez = v - (v @ ex) * ex
    ez /= np.linalg.norm(ez)
    ey = np.cross(ez, ex)
    t['xyz'] = (t['xyz'] - c) @ np.stack([ex, ey, ez]).T
    X = t['xyz']
    # pLDDT per residue (the Calpha's), so a residue is either confident or not.
    sure = prot & (plddt >= 70)
    bands = [(90, 101, NAVY), (70, 90, AZURE)]
    sub = St.select(t, sure)
    cols = np.zeros((int(sure.sum()), 3))
    for lo, hi, tones in bands:
        on = (plddt[sure] >= lo) & (plddt[sure] < hi)
        cols[on] = ramp(tones, np.full(on.sum(), 0.4))
    # The AlphaFold Server model carries no secondary-structure annotation: estimate it from Calpha geometry.
    P.cartoon('Confident', sub, ss[sure] if (ss != Ct.COIL).any() else None, cols)
    unsure = prot & (plddt < 70)
    loose = St.select(t, unsure)
    # The low-confidence chain is drawn faint, and fades into the page with distance from the DNA-binding core,
    # so its long loops end inside the picture instead of at its edge.
    core_c = (X[dbd].min(0) + X[dbd].max(0)) / 2
    fade = np.clip((np.linalg.norm(loose['xyz'] - core_c, axis=1) - 38.0) / 26.0, 0, 1)[:, None]
    P.cartoon('Uncertain', loose, np.full(int(unsure.sum()), Ct.COIL),
              np.array(lin((176, 194, 224))) * (1 - fade) + fade, look.skin_material(PREFIX + 'Loose', 0.28, 0.6))
    assert (plddt[dna] < 70).all(), 'some DNA is >= pLDDT 70: draw it solid'
    amber = look.skin_material(PREFIX + 'DnaGhost', 0.5, 0.85)
    P.nucleic('DNA', St.select(t, dna), [((226, 150, 44), (238, 182, 96))] * 2, (246, 214, 160), (222, 136, 36),
              stick=0.26, material=amber, fill=look.skin_material(PREFIX + 'DnaGhostFill', 0.35, 0.7))
    P.spheres('Zinc', X[zinc], 0.74, ELEMENT['ZN'])
    aim = (X[dbd].min(0) + X[dbd].max(0)) / 2
    core = np.concatenate([X[dbd | tet | dna], X[prot][::7]])
    P.camera(aim, P.fit(core, aim, pct=97.0) * 0.92, az=66, el=20, dof=0.004)
    return {'atoms': len(X), 'confident_atoms': int(sure.sum()), 'zinc': int(zinc.sum())}


@shot('gfp', (2000, 1500))
def shot_gfp(P):
    t, _, ss = load_ss('1EMA', chains=['A'])
    t['xyz'] = G.principal_frame(t['xyz'])
    X = t['xyz']
    cro = t['resn'] == 'CRO'
    focus = X[cro].mean(0)
    az, el = -14, 10
    a, e = math.radians(az), math.radians(el)
    d = np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
    # Cutaway: residues whose Calpha lies in front of the chromophore, near the line of sight, are left out.
    ca_res = {}
    for k in np.nonzero(t['name'] == 'CA')[0]:
        ca_res[(t['chain'][k], t['resi'][k])] = X[k]
    front = np.zeros(len(X), bool)
    for (ch, r), p in ca_res.items():
        v = p - focus
        along = v @ d
        perp = np.linalg.norm(v - along * d)
        if along > 3.0 and perp < 15.0:
            front |= (t['chain'] == ch) & (t['resi'] == r)
    keep = ~cro & ~front
    sub = St.select(t, keep)
    P.cartoon('Barrel', sub, ss[keep], protein_colors(sub, {'A': NAVY}), min_residues=4)
    ch = St.select(t, cro)
    P.ball_and_stick('Chromophore', ch, element_colors(ch, (120, 214, 150)))
    mat, _ = look.fluorescence_material(PREFIX + 'Fluor', FLUOR_GREEN, 2.5, opacity=0.4)
    P.pi_clouds('ChromophorePi', ch, E.pi_systems(ch, {'CRO'}), mat)
    P.camera(focus, 104.0, az=az, el=el, dof=0.006)
    return {'atoms': len(X), 'chromophore_atoms': int(cro.sum()), 'residues_cut_away': len({(c, r) for c, r in zip(
        t['chain'][front], t['resi'][front])})}


@shot('kcsa', (2000, 1500))
def shot_kcsa(P):
    t, lines, ss = load_ss('1K4C', chains=['C'], ops=['1', '2', '3', '4'], skip={'DGA', 'F09'})
    axis, point = G.operator_axis(lines, '2')
    ions = t['resn'] == 'K'
    keep = np.ones(len(ions), bool)
    idx = np.nonzero(ions)[0]
    for a_i, a in enumerate(idx):
        for b in idx[:a_i]:
            if keep[b] and np.linalg.norm(t['xyz'][a] - t['xyz'][b]) < 0.8:
                keep[a] = False
    t, ss = St.select(t, keep), ss[keep]
    ions = t['resn'] == 'K'
    origin = t['xyz'][ions].mean(0)
    t['xyz'] = G.principal_frame(t['xyz'], up=axis, origin=origin)
    X = t['xyz']
    prot = ~ions
    copy = np.array([int(c[-1]) if c[-1].isdigit() else -1 for c in t['chain']])
    # Two opposite subunits of the four, so the pore between them is in view (as in the classic KcsA figures).
    pair = prot & np.isin(copy, [0, 2])
    sub = St.select(t, pair)
    P.cartoon('Channel', sub, ss[pair], protein_colors(sub, {'C0': NAVY, 'C2': AZURE}))
    # Pore: free-radius profile along the four-fold axis, from all four subunits (gallery.shot_kcsa).
    vdw = St.radii(t['element'][prot])
    zs = np.arange(X[prot][:, 2].min() + 2, X[prot][:, 2].max() - 2, 1.0)
    centres, free = Pw.pore_profile(X[prot], vdw, [(0.0, 0.0, zs[0]), (0.0, 0.0, zs[-1])], zs, axis=2)
    line = Pw.polyline(Pw.relax_path(centres, X[prot], vdw, axis=2), spacing=0.5, smooth=2)
    r = Pw.clearance(line, X[prot], vdw)
    r = np.convolve(np.pad(r, 2, mode='edge'), np.ones(5) / 5, mode='valid')
    P.skin('Pore', line, np.clip(r, 0.3, None), look.skin_material(PREFIX + 'Pore', 0.22, 0.6, (150, 196, 246)),
           voxel=0.25, smooth=2)
    P.spheres('Potassium', X[ions], 1.33, AMBER)
    P.camera(np.array([0.0, 0.0, -6.0]), 158.0, az=0, el=4, dof=0.005)
    return {'protein_atoms_shown': int(pair.sum()), 'k_ions': int(ions.sum()),
            'pore_min_free_radius_A': round(float(r.min()), 2), 'pore_max_free_radius_A': round(float(r.max()), 2)}


@shot('aquaporin', (2000, 1500))
def shot_aquaporin(P):
    t, lines, ss = load_ss('1J4N', chains=['A'], ops=['1', '2', '3', '4'])
    axis, point = G.operator_axis(lines, '2')
    c = t['xyz'].mean(0)
    origin = point + axis * float((c - point) @ axis)
    t['xyz'] = G.principal_frame(t['xyz'], up=axis, origin=origin)
    X = t['xyz']
    P.cartoon('Tetramer', t, ss, protein_colors(t, {'A0': NAVY, 'A1': AZURE, 'A2': NAVY, 'A3': AZURE}))
    # A round patch of bilayer that ends inside the frame (the picture shares the page's white), cut in front.
    patch = 98.0
    mem = membrane.bilayer((-patch, patch, 4.0, 2 * patch), X, seed=5,
                           keep=lambda p: (p[1] > 4.0) & (np.hypot(p[0], p[1]) < patch))
    head = mem['part'] == 'head'
    rng = np.random.default_rng(3)
    shade = rng.uniform(0, 1, len(head))[:, None]
    hc = np.array(lin((176, 190, 210))) + (np.array(lin((214, 222, 233))) - np.array(lin((176, 190, 210)))) * shade
    tc = np.array(lin((222, 228, 236))) + (np.array(lin((240, 243, 247))) - np.array(lin((222, 228, 236)))) * shade
    rim = np.clip((np.hypot(mem['xyz'][:, 0], mem['xyz'][:, 1]) - 0.7 * patch) / (0.3 * patch), 0, 1)[:, None]
    lip = mesh.points_mesh(PREFIX + 'Membrane', mem['xyz'], None,
                           {'radius': ('FLOAT', St.radii(mem['element']) * np.where(head, 0.62, 0.78)),
                            'col': ('FLOAT_COLOR', np.where(head[:, None], hc, tc) * (1 - rim) + rim),
                            'emit': ('FLOAT', np.zeros(len(head)))}, P.col)
    lm = lip.modifiers.new('Lipids', 'NODES')
    lm.node_group = groups.spheres(PREFIX, None)
    set_modifier_inputs(lm, {'Material': look.attr_material(PREFIX + 'Lipid', roughness=0.5, specular=0.3)})
    P.camera(np.array([0.0, 10.0, -2.0]), 360.0, az=-22, el=18, dof=0.006)
    return {'atoms': len(X), 'lipids': int(mem['count'])}


@shot('igg', (2000, 1125))
def shot_igg(P):
    t, _, ss = load_ss('1IGT')
    t['xyz'] = G.principal_frame(t['xyz'])
    X = t['xyz']
    sugar = np.isin(t['resn'], list(G.SUGARS))
    prot = St.select(t, ~sugar)
    P.cartoon('Antibody', prot, ss[~sugar], protein_colors(prot, {'B': NAVY, 'D': STEEL, 'A': AZURE, 'C': SKY}))
    P.skin('Envelope', prot['xyz'], St.radii(prot['element']), look.skin_material(PREFIX + 'Skin', 0.05, 0.38, (172, 192, 226)),
           voxel=0.8, smooth=3)
    s = St.select(t, sugar)
    P.ball_and_stick('Glycans', s, element_colors(s, AMBER))
    aim = np.zeros(3)
    P.camera(aim, P.fit(X, aim) * 0.98, az=-12, el=8, dof=0.005)
    return {'atoms': len(X), 'glycan_atoms': int(sugar.sum())}


@shot('nucleosome', (3200, 1800))
def shot_nucleosome(P):
    """The call to action: the nucleosome as the electrostatic object it is. Histones carry many lysines and
    arginines (positive, blue), the DNA its phosphates (negative, red); the skin shows the potential."""
    t, _, ss = load_ss('1KX5')
    t['xyz'] = G.principal_frame(t['xyz'])
    X = t['xyz']
    dna = np.isin(t['chain'], ['I', 'J'])
    ion = np.isin(t['resn'], ['CL', 'MN'])
    hist = ~dna & ~ion
    tones = {'A': NAVY, 'E': NAVY, 'B': AZURE, 'F': AZURE, 'C': STEEL, 'G': STEEL, 'D': SKY, 'H': SKY}
    h = St.select(t, hist)
    P.cartoon('Histones', h, ss[hist], protein_colors(h, tones))
    # The histone spool's van der Waals envelope, coloured by the histones' own potential: lysines and arginines
    # make it positive (blue) where the DNA lies; acidic residues show red.
    P.potential_skin('HistonePotential', h, look.skin_material(PREFIX + 'PotentialSkin', 0.42, 0.85), voxel=0.75,
                     smooth=3)
    # The DNA's charge is on its phosphate backbone: the strands take the same red as negative potential.
    # The DNA atom by atom; its phosphate groups, one negative charge each, in the potential's red.
    P.nucleic('DNA', St.select(t, dna), [STEEL, SLATE_DNA], (206, 214, 226), PHOSPHATE, stick=0.3)
    aim = X[hist & (t['name'] == 'CA')].mean(0)                  # the histone core, so the disc sits centred
    P.camera(aim, P.fit(X, aim, pct=99.9) * 0.84, az=-12, el=14, dof=0.003)   # near face-on: the DNA wraps the spool
    body = St.select(t, ~ion)
    q = E.formal_charges(body)
    on_dna = np.isin(body['chain'], ['I', 'J'])
    return {'atoms': len(X), 'dna_atoms': int(dna.sum()), 'histone_charge_e': round(float(q[~on_dna].sum()), 1),
            'dna_charge_e': round(float(q[on_dna].sum()), 1)}


@shot('agents', (2000, 1250))
def shot_agents(P):
    rng = np.random.default_rng(5)
    specs = [  # as gallery.shot_agents: (structure, chains, ops, centre, extra rotation, tones)
        ('1KX5', None, None, (-112, 50, 22), ('x', 70), AZURE),
        ('2HHB', ['A', 'B', 'C', 'D'], None, (-18, -25, -34), ('z', 20), NAVY),
        ('1IGT', None, None, (96, 55, 26), ('z', -25), AZURE),
        ('1EMA', ['A'], None, (30, -60, 44), ('x', 30), NAVY),
        ('1K4C', ['C'], ['1', '2', '3', '4'], (128, -15, -44), ('y', 20), NAVY),
        ('AF-P04637-F1', None, None, (-92, -50, -56), ('z', 60), AZURE),
    ]
    everything, markers = [], []
    skin = look.skin_material(PREFIX + 'Skin', 0.06, 0.42, (172, 192, 226))
    for k, (name, chains, ops, centre, (ax, deg), tones) in enumerate(specs):
        t, _, ss = load_ss(name, chains=chains, ops=ops, skip={'DGA', 'F09', 'K'} if name == '1K4C' else set())
        if name == 'AF-P04637-F1':
            on = (t['resi'] >= 94) & (t['resi'] <= 292)
            t, ss = St.select(t, on), ss[on]
        t['xyz'] = G.principal_frame(t['xyz']) @ G.rot(ax, deg).T + np.asarray(centre, float)
        nuc = np.isin(t['resn'], list(Ct.NUCLEOTIDES))
        prot = St.select(t, ~nuc)
        P.cartoon(f'M{k}', prot, ss[~nuc], protein_colors(prot, {}, tones))
        P.skin(f'M{k}Skin', t['xyz'], St.radii(t['element']), skin, voxel=1.0, smooth=3)
        if nuc.any():
            P.nucleic(f'M{k}DNA', St.select(t, nuc), [STEEL, SLATE_DNA], (206, 214, 226), PHOSPHATE, stick=0.45)
        X = t['xyz']
        everything.append(X)
        c = X.mean(0)
        markers.append((X, c, X - c))
    allx = np.vstack(everything)
    aim = (allx.min(0) + allx.max(0)) / 2
    P.camera(aim, P.fit(allx, aim, pct=99.5) * 0.86, az=-8, el=10, dof=0.008)
    pts = []
    for X, c, out in markers:
        r = np.linalg.norm(out, axis=1)
        facing = (out @ P.direction) / (r + 1e-9)
        cand = np.nonzero((r > np.percentile(r, 75)) & (facing > 0.45))[0]
        i = int(cand[rng.integers(len(cand))]) if len(cand) else int(np.argmax(facing))
        pts.append(X[i] + out[i] / (r[i] + 1e-9) * 2.5)
    pts = np.array(pts)
    right = np.cross(P.direction, (0.0, 0.0, 1.0))
    right /= np.linalg.norm(right)
    up = np.cross(right, P.direction)
    pts = pts[np.argsort(np.arctan2((pts - aim) @ up, (pts - aim) @ right))]
    P.spheres('Agents', pts, 3.0, AMBER)
    cu = bpy.data.curves.new(PREFIX + 'Trail', 'CURVE')
    cu.dimensions, cu.bevel_depth, cu.bevel_resolution = '3D', 0.45, 3
    for a, b in zip(pts[:-1], pts[1:]):
        mid = (a + b) / 2 + np.array([0.0, -0.12 * np.linalg.norm(b - a), 0.10 * np.linalg.norm(b - a)])
        sp = cu.splines.new('BEZIER')
        sp.bezier_points.add(1)
        for bp, p, hnd in ((sp.bezier_points[0], a, a + (mid - a) * 0.6), (sp.bezier_points[1], b, b + (mid - b) * 0.6)):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = 'FREE'
            bp.handle_left = bp.handle_right = hnd
    trail = bpy.data.objects.new(PREFIX + 'Trail', cu)
    trail.data.materials.append(look.flat_material(PREFIX + 'TrailMat', AMBER, roughness=0.4))
    P.col.objects.link(trail)
    return {'molecules': [s[0] for s in specs], 'markers': len(pts)}


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', required=True, choices=sorted(SHOTS))
    ap.add_argument('--still', required=True)
    ap.add_argument('--percent', type=int, default=100)
    ap.add_argument('--samples', type=int, default=256)
    args = ap.parse_args(argv)
    W.gpu()
    res, fn = SHOTS[args.shot]
    P = Plate(args.shot, res)
    report = {'shot': args.shot, 'res': list(res), **fn(P)}
    scene = P.finish(args.samples)
    report['layers'] = P.report
    scene.render.resolution_percentage = args.percent
    out = Path(args.still).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out)
    with bpy.context.temp_override(scene=scene):
        bpy.ops.render.render(write_still=True, scene=scene.name)
    report['still'] = str(out)
    print('RESULT ' + json.dumps(report))
