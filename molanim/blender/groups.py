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


# RMS per axis of (Noise Texture colour - 0.5) for 4D Perlin noise at Detail 1, measured over 40,000 samples in
# Blender 5.2. thermal() divides by it, so its amplitudes are RMS displacements per axis in A.
NOISE_RMS = 0.0912


def thermal(prefix, coherent=(6.0, 1.5), fine=(1.6, 3.0), loop_frames=None, fps=24, name='Thermal'):
    """Illustrative thermal motion (not a simulation): two 4D noise fields in position and time. The coherent
    field (size coherent[0] A, coherent[1] cycles per second) moves neighbouring atoms together, with an RMS per
    axis equal to each vertex's 'thermal' attribute (A). The fine field moves atoms more independently, with RMS
    'thermal_fine'. Vertices without these attributes stay put.

    With `loop_frames` the noise is sampled on a circle in (x, w) noise space, at the same speed, so frame
    loop_frames + 1 equals frame 1 (seamless loops).

    molecule(), spheres() and dotted_link() apply it as `thermal_group` after cuts and reveals are evaluated, so
    atoms jittering across a cut surface do not flicker."""
    ng, g, gin, gout = new_group(prefix + name, [('Gain', 'NodeSocketFloat', 1.0)])
    I = gin.outputs
    pos = g.node('GeometryNodeInputPosition').outputs['Position']
    time = g.node('GeometryNodeInputSceneTime')
    if loop_frames:
        phase = g.math('MULTIPLY', g.math('DIVIDE', g.math('SUBTRACT', time.outputs['Frame'], 1.0), float(loop_frames)), 2 * math.pi)
        cos_t, sin_t = g.math('COSINE', phase), g.math('SINE', phase)
    offset = None
    for (size, rate), seed, amp in ((coherent, 5.7, 'thermal'), (fine, 29.3, 'thermal_fine')):
        # The texture's Scale also scales W, so W (and the loop circle) are in A: `rate` cycles per second is a
        # speed of rate x size A per second in noise space.
        if loop_frames:
            radius = rate * size * (loop_frames / fps) / (2 * math.pi)
            vec = g.vec('ADD', pos, g.node('ShaderNodeCombineXYZ', {'X': g.math('MULTIPLY', sin_t, radius)}).outputs[0])
            w = g.math('ADD', g.math('MULTIPLY', cos_t, radius), seed * size)
        else:
            vec, w = pos, g.math('ADD', g.math('MULTIPLY', time.outputs['Seconds'], rate * size), seed)
        noise = g.node('ShaderNodeTexNoise', {'Vector': vec, 'W': w, 'Scale': 1.0 / size, 'Detail': 1.0},
                       noise_dimensions='4D')
        term = g.vec('SCALE', g.vec('SUBTRACT', noise.outputs['Color'], (0.5, 0.5, 0.5)),
                     scale=g.math('MULTIPLY', g.attr(amp), 1.0 / NOISE_RMS))
        offset = term if offset is None else g.vec('ADD', offset, term)
    offset = g.vec('SCALE', offset, scale=I['Gain'])
    setpos = g.node('GeometryNodeSetPosition', {'Geometry': I['Geometry'], 'Offset': offset})
    g.put(setpos.outputs['Geometry'], gout.inputs['Geometry'])
    return ng


# Detail-0 4D noise (the motion groups below): RMS per axis of (colour - 0.5), and the lag (noise units, along W
# or in space) at which its autocorrelation falls to 1/e. Measured in Blender 5.2 over 64,000 samples. A process
# with correlation time tau (ns) therefore advances W by NOISE0_CORR / tau per ns of the clock.
NOISE0_RMS, NOISE0_CORR = 0.1223, 0.58


