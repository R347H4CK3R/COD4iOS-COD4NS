#include "../SurvivalMW3Data.hpp"
#include <cassert>
using namespace cod4ios::survival::mw3;
int main() {
    CsvTable table; std::string error;
    assert(parseCsv("\xEF\xBB\xBF" "0,7,1,synthetic_squad,8,dog,2,jug,chopper,0,weapon equipment\r\n",table,error));
    Wave wave; assert(decodeWave(table.rows[0],wave,error));
    assert(wave.number==1 && wave.bossDelay==7 && wave.squadCount==8 && wave.armoryUnlocks=="weapon equipment");
    assert(parseCsv("1,test_ref,weapon,750,\"Name, with comma\",\"Line\n\"\"quoted\"\"\",icon,2,upgrade,,1,extra\n",table,error));
    ArmoryItem item; assert(decodeArmoryItem(table.rows[0],item,error));
    assert(item.rankIndex==2);
    assert(item.cost==750 && item.name=="Name, with comma" && item.description=="Line\n\"quoted\"");
    assert(table.find(1,"test_ref")==&table.rows[0]);
    auto previous=table.rows;
    assert(!parseCsv(std::string(128,','),table,error)); assert(table.rows==previous);
    std::string excessiveRows; excessiveRows.reserve(200002);
    for(unsigned i=0;i<100001;++i) excessiveRows+="x\n";
    assert(!parseCsv(excessiveRows,table,error)); assert(table.rows==previous);
    for(auto invalid:{"\"unterminated", "a,\"b\"oops", "a,b\"c"}) { assert(!parseCsv(invalid,table,error)); assert(table.rows==previous); }
    assert(!parseCsv(std::string("x\0y",3),table,error)); assert(table.rows==previous);
    Row bad=table.rows[0]; bad[3]="-1"; auto previousItem=item;
    assert(!decodeArmoryItem(bad,item,error)); assert(item.ref==previousItem.ref && item.cost==previousItem.cost);
    bad[3]="4294967296"; assert(!decodeArmoryItem(bad,item,error));
    unsigned value=77; assert(!unsignedValue("12oops",value) && value==77);
    assert(parseCsv("a,b,\n",table,error) && table.rows[0].size()==3 && table.rows[0][2].empty());
    assert(parseCsv("4,,5,,,,,,,1,",table,error)); assert(decodeWave(table.rows[0],wave,error));
    assert(wave.squadCount==0 && wave.bossDelay==0 && wave.repeating==1);
    LoadoutItem loadout; assert(decodeLoadoutItem(Row{"1000","weapon_1","synthetic_weapon",""},loadout,error));
    assert(loadout.slot=="weapon_1" && loadout.amount==0);
    Perk perk; assert(decodePerk(Row{"0","synthetic_perk","Name","Description","Icon","0","1"},perk,error));
    assert(perk.ref=="synthetic_perk" && perk.column6=="1");
    assert(parseCsv("",table,error) && table.rows.empty());
    assert(parseCsv("same,first\nsame,second",table,error)); assert((*table.find(0,"same"))[1]=="first");
}
