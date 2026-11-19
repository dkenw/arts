# Still Running

An empty photographic darkroom. A thin stream meets the wash bath beside a floating fibre print. A current of air moves through the tied blackout curtain. Fibres catch the red safelight, then slip into shadow. Under the enlarger, suspended dust drifts through the light coming from the negative.

## Render

From the project root, `uv run render.py` builds the native still and saves its scene buffers in `build/still/` before rendering this loop. To render the animation again using those buffers, run the following from the `animation` directory.

```sh
uv run animate.py --master ../build/still --work ../build/animation --output ../renders
```

The loop runs for 14.4 seconds at 25 fps. The lossless native GIF is 528 × 304. The display GIF is a 2× integer enlargement. The silent H.264 video is 1584 × 912. The full-room phone preview is a lossless animated WebP at 330 × 190. It samples the finished frames in RGB. The curtain and dust detail is a 3× crop.

Use `--samples 4` for a quicker water proof. Set the number of render threads with `--threads 6`. Run `--encode-only` to regrade and export completed exposures.

## The tap and bath

The mean stream radius follows the taper in the still. Water leaves the lip with a small sideways velocity and accelerates as it falls. Capillary ridges travel down the column, turning rounded shoulders toward the safelight. Thin, flattened sections between the shoulders let the dark room show through. The changing cross section and reflections are drawn with the same camera as the sink.

Unequal groups of waves leave the landing point. Each front samples the inlet at its emission time, then travels out across the bath. Steeper crests carry the warm reflection past the loose print. Weaker returns from the steel walls cross it on the open side, while the shallow film over the paper damps the shorter waves.

The loose print follows a small, slow circulation in the sink. Its shift, slight yaw and heave drive the printed image, its curled edge, the water film and the light on the steel beneath it.

The water, the paper and the interior steel are traced through the same interfaces. The camera uses 25 samples per native pixel and 64 along the narrow jet. Two shutter samples capture the travel of the surface. The 7.2-second water cycle plays twice in the full loop.

## The curtain

Two unequal pulses of air reach the cloth at different times. The gathered upper panel has less travel than the hem. The heading and the tie stay anchored. The slack panel above the tie bows, while the lower hem swings and takes a little longer to settle. Warp and weft constraints preserve the yarn lengths as the gathers open on the bias. The seams, turnback and thread geometry are rebuilt on the posed fabric.

A paired exposure of the resting and moving panel captures the changing folds and the safelight shadow they cast across the tiles. The clearest contours use 144 camera samples per pixel. Close-spaced poses resolve the movement between native pixels.

## Light in the air

The projected beam uses the same direction and light level as in the still. The renderer integrates a changing dust density through it, clipped by the surfaces of the room. The negative and the finite lens determine which parts of the air can catch light. A few longer fibres turn through the red light and the smaller cool pool under the enlarger. Their camera and light paths are checked against the room geometry.

## Video colour

The indexed GIFs preserve the still’s palette. The MP4 stores the same display-referred colours using an sRGB transfer function, BT.709 primaries and the BT.709 YCbCr matrix in limited range. Both the H.264 stream and the MP4 container carry the colour description. An FFmpeg build with zscale gives the most accurate chroma conversion.

## Files

| File | Contents |
| --- | --- |
| `animate.py` | Render orchestration, fixed-palette grading, GIF and MP4 export |
| `flow.cpp` | Camera, shutter integration and scene acceleration |
| `cloth.cpp` | Deformed curtain geometry and paired camera exposures |
| `scene/draft.hpp` | Air pressure pulse and delayed fold response |
| `scene/clothplate.py` | Subpixel curtain coverage, shadows and pose interpolation |
| `air.cpp` | Dust paths, illumination, occlusion and subpixel light collection |
| `scene/camera.hpp` | Shared lens and composition |
| `scene/airplate.py` | Sparse exposures for the air and illuminated fibres |
| `scene/airvolume.hpp` | Aperture- and depth-limited volumetric light integration |
| `scene/rinse.hpp` | Filament, contact dimple, waves and print motion |
| `scene/basinlight.hpp` | Refracted safelight on the submerged steel |
| `scene/draw.cpp` | Lighting and ray-traced optics |
| `scene/color.py` | 68-colour palette and exposure |
| `../build/still/` | Generated still and its linear-light, depth, and material buffers |
| `mask.py` | Render footprint for the water, nearby reflected light and occluding edges |
