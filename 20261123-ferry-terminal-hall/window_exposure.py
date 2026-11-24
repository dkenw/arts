"""Trace the transmitted harbour and the coverage of the window apertures."""

import numpy as np


def harbour_bounds(scene):
    width = scene.render.resolution_x
    return tuple(int(v * width / 528) for v in (270, 66, 528, 236))


def trace_apertures(scene, bounds, *, large):
    import bpy
    from mathutils import Vector

    camera = scene.camera
    eye = camera.location.copy()
    graph = bpy.context.evaluated_depsgraph_get()
    frame = camera.data.view_frame(scene=scene)
    left, right = min(p.x for p in frame), max(p.x for p in frame)
    low, top = min(p.y for p in frame), max(p.y for p in frame)
    width, height = scene.render.resolution_x, scene.render.resolution_y
    x0, y0, x1, y1 = bounds
    basis = camera.matrix_world.to_3x3()
    start = basis @ Vector((left+(right-left)*(x0+0.5)/width, top+(low-top)*(y0+0.5)/height, frame[0].z))
    step_x = basis @ Vector(((right-left)/width, 0, 0))
    step_y = basis @ Vector((0, (low-top)/height, 0))
    panes = {"salt-hazed glass", "rain-washed transom"}
    air = {"suspended sea air", "low air above the inlet", "dried runs beside the glazing rebate"}

    def sees_outside(direction):
        ray = direction.normalized()
        origin = eye
        for _ in range(7):
            hit, point, _, _, obj, _ = scene.ray_cast(graph, origin, ray, distance=330)
            if not hit or point.x > 10.72 or obj.name in panes:
                return True
            if obj.name not in air:
                return False
            origin = point + ray*0.002
        return False

    aperture = np.zeros((height, width), dtype=bool)
    for y in range(y0, y1):
        row = start + step_y*(y-y0)
        for x in range(x0, x1):
            aperture[y, x] = sees_outside(row + step_x*(x-x0))

    if not large:
        return aperture, None

    # Fractional coverage matters where a single large-print pixel straddles
    # the ironwork or the torn blind. Only the edge needs the extra ray samples.
    patch = aperture[y0:y1, x0:x1]
    padded = np.pad(patch, 1, mode="edge")
    edges = np.zeros_like(patch)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            edges |= patch != padded[1+dy:1+dy+y1-y0, 1+dx:1+dx+x1-x0]
    coverage = aperture.astype(np.uint8)*255
    offsets = [step_x*dx + step_y*dy for dy in (-0.375,-0.125,0.125,0.375)
               for dx in (-0.375,-0.125,0.125,0.375)]
    for y, x in zip(*np.nonzero(edges)):
        centre = start + step_y*int(y) + step_x*int(x)
        count = sum(sees_outside(centre + offset) for offset in offsets)
        coverage[y0+y, x0+x] = round(255*count/len(offsets))
    return coverage > 0, coverage


def distant_coverage(scene, bounds, aperture):
    """Amount of distant water or land visible behind each glass sample."""
    import bpy
    from mathutils import Vector

    camera = scene.camera
    eye = camera.location.copy()
    graph = bpy.context.evaluated_depsgraph_get()
    frame = camera.data.view_frame(scene=scene)
    left, right = min(v.x for v in frame), max(v.x for v in frame)
    bottom, top = min(v.y for v in frame), max(v.y for v in frame)
    height, width = aperture.shape
    x0, y0, x1, y1 = bounds
    basis = camera.matrix_world.to_3x3()
    dx = basis @ Vector(((right-left)/width, 0, 0))
    dy = basis @ Vector((0, (bottom-top)/height, 0))
    start = basis @ Vector((left+(x0+.5)*(right-left)/width, top+(y0+.5)*(bottom-top)/height, frame[0].z))

    def ease(t):
        t = max(0., min(1., t))
        return t*t*(3.-2.*t)

    def weight(direction):
        # Start outside the glass. The landing stays in the first exposure.
        # Blend across ordinary near water, then expose the whole city and sky.
        outside = eye + direction*((10.73-eye.x)/direction.x)
        hit, point, _, _, _, _ = scene.ray_cast(graph, outside, direction.normalized(), distance=1450.)
        if not hit:
            return 1.
        return ease((point.x-28.)/9.)

    result = np.zeros((height,width),np.uint8)
    for y in range(y0,y1):
        row = start + (y-y0)*dy
        for x in np.flatnonzero(aperture[y,x0:x1])+x0:
            result[y,x] = round(255.*weight(row + int(x-x0)*dx))
    # Sample the edge of any front fitting on the same camera grid. A single
    # centre ray is ambiguous where a post partly occludes the far bank.
    small = result[y0:y1,x0:x1]
    padded = np.pad(small.astype(np.int16),1,mode="edge")
    edges = np.zeros_like(small,dtype=bool)
    for iy,ix in ((0,1),(1,0),(1,2),(2,1)):
        edges |= np.abs(small - padded[iy:iy+y1-y0,ix:ix+x1-x0]) > 48
    offsets = [(i*dx+j*dy) for j in (-.375,-.125,.125,.375) for i in (-.375,-.125,.125,.375)]
    for y,x in zip(*np.nonzero(edges & aperture[y0:y1,x0:x1])):
        direction = start + int(x)*dx + int(y)*dy
        result[y+y0,x+x0] = round(255.*sum(weight(direction+d) for d in offsets)/len(offsets))
    return result


def take(scene, path, *, large=False, far_shore=False):
    from surface_guides import expose

    render = scene.render
    width, height = render.resolution_x, render.resolution_y
    x0, y0, x1, y1 = harbour_bounds(scene)
    render.use_border = True
    render.use_crop_to_border = False
    render.border_min_x, render.border_max_x = x0/width, x1/width
    render.border_min_y, render.border_max_y = 1-y1/height, 1-y0/height
    mask, coverage = trace_apertures(scene, (x0,y0,x1,y1), large=large)
    fields = {"aperture": mask}
    if coverage is not None:
        fields["coverage"] = coverage
    if far_shore:
        fields["distant"] = distant_coverage(scene, (x0,y0,x1,y1), mask)
        # Expose every affected sample and a margin for the optical filter.
        # The complete camera grid and frame registration stay with the plate.
        rows, cols = np.nonzero(fields["distant"])
        if not len(rows):
            raise ValueError("The far shore is outside the window openings.")
        guard = max(5,round(2.0*width/528))
        render.border_min_x = max(0, int(cols.min())-guard)/width
        render.border_max_x = min(width, int(cols.max())+guard+1)/width
        render.border_min_y = 1-min(height, int(rows.max())+guard+1)/height
        render.border_max_y = 1-max(0, int(rows.min())-guard)/height
    np.savez_compressed(path.with_suffix(".aperture.npz"), **fields)
    expose(scene, path, large=large)
