#include "../SurvivalArmory.hpp"
#include <cassert>
using namespace cod4ios::survival;
int main() {
 Armory a; assert(Armory::fastReloadCost==2500);
 assert(!a.canBuyFastReload(5) && !a.buyFastReload(5) && !a.fastReloadEnabled());
 assert(a.canBuyFastReload(6) && a.buyFastReload(6) && a.fastReloadEnabled());
 assert(!a.canBuyFastReload(50) && !a.buyFastReload(50));
 a.reset(); assert(!a.fastReloadEnabled() && a.canBuyFastReload(6));
 Killstreaks streak;
 for(unsigned n=1;n<=20;++n) {
  const unsigned expected=n==5?Killstreaks::Supply:n==8?Killstreaks::Armor:n==12?Killstreaks::ReserveCash:0;
  assert(streak.kill()==expected && streak.count()==n);
 }
 streak.reset(); assert(streak.count()==0);
 for(unsigned n=1;n<5;++n) assert(streak.kill()==0);
 assert(streak.kill()==Killstreaks::Supply);
 streak.reset(); assert(streak.count()==0); assert(streak.kill()==0);
}

