"""Read the alpha of textured scene overlays at a concrete registration ray hit."""

import math

import numpy as np


def alpha_triangles(scene, names, ranges):
    """Associate triangle indices in the visibility tree with their UVs and alpha map."""
    import bpy

    graph = bpy.context.evaluated_depsgraph_get()
    faces = {}
    for name in names:
        obj = scene.objects[name].evaluated_get(graph)
        mesh = obj.data
        mesh.calc_loop_triangles()
        texture = next(node.image for node in mesh.materials[0].node_tree.nodes
                       if node.type == "TEX_IMAGE" and node.image is not None)
        width, height = texture.size
        rgba = np.empty(width*height*4, np.float32)
        texture.pixels.foreach_get(rgba)
        alpha = rgba.reshape(height,width,4)[...,3].copy()
        vertices = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
        uv_layer = mesh.uv_layers.active.data
        for index, triangle in zip(ranges[name],mesh.loop_triangles,strict=True):
            a, b, c = (vertices[i] for i in triangle.vertices)
            uv_a, uv_b, uv_c = (uv_layer[i].uv.copy() for i in triangle.loops)
            ab, ac = b-a, c-a
            aa, bb, ab_ac = ab.dot(ab), ac.dot(ac), ab.dot(ac)
            determinant = aa*bb-ab_ac*ab_ac
            if determinant > 1e-15:
                weight_b = (bb*ab-ab_ac*ac)/determinant
                weight_c = (aa*ac-ab_ac*ab)/determinant
                faces[index] = (a,weight_b,weight_c,uv_a,uv_b-uv_a,uv_c-uv_a,alpha)
    return faces


def opacity(triangle, point):
    origin, weight_b, weight_c, base, duv_b, duv_c, alpha = triangle
    rel = point-origin
    u, v = base + weight_b.dot(rel)*duv_b + weight_c.dot(rel)*duv_c
    height, width = alpha.shape
    # Blender's Linear image interpolation, with Repeat extension along the edge.
    x, y = u*width-.5, v*height-.5
    x0, y0 = math.floor(x), math.floor(y)
    sx, sy = x-x0, y-y0
    top = (1-sx)*alpha[y0%height,x0%width] + sx*alpha[y0%height,(x0+1)%width]
    bottom = (1-sx)*alpha[(y0+1)%height,x0%width] + sx*alpha[(y0+1)%height,(x0+1)%width]
    return float((1-sy)*top+sy*bottom)


def first_surface(tree, eye, direction, distance, overlays):
    point, _, index, _ = tree.ray_cast(eye,direction,distance)
    transmission = 1.
    while index in overlays:
        transmission *= 1-opacity(overlays[index],point)
        if transmission < .5/255:
            return None,None,0
        point, _, index, _ = tree.ray_cast(point+.00025*direction,direction,distance)
    return point,index,transmission
