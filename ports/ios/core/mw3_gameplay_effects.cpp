#include "mw3_gameplay_effects.h"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <limits>
namespace mw3 {
bool property_float(const Definition& d,const char* key,float& out) {
 const auto i=d.properties.find(key);
 if(i==d.properties.end()) return false;
 const char* p=i->second.c_str(); char* end=nullptr;
 const float value=std::strtof(p,&end);
 if(end==p || *end || !std::isfinite(value)) return false;
 out=value;return true;
}
bool property_int(const Definition& d,const char* key,int& out) {
 const auto i=d.properties.find(key);
 if(i==d.properties.end()) return false;
 const char* p=i->second.c_str();char* end=nullptr;
 const long value=std::strtol(p,&end,10);
 if(end==p||*end||value<std::numeric_limits<int>::min()||value>std::numeric_limits<int>::max()) return false;
 out=static_cast<int>(value);return true;
}
int effective_damage(const CombatTuning& t) {
 const double value=std::max(0,t.base_damage)*std::clamp(static_cast<double>(t.perk_damage_multiplier),0.0,10.0);
 return static_cast<int>(std::min(value,100000.0)+0.5);
}
float effective_reload_seconds(const CombatTuning& t) {
 return std::clamp(t.reload_seconds,0.0f,120.0f)*std::clamp(t.perk_reload_multiplier,0.05f,10.0f);
}
bool streak_available(int score,const CombatTuning& t) {return t.streak_score_required>0&&score>=t.streak_score_required;}
int lethal_fuse_ms(const CombatTuning& t) {return std::clamp(t.lethal_fuse_ms,0,60000);}
float tactical_duration_seconds(const CombatTuning& t) {return std::clamp(t.tactical_duration_seconds,0.0f,120.0f);}
CombatTuning resolved_tuning(const GameplayRegistry& r,Section section,const std::string& weapon,const std::string& perk,const std::string& lethal,const std::string& tactical,const std::string& streak) {
 CombatTuning t;
 if(auto d=r.find(section,Category::Weapon,weapon)) {
  property_int(*d,"damage",t.base_damage);
  property_int(*d,"magazine",t.magazine_size);
  property_float(*d,"reload_seconds",t.reload_seconds);
 }
 if(auto d=r.find(section,Category::Perk,perk)) {
  property_float(*d,"damage_multiplier",t.perk_damage_multiplier);
  property_float(*d,"reload_multiplier",t.perk_reload_multiplier);
 }
 if(auto d=r.find(section,Category::Lethal,lethal)) property_int(*d,"fuse_ms",t.lethal_fuse_ms);
 if(auto d=r.find(section,Category::Tactical,tactical)) property_float(*d,"duration_seconds",t.tactical_duration_seconds);
 if(auto d=r.find(section,Category::Killstreak,streak)) property_int(*d,"score_requirement",t.streak_score_required);
 return t;
}
}
