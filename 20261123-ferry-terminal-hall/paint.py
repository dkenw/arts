"""Hand-built surface maps for No Further Sailings. All lengths in the hall are metres."""

import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from layout import LIFTED, PITCH, DRIP, SILL_JOINT, feet, on_bank


GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("111", "010", "010", "010", "010", "010", "111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "1": ("010", "110", "010", "010", "010", "010", "111"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01111", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "11110"),
    ":": ("0", "1", "1", "0", "1", "1", "0"),
    "-": ("000", "000", "000", "111", "000", "000", "000"),
    "/": ("0001", "0001", "0010", "0010", "0100", "1000", "1000"),
    " ": ("00",) * 7,
    ".": ("0", "0", "0", "0", "0", "1", "1"),
}


def letters(d, xy, s, color, scale=(2, 2), gap=1):
    x, y = xy
    sx, sy = scale
    for c in s:
        g = GLYPHS.get(c, GLYPHS[" "])
        for j, line in enumerate(g):
            for i, a in enumerate(line):
                if a == "1":
                    d.rectangle(
                        (
                            x + i * sx,
                            y + j * sy,
                            x + (i + 1) * sx - 1,
                            y + (j + 1) * sy - 1,
                        ),
                        fill=color,
                    )
        x += (len(g[0]) + gap) * sx
    return x


def noise(rng, w, h, nx, ny):
    small = rng.normal(128, 38, (ny, nx)).clip(0, 255).astype("uint8")
    return (
        np.asarray(
            Image.fromarray(small).resize((w, h), Image.Resampling.BICUBIC),
            dtype="float32",
        )
        - 128
    ) / 38


