# IW5xport map command registration defect — verified source finding

Source: `iw4x/iw5x-port/src/module/command.cpp` in `command::post_load()`.

Upstream code:

```cpp
add("map", [](const params& params)
{
    if (params.size() == 1)
    {
        const auto map_name = params.get(0);
        game::native::SV_Map_f(0, map_name, false, false);
    }
});
```

But `params::size()` returns `cmd_args->argc[nesting]`, and `params::get(index)` returns `cmd_args->argv[nesting][index]`. Index 0 is the command name; index 1 is the first argument. Thus `map mp_dome` has argc 2; the current handler does nothing.

Correct handler:

```cpp
add("map", [](const params& params)
{
    if (params.size() == 2)
    {
        const auto map_name = params.get(1);
        game::native::SV_Map_f(0, map_name, false, false);
    }
});
```

This change has been **identified but not built or tested yet**. The unrelated `loadzone` and `devmap` attempts are not proven routes. `dumpGfxWorld` enumerates loaded GfxWorld assets with `DB_EnumXAssets`; supplying an asset name to it is not necessary. Confirm map loading before dumping.

Next milestone: build a patched IW5xport executable (private build; do not redistribute MW3 binaries/assets), then run `map mp_dome`, verify loading, and run the exporters. If no loaded map geometry appears, investigate the separate IW5 runtime's Steam and initialization diagnostics.

No COD4 map conversion has occurred.
