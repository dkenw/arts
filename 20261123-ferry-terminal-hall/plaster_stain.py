"""Native-pixel pigment on the berth wall, below the old parapet seep."""

import math
from collections import defaultdict
from mathutils import Vector


def smooth(lo, hi, x):
    t = max(0.0, min(1.0, (x - lo) / (hi - lo)))
    return t * t * (3.0 - 2.0 * t)


def deposits(x, z):
    """Dust washed into the plaster, sediment at its drying front, and a trace of lime."""
    seam_x, rail_z = 3.25, 4.72
    s = x - seam_x
    # Fine changes in the drying edge follow the plaster. Keep them much
    # smaller than its lobes, which still read as one stain from the landing.
    tooth = 0.022 * math.sin(18 * x + 4 * z) + 0.015 * math.sin(29 * z - 9 * x)
    if z > rail_z:
        fall = (6.78 - z) / (6.78 - rail_z)
        reach = 0.17 + 0.46 * fall + 0.095 * math.sin(8.2 * fall)
        centre = -0.10 * fall + 0.045 * math.sin(11 * fall)
        dist = reach - abs(s - centre) + tooth
        cover = smooth(0.0, 0.16, fall) * smooth(-0.070, 0.145, dist)
        flow = 0.39 + 0.13 * math.cos(8.0 * s + 1.5 * fall)
        strand = math.exp(-((s + 0.30 * fall - 0.045 * math.sin(6 * fall)) / 0.115) ** 2)
        # Most of the old, exposed mortar already reads dark. The trace is
        # easier to see in the porous paint at its shoulders.
        shoulder = 0.51 + 0.49 * smooth(0.075, 0.29, abs(s - centre))
        wash = cover * (flow + 0.20 * strand) * shoulder
        edge = math.exp(-((dist - 0.022) / 0.074) ** 2)
        sediment = edge * smooth(0.01, 0.28, fall) * (0.18 + 0.11 * math.sin(8 * z - 3 * x))
        return wash, sediment, 0.0

    # Water travelled sideways along the picture rail before soaking back
    # into the plaster. The longer lobe sits slightly aside from the old run.
    depth = (
        0.78 * math.exp(-((s + 0.34) / 0.54) ** 2)
        + 0.35 * math.exp(-((s + 0.88) / 0.27) ** 2)
        + 0.20 * math.exp(-((s - 0.04) / 0.26) ** 2)
        + 0.20 * math.exp(-((s - 0.33) / 0.21) ** 2)
    )
    bottom = rail_z - depth + 0.041 * math.sin(11 * x) + tooth
    dist = z - bottom
    lateral = smooth(0.04, 0.24, depth)
    cover = smooth(-0.045, 0.17, dist) * lateral
    travelled = smooth(0.0, 0.52, rail_z - z)
    wash = cover * (0.42 + 0.09 * math.sin(9 * s + 0.5 * z) - 0.11 * travelled)
    # A discontinuous line of deposited silt. A few sections have a very
    # thin, lighter outer shore where the last water dried.
    broken = 0.48 + 0.23 * math.sin(8.7 * x) + 0.15 * math.sin(19.3 * x + 0.6)
    sediment = lateral * broken * math.exp(-((dist - 0.058) / 0.079) ** 2)
    lime = lateral * smooth(0.43, 0.78, broken) * 0.47 * math.exp(-((dist + 0.035) / 0.045) ** 2)
    return wash, sediment, lime


def print_seepage(scene, width, height, project, visible, marks):
    """Project the pigment through the actual camera and mask the iron picture rail."""
    # The exact surface that carries the older painted wall in terminal.py.
    wall_y = 16.039
    bounds = [(2.05, 3.61), (4.26, 3.61), (2.05, 6.84), (4.26, 6.84)]
    corners = [project((x, wall_y, z)) for x, z in bounds]
    xs, ys = zip(*corners)
    columns = range(max(0, math.floor(min(xs))), min(width, math.ceil(max(xs))))
    rows = range(max(0, math.floor(min(ys))), min(height, math.ceil(max(ys))))
    cam = scene.camera
    eye = cam.location.copy()
    camera_basis = cam.matrix_world.to_3x3()
    frame = cam.data.view_frame(scene=scene)
    left, right = min(p.x for p in frame), max(p.x for p in frame)
    low, top = min(p.y for p in frame), max(p.y for p in frame)

    def on_wall(px, py):
        local = Vector((left + (right - left) * px / width, top - (top - low) * py / height, frame[0].z))
        ray = camera_basis @ local
        return eye + ray * ((wall_y - eye.y) / ray.y)

    groups = defaultdict(list)
    inks = ('old seepage', 'dry silt', 'lime trace')
    # Integrate pigment over each native pixel before reducing to the print palette.
    samples = (0.20, 0.50, 0.80)
    for py in rows:
        for px in columns:
            centre = on_wall(px + 0.5, py + 0.5)
            if not visible(centre):
                continue
            summed = [0.0, 0.0, 0.0]
            for dy in samples:
                for dx in samples:
                    p = on_wall(px + dx, py + dy)
                    for i, v in enumerate(deposits(p.x, p.z)):
                        summed[i] += v
            for ink, total in zip(inks, summed):
                strength = round(total * 48 / (len(samples) ** 2))
                if strength > 0:
                    groups[(ink, strength)].append((px, py))
    for (ink, strength), pixels in groups.items():
        marks.append([ink, strength / 48, pixels])
