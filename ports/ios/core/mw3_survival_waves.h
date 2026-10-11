#pragma once
namespace mw3 {
struct SurvivalState {
 int wave=0;
 int spawned=0;
 int alive=0;
 int killed=0;
 bool started=false;
};
struct SurvivalRules {
 int base_enemies=5;
 int increment=2;
 int maximum=35;
 int simultaneous=8;
};
class SurvivalWaves {
public:
 explicit SurvivalWaves(SurvivalRules rules={}):rules_(rules){}
 bool start();
 int spawn_budget() const;
 int pending_spawns() const;
 int spawn(int count);
 bool enemy_killed(int count=1);
 bool advance_wave();
 const SurvivalState& state() const {return state_;}
private:
 SurvivalRules rules_;
 SurvivalState state_;
};
}
