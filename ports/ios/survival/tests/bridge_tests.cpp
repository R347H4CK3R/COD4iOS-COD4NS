#include "../SurvivalBridge.hpp"
#include <cassert>
using namespace cod4ios::survival;
int main() {
    resetBridge(); auto s=readStatus();
    assert(!queueAction(Action::Ammo,s.epoch));
    s.active=true; publishStatus(s);
    assert(!queueAction(Action::Ammo,s.epoch+1));
    assert(!queueAction(static_cast<Action>(99),s.epoch));
    for(unsigned i=0;i<32;++i) assert(queueAction(Action::Ammo,s.epoch));
    assert(!queueAction(Action::Ammo,s.epoch));
    assert(takeActions().size()==32); assert(takeActions().empty());
    assert(queueAction(Action::Retry,s.epoch)); resetBridge();
    assert(takeActions().empty()); assert(readStatus().epoch!=s.epoch);
    s.match.phase=Phase::Intermission;
    auto next=s;
    assert(shopRequestPending(next,s));
    next.match.phase=Phase::Fighting;
    assert(!shopRequestPending(next,s));
    next=s; ++next.epoch; assert(!shopRequestPending(next,s));
    assert(takeModeRequest()==-1);
    requestSinglePlayerMode(true); assert(takeModeRequest()==1);
    requestSinglePlayerMode(false); resetBridge(); assert(takeModeRequest()==0);
}
