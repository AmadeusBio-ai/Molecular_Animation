"""Blender 5.x helpers. Import inside Blender only (they need bpy).

    scene   idempotent scene reset by name prefix, save one scene, keys, empties, lights, render settings
    nodes   a small geometry-node builder (G) and modifier inputs by socket name
    groups  geometry-node groups: breathing, molecule with roles + cutaway, spheres, frame-indexed particles,
            wave packets, tubes, dotted links
    mesh    point meshes with attributes, frame-indexed tracks, absolute shape keys (one coordinate source)
    look    attribute-driven, flat, glow and ghost materials; studio gradient world; bloom compositor
    rig     bake a camera path with depth of field; bake an object along keyed points
    labels  the separate label pass: captions, evidence tags, timescales, pointers with halos
"""
