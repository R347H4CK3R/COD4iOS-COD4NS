#pragma once
#include <array>
#include <algorithm>
#include <limits>
namespace cod4ios::survival {
class WeaponUpgrades {
    std::array<unsigned,128> tiers_{};
public:
    void reset() { tiers_.fill(0); }
    unsigned tier(unsigned weapon) const { return weapon<tiers_.size() ? tiers_[weapon] : 0; }
    unsigned cost(unsigned weapon) const { return weapon && weapon<tiers_.size() && tier(weapon)<3 ? 2000*(tier(weapon)+1) : 0; }
    bool upgrade(unsigned weapon) { if(!cost(weapon)) return false; ++tiers_[weapon]; return true; }
    int damage(unsigned weapon,int original) const {
        if(original<=0) return original;
        const auto scaled=static_cast<long long>(original)*(tier(weapon)+1);
        return static_cast<int>(std::min(scaled,static_cast<long long>(std::numeric_limits<int>::max())));
    }
};
}
