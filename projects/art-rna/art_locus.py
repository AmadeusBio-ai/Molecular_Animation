"""Science for the ART film: the phage SA1 array locus, B-DNA built from its sequence, and the AlphaFold 3 models.

Pure numpy (tests: tests/test_art_rna.py). Numbers this module produces are quoted in record.md.

Sequence: GenBank MW218148.1 (Staphylococcus phage SA1), positions 9421-13020, as archived in the AF3 job
package (sources/af3-job-package/provenance). The repeat array sits in the non-coding tract 9448-10646, upstream
of the reverse transcriptase CDS (QPI16926.1, 10647-12152) and its downstream partner CDS (QPI16927.1,
12154-12951). Repeat boundaries here are our own sequence comparison, not the authors' annotation.

DNA geometry: base pairs of the B-DNA dodecamer 1BNA as templates, stacked with an ideal B-DNA step (36.0 deg,
3.38 A) about the screw axis fitted to 1BNA, then bent onto a smooth path. The path is illustrative.
"""
import json
import math
import re
from pathlib import Path

import numpy as np

from molanim import structure as St

HERE = Path(__file__).resolve().parent
EXCERPT = HERE / 'sources' / 'af3-job-package' / 'provenance' / 'sa1_genomic_excerpt_9421_13020.txt'
AF3 = HERE / 'af3'

CORE = 'ATATGAATACGTAT'                 # the 14-nt seed recurring in the tract (job package manifest)
TRACT = (9448, 10646)                   # non-coding tract upstream of the RT, 1-based inclusive
RT_CDS, PARTNER_CDS = (10647, 12152), (12154, 12951)
RT_LENGTH, PARTNER_LENGTH = 501, 265
YADD = (366, 369)                       # the RT's YADD motif (sequence annotation in the job package)
WINDOWS = {'W1': (9598, 9809), 'W2': (9810, 9980), 'W3': (9981, 10181), 'W4': (10182, 10357)}   # RNA inputs
JOBS = {
    'RT': 'art_sa1_01_rt_qpi16926_s101', 'PARTNER': 'art_sa1_02_partner_qpi16927_s101',
    'W1': 'art_sa1_04_expl_rna_w1_9598_9809_s101', 'W2': 'art_sa1_05_expl_rna_w2_9810_9980_s101',
    'W3': 'art_sa1_06_expl_rna_w3_9981_10181_s101', 'W4': 'art_sa1_07_expl_rna_w4_10182_10357_s101',
    'RT_PARTNER': ['art_sa1_03_hyp_rt_partner_1to1_s101', 'art_sa1_03_hyp_rt_partner_1to1_s202',
                   'art_sa1_03_hyp_rt_partner_1to1_s303'],
}
COMPLEX_PREFIXES = ('art_sa1_03_', 'art_sa1_08_', 'art_sa1_09_', 'art_sa1_10_', 'art_sa1_11_', 'art_sa1_12_',
                    'art_sa1_13_', 'art_sa1_14_', 'art_sa1_15_', 'art_sa1_16_', 'art_sa1_17_', 'art_sa1_18_',
                    'art_sa1_19_')

TWIST, RISE = 36.0, 3.38                # ideal B-DNA step (deg, A)
BACKBONE_NA = {'P', 'OP1', 'OP2', 'OP3', "O5'", "C5'", "C4'", "O4'", "C3'", "O3'", "C2'", "C1'", "O2'"}
COMP = str.maketrans('ACGT', 'TGCA')


# ----------------------------------------------------------------------------- the locus

def genome(path=EXCERPT):
    """(sequence, first position): the excerpt's numbered GenBank lines joined, upper case."""
    seq, first = [], None
    for line in Path(path).read_text().splitlines():
        m = re.match(r'\s*(\d+)\s+([acgtn ]+)$', line, re.I)
        if m:
            first = first or int(m.group(1))
            seq.append(m.group(2).replace(' ', ''))
    return ''.join(seq).upper(), first


def sub(seq, first, a, b):
    """Positions a..b (1-based, inclusive) of a sequence that starts at position `first`."""
    return seq[a - first:b - first + 1]


