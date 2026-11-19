#!/usr/bin/env python3
# /// script
# requires-python = "==3.12.11"
# dependencies = ["numpy==2.3.5", "pillow==13.0.0"]
# ///
"""Draw After Hours from a shared 3D scene, camera and authored pixel palette.

Run: uv run after_hours.py
"""

import argparse
import json
import math
import os
from pathlib import Path
import sys
import time

import numpy as np
from PIL import Image
import art

ROOT = Path(__file__).resolve().parent


def configure_paths(output_dir=None, build_dir=None):
    """Share absolute paths with animation workers and verification processes."""
    global OUTPUT_DIR, BUILD_DIR, STILL_DIR, ANIMATION_DIR, PALETTE_DIR, REPORT_DIR, FRAME_DIR, NATIVE_DIR
    OUTPUT_DIR = Path(output_dir if output_dir is not None else os.environ.get("AFTER_HOURS_OUTPUT_DIR", ROOT / "build/exports")).resolve()
    BUILD_DIR = Path(build_dir if build_dir is not None else os.environ.get("AFTER_HOURS_BUILD_DIR", ROOT / "build")).resolve()
    STILL_DIR = OUTPUT_DIR / "still"
    ANIMATION_DIR = OUTPUT_DIR / "animation"
    PALETTE_DIR = OUTPUT_DIR / "palette"
    REPORT_DIR = BUILD_DIR / "reports"
    FRAME_DIR = BUILD_DIR / "frames"
    NATIVE_DIR = BUILD_DIR / "native"
    os.environ["AFTER_HOURS_OUTPUT_DIR"] = str(OUTPUT_DIR)
    os.environ["AFTER_HOURS_BUILD_DIR"] = str(BUILD_DIR)


configure_paths()


# Scene geometry, camera, water optics and rendering.


W, H = 384, 256
ANIMATION_TIME = 0.0
LOOP_SECONDS = 8.0
# An off-centre principal point is equivalent to cropping the taller camera
# view. It tightens the framing without distorting or moving scene objects.
CX, CY = W / 2, H / 2 - 16
EYE = np.array([-2.7, 5.5, 1.4])
TARGET = np.array([6.5, 0.35, 6.2])
FOV = 62.0
WATER = -0.15
FLOOR = -3.95
IOR = 1.333
ABSORPTION = np.array([0.50, 0.115, 0.075])
WATER_SCATTER = np.array([0.001, 0.005, 0.009])
PAL = {
    "ink": "0b0c19",
    "blackberry": "1b142b",
    "night": "2b1c3e",
    "plum": "472344",
    "mauve": "67344e",
    "dust": "8a4b63",
    "lilac": "b27584",
    "rose": "dda39f",
    "clay": "e7c9a6",
    "petrol": "0b2036",
    "deepwater": "103e57",
    "teal": "106974",
    "verdigris": "11978d",
    "jade": "45cbb2",
    "sage": "98edc9",
    "celadon": "e2ffe2",
    "litgrout": "704337",
    "rust": "874030",
    "terracotta": "bc6139",
    "ochre": "e99a4b",
    "apricot": "ffd185",
    "butter": "fff0c2",
    "red": "ed626e",
    "slate": "203147",
    "bluegrey": "34596b",
    "steel": "5b929e",
    "pewter": "a2c7c4",
    "grout": "442b31",
}
RGB = np.array([tuple(bytes.fromhex(c)) for c in PAL.values()], float) / 255


def norm(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-15)


def linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - 0.055)


def colour(n):
    return linear(RGB[list(PAL).index(n)])


FORWARD = norm(TARGET - EYE)
RIGHT = norm(np.cross([0, 1, 0], FORWARD))
UP = norm(np.cross(FORWARD, RIGHT))
FOCAL = W / (2 * math.tan(math.radians(FOV) / 2))


def project(p):
    q = np.asarray(p) - EYE
    return np.stack([CX + FOCAL * (q @ RIGHT) / (q @ FORWARD), CY - FOCAL * (q @ UP) / (q @ FORWARD)], axis=-1)


def camera_rays():
    y, x = np.mgrid[0:H, 0:W]
    d = FORWARD + ((x.ravel() + 0.5 - CX) / FOCAL)[:, None] * RIGHT - ((y.ravel() + 0.5 - CY) / FOCAL)[:, None] * UP
    return np.broadcast_to(EYE, d.shape).copy(), norm(d)