def _unit_noise(g, vec, w):
    """Smooth random 3-vector field with unit RMS per axis (detail-0 4D noise)."""
    n = g.node('ShaderNodeTexNoise', {'Vector': vec, 'W': w, 'Scale': 1.0, 'Detail': 0.0}, noise_dimensions='4D')
    return g.vec('SCALE', g.vec('SUBTRACT', n.outputs['Color'], (0.5, 0.5, 0.5)), scale=1.0 / NOISE0_RMS)


def _clock_w(g, clock, tau):
    """Noise W for a process of correlation time tau (ns) on the clock (an empty whose x is molecular time, ns)."""
    t, _, _ = g.xyz(g.loc(clock))
    return g.math('MULTIPLY', t, NOISE0_CORR / tau)


def lipid_motion(prefix, clock, motion, name='LipidMotion'):
    """Thermal motion of lipids as molecules (illustrative, from measured rates; docs/motion.md). Every atom
    of a lipid samples the same random processes (seeded by the per-lipid vector 'mol_seed'), so the lipid keeps
    its shape:
      head    the choline turns about the phosphate ('pivot_h'), atoms weighted by 'head_w';
      tail    each chain bends about its ester carbon ('pivot_t'), more toward its end ('tail_w'), chains
              told apart by 'tail_k' (0, 1);
      turn    the whole lipid turns about its glycerol ('pivot'): axial rotation about the membrane normal and
              a small wobble of the long axis;
      move    lateral displacement = a spatially correlated flow (sampled at the pivot, so neighbours move
              together, as in concerted lipid diffusion) + the lipid's own rattle, and vertical bobbing.
    'mobility' (0-1) scales all of it (annular lipids against a protein move less). `motion` = {process:
    (RMS, tau ns)} for head, tail, axial, wobble (rad), rattle, bob (A), and flow: (RMS A, tau ns, length A)."""
    ng, g, gin, gout = new_group(prefix + name, [('Gain', 'NodeSocketFloat', 1.0)])
    I = gin.outputs
    p = g.node('GeometryNodeInputPosition').outputs['Position']
    seed = g.attr('mol_seed', 'FLOAT_VECTOR')
    mob = g.math('MULTIPLY', g.attr('mobility'), I['Gain'])

    def proc(key, k, offset=None):
        rms, tau = motion[key][:2]
        s = g.vec('ADD', seed, (k * 53.7, k * 29.3, k * 71.9))
        if offset is not None:
            s = g.vec('ADD', s, offset)
        return g.vec('SCALE', _unit_noise(g, s, _clock_w(g, clock, tau)), scale=rms)
    flat = (1.0, 1.0, 0.0)
    rv = g.vec('SCALE', proc('head', 1), scale=g.math('MULTIPLY', g.attr('head_w'), mob))
    p = g.rotate_about(p, g.attr('pivot_h', 'FLOAT_VECTOR'), rv)
    chain = g.vec('SCALE', (17.1, 5.3, 9.9), scale=g.attr('tail_k'))
    rv = g.vec('SCALE', g.vec('MULTIPLY', proc('tail', 2, chain), flat), scale=g.math('MULTIPLY', g.attr('tail_w'), mob))
    p = g.rotate_about(p, g.attr('pivot_t', 'FLOAT_VECTOR'), rv)
    rv = g.vec('ADD', g.vec('MULTIPLY', proc('wobble', 3), flat), g.vec('MULTIPLY', proc('axial', 4), (0.0, 0.0, 1.0)))
    pivot = g.attr('pivot', 'FLOAT_VECTOR')
    p = g.rotate_about(p, pivot, g.vec('SCALE', rv, scale=mob))
    rms, tau, length = motion['flow']
    where = g.vec('ADD', g.vec('SCALE', g.vec('MULTIPLY', pivot, flat), scale=NOISE0_CORR / length),
                  g.vec('SCALE', (0.0, 0.0, 7.3), scale=g.attr('leaflet')))
    flow = g.vec('SCALE', g.vec('MULTIPLY', _unit_noise(g, where, _clock_w(g, clock, tau)), flat), scale=rms)
    move = g.vec('ADD', g.vec('ADD', flow, g.vec('MULTIPLY', proc('rattle', 5), flat)),
                 g.vec('MULTIPLY', proc('bob', 6), (0.0, 0.0, 1.0)))
    p = g.vec('ADD', p, g.vec('SCALE', move, scale=mob))
    setpos = g.node('GeometryNodeSetPosition', {'Geometry': I['Geometry'], 'Position': p})
    g.put(setpos.outputs['Geometry'], gout.inputs['Geometry'])
    return ng