def motif_hits(seq, first, motif=CORE, span=TRACT, max_mismatch=1):
    """Starts (1-based) and mismatch counts of near matches of `motif` on the + strand within `span`.
    The reverse complement is searched too and returned separately (none expected)."""
    out = {'+': [], '-': []}
    for strand, m in (('+', motif), ('-', motif.translate(COMP)[::-1])):
        for p in range(span[0], span[1] - len(m) + 2):
            d = sum(x != y for x, y in zip(sub(seq, first, p, p + len(m) - 1), m))
            if d <= max_mismatch:
                out[strand].append((p, d))
    return out


def repeat_copies(seq, first, starts, reach=60):
    """The repeat element around each core start, by comparison of the copies.

    The reference trio is the three copies that agree best over +-`reach` nt. The element runs outward from the
    core while the trio agrees, bridging single disagreements (no two in a row). Each copy's nucleotides that
    match the five-copy consensus are its 'lit' positions. Returns a dict with the window (offsets from the core
    start), the consensus, per-copy (start, end, identity, lit positions) and the trio."""
    starts = list(starts)
    offs = np.arange(-reach, reach + len(CORE))
    cols = np.array([[sub(seq, first, p + o, p + o) for o in offs] for p in starts])
    best, trio = -1, None
    for i in range(len(starts)):
        for j in range(i + 1, len(starts)):
            for k in range(j + 1, len(starts)):
                score = int(((cols[i] == cols[j]) & (cols[j] == cols[k])).sum())
                if score > best:
                    best, trio = score, (i, j, k)
    agree = (cols[trio[0]] == cols[trio[1]]) & (cols[trio[1]] == cols[trio[2]])
    core = np.nonzero((offs >= 0) & (offs < len(CORE)))[0]
    lo, hi = core[0], core[-1]
    while lo > 0 and (agree[lo - 1] or (lo > 1 and agree[lo - 2])):
        lo -= 1
    while not agree[lo]:
        lo += 1
    while hi < len(offs) - 1 and (agree[hi + 1] or (hi < len(offs) - 2 and agree[hi + 2])):
        hi += 1
    while not agree[hi]:
        hi -= 1
    window = (int(offs[lo]), int(offs[hi]))
    consensus = []
    for c in range(lo, hi + 1):
        votes = {b: int((cols[:, c] == b).sum()) for b in 'ACGT'}
        top = max(votes.values())
        tied = [b for b in 'ACGT' if votes[b] == top]
        consensus.append(cols[trio[0], c] if cols[trio[0], c] in tied else tied[0])
    consensus = ''.join(consensus)
    copies = []
    for row, p in enumerate(starts):
        seg = ''.join(cols[row, lo:hi + 1])
        lit = [p + window[0] + k for k, (x, y) in enumerate(zip(seg, consensus)) if x == y]
        copies.append({'core': p, 'start': p + window[0], 'end': p + window[1], 'seq': seg,
                       'identity': round(len(lit) / len(consensus), 3), 'lit': lit})
    return {'window': window, 'length': len(consensus), 'consensus': consensus, 'copies': copies,
            'trio': [starts[t] for t in trio]}


def locus():
    """Everything the film needs about the locus, with the checks that back it."""
    seq, first = genome()
    hits = motif_hits(seq, first)
    starts = [p for p, _ in hits['+']]
    rep = repeat_copies(seq, first, starts)
    spacers = [b['start'] - a['end'] - 1 for a, b in zip(rep['copies'], rep['copies'][1:])]
    periods = [b - a for a, b in zip(starts, starts[1:])]
    at = sum(sub(seq, first, *TRACT).count(b) for b in 'AT') / (TRACT[1] - TRACT[0] + 1)
    return {'seq': seq, 'first': first, 'hits': hits, 'starts': starts, 'repeats': rep, 'spacers': spacers,
            'periods': periods, 'tract_at': round(at, 3),
            'rt_start_codon': sub(seq, first, RT_CDS[0], RT_CDS[0] + 2),
            'partner_start_codon': sub(seq, first, PARTNER_CDS[0], PARTNER_CDS[0] + 2)}


# ----------------------------------------------------------------------------- B-DNA from sequence

