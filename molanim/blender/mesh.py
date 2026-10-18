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


def table(name, columns, collection):
    """A lookup table as a vertex-only mesh (renders nothing): row k is vertex k, columns are point attributes
    {name: (rows,) floats or (rows, 3) vectors}. Geometry nodes read it with G.sample(); per-frame tables put
    frame f (1-based) of item i at row (f - 1) x items + i."""
    rows = len(next(iter(columns.values())))
    attrs = {k: ('FLOAT_VECTOR' if np.ndim(v) == 2 else 'FLOAT', v) for k, v in columns.items()}
    return points_mesh(name, np.zeros((rows, 3)), None, attrs, collection)


def dynamics_tables(prefix, motion, collection, loop=False):
    """Frame tables for groups.dynamics from dynamics.protein_motion() ({'q': (frames, modes), 'chi': (frames,
    residues, 2)}). Returns (modes table, chi table or None, rows): pass `rows` as groups.dynamics' frames. With
    loop=True a last row repeats frame 1, so frame frames + 1 equals frame 1."""
    q, chi = motion['q'], motion.get('chi')
    if loop:
        q, chi = np.concatenate([q, q[:1]]), None if chi is None else np.concatenate([chi, chi[:1]])
    qp = np.pad(q, ((0, 0), (0, -q.shape[1] % 3)))
    modes = table(prefix + 'Modes', {f'q{j}': qp[:, 3 * j:3 * j + 3] for j in range(qp.shape[1] // 3)}, collection)
    chi_tab = None if chi is None else table(prefix + 'Chi', {'chi': np.pad(chi, ((0, 0), (0, 0), (0, 1))).reshape(-1, 3)},
                                             collection)
    return modes, chi_tab, len(q)


def dynamics_attrs(motion, idx=None, turns=True):
    """Point attributes for groups.dynamics from dynamics.protein_motion(): mode shapes 'm0', 'm1'... and, with
    `turns`, the side-chain topology. `idx` selects atoms for a mesh that holds only some of them (a ghost, a
    marker); their turn axes refer to the full mesh, so such meshes take turns=False."""
    idx = slice(None) if idx is None else idx
    shapes, topo = motion['shapes'][idx], motion['topo']
    out = {f'm{k}': ('FLOAT_VECTOR', shapes[:, :, k]) for k in range(shapes.shape[2])}
    if turns:
        out['res_i'] = ('FLOAT', topo['slot'][idx])
        out.update({k: ('FLOAT', topo[k][idx]) for k in ('chi1_w', 'chi2_w', 'i_ca', 'i_cb', 'i_cg')})
    return out


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
