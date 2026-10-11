#include "../core/mw3_gameplay_bridge.h"
#include <cassert>
#include <cstring>
int main() {
 mw3_reset_registry();
 char value[32]={};
 assert(mw3_register_definition("rifle",MW3_WEAPON,MW3_SOURCE_COD4,3,"damage","30"));
 assert(mw3_register_definition("rifle",MW3_WEAPON,MW3_SOURCE_MW3,3,"damage","32"));
 assert(mw3_resolve_string(MW3_MODE_MULTIPLAYER,MW3_WEAPON,"rifle","damage",value,sizeof(value)));
 assert(std::strcmp(value,"32")==0);
 assert(mw3_register_definition("uav",MW3_KILLSTREAK,MW3_SOURCE_MW3,1,"score","300"));
 assert(!mw3_resolve_string(MW3_MODE_SPECIAL_OPS,MW3_KILLSTREAK,"uav","score",value,sizeof(value)));
 assert(!mw3_register_definition("uav",MW3_KILLSTREAK,MW3_SOURCE_MW3,1,"score","300"));
 assert(!mw3_resolve_string(MW3_MODE_MULTIPLAYER,MW3_WEAPON,"rifle","damage",value,1));
 mw3_reset_registry();
 assert(!mw3_resolve_string(MW3_MODE_MULTIPLAYER,MW3_WEAPON,"rifle","damage",value,sizeof(value)));
}
