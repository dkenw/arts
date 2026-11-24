"""Small construction details resolved by the larger grid of the side study."""

import math


def cast_haunch(points):
    """Round the transitions of the cast web, retaining the flat soffit and pier faces."""
    rounded = []
    bends = {3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16}
    for i, middle in enumerate(points):
        if i not in bends:
            rounded.append(middle)
            continue

        def toward(p):
            length = math.dist(p, middle)
            scale = min(0.40, 0.48 / length)
            return tuple(v + scale * (a - v) for v, a in zip(middle, p))

        a, b = toward(points[i - 1]), toward(points[i + 1])
        for j in range(7):
            t = j / 6
            rounded.append(tuple((1-t)**2 * u + 2*t*(1-t) * m + t*t*v for u, m, v in zip(a, middle, b)))
    return rounded


def moulded_shell(points):
    """Monotone cubic sections pass through each of the original shell stations."""
    def slope(a, b, c):
        left, right = b - a, c - b
        return 2 * left * right / (left + right) if left * right > 0 else 0.0

    slopes = [tuple(b - a for a, b in zip(points[0], points[1]))]
    for i in range(1, len(points) - 1):
        slopes.append(tuple(slope(*xyz) for xyz in zip(points[i - 1], points[i], points[i + 1])))
    slopes.append(tuple(b - a for a, b in zip(points[-2], points[-1])))
    result = []
    for i, (a, b) in enumerate(zip(points, points[1:])):
        for j in range(4):
            t = j / 4
            h = t*t*(3 - 2*t)
            result.append(tuple((1-h)*u + h*v + t*(1-t)**2*m - t*t*(1-t)*n
                                for u, v, m, n in zip(a, b, slopes[i], slopes[i+1])))
    return result + [points[-1]]


def dial_paint(path):
    """Draw the sixty printed divisions on enamel. Both hands are separate pieces of metal."""
    import numpy as np
    from PIL import Image
    from paint import noise

    size = 1024
    yy, xx = (np.indices((size, size), dtype=np.float32) + 0.5) * 256 / size
    x, y = xx - 127.5, yy - 127.5
    radius = np.hypot(x, y)
    rng = np.random.default_rng(2511)
    broad = noise(rng, size, size, 23, 28)
    pores = noise(rng, size, size, 151, 169)
    varnish = np.clip((radius - 92 + 1.5 * broad) / 22, 0, 1)**2 * np.clip((yy - 75) / 133, 0.1, 1)
    face = (np.array([202, 187, 146]) - varnish[..., None] * np.array([8, 14, 20])
            + (1.4 * broad + 0.45 * pores)[..., None])
    face = np.where((radius > 112.7)[..., None], (124, 122, 96), face)
    face = np.where((radius > 115.8)[..., None], (56, 64, 62), face)
    face = np.where((radius > 121.2)[..., None], (133, 136, 120), face)

    angle = np.arctan2(x, -y)
    minute = np.rint(angle * 60 / math.tau).astype(int)
    relative = angle - minute * math.tau / 60
    major = minute % 5 == 0
    along, across = radius * np.cos(relative), np.abs(radius * np.sin(relative))
    inside = np.minimum(np.minimum(along - np.where(major, 86, 100), 107 - along),
                        np.where(major, 3, 1) - across)
    coverage = np.clip(0.5 + inside * 3.1, 0, 1)
    face += coverage[..., None] * (np.array([48, 59, 56]) - face)
    rgba = np.empty((size, size, 4), dtype=np.uint8)
    rgba[..., :3] = np.clip(face + 0.5, 0, 255).astype(np.uint8)
    rgba[..., 3] = (255 * np.clip((124.8 - radius)*3.5, 0, 1)).astype(np.uint8)
    Image.fromarray(rgba).save(path / "clock.png")


def dial_hands(g):
    from layout import dial

    mesh, cyl = g["mesh"], g["cyl"]
    enamel = g["solid"]("baked graphite on the clock hands", "303633", 0.49, 0.18)
    spindle = g["solid"]("aged brass clock spindle", "695648", 0.42, 0.45)
    slot = g["solid"]("spindle slot", "413c36", 0.68)
    for side in (1, -1):
        def point(x, z, depth):
            return dial(side * x, z, side * depth)

        for angle, length, half, depth in ((math.tau * 4.75/12, 0.254, 0.026, 0.231),
                                            (math.tau * 45/60, 0.386, 0.016, 0.245)):
            sine, cosine = math.sin(angle), math.cos(angle)
            rim = [(-half * 0.64, -0.019), (half * 0.64, -0.019), (half, 0.037),
                   (half * 0.83, length - 0.020), (half * 0.52, length),
                   (-half * 0.52, length), (-half * 0.83, length - 0.020), (-half, 0.037)]
            vertices = [point(t*cosine + along*sine, -t*sine + along*cosine, plane)
                        for plane in (depth, depth+0.004) for t, along in rim]
            n = len(rim)
            faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2*n))]
            faces += [(i, (i+1)%n, n+(i+1)%n, n+i) for i in range(n)]
            mesh(vertices, [face if side > 0 else face[::-1] for face in faces], enamel)
        cyl(point(0,0,0.225), point(0,0,0.248), 0.035, enamel, 56)
        cyl(point(0,0,0.249), point(0,0,0.254), 0.026, spindle, 64, 0.022)
        g["beam"](point(-0.009,-0.003,0.2542), point(0.009,0.003,0.2542), 0.0025, 0.0014, slot)
