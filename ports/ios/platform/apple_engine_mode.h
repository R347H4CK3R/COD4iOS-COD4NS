#pragma once
#ifdef __cplusplus
extern "C" {
#endif
// "sp" or "mp": which engine dylib the launcher loads on the next start.
void KisakApple_SetEngineMode(const char *mode);
const char *KisakApple_GetEngineMode();
// Stable UI mode IDs: campaign, survival, multiplayer. Invalid requests are rejected.
bool KisakApple_SetGameMode(const char *mode);
const char *KisakApple_GetGameMode();
unsigned KisakApple_GetSurvivalBestWave();
void KisakApple_RecordSurvivalBestWave(unsigned wave);
void KisakApple_PromptEngineRestart(const char *mode);
#ifdef __cplusplus
}
#endif