def _residues(table, chain):
    out = {}
    for k in np.nonzero(table['chain'] == chain)[0]:
        out.setdefault(int(table['resi'][k]), {'resn': table['resn'][k], 'atoms': {}})
        out[int(table['resi'][k])]['atoms'][table['name'][k]] = (table['element'][k], table['xyz'][k])
    return out


def bp_frame(r1, r2):
    """4x4 base-pair frame: origin at the C1'-C1' midpoint, y from strand-2 C1' to strand-1 C1' (in the base
    plane), x toward the base atoms (major-groove side), z = x cross y."""
    c1, c2 = r1["C1'"][1], r2["C1'"][1]
    base = np.array([v[1] for r in (r1, r2) for n, v in r.items() if n not in BACKBONE_NA])
    mid = (c1 + c2) / 2
    nrm = np.linalg.svd(base - base.mean(0))[2][2]
    y = c1 - c2
    y -= nrm * (y @ nrm)
    y /= np.linalg.norm(y)
    x = np.cross(y, nrm)
    if x @ (base.mean(0) - mid) < 0:
        x = -x
    F = np.eye(4)
    F[:3, 0], F[:3, 1], F[:3, 2], F[:3, 3] = x, y, np.cross(x, y), mid
    return F


def _mean_rotation(Rs):
    U, _, Vt = np.linalg.svd(np.sum(Rs, axis=0))
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1
        R = U @ Vt
    return R


def _axis_angle(R):
    angle = math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2)))
    axis = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    return axis / np.linalg.norm(axis), angle


def _rotation(axis, angle):
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(angle) * K + (1 - math.cos(angle)) * K @ K


def templates(cif):
    """Base-pair templates and the helix step from the B-DNA dodecamer 1BNA (CGCGAATTCGCG, chains A and B).

    Returns (templates, step, fit): templates[b] for strand-1 base b in ACGT is (local xyz, elements, names,
    strand 0/1) in its bp frame; step is the ideal B-DNA step (TWIST, RISE) about the screw axis fitted to the
    central eight steps; fit reports the fitted twist, rise and axis offset."""
    t, _ = St.read_mmcif(cif)
    t = St.first_conformer(St.select(t, t['model'] == t['model'].min()))
    A, B = _residues(t, 'A'), _residues(t, 'B')
    pairs = [(A[i], B[25 - i]) for i in range(1, 13)]
    frames = [bp_frame(a['atoms'], b['atoms']) for a, b in pairs]
    rels = [np.linalg.inv(f0) @ f1 for f0, f1 in zip(frames[2:9], frames[3:10])]
    R = _mean_rotation([r[:3, :3] for r in rels])
    tv = np.mean([r[:3, 3] for r in rels], axis=0)
    u, ang = _axis_angle(R)
    rise_fit = float(tv @ u)
    if rise_fit < 0:
        u, ang, rise_fit = -u, -ang, -rise_fit
    point = np.linalg.lstsq(np.eye(3) - R, tv - rise_fit * u, rcond=None)[0]
    point -= u * (point @ u)
    step = np.eye(4)
    step[:3, :3] = _rotation(u, math.radians(TWIST))
    step[:3, 3] = point - step[:3, :3] @ point + RISE * u
    by_base = {}
    for k, ((a, b), F) in enumerate(zip(pairs, frames)):
        key = a['resn'][1:]                       # DA -> A
        if key in by_base and abs(k - 5.5) >= by_base[key][0]:
            continue                              # prefer the base pairs nearest the centre of the dodecamer
        inv = np.linalg.inv(F)
        xyz, el, nm, st = [], [], [], []
        for s, res in enumerate((a, b)):
            for name, (e, p) in res['atoms'].items():
                xyz.append(St.transform(p[None], inv)[0])
                el.append(e)
                nm.append(name)
                st.append(s)
        by_base[key] = (abs(k - 5.5), (np.array(xyz), np.array(el), np.array(nm), np.array(st)))
    tmpl = {k: v[1] for k, v in by_base.items()}
    fit = {'twist_deg': round(math.degrees(ang), 2), 'rise_A': round(rise_fit, 3),
           'axis_offset_A': [round(float(c), 2) for c in point], 'axis_local': [round(float(c), 3) for c in u]}
    return tmpl, step, fit