# All lengths below are metres. X crosses the pool, Z follows its long side;
# Y is height. No object has a screen-space position or apparent-size override.
MATS = {
    "wall": ("mauve", 0.0),
    "concrete": ("mauve", 0.0),
    "concrete_light": ("lilac", 0.0),
    "deck": ("dust", 0.0),
    "coping": ("clay", 0.0),
    "pool": ("sage", 0.0),
    "black": ("ink", 0.0),
    "metal": ("steel", 0.45),
    "wood": ("rust", 0.0),
    "door": ("rust", 0.0),
    "inside": ("ochre", 0.0),
    "glass": ("slate", 0.15),
    "shirt": ("terracotta", 0.02),
    "pants": ("slate", 0.0),
    "skin": ("ochre", 0.0),
    "cap": ("petrol", 0.0),
    "cup": ("clay", 0.0),
    "ring": ("clay", 0.0),
    "ring_red": ("red", 0.0),
    "rope": ("dust", 0.0),
    "towel": ("terracotta", 0.0),
    "lamp": ("butter", 0.0),
    "wetlamp": ("celadon", 0.0),
    "utility_lamp": ("butter", 0.0),
    "foreground": ("mauve", 0.0),
    "foreground_metal": ("steel", 0.50),
    "hair": ("blackberry", 0.0),
    "towel_fabric": ("bluegrey", 0.0),
}
OBJECTS = []


def box(lo, hi, mat, label=""):
    OBJECTS.append(dict(kind="box", lo=np.array(lo, float), hi=np.array(hi, float), mat=mat, label=label))


def rect(p, a, b, mat, label=""):
    p, a, b = map(lambda x: np.array(x, float), (p, a, b))
    n = norm(np.cross(a, b))
    OBJECTS.append(dict(kind="rect", p=p, a=a, b=b, n=n, mat=mat, label=label))


def ellipsoid(c, r, mat, label=""):
    OBJECTS.append(dict(kind="ellipsoid", p=np.array(c, float), r=np.array(r, float), mat=mat, label=label))


def tube(a, b, r, mat, label=""):
    a, b = np.array(a, float), np.array(b, float)
    if np.linalg.norm(b - a) < 1e-8:
        return
    OBJECTS.append(dict(kind="tube", p=a, axis=norm(b - a), length=float(np.linalg.norm(b - a)), r=r, mat=mat, label=label))


def pipe(points, r, mat, label=""):
    for a, b in zip(points, points[1:]):
        tube(a, b, r, mat, label)
    for p in points[1:-1]:
        ellipsoid(p, [r] * 3, mat, label)


# Building envelope, with a genuine door opening cut from the back wall.
rect((-3, 0, 14), (11.2, 0, 0), (0, 6.5, 0), "wall", "back-wall-left")
rect((9.2, 0, 14), (2.8, 0, 0), (0, 6.5, 0), "wall", "back-wall-right")
rect((8.2, 2.1, 14), (1, 0, 0), (0, 4.4, 0), "wall", "door-lintel-wall")
rect((-3, 0, -4), (0, 0, 18), (0, 6.5, 0), "wall", "left-wall")
rect((12, 0, 14), (0, 0, -18), (0, 6.5, 0), "wall", "right-wall")
rect((-3, 6.5, -4), (15, 0, 0), (0, 0, 18), "concrete", "ceiling")
# Deck is four non-overlapping rectangles with an actual opening for the basin.
rect((-3, 0, -4), (15, 0, 0), (0, 0, 4), "deck", "near-deck")
rect((-3, 0, 0), (3, 0, 0), (0, 0, 12), "deck", "left-deck")
rect((8, 0, 0), (4, 0, 0), (0, 0, 12), "deck", "right-deck")
rect((-3, 0, 12), (15, 0, 0), (0, 0, 2), "deck", "far-deck")
rect((0, FLOOR, 0), (8, 0, 0), (0, 0, 12), "pool", "basin-floor")
rect((0, FLOOR, 0), (0, 0, 12), (0, -FLOOR, 0), "pool", "basin-left")
rect((8, FLOOR, 12), (0, 0, -12), (0, -FLOOR, 0), "pool", "basin-right")
rect((0, FLOOR, 12), (8, 0, 0), (0, -FLOOR, 0), "pool", "basin-far")
rect((8, FLOOR, 0), (-8, 0, 0), (0, -FLOOR, 0), "pool", "basin-near")
# Coping overhang remains thin, with a real waterline 15 cm below the deck.
box((-0.18, -0.08, -0.18), (8.18, 0.045, 0), "coping", "near-coping")
box((-0.18, -0.08, 12), (8.18, 0.045, 12.18), "coping", "far-coping")
box((-0.18, -0.08, 0), (0, 0.045, 12), "coping", "left-coping")
box((8, -0.08, 0), (8.18, 0.045, 12), "coping", "right-coping")

# Tall clerestory, columns, and ceiling beams. Frame spacings are physical.
for x in np.arange(-2.7, 11.4, 1.35):
    rect((x, 3.05, 13.975), (1.22, 0, 0), (0, 2.25, 0), "glass", "window")
    box((x - 0.035, 3.01, 13.91), (x + 0.035, 5.35, 14), "concrete", "window-mullion")
    box((x, 4.14, 13.91), (x + 1.22, 4.19, 14), "metal", "window-crossbar")
for y in [3.0, 5.31]:
    box((-3, y, 13.87), (12, y + 0.07, 14), "concrete_light", "window-sill")
for x in [-2.9, 2.4, 6.7, 11.5]:
    box((x, 0, 13.7), (x + 0.26, 6.5, 14), "concrete_light", "building-column")
    box((x, 6.1, -4), (x + 0.26, 6.5, 14), "concrete", "ceiling-beam")

