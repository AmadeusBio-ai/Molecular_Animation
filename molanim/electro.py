"""Electrons, drawn for what they are: where the cloud ends, what its charge does, and where it is shared.

Three ideas, each with a picture in the Blender layer:
  - The van der Waals surface is a good stand-in for the outer edge of a molecule's electron cloud. The usual
    definition of a molecule's size is its 0.001 e/bohr^3 electron-density contour (Boyd 1977; Bader, Carroll,
    Cheeseman & Chang 1987, J. Am. Chem. Soc. 109, 7968), and atomic radii at that contour match van der Waals
    radii to about 0.2 A (Rahm, Hoffmann & Ashcroft 2016, Chem. Eur. J. 22, 14625).
    molanim.blender.groups.envelope() draws the union of van der Waals spheres as a translucent skin.
  - The skin can be coloured by the Coulombic electrostatic potential of the molecule's charges: red negative,
    white neutral, blue positive, saturating at +-10 kcal/(mol e), with a distance-dependent dielectric
    (epsilon = 4r) and the potential read 1.4 A outside the surface, the defaults of UCSF ChimeraX's `coulombic`
    command (other fields use other colours; say which in the caption). Charges here are formal charges per
    titratable group at neutral pH. It is an estimate for pictures, not a Poisson-Boltzmann solution.
  - Conjugated and aromatic groups share their pi electrons over the whole ring system (resonance), on both faces
    of its plane. pi_systems() finds those planes and pi_lobes() places two lobes per group, one each side.
    Drawing the delocalised cloud is more faithful than alternating double bonds. The lobes' offset from the
    plane is a drawing choice, not a measured density maximum.

Sources, with how far each was verified: docs/depiction-sources.md.

Pure numpy; Angstrom; potentials in kcal/(mol e).
"""
import numpy as np

COULOMB = 332.0637                     # kcal A / (mol e^2): e^2 / (4 pi eps0) in these units

# Formal charges at neutral pH, spread over the atoms that share them. Histidine is taken as neutral.
SIDE_CHAIN_CHARGES = {
    'LYS': {'NZ': 1.0},
    'ARG': {'NH1': 0.5, 'NH2': 0.5},
    'ASP': {'OD1': -0.5, 'OD2': -0.5},
    'GLU': {'OE1': -0.5, 'OE2': -0.5},
    'HEM': {'O1A': -0.5, 'O2A': -0.5, 'O1D': -0.5, 'O2D': -0.5},   # the two propionates
}
ION_CHARGES = {'K': 1.0, 'NA': 1.0, 'LI': 1.0, 'MG': 2.0, 'CA': 2.0, 'ZN': 2.0, 'MN': 2.0, 'CL': -1.0}
NUCLEOTIDE_NAMES = {'DA', 'DC', 'DG', 'DT', 'DU', 'A', 'C', 'G', 'U'}
AMINO_ACIDS = {'ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'GLY', 'HIS', 'ILE', 'LEU', 'LYS', 'MET', 'PHE',
               'PRO', 'SER', 'THR', 'TRP', 'TYR', 'VAL', 'MSE'}

# Conjugated, planar atom sets (pi systems) by residue name.
PI_ATOMS = {
    'PHE': ['CG', 'CD1', 'CD2', 'CE1', 'CE2', 'CZ'],
    'TYR': ['CG', 'CD1', 'CD2', 'CE1', 'CE2', 'CZ'],
    'TRP': ['CG', 'CD1', 'NE1', 'CE2', 'CD2', 'CE3', 'CZ3', 'CH2', 'CZ2'],
    'HIS': ['CG', 'ND1', 'CE1', 'NE2', 'CD2'],
    'PURINE': ['N9', 'C8', 'N7', 'C5', 'C6', 'N1', 'C2', 'N3', 'C4'],
    'PYRIMIDINE': ['N1', 'C2', 'N3', 'C4', 'C5', 'C6'],
    # Heme: the porphyrin macrocycle, an aromatic ring of 18 delocalised pi electrons, with its four nitrogens.
    'HEM': ['CHA', 'CHB', 'CHC', 'CHD', 'C1A', 'C2A', 'C3A', 'C4A', 'C1B', 'C2B', 'C3B', 'C4B', 'C1C', 'C2C',
            'C3C', 'C4C', 'C1D', 'C2D', 'C3D', 'C4D', 'NA', 'NB', 'NC', 'ND'],
    # GFP chromophore (p-hydroxybenzylidene-imidazolinone): phenol ring, methine bridge and imidazolinone.
    'CRO': ['CG2', 'CD1', 'CD2', 'CE1', 'CE2', 'CZ', 'OH', 'CB2', 'CA2', 'C2', 'O2', 'N3', 'C1', 'N2'],
}
PURINES = {'DA', 'DG', 'A', 'G'}
PYRIMIDINES = {'DC', 'DT', 'DU', 'C', 'U'}


def formal_charges(table):
    """Per-atom formal charges (e) at neutral pH: Lys +1, Arg +1, Asp -1, Glu -1 (spread over the charged
    group's atoms), the free N-terminus +1 and C-terminus -1 of every protein chain, -1 per nucleic-acid phosphate
    (OP1/OP2), heme propionates -1 each, and monatomic ions by element."""
    names, resn = table['name'], table['resn']
    q = np.zeros(len(names))
    for res, atoms in SIDE_CHAIN_CHARGES.items():
        on = resn == res
        for atom, value in atoms.items():
            q[on & (names == atom)] = value
    phosphate = np.isin(resn, list(NUCLEOTIDE_NAMES)) & np.isin(names, ['OP1', 'OP2'])
    q[phosphate] = -0.5
    for el, value in ION_CHARGES.items():
        q[(table['element'] == el) & (resn == el)] = value
    protein = np.isin(resn, list(AMINO_ACIDS))
    for chain in dict.fromkeys(table['chain'][protein].tolist()):
        on = protein & (table['chain'] == chain)
        resi = table['resi'][on]
        first, last = resi.min(), resi.max()
        n_term = on & (table['resi'] == first) & (names == 'N')
        q[n_term] += 1.0
        c_term = on & (table['resi'] == last) & np.isin(names, ['O', 'OXT'])
        if c_term.sum():
            q[c_term] += -1.0 / c_term.sum()
    return q


