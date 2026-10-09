// Standalone smoke test: c++ -std=c++17 -Wall -Wextra -pedantic -I. ports/ios/survival/tests/session_smoke.cpp -o /tmp/survival_smoke && /tmp/survival_smoke
#include "../SurvivalSession.hpp"
#include <cassert>
using namespace cod4ios::survival;
int main() {
  Session s;
  assert(s.snapshot().phase==Phase::Idle);
  s.begin();
  assert(s.snapshot().phase==Phase::Intermission);
  assert(!s.purchase(Purchase::Ammo));
  s.tick(3);
  assert(s.snapshot().wave==1 && s.snapshot().spawnRemaining==11);
  assert(s.consumeSpawnBudget(4)==4 && s.snapshot().alive==4);
  s.refundFailedSpawns(1);
  assert(s.snapshot().alive==3 && s.snapshot().spawnRemaining==8);
  s.consumeSpawnBudget(100);
  assert(s.snapshot().alive==11 && s.snapshot().spawnRemaining==0);
  for(int i=0;i<11;++i) s.onEnemyKilled();
  assert(s.snapshot().credits==1100);
  s.tick(0.016);
  assert(s.snapshot().phase==Phase::Intermission);
  assert(s.purchase(Purchase::Ammo));
  assert(s.purchase(Purchase::Armor));
  assert(!s.purchase(Purchase::Armor));
  s.tick(10);
  assert(s.snapshot().wave==2);
  s.onPlayerDied();
  assert(s.snapshot().phase==Phase::GameOver);
  assert(s.consumeSpawnBudget(10)==0);
}
