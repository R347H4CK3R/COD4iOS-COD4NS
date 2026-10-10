#!/usr/bin/env python3
"""Execute production shop actions and damage hooks without retail data."""
from pathlib import Path
import os, shlex, shutil, subprocess, tempfile
root=Path(__file__).resolve().parents[4]
native=(root/'ports/ios/survival/survival_engine.cpp').read_text()
def extract(name):
    start=native.index(name); opening=native.index('{',start); depth=1; end=opening+1
    while depth:
        depth += (native[end]=='{') - (native[end]=='}'); end+=1
    return native[start:end]+'\n'
compiler=['xcrun','clang++'] if shutil.which('xcrun') else shlex.split(os.environ.get('CXX','clang++'))
stubs=r'''
#include <cassert>
#include <cstring>
#include <string>
#include <array>
#include <atomic>
#include "ports/ios/survival/SurvivalArmory.hpp"
#include "ports/ios/survival/SurvivalRuntime.hpp"
#include "ports/ios/survival/SurvivalProfile.hpp"
#include "ports/ios/survival/SurvivalPause.hpp"
#include "ports/ios/survival/SurvivalUpgrades.hpp"
#include "ports/ios/survival/SurvivalBridge.hpp"
using namespace cod4ios::survival;
Runtime runtime; Status status; Profile profile; PauseLease pauseLease; WeaponUpgrades upgrades;
Config config; std::array<unsigned,4> generations{};
Armory armory; Rewards rewards; std::array<bool,4> heavyEnemies{};
Killstreaks killstreaks; std::atomic<bool> fastReloadEnabled{false};
int lastDamage=0, lastRecovery=0, reviveUntil=0;
bool active=true, mode=true, grantWorks=true;
bool selected() { return mode; }
unsigned mw3XP=0;
unsigned currentRank() { return rankForXP(profile.xp); }
void addMW3XP(unsigned amount) { mw3XP+=amount; }
bool grantWeapon(const char*) { return grantWorks; }
struct Dvar { struct { int integer=0; } current; } pauseValue;
const Dvar* cl_paused=&pauseValue;
void Dvar_SetInt(const Dvar* d,int value) { const_cast<Dvar*>(d)->current.integer=value; }
enum { STAT_HEALTH, STAT_MAX_HEALTH };
struct Client { struct { unsigned weapon=1; unsigned weaponmodels[128]{}; int stats[2]{100,100}; } ps; } client;
struct Sentient { int eTeam; } hostile{1}, friendly{2};
constexpr int TEAM_AXIS=1, WEAPTYPE_BULLET=0;
struct Entity { struct { bool inuse=true; } r; struct { int number=1; } s; int health=100; Client* client=nullptr; void* actor=nullptr; Sentient* sentient=nullptr; };
using gentity_s=Entity;
Entity g_entities[4]; struct { int num_entities=4, time=0; } level;
struct Weapon { int weapType=0; } gun;
unsigned BG_GetNumWeapons() { return 3; }
Weapon* BG_GetWeaponDef(unsigned) { return &gun; }
int Add_Ammo(Entity*,unsigned,unsigned,int,int) { return 1; }
void G_FreeEntity(Entity* e) { e->r.inuse=false; }
unsigned supplyGrants=0;
bool grant(Purchase item) { if(item==Purchase::Ammo && grantWorks) ++supplyGrants; return grantWorks; }
void message(const char* text) { std::snprintf(status.message,sizeof(status.message),"%s",text); }
void persistProfile() { status.bank=profile.bank; status.xp=profile.xp; }
void publish() { status.match=runtime.session().snapshot(); status.active=active; publishStatus(status); }
int reloads=0;
const char* reloadCommand(bool=false) { return "devmap bog_a\n"; }
void Cbuf_AddText(int,const char*) { ++reloads; }
'''
tests=r'''
void action(Action value,unsigned amount=0) { publish(); assert(queueAction(value,status.epoch,amount)); processActions(); publish(); }
int main() {
 resetBridge(); status=readStatus(); status.active=true;
 g_entities[0].client=&client;
 runtime.begin(); runtime.tick(3); runtime.session().addCredits(20000); publish();
 action(Action::OpenShop); assert(status.shopOpen && pauseValue.current.integer==1);
 action(Action::ACR); assert(runtime.session().snapshot().credits==20000);
 action(Action::Revive); assert(!armory.reviveReady() && runtime.session().snapshot().credits==20000);
 profile.xp=1500; action(Action::Revive); action(Action::Recovery);
 assert(armory.reviveReady() && armory.recoveryEnabled() && runtime.session().snapshot().credits==16500);
 action(Action::Revive); action(Action::Recovery); assert(runtime.session().snapshot().credits==16500);
 runtime.session().addCredits(3500);
 action(Action::FastReload); assert(!armory.fastReloadEnabled() && runtime.session().snapshot().credits==20000);
 profile.xp=2500; action(Action::FastReload); assert(armory.fastReloadEnabled() && runtime.session().snapshot().credits==17500);
 action(Action::FastReload); assert(runtime.session().snapshot().credits==17500);
 assert(KisakSurvival_ReloadDuration(0,1000)==500 && KisakSurvival_ReloadDuration(1,1000)==1000);
 assert(KisakSurvival_ReloadDuration(0,1)==1 && KisakSurvival_ReloadDuration(0,0)==0);
 fastReloadEnabled=false; assert(KisakSurvival_ReloadDuration(0,1000)==1000);
 runtime.session().addCredits(2500);
 g_entities[0].health=20; status.armor=0;
 assert(KisakSurvival_AbsorbDamage(&g_entities[0],30)==0 && g_entities[0].health==100 && !armory.reviveReady());
 assert(KisakSurvival_Invulnerable(&g_entities[0])); level.time=3000;
 assert(!KisakSurvival_Invulnerable(&g_entities[0]));
 assert(KisakSurvival_AbsorbDamage(&g_entities[0],30)==30);
 mode=false; status.armor=100; assert(KisakSurvival_AbsorbDamage(&g_entities[0],30)==30 && status.armor==100); mode=true;
 assert(KisakSurvival_AbsorbDamage(&g_entities[1],30)==30 && status.armor==100);
 g_entities[0].health=50; lastDamage=3000;
 updateRecovery(4999); assert(g_entities[0].health==50);
 updateRecovery(5000); assert(g_entities[0].health==55 && client.ps.stats[STAT_HEALTH]==55);
 updateRecovery(5001); assert(g_entities[0].health==55);
 g_entities[0].health=98; updateRecovery(5250); assert(g_entities[0].health==100);
 g_entities[0].health=0; updateRecovery(5500); assert(g_entities[0].health==0); g_entities[0].health=100;
 // Actions keep running in the paused simulation: funds remain conserved.
 action(Action::Deposit,1000); assert(profile.bank==1000 && runtime.session().snapshot().credits==19000);
 action(Action::Withdraw,500); assert(profile.bank==500 && runtime.session().snapshot().credits==19500);
 action(Action::Withdraw,1000); assert(profile.bank==500 && runtime.session().snapshot().credits==19500);
 action(Action::Pack); assert(upgrades.tier(1)==1 && runtime.session().snapshot().credits==17500);
 action(Action::Pack); action(Action::Pack); assert(upgrades.tier(1)==3 && runtime.session().snapshot().credits==7500);
 action(Action::Pack); assert(runtime.session().snapshot().credits==7500);
 grantWorks=false; action(Action::Ammo); assert(runtime.session().snapshot().credits==7500);
 action(Action::God); assert(KisakSurvival_Invulnerable(&g_entities[0]));
 assert(!KisakSurvival_Invulnerable(&g_entities[1])); mode=false;
 assert(!KisakSurvival_Invulnerable(&g_entities[0])); mode=true;
 Entity enemy; enemy.actor=&enemy; enemy.sentient=&hostile;
 assert(KisakSurvival_ModifyDamage(&enemy,&g_entities[0],25,1)==100);
 heavyEnemies[1]=true; assert(KisakSurvival_ModifyDamage(&enemy,&g_entities[0],25,1)==48); heavyEnemies[1]=false;
 assert(KisakSurvival_ModifyDamage(&enemy,&g_entities[1],25,1)==25);
 enemy.sentient=&friendly; assert(KisakSurvival_ModifyDamage(&enemy,&g_entities[0],25,1)==25);
 enemy.sentient=&hostile; mode=false; assert(KisakSurvival_ModifyDamage(&enemy,&g_entities[0],25,1)==25); mode=true;
 action(Action::InfiniteAmmo); assert(status.infiniteAmmo);
 action(Action::Money); assert(runtime.session().snapshot().credits==17500);
 action(Action::CloseShop); assert(!status.shopOpen && pauseValue.current.integer==0);
 action(Action::Money); assert(runtime.session().snapshot().credits==17500);
 action(Action::OpenShop); action(Action::NextWave); assert(runtime.session().snapshot().phase==Phase::Intermission);
 assert(runtime.session().snapshot().bestCompletedWave==0);
 // A queued purchase behind Retry must not execute against the outgoing match.
 publish(); assert(queueAction(Action::Retry,status.epoch)); assert(queueAction(Action::Money,status.epoch)); processActions();
 assert(!active && reloads==1 && pauseValue.current.integer==0 && runtime.session().snapshot().credits==17500);
 active=true; grantWorks=true; runtime.begin(); runtime.tick(3); runtime.session().skipWave(); runtime.tick(10);
 killstreaks.reset(); rewards.reset(); rewards.beginWave(2); supplyGrants=0; status.armor=0;
 enemy.sentient=&hostile; enemy.s.number=1;
 for(unsigned n=1;n<=12;++n) {
   assert(runtime.reserve(1)); assert(runtime.spawned(1,++generations[1]));
   KisakSurvival_EnemyDied(&enemy,&g_entities[0]);
   KisakSurvival_EnemyDied(&enemy,&g_entities[0]); // duplicate death cannot farm cash or streaks
   assert(killstreaks.count()==n);
 }
 assert(supplyGrants==1 && status.armor==100 && runtime.session().snapshot().credits==2400);
 assert(runtime.reserve(1)); assert(runtime.spawned(1,++generations[1]));
 KisakSurvival_Removed(&enemy); assert(killstreaks.count()==12 && runtime.session().snapshot().credits==2400);
 action(Action::OpenShop); runtime.session().addCredits(1000); profile.xp=6500;
 grantWorks=false; action(Action::ACR); assert(runtime.session().snapshot().credits==3400);
 grantWorks=true; action(Action::ACR); assert(runtime.session().snapshot().credits==400);
 // Completing a whole wave awards XP once per tracked kill, including the last.
 runtime.begin(); runtime.tick(3); killstreaks.reset(); rewards.reset(); rewards.beginWave(1);
 const unsigned oldXP=profile.xp, startingXP=mw3XP;
 unsigned kills=0;
 while(runtime.session().snapshot().phase==Phase::Fighting) {
   assert(runtime.reserve(1)); assert(runtime.spawned(1,++generations[1]));
   KisakSurvival_EnemyDied(&enemy,&g_entities[0]); ++kills; runtime.tick(0.001);
 }
 assert(runtime.session().snapshot().phase==Phase::Intermission);
 assert(mw3XP==startingXP+kills*125 && profile.xp==oldXP && killstreaks.count()==kills);
 KisakSurvival_EnemyDied(&enemy,&g_entities[0]);
 assert(mw3XP==startingXP+kills*125);
}
'''
code=stubs+extract('void syncPause()')+extract('void updateRecovery(')+extract('void processActions()')+extract('bool KisakSurvival_Invulnerable(')+extract('int KisakSurvival_ModifyDamage(')+extract('int KisakSurvival_AbsorbDamage(')+extract('int KisakSurvival_ReloadDuration(')+extract('void KisakSurvival_EnemyDied(')+extract('void KisakSurvival_Removed(')+tests
reload_source=(root/'src/bgame/bg_weapons.cpp').read_text()
start=reload_source.index('void __cdecl PM_SetReloadingState(')
end=reload_source.index('void __cdecl PM_SetWeaponReloadAddAmmoDelay(',start)
assert 'ps->weaponTime=KisakSurvival_ReloadDuration(ps->clientNum,ps->weaponTime)' in reload_source[start:end]
with tempfile.TemporaryDirectory(prefix='survival-actions-test-') as directory:
    folder=Path(directory); source=folder/'test.cpp'; executable=folder/('actions.exe' if os.name=='nt' else 'actions')
    source.write_text(code)
    subprocess.run(compiler+['-std=c++17','-I',str(root),str(source),str(root/'ports/ios/survival/SurvivalBridge.cpp'),'-o',str(executable)],check=True)
    subprocess.run([str(executable)],check=True)
print('Production combat Shop, paused bank/purchases, upgrade caps, cheats, retry ordering and Campaign damage isolation passed')
