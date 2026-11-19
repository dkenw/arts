"""Authored materials, mural, caustics, lighting, finishing and shared waves.

All artwork is computed from world-space geometry and the authored palette.
"""

import math
import numpy as np
from PIL import Image, ImageDraw

# Scene detail, materials and caustics.

MURAL = None
STENCIL = None
CAUSTIC = None
CAUSTIC_STATS = {}
CAUSTIC_POWER = np.array([4.0, 11.0, 12.0])
CAUSTIC_SOURCE = np.array([6.8, 6.08, 13.35])
FONT = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    "M": ["10001", "11011", "10101", "10101", "10101"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "P": ["110", "101", "110", "100", "100"],
    "N": ["1001", "1101", "1011", "1001", "1001"],
    "O": ["111", "101", "101", "101", "111"],
    "L": ["100", "100", "100", "100", "111"],
    "C": ["111", "100", "100", "100", "111"],
    "S": ["111", "100", "111", "001", "111"],
    ".": ["0", "0", "0", "0", "1"],
    " ": ["00"] * 5,
}


def lettering(text):
    rows = [[] for _ in range(5)]
    for char in text:
        for j, line in enumerate(FONT[char]):
            rows[j].extend([int(k) for k in line] + [0])
    return np.array(rows, dtype=np.uint8)


def bezier(points, count=90):
    p = np.array(points, float)
    t = np.linspace(0, 1, count)[:, None]
    return (1 - t) ** 3 * p[0] + 3 * (1 - t) ** 2 * t * p[1] + 3 * (1 - t) * t * t * p[2] + t**3 * p[3]


