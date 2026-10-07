"""Geometry-node groups for molecular shots (Blender 5.x).

Animated controllers are empties whose location channels (x, y, z) drive reveals, cuts and glows, so a
shot's choreography is plain keyframes on a few empties. Group names are `prefix + name`.
"""
import math

from ..color import lin
from .nodes import new_group


def breath(prefix, sway=0.35, sway_size=30.0, jitter=0.12, jitter_size=5.0, loop_frames=None, drift=0.35,
           name='Breath'):
    """Offset: slow, spatially coherent sway plus fine thermal jitter (A; sizes are noise scales in A).

    Without `loop_frames` the motion is aperiodic 4D noise over time. With `loop_frames` it samples 3D noise
    at position + a circle in noise space, so frame loop_frames + 1 equals frame 1 (seamless loops)."""
    ng, g, gin, gout = new_group(prefix + name, [('Sway', 'NodeSocketFloat', sway), ('Sway Size', 'NodeSocketFloat', sway_size),
                                                 ('Jitter', 'NodeSocketFloat', jitter), ('Jitter Size', 'NodeSocketFloat', jitter_size)])
    I = gin.outputs
    pos = g.node('GeometryNodeInputPosition').outputs['Position']
    offset = None
    if loop_frames is None:
        secs = g.node('GeometryNodeInputSceneTime').outputs['Seconds']
        for amp, size, rate, seed in (('Sway', 'Sway Size', 0.22, 3.1), ('Jitter', 'Jitter Size', 0.9, 17.3)):
            noise = g.node('ShaderNodeTexNoise', {'Vector': pos, 'W': g.math('ADD', g.math('MULTIPLY', secs, rate), seed),
                                                  'Scale': g.math('DIVIDE', 1.0, I[size]), 'Detail': 1.0}, noise_dimensions='4D')
            term = g.vec('SCALE', g.vec('SUBTRACT', noise.outputs['Color'], (0.5, 0.5, 0.5)), scale=g.math('MULTIPLY', I[amp], 2.0))
            offset = term if offset is None else g.vec('ADD', offset, term)
    else:
        frame = g.node('GeometryNodeInputSceneTime').outputs['Frame']
        phase = g.math('MULTIPLY', g.math('DIVIDE', g.math('SUBTRACT', frame, 1.0), float(loop_frames)), 2 * math.pi)
        cos_t, sin_t = g.math('COSINE', phase), g.math('SINE', phase)
        for amp, size, seed in (('Sway', 'Sway Size', 11.3), ('Jitter', 'Jitter Size', 47.9)):
            r = g.math('MULTIPLY', I[size], drift)
            circle = g.node('ShaderNodeCombineXYZ', {'X': g.math('MULTIPLY', cos_t, r), 'Y': g.math('MULTIPLY', sin_t, r)}).outputs[0]
            sample = g.vec('ADD', g.vec('ADD', pos, circle), g.vec('SCALE', (seed, seed * 0.61, seed * 0.37), scale=I[size]))
            noise = g.node('ShaderNodeTexNoise', {'Vector': sample, 'Scale': g.math('DIVIDE', 1.0, I[size]), 'Detail': 1.0},
                           noise_dimensions='3D')
            term = g.vec('SCALE', g.vec('SUBTRACT', noise.outputs['Color'], (0.5, 0.5, 0.5)), scale=g.math('MULTIPLY', I[amp], 2.0))
            offset = term if offset is None else g.vec('ADD', offset, term)
    setpos = g.node('GeometryNodeSetPosition', {'Geometry': I['Geometry'], 'Offset': offset})
    g.put(setpos.outputs['Geometry'], gout.inputs['Geometry'])
    return ng


