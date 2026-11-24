"""Worn handwriting, chalk, and moisture deposits, painted in the surfaces' own coordinates."""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from paint import noise
from patina import curve
from layout import BOAT_LINES, wick_height


def stroke(mask, spans, width, strength=255, phase=0):
    """A pressure-sensitive brush along a chain of cubic Béziers, in paper coordinates."""
    points = []
    for span in spans:
        points.extend(curve(span, 26)[:-1])
    points.append(spans[-1][-1])
    xy = np.asarray(points) * np.asarray(mask.size)
    distance = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    t = np.r_[0, np.cumsum(distance)] / max(1, distance.sum())
    direction = np.gradient(xy, axis=0)
    normal = np.c_[-direction[:, 1], direction[:, 0]]
    normal /= np.maximum(0.0001, np.linalg.norm(normal, axis=1, keepdims=True))
    taper = np.minimum(np.minimum(t / 0.069, (1 - t) / 0.082), 1).clip(0, 1)
    pressure = (0.33 + 0.67 * taper) * (
        0.88 + 0.11 * np.sin(t * 5.5 + phase) + 0.046 * np.sin(t * 27 + phase)
    )
    edge = 0.5 * width * pressure[:, None] * normal
    polygon = np.vstack((xy + edge, (xy - edge)[::-1]))
    ImageDraw.Draw(mask).polygon([tuple(p) for p in polygon], fill=strength)


