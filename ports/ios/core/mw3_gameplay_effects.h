#pragma once
#include "mw3_gameplay_registry.h"
namespace mw3 {
struct CombatTuning {
 int base_damage=0;
 int magazine_size=0;
 float reload_seconds=0.0f;
 float perk_damage_multiplier=1.0f;
 float perk_reload_multiplier=1.0f;
 float tactical_duration_seconds=0.0f;
 int lethal_fuse_ms=0;
 int streak_score_required=0;
};
int effective_damage(const CombatTuning& tuning);
float effective_reload_seconds(const CombatTuning& tuning);
bool streak_available(int score, const CombatTuning& tuning);
int lethal_fuse_ms(const CombatTuning& tuning);
float tactical_duration_seconds(const CombatTuning& tuning);
bool property_int(const Definition& definition,const char* key,int& result);
bool property_float(const Definition& definition,const char* key,float& result);
CombatTuning resolved_tuning(const GameplayRegistry& registry,Section section,const std::string& weapon_id,const std::string& perk_id,const std::string& lethal_id,const std::string& tactical_id,const std::string& streak_id);
}
