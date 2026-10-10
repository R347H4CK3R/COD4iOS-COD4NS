#include "../SurvivalConfig.hpp"
#include "../SurvivalProfile.hpp"
#include "../SurvivalArmory.hpp"
#include <cassert>
#include <limits>
#include <cstring>
using namespace cod4ios::survival;
int main() {
 Armory armory; assert(!armory.canBuyRevive(1) && !armory.buyRevive(1));
 assert(armory.canBuyRevive(2) && armory.buyRevive(2)); assert(!armory.buyRevive(50));
 assert(armory.reviveReady()); assert(armory.consumeRevive() && !armory.consumeRevive()); assert(armory.buyRevive(2));
 assert(!armory.buyRecovery(3)); assert(armory.buyRecovery(4) && armory.recoveryEnabled()); assert(!armory.buyRecovery(50));
 armory.reset(); assert(!armory.consumeRevive() && !armory.recoveryEnabled());
 Session perks; perks.begin(); perks.addCredits(1500);
 assert(!perks.trySpend(Armory::reviveCost,[&]{return armory.buyRevive(1);}) && perks.snapshot().credits==1500);
 assert(perks.trySpend(Armory::reviveCost,[&]{return armory.buyRevive(2);}) && perks.snapshot().credits==0);
 assert(!perks.trySpend(Armory::recoveryCost,[&]{return armory.buyRecovery(4);}) && !armory.recoveryEnabled());
 Rewards rewards; assert(rewards.kill()==0 && rewards.completeWave(0)==0);
 rewards.beginWave(1); for(unsigned i=0;i<4;++i) assert(rewards.kill()==0); assert(rewards.kill()==100);
 rewards.damaged(); for(unsigned i=0;i<4;++i) assert(rewards.kill()==0); assert(rewards.kill()==100);
 assert(rewards.completeWave(2)==0 && rewards.completeWave(1)==125 && rewards.completeWave(1)==0);
 rewards.beginWave(1); assert(rewards.completeWave(1)==0); rewards.beginWave(2); assert(rewards.completeWave(2)==300);
 rewards.beginWave(std::numeric_limits<unsigned>::max()); assert(rewards.completeWave(std::numeric_limits<unsigned>::max())==2750);
 rewards.reset(); rewards.beginWave(1); rewards.abandonWave(); assert(rewards.kill()==0 && rewards.completeWave(1)==0); rewards.beginWave(2); assert(rewards.completeWave(2)==300);
 rewards.reset(); rewards.beginWave(1); assert(rewards.completeWave(1)==275);
 Config invalid{99,99,99}; invalid.sanitize(); assert(invalid.map==0 && invalid.difficulty==1 && invalid.playerClass==0);
 assert(rankForXP(0)==1 && rankForXP(499)==1 && rankForXP(500)==2 && rankForXP(1000000000)==50);
 assert(enemyHealth(999999,3)<=1000 && enemyHealth(1,0)<enemyHealth(1,3));
 assert(enemyAccuracy(999999,3)<=1.0f && killReward(1)==100);
 assert(std::strcmp(mapId(0),"bog_a")==0 && std::strcmp(mapId(4),"armada")==0);
 assert(std::strcmp(classWeapon(1),"ak47")==0 && std::strcmp(classWeapon(2),"m4_grunt")==0);
 for(unsigned d=0;d<4;++d) { assert(enemyAccuracy(0,d)>0 && enemyAccuracy(0,d)<1); assert(killXP(d)>0); }
 Profile xpProfile; xpProfile.addXP(499); assert(rankForXP(xpProfile.xp)==1); xpProfile.addXP(1); assert(rankForXP(xpProfile.xp)==2);
 xpProfile.addXP(std::numeric_limits<unsigned>::max()); assert(xpProfile.xp==maxProgress);
 Session s; Profile p; s.begin(); s.addCredits(10000);
 assert(!deposit(s,p,0) && !deposit(s,p,10001));
 assert(deposit(s,p,2500) && p.bank==2500 && s.snapshot().credits==7500);
 assert(!withdraw(s,p,2501)); assert(withdraw(s,p,500) && p.bank==2000 && s.snapshot().credits==8000);
 p.bank=1000000000; assert(!deposit(s,p,1) && s.snapshot().credits==8000);
 assert(!s.trySpend(100,[]{return false;}) && s.snapshot().credits==8000);
 assert(s.trySpend(100,[]{return true;}) && s.snapshot().credits==7900);
 s.tick(3); assert(s.spendCredits(100)); assert(s.tryPurchase(Purchase::Ammo,[]{return true;}));
 s.configureReward(150); s.begin(); s.tick(3); s.consumeSpawnBudget(1); s.onEnemyKilled(); assert(s.snapshot().credits==150);
 s.addCredits(std::numeric_limits<unsigned>::max()); assert(s.snapshot().credits==std::numeric_limits<unsigned>::max());
 p.bank=10; assert(!withdraw(s,p,1) && p.bank==10);
 s.onPlayerDied(); assert(!s.spendCredits(1) && !deposit(s,p,1));
 const auto dead=s.snapshot(); s.skipWave(); assert(s.snapshot().phase==dead.phase && s.snapshot().credits==dead.credits);
 s.reset(); s.skipWave(); assert(s.snapshot().phase==Phase::Idle); assert(!s.trySpend(1,[]{return true;}));
 s.begin(); s.skipWave(); assert(s.snapshot().phase==Phase::Intermission && s.snapshot().secondsRemaining==3); unsigned grants=0;
 assert(!s.trySpend(1,[&]{++grants; return true;}) && grants==0);
 s.configureReward(std::numeric_limits<unsigned>::max()); s.tick(3); s.consumeSpawnBudget(1); s.onEnemyKilled(); assert(s.snapshot().credits==10000);
 const auto before=s.snapshot(); s.skipWave(); assert(s.snapshot().phase==Phase::Intermission && s.snapshot().alive==0 && s.snapshot().spawnRemaining==0 && s.snapshot().credits==before.credits && s.snapshot().bestCompletedWave==before.bestCompletedWave);
 p.bank=5; assert(withdraw(s,p,5) && p.bank==0); assert(!withdraw(s,p,1));
}
