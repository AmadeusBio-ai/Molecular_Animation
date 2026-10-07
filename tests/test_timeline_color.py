import math

import numpy as np

from molanim import color, timeline


def test_easing():
    for f in (timeline.smoothstep, timeline.smootherstep):
        assert f(-1) == 0 and f(0) == 0 and f(1) == 1 and f(2) == 1 and abs(f(0.5) - 0.5) < 1e-12
    assert timeline.ramp(5, 10, 20) == 0 and timeline.ramp(25, 10, 20) == 1


def test_camera_path_dives_in_log_distance():
    points = {'a': np.zeros(3)}
    path = timeline.camera_path([(1, 'a', 400, 0, 0, 50), (11, 'a', 100, 0, 0, 50)], points, 11)
    assert len(path) == 11
    assert abs(path[5][3] - 200.0) < 1e-9                           # u = 0.5 -> geometric mean of 400 and 100
    assert np.allclose(path[0][1], (0, -400, 0))                    # azimuth 0 looks from -Y


def test_orbit_closes_for_loops():
    path = timeline.orbit_path((1, 2, 3), 50, 10, 50, frames=120)
    assert len(path) == 121 and np.allclose(path[120][1], path[0][1])


def test_project_puts_the_aim_at_the_centre():
    xy, z = timeline.project((0, 0, 0), np.array([0.0, -100, 0]), np.zeros(3), 50, (1920, 1080))
    assert np.allclose(xy, (960, 540)) and abs(z - 100) < 1e-9
    xy, _ = timeline.project((10, 0, 0), np.array([0.0, -100, 0]), np.zeros(3), 50, (1920, 1080))
    assert xy[0] > 960                                              # +X is screen right


def test_fstop():
    assert math.isclose(timeline.fstop_for(0.016, 50, 100), 0.05 / 3.2)


def test_srgb_is_exact():
    assert color.srgb(0, 255, 128) == (0.0, 1.0, ((128 / 255 + 0.055) / 1.055) ** 2.4)
    assert color.hex_rgb('#002655') == (0, 38, 85)
    c = color.shade(np.random.default_rng(0), ((0, 0, 0), (255, 255, 255)), 5)
    assert c.shape == (5, 3) and c.min() >= 0 and c.max() <= 1
