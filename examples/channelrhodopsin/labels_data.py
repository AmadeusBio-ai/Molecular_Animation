"""The channelrhodopsin film's labels as data, for a web page that draws them over the clean film
(molanim.timeline.label_data): storyboard_v4's captions, evidence tags, timescales and pointers, with pointer
anchors projected along the film's camera path. Pure numpy.

channelrhodopsin_v4.py exports the authoritative file with every build (delivery/channelrhodopsin-v4/labels.json),
from its own anchors and ion tracks. Run this module directly only for development: its 'Na+' pointer follows a
transit drawn from a fresh random stream, not the rendered one.

    python examples/channelrhodopsin/labels_data.py OUT.json      (not into delivery/: that file is the build's)
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(HERE)]
import c1c2 as S  # noqa: E402
import storyboard_v4 as B  # noqa: E402
from molanim import particles  # noqa: E402
from molanim import structure as St  # noqa: E402
from molanim import timeline as TL  # noqa: E402

DARK, LIGHT = ROOT / 'assets' / 'pdb' / '9GO1.cif', ROOT / 'assets' / 'pdb' / '9GO2.cif'


def anchors(s, A, points, through):
    """Pointer anchors on the stage: A is protomer A's snapshot list, points the film's named points, through the
    transit tracks (frames, ions, 3)."""
    def at(resi, name, snap=0):
        return A[snap][S.atom_index(s, resi, name)]
    ring_atoms = [S.atom_index(s, 262, n) for n in ('CD2', 'CE2', 'CE3', 'CZ2', 'CZ3', 'CH2')]
    k = B.TWIST_STEPS
    return {
        'extracellular': np.array([-62.0, 30.0, 40.0]), 'cytoplasm': np.array([-62.0, 30.0, -31.0]),
        'bilayer': np.array([58.0, B.SECTION_Y + 4, 4.0]),
        'retinal': points['retinal'], 'k296': at(296, 'NZ'),
        'c13c14': (at('RET', 'C13', k) + at('RET', 'C14', k)) / 2,
        'ghost': at('RET', 'C10'),
        # Trp262's pointer runs during the twist (stage 1), so it marks the ring where the twist leaves it; the
        # final snapshot's ring lies 1.6 A further on, off the rendered indole.
        'w262': A[k][ring_atoms].mean(0), 'k132': at(132, 'NZ', -1), 'e129': at(129, 'OE1', -1),
        'central_gate': points['central_gate'], 'inner_gate': points['inner_gate'],
        'ion': through[:, 0],
    }


def export(path, anchor_points, out):
    """Write the label data for the camera `path` (timeline.camera_path) and the anchors to `out` (JSON)."""
    data = TL.label_data(B.LABELS, path, anchor_points, B.RES, B.FRAMES, B.FPS, levels=B.TAG_LEVELS)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return data


def points_and_path():
    """The film's named points, snapshots and camera path, as the build computes them."""
    s = S.states(DARK, LIGHT)
    snaps, _ = S.activation_path(s, S.bonds(s), B.TWIST_STEPS, B.NETWORK_STEPS)
    Tm = S.stage_matrix(s, B.MEMBRANE_Y, B.YAW_OFFSET)
    A = [St.transform(x, Tm) for x in snaps]
    ret = s['resn'] == 'RET'

    def centre(names):
        return np.mean([A[0][S.atom_index(s, r, a)] for r, a in names], axis=0)
    points = {'dimer_top': np.array([0.0, 0.0, 6.0]), 'retinal': A[0][ret].mean(0),
              'network': centre([(132, 'NZ'), (129, 'CD'), ('RET', 'C15'), (262, 'CZ2')]),
              'central_gate': centre(S.GATE_ATOMS['central']), 'inner_gate': centre(S.GATE_ATOMS['inner'])}
    line, r_free, site_s, _ = S.pathway(s, snaps[-1], Tm, B.SITES)
    points['pore'] = (points['central_gate'] + points['inner_gate']) / 2
    return s, snaps, A, points, line, site_s, TL.camera_path(B.CAMERA, points, B.FRAMES)


if __name__ == '__main__':
    s, snaps, A, points, line, site_s, path = points_and_path()
    through = particles.transits(np.random.default_rng(3), line, site_s, B.ION_ENTRIES, B.FRAMES, lateral=0.3)
    d = export(path, anchors(s, A, points, through), sys.argv[1])
    print(json.dumps({k: len(v) if isinstance(v, list) else v for k, v in d.items() if k != 'header'}))
