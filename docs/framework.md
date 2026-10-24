# The `molanim` framework

`molanim` is a small Python package used by shot scripts inside Blender 5.x. It has two layers:

- **The pure layer** (`molanim.*`) needs only numpy. It runs in Blender's bundled Python and in plain Python, and the unit tests in `tests/` cover it. Put science here: anything you must be able to check.
- **The Blender layer** (`molanim.blender.*`) builds scenes: geometry-node groups, materials, the camera rig and the label pass.

A shot script puts the repo root on `sys.path`, calls `molanim.reload()` (so re-running in a live Blender picks up edits), and imports what it needs. Start from `templates/shot/shot.py` (`python pipeline.py new`) or from the case study.

Conventions:
- 1 Blender unit = 1 Å.
- Colours are written as sRGB 0–255 and converted exactly.
- Frames are 1-based.
- An "atom table" is a dict of equal-length numpy arrays (`chain`, `resi`, `resn`, `name`, `alt`, `element`, `occupancy`, `model`, `xyz`).

## Pure layer

### `molanim.structure`: structures, states, topology

| Function | Use |
| --- | --- |
| `read_mmcif(path, skip=WATERS\|ADDITIVES, hydrogens=False, model=None)` | Atom table and raw lines; every alt-loc kept |
| `select(table, mask)`, `first_conformer(table)` | Subsets; drop alternate conformers |
| `title(lines)`, `method(lines)`, `item(lines, key)` | Entry metadata for captions and evidence tags |
| `assembly_operator(lines, op_id)` | 4×4 matrix of a `_pdbx_struct_oper_list` entry (build oligomers from the deposited assembly) |
| `match_states(ref, other, ref_key, other_key, keep_other)` | Two states of one molecule matched atom by atom (undo renumbering, choose the alt-loc); adds `start`, `end`, `matched` |
| `bonds(table, xyz, links, residue)` | Covalent bonds: within residues by distance, peptide, disulfide, plus explicit links (e.g. a Schiff base); spatial hash, no n×n matrix |
| `close_pairs(xyz, cutoff)` | All atom pairs closer than `cutoff` |
| `neighbours`, `angle_pairs`, `torsion_pairs` | Topology for constraints |
| `transform`, `kabsch`, `dihedral`, `radii`, `find` | Geometry and measurements for checks |

### `molanim.morph`: illustrative motion between experimental endpoints

| Function | Use |
| --- | --- |
| `morph(A, B, edges, moving, steps, rigid_pairs, iterations)` | Constrained interpolation: bond lengths, angles and chosen 1-4 distances follow their interpolated values, and non-bonded atoms are kept apart. Stage large changes with several calls |
| `max_bond_deviation(frames, edges)` | The number to report in `RESULT` |

### `molanim.pathway`: is there a way through?

| Function | Use |
| --- | --- |
| `pore_profile(xyz, radius, guide, ys)` | HOLE-like slice search for the widest point along a guide |
| `relax_path(centres, xyz, radius)` | Elastic-band smoothing that still seeks free space |
| `clearance(points, xyz, radius)` | Free radius (distance to the nearest atom surface) |
| `polyline`, `arc_length` | Resampling and arc length |

### `molanim.membrane`: context, not simulation

| Function | Use |
| --- | --- |
| `bilayer(bounds, protein_xyz, keep=...)` | POPC-like bilayer on a jittered hexagonal grid, with lipids clashing with the protein removed; `keep` cuts a section |
| `occupancy(xyz, clearance)` | Fast "is this point near the protein?" test |
| `lipid_handles(mem, rng, protein_xyz)` | Each lipid atom's pivots, weights, seed and mobility, so `groups.lipid_motion` moves lipids as molecules (annular lipids move less) |

### `molanim.particles`: ions and solvent, sparse and irregular

