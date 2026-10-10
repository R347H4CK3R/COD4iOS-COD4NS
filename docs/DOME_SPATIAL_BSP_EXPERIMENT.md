# Dome spatial simplification compiler experiments (2026-10-10)

Private user-owned assets and outputs remain on authorized Windows PC.

**Goal:** Avoid `MAX_MAP_NODES` by spatially sampling the 7,087 source collision brushes.

Source: `Documents/MW3-Dome-IW4-Export/clipmap/mp_dome.iw4x.json`. Staged corrected IWMap source: `Documents/COD4-ModTools-Staging/bin/maps/mp/mp_dome_collision_winding_fixed.map`.

Python sampling script on PC: `Documents/COD4-ModTools-Staging/sample_dome_spatial.py`. It quantizes collision-brush centers into 512-unit 3D cells, keeps the largest-volume brush in each cell, then fills up to a requested sample count with largest remaining volume brushes. This is a diagnostic sampling strategy and DOES NOT preserve exact collision, walkability, visibility or game play.

- 130 distinct spatial-cell representatives: compiler completes; `mp_dome_spatial_130.d3dbsp` = **490,436 bytes**, output `Documents/COD4-ModTools-Staging/bin/maps/mp`; compilation log `dome_spatial130.log`.
- 900 selected representatives across those cells: compiler completes in **59 seconds**; `mp_dome_spatial_900.d3dbsp` = **3,641,204 bytes**, same location; log `dome_spatial900.log`.
- 2,000 first-in-order brushes: failed with `MAX_MAP_NODES`.

Important: These are placeholder textured collision prototypes; the 900 brush success does not establish that a playable version of Dome exists. Source files remain in the `bin/maps/mp` test folder. Next gates: validate brush solids and map bounds, add actual player start, material/map scripts, build IW3 asset zone via COD4 Mod Tools, launch actual game in private environment, and implement any game-engine requirements for iOS COD4 project. Large visual/asset fidelity to original MW3 Dome is not achieved.
