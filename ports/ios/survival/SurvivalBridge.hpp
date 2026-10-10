#pragma once
#include "SurvivalSession.hpp"
#include <cstdint>
#include <vector>
namespace cod4ios::survival {
enum class Action { OpenShop, CloseShop, Ammo, Armor, Rifle, Retry, Deposit, Withdraw, Pack, God, InfiniteAmmo, Money, NextWave, Revive, Recovery, FastReload, ACR };
struct Status {
    Snapshot match{Phase::Idle,0,0,0,0,0,0};
    bool active=false, shopOpen=false;
    unsigned bestWave=0, armor=0;
    unsigned bank=0, xp=0, rank=1, packTier=0, map=0, difficulty=1, playerClass=0;
    bool godMode=false, infiniteAmmo=false;
    bool reviveReady=false, quickRecovery=false, fastReload=false;
    unsigned killstreak=0;
    bool acrAvailable=false;
    std::uint64_t noticeSerial=0;
    std::uint64_t epoch=0;
    char message[192]{};
};
struct Request { Action action; std::uint64_t epoch; unsigned amount=0; };
Status readStatus();
bool queueAction(Action action,std::uint64_t epoch,unsigned amount=0);
std::vector<Request> takeActions();
void publishStatus(const Status &status);
void resetBridge();
// A mode change is consumed at the safe start of Com_Frame, never in an entity update.
void requestSinglePlayerMode(bool survival);
int takeModeRequest(); // -1 none, 0 campaign, 1 survival
inline bool shopRequestPending(const Status &now,const Status &requested) {
    return now.active && now.epoch==requested.epoch && (now.match.phase==Phase::Intermission || now.match.phase==Phase::Fighting);
}
}
