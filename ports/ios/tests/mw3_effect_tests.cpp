#include "../core/mw3_gameplay_effects.h"
#include <cassert>
#include <cmath>
int main(){
 using namespace mw3;
 GameplayRegistry r;
 r.add({"rifle",Category::Weapon,Source::COD4,{Section::Multiplayer,Section::SpecialOps},{{"damage","30"},{"magazine","30"},{"reload_seconds","2.5"}}});
 r.add({"rifle",Category::Weapon,Source::MW3,{Section::Multiplayer,Section::SpecialOps},{{"damage","32"},{"magazine","30"},{"reload_seconds","2.1"}}});
 r.add({"fast",Category::Perk,Source::MW3,{Section::Multiplayer},{{"reload_multiplier","0.8"}}});
 r.add({"frag",Category::Lethal,Source::MW3,{Section::Multiplayer},{{"fuse_ms","3500"}}});
 r.add({"flash",Category::Tactical,Source::MW3,{Section::Multiplayer},{{"duration_seconds","2"}}});
 r.add({"uav",Category::Killstreak,Source::MW3,{Section::Multiplayer},{{"score_requirement","300"}}});
 auto mp=resolved_tuning(r,Section::Multiplayer,"rifle","fast","frag","flash","uav");
 assert(effective_damage(mp)==32);
 assert(std::fabs(effective_reload_seconds(mp)-1.68f)<0.001f);
 assert(streak_available(300,mp)&&!streak_available(299,mp));
 assert(lethal_fuse_ms(mp)==3500);
 assert(tactical_duration_seconds(mp)==2.0f);
 auto spec=resolved_tuning(r,Section::SpecialOps,"rifle","fast","frag","flash","uav");
 assert(spec.streak_score_required==0 && spec.perk_reload_multiplier==1.0f);
 assert(std::fabs(effective_reload_seconds(spec)-2.1f)<0.001f);
 assert(!streak_available(999,spec));
 int number=0;
 Definition malformed{"bad",Category::Weapon,Source::MW3,{Section::Multiplayer},{{"damage","not-a-number"}}};
 assert(!property_int(malformed,"damage",number));
 return 0;
}
