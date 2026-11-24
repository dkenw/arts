"""Native-pixel brushwork. Marks are projected from metre coordinates and tested for visibility."""

import json
import math
from collections import defaultdict
from random import Random
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from plaster_stain import print_seepage
from layout import BANKS, PITCH, DRIP, dial, floor_height, LIFTED, feet, on_bank
from layout import BIN_CENTRE, BIN_HEADING, BOAT_LINES, boat_point, wick_height, SILL_JOINT, timetable_point
from layout import RING_CENTRE


def draw(scene, graph, fname, *, large=False):
    W, H = (scene.render.resolution_x, scene.render.resolution_y) if large else (528, 396)
    rng = Random(18048)
    cam = scene.camera
    eye = cam.location.copy()

    def project(pt):
        a = world_to_camera_view(scene, cam, Vector(pt))
        return (a.x * W, (1 - a.y) * H)

    def visible(q):
        d = Vector(q) - eye
        length = d.length
        d.normalize()
        origin = eye
        for _ in range(8):
            room = length - (origin - eye).length - 0.029
            if room < 0.005:
                return True
            hit, loc, _, _, obj, _ = scene.ray_cast(graph, origin, d, distance=room)
            if not hit:
                return True
            if obj.name not in (
                "suspended sea air",
                "low air above the inlet",
                "salt-hazed glass",
                "rain-washed transom",
                "clear rooflight",
            ):
                return False
            origin = loc + d * 0.04
        return False

    marks = []

    # Widths are fractions of a pixel on the original print. On the large
    # sheet a scuffed edge can have a soft shoulder and a sharp centre.
    widths = {"nickel": 0.42, "varnish": 0.52, "spall": 0.47, "hairline": 0.29,
              "water": 0.33, "mineral": 0.42, "paper fold": 0.33, "chalk": 0.42,
              "blue ink": 0.38, "rust ink": 0.38, "glass": 0.32, "rope shade": 0.36,
              "linen": 0.41, "cork paint": 0.46}

    def samples(pts):
        for p, q in zip(pts, pts[1:]):
            pp, qq = project(p), project(q)
            n = max(1, math.ceil(max(abs(pp[0] - qq[0]), abs(pp[1] - qq[1])) * 1.6))
            for k in range(n + 1):
                t = k / n
                pos = tuple(a + (b - a) * t for a, b in zip(p, q))
                yield project(pos), pos

    def pixel_line(pts, kind, strength=1):
        pixels = {}
        for (u, v), pos in samples(pts):
            x, y = math.floor(u), math.floor(v)
            if 0 <= x < W and 0 <= y < H and (x, y) not in pixels and visible(pos):
                pixels[x, y] = None
        if pixels:
            marks.append([kind, strength, list(pixels)])

    def fine_line(pts, kind, strength=1):
        radius = max(0.36, 0.5 * widths.get(kind, 0.51) * W / 528)
        reach = radius + 0.5
        coverage = {}
        for (u, v), pos in samples(pts):
            if not (-reach < u < W + reach and -reach < v < H + reach and visible(pos)):
                continue
            y0, y1 = max(0, math.ceil(v - reach - 0.5)), min(H, math.floor(v + reach - 0.5) + 1)
            x0, x1 = max(0, math.ceil(u - reach - 0.5)), min(W, math.floor(u + reach - 0.5) + 1)
            for y in range(y0, y1):
                for x in range(x0, x1):
                    weight = round(32 * min(1.0, reach - math.hypot(x + 0.5 - u, y + 0.5 - v)))
                    if weight > coverage.get((x, y), 0):
                        coverage[x, y] = weight
        batches = defaultdict(list)
        for pixel, weight in coverage.items():
            batches[weight].append(pixel)
        for weight, pixels in batches.items():
            marks.append([kind, strength * weight / 32, pixels])

    mark = fine_line if large else pixel_line

    # At twelve pixels wide the leaflet reads through its cover, printed
    # headings, and raised fold. Reserve a few clusters for those marks.
    def on_sheet(u0, v0, u1, v1, ink, amount):
        mark([timetable_point(u0 + (u1 - u0) * i / 8, v0 + (v1 - v0) * i / 8) for i in range(9)], ink, amount)

    on_sheet(0.04, 0.85, 0.287, 0.85, "blue ink", 1.16)
    on_sheet(0.06, 0.73, 0.28, 0.73, "rust ink", 0.70)
    on_sheet(0.36, 0.90, 0.61, 0.90, "blue ink", 0.81)
    on_sheet(0.71, 0.90, 0.94, 0.90, "blue ink", 0.76)
    on_sheet(1 / 3, 0.14, 1 / 3, 0.72, "paper fold", 1.06)
    on_sheet(0.68, 0.22, 0.70, 0.56, "blue ink", 0.57)
    # Only two timetable rules survive at this scale, with a break at the fold.
    on_sheet(0.43, 0.43, 0.58, 0.43, "blue ink", 1.34)
    on_sheet(0.75, 0.44, 0.91, 0.44, "blue ink", 0.98)
    on_sheet(0.80, 0.09, 0.95, 0.09, "paper fold", 0.48)

    # Three areas on the polished bezel catch the harbour windows.
    def bezel(t, r=0.579, deep=0.215):
        x = r * math.cos(t)
        z = r * math.sin(t)
        return dial(x, z, deep)

    for a, b, k in [(32, 63, 0.75), (66, 91, 0.45), (-75, -59, 0.40)]:
        mark([bezel(math.radians(a + (b - a) * i / 12)) for i in range(13)], "nickel", k)
    # Little directional chips on the shell lips. Skip the absent seat.
    for cx, cy, theta, seats in BANKS:
        for k, material in enumerate(seats):
            if material is None:
                continue
            center = (k - (len(seats) - 1) * 0.5) * PITCH

            def seat(x, y, z):
                x += center
                return (
                    cx + x * math.cos(theta) - y * math.sin(theta),
                    cy + x * math.sin(theta) + y * math.cos(theta),
                    z,
                )

            for a, b in [(-0.21, -0.14), (0.055, 0.152)]:
                mark(
                    [seat(a, -0.398, 0.932), seat(b, -0.398, 0.928)],
                    "nickel",
                    rng.uniform(0.46, 0.88),
                )

    # The front cheek and surviving varnish share the actual stair curve.
    def hand(s, zfrac=0):
        t = s / 10.65
        return (
            -6.61 - 10.65 + (10.65 + 1.74 + 0.025) * math.cos(t),
            -9.12 + (10.65 + 1.74 + 0.025) * math.sin(t),
            3.528 - s * 0.168 / 0.335 + 0.98 + 0.050 + zfrac,
        )

    for a, b in [
        (0.08, 0.15),
        (0.54, 0.77),
        (0.80, 0.88),
        (1.22, 1.36),
        (2.61, 2.95),
        (4.21, 4.33),
    ]:
        mark([hand(a), hand(b)], "varnish", 0.74)
    for x, y, dx, dy in [
        (-4.852, -9.65, 0, 0.14),
        (-4.85, -10.09, 0, 0.16),
        (-4.855, -11.05, 0, 0.055),
    ]:
        mark([(x, y, 4.559), (x + dx, y + dy, 4.559)], "varnish", 0.75)
    # Aggregate exposed near the corners, darker drips only at the form joints.
    for y in [-2.0, 5.3, 12.6]:
        for side in [0, 1]:
            for _ in range(22):
                a = rng.uniform(0.03, 0.95)
                h = rng.choice([0.32, 0.60, 1.80, 3.64]) + rng.uniform(-0.12, 0.08)
                du = rng.uniform(0.009, 0.054)
                dh = rng.uniform(0.014, 0.071)
                if side == 0:
                    p = (6.12 + 0.66 * a, y - 0.261, h)
                    q = (p[0] + du, y - 0.261, h + dh)
                else:
                    p = (6.113, y - 0.25 + 0.50 * a, h)
                    q = (6.113, p[1] + du, h + dh)
                mark([p, q], "spall", rng.uniform(0.23, 0.76))
        for x in (6.18, 6.43, 6.71):
            mark(
                [
                    (x, y - 0.263, 3.62),
                    (x + 0.009, y - 0.263, 3.46 - rng.uniform(0, 0.20)),
                ],
                "bleed",
                0.38,
            )
    # Surface fissures radiate from the old fixings. They stop at the next construction joint.
    for x, z, dx, dz, L in [
        (3.97, 4.66, -0.67, -0.72, 1.26),
        (-0.79, 4.67, 0.51, 0.78, 0.80),
        (8.91, 2.98, 0.34, 0.82, 0.82),
        (2.12, 5.35, -0.55, 0.88, 0.64),
    ]:
        a = (x, 16.025, z)
        for k in range(13):
            j = k + 1
            b = (
                x + dx * L * j / 13 + rng.uniform(-0.043, 0.043),
                16.025,
                z + dz * L * j / 13 + rng.uniform(-0.023, 0.023),
            )
            if k not in [3, 8, 11]:
                mark([a, b], "hairline", 0.57 - 0.021 * k)
            if k == 6:
                mark(
                    [
                        b,
                        (b[0] + 0.13, 16.025, b[2] - 0.06),
                        (b[0] + 0.22, 16.025, b[2] - 0.18),
                    ],
                    "hairline",
                    0.28,
                )
            a = b
    # Sparse brush streaks on the most exposed window, left alone wherever the sash occludes it.
    for y in [2.01, 4.66, 7.61, 10.43, 13.94]:
        for _ in range(6):
            yy = y + rng.uniform(-0.07, 0.12)
            z = rng.choice([4.66, 1.33, 5.59]) + rng.uniform(-0.04, 0.07)
            mark(
                [(10.49, yy, z), (10.49, yy + 0.009, z - rng.uniform(0.11, 0.38))],
                "glass",
                rng.uniform(0.21, 0.58),
            )
    for a, b in [(1.91, 2.3), (3.82, 4.38), (5.12, 5.77), (7.96, 8.38), (10.77, 11.38)]:
        mark([(10.28, a, 1.143), (10.28, b, 1.143)], "nickel", 0.47)
    # Thin, broken ripple arcs below the nose of the leaking window sill.
    cx, cy, base = DRIP
    for j, r in enumerate([0.28, 0.56, 0.73, 0.94]):
        for a, b in [(0.30, 0.71), (2.72, 3.27), (4.14, 4.56)]:
            if j == 0 and a > 2:
                continue
            rad = r * base
            mark(
                [
                    (
                        cx + rad * math.cos(a + (b - a) * k / 10),
                        cy + rad * math.sin(a + (b - a) * k / 10),
                        floor_height(cx) + 0.009,
                    )
                    for k in range(11)
                ],
                "water",
                0.76 - 0.10 * j,
            )
    # The chalk is paler along the pressure side of a stroke. Its short folds
    # remain visible after resolving a slanting wall to the native grid.
    for points, weight in zip(BOAT_LINES, (0.78, 0.89, 0.53, 0.39)):
        mark([boat_point(u, v) for u, v in points], "chalk", weight)
    # Two dark tongues of runoff and a discontinuous mineral edge. All marks
    # lie on the low wall directly below the failed joint.
    for off, t0, t1, ink, weight in [
        (0.009, 0.05, 0.38, "damp", 0.89),
        (0.009, 0.49, 0.73, "damp", 0.63),
        (-0.15, 0.11, 0.48, "damp", 0.78),
        (0.17, 0.04, 0.25, "mineral", 0.82),
        (0.22, 0.39, 0.55, "mineral", 0.68),
        (-0.25, 0.57, 0.73, "mineral", 0.66),
        (-0.34, 0.83, 0.94, "mineral", 0.54),
    ]:
        pts = []
        for j in range(11):
            t = t0 + (t1 - t0) * j / 10
            drift = 0.032 * math.sin(t * 4.8) - 0.060 * t + 0.013 * math.sin(t * 19)
            pts.append((10.413, SILL_JOINT + off + drift, 1.004 - 0.993 * t))
        mark(pts, ink, weight)
    # The pale lip of the damp patch follows exposed aggregate in three places.
    for lo, hi, weight in [
        (-0.18, -0.08, 0.69),
        (-0.046, 0.11, 0.79),
        (0.18, 0.29, 0.54),
        (0.47, 0.55, 0.43),
    ]:
        pts = []
        for k in range(13):
            u = lo + (hi - lo) * k / 12
            x, y = (6.114, -2.25 - u) if u < 0 else (6.12 + u, -2.257)
            pts.append((x, y, wick_height(u) + 0.007 * math.sin(u * 71)))
        mark(pts, "mineral", weight)

    # One side of the hood catches the window. Break the glint at the seam.
    def rim(angle, rad, z):
        return (BIN_CENTRE[0] + rad * math.cos(angle), BIN_CENTRE[1] + rad * math.sin(angle), z)

    for a, b, rad, z, weight in [
        (0.17, 0.59, 0.235, 0.838, 0.74),
        (0.30, 0.68, 0.271, 0.591, 0.72),
        (-0.24, 0.02, 0.269, 0.596, 0.36),
    ]:
        mark([rim(BIN_HEADING + a + (b - a) * k / 8, rad, z) for k in range(9)], "nickel", weight)

    # Trace the rust at the rear bolts of the three removed seat feet.
    cx, cy, turn, count = LIFTED
    for x, y in [on_bank(cx, cy, turn, side, -0.22) for side in feet(count)]:
        for a, b in [(0.20, 2.16), (3.8, 5.25)]:
            mark(
                [
                    (
                        x + 0.06 * math.cos(a + (b - a) * k / 9),
                        y + 0.075 * math.sin(a + (b - a) * k / 9),
                        0.013,
                    )
                    for k in range(10)
                ],
                "oxide",
                0.68,
            )
    print_seepage(scene, W, H, project, visible, marks)
    window_fittings(mark)
    with open(fname, "w") as f:
        json.dump(marks, f, separators=(",", ":"))


