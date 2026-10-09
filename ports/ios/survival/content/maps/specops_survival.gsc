// Independent Survival entry. Retail map/actor assets remain in main and zone.
main()
{
    precacheItem("m4_grunt");
    precacheItem("ak47");
    maps\_load::main();
    level.player = getent("player", "classname");
    level.player takeAllWeapons();
    level.player giveWeapon("m4_grunt");
    level.player giveMaxAmmo("m4_grunt");
    level.player switchToWeapon("m4_grunt");
    level.player enableWeapons();
    setdvar("g_reloading", "0");
}
