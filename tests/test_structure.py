import itertools
import math

import numpy as np

from molanim import structure as St


def test_read_mmcif_9go1(pdb):
    t, lines = St.read_mmcif(pdb('9GO1'))
    assert len(t['name']) == len(t['xyz']) > 2000
    assert set(t['element']) <= {'C', 'N', 'O', 'S'}            # hydrogens, waters and additives dropped
    assert 'HOH' not in set(t['resn']) and 'RET' in set(t['resn'])
    assert St.method(lines) == 'X-RAY DIFFRACTION'
    assert 'Channelrhodopsin' in St.title(lines)


def test_assembly_operator_is_the_dimer_two_fold(pdb):
    _, lines = St.read_mmcif(pdb('9GO1'))
    M = St.assembly_operator(lines, '2')
    assert np.allclose(M[:3, :3], np.diag([-1, 1, -1]), atol=1e-6)    # -x, y, -z + 47.2 (record.md)
    assert abs(M[2, 3] - 47.2) < 0.1


def test_item_reads_semicolon_blocks():
    lines = ['_struct.title', ';A long title', 'on two lines', ';', '_exptl.method   "ELECTRON MICROSCOPY"']
    assert St.item(lines, '_struct.title') == 'A long title on two lines'
    assert St.method(lines) == 'ELECTRON MICROSCOPY'


def test_close_pairs_matches_brute_force():
    rng = np.random.default_rng(0)
    xyz = rng.uniform(0, 12, size=(300, 3))
    i, j = St.close_pairs(xyz, 1.6)
    got = set(zip(i.tolist(), j.tolist()))
    want = {(a, b) for a, b in itertools.combinations(range(len(xyz)), 2) if np.linalg.norm(xyz[a] - xyz[b]) < 1.6}
    assert got == want


def test_bonds_of_a_protein_are_chemical(pdb):
    t = St.first_conformer(St.read_mmcif(pdb('9GO1'))[0])
    edges = St.bonds(t)
    d = np.linalg.norm(t['xyz'][edges[:, 0]] - t['xyz'][edges[:, 1]], axis=1)
    assert d.max() < 2.2 and d.min() > 1.0
    assert len(edges) > 0.95 * len(t['name'])                     # roughly one bond per heavy atom
    k = St.find(t, 'CA', resi=129)
    partners = {t['name'][b if a == k else a] for a, b in edges if k in (a, b)}
    assert {'N', 'C', 'CB'} <= partners


def test_dihedral_and_kabsch():
    p = [np.array(v, float) for v in ((1, 0, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1))]
    assert abs(St.dihedral(*p) - 90.0) < 1e-9
    rng = np.random.default_rng(1)
    P = rng.normal(size=(20, 3))
    a = 0.7
    R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Q = P @ R.T + (1, 2, 3)
    R2, t2 = St.kabsch(P, Q)
    assert np.allclose(R2, R) and np.allclose(t2, (1, 2, 3))


def test_match_states_undoes_renumbering():
    ref = {'resi': np.array([1, 1, 2]), 'name': np.array(['N', 'CA', 'N']), 'xyz': np.zeros((3, 3))}
    other = {'resi': np.array([11, 11]), 'name': np.array(['N', 'CA']), 'alt': np.array(['B', 'B']),
             'xyz': np.array([[1.0, 0, 0], [2.0, 0, 0]])}
    s = St.match_states(ref, other, lambda t, i: (int(t['resi'][i]), t['name'][i]),
                        lambda t, i: (int(t['resi'][i]) - 10, t['name'][i]), lambda t, i: t['alt'][i] == 'B')
    assert s['matched'].tolist() == [True, True, False]
    assert np.allclose(s['end'][:, 0], [1, 2, 0])
