"""C1C2 channelrhodopsin science for the case study. Pure numpy on top of molanim; tested in tests/test_c1c2.py.

Crystal frame of 9GO1: the dimer's two-fold axis is +y, the membrane normal, pointing from the extracellular
side (N-terminus, low y) to the cytoplasm (high y).

- states(): dark (9GO1) and light-activated (9GO2 alt B, 30 % occupancy) coordinates matched atom by atom.
- activation_path(): the two-stage constrained morph (retinal + Lys296 + Trp262 first, then the network).
- pathway(): protomer A's cation pathway (slice search, elastic band, free radius) and its binding sites.
- dilation(): the illustrative conducting state (lining residues step back rigidly from the pathway).
"""
import math

import numpy as np

from molanim import morph as Mo
from molanim import pathway as Pw
from molanim import structure as St

SKIP = {'HOH', 'OLC'}               # crystal waters, monoolein from the lipidic cubic phase
LIGHT_ALT, LIGHT_OFFSET = 'B', 307  # 9GO2: alt A copies the dark state, alt B is the activated conformer, resi +307
GATE_ATOMS = {'central': [(102, 'OG'), (129, 'CD'), (297, 'CG')], 'inner': [(122, 'CD'), (173, 'NE2'), (109, 'OH')]}


def states(dark_path, light_path):
    """One protomer in both states: an atom table with 'dark', 'light', 'matched' and the dimer 'operator'."""
    dark, dark_lines = St.read_mmcif(dark_path, skip=SKIP)
    light, _ = St.read_mmcif(light_path, skip=SKIP)

    def dark_key(t, i):
        return ('RET', t['name'][i]) if t['resn'][i] == 'RET' else (int(t['resi'][i]), t['name'][i])

    def light_key(t, i):
        return ('RET', t['name'][i]) if t['resn'][i] == 'RET' else (int(t['resi'][i]) - LIGHT_OFFSET, t['name'][i])

    s = St.match_states(dark, light, dark_key, light_key, keep_other=lambda t, i: t['alt'][i] in (LIGHT_ALT, '.'))
    s['dark'], s['light'] = s['start'], s['end']
    s['operator'] = St.assembly_operator(dark_lines)
    return s


def atom_index(s, resi, name):
    """Atom of residue `resi` (a number, or 'RET' for the retinal) called `name`."""
    sel = (s['resn'] == 'RET') if resi == 'RET' else (s['resi'] == resi) & (s['resn'] != 'RET')
    return int(np.nonzero(sel & (s['name'] == name))[0][0])


def bonds(s):
    """Covalent bonds, plus the retinal Schiff-base link Lys296 NZ - C15."""
    residue = np.where(s['resn'] == 'RET', -1, s['resi'])
    link = (atom_index(s, 296, 'NZ'), atom_index(s, 'RET', 'C15'))
    return St.bonds(s, s['dark'], links=[link], residue=residue)


