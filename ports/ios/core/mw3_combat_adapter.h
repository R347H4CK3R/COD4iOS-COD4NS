#pragma once
#include "mw3_gameplay_bridge.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Optional live-combat adapter. Uses the original damage when no override exists.
 * Requires registration and a separate call-site integration to have an effect. */
int mw3_optional_weapon_damage(MW3Mode mode, const char* weapon_internal_name, int original_damage);
int mw3_optional_reload_ms(MW3Mode mode, const char* weapon_internal_name, int original_reload_ms);
#ifdef __cplusplus
}
#endif
