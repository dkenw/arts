"""Procedurally paint an overcast estuary sky and the erosion below a failed parapet joint."""

import math
import numpy as np
from PIL import Image, ImageDraw
from paint import noise


def make(path, wall):
    rng = np.random.default_rng(405)
    w, h = 1632, 816
    yy, xx = np.mgrid[:h, :w]
    elevation = (0.5 - yy / h) * math.pi
    low = noise(rng, w, h, 35, 45)
    fine = noise(rng, w, h, 99, 110)
    deg = elevation * 180 / math.pi
    belt = deg - 4.1 - 1.0 * np.sin(xx / 86) - 0.44 * low
    clouds = np.exp(-((belt / 3.1) ** 2)) * np.clip(0.55 + 0.20 * low + 0.12 * fine, 0.05, 1)
    light = np.exp(-(((deg - 1.1) / 2.14) ** 2))
    high = np.clip(deg / 60, 0, 1)
    tone = 9.5 * light - 23 * clouds - 21 * high + 2 * low + 1.15 * fine
    base = np.array([216, 225, 228])[None, None, :]
    sky = base + tone[:, :, None]
    sky[:, :, 0] -= 3 * high
    sky[:, :, 2] += 2 * high
    Image.fromarray(np.uint8(np.clip(sky, 0, 255))).save(path / "sea-sky.png")
    # Salt eats into the wall from a failed seam, leaving a hard pale edge to the old paint.
    w, h = wall.size
    ar = np.array(wall, dtype=np.float32)
    yy, xx = np.mgrid[:h, :w]
    low = noise(rng, w, h, 87, 33)
    fine = noise(rng, w, h, 279, 145)
    for x, y, xr, yr in [
        (1660, 260, 32, 152),
        (1592, 560, 22, 74),
        (1320, 740, 89, 22),
        (453, 316, 55, 28),
        (891, 715, 63, 38),
    ]:
        # Gravity-directed tangles of surviving plaster and darker revealed mortar.
        dist = ((xx - x - 9 * np.sin(yy / 32)) / xr) ** 2 + ((yy - y) / yr) ** 2
        field = 1 - dist + 0.32 * low + 0.25 * fine
        core = np.clip(field * 3.5, 0, 0.88)
        lip = np.exp(-(((field + 0.06) / 0.13) ** 2))
        target = np.array([110, 117, 105])[None, None, :] + (6.5 * low + 3 * fine)[:, :, None]
        ar = ar * (1 - core[:, :, None]) + target * core[:, :, None] + 6 * lip[:, :, None]
    im = Image.fromarray(np.uint8(ar.clip(0, 255)))
    d = ImageDraw.Draw(im, "RGBA")
    for k in range(38):
        x = float(rng.normal(1630, 26))
        yb = float(rng.uniform(35, 123))
        end = yb + rng.uniform(75, 224)
        d.polygon(
            [
                (x, yb),
                (x + rng.uniform(2, 6), yb),
                (x + 3.0, yb + 0.61 * (end - yb)),
                (x + rng.uniform(-3.5, 3.5), end),
            ],
            fill=(96, 87, 69, int(rng.uniform(21, 58))),
        )
    return im