def potential(points, xyz, q, dielectric=4.0, distance_dependent=True, min_distance=1.0, chunk=4096):
    """Coulombic potential (kcal/(mol e)) at `points` from charges `q` at `xyz`: sum of 332 q / (eps r), with
    eps = dielectric * r (distance-dependent, the default) or a constant. Distances below `min_distance` are
    clamped. Only charged atoms are summed."""
    points = np.asarray(points, float)
    on = np.asarray(q) != 0
    src, qs = np.asarray(xyz, float)[on], np.asarray(q, float)[on]
    out = np.zeros(len(points))
    for s in range(0, len(points), chunk):
        d = np.linalg.norm(points[s:s + chunk, None] - src[None], axis=2)
        d = np.maximum(d, min_distance)
        eps = dielectric * d if distance_dependent else dielectric
        out[s:s + chunk] = COULOMB * (qs[None] / (eps * d)).sum(1)
    return out


def potential_colors(phi, limit=10.0, negative=(206, 68, 60), neutral=(255, 255, 255), positive=(52, 104, 214)):
    """Linear RGB per value on a red - white - blue scale, saturating at +-`limit` kcal/(mol e)."""
    from .color import lin
    neg, mid, pos = (np.array(lin(c)) for c in (negative, neutral, positive))
    u = np.clip(np.asarray(phi, float) / limit, -1, 1)[:, None]
    return np.where(u < 0, mid + (neg - mid) * -u, mid + (pos - mid) * u)


def pi_systems(table, residues=None):
    """Planar pi systems of the atom table: [(residue name, chain, resi, atom indices)] for aromatic side chains,
    nucleobases, heme porphyrins and the GFP chromophore (PI_ATOMS). Only complete groups are returned.
    `residues` limits the search to residue names."""
    out = []
    names = table['name']
    keys = dict.fromkeys(zip(table['chain'].tolist(), table['resi'].tolist(), table['resn'].tolist()))
    for chain, resi, resn in keys:
        if residues is not None and resn not in residues:
            continue
        group = PI_ATOMS.get('PURINE' if resn in PURINES else 'PYRIMIDINE' if resn in PYRIMIDINES else resn)
        if group is None:
            continue
        sel = (table['chain'] == chain) & (table['resi'] == resi) & (table['resn'] == resn)
        idx = {nm: int(k) for k, nm in zip(np.nonzero(sel)[0], names[sel])}
        if all(a in idx for a in group):
            out.append((resn, chain, resi, np.array([idx[a] for a in group])))
    return out


# Retinal (RET) bound to lysine as a protonated Schiff base: the conjugated chain from the beta-ionone ring's
# C5=C6 through the polyene to C15=NZ, in bond order. NZ belongs to the lysine (pass its index separately).
RETINAL_CHAIN = ['C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'C13', 'C14', 'C15']


def pi_chain_lobes(xyz, offset=0.95):
    """Pi lobes along a conjugated chain that need not be flat (retinal's polyene, which twists about C13=C14 on
    photoisomerisation): each atom gets its own normal, from the plane of its two chain bonds, flipped to agree with
    its neighbour's. Where a bond twists, the normals of its atoms turn apart and the lobes split there: the
    overlap of their p orbitals, and with it the conjugation, is broken. Returns (above, below, normals, twist):
    twist[i] is the angle (deg) between the normals of atoms i and i+1."""
    p = np.asarray(xyz, float)
    n = len(p)
    nrm = np.zeros((n, 3))
    for i in range(1, n - 1):
        v = np.cross(p[i] - p[i - 1], p[i + 1] - p[i])
        if np.linalg.norm(v) < 1e-6:                   # a straight run: keep the neighbour's normal
            v = nrm[i - 1] if i > 1 else np.cross(p[i + 1] - p[i - 1], [0.0, 0.0, 1.0])
        nrm[i] = v / np.linalg.norm(v)
        if i > 1 and nrm[i] @ nrm[i - 1] < 0:
            nrm[i] = -nrm[i]
    nrm[0], nrm[-1] = nrm[1], nrm[-2]                  # an end atom has one bond: it shares its neighbour's plane
    twist = np.degrees(np.arccos(np.clip((nrm[:-1] * nrm[1:]).sum(1), -1, 1)))
    return p + offset * nrm, p - offset * nrm, nrm, twist


def pi_lobes(xyz, offset=0.95):
    """The two lobes of a planar pi system: its atom positions moved +-`offset` A along the best-fit plane normal,
    one lobe on each face of the ring, as pi clouds are drawn in textbooks (the 2p orbitals that form them have
    a node in the plane). Returns (above, below, normal, plane RMS deviation)."""
    xyz = np.asarray(xyz, float)
    c = xyz.mean(0)
    _, _, vt = np.linalg.svd(xyz - c)
    nrm = vt[2]
    rms = float(np.sqrt(np.mean(((xyz - c) @ nrm) ** 2)))
    return xyz + offset * nrm, xyz - offset * nrm, nrm, rms
