import math
from pathlib import Path

import numpy as np
import pytest

from molanim import cartoon as Ct
from molanim import electro as E
from molanim import structure as St

WEB_PDB = Path(__file__).resolve().parents[1] / 'projects' / 'website' / 'pdb'


def web(name):
    path = WEB_PDB / f'{name}.cif'
    if not path.exists():
        pytest.skip(f'{name} not in projects/website/pdb')
    t, lines = St.read_mmcif(path)
    return St.first_conformer(St.select(t, t['model'] == t['model'].min())), lines


# ----------------------------------------------------------------------------- mmCIF loops

def test_loop_reads_rows_and_single_items():
    lines = ['loop_', '_x.a', '_x.b', '1 "two words"', '3 4', '#', '_y.k 7', '_y.l "q r"', '#']
    assert St.loop(lines, '_x') == [{'a': '1', 'b': 'two words'}, {'a': '3', 'b': '4'}]
    assert St.loop(lines, '_y') == [{'k': '7', 'l': 'q r'}]
    assert St.loop(lines, '_z') == []


# ----------------------------------------------------------------------------- secondary structure

def test_deposited_secondary_structure_of_hemoglobin_is_helical():
    t, lines = web('2HHB')
    ss = Ct.secondary_structure(lines, t)
    ca = t['name'] == 'CA'
    assert (ss[ca] == Ct.HELIX).mean() > 0.7 and not (ss[ca] == Ct.STRAND).any()   # the globin fold


def test_estimate_matches_the_annotation():
    for name, code, recall in (('2HHB', Ct.HELIX, 0.85), ('1EMA', Ct.STRAND, 0.85)):
        t, lines = web(name)
        segs = Ct.protein_segments(t, Ct.secondary_structure(lines, t))
        dep = np.concatenate([s['ss'] for s in segs])
        est = np.concatenate([s['ss'] for s in Ct.protein_segments(t)])
        assert ((est == code) & (dep == code)).sum() / (dep == code).sum() > recall, name
        assert ((est == code) & (dep == code)).sum() / (est == code).sum() > 0.8, name


def test_ideal_helix_is_estimated_as_helix():
    k = np.arange(20)
    ca = np.stack([2.3 * np.cos(np.radians(100) * k), 2.3 * np.sin(np.radians(100) * k), 1.5 * k], 1)
    ss = Ct.estimate_secondary_structure(ca)
    assert (ss[2:-4] == Ct.HELIX).all()


# ----------------------------------------------------------------------------- ribbons

def test_catmull_rom_passes_through_its_points():
    p = np.random.default_rng(1).normal(size=(6, 3))
    path, par = Ct.catmull_rom(p, 8)
    assert len(path) == 5 * 8 + 1
    assert np.allclose(path[::8], p)
    assert np.allclose(par[::8], np.arange(6))


def test_ribbon_mesh_is_valid_and_sized():
    t, lines = web('1EMA')
    v, f, a, segs = Ct.cartoon(t, Ct.secondary_structure(lines, t))
    assert np.isfinite(v).all() and len(f) > 1000
    assert max(max(face) for face in f) < len(v) and min(min(face) for face in f) >= 0
    assert set(np.unique(a['ss'])) == {0.0, 1.0, 2.0}
    # Nothing strays far from the backbone: every vertex within the widest half-section of some Calpha.
    ca = np.vstack([s['ca'] for s in segs])
    d = np.min(np.linalg.norm(v[::37, None] - ca[None], axis=2), axis=1)
    assert d.max() < 4.0


