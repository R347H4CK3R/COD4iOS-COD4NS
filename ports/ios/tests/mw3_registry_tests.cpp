#include "../core/mw3_gameplay_registry.h"
#include <cassert>
#include <stdexcept>
int main() {
 using namespace mw3;
 GameplayRegistry r;
 r.add({"rifle",Category::Weapon,Source::COD4,{Section::Multiplayer,Section::SpecialOps},{{"damage","30"}}});
 r.add({"rifle",Category::Weapon,Source::MW3,{Section::Multiplayer,Section::SpecialOps},{{"damage","32"}}});
 r.add({"uav",Category::Killstreak,Source::MW3,{Section::Multiplayer},{{"score","300"}}});
 assert(r.find(Section::Multiplayer,Category::Weapon,"rifle")->properties.at("damage")=="32");
 assert(r.find(Section::Multiplayer,Category::Weapon,"rifle",Source::COD4)->properties.at("damage")=="30");
 assert(r.find(Section::SpecialOps,Category::Killstreak,"uav")==nullptr);
 assert(r.count(Section::Multiplayer,Category::Weapon)==1);
 bool rejected=false;
 try {r.add({"rifle",Category::Weapon,Source::MW3,{Section::Multiplayer},{}});}
 catch(const std::invalid_argument&) {rejected=true;}
 assert(rejected);
 return 0;
}
