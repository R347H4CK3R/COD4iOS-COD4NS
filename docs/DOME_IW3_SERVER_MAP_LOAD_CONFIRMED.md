# First confirmed IW3 load of a Dome-derived experimental map (2026-10-10)

## Server-side breakthrough

Using the connected Windows GamingLaptop and a COD4 Mod Tools staging workspace, a **shortened map identifier** successfully entered COD4's dedicated-server map state:

```
]status
map: mp_dome_t
```

That output was read from COD4's actual Win32 dedicated-server console after issuing the map command via WM_CHAR/Enter and then querying `status`. Earlier `mp_dome_spatial_playtest` attempts failed back to stock map `mp_bloc`. Renaming and rebuilding into `mp_dome_t`, while using proper custom-map layout and `fs_game`, succeeded. **The precise necessity of shortening the identifier was not independently isolated** because multiple conditions were corrected; don't claim name length alone was the root cause.

The working experimental test is a spatial sample of **130 MW3 Dome-derived collision brushes** with placeholder materials and provisional spawn entities:
- Map source `Documents/COD4-ModTools-Staging/bin/maps/mp/mp_dome_t.map`
- BSP `.../bin/maps/mp/mp_dome_t.d3dbsp`, **456,148 bytes**
- Main fastfile `mp_dome_t.ff`, **26,537,357 bytes**
- Load fastfile `mp_dome_t_load.ff`, **241 bytes**
- Both private fastfiles installed in `C:\Program Files (x86)\Call of Duty 4 Modern Warfare\usermaps\mp_dome_t\`
- Empty `mods/domedebug` directory; server launch specified `+set fs_game mods/domedebug`.
- Successful query log: `Documents/COD4-ModTools-Staging/dome_short_runtime.log`.

## Controls, reference, and still-open gates

The prior longer map `mp_dome_spatial_playtest` also had a missing `_load.ff`; this was built and installed, but a later test still fell back to stock. Reference custom map convention: two fastfiles inside `usermaps/<mapname>` and an active mod `fs_game`, as described in LinuxGSM-Docs COD4 custom map documentation and zeroy COD4 map testing guide.

**Server map state is confirmed**, but **client rendering/gameplay is not**. First local client launched with `+connect 127.0.0.1` displayed `Awaiting connection...6...`. A retry using `+set net_port 28961 +connect 127.0.0.1:28960` exited before in-game render. Spawning, walkable geometry, scripts, collision, and actual player join remain unverified. This is a simplified test, not an MW3 Dome fidelity restoration or iOS IPA. Private proprietary game fastfiles must not be committed to public GitHub.

The authorized user's stock COD4 install executable was not modified. Development build remains on PC.
