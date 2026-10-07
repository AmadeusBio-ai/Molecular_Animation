"""Structures: mmCIF reading, assembly operators, matching two states atom by atom, bonds and measurements.

Pure numpy; coordinates in Angstrom. An "atom table" is a dict of equal-length numpy arrays
(chain, resi, resn, name, alt, element, occupancy, model, xyz) as returned by read_mmcif().
"""
import math

import numpy as np

VDW = {'H': 1.10, 'C': 1.70, 'N': 1.55, 'O': 1.52, 'S': 1.80, 'P': 1.80, 'SE': 1.90}
WATERS = {'HOH', 'DOD', 'WAT'}
ADDITIVES = {'SO4', 'PO4', 'GOL', 'EDO', 'PEG', 'OLC', 'OLA', 'MPD', 'ACT', 'DMS', 'TRS', 'EPE'}
IONS = {'NA', 'K', 'CL', 'MG', 'MN', 'ZN', 'CA', 'CD', 'NI', 'CO', 'IOD', 'BR'}


# ----------------------------------------------------------------------------- reading

def read_mmcif(path, skip=WATERS | ADDITIVES, hydrogens=False, model=None):
    """Atom rows of an mmCIF file (every alt-loc kept) as an atom table, plus the file's lines.

    `skip` drops residues by name (default: waters and common crystallisation additives); hydrogens and
    deuteriums are dropped unless `hydrogens`. `model` keeps one model number (default: all rows)."""
    with open(path) as fh:
        lines = fh.read().splitlines()
    i = next(n for n, line in enumerate(lines) if line.startswith('_atom_site.'))
    cols = []
    while lines[i].startswith('_atom_site.'):
        cols.append(lines[i].split('.', 1)[1].strip())
        i += 1
    c = {k: n for n, k in enumerate(cols)}
    out = {k: [] for k in ('chain', 'resi', 'resn', 'name', 'alt', 'element', 'occupancy', 'model', 'xyz')}
    while i < len(lines) and lines[i].startswith(('ATOM', 'HETATM')):
        r = lines[i].split()
        i += 1
        if (not hydrogens and r[c['type_symbol']] in ('H', 'D')) or r[c['label_comp_id']] in skip:
            continue
        if model is not None and r[c['pdbx_PDB_model_num']] != str(model):
            continue
        out['chain'].append(r[c['auth_asym_id']])
        out['resi'].append(int(r[c['auth_seq_id']]))
        out['resn'].append(r[c['label_comp_id']])
        out['name'].append(r[c['label_atom_id']].strip('"'))
        out['alt'].append(r[c['label_alt_id']])
        out['element'].append(r[c['type_symbol']].upper())
        out['occupancy'].append(float(r[c['occupancy']]))
        out['model'].append(int(r[c['pdbx_PDB_model_num']]))
        out['xyz'].append((float(r[c['Cartn_x']]), float(r[c['Cartn_y']]), float(r[c['Cartn_z']])))
    table = {k: np.array(v) for k, v in out.items()}
    table['xyz'] = table['xyz'].astype(float).reshape(-1, 3)
    return table, lines


def select(table, mask):
    """Rows of an atom table where `mask` is True."""
    return {k: v[mask] for k, v in table.items()}


def first_conformer(table, alt=('.', 'A')):
    """Keep atoms without alt-loc or with the given alt-loc ids (default: the first conformer)."""
    return select(table, np.isin(table['alt'], list(alt)))


def item(lines, key):
    """A single-valued mmCIF item (e.g. '_struct.title', '_exptl.method'), or '' if absent. Handles values on
    the same line (quoted or not) and semicolon-delimited text blocks."""
    for k, line in enumerate(lines):
        if line.startswith(key + ' ') or line == key:
            rest = line[len(key):].strip()
            if rest:
                return ' '.join(_split(rest))
            if k + 1 < len(lines) and lines[k + 1].startswith(';'):
                text = [lines[k + 1][1:]]
                for nxt in lines[k + 2:]:
                    if nxt.startswith(';'):
                        break
                    text.append(nxt)
                return ' '.join(t.strip() for t in text).strip()
            return ' '.join(_split(lines[k + 1])) if k + 1 < len(lines) else ''
    return ''


