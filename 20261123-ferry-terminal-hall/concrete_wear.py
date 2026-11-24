"""Shallow surface loss and material marks in the passenger hall. Units are metres."""

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from pathlib import Path

import numpy as np

from casting_patina import booth_coordinates, ceiling_coordinates, draw_detail, shoulder_coordinates, sill_coordinates, smooth
from layout import SILL_JOINT


def pier_coordinates(station, x, y, z):
    return x - 6.12 - (y - station), z


def beam_coordinates(station, x, y, z):
    return x, z - np.interp(x, EDGE_X, EDGE_Z) - (y - station)


@dataclass(frozen=True)
class Site:
    name: str
    front_y: float
    world_min: tuple
    world_max: tuple
    sheet: tuple              # u min/max, v min/max on the unfolded surface
    lobes: tuple              # centres and radii of islands of worn cement
    seed: int
    surfaces: tuple = ("weathered piers",)
    coordinates: Callable = pier_coordinates


RELIEF_SITES = (
    Site("beam", -2.25, (1.78, -2.26, 6.50), (5.30, -1.74, 7.18),
         (1.72, 5.36, -0.27, 0.39),
         ((2.03,.042,.16,.045), (2.39,.071,.14,.054), (2.77,.043,.30,.062),
          (3.07,.085,.23,.082), (3.59,.047,.39,.067), (3.86,.091,.27,.090),
          (4.14,.064,.32,.143), (4.38,.118,.15,.060), (4.72,.034,.15,.060),
          (4.97,.059,.080,.022)), 4611, coordinates=beam_coordinates),
    Site("pier", -2.25, (6.10, -2.26, .41), (6.65, -1.74, 1.81),
         (-.47, .49, .40, 1.83),
         ((-.018,.63,.065,.11), (-.025,.87,.11,.18), (.004,1.06,.16,.22),
          (.080,1.09,.14,.10), (-.010,1.28,.090,.17), (.027,1.43,.059,.080),
          (-.139,.98,.045,.038), (.054,1.62,.032,.047)), 2374),
    Site("joint", 5.05, (6.08, 5.04, 5.22), (6.81, 5.56, 5.76),
         (-.20, .72, 5.23, 5.74),
         ((.13,5.49,.058,.018), (.28,5.515,.095,.048), (.365,5.477,.115,.039),
          (.466,5.50,.067,.027), (.54,5.493,.022,.016)), 9302),
)

PATINA_SITES = (
    Site("ticket_fascia", 12.18, (-6.91,10.30,2.767), (-2.38,12.03,3.203),
         (-2.68,2.84,-.01,.445), (), 4278, ("old base render",), booth_coordinates),
    Site("ceiling_board", 3.05, (-1.61,.60,7.672), (.045,5.002,7.686),
         (-2.48,1.98,-.52,1.16), (), 1869, ("sheltered soffit",), ceiling_coordinates),
    Site("boarding_pier", 12.35, (6.105,12.342,.153), (6.80,12.854,1.43),
         (-.52,.71,.15,1.44), (), 5917),
    Site("window_base", SILL_JOINT, (10.413,1.00,.016), (10.426,7.06,.95),
         (-3.83,2.28,.01,.96), (), 3722,
         ("old base render", "water and mineral under the leaking sill"), sill_coordinates),
    Site("arch_repair", 5.05, (6.73,5.042,5.67), (8.51,5.56,7.26),
         (-.080,1.74,-.085,.73), (), 7271, coordinates=shoulder_coordinates),
)

SITES = RELIEF_SITES + PATINA_SITES

# Lower edge of the inside return, taken from the formwork stations in terminal.py.
EDGE_X = (-9.35, 3.45, 4.58, 5.23, 5.66, 5.96, 6.12)
EDGE_Z = (6.91, 6.86, 6.76, 6.60, 6.36, 6.03, 5.68)
SUBSAMPLES = 2
EMPTY = np.iinfo(np.int16).min


