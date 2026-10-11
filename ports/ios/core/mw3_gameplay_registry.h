#pragma once
#include <string>
#include <vector>
#include <map>
namespace mw3 {
enum class Section { Multiplayer, SpecialOps };
enum class Source { COD4, MW3 };
enum class Category { Weapon, Attachment, Perk, Lethal, Tactical, Killstreak };
struct Definition {
 std::string id;
 Category category;
 Source source;
 std::vector<Section> sections;
 std::map<std::string,std::string> properties;
};
class GameplayRegistry {
public:
 void add(Definition definition);
 void addProperty(Definition definition);
 const Definition* find(Section section, Category category, const std::string& id, Source preferred=Source::MW3) const;
 std::size_t count(Section section, Category category) const;
private:
 std::vector<Definition> entries_;
};
}
