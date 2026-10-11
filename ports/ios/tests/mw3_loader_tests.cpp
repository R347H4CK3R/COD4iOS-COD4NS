#include "../core/mw3_definition_loader.h"
#include "../core/mw3_gameplay_bridge.h"
#include <cassert>
#include <cstdio>
#include <cstring>
int main() {
 const char* name="mw3_loader_test.tsv";
 FILE* file=std::fopen(name,"wb");assert(file);
 std::fputs("# local definitions\n1\t0\t1\ttest_rifle\tdamage\t36\n2\t0\t0\ttest_rifle\tdamage\t24\n",file);
 std::fclose(file);
 mw3_reset_registry();
 assert(mw3_load_definitions_tsv(name)==2);
 char value[32]={};
 assert(mw3_resolve_string(MW3_MODE_MULTIPLAYER,MW3_WEAPON,"test_rifle","damage",value,sizeof(value)));
 assert(std::strcmp(value,"36")==0);
 assert(mw3_resolve_string(MW3_MODE_SPECIAL_OPS,MW3_WEAPON,"test_rifle","damage",value,sizeof(value)));
 assert(std::strcmp(value,"24")==0);
 std::remove(name);
 assert(mw3_load_definitions_tsv(name)==-1);
}
