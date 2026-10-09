#pragma once
#include "SurvivalSession.hpp"
#include <unordered_map>
namespace cod4ios::survival {
// Engine-thread owned. Reservations become tracked actors only after spawn succeeds.
class Runtime {
    Session session_;
    std::unordered_map<unsigned,unsigned> enemies_;
    unsigned pending_=0;
public:
    Session &session() { return session_; }
    void shutdown() { enemies_.clear(); pending_=0; session_.reset(); }
    void begin() { shutdown(); session_.begin(); }
    void tick(double seconds) { session_.tick(seconds); }
    unsigned reserve(unsigned slots) { const unsigned n=session_.consumeSpawnBudget(slots); pending_+=n; return n; }
    bool spawned(unsigned slot,unsigned generation) {
        if(!pending_ || enemies_.count(slot) || session_.snapshot().phase!=Phase::Fighting) return false;
        enemies_.emplace(slot,generation); --pending_; return true;
    }
    void refund(unsigned count) {
        const unsigned n=std::min(count,pending_); pending_-=n; session_.refundFailedSpawns(n);
    }
    bool removed(unsigned slot,unsigned generation) { return killed(slot,generation,false); }
    bool killed(unsigned slot,unsigned generation,bool playerKill) {
        const auto found=enemies_.find(slot);
        if(found==enemies_.end() || found->second!=generation) return false;
        enemies_.erase(found);
        if(playerKill) session_.onEnemyKilled(); else session_.onEnemyRemoved();
        return true;
    }
};
}
