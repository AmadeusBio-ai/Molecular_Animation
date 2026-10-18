"""Thermal motion from physical rates, for animation: a film clock, diffusion constants, tethered Brownian
motion, elastic-network normal modes and side-chain torsions.

None of this simulates a particular molecule. Each motion is a stationary random process whose amplitude and
correlation time come from measured or hydrodynamic values (docs/motion.md). The processes run on a film clock
(molecular ns per frame) and every frame shows the average over its exposure, as a camera would: motions much
faster than a frame average out, motions much slower than the film look frozen. Molecules move as units:
rigid-body diffusion of the whole, collective normal modes inside it, rotations about bonds for side chains, so
covalent geometry is kept.

Units: A, ns, rad.
"""
import math

import numpy as np

KB = 1.380649e-23                          # J/K
WATER_VISCOSITY = {293.15: 1.0016e-3, 298.15: 0.8900e-3, 303.15: 0.7972e-3, 310.15: 0.6913e-3}   # Pa s


def viscosity(T=298.15):
    """Water viscosity (Pa s) at T (K), interpolated from the table."""
    ts = sorted(WATER_VISCOSITY)
    return float(np.interp(T, ts, [WATER_VISCOSITY[t] for t in ts]))


def stokes_einstein(radius, T=298.15, eta=None):
    """Translational diffusion coefficient (A^2/ns) of a sphere of hydrodynamic radius `radius` (A)."""
    eta = viscosity(T) if eta is None else eta
    return KB * T / (6 * math.pi * eta * radius * 1e-10) * 1e20 * 1e-9


def stokes_einstein_debye(radius, T=298.15, eta=None):
    """Rotational diffusion coefficient (rad^2/ns) of a sphere of hydrodynamic radius `radius` (A). The
    rotational correlation time of a rank-2 probe (NMR, fluorescence anisotropy) is 1 / (6 D_r)."""
    eta = viscosity(T) if eta is None else eta
    return KB * T / (8 * math.pi * eta * (radius * 1e-10) ** 3) * 1e-9


def hydrodynamic_radius(xyz, shell=3.0):
    """Hydrodynamic radius (A) of a compact molecule: the radius of the uniform sphere with the same radius of
    gyration, sqrt(5/3) Rg, plus a hydration shell. A rough estimate (elongated molecules diffuse faster
    than their Rg suggests); state it as such."""
    X = np.asarray(xyz, float)
    rg = math.sqrt(((X - X.mean(0)) ** 2).sum(1).mean())
    return math.sqrt(5 / 3) * rg + shell


def ellipsoid(xyz, shell=3.0):
    """Principal axes (3x3, rows, longest first) and semi-axes (A) of the uniform ellipsoid with the same second
    moments as the atoms (a_i = sqrt(5 var_i)), plus a hydration shell."""
    X = np.asarray(xyz, float)
    X = X - X.mean(0)
    w, v = np.linalg.eigh(X.T @ X / len(X))
    order = np.argsort(w)[::-1]
    return v[:, order].T, np.sqrt(5 * np.maximum(w[order], 0)) + shell


def perrin(semi_axes, T=298.15, eta=None):
    """Diffusion of a rigid body treated as a prolate spheroid (Perrin 1934, with Koenig's 1975 correction):
    long semi-axis a = semi_axes[0], short b = sqrt(semi_axes[1] semi_axes[2]) (A). Returns translational D
    (A^2/ns, orientation-averaged) and rotational D (rad^2/ns) about the three principal axes (the long axis
    first). A sphere gives Stokes-Einstein and Stokes-Einstein-Debye."""
    eta = viscosity(T) if eta is None else eta
    a = semi_axes[0] * 1e-10
    b = math.sqrt(semi_axes[1] * semi_axes[2]) * 1e-10
    a = max(a, 1.001 * b)                               # the formulas are 0/0 for a sphere
    e = math.sqrt(a * a - b * b)
    S = 2 / e * math.log((a + e) / b)
    zeta_t = 12 * math.pi * eta / S
    zeta_par = 32 * math.pi * eta / 3 * (a * a - b * b) * b * b / (2 * a - b * b * S)
    zeta_perp = 32 * math.pi * eta / 3 * (a ** 4 - b ** 4) / ((2 * a * a - b * b) * S - 2 * a)
    kT = KB * T
    return kT / zeta_t * 1e20 * 1e-9, np.array([kT / zeta_par, kT / zeta_perp, kT / zeta_perp]) * 1e-9


