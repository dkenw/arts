"""Print the transmitted harbour view and the reflected hall on the same glass."""

from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter, map_coordinates


def sheet_reflectance(cosine):
    """Unpolarised Fresnel reflectance for the two faces of an uncoated sheet."""
    index = 1.52
    refracted = np.sqrt(1.0 - (1.0 - cosine**2) / index**2)
    rs = ((cosine - index * refracted) / (cosine + index * refracted))**2
    rp = ((index * cosine - refracted) / (index * cosine + refracted))**2
    # Sum the bounces inside the sheet for each polarisation before averaging.
    return 0.5 * (2.0 * rs / (1.0 + rs) + 2.0 * rp / (1.0 + rp))


def weathering(bay, s, z, tilted):
    """Sea film at the rebate and washed trails underneath the leaky transom."""
    # s is distance in metres along one sheet. The salt collects at the foot
    # and in sheltered corners. The exposed centres have been washed clearer.
    upper = z > 4.77
    vent = np.isin(bay, (4, 7, 8, 10))
    bottom = np.where(upper, 4.80, 1.205)
    bottom = np.where(vent & (z > 5.57), 5.589, bottom)
    bottom = np.where(tilted, 6.68 - 1.09 * np.cos(np.deg2rad(23.0)), bottom)
    foot = np.maximum(0.0, z - bottom)
    edge = np.maximum(0.0, np.minimum(s, 2.92 - s) - 0.046)
    corner = np.exp(-edge / 0.19)
    irregular = 0.93 + 0.18 * np.sin(4.2 * s + bay) + 0.10 * np.sin(14.1 * s - 0.4 * bay)
    tide = (0.05 + 0.19 * corner) * irregular
    bloom = (0.13 + 0.18 * corner) * np.exp(-foot / (0.10 + 0.18 * corner))
    bloom += 0.09 * np.exp(-((foot - tide) / 0.045)**2) * np.clip(irregular - 0.27, 0, 1)
    bloom += 0.060 * corner * np.exp(-foot / 1.27)
    bloom *= np.where(upper, 0.52, 1.0)
    bloom *= np.where(bay == 7, 1.0, np.where(bay == 8, 0.79, 0.56))

    # Broken shoulders of deposited silt enclose the cleaner middle of a run.
    stains = np.zeros_like(z)
    cleaned = np.zeros_like(z)
    for panel, centre, width, high, low, phase in (
        (7, 2.55, 0.070, 4.69, 1.72, 0.6),
        (7, 2.42, 0.036, 3.76, 2.38, 2.7),
        (8, 0.35, 0.046, 4.72, 3.33, 1.8),
    ):
        fall = np.clip((high - z) / (high - low), 0, 1)
        path = centre + 0.029 * np.sin(4.4 * fall + phase) + 0.012 * np.sin(11 * fall + phase)
        offset = (s - path) / (width * (1.0 - 0.47 * fall))
        ends = np.clip((high - z) / 0.14, 0, 1) * np.clip((z - low) / 0.35, 0, 1)
        broken = np.clip(0.62 + 0.30 * np.sin(9 * fall + phase) + 0.19 * np.sin(25 * fall + phase), 0, 1)
        active = (bay == panel) * ends
        stains += active * broken * np.exp(-((offset - 0.68) / 0.40)**2)
        cleaned += active * np.exp(-(offset / 0.76)**2)
    return bloom, stains, cleaned, edge, foot


def view_through_old_glass(patch, bay, along, z, visible, scale):
    """A slight variation in two old sheets bends the outline of the distant quay."""
    row, col = np.indices(z.shape, dtype=np.float32)
    strength = np.zeros_like(z)
    for number, amplitude in ((7, 0.61), (8, 0.36)):
        pane = visible & (bay == number) & (z < 4.72)
        # Stop clear of the steel, blind and sill, which are on the camera side.
        interior = np.clip(distance_transform_edt(pane) / scale - 1.1, 0, 1)
        strength += amplitude * interior
    dx = strength * scale * (np.sin(1.56 * z + 1.8 * along) + 0.18 * np.sin(4.3 * z + 0.78 * along))
    dy = 0.30 * strength * scale * np.cos(2.53 * along + 0.48 * z)
    coords = (row + dy, col + dx)
    channels = [map_coordinates(ch, coords, order=1, mode="nearest") for ch in patch.transpose(2, 0, 1)]
    return np.stack(channels, axis=-1)


