#include "../SurvivalPause.hpp"
#include "../SurvivalUpgrades.hpp"
#include <cassert>
#include <limits>
using namespace cod4ios::survival;
int main() {
 PauseLease pause; int current=0,changes=0;
 auto set=[&](int value){current=value; ++changes;};
 pause.update(true,current,set); assert(current==1 && changes==1);
 pause.update(true,current,set); assert(changes==1);
 pause.update(false,current,set); assert(current==0 && !pause.owned());
 pause.update(false,current,set); assert(changes==2);
 current=1; pause.update(true,current,set); pause.update(false,current,set); assert(current==1);
 WeaponUpgrades guns; assert(guns.cost(0)==0 && guns.cost(128)==0);
 assert(guns.damage(1,30)==30); assert(guns.cost(1)==2000);
 assert(guns.upgrade(1) && guns.damage(1,30)==60 && guns.cost(1)==4000);
 assert(guns.damage(2,30)==30); assert(guns.upgrade(1) && guns.cost(1)==6000);
 assert(guns.upgrade(1) && guns.damage(1,30)==120 && guns.cost(1)==0);
 assert(!guns.upgrade(1)); assert(guns.damage(1,std::numeric_limits<int>::max())==std::numeric_limits<int>::max());
 assert(guns.damage(1,-10)==-10); guns.reset(); assert(guns.tier(1)==0);
}