def molecule(prefix, breath_group, scale=0.64, ball=0.28, stick=0.16, section_rgb=(176, 220, 212), section_mix=0.45,
             name='Protein'):
    """Atoms -> spheres (context) and ball-and-stick (roles), with a camera-aimed cutaway funnel and a section slab.

    Mesh: atom vertices plus bond edges. Per-atom attributes:
      vdw (A), role (0 context, >0 shown as ball-and-stick when revealed), g0/g1/g2 (reveal-group weights:
      g0 always, g1 by Look.x, g2 by Cut.z), ball (ball scale multiplier), stick_w (stick multiplier),
      dilate (vector, scaled by Path Control.y), col_ctx and col_hi (colours before/after reveal),
      emit_w and glow_w (emission weights driven by Look.y and Look.z).
    Controllers (empties, by location): Cut = (funnel open, slab open, group-2 reveal),
      Look = (group-1 reveal, glow 1, glow 2), Path Control = (-, dilation, -).
    The funnel removes atoms near the camera-target line in front of Target; the slab removes atoms in front
    of a vertical plane through Slab facing the camera. Atoms on cut surfaces turn toward `section_rgb`."""
    ng, g, gin, gout = new_group(prefix + name, [
        ('Material', 'NodeSocketMaterial', None), ('Camera', 'NodeSocketObject', None), ('Target', 'NodeSocketObject', None),
        ('Slab', 'NodeSocketObject', None), ('Cut', 'NodeSocketObject', None), ('Look', 'NodeSocketObject', None),
        ('Scale', 'NodeSocketFloat', scale), ('Ball', 'NodeSocketFloat', ball), ('Stick', 'NodeSocketFloat', stick),
        ('Cut Enable', 'NodeSocketFloat', 1.0), ('Funnel', 'NodeSocketFloat', 9.0), ('Slope', 'NodeSocketFloat', 0.5),
        ('Back', 'NodeSocketFloat', 6.0), ('Slab Reach', 'NodeSocketFloat', 45.0),
        ('Path Control', 'NodeSocketObject', None)])
    I = gin.outputs
    geo = g.node('GeometryNodeGroup', {'Geometry': I['Geometry']}, node_tree=breath_group).outputs['Geometry']
    pos = g.node('GeometryNodeInputPosition').outputs['Position']
    # Optional rigid offsets per residue (e.g. an illustrative open state), scaled by Path Control.y.
    _, opened, _ = g.xyz(g.loc(I['Path Control']))
    geo = g.node('GeometryNodeSetPosition', {'Geometry': geo, 'Offset': g.vec('SCALE', g.attr('dilate', 'FLOAT_VECTOR'),
                                                                             scale=opened)}).outputs['Geometry']
    cam, tgt, slab = g.loc(I['Camera']), g.loc(I['Target']), g.loc(I['Slab'])
    cut, slab_amt, gates = g.xyz(g.loc(I['Cut']))
    pocket, ret_glow, bond_glow = g.xyz(g.loc(I['Look']))

    # Funnel: atoms near the camera-target line, in front of the target, shrink away.
    a = g.vec('NORMALIZE', g.vec('SUBTRACT', cam, tgt))
    v = g.vec('SUBTRACT', pos, tgt)
    along = g.vec('DOT_PRODUCT', v, a)
    perp = g.vec('LENGTH', g.vec('SUBTRACT', v, g.vec('SCALE', a, scale=along)))
    radius = g.math('MULTIPLY', g.math('ADD', I['Funnel'], g.math('MULTIPLY', I['Slope'], g.math('MAXIMUM', along, 0.0))), cut)
    # Atoms shrink across a band that is wide while a cut moves and narrow (0.3 A) at rest, so finished cuts
    # leave no half-size atoms floating at their surface.
    band_f = g.math('ADD', 0.3, g.math('MULTIPLY', 1.2, g.math('SUBTRACT', 1.0, cut)))
    inside = g.smooth(perp, g.math('SUBTRACT', radius, band_f), g.math('ADD', radius, band_f), 1.0, 0.0)
    front = g.smooth(along, g.math('SUBTRACT', 0.0, g.math('ADD', I['Back'], 1.5)), g.math('SUBTRACT', 1.5, I['Back']))
    rm_funnel = g.math('MULTIPLY', inside, front)
    # Section slab: a vertical plane through the slab empty, facing the camera, sweeps in from the front.
    n = g.vec('NORMALIZE', g.vec('MULTIPLY', g.vec('SUBTRACT', cam, slab), (1.0, 1.0, 0.0)))
    depth = g.vec('DOT_PRODUCT', g.vec('SUBTRACT', pos, slab), n)
    offset = g.math('MULTIPLY', g.math('SUBTRACT', 1.0, slab_amt), I['Slab Reach'])
    band_s = g.math('ADD', 0.3, g.math('MULTIPLY', 1.2, g.math('SUBTRACT', 1.0, slab_amt)))
    rm_slab = g.math('MULTIPLY', g.smooth(depth, g.math('SUBTRACT', offset, band_s), g.math('ADD', offset, band_s)),
                     g.math('GREATER_THAN', slab_amt, 0.001))
    remove = g.math('MULTIPLY', g.math('MAXIMUM', rm_funnel, rm_slab), I['Cut Enable'])

    role = g.attr('role')
    is_role = g.math('GREATER_THAN', role, 0.5)
    reveal = g.math('MINIMUM', 1.0, g.math('ADD', g.attr('g0'), g.math('ADD', g.math('MULTIPLY', g.attr('g1'), pocket),
                                                                          g.math('MULTIPLY', g.attr('g2'), gates))))
    reveal = g.math('MULTIPLY', reveal, is_role)
    vdw = g.attr('vdw')
    r_ctx = g.math('MULTIPLY', g.math('MULTIPLY', vdw, I['Scale']), g.math('SUBTRACT', 1.0, remove))
    ball_r = g.math('MULTIPLY', I['Ball'], g.attr('ball'))
    r_role = g.math('MULTIPLY', vdw, g.math('ADD', I['Scale'], g.math('MULTIPLY', reveal, g.math('SUBTRACT', ball_r, I['Scale']))))
    r = g.node('GeometryNodeSwitch', {'Switch': is_role, 'False': r_ctx, 'True': r_role}, input_type='FLOAT').outputs['Output']
    col = g.mix_color(reveal, g.attr('col_ctx', 'FLOAT_COLOR'), g.attr('col_hi', 'FLOAT_COLOR'))
    # Cut surfaces read as sections: context atoms just behind the slab plane or the funnel wall turn paler.
    band_slab = g.math('MULTIPLY', g.smooth(depth, g.math('SUBTRACT', offset, 4.5), g.math('SUBTRACT', offset, 1.0)),
                       g.math('GREATER_THAN', slab_amt, 0.001))
    band_funnel = g.math('MULTIPLY', g.math('MULTIPLY', g.smooth(perp, g.math('ADD', radius, 4.0), g.math('ADD', radius, 1.2)), front),
                         g.math('GREATER_THAN', cut, 0.001))
    band = g.math('MULTIPLY', g.math('MULTIPLY', g.math('MAXIMUM', band_slab, band_funnel), g.math('SUBTRACT', 1.0, is_role)),
                  g.math('MULTIPLY', I['Cut Enable'], section_mix))
    col = g.mix_color(band, col, (*lin(section_rgb), 1.0))
    emit = g.math('ADD', g.math('MULTIPLY', g.attr('emit_w'), ret_glow), g.math('MULTIPLY', g.attr('glow_w'), bond_glow))

    geo = g.store(geo, 'radius', r)
    geo = g.store(geo, 'reveal', reveal)
    geo = g.store(geo, 'col', col, 'FLOAT_COLOR')
    geo = g.store(geo, 'emit', emit)
    points = g.node('GeometryNodeMeshToPoints', {'Mesh': geo, 'Selection': g.math('GREATER_THAN', g.attr('radius'), 0.04),
                                                 'Radius': g.attr('radius')}, mode='VERTICES').outputs['Points']
    # Sticks: bonds whose two atoms are both revealed.
    both = g.node('GeometryNodeFieldOnDomain', {'Value': g.attr('reveal')}, domain='EDGE', data_type='FLOAT').outputs[0]
    shown = g.node('GeometryNodeFieldOnDomain', {'Value': g.math('GREATER_THAN', g.attr('reveal'), 0.01)}, domain='EDGE',
                   data_type='FLOAT').outputs[0]
    curve = g.node('GeometryNodeMeshToCurve', {'Mesh': geo, 'Selection': g.math('GREATER_THAN', g.math('MINIMUM', both, shown), 0.99)},
                   mode='EDGES').outputs['Curve']
    profile = g.node('GeometryNodeCurvePrimitiveCircle', {'Resolution': 10, 'Radius': 1.0}, mode='RADIUS').outputs['Curve']
    sticks = g.node('GeometryNodeCurveToMesh', {'Curve': curve, 'Profile Curve': profile,
                                               'Scale': g.math('MULTIPLY', g.math('MULTIPLY', g.attr('reveal'), g.attr('stick_w')),
                                                               I['Stick'])}).outputs['Mesh']
    sticks = g.node('GeometryNodeSetShadeSmooth', {'Geometry': sticks}).outputs['Mesh']
    join = g.node('GeometryNodeJoinGeometry')
    g.put(sticks, join.inputs[0])
    g.put(points, join.inputs[0])
    g.put(g.material(join.outputs[0], I['Material']), gout.inputs['Geometry'])
    return ng


