"""Shared setting-out dimensions for the clock and the waiting bays, in metres."""

import math

LANDING_EYE = (-5.38, -9.87, 5.28)
CLOCK = (-4.35, -2.08, 5.67)
GATE = (6.66, 16.05)
RING_CENTRE = (6.45, 5.3 - 0.36, 1.72)
# The back dial looks directly toward the boarding passage.
CLOCK_ANGLE = -math.atan2(GATE[0] - CLOCK[0], GATE[1] - CLOCK[1])


def dial(x, z, depth):
    cs, sn = math.cos(CLOCK_ANGLE), math.sin(CLOCK_ANGLE)
    return (
        CLOCK[0] + cs * x + sn * depth,
        CLOCK[1] + sn * x - cs * depth,
        CLOCK[2] + z,
    )


PITCH = 0.73
# Modules share an aisle edge. The wide bank nearer the counter has two faces.
AISLE_EDGE = 2.545
BANKS = [
    (AISLE_EDGE - 2.5 * PITCH, 0.08, 0, ("sea", "deep", None, "deep", "ochre")),
    (AISLE_EDGE - 2.5 * PITCH, 4.72, math.pi, ("deep", "sea", "sea", "lichen", "deep")),
    (AISLE_EDGE - 2.5 * PITCH, 5.79, 0, ("lichen", "sea", "deep", "deep", "sea")),
    (-6.62, 4.72, math.pi, ("sea", "deep", "deep", "lichen")),
    (-6.62, 5.79, 0, ("deep", "deep", "sea", "lichen")),
]
# The near bank has lost its return row. Its old feet follow the same drill pattern.
LIFTED = (AISLE_EDGE - 2.5 * PITCH, -0.99, math.pi, 5)


def feet(count):
    reach = count * PITCH / 2 - 0.31
    return (-reach, 0.0, reach) if count >= 5 else (-reach, reach)


def on_bank(cx, cy, heading, x, y):
    co, si = math.cos(heading), math.sin(heading)
    return (cx + co * x - si * y, cy + si * x + co * y)


# The windward transom, failed sill joint, and the shallow fan of runoff use
# a single setting-out point. The bay number counts from the entrance end.
OPEN_BAY = 7
SILL_JOINT = -18.56 + 2.92 * (OPEN_BAY + 1)
DRIP = (10.23, SILL_JOINT - 0.07, 0.46)


def floor_height(x):
    """The last 1.9 m of the window apron falls 12 mm toward the level hall."""
    return max(0.0, min(x - 8.52, 1.90)) * (0.012 / 1.90)


# Marks are authored flat, then placed back onto the masonry for selected
# single-pixel accents. UV coordinates here follow the top-down drawing.
BOAT_PANEL = (7.17, 8.32, 0.44, 0.86)
BOAT_LINES = (
    ((0.075, 0.49), (0.27, 0.51), (0.675, 0.47), (0.937, 0.38), (0.74, 0.74), (0.34, 0.79), (0.075, 0.49)),
    ((0.26, 0.51), (0.51, 0.13), (0.58, 0.48)),
    ((0.52, 0.14), (0.70, 0.43), (0.77, 0.44)),
    ((0.11, 0.51), (0.49, 0.68), (0.90, 0.41)),
)
BIN_CENTRE = (-2.32, 10.45)
BIN_HEADING = math.radians(-79)


def boat_point(u, v):
    near, far, low, high = BOAT_PANEL
    return (10.412, far - (far - near) * u, high - (high - low) * v)


def wick_height(distance):
    return (
        0.19
        + 0.13 * math.exp(-(((distance + 0.07) / 0.37) ** 2))
        + 0.026 * math.sin(distance * 22)
        + 0.037 * math.sin(distance * 8)
    )


# The two main folds are one third and two thirds across the opened sheet.
SHEET_X = (-0.189, -0.128, -0.063, 0.001, 0.063, 0.123, 0.182)
SHEET_NEAR = (0.0007, 0.013, 0.034, 0.012, 0.0012, 0.008, 0.019)
SHEET_FAR = (0.009, 0.022, 0.047, 0.020, 0.0014, 0.0010, 0.007)


def timetable_point(u, v):
    """Position on the printed face. The three rows match the meshed folds."""
    ux = max(0.0, min(1.0, u)) * 6
    i = min(int(ux), 5)
    k = ux - i
    x = SHEET_X[i] + (SHEET_X[i + 1] - SHEET_X[i]) * k
    right = k if i == 5 else 0
    edge = (1 - k if i == 0 else 0) + right
    near = SHEET_NEAR[i] + (SHEET_NEAR[i + 1] - SHEET_NEAR[i]) * k
    far = SHEET_FAR[i] + (SHEET_FAR[i + 1] - SHEET_FAR[i]) * k
    mid = (near + 0.48 * (far - near)) * (1 - 0.36 * edge)
    h = near + (mid - near) * (v / 0.48) if v < 0.48 else mid + (far - mid) * ((v - 0.48) / 0.52)
    x -= 0.011 * right * max(0, (v - 0.48) / 0.52)
    y = (v - 0.5) * 0.216 + 0.010 * right * max(0, 1 - v / 0.48)
    wx, wy = on_bank(-0.38, -2.12, -0.31, x, y)
    return (wx, wy, floor_height(wx) + h)


# Both the hanging mesh and its print use the same lower edge.
BLIND_Y = (4.84, 7.63)


def blind_hem(s, sine=math.sin):
    """Height of the blind's hem for a station between zero and one."""
    h = 5.43 + .35*s - .11*sine(s*4.8) - .08*sine(s*14)*s
    tail = (s-.77)/.23
    lifted = .5*(tail+abs(tail))
    return h + .17*sine(lifted*math.pi)
