#pragma once
namespace cod4ios::survival {
// Own only the pause we acquired, restoring the prior state across all exits.
class PauseLease {
    int previous_=0; bool owned_=false;
public:
    template<class Set> void update(bool wanted,int current,Set set) {
        if(wanted) {
            if(!owned_) { previous_=current; owned_=true; }
            if(current!=1) set(1);
        } else if(owned_) { owned_=false; set(previous_); }
    }
    bool owned() const { return owned_; }
};
}
