# COD4 Dome conversion state — 2026-10-10

On authorized Windows PC, from existing private exported clipmap, created an experimental COD4 Radiant map draft at:
`C:\Users\Chris\Documents\MW3-Dome-IW4-Export\iw3-radiant-drafts\mp_dome_collision_iwmap4.map`

This map draft begins with `iwmap 4`, includes `"000_Global" flags active`, `"The Map" flags`, and COD4-style face texture/lightmap fields; 7,087 brush blocks and 71,962 face lines; 10,629,852 bytes.

**Limitations:** generated brushes originate from IW4 collision AABBs and nonaxial clipping planes, not complete visual geometry. Brush intersection/winding and IW3 Radiant parsing have **not been verified**, nor any COD4 compiler or in-game loading. The file does **not** establish a usable playable map. No COD4 map compiler was found on PATH. Official CoD4 Mod Tools typically require an installed COD4 PC game at expected location; no such install was detected in checked standard paths. Do not install COD4 mod tools into an MW3 directory.

Established public references: https://github.com/cod4mw/CoD4-Mod-Tools and https://github.com/xoxor4d/iw3xo-radiant. These do not themselves solve textures, rendered world surfaces, models, mapents, scripting, fastfile build or iOS integration.

The full MW3→IW4 export (7,783 files) remains private in Documents. Proprietary assets are not committed. Next step must include real Radiant parse/compile test and brush geometry fixes before claiming successful IW3 conversion.