def write_tag(path, wall):
    # The writer leans two joined initials forward and then returns under them.
    w, h = 460, 208
    ink = Image.new("L", (w, h))
    stroke(
        ink,
        [
            [(0.04, 0.69), (0.13, 0.69), (0.27, 0.28), (0.39, 0.18)],
            [(0.39, 0.18), (0.52, 0.09), (0.37, 0.44), (0.21, 0.77)],
        ],
        16,
        232,
    )
    stroke(
        ink,
        [
            [(0.16, 0.59), (0.30, 0.37), (0.54, 0.20), (0.58, 0.33)],
            [(0.58, 0.33), (0.64, 0.47), (0.43, 0.63), (0.31, 0.53)],
            [(0.31, 0.53), (0.41, 0.54), (0.46, 0.80), (0.57, 0.72)],
            [(0.57, 0.72), (0.67, 0.62), (0.70, 0.35), (0.73, 0.37)],
            [(0.73, 0.37), (0.78, 0.41), (0.64, 0.67), (0.68, 0.66)],
            [(0.68, 0.66), (0.78, 0.58), (0.85, 0.32), (0.87, 0.39)],
            [(0.87, 0.39), (0.92, 0.48), (0.76, 0.72), (0.90, 0.62)],
        ],
        17,
        249,
        1.2,
    )
    stroke(ink, [[(0.24, 0.89), (0.40, 0.78), (0.68, 0.79), (0.94, 0.67)]], 8.9, 195, 2)
    stroke(ink, [[(0.67, 0.22), (0.70, 0.15), (0.74, 0.12), (0.77, 0.12)]], 6.8, 194)
    rng = np.random.default_rng(8530)
    grain = noise(rng, w, h, 166, 82)
    pores = noise(rng, w, h, 44, 21)
    raw = np.asarray(ink).astype(float) / 255
    fog = np.asarray(ink.filter(ImageFilter.GaussianBlur(2.6))).astype(float) / 255
    alpha = np.clip(0.84 * raw + 0.065 * fog, 0, 1) * np.clip(0.83 + 0.17 * grain - 0.14 * pores, 0.27, 1)
    rgba = np.empty((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = np.uint8(np.clip(np.array([73, 57, 82]) + grain[:, :, None] * 3, 0, 255))
    rgba[:, :, 3] = np.uint8(alpha * 255)
    tag = Image.fromarray(rgba)
    wall = wall.convert("RGBA")
    x = lambda p: round((p + 12.55) * wall.width / (4.54 + 12.55))
    y = lambda z: round((1 - z / 7.68) * wall.height)
    left, right = x(-0.49), x(1.02)
    top, bottom = y(2.00), y(1.23)
    wall.alpha_composite(tag.resize((right - left, bottom - top), Image.Resampling.LANCZOS), (left, top))
    wall.convert("RGB").save(path / "end-wall.png")

    # A second hand, a tiny folded-paper boat scratched through the weathered coating.
    w, h = 320, 148
    boat = Image.new("L", (w, h))

    def line(points, weight, strength):
        d = ImageDraw.Draw(boat)
        d.line([(round(x * w), round(y * h)) for x, y in points], fill=strength, width=weight, joint="curve")

    for points, width, patina in zip(BOAT_LINES, (11, 9, 8, 6), (245, 224, 193, 173)):
        line(points, width, patina)
    wear = noise(rng, w, h, 105, 44) + 0.55 * noise(rng, w, h, 31, 17)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = np.array([190, 196, 183])
    rgba[:, :, 3] = np.uint8(np.asarray(boat).astype(float) * 0.86 * np.clip(0.83 + 0.24 * wear, 0.20, 1))
    Image.fromarray(rgba).save(path / "chalk-boat.png")


def layer(image, colour, opacity):
    rgba = np.empty((*opacity.shape, 4), dtype=np.uint8)
    rgba[:, :, :3] = np.uint8(np.clip(colour, 0, 255))
    rgba[:, :, 3] = np.uint8(255 * np.clip(opacity, 0, 1))
    return Image.alpha_composite(image, Image.fromarray(rgba))


def rain(path):
    rng = np.random.default_rng(30914)
    w, h = 476, 300
    row, col = np.mgrid[:h, :w]
    off = 0.87 - 1.76 * col / (w - 1)
    fall = row / (h - 1)
    broad = noise(rng, w, h, 25, 14)
    grain = noise(rng, w, h, 96, 89)
    stream = 0.032 * np.sin(fall * 4.8) - 0.060 * fall + 0.013 * np.sin(fall * 19)
    width = 0.16 + 0.21 * fall**1.3 + 0.030 * broad
    plume = np.exp(-(((off - stream) / np.clip(width, 0.08, 0.46)) ** 2))
    base = np.exp(-(((1 - fall) / (0.10 + 0.055 * np.exp(-((off / 0.55) ** 2)))) ** 2)) * np.exp(
        -((off / 0.54) ** 2)
    )
    image = Image.new("RGBA", (w, h))
    soft = np.clip(0.53 * plume * (0.85 + 0.14 * broad) + 0.46 * base, 0, 0.78)
    image = layer(image, np.array([47, 58, 56]) + grain[:, :, None] * 3, soft)
    veins = np.zeros((h, w))
    for start, rad, length, weight in [
        (-0.15, 0.039, 0.74, 0.67),
        (-0.061, 0.021, 0.83, 0.44),
        (0.012, 0.049, 0.99, 0.73),
        (0.069, 0.014, 0.52, 0.54),
        (0.103, 0.019, 0.77, 0.42),
        (0.19, 0.014, 0.29, 0.38),
    ]:
        center = start + stream * (0.54 + 2 * abs(start)) + 0.008 * np.sin(fall * 17 + start * 16)
        fade = np.clip((length - fall) * 13, 0, 1)
        veins = np.maximum(
            veins, weight * fade * np.exp(-(((off - center) / (rad * (0.90 + 0.18 * fall))) ** 2))
        )
    image = layer(
        image, np.array([34, 44, 42]) + grain[:, :, None] * 3, veins * np.clip(0.91 + 0.13 * grain, 0.50, 1)
    )
    # The old evaporating edge wanders across the newer dark run and peters out.
    edge = np.abs(off - stream) / np.clip(width + 0.018 * grain, 0.08, 0.47)
    bloom = np.exp(-(((edge - 1.08) / 0.16) ** 2)) * np.clip(0.59 + 0.23 * broad + 0.16 * grain, 0, 0.88)
    bloom *= 0.62 + 0.38 * fall
    image = layer(image, np.array([181, 183, 166]) + grain[:, :, None] * 4, bloom)
    image.save(path / "sill-runoff.png")

    # A single unwrapped damp patch on the two visible faces of the nearest pier.
    w, h = 384, 173
    row, col = np.mgrid[:h, :w]
    u = -0.5 + 1.17 * col / (w - 1)
    z = 0.55 * (1 - row / (h - 1))
    n = noise(rng, w, h, 35, 14)
    grit = noise(rng, w, h, 151, 63)
    form = np.array([wick_height(d) for d in u[0]])[None, :] + 0.013 * n
    amount = np.clip((form - z) / 0.095 + 0.38, 0, 1) * np.clip(0.65 + 0.15 * n + 0.1 * grit, 0.35, 0.91)
    im = Image.new("RGBA", (w, h))
    im = layer(im, np.array([61, 70, 66]) + grit[:, :, None] * 3, amount)
    lip = np.exp(-(((z - form - 0.009 * grit) / 0.016) ** 2)) * np.clip(
        0.59 + 0.16 * n + 0.30 * grit, 0.07, 0.82
    )
    im = layer(im, np.array([164, 164, 146]) + grit[:, :, None] * 4, lip)
    im.save(path / "pier-bloom.png")


def make(path, wall):
    write_tag(path, wall)
    rain(path)