def test_strand_ends_in_an_arrowhead():
    n = 8
    ca = np.stack([np.arange(n) * 3.3, np.zeros(n), np.zeros(n)], 1)
    seg = {'ca': ca, 'c': ca + [0.5, 0, 0], 'o': ca + [0.5, 1.2, 0], 'ss': np.array(['C'] * 2 + ['E'] * 5 + ['C'])}
    v, f, a = Ct.ribbon(seg, k=8)
    rings = v[:-2].reshape(-1, Ct.SIDES, 3)                       # the cross-sections, in order (caps last)
    x, width = rings[:, :, 0].mean(1), np.ptp(rings[:, :, 1], axis=1)   # width lies along the C=O (y) direction
    at = lambda pos: width[np.argmin(np.abs(x - pos))]
    assert at(3 * 3.3) == pytest.approx(2 * Ct.STRAND_SECTION[0], abs=0.05)       # strand body
    assert width.max() == pytest.approx(2 * Ct.ARROW_HALF_WIDTH, abs=0.05)         # arrowhead base
    assert at(6 * 3.3) < 0.2                                                        # arrowhead point
    assert at(5 * 3.3 + 1.6) > at(6 * 3.3 - 0.4)                                    # tapering


# ----------------------------------------------------------------------------- nucleic acids

def test_ladder_of_b_dna():
    t, _ = web('1BNA')
    v, f, a, nts = Ct.ladder(t)
    assert len(nts) == 24 and np.isfinite(v).all()
    assert set(np.unique(a['part'])) == {0.0, 1.0, 2.0}
    # Base stacking: neighbouring base-ring centroids on a strand sit about one rise apart (3.4 A in B-DNA).
    rises = []
    for chain in ('A', 'B'):
        cen = np.array([t['xyz'][n['ring']].mean(0) for n in nts if n['chain'] == chain])
        _, nrm, _ = Ct.plane(t['xyz'][[n['ring'] for n in nts if n['chain'] == chain][5]])
        rises += list(np.abs(np.diff(cen, axis=0) @ nrm))
    assert 3.0 < np.median(rises) < 3.8


def test_phosphodiester_bonds_join_the_nucleotides():
    t, _ = web('1BNA')
    e = St.bonds(t)
    names = t['name']
    o3p = [(a, b) for a, b in e if {names[a], names[b]} == {"O3'", 'P'}]
    assert len(o3p) == 22                                            # 11 per strand of 12 nucleotides
    for a, b in o3p:
        assert t['chain'][a] == t['chain'][b] and abs(t['resi'][a] - t['resi'][b]) == 1
        assert 1.5 < np.linalg.norm(t['xyz'][a] - t['xyz'][b]) < 1.7  # a P-O single bond, about 1.6 A


def test_ring_fills_two_or_three_plates_per_nucleotide():
    t, _ = web('1BNA')
    v, f, a = Ct.ring_fills(t)
    nts = Ct.nucleotides(t)
    assert np.isfinite(v).all() and max(max(face) for face in f) < len(v)
    # One sugar plate per nucleotide; one base plate per pyrimidine, two (fused) per purine. A plate of an
    # m-membered ring has 2 m + 2 vertices (both faces and their centres).
    assert len(np.unique(a['nt'][a['part'] == 0])) == len(nts) == 24
    assert (a['part'] == 1).sum() == sum(12 + 14 if n['base'] in 'AG' else 14 for n in nts)
    assert len(np.unique(a['plate'])) == sum(3 if n['base'] in 'AG' else 2 for n in nts)    # sugar + 1 or 2 base plates


def test_slab_planes_are_flat():
    t, _ = web('1BNA')
    for n in Ct.nucleotides(t):
        assert Ct.plane(t['xyz'][n['ring']])[2] < 0.1


# ----------------------------------------------------------------------------- electrostatics and pi systems

def test_formal_charges():
    t, _ = web('1BNA')
    assert E.formal_charges(t).sum() == pytest.approx(-22)          # 2 x 11 phosphates; the 5' ends have none
    t, _ = web('1KX5')
    q = E.formal_charges(t)
    dna = np.isin(t['chain'], ['I', 'J'])
    assert q[~dna & ~np.isin(t['resn'], ['CL', 'MN'])].sum() > 100  # histones: lysine- and arginine-rich
    assert q[dna].sum() < -250


