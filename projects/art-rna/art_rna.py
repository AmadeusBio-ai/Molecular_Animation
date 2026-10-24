"""ART: a hidden repertoire of RNA. The array of phage SA1, the RNAs it is expressed as, the reverse transcriptase
beside it, and the open question of how they work together.

Scientific illustration after sources/CRISPR-Like.txt (an AI-generated brief), its recommended core: the repeat
array reveal (section 1), the RNA repertoire (section 3) and the unresolved partner (section 6), in the studio
"mist" look of amadeusbio.ai. The phage exterior (section 2) and the comparison systems 6AR1, 9LM3 and 8QBM
(sections 4, 5, 7) are not in this film: they are not ART structures (see brief.md).

Coordinates and evidence (see art_locus.py and record.md):
  DNA      GenBank MW218148.1 positions 9421-10900, built base pair by base pair from 1BNA templates (ideal B-DNA
           step) and bent onto an illustrative path. Repeat positions are our sequence comparison.
  RNAs     AlphaFold Server (AlphaFold 3) model 0 of the four genomic-window RNAs W1-W4: low confidence (mean
           pLDDT 40-50), endpoints are window choices, not mapped transcripts. Drawn translucent.
  RT       AlphaFold 3 model 0 of QPI16926.1 (pTM 0.80): pLDDT >= 70 solid, below 70 translucent.
  Partner  AlphaFold 3 model 0 of QPI16927.1 (pTM 0.21, mean pLDDT 33): translucent throughout.
  No complex is shown: every complex prediction had ipTM <= 0.24. The molecules are placed apart, by hand.
Motion (docs/motion.md): Brownian tumbling and diffusion of the free molecules at hydrodynamic rates, their
normal modes, the RT's side-chain turns and the DNA's worm-like-chain bending and twisting, on one clock
(1 s = 5 ns). Rates from the literature; illustrative, not simulated.
AlphaFold Server output is subject to the AlphaFold Server Output Terms of Use (af3/terms_of_use.md).

Beats (24 fps): close on the DNA, the first repeat lights (0-3 s) -> pull back as four more recur (3-8 s) ->
the array beside the RT gene, locus diagram (8-10.5 s) -> four array RNAs resolve beneath their units (11-17.5 s)
-> travel to the reverse transcriptase, its YADD motif (18-24.5 s) -> orbit to the partner: open questions (25-31 s).

Run:  python pipeline.py build art-rna        or, in Blender through MCP:
    import runpy; runpy.run_path(r'<repo>/projects/art-rna/art_rna.py', run_name='__main__')['RESULT']
"""
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
from molanim import color  # noqa: E402
from molanim import dynamics as D  # noqa: E402
from molanim import structure as St  # noqa: E402
from molanim import timeline as TL  # noqa: E402
from molanim.blender import groups, labels, look, mesh, rig  # noqa: E402
from molanim.blender import scene as SC  # noqa: E402
from molanim.blender.nodes import by_type, new_group, set_modifier_inputs  # noqa: E402

if 'art_locus' in sys.modules:
    import importlib
    importlib.reload(A)

NAME, SCENE_NAME, PREFIX = 'art-rna', 'ArtRna', 'ART_'
BNA = ROOT / 'assets' / 'pdb' / '1BNA.cif'
BLEND_PATH = HERE / 'art-rna.blend'
FPS, FRAMES, RES = 24, 744, (1920, 1080)
SAMPLES = 96

# Stage: X along the array (left to right = 5' to 3' on the + strand), Y away from the camera, Z up.
# The DNA is the genomic + strand from GENOME[0]; the array centre (CENTRE_BP) sits at the origin.
GENOME = (9421, 10900)
CENTRE_BP = 9972
DNA_WAYPOINTS = [(0, 0, 0), (700, 90, 50), (1400, -40, -40), (2100, 70, 30), (2800, -60, -30), (3500, 40, 40),
                 (4200, -30, -20), (4900, 20, 10), (5600, 0, 0)]
# Each RNA hangs below and in front of its array unit (offset from the unit's DNA axis point), turned so its
# long axis lies across the frame with a tilt (deg about Y, then Z).
RNA_PLACE = {'W1': ((0, -200, -200), (14, -10)), 'W2': ((0, -90, -175), (-20, 25)),
             'W3': ((0, -260, -165), (35, 8)), 'W4': ((60, -140, -150), (-8, -20))}
RT_PLACE = ((-40, -200, -195), 10376)       # offset from the DNA point at the end of repeat 5; YADD faces -Y
PARTNER_OFFSET = np.array([175.0, 30.0, 95.0])     # from the RT centroid (stage axes)

# Timeline (frames). Editorial time, not molecular time.
LIT = [46, 100, 124, 144, 162]          # each repeat copy lights (copy 1 first, alone, then the rhythm)
T = {
    'diagram': (196, 258),              # locus diagram (label pass)
    'rna': [266, 284, 302, 320],        # W1-W4 resolve (30 frames each)
    'rt_in': 300,                       # the RT exists from here (off screen until the camera turns to it)
    'cut': (474, 516),                  # cutaway toward the YADD motif
    'yadd': (496, 528),                 # YADD side chains as ball-and-stick, glowing
    'uncut': (566, 600),
    'partner': (586, 628),              # the partner protein resolves
    'follow': (440, 490, 590, 640),     # the camera keeps the tumbling RT framed while it is close (in, in, out, out)
}