def record_surfaces(scene, destination, *, large, areas=SITES, suffix=".concrete.npz",
                    overlays=()):
    """Save millimetre coordinates only where the camera first hits the selected casting."""
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    from harbour_air import surface_ranges
    from surface_alpha import alpha_triangles, first_surface

    width = scene.render.resolution_x if large else 528
    height = 3 * width // 4
    names = {name for site in areas for name in site.surfaces}.union(overlays)
    tree, ranges = surface_ranges(scene, {"suspended sea air", "low air above the inlet"}, names)
    if set(ranges) != names:
        raise ValueError(f"Missing surface materials: {sorted(names.difference(ranges))}")
    translucent = alpha_triangles(scene, overlays, ranges) if overlays else {}
    cam = scene.camera
    eye = cam.location.copy()
    frame = cam.data.view_frame(scene=scene)
    left, right = min(v.x for v in frame), max(v.x for v in frame)
    bottom, top = min(v.y for v in frame), max(v.y for v in frame)
    basis = cam.matrix_world.to_3x3()
    samples = SUBSAMPLES
    dx = basis @ Vector(((right-left) / (width*samples), 0, 0))
    dy = basis @ Vector((0, (bottom-top) / (height*samples), 0))
    top_left = basis @ Vector((left, top, frame[0].z))
    guide = dict(size=(width, height), samples=samples)
    for site in areas:
        face_ranges = [ranges[name] for name in site.surfaces]
        lo, hi = site.world_min, site.world_max
        corners = [world_to_camera_view(scene, cam, Vector(p)) for p in product(*zip(lo, hi))]
        x0 = max(0, int(np.floor(width * min(p.x for p in corners))) - 1)
        x1 = min(width, int(np.ceil(width * max(p.x for p in corners))) + 1)
        y0 = max(0, int(np.floor(height * (1-max(p.y for p in corners)))) - 1)
        y1 = min(height, int(np.ceil(height * (1-min(p.y for p in corners)))) + 1)
        uv = np.full(((y1-y0)*samples, (x1-x0)*samples, 2), EMPTY, np.int16)
        through = np.full(uv.shape[:2], 255, np.uint8) if overlays else None
        first = top_left + dx*(x0*samples+.5) + dy*(y0*samples+.5)
        for j in range(uv.shape[0]):
            ray = first + dy*j
            for i in range(uv.shape[1]):
                direction = (ray+dx*i).normalized()
                if translucent:
                    point,index,visibility = first_surface(tree,eye,direction,cam.data.clip_end,translucent)
                else:
                    point, _, index, _ = tree.ray_cast(eye, direction, cam.data.clip_end)
                    visibility = 1.
                if not any(index in face_range for face_range in face_ranges):
                    continue
                x, y, z = point
                if not (lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1] and lo[2] <= z <= hi[2]):
                    continue
                coords = site.coordinates(site.front_y, x, y, z)
                if coords is None:
                    continue
                u, v = coords
                uv[j, i] = round(1000*u), round(1000*v)
                if through is not None:
                    through[j,i] = round(255*visibility)
        if not np.any(uv[..., 0] != EMPTY):
            raise ValueError(f"No part of the {site.name} is visible to the camera.")
        guide[site.name] = uv
        guide[site.name + "_origin"] = (x0, y0)
        if through is not None and np.any(through != 255):
            guide[site.name + "_through"] = through
    path = Path(destination).with_suffix(suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **guide)
    return path