def test_coulomb_potential_of_one_charge():
    # 332.06 / (4 r * r) kcal/(mol e) with a distance-dependent dielectric of 4r
    assert E.potential([[5.0, 0, 0]], [[0, 0, 0]], [1.0])[0] == pytest.approx(332.0637 / 100)
    assert E.potential([[5.0, 0, 0]], [[0, 0, 0]], [-1.0], distance_dependent=False)[0] == pytest.approx(-332.0637 / 20)


def test_potential_colors_run_red_white_blue():
    c = E.potential_colors(np.array([-20.0, 0.0, 20.0]))
    assert c[0, 0] > c[0, 2] and np.allclose(c[1], 1.0) and c[2, 2] > c[2, 0]


def test_retinal_lobes_split_only_while_c13_c14_twists(pdb):
    import c1c2 as S
    s = S.states(pdb('9GO1'), pdb('9GO2'))
    snaps, _ = S.activation_path(s, S.bonds(s), 12, 12)
    idx = [S.atom_index(s, 'RET', nm) for nm in E.RETINAL_CHAIN] + [S.atom_index(s, 296, 'NZ')]
    c13 = E.RETINAL_CHAIN.index('C13')                              # twist[c13] is the C13-C14 bond
    for k, mid in ((0, False), (6, True), (12, False), (len(snaps) - 1, False)):
        tw = E.pi_chain_lobes(snaps[k][idx])[3]
        polyene = np.delete(tw[2:], c13 - 2)                        # C7 onward, without the twisting bond
        assert polyene.max() < 15, (k, tw)                          # conjugated: neighbouring p orbitals aligned
        assert (tw[c13] > 60) == mid, (k, tw[c13])                  # halfway through the isomerisation it breaks


def test_label_data_projects_like_the_label_pass():
    from molanim import timeline as TL
    frames, res = 20, (1920, 1080)
    path = [(f, np.array([0.0, -100.0, 0.0]), np.zeros(3), 100.0, 50.0) for f in range(1, frames + 1)]
    spec = {'header': (1, 10, 'H'), 'captions': [(1, 10, 'T', 'S')], 'tags': [(1, 10, 'X-RAY')], 'times': [],
            'pointers': [(5, 12, 'centre', 'Here', (100, -50)), (5, 12, 'side', 'Region', None)]}
    d = TL.label_data(spec, path, {'centre': np.zeros(3), 'side': np.array([10.0, 0, 0])}, res, frames, 24,
                      levels=['experimental'])
    p = d['pointers'][0]
    assert p['from'] == 1 and len(p['xy']) == 12 and p['xy'][0] == [0.5, 0.5]
    assert p['offset'] == [100 / 1920, -50 / 1080] and d['pointers'][1]['region']
    x_side = d['pointers'][1]['xy'][0][0]
    assert x_side == pytest.approx(0.5 + 10 / 100 * 50 / 36, abs=1e-3)       # pinhole: x = f/z, f in sensor widths
    assert d['tags'][0]['level'] == 'experimental' and d['header']['text'] == 'H'
    assert d['shot_ink'] is None and d['layout'] == {'tags_left_from': None}
    d = TL.label_data({**spec, 'shot_ink': [(1, 'dark')], 'tags_left_from': 5}, path, {'centre': np.zeros(3), 'side': np.zeros(3)},
                      res, frames, 24, levels=['experimental'], layout={'time_prefix': ''})
    assert d['shot_ink'] == [[1, 'dark']] and d['layout'] == {'tags_left_from': 5, 'time_prefix': ''}


def test_pi_systems_are_planar():
    for name, res, count, limit in (('2HHB', {'HEM'}, 4, 0.2), ('1EMA', {'CRO'}, 1, 0.1), ('1BNA', None, 24, 0.05)):
        t, _ = web(name)
        groups = E.pi_systems(t, res)
        assert len(groups) == count, name
        for _, _, _, idx in groups:
            above, below, nrm, rms = E.pi_lobes(t['xyz'][idx])
            assert rms < limit and math.isclose(np.linalg.norm(nrm), 1.0, rel_tol=1e-6)
            assert np.allclose((above - below) @ nrm, 1.9)