def spheres(prefix, breath_group=None, sway=0.6, jitter=0.18, name='Lipids'):
    """Atoms -> spheres from the 'radius' attribute, optionally breathing (with the group's Sway/Jitter overridden)."""
    ng, g, gin, gout = new_group(prefix + name, [('Material', 'NodeSocketMaterial', None)])
    I = gin.outputs
    geo = I['Geometry']
    if breath_group is not None:
        geo = g.node('GeometryNodeGroup', {'Geometry': geo, 'Sway': sway, 'Jitter': jitter}, node_tree=breath_group).outputs['Geometry']
    pts = g.node('GeometryNodeMeshToPoints', {'Mesh': geo, 'Radius': g.attr('radius')}, mode='VERTICES').outputs['Points']
    g.put(g.material(pts, I['Material']), gout.inputs['Geometry'])
    return ng


def frame_spheres(prefix, name='Ions'):
    """Frame-indexed tracks (mesh.frame_tracks) -> spheres ('radius' attribute) for the current frame."""
    ng, g, gin, gout = new_group(prefix + name, [('Material', 'NodeSocketMaterial', None)])
    I = gin.outputs
    geo = g.this_frame(I['Geometry'])
    pts = g.node('GeometryNodeMeshToPoints', {'Mesh': geo, 'Radius': g.attr('radius')}, mode='VERTICES').outputs['Points']
    g.put(g.material(pts, I['Material']), gout.inputs['Geometry'])
    return ng