# A 3 m diving platform, its supports on the dry deck, and a reachable stair.
box((-3, 2.75, 1.8), (2.2, 3, 3.2), "foreground", "diving-platform")
box((-1.8, 0, 2.0), (-1.25, 2.75, 3.0), "foreground", "platform-pier")
box((-1.87, 0, 1.94), (-1.18, 0.13, 3.07), "foreground", "pier-footing")
for z in [1.84, 3.16]:
    for x in [-2.9, -1.6, -0.3, 1.0]:
        tube((x, 3, z), (x, 4.05, z), 0.027, "foreground_metal", "platform-guard-post")
    tube((-3, 4.05, z), (1.2, 4.05, z), 0.029, "foreground_metal", "platform-top-rail")
    tube((-3, 3.55, z), (1.2, 3.55, z), 0.02, "foreground_metal", "platform-mid-rail")
for j in range(15):
    z = 3.2 + j * 0.25
    top = 3 - j * 0.2
    box((-2.9, 0, z), (-2.1, top, z + 0.25), "foreground", "access-stair")
for x in [-2.85, -2.15]:
    tube((x, 4.05, 3.25), (x, 1.05, 7), 0.025, "metal", "stair-hand-rail")
    for z, y in [(3.25, 3), (4.5, 2), (5.75, 1), (7, 0)]:
        tube((x, y, z), (x, y + 1.05, z), 0.023, "metal", "stair-post")

# A small folded towel drapes around the far rail: its curved top follows the
# rail, and both hanging sides are constructed in world space.
for j in range(12):
    x = -0.85 + j * 0.052
    z0 = 3.12 + 0.014 * math.sin(j * math.pi / 3)
    z1 = 3.12 + 0.014 * math.sin((j + 1) * math.pi / 3)
    length = 0.68 + 0.025 * math.sin(j * math.pi / 4)
    rect((x, 4.05, z0), (0.052, 0, z1 - z0), (0, -length, 0), "towel_fabric", "rail-towel")
    rect((x, 4.05 - length + 0.045, z0 - 0.001), (0.052, 0, z1 - z0), (0, -0.025, 0), "wood", "towel-border")
    rect((x, 4.05, 3.20), (0.052, 0, 0), (0, -0.37, 0), "towel_fabric", "rail-towel-back")
    for a in np.linspace(0, math.pi, 9)[:-1]:
        b = a + math.pi / 8
        rect(
            (x, 4.05 + 0.04 * math.sin(a), 3.16 + 0.04 * math.cos(a)),
            (0.052, 0, 0),
            (0, 0.04 * (math.sin(b) - math.sin(a)), 0.04 * (math.cos(b) - math.cos(a))),
            "towel_fabric",
            "towel-wrap",
        )

# Pool ladder, .60 m between rails; its .30 m steps really continue underwater.
LADDER_X = [2.15, 2.75]
for x in LADDER_X:
    # Each hoop consists of vertical legs and a semi-circle in the Y/Z plane.
    points = [(x, 0, -0.46), (x, 0.72, -0.46)]
    for a in np.linspace(math.pi, 0, 13):
        points.append((x, 0.72 + 0.39 * math.sin(a), -0.07 + 0.39 * math.cos(a)))
    points += [(x, -1.65, 0.32)]
    pipe(points, 0.026, "metal", "ladder-rail")
    box((x - 0.065, 0, -0.525), (x + 0.065, 0.045, -0.395), "metal", "ladder-anchor")
    tube((x, -1.6, 0.32), (x, -1.6, 0.02), 0.023, "metal", "ladder-wall-standoff")
for y in [-0.15, -0.45, -0.75, -1.05, -1.35, -1.65]:
    box((LADDER_X[0], y - 0.025, 0.23), (LADDER_X[1], y + 0.025, 0.36), "metal", "ladder-tread")

# Door frame and an open leaf rotate around the same floor-level hinge.
for x in [8.16, 9.2]:
    box((x, 0, 13.9), (x + 0.04, 2.14, 14.08), "wood", "door-frame")
box((8.16, 2.1, 13.9), (9.24, 2.16, 14.08), "wood", "door-frame")
rect((8.2, 0.015, 14.02), (0.50, 0, math.sqrt(3) / 2), (0, 2.07, 0), "door", "open-door-leaf")
ellipsoid((8.61, 1.01, 14.71), [0.035, 0.035, 0.035], "metal", "door-handle")
rect((8.18, 0, 16), (1.04, 0, 0), (0, 2.6, 0), "inside", "store-back")
rect((8.18, 0, 14), (1.04, 0, 0), (0, 0, 2), "inside", "store-floor")
rect((8.18, 0, 14), (0, 0, 2), (0, 2.6, 0), "inside", "store-left")
rect((9.22, 0, 16), (0, 0, -2), (0, 2.6, 0), "inside", "store-right")
for y in [0.5, 1.15, 1.8]:
    box((8.3, y, 15.64), (9.1, y + 0.045, 15.97), "wood", "shelf")
