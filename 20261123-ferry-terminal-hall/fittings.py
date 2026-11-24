"""Period fittings and small signs of salt, wind and human use in the terminal."""

import math
from random import Random
from layout import CLOCK, dial as clock, timetable_point


def pocket_timetable(g):
    # An opened three-panel leaflet. The first fold has risen; the outer
    # corners have stuck to the floor. Set the printed sheet onto those folds.
    stock = g["texture"]("water-softened timetable", "pocket-timetable.png", 0.93)[0]
    verts = [timetable_point(i / 6, v) for v in (0.0, 0.48, 1.0) for i in range(7)]
    faces, uvs = [], []
    for j, (v0, v1) in enumerate(((0.0, 0.48), (0.48, 1.0))):
        for i in range(6):
            a = j * 7 + i
            faces.append((a, a + 1, a + 8, a + 7))
            u0, u1 = i / 6, (i + 1) / 6
            uvs.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    g["mesh"](verts, faces, stock, uvs)


def add(g, *, large=False):
    box, beam, cyl, pipe, quad, mesh = (g[k] for k in ("box", "beam", "cyl", "pipe", "quad", "mesh"))
    (
        steel,
        iron,
        wood,
        cream,
        dark,
        tar,
        rust,
        teal,
        sub,
        ledge,
        concrete,
        shutter,
        dolphin,
        farsteel,
        glass,
    ) = (
        g[k]
        for k in (
            "steel",
            "iron",
            "wood",
            "cream",
            "dark",
            "tar",
            "rust",
            "teal",
            "sub",
            "ledge",
            "concrete",
            "shutter",
            "dolphin",
            "farsteel",
            "glass",
        )
    )
    weather, solid = g["weather"], g["solid"]
    rng = Random(64201)
    paper = weather("abandoned paper", "aaa899", "cccbab", 3.3, (1, 1, 1), 0.94, 0.002)
    flake = weather("tide litter", "58583f", "85816a", 3.3, (1, 1, 0.6), 0.89, 0.004)
    fabric = weather("linen sunshade", "9b9f8e", "c3c2a7", 2, (1.4, 2.2, 0.22), 0.95, 0.006)
    old = fabric.node_tree.nodes.get("Principled BSDF")
    dest = fabric.node_tree.nodes.get("Material Output")
    trans = g["node"](fabric, "ShaderNodeBsdfTranslucent")
    trans.inputs[0].default_value = (0.47, 0.50, 0.40, 1)
    mixed = g["node"](fabric, "ShaderNodeMixShader")
    mixed.inputs[0].default_value = 0.63
    g["link"](fabric, old.outputs[0], mixed.inputs[1])
    g["link"](fabric, trans.outputs[0], mixed.inputs[2])
    g["link"](fabric, mixed.outputs[0], dest.inputs[0])
    sleeve = weather("dark enamel clock", "234941", "49645b", 3, (1, 1, 0.8), 0.45, 0.006, 0.33)
    wire = solid("salt rope", "827d63", 0.95)
    # One face reads on the landing, the other from the boarding approach.
    cx, cy, cz = CLOCK
    r = 0.607
    cyl(clock(0, 0, -0.20), clock(0, 0, 0.15), r, sleeve, 80)
    cyl(clock(0, 0, 0.15), clock(0, 0, 0.20), r, sleeve, 80, r - 0.025)
    cyl(clock(0, 0, 0.201), clock(0, 0, 0.218), r - 0.026, steel, 80, r - 0.034)
    cyl(clock(0, 0, -0.22), clock(0, 0, -0.197), r - 0.012, steel, 80, r)
    a = r - 0.034
    for side, depth in ((1, 0.222), (-1, -0.224)):
        quad(
            clock(-side * a, -a, depth),
            clock(side * a, -a, depth),
            clock(side * a, a, depth),
            clock(-side * a, a, depth),
            g["clockface"],
            True,
        )
    if large:
        from large_details import dial_hands
        dial_hands(g)
    # The beam soffit is 6.89 m high here. Fasten the pipe to its exposed face.
    cyl((cx, cy, cz + r * 0.97), (cx, cy, 6.86), 0.052, iron)
    cyl((cx, cy, cz + r * 0.94), (cx, cy, cz + r + 0.106), 0.10, steel)
    box(cx - 0.166, cx + 0.166, cy - 0.151, cy + 0.151, 6.846, 6.905, iron)
    cyl((cx, cy, 6.792), (cx, cy, 6.857), 0.089, steel)
    for dx in (-0.114, 0.114):
        for dy in (-0.104, 0.104):
            cyl((cx + dx, cy + dy, 6.831), (cx + dx, cy + dy, 6.851), 0.023, steel, 6)
    for t in (0, 0.5, 1):
        aa = t * math.pi + math.pi / 2
        cyl(
            clock(math.cos(aa) * 0.585, math.sin(aa) * 0.585, 0.192),
            clock(math.cos(aa) * 0.585, math.sin(aa) * 0.585, 0.214),
            0.014,
            iron,
            7,
        )
    # Wire from the back of the clock to the ceiling rose.
    pipe(
        [
            clock(0.20, 0.53, -0.08),
            (cx + 0.28, cy + 0.07, 6.36),
            (cx + 0.16, cy + 0.04, 6.53),
            (cx + 0.13, cy + 0.04, 6.851),
        ],
        0.011,
        tar,
        6,
    )
    # The glazing has a rolled, torn strip of sun blind in one bay only.
    from layout import BLIND_Y, blind_hem
    ya, yb = BLIND_Y
    cyl((10.33, ya, 6.29), (10.33, yb, 6.29), 0.098, fabric, 16)
    for k in range(36):

        def edge(j, h):
            s = j / 36
            hem = blind_hem(s)
            zz = 6.28 + (hem - 6.28) * h
            return (
                10.32 - 0.12 * h - 0.045 * math.cos(s * 12) * h,
                ya + s * (yb - ya),
                zz,
            )

        for j in range(4):
            quad(
                edge(k, j / 4),
                edge(k + 1, j / 4),
                edge(k + 1, (j + 1) / 4),
                edge(k, (j + 1) / 4),
                fabric,
            )
        if k < 29:
            beam(edge(k, 1), edge(k + 1, 1), 0.019, 0.032, ledge)
    pipe(
        [
            (10.24, yb, 6.30),
            (10.22, yb - 0.03, 4.44),
            (10.22, yb - 0.05, 4.38),
            (10.23, yb - 0.09, 4.44),
            (10.25, yb - 0.08, 6.25),
        ],
        0.008,
        wire,
        6,
    )
    # The pier beyond the right-hand panes has lost its gangway. Two pairs of guide piles remain.
    for x, y, h, lean in [
        (18.3, 12.4, 2.57, 0.15),
        (18.96, 12.91, 2.18, -0.06),
        (19.24, 13.64, 2.78, 0.12),
        (23.2, 17.5, 1.93, -0.11),
        (23.62, 17.95, 2.17, 0.10),
        (27.7, 32.6, 1.93, 0.07),
        (28.1, 32.64, 1.65, 0.02),
    ]:
        cyl((x + lean, y - 0.07, -3.18), (x, y, h), 0.20, dolphin, 14, 0.147)
        for z in [h - 0.49, h - 0.57]:
            cyl((x + 0.018, y, z), (x + 0.018, y, z + 0.032), 0.17, iron, 12)
        cyl((x, y, h - 0.33), (x, y, h - 0.06), 0.151, cream, 14)
    beam((19.02, 13.0, -0.91), (23.5, 18.30, -0.91), 2.26, 0.46, farsteel)
    beam((19.12, 12.39, 0.12), (23.45, 17.69, 0.12), 0.042, 0.056, farsteel)
    for k in range(5):
        t = k / 4
        cyl(
            (19.12 + 4.33 * t, 12.39 + 5.30 * t, -0.68),
            (19.12 + 4.33 * t, 12.39 + 5.30 * t, 0.14),
            0.033,
            farsteel,
        )
    # A handful of tidal ladders and remoter mooring works. Value falls off with distance.
    for x, y in [(18.6, 12.83), (27.8, 32.52)]:
        for dx in [-0.27, 0.27]:
            cyl((x + dx, y - 0.23, -3), (x + dx, y - 0.23, 0.67), 0.026, farsteel, 8)
        for k in range(11):
            cyl(
                (x - 0.27, y - 0.23, -2.87 + k * 0.31),
                (x + 0.27, y - 0.23, -2.87 + k * 0.31),
                0.022,
                farsteel,
                8,
            )
    # Two surviving downpipes. The main one jogs past the sill and disappears into the drain.
    for y in [2.07, 13.77]:
        pipe(
            [
                (10.05, y, 0.07),
                (10.05, y, 1.04),
                (10.07, y, 1.15),
                (10.22, y, 1.31),
                (10.27, y, 1.42),
                (10.27, y, 6.76),
            ],
            0.073,
            steel,
            12,
        )
        for z in [0.31, 2.0, 3.83, 5.68]:
            cyl(
                (10.25 if z > 1 else 10.05, y, z),
                (10.25 if z > 1 else 10.05, y, z + 0.05),
                0.087,
                iron,
                12,
            )
    # Shallow iron drains stand flush with the slabs. The paper curls up along just one edge.
    for x, y in [(3.15, -2.08), (8.84, 5.05), (9.45, -2.20)]:
        box(x - 0.33, x + 0.33, y - 0.21, y + 0.21, 0.006, 0.017, iron)
        box(x - 0.29, x + 0.29, y - 0.175, y + 0.175, 0.018, 0.021, dark)
        for j in range(13):
            box(
                x - 0.28 + j * 0.045,
                x - 0.259 + j * 0.045,
                y - 0.172,
                y + 0.172,
                0.021,
                0.025,
                iron,
            )
    pocket_timetable(g)
    for x, y, a, scale in [
        (2.91, -1.91, 0.41, 0.81),
        (3.34, -2.10, -0.75, 0.47),
        (8.45, 4.33, -0.92, 0.59),
    ]:

        def paperpt(u, v, h):
            return (
                x + scale * (u * math.cos(a) - v * math.sin(a)),
                y + scale * (u * math.sin(a) + v * math.cos(a)),
                0.009 + h,
            )

        cols = [(-0.15, 0.008), (-0.09, 0.009), (0.083, 0.001), (0.145, 0.061)]
        for (a0, h0), (a1, h1) in zip(cols, cols[1:]):
            quad(
                paperpt(a0, -0.145, h0),
                paperpt(a1, -0.14, h1),
                paperpt(a1, 0.145, h1 * 0.42),
                paperpt(a0, 0.15, h0 * 0.42),
                paper,
            )
        for j in range(3):
            quad(
                paperpt(-0.08, -0.09 + j * 0.046, 0.011),
                paperpt(0.055, -0.09 + j * 0.046, 0.010),
                paperpt(0.055, -0.079 + j * 0.046, 0.011),
                paperpt(-0.08, -0.079 + j * 0.046, 0.012),
                sub,
            )
    for x, y, rad, count in [
        (3.04, -2.13, 0.66, 22),
        (9.70, 2.0, 0.7, 20),
        (-2.65, 9.29, 1.2, 15),
        (6.52, 5.15, 0.36, 6),
    ]:
        for _ in range(count):
            xx = x + rng.gauss(0, 0.38) * rad
            yy = y + rng.gauss(0, 0.32) * rad
            a = rng.uniform(0, math.tau)
            l = rng.uniform(0.034, 0.091)
            wid = l * 0.27
            pts = [
                (xx - l * math.cos(a), yy - l * math.sin(a), 0.009),
                (xx - wid * math.sin(a), yy + wid * math.cos(a), 0.017),
                (xx + l * math.cos(a), yy + l * math.sin(a), 0.02),
                (xx + wid * math.sin(a), yy - wid * math.cos(a), 0.008),
            ]
            quad(*pts, flake)
    # Salt-stiff sea grass where a little expansion joint has broken by the glass.
    for x, y, count in [(10.14, 1.48, 16), (9.98, 9.35, 9), (10.15, 1.75, 7)]:
        for i in range(count):
            dx = rng.uniform(-0.14, 0.14)
            dy = rng.uniform(-0.17, 0.17)
            h = rng.uniform(0.12, 0.48)
            w = rng.uniform(0.009, 0.017)
            a = (x + dx / 8, y + dy / 8, 0.018)
            b = (x + dx * 0.45, y + dy * 0.45, h * 0.75)
            c = (x + dx, y + dy, h * (0.78 + rng.random() * 0.22))
            mesh(
                [a, (a[0] + w, a[1], a[2]), (b[0] + w * 0.5, b[1], b[2]), b, c],
                [(0, 1, 2, 3), (3, 2, 4)],
                flake,
            )
    # A tired control cabinet and an exposed conduit beside the boarding passage.
    box(8.93, 9.48, 15.79, 16.04, 1.04, 1.87, teal)
    box(9.36, 9.41, 15.75, 15.81, 1.39, 1.51, steel)
    pipe(
        [
            (9.11, 15.92, 1.05),
            (9.11, 15.92, 0.64),
            (9.19, 15.91, 0.54),
            (10.23, 15.91, 0.54),
            (10.32, 15.89, 0.47),
        ],
        0.023,
        iron,
    )
    # Light rust weeps and aggregate scars on the main castings respect the concrete faces.
    stains = [
        weather("oxide wash", "726e59", "8c826b", 2, (3, 1, 0.25), 0.88, 0.002),
        weather("cement spall", "858b79", "a7a18c", 3, (2, 1, 0.7), 0.91, 0.003),
    ]
    for yy in [-2, 5.3, 12.6]:
        for i in range(44):
            x = rng.uniform(6.145, 6.755)
            z = rng.choice([1.81, 3.64, 5.44, 0.7]) + rng.uniform(-0.11, 0.12)
            le = rng.uniform(0.018, 0.32)
            w = rng.uniform(0.006, 0.033)
            mesh(
                [
                    (x, yy - 0.254, z),
                    (x + w, yy - 0.254, z + 0.016),
                    (x + w * 0.82, yy - 0.254, z - le * 0.66),
                    (x + w * 0.3, yy - 0.254, z - le),
                ],
                [(0, 1, 2, 3)],
                stains[i % 2],
            )