def screw_frame(step):
    """(axis direction, point on axis) of a step, in the bp frame's local coordinates."""
    u, _ = _axis_angle(step[:3, :3])
    t = step[:3, 3]
    if t @ u < 0:
        u = -u
    point = np.linalg.lstsq(np.eye(3) - step[:3, :3], t - (t @ u) * u, rcond=None)[0]
    return u, point - u * (point @ u)


def straight_helix(seq, tmpl, step):
    """B-DNA for `seq` (strand 1, 5'->3') with its helix axis on +Z through the origin.

    Returns a table: xyz, element, name, bp (0-based index into seq), strand (0 = seq, 1 = complement)."""
    u, p = screw_frame(step)
    # G0 maps the local screw axis onto global Z through the origin.
    z = u
    x = np.cross([0.0, 0.0, 1.0] if abs(z[2]) < 0.9 else [1.0, 0.0, 0.0], z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    Rg = np.vstack([x, y, z])
    G = np.eye(4)
    G[:3, :3] = Rg
    G[:3, 3] = -Rg @ p
    xyz, el, nm, bp, st = [], [], [], [], []
    for k, base in enumerate(seq):
        lx, le, ln, ls = tmpl[base]
        xyz.append(St.transform(lx, G))
        el.append(le)
        nm.append(ln)
        bp.append(np.full(len(lx), k))
        st.append(ls)
        G = G @ step
    return {'xyz': np.vstack(xyz), 'element': np.concatenate(el), 'name': np.concatenate(nm),
            'bp': np.concatenate(bp), 'strand': np.concatenate(st)}


def nucleic_table(helix, seq):
    """The residue fields an atom table carries (chain, resi, resn), for straight_helix() output, so that
    molanim's bonds and nucleic-acid builders read it like a PDB file: strand 0 is chain A numbered 1..n 5'->3';
    strand 1 is chain B, also numbered 5'->3' (its O3' joins the P of the base pair before)."""
    n, bp, strand = len(seq), helix['bp'], helix['strand']
    base = np.array(list(seq))[bp]
    comp = np.array(list(''.join(base).translate(COMP)))
    return {**helix, 'chain': np.where(strand == 0, 'A', 'B'), 'resi': np.where(strand == 0, bp + 1, n - bp),
            'resn': np.char.add('D', np.where(strand == 0, base, comp))}


def o3p_links(table):
    """(O3' of nucleotide i, P of nucleotide i + 1) atom pairs along each chain of a nucleic_table()."""
    key = {(c, int(r), n): k for k, (c, r, n) in enumerate(zip(table['chain'], table['resi'], table['name']))
           if n in ("O3'", 'P')}
    return [(k, key[(c, r + 1, 'P')]) for (c, r, n), k in key.items() if n == "O3'" and (c, r + 1, 'P') in key]


def close_backbone(table, edges, links, length=1.6, iterations=200):
    """Stacked templates leave O3'(i) - P(i + 1) gaps of 1.2-2.7 A (the ideal step does not fit every template's
    backbone). Close them: bond-length projection over the sugar-phosphate atoms (bases held fixed), each bond
    kept at its template length and each link pulled to `length`. Returns new coordinates and a report."""
    xyz = np.array(table['xyz'], float)
    e = np.vstack([np.asarray(edges, int).reshape(-1, 2), np.asarray(links, int).reshape(-1, 2)])
    target = np.linalg.norm(xyz[e[:, 0]] - xyz[e[:, 1]], axis=1)
    target[len(edges):] = length
    free = np.isin(table['name'], list(BACKBONE_NA)).astype(float)
    w = free[e]                                            # moving share of each end; a base atom does not move
    share = np.where(w.sum(1) > 0, 1 / np.maximum(w.sum(1), 1e-9), 0.0)[:, None]
    start = xyz.copy()
    for _ in range(iterations):
        d = xyz[e[:, 1]] - xyz[e[:, 0]]
        r = np.linalg.norm(d, axis=1)
        corr = ((r - target) / np.maximum(r, 1e-9))[:, None] * d * share
        step = np.zeros_like(xyz)
        np.add.at(step, e[:, 0], corr * w[:, :1])
        np.add.at(step, e[:, 1], -corr * w[:, 1:])
        deg = np.bincount(e.ravel(), minlength=len(xyz))[:, None]
        xyz += 0.5 * step / np.maximum(deg, 1)
    r = np.linalg.norm(xyz[e[:, 0]] - xyz[e[:, 1]], axis=1)
    gaps0 = np.linalg.norm(start[e[len(edges):, 0]] - start[e[len(edges):, 1]], axis=1)
    return xyz, {'o3p_A_before_p0_p50_p100': [round(float(v), 2) for v in np.percentile(gaps0, [0, 50, 100])],
                 'o3p_A_after_p0_p50_p100': [round(float(v), 2) for v in np.percentile(r[len(edges):], [0, 50, 100])],
                 'bond_change_A_max': round(float(np.abs(r[:len(edges)] - target[:len(edges)]).max()), 3),
                 'atom_shift_A_p95_max': [round(float(v), 2) for v in np.percentile(np.linalg.norm(xyz - start, axis=1), [95, 100])]}


def smooth_path(points, spacing=1.0):
    """Catmull-Rom curve through `points`, resampled every `spacing` A."""
    P = np.asarray(points, float)
    T = np.zeros_like(P)
    T[1:-1] = (P[2:] - P[:-2]) / 2
    T[0], T[-1] = P[1] - P[0], P[-1] - P[-2]
    u = np.linspace(0, 1, 600, endpoint=False)[:, None]
    h00, h10, h01, h11 = 2 * u**3 - 3 * u**2 + 1, u**3 - 2 * u**2 + u, -2 * u**3 + 3 * u**2, u**3 - u**2
    dense = np.vstack([h00 * P[i] + h10 * T[i] + h01 * P[i + 1] + h11 * T[i + 1] for i in range(len(P) - 1)] + [P[-1:]])
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=1))])
    ts = np.arange(0, s[-1], spacing)
    return np.stack([np.interp(ts, s, dense[:, k]) for k in range(3)], axis=1)


