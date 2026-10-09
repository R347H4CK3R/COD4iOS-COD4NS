#pragma once
#include "SurvivalSession.hpp"
#include <cstdint>
#include <vector>
namespace cod4ios::survival {
enum class Action { OpenShop, CloseShop, Ammo, Armor, Rifle, Retry };
struct Status {
    Snapshot match{Phase::Idle,0,0,0,0,0,0};
    bool active=false, shopOpen=false;
    unsigned bestWave=0, armor=0;
    std::uint64_t epoch=0;
    char message[192]{};
};
struct Request { Action action; std::uint64_t epoch; };
Status readStatus();
bool queueAction(Action action,std::uint64_t epoch);
std::vector<Request> takeActions();
void publishStatus(const Status &status);
void resetBridge();
}
