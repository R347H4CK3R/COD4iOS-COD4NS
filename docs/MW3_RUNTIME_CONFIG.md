# Local MW3 gameplay config (experimental)

This supplements COD4iOS; it does not make original MW3 asset packages directly loadable.

For Apple/iOS builds the multiplayer damage adapter attempts to load `<app sandbox>/Documents/mw3_gameplay.tsv` the first time it is used. Missing file = unmodified COD4 weapon damage.

Format is tab-delimited, with exactly **six columns**:
`mode_mask   category   source   id   key   value`

- Modes: 1 multiplayer, 2 Special Ops, 3 shared.
- Categories: 0 weapon, 1 attachment, 2 perk, 3 lethal, 4 tactical, 5 killstreak.
- Source: 0 COD4, 1 MW3.
- `id` must be the engine's internal weapon name for the damage override to match.
- Example (development-only, *not genuine MW3 balancing data*): `1<TAB>0<TAB>1<TAB>example_weapon<TAB>damage<TAB>34`.
- Current loader supports one property per unique definition key and refuses duplicate definitions. Reload requires process restart.
- Values are private user-supplied tuning, not original retail assets. **Do not commit proprietary asset files.**

This is a narrow runtime pathway: multiplayer damage is hooked, other gameplay properties and Special Ops are not yet called by the actual gameplay systems. Native unit tests do not prove iPhone playability.