def rmf(path):
    """Unit tangents and rotation-minimising normals along a polyline (double reflection)."""
    T = np.gradient(path, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    r = np.cross(T[0], [0, 0, 1] if abs(T[0][2]) < 0.9 else [1, 0, 0])
    N = [r / np.linalg.norm(r)]
    for i in range(len(path) - 1):
        v1 = path[i + 1] - path[i]
        c1 = v1 @ v1
        rL = N[i] - (2 / c1) * (v1 @ N[i]) * v1
        tL = T[i] - (2 / c1) * (v1 @ T[i]) * v1
        v2 = T[i + 1] - tL
        c2 = v2 @ v2
        N.append(rL if c2 < 1e-12 else rL - (2 / c2) * (v2 @ rL) * v2)
    N = np.array(N)
    return T, N, np.cross(T, N)


def bend(xyz, path, spacing=1.0):
    """Map a straight helix (axis +Z from the origin) onto `path` (sampled every `spacing` A): each atom keeps
    its distance along the axis and its offset in the rotation-minimising frame. Returns the bent coordinates
    and the per-sample frames (T, N, B)."""
    T, N, B = rmf(path)
    s = xyz[:, 2] / spacing
    sc = np.clip(s, 0, len(path) - 1)
    i = np.clip(np.floor(sc).astype(int), 0, len(path) - 2)
    f = (sc - i)[:, None]
    P = path[i] * (1 - f) + path[i + 1] * f
    Nn = N[i] * (1 - f) + N[i + 1] * f
    Bn = B[i] * (1 - f) + B[i + 1] * f
    Tn = T[i] * (1 - f) + T[i + 1] * f
    out = P + xyz[:, :1] * Nn + xyz[:, 1:2] * Bn
    beyond = (s - sc)[:, None] * spacing                 # straight run-out before the start and past the end
    return out + beyond * Tn, (T, N, B)


def backbone_gaps(table):
    """O3'(k) - P(k+1) distances along each strand (the links between stacked templates), in A."""
    out = []
    for s, nxt in ((0, 1), (1, -1)):
        o3 = {int(b): p for b, p, n, st in zip(table['bp'], table['xyz'], table['name'], table['strand'])
              if n == "O3'" and st == s}
        ph = {int(b): p for b, p, n, st in zip(table['bp'], table['xyz'], table['name'], table['strand'])
              if n == 'P' and st == s}
        out += [float(np.linalg.norm(o3[b] - ph[b + nxt])) for b in o3 if b + nxt in ph]
    return np.array(out)


def neighbour_strain(straight, bent, cutoff=1.9):
    """Largest change (A) of covalent-range neighbour distances caused by bending."""
    i, j = St.close_pairs(straight, cutoff)
    if len(i) == 0:
        return 0.0
    d0 = np.linalg.norm(straight[i] - straight[j], axis=1)
    d1 = np.linalg.norm(bent[i] - bent[j], axis=1)
    return float(np.abs(d1 - d0).max())


# ----------------------------------------------------------------------------- AlphaFold 3 models

def _bfactors(lines):
    i = next(n for n, line in enumerate(lines) if line.startswith('_atom_site.'))
    cols = []
    while lines[i].startswith('_atom_site.'):
        cols.append(lines[i].split('.', 1)[1].strip())
        i += 1
    c = {k: n for n, k in enumerate(cols)}
    out = []
    while i < len(lines) and lines[i].startswith(('ATOM', 'HETATM')):
        r = lines[i].split()
        if r[c['type_symbol']] not in ('H', 'D'):
            out.append(float(r[c['B_iso_or_equiv']]))
        i += 1
    return np.array(out)


def model(job, k=0):
    """Atom table of AF3 model k of `job`, with per-atom pLDDT (the B-factor column) as 'plddt'."""
    t, lines = St.read_mmcif(AF3 / job / f'fold_{job}_model_{k}.cif', skip=set())
    t['plddt'] = _bfactors(lines)
    assert len(t['plddt']) == len(t['name'])
    return t


def summary(job, k=0):
    return json.loads((AF3 / job / f'fold_{job}_summary_confidences_{k}.json').read_text())


def confidence_report():
    """Global numbers quoted on screen and in the record."""
    rep = {}
    for key in ('RT', 'PARTNER', 'W1', 'W2', 'W3', 'W4'):
        t, s = model(JOBS[key]), summary(JOBS[key])
        rep[key] = {'ptm': s['ptm'], 'mean_plddt': round(float(t['plddt'].mean()), 1),
                    'frac_plddt_70': round(float((t['plddt'] >= 70).mean()), 3)}
    iptm = [summary(p.name)['iptm'] for p in sorted(AF3.iterdir()) if p.is_dir() and p.name.startswith(COMPLEX_PREFIXES)]
    rep['complexes'] = {'jobs': len(iptm), 'iptm_max': max(iptm), 'iptm_min': min(iptm)}
    return rep


def kabsch_rmsd(P, Q):
    P, Q = P - P.mean(0), Q - Q.mean(0)
    U, _, Vt = np.linalg.svd(P.T @ Q)
    d = np.sign(np.linalg.det(U @ Vt))
    R = U @ np.diag([1, 1, d]) @ Vt
    return float(np.sqrt(((P @ R - Q) ** 2).sum(1).mean()))


def sample_spread(job, atom):
    """RMSD (A) of AF3 models 1-4 against model 0 over one atom per residue (CA or C4')."""
    ref = model(job, 0)
    P = ref['xyz'][ref['name'] == atom]
    out = []
    for k in range(1, 5):
        t = model(job, k)
        out.append(round(kabsch_rmsd(P, t['xyz'][t['name'] == atom]), 1))
    return out


def principal_frame(X):
    """Rows: principal axes of a point cloud (largest first), right-handed."""
    _, _, Vt = np.linalg.svd(X - X.mean(0), full_matrices=False)
    if np.linalg.det(Vt) < 0:
        Vt[2] *= -1
    return Vt


def rotvec_matrix(v_deg):
    """Rotation matrix of a rotation vector given in degrees."""
    v = np.radians(np.asarray(v_deg, float))
    a = np.linalg.norm(v)
    return np.eye(3) if a < 1e-12 else _rotation(v / a, a)
