"""molanim.dynamics: the clock, OU processes, hydrodynamics, normal modes, side-chain torsions."""
import math
from pathlib import Path

import numpy as np
import pytest

from molanim import dynamics as D
from molanim import structure as St

ROOT = Path(__file__).resolve().parents[1]


def test_clock_runs_and_holds():
    t, e = D.clock(100, 0.05)
    assert np.allclose(np.diff(t), 0.05) and np.allclose(e, 0.05)
    t, e = D.clock(200, 0.05, holds=[(80, 120, 0.0, 6)])
    assert np.allclose(e[85:115], 0.0) and np.allclose(e[:70], 0.05) and np.allclose(e[130:], 0.05)
    assert np.all(np.diff(t) >= 0) and np.ptp(t[85:115]) < 1e-9


def test_ou_statistics():
    rng = np.random.default_rng(0)
    t, e = D.clock(2000, 0.1)
    x = D.ou(rng, t, e * 0.2, (400,), sigma=2.0, tau=3.0, substeps=1)   # short exposure: the raw process
    assert abs(x.std() / 2.0 - 1) < 0.05
    lag = 30                                                      # 3 ns = tau: correlation 1/e
    rho = (x[:-lag] * x[lag:]).mean() / x.var()
    assert abs(rho - math.exp(-1)) < 0.05
    msd = ((x[1:] - x[:-1]) ** 2).mean()                         # short times: free diffusion, 2 D dt
    assert abs(msd / (2 * (4.0 / 3.0) * 0.1) - 1) < 0.1


def test_exposure_averages_out_fast_motion():
    rng = np.random.default_rng(1)
    t, e = D.clock(400, 1.0)
    fast = D.ou(rng, t, e, (300,), sigma=1.0, tau=0.02)            # 50x faster than a frame
    slow = D.ou(rng, t, e, (300,), sigma=1.0, tau=50.0)
    assert fast.std() < 0.25 and abs(slow.std() - 1.0) < 0.15


def test_triangle_shutter_smooths_diffusion():
    # Through a box, a diffusing path's velocity takes a fresh kick every frame (it jerks); a triangle of the same
    # width changes it smoothly. Both keep the RMS that exposure_factor predicts.
    t, e = D.clock(400, 0.2)

    def shown(shutter, tau, seed):
        return D.ou(np.random.default_rng(seed), t, e * 16, (300,), sigma=1.0, tau=tau, substeps=64, shutter=shutter)

    def jerk(x):
        v = np.diff(x, axis=0)
        return np.abs(np.diff(v, axis=0)).mean() / np.abs(v).mean()
    assert jerk(shown('triangle', 40.0, 4)) < 0.8 * jerk(shown('box', 40.0, 4))
    for shutter in ('box', 'triangle'):
        for tau in (0.5, 2.0, 8.0):
            assert abs(shown(shutter, tau, 5).std() / D.exposure_factor(tau, 3.2, shutter) - 1) < 0.08
    assert abs(D.exposure_factor(1e-3, 3.2, 'triangle') / math.sqrt(8e-3 / 9.6) - 1) < 0.01


def test_hydrodynamics_matches_measured_proteins():
    # Lysozyme (r_h ~ 1.9 nm): rotational correlation time ~6 ns at 25 C; GFP (r_h ~ 2.4 nm): D ~ 87-100 um^2/s.
    tau_c = 1 / (6 * D.stokes_einstein_debye(19.0))
    assert 5.0 < tau_c < 8.0
    d_gfp = D.stokes_einstein(24.0) * 1e-20 / 1e-9 * 1e12            # A^2/ns -> um^2/s
    assert 85 < d_gfp < 110


