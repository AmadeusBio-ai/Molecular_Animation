"""Plate rule for loop frames: nothing non-white within `border` px of the frame edge (scaled to the render size),
where non-white means a minimum channel below 246 (the website encoder lifts lighter, near-neutral pixels to white).
The outer 3 px are left out, as the encoder whitens them (stray denoiser pixels in the corners).
Also writes a contact sheet. usage: python loop_edges.py SHEET.png BORDER_PX_AT_FULL_SIZE FULL_WIDTH frame.png ..."""
import sys

import numpy as np
from PIL import Image

sheet, border, full_w, files = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
tiles, bad = [], 0
for f in files:
    im = Image.open(f).convert('RGB')
    a = np.asarray(im).min(axis=2)
    b = max(1, round(border * im.width / full_w))
    w = max(1, round(3 * im.width / full_w))
    a = a.copy()
    a[:w], a[-w:], a[:, :w], a[:, -w:] = 255, 255, 255, 255
    edge = np.concatenate([a[:b].ravel(), a[-b:].ravel(), a[:, :b].ravel(), a[:, -b:].ravel()])
    dark = int((edge < 246).sum())
    bad += dark > 0
    print(f'{f.rsplit("/", 1)[-1].rsplit(chr(92), 1)[-1]}: {im.width}x{im.height}, edge {b} px, '
          f'non-white edge pixels {dark} (darkest {int(edge.min())})')
    tiles.append(im.resize((480, round(480 * im.height / im.width))))
h = max(t.height for t in tiles)
S = Image.new('RGB', (480 * len(tiles), h), 'white')
for i, t in enumerate(tiles):
    S.paste(t, (i * 480, 0))
S.save(sheet)
print('edges ok' if not bad else f'EDGE TOUCHED in {bad} frame(s)')
