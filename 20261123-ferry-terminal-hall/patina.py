"""Painted tile, salt bloom, glazing, and the relief of migrating terns."""

import math
import numpy as np
from PIL import Image, ImageDraw
from paint import noise


def curve(points, count=18):
    a, b, c, d = (np.array(k, dtype=float) for k in points)
    return [
        tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t**3 * d)
        for t in np.linspace(0, 1, count)
    ]


def wall(rng):
    w, h = 1794, 806
    yy, xx = np.mgrid[:h, :w]
    n = noise(rng, w, h, 31, 14)
    n2 = noise(rng, w, h, 141, 70)
    trails = noise(rng, w, h, 175, 5)
    height = 1 - yy / h
    tide_height = 0.11 + 0.027 * np.sin(xx / 143) + 0.021 * noise(rng, w, h, 27, 2)
    damp = np.clip((tide_height - height) * 9 + 0.29, 0, 1)
    breath = np.exp(-(((height - tide_height) / 0.021) ** 2))
    base = np.array([174, 167, 148])[None, None, :]
    rgb = base + (5.2 * n + 2.3 * n2 + 2.6 * trails - 12 * damp + 4.2 * breath)[:, :, None]
    img = Image.fromarray(np.uint8(rgb.clip(0, 255)))
    d = ImageDraw.Draw(img, "RGBA")
    # Pour lines and rusty drips below the old form ties.
    for y in [104, 214, 324, 438, 550, 664]:
        d.line((0, y, w, y), fill=(44, 52, 46, 44), width=1)
        d.line((0, y + 1, w, y + 1), fill=(218, 213, 184, 45), width=1)
        for x in range(24 + (y % 3) * 33, w, 118):
            if rng.random() < 0.16:
                continue
            d.ellipse((x - 1, y + 11, x + 2, y + 13), fill=(78, 82, 70, 93))
            if rng.random() < 0.42:
                l = int(rng.uniform(8, 45))
                d.polygon(
                    [
                        (x - 1, y + 14),
                        (x + 2, y + 14),
                        (x + 3, y + 21),
                        (x, y + 14 + l),
                    ],
                    fill=(92, 82, 63, 45),
                )
    # Five long low shapes painted in aging ceramic glaze, in the manner of a port frieze.
    mW, mH = 1190, 217
    my = 136
    mx = 161
    mr = noise(rng, mW, mH, 28, 8)
    gr = noise(rng, mW, mH, 125, 36)
    mbase = np.array([147.0, 158.0, 141.0]) + (mr * 3 + gr * 1.3)[:, :, None]
    mural = Image.fromarray(np.uint8(mbase.clip(0, 255)))
    md = ImageDraw.Draw(mural)
    for i, (color, baseline, amp) in enumerate(
        [
            ((140, 149, 124), 135, 22),
            ((91, 139, 129), 169, 18),
            ((84, 120, 129), 180, 20),
            ((163, 145, 112), 207, 10),
        ]
    ):
        a = [
            (
                x,
                (
                    baseline
                    + 0.020 * x
                    + amp * math.sin(x / (110 + 35 * i) + i * 0.9)
                    + 9 * math.sin(x / 64 + i)
                ),
            )
            for x in range(-5, mW + 8, 5)
        ]
        md.polygon(a + [(mW + 3, mH + 2), (-5, mH + 2)], fill=color)
    # The banks wind past one another, then fade into the same empty sea as the windows.
    for xx0, yy0, wide in [(190, 172, 141), (690, 177, 213), (850, 191, 84)]:
        md.polygon(
            [
                (xx0, yy0 + 5),
                (xx0 + wide * 0.2, yy0),
                (xx0 + wide, yy0 + 2),
                (xx0 + wide * 0.47, yy0 + 5),
            ],
            fill=(167, 169, 146),
        )

    def tern(x, y, scale, tilt):
        # A bird in profile, one crescent wing exposed and the other foreshortened.
        def place(p):
            u, v = p
            u *= scale
            v *= scale
            return (
                x + u * math.cos(tilt) - v * math.sin(tilt),
                y + u * math.sin(tilt) + v * math.cos(tilt),
            )

        def shape(parts, color):
            q = []
            for p in parts:
                q.extend(curve(p))
            md.polygon([place(p) for p in q], fill=color)

        shape(
            [
                [(-90, 24), (-63, 11), (-28, 0), (-8, 0)],
                [(-8, 0), (1, -1), (9, -10), (21, -10)],
                [(21, -10), (27, -10), (29, -6), (39, -4)],
                [(39, -4), (23, -2), (11, 4), (6, 7)],
                [(6, 7), (-16, 17), (-41, 18), (-54, 20)],
                [(-54, 20), (-70, 20), (-74, 24), (-90, 24)],
            ],
            (62, 85, 84),
        )
        shape(
            [
                [(-22, 9), (-52, -2), (-68, -28), (-106, -69)],
                [(-106, -69), (-82, -59), (-49, -40), (-30, -29)],
                [(-30, -29), (-17, -20), (-10, -9), (0, 2)],
                [(0, 2), (-2, 3), (-12, 9), (-22, 9)],
            ],
            (71, 94, 94),
        )
        shape(
            [
                [(-23, 8), (-45, 20), (-77, 37), (-130, 51)],
                [(-130, 51), (-94, 27), (-55, 3), (-38, -2)],
                [(-38, -2), (-33, -4), (-27, 3), (-23, 8)],
            ],
            (96, 119, 113),
        )
        shape(
            [
                [(-36, 2), (-52, -6), (-71, -31), (-88, -48)],
                [(-88, -48), (-63, -31), (-43, -19), (-22, 1)],
                [(-22, 1), (-30, 5), (-35, 2), (-36, 2)],
            ],
            (153, 162, 141),
        )

    tern(594, 92, 1.27, -0.095)
    tern(858, 62, 0.85, -0.16)
    tern(1054, 98, 0.57, 0.06)
    ma = np.array(mural).astype("float32")
    # Individual ceramic tesserae are deliberately low contrast except where pieces are gone.
    ty, tx = np.mgrid[:mH, :mW]
    tile = 9
    tints = rng.normal(0, 2.1, (mH // tile + 1, mW // tile + 1))[ty // tile, tx // tile]
    joints = ((tx % tile == 0) | (ty % tile == 0))[:, :, None]
    ma += tints[:, :, None]
    ma = np.where(joints, 0.50 * ma + 0.50 * np.array([134, 141, 126]), ma)
    broken = noise(rng, mW, mH, 85, 17) + 0.59 * mr
    loss = np.clip((broken - 1.5) * 0.90, 0, 1)
    ma = ma * (1 - loss[:, :, None]) + (np.array([167, 166, 149]) + 4 * mr[:, :, None]) * loss[:, :, None]
    # Irregular surviving edges, damp gaps and trails.
    opacity = np.clip(1 - 0.37 * (np.maximum(0, mr + gr * 0.4 - 0.45)), 0.19, 0.99)
    edges = np.minimum.reduce([tx + np.zeros_like(ty), mW - 1 - tx, ty + 4, mH - 1 - ty + 4])
    opacity *= np.clip((edges + 4 * gr) / 3, 0, 1)
    img.paste(
        Image.fromarray(np.uint8(ma.clip(0, 255))),
        (mx, my),
        Image.fromarray(np.uint8(opacity * 255)),
    )
    d = ImageDraw.Draw(img, "RGBA")
    # Paint bleed under the roof drip and a recessed rectangle left by an older plate.
    for _ in range(88):
        x = int(rng.uniform(0, w))
        top = int(rng.uniform(0, 18))
        length = int(rng.uniform(12, 174))
        if rng.random() < 0.55:
            x = int(rng.choice([75, 402, 930, 1184, 1575]) + rng.normal(0, 8))
        d.polygon(
            [(x, top), (x + int(rng.uniform(1, 5)), top), (x + 1, top + length)],
            fill=(67, 75, 63, int(rng.uniform(12, 44))),
        )
    return img


def glazing(out, rng):
    w, h = 400, 500
    n = noise(rng, w, h, 20, 24)
    m = noise(rng, w, h, 70, 50)
    yy, xx = np.mgrid[:h, :w]
    edge = np.minimum(xx, w - 1 - xx)
    rim = np.exp(-edge / 13) + 0.9 * np.exp(-(h - 1 - yy) / 28) + 0.42 * np.exp(-yy / 13)
    streak = noise(rng, w, h, 84, 4)
    alpha = np.clip(
        0.025
        + 0.067 * rim
        + 0.016 * n
        + 0.009 * m
        + 0.033 * np.maximum(streak - 0.45, 0) * np.exp(-yy / 280),
        0.008,
        0.28,
    )
    im = Image.fromarray(np.uint8(255 * alpha))
    d = ImageDraw.Draw(im)
    for _ in range(39):
        x = int(rng.uniform(1, w - 1))
        y = int(rng.uniform(-4, 20) if rng.random() < 0.63 else rng.uniform(250, 480))
        L = int(rng.uniform(15, 156))
        delta = rng.choice([-2, -1, 0, 0, 1, 2])
        d.line(
            (x, y, x + delta, y + L * 0.68, x + delta, y + L),
            fill=int(rng.uniform(12, 39)),
            width=int(rng.choice([1, 1, 2])),
        )
    im.save(out / "glass-salt.png")
    # Sea-green ceramic tiles on the office apron.
    w, h = 900, 180
    y, x = np.mgrid[:h, :w]
    tw, th = 29, 20
    n = noise(rng, w, h, 31, 8)
    m = noise(rng, w, h, 80, 30)
    tint = rng.normal(0, 4.3, (h // th + 1, w // tw + 1))[y // th, x // tw]
    c = np.array([68, 108, 97])[None, None, :] + (tint + 3 * n + m)[:, :, None]
    grout = (x % tw < 1) | (y % th < 1)
    bevel = (x % tw == 1) | (y % th == 1)
    c[grout] = np.array([122, 128, 111])
    c[bevel] += 7
    chip = (n + 0.8 * m > 2.78) & ((x % tw < 5) | (y % th < 5))
    c[chip] = np.array([145, 144, 122])
    Image.fromarray(np.uint8(c.clip(0, 255))).save(out / "counter-tile.png")


def make(out):
    rng = np.random.default_rng(6236)
    image = wall(rng)
    glazing(out, rng)
    return image