def wlc_bend(wavelengths, persistence=500.0, T=298.15, eta=None, radius=10.0, friction=1.0):
    """Bending fluctuations of a worm-like chain by wavelength band (Landau-Lifshitz modes): for each band
    [lambda/2, lambda] (A), the RMS transverse displacement per direction, sqrt(7/12 lambda^3 / (Lp (2 pi)^4)),
    and the relaxation time (ns) of its longest wave, zeta lambda^4 / (kT Lp (2 pi)^4) with the slender-rod
    friction zeta = 4 pi eta / (ln(lambda / 2r) + 0.5) x `friction` (crowding). Returns [(RMS A, tau ns)]."""
    eta = viscosity(T) if eta is None else eta
    out = []
    for lam in wavelengths:
        rms = math.sqrt(7 / 12 * lam ** 3 / (persistence * (2 * math.pi) ** 4))
        zeta = 4 * math.pi * eta / (math.log(lam / (2 * radius)) + 0.5) * friction
        tau = zeta * (lam * 1e-10) ** 4 / (KB * T * persistence * 1e-10 * (2 * math.pi) ** 4)
        out.append((rms, tau * 1e9))
    return out


def wlc_twist(length, persistence=750.0, T=298.15, eta=None, radius=10.0, friction=1.0):
    """Twist fluctuations of a double helix over `length` (A): the RMS angle (rad) of a noise field whose values
    `length` apart differ by the twist persistence's variance length / C (with a 1/e correlation over `length`,
    var = 2 sigma^2 (1 - 1/e)), and the relaxation time (ns) of a twist wave of that length,
    zeta_r length^2 / (C kT pi^2), with rotational friction zeta_r = 4 pi eta r^2 x `friction` per length."""
    eta = viscosity(T) if eta is None else eta
    rms = math.sqrt(length / persistence / (2 * (1 - math.exp(-1))))
    zeta = 4 * math.pi * eta * (radius * 1e-10) ** 2 * friction
    tau = zeta * (length * 1e-10) ** 2 / (persistence * 1e-10 * KB * T * math.pi ** 2)
    return rms, tau * 1e9


# ----------------------------------------------------------------------------- the clock

def clock(frames, ns_per_frame, holds=()):
    """Molecular time (ns) at frames 1..frames. `holds` = [(start, end, speed, ease)]: between start and end
    the clock runs at `speed` x its rate (0 freezes it), easing in and out over `ease` frames. Returns
    (times (frames,), exposure (frames,) = the time one frame spans at that moment)."""
    f = np.arange(1, frames + 1, dtype=float)
    speed = np.ones(frames)
    for a, b, s, ease in holds:
        u = np.clip((f - (a - ease)) / max(ease, 1e-9), 0, 1) * np.clip(((b + ease) - f) / max(ease, 1e-9), 0, 1)
        u = u * u * (3 - 2 * u)
        speed = speed * (1 - u) + s * u * speed
    rate = speed * ns_per_frame
    times = np.concatenate([[0.0], np.cumsum((rate[1:] + rate[:-1]) / 2)])
    return times, rate


# ----------------------------------------------------------------------------- random processes

