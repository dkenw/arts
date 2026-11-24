# No Further Sailings · Edition 19

*Salt Lines, revised*

It is quarter to five at Berth 04. The boarding ramp descends from the empty hall to a floating landing. Across the basin, a crane hangs over the quay where it can reach a ship alongside. The ship-repair shop, grain bins and old waterfront warehouses give way to several streets of mid-rise buildings. Rain softens the farther roofs.

| Core print | Native dimensions | Finish |
| --- | --- | --- |
| Original | 528 × 396 | 80-colour pixel drawing |
| Enlarged | 2112 × 1584 | The same 80-colour palette |
| Continuous tone | 2112 × 1584 | RGB |

The three PNGs in [`renders/`](renders/) are the current Edition 19 artwork, rendered from the scene in this repository with Blender 5.2.1. The large finishes share an exposure. The 528 × 396 drawing has its own exposure. All three use the same hall, camera and morning light.

## Render the current edition

Install Blender 5.2 LTS and run the following from the repository root. uv uses Python 3.12 and installs the versions recorded in `uv.lock`.

~~~sh
uv run --locked python render.py
~~~

The command takes fresh camera captures in Blender, saves the working files in `build/`, and replaces the corresponding PNGs in `renders/`. Use `--profile original` for the 528-pixel drawing or `--profile large` for both enlarged prints. Add `--proof` for a lower-sample render in `build/proof/`, where the enlarged finishes are 1056 × 792. Use `--output PATH` to choose another destination. Use `--threads` to set the Blender CPU thread count or `--blender` to select the executable.

## Original Edition 19 archive

The [archive](archive/) holds the original published Edition 19 prints and their Blender 4.3.2 camera captures.

Run `uv run --locked python render.py --from-exposures` to develop the archived camera passes into `build/archive-reprint/`. PNG compression and pixel rounding can vary across platforms.

## Retake the harbour

To change the harbour while keeping the same hall and window frames, trace the exterior alone and register it to a full capture of the same scene. This example uses the archived hall to make a new 528-pixel print.

~~~sh
mkdir -p build/retake
uv run --locked python -c "from paint import make; make('build/retake/maps')"
blender -b --python-exit-code 1 -P terminal.py -- --profile original --maps build/retake/maps --output build/retake/harbour.png --width 1056 --samples 560 --exterior-only --far-shore
uv run --locked python harbour_plate.py archive/exposures/original/exposure.png build/retake/harbour.png build/retake/registered/exposure.png --profile original
uv run --locked python pixel.py build/retake/registered/exposure.png build/retake/prints --profile original
~~~

For a large retake, use a second output directory, generate its maps with `make(path, large=True)`, select profile `large` and use a width of 2112 pixels and 224 maximum samples. The large exterior take also records the distances for the revised scene. Register to `archive/exposures/large/exposure.png`. Develop the result with `pixel.py` using `--profile large` to write both enlarged finishes.

To redraw the cloth and concrete registrations alone, use the same `terminal.py` invocation with `--surfaces-only` in place of `--exterior-only --far-shore`. Use `--film-only` to measure the floor material alone. Use `--berth-concrete-only` to register the seven larger areas of concrete wear. All three commands write sidecars next to the named output path. After editing the hall geometry, generate a fresh full exposure so the material and room passes align.

## Concrete on the beams, pillars and sill

A long area of porous cement marks the nearest overhead beam. Smaller air pockets run along the beam behind the clock. Between the beams, a dark board impression crosses the soffit beside the clock, and an old mineral line follows a second seam nearer the harbour windows.

On the window side, runoff starts at the upper casting joint of the lifebuoy pillar and narrows as it descends. The nearest pillar carries a broader area of scuffed and chipped cement around the corner at luggage height. The strip below the window sill shows where a skim of mortar has lifted in the damp.

The exposed cement on the nearest beam sits in cool shadow, with dark pores, short scratches and a few lighter grains. Close to the lower edge the wear fades into a strip of intact concrete, so the narrow underside stays legible.

These seven material drawings use the same metre coordinates in all three prints. Four rays per pixel establish which surfaces are visible. The moisture, chalk and clock artwork contributes its texture opacity at each hit. The surface marks respond to the light on each concrete face.

## Cloth, water and small concrete details

The hanging blind has a turned hem, with two thicknesses of linen along the lower edge. Shallow folds fan out from the roller as the linen sags. The pattern is drawn in cloth coordinates so the weave follows the hem. The roller and window frames occlude the fabric.

At the foreground drain, the lower bank of the puddle breaks into a thinner film. Two matched Cycles exposures sample the actual floor for wet and shallow-film materials. Their difference is developed only on visible terrazzo in the affected patch. Standing water still carries the dark reflections. More of that edge survives in the 528-pixel print, where a single palette step changes the silhouette.

