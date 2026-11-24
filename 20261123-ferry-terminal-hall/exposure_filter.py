"""Filter the high-resolution exposures using surface colour and orientation as edge guides."""

import numpy as np
from scipy import ndimage as ndi


def luma(rgb):
    return rgb @ np.array([0.23, 0.65, 0.12], dtype=np.float32)


def filter_tile(rgb, normal, albedo):
    # Neighbourhoods grow in three short steps. A mark in the printed dial or
    # an edge between steel and sky stays separate even if both have the same value.
    guide = ndi.gaussian_filter(ndi.median_filter(luma(rgb), 3), 0.65)
    current = rgb
    for step, value_width, amount in ((1, 8.0, 0.98), (2, 6.6, 0.88), (4, 5.0, 0.63)):
        h, w = guide.shape
        cur = np.pad(current, ((step, step), (step, step), (0, 0)), mode="edge")
        guide_pad = np.pad(guide, step, mode="edge")
        normal_pad = np.pad(normal, ((step, step), (step, step), (0, 0)), mode="edge")
        albedo_pad = np.pad(albedo, ((step, step), (step, step), (0, 0)), mode="edge")
        total = np.ones_like(guide)
        summed = current.copy()
        for dy, dx in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
            ys, xs = (dy+1)*step, (dx+1)*step
            area = np.s_[ys:ys+h, xs:xs+w]
            gap = guide_pad[area] - guide
            dn = normal_pad[area] - normal
            da = albedo_pad[area] - albedo
            squared = (gap/value_width)**2 + np.einsum("ijk,ijk->ij",dn,dn)/14.5**2
            squared += np.einsum("ijk,ijk->ij",da,da)/13.0**2
            weight = np.exp(-0.5*squared) * (0.65 if dx and dy else 1.0)
            total += weight
            summed += cur[area] * weight[...,None]
        averaged = summed / total[...,None]
        current = current + amount * (averaged - current)
    return current


def clean(rgb, normal, albedo):
    """Overlap strips beyond the support of all three steps to avoid joins."""
    result = np.empty_like(rgb)
    h = rgb.shape[0]
    for top in range(0, h, 192):
        bottom = min(h, top + 192)
        a, b = max(0, top - 16), min(h, bottom + 16)
        patch = filter_tile(rgb[a:b], normal[a:b], albedo[a:b])
        result[top:bottom] = patch[top-a:bottom-a]
    return result