def window_mean(grid, path, times, exposure, shutter='box'):
    """Mean of `path` (len(grid), ...) over [t - e/2, t + e/2] for each frame time t; point values where the
    window is shorter than a grid step. shutter='triangle' weights the window as a triangle of full width e (a
    box of e/2 applied twice). A box's edges add a fresh random increment to a diffusing path's velocity every
    frame, so Brownian motion shown through it jerks; through a triangle its velocity changes smoothly."""
    if shutter == 'triangle':
        half = np.asarray(exposure, float) / 2
        inner = window_mean(grid, path, grid, np.interp(grid, times, half))
        return window_mean(grid, inner, times, half)
    cum = np.concatenate([np.zeros((1, *path.shape[1:])),
                          np.cumsum((path[1:] + path[:-1]) / 2 * np.diff(grid)[(...,) + (None,) * (path.ndim - 1)], axis=0)])
    a, b = times - exposure / 2, times + exposure / 2

    def at(arr, t):
        k = np.clip(np.searchsorted(grid, t) - 1, 0, len(grid) - 2)
        u = ((t - grid[k]) / (grid[k + 1] - grid[k]))[(...,) + (None,) * (path.ndim - 1)]
        return arr[k] * (1 - u) + arr[k + 1] * u
    width = (b - a)[(...,) + (None,) * (path.ndim - 1)]
    step = grid[1] - grid[0]
    mean = (at(cum, b) - at(cum, a)) / np.maximum(width, 1e-12)
    return np.where(width > step, mean, at(path, times))


def ou(rng, times, exposure, shape, sigma, tau, substeps=8, shutter='box'):
    """Ornstein-Uhlenbeck processes (stationary RMS `sigma`, correlation time `tau` in ns; both broadcast to
    `shape`), shown at the frame `times` and averaged over each frame's `exposure` (ns). At times short
    compared with tau an OU process diffuses with D = sigma^2 / tau per axis; at long times it stays within
    ~sigma of zero (a tethered or caged random walk). `shutter` as in window_mean. Returns (frames, *shape)."""
    times, exposure = np.asarray(times, float), np.asarray(exposure, float)
    shape = (shape,) if isinstance(shape, int) else tuple(shape)
    sigma = np.broadcast_to(np.asarray(sigma, float), shape)
    tau = np.broadcast_to(np.asarray(tau, float), shape)
    pos = exposure[exposure > 0]
    window = np.median(pos) if len(pos) else 1.0
    h = window / substeps
    # Processes much faster than the exposure would need a finer grid; they average out to small, frame-to-frame
    # independent values, so run them at tau = 2h with sigma scaled to keep their exposure-averaged RMS.
    fast = tau < 2 * h
    if fast.any():
        keep = np.vectorize(lambda t: exposure_factor(t, window, shutter))
        sigma = np.where(fast, sigma * keep(tau) / exposure_factor(2 * h, window, shutter), sigma)
        tau = np.where(fast, 2 * h, tau)
    lo, hi = times[0] - exposure[0], times[-1] + exposure[-1]
    grid = lo + h * np.arange(int(math.ceil((hi - lo) / h)) + 2)
    a = np.exp(-h / tau)
    noise = np.sqrt(1 - a * a) * sigma
    path = np.empty((len(grid), *shape))
    path[0] = rng.normal(size=shape) * sigma
    for k in range(1, len(grid)):
        path[k] = path[k - 1] * a + noise * rng.normal(size=shape)
    return window_mean(grid, path, times, exposure, shutter)


def exposure_factor(tau, window, shutter='box'):
    """RMS of an OU process (correlation time tau) averaged over `window`, relative to its raw RMS. Box:
    sqrt(2 (tau/T)^2 (T/tau - 1 + exp(-T/tau))); motions much faster than the window fade as sqrt(2 tau / T).
    Triangle (full width T): the kernel's autocorrelation integrated against exp(-|r|/tau); fast motions fade
    as sqrt(8 tau / 3T)."""
    x = window / tau
    if x < 1e-9:
        return 1.0
    if shutter == 'box':
        return math.sqrt(2 * (x - 1 + math.exp(-x))) / x
    if x > 200:
        return math.sqrt(8 / (3 * x))
    k = 1 - np.abs(np.linspace(-1, 1, 801))
    acf = np.convolve(k / k.sum(), k / k.sum())
    lag = np.arange(-800, 801) * (window / 800)
    return math.sqrt(float((acf * np.exp(-np.abs(lag) / tau)).sum()))


