#pragma once
struct gentity_s;
const char *KisakSurvival_LevelScript(const char *original);
void KisakSurvival_Begin();
void KisakSurvival_Frame();
void KisakSurvival_EnemyDied(gentity_s *enemy,gentity_s *attacker);
void KisakSurvival_Removed(gentity_s *enemy);
void KisakSurvival_PlayerDied();
int KisakSurvival_AbsorbDamage(gentity_s *player,int damage);
void KisakSurvival_Shutdown();
void KisakSurvival_PumpMode();
bool KisakSurvival_UsesManualRetry();
const char *KisakSurvival_SaveGameDirectory();
bool KisakSurvival_IsSelected();

const char *KisakSurvival_StartupCommand();
bool KisakSurvival_Invulnerable(gentity_s *player);
int KisakSurvival_ModifyDamage(gentity_s *target,gentity_s *attacker,int damage,unsigned weapon);
