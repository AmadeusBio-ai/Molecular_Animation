"""Camera and controller rigs baked from per-frame paths (see molanim.timeline)."""
from ..timeline import fstop_for, keyed
from .scene import set_linear


def bake_camera(cam, aim, path, aperture_ratio, clip=(0.5, 6000)):
    """Key the camera and its aim empty on every frame of `path` (timeline.camera_path / orbit_path), with depth
    of field focused on the aim: aperture radius = aperture_ratio x focus distance, so the blur stays
    proportionate as the camera dives. The camera tracks the aim (TRACK_TO, up +Z, no roll)."""
    for f, loc, aim_pt, dist, lens in path:
        cam.location, aim.location = loc, aim_pt
        cam.keyframe_insert('location', frame=f)
        aim.keyframe_insert('location', frame=f)
        cam.data.lens = lens
        cam.data.keyframe_insert('lens', frame=f)
        cam.data.dof.aperture_fstop = fstop_for(aperture_ratio, lens, dist)
        cam.data.dof.keyframe_insert('aperture_fstop', frame=f)
    for block in (cam, aim, cam.data):
        set_linear(block)
    track = cam.constraints.new('TRACK_TO')
    track.target, track.track_axis, track.up_axis = aim, 'TRACK_NEGATIVE_Z', 'UP_Y'
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = aim
    cam.data.clip_start, cam.data.clip_end = clip


def bake_location(obj, keys, points, frames):
    """Key `obj` on every frame along keys [(frame, point), ...] (named points allowed), eased between keys."""
    for f, ((a, b, u),) in keyed(keys, points, frames):
        obj.location = a * (1 - u) + b * u
        obj.keyframe_insert('location', frame=f)
    set_linear(obj)