def mural_bitmap(s):
    """Two long-fin koi painted as curved silhouettes with scales and pigment."""
    im = Image.new("RGBA", (512, 192))
    d = ImageDraw.Draw(im)

    def rgb(name, a=210):
        return tuple(bytes.fromhex(s.PAL[name])) + (a,)

    def fish(curve, width, body, patch, flip=1):
        nonlocal d
        c = bezier(curve)
        t = np.linspace(0, 1, len(c))
        tangent = np.gradient(c, axis=0)
        tangent /= np.linalg.norm(tangent, axis=1)[:, None]
        normal = np.stack([-tangent[:, 1], tangent[:, 0]], axis=1)
        w = width * (0.38 + 0.62 * np.sin(np.pi * (t * 0.83 + 0.10))) * (1 - t * 0.91)
        edge1 = c + normal * w[:, None]
        edge2 = c - normal * w[:, None]
        mask = Image.new("L", im.size)
        md = ImageDraw.Draw(mask)
        outline = [tuple(v) for v in np.r_[edge1, edge2[::-1]]]
        md.polygon(outline, fill=255)
        # Forked tail and soft pectoral fins, painted before the body.
        tail = c[-1]
        a = tangent[-1]
        b = normal[-1]
        tailshape = [tail - b * 4, tail + a * 40 - b * 25, tail + a * 26 - b * 4, tail + a * 43 + b * 24, tail + b * 4]
        d.polygon([tuple(v) for v in tailshape], fill=rgb(body, 170))
        for side in [-1, 1]:
            q = c[24]
            a = tangent[24]
            b = normal[24] * side
            fin = [q - b * 2, q + b * 25 - a * 5, q + b * 33 + a * 17, q + b * 8 + a * 25]
            d.polygon([tuple(v) for v in fin], fill=rgb(body, 170))
            for k in range(4):
                d.line([tuple(q + b * 8), tuple(q + b * (20 + k * 3) + a * (k * 6))], fill=rgb("jade", 150), width=1)
        paint = Image.new("RGBA", im.size, rgb(body))
        pd = ImageDraw.Draw(paint)
        for q, rx, ry in [(c[13], 18, 14), (c[43], 16, 12), (c[61], 10, 10)]:
            pd.ellipse((q[0] - rx, q[1] - ry, q[0] + rx, q[1] + ry), fill=rgb(patch, 220))
        # Short staggered arcs make scale groups, rather than random grain.
        for k in range(25, 80, 6):
            for side in [-0.6, 0, 0.6]:
                q = c[k] + normal[k] * w[k] * side
                pd.arc((q[0] - 4, q[1] - 3, q[0] + 4, q[1] + 3), 30, 160, fill=rgb("jade", 170), width=1)
        im.alpha_composite(Image.composite(paint, Image.new("RGBA", im.size), mask))
        d = ImageDraw.Draw(im)
        q = c[5] + normal[5] * w[5] * 0.6 * flip
        d.ellipse((q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2), fill=rgb("petrol", 255))
        d.point(tuple(q + [-1, -1]), fill=rgb("butter", 230))
        q = c[16]
        d.line(
            [tuple(q - normal[16] * w[16] * 0.75), tuple(q + tangent[16] * 4), tuple(q + normal[16] * w[16] * 0.75)],
            fill=rgb("verdigris", 210),
            width=2,
        )
        q = c[0]
        for side in [-1, 1]:
            pts = bezier(
                [
                    q,
                    q - tangent[0] * 8 + normal[0] * side * 7,
                    q - tangent[0] * 14 + normal[0] * side * 10,
                    q - tangent[0] * 17 + normal[0] * side * 6,
                ],
                15,
            )
            d.line([tuple(v) for v in pts], fill=rgb(body, 190), width=1)

    fish([(105, 77), (190, 145), (269, 8), (354, 63)], 33, "clay", "terracotta")
    fish([(387, 127), (305, 174), (230, 107), (191, 149)], 17, "jade", "ochre", -1)
    d = ImageDraw.Draw(im)
    # Sparse bubbles, broken spiral strokes and the tesserae of an old mosaic.
    for x, y, r in [(81, 43, 7), (66, 23, 3), (399, 94, 5), (413, 78, 3)]:
        d.ellipse((x - r, y - r, x + r, y + r), outline=rgb("jade", 150), width=1)
    arr = np.array(im)
    yy, xx = np.mgrid[:192, :512]
    tile = (xx % 8 == 0) | (yy % 8 == 0)
    arr[tile, 3] = (arr[tile, 3] * 0.52).astype(np.uint8)
    missing = np.sin((xx // 8) * 17.31 + (yy // 8) * 21.17) > 0.93
    arr[missing, 3] = (arr[missing, 3] * 0.18).astype(np.uint8)
    return arr


def build_scene(s):
    global MURAL, STENCIL
    s.MATS.update(
        {
            "copper": ("rust", 0.15),
            "coldlamp": ("celadon", 0.0),
            "mural": ("mauve", 0.0),
            "bag": ("terracotta", 0.0),
            "bag_dark": ("rust", 0.0),
            "canvas": ("clay", 0.0),
            "clock": ("clay", 0.0),
            "clock_rim": ("rust", 0.15),
            "paper": ("clay", 0.0),
            "notice": ("clay", 0.0),
            "rubber": ("petrol", 0.0),
            "jacket_trim": ("petrol", 0.0),
            "coffee": ("blackberry", 0.0),
            "stitch": ("steel", 0.0),
            "sole": ("clay", 0.0),
        }
    )
    MURAL = mural_bitmap(s)
    STENCIL = lettering("3 M")
    s.rect((11.992, 0.6, 3.4), (0, 0, 8.0), (0, 2.5, 0), "mural", "faded-koi-mosaic")
    # Plumbing follows the wall, with visible elbows, brackets and a shutoff valve.
    s.pipe([(11.91, 0.86, 2.7), (11.91, 0.86, 11.7), (11.91, 0.73, 11.85), (11.91, 0.25, 11.85)], 0.024, "copper", "service-pipe")
    for z in [3.2, 5.4, 7.6, 9.8, 11.5]:
        s.box((11.87, 0.815, z - 0.04), (11.99, 0.905, z + 0.04), "metal", "pipe-clip")
    c = np.array([11.81, 0.86, 10.8])
    for a, b in zip(np.linspace(0, 2 * math.pi, 19)[:-1], np.linspace(0, 2 * math.pi, 19)[1:]):
        s.tube(
            c + [0, 0.12 * math.cos(a), 0.12 * math.sin(a)], c + [0, 0.12 * math.cos(b), 0.12 * math.sin(b)], 0.009, "wood", "valve-wheel"
        )
    for a in np.arange(3) * 2 * math.pi / 3:
        s.tube(c, c + [0, 0.12 * math.cos(a), 0.12 * math.sin(a)], 0.008, "wood", "valve-spoke")
    # An analogue clock: 01:47. The face and hands occupy the same Y/Z plane.
    c = np.array([11.94, 2.18, 10.55])
    s.ellipsoid(c, [0.045, 0.32, 0.32], "clock_rim", "wall-clock-rim")
    s.ellipsoid(c + [-0.041, 0, 0], [0.01, 0.278, 0.278], "clock", "wall-clock-face")
    for k in range(12):
        a = k * math.pi / 6
        v = np.array([0, math.cos(a), math.sin(a)])
        s.tube(c + [-0.057, 0, 0] + v * 0.235, c + [-0.057, 0, 0] + v * 0.265, 0.009 if k % 3 == 0 else 0.005, "black", "clock-tick")
    for angle, length, r in [(47 * math.pi / 30, 0.22, 0.009), ((1 + 47 / 60) * math.pi / 6, 0.15, 0.012)]:
        s.tube(c + [-0.06, 0, 0], c + [-0.06, math.cos(angle) * length, math.sin(angle) * length], r, "black", "clock-hand")
    s.ellipsoid(c + [-0.065, 0, 0], [0.012] * 3, "wood", "clock-hub")
    s.rect((11.983, 1.20, 3.9), (0, 0, 0.66), (0, 0.47, 0), "notice", "depth-notice")
    # The overhead tube is outside the crop; its rippled water reflection is real.
    s.box((3.6, 6.12, 13.25), (9.0, 6.2, 13.46), "black", "fluorescent-housing")
    s.rect((3.7, 6.113, 13.29), (5.15, 0, 0), (0, 0, 0.10), "coldlamp", "ceiling-fluorescent")
    for x in [3.9, 8.7]:
        s.tube((x, 6.2, 13.35), (x, 6.5, 13.35), 0.012, "metal", "light-suspension")
    # A few loose threads are anchored to the towel's uneven lower hem.
    for j in range(15):
        x = -0.84 + j * 0.041
        y = 3.37 + 0.018 * math.sin(j * 2.1)
        s.tube((x, y, 3.105), (x + 0.004, y - 0.035 - (j % 3) * 0.008, 3.105), 0.0028, "canvas", "towel-fringe")
    for z in [2.2, 7.7]:
        s.ellipsoid((7.985, -0.27, z), [0.024, 0.065, 0.065], "metal", "return-jet")
    # Bolted rail feet and discrete paint chips are modelled at real scale.
    for z in [1.84, 3.16]:
        for x in [-2.9, -1.6, -0.3, 1.0]:
            s.box((x - 0.08, 3.0, z - 0.065), (x + 0.08, 3.025, z + 0.065), "foreground_metal", "rail-footplate")
            for dx in [-0.055, 0.055]:
                s.ellipsoid((x + dx, 3.03, z), [0.014, 0.009, 0.014], "metal", "rail-bolt")
    # A canvas bag and worn pool sandals: small, grounded narrative objects.
    s.ellipsoid((1.24, 3.16, 2.83), [0.23, 0.16, 0.135], "bag", "canvas-bag")
    s.box((1.08, 3.12, 2.69), (1.41, 3.27, 2.74), "bag_dark", "bag-pocket")
    s.pipe([(1.12, 3.27, 2.81), (1.12, 3.43, 2.81), (1.34, 3.43, 2.81), (1.34, 3.27, 2.81)], 0.013, "canvas", "bag-handle")
    s.tube((1.06, 3.29, 2.77), (1.42, 3.29, 2.77), 0.008, "metal", "bag-zipper")
    for x, z in [(0.53, 2.38), (0.80, 2.51)]:
        s.ellipsoid((x, 3.025, z), [0.13, 0.025, 0.052], "rubber", "sandals")
        s.pipe([(x - 0.04, 3.04, z - 0.044), (x + 0.025, 3.085, z), (x - 0.04, 3.04, z + 0.044)], 0.013, "wood", "sandal-strap")

    # Local coordinates keep added face, cuff and cup details attached to the pose.
    def hp(q):
        return s.turn @ np.array(q, float) + [s.hx, s.SEAT_OFFSET, s.hz]

    def ht(a, b, r, mat, label):
        s.tube(hp(a), hp(b), r, mat, label)

    def he(c, r, mat, label):
        s.ellipsoid(hp(c), r, mat, label)
        s.OBJECTS[-1]["rotation"] = s.turn.copy()

    he((0, 1.24, -0.153), [0.027, 0.032, 0.035], "skin", "nose")
    for side in [-1, 1]:
        he((side * 0.071, 1.266, -0.124), [0.010, 0.009, 0.009], "black", "eye")
        elbow = np.array([side * 0.26, 0.78, -0.17])
        hand = np.array([side * 0.07, 0.73, -0.35])
        ht(elbow * 0.23 + hand * 0.77, elbow * 0.08 + hand * 0.92, 0.060, "jacket_trim", "ribbed-cuff")
        # A light sole and toe cap on each dark shoe.
        he((side * 0.17, 0.035, -0.70), [0.087, 0.012, 0.16], "sole", "shoe-sole")
    # Cup handle, dark coffee and a narrow porcelain rim.
    he((0, 0.821, -0.38), [0.039, 0.003, 0.039], "coffee", "coffee-surface")
    for a in np.linspace(0, 2 * math.pi, 17)[:-1]:
        b = a + math.pi / 8
        ht(
            (0.065 + 0.035 * math.cos(a), 0.758 + 0.041 * math.sin(a), -0.38),
            (0.065 + 0.035 * math.cos(b), 0.758 + 0.041 * math.sin(b), -0.38),
            0.006,
            "cup",
            "cup-handle",
        )
        ht(
            (0.043 * math.cos(a), 0.823, -0.38 + 0.043 * math.sin(a)),
            (0.043 * math.cos(b), 0.823, -0.38 + 0.043 * math.sin(b)),
            0.003,
            "cup",
            "cup-rim",
        )
    # Clipped paper label and a screw on the lamp above the door.
    s.rect((8.48, 2.335, 13.751), (0.13, 0, 0), (0, 0.09, 0), "paper", "lamp-label")


def hash2(x, y):
    v = np.sin(x * 127.1 + y * 311.7) * 43758.5453
    return v - np.floor(v)


def stencil_sample(bitmap, u, v):
    inside = (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
    x = np.clip((u * bitmap.shape[1]).astype(int), 0, bitmap.shape[1] - 1)
    y = np.clip((v * bitmap.shape[0]).astype(int), 0, bitmap.shape[0] - 1)
    return inside & (bitmap[y, x] > 0)


def material(p, n, mat, foot, base, s):
    """Authored wear, painted motifs and cloth shading; never screen noise."""
    x, y, z = p.T

    def col(name):
        return s.colour(name)

    if mat in ["wall", "mural"]:
        along = np.where(np.abs(n[:, 0]) > 0.5, z, x)
        # Old glazed wainscoting; large plaster stains above it.
        cells = hash2(np.floor(along / 0.19), np.floor(y / 0.19))
        tiles = (y < 1.17) & (y > 0.16)
        base[tiles] = col("bluegrey") * (0.58 + 0.26 * cells[tiles, None])
        joint = (np.mod(along, 0.19) < 0.009) | (np.mod(y, 0.19) < 0.008)
        base[tiles & joint] *= 0.63
        border = (y > 1.14) & (y < 1.21)
        base[border] = col("rust") * 0.8
        stain = np.sin(along * 1.6 + np.sin(y * 2.1)) + 0.6 * np.sin(along * 4.4 - y * 0.6)
        base[(~tiles) & (stain > 1.0)] *= 0.78
        # Missing glaze collects in a few damp patches instead of everywhere.
        patch = (np.sin(along * 0.74 + 2.2) + np.cos(y * 2.2) > 1.25) & (y < 1.1)
        base[patch & (cells > 0.58)] = col("dust") * 0.60
        drip = (np.mod(along * 1.6 + np.sin(along * 2.4) * 0.6, 1) < 0.09) & (y < 1.5) & (y > 0.3)
        base[drip] *= 0.74
        if mat == "mural":
            u = np.clip(((z - 3.4) / 8 * 512).astype(int), 0, 511)
            v = np.clip(((3.1 - y) / 2.5 * 192).astype(int), 0, 191)
            rgba = MURAL[v, u]
            alpha = rgba[:, 3:4] / 255 * 0.78
            pigment = s.linear(rgba[:, :3] / 255) * 0.95
            base = base * (1 - alpha) + pigment * alpha
    elif mat == "deck":
        a = x / 0.5
        b = z / 0.5
        tiles = hash2(np.floor(a), np.floor(b))
        base *= (0.78 + 0.37 * tiles)[:, None]
        seams = (np.mod(x, 0.5) < 0.013) | (np.mod(z, 0.5) < 0.013)
        base[seams] *= 0.55
        # Irregular damp patches stay near the pool lip, below the eye line.
        edge = np.minimum.reduce([np.abs(x), np.abs(x - 8), np.abs(z), np.abs(z - 12)])
        wet = (edge < 0.55) & (np.sin(x * 4.7 + np.sin(z * 2.1)) + 0.65 * np.cos(z * 3.9) > 0.65)
        base[wet] *= 0.61
        speck = hash2(np.floor(x * 21), np.floor(z * 21))
        chips = (speck > 0.98) & seams
        base[chips] = col("lilac") * 0.75
    elif mat == "coping":
        a = np.where(np.abs(n[:, 0]) > 0.6, z, x)
        joint = np.mod(a, 0.42) < 0.015
        base[joint] *= 0.46
        salt = hash2(np.floor(x * 38), np.floor(z * 38))
        base[(salt > 0.88) & (y > 0.025)] *= 1.25
        base[(salt < 0.08) & (y < 0.02)] *= 0.46
    elif mat == "foreground":
        top = (n[:, 1] > 0.7) & (y > 2.99)
        edge = np.minimum(np.abs(z - 1.8), np.abs(z - 3.2))
        base[top] = col("dust") * 0.60
        runner = top & (z > 1.99) & (z < 3.01)
        base[runner] = col("slate") * 0.59
        # Broad scuffs plus sparse connected chips, in metre-sized material space.
        cell = hash2(np.floor(x * 20), np.floor(z * 20))
        chip = top & (edge < 0.06 + 0.05 * np.sin(x * 17)) & (cell > 0.23)
        base[chip] = col("lilac") * 0.80
        scuff = np.sin(x * 12 + np.sin(z * 9)) + 0.8 * np.cos(z * 31 + x * 7)
        base[runner & (scuff > 1.42)] *= 1.6
        seam = top & (np.mod(x + 0.15, 0.62) < 0.016)
        base[seam] *= 0.52
        # A worn metric height stencil follows the top of the platform.
        mark = stencil_sample(STENCIL, (2.91 - z) / 0.58, (0.75 - x) / 0.25) & top
        base[mark & (cell > 0.15)] = col("clay") * 0.90
        for cx, cz in [(-0.9, 2.48), (-0.48, 2.66), (-0.12, 2.46)]:
            sole = ((x - cx) / 0.13) ** 2 + ((z - cz) / 0.055) ** 2 < 1
            base[top & sole] *= 0.46
        # Subsurface pits on the concrete fascia are clustered along its edge.
        pits = hash2(np.floor(x * 32), np.floor(y * 34))
        base[(~top) & (pits > 0.9) & (y > 2.91)] *= 1.45
    elif mat in ["metal", "foreground_metal", "copper"]:
        along = x * 0.9 + y * 0.6 + z * 1.3
        rust = np.sin(along * 8.1) + 0.4 * np.sin(along * 39)
        worn = rust > 1.13
        base[worn] = col("rust") * 0.65
        base[(rust < -0.8) & (n[:, 1] > 0.2)] *= 1.2
    elif mat == "towel_fabric":
        # The hanging towel has broad indigo stripes, hem stitching and darker folds.
        base[:] = col("clay") * 0.9
        fold = 0.68 + 0.25 * np.cos((x + 0.85) * 2 * math.pi / 0.16)
        base *= fold[:, None]
        stripe = (np.mod(y - 3.31, 0.19) < 0.047) & (y < 3.98)
        base[stripe] = col("teal") * fold[stripe, None]
        hem = y < 3.44
        base[hem] = col("deepwater") * 0.85
        stitches = hem & (np.mod(x + 0.85, 0.043) < 0.012) & (y > 3.405) & (y < 3.42)
        base[stitches] = col("clay")
    elif mat in ["shirt", "pants", "cap", "bag"]:
        if mat in ["shirt", "pants", "cap"]:
            q = (p - [s.hx, s.SEAT_OFFSET, s.hz]) @ s.turn
            if mat == "shirt" and hasattr(s, "CLOTH_ROTATION"):
                q = (q - s.CLOTH_ORIGIN) @ s.CLOTH_ROTATION + np.array([0, 0.88, 0.015])
            u, v, w = q.T
        else:
            u, v, w = x, y, z
        if mat == "shirt":
            # Cuff/waist folds are directional strokes, not a smooth capsule gradient.
            fold = np.sin(v * 61 + u * 19 + np.sin(w * 18))
            lower = v < 0.83
            base[lower & (fold < -0.60)] *= 0.54
            base[lower & (fold > 0.8)] *= 1.25
            shoulder = (v > 1.03) & (np.abs(u) > 0.15)
            base[shoulder] *= 1.25
            # The upper back catches the spotlight. A curved yoke and a few long
            # fabric creases break the otherwise smooth ellipsoid into cloth panels.
            back = w > 0.075
            yoke = 1.065 - 0.9 * u * u
            base[back & (np.abs(v - yoke) < 0.009)] *= 0.28
            pleat = np.abs(u - (0.115 + 0.022 * np.sin(v * 18))) < 0.010
            base[back & pleat & (v > 0.85) & (v < 1.055)] *= 0.42
            for side in [-1, 1]:
                crease = np.abs(v - (0.93 + side * u * 0.42)) < 0.007
                base[back & crease & (np.abs(u) > 0.11) & (v < 1.04)] *= 0.42
            collar = v > 1.11
            base[collar] = col("petrol")
            seam = (np.abs(u) < 0.012) & (w > 0.11)
            base[seam] *= 0.55
            # A softly worn lower canvas panel and a few connected creases give the
            # jacket weight without a large, attention-grabbing numbered graphic.
            panel = back & (v < 1.015 - 0.55 * u * u)
            base[panel] *= 0.68
            crease = np.abs(u - (0.075 + 0.11 * (1.02 - v))) < 0.009
            base[back & crease & (v > 0.81) & (v < 1.025)] *= 0.49
        elif mat == "pants":
            folds = (np.sin(v * 71 + w * 40 + u * 18) < -0.80) & (v < 0.57)
            base[folds] *= 0.45
            edge = np.mod(w * 11 + v * 4, 1) < 0.08
            base[edge] *= 1.35
        elif mat == "cap":
            seam = (np.abs(u) < 0.009) | (np.abs(u - 0.075) < 0.006)
            base[seam] *= 0.65
        else:
            weave = hash2(np.floor(x * 55), np.floor(y * 55))
            base *= (0.78 + 0.28 * weave)[:, None]
            fold = np.sin(x * 45 + y * 31) < -0.7
            base[fold] *= 0.65
    elif mat == "notice":
        base[:] = col("clay") * 0.65
        inside = (y > 1.23) & (y < 1.64) & (z > 3.93) & (z < 4.53)
        base[~inside] = col("wood") if "wood" in s.PAL else col("rust")
        mark = stencil_sample(lettering("3.8 M"), (z - 3.96) / 0.55, (1.55 - y) / 0.14)
        base[mark] = col("petrol")
    elif mat == "clock":
        # A pale dial with a slight age stain, not an emissive disk.
        base *= (0.80 + 0.10 * np.cos((z - 10.55) * 9))[:, None]
    return base


def caustic_light(p, n, s):
    """Forward-map flux through the wave surface onto the basin floor.

     This samples three points on the tube fixture. It computes focusing,
    Snell transmission, Fresnel loss and absorption; it omits visibility tests
    against other objects along the light-to-water path.
    """
    global CAUSTIC, CAUSTIC_STATS
    if CAUSTIC is None:
        nx, nz = 640, 960
        mw, mh = 256, 384
        zz, xx = np.mgrid[0:nz, 0:nx]
        x = (xx.ravel() + 0.5) * 8 / nx
        z = (zz.ravel() + 0.5) * 12 / nz
        h, dx, dz = s.wave(x, z)
        points = np.stack([x, h, z], 1)
        normals = s.norm(np.stack([-dx, np.ones_like(x), -dz], 1))
        accum = np.zeros((mh * mw, 3))
        input_flux = np.zeros(3)
        for lx in [4.25, 6.275, 8.30]:
            source = CAUSTIC_SOURCE.copy()
            source[0] = lx
            incoming = points - source
            dist = np.linalg.norm(incoming, axis=1)
            incoming /= dist[:, None]
            _, transmitted, F = s.optics(incoming, normals)
            t = (s.FLOOR - h) / transmitted[:, 1]
            dest = points + t[:, None] * transmitted
            cosine = np.maximum(0, -(incoming * normals).sum(1))
            flux = (cosine / dist**2 * (1 - F) * (8 / nx) * (12 / nz))[:, None] * CAUSTIC_POWER / 3
            flux *= np.exp(-t[:, None] * s.ABSORPTION)
            input_flux += flux.sum(0)
            u = dest[:, 0] / 8 * mw - 0.5
            v = dest[:, 2] / 12 * mh - 0.5
            ix = np.floor(u).astype(int)
            iy = np.floor(v).astype(int)
            fx = u - ix
            fy = v - iy
            for ox, oy, weight in [(0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)]:
                bx = ix + ox
                by = iy + oy
                good = (bx >= 0) & (bx < mw) & (by >= 0) & (by < mh)
                bins = (by[good] * mw + bx[good]).astype(int)
                for c in range(3):
                    accum[:, c] += np.bincount(bins, weights=flux[good, c] * weight[good], minlength=mh * mw)
        CAUSTIC = accum.reshape(mh, mw, 3) / ((8 / mw) * (12 / mh))
        # Pixel-footprint smoothing avoids a photon-lattice alias pattern.
        padded = np.pad(CAUSTIC, ((1, 1), (1, 1), (0, 0)))
        CAUSTIC = (CAUSTIC * 4 + padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:]) / 8
        CAUSTIC_STATS = {
            "samples": nx * nz * 3,
            "transmitted_flux_rgb": input_flux.tolist(),
            "floor_flux_rgb": (CAUSTIC.sum((0, 1)) * (8 / mw) * (12 / mh)).tolist(),
            "peak_irradiance": float(CAUSTIC.max()),
            "finite_nonnegative": bool(np.all(np.isfinite(CAUSTIC)) and np.all(CAUSTIC >= 0)),
        }
    out = np.zeros_like(p)
    good = (p[:, 1] < s.FLOOR + 0.025) & (n[:, 1] > 0.8) & (p[:, 0] >= 0) & (p[:, 0] < 8) & (p[:, 2] >= 0) & (p[:, 2] < 12)
    ix = np.clip((p[good, 0] / 8 * 256).astype(int), 0, 255)
    iy = np.clip((p[good, 2] / 12 * 384).astype(int), 0, 383)
    out[good] = CAUSTIC[iy, ix]
    return out


def pixel_finish(image, s, depth, ids):
    """Small explicit pixel clusters, anchored to world positions and depth."""
    d = ImageDraw.Draw(image)
    names = list(s.PAL)

    def idx(name):
        return names.index(name)

    # Selective one-pixel contours make the near figure and bag more deliberate.
    # Only pixels already inside their projected silhouette are changed.
    arr = np.array(image)
    labels = {
        "torso",
        "upper-arm",
        "forearm",
        "ribbed-cuff",
        "hips",
        "thigh",
        "shin",
        "knee",
        "shoe",
        "shoe-sole",
        "head",
        "ear",
        "nose",
        "hair",
        "cap-crown",
        "cap-brim",
        "hand",
        "canvas-bag",
        "bag-pocket",
    }
    selected = np.isin(ids, [k for k, o in enumerate(s.OBJECTS) if o["label"] in labels])
    shadow_edge = selected & (~np.roll(selected, -1, 0) | ~np.roll(selected, -1, 1))
    light_edge = selected & (~np.roll(selected, 1, 0)) & ~shadow_edge
    for k, o in enumerate(s.OBJECTS):
        if o["label"] not in labels:
            continue
        own = ids == k
        mat = o["mat"]
        dark = "terracotta" if mat == "skin" else ("rust" if mat in ["cap", "bag", "bag_dark"] else "blackberry")
        lit = "apricot" if mat == "skin" else ("ochre" if mat in ["cap", "bag", "bag_dark"] else "bluegrey")
        if mat == "shirt":
            dark = "rust"
            lit = "apricot"
        if mat == "cap":
            dark = "petrol"
            lit = "steel"
        arr[own & shadow_edge] = idx(dark)
        arr[own & light_edge] = idx(lit)
    image = Image.fromarray(arr, "P")
    image.putpalette((s.RGB * 255 + 0.5).astype(np.uint8).ravel().tolist() + [0] * (768 - 3 * len(s.RGB)))
    d = ImageDraw.Draw(image)
    # Wisps rise from the coffee. The pinhole projection and depth test keep
    # them attached to the cup and behind any intervening rail.
    cup = s.turn @ np.array([0.0, 0.83, -0.38]) + [s.hx, s.SEAT_OFFSET, s.hz]
    if hasattr(s, "ANIMATION_TIME"):
        # A continuous upward-travelling ribbon: periodic phases and fading gaps
        # keep the loop seamless without translating or warping the rendered cup.
        phase = math.tau * (s.ANIMATION_TIME % s.LOOP_SECONDS) / s.LOOP_SECONDS
        for branch in range(2):
            for k in range(40):
                h = 0.012 + k * 0.008
                visible = math.sin(h * 43 - phase * 2 + branch * 2) > 0.05 + h * 0.85
                if not visible:
                    continue
                spread = 0.008 + h * 0.11
                p = cup + [spread * math.sin(h * 23 - phase * 2 + branch * 2), h, spread * 0.65 * math.sin(h * 17 - phase + branch)]
                uv = s.project(p)
                x, y = np.floor(uv).astype(int)
                if 0 <= x < s.W and 0 <= y < s.H and np.linalg.norm(p - s.EYE) < depth[y, x] + 0.025:
                    d.point((int(x), int(y)), fill=idx("pewter" if h < 0.08 else "steel" if h < 0.18 else "bluegrey"))
        return image
    for branch in range(2):
        for k in range(28):
            h = 0.025 + k * 0.009
            p = cup + [0.024 * math.sin(h * 26 + branch * 2), h, 0.020 * math.sin(h * 18 + branch)]
            uv = s.project(p)
            x, y = np.floor(uv).astype(int)
            if 0 <= x < s.W and 0 <= y < s.H and k % 5 != 3:
                if np.linalg.norm(p - s.EYE) < depth[y, x] + 0.03:
                    d.point((int(x), int(y)), fill=idx("steel" if k < 15 else "bluegrey"))
    return image


# Spotlight, humid air, dust and bloom.

SOURCE = np.array([0.5, 6.05, 9.5])
AIM = np.array([2.08, 3.66, 2.45])
POWER = np.array([300.0, 180.0, 68.0])
SCATTER_GAIN = 0.85
AXIS = (AIM - SOURCE) / np.linalg.norm(AIM - SOURCE)
RIGHT = np.cross([0.0, 1.0, 0.0], AXIS)
RIGHT /= np.linalg.norm(RIGHT)
UP = np.cross(AXIS, RIGHT)
INNER = math.cos(math.radians(1.7))
OUTER = math.cos(math.radians(3.6))
SHADOW = None
SHADOW_TAN = math.tan(math.radians(16.5))
EMISSIONS = {
    "lamp": np.array([1.5, 0.20, 0.035]),
    "wetlamp": np.array([0.18, 4.5, 3.9]),
    "utility_lamp": np.array([0.01, 0.06, 0.12]),
    "coldlamp": np.array([0.025, 0.6, 0.65]),
    "focuslamp": np.array([12.0, 5.0, 1.5]),
}


def build_spotlight(s):
    s.MATS["focuslamp"] = ("butter", 0.0)
    # The focused fixture has a real housing, lens plane and ceiling mount.
    s.tube(SOURCE - AXIS * 0.25, SOURCE - AXIS * 0.035, 0.145, "black", "spot-housing")
    c = SOURCE - AXIS * 0.03
    s.rect(c - 0.12 * RIGHT - 0.12 * UP, 0.24 * RIGHT, 0.24 * UP, "focuslamp", "spot-lens")
    s.tube(SOURCE - AXIS * 0.18, np.array([SOURCE[0], 6.5, SOURCE[2]]), 0.018, "metal", "spot-mount")


def cone(points):
    v = points - SOURCE
    dist = np.linalg.norm(v, axis=1)
    direction = v / np.maximum(dist[:, None], 1e-8)
    x = np.clip((direction @ AXIS - OUTER) / (INNER - OUTER), 0, 1)
    return x * x * (3 - 2 * x), dist, direction


def direct(p, n, view, albedo, spec, s):
    strength, dist, from_light = cone(p)
    ld = -from_light
    nd = np.maximum((ld * n).sum(1), 0)
    valid = (strength > 0) & (nd > 0) & (p[:, 1] > s.WATER)
    active = np.where(valid)[0]
    out = np.zeros_like(p)
    if not len(active):
        return out
    _, hit, _ = s.intersection(p[active] + n[active] * 0.0015, ld[active], dist[active] - 0.005)
    visible = hit < 0
    weight = strength[active] * visible / np.maximum(dist[active] ** 2, 0.1)
    incident = weight[:, None] * POWER
    out[active] = albedo[active] * incident * nd[active, None]
    half = s.norm(ld[active] - view[active])
    nh = np.maximum((half * n[active]).sum(1), 0)
    out[active] += incident * ((nh**48) * spec[active] * 0.35)[:, None]
    return out


def prepare_shadow(s):
    global SHADOW
    size = 192
    y, x = np.mgrid[:size, :size]
    d = (
        AXIS
        + ((x.ravel() + 0.5) / size * 2 - 1)[:, None] * SHADOW_TAN * RIGHT
        - ((y.ravel() + 0.5) / size * 2 - 1)[:, None] * SHADOW_TAN * UP
    )
    d = s.norm(d)
    o = np.broadcast_to(SOURCE, d.shape).copy()
    depth, _, _ = s.intersection(o, d)
    SHADOW = depth.reshape(size, size)


def visibility(points):
    v = points - SOURCE
    z = v @ AXIS
    u = (v @ RIGHT) / np.maximum(z, 1e-7) / SHADOW_TAN * 0.5 + 0.5
    w = -(v @ UP) / np.maximum(z, 1e-7) / SHADOW_TAN * 0.5 + 0.5
    good = (z > 0) & (u >= 0) & (u < 1) & (w >= 0) & (w < 1)
    ix = np.clip((u * 192).astype(int), 0, 191)
    iy = np.clip((w * 192).astype(int), 0, 191)
    return good & (np.linalg.norm(v, axis=1) < SHADOW[iy, ix] + 0.025)


def atmosphere(ro, rd, depth, rgb, s):
    """Single scattering through humid room air, with a shadowed light shaft."""
    if SHADOW is None:
        prepare_shadow(s)
    distance = np.minimum(depth, 30)
    trans = np.ones(len(rd))
    scatter = np.zeros_like(rgb)
    count = 40
    step = distance / count
    for j in range(count):
        t = (j + 0.5) * step
        p = ro + rd * t[:, None]
        # There is more moisture immediately above the pool.
        over = (p[:, 0] > 0) & (p[:, 0] < 8) & (p[:, 2] > 0) & (p[:, 2] < 12) & (p[:, 1] > s.WATER)
        low = np.exp(-(((p[:, 1] - 0.18) / 0.34) ** 2)) * over
        density = 0.022 + 0.045 * low
        strength, dist, from_light = cone(p)
        active = np.where(strength > 0)[0]
        illumination = np.zeros_like(rgb)
        if len(active):
            visible = visibility(p[active])
            cosine = (from_light[active] * (-rd[active])).sum(1)
            g = 0.32
            phase = (1 - g * g) / (4 * math.pi * (1 + g * g - 2 * g * cosine) ** 1.5)
            falloff = strength[active] * visible / np.maximum(dist[active] ** 2, 0.15)
            illumination[active] = (falloff * phase * SCATTER_GAIN)[:, None] * POWER
        illumination += low[:, None] * np.array([0.008, 0.15, 0.095])
        attenuation = np.exp(-density * step)
        scatter += trans[:, None] * (1 - attenuation)[:, None] * illumination
        trans *= attenuation
    return rgb * trans[:, None] + scatter


def bloom(rgb, height, width):
    """Small native-grid highlight spill; final quantisation restores 28 colours."""
    bright = np.maximum(rgb.reshape(height, width, 3) - 0.27, 0)
    for _ in range(2):
        a = np.pad(bright, ((1, 1), (1, 1), (0, 0)))
        bright = (a[1:-1, 1:-1] * 4 + a[1:-1, :-2] + a[1:-1, 2:] + a[:-2, 1:-1] + a[2:, 1:-1]) / 8
    return rgb + bright.reshape(-1, 3) * 0.18


def finish(image, s, depth):
    # Sparse illuminated dust uses world positions, cone falloff and occlusion.
    rng = np.random.default_rng(3409)
    d = ImageDraw.Draw(image)
    names = list(s.PAL)
    for i in range(200):
        z = rng.uniform(0.75, 7.2)
        r = math.sqrt(rng.random()) * z * 0.07
        a = rng.random() * math.tau
        p = SOURCE + AXIS * z + RIGHT * (math.cos(a) * r) + UP * (math.sin(a) * r)
        if hasattr(s, "ANIMATION_TIME"):
            phase = math.tau * (s.ANIMATION_TIME % s.LOOP_SECONDS) / s.LOOP_SECONDS
            p += RIGHT * (0.055 * math.sin(phase + a)) + UP * (0.075 * math.cos(phase + a)) + AXIS * (0.025 * math.sin(2 * phase + a))
        uv = s.project(p)
        x, y = np.floor(uv).astype(int)
        if not (0 <= x < s.W and 0 <= y < s.H):
            continue
        if np.linalg.norm(p - s.EYE) > depth[y, x] or not visibility(p[None, :])[0] or cone(p[None, :])[0][0] < 0.2:
            continue
        if i % 7:
            continue
        d.point((int(x), int(y)), fill=names.index("ochre" if i % 3 else "apricot"))
    return image


# Ambient light, figure pose and periodic gravity waves.


def ambient(p, n, underwater):
    a = np.broadcast_to([0.02624, 0.02788, 0.0697], p.shape).copy()
    a *= (0.55 + 0.45 * np.maximum(n[:, 1], 0))[:, None]
    a[underwater] = [0.0025, 0.011, 0.0135]
    near = (p[:, 0] > -0.4) & (p[:, 0] < 8.4) & (p[:, 2] > -0.4) & (p[:, 2] < 12.4) & (~underwater)
    fill = np.exp(-np.maximum(p[:, 1], 0) / 2) * np.clip(1 - n[:, 1], 0, 1.6) * near
    return a + fill[:, None] * [0.00328, 0.1804, 0.1804]


def configure_pose(s):
    # Give the seated figure a slight forward lean toward the cup.
    origin = np.array([s.hx, s.SEAT_OFFSET, s.hz])

    def hp(q):
        return s.turn @ np.array(q, float) + origin

    def rx(a):
        return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])

    torso = next(o for o in s.OBJECTS if o["label"] == "torso")
    torso["p"] = hp([0, 0.87, -0.025])
    torso["rotation"] = s.turn @ rx(-0.12)
    s.CLOTH_ROTATION = rx(-0.12)
    s.CLOTH_ORIGIN = np.array([0, 0.87, -0.025])
    headrot = rx(-0.25)
    upright_head = np.array([0, 1.235, -0.045])
    lowered_head = np.array([0, 1.20, -0.10])
    for o in s.OBJECTS:
        if o["label"] in ["head", "hair", "ear", "nose", "eye", "cap-crown", "cap-brim"]:
            q = s.turn.T @ (o["p"] - origin)
            o["p"] = hp(lowered_head + headrot @ (q - upright_head))
            o["rotation"] = s.turn @ headrot
    # Shoulders follow the torso. Keep the elbows fixed to preserve the cup grip.
    for o in s.OBJECTS:
        if o["label"] == "upper-arm":
            q = s.turn.T @ (o["p"] - origin)
            end = o["p"] + o["axis"] * o["length"]
            q[1] -= 0.025 if q[0] < 0 else 0.045
            q[2] -= 0.04
            o["p"] = hp(q)
            delta = end - o["p"]
            o["length"] = float(np.linalg.norm(delta))
            o["axis"] = delta / o["length"]
    # Attach the handle in the plane of the open door leaf.
    leaf = next(o for o in s.OBJECTS if o["label"] == "open-door-leaf")
    handle = next(o for o in s.OBJECTS if o["label"] == "door-handle")
    handle["p"] = leaf["p"] + leaf["a"] * 0.82 + [0, 1.01, 0] - leaf["n"] * 0.025


