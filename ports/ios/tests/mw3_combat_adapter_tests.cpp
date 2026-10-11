#include "../core/mw3_combat_adapter.h"
#include <cassert>
int main() {
 mw3_reset_registry();
 assert(mw3_optional_weapon_damage(MW3_MODE_MULTIPLAYER,"ak",27)==27);
 assert(mw3_register_definition("ak",MW3_WEAPON,MW3_SOURCE_MW3,1,"damage","34"));
 assert(mw3_optional_weapon_damage(MW3_MODE_MULTIPLAYER,"ak",27)==34);
 assert(mw3_optional_weapon_damage(MW3_MODE_SPECIAL_OPS,"ak",27)==27);
 assert(mw3_register_definition("ak",MW3_WEAPON,MW3_SOURCE_COD4,2,"damage","22"));
 assert(mw3_optional_weapon_damage(MW3_MODE_SPECIAL_OPS,"ak",27)==22);
 assert(mw3_optional_reload_ms(MW3_MODE_MULTIPLAYER,"ak",2000)==2000);
 assert(mw3_register_definition("ak",MW3_WEAPON,MW3_SOURCE_MW3,1,"reload_ms","1800")==0); /* duplicate definition rejected */
 mw3_reset_registry();
 assert(mw3_register_definition("bad",MW3_WEAPON,MW3_SOURCE_MW3,1,"damage","nonsense"));
 assert(mw3_optional_weapon_damage(MW3_MODE_MULTIPLAYER,"bad",27)==27);
}
