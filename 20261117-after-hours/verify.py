#!/usr/bin/env python3
# /// script
# requires-python = "==3.12.11"
# dependencies = ["numpy==2.3.5", "pillow==13.0.0"]
# ///
"""Independent checksum, scene-geometry, optics and animation checks.

Run: uv run verify.py [all|checksums|scene|animation]
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import after_hours as s


def check_checksums():
    manifest = s.OUTPUT_DIR / "SHA256SUMS"
    failures = []
    count = 0
    for line in manifest.read_text().splitlines():
        if not line.strip():
            continue
        expected, name = line.split(maxsplit=1)
        path = s.OUTPUT_DIR / name
        if not path.is_file():
            failures.append(f"Missing: {name}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(f"Changed: {name}")
        count += 1
    if failures:
        raise SystemExit("\n".join(failures))
    if not count:
        raise SystemExit(f"Empty artifact manifest: {manifest}")
    print(f"All {count} preserved artifact checksums match.")


def check_scene():
    s.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    checks = {}

    def record(name, value, passed):
        checks[name] = {"value": value, "passed": bool(passed)}
        assert passed, (name, value)

    # Projecting rays back to their originating pixel checks camera consistency.
    ro, rd = s.camera_rays()
    p = ro + rd * np.linspace(3, 25, len(rd))[:, None]
    y, x = np.mgrid[0 : s.H, 0 : s.W]
    expected = np.stack([x.ravel() + 0.5, y.ravel() + 0.5], axis=1)
    err = float(np.max(np.abs(s.project(p) - expected)))
    record("camera_round_trip_max_error_pixels", err, err < 1e-10)

    def vp(axis):
        a = np.array(axis, float)
        return np.array([s.CX + s.FOCAL * (a @ s.RIGHT) / (a @ s.FORWARD), s.CY - s.FOCAL * (a @ s.UP) / (a @ s.FORWARD)])

    vpx, vpz, vpy = vp([1, 0, 0]), vp([0, 0, 1]), vp([0, 1, 0])

    def dist_vp(start, end, v):
        a, b = s.project([start, end])
        line = np.cross([*a, 1], [*b, 1])
        return abs(line @ [*v, 1]) / np.linalg.norm(line[:2])

    parallel = []
    for y, z in [(0, 12), (0, -0.18), (s.FLOOR, 8), (2.75, 1.8), (3.0, 3.2), (3.0, 14)]:
        parallel.append(dist_vp([0, y, z], [8, y, z], vpx))
    for x, y in [(0, 0), (8, 0), (-0.3, 0), (2, s.FLOOR), (6, s.FLOOR)]:
        parallel.append(dist_vp([x, y, 0], [x, y, 12], vpz))
    record("shared_vanishing_point_max_line_error_pixels", float(max(parallel)), max(parallel) < 1e-8)
    orth = float(np.dot(vpx - [s.CX, s.CY], vpz - [s.CX, s.CY]) + s.FOCAL**2)
    record("orthogonal_world_axes_projection_residual", orth, abs(orth) < 1e-7)

    # Degenerate primitives and non-orthogonal rectangle parameterisations would
    # break the renderer, so check the complete constructed scene, not a mock.
    valid = True
    for o in s.OBJECTS:
        if o["kind"] == "box":
            valid &= bool(np.all(o["hi"] > o["lo"]))
        elif o["kind"] == "tube":
            valid &= o["length"] > 1e-8 and abs(np.linalg.norm(o["axis"]) - 1) < 1e-10 and o["r"] > 0
        elif o["kind"] == "ellipsoid":
            rot = o.get("rotation", np.eye(3))
            valid &= bool(np.all(o["r"] > 0)) and np.max(np.abs(rot @ rot.T - np.eye(3))) < 1e-12
        else:
            valid &= abs(o["a"] @ o["b"]) < 1e-10 and abs(np.linalg.norm(o["n"]) - 1) < 1e-10
    record("all_scene_primitives_valid", len(s.OBJECTS), valid)

    # Check the first surface hit by the spotlight's central ray.
    spot_distance, spot_id, _ = s.intersection(s.art.SOURCE[None, :], s.art.AXIS[None, :])
    spot_target = s.OBJECTS[int(spot_id[0])]["label"] if spot_id[0] >= 0 else None
    record("spotlight_axis_first_hit_is_figure", spot_target, spot_target in ["torso", "head", "upper-arm", "cap-crown"])

    # The platform is supported, the pelvis contacts its top, and the legs hang
    # beyond its open end. Hidden ladder geometry remains grounded in the scene.
    platform = next(o for o in s.OBJECTS if o["label"] == "diving-platform")
    pier = next(o for o in s.OBJECTS if o["label"] == "platform-pier")
    record("platform_support_contact_gap_metres", float(platform["lo"][1] - pier["hi"][1]), abs(platform["lo"][1] - pier["hi"][1]) < 1e-10)
    hips = next(o for o in s.OBJECTS if o["label"] == "hips")
    gap = abs(hips["p"][1] - hips["r"][1] - platform["hi"][1])
    record(
        "seated_pelvis_platform_contact_gap_metres",
        float(gap),
        gap < 1e-10 and platform["lo"][0] < hips["p"][0] < platform["hi"][0] and platform["lo"][2] < hips["p"][2] < platform["hi"][2],
    )
    shoes = [o for o in s.OBJECTS if o["label"] == "shoe"]
    clearance = min(o["p"][0] - np.linalg.norm(o["rotation"][0] * o["r"]) - platform["hi"][0] for o in shoes)
    record(
        "dangling_feet_clear_platform_end_metres",
        float(clearance),
        clearance > 0 and all(s.WATER < o["p"][1] < platform["hi"][1] for o in shoes),
    )

    # Test the new oriented ellipsoid code against independently constructed
    # surface points and outward normals, rather than just checking its matrix.
    head = next(o for o in s.OBJECTS if o["label"] == "head")
    rng = np.random.default_rng(827)
    unit = s.norm(rng.normal(size=(48, 3)))
    surface = head["p"] + (unit * head["r"]) @ head["rotation"].T
    outward = s.norm((unit / head["r"]) @ head["rotation"].T)
    scene = s.OBJECTS
    try:
        s.OBJECTS = [head]
        distances, hit_ids, normals = s.intersection(surface + outward, -outward)
    finally:
        s.OBJECTS = scene
    ellipsoid_error = float(max(np.max(np.abs(distances - 1)), np.max(np.abs(normals - outward))))
    record("oriented_ellipsoid_hit_and_normal_max_error", ellipsoid_error, ellipsoid_error < 1e-10 and np.all(hit_ids == 0))
    treads = [o for o in s.OBJECTS if o["label"] == "ladder-tread"]
    ys = sorted((o["lo"][1] + o["hi"][1]) / 2 for o in treads)
    spacing = float(np.max(np.abs(np.diff(ys) - 0.3)))
    record("ladder_tread_spacing_max_error_metres", spacing, spacing < 1e-10)
    record(
        "ladder_treads_within_pool",
        len(treads),
        all(o["lo"][0] > 0 and o["hi"][0] < 8 and o["lo"][2] > 0 and o["hi"][2] < 12 for o in treads),
    )
    anchors = [o for o in s.OBJECTS if o["label"] == "ladder-anchor"]
    record("ladder_anchors_on_dry_deck", len(anchors), all(o["lo"][1] == 0 and o["hi"][2] < 0 for o in anchors))

    # Exact dielectric formula is tested separately from rendering.
    angles = np.deg2rad(np.arange(0, 86))
    incident = np.stack([np.sin(angles), -np.cos(angles), np.zeros_like(angles)], axis=1)
    normal = np.broadcast_to([0.0, 1.0, 0.0], incident.shape)
    refl, refr, F = s.optics(incident, normal)
    snell = float(np.max(np.abs(np.sin(angles) - s.IOR * np.linalg.norm(refr[:, [0, 2]], axis=1))))
    record("snell_law_max_residual", snell, snell < 1e-12)
    reflect = float(np.max(np.abs(refl[:, 1] - np.cos(angles))))
    record("equal_reflection_angle_max_cosine_error", reflect, reflect < 1e-12)
    unit = float(np.max(np.abs(np.linalg.norm(refr, axis=1) - 1)))
    record("refracted_ray_unit_length_error", unit, unit < 1e-12)
    f0 = ((1 - s.IOR) / (1 + s.IOR)) ** 2
    record("normal_incidence_water_reflectance", float(F[0]), abs(F[0] - f0) < 1e-12 and np.all((F >= 0) & (F <= 1)))

    # A flat-water reflected lamp must agree with the virtual-image construction.
    source = np.array([8.7, 2.385, 13.755])
    mirror = source.copy()
    mirror[1] = 2 * s.WATER - source[1]
    alpha = (s.WATER - s.EYE[1]) / (mirror[1] - s.EYE[1])
    contact = s.EYE + alpha * (mirror - s.EYE)
    d = s.norm(contact - s.EYE)[None, :]
    r, _, _ = s.optics(d, np.array([[0.0, 1.0, 0.0]]))
    mirror_error = float(np.max(np.abs(r[0] - s.norm(source - contact))))
    record("flat_reflection_vs_mirrored_source_direction_error", mirror_error, mirror_error < 1e-12)

    tw, nw = s.water_hit(ro, rd)
    good = np.isfinite(tw)
    wp = ro[good] + tw[good, None] * rd[good]
    height, dx, dz = s.wave(wp[:, 0], wp[:, 2])
    wave_error = float(np.max(np.abs(wp[:, 1] - height)))
    record("ray_wave_surface_max_intersection_error_metres", wave_error, wave_error < 1e-7)
    eps = 1e-5
    dh = (s.wave(wp[:, 0] + eps, wp[:, 2])[0] - s.wave(wp[:, 0] - eps, wp[:, 2])[0]) / (2 * eps)
    normal_error = float(np.max(np.abs(dh - dx)))
    record("wave_gradient_finite_difference_error", normal_error, normal_error < 1e-7)

    # Check finiteness and the flux budget of the forward caustic map.
    s.art.caustic_light(np.array([[4.0, s.FLOOR, 6.0]]), np.array([[0.0, 1.0, 0.0]]), s)
    caustic_stats = s.art.CAUSTIC_STATS
    record(
        "caustic_map_finite_nonnegative",
        caustic_stats["peak_irradiance"],
        caustic_stats["finite_nonnegative"] and caustic_stats["peak_irradiance"] > 0,
    )
    flux_ratio = float(np.max(np.array(caustic_stats["floor_flux_rgb"]) / np.array(caustic_stats["transmitted_flux_rgb"])))
    record("caustic_floor_to_transmitted_flux_max_ratio", flux_ratio, 0 < flux_ratio <= 1 + 1e-12)

    native = Image.open(s.STILL_DIR / "after-hours-native.png")
    large = Image.open(s.STILL_DIR / "after-hours.png")
    record("native_resolution_pixels", list(native.size), native.size == (384, 256))
    record("used_palette_colours", len(native.getcolors()), len(native.getcolors()) <= 28)
    record("preview_exact_nearest_neighbour", True, native.resize(large.size, Image.Resampling.NEAREST).tobytes() == large.tobytes())
    rendered = s.render(save=False, verbose=False)
    identical = rendered.convert("RGB").tobytes() == native.convert("RGB").tobytes()
    record("rendered_still_matches_preserved_pixels", identical, identical)

    info = {
        "camera": {
            "eye_metres": s.EYE.tolist(),
            "target_metres": s.TARGET.tolist(),
            "horizontal_fov_degrees": s.FOV,
            "focal_length_pixels": s.FOCAL,
            "principal_point_pixels": [s.CX, s.CY],
        },
        "vanishing_points_pixels": {"X": vpx.tolist(), "Y": vpy.tolist(), "Z": vpz.tolist()},
        "dimensions_metres": {
            "pool": [8, 12],
            "water_depth_mean": s.WATER - s.FLOOR,
            "deck_to_water_drop": -s.WATER,
            "door_opening": [1, 2.1],
            "platform_height": 3.0,
            "figure_cap_height_above_platform": max(
                o["p"][1] + np.linalg.norm(o.get("rotation", np.eye(3))[1] * o["r"])
                for o in s.OBJECTS
                if o["label"] in ["cap-crown", "cap-brim"]
            )
            - 3.0,
            "ladder_rail_spacing": 0.60,
            "ladder_tread_spacing": 0.30,
        },
        "flat_lamp_reflection_water_contact_metres": contact.tolist(),
        "caustic_map": caustic_stats,
        "spotlight": {
            "source_metres": s.art.SOURCE.tolist(),
            "aim_metres": s.art.AIM.tolist(),
            "inner_half_angle_degrees": math.degrees(math.acos(s.art.INNER)),
            "outer_half_angle_degrees": math.degrees(math.acos(s.art.OUTER)),
            "first_hit": spot_target,
        },
        "checks": checks,
        "limitations": [
            "Fixed-palette pixel stylisation, not photometric calibration.",
            "Ambient term approximates diffuse indirect light, including cool pool fill.",
            "Finite fixtures are approximated by point lights for direct illumination.",
            "Water uses analytic waves and one reflected/refracted secondary ray per pixel.",
            "The caustic map samples three points on the tube and omits visibility between the emitter and water.",
            "Air uses 40-step single scattering with a 192-pixel shadow map and an artistic scattering gain.",
            "Native-grid bloom is an artistic finishing effect.",
            "No full global illumination or volumetric multiple scattering.",
            "Selective pixel contours, dust and steam are authored finishing touches anchored to projected geometry.",
            "Clearances are a plausible illustration layout, not a certified pool design.",
        ],
    }
    (s.REPORT_DIR / "geometry-checks.json").write_text(json.dumps(info, indent=2) + "\n")
    print(json.dumps(info, indent=2))

    # A review sheet: artwork plus a metric plan and the common projected axes.
    sheet = Image.new("RGB", (1160, 760), "#151924")
    draw = ImageDraw.Draw(sheet)
    fontpath = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        title = ImageFont.truetype(fontpath, 26)
        font = ImageFont.truetype(fontpath, 17)
        small = ImageFont.truetype(fontpath, 14)
    except OSError:
        title = font = small = ImageFont.load_default()
    draw.text((28, 20), "AFTER HOURS / GEOMETRY REVIEW", font=title, fill="#d0dac0")
    draw.text((28, 60), "One camera, metre-scale objects, shared reflection and refraction geometry", font=font, fill="#97aaa5")
    art = native.convert("RGB").resize((768, 512), Image.Resampling.NEAREST)
    ad = ImageDraw.Draw(art)

    def sp(p):
        return tuple(s.project(p) * 2)

    for a, b in [((0, 0.05, 0), (0, 0.05, 12)), ((8, 0.05, 0), (8, 0.05, 12))]:
        ad.line([sp(a), sp(b)], fill="#a5c9af", width=2)
    for a, b in [((0, 0.05, 12), (8, 0.05, 12)), ((0, 3, 14), (12, 3, 14))]:
        ad.line([sp(a), sp(b)], fill="#e5ae79", width=2)
    horizony = vpz[1] * 2
    if 0 <= horizony < 512:
        ad.line([(0, horizony), (768, horizony)], fill="#886b80", width=1)
        ad.text((6, horizony - 21), "HORIZON", font=small, fill="#a38794")
    sheet.paste(art, (28, 106))
    draw.text((824, 108), "METRIC FLOOR PLAN", font=font, fill="#d0dac0")

    def plan(x, z):
        return (850 + (x + 3) * 17, 165 + (14 - z) * 20)

    draw.rectangle([plan(-3, 14), plan(12, -4)], outline="#886b80", width=2)
    draw.rectangle([plan(0, 12), plan(8, 0)], fill="#17343d", outline="#73a99a", width=2)
    draw.text(plan(0.7, 7), "8 m x 12 m", font=small, fill="#a5c9af")
    draw.line([plan(8.2, 14), plan(9.2, 14)], fill="#e5ae79", width=5)
    draw.rectangle([plan(-3, 3.2), plan(2.2, 1.8)], fill="#6d536b")
    for xx in s.LADDER_X:
        draw.line([plan(xx, 0.32), plan(xx, -0.46)], fill="#97aaa5", width=3)
    cx, cy = plan(s.EYE[0], s.EYE[2])
    draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill="#e5ae79")
    draw.line([(cx, cy), plan(s.TARGET[0], s.TARGET[2])], fill="#e5ae79", width=1)
    fx, fy = plan(s.hx, s.hz)
    draw.ellipse((fx - 4, fy - 4, fx + 4, fy + 4), fill="#bf655f")
    draw.text((824, 550), "Door: 1.00 x 2.10 m", font=font, fill="#d0dac0")
    draw.text((824, 580), "Platform top: 3.00 m", font=font, fill="#d0dac0")
    draw.text((824, 610), "Water depth: 3.80 m", font=font, fill="#d0dac0")
    draw.text((824, 640), "Pelvis touches platform", font=font, fill="#d0dac0")
    draw.text((824, 670), "Feet clear the open end", font=font, fill="#d0dac0")
    draw.text((28, 640), "The common horizon lies above this tighter crop.", font=small, fill="#97aaa5")
    draw.text(
        (28, 700),
        f"{len(checks)} numerical checks passed. Perspective lines are overlays, not part of the artwork.",
        font=font,
        fill="#a5c9af",
    )
    draw.text(
        (28, 730),
        "Lighting is deliberately stylised; optical checks cover the stated ray model, not full light transport.",
        font=small,
        fill="#97aaa5",
    )
    sheet.save(s.REPORT_DIR / "geometry-review.png")


def check_animation():
    import animate as animation

    s.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(352)
    reference = s.intersection
    accelerator = animation.Accelerator(s)
    ro, rd = s.camera_rays()
    idx = rng.choice(len(ro), 4096, replace=False)
    origins = np.concatenate([ro[idx], rng.uniform([-2.8, -3.8, -3.8], [11.8, 6.2, 13.8], (4096, 3))])
    directions = np.concatenate([rd[idx], s.norm(rng.normal(size=(4096, 3)))])
    t, ids, n = reference(origins, directions)
    ta, ia, na = accelerator.intersection(origins, directions)
    hit = (ids >= 0) & (ia >= 0)
    depth_error = float(np.max(abs(t[hit] - ta[hit])))
    normal_error = float(np.max(abs(n[hit] - na[hit])))
    assert np.array_equal(ids, ia)
    assert depth_error < 1e-8 and normal_error < 1e-8
    limits = rng.uniform(0.2, 8, len(ids))
    _, limited, _ = accelerator.intersection(origins, directions, limits)
    assert np.array_equal(limited, np.where(t >= limits, -1, ids))

    animation.configure()
    heights = []
    max_residual = 0.0
    max_gradient_error = 0.0
    for moment in [0.0, 1.3, 4.8, animation.LOOP]:
        s.ANIMATION_TIME = moment
        tw, _ = s.water_hit(ro[idx], rd[idx])
        valid = np.isfinite(tw)
        p = ro[idx][valid] + tw[valid, None] * rd[idx][valid]
        h, dx, dz = s.wave(p[:, 0], p[:, 2])
        heights.append(h)
        max_residual = max(max_residual, float(np.max(abs(p[:, 1] - h))))
        eps = 1e-5
        finite = (s.wave(p[:, 0] + eps, p[:, 2])[0] - s.wave(p[:, 0] - eps, p[:, 2])[0]) / (2 * eps)
        max_gradient_error = max(max_gradient_error, float(np.max(abs(finite - dx))))
    assert max_residual < 1e-7 and max_gradient_error < 1e-7
    assert np.array_equal(heights[0], heights[-1])
    first = animation.frame_at(0)
    endpoint = animation.frame_at(animation.LOOP)
    assert first.tobytes() == endpoint.tobytes()

    gif = Image.open(s.ANIMATION_DIR / "after-hours-animated-native.gif")
    assert gif.size == (384, 256) and gif.n_frames == animation.FRAMES and gif.info["loop"] == 0
    samples = [0, 16, 32, 64, 100, 160]
    duration = 0
    pal = {tuple(c) for c in (s.RGB * 255 + 0.5).astype(np.uint8)}
    for i in range(gif.n_frames):
        gif.seek(i)
        duration += gif.info["duration"]
        assert gif.info["duration"] == 40
        rgb = np.array(gif.convert("RGB"))
        if i in samples:
            rendered = first if i == 0 else animation.frame_at(i / animation.FPS)
            assert rgb.tobytes() == rendered.convert("RGB").tobytes(), ("rendered frame differs", i)
        assert {tuple(c) for c in np.unique(rgb.reshape(-1, 3), axis=0)} <= pal
    assert duration == int(animation.LOOP * 1000)
    gif.seek(0)
    assert gif.convert("RGB").tobytes() == first.convert("RGB").tobytes()
    data = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,nb_frames,r_frame_rate,duration",
                "-of",
                "json",
                str(s.ANIMATION_DIR / "after-hours-animated.mp4"),
            ]
        )
    )["streams"][0]
    assert data["width"] == 1536 and data["height"] == 1024
    assert int(data["nb_frames"]) == animation.FRAMES and data["r_frame_rate"] == "25/1"
    assert abs(float(data["duration"]) - animation.LOOP) < 1e-6
    report = {
        "accelerator_rays_compared": len(ids),
        "all_hit_ids_match": True,
        "depth_error_metres": depth_error,
        "normal_error": normal_error,
        "animated_wave_intersection_error_metres": max_residual,
        "animated_wave_gradient_error": max_gradient_error,
        "loop_end_image_identical_to_start": True,
        "gif_all_frames_in_authored_palette": True,
        "gif_duration_ms": duration,
        "rendered_sample_frame_indices": samples,
        "video": data,
    }
    (s.REPORT_DIR / "animation-geometry-checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify the preserved After Hours exports and renderer.")
    parser.add_argument("target", nargs="?", default="all", choices=["all", "checksums", "scene", "animation"])
    parser.add_argument("--output-dir", type=Path, default=s.ROOT / "artifacts", help="reference exports (default: artifacts/)")
    parser.add_argument("--build-dir", type=Path, default=s.BUILD_DIR, help="new reports and native binary (default: build/)")
    args = parser.parse_args(argv)
    s.configure_paths(args.output_dir, args.build_dir)
    if args.target == "all":
        # Give each check a fresh scene; animation replaces its intersection
        # function and changes the time and lighting caches.
        for target in ["checksums", "scene", "animation"]:
            subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), target, "--output-dir", str(s.OUTPUT_DIR), "--build-dir", str(s.BUILD_DIR)],
                check=True,
            )
    else:
        {"checksums": check_checksums, "scene": check_scene, "animation": check_animation}[args.target]()


if __name__ == "__main__":
    main()