def test_anm_drops_rigid_modes_and_calibrates():
    rng = np.random.default_rng(2)
    nodes = np.cumsum(rng.normal(scale=2.2, size=(80, 3)), axis=0)   # a compact random chain
    nodes += rng.normal(scale=0.3, size=nodes.shape)
    w, v = D.anm(nodes, cutoff=12.0)
    assert w.min() > 1e-6 and v.shape == (80, 3, 80 * 3 - 6)
    flat = v.reshape(-1, v.shape[-1])
    for axis in range(3):                                         # orthogonal to rigid translations
        tr = np.zeros((80, 3))
        tr[:, axis] = 1 / math.sqrt(80)
        assert np.abs(tr.ravel() @ flat).max() < 1e-8
    w, v = w[:20], v[..., :20]
    s = D.mode_scale(w, v, 1.2)
    assert abs(math.sqrt((D.node_rmsf(w, v, s) ** 2).mean()) - 1.2) < 1e-9
    t, e = D.clock(50, 0.5)
    q = D.mode_amplitudes(rng, w, t, e, s, tau_softest=20.0)
    assert q.shape == (50, 20)


def test_chi_turns_keep_covalent_geometry():
    t, _ = St.read_mmcif(ROOT / 'assets' / 'pdb' / '9GO1.cif')
    t = St.select(t, (t['chain'] == t['chain'][0]) & (t['resi'] < 140))
    edges = St.bonds(t)
    topo = D.chi_topology(t['resn'], t['resi'], t['name'])
    rng = np.random.default_rng(3)
    chi1, chi2 = rng.normal(scale=0.4, size=(2, topo['residues']))
    X = D.apply_chi(t['xyz'], topo, chi1, chi2)
    length = lambda P: np.linalg.norm(P[edges[:, 0]] - P[edges[:, 1]], axis=1)   # noqa: E731
    assert np.abs(length(X) - length(t['xyz'])).max() < 1e-6
    back = np.isin(t['name'], ['N', 'CA', 'C', 'O', 'CB'])
    assert np.allclose(X[back], t['xyz'][back])
    moved = np.linalg.norm(X - t['xyz'], axis=1) > 0.05
    assert moved.sum() > 100 and not (moved & back).any()


def test_blended_mode_shapes_keep_bonds_better_than_rigid_residues():
    t, _ = St.read_mmcif(ROOT / 'assets' / 'pdb' / '9GO1.cif')
    t = St.select(t, (t['chain'] == t['chain'][0]) & (t['resn'] != 'RET') & np.isin(t['alt'], ['.', 'A']))
    edges = St.bonds(t)
    nodes, node_of = D.residue_nodes(t['resi'], t['name'])
    pairs = D.sequence_pairs(t['xyz'], nodes)
    w, v = D.anm(t['xyz'][nodes], 15.0, modes=20, bonded=pairs)
    q = np.random.default_rng(4).normal(size=(20, len(w))) * np.sqrt(D.mode_scale(w, v, 0.8) / w)   # thermal draws
    length = lambda P: np.linalg.norm(P[edges[:, 0]] - P[edges[:, 1]], axis=1)   # noqa: E731
    strain = {}
    for name, shapes in (('rigid', v[node_of]), ('blended', D.atom_shapes(t['xyz'], v, nodes, node_of, pairs))):
        strain[name] = np.array([np.abs(length(t['xyz'] + shapes @ qq) - length(t['xyz'])) for qq in q])
    assert strain['blended'].max() < 0.4 * strain['rigid'].max()
    assert np.percentile(strain['blended'], 99) < 0.25               # only the floppy termini strain more


def test_perrin_reduces_to_a_sphere_and_slows_rods():
    D_t, D_r = D.perrin((20.0, 20.0, 20.0))
    assert abs(D_t / D.stokes_einstein(20.0) - 1) < 0.01
    assert np.allclose(D_r / D.stokes_einstein_debye(20.0), 1, atol=0.01)
    D_t, D_r = D.perrin((100.0, 15.0, 15.0))                       # a rod of the same width
    assert D_r[1] < D_r[0] and D_r[1] < 0.05 * D.stokes_einstein_debye(15.0)


