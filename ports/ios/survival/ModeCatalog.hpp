#pragma once
// Portable mode catalog for the COD4iOS menu integration.
// No filesystem operations and no direct mutation of the active engine.
#include <string_view>
namespace cod4ios::modes {
enum class Mode { Campaign, Survival, Multiplayer, Invalid };
enum class Engine { SinglePlayer, MultiPlayer };
constexpr Mode fromId(std::string_view id) {
  return id=="campaign" ? Mode::Campaign :
         id=="survival" ? Mode::Survival :
         id=="multiplayer" ? Mode::Multiplayer : Mode::Invalid;
}
constexpr Mode fromSavedId(std::string_view value) {
  if(value=="sp") return Mode::Campaign;
  if(value=="mp") return Mode::Multiplayer;
  const Mode parsed=fromId(value);
  return parsed==Mode::Invalid ? Mode::Campaign : parsed;
}
constexpr const char* id(Mode mode) {
  switch(mode) {
    case Mode::Campaign: return "campaign";
    case Mode::Survival: return "survival";
    case Mode::Multiplayer: return "multiplayer";
    default: return "";
  }
}
constexpr Engine engine(Mode mode) {
  return mode==Mode::Multiplayer ? Engine::MultiPlayer : Engine::SinglePlayer;
}
constexpr bool requiresRestart(Mode current, Mode requested) {
  return current!=Mode::Invalid && requested!=Mode::Invalid &&
         engine(current)!=engine(requested);
}
// Later native adapter must validate this relative path against COD4iOS
// Documents root and never traverse outside that root.
constexpr std::string_view survivalContentFolder() {
  return "mods/specops_survival";
}
} // namespace cod4ios::modes
