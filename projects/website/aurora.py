"""Website stills in the 'aurora' look (October 2026 redesign of amadeusbio.ai): the shots of gallery.py, re-lit.

Same structures, staging, cameras, cuts and measurements as gallery.py (this script calls its shot functions);
only the look changes:
  atoms       a soft 'candy' material (subsurface, clear coat, a rim of their own colour) instead of matte spheres,
              coloured by a smooth gradient across the molecule mixed into each shot's semantic tones
  envelope    an optional translucent, rim-lit surface around the shown atoms (union of their spheres, closed by
              a 3.5 A probe, lifted 1.5 A and smoothed), so the molecule reads as one glassy shape
  backdrop    window-space colour washes and out-of-focus discs drawn by the world shader: they are not objects
              in the scene and stand for nothing in it
  camera      shallower depth of field, stronger bloom, a trace of lens dispersion
Film grain is not baked in: the website lays it over the page (smaller files, one grain for every image).
Amber still marks the one thing that matters in each picture (hemes, hydrogen bonds, ions, glycans, agents).

Headless (from the repo root):
  blender -b --factory-startup --python projects/website/aurora.py -- --shot hemoglobin --still renders/website/aurora/hemoglobin.png
Options: --percent P, --samples N.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import gallery as G  # noqa: E402  (shots, loaders, Stage; also imports molanim and website)

from molanim.color import lin  # noqa: E402
from molanim.blender import look  # noqa: E402
from molanim.blender import scene as SC  # noqa: E402
from molanim.blender.nodes import by_type, new_group, set_modifier_inputs  # noqa: E402

W = G.W

# ----------------------------------------------------------------------------- palette
# gallery.py's tones (sRGB ramps, dark -> light) re-mapped onto an iridescent family: cobalt, cyan, orchid, pearl.
# Each shot keeps its distinctions (alpha vs beta chains, pLDDT bands, strand A vs B); only the hues move.
TONES = {
    'NAVY': ((52, 78, 236), (110, 140, 255)),
    'STEEL': ((40, 170, 236), (120, 214, 255)),
    'SLATE': ((196, 120, 236), (240, 184, 252)),
    'PALE': ((226, 206, 244), (250, 240, 255)),
    'AZURE': ((96, 128, 246), (160, 186, 255)),
    'PORCELAIN': ((222, 218, 250), (255, 250, 255)),
    'CREAM': ((252, 190, 164), (255, 226, 206)),
    'AMBER': ((255, 132, 36), (255, 190, 92)),
}
# The gradient laid across every molecule (sRGB stops at 0, 1/3, 2/3, 1), mixed in at GRADIENT_MIX.
GRADIENT = [(70, 226, 255), (84, 136, 255), (206, 104, 255), (255, 140, 160)]
GRADIENT_MIX = 0.5

# Looks: 'nebula' for the site's dark panels, 'pastel' (lavender-pink) and 'sky' (pale blue) for light image cards. World = base wash, colour blobs
# ((x, y) in window coordinates, radius, sRGB, strength), and bokeh discs (cells across the frame height, share
# of cells lit, strength).
LOOKS = {
    'nebula': {
        'base': ((10, 10, 30), (20, 16, 46)),
        'blobs': [((0.82, 0.78), 0.62, (84, 64, 210), 0.9), ((0.12, 0.18), 0.55, (176, 52, 140), 0.55),
                  ((0.55, 0.42), 0.45, (40, 110, 170), 0.35)],
        'bokeh': [(7.0, 0.22, 0.2), (13.0, 0.18, 0.12)],
        'ambient': ((120, 110, 190), 0.30),
        'key': ((-0.55, -0.8, 0.75), 3.6, (255, 236, 222)),
        'rim': ((0.8, 0.7, 0.35), 7.0, (150, 120, 255)),
        'rim2': ((-0.9, 0.5, -0.1), 4.5, (255, 110, 196)),
        'fill': ((0.1, -1.0, -0.45), 0.6, (120, 200, 255)),
        'atom_rim': 0.55, 'aura': ((150, 140, 255), 2.2), 'section': (210, 196, 255),
        'lipid_head': ((120, 96, 210), (170, 150, 240)), 'lipid_tail': ((70, 60, 150), (110, 96, 190)),
    },
    'pastel': {
        'base': ((178, 186, 255), (255, 196, 232)),
        'blobs': [((0.86, 0.84), 0.62, (140, 206, 255), 0.75), ((0.1, 0.12), 0.6, (255, 162, 214), 0.6),
                  ((0.5, 0.5), 0.5, (214, 196, 255), 0.35)],
        'bokeh': [(6.0, 0.22, 0.32), (11.0, 0.18, 0.2)],
        'ambient': ((236, 230, 255), 0.55),
        'key': ((-0.55, -0.75, 0.9), 3.2, (255, 248, 240)),
        'rim': ((0.7, 0.9, 0.45), 3.4, (190, 210, 255)),
        'rim2': ((-0.9, 0.6, -0.1), 2.4, (255, 176, 220)),
        'fill': ((0.3, -1.0, -0.2), 0.5, (236, 242, 255)),
        'atom_rim': 0.5, 'aura': ((176, 186, 255), 1.5), 'section': (226, 214, 255),
        'lipid_head': ((206, 170, 236), (240, 214, 252)), 'lipid_tail': ((232, 226, 250), (250, 246, 255)),
    },
    'sky': {
        'base': ((168, 204, 255), (214, 200, 255)),
        'blobs': [((0.84, 0.82), 0.62, (150, 232, 255), 0.7), ((0.12, 0.16), 0.58, (226, 190, 255), 0.55),
                  ((0.5, 0.5), 0.5, (222, 236, 255), 0.35)],
        'bokeh': [(6.0, 0.22, 0.3), (11.0, 0.18, 0.2)],
        'ambient': ((226, 236, 255), 0.55),
        'key': ((-0.55, -0.75, 0.9), 3.2, (255, 248, 240)),
        'rim': ((0.7, 0.9, 0.45), 3.4, (176, 226, 255)),
        'rim2': ((-0.9, 0.6, -0.1), 2.4, (236, 176, 255)),
        'fill': ((0.3, -1.0, -0.2), 0.5, (236, 242, 255)),
        'atom_rim': 0.5, 'aura': ((176, 214, 255), 1.5), 'section': (214, 226, 255),
        'lipid_head': ((150, 186, 240), (200, 220, 252)), 'lipid_tail': ((226, 234, 250), (246, 250, 255)),
    },
}
# Shots: look, which molecules (gallery object names) get an envelope, envelope settings, and the depth-of-field
# gain (aperture x gallery.py's per-shot value). Resolutions are gallery.py's.
SHOTS = {
    'hemoglobin': dict(look='pastel', envelope=['Globins']),
    'dna': dict(look='sky', envelope=['Duplex'], env={'Grow': 1.2, 'Probe': 1.2, 'Lift': 0.5, 'Smooth': 3, 'Voxel': 0.5}),
    'p53dna': dict(look='pastel', envelope=['Confident']),
    'gfp': dict(look='nebula', envelope=[], dof=1.6),
    'kcsa': dict(look='nebula', envelope=['Channel']),
    'aquaporin': dict(look='sky', envelope=['Tetramer']),
    'igg': dict(look='sky', envelope=['Antibody']),
    'nucleosome': dict(look='nebula', envelope=[], dof=1.3),
    'agents': dict(look='nebula', envelope=['M0', 'M1', 'M2', 'M3', 'M4', 'M5']),
}


def ramp(t):
    """Linear colours of GRADIENT at t in [0, 1]."""
    stops = np.array([lin(c) for c in GRADIENT])
    x = np.clip(t, 0, 1) * (len(stops) - 1)
    k = np.minimum(x.astype(int), len(stops) - 2)
    u = (x - k)[:, None]
    return stops[k] * (1 - u) + stops[k + 1] * u


# ----------------------------------------------------------------------------- materials

def candy_material(name, rim_strength):
    """Atoms: base colour from 'col', subsurface and clear coat, emission = 'emit' (highlights) plus a Fresnel rim
    in the atom's own, lightened colour."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    p = by_type(nt, 'BSDF_PRINCIPLED')
    for k, v in (('Roughness', 0.32), ('Subsurface Weight', 0.45), ('Subsurface Scale', 0.6), ('Coat Weight', 0.55),
                 ('Coat Roughness', 0.08), ('Specular IOR Level', 0.55), ('Sheen Weight', 0.25), ('Sheen Roughness', 0.3)):
        p.inputs[k].default_value = v
    col = nt.nodes.new('ShaderNodeAttribute')
    col.attribute_type, col.attribute_name = 'GEOMETRY', 'col'
    emit = nt.nodes.new('ShaderNodeAttribute')
    emit.attribute_type, emit.attribute_name = 'GEOMETRY', 'emit'
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.35
    rim = nt.nodes.new('ShaderNodeMapRange')
    rim.inputs['From Min'].default_value, rim.inputs['From Max'].default_value = 0.35, 1.0
    rim.inputs['To Min'].default_value, rim.inputs['To Max'].default_value = 0.0, rim_strength
    total = nt.nodes.new('ShaderNodeMath')
    total.operation = 'ADD'
    light = nt.nodes.new('ShaderNodeMix')
    light.data_type = 'RGBA'
    sock = {s.identifier: s for s in light.inputs}
    sock['Factor_Float'].default_value = 0.45
    sock['B_Color'].default_value = (1.0, 0.95, 1.0, 1)
    L = nt.links
    L.new(col.outputs['Color'], p.inputs['Base Color'])
    L.new(col.outputs['Color'], p.inputs['Subsurface Radius'])
    L.new(col.outputs['Color'], sock['A_Color'])
    L.new(next(s for s in light.outputs if s.identifier == 'Result_Color'), p.inputs['Emission Color'])
    L.new(lw.outputs['Facing'], rim.inputs['Value'])
    L.new(rim.outputs['Result'], total.inputs[0])
    L.new(emit.outputs['Fac'], total.inputs[1])
    L.new(total.outputs[0], p.inputs['Emission Strength'])
    return m


