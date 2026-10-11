#include "mw3_gameplay_bridge.h"
#include "mw3_gameplay_registry.h"
#include <cstring>
#include <mutex>
#include <memory>
#include <string>
namespace {
std::mutex mutex_;
std::unique_ptr<mw3::GameplayRegistry> registry(new mw3::GameplayRegistry);
bool valid_mode(MW3Mode mode) {return mode==MW3_MODE_MULTIPLAYER||mode==MW3_MODE_SPECIAL_OPS;}
bool valid_category(MW3Category c) {return c>=MW3_WEAPON&&c<=MW3_KILLSTREAK;}
}
extern "C" int mw3_register_definition(const char* id,MW3Category category,MW3Source source,unsigned int mode_mask,const char* key,const char* value) {
 if(!id||!*id||!key||!*key||!value||!valid_category(category)||(source!=MW3_SOURCE_COD4&&source!=MW3_SOURCE_MW3)||!(mode_mask&3)|| (mode_mask&~3u)) return 0;
 mw3::Definition d;
 d.id=id;d.category=static_cast<mw3::Category>(category);d.source=source==MW3_SOURCE_MW3?mw3::Source::MW3:mw3::Source::COD4;
 if(mode_mask&1) d.sections.push_back(mw3::Section::Multiplayer);
 if(mode_mask&2) d.sections.push_back(mw3::Section::SpecialOps);
 d.properties[key]=value;
 std::lock_guard<std::mutex> lock(mutex_);
 try {registry->add(std::move(d));return 1;} catch(...) {return 0;}
}
extern "C" int mw3_resolve_string(MW3Mode mode, MW3Category category, const char* id, const char* key,char* output,unsigned int output_size) {
 if(!valid_mode(mode)||!valid_category(category)||!id||!key||!output||!output_size) return 0;
 std::lock_guard<std::mutex> lock(mutex_);
 const auto* d=registry->find(mode==MW3_MODE_MULTIPLAYER?mw3::Section::Multiplayer:mw3::Section::SpecialOps,static_cast<mw3::Category>(category),id);
 if(!d) return 0;
 auto item=d->properties.find(key);
 if(item==d->properties.end()||item->second.size()+1>output_size) return 0;
 std::memcpy(output,item->second.c_str(),item->second.size()+1);
 return 1;
}
extern "C" void mw3_reset_registry(void) {
 std::lock_guard<std::mutex> lock(mutex_);
 registry.reset(new mw3::GameplayRegistry);
}