for x, y in [(8.4, 1.2), (8.8, 0.55), (8.82, 1.85)]:
    box((x, y, 15.7), (x + 0.16, y + 0.21, 15.86), "cup", "bottle")
    box((x + 0.04, y + 0.21, 15.74), (x + 0.11, y + 0.25, 15.81), "wood", "bottle-lid")
box((8.4, 2.3, 13.76), (9, 2.48, 13.96), "black", "lamp-housing")
rect((8.43, 2.33, 13.755), (0.54, 0, 0), (0, 0.11, 0), "lamp", "amber-lamp")

# The far underwater lamp lights the basin. The near lamp is dark.
for z in [3.7, 9.2]:
    box((7.94, -1.03, z - 0.19), (8, -0.73, z + 0.19), "black", "pool-lamp-housing")
    rect((7.935, -1.0, z - 0.16), (0, 0, 0.32), (0, 0.24, 0), "black" if z < 7 else "wetlamp", "pool-lamp")

# Bench and equipment, all sized and grounded in the same coordinate system.
for z in [13.0, 13.17, 13.34]:
    box((3.5, 0.46, z), (5.55, 0.515, z + 0.13), "wood", "bench-slat")
for x in [3.65, 5.4]:
    for z in [13.04, 13.4]:
        box((x, 0, z), (x + 0.065, 0.46, z + 0.065), "metal", "bench-leg")
box((4.2, 0.52, 13.0), (4.53, 0.54, 13.45), "towel", "folded-towel")
rect((4.2, 0.2, 12.995), (0.33, 0, 0), (0, 0.32, 0), "towel", "hanging-towel")
# Lifebuoy as a true torus assembled from short round sections in the wall plane.
center = np.array([5.45, 1.55, 13.81])
rr = 0.29
for i in range(28):
    a = 2 * math.pi * i / 28
    b = 2 * math.pi * (i + 1) / 28
    p = center + [rr * math.cos(a), rr * math.sin(a), 0]
    q = center + [rr * math.cos(b), rr * math.sin(b), 0]
    tube(p, q, 0.058, "ring_red" if i % 7 in [0, 1] else "ring", "lifebuoy")
pipe([(5.17, 1.5, 13.84), (5.18, 0.98, 13.85), (5.45, 0.85, 13.84), (5.72, 0.99, 13.84), (5.74, 1.5, 13.84)], 0.013, "rope", "buoy-rope")

# Seated adult at the end of the platform, holding a cup. The pelvis touches
# the deck at Y=3 m; knees and feet hang beyond the open end. Dimensions are
# retained in metres, and the entire pose is rotated rigidly in world space.
PERSON_START = len(OBJECTS)
hx, hz = 2.10, 2.50
ellipsoid((hx, 0.59, hz), [0.20, 0.15, 0.16], "pants", "hips")
ellipsoid((hx, 0.88, hz + 0.015), [0.235, 0.30, 0.145], "shirt", "torso")
ellipsoid((hx, 1.235, hz - 0.045), [0.11, 0.14, 0.105], "skin", "head")
ellipsoid((hx, 1.355, hz - 0.045), [0.12, 0.045, 0.115], "cap", "cap-crown")
ellipsoid((hx, 1.33, hz - 0.14), [0.12, 0.014, 0.12], "cap", "cap-brim")
# Hair and ears distinguish the back/side of the head from the jacket collar.
ellipsoid((hx, 1.265, hz + 0.048), [0.10, 0.078, 0.065], "hair", "hair")
for side in [-1, 1]:
    ellipsoid((hx + 0.109 * side, 1.225, hz - 0.035), [0.024, 0.035, 0.034], "skin", "ear")
for s in [-1, 1]:
    hip = (hx + s * 0.13, 0.56, hz - 0.04)
    knee = (hx + s * 0.17, 0.49, hz - 0.46)
    ankle = (hx + s * 0.17, 0.105, hz - 0.61)
    tube(hip, knee, 0.083, "pants", "thigh")
    ellipsoid(knee, [0.08] * 3, "pants", "knee")
    tube(knee, ankle, 0.065, "pants", "shin")
    ellipsoid((hx + s * 0.17, 0.065, hz - 0.7), [0.085, 0.065, 0.16], "black", "shoe")
    shoulder = (hx + s * 0.21, 1.02, hz + 0.005)
    elbow = (hx + s * 0.26, 0.78, hz - 0.17)
    hand = (hx + s * 0.07, 0.73, hz - 0.35)
    tube(shoulder, elbow, 0.065, "shirt", "upper-arm")
    tube(elbow, hand, 0.055, "shirt", "forearm")
    ellipsoid(hand, [0.046] * 3, "skin", "hand")