def dynamics(prefix, modes_table, frames, n_modes, chi_table=None, n_res=0, name='Dynamics'):
    """Internal motion of a protein or nucleic acid from frame tables (molanim.dynamics computes them; numpy
    therefore knows every atom's position on every frame):
      chi     side chains turn about CB-CG (chi2), then CA-CB (chi1), by the angles in `chi_table` (row
              (frame - 1) x n_res + 'res_i', vector (chi1, chi2, 0) rad), for atoms with 'chi1_w' / 'chi2_w';
              axis atoms are found by their indices 'i_ca', 'i_cb', 'i_cg' in this mesh. Rigid turns about
              bonds: bond lengths and angles are kept.
      modes   offset = sum_k q_k(frame) 'm{k}', with normal-mode shapes 'm0'... (A per unit amplitude) and
              amplitudes q from `modes_table` (row frame - 1, vectors 'q0', 'q1', ... = modes 0-2, 3-5, ...).
    Apply after cuts and reveals (molecule(thermal_group=...)), like thermal()."""
    ng, g, gin, gout = new_group(prefix + name, [('Gain', 'NodeSocketFloat', 1.0)])
    I = gin.outputs
    frame = g.node('GeometryNodeInputSceneTime').outputs['Frame']
    fi = g.math('MINIMUM', g.math('MAXIMUM', g.math('FLOOR', g.math('ADD', frame, -0.5)), 0.0), float(frames - 1))
    geo = I['Geometry']
    pos = g.node('GeometryNodeInputPosition').outputs['Position']
    if chi_table is not None:
        tab = g.node('GeometryNodeObjectInfo', {'Object': chi_table}, transform_space='ORIGINAL').outputs['Geometry']
        row = g.math('ADD', g.math('MULTIPLY', fi, float(n_res)), g.attr('res_i'))
        chi1, chi2, _ = g.xyz(g.sample(tab, 'chi', row))
        for angle, w, a_idx, b_idx in ((chi2, 'chi2_w', 'i_cb', 'i_cg'), (chi1, 'chi1_w', 'i_ca', 'i_cb')):
            a = g.sample(geo, pos, g.attr(a_idx))
            b = g.sample(geo, pos, g.attr(b_idx))
            turn = g.math('MULTIPLY', g.math('MULTIPLY', angle, g.attr(w)), I['Gain'])
            rv = g.vec('SCALE', g.vec('NORMALIZE', g.vec('SUBTRACT', b, a)), scale=turn)
            geo = g.node('GeometryNodeSetPosition', {'Geometry': geo, 'Position': g.rotate_about(pos, a, rv)}).outputs['Geometry']
    tab = g.node('GeometryNodeObjectInfo', {'Object': modes_table}, transform_space='ORIGINAL').outputs['Geometry']
    offset = None
    for j in range((n_modes + 2) // 3):
        qs = g.xyz(g.sample(tab, f'q{j}', fi))
        for c in range(3):
            k = 3 * j + c
            if k >= n_modes:
                break
            term = g.vec('SCALE', g.attr(f'm{k}', 'FLOAT_VECTOR'), scale=qs[c])
            offset = term if offset is None else g.vec('ADD', offset, term)
    geo = g.node('GeometryNodeSetPosition', {'Geometry': geo, 'Offset': g.vec('SCALE', offset, scale=I['Gain'])}).outputs['Geometry']
    g.put(geo, gout.inputs['Geometry'])
    return ng


def chain_motion(prefix, clock, bend, twist, name='ChainMotion'):
    """Thermal motion of a double helix along its arc length 's' (A), as a worm-like chain (illustrative, from
    measured stiffness and rates; docs/motion.md). Every atom of a base pair shares 's', so base pairs move as
    units. Bending: the axis point ('axis_p') moves across the local frame ('nrm', 'bin') by a sum of octaves
    bend = [(RMS A, tau ns, wavelength A), ...]. Twisting: the base pair turns about the local tangent ('tan')
    by twist = (RMS rad, tau ns, correlation length A). Long waves are large and slow, short ones small and
    fast, so the shape far away barely changes while the helix rocks locally."""
    ng, g, gin, gout = new_group(prefix + name, [('Gain', 'NodeSocketFloat', 1.0)])
    I = gin.outputs
    p = g.node('GeometryNodeInputPosition').outputs['Position']
    s = g.attr('s')
    axis = g.attr('axis_p', 'FLOAT_VECTOR')
    rms, tau, length = twist
    along = g.node('ShaderNodeCombineXYZ', {'X': g.math('MULTIPLY', s, NOISE0_CORR / length), 'Y': 311.7}).outputs[0]
    angle = g.math('MULTIPLY', g.xyz(_unit_noise(g, along, _clock_w(g, clock, tau)))[0], g.math('MULTIPLY', rms, I['Gain']))
    p = g.rotate_about(p, axis, g.vec('SCALE', g.attr('tan', 'FLOAT_VECTOR'), scale=angle))
    offset = None
    for k, (rms, tau, wave) in enumerate(bend):
        along = g.node('ShaderNodeCombineXYZ', {'X': g.math('MULTIPLY', s, NOISE0_CORR / (wave / 2)), 'Y': 37.9 * (k + 1)}).outputs[0]
        nx, ny, _ = g.xyz(_unit_noise(g, along, _clock_w(g, clock, tau)))
        term = g.vec('ADD', g.vec('SCALE', g.attr('nrm', 'FLOAT_VECTOR'), scale=nx), g.vec('SCALE', g.attr('bin', 'FLOAT_VECTOR'), scale=ny))
        term = g.vec('SCALE', term, scale=rms)
        offset = term if offset is None else g.vec('ADD', offset, term)
    p = g.vec('ADD', p, g.vec('SCALE', offset, scale=I['Gain']))
    setpos = g.node('GeometryNodeSetPosition', {'Geometry': I['Geometry'], 'Position': p})
    g.put(setpos.outputs['Geometry'], gout.inputs['Geometry'])
    return ng


def molecule(prefix, breath_group, scale=0.64, ball=0.28, stick=0.16, section_rgb=(176, 220, 212), section_mix=0.45,
             name='Protein', thermal_group=None, space='ORIGINAL'):
    """Atoms -> spheres (context) and ball-and-stick (roles), with a camera-aimed cutaway funnel and a section slab.
    `breath_group` (optional) moves atoms before the cuts, `thermal_group` (optional) after them.

    Mesh: atom vertices plus bond edges. Per-atom attributes:
      vdw (A), role (0 context, >0 shown as ball-and-stick when revealed), g0/g1/g2 (reveal-group weights:
      g0 always, g1 by Look.x, g2 by Cut.z), ball (ball scale multiplier), stick_w (stick multiplier),
      dilate (vector, scaled by Path Control.y), col_ctx and col_hi (colours before/after reveal),
      emit_w and glow_w (emission weights driven by Look.y and Look.z).
    Controllers (empties, by location): Cut = (funnel open, slab open, group-2 reveal),
      Look = (group-1 reveal, glow 1, glow 2), Path Control = (-, dilation, -).
    The funnel removes atoms near the camera-target line in front of Target; the slab removes atoms in front
    of a vertical plane through Slab facing the camera. Atoms on cut surfaces turn toward `section_rgb`.
    space='RELATIVE' reads Camera, Target and Slab in the object's own frame, for a molecule whose object moves
    (rigid-body diffusion)."""
    ng, g, gin, gout = new_group(prefix + name, [
        ('Material', 'NodeSocketMaterial', None), ('Camera', 'NodeSocketObject', None), ('Target', 'NodeSocketObject', None),
        ('Slab', 'NodeSocketObject', None), ('Cut', 'NodeSocketObject', None), ('Look', 'NodeSocketObject', None),
        ('Scale', 'NodeSocketFloat', scale), ('Ball', 'NodeSocketFloat', ball), ('Stick', 'NodeSocketFloat', stick),
        ('Cut Enable', 'NodeSocketFloat', 1.0), ('Funnel', 'NodeSocketFloat', 9.0), ('Slope', 'NodeSocketFloat', 0.5),
        ('Back', 'NodeSocketFloat', 6.0), ('Slab Reach', 'NodeSocketFloat', 45.0),
        ('Path Control', 'NodeSocketObject', None)])
    I = gin.outputs
    geo = I['Geometry']
    if breath_group is not None:
        geo = g.node('GeometryNodeGroup', {'Geometry': geo}, node_tree=breath_group).outputs['Geometry']
    pos = g.node('GeometryNodeInputPosition').outputs['Position']
    # Optional rigid offsets per residue (e.g. an illustrative open state), scaled by Path Control.y.
    _, opened, _ = g.xyz(g.loc(I['Path Control']))
    geo = g.node('GeometryNodeSetPosition', {'Geometry': geo, 'Offset': g.vec('SCALE', g.attr('dilate', 'FLOAT_VECTOR'),
                                                                             scale=opened)}).outputs['Geometry']
    cam, tgt, slab = g.loc(I['Camera'], space), g.loc(I['Target'], space), g.loc(I['Slab'], space)
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
    if thermal_group is not None:                    # after the cuts: jitter never moves an atom across a cut
        geo = g.node('GeometryNodeGroup', {'Geometry': geo}, node_tree=thermal_group).outputs['Geometry']
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


def spheres(prefix, breath_group=None, sway=0.6, jitter=0.18, name='Lipids', thermal_group=None):
    """Atoms -> spheres from the 'radius' attribute, optionally breathing (with the group's Sway/Jitter overridden)
    and with thermal motion (see thermal())."""
    ng, g, gin, gout = new_group(prefix + name, [('Material', 'NodeSocketMaterial', None)])
    I = gin.outputs
    geo = I['Geometry']
    if breath_group is not None:
        geo = g.node('GeometryNodeGroup', {'Geometry': geo, 'Sway': sway, 'Jitter': jitter}, node_tree=breath_group).outputs['Geometry']
    if thermal_group is not None:
        geo = g.node('GeometryNodeGroup', {'Geometry': geo}, node_tree=thermal_group).outputs['Geometry']
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


def dotted_link(prefix, breath_group, dots=7, bead=0.17, name='Bridge', thermal_group=None):
    """Two vertices -> a dotted line of small beads (an interaction marker: salt bridge, H-bond), sized by
    the Show empty's x. Breathes with the atoms it joins (and moves with them under `thermal_group`, given the
    same 'thermal' values on its two vertices)."""
    ng, g, gin, gout = new_group(prefix + name, [('Material', 'NodeSocketMaterial', None), ('Show', 'NodeSocketObject', None),
                                                 ('Dots', 'NodeSocketInt', dots), ('Bead', 'NodeSocketFloat', bead)])
    I = gin.outputs
    geo = I['Geometry']
    for group in (breath_group, thermal_group):
        if group is not None:
            geo = g.node('GeometryNodeGroup', {'Geometry': geo}, node_tree=group).outputs['Geometry']
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
