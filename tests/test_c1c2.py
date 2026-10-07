"""The case study's science must keep producing the numbers in examples/channelrhodopsin/record.md."""
import numpy as np
import pytest

import c1c2 as S

SITES = [(140, 'CD'), (136, 'CD'), (129, 'CD'), (122, 'CD')]


@pytest.fixture(scope='module')
def states(request):
    from conftest import ROOT
    s = S.states(ROOT / 'assets/pdb/9GO1.cif', ROOT / 'assets/pdb/9GO2.cif')
    return s, S.bonds(s)


def test_states_match_atom_by_atom(states):
    s, edges = states
    assert len(s['name']) == 2321 and int(s['matched'].sum()) == 2316
    assert len(edges) == 2382


def test_retinal_twist_and_salt_bridge(states):
    s, _ = states
    ix = [S.atom_index(s, 'RET', n) for n in ('C12', 'C13', 'C14', 'C15')]
    assert round(S.St.dihedral(*(s['dark'][i] for i in ix))) == -176                     # all-trans
    assert abs(S.St.dihedral(*(s['light'][i] for i in ix)) - 0.6) < 0.5                  # 13-cis
    nz, c15 = S.atom_index(s, 296, 'NZ'), S.atom_index(s, 'RET', 'C15')
    assert abs(np.linalg.norm(s['dark'][nz] - s['dark'][c15]) - 1.33) < 0.02             # Schiff base
    k, e = S.atom_index(s, 132, 'NZ'), S.atom_index(s, 129, 'OE1')
    assert round(float(np.linalg.norm(s['dark'][k] - s['dark'][e])), 1) == 9.0
    assert round(float(np.linalg.norm(s['light'][k] - s['light'][e])), 2) == 2.66


def test_activation_path_and_pathway(states):
    s, edges = states
    snaps, report = S.activation_path(s, edges)
    assert report['twist_dihedral_deg'] == [-176, -178, 180, 175, 164, 138, 98, 64, 37, 19, 10, 4, 1]
    assert report['k132_e129_A'][0] == 9.01 and report['k132_e129_A'][-1] == 2.66
    assert report['max_bond_dev_A'] == [0.154, 0.219]
    Tm = S.stage_matrix(s, 33.0)
    line, r, sites, _ = S.pathway(s, snaps[-1], Tm, SITES)
    assert round(float(S.Pw.arc_length(line)[-1]), 1) == 89.3
    assert [round(v, 1) for v in sites] == [20.3, 27.0, 42.4, 66.9]
    assert r.min() < 0.1                                       # 9GO2's pathway is interrupted