def title(lines):
    """The entry's title (_struct.title)."""
    return item(lines, '_struct.title')


def method(lines):
    """The experimental method (_exptl.method), e.g. 'X-RAY DIFFRACTION', 'ELECTRON MICROSCOPY'."""
    return item(lines, '_exptl.method')


def assembly_operator(lines, op_id='2'):
    """4x4 matrix of one _pdbx_struct_oper_list entry (e.g. the mate of a dimer)."""
    k = next(n for n, line in enumerate(lines) if line.startswith('_pdbx_struct_oper_list.'))
    keys = []
    while lines[k].startswith('_pdbx_struct_oper_list.'):
        keys.append(lines[k].split('.', 1)[1].strip())
        k += 1
    tokens = []
    while not lines[k].startswith('#'):
        tokens += _split(lines[k])
        k += 1
    for row in (tokens[n:n + len(keys)] for n in range(0, len(tokens), len(keys))):
        rec = dict(zip(keys, row))
        if rec['id'] == op_id:
            M = np.eye(4)
            for a in range(3):
                for b in range(3):
                    M[a, b] = float(rec[f'matrix[{a + 1}][{b + 1}]'])
                M[a, 3] = float(rec[f'vector[{a + 1}]'])
            return M
    raise KeyError(op_id)


def _split(line):
    out, word, quote = [], '', None
    for ch in line:
        if quote:
            if ch == quote:
                out.append(word)
                word, quote = '', None
            else:
                word += ch
        elif ch in '\'"' and not word:
            quote = ch
        elif ch.isspace():
            if word:
                out.append(word)
            word = ''
        else:
            word += ch
    if word:
        out.append(word)
    return out


def match_states(ref, other, ref_key, other_key, keep_other=None):
    """Two states of one molecule matched atom by atom.

    `ref_key(table, i)` and `other_key(table, i)` give a hashable identity per atom, e.g. (resi, name), with
    any renumbering or alt-loc offsets undone; `keep_other(table, i)` filters the other state's rows (choose
    its conformer). Returns the reference table plus 'start' and 'end' coordinates and 'matched' (atoms
    absent from the other state keep their reference position)."""
    end = {}
    for i in range(len(other['name'])):
        if keep_other is None or keep_other(other, i):
            end[other_key(other, i)] = other['xyz'][i]
    out = dict(ref)
    keys = [ref_key(ref, i) for i in range(len(ref['name']))]
    out['start'] = ref['xyz'].astype(float).copy()
    out['end'] = np.array([end.get(k, x) for k, x in zip(keys, ref['xyz'])], float).reshape(-1, 3)
    out['matched'] = np.array([k in end for k in keys])
    return out


# ----------------------------------------------------------------------------- geometry

def transform(xyz, M):
    return np.asarray(xyz) @ M[:3, :3].T + M[:3, 3]


def kabsch(P, Q):
    """Rotation R and translation t with R @ p + t ~ q (least squares)."""
    pc, qc = P.mean(0), Q.mean(0)
    U, _, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    R = Vt.T @ D @ U.T
    return R, qc - R @ pc


def dihedral(p0, p1, p2, p3):
    """Torsion angle p0-p1-p2-p3 in degrees."""
    b0, b1, b2 = p0 - p1, p2 - p1, p3 - p2
    b1 = b1 / np.linalg.norm(b1)
    v, w = b0 - (b0 @ b1) * b1, b2 - (b2 @ b1) * b1
    return math.degrees(math.atan2(np.cross(b1, v) @ w, v @ w))


def radii(elements, scale=1.0):
    """Van der Waals radii (A) of an element array, times `scale`."""
    return np.array([VDW.get(e, 1.7) for e in elements]) * scale


def find(table, name, resi=None, resn=None, chain=None):
    """Index of the first atom called `name` in the residue given by any of resi / resn / chain."""
    sel = table['name'] == name
    for key, value in (('resi', resi), ('resn', resn), ('chain', chain)):
        if value is not None:
            sel &= table[key] == value
    hits = np.nonzero(sel)[0]
    if not len(hits):
        raise KeyError((name, resi, resn, chain))
    return int(hits[0])


