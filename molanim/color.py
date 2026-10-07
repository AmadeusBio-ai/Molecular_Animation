"""Colour: write sRGB 0-255 in scripts, convert exactly to linear for Blender."""
import numpy as np


def srgb(*rgb255):
    """sRGB 0-255 -> linear 0-1 (exact IEC 61966-2-1 transfer)."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(lin(float(c)) for c in rgb255)


def lin(rgb):
    """srgb() of one (r, g, b) tuple."""
    return srgb(*rgb)


def hex_rgb(h):
    """'#RRGGBB' -> (r, g, b) 0-255."""
    h = h.lstrip('#')
    return tuple(int(h[k:k + 2], 16) for k in (0, 2, 4))


def shade(rng, ramp, n, lo=0.0, hi=1.0):
    """n linear colours drawn between the two sRGB tones of `ramp` (dark, light), uniform in [lo, hi]:
    per-atom variation that gives sphere models their beaded texture."""
    u = rng.uniform(lo, hi, n)[:, None]
    a, b = np.array(lin(ramp[0])), np.array(lin(ramp[1]))
    return a + (b - a) * u


def tile(rgb, n):
    """n copies of one sRGB colour, linear."""
    return np.tile(lin(rgb), (n, 1))
