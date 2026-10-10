// Saved class. Imported weapons are precached only after native exact-asset validation.
main()
{
    precacheItem("m4_grunt");
    precacheItem("ak47");
    precacheItem("fraggrenade");
    precacheItem("flash_grenade");
    if (getdvarint("kisak_survival_acr") == 1) precacheItem("mw3_acr");
    if (getdvarint("kisak_survival_usp") == 1) precacheItem("mw3_usp45");
    if (getdvarint("kisak_survival_mp7") == 1) precacheItem("mw3_mp7");
    maps\_load::main();
    level.player = getent("player", "classname");
    level.player takeAllWeapons();
    if (getdvarint("kisak_survival_loadout_valid") == 1)
    {
        primary = getdvarint("kisak_survival_primary");
        weapon = "";
        if (primary == 1) weapon = "mw3_mp7";
        if (primary == 2) weapon = "mw3_acr";
        if (primary == 3) weapon = "m4_grunt";
        if (primary == 4) weapon = "ak47";
        if (getdvarint("kisak_survival_secondary") == 0)
        {
            level.player giveWeapon("mw3_usp45");
            level.player giveMaxAmmo("mw3_usp45");
            level.player switchToWeapon("mw3_usp45");
        }
        if (weapon != "")
        {
            level.player giveWeapon(weapon);
            level.player giveMaxAmmo(weapon);
            level.player switchToWeapon(weapon);
        }
        if (getdvarint("kisak_survival_equipment") == 2)
        {
            level.player giveWeapon("fraggrenade");
            level.player giveMaxAmmo("fraggrenade");
            level.player giveWeapon("flash_grenade");
            level.player giveMaxAmmo("flash_grenade");
        }
    }
    level.player enableWeapons();
    setdvar("g_reloading", "0");
}
