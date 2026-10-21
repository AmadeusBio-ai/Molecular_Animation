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


def surface_mesh(name, verts, faces, attrs=None, collection=None, smooth=True):
    """Object from mesh arrays (e.g. molanim.cartoon builders): `verts` (n, 3), `faces` (index tuples), point
    attributes {name: values} where (n,) arrays become FLOAT (INT if given as ('INT', values)) and (n, 3)
    arrays FLOAT_COLOR if the name starts with 'col', FLOAT_VECTOR otherwise. Faces are shaded smooth unless smooth=False."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in np.asarray(verts, float)], [], [tuple(f) for f in faces])
    for key, values in (attrs or {}).items():
        explicit = None
        if isinstance(values, tuple):                  # (kind, values), as dynamics_attrs() returns them
            explicit, values = values
        values = np.asarray(values, np.float32)
        if values.ndim == 2:
            kind = explicit or ('FLOAT_COLOR' if key.startswith('col') else 'FLOAT_VECTOR')
            a = me.attributes.new(key, kind, 'POINT')
            if kind == 'FLOAT_COLOR':
                a.data.foreach_set('color', np.hstack([values, np.ones((len(values), 1), np.float32)]).ravel())
            else:
                a.data.foreach_set('vector', values.ravel())
        elif explicit == 'INT':
            me.attributes.new(key, 'INT', 'POINT').data.foreach_set('value', values.astype(np.int32))
        else:
            me.attributes.new(key, 'FLOAT', 'POINT').data.foreach_set('value', values)
    me.polygons.foreach_set('use_smooth', [smooth] * len(me.polygons))
    me.update()
    obj = bpy.data.objects.new(name, me)
    if collection is not None:
        collection.objects.link(obj)
    return obj


def realize(obj, name=None, collection=None):
    """A plain mesh object holding the evaluated geometry of `obj` (modifiers applied, e.g. a node-built
    surface), so numpy can work on its vertices. The source object is left untouched."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.name = name or obj.name + '_Mesh'
    out = bpy.data.objects.new(me.name, me)
    out.matrix_world = obj.matrix_world.copy()
    if collection is not None:
        collection.objects.link(out)
    return out


def vertices(obj):
    """(n, 3) vertex positions of a mesh object, in its local frame."""
    v = np.empty(len(obj.data.vertices) * 3, np.float32)
    obj.data.vertices.foreach_get('co', v)
    return v.reshape(-1, 3).astype(float)


def set_point_colors(obj, name, rgb):
    """Write (n, 3) linear colours to the point attribute `name` (FLOAT_COLOR) of a mesh object."""
    me = obj.data
    a = me.attributes.get(name) or me.attributes.new(name, 'FLOAT_COLOR', 'POINT')
    rgb = np.asarray(rgb, np.float32)
    a.data.foreach_set('color', np.hstack([rgb, np.ones((len(rgb), 1), np.float32)]).ravel())
    me.update()
