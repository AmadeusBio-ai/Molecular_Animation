"""Materials, the studio world and bloom (Blender 5.x). Colours are sRGB 0-255.

New materials and worlds come with node trees in 5.x (Principled BSDF + Material Output, Background + World Output),
so nothing here sets the deprecated `use_nodes`; default nodes are found by type (nodes.by_type)."""
import bpy

from ..color import lin
from .nodes import by_type


def _alpha(m, attribute):
    """Opacity of the Principled BSDF from a point attribute (0 clear - 1 solid), e.g. low-confidence parts of a
    prediction drawn translucent."""
    nt = m.node_tree
    a = nt.nodes.new('ShaderNodeAttribute')
    a.attribute_type, a.attribute_name = 'GEOMETRY', attribute
    a.location = (-700, -500)
    nt.links.new(a.outputs['Fac'], by_type(nt, 'BSDF_PRINCIPLED').inputs['Alpha'])
    m.surface_render_method = 'DITHERED'


def attr_material(name, roughness=0.45, specular=0.4, sheen=0.0, emission_tint=0.4, alpha=None):
    """Base colour from the 'col' attribute; emission strength from 'emit' (colour tinted toward warm white).
    Pairs with groups.molecule(), which stores both per atom. `alpha` names an opacity attribute (optional)."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    p = by_type(nt, 'BSDF_PRINCIPLED')
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
    if alpha:
        _alpha(m, alpha)
    return m


def flat_material(name, rgb, emission=0.0, roughness=0.4):
    m = bpy.data.materials.new(name)
    p = by_type(m.node_tree, 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*lin(rgb), 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Emission Color'].default_value = (*lin(rgb), 1)
    p.inputs['Emission Strength'].default_value = emission
    return m


def glow_material(name, rgb, strength, rim=False):
    """Pure emission; with `rim`, emission grows toward grazing angles and the centre is see-through
    (a cavity or envelope that reads as a volume without hiding what is inside). Returns (material, emission node)."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    out = by_type(nt, 'OUTPUT_MATERIAL')
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
    return m, by_type(m.node_tree, 'BSDF_PRINCIPLED').inputs['Alpha']


def gradient_world(name, top, bottom, ambient, ambient_strength):
    """The camera sees a soft vertical gradient (screen space, bottom -> top); objects are lit by a flat
    `ambient` colour instead. Returns (world, bottom colour socket, top colour socket) for keyframing."""
    w = bpy.data.worlds.new(name)
    nt = w.node_tree
    out = by_type(nt, 'OUTPUT_WORLD')
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


def ribbon_material(name, roughness=0.38, coat=0.35, subsurface=0.08, alpha=None):
    """Cartoons and ladders: base colour from the 'col' point attribute; a satin plastic with a light clear coat,
    so folds read by their shading rather than by outlines. `alpha` names an opacity attribute (optional)."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    p = by_type(nt, 'BSDF_PRINCIPLED')
    for k, v in (('Roughness', roughness), ('Coat Weight', coat), ('Coat Roughness', 0.15),
                 ('Subsurface Weight', subsurface), ('Specular IOR Level', 0.45)):
        p.inputs[k].default_value = v
    col = nt.nodes.new('ShaderNodeAttribute')
    col.attribute_type, col.attribute_name = 'GEOMETRY', 'col'
    nt.links.new(col.outputs['Color'], p.inputs['Base Color'])
    col.location = (-400, 200)
    if alpha:
        _alpha(m, alpha)
    return m


def skin_material(name, opacity=0.18, edge=0.6, rgb=None):
    """A translucent skin (the van der Waals envelope, a pi lobe): colour from the 'col' point attribute (e.g. an
    electrostatic potential) or a fixed sRGB `rgb`; `opacity` where the skin faces the camera, rising to `edge`
    at its silhouette, so the shape reads on white without hiding what is inside. No emission: it does not glow."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    out = by_type(nt, 'OUTPUT_MATERIAL')
    p = by_type(nt, 'BSDF_PRINCIPLED')
    p.inputs['Roughness'].default_value = 0.45
    p.inputs['Specular IOR Level'].default_value = 0.3
    if rgb is None:
        col = nt.nodes.new('ShaderNodeAttribute')
        col.attribute_type, col.attribute_name = 'GEOMETRY', 'col'
        nt.links.new(col.outputs['Color'], p.inputs['Base Color'])
    else:
        p.inputs['Base Color'].default_value = (*lin(rgb), 1)
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.4
    ramp = nt.nodes.new('ShaderNodeMapRange')
    ramp.interpolation_type = 'SMOOTHSTEP'
    ramp.inputs['From Min'].default_value, ramp.inputs['From Max'].default_value = 0.2, 1.0
    ramp.inputs['To Min'].default_value, ramp.inputs['To Max'].default_value = opacity, edge
    clear, mix = nt.nodes.new('ShaderNodeBsdfTransparent'), nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lw.outputs['Facing'], ramp.inputs['Value'])
    nt.links.new(ramp.outputs['Result'], mix.inputs[0])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(p.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def fluorescence_material(name, rgb, strength, opacity=0.5):
    """A translucent skin that emits light of its own colour: only for something that really fluoresces (the GFP
    chromophore emits green light). Returns (material, emission strength socket)."""
    m = skin_material(name, opacity=opacity, edge=min(1.0, opacity + 0.3), rgb=rgb)
    p = by_type(m.node_tree, 'BSDF_PRINCIPLED')
    p.inputs['Emission Color'].default_value = (*lin(rgb), 1)
    p.inputs['Emission Strength'].default_value = strength
    return m, p.inputs['Emission Strength']
