"""The city docks across the ferry basin. Dimensions are metres."""

import math
from random import Random
from mathutils import Vector


def draw_shore(g):
    box, quad, mesh, beam, cyl = (g[k] for k in ("box", "quad", "mesh", "beam", "cyl"))
    node, link = g["node"], g["link"]

    def surface(name, dark, light, air, stretch=(0.6, 0.6, 0.25)):
        mat = g["weather"](name, dark, light, 0.55, stretch, 0.78, 0)
        tree = mat.node_tree
        mist = node(mat, "ShaderNodeEmission")
        mist.inputs["Color"].default_value = g["rgba"]("c7d1d2")
        mix = node(mat, "ShaderNodeMixShader")
        mix.inputs[0].default_value = air
        link(mat, tree.nodes.get("Principled BSDF").outputs[0], mix.inputs[1])
        link(mat, mist.outputs[0], mix.inputs[2])
        link(mat, mix.outputs[0], tree.nodes.get("Material Output").inputs["Surface"])
        return mat

    paving = surface("rain on the port apron", "8c9692", "a6afab", 0.29)
    masonry = surface("granite quay blocks", "737f80", "a0a5a0", 0.23, (0.4, 0.48, 0.7))
    tidemark = surface("salt at ordinary high water", "8c9186", "a6aaa0", 0.24)
    wet = surface("wet base of the sea wall", "617575", "808a86", 0.23)
    edging = surface("worn stone coping", "a4a69a", "c0c2b4", 0.30)
    timber = surface("wharf fender timber", "494f50", "737771", 0.21)
    iron = surface("weathered quay iron", "495b60", "738381", 0.20)
    brick = surface("weathered dock brick", "8c7973", "ada096", 0.30)
    mortar = surface("warehouse parapet stone", "969a94", "b9b9a9", 0.33)
    frame = surface("ship hall concrete piers", "8e9590", "b3b2a4", 0.27)
    sheet = surface("blue grey zinc on the repair hall", "829699", "a0adae", 0.27)
    sheet_end = surface("riveted end of the repair hall", "697e83", "8e999a", 0.25)
    roof = surface("rain washed northlight roofs", "939c9e", "b9bcb6", 0.31)
    glazing = surface("wired factory glass", "899b9b", "bdc5be", 0.28)
    shutter = surface("sliding door leaves", "586d72", "7d8c8d", 0.23)
    shadow = surface("deep door and window reveals", "475559", "677675", 0.27)
    wheel = surface("crane bogies and hinge castings", "45545b", "647474", 0.20)
    steel = surface("old lead blue crane enamel", "566b70", "859592", 0.17)
    light_steel = surface("rain lit edges of the luffing jib", "788c8e", "a4b1a9", 0.20)
    cab_glass = surface("shadow inside the operator cab", "415860", "718383", 0.17)
    rng = Random(2806)

    # The repair basin cuts into the continuous quay. Its north and south
    # returns are visible from different panes. The yard slab continues inland.
    level = 0.65
    stations = [(-520, 126, 226), (126, 203, 201), (203, 257, 230),
                (257, 368, 211), (368, 479, 235), (479, 1045, 220)]
    for i, (y0, y1, x) in enumerate(stations):
        box(x, 845, y0, y1, -5.5, level, paving)
        box(x - 0.08, x + 0.04, y0, y1, -4.55, level - 0.18, masonry)
        box(x - 0.14, x + 0.03, y0, y1, -4.55, -2.22, wet)
        box(x - 0.13, x + 0.06, y0, y1, -1.21, -1.02, tidemark)
        box(x - 0.37, x + 0.60, y0, y1, level - 0.28, level + 0.08, edging)
        for y in range(y0 + 5, y1 - 2, 13):
            # Fenders almost touch the water at low tide. A bollard sits on
            # the coping behind every second pair, clear of the crane track.
            box(x - 0.48, x - 0.10, y - 0.24, y + 0.24, -2.96, level - 0.20, timber)
            box(x - 0.48, x - 0.10, y + 0.54, y + 0.92, -2.96, level - 0.20, timber)
            if (y - y0 - 5) % 26 == 0:
                cyl((x + 1.13, y, level), (x + 1.13, y, level + 0.71), 0.34, iron, 10, 0.41)
        if i:
            other = stations[i - 1][2]
            x0, x1 = sorted((x, other))
            face = y0 + (-0.05 if x < other else 0.05)
            box(x0, x1, face - 0.05, face + 0.05, -4.55, level - 0.13, masonry)
            box(x0, x1, face - 0.11, face + 0.11, -4.55, -2.22, wet)
            box(x0 - 0.10, x1 + 0.16, face - 0.42, face + 0.42, level - 0.26, level + 0.08, edging)

    # A full-width ship-repair shop. Its roofs run back into the site, leaving
    # the northlight profile, brick infill and the two tall doors on the quay.
    def northlight_shop(x, y, bays, spacing, depth):
        eave, crest, drop = 7.85, 11.25, 1.02
        length = bays * spacing
        box(x, x + depth, y, y + length, level, eave, sheet)
        box(x - 0.19, x + 0.06, y, y + length, level, 1.70, brick)
        box(x, x + depth, y - 0.08, y + 0.07, level, eave, sheet_end)
        for j in range(bays):
            lo, hi = y + j * spacing, y + (j + 1) * spacing
            ridge = hi - drop
            for side, m in ((x, sheet_end), (x + depth, sheet)):
                mesh([(side, lo, eave), (side, ridge, crest), (side, hi, eave)], [(0, 1, 2)], m)
            quad((x - 0.23, lo - 0.09, eave + 0.02), (x + depth + 0.24, lo - 0.09, eave + 0.02),
                 (x + depth + 0.24, ridge, crest + 0.14), (x - 0.23, ridge, crest + 0.14), roof)
            quad((x - 0.15, ridge, crest + 0.12), (x + depth + 0.15, ridge, crest + 0.12),
                 (x + depth + 0.15, hi, eave + 0.01), (x - 0.15, hi, eave + 0.01), glazing)
            beam((x - 0.28, ridge, crest + 0.13), (x + depth + 0.27, ridge, crest + 0.13), 0.18, 0.16, frame)
            for n in range(1, int(depth / 3.2) + 1):
                px = x + 3.1 * n
                beam((px, ridge, crest + 0.15), (px, hi, eave + 0.03), 0.075, 0.08, frame)
            cy = (lo + hi) / 2
            box(x - 0.23, x + 0.05, lo, lo + 0.32, level, eave + 0.02, frame)
            box(x - 0.08, x + 0.02, lo + 0.6, hi - 0.5, 6.18, 7.17, glazing)
            for sy in (lo + 2.6, cy, hi - 2.5):
                box(x - 0.16, x - 0.07, sy - 0.065, sy + 0.065, 6.13, 7.20, frame)
            if j in (1, 2):
                box(x - 0.12, x - 0.025, cy - 3.8, cy + 3.8, level, 5.82, shadow)
                box(x - 0.16, x - 0.11, cy - 3.55, cy + 3.43, level + 0.08, 5.57, shutter)
                box(x - 0.19, x - 0.15, cy - 0.06, cy + 0.06, level + 0.08, 5.57, shadow)
                box(x - 0.43, x + 0.03, cy - 4.02, cy + 4.02, 5.76, 6.05, frame)
            else:
                for sy in (lo + 2.1, hi - 2.1):
                    box(x - 0.09, x - 0.04, sy - 0.92, sy + 0.92, 2.57, 4.66, glazing)
                    box(x - 0.13, x - 0.07, sy - 0.06, sy + 0.06, 2.51, 4.71, frame)
        # Broad sliding gable door, seen down the side lane in three quarters.
        box(x + 3, x + depth - 3, y - 0.13, y - 0.08, level, 6.38, shutter)
        box(x + depth * 0.51, x + depth * 0.51 + 0.10, y - 0.17, y - 0.13, level, 6.38, shadow)
    northlight_shop(237.5, 240.0, 4, 10.3, 23.4)

    def warehouse(x, y, depth, length, storeys):
        high = level + storeys * 3.5 + 0.64
        box(x, x + depth, y, y + length, level, high, brick)
        box(x - 0.23, x + depth + 0.23, y - 0.22, y + length + 0.22, high - 0.65, high - 0.32, mortar)
        box(x + 0.48, x + depth - 0.48, y + 0.48, y + length - 0.48, high, high + 0.19, roof)
        box(x - 0.12, x + 0.38, y - 0.12, y + length + 0.12, high, high + 0.31, brick)
        box(x, x + depth, y - 0.12, y + 0.36, high, high + 0.31, brick)
        for level_i in range(storeys):
            sill = level + level_i * 3.5 + 0.86
            for j in range(int(length / 4.5)):
                lo = y + 1.4 + j * 4.5
                box(x - 0.07, x - 0.02, lo, lo + 2.15, sill, sill + 1.92, shadow)
                box(x - 0.14, x - 0.07, lo - 0.14, lo + 2.28, sill - 0.13, sill + 0.02, mortar)
                box(x - 0.12, x - 0.07, lo + 1.02, lo + 1.13, sill, sill + 1.92, mortar)
            for j in range(int(depth / 4.3)):
                lo = x + 1.38 + j * 4.3
                box(lo, lo + 1.92, y - 0.065, y - 0.01, sill, sill + 1.94, shutter)
        for j in range(0, int(length) + 1, 9):
            box(x - 0.26, x + 0.1, y + j, y + j + 0.39, level + 0.09, high - 0.65, brick)
        # The surviving lift overrun stands on the inner stair core.
        box(x + depth - 8, x + depth - 2.4, y + length - 9, y + length - 3, high, high + 2.65, brick)
        box(x + depth - 8.2, x + depth - 2.2, y + length - 9.2, y + length - 2.8, high + 2.62, high + 2.90, mortar)
    warehouse(263, 196, 16.8, 25, 3)
    warehouse(280, 335, 17.3, 27.4, 3)

    # Three grain bins and their elevator occupy the next berth. The gallery
    # joins the elevator head to the ridge over the bins; all sit on one raft.
    silo = surface("salted concrete of the grain bins", "929791", "bdbbb0", 0.36)
    silo_rim = surface("zinc caps of the grain bins", "879696", "aeb9b5", 0.35)
    sx, sy = 264.0, 374.0
    box(sx - 4.4, sx + 13, sy - 4.4, sy + 19.5, level, 1.34, frame)
    for cy_bin in (sy, sy + 7.42, sy + 14.84):
        cyl((sx, cy_bin, 1.34), (sx, cy_bin, 15.03), 3.54, silo, 32)
        cyl((sx, cy_bin, 14.91), (sx, cy_bin, 15.19), 3.63, silo_rim, 32)
        cyl((sx, cy_bin, 15.19), (sx, cy_bin, 16.55), 3.62, silo_rim, 32, 0.70)
    bx, by = sx + 9.0, sy + 12.3
    box(bx - 2.48, bx + 2.48, by - 2.73, by + 2.73, 1.29, 17.94, frame)
    box(bx - 2.72, bx + 2.72, by - 3.0, by + 3.0, 17.71, 20.54, silo)
    box(bx - 2.86, bx + 2.86, by - 3.12, by + 3.12, 20.53, 20.84, silo_rim)
    box(bx - 2.78, bx - 2.72, by - 2.0, by + 1.98, 18.36, 19.48, shutter)
    box(sx - 0.47, sx + 0.47, sy - 0.52, sy + 15.31, 16.51, 17.51, sheet)
    beam((sx, by, 17.1), (bx - 2.35, by, 18.30), 1.10, 1.12, silo_rim)
    # The adjoining yard is kept low enough to see the round shoulders.

    # A travelling portal crane has four wheel groups, a slewing house, an
    # A-frame, a luffing jib and a slack-free hoist hanging over the water.
    cx, cy = 209.6, 162.8
    for sx in (-4.15, 4.15):
        box(cx + sx - 0.11, cx + sx + 0.11, 128.5, 200.5, level + 0.04, level + 0.27, wheel)
        for sy in (-4.15, 4.15):
            foot = (cx + sx, cy + sy, level + 0.90)
            shoulder = (cx + sx * 0.56, cy + sy * 0.56, 9.86)
            box(cx + sx - 0.53, cx + sx + 0.53, cy + sy - 1.43, cy + sy + 1.43, level + 0.26, level + 1.12, wheel)
            beam(foot, shoulder, 0.70, 0.84, steel)
        beam((cx + sx, cy - 4.15, 1.88), (cx + sx, cy + 4.15, 1.88), 0.49, 0.58, steel)
        beam((cx + sx * 0.78, cy - 3.2, 5.67), (cx + sx * 0.56, cy + 2.45, 9.76), 0.27, 0.32, steel)
    box(cx - 2.85, cx + 2.85, cy - 2.95, cy + 2.95, 9.44, 10.44, steel)
    cyl((cx, cy, 10.4), (cx, cy, 11.04), 2.35, wheel, 24)
    direction = Vector((-0.995, -0.097, 0)).normalized()
    transverse = Vector((-direction.y, direction.x, 0))
    def crane(t, s, z):
        return Vector((cx, cy, z)) + direction * t + transverse * s
    def house(t0, t1, s0, s1, z0, z1, mat):
        pts = [crane(t, s, z) for z in (z0, z1) for t, s in ((t0, s0), (t1, s0), (t1, s1), (t0, s1))]
        mesh(pts, [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], mat)
    house(-4.9, 2.6, -2.07, 2.07, 11.02, 11.68, steel)
    house(-4.23, 0.72, -1.73, 1.68, 11.68, 14.32, steel)
    house(-4.4, 0.89, -1.87, 1.83, 14.30, 14.52, light_steel)
    house(0.2, 2.44, 0.15, 1.98, 11.75, 14.04, light_steel)
    house(2.43, 2.47, 0.29, 1.85, 12.62, 13.84, cab_glass)
    house(0.58, 2.26, 1.97, 2.02, 12.64, 13.84, cab_glass)
    house(-4.88, -3.91, -1.86, 1.86, 11.63, 13.28, wheel)
    for s in (-1.06, 1.06):
        beam(crane(-3.58, s, 14.36), crane(-1.22, s * 0.80, 18.9), 0.24, 0.28, steel)
        beam(crane(0.81, s, 13.34), crane(-1.22, s * 0.80, 18.9), 0.23, 0.26, steel)
        beam(crane(-1.22, s * 0.80, 18.9), crane(22.8, s * 0.34, 20.85), 0.10, 0.11, steel)
    beam(crane(-1.22, -0.92, 18.9), crane(-1.22, 0.92, 18.9), 0.31, 0.29, wheel)
    # Four angle-iron chords, laced on each face. The section tapers at the sheave.
    def corner(t, s, h):
        belly = math.sin(math.pi * t)**0.9
        half = 0.35 + 0.44 * belly + 0.20 * (1 - t)
        height = 0.40 + 0.81 * belly + 0.26 * (1 - t)
        return crane(1.72 + 23.15 * t, s * half, 12.21 + 8.60 * t + h * height)
    for j in range(8):
        t, u = j / 8, (j + 1) / 8
        for s in (-1, 1):
            for h in (-1, 1):
                beam(corner(t, s, h), corner(u, s, h), 0.21, 0.23, light_steel if h > 0 else steel)
            beam(corner(t, s, 1 if j % 2 else -1), corner(u, s, -1 if j % 2 else 1), 0.15, 0.16, steel)
            beam(corner(t, s, -1), corner(t, s, 1), 0.115, 0.12, steel)
        beam(corner(t, -1, 1), corner(u, 1, 1), 0.13, 0.13, steel)
    nose = crane(24.87, 0, 20.81)
    cyl(nose - transverse * 0.55, nose + transverse * 0.55, 0.49, wheel, 12)
    for s in (-0.22, 0.22):
        beam(crane(24.87, s, 20.82), crane(24.87, s, 13.0), 0.085, 0.09, wheel)
    cyl(crane(24.87, 0, 12.64), crane(24.87, 0, 13.27), 0.30, wheel, 8)
    g["pipe"]([crane(24.87, 0, 12.7), crane(24.85, 0, 12.05),
               crane(24.57, 0, 11.91), crane(24.30, 0, 12.16)], 0.10, wheel, 8)

    # City blocks step inland along three streets. Faces, service courts,
    # setbacks and roof plant give each group depth through the rain.
    rear = surface("distant blue grey city", "9aa9ad", "b7bdbe", 0.73)
    rear_win = surface("distant street glazing", "809299", "9ba9ab", 0.70)
    city = [surface("old cream city render", "a9aaa2", "c2c2b6", 0.57),
            surface("grey warehouses inland", "8f9fa4", "b0b8b7", 0.55),
            surface("dull brick above the port", "a19691", "bbb2a8", 0.58)]
    city_win = surface("damp city sashes", "71868d", "91a2a5", 0.54)
    cornice = surface("city roof courses", "9daaaa", "b9bdb6", 0.58)

    def block(x, y, depth, length, floors, skin, windows, cap, detail=True):
        h = floors * 3.12 + 1.2
        box(x, x + depth, y, y + length, level, h, skin)
        box(x - 0.17, x + depth + 0.17, y - 0.17, y + length + 0.17, h - 0.24, h + 0.19, cap)
        for j in range(floors):
            sill = level + j * 3.12 + 0.74
            for f in range(int(length / 3.9)):
                a = y + 1.15 + f * 3.9
                box(x - 0.07, x - 0.02, a, a + 1.9, sill, sill + 1.44, windows)
            if detail:
                for f in range(int(depth / 4.55)):
                    a = x + 1.4 + f * 4.55
                    box(a, a + 2.05, y - 0.09, y - 0.02, sill, sill + 1.45, windows)
        if floors >= 5 and detail:
            inset = rng.uniform(1.5, 3.4)
            box(x + inset, x + depth - 1.2, y + 3.0, y + length - 3.5, h, h + 2.5, skin)
            box(x + depth * 0.54, x + depth * 0.54 + 4.2, y + length * 0.54, y + length * 0.54 + 4.6, h + 2.45, h + 4.1, cap)
    for args in [(379, 255, 14, 19, 6, 0), (384, 282, 21, 25, 4, 1), (403, 309, 17, 24, 5, 2),
                 (416, 367, 19, 21, 5, 2), (396, 396, 16, 19, 7, 1), (398, 418, 16, 17, 5, 0),
                 (378, 477, 20, 30, 4, 0), (388, 512, 17, 17, 5, 2), (408, 566, 16, 29, 6, 1),
                 (397, 604, 22, 30, 4, 2), (400, 653, 16, 19, 5, 0)]:
        x, y, d, l, f, k = args
        block(x, y, d, l, f, city[k], city_win, cornice)
    for x, y, d, l, f in [(542, 350, 24, 40, 6), (551, 421, 24, 26, 8), (558, 455, 19, 32, 7),
                       (550, 525, 18, 25, 9), (564, 553, 22, 30, 7), (560, 627, 20, 47, 5),
                       (559, 702, 19, 25, 8), (557, 734, 21, 32, 6), (566, 815, 16, 42, 7), (545, 910, 17, 30, 6)]:
        block(x, y, d, l, f, rear, rear_win, rear, False)

    # Long glossy facets appear in loose bands where the wind drops. Draw
    # the two faces just above the water. Their widths and spacing foreshorten
    # on the same plane as the pontoon, and their pointed ends meet the water.
    sky_face = surface("cloud reflected in calm water", "becbca", "ced3c9", 0.25)
    cool_face = surface("water in the wake of a gust", "697f80", "8c9c97", 0.16)
    water_rng = Random(1132)
    for bx, by, count in [(45, 41, 3), (59, 46, 3), (63, 55, 3), (68, 65, 4),
                        (84, 74, 3), (96, 70, 3), (107, 96, 5), (131, 109, 4),
                        (72, 94, 3), (50, 76, 3), (57, 64, 3), (82, 132, 4),
                        (105, 157, 4), (95, 49, 3), (121, 91, 3)]:
        for i in range(count):
            x = bx + water_rng.uniform(-3.4, 3.4)
            y = by + i * 1.6 + water_rng.uniform(-0.42, 0.42)
            angle = water_rng.uniform(-0.57, -0.33)
            along = (math.cos(angle), math.sin(angle))
            across = (-along[1], along[0])
            length = water_rng.uniform(2.1, 5.1)
            width = water_rng.uniform(0.68, 1.68)
            drift = water_rng.uniform(-0.42, 0.42)
            side = sky_face if water_rng.random() < 0.57 else cool_face
            def crest(t, f):
                envelope = max(0, math.sin(t * math.pi))**0.74
                h = (t - 0.5) * length
                v = envelope * (f * width + drift * math.sin(1.8 * math.pi * t))
                return (x + h * along[0] + v * across[0], y + h * along[1] + v * across[1],
                        -3.196 + 0.062 * envelope * (1.0 - abs(f)))
            for k in range(5):
                t, u = k / 5, (k + 1) / 5
                quad(crest(t, -0.76), crest(u, -0.76), crest(u, 0), crest(t, 0), side)
                if i % 3 == 1:
                    quad(crest(t, 0), crest(u, 0), crest(u, 0.49), crest(t, 0.49), sky_face)

    water = g["water"]
    bs = water.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Roughness"].default_value = 0.23
    bs.inputs["Coat Weight"].default_value = 0.18
    bs.inputs["Coat Roughness"].default_value = 0.19
    # Two short wave trains cross the basin. Warped crests turn toward and
    # away from the grey sky in patches. The water underneath is continuous.
    geo = node(water, "ShaderNodeNewGeometry").outputs["Position"]
    gust = node(water, "ShaderNodeTexNoise")
    gust.inputs["Scale"].default_value = 0.124
    gust.inputs["Detail"].default_value = 1.8
    link(water, geo, gust.inputs["Vector"])

    def calculate(operation, first, second=None):
        n = node(water, "ShaderNodeMath")
        n.operation = operation
        for value, socket in zip((first, second), n.inputs):
            if value is None:
                continue
            if isinstance(value, (float, int)):
                socket.default_value = value
            else:
                link(water, value, socket)
        return n.outputs[0]

    def wave(vector, warp):
        along = node(water, "ShaderNodeVectorMath")
        along.operation = "DOT_PRODUCT"
        link(water, geo, along.inputs[0])
        along.inputs[1].default_value = vector
        bend = calculate("MULTIPLY", gust.outputs["Fac"], warp)
        return calculate("SINE", calculate("ADD", along.outputs["Value"], bend))

    main = wave((1.27, 2.73, 0), 6.1)
    short = wave((1.88, 4.77, 0), -5.3)
    crests = calculate("ADD", main, calculate("MULTIPLY", short, 0.42))
    strength = calculate("MULTIPLY", crests, calculate("ADD", 0.23, gust.outputs["Fac"]))
    bump = node(water, "ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.76
    bump.inputs["Distance"].default_value = 0.094
    link(water, strength, bump.inputs["Height"])
    link(water, bs.inputs["Normal"].links[0].from_socket, bump.inputs["Normal"])
    link(water, bump.outputs["Normal"], bs.inputs["Normal"])
    link(water, bump.outputs["Normal"], bs.inputs["Coat Normal"])
