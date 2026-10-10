#include "loading_state.hpp"
#include <cassert>
int main() {
 using namespace kisak::loading;
 assert(state(false,true,false,0)==Result::Loading);
 assert(state(true,true,false,20)==Result::Loading);
 assert(state(true,false,false,2)==Result::Ready);
 assert(state(true,false,true,200)==Result::Failed);
 assert(state(false,true,false,89.9)==Result::Loading);
 assert(state(false,true,false,90)==Result::TimedOut);
 assert(state(true,false,false,200)==Result::Ready);
}