tube((hx, 0.69, hz - 0.38), (hx, 0.82, hz - 0.38), 0.045, "cup", "cup")
# A 45-degree pose exposes the cup and one dangling leg to the oblique camera.
angle = -math.pi / 4
turn = np.array([[math.cos(angle), 0, math.sin(angle)], [0, 1, 0], [-math.sin(angle), 0, math.cos(angle)]])
pivot = np.array([hx, 0, hz])
SEAT_OFFSET = 2.56
for o in OBJECTS[PERSON_START:]:
    if o["kind"] == "box":
        corners = np.array(
            [[x, y, z] for x in [o["lo"][0], o["hi"][0]] for y in [o["lo"][1], o["hi"][1]] for z in [o["lo"][2], o["hi"][2]]]
        )
        corners = (corners - pivot) @ turn.T + pivot
        o["lo"] = corners.min(0)
        o["hi"] = corners.max(0)
    else:
        o["p"] = turn @ (o["p"] - pivot) + pivot + [0, SEAT_OFFSET, 0]
        if o["kind"] == "rect":
            o["a"] = turn @ o["a"]
            o["b"] = turn @ o["b"]
            o["n"] = turn @ o["n"]
        elif o["kind"] == "tube":
            o["axis"] = turn @ o["axis"]
        else:
            o["rotation"] = turn.copy()

# A real ceiling fixture makes the near figure legible. Its housing is outside
# this crop; its direct light still casts shadows against all scene geometry.
box((-0.65, 5.93, 2.32), (0.25, 6.02, 2.68), "metal", "platform-light-housing")
rect((-0.60, 5.925, 2.37), (0.8, 0, 0), (0, 0, 0.26), "utility_lamp", "platform-light")

LIGHTS = [
    (np.array([8.7, 2.35, 13.63]), np.array([0.7, 0.10, 0.025]), "air"),
    (np.array([8.7, 2.3, 15.1]), np.array([10.0, 1.7, 0.28]), "air"),
    (np.array([7.78, -0.88, 9.2]), np.array([0.35, 11.25, 10.25]), "water"),
    (np.array([-0.2, 5.8, 2.5]), np.array([0.25, 0.80, 1.0]), "air"),
]
# Six samples distribute the ceiling tube's power over its length.
for x in np.linspace(3.8, 8.3, 6):
    pos = art.CAUSTIC_SOURCE.copy()
    pos[0] = x
    LIGHTS.append((pos, art.CAUSTIC_POWER / 6, "air"))

art.build_scene(sys.modules[__name__])
art.build_spotlight(sys.modules[__name__])
art.configure_pose(sys.modules[__name__])


def intersection(ro, rd, limit=None):
    """Exact nearest hits for planes, slabs, ellipsoids and capped cylinders."""
    count = len(rd)
    best = np.full(count, np.inf)
    ids = np.full(count, -1, dtype=np.int32)
    normals = np.zeros((count, 3))
    for j, o in enumerate(OBJECTS):
        kind = o["kind"]
        t = np.full(count, np.inf)
        if kind == "box":
            with np.errstate(divide="ignore", invalid="ignore"):
                t1 = (o["lo"] - ro) / rd
                t2 = (o["hi"] - ro) / rd
            near = np.minimum(t1, t2)
            far = np.maximum(t1, t2)
            enter = np.max(near, axis=1)
            leave = np.min(far, axis=1)
            t = np.where(enter > 1e-5, enter, leave)
            valid = (leave >= enter) & (t > 1e-5) & (t < best)
            k = np.where(valid)[0]
            if len(k):
                hit = ro[k] + t[k, None] * rd[k]
                ds = np.abs(np.concatenate([hit - o["lo"], hit - o["hi"]], axis=1))
                axis = np.argmin(ds, axis=1)
                n = np.zeros((len(k), 3))
                n[np.arange(len(k)), axis % 3] = np.where(axis < 3, -1, 1)
        elif kind == "rect":
            den = rd @ o["n"]
            num = (o["p"] - ro) @ o["n"]
            np.divide(num, den, out=t, where=np.abs(den) > 1e-10)
            k = np.where((t > 1e-5) & (t < best))[0]
            if len(k):
                rel = ro[k] + t[k, None] * rd[k] - o["p"]
                u = rel @ o["a"] / (o["a"] @ o["a"])
                v = rel @ o["b"] / (o["b"] @ o["b"])
                k = k[(u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)]
                n = np.broadcast_to(o["n"], (len(k), 3)).copy()
                n *= np.where((n * rd[k]).sum(axis=1) > 0, -1, 1)[:, None]
        elif kind == "ellipsoid":
            rotation = o.get("rotation", np.eye(3))
            oc = ((ro - o["p"]) @ rotation) / o["r"]
            dr = (rd @ rotation) / o["r"]
            aa = (dr * dr).sum(1)
            bb = (oc * dr).sum(1)
            cc = (oc * oc).sum(1) - 1
            disc = bb * bb - aa * cc
            root = np.sqrt(np.maximum(disc, 0))
            t = (-bb - root) / aa
            t = np.where(t > 1e-5, t, (-bb + root) / aa)
            k = np.where((disc >= 0) & (t > 1e-5) & (t < best))[0]
            local_hit = (ro[k] + t[k, None] * rd[k] - o["p"]) @ rotation
            n = norm((local_hit / o["r"] ** 2) @ rotation.T)
        else:
            ax = o["axis"]
            oc = ro - o["p"]
            da = rd @ ax
            oa = oc @ ax
            dp = rd - da[:, None] * ax
            op = oc - oa[:, None] * ax
            aa = (dp * dp).sum(1)
            bb = (dp * op).sum(1)
            cc = (op * op).sum(1) - o["r"] ** 2
            disc = bb * bb - aa * cc
            root = np.sqrt(np.maximum(disc, 0))
            with np.errstate(divide="ignore", invalid="ignore"):
                t0 = (-bb - root) / aa
                t1 = (-bb + root) / aa
            h0 = oa + t0 * da
            h1 = oa + t1 * da
            t = np.where((disc >= 0) & (t0 > 1e-5) & (h0 >= 0) & (h0 <= o["length"]), t0, np.inf)
            t = np.minimum(t, np.where((disc >= 0) & (t1 > 1e-5) & (h1 >= 0) & (h1 <= o["length"]), t1, np.inf))
            cap = np.zeros(count)
            for h, sign in [(0, -1), (o["length"], 1)]:
                tc = np.full(count, np.inf)
                np.divide(h - oa, da, out=tc, where=np.abs(da) > 1e-9)
                # The cap radial test also handles viewing a hollow-looking tiny rail end.
                rc = op + np.where(np.isfinite(tc), tc, 0)[:, None] * dp
                use = (tc > 1e-5) & (tc < t) & ((rc * rc).sum(1) <= o["r"] ** 2)
                t[use] = tc[use]
                cap[use] = sign
            k = np.where((t > 1e-5) & (t < best))[0]
            rel = ro[k] + t[k, None] * rd[k] - o["p"]
            n = norm(rel - (rel @ ax)[:, None] * ax)
            iscap = cap[k] != 0
            n[iscap] = cap[k][iscap, None] * ax
        if len(k):
            best[k] = t[k]
            ids[k] = j
            normals[k] = n
    if limit is not None:
        ids[best >= limit] = -1
    return best, ids, normals


