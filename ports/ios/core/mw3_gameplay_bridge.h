#pragma once
#ifdef __cplusplus
extern "C" {
#endif
/* Lightweight C ABI for existing COD4 C/C++ gameplay call sites.
 * Values are configuration metadata, not active gameplay effects. */
typedef enum { MW3_MODE_MULTIPLAYER=0, MW3_MODE_SPECIAL_OPS=1 } MW3Mode;
typedef enum { MW3_WEAPON=0, MW3_ATTACHMENT=1, MW3_PERK=2, MW3_LETHAL=3, MW3_TACTICAL=4, MW3_KILLSTREAK=5 } MW3Category;
typedef enum { MW3_SOURCE_COD4=0, MW3_SOURCE_MW3=1 } MW3Source;
int mw3_register_definition(const char* id, MW3Category category, MW3Source source, unsigned int mode_mask, const char* key, const char* value);
int mw3_resolve_string(MW3Mode mode, MW3Category category, const char* id, const char* key, char* output, unsigned int output_size);
void mw3_reset_registry(void);
#ifdef __cplusplus
}
#endif
