"""Print the shared ferry-terminal scene at its two native drawing scales."""

import json
from pathlib import Path
import numpy as np
from PIL import Image, PngImagePlugin
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

from capture_passes import print_passes, require_passes
from exposure_filter import clean as filter_exposure, luma
from output_files import staged_output

# The actual eighty inks of Edition IV. Keeping their order also makes a
# palette-index comparison between the two prints possible.
PALETTE = np.frombuffer(
    bytes.fromhex(
        "64707a 465360 55626d 323c48 3c4754 2a323c 212730 555c62 74848e 1f2e37 "
        "95a2a3 889391 a4b0b1 1d2129 272e36 4c5359 7e8f95 171d26 656b6c 36414c "
        "6b7a84 bdc3c2 2f3640 3d444b 9aa8aa 414e58 5d6265 768282 c8cdc8 333b42 "
        "4c5a64 727878 838a86 242b34 19242c 5a6972 d2d6d3 c7c7b8 10161f a3a79e "
        "b8b9ac 8c999d 2b3942 daddd8 647578 434a52 b0b9b9 729a8b 1c2930 85a99a "
        "bcc1b8 959a93 acb2aa e0e4de 23343a 5b8277 446863 51736b d5d6ca 355554 "
        "9ab4a3 2a4347 314c4e 263c40 947455 ced0c4 4c4944 3f5d5b 6c7c6e 899f91 "
        "a78b67 718d80 caab8d adbfae 77604e a47d5e 5f5145 7d725d ac9977 48383a"
    ),
    dtype=np.uint8,
).reshape(-1, 3)


def metric(srgb):
    a = np.clip(srgb / 255, 0, 1)
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    lms = lin @ np.array(
        [
            [0.41222147, 0.21190350, 0.08830246],
            [0.53633254, 0.68069955, 0.28171884],
            [0.05144599, 0.10739696, 0.62997870],
        ]
    )
    lab = np.cbrt(lms) @ np.array(
        [
            [0.21045426, 1.97799850, 0.02590404],
            [0.79361779, -2.42859221, 0.78277177],
            [-0.00407205, 0.45059371, -0.80867577],
        ]
    )
    return lab * np.array([1.0, 1.60, 1.48])


def filter_grain(rgb):
    guide = ndi.median_filter(luma(rgb), size=3, mode="nearest")
    # The local reference follows actual edges, allowing different runs of concrete
    # pixels to coalesce without filling in the dark edge of a handrail or a clock hand.
    radius = 2
    pg = np.pad(guide, radius, mode="edge")
    pr = np.pad(rgb, ((radius, radius), (radius, radius), (0, 0)), mode="edge")
    h, w = guide.shape
    out = np.zeros_like(rgb)
    total = np.zeros_like(guide)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            gy = radius + dy
            gx = radius + dx
            gap = pg[gy : gy + h, gx : gx + w] - guide
            ok = np.exp(-gap * gap / (2 * 7.2**2) - 0.5 * (dy * dy + dx * dx) / 1.18**2)
            total += ok
            out += pr[gy : gy + h, gx : gx + w] * ok[:, :, None]
    return out / total[:, :, None]


def cluster_midtones(rgb):
    # Join adjacent steps of value on the dry floor and in the soffit. A
    # resistant centre keeps the outlines of the hands, chains and seat lips.
    lum = luma(rgb)
    centre = ndi.median_filter(lum, size=3)
    broad = ndi.gaussian_filter(centre, 1.1)
    gradient = np.hypot(ndi.sobel(broad, axis=1), ndi.sobel(broad, axis=0)) / 8
    quiet = 1 - np.clip((gradient - 1.35) / 4.8, 0, 1)
    keep = np.exp(-(((lum - centre) / 7.3) ** 2))
    adjacent = ndi.gaussian_filter(rgb, (1.08, 1.08, 0))
    return rgb + (adjacent - rgb) * (0.58 * quiet * keep)[:, :, None]