def wave_packets(prefix, cycles=5.0, amplitude=0.075, name='Photons'):
    """Frame-indexed heads -> wave packets (a sine squiggle under a smooth envelope) trailing behind each head
    along its 'dir' attribute; 'size' is the packet length, 'thick' the line radius. A symbol for light."""
    ng, g, gin, gout = new_group(prefix + name, [('Material', 'NodeSocketMaterial', None), ('Cycles', 'NodeSocketFloat', cycles),
                                                 ('Amplitude', 'NodeSocketFloat', amplitude)])
    I = gin.outputs
    heads = g.this_frame(I['Geometry'])
    line = g.node('GeometryNodeCurvePrimitiveLine', {'Start': (0, 0, -1), 'End': (0, 0, 0)}, mode='POINTS').outputs['Curve']
    line = g.node('GeometryNodeResampleCurve', {'Curve': line, 'Count': 160}).outputs['Curve']
    u = g.node('GeometryNodeSplineParameter').outputs['Factor']
    env = g.math('POWER', g.math('SINE', g.math('MULTIPLY', u, math.pi)), 2.0)
    wave = g.math('SINE', g.math('MULTIPLY', u, g.math('MULTIPLY', I['Cycles'], 2 * math.pi)))
    off = g.node('ShaderNodeCombineXYZ', {'X': g.math('MULTIPLY', g.math('MULTIPLY', env, wave), I['Amplitude'])}).outputs[0]
    squiggle = g.node('GeometryNodeSetPosition', {'Geometry': line, 'Offset': off}).outputs['Geometry']
    rot = g.node('FunctionNodeAlignRotationToVector', {'Vector': g.attr('dir', 'FLOAT_VECTOR')}, axis='Z').outputs['Rotation']
    size = g.attr('size')
    inst = g.node('GeometryNodeInstanceOnPoints', {'Points': heads, 'Instance': squiggle, 'Rotation': rot,
                                                  'Scale': g.node('ShaderNodeCombineXYZ', {'X': size, 'Y': size, 'Z': size}).outputs[0]})
    real = g.node('GeometryNodeRealizeInstances', {'Geometry': inst.outputs['Instances']}).outputs['Geometry']
    taper = g.math('MULTIPLY', g.attr('thick'), g.math('POWER', g.math('SINE', g.math('MULTIPLY', g.node('GeometryNodeSplineParameter').outputs['Factor'], math.pi)), 0.5))
    profile = g.node('GeometryNodeCurvePrimitiveCircle', {'Resolution': 8, 'Radius': 1.0}, mode='RADIUS').outputs['Curve']
    tube_mesh = g.node('GeometryNodeCurveToMesh', {'Curve': real, 'Profile Curve': profile, 'Scale': taper}).outputs['Mesh']
    tube_mesh = g.node('GeometryNodeSetShadeSmooth', {'Geometry': tube_mesh}).outputs['Mesh']
    g.put(g.material(tube_mesh, I['Material']), gout.inputs['Geometry'])
    return ng


