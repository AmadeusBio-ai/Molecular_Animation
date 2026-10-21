"""Smallest margin (px) between the picture (min channel < 246) and each frame edge, over every frame of a plate loop.
usage: python projects/website/loop_margins.py SHOT [take-01]"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

shot = sys.argv[1]
take = sys.argv[2] if len(sys.argv) > 2 else 'take-01'
T = Path(__file__).resolve().parents[2] / 'renders' / 'website' / 'plate-loops' / shot / take
worst = {'top': (9999, 0), 'bottom': (9999, 0), 'left': (9999, 0), 'right': (9999, 0)}
frames = sorted(T.glob('[0-9][0-9][0-9][0-9].png'))
for f in frames:
    a = np.asarray(Image.open(f).convert('RGB')).min(axis=2)
    h, w = a.shape
    inner = a[3:h - 3, 3:w - 3] < 246            # the encoder whitens the outer 3 px
    rows, cols = np.nonzero(inner.any(axis=1))[0] + 3, np.nonzero(inner.any(axis=0))[0] + 3
    k = int(f.stem)
    for side, m in (('top', rows.min()), ('bottom', h - 1 - rows.max()), ('left', cols.min()), ('right', w - 1 - cols.max())):
        if m < worst[side][0]:
            worst[side] = (int(m), k)
print(f'{shot} {take}: {len(frames)} frames; smallest margin (px, frame): ' +
      ', '.join(f'{s} {m} (f{k})' for s, (m, k) in worst.items()) +
      ('  OK' if min(m for m, _ in worst.values()) >= 6 else '  TOO CLOSE'))
