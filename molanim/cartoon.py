"""Cartoons: protein ribbons and nucleic-acid ladders as plain mesh arrays.

Proteins are drawn the way Jane Richardson drew them: a smooth backbone through the Calpha atoms, flat ribbons
for alpha-helices, arrows for beta-strands and thin tubes for everything else. Secondary structure comes from the
deposited annotation (_struct_conf, _struct_sheet_range) or, for models without one, from Calpha geometry. The
ribbon's width follows the peptide carbonyls (C=O), so helix ribbons face outward from the helix axis and strand
arrows lie in the plane of their sheet.

Nucleic acids are drawn as ladders: one tube per strand through the phosphorus atoms, and each base as a slab
cut from its own ring atoms (so stacking, pairing and tilt are the measured ones), joined to the backbone by a rod.

Pure numpy; coordinates in Angstrom. Every builder returns (vertices (n, 3), faces [list of index tuples],
attributes {name: (n,) or (n, 3) array}) for molanim.blender.mesh.surface_mesh().
"""
import numpy as np

from . import structure as St

HELIX, STRAND, COIL = 'H', 'E', 'C'
SS_CODE = {HELIX: 0.0, STRAND: 1.0, COIL: 2.0}

# Cross-sections (half-width, half-thickness, superellipse exponent) in Angstrom.
HELIX_SECTION = (1.15, 0.24, 4.0)
STRAND_SECTION = (0.95, 0.24, 4.0)
ARROW_HALF_WIDTH = 1.55
COIL_SECTION = (0.3, 0.3, 2.0)
SIDES = 12

NUCLEOTIDES = {'DA': 'A', 'DC': 'C', 'DG': 'G', 'DT': 'T', 'DU': 'U', 'A': 'A', 'C': 'C', 'G': 'G', 'U': 'U'}
PURINE_RING = ['N9', 'C8', 'N7', 'C5', 'C6', 'N1', 'C2', 'N3', 'C4']
PYRIMIDINE_RING = ['N1', 'C2', 'N3', 'C4', 'C5', 'C6']
BASE_CODE = {'A': 0.0, 'C': 1.0, 'G': 2.0, 'T': 3.0, 'U': 4.0}


# ----------------------------------------------------------------------------- secondary structure

def secondary_structure(lines, table):
    """Per-atom code H / E / C from the deposited annotation: helices from _struct_conf rows whose conf_type_id
    starts with HELX, strands from _struct_sheet_range. Residues are matched by author chain and number, as in
    read_mmcif(). Returns an array of one-letter codes, COIL where nothing is annotated."""
    ss = np.full(len(table['name']), COIL, dtype='<U1')
    ranges = [(row, HELIX) for row in St.loop(lines, '_struct_conf') if row.get('conf_type_id', '').startswith('HELX')]
    ranges += [(row, STRAND) for row in St.loop(lines, '_struct_sheet_range')]
    for row, code in ranges:
        try:
            chain, lo, hi = row['beg_auth_asym_id'], int(row['beg_auth_seq_id']), int(row['end_auth_seq_id'])
        except (KeyError, ValueError):
            continue
        sel = (table['chain'] == chain) & (table['resi'] >= lo) & (table['resi'] <= hi)
        ss[sel] = code
    return ss