def colour_grade(rgb, *, large):
    h, w = rgb.shape[:2]
    scale = w / 528
    if not large:
        rgb = cluster_midtones(rgb)
    lum = luma(rgb)
    x = np.array([0, 17, 36, 56, 80, 106, 132, 158, 184, 208, 229, 247, 255])
    stops = np.array(
        [
            [11, 16, 23],
            [23, 27, 36],
            [38, 43, 54],
            [56, 63, 76],
            [77, 86, 99],
            [101, 111, 122],
            [126, 136, 143],
            [152, 160, 164],
            [180, 185, 184],
            [207, 211, 208],
            [224, 230, 224],
            [239, 242, 234],
            [246, 246, 234],
        ]
    )
    base = np.stack([np.interp(lum, x, stops[:, i]) for i in range(3)], axis=-1)
    chroma = rgb - lum[:, :, None]
    oxide = np.clip((rgb[:, :, 0] - rgb[:, :, 1] - 3) / 17, 0, 1)
    marine = np.clip((rgb[:, :, 1] - rgb[:, :, 0] - 5) / 14, 0, 1)
    gain = (
        np.interp(lum, [0, 45, 120, 185, 255], [0.59, 0.83, 0.98, 0.80, 0.41]) + 0.56 * oxide + 0.33 * marine
    )[:, :, None]
    result = base + gain * chroma
    # Restrained ink on the inside of abrupt edges and readable metal glints.
    local_radius = 0.65 * np.sqrt(scale) if large else 0.68
    local = ndi.gaussian_filter(lum, local_radius)
    edge = np.clip((lum - local) * 0.65, -6, 4.3) + np.clip(
        0.22 * (lum - ndi.gaussian_filter(lum, 5 * scale)), -5.6, 6.0
    )
    yy, xx = np.ogrid[:h, :w]
    falloff = ((xx / w - 0.58) / 0.75) ** 2 + ((yy / h - 0.45) / 0.88) ** 2
    result *= np.clip(1.035 - 0.057 * falloff, 0.93, 1.035)[:, :, None]
    result = np.clip(result + edge[:, :, None], 0, 255)
    light = luma(result)
    separation = np.interp(
        light, [0, 25, 48, 75, 102, 132, 161, 198, 222, 255], [0, -0.2, -2, -4, -2, 1.4, 3.2, 4, 2, 0]
    )
    result = np.clip(result + separation[:, :, None], 0, 255)
    light = luma(result)
    slate = np.exp(-(((light - 102) / 45) ** 2))
    pearl = np.clip((light - 126) / 65, 0, 1) * np.clip((245 - light) / 34, 0, 1)
    return np.clip(
        result
        + slate[:, :, None] * np.array([2.4, -0.65, 0.65])
        + pearl[:, :, None] * np.array([3.3, 0.38, -1.3]),
        0,
        255,
    )


INKS = {
    "blue ink": (-31, -22, -17),
    "rust ink": (12, -4, -12),
    "paper fold": (41, 40, 33),
    "nickel": (18, 21, 20),
    "varnish": (20, 13, 7),
    "spall": (14, 14, 10),
    "bleed": (-13, -13, -12),
    "hairline": (-21, -18, -14),
    "glass": (-16, -14, -9),
    "water": (15, 18, 17),
    "chalk": (36, 34, 27),
    "damp": (-22, -24, -23),
    "old seepage": (-12, -23, -30),
    "dry silt": (-26, -29, -26),
    "lime trace": (22, 21, 15),
    "mineral": (29, 29, 22),
    "linen": (23, 27, 23),
    "cork paint": (19, -4, -13),
    "rope shade": (-24, -23, -19),
    "oxide": (7, -4, -9),
}


def rgb_image(path):
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.float32)


def blend_clock(base, source, *, large):
    from clock_glass import BOUNDS

    lens = rgb_image(source.with_suffix(".glass.png"))
    if lens.shape != base.shape:
        raise ValueError("The clock and room exposures must use the same camera resolution.")
    h, w = base.shape[:2]
    left, top, right, bottom = BOUNDS
    yy, xx = np.ogrid[:h, :w]
    nx, ny = (xx + 0.5) * 528 / w, (yy + 0.5) * 396 / h
    edge = np.minimum(np.minimum(nx - left, right - nx), np.minimum(ny - top, bottom - ny))
    coverage = np.clip((edge - 1) / 4, 0, 1)
    if not large:
        weight = (0.27 * coverage).astype(np.float32)
        return base + (lens - base) * weight[..., None]
    direct = rgb_image(source.with_suffix(".direct.png"))
    if direct.shape != base.shape:
        raise ValueError("The enamel exposure must use the full camera resolution.")
    glazed = direct + 0.27 * (lens - direct)
    return base + coverage.astype(np.float32)[..., None] * (glazed - base)


def apply_marks(graded, base, markings):
    for kind, strength, points in json.loads(markings.read_text()):
        xy = np.asarray(points, dtype=np.int32)
        ix, iy = xy[:, 0], xy[:, 1]
        adaptation = np.clip(0.49 + 0.0022 * luma(base[iy, ix]), 0.51, 1.02)
        ink = np.asarray(INKS[kind], dtype=graded.dtype)
        graded[iy, ix] += ink * strength * adaptation[:, None]


def indexed_print(colour):
    """Quantise the newly sampled grid, with the same ink distances and dither as IX."""
    height, width = colour.shape[:2]
    tree = cKDTree(metric(PALETTE.astype(float)))
    pattern = np.array([[0,9,2,11],[13,5,15,7],[3,10,1,8],[14,6,12,4]], np.float32)
    pat = (pattern / 15 - 0.5) * 1.65
    idx = np.empty((height, width), dtype=np.uint8)
    yy, xx = np.ogrid[:height, :width]
    for row in range(0,height,128):
        stop = min(height, row+128)
        values = colour[row:stop] + pat[yy[row:stop] % 4, xx % 4][...,None]
        _, nearest = tree.query(metric(values).reshape(-1,3))
        idx[row:stop] = nearest.reshape(stop-row,width)
    padded = np.pad(idx, 1, mode="edge")
    agree = np.zeros_like(idx)
    for dy, dx in ((0,1),(1,0),(1,2),(2,1),(0,0),(0,2),(2,0),(2,2)):
        agree += idx == padded[dy:dy+height, dx:dx+width]
    lum = luma(colour.astype(np.float32, copy=False))
    lonely = (agree == 0) & (ndi.maximum_filter(lum,3) - ndi.minimum_filter(lum,3) < 10)
    if lonely.any():
        blurred = ndi.gaussian_filter(colour, (0.82,0.82,0))
        _, idx[lonely] = tree.query(metric(blurred[lonely]))
    inked = Image.fromarray(idx, "P")
    inked.putpalette(PALETTE.tobytes())
    return inked


