"""A procedural POPC-like lipid bilayer, for membrane context (not a simulation).

Stage convention: membrane centre at z = 0, normal +z (choose which side is extracellular in the shot).
Lipids that clash with the protein are dropped, so place the protein in the bilayer first.
"""
import math

import numpy as np


def _lipid_template(rng):
    """One POPC-like lipid in leaflet coordinates (z toward the water, P at the origin).

    Head group, phosphate, glycerol and ester atoms are placed by hand; the palmitoyl (sn-1, 16 C)
    and oleoyl (sn-2, 18 C, cis C9=C10) chains are zig-zags along a meandering axis that heads
    for the bilayer centre. Returns xyz, elements and part labels ('head' or 'tail')."""
    head = np.array([
        (0, 0, 0), (0.6, -1.2, 0.6), (-1.3, -0.2, 0.6), (0.9, 1.1, 0.6), (0.2, 0.3, -1.5),   # P, O13, O14, O12, O11
        (2.2, 1.0, 1.2), (2.9, 2.2, 1.9), (4.3, 2.0, 2.4),                                     # C11, C12, N
        (4.6, 0.6, 2.9), (5.0, 2.3, 1.1), (4.7, 3.0, 3.4),                                     # methyls
        (-0.6, 1.2, -2.3), (-0.1, 1.3, -3.7), (-1.2, 1.9, -4.6),                               # glycerol C1-C3
        (1.1, 2.1, -3.8), (2.1, 1.6, -4.5), (2.0, 0.5, -5.0),                                  # O21, C21, O22
        (-1.6, 3.2, -4.2), (-2.0, 3.9, -5.2), (-2.2, 3.4, -6.3)], float)                       # O31, C31, O32
    # Swing the choline about the phosphate so head groups don't all point the same way.
    a = rng.uniform(-0.6, 0.6)
    R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    head[5:11] = head[5:11] @ R.T
    elements = ['P', 'O', 'O', 'O', 'O', 'C', 'C', 'N', 'C', 'C', 'C', 'C', 'C', 'C', 'O', 'C', 'O', 'O', 'C', 'O']
    tails = []
    for start, count, kink in ((head[15], 17, 8), (head[18], 15, None)):
        tails.append(_tail(rng, start, count, kink))
    xyz = np.vstack([head, *tails])
    elements += ['C'] * sum(len(t) for t in tails)
    part = ['head'] * len(head) + ['tail'] * (len(xyz) - len(head))
    return xyz, np.array(elements), np.array(part)


def _tail(rng, start, count, kink, depth=17.5):
    for _ in range(200):
        tilt = rng.uniform(0, 0.45)
        phi = rng.uniform(0, 2 * math.pi)
        u = np.array([math.sin(tilt) * math.cos(phi), math.sin(tilt) * math.sin(phi), -math.cos(tilt)])
        side = np.cross(u, (1, 0, 0))
        side /= np.linalg.norm(side)
        pts, p = [], np.array(start, float)
        for k in range(count):
            if k == kink:                                   # cis double bond: a 30 deg bend
                u = _rotate(u, np.cross(u, side), math.radians(rng.choice((-1, 1)) * 30))
            elif rng.random() < 0.18 + 0.03 * k:            # gauche defects, more toward the chain end
                u = _rotate(u, _perp(u, rng), math.radians(rng.uniform(15, 40)))
            u = u + np.array((0, 0, -0.12))                 # lipids stay aligned with the normal
            u /= np.linalg.norm(u)
            side = side - (side @ u) * u
            side /= np.linalg.norm(side)
            p = p + 1.26 * u
            pts.append(p + (0.42 if k % 2 else -0.42) * side)
        pts = np.array(pts)
        if -depth + 0.5 < pts[-1, 2] < -depth + 4.0 and pts[:, 2].min() > -depth - 0.5:
            return pts
    return pts


def _perp(u, rng):
    v = np.cross(u, rng.normal(size=3))
    return v / np.linalg.norm(v)


def _rotate(v, axis, angle):
    axis = axis / np.linalg.norm(axis)
    return v * math.cos(angle) + np.cross(axis, v) * math.sin(angle) + axis * (axis @ v) * (1 - math.cos(angle))


def bilayer(bounds, protein_xyz, seed=0, spacing=8.6, phosphate_z=19.5, clearance=3.0, templates=48, keep=None):
    """POPC-like bilayer over `bounds` = (x0, x1, y0, y1).

    Lipids sit on a jittered hexagonal grid (~64 A^2 per lipid, P-P ~39 A). A lipid is dropped if its head
    group clashes with the protein; clashing tail atoms are removed individually. `keep(p_xy)` can veto
    lipids by their phosphate position (e.g. a section cut). Returns xyz, element, part ('head'/'tail'),
    leaflet (+1 upper, -1 lower), lipid id, and the lipid count."""
    rng = np.random.default_rng(seed)
    lib = [_lipid_template(rng) for _ in range(templates)]
    x0, x1, y0, y1 = bounds
    occ = occupancy(protein_xyz, clearance)
    out = {k: [] for k in ('xyz', 'element', 'part', 'leaflet', 'lipid')}
    lipid = 0
    for leaflet in (1, -1):
        rows = np.arange(y0, y1, spacing * math.sqrt(3) / 2)
        for r, y in enumerate(rows):
            for x in np.arange(x0 + (r % 2) * spacing / 2 + leaflet * 2.1, x1, spacing):
                p = np.array((x, y)) + rng.normal(scale=1.1, size=2)
                if keep is not None and not keep(p):
                    continue
                xyz, el, part = lib[rng.integers(templates)]
                a = rng.uniform(0, 2 * math.pi)
                R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
                pos = xyz @ R.T
                pos[:, 2] += phosphate_z + rng.normal(scale=0.8)
                if leaflet < 0:
                    pos[:, 1] *= -1
                    pos[:, 2] *= -1
                pos[:, :2] += p
                hit = occ(pos)
                if hit[part == 'head'].any() or hit.sum() > 8:
                    continue
                ok = ~hit
                n = int(ok.sum())
                out['xyz'].append(pos[ok])
                out['element'].append(el[ok])
                out['part'].append(part[ok])
                out['leaflet'].append(np.full(n, leaflet))
                out['lipid'].append(np.full(n, lipid))
                lipid += 1
    res = {k: np.concatenate(v) for k, v in out.items()}
    res['count'] = lipid
    return res


def occupancy(xyz, clearance, voxel=1.0):
    """Function: points -> bool, True within `clearance` (+ half a voxel) of any atom in `xyz`."""
    lo = xyz.min(0) - clearance - 2
    shape = np.ceil((xyz.max(0) + clearance + 2 - lo) / voxel).astype(int) + 1
    grid = np.zeros(shape, bool)
    r = int(math.ceil(clearance / voxel))
    offs = np.array([(a, b, c) for a in range(-r, r + 1) for b in range(-r, r + 1) for c in range(-r, r + 1)
                     if a * a + b * b + c * c <= (clearance / voxel + 0.5) ** 2])
    idx = np.rint((xyz - lo) / voxel).astype(int)
    for o in offs:
        q = np.clip(idx + o, 0, shape - 1)
        grid[q[:, 0], q[:, 1], q[:, 2]] = True

    def test(points):
        q = np.rint((np.asarray(points) - lo) / voxel).astype(int)
        inside = np.all((q >= 0) & (q < shape), axis=1)
        out = np.zeros(len(q), bool)
        qi = q[inside]
        out[inside] = grid[qi[:, 0], qi[:, 1], qi[:, 2]]
        return out
    return test
