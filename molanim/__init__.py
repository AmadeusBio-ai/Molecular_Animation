"""molanim: building blocks for honest, beautiful molecular animation in Blender.

Pure-numpy modules (run anywhere, unit-tested):
    structure   mmCIF reading, assemblies, atom matching between states, bonds, measurements
    morph       chemically constrained interpolation between two conformations
    pathway     HOLE-like pathway search and free-radius profiles
    membrane    procedural lipid bilayer with protein exclusion
    particles   illustrative ion/solvent motion: drift, site-to-site transits, clearance steering
    timeline    easing, beat ramps, keyed camera paths, pinhole projection for labels
    color       exact sRGB -> linear conversion, per-atom tone variation

Blender modules (import inside Blender 5.x only): molanim.blender.*
    scene, nodes, groups, mesh, look, rig, labels
"""
import importlib
import sys

__version__ = '0.1.0'

_ORDER = ('color', 'timeline', 'structure', 'morph', 'pathway', 'membrane', 'particles',
          'blender.scene', 'blender.nodes', 'blender.groups', 'blender.mesh', 'blender.look', 'blender.rig',
          'blender.labels')


def reload():
    """Re-import every loaded molanim module in dependency order. Shot scripts call this first, so re-running
    a script in a live Blender session (Blender MCP) picks up edits to the framework."""
    for name in _ORDER:
        module = sys.modules.get(f'{__name__}.{name}')
        if module is not None:
            importlib.reload(module)
