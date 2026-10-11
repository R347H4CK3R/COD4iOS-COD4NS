#pragma once
#include "mw3_gameplay_bridge.h"
#ifdef __cplusplus
extern "C" {
#endif
void mw3_ensure_config_loaded(void);
int mw3_optional_weapon_damage(MW3Mode mode, const char* weapon_internal_name, int original_damage);
int mw3_optional_reload_ms(MW3Mode mode, const char* weapon_internal_name, int original_reload_ms);
#ifdef __cplusplus
}
#endif
