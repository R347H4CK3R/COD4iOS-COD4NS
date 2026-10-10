#pragma once
// Read user-supplied MW3 CSV data. No original data or script implementation is embedded.
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace cod4ios::survival::mw3 {
using Row = std::vector<std::string>;
struct CsvTable {
    std::vector<Row> rows;
    const Row *find(unsigned column, std::string_view key) const {
        for(const auto &row:rows) if(column<row.size() && row[column]==key) return &row;
        return nullptr; // Preserve first-match tablelookup semantics.
    }
};
inline bool parseCsv(std::string_view text, CsvTable &out, std::string &error) {
    constexpr std::size_t maxBytes=64*1024*1024, maxRows=100000, maxColumns=128;
    error.clear();
    auto fail=[&](const char *reason) { error=reason; return false; };
    if(text.size()>maxBytes) return fail("CSV exceeds 64 MiB");
    if(text.find('\0')!=std::string_view::npos) return fail("CSV contains NUL");
    if(text.substr(0,3)=="\xEF\xBB\xBF") text.remove_prefix(3);
    CsvTable parsed; Row row; std::string field;
    bool quoted=false, closed=false, touched=false;
    auto pushField=[&]() { row.push_back(std::move(field)); field.clear(); closed=false; return row.size()<=maxColumns; };
    auto pushRow=[&]() { parsed.rows.push_back(std::move(row)); row.clear(); touched=false; return parsed.rows.size()<=maxRows; };
    for(std::size_t i=0;i<text.size();++i) {
        char c=text[i];
        if(quoted) {
            if(c=='"') {
                if(i+1<text.size() && text[i+1]=='"') { field+='"'; ++i; }
                else { quoted=false; closed=true; }
            } else field+=c;
            continue;
        }
        if(closed && c!=',' && c!='\r' && c!='\n') return fail("Characters after closing quote");
        if(c=='"') {
            if(!field.empty() || closed) return fail("Quote inside unquoted field");
            quoted=true; touched=true;
        } else if(c==',') {
            touched=true; if(!pushField()) return fail("Too many CSV columns");
        } else if(c=='\r' || c=='\n') {
            if(c=='\r' && i+1<text.size() && text[i+1]=='\n') ++i;
            if(!pushField()) return fail("Too many CSV columns");
            if(!pushRow()) return fail("Too many CSV rows");
        } else { field+=c; touched=true; }
    }
    if(quoted) return fail("Unterminated quoted field");
    if(touched || closed || !row.empty()) {
        if(!pushField()) return fail("Too many CSV columns");
        if(!pushRow()) return fail("Too many CSV rows");
    }
    out=std::move(parsed); return true; // Failed reads never replace prior data.
}
inline bool unsignedValue(std::string_view text, unsigned &value) {
    if(text.empty()) return false;
    unsigned parsed=0;
    for(char c:text) {
        if(c<'0' || c>'9') return false;
        unsigned digit=unsigned(c-'0');
        if(parsed>(std::numeric_limits<unsigned>::max()-digit)/10) return false;
        parsed=parsed*10+digit;
    }
    value=parsed; return true;
}
inline bool optionalUnsigned(std::string_view text, unsigned &value) {
    if(text.empty()) { value=0; return true; }
    return unsignedValue(text,value);
}
struct Wave {
    unsigned index=0, bossDelay=0, number=0, squadCount=0, repeating=0;
    std::string squadType, specialTypes, specialCounts, aiBosses, nonAiBosses, armoryUnlocks;
};
// Column meanings are derived from script accessor calls. Row selection is explicit:
// tier CSVs also contain loadout records; callers must not treat every row as a wave.
inline bool decodeWave(const Row &row, Wave &out, std::string &error) {
    if(row.size()<11) { error="Wave requires at least 11 columns"; return false; }
    Wave value;
    if(!unsignedValue(row[0],value.index) || !optionalUnsigned(row[1],value.bossDelay) ||
       !unsignedValue(row[2],value.number) || !optionalUnsigned(row[4],value.squadCount) ||
       !optionalUnsigned(row[9],value.repeating)) { error="Invalid unsigned wave field"; return false; }
    value.squadType=row[3]; value.specialTypes=row[5]; value.specialCounts=row[6];
    value.aiBosses=row[7]; value.nonAiBosses=row[8]; value.armoryUnlocks=row[10];
    out=std::move(value); error.clear(); return true;
}
struct ArmoryItem {
    unsigned index=0, cost=0, rankIndex=0;
    std::string ref, type, name, description, icon, upgrades, restrictions, column10, column11;
};
inline bool decodeArmoryItem(const Row &row, ArmoryItem &out, std::string &error) {
    if(row.size()<12) { error="Armory requires at least 12 columns"; return false; }
    ArmoryItem value;
    if(!unsignedValue(row[0],value.index) || !unsignedValue(row[3],value.cost) || !optionalUnsigned(row[7],value.rankIndex) || row[1].empty()) {
        error="Invalid armory index, cost or ref"; return false;
    }
    value.ref=row[1]; value.type=row[2]; value.name=row[4]; value.description=row[5]; value.icon=row[6];
    value.upgrades=row[8]; value.restrictions=row[9]; value.column10=row[10]; value.column11=row[11];
    out=std::move(value); error.clear(); return true;
}
struct LoadoutItem {
    unsigned index=0, amount=0;
    std::string slot, ref;
};
inline bool decodeLoadoutItem(const Row &row, LoadoutItem &out, std::string &error) {
    if(row.size()<4) { error="Loadout requires at least 4 columns"; return false; }
    LoadoutItem value;
    if(!unsignedValue(row[0],value.index) || row[1].empty() || !optionalUnsigned(row[3],value.amount)) {
        error="Invalid loadout index, slot or amount"; return false;
    }
    value.slot=row[1]; value.ref=row[2]; out=std::move(value); error.clear(); return true;
}
struct Perk {
    unsigned index=0;
    std::string ref, name, description, icon, column5, column6;
};
inline bool decodePerk(const Row &row, Perk &out, std::string &error) {
    if(row.size()<7) { error="Perk requires at least 7 columns"; return false; }
    Perk value;
    if(!unsignedValue(row[0],value.index) || row[1].empty()) { error="Invalid perk index or ref"; return false; }
    value.ref=row[1]; value.name=row[2]; value.description=row[3]; value.icon=row[4];
    value.column5=row[5]; value.column6=row[6]; out=std::move(value); error.clear(); return true;
}

}
