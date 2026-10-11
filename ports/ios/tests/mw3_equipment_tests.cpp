#include "../core/mw3_equipment_adapter.h"
#include <cassert>
#include <cmath>
int main(){
 mw3_reset_registry();
 assert(mw3_optional_fuse_ms(MW3_MODE_MULTIPLAYER,"frag",3000)==3000);
 assert(mw3_register_definition("frag",MW3_LETHAL,MW3_SOURCE_MW3,1,"fuse_ms","2500"));
 assert(mw3_optional_fuse_ms(MW3_MODE_MULTIPLAYER,"frag",3000)==2500);
 assert(mw3_optional_fuse_ms(MW3_MODE_SPECIAL_OPS,"frag",3000)==3000);
 assert(mw3_register_definition("flash",MW3_TACTICAL,MW3_SOURCE_MW3,1,"duration_ms","1700"));
 assert(mw3_optional_tactical_ms(MW3_MODE_MULTIPLAYER,"flash",2000)==1700);
 assert(mw3_register_definition("uav",MW3_KILLSTREAK,MW3_SOURCE_MW3,1,"score_requirement","400"));
 assert(mw3_optional_killstreak_threshold(MW3_MODE_MULTIPLAYER,"uav",300)==400);
 assert(mw3_register_definition("fast",MW3_PERK,MW3_SOURCE_MW3,1,"reload_multiplier","0.8"));
 assert(std::fabs(mw3_optional_perk_multiplier(MW3_MODE_MULTIPLAYER,"fast","reload_multiplier",1.f)-0.8f)<0.001f);
 assert(mw3_optional_perk_multiplier(MW3_MODE_MULTIPLAYER,"fast","unrecognized",1.f)==1.f);
}
