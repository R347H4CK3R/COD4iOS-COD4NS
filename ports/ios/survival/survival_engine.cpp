#include "survival_engine.h"
#include "SurvivalRuntime.hpp"
#include "SurvivalBridge.hpp"
#include "../platform/apple_engine_mode.h"
#include <game/g_main.h>
#include <game/g_local.h>
#include <game/actor.h>
#include <game/actor_spawner.h>
#include <game/actor_senses.h>
#include <game/actor_threat.h>
#include <game/actor_events.h>
#include <game/sentient.h>
#include <server/server.h>
#include <qcommon/cmd.h>
#include <qcommon/qcommon.h>
#include <universal/com_files.h>
#include <client/client.h>
#include <cstdlib>
#include <cstring>
#include <cstdio>
#include <array>

namespace {
using namespace cod4ios::survival;
Runtime runtime;
Status status;
std::array<unsigned,MAX_GENTITIES> generations{};
std::vector<int> spawners;
int lastTime=0, nextSpawn=0, lastProgress=0;
unsigned nextSpawner=0;
bool active=false, failed=false;
bool selected() { const char *value=std::getenv("KISAK_SURVIVAL_MODE"); return value && !std::strcmp(value,"1"); }
void message(const char *text) { std::snprintf(status.message,sizeof(status.message),"%s",text); }
void publish() { status.match=runtime.session().snapshot(); status.active=active; publishStatus(status); }
bool grant(Purchase item) {
    gentity_s *player=&g_entities[0];
    if(!player->r.inuse || !player->client || player->health<=0) return false;
    auto &ps=player->client->ps;
    if(item==Purchase::Armor) {
        if(status.armor==100) return false;
        status.armor=100; return true;
    }
    if(item==Purchase::Ammo) {
        bool changed=false;
        for(unsigned weapon=1;weapon<BG_GetNumWeapons() && weapon<128;++weapon) {
            if(!(ps.weapons[weapon>>5] & (1u<<(weapon&31)))) continue;
            changed|=Add_Ammo(player,weapon,ps.weaponmodels[weapon],999,1)>0;
        }
        return changed;
    }
    const unsigned rifle=BG_FindWeaponIndexForName("ak47");
    if(!rifle || rifle>=128 || (ps.weapons[rifle>>5] & (1u<<(rifle&31)))) return false;
    if(!G_GivePlayerWeapon(&ps,rifle,0)) return false;
    Add_Ammo(player,rifle,0,999,1);
    return true;
}
void processActions() {
    for(const auto &request:takeActions()) {
        if(request.epoch!=status.epoch) continue;
        const auto phase=runtime.session().snapshot().phase;
        if(request.action==Action::CloseShop) { status.shopOpen=false; continue; }
        if(request.action==Action::Retry) {
            if(phase==Phase::GameOver || failed) {
                status.shopOpen=false; active=false; publish();
                Cbuf_AddText(0,"devmap bog\n");
            }
            continue;
        }
        if(phase!=Phase::Intermission || failed) { status.shopOpen=false; continue; }
        if(request.action==Action::OpenShop) { status.shopOpen=true; continue; }
        if(!status.shopOpen) continue;
        const Purchase item=request.action==Action::Ammo ? Purchase::Ammo :
                            request.action==Action::Armor ? Purchase::Armor : Purchase::Rifle;
        if(runtime.session().tryPurchase(item,[&]{return grant(item);})) message("Purchase complete");
        else message("Purchase unavailable: check credits, ammo or inventory");
    }
}
}