def original_grid(raw):
    # The centre-weighted mix keeps thin fittings legible on the 528-pixel grid.
    smooth = filter_grain(raw)
    high = Image.fromarray(np.uint8(np.clip(smooth + 0.5, 0, 255)))
    size = (528, 396)
    box = np.asarray(high.resize(size, Image.Resampling.BOX), dtype=np.float32)
    lanczos = np.asarray(high.resize(size, Image.Resampling.LANCZOS), dtype=np.float32)
    return 0.62 * box + 0.38 * lanczos


def camera_layer(source, suffix, channel, frame):
    rgb = rgb_image(source.with_suffix(suffix))
    if frame is not None:
        from harbour_plate import restore_frame_context
        restore_frame_context(rgb, channel, frame)
    return rgb


def large_grid(raw, source, frame):
    normal = camera_layer(source, ".normal.png", "normal", frame)
    albedo = camera_layer(source, ".albedo.png", "albedo", frame)
    if raw.shape != normal.shape or raw.shape != albedo.shape:
        raise ValueError("The exposure and its guides must use the same pixel grid.")
    return filter_exposure(raw, normal, albedo)


def develop(source, *, large, frame=None):
    from berth_concrete import SITES as berth_sites, material as berth_material
    from concrete_wear import SITES, apply_surfaces, material
    from drain_film import apply as develop_film
    from hall_finishes import FINISHES, material as finish_material
    from harbour_air import in_morning_air
    from window_print import glaze

    colour_exposure = camera_layer(source, ".png", "colour", frame)
    develop_film(colour_exposure, source, large=large)
    exposed = blend_clock(colour_exposure, source, large=large)
    del colour_exposure
    harbour_optics = large and frame is None
    if harbour_optics:
        exposed = in_morning_air(exposed, source)
    raw = glaze(exposed, source, damp_glass=harbour_optics)
    del exposed
    base = large_grid(raw, source, frame) if large else original_grid(raw)
    del raw
    colour = colour_grade(base, large=large)
    if large:
        colour = colour.astype(np.float32)
    apply_surfaces(colour, source.with_suffix(".concrete.npz"), SITES, material)
    apply_surfaces(colour, source.with_suffix(".finishes.npz"), FINISHES, finish_material)
    apply_surfaces(colour, source.with_suffix(".berth-concrete.npz"), berth_sites, berth_material)
    apply_marks(colour, base, source.with_suffix(".marks.json"))
    if not large:
        return {"native": indexed_print(colour)}

    colour = np.clip(colour, 0, 255)
    continuous = Image.fromarray(np.uint8(np.clip(colour + 0.5, 0, 255)))
    return {"tonal": continuous, "80-colours": indexed_print(colour)}


def resolve(source, destination, *, large):
    """Develop one profile and publish its finished prints together."""
    with staged_output(destination) as stage:
        return write_prints(source, stage, large=large)


def write_prints(source, destination, *, large):
    from harbour_plate import print_mask

    source, page = Path(source), Path(destination)
    require_passes(source, print_passes(large=large), "Edition 19 capture")

    pictures = develop(source, large=large)
    width, height = next(iter(pictures.values())).size
    frame_file = source.with_suffix(".frame.npz")
    if frame_file.is_file():
        # The same colour treatment is used on both sides of the glass. Keep
        # the ink on the hall side of the aperture from the approved exposure.
        with np.load(frame_file) as frame:
            mask = print_mask(frame, (width, height))
            room = develop(source, large=large, frame=frame)
        for finish, background in room.items():
            background.paste(pictures[finish], (0, 0), mask)
        pictures = room

    prefix = "No-Further-Sailings-19"
    page.mkdir(parents=True, exist_ok=True)
    if not large:
        filename = f"{prefix}-528.png"
        pictures["native"].save(page / filename, optimize=True)
        return [filename]

    files = []
    for finish, image in pictures.items():
        filename = f"{prefix}-{width}-{finish}.png"
        treatment = "Continuous tone" if finish == "tonal" else "Edition IX palette"
        info = PngImagePlugin.PngInfo()
        info.add_text("Title", "No Further Sailings — Salt Lines, revised")
        info.add_text("Description", f"{treatment}. Urban ferry basin at {width} × {height} native.")
        image.save(page / filename, pnginfo=info, optimize=True)
        files.append(filename)
    return files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--profile", choices=("original", "large"), required=True)
    args = parser.parse_args()
    try:
        files = resolve(args.source, args.output, large=(args.profile == "large"))
    except ValueError as error:
        parser.error(str(error))
    print(*files, sep="\n")