def test_wlc_bands_scale_as_the_theory():
    (r1, t1), (r2, t2) = D.wlc_bend([200.0, 400.0])
    assert abs(r2 / r1 - 2 ** 1.5) < 1e-9 and 11 < t2 / t1 < 16     # amplitude ~ lambda^1.5, time ~ lambda^4 / log
    rms, tau = D.wlc_twist(340.0)                                   # 100 bp: a few ns (Barkley-Zimm)
    assert 0.3 < rms < 0.7 and 1.0 < tau < 10.0


def test_periodic_ou_loops_seamlessly():
    rng = np.random.default_rng(6)
    t, e = D.clock(480, 0.05)                                      # a 24 ns loop
    x = D.ou(rng, t, e * 0.2, (2000,), sigma=1.5, tau=1.0, period=24.0)
    assert abs(x.std() / 1.5 - 1) < 0.05
    rho = (x * np.roll(x, -20, axis=0)).mean() / x.var()          # 1 ns = tau: correlation 1/e
    assert abs(rho - math.exp(-1)) < 0.05
    step, seam = np.abs(np.diff(x, axis=0)).mean(), np.abs(x[0] - x[-1]).mean()
    assert abs(seam / step - 1) < 0.1                              # the seam is an ordinary step
    for shutter in ('box', 'triangle'):
        shown = D.ou(rng, t, e * 16, (2000,), 1.0, 2.0, shutter=shutter, period=24.0)
        assert abs(shown.std() / D.exposure_factor(2.0, 0.8, shutter) - 1) < 0.08
    with pytest.raises(ValueError):                                # a held clock cannot loop
        D.ou(rng, *D.clock(480, 0.05, holds=[(100, 200, 0.0, 6)]), (3,), 1.0, 1.0, period=24.0)


def test_protein_motion_moves_a_protein_as_a_protein():
    t, _ = St.read_mmcif(ROOT / 'assets' / 'pdb' / '9GO1.cif')
    t = St.select(t, t['chain'] == t['chain'][0])
    X = t['xyz']
    times, rate = D.clock(96, 1.0 / 24)
    m = D.protein_motion(np.random.default_rng(8), X, t['resn'], t['resi'], t['name'], t['chain'], times, rate * 2)
    ret, lys = t['resn'] == 'RET', t['resi'] == 296
    assert m['report']['bonded_riders'] == [f"{t['chain'][0]}:{t['resi'][ret][0]}:RET - {t['chain'][0]}:296:LYS"]
    assert np.allclose(m['shapes'][ret], m['shapes'][lys][0]) and np.allclose(m['shapes'][lys], m['shapes'][lys][0])
    assert m['topo']['chi1_w'][ret | lys].max() == 0 and m['report']['turning_residues'] > 200
    edges = St.bonds(t)
    length = lambda P: np.linalg.norm(P[edges[:, 0]] - P[edges[:, 1]], axis=1)   # noqa: E731
    strain = np.array([np.abs(length(X + D.displacement(m, X, f)) - length(X)) for f in range(0, 96, 8)])
    assert np.percentile(strain, 99) < 0.25 and strain.max() < 1.2   # turns are exact; modes keep bonds to 1st order
    nz, c15 = np.nonzero(lys & (t['name'] == 'NZ'))[0][0], np.nonzero(ret & (t['name'] == 'C15'))[0][0]
    d = [np.linalg.norm((X + D.displacement(m, X, f))[nz] - (X + D.displacement(m, X, f))[c15]) for f in range(0, 96, 8)]
    assert np.ptp(d) < 1e-9                                        # the Schiff base moves as one
    loop = D.protein_motion(np.random.default_rng(8), X, t['resn'], t['resi'], t['name'], t['chain'], times, rate * 2,
                            period=4.0, max_nodes=100)
    assert loop['report']['stride'] == 3 and loop['report']['modes'] == 30 and np.isfinite(loop['q']).all()
    step = [np.linalg.norm(D.displacement(loop, X, b) - D.displacement(loop, X, a), axis=1).mean() for a, b in
            ((k, k + 1) for k in range(95))]
    seam = np.linalg.norm(D.displacement(loop, X, 0) - D.displacement(loop, X, 95), axis=1).mean()
    assert seam < 2 * np.median(step)