# Look (sRGB 0-255): the amadeusbio.ai "mist" look (projects/website/website.py LOOKS['mist']).
BACKDROP_TOP, BACKDROP_BOTTOM = (247, 249, 252), (219, 227, 236)
AMBIENT_RGB, AMBIENT_STRENGTH = (224, 230, 238), 0.50
KEY = ((-0.55, -0.75, 0.9), 3.4, (255, 250, 242))
RIM = ((0.6, 1.0, 0.5), 1.8, (255, 255, 255))
FILL = ((0.3, -1.0, -0.2), 0.4, (236, 242, 250))
DNA_BACK = ((150, 166, 190), (196, 207, 222))       # sugar-phosphate backbone: slate
DNA_BASE = ((196, 206, 220), (232, 237, 244))       # bases: porcelain
AMBER = ((226, 136, 28), (255, 192, 84))            # the repeat (the website's accent)
RT_SURE = {90: ((20, 50, 98), (78, 110, 156)), 70: ((72, 102, 146), (128, 154, 190))}   # pLDDT >= 90 navy, 70-90 steel
RT_GHOST = ((170, 188, 214), (206, 218, 234))
RNA_TEAL = ((10, 112, 120), (64, 176, 176))         # RNA: teal, paler where pLDDT is lower
RNA_PALE = (150, 206, 206)
PARTNER = ((214, 112, 96), (240, 160, 140))         # partner: coral
ELEMENT = {'C': ((198, 205, 214), (236, 240, 244)), 'N': ((52, 94, 204), (96, 136, 236)),
           'O': ((208, 72, 62), (236, 112, 98)), 'S': ((226, 186, 40), (246, 214, 90))}
DNA_SCALE, PROTEIN_SCALE, GHOST_SCALE, BALL_SCALE, STICK_RADIUS = 0.70, 0.64, 0.56, 0.28, 0.16
GHOST_ALPHA = {'rna': (0.55, 0.88), 'rt': 0.55, 'partner': (0.50, 0.78)}   # alpha at low / high pLDDT
# Brownian and thermal motion (docs/motion.md; illustrative, from measured rates, not simulated). One clock:
# 1 s of film = CLOCK_NS ns at 37 C, and each frame shows a triangle-weighted average over EXPOSURE frames of it
# (a soft shutter: through a 3-frame box, take-02's tumbling RT lurched frame to frame). Free molecules
# diffuse and tumble as rigid bodies at Perrin-ellipsoid rates for their own shapes, slowed by the crowded
# cytoplasm, held near their places by a soft tether so the composition keeps. Inside, they flex by elastic-
# network normal modes, and the RT's side chains turn about their bonds. The DNA bends and twists as a worm-like
# chain about its designed path (the mean shape).
CLOCK_NS, EXPOSURE, SHUTTER, TEMP = 5.0, 16.0, 'triangle', 310.15
SHUTTER_ARGS = {'substeps': int(4 * EXPOSURE), 'shutter': SHUTTER}   # a quarter-frame grid
CROWDING = {'translation': 4.0, 'rotation': 2.0}    # short-time slow-down in cytoplasm vs water
TETHER = {'shift': 9.0, 'turn': 0.35}               # RMS A, rad
RT_SEED = 339       # the RT's own tumbling stream: of 3,000 seeds, the one whose close-up pose best matches take-02's
                    # (the active-site cleft toward the camera; mean 12.5 deg away over frames 474-600)
ANM = {'rt': (15.0, 24, 1.0, 50.0), 'partner': (15.0, 24, 2.0, 30.0), 'rna': (20.0, 24, 2.5, 60.0)}  # cutoff A, modes, mean node RMSF A, softest tau ns
CHI = {'sd': (8.0, 18.0), 'tau': (1.5, 0.3)}        # RT side chains, buried -> exposed: deg, ns
DNA_MOTION = {'persistence': 500.0, 'twist_persistence': 750.0, 'waves': (150.0, 300.0, 600.0), 'twist_length': 200.0,
              'friction': 2.0}                     # A; friction: cytoplasmic microviscosity vs water
BLOOM = {'threshold': 1.0, 'strength': 0.45, 'size': 0.6}
APERTURE_RATIO = 0.012

# Camera: (frame, aim, distance A, azimuth deg from front toward +X, elevation deg, lens mm).
CAMERA = [
    (1, ('dna_start', (0, 0, -4)), 165, -36, 12, 50),
    (72, ('rep1', (0, 0, -4)), 420, -24, 10, 50),
    (190, ('array', (0, 0, -120)), 5400, -6, 8, 50),
    (252, ('array', (0, 0, -130)), 5150, -3, 8, 50),
    (344, ('w23', (0, 0, -40)), 1300, -4, 6, 50),
    (424, 'w4', 1000, 6, 6, 50),
    (494, 'yadd', 235, 0, 6, 50),
    (566, 'yadd', 215, 7, 6, 50),
    (648, 'tableau', 960, 8, 4, 50),
    (744, 'tableau', 900, 11, 5, 50),
]

# Labels: a separate, cheap EEVEE pass composited at encode time. Positions in 1920x1080 pixels.
LABEL_SCENE, LABEL_PREFIX = 'ArtRna_Labels', 'ARTL_'
LABEL_BLEND = HERE / 'art-rna-labels.blend'
INK = {'dark': (10, 26, 49), 'light': (248, 250, 252)}
LABELS = {
    'ink': INK,
    'halo': {'dark': (240, 244, 248), 'light': (2, 15, 38)},
    'shot_ink': [(1, 'dark')],
    'header': (10, 258, 'ART  ·  ARRAY-ASSOCIATED REVERSE TRANSCRIPTASE  ·  STAPHYLOCOCCUS PHAGE SA1'),
    'captions': [
        (12, 168, 'A rhythm in a phage genome', 'A repeat recurs between unique spacers in the DNA of phage SA1'),
        (178, 258, 'A repeat array beside a reverse transcriptase gene',
         'The layout resembles a CRISPR array, but ART loci lack cas genes'),
        (268, 424, 'The array is expressed as distinct short RNAs',
         'Up to 8 % of phage RNA 15 min into infection; the shapes shown are uncertain predictions'),
        (436, 590, 'Beside it, a reverse transcriptase',
         'Its family copies RNA into DNA; whether this one is active is untested'),
        (602, 744, 'The components are emerging', 'Their molecular relationship remains to be resolved'),
    ],
    'tags': [
        (12, 258, 'SEQUENCE  ·  GENBANK MW218148.1  ·  DNA SHAPE ILLUSTRATIVE'),
        (268, 424, 'ALPHAFOLD 3 PREDICTIONS  ·  RNA ENDS ASSUMED'),
        (436, 590, 'ALPHAFOLD 3 PREDICTION  ·  RT QPI16926'),
        (602, 744, 'HYPOTHESES  ·  NO CONFIDENT INTERFACE PREDICTED'),
    ],
    'times': [
        (12, 258, 'Repeat positions: our comparison of the sequence'),
        (268, 424, 'Low confidence  ·  mean pLDDT 40–50'),
        (436, 590, 'pTM 0.80  ·  translucent: pLDDT below 70'),
        (602, 744, 'Partner mean pLDDT 33  ·  complexes ipTM ≤ 0.24'),
    ],
    'pointers': [
        (50, 128, 'rep1', 'Repeat', (150, -120)),
        (104, 150, 'spacer1', 'Spacer', (110, 110)),
        (282, 424, 'W1', 'Unit 1', (-70, 140)),
        (300, 424, 'W2', 'Unit 2', (-70, 140)),
        (318, 424, 'W3', 'Unit 3', (-70, 140)),
        (336, 424, 'W4', 'Unit 4', (-70, 140)),
        (504, 590, 'yadd', 'YADD motif', (270, -170)),
        (626, 744, 'rt', 'Reverse transcriptase', (-150, -190)),
        (640, 744, 'partner', 'Partner protein', (-70, -170)),
        (652, 744, 'W4', 'Array RNA', (-60, -160)),
    ],
    'links': [],                        # filled in build(): guides and hypotheses
}
DIAGRAM = {'y': 832, 'x': (300, 1620), 'span': (9421, 12951), 'h': (24, 14), 'scale_bp': 500}
DIAGRAM_RGB = {'line': (120, 136, 160), 'repeat': (236, 150, 40), 'rt': (52, 84, 136), 'partner': (214, 112, 96)}
FOOTER = (630, 744, 'Predicted structures: AlphaFold Server. AlphaFold Server Output Terms of Use apply.')