# Measured in output pixels on the 2112-pixel print. The wider lobe accounts
# for the small amount of light scattered outside the narrow refracted image.
SASH_SPREAD = (2.45, 1.85)
SASH_SCATTER = 0.91
FIXED_SCATTER = 0.28


def damp_transmission(colour, source, origin, size, signed, bay, along, z):
    """Spread only light transmitted through an actual wet sheet of glass."""
    from scipy.ndimage import find_objects
    from harbour_air import SKY, from_linear, to_linear
    from layout import LANDING_EYE, OPEN_BAY

    path = source.with_suffix(".harbour-depth.npz")
    width, height = size
    x, y = origin
    h, w = signed.shape
    # The pane and depth passes use different rectangles on the same camera.
    with np.load(path) as guide:
        if tuple(guide["size"]) != (width, height):
            raise ValueError("The pane and harbour passes must share a camera.")
        dx, dy = map(int, guide["origin"])
        distance = guide["metres"]
    gh, gw = distance.shape[:2]
    x0, x1 = max(x, dx), min(x + w, dx + gw)
    y0, y1 = max(y, dy), min(y + h, dy + gh)
    if x0 >= x1 or y0 >= y1:
        return colour
    destination = np.s_[y0 - y:y1 - y, x0 - x:x1 - x]
    distance = distance[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    cosine = signed[destination]
    tilted = cosine < 0
    level = z[destination]
    along = along[destination]
    panel = bay[destination]
    vent = np.isin(panel, (4, OPEN_BAY, 8, 10)) & (level > 5.57)
    fixed_x = np.where(vent, 10.53, 10.56)
    ray_x = np.where(tilted, 10.53 + (level - 6.68) * np.tan(np.deg2rad(23.0)), fixed_x)
    eye_x, eye_y, eye_z = LANDING_EYE
    glass_range = np.sqrt((ray_x - eye_x)**2 + (along - eye_y)**2 + (level - eye_z)**2)
    # The same angular deflection displaces the far shore more than an object
    # close behind the pane. At sky distance the full deflection applies.
    inverse = np.where(distance == SKY, 0.0, 1.0 / np.maximum(distance, 1))
    leverage = np.maximum(0.0, 1.0 - glass_range[..., None] * inverse).mean(axis=2)
    all_distant = (distance > 55).all(axis=2)
    eligible = (cosine != 0) & all_distant
    if not np.any(eligible):
        return colour

    # Each fixed light and opening sash has its own surface. An unglazed gap,
    # the blind, the rails and nearby piling never enter the optical average.
    piece = np.where(tilted, 3, np.where(vent, 2, np.where(level > 4.77, 1, 0)))
    labels = np.where(eligible, 1 + 4 * panel + piece, 0).astype(np.int32)
    view = colour[destination]
    linear = to_linear(view)
    result = linear.copy()
    scale = width / 2112
    s = along + 18.56 - 2.92 * panel
    # Slightly cleaner vertical runs, located in glass coordinates, let a
    # little more of the original view through between patches of moisture.
    path_of_run = 0.71 + 0.045 * np.sin(2.7 * level)
    film = 1.0 - 0.13 * np.exp(-((s - path_of_run) / 0.23)**2)
    film -= 0.075 * np.exp(-((s - 2.36 - 0.04 * np.sin(3.0 * level)) / 0.17)**2)
    amount = np.where(tilted, SASH_SCATTER, FIXED_SCATTER) * film * leverage**1.65
    for index, box in enumerate(find_objects(labels), start=1):
        if box is None:
            continue
        member = labels[box] == index
        mask = member.astype(np.float32)
        sub = linear[box]
        wet_sash = (index - 1) % 4 == 3
        core = np.asarray(SASH_SPREAD) * scale * (1.0 if wet_sash else 0.78)

        def scattered(radius):
            sigma = tuple(core * radius)
            total = gaussian_filter(mask, sigma, mode="constant")
            light = gaussian_filter(sub * mask[..., None], (*sigma, 0), mode="constant")
            return light / np.maximum(total[..., None], 1e-6)

        image = 0.78 * scattered(1.0) + 0.22 * scattered(2.65)
        local_result = result[box]
        local_result[member] = sub[member] + amount[box][member, None] * (image[member] - sub[member])

    converted = from_linear(result)
    view[eligible] = np.clip(255.0 * converted[eligible], 0.0, 255.0)
    return colour


def glaze(rgb, source, *, damp_glass=False):
    path = Path(source)
    with np.load(path.with_suffix(".panes.npz")) as data:
        x, y = data["origin"]
        width, height = data["size"]
        if (width, height) != (rgb.shape[1], rgb.shape[0]):
            raise ValueError("Window surfaces and exposure must share a camera resolution.")
        signed = data["cosine"]
        along, z = data["along"], data["elevation"]
    h, w = signed.shape
    with Image.open(path.with_suffix(".room.png")) as im:
        if im.size != (width, height):
            raise ValueError("The reflected and transmitted views must align.")
        mirror = np.asarray(im.convert("RGB").crop((x, y, x + w, y + h)), dtype=np.float32)

    patch = rgb[y : y + h, x : x + w]
    visible = signed != 0
    tilted = signed < 0
    bay = np.floor((along + 18.56) / 2.92).astype(int)
    s = (along + 18.56) - 2.92 * bay
    bloom, stains, cleaned, edge, foot = weathering(bay, s, z, tilted)
    cosine = np.maximum(np.abs(signed), 0.40)

    # The tilted sash already catches a little of the room in the first exposure.
    reflection = sheet_reflectance(cosine) * np.where(tilted, 1.02, 1.43)
    tint = np.select([bay == 6, bay == 7, bay == 8, bay == 11], [0.87, 1.06, 0.73, 0.82], default=1.0)
    depth = tint / cosine * np.where(tilted, 0.63, 1.0)
    scale = width / 528
    transmitted = view_through_old_glass(patch, bay, s, z, visible, scale)
    if damp_glass:
        transmitted = damp_transmission(transmitted, path, (x, y), (width, height), signed, bay, along, z)
    through = transmitted * np.exp(-depth[..., None] * np.array([0.019, 0.006, 0.010], np.float32))
    colour = through + reflection[..., None] * (mirror - through)

    # Compare reflected values only with their neighbours on the same plane.
    # This keeps the stencil and pilasters legible at the native print size.
    room_value = mirror @ np.array([0.24, 0.66, 0.10], np.float32)
    for face in (signed > 0, tilted):
        light = np.where(face, room_value, 0)
        mask = face.astype(np.float32)
        fine_radius, broad_radius = scale * 0.70, scale * 7.8
        near = gaussian_filter(light, fine_radius) / np.maximum(gaussian_filter(mask, fine_radius), 0.001)
        broad = gaussian_filter(light, broad_radius) / np.maximum(gaussian_filter(mask, broad_radius), 0.001)
        relief = np.clip(near - broad, -44, 44)
        colour += np.where(face, 0.27 * relief, 0)[..., None]

    film = np.clip(bloom + 0.19 * stains - 0.055 * cleaned, 0, 0.40)
    colour += film[..., None] * (np.array([155, 170, 163], np.float32) - colour)
    colour += (2.4 * cleaned - 4.5 * stains)[..., None]
    # A narrow bedding line gives the nearest sheets a cut edge against the steel.
    bedding = 0.22 * np.exp(-edge / 0.020) + 0.16 * np.exp(-foot / 0.028)
    colour += bedding[..., None] * (np.array([98, 115, 111], np.float32) - colour)
    result = rgb.copy()
    result[y : y + h, x : x + w] = np.where(visible[..., None], colour, patch)
    return result
