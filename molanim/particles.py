"""Illustrative motion for ions and solvent: smooth wandering, site-to-site transits, clearance steering.

None of this is a simulation. Keep it sparse and irregular (dwell times, lateral jitter, one particle per
site), keep particles clear of atoms, and don't present the apparent rate as physiological.
"""
import math

import numpy as np

from .timeline import smoothstep


def drift(rng, frames, n, amp=4.0, periods=(60.0, 260.0), waves=4):
    """Smooth, aperiodic wandering: (frames, n, 3) offsets, each axis a sum of random sinusoids."""
    t = np.arange(frames)[:, None, None]
    out = np.zeros((frames, n, 3))
    for _ in range(waves):
        period = rng.uniform(*periods, size=(1, n, 3))
        phase = rng.uniform(0, 2 * math.pi, size=(1, n, 3))
        out += np.sin(2 * math.pi * t / period + phase) * rng.uniform(0.5, 1.0, size=(1, n, 3))
    return out * amp / math.sqrt(waves / 2)


def transits(rng, path, sites, entries, frames, hop=(7, 12), dwell=(5, 16), approach=18, leave=26,
             lateral=0.45, above=16.0, below=20.0, bulk_amp=3.0, speed=1.4):
    """Particle tracks through a pathway: (frames, len(entries), 3).

    `path` runs from the entry mouth (index 0) to the exit; `sites` are arc lengths of binding sites in
    passage order. Each particle waits in the bulk beyond the mouth, drops in at its entry frame, hops
    between sites with eased moves (averaging at most `speed` A per frame) and irregular dwell times (never
    sharing a site with the particle ahead), then leaves into the bulk beyond the exit. Small lateral jitter
    keeps the motion from reading as a bead on a wire."""
    P = np.asarray(path, float)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    tang = np.gradient(P, axis=0)
    tang /= np.linalg.norm(tang, axis=1)[:, None]

    def at(arc):
        k = np.clip(np.searchsorted(s, arc), 1, len(s) - 1)
        u = (arc - s[k - 1]) / max(s[k] - s[k - 1], 1e-9)
        return P[k - 1] * (1 - u) + P[k] * u, tang[k]

    stops = [0.0, *sites, s[-1]]
    free_at = {k: -1e9 for k in range(len(stops))}
    out = np.zeros((frames, len(entries), 3))
    wander = drift(rng, frames, len(entries), amp=bulk_amp)
    jitter = drift(rng, frames, len(entries), amp=lateral, periods=(6.0, 18.0))
    up, down = P[0] - P[min(8, len(P) - 1)], P[-1] - P[max(-9, -len(P))]
    up, down = up / np.linalg.norm(up), down / np.linalg.norm(down)
    for i, t0 in enumerate(sorted(entries)):
        start = P[0] + up * (above + rng.uniform(-3, 5)) + rng.normal(scale=2.0, size=3)
        end = P[-1] + down * (below + rng.uniform(-3, 6)) + rng.normal(scale=3.0, size=3)
        hops = []                                            # (hop start, arrival, arc from, arc to)
        t = t0
        for k in range(1, len(stops)):
            t = max(t + int(rng.integers(*dwell)), free_at[k])   # dwell, and wait until the next site is free
            free_at[k - 1] = t + 2
            h = max(int(rng.integers(*hop)), math.ceil((stops[k] - stops[k - 1]) / speed))
            hops.append((t, t + h, stops[k - 1], stops[k]))
            t += h
        free_at[len(stops) - 1] = t + 2
        for f in range(frames):
            fr = f + 1
            if fr <= t0 - approach:
                pos = start + wander[f, i]
            elif fr <= t0:
                u = smoothstep((fr - (t0 - approach)) / approach)
                pos = (start + wander[f, i]) * (1 - u) + at(0.0)[0] * u
            elif fr <= t:
                arc = stops[0]
                for a, b, s0, s1 in hops:
                    if fr < a:
                        arc = s0
                        break
                    if fr <= b:
                        arc = s0 + (s1 - s0) * smoothstep((fr - a) / (b - a))
                        break
                    arc = s1
                p, tg = at(arc)
                pos = p + jitter[f, i] - tg * (jitter[f, i] @ tg) * 0.6
            else:
                u = smoothstep(min(1.0, (fr - t) / leave))
                pos = at(s[-1])[0] * (1 - u) + (end + wander[f, i]) * u
            out[f, i] = pos
    return out


def keep_clear(tracks, X, need, atom_radius, offsets=None, weights=None, decay=0.75, iterations=30):
    """Tracks (frames, n, 3) that keep `need` between each particle centre and every atom surface.

    Atoms sit at X + offsets * weights[frame] (e.g. residues stepping back as a channel opens; omit for
    static atoms). Each particle carries an offset from its target track that decays every frame and is
    extended only as far as needed to clear the atoms; because it starts from last frame's offset, the
    particle slides around an atom instead of snapping between sides. Until a particle first touches an
    atom its track is unchanged. Returns tracks and a report: smallest gap (A, frame, particle), largest
    step and change of step (after and before)."""
    offsets = np.zeros_like(X) if offsets is None else offsets
    weights = np.zeros(len(tracks)) if weights is None else weights
    out = np.empty_like(tracks)
    for i in range(tracks.shape[1]):
        offset = np.zeros(3)
        for f in range(len(tracks)):
            offset *= decay
            x = tracks[f, i] + offset
            atoms = X + offsets * weights[f]
            near = np.linalg.norm(atoms - x, axis=1) < need + atom_radius.max() + 3
            A, r = atoms[near], atom_radius[near]
            for _ in range(iterations if len(A) else 0):
                v = x - A
                d = np.linalg.norm(v, axis=1) + 1e-9
                over = need - (d - r)
                if over.max() <= 0:
                    break
                x = x + ((v / d[:, None]) * np.clip(over, 0, None)[:, None]).sum(0) * 0.6
            offset = x - tracks[f, i]
            out[f, i] = x
    gap = min((float((np.linalg.norm(X + offsets * weights[f] - out[f, i], axis=1) - atom_radius).min()), f + 1, i)
              for f in range(len(out)) for i in range(out.shape[1]))

    def motion(t):
        steps = np.linalg.norm(np.diff(t, axis=0), axis=2)
        return round(float(steps.max()), 2), round(float(np.abs(np.diff(steps, axis=0)).max()), 2)
    return out, {'min_gap': (round(gap[0], 2), gap[1], gap[2]), 'max_step_and_change_after': motion(out),
                 'before': motion(tracks)}
