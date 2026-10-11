#pragma once
#include "mw3_gameplay_bridge.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Safe opt-in queries. Missing or invalid configuration returns original values. */
int mw3_optional_fuse_ms(MW3Mode mode,const char* equipment_id,int original_ms);
int mw3_optional_tactical_ms(MW3Mode mode,const char* equipment_id,int original_ms);
int mw3_optional_killstreak_threshold(MW3Mode mode,const char* streak_id,int original_score);
float mw3_optional_perk_multiplier(MW3Mode mode,const char* perk_id,const char* property,float original);
#ifdef __cplusplus
}
#endif