def floor_maps(path):
    rng = np.random.default_rng(3904)
    w, h = 1880, 2540
    x = np.linspace(-15, 11, w, dtype="float32")[None, :]
    y = np.linspace(16.8, -19, h, dtype="float32")[:, None]
    broad = noise(rng, w, h, 12, 15)
    mid = noise(rng, w, h, 65, 84)
    fine = noise(rng, w, h, 200, 275)

    # A lopsided sheet of rainwater creeping in from the glazing, with satellite pools.
    def ellipse(cx, cy, rx, ry, tilt):
        xx = x - cx
        yy = y - cy
        a = (xx * np.cos(tilt) + yy * np.sin(tilt)) / rx
        b = (-xx * np.sin(tilt) + yy * np.cos(tilt)) / ry
        return 1 - a * a - b * b

    field = np.maximum.reduce(
        [
            ellipse(6.4, -1.5, 4.2, 8.4, -0.36),
            ellipse(4.8, 6.2, 1.15, 4.6, -0.47),
            ellipse(2.25, -5.4, 1.7, 0.57, -0.21),
            ellipse(1.4, 0.5, 1.05, 0.46, 0.28),
        ]
    )
    field += 0.35 * broad + 0.23 * mid + 0.075 * fine
    # A joined set of shallow rivulets from the split coping, widening toward
    # the depressed, level portion of the floor. The wet region stays continuous.
    flow = [
        (10.51, SILL_JOINT - 0.025, 0.14),
        (10.19, SILL_JOINT - 0.09, 0.22),
        (9.85, 4.57, 0.25),
        (9.40, 4.42, 0.29),
        (9.08, 4.27, 0.37),
        (8.82, 3.94, 0.46),
        (8.46, 3.73, 0.58),
        (8.04, 3.32, 0.65),
        (7.54, 2.83, 0.73),
    ]
    for (ax, ay, aw), (bx, by, bw) in zip(flow, flow[1:]):
        dx, dy = bx - ax, by - ay
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0, 1)
        wlocal = aw + t * (bw - aw)
        dsq = ((x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2) / (wlocal**2)
        field = np.maximum(field, 0.70 - dsq + 0.14 * mid + 0.048 * fine)
    # A wet joint leads a narrower finger away from the inner lip of the sill.
    spur = ellipse(10.10, 4.40, 0.22, 0.46, -0.31)
    field = np.maximum(field, 0.38 * spur + 0.08 * mid)
    wet = np.clip(field * 5.4 + 0.52, 0, 1)
    # Only a hair of sediment sits on the lip; most of the hall is quiet.
    tide = np.exp(-(((field + 0.10) / 0.144) ** 2)) * 0.85
    frac = lambda a: np.abs((a + 0.5) % 1 - 0.5)
    joint = np.minimum(frac((x + 0.38) / 1.36) * 1.36, frac((y - 0.27) / 1.36) * 1.36)
    tx = np.floor((x + 0.38) / 1.36).astype("int32")
    ty = np.floor((y - 0.27) / 1.36).astype("int32")
    stones = rng.normal(0, 1, (80, 80)).astype("float32")[ty % 80, tx % 80]
    grains = rng.normal(0, 1, (h, w)).astype("float32")
    value = 3.5 * broad + 2.3 * mid + 1.25 * fine + 1.1 * grains + 1.6 * stones
    value -= np.clip(1 - joint / 0.023, 0, 1) * (19 + 2.4 * np.tanh(mid))
    value += tide * 6.3
    base = np.array([126, 127, 120], dtype="float32")
    rgb = base[None, None, :] + value[:, :, None]
    rgb -= wet[:, :, None] * np.array([45, 42, 32], dtype="float32")
    # Sheltered terrazzo and its three mounting shoes record the missing bank.
    cx, cy, angle, count = LIFTED
    edge_y = np.abs(y - cy + 0.032 * mid)
    ends = np.clip((count * PITCH / 2 + 0.07 - np.abs(x - cx) + 0.08 * broad) / 0.30, 0, 1)
    old_polish = ends * np.exp(-((edge_y / 0.34) ** 4)) * (0.63 + 0.19 * np.tanh(mid)) * (1 - 0.65 * wet)
    rgb += old_polish[:, :, None] * np.array([12, 9, 3])
    for side in feet(count):
        fx, fy = on_bank(cx, cy, angle, side, 0)
        dx, dy = np.abs(x - fx), np.abs(y - fy)
        footprint = np.maximum(dx / 0.092, dy / 0.30)
        inner = np.clip((1.05 - footprint) * 4.8, 0, 1)
        lip = np.exp(-(((footprint - 1.14 - 0.055 * fine) / 0.20) ** 2))
        rgb += inner[:, :, None] * np.array([25, 18, 8])
        rgb += (lip * (0.72 + 0.20 * np.tanh(mid)))[:, :, None] * np.array([-19, -26, -26])
        for off in (-0.22, 0.24):
            hx, hy = on_bank(cx, cy, angle, side, off)
            dist = np.sqrt(((x - hx) / 0.034) ** 2 + ((y - hy) / 0.035) ** 2)
            hole = np.clip((1.2 - dist) * 3.5, 0, 1)
            collar = np.exp(-(((dist - 1.28) / 0.41) ** 2))
            rgb += hole[:, :, None] * np.array([-51, -49, -42]) + collar[:, :, None] * np.array([1, -14, -20])
    img = Image.fromarray(rgb.clip(0, 255).astype("uint8"))
    d = ImageDraw.Draw(img)

    def pix(px, py):
        return ((px + 15) / 26 * (w - 1), (16.8 - py) / 35.8 * (h - 1))

    # Chips follow expansion joints. Long fissures change direction at slab boundaries.
    for i in range(178):
        px = rng.uniform(-13, 10.2)
        py = rng.uniform(-16, 15.8)
        if i % 2:
            px = round((px + 0.38) / 1.36) * 1.36 - 0.38
        else:
            py = round((py - 0.27) / 1.36) * 1.36 + 0.27
        pts = [pix(px, py)]
        for j in range(int(rng.integers(2, 8))):
            px += rng.normal(0.045, 0.045)
            py += rng.normal(0.025, 0.05)
            pts.append(pix(px, py))
        ix, iy = map(int, pts[0])
        samp = np.asarray(img.getpixel((min(w - 1, max(0, ix)), min(h - 1, max(0, iy)))))
        color = tuple(np.clip(samp - rng.integers(8, 21), 0, 255).tolist())
        d.line(pts, fill=color, width=int(rng.integers(1, 3)))
    img.save(path / "terrazzo.png")
    # A thin sheet follows the uneven polish of the stone. Its changing
    # roughness and slope break reflected window light into short silver runs.
    rough = np.clip(
        0.52 + 0.11 * np.tanh(mid) + 0.04 * fine - wet * 0.433 + 0.19 * old_polish,
        0.048,
        0.89,
    )
    Image.fromarray(np.uint8(255 * rough)).save(path / "floor-rough.png")
    ripple = np.zeros_like(field)
    cx, cy, rad = DRIP
    radius = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    for off in [0.28, 0.56, 0.73, 0.94]:
        ripple += (
            0.24 * np.exp(-(((radius - off * rad) / 0.036) ** 2)) * np.clip(1 - radius / (1.7 * rad), 0, 1)
        )
    relief = (
        0.45
        + 0.10 * np.tanh(fine)
        + wet * (0.05 * np.sin(5 * x + 11 * y + mid * 0.29) + ripple)
        + 0.075 * np.tanh(mid)
    )
    Image.fromarray(np.uint8(255 * np.clip(relief, 0, 1))).save(path / "floor-relief.png")

    # A second set of local material maps records the thinning edge without
    # resampling the approved reflections in the rest of the hall.
    from drain_film import thinning
    change, transition = thinning(x, y, wet, mid, fine)
    film_rgb = np.asarray(img).astype(np.float32)
    film_rgb += change[..., None]*np.array([45,42,32],np.float32)
    pebbles = transition*(1.5*np.tanh(fine) + 1.2*np.tanh(grains))
    film_rgb += pebbles[...,None]
    Image.fromarray(np.uint8(np.clip(film_rgb,0,255))).save(path / "floor-film-colour.png")
    film_rough = np.clip(rough + .433*change + .035*transition, .048, .89)
    Image.fromarray(np.uint8(255*film_rough)).save(path / "floor-film-rough.png")
    film_relief = relief - change*(.05*np.sin(5*x+11*y+mid*.29)+ripple)
    Image.fromarray(np.uint8(255*np.clip(film_relief,0,1))).save(path / "floor-film-relief.png")



def painted_dial(path):
    im = Image.new("RGBA", (256, 256))
    d = ImageDraw.Draw(im)
    d.ellipse((3, 3, 252, 252), fill=(56, 64, 62), outline=(133, 136, 120), width=3)
    d.ellipse((12, 12, 243, 243), fill=(202, 187, 146), outline=(123, 121, 94), width=3)
    # A little amber staining on the lower gasket. The minute marks stay sharp.
    yy, xx = np.mgrid[:256, :256]
    radius = np.hypot(xx - 127.5, yy - 127.5)
    enamel_noise = noise(np.random.default_rng(2511), 256, 256, 23, 28)
    varnish = np.clip((radius - 92 + 1.5 * enamel_noise) / 22, 0, 1) ** 2
    varnish *= np.clip((yy - 75) / 133, 0.1, 1)
    face = np.array(im)
    enamel = radius < 112.8
    colour = face[:, :, :3].astype(float) - varnish[:, :, None] * np.array([8, 14, 20])
    face[:, :, :3][enamel] = np.uint8(np.clip(colour[enamel], 0, 255))
    im = Image.fromarray(face)
    d = ImageDraw.Draw(im)
    for k in range(60):
        ang = math.tau * k / 60
        sn, cs = math.sin(ang), math.cos(ang)
        r = 86 if k % 5 == 0 else 100
        d.line(
            (128 + r * sn, 128 - r * cs, 128 + 107 * sn, 128 - 107 * cs),
            fill=(48, 59, 56),
            width=6 if k % 5 == 0 else 2,
        )
    for ang, length, width in [(math.tau * 4.75 / 12, 56, 12), (math.tau * 45 / 60, 86, 7)]:
        d.line(
            (128, 128, 128 + length * math.sin(ang), 128 - length * math.cos(ang)),
            fill=(48, 54, 51),
            width=width,
        )
    d.ellipse((121, 121, 135, 135), fill=(97, 73, 58))
    im.save(path / "clock.png")


def decal_maps(path, *, large=False):
    rng = np.random.default_rng(17081)
    # Large number painted on a concrete pier. Its stencil has a narrow, cut-paper four.
    im = Image.new("RGBA", (336, 356))
    d = ImageDraw.Draw(im)
    paint = (74, 89, 87, 247)
    letters(d, (12, 19), "BERTH", paint, (6, 6), 2)
    d.rounded_rectangle((9, 85, 151, 323), radius=53, fill=paint)
    d.rounded_rectangle((47, 123, 112, 286), radius=21, fill=(0, 0, 0, 0))
    d.polygon(
        [
            (239, 85),
            (298, 85),
            (298, 229),
            (326, 229),
            (326, 267),
            (298, 267),
            (298, 323),
            (258, 323),
            (258, 267),
            (163, 267),
            (163, 229),
        ],
        fill=paint,
    )
    d.polygon([(258, 133), (258, 230), (198, 230)], fill=(0, 0, 0, 0))
    a = np.array(im)
    wear = noise(rng, 336, 356, 34, 40) + 0.35 * noise(rng, 336, 356, 114, 130)
    a[:, :, 3] = (a[:, :, 3] * np.clip((2.2 - wear) * 1.55, 0, 1)).astype("uint8")
    Image.fromarray(a).save(path / "berth.png")
    # Hinged split-flap display. A handful of characters remain; the lower row is blank.
    im = Image.new("RGB", (512, 124), (39, 46, 45))
    d = ImageDraw.Draw(im)
    d.rectangle((5, 4, 506, 120), outline=(90, 98, 88), width=2)
    letters(d, (15, 10), "DEPARTURES", (190, 183, 145), (3, 3), 1)
    letters(d, (388, 12), "TIME", (148, 157, 140), (2, 2), 2)
    d.line((12, 37, 499, 37), fill=(133, 135, 108), width=2)
    for row, line in enumerate(["NORTH SHORE    --:--", "                     "]):
        for j in range(24):
            x = 14 + j * 20
            y = 46 + row * 33
            c = int(rng.integers(39, 54))
            if row == 1 and 13 <= j <= 19:
                # Where the cassettes have been taken out, a dusty carrier rail
                # continues across the opening and the two exposed contacts remain.
                d.rectangle((x, y, x + 19, y + 23), fill=(88, 83, 66))
                d.rectangle((x, y + 14, x + 19, y + 16), fill=(136, 125, 91))
                d.rectangle((x + 5, y + 5, x + 8, y + 9), fill=(47, 53, 47))
                continue
            d.rectangle((x, y, x + 17, y + 23), fill=(c, c + 5, c + 2))
            if j < len(line):
                letters(d, (x + 3, y + 3), line[j], (170, 169, 145), (2, 2))
            d.line((x, y + 12, x + 17, y + 12), fill=(35, 38, 34))
    im.save(path / "departures.png")
    if large:
        from large_details import dial_paint
        dial_paint(path)
    else:
        painted_dial(path)
    # The network diagram has been pulled out. A ragged piece still clings under
    # the upper clamp and three hinges of yellowed tape mark the paper rectangle.
    w, h = 210, 290
    yy, xx = np.mgrid[:h, :w]
    n = noise(rng, w, h, 23, 44)
    stains = noise(rng, w, h, 57, 13)
    stock = np.array([158, 139, 106])[None, None, :] + (3.0 * n + 1.9 * stains)[:, :, None]
    rim = (xx < 12) | (xx > w - 13) | (yy < 19) | (yy > h - 18)
    stock[rim] *= np.array([0.80, 0.83, 0.81])
    im = Image.fromarray(np.uint8(np.clip(stock, 0, 255)))
    d = ImageDraw.Draw(im)
    d.polygon(
        [
            (12, 18),
            (138, 18),
            (131, 22),
            (103, 23),
            (90, 32),
            (97, 38),
            (67, 32),
            (54, 51),
            (35, 48),
            (25, 68),
            (12, 73),
        ],
        fill=(181, 187, 159),
    )
    d.polygon(
        [(12, 18), (138, 18), (118, 25), (81, 29), (68, 25), (52, 32), (12, 41)],
        fill=(77, 113, 106),
    )
    d.polygon(
        [(142, 273), (163, 261), (179, 263), (192, 243), (197, 241), (197, 274)],
        fill=(177, 174, 139),
    )
    for x, y in [(10, 15), (168, 14), (11, 258)]:
        d.rectangle((x, y, x + 27, y + 7), fill=(187, 160, 103))
    for x in [7, 202]:
        for y in [9, 281]:
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(77, 83, 73))
    im.save(path / "map.png")
    # Withdrawn-service circular pasted on the shutter, with old fold lines
    # and a tide of discoloured paste along the bottom edge.
    w, h = 168, 224
    yy, xx = np.mgrid[:h, :w]
    grain = noise(rng, w, h, 49, 61)
    wash = noise(rng, w, h, 17, 19)
    grime = np.clip((yy / h - 0.71) * 2 + 0.18 * wash, 0, 1)
    col = np.array([207, 196, 163])[None, None, :] + (2.8 * grain + 3.3 * wash)[:, :, None]
    col -= grime[:, :, None] * np.array([13, 21, 26])
    im = Image.fromarray(np.uint8(col.clip(0, 255)))
    d = ImageDraw.Draw(im)
    d.rectangle((11, 12, 156, 30), fill=(119, 73, 55))
    letters(d, (18, 17), "FERRY SERVICE", (229, 214, 174), (1, 1))
    letters(d, (13, 46), "ROUTE", (68, 71, 64), (3, 3))
    letters(d, (12, 77), "WITHDRAWN", (68, 71, 64), (2, 3))
    d.line((12, 113, 149, 113), fill=(116, 104, 85), width=2)
    for j, length in enumerate([119, 131, 94, 121, 84, 109]):
        d.line((13, 129 + 8 * j, 13 + length, 129 + 8 * j), fill=(126, 124, 104), width=2)
    d.line((4, 111, 164, 113), fill=(175, 165, 135))
    d.rectangle((105, 191, 143, 205), outline=(116, 92, 73), width=2)
    im.save(path / "withdrawn.png")
    im = Image.new("RGB", (238, 49), (70, 93, 83))
    d = ImageDraw.Draw(im)
    d.rectangle((2, 2, 235, 46), outline=(153, 161, 135), width=2)
    letters(d, (14, 13), "BOARDING", (208, 201, 164), (3, 3), 1)
    d.line((182, 24, 219, 24), fill=(204, 200, 168), width=6)
    d.polygon([(209, 13), (222, 24), (209, 35)], fill=(204, 200, 168))
    im.save(path / "boarding.png")


