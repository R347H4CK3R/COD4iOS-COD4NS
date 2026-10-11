#include "mw3_gameplay_registry.h"
#include <algorithm>
#include <stdexcept>
#include <utility>
namespace mw3 {
void GameplayRegistry::add(Definition definition) {
 if(definition.id.empty() || definition.sections.empty()) throw std::invalid_argument("invalid gameplay definition");
 for (const auto& entry:entries_) {
  if(entry.id==definition.id && entry.category==definition.category && entry.source==definition.source)
   throw std::invalid_argument("duplicate gameplay definition");
 }
 entries_.push_back(std::move(definition));
}
const Definition* GameplayRegistry::find(Section section, Category category, const std::string& id, Source preferred) const {
 const Definition* candidate=nullptr;
 for(const auto& entry:entries_) {
  if(entry.id!=id || entry.category!=category) continue;
  if(std::find(entry.sections.begin(),entry.sections.end(),section)==entry.sections.end()) continue;
  if(entry.source==preferred) return &entry;
  candidate=&entry;
 }
 return candidate;
}
std::size_t GameplayRegistry::count(Section section, Category category) const {
 std::size_t n=0;
 for(const auto& e:entries_)
  if(e.category==category && std::find(e.sections.begin(),e.sections.end(),section)!=e.sections.end() && find(section,category,e.id)==&e) ++n;
 return n;
}
}
