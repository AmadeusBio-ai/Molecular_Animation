"""Editorial time: easing, beat ramps, keyed paths and the camera, plus projection for labels.

Frames are 1-based like Blender's. A beat is a (start, end) frame pair; a key list is
[(frame, param, param, ...), ...] whose moves between consecutive keys ease in and out.
"""
import math

import numpy as np


def smoothstep(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def smootherstep(u):
    """C2-continuous ease (zero velocity and acceleration at both ends): the default for beats and moves."""
    u = min(max(u, 0.0), 1.0)
    return u * u * u * (u * (6 * u - 15) + 10)


def ramp(frame, a, b):
    """0 before frame a, 1 after frame b, eased in between."""
    return smootherstep((frame - a) / max(b - a, 1e-6))


def resolve(value, points):
    """A key parameter: a name in `points`, a (name, offset) pair, or a literal value."""
    if isinstance(value, str):
        return points[value]
    if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
        return points[value[0]] + np.asarray(value[1], float)
    return value


def keyed(keys, points, frames):
    """Per frame 1..frames: [(frame, [(from, to, u) per parameter])], with u eased between keys."""
    out = []
    for f in range(1, frames + 1):
        k = max([i for i, key in enumerate(keys) if key[0] <= f] or [0])
        k2 = min(k + 1, len(keys) - 1)
        f0, f1 = keys[k][0], keys[k2][0]
        u = smootherstep((f - f0) / (f1 - f0)) if f1 > f0 and f >= f0 else 0.0
        out.append((f, [(resolve(a, points), resolve(b, points), u) for a, b in zip(keys[k][1:], keys[k2][1:])]))
    return out


def camera_path(keys, points, frames):
    """Camera keys (frame, aim, distance, azimuth deg, elevation deg, lens mm) -> per frame
    (frame, location, aim, distance, lens). Azimuth 0 looks from -Y toward +Y; positive turns toward +X.
    Distance interpolates in log space, so a dive zooms by a steady percentage per frame."""
    out = []
    for f, ((a0, a1, u), (d0, d1, _), (z0, z1, _), (e0, e1, _), (l0, l1, _)) in keyed(keys, points, frames):
        aim = a0 * (1 - u) + a1 * u
        dist = math.exp(math.log(d0) * (1 - u) + math.log(d1) * u)
        az, el = math.radians(z0 * (1 - u) + z1 * u), math.radians(e0 * (1 - u) + e1 * u)
        direction = np.array([math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)])
        out.append((f, aim + dist * direction, aim, dist, l0 * (1 - u) + l1 * u))
    return out


def orbit_path(aim, distance, elevation, lens, frames, azimuth0=0.0, turns=1.0, extra=1):
    """A constant-speed orbit that closes on itself after `frames` (for seamless loops): frame frames + 1
    equals frame 1. Includes `extra` frames after the loop (the seam check). Same format as camera_path()."""
    out = []
    aim = np.asarray(aim, float)
    for f in range(1, frames + 1 + extra):
        az = math.radians(azimuth0 + 360.0 * turns * (f - 1) / frames)
        el = math.radians(elevation)
        direction = np.array([math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)])
        out.append((f, aim + distance * direction, aim, distance, lens))
    return out


def project(p, loc, aim, lens, res, sensor=36.0):
    """Stage point -> ((x, y) pixels from the top-left, depth) for a camera at `loc` aimed at `aim` with no
    roll (Blender TRACK_TO with up +Z), horizontal sensor fit."""
    fwd = (aim - loc) / np.linalg.norm(aim - loc)
    right = np.cross(fwd, (0.0, 0.0, 1.0))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    v = np.asarray(p, float) - loc
    z = v @ fwd
    f = lens / sensor * res[0]
    return np.array([res[0] / 2 + f * (v @ right) / z, res[1] / 2 - f * (v @ up) / z]), z


def fstop_for(aperture_ratio, lens, distance):
    """Cycles f-stop whose aperture radius is `aperture_ratio` x the focus distance (radius = focal / 2N)."""
    return (lens / 1000) / (2 * aperture_ratio * distance)


def label_data(spec, path, anchors, res, frames, fps, levels=None, lead=10, layout=None):
    """The label spec of a film (molanim.blender.labels.label_pass format) as plain data, for drawing the labels
    outside the video (a web page) in sync with it: header, captions, evidence tags (with `levels`, one per tag:
    'experimental', 'predicted', 'illustrative' or 'symbolic'), timescales, and every pointer and link with its
    anchors projected exactly as the label pass projects them. Screen positions are fractions of the frame
    (x from the left, y from the top), one per frame from `lead` frames before the item starts to its end;
    'from' is the first of those frames. Frames are 1-based, as in Blender. 'shot_ink' is the spec's ink per shot
    ([frame, 'dark' | 'light'], or None). 'layout' carries the label pass's placement hints: 'tags_left_from' (the
    frame from which tags and timescales sit top left, or None) plus `layout`, the label pass's own overrides
    (e.g. {'time_prefix': ''})."""
    def track(anchor):
        a = np.asarray(anchors[anchor], float)
        return a if a.ndim == 2 else np.repeat(a[None], frames, 0)

    def screen(anchor, f):
        if not isinstance(anchor, str):                         # a fixed screen position in pixels
            return np.asarray(anchor, float)
        _, loc, aim, _, lens = path[f - 1]
        return project(track(anchor)[f - 1], loc, aim, lens, res)[0]

    def positions(anchor, f0, f1):
        first = max(1, f0 - lead)
        xy = [screen(anchor, f) / np.array(res, float) for f in range(first, min(frames, f1) + 1)]
        return first, [[round(float(x), 4), round(float(y), 4)] for x, y in xy]

    tags = spec.get('tags', [])
    levels = list(levels) if levels is not None else [None] * len(tags)
    assert len(levels) == len(tags), 'one evidence level per tag'
    out = {
        'fps': fps, 'frames': frames, 'width': res[0], 'height': res[1],
        'header': None if not spec.get('header') else dict(zip(('start', 'end', 'text'), spec['header'])),
        'captions': [dict(zip(('start', 'end', 'title', 'subtitle'), c)) for c in spec.get('captions', [])],
        'tags': [{'start': a, 'end': b, 'text': t, 'level': lv} for (a, b, t), lv in zip(tags, levels)],
        'times': [dict(zip(('start', 'end', 'text'), t)) for t in spec.get('times', [])],
        'pointers': [], 'links': [], 'shot_ink': [list(s) for s in spec.get('shot_ink', [])] or None,
        'layout': {'tags_left_from': spec.get('tags_left_from'), **(layout or {})},
    }
    for f0, f1, anchor, body, offset in spec.get('pointers', []):
        first, xy = positions(anchor, f0, f1)
        out['pointers'].append({'start': f0, 'end': f1, 'text': body, 'region': offset is None,
                                'offset': None if offset is None else [offset[0] / res[0], offset[1] / res[1]],
                                'from': first, 'xy': xy})
    for f0, f1, a, b, opts in spec.get('links', []):
        first, xa = positions(a, f0, f1)
        _, xb = positions(b, f0, f1)
        out['links'].append({'start': f0, 'end': f1, 'from': first, 'a': xa, 'b': xb, 'dashes': opts.get('dashes', 0),
                             'text': opts.get('text')})
    return out
