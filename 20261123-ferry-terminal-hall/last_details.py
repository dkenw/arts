"""The folded boarding gate, pier wall, landing rail and boarding fittings."""

import math
from random import Random


def add(g):
    box, beam, cyl, pipe, quad, mesh = (g[k] for k in ("box", "beam", "cyl", "pipe", "quad", "mesh"))
    iron, steel, teal, wood, ledge, rust, cream, shutter, sub, tar, glass = (
        g[k]
        for k in (
            "iron",
            "steel",
            "teal",
            "wood",
            "ledge",
            "rust",
            "cream",
            "shutter",
            "sub",
            "tar",
            "glass",
        )
    )
    weather, texture = g["weather"], g["texture"]
    rng = Random(72183)
    bone = weather("washed lime", "a3aa96", "c3bfa6", 1.6, (2, 2, 0.40), 0.91, 0.004)
    verdigris = weather("patinated copper", "515f50", "7e8670", 1.3, (2, 2, 0.56), 0.59, 0.008, 0.32)
    # A retractable gate, pulled two thirds shut. Its diamond links share every pivot.
    start, end, y, bot, top = 4.70, 7.35, 16.28, 0.20, 2.54
    box(4.53, 8.77, 16.18, 16.43, 2.58, 2.67, iron)
    box(start - 0.06, start + 0.03, y - 0.09, y + 0.08, 0.07, 2.57, steel)
    for i in range(10):
        xa = start + (end - start) * i / 10
        xb = start + (end - start) * (i + 1) / 10
        box(xa - 0.016, xa + 0.016, y - 0.02, y + 0.018, bot, top, shutter)
        for j in range(3):
            z = bot + j * (top - bot) / 3
            dz = (top - bot) / 3
            beam((xa, y - 0.035, z), (xb, y - 0.035, z + dz), 0.022, 0.035, steel)
            beam((xa, y - 0.053, z + dz), (xb, y - 0.053, z), 0.021, 0.031, iron)
            cyl(
                ((xa + xb) / 2, y - 0.060, z + dz * 0.5),
                ((xa + xb) / 2, y - 0.07, z + dz * 0.5),
                0.021,
                cream,
                8,
            )
    box(end - 0.03, end + 0.02, y - 0.045, y + 0.04, 0.09, 2.61, iron)
    box(end - 0.09, end - 0.05, y - 0.088, y - 0.06, 0.96, 1.15, steel)
    # The counters were stripped first. A galvanised chain now stays across the
    # two queue mouths, on lugs welded to the existing front stanchions.
    chain = weather("dulled galvanised chain", "645f51", "928b76", 2.8, (1, 1, 1), 0.52, 0.004, 0.53)
    for x in (4.97, 6.42, 8.07):
        box(x - 0.035, x + 0.035, 12.92, 12.98, 0.86, 0.94, iron)
    for xa, xb, drop in [(4.97, 6.42, 0.235), (6.42, 8.07, 0.28)]:
        count = round((xb - xa) / 0.051)
        pitch = (xb - xa) / count
        for i in range(count + 1):
            t = i / count
            x = xa + (xb - xa) * t
            z = 0.902 - 4 * drop * t * (1 - t)
            slope = 4 * drop * (2 * t - 1) / (xb - xa)
            # Alternating link planes prevent the chain from reading as a wire.
            tilt = 0.14 if i % 2 else 1.14
            ring = []
            for q in range(13):
                a = q * math.tau / 12
                dx = 0.71 * pitch * math.cos(a)
                v = 0.021 * math.sin(a)
                ring.append(
                    (
                        x + dx,
                        12.917 + v * math.sin(tilt),
                        z + slope * dx + v * math.cos(tilt),
                    )
                )
            pipe(ring, 0.0068, chain, 6)
    # Pillar-mounted emergency connection and conduit with its offset around the slab joint.
    for yy in [5.3, 12.6]:
        x = 6.82
        pipe(
            [
                (x, yy - 0.15, 0.26),
                (x, yy - 0.15, 2.15),
                (x, yy - 0.12, 2.22),
                (x, yy - 0.09, 2.3),
                (x, yy - 0.09, 5.26),
                (6.85, yy - 0.06, 5.44),
                (7.35, yy - 0.06, 6.0),
            ],
            0.021,
            steel,
            8,
        )
        for z in [0.65, 1.92, 3.64, 4.75]:
            box(6.79, 6.86, yy - 0.16, yy - 0.02, z, z + 0.043, iron)
    # Small screw heads, utility fixtures, and the missing kick plate on the berth jamb.
    box(3.92, 4.17, 15.88, 16.02, 0.98, 1.46, teal)
    box(3.98, 4.095, 15.85, 15.89, 1.12, 1.26, iron)
    for x in (3.95, 4.14):
        for z in (1.01, 1.42):
            cyl((x, 15.875, z), (x, 15.858, z), 0.012, steel, 7)
    # A tiny coastal service enamel on the passage lintel, a thick glass cover on the route board.
    sign = texture("boarding plaque", "boarding.png", 0.57)[0]
    box(4.83, 7.02, 15.87, 16.02, 3.30, 3.81, teal)
    g["fronttex"](4.88, 6.97, 15.854, 3.34, 3.76, sign)
    # A crack that grew out of a frame fixing. Its faint branches stop inside a single pane.
    for y, z, fl in [(2.18, 1.95, 1), (9.79, 4.61, -1)]:
        x = 10.51
        for arr in [
            [(0, 0), (0.17, 0.09), (0.26, 0.255), (0.44, 0.29), (0.64, 0.49)],
            [(0.26, 0.255), (0.23, 0.38), (0.30, 0.54)],
            [(0.17, 0.09), (0.21, -0.03), (0.30, -0.12)],
        ]:
            pts = [(x, y + dy * fl, z + dz) for dy, dz in arr]
            pipe(pts, 0.005, steel, 5)
    # A flat bronze expansion strip breaks off where it meets the wet tiles.
    for x0, x1 in [
        (-9.9, -5.3),
        (-4.9, 0.63),
        (0.68, 3.75),
        (3.80, 6.9),
        (7.02, 10.06),
    ]:
        box(x0, x1, -1.32, -1.293, 0.002, 0.009, verdigris)
    # Back-office ventilator and ticket ledge. The blank glass slots have a physical thickness.
    box(-1.97, -1.07, 15.88, 16.026, 3.05, 3.49, iron)
    for k in range(6):
        box(-1.93, -1.11, 15.849, 15.885, 3.09 + k * 0.059, 3.11 + k * 0.059, shutter)
    for x in [-10.6, -7.87, -5.2]:
        box(x - 0.17, x + 0.17, 9.92, 10.36, 1.09, 1.13, steel)
    # Paper follows the shutter ribs. The lower right corner has come away from the paste.
    notice = texture("withdrawal circular", "withdrawn.png", 0.92)[0]

    def on_shutter(u, v):
        x = -6.28 + 0.58 * u - 0.017 * (v - 0.5)
        z = 1.37 + 0.777 * v + 0.014 * (u - 0.5)
        fold = 0.055 * max(0.0, (u - 0.58) / 0.42) ** 2 * max(0.0, (0.42 - v) / 0.42) ** 2
        return (
            x,
            10.538 - 0.004 * math.cos((z - 1.14) * math.tau / 0.107) - fold,
            z + fold * 0.25,
        )

    cols, rows = 5, 22
    verts, faces, uvs = [], [], []
    for j in range(rows + 1):
        for i in range(cols + 1):
            verts.append(on_shutter(i / cols, j / rows))
    for j in range(rows):
        for i in range(cols):
            q = j * (cols + 1) + i
            faces.append((q, q + 1, q + cols + 2, q + cols + 1))
            uvs.append(
                [
                    (i / cols, j / rows),
                    ((i + 1) / cols, j / rows),
                    ((i + 1) / cols, (j + 1) / rows),
                    (i / cols, (j + 1) / rows),
                ]
            )
    mesh(verts, faces, notice, uvs)
    # The rim of the upper landing: brass cuffs interrupt the timber, held on cast brackets.
    for yy in [-11.35, -10.22, -9.52]:
        x = -4.87
        cyl((x, yy - 0.043, 4.508), (x, yy + 0.043, 4.508), 0.068, verdigris, 16)
        box(x - 0.041, x + 0.041, yy - 0.071, yy + 0.071, 4.36, 4.43, iron)
    # Three panels of much older roughcast remain below the municipal enamel.
    for k in range(28):
        x = rng.uniform(-11.1, -4.6)
        z = rng.uniform(0.18, 0.91)
        l = rng.uniform(0.027, 0.19)
        if (int(x * 4) + k) % 3 == 0:
            quad(
                (x, 10.304, z),
                (x + l * 0.6, 10.304, z + 0.018),
                (x + l, 10.304, z + 0.067),
                (x + l * 0.15, 10.304, z + 0.042),
                bone,
            )
    # Fine cracks in the floor stop or turn at expansion joints.
    for x, y, heading, length in [
        (6.16, 5.06, -1.78, 1.62),
        (6.12, -2.2, -2.78, 1.83),
        (2.84, -1.96, -2.83, 1.18),
        (-1.49, 0.41, -0.93, 0.72),
    ]:
        dx, dy = math.cos(heading), math.sin(heading)
        at = (x, y)
        for k in range(15):
            t = length * (k + 1) / 15
            shift = rng.uniform(-0.037, 0.037) * (1 + 0.35 * math.sin(k))
            to = (x + t * dx - dy * shift, y + t * dy + dx * shift)
            wid = 0.010 * (1 - 0.40 * k / 15)
            quad(
                (at[0] - dy * wid, at[1] + dx * wid, 0.006),
                (to[0] - dy * wid, to[1] + dx * wid, 0.006),
                (to[0] + dy * wid, to[1] - dx * wid, 0.006),
                (at[0] + dy * wid, at[1] - dx * wid, 0.006),
                sub,
            )
            at = to
