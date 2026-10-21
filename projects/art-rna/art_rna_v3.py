"""ART: a hidden repertoire of RNA, version 3. Version 2's science, placements, timeline, camera and motion, drawn as
the website's plates draw molecules, on a white ground for the website (story_v3.py says what changed and why).

Coordinates and evidence as version 2 (record.md): the DNA from GenBank MW218148.1 9421-10900, built from 1BNA base
pairs (now with the O3'-P links between stacked templates closed to 1.6 A) and bent onto an illustrative path;
AlphaFold Server (AlphaFold 3) model 0 of the four array RNAs, the RT (QPI16926.1) and the partner (QPI16927.1);
no complex. AlphaFold Server output is subject to the AlphaFold Server Output Terms of Use (af3/terms_of_use.md).

    python pipeline.py build art-rna-v3
Rebuilds scene `ArtRna_v3` (art-rna-v3.blend), its label scene (art-rna-v3-labels.blend) and the web labels
(delivery/art-rna-v3/labels.json).
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(HERE)]
import molanim  # noqa: E402

molanim.reload()
import art_locus as A  # noqa: E402
import story_v3 as B  # noqa: E402
from molanim import cartoon as Ct  # noqa: E402
from molanim import color  # noqa: E402
from molanim import dynamics as D  # noqa: E402
from molanim import structure as St  # noqa: E402
from molanim import timeline as TL  # noqa: E402
from molanim.blender import groups, labels, look, mesh, rig  # noqa: E402
from molanim.blender import scene as SC  # noqa: E402
from molanim.blender.nodes import new_group, set_modifier_inputs  # noqa: E402

for _m in ('art_locus', 'story_v3'):
    if _m in sys.modules:
        import importlib
        importlib.reload(sys.modules[_m])

SCENE_NAME, PREFIX = 'ArtRna_v3', 'AR3_'
BNA = ROOT / 'assets' / 'pdb' / '1BNA.cif'
BLEND_PATH = HERE / 'art-rna-v3.blend'
LABEL_BLEND = HERE / 'art-rna-v3-labels.blend'
WEB_LABELS = ROOT / 'delivery' / 'art-rna-v3' / 'labels.json'
V2_RESULT = ROOT / 'renders' / 'art-rna' / 'build-result.json'
FPS, FRAMES, RES, T = B.FPS, B.FRAMES, B.RES, B.T
lin = color.lin


def ramp(tones, u):
    a, b = np.array(lin(tones[0])), np.array(lin(tones[1]))
    return a + (b - a) * np.asarray(u, float)[:, None]


# ----------------------------------------------------------------------------- node groups

def lit_group(prefix):
    """DNA colour: 'col_ctx' until the nucleotide's repeat copy lights ('lit_t'), then 'col_hi', eased over 16
    frames (colour only: the repeat is marked, it does not glow)."""
    ng, g, gin, gout = new_group(prefix + 'Lit', [])
    frame = g.node('GeometryNodeInputSceneTime').outputs['Frame']
    h = g.smooth(g.math('SUBTRACT', frame, g.attr('lit_t')), 0.0, 16.0)
    geo = g.store(gin.outputs['Geometry'], 'col', g.mix_color(h, g.attr('col_ctx', 'FLOAT_COLOR'), g.attr('col_hi', 'FLOAT_COLOR')),
                  'FLOAT_COLOR')
    g.put(geo, gout.inputs['Geometry'])
    return ng


def fade_group(prefix):
    """'alpha' = 'alpha0' x Show.x: a translucent molecule fades in as a whole."""
    ng, g, gin, gout = new_group(prefix + 'FadeIn', [('Show', 'NodeSocketObject', None)])
    x, _, _ = g.xyz(g.loc(gin.outputs['Show']))
    geo = g.store(gin.outputs['Geometry'], 'alpha', g.math('MULTIPLY', g.attr('alpha0'), g.smooth(x, 0.0, 1.0)))
    g.put(geo, gout.inputs['Geometry'])
    return ng


def stack(obj, mods):
    """Geometry-node modifiers in order: [(name, group, inputs)]."""
    for name, ng, inputs in mods:
        md = obj.modifiers.new(name, 'NODES')
        md.node_group = ng
        if inputs:
            set_modifier_inputs(md, inputs)


# ----------------------------------------------------------------------------- version 2's helpers (unchanged)

def euler_keys(obj, frames_xyz, frames_R):
    obj.rotation_mode = 'XYZ'
    prev = None
    for f, (loc, R) in enumerate(zip(frames_xyz, frames_R), 1):
        obj.location = loc
        e = Matrix(R.tolist()).to_euler('XYZ', prev) if prev is not None else Matrix(R.tolist()).to_euler('XYZ')
        obj.rotation_euler = e
        prev = e
        obj.keyframe_insert('location', frame=f)
        obj.keyframe_insert('rotation_euler', frame=f)
    SC.set_linear(obj)


def turn(deg_y, deg_z):
    return A.rotvec_matrix([0, 0, deg_z]) @ A.rotvec_matrix([0, deg_y, 0])


def tumbling(X, rng, times, window):
    axes, semi = D.ellipsoid(X)
    D_t, D_r = D.perrin(semi, B.TEMP)
    D_t, D_r = D_t / B.CROWDING['translation'], D_r / B.CROWDING['rotation']
    shift, rv = D.rigid_brownian(rng, times, window, D_t, D_r, B.TETHER['shift'], B.TETHER['turn'], **B.SHUTTER_ARGS)
    Rs = axes.T @ D.rotation_matrix(rv) @ axes
    sec = FPS
    turned = [math.degrees(math.acos(np.clip((np.trace(Rs[f + sec] @ Rs[f].T) - 1) / 2, -1, 1))) for f in range(0, FRAMES - sec, 6)]
    return shift, Rs, {'semi_axes_A': [round(float(v)) for v in semi], 'D_t_um2_s': round(D_t * 1e-20 / 1e-9 * 1e12, 1),
                       'D_r_per_us': [round(float(v) * 1e3, 2) for v in D_r],
                       'per_film_second': {'shift_A': round(float(np.median(np.linalg.norm(shift[sec:] - shift[:-sec], axis=1))), 1),
                                           'turn_deg': round(float(np.median(turned)), 1)}}


def normal_modes(name, X, t, params, reach, rng, times, window, collection):
    cutoff, count, rmsf, tau = params
    nodes, node_of = D.residue_nodes(t['resi'], t['name'])
    links = D.sequence_pairs(X, nodes, reach)
    eig, vec = D.anm(X[nodes], cutoff, modes=count, bonded=links)
    scale = D.mode_scale(eig, vec, rmsf)
    q = D.mode_amplitudes(rng, eig, times, window, scale, tau, **B.SHUTTER_ARGS)
    shapes = D.atom_shapes(X, vec, nodes, node_of, links)
    qp = np.pad(q, ((0, 0), (0, -count % 3)))
    table = mesh.table(f'{PREFIX}Modes_{name}', {f'q{j}': qp[:, 3 * j:3 * j + 3] for j in range(qp.shape[1] // 3)}, collection)
    attrs = {f'm{k}': ('FLOAT_VECTOR', shapes[:, :, k]) for k in range(count)}
    return shapes, q, table, attrs, {'nodes': len(nodes), 'tau_ns': [tau, round(tau * float(eig[0] / eig[-1]), 2)],
                                     'node_rmsf_A_p50_p95_max': [round(float(v), 2) for v in
                                                                 np.percentile(D.node_rmsf(eig, vec, scale), [50, 95, 100])]}


def min_distance(P, Q, chunk=256):
    best = np.inf
    for k in range(0, len(P), chunk):
        d = np.linalg.norm(P[k:k + chunk, None] - Q[None], axis=2)
        best = min(best, float(d.min()))
    return best


def near(P, Q, reach):
    lo, hi = P.min(0) - reach, P.max(0) + reach
    return Q[np.all((Q >= lo) & (Q <= hi), axis=1)]


# ----------------------------------------------------------------------------- locus map and notice

def diagram_items(rep):
    """The locus map as primitives in label pixels (x right, y down): genome line, the five repeat copies, the RT
    and partner genes, their names and a scale bar. Drawn by the label pass and, as fractions, by the web page."""
    (x0, x1), y, (span0, span1) = B.DIAGRAM['x'], B.DIAGRAM['y'], B.DIAGRAM['span']

    def px(g):
        return x0 + (g - span0) / (span1 - span0) * (x1 - x0)
    items = [{'type': 'box', 'x0': x0, 'x1': x1, 'y': y, 'h': 2.0, 'color': 'line'}]
    for c in rep['copies']:
        items.append({'type': 'box', 'x0': px(c['start']), 'x1': px(c['end'] + 1), 'y': y, 'h': B.DIAGRAM['h'][0], 'color': 'repeat'})
    for cds, kind in ((A.RT_CDS, 'rt'), (A.PARTNER_CDS, 'partner')):
        items.append({'type': 'arrow', 'x0': px(cds[0]), 'x1': px(cds[1] + 1), 'y': y, 'h': B.DIAGRAM['h'][0] * 0.8, 'color': kind})
    first, last = rep['copies'][0]['start'], rep['copies'][-1]['end']
    mid = {'array': (px(first) + px(last)) / 2, 'rt': (px(A.RT_CDS[0]) + px(A.RT_CDS[1])) / 2,
           'partner': (px(A.PARTNER_CDS[0]) + px(A.PARTNER_CDS[1])) / 2}
    for text, x, dy, size in (('Repeat array', mid['array'], -38, 24), ('Reverse transcriptase gene', mid['rt'], -38, 24),
                              ('Partner gene', mid['partner'], -38, 24),
                              (f'{len(rep["copies"])} repeats of {rep["length"]} nt, spacers 122–163 nt', mid['array'], 36, 19),
                              ('QPI16926 · 501 aa', mid['rt'], 36, 19), ('QPI16927 · 265 aa', mid['partner'], 36, 19)):
        items.append({'type': 'text', 'text': text, 'x': x, 'y': y + dy, 'size': size, 'align': 'CENTER'})
    sb = B.DIAGRAM['scale_bp']
    w = px(span0 + sb) - x0
    items.append({'type': 'rect', 'x0': x1 - w, 'x1': x1, 'y0': y + 62, 'y1': y + 64, 'color': 'ink'})
    items.append({'type': 'text', 'text': f'{sb} bp', 'x': x1, 'y': y + 82, 'size': 19, 'align': 'RIGHT'})
    return items, (round(px(first), 1), round(px(last + 1), 1))


def fade_material(name, rgb, f0, f1, fade=8):
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes['Material Output']
    for nd in list(nt.nodes):
        if nd != out:
            nt.nodes.remove(nd)
    em, clear, mix, val = (nt.nodes.new(k) for k in ('ShaderNodeEmission', 'ShaderNodeBsdfTransparent',
                                                      'ShaderNodeMixShader', 'ShaderNodeValue'))
    em.inputs['Color'].default_value = (*lin(rgb), 1)
    nt.links.new(val.outputs[0], mix.inputs[0])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    for f, v in ((f0 - fade, 0.0), (f0, 1.0), (f1 - fade, 1.0), (f1, 0.0)):
        val.outputs[0].default_value = v
        val.outputs[0].keyframe_insert('default_value', frame=f)
    m.surface_render_method = 'BLENDED'
    return m


def draw_diagram(lscene, items):
    """The locus map in the label scene (version 2's drawing, from diagram_items())."""
    col = lscene.collection.children[0]
    f0, f1 = T['diagram']
    mats = {k: fade_material(f'{B.LABEL_PREFIX}Map_{k}', rgb, f0, f1) for k, rgb in B.DIAGRAM_RGB.items()}
    mats['ink'] = fade_material(B.LABEL_PREFIX + 'Map_ink', B.INK['dark'], f0, f1)
    for k, it in enumerate(items):
        if it['type'] == 'text':
            cu = bpy.data.curves.new(f'{B.LABEL_PREFIX}Map_T{k:02d}', 'FONT')
            cu.body, cu.size, cu.align_x, cu.align_y = it['text'], it['size'], it['align'], 'CENTER'
            cu.materials.append(mats['ink'])
            obj = bpy.data.objects.new(cu.name, cu)
            obj.location = (it['x'], -it['y'], 0)
            col.objects.link(obj)
            continue
        if it['type'] == 'box':
            a, b, y, h = it['x0'], it['x1'], it['y'], it['h']
            pts = [(a, y - h / 2), (b, y - h / 2), (b, y + h / 2), (a, y + h / 2)]
        elif it['type'] == 'arrow':
            a, b, y, h = it['x0'], it['x1'], it['y'], it['h']
            tip = min(18.0, (b - a) / 3)
            pts = [(a, y - h / 2), (b - tip, y - h / 2), (b, y), (b - tip, y + h / 2), (a, y + h / 2)]
        else:
            pts = [(it['x0'], it['y0']), (it['x1'], it['y0']), (it['x1'], it['y1']), (it['x0'], it['y1'])]
        me = bpy.data.meshes.new(f'{B.LABEL_PREFIX}Map_{k:02d}')
        me.from_pydata([(x, -yy, 0) for x, yy in pts], [], [tuple(range(len(pts)))])
        me.materials.append(mats[it['color']])
        col.objects.link(bpy.data.objects.new(me.name, me))


def draw_footer(lscene):
    col = lscene.collection.children[0]
    f0, f1, body = B.FOOTER
    cu = bpy.data.curves.new(B.LABEL_PREFIX + 'Footer', 'FONT')
    cu.body, cu.size, cu.align_x, cu.align_y = body, 16, 'RIGHT', 'BOTTOM_BASELINE'
    cu.materials.append(fade_material(B.LABEL_PREFIX + 'Footer', B.INK['dark'], f0, f1))
    obj = bpy.data.objects.new(cu.name, cu)
    obj.location = (RES[0] - 96, -(RES[1] - 30), 0)
    col.objects.link(obj)


def web_extras(items):
    """Locus map and notice for the web page: positions as fractions of the frame, sizes as fractions of its
    height, colours as hex."""
    W, H = RES
    hexes = {k: '#%02x%02x%02x' % tuple(rgb) for k, rgb in {**B.DIAGRAM_RGB, 'ink': B.INK['dark']}.items()}
    out = []
    for it in items:
        o = dict(it)
        for k in ('x', 'x0', 'x1'):
            if k in o:
                o[k] = round(o[k] / W, 4)
        for k in ('y', 'y0', 'y1', 'h', 'size'):
            if k in o:
                o[k] = round(o[k] / H, 4)
        out.append(o)
    f0, f1, body = B.FOOTER
    return {'diagram': {'start': T['diagram'][0], 'end': T['diagram'][1], 'colors': hexes, 'items': out},
            'notice': {'start': f0, 'end': f1, 'text': body}}


# ----------------------------------------------------------------------------- build

def build():
    scene = SC.reset_scene(SCENE_NAME, PREFIX)
    col_dna, col_mol, col_rig = (SC.collection(scene, PREFIX + c) for c in ('DNA', 'Molecules', 'Rig'))
    rng = np.random.default_rng(29)
    report = {}

    # --- the locus and its DNA, atom by atom
    loc_ = A.locus()
    seq, first, rep = loc_['seq'], loc_['first'], loc_['repeats']
    tmpl, step, fit = A.templates(BNA)
    span = A.sub(seq, first, *B.GENOME)
    helix = A.nucleic_table(A.straight_helix(span, tmpl, step), span)
    names = helix['name']
    edges = np.array([(a, b) for a, b in St.bonds(helix) if {names[a], names[b]} != {"O3'", 'P'}])
    links = A.o3p_links(helix)
    relaxed, closing = A.close_backbone(helix, edges, links)
    edges = np.vstack([edges, np.array(links)])
    path = A.smooth_path(B.DNA_WAYPOINTS, spacing=1.0)
    xyz, _ = A.bend(relaxed, path)
    zc = np.array([helix['xyz'][helix['bp'] == k][:, 2].mean() for k in range(len(span))])     # as version 2

    def axis_point(g):
        return A.bend(np.array([[0.0, 0.0, zc[g - B.GENOME[0]]]]), path)[0][0]
    centre = axis_point(B.CENTRE_BP)
    xyz -= centre

    def dna_point(g):
        return axis_point(g) - centre
    bp, strand = helix['bp'], helix['strand']
    gpos = bp + B.GENOME[0]
    n_dna = len(xyz)
    lit_bp = np.full(len(span), 1e6)
    for k, c in enumerate(rep['copies']):
        lit_bp[np.isin(np.arange(len(span)) + B.GENOME[0], c['lit'])] = B.LIT[k]
    back = np.isin(names, list(A.BACKBONE_NA))
    phos = np.isin(names, ['P', 'OP1', 'OP2'])
    along = (helix['resi'] - 1) / (len(span) - 1)

    def dna_colors(strands, base_rgb, phosphate_rgb):
        col = np.tile(np.array(lin(base_rgb)), (n_dna, 1))
        for el, rgb in B.ELEMENT.items():
            col[helix['element'] == el] = lin(rgb)
        for k in (0, 1):
            on = back & (strand == k)
            col[on] = ramp(strands[k], along[on])
        col[phos] = lin(phosphate_rgb)
        return col
    vdw = St.radii(helix['element'])
    ball = np.full(n_dna, B.DNA_STICK) / vdw
    for nm, mult in B.BALL.items():
        ball[names == nm] = B.DNA_STICK * mult / vdw[names == nm]

    mrng = np.random.default_rng(43)
    times, rate = D.clock(FRAMES, B.CLOCK_NS / FPS)
    window = rate * B.EXPOSURE
    win = float(np.median(window))
    report['clock'] = {'ns_per_film_second': B.CLOCK_NS, 'shutter': B.SHUTTER, 'window_frames': B.EXPOSURE, 'window_ns': round(win, 2)}
    clock = SC.empty(PREFIX + 'Clock', col_rig)
    rig.bake_track(clock, np.stack([times, np.zeros(FRAMES), np.zeros(FRAMES)], 1))
    T_, N_, B_ = A.rmf(path)
    k_ = np.clip(np.rint(zc).astype(int), 0, len(path) - 1)
    axis_bp = A.bend(np.stack([np.zeros_like(zc), np.zeros_like(zc), zc], axis=1), path)[0] - centre

    def along_axis(bps):
        return {'s': ('FLOAT', zc[bps]), 'axis_p': ('FLOAT_VECTOR', axis_bp[bps]), 'tan': ('FLOAT_VECTOR', T_[k_][bps]),
                'nrm': ('FLOAT_VECTOR', N_[k_][bps]), 'bin': ('FLOAT_VECTOR', B_[k_][bps]), 'lit_t': ('FLOAT', lit_bp[bps])}
    M = B.DNA_MOTION
    waves = D.wlc_bend(M['waves'], M['persistence'], B.TEMP, friction=M['friction'])
    bend = [(rms * D.exposure_factor(tau, win, B.SHUTTER), max(tau, win), lam) for lam, (rms, tau) in zip(M['waves'], waves)]
    tw_rms, tw_tau = D.wlc_twist(M['twist_length'], M['twist_persistence'], B.TEMP, friction=M['friction'])
    twist = (tw_rms * D.exposure_factor(tw_tau, win, B.SHUTTER), max(tw_tau, win), M['twist_length'])
    motion_dna = groups.chain_motion(PREFIX, clock, bend, twist)
    lit = lit_group(PREFIX)
    ctl_detail = SC.empty(PREFIX + 'Ctl_Detail', col_rig)   # x: 1 atom by atom, 0 space-filling
    ctl_on = SC.empty(PREFIX + 'Ctl_On', col_rig, (1.0, 0.0, 0.0))
    SC.keys(ctl_detail, 'location', [(1, 1.0), (T['detail'][0], 1.0), (T['detail'][1], 0.0)], 0)
    atom_mat = look.attr_material(PREFIX + 'Atom', roughness=0.4, specular=0.45)
    bs_dna = groups.ball_stick(PREFIX, stick=B.DNA_STICK, fill=B.FILL_SCALE, name='BallStickDNA')
    plates_ng = groups.plates(PREFIX)
    dna = mesh.points_mesh(PREFIX + 'DNA', xyz, edges, {
        'vdw': ('FLOAT', vdw), 'ball': ('FLOAT', ball), 'u': ('FLOAT', np.zeros(n_dna)),
        'col_ctx': ('FLOAT_COLOR', dna_colors(B.DNA_STRANDS, B.DNA_BASE, B.PHOSPHATE)),
        'col_hi': ('FLOAT_COLOR', dna_colors((B.LIT_STRAND, B.LIT_STRAND), B.LIT_BASE, B.LIT_PHOSPHATE)),
        **along_axis(bp)}, col_dna)
    stack(dna, [('Motion', motion_dna, {}), ('Lit', lit, {}),
                ('Atoms', bs_dna, {'Material': atom_mat, 'Detail': ctl_detail, 'Show': ctl_on})])
    table = {**helix, 'xyz': xyz}
    nts = Ct.nucleotides(table)
    fv, ff, fa = Ct.ring_fills(table)
    nt_bp = np.array([n['resi'] - 1 if n['chain'] == 'A' else len(span) - n['resi'] for n in nts])
    nt_strand = np.array([0 if n['chain'] == 'A' else 1 for n in nts])
    vbp = nt_bp[fa['nt'].astype(int)]
    vst = nt_strand[fa['nt'].astype(int)]
    sugar = fa['part'] == 0

    def plate_colors(strands, base_rgb):
        c = np.tile(np.array(lin(base_rgb)), (len(fv), 1))
        for k in (0, 1):
            on = sugar & (vst == k)
            c[on] = ramp(strands[k], np.full(int(on.sum()), 0.75))
        return c
    pid = fa['plate'].astype(int)
    centres = np.zeros((pid.max() + 1, 3))
    np.add.at(centres, pid, fv)
    centres /= np.bincount(pid)[:, None]
    dna_plates = mesh.surface_mesh(PREFIX + 'DNARings', fv, ff, {
        'col_ctx': plate_colors(B.DNA_STRANDS, B.DNA_BASE), 'col_hi': plate_colors((B.LIT_STRAND, B.LIT_STRAND), B.LIT_BASE),
        'centre': ('FLOAT_VECTOR', centres[pid]), 'u': ('FLOAT', np.zeros(len(fv))), **along_axis(vbp)}, col_dna)
    fill_mat = look.skin_material(PREFIX + 'Fill', *B.PLATE_OPACITY['dna'])
    stack(dna_plates, [('Motion', motion_dna, {}), ('Lit', lit, {}),
                       ('Plates', plates_ng, {'Material': fill_mat, 'Detail': ctl_detail, 'Show': ctl_on})])
    report['dna_motion'] = {'bend_rms_A_tau_ns_wave_A': [[round(v, 2) for v in b] for b in bend],
                            'twist_rms_deg_tau_ns': [round(math.degrees(twist[0]), 1), round(twist[1], 2)]}
    report['dna'] = {'bp': len(span), 'atoms': n_dna, 'template_fit': fit, 'backbone_closing': closing,
                     'bonds': len(edges), 'phosphodiester_links': len(links), 'ring_plates': int(pid.max() + 1),
                     'bend_strain_A': round(A.neighbour_strain(relaxed, xyz + centre), 3),
                     'lit_nt': int(sum(len(c['lit']) for c in rep['copies'])), 'lit_bp': int((lit_bp < 1e5).sum())}

    # --- rig
    cam = bpy.data.objects.new(PREFIX + 'Camera', bpy.data.cameras.new(PREFIX + 'Camera'))
    col_rig.objects.link(cam)
    scene.camera = cam
    aim = SC.empty(PREFIX + 'Aim', col_rig)
    target = SC.empty(PREFIX + 'CutTarget', col_rig)
    slab = SC.empty(PREFIX + 'Slab', col_rig, (0, 1e5, 0))
    ctl_cut = SC.empty(PREFIX + 'Ctl_Cut', col_rig)
    ctl_look = SC.empty(PREFIX + 'Ctl_Look', col_rig)
    ctl_path = SC.empty(PREFIX + 'Ctl_Path', col_rig)

    # --- the four array RNAs, atom by atom (version 2's motion streams, in version 2's order)
    rna_mat = look.attr_material(PREFIX + 'RNA', roughness=0.4, specular=0.45, alpha='alpha')
    rna_fill = look.skin_material(PREFIX + 'RNAFill', *B.PLATE_OPACITY['rna'])
    bs_rna = groups.ball_stick(PREFIX, stick=B.RNA_STICK, fill=B.FILL_SCALE, name='BallStickRNA')
    rna_tracks, rna_world, rna_rep = {}, {}, {}
    for k, key in enumerate(('W1', 'W2', 'W3', 'W4')):
        t = A.model(A.JOBS[key])
        X = t['xyz'] - t['xyz'].mean(0)
        X = X @ A.principal_frame(X).T
        (off, (ty, tz)) = B.RNA_PLACE[key]
        R0 = turn(ty, tz)
        a, b = A.WINDOWS[key]
        base = dna_point((a + b) // 2) + np.array(off, float)
        shift, Rt, motion = tumbling(X, mrng, times, window)
        locs = base + shift
        Rs = R0 @ Rt
        shapes, q, mtable, mode_attrs, modes_rep = normal_modes(key, X, t, B.ANM['rna'], 7.5, mrng, times, window, col_rig)
        n = len(X)
        tt = {**t, 'xyz': X}
        p = t['plddt']
        w = np.clip((p - 30.0) / 40.0, 0, 1)
        nb = np.isin(t['name'], list(A.BACKBONE_NA))
        rphos = np.isin(t['name'], ['P', 'OP1', 'OP2'])
        cols = color.shade(rng, B.RNA_TEAL, n) * w[:, None] + np.array(lin(B.RNA_PALE)) * (1 - w[:, None])
        cols[~nb] = cols[~nb] * 0.45 + np.array(lin(B.RNA_PALE)) * 0.55
        cols[rphos] = lin(B.PHOSPHATE)
        rvdw = St.radii(t['element'])
        rball = np.full(n, B.RNA_STICK) / rvdw
        for nm, mult in B.BALL.items():
            rball[t['name'] == nm] = B.RNA_STICK * mult / rvdw[t['name'] == nm]
        obj = mesh.points_mesh(f'{PREFIX}RNA_{key}', X, St.bonds(tt), {
            'vdw': ('FLOAT', rvdw), 'ball': ('FLOAT', rball), 'col': ('FLOAT_COLOR', cols),
            'alpha': ('FLOAT', B.RNA_ALPHA[0] + (B.RNA_ALPHA[1] - B.RNA_ALPHA[0]) * w), 'u': ('FLOAT', rng.random(n)),
            **mode_attrs}, col_mol)
        show = SC.empty(f'{PREFIX}Ctl_Show_{key}', col_rig)
        f0 = T['rna'][k]
        SC.keys(show, 'location', [(1, 0.0), (f0, 0.0), (f0 + 30, 1.0)], 0)
        dyn = groups.dynamics(PREFIX, mtable, FRAMES, q.shape[1], name=f'Dynamics_{key}')
        stack(obj, [('Motion', dyn, {}), ('Atoms', bs_rna, {'Material': rna_mat, 'Detail': ctl_on, 'Show': show})])
        obj.visible_shadow = False
        # Ring plates: each vertex moves with its nucleotide (mean mode shape of the residue's atoms).
        rv, rf, ra = Ct.ring_fills(tt)
        rnts = Ct.nucleotides(tt)
        res_atoms = [np.nonzero((t['chain'] == nt['chain']) & (t['resi'] == nt['resi']))[0] for nt in rnts]
        res_shape = np.array([shapes[ix].mean(0) for ix in res_atoms])           # (nts, 3, modes)
        res_w = np.array([w[ix].mean() for ix in res_atoms])
        rnt = ra['nt'].astype(int)
        rpid = ra['plate'].astype(int)
        rcen = np.zeros((rpid.max() + 1, 3))
        np.add.at(rcen, rpid, rv)
        rcen /= np.bincount(rpid)[:, None]
        pcol = np.array(lin(B.RNA_TEAL[1])) * res_w[rnt][:, None] + np.array(lin(B.RNA_PALE)) * (1 - res_w[rnt][:, None])
        pcol[ra['part'] == 1] = pcol[ra['part'] == 1] * 0.45 + np.array(lin(B.RNA_PALE)) * 0.55
        plate_u = rng.random(rpid.max() + 1)
        pl = mesh.surface_mesh(f'{PREFIX}RNARings_{key}', rv, rf, {
            'col': pcol, 'centre': ('FLOAT_VECTOR', rcen[rpid]), 'u': ('FLOAT', plate_u[rpid]),
            **{f'm{j}': ('FLOAT_VECTOR', res_shape[rnt, :, j]) for j in range(q.shape[1])}}, col_mol)
        stack(pl, [('Motion', dyn, {}), ('Plates', plates_ng, {'Material': rna_fill, 'Detail': ctl_on, 'Show': show})])
        pl.visible_shadow = False
        pl.parent = obj
        euler_keys(obj, locs, Rs)
        rna_tracks[key] = locs
        rna_world[key] = (X, locs, Rs, shapes, q)
        rna_rep[key] = {'nt': int(len(np.unique(t['resi']))), 'atoms': n, 'bonds': len(obj.data.edges),
                        'ring_plates': int(rpid.max() + 1), 'mean_plddt': round(float(p.mean()), 1),
                        'extent_A': [round(float(v)) for v in np.ptp(X, 0)], 'tumbling': motion, 'modes': modes_rep}
    report['rnas'] = rna_rep

    # --- the reverse transcriptase: a cartoon coloured by confidence, YADD in ball-and-stick
    t = A.model(A.JOBS['RT'])
    ca = t['name'] == 'CA'
    yadd = (t['resi'] >= A.YADD[0]) & (t['resi'] <= A.YADD[1])
    c0 = t['xyz'].mean(0)
    X = t['xyz'] - c0
    v = X[yadd].mean(0)
    up = A.principal_frame(X)[0]
    fwd = -v / np.linalg.norm(v)
    up = up - fwd * (up @ fwd)
    up /= np.linalg.norm(up)
    right = np.cross(fwd, up)
    R = np.stack([right, fwd, up])
    rt_pos = dna_point(B.RT_PLACE[1]) + np.array(B.RT_PLACE[0], float)
    Xrt = X @ R.T + rt_pos
    p = t['plddt']
    n = len(Xrt)
    sure = p >= 70
    c_rt = Xrt.mean(0)
    Xl = Xrt - c_rt
    rt_shift, rt_R, rt_motion = tumbling(Xl, np.random.default_rng(B.RT_SEED), times, window)
    rt_shapes, rt_q, rt_table, rt_modes, rt_modes_rep = normal_modes('RT', Xl, t, B.ANM['rt'], 4.3, mrng, times, window, col_rig)
    topo = D.chi_topology(t['resn'], t['resi'], t['name'])
    probe = np.array([next((i for nm in ('CB', 'CA') for i in np.nonzero(topo['slot'] == r)[0] if t['name'][i] == nm))
                      for r in range(topo['residues'])])
    crowd = D.burial(Xl, probe)
    exposed = np.clip((np.percentile(crowd, 90) - crowd) / np.ptp(np.percentile(crowd, [10, 90])), 0, 1)
    chi = D.ou(mrng, times, window, (topo['residues'], 2), np.radians(B.CHI['sd'][0] + (B.CHI['sd'][1] - B.CHI['sd'][0]) * exposed)[:, None],
               (B.CHI['tau'][0] * (B.CHI['tau'][1] / B.CHI['tau'][0]) ** exposed)[:, None], **B.SHUTTER_ARGS)
    chi_tab = mesh.table(PREFIX + 'Chi_RT', {'chi': np.pad(chi, ((0, 0), (0, 0), (0, 1))).reshape(-1, 3)}, col_rig)
    dyn_rt = groups.dynamics(PREFIX, rt_table, FRAMES, rt_q.shape[1], chi_tab, topo['residues'], name='Dynamics_RT')
    dyn_rt_modes = groups.dynamics(PREFIX, rt_table, FRAMES, rt_q.shape[1], name='DynamicsModes_RT')
    band = np.where(p >= 90, 90, np.where(p >= 70, 70, 0))
    rt_col = np.array([lin(B.RT_BANDS[b_]) for b_ in band])
    rt_alpha = np.array([B.RT_ALPHA[b_] for b_ in band])
    tl = {**t, 'xyz': Xl}
    rv, rf, ra, rsegs = Ct.cartoon(tl, None, per_atom={'col': rt_col, 'alpha': rt_alpha,
                                                       **{f'm{k}': rt_shapes[:, :, k] for k in range(rt_q.shape[1])}})
    rt_obj = mesh.surface_mesh(PREFIX + 'RT', rv, rf, {
        'col': ra['col'], 'alpha': ra['alpha'], 'ring': ('INT', ra['ring']),
        **{f'm{k}': ('FLOAT_VECTOR', ra[f'm{k}']) for k in range(rt_q.shape[1])}}, col_mol)
    rt_obj.data.materials.append(look.ribbon_material(PREFIX + 'Ribbon', alpha='alpha'))
    stack(rt_obj, [('Section', groups.section(PREFIX, name='SectionRT', space='RELATIVE', group='ring'),
                    {'Camera': cam, 'Target': target, 'Slab': slab, 'Cut': ctl_cut, 'Cut Enable': 1.0, 'Funnel': 8.0}),
                   ('Motion', dyn_rt_modes, {})])
    # YADD: side chains (from Calpha) in ball-and-stick, hidden until revealed (Look.x)
    side = ~np.isin(t['name'], ['N', 'C', 'O'])
    sel = yadd & side
    idx = np.nonzero(sel)[0]
    sub = St.select(t, sel)
    e_y = St.bonds(sub, Xl[idx])
    hi = np.tile(np.array(lin(B.AMBER)), (len(idx), 1))
    for el, rgb in B.ELEMENT.items():
        hi[sub['element'] == el] = lin(rgb)
    turns = D.chi_topology(sub['resn'], sub['resi'], sub['name'])
    ones, zeros = np.ones(len(idx)), np.zeros(len(idx))
    yobj = mesh.points_mesh(PREFIX + 'YADD', Xl[idx], e_y, {
        'vdw': ('FLOAT', St.radii(sub['element'])), 'role': ('FLOAT', ones), 'ball': ('FLOAT', ones), 'stick_w': ('FLOAT', ones),
        'dilate': ('FLOAT_VECTOR', np.zeros((len(idx), 3))), 'g0': ('FLOAT', zeros), 'g1': ('FLOAT', ones), 'g2': ('FLOAT', zeros),
        'col_ctx': ('FLOAT_COLOR', hi), 'col_hi': ('FLOAT_COLOR', hi), 'emit_w': ('FLOAT', zeros), 'glow_w': ('FLOAT', zeros),
        **{k_: (kind, val[idx]) for k_, (kind, val) in rt_modes.items()},
        'res_i': ('FLOAT', topo['slot'][idx]), **{k_: ('FLOAT', turns[k_]) for k_ in ('chi1_w', 'chi2_w', 'i_ca', 'i_cb', 'i_cg')}},
        col_mol)
    yng = groups.molecule(PREFIX, None, 0.0, 0.26, 0.15, (220, 228, 240), 0.0, name='YADD', thermal_group=dyn_rt, space='RELATIVE')
    stack(yobj, [('Atoms', yng, {'Material': atom_mat, 'Camera': cam, 'Target': target, 'Slab': slab, 'Cut': ctl_cut,
                                 'Look': ctl_look, 'Cut Enable': 0.0, 'Path Control': ctl_path})])
    for obj in (rt_obj, yobj):
        euler_keys(obj, c_rt + rt_shift, rt_R)
        for f, hidden in ((1, True), (T['rt_in'], False)):
            obj.hide_render = obj.hide_viewport = hidden
            obj.keyframe_insert('hide_render', frame=f)
            obj.keyframe_insert('hide_viewport', frame=f)

    def rt_track(local):
        return c_rt + rt_shift + rt_R @ local
    yadd_local = Xl[yadd & side].mean(0)
    yadd_pt, yadd_track = c_rt + yadd_local, rt_track(yadd_local)
    low_track = rt_track(Xl[~sure & ca].mean(0))
    rss = np.concatenate([sg['ss'] for sg in rsegs])
    report['rt'] = {'atoms': n, 'residues': int(ca.sum()), 'plddt_ge_70_atoms': round(float(sure.mean()), 3),
                    'yadd_plddt': round(float(p[yadd].mean()), 1), 'yadd_depth_from_centroid_A': round(float(np.linalg.norm(v)), 1),
                    'cartoon': {'segments': len(rsegs), 'helix': int((rss == Ct.HELIX).sum()), 'strand': int((rss == Ct.STRAND).sum()),
                                'vertices': len(rv)},
                    'tumbling': rt_motion, 'modes': rt_modes_rep,
                    'yadd_travel_A': round(float(np.linalg.norm(yadd_track - yadd_pt, axis=1).max()), 1)}

    # --- the partner: a translucent coral cartoon (mean pLDDT 33) that fades in
    t = A.model(A.JOBS['PARTNER'])
    X = t['xyz'] - t['xyz'].mean(0)
    n = len(X)
    p = t['plddt']
    w = np.clip((p - 25.0) / 45.0, 0, 1)
    p_pos = Xrt.mean(0) + np.array(B.PARTNER_OFFSET)
    R0 = turn(20, 140)
    shift, Rt, p_motion = tumbling(X, mrng, times, window)
    Rs = R0 @ Rt
    plocs = p_pos + shift
    p_shapes, p_q, p_table, p_modes, p_modes_rep = normal_modes('Partner', X, t, B.ANM['partner'], 4.3, mrng, times, window, col_rig)
    pv, pf, pa, psegs = Ct.cartoon({**t, 'xyz': X}, None, per_atom={
        'col': np.tile(np.array(lin(B.PARTNER)), (n, 1)),
        'alpha0': B.PARTNER_ALPHA[0] + (B.PARTNER_ALPHA[1] - B.PARTNER_ALPHA[0]) * w,
        **{f'm{k}': p_shapes[:, :, k] for k in range(p_q.shape[1])}})
    pobj = mesh.surface_mesh(PREFIX + 'Partner', pv, pf, {
        'col': pa['col'], 'alpha0': pa['alpha0'], **{f'm{k}': ('FLOAT_VECTOR', pa[f'm{k}']) for k in range(p_q.shape[1])}}, col_mol)
    pobj.data.materials.append(look.ribbon_material(PREFIX + 'PartnerRibbon', alpha='alpha'))
    pshow = SC.empty(PREFIX + 'Ctl_Show_Partner', col_rig)
    SC.keys(pshow, 'location', [(1, 0.0), (T['partner'][0], 0.0), (T['partner'][1], 1.0)], 0)
    stack(pobj, [('Motion', groups.dynamics(PREFIX, p_table, FRAMES, p_q.shape[1], name='Dynamics_Partner'), {}),
                 ('Fade', fade_group(PREFIX), {'Show': pshow})])
    pobj.visible_shadow = False
    euler_keys(pobj, plocs, Rs)
    pss = np.concatenate([sg['ss'] for sg in psegs])
    report['partner'] = {'tumbling': p_motion, 'modes': p_modes_rep,
                         'cartoon': {'helix': int((pss == Ct.HELIX).sum()), 'strand': int((pss == Ct.STRAND).sum()), 'vertices': len(pv)}}

    # --- clearances (version 2's check, with the same motion): nothing touches
    gaps, reach = {}, 120.0
    for f in range(1, FRAMES + 1, 16):
        world = {key: (X_ + sh_ @ q_[f - 1]) @ Rs_[f - 1].T + locs_[f - 1]
                 for key, (X_, locs_, Rs_, sh_, q_) in rna_world.items()}
        world['partner'] = (X + p_shapes @ p_q[f - 1]) @ Rs[f - 1].T + plocs[f - 1]
        world['rt'] = (Xl + rt_shapes @ rt_q[f - 1]) @ rt_R[f - 1].T + c_rt + rt_shift[f - 1]
        world['dna'] = xyz
        keys_ = list(world)
        for i, a in enumerate(keys_):
            for b in keys_[i + 1:]:
                Q = near(world[a], world[b], reach)
                d = min(min_distance(world[a], Q), reach) if len(Q) else reach
                gaps[f'{a}-{b}'] = min(gaps.get(f'{a}-{b}', reach), d)
    report['min_gap_A'] = {k: round(v, 1) for k, v in gaps.items() if v < reach}

    # --- camera and choreography (version 2's)
    unit_pts = {key: dna_point((a + b) // 2) for key, (a, b) in A.WINDOWS.items()}
    points = {
        'dna_start': dna_point(9548), 'rep1': dna_point((rep['copies'][0]['start'] + rep['copies'][0]['end']) // 2),
        'array': (dna_point(rep['copies'][0]['start']) + dna_point(rep['copies'][-1]['end'])) / 2,
        'w23': (rna_tracks['W2'][0] + rna_tracks['W3'][0] + unit_pts['W2'] + unit_pts['W3']) / 4,
        'w4': (2 * rna_tracks['W4'][0] + unit_pts['W4']) / 3,
        'yadd': yadd_pt, 'pair': (Xrt.mean(0) + p_pos) / 2,
        'tableau': (rna_tracks['W4'][0] + Xrt.mean(0) + p_pos) / 3 + np.array([0.0, 0.0, 50.0]),
    }
    cam_path = TL.camera_path(B.CAMERA, points, FRAMES)
    a0, a1, b0, b1 = T['follow']
    follow = np.array([TL.ramp(f, a0, a1) * (1 - TL.ramp(f, b0, b1)) for f in range(1, FRAMES + 1)])
    drift = (yadd_track - yadd_pt) * follow[:, None]
    cam_path = [(f, loc + d, aim_pt + d, dist, lens) for (f, loc, aim_pt, dist, lens), d in zip(cam_path, drift)]
    rig.bake_camera(cam, aim, cam_path, B.APERTURE_RATIO, clip=(1.0, 60000))
    rig.bake_track(target, yadd_track)
    SC.keys(ctl_cut, 'location', [(1, 0.0), (T['cut'][0], 0.0), (T['cut'][1], 1.0), (T['uncut'][0], 1.0), (T['uncut'][1], 0.0)], 0)
    SC.keys(ctl_look, 'location', [(1, 0.0), (T['yadd'][0], 0.0), (T['yadd'][1], 1.0)], 0)

    # --- white world and light (no bloom: nothing here emits light)
    scene.world = look.gradient_world(PREFIX + 'World', (255, 255, 255), (255, 255, 255), B.AMBIENT_RGB, B.AMBIENT_STRENGTH)[0]
    for nm, (d, e, rgb) in (('Key', B.KEY), ('Fill', B.FILL), ('Rim', B.RIM)):
        SC.sun(PREFIX + nm, d, e, 24 if nm == 'Key' else 14, col_rig, rgb)
    SC.cycles_settings(scene, RES, FRAMES, FPS, samples=B.SAMPLES, transparent=24)
    scene.frame_set(1)
    SC.save_scene(scene, BLEND_PATH)

    # --- labels: the web page's data and the label pass (version 2's text, map and notice)
    anchors = {
        'rep1': points['rep1'], 'spacer1': dna_point((rep['copies'][0]['end'] + rep['copies'][1]['start']) // 2),
        **{k: rna_tracks[k] for k in rna_tracks}, **{f'unit_{k}': unit_pts[k] for k in unit_pts},
        'yadd': yadd_track, 'rt_low': low_track, 'rt': c_rt + rt_shift, 'partner': plocs,
        'rep_first': dna_point(rep['copies'][0]['start']), 'rep_last': dna_point(rep['copies'][-1]['end']),
    }
    spec = dict(B.LABELS)
    guide = []
    for k, key in enumerate(('W1', 'W2', 'W3', 'W4')):
        f0 = T['rna'][k]
        guide.append((f0 + 4, f0 + 96, f'unit_{key}', key, {'trim': (12, 70)}))
    spec['links'] = guide + [
        (628, 744, 'rt', 'partner', {'dashes': 7, 'trim': (100, 80), 'text': '?', 'size': 36}),
        (644, 744, 'rt', 'W4', {'dashes': 9, 'trim': (100, 150), 'text': '?', 'size': 36}),
        (660, 744, 'partner', 'W4', {'dashes': 15, 'trim': (80, 150), 'text': '?', 'size': 36}),
    ]
    items, array_px = diagram_items(rep)
    web = TL.label_data(spec, cam_path, anchors, RES, FRAMES, FPS, levels=B.TAG_LEVELS, layout={'time_prefix': ''})
    for lk, (_, _, _, _, opts) in zip(web['links'], spec['links']):
        lk['trim'] = [round(v / RES[0], 4) for v in opts.get('trim', (0, 0))]
    web.update(web_extras(items))
    WEB_LABELS.parent.mkdir(parents=True, exist_ok=True)
    WEB_LABELS.write_text(json.dumps(web, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    label_result = labels.label_pass(B.LABEL_SCENE, B.LABEL_PREFIX, spec, cam_path, anchors, RES, FRAMES, FPS, LABEL_BLEND,
                                     layout={'time_prefix': ''})
    lscene = bpy.data.scenes[B.LABEL_SCENE]
    draw_diagram(lscene, items)
    draw_footer(lscene)
    SC.save_scene(lscene, LABEL_BLEND)
    SC.show(scene)

    result = {
        'blender': bpy.app.version_string, 'scene': scene.name, 'frames': FRAMES,
        'locus': {'repeat_window': rep['window'], 'repeat_length': rep['length'], 'consensus': rep['consensus'],
                  'copies': [{k: c[k] for k in ('core', 'start', 'end', 'identity')} for c in rep['copies']],
                  'spacers_nt': loc_['spacers'], 'periods_nt': loc_['periods'], 'tract_AT': loc_['tract_at'],
                  'minus_strand_hits': len(loc_['hits']['-'])},
        **report,
        'confidence': A.confidence_report(),
        'points': {k: [round(float(c), 1) for c in v] for k, v in points.items()},
        'labels': {**label_result, 'links': len(spec['links']), 'array_px': array_px, 'web': str(WEB_LABELS)},
        'objects': len(scene.objects), 'blend': str(BLEND_PATH),
    }
    # Version 2's science and motion must come out unchanged: the drawing changed, not the model.
    if V2_RESULT.exists():
        v2 = json.loads(V2_RESULT.read_text())
        same = {k: v2.get(k) == json.loads(json.dumps(result[k], default=str)) for k in ('locus', 'confidence', 'points')}
        same['rna_tumbling'] = all(v2['rnas'][k]['tumbling'] == json.loads(json.dumps(result['rnas'][k]['tumbling']))
                                   for k in result['rnas'])
        same['rt_tumbling'] = v2['rt']['tumbling'] == json.loads(json.dumps(result['rt']['tumbling']))
        same['partner_tumbling'] = v2['partner']['tumbling'] == json.loads(json.dumps(result['partner']['tumbling']))
        result['same_as_v2'] = same
    return result


RESULT = build()
