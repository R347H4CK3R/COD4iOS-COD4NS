#include "loading_state.hpp"
#include <cassert>
int main() {
 using namespace kisak::loading;
 assert(state(false,true,false,false,0)==Result::Loading);
 assert(state(true,true,false,false,20)==Result::Loading);
 assert(state(true,false,false,false,2)==Result::Loading);
 assert(state(true,false,false,true,2)==Result::Ready);
 assert(state(true,false,true,false,200)==Result::Failed);
 assert(state(false,true,false,false,89.9)==Result::Loading);
 assert(state(false,true,false,false,90)==Result::TimedOut);
 assert(state(true,false,false,true,200)==Result::Ready);
}
