# Still Running

This project renders an empty photographic darkroom as a **still image** and a **14.4-second running-water loop**. In the loop, glints travel along the stream, ripples widen, a print drifts, the curtain moves, and dust passes through the light.

The renderers draw the photographs and labels, build the room and its furnishings in 3D, trace the light, and map the result to the 68-colour pixel palette. The animation reads the colour, depth, material IDs, and native PNG produced by the still renderer.

## Render both

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and a C++17 compiler available as `c++` (or set `CXX` to its executable). The tested setup uses Python 3.12. `uv` sets up the environment and installs the pinned dependencies. To produce the MP4, install FFmpeg with the `libx264` encoder on your PATH. A build with `zscale` provides the reference video colour conversion.

From this project directory on macOS or Linux, run

```sh
uv run --python 3.12 render.py
```

The finished files go into `renders/`. Intermediate photographs, compiled C++ programs, and ray-tracing data go into `build/`. Rendering is CPU-based. For the still alone, use `uv run render.py still`. Run `uv run render.py --help` to choose different output or working directories.

## Finished artwork

| File in `renders/` | Contents |
| --- | --- |
| [Still-Running-native.png](renders/Still-Running-native.png) | Native 528 × 304 indexed still |
| [Still-Running.png](renders/Still-Running.png) | 1584 × 912 nearest-neighbour enlargement |
| [Still-Running-flow-native.gif](renders/Still-Running-flow-native.gif) | 528 × 304 lossless loop, 360 frames at 25 fps |
| [Still-Running-flow.gif](renders/Still-Running-flow.gif) | 1056 × 608 pixel-art loop |
| [Still-Running-flow.mp4](renders/Still-Running-flow.mp4) | 1584 × 912 H.264 video with sRGB transfer and BT.709 primaries |
| [Still-Running-phone.webp](renders/Still-Running-phone.webp) | 330 × 190 whole-room mobile preview |
| [Still-Running-dust-detail.gif](renders/Still-Running-dust-detail.gif) | Enlarged detail of the curtain and light shafts |

## Where to edit

| Source | What it controls |
| --- | --- |
| `still/src/plates.py` and `still/src/platform_print.py` | Draw the photographs, contact sheet, lettering, clock face, and labels |
| `still/src/room.hpp`, `objects.hpp`, `details.hpp`, and `muffler.hpp` | Build the room, tap, enlarger, stool, scarf, and other geometry |
| `still/src/draw.cpp` and `still/src/color.py` | The still camera, lighting, ray tracing, and final indexed colours |
| `animation/scene/rinse.hpp` and `animation/scene/basinlight.hpp` | Falling water, expanding wave fronts, floating print, and light refracted onto the sink |
| `animation/cloth.cpp` and `animation/scene/draft.hpp` | The tied curtain, its folds, and its changing shadows |
| `animation/air.cpp` and `animation/scene/airvolume.hpp` | Moving dust and suspended fibres in the safelight and enlarger beam |
| `animation/animate.py` | Composites the exposures, grades each frame, and exports the loops |

The `still/` and `animation/` directories each contain the scene and shading code for their renderer. The still uses 144 camera samples per native pixel. The animation reuses the static room exposure and traces the moving regions separately. Further rendering details are in the README inside each directory.

## Rebuild the animation after editing it

Once the still has run at its native resolution, this command uses its generated scene buffers directly. Run it from the top-level project directory.

```sh
uv run animation/animate.py --master build/still --work build/animation --output renders
```

For changes to the palette or export code alone, add `--encode-only` to regrade a completed set of motion passes. The reference environment used Python 3.12.14, NumPy 2.3.5, Pillow 13.0.0, SciPy 1.17.0, GCC 14.2.0, and FFmpeg 7.1.5.