def estimate_secondary_structure(ca, min_helix=4, min_strand=3, partners=None):
    """H / E / C per residue of one chain from Calpha positions alone (for predicted models without an
    annotation). A residue starts an alpha-helical turn when its Calpha(i, i+3) distance is 4.2-5.9 A and
    Calpha(i, i+4) is 5.3-6.9 A (ideal: 5.0 and 6.2); two consecutive turns make a helix. A residue is in a
    strand when it is extended (Calpha(i-1, i+1) above 6.0 A; ideal 6.4-7.0) and paired: an extended Calpha of
    another stretch lies 4.2-5.6 A away, as across a sheet (4.4-5.5 A). `partners` (m, 3) adds Calpha positions of other chains to pair with. Runs
    shorter than the minimum lengths stay coil."""
    ca = np.asarray(ca, float)
    n = len(ca)
    ss = np.full(n, COIL, dtype='<U1')
    d = lambda k: np.r_[np.linalg.norm(ca[k:] - ca[:-k], axis=1), np.full(k, np.nan)] if n > k else np.full(n, np.nan)
    d3, d4 = d(3), d(4)
    turn = (d3 > 4.2) & (d3 < 5.9) & (d4 > 5.3) & (d4 < 6.9)
    helix = np.zeros(n, bool)
    for i in np.nonzero(turn[:-1] & turn[1:])[0]:          # two consecutive turns: a single tight turn is a loop
        helix[i:i + 6] = True
    d2 = np.r_[np.nan, np.linalg.norm(ca[2:] - ca[:-2], axis=1), np.nan] if n > 2 else np.full(n, np.nan)
    ext = (d2 > 6.0) & ~helix
    paired = np.zeros(n, bool)
    if ext.any():
        i, j = St.close_pairs(ca, 5.6)
        dist = np.linalg.norm(ca[i] - ca[j], axis=1)
        ok = (np.abs(i - j) > 2) & (dist > 4.2) & ext[i] & ext[j]
        paired[i[ok]] = paired[j[ok]] = True
        if partners is not None and len(partners):
            allp = np.vstack([ca, partners])
            i, j = St.close_pairs(allp, 5.6)
            cross = (i < n) != (j < n)
            a, b = np.where(i < n, i, j)[cross], np.where(i < n, j, i)[cross]
            dist = np.linalg.norm(allp[a] - allp[b], axis=1)
            paired[a[(dist > 4.2) & ext[a]]] = True
    extended = ext & paired
    for mask, code, length in ((helix, HELIX, min_helix), (extended, STRAND, min_strand)):
        i = 0
        while i < n:
            if mask[i]:
                j = i
                while j < n and mask[j]:
                    j += 1
                if j - i >= length:
                    ss[i:j] = code
                i = j
            else:
                i += 1
    return ss


# ----------------------------------------------------------------------------- backbone

def protein_segments(table, ss=None, gap=4.3, min_residues=2):
    """Continuous Calpha traces of a protein atom table: [{chain, resi, ca, o, c, ss, atoms}], split at chain
    breaks (Calpha-Calpha above `gap` A); traces shorter than `min_residues` are dropped. `ss` is a per-atom code
    array (default: estimated from Calpha geometry, strands paired across all segments). `atoms` holds the index
    of each residue's Calpha in the table."""
    names = table['name']
    out = []
    for chain in dict.fromkeys(table['chain'].tolist()):
        on = table['chain'] == chain
        res = []
        for r in dict.fromkeys(table['resi'][on].tolist()):
            sel = on & (table['resi'] == r)
            idx = {nm: int(k) for k, nm in zip(np.nonzero(sel)[0], names[sel])}
            if 'CA' in idx and 'O' in idx and 'C' in idx:
                res.append((r, idx))
        if len(res) < 2:
            continue
        start = 0
        for k in range(1, len(res) + 1):
            if k == len(res) or np.linalg.norm(table['xyz'][res[k][1]['CA']] - table['xyz'][res[k - 1][1]['CA']]) > gap:
                part = res[start:k]
                if len(part) >= max(2, min_residues):
                    ca_idx = np.array([p[1]['CA'] for p in part])
                    seg = {'chain': chain, 'resi': np.array([p[0] for p in part]), 'atoms': ca_idx,
                           'ca': table['xyz'][ca_idx], 'o': table['xyz'][[p[1]['O'] for p in part]],
                           'c': table['xyz'][[p[1]['C'] for p in part]]}
                    if ss is not None:
                        seg['ss'] = ss[ca_idx]
                    out.append(seg)
                start = k
    if ss is None:
        for seg in out:
            others = [o['ca'] for o in out if o is not seg]
            seg['ss'] = estimate_secondary_structure(seg['ca'], partners=np.vstack(others) if others else None)
    return out