| Function | Use |
| --- | --- |
| `drift(rng, frames, n, amp)` | Smooth, aperiodic wandering |
| `transits(rng, path, sites, entries, frames)` | Stop-and-go passage between binding sites, with irregular dwell times and one particle per site |
| `brownian(rng, starts, times, exposure, D, lo, hi)` | Free diffusion on the clock, reflected in boxes, exposure-averaged |
| `keep_clear(tracks, X, need, atom_radius, offsets, weights, moves, drop_below)` | Steer tracks to keep a minimum gap from atom surfaces (`moves(f)`: the atoms' thermal displacement on frame f); reports the smallest gap and the step continuity. `drop_below` leaves out a particle wedged where it cannot clear (reported as `dropped`) |

### `molanim.dynamics`: thermal and Brownian motion from physical rates

Units are Å, ns and rad. The schematic and its sources are in `docs/motion.md`.

| Function | Use |
| --- | --- |
| `clock(frames, ns_per_frame, holds)` | Molecular time per frame and each frame's span; `holds` slow or stop it for a labelled timescale change |
| `ou(rng, times, exposure, shape, sigma, tau, shutter='box', period=None)` | Ornstein–Uhlenbeck processes on the clock, averaged over each frame's exposure. They diffuse at short times and are tethered at long times. `shutter='triangle'` weights the window softly, so diffusing bodies change speed smoothly instead of jerking every frame. `period` (ns) makes them repeat exactly, for loops (`periodic_ou`) |
| `protein_motion(rng, X, resn, resi, name, chain, times, exposure, rmsf, tau, ..., period)` | The whole recipe for a protein or nucleic acid: residue-network normal modes plus side-chain turns scaled by burial. Ligands ride on the residue they bond to (whose side chain is held), other riders on the nearest node; large structures are coarsened. Returns the frame tables, mode shapes, topology and a report for `RESULT` |
| `displacement(motion, X, f)` | Every atom's displacement on a frame, exactly as `groups.dynamics` applies it: for clearances, bond-strain and RMSF checks |
| `exposure_factor(tau, window, shutter='box')` | How much of a motion survives exposure averaging |
| `window_mean(grid, path, times, exposure, shutter)` | The exposure average itself (box or triangle), for processes you sample yourself |
| `stokes_einstein`, `stokes_einstein_debye`, `ellipsoid`, `perrin`, `hydrodynamic_radius`, `viscosity` | Translational and rotational diffusion; Perrin prolate spheroids from a structure's second moments; water viscosity by temperature |
| `rigid_brownian(rng, times, exposure, D_t, D_r, tether_t, tether_r, shutter)`, `tether(D, sigma)` | Tethered rigid-body diffusion and tumbling (per body axis); the correlation time that holds a diffusing body within RMS sigma |
| `rotation_matrix(rotvec)` | Rodrigues, batched |
| `anm(nodes, cutoff, modes, bonded)`, `residue_nodes`, `sequence_pairs` | Anisotropic network model with stiffer sequence-neighbour springs |
| `atom_shapes(X, vec, nodes, node_of, pairs, rigid)` | Per-atom mode shapes blended along the chain, so bonds keep their lengths to first order |
| `mode_scale`, `mode_amplitudes(..., period)`, `node_rmsf` | Calibrate to a mean RMSF; Langevin amplitudes (variance ∝ 1/λ, τ ∝ 1/λ) |
| `chi_topology`, `apply_chi`, `burial` | Side-chain χ1/χ2 turns about bonds (the numpy twin of `groups.dynamics`) |
| `wlc_bend(wavelengths, persistence)`, `wlc_twist(length, persistence)` | Worm-like-chain bending bands and twist: RMS and relaxation time |

### `molanim.timeline` and `molanim.color`

| Function | Use |
| --- | --- |
| `smoothstep`, `smootherstep`, `ramp(frame, a, b)` | Easing and beat ramps |
| `camera_path(keys, points, frames)` | Keys (frame, aim, distance, azimuth, elevation, lens) → per-frame camera, with log-distance dives |
| `orbit_path(aim, distance, elevation, lens, frames)` | A constant-speed orbit that closes exactly (loops) |
| `keyed(keys, points, frames)` | Generic eased keys with named points |
| `project(p, loc, aim, lens, res)` | 3D → pixel, for label anchors |
| `label_data(spec, path, anchors, res, frames, fps, levels)` | A film's labels as plain data for a web page that draws them over the clean film: header, captions, evidence tags with their level, timescales, and every pointer and link with its anchors projected on each frame exactly as the label pass projects them (fractions of the frame), plus layout hints |
| `fstop_for(ratio, lens, distance)` | Depth of field as a fraction of the focus distance |
| `color.srgb`, `lin`, `shade(rng, ramp, n)`, `tile`, `hex_rgb` | Exact sRGB → linear; per-atom tone variation |

### `molanim.cartoon`: folds as cartoons, nucleic acids as ladders

Builders return plain mesh arrays `(vertices, faces, attributes)` for `mesh.surface_mesh`.

| Function | Use |
| --- | --- |
| `secondary_structure(lines, table)` | Per-atom H / E / C from the deposited `_struct_conf` and `_struct_sheet_range` (author chain and number) |
| `estimate_secondary_structure(ca, partners)` | H / E / C from Calpha geometry for models without an annotation: two consecutive i, i+3 / i, i+4 turns make a helix; extended residues paired 4.2-5.6 A across a sheet make a strand. On mainly helical deposited proteins it recovers 90-93 % of helices; strands 84-93 % (1EMA, 1IGT); short helices in beta proteins are missed |
| `protein_segments(table, ss, gap, min_residues)` | Continuous Calpha traces with carbonyls, split at chain breaks |
| `ribbon(segment, k)`, `cartoon(table, ss, per_atom)` | Richardson cartoons: a Catmull-Rom backbone through the Calphas whose width follows the peptide C=O, so helix ribbons face out from their axis and strands lie in their sheet; strand arrowheads on each strand's last residue; coil tubes. `per_atom` samples attributes (a colour, a pLDDT, normal-mode shapes) at each vertex's residue; `ring` numbers the cross-sections, for cuts that remove whole sections |
| `ladder(table)`, `nucleotides(table)` | A tube per strand through the P atoms, each base as a slab cut from its own ring atoms (so pairing, stacking and tilt are the measured ones), a rod from C4' through C1' to the base |
| `ring_fills(table)` | Sugar and base rings as thin plates over a stick model (the 'fill' style of molecular viewers); attributes `part`, `base`, `nt`, `plate` |
| `sticks(xyz, edges, radius)`, `sweep`, `catmull_rom`, `plane`, `combine` | Half-bonds for ball-and-stick; the tube sweep and spline underneath; best-fit planes |

### `molanim.electro`: electrons, drawn for what they are

| Function | Use |
| --- | --- |
| `formal_charges(table)` | Formal charges at neutral pH: Lys, Arg +1; Asp, Glu -1; chain termini; -1 per nucleic-acid phosphate; heme propionates; monatomic ions |
| `potential(points, xyz, q)` | Coulombic potential (kcal/(mol e)) with a distance-dependent dielectric of 4r, as UCSF ChimeraX's `coulombic` command; an estimate for pictures, not Poisson-Boltzmann |
| `potential_colors(phi, limit)` | Red (negative) - white - blue (positive), saturating at +-10, ChimeraX's defaults |
| `pi_chain_lobes(xyz, offset)` | Lobes along a conjugated chain that need not be flat (retinal's polyene): a normal per atom from its two chain bonds, so the lobes split where a bond twists (conjugation broken) and report the twist per bond |
| `pi_systems(table)`, `pi_lobes(xyz, offset)` | Planar conjugated groups (aromatic side chains, nucleobases, heme porphyrin, the GFP chromophore) and two lobes per group, one on each face: the shared, delocalised pi electrons that resonance describes, in place of alternating double bonds |

The van der Waals envelope (`groups.envelope`) stands for the outer edge of the electron cloud: the usual size of a molecule is its 0.001 e/bohr^3 density contour, and radii there match van der Waals radii to about 0.2 A (sources in `docs/depiction-sources.md`). Colour it by `potential` where electrostatics is the point (DNA on histones, a cation-selective pore), and keep emission for what really emits light (a fluorescent chromophore).

## Blender layer (`molanim.blender`)

| Module | Function | Use |
| --- | --- | --- |
| `scene` | `reset_scene(name, prefix)` | Idempotent rebuild: removes the previous build and only that prefix's orphans |
| | `save_scene(scene, path)` | Write only this scene and its dependencies |
| | `collection`, `empty`, `keys`, `set_linear`, `fcurves`, `look_at`, `sun`, `show` | Building blocks; empties double as animated controllers |
| | `cycles_settings(scene, res, frames, fps, samples)` | Studio defaults: GPU, adaptive sampling, denoised, Standard view |
| `nodes` | `G`, `new_group`, `set_modifier_inputs`, `add_nodes_modifier` | A compact geometry-node builder; modifier inputs by socket name (5.x API) |
| | `by_type(tree, kind)` | A default node by type (`'BSDF_PRINCIPLED'`, `'OUTPUT_MATERIAL'`, `'OUTPUT_WORLD'`, `'BACKGROUND'`): default node names follow the UI language |
| `groups` | `breath(prefix, ..., loop_frames)` | Coherent sway plus jitter; exactly periodic when `loop_frames` is set. Per-atom noise: kept for old scripts; new films use `dynamics` |
| | `molecule(prefix, breath_group, ..., thermal_group, space)` | Spheres for context, ball-and-stick for roles, a camera-aimed cutaway funnel, a section slab, reveal groups, glow, optional per-residue offsets. `thermal_group` (e.g. `dynamics`) moves atoms after the cuts, so no atom flickers across a cut surface; `space='RELATIVE'` for a molecule whose object tumbles |
| | `spheres`, `frame_spheres` | Plain or frame-indexed sphere clouds (lipids, ions); `spheres` takes a `thermal_group` too |
| | `wave_packets` | Photons as a symbol |
| | `tube` | A cavity or pathway tube from measured and illustrative radii |
| | `dotted_link` | An interaction marker between two atoms; with `thermal_group` it moves with the atoms it joins |
| | `envelope(prefix, voxel, smooth, offset)` | Points with a `radius` -> the surface of their union (SDF grid, smoothed): the van der Waals envelope, or pi lobes from `electro.pi_lobes` / `pi_chain_lobes` |
| | `section(prefix, space, group)` | `molecule()`'s funnel and slab for meshes (cartoons, sticks, surfaces): deletes what the cuts remove; `group='ring'` removes whole ribbon cross-sections, so cut ends are clean. Put it before the motion modifier |
| | `offset_by(prefix, attribute)` | Points move by a vector attribute x Control.y (an illustrative opening, for meshes) |
| | `ball_stick(prefix, stick, fill)`, `plates(prefix)` | Nucleic acids (or any molecule) atom by atom: a ball per atom and a stick per bond edge, morphing continuously to space-filling as Detail.x goes 1 -> 0 (a camera pulling back until bonds are sub-pixel), appearing atom by atom on Show.x; ring plates that grow and drop out with them |
| | `dynamics(prefix, modes_table, frames, n_modes, chi_table, n_res)` | Normal modes and side-chain turns read from frame tables (numpy knows every atom's position) |
| | `lipid_motion(prefix, clock, motion)` | Lipids as molecules: spin, wobble, bob, rattle and a shared flow; bending chains; swinging choline |
| | `chain_motion(prefix, clock, bend, twist)` | A double helix that bends and twists along its arc length as a worm-like chain |
| | `thermal(prefix, ...)` | Per-atom noise (version 2; kept for old scripts, not for new films) |
| `mesh` | `points_mesh`, `frame_tracks`, `table`, `absolute_keys` | Attribute-carrying point meshes; per-frame tracks; lookup tables for geometry nodes; morphs as shape keys |
| | `surface_mesh(name, verts, faces, attrs)` (`('INT', values)` for integer attributes), `realize(obj)`, `vertices(obj)`, `set_point_colors(obj, name, rgb)` | Objects from `cartoon` arrays; a node-built surface baked to a mesh so numpy can colour its vertices (e.g. by `electro.potential`) |
| | `dynamics_tables(prefix, motion, collection, loop)`, `dynamics_attrs(motion, idx, turns)` | Frame tables and per-atom attributes for `groups.dynamics` from `dynamics.protein_motion` (a loop's last row repeats frame 1) |
| `look` | `attr_material`, `flat_material`, `glow_material`, `ghost_material`, `gradient_world`, `bloom` | Materials, the studio backdrop (the camera sees a gradient, objects see the ambient), bloom |
| | `ribbon_material(alpha)`, `skin_material(opacity, edge, rgb)`, `fluorescence_material(rgb, strength)` | Satin cartoons from the `col` attribute (opacity from an attribute with `alpha`, e.g. low-confidence predictions; `attr_material` takes it too); a translucent skin that is denser at its silhouette and does not glow; a skin that emits, only for a real fluorophore |
| `rig` | `bake_camera(cam, aim, path, aperture_ratio)`, `bake_location`, `bake_track` | Camera with tracking and proportional depth of field; controllers along keyed points or per-frame tracks (a clock, a moving target) |
| `labels` | `label_pass(scene_name, prefix, spec, path, anchors, res, frames, fps, blend_path)` | The label scene: captions, evidence tags, timescales, pointers with leader lines, links between two anchors (solid or dashed, optional mid text: editorial guides, hypotheses), ink and halo switching per shot |

### The controller pattern

`groups.molecule` reads three empties by location:
- **`Cut`**: x = funnel open, y = section slab, z = reveal group 2.
- **`Look`**: x = reveal group 1, y = glow 1, z = glow 2.
- **`Path Control`**: y scales the per-residue `dilate` offsets.

Choreography is plain keyframes on these channels (`scene.keys(ctl, 'location', [(frame, value), ...], index)`), so a shot's whole timing can be read from its script.

## Pipeline tools

- `tools/render.py` runs inside Blender. It picks the GPU (OptiX first) and renders a still, a crop (`--border`) or a resumable sequence.
- `tools/encode.py` encodes PNG sequences to H.264 MP4 and VP9 WebM, with an optional `--overlay` label pass, and verifies frame counts and durations with ffprobe.
- `tools/bpy_lint.py` flags Blender Python written for an older Blender: errors for APIs that 5.2 rejects, warnings for deprecated or fragile ones (`use_nodes`, default nodes by name, `bpy.ops` where the data API works). It needs no Blender: `pipeline.py lint`, `pipeline.py build` (first), and the test suite.
- `tools/api_probe.py` runs inside Blender and checks the API facts that `docs/blender-5.md` states and the lint relies on. `pipeline.py doctor` runs it.
- `tools/mcp_smoke_test.py` is a minimal scene for checking a Blender MCP connection.
- `tools/blender_mcp_launch.py` is the Windows stdin fix for the Blender MCP server (`docs/setup.md`).
- `pipeline.py` discovers `examples/*/shots.json` and `projects/*/shots.json` and wraps all of the above (`docs/workflow.md`).

## Extending the framework

Add a function to `molanim` when a second shot needs it. Keep science pure-numpy with a unit test, keep Blender code thin, and document it in this file. A change that alters existing behaviour must keep `python pipeline.py check channelrhodopsin` passing, or come with a re-rendered, re-verified case study.