def tether(D, sigma):
    """Correlation time (ns) of an OU process with short-time diffusion D (A^2/ns or rad^2/ns per axis) held
    within RMS sigma: tau = sigma^2 / D."""
    return sigma * sigma / D


def rotation_matrix(rotvec):
    """Rotation matrices (..., 3, 3) from rotation vectors (..., 3) in rad (Rodrigues)."""
    v = np.asarray(rotvec, float)
    th = np.linalg.norm(v, axis=-1)[..., None, None]
    k = v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)
    K = np.zeros(v.shape[:-1] + (3, 3))
    K[..., 0, 1], K[..., 0, 2], K[..., 1, 2] = -k[..., 2], k[..., 1], -k[..., 0]
    K[..., 1, 0], K[..., 2, 0], K[..., 2, 1] = k[..., 2], -k[..., 1], k[..., 0]
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def rigid_brownian(rng, times, exposure, D_t, D_r, tether_t, tether_r, substeps=8, shutter='box'):
    """Tethered rigid-body Brownian motion of a free molecule: translation (frames, 3) in A and rotation
    vectors (frames, 3) in rad. Each axis diffuses with D_t (A^2/ns) and D_r (rad^2/ns) at short times and is
    held within RMS tether_t / tether_r at long times (so the molecule keeps its place in the composition).
    The rotation vector is a small-angle composition of the three axis processes, exact enough for tethers
    up to ~30 deg."""
    shift = ou(rng, times, exposure, (3,), tether_t, tether(D_t, tether_t), substeps, shutter)
    turn = ou(rng, times, exposure, (3,), tether_r, tether(D_r, tether_r), substeps, shutter)
    return shift, turn


# ----------------------------------------------------------------------------- normal modes

def anm(nodes, cutoff=15.0, gamma=1.0, modes=None, bonded=None, bonded_gamma=10.0):
    """Anisotropic network model (Atilgan et al. 2001): springs of constant gamma between nodes closer than
    `cutoff` (A), and of `bonded_gamma` between the node pairs in `bonded` (sequence neighbours: a stiffer
    covalent backbone, as in refined elastic networks). Returns (eigenvalues (k,), eigenvectors (n, 3, k)) of the
    Hessian without the six rigid-body modes, softest first, unit-normalised in 3n."""
    X = np.asarray(nodes, float)
    n = len(X)
    d = X[:, None] - X[None]
    r2 = (d * d).sum(-1)
    near = (r2 < cutoff * cutoff) & ~np.eye(n, dtype=bool)
    k = np.where(near, gamma, 0.0)
    for i, j in ([] if bonded is None else bonded):
        k[i, j] = k[j, i] = bonded_gamma
    near = k > 0
    blocks = -k[..., None, None] * d[..., :, None] * d[..., None, :] / np.where(near, r2, 1.0)[..., None, None]
    blocks[~near] = 0.0
    H = blocks.transpose(0, 2, 1, 3).reshape(3 * n, 3 * n)
    for i in range(n):
        H[3 * i:3 * i + 3, 3 * i:3 * i + 3] = -blocks[i].sum(0)
    w, v = np.linalg.eigh(H)
    keep = slice(6, None if modes is None else 6 + modes)
    return w[keep], v[:, keep].reshape(n, 3, -1)


def mode_amplitudes(rng, eigvals, times, exposure, scale, tau_softest, substeps=8, shutter='box'):
    """Langevin dynamics of normal modes in the overdamped limit: mode k is an OU process with variance
    scale / lambda_k (equipartition, scale = kT / gamma) and correlation time tau_softest * lambda_0 / lambda_k
    (friction / stiffness). Soft modes are large and slow, stiff ones small and fast. Returns (frames, k)."""
    lam = np.asarray(eigvals, float)
    return ou(rng, times, exposure, (len(lam),), np.sqrt(scale / lam), tau_softest * lam[0] / lam, substeps, shutter)


