"""Pathways through a protein: HOLE-like slice search, elastic-band relaxation and free radius.

The free radius at a point is the distance to the nearest atom surface (centre distance minus radius).
A pathway whose free radius drops to about zero is interrupted: show that, don't paint a tube through it.
"""
import numpy as np


def pore_profile(xyz, radius, guide, ys, window=7.0, grid=0.5, axis=1):
    """In each slice (coordinate `y` along `axis`) the point with the most free space, searched within
    `window` of the guide polyline. Returns centres (len(ys), 3) and free radii."""
    other = [a for a in range(3) if a != axis]
    guide = np.asarray(guide, float)
    order = np.argsort(guide[:, axis])
    guide = guide[order]
    centres, free = [], []
    offs = np.arange(-window, window + 1e-6, grid)
    gu, gv = np.meshgrid(offs, offs)
    for y in ys:
        g = np.array([np.interp(y, guide[:, axis], guide[:, a]) for a in range(3)])
        cand = np.repeat(g[None], gu.size, 0)
        cand[:, other[0]] += gu.ravel()
        cand[:, other[1]] += gv.ravel()
        near = np.abs(xyz[:, axis] - y) < 12
        dist = np.linalg.norm(cand[:, None] - xyz[near][None], axis=2) - radius[near][None]
        clear = dist.min(1) - 0.02 * np.linalg.norm(cand - g, axis=1)   # prefer the guide when tied
        best = int(np.argmax(clear))
        centres.append(cand[best])
        free.append(float(dist[best].min()))
    return np.array(centres), np.array(free)


def relax_path(centres, xyz, radius, axis=1, window=1.5, grid=0.25, stiffness=1.0, passes=8, max_dev=4.0):
    """Elastic-band refinement of a slice-wise pathway: each slice moves in its plane (at most `max_dev` from
    where it started) to maximise clearance minus `stiffness` x squared distance from its neighbours' mean."""
    P = np.array(centres, float)
    start = P.copy()
    other = [a for a in range(3) if a != axis]
    offs = np.arange(-window, window + 1e-6, grid)
    gu, gv = (a.ravel() for a in np.meshgrid(offs, offs))
    near_path = np.min(np.linalg.norm(xyz[:, None] - P[None, ::4], axis=2), axis=1) < 18
    xyz, radius = xyz[near_path], radius[near_path]
    for _ in range(passes):
        for i in range(len(P)):
            mid = (P[max(i - 1, 0)] + P[min(i + 1, len(P) - 1)]) / 2
            cand = np.repeat(P[i][None], gu.size, 0)
            cand[:, other[0]] += gu
            cand[:, other[1]] += gv
            ok = np.linalg.norm(cand - start[i], axis=1) <= max_dev
            near = np.abs(xyz[:, axis] - P[i, axis]) < 10
            clear = (np.linalg.norm(cand[:, None] - xyz[near][None], axis=2) - radius[near][None]).min(1)
            dev = cand - mid
            dev[:, axis] = 0
            score = np.where(ok, clear - stiffness * (dev ** 2).sum(1), -1e9)
            P[i] = cand[np.argmax(score)]
    return P


def clearance(points, xyz, radius):
    """Free radius at each point: distance to the nearest atom surface."""
    points = np.asarray(points, float)
    out = np.empty(len(points))
    for k in range(0, len(points), 256):
        d = np.linalg.norm(points[k:k + 256, None] - xyz[None], axis=2) - radius[None]
        out[k:k + 256] = d.min(1)
    return out


def polyline(points, spacing=0.5, smooth=0):
    """Resample a polyline at even arc length; optional moving-average smoothing (window in samples)."""
    P = np.asarray(points, float)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    t = np.arange(0, s[-1] + 1e-9, spacing)
    out = np.stack([np.interp(t, s, P[:, k]) for k in range(3)], axis=1)
    if smooth > 1:
        pad = np.pad(out, ((smooth, smooth), (0, 0)), mode='edge')
        kernel = np.ones(2 * smooth + 1) / (2 * smooth + 1)
        out = np.stack([np.convolve(pad[:, k], kernel, mode='valid') for k in range(3)], axis=1)
    return out


def arc_length(P):
    """Cumulative arc length along a polyline (starts at 0)."""
    return np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.asarray(P, float), axis=0), axis=1))])
