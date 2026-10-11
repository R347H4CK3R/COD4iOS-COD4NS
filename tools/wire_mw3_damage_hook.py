from pathlib import Path
root=Path(__file__).resolve().parents[1]
path=root/'src/game_mp/g_combat_mp.cpp'
source=path.read_text(encoding='utf-8')
anchor='#include <universal/q_shared.h>'
inc='#if defined(__APPLE__)\n#include "../../ports/ios/core/mw3_combat_adapter.h"\n#endif'
if inc not in source:
 assert anchor in source
 source=source.replace(anchor,anchor+'\n'+inc,1)
hook='''#if defined(__APPLE__)
        // Optional MW3 tuning: no registered override preserves COD4 damage.
        if (weapon > 0 && weapon < BG_GetNumWeapons())
        {
            WeaponDef *mw3Weapon = BG_GetWeaponDef(weapon);
            if (mw3Weapon && mw3Weapon->szInternalName)
                damage = mw3_optional_weapon_damage(MW3_MODE_MULTIPLAYER, mw3Weapon->szInternalName, damage);
        }
#endif
'''
needle='        if (mod != MOD_MELEE)'
if 'mw3_optional_weapon_damage(' not in source:
 assert source.count(needle)==1
 source=source.replace(needle,hook+needle,1)
path.write_text(source,encoding='utf-8')
print('Hook present:', 'mw3_optional_weapon_damage(' in source)
