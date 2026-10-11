#include "../core/mw3_survival_waves.h"
#include <cassert>
int main() {
 mw3::SurvivalWaves game;assert(!game.advance_wave());assert(game.start());assert(!game.start());
 assert(game.spawn_budget()==5);assert(game.spawn(10)==5);assert(game.pending_spawns()==0);
 assert(!game.advance_wave());assert(game.enemy_killed(5));assert(game.advance_wave());
 assert(game.spawn_budget()==7);assert(game.spawn(3)==3);assert(!game.enemy_killed(5));
 assert(game.enemy_killed(3));assert(!game.advance_wave());assert(game.spawn(10)==4);
 assert(game.enemy_killed(4));assert(game.advance_wave());assert(game.state().wave==3);
}
