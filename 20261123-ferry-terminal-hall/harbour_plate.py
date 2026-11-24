"""Register a harbour retake to the hall exposure and hold its window frames in the print."""

from pathlib import Path
import shutil

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

from capture_passes import GEOMETRY_GUIDES, HARBOUR_DEPTH, LARGE_PASSES, print_passes, require_passes
from output_files import staged_output


def capture(earlier, retake, destination, *, large):
    """Register an aligned harbour retake and publish its matching camera passes."""
    earlier, retake, destination = (Path(path).with_suffix(".png") for path in (earlier, retake, destination))
    if destination.resolve() in (earlier.resolve(), retake.resolve()):
        raise ValueError("Give the registered exposure a destination separate from both input captures.")
    channels = (("colour", ".png"),)
    if large:
        channels += GEOMETRY_GUIDES
    channel_passes = tuple(suffix for _, suffix in channels)
    harbour_passes = (*channel_passes, HARBOUR_DEPTH) if large else channel_passes
    required = print_passes(large=large)
    require_passes(earlier, (suffix for suffix in required if suffix != HARBOUR_DEPTH), "Hall capture")
    require_passes(retake, (*harbour_passes, ".aperture.npz"), "Harbour retake")

    # Switching to the original profile drops only the enlarged profile's passes.
    discard = [] if large else [destination.with_suffix(suffix).name for suffix in LARGE_PASSES]
    with staged_output(destination.parent, discard=discard, last=destination.name) as stage:
        registered = stage / destination.name
        _register(earlier, retake, registered, channels=channels)
        for suffix in required:
            if suffix not in channel_passes:
                source = retake if suffix == HARBOUR_DEPTH else earlier
                shutil.copyfile(source.with_suffix(suffix), registered.with_suffix(suffix))


def _register(earlier, retake, destination, *, channels):
    with np.load(retake.with_suffix(".aperture.npz")) as archive:
        aperture = archive["aperture"]
        if aperture.dtype != np.bool_ or aperture.ndim != 2 or not aperture.any():
            raise ValueError("A camera aperture mask is required.")
        coverage = archive["coverage"].astype(np.float32)/255 if "coverage" in archive else aperture.astype(np.float32)
        distant = archive["distant"].astype(np.float32)/255 if "distant" in archive else None
    if coverage.shape != aperture.shape or not coverage.any():
        raise ValueError("Window coverage must occupy the same camera grid as the aperture.")
    alpha = gaussian_filter(coverage, 0.47)
    ys, xs = np.nonzero(alpha > 0)
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    crop = np.s_[y0:y1, x0:x1]
    if distant is not None:
        if distant.shape != aperture.shape:
            raise ValueError("Distant coverage must be on the same camera grid.")
        alpha = gaussian_filter(coverage*distant, 0.47)
    alpha = alpha[crop][..., None]
    height, width = aperture.shape
    matte = {"size": (width, height), "origin": (x0, y0), "aperture": aperture[crop]}
    for key, suffix in channels:
        with Image.open(earlier.with_suffix(suffix)) as im:
            room = np.array(im.convert("RGB"))
        with Image.open(retake.with_suffix(suffix)) as im:
            harbour = np.asarray(im.convert("RGB"))
        if room.shape != (height, width, 3) or harbour.shape != room.shape:
            raise ValueError(f"{key} must use the same full camera grid as the aperture.")
        original = room[crop].copy()
        matte[key] = original
        local = original.astype(np.float32)
        blended = local + alpha * (harbour[crop].astype(np.float32) - local)
        room[crop] = np.uint8(np.clip(blended + 0.5, 0, 255))
        Image.fromarray(room).save(destination.with_suffix(suffix), optimize=True)
    # The raw reference under the ironwork belongs to the first hall exposure.
    # Repeated edits to the view outside must not compound the edge treatment.
    previous = earlier.with_suffix(".frame.npz")
    if previous.is_file():
        with np.load(previous) as stored:
            for key in ("size","origin","aperture"):
                if not np.array_equal(stored[key], matte[key]):
                    raise ValueError("The new take moves the earlier window frames.")
        shutil.copyfile(previous,destination.with_suffix(".frame.npz"))
    else:
        np.savez_compressed(destination.with_suffix(".frame.npz"), **matte)


def restore_frame_context(image, channel, matte):
    """Restore the sampling neighbourhood used to draw the opaque window frame."""
    width, height = map(int, matte["size"])
    x, y = map(int, matte["origin"])
    patch = matte[channel]
    if image.shape != (height, width, 3) or patch.shape[:2] != matte["aperture"].shape:
        raise ValueError("Frame context and camera exposure must be registered.")
    image[y:y+patch.shape[0], x:x+patch.shape[1]] = patch


def print_mask(matte, print_size):
    """A native print pixel can show the harbour if any camera sample sees outside."""
    width, height = map(int, matte["size"])
    w, h = print_size
    sx, sy = width // w, height // h
    if width != sx*w or height != sy*h or sx < 1 or sy < 1:
        raise ValueError("The print grid must divide the camera grid.")
    x, y = map(int, matte["origin"])
    patch = matte["aperture"]
    mask = np.zeros((height, width), dtype=bool)
    mask[y:y+patch.shape[0], x:x+patch.shape[1]] = patch
    native = mask.reshape(h,sy,w,sx).any(axis=(1,3))
    return Image.fromarray(native.astype(np.uint8)*255)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("earlier", type=Path)
    parser.add_argument("retake", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--profile", required=True, choices=("original","large"))
    args = parser.parse_args()
    try:
        capture(args.earlier, args.retake, args.destination, large=(args.profile == "large"))
    except ValueError as error:
        parser.error(str(error))