def catmull_rom(points, k):
    """Uniform Catmull-Rom spline through `points`, `k` samples per span; (len - 1) * k + 1 points, passing
    through every input point. Returns (positions, span parameter as float residue index)."""
    p = np.asarray(points, float)
    if len(p) < 2:
        return p.copy(), np.zeros(len(p))
    ext = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    u = np.linspace(0, 1, k, endpoint=False)[:, None]
    out, par = [], []
    for i in range(len(p) - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        out.append(0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
        par.append(i + u[:, 0])
    out.append(p[-1:])
    par.append([len(p) - 1.0])
    return np.vstack(out), np.concatenate(par)


def _unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-9)


def _frames(path, guide):
    """Tangents and width directions along a sampled path: the guide vectors made perpendicular to the tangent."""
    t = np.gradient(path, axis=0)
    t = _unit(t)
    w = guide - (guide * t).sum(1, keepdims=True) * t
    bad = np.linalg.norm(w, axis=1) < 1e-6
    if bad.any():                                    # guide parallel to the tangent: any perpendicular will do
        alt = np.cross(t[bad], [0.0, 0.0, 1.0])
        alt[np.linalg.norm(alt, axis=1) < 1e-6] = [1.0, 0.0, 0.0]
        w[bad] = alt
    w = _unit(w)
    return t, w, np.cross(t, w)


def _profile(a, b, e, sides=SIDES):
    """Superellipse cross-section points (sides, 2) with half-axes a (width) and b (thickness)."""
    th = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    c, s = np.cos(th), np.sin(th)
    return np.stack([a * np.sign(c) * np.abs(c) ** (2 / e), b * np.sign(s) * np.abs(s) ** (2 / e)], 1)


def sweep(path, w, n, sections, caps=True):
    """Tube mesh along `path` with per-sample frames (w width, n normal) and per-sample sections (a, b, e).
    Every ring has SIDES vertices; consecutive rings are joined by quads, ends closed by triangle fans."""
    rings = []
    for p, wi, ni, (a, b, e) in zip(path, w, n, sections):
        prof = _profile(a, b, e)
        rings.append(p + prof[:, :1] * wi + prof[:, 1:] * ni)
    verts = np.vstack(rings)
    faces = []
    m = SIDES
    for r in range(len(rings) - 1):
        base, nxt = r * m, (r + 1) * m
        for s in range(m):
            faces.append((base + s, base + (s + 1) % m, nxt + (s + 1) % m, nxt + s))
    if caps:
        start = len(verts)
        verts = np.vstack([verts, path[0], path[-1]])
        last = (len(rings) - 1) * m
        for s in range(m):
            faces.append((start, (s + 1) % m, s))
            faces.append((start + 1, last + s, last + (s + 1) % m))
    return verts, faces


def ribbon(segment, k=8):
    """Cartoon of one Calpha segment (protein_segments()): helix ribbons, strand arrows (the arrowhead on each
    strand's last residue), coil tubes. Strand Calpha positions are smoothed (1/4, 1/2, 1/4) to take out the
    pleat. Attributes per vertex: 'u' (position along the segment, 0-1), 'res' (residue index in the segment),
    'ss' (0 helix, 1 strand, 2 coil)."""
    ca, ss = segment['ca'].astype(float), segment['ss']
    n = len(ca)
    pts = ca.copy()
    strand = ss == STRAND
    for i in range(1, n - 1):
        if strand[i]:
            pts[i] = 0.25 * ca[i - 1] + 0.5 * ca[i] + 0.25 * ca[i + 1]
    # Width guide: the carbonyl direction of each peptide, flipped to agree with its predecessor.
    guide = _unit(segment['o'] - segment['c'])
    for i in range(1, n):
        if guide[i] @ guide[i - 1] < 0:
            guide[i] = -guide[i]
    path, par = catmull_rom(pts, k)
    g = np.array([guide[min(int(np.floor(x)), n - 1)] * (1 - (x - np.floor(x))) +
                  guide[min(int(np.floor(x)) + 1, n - 1)] * (x - np.floor(x)) for x in par])
    t, w, nrm = _frames(path, g)

    def base_section(code):
        return {HELIX: HELIX_SECTION, STRAND: STRAND_SECTION}.get(code, COIL_SECTION)

    # Strand ends (arrowheads): the last residue of every strand run.
    ends = [i for i in range(n) if strand[i] and (i == n - 1 or not strand[i + 1])]
    sections, keep_path, keep_w, keep_n, keep_par = [], [], [], [], []
    for j, x in enumerate(par):
        f = x - np.floor(x)
        lo, hi = int(np.floor(x)), min(int(np.floor(x)) + 1, n - 1)
        # After an arrowhead's point the next span grows out of a tube, not out of a strand.
        sa = np.array(COIL_SECTION if lo in ends else base_section(ss[lo]))
        sb = np.array(base_section(ss[hi]))
        # Ease between residues: sections change over the middle half of each span.
        u = np.clip((f - 0.25) / 0.5, 0, 1)
        u = u * u * (3 - 2 * u)
        sec = sa * (1 - u) + sb * u
        end = next((e for e in ends if e - 1 <= x <= e), None)
        if end is not None and end - 1 < x <= end:
            # Arrowhead over the strand's last residue: full width at its start, a point at its end.
            frac = x - (end - 1)
            sec = np.array([ARROW_HALF_WIDTH * (1 - frac) + 0.05 * frac, STRAND_SECTION[1], STRAND_SECTION[2]])
            if keep_par and keep_par[-1] <= end - 1 < x:
                # Step out to the arrow's full width at its base: a second ring at the base position.
                keep_path.append(path[j - 1]); keep_w.append(w[j - 1]); keep_n.append(nrm[j - 1])
                keep_par.append(par[j - 1])
                sections.append((ARROW_HALF_WIDTH, STRAND_SECTION[1], STRAND_SECTION[2]))
        sections.append(tuple(sec))
        keep_path.append(path[j]); keep_w.append(w[j]); keep_n.append(nrm[j]); keep_par.append(x)
    verts, faces = sweep(np.array(keep_path), np.array(keep_w), np.array(keep_n), sections)
    rpar = np.r_[np.repeat(keep_par, SIDES), keep_par[0], keep_par[-1]]
    code = np.array([SS_CODE[s] for s in ss])
    attrs = {'u': rpar / max(n - 1, 1), 'res': rpar,
             'ss': code[np.clip(np.floor(rpar + 0.5).astype(int), 0, n - 1)]}
    return verts, faces, attrs


def combine(parts):
    """Join several (verts, faces, attrs) into one, offsetting face indices. Attribute sets must match."""
    verts, faces, attrs, off = [], [], {}, 0
    for v, f, a in parts:
        verts.append(v)
        faces += [tuple(i + off for i in face) for face in f]
        for key, val in a.items():
            attrs.setdefault(key, []).append(np.asarray(val))
        off += len(v)
    if not verts:
        return np.zeros((0, 3)), [], {}
    return np.vstack(verts), faces, {k: np.concatenate(v) for k, v in attrs.items()}


def cartoon(table, ss=None, k=8, per_atom=None, min_residues=2):
    """Ribbons for every protein segment of `table`, joined. `per_atom` = {name: per-atom array} adds attributes
    sampled at each vertex's residue Calpha (e.g. a chain colour or pLDDT); 'ring' numbers the cross-sections.
    Also returns the segments."""
    segs = protein_segments(table, ss, min_residues=min_residues)
    parts = []
    for s_i, seg in enumerate(segs):
        v, f, a = ribbon(seg, k)
        a['segment'] = np.full(len(v), float(s_i))
        res = np.clip(np.floor(a['res'] + 0.5).astype(int), 0, len(seg['atoms']) - 1)
        for name, values in (per_atom or {}).items():
            a[name] = np.asarray(values)[seg['atoms'][res]]
        parts.append((v, f, a))
    v, f, a = combine(parts)
    # Cross-section of each vertex (rings share a segment and a path parameter): for cuts that remove whole
    # sections (molanim.blender.groups.section(group='ring')).
    _, a['ring'] = np.unique(np.stack([a['segment'], np.round(a['res'], 5)], 1), axis=0, return_inverse=True)
    a['ring'] = a['ring'].ravel().astype(np.int32)
    return v, f, a, segs


def sticks(xyz, edges, radius=0.16, sides_per_bond=2):
    """Bonds as cylinders split at their middle, each half tagged with its atom ('atom' attribute), so a
    ball-and-stick model can colour each half like the atom it belongs to."""
    xyz = np.asarray(xyz, float)
    parts = []
    for i, j in np.asarray(edges, int).reshape(-1, 2):
        mid = (xyz[i] + xyz[j]) / 2
        for a, b, atom in ((xyz[i], mid, i), (mid, xyz[j], j)):
            path = np.linspace(a, b, sides_per_bond)
            _, w, nrm = _frames(path, np.tile(np.cross(b - a, [0.3, 0.5, 0.8]), (len(path), 1)))
            v, f = sweep(path, w, nrm, [(radius, radius, 2.0)] * len(path))
            parts.append((v, f, {'atom': np.full(len(v), float(atom))}))
    v, f, a = combine(parts)
    return v, f, a


# ----------------------------------------------------------------------------- nucleic acids

def plane(xyz):
    """Best-fit plane of points: (centroid, unit normal, RMS distance from the plane)."""
    xyz = np.asarray(xyz, float)
    c = xyz.mean(0)
    _, s, vt = np.linalg.svd(xyz - c)
    nrm = vt[2]
    return c, nrm, float(np.sqrt(np.mean(((xyz - c) @ nrm) ** 2)))


def nucleotides(table):
    """[{chain, resi, base (A/C/G/T/U), ring (atom indices), c1, c4, p (or None)}] of every nucleotide with a
    complete base ring, in chain order."""
    out = []
    names = table['name']
    for chain in dict.fromkeys(table['chain'].tolist()):
        on = table['chain'] == chain
        for r in dict.fromkeys(table['resi'][on].tolist()):
            sel = on & (table['resi'] == r)
            resn = table['resn'][sel][0]
            base = NUCLEOTIDES.get(resn)
            if base is None:
                continue
            idx = {nm: int(k) for k, nm in zip(np.nonzero(sel)[0], names[sel])}
            ring = PURINE_RING if base in 'AG' else PYRIMIDINE_RING
            if not all(a in idx for a in ring) or "C1'" not in idx or "C4'" not in idx:
                continue
            out.append({'chain': chain, 'resi': r, 'base': base, 'ring': np.array([idx[a] for a in ring]),
                        'c1': idx["C1'"], 'c4': idx["C4'"], 'p': idx.get('P')})
    return out


def _slab(xyz, ring, half):
    """A flat slab: the base ring's outline (atoms ordered round their centroid in the best-fit plane), pushed
    out by 0.45 A for the atoms' own size, extruded +-`half` along the plane normal."""
    pts = xyz[ring]
    c, nrm, _ = plane(pts)
    e1 = _unit(pts[0] - c - ((pts[0] - c) @ nrm) * nrm)
    e2 = np.cross(nrm, e1)
    loc = np.stack([(pts - c) @ e1, (pts - c) @ e2], 1)
    order = np.argsort(np.arctan2(loc[:, 1], loc[:, 0]))
    loc = loc[order]
    loc = loc + _unit(np.c_[loc, np.zeros(len(loc))])[:, :2] * 0.45
    outline = c + loc[:, :1] * e1 + loc[:, 1:] * e2
    m = len(outline)
    verts = np.vstack([outline + nrm * half, outline - nrm * half, c + nrm * half, c - nrm * half])
    faces = []
    for s in range(m):
        t = (s + 1) % m
        faces.append((s, t, m + t, m + s))                      # rim
        faces.append((2 * m, t, s))                             # top fan
        faces.append((2 * m + 1, m + s, m + t))                 # bottom fan
    return verts, faces


SUGAR_RING = ["C1'", "C2'", "C3'", "C4'", "O4'"]
# A purine's two fused rings, each in ring order (the shared C4-C5 edge appears in both).
PURINE_RINGS = [['N9', 'C8', 'N7', 'C5', 'C4'], ['N1', 'C2', 'N3', 'C4', 'C5', 'C6']]
PYRIMIDINE_RINGS = [['N1', 'C2', 'N3', 'C4', 'C5', 'C6']]


def _fill(xyz, ring, half):
    """A ring filled as a thin plate: the ring atoms in ring order, fanned from their centroid, offset +-`half`
    along the best-fit normal. Works for puckered rings (a furanose) as well as flat ones."""
    pts = xyz[ring]
    c, nrm, _ = plane(pts)
    m = len(pts)
    verts = np.vstack([pts + nrm * half, pts - nrm * half, c + nrm * half, c - nrm * half])
    faces = []
    for s in range(m):
        t = (s + 1) % m
        faces.append((2 * m, s, t))
        faces.append((2 * m + 1, m + t, m + s))
        faces.append((s, m + s, m + t, t))
    return verts, faces


def ring_fills(table, half=0.12):
    """Nucleic acids as a chemist draws them, with filled rings: every nucleotide's sugar ring and base ring(s)
    as thin plates (the 'fill' style of molecular viewers), to sit over a stick model of all its atoms. A
    purine gives two fused plates. Attributes: 'part' (0 sugar, 1 base), 'base' (A0 C1 G2 T3 U4), 'nt' (index
    in nucleotides()), 'plate' (index of the plate). Rings with a missing atom are skipped."""
    xyz, names = table['xyz'], table['name']
    parts = []
    for n_i, n in enumerate(nucleotides(table)):
        sel = (table['chain'] == n['chain']) & (table['resi'] == n['resi'])
        idx = {nm: int(k) for k, nm in zip(np.nonzero(sel)[0], names[sel])}
        rings = [(0.0, SUGAR_RING)] + [(1.0, r) for r in (PURINE_RINGS if n['base'] in 'AG' else PYRIMIDINE_RINGS)]
        for part, ring in rings:
            if not all(a in idx for a in ring):
                continue
            v, f = _fill(xyz, np.array([idx[a] for a in ring]), half)
            parts.append((v, f, {'part': np.full(len(v), part), 'base': np.full(len(v), BASE_CODE[n['base']]),
                                 'nt': np.full(len(v), float(n_i)), 'plate': np.full(len(v), float(len(parts)))}))
    v, f, a = combine(parts)
    return v, f, a


def ladder(table, k=8, tube=0.95, rod=0.32, slab=0.5):
    """Nucleic-acid ladder: per strand a tube through the P atoms (C4' where a residue has no P), each base as a
    slab from its ring atoms, and a rod from the backbone (C4') through C1' to the base's glycosidic N. Attributes:
    'part' (0 backbone, 1 rod, 2 base), 'base' (A0 C1 G2 T3 U4, -1 on the backbone), 'u' (along the strand),
    'strand' (strand index), 'nt' (nucleotide index in nucleotides())."""
    xyz = table['xyz']
    nts = nucleotides(table)
    parts = []
    for s_i, chain in enumerate(dict.fromkeys(n['chain'] for n in nts)):
        strand = [(i, n) for i, n in enumerate(nts) if n['chain'] == chain]
        pts = np.array([xyz[n['p'] if n['p'] is not None else n['c4']] for _, n in strand])
        if len(pts) >= 2:
            path, par = catmull_rom(pts, k)
            # Width guide for a round tube does not matter; use the direction to the base centroid.
            cen = np.array([xyz[n['ring']].mean(0) for _, n in strand])
            g = np.array([cen[min(int(round(x)), len(cen) - 1)] for x in par]) - path
            _, w, nrm = _frames(path, g)
            v, f = sweep(path, w, nrm, [(tube, tube, 2.0)] * len(path))
            rp = np.r_[np.repeat(par, SIDES), par[0], par[-1]]
            nt_idx = np.array([i for i, _ in strand])[np.clip(np.round(rp).astype(int), 0, len(strand) - 1)]
            parts.append((v, f, {'part': np.zeros(len(v)), 'base': np.full(len(v), -1.0),
                                 'u': rp / max(len(strand) - 1, 1), 'strand': np.full(len(v), float(s_i)),
                                 'nt': nt_idx.astype(float)}))
        for j, (i, n) in enumerate(strand):
            glyco = n['ring'][0]                                 # N9 of a purine, N1 of a pyrimidine
            rod_pts = np.array([xyz[n['c4']], xyz[n['c1']], xyz[glyco]])
            path, _ = catmull_rom(rod_pts, 3)
            _, w, nrm = _frames(path, np.tile([0.0, 0.0, 1.0], (len(path), 1)))
            v, f = sweep(path, w, nrm, [(rod, rod, 2.0)] * len(path))
            u = j / max(len(strand) - 1, 1)
            common = {'u': np.full(len(v), u), 'strand': np.full(len(v), float(s_i)), 'nt': np.full(len(v), float(i))}
            parts.append((v, f, {'part': np.ones(len(v)), 'base': np.full(len(v), BASE_CODE[n['base']]), **common}))
            v, f = _slab(xyz, n['ring'], slab)
            common = {'u': np.full(len(v), u), 'strand': np.full(len(v), float(s_i)), 'nt': np.full(len(v), float(i))}
            parts.append((v, f, {'part': np.full(len(v), 2.0), 'base': np.full(len(v), BASE_CODE[n['base']]), **common}))
    v, f, a = combine(parts)
    return v, f, a, nts
