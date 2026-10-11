from pathlib import Path
root=Path(__file__).resolve().parents[1]
path=root/'ports/ios/core/mw3_combat_adapter.cpp'
s=path.read_text(encoding='utf-8')
assert '#include "mw3_combat_adapter.h"' in s
if '#include "mw3_definition_loader.h"' not in s:
 s=s.replace('#include "mw3_combat_adapter.h"','#include "mw3_combat_adapter.h"\n#include "mw3_definition_loader.h"\n#include <mutex>\n#include <string>\n#include <cstdlib>',1)
needle='bool read_integer(MW3Mode mode,MW3Category category,const char* id,const char* key,int& result){'
new='''void ensure_ios_definitions_loaded() {
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
'''
if 'ensure_ios_definitions_loaded() {' not in s:
 assert needle in s
 s=s.replace(needle,new+needle,1)
needle2=' if(!weapon||!*weapon||original<=0) return original;'
if ' ensure_ios_definitions_loaded();\n'+needle2 not in s:
 assert needle2 in s
 s=s.replace(needle2,' ensure_ios_definitions_loaded();\n'+needle2,1)
path.write_text(s,encoding='utf-8')
print('Installed iOS lazy Documents config loader')
