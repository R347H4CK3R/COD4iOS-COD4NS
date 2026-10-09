#include "../SurvivalRuntime.hpp"
#include "../ModeCatalog.hpp"
#include "../../engine/controller_input.h"
#include <cassert>
#include <limits>
using namespace cod4ios::survival;
int main() {
    Session s;
    s.begin();
    s.tick(std::numeric_limits<double>::quiet_NaN());
    s.tick(std::numeric_limits<double>::infinity());
    assert(s.snapshot().secondsRemaining == 3);
    s.tick(3);
    assert(s.consumeSpawnBudget(20) == 11);
    for (unsigned i=0; i<11; ++i) s.onEnemyKilled();
    s.tick(.05);
    assert(s.snapshot().bestCompletedWave == 1);
    unsigned grants=0;
    assert(!s.tryPurchase(Purchase::Rifle, [&]{++grants; return false;}));
    assert(grants == 1 && s.snapshot().credits == 1100);
    assert(s.tryPurchase(Purchase::Rifle, [&]{++grants; return true;}));
    assert(s.snapshot().credits == 350);
    assert(!s.tryPurchase(Purchase::Armor, [&]{++grants; return true;}));
    assert(!s.tryPurchase(static_cast<Purchase>(99), [&]{++grants; return true;}));
    assert(grants == 2);
    s.onPlayerDied(); s.refundFailedSpawns(999);
    assert(s.snapshot().phase == Phase::GameOver && s.snapshot().spawnRemaining == 0);
    Runtime r;
    r.begin(); r.tick(3);
    assert(r.reserve(20) == 11);
    assert(r.spawned(4, 2));
    assert(!r.spawned(4, 2));
    assert(!r.killed(4, 1, true));
    assert(r.killed(4, 2, true));
    assert(!r.killed(4, 2, true));
    assert(r.session().snapshot().credits == 100);
    assert(r.spawned(4, 3));
    assert(!r.removed(4, 2));
    assert(r.removed(4, 3));
    assert(r.session().snapshot().credits == 100);
    r.refund(9); r.tick(.1);
    assert(r.session().snapshot().phase == Phase::Fighting);
    assert(r.session().snapshot().spawnRemaining == 9);
    r.shutdown(); assert(r.session().snapshot().phase == Phase::Idle);
    assert(cod4ios::modes::fromSavedId("sp") == cod4ios::modes::Mode::Campaign);
    assert(cod4ios::modes::fromSavedId("mp") == cod4ios::modes::Mode::Multiplayer);
    assert(cod4ios::modes::fromSavedId("bad") == cod4ios::modes::Mode::Campaign);
    kisak::controller::ButtonState buttons;
    buttons.Update(0,true,false);
    assert(buttons.Update(1,true,false).pressed == 1);
    assert(buttons.Update(1,true,true).released == 1);
    assert(buttons.Update(1,true,false).pressed == 0);
    buttons.Update(0,true,false);
    assert(buttons.Update(1,true,false).pressed == 1);
}
