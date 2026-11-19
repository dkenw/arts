# Still Running (still image)

An empty photographic darkroom. A thin stream from the tap breaks up the safelight's reflection beside a floating print. The enlarger and blackout curtain cast a cool shadow across the tiles beside the timer.

## Render the still

Install `uv` and a C++17 compiler as described in the [top-level README](../README.md#render-both). Run this command from the `still` directory. `uv` picks up the project environment from the parent directory.

```sh
uv run render.py --output prints
```

The default render draws 144 samples per pixel and writes two indexed PNGs. The native artwork is 528 × 304. The display print is a 3× nearest-neighbour enlargement at 1584 × 912. To make a quicker proof, use `uv run render.py --samples 9 --output proof`.

## How the light is drawn

The scene uses centimetres. The bench, enlarger, sink, curtain and stool share a camera and a system of ray-traced shadows.

- `src/rinse.hpp` describes the floating sheet, the shape of the water at its edge and the surface waves spreading from the tap. `src/basinlight.hpp` traces light through that surface onto the steel below.
- `src/draw.cpp` renders each light path. It samples a finite lens opening for the enlarger's light in the air. The drying photographs, the print in the bath and the negative in the enlarger are drawn by `src/plates.py` and `src/platform_print.py`.
- `src/color.py` sets the final exposure and assigns the pixel colours. Four colour ramps give the wall and cloth their distinct shadow shapes. The metal, the paper and the wool each have their own response to mixed light.