def mode_scale(eigvals, eigvecs, rmsf):
    """The `scale` (kT / gamma) for mode_amplitudes() that gives the nodes a mean-square fluctuation of rmsf^2
    over the kept modes at equilibrium."""
    per_mode = (np.asarray(eigvecs) ** 2).sum(axis=(0, 1)) / len(eigvecs)     # 1/n each for unit vectors
    return rmsf ** 2 / float((per_mode / np.asarray(eigvals)).sum())


def node_rmsf(eigvals, eigvecs, scale):
    """Equilibrium RMS fluctuation (A, all three axes together) of each node over the kept modes."""
    return np.sqrt(((np.asarray(eigvecs) ** 2).sum(1) * scale / np.asarray(eigvals)).sum(1))


def residue_nodes(resi, name, chain=None, node_names=('CA', 'P', "C4'")):
    """One network node per residue: its first atom named in `node_names` (CA for amino acids, P, or C4' for a
    nucleotide without a phosphate). Returns (node atom indices, per-atom node index, -1 for atoms of residues
    without one, e.g. a ligand)."""
    resi, name = np.asarray(resi), np.asarray(name)
    chain = np.full(len(resi), '') if chain is None else np.asarray(chain)
    key = [f'{c}:{r}' for c, r in zip(chain, resi)]
    best = {}
    for k, (kk, nm) in enumerate(zip(key, name)):
        if nm in node_names:
            rank = node_names.index(nm)
            if kk not in best or rank < best[kk][0]:
                best[kk] = (rank, k)
    nodes = sorted(v[1] for v in best.values())
    order = {key[i]: j for j, i in enumerate(nodes)}
    return np.array(nodes), np.array([order.get(kk, -1) for kk in key])


def sequence_pairs(X, nodes, reach=4.3):
    """Consecutive nodes closer than `reach` (A): covalently linked neighbours (CA-CA 3.8 A; use ~7.5 for P-P),
    for anm(bonded=...). Chain breaks are left unlinked."""
    P = np.asarray(X, float)[nodes]
    return [(i, i + 1) for i in range(len(P) - 1) if np.linalg.norm(P[i + 1] - P[i]) < reach]


def atom_shapes(X, vec, nodes, node_of, pairs, rigid=None):
    """Per-atom mode shapes (atoms, 3, k) from node shapes vec (nodes, 3, k). Each atom takes its residue's node
    displacement, blended linearly toward the linked neighbouring node in the direction it lies (the projection
    of its offset onto the node-node bond), so the atoms between two nodes interpolate their motion: small
    rotations of a segment carry its atoms along and bonds keep their lengths to first order. Atoms in
    `rigid` (mask) take their node's displacement unblended (e.g. a ligand and the side chain it is bonded to)."""
    X = np.asarray(X, float)
    P = X[nodes]
    nxt, prv = {i: j for i, j in pairs}, {j: i for i, j in pairs}
    out = vec[np.maximum(node_of, 0)].copy()
    for a in np.nonzero(node_of >= 0)[0]:
        if rigid is not None and rigid[a]:
            continue
        i = node_of[a]
        for j in (nxt.get(i), prv.get(i)):
            if j is None:
                continue
            b = P[j] - P[i]
            w = float(np.clip((X[a] - P[i]) @ b / (b @ b), 0.0, 1.0))
            if w > 0:
                out[a] = (1 - w) * vec[i] + w * vec[j]
                break
    return out


# ----------------------------------------------------------------------------- side-chain torsions

# chi2 axis atom (after CB) per residue type; residues without a chi2 (or without side-chain torsions) are absent.
CHI2_AXIS = {'ARG': 'CG', 'ASN': 'CG', 'ASP': 'CG', 'GLN': 'CG', 'GLU': 'CG', 'HIS': 'CG', 'ILE': 'CG1',
             'LEU': 'CG', 'LYS': 'CG', 'MET': 'CG', 'PHE': 'CG', 'TRP': 'CG', 'TYR': 'CG'}