def timetable_map(path):
    """Two-colour pocket timetable, drawn in the printer’s unfolded layout."""
    w, h = 378, 216
    rng = np.random.default_rng(6194)
    y, x = np.mgrid[:h, :w]
    stain_edge = 186 + 10 * np.sin(x / 42) + 2 * np.cos(x / 14)
    stain = np.clip((y - stain_edge) / 9, 0, 1)
    fibre = 2 * noise(rng, w, h, 18, 12) + 1.2 * noise(rng, w, h, 94, 54)
    base = np.array([207, 206, 180]) + fibre[:, :, None] - stain[:, :, None] * np.array([12, 16, 15])
    paper = Image.fromarray(np.uint8(base.clip(0, 255)))
    d = ImageDraw.Draw(paper)
    blue, red, light = (65, 91, 93), (156, 100, 77), (216, 212, 185)
    d.rectangle((6, 8, 119, 49), fill=blue)
    letters(d, (13, 18), "FERRY", light, (3, 3))
    d.line((7, 57, 118, 57), fill=red, width=4)
    letters(d, (12, 68), "ESTUARY", blue, (2, 2))
    letters(d, (12, 89), "SAILINGS", blue, (2, 2))
    # A small diagram: the channel bends around a headland and two piers.
    d.polygon(
        [(6, 145), (28, 139), (45, 148), (68, 132), (111, 133), (119, 139), (119, 186), (6, 186)],
        fill=(153, 168, 156),
    )
    d.line([(13, 158), (31, 153), (53, 158), (81, 145), (112, 145)], fill=blue, width=3)
    for xx, yy in [(13, 158), (53, 158), (81, 145), (112, 145)]:
        d.ellipse((xx - 3, yy - 3, xx + 3, yy + 3), fill=red)
    for x0, name in [(134, "NORTH SHORE"), (260, "TOWN QUAY")]:
        d.rectangle((x0, 12, x0 + 107, 28), fill=blue)
        letters(d, (x0 + 4, 16), name, light)
        for j in range(10):
            yy = 42 + j * 14
            d.line((x0, yy, x0 + 106, yy), fill=(159, 163, 146), width=1)
            for k in range(3):
                letters(d, (x0 + 1 + k * 37, yy + 3), f"{5 + j:02d}:{(k * 20 + 5):02d}", blue, (1, 1))
        d.line((x0, 187, x0 + 60, 187), fill=red, width=3)
    paper.save(path / "pocket-timetable.png")


def make(path, *, large=False):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    floor_maps(path)
    decal_maps(path, large=large)
    timetable_map(path)
    import patina
    import sea_sky
    from surface_marks import make as make_marks

    wall = patina.make(path)
    wall = sea_sky.make(path, wall)
    make_marks(path, wall)


if __name__ == "__main__":
    import sys

    make(sys.argv[1])
