"""molanim: building blocks for honest, beautiful molecular animation in Blender.

Pure-numpy modules (run anywhere, unit-tested):
    structure   mmCIF reading, assemblies, atom matching between states, bonds, measurements
    morph       chemically constrained interpolation between two conformations
    pathway     HOLE-like pathway search and free-radius profiles
    membrane    procedural lipid bilayer with protein exclusion
    dynamics    thermal and Brownian motion from physical rates: clock, exposure, diffusion, normal modes
    particles   illustrative ion/solvent motion: diffusion, drift, site-to-site transits, clearance steering
    timeline    easing, beat ramps, keyed camera paths, pinhole projection for labels
    color       exact sRGB -> linear conversion, per-atom tone variation
    cartoon     protein ribbons from secondary structure, nucleic-acid ladders (mesh arrays)
    electro     formal charges, Coulombic potential, pi systems and their lobes

Blender modules (import inside Blender 5.x only): molanim.blender.*
    scene, nodes, groups, mesh, look, rig, labels
"""
import importlib
import sys

__version__ = '0.3.0'

_ORDER = ('color', 'timeline', 'structure', 'cartoon', 'electro', 'morph', 'pathway', 'membrane', 'dynamics',
          'particles',
          'blender.scene', 'blender.nodes', 'blender.groups', 'blender.mesh', 'blender.look', 'blender.rig',
          'blender.labels')


def reload():
    """Re-import every loaded molanim module in dependency order. Shot scripts call this first, so re-running
    a script in a live Blender session (Blender MCP) picks up edits to the framework."""
    for name in _ORDER:
        module = sys.modules.get(f'{__name__}.{name}')
        if module is not None:
            importlib.reload(module)
