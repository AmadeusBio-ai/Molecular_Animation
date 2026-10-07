"""Chemically constrained interpolation between two conformations of the same atoms.

A morph is illustrative motion between experimental endpoints, not a trajectory: label it as such.
Each intermediate snapshot is the linear interpolation, relaxed by position-based projection so that
bond lengths and angles (1-2 and 1-3 distances, plus chosen 1-4 distances) follow their interpolated
values and moving atoms don't pass through their neighbours.
"""
import numpy as np

from .structure import angle_pairs


def contacts(A, B, moving, excluded, cutoff=4.2, floor=3.0):
    """Non-bonded pairs touching a moving atom that come within `cutoff` in either state.
    Each gets a minimum distance: `floor`, or less if an endpoint is already closer."""
    mov = np.nonzero(moving)[0]
    pairs = []
    for X in (A, B):
        d = np.linalg.norm(X[mov][:, None] - X[None], axis=2)
        a, b = np.nonzero(d < cutoff)
        pairs.append(np.stack([mov[a], b], 1))
    p = np.unique(np.sort(np.vstack(pairs), axis=1), axis=0)
    p = p[p[:, 0] != p[:, 1]]
    ex = {tuple(e) for e in excluded}
    p = np.array([q for q in p.tolist() if tuple(q) not in ex]).reshape(-1, 2)
    dmin = np.minimum(np.linalg.norm(A[p[:, 0]] - A[p[:, 1]], axis=1), np.linalg.norm(B[p[:, 0]] - B[p[:, 1]], axis=1))
    return p, np.minimum(floor, dmin * 0.98)


def morph(A, B, edges, moving, steps, rigid_pairs=(), iterations=160, pull=0.04):
    """Positions from A to B in `steps` intervals (steps + 1 snapshots, both ends exact).

    Only `moving` atoms are adjusted; the rest follow the linear interpolation (choose `moving` so that
    they move little, e.g. < 0.5 A). `rigid_pairs` adds 1-4 distances to keep (a ring or conjugated unit
    that must turn as a body: see structure.torsion_pairs). Warm-started from the previous snapshot, so
    the path is continuous. Stage large changes (several morph() calls) so parts that must move together do."""
    n = len(A)
    pairs = np.vstack([edges, angle_pairs(edges, n), np.asarray(rigid_pairs).reshape(-1, 2)]).astype(int)
    dA = np.linalg.norm(A[pairs[:, 0]] - A[pairs[:, 1]], axis=1)
    dB = np.linalg.norm(B[pairs[:, 0]] - B[pairs[:, 1]], axis=1)
    near, floor = contacts(A, B, moving, pairs.tolist())
    w = moving.astype(float)
    out, x = [A.copy()], A.copy()
    for k in range(1, steps + 1):
        t = k / steps
        L = (1 - t) * A + t * B
        if k == steps:
            out.append(B.copy())
            break
        target = (1 - t) * dA + t * dB
        x = np.where(moving[:, None], x + (L - x) * 0.5, L)
        for it in range(iterations):
            x = _project(x, pairs, target, w)
            x = _repel(x, near, floor, w)
            if it < iterations - 20:
                x += (L - x) * pull * w[:, None]
        out.append(x.copy())
    return out


def _project(x, pairs, target, w):
    i, j = pairs[:, 0], pairs[:, 1]
    d = x[j] - x[i]
    length = np.linalg.norm(d, axis=1) + 1e-9
    wi, wj = w[i], w[j]
    tot = wi + wj
    ok = tot > 0
    corr = np.zeros_like(d)
    corr[ok] = (d[ok] * ((length[ok] - target[ok]) / length[ok])[:, None]) / tot[ok, None]
    acc, cnt = np.zeros_like(x), np.zeros(len(x))
    np.add.at(acc, i, corr * wi[:, None])
    np.add.at(acc, j, -corr * wj[:, None])
    np.add.at(cnt, i, ok * wi)
    np.add.at(cnt, j, ok * wj)
    return x + acc / np.maximum(cnt, 1)[:, None] * 0.9


def _repel(x, pairs, floor, w):
    if not len(pairs):
        return x
    i, j = pairs[:, 0], pairs[:, 1]
    d = x[j] - x[i]
    length = np.linalg.norm(d, axis=1) + 1e-9
    over = length < floor
    if not over.any():
        return x
    i, j, d, length, f = i[over], j[over], d[over], length[over], floor[over]
    wi, wj = w[i], w[j]
    tot = np.maximum(wi + wj, 1e-9)
    corr = d * ((length - f) / length)[:, None] / tot[:, None]
    acc, cnt = np.zeros_like(x), np.zeros(len(x))
    np.add.at(acc, i, corr * wi[:, None])
    np.add.at(acc, j, -corr * wj[:, None])
    np.add.at(cnt, i, wi)
    np.add.at(cnt, j, wj)
    return x + acc / np.maximum(cnt, 1)[:, None] * 0.9


def max_bond_deviation(frames, edges):
    """Worst bond-length deviation (A) along a path, from the endpoints' mean bond length."""
    i, j = edges[:, 0], edges[:, 1]
    ref = (np.linalg.norm(frames[0][i] - frames[0][j], axis=1) + np.linalg.norm(frames[-1][i] - frames[-1][j], axis=1)) / 2
    return max(float(np.abs(np.linalg.norm(f[i] - f[j], axis=1) - ref).max()) for f in frames)
