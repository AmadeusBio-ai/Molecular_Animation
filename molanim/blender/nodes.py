"""A small geometry-node builder, and modifier inputs by socket name (Blender 5.x)."""
import bpy


class G:
    """Geometry-node builder. Inputs may be sockets (linked) or constants (set)."""

    def __init__(self, ng):
        self.ng, self.N, self.L = ng, ng.nodes, ng.links

    def put(self, value, sock):
        if isinstance(value, bpy.types.NodeSocket):
            self.L.new(value, sock)
        elif value is not None:
            sock.default_value = value

    def node(self, kind, ins=None, **props):
        n = self.N.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        for k, v in (ins or {}).items():
            self.put(v, n.inputs[k])
        return n

    def math(self, op, a, b=None, c=None):
        n = self.node('ShaderNodeMath', operation=op)
        for k, v in enumerate((a, b, c)):
            self.put(v, n.inputs[k])
        return n.outputs[0]

    def vec(self, op, a, b=None, scale=None):
        n = self.node('ShaderNodeVectorMath', operation=op)
        for k, v in enumerate((a, b)):
            self.put(v, n.inputs[k])
        if scale is not None:
            self.put(scale, n.inputs['Scale'])
        return n.outputs['Value'] if op in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else n.outputs['Vector']

    def smooth(self, x, lo, hi, to_lo=0.0, to_hi=1.0):
        n = self.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP', clamp=True)
        for k, v in (('Value', x), ('From Min', lo), ('From Max', hi), ('To Min', to_lo), ('To Max', to_hi)):
            self.put(v, n.inputs[k])
        return n.outputs['Result']

    def attr(self, name, kind='FLOAT'):
        return self.node('GeometryNodeInputNamedAttribute', {'Name': name}, data_type=kind).outputs['Attribute']

    def loc(self, obj_socket):
        """Location of an object input: empties used as animated controllers (x, y, z = three channels)."""
        return self.node('GeometryNodeObjectInfo', {'Object': obj_socket}, transform_space='ORIGINAL').outputs['Location']

    def xyz(self, v):
        n = self.node('ShaderNodeSeparateXYZ', {'Vector': v})
        return n.outputs['X'], n.outputs['Y'], n.outputs['Z']

    def mix_color(self, f, a, b):
        n = self.node('ShaderNodeMix', data_type='RGBA')
        sock = {s.identifier: s for s in n.inputs}
        self.put(f, sock['Factor_Float'])
        self.put(a, sock['A_Color'])
        self.put(b, sock['B_Color'])
        return next(s for s in n.outputs if s.identifier == 'Result_Color')

    def store(self, geo, name, value, kind='FLOAT'):
        return self.node('GeometryNodeStoreNamedAttribute', {'Geometry': geo, 'Name': name, 'Value': value},
                         data_type=kind, domain='POINT').outputs['Geometry']

    def this_frame(self, geo):
        """Keep the vertices whose 'f' attribute is the current frame (frame-indexed point tracks)."""
        frame = self.node('GeometryNodeInputSceneTime').outputs['Frame']
        other = self.math('GREATER_THAN', self.math('ABSOLUTE', self.math('SUBTRACT', self.attr('f'), frame)), 0.5)
        return self.node('GeometryNodeDeleteGeometry', {'Geometry': geo, 'Selection': other}, domain='POINT',
                         mode='ALL').outputs['Geometry']

    def material(self, geo, mat):
        return self.node('GeometryNodeSetMaterial', {'Geometry': geo, 'Material': mat}).outputs['Geometry']


def new_group(name, sockets):
    """Geometry-node group with a Geometry input/output plus `sockets` = [(label, socket type, default)].
    Returns (group, builder, group-input node, group-output node)."""
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    for label, kind, value in sockets:
        sock = ng.interface.new_socket(label, in_out='INPUT', socket_type=kind)
        if value is not None:
            sock.default_value = value
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    g = G(ng)
    return ng, g, g.node('NodeGroupInput'), g.node('NodeGroupOutput')


def set_modifier_inputs(mod, values):
    """Blender 5.x: modifier inputs live at mod.properties.inputs.<socket identifier>.value
    (mod['Socket_0'] = ... raises "doesn't support IDProperties")."""
    ids = {item.name: item.identifier for item in mod.node_group.interface.items_tree
           if item.item_type == 'SOCKET' and item.in_out == 'INPUT'}
    for name, value in values.items():
        getattr(mod.properties.inputs, ids[name]).value = value


def add_nodes_modifier(obj, group, inputs, name='Nodes'):
    mod = obj.modifiers.new(name, 'NODES')
    mod.node_group = group
    set_modifier_inputs(mod, inputs)
    return mod
