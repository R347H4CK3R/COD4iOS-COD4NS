// Versioned independent entry; preserve original retail assets and older scripts.
main()
{
    precacheItem("m4_grunt");
    precacheItem("ak47");
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
