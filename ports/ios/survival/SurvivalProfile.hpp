#pragma once
#include "SurvivalConfig.hpp"
#include "SurvivalSession.hpp"
#include <limits>
namespace cod4ios::survival {
struct Profile {
 unsigned bank=0, xp=0;
 void sanitize() { bank=std::min(bank,maxProgress); xp=std::min(xp,maxProgress); }
 void addXP(unsigned amount) { xp=std::min(xp,maxProgress); xp+=std::min(amount,maxProgress-xp); }
};
inline bool deposit(Session& session,Profile& profile,unsigned amount) {
 if(!amount || profile.bank>maxProgress || amount>maxProgress-profile.bank) return false;
 if(!session.spendCredits(amount)) return false;
 profile.bank+=amount; return true;
}
inline bool withdraw(Session& session,Profile& profile,unsigned amount) {
 const auto snapshot=session.snapshot();
 if(!amount || profile.bank>maxProgress || profile.bank<amount ||
    (snapshot.phase!=Phase::Fighting && snapshot.phase!=Phase::Intermission) ||
    amount>std::numeric_limits<unsigned>::max()-snapshot.credits) return false;
 session.addCredits(amount); profile.bank-=amount; return true;
}
}
