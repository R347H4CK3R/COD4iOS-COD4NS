#!/usr/bin/env python3
"""Execute production asset gating and imported-gun grants without retail data."""
from pathlib import Path
import os, shlex, shutil, subprocess, tempfile
root=Path(__file__).resolve().parents[4]
native=(root/'ports/ios/survival/survival_engine.cpp').read_text()
def extract(name):
    start=native.index(name); opening=native.index('{',start); depth=1; end=opening+1
    while depth:
        depth+=(native[end]=='{')-(native[end]=='}'); end+=1
    return native[start:end]+'\n'
code=r'''
#include <cassert>
#include <cstring>
#include "ports/ios/survival/SurvivalSession.hpp"
#include <map>
#include <string>
using namespace cod4ios::survival;
bool mode=true, loaded=false, giveWorks=true;
bool selected() { return mode; }
struct WeaponDef {const char* szInternalName;};
union XAssetHeader {WeaponDef* weapon;};
enum {ASSET_TYPE_WEAPON};
void DB_EnumXAssets(int,void(*callback)(XAssetHeader,void*),void* context,bool) {
    WeaponDef stock{"m4_grunt"}, imported{"mw3_acr"}, usp{"mw3_usp45"}, mp7{"mw3_mp7"};
    callback(XAssetHeader{&stock},context);
    if(loaded) {callback(XAssetHeader{&imported},context);callback(XAssetHeader{&usp},context);callback(XAssetHeader{&mp7},context);}
}
int gate=-1;
std::map<std::string,int> dvars;
unsigned primary=0,secondary=0,equipment=0,perk=0,rank=1;
bool loadoutValid=false;
unsigned currentRank() {return rank;}
void loadMW3Rules() {}
void loadConfig() {}
void Dvar_SetIntByName(const char* name,int value) { dvars[name]=value; if(!strcmp(name,"kisak_survival_acr")) gate=value; }
struct Client {struct {unsigned weapons[4]{},weaponmodels[128]{};} ps;} client;
struct gentity_s {struct {bool inuse=true;} r; Client* client=nullptr; int health=100;};
gentity_s g_entities[1]; struct {unsigned armor=0;} status;
unsigned BG_GetNumWeapons() {return 3;}
unsigned BG_FindWeaponIndexForName(const char* name) {return !strcmp(name,"mw3_acr") ? loaded?2:0 : 1;}
int ammoGrants=0;
int Add_Ammo(gentity_s*,unsigned,unsigned,int,int) {++ammoGrants;return 1;}
template<class T> bool G_GivePlayerWeapon(T* ps,unsigned weapon,int) {
    if(!giveWorks) return false;
    ps->weapons[weapon>>5]|=1u<<(weapon&31);return true;
}
'''+extract('bool importedWeaponAssetPresent(const char *name) {')+extract('bool importedAcrAssetPresent()')+extract('bool validateLoadout()')+extract('const char *KisakSurvival_LevelScript(')+extract('bool grantWeapon(')+extract('bool grant(Purchase item)')+r'''
int main() {
 const char *campaign="maps/bog_a";
 mode=false; loaded=true;
 assert(KisakSurvival_LevelScript(campaign)==campaign && gate==-1);
 mode=true; loaded=false;
 assert(!strcmp(KisakSurvival_LevelScript(campaign),"maps/specops_survival_v4") && gate==0);
 loaded=true; assert(!strcmp(KisakSurvival_LevelScript(campaign),"maps/specops_survival_v4") && gate==1);
 assert(loadoutValid && dvars["kisak_survival_primary"]==0);
 primary=2; rank=13; assert(!validateLoadout()); rank=14; assert(validateLoadout());
 primary=1; rank=12; assert(!validateLoadout()); rank=13; assert(validateLoadout());
 primary=3; secondary=1; rank=1; assert(validateLoadout());
 perk=1; assert(!validateLoadout()); rank=4; assert(validateLoadout());
 perk=2; assert(!validateLoadout()); rank=6; assert(validateLoadout());
 primary=0; assert(!validateLoadout()); secondary=0; assert(validateLoadout());
 primary=5; assert(!validateLoadout()); primary=0; perk=0;
 g_entities[0].client=&client;
 Session session;session.begin();session.addCredits(6000);
 loaded=false;assert(!session.tryPurchase(Purchase::ACR,[]{return grant(Purchase::ACR);}) && session.snapshot().credits==6000);
 loaded=true;giveWorks=false;
 assert(!session.tryPurchase(Purchase::ACR,[]{return grant(Purchase::ACR);}) && session.snapshot().credits==6000 && ammoGrants==0);
 giveWorks=true;assert(session.tryPurchase(Purchase::ACR,[]{return grant(Purchase::ACR);}) && session.snapshot().credits==3000 && ammoGrants==1);
 assert(!session.tryPurchase(Purchase::ACR,[]{return grant(Purchase::ACR);}) && session.snapshot().credits==3000);
 client.ps.weapons[0]=0;
 assert(session.trySpend(250,[]{return grantWeapon("mw3_usp45");}) && session.snapshot().credits==2750);
 assert(!session.trySpend(250,[]{return grantWeapon("mw3_usp45");}) && session.snapshot().credits==2750);
 client.ps.weapons[0]=0; loaded=false;
 assert(!session.trySpend(2000,[]{return grantWeapon("mw3_mp7");}) && session.snapshot().credits==2750);
 loaded=true; assert(session.trySpend(2000,[]{return grantWeapon("mw3_mp7");}) && session.snapshot().credits==750);
 client.ps.weapons[0]=0;g_entities[0].health=0;
 assert(!session.tryPurchase(Purchase::ACR,[]{return grant(Purchase::ACR);}) && session.snapshot().credits==750);
}
'''
compiler=['xcrun','clang++'] if shutil.which('xcrun') else shlex.split(os.environ.get('CXX','clang++'))
with tempfile.TemporaryDirectory(prefix='imported-weapon-') as directory:
    folder=Path(directory); source=folder/'test.cpp'; executable=folder/('test.exe' if os.name=='nt' else 'test')
    source.write_text(code)
    subprocess.run(compiler+['-std=c++17','-I',str(root),str(source),'-o',str(executable)],check=True)
    subprocess.run([str(executable)],check=True)
print('Imported weapons and Create-a-Class: exact asset gates, USP/MP7/ACR grant transactions, rank/perk validation and Campaign isolation passed')
