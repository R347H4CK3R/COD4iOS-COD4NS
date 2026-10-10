#pragma once
#include "SurvivalMW3Data.hpp"
#include <algorithm>
#include <sstream>

namespace cod4ios::survival::mw3 {
struct Rank { unsigned xp=0; std::string name; };
class Program {
    std::vector<Rank> ranks_;
    std::vector<Wave> waves_, repeat_;
    std::vector<LoadoutItem> loadout_;
    std::vector<ArmoryItem> armory_;
public:
    bool load(std::string_view rankText,std::string_view waveText,std::string_view armoryText,std::string &error) {
        CsvTable ranks,waves,armory;
        if(!parseCsv(rankText,ranks,error)||!parseCsv(waveText,waves,error)||!parseCsv(armoryText,armory,error)) return false;
        Program parsed;
        for(const auto &row:ranks.rows) {
            unsigned index=0,xp=0;
            if(row.empty()||!unsignedValue(row[0],index)) continue;
            if(row.size()<3||index!=parsed.ranks_.size()||!unsignedValue(row[2],xp)||
               (index==0 ? xp!=0 : xp<=parsed.ranks_.back().xp)||index>=50) {error="Invalid rank progression";return false;}
            parsed.ranks_.push_back({xp,row[1]});
        }
        for(const auto &row:waves.rows) {
            unsigned index=0;
            if(row.empty()||!unsignedValue(row[0],index)) continue;
            if(index>=1000) {
                LoadoutItem item;
                if(!decodeLoadoutItem(row,item,error)) return false;
                parsed.loadout_.push_back(std::move(item));
            } else {
                Wave wave;
                if(!decodeWave(row,wave,error)) return false;
                if(wave.number!=parsed.waves_.size()+1||wave.squadCount>120||wave.repeating>1) {error="Invalid wave sequence or budget";return false;}
                if(wave.repeating) parsed.repeat_.push_back(wave);
                parsed.waves_.push_back(std::move(wave));
            }
        }
        for(const auto &row:armory.rows) {
            unsigned index=0;
            if(row.empty()||!unsignedValue(row[0],index)) continue;
            ArmoryItem item;
            if(!decodeArmoryItem(row,item,error)) return false;
            if(parsed.armory(item.ref)) {error="Duplicate armory item";return false;}
            parsed.armory_.push_back(std::move(item));
        }
        if(parsed.ranks_.empty()||parsed.waves_.empty()||parsed.repeat_.empty()||parsed.armory_.empty()) {error="Missing MW3 progression/waves/armory";return false;}
        *this=std::move(parsed);error.clear();return true;
    }
    bool ready() const {return !ranks_.empty();}
    unsigned rankForXP(unsigned xp) const {
        unsigned rank=1;
        for(unsigned i=1;i<ranks_.size()&&xp>=ranks_[i].xp;++i) rank=i+1;
        return rank;
    }
    unsigned xpForRank(unsigned rank) const {return ranks_.empty()?0:ranks_[std::min(std::max(rank,1u),unsigned(ranks_.size()))-1].xp;}
    const std::string &rankName(unsigned xp) const {static const std::string empty;return ranks_.empty()?empty:ranks_[rankForXP(xp)-1].name;}
    Wave wave(unsigned number) const {
        if(!number||waves_.empty()) return {};
        Wave result=number<=waves_.size()?waves_[number-1]:repeat_[(number-unsigned(waves_.size())-1)%repeat_.size()];
        result.number=number;return result;
    }
    const ArmoryItem *armory(std::string_view ref) const {for(const auto &item:armory_) if(item.ref==ref)return &item;return nullptr;}
    const std::vector<LoadoutItem> &loadout() const {return loadout_;}
    static unsigned bossCount(const Wave &wave) {std::istringstream text(wave.aiBosses);std::string ref;unsigned count=0;while(text>>ref)++count;return count;}
    static std::string unsupported(const Wave &wave) {
        std::string value;
        if(!wave.specialTypes.empty()) value="special AI: "+wave.specialTypes;
        if(!wave.nonAiBosses.empty()) {if(!value.empty())value+="; ";value+="air bosses: "+wave.nonAiBosses;}
        return value;
    }
};
}
