"""Expose the hall reflected in the quay windows, and record the visible glass surfaces."""

from pathlib import Path

import numpy as np


def photograph(g, destination, samples):
    import bpy
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    scene = g["scene"]
    camera = scene.camera
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    panes = {g["glass"].name, g["open_glass"].name}
    air = {"suspended sea air", "low air above the inlet", "dried runs beside the glazing rebate"}
    width = scene.render.resolution_x
    height = scene.render.resolution_y
    # Enclose the visible portion of the window wall, including the edge of the sash tipped inwards.
    corners = []
    for y in (-5.5, 16.55):
        for x in (10.10, 10.56):
            for z in (1.14, 6.72):
                p = world_to_camera_view(scene, camera, Vector((x, y, z)))
                corners.append((p.x * width, (1 - p.y) * height))
    xs, ys = zip(*corners)
    x0, x1 = max(0, int(min(xs)) - 3), min(width, int(max(xs)) + 4)
    y0, y1 = max(0, int(min(ys)) - 3), min(height, int(max(ys)) + 4)
    frame = camera.data.view_frame(scene=scene)
    left, right = min(p.x for p in frame), max(p.x for p in frame)
    low, top = min(p.y for p in frame), max(p.y for p in frame)
    basis = camera.matrix_world.to_3x3()
    eye = camera.location.copy()
    # A zero cosine denotes a frame, pier, or a real opening. A negative value denotes the tilted sash.
    cosine = np.zeros((y1 - y0, x1 - x0), np.float32)
    along = np.zeros_like(cosine)
    elevation = np.zeros_like(cosine)
    base_ray = basis @ Vector((
        left + (right - left) * (x0 + 0.5) / width,
        top + (low - top) * (y0 + 0.5) / height,
        frame[0].z,
    ))
    step_x = basis @ Vector(((right - left) / width, 0, 0))
    step_y = basis @ Vector((0, (low - top) / height, 0))
    for row in range(y1 - y0):
        start = base_ray + row * step_y
        for col in range(x1 - x0):
            ray = (start + col * step_x).normalized()
            origin = eye
            for _ in range(7):
                hit, p, normal, _, obj, _ = scene.ray_cast(graph, origin, ray, distance=65)
                if not hit:
                    break
                if obj.name in panes and p.x > 10:
                    sign = -1 if obj.name == g["open_glass"].name else 1
                    cosine[row, col] = sign * abs(normal.dot(ray))
                    along[row, col], elevation[row, col] = p.y, p.z
                    break
                if obj.name not in air:
                    break
                origin = p + ray * 0.002
    destination = Path(destination)
    np.savez_compressed(
        destination.with_suffix(".panes.npz"), origin=(x0, y0), size=(width, height),
        cosine=cosine, along=along, elevation=elevation,
    )

    # Only the camera sees the silvered proof. All rays that light the room still
    # pass through its original glass, including the rays that bounce from the mirror.
    for mat in (g["glass"], g["open_glass"]):
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        out = next(n for n in nodes if n.type == "OUTPUT_MATERIAL")
        original = out.inputs["Surface"].links[0].from_socket
        path = nodes.new("ShaderNodeLightPath")
        mirror = nodes.new("ShaderNodeBsdfGlossy")
        mirror.inputs["Roughness"].default_value = 0.019
        mirror.inputs["Color"].default_value = (1, 1, 1, 1)
        switch = nodes.new("ShaderNodeMixShader")
        links.new(path.outputs["Is Camera Ray"], switch.inputs[0])
        links.new(original, switch.inputs[1])
        links.new(mirror.outputs[0], switch.inputs[2])
        links.new(switch.outputs[0], out.inputs["Surface"])
    r = scene.render
    r.use_border, r.use_crop_to_border = True, False
    r.border_min_x, r.border_max_x = x0 / width, x1 / width
    r.border_min_y, r.border_max_y = 1 - y1 / height, 1 - y0 / height
    scene.cycles.samples = min(samples, 224)
    r.filepath = str(destination.with_suffix(".room.png"))
    bpy.ops.render.render(write_still=True)