# ----------------------------------------------------------------------------- node groups and materials

def dna_group(prefix, breath):
    """DNA atoms -> spheres. Nucleotides light up from frame 'lit_t' (colour col_hi plus an emission pulse that
    settles to a glow)."""
    ng, g, gin, gout = new_group(prefix + 'DNA', [('Material', 'NodeSocketMaterial', None), ('Scale', 'NodeSocketFloat', DNA_SCALE),
                                                  ('Glow', 'NodeSocketFloat', 0.18), ('Pulse', 'NodeSocketFloat', 0.6)])
    I = gin.outputs
    geo = g.node('GeometryNodeGroup', {'Geometry': I['Geometry']}, node_tree=breath).outputs['Geometry']
    frame = g.node('GeometryNodeInputSceneTime').outputs['Frame']
    dt = g.math('SUBTRACT', frame, g.attr('lit_t'))
    h = g.smooth(dt, 0.0, 16.0)
    pulse = g.math('MULTIPLY', g.smooth(dt, 0.0, 5.0), g.math('SUBTRACT', 1.0, g.smooth(dt, 8.0, 46.0)))
    col = g.mix_color(h, g.attr('col_ctx', 'FLOAT_COLOR'), g.attr('col_hi', 'FLOAT_COLOR'))
    emit = g.math('MULTIPLY', h, g.math('ADD', I['Glow'], g.math('MULTIPLY', pulse, I['Pulse'])))
    geo = g.store(geo, 'col', col, 'FLOAT_COLOR')
    geo = g.store(geo, 'emit', emit)
    pts = g.node('GeometryNodeMeshToPoints', {'Mesh': geo, 'Radius': g.math('MULTIPLY', g.attr('vdw'), I['Scale'])},
                 mode='VERTICES').outputs['Points']
    g.put(g.material(pts, I['Material']), gout.inputs['Geometry'])
    return ng


def appear_group(prefix, thermal, name='Appear'):
    """Atoms -> spheres ('radius', 'col', 'alpha' attributes) that resolve as Show.x goes 0 -> 1: each atom grows
    in at its own moment (attribute 'u' in 0-1), so the molecule assembles as a dissolve, not in sequence order.
    `thermal` moves the atoms (a groups.dynamics group)."""
    ng, g, gin, gout = new_group(prefix + name, [('Material', 'NodeSocketMaterial', None), ('Show', 'NodeSocketObject', None)])
    I = gin.outputs
    show, _, _ = g.xyz(g.loc(I['Show']))
    grow = g.smooth(g.math('SUBTRACT', g.math('MULTIPLY', show, 1.6), g.math('MULTIPLY', g.attr('u'), 0.6)), 0.0, 1.0)
    geo = g.node('GeometryNodeGroup', {'Geometry': I['Geometry']}, node_tree=thermal).outputs['Geometry']
    r = g.math('MULTIPLY', g.attr('radius'), grow)
    pts = g.node('GeometryNodeMeshToPoints', {'Mesh': geo, 'Selection': g.math('GREATER_THAN', r, 0.03), 'Radius': r},
                 mode='VERTICES').outputs['Points']
    g.put(g.material(pts, I['Material']), gout.inputs['Geometry'])
    return ng


