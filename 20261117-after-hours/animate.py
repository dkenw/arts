#!/usr/bin/env python3
# /// script
# requires-python = "==3.12.11"
# dependencies = ["numpy==2.3.5", "pillow==13.0.0"]
# ///
"""Render the eight-second, 25 fps loop with compiled ray acceleration.

Run: uv run animate.py --preview
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
import ctypes
import json
import math
import multiprocessing
import os
from pathlib import Path
import subprocess
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import after_hours as s

# Compile and load the native ray-intersection accelerator.

SOURCE = s.ROOT / "fast_rays.cpp"
os.environ.setdefault("OMP_NUM_THREADS", "3")


class Accelerator:
    def __init__(self, scene):
        source = SOURCE
        binary = s.NATIVE_DIR / "fast_rays.so"
        s.NATIVE_DIR.mkdir(parents=True, exist_ok=True)
        if not binary.exists() or binary.stat().st_mtime < source.stat().st_mtime:
            command = [os.environ.get("CXX", "g++"), "-std=c++17", "-O3", "-shared", "-fPIC"]
            result = subprocess.run(command + ["-fopenmp", str(source), "-o", str(binary)], capture_output=True)
            if result.returncode:
                # Apple Clang and some other compilers lack OpenMP; the same code also
                # runs serially. Frame-level multiprocessing still provides parallelism.
                subprocess.run(command + [str(source), "-o", str(binary)], check=True)
        self.library = ctypes.CDLL(str(binary))
        self.scene = scene
        self.scene_identity = None
        doubles = np.ctypeslib.ndpointer(dtype=np.float64, flags="C_CONTIGUOUS")
        ints = np.ctypeslib.ndpointer(dtype=np.int32, flags="C_CONTIGUOUS")
        self.library.load_scene.argtypes = [doubles, ctypes.c_int]
        self.library.trace.argtypes = [doubles, doubles, ctypes.c_int, doubles, ints, doubles]
        self.library.load_scene.restype = self.library.trace.restype = None
        self.reload()

    def reload(self):
        data = np.zeros((len(self.scene.OBJECTS), 32))
        for j, o in enumerate(self.scene.OBJECTS):
            v = data[j]
            kind = o["kind"]
            v[0] = ["box", "rect", "ellipsoid", "tube"].index(kind)
            v[14:23] = o.get("rotation", np.eye(3)).ravel()
            if kind == "box":
                v[1:4] = o["lo"]
                v[4:7] = o["hi"]
            elif kind == "rect":
                v[1:4] = o["p"]
                v[4:7] = o["a"]
                v[7:10] = o["b"]
                v[10:13] = o["n"]
            elif kind == "ellipsoid":
                v[1:4] = o["p"]
                v[4:7] = o["r"]
            else:
                v[1:4] = o["p"]
                v[4:7] = o["axis"]
                v[7] = o["r"]
                v[13] = o["length"]
        self.library.load_scene(data, len(data))
        self.scene_identity = id(self.scene.OBJECTS)

    def intersection(self, ro, rd, limit=None):
        if id(self.scene.OBJECTS) != self.scene_identity:
            self.reload()
        ro = np.ascontiguousarray(ro, dtype=np.float64)
        rd = np.ascontiguousarray(rd, dtype=np.float64)
        count = len(rd)
        t = np.empty(count)
        ids = np.empty(count, dtype=np.int32)
        n = np.empty((count, 3))
        self.library.trace(ro, rd, count, t, ids, n)
        if limit is not None:
            ids[t >= limit] = -1
        return t, ids, n


def install(scene):
    accelerator = Accelerator(scene)
    scene.intersection = accelerator.intersection
    return accelerator


# Animation, export and exact GIF round-trip checks.


LOOP = 8.0
FPS = 25
FRAMES = int(LOOP * FPS)
G = 9.81


def configure():
    s.LOOP_SECONDS = LOOP
    s.ANIMATION_TIME = 0.0
    return install(s)


def frame_at(t):
    s.ANIMATION_TIME = float(t) % LOOP
    s.art.CAUSTIC = None
    return s.render(save=False, verbose=False)


def contact_sheet(frames, output):
    sheet = Image.new("RGB", (384 * 3, 256 * 2 + 28 * 2), "#100e20")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=16)
    for j, index in enumerate([0, 33, 66, 100, 133, 166]):
        x = (j % 3) * 384
        y = (j // 3) * 284
        sheet.paste(frames[index].convert("RGB"), (x, y + 28))
        draw.text((x + 12, y + 6), f"{index / FPS:.2f} s", font=font, fill="#d5ffcf")
    sheet.save(output)


def exports(frames):
    s.ANIMATION_DIR.mkdir(parents=True, exist_ok=True)
    # Pillow preserves the authored global palette. GIF's 10 ms timing quantum
    # represents 25 fps exactly, avoiding uneven 30/40 ms frame durations.
    for scale, name in [(1, "after-hours-animated-native.gif"), (4, "after-hours-animated.gif")]:
        images = [im if scale == 1 else im.resize((s.W * scale, s.H * scale), Image.Resampling.NEAREST) for im in frames]
        images[0].save(s.ANIMATION_DIR / name, save_all=True, append_images=images[1:], duration=40, loop=0, optimize=True, disposal=1)
        print("Exported", name, flush=True)
    # Conventional H.264 MP4 is more widely playable on phones. The GIFs are
    # the exact-palette masters; this compatible video uses lossy YUV encoding.
    command = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{s.W}x{s.H}",
        "-r",
        str(FPS),
        "-i",
        "pipe:0",
        "-vf",
        "scale=1536:1024:flags=neighbor",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "16",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(s.ANIMATION_DIR / "after-hours-animated.mp4"),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    for im in frames:
        process.stdin.write(im.convert("RGB").tobytes())
    process.stdin.close()
    if process.wait():
        raise RuntimeError("MP4 encoding failed")
    contact_sheet(frames, s.ANIMATION_DIR / "animation-contact-sheet.png")
    frames[0].save(s.ANIMATION_DIR / "after-hours-animation-poster-native.png")
    frames[0].resize((s.W * 4, s.H * 4), Image.Resampling.NEAREST).save(s.ANIMATION_DIR / "after-hours-animation-poster.png")


def verify(frames, endpoint):
    arrays = np.stack([np.array(f) for f in frames])
    delta = np.mean(arrays != np.roll(arrays, 1, axis=0), axis=(1, 2))
    report = {
        "frames": len(frames),
        "frames_per_second": FPS,
        "seconds": LOOP,
        "native_dimensions": [s.W, s.H],
        "palette_entries": len(s.PAL),
        "unique_frames": len({f.tobytes() for f in frames}),
        "start_equals_endpoint": frames[0].tobytes() == endpoint.tobytes(),
        "wrap_changed_pixel_fraction": float(delta[0]),
        "internal_changed_pixel_fraction_min": float(delta[1:].min()),
        "internal_changed_pixel_fraction_max": float(delta[1:].max()),
        "wavelengths_metres": [G * LOOP**2 / (math.tau * n * n) for n in [9, 12, 7]],
        "motion": [
            "Gentler water waves, with recomputed intersections, normals, reflected and refracted rays.",
            "Recomputed forward caustic map through the moving surface.",
            "Slower periodic depth-tested rising cup steam.",
            "Sparse periodic depth-tested floating dust.",
        ],
        "limits": [
            "Analytic waves, not a full fluid solver.",
            "Three sample positions approximate the ceiling emitter.",
            "Caustics omit emitter-to-water visibility.",
            "Air scattering, indirect fill and bloom retain the art-directed approximations of the still.",
            "GIF preserves palette RGB values; the compatible MP4 uses lossy YUV encoding.",
        ],
    }
    assert report["unique_frames"] == FRAMES
    assert report["start_equals_endpoint"]
    assert all(f.getpalette() == frames[0].getpalette() for f in frames)
    assert delta[0] <= delta[1:].max() * 1.5
    for name, scale in [("after-hours-animated-native.gif", 1), ("after-hours-animated.gif", 4)]:
        gif = Image.open(s.ANIMATION_DIR / name)
        assert gif.n_frames == FRAMES and gif.info["loop"] == 0
        for i, f in enumerate(frames):
            gif.seek(i)
            assert gif.info["duration"] == 40
            expected = f.convert("RGB").resize((s.W * scale, s.H * scale), Image.Resampling.NEAREST)
            assert gif.convert("RGB").tobytes() == expected.tobytes(), (name, i)
    report["gif_round_trip_exact"] = True
    s.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (s.REPORT_DIR / "animation-checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


def render_index(i):
    im = frame_at(i / FPS)
    im.save(s.FRAME_DIR / f"frame-{i:03d}.png", optimize=False)
    return i


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render and export the After Hours loop.")
    parser.add_argument("--output-dir", type=Path, default=s.OUTPUT_DIR, help="new exports (default: build/exports/)")
    parser.add_argument("--build-dir", type=Path, default=s.BUILD_DIR, help="temporary frames and native binary (default: build/)")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--preview", action="store_true")
    modes.add_argument("--export-only", action="store_true")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    s.configure_paths(args.output_dir, args.build_dir)
    configure()
    work = s.FRAME_DIR
    work.mkdir(parents=True, exist_ok=True)
    if args.preview:
        start = time.time()
        for j, t in enumerate([0.0, 0.64, 1.28, 2.56, 4.0, 6.4]):
            im = frame_at(t)
            im.resize((s.W * 3, s.H * 3), Image.Resampling.NEAREST).save(work / f"preview-{j}.png")
            print(f"Preview {j}: {time.time() - start:.2f}s", flush=True)
        return
    frames = []
    start = time.time()
    if not args.export_only:
        os.environ["OMP_NUM_THREADS"] = "1"
        with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context("spawn"), initializer=configure) as pool:
            for i in pool.map(render_index, range(FRAMES)):
                if (i + 1) % 20 == 0 or i == 0:
                    print(f"Frame {i + 1}/{FRAMES}, {time.time() - start:.1f}s", flush=True)
    for i in range(FRAMES):
        frames.append(Image.open(work / f"frame-{i:03d}.png").copy())
    endpoint = frame_at(LOOP)
    exports(frames)
    verify(frames, endpoint)


if __name__ == "__main__":
    main()
