#include "../SurvivalBridge.hpp"
#include <cassert>
using namespace cod4ios::survival;
int main() {
    resetBridge(); auto s=readStatus();
    assert(!queueAction(Action::Ammo,s.epoch));
    s.active=true; s.gameplayReady=true; publishStatus(s);
    assert(readStatus().gameplayReady);
    assert(!queueAction(Action::Ammo,s.epoch+1));
    assert(!queueAction(static_cast<Action>(99),s.epoch));
    for(unsigned i=0;i<32;++i) assert(queueAction(Action::Ammo,s.epoch));
    assert(!queueAction(Action::Ammo,s.epoch));
    assert(takeActions().size()==32); assert(takeActions().empty());
    assert(queueAction(Action::Retry,s.epoch)); resetBridge();
    assert(takeActions().empty()); assert(readStatus().epoch!=s.epoch && !readStatus().gameplayReady);
    s.match.phase=Phase::Intermission;
    auto next=s;
    assert(shopRequestPending(next,s));
    next.match.phase=Phase::Fighting;
    assert(shopRequestPending(next,s));
    next.match.phase=Phase::GameOver; assert(!shopRequestPending(next,s));
    next=s; ++next.epoch; assert(!shopRequestPending(next,s));
    s=readStatus(); s.active=true; publishStatus(s);
    assert(queueAction(Action::Deposit,s.epoch,500));
    auto transfer=takeActions(); assert(transfer.size()==1 && transfer[0].amount==500);
    assert(takeModeRequest()==-1);
    requestSinglePlayerMode(true); assert(takeModeRequest()==1);
    requestSinglePlayerMode(false); resetBridge(); assert(takeModeRequest()==0);
}
