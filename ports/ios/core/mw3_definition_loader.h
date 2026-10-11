#pragma once
#ifdef __cplusplus
extern "C" {
#endif
/* Loads a private, local tab-separated definition file.
 * Format: mode_mask TAB category TAB source TAB id TAB key TAB value.
 * mode_mask: 1 multiplayer, 2 special_ops, 3 shared
 * category: 0 weapon, 1 attachment, 2 perk, 3 lethal, 4 tactical, 5 killstreak
 * source: 0 COD4, 1 MW3.
 * Returns accepted definition count, -1 on open/format failure.
 * File must be trusted local configuration, not untrusted server content.
 */
int mw3_load_definitions_tsv(const char* path);
#ifdef __cplusplus
}
#endif