def stage_matrix(s, membrane_y, yaw_offset=0.0):
    """Crystal -> stage: membrane normal (-y) to +Z, dimer axis to the origin, the hero retinal facing -Y.
    `membrane_y` is the crystal y of the bilayer centre."""
    op = s['operator']
    axis_xz = op[[0, 2], 3] / 2                       # two-fold axis: x = -x + tx  ->  x = tx / 2
    R0 = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)
    t0 = -R0 @ np.array([axis_xz[0], membrane_y, axis_xz[1]])
    ret = s['resn'] == 'RET'
    chain = np.isin(s['name'], ['C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'C13', 'C14', 'C15'])
    pts = s['dark'][ret & chain] @ R0.T + t0
    normal = np.linalg.svd(pts - pts.mean(0))[2][2]
    if normal[:2] @ pts.mean(0)[:2] < 0:              # point away from the dimer axis
        normal = -normal
    yaw = math.atan2(-1, 0) - math.atan2(normal[1], normal[0]) + math.radians(yaw_offset)
    Rz = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = Rz @ R0, Rz @ t0
    return T


def activation_path(s, edges, twist_steps=12, network_steps=12):
    """Snapshots (crystal frame) of the two-stage illustrative morph: dark -> twisted retinal with Trp262
    repacked -> light-activated (9GO2 alt B). Stage 1 moves retinal, the Lys296 side chain and Trp262 together
    (the twist alone puts the C20 methyl 1.9 A into the Trp262 ring); stage 2 the atoms that still move > 0.5 A.
    Returns snapshots and a report of the checked quantities."""
    side = ~np.isin(s['name'], ['N', 'CA', 'C', 'O'])
    ret = s['resn'] == 'RET'
    k296 = (s['resi'] == 296) & ~ret
    w262 = (s['resi'] == 262) & ~ret
    mid = s['dark'].copy()
    for group, resi in ((ret | (k296 & side), 296), (w262 & side, 262)):
        bb = (s['resi'] == resi) & ~ret & np.isin(s['name'], ['N', 'CA', 'C'])
        R, t = St.kabsch(s['light'][bb], s['dark'][bb])  # light side chain on the dark backbone
        mid[group] = s['light'][group] @ R.T + t
    unit = ret | (k296 & side) | (w262 & side)
    rigid = St.torsion_pairs(edges, len(mid), np.nonzero(ret | k296)[0])
    stage1 = Mo.morph(s['dark'], mid, edges, unit, twist_steps, rigid_pairs=rigid, iterations=240)
    moving = np.linalg.norm(mid - s['light'], axis=1) > 0.5
    stage2 = Mo.morph(mid, s['light'], edges, moving, network_steps, iterations=200)
    ix = [atom_index(s, 'RET', n) for n in ('C12', 'C13', 'C14', 'C15')]
    i1, i2 = atom_index(s, 132, 'NZ'), atom_index(s, 129, 'OE1')
    report = {
        'twist_dihedral_deg': [round(St.dihedral(*(f[i] for i in ix))) for f in stage1],
        'k132_e129_A': [round(float(np.linalg.norm(f[i1] - f[i2])), 2) for f in stage2],
        'max_bond_dev_A': [round(Mo.max_bond_deviation(stage1, edges), 3), round(Mo.max_bond_deviation(stage2, edges), 3)],
        'stage2_moving_atoms': int(moving.sum()),
    }
    return stage1 + stage2[1:], report


def pathway(s, X, Tm, sites):
    """Protomer A's cation pathway in coordinates X (crystal frame): stage-frame centre line (0.5 A spacing,
    extracellular first), its free radius, the arc length of each binding site (residue, atom) and a report."""
    vdw = St.radii(s['element'])
    c = {k: X[atom_index(s, *k)] for k in [(140, 'CD'), (136, 'CD'), *GATE_ATOMS['central'], *GATE_ATOMS['inner']]}
    central = sum(c[k] for k in GATE_ATOMS['central']) / 3
    inner = sum(c[k] for k in GATE_ATOMS['inner']) / 3
    guide = [c[(140, 'CD')] + (0, -14, 0), c[(140, 'CD')], c[(136, 'CD')], central, inner, inner + (0, 16, 0)]
    ys = np.arange(8.0, 68.0, 1.0)
    both = np.vstack([X, St.transform(X, s['operator'])])
    radius = np.concatenate([vdw, vdw])
    centres, free = Pw.pore_profile(both, radius, guide, ys)
    # The widest point jumps about between slices: relax the slice centres into a smooth elastic band
    # that still seeks free space, then measure the free radius along that line.
    line_c = Pw.polyline(Pw.relax_path(centres, both, radius), spacing=0.5, smooth=2)
    r = Pw.clearance(line_c, both, radius)
    r = np.convolve(np.pad(r, 2, mode='edge'), np.ones(5) / 5, mode='valid')
    line = St.transform(line_c, Tm)
    arc = Pw.arc_length(line)
    z_line = line[:, 2]
    site_s = []
    for key in sites:
        p = St.transform(X[atom_index(s, *key)][None], Tm)[0]
        site_s.append(float(arc[np.argmin(np.abs(z_line - p[2]))]))
    return line, r, sorted(site_s), {'slice_free_radius_by_y': dict(zip(ys.astype(int).tolist(), np.round(free, 2).tolist())),
                                     'line_free_radius_every_2A': np.round(r[::4], 2).tolist()}


def dilation(s, X, line, exclude, dilate, dilate_max):
    """Illustrative conducting-state widening: per residue (side chain incl. CA, or the whole residue for
    glycine-like contacts), a rigid offset that moves its closest atom out to `dilate` A from the pathway
    line, by at most `dilate_max`."""
    out = np.zeros_like(X)
    d_all = np.min(np.linalg.norm(X[:, None] - line[None, ::2], axis=2), axis=1)
    near = d_all < dilate
    for resi in np.unique(s['resi'][near & ~exclude]):
        sel = (s['resi'] == resi) & ~exclude & ~np.isin(s['name'], ['N', 'C', 'O'])
        if not (near & sel).any():
            sel = (s['resi'] == resi) & ~exclude
        k = np.argmin(np.linalg.norm(line - X[sel].mean(0), axis=1))
        away = X[sel].mean(0) - line[k]
        away /= np.linalg.norm(away) + 1e-9
        out[sel] = away * min(dilate_max, dilate - d_all[sel].min())
    return out