def pattern(p, n, material, footprint):
    """Tile sizes, lane widths and surface wear are expressed in world metres."""
    base = np.broadcast_to(colour(MATS[material][0]), p.shape).copy()
    if material in ["wall", "deck", "pool", "coping"]:
        horizontal = np.abs(n[:, 1]) > 0.7
        a = np.where(horizontal, p[:, 0], np.where(np.abs(n[:, 2]) > 0.5, p[:, 0], p[:, 2]))
        b = np.where(horizontal, p[:, 2], p[:, 1])
        size = 0.25 if material == "wall" else (0.40 if material == "deck" else 0.2)
        joint = 0.010 if material in ["deck", "wall"] else 0.006

        # Integrate the periodic joint over a pixel footprint. Subpixel grout must
        # fade instead of aliasing into physically impossible random black marks.
        def integral(x):
            return np.floor(x / size) * joint + np.minimum(np.mod(x, size), joint)

        foot = np.maximum(footprint, 0.002)
        ca = (integral(a + foot * 0.5) - integral(a - foot * 0.5)) / foot
        cb = (integral(b + foot * 0.5) - integral(b - foot * 0.5)) / foot
        coverage = np.clip(ca + cb - ca * cb, 0, 1)
        contrast = {"wall": 0.0, "deck": 0.14, "pool": 0.14, "coping": 0.35}[material]
        base *= 1 - contrast * coverage[:, None]
        # Low-contrast wear collects by joints and the foot of vertical surfaces.
        cell = np.sin(np.floor(a * 17) * 17.13 + np.floor(b * 17) * 21.71)
        marks = (cell > 0.994) & (p[:, 1] < 0.15) & (material not in ["pool", "wall"])
        base[marks] *= 0.88
        if material == "wall":
            # The broad dark wall is deliberately quiet. Only its low painted dado
            # breaks the plane; floor and basin retain their metric tile joints.
            stripe = (p[:, 1] > 0.08) & (p[:, 1] < 0.22)
            base[stripe] = colour("bluegrey")
        if material == "pool":
            bottom = horizontal & (p[:, 1] < FLOOR + 0.05)
            lanes = (np.abs(p[:, 0] - 2) < 0.10) | (np.abs(p[:, 0] - 6) < 0.10)
            tees = ((p[:, 2] > 0.6) & (p[:, 2] < 0.76) | (p[:, 2] > 11.24) & (p[:, 2] < 11.4)) & (
                (np.abs(p[:, 0] - 2) < 0.65) | (np.abs(p[:, 0] - 6) < 0.65)
            )
            base[bottom & (lanes | tees)] = colour("deepwater") * 0.82
        if material == "deck":
            # Real slotted drain channels outside all four coping edges.
            edge = ((p[:, 0] > -0.36) & (p[:, 0] < -0.25) & (p[:, 2] >= 0) & (p[:, 2] <= 12)) | (
                (p[:, 0] > 8.25) & (p[:, 0] < 8.36) & (p[:, 2] >= 0) & (p[:, 2] <= 12)
            )
            ends = ((p[:, 2] > -0.36) & (p[:, 2] < -0.25) | (p[:, 2] > 12.25) & (p[:, 2] < 12.36)) & (p[:, 0] >= 0) & (p[:, 0] <= 8)
            slots = np.mod(np.where(edge, p[:, 2], p[:, 0]), 0.075) < 0.038
            base[(edge | ends) & slots] = colour("ink")
    elif material in ["concrete", "concrete_light"]:
        a = np.floor(p[:, 0] * 30)
        b = np.floor(p[:, 1] * 32)
        c = np.floor(p[:, 2] * 30)
        chip = (np.sin(a * 13.31 + b * 7.21 + c * 22.4) > 0.9993) & ((p[:, 1] < 0.3) | (np.abs(p[:, 1] - 3) < 0.15))
        base[chip] *= 0.73
    elif material == "glass":
        base[:] = colour("ink") * 0.6
    return art.material(p, n, material, footprint, base, sys.modules[__name__])


