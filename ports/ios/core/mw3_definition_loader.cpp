#include "mw3_definition_loader.h"
#include "mw3_gameplay_bridge.h"
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cstdlib>
#include <cerrno>
namespace {
bool integer(const std::string& s,int& v) {
 if(s.empty()) return false;
 char* end=nullptr;errno=0;
 long n=std::strtol(s.c_str(),&end,10);
 if(errno||end==s.c_str()||*end||n<0||n>1000) return false;
 v=static_cast<int>(n);return true;
}
}
extern "C" int mw3_load_definitions_tsv(const char* path) {
 if(!path||!*path) return -1;
 std::ifstream file(path);
 if(!file) return -1;
 std::string line;int count=0;
 while(std::getline(file,line)) {
  if(line.empty()||line[0]=='#') continue;
  std::vector<std::string> fields;std::istringstream input(line);std::string field;
  while(std::getline(input,field,'\t')) fields.push_back(field);
  if(fields.size()!=6) return -1;
  int mode=0,category=0,source=0;
  if(!integer(fields[0],mode)||mode<1||mode>3||!integer(fields[1],category)||category>5||!integer(fields[2],source)||source>1) return -1;
  if(fields[3].empty()||fields[4].empty()||fields[3].size()>128||fields[4].size()>64||fields[5].size()>512) return -1;
  if(!mw3_register_definition(fields[3].c_str(),static_cast<MW3Category>(category),static_cast<MW3Source>(source),static_cast<unsigned>(mode),fields[4].c_str(),fields[5].c_str())) return -1;
  ++count;
 }
 return count;
}
