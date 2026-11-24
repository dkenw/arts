"""The ferry hall. Run through Blender (see render.py). Geometry is in metres."""

import argparse
import math
import random
import sys
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from large_details import cast_haunch, moulded_shell
from layout import LANDING_EYE, BANKS, PITCH, OPEN_BAY, SILL_JOINT, RING_CENTRE, feet, floor_height

p = argparse.ArgumentParser()
p.add_argument("--profile", choices=("original", "large"), default="original")
p.add_argument("--maps", type=Path, required=True)
p.add_argument("--output", required=True)
p.add_argument("--width", type=int, default=528)
p.add_argument("--samples", type=int, default=36)
partial = p.add_mutually_exclusive_group()
partial.add_argument("--exterior-only", action="store_true", help="Expose the harbour for the window study.")
partial.add_argument("--harbour-depth-only", action="store_true", help="Trace the range guide for a large harbour print.")
partial.add_argument("--film-only", action="store_true", help="Measure the local change in reflected skylight at the drain.")
partial.add_argument("--surfaces-only", action="store_true", help="Trace the cloth and small concrete details.")
partial.add_argument("--berth-concrete-only", action="store_true", help="Trace the broad areas of concrete wear.")
partial.add_argument("--concrete-only", action="store_true", help="Trace the visible cast surfaces for the concrete study.")
partial.add_argument("--marks-only", action="store_true")
partial.add_argument("--clock-only", action="store_true", help="Render just the dial-glass exposure.")
partial.add_argument("--windows-only", action="store_true", help="Expose the room reflected in the harbour windows.")
p.add_argument("--far-shore", action="store_true", help="Register the distant harbour separately from the landing.")
args = p.parse_args(sys.argv[sys.argv.index("--") + 1 :])
if bpy.app.version < (5, 0, 0):
    p.error("Fresh camera exposures use the Blender 5 API. Use Blender 5.2 LTS.")
if args.far_shore and not args.exterior_only:
    p.error("--far-shore requires --exterior-only")
large = args.profile == "large"
if args.harbour_depth_only and not large:
    p.error("--harbour-depth-only uses the large print profile")
rng = random.Random(6510)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
pieces = {}
materials = {}


