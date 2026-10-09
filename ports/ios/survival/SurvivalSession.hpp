#pragma once
// Engine-independent Survival rules. No proprietary game data or engine hooks.
// Integration must call startWave(), consumeSpawnBudget(), onEnemyKilled(),
// onEnemyRemoved() and tick() from the COD4 single-player game loop.
#include <algorithm>
#include <cstdint>

namespace cod4ios::survival {
enum class Phase { Idle, Intermission, Fighting, GameOver };
enum class Purchase { Ammo, Armor };
struct Snapshot {
  Phase phase;
  unsigned wave;
  unsigned alive;
  unsigned spawnRemaining;
  unsigned credits;
  double secondsRemaining;
};
class Session {
  Phase phase_ = Phase::Idle;
  unsigned wave_ = 0, alive_ = 0, remaining_ = 0, credits_ = 0;
  double timer_ = 0.0;
  static constexpr unsigned maxAlive_ = 12;
  static constexpr double intermissionSeconds_ = 10.0;
public:
  void reset() { phase_=Phase::Idle; wave_=alive_=remaining_=credits_=0; timer_=0; }
  void begin() { reset(); phase_=Phase::Intermission; timer_=3.0; }
  Snapshot snapshot() const { return {phase_,wave_,alive_,remaining_,credits_,timer_}; }
  void tick(double dt) {
    if(dt<=0) return;
    if(phase_==Phase::Intermission) {
      timer_=std::max(0.0,timer_-dt);
      if(timer_==0.0) startWave();
    } else if(phase_==Phase::Fighting && alive_==0 && remaining_==0) {
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
    const unsigned n=std::min(count,alive_);
    alive_-=n;
    remaining_+=n;
  }
  void onEnemyKilled() { if(phase_==Phase::Fighting && alive_>0) { --alive_; credits_+=100; } }
  void onEnemyRemoved() { if(phase_==Phase::Fighting && alive_>0) --alive_; }
  void onPlayerDied() { phase_=Phase::GameOver; timer_=0; }
  bool purchase(Purchase item) {
    if(phase_!=Phase::Intermission) return false;
    const unsigned price=item==Purchase::Ammo ? 250u : 500u;
    if(credits_<price) return false;
    credits_-=price;
    return true; // Caller must grant the purchased item on successful return.
  }
private:
  void startWave() {
    ++wave_;
    // Conservative, bounded scaling; stronger enemies can be added by adapter.
    remaining_=std::min(8u+wave_*3u,120u);
    alive_=0;
    timer_=0.0;
    phase_=Phase::Fighting;
  }
};
} // namespace cod4ios::survival
