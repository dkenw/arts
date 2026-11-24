"""The floating pontoon and its lifting posts seen through the east glazing."""

import math


def add(g):
    box, beam, cyl, pipe, quad, mesh = (g[k] for k in ("box", "beam", "cyl", "pipe", "quad", "mesh"))
    sea = g["farsteel"]
    post = g["dolphin"]
    pale = g["ledge"]
    weather = g["weather"]
    green = weather(
        "salt-grey marine steel", "727f78", "9ca59a", 1.15, (1.6, 1.6, 0.34), 0.68, 0.008, 0.19
    )
    old = weather("outer jetty timbers", "687770", "9a9b88", 2.0, (0.42, 2, 1), 0.85, 0.012)
    zinc = weather("tide staff ivory", "a1a797", "cac9ae", 2, (1, 1, 0.4), 0.68, 0.005)
    x0, y0, x1, y1 = 11.72, 23.12, 22.08, 12.84
    L = math.hypot(x1 - x0, y1 - y0)
    dx = (x1 - x0) / L
    dy = (y1 - y0) / L

    def station(t, s, h):
        return (x0 + (x1 - x0) * t - dy * s, y0 + (y1 - y0) * t + dx * s, 0.04 - 1.72 * t + h)

    box(7.63, 11.79, 21.73, 24.53, -0.29, -0.015, sea)
    for side in [-0.86, 0.86]:
        beam(station(0, side, -0.13), station(1, side, -0.13), 0.17, 0.23, sea)
        for t in [i / 12 for i in range(13)]:
            beam(station(t, side, 0.01), station(t, side, 1.03), 0.055, 0.049, sea)
        for z in [0.48, 1.03]:
            cyl(station(0, side, z), station(1, side, z), 0.030, sea, 8)
        for k in range(0, 11, 2):
            beam(station(k / 12, side, 0.06), station((k + 1) / 12, side, 0.86), 0.022, 0.035, sea)
    for j in range(54):
        t = j / 54
        pts = [
            station(t, -0.85, 0),
            station(t, 0.85, 0),
            station(t + 0.017, 0.85, 0),
            station(t + 0.017, -0.85, 0),
        ]
        quad(*pts, old)
    # At low water the pontoon is down near the waterline and the guide posts stand tall.
    points = [
        station(t, s, -0.06 + 1.72 * (t - 1))[:2]
        for t, s in [(0.93, -1.8), (0.93, 1.8), (1.25, 1.8), (1.25, -1.8)]
    ]
    g["slab_polygon"](points, -3.61, -1.73, green)
    for s in [-1.42, 1.42]:
        x, y, _ = station(1.016, s, 0)
        cyl((x, y, -3.45), (x, y, 3.91), 0.143, green, 14)
        cyl((x, y, 3.48), (x, y, 3.73), 0.154, zinc, 14)
        box(x - 0.145, x + 0.145, y - 0.145, y + 0.145, 3.78, 3.88, pale)
        cyl((x, y, -2.18), (x, y, -0.62), 0.22, old, 12)
    a, b = station(1.016, -1.42, 0), station(1.016, 1.42, 0)
    beam((a[0], a[1], 3.84), (b[0], b[1], 3.84), 0.16, 0.23, green)
    ax, ay = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    beam((a[0], a[1], 3.0), (ax, ay, 3.80), 0.083, 0.092, green)
    beam((b[0], b[1], 3.0), (ax, ay, 3.80), 0.083, 0.092, green)
    for s in [-0.63, 0.63]:
        x, y, _ = station(1.016, s, 0)
        cyl((x - 0.07, y, 3.62), (x + 0.07, y, 3.62), 0.134, old, 16)
        pipe([(x, y, 3.59), (x + 0.03, y - 0.02, 1.41), (x + 0.10, y - 0.04, -1.43)], 0.016, sea, 6)
    # Legible tide staff with a cadenced ten-centimetre scale at one outside guide.
    x, y = b[0] - 0.11, b[1] - 0.13
    box(x - 0.068, x + 0.068, y - 0.026, y + 0.03, -2.71, 2.72, zinc)
    for k in range(27):
        z = -2.60 + k * 0.19
        box(x - 0.065, x + (0.063 if k % 5 == 0 else 0.009), y - 0.038, y - 0.026, z, z + 0.06, post)
