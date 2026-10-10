#pragma once
#include <algorithm>
#include <limits>
namespace cod4ios::survival {
// Match-only perks. Adapter checks a live player and calls buy* inside
// Session::trySpend(cost, callback); rejected grants never debit credits.
class Armory {
 bool revive_=false, recovery_=false, fastReload_=false;
public:
 static constexpr unsigned reviveCost=1500, recoveryCost=2000, fastReloadCost=2500;
 bool canBuyRevive(unsigned rank) const { return rank>=2 && !revive_; }
 bool buyRevive(unsigned rank) { if(!canBuyRevive(rank)) return false; revive_=true; return true; }
 bool canBuyRecovery(unsigned rank) const { return rank>=4 && !recovery_; }
 bool buyRecovery(unsigned rank) { if(!canBuyRecovery(rank)) return false; recovery_=true; return true; }
 bool consumeRevive() { if(!revive_) return false; revive_=false; return true; }
 bool reviveReady() const { return revive_; }
 bool recoveryEnabled() const { return recovery_; }
 bool canBuyFastReload(unsigned rank) const { return rank>=6 && !fastReload_; }
 bool buyFastReload(unsigned rank) { if(!canBuyFastReload(rank)) return false; fastReload_=true; return true; }
 bool fastReloadEnabled() const { return fastReload_; }
 void reset() { revive_=recovery_=fastReload_=false; }
};
// Life-only streaks: adapter calls kill only for tracked player kills. Damage
// and new waves do not reset them; reset on death and new match. Cheat removal
// must never call kill. Actual count saturates at unsigned max; awards fire once.
class Killstreaks {
 unsigned kills_=0;
public:
 enum Award : unsigned { Supply=1, Armor=2, ReserveCash=4 };
 void reset() { kills_=0; }
 unsigned count() const { return kills_; }
 unsigned kill() {
  if(kills_==std::numeric_limits<unsigned>::max()) return 0;
  ++kills_;
  return kills_==5?Supply:kills_==8?Armor:kills_==12?ReserveCash:0;
 }
};
// Engine awards returned cash via Session::addCredits. Only tracked player kills
// call kill(), and actual incoming player damage calls damaged(). A skipped wave
// must not call completeWave(). Wave IDs increase within a match; reset on retry.
class Rewards {
 unsigned wave_=0, completed_=0, chain_=0;
 bool active_=false, flawless_=true;
public:
 void reset() { wave_=completed_=chain_=0; active_=false; flawless_=true; }
 void beginWave(unsigned wave) {
  if(!wave || wave<=wave_) return;
  wave_=wave; chain_=0; flawless_=true; active_=true;
 }
 void abandonWave() { active_=false; chain_=0; }
 void damaged() { if(active_) { chain_=0; flawless_=false; } }
 unsigned kill() {
  if(!active_) return 0;
  if(++chain_==5) { chain_=0; return 100; }
  return 0;
 }
 unsigned completeWave(unsigned wave) {
  if(!active_ || wave!=wave_ || wave<=completed_) return 0;
  active_=false; completed_=wave;
  return 100u+std::min(wave,100u)*25u+(flawless_?150u:0u);
 }
};
}