# ----------------------------------------------------------------------------- topology

def bonds(table, xyz=None, links=(), residue=None):
    """Covalent bonds (i, j) with i < j, sorted: by distance within residues, peptide bonds, disulfides,
    plus explicit `links` (pairs of atom indices, e.g. a ligand's covalent attachment).

    `residue` is an integer key per atom identifying its residue (default: from chain, resi and resn)."""
    xyz = np.asarray(table['xyz'] if xyz is None else xyz, float)
    if residue is None:
        ids = {}
        chain = table.get('chain', np.full(len(table['name']), ''))
        residue = np.array([ids.setdefault((c, r, n), len(ids)) for c, r, n in zip(chain, table['resi'], table['resn'])])
    i, j = close_pairs(xyz, 2.2)
    d = np.linalg.norm(xyz[i] - xyz[j], axis=1)
    name, resi, el = table['name'], table['resi'], table['element']
    limit = np.where((el[i] == 'S') | (el[j] == 'S'), 1.95, 1.75)
    peptide = (((name[i] == 'C') & (name[j] == 'N') & (resi[j] - resi[i] == 1)) |
               ((name[j] == 'C') & (name[i] == 'N') & (resi[i] - resi[j] == 1)))
    disulfide = (name[i] == 'SG') & (name[j] == 'SG')
    bonded = (((residue[i] == residue[j]) | peptide) & (d < limit)) | disulfide
    edges = set(zip(i[bonded].tolist(), j[bonded].tolist()))
    edges |= {(min(a, b), max(a, b)) for a, b in links}
    return np.array(sorted(edges), dtype=int).reshape(-1, 2)


def close_pairs(xyz, cutoff):
    """All pairs (i, j), i < j, closer than `cutoff`, found with a spatial hash (no n x n matrix)."""
    xyz = np.asarray(xyz, float)
    if not len(xyz):
        return np.zeros(0, int), np.zeros(0, int)
    cell = np.floor((xyz - xyz.min(0)) / cutoff).astype(np.int64)
    dims = cell.max(0) + 3
    key = ((cell[:, 0] + 1) * dims[1] + cell[:, 1] + 1) * dims[2] + cell[:, 2] + 1
    order = np.argsort(key, kind='stable')
    skey = key[order]
    out_i, out_j = [], []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                shift = (dx * dims[1] + dy) * dims[2] + dz
                lo = np.searchsorted(skey, key + shift, 'left')
                hi = np.searchsorted(skey, key + shift, 'right')
                counts = hi - lo
                a = np.repeat(np.arange(len(xyz)), counts)
                starts = np.repeat(lo - (np.cumsum(counts) - counts), counts)
                b = order[np.arange(counts.sum()) + starts]
                keep = a < b
                a, b = a[keep], b[keep]
                close = np.linalg.norm(xyz[a] - xyz[b], axis=1) < cutoff
                out_i.append(a[close])
                out_j.append(b[close])
    return np.concatenate(out_i), np.concatenate(out_j)


def neighbours(edges, n):
    nb = [[] for _ in range(n)]
    for a, b in edges:
        nb[a].append(b)
        nb[b].append(a)
    return nb


def angle_pairs(edges, n):
    """1-3 pairs (i, k) of every bond angle i-j-k."""
    nb = neighbours(edges, n)
    out = {(min(a, b), max(a, b)) for j in range(n) for x, a in enumerate(nb[j]) for b in nb[j][x + 1:]}
    return np.array(sorted(out)).reshape(-1, 2)


def torsion_pairs(edges, n, atoms):
    """1-4 pairs (i, l) of every torsion i-j-k-l whose four atoms are all in `atoms`."""
    nb, atoms = neighbours(edges, n), set(atoms)
    out = set()
    for j, k in edges:
        for i in nb[j]:
            for l in nb[k]:
                if len({i, j, k, l}) == 4 and {i, j, k, l} <= atoms:
                    out.add((min(i, l), max(i, l)))
    return np.array(sorted(out)).reshape(-1, 2)
