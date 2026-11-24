"""A second, short exposure for the stair windows reflected in the clock cover."""

import math

# Native-pixel bounds leave space around the bezel for a soft join between exposures.
BOUNDS = (72, 44, 160, 132)


def install(g):
    import bpy
    from layout import dial

    scene = g["scene"]
    glass = g["newmat"]("curved covers of the double-sided clock")
    output = g["node"](glass, "ShaderNodeOutputMaterial")
    clear = g["node"](glass, "ShaderNodeBsdfTransparent")
    clear.inputs[0].default_value = (0.991, 0.995, 0.993, 1)
    g["thin_pane"](glass, clear.outputs[0], output, 0.065)

    # A pressed spherical cap sits just above the enamel with its edge in
    # the bezel. Its forward normals pick up the clerestory behind the stair.
    aperture, rise = 0.562, 0.064
    radius = (aperture**2 + rise**2) / (2 * rise)
    sectors, rings = 96, 14
    for side in (1, -1):
        verts = [dial(0, 0, side * (0.229 + rise))]
        faces = []
        for row in range(1, rings + 1):
            local_r = aperture * row / rings
            depth = 0.229 + math.sqrt(radius**2 - local_r**2) - (radius - rise)
            for j in range(sectors):
                angle = j * math.tau / sectors
                verts.append(dial(local_r * math.cos(angle), local_r * math.sin(angle), side * depth))
            first = 1 + (row - 1) * sectors
            for j in range(sectors):
                a, b = first + j, first + (j + 1) % sectors
                face = (0, a, b) if row == 1 else (a - sectors, a, b, b - sectors)
                faces.append(face if side > 0 else face[::-1])
        mesh = bpy.data.meshes.new("drawn curved glass")
        mesh.from_pydata(verts, [], faces)
        mesh.materials.append(glass)
        mesh.update()
        for poly in mesh.polygons:
            poly.use_smooth = True
        cover = bpy.data.objects.new(
            "clock cover toward stair" if side > 0 else "clock cover toward gate", mesh
        )
        scene.collection.objects.link(cover)


def expose(g, destination, *, large=False):
    import bpy

    scene = g["scene"]
    r = scene.render
    left, top, right, bottom = BOUNDS
    r.use_border = True
    r.use_crop_to_border = False
    r.border_min_x, r.border_max_x = left / 528, right / 528
    r.border_min_y, r.border_max_y = 1 - bottom / 396, 1 - top / 396
    scene.cycles.samples = min(800, max(128, round(scene.cycles.samples * 1.4)))

    def take_glazed_exposure():
        install(g)
        r.filepath = str(destination.with_suffix(".glass.png"))
        bpy.ops.render.render(write_still=True)

    if not large:
        take_glazed_exposure()
        return

    # At print size a specular highlight crosses several sectors of the turned
    # metal case. Interpolate only its side normals. Its square lips stay sharp.
    casing = bpy.data.objects["dark enamel clock"].data
    sharp = [edge.use_edge_sharp for edge in casing.edges]
    rounded = [poly.use_smooth for poly in casing.polygons]
    lips = {key for poly in casing.polygons if len(poly.vertices) > 4 for key in poly.edge_keys}
    for edge in casing.edges:
        if edge.key in lips:
            edge.use_edge_sharp = True
    for poly in casing.polygons:
        if len(poly.vertices) == 4:
            poly.use_smooth = True
    casing.update()
    try:
        r.filepath = str(destination.with_suffix(".direct.png"))
        bpy.ops.render.render(write_still=True)
        take_glazed_exposure()
    finally:
        for edge, original in zip(casing.edges, sharp):
            edge.use_edge_sharp = original
        for poly, original in zip(casing.polygons, rounded):
            poly.use_smooth = original
        casing.update()
