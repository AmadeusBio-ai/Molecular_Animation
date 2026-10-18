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

### `molanim.particles`: ions and solvent, sparse and irregular

| Function | Use |
| --- | --- |
| `drift(rng, frames, n, amp)` | Smooth, aperiodic wandering |
| `transits(rng, path, sites, entries, frames)` | Stop-and-go passage between binding sites, with irregular dwell times and one particle per site |
| `brownian(rng, starts, times, exposure, D, lo, hi)` | Free diffusion on the clock, reflected in boxes, exposure-averaged |
| `keep_clear(tracks, X, need, atom_radius, offsets, weights, moves)` | Steer tracks to keep a minimum gap from atom surfaces (`moves(f)`: the atoms' thermal displacement on frame f); reports the smallest gap and the step continuity |

### `molanim.dynamics`: thermal and Brownian motion from physical rates

Units are Å, ns and rad. The schematic and its sources are in `docs/motion.md`.

| Function | Use |
| --- | --- |
| `clock(frames, ns_per_frame, holds)` | Molecular time per frame and each frame's span; `holds` slow or stop it for a labelled timescale change |
| `ou(rng, times, exposure, shape, sigma, tau, shutter='box')` | Ornstein–Uhlenbeck processes on the clock, averaged over each frame's exposure. They diffuse at short times and are tethered at long times. `shutter='triangle'` weights the window softly, so diffusing bodies change speed smoothly instead of jerking every frame |
| `exposure_factor(tau, window, shutter='box')` | How much of a motion survives exposure averaging |
| `stokes_einstein`, `stokes_einstein_debye`, `ellipsoid`, `perrin` | Translational and rotational diffusion; Perrin prolate spheroids from a structure's second moments |
| `rigid_brownian(rng, times, exposure, D_t, D_r, tether_t, tether_r)` | Tethered rigid-body diffusion and tumbling (per body axis) |
| `rotation_matrix(rotvec)` | Rodrigues, batched |
| `anm(nodes, cutoff, modes, bonded)`, `residue_nodes`, `sequence_pairs` | Anisotropic network model with stiffer sequence-neighbour springs |
| `atom_shapes(X, vec, nodes, node_of, pairs, rigid)` | Per-atom mode shapes blended along the chain, so bonds keep their lengths to first order |
| `mode_scale`, `mode_amplitudes`, `node_rmsf` | Calibrate to a mean RMSF; Langevin amplitudes (variance ∝ 1/λ, τ ∝ 1/λ) |
| `chi_topology`, `apply_chi`, `burial` | Side-chain χ1/χ2 turns about bonds (the numpy twin of `groups.dynamics`) |
| `wlc_bend(wavelengths, persistence)`, `wlc_twist(length, persistence)` | Worm-like-chain bending bands and twist: RMS and relaxation time |

`membrane.lipid_handles(mem, rng, protein_xyz)` gives each lipid atom its pivots, weights, seed and mobility for `groups.lipid_motion`. `particles.brownian` diffuses ions in reflecting boxes on the clock.

### `molanim.timeline` and `molanim.color`

| Function | Use |
| --- | --- |
| `smoothstep`, `smootherstep`, `ramp(frame, a, b)` | Easing and beat ramps |
| `camera_path(keys, points, frames)` | Keys (frame, aim, distance, azimuth, elevation, lens) → per-frame camera, with log-distance dives |
| `orbit_path(aim, distance, elevation, lens, frames)` | A constant-speed orbit that closes exactly (loops) |
| `keyed(keys, points, frames)` | Generic eased keys with named points |
| `project(p, loc, aim, lens, res)` | 3D → pixel, for label anchors |
| `fstop_for(ratio, lens, distance)` | Depth of field as a fraction of the focus distance |
| `color.srgb`, `lin`, `shade(rng, ramp, n)`, `tile`, `hex_rgb` | Exact sRGB → linear; per-atom tone variation |

## Blender layer (`molanim.blender`)

| Module | Function | Use |
| --- | --- | --- |
| `scene` | `reset_scene(name, prefix)` | Idempotent rebuild: removes the previous build and only that prefix's orphans |
| | `save_scene(scene, path)` | Write only this scene and its dependencies |
| | `collection`, `empty`, `keys`, `set_linear`, `fcurves`, `look_at`, `sun`, `show` | Building blocks; empties double as animated controllers |
| | `cycles_settings(scene, res, frames, fps, samples)` | Studio defaults: GPU, adaptive sampling, denoised, Standard view |
| `nodes` | `G`, `new_group`, `set_modifier_inputs`, `add_nodes_modifier` | A compact geometry-node builder; modifier inputs by socket name (5.x API) |
| `groups` | `breath(prefix, ..., loop_frames)` | Coherent sway plus jitter; exactly periodic when `loop_frames` is set |
| | `molecule(prefix, breath, ...)` | Spheres for context, ball-and-stick for roles, a camera-aimed cutaway funnel, a section slab, reveal groups, glow, optional per-residue offsets |
| | `spheres`, `frame_spheres` | Plain or frame-indexed sphere clouds (lipids, ions) |
| | `wave_packets` | Photons as a symbol |
| | `tube` | A cavity or pathway tube from measured and illustrative radii |
| | `dotted_link` | An interaction marker between two atoms |
| | `dynamics(prefix, modes_table, frames, n_modes, chi_table, n_res)` | Normal modes and side-chain turns read from frame tables (numpy knows every atom's position) |
| | `lipid_motion(prefix, clock, motion)` | Lipids as molecules: spin, wobble, bob, rattle and a shared flow; bending chains; swinging choline |
| | `chain_motion(prefix, clock, bend, twist)` | A double helix that bends and twists along its arc length as a worm-like chain |
| | `thermal(prefix, ...)` | Per-atom noise (version 2; kept for old scripts, not for new films) |
| `mesh` | `points_mesh`, `frame_tracks`, `table`, `absolute_keys` | Attribute-carrying point meshes; per-frame tracks; lookup tables for geometry nodes; morphs as shape keys |
| `look` | `attr_material`, `flat_material`, `glow_material`, `ghost_material`, `gradient_world`, `bloom` | Materials, the studio backdrop (the camera sees a gradient, objects see the ambient), bloom |
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
- `tools/mcp_smoke_test.py` is a minimal scene for checking a Blender MCP connection.
- `tools/blender_mcp_launch.py` is the Windows stdin fix for the Blender MCP server (`docs/setup.md`).
- `pipeline.py` discovers `examples/*/shots.json` and `projects/*/shots.json` and wraps all of the above (`docs/workflow.md`).

## Extending the framework

Add a function to `molanim` when a second shot needs it. Keep science pure-numpy with a unit test, keep Blender code thin, and document it in this file. A change that alters existing behaviour must keep `python pipeline.py check channelrhodopsin` passing, or come with a re-rendered, re-verified case study.