def shade(ro, rd, t, ids, n, shadows=True):
    out = np.broadcast_to(colour("ink") * 0.5, (len(rd), 3)).copy()
    good = ids >= 0
    k = np.where(good)[0]
    if not len(k):
        return out
    p = ro[k] + rd[k] * t[k, None]
    nn = n[k]
    ii = ids[k]
    alb = np.zeros_like(p)
    spec = np.zeros(len(k))
    emission = np.zeros_like(p)
    for j in np.unique(ii):
        m = ii == j
        mat = OBJECTS[int(j)]["mat"]
        footprint = np.linalg.norm(p[m] - EYE, axis=1) / FOCAL / np.maximum(np.abs((nn[m] * rd[k][m]).sum(1)), 0.22)
        alb[m] = pattern(p[m], nn[m], mat, footprint)
        spec[m] = MATS[mat][1]
        if mat == "lamp":
            emission[m] = np.array([0.84, 0.42, 0.154])
        if mat == "utility_lamp":
            emission[m] = np.array([3.0, 1.8, 1.1])
        if mat == "coldlamp":
            emission[m] = np.array([0.25, 1.8, 1.35])
        if mat == "wetlamp":
            emission[m] = np.array([0.19, 0.912, 0.722])
        if mat == "glass":
            emission[m] = np.array([0.007, 0.012, 0.017])
        if mat in art.EMISSIONS:
            emission[m] = art.EMISSIONS[mat]
    underwater = p[:, 1] < WATER - 0.015
    # A fixed ambient term approximates indirect room illumination. Direct
    # illumination below is distance-attenuated, normal-dependent and shadowed.
    ambient = art.ambient(p, nn, underwater)
    lum = alb * ambient
    if np.any(underwater):
        lum += alb * art.caustic_light(p, nn, sys.modules[__name__])
    for lp, power, medium in LIGHTS:
        v = lp - p
        dist = np.linalg.norm(v, axis=1)
        ld = v / np.maximum(dist[:, None], 1e-6)
        nd = np.maximum((ld * nn).sum(1), 0)
        eligible = (underwater if medium == "water" else ~underwater) & (nd > 0)
        active = np.where(eligible)[0]
        visibility = np.zeros(len(k))
        visibility[active] = 1
        if shadows and len(active):
            st, si, _ = intersection(p[active] + nn[active] * 0.0015, ld[active], dist[active] - 0.005)
            visibility[active] = si < 0
        irradiance = power[None, :] / np.maximum(dist[:, None] ** 2, 0.08)
        if medium == "water":
            irradiance *= np.exp(-dist[:, None] * ABSORPTION)
        lum += alb * irradiance * (nd * visibility)[:, None]
        half = norm(ld - rd[k])
        nh = np.maximum((half * nn).sum(1), 0)
        lum += irradiance * ((nh**60) * spec * visibility)[:, None] * 0.3
    # A near-field ambient contact term anchors furniture to the deck; the actual
    # direct shadows have already been intersected against the complete scene.
    lum += art.direct(p, nn, rd[k], alb, spec, sys.modules[__name__])
    lum += emission
    out[k] = lum
    return out


def wave(x, z):
    return art.wave(sys.modules[__name__], x, z)


def water_hit(ro, rd):
    t = np.full(len(rd), np.inf)
    np.divide(WATER - ro[:, 1], rd[:, 1], out=t, where=rd[:, 1] < -1e-8)
    valid = (t > 0) & np.isfinite(t)
    k = np.where(valid)[0]
    q = ro[k] + t[k, None] * rd[k]
    for _ in range(5):
        h, dx, dz = wave(q[:, 0], q[:, 2])
        f = q[:, 1] - h
        deriv = rd[k, 1] - dx * rd[k, 0] - dz * rd[k, 2]
        t[k] -= f / deriv
        q = ro[k] + t[k, None] * rd[k]
    h, dx, dz = wave(q[:, 0], q[:, 2])
    n = np.zeros_like(rd)
    n[k] = norm(np.stack([-dx, np.ones(len(k)), -dz], axis=1))
    bounded = (q[:, 0] > 0) & (q[:, 0] < 8) & (q[:, 2] > 0) & (q[:, 2] < 12) & (t[k] > 0)
    t[k[~bounded]] = np.inf
    return t, n