NO_CHI = {'ALA', 'GLY', 'PRO'}             # proline's ring closes on the backbone
BACKBONE = {'N', 'CA', 'C', 'O', 'OXT'}


def chi_topology(resn, resi, name, chain=None):
    """Which side-chain torsions move which atoms. Returns per-atom arrays: residue slot (index into the
    residues, in order of appearance), chi1 and chi2 weights (1 = the atom turns with that torsion), and the
    atom indices of the axes (CA, CB, chi2 axis atom; -1 where absent), plus the residue count. chi1 turns
    every side-chain atom beyond CB about CA-CB; chi2 every atom beyond the chi2 axis atom about CB-it."""
    resn, resi, name = np.asarray(resn), np.asarray(resi), np.asarray(name)
    key = list(zip(resi.tolist(), [''] * len(resi) if chain is None else list(chain)))
    slots, slot = {}, np.zeros(len(name), int)
    for k, kk in enumerate(key):
        slot[k] = slots.setdefault(kk, len(slots))
    w1, w2 = np.zeros(len(name)), np.zeros(len(name))
    i_ca, i_cb, i_cg = (np.full(len(name), -1) for _ in range(3))
    by_slot = {}
    for k in range(len(name)):
        by_slot.setdefault(slot[k], {})[str(name[k])] = k
    for k in range(len(name)):
        atoms, rn, nm = by_slot[slot[k]], str(resn[k]), str(name[k])
        if rn in NO_CHI or nm in BACKBONE or nm == 'CB' or 'CA' not in atoms or 'CB' not in atoms:
            continue
        i_ca[k], i_cb[k] = atoms['CA'], atoms['CB']
        w1[k] = 1.0
        ax = CHI2_AXIS.get(rn)
        if ax and ax in atoms and nm != ax and not (rn == 'ILE' and nm == 'CG2'):
            i_cg[k], w2[k] = atoms[ax], 1.0
    return {'slot': slot, 'chi1_w': w1, 'chi2_w': w2, 'i_ca': i_ca, 'i_cb': i_cb, 'i_cg': i_cg, 'residues': len(slots)}


def _turn_about(P, a, b, angle):
    """Rotate points P about the axis through a toward b by `angle` (rad); all broadcast row-wise."""
    k = b - a
    k = k / np.maximum(np.linalg.norm(k, axis=-1, keepdims=True), 1e-12)
    v = P - a
    c, s = np.cos(angle)[..., None], np.sin(angle)[..., None]
    return a + v * c + np.cross(k, v) * s + k * (k * v).sum(-1, keepdims=True) * (1 - c)


def apply_chi(X, topo, chi1, chi2):
    """Positions after turning each residue's side chain by chi1, chi2 (rad, per residue slot): chi2 first,
    then chi1, as the geometry nodes do. Bond lengths and angles are unchanged (rigid turns about bonds)."""
    X = np.array(X, float)
    s = topo['slot']
    m2 = topo['chi2_w'] > 0
    X[m2] = _turn_about(X[m2], X[topo['i_cb'][m2]], X[topo['i_cg'][m2]], chi2[s[m2]])
    m1 = topo['chi1_w'] > 0
    X[m1] = _turn_about(X[m1], X[topo['i_ca'][m1]], X[topo['i_cb'][m1]], chi1[s[m1]])
    return X


def burial(xyz, probe_idx, radius=10.0):
    """Neighbour count within `radius` of each probe atom: a cheap burial measure (more neighbours = more
    buried, less side-chain freedom)."""
    X = np.asarray(xyz, float)
    out = np.zeros(len(probe_idx), int)
    for k in range(0, len(probe_idx), 256):
        P = X[probe_idx[k:k + 256]]
        out[k:k + 256] = (np.linalg.norm(P[:, None] - X[None], axis=2) < radius).sum(1) - 1
    return out
