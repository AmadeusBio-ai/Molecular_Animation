"""Meshes that carry molecular data: point clouds with attributes, frame-indexed tracks, absolute shape keys."""
import bpy
import numpy as np


def points_mesh(name, xyz, edges=None, attrs=None, collection=None):
    """Object whose vertices are `xyz` (and optional bond `edges`), with point attributes
    attrs = {name: (kind, values)}, kind in FLOAT, FLOAT_VECTOR, FLOAT_COLOR (rgb; alpha 1 is added)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in np.asarray(xyz, float)], [] if edges is None else [tuple(e) for e in edges], [])
    for key, (kind, values) in (attrs or {}).items():
        a = me.attributes.new(key, kind, 'POINT')
        values = np.asarray(values, np.float32)
        if kind == 'FLOAT_COLOR':
            a.data.foreach_set('color', np.hstack([values, np.ones((len(values), 1), np.float32)]).ravel())
        elif kind == 'FLOAT_VECTOR':
            a.data.foreach_set('vector', values.ravel())
        else:
            a.data.foreach_set('value', values)
    me.update()
    obj = bpy.data.objects.new(name, me)
    if collection is not None:
        collection.objects.link(obj)
    return obj


def frame_tracks(name, tracks, attrs, collection):
    """Point tracks (frames, n, 3) as one mesh of frames x n vertices tagged with attribute 'f' (frame number,
    1-based); groups.frame_spheres() / G.this_frame() keep the current frame's points. Per-point attributes are
    (n,) arrays (repeated each frame) or (frames, n) arrays."""
    F, n = tracks.shape[:2]
    out = {'f': ('FLOAT', np.repeat(np.arange(1, F + 1), n))}
    for key, (kind, values) in attrs.items():
        values = np.asarray(values)
        if values.shape[:2] != (F, n):
            values = np.broadcast_to(values, (F, *values.shape))
        out[key] = (kind, values.reshape(F * n, *values.shape[2:]))
    return points_mesh(name, tracks.reshape(-1, 3), None, out, collection)


def absolute_keys(obj, snapshots):
    """Absolute shape keys: snapshot k sits at eval_time 10 k (linear between neighbours). Key the returned
    Key's eval_time to play a morph; every representation built on this mesh follows the same coordinates."""
    obj.shape_key_add(name='S00', from_mix=False)
    for k, xyz in enumerate(snapshots[1:], 1):
        kb = obj.shape_key_add(name=f'S{k:02d}', from_mix=False)
        kb.data.foreach_set('co', np.asarray(xyz, np.float32).ravel())
    key = obj.data.shape_keys
    key.use_relative = False
    key.name = obj.name + '_Key'
    return key