def tube(prefix, margin=0.5, cap=3.2, name='Cavity'):
    """Polyline (vertices + edges) -> a tube whose radius blends from attribute 'r0' to 'r1' with Control.y,
    pinched shut where the radius is below ~1.2 A, shown by Control.x, tapered by 'taper'. Displayed radius =
    min(r + margin, Cap). For a pathway: r0 = measured free radius, r1 = an illustrative open radius."""
    ng, g, gin, gout = new_group(prefix + name, [('Material', 'NodeSocketMaterial', None), ('Control', 'NodeSocketObject', None),
                                                 ('Cap', 'NodeSocketFloat', cap)])
    I = gin.outputs
    show, opened, _ = g.xyz(g.loc(I['Control']))
    r = g.math('ADD', g.attr('r0'), g.math('MULTIPLY', opened, g.math('SUBTRACT', g.attr('r1'), g.attr('r0'))))
    shut = g.smooth(r, 0.8, 1.2)
    disp = g.math('MINIMUM', g.math('ADD', r, margin), I['Cap'])
    disp = g.math('MULTIPLY', g.math('MULTIPLY', disp, shut), g.math('MULTIPLY', show, g.attr('taper')))
    geo = g.store(I['Geometry'], 'disp', disp)
    curve = g.node('GeometryNodeMeshToCurve', {'Mesh': geo}, mode='EDGES').outputs['Curve']
    profile = g.node('GeometryNodeCurvePrimitiveCircle', {'Resolution': 28, 'Radius': 1.0}, mode='RADIUS').outputs['Curve']
    tube_mesh = g.node('GeometryNodeCurveToMesh', {'Curve': curve, 'Profile Curve': profile, 'Scale': g.attr('disp')}).outputs['Mesh']
    tube_mesh = g.node('GeometryNodeSetShadeSmooth', {'Geometry': tube_mesh}).outputs['Mesh']
    g.put(g.material(tube_mesh, I['Material']), gout.inputs['Geometry'])
    return ng


def dotted_link(prefix, breath_group, dots=7, bead=0.17, name='Bridge'):
    """Two vertices -> a dotted line of small beads (an interaction marker: salt bridge, H-bond), sized by
    the Show empty's x. Breathes with the atoms it joins."""
    ng, g, gin, gout = new_group(prefix + name, [('Material', 'NodeSocketMaterial', None), ('Show', 'NodeSocketObject', None),
                                                 ('Dots', 'NodeSocketInt', dots), ('Bead', 'NodeSocketFloat', bead)])
    I = gin.outputs
    geo = g.node('GeometryNodeGroup', {'Geometry': I['Geometry']}, node_tree=breath_group).outputs['Geometry']
    pos = g.node('GeometryNodeInputPosition').outputs['Position']

    def at(i):
        return g.node('GeometryNodeSampleIndex', {'Geometry': geo, 'Value': pos, 'Index': i}, data_type='FLOAT_VECTOR',
                      domain='POINT').outputs[0]
    show, _, _ = g.xyz(g.loc(I['Show']))
    line = g.node('GeometryNodeMeshLine', {'Count': I['Dots'], 'Start Location': at(0), 'Offset': at(1)}, mode='END_POINTS',
                  count_mode='TOTAL').outputs['Mesh']
    pts = g.node('GeometryNodeMeshToPoints', {'Mesh': line, 'Radius': g.math('MULTIPLY', I['Bead'], show),
                                              'Selection': g.math('GREATER_THAN', show, 0.01)}, mode='VERTICES').outputs['Points']
    g.put(g.material(pts, I['Material']), gout.inputs['Geometry'])
    return ng
