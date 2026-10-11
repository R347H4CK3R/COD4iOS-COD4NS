#include "mw3_equipment_adapter.h"
#include "mw3_combat_adapter.h"
#include <cerrno>
#include <cstdlib>
#include <cmath>
#include <climits>
#include <algorithm>
#include <cstring>
namespace {
bool integer(MW3Mode mode,MW3Category type,const char* id,const char* prop,int& out) {
 mw3_ensure_config_loaded();
 if(!id||!*id) return false;
 char str[64]{};
 if(!mw3_resolve_string(mode,type,id,prop,str,sizeof str)) return false;
 char* end=nullptr;errno=0;long n=std::strtol(str,&end,10);
 if(errno||end==str||*end||n<0||n>INT_MAX) return false;
 out=static_cast<int>(n);return true;
}
}
extern "C" int mw3_optional_fuse_ms(MW3Mode m,const char* id,int base) {
 int n=0;return integer(m,MW3_LETHAL,id,"fuse_ms",n)?std::clamp(n,0,60000):base;
}
extern "C" int mw3_optional_tactical_ms(MW3Mode m,const char* id,int base) {
 int n=0;return integer(m,MW3_TACTICAL,id,"duration_ms",n)?std::clamp(n,0,120000):base;
}
extern "C" int mw3_optional_killstreak_threshold(MW3Mode m,const char* id,int base) {
 int n=0;return integer(m,MW3_KILLSTREAK,id,"score_requirement",n)&&n>0?std::min(n,1000000):base;
}
extern "C" float mw3_optional_perk_multiplier(MW3Mode m,const char* id,const char* prop,float base) {
 mw3_ensure_config_loaded();
 if(!id||!prop||!std::isfinite(base))return base;
 if(std::strcmp(prop,"reload_multiplier")&&std::strcmp(prop,"damage_multiplier"))return base;
 char str[64]{};
 if(!mw3_resolve_string(m,MW3_PERK,id,prop,str,sizeof str))return base;
 char* end=nullptr;errno=0;float n=std::strtof(str,&end);
 return errno||end==str||*end||!std::isfinite(n)||n<=0?base:std::clamp(n,0.05f,10.0f);
}