def aura_material(name, rgb, strength, frost=0.1):
    """Envelope: a frosted, tinted glass shell. Mostly clear facing the camera, denser and glowing toward its rim
    (Fresnel), with a faint glossy sheen."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    out = by_type(nt, 'OUTPUT_MATERIAL')
    for nd in list(nt.nodes):
        if nd != out:
            nt.nodes.remove(nd)
    N, L = nt.nodes.new, nt.links.new
    lw = N('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.3
    rim = N('ShaderNodeMapRange')
    rim.interpolation_type = 'SMOOTHSTEP'
    rim.inputs['From Min'].default_value, rim.inputs['From Max'].default_value = 0.15, 0.95
    L(lw.outputs['Facing'], rim.inputs['Value'])
    body = N('ShaderNodeMath')                                   # frost: `frost` facing, up to 3x at the rim
    body.operation = 'MULTIPLY_ADD'
    body.inputs[1].default_value, body.inputs[2].default_value = 2.0 * frost, frost
    L(rim.outputs['Result'], body.inputs[0])
    clear = N('ShaderNodeBsdfTransparent')
    tl, mix = N('ShaderNodeBsdfTranslucent'), N('ShaderNodeMixShader')
    tl.inputs['Color'].default_value = (*lin(rgb), 1)
    L(body.outputs[0], mix.inputs[0])
    L(clear.outputs[0], mix.inputs[1])
    L(tl.outputs[0], mix.inputs[2])
    gloss, gmix = N('ShaderNodeBsdfGlossy'), N('ShaderNodeMixShader')
    gloss.inputs['Roughness'].default_value = 0.1
    sheen = N('ShaderNodeMath')
    sheen.operation = 'MULTIPLY'
    sheen.inputs[1].default_value = 0.35
    L(lw.outputs['Fresnel'], sheen.inputs[0])
    L(sheen.outputs[0], gmix.inputs[0])
    L(mix.outputs[0], gmix.inputs[1])
    L(gloss.outputs[0], gmix.inputs[2])
    em, glow, add = N('ShaderNodeEmission'), N('ShaderNodeMath'), N('ShaderNodeAddShader')
    em.inputs['Color'].default_value = (*lin(rgb), 1)
    glow.operation = 'MULTIPLY'
    glow.inputs[1].default_value = strength
    L(rim.outputs['Result'], glow.inputs[0])
    L(glow.outputs[0], em.inputs['Strength'])
    L(gmix.outputs[0], add.inputs[0])
    L(em.outputs[0], add.inputs[1])
    L(add.outputs[0], out.inputs['Surface'])
    return m


def glass_ghost(name, rgb):
    """Replaces look.ghost_material (p53's low-confidence chain, the predicted DNA): a lit, see-through tint.
    Returns (material, alpha socket) like the original."""
    m = bpy.data.materials.new(name)
    p = by_type(m.node_tree, 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*lin(rgb), 1)
    p.inputs['Emission Color'].default_value = (*lin(rgb), 1)
    p.inputs['Emission Strength'].default_value = 0.9
    p.inputs['Roughness'].default_value = 0.2
    p.inputs['Coat Weight'].default_value = 0.4
    return m, p.inputs['Alpha']


def envelope_group(prefix):
    """Points of the evaluated molecule (radius as drawn) -> union of their van der Waals spheres -> closed by a
    3.5 A probe, lifted 1.5 A -> smoothed -> mesh, joined to the input. Follows every cut, since cut atoms have radius 0."""
    ng, g, gin, gout = new_group(prefix + 'Envelope', [
        ('Material', 'NodeSocketMaterial', None), ('Grow', 'NodeSocketFloat', 1.5), ('Probe', 'NodeSocketFloat', 3.5),
        ('Voxel', 'NodeSocketFloat', 1.0), ('Smooth', 'NodeSocketInt', 14), ('Lift', 'NodeSocketFloat', 1.5)])
    I = gin.outputs
    parts = g.node('GeometryNodeSeparateComponents', {'Geometry': I['Geometry']})
    pts = parts.outputs['Point Cloud']
    radius = g.math('MULTIPLY', g.node('GeometryNodeInputRadius').outputs[0], I['Grow'])
    sdf = g.node('GeometryNodePointsToSDFGrid', {'Points': pts, 'Radius': radius, 'Voxel Size': I['Voxel']}).outputs[0]
    # Dilate by the probe, erode by less (the difference lifts the shell off the atoms), then smooth. Each step
    # stays within the SDF's narrow band; a mesh threshold away from zero would fall outside it.
    sdf = g.node('GeometryNodeSDFGridOffset', {'Grid': sdf, 'Distance': I['Probe']}).outputs[0]
    sdf = g.node('GeometryNodeSDFGridOffset', {'Grid': sdf, 'Distance': g.math('SUBTRACT', I['Lift'], I['Probe'])}).outputs[0]
    sdf = g.node('GeometryNodeSDFGridLaplacian', {'Grid': sdf, 'Iterations': I['Smooth']}).outputs[0]
    shell = g.node('GeometryNodeGridToMesh', {'Grid': sdf, 'Threshold': 0.0, 'Adaptivity': 0.0}).outputs['Mesh']
    shell = g.node('GeometryNodeSetShadeSmooth', {'Geometry': shell}).outputs['Mesh']
    shell = g.material(shell, I['Material'])
    join = g.node('GeometryNodeJoinGeometry')
    g.put(shell, join.inputs[0])
    g.put(I['Geometry'], join.inputs[0])
    g.put(join.outputs[0], gout.inputs['Geometry'])
    return ng


# ----------------------------------------------------------------------------- world

def aurora_world(name, A, res):
    """Camera rays see the wash, blobs and bokeh (window coordinates, aspect-corrected); objects are lit by a
    flat ambient colour, as in gallery.py, so the backdrop never tints the molecules' shading."""
    w = bpy.data.worlds.new(name)
    nt = w.node_tree
    out = by_type(nt, 'OUTPUT_WORLD')
    for n in list(nt.nodes):
        if n != out:
            nt.nodes.remove(n)
    N, L = nt.nodes.new, nt.links.new
    aspect = res[0] / res[1]
    tc = N('ShaderNodeTexCoord')
    win = N('ShaderNodeVectorMath')                          # (x * aspect, y)
    win.operation = 'MULTIPLY'
    win.inputs[1].default_value = (aspect, 1.0, 0.0)
    L(tc.outputs['Window'], win.inputs[0])
    xy = win.outputs[0]

    def color_node(rgb, strength=1.0):
        c = N('ShaderNodeRGB')
        c.outputs[0].default_value = (*[v * strength for v in lin(rgb)], 1)
        return c.outputs[0]

    # base: a diagonal wash between the two base tones
    sep = N('ShaderNodeSeparateXYZ')
    L(tc.outputs['Window'], sep.inputs[0])
    diag = N('ShaderNodeMath')
    diag.operation = 'MULTIPLY_ADD'
    diag.inputs[1].default_value, diag.inputs[2].default_value = 0.5, 0.0
    L(sep.outputs['X'], diag.inputs[0])
    d2 = N('ShaderNodeMath')
    d2.operation = 'MULTIPLY_ADD'
    d2.inputs[1].default_value = 0.5
    L(sep.outputs['Y'], d2.inputs[0])
    L(diag.outputs[0], d2.inputs[2])
    base = N('ShaderNodeMix')
    base.data_type = 'RGBA'
    bs = {s.identifier: s for s in base.inputs}
    L(d2.outputs[0], bs['Factor_Float'])
    L(color_node(A['base'][0]), bs['A_Color'])
    L(color_node(A['base'][1]), bs['B_Color'])
    acc = next(s for s in base.outputs if s.identifier == 'Result_Color')
    glow_mask = None
    for (cx, cy), r, rgb, s in A['blobs']:
        d = N('ShaderNodeVectorMath')
        d.operation = 'DISTANCE'
        d.inputs[1].default_value = (cx * aspect, cy, 0.0)
        L(xy, d.inputs[0])
        f = N('ShaderNodeMapRange')
        f.interpolation_type = 'SMOOTHERSTEP'
        f.inputs['From Min'].default_value, f.inputs['From Max'].default_value = 0.0, r
        f.inputs['To Min'].default_value, f.inputs['To Max'].default_value = 1.0, 0.0
        L(d.outputs['Value'], f.inputs['Value'])
        add = N('ShaderNodeMix')
        add.data_type, add.blend_type = 'RGBA', 'SCREEN'
        sk = {k.identifier: k for k in add.inputs}
        fs = N('ShaderNodeMath')
        fs.operation = 'MULTIPLY'
        fs.inputs[1].default_value = s
        L(f.outputs['Result'], fs.inputs[0])
        L(fs.outputs[0], sk['Factor_Float'])
        L(acc, sk['A_Color'])
        L(color_node(rgb), sk['B_Color'])
        acc = next(k for k in add.outputs if k.identifier == 'Result_Color')
        if glow_mask is None:
            glow_mask = f.outputs['Result']
        else:
            mx = N('ShaderNodeMath')
            mx.operation = 'MAXIMUM'
            L(glow_mask, mx.inputs[0])
            L(f.outputs['Result'], mx.inputs[1])
            glow_mask = mx.outputs[0]
    # bokeh: soft discs on a jittered grid (2D Voronoi), each cell lit at random, brighter inside the blobs
    for k, (cells, share, strength) in enumerate(A['bokeh']):
        vor = N('ShaderNodeTexVoronoi')
        vor.voronoi_dimensions = '2D'
        vor.inputs['Scale'].default_value = cells
        vor.inputs['Randomness'].default_value = 1.0
        off = N('ShaderNodeVectorMath')
        off.operation = 'ADD'
        off.inputs[1].default_value = (17.3 * (k + 1), 5.1 * (k + 1), 0.0)
        L(xy, off.inputs[0])
        L(off.outputs[0], vor.inputs['Vector'])
        disc = N('ShaderNodeMapRange')
        disc.interpolation_type = 'SMOOTHSTEP'
        disc.inputs['From Min'].default_value, disc.inputs['From Max'].default_value = 0.18, 0.24
        disc.inputs['To Min'].default_value, disc.inputs['To Max'].default_value = 1.0, 0.0
        L(vor.outputs['Distance'], disc.inputs['Value'])
        pick = N('ShaderNodeSeparateColor')
        L(vor.outputs['Color'], pick.inputs[0])
        lit = N('ShaderNodeMath')
        lit.operation = 'LESS_THAN'
        lit.inputs[1].default_value = share
        L(pick.outputs['Red'], lit.inputs[0])
        bright = N('ShaderNodeMath')
        bright.operation = 'MULTIPLY_ADD'                     # 0.4 .. 1.0 per disc
        bright.inputs[1].default_value, bright.inputs[2].default_value = 0.6, 0.4
        L(pick.outputs['Green'], bright.inputs[0])
        m1, m2, m3 = (N('ShaderNodeMath') for _ in range(3))
        for m in (m1, m2, m3):
            m.operation = 'MULTIPLY'
        L(disc.outputs['Result'], m1.inputs[0])
        L(lit.outputs[0], m1.inputs[1])
        L(m1.outputs[0], m2.inputs[0])
        L(bright.outputs[0], m2.inputs[1])
        mask = N('ShaderNodeMapRange')
        mask.inputs['To Min'].default_value, mask.inputs['To Max'].default_value = 0.25, 1.0
        L(glow_mask, mask.inputs['Value'])
        L(m2.outputs[0], m3.inputs[0])
        L(mask.outputs['Result'], m3.inputs[1])
        fac = N('ShaderNodeMath')
        fac.operation = 'MULTIPLY'
        fac.inputs[1].default_value = strength
        L(m3.outputs[0], fac.inputs[0])
        add = N('ShaderNodeMix')
        add.data_type, add.blend_type = 'RGBA', 'ADD'
        sk = {s.identifier: s for s in add.inputs}
        L(fac.outputs[0], sk['Factor_Float'])
        L(acc, sk['A_Color'])
        sk['B_Color'].default_value = (1.0, 0.96, 1.0, 1)
        acc = next(s for s in add.outputs if s.identifier == 'Result_Color')
    seen, lit = N('ShaderNodeBackground'), N('ShaderNodeBackground')
    L(acc, seen.inputs['Color'])
    lit.inputs['Color'].default_value = (*lin(A['ambient'][0]), 1)
    lit.inputs['Strength'].default_value = A['ambient'][1]
    path, pick = N('ShaderNodeLightPath'), N('ShaderNodeMixShader')
    L(path.outputs['Is Camera Ray'], pick.inputs[0])
    L(lit.outputs[0], pick.inputs[1])
    L(seen.outputs[0], pick.inputs[2])
    L(pick.outputs[0], out.inputs['Surface'])
    return w


def post(scene, name, dispersion=0.012):
    """Compositor: render -> bloom -> a trace of lens dispersion (colour fringes at high contrast) -> output."""
    ng = look.bloom(scene, name, threshold=0.75, strength=0.7, size=0.75)
    glare = next(n for n in ng.nodes if n.bl_idname == 'CompositorNodeGlare')
    out = next(n for n in ng.nodes if n.bl_idname == 'NodeGroupOutput')
    try:
        lens = ng.nodes.new('CompositorNodeLensdist')
        lens.inputs['Dispersion'].default_value = dispersion
        ng.links.new(glare.outputs['Image'], lens.inputs['Image'])
        ng.links.new(lens.outputs['Image'], out.inputs['Image'])
    except (RuntimeError, KeyError) as e:         # keep the bloom alone if the node's API differs
        print('lens dispersion skipped:', e)
    return ng


# ----------------------------------------------------------------------------- stage

class Aurora(G.Stage):
    def __init__(self, name, look_name, res, envelope=(), env=None, dof=2.2):
        self.A = LOOKS[look_name]
        self.env, self.dof_gain = env or {}, dof
        W.LOOKS[look_name] = {k: self.A[k] for k in ('section', 'lipid_head', 'lipid_tail')}   # read by gallery.py
        super().__init__(name, look_name, res)
        self.mat = candy_material(G.PREFIX + 'Candy', self.A['atom_rim'])
        self.envelope = set(envelope)
        self.objects = {}

    def molecule(self, name, X, t, ctx, hi=None, role=None, emit=None, **kw):
        n = len(X)
        # gradient across the molecule, along the frame's diagonal (stage X right, Z up), never on highlights
        d = np.array([1.0, 0.0, 0.75]) / 1.25
        s = X @ d
        tt = (s - np.percentile(s, 2)) / max(1e-6, np.percentile(s, 98) - np.percentile(s, 2))
        w = np.full(n, GRADIENT_MIX) if emit is None else np.where(np.asarray(emit) > 0, 0.0, GRADIENT_MIX)
        ctx = np.asarray(ctx) * (1 - w[:, None]) + ramp(tt) * w[:, None]
        obj = super().molecule(name, X, t, ctx, hi=hi, role=role, emit=emit, **kw)
        self.objects[name] = obj
        if name in self.envelope:
            if not hasattr(self, '_env'):
                self._env = envelope_group(G.PREFIX)
                self._aura = aura_material(G.PREFIX + 'Aura', *self.A['aura'])
            m = obj.modifiers.new('Envelope', 'NODES')
            m.node_group = self._env
            set_modifier_inputs(m, {'Material': self._aura, **self.env})
        return obj

    def camera(self, aim, dist, az, el, lens=50, dof=0.01):
        super().camera(aim, dist, az, el, lens=lens, dof=dof * self.dof_gain)

    def finish(self, samples):
        A = self.A
        self.scene.world = aurora_world(G.PREFIX + 'World', A, self.res)
        dist = float(np.linalg.norm(self.cam.location - self.aim.location)) if self.direction is not None else 300
        for key in ('key', 'rim', 'rim2', 'fill'):
            d, e, rgb = A[key]
            SC.sun(G.PREFIX + key.title(), d, e, 30 if key == 'key' else 16, self.rigc, rgb, distance=3 * dist)
        SC.cycles_settings(self.scene, self.res, 1, 24, samples=samples, bounces=(8, 3, 4), transparent=24)
        post(self.scene, G.PREFIX + 'Post')
        self.scene.frame_set(1)
        return self.scene


def configure():
    """Point gallery.py's tones and ghost material at the aurora palette (looked up when each shot runs)."""
    for k, v in TONES.items():
        setattr(G, k, v)
    G.look.ghost_material = glass_ghost
    rim = {}
    G.look.attr_material = lambda name, **kw: candy_material(name, rim.get('atom', 0.4))   # lipids, Stage default
    return rim


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', required=True, choices=sorted(SHOTS))
    ap.add_argument('--still', required=True)
    ap.add_argument('--percent', type=int, default=100)
    ap.add_argument('--samples', type=int, default=384)
    args = ap.parse_args(argv)
    W.gpu()
    rim = configure()
    _, res, fn = G.SHOTS[args.shot]
    cfg = SHOTS[args.shot]
    look_name = cfg['look']
    rim['atom'] = LOOKS[look_name]['atom_rim']
    S = Aurora(args.shot, look_name, res, cfg['envelope'], cfg.get('env'), cfg.get('dof', 2.2))
    report = {'shot': args.shot, 'look': look_name, 'envelope': sorted(cfg['envelope']),
              'envelope_settings': cfg.get('env', {}), 'dof_gain': cfg.get('dof', 2.2), **fn(S)}
    scene = S.finish(args.samples)
    scene.render.resolution_percentage = args.percent
    out = Path(args.still).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out)
    with bpy.context.temp_override(scene=scene):
        bpy.ops.render.render(write_still=True, scene=scene.name)
    report['still'] = str(out)
    print('RESULT ' + json.dumps(report))
