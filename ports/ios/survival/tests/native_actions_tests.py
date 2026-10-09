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
#include "ports/ios/survival/SurvivalRuntime.hpp"
#include "ports/ios/survival/SurvivalProfile.hpp"
#include "ports/ios/survival/SurvivalPause.hpp"
#include "ports/ios/survival/SurvivalUpgrades.hpp"
#include "ports/ios/survival/SurvivalBridge.hpp"
using namespace cod4ios::survival;
Runtime runtime; Status status; Profile profile; PauseLease pauseLease; WeaponUpgrades upgrades;
bool active=true, mode=true, grantWorks=true;
bool selected() { return mode; }
struct Dvar { struct { int integer=0; } current; } pauseValue;
const Dvar* cl_paused=&pauseValue;
void Dvar_SetInt(const Dvar* d,int value) { const_cast<Dvar*>(d)->current.integer=value; }
struct Client { struct { unsigned weapon=1; unsigned weaponmodels[128]{}; } ps; } client;
struct Sentient { int eTeam; } hostile{1}, friendly{2};
constexpr int TEAM_AXIS=1, WEAPTYPE_BULLET=0;
struct Entity { struct { bool inuse=true; } r; Client* client=nullptr; void* actor=nullptr; Sentient* sentient=nullptr; };
using gentity_s=Entity;
Entity g_entities[4]; struct { int num_entities=4; } level;
struct Weapon { int weapType=0; } gun;
unsigned BG_GetNumWeapons() { return 3; }
Weapon* BG_GetWeaponDef(unsigned) { return &gun; }
int Add_Ammo(Entity*,unsigned,unsigned,int,int) { return 1; }
void G_FreeEntity(Entity* e) { e->r.inuse=false; }
bool grant(Purchase) { return grantWorks; }
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
}
'''
code=stubs+extract('void syncPause()')+extract('void processActions()')+extract('bool KisakSurvival_Invulnerable(')+extract('int KisakSurvival_ModifyDamage(')+tests
with tempfile.TemporaryDirectory(prefix='survival-actions-test-') as directory:
    folder=Path(directory); source=folder/'test.cpp'; executable=folder/('actions.exe' if os.name=='nt' else 'actions')
    source.write_text(code)
    subprocess.run(compiler+['-std=c++17','-I',str(root),str(source),str(root/'ports/ios/survival/SurvivalBridge.cpp'),'-o',str(executable)],check=True)
    subprocess.run([str(executable)],check=True)
print('Production combat Shop, paused bank/purchases, upgrade caps, cheats, retry ordering and Campaign damage isolation passed')