def ghost_attr_material(name, emission=0.22, roughness=0.36):
    """Translucent atoms: colour from 'col', alpha from 'alpha', a soft self-glow so they read on the pale
    backdrop. Low-confidence predictions are drawn with it."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    p = by_type(nt, 'BSDF_PRINCIPLED')
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Emission Strength'].default_value = emission
    col = nt.nodes.new('ShaderNodeAttribute')
    col.attribute_type, col.attribute_name = 'GEOMETRY', 'col'
    alpha = nt.nodes.new('ShaderNodeAttribute')
    alpha.attribute_type, alpha.attribute_name = 'GEOMETRY', 'alpha'
    nt.links.new(col.outputs['Color'], p.inputs['Base Color'])
    nt.links.new(col.outputs['Color'], p.inputs['Emission Color'])
    nt.links.new(alpha.outputs['Fac'], p.inputs['Alpha'])
    m.surface_render_method = 'DITHERED'
    return m


# ----------------------------------------------------------------------------- helpers

def euler_keys(obj, frames_xyz, frames_R):
    """Key an object's location and rotation on every frame from (frames, 3) locations and (frames, 3, 3)
    rotations; linear between frames (the motion is already smooth)."""
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
    """Tethered rigid-body Brownian motion of a molecule (rest coordinates X, about its centroid) at Perrin rates
    for its shape, 37 C, slowed by crowding: per frame a shift (A) and a rotation (3x3, in X's frame), and the
    rates as a report."""
    axes, semi = D.ellipsoid(X)
    D_t, D_r = D.perrin(semi, TEMP)
    D_t, D_r = D_t / CROWDING['translation'], D_r / CROWDING['rotation']
    shift, rv = D.rigid_brownian(rng, times, window, D_t, D_r, TETHER['shift'], TETHER['turn'], **SHUTTER_ARGS)
    Rs = axes.T @ D.rotation_matrix(rv) @ axes            # turns about the body axes, expressed in X's frame
    sec = FPS
    turned = [math.degrees(math.acos(np.clip((np.trace(Rs[f + sec] @ Rs[f].T) - 1) / 2, -1, 1))) for f in range(0, FRAMES - sec, 6)]
    return shift, Rs, {'semi_axes_A': [round(float(v)) for v in semi], 'D_t_um2_s': round(D_t * 1e-20 / 1e-9 * 1e12, 1),
                       'D_r_per_us': [round(float(v) * 1e3, 2) for v in D_r],
                       'per_film_second': {'shift_A': round(float(np.median(np.linalg.norm(shift[sec:] - shift[:-sec], axis=1))), 1),
                                           'turn_deg': round(float(np.median(turned)), 1)}}


def normal_modes(name, X, t, params, reach, rng, times, window, collection):
    """Elastic-network normal modes of one molecule (rest coordinates X of atom table t) with Langevin amplitudes
    on the clock: per-atom mode shapes, amplitudes per frame, the amplitude table, mode attributes and a report.
    params = (cutoff A, modes, mean node RMSF A, softest tau ns); reach = largest bonded node-node distance."""
    cutoff, count, rmsf, tau = params
    nodes, node_of = D.residue_nodes(t['resi'], t['name'])
    links = D.sequence_pairs(X, nodes, reach)
    eig, vec = D.anm(X[nodes], cutoff, modes=count, bonded=links)
    scale = D.mode_scale(eig, vec, rmsf)
    q = D.mode_amplitudes(rng, eig, times, window, scale, tau, **SHUTTER_ARGS)
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
    """Q's points within `reach` of P's bounding box (speeds up min_distance)."""
    lo, hi = P.min(0) - reach, P.max(0) + reach
    return Q[np.all((Q >= lo) & (Q <= hi), axis=1)]


def fade_material(name, rgb, f0, f1, fade=8):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    out = by_type(nt, 'OUTPUT_MATERIAL')
    for nd in list(nt.nodes):
        if nd != out:
            nt.nodes.remove(nd)
    em, clear, mix, val = (nt.nodes.new(k) for k in ('ShaderNodeEmission', 'ShaderNodeBsdfTransparent',
                                                      'ShaderNodeMixShader', 'ShaderNodeValue'))
    em.inputs['Color'].default_value = (*color.lin(rgb), 1)
    nt.links.new(val.outputs[0], mix.inputs[0])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    for f, v in ((f0 - fade, 0.0), (f0, 1.0), (f1 - fade, 1.0), (f1, 0.0)):
        val.outputs[0].default_value = v
        val.outputs[0].keyframe_insert('default_value', frame=f)
    m.surface_render_method = 'BLENDED'
    return m


def diagram(lscene, rep):
    """The locus as a flat map in the label scene: genome line, the five repeat copies, the RT and partner genes,
    their names and a scale bar. Pixels from the top-left (y down), like the rest of the label pass."""
    col = lscene.collection.children[0]
    f0, f1 = T['diagram']
    (x0, x1), y, (span0, span1) = DIAGRAM['x'], DIAGRAM['y'], DIAGRAM['span']

    def px(g):
        return x0 + (g - span0) / (span1 - span0) * (x1 - x0)
    mats = {k: fade_material(f'{LABEL_PREFIX}Map_{k}', rgb, f0, f1) for k, rgb in DIAGRAM_RGB.items()}
    mats['ink'] = fade_material(LABEL_PREFIX + 'Map_ink', INK['dark'], f0, f1)
    count = [0]

    def quad(pts, mat):
        count[0] += 1
        me = bpy.data.meshes.new(f'{LABEL_PREFIX}Map_{count[0]:02d}')
        me.from_pydata([(x, -yy, 0) for x, yy in pts], [], [tuple(range(len(pts)))])
        me.materials.append(mat)
        col.objects.link(bpy.data.objects.new(me.name, me))

    def box(a, b, h, mat):
        quad([(a, y - h / 2), (b, y - h / 2), (b, y + h / 2), (a, y + h / 2)], mat)

    def arrow(a, b, h, mat):
        tip = min(18.0, (b - a) / 3)
        quad([(a, y - h / 2), (b - tip, y - h / 2), (b, y), (b - tip, y + h / 2), (a, y + h / 2)], mat)

    def label(body, x, yy, size, align='CENTER'):
        cu = bpy.data.curves.new(f'{LABEL_PREFIX}Map_T{count[0]}_{len(body)}', 'FONT')
        cu.body, cu.size, cu.align_x, cu.align_y = body, size, align, 'CENTER'
        cu.materials.append(mats['ink'])
        obj = bpy.data.objects.new(cu.name, cu)
        obj.location = (x, -yy, 0)
        col.objects.link(obj)
        count[0] += 1

    box(x0, x1, 2.0, mats['line'])
    for c in rep['copies']:
        box(px(c['start']), px(c['end'] + 1), DIAGRAM['h'][0], mats['repeat'])
    arrow(px(A.RT_CDS[0]), px(A.RT_CDS[1] + 1), DIAGRAM['h'][0] * 0.8, mats['rt'])
    arrow(px(A.PARTNER_CDS[0]), px(A.PARTNER_CDS[1] + 1), DIAGRAM['h'][0] * 0.8, mats['partner'])
    first, last = rep['copies'][0]['start'], rep['copies'][-1]['end']
    label('Repeat array', (px(first) + px(last)) / 2, y - 38, 24)
    label('Reverse transcriptase gene', (px(A.RT_CDS[0]) + px(A.RT_CDS[1])) / 2, y - 38, 24)
    label('Partner gene', (px(A.PARTNER_CDS[0]) + px(A.PARTNER_CDS[1])) / 2, y - 38, 24)
    label(f'{len(rep["copies"])} repeats of {rep["length"]} nt, spacers 122–163 nt', (px(first) + px(last)) / 2, y + 36, 19)
    label('QPI16926 · 501 aa', (px(A.RT_CDS[0]) + px(A.RT_CDS[1])) / 2, y + 36, 19)
    label('QPI16927 · 265 aa', (px(A.PARTNER_CDS[0]) + px(A.PARTNER_CDS[1])) / 2, y + 36, 19)
    sb = DIAGRAM['scale_bp']
    quad([(x1 - (px(span0 + sb) - x0), y + 62), (x1, y + 62), (x1, y + 64), (x1 - (px(span0 + sb) - x0), y + 64)], mats['ink'])
    label(f'{sb} bp', x1, y + 82, 19, align='RIGHT')
    return {'array_px': (round(px(first), 1), round(px(last + 1), 1))}


def footer(lscene):
    col = lscene.collection.children[0]
    f0, f1, body = FOOTER
    cu = bpy.data.curves.new(LABEL_PREFIX + 'Footer', 'FONT')
    cu.body, cu.size, cu.align_x, cu.align_y = body, 16, 'RIGHT', 'BOTTOM_BASELINE'
    cu.materials.append(fade_material(LABEL_PREFIX + 'Footer', INK['dark'], f0, f1))
    obj = bpy.data.objects.new(cu.name, cu)
    obj.location = (RES[0] - 96, -(RES[1] - 30), 0)
    col.objects.link(obj)


# ----------------------------------------------------------------------------- build

def build():
    scene = SC.reset_scene(SCENE_NAME, PREFIX)
    col_dna, col_mol, col_rig = (SC.collection(scene, PREFIX + c) for c in ('DNA', 'Molecules', 'Rig'))
    rng = np.random.default_rng(29)
    lin = color.lin
    report = {}

    # --- the locus and its DNA
    loc_ = A.locus()
    seq, first, rep = loc_['seq'], loc_['first'], loc_['repeats']
    tmpl, step, fit = A.templates(BNA)
    span = A.sub(seq, first, *GENOME)
    helix = A.straight_helix(span, tmpl, step)
    path = A.smooth_path(DNA_WAYPOINTS, spacing=1.0)
    xyz, _ = A.bend(helix['xyz'], path)
    zc = np.array([helix['xyz'][helix['bp'] == k][:, 2].mean() for k in range(len(span))])

    def axis_point(g):
        return A.bend(np.array([[0.0, 0.0, zc[g - GENOME[0]]]]), path)[0][0]
    centre = axis_point(CENTRE_BP)
    xyz -= centre

    def dna_point(g):
        return axis_point(g) - centre
    gpos = helix['bp'] + GENOME[0]
    n_dna = len(xyz)
    backbone = np.isin(helix['name'], list(A.BACKBONE_NA))
    ctx = np.where(backbone[:, None], color.shade(rng, DNA_BACK, n_dna), color.shade(rng, DNA_BASE, n_dna))
    lit_t = np.full(n_dna, 1e6)
    for k, c in enumerate(rep['copies']):
        lit_t[np.isin(gpos, c['lit'])] = LIT[k]
    # The clock (docs/motion.md): x = molecular time in ns, read by the DNA's motion; the numpy processes below
    # sample the same times.
    mrng = np.random.default_rng(43)
    times, rate = D.clock(FRAMES, CLOCK_NS / FPS)
    window = rate * EXPOSURE
    win = float(np.median(window))
    report['clock'] = {'ns_per_film_second': CLOCK_NS, 'shutter': SHUTTER, 'window_frames': EXPOSURE, 'window_ns': round(win, 2)}
    clock = SC.empty(PREFIX + 'Clock', col_rig)
    rig.bake_track(clock, np.stack([times, np.zeros(FRAMES), np.zeros(FRAMES)], 1))
    # DNA motion along the axis: each base pair carries its arc length, axis point and frame (bent like the atoms).
    T_, N_, B_ = A.rmf(path)
    k_ = np.clip(np.rint(zc).astype(int), 0, len(path) - 1)
    axis_bp = A.bend(np.stack([np.zeros_like(zc), np.zeros_like(zc), zc], axis=1), path)[0] - centre
    bp = helix['bp']
    dna = mesh.points_mesh(PREFIX + 'DNA', xyz, None, {
        'vdw': ('FLOAT', St.radii(helix['element'])), 'col_ctx': ('FLOAT_COLOR', ctx),
        'col_hi': ('FLOAT_COLOR', color.shade(rng, AMBER, n_dna, 0.2, 1.0)),
        'lit_t': ('FLOAT', lit_t), 's': ('FLOAT', zc[bp]), 'axis_p': ('FLOAT_VECTOR', axis_bp[bp]),
        'tan': ('FLOAT_VECTOR', T_[k_][bp]), 'nrm': ('FLOAT_VECTOR', N_[k_][bp]), 'bin': ('FLOAT_VECTOR', B_[k_][bp])}, col_dna)
    M = DNA_MOTION
    waves = D.wlc_bend(M['waves'], M['persistence'], TEMP, friction=M['friction'])
    bend = [(rms * D.exposure_factor(tau, win, SHUTTER), max(tau, win), lam) for lam, (rms, tau) in zip(M['waves'], waves)]
    tw_rms, tw_tau = D.wlc_twist(M['twist_length'], M['twist_persistence'], TEMP, friction=M['friction'])
    twist = (tw_rms * D.exposure_factor(tw_tau, win, SHUTTER), max(tw_tau, win), M['twist_length'])
    atom_mat = look.attr_material(PREFIX + 'Atom', roughness=0.42, specular=0.45, sheen=0.15)
    dmod = dna.modifiers.new('DNA', 'NODES')
    dmod.node_group = dna_group(PREFIX, groups.chain_motion(PREFIX, clock, bend, twist))
    set_modifier_inputs(dmod, {'Material': atom_mat})
    report['dna_motion'] = {'bend_rms_A_tau_ns_wave_A': [[round(v, 2) for v in b] for b in bend],
                            'twist_rms_deg_tau_ns': [round(math.degrees(twist[0]), 1), round(twist[1], 2)]}
    report['dna'] = {'bp': len(span), 'atoms': n_dna, 'template_fit': fit,
                     'o3p_gap_A': [round(float(v), 2) for v in np.percentile(A.backbone_gaps(helix), [0, 50, 100])],
                     'bend_strain_A': round(A.neighbour_strain(helix['xyz'], xyz + centre), 3),
                     'lit_nt': int(sum(len(c['lit']) for c in rep['copies'])), 'lit_atoms': int((lit_t < 1e5).sum())}

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
    ghost_mat = ghost_attr_material(PREFIX + 'Ghost')

    # --- the four array RNAs (AF3 model 0 each), below and in front of their units: they tumble and flex
    rna_tracks, rna_world, rna_rep = {}, {}, {}
    for k, key in enumerate(('W1', 'W2', 'W3', 'W4')):
        t = A.model(A.JOBS[key])
        X = t['xyz'] - t['xyz'].mean(0)
        X = X @ A.principal_frame(X).T                      # long axis on X
        (off, (ty, tz)) = RNA_PLACE[key]
        R0 = turn(ty, tz)
        a, b = A.WINDOWS[key]
        base = dna_point((a + b) // 2) + np.array(off, float)
        shift, Rt, motion = tumbling(X, mrng, times, window)
        locs = base + shift
        Rs = R0 @ Rt
        shapes, q, table, mode_attrs, modes_rep = normal_modes(key, X, t, ANM['rna'], 7.5, mrng, times, window, col_rig)
        n = len(X)
        p = t['plddt']
        w = np.clip((p - 30.0) / 40.0, 0, 1)[:, None]
        cols = color.shade(rng, RNA_TEAL, n) * w + np.array(lin(RNA_PALE)) * (1 - w)
        alpha = GHOST_ALPHA['rna'][0] + (GHOST_ALPHA['rna'][1] - GHOST_ALPHA['rna'][0]) * w[:, 0]
        obj = mesh.points_mesh(f'{PREFIX}RNA_{key}', X, None, {
            'radius': ('FLOAT', St.radii(t['element']) * GHOST_SCALE), 'col': ('FLOAT_COLOR', cols), 'alpha': ('FLOAT', alpha),
            'u': ('FLOAT', rng.random(n)), **mode_attrs}, col_mol)
        show = SC.empty(f'{PREFIX}Ctl_Show_{key}', col_rig)
        f0 = T['rna'][k]
        SC.keys(show, 'location', [(1, 0.0), (f0, 0.0), (f0 + 30, 1.0)], 0)
        mod = obj.modifiers.new('Atoms', 'NODES')
        mod.node_group = appear_group(PREFIX, groups.dynamics(PREFIX, table, FRAMES, q.shape[1], name=f'Dynamics_{key}'),
                                      name=f'Appear_{key}')
        set_modifier_inputs(mod, {'Material': ghost_mat, 'Show': show})
        obj.visible_shadow = False
        euler_keys(obj, locs, Rs)
        rna_tracks[key] = locs
        rna_world[key] = (X, locs, Rs, shapes, q)
        rna_rep[key] = {'nt': int(len(np.unique(t['resi']))), 'atoms': n, 'mean_plddt': round(float(p.mean()), 1),
                        'extent_A': [round(float(v)) for v in np.ptp(X, 0)], 'tumbling': motion, 'modes': modes_rep}
    report['rnas'] = rna_rep

    # --- the reverse transcriptase (AF3 model 0): YADD toward -Y, long axis vertical
    t = A.model(A.JOBS['RT'])
    ca = t['name'] == 'CA'
    yadd = (t['resi'] >= A.YADD[0]) & (t['resi'] <= A.YADD[1])
    c0 = t['xyz'].mean(0)
    X = t['xyz'] - c0
    v = X[yadd].mean(0)
    up = A.principal_frame(X)[0]
    fwd = -v / np.linalg.norm(v)                           # YADD direction maps to -Y
    up = up - fwd * (up @ fwd)
    up /= np.linalg.norm(up)
    right = np.cross(fwd, up)
    R = np.stack([right, fwd, up])                          # rows: stage X, Y, Z in model axes
    rt_pos = dna_point(RT_PLACE[1]) + np.array(RT_PLACE[0], float)
    Xrt = X @ R.T + rt_pos
    p = t['plddt']
    n = len(Xrt)
    sure = p >= 70
    ctx = np.zeros((n, 3))
    ctx[p >= 90] = color.shade(rng, RT_SURE[90], int((p >= 90).sum()))
    ctx[(p >= 70) & (p < 90)] = color.shade(rng, RT_SURE[70], int(((p >= 70) & (p < 90)).sum()))
    ctx[~sure] = color.shade(rng, RT_GHOST, int((~sure).sum()))
    side = ~np.isin(t['name'], ['N', 'C', 'O'])
    role = (yadd & side).astype(float)
    hi = ctx.copy()
    for el, ramp_ in ELEMENT.items():
        sel = (role > 0) & (t['element'] == el)
        hi[sel] = color.shade(rng, ramp_, int(sel.sum()), 0.3, 1.0)
    yc = (role > 0) & (t['element'] == 'C')
    hi[yc] = color.shade(rng, AMBER, int(yc.sum()), 0.4, 1.0)
    # The RT's objects tumble about its centroid (keyed transforms); the cutaway reads the camera in their frame.
    c_rt = Xrt.mean(0)
    Xl = Xrt - c_rt
    rt_shift, rt_R, rt_motion = tumbling(Xl, np.random.default_rng(RT_SEED), times, window)
    rt_shapes, rt_q, rt_table, rt_modes, rt_modes_rep = normal_modes('RT', Xl, t, ANM['rt'], 4.3, mrng, times, window, col_rig)
    topo = D.chi_topology(t['resn'], t['resi'], t['name'])
    probe = np.array([next((i for nm in ('CB', 'CA') for i in np.nonzero(topo['slot'] == r)[0] if t['name'][i] == nm))
                      for r in range(topo['residues'])])
    crowd = D.burial(Xl, probe)
    exposed = np.clip((np.percentile(crowd, 90) - crowd) / np.ptp(np.percentile(crowd, [10, 90])), 0, 1)
    chi = D.ou(mrng, times, window, (topo['residues'], 2), np.radians(CHI['sd'][0] + (CHI['sd'][1] - CHI['sd'][0]) * exposed)[:, None],
               (CHI['tau'][0] * (CHI['tau'][1] / CHI['tau'][0]) ** exposed)[:, None], **SHUTTER_ARGS)
    chi_tab = mesh.table(PREFIX + 'Chi_RT', {'chi': np.pad(chi, ((0, 0), (0, 0), (0, 1))).reshape(-1, 3)}, col_rig)
    dyn_rt = groups.dynamics(PREFIX, rt_table, FRAMES, rt_q.shape[1], chi_tab, topo['residues'], name='Dynamics_RT')
    protein_ng = groups.molecule(PREFIX, None, PROTEIN_SCALE, BALL_SCALE, STICK_RADIUS, (176, 200, 232), 0.4,
                                 thermal_group=dyn_rt, space='RELATIVE')
    for name, sel, mat, scale in (('RT', sure, atom_mat, PROTEIN_SCALE), ('RT_Low', ~sure, None, GHOST_SCALE)):
        idx = np.nonzero(sel)[0]
        sub = St.select(t, sel)
        edges = St.bonds(sub, Xl[idx]) if name == 'RT' else None
        if edges is not None:
            keep = (role[idx][edges[:, 0]] > 0) & (role[idx][edges[:, 1]] > 0)
            edges = edges[keep]
        turns = D.chi_topology(sub['resn'], sub['resi'], sub['name'])   # axes found within this object's atoms
        attrs = {'vdw': ('FLOAT', St.radii(sub['element'])), 'role': ('FLOAT', role[idx]), 'ball': ('FLOAT', np.ones(len(idx))),
                 'stick_w': ('FLOAT', np.ones(len(idx))), 'dilate': ('FLOAT_VECTOR', np.zeros((len(idx), 3))),
                 'g0': ('FLOAT', np.zeros(len(idx))), 'g1': ('FLOAT', role[idx]), 'g2': ('FLOAT', np.zeros(len(idx))),
                 'col_ctx': ('FLOAT_COLOR', ctx[idx]), 'col_hi': ('FLOAT_COLOR', hi[idx]),
                 'emit_w': ('FLOAT', role[idx] * 0.9), 'glow_w': ('FLOAT', np.zeros(len(idx))),
                 'col': ('FLOAT_COLOR', ctx[idx]), 'alpha': ('FLOAT', np.full(len(idx), GHOST_ALPHA['rt'])),
                 **{k_: (kind, val[idx]) for k_, (kind, val) in rt_modes.items()},
                 'res_i': ('FLOAT', topo['slot'][idx]), **{k_: ('FLOAT', turns[k_]) for k_ in ('chi1_w', 'chi2_w', 'i_ca', 'i_cb', 'i_cg')}}
        obj = mesh.points_mesh(PREFIX + name, Xl[idx], edges, attrs, col_mol)
        mod = obj.modifiers.new('Atoms', 'NODES')
        mod.node_group = protein_ng
        set_modifier_inputs(mod, {'Material': mat or ghost_mat, 'Camera': cam, 'Target': target, 'Slab': slab,
                                  'Cut': ctl_cut, 'Look': ctl_look, 'Cut Enable': 1.0, 'Path Control': ctl_path,
                                  'Scale': scale, 'Funnel': 8.0})
        if name == 'RT_Low':
            obj.visible_shadow = False
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
    report['rt'] = {'atoms': n, 'residues': int(ca.sum()), 'plddt_ge_70_atoms': round(float(sure.mean()), 3),
                    'yadd_plddt': round(float(p[yadd].mean()), 1), 'yadd_depth_from_centroid_A': round(float(np.linalg.norm(v)), 1),
                    'tumbling': rt_motion, 'modes': rt_modes_rep,
                    'yadd_travel_A': round(float(np.linalg.norm(yadd_track - yadd_pt, axis=1).max()), 1)}

    # --- the partner (AF3 model 0, translucent: mean pLDDT 33), beside the RT but not touching it
    t = A.model(A.JOBS['PARTNER'])
    X = t['xyz'] - t['xyz'].mean(0)
    n = len(X)
    p = t['plddt']
    w = np.clip((p - 25.0) / 45.0, 0, 1)
    p_pos = Xrt.mean(0) + PARTNER_OFFSET
    R0 = turn(20, 140)
    shift, Rt, p_motion = tumbling(X, mrng, times, window)
    Rs = R0 @ Rt
    plocs = p_pos + shift
    p_shapes, p_q, p_table, p_modes, p_modes_rep = normal_modes('Partner', X, t, ANM['partner'], 4.3, mrng, times, window, col_rig)
    pobj = mesh.points_mesh(PREFIX + 'Partner', X, None, {
        'radius': ('FLOAT', St.radii(t['element']) * GHOST_SCALE), 'col': ('FLOAT_COLOR', color.shade(rng, PARTNER, n)),
        'alpha': ('FLOAT', GHOST_ALPHA['partner'][0] + (GHOST_ALPHA['partner'][1] - GHOST_ALPHA['partner'][0]) * w),
        'u': ('FLOAT', rng.random(n)), **p_modes}, col_mol)
    pshow = SC.empty(PREFIX + 'Ctl_Show_Partner', col_rig)
    SC.keys(pshow, 'location', [(1, 0.0), (T['partner'][0], 0.0), (T['partner'][1], 1.0)], 0)
    pmod = pobj.modifiers.new('Atoms', 'NODES')
    pmod.node_group = appear_group(PREFIX, groups.dynamics(PREFIX, p_table, FRAMES, p_q.shape[1], name='Dynamics_Partner'),
                                   name='Appear_Partner')
    set_modifier_inputs(pmod, {'Material': ghost_mat, 'Show': pshow})
    pobj.visible_shadow = False
    euler_keys(pobj, plocs, Rs)
    report['partner'] = {'tumbling': p_motion, 'modes': p_modes_rep}

    # --- clearances (sampled frames, with every molecule's motion; the DNA at rest, its bending stays within
    # report['dna_motion']): the molecules never touch each other or the DNA
    gaps, reach = {}, 120.0                                 # gaps beyond `reach` are reported as `reach`
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

    # --- camera and choreography
    unit_pts = {key: dna_point((a + b) // 2) for key, (a, b) in A.WINDOWS.items()}
    points = {
        'dna_start': dna_point(9548), 'rep1': dna_point((rep['copies'][0]['start'] + rep['copies'][0]['end']) // 2),
        'array': (dna_point(rep['copies'][0]['start']) + dna_point(rep['copies'][-1]['end'])) / 2,
        'w23': (rna_tracks['W2'][0] + rna_tracks['W3'][0] + unit_pts['W2'] + unit_pts['W3']) / 4,
        'w4': (2 * rna_tracks['W4'][0] + unit_pts['W4']) / 3,
        'yadd': yadd_pt, 'pair': (Xrt.mean(0) + p_pos) / 2,
        'tableau': (rna_tracks['W4'][0] + Xrt.mean(0) + p_pos) / 3 + np.array([0.0, 0.0, 50.0]),
    }
    cam_path = TL.camera_path(CAMERA, points, FRAMES)
    a0, a1, b0, b1 = T['follow']
    follow = np.array([TL.ramp(f, a0, a1) * (1 - TL.ramp(f, b0, b1)) for f in range(1, FRAMES + 1)])
    drift = (yadd_track - yadd_pt) * follow[:, None]
    cam_path = [(f, loc + d, aim_pt + d, dist, lens) for (f, loc, aim_pt, dist, lens), d in zip(cam_path, drift)]
    rig.bake_camera(cam, aim, cam_path, APERTURE_RATIO, clip=(1.0, 60000))
    rig.bake_track(target, yadd_track)                      # the cutaway follows YADD as the RT turns
    SC.keys(ctl_cut, 'location', [(1, 0.0), (T['cut'][0], 0.0), (T['cut'][1], 1.0), (T['uncut'][0], 1.0), (T['uncut'][1], 0.0)], 0)
    SC.keys(ctl_look, 'location', [(1, 0.0), (T['yadd'][0], 0.0), (T['yadd'][1], 1.0)], 0)
    SC.keys(ctl_look, 'location', [(1, 0.0), (T['yadd'][0], 0.0), (T['yadd'][0] + 12, 2.2), (T['yadd'][1] + 20, 0.6),
                                   (T['uncut'][1], 0.35)], 1)

    # --- light and world
    world, _, _ = look.gradient_world(PREFIX + 'World', BACKDROP_TOP, BACKDROP_BOTTOM, AMBIENT_RGB, AMBIENT_STRENGTH)
    scene.world = world
    for nm, (d, e, rgb) in (('Key', KEY), ('Rim', RIM), ('Fill', FILL)):
        SC.sun(PREFIX + nm, d, e, 24 if nm == 'Key' else 14, col_rig, rgb)
    SC.cycles_settings(scene, RES, FRAMES, FPS, samples=SAMPLES)
    look.bloom(scene, PREFIX + 'Bloom', **BLOOM)
    scene.frame_set(1)
    SC.save_scene(scene, BLEND_PATH)

    # --- labels (separate scene and file)
    partner_track = plocs
    anchors = {
        'rep1': points['rep1'], 'spacer1': dna_point((rep['copies'][0]['end'] + rep['copies'][1]['start']) // 2),
        **{k: rna_tracks[k] for k in rna_tracks}, **{f'unit_{k}': unit_pts[k] for k in unit_pts},
        'yadd': yadd_track, 'rt_low': low_track, 'rt': c_rt + rt_shift, 'partner': partner_track,
        'rep_first': dna_point(rep['copies'][0]['start']), 'rep_last': dna_point(rep['copies'][-1]['end']),
    }
    spec = dict(LABELS)
    links = []
    for k, key in enumerate(('W1', 'W2', 'W3', 'W4')):
        f0 = T['rna'][k]
        links.append((f0 + 4, f0 + 96, f'unit_{key}', key, {'trim': (12, 70)}))
    spec['links'] = links + [
        (628, 744, 'rt', 'partner', {'dashes': 7, 'trim': (100, 80), 'text': '?', 'size': 36}),
        (644, 744, 'rt', 'W4', {'dashes': 9, 'trim': (100, 150), 'text': '?', 'size': 36}),
        (660, 744, 'partner', 'W4', {'dashes': 15, 'trim': (80, 150), 'text': '?', 'size': 36}),
    ]
    label_result = labels.label_pass(LABEL_SCENE, LABEL_PREFIX, spec, cam_path, anchors, RES, FRAMES, FPS, LABEL_BLEND,
                                     layout={'time_prefix': ''})
    lscene = bpy.data.scenes[LABEL_SCENE]
    map_result = diagram(lscene, rep)
    spec_links = list(spec['links'])
    footer(lscene)
    SC.save_scene(lscene, LABEL_BLEND)
    SC.show(scene)

    return {
        'blender': bpy.app.version_string, 'scene': scene.name, 'frames': FRAMES,
        'locus': {'repeat_window': rep['window'], 'repeat_length': rep['length'], 'consensus': rep['consensus'],
                  'copies': [{k: c[k] for k in ('core', 'start', 'end', 'identity')} for c in rep['copies']],
                  'spacers_nt': loc_['spacers'], 'periods_nt': loc_['periods'], 'tract_AT': loc_['tract_at'],
                  'minus_strand_hits': len(loc_['hits']['-'])},
        **report,
        'confidence': A.confidence_report(),
        'points': {k: [round(float(c), 1) for c in v] for k, v in points.items()},
        'labels': {**label_result, 'links': len(spec_links), **map_result},
        'objects': len(scene.objects), 'blend': str(BLEND_PATH),
    }


RESULT = build()