Four more concrete details follow the construction of the room. Two flush form-tie repairs show on the face of the dark overhead beam. A narrow mineral edge follows a board seam in the ceiling beside the clock hanger. The casting skin has chipped below a joint on the right foreground pillar. Low on the pillar with the lifebuoy, old wash water has left an interrupted tide mark.

## Check a code change

Run `uv run --locked python -m unittest discover -s tests` to check camera-pass validation, batch printing and harbour retakes. The renderer writes the selected profiles together after every requested finish is ready. To check an edit to the print pipeline, develop both profiles from the archived exposures before and after the edit in the same environment and compare the resulting PNGs.

## Concrete through the hall

A pitted edge marks the foreground beam, its pillar has a rubbed corner, and a few chips sit beside a joint above the lifebuoy. More patchwork and wear appear farther into the hall.

| Where to look | Surface |
| --- | --- |
| Above the closed ticket shutters | Several shallow losses open along the underside of the cement band and turn the curved end of the booth. |
| Ceiling just to the right of the clock | One shuttering board left a ragged patch of cement and a few short grain impressions. |
| Low on the pillar beside the boarding gate | Interrupted luggage scuffs cross the corner at two heights. Chipped cement shows at its heel. |
| Curved shoulder above the lifebuoy | A thin mortar repair follows the harbour side of the arch. Window light picks out a few traces of the trowel. |
| Wall below the leaking sill | A broken fringe of mineral bloom fans out from the sill joint and fades before the chalk boat. |

`concrete_wear.py` traces four first-hit samples for each print pixel. `casting_patina.py` draws the five material patches in metre coordinates. The wetting follows gravity, the abrasion wraps around corners, and the window frames, signs and fittings mask the surfaces behind them. Each print responds to the light in its own exposure. Both sizes sample the same underlying drawings.

## Light over the far quay

The enlarged prints keep a light post-rain haze over the water. A camera pass records the distance to each surface. The print mixes the far waterfront toward the grey of the actual sky as the path through the harbour air grows longer.

The upper part of the crane is visible through the tilted vent sash. An uneven moisture film on this pane spreads adjacent colours in the transmitted view. The narrow steel diagonals soften against the overcast sky. The fixed panes scatter a smaller share of the transmitted light. Each pane is processed inside its own boundary and the room reflections are applied afterward. The glass in the 528 × 396 print uses the native pixel treatment.

## Waterfront layout

The terminal looks obliquely across the basin. The pontoon is about 22 metres east of the scene origin. The crane operates on a quay 201 metres east of the origin, leaving approximately 179 metres of water across the basin at that section. Alongshore, the line of the quay steps back into a service berth. The water surface, fenders, gangway and tide staff share a low-water level of −3.2 metres.

The crane travels on two rails. Timber fenders hang from the quay face below the coping. The unloaded hook hangs from the outer sheave with clear water beneath it. The glazing on each sawtooth roof faces the same direction. The grain elevator feeds three bins through a short elevated gallery. Several streets behind the port, the colour and contrast of the building façades diminish with distance.

## Source guide

| Element | Source |
| --- | --- |
| Repair quay and basin, repair hall, brick warehouses, luffing crane, grain elevator, city blocks, wind on the water | `shore.py` |
| Camera, daylight, walls, window openings, floor and sea level | `terminal.py` |
| Layout and clock orientation | `layout.py` |
| Pontoon, gangway, tide staff, benches and interior fittings | `estuary.py`, `fittings.py`, `concourse.py`, `last_details.py` |
| Material maps, weather, clock and hand-drawn marks | `paint.py`, `patina.py`, `surface_marks.py`, `sea_sky.py`, `accents.py`, `plaster_stain.py` |
| Concrete relief, cement repairs, scuffs and mineral deposits | `concrete_wear.py`, `casting_patina.py` |
| Blind weave, hem and folds, beam repairs, ceiling seam, casting joint and pier heel | `hall_finishes.py` |
| Larger beam, slab, pillar and sill finishes, including texture opacity at each surface | `berth_concrete.py`, `surface_alpha.py` |
| Measured change in the reflected window at the drain | `drain_film.py`, `paint.py` |
| Distance through the windows and large-print harbour haze | `harbour_air.py` |
| Glass, reflections and window registration | `clock_glass.py`, `harbour_glass.py`, `window_print.py`, `window_exposure.py`, `harbour_plate.py` |
| Large-print geometry and exposure filtering | `large_details.py`, `surface_guides.py`, `exposure_filter.py` |
| Shared grade, palette, brush treatment and PNG output | `pixel.py` |