const char *KisakSurvival_LevelScript(const char *original) {
    return selected() ? "maps/specops_survival" : original;
}
void KisakSurvival_Shutdown() {
    active=false; failed=false; runtime.shutdown(); spawners.clear(); resetBridge(); status=readStatus();
}
void KisakSurvival_Begin() {
    KisakSurvival_Shutdown();
    if(!selected()) return;
    active=true; runtime.begin(); status.bestWave=KisakApple_GetSurvivalBestWave();
    lastTime=nextSpawn=lastProgress=level.time; nextSpawner=0;
    // The type scripts already ran their spawner setup and precaches during G_LoadLevel.
    // Keep friendly actors; remove preplaced hostiles so they cannot bypass wave accounting.
    for(int i=1;i<level.num_entities;++i) {
        auto &ent=g_entities[i];
        if(!ent.r.inuse) continue;
        if(ent.s.eType==ET_ACTOR_SPAWNER && ent.item[0].ammoCount==TEAM_AXIS)
            spawners.push_back(i);
        else if(ent.actor && ent.sentient && ent.sentient->eTeam==TEAM_AXIS) G_FreeEntity(&ent);
    }
    if(spawners.empty()) {
        failed=true; runtime.session().onPlayerDied();
        message("No compatible hostile spawners. Check the original bog map files, then retry.");
    } else message("Survival: use Shop between waves. Controller: D-pad up opens Shop.");
    publish();
}
void KisakSurvival_Frame() {
    if(!active) return;
    processActions();
    if(!active) return;
    const int now=level.time;
    const double delta=std::clamp((now-lastTime)/1000.0,0.0,0.25); lastTime=now;
    if(!status.shopOpen && !failed) runtime.tick(delta);
    const Snapshot snapshot=runtime.session().snapshot();
    if(snapshot.bestCompletedWave>status.bestWave) {
        status.bestWave=snapshot.bestCompletedWave;
        KisakApple_RecordSurvivalBestWave(status.bestWave);
    }
    if(snapshot.phase!=Phase::Intermission) status.shopOpen=false;
    if(snapshot.phase==Phase::Fighting && snapshot.spawnRemaining && now>=nextSpawn && !failed) {
        nextSpawn=now+500;
        if(runtime.reserve(1)) {
            gentity_s *spawned=nullptr;
            for(unsigned attempt=0;attempt<spawners.size();++attempt) {
                gentity_s &spawner=g_entities[spawners[nextSpawner++%spawners.size()]];
                if(!spawner.r.inuse || spawner.s.eType!=ET_ACTOR_SPAWNER) continue;
                const auto *player=&g_entities[0];
                const float *a=spawner.r.currentOrigin, *b=player->r.currentOrigin;
                const float dx=a[0]-b[0],dy=a[1]-b[1],dz=a[2]-b[2];
                if(dx*dx+dy*dy+dz*dz<256.f*256.f) continue;
                const int oldCount=spawner.count; spawner.count=-1;
                const int oldFlags=spawner.spawnflags; spawner.spawnflags&=~2;
                spawned=SpawnActor(&spawner,0,CHECK_SPAWN,0);
                spawner.count=oldCount; spawner.spawnflags=oldFlags;
                if(spawned) break;
            }
            if(!spawned) runtime.refund(1);
            else {
                const unsigned slot=static_cast<unsigned>(spawned->s.number);
                runtime.spawned(slot,++generations[slot]);
                spawned->health=spawned->maxHealth=100+static_cast<int>(std::min(snapshot.wave-1,20u))*10;
                if(spawned->actor) {
                    spawned->actor->accuracy=std::min(.2f+.015f*std::min(snapshot.wave-1,20u),.5f);
                    spawned->actor->allowDeath=1;
                    if(g_entities[0].sentient) {
                        Actor_GetPerfectInfo(spawned->actor,g_entities[0].sentient);
                        Actor_UpdateThreat(spawned->actor);
                    }
                }
                lastProgress=now; message("");
            }
        }
        if(now-lastProgress>20000 && snapshot.alive==0) {
            failed=true; runtime.session().onPlayerDied();
            message("Enemies cannot reach a safe spawn point. Retry or return to Campaign.");
        }
    } else if(snapshot.phase==Phase::Intermission) lastProgress=now;
    publish();
}
void KisakSurvival_EnemyDied(gentity_s *enemy,gentity_s *attacker) {
    if(!active || !enemy) return;
    const unsigned slot=static_cast<unsigned>(enemy->s.number);
    if(slot>=generations.size()) return;
    runtime.killed(slot,generations[slot],attacker && attacker->client);
}
void KisakSurvival_Removed(gentity_s *enemy) {
    if(!active || !enemy) return;
    const unsigned slot=static_cast<unsigned>(enemy->s.number);
    if(slot<generations.size()) runtime.removed(slot,generations[slot]);
}
void KisakSurvival_PlayerDied() {
    if(!active) return;
    runtime.session().onPlayerDied(); status.shopOpen=false; message("Game over. Retry to start a new match."); publish();
}
int KisakSurvival_AbsorbDamage(gentity_s *player,int damage) {
    if(!active || !player || !player->client || damage<=0) return damage;
    const unsigned absorbed=std::min(status.armor,static_cast<unsigned>(damage)/2);
    status.armor-=absorbed; return damage-static_cast<int>(absorbed);
}
void KisakSurvival_PumpMode() {
    static int transition=-1;
    const int requested=takeModeRequest();
    if(requested!=-1) {
        if(requested==static_cast<int>(selected()) && transition==-1) return;
        transition=requested;
        if(com_sv_running->current.enabled) {
            // The existing disconnect command performs the engine's error-unwind teardown.
            Cbuf_AddText(0,"disconnect\n"); return;
        }
    }
    if(transition==-1 || com_sv_running->current.enabled) return;
    KisakSurvival_Shutdown();
    const bool survival=transition==1; transition=-1;
    if(survival) setenv("KISAK_SURVIVAL_MODE","1",1); else unsetenv("KISAK_SURVIVAL_MODE");
    Dvar_SetString(fs_gameDirVar,survival ? "mods/specops_survival" : "");
    // The existing menu-side renderer restart synchronizes workers, restarts the
    // filesystem when fs_game is modified, and rebuilds UI/world state.
    Cbuf_AddText(0,survival ? "vid_restart\ndevmap bog\n" : "vid_restart\n");
}
