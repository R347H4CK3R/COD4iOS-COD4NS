#pragma once
#include <algorithm>
namespace cod4ios::survival {
constexpr unsigned maxProgress=1000000000u;
// Original MW3 armory row uses zero-based rank 13; this UI displays rank + 1.
constexpr unsigned importedAcrRank=14;
enum class Map : unsigned { Bog, BogContinuation, Ambush, Blackout, Armada };
enum class Difficulty : unsigned { Recruit, Regular, Hardened, Veteran };
enum class PlayerClass : unsigned { Assault, Raider, Armored };
struct Config {
 unsigned map=0, difficulty=1, playerClass=0;
 void sanitize() { if(map>4) map=0; if(difficulty>3) difficulty=1; if(playerClass>2) playerClass=0; }
};
inline const char* mapId(unsigned value) { static const char* ids[]={"bog_a","bog_b","ambush","blackout","armada"}; return ids[value<5?value:0]; }
inline const char* mapName(unsigned value) { static const char* names[]={"Bog","Bog continuation","Ambush","Blackout","Armada"}; return names[value<5?value:0]; }
inline const char* difficultyName(unsigned value) { static const char* names[]={"Recruit","Regular","Hardened","Veteran"}; return names[value<4?value:1]; }
inline const char* className(unsigned value) { static const char* names[]={"Assault","Raider","Armored"}; return names[value<3?value:0]; }
inline const char* classWeapon(unsigned value) { return value==1 ? "ak47" : "m4_grunt"; }
inline unsigned enemyHealth(unsigned wave,unsigned difficulty) { static constexpr unsigned base[]={75,100,125,150}; return std::min(1000u,base[difficulty<4?difficulty:1]+std::min(wave,100u)*5u); }
inline float enemyAccuracy(unsigned wave,unsigned difficulty) { static constexpr float base[]={0.20f,0.35f,0.50f,0.65f}; return std::min(0.90f,base[difficulty<4?difficulty:1]+std::min(wave,100u)*0.005f); }
inline unsigned killReward(unsigned difficulty) { static constexpr unsigned reward[]={75,100,125,150}; return reward[difficulty<4?difficulty:1]; }
inline unsigned killXP(unsigned difficulty) { static constexpr unsigned xp[]={10,15,20,25}; return xp[difficulty<4?difficulty:1]; }
inline unsigned rankForXP(unsigned xp) { return std::min(50u,1u+xp/500u); }
}
