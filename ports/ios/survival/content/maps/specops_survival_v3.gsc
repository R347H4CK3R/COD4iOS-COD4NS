// Optional converted MW3 assets; preserve older entries and all retail files.
main()
{
    precacheItem("m4_grunt");
    precacheItem("ak47");
    if (getdvarint("kisak_survival_acr") == 1)
        precacheItem("mw3_acr");
    maps\_load::main();
    level.player = getent("player", "classname");
    weapon = "m4_grunt";
    if (getdvarint("kisak_survival_class") == 1)
        weapon = "ak47";
    level.player takeAllWeapons();
    level.player giveWeapon(weapon);
    level.player giveMaxAmmo(weapon);
    level.player switchToWeapon(weapon);
    level.player enableWeapons();
    setdvar("g_reloading", "0");
}