def optics(d, n):
    ci = np.clip(-(d * n).sum(1), 0, 1)
    eta = 1 / IOR
    ct = np.sqrt(np.maximum(0, 1 - eta**2 * (1 - ci**2)))
    reflected = d + 2 * ci[:, None] * n
    transmitted = eta * d + (eta * ci - ct)[:, None] * n
    rs = ((ci - IOR * ct) / (ci + IOR * ct)) ** 2
    rp = ((IOR * ci - ct) / (IOR * ci + ct)) ** 2
    return norm(reflected), norm(transmitted), (rs + rp) * 0.5


def render(save=True, verbose=True):
    start = time.time()
    ro, rd = camera_rays()
    t, ids, n = intersection(ro, rd)
    tw, nw = water_hit(ro, rd)
    water = tw < t
    solid = ~water
    rgb = np.zeros((W * H, 3))
    if verbose:
        print("Primary intersections:", round(time.time() - start, 2), flush=True)
    rgb[solid] = shade(ro[solid], rd[solid], t[solid], ids[solid], n[solid])
    wp = ro[water] + tw[water, None] * rd[water]
    rr, rt, f = optics(rd[water], nw[water])
    rro = wp + nw[water] * 0.002
    rto = wp - nw[water] * 0.002
    tr, ir, nr = intersection(rro, rr)
    tt, it, nt = intersection(rto, rt)
    if verbose:
        print("Optical intersections:", round(time.time() - start, 2), flush=True)
    reflection = shade(rro, rr, tr, ir, nr)
    transmission = shade(rto, rt, tt, it, nt)
    attenuation = np.exp(-np.minimum(tt, 60)[:, None] * ABSORPTION)
    transmission = transmission * attenuation + (1 - attenuation) * globals().get("WATER_SCATTER", np.array([0.004, 0.022, 0.026]))
    rgb[water] = f[:, None] * reflection + (1 - f[:, None]) * transmission
    rgb = art.atmosphere(ro, rd, np.minimum(t, tw), rgb, sys.modules[__name__])
    rgb = art.bloom(rgb, H, W)
    # Fixed exposure preserves source/light relationships. A global palette maps
    # each native pixel to one swatch. No image rescaling or antialiasing occurs.
    display = np.clip(srgb(rgb * 1.7), 0, 1)

    # Perceptual distance in OKLab avoids unrelated hue shifts in dark colours.
    def lab(c):
        l = linear(c)
        m1 = np.array(
            [
                [0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005],
            ]
        )
        m2 = np.array(
            [
                [0.2104542553, 0.793617785, -0.0040720468],
                [1.9779984951, -2.428592205, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.808675766],
            ]
        )
        return np.cbrt(l @ m1.T) @ m2.T

    px = lab(display)
    pal = lab(RGB)
    dist = ((px[:, None, :] - pal[None, :, :]) ** 2 * np.array([1.0, 1.5, 1.5])).sum(2)
    index = np.argmin(dist, axis=1).astype(np.uint8).reshape(H, W)
    image = Image.fromarray(index, "P")
    image.putpalette((RGB * 255 + 0.5).astype(np.uint8).ravel().tolist() + [0] * (768 - 3 * len(RGB)))
    image = art.pixel_finish(image, sys.modules[__name__], np.minimum(t, tw).reshape(H, W), np.where(water, -1, ids).reshape(H, W))
    image = art.finish(image, sys.modules[__name__], np.minimum(t, tw).reshape(H, W))
    if save:
        STILL_DIR.mkdir(parents=True, exist_ok=True)
        PALETTE_DIR.mkdir(parents=True, exist_ok=True)
        image.save(STILL_DIR / "after-hours-native.png", optimize=True)
        image.resize((W * 4, H * 4), Image.Resampling.NEAREST).save(STILL_DIR / "after-hours.png", optimize=True)
        (PALETTE_DIR / "palette.json").write_text(json.dumps(PAL, indent=2) + "\n")
        (PALETTE_DIR / "after-hours.gpl").write_text(
            "GIMP Palette\nName: After Hours\nColumns: 7\n#\n"
            + "".join(f"{int(r * 255 + 0.5):3} {int(g * 255 + 0.5):3} {int(b * 255 + 0.5):3} {name}\n" for name, (r, g, b) in zip(PAL, RGB))
        )
    if verbose:
        print("Finished:", round(time.time() - start, 2), "seconds;", len(image.getcolors()), "colours", flush=True)
    return image


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render the After Hours still and palette.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="new exports (default: build/exports/)")
    parser.add_argument("--build-dir", type=Path, default=BUILD_DIR, help="temporary files (default: build/)")
    args = parser.parse_args(argv)
    configure_paths(args.output_dir, args.build_dir)
    render()


if __name__ == "__main__":
    main()
