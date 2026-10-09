#pragma once
// Engine-independent Survival rules. No proprietary game data or engine hooks.
// Integration must call startWave(), consumeSpawnBudget(), onEnemyKilled(),
// onEnemyRemoved() and tick() from the COD4 single-player game loop.
#include <algorithm>
#include <cstdint>
#include <cmath>
#include <limits>

namespace cod4ios::survival {
enum class Phase { Idle, Intermission, Fighting, GameOver };
enum class Purchase { Ammo, Armor, Rifle };
constexpr unsigned price(Purchase item) {
  switch(item) {
    case Purchase::Ammo: return 250;
    case Purchase::Armor: return 500;
    case Purchase::Rifle: return 750;
  }
  return 0;
}
struct Snapshot {
  Phase phase;
  unsigned wave;
  unsigned alive;
  unsigned spawnRemaining;
  unsigned credits;
  double secondsRemaining;
  unsigned bestCompletedWave;
};
class Session {
  Phase phase_ = Phase::Idle;
  unsigned wave_ = 0, alive_ = 0, remaining_ = 0, credits_ = 0;
  double timer_ = 0.0;
  unsigned best_ = 0, killReward_ = 100;
  static constexpr unsigned maxAlive_ = 12;
  static constexpr double intermissionSeconds_ = 10.0;
public:
  void reset() { phase_=Phase::Idle; wave_=alive_=remaining_=credits_=best_=0; timer_=0; }
  void begin() { reset(); phase_=Phase::Intermission; timer_=3.0; }
  Snapshot snapshot() const { return {phase_,wave_,alive_,remaining_,credits_,timer_,best_}; }
  void tick(double dt) {
    if(!std::isfinite(dt) || dt<=0) return;
    if(phase_==Phase::Intermission) {
      timer_=std::max(0.0,timer_-dt);
      if(timer_==0.0) startWave();
    } else if(phase_==Phase::Fighting && alive_==0 && remaining_==0) {
      best_=std::max(best_,wave_);
      phase_=Phase::Intermission;
      timer_=intermissionSeconds_;
    }
  }
  // Returns number of enemy actors the engine may request this update.
  unsigned consumeSpawnBudget(unsigned availableActorSlots) {
    if(phase_!=Phase::Fighting) return 0;
    const unsigned freeSlots=maxAlive_-std::min(alive_,maxAlive_);
    const unsigned n=std::min({remaining_,freeSlots,availableActorSlots});
    remaining_-=n;
    alive_+=n;
    return n;
  }
  // Call if the engine failed to create requested actors; restores the budget.
  void refundFailedSpawns(unsigned count) {
    if(phase_!=Phase::Fighting) return;
    const unsigned n=std::min(count,alive_);
    alive_-=n;
    remaining_+=n;
  }
  void onEnemyKilled() { if(phase_==Phase::Fighting && alive_>0) { --alive_; addCredits(killReward_); } }
  void onEnemyRemoved() { if(phase_==Phase::Fighting && alive_>0) --alive_; }
  void skipWave() {
    if(phase_!=Phase::Fighting) return;
    alive_=remaining_=0;
    phase_=Phase::Intermission;
    timer_=intermissionSeconds_;
  }
  void onPlayerDied() { phase_=Phase::GameOver; timer_=0; remaining_=0; }
  void configureReward(unsigned reward) { killReward_=std::min(reward,10000u); }
  void addCredits(unsigned amount) { credits_+=std::min(amount,std::numeric_limits<unsigned>::max()-credits_); }
  bool spendCredits(unsigned amount) {
    if((phase_!=Phase::Fighting && phase_!=Phase::Intermission) || !amount || credits_<amount) return false;
    credits_-=amount; return true;
  }
  template<class Grant> bool trySpend(unsigned amount, Grant grant) {
    if((phase_!=Phase::Fighting && phase_!=Phase::Intermission) || !amount || credits_<amount) return false;
    if(!grant()) return false;
    credits_-=amount; return true;
  }
  bool purchase(Purchase item) { return spendCredits(price(item)); }
  template<class Grant> bool tryPurchase(Purchase item, Grant grant) { return trySpend(price(item),grant); }
private:
  void startWave() {
    if(wave_<std::numeric_limits<unsigned>::max()) ++wave_;
    // Conservative, bounded scaling; stronger enemies can be added by adapter.
    remaining_=8u+std::min(wave_,37u)*3u;
    remaining_=std::min(remaining_,120u);
    alive_=0;
    timer_=0.0;
    phase_=Phase::Fighting;
  }
};
} // namespace cod4ios::survival
