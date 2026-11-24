"""The shutter-side litter bin, the windward sill and a traveller's small chalk drawing."""

import math
from random import Random
from layout import BIN_CENTRE, BIN_HEADING, BOAT_PANEL, SILL_JOINT


def litter_bin(g):
    # A pressed-steel municipal bin, tucked against the round end of the kiosk.
    # The side-entry hood is hollow, so the bright rim throws a real shadow into the liner.
    mesh, cyl, pipe = (g[k] for k in ("mesh", "cyl", "pipe"))
    weather = g["weather"]
    body = weather("old smoke-blue bin enamel", "576568", "99a19a", 3.8, (1, 1, 0.6), 0.54, 0.005, 0.32)
    cap = weather("spun galvanised bin hood", "7e8b86", "b5b8aa", 4.3, (1, 1, 0.7), 0.44, 0.003, 0.52)
    edge = weather("worn bin beading", "8b9491", "b8bba8", 4, (1, 1, 1), 0.42, 0.002, 0.56)
    interior = weather("sheltered galvanised liner", "263432", "485451", 4, (1, 1, 0.7), 0.86, 0.003, 0.18)
    sole = g["tar"]
    x, y = BIN_CENTRE
    direction = BIN_HEADING
    n = 80

    def vertex(t, rad, z, flute=0):
        r = rad + flute * (0.46 + 0.54 * math.cos(t * 16)) ** 3
        return (x + r * math.cos(t), y + r * math.sin(t), z)

    def turned(profile, material, flute=False):
        vertices = []
        for rad, z in profile:
            amplitude = (
                0.0065 * min(1, max(0, (z - 0.085) / 0.055), max(0, (0.568 - z) / 0.045)) if flute else 0
            )
            vertices.extend(vertex(i * math.tau / n, rad, z, amplitude) for i in range(n))
        faces = []
        for j in range(len(profile) - 1):
            for i in range(n):
                a = j * n + i
                b = j * n + (i + 1) % n
                faces.append((a, b, b + n, a + n))
        mesh(vertices, faces, material, smooth=True)

    turned([(0.195, 0.008), (0.218, 0.011), (0.232, 0.032), (0.232, 0.058), (0.216, 0.070)], sole)
    turned(
        [
            (0.218, 0.046),
            (0.241, 0.059),
            (0.248, 0.083),
            (0.245, 0.106),
            (0.256, 0.553),
            (0.261, 0.571),
            (0.267, 0.584),
            (0.262, 0.602),
            (0.250, 0.615),
        ],
        body,
        True,
    )
    turned([(0.244, 0.083), (0.250, 0.088), (0.250, 0.097), (0.245, 0.102)], cap)
    turned([(0.248, 0.601), (0.248, 0.576), (0.222, 0.548), (0.206, 0.126), (0.004, 0.123)], interior)
    turned([(0.254, 0.573), (0.270, 0.581), (0.271, 0.595), (0.266, 0.607), (0.252, 0.606)], edge)
    # Cut an arch in both skins, then join the cut edges with a folded metal return.
    profile = [
        (0.257, 0.595),
        (0.267, 0.621),
        (0.269, 0.646),
        (0.268, 0.661),
        (0.266, 0.687),
        (0.264, 0.712),
        (0.259, 0.738),
        (0.254, 0.764),
        (0.248, 0.789),
        (0.239, 0.812),
        (0.229, 0.836),
        (0.216, 0.855),
        (0.201, 0.871),
        (0.179, 0.890),
        (0.138, 0.909),
        (0.082, 0.921),
        (0.006, 0.927),
    ]
    rings = len(profile)
    stride = n * rings
    verts = []
    for inner in (False, True):
        for rad, z in profile:
            verts.extend(
                vertex(i * math.tau / n, max(0.002, rad - 0.012 * inner), z - 0.008 * inner) for i in range(n)
            )

    def cut(i, j):
        theta = (i + 0.5) * math.tau / n
        offset = abs(math.atan2(math.sin(theta - direction), math.cos(theta - direction)))
        z = (profile[j][1] + profile[j + 1][1]) * 0.5
        if offset > 0.99 or z < 0.646:
            return False
        return z < 0.768 + 0.073 * math.sqrt(max(0, 1 - (offset / 0.99) ** 2))

    outer = []
    inside = []
    trims = []
    for j in range(rings - 1):
        for i in range(n):
            if cut(i, j):
                continue
            a = j * n + i
            b = j * n + (i + 1) % n
            q = (a, b, b + n, a + n)
            outer.append(q)
            inside.append(tuple(v + stride for v in q[::-1]))
            for k, (di, dj) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
                jj = j + dj
                if 0 <= jj < rings - 1 and cut((i + di) % n, jj):
                    v0, v1 = q[k], q[(k + 1) % 4]
                    trims.append((v1, v0, v0 + stride, v1 + stride))
    mesh(verts, outer, cap, smooth=True)
    mesh(verts, inside, interior, smooth=True)
    mesh(verts, trims, edge)
    cyl((x, y, 0.920), (x, y, 0.928), 0.010, cap, 14)
    # Enamel maker's plate with two rivets; the moulded ribs stop at the shoulder.
    cs, sn = math.cos(direction), math.sin(direction)

    def front(u, depth, z):
        return (x + depth * cs - u * sn, y + depth * sn + u * cs, z)

    plaque = [
        front(u, d, z)
        for u, d, z in [
            (-0.066, 0.259, 0.438),
            (0.066, 0.259, 0.438),
            (0.066, 0.259, 0.484),
            (-0.066, 0.259, 0.484),
        ]
    ]
    mesh(plaque, [(0, 1, 2, 3)], g["teal"])
    for u in (-0.052, 0.052):
        cyl(front(u, 0.259, 0.461), front(u, 0.266, 0.461), 0.0048, edge, 7)
    pipe([front(-0.027, 0.260, 0.464), front(0.027, 0.260, 0.464)], 0.0037, edge, 6)


