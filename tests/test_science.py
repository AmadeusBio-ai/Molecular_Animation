"""Pure-layer science: morph, pathway, membrane, particles."""
import math

import numpy as np

from molanim import membrane, morph, particles, pathway
from molanim import structure as St


def chain(angles):
    """A zig-zag chain of 8 atoms, 1.5 A bonds, turning by `angles` (deg) in the xy-plane."""
    pts, p, heading = [np.zeros(3)], np.zeros(3), 0.0
    for a in angles:
        heading += math.radians(a)
        p = p + 1.5 * np.array([math.cos(heading), math.sin(heading), 0.0])
        pts.append(p)
    return np.array(pts)


def test_morph_keeps_bonds_and_hits_both_ends():
    A = chain([0, 60, -60, 60, -60, 60, -60])
    B = chain([0, 60, -60, 120, 60, 60, -60])                      # a twist in the middle of the chain
    edges = np.array([(k, k + 1) for k in range(len(A) - 1)])
    frames = morph.morph(A, B, edges, np.ones(len(A), bool), steps=8)
    assert len(frames) == 9 and np.allclose(frames[0], A) and np.allclose(frames[-1], B)
    assert morph.max_bond_deviation(frames, edges) < 0.25          # case study: 0.15-0.22 A for real swings
    lerp_mid = (A + B) / 2                                         # the naive midpoint shortens bonds
    naive = np.abs(np.linalg.norm(lerp_mid[edges[:, 0]] - lerp_mid[edges[:, 1]], axis=1) - 1.5).max()
    assert morph.max_bond_deviation(frames, edges) < naive / 5


def test_pore_profile_finds_the_axis_of_a_tube():
    ring = [(5 * math.cos(a), y, 5 * math.sin(a)) for y in np.arange(-10, 10.1, 1.5)
            for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    xyz = np.array(ring) + (3.0, 0.0, -2.0)
    radius = np.full(len(xyz), 1.5)
    # The search stays within `window` of the guide; in a protein, atoms surround it on all sides.
    centres, free = pathway.pore_profile(xyz, radius, guide=[(4, -12, -1), (4, 12, -1)], ys=np.arange(-6, 7, 2.0),
                                         window=2.5)
    assert np.abs(centres[:, [0, 2]] - (3.0, -2.0)).max() <= 0.5
    assert np.all(np.abs(free - 3.5) < 0.3)                        # 5 A ring - 1.5 A atom radius


def test_polyline_and_clearance():
    line = pathway.polyline([(0, 0, 0), (10, 0, 0)], spacing=0.5)
    assert len(line) == 21 and np.allclose(np.diff(pathway.arc_length(line)), 0.5)
    assert np.allclose(pathway.clearance([(0, 0, 0)], np.array([[3.0, 0, 0]]), np.array([1.0])), 2.0)


def test_bilayer_avoids_the_protein():
    rng = np.random.default_rng(0)
    protein = rng.normal(scale=6.0, size=(400, 3))
    mem = membrane.bilayer((-40, 40, -40, 40), protein, seed=1, templates=6)
    assert mem['count'] > 20
    p = mem['xyz'][mem['element'] == 'P']
    assert np.all(np.abs(np.abs(p[:, 2]) - 19.5) < 4)                # phosphates in two leaflets
    near = np.min(np.linalg.norm(mem['xyz'][:, None] - protein[None], axis=2), axis=1)
    assert near.min() > 2.0                                        # clearance 3 A, voxel tolerance


def test_transits_and_keep_clear():
    rng = np.random.default_rng(2)
    path = pathway.polyline([(0, 0, 20), (0, 0, -20)], spacing=0.5)
    tracks = particles.transits(rng, path, sites=[10.0, 25.0], entries=[30, 60], frames=200)
    assert tracks.shape == (200, 2, 3)
    assert tracks[0, 0, 2] > 20 and tracks[-1, 0, 2] < -20          # from above the mouth to below the exit
    atom = np.array([[0.4, 0.0, 0.0]])
    clear, report = particles.keep_clear(tracks, atom, need=1.7, atom_radius=np.array([1.0]))
    assert report['min_gap'][0] >= 1.7 - 0.05


def test_radii():
    assert St.radii(['C', 'N', 'XX']).tolist() == [1.7, 1.55, 1.7]
