#include "mw3_combat_adapter.h"
#include "mw3_definition_loader.h"
#include <mutex>
#include <string>
#include <cstdlib>
#include <algorithm>
#include <cerrno>
#include <climits>
#include <cstdlib>
#include <cmath>
namespace {
void ensure_ios_definitions_loaded() {
#if defined(__APPLE__)
 static std::once_flag load_once;
 std::call_once(load_once, [] {
  const char* home=std::getenv("HOME");
  if(home && *home) {
   const std::string path=std::string(home)+"/Documents/mw3_gameplay.tsv";
   mw3_load_definitions_tsv(path.c_str());
  }
 });
#endif
}
bool read_integer(MW3Mode mode,MW3Category category,const char* id,const char* key,int& result){
 char buffer[48]={};
 if(!mw3_resolve_string(mode,category,id,key,buffer,sizeof(buffer))) return false;
 char* end=nullptr;errno=0;
 const long value=std::strtol(buffer,&end,10);
 if(errno || end==buffer || *end || value<INT_MIN || value>INT_MAX) return false;
 result=static_cast<int>(value);return true;
}
}
extern "C" int mw3_optional_weapon_damage(MW3Mode mode,const char* weapon,int original) {
 ensure_ios_definitions_loaded();
 if(!weapon||!*weapon||original<=0) return original;
 int replacement=0;
 if(!read_integer(mode,MW3_WEAPON,weapon,"damage",replacement)||replacement<=0) return original;
 return std::clamp(replacement,1,100000);
}
extern "C" int mw3_optional_reload_ms(MW3Mode mode,const char* weapon,int original) {
 if(!weapon||!*weapon||original<0) return original;
 int replacement=0;
 if(!read_integer(mode,MW3_WEAPON,weapon,"reload_ms",replacement)||replacement<0) return original;
 return std::clamp(replacement,0,120000);
}