def window_fittings(mark):
    # The pivot and the underside of the tilted sash appear against open sky.
    # Only short stretches of the folded alloy catch the morning light.
    tilt = math.radians(23)
    nose_x, nose_z = 10.53 - 1.09 * math.sin(tilt), 6.68 - 1.09 * math.cos(tilt)
    for start, stop in ((0.27, 0.48), (1.52, 1.94)):
        lip = [(nose_x - 0.032, SILL_JOINT - u, nose_z + 0.024) for u in (start, stop)]
        mark(lip, "nickel", 0.63)
    for y in (SILL_JOINT - 0.096, SILL_JOINT - 2.92 + 0.096):
        mark([(10.488, y, 5.633), (10.468, y, 5.625)], "nickel", 0.83)

    # Brush the actual front of the cork ring. The warm paint is interrupted
    # by four linen-coloured sleeves. Only a little of each crest is lit.
    cx, cy, cz = RING_CENTRE

    def cork(angle, tube_angle):
        radius = 0.34 + 0.063 * math.cos(tube_angle)
        return (cx + radius * math.cos(angle), cy + 0.063 * math.sin(tube_angle), cz + radius * math.sin(angle))

    def band(start, stop, outer, inner, ink, strength):
        path = []
        for i in range(5):
            along = start + (stop - start) * i / 4
            for j in range(6):
                across = (j if i % 2 == 0 else 5 - j) / 5
                path.append(cork(along, outer + (inner - outer) * across))
        mark(path, ink, strength)

    for quadrant, strength in enumerate((0.81, 0.65, 0.54, 0.70)):
        angle = quadrant * math.pi / 2
        band(angle + 0.17, angle + 0.46, -0.67, -2.37, "linen", strength)
        band(angle + 0.67, angle + 1.22, -1.13, -2.13, "cork paint", 0.68)
    # The grab line bows clear of the ring between its bindings. Two short
    # lengths survive against the darker pillar and the sunken window reveal.
    for start, stop, strength in ((0.00, 0.31, 0.58), (4.56, 4.93, 0.52)):
        points = []
        for k in range(9):
            t = start + (stop - start) * k / 8
            r = 0.395 + 0.034 * (1 + math.cos(4 * t))
            points.append((cx + r * math.cos(t), cy + 0.04, cz + r * math.sin(t) - 0.04))
        mark(points, "linen", strength)
    # A kink in the hanging grab line turns its shaded side towards the stair.
    tail = [(cx + 0.30, cy + 0.043, cz - 0.36), (cx + 0.34, cy + 0.030, cz - 0.51),
            (cx + 0.29, cy + 0.020, cz - 0.64)]
    mark(tail, "rope shade", 0.74)
    mark([tail[-1], (cx + 0.25, cy + 0.025, cz - 0.61)], "linen", 0.54)