def wave(s, x, z):
    """The same periodic gravity waves for the still and every animated frame."""
    loop = 8.0
    time = getattr(s, "ANIMATION_TIME", 0.0) % loop
    h = np.full_like(x, s.WATER)
    dx = np.zeros_like(x)
    dz = np.zeros_like(x)
    for amp, mode, theta, phase in [(0.010, 9, 0.28, 0.3), (0.0055, 12, -0.85, 1.4), (0.0035, 7, 1.2, 0.7)]:
        omega = math.tau * mode / loop
        k = omega * omega / 9.81
        kx = k * math.cos(theta)
        kz = k * math.sin(theta)
        q = kx * x + kz * z + phase - omega * time
        h += amp * np.sin(q)
        dx += amp * kx * np.cos(q)
        dz += amp * kz * np.cos(q)
    omega = math.tau * 15 / loop
    k = omega * omega / 9.81
    for x0, z0, amp, phase in [(7.8, 7.7, 0.0011, 0.6), (7.8, 2.2, 0.0008, 2.1)]:
        xx = x - x0
        zz = z - z0
        r = np.sqrt(xx * xx + zz * zz + 0.01)
        env = amp * np.exp(-r / 2.2)
        q = k * r + phase - omega * time
        h += env * np.sin(q)
        derivative = env * (k * np.cos(q) - np.sin(q) / 2.2)
        dx += derivative * xx / r
        dz += derivative * zz / r
    return h, dx, dz
