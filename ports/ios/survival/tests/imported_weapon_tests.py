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
using namespace cod4ios::survival;
bool mode=true, loaded=false, giveWorks=true;
bool selected() { return mode; }
struct WeaponDef {const char* szInternalName;};
union XAssetHeader {WeaponDef* weapon;};
enum {ASSET_TYPE_WEAPON};
void DB_EnumXAssets(int,void(*callback)(XAssetHeader,void*),void* context,bool) {
    WeaponDef stock{"m4_grunt"}, imported{"mw3_acr"};
    callback(XAssetHeader{&stock},context);
    if(loaded) callback(XAssetHeader{&imported},context);
}
int gate=-1;
void Dvar_SetIntByName(const char*,int value) {gate=value;}
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
'''+extract('bool importedAcrAssetPresent()')+extract('const char *KisakSurvival_LevelScript(')+extract('bool grant(Purchase item)')+r'''
int main() {
 const char *campaign="maps/bog_a";
 mode=false; loaded=true;
 assert(KisakSurvival_LevelScript(campaign)==campaign && gate==-1);
 mode=true; loaded=false;
 assert(!strcmp(KisakSurvival_LevelScript(campaign),"maps/specops_survival_v3") && gate==0);
 loaded=true; assert(!strcmp(KisakSurvival_LevelScript(campaign),"maps/specops_survival_v3") && gate==1);
 g_entities[0].client=&client;
 Session session;session.begin();session.addCredits(6000);
 loaded=false;assert(!session.tryPurchase(Purchase::ACR,[]{return grant(Purchase::ACR);}) && session.snapshot().credits==6000);
 loaded=true;giveWorks=false;
 assert(!session.tryPurchase(Purchase::ACR,[]{return grant(Purchase::ACR);}) && session.snapshot().credits==6000 && ammoGrants==0);
 giveWorks=true;assert(session.tryPurchase(Purchase::ACR,[]{return grant(Purchase::ACR);}) && session.snapshot().credits==3000 && ammoGrants==1);
 assert(!session.tryPurchase(Purchase::ACR,[]{return grant(Purchase::ACR);}) && session.snapshot().credits==3000);
 client.ps.weapons[0]=0;g_entities[0].health=0;
 assert(!session.tryPurchase(Purchase::ACR,[]{return grant(Purchase::ACR);}) && session.snapshot().credits==3000);
}
'''
compiler=['xcrun','clang++'] if shutil.which('xcrun') else shlex.split(os.environ.get('CXX','clang++'))
with tempfile.TemporaryDirectory(prefix='imported-weapon-') as directory:
    folder=Path(directory); source=folder/'test.cpp'; executable=folder/('test.exe' if os.name=='nt' else 'test')
    source.write_text(code)
    subprocess.run(compiler+['-std=c++17','-I',str(root),str(source),'-o',str(executable)],check=True)
    subprocess.run([str(executable)],check=True)
print('Imported ACR: exact loaded-asset precache gate, Campaign isolation, absent/dead/failed/duplicate purchases preserve cash')
