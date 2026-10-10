#!/usr/bin/env python3
"""Run production reload state transitions, including bolt ammunition timing."""
from pathlib import Path
import os, shlex, shutil, subprocess, tempfile
root=Path(__file__).resolve().parents[4]
source=(root/'src/bgame/bg_weapons.cpp').read_text()
names=['PM_SetReloadingState','PM_SetWeaponReloadAddAmmoDelay','PM_Weapon_AllowReload','PM_Weapon_ReloadDelayedAction','PM_ReloadClip','PM_Weapon_FinishReload','PM_Weapon_FinishReloadStart','PM_BeginWeaponReload']
functions=[]
for name in names:
    start=source.index('void __cdecl '+name+'(') if name!='PM_Weapon_AllowReload' else source.index('int __cdecl '+name+'(')
    brace=source.index('{',start); depth=1; end=brace+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}'); end+=1
    functions.append(source[start:end])
stubs=r'''
#include <cassert>
#include <algorithm>
#include <cstdint>
#ifndef __cdecl
#define __cdecl
#endif
#define __APPLE__ 1
#define KISAK_SP 1
#define iassert assert
enum {WEAPON_READY,WEAPON_FIRING,WEAPON_RECHAMBERING,WEAPON_RELOAD_START,WEAPON_RELOAD_START_INTERUPT,WEAPON_RELOADING,WEAPON_RELOADING_INTERUPT,WEAPON_RELOAD_END,WEAPON_SPRINT_RAISE=20,WEAPON_SPRINT_DROP=22};
enum {WEAP_RELOAD,WEAP_RELOAD_EMPTY,WEAP_RELOAD_END,WEAP_IDLE,WEAP_RELOAD_START};
enum {EV_RELOAD,EV_RELOAD_FROM_EMPTY,EV_RELOAD_END,EV_EJECT_BRASS,EV_RELOAD_ADDAMMO,EV_RESET_ADS,EV_RELOAD_START_NOTIFY,EV_RELOAD_START};
constexpr int BUTTON_ATTACK=1;
struct playerState_s {int clientNum=0,weapon=1,weaponstate=0,weaponTime=0,weaponDelay=0,weaponShotCount=0; int ammoclip[2]{},ammo[2]{},weaponrechamber[2]{};};
struct pmove_t {playerState_s *ps; struct {int buttons=0;} cmd;};
struct WeaponDef {int iReloadTime=3000,iReloadEmptyTime=3000,iReloadAddTime=2800,iRechamberBoltTime=500,iReloadStartTime=1000,iReloadStartAddTime=800,iReloadEndTime=600,iReloadStartAdd=1,iReloadAmmoAdd=0,iClipSize=5,weapType=0; bool bBoltAction=true,bSegmentedReload=false,bNoPartialReload=false;} definition;
bool perk=true; int ammoEvents=0,elapsed=0,ammoAt=-1;
int KisakSurvival_ReloadDuration(int client,int duration) {return perk && client==0 && duration>0 ? std::max(1,duration/2):duration;}
WeaponDef *BG_GetWeaponDef(int) {return &definition;}
int BG_ClipForWeapon(int) {return 1;} int BG_AmmoForWeapon(int) {return 1;} int BG_GetNumWeapons() {return 2;}
bool Com_BitCheckAssert(int *bits,unsigned,int) {return bits[0]!=0;} void Com_BitClearAssert(int *bits,unsigned,int) {bits[0]=0;}
void PM_StartWeaponAnim(playerState_s *,int) {}
void PM_AddEvent(playerState_s *,int event) {if(event==EV_RELOAD_ADDAMMO) {++ammoEvents; ammoAt=elapsed;}}
void PM_SetReloadingState(playerState_s *); void PM_SetWeaponReloadAddAmmoDelay(playerState_s *); int PM_Weapon_AllowReload(playerState_s *); void PM_Weapon_ReloadDelayedAction(playerState_s *); void PM_ReloadClip(playerState_s *);
'''
tests=r'''
void bolt(bool enabled,int client) {
 perk=enabled; definition=WeaponDef{}; ammoEvents=0; ammoAt=-1; elapsed=0;
 playerState_s ps; ps.clientNum=client; ps.ammo[1]=20; ps.weaponrechamber[0]=1; pmove_t pm{&ps};
 PM_SetReloadingState(&ps);
 const int expected=enabled && client==0 ? 1500:3000;
 assert(ps.weaponTime==expected);
 while(ps.weaponstate!=WEAPON_READY && elapsed<4000) {
  ++elapsed; if(ps.weaponTime>0)--ps.weaponTime;
  bool delayed=false; if(ps.weaponDelay>0) delayed=(--ps.weaponDelay==0);
  PM_Weapon_FinishReload(&pm,delayed);
 }
 assert(elapsed==expected && ammoEvents==1 && ps.ammoclip[1]==5);
 assert(ammoAt>0 && ammoAt<elapsed);
 assert(definition.iReloadTime==3000 && definition.iRechamberBoltTime==500);
}
void segmented(bool enabled,int client) {
 perk=enabled; definition=WeaponDef{}; definition.bSegmentedReload=true;
 const int divisor=enabled && client==0 ? 2:1;
 playerState_s ps; ps.clientNum=client; ps.ammo[1]=20; pmove_t pm{&ps}; PM_BeginWeaponReload(&ps);
 assert(ps.weaponTime==1000/divisor && ps.weaponDelay==800/divisor);
 ps.weaponTime=0; ps.weaponDelay=0; ps.weaponstate=WEAPON_RELOAD_START_INTERUPT; ps.ammoclip[1]=1;
 PM_Weapon_FinishReloadStart(&pm,0); assert(ps.weaponstate==WEAPON_RELOAD_END && ps.weaponTime==600/divisor);
 ps.weaponTime=0; ps.weaponstate=WEAPON_RELOADING_INTERUPT;
 PM_Weapon_FinishReload(&pm,0); assert(ps.weaponstate==WEAPON_RELOAD_END && ps.weaponTime==600/divisor);
}
int main() {
 bolt(true,0); bolt(false,0); bolt(true,1);
 segmented(true,0); segmented(false,0); segmented(true,1);
}
'''
compiler=['xcrun','clang++'] if shutil.which('xcrun') else shlex.split(os.environ.get('CXX','clang++'))
with tempfile.TemporaryDirectory(prefix='reload-timing-') as directory:
 folder=Path(directory); code=folder/'test.cpp'; executable=folder/('test.exe' if os.name=='nt' else 'test')
 code.write_text(stubs+'\n'.join(functions)+tests)
 subprocess.run(compiler+['-std=c++17',str(code),'-o',str(executable)],check=True)
 subprocess.run([str(executable)],check=True)
print('Production reload timing: bolt ammo precedes completion; segmented stages scale; Campaign and other clients retain stock timing')
