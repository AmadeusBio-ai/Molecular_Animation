"""The ART film's science (projects/art-rna/art_locus.py) must keep producing the numbers in its record.md."""
import sys

import numpy as np
import pytest

from conftest import ROOT

HERE = ROOT / 'projects' / 'art-rna'
if not (HERE / 'art_locus.py').exists():
    pytest.skip('projects/art-rna is not in this checkout', allow_module_level=True)
sys.path.insert(0, str(HERE))
import art_locus as A  # noqa: E402

WAYPOINTS = [(0, 0, 0), (700, 90, 50), (1400, -40, -40), (2100, 70, 30), (2800, -60, -30), (3500, 40, 40),
             (4200, -30, -20), (4900, 20, 10), (5600, 0, 0)]


@pytest.fixture(scope='module')
def locus():
    return A.locus()


@pytest.fixture(scope='module')
def dna():
    return A.templates(ROOT / 'assets' / 'pdb' / '1BNA.cif')


def test_excerpt_and_genes(locus):
    assert locus['first'] == 9421 and len(locus['seq']) == 3600
    assert locus['rt_start_codon'] == 'ATG' and locus['partner_start_codon'] == 'ATG'


def test_repeat_array(locus):
    assert locus['hits']['+'] == [(9598, 1), (9810, 0), (9981, 0), (10182, 0), (10358, 1)]
    assert locus['hits']['-'] == []
    rep = locus['repeats']
    assert rep['window'] == (-30, 18) and rep['length'] == 49
    assert rep['consensus'] == 'AGATATTCTATAATTAATTTTATAGACATTATATGAATACGTATAATGA'
    assert [c['identity'] for c in rep['copies']] == [0.633, 0.571, 1.0, 0.98, 0.98]
    assert locus['spacers'] == [163, 122, 152, 127]          # within the reported 120-220 nt
    assert locus['periods'] == [212, 171, 201, 176]


def test_bdna_from_sequence(locus, dna):
    tmpl, step, fit = dna
    assert sorted(tmpl) == ['A', 'C', 'G', 'T']
    assert abs(fit['twist_deg'] - 34.35) < 0.05 and abs(fit['rise_A'] - 3.362) < 0.005
    seq = A.sub(locus['seq'], locus['first'], 9568, 9616)    # repeat copy 1
    h = A.straight_helix(seq, tmpl, step)
    P = h['xyz'][h['name'] == 'P']
    assert abs(np.linalg.norm(P[:, :2], axis=1).mean() - 9.7) < 0.3   # phosphates ~9.7 A from the axis
    zc = [h['xyz'][h['bp'] == k][:, 2].mean() for k in range(len(seq))]
    assert abs(np.diff(zc).mean() - A.RISE) < 1e-6
    gaps = A.backbone_gaps(h)
    assert gaps.min() > 1.0 and gaps.max() < 2.8


def test_bending_keeps_covalent_geometry(locus, dna):
    tmpl, step, _ = dna
    h = A.straight_helix(A.sub(locus['seq'], locus['first'], 9421, 10900), tmpl, step)
    path = A.smooth_path(WAYPOINTS, 1.0)
    bent, _ = A.bend(h['xyz'], path)
    assert A.neighbour_strain(h['xyz'], bent) < 0.05


@pytest.mark.skipif(not (A.AF3 / A.JOBS['RT']).exists(), reason='AlphaFold Server output not unpacked (af3/)')
def test_alphafold_confidences():
    rep = A.confidence_report()
    assert rep['RT']['ptm'] == 0.8 and rep['RT']['mean_plddt'] == 78.2
    assert rep['PARTNER']['ptm'] == 0.21 and rep['PARTNER']['mean_plddt'] == 33.3
    assert [rep[k]['mean_plddt'] for k in ('W1', 'W2', 'W3', 'W4')] == [39.7, 45.6, 40.8, 49.5]
    assert rep['complexes'] == {'jobs': 23, 'iptm_max': 0.24, 'iptm_min': 0.07}
    t = A.model(A.JOBS['RT'])
    ca = t['name'] == 'CA'
    assert ''.join(t['resn'][ca][A.YADD[0] - 1:A.YADD[1]]) == 'TYRALAASPASP'


def test_helix_reads_as_an_atom_table_and_its_backbone_closes(locus, dna):
    from molanim import cartoon as Ct
    from molanim import structure as St
    tmpl, step, _ = dna
    seq = A.sub(locus['seq'], locus['first'], 9421, 9480)                 # 60 bp
    h = A.nucleic_table(A.straight_helix(seq, tmpl, step), seq)
    nts = Ct.nucleotides(h)
    assert len(nts) == 120 and {n['chain'] for n in nts} == {'A', 'B'}
    assert all(h['resn'][n['ring'][0]] == 'D' + n['base'] for n in nts)
    links = A.o3p_links(h)
    assert len(links) == 2 * 59                                            # 5' to 3' along both strands
    names = h['name']
    edges = [(a, b) for a, b in St.bonds(h) if {names[a], names[b]} != {"O3'", 'P'}]
    xyz, report = A.close_backbone(h, edges, links)
    d = np.linalg.norm(xyz[[a for a, _ in links]] - xyz[[b for _, b in links]], axis=1)
    assert np.allclose(d, 1.6, atol=0.01) and report['bond_change_A_max'] < 0.01
    base = ~np.isin(names, list(A.BACKBONE_NA))
    assert np.allclose(xyz[base], h['xyz'][base])                          # the bases do not move
    assert report['atom_shift_A_p95_max'][1] < 1.0