def wall_marks(g):
    mesh, quad, texture = (g[k] for k in ("mesh", "quad", "texture"))
    runoff = texture("water and mineral under the leaking sill", "sill-runoff.png", 0.77, True)[0]
    bloom = texture("wicked moisture at the pier foot", "pier-bloom.png", 0.85, True)[0]
    chalk = texture("chalked paper boat", "chalk-boat.png", 0.94, True)[0]

    def side_patch(x, near, far, low, high, material):
        quad((x, far, low), (x, near, low), (x, near, high), (x, far, high), material, True)

    side_patch(10.416, SILL_JOINT - 0.89, SILL_JOINT + 0.87, 0.007, 1.006, runoff)
    side_patch(10.416, *BOAT_PANEL, chalk)

    # Wrap the capillary line around one corner, including the two faces of its foot.
    corner = 0.50 / 1.17

    def face(p0, p1, low, high, u0, u1):
        verts = [(*p0, low), (*p1, low), (*p1, high), (*p0, high)]
        mesh(
            verts,
            [(0, 1, 2, 3)],
            bloom,
            [[(u0, low / 0.55), (u1, low / 0.55), (u1, high / 0.55), (u0, high / 0.55)]],
        )

    face((6.117, -1.75), (6.117, -2.251), 0.150, 0.55, 0, corner)
    face((6.120, -2.254), (6.79, -2.254), 0.150, 0.55, corner, 1)
    face((6.077, -1.716), (6.077, -2.284), 0.003, 0.150, 0, corner)
    face((6.080, -2.288), (6.83, -2.288), 0.003, 0.150, corner, 1)

    # Deposits on the inside of the fixed pane below the upper sash. The frame
    # itself interrupts the runs at the transom and above the sill.
    scale, bs = g["base"]("dried runs beside the glazing rebate", "9b9e91", 0.83)
    bs.inputs["Alpha"].default_value = 0.29
    rng = Random(4625)
    for offset, start, end, width in [
        (-0.092, 5.548, 3.67, 0.016),
        (-0.116, 4.64, 2.52, 0.011),
        (-0.182, 3.04, 1.20, 0.019),
        (-0.068, 2.76, 1.21, 0.013),
    ]:
        steps = 26
        edge = []
        for k in range(steps + 1):
            t = k / steps
            y = SILL_JOINT + offset + 0.009 * math.sin(t * 5.6 + offset * 31) + 0.004 * math.sin(13 * t)
            z = start + (end - start) * t
            w = width * (1 - 0.57 * t) * (0.77 + rng.random() * 0.42)
            edge.append(((10.551, y - w, z), (10.551, y + w, z)))
        for k, (e, f) in enumerate(zip(edge, edge[1:])):
            if k % 12 not in (8, 9):
                quad(e[0], e[1], f[1], f[0], scale)


def add(g):
    litter_bin(g)
    wall_marks(g)
