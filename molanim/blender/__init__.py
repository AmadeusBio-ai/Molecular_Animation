"""Blender 5.x helpers. Import inside Blender only (they need bpy).

    scene   idempotent scene reset by name prefix, save one scene, keys, empties, lights, render settings
    nodes   a small geometry-node builder (G) and modifier inputs by socket name
    groups  geometry-node groups: molecule with roles + cutaway, spheres, frame-indexed particles, wave packets,
            tubes, dotted links; thermal motion from frame tables (dynamics), lipids as molecules (lipid_motion),
            a worm-like double helix (chain_motion); per-atom noise (breath, thermal) for old scripts
    mesh    point meshes with attributes, frame-indexed tracks, lookup tables (motion tables for dynamics),
            absolute shape keys (one coordinate source)
    look    attribute-driven, flat, glow and ghost materials; studio gradient world; bloom compositor
    rig     bake a camera path with depth of field; bake an object along keyed points or a per-frame track
    labels  the separate label pass: captions, evidence tags, timescales, pointers and links with halos
"""