@lru_cache(maxsize=len(SITES))
def material(site):
    """Paint one continuous relief sheet, shared by every drawing resolution."""
    from PIL import Image, ImageDraw
    from scipy import ndimage as ndi

    if site in PATINA_SITES:
        return draw_detail(site)
    rng = np.random.default_rng(site.seed)
    left, right, bottom, top = site.sheet
    # Two-millimetre texels resolve the lips of shallow air pockets in the large print.
    p = 500
    w, h = round((right-left)*p)+1, round((top-bottom)*p)+1
    u = np.linspace(left, right, w, dtype=np.float32)[None, :]
    v = np.linspace(bottom, top, h, dtype=np.float32)[:, None]

    def grain(du, dv):
        cells = (max(2, round((top-bottom)/dv)), max(2, round((right-left)/du)))
        grid = rng.uniform(-1, 1, cells).astype(np.float32)
        return np.asarray(Image.fromarray(grid).resize((w, h), Image.Resampling.BICUBIC))

    broad = grain(.19, .115)
    flakes = grain(.054, .041)
    grit = grain(.017, .016)
    fine = grain(.006, .007)
    u_warped = u + .037*broad + .017*grit
    v_warped = v + .034*grain(.16, .13) + .012*flakes
    distance = np.full((h, w), -5.0, np.float32)
    for cu, cv, ru, rv in site.lobes:
        radius = np.hypot((u_warped-cu)/ru, (v_warped-cv)/rv)
        np.maximum(distance, 1-radius, out=distance)
    # A ragged margin gives way first. Sound islands of the cement skin survive inside it.
    boundary = distance + .24*flakes + .095*grit
    edge = smooth(-.28, .30, boundary)
    lost = edge*smooth(-.23, .36, .27*distance + .66*flakes + .34*grit + .13*broad)
    shoulder = smooth(-.65, .16, boundary)
    if site.name == "pier":
        # Contact polishes the outer arris, reaching a little way onto either face.
        rubbed = shoulder*np.exp(-np.abs(u+.016*flakes+.012*broad)/.115)
        rubbed *= .68 + .28*grain(.030, .17)
        front = smooth(-.07, .09, u_warped)
        tone = (17-12*front)*rubbed + lost*(-7 + 5*flakes + 3.0*grit) - 1.7*edge
    elif site.name == "beam":
        tone = -1.3*edge + lost*(-6 + 6*broad + 3.2*grit)
    else:
        tone = -1.5*edge + lost*(-6 + 3.0*grit)

    # Draw the cavities as small angular sections, in loose pockets of weaker paste.
    # A few pale inclusions sit flush with the skin; only holes have a shadowed lip.
    pits = Image.new("L", (w, h))
    stone = Image.new("L", (w, h), 128)
    holes, grains = ImageDraw.Draw(pits), ImageDraw.Draw(stone)

    def fragment(draw, cu, cv, ru, rv, tilt, value):
        count = int(rng.integers(5, 9))
        angle = np.arange(count) * (2*np.pi/count) + rng.uniform(-.26, .26, count)
        radius = rng.uniform(.66, 1.16, count)
        a, b = ru*radius*np.cos(angle), rv*radius*np.sin(angle)
        x = (cu + np.cos(tilt)*a - np.sin(tilt)*b - left)*p
        y = (cv + np.sin(tilt)*a + np.cos(tilt)*b - bottom)*p
        draw.polygon(list(zip(x.tolist(), y.tolist())), fill=int(value))

    for _ in range(round((right-left)*(top-bottom)*2300)):
        cu, cv = rng.uniform(left, right), rng.uniform(bottom, top)
        i, j = round((cu-left)*p), round((cv-bottom)*p)
        density = (.12*shoulder[j,i] + .46*edge[j,i] + .42*lost[j,i])
        if rng.random() > density:
            continue
        size = .003 + .017*rng.random()**3
        ru, rv = size*rng.uniform(.78, 1.4), size*rng.uniform(.44, .94)
        angle = rng.uniform(-1.2, 1.2)
        if rng.random() < (.23 if site.name == "pier" else .46):
            fragment(holes, cu, cv, ru, rv, angle, rng.uniform(105, 230))
        else:
            fragment(grains, cu, cv, ru, rv, angle, rng.uniform(48, 220))

    # These larger voids give the beam an uneven cadence. Their edges are undercut
    # just enough for the lip nearest the window to collect a little light.
    if site.name == "beam":
        for cu, cv, ru, rv, angle in (
            (2.64,.052,.036,.010,-.10), (3.05,.088,.026,.013,.37),
            (3.60,.043,.031,.012,.09), (3.94,.116,.031,.015,-.04),
            (4.12,.061,.041,.016,.18), (4.19,.097,.022,.012,-.57),
            (4.30,.076,.025,.009,.11), (4.72,.042,.016,.009,.20),
        ):
            fragment(holes, cu, cv, ru, rv, angle, rng.uniform(165, 235))
    # Larger losses are drawn individually. Their edges follow the lip of the beam
    # or turn around the pier, and the cavities show warm-grey granular cement inside.
    # Coordinates are on the unfolded casting, so one flake can straddle two faces.
    spalls = {
        "beam": (
            ((2.66,.008),(2.72,.038),(2.79,.040),(2.84,.069),(2.94,.080),
             (2.99,.076),(2.94,.051),(2.86,.025),(2.79,.010),(2.74,-.012)),
            ((3.49,.025),(3.58,.053),(3.62,.045),(3.72,.068),(3.79,.057),
             (3.74,.030),(3.67,.026),(3.64,.008),(3.53,-.011)),
            ((3.96,.001),(4.01,.045),(4.08,.062),(4.10,.090),(4.19,.094),
             (4.21,.115),(4.29,.105),(4.34,.116),(4.38,.096),(4.35,.073),
             (4.25,.055),(4.22,.023),(4.15,.018),(4.12,-.017),(4.05,-.034)),
            ((4.43,.039),(4.48,.066),(4.57,.059),(4.55,.040),(4.47,.022)),
        ),
        "pier": (
            ((-.125,.918),(-.117,.976),(-.146,1.017),(-.121,1.075),(-.092,1.087),
             (-.074,1.143),(-.022,1.171),(-.015,1.214),(.037,1.196),(.051,1.155),
             (.109,1.151),(.142,1.109),(.161,1.084),(.121,1.087),(.094,1.063),
             (.048,1.055),(.018,1.014),(-.027,1.039),(-.049,.998),(-.07,.993),(-.086,.948)),
            ((-.080,1.264),(-.059,1.308),(-.057,1.351),(-.032,1.378),(.011,1.369),
             (.038,1.397),(.057,1.365),(.051,1.328),(.018,1.310),(.012,1.288)),
            ((-.048,.68),(-.04,.729),(-.013,.754),(.017,.75),(.026,.733),
             (.004,.701),(-.014,.696),(-.024,.667)),
        ),
        "joint": (
            ((.272,5.478),(.300,5.493),(.366,5.50),(.402,5.488),(.424,5.492),
             (.407,5.471),(.359,5.465),(.325,5.475),(.29,5.468)),
        ),
    }
    scars = Image.new("L", (w,h))
    draw = ImageDraw.Draw(scars)
    for polygon in spalls[site.name]:
        draw.polygon([((a-left)*p,(b-bottom)*p) for a,b in polygon],fill=255)
    binary = np.asarray(scars) > 0
    # Let the cement fracture around embedded aggregate at the margin of each loss.
    signed = (ndi.distance_transform_edt(binary)-ndi.distance_transform_edt(~binary))/p
    fracture = smooth(-.0025,.0035,signed+.013*flakes+.007*grit+.003*fine)
    upper = np.maximum(0,fracture - ndi.shift(fracture,(-2.6,1.0),order=1))
    lower = np.maximum(0,ndi.shift(fracture,(-1.8,1.1),order=1) - fracture)
    fresh = (10.5 - 24.0*front) if site.name == "pier" else 8.0
    tone = tone + fracture*(fresh + 6*grit + 4*flakes) - 13*upper + (5+4*flakes)*lower
    void = ndi.gaussian_filter(np.asarray(pits, np.float32)/255, .64)
    aggregate = ndi.gaussian_filter((np.asarray(stone, np.float32)-128)/127, .58)
    lip = np.maximum(0, ndi.shift(void, (-1.35, .70), order=1) - void)
    # Skin breaking away also has a broader, shallower rim, broken by intact mortar.
    flake_lip = np.maximum(0, ndi.shift(lost, (-2.2, 1.15), order=1) - lost)
    broken = (16*lip - 22*void + 17*aggregate + 11*flake_lip
              + lost*(4*grit + 2*fine))
    if site.name == "beam":
        # Intact fillets between pours interrupt the line of pockets at the bend.
        interrupted = (1 - .84*np.exp(-((u_warped-3.32)/.16)**4))
        interrupted *= 1 - .65*np.exp(-((u_warped-4.52)/.11)**2)
        interrupted *= .72 + .28*smooth(2.56, 3.92, u_warped)
        amount = interrupted
    elif site.name == "pier":
        # Repeated contact takes the high points off the exposed strip at the corner.
        broken *= 1 - .42*rubbed
        amount = 1.0
    else:
        amount = .63
    tone = (tone + broken)*amount
    dust = amount*(.26*edge + .37*lost + .38*fracture + .16*np.maximum(aggregate, 0))
    return np.asarray(tone, np.float32), np.asarray(dust, np.float32)


