from pathlib import Path
p=Path(__file__).resolve().parents[1]/"src/bgame/bg_weapons.cpp"
s=p.read_text(encoding="utf-8")
anchor='#include <universal/q_shared.h>'
include='#if defined(__APPLE__) && defined(KISAK_MP)\n#include "../../ports/ios/core/mw3_combat_adapter.h"\n#endif'
if include not in s:
 assert anchor in s
 s=s.replace(anchor,anchor+"\n"+include,1)
start=s.index("void __cdecl PM_SetReloadingState(playerState_s *ps)")
end=s.index("void __cdecl PM_SetWeaponReloadAddAmmoDelay(playerState_s *ps)",start)
fragment=s[start:end]
needle="    if (ps->weaponstate == WEAPON_RELOAD_START_INTERUPT)"
hook='''#if defined(__APPLE__) && defined(KISAK_MP)
    // Optional override of player reload timing; original duration retained when absent.
    // Do not mutate shared WeaponDef fields or globally modify weapon definitions.
    if (weapDef && weapDef->szInternalName)
        ps->weaponTime = mw3_optional_reload_ms(MW3_MODE_MULTIPLAYER, weapDef->szInternalName, ps->weaponTime);
#endif
'''
assert needle in fragment
if "mw3_optional_reload_ms(" not in fragment:
 fragment=fragment.replace(needle,hook+needle,1)
 s=s[:start]+fragment+s[end:]
p.write_text(s,encoding="utf-8")
print("Reload state integration present")
