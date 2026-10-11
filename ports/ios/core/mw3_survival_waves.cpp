#include "mw3_survival_waves.h"
#include <algorithm>
namespace mw3 {
bool SurvivalWaves::start() {if(state_.started)return false;state_.started=true;state_.wave=1;return true;}
int SurvivalWaves::spawn_budget() const {return state_.started?std::min(rules_.maximum,rules_.base_enemies+(state_.wave-1)*rules_.increment):0;}
int SurvivalWaves::pending_spawns() const {return std::max(0,spawn_budget()-state_.spawned);}
int SurvivalWaves::spawn(int count) {
 if(!state_.started||count<=0)return 0;
 int n=std::min({count,pending_spawns(),std::max(0,rules_.simultaneous-state_.alive)});
 state_.spawned+=n;state_.alive+=n;return n;
}
bool SurvivalWaves::enemy_killed(int count) {
 if(!state_.started||count<1||count>state_.alive)return false;
 state_.alive-=count;state_.killed+=count;return true;
}
bool SurvivalWaves::advance_wave() {
 if(!state_.started||state_.alive!=0||pending_spawns()!=0)return false;
 ++state_.wave;state_.spawned=0;state_.killed=0;return true;
}
}