def apply_surfaces(colour, path, sites, paint):
    """Filter physical surface drawings over the visible subpixel samples."""
    from scipy import ndimage as ndi

    from exposure_filter import luma

    with np.load(path) as guide:
        required = {"size", "samples"}
        for site in sites:
            required.update((site.name, site.name + "_origin"))
        missing = required.difference(guide.files)
        if missing:
            raise ValueError(f"{path.name} is missing surface fields {', '.join(sorted(missing))}.")
        width, height = map(int, guide["size"])
        if colour.shape != (height, width, 3):
            raise ValueError("The concrete guide and print must use the same camera grid.")
        samples = int(guide["samples"])
        for site in sites:
            mm = guide[site.name]
            x, y = map(int, guide[site.name + "_origin"])
            h, w = mm.shape[0]//samples, mm.shape[1]//samples
            view = colour[y:y+h, x:x+w]
            sheet, dust = paint(site)
            left, right, bottom, top = site.sheet
            u = (mm[...,0].astype(np.float32)*.001-left) * ((sheet.shape[1]-1)/(right-left))
            v = (mm[...,1].astype(np.float32)*.001-bottom) * ((sheet.shape[0]-1)/(top-bottom))
            coords = np.stack((v, u))
            through_key = site.name + "_through"
            transmission = guide[through_key].astype(np.float32)/255 if through_key in guide else None

            def sample(texture):
                values = ndi.map_coordinates(texture, coords, order=1, mode="constant", cval=0)
                if transmission is not None:
                    values *= transmission
                return values.reshape(h, samples, w, samples).mean(axis=(1,3))

            local = sample(sheet)
            patina = sample(dust)
            # A chip in the dark return has less available light than the same chip on
            # the pale face. The room's light is already present in the registered print.
            light = luma(view)
            response = np.clip(.47 + .0044*light, .55, 1.13)
            local *= response
            patina *= response
            view[...,0] += local*1.025 + 1.15*patina
            view[...,1] += local
            view[...,2] += local*.98 - .95*patina
