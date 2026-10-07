"""Materials, the studio world and bloom (Blender 5.x). Colours are sRGB 0-255."""
import bpy

from ..color import lin


def _nodes(m):
    if m.node_tree is None:
        m.use_nodes = True
    return m.node_tree


def attr_material(name, roughness=0.45, specular=0.4, sheen=0.0, emission_tint=0.4):
    """Base colour from the 'col' attribute; emission strength from 'emit' (colour tinted toward warm white).
    Pairs with groups.molecule(), which stores both per atom."""
    m = bpy.data.materials.new(name)
    nt = _nodes(m)
    p = nt.nodes['Principled BSDF']
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Specular IOR Level'].default_value = specular
    p.inputs['Sheen Weight'].default_value = sheen
    col = nt.nodes.new('ShaderNodeAttribute')
    col.attribute_type, col.attribute_name = 'GEOMETRY', 'col'
    emit = nt.nodes.new('ShaderNodeAttribute')
    emit.attribute_type, emit.attribute_name = 'GEOMETRY', 'emit'
    tint = nt.nodes.new('ShaderNodeMix')
    tint.data_type = 'RGBA'
    sock = {s.identifier: s for s in tint.inputs}
    sock['Factor_Float'].default_value = emission_tint
    sock['B_Color'].default_value = (1.0, 0.92, 0.75, 1)
    nt.links.new(col.outputs['Color'], p.inputs['Base Color'])
    nt.links.new(col.outputs['Color'], sock['A_Color'])
    nt.links.new(next(s for s in tint.outputs if s.identifier == 'Result_Color'), p.inputs['Emission Color'])
    nt.links.new(emit.outputs['Fac'], p.inputs['Emission Strength'])
    col.location, emit.location, tint.location = (-700, 200), (-700, -250), (-400, -100)
    return m


def flat_material(name, rgb, emission=0.0, roughness=0.4):
    m = bpy.data.materials.new(name)
    p = _nodes(m).nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*lin(rgb), 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Emission Color'].default_value = (*lin(rgb), 1)
    p.inputs['Emission Strength'].default_value = emission
    return m


def glow_material(name, rgb, strength, rim=False):
    """Pure emission; with `rim`, emission grows toward grazing angles and the centre is see-through
    (a cavity or envelope that reads as a volume without hiding what is inside). Returns (material, emission node)."""
    m = bpy.data.materials.new(name)
    nt = _nodes(m)
    out = nt.nodes['Material Output']
    for nd in list(nt.nodes):
        if nd != out:
            nt.nodes.remove(nd)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*lin(rgb), 1)
    em.inputs['Strength'].default_value = strength
    if not rim:
        nt.links.new(em.outputs[0], out.inputs['Surface'])
        return m, em
    lw, curve, mix, clear = (nt.nodes.new(k) for k in ('ShaderNodeLayerWeight', 'ShaderNodeMapRange', 'ShaderNodeMixShader',
                                                       'ShaderNodeBsdfTransparent'))
    lw.inputs['Blend'].default_value = 0.25
    curve.inputs['From Min'].default_value, curve.inputs['From Max'].default_value = 0.05, 0.9
    curve.inputs['To Min'].default_value, curve.inputs['To Max'].default_value = 0.03, 1.0
    nt.links.new(lw.outputs['Facing'], curve.inputs['Value'])
    nt.links.new(curve.outputs['Result'], mix.inputs[0])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m, em


def ghost_material(name, rgb):
    """Translucent pale material for comparison ghosts (e.g. a previous state); returns (material, alpha socket)
    so the alpha can be keyframed."""
    m = flat_material(name, rgb, emission=0.6, roughness=0.3)
    return m, m.node_tree.nodes['Principled BSDF'].inputs['Alpha']


def gradient_world(name, top, bottom, ambient, ambient_strength):
    """The camera sees a soft vertical gradient (screen space, bottom -> top); objects are lit by a flat
    `ambient` colour instead. Returns (world, bottom colour socket, top colour socket) for keyframing."""
    w = bpy.data.worlds.new(name)
    nt = _nodes(w)
    out = nt.nodes['World Output']
    for n in list(nt.nodes):
        if n != out:
            nt.nodes.remove(n)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    rmap = nt.nodes.new('ShaderNodeMapRange')
    rmap.interpolation_type = 'SMOOTHSTEP'
    rmap.inputs['From Min'].default_value, rmap.inputs['From Max'].default_value = -0.1, 1.05
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    sock = {s.identifier: s for s in mix.inputs}
    sock['A_Color'].default_value = (*lin(bottom), 1)
    sock['B_Color'].default_value = (*lin(top), 1)
    nt.links.new(tc.outputs['Window'], sep.inputs[0])
    nt.links.new(sep.outputs['Y'], rmap.inputs['Value'])
    nt.links.new(rmap.outputs['Result'], sock['Factor_Float'])
    seen, lit = nt.nodes.new('ShaderNodeBackground'), nt.nodes.new('ShaderNodeBackground')
    nt.links.new(next(s for s in mix.outputs if s.identifier == 'Result_Color'), seen.inputs['Color'])
    lit.inputs['Color'].default_value = (*lin(ambient), 1)
    lit.inputs['Strength'].default_value = ambient_strength
    path, pick = nt.nodes.new('ShaderNodeLightPath'), nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(path.outputs['Is Camera Ray'], pick.inputs[0])
    nt.links.new(lit.outputs[0], pick.inputs[1])
    nt.links.new(seen.outputs[0], pick.inputs[2])
    nt.links.new(pick.outputs[0], out.inputs['Surface'])
    return w, sock['A_Color'], sock['B_Color']


def bloom(scene, name, threshold=1.0, strength=0.55, size=0.55, quality='High'):
    """Compositor: render -> soft bloom on highlights above `threshold` (emissive accents) -> output."""
    old = bpy.data.node_groups.get(name)
    if old and old.users == 0:
        bpy.data.node_groups.remove(old)
    ng = bpy.data.node_groups.new(name, 'CompositorNodeTree')
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl, glare, out = ng.nodes.new('CompositorNodeRLayers'), ng.nodes.new('CompositorNodeGlare'), ng.nodes.new('NodeGroupOutput')
    rl.scene = scene
    glare.inputs['Type'].default_value = 'Bloom'
    glare.inputs['Quality'].default_value = quality
    for k, v in (('Threshold', threshold), ('Strength', strength), ('Size', size)):
        glare.inputs[k].default_value = v
    ng.links.new(rl.outputs['Image'], glare.inputs['Image'])
    ng.links.new(glare.outputs['Image'], out.inputs['Image'])
    scene.compositing_node_group = ng
    scene.render.use_compositing = True
    return ng
