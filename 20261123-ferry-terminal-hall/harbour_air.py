"""Depth and optical treatment of the morning air in the large harbour print."""

from pathlib import Path

import numpy as np

SKY = 65535
# One metre is more than sufficient for this light falloff over hundreds of metres.
TRANSPARENT = {
    "salt-hazed glass", "rain-washed transom", "clear rooflight",
    "suspended sea air", "low air above the inlet", "dried runs beside the glazing rebate",
}


def surface_ranges(scene, transparent, tracked=()):
    """Build the first-hit tree and register the triangle ranges for the requested surfaces."""
    import bpy
    from mathutils.bvhtree import BVHTree

    graph = bpy.context.evaluated_depsgraph_get()
    vertices, faces = [], []
    tracked_faces = {}
    for original in scene.objects:
        if original.type != "MESH" or original.hide_render or original.name in transparent:
            continue
        obj = original.evaluated_get(graph)
        mesh = obj.data
        offset = len(vertices)
        begin = len(faces)
        matrix = obj.matrix_world
        vertices.extend(matrix @ vertex.co for vertex in mesh.vertices)
        mesh.calc_loop_triangles()
        faces.extend(tuple(offset + i for i in triangle.vertices) for triangle in mesh.loop_triangles)
        if original.name in tracked:
            tracked_faces[original.name] = range(begin, len(faces))
    return BVHTree.FromPolygons(vertices, faces, all_triangles=True), tracked_faces


def solid_surfaces(scene, transparent, tracked=None):
    """Return the first-hit tree and the optional single object's triangle range."""
    tree, ranges = surface_ranges(scene, transparent, (tracked,) if tracked is not None else ())
    return tree, ranges.get(tracked, range(0))


def record_distance(scene, destination):
    """Record the distance to the first solid surface behind the window wall."""
    from mathutils import Vector
    from window_exposure import harbour_bounds

    width = scene.render.resolution_x
    height = scene.render.resolution_y
    x0, y0, x1, y1 = harbour_bounds(scene)
    solid, _ = solid_surfaces(scene, TRANSPARENT)

    camera = scene.camera
    eye = camera.location.copy()
    frame = camera.data.view_frame(scene=scene)
    left, right = min(v.x for v in frame), max(v.x for v in frame)
    bottom, top = min(v.y for v in frame), max(v.y for v in frame)
    basis = camera.matrix_world.to_3x3()
    dx = basis @ Vector(((right - left) / width, 0, 0))
    dy = basis @ Vector((0, (bottom - top) / height, 0))
    start = basis @ Vector((
        left + (x0 + 0.5) * (right - left) / width,
        top + (y0 + 0.5) * (bottom - top) / height, frame[0].z,
    ))

    def distance(direction):
        point, _, _, metres = solid.ray_cast(eye, direction.normalized(), camera.data.clip_end)
        if point is None:
            return SKY
        if point.x < 10.73:
            return 0
        return max(1, min(SKY - 1, round(metres)))

    centre = np.empty((y1 - y0, x1 - x0), np.uint16)
    for y in range(centre.shape[0]):
        row = start + dy * y
        for x in range(centre.shape[1]):
            centre[y, x] = distance(row + dx * x)

    # Four subpixel rays distinguish the fine hoist lines from the sky and
    # a far wall from a near mullion at a shared edge.
    depths = np.repeat(centre[:, :, None], 4, axis=2)
    padded = np.pad(centre.astype(np.int32), 1, mode="edge")
    h, w = centre.shape
    edges = np.zeros((h, w), bool)
    for yy, xx in ((0, 1), (1, 0), (1, 2), (2, 1), (0, 0), (2, 2), (0, 2), (2, 0)):
        edges |= np.abs(padded[yy:yy+h, xx:xx+w] - centre) > 18
    offsets = tuple(dx * i + dy * j for i in (-0.27, 0.27) for j in (-0.27, 0.27))
    for y, x in zip(*np.nonzero(edges)):
        ray = start + dx * int(x) + dy * int(y)
        depths[y, x] = [distance(ray + offset) for offset in offsets]

    path = Path(destination).with_suffix(".harbour-depth.npz")
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, size=(width, height), origin=(x0, y0), metres=depths)
    return path


# The 528-pixel plate already merges the fine shore details into its pixel clusters.
# These are print settings for the large exposure of the same overcast morning.
EXTINCTION = 0.00044
MAX_VEIL = 0.16
SCATTER_FRACTION = 0.19
SPREAD_AT_2112 = 1.7


def to_linear(colour):
    """Convert camera RGB on the 0–255 scale to relative linear light."""
    value = colour / 255.0
    return np.where(value <= 0.04045, value / 12.92, ((value + 0.055) / 1.055)**2.4)


def from_linear(light):
    """Return display-encoded sRGB in the unit interval for ordinary exposures."""
    return np.where(light <= 0.0031308, 12.92 * light,
                    1.055 * np.maximum(light, 0)**(1.0 / 2.4) - 0.055)


def in_morning_air(rgb, source):
    """Attenuate the exterior in linear light, before the old glass reflects the hall."""
    from scipy.ndimage import binary_erosion, gaussian_filter

    path = Path(source).with_suffix(".harbour-depth.npz")
    with np.load(path) as guide:
        width, height = map(int, guide["size"])
        x, y = map(int, guide["origin"])
        metres = guide["metres"]
    if (height, width, 3) != rgb.shape or metres.ndim != 3 or metres.shape[2] != 4:
        raise ValueError("The harbour distances must use the camera grid of this exposure.")
    h, w = metres.shape[:2]
    view = rgb[y:y+h, x:x+w]
    if view.shape != (h, w, 3):
        raise ValueError("The harbour range guide extends beyond the exposure.")
    sky = metres == SKY
    # Sample the overcast light already present above the skyline. Keep away
    # from mullions, the edge of the blind and silhouetted steel for this reading.
    clean_sky = binary_erosion(sky.all(axis=2), iterations=max(1, round(4 * width / 2112)))
    if not np.any(clean_sky):
        return rgb
    air_colour = np.median(view[clean_sky], axis=0)

    # The air path grows beyond the sheltered landing. The raw exposure already
    # contains the sky, so pure sky needs no additional airlight.
    path_length = np.maximum(metres.astype(np.float32) - 65.0, 0.0)
    path_length[sky] = 0.0
    veil = np.minimum(-np.expm1(-EXTINCTION * path_length), MAX_VEIL).mean(axis=2)
    linear = to_linear(view)
    transmitted = linear + veil[..., None] * (to_linear(air_colour) - linear)

    # Small-angle scatter gently rounds a strand of cable against its local sky.
    # Only distant samples enter the average. A nearby frame cannot bleed into it.
    sigma = max(0.4, SPREAD_AT_2112 * width / 2112)
    backdrop = (metres > 95).all(axis=2).astype(np.float32)
    weight = gaussian_filter(backdrop, sigma)
    spread = gaussian_filter(transmitted * backdrop[..., None], (sigma, sigma, 0))
    spread /= np.maximum(weight[..., None], 1e-6)
    reach = np.minimum(path_length / 250.0, 1.0).mean(axis=2)
    # On the sky side, keep just the narrow share scattered from the outline.
    reach += sky.mean(axis=2) * gaussian_filter(reach, sigma)
    scatter = SCATTER_FRACTION * np.minimum(reach, 1.0) * backdrop
    transmitted += scatter[..., None] * (spread - transmitted)

    value = from_linear(transmitted)
    affected = (veil > 0) | (scatter > 0)
    view[affected] = np.clip(255.0 * value[affected], 0.0, 255.0)
    return rgb
