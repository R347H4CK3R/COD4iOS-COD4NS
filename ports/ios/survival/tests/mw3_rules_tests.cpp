#include "../SurvivalMW3Rules.hpp"
#include <cassert>
#include <fstream>
#include <iterator>
#include <iostream>
using namespace cod4ios::survival::mw3;
int main(int argc,char **argv) {
    if(argc==4) {
        auto read=[](const char *path) {std::ifstream file(path);assert(file.good());return std::string(std::istreambuf_iterator<char>(file),{});};
        Program actual;std::string reason;
        if(!actual.load(read(argv[1]),read(argv[2]),read(argv[3]),reason)) {std::cerr<<reason;return 1;}
        assert(actual.rankForXP(7199)==1 && actual.rankForXP(7200)==2);
        assert(actual.rankForXP(2065400)==50 && actual.xpForRank(50)==2065400);
        assert(actual.wave(1).squadCount==8 && actual.wave(28).squadCount==9);
        assert(actual.armory("iw5_acr_mp")->cost==3000);
        std::cout<<"Original MW3 rank, wave, repeat and armory tables validated\n";
        return 0;
    }
    Program p;std::string error;
    const char *ranks="idx,name,xp\n0,R1,0\n1,R2,900\n2,R3,2500\n";
    const char *waves="header\n0,1,1,easy,4,,,,,,weapon\n1,1,2,regular,5,test_dog,2,,,1,equipment\n2,0,3,hard,2,,,test_boss,test_air,1,\n1000,weapon_1,test_pistol,75\n";
    const char *armory="header\n0,test_weapon,weapon,600,NAME,DESC,ICON,1,,,,\n";
    assert(p.load(ranks,waves,armory,error));
    assert(p.rankForXP(899)==1&&p.rankForXP(900)==2&&p.rankForXP(999999)==3);
    assert(p.xpForRank(2)==900&&p.xpForRank(0)==0&&p.xpForRank(99)==2500);
    assert(p.wave(1).squadCount==4&&p.wave(4).squadCount==5&&p.wave(5).squadCount==2&&p.wave(6).squadCount==5);
    assert(p.wave(0).number==0&&p.wave(1000000).number==1000000);
    assert(p.armory("test_weapon")->cost==600&&p.armory("absent")==nullptr);
    assert(p.loadout().size()==1&&p.loadout()[0].amount==75);
    assert(!Program::unsupported(p.wave(2)).empty()&&Program::bossCount(p.wave(3))==1);
    assert(!p.load("0,R1,1",waves,armory,error));
    assert(p.rankForXP(900)==2); // failed load preserves the prior validated program
    assert(!p.load(ranks,"0,1,2,easy,4,,,,,,",armory,error));
}
