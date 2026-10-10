#include "SurvivalBridge.hpp"
#include <mutex>
namespace cod4ios::survival {
namespace { std::mutex lock; Status current; std::vector<Request> pending; int requestedMode=-1; }
Status readStatus() { std::lock_guard<std::mutex> guard(lock); return current; }
bool queueAction(Action action,std::uint64_t epoch,unsigned amount) {
    std::lock_guard<std::mutex> guard(lock);
    if(!current.active || epoch!=current.epoch || pending.size()>=32 ||
       static_cast<unsigned>(action)>static_cast<unsigned>(Action::FastReload)) return false;
    pending.push_back({action,epoch,amount}); return true;
}
std::vector<Request> takeActions() {
    std::lock_guard<std::mutex> guard(lock);
    std::vector<Request> result; result.swap(pending); return result;
}
void publishStatus(const Status &status) { std::lock_guard<std::mutex> guard(lock); current=status; }
void resetBridge() {
    std::lock_guard<std::mutex> guard(lock);
    const auto next=current.epoch+1; current=Status{}; current.epoch=next; pending.clear();
}
void requestSinglePlayerMode(bool survival) { std::lock_guard<std::mutex> guard(lock); requestedMode=survival ? 1 : 0; }
int takeModeRequest() { std::lock_guard<std::mutex> guard(lock); const int mode=requestedMode; requestedMode=-1; return mode; }
}