def linear(x):
    x = x / 255
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def rgba(s):
    s = s.lstrip("#")
    return tuple(linear(int(s[i : i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def newmat(name):
    m = bpy.data.materials.new(name)
    materials[name] = m
    m.node_tree.nodes.clear()
    return m


def node(m, t):
    return m.node_tree.nodes.new(t)


def link(m, a, b):
    m.node_tree.links.new(a, b)


def base(name, color, rough=0.6, metal=0):
    m = newmat(name)
    out = node(m, "ShaderNodeOutputMaterial")
    bs = node(m, "ShaderNodeBsdfPrincipled")
    link(m, bs.outputs[0], out.inputs["Surface"])
    bs.inputs["Base Color"].default_value = rgba(color)
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    return m, bs


def solid(name, c, r=0.6, metal=0):
    return base(name, c, r, metal)[0]


def weather(name, dark, light, scale=1.0, stretch=(1, 1, 1), r=0.75, bump=0.012, metal=0):
    m, bs = base(name, light, r, metal)
    geom = node(m, "ShaderNodeNewGeometry")
    mult = node(m, "ShaderNodeVectorMath")
    mult.operation = "MULTIPLY"
    link(m, geom.outputs["Position"], mult.inputs[0])
    mult.inputs[1].default_value = stretch
    noise = node(m, "ShaderNodeTexNoise")
    link(m, mult.outputs[0], noise.inputs[0])
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 4
    noise.inputs["Roughness"].default_value = 0.64
    ramp = node(m, "ShaderNodeValToRGB")
    for el, v, col in zip(ramp.color_ramp.elements, (0.22, 0.77), (dark, light)):
        el.position = v
        el.color = rgba(col)
    link(m, noise.outputs["Fac"], ramp.inputs[0])
    link(m, ramp.outputs[0], bs.inputs["Base Color"])
    if bump:
        grain = node(m, "ShaderNodeTexNoise")
        link(m, mult.outputs[0], grain.inputs[0])
        grain.inputs["Scale"].default_value = 18
        grain.inputs["Detail"].default_value = 2.1
        b = node(m, "ShaderNodeBump")
        b.inputs["Strength"].default_value = 0.16
        b.inputs["Distance"].default_value = bump
        link(m, grain.outputs[0], b.inputs["Height"])
        link(m, b.outputs[0], bs.inputs["Normal"])
    return m


def texture(name, file, rough=0.62, alpha=False):
    m, bs = base(name, "dddddd", rough)
    n = node(m, "ShaderNodeTexImage")
    n.image = bpy.data.images.load(str(args.maps / file))
    n.interpolation = "Linear"
    link(m, n.outputs["Color"], bs.inputs["Base Color"])
    if alpha:
        link(m, n.outputs["Alpha"], bs.inputs["Alpha"])
    return m, bs


def thin_pane(m, transmitted, out, roughness):
    # Both surfaces of a thin sheet reflect a little of the room. With parallel
    # faces the emerging ray has the original direction. Use |N.I| on either side.
    geo = node(m, "ShaderNodeNewGeometry")
    dot = node(m, "ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    link(m, geo.outputs["Incoming"], dot.inputs[0])
    link(m, geo.outputs["Normal"], dot.inputs[1])
    absolute = node(m, "ShaderNodeMath")
    absolute.operation = "ABSOLUTE"
    link(m, dot.outputs["Value"], absolute.inputs[0])
    grazing = node(m, "ShaderNodeMath")
    grazing.operation = "SUBTRACT"
    grazing.inputs[0].default_value = 1
    link(m, absolute.outputs[0], grazing.inputs[1])
    power = node(m, "ShaderNodeMath")
    power.operation = "POWER"
    power.inputs[1].default_value = 5
    link(m, grazing.outputs[0], power.inputs[0])
    fresnel = node(m, "ShaderNodeMath")
    fresnel.operation = "MULTIPLY_ADD"
    fresnel.inputs[1].default_value = 0.93
    fresnel.inputs[2].default_value = 0.07
    link(m, power.outputs[0], fresnel.inputs[0])
    reflection = node(m, "ShaderNodeBsdfGlossy")
    reflection.inputs["Roughness"].default_value = roughness
    mix = node(m, "ShaderNodeMixShader")
    link(m, fresnel.outputs[0], mix.inputs[0])
    link(m, transmitted, mix.inputs[1])
    link(m, reflection.outputs[0], mix.inputs[2])
    link(m, mix.outputs[0], out.inputs["Surface"])


def glassmaterial(name="salt-hazed glass", reflect=False):
    m = newmat(name)
    o = node(m, "ShaderNodeOutputMaterial")
    tr = node(m, "ShaderNodeBsdfTransparent")
    tr.inputs[0].default_value = (0.97, 0.984, 0.977, 1)
    bs = node(m, "ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = rgba("98aa9f")
    bs.inputs["Roughness"].default_value = 0.23
    mix = node(m, "ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.042
    levels = node(m, "ShaderNodeTexImage")
    levels.image = bpy.data.images.load(str(args.maps / "glass-salt.png"))
    levels.image.colorspace_settings.name = "Non-Color"
    link(m, levels.outputs["Color"], mix.inputs[0])
    link(m, tr.outputs[0], mix.inputs[1])
    link(m, bs.outputs[0], mix.inputs[2])
    if reflect:
        thin_pane(m, mix.outputs[0], o, 0.065)
    else:
        link(m, mix.outputs[0], o.inputs[0])
    return m


concrete = weather("cast shell", "77796e", "aaa99a", 0.65, (1.3, 1, 0.6), 0.85)
under = weather("sheltered soffit", "555e5b", "898b7d", 0.74, (0.38, 1.1, 1), 0.86)
piermat = weather("weathered piers", "747e79", "abae9f", 0.82, (1.5, 1.3, 0.34), 0.75)
plaster = weather("salt plaster", "80877c", "c0bdab", 0.87, (1.7, 1.5, 0.44))
sub = weather("old base render", "515e59", "8a8d7c", 1.2, (1.4, 1.1, 0.52))
ledge = weather("sill stone", "646e6a", "9ca494", 1.4, (1, 1, 1), 0.58)
iron = weather("graphite metal", "28383c", "5d6864", 2.9, (1.4, 1.1, 0.52), 0.54, 0.007, 0.47)
steel = weather("dull aluminium", "586665", "9ba59b", 3, (1.7, 1.5, 0.57), 0.34, 0.006, 0.59)
dark = solid("join shadow", "263336", 0.76)
tar = solid("glazing rubber", "37413e", 0.83)
teal = weather("municipal enamel", "315d57", "678c74", 1.45, (1, 1, 0.5), 0.49, 0.005, 0.15)
wood = weather("rain-polished timber", "3a3430", "66574a", 1.55, (4, 0.36, 3), 0.52, 0.013)
rust = weather("red oxide", "844c38", "bc7754", 2.4, (1, 1, 0.6), 0.66)
cream = weather("old ivory", "aba68c", "d3cbb0", 2.2, (1, 1, 0.8), 0.63)
shutter = weather("galvanised shutter", "596963", "849189", 1.8, (1, 1, 0.5), 0.5, 0.006, 0.4)
seat1 = weather("bottle-green fibreglass", "365b54", "6d8a77", 2.0, (1, 1, 1), 0.41, 0.005)
seat2 = weather("sea-green fibreglass", "507368", "88a18d", 1.8, (1, 1, 1), 0.44, 0.004)
seat3 = weather("faded loden fibreglass", "606e56", "93a082", 2.0, (1, 1, 1), 0.50, 0.003)
ochre_seat = weather("tobacco ochre replacement shell", "83654e", "ad9271", 1.6, (1, 1, 0.8), 0.50, 0.003)
glass = glassmaterial()
open_glass = glassmaterial("rain-washed transom", True)
water = weather("water of the inlet", "6a8b85", "a9bcb3", 0.95, (0.24, 3, 1), 0.30, 0.01, 0.18)
mud = weather("silt", "817964", "aaa48f", 1.3, (0.34, 2.1, 1), 0.88)
farsteel = weather("estuary works", "6e807b", "a0aaa0", 1.4, (1, 1, 0.4), 0.74)
dolphin = weather("old wet piles", "4e5e5a", "8c9282", 1.75, (1.8, 1.8, 0.32), 0.66)
floormat, bs = texture("wet terrazzo", "terrazzo.png")
rough = node(floormat, "ShaderNodeTexImage")
rough.image = bpy.data.images.load(str(args.maps / "floor-rough.png"))
rough.image.colorspace_settings.name = "Non-Color"
link(floormat, rough.outputs["Color"], bs.inputs["Roughness"])
bs.inputs["IOR"].default_value = 1.48
height = node(floormat, "ShaderNodeTexImage")
height.image = bpy.data.images.load(str(args.maps / "floor-relief.png"))
height.image.colorspace_settings.name = "Non-Color"
fb = node(floormat, "ShaderNodeBump")
fb.inputs["Distance"].default_value = 0.013
fb.inputs["Strength"].default_value = 0.50
link(floormat, height.outputs["Color"], fb.inputs["Height"])
link(floormat, fb.outputs[0], bs.inputs["Normal"])
bs.inputs["Coat Weight"].default_value = 0.15
link(floormat, rough.outputs["Color"], bs.inputs["Coat Roughness"])
number = texture("berth stencil", "berth.png", 0.86, True)[0]
board = texture("departure flaps", "departures.png", 0.62)[0]
clockface = texture("clock face", "clock.png", 0.42, True)[0]
routemap = texture("stripped route frame", "map.png", 0.86)[0]
paintedwall = texture("faded tern mosaic and wall", "end-wall.png", 0.88)[0]
tile = texture("glazed sea-green tiles", "counter-tile.png", 0.42)[0]


# Buffer geometry by material so thin fittings remain inexpensive to trace.
def mesh(v, faces, m, uv=None, smooth=False):
    if m.name not in pieces:
        pieces[m.name] = [[], [], [], []]
    verts, polys, uvs, smooths = pieces[m.name]
    offset = len(verts)
    verts.extend(v)
    for k, f in enumerate(faces):
        polys.append(tuple(i + offset for i in f))
        uvs.append(uv[k] if uv else None)
        smooths.append(smooth)


def quad(a, b, c, d, m, tex=False):
    mesh(
        [a, b, c, d],
        [(0, 1, 2, 3)],
        m,
        [[(0, 0), (1, 0), (1, 1), (0, 1)]] if tex else None,
    )


def box(x0, x1, y0, y1, z0, z1, m):
    if min(x1 - x0, y1 - y0, z1 - z0) <= 0.00001:
        return
    v = [
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    ]
    mesh(
        v,
        [
            (3, 2, 1, 0),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7),
        ],
        m,
    )


def beam(a, b, width, depth, m):
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    side = axis.cross(Vector((0, 0, 1)))
    if side.length < 0.01:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(axis).normalized()
    ring = [
        side * width * 0.5 + up * depth * 0.5,
        -side * width * 0.5 + up * depth * 0.5,
        -side * width * 0.5 - up * depth * 0.5,
        side * width * 0.5 - up * depth * 0.5,
    ]
    verts = [tuple(c + k) for c in [a, b] for k in ring]
    mesh(
        verts,
        [(3, 2, 1, 0), (4, 5, 6, 7)] + [(j, (j + 1) % 4, 4 + (j + 1) % 4, 4 + j) for j in range(4)],
        m,
    )


def cyl(a, b, rad, m, n=12, r2=None):
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    side = axis.cross(Vector((0, 0, 1)))
    if side.length < 0.01:
        side = Vector((1, 0, 0))
    side.normalize()
    up = axis.cross(side).normalized()
    rings = [side * math.cos(i * math.tau / n) + up * math.sin(i * math.tau / n) for i in range(n)]
    v = [tuple(c + t * r) for c, r in ((a, rad), (b, rad if r2 is None else r2)) for t in rings]
    mesh(
        v,
        [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
        + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)],
        m,
    )


def pipe(pts, r, m, n=8):
    for a, b in zip(pts, pts[1:]):
        cyl(a, b, r, m, n)


def xz_prism(points, y0, y1, m):
    n = len(points)
    v = [(x, y, z) for y in [y0, y1] for x, z in points]
    mesh(
        v,
        [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
        + [(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)],
        m,
    )


def slab_polygon(pts, z0, z1, m):
    n = len(pts)
    v = [(x, y, z) for z in [z0, z1] for x, y in pts]
    mesh(
        v,
        [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
        + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)],
        m,
    )


def fronttex(x0, x1, y, z0, z1, m):
    quad((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1), m, True)


# Exterior light meets the interior first at the worn sill on the east side.
for left, right in [(-15, 8.52), (8.52, 10.42), (10.42, 11)]:
    zl, zr = floor_height(left), floor_height(right)
    u0, u1 = (left + 15) / 26, (right + 15) / 26
    mesh(
        [(left, -19, zl), (right, -19, zr), (right, 16.8, zr), (left, 16.8, zl)],
        [(0, 1, 2, 3)],
        floormat,
        [[(u0, 0), (u1, 0), (u1, 1), (u0, 1)]],
    )
# A ribbon of glazing above the stair borrows sky from the landside. The entrance
# is level with the raised landing, behind the camera at the south end.
for a, b in [(-19.0, -12.25), (-4.65, 16.8)]:
    box(-13, -12.55, a, b, -0.12, 8.10, plaster)
box(-13, -12.55, -12.25, -4.65, -0.12, 5.10, plaster)
box(-13, -12.55, -12.25, -4.65, 7.22, 8.10, plaster)
for i in range(4):
    a = -12.25 + 1.90 * i
    box(-12.91, -12.74, a, a + 0.06, 5.1, 7.22, iron)
    quad(
        (-12.83, a + 0.06, 5.10),
        (-12.83, a + 1.90, 5.10),
        (-12.83, a + 1.90, 7.22),
        (-12.83, a + 0.06, 7.22),
        glass,
        True,
    )
box(-12.55, -9.13, -19, -18.55, -0.12, 8.1, under)
box(-5.15, 10.8, -19, -18.55, -0.12, 8.1, under)
box(-9.13, -5.15, -19, -18.55, -0.12, 3.52, under)
box(-9.13, -5.15, -19, -18.55, 6.78, 8.1, under)
for i in range(2):
    a = -9.13 + i * 1.99
    b = a + 1.99
    for x in (a, b - 0.047):
        box(x, x + 0.047, -18.82, -18.72, 3.53, 6.78, steel)
    for lo, hi in [(3.54, 5.89), (5.96, 6.77)]:
        fronttex(a + 0.047, b - 0.047, -18.76, lo, hi, glass)
    box(a, b, -18.82, -18.69, 5.89, 5.96, steel)
    box(a + 0.05, b - 0.05, -18.72, -18.64, 4.46, 4.51, steel)
# A recessed roof monitor admits the narrow light that reaches past the rows of seats.
for a, b, c, d in [
    (-12.7, 5.02, -19, 16.9),
    (9.27, 10.85, -19, 16.9),
    (5.02, 9.27, -19, 5.82),
    (5.02, 9.27, 9.16, 16.9),
]:
    box(a, b, c, d, 7.68, 8.05, under)
for x in [5.02, 9.20]:
    box(x, x + 0.073, 5.82, 9.16, 7.68, 8.37, concrete)
for y in [5.82, 9.07]:
    box(5.02, 9.27, y, y + 0.09, 7.68, 8.37, concrete)
# Sloping clear rooflight. An intact roof keeps the leak local to the wall glazing.
roof_glass = newmat("clear rooflight")
pane_out = node(roof_glass, "ShaderNodeOutputMaterial")
through = node(roof_glass, "ShaderNodeBsdfTransparent")
through.inputs[0].default_value = (0.994, 0.996, 0.997, 1)
thin_pane(roof_glass, through.outputs[0], pane_out, 0.075)


def roof_z(x):
    return 8.37 + 0.045 * (9.27 - x)


for x in [5.035, 6.44, 7.86, 9.255]:
    beam((x, 5.825, roof_z(x)), (x, 9.155, roof_z(x)), 0.069, 0.077, iron)
for y in [5.85, 7.47, 9.125]:
    beam((5.035, y, roof_z(5.035)), (9.255, y, roof_z(9.255)), 0.072, 0.082, iron)
for x0, x1 in [(5.035, 6.44), (6.44, 7.86), (7.86, 9.255)]:
    for y0, y1 in [(5.85, 7.47), (7.47, 9.125)]:
        quad(
            (x0, y0, roof_z(x0)), (x1, y0, roof_z(x1)), (x1, y1, roof_z(x1)), (x0, y1, roof_z(x0)), roof_glass
        )
for y in [5.85, 9.125]:
    quad((5.035, y, 8.34), (9.255, y, 8.34), (9.255, y, roof_z(9.255)), (5.035, y, roof_z(5.035)), concrete)
box(5.025, 5.071, 5.83, 9.13, 8.32, roof_z(5.035), concrete)
box(10.42, 10.85, -19, 16.8, -0.18, 1.02, sub)
# The recessed joint exposes the head of the knee wall beneath the sill.
for y0, y1 in [(-19, SILL_JOINT - 0.026), (SILL_JOINT + 0.023, 16.8)]:
    box(10.27, 10.87, y0, y1, 1, 1.14, ledge)
box(10.415, 10.87, SILL_JOINT - 0.026, SILL_JOINT + 0.023, 1, 1.124, sub)
box(10.44, 10.86, -19, 16.8, 6.72, 7.85, concrete)
for yy in [-16.6, -9.3, -2, 5.3, 12.6, 16.5]:
    # Flared web and curved haunch cast as one continuous cross-roof frame.
    xz = [
        (-12.6, 7.72),
        (10.56, 7.72),
        (10.56, 6.87),
        (8.72, 6.86),
        (7.92, 6.58),
        (7.12, 6.04),
        (6.79, 5.64),
        (6.79, 0.02),
        (6.12, 0.02),
        (6.12, 5.68),
        (5.96, 6.03),
        (5.66, 6.36),
        (5.23, 6.60),
        (4.58, 6.76),
        (3.45, 6.86),
        (-9.35, 6.91),
        (-10.85, 6.74),
        (-12.60, 6.28),
    ]
    if large:
        xz = cast_haunch(xz)
    xz_prism(xz, yy - 0.25, yy + 0.25, piermat)
    box(6.08, 6.83, yy - 0.285, yy + 0.285, 0, 0.15, ledge)
    # Shutter-board lines die out on the side faces instead of outlining the structure.
    for z in [1.82, 3.64, 5.45]:
        box(6.12, 6.79, yy - 0.258, yy - 0.25, z, z + 0.012, sub)
for k in range(9):
    x = -11.7 + k * 2.65
    box(x, x + 0.033, -18.55, 16.6, 7.664, 7.681, sub)
# Cast-in roof conduit and two remaining pendant fluorescent strips.
for x in (-5.5, 2.85):
    cyl((x, -18.4, 7.50), (x, 16.3, 7.50), 0.039, iron)
    for y in [-12.5, -5.65, 1.65, 8.95]:
        for yy in [y - 0.72, y + 0.72]:
            cyl((x, yy, 6.78), (x, yy, 7.67), 0.013, steel, 7)
        box(x - 0.125, x + 0.125, y - 0.98, y + 0.98, 6.69, 6.79, iron)
        for xx in (x - 0.056, x + 0.056):
            cyl((xx, y - 0.88, 6.675), (xx, y + 0.88, 6.675), 0.022, cream, 8)
# Steel window wall; narrow awning lights open independently above the main panes.
ys = [-18.56 + i * 2.92 for i in range(13)]
ys[-1] = 16.55


def fixed_pane(a, b, lo, hi):
    quad(
        (10.56, a + 0.046, lo),
        (10.56, b - 0.046, lo),
        (10.56, b - 0.046, hi),
        (10.56, a + 0.046, hi),
        glass,
        True,
    )


for idx, (a, b) in enumerate(zip(ys, ys[1:])):
    box(10.44, 10.57, a - 0.045, a + 0.045, 1.11, 6.77, iron)
    box(10.40, 10.58, a, b, 4.72, 4.80, steel)
    box(10.42, 10.56, a, b, 1.15, 1.205, iron)
    fixed_pane(a, b, 1.14, 4.72)
    if idx not in (4, OPEN_BAY, 8, 10):
        fixed_pane(a, b, 4.8, 6.72)
        continue
    fixed_pane(a, b, 4.8, 5.565)
    box(10.44, 10.56, a + 0.036, b - 0.036, 5.546, 5.589, steel)
    angle = math.radians(23 if idx == OPEN_BAY else 0)
    head_x, head_z = 10.53, 6.68
    bottom_x = head_x - 1.09 * math.sin(angle)
    bottom_z = head_z - 1.09 * math.cos(angle)
    y0, y1 = a + 0.071, b - 0.071
    quad(
        (bottom_x, y0, bottom_z),
        (bottom_x, y1, bottom_z),
        (head_x, y1, head_z),
        (head_x, y0, head_z),
        open_glass if idx == OPEN_BAY else glass,
        True,
    )
    for y in (y0, y1):
        beam((bottom_x, y, bottom_z), (head_x, y, head_z), 0.046, 0.055, steel)
    beam((bottom_x, y0, bottom_z), (bottom_x, y1, bottom_z), 0.062, 0.069, iron)
    beam((head_x, y0, head_z), (head_x, y1, head_z), 0.059, 0.06, steel)
    if idx == OPEN_BAY:
        # Two steel stays brace the open sash; the adjacent blind hangs in its own bay.
        for y in (y0 + 0.025, y1 - 0.025):
            beam((10.493, y, 5.621), (bottom_x + 0.082, y, bottom_z + 0.17), 0.030, 0.036, steel)
            cyl((10.49, y - 0.023, 5.621), (10.49, y + 0.023, 5.621), 0.033, iron, 12)
            cyl(
                (bottom_x + 0.082, y - 0.022, bottom_z + 0.17),
                (bottom_x + 0.082, y + 0.022, bottom_z + 0.17),
                0.027,
                steel,
                12,
            )
        box(
            bottom_x - 0.034,
            bottom_x + 0.029,
            (a + b) / 2 - 0.09,
            (a + b) / 2 + 0.09,
            bottom_z - 0.056,
            bottom_z - 0.022,
            steel,
        )
# The terminal stands on the west side of a dredged harbour basin.
quad((10.8, -550, -3.2), (870, -550, -3.2), (870, 1130, -3.2), (10.8, 1130, -3.2), water)
for j, (xc, yc, rx, ry) in enumerate([(15.6, -9, 4.6, 14.0)]):
    poly = []
    for i in range(78):
        t = math.tau * i / 78
        r = 1 + 0.12 * math.sin(3 * t + 1.2 * j) + 0.06 * math.sin(10 * t + j)
        poly.append((xc + rx * r * math.cos(t), yc + ry * r * math.sin(t)))
    slab_polygon(poly, -3.23, -3.16 + j * 0.004, mud)
# Keep the hall weathering on the same random sequence as the original exposure.
for _ in range(108):
    rng.uniform(-0.20, 0.20)
for a, b in [((26, -4), (35, 0)), ((35, 0), (42, 0))]:
    beam((a[0], a[1], -0.42), (b[0], b[1], -0.42), 1.4, 0.32, farsteel)
    for s in [0, 0.5, 1]:
        xx = a[0] + (b[0] - a[0]) * s
        yy = a[1] + (b[1] - a[1]) * s
        cyl((xx, yy, -3.24), (xx, yy, -0.30), 0.16, dolphin)
for xx, yy, ht in [
    (17, 4, 1.0),
    (17.8, 4.35, 0.74),
    (16.8, 5.12, 1.12),
    (30, 13, 0.8),
    (31, 13.2, 0.7),
    (38, 24, 0.3),
    (22, -11, 0.76),
    (24, -10.8, 0.62),
]:
    cyl((xx + 0.12, yy, -3.3), (xx, yy, ht), 0.20, dolphin, 12, 0.145)
    cyl((xx, yy, ht - 0.32), (xx, yy, ht - 0.25), 0.156, iron)
    cyl((xx + 0.07, yy, -2.6), (xx + 0.035, yy, -1.65), 0.203, sub)
# Rear bulkhead and the disused boarding passage. Apertures are actual holes.
back_y = 16.05
box(-12.6, 0.0, back_y, 16.56, 0, 7.73, plaster)
box(0.0, 4.54, back_y, 16.56, 0, 7.73, plaster)
box(8.78, 10.55, back_y, 16.56, 0, 7.73, plaster)
box(4.54, 8.78, back_y, 16.56, 3.05, 7.73, plaster)
fronttex(-12.55, 4.54, 16.039, 0, 7.68, paintedwall)
fronttex(1.10, 3.53, 15.997, 1.15, 3.72, number)
# Thin scar left by an earlier sign, and the former picture rail.
box(-12.5, 10.44, 15.99, 16.05, 4.69, 4.755, ledge)
box(4.54, 8.78, 16.05, 23.2, -0.16, -0.01, sub)
box(4.50, 4.66, 16, 23.26, 0, 3.09, sub)
box(8.66, 8.79, 16, 23.26, 0, 3.09, sub)
box(4.53, 8.81, 16, 23.3, 2.98, 3.14, under)
box(4.53, 7.41, 22.98, 23.25, 0, 3.08, iron)
box(7.41, 8.79, 22.98, 23.25, 2.24, 3.08, iron)
# The turning landing is outside the far doorway. Its galvanised handrail
# breaks the light behind the locked gate. The gangway leaves on the east.
box(7.37, 7.43, 22.95, 23.27, -0.005, 2.26, steel)
box(7.40, 8.73, 22.95, 23.27, 2.22, 2.28, steel)
box(7.39, 7.69, 23.12, 24.53, -0.28, -0.015, sub)
for xx in (7.44, 9.57, 11.69):
    cyl((xx, 24.47, -0.06), (xx, 24.47, 1.04), 0.035, farsteel, 10)
for h in (0.50, 1.04):
    cyl((7.44, 24.47, h), (11.69, 24.47, h), 0.032, farsteel, 10)
for xx in (4.69, 6.70, 8.57):
    box(xx - 0.039, xx + 0.039, 16.49, 16.61, 0, 2.92, steel)
for a, b in [(4.74, 6.65), (6.75, 8.52)]:
    box(a, b, 16.52, 16.61, 0.04, 0.43, teal)
    box(a, b, 16.53, 16.59, 1.08, 1.18, steel)
    box(a, b, 16.5, 16.58, 2.78, 2.92, steel)
    quad((a, 16.58, 0.44), (b, 16.58, 0.44), (b, 16.58, 2.76), (a, 16.58, 2.76), glass)
    box(b - 0.25, b - 0.22, 16.40, 16.54, 0.89, 1.21, steel)


# The round-ended ticket office is pulled out from the end wall to form its own shadow.
def ticket_office():
    x0, xc, yc = -12.6, -4.25, 12.18
    rad = 1.86
    front = yc - rad
    seg = [(x0, front), (xc, front)]
    for i in range(1, 17):
        t = -math.pi / 2 + i * math.pi / 2 / 16
        seg.append((xc + rad * math.cos(t), yc + rad * math.sin(t)))
    seg.extend([(xc + rad, 16.04), (x0, 16.04)])
    slab_polygon(seg, 0, 1.08, teal)
    slab_polygon(seg, 2.77, 3.23, sub)
    length = 0
    for a, b in zip(seg[:18], seg[1:19]):
        ax, ay = a
        bx, by = b
        t = math.hypot(bx - ax, by - ay)
        nx = (by - ay) / t * 0.012
        ny = -(bx - ax) / t * 0.012
        vv = [
            (ax + nx, ay + ny, 0.13),
            (bx + nx, by + ny, 0.13),
            (bx + nx, by + ny, 1.02),
            (ax + nx, ay + ny, 1.02),
        ]
        mesh(
            vv,
            [(0, 1, 2, 3)],
            tile,
            [
                [
                    (length / 4.5, 0),
                    ((length + t) / 4.5, 0),
                    ((length + t) / 4.5, 1),
                    (length / 4.5, 1),
                ]
            ],
        )
        length += t
    cap = [(x0, front - 0.28), (xc, front - 0.28)]
    for i in range(1, 19):
        t = -math.pi / 2 + i * math.pi / 2 / 18
        cap.append((xc + (rad + 0.28) * math.cos(t), yc + (rad + 0.28) * math.sin(t)))
    cap.extend([(xc + rad + 0.28, 16.05), (x0, 16.05)])
    slab_polygon(cap, 3.20, 3.42, ledge)
    # Horizontal metal ticket shutters behind three deep, dark recesses.
    for j in range(3):
        a = -12.43 + j * 2.67
        b = a + 2.32
        box(a - 0.13, a, front - 0.02, front + 0.18, 1.04, 2.77, piermat)
        box(a, b, front + 0.31, front + 0.36, 1.07, 2.65, dark)
        box(
            a + 0.04,
            b - 0.04,
            front + 0.24,
            front + 0.30,
            1.10 + (j == 1) * 0.18,
            2.63,
            shutter,
        )
        for n in range(14):
            zz = 1.14 + 0.107 * n
            if j != 1 or n >= 2:
                box(
                    a + 0.055,
                    b - 0.055,
                    front + 0.228,
                    front + 0.24,
                    zz,
                    zz + 0.016,
                    iron,
                )
        box(a - 0.15, b + 0.08, front - 0.20, front + 0.31, 1.02, 1.105, ledge)
    for a, b in zip(seg[1:18], seg[2:19]):
        ax, ay = a
        bx, by = b
        quad((ax, ay, 1.09), (bx, by, 1.09), (bx, by, 2.77), (ax, ay, 2.77), shutter)
        if (seg.index(a) - 1) % 3 == 0:
            cyl((ax, ay, 1.07), (ax, ay, 2.79), 0.045, iron, 8)
    for a, b in zip(seg[:17], seg[1:18]):
        beam((a[0], a[1], 0.17), (b[0], b[1], 0.17), 0.045, 0.07, sub)


ticket_office()
# A route map and a moveable-looking display still bolted to the building.
box(-1.65, -0.52, 15.83, 16, 1.10, 2.68, iron)
fronttex(-1.59, -0.58, 15.82, 1.16, 2.62, routemap)
box(-7.55, -3.42, 10.06, 10.31, 3.45, 4.38, iron)
fronttex(-7.47, -3.50, 10.048, 3.51, 4.31, board)
for xx in (-7.16, -3.80):
    box(xx - 0.035, xx + 0.035, 10.20, 10.28, 3.34, 3.51, steel)


# Floor anchors, broad curved seat pans and several bare brackets.
def bench(cx, cy, angle, seats):
    ca, sa = math.cos(angle), math.sin(angle)

    def pos(x, y, z):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca, z)

    n = len(seats)
    step = PITCH
    span = n * step
    for xx in feet(n):
        beam(pos(xx, -0.26, 0.045), pos(xx, 0.28, 0.045), 0.12, 0.07, iron)
        beam(pos(xx, -0.06, 0.08), pos(xx, -0.01, 0.36), 0.10, 0.09, steel)
        for yy in [-0.22, 0.24]:
            cyl(pos(xx, yy, 0.077), pos(xx, yy, 0.10), 0.027, steel, 8)
    beam(
        pos(-span * 0.5 + 0.06, -0.04, 0.34),
        pos(span * 0.5 - 0.06, -0.04, 0.34),
        0.12,
        0.11,
        iron,
    )
    # Bent alloy end grips share the through-rail. The small bakelite pads have
    # lost the finish on the upper curve where people used them to rise.
    for end in (-1, 1):
        k = end * (span * 0.5 - 0.045)
        rail = [
            (k, -0.17, 0.36),
            (k, -0.24, 0.59),
            (k, -0.205, 0.665),
            (k, -0.139, 0.687),
            (k, 0.127, 0.687),
            (k, 0.195, 0.669),
            (k, 0.217, 0.612),
            (k, 0.150, 0.425),
        ]
        pipe([pos(*q) for q in rail], 0.018, steel, 10)
        cyl(pos(k, -0.134, 0.690), pos(k, 0.130, 0.690), 0.029, dark, 12)
    for k, mat in enumerate(seats):
        cen = (k - (n - 1) * 0.5) * step
        for di in [-0.16, 0.16]:
            beam(
                pos(cen + di, -0.30, 0.395),
                pos(cen + di, 0.24, 0.395),
                0.041,
                0.055,
                steel,
            )
        if mat is None:
            continue
        profile = [
            (0.325, 0.445, 0.78),
            (0.329, 0.481, 0.86),
            (0.274, 0.505, 0.96),
            (0.125, 0.462, 1),
            (-0.07, 0.435, 1),
            (-0.19, 0.458, 1),
            (-0.266, 0.518, 1),
            (-0.288, 0.60, 1),
            (-0.327, 0.76, 0.98),
            (-0.388, 0.897, 0.90),
            (-0.397, 0.925, 0.77),
        ]
        if large:
            profile = moulded_shell(profile)
            us = [j / 8 for j in range(-8, 9)]
        else:
            us = [-1, -0.86, -0.57, 0, 0.57, 0.86, 1]
        w = 0.314
        vertices = []
        for skin in [0, 1]:
            for i, (yy, zz, sw) in enumerate(profile):
                fraction = i / (len(profile) - 1)
                taper = fraction * 2 / 3 if large else i / 15
                for u in us:
                    side = u * u
                    vertices.append(
                        pos(
                            cen + w * sw * u,
                            yy + 0.034 * side * fraction - skin * 0.028 * fraction,
                            zz + 0.043 * side * (1 - taper) - skin * 0.033,
                        )
                    )
        n1 = len(us)
        half = n1 * len(profile)
        faces = []
        for skin in [0, 1]:
            for i in range(len(profile) - 1):
                for j in range(n1 - 1):
                    idx = skin * half + n1 * i + j
                    face = (idx, idx + 1, idx + n1 + 1, idx + n1)
                    faces.append(face if skin else face[::-1])
        for j in range(n1 - 1):
            for i in [0, len(profile) - 1]:
                q = i * n1 + j
                faces.append((q, q + 1, q + 1 + half, q + half))
        for i in range(len(profile) - 1):
            for j in [0, n1 - 1]:
                q = i * n1 + j
                faces.append((q, q + n1, q + n1 + half, q + half))
        mesh(vertices, faces, mat, smooth=True)


shells = {"deep": seat1, "sea": seat2, "lichen": seat3, "ochre": ochre_seat, None: None}
for cx, cy, heading, colours in BANKS:
    bench(cx, cy, heading, [shells[c] for c in colours])


# Curving stair: every nosing, cheek and rail shares the same plan arc and rise.
def stair():
    sx, sy = -6.61, -9.12
    rad = 10.65
    width = 3.48
    steps = 21
    run = 0.335
    rise = 0.168

    def spot(s, u, z):
        t = s / rad
        return (sx - rad + (rad + u) * math.cos(t), sy + (rad + u) * math.sin(t), z)

    bottom = steps * rise
    box(-12.55, sx + width / 2, -18.56, sy, -0.1, bottom - 0.12, under)
    box(-12.55, sx + width / 2, -18.56, sy, bottom - 0.13, bottom, ledge)
    for k in range(steps):
        s = k * run
        t = (k + 1) * run
        z = bottom - k * rise
        quad(
            spot(t, -width / 2, z - rise - 0.38),
            spot(t, width / 2, z - rise - 0.38),
            spot(s, width / 2, z - 0.38),
            spot(s, -width / 2, z - 0.38),
            under,
        )
        P = [
            spot(s, -width / 2, z),
            spot(s, width / 2, z),
            spot(t, width / 2, z),
            spot(t, -width / 2, z),
        ]
        quad(*P, sub)
        quad(
            spot(t, -width / 2, z - rise),
            spot(t, width / 2, z - rise),
            P[2],
            P[3],
            piermat,
        )
        quad(
            spot(t - 0.047, -width / 2, z + 0.004),
            spot(t - 0.047, width / 2, z + 0.004),
            spot(t, width / 2, z + 0.004),
            spot(t, -width / 2, z + 0.004),
            ledge,
        )
    for u in [-width / 2, width / 2]:
        for k in range(steps):
            s = k * run
            t = (k + 1) * run
            za = bottom - k * rise
            zb = za - rise
            for du in [-0.085, 0.085]:
                quad(
                    spot(s, u + du, za - 0.39),
                    spot(t, u + du, zb - 0.39),
                    spot(t, u + du, zb + 0.19),
                    spot(s, u + du, za + 0.19),
                    sub,
                )
            quad(
                spot(s, u - 0.085, za + 0.19),
                spot(s, u + 0.085, za + 0.19),
                spot(t, u + 0.085, zb + 0.19),
                spot(t, u - 0.085, zb + 0.19),
                ledge,
            )
            a = spot(s, u, za + 0.98)
            b = spot(t, u, zb + 0.98)
            cyl(a, b, 0.065, wood, 12)
            for h in [0.44, 0.65]:
                cyl(spot(s, u, za + h), spot(t, u, zb + h), 0.017, iron, 8)
            if k % 3 == 0:
                cyl(spot(s, u, za + 0.12), spot(s, u, za + 0.96), 0.027, steel, 10)
        for h, r, m in [(0.98, 0.065, wood), (0.65, 0.017, iron), (0.44, 0.017, iron)]:
            cyl((sx + u, -18.45, bottom + h), (sx + u, sy, bottom + h), r, m)
        for yy in [-17.8, -16.5, -15.2, -13.9, -12.6, -11.3, -10.0]:
            cyl((sx + u, yy, bottom), (sx + u, yy, bottom + 0.96), 0.029, steel, 10)
    # Rounded end of the outer handrail.
    a = spot(steps * run, width / 2, 0.98)
    b = spot(steps * run + 0.22, width / 2, 0.91)
    pipe([a, b, (b[0] - 0.012, b[1] + 0.035, 0.76)], 0.059, wood)


stair()


# A single faded life ring and its rope on the side of a pier.
def life_ring(cx, cy, z):
    R = 0.34
    r = 0.062
    for i in range(48):
        a = math.tau * i / 48
        b = math.tau * (i + 1) / 48
        col = cream if i % 12 in (1, 2, 3) else rust
        vv = []
        for t in [a, b]:
            for j in range(10):
                f = math.tau * j / 10
                vv.append(
                    (
                        cx + (R + r * math.cos(f)) * math.cos(t),
                        cy + r * math.sin(f),
                        z + (R + r * math.cos(f)) * math.sin(t),
                    )
                )
        mesh(
            vv,
            [(j, (j + 1) % 10, 10 + (j + 1) % 10, 10 + j) for j in range(10)],
            col,
            smooth=True,
        )
    pts = []
    for i in range(65):
        a = i * math.tau / 64
        rr = 0.395 + 0.034 * (1 + math.cos(4 * a))
        pts.append((cx + rr * math.cos(a), cy + 0.04, z + rr * math.sin(a) - 0.04))
    pipe(pts, 0.012, cream, 6)
    pipe(
        [
            (cx + 0.27, cy + 0.055, z - 0.24),
            (cx + 0.34, cy + 0.03, z - 0.51),
            (cx + 0.29, cy + 0.02, z - 0.64),
            (cx + 0.25, cy + 0.025, z - 0.61),
        ],
        0.011,
        cream,
        6,
    )
    box(cx - 0.06, cx + 0.06, cy + 0.04, cy + 0.18, z + 0.32, z + 0.43, iron)


life_ring(*RING_CENTRE)
# A swing gate near the berth. Gate rails are open enough to see the threshold.
for lane in [4.97, 6.42, 8.07]:
    for yy in [13.0, 14.6]:
        cyl((lane, yy, 0.02), (lane, yy, 1.02), 0.046, steel)
        cyl((lane, yy, 0.006), (lane, yy, 0.047), 0.092, iron)
    for zz in [0.32, 0.74, 1.01]:
        cyl((lane, 13, zz), (lane, 14.60, zz), 0.028, steel)
for x in (4.97, 6.42):
    cyl((x + 0.04, 14.4, 0.79), (x + 0.71, 14.4, 0.79), 0.032, iron)
import fittings, last_details, estuary, concourse

fittings.add(globals(), large=large)
last_details.add(globals())
estuary.add(globals())
concourse.add(globals())
from shore import draw_shore
draw_shore(globals())
# A thin volume gives the skylight a path through the sea air.
haze = newmat("suspended sea air")
out = node(haze, "ShaderNodeOutputMaterial")
vol = node(haze, "ShaderNodeVolumeScatter")
vol.inputs["Density"].default_value = 0.0048
vol.inputs["Color"].default_value = (0.77, 0.83, 0.82, 1)
vol.inputs["Anisotropy"].default_value = 0.28
link(haze, vol.outputs[0], out.inputs["Volume"])
box(-12.52, 10.41, -18.53, 16.018, 0.008, 7.66, haze)
# Populate and render.
for key, (vertices, faces, uvs, smooths) in pieces.items():
    data = bpy.data.meshes.new(key)
    data.from_pydata(vertices, [], faces)
    data.materials.append(materials[key])
    data.update()
    ob = bpy.data.objects.new(key, data)
    scene.collection.objects.link(ob)
    if any(u is not None for u in uvs):
        layer = data.uv_layers.new()
        for poly, uv in zip(data.polygons, uvs):
            if uv is not None:
                for li, xy in zip(poly.loop_indices, uv):
                    layer.data[li].uv = xy
    for poly, s in zip(data.polygons, smooths):
        poly.use_smooth = s
world = bpy.data.worlds.new("estuary sky")
scene.world = world
world.node_tree.nodes["Background"].inputs[0].default_value = (0.72, 0.83, 0.91, 1)
env = world.node_tree.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(str(args.maps / "sea-sky.png"))
world.node_tree.links.new(env.outputs["Color"], world.node_tree.nodes["Background"].inputs[0])
world.node_tree.nodes["Background"].inputs[1].default_value = 0.81


def light(name, kind, position, vec, power, color, size):
    d = bpy.data.lights.new(name, kind)
    d.energy = power
    d.color = color
    if kind == "SUN":
        d.angle = size
    else:
        d.shape = "DISK"
        d.size = size
    o = bpy.data.objects.new(name, d)
    scene.collection.objects.link(o)
    o.location = position
    o.rotation_euler = Vector(vec).to_track_quat("-Z", "Y").to_euler()


light(
    "daylight filtered through morning cloud",
    "SUN",
    (25, 9, 18),
    (-0.82, 0.415, -0.46),
    4.23,
    (0.990, 0.944, 0.860),
    0.056,
)
# The open sky is both fill for the hall and a source of reflections. Its
# position and width place its broken image alongside the nearest pier.
light(
    "open sky beyond glazing",
    "AREA",
    (18, 1, 8),
    (-1, 0.04, -0.47),
    5800,
    (0.82, 0.91, 1),
    15,
)
light(
    "overcast sky above the landside stair",
    "AREA",
    (-13.5, -8.65, 6.25),
    (1, 0.46, -0.12),
    425,
    (0.86, 0.92, 1),
    6.4,
)
cam = bpy.data.cameras.new("landing")
o = bpy.data.objects.new("landing camera", cam)
scene.collection.objects.link(o)
eye = LANDING_EYE
target = (2.8, 7.0, 1.53)
lens = 29.0
o.location = eye
o.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
cam.lens = lens
cam.clip_end = 1500
scene.camera = o
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = args.samples
scene.cycles.use_denoising = False
scene.cycles.seed = 102
scene.cycles.volume_bounces = 1
scene.cycles.max_bounces = 7
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 3
scene.cycles.transparent_max_bounces = 8
if large:
    scene.cycles.adaptive_threshold = 0.035 if args.samples <= 64 else 0.023
    scene.cycles.adaptive_min_samples = 16 if args.samples <= 64 else 40
    scene.cycles.filter_width = 1.10
else:
    scene.cycles.adaptive_threshold = 0.036 if args.samples <= 56 else (0.016 if args.samples < 256 else 0.012)
    scene.cycles.filter_width = 0.90
scene.render.resolution_x = args.width
scene.render.resolution_y = args.width * 3 // 4
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.30
outpath = Path(args.output).resolve()
bpy.context.view_layer.update()
full_capture = not any((args.clock_only, args.windows_only, args.marks_only, args.exterior_only,
                        args.harbour_depth_only, args.concrete_only, args.film_only, args.surfaces_only,
                        args.berth_concrete_only))
if args.berth_concrete_only or full_capture:
    from berth_concrete import SITES as berth_sites, OVERLAYS as berth_overlays
    from concrete_wear import record_surfaces
    record_surfaces(scene, outpath, large=large, areas=berth_sites, suffix=".berth-concrete.npz",
                    overlays=berth_overlays)
if args.berth_concrete_only:
    raise SystemExit(0)
if args.film_only or full_capture:
    from drain_film import record as record_film
    record_film(scene, floormat, args.maps, outpath)
if args.film_only:
    raise SystemExit(0)
if args.surfaces_only or full_capture:
    from concrete_wear import record_surfaces
    from hall_finishes import FINISHES
    record_surfaces(scene, outpath, large=large, areas=FINISHES, suffix=".finishes.npz")
if args.surfaces_only:
    raise SystemExit(0)
if args.concrete_only or full_capture:
    from concrete_wear import record_surfaces
    record_surfaces(scene, outpath, large=large)
if args.concrete_only:
    raise SystemExit(0)
if large and not (args.clock_only or args.windows_only or args.marks_only):
    from harbour_air import record_distance
    record_distance(scene, outpath)
if args.harbour_depth_only:
    raise SystemExit(0)
if args.exterior_only:
    from window_exposure import take
    take(scene, outpath, large=large, far_shore=args.far_shore)
    raise SystemExit(0)

import accents

if not (args.clock_only or args.windows_only):
    accents.draw(scene, bpy.context.evaluated_depsgraph_get(), outpath.with_suffix(".marks.json"), large=large)
if not args.marks_only:
    if not (args.clock_only or args.windows_only):
        import surface_guides
        surface_guides.expose(scene, outpath, large=large)
    if not args.windows_only:
        from clock_glass import expose
        expose(globals(), outpath, large=large)
    else:
        from clock_glass import install
        install(globals())
    if not args.clock_only:
        from harbour_glass import photograph
        photograph(globals(), outpath, args.samples)
